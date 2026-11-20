# Codex brief: paint the elder hat onto its exact 3D shape (mm9_honkmale_claude/hats/work)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_honkmale_claude/hats/work/`. No builds, no Meshy.
The renders are of the final low-poly 3D mesh of the hat. The paint is projected straight back onto it, so THE OUTLINE AND EVERY PART MUST
STAY AT EXACTLY THE SAME PIXEL POSITIONS: same canvas, same framing, same silhouette, same transparent background. Add surface colour and fine
detail only, as flat even colours with very soft shading in the recesses, no highlights, no cast shadows.

## Inputs (attached, in order)
`elder_front.png`, `elder_q34.png`, `elder_side.png`, `elder_sidem.png`, `elder_back.png`, `elder_backq.png`: clay renders (6 views).
Then `hats/references/elder_01_front.png`, `elder_02_back.png`, `elder_03_left.png`, `elder_00.png`: the approved HD look: hammered silver scale
feathers on the body, embossed feathers on the wings, a gold knotwork brim, polished gold goose neck and head with a bead eye, hammered gold back sheets.

## Deliverables (unresized, 1254 x 1254)
`paint_front.png`, `paint_q34.png`, `paint_side.png`, `paint_sidem.png`, `paint_back.png`, `paint_backq.png`: each the repaint of the clay view of the
same name. Paint `paint_front` first, then the others with it as an extra input. One corrective regeneration at most. Write `generation_runs.json`.
