"""
Test: Builds GyML data structures directly (bypassing the composer)
and renders them with animations to verify data-segment attributes.

In the browser console:
    const a = Object.values(window.slideAnimators)[0];
    a.revealNext();   // reveal next segment
    a.revealAll();    // show everything
    a.reset();        // hide all
"""

import os
import sys
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


def build_test_sections():
    """Build a set of GyML sections covering all animatable content types."""

    # 1. Timeline slide — line stays visible, cards animate
    timeline_section = GyMLSection(
        id="test_timeline",
        image_layout="none",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Evolution of Computing"),
                GyMLSmartLayout(
                    variant="timeline",
                    items=[
                        GyMLSmartLayoutItem(
                            year="1940s",
                            description="First electronic computers using vacuum tubes",
                        ),
                        GyMLSmartLayoutItem(
                            year="1950s",
                            description="Transistors replace vacuum tubes, making computers smaller",
                        ),
                        GyMLSmartLayoutItem(
                            year="1960s",
                            description="Integrated circuits combine multiple transistors",
                        ),
                        GyMLSmartLayoutItem(
                            year="1970s",
                            description="Microprocessors bring the personal computer revolution",
                        ),
                    ],
                ),
            ]
        ),
    )

    # 2. Card grid slide — cards animate one by one
    card_section = GyMLSection(
        id="test_cards",
        image_layout="none",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Key Advantages"),
                GyMLSmartLayout(
                    variant="cardGrid",
                    items=[
                        GyMLSmartLayoutItem(
                            heading="Speed",
                            description="Process millions of operations per second",
                            icon=GyMLImage(src="icon", alt="ri-speed-line"),
                        ),
                        GyMLSmartLayoutItem(
                            heading="Accuracy",
                            description="Precise calculations without human error",
                            icon=GyMLImage(src="icon", alt="ri-checkbox-circle-line"),
                        ),
                        GyMLSmartLayoutItem(
                            heading="Storage",
                            description="Store vast amounts of data efficiently",
                            icon=GyMLImage(src="icon", alt="ri-database-2-line"),
                        ),
                    ],
                ),
            ]
        ),
    )

    # 3. Comparison slide — cards slide from left/right
    comparison_section = GyMLSection(
        id="test_comparison",
        image_layout="none",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Analog vs Digital"),
                GyMLSmartLayout(
                    variant="comparison",
                    items=[
                        GyMLSmartLayoutItem(
                            heading="Analog Computers",
                            description="Continuous signals\nMechanical parts\nLimited precision",
                        ),
                        GyMLSmartLayoutItem(
                            heading="Digital Computers",
                            description="Discrete signals\nElectronic circuits\nHigh precision",
                        ),
                    ],
                ),
            ]
        ),
    )

    # 4. Columns slide — columns animate from sides
    columns_section = GyMLSection(
        id="test_columns",
        image_layout="none",
        body=GyMLBody(
            children=[
                GyMLHeading(level=2, text="Hardware vs Software"),
                GyMLColumns(
                    colwidths=[50, 50],
                    columns=[
                        GyMLColumnDiv(
                            children=[
                                GyMLParagraph(
                                    text="Hardware refers to the physical components of a computer system, including the CPU, memory, and storage devices."
                                ),
                            ]
                        ),
                        GyMLColumnDiv(
                            children=[
                                GyMLParagraph(
                                    text="Software refers to the programs and operating systems that run on the hardware, providing functionality to users."
                                ),
                            ]
                        ),
                    ],
                ),
            ]
        ),
    )

    # 5. Paragraph slide — paragraphs fade in
    paragraph_section = GyMLSection(
        id="test_paragraphs",
        image_layout="none",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Introduction"),
                GyMLParagraph(
                    text="Computers have transformed every aspect of modern life, from communication to entertainment to scientific research.",
                    variant="intro",
                ),
                GyMLParagraph(
                    text="The evolution of computers spans several generations, each marked by a significant technological advancement."
                ),
                GyMLParagraph(
                    text="Understanding these generations helps us appreciate how far technology has come and where it might be heading.",
                    variant="outro",
                ),
            ]
        ),
    )

    # 6. Accent image slide — image stays visible, body content animates
    accent_section = GyMLSection(
        id="test_accent",
        image_layout="right",
        accent_image=GyMLImage(src="placeholder", alt="Computer hardware illustration"),
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Vacuum Tube Era"),
                GyMLParagraph(
                    text="The first generation of computers used vacuum tubes for circuitry and magnetic drums for memory."
                ),
                GyMLParagraph(
                    text="These machines were enormous, filling entire rooms and consuming massive amounts of electricity."
                ),
            ]
        ),
    )

    return [
        timeline_section,
        card_section,
        comparison_section,
        columns_section,
        paragraph_section,
        accent_section,
    ]


def main():
    sections = build_test_sections()
    renderer = GyMLRenderer(theme=get_theme("midnight"), animated=True)

    html = renderer.render_complete(sections)

    out_path = os.path.join(script_dir, "animation_test.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Verify data-segment attributes
    import re

    segments = re.findall(r'data-segment="(\d+)"', html)
    print(f"Sections rendered: {len(sections)}")
    print(f"data-segment elements: {len(segments)}")
    print(f"Segment indices: {sorted(set(int(s) for s in segments))}")
    print(f"anim-slide-up: {html.count('anim-slide-up')}")
    print(f"anim-slide-left: {html.count('anim-slide-left')}")
    print(f"anim-slide-right: {html.count('anim-slide-right')}")
    print(f"anim-fade: {html.count('anim-fade')}")

    # Check accent image is NOT animated
    accent_section_html = html[
        html.index("test_accent") : html.index("</section>", html.index("test_accent"))
    ]
    has_accent_segment = (
        "data-segment" in accent_section_html.split('<div class="body">')[0]
    )
    print(f"Accent image animated (should be False): {has_accent_segment}")

    print(f"\nSaved: {out_path}")
    print(f"\nConsole commands:")
    print(f"  const a = Object.values(window.slideAnimators)[0];")
    print(f"  a.revealNext();")
    print(f"  a.revealAll();")
    print(f"  a.reset();")

    webbrowser.open(f"file:///{out_path.replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
