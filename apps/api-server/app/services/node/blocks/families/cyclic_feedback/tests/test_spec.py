from blocks.families.cyclic_feedback.spec import CYCLIC_FEEDBACK_BLOCKS
from blocks.shared.base_spec import satisfies_density


def test_all_blocks_present():
    expected = ["cyclic_process_block"]
    assert set(CYCLIC_FEEDBACK_BLOCKS.keys()) == set(expected)


def test_absorbed_blocks_not_present():
    # cyclicBlock (B039) was absorbed into cyclic_process_block
    assert "cyclicBlock" not in CYCLIC_FEEDBACK_BLOCKS
    assert "CYCLIC_PROCESS_BLOCK" not in CYCLIC_FEEDBACK_BLOCKS


def test_cyclic_process_block_is_wide():
    block = CYCLIC_FEEDBACK_BLOCKS["cyclic_process_block"]
    for profile in block.item_count_profiles:
        assert profile.width_class == "wide"


def test_wide_blocks_never_have_side_images():
    for variant, block in CYCLIC_FEEDBACK_BLOCKS.items():
        for profile in block.item_count_profiles:
            assert "left" not in profile.supported_layouts, \
                f"{variant} is wide but has 'left' in supported_layouts"
            assert "right" not in profile.supported_layouts, \
                f"{variant} is wide but has 'right' in supported_layouts"


def test_not_combinable():
    # Wide block — Rule 2 forces combinable=False
    block = CYCLIC_FEEDBACK_BLOCKS["cyclic_process_block"]
    for profile in block.item_count_profiles:
        assert profile.combinable is False


def test_density_gates():
    block = CYCLIC_FEEDBACK_BLOCKS["cyclic_process_block"]
    assert satisfies_density(block, "balanced") is True
    assert satisfies_density(block, "dense") is True
    assert satisfies_density(block, "sparse") is False
    assert satisfies_density(block, "super_dense") is False


def test_item_range():
    block = CYCLIC_FEEDBACK_BLOCKS["cyclic_process_block"]
    for profile in block.item_count_profiles:
        assert profile.item_range == (3, 4)


def test_blank_only_layout():
    block = CYCLIC_FEEDBACK_BLOCKS["cyclic_process_block"]
    for profile in block.item_count_profiles:
        assert profile.supported_layouts == ("blank",)


def test_no_rule1_split():
    # Wide block — Rule 1 never applies; exactly one profile
    block = CYCLIC_FEEDBACK_BLOCKS["cyclic_process_block"]
    assert len(block.item_count_profiles) == 1