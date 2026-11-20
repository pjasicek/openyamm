# Codex brief: head turnaround for the MM7 Necromancer (m294)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m294_claude/references_head/`. No
builds, no Meshy, no other files. If the image tool declines a request, do NOT rephrase or retry it yourself: stop,
record the exact refusal text in `generation_runs.json` and in your last message.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m294_claude/references_hd/00_three_quarter.png` — the selected HD body master: IDENTITY AUTHORITY (face, skin,
   eyes, circlet, choker, hair).
2. `mm7_m294_claude/references_hd/01_front.png` — the selected HD front master (same character, front view).
3. `mm7_m294_claude/references_hd/02_back.png` — the selected HD back master (the long white hair from behind).

Deliverables: four head-and-neck portraits, each 1254 x 1254 (or the nearest available square size), genuine
transparent background, unresized returns, raw copies under `raw/`, records in `generation_runs.json` (name, prompt,
inputs with sha256, output path, selected flag, reason), and `selected_views_review.png` (all four side by side on
mid-grey):

| File | Camera |
|---|---|
| `00_three_quarter.png` | front three-quarter, camera 30 degrees toward her anatomical left |
| `01_front.png` | straight front |
| `02_profile.png` | exact LEFT profile (she faces IMAGE LEFT) |
| `03_back.png` | straight back (the back of the head, the forehead band's tie and the long white hair) |

Prompt (adapt the camera per view):
Use case: stylized-concept. Create one high definition head-and-hair portrait modelling texture reference of the SAME
Might and Magic VII Necromancer (a dignified undead sorceress) as in the supplied body references. Square composition,
transparent background. Frame the head, the neck with its black choker and the long hair down to the shoulders (crop
the hair at shoulder height); the high purple collar may show at the bottom edge; generous clear margins. Preserve
exactly: her stern adult face with a neutral expression, very pale grey-white skin, pale glowing white eyes, dark
lips, the thin black forehead band with the small round gold ornament and pale jewel at the brow, the black choker,
and the long straight WHITE hair parted at the centre, falling past the ears and behind the shoulders. Neutral even
studio light, no directional shadows or highlights, no dramatic grading; fine hair and skin detail useful for a game
texture. One head only, no labels, no text, no floor or shadow.

Checks before selecting each view: correct camera and facing; one head only; white straight hair, circlet, choker,
face and skin as in the references; nothing cropped; true transparent alpha. Do at most ONE corrective regeneration
per failed view, then keep the better one and note residual faults.
