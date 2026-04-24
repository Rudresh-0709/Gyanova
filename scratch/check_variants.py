import json, re

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\.persistent_data\task_states\371db3e5-1529-4139-84e2-7e629a5bfe7e.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

result = data['result']
slides_dict = result['slides']

for sub_key, slides_list in slides_dict.items():
    print(f"=== {sub_key} ({len(slides_list)} slides) ===")
    for i, s in enumerate(slides_list):
        vc = s.get('visual_content', {})
        blocks = vc.get('contentBlocks', [])
        sl_block = next((b for b in blocks if isinstance(b, dict) and b.get('type') == 'smart_layout'), None)
        variant_llm = sl_block.get('variant', 'N/A') if sl_block else 'N/A'

        html = s.get('html_content', '')
        smart_matches = re.findall(r'class="smart-layout[^"]*"[^>]*data-variant="([^"]*)"', html)
        if not smart_matches:
            smart_matches = re.findall(r'data-variant="([^"]*)"', html[:5000])

        title = vc.get('title', '?')
        status = ""
        if variant_llm != 'N/A' and smart_matches:
            if variant_llm.lower() == smart_matches[0].lower() and variant_llm != smart_matches[0]:
                status = " [NORMALIZED]"
            elif variant_llm == smart_matches[0]:
                status = " [RAW - NOT NORMALIZED]"
        
        print(f"  Slide {i}: {title}")
        print(f"    LLM:  {variant_llm}")
        print(f"    HTML: {smart_matches[:2] if smart_matches else 'NONE'}{status}")
