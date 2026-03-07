import asyncio
import os
import sys
from pathlib import Path

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
api_server_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if api_server_root not in sys.path:
    sys.path.insert(0, api_server_root)

# Load env vars for API key
from dotenv import load_dotenv

load_dotenv(os.path.join(api_server_root, ".env"))

from app.services.node.slides.gyml.image_generator import ImageGenerator


async def test_diag():
    prompt = "A critical meeting between revolutionary leaders and a defiant clergyman in 18th-century France, symbolizing the church's resistance."
    print(f"Testing Leonardo AI with prompt: {prompt}")

    # Use real generator
    url = await ImageGenerator.generate_accent_image(
        prompt, "French Revolution", "left"
    )

    if url:
        print(f"SUCCESS! URL: {url}")
    else:
        print("FAIL: Returned None")


if __name__ == "__main__":
    asyncio.run(test_diag())
