# Architecture

```
Browser (index.html + jQuery app.js)
   │  POST /api/briefs/  JSON + X-CSRFToken
   ▼
Django view  briefs.views.generate_brief
   ├─ rate limit (Django cache, per IP)
   ├─ BriefRequestForm  → validated, normalised inputs
   ├─ get_generator()   → AnthropicBriefGenerator | DemoBriefGenerator
   │      └─ Claude Messages API, structured JSON output (json_schema)
   ├─ Brief (Pydantic) validation of model output
   └─ JSON response + `brief_generated` log event
```

## Modules (`briefs/`)
| File | Responsibility |
|------|----------------|
| `forms.py` | Input validation and choice labels (single source for allowed values). |
| `schemas.py` | `Brief` Pydantic model; JSON schema handed to the LLM. |
| `prompts.py` | System prompt + user prompt builder (inputs wrapped in tags, treated as data). |
| `generators.py` | `BriefGenerator` protocol, `AnthropicBriefGenerator`, `DemoBriefGenerator`, `get_generator()`, typed errors. |
| `ratelimit.py` | Fixed-window per-IP counter on Django's cache. |
| `analytics.py` | `track(event, **props)` → structured JSON log line. |
| `views.py` | Page view, briefs API, events API. Maps errors to HTTP codes. |
| `templates/briefs/index.html` | Page markup. |
| `static/briefs/css/app.css` | Collabstr design tokens + components used here. |
| `static/briefs/js/app.js` | Form handling, state machine, rendering, edit + copy. |

## Key properties
- **Stateless.** No database; nothing user-entered is stored. Horizontal scaling is trivial.
- **Provider boundary.** The view only knows `BriefGenerator.generate(inputs) -> Brief`. Tests inject a fake;
  the demo generator lets the app run without a key and is clearly labelled in the UI.
- **Fail closed.** Any LLM error, refusal, truncation or schema mismatch becomes a typed error and a
  friendly message; the raw model output is never sent to the client unvalidated.
- **Safe rendering.** The frontend builds DOM with `.text()` only.
- **Config via env:** `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `ANTHROPIC_API_KEY`,
  `ANTHROPIC_MODEL`, `BRIEF_GENERATOR` (`auto`|`anthropic`|`demo`), `BRIEF_RATE_LIMIT_PER_MIN`.

## Deployment
Gunicorn + WhiteNoise for static files, `render.yaml` blueprint for one-click Render deploy.
Health check at `/healthz`.
