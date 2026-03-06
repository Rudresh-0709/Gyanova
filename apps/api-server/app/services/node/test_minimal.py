import os
import asyncio
import json
import sys
from unittest.mock import MagicMock

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
api_server_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if api_server_root not in sys.path:
    sys.path.insert(0, api_server_root)

from app.services.node.slides.gyml.serializer import GyMLSerializer
from app.services.node.slides.gyml.image_generator import ImageGenerator
from app.services.node.slides.gyml.definitions import ComposedBlock
from app.services.node.slides.gyml.constants import BlockType


async def test_minimal():
    serializer = GyMLSerializer()

    # 1. Test Bullet Serialization
    test_block = {
        "type": "smart_layout",
        "variant": "comparison",
        "items": [{"heading": "Test Heading", "points": ["Point 1", "Point 2"]}],
    }
    # Wrap in ComposedBlock as rendering_node does
    composed = ComposedBlock(type="smart_layout", content=test_block)
    node = serializer._serialize_block(composed)

    print("--- Serialization Test ---")
    if node and node.items:
        desc = node.items[0].description
        print(f"Description: {repr(desc)}")
        if "•" in desc:
            print("✅ Bullets found!")
        else:
            print("❌ Bullets missing!")
    else:
        print("❌ Block serialization failed")

    # 2. Test Image Generation (Single)
    print("\n--- Image Gen Test ---")
    url = await ImageGenerator.generate_image(
        "A simple red apple", width=512, height=512, style="simple_drawing"
    )
    if url:
        print(f"✅ Image generated: {url}")
    else:
        print("❌ Image generation failed")


if __name__ == "__main__":
    asyncio.run(test_minimal())
