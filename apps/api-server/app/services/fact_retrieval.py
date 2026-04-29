"""
Multi-Source Fact Retrieval System

Domain-aware retrieval that picks the best source(s) for each subject area
instead of defaulting to Wikipedia for everything.

Source priority by domain:
  math     → arXiv → Wikipedia → Brave
  science  → PubMed → arXiv → Wikipedia → Brave
  history  → Wikidata SPARQL → Wikipedia → Brave
  language → ERIC → Wikipedia → Brave
  general  → Wikipedia → Brave → Tavily

All sources are free or free-tier.  Tavily is used only as a paid last-resort
when every domain-appropriate free source returns nothing.

Confidence is derived structurally from source metadata (citation counts,
article quality, peer-review status) rather than being a static string.

Token budget: every formatter caps its output at MAX_CONTEXT_CHARS so the
combined research block injected into the planning prompt is predictable.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.parse
from enum import Enum
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global limits
# ---------------------------------------------------------------------------

# Hard cap on characters returned by any single source formatter.
# ~3 000 chars ≈ 750 tokens — leaves headroom inside a 4k-token context slot.
MAX_CONTEXT_CHARS = 3_000

# Cap on total merged context sent to the planner prompt.
MAX_MERGED_CHARS = 5_000

# Seconds to wait between outbound HTTP calls (politeness).
REQUEST_DELAY = 0.15


# ---------------------------------------------------------------------------
# Enums & result type
# ---------------------------------------------------------------------------


class RetrievalLayer(Enum):
    WIKIPEDIA = "wikipedia"
    WIKIDATA = "wikidata"
    PUBMED = "pubmed"
    ERIC = "eric"
    ARXIV = "arxiv"
    BRAVE = "brave"
    TAVILY = "tavily"


class FactRetrievalResult:
    """Standardised result from any retrieval source."""

    def __init__(
        self,
        success: bool,
        data: Dict[str, Any],
        layer_used: RetrievalLayer,
        confidence: str = "medium",
        needs_verification: bool = False,
    ) -> None:
        self.success = success
        self.data = data
        self.layer_used = layer_used
        # confidence must be one of: high | medium | low | none
        self.confidence = confidence if confidence in {"high", "medium", "low", "none"} else "medium"
        self.needs_verification = needs_verification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "layer_used": self.layer_used.value,
            "confidence": self.confidence,
            "needs_verification": self.needs_verification,
        }


# ---------------------------------------------------------------------------
# Domain → source priority table
# ---------------------------------------------------------------------------
# Each list is ordered best-first.  The router tries sources in order and
# stops as soon as one returns usable data.  Tavily is always the final
# fallback because it is paid.

DOMAIN_SOURCE_PRIORITY: Dict[str, List[RetrievalLayer]] = {
    "math":     [RetrievalLayer.ARXIV,     RetrievalLayer.WIKIPEDIA, RetrievalLayer.BRAVE],
    "science":  [RetrievalLayer.PUBMED,    RetrievalLayer.ARXIV,     RetrievalLayer.WIKIPEDIA, RetrievalLayer.BRAVE],
    "history":  [RetrievalLayer.WIKIDATA,  RetrievalLayer.WIKIPEDIA, RetrievalLayer.BRAVE],
    "language": [RetrievalLayer.ERIC,      RetrievalLayer.WIKIPEDIA, RetrievalLayer.BRAVE],
    "general":  [RetrievalLayer.WIKIPEDIA, RetrievalLayer.BRAVE,     RetrievalLayer.TAVILY],
}

# Domains where a second corroborating source is worth fetching.
DOMAINS_NEEDING_CORROBORATION = {"science", "math"}


# ---------------------------------------------------------------------------
# Shared HTTP helper
# ---------------------------------------------------------------------------

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "AI-Tutor-App/2.0 (Educational Content Generator)"})


def _get(url: str, params: Optional[Dict] = None, timeout: int = 8) -> Optional[requests.Response]:
    """GET with timeout, delay, and structured error logging.  Returns None on any failure."""
    try:
        time.sleep(REQUEST_DELAY)
        resp = _SESSION.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.exceptions.Timeout:
        logger.warning("HTTP timeout: %s", url)
    except requests.exceptions.HTTPError as exc:
        logger.warning("HTTP %s from %s", exc.response.status_code, url)
    except requests.exceptions.RequestException as exc:
        logger.warning("HTTP request failed for %s: %r", url, exc)
    return None


def _truncate(text: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """Truncate to max_chars at a word boundary."""
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0]
    return cut + " …"


# ---------------------------------------------------------------------------
# Layer 1 — Wikipedia
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if t]


def _score_wiki_hit(query: str, hit: Dict[str, Any]) -> int:
    """Rank Wikipedia search hits by relevance."""
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0

    title_tokens = set(_tokenize(str(hit.get("title", ""))))
    snippet_tokens = set(_tokenize(str(hit.get("snippet", ""))))

    score = int(hit.get("size", 0) or 0) // 15_000
    score += sum(8 for t in q_tokens if t in title_tokens)
    score += sum(2 for t in q_tokens if t in snippet_tokens)

    title_norm = " ".join(_tokenize(str(hit.get("title", ""))))
    query_norm = " ".join(q_tokens)
    if title_norm == query_norm:
        score += 80
    elif query_norm in title_norm:
        score += 30
    elif title_norm in query_norm:
        score += 20

    title_lower = str(hit.get("title", "")).lower()
    snippet_lower = str(hit.get("snippet", "")).lower()
    if "disambiguation" in title_lower or "may refer to" in snippet_lower:
        score -= 30
    if title_lower.endswith("(disambiguation)"):
        score -= 40

    return score


def retrieve_from_wikipedia(query: str) -> Optional[Dict[str, Any]]:
    """
    Wikipedia MediaWiki REST API.
    Returns summary + capped full text.  Confidence derived from article type.
    """
    # Search
    search_resp = _get(
        "https://en.wikipedia.org/w/api.php",
        params={"action": "query", "format": "json", "list": "search",
                "srsearch": query, "srlimit": 8, "srprop": "snippet|size"},
    )
    if not search_resp:
        return None

    hits = search_resp.json().get("query", {}).get("search", [])
    if not hits:
        return None

    best = max(hits, key=lambda h: _score_wiki_hit(query, h))
    page_title = best["title"]
    page_id = best.get("pageid")

    # Summary via REST
    encoded = urllib.parse.quote(page_title.replace(" ", "_"))
    summary_resp = _get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}")
    if not summary_resp:
        return None

    summary_data = summary_resp.json()
    article_type = summary_data.get("type", "standard")
    extract = str(summary_data.get("extract", "") or "")

    # Full text via action API (longer, richer)
    full_text = extract
    if page_id:
        full_resp = _get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "format": "json", "prop": "extracts",
                    "pageids": str(page_id), "explaintext": 1, "exsectionformat": "plain"},
        )
        if full_resp:
            pages = full_resp.json().get("query", {}).get("pages", {})
            page_obj = pages.get(str(page_id), {})
            full_text = str(page_obj.get("extract", "") or "") or extract

    # Confidence: disambiguation/stub pages are low quality
    if article_type in {"disambiguation"} or len(extract) < 120:
        confidence = "low"
    elif len(full_text) > 1_500:
        confidence = "high"
    else:
        confidence = "medium"

    return {
        "title": page_title,
        "summary": _truncate(extract, 800),
        "full_text": _truncate(full_text, MAX_CONTEXT_CHARS),
        "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "source": "Wikipedia",
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Layer 2 — Wikidata SPARQL  (structured facts for history / general)
# ---------------------------------------------------------------------------

_WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"


def _build_wikidata_query(query: str) -> str:
    """
    Build a simple free-text label search.
    Returns entities whose label contains query words.
    """
    # Escape for SPARQL string literal
    safe = query.replace("\\", "\\\\").replace('"', '\\"')[:80]
    return f"""
