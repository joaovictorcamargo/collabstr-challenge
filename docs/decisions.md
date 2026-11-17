# Decision log

| # | Decision | Why | Tradeoff |
|---|----------|-----|----------|
| 1 | Django 5.2 LTS, no database | Feature is stateless; fewer moving parts to deploy and secure. | Can't save briefs or join events to users yet. |
| 2 | Claude via official `anthropic` SDK, model `claude-opus-5-5`, effort `low`, configurable with `ANTHROPIC_MODEL` | Strong writing quality for a short structured task; `low` effort keeps latency reasonable. Model is one env var away from a cheaper/faster one. | Costlier per call than a small model; measure before downgrading. |
| 3 | Structured outputs (`output_config.format` json_schema) + server-side Pydantic validation | Guarantees parseable JSON and lets the UI render sections, edit and copy reliably. Double validation catches drift. | Schema changes need code changes on both ends. |
| 4 | Single non-streaming request, 40s timeout, SDK retries = 1 (worst case 80s < gunicorn 90s < browser 95s), server-side refusal fallback (`fallbacks: "default"`) | Simple, easy to test; skeleton loader covers the wait. Fallback keeps false-positive refusals from becoming errors. | No token streaming; perceived latency higher than a streamed UI. |
| 5 | Demo generator when no API key (`BRIEF_GENERATOR=auto`) | App and tests run without credentials; reviewers can click through. UI shows a "Demo content" badge so it's never mistaken for AI output. | Demo text is templated and less tailored. |
| 6 | Native radio inputs styled as DS option cards/pills | Free keyboard + screen-reader support, matches Collabstr's `ds-option-card` pattern. | Slightly more CSS than a `<select>`. |
| 7 | Chosen interaction: **edit in place + one-click "Copy brief"** | The brief's next stop is a campaign form or a creator message; copying edited text is the shortest path, and copy is a clean adoption signal. | Not a deep integration (would post straight into a Collabstr campaign in production). |
| 8 | Optional "What are you promoting?" field | Brand name alone forces the model to guess the product; one short optional field makes briefs much more specific. | One extra field beyond the four in the brief; kept optional. |
| 9 | Per-IP rate limit on Django cache (LocMem); client IP from `X-Forwarded-For` only for `TRUSTED_PROXY_COUNT` hops | Caps LLM spend and abuse with zero infra; a spoofed header can't mint fresh buckets. | Per-process counts; production would use Redis. Render hop count to confirm after deploy. |
| 13 | Anthropic 4xx → 503 + ERROR log, not 502 | Inputs are validated first, so a 4xx is our bug or config; telling users to "tweak inputs" would mislead. | — |
| 14 | Content-Security-Policy via a 20-line middleware | No inline scripts, so `script-src 'self'` is free hardening against XSS. | Google Fonts allowed explicitly. |
| 15 | Confirm before Regenerate discards edits | Edits are the user's work; losing them silently is the worst failure of the chosen interaction. | One native confirm dialog. |
| 10 | Events logged as JSON lines | Lets us compute the success metric today without new infra. | Needs a log drain/analytics tool to query. |
| 11 | No Playwright suite; browser QA done manually with a checklist | Keeps the slice small for the timebox; backend + API tests cover logic. | Frontend regressions not caught in CI. Listed as next step. |
| 12 | uv + Ruff + mypy (django-stubs) + pytest | Fast, standard Python tooling. | — |
