# AI Usage Log

The pre-work asks for honesty about AI tools, so here's an accurate account.

## Tool used

**Claude (Anthropic)** — used as a pair-programmer to scaffold the project,
generate boilerplate, and pressure-test design choices. I drove the
decisions and reviewed every file before committing it.

## How I used it

I used Claude in three modes:

### 1. Brainstorming the concept
I described the brief and asked for a shortlist of "team app" ideas with
brief pros/cons for each. We landed on a kudos board because it solves a
real new-team problem (lowering the social cost of giving recognition) and
is small enough to build well in a take-home timeframe.

### 2. Generating the initial scaffold
After agreeing on Flask + SQLite + server-rendered templates, I asked
Claude to produce a first cut of `app.py`, the Jinja template, the CSS,
and the front-end JS. I then read each file, edited the bits I wanted to
change, and verified the app runs.

### 3. Sanity-checking decisions
I asked Claude to argue against my choices ("why might someone pick
SQLAlchemy over raw sqlite3 here?", "what would per-user reaction de-dupe
require?") so the README's "decisions" section reflects real tradeoffs
rather than rationalizations.

## Representative prompts

These aren't verbatim transcripts but they capture the substance:

- *"I'm doing a take-home for a Jr SW Dev role. Brief: build a web app for a
  brand-new team to use. I want a Python/Flask stack and an idea that
  shows judgment, not just CRUD. Give me five options ranked by how well
  they fit the brief."*
- *"Generate a Flask app for a team kudos board with these features: post a
  kudos with from/to/category/message, see a feed, react with emojis,
  filter by category and recipient, and a leaderboard. Use stdlib sqlite3,
  not SQLAlchemy. Keep it in one file. Add comments that explain why
  decisions were made, not just what the code does."*
- *"Now the Jinja template and a clean CSS file — no framework, custom
  properties at the top so the theme is editable in one place."*
- *"Write the smallest amount of vanilla JS needed to make the reaction
  buttons update the count in place. Use optimistic UI with rollback on
  error."*
- *"Pretend you're the reviewer. Three tough questions you'd ask me about
  this code, and what good answers look like."*

## What I changed after Claude's output

- Tightened a few comments that were over-explaining obvious code
- Added the "no per-user reaction limit" note to the README — Claude's
  initial draft didn't flag it as a deliberate tradeoff, and I think a
  reviewer would specifically ask
- Adjusted the seed data so the example kudos messages sound like things a
  real teammate would say (specific actions, not generic praise)
- Hand-picked the category list down from a longer suggestion to five —
  fewer categories means less decision paralysis when posting

## What I did *not* delegate

- Choosing the app concept (I picked from the brainstormed list)
- Reading and approving every file before it landed
- Deciding the visual direction (warm cream + coral accent, soft cards)
- Running the app locally and clicking through every flow
- Writing this log

## Reviewer note

If you want to pressure-test which parts I actually understand, ask me
about: why server-rendered HTML over a SPA, why reaction counts are
recomputed instead of cached, what happens if the `react` POST fails
mid-flight, and what I'd do if the team grew to 100+ people.
