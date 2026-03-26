"""
ui/main_window.py  –  CustomTkinter UI for RevoMC
All program logic is identical to the original PyQt6 version.
"""

import threading
import customtkinter as ctk
from tkinter import messagebox

import core.config as config
from core.installer import (
    fetch_release_versions,
    fetch_fabric_versions,
    install_minecraft,
    install_fabric,
    install_mods,
    AVAILABLE_MODS,
)
from core.launcher import launch

# ── Appearance ────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# Colour tokens (matching the original palette)
BG_PRIMARY   = "#1a1a2e"
BG_SECONDARY = "#16213e"
BG_CONSOLE   = "#0f0f1a"
BORDER_COL   = "#2d3748"
GREEN        = "#4ade80"
GREEN_DARK   = "#22c55e"
BLUE         = "#60a5fa"
RED          = "#f87171"
TEXT_FG      = "#e0e0e0"
TEXT_MUTED   = "#9ca3af"
TEXT_LABEL   = "#6b7280"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _section_label(master, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        master, text=text.upper(),
        text_color=TEXT_LABEL,
        font=ctk.CTkFont(size=10, weight="bold"),
    )


# ── New Profile Dialog ─────────────────────────────────────────────────────────

class NewProfileDialog(ctk.CTkToplevel):
    """Modal dialog for creating a new profile.  Mirrors the original QDialog."""

    def __init__(self, parent, all_versions: list[str], fabric_versions: list[str]):
        super().__init__(parent)
        self.all_versions    = all_versions
        self.fabric_versions = fabric_versions
        self.result: dict | None = None

        self.title("New Profile")
        self.geometry("460x600")
        self.resizable(False, True)
        self.minsize(460, 480)
        # Make modal
        self.transient(parent)
        self.grab_set()

        self._build()
        self.wait_window(self)  # blocks until dialog closes

    # ── Dialog UI ─────────────────────────────────────────────────────────────

    def _build(self):
        pad = {"padx": 20, "pady": (8, 0)}

        # ── Bottom buttons pinned first so they're always visible ─────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", padx=20, pady=12)
        ctk.CTkButton(btn_row, text="Cancel", fg_color="transparent",
                      border_width=1, border_color=BORDER_COL,
                      text_color=TEXT_FG,
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_row, text="Create", fg_color=GREEN, text_color=BG_PRIMARY,
                      hover_color=GREEN_DARK,
                      command=self._on_ok).pack(side="right")

        # ── Scrollable body ───────────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Profile name (optional)
        _section_label(body, "Profile Name  (optional)").pack(anchor="w", padx=20, pady=(10, 0))
        self.name_var = ctk.StringVar()
        ctk.CTkEntry(
            body, textvariable=self.name_var,
            placeholder_text="Leave blank for default name…",
            width=420,
        ).pack(padx=20, pady=(4, 0))

        # Profile type
        _section_label(body, "Profile Type").pack(anchor="w", padx=20, pady=(10, 0))
        type_row = ctk.CTkFrame(body, fg_color="transparent")
        type_row.pack(anchor="w", padx=20, pady=(4, 0))
        self.type_var = ctk.StringVar(value="fabric")
        ctk.CTkRadioButton(
            type_row, text="Fabric + Mods",
            variable=self.type_var, value="fabric",
            command=self._on_type_changed,
        ).pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(
            type_row, text="Vanilla",
            variable=self.type_var, value="vanilla",
            command=self._on_type_changed,
        ).pack(side="left")

        # Minecraft version list
        _section_label(body, "Minecraft Version").pack(anchor="w", padx=20, pady=(10, 0))
        self.version_frame = ctk.CTkScrollableFrame(body, height=150, width=420)
        self.version_frame.pack(padx=20, pady=(4, 0))
        self._version_buttons: list[ctk.CTkButton] = []
        self._selected_version: str | None = None

        # Mods section
        self.mods_outer = ctk.CTkFrame(body, fg_color="transparent")
        self.mods_outer.pack(fill="x", padx=20, pady=(10, 0))
        _section_label(self.mods_outer, "Mods  (Fabric API always included)").pack(anchor="w")
        self.mod_vars: dict[str, ctk.BooleanVar] = {}
        for key, mod in AVAILABLE_MODS.items():
            var = ctk.BooleanVar(value=True)
            self.mod_vars[key] = var
            ctk.CTkCheckBox(
                self.mods_outer,
                text=f"{mod['label']}  :  {mod['desc']}",
                variable=var,
            ).pack(anchor="w", pady=2)

        self._on_type_changed()  # initial populate

    def _on_type_changed(self):
        # Clear existing buttons
        for btn in self._version_buttons:
            btn.destroy()
        self._version_buttons.clear()
        self._selected_version = None

        is_fabric = self.type_var.get() == "fabric"
        versions = self.fabric_versions if is_fabric else self.all_versions

        # Toggle mods frame
        if is_fabric:
            self.mods_outer.pack(fill="x", padx=20, pady=(8, 0))
        else:
            self.mods_outer.pack_forget()

        # Populate version list
        for i, v in enumerate(versions):
            btn = ctk.CTkButton(
                self.version_frame, text=v,
                fg_color="transparent", text_color=TEXT_FG,
                hover_color=BG_SECONDARY, anchor="w",
                command=lambda ver=v: self._select_version(ver),
            )
            btn.pack(fill="x", pady=1)
            self._version_buttons.append(btn)
            if i == 0:
                self._select_version(v)

    def _select_version(self, ver: str):
        self._selected_version = ver
        for btn in self._version_buttons:
            if btn.cget("text") == ver:
                btn.configure(fg_color=GREEN, text_color=BG_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_FG)

    def _on_ok(self):
        if not self._selected_version:
            return
        profile_type = self.type_var.get()
        name = self.name_var.get().strip()
        if not name:
            name = "Untitled Fabric" if profile_type == "fabric" else "Untitled Vanilla"
        enabled_mods = (
            [k for k, v in self.mod_vars.items() if v.get()]
            if profile_type == "fabric"
            else []
        )
        self.result = {
            "name": name,
            "mc_version": self._selected_version,
            "type": profile_type,
            "mods": enabled_mods,
        }
        self.destroy()


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg              = config.load()
        self.all_versions: list[str]    = []
        self.fabric_versions: list[str] = []
        self._busy            = False
        self._selected_profile_idx: int = -1

        self._setup_ui()
        self._check_java()
        self._load_versions()

    # ── Java check (same as original) ─────────────────────────────────────────

    def _check_java(self):
        from core.java_manager import is_runtime_installed
        if not is_runtime_installed():
            self._log("⚠  Java runtime not found — it will be downloaded automatically when you click Install.")
        else:
            self._log("✅ Java runtime ready.")

    # ── UI Construction ───────────────────────────────────────────────────────

    def _setup_ui(self):
        self.title("RevoMC")
        self.minsize(960, 660)
        self.configure(fg_color=BG_PRIMARY)

        # Root vstack
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=24, pady=20)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(root, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        # Title block
        ctk.CTkLabel(
            header, text="⛏  RevoMC",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=GREEN,
        ).pack(side="left", anchor="s")
        ctk.CTkLabel(
            header,
            text="   Fabric enabled, performance optimised launcher for Minecraft",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_LABEL,
        ).pack(side="left", anchor="s", pady=(0, 3))

        # Username block (right side)
        user_block = ctk.CTkFrame(header, fg_color="transparent")
        user_block.pack(side="right", anchor="s")
        _section_label(user_block, "Username").pack(anchor="w")
        self.username_var = ctk.StringVar(value=self.cfg.get("username", ""))
        self.username_var.trace_add("write", self._on_username_changed)
        ctk.CTkEntry(
            user_block, textvariable=self.username_var,
            placeholder_text="Enter username…", width=200,
        ).pack()

        # Divider
        ctk.CTkFrame(root, height=1, fg_color=BORDER_COL).pack(fill="x", pady=(0, 14))

        # ── Content (left + right columns) ────────────────────────────────────
        content = ctk.CTkFrame(root, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        self._build_left(content)
        self._build_right(content)

    def _build_left(self, parent):
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(1, weight=1)

        # Profile header row
        ph = ctk.CTkFrame(left, fg_color="transparent")
        ph.pack(fill="x", pady=(0, 6))
        _section_label(ph, "Profiles").pack(side="left")
        self.del_btn = ctk.CTkButton(
            ph, text="Delete", width=72,
            fg_color="transparent", border_width=1, border_color=RED,
            text_color=RED, hover_color=RED,
            command=self._on_delete_profile,
        )
        self.del_btn.pack(side="right", padx=(6, 0))
        self.new_btn = ctk.CTkButton(
            ph, text="+ New", width=72,
            fg_color="transparent", border_width=1, border_color=BLUE,
            text_color=BLUE, hover_color=BLUE,
            command=self._on_new_profile,
        )
        self.new_btn.pack(side="right")

        # Profile list (scrollable frame with radio-style selection)
        self.profile_list_frame = ctk.CTkScrollableFrame(
            left, label_text="", fg_color=BG_SECONDARY,
            border_color=BORDER_COL, border_width=1,
        )
        self.profile_list_frame.pack(fill="both", expand=True, pady=(0, 8))

        # Info card
        self.info_card = ctk.CTkFrame(
            left, fg_color=BG_SECONDARY,
            border_color=BORDER_COL, border_width=1, corner_radius=6,
        )
        self.info_card.pack(fill="x", pady=(0, 8))
        self.info_version_lbl = ctk.CTkLabel(
            self.info_card, text="", text_color=TEXT_MUTED, font=ctk.CTkFont(size=12),
        )
        self.info_version_lbl.pack(anchor="w", padx=12, pady=(8, 0))
        self.info_mods_lbl = ctk.CTkLabel(
            self.info_card, text="", text_color=TEXT_MUTED, font=ctk.CTkFont(size=12),
            wraplength=380, justify="left",
        )
        self.info_mods_lbl.pack(anchor="w", padx=12, pady=(2, 8))

        # RAM slider
        ram_row = ctk.CTkFrame(left, fg_color="transparent")
        ram_row.pack(fill="x", pady=(0, 4))
        self.ram_label_lbl = _section_label(ram_row, f"RAM — {self.cfg.get('ram_gb', 2)} GB")
        self.ram_label_lbl.pack(side="left")
        self.ram_var = ctk.IntVar(value=self.cfg.get("ram_gb", 2))
        self.ram_slider = ctk.CTkSlider(
            left, from_=1, to=16, number_of_steps=15,
            variable=self.ram_var, command=self._on_ram_changed,
        )
        self.ram_slider.pack(fill="x", pady=(0, 10))

        # Single smart Play / Install & Play button
        self.play_btn = ctk.CTkButton(
            left, text="▶  PLAY",
            fg_color=GREEN, text_color=BG_PRIMARY,
            hover_color=GREEN_DARK, font=ctk.CTkFont(size=15, weight="bold"),
            height=44, command=self._on_play_btn,
        )
        self.play_btn.pack(fill="x")

        self._profile_buttons: list[ctk.CTkFrame] = []
        self._refresh_profile_list()

    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.rowconfigure(1, weight=1)

        _section_label(right, "Console").pack(anchor="w", pady=(0, 4))

        self.log_box = ctk.CTkTextbox(
            right, state="disabled",
            fg_color=BG_CONSOLE, border_color=BORDER_COL, border_width=1,
            font=ctk.CTkFont(family="monospace", size=11),
            text_color="#a0aec0",
        )
        self.log_box.pack(fill="both", expand=True, pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(
            right, progress_color=GREEN, fg_color=BG_SECONDARY,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 4))

        self.status_lbl = ctk.CTkLabel(
            right, text="Ready.", text_color=TEXT_LABEL,
            font=ctk.CTkFont(size=11), anchor="w",
        )
        self.status_lbl.pack(anchor="w")

    # ── Version loading ────────────────────────────────────────────────────────

    def _load_versions(self):
        self._log("🌐 Fetching Minecraft versions…")

        def _task():
            try:
                all_v = fetch_release_versions()
                self.all_versions = [v["id"] for v in all_v]
                self.after(0, lambda: self._log(f"✅ {len(self.all_versions)} total MC releases found."))
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Could not fetch MC versions: {e}"))

            try:
                self.fabric_versions = fetch_fabric_versions()
                self.after(0, lambda: self._log(f"✅ {len(self.fabric_versions)} versions supported by Fabric."))
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Could not fetch Fabric versions: {e}"))

            self.after(0, self._refresh_buttons)

        threading.Thread(target=_task, daemon=True).start()

    # ── Profiles ──────────────────────────────────────────────────────────────

    def _refresh_profile_list(self):
        # Destroy old widgets
        for w in self.profile_list_frame.winfo_children():
            w.destroy()
        self._profile_buttons = []

        profiles = self.cfg.get("profiles", [])
        active   = self.cfg.get("active_profile")

        for i, p in enumerate(profiles):
            type_tag = "🟢 Fabric" if p["type"] == "fabric" else "🍦 Vanilla"
            label    = f"{p['name']}\n{p['mc_version']}  ·  {type_tag}"

            btn = ctk.CTkButton(
                self.profile_list_frame,
                text=label,
                anchor="w",
                fg_color=GREEN if p["name"] == active else BG_SECONDARY,
                text_color=BG_PRIMARY if p["name"] == active else TEXT_FG,
                hover_color=GREEN_DARK if p["name"] == active else "#1e293b",
                font=ctk.CTkFont(size=12),
                command=lambda idx=i: self._on_profile_selected(idx),
            )
            btn.pack(fill="x", pady=2, padx=4)
            self._profile_buttons.append(btn)

        # Restore selection
        if active:
            for i, p in enumerate(profiles):
                if p["name"] == active:
                    self._selected_profile_idx = i
                    self._update_info_card(p)
                    break
        self._refresh_buttons()

    def _current_profile(self) -> dict | None:
        profiles = self.cfg.get("profiles", [])
        i = self._selected_profile_idx
        return profiles[i] if 0 <= i < len(profiles) else None

    def _on_profile_selected(self, idx: int):
        profiles = self.cfg.get("profiles", [])
        if 0 <= idx < len(profiles):
            self._selected_profile_idx = idx
            self.cfg["active_profile"] = profiles[idx]["name"]
            config.save(self.cfg)
            self._update_info_card(profiles[idx])
            # Recolour buttons
            for i, btn in enumerate(self._profile_buttons):
                if i == idx:
                    btn.configure(fg_color=GREEN, text_color=BG_PRIMARY, hover_color=GREEN_DARK)
                else:
                    btn.configure(fg_color=BG_SECONDARY, text_color=TEXT_FG, hover_color="#1e293b")
        self._refresh_buttons()

    def _update_info_card(self, profile: dict):
        self.info_version_lbl.configure(
            text=f"MC {profile['mc_version']}  ·  {'Fabric' if profile['type'] == 'fabric' else 'Vanilla'}"
        )
        if profile["type"] == "fabric":
            mods   = profile.get("mods", [])
            labels = [AVAILABLE_MODS[m]["label"] for m in mods if m in AVAILABLE_MODS]
            self.info_mods_lbl.configure(text="Mods: " + (", ".join(labels) if labels else "none"))
        else:
            self.info_mods_lbl.configure(text="No mods — pure vanilla")

    def _on_new_profile(self):
        if not self.all_versions:
            self._log("⚠  Still loading versions, try again in a moment.")
            return
        dlg = NewProfileDialog(self, self.all_versions, self.fabric_versions)
        profile = dlg.result
        if not profile:
            return
        if not profile.get("name"):
            self._log("⚠  Profile name cannot be empty.")
            return
        if any(p["name"] == profile["name"] for p in self.cfg.get("profiles", [])):
            self._log(f"⚠  A profile named '{profile['name']}' already exists.")
            return
        self.cfg.setdefault("profiles", []).append(profile)
        self.cfg["active_profile"] = profile["name"]
        config.save(self.cfg)
        self._refresh_profile_list()
        self._log(f"✅ Profile '{profile['name']}' created  ({profile['mc_version']}, {profile['type']}).")

    def _on_delete_profile(self):
        profile = self._current_profile()
        if not profile:
            return
        if not messagebox.askyesno("Delete Profile", f"Delete '{profile['name']}'?", parent=self):
            return
        self.cfg["profiles"] = [
            p for p in self.cfg.get("profiles", []) if p["name"] != profile["name"]
        ]
        if self.cfg.get("active_profile") == profile["name"]:
            self.cfg["active_profile"] = None
        self._selected_profile_idx = -1
        config.save(self.cfg)
        self._refresh_profile_list()
        self._log(f"🗑  Deleted '{profile['name']}'.")

    # ── Install & Play (unified) ───────────────────────────────────────────────

    def _is_installed_for_profile(self, profile: dict) -> bool:
        """Return True only when the version is installed with the *same* type (fabric/vanilla)."""
        entry = self.cfg.get("installed_versions", {}).get(profile["mc_version"])
        if not entry:
            return False
        return entry.get("type") == profile["type"]

    def _on_play_btn(self):
        profile = self._current_profile()
        if not profile:
            return
        username = self.username_var.get().strip()
        if not username:
            self._log("⚠  Please enter a username before playing.")
            return

        mc_version   = profile["mc_version"]
        profile_type = profile["type"]
        enabled_mods = profile.get("mods", [])
        ram_gb       = self.ram_var.get()
        needs_install = not self._is_installed_for_profile(profile)

        self._set_busy(True)
        self._log(f"\n{'─'*40}")
        if needs_install:
            self._log(f"📦 Installing '{profile['name']}' ({mc_version}, {profile_type})…")
        else:
            self._log(f"🚀 Launching '{profile['name']}'…")

        def worker():
            try:
                fabric_profile_id = None

                # ── Install phase (skipped if already up-to-date) ──────────
                if needs_install:
                    from core.java_manager import install_java
                    install_java(
                        log=lambda m: self.after(0, lambda msg=m: self._log(msg)),
                        progress=lambda t, p: self.after(0, lambda tt=t, pp=p: self._on_progress(tt, pp)),
                    )
                    install_minecraft(
                        mc_version,
                        log=lambda m: self.after(0, lambda msg=m: self._log(msg)),
                        progress=lambda t, p: self.after(0, lambda tt=t, pp=p: self._on_progress(tt, pp)),
                    )
                    if profile_type == "fabric":
                        fabric_profile_id = install_fabric(
                            mc_version,
                            log=lambda m: self.after(0, lambda msg=m: self._log(msg)),
                            progress=lambda t, p: self.after(0, lambda tt=t, pp=p: self._on_progress(tt, pp)),
                        )
                        install_mods(
                            mc_version, enabled_mods,
                            log=lambda m: self.after(0, lambda msg=m: self._log(msg)),
                            progress=lambda t, p: self.after(0, lambda tt=t, pp=p: self._on_progress(tt, pp)),
                        )
                    self.cfg.setdefault("installed_versions", {})[mc_version] = {
                        "fabric_profile_id": fabric_profile_id,
                        "type": profile_type,
                    }
                    config.save(self.cfg)
                    self.after(0, lambda: self._log("✅ Installation complete — launching…"))
                else:
                    fabric_profile_id = (
                        self.cfg.get("installed_versions", {})
                        .get(mc_version, {})
                        .get("fabric_profile_id")
                    )

                # ── Launch phase ──────────────────────────────────────────
                self.after(0, lambda: self._log("🚀 Starting game…"))
                proc = launch(
                    mc_version=mc_version,
                    profile_type=profile_type,
                    fabric_profile_id=fabric_profile_id,
                    username=username,
                    ram_gb=ram_gb,
                    log=lambda m: self.after(0, lambda msg=m: self._log(msg)),
                )
                self.after(0, lambda: self._log("🎮 Game launched!"))
                for line in proc.stdout:
                    self.after(0, lambda l=line: self._log(l.rstrip()))
                proc.wait()
                self.after(
                    0,
                    lambda: self._on_worker_done(True, f"Game exited (code {proc.returncode})"),
                )
            except Exception as e:
                self.after(0, lambda err=e: self._on_worker_done(False, str(err)))

        threading.Thread(target=worker, daemon=True).start()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _on_username_changed(self, *_):
        text = self.username_var.get()
        self.cfg["username"] = text
        config.save(self.cfg)
        self._refresh_buttons()

    def _on_ram_changed(self, val):
        gb = int(val)
        self.cfg["ram_gb"] = gb
        config.save(self.cfg)
        self.ram_label_lbl.configure(text=f"RAM — {gb} GB")

    def _refresh_buttons(self):
        profile     = self._current_profile()
        username    = self.username_var.get().strip()
        has_profile = profile is not None
        installed   = has_profile and self._is_installed_for_profile(profile)

        # Button label changes based on install state
        if not has_profile:
            btn_text  = "▶  PLAY"
            state_play = "disabled"
        elif not installed:
            btn_text  = "⬇  Install & Play"
            state_play = "normal" if bool(username) else "disabled"
        else:
            btn_text  = "▶  PLAY"
            state_play = "normal" if bool(username) else "disabled"

        self.play_btn.configure(text=btn_text, state=state_play)
        self.del_btn.configure(state="normal" if has_profile else "disabled")

    def _on_progress(self, task: str, pct: int):
        self.progress_bar.set(pct / 100)
        self.status_lbl.configure(text=f"{task}: {pct}%")

    def _on_worker_done(self, success: bool, message: str):
        self._set_busy(False)
        self.progress_bar.set(1.0 if success else 0.0)
        self._log(f"{'✅' if success else '❌'} {message}")
        self.status_lbl.configure(text="Ready.")
        self._refresh_buttons()

    def _set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.play_btn.configure(state=state)
        self.new_btn.configure(state=state)
        self.del_btn.configure(state=state)
        if not busy:
            self._refresh_buttons()  # restore correct label after busy clears

    def _log(self, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.configure(state="disabled")
        self.log_box.see("end")
