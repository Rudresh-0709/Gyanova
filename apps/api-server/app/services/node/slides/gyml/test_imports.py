import sys
from pathlib import Path

# Add the app directory to sys.path
app_root = Path(__file__).resolve().parents[4]
sys.path.append(str(app_root))

print(f"app_root: {app_root}")

try:
    from services.node.slides.gyml.definitions import (
        GyMLProcessArrowBlock,
        GyMLCyclicProcessBlock,
    )
    import services.node.slides.gyml.definitions as defs

    print("Definitions imported successfully!")
    print(f"Definitions file: {defs.__file__}")
except Exception as e:
    import traceback

    traceback.print_exc()

try:
    from services.node.slides.gyml.renderer import GyMLRenderer
    import services.node.slides.gyml.renderer as rend

    print("Renderer imported successfully!")
    print(f"Renderer file: {rend.__file__}")
    print(f"Has _render_heading: {hasattr(GyMLRenderer, '_render_heading')}")
    # Also check methods list
    methods = [m for m in dir(GyMLRenderer) if m.startswith("_render_")]
    print(f"Render methods: {methods}")
except Exception as e:
    import traceback

    traceback.print_exc()
