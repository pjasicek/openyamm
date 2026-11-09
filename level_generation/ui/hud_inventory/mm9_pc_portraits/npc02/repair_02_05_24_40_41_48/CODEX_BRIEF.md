# Codex brief: repair slots 2, 5, 24, 40, 41, 48 of MM9 NPC02

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc02/repair_02_05_24_40_41_48`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 6 windows of 118x158 in 156x182 slots, left to right = slots 2, 5, 24, 40, 41, 48
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc05, pc07, 7pc02):
   - row 1: slot 2 (cursed: heavy-lidded, drained)
   - row 2: slot 5 (fear: wide eyes, open mouth)
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
- slot 5: fear: wide eyes, open mouth, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 24: talk: O mouth, as in row 3 of `consensus.png`, with the head as in input 1's window 3.
- slot 40: smile, as in row 4 of `consensus.png`, with the head as in input 1's window 4.
- slot 41: wide smile, as in row 5 of `consensus.png`, with the head as in input 1's window 5.
- slot 48: smug closed-mouth smile, as in row 6 of `consensus.png`, with the head as in input 1's window 6.

The character: half-orc man around thirty, dark brown skin with a slight reddish-mauve tone (keep it dark brown in every frame, never lighter tan and never green), head shaved bald with only a faint dark stubble on the crown, no hair, clean-shaven, no beard or moustache; small short ivory-white horns: a pointed horn growing up and outward from the upper forehead on his own LEFT side (the VIEWER'S RIGHT in a frontal view), a smaller horn sticking sideways out of his own RIGHT temple (VIEWER'S LEFT), and a tiny horn nub at his own left temple; a small dark blue-black angular stone or scale stud set in the upper forehead on his own RIGHT side (VIEWER'S LEFT); a ragged dark tribal scar-tattoo line runs across the forehead between the stud and the left horn, and dark mottled tattoo scarring covers the skin around his own LEFT eye and down his own LEFT cheek (VIEWER'S RIGHT); these markings are part of his skin and keep their sides when the head turns or tilts, never mirrored; long gaunt face with high prominent cheekbones and hollow cheeks, heavy brow, broad flat nose, thick lips, slightly pointed ears close to the head, pale glassy grey eyes. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
