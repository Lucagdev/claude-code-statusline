"""Live statusline builder — single screen, always-visible preview.

The statusline preview is always at the top. Every change, hover, or navigation
updates the preview instantly. Full CRUD for widgets with live feedback.
"""

from __future__ import annotations

import sys

if sys.platform == "win32":
    import msvcrt
else:
    import tty
    import termios

from .config import (
    StatuslineConfig, LineConfig, WidgetConfig,
    load_config, save_config, install_to_claude,
)
from .themes import THEMES
from .widgets import (
    WIDGET_CATALOG, CATEGORIES, WIDGET_MAP, format_widget, RESET,
    BOLD, DIM, _hex_to_ansi_fg,
)

# ── Sample payload ───────────────────────────────────────────────

SAMPLE_PAYLOAD = {
    "model": {"id": "claude-opus-4-6[1m]", "display_name": "Opus 4.6"},
    "version": "2.1.78",
    "session_id": "a1b2c3d4e5f6a7b8",
    "exceeds_200k_tokens": False,
    "cwd": "/home/user/projetos/my-project/src",
    "workspace": {
        "current_dir": "/home/user/projetos/my-project/src",
        "project_dir": "/home/user/projetos/my-project",
    },
    "cost": {
        "total_cost_usd": 3.47,
        "total_duration_ms": 7200000,
        "total_lines_added": 245,
        "total_lines_removed": 89,
    },
    "context_window": {
        "total_input_tokens": 87000,
        "total_output_tokens": 12000,
        "context_window_size": 1000000,
        "used_percentage": 42,
        "remaining_percentage": 58,
        "current_usage": {
            "input_tokens": 87000,
            "output_tokens": 12000,
            "cache_creation_input_tokens": 15000,
            "cache_read_input_tokens": 8000,
        },
    },
    "vim": {"mode": "NORMAL"},
    "agent": {"name": "frontend-dev"},
    "worktree": {"name": "feat-login", "branch": "feat/login", "original_branch": "main"},
}

# ── ANSI helpers ─────────────────────────────────────────────────

CLEAR_SCREEN = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
ALT_SCREEN_ON = "\033[?1049h"
ALT_SCREEN_OFF = "\033[?1049l"

P = "\033[38;2;203;166;247m"   # purple
G = "\033[38;2;166;227;161m"   # green
Y = "\033[38;2;249;226;175m"   # yellow
R = "\033[38;2;243;139;168m"   # red
M = "\033[38;2;108;112;134m"   # muted/gray
W = "\033[38;2;205;214;244m"   # white
C = "\033[38;2;137;180;250m"   # cyan


def _read_key() -> str:
    if sys.platform == "win32":
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return {"H": "up", "P": "down", "M": "right", "K": "left"}.get(ch2, "")
        if ch == "\x1b":
            return "escape"
        if ch in ("\r", "\n"):
            return "enter"
        if ch == "\x03":
            return "quit"
        if ch == "\x08":
            return "backspace"
        return ch
    else:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    return {"A": "up", "B": "down", "C": "right", "D": "left"}.get(ch3, "")
                return "escape"
            if ch in ("\r", "\n"):
                return "enter"
            if ch == "\x03":
                return "quit"
            if ch == "\x7f":
                return "backspace"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ── Preview renderer ─────────────────────────────────────────────

def render_preview(config: StatuslineConfig, phantom_widget: str | None = None, phantom_line: int = -1) -> str:
    """Render preview. If phantom_widget is set, temporarily shows it added to phantom_line."""
    theme = THEMES.get(config.theme, THEMES["catppuccin"])
    sep = f" {RESET}\033[2m|\033[22m "
    output_lines: list[str] = []

    for li, line_cfg in enumerate(config.lines):
        segments: list[str] = []
        for wc in line_cfg.widgets:
            text = format_widget(wc.id, SAMPLE_PAYLOAD, theme, fg_override=wc.fg)
            if text is not None:
                segments.append(text)

        # Add phantom widget preview
        if phantom_widget and li == phantom_line:
            text = format_widget(phantom_widget, SAMPLE_PAYLOAD, theme)
            if text is not None:
                segments.append(f"\033[2m{text}\033[22m")  # dim to show it's a preview

        if segments:
            output_lines.append(sep.join(segments) + RESET)
        else:
            output_lines.append(f"{DIM}(empty){RESET}")

    return "\n".join(output_lines) if output_lines else f"{DIM}(no lines){RESET}"


