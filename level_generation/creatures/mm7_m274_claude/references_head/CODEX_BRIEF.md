# Codex brief: head turnaround for the MM7 Mage (m274)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m274_claude/references_head/`. No builds,
no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m274_claude/references_hd/00_three_quarter.png` — the selected HD body master: IDENTITY AUTHORITY (face, skin,
   eyes, helmet, hair).
2. `mm7_m274_claude/references_hd/01_front.png` — the selected HD front master (same character, front view).
3. `mm7_m274/native/m274sa0.png` — ORIGINAL native front frame (palette authority; transparent background).

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
Use case: stylized-concept. Create one high definition head-and-beard portrait modelling texture reference of the SAME
MM7 Mage as in the supplied body references. Square composition, transparent background. Frame the head, the hair and
the WHOLE long beard down to its tip with the two thin braids, the neck; leave out the magenta collar, the gold yoke,
the robe and the hands (the beard hangs free in front of where the chest would be), generous clear margins. Preserve
exactly: the stern middle-aged face with heavy ginger brows, a long straight nose, light warm skin, receding ginger
hair swept back, and the very long thick GINGER-ORANGE beard with its texture of coarse wavy strands and the two thin
braided strands hanging from the moustache. Neutral even studio light, no directional shadows or highlights, no
dramatic grading; fine hair and skin detail useful for a game texture. One head only, no labels, no text, no floor or
shadow.

Checks before selecting each view: correct camera and facing; one head only; ginger beard with two braids, ginger hair and skin as in the
references; nothing cropped; true transparent alpha. Do at most ONE corrective regeneration per
failed view, then keep the better one and note residual faults.
