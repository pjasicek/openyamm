# Codex brief (run 3): four HD front/back/side views for the MM7 Harpy (m262)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m262_claude/references_hd/`. No builds,
no Meshy. Do NOT touch `00_three_quarter.png` or `knife.png`: the primary is ALREADY SELECTED by the orchestrator
(run `m262_three_quarter_v3`). Append the new runs to `generation_runs.json` (same format), raw returns under `raw/`
(`m262_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m262_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every view:
   same harpy, face, silver hair, silver bodice, gold waist band, teal bracers, feathered thighs, orange bird legs and
   feet, wings (raised high), colours, pose, proportions, light and render style.
2. `mm7_m262/native/m262wa0.png` — ORIGINAL native front.
3. `mm7_m262/native/m262wa2.png` — ORIGINAL native side profile.
4. `mm7_m262/native/m262wa4.png` — ORIGINAL native back (wings from behind, tail fan, hair crest).

## Deliverables (1536 x 1024 landscape, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" = the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front | face, bodice, both wings raised symmetrically behind; its RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind | back of the hair crest, the wing roots on the shoulder blades, backs of both wings, the tail fan; its RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm and leg nearest the camera; wings rise behind its back |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm and leg nearest the camera; wings rise behind its back |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a failed
view do at most ONE targeted corrective regeneration, then select the better of the two and note residual faults.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same harpy as input 1 (a
faithful HD reconstruction of the existing Might and Magic VII Harpy monster), as a 3D modelling reference. Not a new
design. ONE complete figure, hair to talons and both wings to their tips, centred, GENEROUS margins on all four sides
(talons well above the bottom edge), near-orthographic camera at chest height, transparent background, no floor, no
shadow, no scenery, no text. Even soft neutral studio light, same render style and materials as input 1.

Identity (as in input 1): lean middle-aged harpy woman, gaunt stern face, tan-olive skin, long silver-white hair swept
back; silver metal bodice cups with gold edges covering the bust; bare abdomen; narrow gold waist band; teal-green
bracers with gold rims on both forearms; empty human hands with five fingers; dark brown mottled feathers covering
hips and thighs, a short brown tail fan behind; long orange scaly bird legs and orange bird feet with three front toes,
one back toe and dark curved talons; two feathered wings on the shoulder blades: brown mottled coverts, long teal-green
flight feathers, raised high in a steep V with the inner trailing edge above the shoulders.

Pose (identical in all views, as in input 1): standing upright on the bird feet, legs straight and apart, arms hanging
down and out at about 30 degrees with a clear gap to the body, hands empty, head level, wings raised high.

Do NOT: draw the knife or any weapon; add armour or clothing; add nudity (the bodice covers the bust); add extra arms
or wings, a beak or a bird head; change colours or pose; crop wing tips, hair or talons; add floor, shadow or text.

Checks per view: correct camera (side and facing); pure front/back/profile; same figure, pose, wings and colours as
input 1; whole figure inside the frame with margins, true alpha, 1536 x 1024; five fingers per hand where visible; in
profile the near arm hangs clear of the torso and the wings sit behind the back.
