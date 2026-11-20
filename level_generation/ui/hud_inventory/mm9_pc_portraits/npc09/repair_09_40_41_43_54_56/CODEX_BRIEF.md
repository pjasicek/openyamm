# Codex brief: repair slots 9, 40, 41, 43, 54, 56 of MM9 NPC09

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/repair_09_40_41_43_54_56`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 6 windows of 118x158 in 156x182 slots, left to right = slots 9, 40, 41, 43, 54, 56
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc05, pc07, pc01):
   - row 1: slot 9 (diseased: pustules)
   - row 2: slot 40 (smile)
   - row 3: slot 41 (wide smile)
   - row 4: slot 43 (casting: eyes squeezed shut)
   - row 5: slot 54 (enraged: red face, snarl)
   - row 6: slot 56 (shout, mouth wide open)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 6 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 3072x1024 or larger:

- slot 9: diseased: pustules, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 40: smile, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 41: wide smile, as in row 3 of `consensus.png`, with the head as in input 1's window 3.
- slot 43: casting: eyes squeezed shut, as in row 4 of `consensus.png`, with the head as in input 1's window 4. Normal skin colour,
  never green (the sheet's first slot 43 wrongly had poisoned green skin).
- slot 54: enraged: red face, snarl, as in row 5 of `consensus.png`, with the head as in input 1's window 5. The whole face
  flushed strongly red, eyes narrowed.
- slot 56: shout, mouth wide open, as in row 6 of `consensus.png`, with the head as in input 1's window 6.

The character: burly human man in his forties, fair pale skin with a warm pink tone, completely bald smooth shiny dome on top: no hair on the crown or forehead; short bushy curly mid-brown hair only around the sides and back of the head, below the dome, merging into a huge bushy curly mid-brown beard that starts at the cheekbones, covers the jaw, cheeks and chin and spreads wide and round below the face; a thin dark-brown moustache over the mouth, dark straight brows, calm blue eyes with slightly heavy lids (never bulging or staring), straight nose, the mouth only visible as lips inside the beard; keep the beard full and wide like a big round bush but within the portrait. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
