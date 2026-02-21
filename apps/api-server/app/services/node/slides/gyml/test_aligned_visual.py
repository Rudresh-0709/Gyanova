"""
Visual + Audio test: LLM-generated slides with audio-synced animations.

Full pipeline:
  1. Generate narration (LLM) with expected point count
  2. Count segments (segment_narration)
  3. Generate aligned GyML (point_count constraint)
  4. Generate TTS audio per segment (OpenAI TTS)
  5. Compose + Serialize + Render HTML
  6. Inject AudioAnimationController (audio-synced reveals)
  7. Open in browser with Play/Stop/Reset controls

Run with the project venv:
    .venv/Scripts/python.exe -X utf8 apps/api-server/app/services/node/slides/gyml/test_aligned_visual.py
"""

import os
import sys
import json
import re
import webbrowser
import importlib.util
from pathlib import Path

script_dir = os.path.dirname(os.path.abspath(__file__))
gyml_parent = os.path.dirname(script_dir)
sys.path.insert(0, gyml_parent)

# script_dir = gyml/, go up: gyml -> slides -> node -> services (3 levels)
services_dir = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
sys.path.insert(0, services_dir)
app_dir = os.path.dirname(services_dir)
sys.path.insert(0, app_dir)

from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from llm.model_loader import load_openai

# Import generator directly to avoid __init__.py chain
gen_path = os.path.join(script_dir, "generator.py")
spec = importlib.util.spec_from_file_location("gyml_gen", gen_path)
gen_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_mod)
GyMLContentGenerator = gen_mod.GyMLContentGenerator

from gyml.composer import SlideComposer
from gyml.serializer import GyMLSerializer
from gyml.renderer import GyMLRenderer
from gyml.theme import get_theme

# Audio node for segment counting
audio_node_path = os.path.join(services_dir, "node", "audio_generation_node.py")
spec2 = importlib.util.spec_from_file_location("audio_node", audio_node_path)
audio_mod = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(audio_mod)
segment_narration = audio_mod.segment_narration

# ── Audio output directory ─────────────────────────────────────────────
audio_output_dir = os.path.join(script_dir, "test_audio_output")
os.makedirs(audio_output_dir, exist_ok=True)

TTS_MODEL = "tts-1"
TTS_VOICE = "nova"


# ── TTS generation ───────────────────────────────────────────────────
def generate_tts(client, text, filepath):
    """Generate an mp3 from text via OpenAI TTS."""
    response = client.audio.speech.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=text,
    )
    response.write_to_file(str(filepath))
    return str(filepath)


# ── Narration generator ──────────────────────────────────────────────
def generate_narration(title, goal, subtopic, expected_points=0):
    """
    Generate teacher narration.

    Args:
        expected_points: If > 0, tells the LLM to produce exactly this many
                         distinct narration segments, each starting with a
                         transition marker (First/Second/Next/Finally etc.).
                         Word count scales: ~50-70 words per point.
    """
    llm = load_openai()

    # Scale word count: ~60 words per point, min 120, max 400
    if expected_points > 1:
        word_min = max(120, expected_points * 50)
        word_max = max(180, expected_points * 70)
        point_instruction = f"""
    6. You MUST cover EXACTLY {expected_points} distinct points, one per item.
       Start each point with a transition word:
       "First,", "Second,", "Third,", "Next,", "Finally,", etc.
       Each point should be its own mini-paragraph of 40-70 words.
       Do NOT group or combine multiple items into a single point.
       Do NOT skip any item — cover all {expected_points}."""
    else:
        word_min = 120
        word_max = 180
        point_instruction = ""

    prompt = f"""
    You are an expert teacher. Write the spoken narration for a slide.

    CONTEXT:
    - Subtopic: {subtopic}
    - Slide Title: {title}
    - Slide Goal: {goal}

    RULES:
    1. Write exactly what the teacher would say.
    2. Be engaging, clear, and pedagogically sound.
    3. {word_min}-{word_max} words.
    4. NO markdown, NO "In this slide", NO "Moving on".
    5. Your narration EXPLAINS what the student sees on screen.
       The slide will show short labels, card headings, and brief summaries.
       Your job is to ELABORATE with deeper context, examples, real-world
       connections, and analogies that are NOT written on screen.
       Do NOT just read out what the slide says.{point_instruction}
    """
    resp = llm.invoke([{"role": "user", "content": prompt}])
    return resp.content.strip()


