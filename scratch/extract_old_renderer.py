import re
with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\scratch\old_renderer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# find CSS dictionary
match = re.search(r'(_CSS_SNIPPETS\s*=\s*\{.*?\})', content, re.DOTALL)
if match:
    css_dict = match.group(1)
    # Extract diamondGrid
    dg_match = re.search(r'("diamondGrid"\s*:\s*"""(.*?)""")', css_dict, re.DOTALL)
    if dg_match:
        print("DIAMOND GRID CSS from e3a3a44:")
        print(dg_match.group(2))
    else:
        print("diamondGrid not found in CSS snippets")
else:
    print("Could not find _CSS_SNIPPETS")
