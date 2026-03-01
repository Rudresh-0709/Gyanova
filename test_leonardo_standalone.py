import sys
import os
from dotenv import load_dotenv

# Ensure we can import from the app directory
root = os.path.dirname(os.path.abspath(__file__))
gyml_path = os.path.join(
    root, "apps", "api-server", "app", "services", "node", "slides", "gyml"
)
if gyml_path not in sys.path:
    sys.path.append(gyml_path)

# Correct the import to use the local file directly if path is in sys.path
from image_generator import ImageGenerator


def test():
    print("🚀 Testing Leonardo AI Generation (FLUX Schnell)...")
    url = ImageGenerator.generate_accent_image(
        prompt="A vibrant 3D render of a futuristic computer microprocessor with glowing circuits",
        layout="top",
        topic="Microprocessors",
    )
    if url:
        print(f"\n✅ SUCCESS! Image URL: {url}")
    else:
        print("\n❌ FAILED: No URL returned. Check debug prints above.")


if __name__ == "__main__":
    test()
