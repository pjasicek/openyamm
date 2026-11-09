# Codex brief: repair slots 5, 44, 53, 54, 56 of MM9 PC10

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc10/repair_05_44_53_54_56`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 5 windows of 118x158 in 156x182 slots, left to right = slots 5, 44, 53, 54, 56
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families (pc02, 7pc05, pc12):
   - row 1: slot 5 (fear: wide eyes, open mouth)
   - row 2: slot 44 (determined, lips parted)
   - row 3: slot 53 (angry)
   - row 4: slot 54 (enraged: red face, snarl)
   - row 5: slot 56 (shout, mouth wide open)
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 5 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 2560x1024 or larger:

- slot 5: fear: wide eyes, open mouth, as in row 1 of `consensus.png`, with the head as in input 1's window 1.
- slot 44: determined, lips parted, as in row 2 of `consensus.png`, with the head as in input 1's window 2.
- slot 53: angry, as in row 3 of `consensus.png`, with the head as in input 1's window 3.
- slot 54: enraged: red face, snarl, as in row 4 of `consensus.png`, with the head as in input 1's window 4.
- slot 56: shout, mouth wide open, as in row 5 of `consensus.png`, with the head as in input 1's window 5.

The character: young half-orc woman with cool ashen grey-brown skin (a muted greyish brown, never green and never pinkish-white), no horns; short black hair shaved close at the sides with a short spiky black crest on top of the head and long thin blue-grey streaked strands falling from behind the ears down both sides of the neck; long pointed ears swept back from the sides of the head; one small gold hoop earring in each earlobe; heavy dark smoky shadow around pale green-grey eyes; strong brow, wide cheekbones, broad flat nose, very full dark plum lips, narrow chin, no tattoos. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears kept as close to the head as in the identity master.

Make each expression read clearly at portrait size, as strong as in the consensus rows: 5 wide-eyed fear with the mouth open and brows raised; 44 lips parted; 53 angry, frontal head; 54 enraged, frontal head, face flushed darker red-brown, teeth bared in a snarl; 56 shouting with the mouth wide open. Slots 53 and 54 face the viewer as in input 1, not turned.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
