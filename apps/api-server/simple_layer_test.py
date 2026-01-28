"""
Simple test - no emojis, just facts
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app.services.fact_retrieval import (
    retrieve_from_wikipedia,
    retrieve_from_brave,
    retrieve_from_tavily,
)

print("\nTEST 1: Wikipedia")
print("-" * 60)
try:
    wiki = retrieve_from_wikipedia("Artificial Intelligence")
    if wiki:
        print("STATUS: WORKING")
        print("Title:", wiki.get("title"))
        print("Summary:", wiki.get("summary", "")[:150])
    else:
        print("STATUS: FAILED - No data returned")
except Exception as e:
    print("STATUS: ERROR -", str(e))

print("\n\nTEST 2: Brave Search")
print("-" * 60)
try:
    brave = retrieve_from_brave("Computer Generations")
    if brave:
        print("STATUS: WORKING")
        print("Results:", brave.get("count"))
    else:
        print("STATUS: NOT CONFIGURED")
        print("ADD TO .env FILE: BRAVE_API_KEY=your_key_here")
        print("Get key from: https://brave.com/search/api/")
except Exception as e:
    print("STATUS: ERROR -", str(e))

print("\n\nTEST 3: Tavily")
print("-" * 60)
try:
    tavily = retrieve_from_tavily("Computer history")
    if tavily:
        print("STATUS: WORKING (same as before)")
        print("Results:", tavily.get("count"))
    else:
        print("STATUS: FAILED")
except Exception as e:
    print("STATUS: ERROR -", str(e))

print("\n" + "=" * 60)
print("SUMMARY:")
print("Wikipedia:", "WORKING" if wiki else "FAILED")
print("Brave:", "CONFIGURED" if brave else "NOT CONFIGURED")
print("Tavily:", "WORKING" if tavily else "FAILED")
print("=" * 60)
