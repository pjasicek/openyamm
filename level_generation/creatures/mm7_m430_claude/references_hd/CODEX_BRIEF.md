# Codex brief (run 2): four HD front/back/side views for the MM7 Wight (m430)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m430_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m430_three_quarter_v2` in
`generation_runs.json`; earlier brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new
runs to the existing `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m430_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m430_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same wight, face, hair, robe, sleeves, cord, hem, hands, colours, pose,
   proportions, light and render style.
2. `mm7_m430/native/m430sa0.png` — ORIGINAL native front.
3. `mm7_m430/native/m430sa2.png` — ORIGINAL native right profile (head carried forward, hair, robe fall).
4. `mm7_m430/native/m430sa4.png` — ORIGINAL native back (long hair, waist cord, hem).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" means the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of it | face, V neckline, waist cord; its RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind it | back of the head with the long hair, back of the robe, cord, hem; its RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm nearest the camera |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in stains or small surface spots.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same wight as input 1 (a
faithful HD reconstruction of the existing Might and Magic VII Wight monster), as a 3D modelling reference. Not a new
design. ONE complete figure, top of the head to the robe hem, centred, generous margins, near-orthographic camera at
chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same
render style and materials as input 1.

Identity (as in input 1): tall thin undead; small gaunt skull-like face with pale grey-green skin, black empty eye
sockets, narrow nose, thin closed mouth; bald head with long straight thin silver-grey hair hanging at the sides and
back to the shoulders, no hood; worn dark earth-brown floor-length coarse robe with crossed V neckline, loose flared
sleeves ending in long pointed torn strips, narrow dark brown waist cord tied in front with hanging ends, widely
spread ragged hem with holes and torn points hiding the feet; long bony pale grey-green five-fingered hands.

Pose (identical in all views, as in input 1): standing upright, robe falling to the ground; arms held down and out
from the body, elbows very slightly bent, a clear gap of air between each arm (with its sleeve) and the body; hands
open and relaxed, fingers slightly apart, palms toward the body. Head level, looking forward.

Do NOT: draw a dagger or any weapon, a hood, armour, feet, extra limbs; add blood, glow or effects; change the
colours; change the pose (no turned head, no raised arm); crop the head or the hem; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same figure, proportions, pose and colours as input 1;
- whole figure inside the frame with margins, true transparent background, 1024 x 1536;
- empty hands, no weapon; five digits per hand wherever visible;
- in profile, the arm nearest the camera hangs clear of the torso and the far arm is mostly hidden behind it.
