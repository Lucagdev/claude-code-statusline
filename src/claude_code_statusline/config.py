"""Config loading/saving for the statusline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "claude-code-statusline"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class WidgetConfig:
    id: str
    fg: str | None = None  # None = use theme color


@dataclass
class LineConfig:
    widgets: list[WidgetConfig] = field(default_factory=list)


@dataclass
class StatuslineConfig:
    theme: str = "catppuccin"
    lines: list[LineConfig] = field(default_factory=list)

    def __post_init__(self):
        if not self.lines:
            self.lines = default_layout()


def default_layout() -> list[LineConfig]:
    """Clean 4-line layout inspired by allthingsclaude/bar."""
    return [
        LineConfig(widgets=[
            WidgetConfig("model_name"),
            WidgetConfig("context_usage"),
        ]),
        LineConfig(widgets=[
            WidgetConfig("session_usage"),
        ]),
        LineConfig(widgets=[
            WidgetConfig("session_cost"),
            WidgetConfig("session_duration"),
            WidgetConfig("lines_changed"),
        ]),
        LineConfig(widgets=[
            WidgetConfig("directory"),
        ]),
    ]


def load_config() -> StatuslineConfig:
    if not CONFIG_FILE.exists():
        return StatuslineConfig()
    try:
        raw = json.loads(CONFIG_FILE.read_text())
        lines = []
        for line_data in raw.get("lines", []):
            widgets = [WidgetConfig(**w) for w in line_data.get("widgets", [])]
            lines.append(LineConfig(widgets=widgets))
        return StatuslineConfig(
            theme=raw.get("theme", "catppuccin"),
            lines=lines if lines else default_layout(),
        )
    except (json.JSONDecodeError, TypeError, KeyError):
        return StatuslineConfig()


def save_config(config: StatuslineConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "theme": config.theme,
        "lines": [
            {"widgets": [_widget_to_dict(w) for w in line.widgets]}
            for line in config.lines
        ],
    }
    CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n")


def _widget_to_dict(w: WidgetConfig) -> dict:
    d: dict = {"id": w.id}
    if w.fg:
        d["fg"] = w.fg
    return d


def _detect_command() -> str:
    """Detect the best command to run the statusline based on install method."""
    import sys

    # If running from ~/.claude-statusline/, use python directly
    script_dir = Path(__file__).resolve().parent
    home_install = Path.home() / ".claude-statusline"
    if str(script_dir).startswith(str(home_install)):
        python = "python3" if sys.platform != "win32" else "python"
        path = str(home_install / 'statusline.py').replace('\\', '/')
        return f"{python} {path}"

    # Check if existing settings.json has a command configured
    settings_path = Path.home() / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
            existing = settings.get("statusLine", {}).get("command", "")
            if existing:
                return existing
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback to uvx
    return "uvx claude-code-statusline"


def install_to_claude(command: str = "") -> None:
    """Write statusLine config to ~/.claude/settings.json."""
    settings_path = Path.home() / ".claude" / "settings.json"

    if not command:
        command = _detect_command()

    if settings_path.exists():
        settings = json.loads(settings_path.read_text())
    else:
        settings = {}

    settings["statusLine"] = {
        "type": "command",
        "command": command,
        "padding": 0,
    }
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
