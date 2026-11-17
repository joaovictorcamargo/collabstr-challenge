# Functional & API Spec

## Page: `GET /`
One page, two areas:
1. **Form card** — Brand name (text, required, 2–60 chars), Platform (option pills: Instagram /
   TikTok / UGC), Goal (option cards: Awareness / Conversions / Content Assets), Tone (option pills:
   Professional / Friendly / Playful), optional "What are you promoting?" (textarea, max 280 chars,
   live counter). Primary button "Generate brief".
2. **Result area** — empty state → loading skeleton → result card or error alert.

Choice inputs are native radio buttons styled as Collabstr option cards, so keyboard (arrow keys),
screen readers and no-JS form semantics work without extra code. Defaults: none selected for
platform/goal/tone, so the brand makes a conscious choice; inline errors if missing.

## API: `POST /api/briefs/`
Request (`application/json`, CSRF header `X-CSRFToken` required):
```json
{"brand_name": "Glow Lab", "platform": "tiktok", "goal": "awareness",
 "tone": "playful", "product_note": "new vitamin C serum"}
```
`platform ∈ {instagram, tiktok, ugc}`, `goal ∈ {awareness, conversions, content_assets}`,
`tone ∈ {professional, friendly, playful}`; `product_note` optional.

Responses:
| Status | Body | When |
|--------|------|------|
| 200 | `{"brief": Brief, "meta": {"source": "anthropic"\|"demo", "request_id": str}}` | Success |
| 400 | `{"error": {"code": "invalid_input", "message": str, "fields": {name: [msg]}}}` | Validation failed / malformed JSON |
| 405 | Django default | Not POST |
| 429 | `{"error": {"code": "rate_limited", "message": str}}` | > N requests/min per client |
| 502 | `{"error": {"code": "generation_failed", "message": str}}` | LLM refused or returned invalid output |
| 503 | `{"error": {"code": "generation_unavailable", "message": str}}` | LLM timeout/overloaded/not configured |

`Brief` schema (also the LLM's JSON schema):
```
campaign_title: str
summary: str                         # 2–3 sentences
objective: str                       # tied to goal, with a measurable signal
key_message: str
deliverables: [str] (2–4)            # platform-specific formats
dos: [str] (3–5)
donts: [str] (2–4)
content_angles: [{title: str, hook: str, description: str}] (3–5)
creator_criteria: [{criterion: str, detail: str}] (3–6)
```
Server validates model output against this schema (Pydantic) before returning it; anything else is a 502.

## API: `POST /api/events/`
`{"event": "brief_copied"|"brief_edited"|"brief_regenerated", "request_id": str}` → 204.
Logged as one JSON line for analytics; unknown events → 400. Rate-limited and CSRF-protected.
`brief_generated` is logged server-side by the briefs endpoint.

## UI states
- **Empty:** short explanation of what you'll get.
- **Loading:** button disabled with spinner + "Generating…", skeleton card, live region announces
  "Generating your brief". Form inputs locked to avoid double submits.
- **Success:** result card, focus moves to its heading, live region announces completion.
  Sections editable in place; "Copy brief" (primary), "Regenerate" (secondary), demo badge when the
  demo generator served the result.
- **Error:** alert with message and "Try again"; inputs kept. Field errors show under each field
  and the first invalid field is focused.
- **Copied:** toast "Brief copied to clipboard" (falls back to selecting text if clipboard API is blocked).

## Copy format
Plain text with headings and bullet lines, using the *edited* content, e.g.
```
Glow Lab — TikTok campaign brief
Goal: Awareness · Tone: Playful

SUMMARY
...
CONTENT ANGLES
1. Title — hook
   description
```
