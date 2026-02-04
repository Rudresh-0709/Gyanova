import os

css_path = "services/node/slides/gyml/styles/gyml_theme.css"
with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Replace block-separator style
new_style = """
/* 1. SECTION SEPARATORS (Geometry) */
.block-separator {
    height: 2px;
    width: 60px; /* Short geometric line */
    background: var(--accent-primary); /* Use accent color */
    margin: var(--space-md) auto; /* Centered with vertical space */
    opacity: 0.6;
    border-radius: 2px;
}
"""

# RegEx replacement might be hard, let's just append or replace
# We know where it is roughly from previous write
if ".block-separator {" in css:
    # Need to replace the block
    import re

    css = re.sub(r"\.block-separator \{[^}]+\}", new_style.strip(), css)
else:
    css += new_style

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css)

print("Enhanced separator styles.")
