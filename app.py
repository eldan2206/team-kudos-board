"""
Team Kudos Board - Flask application.

A small internal web app where teammates publicly recognize each other.
Built for the Jr Software Developer pre-work challenge.

Design notes:
- Single-file Flask app to keep the project easy to read top-to-bottom.
- Uses the stdlib `sqlite3` module rather than SQLAlchemy. The schema is tiny
  and avoiding an ORM means every database call is visible and explainable.
- Server-rendered Jinja templates for the main view; small fetch() calls for
  the reaction button so reactions feel snappy without a full page reload.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, g, jsonify, redirect, render_template, request, url_for

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "kudos.db"

# Categories are intentionally hard-coded. In a larger app these would live in
# the database, but for a team tool a fixed taxonomy is easier to reason about
# and easier for teammates to use consistently.
CATEGORIES = [
    ("teamwork", "Teamwork"),
    ("innovation", "Innovation"),
    ("helpfulness", "Helpfulness"),
    ("ownership", "Ownership"),
    ("learning", "Learning"),
]
CATEGORY_KEYS = {key for key, _ in CATEGORIES}

# Reaction emojis. Kept short so the UI doesn't become a sticker drawer.
REACTIONS = ["clap", "party", "fire", "heart"]
REACTION_EMOJI = {
    "clap": "\U0001F44F",   # clapping hands
    "party": "\U0001F389",  # party popper
    "fire": "\U0001F525",   # fire
    "heart": "❤️",  # red heart
}

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Return a request-scoped sqlite connection.

    Flask's `g` object lives for the duration of a single request, so each
    request gets its own connection and we don't have to worry about thread
    safety with sqlite.
    """
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # Foreign keys are off by default in sqlite. Turn them on so the
        # `kudos_id` reference in `reactions` is actually enforced.
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Create tables and seed initial data if the DB is empty."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS teammates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                emoji TEXT NOT NULL DEFAULT '\U0001F642'
            );

            CREATE TABLE IF NOT EXISTS kudos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_name TEXT NOT NULL,
                to_name TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kudos_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                FOREIGN KEY (kudos_id) REFERENCES kudos (id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_kudos_to ON kudos(to_name);
            CREATE INDEX IF NOT EXISTS idx_kudos_category ON kudos(category);
            CREATE INDEX IF NOT EXISTS idx_reactions_kudos ON reactions(kudos_id);
            """
        )

        # Seed sample teammates only if the table is empty. This keeps
        # `init_db()` idempotent and safe to call on every startup.
        existing = conn.execute("SELECT COUNT(*) AS n FROM teammates").fetchone()["n"]
        if existing == 0:
            sample_team = [
                ("Avery", "\U0001F9D1‍\U0001F4BB"),  # technologist
                ("Bao", "\U0001F9D1‍\U0001F3A8"),    # artist
                ("Cam", "\U0001F9D1‍\U0001F52C"),    # scientist
                ("Devi", "\U0001F9D1‍\U0001F3EB"),   # teacher
                ("Eli", "\U0001F9D1‍\U0001F680"),    # astronaut
                ("Frankie", "\U0001F9D1‍\U0001F373"),  # cook
            ]
            conn.executemany(
                "INSERT INTO teammates (name, emoji) VALUES (?, ?)",
                sample_team,
            )

            # Seed a couple of example kudos so the empty state isn't, well, empty.
            now = datetime.now(timezone.utc).isoformat()
            seed_kudos = [
                ("Avery", "Bao", "innovation",
                 "The new onboarding doc layout you proposed is so much clearer. Saved me an hour today.",
                 now),
                ("Cam", "Devi", "helpfulness",
                 "Thanks for jumping into the deploy issue at 7am. You absolutely did not have to do that.",
                 now),
                ("Frankie", "Eli", "ownership",
                 "Loved how you owned the post-mortem end-to-end and turned it into action items.",
                 now),
            ]
            conn.executemany(
                "INSERT INTO kudos (from_name, to_name, category, message, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                seed_kudos,
            )
    conn.close()


# ---------------------------------------------------------------------------
# Data access functions
#
# These are kept as plain functions (not a class) because the app is small and
# the call sites are few. If the project grew I'd move these into a
# `repository.py` module.
# ---------------------------------------------------------------------------

def fetch_teammates() -> list[sqlite3.Row]:
    return get_db().execute(
        "SELECT name, emoji FROM teammates ORDER BY name"
    ).fetchall()


def fetch_kudos(category: str | None = None, recipient: str | None = None) -> list[dict]:
    """Return kudos rows joined with their reaction counts.

    Filters are applied at the SQL level so we don't pull every row into Python
    just to throw most of them away.
    """
    sql = """
        SELECT
            k.id, k.from_name, k.to_name, k.category, k.message, k.created_at,
            (SELECT COUNT(*) FROM reactions r WHERE r.kudos_id = k.id AND r.kind = 'clap')  AS clap,
            (SELECT COUNT(*) FROM reactions r WHERE r.kudos_id = k.id AND r.kind = 'party') AS party,
            (SELECT COUNT(*) FROM reactions r WHERE r.kudos_id = k.id AND r.kind = 'fire')  AS fire,
            (SELECT COUNT(*) FROM reactions r WHERE r.kudos_id = k.id AND r.kind = 'heart') AS heart
        FROM kudos k
        WHERE 1=1
    """
    params: list[str] = []
    if category and category in CATEGORY_KEYS:
        sql += " AND k.category = ?"
        params.append(category)
    if recipient:
        sql += " AND k.to_name = ?"
        params.append(recipient)
    sql += " ORDER BY k.id DESC"

    rows = get_db().execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def fetch_leaderboard(limit: int = 5) -> list[dict]:
    """Top recipients by kudos count over all time."""
    rows = get_db().execute(
        """
        SELECT k.to_name AS name, COUNT(*) AS kudos_count, t.emoji AS emoji
        FROM kudos k
        LEFT JOIN teammates t ON t.name = k.to_name
        GROUP BY k.to_name
        ORDER BY kudos_count DESC, k.to_name ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    category = request.args.get("category") or None
    recipient = request.args.get("to") or None
    kudos = fetch_kudos(category=category, recipient=recipient)
    return render_template(
        "index.html",
        kudos=kudos,
        teammates=fetch_teammates(),
        leaderboard=fetch_leaderboard(),
        categories=CATEGORIES,
        active_category=category,
        active_recipient=recipient,
        reactions=REACTIONS,
        reaction_emoji=REACTION_EMOJI,
    )


@app.route("/kudos", methods=["POST"])
def create_kudos():
    """Handle the form submission to create a new kudos."""
    from_name = (request.form.get("from_name") or "").strip()
    to_name = (request.form.get("to_name") or "").strip()
    category = (request.form.get("category") or "").strip()
    message = (request.form.get("message") or "").strip()

    # Server-side validation. The form has matching constraints client-side
    # but we never trust the client.
    errors = []
    if not from_name:
        errors.append("Pick who the kudos is from.")
    if not to_name:
        errors.append("Pick who the kudos is for.")
    if from_name and to_name and from_name == to_name:
        errors.append("Kudos to yourself doesn't quite work — pick a teammate.")
    if category not in CATEGORY_KEYS:
        errors.append("Pick a valid category.")
    if not message:
        errors.append("Add a short message.")
    elif len(message) > 500:
        errors.append("Message is too long (max 500 characters).")

    if errors:
        # Keep it simple — we just abort with a 400 and the error text. A
        # production app would re-render the form with field-level errors.
        return ("\n".join(errors), 400)

    db = get_db()
    with db:
        db.execute(
            "INSERT INTO kudos (from_name, to_name, category, message, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (from_name, to_name, category, message, datetime.now(timezone.utc).isoformat()),
        )
    return redirect(url_for("index"))


@app.route("/api/kudos/<int:kudos_id>/react", methods=["POST"])
def react(kudos_id: int):
    """Add a reaction to a kudos and return the updated counts.

    Returning JSON lets the front-end update the count in place without a
    full page reload. There's intentionally no per-user dedupe — anyone can
    keep clicking and the counter goes up. For a small trusted team this
    feels playful; for a larger app you'd want sessions and one-vote-per-user.
    """
    payload = request.get_json(silent=True) or {}
    kind = payload.get("kind")
    if kind not in REACTIONS:
        abort(400, description="Unknown reaction kind.")

    db = get_db()
    # Confirm the kudos exists so we return a clean 404 instead of silently
    # inserting an orphan row (foreign keys would catch it but the error is uglier).
    exists = db.execute("SELECT 1 FROM kudos WHERE id = ?", (kudos_id,)).fetchone()
    if not exists:
        abort(404)

    with db:
        db.execute(
            "INSERT INTO reactions (kudos_id, kind) VALUES (?, ?)",
            (kudos_id, kind),
        )

    counts = db.execute(
        """
        SELECT
            SUM(CASE WHEN kind = 'clap'  THEN 1 ELSE 0 END) AS clap,
            SUM(CASE WHEN kind = 'party' THEN 1 ELSE 0 END) AS party,
            SUM(CASE WHEN kind = 'fire'  THEN 1 ELSE 0 END) AS fire,
            SUM(CASE WHEN kind = 'heart' THEN 1 ELSE 0 END) AS heart
        FROM reactions WHERE kudos_id = ?
        """,
        (kudos_id,),
    ).fetchone()
    return jsonify({k: counts[k] or 0 for k in REACTIONS})


@app.route("/api/kudos")
def api_kudos():
    """JSON list of kudos. Handy for testing and for anyone who wants to
    point a different front-end at the same data."""
    return jsonify(fetch_kudos(
        category=request.args.get("category"),
        recipient=request.args.get("to"),
    ))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

# Initialize the database when this module is imported. gunicorn (used in
   # production) imports this file but doesn't execute the __main__ block, so
   # the call has to live here. init_db() is idempotent — safe to call on
   # every startup.
   init_db()

   if __name__ == "__main__":
       # debug=True is fine for local dev; gunicorn ignores this block.
       app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)