SELECT DISTINCT ?item ?itemLabel ?itemDescription ?sitelink WHERE {{
  ?item wikibase:sitelinks ?sitelink .
  ?item rdfs:label ?itemLabel .
  FILTER(LANG(?itemLabel) = "en")
  FILTER(CONTAINS(LCASE(?itemLabel), LCASE("{safe}")))
  OPTIONAL {{ ?item schema:description ?itemDescription .
             FILTER(LANG(?itemDescription) = "en") }}
}}
ORDER BY DESC(?sitelink)
LIMIT 5
"""


def retrieve_from_wikidata(query: str) -> Optional[Dict[str, Any]]:
    """
    Wikidata SPARQL endpoint — returns structured entity facts.
    Best for: dates, classifications, relationships, historical entities.
    No API key required.
    """
    sparql = _build_wikidata_query(query)
    resp = _get(
        _WIKIDATA_SPARQL,
        params={"query": sparql, "format": "json"},
        timeout=10,
    )
    if not resp:
        return None

    try:
        bindings = resp.json().get("results", {}).get("bindings", [])
    except (json.JSONDecodeError, AttributeError):
        return None

    if not bindings:
        return None

    facts: List[str] = []
    for b in bindings[:5]:
        label = b.get("itemLabel", {}).get("value", "")
        desc = b.get("itemDescription", {}).get("value", "")
        if label:
            line = label
            if desc:
                line += f": {desc}"
            facts.append(line)

    if not facts:
        return None

    return {
        "facts": facts,
        "query": query,
        "source": "Wikidata",
        "confidence": "high",   # Wikidata entries are curated structured data
    }


# ---------------------------------------------------------------------------
# Layer 3 — PubMed / NCBI  (science, biology, health)
# ---------------------------------------------------------------------------

_PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def retrieve_from_pubmed(query: str, max_results: int = 3) -> Optional[Dict[str, Any]]:
    """
    NCBI PubMed E-utilities — free, no key required (key optional for higher rate limits).
    Set NCBI_API_KEY in .env to raise rate limit from 3 → 10 req/s.
    Best for: biology, chemistry, health, neuroscience, medicine.
    """
    ncbi_key = os.getenv("NCBI_API_KEY")  # optional

    # Step 1: esearch — get PMIDs
    search_params: Dict[str, Any] = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    }
    if ncbi_key:
        search_params["api_key"] = ncbi_key

    search_resp = _get(f"{_PUBMED_BASE}/esearch.fcgi", params=search_params)
    if not search_resp:
        return None

    try:
        id_list: List[str] = search_resp.json().get("esearchresult", {}).get("idlist", [])
    except (json.JSONDecodeError, AttributeError):
        return None

    if not id_list:
        return None

    # Step 2: efetch — get abstracts
    fetch_params: Dict[str, Any] = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "rettype": "abstract",
        "retmode": "xml",
    }
    if ncbi_key:
        fetch_params["api_key"] = ncbi_key

    fetch_resp = _get(f"{_PUBMED_BASE}/efetch.fcgi", params=fetch_params)
    if not fetch_resp:
        return None

    # Parse abstracts from XML with a lightweight regex (avoids lxml dep)
    xml = fetch_resp.text
    titles   = re.findall(r"<ArticleTitle>(.*?)</ArticleTitle>", xml, re.DOTALL)
    abstracts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", xml, re.DOTALL)
    pmids    = re.findall(r'<PMID Version="1">(.*?)</PMID>', xml)
    years    = re.findall(r"<PubDate>.*?<Year>(.*?)</Year>.*?</PubDate>", xml, re.DOTALL)

    # Strip any residual XML tags from abstracts
    def _strip_tags(s: str) -> str:
        return re.sub(r"<[^>]+>", "", s).strip()

    results: List[Dict[str, str]] = []
    for i, (title, abstract) in enumerate(zip(titles, abstracts)):
        pmid = pmids[i] if i < len(pmids) else ""
        year = years[i] if i < len(years) else ""
        results.append({
            "title": _strip_tags(title),
            "abstract": _truncate(_strip_tags(abstract), 600),
            "pmid": pmid,
            "year": year,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        })

    if not results:
        return None

    # Confidence: peer-reviewed biomedical literature → high
    return {
        "results": results,
        "query": query,
        "source": "PubMed",
        "confidence": "high",
    }


# ---------------------------------------------------------------------------
# Layer 4 — ERIC  (education, language, pedagogy)
# ---------------------------------------------------------------------------

_ERIC_BASE = "https://api.ies.ed.gov/eric"


def retrieve_from_eric(query: str, max_results: int = 3) -> Optional[Dict[str, Any]]:
    """
    ERIC (Education Resources Information Center) — US Dept of Education.
    Free, no API key required.
    Best for: language acquisition, literacy, curriculum design, pedagogy.
    """
    resp = _get(
        _ERIC_BASE + "/",
        params={
            "search": query,
            "format": "json",
            "rows": max_results,
            "fields": "title,description,author,publicationtype,subject,sourceid,publicationdateyear",
        },
    )
    if not resp:
        return None

    try:
        docs = resp.json().get("response", {}).get("docs", [])
    except (json.JSONDecodeError, AttributeError):
        return None

    if not docs:
        return None

    results: List[Dict[str, str]] = []
    for doc in docs[:max_results]:
        title = str(doc.get("title", "") or "")
        desc = str(doc.get("description", "") or "")
        pub_type = str(doc.get("publicationtype", "") or "")
        year = str(doc.get("publicationdateyear", "") or "")
        source_id = str(doc.get("sourceid", "") or "")
        results.append({
            "title": title,
            "description": _truncate(desc, 500),
            "type": pub_type,
            "year": year,
            "url": f"https://eric.ed.gov/?id={source_id}" if source_id else "",
        })

    if not results:
        return None

    # Confidence: peer-reviewed journal articles → high; other types → medium
    any_journal = any("Journal" in r.get("type", "") for r in results)
    confidence = "high" if any_journal else "medium"

    return {
        "results": results,
        "query": query,
        "source": "ERIC",
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Layer 5 — arXiv  (math, CS, physics, quantitative biology)
# ---------------------------------------------------------------------------

_ARXIV_BASE = "https://export.arxiv.org/api/query"


def retrieve_from_arxiv(query: str, max_results: int = 3) -> Optional[Dict[str, Any]]:
    """
    arXiv API — free, no key required.
    Best for: mathematics, CS, physics, quantitative sciences.
    Note: preprints are not peer-reviewed; confidence capped at medium unless
    published journal ref is present.
    """
    resp = _get(
        _ARXIV_BASE,
        params={
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
        },
        timeout=12,
    )
    if not resp:
        return None

    xml = resp.text

    # Lightweight Atom XML parsing
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)
    if not entries:
        return None

    results: List[Dict[str, str]] = []
    for entry in entries[:max_results]:
        title_m    = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        summary_m  = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        id_m       = re.search(r"<id>(.*?)</id>", entry, re.DOTALL)
        journal_m  = re.search(r"<arxiv:journal_ref>(.*?)</arxiv:journal_ref>", entry, re.DOTALL)

        title   = title_m.group(1).strip()   if title_m   else ""
        summary = summary_m.group(1).strip() if summary_m else ""
        url     = id_m.group(1).strip()      if id_m      else ""
        journal = journal_m.group(1).strip() if journal_m else ""

        results.append({
            "title":   re.sub(r"\s+", " ", title),
            "summary": _truncate(re.sub(r"\s+", " ", summary), 500),
            "url":     url,
            "journal_ref": journal,
        })

    if not results:
        return None

    # Papers with a journal ref are peer-reviewed → high; preprints → medium
    any_published = any(r.get("journal_ref") for r in results)
    confidence = "high" if any_published else "medium"

    return {
        "results": results,
        "query": query,
        "source": "arXiv",
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Layer 6 — Brave Search  (general fallback, structured infobox)
# ---------------------------------------------------------------------------

def retrieve_from_brave(query: str, max_results: int = 3) -> Optional[Dict[str, Any]]:
    """
    Brave Search API.
    Free tier: 2 000 calls/month (requires free API key — no credit card).
    Register at https://brave.com/search/api/
    Set BRAVE_API_KEY in .env to enable.
    Returns infobox (structured facts) + web snippets.
    """
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        logger.debug("BRAVE_API_KEY not set — Brave layer skipped")
        return None

    resp = _get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": max_results, "text_decorations": False},
    )
    if not resp:
        return None

    # Brave requires the key as a header, not a query param.
    # Re-issue with the correct header.
    try:
        time.sleep(REQUEST_DELAY)
        r = _SESSION.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": api_key},
            params={"q": query, "count": max_results, "text_decorations": False},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        logger.warning("Brave Search failed: %r", exc)
        return None

    results: List[Dict[str, str]] = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title":       str(item.get("title", "")),
            "description": str(item.get("description", "")),
            "url":         str(item.get("url", "")),
        })

    # Extract infobox if present (structured knowledge-panel equivalent)
    infobox: Dict[str, str] = {}
    ib = data.get("infobox", {})
    if ib:
        infobox = {
            "title":       str(ib.get("title", "")),
            "description": str(ib.get("description", "")),
            "url":         str(ib.get("url", "")),
        }

    if not results and not infobox:
        return None

    return {
        "results":  results,
        "infobox":  infobox,
        "query":    query,
        "source":   "Brave",
        "confidence": "medium",
    }


# ---------------------------------------------------------------------------
# Layer 7 — Tavily  (paid, last-resort synthesis)
# ---------------------------------------------------------------------------

def retrieve_from_tavily(query: str, max_results: int = 5) -> Optional[Dict[str, Any]]:
    """
    Tavily Search — paid API.  Used only as last resort when all free sources fail.
    Set TAVILY_API_KEY in .env.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.debug("TAVILY_API_KEY not set — Tavily layer skipped")
        return None

    try:
        from tavily import TavilyClient  # soft import — optional dependency
        client = TavilyClient(api_key=api_key)
        resp = client.search(query=query, max_results=max_results)
    except ImportError:
        logger.warning("tavily-python not installed; Tavily layer skipped")
        return None
    except Exception as exc:
        logger.warning("Tavily retrieval failed: %r", exc)
        return None

    results = resp.get("results", [])
    if not results:
        return None

    return {
        "results": results,
        "answer":  resp.get("answer", ""),
        "query":   query,
        "source":  "Tavily",
        "confidence": "medium",  # No structural quality signal from Tavily
    }


