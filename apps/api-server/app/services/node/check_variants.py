"""Check variant diversity in test_output_history.json"""
import json, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output_history.json")
data = json.load(open(path, encoding="utf-8"))

for sub_id, slides in data["slides"].items():
    print(f"Subtopic: {sub_id} ({len(slides)} slides)")
    for i, s in enumerate(slides):
        blocks = s.get("gyml_content", {}).get("contentBlocks", [])
        block_types = [b.get("type", "?") for b in blocks]
        
        # Find smart_layout variant
        variants = [b.get("variant", "?") for b in blocks if b.get("type") == "smart_layout"]
        variant_str = variants[0] if variants else "N/A"
        
        primary_idx = s.get("primary_block_index", 0)
        primary_type = blocks[primary_idx].get("type", "?") if primary_idx < len(blocks) else "?"
        if primary_type == "smart_layout" and primary_idx < len(blocks):
            primary_type += f"/{blocks[primary_idx].get('variant', '?')}"
        
        print(f"  Slide {i+1}: {s.get('title')}")
        print(f"    Angle:    {s.get('content_angle')}")
        print(f"    Template: {s.get('selected_template')}")
        print(f"    Density:  {s.get('slide_density')}")
        print(f"    Blocks:   {' -> '.join(block_types)}")
        print(f"    Primary:  [{primary_idx}] {primary_type}")
        print(f"    Variant:  {variant_str}")
        print()

# Check diversity
variants_used = []
for sub_id, slides in data["slides"].items():
    for s in slides:
        blocks = s.get("gyml_content", {}).get("contentBlocks", [])
        for b in blocks:
            if b.get("type") == "smart_layout":
                variants_used.append(b.get("variant"))

unique = set(variants_used)
print(f"Variant Diversity: {len(unique)}/{len(variants_used)} unique")
print(f"  Variants used: {variants_used}")