def _render_line_inline(config: StatuslineConfig, line_idx: int) -> str:
    """Render a single line's widgets inline."""
    theme = THEMES.get(config.theme, THEMES["catppuccin"])
    sep = f" {RESET}{M}|{RESET} "
    segments = []
    for wc in config.lines[line_idx].widgets:
        text = format_widget(wc.id, SAMPLE_PAYLOAD, theme, fg_override=wc.fg)
        if text is not None:
            segments.append(text)
    return sep.join(segments) + RESET if segments else f"{DIM}(empty){RESET}"


# ── Modes ────────────────────────────────────────────────────────

MODE_LINES = "lines"
MODE_ADDING = "adding"
MODE_EDITING = "editing"     # editing widgets within a line
MODE_CONFIRM = "confirm"


class Builder:
    def __init__(self):
        self.config = load_config()
        self.line_cursor = 0
        self.mode = MODE_LINES
        self.widget_cursor = 0       # cursor in widget list (editing mode)
        self.add_cursor = 0          # cursor in catalog (adding mode)
        self.add_list: list = []
        self.message = ""
        self.dirty = False

    def run(self):
        if not sys.stdin.isatty():
            print("Error: interactive mode requires a terminal (TTY)")
            return

        sys.stdout.write(ALT_SCREEN_ON + HIDE_CURSOR)
        sys.stdout.flush()
        try:
            self._draw()
            while True:
                key = _read_key()
                if self._handle(key):
                    break
                self._draw()
        except Exception as e:
            sys.stdout.write(SHOW_CURSOR + ALT_SCREEN_OFF)
            sys.stdout.flush()
            print(f"Error: {e}")
            raise
        finally:
            sys.stdout.write(SHOW_CURSOR + ALT_SCREEN_OFF)
            sys.stdout.flush()

    def _handle(self, key: str) -> bool:
        self.message = ""

        if self.mode == MODE_CONFIRM:
            if key in ("q", "escape"):
                return True
            if key == "s":
                save_config(self.config)
                self.dirty = False
                self.message = f"{G}Saved!{RESET}"
                self.mode = MODE_LINES
            return False

        if self.mode == MODE_LINES:
            return self._h_lines(key)
        if self.mode == MODE_ADDING:
            self._h_adding(key)
            return False
        if self.mode == MODE_EDITING:
            self._h_editing(key)
            return False
        return False

    # ── Lines mode ───────────────────────────────────────

    def _h_lines(self, key: str) -> bool:
        if key in ("q", "escape"):
            if self.dirty:
                self.message = f"{Y}Unsaved changes! s=save, q=discard{RESET}"
                self.mode = MODE_CONFIRM
                return False
            return True
        if key == "up" and self.config.lines:
            self.line_cursor = (self.line_cursor - 1) % len(self.config.lines)
        elif key == "down" and self.config.lines:
            self.line_cursor = (self.line_cursor + 1) % len(self.config.lines)
        elif key in ("left", "right"):
            names = list(THEMES.keys())
            idx = names.index(self.config.theme) if self.config.theme in names else 0
            delta = 1 if key == "right" else -1
            self.config.theme = names[(idx + delta) % len(names)]
            self.dirty = True
        elif key == "enter" and self.config.lines:
            # Enter editing mode for current line
            widgets = self.config.lines[self.line_cursor].widgets
            self.widget_cursor = len(widgets) - 1 if widgets else 0
            self.mode = MODE_EDITING
        elif key == "a":
            self._enter_add_mode()
        elif key == "n":
            self.config.lines.append(LineConfig())
            self.line_cursor = len(self.config.lines) - 1
            self.dirty = True
            self.message = f"{G}Line {len(self.config.lines)} added{RESET}"
        elif key == "x" and self.config.lines:
            self.config.lines.pop(self.line_cursor)
            self.line_cursor = max(0, min(self.line_cursor, len(self.config.lines) - 1))
            self.dirty = True
            self.message = f"{R}Line removed{RESET}"
        elif key == "s":
            save_config(self.config)
            self.dirty = False
            self.message = f"{G}Config saved!{RESET}"
        elif key == "i":
            save_config(self.config)
            install_to_claude()
            self.dirty = False
            self.message = f"{G}Saved & installed to Claude Code!{RESET}"
        return False

    # ── Editing mode (widgets in a line) ─────────────────

    def _h_editing(self, key: str):
        widgets = self.config.lines[self.line_cursor].widgets
        if key in ("escape", "q"):
            self.mode = MODE_LINES
        elif key == "up" and widgets:
            self.widget_cursor = (self.widget_cursor - 1) % len(widgets)
        elif key == "down" and widgets:
            self.widget_cursor = (self.widget_cursor + 1) % len(widgets)
        elif key == "left" and widgets and self.widget_cursor > 0:
            # Move widget left (swap)
            i = self.widget_cursor
            widgets[i], widgets[i - 1] = widgets[i - 1], widgets[i]
            self.widget_cursor -= 1
            self.dirty = True
        elif key == "right" and widgets and self.widget_cursor < len(widgets) - 1:
            # Move widget right (swap)
            i = self.widget_cursor
            widgets[i], widgets[i + 1] = widgets[i + 1], widgets[i]
            self.widget_cursor += 1
            self.dirty = True
        elif key in ("d", "backspace", "x") and widgets:
            removed = widgets.pop(self.widget_cursor)
            w = WIDGET_MAP.get(removed.id)
            self.message = f"{R}Removed {w.label if w else removed.id}{RESET}"
            self.widget_cursor = max(0, min(self.widget_cursor, len(widgets) - 1))
            self.dirty = True
            if not widgets:
                self.mode = MODE_LINES
        elif key == "c" and widgets:
            self._cycle_widget_color()
        elif key == "r" and widgets:
            wc = widgets[self.widget_cursor]
            wc.fg = None
            self.dirty = True
            self.message = f"{M}Color reset to theme default{RESET}"
        elif key == "a":
            self._enter_add_mode()

    # ── Color cycling ─────────────────────────────────────

    def _color_options(self) -> list[tuple[str, str]]:
        """Return list of (role, hex) pairs from current theme, plus (None, None) for default."""
        theme = THEMES.get(self.config.theme, THEMES["catppuccin"])
        return [(role, hex_val) for role, hex_val in theme.colors.items()]

    def _cycle_widget_color(self):
        widgets = self.config.lines[self.line_cursor].widgets
        wc = widgets[self.widget_cursor]
        options = self._color_options()  # list of (role, hex)
        current_fg = wc.fg

        if current_fg is None:
            # None → first color
            next_role, next_hex = options[0]
        else:
            # Find current hex in options, advance to next
            current_idx = next(
                (i for i, (_, h) in enumerate(options) if h == current_fg),
                -1,
            )
            if current_idx == -1 or current_idx >= len(options) - 1:
                # Not found or at end → wrap to None (theme default)
                wc.fg = None
                self.dirty = True
                self.message = f"{M}Color: theme default{RESET}"
                return
            next_role, next_hex = options[current_idx + 1]

        wc.fg = next_hex
        self.dirty = True
        dot = f"{_hex_to_ansi_fg(next_hex)}\u25cf{RESET}"
        self.message = f"Color: {dot} {next_role} ({next_hex})"

    # ── Adding mode (widget catalog with toggle) ────────

    def _enter_add_mode(self):
        if not self.config.lines:
            self.config.lines.append(LineConfig())
            self.line_cursor = 0
            self.dirty = True
        self.add_cursor = 0
        self.mode = MODE_ADDING

    def _active_widget_ids(self) -> set[str]:
        return {w.id for w in self.config.lines[self.line_cursor].widgets}

    def _h_adding(self, key: str):
        if key in ("escape", "q"):
            self.mode = MODE_EDITING if self.config.lines[self.line_cursor].widgets else MODE_LINES
        elif key == "up":
            self.add_cursor = (self.add_cursor - 1) % len(WIDGET_CATALOG)
        elif key == "down":
            self.add_cursor = (self.add_cursor + 1) % len(WIDGET_CATALOG)
        elif key in ("enter", " "):
            w = WIDGET_CATALOG[self.add_cursor]
            widgets = self.config.lines[self.line_cursor].widgets
            existing = [i for i, wc in enumerate(widgets) if wc.id == w.id]
            if existing:
                # Remove (toggle off)
                widgets.pop(existing[0])
                self.message = f"{R}- {w.label}{RESET}"
            else:
                # Add (toggle on)
                widgets.append(WidgetConfig(id=w.id))
                self.message = f"{G}+ {w.label}{RESET}"
            self.dirty = True

    # ── Drawing ──────────────────────────────────────────

    def _draw(self):
        o = [CLEAR_SCREEN]

        theme_names = list(THEMES.keys())
        theme_idx = theme_names.index(self.config.theme) if self.config.theme in theme_names else 0
        prev_t = theme_names[(theme_idx - 1) % len(theme_names)]
        next_t = theme_names[(theme_idx + 1) % len(theme_names)]

        # ── Title + theme ────────────────────────────────
        o.append(f"  {BOLD}{P}Claude Code Statusline Builder{RESET}")
        o.append(f"  {M}{prev_t} <{RESET}  {BOLD}{P}{self.config.theme}{RESET}  {M}> {next_t}{RESET}   {DIM}arrows change theme{RESET}")
        o.append("")

        # ── Live preview (always visible) ────────────────
        phantom = None
        phantom_line = -1
        if self.mode == MODE_ADDING:
            w = WIDGET_CATALOG[self.add_cursor]
            # Only show phantom if widget is NOT already active
            if w.id not in self._active_widget_ids():
                phantom = w.id
                phantom_line = self.line_cursor

        preview = render_preview(self.config, phantom, phantom_line)
        o.append(f"  {M}{'=' * 60}{RESET}")
        for line in preview.split("\n"):
            o.append(f"    {line}")
        o.append(f"  {M}{'=' * 60}{RESET}")
        o.append("")

        # ── Lines ────────────────────────────────────────
        if not self.config.lines:
            o.append(f"  {DIM}No lines. Press n to add one.{RESET}")
        else:
            for li, line_cfg in enumerate(self.config.lines):
                is_active = li == self.line_cursor
                arrow = f"{P}>{RESET}" if is_active else " "
                lbl = f"{BOLD}{W}Line {li + 1}{RESET}" if is_active else f"{M}Line {li + 1}{RESET}"

                if self.mode == MODE_EDITING and is_active and line_cfg.widgets:
                    # Show widgets as individual items for editing
                    o.append(f"  {arrow} {lbl}")
                    theme = THEMES.get(self.config.theme, THEMES["catppuccin"])
                    for wi, wc in enumerate(line_cfg.widgets):
                        w = WIDGET_MAP.get(wc.id)
                        rendered = format_widget(wc.id, SAMPLE_PAYLOAD, theme, fg_override=wc.fg) or ""
                        is_sel = wi == self.widget_cursor
                        # Color dot indicator
                        if wc.fg:
                            color_dot = f" {_hex_to_ansi_fg(wc.fg)}\u25cf{RESET}"
                        else:
                            color_dot = ""
                        if is_sel:
                            o.append(f"      {C}>{RESET} {rendered}  {DIM}({w.label if w else wc.id}){RESET}{color_dot}")
                        else:
                            o.append(f"        {rendered}  {DIM}({w.label if w else wc.id}){RESET}{color_dot}")
                else:
                    # Show line summary
                    inline = _render_line_inline(self.config, li)
                    o.append(f"  {arrow} {lbl}  {inline}")

        # ── Adding catalog (toggle checkboxes + scroll) ──
        if self.mode == MODE_ADDING:
            active_ids = self._active_widget_ids()
            o.append("")
            o.append(f"  {BOLD}{Y}Widgets for Line {self.line_cursor + 1}:{RESET}  {DIM}enter toggle  esc done{RESET}")
            o.append("")

            try:
                import shutil
                term_h = shutil.get_terminal_size().lines
            except Exception:
                term_h = 40
            used_lines = len(o) + 5
            visible_rows = max(5, term_h - used_lines)

            total = len(WIDGET_CATALOG)
            if total <= visible_rows:
                start, end = 0, total
            else:
                half = visible_rows // 2
                start = max(0, self.add_cursor - half)
                end = start + visible_rows
                if end > total:
                    end = total
                    start = end - visible_rows

            if start > 0:
                o.append(f"    {M}  ... {start} more above ...{RESET}")

            current_cat = ""
            for i in range(start, end):
                w = WIDGET_CATALOG[i]
                if w.category != current_cat:
                    current_cat = w.category
                    o.append(f"    {M}-- {current_cat.upper()} --{RESET}")

                is_sel = i == self.add_cursor
                is_active = w.id in active_ids
                check = f"{G}x{RESET}" if is_active else " "

                if is_sel:
                    o.append(f"    {P}>{RESET} [{check}] {BOLD}{w.label:20s}{RESET} {M}{w.description}{RESET}")
                else:
                    marker = f"[{check}]" if is_active else f"{DIM}[ ]{RESET}"
                    label = f"{w.label:20s}" if is_active else f"{DIM}{w.label:20s}"
                    o.append(f"      {marker} {label} {M}{w.description}{RESET}")

            if end < total:
                o.append(f"    {M}  ... {total - end} more below ...{RESET}")

        # ── Message ──────────────────────────────────────
        if self.message:
            o.append(f"\n  {self.message}")

        # ── Keybindings ──────────────────────────────────
        o.append("")
        if self.mode == MODE_LINES:
            dirty = f"  {Y}*{RESET}" if self.dirty else ""
            o.append(
                f"  {M}enter{RESET} edit line  "
                f"{M}a{RESET} add  "
                f"{M}n{RESET} new line  "
                f"{M}x{RESET} del line  "
                f"{M}s{RESET} save  "
                f"{M}i{RESET} install  "
                f"{M}q{RESET} quit{dirty}"
            )
        elif self.mode == MODE_EDITING:
            o.append(
                f"  {M}up/dn{RESET} select  "
                f"{M}left/right{RESET} reorder  "
                f"{M}a{RESET} add  "
                f"{M}d{RESET} remove  "
                f"{M}c{RESET} color  "
                f"{M}r{RESET} reset color  "
                f"{M}esc{RESET} back"
            )
        elif self.mode == MODE_ADDING:
            o.append(
                f"  {M}up/dn{RESET} browse  "
                f"{M}enter{RESET} add  "
                f"{M}esc{RESET} done"
            )
        elif self.mode == MODE_CONFIRM:
            o.append(f"  {M}s{RESET} save  {M}q{RESET} discard & quit")

        sys.stdout.write("\n".join(o) + "\n")
        sys.stdout.flush()


def main():
    builder = Builder()
    builder.run()


if __name__ == "__main__":
    main()
