"""
Build an integrated test: GyML slide + audio segments auto-playing with animations.
Picks slides that have audio segments and renders them with an AudioAnimationController.
"""

import os
import sys
import json
import webbrowser

script_dir = os.path.dirname(os.path.abspath(__file__))
gyml_parent = os.path.dirname(script_dir)
sys.path.insert(0, gyml_parent)

from gyml.definitions import (
    GyMLSection,
    GyMLBody,
    GyMLHeading,
    GyMLParagraph,
    GyMLSmartLayout,
    GyMLSmartLayoutItem,
    GyMLImage,
)
from gyml.renderer import GyMLRenderer
from gyml.theme import get_theme

# Paths
api_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "..", ".."))
audio_base = os.path.join(api_root, "audio_output", "slides")
output_json = os.path.join(api_root, "app", "computer_generations_workflow_output.json")


def get_slide_data():
    """Load workflow data and find slides that have audio segments."""
    with open(output_json, "r", encoding="utf-8") as f:
        state = json.load(f)

    results = []
    for sub_id, slide_list in state.get("slides", {}).items():
        for slide in slide_list:
            sid = slide.get("slide_id", "")
            slide_audio_dir = os.path.join(audio_base, sid)
            if os.path.isdir(slide_audio_dir):
                # Count segment files
                mp3s = sorted(
                    [f for f in os.listdir(slide_audio_dir) if f.endswith(".mp3")]
                )
                results.append(
                    {
                        "slide_id": sid,
                        "title": slide.get("slide_title", ""),
                        "narration_format": slide.get("narration_format", "paragraph"),
                        "narration_text": slide.get("narration_text", ""),
                        "content_type": slide.get("content_type", ""),
                        "visual_content": slide.get("visual_content", {}),
                        "audio_files": mp3s,
                        "audio_dir": slide_audio_dir,
                    }
                )
    return results


def build_gyml_from_slide(slide_data):
    """Build a representative GyML section from slide data."""
    sid = slide_data["slide_id"]
    title = slide_data["title"]
    fmt = slide_data["narration_format"]
    vc = slide_data.get("visual_content", {})
    num_segments = len(slide_data["audio_files"])

    children = [GyMLHeading(level=1, text=title)]

    # Build content based on narration format and segment count
    if fmt in ("points", "sequential_points", "comparative_points"):
        # Use bullet points from visual_content if available
        points = vc.get("bullet_points", vc.get("points", []))
        if not points:
            # Generate placeholder points matching segment count
            segments = slide_data["narration_text"].split(". ")
            points = [
                {"text": s.strip() + "." if not s.endswith(".") else s.strip()}
                for s in segments
                if s.strip()
            ][:num_segments]

        items = []
        for i, pt in enumerate(points[:num_segments]):
            text = (
                pt
                if isinstance(pt, str)
                else pt.get("text", pt.get("description", f"Point {i+1}"))
            )
            items.append(GyMLSmartLayoutItem(heading=f"Point {i+1}", description=text))

        if items:
            children.append(GyMLSmartLayout(variant="bigBullets", items=items))
    else:
        # Single paragraph
        children.append(GyMLParagraph(text=slide_data["narration_text"][:200]))

    return GyMLSection(id=sid, image_layout="none", body=GyMLBody(children=children))


