import json, re

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\.persistent_data\task_states\b07cd38d-30ed-4d2f-8adb-f5b8202ce8aa.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

result = data['result']
slides_dict = result['slides']

# Check slide 3 (diamondGrid) - the one that was showing boxes
for sub_key, slides_list in slides_dict.items():
    slide = slides_list[3]  # The Prime Minister and Cabinet slide
    html = slide.get('html_content', '')
    
    # Find the smart-layout div and its context
    match = re.search(r'<div class="smart-layout[^"]*"[^>]*data-variant="([^"]*)"[^>]*>', html)
    if match:
        start = match.start()
        print(f"Smart layout div found at position {start}:")
        print(f"  {match.group()}")
        print()
    
    # Check CSS for diamondGrid rules
    style_match = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    if style_match:
        css = style_match.group(1)
        # Find all diamondGrid CSS rules
        dg_rules = re.findall(r'([^\n{]*diamondGrid[^\n{]*\{[^}]*\})', css, re.IGNORECASE)
        print(f"Total diamondGrid CSS rules found: {len(dg_rules)}")
        for r in dg_rules[:3]:
            print(f"  {r[:120]}...")
        print()
        
        # Also check for cardGridDiamond
        cgd_rules = re.findall(r'([^\n{]*cardGridDiamond[^\n{]*\{[^}]*\})', css, re.IGNORECASE)
        print(f"Total cardGridDiamond CSS rules found: {len(cgd_rules)}")
        for r in cgd_rules[:3]:
            print(f"  {r[:120]}...")
        print()
        
        # Check what variant-specific CSS exists at all
        all_variants_in_css = re.findall(r'data-variant="([^"]*)"', css)
        unique_variants = sorted(set(all_variants_in_css))
        print(f"All variant CSS selectors ({len(unique_variants)}):")
        for v in unique_variants:
            print(f"  - {v}")
    else:
        print("NO <style> block found in HTML!")
