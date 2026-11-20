# Codex brief: repair slots 6, 44, 47 of MM9 PC05

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc05/repair_06_44_47`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 3 windows of 118x158 in 156x182 slots, left to right = slots 6, 44, 47
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus_06.png`: slot 6 (drunk: tilted, loose grin) in 3 existing families (pc02, 7pc05, pc05): the wanted look for that slot.
3. `consensus_44.png`: slot 44 (determined, lips parted) in 3 existing families (pc02, 7pc05, pc05): the wanted look for that slot.
4. `consensus_47.png`: slot 47 (eyes closed, calm) in 3 existing families (pc02, 7pc05, pc05): the wanted look for that slot.
5. `../raw_A.png` and 6. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 3 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1536x1024 or larger:

- slot 6: drunk: tilted, loose grin, as in `consensus_06.png`, with the head as in input 1's window 1.
- slot 44: determined, lips parted, as in `consensus_44.png`, with the head as in input 1's window 2.
- slot 47: eyes closed, calm, as in `consensus_47.png`, with the head as in input 1's window 3.

Hair, horns and ears kept as close to the head as in the identity master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
