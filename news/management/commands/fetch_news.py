import os
from urllib.parse import quote_plus

import requests
from dateutil import parser

from django.core.management.base import BaseCommand
from django.utils import timezone

from news.models import Article



# Importing .env values
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass  # dotenv not required in production if env vars are set another way




# ----- importing from .env -----
GDELT_BASE = os.getenv("GDELT_BASE", "https://api.gdeltproject.org/api/v2/doc/doc")
GDELT_MAX = int(os.getenv("GDELT_MAX_RECORDS", "50"))     # how many raw records to request
TOP_N = int(os.getenv("TOP_N", "20"))                     # how many to save to DB
FETCH_INTERVAL = int(os.getenv("FETCH_MIN_INTERVAL_SECONDS", "3600"))  # seconds




# small list of economic keywords used to build query
ECON_KEYWORDS = ["inflation", "gdp", "recession", "oil", "sanction", "trade", "tariff", "currency"]

def build_gdelt_query(keywords):
    q = " OR ".join(quote_plus(k) for k in keywords)
    return f"({q})"


# --- function: It makes the data consistent for each article (every dict should contain same key:value)
def normalize_article(a: dict):
    """Return a normalized dict with common keys used later."""
    return {
        "title": a.get("title") or a.get("titleplain") or "",
        "url": a.get("url") or a.get("urlapi") or "",
        "snippet": a.get("snippet") or a.get("description") or "",
        "published_at_raw": a.get("seendate") or a.get("publishdate") or a.get("pubDate") or None,
        "source": a.get("domain") or a.get("source") or "gdelt",
    } 

# --- function: It takes raw time and checks it empty or included timezone or not 
def parse_published_at(raw): 
    """Try flexible parsing; return timezone-aware datetime or None."""
    if not raw:
        return None
    try:
        dt = parser.parse(raw)
        # make timezone-aware in UTC if naive
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        return dt
    except Exception:
        return None





class Command(BaseCommand):
    help = "Fetch top economic news (simple) and save to DB"

    def handle(self, *args, **options):
        now = timezone.now()

        # --- 1) caching: skip if last fetch was recent
        last = Article.objects.order_by("-fetched_at").first()
        if last:
            delta = (now - last.fetched_at).total_seconds()
            if delta < FETCH_INTERVAL:
                self.stdout.write(self.style.SUCCESS(
                    f"Skipping fetch — last fetched {int(delta)}s ago (<{FETCH_INTERVAL}s)."
                ))
                return
    
        # --- 2) fetch from GDELT 
        self.stdout.write("Fetching from GDELT...")
        params = {
            "query": build_gdelt_query(ECON_KEYWORDS),
            "mode": "artlist",
            "format": "json",
            "maxrecords": str(GDELT_MAX),
        }
        # What to search (query)
        # How to shape the output (mode)
        # What format to return (format)
        # How many records to return (maxrecords)

        # Article dictionaries stored in articles list
        articles = []
        #This prevents this command from crashing (No internet, GDELT down, Timeout, Invalid JSON, HTTP error).
        try:
            #timeout=20: If the server doesn’t respond within 20 seconds, stop and raise an error.
            resp = requests.get(GDELT_BASE, params=params, timeout=20)
            print(resp.status_code)
            print(resp.text[:500])
            # 200 → OK → continue
            # 400 → Bad request → raise error
            # 401 → Unauthorized → raise error
            # 403 → Forbidden → raise error
            # 404 → Not found → raise error
            # 500 → Server error → raise error
            resp.raise_for_status()

            #converts json -> python dict/list/str/int/None
            data = resp.json()
            raw_list = data.get("articles") or data.get("artlist") or []
            for a in raw_list:
                articles.append(normalize_article(a))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"GDELT fetch error: {e}"))
            articles = []

        # If no articles were fetched, warn and exit
        if not articles:
            self.stdout.write(self.style.WARNING("No articles returned by GDELT. Done."))
            return



        # --- 3) optionally: simple filtering by presence of any keyword in title/snippet
        filtered = []
        for a in articles:
            combined = (a["title"] + " " + a["snippet"]).lower()
            if any(k in combined for k in ECON_KEYWORDS):
                filtered.append(a)


        # fallback: if nothing matched, take original list up to TOP_N
        if not filtered:
            filtered = articles[:TOP_N]



        # --- 4) take top N, parse dates, and save to DB (update_or_create by url).
        # Check if URL is missing or already seen.
        saved = 0
        seen = set()
        for item in filtered[:TOP_N]:
            url = item.get("url")
            if not url or url in seen:
                continue
            seen.add(url)


            title = (item.get("title") or "")[:300]
            summary = item.get("snippet") or ""
            published_at = parse_published_at(item.get("published_at_raw"))

            try:
                obj, created = Article.objects.update_or_create(
                    url=url,
                    defaults={
                        "source": item.get("source") or "gdelt",
                        "title": title,
                        "summary": summary,
                        "published_at": published_at,
                    }
                )

                if created:
                    saved += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed saving {url[:80]}: {e}"))
        # --- Fetch Complete
        self.stdout.write(self.style.SUCCESS(f"Fetch complete — saved {saved} new articles."))
