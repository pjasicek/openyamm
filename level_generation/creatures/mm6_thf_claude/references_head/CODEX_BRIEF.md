# Codex brief: HD head turnaround for the MM6 Thief (thf)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_thf_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the record format of
`level_generation/creatures/mm6_thf_claude/references_hd/generation_runs.json`. Attached inputs, in order:
1. `level_generation/creatures/mm6_thf_claude/references_hd/01_front.png` — the SELECTED HD front body master:
   exact face, hair, moustache and hood identity authority.
2. `level_generation/creatures/mm6_thf_claude/references_hd/00_three_quarter.png` — the selected three-quarter
   master: hood depth and the face inside it.
3. `level_generation/creatures/mm6_thf_claude/references_hd/02_back.png` — the selected back master: back of the hood.

## Deliverables (5 images, 1024 x 1024 SQUARE, true transparent background, unresized returns)

| File | View |
|---|---|
| `00_front.png` | exact straight-on front (primary; generate first) |
| `01_three_quarter.png` | front-right three-quarter (camera 45 degrees toward his right) |
| `02_left.png` | his own LEFT side, pure profile: he faces IMAGE LEFT |
| `03_back.png` | straight from behind |
| `04_right.png` | his own RIGHT side, pure profile: he faces IMAGE RIGHT |

Generate 01–04 with 00 as an additional input so all five show the SAME head. Accept a view as soon as it passes the
checks; at most ONE targeted corrective regeneration per view. Write `generation_runs.json` and a
`selected_views_review.png` contact sheet; keep raw returns under `raw/`.

## Prompt content (adapt per view)

Use case: identity-preserve. Asset: head texture reference turnaround for the existing MM6 Thief, not a new design.
The EXACT SAME hooded head as the selected body masters, isolated: ONE HOODED HEAD AND NECK ONLY, like a sculpted
bust WITHOUT shoulders, mantle or chest: the hood and neck end in a clean straight HORIZONTAL cut a little below the
chin. Head centred and level; from the hood tip to the cut fills about 80% of the frame height, generous transparent
margins, near-orthographic camera at eye height. Do not crop the hood.

Identity (must match the body masters exactly): slim adult man, long thin face, pale skin, straight nose, narrow eyes
with visible irises, a thin drooping brown moustache and short chin stubble, straight brown hair falling to the jaw at
both sides of the face inside the hood. Deep soft loose grey-green wool hood, up, with a soft point at the back;
plain weave with a few irregular dark worn blotches (no woven or embossed pattern); the face fully visible in the
opening. Sharp fine detail: skin, eyes, eyebrows, moustache and hair strands, wool weave.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow, background
gradient, checkerboard drawn into the image, scene or text. No shoulders, mantle, cloak body or jerkin. Do not change
colours.

Checks per image: 1024 x 1024; true transparency; only the hooded head and neck with a straight horizontal cut below
the chin; whole hood inside the frame; same face, hair, moustache and hood as the body masters; side views facing the
stated direction.
