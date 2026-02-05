"""
GyML Theme Configuration

Gamma-style themes: clean, professional, light.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List


def hex_to_rgb(hex_color: str) -> str:
    """Convert hex color to RGB values string."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "0, 0, 0"
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"{r}, {g}, {b}"


@dataclass
class ThemeConstraints:
    """Constraints imposed by the theme."""

    allowed_block_types: list[str] = field(
        default_factory=lambda: []
    )  # Empty = all allowed
    allowed_layouts: list[str] = field(
        default_factory=lambda: []
    )  # Empty = all allowed
    max_items_per_slide: int = 6


@dataclass
class ComponentStyle:
    """Visual styles for specific components."""

    card_shadow: str = "none"
    card_radius: str = "0.5rem"
    divider_style: str = "solid"  # solid, dashed, dotted
    font_family_override: Optional[str] = None


@dataclass
class Theme:
    """Theme configuration for Gamma-style slides."""

    name: str

    # Colors
    bg_primary: str
    bg_secondary: str
    text_primary: str
    text_secondary: str
    accent: str
    border_color: str
    number_bg: str
    callout_bg: str
    icon_bg: str

    # Typography
    font_heading: str = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    font_body: str = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"

    # Advanced Configuration
    constraints: ThemeConstraints = field(default_factory=ThemeConstraints)
    component_styles: ComponentStyle = field(default_factory=ComponentStyle)

    def to_css_vars(self) -> str:
        """Generate CSS custom properties."""
        return f"""
:root {{
    --bg-primary: {self.bg_primary};
    --bg-secondary: {self.bg_secondary};
    --text-primary: {self.text_primary};
    --text-secondary: {self.text_secondary};
    --accent: {self.accent};
    --border-color: {self.border_color};
    --number-bg: {self.number_bg};
    --callout-bg: {self.callout_bg};
    --icon-bg: {self.icon_bg};
    --timeline-color: #2d8a6e;
    --font-heading: {self.font_heading};
    --font-body: {self.font_body};
    
    /* Component Styles */
    --card-shadow: {self.component_styles.card_shadow};
    --card-radius: {self.component_styles.card_radius};
    --divider-style: {self.component_styles.divider_style};
}}
"""

    def to_dict(self) -> Dict:
        """Convert theme to dictionary."""
        return {
            "name": self.name,
            "colors": {
                "bg_primary": self.bg_primary,
                "bg_secondary": self.bg_secondary,
                "text_primary": self.text_primary,
                "text_secondary": self.text_secondary,
                "accent": self.accent,
            },
        }


# =============================================================================
# PRESET THEMES - Gamma Style
# =============================================================================

THEMES: Dict[str, Theme] = {
    "gamma_light": Theme(
        name="Gamma Light",
        bg_primary="#f8f7f4",
        bg_secondary="#ffffff",
        text_primary="#1a1a1a",
        text_secondary="#555555",
        accent="#666666",
        border_color="#e5e5e5",
        number_bg="#f0f0f0",
        callout_bg="#f5f5f5",
        icon_bg="#1a1a1a",
    ),
    "gamma_cream": Theme(
        name="Gamma Cream",
        bg_primary="#faf8f5",
        bg_secondary="#ffffff",
        text_primary="#2d2a26",
        text_secondary="#6b6560",
        accent="#8b7355",
        border_color="#e8e4df",
        number_bg="#f5f2ed",
        callout_bg="#faf8f5",
        icon_bg="#2d2a26",
    ),
    "gamma_blue": Theme(
        name="Gamma Blue",
        bg_primary="#f5f7fa",
        bg_secondary="#ffffff",
        text_primary="#1e293b",
        text_secondary="#475569",
        accent="#3b82f6",
        border_color="#e2e8f0",
        number_bg="#eff6ff",
        callout_bg="#f0f9ff",
        icon_bg="#1e40af",
    ),
    "gamma_dark": Theme(
        name="Gamma Dark",
        bg_primary="#121212",
        bg_secondary="#1e1e1e",
        text_primary="#ffffff",
        text_secondary="#a0a0a0",
        accent="#888888",
        border_color="#333333",
        number_bg="#2a2a2a",
        callout_bg="#252525",
        icon_bg="#ffffff",
    ),
    "gamma_navy": Theme(
        name="Gamma Navy",
        bg_primary="#0f172a",
        bg_secondary="#1e293b",
        text_primary="#f8fafc",
        text_secondary="#94a3b8",
        accent="#60a5fa",
        border_color="#334155",
        number_bg="#1e293b",
        callout_bg="#1e293b",
        icon_bg="#3b82f6",
    ),
    "midnight": Theme(
        name="Midnight",
        bg_primary="#0a0f1a",
        bg_secondary="#0f172a",
        text_primary="#f8fafc",
        text_secondary="#94a3b8",
        accent="#38bdf8",
        border_color="#1e293b",
        number_bg="#1e293b",
        callout_bg="#1e293b",
        icon_bg="#38bdf8",
    ),
}


def get_theme(name: str) -> Theme:
    """Get a theme by name. Falls back to 'gamma_light'."""
    return THEMES.get(name.lower(), THEMES["gamma_light"])


def create_custom_theme(name: str, **kwargs) -> Theme:
    """Create a custom theme."""
    defaults = {
        "bg_primary": "#f8f7f4",
        "bg_secondary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#555555",
        "accent": "#666666",
        "border_color": "#e5e5e5",
        "number_bg": "#f0f0f0",
        "callout_bg": "#f5f5f5",
        "icon_bg": "#1a1a1a",
    }
    defaults.update(kwargs)
    return Theme(name=name, **defaults)
