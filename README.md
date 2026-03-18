# claude-code-statusline

Beautiful, customizable statusline for Claude Code CLI.

---

## Install

**Linux / macOS / WSL**

```bash
curl -fsSL https://raw.githubusercontent.com/Lucagdev/claude-code-statusline/main/install.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/Lucagdev/claude-code-statusline/main/install.ps1 | iex
```

Restart Claude Code after installing.

---

## Features

- **35 widgets** — model, context, tokens, cost, duration, git, vim mode, agent, and more
- **7 themes** — Catppuccin, Tokyo Night, Gruvbox, Nord, Dracula, Rosé Pine, Warm
- **Interactive TUI builder** — arrow-key navigation, live preview, no config file editing
- **Usage API** — real-time 5h session and 7d weekly rate limit bars via Anthropic OAuth
- **Zero dependencies** — stdlib only, works on Python 3.10+
- **Cross-platform** — Linux, macOS, Windows
- **Single file** — `statusline.py`, copy anywhere

---

## Screenshot

```
Opus 4.6 (1M)  │  87k/1.0M [████░░░░░░] 42%
Session [██░░░░░░░░] 19%  resets 4h 31m
$3.47  │  2h 00m  │  +245 -89
~/projetos/my-project/src
```

---

## Configure

Run the interactive builder at any time:

```bash
python3 ~/.claude-statusline/statusline.py
```

**Builder controls:**

| Key | Action |
|-----|--------|
| `↑ ↓` | Navigate lines / widgets |
| `← →` | Cycle themes |
| `enter` | Edit line widgets |
| `a` | Add widget |
| `n` | New line |
| `x` | Delete line / widget |
| `c` | Cycle widget color |
| `r` | Reset color to theme default |
| `s` | Save |
| `i` | Save + install to Claude Code |
| `q` | Quit |

---

## Widgets

| ID | Category | Preview |
|----|----------|---------|
| `model_name` | model | `Opus 4.6 (1M)` |
| `model_id` | model | `claude-opus-4-6` |
| `session_cost` | model | `$3.47` |
| `session_duration` | model | `2h 00m` |
| `version` | model | `v2.1.78` |
| `session_id` | model | `a1b2c3d4` |
| `context_usage` | context | `87k/1.0M [████░░░░░░] 42%` |
| `context_percent` | context | `42%` |
| `context_bar` | context | `[████░░░░░░]` |
| `context_remaining` | context | `58% free` |
| `tokens_in` | context | `87k in` |
| `tokens_out` | context | `12k out` |
| `tokens_total` | context | `99k total` |
| `tokens_cache` | context | `15k cached, 8k hit` |
| `context_warning` | context | `! HIGH 85%` (80%+) |
| `lines_changed` | code | `+245 -89` |
| `lines_added` | code | `+245` |
| `lines_removed` | code | `-89` |
| `directory` | workspace | `~/projetos/app/src` |
| `project_dir` | workspace | `~/projetos/app` |
| `git_branch` | git | `feat/login` |
| `worktree_name` | git | `feat-login` |
| `worktree_branch` | git | `feat/login` |
| `original_branch` | git | `main` |
| `session_usage` | usage | `Session [██░░░░░░░░] 19% resets 4h` |
| `session_pct` | usage | `19%` |
| `session_bar` | usage | `[██░░░░░░░░]` |
| `session_reset` | usage | `resets 4h 31m` |
| `weekly_usage` | usage | `Weekly [████░░░░░░] 42% resets 2d 5h` |
| `weekly_pct` | usage | `42%` |
| `weekly_bar` | usage | `[████░░░░░░]` |
| `weekly_reset` | usage | `resets 2d 5h` |
| `vim_mode` | state | `NORMAL` |
| `agent_name` | state | `security-reviewer` |
| `exceeds_200k` | state | `200k+` |

---

## Themes

| Name | Description |
|------|-------------|
| `catppuccin` | Catppuccin Mocha — soft pastels |
| `tokyo-night` | Tokyo Night — cool blues and purples |
| `gruvbox` | Gruvbox Dark — warm retro |
| `nord` | Nord — arctic cool blues |
| `dracula` | Dracula — vibrant dark |
| `rose-pine` | Rosé Pine — elegant muted rose |
| `warm` | Warm — earthy tones |

Switch theme from CLI:

```bash
python3 ~/.claude-statusline/statusline.py --theme nord
```

---

## Usage API (rate limit bars)

The `session_usage` and `weekly_usage` widgets fetch your 5-hour and 7-day rate limit utilization from the Anthropic API. Token resolution order:

1. `CLAUDE_CODE_OAUTH_TOKEN` environment variable
2. `~/.claude/.credentials.json` → `claudeAiOauth.accessToken`
3. `~/.bar/tokens.json` (if [allthingsclaude/bar](https://github.com/allthingsclaude/bar) is installed)

Results are cached for 120 seconds in `$TMPDIR`.

---

## CLI Reference

```
python3 statusline.py [OPTIONS]

Options:
  --config         Open the interactive TUI builder
  --theme NAME     Set active theme
  --install        Write statusLine to ~/.claude/settings.json
  --list-themes    Print all themes
  --list-widgets   Print all widgets
  --help           Show this help
```

---

## License

MIT — Copyright (c) 2026 Lucas G. (lucasgdev)
