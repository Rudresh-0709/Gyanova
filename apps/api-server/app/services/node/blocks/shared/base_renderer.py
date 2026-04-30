from dataclasses import dataclass, field
from html import escape

try:
    from app.services.node.slides.gyml.theme import Theme, get_theme
except ModuleNotFoundError:
    from slides.gyml.theme import Theme, get_theme


@dataclass
class RenderContext:
    density: str = "balanced"
    image_layout: str = "blank"
    item_count: int = 0
    block_width: str = "normal"
    has_image: bool = False
    animated: bool = False
    theme: Theme = field(default_factory=lambda: get_theme("gamma_light"))
    _segment_counter: int = 0

    def _escape(self, raw: object) -> str:
        return escape("" if raw is None else str(raw), quote=True)
