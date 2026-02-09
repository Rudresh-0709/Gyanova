"""
GyML Playground
Use this file to test the slide engine with your own mock data.
Run using: python -m gyml.playground
"""

import os
import sys

# Ensure import path works if running directly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from gyml.composer import SlideComposer
from gyml.serializer import GyMLSerializer
from gyml.renderer import GyMLRenderer

# ==========================================
# 1. DEFINE YOUR MOCK DATA HERE
# ==========================================

MOCK_SCENARIOS = [
    # SCENARIO A: Timeline (Narrate)
    # {
    #     "title": "Company History",
    #     "intent": "narrate",
    #     "summary": "From humble beginnings to global influence, the company’s journey reflects a decade of innovation, resilience, and customer-focused growth. What started as an experimental project eventually evolved into a technology powerhouse shaping modern digital experiences.",
    #     "points": [
    #         "2010: Founded in a small garage with only two founders, minimal funding, and a dream to build intuitive digital tools.",
    #         "2011–2014: Early product iterations attracted a small but passionate user base, fueling gradual growth and inspiring the launch of new feature prototypes.",
    #         "2015: Reached 1 million users following a major platform redesign that improved performance, usability, and accessibility.",
    #         "2016–2019: Expanded the product ecosystem to include collaboration tools, cloud storage, and a developer API, making it a versatile platform for individuals and small businesses.",
    #         "2020: Global expansion accelerated through partnerships across Europe, Asia, and South America, transforming the company into an internationally recognized brand.",
    #     ],
    #     "image": {"url": "https://placehold.co/600x400", "layout": "right"},
    # },
    # SCENARIO B: Process Steps (Demo)
    # {
    #     "title": "How to deploy",
    #     "intent": "demo",
    #     "points": [
    #         "Install dependencies",
    #         "Run build script",
    #         "Deploy to edge",
    #         "Verify health checks",
    #     ],
    # },
    # SCENARIO C: Stats (Prove)
    # {
    #     "title": "Q4 Performance",
    #     "intent": "prove",
    #     "points": [
    #         {"label": "Revenue", "value": "$2.5M"},
    #         {"label": "Growth", "value": "+120%"},
    #         {"label": "Churn", "value": "< 1%"},
    #     ],
    #     "image": {"url": "https://placehold.co/600x400", "layout": "left"},
    # },
    # SCENARIO D: Comparison (Side-by-Side)
    # {
    #     "title": "Monolith vs Microservices",
    #     "intent": "compare",
    #     "contentBlocks": [
    #         {
    #             "type": "comparison",
    #             "items": [
    #                 {
    #                     "title": "Monolith",
    #                     "points": [
    #                         "A monolith is built as a single, unified codebase. All features and components live together in one structure.",
    #                         "It is generally easy to deploy at the beginning. The simplicity of having everything in one place reduces initial setup complexity.",
    #                         "However, it becomes difficult to scale horizontally as the system grows. Changes in one part can affect the entire application, making scaling more restrictive.",
    #                         "Example: A traditional e-commerce website where the frontend, backend, and database are all part of a single application.",
    #                     ],
    #                 },
    #                 {
    #                     "title": "Microservices",
    #                     "points": [
    #                         "Microservices use a distributed architecture. Each service is independent and handles a specific function within the system.",
    #                         "This approach introduces operational complexity. Managing many services requires strong observability, coordination, and infrastructure.",
    #                         "However, microservices offer virtually unlimited scaling potential. Each service can scale independently, allowing the system to grow without major rework.",
    #                         "Example: An e-commerce platform where the frontend, backend, and database are all part of a single application.",
    #                     ],
    #                 },
    #             ],
    #         }
    #     ],
    # },
    {
        "title": "Python Hello World",
        "intent": "teach",
        "contentBlocks": [
            {
                "type": "paragraph",
                "text": "Below is a simple demonstration of how to print text to the console in Python. Printing is one of the first operations you learn because it's essential.",
            },
            {
                "type": "code",
                "language": "python",
                "code": "print('Hello World')\nprint('This is an expanded example!')",
            },
            {
                "type": "callout",
                "text": "Note: In Python 3, print is a function and requires parentheses. You can also print complex data such as lists, formatted strings, and values stored in variables.",
            },
        ]
    },
    # SCENARIO F: Boxed List (Card Grid)
    # {
    #     "title": "Key Features",
    #     "intent": "explain",
    #     "contentBlocks": [
    #         {
    #             "type": "heading",
    #             "level": 2,
    #             "text": "Why choose this architecture?",
    #         },
    #         {
    #             "type": "card_grid",
    #             "cards": [
    #                 {
    #                     "title": "Modular Design",
    #                     "text": "The system is designed around independent, self-contained components that can be developed, tested, and modified in isolation. This modular approach reduces coupling between features, makes the codebase easier to understand, and allows teams to evolve individual parts of the system without risking widespread regressions or unintended side effects.",
    #                     "icon": "layout-masonry",
    #                 },
    #                 {
    #                     "title": "Scalable",
    #                     "text": "The architecture is built to grow seamlessly as demand increases. By distributing workload across multiple nodes or services, the system can handle higher traffic, larger datasets, and more concurrent users without performance degradation or major architectural rework.",
    #                     "icon": "bar-chart",
    #                 },
    #                 {
    #                     "title": "Secure",
    #                     "text": "Security is treated as a core architectural concern rather than an afterthought. Features such as encryption at rest and in transit, authentication mechanisms, and role-based access control ensure that data and system operations remain protected against unauthorized access and common attack vectors.",
    #                     "icon": "shield-check",
    #                 },
    #                 {
    #                     "title": "Fast Deployment",
    #                     "text": "Automated build and deployment pipelines enable teams to release changes quickly and reliably. Continuous integration and continuous delivery practices reduce manual effort, catch issues early, and allow new features, fixes, and improvements to reach users in short, repeatable release cycles.",
    #                     "icon": "rocket",
    #                 },
    #             ],
    #         },
    #     ],
    # }
    # SCENARIO E: Coding Tutorial (Teach)
    # {
    #     "title": "Python Hello World",
    #     "intent": "teach",
    #     "contentBlocks": [
    #         {
    #             "type": "paragraph",
    #             "text": "Below is a simple demonstration of how to print text to the console in Python. Printing is one of the first operations you learn because it's essential for debugging, exploring code behavior, and interacting with users.",
    #         },
    #         {
    #             "type": "code",
    #             "language": "python",
    #             "code": "print('Hello World')\nprint('This is an expanded example!')\n\n\nname = 'Alice'\nage = 29\nfavorite_languages = ['Python', 'JavaScript', 'Go']\n\nprint(f'Name: {name}')\nprint(f'Age: {age}')\nprint('Favorite Languages:')\nfor lang in favorite_languages:\n    print(' -', lang)",
    #         },
    #         {
    #             "type": "callout",
    #             "text": "Note: In Python 3, print is a function and requires parentheses. You can also print complex data such as lists, formatted strings, and values stored in variables.",
    #         },
    #     ],
    # }
]

# ==========================================
# 2. RUN PIPELINE
# ==========================================


def run_playground():
    print(f"🎨 Running GyML Playground with {len(MOCK_SCENARIOS)} scenarios...")

    composer = SlideComposer()
    serializer = GyMLSerializer()
    renderer = GyMLRenderer()

    generated_sections = []

    for i, data in enumerate(MOCK_SCENARIOS):
        print(f"   Processing: {data.get('title')}")

        # 1. Compose (Data -> List of Slide Objects)
        # We use compose() because it handles splitting (returns list of slides)
        composed_slides = composer.compose(
            data
        )  # compose expects Dict, returns List[ComposedSlide]

        for slide in composed_slides:
            # 2. Serialize (Slide Object -> GyML AST)
            section = serializer.serialize(slide)

            # 3. Accumulated for rendering
            generated_sections.append(section)

    # 4. Render Layout (GyML AST -> HTML)
    full_html = renderer.render_complete(generated_sections)

    output_path = os.path.join(os.path.dirname(__file__), "output_playground.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"\n✅ Done! Open this file in your browser:\n{output_path}")


if __name__ == "__main__":
    run_playground()
