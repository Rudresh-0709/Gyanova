"""
AI-Powered Dynamic Slide Generator
Generates unique, context-aware slide designs using LLM reasoning
Similar to Gamma AI's approach
"""

from ...llm.model_loader import load_openai, load_groq
import json
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

    def _normalize_design_plan(self, plan: dict) -> dict:
    # Merge plan with safe defaults for keys we use
        defaults = {
            "title": {"position": {"x":100, "y":40}, "font_size":72, "font_weight":"bold",
                    "color":"#1F2937", "alignment":"left", "max_width":1400},
            "image": {"position":{"x":1000,"y":160}, "width":720, "height":540,
                    "style":"contained", "opacity":1.0, "border_radius":0, "shadow":False},
            "points": {"container":{"x":100,"y":260,"width":800},
                    "layout":"vertical_list","spacing":64,"font_size":30,
                    "bullet_style":"icon","text_color":"#374151","alignment":"left",
                    "background":"none"},
            "background": {"type":"solid","primary_color":"#FFFFFF","secondary_color":"#FFFFFF","gradient_direction":"vertical"},
            "accents": [],
            "animation_hint":"none"
        }
        # deep-merge plan into defaults
        import copy
        out = copy.deepcopy(defaults)
        def deep_update(d, u):
            for k,v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        out = deep_update(out, plan or {})
        return out

    def _rounded_rectangle(self, draw, bbox, radius=10, fill=None, outline=None):
        x1,y1,x2,y2 = bbox
        draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline)

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
            print("DEBUG: design_plan =", json.dumps(design_plan, indent=2))
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
        design_plan = self._normalize_design_plan(design_plan)
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
        self._render_title(draw, slide_data.get("title", ""), title_config, canvas)

        # Render image (if not background)
        if slide_data.get("image_path") and os.path.exists(slide_data["image_path"]):
            if image_config.get("style") != "background_overlay":
                self._render_image(canvas, slide_data["image_path"], image_config)

        # Render points
        points_config = design_plan.get("points", {})
        self._render_points(draw, slide_data.get("points", []), points_config, canvas)

        # Render accents/decorative elements
        for accent in design_plan.get("accents", []):
            self._render_accent(draw, accent)

        # Save
        canvas.save(output_path, "PNG", quality=95)
        return output_path

    def _create_gradient_background(self, color1: str, color2: str, direction: str):
        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)
        c1 = self._hex_to_rgb(color1)
        c2 = self._hex_to_rgb(color2)
        if direction == "vertical":
            for y in range(self.height):
                ratio = y / (self.height - 1)
                r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
                g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
                b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
                draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        elif direction == "horizontal":
            for x in range(self.width):
                ratio = x / (self.width - 1)
                r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
                g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
                b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
                draw.line([(x, 0), (x, self.height)], fill=(r, g, b))
        elif direction == "diagonal":
            # basic diagonal by mapping y->x; simpler but works visually
            for y in range(self.height):
                ratio = y / (self.height - 1)
                r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
                g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
                b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
                draw.line([(0, y), (int(self.width*ratio), y)], fill=(r,g,b))
        return img

    def _render_title(self, canvas_draw, title: str, config: dict, canvas):
    # canvas is PIL.Image instance (we need width to compute centering)
        font_size = int(config.get("font_size", 72))
        # choose font variant by weight if available
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if config.get("font_weight", "bold").lower() in ("light","regular"):
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
            pos = config.get("position", {"x":100,"y":40})
            max_w = config.get("max_width", 1400)
            color = self._hex_to_rgb(config.get("color", "#000000"))

        # wrap to max_width by measuring text
        lines = []
        words = title.split()
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            bbox = canvas_draw.textbbox((0, 0), test, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            if tw <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)

        # compute total height
        bbox = font.getbbox("Ay")
        line_height = (bbox[3] - bbox[1]) + 6
        total_h = line_height * len(lines)
        alignment = config.get("alignment","left")
        x = pos["x"]
        y = pos["y"]

        for line in lines:
            bbox = canvas_draw.textbbox((0, 0), test, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            if alignment == "center":
                draw_x = int((self.width - tw) / 2) if pos.get("x") == 0 else int(pos["x"])
                # if user put x as 0, treat it as center; else do left at pos.x
                if pos.get("x") == 0:
                    draw_x = int((self.width - tw) / 2)
                else:
                    if config.get("alignment") == "center":
                        draw_x = int((self.width - tw) / 2)
                    else:
                        draw_x = x
            elif alignment == "right":
                draw_x = pos["x"] - tw
            else:
                draw_x = x
            canvas_draw.text((draw_x, y), line, fill=color, font=font)
            y += line_height

    def _render_points(self, canvas_draw, points: list, config: dict, canvas):
        font_size = int(config.get("font_size", 30))
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()

        container = config.get("container", {"x":100,"y":260,"width":800})
        spacing = int(config.get("spacing", 64))
        text_color = self._hex_to_rgb(config.get("text_color","#374151"))
        bullet = config.get("bullet_style", "circle")
        alignment = config.get("alignment","left")
        x = container["x"]
        y = container["y"]
        max_w = container["width"]

        for i, p in enumerate(points):
            # form text line (numbered/dash/ bullet)
            if config.get("layout") == "numbered_sequence":
                lead = f"{i+1}. "
            elif bullet == "dash":
                lead = "— "
            elif bullet == "number":
                lead = f"{i+1}. "
            else:
                lead = "• "

            # wrap text by measuring words
            import textwrap
            words = p.split()
            lines = []
            cur = ""
            for w in words:
                test = (cur + " " + w).strip()
                bbox = canvas_draw.textbbox((0, 0), test, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]

                if tw <= max_w - 40:  # padding for bullet
                    cur = test
                else:
                    lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)

            # optional card background
            if config.get("background") == "card":
                card_pad = 14
                # compute height
                bbox = font.getbbox("Ay")
                line_height = (bbox[3] - bbox[1]) + 6

                card_h = line_height*len(lines) + card_pad*2
                card_w = max_w
                # draw rounded rect
                bbox = [x, y, x + card_w, y + card_h]
                self._rounded_rectangle(canvas_draw, bbox, radius=12, fill=(245,245,248))
                inner_x = x + card_pad
                inner_y = y + card_pad
            else:
                inner_x = x + 10
                inner_y = y

            # draw bullet or number at inner_x
            if lead.strip():
                canvas_draw.text((inner_x, inner_y), lead, fill=text_color, font=font)
                # shift text start to account for lead width
                bbox = canvas_draw.textbbox((0, 0), lead, font=font)
                lead_w = bbox[2] - bbox[0]

                text_x = inner_x + lead_w
            else:
                text_x = inner_x

            # draw wrapped lines
            for j, line in enumerate(lines):
    # compute height once
                bbox = font.getbbox("Ay")
                line_height = (bbox[3] - bbox[1]) + 6

                for j, line in enumerate(lines):
                    canvas_draw.text((text_x, inner_y + j * line_height), line, fill=text_color, font=font)

            # if card, use card_h else use len(lines)*line_height + spacing
            if config.get("background") == "card":
                y += card_h + int(spacing*0.2)
            else:
                bbox = font.getbbox("Ay")
                line_height = (bbox[3] - bbox[1]) + 6
                y += (line_height * len(lines)) + spacing

    def _render_image(self, canvas, image_path: str, config: dict):
        try:
            img = Image.open(image_path).convert("RGBA")
        except:
            return
        target_w = int(config.get("width", 800))
        target_h = int(config.get("height", 600))
        img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

        # create mask for rounded corners
        border_radius = int(config.get("border_radius", 0))
        if border_radius > 0:
            mask = Image.new("L", img.size, 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.rounded_rectangle([(0,0), img.size], radius=border_radius, fill=255)
            img.putalpha(mask)

        # apply opacity
        opacity = float(config.get("opacity", 1.0))
        if opacity < 1.0:
            alpha = img.split()[-1].point(lambda p: int(p * opacity))
            img.putalpha(alpha)

        # add shadow if requested
        pos = config.get("position", {"x":1000,"y":160})
        if config.get("shadow", False):
            # shadow layer: paste a blurred rectangle behind the image
            shadow = Image.new("RGBA", (img.size[0]+40, img.size[1]+40), (0,0,0,0))
            sdraw = ImageDraw.Draw(shadow)
            sdraw.rounded_rectangle([(20,20),(20+img.size[0],20+img.size[1])], radius=border_radius+4, fill=(0,0,0,180))
            shadow = shadow.filter(ImageFilter.GaussianBlur(8))
            # paste shadow then image
            canvas.paste(shadow, (pos["x"]-20, pos["y"]-20), shadow)
        # final paste
        canvas.paste(img, (pos["x"], pos["y"]), img)

    def _render_background_image(self, canvas, image_path: str, config: dict):
        """Render image as background with overlay"""
        img = Image.open(image_path)
        img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)

        # Apply opacity
        opacity = int(config.get("opacity", 0.5) * 255)
        img.putalpha(opacity)

        canvas.paste(img, (0, 0), img)

    def _render_accent(self, draw, accent: dict):
        t = accent.get("type","line")
        pos = accent.get("position", {"x":0,"y":0})
        color = self._hex_to_rgb(accent.get("color", "#3B82F6"))
        purpose = accent.get("purpose","emphasis")
        if t == "line":
            length = accent.get("length", 200)
            width = accent.get("width", 4)
            draw.line([(pos["x"], pos["y"]), (pos["x"] + length, pos["y"])], fill=color, width=width)
        elif t == "shape":
            w = accent.get("width", 120); h = accent.get("height", 6)
            draw.rectangle([(pos["x"], pos["y"]), (pos["x"]+w, pos["y"]+h)], fill=color)
        elif t == "icon":
            # draw a simple circle or placeholder for icon
            r = accent.get("radius", 10)
            draw.ellipse([(pos["x"]-r, pos["y"]-r),(pos["x"]+r,pos["y"]+r)], fill=color)


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
    sample_plan = {
    "layout_strategy": "split_screen",
    "title": {"position":{"x":100,"y":20},"font_size":64,"font_weight":"bold","color":"#0F172A","alignment":"left","max_width":900},
    "image": {"position":{"x":980,"y":120},"width":760,"height":540,"style":"contained","border_radius":16,"shadow":True,"opacity":0.95},
    "points": {"container":{"x":100,"y":200,"width":760},"layout":"vertical_list","spacing":48,"font_size":28,"bullet_style":"dash","text_color":"#1E40AF","background":"none"},
    "background": {"type":"gradient","primary_color":"#FFFFFF","secondary_color":"#EFF6FF","gradient_direction":"vertical"},
    "accents":[{"type":"line","position":{"x":820,"y":620},"color":"#1E40AF","length":260,"width":5}],
    "animation_hint":"fade_in",
    "design_rationale":"Split-screen pairs title + bullets on left with hero image on right for clarity."
    }
    # 4. Render the slide to a PNG file
    output_filename = "test_slide_output.png"
    print(f"🖼️ Rendering slide to '{output_filename}'...")
    # after generator = DynamicSlideGenerator()
    design_plan = sample_plan  # use the sample plan above to validate rendering
    generator.render_slide(test_slide_data, design_plan, "test_slide_output_debug.png")
    print("Rendered debug image at test_slide_output_debug.png")

    
    print(f"\n✅ Success! Slide saved as {output_filename}")
