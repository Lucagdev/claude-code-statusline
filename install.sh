#!/usr/bin/env bash
# Claude Code Statusline — Installer for Linux/Mac/WSL/Windows (Git Bash)

set -e

REPO="https://raw.githubusercontent.com/Lucagdev/claude-code-statusline/main"
INSTALL_DIR="$HOME/.claude-statusline"

echo ""
echo "  Claude Code Statusline"
echo "  Beautiful, customizable status bar for Claude Code"
echo ""

# Check Python (python3 on Linux/Mac, python on Windows/Git Bash)
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null && python -c "import sys; sys.exit(0 if sys.version_info.major==3 else 1)" 2>/dev/null; then
    PYTHON=python
else
    echo "Error: Python 3 is required. Install it first."
    exit 1
fi

# Check Python version >= 3.10
PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
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

# Convert Git Bash paths (/c/Users/...) to Windows paths (C:/Users/...) for Python
if [[ "$(uname -s)" == MINGW* ]] || [[ "$(uname -s)" == MSYS* ]]; then
    PY_SETTINGS=$(cygpath -w "$CLAUDE_SETTINGS" 2>/dev/null || echo "$CLAUDE_SETTINGS")
    PY_INSTALL_DIR=$(cygpath -w "$INSTALL_DIR" 2>/dev/null || echo "$INSTALL_DIR")
else
    PY_SETTINGS="$CLAUDE_SETTINGS"
    PY_INSTALL_DIR="$INSTALL_DIR"
fi

if [ -f "$CLAUDE_SETTINGS" ]; then
    # Use Python to safely merge JSON
    $PYTHON -c "
import json, os
settings_path = r'$PY_SETTINGS'
install_dir = r'$PY_INSTALL_DIR'
with open(settings_path) as f:
    s = json.load(f)
cmd = '$PYTHON ' + os.path.join(install_dir, 'statusline.py')
s['statusLine'] = {'type': 'command', 'command': cmd, 'padding': 0}
with open(settings_path, 'w') as f:
    json.dump(s, f, indent=2)
    f.write('\n')
"
else
    mkdir -p "$HOME/.claude"
    $PYTHON -c "
import json, os
settings_path = r'$PY_SETTINGS'
install_dir = r'$PY_INSTALL_DIR'
cmd = '$PYTHON ' + os.path.join(install_dir, 'statusline.py')
s = {'statusLine': {'type': 'command', 'command': cmd, 'padding': 0}}
with open(settings_path, 'w') as f:
    json.dump(s, f, indent=2)
    f.write('\n')
"
fi

echo ""
echo "  ✓ Installed!"
echo ""
echo "  Restart Claude Code to see your statusline."
echo ""

# Launch interactive configurator if running in a terminal
# (won't work when piped via curl | bash — stdin is not a TTY)
if [ -t 0 ] && [ -t 1 ]; then
    $PYTHON "$INSTALL_DIR/statusline.py" --config
else
    echo "  To customize: $PYTHON ~/.claude-statusline/statusline.py"
    echo ""
fi
