# Codex brief: repair slots 2, 5, 40, 47 of MM9 NPC07

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc07/repair_02_05_40_47`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 4 windows of 118x158 in 156x182 slots, left to right = slots 2, 5, 40, 47
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc02, pc31, 7pc05):
   - row 1: slot 2 (cursed: heavy-lidded, drained)
   - row 2: slot 5 (fear: wide eyes, open mouth)
   - row 3: slot 40 (smile)
   - row 4: slot 47 (eyes closed, calm)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 4 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 2048x1024 or larger:

- slot 2: cursed: heavy-lidded, drained, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 5: fear: wide eyes, open mouth, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 40: smile, as in row 3 of `consensus.png`, with the head as in input 1's window 3.
- slot 47: eyes closed, calm, as in row 4 of `consensus.png`, with the head as in input 1's window 4.

The character: young woman in her twenties, fair pale skin with a soft pink flush, long full ash-blonde hair with a slightly frizzy wave, a straight thick fringe cut just above the eyebrows, and two thick plaited braids that hang from behind the ears down in front of the neck on BOTH sides, symmetric, ending below the jaw; oval face, high soft cheekbones, small straight nose, dark brown eyes with heavy dark smoky eye make-up on the upper lids, thin arched brows hidden under the fringe, full lips with glossy pink-magenta lipstick; no jewellery on the head. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
