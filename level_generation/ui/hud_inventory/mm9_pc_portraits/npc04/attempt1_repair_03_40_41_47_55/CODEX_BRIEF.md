# Codex brief: repair slots 3, 40, 41, 47, 55 of MM9 NPC04

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc04/repair_03_40_41_47_55`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 5 windows of 118x158 in 156x182 slots, left to right = slots 3, 40, 41, 47, 55
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (7pc04, 7pc14, pc34):
   - row 1: slot 3 (weak: eyes almost closed, tired)
   - row 2: slot 40 (smile)
   - row 3: slot 41 (wide smile)
   - row 4: slot 47 (eyes closed, calm)
   - row 5: slot 55 (grin)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 5 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 2560x1024 or larger:

- slot 3: weak: eyes almost closed, tired, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 40: smile, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 41: wide smile, as in row 3 of `consensus.png`, with the head as in input 1's window 3.
- slot 47: eyes closed, calm, as in row 4 of `consensus.png`, with the head as in input 1's window 4.
- slot 55: grin, as in row 5 of `consensus.png`, with the head as in input 1's window 5.

The character: stocky dwarf man in his forties, weathered ruddy tanned skin, broad face with prominent cheekbones, heavy straight nose with a broad tip, deep-set pale blue eyes under heavy dark furrowed brows, stern down-turned mouth with thin lips, a full bushy grey-brown beard and moustache covering the jaw and chin; he always wears the same fur hood, which is part of the head: shaggy grey-brown fur, closely framing the face like a parka hood, covering the crown, the sides of the head and the ears and joining the beard under the jaw, with a dark red leather headband running straight across the forehead over the fur just above the brows; no hair or ears show; the hood keeps the same shape, colour and size in every portrait, is no wider than a dwarf's bushy hair, and is never removed. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
