import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent)
)

from app.services.node.slides.gyml.definitions import (
    GyMLSection,
    GyMLBody,
    GyMLHeading,
    GyMLFeatureShowcaseBlock,
    GyMLFeatureShowcaseItem,
)
from app.services.node.slides.gyml.renderer import GyMLRenderer
from app.services.node.slides.gyml.theme import THEMES
from app.services.node.slides.gyml.image_generator import ImageGenerator

output_file = str(Path(__file__).resolve().parent / "feature_showcase_test.html")


async def generate_center_image(prompt: str) -> str:
    """Generate a single Leonardo AI image for the central hub circle."""
    print(f"   🎨 Generating center image — prompt: {prompt[:80]}...")
    url = await ImageGenerator.generate_image(
        prompt=prompt,
        width=512,
        height=512,
        style="simple_drawing",
    )
    status = "✅" if url else "⚠ (no image)"
    print(f"   {status} Center image generated")
    return url


async def main():
    sections = []

    # ── Test 1: 6 items — Roles & Responsibilities ────────────────────────
    print("🔥 Generating center image for Roles & Responsibilities...")
    center_url_1 = await generate_center_image(
        "A professional product manager figure in business attire, "
        "flat minimalist illustration, pastel blue background, no text, centered composition"
    )

    sections.append(
        GyMLSection(
            id="test_6",
            body=GyMLBody(
                children=[
                    GyMLHeading(level=1, text="Roles and Responsibilities"),
                    GyMLFeatureShowcaseBlock(
                        title="Product Manager",
                        image_url=center_url_1,
                        items=[
                            GyMLFeatureShowcaseItem(
                                label="Set product strategy",
                                icon="compass-3",
                                color="#e74c3c",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Conduct market research",
                                icon="search-eye",
                                color="#e91e63",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Create roadmaps",
                                icon="road-map",
                                color="#9b59b6",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Manage risk",
                                icon="shield-check",
                                color="#3498db",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Gather feedback",
                                icon="feedback",
                                color="#2980b9",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Launch products",
                                icon="rocket",
                                color="#1abc9c",
                            ),
                        ],
                    ),
                ]
            ),
        )
    )

    # ── Test 2: 4 items — Key Features ─────────────────────────────────────
    print("🔥 Generating center image for Key Features...")
    center_url_2 = await generate_center_image(
        "An AI robot teacher or tutor figure with a friendly face, "
        "flat minimalist illustration, soft gradient background, no text"
    )

    sections.append(
        GyMLSection(
            id="test_4",
            body=GyMLBody(
                children=[
                    GyMLHeading(level=1, text="Key Features"),
                    GyMLFeatureShowcaseBlock(
                        title="AI Tutor",
                        image_url=center_url_2,
                        items=[
                            GyMLFeatureShowcaseItem(
                                label="Adaptive Learning",
                                icon="brain",
                                color="#6366f1",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Real-time Feedback",
                                icon="chat-3",
                                color="#10b981",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Visual Slides",
                                icon="slideshow-3",
                                color="#f59e0b",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Voice Narration",
                                icon="volume-up",
                                color="#ef4444",
                            ),
                        ],
                    ),
                ]
            ),
        )
    )

    # ── Test 3: 8 items — Limitations (no Leonardo AI, placeholder) ────────
    sections.append(
        GyMLSection(
            id="test_8",
            body=GyMLBody(
                children=[
                    GyMLHeading(level=1, text="Current Limitations"),
                    GyMLFeatureShowcaseBlock(
                        title="Known Constraints",
                        items=[
                            GyMLFeatureShowcaseItem(
                                label="Internet required",
                                icon="wifi",
                                color="#64748b",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="English only",
                                icon="translate-2",
                                color="#78716c",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="No offline mode",
                                icon="wifi-off",
                                color="#94a3b8",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Limited file types",
                                icon="file-warning",
                                color="#a1a1aa",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Processing time",
                                icon="time",
                                color="#737373",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="API rate limits",
                                icon="speed",
                                color="#71717a",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Storage caps",
                                icon="hard-drive-2",
                                color="#a3a3a3",
                            ),
                            GyMLFeatureShowcaseItem(
                                label="Beta features",
                                icon="flask",
                                color="#9ca3af",
                            ),
                        ],
                    ),
                ]
            ),
        )
    )

    # Render
    renderer = GyMLRenderer(theme=THEMES["gamma_light"], animated=False)
    html_content = renderer.render_complete(sections)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n🎉 Generated {output_file} successfully.")


if __name__ == "__main__":
    asyncio.run(main())
