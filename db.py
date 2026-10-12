"""SQLite storage. One table. status: new -> match | rejected -> sent | failed."""
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone

from settings import DATA_DIR, DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    channel     TEXT    NOT NULL,
    msg_id      INTEGER NOT NULL,
    text        TEXT    NOT NULL,
    text_hash   TEXT    NOT NULL,
    link        TEXT,
    extra_links TEXT,
    status      TEXT    NOT NULL DEFAULT 'new',
    details     TEXT,
    created_at  TEXT    NOT NULL,
    UNIQUE (channel, msg_id)
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_hash   ON jobs (text_hash);
"""


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_post(conn, channel, msg_id, text, link, extra_links) -> bool:
    """Store a post. False if it was already stored or the same text was seen before (cross-posted job)."""
    h = hashlib.sha256(re.sub(r"\s+", " ", text).strip().casefold().encode()).hexdigest()
    if conn.execute("SELECT 1 FROM jobs WHERE text_hash = ?", (h,)).fetchone():
        return False
    cur = conn.execute(
        "INSERT OR IGNORE INTO jobs (channel, msg_id, text, text_hash, link, extra_links, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (channel, msg_id, text, h, link, json.dumps(extra_links) if extra_links else None,
         datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )
    conn.commit()
    return cur.rowcount == 1


def posts(conn, status):
    return conn.execute("SELECT * FROM jobs WHERE status = ? ORDER BY id", (status,)).fetchall()


def set_status(conn, post_id, status) -> None:
    conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, post_id))
    conn.commit()


def set_details(conn, post_id, details: dict) -> None:
    conn.execute("UPDATE jobs SET details = ? WHERE id = ?", (json.dumps(details, ensure_ascii=False), post_id))
    conn.commit()


def counts(conn) -> dict:
    return {r["status"]: r["c"] for r in conn.execute("SELECT status, COUNT(*) AS c FROM jobs GROUP BY status")}
