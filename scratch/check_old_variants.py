import json, re, subprocess

commit = "12629b9"
task_files = [
    ".persistent_data/task_states/17f0a9bb-ae75-4cdd-862c-78f0ce454716.json",
    ".persistent_data/task_states/362d4a8b-0570-4143-9fa6-fe392eb7bcff.json",
    ".persistent_data/task_states/631224b6-b20b-4fcf-afd5-fddb5b4c39c5.json",
    ".persistent_data/task_states/71713f7e-2edd-4067-a9f3-883ef2a30851.json",
    ".persistent_data/task_states/74a9b16f-489a-4be7-9f37-b9790de14e30.json",
]

print(f"=== VARIANTS FROM COMMIT {commit} ===\n")

for tf in task_files:
    r = subprocess.run(
        ["git", "show", f"{commit}:{tf}"],
        capture_output=True, cwd=r"d:\DATA\Desktop\AI_TUTOR\ai-teacher-app"
    )
    try:
        data = json.loads(r.stdout.decode("utf-8", errors="replace"))
    except:
        continue
    
    slides_dict = data.get("result", {}).get("slides", {})
    if not slides_dict:
        continue
    
    import os
    print(f"--- {os.path.basename(tf)} ---")
    for sub_key, slides_list in slides_dict.items():
        for i, s in enumerate(slides_list):
            vc = s.get("visual_content", {}) or {}
            blocks = vc.get("contentBlocks", []) or []
            sl_blocks = [b for b in blocks if isinstance(b, dict) and b.get("type") == "smart_layout"]
            llm_variants = [b.get("variant", "N/A") for b in sl_blocks]
            
            html = s.get("html_content", "")
            html_variants = re.findall(r'class="smart-layout[^"]*"[^>]*data-variant="([^"]*)"', html)
            if not html_variants:
                html_variants = re.findall(r'data-variant="([^"]*)"', html[:8000])
            
            title = vc.get("title", "?")
            
            if llm_variants:
                print(f"  Slide {i}: {title[:50]}")
                print(f"    LLM:  {llm_variants}")
                print(f"    HTML: {html_variants[:3]}")
    print()
