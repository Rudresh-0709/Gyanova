
import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    from app.services.node.slides.gyml.constants import BlockType
    print("BlockType members:", [m.name for m in BlockType])
    
    from app.services.node.slides.gyml.rules import validate_block_combination
    print("Import rules successful")
    
    # Try calling the function that had line 369
    result = validate_block_combination(["heading", "paragraph"])
    print(f"Result: {result}")
    print("VERIFICATION SUCCESSFUL")
except Exception as e:
    import traceback
    traceback.print_exc()
    print("VERIFICATION FAILED")
