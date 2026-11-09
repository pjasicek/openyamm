# Codex brief: HD head turnarounds for the MM9 mummies (mm9_mummy_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_mummy_claude/references_head/`. No builds, no Meshy, no other files.
Tiers are as in `../references_hd/CODEX_BRIEF.md`. Use your built-in image generation tool.

## Inputs (attached, in order)
1. `references_head/mm9_head_t1.png`, `mm9_head_t2.png`, `mm9_head_t3.png`: renders of the ORIGINAL low-poly head and shoulders with skins 1, 2, 3 (three-quarter, side, front, back). Face, strip layout and colour authority; blur and faceting are not the design.
2. `references_hd/mm9_skin_x4_t1.png`, `_t2`, `_t3`: original skins enlarged: the face panel top left is the sharpest evidence of each face.
3. Selected tier A body masters `references_hd/00_three_quarter.png`, `01_front.png`, `02_back.png`, `03_left.png`: head shape, hood wraps and the identity of tier A.

## Deliverables (1254x1254, true transparent background, bust only: crown to the collarbones, head level, shoulders cut cleanly, never cropped at the crown)
For each tier X in A, B, C, in `references_head/tier<X>/`: `01_front.png`, `02_back.png`, `03_left.png` (pure profile facing IMAGE RIGHT), `04_right.png` (pure profile facing IMAGE LEFT).
All twelve show the SAME head: the SAME skull proportions, hood outline, neck and collar as the tier A master. Only the surface changes. At most one corrective regeneration per image. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and `selected_views_review.png`.

## Surface
- Tier A: exactly the master's head: tight linen bandage hood with overlapping raised bands and dark gaps, a gaunt dead bearded man's open face, one strip diagonally across the face over one eye, the visible eye dull and half open. Back of the head: chevron-crossed bands converging toward the nape, as in the render.
- Tier B: same hood, more torn, dark gaps and dried brown skin at the temples. The face is a yellowed SKULL with shreds of dried skin: cracked cheekbone, long bare teeth (upper and lower row, mouth closed), nasal hole, pale blue dead eyes in dark sockets. One strip crosses the forehead diagonally.
- Tier C: same hood, darker and dirtier, more strips across the face. The face is a darker rotted skull, almost black flesh in the hollows, one reddish eye, the other half hidden by a strip, dark lips over a few teeth.
No hair beyond the short beard of tier A. No loose strips standing away from the head. No jewels, no floor, no shadow, no text. Even soft studio light. Near-orthographic.

## Additional deliverable, first image of this run: `references_head/00_geometry.png`
For 3D modelling only: 1254x1254, true alpha, the same bust at a front three-quarter view, camera at eye height. The same head shape and hood outline, as a clean SCULPT reference: a gaunt old man's
head with clear anatomy (brow, deep eye sockets, closed eyelids, thin straight nose, hollow cheeks, closed thin lips, strong chin, NO beard, NO strip across the face) inside a smooth tight cloth hood that covers crown, ears and neck
and leaves the face open, the hood's edge a clear raised rim round the face. Neutral matte clay-beige, no pattern, even light. It must read as one clean solid form: the mouth must not bulge, no moustache, no folds on the face.
