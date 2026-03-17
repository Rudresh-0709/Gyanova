
import os
import json
import sys

# Set encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8", errors="replace")

# Ensure we can import from the subdirectories
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "slides", "gyml")))

from slides.gyml.generator import GyMLContentGenerator
from slides.gyml.renderer import GyMLRenderer
from slides.gyml.definitions import (
    GyMLSection, GyMLBody, GyMLParagraph, GyMLCyclicBlock, 
    GyMLCyclicItem, GyMLFeatureShowcaseBlock, GyMLFeatureShowcaseItem,
    GyMLImage
)

def test_ultra_density():
    generator = GyMLContentGenerator()
    
    print("[LOG] Generating complex content via LLM...")
    # Generate a cyclic block slide first
    result_cyclic = generator.generate(
        title="Agile Product Lifecycle",
        goal="Detail the full iterative cycle of modern product development from ideation to scale.",
        purpose="process",
        subtopic="Product Management",
        content_angle="mechanism",
        template_name="Cyclic process block",
        slide_index=5
    )
    
    # Generate a showcase block slide
    result_showcase = generator.generate(
        title="Modern Tech Stack",
        goal="Showcase the various layers of a modern enterprise application stack.",
        purpose="showcase",
        subtopic="System Architecture",
        content_angle="visualization",
        template_name="Feature showcase block",
        slide_index=1
    )
    
    # helper to convert dict to proper objects
    def dict_to_node(d):
        t = d.get("type")
        if t in ["paragraph", "intro_paragraph", "context_paragraph", "outro_paragraph", "callout", "takeaway"]:
            return GyMLParagraph(text=d.get("text") or d.get("content", ""), variant=t)
            
        # FORCE map cyclic_process_block or cyclic_block to the new GyMLCyclicBlock
        if t in ["cyclic_block", "cyclic_process_block"]:
            items = []
            for item in d.get("items", []):
                # Handle various LLM key names
                label = item.get("label") or item.get("heading") or "Item"
                description = item.get("description") or item.get("text") or item.get("content", "")
                icon = item.get("icon") or item.get("icon_name")
                
                # Filter for dataclass
                items.append(GyMLCyclicItem(
                    label=str(label),
                    description=str(description),
                    icon=str(icon) if icon else None,
                    image_url=item.get("image_url"),
                    color=item.get("color")
                ))
            return GyMLCyclicBlock(items=items, hub_label=d.get("hub_label"), variant=d.get("variant", "chevron"))
            
        # FORCE map feature_showcase_block or smart_layout to FeatureShowcaseBlock if it looks like features
        if t in ["feature_showcase_block", "smart_layout"]:
            items = []
            raw_items = d.get("items") or d.get("cards") or d.get("features", [])
            for item in raw_items:
                label = item.get("label") or item.get("heading") or item.get("title") or "Feature"
                description = item.get("description") or item.get("text") or item.get("content", "")
                icon = item.get("icon") or item.get("icon_name")
                if isinstance(icon, dict): icon = icon.get("alt") or icon.get("name")
                items.append(GyMLFeatureShowcaseItem(label=str(label), description=str(description), icon=str(icon) if icon else None))
            
            title = d.get("title") or d.get("hub_label") or d.get("label") or "Core System"
            return GyMLFeatureShowcaseBlock(title=str(title), items=items, image_url=d.get("image_url"))
            
        print(f"[WARN] Unknown block type: {t}")
        return None

    # 1. Slide 1: Intro + Cyclic
    children_slide1 = []
    # Intro from cyclic
    for b in result_cyclic.get("contentBlocks", []):
        if b["type"] in ["intro_paragraph", "paragraph"]:
            node = dict_to_node(b)
            if node: children_slide1.append(node)
            break
            
    # Cyclic Block
    for b in result_cyclic.get("contentBlocks", []):
        if b["type"] in ["cyclic_block", "cyclic_process_block"]:
            node = dict_to_node(b)
            if node: children_slide1.append(node)
            break

    section1 = GyMLSection(
        id="ultra_test_cyclic",
        image_layout="blank",
        slide_density="super_dense",
        body=GyMLBody(children=children_slide1)
    )

    # 2. Slide 2: Intermediate + Showcase
    children_slide2 = []
    children_slide2.append(GyMLParagraph(
        text="Furthermore, this cycle is supported by a robust internal architecture that powers every spoke of the operation."
    ))
    
    # Feature Showcase from showcase result
    for b in result_showcase.get("contentBlocks", []):
        if b["type"] in ["feature_showcase_block", "smart_layout"]:
            node = dict_to_node(b)
            if node: children_slide2.append(node)
            break

    section2 = GyMLSection(
        id="ultra_test_showcase",
        image_layout="blank",
        slide_density="super_dense",
        body=GyMLBody(children=children_slide2)
    )
    
    print(f"[LOG] Split into 2 slides: Slide1({len(children_slide1)} nodes), Slide2({len(children_slide2)} nodes)")
    
    # Render (Set animated=False to avoid opacity:0 issues in static preview)
    renderer = GyMLRenderer(animated=False)
    
    # Render both sections as a sequence (deck)
    full_html = renderer.render_complete([section1, section2])
    
    out_path = os.path.join(os.path.dirname(__file__), "test_preview_variants", "ultra_dense_test.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    
    print(f"[LOG] Slide rendered to: {out_path}")

if __name__ == "__main__":
    test_ultra_density()
