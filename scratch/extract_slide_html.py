import json
import os

json_file = r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\.persistent_data\task_states\362d4a8b-0570-4143-9fa6-fe392eb7bcff.json'
output_file = r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\artifacts\first_slide.html'

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# The structure observed was:
# "slides": {
#   "sub_1_3b4e0b": [
#     {
#       "slide_id": "sub_1_3b4e0b_t1",
#       ...
#       "html_content": "..."
#     }
#   ]
# }

# Find the first slide in any subtopic array
first_slide_html = None
for subtopic_id, slides in data.get('result', {}).get('slides', {}).items():
    if slides:
        first_slide_html = slides[0].get('html_content')
        break

if first_slide_html:
    # Ensure artifacts directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(first_slide_html)
    print(f"Successfully wrote HTML to {output_file}")
else:
    print("Could not find html_content in the JSON file.")
