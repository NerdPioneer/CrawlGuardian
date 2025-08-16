import csv
import json
import os
from datetime import datetime
from typing import List

from app.models import Item, ItemVersion, ScrapeRun, Source


def export_items_to_csv(items: List[Item], path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["item_id", "source_id", "title", "url", "first_seen", "last_seen", "latest_version_hash", "price_value"])
        for item in items:
            latest_hash = None
            price_value = None
            if item.latest_version_id and item.versions:
                latest = sorted(item.versions, key=lambda v: v.seen_at)[-1]
                latest_hash = latest.content_hash
                price_value = latest.price_value
            writer.writerow([
                item.id,
                item.source_id,
                item.title or "",
                item.url,
                item.first_seen.isoformat(),
                item.last_seen.isoformat(),
                latest_hash or "",
                price_value if price_value is not None else "",
            ])
    return path


def export_items_to_json(items: List[Item], path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = []
    for item in items:
        latest_hash = None
        price_value = None
        if item.latest_version_id and item.versions:
            latest = sorted(item.versions, key=lambda v: v.seen_at)[-1]
            latest_hash = latest.content_hash
            price_value = latest.price_value
        payload.append({
            "item_id": item.id,
            "source_id": item.source_id,
            "title": item.title,
            "url": item.url,
            "first_seen": item.first_seen.isoformat(),
            "last_seen": item.last_seen.isoformat(),
            "latest_version_hash": latest_hash,
            "price_value": price_value,
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def export_items_to_markdown(items: List[Item], path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = ["| ID | Source | Title | URL | First Seen | Last Seen | Latest Hash | Price |", "|---:|---:|---|---|---|---|---|---:|"]
    for item in items:
        latest_hash = None
        price_value = None
        if item.latest_version_id and item.versions:
            latest = sorted(item.versions, key=lambda v: v.seen_at)[-1]
            latest_hash = latest.content_hash
            price_value = latest.price_value
        title = (item.title or "").replace("|", "\|")
        url_md = f"[{item.url}]({item.url})"
        lines.append(
            f"| {item.id} | {item.source_id} | {title} | {url_md} | {item.first_seen.isoformat()} | {item.last_seen.isoformat()} | {latest_hash or ''} | {'' if price_value is None else price_value} |"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def export_run_results(session, run: ScrapeRun) -> ScrapeRun:
    from sqlmodel import select
    items = session.exec(select(Item).where(Item.source_id == run.source_id)).all()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_dir = os.getenv("EXPORTS_DIR", "/workspace/exports")
    base = os.path.join(base_dir, f"source_{run.source_id}")
    os.makedirs(base, exist_ok=True)

    csv_path = os.path.join(base, f"items_{timestamp}.csv")
    json_path = os.path.join(base, f"items_{timestamp}.json")
    md_path = os.path.join(base, f"items_{timestamp}.md")

    export_items_to_csv(items, csv_path)
    export_items_to_json(items, json_path)
    export_items_to_markdown(items, md_path)

    run.export_csv_path = csv_path
    run.export_json_path = json_path
    run.export_md_path = md_path
    session.add(run)
    session.commit()
    session.refresh(run)
    return run