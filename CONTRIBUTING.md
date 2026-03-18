# Contributing

Thanks for your interest in improving claude-code-statusline!

## How it works

The project has two versions of the code:

- **`src/claude_code_statusline/`** — modular source code (edit this)
- **`statusline.py`** — single-file distribution (generated, don't edit)

## Development workflow

1. Fork and clone the repo
2. Edit files in `src/claude_code_statusline/`
3. Test locally:
   ```bash
   echo '{"model":{"display_name":"Test"}}' | python3 src/claude_code_statusline/render.py
   ```
4. Build the single file:
   ```bash
   ./build.sh
   ```
5. Test the built file:
   ```bash
   echo '{"model":{"display_name":"Test"}}' | python3 statusline.py
   ```
6. Commit both `src/` and `statusline.py`
7. Open a PR

## Source modules

| File | Purpose |
|------|---------|
| `themes.py` | Color themes (7 themes, semantic color roles) |
| `config.py` | Config loading/saving, default layout |
| `usage.py` | Anthropic API usage fetcher + cache |
| `widgets.py` | 35 widget definitions + formatters |
| `render.py` | Renderer (stdin JSON → ANSI output) |
| `configure.py` | Interactive builder (TUI) |
| `main.py` | Entry point, CLI args, TTY detection |

## Ideas for contributions

- New widgets (PR welcome!)
- New themes
- Better Windows support
- Translations for the landing page
- Tests
- Performance improvements

## Guidelines

- Zero external dependencies — stdlib only
- Python 3.10+ compatible
- Cross-platform (Linux, macOS, Windows)
- Always run `./build.sh` before committing
