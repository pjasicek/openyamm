# Codex brief: repair slots 2 of MM9 PC08

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc08/repair_02`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 1 windows of 118x158 in 156x182 slots, left to right = slots 2
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc02, pc31, 7pc05):
   - row 1: slot 2 (cursed: heavy-lidded, drained)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 1 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1024x1024 or larger:

- slot 2: cursed: heavy-lidded, drained, as in row 1 of `consensus.png`, with the head as in input 1's window 1.

The character: young female elf, short thick cropped golden-brown hair brushed up and back in a soft rounded crop, no braids or beads, very large long pointed ears that stick out sideways, fair pale-pink skin, oval face with high cheekbones and a small pointed chin, small straight nose, full lips with deep red lipstick, pale grey-blue eyes with dark eye make-up and strongly arched dark brows. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears kept as close to the head as in the identity master.

Slot 2 is the CURSED condition: heavy, drooping half-closed eyelids, a drained, weary look and slack lips, as in
the consensus strip. The very large pointed ears stick out sideways exactly as far as in the frontal portraits of
`raw_A.png` (whole-head width about 0.80 of the crown-to-chin height); do not shrink them. Brows strongly arched
and dark brown, deep red lips, dark eye make-up, golden-brown cropped hair exactly as in the identity master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
