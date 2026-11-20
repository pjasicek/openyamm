# Codex brief: paint the cheek under a shortened cheek strap (mm9_dookmilitia_claude, run 2)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dookmilitia_claude/references_head/strip/`. No builds, no Meshy. Use your built-in image generation tool (an image edit of input 1).

A fantasy video-game character's head seen from his left side (a half-orc soldier in a helmet), a colour map that is projected onto a 3D head. On the 3D model the vertical dark-leather cheek strap is SHORTER than in this painting: it ends at the top of the red area. So the cheek and jaw skin under the lower part of the strap must be painted.

## Inputs (attached, in order)
1. `references_head/<t>_03_left_clean.png`: the painting to edit.
2. `references_head/strip/<t>_03_left_overlay.png`: the same image with the area to repaint tinted red.

## Deliverable
`references_head/strip/<t>_03_left_nobar.png`: input 1, edited, the SAME size (1254 x 1254), the same framing, pixel for pixel: the head must not move, scale, turn or change. Inside the red area of input 2 only: remove the cheek strap (dark leather, gold edges, silver stud) completely and paint the bare half-orc skin that lies under it: the cheek and the side of the jaw, the same tawny brown skin, pores, stubble and soft shading as the cheek just in front of and behind the strap, continuing the jaw line and the cheek's form naturally, with no straight edges, no outline of the strap, no shadow of it. Everything outside the red area stays exactly as in input 1, including the upper part of the strap above the red area, the ear, the helmet and the background. Even soft studio light, no new shadows, no text.
Keep the raw return in `references_head/strip/raw/`. Write `references_head/strip/generation_runs_<t>.json` (prompt, inputs, output path). At most one corrective regeneration.
