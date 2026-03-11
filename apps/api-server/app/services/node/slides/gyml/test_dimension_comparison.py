import sys
import os
from pathlib import Path
import json

# Add the correct paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.services.node.slides.gyml.serializer import GyMLSerializer
from app.services.node.slides.gyml.renderer import GyMLRenderer
from app.services.node.slides.gyml.definitions import ComposedBlock
from app.services.node.slides.gyml.constants import BlockType

def test_dimension_comparison():
    serializer = GyMLSerializer()
    renderer = GyMLRenderer()
    
    # 1. Dimension-centric data for CARDS (2 items)
    cards_content = {
        "variant": "comparison",
        "items": [
            {
                "heading": "Power Source",
                "points": ["Monarchy: Divine Right of Kings", "Republic: Popular Sovereignty"]
            },
            {
                "heading": "Leadership",
                "points": ["Monarchy: Hereditary King/Queen", "Republic: Elected Representative"]
            }
        ]
    }
    
    # 2. Dimension-centric data for TABLE (5 items)
    table_content = {
        "variant": "comparison",
        "items": [
            {"heading": "Source of Authority", "points": ["Monarchy: Divine Right", "Republic: People's Will"]},
            {"heading": "Head of State", "points": ["Monarchy: King Louis XVI", "Republic: National Convention"]},
            {"heading": "Legal System", "points": ["Monarchy: Royal Decrees", "Republic: Declaration of Rights"]},
            {"heading": "Social Structure", "points": ["Monarchy: Estate System", "Republic: Citizen Equality"]},
            {"heading": "Key Symbol", "points": ["Monarchy: Fleur-de-lis", "Republic: Tricolore Flag"]}
        ]
    }
    
    # Create ComposedBlocks
    cards_block = ComposedBlock(type=BlockType.SMART_LAYOUT, content=cards_content)
    table_block = ComposedBlock(type=BlockType.SMART_LAYOUT, content=table_content)
    
    # Serialize
    cards_node = serializer._serialize_block(cards_block)
    table_node = serializer._serialize_block(table_block)
    
    # Render
    html_cards = renderer._render_node(cards_node)
    html_table = renderer._render_node(table_node)
    
    # Get Styles
    gamma_styles = renderer._get_gamma_styles()
    theme_styles = renderer.theme.to_css_vars()
    resp_styles = renderer._get_responsive_styles()
    
    output = f"""<!DOCTYPE html>
<html>
<head>
    <title>Dimension Comparison Test</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css" rel="stylesheet">
    <style>
        {gamma_styles}
        {theme_styles}
        {resp_styles}
        body {{
            background: #0f172a;
            color: #f8fafc;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            padding: 4rem;
            max-width: 1000px;
            margin: 0 auto;
        }}
        h2 {{ color: #38bdf8; margin-top: 3rem; border-bottom: 1px solid #1e293b; padding-bottom: 0.5rem; }}
        .gyml-deck {{ width: 100%; }}
        section {{ padding: 2rem; border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; background: rgba(255,255,255,0.02); margin-bottom: 2rem; }}
        
        /* Ensure cards look good in the test environment */
        .smart-layout {{ display: flex; gap: 1.5rem; flex-wrap: wrap; margin-top: 1.5rem; }}
        .card {{ 
            background: rgba(30, 41, 59, 0.7); 
            backdrop-filter: blur(10px); 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 16px; 
            padding: 1.5rem; 
            flex: 1 1 300px; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .card-title {{ margin-top: 0; color: #38bdf8; font-size: 1.25rem; font-weight: 700; }}
    </style>
</head>
<body class="dark">
    <h1>Dimension-Centric Comparison Test</h1>
    <p>This test verifies the "Dimension-centric" logic where each item is a criterion.</p>
    
    <div class="gyml-deck">
        <section class="slide-section">
            <h2>1. Comparison Cards (≤ 3 Items)</h2>
            <p>Should show two subjects side-by-side inside each card.</p>
            {html_cards}
        </section>

        <section class="slide-section">
            <h2>2. Comparison Table (> 3 Items)</h2>
            <p>Should pivot the items into columns (Subjects) and rows (Dimensions).</p>
            {html_table}
        </section>
    </div>
</body>
</html>
"""
    
    output_path = Path(__file__).parent / "test_dim_cmp_output.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"✅ Generated verification page: {output_path}")

if __name__ == "__main__":
    test_dimension_comparison()
