
import json

file_path = r"d:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\test_output_variants.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Slides are in data["slides"]["variants"]
# Slide 1 (index 0) is Hub and Spoke
# Slide 2 (index 1) is Process Arrow

for i in [0, 1]:
    if i < len(data["slides"]["variants"]):
        gyml = data["slides"]["variants"][i]["gyml_content"]
        for block in gyml.get("contentBlocks", []):
            if block["type"] in ["hub_and_spoke", "process_arrow_block"]:
                for item in block.get("items", []):
                    if "color" in item:
                        del item["color"]

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("Successfully removed color overrides for Slide 1 and 2.")
