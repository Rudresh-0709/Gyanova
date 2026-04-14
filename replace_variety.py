import re

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\v2\variety_policy_v2.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '''def pick_smart_layout_variant(
    preferred_variant: str,
    allowed_variants: List[str],
    variant_history: List[str],
) -> str:''',
    '''def pick_smart_layout_variant(
    preferred_variant: Union[str, List[str]],
    allowed_variants: List[str],
    variant_history: List[str],
) -> str:'''
)

text = text.replace(
    '''    if not allowed_variants:
        return preferred_variant or "bigBullets"

    scored: List[Tuple[int, str]] = []
    for variant in allowed_variants:
        base = 10 if variant == preferred_variant else 0
        adjustment = score_smart_layout_variant(variant, variant_history)
        scored.append((base + adjustment, variant))

    scored.sort(key=lambda x: -x[0])
    return scored[0][1] if scored else (preferred_variant or "bigBullets")''',
    '''    if isinstance(preferred_variant, str):
        preferred_list = [preferred_variant] if preferred_variant else []
    else:
        preferred_list = list(preferred_variant or [])

    default_fallback = preferred_list[0] if preferred_list else "bigBullets"

    if not allowed_variants:
        return default_fallback

    scored: List[Tuple[int, str]] = []
    for variant in allowed_variants:
        base = 10 if variant in preferred_list else 0
        adjustment = score_smart_layout_variant(variant, variant_history)
        scored.append((base + adjustment, variant))

    if not scored:
        return default_fallback

    max_score = max(s[0] for s in scored)
    top_candidates = [s[1] for s in scored if s[0] == max_score]

    return random.choice(top_candidates)'''
)

with open(r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\apps\api-server\app\services\node\v2\variety_policy_v2.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text)

