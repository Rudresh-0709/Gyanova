import re

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\v2\block_catalog_v2.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add sequentialSteps to BLOCK_CATALOG
text = text.replace(
'''    ("smart_layout", "processSteps"): BlockSpec(
        family="smart_layout",
        variant="processSteps",
        width_class="normal",
        supported_layouts=("left", "right", "blank"),
        density_ok=("sparse", "balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="processSteps",
        intent_fit=("teach", "demo", "explain"),
    ),''',
'''    ("smart_layout", "processSteps"): BlockSpec(
        family="smart_layout",
        variant="processSteps",
        width_class="normal",
        supported_layouts=("left", "right", "blank"),
        density_ok=("sparse", "balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="processSteps",
        intent_fit=("teach", "demo", "explain"),
    ),
    ("smart_layout", "sequentialSteps"): BlockSpec(
        family="smart_layout",
        variant="sequentialSteps",
        width_class="wide",
        supported_layouts=("top", "bottom", "blank"),
        density_ok=("balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="sequentialSteps",
        intent_fit=("teach", "demo", "explain", "sequence"),
    ),'''
)

# 2. Add sequentialSteps to intents
text = text.replace(
    '''("teach", "mechanism"):     ["processSteps", "processAccordion", "timelineSequential"],''',
    '''("teach", "mechanism"):     ["processSteps", "processAccordion", "timelineSequential", "sequentialSteps"],'''
)

text = text.replace(
    '''("teach", "sequence"):      ["processSteps", "processArrow", "timeline"],''',
    '''("teach", "sequence"):      ["processSteps", "sequentialSteps", "processArrow", "timeline"],'''
)

text = text.replace(
    '''("demo", "sequence"):       ["sequentialOutput", "processSteps", "timeline"],''',
    '''("demo", "sequence"):       ["sequentialOutput", "processSteps", "sequentialSteps", "timeline"],'''
)

text = text.replace(
    '''("demo", "mechanism"):      ["processArrow", "sequentialOutput", "processSteps"],''',
    '''("demo", "mechanism"):      ["processArrow", "sequentialOutput", "sequentialSteps", "processSteps"],'''
)

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\v2\block_catalog_v2.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text)

