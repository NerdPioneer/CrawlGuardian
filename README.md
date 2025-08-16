# Python Scraper + Web UI

A modular FastAPI application for scraping web content with a clean web UI. Supports multiple use-cases (blogs, news, competitor pricing) and exports (CSV, JSON, Markdown), email summaries, and versioned snapshots.

## Features
- Sources categorized as blog/news/pricing/other
- On-demand scraping via web UI
- Item change detection with versioned snapshots
- Exports: CSV, JSON, Markdown table
- Email summaries (SMTP)
- SQLite storage, ready for growth

## Quickstart

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Configure environment (optional):

Copy `.env.example` to `.env` and set values as needed (SMTP for email, DB path, etc.).

3. Run the server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open the UI:

Visit `http://localhost:8000`.

## Project Structure

```
app/
  main.py
  models.py
  routers/
    sources.py
    jobs.py
    results.py
  services/
    scraper.py
    exporters.py
    emailer.py
    diff.py
    scheduler.py
  utils/
    http.py
  templates/
    base.html
    index.html
    sources.html
    results.html
  static/
    styles.css
```

## Notes
- This is a foundation. Extend category-specific scrapers or add Playwright/Selenium when needed.
- Add authentication or permissions later if required.
- For scheduling, wire up the APScheduler in `services/scheduler.py`.
