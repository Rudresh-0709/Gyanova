import os

file_path = "services/node/slides/gyml/composer.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Relax Timeline Rule (was > 4)
for i in range(len(lines)):
    if "if len(events) > 4:" in lines[i]:
        lines[i] = lines[i].replace("4", "5")
        print("Relaxed Timeline limit to 5.")

# Relax Card Grid Rule (was > 3)
for i in range(len(lines)):
    if "if len(cards) > 3:" in lines[i]:
        lines[i] = lines[i].replace("3", "5")
        print("Relaxed Card Grid limit to 5.")

# Save
with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Composer limits relaxed.")
