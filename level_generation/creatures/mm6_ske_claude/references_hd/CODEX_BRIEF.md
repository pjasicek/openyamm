# Codex brief (run 2): four HD front/back/side views for the MM6 Skeleton (ske)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_ske_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `ske_three_quarter_v1` in
`generation_runs.json`; earlier brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new
runs to the existing `generation_runs.json` (same record format), keep raw returns under `raw/`
(`ske_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm6_ske_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same skeleton, skull, ribcage, spine, pelvis, limb bones, hands, feet, bone colour, pose, proportions,
   light and render style.
2. `mm6_ske/references/standing.png` — ORIGINAL native five-view sheet (top row: front, front three-quarter,
   profile; bottom row: rear three-quarter, back). Magenta is background. Use it for what each view shows (the
   shoulder blades and spine from behind, the neck carry in profile).
3. `mm6_ske/native/skesta2.png` — ORIGINAL native profile frame.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the skeleton faces the viewer in `01_front`; "its left" means the skeleton's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of it | face, sternum and front of the ribcage; its RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind it | back of the skull, spine, both shoulder blades, back of the pelvis; its RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm and leg nearest the camera |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm and leg nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in rib count or small surface spots.

## Prompt content (adapt per view)

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same skeleton as input 1
(a faithful HD reconstruction of the existing Might and Magic VI Skeleton monster), as a 3D modelling reference. Not
a new design. ONE complete figure, top of the skull to the foot bones, centred, generous margins, near-orthographic
camera at chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio
light, same render style and bone material as input 1.

Identity (as in input 1): a complete, tall and lanky adult human skeleton. Smooth rounded skull with deep round eye
sockets holding a small glowing RED point each, dark nasal opening, full upper and lower teeth, closed lower jaw.
Short cervical spine with the head carried slightly forward. Sternum and about twelve pairs of thin separate curved
ribs with dark gaps, clavicles, shoulder blades on the back. A single visible column of lumbar vertebrae between the
ribcage and the broad pelvis, open space on both sides of it. Upper arm bones, two thin forearm bones, knobbly
elbows, bony five-fingered hands. Long femurs, kneecaps, two lower-leg bones, long flat bony feet with five toes.
Clean smooth dry bone in the SAME warm ivory/cream colour as input 1, soft grey shading in crevices, small darker
pores; no dirt, cracks, moss, blood or rust.

Pose (identical in all views, as in input 1): neutral A-pose, standing upright, legs straight and apart with a clear
gap between the legs and feet, feet flat with toes forward. Arms hanging down and out at about 35 degrees from
vertical, elbows very slightly bent, a clear gap of air between each arm and the body and between each hand and the
thigh. Hands relaxed, fingers slightly curled and held together, palms facing the thighs. Head level, looking
forward.

Do NOT: draw a sword or any weapon, a shield, armour, clothing, rags, a belt or any equipment; add flesh, skin,
muscle or organs; fill the rib gaps; add extra fingers, toes, ribs, horns or spikes; change the bone colour; change
the pose (no turned head, no raised arm); crop the skull or the feet; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same skeleton, proportions, pose and bone colour as input 1;
- whole figure inside the frame with margins, true transparent background, 1024 x 1536;
- empty hands, five fingers and five toes wherever visible, red eye points visible in front and profile views;
- in profile, the arm nearest the camera hangs clear of the ribcage and the far arm is mostly hidden behind it.
