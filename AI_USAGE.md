# AI Usage Log

Here's how I used AI tools on this project — what I asked Claude to do, what I changed, and where I just trusted it.

## Tool used

**Claude (Anthropic)** — used as a pair-programmer for the build, and as a
guide when I got stuck pushing the project to GitHub.

## Where I'm coming from

I'm a beginner with Python, so I knew going in that I'd lean on Claude more
for the actual code than for the design. My goal here is to be upfront
about that rather than pretend otherwise. The thinking I put in went into
picking the app idea, framing *why* it was the right choice for this
brief, and making sure I could explain every part of the result.

## How I used it

### 1. Picking the app idea

I shared the recruiter's brief with Claude, told it I wanted to use Python,
and that my Python skills were beginner level. I asked for a shortlist of
team app ideas with pros and cons.

I picked the kudos board. What sold me on it: the category system
(Teamwork, Innovation, Helpfulness, Ownership, Learning) doubles as a
soft way to surface each teammate's strengths over time. If you're a new
team member trying to figure out who's good at what, the leaderboard and
category filters basically answer "who has been recognized for X" — so
it's both a recognition tool and a "who do I go to for help with this"
tool. That dual purpose is what made it feel right for the "team is still
getting to know each other" framing in the brief.

### 2. Generating the code

After we agreed on Flask + SQLite + server-rendered templates, I asked
Claude to produce the full app — `app.py`, the Jinja template, the CSS,
and the front-end JS. I specifically asked for comments that explain *why*
decisions were made, not just *what* the code does, so that when I read it
back I'd actually learn from it.

I'm not going to claim I rewrote big chunks — I didn't. I read through
every file, asked Claude to walk me through anything I didn't follow, and
kept the code largely as written. The comments and the "Decisions and
tradeoffs" section in the README are what I leaned on to build a mental
model of why the code is shaped the way it is.

### 3. GitHub push troubleshooting

I've uploaded individual files to GitHub before but hadn't pushed a whole
project folder from the command line. I followed a YouTube tutorial to get
started and ran into the credentials wall: macOS Keychain was caching old
credentials and silently re-sending them, so even after I generated a
fresh Personal Access Token my pushes kept failing with
"Authentication failed."

Claude walked me through, in order:

- Generating a Personal Access Token with the right `repo` scope
- Deleting the stale `github.com` entry from Keychain Access
- Putting the token directly in the remote URL as a workaround when
  pasting at the password prompt wasn't behaving
- Cleaning up afterwards: removing the token from the local git config
  and revoking the exposed token on GitHub

It took several tries. I'm flagging that because the brief asks for
honesty about *how* I work through problems, not just whether I solved
them.

## Representative prompts

Paraphrased from what I actually sent:

- *"I'm doing pre-work for a Jr SW Dev role. Brief: build a web app for a
  brand-new team. I want to use Python and my Python skills are beginner
  level. Give me team app ideas with pros and cons."*
- *"Build a Flask + SQLite kudos board with from/to/category/message, a
  feed, emoji reactions, a leaderboard, and category filters. Add comments
  explaining why decisions were made, not just what the code does."*
- *"Write a README that covers setup, how it works, and the decisions
  made — written so I can speak to each one in an interview."*
- *"Help me push this folder to GitHub from the command line — I've only
  uploaded individual files before."*
- *"macOS Keychain keeps rejecting my GitHub credentials even with a fresh
  token. Help me debug step by step."*

## What I did *not* delegate

- Picking the app idea from the shortlist Claude brainstormed
- Reading the README and code so I can explain the decisions out loud
- Running the app locally and clicking through every flow
- Writing this log (Claude helped me shape it; the substance is mine)

## What I'd want a reviewer to know

I'm being upfront: I'm a beginner with Python and Claude wrote most of the
code. Where I'd push back on calling this a "tutorial follow," though, is
that I picked the idea, framed *why* it fits the brief (the
strengths-surfacing angle), made the call on the stack, and worked through
the GitHub auth issues end-to-end instead of giving up. I treated Claude
as a senior engineer pair — describe the goal and constraints, get a
draft, read it, ask questions until I understand it, then commit. That's a
workflow I plan to keep using as I level up.

If you want to pressure-test what I actually understand, ask me about:
why a kudos board fits a brand-new team, why server-rendered HTML over a
SPA, what each of the three database tables is for, what happens if a
reaction `POST` fails mid-flight, and what I'd change if 100 people used
this.