# ── Slide generation pipeline ────────────────────────────────────────
def generate_slide(title, goal, subtopic, slide_id, tts_client, expected_points=0):
    """Full pipeline: narration -> segment -> GyML -> TTS -> compose."""
    print(f"\n  [{slide_id}] {title}")

    # 1. Narrate (with expected point count hint)
    print(f"    Generating narration (expected_points={expected_points})...")
    narration = generate_narration(title, goal, subtopic, expected_points)
    words = len(narration.split())

    # 2. Count segments
    segments = segment_narration(narration, "points")
    n = len(segments)
    print(f"    Narration: {words} words, {n} segment(s)")
    for i, s in enumerate(segments):
        print(f"      [{i}] {s[:70]}...")

    # If we expected a specific count and got it wrong, log a warning
    if expected_points > 0 and n != expected_points:
        print(f"    WARNING: Expected {expected_points} segments, got {n}")

    # 3. Generate GyML with point_count
    print(f"    Generating GyML (point_count={n})...")
    generator = GyMLContentGenerator()
    gyml = generator.generate(
        narration=narration,
        title=title,
        purpose="explain",
        subtopic=subtopic,
        point_count=n,
    )

    # STRICT SYNC: Force items to match segment count exactly
    # This prevents the "drift" where 4 audio segments map to 6 cards, causing early playback.
    for block in gyml.get("contentBlocks", []):
        if block.get("type") == "smart_layout":
            items = block.get("items", [])
            original_count = len(items)

            if original_count > n:
                print(f"    ⚠️ Trimming {original_count} items to match {n} segments")
                block["items"] = items[:n]
            elif original_count < n:
                print(
                    f"    ⚠️ Warning: {original_count} items for {n} segments (some audio will share cards)"
                )

            # Verify final count
            final_items = len(block["items"])
            variant = block.get("variant", "?")
            print(
                f"    -> smart_layout ({variant}): {final_items} items (synced to {n} segments)"
            )

    # 4. Generate TTS audio per segment
    slide_audio_dir = os.path.join(audio_output_dir, slide_id)
    os.makedirs(slide_audio_dir, exist_ok=True)
    audio_files = []

    print(f"    Generating audio ({n} segment(s))...")
    for i, seg_text in enumerate(segments):
        if n > 1:
            filename = f"segment_{i + 1}.mp3"
        else:
            filename = "full.mp3"
        filepath = os.path.join(slide_audio_dir, filename)
        try:
            generate_tts(tts_client, seg_text, filepath)
            audio_files.append(filepath)
            print(f"      [{i}] -> {filename}")
        except Exception as e:
            print(f"      [{i}] FAILED: {e}")

    # 5. Compose + Serialize
    composer = SlideComposer()
    composed = composer.compose(gyml)
    serializer = GyMLSerializer()
    sections = serializer.serialize_many(composed)
    print(
        f"    -> {len(sections)} section(s) composed, {len(audio_files)} audio file(s)"
    )

    return {
        "id": slide_id,
        "title": title,
        "narration": narration,
        "segments": segments,
        "gyml": gyml,
        "sections": sections,
        "audio_files": audio_files,
    }


