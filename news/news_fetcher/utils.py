
from dateutil import parser
from django.utils import timezone


def word_count(text: str) -> int:
    """Returns number of words in text"""
    return len(text.split()) if text else 0


def build_gdelt_query(keywords):
    """
    Converts them into a GDELT-style search query
    eg: ("inflation" OR "oil prices" OR "trade war")
    """
    # Wrap each keyword in quotes to handle multi-word phrases correctly
    q = " OR ".join(f'"{k}"' for k in keywords)
    return f"({q})"


def normalize_article(a: dict):
    """
    Normalize raw article from GDELT
    """
    return {
        "title": a.get("title") or a.get("titleplain") or "",
        "url": a.get("url") or a.get("urlapi") or "",
        "snippet": a.get("snippet") or a.get("description") or "",
        "published_at_raw": a.get("seendate") or a.get("publishdate") or a.get("pubDate"),
        "source": a.get("domain") or a.get("source") or "gdelt",
    }


def parse_published_at(raw):
    """Parse date safely"""
    if not raw:
        return None
    try:
        dt = parser.parse(raw)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        return dt
    except Exception:
        return None
