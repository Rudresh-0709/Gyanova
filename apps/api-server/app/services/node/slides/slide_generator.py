"""
AI-Powered Dynamic Slide Generator
Generates unique, context-aware slide designs using LLM reasoning
Similar to Gamma AI's approach
"""

from ...llm.model_loader import load_openai, load_groq
import json
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os


class DynamicSlideGenerator:
    """
    Uses AI to make design decisions for each slide dynamically
    No fixed templates - each slide is uniquely designed
    """

    def __init__(self):
        self.llm = load_openai()
        self.width = 1920
        self.height = 1080

    def generate_slide_design_plan(
        self, slide_data: dict, subtopic_context: str
    ) -> dict:
        """
        Uses LLM to create a unique design plan for this specific slide
        Returns positioning, colors, typography, spacing decisions
        """

        DESIGN_SYSTEM_PROMPT = """
You are an expert UI/UX designer and slide design specialist. Your task is to create a unique, visually striking slide design that perfectly matches the content.

🎯 DESIGN PHILOSOPHY:
- Every slide should feel unique and purposeful
- Design choices must enhance comprehension, not just decoration
- Use modern, clean aesthetics with intentional negative space
- Balance visual hierarchy: title > key visual > supporting points
- Adapt layout based on content density and message type

📐 YOUR TASK:
Analyze the slide content and generate a complete design specification as JSON.

Consider:
1. **Content Analysis**: What's the main message? Is it conceptual, factual, comparative, sequential?
2. **Visual Hierarchy**: What should the eye see first, second, third?
3. **Layout Strategy**: How should elements be positioned for maximum impact?
4. **Color Psychology**: What colors enhance this specific message?
5. **Typography**: What text sizes/weights communicate importance?

🎨 DESIGN ELEMENTS TO SPECIFY:

{
  "layout_strategy": "describe the overall spatial organization",
  "title": {
    "position": {"x": 0-1920, "y": 0-1080},
    "font_size": 40-120,
    "font_weight": "light|regular|bold|black",
    "color": "#hexcode",
    "alignment": "left|center|right",
    "max_width": 400-1600,
    "style_notes": "any special styling like underline, background, etc"
  },
  "image": {
    "position": {"x": 0-1920, "y": 0-1080},
    "width": 400-1800,
    "height": 300-1000,
    "style": "full_bleed|contained|circular|split_screen|background_overlay",
    "opacity": 0.3-1.0,
    "border_radius": 0-50,
    "shadow": true/false
  },
  "points": {
    "container": {"x": 0-1920, "y": 0-1080, "width": 400-1000},
    "layout": "vertical_list|grid_2col|horizontal_flow|numbered_sequence",
    "spacing": 40-120,
    "font_size": 24-48,
    "bullet_style": "circle|dash|number|icon|none",
    "text_color": "#hexcode",
    "background": "none|card|subtle_box",
    "alignment": "left|center"
  },
  "background": {
    "type": "solid|gradient|image_overlay",
    "primary_color": "#hexcode",
    "secondary_color": "#hexcode",
    "gradient_direction": "vertical|horizontal|diagonal",
    "texture": "none|subtle_noise|geometric_pattern"
  },
  "accents": [
    {
      "type": "line|shape|icon|decorative_element",
      "position": {"x": 0-1920, "y": 0-1080},
      "color": "#hexcode",
      "purpose": "visual_separation|emphasis|brand_element"
    }
  ],
  "animation_hint": "fade_in|slide_from_left|reveal_sequence|none",
  "design_rationale": "brief explanation of why these choices work for this content"
}

🎨 DESIGN GUIDELINES:
- For **conceptual/abstract content**: Use ample whitespace, centered layouts, minimal colors
- For **data/factual content**: Use structured grids, clear hierarchies, data visualization colors
- For **process/sequential content**: Use directional layouts (left-to-right flow), numbered elements
- For **comparison content**: Use split-screen or side-by-side layouts with contrasting colors
- For **introductory slides**: Bold, large type, hero image placement
- For **detailed slides**: Multi-column, organized sections, smaller type

COLOR PSYCHOLOGY:
- Science/Tech: Blues (#3B82F6, #1E40AF), teals, purples
- History: Sepia tones (#8B7355), warm neutrals, gold accents
- Creative: Bold colors (#EC4899, #F59E0B), gradients
- Professional: Navy (#1E3A8A), gray (#6B7280), minimal accent

AVOID:
- Cookie-cutter templates
- Centering everything
- Default bullet points
- Predictable layouts
- Ignoring content context

Return ONLY valid JSON, nothing else.
"""

        user_content = f"""
Subtopic Context: {subtopic_context}

Slide Content:
Title: {slide_data.get('title', '')}
Points: {json.dumps(slide_data.get('points', []), indent=2)}
Image Available: {'Yes' if slide_data.get('image_path') else 'No'}
Image Type: {slide_data.get('imageType', 'N/A')}

Design a unique, purposeful slide layout for this specific content.
"""

        response = self.llm.invoke(
            [
                {"role": "system", "content": DESIGN_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
        )

        try:
            design_plan = json.loads(response.content)
        except:
            # Fallback to basic design
            design_plan = self._get_fallback_design()

        return design_plan

    def _get_fallback_design(self):
        """Fallback design if LLM fails"""
        return {
            "layout_strategy": "clean modern",
            "title": {
                "position": {"x": 100, "y": 100},
                "font_size": 72,
                "color": "#1F2937",
                "alignment": "left",
            },
            "image": {
                "position": {"x": 1000, "y": 200},
                "width": 800,
                "height": 700,
                "style": "contained",
            },
            "points": {
                "container": {"x": 100, "y": 300, "width": 800},
                "layout": "vertical_list",
                "spacing": 80,
                "font_size": 36,
            },
            "background": {"type": "solid", "primary_color": "#FFFFFF"},
        }

    def render_slide(
        self, slide_data: dict, design_plan: dict, output_path: str
    ) -> str:
        """
        Renders the slide based on the AI-generated design plan
        """
        # Create canvas
        bg_config = design_plan.get("background", {})

        if bg_config.get("type") == "gradient":
            canvas = self._create_gradient_background(
                bg_config.get("primary_color", "#FFFFFF"),
                bg_config.get("secondary_color", "#F3F4F6"),
                bg_config.get("gradient_direction", "vertical"),
            )
        else:
            bg_color = self._hex_to_rgb(bg_config.get("primary_color", "#FFFFFF"))
            canvas = Image.new("RGB", (self.width, self.height), bg_color)

        draw = ImageDraw.Draw(canvas)

        # Render image first (if it should be background)
        image_config = design_plan.get("image", {})
        if slide_data.get("image_path") and os.path.exists(slide_data["image_path"]):
            if image_config.get("style") == "background_overlay":
                self._render_background_image(
                    canvas, slide_data["image_path"], image_config
                )

        # Render title
        title_config = design_plan.get("title", {})
        self._render_title(draw, slide_data.get("title", ""), title_config)

        # Render image (if not background)
        if slide_data.get("image_path") and os.path.exists(slide_data["image_path"]):
            if image_config.get("style") != "background_overlay":
                self._render_image(canvas, slide_data["image_path"], image_config)

        # Render points
        points_config = design_plan.get("points", {})
        self._render_points(draw, slide_data.get("points", []), points_config)

        # Render accents/decorative elements
        for accent in design_plan.get("accents", []):
            self._render_accent(draw, accent)

        # Save
        canvas.save(output_path, "PNG", quality=95)
        return output_path

    def _create_gradient_background(self, color1: str, color2: str, direction: str):
        """Create gradient background"""
        from PIL import Image

        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)

        c1 = self._hex_to_rgb(color1)
        c2 = self._hex_to_rgb(color2)

        if direction == "vertical":
            for y in range(self.height):
                ratio = y / self.height
                r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
                g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
                b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
                draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        return img

    def _render_title(self, draw, title: str, config: dict):
        """Render title with AI-specified styling"""
        try:
            font_size = config.get("font_size", 72)
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
            )
        except:
            font = ImageFont.load_default()

        pos = config.get("position", {"x": 100, "y": 100})
        color = self._hex_to_rgb(config.get("color", "#000000"))

        draw.text((pos["x"], pos["y"]), title, fill=color, font=font)

    def _render_points(self, draw, points: list, config: dict):
        """Render points with AI-specified layout"""
        try:
            font_size = config.get("font_size", 36)
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
            )
        except:
            font = ImageFont.load_default()

        container = config.get("container", {"x": 100, "y": 300, "width": 800})
        spacing = config.get("spacing", 80)
        layout = config.get("layout", "vertical_list")
        color = self._hex_to_rgb(config.get("text_color", "#4B5563"))

        y_offset = container["y"]

        for i, point in enumerate(points):
            if layout == "numbered_sequence":
                text = f"{i+1}. {point}"
            elif config.get("bullet_style") == "dash":
                text = f"— {point}"
            else:
                text = f"• {point}"

            # Wrap text
            import textwrap

            wrapped = textwrap.fill(
                text, width=int(container["width"] / (font_size * 0.6))
            )

            draw.text((container["x"], y_offset), wrapped, fill=color, font=font)
            y_offset += spacing

    def _render_image(self, canvas, image_path: str, config: dict):
        """Render image with AI-specified styling"""
        img = Image.open(image_path)

        # Resize
        target_w = config.get("width", 800)
        target_h = config.get("height", 600)
        img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

        # Position
        pos = config.get("position", {"x": 1000, "y": 200})

        # Apply styling
        if config.get("border_radius", 0) > 0:
            # Create rounded corners (simplified)
            pass

        canvas.paste(img, (pos["x"], pos["y"]))

    def _render_background_image(self, canvas, image_path: str, config: dict):
        """Render image as background with overlay"""
        img = Image.open(image_path)
        img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)

        # Apply opacity
        opacity = int(config.get("opacity", 0.5) * 255)
        img.putalpha(opacity)

        canvas.paste(img, (0, 0), img)

    def _render_accent(self, draw, accent: dict):
        """Render decorative accents"""
        accent_type = accent.get("type")
        pos = accent.get("position", {"x": 0, "y": 0})
        color = self._hex_to_rgb(accent.get("color", "#3B82F6"))

        if accent_type == "line":
            draw.line(
                [(pos["x"], pos["y"]), (pos["x"] + 200, pos["y"])], fill=color, width=4
            )

    def _hex_to_rgb(self, hex_color: str):
        """Convert hex to RGB tuple"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def generate_html_presentation(self, state: dict) -> str:
        """Generate interactive HTML with unique styling per slide"""

        HTML_GEN_PROMPT = """
