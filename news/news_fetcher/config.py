import os

# ----- config from env (with defaults) -----
GDELT_BASE = os.getenv("GDELT_BASE", "https://api.gdeltproject.org/api/v2/doc/doc")
GDELT_MAX = int(os.getenv("GDELT_MAX_RECORDS", "50"))
TOP_N = int(os.getenv("TOP_N", "20"))
FETCH_INTERVAL = int(os.getenv("FETCH_MIN_INTERVAL_SECONDS", "3"))
ARTICLE_FETCH_TIMEOUT = int(os.getenv("ARTICLE_FETCH_TIMEOUT", "200"))
ARTICLE_FETCH_PAUSE = float(os.getenv("ARTICLE_FETCH_PAUSE_SECONDS", "0.6"))
MIN_ARTICLE_LENGTH = int(os.getenv("MIN_ARTICLE_LENGTH", 300))

# language control
FETCH_LANGUAGE = os.getenv("FETCH_LANGUAGE", "en")  # "en" or "all"

# Keywords (Job Market Focus)
ECON_KEYWORDS = os.getenv(
    "ECON_KEYWORDS",
    "Remote work trends,Tech hiring 2026,Industry layoffs,Emerging skill demands,Wage growth statistics,Labor market analysis,Future of work,Gig economy,AI in recruitment,Workplace automation,Employee retention,Green jobs,Cybersecurity skills,Healthcare staffing,Education tech trends"
)
ECON_KEYWORDS = [k.strip() for k in ECON_KEYWORDS.split(",") if k.strip()]

USER_AGENT = os.getenv(
    "FETCH_USER_AGENT",
    "geo-econ-fetcher/1.0 (+https://example.com)"
)
