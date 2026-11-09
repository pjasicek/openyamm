# Codex brief (run 2): four HD front/back/side views for the MM6 Barbarian (bar1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_bar1_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (run `bar1_three_quarter_v2` in `generation_runs.json`; brief
`CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new runs to `generation_runs.json` (same
record format), keep raw returns under `raw/` (`bar1_front_v1.png`, ...), and at the end write
`selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm6_bar1_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same character, face, hair, circlet, armour, gauntlets, belt, scale armour panel, boots, colours, pose,
   proportions, light and render style.
2. `mm6_bar1/references/standing.png` — ORIGINAL native five-view sheet (blue palette; magenta background). Use it for
   what each view shows (the back of the armour, the hair at the back).
3. `mm6_bar1/native_variants/bar1sta2_663.png` — ORIGINAL native profile frame (tier A colours).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (she faces the viewer in `01_front`; "her left" means her own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of her | face and chest; her RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind her | back of the hair, the chest plate's back strap, the back of the belt and armour panel straps; her RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at her LEFT side, pure 90-degree profile | she faces IMAGE LEFT; her LEFT arm and leg nearest the camera |
| `04_right.png` | at her RIGHT side, pure 90-degree profile | she faces IMAGE RIGHT; her RIGHT arm and leg nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a failed
view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual fault.

## Prompt content (adapt per view)

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VI Barbarian), as a 3D modelling reference. Not a new
design. ONE complete figure, top of the hair to the boot soles, centred, generous margins, near-orthographic camera
at chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light,
same render style and materials as input 1.

Identity (as in input 1): a practical, non-sexualised fantasy warrior character for a game: an athletic, muscular
woman, tanned skin, long thick wavy auburn hair past the shoulders, a thin gold circlet on the forehead. Armour exactly
as input 1: a pale gold metal chest plate made of two rounded plates with gold trim and a small red gem at the centre;
a gold collar and flared pointed gold shoulder guards; gold armlets on the upper arms; long dark brown leather
gauntlets to below the elbows with gold studs and separate fingers; a brown leather war belt with a round gold buckle
and red gem; a bronze-gold scale-mail armour panel hanging from the belt to mid-thigh; dark brown leather knee boots
with gold straps and studs and thick pale fur cuffs at the top. Keep the armour coverage exactly as in input 1.
Neutral, modest presentation: straight neutral stance, calm expression, documentation-style turnaround view.

If the image tool refuses a view, retry that view ONCE adding a thin dark brown leather underlayer (fitted shorts
under the scale panel and a fitted top under the chest plate), and note the deviation in the run's reason.

Pose (identical in all views, as in input 1): neutral A-pose, standing upright, legs straight and slightly apart
with a clear gap between the legs and boots, feet flat, toes forward. Arms hanging down and out at about 25-35 degrees
from vertical, elbows very slightly bent, a clear gap of air between each arm and the body and between each hand and
the thigh. Hands relaxed and open, fingers slightly curled and slightly apart, palms facing the thighs. Head level,
looking forward.

Do NOT: draw a sword, scabbard, weapon or shield; add a cape, cloak, skirt, helmet or pouches; change any colour;
change the pose (no turned head, no raised arm); crop the hair or boots; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same character, proportions, pose and colours as input 1;
- whole figure inside the frame with margins, true transparent background, 1024 x 1536;
- empty open hands with five fingers wherever visible; no weapon or scabbard;
- in profile, the arm nearest the camera hangs clear of the torso.
