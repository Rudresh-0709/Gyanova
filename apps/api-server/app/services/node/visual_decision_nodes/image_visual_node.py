import os
import json
import re

from .generators.ai_image import create_ai_enhanced_visual
from .generators.ai_image_generation import generate_ai_image

# from .generators.diagram import generate_diagram
# from .utils.save_image import save_image
import copy


def sanitize_filename(name: str) -> str:
    """
    Convert slide titles to safe filenames.
    Removes special characters and replaces spaces with underscores.
    """
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip())


def generate_visuals(
    full_state: dict,
    output_dir: str = os.path.join(
        os.path.dirname(__file__), "../slides/static/images"
    ),
) -> dict:
    """
    Iterate through slides and generate visuals based on imageType.
    Returns updated state with image_path added for each slide.
    """
    os.makedirs(output_dir, exist_ok=True)

    slides_state = full_state.get("slides", {})
    if not slides_state:
        print("⚠️ No slides found in the given state.")
        return full_state  # Return unchanged if no slides

    # Work on a copy to avoid mutating original state
    updated_state = copy.deepcopy(full_state)

    for section_id, slides in slides_state.items():
        print(f"\n🧠 Processing section: {section_id}")

        section_dir = os.path.join(output_dir, section_id)
        os.makedirs(section_dir, exist_ok=True)

        for idx, slide in enumerate(slides):
            slide_title = slide.get("title", f"slide_{idx}")
            image_type = slide.get("imageType")
            print(f"   🎨 Slide {idx + 1}: {slide['title']} [{image_type}]")

            safe_filename = sanitize_filename(slide_title) + ".png"
            image_path = os.path.join(section_dir, safe_filename)

            try:
                image_bytes = None
                if image_type == "ai_enhanced_image":
                    image_bytes = create_ai_enhanced_visual(
                        image_prompt=slide.get("imagePrompt", ""),
                        narration=slide.get("points", []),
                        save_dir=os.path.dirname(image_path),
                        output_path=image_path,
                    )
                    print("AI enhanced image found")

                elif image_type == "ai_image":
                    image_bytes = generate_ai_image(
                        prompt=slide.get("imagePrompt", ""),
                        narration=slide.get("points", []),
                        output_path=image_path,
                    )
                    print("AI image found")

                else:
                    print(f"      ⚠️ Unknown imageType: {image_type}, skipping...")
                    continue
                if image_bytes:
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    print(f"      ✅ Saved image to {image_path}")

                updated_state["slides"][section_id][idx]["image_path"] = image_path
            except Exception as e:
                print(f"      ❌ Failed to generate for slide {idx}: {e}")

    return updated_state


