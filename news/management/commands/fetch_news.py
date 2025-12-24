import os
import time
from urllib.parse import quote_plus #replaces spaces with the plus sign (+) for URL

import requests
from dateutil import parser

from django.core.management.base import BaseCommand
from django.utils import timezone

# models
from news.models import Article, SummaryPage

# HTML parser fallback
from bs4 import BeautifulSoup




# True when importing package is successful
try:
    from newspaper import Article as NewspaperArticle  # newspaper3k
    HAVE_NEWSPAPER = True
except Exception:
    HAVE_NEWSPAPER = False

try:
    import trafilatura
    HAVE_TRAFILATURA = True
except Exception:
    HAVE_TRAFILATURA = False




# load .env values
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass



# ----- config from env (with defaults) -----
GDELT_BASE = os.getenv("GDELT_BASE", "https://api.gdeltproject.org/api/v2/doc/doc")
GDELT_MAX = int(os.getenv("GDELT_MAX_RECORDS", "50"))
TOP_N = int(os.getenv("TOP_N", "20"))
FETCH_INTERVAL = int(os.getenv("FETCH_MIN_INTERVAL_SECONDS", "3600"))
ARTICLE_FETCH_TIMEOUT = int(os.getenv("ARTICLE_FETCH_TIMEOUT", "10")) #It sets how long (in seconds) your app will wait
ARTICLE_FETCH_PAUSE = float(os.getenv("ARTICLE_FETCH_PAUSE_SECONDS", "0.6"))  # delay between fetching pages

#Keywords
ECON_KEYWORDS = os.getenv("ECON_KEYWORDS", "inflation,gdp,recession,oil,sanction,trade,tariff,currency")
ECON_KEYWORDS = [k.strip() for k in ECON_KEYWORDS.split(",") if k.strip()]

USER_AGENT = os.getenv("FETCH_USER_AGENT", "geo-econ-fetcher/1.0 (+https://example.com)")




def build_gdelt_query(keywords):
    """Converts them into a GDELT-style search query and returns it ,
    eg: (inflation OR oil+prices OR trade+war)"""
    q = " OR ".join(quote_plus(k) for k in keywords)
    return f"({q})"




def normalize_article(a: dict):
    """It takes raw article data (from GDELT / APIs) and them makes a predictable structure and returns it"""
    return {
        "title": a.get("title") or a.get("titleplain") or "",
        "url": a.get("url") or a.get("urlapi") or "",
        "snippet": a.get("snippet") or a.get("description") or "",
        "published_at_raw": a.get("seendate") or a.get("publishdate") or a.get("pubDate") or None,
        "source": a.get("domain") or a.get("source") or "gdelt",
    }



def parse_published_at(raw):
    """Try flexible parsing; return timezone-aware datetime or None."""
    if not raw:
        return None
    try:
        # Converts raw date strings into Python datetime objects.
        dt = parser.parse(raw)                      
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        return dt
    except Exception:
        return None







def fetch_full_text(url, timeout=ARTICLE_FETCH_TIMEOUT):
    """
    Try several extractors to get the full article text.
    Returns string (may be empty) — never raises.
    Order: newspaper3k -> trafilatura -> BeautifulSoup fallback.
    """
    #startswith() returns boolean value
    # Returns empty string if not start with http or any other condition like None,etc.
    if not url or not url.startswith("http"):
        return ""

    headers = {"User-Agent": USER_AGENT}


    # 1) newspaper3k
    if HAVE_NEWSPAPER:
        try:
            art = NewspaperArticle(url, language="en")
            art.download()
            art.parse()
            text = (art.text or "").strip()
            if text and len(text) > 100:
                return text
        except Exception:
            pass


    # 2) trafilatura - extracts the main readable text from web pages, It removes ads, menus, footers, sidebars, junk.
    if HAVE_TRAFILATURA:
        try:
            downloaded = trafilatura.fetch_url(url, timeout=timeout)
            if downloaded:
                text = trafilatura.extract(downloaded)
                if text and len(text) > 100:
                    return text.strip()
        except Exception:
            pass


    # 3) fallback: fetch raw HTML and extract <article> or <p> tags
    # header = User agent
    try:
        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # prefer <article> tag(s)
        article_tag = soup.find("article")
        if article_tag:
            paragraphs = [
                p.get_text(" ", strip=True) 
                for p in article_tag.find_all("p")
                ]
            
            txt = "\n\n".join([p for p in paragraphs if p])
            if len(txt) > 200:
                return txt.strip()

        # fallback: gather main <p> tags and return joined content
        p_texts = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        if p_texts:
            joined = "\n\n".join([pt for pt in p_texts if pt])
            # attempt to heuristically remove nav/footer by taking the largest continuous block
            if len(joined) > 200:
                return joined.strip()

    except Exception:
        pass

    return ""






