# Codex brief (run 2): four HD front/back/side views for the MM7 Ghost (m242)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m242_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m242_three_quarter_v3`). Do not
regenerate or re-judge it. Append the new runs to `generation_runs.json` (same record format), keep raw returns under
`raw/` (`m242_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m242_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every view:
   same ghost, skull, hood, ribcage, bony arms and hands, robe, colours, pose, proportions, light and render style.
2. `mm7_m242/native/m242sa0.png` — ORIGINAL native front.
3. `mm7_m242/native/m242sa2.png` — ORIGINAL native side profile (thin robe, hood peak).
4. `mm7_m242/native/m242sa4.png` — ORIGINAL native back (the robe's back and its ragged hem points).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the ghost faces the viewer in `01_front`; "its left" means its own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of it | skull face in the hood, the open robe front with the ribcage; its RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind it | the back of the hood and the robe's back with its tattered hem; its RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm nearest the camera; the robe thin front to back |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a failed view
do at most ONE targeted corrective regeneration, then select the better of the two and note any residual fault.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same floating ghost as
input 1 (a faithful HD reconstruction of the existing Might and Magic VII Ghost monster), as a 3D modelling reference.
Not a new design. ONE complete figure from the hood peak to the lowest robe shreds, centred, generous margins,
near-orthographic camera at chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft
neutral studio light, same render style and materials as input 1.

Identity (as in input 1): a yellowed ivory human skull with black hollow sockets inside a deep pointed dark umber
hood; the robe open at the front from the neck to the waist showing the ivory ribcage, sternum and spine; the robe
draped over the shoulders and upper arms like a cape; bare bony forearms and long five-fingered skeletal hands; a
heavy, worn, moth-eaten dark umber-brown robe falling straight to a deeply tattered hem of long pointed shreds; NO legs
and NO feet.

Pose (identical in all views, as in input 1): floating upright, both bony arms held out to the sides and slightly
forward, the forearms and open claw hands entirely clear of the robe, fingers spread, palms down; head level; the robe
hanging straight and still.

Do NOT: draw legs, feet, a scythe or any weapon, chains, lantern or effects; add skin or eyes; change the colours or the
pose; let the hands touch the robe; crop the hood or the hem; add a floor, shadow or text.

Checks per view:
- the camera matches the table; pure front/back/profile, not three-quarter;
- same figure, proportions, pose and colours as input 1; no legs;
- whole figure inside the frame with margins, true transparent background, 1024 x 1536;
- five fingers per hand where visible; hands clear of the robe;
- in profile the near arm and hand are clear of the robe and the far arm mostly hidden behind the body.
