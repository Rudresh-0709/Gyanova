from ...llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
from ...state import TutorState
import json

llm = load_openai()


def generate_contentblocks_for_slide(slide, llm):
    """
    slide: dict containing title, points, template, imageType, imagePrompt
    llm: your language model function that returns the contentBlocks json
    """

    # Prepare user prompt with your standard format
    title = slide["title"]
    narration_points = slide["points"]

    SYSTEM_PROMPT = """
      You are an AI content-visualization generator.
      Your task is to create the contentBlocks JSON array for a slide.

      Do NOT rewrite the title or narration.
      Use the slide title and narration points ONLY as context.

      The contentBlocks you generate must:
      - Add NEW supporting information (not extracted from narration_points)
      - NOT repeat or paraphrase narration_points
      - Help visually enrich the slide
      - Fit logically with the topic
      - Follow the allowed contentBlock types and rules

      Your output must be:

      {
        "contentBlocks": [ ... ]
      }

      ──────────────────────── RULES ────────────────────────

      You may generate:
      - 1 contentBlock (default)
      - OR **2 contentBlocks** if:
        • the first block is short (low detail)
        • the slide would benefit from an extra supporting block
        • the combination is allowed

      NEVER generate more than 2 blocks.

      ──────────────────────── CONTENT TYPES ────────────────────────

      Allowed types:

      - explanation
      - timeline
      - comparison
      - steps
      - statistics
      - story
      - takeaways

      ──────────────────────── VALID COMBINATIONS ────────────────────────

      You may use:

      - narration + explanation
      - narration + timeline
      - narration + comparison
      - narration + statistics
      - narration + steps
      - narration + takeaways

      OR

      - a single block type (explanation, timeline, comparison, steps, statistics, story, takeaways)

      If generating 2 blocks, the pair must be valid.

      ──────────────────────── INVALID COMBINATIONS ────────────────────────

      Never use:

      - timeline + comparison
      - statistics + comparison
      - timeline + steps
      - statistics + steps
      - any mix of 3 or more block types

      ──────────────────────── FORMATS (MUST FOLLOW EXACTLY) ────────────────────────

      EXPLANATION
      {
        "type": "explanation",
        "paragraphs": ["..."]
      }

      TIMELINE
      {
        "type": "timeline",
        "events": [
          { "year": "", "description": "" }
        ]
      }

      COMPARISON
      {
        "type": "comparison",
        "columns": [
          { "title": "", "items": [""] },
          { "title": "", "items": [""] }
        ]
      }

      STEPS
      {
        "type": "steps",
        "steps": [
          { "step": 1, "title": "", "description": "" }
        ]
      }

      STATISTICS
      {
        "type": "statistics",
        "stats": [
          { "label": "", "value": "" }
        ]
      }

      STORY
      {
        "type": "story",
        "text": ""
      }

      TAKEAWAYS
      {
        "type": "takeaways",
        "points": ["", ""]
      }

      ──────────────────────── VISUAL DESIGN INSTRUCTIONS ────────────────────────

      You must also analyze the slide's topic and content to determine the best visual layout.
      Add a "design" object to your response with the following keys:

      1. "layout_mode": Choose the best structural fit.Each slide should have random layout.
         - "layout-split-balanced": Standard 50/50 text/image split. (Good for general info).
         - "layout-bento": Boxy, grid-like arrangement. (Good for distinct stats or multiple items).
         - "layout-magazine": Editorial style, image top, text columns bottom. (Good for stories).
         - "layout-image-card-right": Image left, card blocks on right.
         - "layout-image-card-left": Image right, card blocks on left.
         - "layout-explanation-bottom-image-left": Image on left, points on the right, explanation on the bottom of the image, good when points are more or more than one contentBlock.
         - "layout-explanation-bottom-image-right": Image on right, points on the left, explanation on the bottom of the image, good when points are more or more than one contentBlock.

      2. "decoration_style": Choose the aesthetic vibe. Every slide should have the same decoration style.
         - "decor-tech": Circuit lines, geometric shapes, monospaced accents. (For hardware/code).
         - "decor-organic": Soft blobs, curves, fluid shapes. (For nature/biology/humanities).
         - "decor-minimal": Clean lines, whitespace, solid dividers. (For business/data).
         - "decor-glass": Heavy glassmorphism, blurred cards. (For modern/futuristic).

      3. "point_display": How narration points should appear.

        - "points-list": Standard clean vertical bullet list with icons.
            (Best for general narration; works on most slides.)

        - "points-numbered": Vertical steps 1, 2, 3 with emphasis styling. 
            (Use when narration points follow a sequence or flow.)

        - "points-cards": Each point inside a rounded card or pill-shaped box. 
            (Best when points are short and need visual separation.)

        - "points-bento": Each point sits inside a mini square/rectangle module (bento grid). 
            (Use when there are 4–6 short high-level points; looks modern.)

      ──────────────────────── UPDATED OUTPUT FORMAT ────────────────────────

      Produce ONLY:

      {
        "design": {
            "layout_mode": "...",
            "decoration_style": "...",
            "point_display": "..."
        },
        "contentBlocks": [
          ...
        ]
      }

      No title.
      No narration.
      No extra commentary.
      No explanation outside blocks.
      Only the contentBlocks array.

    """
    title = slide["title"]
    narration_points = slide["points"]

    USER_PROMPT = f"""Using the rules from the system prompt, generate the contentBlocks for this slide.

      slide_title:{title}

      narration_points:{narration_points}

      Output ONLY the contentBlocks JSON object."""

    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ]
    )

    # Parse returned JSON
    response_text = response.content

    # Clean JSON if needed: remove ```json blocks if present
    if response_text.strip().startswith("```"):
        response_text = response_text.strip("`")
        response_text = response_text.replace("json", "").strip()

    # Now parse JSON
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        # If double-encoded JSON, decode twice
        data = json.loads(json.loads(response_text))

    return data


# def process_state_add_contentblocks(State, llm):
#     """
#     Returns a NEW updated State with contentBlocks added to each slide.
#     """
#     new_state = State.copy()
#     new_state["slides"] = {}

#     for subtopic_id, slides in State["slides"].items():
#         updated_slides = []

#         for slide in slides:
#             # Generate contentBlocks
#             cb = generate_contentblocks_for_slide(slide, llm)

#             # Create new slide dict with contentBlocks added
#             new_slide = slide.copy()
#             new_slide["contentBlocks"] = cb

#             updated_slides.append(new_slide)

#         new_state["slides"][subtopic_id] = updated_slides

#     return new_state


def process_state_add_contentblocks(State, llm):
    """
    Returns a NEW updated State with design + contentBlocks added to each slide.
    """
    new_state = State.copy()
    new_state["slides"] = {}

    for subtopic_id, slides in State["slides"].items():
        updated_slides = []

        for slide in slides:
            # Generate design + contentBlocks (new structure)
            result = generate_contentblocks_for_slide(slide, llm)
            # result should look like:
            # { "design": {...}, "contentBlocks": [...] }

            # Clean dict creation
            new_slide = slide.copy()

            # Add both new fields
            new_slide["design"] = result.get("design")
            new_slide["contentBlocks"] = result.get("contentBlocks")

            updated_slides.append(new_slide)

        new_state["slides"][subtopic_id] = updated_slides

    return new_state


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
    updated_state = process_state_add_contentblocks(State, llm)
    print(json.dumps(updated_state, indent=2))


