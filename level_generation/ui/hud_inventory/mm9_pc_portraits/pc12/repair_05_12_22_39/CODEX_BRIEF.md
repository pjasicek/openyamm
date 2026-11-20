# Codex brief: repair slots 5, 12, 22, 39 of MM9 PC12

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 4 windows of 118x158 in 156x182 slots, left to right = slots 5, 12, 22, 39
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus_05.png`: slot 5 (fear: wide eyes, open mouth) in 3 existing families (pc02, pc12, 7pc05): the wanted look for that slot.
3. `consensus_12.png`: slot 12 (petrified: grey stone) in 3 existing families (pc02, pc12, 7pc05): the wanted look for that slot.
4. `consensus_22.png`: slot 22 (talk: mouth open) in 3 existing families (pc02, pc12, 7pc05): the wanted look for that slot.
5. `consensus_39.png`: slot 39 (hit, major: battered, mouth open) in 3 existing families (pc02, pc12, 7pc05): the wanted look for that slot.
6. `../raw_A.png` and 7. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 4 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 2048x1024 or larger:

- slot 5: fear: wide eyes, open mouth, as in `consensus_05.png`, with the head as in input 1's window 1.
- slot 12: petrified: grey stone, as in `consensus_12.png`, with the head as in input 1's window 2.
- slot 22: talk: mouth open, as in `consensus_22.png`, with the head as in input 1's window 3.
- slot 39: hit, major: battered, mouth open, as in `consensus_39.png`, with the head as in input 1's window 4.

Hair, horns and ears kept as close to the head as in the identity master.

Slot 12 is the whole head turned to grey stone: carve the NEW character's own messy, tousled shoulder-length hair and forehead tattoo in stone (not the braided hair of the sheet A stone frame or of input 1). Slot 39 is dazed after a heavy blow: head thrown back, mouth open, faint bruising, no blood.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
