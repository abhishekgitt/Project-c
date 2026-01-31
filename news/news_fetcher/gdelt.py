import requests

from .config import (
    GDELT_BASE, GDELT_MAX, FETCH_LANGUAGE, USER_AGENT, ECON_KEYWORDS
)
from .utils import build_gdelt_query, normalize_article


def chunk_list(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def fetch_articles():
    """Fetch raw articles from GDELT, handling query length limits by chunking"""
    all_articles = []
    seen_urls = set()
    
    # Split keywords into chunks of 2 to avoid timeouts or query limits
    keyword_chunks = list(chunk_list(ECON_KEYWORDS, 2))
    
    # Divide max records by number of chunks to keep total roughly same (or just fetch max per chunk?)
    # Let's fetch a portion per chunk to avoid fetching too many duplicates, 
    # but GDELT sorts by relevance/date so we want top from each topic group.
    # We'll fetch GDELT_MAX for each chunk and then deduplicate/rank later.
    
    for chunk in keyword_chunks:
        if not chunk: 
            continue
            
        params = {
            "query": build_gdelt_query(chunk),
            "mode": "artlist",
            "format": "json",
            "maxrecords": str(GDELT_MAX),
        }

        if FETCH_LANGUAGE != "all":
            params["sourcelang"] = FETCH_LANGUAGE

        try:
            resp = requests.get(
                GDELT_BASE,
                params=params,
                timeout=30,
                headers={"User-Agent": USER_AGENT},
            )
            resp.raise_for_status()

            data = resp.json()
            raw_list = data.get("articles") or data.get("artlist") or []
            
            for a in raw_list:
                norm = normalize_article(a)
                if norm['url'] not in seen_urls:
                    all_articles.append(norm)
                    seen_urls.add(norm['url'])
                    
        except Exception as e:
            print(f"Error fetching chunk {chunk}: {e}")
            continue

    return all_articles
