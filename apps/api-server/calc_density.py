"""
Calculate slide density for each slide from the workflow test log,
using the same formula as fitness.py:

density = (word_count / 250) + (block_count * 0.08) + (internal_items * 0.03) + (0.35 if image else 0)
"""

slides = [
    {
        "title": "First Generation Computers Overview",
        "blocks": [
            {"type": "intro_paragraph", "words": 56},
        ],
        "has_image": True,
        "internal_items": 0,
    },
    {
        "title": "Vacuum Tubes: The Core Technology",
        "blocks": [
            {"type": "intro_paragraph", "words": 30},
            {"type": "smart_layout", "words": 80, "items": 4},
            {"type": "annotation_paragraph", "words": 22},
        ],
        "has_image": True,
        "internal_items": 4,
    },
    {
        "title": "Electromechanical Components",
        "blocks": [
            {"type": "intro_paragraph", "words": 28},
            {"type": "smart_layout", "words": 90, "items": 5},
            {"type": "annotation_paragraph", "words": 15},
        ],
        "has_image": True,
        "internal_items": 5,
    },
    {
        "title": "Architecture of First Gen Computer",
        "blocks": [
            {"type": "intro_paragraph", "words": 30},
            {"type": "smart_layout_labeled_diagram", "words": 30, "items": 4},
            {"type": "annotation_paragraph", "words": 40},
        ],
        "has_image": True,
        "internal_items": 4,
    },
    {
        "title": "Evolution Timeline: 1940-1959",
        "blocks": [
            {"type": "intro_paragraph", "words": 25},
            {"type": "smart_layout", "words": 70, "items": 4},
            {"type": "outro_paragraph", "words": 25},
        ],
        "has_image": True,
        "internal_items": 4,
    },
    {
        "title": "Vacuum Tubes vs Electromechanical",
        "blocks": [
            {"type": "intro_paragraph", "words": 28},
            {"type": "comparison_table", "words": 100, "items": 4},
        ],
        "has_image": True,
        "internal_items": 4,
    },
]

print("=" * 70)
print(f"{'Slide':<45} {'Density':>8}  {'Profile'}")
print("=" * 70)

densities = []
for s in slides:
    total_words = sum(b.get("words", 0) for b in s["blocks"])
    block_count = len(s["blocks"])
    internal_items = s["internal_items"]
    has_image = s["has_image"]

    word_util = total_words / 250
    struct_util = (block_count * 0.08) + (internal_items * 0.03)
    image_util = 0.35 if has_image else 0.0
    density = word_util + struct_util + image_util

    if density > 0.95:
        profile = "super_dense"
    elif density > 0.70:
        profile = "dense"
    elif density > 0.45:
        profile = "balanced"
    else:
        profile = "impact"

    densities.append(density)
    print(f"  {s['title']:<43} {density:>6.2f}  -> {profile}")

print("=" * 70)
print(
    f"\n  Min: {min(densities):.2f}  Max: {max(densities):.2f}  Avg: {sum(densities)/len(densities):.2f}"
)
print(f"  All super_dense: {all(d > 0.95 for d in densities)}")

print("\n\n" + "=" * 70)
print("WITH PROPOSED NEW THRESHOLDS:")
print("=" * 70)
for i, s in enumerate(slides):
    d = densities[i]
    if d > 1.30:
        profile = "super_dense"
    elif d > 1.00:
        profile = "dense"
    elif d > 0.60:
        profile = "balanced"
    else:
        profile = "impact"
    print(f"  {s['title']:<43} {d:>6.2f}  -> {profile}")
