"""
Two-Layer Fact Retrieval System (MVP Version)

A cost-efficient, reusable module for retrieving and verifying factual information:
- Layer 1 (Primary): Wikipedia - Canonical definitions and core concepts (FREE)
- Layer 2 (Secondary): Tavily - Complex synthesis across sources (PAID)

FUTURE FEATURE (Post-MVP):
- Layer 2.5 (Verification): Brave Search - Will be added after MVP (requires credit card)

The system automatically escalates to higher layers when:
- Lower layers return insufficient data
- Topic complexity requires deeper research
- Verification is needed for accuracy
"""

import os
import json
import re
import requests
from typing import Dict, Any, List, Optional
from enum import Enum
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()


class RetrievalLayer(Enum):
    """Defines the three retrieval layers"""

    WIKIPEDIA = "wikipedia"
    BRAVE = "brave"
    TAVILY = "tavily"


class FactRetrievalResult:
    """Standardized result from fact retrieval"""

    def __init__(
        self,
        success: bool,
        data: Dict[str, Any],
        layer_used: RetrievalLayer,
        confidence: str = "medium",
        needs_verification: bool = False,
    ):
        self.success = success
        self.data = data
        self.layer_used = layer_used
        self.confidence = confidence
        self.needs_verification = needs_verification

    def to_dict(self):
        return {
            "success": self.success,
            "data": self.data,
            "layer_used": self.layer_used.value,
            "confidence": self.confidence,
            "needs_verification": self.needs_verification,
        }


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 1: Wikipedia - Primary Source (FREE)
# ═══════════════════════════════════════════════════════════════════════════


def _tokenize_text(text: str) -> List[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if t]


def _normalized_text(text: str) -> str:
    return " ".join(_tokenize_text(text))


def _score_wiki_search_hit(query: str, hit: Dict[str, Any]) -> int:
    """Generic heuristic rank for Wikipedia search hits."""
    query_norm = _normalized_text(query)
    title = str(hit.get("title", "") or "")
    title_norm = _normalized_text(title)
    snippet_norm = _normalized_text(str(hit.get("snippet", "") or ""))

    score = int(hit.get("size", 0) or 0) // 15000

    query_tokens = _tokenize_text(query_norm)
    if not query_tokens:
        return score

    title_tokens = set(_tokenize_text(title_norm))
    snippet_tokens = set(_tokenize_text(snippet_norm))
    overlap_title = len([t for t in query_tokens if t in title_tokens])
    overlap_snippet = len([t for t in query_tokens if t in snippet_tokens])

    score += overlap_title * 8
    score += overlap_snippet * 2

    if title_norm == query_norm:
        score += 80
    elif query_norm and query_norm in title_norm:
        score += 30
    elif title_norm and title_norm in query_norm:
        score += 20

    # Slightly prefer canonical pages over list/disambiguation pages.
    title_l = title.lower()
    snippet_l = str(hit.get("snippet", "") or "").lower()
    if "disambiguation" in title_l or "may refer to" in snippet_l:
        score -= 30
    if title_l.endswith("(disambiguation)"):
        score -= 40

    # Light penalty for overly long titles compared to query specificity.
    score -= max(0, len(title_tokens) - len(set(query_tokens)))

    return score


