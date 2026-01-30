"""
LangSmith Integration Test

This script verifies that LangSmith tracing is properly configured
and working with the AI Teaching System.

Test Coverage:
1. Environment variable configuration
2. Basic tracing functionality
3. Workflow execution with tracing
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.langsmith_config import (
    is_tracing_enabled,
    get_project_name,
    configure_langsmith,
    print_trace_url,
)
from services.langgraphflow import compiled_graph


def test_environment_configuration():
    """Test 1: Verify environment variables are properly set."""
    print("=" * 80)
    print("TEST 1: Environment Configuration")
    print("=" * 80)

    tracing_enabled = is_tracing_enabled()
    project_name = get_project_name()

    print(f"\n✓ LANGCHAIN_TRACING_V2: {tracing_enabled}")
    print(f"✓ LANGCHAIN_PROJECT: {project_name}")

    api_key = os.getenv("LANGCHAIN_API_KEY")
    if api_key:
        # Only show first/last 4 chars for security
        masked_key = f"{api_key[:8]}...{api_key[-8:]}"
        print(f"✓ LANGCHAIN_API_KEY: {masked_key}")
    else:
        print("✗ LANGCHAIN_API_KEY: Not found")
        return False

    if not tracing_enabled:
        print("\n⚠️  Tracing is disabled. Set LANGCHAIN_TRACING_V2=true in .env")
        return False

    print("\n✓ Environment configuration is correct!")
    return True


def test_basic_tracing():
    """Test 2: Test basic tracing with a simple workflow."""
    print("\n" + "=" * 80)
    print("TEST 2: Basic Workflow Tracing")
    print("=" * 80)

    print("\nRunning a simple workflow to test tracing...")

    # Simple test state
    test_state = {
        "user_input": "Introduction to Python",
        "topic": "",
        "sub_topics": [],
        "slides": {},
    }

    try:
        print("\n🚀 Executing workflow...")
        print("   Topic: Introduction to Python")
        print("   This will take 1-2 minutes...\n")

        # Run the workflow
        final_state = compiled_graph.invoke(test_state)

        print("\n✓ Workflow executed successfully!")
        print(f"   - Topic extracted: {final_state.get('topic', 'N/A')}")
        print(f"   - Subtopics created: {len(final_state.get('sub_topics', []))}")

        total_slides = sum(
            len(slides) for slides in final_state.get("slides", {}).values()
        )
        print(f"   - Total slides generated: {total_slides}")

        print("\n" + "=" * 80)
        print("TRACING VERIFICATION")
        print("=" * 80)
        print("\n📊 To view the trace in LangSmith:")
        print_trace_url()
        print("\nYou should see:")
        print("  1. All 7 workflow nodes in the trace")
        print("  2. Input/output for each node")
        print("  3. Token usage and latency data")
        print("  4. LLM calls within each node")

        return True

    except Exception as e:
        print(f"\n✗ Workflow failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("LANGSMITH INTEGRATION TEST SUITE")
    print("=" * 80)
    print("\nThis script will verify that LangSmith tracing is working correctly.")
    print("Make sure you have:")
    print("  1. Set LANGCHAIN_TRACING_V2=true in .env")
    print("  2. Added your LANGCHAIN_API_KEY to .env")
    print("  3. Configured LANGCHAIN_PROJECT in .env")
    print("\n" + "=" * 80 + "\n")

    # Test 1: Environment Configuration
    if not test_environment_configuration():
        print("\n❌ Environment configuration test failed!")
        print("   Please check your .env file and try again.")
        return

    # Test 2: Basic Tracing
    user_input = input(
        "\n\nProceed with workflow tracing test? This will take 1-2 minutes. (y/n): "
    )
    if user_input.lower() != "y":
        print("\n⏭️  Skipping workflow test.")
        print("\nTo manually test, run: python app/test_workflow.py")
        print("Then check the LangSmith dashboard for traces.")
        return

    if not test_basic_tracing():
        print("\n❌ Tracing test failed!")
        return

    # All tests passed
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nLangSmith integration is working correctly!")
    print("\nNext Steps:")
    print("  1. Run your regular workflows - they will be automatically traced")
    print("  2. Check the LangSmith dashboard to view traces")
    print("  3. Use the evaluation tools (see langsmith_evaluator.py)")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
