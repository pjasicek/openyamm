# Codex brief: repair slots 2, 6, 44 of MM9 NPC01

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc01/repair_02_06_44`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 3 windows of 118x158 in 156x182 slots, left to right = slots 2, 6, 44
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc07, pc34, pc35):
   - row 1: slot 2 (cursed: heavy-lidded, drained)
   - row 2: slot 6 (drunk: tilted, loose grin)
   - row 3: slot 44 (determined, lips parted)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 3 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1536x1024 or larger:

- slot 2: cursed: heavy-lidded, drained, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 6: drunk: tilted, loose grin, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 44: determined, lips parted, as in row 3 of `consensus.png`, with the head as in input 1's window 3.

The character: young man in his mid-twenties, warm light-tan skin, clean-shaven with a faint dark stubble shadow on the jaw and upper lip, broad square jaw, straight medium nose, wide mouth with a full lower lip, grey-blue eyes under straight dark-brown brows, calm steady look; he always wears the same leather helmet, which is part of the head: a rounded dark-brown boiled-leather skullcap built from vertical segments with raised seams, sitting low just above the brows, a dark leather brow band with a row of small round silver rivets, one round polished brass boss at the centre of the brow band above the nose, and two long soft dark-brown leather ear flaps hanging straight down from the brow band on both sides, covering the ears and reaching just below the jaw, close to the cheeks; no hair shows except a few short dark-brown strands at the temples; the helmet keeps the same shape, colours and size in every portrait, turns with the head and is never removed. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