class Command(BaseCommand):
    help = "Fetch top economic news (GDELT) and save to DB (Article + SummaryPage), extracting full article text"

    def handle(self, *args, **options):
        now = timezone.now()

        # 1) caching: skip if last fetch was recent
        last = Article.objects.order_by("-fetched_at").first()
        if last:
            delta = (now - last.fetched_at).total_seconds()
            if delta < FETCH_INTERVAL:
                self.stdout.write(self.style.SUCCESS(
                    f"Skipping fetch — last fetched {int(delta)}s ago (<{FETCH_INTERVAL}s)."
                ))
                return

        # 2) fetch from GDELT
        self.stdout.write("Fetching list from GDELT...")
        params = {
            "query": build_gdelt_query(ECON_KEYWORDS),
            "mode": "artlist",
            "format": "json",
            "maxrecords": str(GDELT_MAX),
        }

        # Converts the received articles to structured python objects for database
        articles = []
        try:
            resp = requests.get(GDELT_BASE, params=params, timeout=20, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            # Converts JSON to python dict
            data = resp.json()
            raw_list = data.get("articles") or data.get("artlist") or []
            for a in raw_list:
                articles.append(normalize_article(a))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"GDELT fetch error: {e}"))
            articles = []

        if not articles:
            self.stdout.write(self.style.WARNING("No articles returned by GDELT. Done."))
            return

  
        # 3) simple filtering by keywords presence in title/snippet
        filtered = []
        for a in articles:
            combined = (a["title"] + " " + a["snippet"]).lower()
            if any(k in combined for k in ECON_KEYWORDS):
                filtered.append(a)

        if not filtered:
            filtered = articles[:TOP_N]

        # 4) save top N, create Article and linked SummaryPage
        saved = 0 # How many article is saved 
        seen = set()

        for item in filtered[:TOP_N]:
            url = item.get("url")
            if not url or url in seen:
                continue
            seen.add(url)

            title = (item.get("title") or "")[:300] # 300 max limit for the title 
            provided_snippet = (item.get("snippet") or "").strip()
            published_at = parse_published_at(item.get("published_at_raw"))


            # if provided snippet too short, try to extract full body
            snippet = provided_snippet
            if not snippet or len(snippet) < 200:
                # polite pause before fetching article page
                try:
                    fetched_text = fetch_full_text(url)
                    # prefer fetched_text if it's substantially longer
                    if fetched_text and len(fetched_text) > len(snippet):
                        snippet = fetched_text
                except Exception:
                    snippet = snippet or ""



                # small pause so we don't hammer target sites
                time.sleep(ARTICLE_FETCH_PAUSE)

            try:
                # Save/update Article
                # update_or_create() returns object, bool 
                article_obj, created = Article.objects.update_or_create(
                    url=url,
                    defaults={
                        "source": item.get("source") or "gdelt",
                        "title": title,
                        "snippet": snippet,
                        "published_at": published_at,
                    }
                )

                # Create or update SummaryPage for this Article.
                # Seed short_preview and ai_summary with snippet so the AI pipeline has source text.
                short_preview = (snippet or title)[:200]

                SummaryPage.objects.update_or_create(
                    article=article_obj,
                    defaults={
                        "hero_image": "",             # fill if you extract images later
                        "short_preview": short_preview,
                        "ai_summary": snippet,        # seed with raw snippet so AI worker can read it
                        "summarized_at": None,
                        "model_version": "",
                        "confidence": None,
                    }
                )

                if created:
                    saved += 1

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed saving {url[:80]}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Fetch complete — saved {saved} new articles."))
