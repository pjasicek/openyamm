# Codex brief: repair slots 43, 44 of MM9 PC19

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc19/repair_43_44`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 2 windows of 118x158 in 156x182 slots, left to right = slots 43, 44
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus_43.png`: slot 43 (casting: eyes squeezed shut) in 3 existing families (pc27, pc28, pc29): the wanted look for that slot.
3. `consensus_44.png`: slot 44 (determined, lips parted) in 3 existing families (pc27, pc28, pc29): the wanted look for that slot.
4. `../raw_A.png` and 5. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 2 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1024x1024 or larger:

- slot 43: casting: eyes squeezed shut, as in `consensus_43.png`, with the head as in input 1's window 1.
- slot 44: determined, lips parted, as in `consensus_44.png`, with the head as in input 1's window 2.

Hair, horns and ears kept as close to the head as in the identity master. No green, pink or red tint on the bone: the skull stays the same bone-white as frame 01 of sheet A.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
