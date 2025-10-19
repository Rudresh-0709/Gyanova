from ..llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
from ..state import TutorState
import json

def decide_visual_type(slide):
    """
    Decide the visual type for a slide using LLM.
    
    Input:
        slide: dict with slide details (title, key_terms, narration, etc.)
    Output:
        slide: dict with an added 'visual_type_decision' and 'visual_justification'
    """
    llm = load_openai()
    
    SYSTEM_PROMPT = f"""
    You are an expert visual content advisor for an AI tutoring platform. 
    Your role is to analyze each lesson topic or concept and recommend the most appropriate visual type 
    from the following options: 

    1. AI-Generated Image — for creative, abstract, microscopic, or conceptual topics 
    (e.g., atoms, emotions, space, ancient civilizations). 
    Choose this when artistic visualization or imagination helps learning.
    Avoid using for sensitive or factual topics that require exact accuracy.

    2. Stock Image — for real-world, general-purpose photos such as landscapes, 
    crowds, cities, people, or objects. 
    Ideal for giving context or realism where authenticity is important.

    3. Programmatically Generated Diagram — only for clearly structured, 
    logic-based, or data-oriented visuals such as:
    - timelines
    - flowcharts
    - graphs
    - decision trees
    - labeled steps or processes
    Do NOT use this for scientific structures (like atoms, cells, or planets), 
    as those require detailed visualization beyond programmatic rendering.

    4. AI-Enhanced Search Image — for real-world or scientific examples 
    (e.g., cell diagrams, atom structures, ecosystems, lab equipment) 
    where accurate base images exist but require enhancement, highlighting, or labeling.
    This ensures factual correctness while still engaging the viewer visually.

    Instructions:
    - Think about whether the topic is **conceptual**, **real-world**, **structured**, or **scientific**.
    - Avoid suggesting "Programmatically Generated Diagram" unless it clearly fits a diagrammatic representation.
    - Provide a short but clear justification for your choice.

    Slide data: {json.dumps(slide, ensure_ascii=False)}
    
    Output format:

    {{
        "selected_visual_type": "one of the 4 types",
        "justification": "brief reasoning"
    }}
    """

    response = llm.invoke(SYSTEM_PROMPT)
    
    try:
        visual_decision = json.loads(response.content)
        slide['visual_type_decision'] = visual_decision.get('selected_visual_type', 'AI-Generated Image')
        slide['visual_justification'] = visual_decision.get('justification', '')
    except Exception as e:
        print("Visual decision parsing failed:", e)
        slide['visual_type_decision'] = 'AI-Generated Image'
        slide['visual_justification'] = 'Default choice due to parsing error.'

    return slide

