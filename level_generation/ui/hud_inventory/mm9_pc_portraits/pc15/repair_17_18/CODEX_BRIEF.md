# Codex brief: repair slots 17, 18 of MM9 PC15

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc15/repair_17_18`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 2 windows of 118x158 in 156x182 slots, left to right = slots 17, 18
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus_17.png`: slot 17 (look up) in 4 existing families (7pc14, 7pc13, pc05, pc01): the wanted look for that slot.
3. `consensus_18.png`: slot 18 (glance to its own left (viewer's right), head nearly frontal) in 4 existing families (7pc14, 7pc13, pc05, pc01): the wanted look for that slot.
4. `../raw_A.png` and 5. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 2 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1024x1024 or larger:

- slot 17: look up, as in `consensus_17.png`, with the head as in input 1's window 1.
- slot 18: glance to its own left (viewer's right), head nearly frontal, as in `consensus_18.png`, with the head as in input 1's window 2.

Hair, horns and ears kept as close to the head as in the identity master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
