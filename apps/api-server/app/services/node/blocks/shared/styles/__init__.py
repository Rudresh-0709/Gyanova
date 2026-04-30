from __future__ import annotations

from pathlib import Path

try:
    from app.services.node.slides.gyml.theme import Theme, get_theme
except ModuleNotFoundError:
    from slides.gyml.theme import Theme, get_theme


SHARED_STYLES_DIR = Path(__file__).parent
FAMILY_STYLES_DIR = Path(__file__).parent.parent.parent / "families"
SHARED_STYLE_ORDER = ("card.css", "flow.css", "table.css", "layout.css", "density.css")


def get_slide_css(family: str, theme: Theme | None = None) -> str:
    """
    Assemble complete CSS for a slide render in this order:
    1. Theme variables (:root block) -- must come first.
    2. Shared base styles (card, flow, table, layout, density).
    3. Family-specific styles.

    Passing "__all__" loads every registered family stylesheet. This keeps
    full-deck renders safe when a deck contains multiple block families.
    """
    active_theme = theme or get_theme("gamma_light")
    parts: list[str] = [active_theme.to_css_vars()]

    for filename in SHARED_STYLE_ORDER:
        css_path = SHARED_STYLES_DIR / filename
        if css_path.exists():
            parts.append(css_path.read_text(encoding="utf-8"))

    family_names = [family]
    if family in {"__all__", "all", "*"}:
        family_names = sorted(
            path.name for path in FAMILY_STYLES_DIR.iterdir() if path.is_dir()
        )

    for family_name in family_names:
        family_css = FAMILY_STYLES_DIR / family_name / "styles.css"
        if family_css.exists():
            parts.append(family_css.read_text(encoding="utf-8"))

    return "\n".join(part for part in parts if part)


__all__ = ["get_slide_css"]
