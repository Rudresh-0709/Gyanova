"""
Full integration test: Real GyML slides + real audio segments.
Builds rich slide content from the actual course narration text,
renders through the full pipeline with animations, and syncs with audio.
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
    GyMLColumns,
    GyMLColumnDiv,
)
from gyml.renderer import GyMLRenderer
from gyml.theme import get_theme

api_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "..", ".."))
audio_base = os.path.join(api_root, "audio_output", "slides")


def build_real_slides():
    """
    Build GyML sections that mirror the actual course content for slides
    that have audio segments. Content comes from the real narration text.
    """
    slides = []

    # ─── Slide 1: sub_1_582521_s1 (paragraph, 1 full audio) ─────────
    slides.append(
        {
            "id": "sub_1_582521_s1",
            "section": GyMLSection(
                id="sub_1_582521_s1",
                image_layout="right",
                accent_image=GyMLImage(
                    src="placeholder", alt="Computer evolution illustration"
                ),
                body=GyMLBody(
                    children=[
                        GyMLHeading(
                            level=1, text="Introduction to Computer Generations"
                        ),
                        GyMLParagraph(
                            text="Understanding computer generations is like taking a journey through time to see how technology has evolved.",
                            variant="intro",
                        ),
                        GyMLParagraph(
                            text="Each generation marks a significant leap in the design, speed, and capabilities of computers, shaping the way we live and work today.",
                        ),
                        GyMLParagraph(
                            text="By studying these generations, we gain insight into the innovations that paved the way for modern computing and appreciate the rapid progress that continues to transform our world.",
                            variant="outro",
                        ),
                    ]
                ),
            ),
        }
    )

    # ─── Slide 2: sub_1_582521_s2 (sequential_points, 3 audio segments) ──
    slides.append(
        {
            "id": "sub_1_582521_s2",
            "section": GyMLSection(
                id="sub_1_582521_s2",
                image_layout="none",
                body=GyMLBody(
                    children=[
                        GyMLHeading(
                            level=1, text="Overview of the Five Computer Generations"
                        ),
                        GyMLSmartLayout(
                            variant="timeline",
                            items=[
                                GyMLSmartLayoutItem(
                                    year="1940s–1950s",
                                    description="The first generation used vacuum tubes for circuitry and magnetic drums for memory, making computers large and power-hungry.",
                                ),
                                GyMLSmartLayoutItem(
                                    year="1950s–1960s",
                                    description="The second generation introduced transistors, which were smaller, faster, and more reliable than vacuum tubes, leading to more efficient machines.",
                                ),
                                GyMLSmartLayoutItem(
                                    year="1960s–Present",
                                    description="The third generation brought integrated circuits, combining many transistors on a single chip, greatly increasing processing speed and reducing size.",
                                ),
                            ],
                        ),
                    ]
                ),
            ),
        }
    )

    # ─── Slide 3: sub_1_582521_s3 (points, 3 audio segments) ─────────
    slides.append(
        {
            "id": "sub_1_582521_s3",
            "section": GyMLSection(
                id="sub_1_582521_s3",
                image_layout="none",
                body=GyMLBody(
                    children=[
                        GyMLHeading(
                            level=1, text="Key Features of Each Computer Generation"
                        ),
                        GyMLSmartLayout(
                            variant="bigBullets",
                            items=[
                                GyMLSmartLayoutItem(
                                    heading="Vacuum Tubes Era",
                                    description="The earliest computers used vacuum tubes, which made them large, slow, and power-hungry, but they introduced the basic concept of programmable machines.",
                                    icon=GyMLImage(
                                        src="icon", alt="ri-flashlight-line"
                                    ),
                                ),
                                GyMLSmartLayoutItem(
                                    heading="Transistor Revolution",
                                    description="The second generation brought transistors, which were smaller, faster, and more reliable, allowing computers to become more accessible and efficient.",
                                    icon=GyMLImage(src="icon", alt="ri-cpu-line"),
                                ),
                                GyMLSmartLayoutItem(
                                    heading="Integrated Circuits",
                                    description="The third generation introduced integrated circuits, combining many transistors on a single chip, which greatly increased processing speed and reduced size.",
                                    icon=GyMLImage(src="icon", alt="ri-chip-line"),
                                ),
                            ],
                        ),
                    ]
                ),
            ),
        }
    )

    # ─── Slide 4: sub_2_c5c5fe_s3 (data_interpretation, 1 full audio) ───
    slides.append(
        {
            "id": "sub_2_c5c5fe_s3",
            "section": GyMLSection(
                id="sub_2_c5c5fe_s3",
                image_layout="none",
                body=GyMLBody(
                    children=[
                        GyMLHeading(
                            level=1, text="Vacuum Tubes in Computer Architecture"
                        ),
                        GyMLColumns(
                            colwidths=[50, 50],
                            columns=[
                                GyMLColumnDiv(
                                    children=[
                                        GyMLParagraph(
                                            text="Vacuum tubes acted as electronic switches, controlling the flow of electrical signals to perform calculations and data processing.",
                                            variant="intro",
                                        ),
                                        GyMLParagraph(
                                            text="They were arranged systematically to form circuits that could execute basic operations like addition and data storage.",
                                        ),
                                    ]
                                ),
                                GyMLColumnDiv(
                                    children=[
                                        GyMLParagraph(
                                            text="Although bulky and prone to overheating, vacuum tubes enabled the first generation of computers to function and paved the way for modern digital systems.",
                                        ),
                                        GyMLParagraph(
                                            text="Understanding their role helps us appreciate how far computer architecture has come.",
                                            variant="outro",
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ]
                ),
            ),
        }
    )

    # ─── Slide 5: sub_2_c5c5fe_s4 (comparative_points, 5 audio segments) ─
    slides.append(
        {
            "id": "sub_2_c5c5fe_s4",
            "section": GyMLSection(
                id="sub_2_c5c5fe_s4",
                image_layout="none",
                body=GyMLBody(
                    children=[
                        GyMLHeading(
                            level=1, text="Advantages & Limitations of Vacuum Tubes"
                        ),
                        GyMLSmartLayout(
                            variant="comparison",
                            items=[
                                GyMLSmartLayoutItem(
                                    heading="Advantages",
                                    description="Could amplify electrical signals for electronic data processing\nRelatively easy to understand and manufacture at the time\nEnabled the very first programmable digital computers",
                                ),
                                GyMLSmartLayoutItem(
                                    heading="Limitations",
                                    description="Generated excessive heat, requiring massive cooling systems\nConsumed enormous amounts of electricity\nWere fragile and had very short operational lifespans",
                                ),
                            ],
                        ),
                        GyMLParagraph(
                            text="Despite their limitations, vacuum tubes were a groundbreaking technology that jumpstarted the development of digital computing.",
                            variant="outro",
                        ),
                    ]
                ),
            ),
        }
    )

    return slides


def build_html(slide_entries):
    """Render all sections and inject the audio animation controller."""
    renderer = GyMLRenderer(theme=get_theme("midnight"), animated=True)

    sections = [entry["section"] for entry in slide_entries]
    base_html = renderer.render_complete(sections)

    # Build audio file map
    audio_data = {}
    for entry in slide_entries:
        sid = entry["id"]
        slide_dir = os.path.join(audio_base, sid)
        if os.path.isdir(slide_dir):
            mp3s = sorted([f for f in os.listdir(slide_dir) if f.endswith(".mp3")])
            files = [
                f"file:///{os.path.join(slide_dir, f).replace(os.sep, '/')}"
                for f in mp3s
            ]
            audio_data[sid] = files
        else:
            audio_data[sid] = []

    controller_js = f"""