def build_html(slide_entries):
    """Build the full HTML with audio controller."""
    renderer = GyMLRenderer(theme=get_theme("midnight"), animated=True)

    # Build sections
    sections = [build_gyml_from_slide(s) for s in slide_entries]

    # Render base HTML
    base_html = renderer.render_complete(sections)

    # Build audio data for JS
    audio_data = {}
    for entry in slide_entries:
        sid = entry["slide_id"]
        audio_dir_abs = entry["audio_dir"]
        # Use file:// URLs for local playback
        files = [
            f"file:///{os.path.join(audio_dir_abs, f).replace(os.sep, '/')}"
            for f in entry["audio_files"]
        ]
        audio_data[sid] = files

    # Inject the audio controller JS before </body>
    controller_js = (
        f"""
<script>
const AUDIO_DATA = {json.dumps(audio_data, indent=2)};

class AudioAnimationController {{
    constructor(sectionId) {{
        this.sectionId = sectionId;
        this.animator = window.slideAnimators[sectionId];
        this.audioFiles = AUDIO_DATA[sectionId] || [];
        this.currentSegment = 0;
        this.audio = new Audio();
        this.playing = false;
        
        // When a segment finishes, play the next
        this.audio.addEventListener('ended', () => this._onSegmentEnd());
    }}

    /** Start playing from the beginning. */
    play() {{
        this.currentSegment = 0;
        this.animator.reset();
        this.playing = true;
        this._playSegment(0);
    }}

    /** Play a specific segment and reveal its animation. */
    _playSegment(index) {{
        if (index >= this.audioFiles.length) {{
            this.playing = false;
            console.log(`✅ ${{this.sectionId}}: All segments complete`);
            return;
        }}
        
        console.log(`🔊 ${{this.sectionId}}: Playing segment ${{index + 1}}/${{this.audioFiles.length}}`);
        this.animator.revealSegment(index);
        this.audio.src = this.audioFiles[index];
        this.audio.play().catch(e => console.error('Audio play failed:', e));
        this.currentSegment = index;
    }}

    _onSegmentEnd() {{
        this._playSegment(this.currentSegment + 1);
    }}

    /** Stop playback. */
    stop() {{
        this.audio.pause();
        this.audio.currentTime = 0;
        this.playing = false;
    }}

    /** Skip to next segment. */
    next() {{
        this.audio.pause();
        this._playSegment(this.currentSegment + 1);
    }}
}}

// Auto-init controllers
window.audioControllers = {{}};
Object.keys(AUDIO_DATA).forEach(sectionId => {{
    window.audioControllers[sectionId] = new AudioAnimationController(sectionId);
}});

console.log('🎬 Audio Animation Controllers ready!');
console.log('Available slides:', Object.keys(window.audioControllers));
console.log('');
console.log('Quick start:');
console.log('  const c = Object.values(window.audioControllers)[0];');
console.log('  c.play();    // play all segments with animation');
console.log('  c.next();    // skip to next segment');
console.log('  c.stop();    // stop playback');
</script>

<!-- Quick play buttons -->
<div style="position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px;">
"""
        + "".join(
            [
                f"""<button onclick="window.audioControllers['{e["slide_id"]}'].play()" 
         style="padding: 10px 20px; background: #38bdf8; color: #0f172a; border: none; 
                border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px;">
        ▶ {e["title"][:30]} ({len(e["audio_files"])} seg)
    </button>"""
                for e in slide_entries
            ]
        )
        + """
    <button onclick="Object.values(window.audioControllers).forEach(c => { c.stop(); c.animator.reset(); })" 
         style="padding: 10px 20px; background: #ef4444; color: white; border: none; 
                border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px;">
        ⏹ Reset All
    </button>
</div>
"""
    )

    # Inject before </body>
    final_html = base_html.replace("</body>", controller_js + "\n</body>")
    return final_html


def main():
    slides = get_slide_data()
    if not slides:
        print("No slides with audio segments found!")
        return

    print(f"Found {len(slides)} slides with audio:")
    for s in slides:
        print(
            f"  {s['slide_id']} | {s['narration_format']} | {len(s['audio_files'])} files | {s['title'][:50]}"
        )

    html = build_html(slides)

    out_path = os.path.join(script_dir, "audio_animation_test.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nSaved: {out_path}")
    print(f"\nClick the play buttons or use console:")
    print(f"  const c = Object.values(window.audioControllers)[0];")
    print(f"  c.play();    // audio + animation synced!")

    webbrowser.open(f"file:///{out_path.replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
