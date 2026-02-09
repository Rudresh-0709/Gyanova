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
    # {
    #     "title": "Unified Component Test",
    #     "intent": "teach",
    #     "contentBlocks": [
    #         {
    #             "type": "smart_layout",
    #             "variant": "quote",
    #             "items": [
    #                 {
    #                     "heading": "Steve Jobs",
    #                     "description": "Design is not just what it looks like and feels like. Design is how it works.",
    #                 }
    #             ],
    #         },
    #         {
    #             "type": "smart_layout",
    #             "variant": "processSteps",
    #             "items": [
    #                 {
    #                     "heading": "Analyze",
    #                     "description": "Review current system architecture and identify core bottlenecks.",
    #                 },
    #                 {
    #                     "heading": "Deploy",
    #                     "description": "Execute blue-green deployment across multiple data centers.",
    #                 },
    #             ],
    #         },
    #         {
    #             "type": "smart_layout",
    #             "variant": "definition",
    #             "items": [
    #                 {
    #                     "heading": "Microservices",
    #                     "description": "An architectural style where applications are composed of small, independent services communicating over lightweight APIs.",
    #                 },
    #             ],
    #         },
    #     ],
    # },
    # {
    #     "title": "Super Dense Content",
    #     "intent": "explain",
    #     "contentBlocks": [
    #         {
    #             "type": "paragraph",
    #             "text": "This slide is intentionally packed with content to test the threshold exceeding 0.95 density. When a slide reaches this level of saturation, the system should automatically switch to the 'super_dense' profile to prevent overflow. This involves significantly reducing font sizes and tightening vertical gaps between elements. We will include multiple paragraphs and a complex card grid to ensure the calculation hits the upper limit.",
    #         },
    #         {
    #             "type": "paragraph",
    #             "text": "Effective layout management is critical in educational presentations. If a slide is too sparse, it feels empty; if it is too dense, it becomes unreadable. Our adaptive engine balances these extremes by selecting the appropriate hierarchical profile based on estimated vertical height. This specific test ensures that even with massive amounts of text and structural blocks, the presentation remain scanable through compact typography.",
    #         },
    #         {
    #             "type": "smart_layout",
    #             "variant": "cardGrid",
    #             "items": [
    #                 {
    #                     "heading": "Scalability",
    #                     "description": "Ensuring the system can handle increased load without performance degradation.",
    #                 },
    #                 {
    #                     "heading": "Reliability",
    #                     "description": "Guaranteeing consistent operation under varying network conditions.",
    #                 },
    #                 {
    #                     "heading": "Security",
    #                     "description": "Protecting user data through end-to-end encryption and strict access controls.",
    #                 },
    #                 {
    #                     "heading": "Performance",
    #                     "description": "Optimizing latency and throughput for a seamless user experience.",
    #                 },
    #             ],
    #         },
    #     ],
    # },
    # {
    #     "title": "Super Dense Alternative",
    #     "intent": "teach",
    #     "contentBlocks": [
    #         {
    #             "type": "paragraph",
    #             "text": "Refactoring monolithic architectures into microservices is a multifaceted challenge that demands a rigorous approach to system design, network reliability, and distributed data consistency. This alternative high-density scenario is crafted to evaluate the 'super_dense' vertical layout logic by combining a voluminous introductory paragraph with a highly descriptive series of bullet points. The objective is to verify that these diverse content types—each packed with technical detail—correctly stack as vertical 'rows' without spilling into parallel columns or triggering an unwanted pagination split. Maintaining readability through precise font scaling and minimal vertical spacing is paramount when the information density reaches its upper limit. This test confirms that our adaptive engine can handle saturated educational content while preserving the expected structural hierarchy and visual rhythm required for effective knowledge transfer in complex technical domains.",
    #         },
    #         {
    #             "type": "smart_layout",
    #             "variant": "bigBullets",
    #             "items": [
    #                 "Design service-to-service communication using idempotent API endpoints and robust retry policies with jittered exponential backoff to ensure resilience against transient failures.",
    #                 "Implement the transactional outbox pattern to decouple database updates from message publishing, guaranteeing that events are reliably delivered to downstream consumers.",
    #                 "Deploy centralized observability platforms incorporating distributed tracing and log aggregation to provide deep insights into request lifecycles across the service mesh.",
    #                 "Enforce strict service boundaries through domain-driven design, ensuring that each microservice manages its own data persistence layer and scales independently of others.",
    #             ],
    #         },
    #     ],
    # },
    {
        "title": "Semantic Paragraph Test",
        "intent": "explain",
        "contentBlocks": [
            {
                "type": "intro_paragraph",
                "text": "This paragraph introduces the concept of semantic versioning, a widely adopted standard for versioning software. It communicates changes clearly using MAJOR.MINOR.PATCH logic.",
            },
            {
                "type": "context_paragraph",
                "text": "Historically, versioning was inconsistent across libraries, leading to dependency hell where developers couldn't trust that updates wouldn't break their code.",
            },
            {
                "type": "smart_layout",
                "variant": "cardGrid",
                "items": [
                    {"heading": "MAJOR", "text": "Increment for breaking changes."},
                    {"heading": "MINOR", "text": "Increment for new features."},
                    {"heading": "PATCH", "text": "Increment for bug fixes."},
                ],
            },
            {
                "type": "annotation_paragraph",
                "text": "Note: MAJOR version 0 is for initial development where everything can change.",
            },
            {
                "type": "outro_paragraph",
                "text": "In summary, following SemVer principles reduces complexity and builds trust in the ecosystem.",
            },
            {
                "type": "caption",
                "text": "Figure 1: The three pillars of semantic versioning logic.",
            },
        ],
    },
    {
          "title": "Key Components of a Microprocessor",
          "subtitle": "Introduction to Microprocessors and Their History",
          "intent": "explain",
          "contentBlocks": [
            {
              "type": "intro_paragraph",
              "text": "A microprocessor is the brain of a computer system, composed of several key components working together to process data and execute instructions."
            },
            {
              "type": "smart_layout",
              "variant": "cardGridIcon",
              "items": [
                {
                  "heading": "Arithmetic Logic Unit (ALU)",
                  "text": "Performs all mathematical calculations and logical operations such as addition, subtraction, and comparisons.",
                  "icon": "ri-function-line"
                },
                {
                  "heading": "Control Unit",
                  "text": "Acts as the microprocessor\u2019s director by interpreting program instructions and coordinating the actions of other components.",
                  "icon": "ri-steering-line"
                },
                {
                  "heading": "Registers",
                  "text": "Small, fast storage locations that temporarily hold data and instructions, serving as the microprocessor\u2019s short-term memory for quick access.",
                  "icon": "ri-database-2-line"
                }
              ]
            },
            {
              "type": "annotation_paragraph",
              "text": "Together, the ALU, Control Unit, and registers form the core of the microprocessor, enabling efficient and accurate execution of complex tasks."
            },
            {
              "type": "outro_paragraph",
              "text": "Understanding these components helps us appreciate how microprocessors power everything from simple gadgets to advanced computers."
            }
          ],
          "takeaway": "The ALU, Control Unit, and registers are fundamental parts of a microprocessor that work in harmony to execute instructions and process data efficiently.",
          "imagePrompt": "Detailed diagram illustrating the key components of a microprocessor: Arithmetic Logic Unit (ALU), Control Unit, and Registers, with labels and icons representing their functions."
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
