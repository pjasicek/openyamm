# Codex brief: repair slots 2, 18, 24, 40, 41, 48 of MM9 NPC15

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc15/repair_02_18_24_40_41_48`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 6 windows of 118x158 in 156x182 slots, left to right = slots 2, 18, 24, 40, 41, 48
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc05, pc07, 7pc02):
   - row 1: slot 2 (cursed: heavy-lidded, drained)
   - row 2: slot 18 (glance to its own left (viewer's right), head nearly frontal)
   - row 3: slot 24 (talk: O mouth)
   - row 4: slot 40 (smile)
   - row 5: slot 41 (wide smile)
   - row 6: slot 48 (smug closed-mouth smile)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 6 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 3072x1024 or larger:

- slot 2: cursed: heavy-lidded, drained, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 18: glance to its own left (viewer's right), head nearly frontal, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 24: talk: O mouth, as in row 3 of `consensus.png`, with the head as in input 1's window 3.
- slot 40: smile, as in row 4 of `consensus.png`, with the head as in input 1's window 4.
- slot 41: wide smile, as in row 5 of `consensus.png`, with the head as in input 1's window 5.
- slot 48: smug closed-mouth smile, as in row 6 of `consensus.png`, with the head as in input 1's window 6.

The character: human man in his thirties, warm medium-brown skin with a reddish tone (keep it brown in every frame, never pale), very short close-cropped dark-brown hair with a rounded hairline, no ponytail, no crest and no long hair at the back; a thin dark-brown moustache joined at the mouth corners to a short pointed goatee on the chin (a circle beard), the cheeks and jaw clean-shaven; strong heavy dark brows, green eyes, broad straight nose, full lips, square jaw; no jewellery on the head. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
