from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from app.models import Item, ItemVersion, Source, get_session
from sqlmodel import Session

router = APIRouter(prefix="/results", tags=["results"])

templates = Jinja2Templates(directory="/workspace/app/templates")


@router.get("/", response_class=HTMLResponse)
def list_items(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    items = session.exec(select(Item).order_by(Item.last_seen.desc())).all()
    return templates.TemplateResponse("results.html", {"request": request, "items": items})


@router.get("/item/{item_id}", response_class=HTMLResponse)
def item_detail(item_id: int, request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    versions = session.exec(select(ItemVersion).where(ItemVersion.item_id == item_id).order_by(ItemVersion.seen_at.desc())).all()
    return templates.TemplateResponse("item_detail.html", {"request": request, "item": item, "versions": versions})