"""Fetch session (5h) and weekly (7d) usage from Anthropic API.

Token resolution order:
1. CLAUDE_CODE_OAUTH_TOKEN env var
2. ~/.claude/.credentials.json → claudeAiOauth.accessToken
3. ~/.bar/tokens.json (if allthingsclaude/bar is installed)

Results are cached for 30 seconds in a temp file.
"""

from __future__ import annotations

import json
import os
import time
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CACHE_TTL = 120  # seconds — avoid rate limiting
CACHE_FILE = Path(tempfile.gettempdir()) / "claude-statusline-usage-cache.json"


@dataclass
class UsageWindow:
    utilization_pct: int  # 0-100
    reset_seconds: int    # seconds until reset


@dataclass
class UsageData:
    five_hour: UsageWindow | None
    seven_day: UsageWindow | None


def get_usage() -> UsageData | None:
    """Get usage data, from cache or API. Falls back to stale cache on errors."""
    # Try fresh cache first
    cached = _read_cache()
    if cached is not None:
        return cached

    # Get token
    token = _resolve_token()
    if not token:
        return _read_cache(ignore_ttl=True)  # stale is better than nothing

    # Fetch from API
    try:
        data = _fetch_usage(token)
        if data:
            _write_cache(data)
            return data
    except Exception:
        pass

    # API failed — return stale cache if available
    return _read_cache(ignore_ttl=True)


def _resolve_token() -> str | None:
    """Find OAuth token from available sources."""
    # 1. Environment variable
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if token:
        return token

    # 2. Claude Code credentials
    creds_path = Path.home() / ".claude" / ".credentials.json"
    if creds_path.exists():
        try:
            creds = json.loads(creds_path.read_text())
            token = creds.get("claudeAiOauth", {}).get("accessToken")
            if token:
                return token
        except (json.JSONDecodeError, KeyError):
            pass

    # 3. Bar tokens (if installed)
    bar_path = Path.home() / ".bar" / "tokens.json"
    if bar_path.exists():
        try:
            tokens = json.loads(bar_path.read_text())
            token = tokens.get("access_token")
            if token:
                return token
        except (json.JSONDecodeError, KeyError):
            pass

    return None


def _fetch_usage(token: str) -> UsageData | None:
    """Call Anthropic usage API."""
    req = Request(USAGE_URL)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("anthropic-beta", "oauth-2025-04-20")
    req.add_header("User-Agent", "claude-code-statusline/0.1.0")

    try:
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except (HTTPError, URLError, json.JSONDecodeError, TimeoutError):
        return None

    return _parse_response(data)


def _parse_response(data: dict) -> UsageData:
    """Parse API response into UsageData."""
    five_hour = _parse_window(data.get("five_hour") or data.get("fiveHour"))
    seven_day = _parse_window(data.get("seven_day") or data.get("sevenDay"))
    return UsageData(five_hour=five_hour, seven_day=seven_day)


def _parse_window(window: dict | None) -> UsageWindow | None:
    if not window:
        return None
    util = window.get("utilization", 0)
    # API returns 0-100 directly (not 0-1)
    pct = round(util) if isinstance(util, (int, float)) else 0
    reset_at = window.get("resets_at") or window.get("resetAt")
    reset_secs = _time_until(reset_at) if reset_at else 0
    return UsageWindow(utilization_pct=pct, reset_seconds=reset_secs)


def _time_until(iso_timestamp: str) -> int:
    """Seconds until a given ISO timestamp."""
    try:
        from datetime import datetime, timezone
        target = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = (target - now).total_seconds()
        return max(0, int(diff))
    except (ValueError, TypeError):
        return 0


def _format_countdown(seconds: int) -> str:
    """Format seconds into human-readable countdown."""
    if seconds <= 0:
        return "now"
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    if hours > 24:
        days = hours // 24
        remaining_hours = hours % 24
        return f"{days}d {remaining_hours}h"
    if hours > 0:
        return f"{hours}h {mins:02d}m"
    return f"{mins}m"


# ── Cache ────────────────────────────────────────────────────────

def _read_cache(ignore_ttl: bool = False) -> UsageData | None:
    if not CACHE_FILE.exists():
        return None
    try:
        raw = json.loads(CACHE_FILE.read_text())
        if not ignore_ttl and time.time() - raw.get("_ts", 0) > CACHE_TTL:
            return None
        return UsageData(
            five_hour=UsageWindow(**raw["five_hour"]) if raw.get("five_hour") else None,
            seven_day=UsageWindow(**raw["seven_day"]) if raw.get("seven_day") else None,
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def _write_cache(data: UsageData) -> None:
    try:
        raw = {
            "_ts": time.time(),
            "five_hour": {"utilization_pct": data.five_hour.utilization_pct, "reset_seconds": data.five_hour.reset_seconds} if data.five_hour else None,
            "seven_day": {"utilization_pct": data.seven_day.utilization_pct, "reset_seconds": data.seven_day.reset_seconds} if data.seven_day else None,
        }
        CACHE_FILE.write_text(json.dumps(raw))
    except OSError:
        pass