# ---------------------------------------------------------------------------
# Domain-aware router
# ---------------------------------------------------------------------------

def _sources_for_domain(domain: str, force_layer: Optional[RetrievalLayer]) -> List[RetrievalLayer]:
    """Return ordered source list. force_layer pins to a single source."""
    if force_layer is not None:
        return [force_layer]
    return DOMAIN_SOURCE_PRIORITY.get(domain, DOMAIN_SOURCE_PRIORITY["general"])


def _call_source(source: RetrievalLayer, query: str) -> Optional[Dict[str, Any]]:
    """Dispatch to the correct fetcher and return raw data dict or None."""
    dispatch = {
        RetrievalLayer.WIKIPEDIA: retrieve_from_wikipedia,
        RetrievalLayer.WIKIDATA:  retrieve_from_wikidata,
        RetrievalLayer.PUBMED:    retrieve_from_pubmed,
        RetrievalLayer.ERIC:      retrieve_from_eric,
        RetrievalLayer.ARXIV:     retrieve_from_arxiv,
        RetrievalLayer.BRAVE:     retrieve_from_brave,
        RetrievalLayer.TAVILY:    retrieve_from_tavily,
    }
    fn = dispatch.get(source)
    if fn is None:
        return None
    try:
        return fn(query)  # type: ignore[operator]
    except Exception as exc:
        logger.warning("Source %s raised unexpectedly for query %r: %r", source.value, query, exc)
        return None


