
import os

file_path = r"d:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\slides\gyml\renderer.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace Hub-and-Spoke and Process Arrow palettes back to blue
old_p = '        vibrant_palette = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]'
new_p = '        blue_palette = ["#1e3a8a", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]'

# Handle both instances if they are identical
if old_p in content:
    content = content.replace(old_p, new_p)
    content = content.replace('color = item.color or vibrant_palette[i % len(vibrant_palette)]', 'color = item.color or blue_palette[i % len(blue_palette)]')

# Also check for the Process Arrow one which might have a different indent or list
# Re-reading the file content to be sure of the PA one
# PA one was: vibrant_palette = ["#6366f1", "#ec4899", "#06b6d4", "#10b981"]

old_p_pa = '        vibrant_palette = ["#6366f1", "#ec4899", "#06b6d4", "#10b981"]'
if old_p_pa in content:
    content = content.replace(old_p_pa, new_p)

if new_p in content:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully restored blue palettes.")
else:
    print("Could not find the target vibrant palette strings.")
    # Fallback to a broader search if literal replacement fails
    if "vibrant_palette =" in content:
         import re
         content = re.sub(r'vibrant_palette = \[.*?\]', new_p.strip(), content)
         content = content.replace('vibrant_palette[', 'blue_palette[')
         with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
         print("Restored using regex fallback.")
