# Codex brief: repair slots 5, 18, 40, 48, 52 of MM9 NPC10

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc10/repair_05_18_40_48_52`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 5 windows of 118x158 in 156x182 slots, left to right = slots 5, 18, 40, 48, 52
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc04, 7pc05, 7pc07):
   - row 1: slot 5 (fear: wide eyes, open mouth)
   - row 2: slot 18 (glance to its own left (viewer's right), head nearly frontal)
   - row 3: slot 40 (smile)
   - row 4: slot 48 (smug closed-mouth smile)
   - row 5: slot 52 (slight smile)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 5 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 2560x1024 or larger:

- slot 5: fear: wide eyes, open mouth, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 18: glance to its own left (viewer's right), head nearly frontal, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 40: smile, as in row 3 of `consensus.png`, with the head as in input 1's window 3.
- slot 48: smug closed-mouth smile, as in row 4 of `consensus.png`, with the head as in input 1's window 4.
- slot 52: slight smile, as in row 5 of `consensus.png`, with the head as in input 1's window 5.

The character: young woman in her twenties, pale fair skin with strong rosy-pink blush on both cheeks, light reddish-brown (ginger-tinged light brown) chin-length bob haircut, smooth and full, swept back from a high forehead with a slight side parting, rounded volume around the crown and ears, ends curving in at jaw level (short hair, nothing below the jaw); oval face, softly rounded chin, small straight nose, dark brown eyes with dark winged eyeliner on the upper lids, thin light-brown brows with slightly raised inner ends giving a gentle worried look, full lips in pale pink; small earrings are not visible; no jewellery on the head. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
