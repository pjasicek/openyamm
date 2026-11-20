# Codex brief: repair slots 48 of MM9 NPC08

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc08/repair_48`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 1 windows of 118x158 in 156x182 slots, left to right = slots 48
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc05, 7pc02, 7pc01):
   - row 1: slot 48 (smug closed-mouth smile)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 1 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1024x1024 or larger:

- slot 48: smug closed-mouth smile, as in row 1 of `consensus.png`, with the head as in input 1's window 1.

The character: young man in his early twenties, fair light skin with a warm light-tan tone, clean-shaven; light ash-brown hair, straight and smooth, combed straight back from the forehead with no fringe or parting, ear length at the sides and nape, neat and close to the head; long narrow face, angular jaw, high cheekbones, slightly hollow cheeks, long straight nose, thin lips, large blue eyes under straight light-brown brows; no jewellery on the head. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
