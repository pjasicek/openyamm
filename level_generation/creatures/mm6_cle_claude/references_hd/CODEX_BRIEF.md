# Codex brief (run 2): four HD side/front/back views for the MM6 Cleric (cle)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_cle_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `cle_three_quarter_v2` in
`generation_runs.json`; earlier run brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the
new runs to the existing `generation_runs.json` (same record format), keep raw returns under `raw/`, and at the end
write `selected_views_review.png` (all five selected views side by side on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm6_cle_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same man, face, hair, collar, mantle, emblem, cloak, tunic, belt, cuffs, trousers, boots, colours, pose,
   proportions, light and render style.
2. `mm6_cle/references/standing.png` — ORIGINAL native five-view sheet (front, front three-quarter, profile, rear
   three-quarter, back); magenta is background, and the staff in it is NOT to be drawn. Use it for what each view
   shows (how the cloak covers the side and the back).
3. `mm6_cle/native/clesta2.png` — ORIGINAL native profile frame (transparent background).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the cleric faces the viewer in `01_front`; "his left" means the cleric's own anatomical left;
his LEFT hand is the firm fist, his RIGHT hand the loosely closed one):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | the firm LEFT fist on IMAGE RIGHT, the loosely closed right hand on IMAGE LEFT; emblem centred on the mantle; belt tongue centred |
| `02_back.png` | straight behind him | the closed cloak back from the collar to the ankles, the back of the head and collar; his LEFT (fist) hand, where visible, on IMAGE LEFT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his LEFT arm and fist nearest the camera |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his RIGHT arm and loosely closed hand nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in fold detail.

## Prompt content (adapt per view)

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VI Cleric of Baa), as a 3D modelling reference. Not a
new design. ONE complete figure, hair to boot soles, centred, about 80% of the canvas height, generous margins,
near-orthographic camera at chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft
neutral studio light, same render style and materials as input 1.

Identity (as in input 1): clean-shaven adult man with a narrow face and jaw-length light brown hair parted in the
middle; a pale silver-grey stand-up collar joined to a short round grey shoulder mantle with thin dark navy piping,
a small dark navy ankh-like emblem centred on the chest of the mantle; a long pale grey cloak hanging from the
shoulders to the ankles, OPEN AT THE FRONT and closed all round the back, behind the arms, with a thin dark hem edge;
a medium blue long-sleeved tunic to just below the knees with a hem longer at the centre front; a tan leather belt
with a gold buckle and a long tongue hanging down the centre front; broad gold wrist cuffs; dark navy trousers and
dark navy boots.

Pose (identical to input 1): standing upright, legs straight and slightly apart with a gap between the legs and the
boots, feet flat; arms down and away from the body at about 25 degrees, the arms in front of the open cloak, with air
between each arm and the torso; his LEFT hand a firm fist with a vertical grip opening (as if holding an invisible
upright staff), his RIGHT hand loosely closed; both hands empty. Head level, looking forward.

Do NOT: draw a staff or any held object; add a hood, beard, armour, extra jewellery, embroidery or extra symbols;
put a clasp or symbol on the cloak; change colours; close the cloak at the front; let the cloak cover the hands;
crop the hair, cloak hem or boots; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); same pose and proportions as input 1;
- whole figure inside the frame (hair, cloak hem, both boots), true transparent background, 1024 x 1536;
- same collar, mantle with piping, emblem (front only), cloak length and openness, tunic, belt, cuffs, trousers and
  boots wherever the view can see them;
- left hand a firm fist, right hand loosely closed, both empty; no added object.
