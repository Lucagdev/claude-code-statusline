"""Single entry point — detects context and acts accordingly.

- TTY (user ran manually): opens interactive setup wizard
- Pipe (Claude Code calling): renders statusline from stdin JSON
- CLI args: handles subcommands (--config, --theme, --help)
"""

from __future__ import annotations

import argparse
import sys


def entry():
    # Ensure stdout supports Unicode on Windows
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="claude-code-statusline",
        description="Beautiful, customizable statusline for Claude Code CLI",
    )
    parser.add_argument(
        "--config", action="store_true",
        help="Open the interactive TUI configurator",
    )
    parser.add_argument(
        "--theme", type=str, metavar="NAME",
        help="Set theme (catppuccin, tokyo-night, gruvbox, nord, dracula, rose-pine, warm)",
    )
    parser.add_argument(
        "--install", action="store_true",
        help="Install statusline to Claude Code settings",
    )
    parser.add_argument(
        "--list-themes", action="store_true",
        help="List available themes",
    )
    parser.add_argument(
        "--list-widgets", action="store_true",
        help="List available widgets",
    )

    # If stdin is a pipe (Claude Code calling), skip arg parsing and render
    if not sys.stdin.isatty():
        _render_mode()
        return

    args = parser.parse_args()

    if args.list_themes:
        _list_themes()
    elif args.list_widgets:
        _list_widgets()
    elif args.theme:
        _set_theme(args.theme)
    elif args.install:
        _install()
    elif args.config:
        _open_config()
    else:
        # Default: open the live builder
        _open_config()


def _render_mode():
    """Read JSON from stdin, render statusline."""
    import json
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, EOFError, ValueError):
        data = {}

    from .render import render
    output = render(data)
    if output:
        print(output)


def _render_preview_for_theme(theme_name: str, layout: str = "default"):
    """Render a preview statusline with the given theme. Used as on_change callback."""
    from .config import StatuslineConfig, LineConfig, WidgetConfig, default_layout
    from .configure import SAMPLE_PAYLOAD, render_preview

    config = StatuslineConfig(theme=theme_name, lines=_get_layout_lines(layout))
    output = render_preview(config)
    # Print each line (the preview area)
    for line in output.split("\n"):
        sys.stdout.write(f"  {line}\n")
    sys.stdout.flush()


def _render_preview_for_layout(layout_name: str, theme: str):
    """Render a preview for a given layout preset."""
    from .config import StatuslineConfig
    from .configure import SAMPLE_PAYLOAD, render_preview

    config = StatuslineConfig(theme=theme, lines=_get_layout_lines(layout_name))
    output = render_preview(config)
    for line in output.split("\n"):
        sys.stdout.write(f"  {line}\n")
    # Pad remaining lines if layout has fewer lines
    lines_count = len(output.split("\n"))
    for _ in range(3 - lines_count):
        sys.stdout.write(f"  \n")
    sys.stdout.flush()


def _get_layout_lines(layout: str):
    from .config import LineConfig, WidgetConfig, default_layout

    if layout == "minimal":
        return [
            LineConfig(widgets=[
                WidgetConfig("model_name"),
                WidgetConfig("context_percent"),
                WidgetConfig("session_cost"),
            ]),
        ]
    elif layout == "full":
        return [
            LineConfig(widgets=[
                WidgetConfig("model_name"),
                WidgetConfig("context_usage"),
            ]),
            LineConfig(widgets=[
                WidgetConfig("session_cost"),
                WidgetConfig("session_duration"),
                WidgetConfig("lines_changed"),
                WidgetConfig("version"),
            ]),
            LineConfig(widgets=[
                WidgetConfig("directory"),
                WidgetConfig("vim_mode"),
                WidgetConfig("git_branch"),
            ]),
        ]
    else:
        return default_layout()


