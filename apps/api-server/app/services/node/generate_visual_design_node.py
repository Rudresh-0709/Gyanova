from typing import Dict, Any
import json
from ..llm.model_loader import load_openai

# 🔹 SYSTEM PROMPT — Visual Generation Stage
SYSTEM_PROMPT = """
You are an expert visual designer and slide layout planner for an AI-powered educational platform.

🎯 PURPOSE:
Your task is to transform an existing slide narration (title + points) into a **visually engaging and pedagogically clear design plan**.
Each output should define:
1. The **layout template** — how text and visuals will be positioned.
2. The **image type** — the kind of visual best suited for the concept.
3. The **image prompt** — a detailed yet concise description of what the image should show.

---

🧩 INPUT FORMAT:
You will receive a JSON object containing:
{
  "title": "string",
  "points": ["point1", "point2", "point3", ...]
}

---

🖼️ OUTPUT FORMAT:
Return valid JSON only:
{
  "template": "image_left" | "image_right" | "image_full" | "text_only" | "split_horizontal",
  "imageType": "ai_image" | "ai_enhanced_image" | "chart_diagram",
  "imagePrompt": "string"
}

---

🎨 DESIGN RULES:

1. **Template Selection (Layout)**  
   Choose from ["image_right", "image_left", "image_full", "text_only", "split_horizontal"].  
   - Use different templates across slides when possible (for visual variety).  
   - Examples:
     - "image_left" → When visuals explain sequential or process-like ideas.
     - "image_right" → When text drives the slide and visuals are supportive.
     - "image_full" → For diagrams, timelines, or big-picture visuals.
     - "text_only" → For abstract or purely conceptual ideas.
     - "split_horizontal" → For comparisons, dual stages, or layered structures.

2. **Image Type Rules (Balanced Use)**  
   Choose from ["ai_image", "ai_enhanced_image"]  

   - `ai_image`: Use for creative, conceptual, or real-world context scenes where atmosphere or visualization matters more than labeling.  
     Examples: historical scenes, natural processes, mythological depictions, imaginative metaphors.
     Also use for structured, timeline, stepwise, or comparative visuals.  
     Examples: evolution stages, process flows, hierarchies, cycles, data comparisons.

   - `ai_enhanced_image`: Use for labeled or factual visuals needing clarity and precision.  
     Examples: scientific diagrams, anatomical structures, internal mechanisms, labeled educational illustrations.  
     ⚠ Use sparingly.

   

    "Timeline / Sequence" — for chronological or step-based visual progression.` 
   Aim for an overall balance
   Do not overuse ai_enhanced_image.

3. **Image Prompt Design Rules**
   - The imagePrompt must directly reflect the narration’s *content and sequence of ideas*.  
   - Include key visual elements and perspectives (e.g., “timeline view”, “cross-section”, “side comparison”).  
   - Use educational clarity — focus on what helps a learner understand visually.  
   - Include artistic style hints: "clean infographic", "vector educational style", "simple labeled illustration", etc.  
   - Avoid generic phrasing like “an image showing the concept.”  

---

📚 EXAMPLES:

Input:
{
  "title": "Evolution of the Human Brain",
  "points": [
    "Early humans had smaller brains suited for survival and basic tools.",
    "Over time, brain regions expanded to handle complex reasoning.",
    "Modern humans developed larger frontal lobes for creativity and decision-making."
  ]
}

Output:
{
  "template": "image_left",
  "imageType": "ai_image",
  "imagePrompt": "educational timeline infographic showing human brain evolution from early hominids to modern humans, labeled stages, clean vector style"
}

---

⚙️ ADDITIONAL GUIDELINES:
- Maintain alignment between the **complexity of narration** and the **visual type**:
  - Abstract or emotional → ai_image  
  - Analytical or labeled → ai_enhanced_image  
- Encourage visual variety and avoid repetitive prompt wording.
- Prefer *educationally supportive visuals* over decorative ones.
- Never include narration text, slide titles, or extra markup in the output.

---

Your role: Create **educationally meaningful and visually balanced slide visuals** that perfectly complement the narration content.
"""


