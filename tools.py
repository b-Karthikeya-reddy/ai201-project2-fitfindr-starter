"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:

    listings = load_listings()

    keywords = description.lower().split()

    matches = []

    for listing in listings:

        if max_price is not None:
            if listing["price"] > max_price:
                continue

        if size is not None:
            if size.lower() not in listing["size"].lower():
                continue

        text = (
            listing["title"] + " "
            + listing["description"] + " "
            + " ".join(listing["style_tags"])
        ).lower()

        score = 0

        for word in keywords:
            if word in text:
                score += 1

        if score > 0:
            matches.append((score, listing))

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []

    for score, listing in matches:
        results.append(listing)

    return results



# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    client = _get_groq_client()

    items = wardrobe.get("items", []) if wardrobe else []

    title = new_item.get("title", "this item")

    if len(items) == 0:
        prompt = f"""
Give general styling advice for this thrifted item:

{title}

Keep it short and practical.
"""
    else:
        wardrobe_text = ""
        for item in items:
            wardrobe_text += str(item) + "\n"

        prompt = f"""
New thrifted item:
{title}

User wardrobe:
{wardrobe_text}

Suggest 1-2 outfits using the thrifted item and pieces from the wardrobe.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """Generate an Instagram-style caption for the outfit and new item."""
    if not outfit or outfit.strip() == "":
        return "Unable to create fit card because no outfit suggestion was generated."

    client = _get_groq_client()

    title = new_item.get("title", "this item")
    price = new_item.get("price", "N/A")
    platform = new_item.get("platform", "the platform")

    prompt = f"""
Create a short Instagram-style outfit caption.

Item:
{title}

Price:
${price}

Platform:
{platform}

Outfit:
{outfit}

Keep it casual and natural.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    results = search_listings(
        "vintage graphic tee",
        size=None,
        max_price=50
    )

    item = results[0]

    outfit = suggest_outfit(
        item,
        get_example_wardrobe()
    )

    print("\nOUTFIT:")
    print(outfit)

    fit_card = create_fit_card(
        outfit,
        item
    )

    print("\nFIT CARD:")
    print(fit_card)