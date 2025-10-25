import os
import json
# from .generators.ai_image_generation import generate_ai_enhanced_image
# from .generators.ai_image import generate_ai_image,create_ai_enhanced_image
# from .generators.diagram import generate_diagram
# from .utils.save_image import save_image
import copy


def generate_visuals(full_state: dict, output_dir: str = "./generated_images") -> dict:
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
            image_type = slide.get("imageType")
            print(f"   🎨 Slide {idx + 1}: {slide['title']} [{image_type}]")

            image_bytes = None

            try:
                if image_type == "ai_enhanced_image":
                    # image_bytes = generate_ai_enhanced_image(slide)
                    print("AI enhanced image found")

                elif image_type == "ai_image":
                    # image_bytes = generate_ai_image(slide)
                    print("AI image found")

                elif image_type in ["chart_diagram", "diagram"]:
                    # image_bytes = generate_diagram(slide)
                    print("Chart Diagram found")

                else:
                    print(f"      ⚠️ Unknown imageType: {image_type}, skipping...")
                    continue

                # Save image to file
                # filename = f"{idx}_{image_type}.png"
                # image_path = save_image(section_dir, filename, image_bytes)
                # updated_state["slides"][section_id][idx]["image_path"] = image_path

                # print(f"      ✅ Saved: {image_path}")

            except Exception as e:
                print(f"      ❌ Failed to generate for slide {idx}: {e}")

    return updated_state

