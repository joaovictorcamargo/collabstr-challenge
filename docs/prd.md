# Lite PRD — AI Brief Generator

## Problem
Brands arrive at Collabstr knowing *who* they are and roughly *what* they want ("more TikTok buzz"),
but not how to write a brief a creator can act on. A vague brief leads to fewer good applicants,
more back-and-forth in chat, and content that misses the goal. The blank page is the blocker.

## Who
A small or mid-size brand marketer starting their first or second creator campaign on Collabstr,
usually without an agency or a brief template.

## Intended outcome
In under a minute, the brand goes from four choices to a structured, editable first draft
(brief, content angles, creator criteria) that it copies into its campaign or creator outreach.

## Primary success metric
**Brief adoption rate** = briefs copied ÷ briefs generated (per session).
Copying is the clearest sign the draft was good enough to carry into the next step.
Instrumented now with `brief_generated` and `brief_copied` events.

Guardrails (watched, not optimised): generation error rate, p95 latency, regenerate rate
(a high rate suggests weak first drafts).

Downstream (needs real product integration): campaigns posted with a generated brief, and
applications per campaign compared with campaigns without one.

## Scope
In:
- Four required inputs (brand, platform, goal, tone) plus one optional short "What are you promoting?" note.
- One LLM call that returns structured JSON: summary, objective, key message, deliverables, do's/don'ts, content angles, creator criteria.
- Editable result, one-click "Copy brief", regenerate, loading/success/error states.
- Rate limiting, input validation, safe rendering, usage events in logs.

Out (later):
- Saving briefs, accounts, pushing the brief straight into Collabstr's campaign flow.
- Budget, timeline, and creator matching against real Collabstr creator data.
- Streaming, multi-language, A/B testing infrastructure.

## Assumptions
- Brands want a solid starting point to edit, not a final document.
- The next step is pasting into a campaign form or a message to creators, so plain text copy is the right hand-off.
- An optional product note is worth one extra field: without it, the model can only guess what the brand sells.
- Within the timebox, logs are an acceptable analytics sink; production would use the existing analytics pipeline.
