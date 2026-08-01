"""
ui/theme.py
Defines the color palettes for the RevoMC launcher.
"""

def get_theme(name: str) -> dict:
    # Common colors
    common = {
        "RED": "#f87171",
        "MS_BLUE": "#2f7ee7",
        "MS_BLUE_DARK": "#1a5ebf",
        "TEXT_FG": "#e0e0e0",
        "TEXT_MUTED": "#9ca3af",
        "TEXT_LABEL": "#6b7280",
    }
    
    themes = {
        "overworld": {
            "BG_PRIMARY": "#1a2e1a",
            "BG_SECONDARY": "#213e21",
            "BG_CONSOLE": "#0f1a0f",
            "BORDER_COL": "#37482d",
            "ACCENT": "#4ade80",
            "ACCENT_DARK": "#22c55e",
            "ACCENT_ALT": "#60a5fa",
        },
        "nether": {
            "BG_PRIMARY": "#2e1a1a",
            "BG_SECONDARY": "#3e2116",
            "BG_CONSOLE": "#1a0f0f",
            "BORDER_COL": "#48372d",
            "ACCENT": "#f97316",
            "ACCENT_DARK": "#ea580c",
            "ACCENT_ALT": "#facc15",
        },
        "end": {
            "BG_PRIMARY": "#1a1a2e",
            "BG_SECONDARY": "#16213e",
            "BG_CONSOLE": "#0f0f1a",
            "BORDER_COL": "#2d3748",
            "ACCENT": "#a78bfa",
            "ACCENT_DARK": "#7c3aed",
            "ACCENT_ALT": "#60a5fa",
        }
    }
    
    # Default to overworld if invalid name
    selected = themes.get(name.lower(), themes["overworld"])
    return {**common, **selected}