<script>
const AUDIO_DATA = {json.dumps(audio_data, indent=2)};

class AudioAnimationController {{
    constructor(sectionId) {{
        this.sectionId = sectionId;
        this.animator = window.slideAnimators[sectionId];
        this.audioFiles = AUDIO_DATA[sectionId] || [];
        this.currentAudioIdx = 0;
        this.audio = new Audio();
        this.playing = false;

        // Build mapping: which animation segments to reveal per audio segment.
        // If 1 audio file (full.mp3) → reveal all at once.
        // If audio count matches animation count → 1:1 mapping.
        // If mismatch → distribute evenly.
        const totalAnims = this.animator.totalSegments;
        const totalAudio = this.audioFiles.length;

        this.revealMap = []; // revealMap[audioIdx] = [animSegIdx, ...]

        if (totalAudio === 1) {{
            // Single audio → reveal everything on play
            this.revealMap = [Array.from({{length: totalAnims}}, (_, i) => i)];
        }} else if (totalAudio === totalAnims) {{
            // Perfect 1:1
            for (let i = 0; i < totalAudio; i++) this.revealMap.push([i]);
        }} else if (totalAnims > 0 && totalAudio > 0) {{
            // Distribute: group animation segments across audio segments
            // e.g., 3 anims / 5 audio → [0], [1], [2], [], []
            // e.g., 6 anims / 2 audio → [0,1,2], [3,4,5]
            for (let a = 0; a < totalAudio; a++) {{
                const start = Math.round(a * totalAnims / totalAudio);
                const end = Math.round((a + 1) * totalAnims / totalAudio);
                this.revealMap.push(Array.from({{length: end - start}}, (_, i) => start + i));
            }}
        }}

        console.log(`  ${{sectionId}}: ${{totalAudio}} audio → ${{totalAnims}} anims, map:`, this.revealMap);

        this.audio.addEventListener('ended', () => this._onSegmentEnd());
    }}

