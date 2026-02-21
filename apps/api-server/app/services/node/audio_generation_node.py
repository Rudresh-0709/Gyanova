"""
Audio Generation Node

Uses OpenAI TTS to convert all narrations in the state into audio files.
Supports narration segmentation — point-based narrations are split into
individual audio files for slide animation sync triggers.

Narration sources:
1. lesson_intro_narration  → lesson-level opening
2. subtopic_intro_narrations → per-subtopic transitions
3. slides[sub_id][i].narration_text → per-slide spoken narration

Directory structure:
  audio_output/
  ├── lesson_intro.mp3
  ├── subtopic_intros/
  │   ├── sub_1_xxxxx.mp3
  │   └── sub_2_xxxxx.mp3
  └── slides/
      ├── sub_1_xxxxx_s1/
      │   ├── segment_1.mp3
      │   ├── segment_2.mp3
      │   └── segment_3.mp3
      └── sub_1_xxxxx_s2/
          └── full.mp3            (paragraph — single file)
"""

import os
import re
import sys
from typing import Dict, Any, List
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

try:
    from ..state import TutorState
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from state import TutorState

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

VOICE_MAP = {
    0: "alloy",
    1: "echo",
    2: "fable",
    3: "onyx",
    4: "nova",
    5: "shimmer",
}

DEFAULT_VOICE = "nova"
TTS_MODEL = "tts-1"

# Formats that should be split into segments
SEGMENTED_FORMATS = {"points", "sequential_points", "comparative_points"}
# Formats kept as a single audio file
SINGLE_FORMATS = {"paragraph", "data_interpretation"}

