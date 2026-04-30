from blocks.families.sequential_process.spec import SEQUENTIAL_PROCESS_BLOCKS
from blocks.shared.base_spec import satisfies_density


def test_all_blocks_present():
    expected = [
        "processAccordion",
        "processArrow",
        "processSteps",
        "sequentialOutput",
        "sequentialSteps",
        "branching_path",
        "input_process_output",
        "image_process",
    ]
    assert set(SEQUENTIAL_PROCESS_BLOCKS.keys()) == set(expected)


def test_image_process_renamed_not_camel():
    # L026 was renamed from imageProcess → image_process; old name must not exist
    assert "imageProcess" not in SEQUENTIAL_PROCESS_BLOCKS
    assert "image_process" in SEQUENTIAL_PROCESS_BLOCKS


def test_image_process_wide_blank_only():
    block = SEQUENTIAL_PROCESS_BLOCKS["image_process"]
    for profile in block.item_count_profiles:
        assert profile.width_class == "wide"
        assert profile.supported_layouts == ("blank",)



def test_density_gates():
    block = SEQUENTIAL_PROCESS_BLOCKS["processAccordion"]
    assert satisfies_density(block, "standard") is True
    assert satisfies_density(block, "sparse") is False

    block = SEQUENTIAL_PROCESS_BLOCKS["processSteps"]
    assert satisfies_density(block, "sparse") is True
    assert satisfies_density(block, "super_dense") is False


def test_wide_blocks_never_have_side_images():
    for variant, block in SEQUENTIAL_PROCESS_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.width_class == "wide":
                assert "left" not in profile.supported_layouts, \
                    f"{variant} is wide but has 'left' in supported_layouts"
                assert "right" not in profile.supported_layouts, \
                    f"{variant} is wide but has 'right' in supported_layouts"


def test_combinable_rule2_normal_width_low_count():
    # Rule 2: combinable=True on normal-width profiles requires item_range max ≤ 4.
    # Wide blocks may be combinable regardless of item count.
    for variant, block in SEQUENTIAL_PROCESS_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.combinable and profile.width_class == "normal":
                assert profile.item_range[1] <= 4, \
                    f"{variant}: combinable=True on normal width but max items {profile.item_range[1]} > 4"


def test_sequential_output_has_two_profiles():
    block = SEQUENTIAL_PROCESS_BLOCKS["sequentialOutput"]
    assert len(block.item_count_profiles) == 2
    low = next(p for p in block.item_count_profiles if p.item_range[0] == 2)
    high = next(p for p in block.item_count_profiles if p.item_range[1] == 6)
    assert low.width_class == "normal"
    assert high.width_class == "wide"


def test_process_arrow_absorbed_transformation_strip():
    # Verify merge note is reflected: processArrow is the surviving block
    assert "processArrow" in SEQUENTIAL_PROCESS_BLOCKS
    # transformation_strip must not exist as its own entry
    assert "transformation_strip" not in SEQUENTIAL_PROCESS_BLOCKS


def test_input_process_output_fixed_item_count():
    block = SEQUENTIAL_PROCESS_BLOCKS["input_process_output"]
    for profile in block.item_count_profiles:
        assert profile.item_range == (3, 3)


def test_branching_path_is_wide_no_side_images():
    block = SEQUENTIAL_PROCESS_BLOCKS["branching_path"]
    for profile in block.item_count_profiles:
        assert profile.width_class == "wide"
        assert "left" not in profile.supported_layouts
        assert "right" not in profile.supported_layouts


def test_process_accordion_no_blank_layout():
    block = SEQUENTIAL_PROCESS_BLOCKS["processAccordion"]
    for profile in block.item_count_profiles:
        assert "blank" not in profile.supported_layouts