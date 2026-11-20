# Codex brief (run 2): four HD front/back/side views for the MM7 Lich (m270)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m270_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m270_three_quarter_v2` in
`generation_runs.json`; earlier brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new
runs to the existing `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m270_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m270_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same lich, skull, crown, coif, plate, pauldrons, belt, chain sleeves and skirt, hands, colours, pose,
   proportions, light and render style.
2. `mm7_m270/native/m270sa0.png` — ORIGINAL native front.
3. `mm7_m270/native/m270sa2.png` — ORIGINAL native right profile (coif, crown, plate and skirt profile).
4. `mm7_m270/native/m270sa4.png` — ORIGINAL native back (coif, back plate, belt, skirt).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" means the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of it | skull face, breastplate, belt buckle; its RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind it | back of the coif and crown, back plate, belt, skirt; its RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm nearest the camera |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in stains or small surface spots.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same lich as input 1 (a
faithful HD reconstruction of the existing Might and Magic VII Lich monster), as a 3D modelling reference. Not a new
design. ONE complete figure, crown points to the shoe tips, centred, generous margins, near-orthographic camera at
chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same
render style and materials as input 1.

Identity (as in input 1): an undead skeletal king-sorcerer: small bare ivory-grey skull face with dark sockets and
teeth under a gold pointed crown; a dark blue-violet grey chainmail coif around the head and neck; polished silver
breastplate with segmented abdomen and large angular gold-rimmed silver pauldrons, matching back plate; broad gold
belt with an ornate buckle; dark blue-violet grey chain sleeves with silver gold-rimmed wrist cuffs; bare bony
five-fingered skeletal hands; a long narrow floor-length chainmail skirt over dark steel pointed shoes.

Pose (identical in all views, as in input 1): standing upright, the skirt falling straight; arms held down and out
from the body, elbows very slightly bent, a clear gap of air between each arm and the body; bony hands open and
relaxed, fingers slightly apart, palms toward the body. Head level, looking forward.

Do NOT: draw a staff, orb or any weapon, a cape, wings or extra ornaments; add flesh; change the colours; change the
pose; crop the crown or the feet; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same figure, proportions, pose and colours as input 1;
- whole figure inside the frame with margins, true transparent background, 1024 x 1536;
- empty hands, no weapon; five digits per hand wherever visible;
- in profile, the arm nearest the camera hangs clear of the torso and the far arm is mostly hidden behind it.
