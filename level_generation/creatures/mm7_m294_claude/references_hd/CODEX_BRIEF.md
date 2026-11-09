# Codex brief (run 3): four HD views for the MM7 Necromancer (m294), covered outfit

User decision 2026-10-20: reworded, non-sexualised reference (fully covered version of the native outfit); see run 2.

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m294_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m294_three_quarter_v2_corrective`
in `generation_runs.json`). Do not regenerate or re-judge it. Append the new runs to `generation_runs.json` (same
record format), keep raw returns under `raw/`, and at the end write `selected_views_review.png` (all five selected
views side by side on a mid-grey background). If the image tool declines a request, do NOT rephrase or retry it
yourself: stop, record the exact refusal text in `generation_runs.json` and in your last message.

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m294_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same sorceress, face, white hair, circlet, choker, long-sleeved high-necked purple tunic with black inset
   panels and diagonal black straps, black leggings, black heeled boots with gold knee chevrons, long ragged black
   split cape; same pose, proportions, light and render style.
2. `mm7_m294/native/m294sa4.png` — original low-resolution game BACK frame: the long white hair down the back over the
   long ragged black cape to the floor (silhouette and colours only).
3. `mm7_m294/native/m294sa2.png` — original low-resolution game PROFILE frame (silhouette only).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (she faces the viewer in `01_front`; "her left" means her own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of her | symmetric front: face and circlet ornament centred, her RIGHT hand on IMAGE LEFT, her LEFT hand on IMAGE RIGHT, the cape panels behind the arms and beside the legs |
| `02_back.png` | straight behind her | the long white hair down the back over the black cape, the cape to the floor with a ragged hem; her LEFT hand on IMAGE LEFT |
| `03_left.png` | at her LEFT side, pure 90-degree profile | she faces IMAGE LEFT; her left arm and hand nearest the camera |
| `04_right.png` | at her RIGHT side, pure 90-degree profile | she faces IMAGE RIGHT; her right arm and hand nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason.

## Prompt content (adapt per view)

TASK CONTEXT — FANTASY-GAME 3D MODELLING REFERENCE: one more orthographic view of the EXACT same character as input 1
(the Might and Magic VII Necromancer, a dignified undead sorceress), as a 3D modelling reference. Not a new design.
ONE complete figure from the top of the head to the boot soles and cape hem, centred, about 80% of the canvas height,
generous margins, near-orthographic camera at chest height, transparent background, no floor, no shadow, no scenery,
no text. Even soft neutral studio light, same render style and materials as input 1.

Character (as in input 1): pale grey-white skin, neutral expression, pale glowing eyes; long straight white hair to
the waist; thin black forehead band with a gold ornament; black choker; an opaque dark purple long-sleeved tunic with
a high neckline, black and darker-purple inset panels and diagonal black straps, reaching the upper thighs; opaque
black leggings; tall glossy black heeled boots to just above the knee with gold chevron knee trim; a long ragged black
cape from the shoulders to the floor, split at the front into two panels beside the legs, hem torn into long strips;
slender pale hands with long dark nails, empty.

Pose (identical to input 1): neutral reference A-pose, standing upright, feet about shoulder width apart with a gap
between the legs; arms out from the body at about 40 degrees from vertical with air between each arm and the body and
cape, arms in front of the cape; hands open, fingers separated; head level.

Do NOT: draw a weapon or held object; add armour, a hood or extra jewellery; show bare torso, bare legs or openings
in the outfit; change colours; let the cape or the hair cover the arms or hands; crop the head, boots or cape hem; add
a floor, shadow, glow or text.

Checks per view:
- the camera matches the table (side and facing direction); same pose and proportions as input 1;
- whole figure inside the frame (head, boots, cape hem), true transparent background, 1024 x 1536;
- same hair, circlet, choker, tunic panels and straps, leggings, boots with gold chevrons and cape wherever the view
  can see them; hands open and empty; no added object.
