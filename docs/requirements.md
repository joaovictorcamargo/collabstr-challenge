# Requirements — AI Brief Generator

Source of truth: the "Collabstr Product Engineer Project" brief. Each requirement has an ID that
`docs/tasks.md` and the final verification table in `README.md` refer back to.

## Functional

| ID | Requirement |
|----|-------------|
| F1 | Single-page experience. |
| F2 | Input: Brand name (free text). |
| F3 | Input: Target platform — Instagram, TikTok, or UGC. |
| F4 | Input: Goal — Awareness, Conversions, or Content Assets. |
| F5 | Input: Tone — Professional, Friendly, or Playful. |
| F6 | Output: a campaign brief tailored to the inputs. |
| F7 | Output: suggested content angles. |
| F8 | Output: creator selection criteria. |
| F9 | Result is usable in the brand's next step (e.g. copy or edit it). |
| F10 | One small, deliberately chosen interaction, with the reason explained. |
| F11 | Clear loading, success, and error states. |
| F12 | An LLM generates the brief. |

## Technical

| ID | Requirement |
|----|-------------|
| T1 | Backend in Python / Django. |
| T2 | Frontend in plain HTML / CSS / JavaScript with jQuery. |
| T3 | Looks and feels like a Collabstr product, using https://collabstr.com/design-system as reference. |
| T4 | Production-minded decisions that suit a small feature (no over-engineering). |
| T5 | Code is clear and appropriately tested. |

## README write-up (brief, a few bullets each)

| ID | Requirement |
|----|-------------|
| D1 | Lite PRD: user problem, intended outcome, one primary success metric, scope, assumptions. |
| D2 | Technical approach: how frontend, Django and LLM fit together; decisions and tradeoffs; implemented vs. production additions; reliability and safety. |
| D3 | Design rationale: main UX decisions and how the design system was used. |
| D4 | Validation and iteration: what was tested, what to measure/learn, what to improve next. |
| D5 | Setup and run instructions. |
| D6 | How AI tools were used and what was checked by hand. |
| D7 | Tradeoffs and anything not finished within the timebox are called out. |

## Deliverables (sent by the candidate)

| ID | Deliverable | Delivered |
|----|-------------|-----|
| X1 | Public GitHub repository with the README. | https://github.com/joaovictorcamargo/collabstr-challenge |
| X2 | Publicly accessible live implementation. | https://collabstr-brief-generator.onrender.com |
| X3 | Loom demo under 1 minute (core flow plus one product decision). | https://www.loom.com/share/2e68fc7bf39a4341b4a4e36dfb9d4324 |

## Constraints

- Timebox of roughly one hour for the original exercise. Favour a working end-to-end slice over many features.
- No customer interviews or live experiments are needed.
- Unfinished items or tradeoffs go in the README, not into extra scope.

## Evaluation criteria (what reviewers check)

1. Product judgment and ownership
2. UX and design consistency with Collabstr
3. Full-stack execution (Django to frontend, tests)
4. AI and production thinking
5. Measurement and iteration
6. Communication (assumptions, risks, AI-tool use)

## Acceptance criteria

- AC1: With valid inputs, the user gets a brief, at least 3 content angles and at least 3 creator criteria, each tailored to brand, platform, goal and tone.
- AC2: Invalid or missing inputs are rejected by the server with field-level messages, and the UI shows them next to the field.
- AC3: While generating, the button is disabled, a progress state is shown, and duplicate submits are blocked.
- AC4: If the LLM fails, times out, or returns unusable output, the user sees a plain-language error and can retry without retyping.
- AC5: The user can edit any part of the result and copy the whole (edited) brief as clean text in one click, with confirmation.
- AC6: Works with keyboard only and with a screen reader (labels, live regions, focus handling), and at 375px width.
- AC7: Model output is rendered as text, never as HTML.
- AC8: The API key never reaches the browser; the endpoint is CSRF-protected and rate-limited.
