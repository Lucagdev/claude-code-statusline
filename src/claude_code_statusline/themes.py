"""Color themes — semantic color roles, not per-widget styles.

Each theme defines a small palette of semantic colors.
Widgets pick the right color by role (primary, accent, success, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Theme:
    name: str
    description: str
    colors: dict[str, str] = field(default_factory=dict)


# Semantic color roles:
#   primary   — model name, main labels
#   secondary — purple/pink accents (tokens out, agents)
#   accent    — blue accents (branch, context, links)
#   info      — cyan/teal (tokens in, worktree)
#   success   — green (cost, lines added)
#   warning   — yellow/orange (context warning, vim mode)
#   danger    — red (high usage, lines removed)
#   muted     — dim text (duration, paths, separators)
#   text      — default foreground

THEMES: dict[str, Theme] = {
    "tokyo-night": Theme(
        name="tokyo-night",
        description="Tokyo Night — cool blues and purples",
        colors={
            "primary":   "#c0caf5",
            "secondary": "#bb9af7",
            "accent":    "#7aa2f7",
            "info":      "#7dcfff",
            "success":   "#9ece6a",
            "warning":   "#e0af68",
            "danger":    "#f7768e",
            "muted":     "#565f89",
            "text":      "#a9b1d6",
        },
    ),
    "catppuccin": Theme(
        name="catppuccin",
        description="Catppuccin Mocha — soft pastels",
        colors={
            "primary":   "#cdd6f4",
            "secondary": "#cba6f7",
            "accent":    "#89b4fa",
            "info":      "#94e2d5",
            "success":   "#a6e3a1",
            "warning":   "#f9e2af",
            "danger":    "#f38ba8",
            "muted":     "#6c7086",
            "text":      "#bac2de",
        },
    ),
    "gruvbox": Theme(
        name="gruvbox",
        description="Gruvbox Dark — warm retro",
        colors={
            "primary":   "#ebdbb2",
            "secondary": "#d3869b",
            "accent":    "#83a598",
            "info":      "#8ec07c",
            "success":   "#b8bb26",
            "warning":   "#fabd2f",
            "danger":    "#fb4934",
            "muted":     "#928374",
            "text":      "#d5c4a1",
        },
    ),
    "nord": Theme(
        name="nord",
        description="Nord — arctic cool blues",
        colors={
            "primary":   "#eceff4",
            "secondary": "#b48ead",
            "accent":    "#5e81ac",
            "info":      "#88c0d0",
            "success":   "#a3be8c",
            "warning":   "#ebcb8b",
            "danger":    "#bf616a",
            "muted":     "#4c566a",
            "text":      "#d8dee9",
        },
    ),
    "dracula": Theme(
        name="dracula",
        description="Dracula — vibrant dark",
        colors={
            "primary":   "#f8f8f2",
            "secondary": "#ff79c6",
            "accent":    "#bd93f9",
            "info":      "#8be9fd",
            "success":   "#50fa7b",
            "warning":   "#f1fa8c",
            "danger":    "#ff5555",
            "muted":     "#6272a4",
            "text":      "#f8f8f2",
        },
    ),
    "rose-pine": Theme(
        name="rose-pine",
        description="Rosé Pine — elegant muted rose",
        colors={
            "primary":   "#e0def4",
            "secondary": "#c4a7e7",
            "accent":    "#31748f",
            "info":      "#9ccfd8",
            "success":   "#31748f",
            "warning":   "#f6c177",
            "danger":    "#eb6f92",
            "muted":     "#6e6a86",
            "text":      "#e0def4",
        },
    ),
    "warm": Theme(
        name="warm",
        description="Warm — earthy tones like allthingsclaude/bar",
        colors={
            "primary":   "#d4a574",
            "secondary": "#c4956a",
            "accent":    "#b8956a",
            "info":      "#a8b89a",
            "success":   "#8faa7a",
            "warning":   "#d4a040",
            "danger":    "#c47070",
            "muted":     "#7a7a6a",
            "text":      "#c0b8a8",
        },
    ),
}
