"""
GOB - Government Job Agent
FastAPI Backend: manages the list of websites to monitor + alert log.

API Docs: http://localhost:8000/docs  (auto-generated, beautiful UI)
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─────────────────────────────────────────────
#  App Setup
# ─────────────────────────────────────────────

app = FastAPI(
    title="GOB - Government Job Agent",
    description="Manages sites to monitor for govt exam notifications",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite lives in /app/data (persisted via Docker volume)
DB_PATH = "/app/data/gob.db"


# ─────────────────────────────────────────────
#  Database
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # rows behave like dicts
    return conn


def init_db():
    """Create tables if they don't exist yet."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # Sites to watch
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            url         TEXT    NOT NULL UNIQUE,
            keywords    TEXT    NOT NULL DEFAULT '[]',
            description TEXT,
            active      INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Alert log (every time the agent fires an alert)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id     INTEGER REFERENCES sites(id),
            site_name   TEXT,
            title       TEXT,
            summary     TEXT,
            link        TEXT,
            confidence  TEXT,
            sent_at     TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup():
    init_db()
    # Seed with popular Indian govt exam sites if DB is empty
    seed_default_sites()


def seed_default_sites():
    conn = get_db()
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(*) FROM sites").fetchone()[0]

    if count == 0:
        default_sites = [
            {
                "name": "RBI Opportunities",
                "url": "https://www.rbi.org.in/Scripts/Opportunities.aspx",
                "keywords": ["Grade B", "Officer", "Assistant", "2026", "Notification"],
                "description": "RBI official recruitment page",
            },
            {
                "name": "GATE 2026 Official",
                "url": "https://gate2026.iitr.ac.in/",
                "keywords": ["GATE 2026", "notification", "schedule", "admit card", "result"],
                "description": "GATE 2026 official website (IIT Roorkee)",
            },
            {
                "name": "UPSC Notifications",
                "url": "https://upsc.gov.in/examinations/active-examinations",
                "keywords": ["IES", "GATE", "Engineer", "technical", "notification"],
                "description": "UPSC active exam notifications",
            },
            {
                "name": "SSC Notifications",
                "url": "https://ssc.gov.in/notice-board/notification",
                "keywords": ["JE", "Junior Engineer", "CGL", "2026", "notification"],
                "description": "SSC official notifications",
            },
        ]
        for site in default_sites:
            cursor.execute(
                "INSERT OR IGNORE INTO sites (name, url, keywords, description) VALUES (?, ?, ?, ?)",
                (site["name"], site["url"], json.dumps(site["keywords"]), site["description"]),
            )
        conn.commit()

    conn.close()


# ─────────────────────────────────────────────
#  Pydantic Models
# ─────────────────────────────────────────────

class SiteCreate(BaseModel):
    name: str
    url: str
    keywords: List[str] = []
    description: Optional[str] = None


class SiteOut(BaseModel):
    id: int
    name: str
    url: str
    keywords: List[str]
    description: Optional[str]
    active: bool
    created_at: str


class AlertCreate(BaseModel):
    site_id: Optional[int] = None
    site_name: str
    title: str
    summary: str
    link: Optional[str] = None
    confidence: Optional[str] = None


class AlertOut(BaseModel):
    id: int
    site_id: Optional[int]
    site_name: str
    title: str
    summary: str
    link: Optional[str]
    confidence: Optional[str]
    sent_at: str


# ─────────────────────────────────────────────
#  Routes: Health
# ─────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health():
    return {
        "status": "GOB is alive 🤖",
        "docs": "http://localhost:8000/docs",
        "version": "1.0.0"
    }


# ─────────────────────────────────────────────
#  Routes: Sites
# ─────────────────────────────────────────────

@app.get("/sites", response_model=List[SiteOut], tags=["Sites"])
def list_sites(active_only: bool = True):
    """Get all sites GOB is monitoring. n8n calls this every run."""
    conn = get_db()
    if active_only:
        rows = conn.execute("SELECT * FROM sites WHERE active = 1").fetchall()
    else:
        rows = conn.execute("SELECT * FROM sites").fetchall()
    conn.close()

    result = []
    for row in rows:
        site = dict(row)
        site["keywords"] = json.loads(site["keywords"])
        site["active"] = bool(site["active"])
        result.append(site)
    return result


@app.post("/sites", response_model=SiteOut, tags=["Sites"])
def add_site(site: SiteCreate):
    """Add a new website to monitor."""
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO sites (name, url, keywords, description) VALUES (?, ?, ?, ?)",
            (site.name, site.url, json.dumps(site.keywords), site.description),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM sites WHERE id = ?", (cursor.lastrowid,)).fetchone()
        result = dict(row)
        result["keywords"] = json.loads(result["keywords"])
        result["active"] = bool(result["active"])
        return result
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail=f"URL already exists: {site.url}")
    finally:
        conn.close()


@app.delete("/sites/{site_id}", tags=["Sites"])
def remove_site(site_id: int):
    """Deactivate a site (soft delete — keeps alert history)."""
    conn = get_db()
    conn.execute("UPDATE sites SET active = 0 WHERE id = ?", (site_id,))
    conn.commit()
    conn.close()
    return {"message": f"Site {site_id} deactivated"}


@app.put("/sites/{site_id}/toggle", tags=["Sites"])
def toggle_site(site_id: int):
    """Pause or resume monitoring a site."""
    conn = get_db()
    current = conn.execute("SELECT active FROM sites WHERE id = ?", (site_id,)).fetchone()
    if not current:
        raise HTTPException(status_code=404, detail="Site not found")
    new_state = 0 if current["active"] else 1
    conn.execute("UPDATE sites SET active = ? WHERE id = ?", (new_state, site_id))
    conn.commit()
    conn.close()
    return {"message": "Activated" if new_state else "Paused", "active": bool(new_state)}


# ─────────────────────────────────────────────
#  Routes: Alerts
# ─────────────────────────────────────────────

@app.get("/alerts", response_model=List[AlertOut], tags=["Alerts"])
def list_alerts(limit: int = 50):
    """View the last N alerts GOB has sent. Most recent first."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY sent_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/alerts", response_model=AlertOut, tags=["Alerts"])
def log_alert(alert: AlertCreate):
    """n8n calls this after sending a Telegram alert to keep a record."""
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO alerts (site_id, site_name, title, summary, link, confidence)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (alert.site_id, alert.site_name, alert.title, alert.summary, alert.link, alert.confidence),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM alerts WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.delete("/alerts", tags=["Alerts"])
def clear_old_alerts(keep_days: int = 30):
    """Remove alerts older than N days to keep DB clean."""
    conn = get_db()
    conn.execute(
        "DELETE FROM alerts WHERE sent_at < datetime('now', ?)",
        (f"-{keep_days} days",),
    )
    conn.commit()
    count = conn.execute("SELECT changes()").fetchone()[0]
    conn.close()
    return {"message": f"Removed {count} old alerts"}
