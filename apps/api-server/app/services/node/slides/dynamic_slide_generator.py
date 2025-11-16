"""
Template-Based Dynamic Slide Generator with Improved Styling
Uses HTML templates for each layout type and LLM for creative styling
"""

from ...llm.model_loader import load_openai, load_groq
import json
import os
import base64
from pathlib import Path
from typing import Dict, List


class SlideTemplates:
    """HTML templates for different slide layouts"""
    
    @staticmethod
    def get_base_structure(layout_type: str) -> dict:
        """Returns HTML structure with class names for each layout type"""
        
        templates = {
            "image_right": {
                "html": """
                <div class="slide slide-image-right">
                    <div class="slide-content">
                        <h1 class="slide-title">{title}</h1>
                        <ul class="slide-points">
                            {points}
                        </ul>
                    </div>
                    <div class="slide-image-container">
                        <img src="{image}" class="slide-image" alt="Visual"/>
                    </div>
                </div>
                """,
                "classes": [
                    ".slide-image-right",
                    ".slide-content", 
                    ".slide-title",
                    ".slide-points",
                    ".slide-points li",
                    ".slide-image-container",
                    ".slide-image"
                ]
            },
            
            "image_left": {
                "html": """
                <div class="slide slide-image-left">
                    <div class="slide-image-container">
                        <img src="{image}" class="slide-image" alt="Visual"/>
                    </div>
                    <div class="slide-content">
                        <h1 class="slide-title">{title}</h1>
                        <ul class="slide-points">
                            {points}
                        </ul>
                    </div>
                </div>
                """,
                "classes": [
                    ".slide-image-left",
                    ".slide-image-container",
                    ".slide-image",
                    ".slide-content",
                    ".slide-title",
                    ".slide-points",
                    ".slide-points li"
                ]
            },
            
            "split_horizontal": {
                "html": """
                <div class="slide slide-split-horizontal">
                    <div class="slide-top">
                        <h1 class="slide-title">{title}</h1>
                        <ul class="slide-points">
                            {points}
                        </ul>
                    </div>
                    <div class="slide-bottom">
                        <img src="{image}" class="slide-image" alt="Visual"/>
                    </div>
                </div>
                """,
                "classes": [
                    ".slide-split-horizontal",
                    ".slide-top",
                    ".slide-title",
                    ".slide-points",
                    ".slide-points li",
                    ".slide-bottom",
                    ".slide-image"
                ]
            },
            
            "image_background": {
                "html": """
                <div class="slide slide-image-background">
                    <img src="{image}" class="slide-background-image" alt="Background"/>
                    <div class="slide-overlay"></div>
                    <div class="slide-content">
                        <h1 class="slide-title">{title}</h1>
                        <ul class="slide-points">
                            {points}
                        </ul>
                    </div>
                </div>
                """,
                "classes": [
                    ".slide-image-background",
                    ".slide-background-image",
                    ".slide-overlay",
                    ".slide-content",
                    ".slide-title",
                    ".slide-points",
                    ".slide-points li"
                ]
            },
            
            "hero": {
                "html": """
                <div class="slide slide-hero">
                    <div class="hero-content">
                        <h1 class="hero-title">{title}</h1>
                        <p class="hero-subtitle">{subtitle}</p>
                    </div>
                    {image_section}
                </div>
                """,
                "classes": [
                    ".slide-hero",
                    ".hero-content",
                    ".hero-title",
                    ".hero-subtitle",
                    ".hero-image-container",
                    ".hero-image"
                ]
            },
            
            "centered": {
                "html": """
                <div class="slide slide-centered">
                    <div class="centered-content">
                        <h1 class="slide-title">{title}</h1>
                        <ul class="slide-points">
                            {points}
                        </ul>
                        {image_section}
                    </div>
                </div>
                """,
                "classes": [
                    ".slide-centered",
                    ".centered-content",
                    ".slide-title",
                    ".slide-points",
                    ".slide-points li",
                    ".slide-image"
                ]
            }
        }
        
        return templates.get(layout_type, templates["image_right"])