# ── Build the HTML with audio-synced controls ─────────────────────────
def build_html(slides):
    all_sections = []
    for s in slides:
        all_sections.extend(s["sections"])

    renderer = GyMLRenderer(theme=get_theme("midnight"), animated=True)
    base_html = renderer.render_complete(all_sections)

    # Audio file lists ordered to match rendered sections
    audio_lists = []
    for s in slides:
        files = [f"file:///{p.replace(os.sep, '/')}" for p in s["audio_files"]]
        audio_lists.append(files)

    controller = f"""
<script>
const AUDIO_LISTS = {json.dumps(audio_lists)};

class AudioAnimationController {{
    constructor(sectionId, audioFiles) {{
        this.sectionId = sectionId;
        this.animator = window.slideAnimators[sectionId];
        this.audioFiles = audioFiles;
        this.currentAudioIdx = 0;
        this.audio = new Audio();
        this.playing = false;

        const totalAnims = this.animator.totalSegments;
        const totalAudio = this.audioFiles.length;

        this.revealMap = [];
        if (totalAudio === 1) {{
            this.revealMap = [Array.from({{length: totalAnims}}, (_, i) => i)];
        }} else if (totalAudio === totalAnims) {{
            for (let i = 0; i < totalAudio; i++) this.revealMap.push([i]);
        }} else if (totalAnims > 0 && totalAudio > 0) {{
            for (let a = 0; a < totalAudio; a++) {{
                const start = Math.round(a * totalAnims / totalAudio);
                const end = Math.round((a + 1) * totalAnims / totalAudio);
                this.revealMap.push(Array.from({{length: end - start}}, (_, i) => start + i));
            }}
        }}

        console.log(`  ${{sectionId}}: ${{totalAudio}} audio -> ${{totalAnims}} anims, map:`, this.revealMap);
        this.audio.addEventListener('ended', () => this._onSegmentEnd());
    }}

    play() {{
        this.currentAudioIdx = 0;
        this.animator.reset();
        this.playing = true;
        const el = document.getElementById(this.sectionId);
        if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        setTimeout(() => this._playAudio(0), 400);
    }}

    _playAudio(audioIdx) {{
        if (audioIdx >= this.audioFiles.length) {{
            this.playing = false;
            console.log('Done: ' + this.sectionId);
            return;
        }}
        const animSegments = this.revealMap[audioIdx] || [];
        animSegments.forEach(segIdx => this.animator.revealSegment(segIdx));

        console.log('Playing ' + this.sectionId + ': audio ' + (audioIdx + 1) +
                     '/' + this.audioFiles.length + ' -> anims ' + JSON.stringify(animSegments));

        this.audio.src = this.audioFiles[audioIdx];
        this.audio.play().catch(e => {{
            console.error('Audio play failed (click page first):', e);
            this.playing = false;
        }});
        this.currentAudioIdx = audioIdx;
    }}

    _onSegmentEnd() {{
        this._playAudio(this.currentAudioIdx + 1);
    }}

    stop() {{
        this.audio.pause();
        this.audio.currentTime = 0;
        this.playing = false;
    }}

    next() {{
        this.audio.pause();
        this._playAudio(this.currentAudioIdx + 1);
    }}

    reset() {{
        this.stop();
        this.animator.reset();
    }}
}}

window.audioControllers = {{}};
const sectionIds = Object.keys(window.slideAnimators);
sectionIds.forEach((sid, idx) => {{
    const audioFiles = AUDIO_LISTS[idx] || [];
    if (audioFiles.length > 0) {{
        window.audioControllers[sid] = new AudioAnimationController(sid, audioFiles);
    }}
}});
console.log('Audio Animation Controllers ready:', Object.keys(window.audioControllers));
</script>

<style>
    .control-panel {{
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 6px;
        max-height: 85vh;
        overflow-y: auto;
        padding: 12px;
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid #334155;
        border-radius: 12px;
        backdrop-filter: blur(12px);
        min-width: 240px;
        font-family: 'Inter', sans-serif;
    }}
    .control-panel .slide-group {{
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding-bottom: 8px;
        border-bottom: 1px solid #1e293b;
    }}
    .control-panel .slide-group:last-child {{ border-bottom: none; }}
    .control-panel .slide-title {{
        font-size: 11px;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.03em;
        padding: 2px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 220px;
    }}
    .control-panel .btn-row {{ display: flex; gap: 4px; }}
    .control-panel button {{
        padding: 8px 12px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        font-size: 12px;
        font-family: 'Inter', sans-serif;
        transition: transform 0.1s, opacity 0.15s;
        flex: 1;
    }}
    .control-panel button:hover {{ opacity: 0.85; }}
    .control-panel button:active {{ transform: scale(0.96); }}
    .btn-play {{ background: linear-gradient(135deg, #38bdf8, #0ea5e9); color: #0f172a; }}
    .btn-next {{ background: #6366f1; color: white; }}
    .btn-stop {{ background: #f59e0b; color: #0f172a; }}
    .btn-reset {{ background: #ef4444; color: white; }}
    .panel-header {{
        font-size: 13px; color: #e2e8f0; font-weight: 700;
        padding-bottom: 6px; border-bottom: 1px solid #334155; margin-bottom: 4px;
    }}
    .seg-info {{ font-size: 10px; color: #64748b; padding-left: 2px; }}
</style>
<div class="control-panel" id="ctrl-panel">
    <div class="panel-header">Audio + Animation</div>
</div>

<script>
(function() {{
    const panel = document.getElementById('ctrl-panel');
    const sectionIds = Object.keys(window.audioControllers);
    sectionIds.forEach((sid, idx) => {{
        const ctrl = window.audioControllers[sid];
        const section = document.getElementById(sid);
        const h1 = section ? section.querySelector('h1') : null;
        const title = h1 ? h1.textContent.substring(0, 30) : ('Slide ' + (idx + 1));
        const nAudio = ctrl.audioFiles.length;
        const nAnims = ctrl.animator.totalSegments;

        const group = document.createElement('div');
        group.className = 'slide-group';
        group.innerHTML = `
            <div class="slide-title">${{title}}</div>
            <div class="seg-info">${{nAudio}} audio, ${{nAnims}} animations</div>
            <div class="btn-row">
                <button class="btn-play" onclick="window.audioControllers['${{sid}}'].play()">Play</button>
                <button class="btn-next" onclick="window.audioControllers['${{sid}}'].next()">Next</button>
            </div>
            <div class="btn-row">
                <button class="btn-stop" onclick="window.audioControllers['${{sid}}'].stop()">Stop</button>
                <button class="btn-reset" onclick="window.audioControllers['${{sid}}'].reset()">Reset</button>
            </div>
        `;
        panel.appendChild(group);
    }});
    const resetAll = document.createElement('div');
    resetAll.className = 'slide-group';
    resetAll.style.paddingTop = '4px';
    resetAll.innerHTML = '<div class="btn-row"><button class="btn-reset" onclick="Object.values(window.audioControllers).forEach(c => c.reset())" style="flex:1">Reset All</button></div>';
    panel.appendChild(resetAll);
}})();
</script>
"""
    return base_html.replace("</body>", controller + "\n</body>")