    play() {{
        this.currentAudioIdx = 0;
        this.animator.reset();
        this.playing = true;
        // Scroll to the section
        const el = document.getElementById(this.sectionId);
        if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        // Small delay for scroll to finish
        setTimeout(() => this._playAudio(0), 400);
    }}

    _playAudio(audioIdx) {{
        if (audioIdx >= this.audioFiles.length) {{
            this.playing = false;
            console.log('✅ ' + this.sectionId + ': Complete');
            return;
        }}

        // Reveal all animation segments mapped to this audio index
        const animSegments = this.revealMap[audioIdx] || [];
        animSegments.forEach(segIdx => this.animator.revealSegment(segIdx));

        console.log('🔊 ' + this.sectionId + ': audio ' + (audioIdx + 1) + '/' + this.audioFiles.length +
                     ' → revealing anims ' + JSON.stringify(animSegments));

        this.audio.src = this.audioFiles[audioIdx];
        this.audio.play().catch(e => {{
            console.error('Audio play failed (click page first):', e);
            // If autoplay blocked, still advance animation
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
}}

// Auto-init
window.audioControllers = {{}};
Object.keys(AUDIO_DATA).forEach(id => {{
    if (window.slideAnimators[id]) {{
        window.audioControllers[id] = new AudioAnimationController(id);
    }}
}});

console.log('🎬 Audio Animation Controllers ready');
console.log('Click a ▶ button or use: Object.values(window.audioControllers)[0].play()');
</script>

<!-- Control panel -->
<style>
    .control-panel {{
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 8px;
        max-height: 80vh;
        overflow-y: auto;
        padding: 12px;
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid #334155;
        border-radius: 12px;
        backdrop-filter: blur(12px);
    }}
    .control-panel button {{
        padding: 10px 18px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 13px;
        font-family: 'Inter', sans-serif;
        transition: transform 0.1s;
        text-align: left;
    }}
    .control-panel button:active {{ transform: scale(0.97); }}
    .btn-play {{
        background: linear-gradient(135deg, #38bdf8, #0ea5e9);
        color: #0f172a;
    }}
    .btn-reset {{
        background: #ef4444;
        color: white;
    }}
    .control-panel .label {{
        font-size: 11px;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 4px 0;
    }}
</style>
<div class="control-panel">
    <div class="label">Audio + Animation</div>
"""

    for entry in slide_entries:
        sid = entry["id"]
        section = entry["section"]
        title = section.body.children[0].text if section.body.children else sid
        n = len(audio_data.get(sid, []))
        label = f"▶ {title[:28]}" if len(title) <= 28 else f"▶ {title[:28]}…"
        seg_label = f"{n} segment{'s' if n != 1 else ''}" if n > 0 else "no audio"
        controller_js += f"""
    <button class="btn-play" onclick="window.audioControllers['{sid}']?.play()"
            title="{title}">
        {label}<br><span style="font-size:11px;font-weight:400;opacity:0.7">{seg_label}</span>
    </button>"""

    controller_js += """
    <button class="btn-reset" onclick="Object.values(window.audioControllers).forEach(c => { c.stop(); c.animator.reset(); })">
        ⏹ Reset All
    </button>
</div>
"""

    return base_html.replace("</body>", controller_js + "\n</body>")


def main():
    slide_entries = build_real_slides()

    html = build_html(slide_entries)

    out_path = os.path.join(script_dir, "audio_animation_test.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Stats
    import re

    segments = re.findall(r'data-segment="(\d+)"', html)
    print(f"Slides: {len(slide_entries)}")
    print(f"Animated elements: {len(segments)}")
    print(
        f"Animation types: slide-up={html.count('anim-slide-up')}, "
        f"slide-left={html.count('anim-slide-left')}, "
        f"slide-right={html.count('anim-slide-right')}, "
        f"fade={html.count('anim-fade')}"
    )

    for entry in slide_entries:
        sid = entry["id"]
        audio_dir = os.path.join(audio_base, sid)
        n = (
            len([f for f in os.listdir(audio_dir) if f.endswith(".mp3")])
            if os.path.isdir(audio_dir)
            else 0
        )
        print(f"  {sid}: {n} audio segment(s)")

    print(f"\nSaved: {out_path}")
    webbrowser.open(f"file:///{out_path.replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
