"""
core/auth.py
Microsoft account authentication for RevoMC using minecraft-launcher-lib.

Uses the OAuth2 PKCE flow with a local HTTP server to capture the redirect,
so the user never has to copy-paste URLs.
"""

import json
import socket
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Optional
from urllib.parse import urlparse, parse_qs

import minecraft_launcher_lib.microsoft_account as ms_auth
from minecraft_launcher_lib.microsoft_account import (
    AzureAppNotPermitted,
    InvalidRefreshToken,
    AccountNotOwnMinecraft,
)

import core.config as config

# ── Azure Application ─────────────────────────────────────────────────────────

CLIENT_ID = "50587c66-8ef5-44fe-9a3d-dcb519f73cea"
REDIRECT_URI = "http://localhost"

# ── Local HTTP Server for OAuth Redirect ──────────────────────────────────────


class _AuthCallbackHandler(BaseHTTPRequestHandler):
    """One-shot HTTP handler that captures the OAuth redirect URL."""

    auth_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        # Store the full URL for parsing
        full_url = f"http://localhost:{self.server.server_address[1]}{self.path}"
        server = self.server

        try:
            if ms_auth.url_contains_auth_code(full_url):
                code = ms_auth.parse_auth_code_url(full_url, server._state)
                server._auth_code = code
                self._send_success_page()
            else:
                # Check for error in query params
                query = parse_qs(urlparse(self.path).query)
                error = query.get("error", [""])[0]
                error_desc = query.get("error_description", ["Authentication failed"])[0]
                server._error = error_desc if error else "No authorization code received."
                self._send_error_page(server._error)
        except (AssertionError, KeyError) as e:
            server._error = f"State validation failed: {e}"
            self._send_error_page(server._error)

        # Signal that we're done
        threading.Thread(target=server.shutdown, daemon=True).start()

    def _send_success_page(self):
        html = """<!DOCTYPE html><html><head><meta charset="utf-8">
        <title>RevoMC — Signed In</title>
        <style>
            body { font-family: -apple-system, sans-serif; background: #1a1a2e;
                   color: #e0e0e0; display: flex; justify-content: center;
                   align-items: center; height: 100vh; margin: 0; }
            .card { text-align: center; background: #16213e; padding: 48px 64px;
                    border-radius: 16px; border: 1px solid #2d3748; }
            h1 { color: #4ade80; margin-bottom: 8px; }
            p { color: #9ca3af; }
        </style></head><body>
        <div class="card">
            <h1>✅ Signed In!</h1>
            <p>You can close this tab and return to RevoMC.</p>
        </div></body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_error_page(self, message: str):
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
        <title>RevoMC — Error</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #1a1a2e;
                   color: #e0e0e0; display: flex; justify-content: center;
                   align-items: center; height: 100vh; margin: 0; }}
            .card {{ text-align: center; background: #16213e; padding: 48px 64px;
                    border-radius: 16px; border: 1px solid #2d3748; }}
            h1 {{ color: #f87171; margin-bottom: 8px; }}
            p {{ color: #9ca3af; }}
        </style></head><body>
        <div class="card">
            <h1>❌ Authentication Failed</h1>
            <p>{message}</p>
            <p>Please close this tab and try again in RevoMC.</p>
        </div></body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress default HTTP request logging."""
        pass


class _AuthServer(HTTPServer):
    """HTTPServer subclass that stores auth state."""

    _auth_code: Optional[str] = None
    _error: Optional[str] = None
    _state: Optional[str] = None


def _find_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


# ── Public API ────────────────────────────────────────────────────────────────


