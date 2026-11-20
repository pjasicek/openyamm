# Codex brief: repair slots 40, 41 of MM9 PC16

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc16/repair_40_41`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 2 windows of 118x158 in 156x182 slots, left to right = slots 40, 41
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus_40.png`: slot 40 (smile) in 4 existing families (7pc15, pc02, 7pc05, pc12): the wanted look for that slot.
3. `consensus_41.png`: slot 41 (wide smile) in 4 existing families (7pc15, pc02, 7pc05, pc12): the wanted look for that slot.
4. `../raw_A.png` and 5. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 2 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1024x1024 or larger:

- slot 40: smile, as in `consensus_40.png`, with the head as in input 1's window 1.
- slot 41: wide smile, as in `consensus_41.png`, with the head as in input 1's window 2.

Hair, horns and ears kept as close to the head as in the identity master.

Eyes: pale blue-grey irises exactly as in `raw_A.png` and `raw_B.png`, never brown (a first repair drew brown eyes
and was rejected). Copy only the smile from the consensus strips; eye colour, brows, skin and hair come from the
identity master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
