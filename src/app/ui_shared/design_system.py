"""Central design system for PySort Visualizer.

This module defines all design tokens including colors, spacing, typography,
and component specifications for a consistent, professional UI.
"""

# ============================================================================
# GRID SYSTEM - All spacing must be multiples of 8px
# ============================================================================

GRID_UNIT = 8

SPACING = {
    "none": 0,
    "xs": GRID_UNIT,  # 8px
    "sm": GRID_UNIT * 2,  # 16px
    "md": GRID_UNIT * 3,  # 24px
    "lg": GRID_UNIT * 4,  # 32px
    "xl": GRID_UNIT * 6,  # 48px
    "xxl": GRID_UNIT * 8,  # 64px
}

# ============================================================================
# DIMENSIONS - Component sizes aligned to grid
# ============================================================================

DIMENSIONS = {
    "toolbar_height": GRID_UNIT * 6,  # 48px
    "statusbar_height": GRID_UNIT * 3,  # 24px
    "button_height": GRID_UNIT * 4,  # 32px
    "button_icon_size": GRID_UNIT * 2,  # 16px
    "input_height": GRID_UNIT * 4,  # 32px
    "slider_height": GRID_UNIT * 4,  # 32px
    "min_panel_width": GRID_UNIT * 30,  # 240px
    "scrollbar_width": GRID_UNIT,  # 8px
    "border_radius": 4,  # 4px (not grid-aligned)
    "border_width": 1,  # 1px (not grid-aligned)
}

# ============================================================================
# COLOR PALETTE - Professional dark theme
# ============================================================================

COLORS = {
    # Background layers
    "bg_primary": "#0f1115",  # Main background
    "bg_secondary": "#1a1d23",  # Raised surfaces
    "bg_tertiary": "#22252e",  # Elevated elements
    # Borders
    "border_default": "#2a2e38",  # Default border
    "border_subtle": "#1f2229",  # Subtle separation
    "border_strong": "#363a45",  # Strong separation
    "border_focus": "#4a9eff",  # Focus indicator
    # Text
    "text_primary": "#ffffff",  # Primary text (pure white)
    "text_secondary": "#c9d1d9",  # Secondary text (light gray)
    "text_tertiary": "#8b949e",  # Disabled/hint text (medium gray)
    "text_inverse": "#0f1115",  # Text on light backgrounds
    # Interactive states
    "accent": "#4a9eff",  # Primary accent
    "accent_hover": "#6bb1ff",  # Hover state
    "accent_active": "#2d7dd8",  # Active/pressed state
    # Semantic colors
    "success": "#4ade80",  # Success/complete
    "warning": "#fbbf24",  # Warning
    "error": "#f87171",  # Error
    "info": "#60a5fa",  # Information
    # Visualization specific
    "bar_default": "#6aa0ff",  # Default bar color
    "bar_compare": "#ffe08a",  # Comparison highlight
    "bar_swap": "#fa8072",  # Swap highlight
    "bar_pivot": "#90ee90",  # Pivot element
    "bar_complete": "#62d26f",  # Completed element
}

# ============================================================================
# TYPOGRAPHY - System fonts for best rendering
# ============================================================================

FONTS = {
    "family": {
        "sans": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        "mono": '"SF Mono", Monaco, Consolas, "Courier New", monospace',
    },
    "size": {
        "xs": 11,
        "sm": 12,
        "md": 13,
        "lg": 14,
        "xl": 16,
        "xxl": 20,
    },
    "weight": {
        "normal": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700,
    },
    "line_height": {
        "tight": 1.2,
        "normal": 1.5,
        "relaxed": 1.75,
    },
}

# ============================================================================
# SHADOWS - Subtle depth indication
# ============================================================================

SHADOWS = {
    "none": "none",
    "sm": "0 1px 2px rgba(0, 0, 0, 0.4)",
    "md": "0 2px 4px rgba(0, 0, 0, 0.5)",
    "lg": "0 4px 8px rgba(0, 0, 0, 0.6)",
    "xl": "0 8px 16px rgba(0, 0, 0, 0.7)",
    "focus": f'0 0 0 3px {COLORS["accent"]}33',  # 20% opacity
}

# ============================================================================
# ANIMATIONS - Smooth, professional transitions
# ============================================================================

ANIMATIONS = {
    "duration": {
        "instant": 0,
        "fast": 150,
        "normal": 250,
        "slow": 350,
    },
    "easing": {
        "linear": "linear",
        "ease_in": "ease-in",
        "ease_out": "ease-out",
        "ease_in_out": "ease-in-out",
        "spring": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
    },
}

# ============================================================================
# Z-INDEX LAYERS - Consistent stacking order
# ============================================================================

Z_INDEX = {
    "base": 0,
    "raised": 10,
    "dropdown": 100,
    "sticky": 200,
    "overlay": 300,
    "modal": 400,
    "popover": 500,
    "tooltip": 600,
    "notification": 700,
}

# ============================================================================
# BREAKPOINTS - Responsive design thresholds
# ============================================================================

BREAKPOINTS = {
    "mobile": 640,
    "tablet": 768,
    "desktop": 1024,
    "wide": 1280,
    "ultrawide": 1536,
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def snap_to_grid(value: int) -> int:
    """Snap a value to the nearest grid unit."""
    return round(value / GRID_UNIT) * GRID_UNIT


def get_spacing(size: str) -> int:
    """Get spacing value by size name."""
    return SPACING.get(size, SPACING["md"])


def get_color(name: str, opacity: float = 1.0) -> str:
    """Get color with optional opacity."""
    color = COLORS.get(name, COLORS["text_primary"])
    if opacity >= 1.0:
        return color
    # Convert hex to rgba
    import re

    match = re.match(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$", color)
    if match:
        r, g, b = (int(x, 16) for x in match.groups())
        return f"rgba({r}, {g}, {b}, {opacity})"
    return color


def get_font_style(size: str = "md", weight: str = "normal", family: str = "sans") -> dict:
    """Get complete font style specification."""
    return {
        "family": FONTS["family"][family],
        "size": FONTS["size"][size],
        "weight": FONTS["weight"][weight],
    }
