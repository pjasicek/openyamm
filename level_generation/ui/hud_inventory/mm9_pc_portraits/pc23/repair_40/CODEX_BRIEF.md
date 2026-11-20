# Codex brief: repair slots 40 of MM9 PC23

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc23/repair_40`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 1 windows of 118x158 in 156x182 slots, left to right = slots 40
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc27, pc28, pc29):
   - row 1: slot 40 (smile)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 1 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1024x1024 or larger:

- slot 40: smile, as in row 1 of `consensus.png`, with the head as in input 1's window 1.

The character: hooded lich: a bone-white skull with glowing red eyes ringed in green, inside a deep dark-green hood of thick cloth, a gold winged crest on the brow with a blue jewel at its centre, black vertebrae below the jaw; no skin or hair. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
