import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.node.content_generation_node import (
        load_llm_schema,
        generate_slide_content,
    )

    print("✅ Successfully imported content_generation_node")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

# Test Schema Loading
schema = load_llm_schema()
try:
    parsed = json.loads(schema)
    print("✅ Schema loaded and is valid JSON")
    print(f"   Schema has {len(parsed.get('properties', {}))} properties")
except Exception as e:
    print(f"❌ Schema loading failed: {e}")

print("\nReady for integration testing.")