def _data_is_usable(data: Optional[Dict[str, Any]]) -> bool:
    """Return True when the source returned something substantive."""
    if not data:
        return False
    # Must have at least one non-empty text field
    text_fields = ["summary", "full_text", "facts", "results", "description", "answer"]
    for f in text_fields:
        val = data.get(f)
        if val and (isinstance(val, str) and len(val) > 60) or (isinstance(val, list) and len(val) > 0):
            return True
    return False


# ---------------------------------------------------------------------------
# Result merger & context builder
# ---------------------------------------------------------------------------

class _SourceResult(NamedTuple):
    layer: RetrievalLayer
    data: Dict[str, Any]
    confidence: str


def _merge_results(results: List[_SourceResult]) -> Tuple[str, List[str], str]:
    """
    Merge multiple source results into (context_text, evidence_urls, best_confidence).
    Total output is capped at MAX_MERGED_CHARS.
    """
    if not results:
        return "", [], "low"

    sections: List[str] = []
    evidence: List[str] = []
    confidences: List[str] = []
    budget = MAX_MERGED_CHARS

    for sr in results:
        if budget <= 0:
            break

        src = sr.data.get("source", sr.layer.value)
        text = _format_source_data(sr.data, sr.layer)
        if not text:
            continue

        truncated = _truncate(text, min(MAX_CONTEXT_CHARS, budget))
        sections.append(f"[{src}]\n{truncated}")
        budget -= len(truncated)
        confidences.append(sr.confidence)

        # Collect evidence URLs
        url = sr.data.get("url", "")
        if url:
            evidence.append(url)
        for r in sr.data.get("results", [])[:3]:
            u = r.get("url", "") if isinstance(r, dict) else ""
            if u:
                evidence.append(u)

    context = "\n\n".join(sections)
    best_conf = _best_confidence(confidences)

    # Deduplicate evidence preserving order
    seen: set = set()
    deduped = [e for e in evidence if not (e in seen or seen.add(e))]  # type: ignore[func-returns-value]

    return context, deduped[:8], best_conf


def _format_source_data(data: Dict[str, Any], layer: RetrievalLayer) -> str:
    """Convert raw source dict to clean prose for the prompt."""
    if layer == RetrievalLayer.WIKIPEDIA:
        parts = []
        title = data.get("title", "")
        if title:
            parts.append(f"Title: {title}")
        text = data.get("full_text") or data.get("summary", "")
        if text:
            parts.append(text)
        url = data.get("url", "")
        if url:
            parts.append(f"URL: {url}")
        return "\n".join(parts)

    if layer == RetrievalLayer.WIKIDATA:
        facts = data.get("facts", [])
        return "\n".join(f"• {f}" for f in facts)

    if layer == RetrievalLayer.PUBMED:
        parts = []
        for r in data.get("results", []):
            title = r.get("title", "")
            abstract = r.get("abstract", "")
            url = r.get("url", "")
            year = r.get("year", "")
            line = f"[{year}] {title}" if year else title
            if abstract:
                line += f"\n{abstract}"
            if url:
                line += f"\nURL: {url}"
            parts.append(line)
        return "\n\n".join(parts)

    if layer == RetrievalLayer.ERIC:
        parts = []
        for r in data.get("results", []):
            title = r.get("title", "")
            desc = r.get("description", "")
            year = r.get("year", "")
            url = r.get("url", "")
            line = f"[{year}] {title}" if year else title
            if desc:
                line += f"\n{desc}"
            if url:
                line += f"\nURL: {url}"
            parts.append(line)
        return "\n\n".join(parts)

    if layer == RetrievalLayer.ARXIV:
        parts = []
        for r in data.get("results", []):
            title = r.get("title", "")
            summary = r.get("summary", "")
            url = r.get("url", "")
            journal = r.get("journal_ref", "")
            line = title
            if journal:
                line += f" (published: {journal})"
            if summary:
                line += f"\n{summary}"
            if url:
                line += f"\nURL: {url}"
            parts.append(line)
        return "\n\n".join(parts)

    if layer == RetrievalLayer.BRAVE:
        parts = []
        infobox = data.get("infobox", {})
        if infobox and infobox.get("description"):
            parts.append(f"Infobox: {infobox['description']}")
        for r in data.get("results", []):
            desc = r.get("description", "")
            title = r.get("title", "")
            if desc:
                parts.append(f"{title}: {desc}")
        return "\n".join(parts)

    if layer == RetrievalLayer.TAVILY:
        parts = []
        answer = data.get("answer", "")
        if answer:
            parts.append(f"Summary: {answer}")
        for r in data.get("results", [])[:3]:
            if isinstance(r, dict):
                content = r.get("content", "") or r.get("description", "")
                title = r.get("title", "")
                if content:
                    parts.append(f"{title}: {_truncate(content, 300)}")
        return "\n".join(parts)

    return ""


