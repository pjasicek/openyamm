# Codex brief: repair slots 2, 5, 24, 44 of MM9 NPC14

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc14/repair_02_05_24_44`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 4 windows of 118x158 in 156x182 slots, left to right = slots 2, 5, 24, 44
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc07, pc34, 7pc01):
   - row 1: slot 2 (cursed: heavy-lidded, drained)
   - row 2: slot 5 (fear: wide eyes, open mouth)
   - row 3: slot 24 (talk: O mouth)
   - row 4: slot 44 (determined, lips parted)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 4 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 2048x1024 or larger:

- slot 2: cursed: heavy-lidded, drained, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 5: fear: wide eyes, open mouth, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 24: talk: O mouth, as in row 3 of `consensus.png`, with the head as in input 1's window 3.
- slot 44: determined, lips parted, as in row 4 of `consensus.png`, with the head as in input 1's window 4.

The character: warrior chieftain in his forties, dark brown skin, broad face, strong cheekbones, broad flat nose, full lips, narrowed dark-brown eyes under heavy black brows, stern proud look, thin black moustache drooping past the corners of the mouth and a short pointed black goatee on the chin, the cheeks shaven; long black hair in thin braids hanging straight down from under the helmet on both sides to below the jaw, close to the cheeks; he always wears the same helmet, which is part of the head: a rounded glossy black iron skullcap with a short straight ivory spike rising from the centre front, two smooth ivory horns rising from the sides and curving up and inward like a crescent (moderate size, staying close to the head), and a thick shaggy grey-brown fur band around the rim, covering the forehead to just above the brows and the ears; the helmet keeps the same shape, colours and size in every portrait and is never removed. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
