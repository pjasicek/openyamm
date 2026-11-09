# Codex brief: HD reference views for the MM7 Ooze (mm7_m298_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m298_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (record format as in
`level_generation/creatures/mm6_ooz_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM7 standing sprites enlarged 4x with nearest neighbour, top to
   bottom: front, front three-quarter, side, rear three-quarter, back. Magenta is background, not creature. Design,
   shape and colour authority (tier A colouring).
2. `references_hd/native_palettes.png` — the three-quarter view in the three native palettes (green, blue, red). Use
   the LEFT (green) colouring only.
3. `references_hd/native_actions.png` — native attack frames (a knobbed pseudopod rises out of the middle). Material
   evidence only: do NOT draw a pseudopod.
4. `level_generation/creatures/mm7_m298/trimmed_2x/m298sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY (never the design).

## Deliverables (5 images, transparent background, 1536 x 1024 LANDSCAPE, unresized returns)

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, camera above at about 30 degrees elevation (primary; generate first) |
| `01_front.png` | front, camera at about 20 degrees elevation |
| `02_back.png` | back, camera at about 20 degrees elevation |
| `03_left.png` | the blob's left side, camera at about 20 degrees elevation |
| `04_right.png` | the blob's right side, camera at about 20 degrees elevation |

The blob has no face; "front" is simply the side shown in native view 0. Left/right: in `03_left` the blob's front
points to image LEFT, in `04_right` to image RIGHT.

Generate ONLY `00_three_quarter.png` in the first run unless told otherwise. Views 01–04 come in a separate run with
the frozen `00` as the FIRST input, so all five show the SAME blob with the same lobes and lumps. At most one
corrective regeneration per view. Also write `generation_runs.json` (id, prompt, inputs with sha256, output path,
selected flag, reason, superseded runs) and a `selected_views_review.png` contact sheet. Keep raw returns in
`references_hd/raw/`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Ooze from the supplied original sprites, as a 3D modelling and texturing reference. Not a new design.
Credible, fully three-dimensional object with semi-realistic game material and sharp fine detail.

Identity (from the native sprites): a low, flat, irregular puddle-mound of thick gelatinous slime. In plan it is a
rounded, roughly oval shape, only slightly wider than it is long (native front view 178 px wide, side view 164 px
long), and its height is only about one quarter of its width (native height about 42 px). The middle is a gentle low
dome; toward the rim it thins out. The rim is irregular and lobed: several rounded bulging lobes of different sizes,
and on the left and right sides (seen from the front) a longer tapering tongue-like lobe that flows out along the
floor. The whole surface is covered with soft, rounded, wormy ridges, coiled bulges and shallow dimples, like thick
churning jelly, with fine smooth specular ridges. Material: wet, glossy, very DARK green slime (deep bottle-green to
blackish green in the creases, dark mid green on the bulges, a faint teal tinge on the edges of the bulges), opaque
but looking slightly translucent at the thin rim. Keep the specular glints SMALL and soft (the game engine adds its
own gloss): the base colour must read as dark green, not white. No eyes, no mouth, no face, no bones, no objects
inside.

Camera and light: one complete blob centred with generous margins, near-orthographic camera, even soft neutral
studio light from above (no dramatic shadows, no coloured light, no rim light), transparent background, no floor, no
cast shadow, no text.

Do NOT: add eyes, teeth, a face, a pseudopod or tentacles, bubbles floating in the air, skulls or bones inside, drips
in the air, a floor, puddle reflections or shadows; make it tall or spherical; brighten or change the colour (it is
very dark green); crop the rim or the side tongues.

## Checks per image (re-run before selecting)

Whole blob in frame with margins; low flat proportions (height about one quarter of the width, plan nearly round,
slightly wider than long); lobed rim with rounded lumps and the two side tongues; wormy glossy surface; very dark
green; no face or added features; transparent background (true alpha); 1536 x 1024; the same blob as `00`.
