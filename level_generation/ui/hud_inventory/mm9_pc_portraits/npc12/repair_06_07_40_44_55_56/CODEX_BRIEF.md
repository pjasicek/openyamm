# Codex brief: repair slots 6, 7, 40, 44, 55, 56 of MM9 NPC12

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc12/repair_06_07_40_44_55_56`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 6 windows of 118x158 in 156x182 slots, left to right = slots 6, 7, 40, 44, 55, 56
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc05, pc07, pc33):
   - row 1: slot 6 (drunk: tilted, loose grin)
   - row 2: slot 7 (insane: manic grin)
   - row 3: slot 40 (smile)
   - row 4: slot 44 (determined, lips parted)
   - row 5: slot 55 (grin)
   - row 6: slot 56 (shout, mouth wide open)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 6 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 3072x1024 or larger:

- slot 6: drunk: tilted, loose grin, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 7: insane: manic grin, as in row 2 of `consensus.png`, with the head as in input 1's window 2. Normal
  even teeth: no fangs, no vampire teeth, no drool (the sheet's first slot 7 wrongly had fangs).
- slot 40: smile, as in row 3 of `consensus.png`, with the head as in input 1's window 3.
- slot 44: determined, lips parted, as in row 4 of `consensus.png`, with the head as in input 1's window 4.
- slot 55: grin, as in row 5 of `consensus.png`, with the head as in input 1's window 5.
- slot 56: shout, mouth wide open, as in row 6 of `consensus.png`, with the head as in input 1's window 6.

The character: male elf in his thirties, fair light skin with a cool pale tone, clean-shaven; straight shoulder-length ash-blonde hair (greyish blond, not golden) combed back from the forehead with no fringe, falling straight down both sides of the face to the jaw and shoulders; long pointed elf ears that stick out sideways through the hair at eye level on both sides, keep the ears long and clearly visible; long face with a strong square jaw and firm chin, high cheekbones, long straight nose, thin lips, deep-set dark blue eyes under straight brown brows; no jewellery on the head. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
