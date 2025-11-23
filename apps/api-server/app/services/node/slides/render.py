import json
import os
from jinja2 import Environment, FileSystemLoader

# Configuration
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
OUTPUT_FILE = "final_output.html"


class ThemeManager:
    THEMES = {
        "Midnight": {
            "bg_primary": "#0f172a",
            "bg_secondary": "#1e293b",
            "text_primary": "#f8fafc",
            "text_secondary": "#cbd5e1",
            "accent": "#38bdf8",
            "bg_image": "../static/backgrounds/nebula.jpg",
        },
        "Corporate": {
            "bg_primary": "#ffffff",
            "bg_secondary": "#f3f4f6",
            "text_primary": "#111827",
            "text_secondary": "#4b5563",
            "accent": "#4f46e5",
            "bg_image": "../static/backgrounds/abstract.jpg",
        },
        "Playful": {
            "bg_primary": "#fffbeb",
            "bg_secondary": "#fef3c7",
            "text_primary": "#78350f",
            "text_secondary": "#92400e",
            "accent": "#d97706",
            "bg_image": "",
        },
    }

    @staticmethod
    def get_theme(theme_name):
        return ThemeManager.THEMES.get(theme_name, ThemeManager.THEMES["Corporate"])


def render_slide(state):
    # 1. Setup Jinja Environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("master_slide.html")

    # 2. Extract Design Metadata
    design = state.get("design", {})
    layout_class = design.get("layout_mode", "layout-split-balanced")
    decor_class = design.get("decoration_style", "decor-minimal")
    point_style_class = design.get("point_display", "points-list")
    point_style_class = design.get("point_display", "points-list")

    # 3. Get Theme Data
    # For now, we default to "Corporate", but this could be passed in state
    theme_data = ThemeManager.get_theme("Corporate")

    # 4. Resolve Image Path
    # Logic: Look for an image that matches the title (sanitized) in static/images
    image_path = "https://placehold.co/600x600?text=No+Image+Found"

    # Sanitize title to match filename convention (e.g., "Evolution of Computers" -> "Evolution_of_Computers.png")
    sanitized_title = state["title"].replace(" ", "_")

    images_root = os.path.join(STATIC_DIR, "images")
    if os.path.exists(images_root):
        for root, dirs, files in os.walk(images_root):
            for file in files:
                # Check if file starts with sanitized title (ignoring case and extension)
                if file.lower().startswith(
                    sanitized_title.lower()
                ) and file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    # Found an image! Construct relative path for HTML
                    abs_image_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_image_path, os.getcwd())
                    image_path = rel_path.replace("\\", "/")
                    break
            if image_path != "https://placehold.co/600x600?text=No+Image+Found":
                break

    css_path = os.path.join(STATIC_DIR, "css", "styles.css")
    css_content = ""
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
    else:
        print(f"⚠️ Warning: CSS file not found at {css_path}")

    # 6. Render Template
    html_output = template.render(
        title=state["title"],
        points=state["points"],
        contentBlocks=state["contentBlocks"],
        image_path=image_path,
        layout_class=layout_class,
        decor_class=decor_class,
        point_style_class=point_style_class,
        theme=theme_data,
        styles=css_content,
    )

    # 7. Save Output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"✅ Slide rendered to {OUTPUT_FILE}")
    print(f"   Layout: {layout_class}")
    print(f"   Decor: {decor_class}")
    print(f"   Points: {point_style_class}")


if __name__ == "__main__":
    # Sample State (from User Request)
    sample_state = {
        "title": "Evolution of Computers",
        "points": [
            "Computers have evolved through distinct generations, each marked by significant advancements.",
            "First generation computers used vacuum tubes, while second generation computers adopted transistors.",
            "Third generation computers integrated integrated circuits, leading to smaller, more powerful machines.",
        ],
        "template": "image_left",
        "imageType": "ai_enhanced_image",
        "imagePrompt": "educational diagram illustrating the evolution of computers through generations...",
        "design": {
            "layout_mode": "layout-explanation-bottom-image-right",  # Testing a complex layout
            "decoration_style": "decor-tech",
            "point_display": "points-numbered",
        },
        "contentBlocks": [
            {
                "type": "timeline",
                "events": [
                    {
                        "year": "1940s-1950s",
                        "description": "First Generation: Vacuum tubes used as main electronic component, large and power-hungry.",
                    },
                    {
                        "year": "1950s-1960s",
                        "description": "Second Generation: Transistors replaced vacuum tubes, improving reliability and reducing size.",
                    },
                    {
                        "year": "1960s-1970s",
                        "description": "Third Generation: Introduction of integrated circuits, enabling more compact and efficient computers.",
                    },
                    {
                        "year": "1970s-Present",
                        "description": "Fourth Generation: Microprocessors revolutionized computing by integrating thousands of ICs onto a single chip.",
                    },
                ],
            },
            {
                "type": "explanation",
                "paragraphs": [
                    "Each generation of computers not only improved hardware components but also expanded the scope of applications, from basic calculations to complex data processing and artificial intelligence.",
                    "The evolution reflects continuous innovation in materials, design, and manufacturing techniques, driving the exponential growth in computing power.",
                ],
            },
        ],
    }

    render_slide(sample_state)