def add_visual_design_to_state(full_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes the narration-based state and returns the same state
    after adding visual design fields (template, imageType, imagePrompt)
    to each slide using the LLM model.
    """

    llm = load_openai()

    slides_dict = full_state.get("slides", {})
    if not slides_dict or not isinstance(slides_dict, dict):
        print("⚠️ No valid slides found in the given state.")
        return full_state

    # Iterate through each subtopic and its slides
    for subtopic_id, slides_list in slides_dict.items():
        if not isinstance(slides_list, list):
            print(f"⚠️ Slides for {subtopic_id} are not a list. Skipping.")
            continue

        updated_slides = []

        for index, slide in enumerate(slides_list, start=1):
            if not isinstance(slide, dict):
                print(f"⚠️ Slide {index} under {subtopic_id} is not a dict. Skipping.")
                continue

            # Prepare input for model
            user_prompt = json.dumps(
                {"title": slide.get("title", ""), "points": slide.get("points", [])},
                ensure_ascii=False,
                indent=2,
            )

            # Call model
            response = llm.invoke(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ]
            )

            # Parse JSON safely
            response_content = getattr(response, "content", response)

            # Parse JSON safely
            try:
                visual_data = json.loads(response_content)
            except json.JSONDecodeError:
                print(
                    f"⚠️ Invalid JSON from model on {subtopic_id} slide {index}. Raw response:\n{response_content}"
                )
                visual_data = {}

            # Merge results into slide
            slide.update(
                {
                    "template": visual_data.get("template", "image_right"),
                    "imageType": visual_data.get("imageType", "ai_image"),
                    "imagePrompt": visual_data.get(
                        "imagePrompt",
                        "simple educational visual representing the concept",
                    ),
                }
            )

            updated_slides.append(slide)

        # Update the subtopic’s slides list
        full_state["slides"][subtopic_id] = updated_slides

    return full_state


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
                },
                {
                    "title": "First Generation Computers",
                    "points": [
                        "First generation computers used vacuum tubes for processing data.",
                        "ENIAC, developed in the 1940s, was one of the earliest electronic general-purpose computers.",
                        "These computers were huge in size and consumed a significant amount of electricity.",
                    ],
                },
                {
                    "title": "Evolution from Second to Third Gen Computers",
                    "points": [
                        "Transistors replaced vacuum tubes, enhancing speed and reliability in second-gen computers.",
                        "Integrated Circuits (ICs) compacted multiple components, reducing size and cost.",
                        "Mainframes in third-gen computers enabled multi-user access, advancing computing capabilities.",
                    ],
                },
                {
                    "title": "Evolution of Computing Power",
                    "points": [
                        "The first generation of computers used vacuum tubes for processing data.",
                        "Second-generation computers introduced transistors, enhancing speed and reliability.",
                        "Microprocessors revolutionized computing, leading to personal computers and AI advancements.",
                    ],
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
                },
                {
                    "title": "Vacuum Tube Basics",
                    "points": [
                        "Vacuum tubes are early electronic devices used as switches and amplifiers.",
                        "They manipulate electric signals by controlling the flow of electrons.",
                        "Vacuum tubes played a crucial role in early electronic technology advancements.",
                        "Understanding vacuum tubes is fundamental for grasping the evolution of modern electronics.",
                    ],
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
                },
                {
                    "title": "Limitations of Vacuum Tubes",
                    "points": [
                        "Vacuum tubes produce significant heat, leading to inefficiency and cooling requirements.",
                        "Reliability is a concern due to tube fragility and susceptibility to wear and tear.",
                        "Maintenance of vacuum tubes is labor-intensive, requiring frequent replacements and adjustments.",
                    ],
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
                },
                {
                    "title": "Evolution of Personal Computers",
                    "points": [
                        "4th gen computers (1971-1980) introduced microprocessors for faster processing.",
                        "Microcomputers became more affordable and accessible to individuals and businesses.",
                        "Advancements led to smaller, more powerful computers, revolutionizing computing capabilities.",
                        "This era laid the foundation for modern personal computing and digital revolution.",
                    ],
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
                },
                {
                    "title": "Generational Differences",
                    "points": [
                        "Each generation is shaped by unique events and cultural influences.",
                        "Generational traits impact communication styles and work preferences.",
                        "Understanding generational differences fosters empathy and effective collaboration.",
                    ],
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
                },
                {
                    "title": "AI vs. Machine Learning",
                    "points": [
                        "AI is the broader concept of machines performing tasks that typically require human intelligence.",
                        "Machine Learning is a subset of AI where machines learn from data to improve performance.",
                        "AI encompasses various techniques beyond Machine Learning, like neural networks for complex pattern recognition.",
                    ],
                },
                {
                    "title": "Internet Basics",
                    "points": [
                        "The internet is a global network connecting devices worldwide for communication and information sharing.",
                        "The World Wide Web is a collection of websites and web pages accessible via the internet.",
                        "Connectivity enables devices to link to the internet, facilitating data exchange and online activities.",
                    ],
                },
                {
                    "title": "Evolution of Computing Technologies",
                    "points": [
                        "Cloud computing enables remote data storage and processing over the internet.",
                        "Big data involves analyzing vast amounts of data to uncover patterns and insights.",
                        "IoT connects everyday objects to the internet, enhancing automation and data collection.",
                        "These technologies collectively shape the future of interconnected systems and smart devices.",
                    ],
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
                },
                {
                    "title": "First Generation Computers",
                    "points": [
                        "Early computers used vacuum tubes for processing data in the 1940s.",
                        "ENIAC, the first electronic general-purpose computer, was a key innovation.",
                        "These computers were huge in size, consumed massive amounts of power, and generated a lot of heat.",
                    ],
                },
                {
                    "title": "Evolution of Computing Generations",
                    "points": [
                        "Second generation introduced transistors, smaller and more reliable than vacuum tubes.",
                        "Third generation saw microprocessors enabling smaller, faster, and more powerful computers.",
                        "Fourth generation brought mainframe computers with advanced processing capabilities.",
                    ],
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
                },
            ],
        },
    }

updated_state = add_visual_design_to_state(State)
print(json.dumps(updated_state, indent=2))
