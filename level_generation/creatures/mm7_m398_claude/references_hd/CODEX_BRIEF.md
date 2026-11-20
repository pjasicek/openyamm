# Codex brief (run 2): four HD front/back/side views for the MM7 Skeleton Warrior (m398)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m398_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m398_three_quarter_v2` in
`generation_runs.json`; earlier brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new
runs to the existing `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m398_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m398_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same skeleton warrior, skull, helmet, cuirass, bones, gauntlets, breeches, greaves, colours, pose,
   proportions, light and render style.
2. `mm7_m398/native/m398sa0.png` — ORIGINAL native front.
3. `mm7_m398/native/m398sa2.png` — ORIGINAL native right profile (open armour side with ribs, neck, helmet spike).
4. `mm7_m398/native/m398sa4.png` — ORIGINAL native back (dark back plate, breeches seat, greaves from behind).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" means the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of it | skull face, front of the cuirass; its RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind it | back of the skull and helmet, the back plate, seat of the breeches, backs of the greaves; its RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm and leg nearest the camera; ribs visible through the open brass-rimmed side of the cuirass |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm and leg nearest the camera; ribs visible through the open side |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in stains or small surface spots.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same armoured skeleton as
input 1 (a faithful HD reconstruction of the existing Might and Magic VII Skeleton Warrior monster), as a 3D modelling
reference. Not a new design. ONE complete figure, helmet spike to soles, centred, generous margins, near-orthographic
camera at chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio
light, same render style and materials as input 1.

Identity (as in input 1): bare aged ochre-ivory human skull with hollow dark eye sockets and exposed teeth under a
small rounded steel skull-cap helmet with a brass band and one short top spike; thin bony neck in a raised
brass-rimmed collar; a dented dark steel cuirass with thick brass borders at the neck, arm holes and lower edge, its
sides open frames through which thin ribs show, with a matching back plate; bare-bone shoulders and upper arms with
rusty red stains; dark steel gauntlets from the elbow with brass rims and articulated five-fingered plated hands;
ragged faded blue-violet breeches to just below the knee, frayed hem, rusty red stains; bare bone knees and upper
shins; tall dark steel greaves with a brass ring at the top and plated feet. Rusty dark red streaks on bone, armour
and cloth as in input 1.

Pose (identical in all views, as in input 1): standing upright, legs straight and apart with a clear gap between the
legs and feet, feet flat with toes forward. Arms hanging down and slightly out to the sides, elbows very slightly
bent, a clear gap of air between each arm and the body and between each hand and the thigh. Gauntleted hands open and
relaxed, fingers slightly apart, palms facing the thighs. Head level, looking forward.

Do NOT: draw a sword or any weapon, arrows, a shield, a cape or any extra equipment; add skin, flesh or eyes; add
extra spikes, horns or pauldrons; change the colours; change the pose (no turned head, no raised arm); crop the
helmet spike or the feet; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same figure, proportions, pose and colours as input 1;
- whole figure inside the frame with margins, true transparent background, 1024 x 1536;
- empty hands, no arrows, no weapon; five digits per gauntlet wherever visible;
- in profile, the arm nearest the camera hangs clear of the torso and the far arm is mostly hidden behind it.
