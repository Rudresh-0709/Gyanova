import app.services.node.slides.gyml.generator
from app.services.node.slides.gyml.definitions import GyMLComparisonTable
from app.services.node.slides.gyml.renderer import GyMLRenderer
from pathlib import Path

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
    
    renderer = GyMLRenderer()
    html = renderer._render_comparison_table(table)
    
    css = renderer._get_gamma_styles() 
    
    output = f"""<!DOCTYPE html>
<html>
<head>
    <title>Comparison Table Test</title>
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    <style>
        body {{
            background: #0f172a;
            color: #ffffff;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            padding: 4rem 2rem;
        }}
        {css}
    </style>
</head>
<body class="dark">
    {html}
</body>
</html>
"""
    
    output_path = Path(__file__).parent / "test_cmp_output.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"✅ Generated: {output_path}")

if __name__ == "__main__":
    render_test_table()
