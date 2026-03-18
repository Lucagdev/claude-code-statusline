"""Renderer — reads JSON from stdin, outputs clean statusline to stdout.

Design inspired by allthingsclaude/bar: clean separators, progress bars,
semantic line grouping. No powerline arrows — minimal and readable.
"""

from __future__ import annotations

import json
import sys

from .config import load_config
from .themes import THEMES
from .widgets import format_widget, reset_usage_cache, _hex_to_ansi_fg, RESET


def render(data: dict) -> str:
    reset_usage_cache()  # fresh usage data each render
    config = load_config()
    theme = THEMES.get(config.theme, THEMES["tokyo-night"])
    sep = f" {RESET}\033[2m│\033[22m "  # dim pipe separator

    output_lines: list[str] = []

    for line_cfg in config.lines:
        segments: list[str] = []

        for wc in line_cfg.widgets:
            text = format_widget(wc.id, data, theme, fg_override=wc.fg)
            if text is None:
                continue
            segments.append(text)

        if segments:
            output_lines.append(sep.join(segments) + RESET)

    return "\n".join(output_lines)


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, EOFError, ValueError):
        data = {}

    output = render(data)
    if output:
        print(output)
