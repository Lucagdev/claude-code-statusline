"""Widget definitions — each widget extracts + formats data from the Claude Code payload.

Design: clean text with color accents, no heavy backgrounds.
All data comes from the JSON stdin payload — no API calls, no subprocess.
"""

from __future__ import annotations

from dataclasses import dataclass


# ── ANSI helpers ─────────────────────────────────────────────────

def _hex_to_ansi_fg(hex_color: str) -> str:
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return f"\033[38;2;{r};{g};{b}m"


RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"


# ── Widget registry ──────────────────────────────────────────────

@dataclass
class WidgetDef:
    id: str
    label: str
    category: str
    description: str


WIDGET_CATALOG: list[WidgetDef] = [
    # Model / Session
    WidgetDef("model_name",      "Model Name",      "model",     "Opus 4.6 (1M)"),
    WidgetDef("model_id",        "Model ID",        "model",     "claude-opus-4-6"),
    WidgetDef("session_cost",    "Session Cost",    "model",     "$3.47"),
    WidgetDef("session_duration","Duration",         "model",     "2h 00m"),
    WidgetDef("version",         "CC Version",      "model",     "v2.1.78"),
    WidgetDef("session_id",      "Session ID",      "model",     "abc123 (short)"),

    # Context
    WidgetDef("context_usage",   "Context Usage",   "context",   "87k/1.0M [bar] 42%"),
    WidgetDef("context_percent", "Context %",       "context",   "42%"),
    WidgetDef("context_bar",     "Context Bar",     "context",   "[████░░░░░░]"),
    WidgetDef("context_remaining","Ctx Remaining",  "context",   "58% free"),
    WidgetDef("tokens_in",       "Tokens In",       "context",   "87k in"),
    WidgetDef("tokens_out",      "Tokens Out",      "context",   "12k out"),
    WidgetDef("tokens_total",    "Tokens Total",    "context",   "99k total"),
    WidgetDef("tokens_cache",    "Cache Tokens",    "context",   "5k created, 2k read"),
    WidgetDef("context_warning", "Ctx Warning",     "context",   "! HIGH (80%+)"),

    # Code
    WidgetDef("lines_changed",   "Lines Changed",   "code",      "+245 -89"),
    WidgetDef("lines_added",     "Lines Added",     "code",      "+245"),
    WidgetDef("lines_removed",   "Lines Removed",   "code",      "-89"),

    # Workspace
    WidgetDef("directory",       "Directory",       "workspace", "~/projetos/app/src"),
    WidgetDef("project_dir",     "Project Dir",     "workspace", "~/projetos/app"),

    # Git / Worktree
    WidgetDef("git_branch",      "Git Branch",      "git",       "feat/login"),
    WidgetDef("worktree_name",   "Worktree Name",   "git",       "feat-login"),
    WidgetDef("worktree_branch", "Worktree Branch", "git",       "worktree-feat-login"),
    WidgetDef("original_branch", "Original Branch", "git",       "main"),

    # Usage (API — 5h session + 7d weekly limits)
    WidgetDef("session_usage",   "Session Usage",   "usage",     "Session [bar] 19% resets 4h"),
    WidgetDef("session_pct",     "Session %",       "usage",     "19%"),
    WidgetDef("session_bar",     "Session Bar",     "usage",     "[██░░░░░░░░]"),
    WidgetDef("session_reset",   "Session Reset",   "usage",     "resets 4h 31m"),
    WidgetDef("weekly_usage",    "Weekly Usage",    "usage",     "Weekly [bar] 42% resets 47h"),
    WidgetDef("weekly_pct",      "Weekly %",        "usage",     "42%"),
    WidgetDef("weekly_bar",      "Weekly Bar",      "usage",     "[████░░░░░░]"),
    WidgetDef("weekly_reset",    "Weekly Reset",    "usage",     "resets 2d 5h"),

    # State
    WidgetDef("vim_mode",        "Vim Mode",        "state",     "NORMAL / INSERT"),
    WidgetDef("agent_name",      "Agent Name",      "state",     "security-reviewer"),
    WidgetDef("exceeds_200k",    "200k+ Warning",   "state",     "! when >200k tokens"),
]

