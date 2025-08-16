import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import init_db
from app.routers import sources, jobs, results

# Load .env early
load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "ScraperUI"))

# Static and templates
app.mount("/static", StaticFiles(directory="/workspace/app/static"), name="static")
templates = Jinja2Templates(directory="/workspace/app/templates")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/download")
def download(path: str) -> FileResponse:
    # Simple safe-guard: only allow downloads from exports/snapshots directories
    allowed_roots = [os.getenv("EXPORTS_DIR", "/workspace/exports"), os.getenv("SNAPSHOTS_DIR", "/workspace/snapshots")]
    path = os.path.abspath(path)
    if any(path.startswith(os.path.abspath(root)) for root in allowed_roots) and os.path.exists(path):
        filename = os.path.basename(path)
        return FileResponse(path, filename=filename)
    return RedirectResponse("/", status_code=302)


# Routers
app.include_router(sources.router)
app.include_router(jobs.router)
app.include_router(results.router)