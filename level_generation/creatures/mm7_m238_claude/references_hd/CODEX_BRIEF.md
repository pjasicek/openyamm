# Codex brief (run 2): four HD front/back/side views for the MM7 Genie (m238)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m238_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png` or `lamp.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m238_three_quarter_v2` in
`generation_runs.json`; earlier brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new
runs to the existing `generation_runs.json` (same record format), keep raw returns under `raw/` (`m238_front_v1.png`,
...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m238_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same genie, face, hair, ponytail rings, circlet, earrings, collar, top, cuffs, vortex tail, colours, pose,
   proportions, light and render style.
2. `mm7_m238/native/m238wa0.png` — ORIGINAL native front.
3. `mm7_m238/native/m238wa2.png` — ORIGINAL native side profile.
4. `mm7_m238/native/m238wa4.png` — ORIGINAL native back (ponytail from behind, bare back, the vortex).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" means the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of her | face, front of the top and collar, the vortex front; her RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind her | back of the head and ponytail, bare back, the halter straps, the vortex from behind; her RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at her LEFT side, pure 90-degree profile | she faces IMAGE LEFT; her LEFT arm nearest the camera; the ponytail curving back |
| `04_right.png` | at her RIGHT side, pure 90-degree profile | she faces IMAGE RIGHT; her RIGHT arm nearest the camera; the ponytail curving back |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in feather counts or small surface spots.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same genie as input 1 (a
faithful HD reconstruction of the existing Might and Magic VII Genie monster), as a 3D modelling reference. Not a new
design. ONE complete figure, top of the ponytail to the tip of the vortex tail, centred, generous margins,
near-orthographic camera at chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft
neutral studio light, same render style and materials as input 1.

Identity (as in input 1): a slender female genie with cobalt-blue skin and NO LEGS; a stern face, pointed ears; navy
hair in a tall high ponytail wrapped by gold rings and ending in a gold cone; a gold circlet with a red forehead jewel;
green drop earrings; a green high collar with gold edges; a green halter top with gold trim; green wrist cuffs with gold
trim; bare blue midriff and arms; below the hips a swirling pale blue-white water-mist vortex tail tapering to a point.

Pose (identical in all views, as in input 1): upright, floating, the vortex hanging straight down. Arms hanging down and
out to the sides at about 30 degrees from vertical, elbows very slightly bent, a clear gap of air between each arm and
the body; hands open, five fingers, palms facing the body. Head level, looking forward.

Do NOT: fold the arms; add legs, a cloth skirt, a lamp, sparkles, smoke clouds or glow; change the colours; change the
pose; crop the ponytail or the tail tip; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same figure, proportions, pose, ponytail, vortex and colours as input 1;
- whole figure inside the frame with margins, true transparent background, 1024 x 1536;
- empty hands; five fingers per hand wherever visible;
- in profile, the arm nearest the camera hangs clear of the torso; the ponytail behind the head;
- no legs anywhere: the vortex tail starts at the hips.