WIDGET_MAP: dict[str, WidgetDef] = {w.id: w for w in WIDGET_CATALOG}
CATEGORIES = ["model", "context", "usage", "code", "workspace", "git", "state"]


# ── Formatting helpers ───────────────────────────────────────────

def _shorten_path(path: str) -> str:
    if not path:
        return ""
    parts = path.rstrip("/").split("/")
    if len(parts) > 2 and parts[1] == "home":
        home = f"/home/{parts[2]}"
        if path.startswith(home):
            return "~" + path[len(home):]
    return path


def _format_duration(ms: float | None) -> str:
    if not ms:
        return "0m"
    total_secs = int(ms / 1000)
    hours = total_secs // 3600
    mins = (total_secs % 3600) // 60
    if hours > 0:
        return f"{hours}h {mins:02d}m"
    return f"{mins}m"


def _format_tokens(n: int | None) -> str:
    if not n:
        return "0"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def _progress_bar(pct: float | None, width: int = 10) -> str:
    if pct is None:
        pct = 0
    pct = min(100, max(0, pct))
    filled = round(pct / 100 * width)
    empty = width - filled
    return "\u2588" * filled + "\u2591" * empty


def _pct_color(pct: float | None, theme) -> str:
    if pct is None:
        pct = 0
    if pct >= 80:
        return theme.colors.get("danger", "#f38ba8")
    if pct >= 60:
        return theme.colors.get("warning", "#f9e2af")
    return theme.colors.get("accent", "#89b4fa")


# ── Widget formatters ────────────────────────────────────────────

def format_widget(widget_id: str, data: dict, theme, fg_override: str | None = None) -> str | None:
    """Return formatted ANSI string for a widget, or None if data unavailable.

    If fg_override is set (a hex color like '#a6e3a1'), ALL foreground colors
    in the output are replaced with the override color.
    """
    result = _format_widget_inner(widget_id, data, theme)
    if result is None:
        return None
    if fg_override:
        import re
        fg_code = _hex_to_ansi_fg(fg_override)
        # Replace all fg color codes (38;2;R;G;B) with the override
        result = re.sub(r'\033\[38;2;\d+;\d+;\d+m', fg_code, result)
        # Re-apply override after every RESET so color persists
        result = result.replace(RESET, RESET + fg_code)
        # Wrap with override and end with clean RESET
        return f"{fg_code}{result}{RESET}"
    return result