# ── Main ──────────────────────────────────────────────────────────────
def main():
    subtopic = "Introduction to Computer Generations"
    # (title, goal, expected_points)
    # expected_points tells the narration LLM how many distinct items to cover
    slide_defs = [
        (
            "The Five Generations of Computers",
            "Students understand each of the five generations, their defining technology, and key innovations.",
            5,  # one per generation
        ),
        (
            "Vacuum Tubes: The First Generation",
            "Students learn how vacuum tubes work, key machines like ENIAC, and why they were eventually replaced.",
            3,  # how they work, key machines, why replaced
        ),
        (
            "Advantages and Limitations of Early Computers",
            "Students compare the strengths and weaknesses of first-generation computing.",
            2,  # advantages vs limitations
        ),
    ]

    print("=" * 60)
    print("  ALIGNED VISUAL + AUDIO TEST")
    print("=" * 60)

    tts_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    slides = []
    for i, (title, goal, expected_pts) in enumerate(slide_defs, 1):
        sid = f"aligned_s{i}"
        slide = generate_slide(title, goal, subtopic, sid, tts_client, expected_pts)
        slides.append(slide)

    # Build and save
    html = build_html(slides)
    out = os.path.join(script_dir, "alignment_visual_test.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    # Stats
    segs = re.findall(r'data-segment="\d+"', html)
    seps = html.count('<div class="block-separator"></div>')
    total_audio = sum(len(s["audio_files"]) for s in slides)
    print(f"\n  Total animated elements: {len(segs)}")
    print(f"  Block separators: {seps}")
    print(f"  Total audio files: {total_audio}")
    print(f"\n  Saved: {out}")

    webbrowser.open(f"file:///{out.replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
