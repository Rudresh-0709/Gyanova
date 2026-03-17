
import os

path = r"d:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\test_preview_variants\ultra_dense_test.html"

if not os.path.exists(path):
    print("File not found")
    exit()

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

print(f"File size: {len(content)} characters")

# Check for presence of key blocks
print(f"Has cyclic-container: {'cyclic-container' in content}")
print(f"Has fs-radial-container: {'fs-radial-container' in content}")
print(f"Has Furthermore: {'Furthermore' in content}")

# Find the end of the section and print structure
idx = content.find('<section id="ultra_test"')
if idx != -1:
    section_end = content.find('</section>', idx) + 10
    print("\n--- Section Structure ---")
    print(content[idx:idx+200])
    print("...")
    print(content[section_end-200:section_end])
else:
    print("Section not found")

# Check for carriage returns
print(f"\nCarriage returns count: {content.count('\\r')}")
print(f"Newlines count: {content.count('\\n')}")
