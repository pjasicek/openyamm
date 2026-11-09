# Codex brief: repair slots 5, 8, 9, 11 of MM9 NPC03

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc03/repair_05_08_09_11`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 4 windows of 118x158 in 156x182 slots, left to right = slots 5, 8, 9, 11
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc04, pc06, pc31):
   - row 1: slot 5 (fear: wide eyes, open mouth)
   - row 2: slot 8 (poisoned: sickly green skin)
   - row 3: slot 9 (diseased: pustules)
   - row 4: slot 11 (unconscious: eyes closed, bruise, tilted)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 4 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 2048x1024 or larger:

- slot 5: fear: wide eyes, open mouth, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 8: poisoned: sickly green skin, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 9: diseased: pustules, as in row 3 of `consensus.png`, with the head as in input 1's window 3.
- slot 11: unconscious: eyes closed, bruise, tilted, as in row 4 of `consensus.png`, with the head as in input 1's window 4.

The character: young elf woman in her twenties, smooth light-tan skin, very long straight pure white (silver-white, not blonde, not grey) hair parted in the middle, combed smoothly back over the crown and falling straight down behind the ears and past the shoulders on BOTH sides in flat smooth sheets that hang close to the neck (never puffed out sideways, no braids, no fringe); long pointed elf ears that poke out through the hair and keep their full size; a slim gold circlet on the forehead shaped as a shallow V (chevron) dipping to a point between the brows, with a small round red gem at the centre, worn just above the brows and running into the hair at the temples; oval face with a narrow pointed chin, high cheekbones, straight narrow nose, dark blue eyes, thin dark arched brows, full lips in natural rose-beige, light eye make-up; no earrings. Keep eye colour, hair colour and every feature exactly as in the identity master.
The gold V-shaped circlet with its red gem is part of her head in EVERY state: draw it in all four slots, including poisoned (8), diseased (9) and unconscious (11). The old windows 8, 9 and 11 of `raw_A.png` lack it by mistake; those are exactly the frames being replaced, so do not copy that.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