if __name__=="__main__":
    TutorState={
        "topic": "Computer generations",
        "sub_topics": [
            {
            "name": "What is an atom?",
            "difficulty": "Beginner",
            "id": "sub_1_af16be"
            },
            {
            "name": "Parts of an atom",
            "difficulty": "Intermediate",
            "id": "sub_2_f30be9"
            },
            {
            "name": "Atomic number and mass number",
            "difficulty": "Intermediate",
            "id": "sub_3_7b69d0"
            },
            {
            "name": "Electron shells for first 20 elements",
            "difficulty": "Advanced",
            "id": "sub_4_78635b"
            },
            {
            "name": "Ions and neutral atoms",
            "difficulty": "Intermediate",
            "id": "sub_5_283526"
            }
        ],
        "slides": {
            "sub_1_af16be": [
            {
                "title": "Introduction to Atoms",
                "key_terms": [
                "atom",
                "matter",
                "structure"
                ],
                "id": "slide_1_075595",
                "order": 1,
                "narration": "Have you ever stopped to think about the tiniest building blocks of everything around us? Welcome to the world of atoms! An atom is the basic unit of matter, the fundamental particle that makes up everything we see. Picture it like a miniature solar system, with a nucleus at the center and electrons orbiting around it. This simple structure holds the key to understanding the complexity of the universe. Now that we understand the essence of atoms, let's explore how their structure influences the properties of matter.",
                "narration_style": "default educational style"
            },
            {
                "title": "Atom Composition",
                "key_terms": [
                "proton",
                "neutron",
                "electron"
                ],
                "id": "slide_2_7cd67b",
                "order": 2,
                "narration": "Imagine the atom as a tiny solar system, with a dense core at its center. This core, called the nucleus, contains positively charged protons and neutral neutrons. Think of protons as the sun and neutrons as planets orbiting around it. Surrounding this nucleus are negatively charged electrons, akin to the moon orbiting the Earth. Together, these three particles\u2014protons, neutrons, and electrons\u2014make up the basic composition of an atom, defining its properties and interactions.",
                "narration_style": "default educational style"
            },
            {
                "title": "Atomic Structure",
                "key_terms": [
                "nucleus",
                "orbit",
                "energy level"
                ],
                "id": "slide_3_09a1ad",
                "order": 3,
                "narration": "Imagine the atom as a tiny solar system. At its core is the nucleus, akin to the sun, holding protons and neutrons tightly together. Electrons, like planets, orbit around the nucleus in specific energy levels, similar to planets orbiting the sun at different distances. These energy levels determine the electron's potential energy and position. Understanding the atomic structure helps us grasp how elements interact and form compounds, shaping the world around us. Now that we understand the nucleus, orbits, and energy levels, let's explore how they contribute to the properties of different elements.",
                "narration_style": "default educational style"
            },
            {
                "title": "Atom Summary",
                "key_terms": [
                "atom",
                "element",
                "compound"
                ],
                "id": "slide_4_e5cdd6",
                "order": 4,
                "narration": "Let's dive into the fascinating world of atoms. Atoms are the building blocks of everything around us. Each atom consists of a nucleus at its center, surrounded by electrons. Elements are made up of one type of atom, while compounds are formed when atoms of different elements bond together. Imagine atoms as the Lego pieces that combine to create the vast array of substances in the universe.",
                "narration_style": "default educational style"
            }
            ],
            "sub_2_f30be9": [
            {
                "title": "Introduction to Atoms",
                "key_terms": [
                "atom",
                "matter",
                "structure"
                ],
                "id": "slide_1_61a532",
                "order": 1,
                "narration": "Have you ever stopped to think about the building blocks of everything around us? Let's dive into the fascinating world of atoms. An atom is the basic unit of matter, the tiny particles that make up everything we see and touch. It has a unique structure with a nucleus at the center, composed of protons and neutrons, surrounded by electrons whizzing around like planets around the sun. Understanding the structure of atoms is key to unraveling the mysteries of the universe. Now that we understand the basics, let's explore how atoms come together to form everything in our world.",
                "narration_style": "default educational style"
            },
            {
                "title": "Protons and Neutrons",
                "key_terms": [
                "nucleon",
                "proton",
                "neutron"
                ],
                "id": "slide_2_dbebc2",
                "order": 2,
                "narration": "Have you ever wondered what makes up the core of an atom? Well, at the heart of it all are protons and neutrons, known as nucleons. Protons carry a positive charge, while neutrons have no charge. Together, they form the nucleus of an atom, holding everything together like glue. Think of protons and neutrons as the pillars supporting a structure, ensuring stability and balance within the atom. Understanding these fundamental particles is key to unraveling the mysteries of the atomic world. Now that we understand the roles of protons and neutrons, let's explore their significance in atomic structure.",
                "narration_style": "default educational style"
            },
            {
                "title": "Electrons and Orbits",
                "key_terms": [
                "electron",
                "orbit",
                "energy level"
                ],
                "id": "slide_3_ad9a57",
                "order": 3,
                "narration": "Have you ever wondered how electrons move around an atom? Imagine them like tiny planets orbiting a sun. Electrons are negatively charged particles that whirl around the nucleus in specific paths called orbits. These orbits are like different floors in a building, each representing an energy level. As electrons jump between these orbits, they absorb or release energy, creating the colorful world of chemistry. Now that we understand the dance of electrons in their orbits, let's explore how these movements shape the properties of elements.",
                "narration_style": "default educational style"
            },
            {
                "title": "Atom Structure Summary",
                "key_terms": [
                "nucleus",
                "electron cloud",
                "atomic mass"
                ],
                "id": "slide_4_82e3a8",
                "order": 4,
                "narration": "Let's take a closer look at the intricate structure of an atom. At its core, we find the nucleus, housing the protons and neutrons tightly bound together. Surrounding the nucleus is the electron cloud, where electrons move in orbits. The atomic mass represents the total mass of an atom, mainly concentrated in the nucleus. Understanding these components gives us insight into the fundamental building blocks of matter. Now that we understand the key components of an atom, let's explore how they interact to form different elements and compounds.",
                "narration_style": "default educational style"
            }
            ],
            "sub_3_7b69d0": [
            {
                "title": "Introduction to Atomic Number",
                "key_terms": [
                "atomic number",
                "protons",
                "elements"
                ],
                "id": "slide_1_dfbeae",
                "order": 1,
                "narration": "Have you ever wondered what makes each element unique? Well, at the heart of this mystery lies the concept of atomic number. The atomic number of an element is the number of protons in the nucleus of its atom. It's like a unique ID for each element, determining its identity and properties. For example, hydrogen has an atomic number of 1 because it has one proton, while helium has an atomic number of 2 due to its two protons. Understanding atomic numbers is key to unraveling the secrets of the elements around us. Now that we understand the role of atomic number, let's explore how it influences the behavior of elements.",
                "narration_style": "default educational style"
            },
            {
                "title": "Understanding Mass Number",
                "key_terms": [
                "mass number",
                "nucleons",
                "isotopes"
                ],
                "id": "slide_2_65abc0",
                "order": 2,
                "narration": "Have you ever wondered how scientists determine the weight of an atom? Enter the concept of mass number. This number represents the total sum of protons and neutrons in an atom's nucleus, also known as nucleons. When atoms of the same element have different mass numbers, we call them isotopes. These isotopes have the same number of protons but differ in the number of neutrons. Understanding mass number helps us grasp the intricacies of atomic structure and the diversity within elements. Now that we understand this, let's explore how isotopes play a crucial role in various scientific fields.",
                "narration_style": "default educational style"
            },
            {
                "title": "Relationship Between Atomic and Mass Number",
                "key_terms": [
                "atomic mass",
                "protons",
                "neutrons"
                ],
                "id": "slide_3_09dff5",
                "order": 3,
                "narration": "Have you ever wondered about the connection between the atomic number and the mass number of an atom? The atomic number represents the number of protons in the nucleus, while the mass number includes both protons and neutrons. Think of the atomic number as the unique ID of an element, like a fingerprint, and the mass number as the total weight of the nucleus. Understanding this relationship helps us distinguish between different elements and their isotopes. Now that we understand how atomic and mass numbers are related, let's explore how they define the characteristics of elements.",
                "narration_style": "default educational style"
            },
            {
                "title": "Applications of Atomic and Mass Number",
                "key_terms": [
                "isotopes",
                "atomic structure",
                "chemistry"
                ],
                "id": "slide_4_703696",
                "order": 4,
                "narration": "Have you ever wondered how scientists use atomic and mass numbers in real-life applications? These numbers help us understand isotopes, which are atoms of the same element with different numbers of neutrons. By studying atomic structure and chemistry, scientists can identify isotopes and their unique properties. For example, in medicine, isotopes are used in imaging techniques to diagnose diseases. Understanding these numbers is like deciphering a secret code that unlocks a world of possibilities in various fields.",
                "narration_style": "default educational style"
            }
            ],
            "sub_4_78635b": [
            {
                "title": "Introduction to Electron Shells",
                "key_terms": [
                "electron",
                "shell",
                "atom"
                ],
                "id": "slide_1_127355",
                "order": 1,
                "narration": "Have you ever wondered how electrons are organized around an atom? Let's dive into the fascinating world of electron shells. Electrons, the tiny particles with negative charge, whiz around the nucleus in specific energy levels called shells. These shells are like concentric layers around the nucleus, each capable of holding a certain number of electrons. Understanding electron shells is crucial in comprehending the behavior and properties of atoms. Now that we understand the basics, let's explore how these shells influence chemical reactions and bonding.",
                "narration_style": "default educational style"
            },
            {
                "title": "Electron Shell Configuration",
                "key_terms": [
                "electron configuration",
                "shell model",
                "energy level"
                ],
                "id": "slide_2_301bcd",
                "order": 2,
                "narration": "Have you ever wondered how electrons arrange themselves around an atom's nucleus? This process is known as electron shell configuration. Imagine the nucleus as the center of a solar system, and the electrons as planets orbiting around it in specific energy levels or shells. These shells, following the shell model, can hold a certain number of electrons based on their energy levels. Understanding electron configuration helps us predict an element's properties and chemical behavior. Now that we understand how electrons organize themselves in an atom, let's explore the fascinating world of electron shell configurations further.",
                "narration_style": "default educational style"
            },
            {
                "title": "First 20 Elements: Electron Shells",
                "key_terms": [
                "periodic table",
                "electron shell",
                "elements"
                ],
                "id": "slide_3_44aae9",
                "order": 3,
                "narration": "Have you ever wondered how the arrangement of electrons in an atom works? Let's dive into the first 20 elements of the periodic table and explore the concept of electron shells. Imagine each electron shell as a layer surrounding the nucleus, like different floors in a building. These shells can hold a specific number of electrons, with the closest shell to the nucleus holding the least. Understanding electron shells helps us grasp how elements interact and form compounds. Now that we understand the basic idea of electron shells, let's explore how they influence the behavior of different elements.",
                "narration_style": "default educational style"
            },
            {
                "title": "Applying Electron Shells to Elements",
                "key_terms": [
                "electron configuration",
                "chemical properties",
                "periodicity"
                ],
                "id": "slide_4_7f9ef8",
                "order": 4,
                "narration": "Have you ever wondered how the arrangement of electrons in an atom influences the behavior of elements? This arrangement, known as electron configuration, plays a crucial role in determining the chemical properties of elements and their periodic trends. Imagine electron shells as layers surrounding the nucleus, with each shell accommodating a specific number of electrons. This organization affects how elements interact with each other and their reactivity. Understanding electron shells helps us predict the behavior of elements in the periodic table. Now that we understand the significance of electron shells, let's explore how they contribute to the diversity of elements around us.",
                "narration_style": "default educational style"
            }
            ],
            "sub_5_283526": [
            {
                "title": "Introduction to Ions",
                "key_terms": [
                "ion",
                "atom",
                "charge"
                ],
                "id": "slide_1_609c03",
                "order": 1,
                "narration": "Have you ever wondered how atoms can become electrically charged? Let's dive into the world of ions. An ion is an atom that has gained or lost electrons, giving it a positive or negative charge. Picture it like a game of musical chairs where electrons are the players \u2014 when one leaves or joins the atom, the charge changes. This transformation from a neutral atom to an ion is what creates ions with positive or negative charges. Now that we understand the basics, let's explore how ions play a crucial role in chemistry and everyday life.",
                "narration_style": "default educational style"
            },
            {
                "title": "Formation of Ions",
                "key_terms": [
                "ionization",
                "electron",
                "proton"
                ],
                "id": "slide_2_ba47a4",
                "order": 2,
                "narration": "Have you ever wondered how atoms transform into ions? When atoms gain or lose electrons, they become charged particles called ions. This process is known as ionization. Electrons are negatively charged particles orbiting the nucleus of an atom, while protons are positively charged particles found in the nucleus. When an atom gains an electron, it becomes a negative ion, and when it loses an electron, it becomes a positive ion. This transformation is crucial in creating a balance of positive and negative charges in nature. Now that we understand how ions form, let's explore their significance in chemical reactions.",
                "narration_style": "default educational style"
            },
            {
                "title": "Neutral Atoms vs Ions",
                "key_terms": [
                "neutral",
                "ion",
                "stability"
                ],
                "id": "slide_3_d5c448",
                "order": 3,
                "narration": "Have you ever wondered about the difference between neutral atoms and ions? Let's dive in! Neutral atoms have an equal number of protons and electrons, creating a balanced charge. On the other hand, ions are charged particles due to gaining or losing electrons, upsetting the balance. This imbalance affects their stability, with ions constantly seeking to regain balance by either giving away or acquiring electrons. Understanding these differences helps us grasp how atoms maintain stability in different forms. Now that we understand the concept of neutral atoms versus ions, let's explore how this balance impacts chemical reactions.",
                "narration_style": "default educational style"
            },
            {
                "title": "Properties of Ions",
                "key_terms": [
                "ionic",
                "compound",
                "reactivity"
                ],
                "id": "slide_4_9768fa",
                "order": 4,
                "narration": "Have you ever wondered about the unique properties of ions? Ions are charged particles formed when atoms gain or lose electrons, creating an imbalance in their positive or negative charges. This imbalance leads to the formation of ionic compounds, which are held together by strong electrostatic forces. These compounds often exhibit high reactivity due to their tendency to gain or lose electrons to achieve a stable electron configuration. Understanding the properties of ions can help us comprehend the behavior of various substances in chemical reactions. Now that we understand how ions form and their impact on reactivity, let's explore their role in creating diverse compounds.",
                "narration_style": "default educational style"
            }
            ]
        }
    }

    for sub_id, slides in TutorState["slides"].items():
        for i, slide in enumerate(slides):
            TutorState["slides"][sub_id][i] = decide_visual_type(slide)

    print(json.dumps(TutorState, indent=2, ensure_ascii=False))