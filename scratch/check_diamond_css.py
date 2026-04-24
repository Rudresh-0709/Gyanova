import json, re

file_path = r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\.persistent_data\task_states\2e785ddc-4b5d-41f7-a778-7698a7a9a60e.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

result = data.get("result", {}).get("slides", {})
slide_with_diamond = None
for sub_key, slides in result.items():
    for s in slides:
        html = s.get("html_content", "")
        if 'data-variant="diamondGrid"' in html:
            slide_with_diamond = s
            break

if slide_with_diamond:
    html = slide_with_diamond["html_content"]
    
    # Check classes of the smart-layout container
    match = re.search(r'<div class="smart-layout([^"]*)"[^>]*data-variant="diamondGrid"[^>]*data-item-count="([^"]*)"', html)
    if match:
        classes = match.group(1).strip()
        item_count = match.group(2)
        print(f"Container classes: '{classes}', item_count: {item_count}")
        
    # Check CSS rules for diamondGrid
    style_match = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    if style_match:
        css = style_match.group(1)
        grid_rules = re.findall(r'(\.smart-layout\[data-variant="diamondGrid"\]\s*(?:\.[^{\s]+)?\s*\{[^}]+\})', css)
        print(f"\ndiamondGrid CSS rules ({len(grid_rules)}):")
        for r in grid_rules[:5]:
            print("  " + r.replace('\n', ' '))
            
    # Check the HTML structure of the items
    items = re.findall(r'(<div class="card[^>]*>.*?</div>\s*</div>\s*</div>)', html, re.DOTALL)
    if items:
        print("\nFirst item HTML structure:")
        print("  " + items[0][:300].replace('\n', ' '))
else:
    print("Could not find a slide with diamondGrid in the HTML.")
