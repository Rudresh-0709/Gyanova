"""
GyML Image Manager
Handles decision logic for image placement and necessity.
Decoupled from Composer to allow stricter validation rules.
"""

import random
from dataclasses import dataclass
from typing import Optional, Literal
from .definitions import ComposedSlide, GyMLImage

# Placement Types
ImagePlacementValue = Literal["right", "left", "top", "behind", "blank"]


class ImageManager:
    """
    Determines if a slide NEEDS an image, and where it should go.
    Does NOT generate images (Composer does that via tools), only decides placement.
    """

    @staticmethod
    def determine_placement(
        slide_density: float,
        has_user_image: bool,
        intent: str,
        explicit_layout: Optional[ImagePlacementValue] = None,
        slide_index: int = 0,
    ) -> ImagePlacementValue:
        """
        Decide image layout based on density, intent, and explicit orientation.

        Rules:
        - If explicit_layout is provided, PRIORITIZE it (unless blank).
        - Density < 0.5: REQUIRE image (Right or Left) to fill space.
        - Density > 0.8: AVOID large images (use 'top' or 'blank').
        - Fallback: Alternate between 'left' and 'right' based on slide_index.
        """
        # 1. Respect Explicit Layout from LLM/Teacher
        if explicit_layout and explicit_layout != "blank":
            return explicit_layout

        # 2. High Density (Avoid cramping)
        # Aligned with SUPER_DENSE profile threshold (1.20)
        if slide_density > 1.20:
            # Respect user image but keep it right aligned if dense
            if has_user_image:
                return "right"
            return "blank"

        # 3. Low & Medium Density - Random for Variety
        return random.choice(["left", "right"])

    @staticmethod
    def should_inject_placeholder(slide_density: float, has_image: bool) -> bool:
        """
        Return True if we MUST inject a placeholder to save the slide layout.
        """
        # Strict Rule: If < 120% filled and no image, slide looks broken.
        return slide_density < 1.20 and not has_image

    @staticmethod
    def get_placeholder_image() -> GyMLImage:
        """Return the standard placeholder definition."""
        return GyMLImage(
            src="placeholder", alt="Decorative background placeholder", is_accent=True
        )


# [STEP 1] Extracting Topic...

# --- [DEBUG] TOPIC EXTRACTION LLM OUTPUT ---
# {
#     "topic": "Computer generations",
#     "granularity": "Focused"
# }
# --------------------------------------------

#   Extracted Topic: Computer generations
#   Granularity: Focused

# [STEP 2] Extracting Sub-topics...

# --- [DEBUG] SUB-TOPIC EXTRACTION LLM OUTPUT ---
# {
#     "topic": "Computer generations",
#     "sub_topics": [
#         {"name": "First Generation (1940-1959): Vacuum Tubes & Electromechanical Computers", "difficulty": "Beginner"},
#         {"name": "Second Generation (1959-1965): Transistors & Magnetic Cores", "difficulty": "Beginner"},
#         {"name": "Third Generation (1965-1971): Integrated Circuits & Microprocessors", "difficulty": "Intermediate"},
#         {"name": "Fourth Generation (1971-1980): Microprocessors & Personal Computers", "difficulty": "Intermediate"},
#         {"name": "Fifth Generation (1980-1990): Artificial Intelligence & Parallel Processing", "difficulty": "Advanced"},
#         {"name": "Sixth Generation (1990-present): Nanotechnology, Quantum Computing, and AI Advancements", "difficulty": "Advanced"},
#         {"name": "Comparison of Computer Generations: Performance, Power Consumption, and Applications", "difficulty": "Intermediate"}
#     ]
# }
# ------------------------------------------------

#   Found 7 sub-topics:
#     1. First Generation (1940-1959): Vacuum Tubes & Electromechanical Computers (Beginner)
#     2. Second Generation (1959-1965): Transistors & Magnetic Cores (Beginner)
#     3. Third Generation (1965-1971): Integrated Circuits & Microprocessors (Intermediate)
#     4. Fourth Generation (1971-1980): Microprocessors & Personal Computers (Intermediate)
#     5. Fifth Generation (1980-1990): Artificial Intelligence & Parallel Processing (Advanced)
#     6. Sixth Generation (1990-present): Nanotechnology, Quantum Computing, and AI Advancements (Advanced)
#     7. Comparison of Computer Generations: Performance, Power Consumption, and Applications (Intermediate)

# [STEP 3] Planning Slides for Subtopic: 'First Generation (1940-1959): Vacuum Tubes & Electromechanical Computers'