Generate a complete, modern HTML presentation file. Each slide should have unique, beautiful styling.

Requirements:
- Responsive design
- Smooth animations
- Keyboard navigation (arrow keys)
- Progress indicator
- Modern CSS (flexbox, grid, gradients, shadows)
- Each slide's HTML/CSS should match its design plan
- No external dependencies (all CSS inline or in <style>)

Return complete HTML file ready to open in browser.
"""

        # Generate HTML using LLM with slide data
        response = self.llm.invoke(
            [
                {"role": "system", "content": HTML_GEN_PROMPT},
                {
                    "role": "user",
                    "content": f"Generate HTML for: {json.dumps(state.get('topic'))}",
                },
            ]
        )

        return response.content


def generate_dynamic_slides(state: dict) -> dict:
    """
    Main node function: Generate uniquely designed slides using AI
    """
    generator = DynamicSlideGenerator()

    slides_data = state.get("slides", {})
    output_dir = "./dynamic_slides"
    os.makedirs(output_dir, exist_ok=True)

    for subtopic_id, slides in slides_data.items():
        subtopic_name = next(
            (
                st["name"]
                for st in state.get("sub_topics", [])
                if st["id"] == subtopic_id
            ),
            subtopic_id,
        )

        for idx, slide in enumerate(slides):
            print(f"🎨 Designing slide {idx+1}: {slide.get('title')}")

            # Get unique design plan from AI
            design_plan = generator.generate_slide_design_plan(slide, subtopic_name)

            # Render slide
            output_path = f"{output_dir}/{subtopic_id}_slide_{idx+1}.png"
            generator.render_slide(slide, design_plan, output_path)

            slide["final_slide_path"] = output_path
            slide["design_plan"] = design_plan

            print(f"   ✅ Generated: {output_path}")
            print(f"   📐 Strategy: {design_plan.get('layout_strategy', 'N/A')}")

    state["dynamic_slides_generated"] = True
    return state


if __name__ == "__main__":
    # This is a test runner to generate a single slide image.
    # Note: For the image to appear, a file named 'test_image.png' 
    # must exist in the directory where you run this script.
    # If it doesn't exist, a placeholder will be created.
    
    print("Starting single slide generation test...")

    # 1. Define sample slide data
    test_slide_data = {
        "title": "Evolution of Computers",
        "points": [
            "1st Gen: Vacuum Tubes (1940s-50s)",
            "2nd Gen: Transistors (1950s-60s)",
            "3rd Gen: Integrated Circuits (1960s-70s)",
            "4th Gen: Microprocessors (1970s-Present)"
        ],
        "image_path": "test_image.png" # A placeholder image file
    }
    
    # Create a dummy image file if it doesn't exist, so the test can run
    if not os.path.exists(test_slide_data["image_path"]):
        print(f"'{test_slide_data['image_path']}' not found. Creating a dummy placeholder image.")
        try:
            placeholder_img = Image.new('RGB', (600, 400), color = 'grey')
            d = ImageDraw.Draw(placeholder_img)
            d.text((10,10), "Placeholder Image", fill='white')
            placeholder_img.save(test_slide_data["image_path"])
        except Exception as e:
            print(f"Could not create placeholder image: {e}")
            # Remove image path if creation fails
            del test_slide_data["image_path"]


    # 2. Initialize the generator
    generator = DynamicSlideGenerator()
    
    # 3. Generate the design plan from the AI
    print("🎨 Designing slide with AI...")
    design_plan = generator.generate_slide_design_plan(test_slide_data, "Introduction to Computing")
    print("   📐 Design plan received:")
    # print(json.dumps(design_plan, indent=2)) # Optional: uncomment to see the full design
    
    # 4. Render the slide to a PNG file
    output_filename = "test_slide_output.png"
    print(f"🖼️ Rendering slide to '{output_filename}'...")
    generator.render_slide(test_slide_data, design_plan, output_filename)
    
    print(f"\n✅ Success! Slide saved as {output_filename}")
