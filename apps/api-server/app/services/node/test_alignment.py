import sys
import os
import json
import re
import importlib.util

# Setup paths
services_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, services_dir)

# Import segment_narration normally (audio node has no broken chains)
from node.audio_generation_node import segment_narration
from llm.model_loader import load_openai

# Import generator DIRECTLY (bypass gyml/__init__.py which pulls in composer→fitness→broken path)
gen_path = os.path.join(services_dir, "node", "slides", "gyml", "generator.py")
spec = importlib.util.spec_from_file_location("gyml_generator", gen_path)
gen_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_mod)
GyMLContentGenerator = gen_mod.GyMLContentGenerator


def generate_narration(slide_title, slide_goal, subtopic_name):
    """Generate narration with the updated prompt (elaboration, not repetition)."""
    llm = load_openai()
    prompt = f"""
    You are an expert teacher. Write the spoken narration for a slide.

    CONTEXT:
    - Subtopic: {subtopic_name}
    - Slide Title: {slide_title}
    - Slide Goal: {slide_goal}

    RULES:
    1. Write exactly what the teacher would say.
    2. Be engaging, clear, and pedagogically sound.
    3. 120-180 words.
    4. NO markdown, NO "In this slide", NO "Moving on".
    5. Your narration EXPLAINS what the student sees on screen.
       The slide will show short labels, card headings, and brief summaries.
       Your job is to ELABORATE with deeper context, examples, real-world
       connections, and analogies that are NOT written on screen.
       Do NOT just read out what the slide says — add value beyond the visuals.
    """
    resp = llm.invoke([{"role": "user", "content": prompt}])
    return resp.content.strip()


def count_layout_items(gyml: dict) -> int:
    for block in gyml.get("contentBlocks", []):
        if block.get("type") == "smart_layout":
            return len(block.get("items", []))
    return 0


def get_onscreen_texts(gyml: dict) -> list:
    texts = []
    for block in gyml.get("contentBlocks", []):
        if block.get("type") == "smart_layout":
            for item in block.get("items", []):
                for key in ("heading", "description"):
                    if item.get(key):
                        texts.append(item[key])
        elif block.get("type") in ("paragraph", "intro_paragraph", "outro_paragraph"):
            if block.get("text"):
                texts.append(block["text"])
    return texts


def check_overlap(narration: str, onscreen: list) -> list:
    narr_sentences = [
        s.strip() for s in re.split(r"[.!?]+", narration) if len(s.strip()) > 25
    ]
    overlaps = []
    for ns in narr_sentences:
        for ot in onscreen:
            if len(ot) > 25 and (ns.lower() in ot.lower() or ot.lower() in ns.lower()):
                overlaps.append(f"NARR: {ns[:50]}... ↔ SCREEN: {ot[:50]}...")
    return overlaps


def test_slide(title, goal, subtopic, idx):
    print(f"\n{'─'*60}")
    print(f"  SLIDE {idx}: {title}")
    print(f"{'─'*60}")

    # 1. Generate narration
    print("  1️⃣  Generating narration...")
    narration = generate_narration(title, goal, subtopic)
    words = len(narration.split())
    print(f"     ({words} words)")
    # Print first 2 sentences
    sentences = [s.strip() for s in narration.split(".") if s.strip()]
    for s in sentences[:2]:
        print(f"     > {s}.")

    # 2. Count segments
    segments = segment_narration(narration, "points")
    n_seg = len(segments)
    print(f"\n  2️⃣  Narration segments: {n_seg}")
    for i, seg in enumerate(segments):
        print(f"     [{i}] {seg[:65]}{'...' if len(seg)>65 else ''}")

    # 3. Generate GyML
    print(f"\n  3️⃣  Generating GyML (point_count={n_seg})...")
    gen = GyMLContentGenerator()
    gyml = gen.generate(
        narration=narration,
        title=title,
        purpose="explain",
        subtopic=subtopic,
        point_count=n_seg,
    )

    # 4. Analyze
    n_items = count_layout_items(gyml)
    onscreen = get_onscreen_texts(gyml)

    print(f"     Intent: {gyml.get('intent', '?')}")
    print(f"     Blocks: {len(gyml.get('contentBlocks', []))}")
    for block in gyml.get("contentBlocks", []):
        t = block.get("type", "?")
        if t == "smart_layout":
            v = block.get("variant", "?")
            n = len(block.get("items", []))
            print(f"       → {t} ({v}): {n} items")
            for item in block.get("items", []):
                h = item.get("heading", "")
                d = item.get("description", "")[:40]
                print(f"         • {h}: {d}...")
        else:
            txt = block.get("text", "")[:50]
            print(f"       → {t}: {txt}...")

    # 5. Alignment
    aligned = n_items == n_seg
    print(
        f"\n  4️⃣  ALIGNMENT: {n_seg} segments → {n_items} items {'✅' if aligned else '❌'}"
    )

    # 6. Overlap
    overlaps = check_overlap(narration, onscreen)
    if overlaps:
        print(f"  5️⃣  ⚠ OVERLAP ({len(overlaps)}):")
        for o in overlaps[:3]:
            print(f"       {o}")
    else:
        print(f"  5️⃣  ✅ No verbatim overlap")

    return aligned, len(overlaps)


def main():
    subtopic = "Introduction to Computer Generations"
    slides = [
        (
            "The Five Generations of Computers",
            "Students understand the five eras of computing and their technologies.",
        ),
        (
            "Vacuum Tubes: The First Generation",
            "Students learn about vacuum tube technology in first-gen computers.",
        ),
        (
            "Advantages and Limitations of Early Computers",
            "Students compare strengths and weaknesses of first-gen computing.",
        ),
    ]

    print("=" * 60)
    print("  CONTENT-NARRATION ALIGNMENT TEST")
    print("=" * 60)

    results = []
    for i, (title, goal) in enumerate(slides, 1):
        aligned, overlaps = test_slide(title, goal, subtopic, i)
        results.append((title, aligned, overlaps))

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    for title, aligned, overlaps in results:
        a = "✅" if aligned else "❌"
        o = "✅" if overlaps == 0 else f"⚠ {overlaps}"
        print(f"  {a} {title} | overlap: {o}")

    n_aligned = sum(1 for _, a, _ in results if a)
    print(f"\n  Aligned: {n_aligned}/{len(results)}")


if __name__ == "__main__":
    main()