def _setup_wizard():
    """Fully interactive setup wizard with arrow-key navigation and live preview."""
    from .themes import THEMES
    from .config import (
        StatuslineConfig, load_config, save_config,
        install_to_claude, CONFIG_FILE,
    )
    from .selector import select_option

    # Banner
    print("\033[1m\033[38;2;203;166;247m")
    print("  ┌─────────────────────────────────────────┐")
    print("  │     Claude Code Statusline               │")
    print("  │     Beautiful, customizable status bar    │")
    print("  └─────────────────────────────────────────┘")
    print("\033[0m")

    config = load_config()

    # ── Step 1: Theme ────────────────────────────────────────
    theme_names = list(THEMES.keys())
    theme_options = [
        (name, f"{name:15s} \033[2m{THEMES[name].description}\033[0m")
        for name in theme_names
    ]
    default_idx = theme_names.index(config.theme) if config.theme in theme_names else 0

    def on_theme_change(idx, theme_id):
        _render_preview_for_theme(theme_id)

    print("  \033[1mStep 1/3\033[0m \033[2m─ Choose a theme (↑↓ navigate, enter confirm)\033[0m")

    theme_idx = select_option(
        title="Theme",
        options=theme_options,
        default=default_idx,
        on_change=on_theme_change,
        preview_lines=3,
    )

    if theme_idx is None:
        print("  \033[2mCancelled.\033[0m")
        return

    config.theme = theme_names[theme_idx]

    # ── Step 2: Layout ───────────────────────────────────────
    layout_options = [
        ("default", "Default    \033[2m3 lines: model+context, cost+duration+lines, directory\033[0m"),
        ("minimal", "Minimal    \033[2m1 line: model, context%, cost\033[0m"),
        ("full",    "Full       \033[2m3 lines: all widgets including vim, git, version\033[0m"),
        ("custom",  "Custom     \033[2mopen TUI configurator for full control\033[0m"),
    ]

    def on_layout_change(idx, layout_id):
        if layout_id != "custom":
            _render_preview_for_layout(layout_id, config.theme)
        else:
            sys.stdout.write("  \033[2mOpens interactive TUI with full widget control\033[0m\n")
            sys.stdout.write("  \n")
            sys.stdout.write("  \n")
            sys.stdout.flush()

    print("  \033[1mStep 2/3\033[0m \033[2m─ Choose a layout\033[0m")

    layout_idx = select_option(
        title="Layout",
        options=layout_options,
        default=0,
        on_change=on_layout_change,
        preview_lines=3,
    )

    if layout_idx is None:
        print("  \033[2mCancelled.\033[0m")
        return

    layout_id = layout_options[layout_idx][0]

    if layout_id == "custom":
        config.lines = _get_layout_lines("default")
        save_config(config)
        _open_config()
        return

    config.lines = _get_layout_lines(layout_id)

    # ── Step 3: Install ──────────────────────────────────────
    print("  \033[1mStep 3/3\033[0m \033[2m─ Install to Claude Code\033[0m")

    install_options = [
        ("yes", "Yes — install to ~/.claude/settings.json"),
        ("no",  "No  — just save the config"),
    ]

    install_idx = select_option(
        title="Install",
        options=install_options,
        default=0,
    )

    save_config(config)

    if install_idx == 0:
        install_to_claude(command="uvx claude-code-statusline")
        print("  \033[32m✓ Installed!\033[0m Restart Claude Code to see your statusline.\n")
    else:
        print(f"  \033[32m✓ Config saved!\033[0m at {CONFIG_FILE}")
        print(f"    To install later: claude-code-statusline --install\n")

    # Final preview
    print("  \033[1mYour statusline:\033[0m\n")
    from .configure import SAMPLE_PAYLOAD, render_preview
    output = render_preview(config)
    for line in output.split("\n"):
        print(f"  {line}")

    print(f"\n  \033[2mReconfigure anytime: claude-code-statusline")
    print(f"  TUI editor:         claude-code-statusline --config")
    print(f"  Config file:        {CONFIG_FILE}\033[0m\n")


def _open_config():
    """Open the TUI configurator."""
    from .configure import main as tui_main
    tui_main()


def _set_theme(name: str):
    from .themes import THEMES
    from .config import load_config, save_config

    if name not in THEMES:
        print(f"Unknown theme: {name}")
        print(f"Available: {', '.join(THEMES.keys())}")
        return

    config = load_config()
    config.theme = name
    save_config(config)
    print(f"Theme set to: {name}")


def _list_themes():
    from .themes import THEMES
    from .config import load_config

    current = load_config().theme
    print("\033[1mAvailable themes:\033[0m\n")
    for name, t in THEMES.items():
        marker = " ◂" if name == current else ""
        print(f"  {name:15s} — {t.description}{marker}")


def _list_widgets():
    from .widgets import WIDGET_CATALOG, CATEGORIES

    print("\033[1mAvailable widgets:\033[0m\n")
    for cat in CATEGORIES:
        print(f"  \033[2m── {cat.upper()} ──\033[0m")
        for w in WIDGET_CATALOG:
            if w.category == cat:
                print(f"    {w.id:20s} {w.description}")
        print()


def _install():
    from .config import install_to_claude
    install_to_claude(command="uvx claude-code-statusline")
    print("\033[32m✓ Installed to Claude Code!\033[0m")
    print("  Restart Claude Code to see your statusline.")
