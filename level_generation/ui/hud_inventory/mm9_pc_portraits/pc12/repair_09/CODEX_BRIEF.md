# Codex brief: repair slots 9 of MM9 PC12

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_09`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 1 windows of 118x158 in 156x182 slots, left to right = slots 9
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc20, pc31, pc04, 7pc07):
   - row 1: slot 9 (diseased: pustules)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.
   EXCEPTION: the 9th portrait of `raw_A.png` (row 2, second from left, the diseased one) is WRONG: it shows the
   template character's face (round face, soft curly hair, no forehead tattoo) instead of the new character. That
   wrong frame is what this repair replaces; never copy its face or hair.

Input 1 also shows that other character (curly hair, rounder face): take only head size, position, angle and crop
from it, never its face, hair or skin. The new character's forehead glyph tattoo stays visible through the
pustules, and her messy shoulder-length hair, face shape and pale grey eyes are exactly as in her other frames.

## Produce

One image with exactly 1 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1024x1024 or larger:

- slot 9: diseased: pustules, as in row 1 of `consensus.png`, with the head as in input 1's window 1.

The character: young half-orc woman, warm medium-dark brown skin (keep it brown in every frame), no horns, no earrings; messy shoulder-length dark brown-black hair, tousled and layered, loosely parted near the centre and falling around the face and over the ears; a dark tribal glyph tattoo across the forehead made of two matching angular clusters either side of the centre line, part of her skin; dark eyeliner around pale grey eyes, thin arched brows, rounded cheekbones, broad nose, full lips, a softly rounded chin. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
