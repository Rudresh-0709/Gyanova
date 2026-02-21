import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "app")))

from services.node.slides.gyml.composer import SlideComposer

payload = {
    "title": "What is a Microprocessor?",
    "subtitle": "Discovering the brain behind modern computing",
    "contentBlocks": [
        {
            "type": "smart_layout",
            "content": {
                "variant": "cardGrid",
                "items": [
                    {"heading": "A", "description": "B"},
                    {"heading": "C", "description": "D"},
                ],
            },
        }
    ],
}

composer = SlideComposer()
slides = composer.compose(payload)

from services.node.slides.gyml.serializer import GyMLSerializer

serializer = GyMLSerializer()
gyml_sections = serializer.serialize_many(slides)

for sec in gyml_sections:
    print(f"DEBUG: GYML SECTION DUMP: {sec}")

from services.node.slides.gyml.renderer import GyMLRenderer

renderer = GyMLRenderer(animated=True)
html_out = renderer.render_complete(gyml_sections)
print("\n--- HTML DUMP ---")
print(html_out)
print("Done")
