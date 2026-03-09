import json

with open("test_output_history.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for slide in d["slides"]["hist-fr"]:
    # Remove cached real image URLs and HTML to force regeneration
    slide.pop("accent_image_url", None)
    slide.pop("html_content", None)

    # Also verify imageStyle is present
    if "gyml_content" in slide:
        slide["gyml_content"]["imageStyle"] = "Illustration"

with open("test_output_history.json", "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2)

print("Cleared cache and forced Illustration style in test JSON.")
