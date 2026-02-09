import json
import os
import sys
import io

# Force UTF-8 for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# verify_generation.py is in apps/api-server/app/services/node/slides/gyml/
current_dir = os.path.dirname(os.path.abspath(__file__))
print(f"DEBUG: current_dir: {current_dir}")

# 1. Add api-server/ to sys.path (for 'app.services...')
# Need 5 levels up to reach api-server from gyml/
api_server_dir = current_dir
for _ in range(5):
    api_server_dir = os.path.dirname(api_server_dir)
print(f"DEBUG: api_server_dir: {api_server_dir}")
if api_server_dir and api_server_dir not in sys.path:
    sys.path.insert(0, api_server_dir)

# 2. Add slides/ to sys.path (for 'import gyml' used internally by the engine)
# Need 1 level up to reach slides/ from gyml/
slides_dir = os.path.dirname(current_dir)
print(f"DEBUG: slides_dir: {slides_dir}")
if slides_dir and slides_dir not in sys.path:
    sys.path.insert(0, slides_dir)

# Try relative import first (for when run as part of the app)
try:
    from ...llm.model_loader import load_openai
except ImportError:
    # Fallback for different import paths (for when run directly)
    # Need 5 levels up to reach api-server root from gyml/
    root = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        root = os.path.dirname(root)
    if root not in sys.path:
        sys.path.append(root)
    from app.services.llm.model_loader import load_openai

from app.services.node.slides.gyml.generator import GyMLContentGenerator


def test_generation():
    print("🚀 Testing GyML Content Generation...")

    generator = GyMLContentGenerator()

    scenarios = [
        {
            "title": "The Rise of Microservices",
            "purpose": "narrate",
            "subtopic": "Modern Architecture",
            "narration": "In the early 2010s, monoliths were king. But as companies like Netflix and Amazon scaled, they moved to microservices. This allowed for independent scaling and faster deployments. Today, microservices are the standard for large-scale applications.",
        },
        {
            "title": "React vs Vue",
            "purpose": "compare",
            "subtopic": "Frontend Frameworks",
            "narration": "React is a library focused on the view layer, using a virtual DOM. Vue is a progressive framework that offers a more opinionated structure. Both are great, but React has a larger ecosystem while Vue is often seen as more approachable for beginners.",
        },
    ]

    output_data = []
    for scenario in scenarios:
        print(f"\n--- Scenario: {scenario['title']} ---")
        result = generator.generate(
            narration=scenario["narration"],
            title=scenario["title"],
            purpose=scenario["purpose"],
            subtopic=scenario["subtopic"],
        )

        output_data.append({"scenario": scenario["title"], "generated_json": result})

        print(json.dumps(result, indent=2))

        # Basic validation
        if "contentBlocks" in result and len(result["contentBlocks"]) >= 2:
            print("✅ Richness Requirement: Met")
        else:
            print("⚠️ Richness Requirement: Potentially low density")

        has_semantic_para = any(
            b["type"]
            in [
                "intro_paragraph",
                "context_paragraph",
                "annotation_paragraph",
                "outro_paragraph",
            ]
            for b in result.get("contentBlocks", [])
        )
        if has_semantic_para:
            print("✅ Semantic Paragraphs: Used")
        else:
            print("ℹ️ Semantic Paragraphs: Not used in this instance")

    # Save results to file
    with open(
        os.path.join(current_dir, "test_results.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(output_data, f, indent=2)
    print(f"\n💾 Results saved to: {os.path.join(current_dir, 'test_results.json')}")


if __name__ == "__main__":
    test_generation()
