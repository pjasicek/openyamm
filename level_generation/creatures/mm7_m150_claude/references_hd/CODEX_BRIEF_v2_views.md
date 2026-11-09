# Codex brief (v2 run 2): four HD front/back/side views for the MM7 Angel (m150), bare head, steel cuirass

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m150_claude/references_hd/v2/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `v2/00_three_quarter.png`, `v2/helmet.png` or `v2/shield.png`.

The primary `v2/00_three_quarter.png` is ALREADY SELECTED by the orchestrator (`v2/generation_runs.json`; brief:
`CODEX_BRIEF_v2_primary.md`). Do not regenerate or re-judge it. Append the new
runs to `v2/generation_runs.json` (same record format), keep raw returns under `v2/raw/` (`m150_front_v1.png`,
...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m150_claude/references_hd/v2/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same angel, face, bare head and hair (NO helmet), polished steel cuirass, bracers, belt, skirt and leather tabs, greaves, sandals, wings,
   colours, pose, proportions, light and render style.
2. `mm7_m150/native/m150sa0.png` — ORIGINAL native front.
3. `mm7_m150/native/m150sa2.png` — ORIGINAL native side profile.
4. `mm7_m150/native/m150sa4.png` — ORIGINAL native back (wings from behind, back plate, skirt seat).

## Deliverables (1536 x 1024 landscape, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" means the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `v2/01_front.png` | straight in front of it | face, front of the breastplate, both wings spread symmetrically behind; its RIGHT arm on IMAGE LEFT |
| `v2/02_back.png` | straight behind it | back of the head and hair, the back plate, the wing roots on the shoulder blades and the backs of both wings, seat of the skirt; its RIGHT arm on IMAGE RIGHT |
| `v2/03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm and leg nearest the camera; the wings rise behind its back |
| `v2/04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm and leg nearest the camera; the wings rise behind its back |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in feather counts or small surface spots.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same winged warrior as
input 1 (a faithful HD reconstruction of the existing Might and Magic VII Angel monster), as a 3D modelling reference.
Not a new design. ONE complete figure, top of the head to soles and both wings to their tips, centred, generous margins,
near-orthographic camera at chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft
neutral studio light, same render style and materials as input 1.

Identity (as in input 1): athletic muscular man with a stern clean-shaven tan face, BARE HEAD (no helmet, no
headband), dark brown wavy hair combed back and falling to the nape; a POLISHED SILVER STEEL muscled cuirass (front
and back plates) with brass-gold rims at the neck, armholes and lower edge and a brass-rimmed steel shoulder strap
over each shoulder; a brown leather belt with a round brass buckle and brass rings; dark steel bracers with
brass rims on both forearms; bare tan arms and hands; a green knee-length skirt with dark brown leather strap tabs and
small brass rings hanging over it; dark steel greaves with brass rims and brown leather straps; brown leather sandals.
Two large feathered wings on the shoulder blades: white to pale lavender upper feathers, blue-violet undersides,
long primary feathers at the tips.

Pose (identical in all views, as in input 1): standing upright, legs straight and apart with a clear gap between the
legs and feet, feet flat with toes forward. Arms hanging down and slightly out to the sides, elbows very slightly
bent, a clear gap of air between each arm and the body and between each hand and the skirt. Hands empty, open and
relaxed, fingers slightly apart, palms facing the thighs. Head level, looking forward. Wings spread and raised in a
high open V exactly as in input 1, tips high, the trailing edges above the elbows. Arms out at 35-40 degrees as in
input 1, with open armpits.

Do NOT: draw a helmet or headband, a sword, a shield or any weapon; dark armour; add a cape, halo, glow or magic effects; add a beard, extra arms or extra
wings; change the colours; change the pose (no turned head, no raised arm, no folded wings); crop the wing tips, the
crest or the feet; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same figure, proportions, pose, wings and colours as input 1;
- whole figure and both wing tips inside the frame with margins, true transparent background, 1536 x 1024;
- empty hands, no weapon or shield; five fingers per hand wherever visible;
- in profile, the arm nearest the camera hangs clear of the torso; the wings sit behind the back (the far wing mostly
  hidden behind the near wing);
- in the front and back views the wings are symmetric and attached at the shoulder blades.