# --- [DEBUG] SLIDE PLANNING LLM OUTPUT ---
# {
#   "slides": [
#     {
#       "title": "First Generation Computers: Vacuum Tubes & Electromechanical Era",
#       "purpose": "definition",
#       "selected_template": "Title card",
#       "role": "Introduce",
#       "goal": "Introduce the historical context and significance of first generation computers using vacuum tubes and electromechanical components.",
#       "reasoning": "A title card with a clear, impactful title and a concise hook sets the stage for the lesson and engages learners by highlighting the era's importance."
#     },
#     {
#       "title": "Core Components of First Generation Computers",
#       "purpose": "definition",
#       "selected_template": "Four columns",
#       "role": "Interpret",
#       "goal": "Explain the four main hardware components: vacuum tubes, electromechanical relays, punch cards, and magnetic drums with concise descriptions.",
#       "reasoning": "Four columns visually break down the components with icons and short explanations, making technical hardware accessible to beginners."
#     },
#     {
#       "title": "How Vacuum Tubes Enabled Computing",
#       "purpose": "intuition",
#       "selected_template": "Image and text",
#       "role": "Guide",
#       "goal": "Build intuition on the function of vacuum tubes as electronic switches and amplifiers in early computers through detailed narrative and visuals.",
#       "reasoning": "Combining a large image with explanatory paragraphs helps learners visualize vacuum tubes' physical form and understand their role conceptually."
#     },
#     {
#       "title": "Electromechanical vs. Electronic Components",
#       "purpose": "comparison",
#       "selected_template": "Two columns",
#       "role": "Contrast",
#       "goal": "Compare electromechanical relays and vacuum tubes in terms of speed, reliability, and size to clarify technological evolution.",
#       "reasoning": "Two columns allow side-by-side comparison of characteristics, emphasizing differences crucial to understanding first generation computing challenges."
#     },
#     {
#       "title": "Timeline: Evolution of First Generation Computers (1940-1959)",
#       "purpose": "process",
#       "selected_template": "Timeline",
#       "role": "Connect",
#       "goal": "Outline key milestones from early electromechanical machines to vacuum tube-based computers, showing chronological development.",
#       "reasoning": "A timeline visually organizes historical events, helping learners grasp the progression and contextualize technological advances."
#     },
#     {
#       "title": "Anatomy of a Vacuum Tube Computer",
#       "purpose": "visualization",
#       "selected_template": "Labeled diagram",
#       "role": "Emphasize",
#       "goal": "Detail the internal architecture of a typical vacuum tube computer, labeling major parts such as CPU, memory, and input/output devices.",
#       "reasoning": "A labeled diagram clarifies complex hardware structure, enabling learners to spatially connect components and their functions."
#     },
#     {
#       "title": "Key Specifications of First Generation Computers",
#       "purpose": "reinforcement",
#       "selected_template": "Key-Value list",
#       "role": "Reinforce",
#       "goal": "Summarize technical specifications including speed, power consumption, size, and reliability to consolidate understanding.",
#       "reasoning": "A key-value list efficiently presents critical technical data, reinforcing core facts needed for foundational knowledge."
#     }
#   ]
# }
# ------------------------------------------

#   Planned 7 slides.

# [STEP 4] Generating Content for First 2 Slides...
#   (This will trigger debug prints for Narration and GyML generation)

# 🎬 [Batch Gen] Subtopic: First Generation (1940-1959): Vacuum Tubes & Electromechanical Computers | Slides 1-2 of 7
#   📝 Generating Slide 1: First Generation Computers: Vacuum Tubes & Electromechanical Era

# --- [DEBUG] NARRATION LLM OUTPUT ---
# First, the first generation of computers, spanning roughly from 1946 to 1959, relied heavily on vacuum tubes. These glass tubes acted like tiny switches, controlling electrical signals to perform calculations, but they were large, generated a lot of heat, and were prone to failure, making these machines bulky and less reliable.

# Second, many of these early computers, like the ENIAC and UNIVAC, also used electromechanical components such as punch cards and paper tapes for input and output. Imagine feeding information into a machine by physically punching holes in cards—this was the start of programming and data storage before screens and keyboards existed.

# Third, despite their limitations, these first-generation computers were groundbreaking. They marked the transition from mechanical calculators to electronic machines, laying the foundation for the digital age. Their development paved the way for faster, smaller, and more efficient computers in the generations that followed.

# Finally, while slow and energy-hungry by today’s standards, these machines revolutionized fields like science, engineering, and business, showing us the incredible potential of automating complex calculations with electricity rather than human effort.
# --------------------------------------

#     → Narration: 4 segment(s)