def retrieve_from_wikipedia(
    query: str, max_chars: int = 6000
) -> Optional[Dict[str, Any]]:
    """
    Retrieves factual information from Wikipedia using MediaWiki REST API.
    Best for: Definitions, historical facts, scientific concepts, biographies.
    """
    try:
        import urllib.parse

        headers = {"User-Agent": "AI-Tutor-App/1.0 (Educational Content Generator)"}

        def _fetch_page(page_title: str, page_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
            encoded_title = urllib.parse.quote(page_title.replace(" ", "_"))

            content_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
            content_response = requests.get(content_url, headers=headers, timeout=5)
            if content_response.status_code != 200:
                return None

            content_data = content_response.json()
            extract = str(content_data.get("extract", "") or "")

            full_text = ""
            if page_id is not None:
                long_params = {
                    "action": "query",
                    "format": "json",
                    "prop": "extracts",
                    "pageids": str(page_id),
                    "explaintext": 1,
                    "exsectionformat": "plain",
                }
                long_response = requests.get(
                    "https://en.wikipedia.org/w/api.php",
                    params=long_params,
                    headers=headers,
                    timeout=8,
                )
                if long_response.status_code == 200:
                    long_data = long_response.json()
                    pages = long_data.get("query", {}).get("pages", {})
                    page_obj = pages.get(str(page_id), {}) if isinstance(pages, dict) else {}
                    full_text = str(page_obj.get("extract", "") or "")

            if not full_text:
                full_text = extract

            return {
                "title": page_title,
                "summary": extract[:max_chars],
                "full_text": full_text[:max_chars],
                "url": content_data.get("content_urls", {})
                .get("desktop", {})
                .get("page", ""),
                "source": "Wikipedia",
                "type": content_data.get("type", "standard"),
            }

        # Search for the article
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": 8,
            "srprop": "snippet",
        }

        search_response = requests.get(
            search_url, params=search_params, headers=headers, timeout=5
        )
        search_response.raise_for_status()
        search_data = search_response.json()

        hits = search_data.get("query", {}).get("search", [])
        if not hits:
            return None

        # Rank hits instead of blindly taking first result.
        search_hit = max(hits, key=lambda h: _score_wiki_search_hit(query, h))
        page_title = search_hit["title"]
        page_id = search_hit.get("pageid")

        return _fetch_page(page_title, page_id=page_id)

    except requests.exceptions.RequestException as e:
        print(f"   ⚠ Wikipedia API request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"   ⚠ Wikipedia JSON parsing failed: {e}")
        return None
    except Exception as e:
        print(f"   ⚠ Wikipedia retrieval failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 2: Brave Search - Verification Layer (LOW COST) - FUTURE FEATURE
# ═══════════════════════════════════════════════════════════════════════════
# NOTE: Commented out for MVP. Re-enable after getting Brave API key.
# Free tier requires credit card setup - will implement post-MVP.

# def retrieve_from_brave(query: str, max_results: int = 3) -> Optional[Dict[str, Any]]:
#     """
#     Retrieves information from Brave Search API for verification.
#     Best for: Cross-referencing facts, recent information, news.
#
#     TO ENABLE:
#     1. Get API key from https://brave.com/search/api/
#     2. Add to .env: BRAVE_API_KEY=your_key
#     3. Uncomment this function
#     """
#     try:
#         api_key = os.getenv("BRAVE_API_KEY")
#         if not api_key:
#             print("   ⚠ BRAVE_API_KEY not set, skipping Brave layer")
#             return None
#
#         url = "https://api.search.brave.com/res/v1/web/search"
#         headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
#         params = {"q": query, "count": max_results, "text_decorations": False}
#
#         response = requests.get(url, headers=headers, params=params, timeout=10)
#         response.raise_for_status()
#         data = response.json()
#
#         results = []
#         for item in data.get("web", {}).get("results", []):
#             results.append(
#                 {
#                     "title": item.get("title", ""),
#                     "description": item.get("description", ""),
#                     "url": item.get("url", ""),
#                 }
#             )
#
#         return {
#             "results": results,
#             "query": query,
#             "source": "Brave Search",
#             "count": len(results),
#         }
#
#     except Exception as e:
#         print(f"   ⚠ Brave Search failed: {e}")
#         return None


def retrieve_from_brave(query: str, max_results: int = 3) -> Optional[Dict[str, Any]]:
    """
    Brave Search - DISABLED FOR MVP (requires credit card for free tier).
    Will be re-enabled post-MVP.
    """
    return None


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 3: Tavily - Deep Synthesis (HIGHER COST)
# ═══════════════════════════════════════════════════════════════════════════


def retrieve_from_tavily(query: str, max_results: int = 5) -> Optional[Dict[str, Any]]:
    """
    Retrieves synthesized information from Tavily for complex topics.
    Best for: Nuanced analysis, multi-source synthesis, ambiguous topics.
    """
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("   ⚠ TAVILY_API_KEY not set, skipping Tavily layer")
            return None

        client = TavilyClient(api_key=api_key)
        results = client.search(query=query, max_results=max_results)

        return {
            "results": results.get("results", []),
            "query": query,
            "source": "Tavily",
            "answer": results.get("answer", ""),
            "count": len(results.get("results", [])),
        }

    except Exception as e:
        print(f"   ⚠ Tavily retrieval failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# INTELLIGENT ESCALATION LOGIC
# ═══════════════════════════════════════════════════════════════════════════


def determine_complexity(query: str, context: Dict[str, Any]) -> str:
    """
    Analyzes query complexity to determine starting layer.
    Returns: 'simple', 'moderate', 'complex'
    """
    # Simple topics - Wikipedia is sufficient
    simple_indicators = [
        "what is",
        "who is",
        "definition of",
        "meaning of",
        "explain",
        "describe",
        "introduction to",
    ]

    # Complex topics - May need Tavily
    complex_indicators = [
        "compare",
        "contrast",
        "why",
        "analyze",
        "evaluate",
        "pros and cons",
        "advantages and disadvantages",
        "debate",
        "controversy",
        "impact",
        "implications",
        "recent",
        "latest",
        "current",
        "2024",
        "2025",
        "2026",
    ]

    query_lower = query.lower()

    if any(indicator in query_lower for indicator in complex_indicators):
        return "complex"
    elif any(indicator in query_lower for indicator in simple_indicators):
        return "simple"
    else:
        return "moderate"


def retrieve_facts(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    force_layer: Optional[RetrievalLayer] = None,
) -> FactRetrievalResult:
    """
    Main entry point for fact retrieval with automatic layer escalation.

    Args:
        query: The information query
        context: Additional context (slide title, purpose, etc.)
        force_layer: Force a specific layer (for testing/debugging)

    Returns:
        FactRetrievalResult with data and metadata
    """
    context = context or {}
    complexity = determine_complexity(query, context)

    print(f"   📊 Query Complexity: {complexity.upper()}")

    # If forced to a specific layer
    if force_layer:
        print(f"   🔒 Forcing layer: {force_layer.value}")
        if force_layer == RetrievalLayer.WIKIPEDIA:
            data = retrieve_from_wikipedia(query)
            if data:
                return FactRetrievalResult(True, data, RetrievalLayer.WIKIPEDIA, "high")
        elif force_layer == RetrievalLayer.BRAVE:
            data = retrieve_from_brave(query)
            if data:
                return FactRetrievalResult(True, data, RetrievalLayer.BRAVE, "medium")
        elif force_layer == RetrievalLayer.TAVILY:
            data = retrieve_from_tavily(query)
            if data:
                return FactRetrievalResult(True, data, RetrievalLayer.TAVILY, "high")

        return FactRetrievalResult(False, {}, force_layer, "low")

    # STRATEGY 1: Simple queries → Wikipedia only
    if complexity == "simple":
        print(f"   🌐 Layer 1: Retrieving from Wikipedia...")
        wiki_data = retrieve_from_wikipedia(query)

        if wiki_data and len(wiki_data.get("summary", "")) > 100:
            print(f"   ✓ Wikipedia SUCCESS (sufficient data)")
            return FactRetrievalResult(
                success=True,
                data=wiki_data,
                layer_used=RetrievalLayer.WIKIPEDIA,
                confidence="high",
                needs_verification=False,
            )
        else:
            # Skip Brave (disabled), escalate to Tavily for verification
            print(f"   ⚠ Wikipedia insufficient, escalating to Tavily...")
            tavily_data = retrieve_from_tavily(query)
            if tavily_data:
                print(f"   ✓ Tavily SUCCESS")
                return FactRetrievalResult(
                    success=True,
                    data=tavily_data,
                    layer_used=RetrievalLayer.TAVILY,
                    confidence="high",
                    needs_verification=False,
                )

    # STRATEGY 2: Moderate queries → Wikipedia + Tavily verification (Brave disabled)
    elif complexity == "moderate":
        print(f"   🌐 Layer 1: Retrieving from Wikipedia...")
        wiki_data = retrieve_from_wikipedia(query)

        if wiki_data:
            print(f"   ✓ Wikipedia data found")
            print(f"   🎯 Layer 2: Verifying with Tavily...")
            tavily_data = retrieve_from_tavily(query)

            if tavily_data:
                print(f"   ✓ Tavily verification complete")
                # Combine both sources
                combined_data = {
                    "primary": wiki_data,
                    "synthesis": tavily_data,
                    "combined": True,
                }
                return FactRetrievalResult(
                    success=True,
                    data=combined_data,
                    layer_used=RetrievalLayer.TAVILY,
                    confidence="high",
                    needs_verification=False,
                )
            else:
                return FactRetrievalResult(
                    success=True,
                    data=wiki_data,
                    layer_used=RetrievalLayer.WIKIPEDIA,
                    confidence="medium",
                    needs_verification=True,
                )
        else:
            # No Wikipedia, try Tavily directly
            print(f"   ⚠ Wikipedia failed, using Tavily...")
            tavily_data = retrieve_from_tavily(query)
            if tavily_data:
                return FactRetrievalResult(
                    success=True,
                    data=tavily_data,
                    layer_used=RetrievalLayer.TAVILY,
                    confidence="medium",
                    needs_verification=False,
                )

    # STRATEGY 3: Complex queries → Wikipedia + Tavily (Brave layer disabled)
    elif complexity == "complex":
        print(f"   🌐 Layer 1: Checking Wikipedia...")
        wiki_data = retrieve_from_wikipedia(query)
        print(f"   🎯 Layer 2: Deep synthesis with Tavily...")
        tavily_data = retrieve_from_tavily(query)

        if tavily_data:
            print(f"   ✓ Tavily SUCCESS (comprehensive synthesis)")
            combined_data = {
                "primary": wiki_data if wiki_data else {},
                "synthesis": tavily_data,
                "combined": True,
            }
            return FactRetrievalResult(
                success=True,
                data=combined_data,
                layer_used=RetrievalLayer.TAVILY,
                confidence="high",
                needs_verification=False,
            )
        elif wiki_data:
            return FactRetrievalResult(
                success=True,
                data=wiki_data,
                layer_used=RetrievalLayer.WIKIPEDIA,
                confidence="low",
                needs_verification=True,
            )

    # Fallback if all layers fail
    print(f"   ❌ All layers failed")
    return FactRetrievalResult(
        success=False,
        data={},
        layer_used=RetrievalLayer.WIKIPEDIA,
        confidence="none",
        needs_verification=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS FOR INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════


def format_for_llm(result: FactRetrievalResult) -> str:
    """
    Formats retrieval result for LLM consumption.
    Returns a clean string with source attribution.
    """
    if not result.success:
        return ""

    formatted = f"\n📚 VERIFIED FACTS (Source: {result.layer_used.value.upper()}):\n"
    formatted += f"Confidence: {result.confidence.upper()}\n\n"

    data = result.data

    if "primary" in data and "combined" in data:
        # Combined data from multiple layers
        if data.get("primary"):
            formatted += (
                f"Primary Source (Wikipedia):\n{data['primary'].get('summary', '')}\n\n"
            )
        if data.get("synthesis"):
            formatted += (
                f"Synthesis (Tavily):\n{json.dumps(data['synthesis'], indent=2)}\n"
            )
    elif "summary" in data:
        # Wikipedia data
        full_text = str(data.get("full_text", "") or "").strip()
        summary = str(data.get("summary", "") or "").strip()
        wiki_text = full_text or summary
        formatted += f"{wiki_text}\n"
        formatted += f"Source URL: {data.get('url', '')}\n"
    elif "results" in data:
        # Brave or Tavily results
        formatted += json.dumps(data, indent=2)

    if result.needs_verification:
        formatted += "\n⚠️ WARNING: This data needs additional verification.\n"

    return formatted


if __name__ == "__main__":
    # Test the three-layer system
    print("\n" + "=" * 80)
    print("FACT RETRIEVAL SYSTEM TEST")
    print("=" * 80 + "\n")

    test_queries = [
        ("What is artificial intelligence", {"complexity": "simple"}),
        ("Computer Generations timeline", {"complexity": "moderate"}),
        (
            "Compare quantum computing vs classical computing advantages",
            {"complexity": "complex"},
        ),
    ]

    for query, context in test_queries:
        print(f"\n{'─' * 80}")
        print(f"QUERY: {query}")
        print(f"{'─' * 80}")

        result = retrieve_facts(query, context)

        print(f"\n✓ Success: {result.success}")
        print(f"✓ Layer Used: {result.layer_used.value}")
        print(f"✓ Confidence: {result.confidence}")
        print(f"\nFormatted for LLM:")
        print(format_for_llm(result))
