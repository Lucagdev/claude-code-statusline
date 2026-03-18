"""Interactive arrow-key selector for terminal.

Renders a list of options, highlights current selection,
and calls a callback on each move for live preview.
"""

from __future__ import annotations

import sys
import tty
import termios


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR_LINE = "\033[2K"


def _read_key() -> str:
    """Read a single keypress, handling arrow keys."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                if ch3 == "A":
                    return "up"
                elif ch3 == "B":
                    return "down"
                elif ch3 == "C":
                    return "right"
                elif ch3 == "D":
                    return "left"
            return "escape"
        elif ch in ("\r", "\n"):
            return "enter"
        elif ch == "q":
            return "quit"
        elif ch == "\x03":  # Ctrl+C
            return "quit"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _move_up(n: int):
    if n > 0:
        sys.stdout.write(f"\033[{n}A")


def _move_down(n: int):
    if n > 0:
        sys.stdout.write(f"\033[{n}B")


def select_option(
    title: str,
    options: list[tuple[str, str]],  # (id, display_text)
    default: int = 0,
    on_change: callable = None,  # callback(index, option_id) for live preview
    preview_lines: int = 0,  # how many lines the preview uses below the list
) -> int | None:
    """Interactive selector with arrow keys. Returns selected index or None if cancelled.

    Args:
        title: Header text
        options: List of (id, display_text) tuples
        default: Default selected index
        on_change: Called on each navigation with (index, option_id)
        preview_lines: Number of lines the on_change callback prints below the list
    """
    current = default
    total_lines = len(options)

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()

    def _render(clear_preview: bool = False):
        # Move to start
        sys.stdout.write(f"\r")

        for i, (opt_id, display) in enumerate(options):
            sys.stdout.write(CLEAR_LINE)
            if i == current:
                sys.stdout.write(f"  {BOLD}\033[38;2;203;166;247m❯ {display}{RESET}\n")
            else:
                sys.stdout.write(f"  {DIM}  {display}{RESET}\n")

        # Clear preview area
        if preview_lines > 0:
            sys.stdout.write("\n")  # blank line before preview
            for _ in range(preview_lines):
                sys.stdout.write(CLEAR_LINE + "\n")
            # Move back up to after the list
            _move_up(preview_lines + 1)

        sys.stdout.flush()

        # Call preview callback
        if on_change:
            sys.stdout.write("\n")  # blank line
            on_change(current, options[current][0])
            sys.stdout.flush()
            # Move back up: preview_lines + 1 (blank line)
            _move_up(preview_lines + 1)

        # Move back to top of list
        _move_up(total_lines)

    # Print title
    sys.stdout.write(f"\n  {BOLD}{title}{RESET}\n\n")
    sys.stdout.flush()

    _render()

    try:
        while True:
            key = _read_key()

            if key == "up":
                current = (current - 1) % total_lines
                _render()
            elif key == "down":
                current = (current + 1) % total_lines
                _render()
            elif key == "enter":
                # Move cursor past the list + preview
                _move_down(total_lines)
                if preview_lines > 0:
                    _move_down(preview_lines + 1)
                sys.stdout.write("\n")
                sys.stdout.write(SHOW_CURSOR)
                sys.stdout.flush()
                return current
            elif key in ("quit", "escape"):
                _move_down(total_lines)
                if preview_lines > 0:
                    _move_down(preview_lines + 1)
                sys.stdout.write("\n")
                sys.stdout.write(SHOW_CURSOR)
                sys.stdout.flush()
                return None
    except Exception:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()
        raise


def select_multi(
    title: str,
    options: list[tuple[str, str, bool]],  # (id, display, initially_selected)
    on_change: callable = None,
    preview_lines: int = 0,
) -> list[str] | None:
    """Multi-select with space to toggle, enter to confirm. Returns list of selected IDs."""
    current = 0
    selected = [s for _, _, s in options]
    total_lines = len(options)

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()

    def _render():
        sys.stdout.write(f"\r")

        for i, (opt_id, display, _) in enumerate(options):
            sys.stdout.write(CLEAR_LINE)
            check = "\033[38;2;166;227;161m✓" if selected[i] else " "
            if i == current:
                sys.stdout.write(f"  {BOLD}\033[38;2;203;166;247m❯ [{check}{BOLD}\033[38;2;203;166;247m] {display}{RESET}\n")
            else:
                sys.stdout.write(f"  {DIM}  [{check}{DIM}] {display}{RESET}\n")

        if preview_lines > 0:
            sys.stdout.write("\n")
            for _ in range(preview_lines):
                sys.stdout.write(CLEAR_LINE + "\n")
            _move_up(preview_lines + 1)

        sys.stdout.flush()

        if on_change:
            active_ids = [options[i][0] for i in range(len(options)) if selected[i]]
            sys.stdout.write("\n")
            on_change(active_ids)
            sys.stdout.flush()
            _move_up(preview_lines + 1)

        _move_up(total_lines)

    sys.stdout.write(f"\n  {BOLD}{title}{RESET}  {DIM}(space=toggle, enter=confirm){RESET}\n\n")
    sys.stdout.flush()

    _render()

    try:
        while True:
            key = _read_key()

            if key == "up":
                current = (current - 1) % total_lines
                _render()
            elif key == "down":
                current = (current + 1) % total_lines
                _render()
            elif key == " ":
                selected[current] = not selected[current]
                _render()
            elif key == "enter":
                _move_down(total_lines)
                if preview_lines > 0:
                    _move_down(preview_lines + 1)
                sys.stdout.write("\n" + SHOW_CURSOR)
                sys.stdout.flush()
                return [options[i][0] for i in range(len(options)) if selected[i]]
            elif key in ("quit", "escape"):
                _move_down(total_lines)
                if preview_lines > 0:
                    _move_down(preview_lines + 1)
                sys.stdout.write("\n" + SHOW_CURSOR)
                sys.stdout.flush()
                return None
    except Exception:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()
        raise
