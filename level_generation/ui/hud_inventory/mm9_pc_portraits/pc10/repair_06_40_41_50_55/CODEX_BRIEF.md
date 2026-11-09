# Codex brief: repair slots 6, 40, 41, 50, 55 of MM9 PC10

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc10/repair_06_40_41_50_55`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 5 windows of 118x158 in 156x182 slots, left to right = slots 6, 40, 41, 50, 55
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus_06.png`: slot 6 (drunk: tilted, loose grin) in 3 existing families (pc02, 7pc05, pc12): the wanted look for that slot.
3. `consensus_40.png`: slot 40 (smile) in 3 existing families (pc02, 7pc05, pc12): the wanted look for that slot.
4. `consensus_41.png`: slot 41 (wide smile) in 3 existing families (pc02, 7pc05, pc12): the wanted look for that slot.
5. `consensus_50.png`: slot 50 (happy) in 3 existing families (pc02, 7pc05, pc12): the wanted look for that slot.
6. `consensus_55.png`: slot 55 (grin) in 3 existing families (pc02, 7pc05, pc12): the wanted look for that slot.
7. `../raw_A.png` and 8. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 5 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 2560x1024 or larger:

- slot 6: drunk: tilted, loose grin, as in `consensus_06.png`, with the head as in input 1's window 1.
- slot 40: smile, as in `consensus_40.png`, with the head as in input 1's window 2.
- slot 41: wide smile, as in `consensus_41.png`, with the head as in input 1's window 3.
- slot 50: happy, as in `consensus_50.png`, with the head as in input 1's window 4.
- slot 55: grin, as in `consensus_55.png`, with the head as in input 1's window 5.

Hair, horns and ears kept as close to the head as in the identity master.

These are her smiles: make each one clearly read as a smile at portrait size (corners of the full lips lifted, cheeks raised; teeth showing in 41, 50 and 55), as strong as in the consensus strips, not the near-neutral mouth of her other frames.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
