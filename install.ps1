# Claude Code Statusline — Installer for Windows
# Usage: & ([scriptblock]::Create((irm https://raw.githubusercontent.com/Lucagdev/claude-code-statusline/main/install.ps1)))
$ErrorActionPreference = "Stop"

$repo = "https://raw.githubusercontent.com/Lucagdev/claude-code-statusline/main"
$installDir = "$env:USERPROFILE\.claude-statusline"

Write-Host ""
Write-Host "  Claude Code Statusline" -ForegroundColor Magenta
Write-Host "  Beautiful, customizable status bar for Claude Code"
Write-Host ""

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "  Found: $pyVersion"
} catch {
    Write-Host "  Error: Python 3 is required. Install from python.org" -ForegroundColor Red
    exit 1
}

# Create install dir
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

# Download statusline.py
Write-Host "  Downloading statusline.py..."
Invoke-WebRequest -Uri "$repo/statusline.py" -OutFile "$installDir\statusline.py"

# Configure Claude Code settings.json
$claudeSettings = "$env:USERPROFILE\.claude\settings.json"
if (Test-Path $claudeSettings) {
    $settings = Get-Content $claudeSettings | ConvertFrom-Json
} else {
    New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude" | Out-Null
    $settings = @{}
}
$settings.statusLine = @{
    type = "command"
    command = "python `"$installDir\statusline.py`""
    padding = 0
}
$settings | ConvertTo-Json -Depth 10 | Set-Content $claudeSettings

Write-Host ""
Write-Host "  ✓ Installed!" -ForegroundColor Green
Write-Host ""
Write-Host "  Restart Claude Code to see your statusline."
Write-Host ""

# Launch interactive configurator
python "$installDir\statusline.py" --config
