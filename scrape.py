import asyncio, re, json
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import pytz
from rooms import ROOMS

# Timezone for OSU (Corvallis)
TZ = pytz.timezone("America/Los_Angeles")
OUTFILE = "status.json"

def parse_time_to_today(clock_str: str, today: datetime) -> datetime:
    # Accepts 'H AM/PM' or 'H:MM AM/PM'
    fmt = "%I:%M %p" if ":" in clock_str else "%I %p"
    dt = datetime.strptime(clock_str, fmt)
    dt = today.replace(hour=dt.hour, minute=dt.minute, second=0, microsecond=0)
    return TZ.localize(dt)

async def scrape_room(page, name, url, today):
    await page.goto(url, wait_until="networkidle", timeout=60000)

    # Grab full HTML and regex for time ranges like '10:00 AM - 11:00 AM' or '10 AM–11:30 AM'
    html = await page.content()
    pattern = r"""
        (\b\d{1,2}(?::\d{2})?\s*(?:AM|PM))     # start
        \s*[-–]\s*
        (\d{1,2}(?::\d{2})?\s*(?:AM|PM)\b)     # end
    """
    matches = re.findall(pattern, html, flags=re.IGNORECASE | re.VERBOSE)
    blocks = []
    for s, e in matches:
        try:
            sdt = parse_time_to_today(s.upper(), today)
            edt = parse_time_to_today(e.upper(), today)
            if edt <= sdt:
                # handle wraparound (rare)
                edt = edt + timedelta(days=1)
            blocks.append((sdt, edt))
        except Exception:
            continue

    # Deduplicate
    seen = set()
    uniq = []
    for sdt, edt in blocks:
        key = (sdt.isoformat(), edt.isoformat())
        if key in seen: 
            continue
        seen.add(key)
        uniq.append((sdt, edt))
    blocks = sorted(uniq)

    # Compute availability
    now = datetime.now(TZ)
    horizon = now + timedelta(hours=8)

    # Keep only relevant blocks (today and in future)
    rel = [(s, e) for (s, e) in blocks if e >= now and s <= horizon]

    busy_now = any(s <= now < e for s, e in rel)
    free_until = None
    busy_until = None
    if busy_now:
        busy_until = min(e for s, e in rel if s <= now < e)
    else:
        future = sorted(s for s, e in rel if s > now)
        free_until = future[0] if future else horizon

    # Next events (up to 5)
    next_events = [{"start": s.isoformat(), "end": e.isoformat()} for s, e in rel[:5]]

    return {
        "room": name,
        "available_now": not busy_now,
        "free_until": free_until.isoformat() if free_until else None,
        "busy_until": busy_until.isoformat() if busy_until else None,
        "next_events": next_events,
        "source": url
    }

async def main():
    today = datetime.now(TZ)
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            "--disable-gpu","--no-sandbox","--disable-dev-shm-usage"
        ])
        page = await browser.new_page()
        for name, url in ROOMS.items():
            try:
                res = await scrape_room(page, name, url, today)
            except Exception as e:
                res = {"room": name, "available_now": False, "error": str(e), "source": url}
            results.append(res)
        await browser.close()

    # Sort available first, then soonest free/busy
    def sort_key(r):
        if r.get("available_now"):
            return (0, r.get("free_until") or "")
        return (1, r.get("busy_until") or "9999")
    results.sort(key=sort_key)

    with open(OUTFILE, "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
