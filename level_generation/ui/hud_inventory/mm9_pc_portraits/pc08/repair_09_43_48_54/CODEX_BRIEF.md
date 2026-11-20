# Codex brief: repair slots 9, 43, 48, 54 of MM9 PC08

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc08/repair_09_43_48_54`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 4 windows of 118x158 in 156x182 slots, left to right = slots 9, 43, 48, 54
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus_09.png`: slot 9 (diseased: pustules) in 4 existing families (pc02, pc12, pc31, 7pc05): the wanted look for that slot.
3. `consensus_43.png`: slot 43 (casting: eyes squeezed shut) in 4 existing families (pc02, pc12, pc31, 7pc05): the wanted look for that slot.
4. `consensus_48.png`: slot 48 (smug closed-mouth smile) in 4 existing families (pc02, pc12, pc31, 7pc05): the wanted look for that slot.
5. `consensus_54.png`: slot 54 (enraged: red face, snarl) in 4 existing families (pc02, pc12, pc31, 7pc05): the wanted look for that slot.
6. `../raw_A.png` and 7. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 4 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 2048x1024 or larger:

- slot 9: diseased: pustules, as in `consensus_09.png`, with the head as in input 1's window 1.
- slot 43: casting: eyes squeezed shut, as in `consensus_43.png`, with the head as in input 1's window 2.
- slot 48: smug closed-mouth smile, as in `consensus_48.png`, with the head as in input 1's window 3.
- slot 54: enraged: red face, snarl, as in `consensus_54.png`, with the head as in input 1's window 4.

Hair, horns and ears kept as close to the head as in the identity master.

Correction after a first attempt (kept in `attempt1/`): it drew the ears shorter and the brows lighter than
sheets A and B. If the image tool accepts at most five reference images, pass `template.png`, `raw_A.png`,
`raw_B.png` and the two consensus strips you need most, and describe the others in the prompt. The very large
pointed ears stick out sideways exactly as far as in the frontal portraits of `raw_A.png` (whole-head width about
0.80 of the crown-to-chin height); do not shrink them. Brows strongly arched and dark brown, deep red lips, dark
eye make-up, golden-brown cropped hair exactly as in the identity master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
