import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request


PLATFORM_URLS = {
    "Amazon": "https://www.amazon.in/s?k=",
    "IKEA": "https://www.ikea.com/in/en/search/?q=",
    "Flipkart": "https://www.flipkart.com/search?q=",
    "Myntra": "https://www.myntra.com/",
    "Swiggy": "https://www.swiggy.com/search?query=",
    "Zomato": "https://www.zomato.com/search?q=",
    "Google Maps": "https://www.google.com/maps/search/",
}

FALLBACKS = {
    "home": [
        ("Lighting", "Layered ambient light to make the room feel warmer.", "IKEA", 0.28),
        ("Soft furnishings", "A few tactile accents that bring the palette together.", "Amazon", 0.22),
        ("Wall detail", "One considered art or mirror piece for a finished look.", "Flipkart", 0.18),
    ],
    "party": [
        ("Food & drinks", "A flexible catering spread sized for your guest list.", "Swiggy", 0.42),
        ("Gathering space", "Compare nearby spaces that fit your group and timing.", "Google Maps", 0.32),
        ("Table & decor", "Simple reusable details that pull the celebration together.", "Amazon", 0.14),
    ],
    "jewelry": [
        ("Everyday earrings", "A versatile pair selected to complement your outfit.", "Myntra", 0.34),
        ("Necklace", "A balanced finishing piece for the occasion and neckline.", "Amazon", 0.3),
        ("Finishing detail", "A subtle accent that works with the rest of the set.", "Flipkart", 0.2),
    ],
}


def generate_recommendations(category, payload, image=None, image_mime=None):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            suggestions = _ask_gemini(api_key, category, payload, image, image_mime)
            if suggestions:
                return {"items": suggestions, "source": "gemini", "note": "AI-generated planning estimates. Confirm live prices and availability with the retailer."}
        except (OSError, ValueError, KeyError, urllib.error.URLError, json.JSONDecodeError):
            pass
    return {
        "items": _fallback(category, payload),
        "source": "sample",
        "note": "Planning estimates for a first pass. Confirm live prices and availability with the retailer.",
    }


def _ask_gemini(api_key, category, payload, image, image_mime):
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={urllib.parse.quote(api_key)}"
    instructions = (
        "You are PocketSmart, a careful budget-planning assistant for India. "
        "Return only a JSON object with an items array. Each item must have title, detail, platform, and price (a positive INR number). "
        "Return 3 or 4 practical options whose combined prices do not exceed the user's budget. Prices are estimates, not live offers. "
        "Never claim an item is in stock or an exact current listing. Use only these platforms: Amazon, IKEA, Flipkart, Myntra, Swiggy, Zomato, Google Maps. "
        f"Category: {category}. User details: {json.dumps(payload, ensure_ascii=False)}"
    )
    parts = [{"text": instructions}]
    if image:
        import base64

        parts.append({"inline_data": {"mime_type": image_mime, "data": base64.b64encode(image).decode()}})
    body = json.dumps({"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json"}}).encode()
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read())
    text = "".join(part.get("text", "") for part in data["candidates"][0]["content"]["parts"])
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    items = json.loads(text).get("items", [])
    cleaned = []
    for item in items[:4]:
        title = str(item.get("title", "")).strip()[:80]
        detail = str(item.get("detail", "")).strip()[:220]
        platform = str(item.get("platform", "Amazon")).strip()
        price = float(item.get("price", 0))
        if not title or not detail or platform not in PLATFORM_URLS or price <= 0:
            continue
        cleaned.append(_item(title, detail, platform, round(price)))
    if not cleaned or sum(item["price"] for item in cleaned) > float(payload["budget"]):
        return []
    return cleaned


def _fallback(category, payload):
    budget = float(payload["budget"])
    query = " ".join(str(payload.get(key, "")) for key in ("room", "style", "occasion", "outfit", "locality") if payload.get(key))
    return [
        _item(title, detail, platform, max(1, round(budget * share)), query)
        for title, detail, platform, share in FALLBACKS[category]
    ]


def _item(title, detail, platform, price, query=None):
    search = urllib.parse.quote_plus(query or title)
    return {"title": title, "detail": detail, "platform": platform, "price": price, "search_url": PLATFORM_URLS[platform] + search}