def start_login(
    log: Callable[[str], None],
    on_success: Callable[[dict], None],
    on_error: Callable[[str], None],
) -> None:
    """
    Start the Microsoft OAuth2 PKCE login flow in a background thread.

    1. Picks a free port and builds the redirect URI
    2. Generates the login URL via minecraft-launcher-lib
    3. Opens the user's browser
    4. Starts a local HTTP server to capture the redirect
    5. Exchanges the auth code for Minecraft tokens
    6. Calls on_success(login_data) or on_error(message)
    """

    def _worker():
        try:
            port = _find_free_port()
            redirect_uri = f"{REDIRECT_URI}:{port}"

            log("🔵 Generating secure login data…")
            login_url, state, code_verifier = ms_auth.get_secure_login_data(
                CLIENT_ID, redirect_uri
            )

            # Start the local server
            server = _AuthServer(("", port), _AuthCallbackHandler)
            server._state = state

            log("🌐 Opening Microsoft login in your browser…")
            webbrowser.open(login_url)
            log("⏳ Waiting for authentication (you have 5 minutes)…")

            # Set a timeout — server.handle_request() blocks, so we use
            # serve_forever with shutdown from the handler
            server.timeout = 300  # 5 minutes
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            server_thread.join(timeout=300)

            if server._auth_code is None:
                if server._error:
                    on_error(server._error)
                else:
                    server.shutdown()
                    on_error("Login timed out — no response received within 5 minutes.")
                return

            log("🔑 Exchanging authorization code for Minecraft tokens…")
            login_data = ms_auth.complete_login(
                CLIENT_ID,
                None,  # No client secret for public apps
                redirect_uri,
                server._auth_code,
                code_verifier,
            )

            # Persist to config
            _save_account(login_data)
            log(f"✅ Signed in as {login_data['name']}")
            log("🎮 Ready to play on online-mode servers!")
            on_success(dict(login_data))

        except AzureAppNotPermitted:
            on_error(
                "Azure app not permitted to use Minecraft API. "
                "Apply at: https://aka.ms/mce-reviewappid"
            )
        except AccountNotOwnMinecraft:
            on_error(
                "This Microsoft account does not own Minecraft Java Edition. "
                "Purchase the game at minecraft.net to use online mode."
            )
        except Exception as e:
            on_error(f"Login failed: {e}")

    threading.Thread(target=_worker, daemon=True).start()


def try_refresh(log: Callable[[str], None]) -> Optional[dict]:
    """
    Attempt to silently refresh the session using a stored refresh token.
    Returns the refreshed login_data dict, or None if refresh failed.
    """
    cfg = config.load()
    account = cfg.get("ms_account")
    if not account or not account.get("refresh_token"):
        return None

    try:
        log("🔄 Refreshing Microsoft session…")
        login_data = ms_auth.complete_refresh(
            CLIENT_ID,
            None,  # No client secret
            None,  # No redirect URI needed for refresh
            account["refresh_token"],
        )
        _save_account(login_data)
        log(f"✅ Session refreshed — signed in as {login_data['name']}")
        return dict(login_data)
    except InvalidRefreshToken:
        log("⚠  Session expired — please sign in again.")
        _clear_account()
        return None
    except Exception as e:
        log(f"⚠  Refresh failed: {e}")
        _clear_account()
        return None


def logout(log: Callable[[str], None]) -> None:
    """Clear stored Microsoft account data."""
    _clear_account()
    log("🚪 Signed out of Microsoft account.")


def get_stored_account() -> Optional[dict]:
    """Return the stored Microsoft account dict, or None."""
    cfg = config.load()
    return cfg.get("ms_account")


def is_logged_in() -> bool:
    """Quick check whether a Microsoft account session is stored."""
    account = get_stored_account()
    return account is not None and bool(account.get("access_token"))


# ── Internal helpers ──────────────────────────────────────────────────────────


def _save_account(login_data: dict) -> None:
    """Persist account data to config."""
    cfg = config.load()
    cfg["auth_mode"] = "microsoft"
    cfg["ms_account"] = {
        "name": login_data["name"],
        "id": login_data["id"],
        "access_token": login_data["access_token"],
        "refresh_token": login_data["refresh_token"],
    }
    config.save(cfg)


def _clear_account() -> None:
    """Remove account data from config."""
    cfg = config.load()
    cfg["ms_account"] = None
    config.save(cfg)