def _format_widget_inner(widget_id: str, data: dict, theme) -> str | None:
    """Internal: format without fg_override."""
    w = WIDGET_MAP.get(widget_id)
    if not w:
        return None

    match widget_id:
        # ── Model / Session ──────────────────────────────
        case "model_name":
            name = _safe_get(data, "model", "display_name")
            if not name:
                return None
            model_id = _safe_get(data, "model", "id") or ""
            ctx_size = _safe_get(data, "context_window", "context_window_size") or 0
            if "1m" in model_id.lower() or ctx_size >= 1_000_000:
                name += " (1M)"
            color = theme.colors.get("primary", "#c0caf5")
            return f"{BOLD}{_hex_to_ansi_fg(color)}{name}{RESET}"

        case "model_id":
            mid = _safe_get(data, "model", "id")
            if not mid:
                return None
            color = theme.colors.get("muted", "#6c7086")
            return f"{_hex_to_ansi_fg(color)}{mid}{RESET}"

        case "session_cost":
            cost = _safe_get(data, "cost", "total_cost_usd")
            val = f"${cost:.2f}" if cost else "$0.00"
            color = theme.colors.get("success", "#a6e3a1")
            return f"{_hex_to_ansi_fg(color)}{val}{RESET}"

        case "session_duration":
            ms = _safe_get(data, "cost", "total_duration_ms")
            color = theme.colors.get("muted", "#6c7086")
            return f"{_hex_to_ansi_fg(color)}{_format_duration(ms)}{RESET}"

        case "version":
            v = data.get("version")
            if not v:
                return None
            color = theme.colors.get("muted", "#6c7086")
            return f"{_hex_to_ansi_fg(color)}v{v}{RESET}"

        case "session_id":
            sid = data.get("session_id")
            if not sid:
                return None
            color = theme.colors.get("muted", "#6c7086")
            short = sid[:8] if len(sid) > 8 else sid
            return f"{_hex_to_ansi_fg(color)}{short}{RESET}"

        # ── Context ──────────────────────────────────────
        case "context_usage":
            pct = _safe_get(data, "context_window", "used_percentage")
            total_in = _safe_get(data, "context_window", "total_input_tokens") or 0
            ctx_size = _safe_get(data, "context_window", "context_window_size") or 0
            bar_color = _pct_color(pct, theme)
            muted = theme.colors.get("muted", "#6c7086")
            pct_val = pct if pct is not None else 0
            bar = _progress_bar(pct_val)
            return (
                f"{_hex_to_ansi_fg(muted)}{_format_tokens(total_in)}/{_format_tokens(ctx_size)}"
                f" {_hex_to_ansi_fg(bar_color)}[{bar}]"
                f" {BOLD}{pct_val}%{RESET}"
            )

        case "context_percent":
            pct = _safe_get(data, "context_window", "used_percentage")
            pct_val = pct if pct is not None else 0
            color = _pct_color(pct, theme)
            return f"{_hex_to_ansi_fg(color)}{pct_val}%{RESET}"

        case "context_bar":
            pct = _safe_get(data, "context_window", "used_percentage")
            color = _pct_color(pct, theme)
            return f"{_hex_to_ansi_fg(color)}[{_progress_bar(pct)}]{RESET}"

        case "context_remaining":
            pct = _safe_get(data, "context_window", "remaining_percentage")
            if pct is None:
                used = _safe_get(data, "context_window", "used_percentage")
                pct = (100 - used) if used is not None else 0
            color = theme.colors.get("info", "#89b4fa")
            return f"{_hex_to_ansi_fg(color)}{pct}% free{RESET}"

        case "tokens_in":
            t = _safe_get(data, "context_window", "total_input_tokens")
            color = theme.colors.get("info", "#89b4fa")
            return f"{_hex_to_ansi_fg(color)}{_format_tokens(t)} in{RESET}"

        case "tokens_out":
            t = _safe_get(data, "context_window", "total_output_tokens")
            color = theme.colors.get("secondary", "#cba6f7")
            return f"{_hex_to_ansi_fg(color)}{_format_tokens(t)} out{RESET}"

        case "tokens_total":
            t_in = _safe_get(data, "context_window", "total_input_tokens") or 0
            t_out = _safe_get(data, "context_window", "total_output_tokens") or 0
            color = theme.colors.get("text", "#bac2de")
            return f"{_hex_to_ansi_fg(color)}{_format_tokens(t_in + t_out)} total{RESET}"

        case "tokens_cache":
            created = _safe_get(data, "context_window", "current_usage", "cache_creation_input_tokens") or 0
            read = _safe_get(data, "context_window", "current_usage", "cache_read_input_tokens") or 0
            if not created and not read:
                return None
            muted = theme.colors.get("muted", "#6c7086")
            parts = []
            if created:
                parts.append(f"{_format_tokens(created)} cached")
            if read:
                parts.append(f"{_format_tokens(read)} hit")
            return f"{_hex_to_ansi_fg(muted)}{', '.join(parts)}{RESET}"

        case "context_warning":
            pct = _safe_get(data, "context_window", "used_percentage")
            if pct is None or pct < 80:
                return None
            color = theme.colors.get("danger", "#f38ba8")
            if pct >= 95:
                return f"{BOLD}{_hex_to_ansi_fg(color)}!! CRITICAL {pct}%{RESET}"
            return f"{BOLD}{_hex_to_ansi_fg(color)}! HIGH {pct}%{RESET}"

        # ── Code ─────────────────────────────────────────
        case "lines_changed":
            added = _safe_get(data, "cost", "total_lines_added") or 0
            removed = _safe_get(data, "cost", "total_lines_removed") or 0
            c_add = theme.colors.get("success", "#a6e3a1")
            c_rem = theme.colors.get("danger", "#f38ba8")
            return f"{_hex_to_ansi_fg(c_add)}+{added}{RESET} {_hex_to_ansi_fg(c_rem)}-{removed}{RESET}"

        case "lines_added":
            n = _safe_get(data, "cost", "total_lines_added") or 0
            color = theme.colors.get("success", "#a6e3a1")
            return f"{_hex_to_ansi_fg(color)}+{n}{RESET}"

        case "lines_removed":
            n = _safe_get(data, "cost", "total_lines_removed") or 0
            color = theme.colors.get("danger", "#f38ba8")
            return f"{_hex_to_ansi_fg(color)}-{n}{RESET}"

        # ── Workspace ────────────────────────────────────
        case "directory":
            d = data.get("cwd") or _safe_get(data, "workspace", "current_dir")
            if not d:
                return None
            color = theme.colors.get("muted", "#6c7086")
            return f"{_hex_to_ansi_fg(color)}{_shorten_path(d)}{RESET}"

        case "project_dir":
            d = _safe_get(data, "workspace", "project_dir")
            if not d:
                return None
            color = theme.colors.get("muted", "#6c7086")
            return f"{_hex_to_ansi_fg(color)}{_shorten_path(d)}{RESET}"

        # ── Git / Worktree ───────────────────────────────
        case "git_branch":
            branch = (
                _safe_get(data, "worktree", "branch")
                or _safe_get(data, "worktree", "original_branch")
            )
            if not branch:
                return None
            color = theme.colors.get("accent", "#89b4fa")
            return f"{_hex_to_ansi_fg(color)}{branch}{RESET}"

        case "worktree_name":
            name = _safe_get(data, "worktree", "name")
            if not name:
                return None
            color = theme.colors.get("info", "#89b4fa")
            return f"{_hex_to_ansi_fg(color)}{name}{RESET}"

        case "worktree_branch":
            branch = _safe_get(data, "worktree", "branch")
            if not branch:
                return None
            color = theme.colors.get("info", "#89b4fa")
            return f"{_hex_to_ansi_fg(color)}{branch}{RESET}"

        case "original_branch":
            branch = _safe_get(data, "worktree", "original_branch")
            if not branch:
                return None
            color = theme.colors.get("muted", "#6c7086")
            return f"{_hex_to_ansi_fg(color)}{branch}{RESET}"

        # ── Usage (API data) ──────────────────────────────
        case "session_usage":
            usage = _get_usage_data(data)
            if not usage or not usage.five_hour:
                return None
            u = usage.five_hour
            bar_color = _pct_color(u.utilization_pct, theme)
            muted = theme.colors.get("muted", "#6c7086")
            primary = theme.colors.get("primary", "#c0caf5")
            bar = _progress_bar(u.utilization_pct)
            from .usage import _format_countdown
            reset = _format_countdown(u.reset_seconds)
            return (
                f"{BOLD}{_hex_to_ansi_fg(primary)}Session{RESET}"
                f" {_hex_to_ansi_fg(bar_color)}[{bar}] {BOLD}{u.utilization_pct}%{RESET}"
                f" {_hex_to_ansi_fg(muted)}resets {reset}{RESET}"
            )

        case "session_pct":
            usage = _get_usage_data(data)
            if not usage or not usage.five_hour:
                return None
            color = _pct_color(usage.five_hour.utilization_pct, theme)
            return f"{_hex_to_ansi_fg(color)}{usage.five_hour.utilization_pct}%{RESET}"

        case "session_bar":
            usage = _get_usage_data(data)
            if not usage or not usage.five_hour:
                return None
            color = _pct_color(usage.five_hour.utilization_pct, theme)
            return f"{_hex_to_ansi_fg(color)}[{_progress_bar(usage.five_hour.utilization_pct)}]{RESET}"

        case "session_reset":
            usage = _get_usage_data(data)
            if not usage or not usage.five_hour:
                return None
            from .usage import _format_countdown
            muted = theme.colors.get("muted", "#6c7086")
            return f"{_hex_to_ansi_fg(muted)}resets {_format_countdown(usage.five_hour.reset_seconds)}{RESET}"

        case "weekly_usage":
            usage = _get_usage_data(data)
            if not usage or not usage.seven_day:
                return None
            u = usage.seven_day
            bar_color = _pct_color(u.utilization_pct, theme)
            muted = theme.colors.get("muted", "#6c7086")
            primary = theme.colors.get("primary", "#c0caf5")
            bar = _progress_bar(u.utilization_pct)
            from .usage import _format_countdown
            reset = _format_countdown(u.reset_seconds)
            return (
                f"{BOLD}{_hex_to_ansi_fg(primary)}Weekly{RESET}"
                f" {_hex_to_ansi_fg(bar_color)}[{bar}] {BOLD}{u.utilization_pct}%{RESET}"
                f" {_hex_to_ansi_fg(muted)}resets {reset}{RESET}"
            )

        case "weekly_pct":
            usage = _get_usage_data(data)
            if not usage or not usage.seven_day:
                return None
            color = _pct_color(usage.seven_day.utilization_pct, theme)
            return f"{_hex_to_ansi_fg(color)}{usage.seven_day.utilization_pct}%{RESET}"

        case "weekly_bar":
            usage = _get_usage_data(data)
            if not usage or not usage.seven_day:
                return None
            color = _pct_color(usage.seven_day.utilization_pct, theme)
            return f"{_hex_to_ansi_fg(color)}[{_progress_bar(usage.seven_day.utilization_pct)}]{RESET}"

        case "weekly_reset":
            usage = _get_usage_data(data)
            if not usage or not usage.seven_day:
                return None
            from .usage import _format_countdown
            muted = theme.colors.get("muted", "#6c7086")
            return f"{_hex_to_ansi_fg(muted)}resets {_format_countdown(usage.seven_day.reset_seconds)}{RESET}"

        # ── State ────────────────────────────────────────
        case "vim_mode":
            mode = _safe_get(data, "vim", "mode")
            if not mode:
                return None
            color = theme.colors.get("warning", "#f9e2af")
            return f"{BOLD}{_hex_to_ansi_fg(color)}{mode}{RESET}"

        case "agent_name":
            name = _safe_get(data, "agent", "name")
            if not name:
                return None
            color = theme.colors.get("secondary", "#cba6f7")
            return f"{_hex_to_ansi_fg(color)}{name}{RESET}"

        case "exceeds_200k":
            exceeds = data.get("exceeds_200k_tokens")
            if not exceeds:
                return None
            color = theme.colors.get("warning", "#f9e2af")
            return f"{BOLD}{_hex_to_ansi_fg(color)}200k+{RESET}"

    return None


_usage_cache = None

def _get_usage_data(data: dict):
    """Get usage data (cached per render cycle)."""
    global _usage_cache
    if _usage_cache is not None:
        return _usage_cache
    try:
        from .usage import get_usage
        _usage_cache = get_usage()
    except Exception:
        _usage_cache = None
    return _usage_cache


def reset_usage_cache():
    """Call at start of each render cycle."""
    global _usage_cache
    _usage_cache = None


def _safe_get(data: dict, *keys: str):
    current = data
    for k in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(k)
    return current
