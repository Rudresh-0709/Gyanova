import re

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\scratch\old_css.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Extract diamondGrid or similar variants
blocks = re.findall(r'(\.smart-layout\[data-variant="[^"]*diamond[^"]*"\][^{]*\{[^}]+\})', css, re.IGNORECASE)
for b in blocks:
    print(b)
