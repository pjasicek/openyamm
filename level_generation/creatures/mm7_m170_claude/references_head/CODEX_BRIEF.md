# Codex brief: head turnaround for the MM7 Cleric of the Moon (m170)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m170_claude/references_head/`. No builds,
no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m170_claude/references_hd/00_three_quarter.png` — the selected HD body master: IDENTITY AUTHORITY (face, skin,
   eyes, helmet, hair).
2. `mm7_m170_claude/references_hd/01_front.png` — the selected HD front master (same character, front view).
3. `mm7_m170/native/m170sa0.png` — ORIGINAL native front frame (palette authority; transparent background).

Deliverables: four head-and-neck portraits, each 1254 x 1254 (or the nearest available square size), genuine
transparent background, unresized returns, raw copies under `raw/`, records in `generation_runs.json` (name, prompt,
inputs with sha256, output path, selected flag, reason), and `selected_views_review.png` (all four side by side on
mid-grey):

| File | Camera |
|---|---|
| `00_three_quarter.png` | front three-quarter, camera 30 degrees toward his anatomical left |
| `01_front.png` | straight front |
| `02_profile.png` | exact LEFT profile (he faces IMAGE LEFT) |
| `03_back.png` | straight back (back of the helmet and the long black hair) |

Prompt (adapt the camera per view):
Use case: stylized-concept. Create one high definition head-and-neck portrait modelling texture reference of the SAME
MM7 Cleric of the Moon as in the supplied body references. Square composition, transparent background. Frame only the
head, helmet, hair and neck, the neck ending just above the collar, generous clear margins; no collar, crescent, back
frame, banners, robe or hands. Preserve the same gaunt, severe adult male face with ashen GREY (cool blue-grey) skin,
long narrow face, high cheekbones, sunken cheeks, thin lips, straight nose, pale eyes, clean-shaven; the polished GOLD
domed helmet with its broad browband and short gold cheek plates exactly as in the references; long straight BLACK hair
falling from under the helmet behind the ears down the back. Neutral even studio light, no directional shadows or
highlights, no dramatic grading; realistic skin pores and fine hair strands useful for a game texture. One head only,
no labels, no text, no floor or shadow.

Checks before selecting each view: correct camera and facing; one head only; grey skin, pale eyes, black hair, gold
helmet as in the references; nothing cropped; true transparent alpha. Do at most ONE corrective regeneration per
failed view, then keep the better one and note residual faults.
