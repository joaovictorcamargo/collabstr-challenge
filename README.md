# AI Brief Generator for Collabstr

A brand gives four inputs (brand, platform, goal, tone), plus an optional product note. In about
15 seconds it gets back an editable campaign brief, content angles, and creator selection criteria,
and can copy the result straight into a campaign or a message to creators.

**Live demo:** _add URL after deploy_ · **Loom:** _add URL_ · **Stack:** Django 5.2 · jQuery 3.7 · Claude (Anthropic API)

---

## 1. Lite PRD

- **Problem:** Brands know their product and a rough goal ("more TikTok buzz") but not how to write a brief creators can act on. A vague brief means fewer good applicants, more back-and-forth in chat, and content that misses the goal. The blank page is the blocker.
- **Intended outcome:** In under a minute, the brand goes from a few choices to a structured first draft it trusts enough to edit and use.
- **Primary success metric: brief adoption rate** = `brief_copied / brief_generated`. Copying is the clearest sign the draft was good enough to carry into the next step. Both events are instrumented (see [Validation](#4-validation-and-iteration)).
  Guardrails: error rate, p95 latency, regenerate rate (a high rate means weak first drafts).
- **Scope:** one page, four required inputs + one optional "What are you promoting?" field, one LLM call returning structured JSON, edit in place, copy, regenerate, loading/success/error states.
  **Out of scope:** saving briefs, accounts, pushing into Collabstr's real campaign flow, budget/timeline, matching against real creators.
- **Assumptions:** brands want an editable starting point, not a final document; the next step is pasting into a campaign form or a creator message, so plain-text copy is the right hand-off; one optional product field is worth it, because a brand name alone forces the model to guess what is being sold.

## 2. Technical approach

```
Browser (index.html + app.js, jQuery)
  │ POST /api/briefs/ (JSON, X-CSRFToken)
  ▼
Django view ─ rate limit (per IP) ─ BriefRequestForm (validation)
  │
  ├─ get_generator() ─► AnthropicBriefGenerator ─► Claude Messages API (json_schema output)
  │                  └► DemoBriefGenerator (no API key: templated, labelled "Demo content")
  ├─ Brief (Pydantic) validates the model output
  └─ JSON response + `brief_generated` event (JSON log line)
```

- **Frontend ↔ Django:** Django renders the page; jQuery posts JSON to `/api/briefs/` and renders the result. There is one endpoint and the API contract is in [docs/spec.md](docs/spec.md). The form posts JSON rather than a page reload, so the inputs stay put during loading, errors, and regeneration.
- **Django ↔ LLM:** one non-streaming call through the official `anthropic` SDK. **Structured outputs** (`output_config.format: json_schema`) make the reply always parse, and a **Pydantic `Brief` model** checks it again on our side (counts, empty strings, extra keys) before anything reaches the browser.
- **Model:** `claude-opus-5-5` at `effort: "low"`, set by `ANTHROPIC_MODEL`. I chose writing quality first for a short task. The model is one env var, so a cheaper or faster model can be A/B tested against adoption rate rather than guessed.
- **Prompting:** the system prompt holds platform rules (Reels vs. native TikTok vs. UGC deliverables and usage rights), goal rules (each with a measurable signal), tone, and size limits. User inputs arrive in XML tags and are HTML-escaped, so they can't close a tag. The model is told to treat them as data, never invent prices or claims (it uses `[placeholders]` instead), and never use protected traits in creator criteria.
- **Reliability:** 40s timeout plus 1 SDK retry (browser waits 95s, gunicorn 90s, so the client never gives up first); `stop_reason` is checked (a truncated or refused reply is an error, never shown half-done); server-side **refusal fallback** (`fallbacks: "default"`), so a false-positive safety decline re-runs on another model instead of failing; unusable output becomes a 502, while outages and config errors (4xx from Anthropic, logged at ERROR) become a 503, each with a plain-language message; gunicorn uses threaded workers because the work is I/O-bound.
- **Safety & security:** the API key stays on the server; CSRF on every POST; per-IP rate limit (10/min) caps spend and abuse; input length limits and control-character stripping; model output is rendered only with jQuery `.text()` (no HTML injection); `X-Forwarded-For` is only trusted for the configured number of proxy hops (`TRUSTED_PROXY_COUNT`), so a spoofed header can't dodge the limit; production settings set a Content-Security-Policy (`script-src 'self'`), HSTS, secure cookies, `nosniff`, and `X-Frame-Options: DENY`; no user data is stored.
- **Implemented vs. production:**

  | Now | For production |
  |---|---|
  | Logs as analytics sink | Send events to the existing analytics pipeline (Segment/Amplitude), join to campaign creation |
  | LocMem rate limit (per process) | Redis-backed limits per account plus a daily spend cap |
  | One blocking request (~16s measured) | Stream sections as they generate; cache by input hash |
  | Copy to clipboard | "Use this brief" that pre-fills Collabstr's campaign form |
  | Demo generator when no key | Remove, or keep only for previews |
  | Unit + API tests, manual browser QA | Playwright E2E in CI, a small eval set of briefs scored by a rubric and an LLM judge |

## 3. Design rationale

- **One screen, two panes:** form on the left (sticky), brief on the right. The brand sees the inputs and output together, so changing one choice and regenerating is a single click. On mobile it stacks and scrolls to the result.
- **Option cards and pills instead of dropdowns:** all choices are visible, one click each, and goals carry a one-line explanation ("Drive clicks, sign-ups or sales"), which helps first-time brands. They are native radio buttons under the hood, so arrow keys and screen readers work for free.
- **The one small interaction: edit in place + "Copy brief."** Every line of the result is directly editable, and Copy exports the *edited* version as clean, labelled plain text. Why this one: the brief's next stop is a campaign form or a creator DM, so copying is the shortest path into the existing workflow. It is also the most honest signal for the success metric. I chose it over export to PDF/Docs (more steps) and per-section regeneration (more scope, harder to measure).
- **States:** an empty state says what you'll get; loading uses a skeleton plus "can take up to 30 seconds" (honest about the wait) and keeps focus on the result; errors keep every input, are announced, and move focus to "Try again"; regenerating after editing asks before discarding the edits; success announces itself to screen readers and moves focus to the result.
- **Design system:** tokens taken from collabstr.com/design-system and kept under the same names (`--gray-*`, `--pink-*`, `--color-text-*`, `--shadow-md`, radii, durations), plus the DS component patterns `ds-btn` (dark primary), `ds-option-card`, `ds-tag`, `ds-badge`, `ds-alert`, `ds-toast`, `ds-skeleton`, with Inter and Lucide-style icons. **Deviation:** the DS brand pinks measure 2.8–3.0:1 for 12px text, so small pink text uses a darker pink to meet WCAG AA ([details](docs/design-notes.md)).

## 4. Validation and iteration

**What was tested**
- 104 automated tests (`uv run pytest`): form validation, the `Brief` schema and its strictness for structured outputs, prompt building (including tag-injection escaping), every generator failure mode (refusal, truncation, bad JSON, fewer than 3 angles or criteria, timeout, 429, 5xx, 400/401/404, unexpected SDK errors), API status codes, CSRF enforcement, rate limiting (including spoofed and rotated `X-Forwarded-For`), non-string JSON values, CSP header, and events. The Claude client is faked; tests never call the API.
- Ruff + mypy (strict) clean; CI workflow runs all of it plus `collectstatic` and `check --deploy`.
- Browser QA (built-in browser): validation messages and focus, keyboard-only selection, loading lock (no double submit), success render, editing and copy output, the real error path (an invalid API key hits Anthropic, gets 401, and the UI shows a friendly 503 message with inputs kept), 375px layout with no horizontal scroll, a scripted WCAG contrast check, labels, heading order.
- Production smoke test: gunicorn + WhiteNoise serving hashed static files, `/healthz`, security headers.
- **Live Claude check** (scripted, 4 input combinations plus a prompt-injection probe): all returned valid briefs in 15–20s, using about 1.7k input and 1.3–1.5k output tokens, **≈ $0.035 per brief** on Opus 5.5. Each was checked for brand and platform mentions, ≥3 angles and criteria, no invented prices, usage rights on UGC briefs, and a conversion signal on Conversions briefs. The injection note ("ignore all previous instructions…") was ignored.
- **What the live run changed:** the model once explained the placeholder rule inside a brief and once titled a campaign "…On Us…" (implying a free offer), so the prompt now forbids both. Real briefs carry up to ~17 `[placeholders]`, so the UI now shows how many are left to fill in before sharing, updating as you edit.

**What I'd measure**
- Adoption rate (copied ÷ generated) by platform/goal/tone; edit rate and how much gets edited (heavy edits mean weak drafts); regenerate rate; p95 latency; error rate by code.
- Downstream: share of new campaigns posted with a generated brief, and applications per campaign versus campaigns without one.
- Qualitative: a thumbs up/down on the brief plus 5 brand interviews about what they changed before sending.

**What I'd improve next**
1. "Use this brief" → pre-fill Collabstr's campaign form (deeper hand-off, cleaner metric). Pre-fill known placeholders ([discount code], [link]) from the brand's account.
2. Streaming output to cut perceived latency.
3. An eval set of ~30 input combinations scored against a rubric before any model or prompt change.
4. Optional inputs (budget, timeline, audience) only if the data shows briefs being edited for those reasons.

## 5. Setup and run

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 automatically).

```bash
uv sync
cp .env.example .env               # optional: add ANTHROPIC_API_KEY
uv run --env-file .env python manage.py runserver
# open http://127.0.0.1:8000
```
Without an API key the app runs in **demo mode**: templated briefs marked "Demo content" in the UI.

```bash
uv run pytest                       # tests
uv run ruff check . && uv run ruff format --check .
uv run mypy .
```

**Deploy (Render, free tier):** push to GitHub → Render → New → Blueprint → select the repo (`render.yaml`) → set `ANTHROPIC_API_KEY` in the dashboard. A `Procfile` is included for Railway or Heroku.

| Env var | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | — (required when not DEBUG) | Django secret |
| `DJANGO_DEBUG` | `false` | Dev mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Plus Render's hostname automatically |
| `ANTHROPIC_API_KEY` | empty | Enables Claude |
| `ANTHROPIC_MODEL` | `claude-opus-5-5` | Model id |
| `BRIEF_GENERATOR` | `auto` | `auto` / `anthropic` / `demo` |
| `BRIEF_RATE_LIMIT_PER_MIN` | `10` | Per-IP limit |
| `TRUSTED_PROXY_COUNT` | `0` | Proxies appending to `X-Forwarded-For` (Render: `1`) |

## 6. AI tools

- Built with Claude Code (Claude Opus 5.5), working from written specs first ([docs/](docs/): requirements, PRD, spec, architecture, decisions) and tests before code.
- Used for: reading the design system page and extracting its tokens, drafting the specs, writing the code and tests, browser QA, and an independent review pass by a separate agent. Its findings (4xx error mapping, minimum angle and criteria counts, `X-Forwarded-For` trust, regenerate state bugs, focus and ARIA issues, CSP) were fixed with tests and re-checked in the browser.
- Checked by running, not by trusting: the test suite, lint/types, the production build, and browser checks listed above; the jQuery SRI hash was compared with the official CDN's; the SDK parameters were checked against the installed `anthropic` package's signatures.
- _Candidate: add a line on what you personally reviewed before submitting._

## 7. Tradeoffs and not done in the timebox

- No browser E2E suite: browser QA was manual, with backend logic covered by tests.
- In-memory rate limiting is per process; fine for one small instance, not for a fleet. `TRUSTED_PROXY_COUNT=1` for Render is an assumption about its proxy chain; confirm against the real headers after the first deploy.
- Analytics are log lines; computing the metric needs a log drain or analytics tool.
- One optional input added beyond the brief's four, on purpose (see PRD).

## Project layout

```
config/            settings, urls, wsgi
briefs/
  forms.py         input validation
  schemas.py       Brief model + JSON schema for the LLM
  prompts.py       system prompt + user prompt builder
  generators.py    Claude + demo generators, typed errors
  views.py         page, /api/briefs/, /api/events/, /healthz
  ratelimit.py     per-IP fixed window
  analytics.py     JSON-line events
  templates/ static/
  tests/
docs/              requirements, PRD, spec, architecture, decisions, design notes, tasks, demo script
```
