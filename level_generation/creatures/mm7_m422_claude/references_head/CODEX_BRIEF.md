# Codex brief: head turnaround for the MM7 m422 character (pale court nobleman)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m422_claude/references_head/`. No builds,
no Meshy, no other files.

This brief uses the neutral wording that the image tool accepted for the body masters (see
`../references_hd/generation_runs.json`, note `note_refusal_override_20261020`). If the image tool declines a view,
record the refusal text (error code, moderation fields) in `generation_runs.json` and in your last message, skip that
view, continue with the others, and do not reword the request yourself.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m422_claude/references_hd/01_front.png` — the selected HD front master: IDENTITY AUTHORITY (face, skin, eyes,
   hair, render style).
2. `mm7_m422_claude/references_hd/03_left.png` — the selected HD left profile (same character).
3. `mm7_m422_claude/references_hd/02_back.png` — the selected HD back view (back of the head, hair).
4. `mm7_m422/native/m422sa0.png` — original low-resolution game frame, front (palette authority; the transparent
   background is not part of the figure).

Deliverables: four head-and-neck portraits, each 1254 x 1254 (or the nearest available square size), genuine
transparent background, unresized returns, raw copies under `raw/`, records in `generation_runs.json` (id, prompt,
inputs with sha256, output path, selected flag, reason), and `selected_views_review.png` (all selected views side by
side on mid-grey):

| File | Camera |
|---|---|
| `00_three_quarter.png` | front three-quarter, camera 30 degrees toward his anatomical left |
| `01_front.png` | straight front |
| `02_profile.png` | exact LEFT profile (he faces IMAGE LEFT) |
| `03_back.png` | straight back (back of the head and the hair) |

Prompt (adapt the camera per view):
Use case: stylized-concept. A high definition head-and-neck texture reference of the SAME original fantasy game
character as in the supplied body references (a calm, dignified court nobleman). Stylised hand-painted game-art
render, clearly a game character and not a photograph; an original face that does not resemble any real person, actor
or film character. Square composition, transparent background. Frame the head, the hair and the neck down to the base
of the neck; leave out the collar, the cape, the coat and the shoulders; generous clear margins. Preserve: very pale
ivory-grey skin, a narrow composed face with high cheekbones, a calm neutral expression, dark eyes, dark brows, the
mouth gently closed with the tips of two small pointed canine teeth just visible over the lower lip (subtle), short
neat swept-back charcoal-grey hair with a pointed hairline in the middle of the forehead. Neutral even studio light, no
directional shadows or highlights, no dramatic grading; fine hair and skin detail useful for a game texture. One head
only, no labels, no text, no floor or shadow, no blood or effects.

Checks before selecting each view: correct camera and facing; one head only; skin, hair and face as in the references;
nothing cropped; true transparent alpha. Do at most ONE corrective regeneration per failed view, then keep the better
one and note residual faults.