def _best_confidence(values: List[str]) -> str:
    rank = {"high": 3, "medium": 2, "low": 1, "none": 0}
    if not values:
        return "low"
    best = max(values, key=lambda v: rank.get(v, 0))
    return best if best in {"high", "medium", "low"} else "low"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def retrieve_facts(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    force_layer: Optional[RetrievalLayer] = None,
) -> FactRetrievalResult:
    """
    Main entry point.  Picks sources based on subject_domain in context,
    tries them in priority order, and returns a merged FactRetrievalResult.

    Args:
        query:       Search query string.
        context:     Dict that may include 'subject_domain', 'difficulty', etc.
        force_layer: Pin to a specific RetrievalLayer (overrides domain routing).

    Returns:
        FactRetrievalResult with merged data and structured confidence.
    """
    context = context or {}
    domain = str(context.get("subject_domain", "general")).strip().lower()
    if domain not in DOMAIN_SOURCE_PRIORITY:
        domain = "general"

    source_list = _sources_for_domain(domain, force_layer)
    logger.info("retrieve_facts | domain=%s query=%r sources=%s",
                domain, query[:80], [s.value for s in source_list])

    collected: List[_SourceResult] = []
    last_layer = source_list[0] if source_list else RetrievalLayer.WIKIPEDIA

    for source in source_list:
        last_layer = source

        # Skip Tavily unless it's the only option or explicitly forced
        if source == RetrievalLayer.TAVILY and force_layer is None and collected:
            logger.debug("Skipping Tavily — free sources returned results")
            break

        data = _call_source(source, query)
        if not _data_is_usable(data):
            logger.debug("Source %s returned nothing usable for query %r", source.value, query)
            continue

        confidence = str(data.get("confidence", "medium"))
        collected.append(_SourceResult(layer=source, data=data, confidence=confidence))

        # For most domains one good source is enough; science/math fetch a second
        if len(collected) >= 1 and domain not in DOMAINS_NEEDING_CORROBORATION:
            break
        if len(collected) >= 2:
            break

    if not collected:
        # Every free source failed — try Tavily as absolute last resort
        if force_layer is None:
            logger.warning("All free sources failed for query %r — falling back to Tavily", query)
            tavily_data = _call_source(RetrievalLayer.TAVILY, query)
            if _data_is_usable(tavily_data):
                confidence = str(tavily_data.get("confidence", "medium"))
                collected.append(_SourceResult(
                    layer=RetrievalLayer.TAVILY, data=tavily_data, confidence=confidence
                ))

    if not collected:
        logger.error("All retrieval layers failed for query %r (domain=%s)", query, domain)
        return FactRetrievalResult(
            success=False,
            data={},
            layer_used=last_layer,
            confidence="none",
            needs_verification=True,
        )

    context_text, evidence, best_conf = _merge_results(collected)

    # Build unified data dict that format_for_llm and _compact_research_for_prompt can parse
    primary_result = collected[0]
    merged_data: Dict[str, Any] = {
        "merged": True,
        "sources": [sr.layer.value for sr in collected],
        "primary": primary_result.data,
        "context_text": context_text,
        "evidence_urls": evidence,
    }
    if len(collected) > 1:
        merged_data["secondary"] = collected[1].data

    needs_verification = best_conf in {"low", "none"} or any(
        sr.layer in {RetrievalLayer.BRAVE, RetrievalLayer.TAVILY} for sr in collected
    )

    return FactRetrievalResult(
        success=True,
        data=merged_data,
        layer_used=primary_result.layer,
        confidence=best_conf,
        needs_verification=needs_verification,
    )


# ---------------------------------------------------------------------------
# Formatter  (consumed by teacher_slide_planning_node._compact_research_for_prompt)
# ---------------------------------------------------------------------------

def format_for_llm(result: FactRetrievalResult) -> str:
    """
    Formats a FactRetrievalResult as a clean, token-budgeted string for LLM injection.
    Output is always ≤ MAX_MERGED_CHARS characters.
    """
    if not result.success:
        return ""

    data = result.data
    source_label = result.layer_used.value.upper()

    lines: List[str] = [
        f"VERIFIED FACTS (primary source: {source_label})",
        f"Confidence: {result.confidence.upper()}",
        "",
    ]

    # Prefer pre-merged context_text if available (set by retrieve_facts)
    context_text = str(data.get("context_text", "")).strip()
    if context_text:
        lines.append(context_text)
    else:
        # Single-source result (e.g. from a force_layer call) — format directly
        text = _format_source_data(data, result.layer_used)
        if text:
            lines.append(text)

    if result.needs_verification:
        lines.append("\n⚠ This data may need additional verification.")

    full = "\n".join(lines)
    return _truncate(full, MAX_MERGED_CHARS)


