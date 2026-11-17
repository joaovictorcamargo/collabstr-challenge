# Implementation checklist

- [x] Discovery: requirements, design-system tokens, Claude API docs (`docs/requirements.md`, `docs/design-notes.md`)
- [x] Specs: PRD, spec, architecture, decisions
- [x] Project setup: uv, Django, Ruff, mypy, pytest, git
- [x] Tests first: form validation, schema, prompt builder, generators, views (F2–F8, F11, F12, AC2, AC4, AC7, AC8)
- [x] Backend: forms, schemas, prompts, generators, rate limit, analytics, views, health check
- [x] Frontend: template, DS-based CSS, jQuery app (states, edit, copy, regenerate, events)
- [x] QA: tests, lint, types, browser flow, 375px layout, keyboard + contrast pass, production build (`collectstatic`, `check --deploy`, gunicorn smoke test)
- [x] Independent code review and fixes (see decisions 13–15)
- [x] Delivery: README write-up, deploy config (Render/Procfile), CI, demo script
- [ ] Owner: set `ANTHROPIC_API_KEY`, run one live generation, deploy, push public repo, record Loom, email links

## Requirement verification

| ID | Status | Evidence |
|----|--------|----------|
| F1 | Done | Single page `GET /` |
| F2–F5 | Done | Form fields + `BriefRequestForm`; `test_forms.py` |
| F6–F8 | Done | `Brief` schema; rendered sections; `test_schemas.py`, `test_views.py` |
| F9, F10 | Done | Edit in place + Copy brief; verified in browser (copied text includes edits) |
| F11 | Done | Empty/loading/success/error states; verified in browser incl. real 401 path |
| F12 | Done (code) | `AnthropicBriefGenerator`; live success not run here (no API key) |
| T1, T2 | Done | Django 5.2; HTML/CSS + jQuery 3.7.1 |
| T3 | Done | DS tokens/components; deviations documented in `design-notes.md` |
| T4, T5 | Done | No DB, typed errors, rate limit, CSP; 101 tests, Ruff, mypy strict, CI |
| D1–D7 | Done | `README.md` sections 1–7 |
| AC1 | Done | ≥3 angles/criteria enforced server-side |
| AC2 | Done | Field errors client + server, first invalid field focused |
| AC3 | Done | Button disabled, inputs locked, `state.pending` guard |
| AC4 | Done | 502/503 with friendly copy, inputs kept, Try again |
| AC5 | Done | Editable sections, one-click copy, toast |
| AC6 | Done | Keyboard, labels, live region, focus management, 375px, contrast ≥4.5:1 |
| AC7 | Done | `.text()` only; reviewed |
| AC8 | Done | Key server-side, CSRF test, rate-limit tests |
| X1–X3 | Owner | Needs GitHub account, hosting account + API key, Loom |
