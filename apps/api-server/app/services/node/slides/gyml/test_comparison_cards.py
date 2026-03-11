import sys
import os
from pathlib import Path

# Add the correct paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.services.node.slides.gyml.definitions import GyMLComparisonTable
from app.services.node.slides.gyml.renderer import Renderer

def render_test_table():
    table = GyMLComparisonTable(
        headers=["First Estate: Clergy", "Second Estate: Nobility", "Third Estate: Commoners"],
        rows=[
            ["Held significant religious power.", "Owned large land estates.", "Included peasants and bourgeoisie."],
            ["Exempt from many taxes.", "Exempt from most taxes.", "Paid heavy taxes."],
            ["Spiritual guidance.", "Few economic burdens.", "Carried most economic burdens."]
        ],
        caption="The Three Estates of Pre-Revolutionary France"
    )
    
    renderer = Renderer()
    html = renderer._render_comparison_table(table)
    
    css = renderer._get_core_css() # or from template directly if needed to check
    
    output = f"""<!DOCTYPE html>
<html>
<head>
    <title>Comparison Table Test</title>
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    <style>
        body {{
            background: #111;
            color: #fff;
            font-family: system-ui, -apple-system, sans-serif;
            padding: 2rem;
        }}
        {renderer.core_css}
    </style>
</head>
<body class="dark">
    {html}
</body>
</html>
"""
    
    output_path = Path(__file__).parent / "test_comparison_cards_output.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"✅ Generated: {output_path}")

if __name__ == "__main__":
    render_test_table()
