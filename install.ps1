# Claude Code Statusline — Installer for Windows
# Usage: & ([scriptblock]::Create((irm https://raw.githubusercontent.com/Lucagdev/claude-code-statusline/main/install.ps1)))
$ErrorActionPreference = "Stop"

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

# Download statusline.py (use GitHub API to avoid raw.githubusercontent cache)
Write-Host "  Downloading statusline.py..."
Invoke-WebRequest -Uri "https://api.github.com/repos/Lucagdev/claude-code-statusline/contents/statusline.py" `
    -Headers @{ Accept = "application/vnd.github.v3.raw" } `
    -OutFile "$installDir\statusline.py"

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
    command = "python `"$($installDir.Replace('\','/'))/statusline.py`""
    padding = 0
}
$settings | ConvertTo-Json -Depth 10 | Set-Content $claudeSettings

Write-Host ""
Write-Host "  ✓ Installed!" -ForegroundColor Green
Write-Host ""
Write-Host "  Restart Claude Code to see your statusline."
Write-Host ""

# Launch interactive configurator
try {
    python "$installDir\statusline.py" --config
} catch {
    Write-Host "  To customize: python ~/.claude-statusline/statusline.py" -ForegroundColor DarkGray
    Write-Host ""
}
