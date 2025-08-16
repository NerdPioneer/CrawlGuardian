import json
import os
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

from selectolax.parser import HTMLParser
from sqlmodel import Session, select

from app.models import Category, Item, ItemVersion, ScrapeRun, Source
from app.services.diff import has_changed, sha256_text
from app.services.http import get_http_client


class ParsedItem:
    def __init__(self, url: str, title: Optional[str], content_text: Optional[str], price_value: Optional[float]):
        self.url = url
        self.title = title
        self.content_text = content_text
        self.price_value = price_value


def parse_items_from_html(source: Source, html: str) -> List[ParsedItem]:
    tree = HTMLParser(html)
    items: List[ParsedItem] = []

    # Basic strategies:
    # - If list_selector provided, iterate nodes and build URLs/titles via per-node selectors
    # - Else try generic article/listing heuristics
    if source.list_selector:
        for node in tree.css(source.list_selector):
            link_url = None
            title_text = None
            content_text = None
            price_value = None
            if source.link_selector:
                link = node.css_first(source.link_selector)
                if link and link.attributes.get("href"):
                    link_url = link.attributes.get("href")
            else:
                a = node.css_first("a")
                if a and a.attributes.get("href"):
                    link_url = a.attributes.get("href")
            if source.title_selector:
                t = node.css_first(source.title_selector)
                if t:
                    title_text = t.text().strip()
            elif node.css_first("a"):
                title_text = node.css_first("a").text().strip()
            if source.content_selector:
                c = node.css_first(source.content_selector)
                if c:
                    content_text = c.text().strip()
            # pricing
            if source.price_selector:
                p = node.css_first(source.price_selector)
                if p:
                    try:
                        price_value = float("".join(ch for ch in p.text() if ch.isdigit() or ch == "."))
                    except Exception:
                        price_value = None
            if link_url:
                abs_url = urljoin(source.url, link_url)
                items.append(ParsedItem(abs_url, title_text, content_text, price_value))
    else:
        # Fallback heuristics for blogs/news
        for node in tree.css("article, li, .post, .entry, .news-item"):
            a = node.css_first("a")
            if not a or not a.attributes.get("href"):
                continue
            abs_url = urljoin(source.url, a.attributes.get("href"))
            title_text = (a.text() or "").strip()
            content_text = None
            teaser = node.css_first("p")
            if teaser:
                content_text = teaser.text().strip()
            items.append(ParsedItem(abs_url, title_text, content_text, None))

    return items


def snapshot_version(version: ItemVersion) -> str:
    base_dir = os.getenv("SNAPSHOTS_DIR", "/workspace/snapshots")
    os.makedirs(base_dir, exist_ok=True)
    item_dir = os.path.join(base_dir, f"item_{version.item_id}")
    os.makedirs(item_dir, exist_ok=True)
    timestamp = version.seen_at.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(item_dir, f"v_{version.id}_{timestamp}.json")
    payload = {
        "item_id": version.item_id,
        "seen_at": version.seen_at.isoformat(),
        "content_text": version.content_text,
        "content_hash": version.content_hash,
        "price_value": version.price_value,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def run_scrape_for_source(session: Session, source: Source) -> ScrapeRun:
    run = ScrapeRun(source_id=source.id, status="running")
    session.add(run)
    session.commit()
    session.refresh(run)

    client = get_http_client()
    try:
        resp = client.get(source.url)
        if resp.status_code >= 400:
            run.status = "error"
            run.error_message = f"HTTP {resp.status_code}"
        else:
            parsed_items = parse_items_from_html(source, resp.text)

            created_items = 0
            changed_items = 0

            for parsed in parsed_items:
                existing: Optional[Item] = session.exec(select(Item).where(Item.source_id == source.id, Item.url == parsed.url)).first()
                content_hash = sha256_text(parsed.content_text or parsed.title or parsed.url)

                if existing is None:
                    item = Item(source_id=source.id, url=parsed.url, title=parsed.title)
                    session.add(item)
                    session.commit()
                    session.refresh(item)

                    version = ItemVersion(item_id=item.id, content_text=parsed.content_text, content_hash=content_hash, price_value=parsed.price_value)
                    session.add(version)
                    session.commit()
                    session.refresh(version)

                    item.latest_version_id = version.id
                    item.first_seen = datetime.utcnow()
                    item.last_seen = item.first_seen
                    session.add(item)
                    session.commit()

                    version.snapshot_path = snapshot_version(version)
                    session.add(version)
                    session.commit()

                    created_items += 1
                else:
                    latest_version: Optional[ItemVersion] = None
                    if existing.latest_version_id:
                        latest_version = session.get(ItemVersion, existing.latest_version_id)
                    if latest_version is None or has_changed(latest_version.content_hash, content_hash):
                        version = ItemVersion(item_id=existing.id, content_text=parsed.content_text, content_hash=content_hash, price_value=parsed.price_value)
                        session.add(version)
                        session.commit()
                        session.refresh(version)
                        existing.latest_version_id = version.id
                        existing.last_seen = datetime.utcnow()
                        session.add(existing)
                        session.commit()
                        version.snapshot_path = snapshot_version(version)
                        session.add(version)
                        session.commit()
                        changed_items += 1
                    else:
                        existing.last_seen = datetime.utcnow()
                        existing.title = existing.title or parsed.title
                        session.add(existing)
                        session.commit()

            run.status = "success"
            run.created_items = created_items
            run.changed_items = changed_items
    except Exception as e:
        run.status = "error"
        run.error_message = str(e)
    finally:
        run.ended_at = datetime.utcnow()
        session.add(run)
        session.commit()
        client.close()
    session.refresh(run)
    return run