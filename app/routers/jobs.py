from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from app.models import ScrapeRun, Source, get_session
from app.services.scraper import run_scrape_for_source
from app.services.exporters import export_run_results
from sqlmodel import Session

router = APIRouter(prefix="/jobs", tags=["jobs"])

templates = Jinja2Templates(directory="/workspace/app/templates")


@router.post("/{source_id}/run")
def run_job(source_id: int, session: Session = Depends(get_session)):
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    run = run_scrape_for_source(session, source)
    export_run_results(session, run)
    return RedirectResponse("/results/", status_code=303)


@router.get("/runs", response_class=HTMLResponse)
def list_runs(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    runs = session.exec(select(ScrapeRun).order_by(ScrapeRun.started_at.desc())).all()
    return templates.TemplateResponse("runs.html", {"request": request, "runs": runs})