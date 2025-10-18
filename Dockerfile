# Playwright base image with system deps
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt &&     playwright install --with-deps chromium

COPY . .

# Poll every 5 minutes by default
ENV SCRAPE_INTERVAL_SECONDS=300
ENV PORT=8000

# Run scraper loop in background and serve the UI
CMD /bin/sh -c "\
  (while true; do python scrape.py; sleep ${SCRAPE_INTERVAL_SECONDS}; done) & \
  uvicorn app:app --host 0.0.0.0 --port ${PORT}"