if __name__=="__main__":
    State={
    "topic": "Computer generations",
    "narration_style": "Teach like you are explaining it to a 7 year old, give analogies and examples.",
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
            "points": [
            "Atoms are the building blocks of all matter around us.",
            "They are incredibly small, too tiny to be seen with the naked eye.",
            "Each atom has a unique structure with a central nucleus.",
            "The nucleus contains protons and neutrons, while electrons orbit around it.",
            "Understanding atoms helps us comprehend the composition of everything in the universe."
            ],
            "template": "image_right",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration of a simple atomic structure with nucleus, protons, neutrons, and orbiting electrons"
        },
        {
            "title": "Atom Composition",
            "points": [
            "Atoms are made up of protons, neutrons, and electrons.",
            "Protons have a positive charge and are found in the nucleus.",
            "Neutrons are neutral and also reside in the nucleus.",
            "Electrons have a negative charge and orbit around the nucleus.",
            "The balance of these particles determines the atom's properties."
            ],
            "template": "image_left",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing the structure of an atom with protons, neutrons, and electrons"
        },
        {
            "title": "Atomic Structure",
            "points": [
            "The nucleus is the central part of an atom containing protons and neutrons.",
            "Electrons orbit around the nucleus in specific energy levels.",
            "Each energy level can hold a specific number of electrons.",
            "Atoms are stable when their electrons fill the energy levels.",
            "Understanding atomic structure helps explain chemical properties."
            ],
            "template": "image_left",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing the nucleus, orbiting electrons, and energy levels of an atom"
        },
        {
            "title": "Atom Summary",
            "points": [
            "Atoms are the basic building blocks of matter.",
            "Each atom represents an element with unique properties.",
            "When atoms combine, they form compounds with new properties."
            ],
            "template": "image_left",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing different atoms, elements, and compounds"
        }
        ],
        "sub_2_f30be9": [
        {
            "title": "Introduction to Atoms",
            "points": [
            "Atoms are the building blocks of everything around us.",
            "They are tiny particles that make up all matter.",
            "Each atom has a unique structure with a nucleus at its center.",
            "Understanding atoms helps us comprehend the composition of materials.",
            "Atoms play a crucial role in shaping the physical world."
            ],
            "template": "image_full",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing different atoms with nucleus and orbiting electrons"
        },
        {
            "title": "Protons and Neutrons",
            "points": [
            "Protons and neutrons are nucleons found in the nucleus of an atom.",
            "Protons carry a positive charge, while neutrons are neutral.",
            "The number of protons determines an element's identity on the periodic table.",
            "Neutrons help stabilize the nucleus and prevent protons from repelling each other.",
            "Together, protons and neutrons form the majority of an atom's mass."
            ],
            "template": "image_left",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing protons and neutrons in the nucleus of an atom"
        },
        {
            "title": "Electrons and Orbits",
            "points": [
            "Electrons are tiny particles with a negative charge.",
            "They move around the nucleus of an atom in specific paths called orbits.",
            "Orbits are organized into energy levels, like floors in a building.",
            "Electrons can jump between energy levels when absorbing or emitting energy.",
            "The arrangement of electrons in orbits determines an atom's properties."
            ],
            "template": "image_left",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing electrons moving in orbits around a nucleus with energy levels"
        },
        {
            "title": "Atom Structure Summary",
            "points": [
            "The nucleus is the center of an atom, containing protons and neutrons.",
            "Electron cloud surrounds the nucleus where electrons are located.",
            "Atomic mass is the total mass of protons and neutrons in an atom.",
            "Protons have a positive charge, neutrons are neutral, and electrons are negatively charged."
            ],
            "template": "image_left",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing the nucleus, electron cloud, and atomic structure of an atom"
        }
        ],
        "sub_3_7b69d0": [
        {
            "title": "Atomic Number Basics",
            "points": [
            "Atomic number defines the number of protons in an atom.",
            "It uniquely identifies elements on the periodic table.",
            "Each element has a distinct atomic number.",
            "Higher atomic numbers indicate heavier elements.",
            "Understanding atomic numbers helps in element identification."
            ],
            "template": "image_left",
            "imageType": "chart_diagram",
            "imagePrompt": "illustration showing how atomic number relates to element identification"
        },
        {
            "title": "Understanding Mass Number",
            "points": [
            "The mass number is the total number of protons and neutrons in an atom.",
            "Nucleons refer to the particles found in the nucleus, which include protons and neutrons.",
            "Isotopes are atoms of the same element with the same number of protons but different numbers of neutrons.",
            "The mass number helps differentiate isotopes of an element based on their total nucleon count."
            ],
            "template": "image_left",
            "imageType": "chart_diagram",
            "imagePrompt": "visual comparison chart showing different isotopes of an element with varying mass numbers"
        },
        {
            "title": "Relationship Between Atomic and Mass Number",
            "points": [
            "Atomic number is the number of protons in an atom.",
            "Mass number is the sum of protons and neutrons in an atom.",
            "To find neutrons, subtract the atomic number from the mass number.",
            "Isotopes have the same atomic number but different mass numbers.",
            "Understanding these numbers helps identify elements uniquely."
            ],
            "template": "image_left",
            "imageType": "chart_diagram",
            "imagePrompt": "illustration showing atomic number, mass number, and neutrons calculation"
        },
        {
            "title": "Applications of Atomic and Mass Number",
            "points": [
            "Isotopes are atoms of the same element with different numbers of neutrons.",
            "Atomic structure helps identify isotopes based on their unique mass numbers.",
            "In chemistry, isotopes play a crucial role in determining the properties and behavior of elements."
            ],
            "template": "image_left",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing isotopes of an element with different mass numbers"
        }
        ],
        "sub_4_78635b": [
        {
            "title": "Electron Shells",
            "points": [
            "Imagine an atom as a tiny solar system with electrons orbiting around the nucleus.",
            "Electron shells are like different floors in a building where electrons reside.",
            "Shells are numbered from the closest to the nucleus (1) to the farthest (higher numbers).",
            "Each shell can hold a specific number of electrons before filling up and moving to the next shell.",
            "Electron shells determine the chemical properties and reactivity of an atom."
            ],
            "template": "image_left",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing electrons orbiting in different shells around the nucleus of an atom"
        },
        {
            "title": "Electron Shell Configuration",
            "points": [
            "Electron configuration refers to the arrangement of electrons in an atom.",
            "The shell model organizes electrons into energy levels or shells.",
            "Each shell can hold a specific number of electrons.",
            "Electrons fill the inner shells before occupying outer shells.",
            "Energy levels determine an atom's chemical properties."
            ],
            "template": "image_left",
            "imageType": "chart_diagram",
            "imagePrompt": "visual diagram illustrating electron shell configuration in an atom"
        },
        {
            "title": "Electron Shells in First 20 Elements",
            "points": [
            "Electron shells are like layers around the nucleus of an atom.",
            "Each shell can hold a specific number of electrons.",
            "The first shell can hold up to 2 electrons, the second up to 8, and the third up to 8 as well.",
            "This pattern helps us understand how elements interact and form bonds."
            ],
            "template": "image_left",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing electron shells around the nucleus of an atom"
        },
        {
            "title": "Applying Electron Shells to Elements",
            "points": [
            "Electron configuration determines the arrangement of electrons in an atom.",
            "Different electron configurations influence an element's chemical properties.",
            "Elements exhibit periodic trends based on their electron shell structures.",
            "Understanding electron shells helps predict how elements will react chemically."
            ],
            "template": "image_left",
            "imageType": "chart_diagram",
            "imagePrompt": "illustration showing electron shell structures of different elements"
        }
        ],
        "sub_5_283526": [
        {
            "title": "Introduction to Ions",
            "points": [
            "Ions are atoms or molecules with an electric charge.",
            "Atoms become ions by gaining or losing electrons.",
            "Positive ions have lost electrons, while negative ions have gained electrons.",
            "Ions play crucial roles in chemical reactions and biological processes."
            ],
            "template": "image_right",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing atoms gaining or losing electrons to become ions"
        },
        {
            "title": "Formation of Ions",
            "points": [
            "Ions are charged particles formed by gaining or losing electrons.",
            "When an atom loses electrons, it becomes a positively charged ion called a cation.",
            "Conversely, when an atom gains electrons, it becomes a negatively charged ion called an anion.",
            "Ionization involves the process of creating ions by altering the electron balance in an atom.",
            "Protons in the nucleus remain constant during ion formation."
            ],
            "template": "image_left",
            "imageType": "chart_diagram",
            "imagePrompt": "illustration showing an atom losing electrons to become a cation and gaining electrons to become an anion"
        },
        {
            "title": "Neutral Atoms vs Ions",
            "points": [
            "Neutral atoms have an equal number of protons and electrons.",
            "Ions are atoms with a different number of protons and electrons.",
            "Neutral atoms are stable due to balanced charges.",
            "Ions can be positively or negatively charged, affecting stability.",
            "Ions form when atoms gain or lose electrons."
            ],
            "template": "image_left",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing neutral atom with balanced protons and electrons, and ions with unequal charges"
        },
        {
            "title": "Properties of Ions",
            "points": [
            "Ions are charged particles formed by gaining or losing electrons.",
            "Ionic compounds are formed by the attraction between positively and negatively charged ions.",
            "Ions influence the reactivity of substances by promoting chemical reactions.",
            "Ionic compounds often have high melting and boiling points due to strong electrostatic forces.",
            "The properties of ions play a crucial role in various chemical processes and reactions."
            ],
            "template": "split_horizontal",
            "imageType": "ai_enhanced_image",
            "imagePrompt": "illustration showing positively and negatively charged ions interacting in an ionic compound"
        }
        ]
    }
    }
    
    generate_visuals(State)