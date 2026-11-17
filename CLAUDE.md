# CLAUDE.md

AI Brief Generator for Collabstr: Django backend + jQuery single page + Claude for generation.

## Read first
- `docs/requirements.md` — requirement IDs (F*, T*, D*, AC*). Source of truth.
- `docs/spec.md` — API contract, `Brief` schema, UI states.
- `docs/architecture.md`, `docs/decisions.md` — structure and why.
- `docs/design-notes.md` — Collabstr design tokens; keep CSS on these tokens.
- `docs/tasks.md` — checklist; tick items as they land.

## Commands
```bash
uv sync                                   # install
uv run pytest                             # tests
uv run ruff check . && uv run ruff format --check .
uv run mypy .
DJANGO_DEBUG=true uv run python manage.py runserver   # demo mode without a key
uv run --env-file .env python manage.py runserver     # with .env
```

## Rules
- Change the spec (`docs/spec.md`) before changing the API or `Brief` schema; keep `briefs/schemas.py` in sync.
- Write or update a test before behaviour changes (TDD). Tests never call the real API — inject a fake generator.
- Render model output with jQuery `.text()` only. Never `.html()` with model or user data.
- Keep the API key server-side. Don't log raw user input beyond what `analytics.track` records.
- No database. If persistence is needed, record it in `docs/decisions.md` first.
- Keep it small: this is a timeboxed vertical slice.
