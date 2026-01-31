
import requests
from news.news_fetcher.config import (
    GDELT_BASE, GDELT_MAX, FETCH_LANGUAGE, USER_AGENT, ECON_KEYWORDS
)

def test_query(name, query_str):
    print(f"\n--- Testing: {name} ---")
    print(f"Query: {query_str}")
    
    params = {
        "query": query_str,
        "mode": "artlist",
        "format": "json",
        "maxrecords": "5",
    }
    if FETCH_LANGUAGE != "all":
        params["sourcelang"] = FETCH_LANGUAGE

    try:
        resp = requests.get(
            GDELT_BASE,
            params=params,
            timeout=20,
            headers={"User-Agent": USER_AGENT},
        )
        print(f"Status: {resp.status_code}")
        print(f"URL: {resp.url}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print("JSON Decode: SUCCESS")
                print(f"Item Count: {len(data.get('articles', []))}")
            except Exception:
                print("JSON Decode: FAILED")
                print("Response Text (first 200 chars):")
                print(resp.text[:200])
        else:
            print("Response Text:")
            print(resp.text[:200])
            
    except Exception as e:
        print(f"Exception: {e}")

def debug_fetch():
    # 1. Simple
    test_query("Simple Word", "economy")
    
    # 2. Quoted Phrase
    test_query("Quoted Phrase", '"remote work"')
    
    # 3. Two Quoted Phrases
    test_query("Two Quoted", '("remote work" OR "hiring")')
    
    # 4. Full Config Query
    # Reconstruct what utils.py does
    q = " OR ".join(f'"{k}"' for k in ECON_KEYWORDS)
    full_q = f"({q})"
    test_query("Full Config", full_q)

if __name__ == "__main__":
    debug_fetch()
