import os

file_path = "services/node/slides/gyml/composer.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Search for the Card Grid check in _enforce_limits
# It was injected around line 550?
# Pattern: if block.type == BlockType.CARD_GRID.value:

insertion_index = -1
for i in range(len(lines)):
    if "if block.type == BlockType.CARD_GRID.value:" in lines[i]:
        # Insert BEFORE this line? Or AFTER the if block?
        # Let's insert before to be safe/clean
        insertion_index = i
        break

if insertion_index != -1:
    new_code = [
        "                if block.type == BlockType.TIMELINE.value:\n",
        '                    events = block.content.get("events", [])\n',
        "                    if len(events) > 4:\n",
        "                        return self._split_slide(slide)\n",
        "\n",
    ]
    lines[insertion_index:insertion_index] = new_code

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Added Timeline limit rule.")
else:
    print("Could not find insertion point.")
