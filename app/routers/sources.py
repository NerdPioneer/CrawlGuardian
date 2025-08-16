from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from app.models import Category, Source, get_session
from sqlmodel import Session

router = APIRouter(prefix="/sources", tags=["sources"])

templates = Jinja2Templates(directory="/workspace/app/templates")


@router.get("/", response_class=HTMLResponse)
def list_sources(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    sources = session.exec(select(Source)).all()
    return templates.TemplateResponse("sources.html", {"request": request, "sources": sources, "categories": list(Category)})


@router.post("/create")
def create_source(
    name: str = Form(...),
    url: str = Form(...),
    category: Category = Form(Category.other),
    list_selector: Optional[str] = Form(None),
    title_selector: Optional[str] = Form(None),
    link_selector: Optional[str] = Form(None),
    content_selector: Optional[str] = Form(None),
    price_selector: Optional[str] = Form(None),
    session: Session = Depends(get_session),
):
    source = Source(
        name=name,
        url=url,
        category=category,
        list_selector=list_selector,
        title_selector=title_selector,
        link_selector=link_selector,
        content_selector=content_selector,
        price_selector=price_selector,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return RedirectResponse("/sources/", status_code=303)


@router.post("/{source_id}/toggle")
def toggle_source(source_id: int, session: Session = Depends(get_session)):
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.active = not source.active
    session.add(source)
    session.commit()
    return RedirectResponse("/sources/", status_code=303)


@router.post("/{source_id}/delete")
def delete_source(source_id: int, session: Session = Depends(get_session)):
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    session.delete(source)
    session.commit()
    return RedirectResponse("/sources/", status_code=303)