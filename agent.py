"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.
"""

import re
from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


# ── query parser ──────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """Extract description, size, and max_price from a natural language query."""
    parsed = {}

    # Extract max price (e.g. "under $30", "$40 max")
    price_match = re.search(r'\$(\d+(?:\.\d+)?)', query)
    if price_match:
        parsed["max_price"] = float(price_match.group(1))
    else:
        parsed["max_price"] = None

    # Extract size (e.g. "size M", "size XL", "in M")
    size_match = re.search(r'\bsize\s+([A-Z]{1,3}\d?|\d+)\b', query, re.IGNORECASE)
    if size_match:
        parsed["size"] = size_match.group(1).upper()
    else:
        parsed["size"] = None

    # Description: remove price and size mentions, clean up
    description = query
    description = re.sub(r'under\s+\$\d+(?:\.\d+)?', '', description, flags=re.IGNORECASE)
    description = re.sub(r'\$\d+(?:\.\d+)?\s*(max)?', '', description, flags=re.IGNORECASE)
    description = re.sub(r'\bsize\s+[A-Z]{1,3}\d?\b', '', description, flags=re.IGNORECASE)
    description = re.sub(r'\s+', ' ', description).strip()
    parsed["description"] = description

    return parsed


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: Search listings
    results = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )
    session["search_results"] = results

    # If no results, set error and return early
    if not results:
        session["error"] = (
            f"No listings found for '{parsed['description']}'"
            + (f" in size {parsed['size']}" if parsed["size"] else "")
            + (f" under ${parsed['max_price']:.0f}" if parsed["max_price"] else "")
            + ". Try broadening your search — remove the size filter or raise your price limit."
        )
        return session

    # Step 4: Select top result
    session["selected_item"] = results[0]

    # Step 5: Suggest outfit
    outfit = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=session["wardrobe"],
    )
    session["outfit_suggestion"] = outfit

    # Step 6: Create fit card
    fit_card = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )
    session["fit_card"] = fit_card

    # Step 7: Return session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")