# --- [DEBUG] GyML GENERATION LLM OUTPUT ---
# {
#   "title": "First Generation Computers: Vacuum Tubes & Electromechanical Era",
#   "intent": "explain",
#   "layout": "left",
#   "contentBlocks": [
#     {
#       "type": "intro_paragraph",
#       "text": "The first generation of computers (1946-1959) relied on vacuum tubes and electromechanical components. These early machines laid the foundation for the digital age despite their size and limitations."
#     },
#     {
#       "type": "smart_layout",
#       "variant": "cardGridIcon",
#       "items": [
#         {
#           "icon": "ri-lightbulb-line",
#           "heading": "Vacuum Tubes as Switches",
#           "text": "Vacuum tubes controlled electrical signals to perform calculations but were large, generated heat, and prone to failure, making computers bulky and less reliable."
#         },
#         {
#           "icon": "ri-punch-card-line",
#           "heading": "Electromechanical Input/Output",
#           "text": "Machines like ENIAC and UNIVAC used punch cards and paper tapes to input and output data, marking the start of programming and data storage."
#         },
#         {
#           "icon": "ri-rocket-line",
#           "heading": "Groundbreaking Transition",
#           "text": "These computers shifted from mechanical calculators to electronic machines, paving the way for faster, smaller, and more efficient future generations."
#         },
#         {
#           "icon": "ri-flashlight-line",
#           "heading": "Revolutionizing Fields",
#           "text": "Though slow and energy-intensive, they transformed science, engineering, and business by automating complex calculations electrically."
#         }
#       ]
#     },
#     {
#       "type": "annotation_paragraph",
#       "text": "First-generation computers, despite their drawbacks, marked the dawn of the digital era and set the stage for modern computing innovations."
#     }
#   ],
#   "imagePrompt": "A vintage computer room glowing with warm light from large vacuum tubes, surrounded by punch cards and paper tapes, evoking the dawn of electronic computing"
# }
# ------------------------------------------

#   📝 Generating Slide 2: Core Components of First Generation Computers

# --- [DEBUG] NARRATION LLM OUTPUT ---
# First, vacuum tubes were the heart of first-generation computers, acting like tiny light bulbs that controlled electrical signals. They allowed early machines to perform calculations electronically but generated a lot of heat and were prone to failure, which made these computers bulky and unreliable.

# Second, electromechanical relays served as switches to control circuits, similar to how a light switch controls a lamp. Though slower than vacuum tubes, relays were essential in early designs for routing electrical signals and helped bridge mechanical and electronic components.

# Third, punch cards were the primary method for inputting data and instructions. Imagine them as early computer “language” written on stiff paper cards with holes representing information. Operators fed these cards into the machine to tell it what to do, which was a slow and manual process.

# Fourth, magnetic drums acted as the first form of computer memory, storing data magnetically on a rotating cylinder. Think of it as a primitive hard drive that allowed computers to quickly access information, though with limited capacity compared to modern storage devices.
# --------------------------------------

#     → Narration: 4 segment(s)

# --- [DEBUG] GyML GENERATION LLM OUTPUT ---
# {
#   "title": "Core Components of First Generation Computers",
#   "subtitle": "First Generation (1940-1959): Vacuum Tubes & Electromechanical Computers",
#   "layout": "left",
#   "intent": "list",
#   "contentBlocks": [
#     {
#       "type": "intro_paragraph",
#       "text": "The first generation of computers relied on four main components that defined their functionality and limitations. Understanding these core elements reveals how early computing technology operated."
#     },
#     {
#       "type": "smart_layout",
#       "variant": "cardGridIcon",
#       "items": [
#         {
#           "heading": "Vacuum Tubes",
#           "text": "Acted as tiny light bulbs controlling electrical signals, enabling electronic calculations. They generated excessive heat and were prone to failure, making computers bulky and unreliable.",
#           "icon": "ri-lightbulb-line"
#         },
#         {
#           "heading": "Electromechanical Relays",
#           "text": "Served as switches to control circuits, similar to light switches. Though slower than vacuum tubes, they were vital for routing signals and bridging mechanical and electronic parts.",
#           "icon": "ri-switch-line"
#         },
#         {
#           "heading": "Punch Cards",
#           "text": "Used as the primary input method, these stiff cards had holes representing data and instructions. Operators manually fed them into machines, making the process slow and laborious.",
#           "icon": "ri-file-list-3-line"
#         },
#         {
#           "heading": "Magnetic Drums",
#           "text": "Functioned as the first magnetic memory, storing data on a rotating cylinder. They allowed faster access to information but had limited capacity compared to modern storage.",
#           "icon": "ri-drum-line"
#         }
#       ]
#     },
#     {
#       "type": "annotation_paragraph",
#       "text": "These components collectively shaped the characteristics of first-generation computers, highlighting both their pioneering innovations and inherent challenges."
#     }
#   ],
#   "imagePrompt": "An atmospheric scene of vintage electronic components glowing softly in a dimly lit room, evoking the dawn of early computing technology"
# }
# ------------------------------------------


# ==================================================
#            FINAL WORKFLOW SUMMARY
# ==================================================
# Total Slides Generated: 2

# --- SLIDE 1 ---
# TITLE: First Generation Computers: Vacuum Tubes & Electromechanical Era
# TEMPLATE: Title card
# NARRATION (First 150 chars): First, the first generation of computers, spanning roughly from 1946 to 1959, relied heavily on vacuum tubes. These glass tubes acted like tiny switch...
# INTENT: explain
# BLOCKS: 3 blocks generated.

# --- SLIDE 2 ---
# TITLE: Core Components of First Generation Computers
# TEMPLATE: Four columns
# NARRATION (First 150 chars): First, vacuum tubes were the heart of first-generation computers, acting like tiny light bulbs that controlled electrical signals. They allowed early ...
# INTENT: list
# BLOCKS: 3 blocks generated.

# [TEST COMPLETED SUCCESSFULLY]
