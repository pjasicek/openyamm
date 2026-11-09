# Codex brief: repaint the underside of a lizard warrior's jaw and throat (mm9_lizardorc_claude, run 2)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_lizardorc_claude/references_head/throat/`. No builds, no Meshy, no other files. Use your built-in image generation tool (an image edit of input 1).

Input 1 is a colour map, not a photo: the head of a fantasy lizard-man warrior seen from straight BELOW and slightly in front, flat-lit, as it will be projected back onto a 3D model. The long crocodile-like lower jaw points UP in the image (its teeth at the top), the throat runs DOWN to a steel breastplate at the bottom. The current paint of the jaw's underside and throat is broken: smeared flat yellow areas, stretched streaks, a flat octagon near the jaw tip, a dark diamond, grey gaps and thin pale rays.

## Inputs (attached, in order)
1. `references_head/throat/throat_below.png`: the painting to edit (1024 x 1024).
2. `references_head/throat/throat_below_overlay.png`: the same image with the area to repaint tinted red.
3. `references_hd/01_front_clean.png`: the character's design (front view) for colours and scale style.

## Deliverable
`references_head/throat/throat_below_edit.png`: input 1 edited, the SAME size (1024 x 1024) and the same framing pixel for pixel: nothing may move, scale or turn. Inside the red area of input 2 only, paint the reptile skin of the underside of the lower jaw and the throat as ONE continuous surface:
- the middle: pale yellow-cream belly scales (rows of soft rounded/hexagonal scales, like the yellow throat scales at the bottom of input 1 above the breastplate and like input 3's throat), running from the breastplate up the throat and along the underside of the jaw to its tip;
- toward the left and right edges: blending smoothly into the green scaled hide of the jaw's sides, matching the green just outside the red area;
- a clear, crisp scale pattern everywhere, same scale size as the throat scales at the bottom, continuous, with no smears, streaks, flat fills, holes, octagons, diamonds, dark spots, seams or straight edges; fill the grey gaps inside the red area with skin.
Everything outside the red area stays exactly as in input 1 (teeth, red mouth corners, steel armour, background grey). Flat even light: no shadows, no highlights, no text.
Keep the raw return in `references_head/throat/raw/`. Write `references_head/throat/generation_runs.json` (prompt, inputs, output path). At most one corrective regeneration.
