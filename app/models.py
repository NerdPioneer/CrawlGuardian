from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel, Session, create_engine
import os


class Category(str, Enum):
    blog = "blog"
    news = "news"
    pricing = "pricing"
    other = "other"


class Source(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    url: str
    category: Category = Field(default=Category.other)

    # Optional site-specific selectors to fine-tune extraction
    list_selector: Optional[str] = None
    title_selector: Optional[str] = None
    link_selector: Optional[str] = None
    content_selector: Optional[str] = None
    price_selector: Optional[str] = None

    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    items: List[Item] = Relationship(back_populates="source")  # type: ignore[name-defined]
    runs: List[ScrapeRun] = Relationship(back_populates="source")  # type: ignore[name-defined]


class ScrapeRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="source.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    status: str = Field(default="running")  # running | success | error
    error_message: Optional[str] = None

    created_items: int = Field(default=0)
    changed_items: int = Field(default=0)

    # simple pointers to exported files
    export_csv_path: Optional[str] = None
    export_json_path: Optional[str] = None
    export_md_path: Optional[str] = None

    source: Optional[Source] = Relationship(back_populates="runs")


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="source.id")

    url: str
    title: Optional[str] = None

    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)

    latest_version_id: Optional[int] = Field(default=None, foreign_key="itemversion.id")

    source: Optional[Source] = Relationship(back_populates="items")
    versions: List[ItemVersion] = Relationship(back_populates="item")  # type: ignore[name-defined]


class ItemVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")

    seen_at: datetime = Field(default_factory=datetime.utcnow)
    content_text: Optional[str] = None
    content_hash: Optional[str] = None

    price_value: Optional[float] = None

    # Path to a JSON snapshot representing this version (absolute path)
    snapshot_path: Optional[str] = None

    item: Optional[Item] = Relationship(back_populates="versions")


# Database setup
DB_URL = os.getenv("DB_URL", "sqlite:////workspace/data/app.db")
engine = create_engine(DB_URL, echo=False)


def init_db() -> None:
    # Ensure directories exist
    os.makedirs("/workspace/data", exist_ok=True)
    os.makedirs(os.getenv("EXPORTS_DIR", "/workspace/exports"), exist_ok=True)
    os.makedirs(os.getenv("SNAPSHOTS_DIR", "/workspace/snapshots"), exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)