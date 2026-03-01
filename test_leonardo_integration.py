import sys
import os
import json
from dotenv import load_dotenv

# Ensure we can import from the app directory
root = os.path.dirname(os.path.abspath(__file__))
# Ensure we can import from the app directory
root = os.path.dirname(os.path.abspath(__file__))
# Note: gyml is in apps/api-server/app/services/node/slides/
slides_path = os.path.join(
    root, "apps", "api-server", "app", "services", "node", "slides"
)
if slides_path not in sys.path:
    sys.path.append(slides_path)

from gyml.composer import SlideComposer
from gyml.definitions import ComposedSlide


def test_integration():
    print("🚀 Testing SlideComposer + Leonardo AI Integration...")

    composer = SlideComposer()

    # Mock data resembling LLM output
    mock_data = {
        "title": "Quantum Computing Fundamentals",
        "topic": "Quantum Computing",
        "intent": "explain",
        "contentBlocks": [
            {
                "type": "intro_paragraph",
                "text": "Quantum computing uses qubits to perform calculations far beyond classical limits.",
            }
        ],
        "imagePrompt": "A glowing holographic qubit suspended in a dark laboratory, neon blue and purple light, hyper-realistic",
        "layout": "right",
    }

    print("DEBUG: Composing slide (this should trigger Leonardo AI)...")
    slides = composer.compose(mock_data)

    if slides:
        slide = slides[0]
        print(f"\n✅ Composition Complete!")
        print(f"Slide ID: {slide.id}")
        print(f"Layout: {slide.image_layout}")
        print(f"Image URL: {slide.accent_image_url}")

        if slide.accent_image_url and "leonardo.ai" in slide.accent_image_url:
            print(
                "\n🎉 INTEGRATION SUCCESSFUL: Image URL is a Leonardo AI generated link."
            )
        else:
            print(
                "\n❌ INTEGRATION FAILED: Image URL is missing or not from Leonardo AI."
            )
    else:
        print("\n❌ FAILED: No slides generated.")


if __name__ == "__main__":
    test_integration()