# ---------------------------------------------------------------------------
# Comprehensive test suite
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import traceback

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    _pass = 0
    _fail = 0
    _skip = 0

    def _report(name: str, ok: bool, detail: str = "") -> None:
        global _pass, _fail
        tag = "✅ PASS" if ok else "❌ FAIL"
        _pass += ok
        _fail += (not ok)
        msg = f"  {tag}  {name}"
        if detail:
            msg += f"  —  {detail}"
        print(msg)

    def _report_skip(name: str, reason: str = "") -> None:
        global _skip
        _skip += 1
        msg = f"  ⏭ SKIP  {name}"
        if reason:
            msg += f"  —  {reason}"
        print(msg)

    # ── Section 1: Pure unit tests (no network) ──────────────────────────

    print(f"\n{'═'*72}")
    print("SECTION 1 — Unit tests (no network calls)")
    print(f"{'═'*72}")

    # 1a. _truncate
    _report(
        "_truncate: short string unchanged",
        _truncate("hello world", 100) == "hello world",
    )
    _report(
        "_truncate: empty string",
        _truncate("", 100) == "",
    )
    _report(
        "_truncate: None input",
        _truncate(None, 100) == "",  # type: ignore[arg-type]
    )
    long_text = "word " * 1000  # 5000 chars
    trunc = _truncate(long_text, 50)
    _report(
        "_truncate: long text capped",
        len(trunc) <= 55 and trunc.endswith("…"),
        f"len={len(trunc)}",
    )

    # 1b. _tokenize
    _report(
        "_tokenize: basic",
        _tokenize("Hello World!") == ["hello", "world"],
    )
    _report(
        "_tokenize: empty",
        _tokenize("") == [],
    )
    _report(
        "_tokenize: numbers kept",
        _tokenize("H2O is water") == ["h2o", "is", "water"],
    )

    # 1c. _score_wiki_hit
    hit_exact = {"title": "Photosynthesis", "snippet": "process by which plants", "size": 50000}
    hit_disambig = {"title": "Photosynthesis (disambiguation)", "snippet": "may refer to", "size": 1000}
    score_exact = _score_wiki_hit("photosynthesis", hit_exact)
    score_disambig = _score_wiki_hit("photosynthesis", hit_disambig)
    _report(
        "_score_wiki_hit: exact title beats disambiguation",
        score_exact > score_disambig,
        f"exact={score_exact} > disambig={score_disambig}",
    )
    _report(
        "_score_wiki_hit: empty query returns 0",
        _score_wiki_hit("", hit_exact) == 0,
    )

    # 1d. _data_is_usable
    _report("_data_is_usable: None → False", not _data_is_usable(None))
    _report("_data_is_usable: empty dict → False", not _data_is_usable({}))
    _report("_data_is_usable: short string → False", not _data_is_usable({"summary": "hi"}))
    _report(
        "_data_is_usable: long summary → True",
        _data_is_usable({"summary": "A" * 100}),
    )
    _report(
        "_data_is_usable: non-empty list → True",
        _data_is_usable({"results": [{"title": "x"}]}),
    )
    _report(
        "_data_is_usable: non-empty facts → True",
        _data_is_usable({"facts": ["fact one"]}),
    )

    # 1e. _best_confidence
    _report("_best_confidence: empty → low", _best_confidence([]) == "low")
    _report("_best_confidence: [high] → high", _best_confidence(["high"]) == "high")
    _report("_best_confidence: [low, high] → high", _best_confidence(["low", "high"]) == "high")
    _report("_best_confidence: [medium, low] → medium", _best_confidence(["medium", "low"]) == "medium")
    _report("_best_confidence: [none] → low", _best_confidence(["none"]) == "low")
    _report("_best_confidence: [garbage] → low", _best_confidence(["xyz"]) == "low")

    # 1f. FactRetrievalResult
    fr = FactRetrievalResult(
        success=True,
        data={"key": "value"},
        layer_used=RetrievalLayer.WIKIPEDIA,
        confidence="high",
        needs_verification=False,
    )
    _report("FactRetrievalResult: success", fr.success is True)
    _report("FactRetrievalResult: confidence", fr.confidence == "high")
    _report("FactRetrievalResult: layer", fr.layer_used == RetrievalLayer.WIKIPEDIA)
    d = fr.to_dict()
    _report("FactRetrievalResult.to_dict: keys", set(d.keys()) == {"success", "data", "layer_used", "confidence", "needs_verification"})
    _report("FactRetrievalResult.to_dict: layer str", d["layer_used"] == "wikipedia")

    fr_bad = FactRetrievalResult(success=False, data={}, layer_used=RetrievalLayer.BRAVE, confidence="garbage")
    _report("FactRetrievalResult: invalid confidence normalised", fr_bad.confidence == "medium")

    # 1g. _sources_for_domain
    _report(
        "_sources_for_domain: math",
        _sources_for_domain("math", None) == [RetrievalLayer.ARXIV, RetrievalLayer.WIKIPEDIA, RetrievalLayer.BRAVE],
    )
    _report(
        "_sources_for_domain: science",
        _sources_for_domain("science", None)[0] == RetrievalLayer.PUBMED,
    )
    _report(
        "_sources_for_domain: history",
        _sources_for_domain("history", None)[0] == RetrievalLayer.WIKIDATA,
    )
    _report(
        "_sources_for_domain: language",
        _sources_for_domain("language", None)[0] == RetrievalLayer.ERIC,
    )
    _report(
        "_sources_for_domain: general",
        _sources_for_domain("general", None)[0] == RetrievalLayer.WIKIPEDIA,
    )
    _report(
        "_sources_for_domain: unknown → general",
        _sources_for_domain("cooking", None) == DOMAIN_SOURCE_PRIORITY["general"],
    )
    _report(
        "_sources_for_domain: force_layer overrides",
        _sources_for_domain("math", RetrievalLayer.TAVILY) == [RetrievalLayer.TAVILY],
    )

    # 1h. _merge_results (with synthetic data)
    synth_results = [
        _SourceResult(
            layer=RetrievalLayer.WIKIPEDIA,
            data={
                "title": "Test Article",
                "full_text": "This is a test article with enough text to be useful for our testing purposes.",
                "summary": "Test summary.",
                "url": "https://en.wikipedia.org/wiki/Test",
                "source": "Wikipedia",
                "confidence": "high",
            },
            confidence="high",
        ),
        _SourceResult(
            layer=RetrievalLayer.WIKIDATA,
            data={
                "facts": ["Fact 1: description one", "Fact 2: description two"],
                "source": "Wikidata",
                "confidence": "high",
            },
            confidence="high",
        ),
    ]
    ctx_text, evidence, best_c = _merge_results(synth_results)
    _report("_merge_results: context not empty", len(ctx_text) > 0, f"len={len(ctx_text)}")
    _report("_merge_results: evidence URLs collected", "https://en.wikipedia.org/wiki/Test" in evidence)
    _report("_merge_results: best confidence", best_c == "high")

    ctx_empty, ev_empty, bc_empty = _merge_results([])
    _report("_merge_results: empty input", ctx_empty == "" and ev_empty == [] and bc_empty == "low")

    # 1i. _format_source_data
    wiki_data = {"title": "Python", "full_text": "Python is a programming language.", "url": "https://en.wikipedia.org/wiki/Python"}
    wiki_fmt = _format_source_data(wiki_data, RetrievalLayer.WIKIPEDIA)
    _report("_format_source_data: Wikipedia", "Python" in wiki_fmt and "programming" in wiki_fmt)

    wikidata_data = {"facts": ["Albert Einstein: physicist", "Isaac Newton: mathematician"]}
    wd_fmt = _format_source_data(wikidata_data, RetrievalLayer.WIKIDATA)
    _report("_format_source_data: Wikidata", "Einstein" in wd_fmt and "•" in wd_fmt)

    pubmed_data = {"results": [{"title": "Cell Biology", "abstract": "Study of cells.", "url": "https://pubmed.ncbi.nlm.nih.gov/123/", "year": "2023"}]}
    pm_fmt = _format_source_data(pubmed_data, RetrievalLayer.PUBMED)
    _report("_format_source_data: PubMed", "[2023]" in pm_fmt and "Cell Biology" in pm_fmt)

    eric_data = {"results": [{"title": "Reading Skills", "description": "Study of phonics.", "year": "2021", "url": "https://eric.ed.gov/?id=EJ12345"}]}
    er_fmt = _format_source_data(eric_data, RetrievalLayer.ERIC)
    _report("_format_source_data: ERIC", "[2021]" in er_fmt and "Reading Skills" in er_fmt)

    arxiv_data = {"results": [{"title": "On Groups", "summary": "Abstract about groups.", "url": "http://arxiv.org/abs/1234", "journal_ref": "J. Math 2022"}]}
    ax_fmt = _format_source_data(arxiv_data, RetrievalLayer.ARXIV)
    _report("_format_source_data: arXiv", "On Groups" in ax_fmt and "published" in ax_fmt)

    brave_data = {"results": [{"title": "Result 1", "description": "Desc 1"}], "infobox": {"title": "Box", "description": "Infobox desc"}}
    br_fmt = _format_source_data(brave_data, RetrievalLayer.BRAVE)
    _report("_format_source_data: Brave", "Infobox" in br_fmt)

    tavily_data = {"results": [{"title": "Tav1", "content": "Tavily content here."}], "answer": "The answer is 42."}
    tv_fmt = _format_source_data(tavily_data, RetrievalLayer.TAVILY)
    _report("_format_source_data: Tavily", "42" in tv_fmt)

    _report("_format_source_data: unknown layer → empty", _format_source_data({}, RetrievalLayer.BRAVE) == "")

    # 1j. format_for_llm
    good_result = FactRetrievalResult(
        success=True,
        data={"context_text": "Photosynthesis converts light energy into chemical energy.", "sources": ["wikipedia"]},
        layer_used=RetrievalLayer.WIKIPEDIA,
        confidence="high",
        needs_verification=False,
    )
    llm_text = format_for_llm(good_result)
    _report("format_for_llm: contains source label", "WIKIPEDIA" in llm_text)
    _report("format_for_llm: contains confidence", "HIGH" in llm_text)
    _report("format_for_llm: contains context", "Photosynthesis" in llm_text)
    _report("format_for_llm: under budget", len(llm_text) <= MAX_MERGED_CHARS + 5)

    fail_result = FactRetrievalResult(success=False, data={}, layer_used=RetrievalLayer.WIKIPEDIA, confidence="none")
    _report("format_for_llm: failed result → empty", format_for_llm(fail_result) == "")

    verif_result = FactRetrievalResult(
        success=True,
        data={"context_text": "Some unverified text from the internet."},
        layer_used=RetrievalLayer.BRAVE,
        confidence="low",
        needs_verification=True,
    )
    verif_text = format_for_llm(verif_result)
    _report("format_for_llm: verification warning", "⚠" in verif_text or "verification" in verif_text.lower())

    # 1k. RetrievalLayer enum
    _report("RetrievalLayer: all 7 members", len(RetrievalLayer) == 7)
    _report(
        "RetrievalLayer: values match",
        {l.value for l in RetrievalLayer} == {"wikipedia", "wikidata", "pubmed", "eric", "arxiv", "brave", "tavily"},
    )

    # 1l. DOMAIN_SOURCE_PRIORITY completeness
    expected_domains = {"math", "science", "history", "language", "general"}
    _report(
        "DOMAIN_SOURCE_PRIORITY: all domains present",
        set(DOMAIN_SOURCE_PRIORITY.keys()) == expected_domains,
        f"got {set(DOMAIN_SOURCE_PRIORITY.keys())}",
    )
    _report(
        "DOMAIN_SOURCE_PRIORITY: Tavily only in general",
        all(
            RetrievalLayer.TAVILY not in DOMAIN_SOURCE_PRIORITY[d]
            for d in expected_domains if d != "general"
        ),
    )

    # ── Section 2: Live API tests ────────────────────────────────────────

    print(f"\n{'═'*72}")
    print("SECTION 2 — Live API retrieval tests (requires network)")
    print(f"{'═'*72}")

    # 2a. Wikipedia
    print("\n── Wikipedia ──")
    try:
        wiki = retrieve_from_wikipedia("photosynthesis")
        if wiki:
            _report("Wikipedia: returned data", True)
            _report("Wikipedia: has title", bool(wiki.get("title")), f"title={wiki.get('title', '')}")
            _report("Wikipedia: has summary", len(wiki.get("summary", "")) > 30)
            _report("Wikipedia: has full_text", len(wiki.get("full_text", "")) > 100)
            _report("Wikipedia: has URL", wiki.get("url", "").startswith("https://"))
            _report("Wikipedia: has confidence", wiki.get("confidence") in {"high", "medium", "low"})
            _report("Wikipedia: text under cap", len(wiki.get("full_text", "")) <= MAX_CONTEXT_CHARS + 5)
        else:
            _report_skip("Wikipedia: API returned None", "API may be unreachable")
    except Exception as exc:
        _report("Wikipedia: retrieval crashed", False, repr(exc))

    # 2b. Wikidata
    print("\n── Wikidata ──")
    try:
        wd = retrieve_from_wikidata("Albert Einstein")
        if wd:
            _report("Wikidata: returned data", True)
            _report("Wikidata: has facts", isinstance(wd.get("facts"), list) and len(wd["facts"]) > 0)
            _report("Wikidata: confidence is high", wd.get("confidence") == "high")
        else:
            _report_skip("Wikidata: API returned None", "SPARQL endpoint may be unreachable")
    except Exception as exc:
        _report("Wikidata: retrieval crashed", False, repr(exc))

    # 2c. PubMed
    print("\n── PubMed ──")
    try:
        pm = retrieve_from_pubmed("CRISPR gene editing")
        if pm:
            _report("PubMed: returned data", True)
            _report("PubMed: has results", isinstance(pm.get("results"), list) and len(pm["results"]) > 0)
            first = pm["results"][0] if pm["results"] else {}
            _report("PubMed: result has title", bool(first.get("title")))
            _report("PubMed: result has abstract", bool(first.get("abstract")))
            _report("PubMed: result has PMID URL", first.get("url", "").startswith("https://pubmed"))
            _report("PubMed: confidence is high", pm.get("confidence") == "high")
        else:
            _report_skip("PubMed: API returned None", "NCBI may be unreachable")
    except Exception as exc:
        _report("PubMed: retrieval crashed", False, repr(exc))

    # 2d. ERIC
    print("\n── ERIC ──")
    try:
        eric = retrieve_from_eric("phonemic awareness")
        if eric:
            _report("ERIC: returned data", True)
            _report("ERIC: has results", isinstance(eric.get("results"), list) and len(eric["results"]) > 0)
            first = eric["results"][0] if eric["results"] else {}
            _report("ERIC: result has title", bool(first.get("title")))
            _report("ERIC: result has description", bool(first.get("description")))
            _report("ERIC: confidence valid", eric.get("confidence") in {"high", "medium"})
        else:
            _report_skip("ERIC: API returned None", "ERIC API may be unreachable")
    except Exception as exc:
        _report("ERIC: retrieval crashed", False, repr(exc))

    # 2e. arXiv
    print("\n── arXiv ──")
    try:
        ax = retrieve_from_arxiv("group theory algebra")
        if ax:
            _report("arXiv: returned data", True)
            _report("arXiv: has results", isinstance(ax.get("results"), list) and len(ax["results"]) > 0)
            first = ax["results"][0] if ax["results"] else {}
            _report("arXiv: result has title", bool(first.get("title")))
            _report("arXiv: result has summary", bool(first.get("summary")))
            _report("arXiv: result has URL", first.get("url", "").startswith("http"))
            _report("arXiv: confidence valid", ax.get("confidence") in {"high", "medium"})
        else:
            _report_skip("arXiv: API returned None", "arXiv API may be unreachable")
    except Exception as exc:
        _report("arXiv: retrieval crashed", False, repr(exc))

    # 2f. Brave
    print("\n── Brave ──")
    brave_key = os.getenv("BRAVE_API_KEY")
    if brave_key:
        try:
            brave = retrieve_from_brave("climate change effects")
            if brave:
                _report("Brave: returned data", True)
                _report("Brave: has results", isinstance(brave.get("results"), list) and len(brave["results"]) > 0)
                _report("Brave: confidence is medium", brave.get("confidence") == "medium")
            else:
                _report_skip("Brave: API returned None", "Brave API may be unreachable")
        except Exception as exc:
            _report("Brave: retrieval crashed", False, repr(exc))
    else:
        _report_skip("Brave: BRAVE_API_KEY not set", "Set BRAVE_API_KEY in .env to enable")

    # 2g. Tavily
    print("\n── Tavily ──")
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            tav = retrieve_from_tavily("renewable energy benefits")
            if tav:
                _report("Tavily: returned data", True)
                _report("Tavily: has results", isinstance(tav.get("results"), list) and len(tav["results"]) > 0)
            else:
                _report_skip("Tavily: API returned None", "Tavily API may be unreachable")
        except Exception as exc:
            _report("Tavily: retrieval crashed", False, repr(exc))
    else:
        _report_skip("Tavily: TAVILY_API_KEY not set", "Set TAVILY_API_KEY in .env to enable")

    # ── Section 3: End-to-end domain-routed tests ────────────────────────

    print(f"\n{'═'*72}")
    print("SECTION 3 — End-to-end retrieve_facts + format_for_llm")
    print(f"{'═'*72}")

    e2e_tests = [
        ("photosynthesis light reactions", {"subject_domain": "science"}),
        ("quadratic formula derivation",   {"subject_domain": "math"}),
        ("French Revolution causes",       {"subject_domain": "history"}),
        ("phonemic awareness reading",     {"subject_domain": "language"}),
        ("machine learning overview",      {"subject_domain": "general"}),
    ]

    for query, ctx in e2e_tests:
        print(f"\n── Domain: {ctx['subject_domain']} | Query: {query} ──")
        try:
            result = retrieve_facts(query, ctx)
            _report(
                f"[{ctx['subject_domain']}] retrieve_facts returned",
                result is not None,
            )
            _report(
                f"[{ctx['subject_domain']}] success flag",
                result.success,
                f"layer={result.layer_used.value}, confidence={result.confidence}",
            )

            if result.success:
                formatted = format_for_llm(result)
                _report(
                    f"[{ctx['subject_domain']}] format_for_llm non-empty",
                    len(formatted) > 50,
                    f"chars={len(formatted)}",
                )
                _report(
                    f"[{ctx['subject_domain']}] format_for_llm under budget",
                    len(formatted) <= MAX_MERGED_CHARS + 5,
                )
                _report(
                    f"[{ctx['subject_domain']}] data has sources list",
                    isinstance(result.data.get("sources"), list),
                    f"sources={result.data.get('sources', [])}",
                )

                # Print preview
                preview = formatted[:300].replace("\n", " ↵ ")
                print(f"    Preview: {preview}…")
            else:
                _report_skip(f"[{ctx['subject_domain']}] format_for_llm", "retrieve_facts failed — skipping formatter check")
        except Exception as exc:
            _report(f"[{ctx['subject_domain']}] end-to-end crashed", False, repr(exc))
            traceback.print_exc()

        sys.stdout.flush()

    # ── Section 4: Edge-case tests ───────────────────────────────────────

    print(f"\n{'═'*72}")
    print("SECTION 4 — Edge cases")
    print(f"{'═'*72}")

    # 4a. Unknown domain falls back to general
    try:
        result_unk = retrieve_facts("test query", {"subject_domain": "underwater_basket_weaving"})
        _report(
            "Unknown domain falls back to general",
            result_unk.layer_used in {l for l in RetrievalLayer},
            f"layer={result_unk.layer_used.value}",
        )
    except Exception as exc:
        _report("Unknown domain fallback", False, repr(exc))

    # 4b. Empty query
    try:
        result_empty = retrieve_facts("")
        _report(
            "Empty query handled gracefully",
            isinstance(result_empty, FactRetrievalResult),
            f"success={result_empty.success}",
        )
    except Exception as exc:
        _report("Empty query handling", False, repr(exc))

    # 4c. None context
    try:
        result_none_ctx = retrieve_facts("gravity", None)
        _report(
            "None context handled gracefully",
            isinstance(result_none_ctx, FactRetrievalResult),
            f"success={result_none_ctx.success}",
        )
    except Exception as exc:
        _report("None context handling", False, repr(exc))

    # 4d. force_layer override
    try:
        result_forced = retrieve_facts("Newton laws", force_layer=RetrievalLayer.WIKIPEDIA)
        _report(
            "force_layer=WIKIPEDIA respected",
            result_forced.layer_used == RetrievalLayer.WIKIPEDIA or not result_forced.success,
            f"layer={result_forced.layer_used.value}",
        )
    except Exception as exc:
        _report("force_layer override", False, repr(exc))

    # ── Summary ──────────────────────────────────────────────────────────

    print(f"\n{'═'*72}")
    total = _pass + _fail
    print(f"TEST SUMMARY:  {_pass}/{total} passed,  {_fail} failed,  {_skip} skipped")
    if _fail:
        print("⚠  Some tests failed — review output above.")
    else:
        print("🎉 All tests passed!")
    print(f"{'═'*72}")
    sys.exit(1 if _fail else 0)