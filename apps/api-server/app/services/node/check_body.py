
import os

path = r"d:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\test_preview_variants\ultra_dense_test.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

body_start = content.find('<div class="body">')
body_end = content.find('</div>', body_start) if body_start != -1 else -1

if body_start != -1:
    # Get children types
    body_content = content[body_start:body_end+6]
    print(f"Body length: {len(body_content)}")
    
    # Check for specific blocks
    import re
    blocks = re.findall(r'<div class="([^"]+)"', body_content)
    print(f"Blocks found: {blocks[:10]}")
    
    # Check if children are empty
    print(f"First child: {body_content[:100]}")
else:
    print("Body not found")