if __name__ == "__main__":
    State = {
        "topic": "Computer generations",
        "sub_topics": [
            {
                "name": "Introduction to Computer Generations",
                "difficulty": "Beginner",
                "id": "sub_1_2b67b6",
            },
            {
                "name": "First Generation Computers (1940s-1950s): Vacuum Tubes",
                "difficulty": "Intermediate",
                "id": "sub_2_30755b",
            },
            {
                "name": "Second to Fifth Generation Computers (1950s-1980s): Transistors, Integrated Circuits, and Microprocessors",
                "difficulty": "Intermediate",
                "id": "sub_3_d87eaf",
            },
            {
                "name": "Modern Computer Generations (1980s-present): Artificial Intelligence, Internet, and Beyond",
                "difficulty": "Advanced",
                "id": "sub_4_c8e0dd",
            },
            {
                "name": "Comparison and Evolution of Computer Generations",
                "difficulty": "Intermediate",
                "id": "sub_5_dca7e2",
            },
        ],
        "slides": {
            "sub_1_2b67b6": [
                {
                    "title": "Evolution of Computers",
                    "points": [
                        "Computers have evolved through distinct generations, each marked by significant advancements.",
                        "First generation computers used vacuum tubes, while second generation computers adopted transistors.",
                        "Third generation computers integrated integrated circuits, leading to smaller, more powerful machines.",
                    ],
                    "template": "image_left",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "educational diagram illustrating the evolution of computers through generations, showcasing first-generation vacuum tube computers, second-generation transistor computers, and third-generation integrated circuit computers, detailed labeled illustration in a clean technical style",
                },
                {
                    "title": "First Generation Computers",
                    "points": [
                        "First generation computers used vacuum tubes for processing data.",
                        "ENIAC, developed in the 1940s, was one of the earliest electronic general-purpose computers.",
                        "These computers were huge in size and consumed a significant amount of electricity.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "detailed labeled diagram of the ENIAC computer, showcasing vacuum tubes, large size, and electricity consumption, schematic illustration with technical details",
                },
                {
                    "title": "Evolution from Second to Third Gen Computers",
                    "points": [
                        "Transistors replaced vacuum tubes, enhancing speed and reliability in second-gen computers.",
                        "Integrated Circuits (ICs) compacted multiple components, reducing size and cost.",
                        "Mainframes in third-gen computers enabled multi-user access, advancing computing capabilities.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "detailed comparison illustration showing the evolution from second to third-gen computers, highlighting transistors vs. vacuum tubes, ICs integration, and mainframes in a clean labeled diagram style",
                },
                {
                    "title": "Evolution of Computing Power",
                    "points": [
                        "The first generation of computers used vacuum tubes for processing data.",
                        "Second-generation computers introduced transistors, enhancing speed and reliability.",
                        "Microprocessors revolutionized computing, leading to personal computers and AI advancements.",
                    ],
                    "template": "image_left",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "educational diagram illustrating the evolution of computing power: 1. Vacuum tube computer with labeled components, 2. Transistor-based computer showing speed improvement, 3. Microprocessor technology enabling personal computers and AI, detailed labeled illustration",
                },
            ],
            "sub_2_30755b": [
                {
                    "title": "Evolution of Computing: First Gen",
                    "points": [
                        "Early computers used vacuum tubes for processing, resembling light bulbs.",
                        "First-generation computers were massive and consumed significant power.",
                        "Computer history traces back to this era, showcasing rapid technological advancements.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "detailed labeled diagram of a first-generation computer with vacuum tubes, side-by-side comparison of a light bulb and a vacuum tube, emphasizing size and power consumption, technical educational style",
                },
                {
                    "title": "Vacuum Tube Basics",
                    "points": [
                        "Vacuum tubes are early electronic devices used as switches and amplifiers.",
                        "They manipulate electric signals by controlling the flow of electrons.",
                        "Vacuum tubes played a crucial role in early electronic technology advancements.",
                        "Understanding vacuum tubes is fundamental for grasping the evolution of modern electronics.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "educational labeled diagram illustrating the internal structure of a vacuum tube, showing electron flow control, detailed components, clean technical illustration style",
                },
                {
                    "title": "ENIAC and Vacuum Tubes",
                    "points": [
                        "ENIAC was the first electronic general-purpose computer built in 1946.",
                        "Vacuum tubes were crucial components in ENIAC, used for computation and memory.",
                        "ENIAC's vacuum tubes generated a significant amount of heat, requiring frequent maintenance.",
                        "The use of vacuum tubes in ENIAC paved the way for modern computing technology.",
                        "Understanding ENIAC and vacuum tubes is key to appreciating the evolution of computers.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "labeled educational illustration comparing ENIAC's internal structure with and without vacuum tubes, highlighting heat generation, detailed cross-section view",
                },
                {
                    "title": "Limitations of Vacuum Tubes",
                    "points": [
                        "Vacuum tubes produce significant heat, leading to inefficiency and cooling requirements.",
                        "Reliability is a concern due to tube fragility and susceptibility to wear and tear.",
                        "Maintenance of vacuum tubes is labor-intensive, requiring frequent replacements and adjustments.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "detailed labeled diagram showing the internal components of a vacuum tube, highlighting heat generation points, fragile areas prone to wear and tear, and areas requiring frequent maintenance, clean technical illustration style",
                },
            ],
            "sub_3_d87eaf": [
                {
                    "title": "Evolution of Computers: 2nd Gen",
                    "points": [
                        "Transistors replaced vacuum tubes in 2nd gen computers, reducing size and improving speed.",
                        "These computers used assembly language for programming, enhancing efficiency.",
                        "Magnetic core memory was introduced, offering faster and more reliable data storage.",
                        "2nd gen computers marked significant advancements in computing power and reliability.",
                        "Understanding 2nd gen computers helps grasp the rapid evolution of technology.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "detailed labeled diagram comparing 1st gen and 2nd gen computers, highlighting transistors replacing vacuum tubes, assembly language usage, and magnetic core memory, educational technical illustration style",
                },
                {
                    "title": "Integrated Circuits",
                    "points": [
                        "Integrated Circuits (ICs) are miniature electronic circuits etched onto a single piece of silicon.",
                        "ICs combine multiple electronic components like transistors and resistors in a compact design.",
                        "The use of silicon allows ICs to be highly efficient, reliable, and cost-effective.",
                        "ICs revolutionized electronics by enabling smaller devices, faster speeds, and increased functionality.",
                        "Understanding ICs is crucial for grasping modern technology's intricate inner workings.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "detailed cross-section diagram of an integrated circuit (IC) showcasing miniature transistors, resistors, and silicon components, highlighting compact design and efficiency, technical labeled illustration",
                },
                {
                    "title": "Microprocessors Emergence",
                    "points": [
                        "Microprocessors revolutionized computing by integrating CPU functions into a single chip.",
                        "These chips enabled smaller, faster, and more efficient computers.",
                        "The emergence of microprocessors marked a shift towards personal computing and digital technology.",
                        "Microprocessors paved the way for advancements in automation, AI, and interconnected devices.",
                        "Understanding microprocessors is key to grasping modern computing and technological progress.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "labeled diagram illustrating the integration of CPU functions into a single chip, showing components like ALU, control unit, registers, in a detailed educational style",
                },
                {
                    "title": "Evolution of Personal Computers",
                    "points": [
                        "4th gen computers (1971-1980) introduced microprocessors for faster processing.",
                        "Microcomputers became more affordable and accessible to individuals and businesses.",
                        "Advancements led to smaller, more powerful computers, revolutionizing computing capabilities.",
                        "This era laid the foundation for modern personal computing and digital revolution.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_image",
                    "imagePrompt": "educational timeline depiction showcasing the evolution of personal computers from 4th gen (1971-1980) to modern PCs, highlighting microprocessor introduction, affordability, size reduction, and computing advancements, clean vector style",
                },
                {
                    "title": "Advancements in 5th Gen Computers",
                    "points": [
                        "5th gen computers integrate AI for advanced problem-solving capabilities.",
                        "They leverage parallel processing to execute multiple tasks simultaneously.",
                        "This parallel processing enhances speed and efficiency in handling complex computations.",
                        "AI algorithms in 5th gen computers enable autonomous decision-making and learning.",
                        "These advancements mark a significant leap in computing power and intelligent automation.",
                    ],
                    "template": "split_horizontal",
                    "imageType": "ai_image",
                    "imagePrompt": "visual comparison of 4th gen vs. 5th gen computers, showcasing AI integration, parallel processing, speed enhancement, autonomous decision-making, and intelligent automation, side-by-side educational comparison",
                },
                {
                    "title": "Generational Differences",
                    "points": [
                        "Each generation is shaped by unique events and cultural influences.",
                        "Generational traits impact communication styles and work preferences.",
                        "Understanding generational differences fosters empathy and effective collaboration.",
                    ],
                    "template": "split_horizontal",
                    "imageType": "ai_image",
                    "imagePrompt": "side-by-side comparison showing key events and cultural influences shaping different generations, highlighting communication styles and work preferences, clean infographic style",
                },
            ],
            "sub_4_c8e0dd": [
                {
                    "title": "Evolution of Computing",
                    "points": [
                        "Computers have evolved from room-sized machines to compact personal devices.",
                        "Microprocessors revolutionized computing by shrinking processing power into a single chip.",
                        "The accessibility of personal computers democratized technology, empowering individuals.",
                        "The evolution of computers has sparked a technological revolution, shaping modern society.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_image",
                    "imagePrompt": "visual comparison showing the evolution of computing technology from room-sized machines to compact personal devices, side-by-side view, emphasizing size reduction and technological advancement, clean and modern infographic style",
                },
                {
                    "title": "AI vs. Machine Learning",
                    "points": [
                        "AI is the broader concept of machines performing tasks that typically require human intelligence.",
                        "Machine Learning is a subset of AI where machines learn from data to improve performance.",
                        "AI encompasses various techniques beyond Machine Learning, like neural networks for complex pattern recognition.",
                    ],
                    "template": "split_horizontal",
                    "imageType": "ai_image",
                    "imagePrompt": "educational comparison illustration showing AI on one side with diverse tasks like speech recognition, image processing, and decision-making, and Machine Learning on the other side focusing on data input and performance improvement, clean vector style",
                },
                {
                    "title": "Internet Basics",
                    "points": [
                        "The internet is a global network connecting devices worldwide for communication and information sharing.",
                        "The World Wide Web is a collection of websites and web pages accessible via the internet.",
                        "Connectivity enables devices to link to the internet, facilitating data exchange and online activities.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "detailed diagram illustrating the structure of the internet with interconnected devices worldwide, labeled network nodes, data exchange paths, and global connectivity, clean and precise educational illustration",
                },
                {
                    "title": "Evolution of Computing Technologies",
                    "points": [
                        "Cloud computing enables remote data storage and processing over the internet.",
                        "Big data involves analyzing vast amounts of data to uncover patterns and insights.",
                        "IoT connects everyday objects to the internet, enhancing automation and data collection.",
                        "These technologies collectively shape the future of interconnected systems and smart devices.",
                    ],
                    "template": "split_horizontal",
                    "imageType": "ai_image",
                    "imagePrompt": "illustrative comparison of cloud computing, big data analysis, and IoT technology in a split-screen layout, showing cloud servers, data analytics process, and interconnected IoT devices, clean modern infographic style",
                },
            ],
            "sub_5_dca7e2": [
                {
                    "title": "Computer Generations",
                    "points": [
                        "Computers have evolved through distinct generations since the mid-20th century.",
                        "Each generation introduced new technologies, making computers faster, smaller, and more powerful.",
                        "Advancements in hardware and software defined the characteristics of each computer generation.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_image",
                    "imagePrompt": "educational comparison illustration showing the evolution of computer generations from 1st to 5th, highlighting key technologies and size differences, side-by-side visual comparison",
                },
                {
                    "title": "First Generation Computers",
                    "points": [
                        "Early computers used vacuum tubes for processing data in the 1940s.",
                        "ENIAC, the first electronic general-purpose computer, was a key innovation.",
                        "These computers were huge in size, consumed massive amounts of power, and generated a lot of heat.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "educational labeled diagram illustrating the internal components of a first-generation computer with vacuum tubes, detailed cross-section view, highlighting ENIAC as the first electronic general-purpose computer",
                },
                {
                    "title": "Evolution of Computing Generations",
                    "points": [
                        "Second generation introduced transistors, smaller and more reliable than vacuum tubes.",
                        "Third generation saw microprocessors enabling smaller, faster, and more powerful computers.",
                        "Fourth generation brought mainframe computers with advanced processing capabilities.",
                    ],
                    "template": "image_left",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "educational diagram comparing computing generations: second generation with transistors, third generation with microprocessors, fourth generation with mainframe computers, detailed labeled illustration",
                },
                {
                    "title": "Future of Computing",
                    "points": [
                        "Fifth Generation focuses on AI, parallel processing, and nanotechnology for advanced computing.",
                        "AI enables machines to learn, reason, and make decisions like humans.",
                        "Parallel processing enhances speed by performing multiple tasks simultaneously.",
                        "Nanotechnology involves building devices at the molecular level for powerful computing capabilities.",
                        "The future of computing lies in combining these technologies for unprecedented advancements.",
                    ],
                    "template": "image_right",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "educational diagram illustrating the Fifth Generation computing technologies: AI, parallel processing, and nanotechnology, detailed labels explaining AI learning, reasoning, and decision-making processes, parallel processing tasks performed simultaneously, nanotechnology molecular-level device construction, advanced educational infographic style",
                },
                {
                    "title": "Computer Generations Compared",
                    "points": [
                        "First generation computers were large, slow, and costly, focusing on basic calculations.",
                        "Second generation saw smaller, faster machines with improved performance and reduced costs.",
                        "Third generation computers introduced integrated circuits, enhancing speed and reducing size and cost.",
                        "Fourth generation computers brought microprocessors, leading to smaller, faster, and more affordable devices.",
                        "Each generation marked significant advancements in performance, size reduction, and cost efficiency.",
                    ],
                    "template": "split_horizontal",
                    "imageType": "ai_image",
                    "imagePrompt": "comparative visual showing the evolution of computer generations from large, slow machines to smaller, faster devices with improved performance and reduced costs, side-by-side comparison, clean infographic style",
                },
                {
                    "title": "Evolution's Influence on Society",
                    "points": [
                        "Technology advances due to evolutionary needs for efficiency and convenience.",
                        "Innovation thrives as societies adapt to changing environments and demands.",
                        "Globalization expands through interconnectedness driven by evolutionary progress.",
                        "Evolution's impact on society showcases the dynamic nature of human adaptation.",
                        "Understanding this influence helps navigate and anticipate future societal changes.",
                    ],
                    "template": "split_horizontal",
                    "imageType": "ai_image",
                    "imagePrompt": "educational comparison illustration showing the evolution of technology and society on one side and modern innovations on the other, highlighting interconnectedness and progress, clean infographic style",
                },
            ],
        },
    }

    generate_visuals(State)
