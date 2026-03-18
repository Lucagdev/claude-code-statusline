#!/usr/bin/env bash
# Claude Code Statusline — Installer for Linux/Mac/WSL

set -e

REPO="https://raw.githubusercontent.com/Lucagdev/claude-code-statusline/main"
INSTALL_DIR="$HOME/.claude-statusline"

echo ""
echo "  Claude Code Statusline"
echo "  Beautiful, customizable status bar for Claude Code"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required. Install it first."
    exit 1
fi

# Check Python version >= 3.10
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo "Error: Python 3.10+ required (found $PY_VERSION)"
    exit 1
fi

# Create install dir
mkdir -p "$INSTALL_DIR"

# Download statusline.py
echo "  Downloading statusline.py..."
curl -fsSL "$REPO/statusline.py" -o "$INSTALL_DIR/statusline.py"
chmod +x "$INSTALL_DIR/statusline.py"

# Configure Claude Code settings.json
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
if [ -f "$CLAUDE_SETTINGS" ]; then
    # Use Python to safely merge JSON
    python3 -c "
import json
with open('$CLAUDE_SETTINGS') as f:
    s = json.load(f)
s['statusLine'] = {'type': 'command', 'command': 'python3 $INSTALL_DIR/statusline.py', 'padding': 0}
with open('$CLAUDE_SETTINGS', 'w') as f:
    json.dump(s, f, indent=2)
    f.write('\n')
"
else
    mkdir -p "$HOME/.claude"
    echo '{"statusLine":{"type":"command","command":"python3 '"$INSTALL_DIR"'/statusline.py","padding":0}}' | python3 -m json.tool > "$CLAUDE_SETTINGS"
fi

echo ""
echo "  ✓ Installed!"
echo ""
echo "  Restart Claude Code to see your statusline."
echo "  To configure: python3 ~/.claude-statusline/statusline.py"
echo ""
