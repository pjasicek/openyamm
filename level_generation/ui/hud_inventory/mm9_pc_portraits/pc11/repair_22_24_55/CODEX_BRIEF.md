# Codex brief: repair slots 22, 24, 55 of MM9 PC11

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc11/repair_22_24_55`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 3 windows of 118x158 in 156x182 slots, left to right = slots 22, 24, 55
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc05, pc33, 7pc01):
   - row 1: slot 22 (talk: mouth open)
   - row 2: slot 24 (talk: O mouth)
   - row 3: slot 55 (grin)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 3 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1536x1024 or larger:

- slot 22: talk: mouth open, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 24: talk: O mouth, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 55: grin, as in row 3 of `consensus.png`, with the head as in input 1's window 3.

Hair, horns and ears kept as close to the head as in the identity master.

He is clean-shaven: no beard, goatee, moustache or stubble in any slot, even where input 1's character has one. Horns stay tightly curled close to the head. Slot 22: mouth clearly open as when talking; slot 24: lips rounded into an O; slot 55: a broad open grin.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