class DynamicSlideGenerator:
    """Generates styled HTML presentations using templates and LLM styling"""
    
    def __init__(self, output_dir="./final_slides"):
        self.llm = load_openai()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.templates = SlideTemplates()
    
    def generate_slide_styles(self, slide_data: dict, slide_index: int, 
                              layout_type: str) -> str:
        """
        Uses LLM to generate complete <style> tag for the slide
        Returns CSS as a complete style tag string
        """
        
        template_info = self.templates.get_base_structure(layout_type)
        
        STYLE_GENERATION_PROMPT = """You are an expert web designer creating stunning, unique presentation slides.

Your task is to generate a complete CSS <style> block for a single slide that will make it visually captivating and professionally designed.

**DESIGN PRINCIPLES:**

1. **Visual Hierarchy**: Title should dominate, then points, then supporting elements
2. **Color Psychology**: 
   - Technical/Science: Blues (#2563EB, #3B82F6, #1E40AF), teals (#0D9488, #14B8A6)
   - Creative/Arts: Vibrant colors (#EC4899, #F59E0B, #8B5CF6), bold gradients
   - Historical: Warm earth tones (#92400E, #78350F, #D97706)
   - Business: Professional blues/grays (#1F2937, #374151, #2563EB)
3. **Typography**: 
   - Use font combinations (e.g., Playfair Display for titles + Inter for body)
   - Size hierarchy: Title (48-96px), Points (20-32px)
   - Line height for readability: 1.2-1.4 for titles, 1.6-2.0 for body
4. **Spacing**: Generous whitespace, consistent padding (60-120px)
5. **Modern Effects**: Subtle shadows, smooth gradients, elegant animations

**LAYOUT STRUCTURE:**

You will be styling these specific classes:
{classes}

**REQUIREMENTS:**

- Generate a complete <style> tag (including opening and closing tags)
- Include all CSS rules for the classes listed above
- Add background styling for the slide container
- Include hover effects, transitions, and subtle animations
- Add decorative accent elements using ::before or ::after pseudo-elements
- Ensure text is readable with proper contrast
- Make each slide UNIQUE - vary colors, layouts, and effects
- Use modern CSS features: gradients, transforms, clip-paths, filters

**CONTEXT ABOUT THIS SLIDE:**

Slide Number: {slide_index}
Title: {title}
Number of Points: {num_points}
Content Preview: {content_preview}
Has Image: {has_image}
Layout Type: {layout_type}

**OUTPUT FORMAT:**

Return ONLY the complete <style> tag with all CSS. Example structure:

<style>
/* Slide Container & Background */
.slide-class-name {
    /* background, dimensions, positioning */
}

/* Title Styling */
.slide-title {
    /* typography, colors, positioning, effects */
}

/* Content Points */
.slide-points {
    /* container styling */
}

.slide-points li {
    /* individual point styling, bullets, spacing */
}

.slide-points li::before {
    /* custom bullet styling */
}

/* Image Styling */
.slide-image {
    /* sizing, effects, positioning */
}

/* Decorative Accents */
.slide-class-name::before {
    /* decorative elements */
}

/* Animations */
@keyframes slideAnimation {
    /* entrance animations */
}

/* Responsive adjustments if needed */
</style>

**CREATIVITY GUIDELINES:**

- For Slide #1-2: Bold hero designs, large typography, dramatic effects
- For Middle slides: Balanced, informative, clear hierarchy
- For Final slides: Memorable, impactful, summary-focused
- Vary gradient angles: 135deg, 225deg, 45deg, 180deg
- Use different animation types: fadeIn, slideIn, scaleIn, bounceIn
- Experiment with asymmetric layouts and dynamic positioning
- Add depth with layered shadows and overlays

Generate creative, production-ready CSS that makes this slide stand out!
"""

        user_prompt = f"""
Generate the <style> tag for slide #{slide_index + 1}:

**Slide Details:**
- Title: "{slide_data.get('title', 'Untitled')}"
- Points: {slide_data.get('points', [])}
- Number of Points: {len(slide_data.get('points', []))}
- Layout Type: {layout_type}
- Has Image: {'Yes' if slide_data.get('image_path') else 'No'}

**Classes to Style:**
{json.dumps(template_info['classes'], indent=2)}

**Design Direction:**
Make this slide visually stunning and unique. Consider the content type and create appropriate styling that enhances understanding and engagement.

Return ONLY the complete <style> tag with all CSS rules.
"""

        try:
            response = self.llm.invoke([
                {"role": "system", "content": STYLE_GENERATION_PROMPT},
                {"role": "user", "content": user_prompt}
            ])
            
            style_tag = response.content.strip()
            
            # Ensure it's wrapped in style tags
            if not style_tag.startswith('<style>'):
                style_tag = f'<style>\n{style_tag}\n</style>'
            
            print(f"✅ Generated styles for slide {slide_index + 1}")
            return style_tag
            
        except Exception as e:
            print(f"⚠️ Style generation failed: {e}")
            return self._get_fallback_styles(layout_type, slide_index)
    
    def _get_fallback_styles(self, layout_type: str, index: int) -> str:
        """Fallback styles if LLM fails"""
        
        colors = [
            ["#1E40AF", "#3B82F6"],
            ["#7C2D12", "#EA580C"],
            ["#15803D", "#22C55E"],
            ["#7E22CE", "#A855F7"]
        ]
        color_set = colors[index % len(colors)]
        
        return f"""
<style>
    .slide {{
        background: linear-gradient(135deg, {color_set[0]}, {color_set[1]});
        width: 100vw;
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 80px;
        position: relative;
    }}
    
    .slide-content {{
        flex: 1;
        max-width: 50%;
    }}
    
    .slide-title {{
        font-size: 64px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 40px;
        line-height: 1.2;
    }}
    
    .slide-points {{
        list-style: none;
        padding: 0;
    }}
    
    .slide-points li {{
        font-size: 28px;
        color: #F3F4F6;
        margin-bottom: 24px;
        line-height: 1.6;
        padding-left: 30px;
        position: relative;
    }}
    
    .slide-points li::before {{
        content: "•";
        position: absolute;
        left: 0;
        color: #FFFFFF;
        font-weight: bold;
        font-size: 32px;
    }}
    
    .slide-image-container {{
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        max-width: 40%;
    }}
    
    .slide-image {{
        max-width: 100%;
        max-height: 70vh;
        border-radius: 12px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }}
</style>
"""
    
    def improve_html_structure(self, base_html: str, slide_data: dict, 
                               slide_index: int) -> str:
        """
        Uses LLM to enhance the HTML structure with better semantics and accessibility
        """
        
        IMPROVEMENT_PROMPT = """You are an expert frontend developer. 

You will receive a basic HTML structure for a slide. Your task is to:

1. **Enhance HTML semantics** - Use proper HTML5 elements
2. **Add accessibility features** - ARIA labels, alt text, semantic structure
3. **Improve structure** - Better nesting, logical grouping
4. **Add micro-interactions** - Data attributes for JS animations
5. **Maintain class names** - Keep existing classes for CSS targeting

**DO NOT:**
- Add inline styles
- Change the overall layout structure
- Remove existing classes
- Add external dependencies

**DO ADD:**
- Semantic HTML5 elements (section, article, figure, etc.)
- ARIA attributes for accessibility
- Data attributes for animations (data-animate="fadeIn", etc.)
- Proper alt text and titles
- Logical element nesting

Return ONLY the improved HTML structure, no explanations.
"""

        try:
            response = self.llm.invoke([
                {"role": "system", "content": IMPROVEMENT_PROMPT},
                {"role": "user", "content": f"Improve this HTML structure:\n\n{base_html}\n\nSlide title: {slide_data.get('title')}\nSlide content: {slide_data.get('points')}"}
            ])
            
            improved_html = response.content.strip()
            print(f"✅ Improved HTML structure for slide {slide_index + 1}")
            return improved_html
            
        except Exception as e:
            print(f"⚠️ HTML improvement failed, using base template: {e}")
            return base_html
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 data URL"""
        if not image_path or not os.path.exists(image_path):
            return ""
        
        try:
            with open(image_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
                image_ext = Path(image_path).suffix[1:]
                return f"data:image/{image_ext};base64,{image_data}"
        except Exception as e:
            print(f"⚠️ Failed to encode image: {e}")
            return ""
    
    def generate_slide_html(self, slide_data: dict, slide_index: int) -> str:
        """Generate complete HTML + CSS for a single slide"""
        
        # Determine layout type
        layout_type = slide_data.get('slideType', 'image_right')
        
        # Get template
        template_info = self.templates.get_base_structure(layout_type)
        base_html = template_info['html']
        
        # Encode image
        image_data = self.encode_image(slide_data.get('image_path', ''))
        
        # Build points HTML
        points_html = ""
        for point in slide_data.get('points', []):
            points_html += f'<li data-animate="fadeInUp">{point}</li>\n'
        
        # Fill template
        html_filled = base_html.format(
            title=slide_data.get('title', ''),
            points=points_html,
            image=image_data,
            subtitle=slide_data.get('subtitle', ''),
            image_section=f'<img src="{image_data}" class="slide-image" alt="Visual"/>'
                        if image_data else ''
        )
        
        # Improve HTML structure with LLM
        improved_html = self.improve_html_structure(html_filled, slide_data, slide_index)
        
        # Generate unique styles for this slide
        style_tag = self.generate_slide_styles(slide_data, slide_index, layout_type)
        
        # Combine style + HTML with wrapper
        complete_slide = f"""
        {style_tag}
        {improved_html}
        """
        
        return complete_slide
    
    def generate_complete_presentation(self, state: dict) -> str:
        """
        Generate complete HTML presentation file with all slides
        """
        
        slides_data = state.get("slides", {})
        all_slides_html = []
        all_styles = []
        
        slide_counter = 0
        
        # Generate each slide
        for subtopic_id, slides in slides_data.items():
            for slide in slides:
                print(f"\n🎨 Generating slide {slide_counter + 1}: {slide.get('title', 'Untitled')}")
                
                # Get layout type from slide data
                layout_type = slide.get('slideType', 'image_right')
                
                # Generate slide HTML and styles
                slide_html = self.generate_slide_html(slide, slide_counter)
                
                # Wrap slide in container
                wrapped_slide = f"""
                <div class="slide-wrapper" data-slide-index="{slide_counter}" style="display: none;">
                    {slide_html}
                </div>
                """
                
                all_slides_html.append(wrapped_slide)
                slide_counter += 1
        
        # Generate complete HTML document
        complete_html = self._build_complete_html(
            state.get('topic', 'Presentation'),
            all_slides_html,
            slide_counter
        )
        
        # Save HTML file
        output_path = self.output_dir / "presentation.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(complete_html)
        
        print(f"\n✅ Complete presentation generated: {output_path}")
        print(f"📊 Total slides: {slide_counter}")
        
        return str(output_path)
    
    def _build_complete_html(self, title: str, slides: List[str], 
                            total_slides: int) -> str:
        """Build the complete HTML document with all slides and controls"""
        
        slides_html = '\n'.join(slides)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700;800;900&family=Montserrat:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    
    <style>
        /* ===== GLOBAL RESET & BASE STYLES ===== */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html {{
            scroll-behavior: smooth;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            overflow: hidden;
            background: #000000;
            color: #1F2937;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        /* ===== SLIDE CONTAINER ===== */
        .slide-container {{
            width: 100vw;
            height: 100vh;
            position: relative;
            overflow: hidden;
        }}
        
        .slide-wrapper {{
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            opacity: 0;
            transform: scale(0.95);
            transition: none;
        }}
        
        .slide-wrapper.active {{
            display: block !important;
            opacity: 1;
            transform: scale(1);
            animation: slideEnter 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .slide-wrapper.exiting {{
            animation: slideExit 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        /* ===== BASE SLIDE STYLES ===== */
        .slide {{
            width: 100%;
            height: 100%;
            position: relative;
            overflow: hidden;
        }}
        
        /* ===== ANIMATIONS ===== */
        @keyframes slideEnter {{
            0% {{
                opacity: 0;
                transform: scale(0.95) translateY(20px);
            }}
            100% {{
                opacity: 1;
                transform: scale(1) translateY(0);
            }}
        }}
        
        @keyframes slideExit {{
            0% {{
                opacity: 1;
                transform: scale(1);
            }}
            100% {{
                opacity: 0;
                transform: scale(0.95);
            }}
        }}
        
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes slideInLeft {{
            from {{
                opacity: 0;
                transform: translateX(-50px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        @keyframes slideInRight {{
            from {{
                opacity: 0;
                transform: translateX(50px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        @keyframes scaleIn {{
            from {{
                opacity: 0;
                transform: scale(0.8);
            }}
            to {{
                opacity: 1;
                transform: scale(1);
            }}
        }}
        
        @keyframes bounceIn {{
            0% {{
                opacity: 0;
                transform: scale(0.3);
            }}
            50% {{
                transform: scale(1.05);
            }}
            70% {{
                transform: scale(0.9);
            }}
            100% {{
                opacity: 1;
                transform: scale(1);
            }}
        }}
        
        /* Staggered animation for list items */
        .slide-wrapper.active [data-animate="fadeInUp"] {{
            animation: fadeInUp 0.8s ease-out backwards;
        }}
        
        .slide-wrapper.active [data-animate="fadeInUp"]:nth-child(1) {{
            animation-delay: 0.2s;
        }}
        
        .slide-wrapper.active [data-animate="fadeInUp"]:nth-child(2) {{
            animation-delay: 0.4s;
        }}
        
        .slide-wrapper.active [data-animate="fadeInUp"]:nth-child(3) {{
            animation-delay: 0.6s;
        }}
        
        .slide-wrapper.active [data-animate="fadeInUp"]:nth-child(4) {{
            animation-delay: 0.8s;
        }}
        
        .slide-wrapper.active [data-animate="fadeInUp"]:nth-child(5) {{
            animation-delay: 1.0s;
        }}
        
        /* ===== NAVIGATION CONTROLS ===== */
        .controls {{
            position: fixed;
            bottom: 40px;
            right: 40px;
            display: flex;
            gap: 15px;
            z-index: 10000;
        }}
        
        .btn {{
            background: rgba(255, 255, 255, 0.95);
            color: #1F2937;
            border: 2px solid transparent;
            padding: 14px 28px;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(10px);
            font-family: 'Inter', sans-serif;
            user-select: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
            background: #FFFFFF;
            border-color: #3B82F6;
        }}
        
        .btn:active {{
            transform: translateY(0);
        }}
        
        .btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }}
        
        .btn:disabled:hover {{
            transform: none;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        }}
        
        /* ===== PROGRESS BAR ===== */
        .progress-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.1);
            z-index: 10000;
        }}
        
        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #3B82F6, #8B5CF6, #EC4899);
            transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }}
        
        /* ===== SLIDE COUNTER ===== */
        .slide-counter {{
            position: fixed;
            bottom: 40px;
            left: 40px;
            background: rgba(255, 255, 255, 0.95);
            padding: 14px 28px;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 600;
            color: #1F2937;
            z-index: 10000;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            font-family: 'Inter', sans-serif;
            user-select: none;
        }}
        
        .slide-counter .current {{
            color: #3B82F6;
            font-weight: 700;
        }}
        
        /* ===== FULLSCREEN BUTTON ===== */
        .fullscreen-btn {{
            position: fixed;
            top: 40px;
            right: 40px;
            background: rgba(255, 255, 255, 0.95);
            border: none;
            padding: 12px;
            border-radius: 10px;
            cursor: pointer;
            z-index: 10000;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
        }}
        
        .fullscreen-btn:hover {{
            transform: scale(1.1);
            background: #FFFFFF;
        }}
        
        .fullscreen-btn svg {{
            width: 20px;
            height: 20px;
            stroke: #1F2937;
        }}
        
        /* ===== KEYBOARD SHORTCUTS HELP ===== */
        .keyboard-help {{
            position: fixed;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.85);
            color: #FFFFFF;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 13px;
            z-index: 9999;
            backdrop-filter: blur(10px);
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            font-family: 'Inter', sans-serif;
        }}
        
        .keyboard-help.show {{
            opacity: 1;
        }}
        
        .keyboard-help kbd {{
            background: rgba(255, 255, 255, 0.2);
            padding: 2px 8px;
            border-radius: 4px;
            font-family: monospace;
            margin: 0 4px;
        }}
        
        /* ===== LOADING SPINNER ===== */
        .loading {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 9998;
        }}
        
        .spinner {{
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-top-color: #3B82F6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* ===== RESPONSIVE DESIGN ===== */
        @media (max-width: 768px) {{
            .controls {{
                bottom: 20px;
                right: 20px;
                gap: 10px;
            }}
            
            .btn {{
                padding: 10px 20px;
                font-size: 14px;
            }}
            
            .slide-counter {{
                bottom: 20px;
                left: 20px;
                padding: 10px 20px;
                font-size: 13px;
            }}
            
            .fullscreen-btn {{
                top: 20px;
                right: 20px;
            }}
        }}
        
        /* ===== PRINT STYLES ===== */
        @media print {{
            .controls,
            .slide-counter,
            .progress-container,
            .fullscreen-btn,
            .keyboard-help {{
                display: none !important;
            }}
            
            .slide-wrapper {{
                page-break-after: always;
                display: block !important;
                opacity: 1 !important;
                transform: none !important;
                position: relative !important;
            }}
            
            body {{
                overflow: visible;
            }}
        }}
    </style>
</head>
<body>
    <!-- Progress Bar -->
    <div class="progress-container">
        <div class="progress-bar" id="progressBar"></div>
    </div>
    
    <!-- Slide Counter -->
    <div class="slide-counter" id="slideCounter">
        <span class="current">1</span> / {total_slides}
    </div>
    
    <!-- Fullscreen Button -->
    <button class="fullscreen-btn" id="fullscreenBtn" title="Toggle Fullscreen (F)">
        <svg fill="none" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-5v4m0-4h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5"/>
        </svg>
    </button>
    
    <!-- Keyboard Shortcuts Help -->
    <div class="keyboard-help" id="keyboardHelp">
        <kbd>←</kbd> <kbd>→</kbd> Navigate • <kbd>Space</kbd> Next • <kbd>F</kbd> Fullscreen • <kbd>?</kbd> Help
    </div>
    
    <!-- Slides Container -->
    <div class="slide-container" id="slideContainer">
        {slides_html}
    </div>
    
    <!-- Navigation Controls -->
    <div class="controls">
        <button class="btn" id="prevBtn" onclick="changeSlide(-1)">
            ← Previous
        </button>
        <button class="btn" id="nextBtn" onclick="changeSlide(1)">
            Next →
        </button>
    </div>
    
    <script>
        // ===== PRESENTATION CONTROLLER =====
        class PresentationController {{
            constructor() {{
                this.currentSlide = 0;
                this.slides = document.querySelectorAll('.slide-wrapper');
                this.totalSlides = this.slides.length;
                this.progressBar = document.getElementById('progressBar');
                this.slideCounter = document.getElementById('slideCounter');
                this.prevBtn = document.getElementById('prevBtn');
                this.nextBtn = document.getElementById('nextBtn');
                this.keyboardHelp = document.getElementById('keyboardHelp');
                this.isTransitioning = false;
                
                this.init();
            }}
            
            init() {{
                this.showSlide(0);
                this.setupEventListeners();
                this.updateControls();
                
                // Show keyboard help briefly on load
                setTimeout(() => {{
                    this.showKeyboardHelp();
                    setTimeout(() => this.hideKeyboardHelp(), 3000);
                }}, 1000);
            }}
            
            setupEventListeners() {{
                // Keyboard navigation
                document.addEventListener('keydown', (e) => {{
                    if (this.isTransitioning) return;
                    
                    switch(e.key) {{
                        case 'ArrowRight':
                        case ' ':
                            e.preventDefault();
                            this.next();
                            break;
                        case 'ArrowLeft':
                            e.preventDefault();
                            this.previous();
                            break;
                        case 'Home':
                            e.preventDefault();
                            this.goToSlide(0);
                            break;
                        case 'End':
                            e.preventDefault();
                            this.goToSlide(this.totalSlides - 1);
                            break;
                        case 'f':
                        case 'F':
                            e.preventDefault();
                            this.toggleFullscreen();
                            break;
                        case '?':
                            e.preventDefault();
                            this.toggleKeyboardHelp();
                            break;
                    }}
                }});
                
                // Fullscreen button
                document.getElementById('fullscreenBtn').addEventListener('click', () => {{
                    this.toggleFullscreen();
                }});
                
                // Touch/swipe support
                let touchStartX = 0;
                let touchEndX = 0;
                
                document.addEventListener('touchstart', (e) => {{
                    touchStartX = e.changedTouches[0].screenX;
                }}, false);
                
                document.addEventListener('touchend', (e) => {{
                    touchEndX = e.changedTouches[0].screenX;
                    this.handleSwipe();
                }}, false);
                
                const handleSwipe = () => {{
                    if (touchEndX < touchStartX - 50) this.next();
                    if (touchEndX > touchStartX + 50) this.previous();
                }};
                
                this.handleSwipe = handleSwipe;
            }}
            
            showSlide(index) {{
                if (index < 0 || index >= this.totalSlides || this.isTransitioning) return;
                
                this.isTransitioning = true;
                
                // Hide current slide
                const currentSlideEl = this.slides[this.currentSlide];
                if (currentSlideEl) {{
                    currentSlideEl.classList.add('exiting');
                    setTimeout(() => {{
                        currentSlideEl.classList.remove('active', 'exiting');
                    }}, 600);
                }}
                
                // Show new slide
                setTimeout(() => {{
                    this.currentSlide = index;
                    this.slides[index].classList.add('active');
                    this.updateProgress();
                    this.updateControls();
                    
                    setTimeout(() => {{
                        this.isTransitioning = false;
                    }}, 800);
                }}, 100);
            }}
            
            next() {{
                if (this.currentSlide < this.totalSlides - 1) {{
                    this.showSlide(this.currentSlide + 1);
                }}
            }}
            
            previous() {{
                if (this.currentSlide > 0) {{
                    this.showSlide(this.currentSlide - 1);
                }}
            }}
            
            goToSlide(index) {{
                this.showSlide(index);
            }}
            
            updateProgress() {{
                const progress = ((this.currentSlide + 1) / this.totalSlides) * 100;
                this.progressBar.style.width = progress + '%';
                
                const counterCurrent = this.slideCounter.querySelector('.current');
                counterCurrent.textContent = this.currentSlide + 1;
            }}
            
            updateControls() {{
                this.prevBtn.disabled = this.currentSlide === 0;
                this.nextBtn.disabled = this.currentSlide === this.totalSlides - 1;
            }}
            
            toggleFullscreen() {{
                if (!document.fullscreenElement) {{
                    document.documentElement.requestFullscreen().catch(err => {{
                        console.log('Fullscreen error:', err);
                    }});
                }} else {{
                    document.exitFullscreen();
                }}
            }}
            
            showKeyboardHelp() {{
                this.keyboardHelp.classList.add('show');
            }}
            
            hideKeyboardHelp() {{
                this.keyboardHelp.classList.remove('show');
            }}
            
            toggleKeyboardHelp() {{
                this.keyboardHel