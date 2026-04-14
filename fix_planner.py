import re

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\v2\designer_slide_planning_v2_node.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''def _build_designer_blueprint(
    *,
    teacher_slide: Dict[str, Any],
    selected_template: str,
    primary_family: str,
    primary_variant: str,
    smart_layout_variant: str,
    primary_block: Dict[str, Any],
    supporting_blocks: List[Dict[str, Any]],
    composition_style: str,
    image_need: str,
    image_tier: str,
    layout: str,
) -> Dict[str, Any]:
    return {
        "smart_layout_variant": smart_layout_variant,
        "composition_style": composition_style,
        "layout": layout,
        "image_need": image_need,
        "image_tier": image_tier,
        "primary_block": primary_block,
        "supporting_blocks": supporting_blocks,
        "notes": [
            f"Planned smart_layout variant: {smart_layout_variant or 'none'}",
            f"Composition style: {composition_style}",
            f"Layout directive: {layout}"
        ],
    }''',
'''def _build_designer_blueprint(
    *,
    teacher_slide: Dict[str, Any],
    selected_template: str,
    primary_family: str,
    primary_variant: str,
    smart_layout_variant: str,
    primary_block: Dict[str, Any],
    supporting_blocks: List[Dict[str, Any]],
    composition_style: str,
    image_need: str,
    image_tier: str,
    layout: str,
) -> Dict[str, Any]:
    template = get_template_spec(selected_template)
    return {
        "template": {
            "name": template.name,
            "is_sparse": template.is_sparse,
            "image_mode_capability": template.image_mode_capability,
            "image_mode_required": template.image_mode_required,
            "max_blocks": template.max_blocks,
            "max_supporting_blocks": template.max_supporting_blocks,
            "supports_high_end_image": template.supports_high_end_image,
        },
        "primary_block": primary_block,
        "primary_family": primary_family,
        "primary_variant": primary_variant,
        "smart_layout_variant": smart_layout_variant,
        "supporting_blocks": supporting_blocks,
        "composition_style": composition_style,
        "image_need": image_need,
        "image_tier": image_tier,
        "layout": layout,
        "notes": [
            f"Teacher intent: {teacher_slide.get('teaching_intent', 'explain')}",
            f"Coverage scope: {teacher_slide.get('coverage_scope', 'foundation')}",
            f"Planned smart_layout variant: {smart_layout_variant or 'none'}",
            f"Composition style: {composition_style}",
            f"Layout directive: {layout}"
        ],
    }'''
)

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\v2\designer_slide_planning_v2_node.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text)

