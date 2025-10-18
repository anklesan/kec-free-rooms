# KEC Free Rooms

A tiny web app that scrapes public Outlook calendar pages for KEC rooms and shows which rooms are **Available now** and until when.

## Deploy (Render.com, Docker)

1. Create a new GitHub repo with these files.
2. Connect the repo on Render → **New Web Service**.
3. Render detects the Dockerfile and builds.
4. Open the URL; add to your phone's Home Screen.

### Env vars
- `SCRAPE_INTERVAL_SECONDS` (default 300).

## Local dev (optional)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# In one terminal (or a cron):
python scrape.py

# In another:
uvicorn app:app --reload --port 8000
```

## Notes
- Be polite with scraping (5 min interval is fine).
- If Outlook markup changes, update the regex/selectors in `scrape.py`.
