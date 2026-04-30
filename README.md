# Team Kudos Board

A small web app for a brand-new team to publicly recognize each other.
Pick a teammate, pick a category, write a short message — and react to other
people's kudos with an emoji. A leaderboard surfaces who's been recognized
most, and category filters make it easy to skim recent recognitions.

Built as the pre-work for the Junior Software Developer (RDO) role.

---

## Why this app

The brief says the team is brand new and needs a way to connect. New teams
have a chicken-and-egg problem with appreciation: people *want* to recognize
good work, but doing it publicly feels awkward when no one has gone first.
A kudos board solves that by making recognition lightweight (a short form),
visible (a public feed), and a little fun (emoji reactions, a leaderboard).

It also doubles as a low-effort way to learn what each teammate values —
when someone says "thanks for the deploy help," you learn how that person
shows up for the team.

## What's in the box

- A feed of kudos with category badges and emoji reactions
- A "send a kudos" form with from/to/category/message
- Filtering by category and by recipient
- A "Top recognized" leaderboard
- A `GET /api/kudos` JSON endpoint and `POST /api/kudos/<id>/react` for the
  reaction buttons (so the page never has to reload to update a count)
- Sample teammates and a few starter kudos so the empty state isn't empty

## Quick start

Requires Python 3.10+ (uses `str | None` type hints and the stdlib only
beyond Flask itself).

```bash
# 1. Get the code
git clone <your-fork-url> team-kudos-board
cd team-kudos-board

# 2. (Recommended) create a virtual environment
python3 -m venv .venv
source .venv/bin/activate            # macOS / Linux
# .venv\Scripts\activate             # Windows

# 3. Install dependencies (just Flask)
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Then open <http://127.0.0.1:5000> in a browser.

The first time you run it, `kudos.db` is created in the project folder and
seeded with sample teammates and three example kudos. Delete `kudos.db`
to reset.

## Project layout

```
team-kudos-board/
├── app.py                # Flask app: routes, DB helpers, schema + seed data
├── requirements.txt      # Just Flask
├── README.md             # You are here
├── AI_USAGE.md           # How AI tools were used and reviewed
├── .gitignore
├── static/
│   ├── styles.css        # All styling, no preprocessor
│   └── app.js            # Vanilla JS — handles emoji reactions
└── templates/
    └── index.html        # The single page (server-rendered Jinja)
```

## How it works

### Backend

`app.py` is intentionally a single file — at this size, splitting into
`models.py`, `routes.py`, `db.py` etc. costs more in navigation than it
saves in clarity. The file has three labeled sections: app/setup, data
access, and routes.

The database is SQLite, accessed via the stdlib `sqlite3` module. Three
tables:

| Table       | Purpose                                          |
|-------------|--------------------------------------------------|
| `teammates` | Names + an emoji avatar for the dropdown / leaderboard |
| `kudos`     | One row per kudos: from, to, category, message, timestamp |
| `reactions` | One row per reaction click, linked to a kudos via FK |

Reaction counts are computed from the `reactions` table at read time using
correlated subqueries in the feed query. That means there's exactly one
source of truth — no cached counter that can drift out of sync with the
underlying rows.

### Frontend

`templates/index.html` is rendered server-side, so a user with JavaScript
disabled can still browse, filter, and post kudos. The form posts a normal
`application/x-www-form-urlencoded` body and the server responds with a
303-style redirect after writing.

The only JavaScript is `static/app.js`, which intercepts clicks on
reaction buttons and sends them to `POST /api/kudos/<id>/react` so the count
updates in place. It uses an *optimistic UI* update — the count bumps
immediately, and we reconcile with the server's response when it arrives.
If the request fails, the count rolls back. This is a pattern worth knowing
because it makes the UI feel instant on slow networks, and you'll see it
in many production codebases.

## Decisions and tradeoffs

These are the choices a reviewer might ask about — answered up front.

**Flask over FastAPI / Django.** FastAPI's superpower is async + automatic
OpenAPI docs, neither of which matter here. Django would bring an admin,
ORM, and migrations system that this app doesn't need. Flask hits the
sweet spot of "small enough that you can read every line, big enough to
demonstrate real patterns (request scopes, blueprints, Jinja)."

**Stdlib `sqlite3` over SQLAlchemy.** SQLAlchemy is great when you have
five+ tables, complex relationships, or migrations. With three tables
and no schema evolution, raw SQL is shorter, faster to read, and lets a
reviewer verify exactly what hits the database.

**No authentication.** The brief is "a tool for your team." Adding login
would multiply the surface area (password storage, sessions, "forgot
password," CSRF on more flows) without adding to what's interesting about
the app. The "from" field is a dropdown — like signing the front of a
greeting card. If this graduated to production, I'd put it behind SSO and
add a per-user reaction de-dupe.

**Server-rendered HTML + sprinkles of JS.** No SPA framework means no build
step, no `node_modules`, no bundler config — the project clones and runs
in one command. The reaction interaction *is* the place where a vanilla
SPA-style update makes sense, so that one piece is JS-driven. Every other
state change is a normal form post.

**No per-user reaction limit.** Right now anyone can click the clap button
ten times and the count goes up ten times. For a small trusted team this
feels playful; if abused, we'd add session-scoped one-vote-per-user.

**Categories are hard-coded.** Five categories cover most kudos people
actually want to give and avoids the "what category is this?" decision
paralysis you get with twenty options. Easy to extend in code.

## What I'd add next

Given more time, in priority order:

1. **A small test suite** — pytest + Flask's test client over the form
   POST + the react endpoint. The API is small enough that 5–10 tests
   would cover the meaningful paths.
2. **Reaction de-dupe** — sessions or a cookie-based identity so each
   visitor counts as one vote per emoji per kudos.
3. **Pagination / infinite scroll** for the feed once the team starts
   leaving more than 50 kudos.
4. **Admin-side teammate management** — a page to add/remove teammates
   without editing seed data.
5. **Slack notification on new kudos** — a webhook so people see kudos
   even when they aren't on the page.

## License

MIT — feel free to fork.
