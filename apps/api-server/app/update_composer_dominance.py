import os

# New Rules Logic
new_assign_emphasis = """    def _assign_emphasis(self, slide: ComposedSlide) -> ComposedSlide:
        \"\"\"
        Assign emphasis and roles.
        Enforces Rule: Exactly ONE dominant block per slide.
        \"\"\"
        for section in slide.sections:
            blocks = section.blocks # Access all blocks via property
            
            # Reset all to secondary initially
            for b in blocks:
                b.emphasis = Emphasis.SECONDARY
                
            # 1. Identify Candidate for Dominance
            dominant_candidate = None
            
            # Check for explicitly assigned roles (e.g. Code Primary)
            for b in blocks:
                if b.role == CodeRole.PRIMARY.value:
                    dominant_candidate = b
                    break
            
            # If no explicit role, find heaviest visual
            if not dominant_candidate:
                for b in blocks:
                    if b.type in [
                        BlockType.TIMELINE.value,
                        BlockType.CARD_GRID.value,
                        BlockType.SMART_LAYOUT.value,
                        BlockType.STATS.value,
                        BlockType.COMPARISON.value,
                        BlockType.TABLE.value,
                        BlockType.DIAGRAM.value,
                    ]:
                        dominant_candidate = b
                        break
            
            # If still none, check for Code (default to primary if it's the only complex thing)
            if not dominant_candidate:
                for b in blocks:
                    if b.type == BlockType.CODE.value:
                         # Default role if not set
                         if not b.role: b.role = CodeRole.PRIMARY.value
                         dominant_candidate = b
                         break

            # If still none, Heading is dominant
            if not dominant_candidate:
                for b in blocks:
                    if b.type == BlockType.HEADING.value:
                        dominant_candidate = b
                        break

            # 2. Apply Dominance
            if dominant_candidate:
                dominant_candidate.emphasis = Emphasis.PRIMARY
                
                # Check for Code Role conflicts
                if dominant_candidate.type == BlockType.CODE.value:
                    if not dominant_candidate.role:
                         dominant_candidate.role = CodeRole.PRIMARY.value
            
            # 3. Mark others as supporting (Tertiary/Secondary)
            for b in blocks:
                if b == dominant_candidate:
                    continue
                
                # Code that isn't dominant is Example or Reference
                if b.type == BlockType.CODE.value:
                    if not b.role:
                        b.role = CodeRole.EXAMPLE.value
                    
                    if b.role == CodeRole.EXAMPLE.value:
                        b.emphasis = Emphasis.SECONDARY # Supports
                    elif b.role == CodeRole.REFERENCE.value:
                        b.emphasis = Emphasis.TERTIARY # Push to end (implied)
                
                elif b.type in [BlockType.CALLOUT.value, BlockType.IMAGE.value]:
                    b.emphasis = Emphasis.TERTIARY
                else:
                    b.emphasis = Emphasis.SECONDARY
                    
        return slide
"""

new_enforce_limits_start = """    def _enforce_limits(self, slide: ComposedSlide) -> List[ComposedSlide]:
        \"\"\"
        Enforce implicit limits and explicit splitting rules.
        \"\"\"
        # Rule: Card Grid > 3 items -> Split or Promote
        for section in slide.sections:
            for block in section.blocks:
                if block.type == BlockType.CARD_GRID.value:
                    cards = block.content.get("cards", [])
                    if len(cards) > 3:
                        # Strategy: Split
                        # We return early to trigger split logic
                        return self._split_slide(slide)
        
        # Standard limits (existing logic)
        word_count = slide.total_word_count()
        block_count = slide.block_count()
"""

# We need to preserve the rest of _enforce_limits.
# Instead of rewriting the whole function blindly, I will use replace logic in Python.

file_path = "services/node/slides/gyml/composer.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1. Update Imports
# Need CodeRole
for i in range(len(lines)):
    if "Relationship," in lines[i]:
        if "CodeRole," not in "".join(lines[i : i + 5]):  # check roughly
            lines.insert(i + 1, "    CodeRole,\n")
        break

# 2. Replace _assign_emphasis
start_idx = -1
end_idx = -1
for i in range(len(lines)):
    if "def _assign_emphasis(self" in lines[i]:
        start_idx = i
    if start_idx != -1 and "def _enforce_variety" in lines[i]:
        end_idx = i
        break

if start_idx != -1:
    # Look for previous definition end more accurately?
    # Actually _enforce_variety follows _assign_emphasis typically.
    # Let's verify end_idx via indentation or next def
    pass

if start_idx != -1 and end_idx != -1:
    # Scan backwards from end_idx to find decorators or comments
    replace_start = start_idx
    replace_end = end_idx

    # We want to keep the headers if possible, but rewriting is safer.
    # But wait, I need to know where the function ENDs.
    # Usually strictly before the next one.
    # Remove the old function lines
    lines[replace_start:replace_end] = [
        new_assign_emphasis
        + "\n\n    # =========================================================================\n    # VARIETY\n    # =========================================================================\n\n"
    ]
    print("Replaced _assign_emphasis")

# 3. Update _enforce_limits
# This one is trickier because I want to inject code at the start of it.
limit_start = -1
for i in range(len(lines)):
    if "def _enforce_limits(self" in lines[i]:
        limit_start = i
        break

if limit_start != -1:
    # Insert the check right after docstring
    # Assume docstring takes 4 lines
    insert_pos = limit_start + 5

    injection = """        # Rule: Card Grid > 3 items -> Split or Promote
        for section in slide.sections:
            for block in section.blocks:
                if block.type == BlockType.CARD_GRID.value:
                    cards = block.content.get("cards", [])
                    if len(cards) > 3:
                        return self._split_slide(slide)
                        
"""
    lines.insert(insert_pos, injection)
    print("Injected Card Grid check into _enforce_limits")

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Composer dominance logic updated.")
