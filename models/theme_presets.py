"""Theme preset definitions — curated colour schemes for the Spamlyser UI."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ThemePreset:
    name: str
    icon: str
    css_variables: dict[str, str]
    is_dark: bool


PRESETS: dict[str, ThemePreset] = {
    "spamlord": ThemePreset(
        name="SpamLord Dark",
        icon="🌙",
        is_dark=True,
        css_variables={
            "--bg-primary": "#0f0f1a",
            "--bg-secondary": "#1a1a2e",
            "--text-primary": "#e0e0ff",
            "--text-secondary": "#9090b0",
            "--card-bg": "#1e1e36",
            "--card-border": "#2d2d50",
            "--input-bg": "#252545",
            "--input-border": "#3a3a60",
            "--accent": "#7c3aed",
            "--error": "#ef4444",
            "--success": "#22c55e",
            "--warning": "#f59e0b",
        },
    ),
    "ocean": ThemePreset(
        name="Ocean Breeze",
        icon="🌊",
        is_dark=False,
        css_variables={
            "--bg-primary": "#f0f8ff",
            "--bg-secondary": "#e6f2ff",
            "--text-primary": "#1a365d",
            "--text-secondary": "#4a5568",
            "--card-bg": "#ffffff",
            "--card-border": "#bee3f8",
            "--input-bg": "#ffffff",
            "--input-border": "#90cdf4",
            "--accent": "#2b6cb0",
            "--error": "#c53030",
            "--success": "#276749",
            "--warning": "#975a16",
        },
    ),
    "forest": ThemePreset(
        name="Forest Canopy",
        icon="🌲",
        is_dark=False,
        css_variables={
            "--bg-primary": "#f0faf0",
            "--bg-secondary": "#e2f0e2",
            "--text-primary": "#1a3a1a",
            "--text-secondary": "#4a6a4a",
            "--card-bg": "#ffffff",
            "--card-border": "#a8d8a8",
            "--input-bg": "#ffffff",
            "--input-border": "#78b878",
            "--accent": "#2d6a2d",
            "--error": "#a03030",
            "--success": "#2d6a2d",
            "--warning": "#8a6a00",
        },
    ),
    "cherry": ThemePreset(
        name="Cherry Blossom",
        icon="🌸",
        is_dark=False,
        css_variables={
            "--bg-primary": "#fff5f7",
            "--bg-secondary": "#ffe8ec",
            "--text-primary": "#5a2d3a",
            "--text-secondary": "#7a5a6a",
            "--card-bg": "#ffffff",
            "--card-border": "#f5c6d0",
            "--input-bg": "#ffffff",
            "--input-border": "#e8a0b0",
            "--accent": "#d6336c",
            "--error": "#c03030",
            "--success": "#2d7a4a",
            "--warning": "#b07a00",
        },
    ),
    "midnight": ThemePreset(
        name="Midnight Blue",
        icon="🌃",
        is_dark=True,
        css_variables={
            "--bg-primary": "#0a0e1a",
            "--bg-secondary": "#141a2e",
            "--text-primary": "#c8d0e0",
            "--text-secondary": "#7888a8",
            "--card-bg": "#1a2240",
            "--card-border": "#2a3260",
            "--input-bg": "#222a50",
            "--input-border": "#3a4280",
            "--accent": "#4f8cff",
            "--error": "#ff4757",
            "--success": "#2ed573",
            "--warning": "#ffa502",
        },
    ),
    "solarized": ThemePreset(
        name="Solarized",
        icon="☀️",
        is_dark=False,
        css_variables={
            "--bg-primary": "#fdf6e3",
            "--bg-secondary": "#eee8d5",
            "--text-primary": "#586e75",
            "--text-secondary": "#839496",
            "--card-bg": "#fdf6e3",
            "--card-border": "#eee8d5",
            "--input-bg": "#fdf6e3",
            "--input-border": "#93a1a1",
            "--accent": "#268bd2",
            "--error": "#dc322f",
            "--success": "#859900",
            "--warning": "#b58900",
        },
    ),
}


def get_preset(name: str) -> ThemePreset | None:
    return PRESETS.get(name)


def get_preset_names() -> list[str]:
    return list(PRESETS.keys())


def preset_choices() -> list[str]:
    return [f"{p.icon} {p.name}" for p in PRESETS.values()]


def css_for_preset(name: str) -> str:
    preset = get_preset(name)
    if preset is None:
        return ""
    var_declarations = "\n  ".join(
        f"{k}: {v};" for k, v in preset.css_variables.items()
    )
    return f"""<style>
:root {{
  {var_declarations}
}}
</style>"""


def apply_preset_to_session(preset_name: str, session_state: Any) -> None:
    preset = get_preset(preset_name)
    if preset:
        session_state["theme_preset"] = preset_name
        session_state["theme"] = "dark" if preset.is_dark else "light"
