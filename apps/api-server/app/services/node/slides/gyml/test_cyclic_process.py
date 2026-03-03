import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path (same pattern as test_process_arrow.py)
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent)
)

from app.services.node.slides.gyml.definitions import (
    GyMLSection,
    GyMLBody,
    GyMLHeading,
    GyMLCyclicProcessBlock,
    GyMLCyclicProcessItem,
)
from app.services.node.slides.gyml.renderer import GyMLRenderer
from app.services.node.slides.gyml.theme import THEMES
from app.services.node.slides.gyml.image_generator import ImageGenerator

output_file = str(Path(__file__).resolve().parent / "cyclic_process_test.html")


async def generate_images_for_items(items_data):
    """Call Leonardo AI to generate a unique image for each cycle circle."""
    tasks = []
    for item in items_data:
        prompt = item["imagePrompt"]
        print(f"   🎨 Generating image for: {item['label']} — prompt: {prompt[:60]}...")
        task = ImageGenerator.generate_image(
            prompt=prompt,
            width=512,
            height=512,
            style="simple_drawing",
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results


async def main():
    # Define items with per-item imagePrompts (Leonardo AI will generate unique images)
    items_data = [
        {
            "label": "Think Like a Customer",
            "description": "Deep interviews to uncover user needs and primary pain points.",
            "imagePrompt": "A person with a magnifying glass examining a glowing lightbulb, flat minimalist illustration, pastel colors, no text",
        },
        {
            "label": "Listen to Customer Voice",
            "description": "Synthesizing feedback from surveys and direct interactions.",
            "imagePrompt": "An ear with colorful sound waves flowing into it, flat minimalist illustration, pastel colors, no text",
        },
        {
            "label": "Anticipate Customers' Needs",
            "description": "Proactively designing features that solve future problems.",
            "imagePrompt": "A crystal ball with small gears and sparkles inside, flat minimalist illustration, pastel colors, no text",
        },
    ]

    # Generate images via Leonardo AI
    print("🔥 Generating images via Leonardo AI...")
    image_urls = await generate_images_for_items(items_data)

    # Build GyML items with the generated image URLs
    items = []
    for data, url in zip(items_data, image_urls):
        items.append(
            GyMLCyclicProcessItem(
                label=data["label"],
                description=data["description"],
                image_url=url,  # Leonardo AI generated URL
            )
        )
        status = "✅" if url else "⚠ (no image)"
        print(f"   {status} {data['label']}")

    # Build sections (3-item and 2-item examples)
    sections = []

    # 3-item cyclic process
    sections.append(
        GyMLSection(
            id="test_3_items",
            body=GyMLBody(
                children=[
                    GyMLHeading(level=1, text="Product Manager Strategy"),
                    GyMLCyclicProcessBlock(items=items),
                ]
            ),
        )
    )

    # 2-item cyclic process (reuse first two items)
    sections.append(
        GyMLSection(
            id="test_2_items",
            body=GyMLBody(
                children=[
                    GyMLHeading(level=1, text="Customer Feedback Loop"),
                    GyMLCyclicProcessBlock(items=items[:2]),
                ]
            ),
        )
    )

    # Render using render_complete (same as test_process_arrow.py)
    renderer = GyMLRenderer(theme=THEMES["gamma_light"], animated=True)
    html_content = renderer.render_complete(sections)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n🎉 Generated {output_file} successfully.")


if __name__ == "__main__":
    asyncio.run(main())
