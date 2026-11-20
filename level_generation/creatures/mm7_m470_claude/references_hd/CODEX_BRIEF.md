# Codex brief (run 2): four HD front/back/side views for the MM7 Ghoul (m470)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m470_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m470_three_quarter_v1`, by orchestrator override in
`generation_runs.json`; earlier brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new
runs to the existing `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m470_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m470_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same ghoul, face, ears, hair, overalls, bracers, clawed hands, bare feet, colours, pose,
   proportions, light and render style.
2. `mm7_m470/native/m470sa0.png` — ORIGINAL native front.
3. `mm7_m470/native/m470sa2.png` — ORIGINAL native right profile (mane, ears, eyelet rows).
4. `mm7_m470/native/m470sa4.png` — ORIGINAL native back (mane, back lacing, straps).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" means the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of it | face, chest lacing; its RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind it | mane down the back, back lacing and straps; its RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm and leg nearest the camera |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm and leg nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in stains or small surface spots.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same ghoul as input 1 (a
faithful HD reconstruction of the existing Might and Magic VII Ghoul monster), as a 3D modelling reference. Not a new
design. ONE complete figure, hair and ear tips to the soles, centred, generous margins, near-orthographic camera at
chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same
render style and materials as input 1.

Identity (as in input 1): tall lean undead humanoid; pale ivory-grey skin; gaunt angular face with a pointed chin, a
toothy grin, small yellow-green eyes, wide pointed ears; coarse ash-blond hair swept up at the front with a long
narrow mane down the back; bare shoulders and upper arms; dark mottled brown leather bib overalls with crisscross pale
lacing through silver eyelets on the chest and the centre back, two narrow shoulder straps, tight trousers with a row
of round silver eyelets down the outside of each leg; brown leather laced forearm bracers; bare pale clawed hands with
long black nails; bare pale feet.

Pose (identical in all views, as in input 1): standing upright, legs straight and apart with a clear gap, feet flat
with toes forward; arms down and out to the sides, elbows very slightly bent, a clear gap of air between each arm and
the body; hands open, long clawed fingers slightly apart and slightly curled. Head level, looking forward.

Do NOT: add weapons, a shirt, shoes or any accessory; add blood or effects; change the colours; change the pose; crop
the ears, hair or feet; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same figure, proportions, pose and colours as input 1;
- whole figure inside the frame with margins, true transparent background, 1024 x 1536;
- empty hands, no weapon; five digits per hand wherever visible;
- in profile, the arm nearest the camera hangs clear of the torso and the far arm is mostly hidden behind it.