# Regex pattern for common point transition markers
# Matches: "First,", "Second,", "Third,", "Fourth,", "Fifth,",
#          "Next,", "Finally,", "However,", "Additionally,",
#          "As a result,", "For one,", "Moreover,", "Furthermore,",
#          "On the other hand,", "In contrast,", "So,", "Let's begin",
#          "Starting with", "Moving into", "Let's review"
POINT_SPLIT_PATTERN = re.compile(
    r"(?=\b(?:"
    r"First(?:ly)?,|"
    r"Second(?:ly)?,|"
    r"Third(?:ly)?,|"
    r"Fourth(?:ly)?,|"
    r"Fifth(?:ly)?,|"
    r"Next,|"
    r"Finally,|"
    r"However,|"
    r"Additionally,|"
    r"Moreover,|"
    r"Furthermore,|"
    r"As a result,|"
    r"For one,|"
    r"On the other hand,|"
    r"In contrast,|"
    r"So,\s|"
    r"Let's begin\b|"
    r"Starting with\b|"
    r"Moving into\b|"
    r"Let's review\b"
    r"))",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════════════════════
# SEGMENTATION LOGIC
# ═══════════════════════════════════════════════════════════════════════════


def segment_narration(text: str, narration_format: str) -> List[str]:
    """
    Split narration text into segments based on the narration format.

    For point-based formats: splits on transition markers.
    For paragraph/data_interpretation: returns text as a single segment.

    Returns:
        List of text segments (always at least 1).
    """
    if narration_format not in SEGMENTED_FORMATS:
        return [text.strip()]

    # Split using transition markers
    parts = POINT_SPLIT_PATTERN.split(text)

    # Clean up: remove empty/whitespace-only segments
    segments = [p.strip() for p in parts if p.strip()]

    # If splitting produced nothing useful, fall back to single segment
    if len(segments) <= 1:
        return [text.strip()]

    # Merge short segments (< 15 words) into the previous one to avoid
    # tiny audio clips that cause animation timing issues
    MIN_WORDS = 15
    merged = [segments[0]]
    for seg in segments[1:]:
        if len(seg.split()) < MIN_WORDS and merged:
            merged[-1] = merged[-1] + " " + seg
        else:
            merged.append(seg)

    return merged if len(merged) > 1 else [text.strip()]


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


def get_voice(state: Dict[str, Any]) -> str:
    """Resolve the OpenAI TTS voice from teacher_voice_id in state."""
    voice_id = state.get("teacher_voice_id")
    if voice_id is not None and voice_id in VOICE_MAP:
        return VOICE_MAP[voice_id]
    return DEFAULT_VOICE


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_audio(client: OpenAI, text: str, filepath: Path, voice: str) -> str:
    """
    Generate an audio file from text using OpenAI TTS.

    Returns:
        The string path of the saved audio file.
    """
    response = client.audio.speech.create(
        model=TTS_MODEL,
        voice=voice,
        input=text,
    )

    response.write_to_file(str(filepath))
    return str(filepath)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN NODE
# ═══════════════════════════════════════════════════════════════════════════


def audio_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node that generates audio for all narrations in the state.

    Processes:
    1. Lesson intro narration → single audio file
    2. Subtopic intro narrations → single audio file each
    3. Per-slide narrations → segmented based on narration_format

    Stores results as:
    - 'audio_url': path to full/single audio file
    - 'narration_segments': list of {text, audio_url, segment_index} dicts
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    voice = get_voice(state)

    # Resolve output directory
    base_dir = state.get("audio_output_dir", os.path.join(os.getcwd(), "audio_output"))
    output_dir = Path(base_dir)
    ensure_dir(output_dir)
    state["audio_output_dir"] = str(output_dir)

    print(f"🔊 [Audio Generation Node] Using voice: {voice}")
    print(f"📁 Output directory: {output_dir}")

    audio_count = 0

    # ─── 1. Lesson Intro Narration ──────────────────────────────────────────
    lesson_intro = state.get("lesson_intro_narration")
    if lesson_intro and lesson_intro.get("narration_text"):
        text = lesson_intro["narration_text"]
        filepath = output_dir / "lesson_intro.mp3"
        print(f"  🎙 Generating lesson intro audio...")

        try:
            path = generate_audio(client, text, filepath, voice)
            state["lesson_intro_narration"]["audio_url"] = path
            state["lesson_intro_narration"]["narration_segments"] = [
                {"text": text, "audio_url": path, "segment_index": 0}
            ]
            audio_count += 1
            print(f"    ✅ Saved: {filepath.name}")
        except Exception as e:
            print(f"    ❌ Failed: {e}")

    # ─── 2. Subtopic Intro Narrations ───────────────────────────────────────
    subtopic_intros = state.get("subtopic_intro_narrations", {})
    subtopic_dir = ensure_dir(output_dir / "subtopic_intros")

    for sub_id, intro_data in subtopic_intros.items():
        if intro_data and intro_data.get("narration_text"):
            text = intro_data["narration_text"]
            filepath = subtopic_dir / f"{sub_id}.mp3"
            print(f"  🎙 Generating subtopic intro: {sub_id}...")

            try:
                path = generate_audio(client, text, filepath, voice)
                state["subtopic_intro_narrations"][sub_id]["audio_url"] = path
                state["subtopic_intro_narrations"][sub_id]["narration_segments"] = [
                    {"text": text, "audio_url": path, "segment_index": 0}
                ]
                audio_count += 1
                print(f"    ✅ Saved: {filepath.name}")
            except Exception as e:
                print(f"    ❌ Failed: {e}")

    # ─── 3. Per-Slide Narrations (Segmented) ────────────────────────────────
    slides = state.get("slides", {})
    slides_dir = ensure_dir(output_dir / "slides")

    for sub_id, slide_list in slides.items():
        for i, slide in enumerate(slide_list):
            narration_text = slide.get("narration_text")
            if not narration_text:
                continue

            slide_id = slide.get("slide_id", f"{sub_id}_s{i + 1}")
            narration_format = slide.get("narration_format", "paragraph")

            # Create per-slide directory
            slide_dir = ensure_dir(slides_dir / slide_id)

            # Segment the narration
            segments = segment_narration(narration_text, narration_format)
            is_segmented = len(segments) > 1

            print(
                f"  🎙 Slide {slide_id} ({narration_format}) → "
                f"{len(segments)} segment{'s' if is_segmented else ''}"
            )

            narration_segments = []

            for seg_idx, segment_text in enumerate(segments):
                if is_segmented:
                    filename = f"segment_{seg_idx + 1}.mp3"
                else:
                    filename = "full.mp3"

                filepath = slide_dir / filename

                try:
                    path = generate_audio(client, segment_text, filepath, voice)
                    narration_segments.append(
                        {
                            "text": segment_text,
                            "audio_url": path,
                            "segment_index": seg_idx,
                        }
                    )
                    audio_count += 1
                    print(f"    ✅ Segment {seg_idx + 1}: {filepath.name}")
                except Exception as e:
                    print(f"    ❌ Segment {seg_idx + 1} failed: {e}")
                    narration_segments.append(
                        {
                            "text": segment_text,
                            "audio_url": None,
                            "segment_index": seg_idx,
                        }
                    )

            # Store results on the slide dict
            slide["narration_segments"] = narration_segments
            # For backward compat, audio_url points to first segment or the full file
            if narration_segments and narration_segments[0].get("audio_url"):
                slide["audio_url"] = narration_segments[0]["audio_url"]

    print(
        f"\n🔊 [Audio Generation Node] Complete — {audio_count} audio files generated."
    )

    return state


# ═══════════════════════════════════════════════════════════════════════════
# STANDALONE TEST (uses real workflow output)
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    # Load the real workflow output
    output_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "computer_generations_workflow_output.json",
    )

    with open(output_path, "r", encoding="utf-8") as f:
        full_state = json.load(f)

    # Pick one slide per narration format for testing
    test_slides = {}
    formats_needed = {
        "paragraph",
        "points",
        "sequential_points",
        "comparative_points",
        "data_interpretation",
    }
    formats_found = set()

    for sub_id, slide_list in full_state.get("slides", {}).items():
        for slide in slide_list:
            fmt = slide.get("narration_format", "paragraph")
            if fmt in formats_needed and fmt not in formats_found:
                if sub_id not in test_slides:
                    test_slides[sub_id] = []
                test_slides[sub_id].append(slide)
                formats_found.add(fmt)
                print(f"📌 Selected slide '{slide.get('slide_id')}' for format: {fmt}")

            if formats_found == formats_needed:
                break
        if formats_found == formats_needed:
            break

    # Build minimal test state
    test_state = {
        "topic": full_state.get("topic"),
        "teacher_voice_id": 4,  # nova
        "lesson_intro_narration": full_state.get("lesson_intro_narration"),
        "subtopic_intro_narrations": {
            # Just test one subtopic intro
            list(full_state.get("subtopic_intro_narrations", {}).keys())[0]: list(
                full_state.get("subtopic_intro_narrations", {}).values()
            )[0]
        },
        "slides": test_slides,
    }

    print(f"\n🧪 Testing with {len(formats_found)} narration formats: {formats_found}")
    print(f"   Total slides: {sum(len(v) for v in test_slides.values())}")
    print()

    # --- Show segmentation preview (without API calls) ---
    print("=" * 60)
    print("📋 SEGMENTATION PREVIEW")
    print("=" * 60)
    for sub_id, slide_list in test_slides.items():
        for slide in slide_list:
            fmt = slide.get("narration_format", "paragraph")
            text = slide.get("narration_text", "")
            segments = segment_narration(text, fmt)
            print(f"\n🎯 Slide: {slide.get('slide_id')} | Format: {fmt}")
            print(f"   Segments: {len(segments)}")
            for j, seg in enumerate(segments):
                preview = seg[:80] + "..." if len(seg) > 80 else seg
                print(f"   [{j + 1}] {preview}")

    # --- Actually generate audio ---
    print("\n" + "=" * 60)
    print("🔊 GENERATING AUDIO")
    print("=" * 60)

    result = audio_generation_node(test_state)

    # --- Summary ---
    print("\n" + "=" * 60)
    print("📦 RESULTS SUMMARY")
    print("=" * 60)

    lesson = result.get("lesson_intro_narration", {})
    print(f"\nLesson intro: {lesson.get('audio_url', 'N/A')}")

    for sid, intro in result.get("subtopic_intro_narrations", {}).items():
        print(f"Subtopic {sid}: {intro.get('audio_url', 'N/A')}")

    for sid, slides in result.get("slides", {}).items():
        for s in slides:
            segs = s.get("narration_segments", [])
            print(f"\nSlide {s.get('slide_id')} ({s.get('narration_format')}):")
            for seg in segs:
                preview = (
                    seg["text"][:60] + "..." if len(seg["text"]) > 60 else seg["text"]
                )
                print(f"  [{seg['segment_index'] + 1}] {seg.get('audio_url', 'N/A')}")
                print(f'      "{preview}"')
