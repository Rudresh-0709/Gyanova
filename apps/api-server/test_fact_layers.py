"""
Test each layer of the fact retrieval system individually
"""

import sys
import os

# Fix import path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app.services.fact_retrieval import (
    retrieve_from_wikipedia,
    retrieve_from_brave,
    retrieve_from_tavily,
    RetrievalLayer,
    retrieve_facts,
)

print("\n" + "=" * 80)
print("INDIVIDUAL LAYER TESTING")
print("=" * 80 + "\n")

# TEST 1: Wikipedia
print("TEST 1: Wikipedia API")
print("-" * 80)
wiki_result = retrieve_from_wikipedia("Artificial Intelligence")
if wiki_result:
    print("SUCCESS: Wikipedia WORKING")
    print(f"  Title: {wiki_result.get('title')}")
    print(f"  Summary (first 200 chars): {wiki_result.get('summary', '')[:200]}...")
    print(f"  URL: {wiki_result.get('url')}")
else:
    print("FAILED: Wikipedia NOT WORKING")

print("\n")

# TEST 2: Brave Search
print("TEST 2: Brave Search API")
print("-" * 80)
brave_result = retrieve_from_brave("Computer Generations")
if brave_result:
    print("SUCCESS: Brave Search WORKING")
    print(f"  Results found: {brave_result.get('count')}")
    for i, result in enumerate(brave_result.get("results", [])[:2], 1):
        print(f"  {i}. {result.get('title')}")
        print(f"     {result.get('description')[:100]}...")
else:
    print("FAILED: Brave Search NOT WORKING")
    print("\nTo fix: Add this to your .env file:")
    print("  BRAVE_API_KEY=your_brave_api_key_here")
    print("\nGet your API key from: https://brave.com/search/api/")

print("\n")

# TEST 3: Tavily
print("TEST 3: Tavily API")
print("-" * 80)
tavily_result = retrieve_from_tavily("History of computers")
if tavily_result:
    print("SUCCESS: Tavily WORKING")
    print(f"  Results found: {tavily_result.get('count')}")
    if tavily_result.get("answer"):
        print(f"  Answer: {tavily_result.get('answer', '')[:150]}...")
else:
    print("FAILED: Tavily NOT WORKING (it should already be configured)")

print("\n" + "=" * 80)
print("INTEGRATED TEST (with automatic escalation)")
print("=" * 80 + "\n")

# TEST 4: Integrated system
test_query = "What is vacuum tube computer"
print(f"Query: {test_query}")
print("-" * 80)
result = retrieve_facts(test_query)
print(f"Success: {result.success}")
print(f"Layer Used: {result.layer_used.value}")
print(f"Confidence: {result.confidence}")
print(f"Needs Verification: {result.needs_verification}")

print("\n" + "=" * 80)
print("\nSUMMARY:")
print("--------")
print(f"Wikipedia: {'WORKING' if wiki_result else 'FAILED'}")
print(f"Brave Search: {'WORKING' if brave_result else 'NOT CONFIGURED'}")
print(f"Tavily: {'WORKING' if tavily_result else 'FAILED'}")
print("=" * 80)
