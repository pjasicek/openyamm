# Codex brief: repair slots 5, 40, 43, 44, 49, 56 of MM9 PC07

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc07/repair_05_40_43_44_49_56`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 6 windows of 118x158 in 156x182 slots, left to right = slots 5, 40, 43, 44, 49, 56
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus_05.png`: slot 5 (fear: wide eyes, open mouth) in 3 existing families (pc05, pc07, 7pc02): the wanted look for that slot.
3. `consensus_40.png`: slot 40 (smile) in 3 existing families (pc05, pc07, 7pc02): the wanted look for that slot.
4. `consensus_43.png`: slot 43 (casting: eyes squeezed shut) in 3 existing families (pc05, pc07, 7pc02): the wanted look for that slot.
5. `consensus_44.png`: slot 44 (determined, lips parted) in 3 existing families (pc05, pc07, 7pc02): the wanted look for that slot.
6. `consensus_49.png`: slot 49 (disgust: tongue out) in 3 existing families (pc05, pc07, 7pc02): the wanted look for that slot.
7. `consensus_56.png`: slot 56 (shout, mouth wide open) in 3 existing families (pc05, pc07, 7pc02): the wanted look for that slot.
8. `../raw_A.png` and 9. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 6 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 3072x1024 or larger:

- slot 5: fear: wide eyes, open mouth, as in `consensus_05.png`, with the head as in input 1's window 1.
- slot 40: smile, as in `consensus_40.png`, with the head as in input 1's window 2.
- slot 43: casting: eyes squeezed shut, as in `consensus_43.png`, with the head as in input 1's window 3.
- slot 44: determined, lips parted, as in `consensus_44.png`, with the head as in input 1's window 4.
- slot 49: disgust: tongue out, as in `consensus_49.png`, with the head as in input 1's window 5.
- slot 56: shout, mouth wide open, as in `consensus_56.png`, with the head as in input 1's window 6.

Hair, horns and ears kept as close to the head as in the identity master.

EAR SIZE (correction after a first attempt, kept in `attempt1/`): that attempt drew the ears clearly shorter than
sheets A and B. This character's pointed ears are very large and long and stick out sideways and slightly up: in
every portrait, each ear must reach as far out from the head, relative to the face width, as in the frontal
portraits of `raw_A.png` (whole-head width about 0.88 of the head height from crown to chin stub). Do not shrink
or tuck the ears.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
