# Codex brief: repair slots 6 of MM9 PC02

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc02/repair_06`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 1 windows of 118x158 in 156x182 slots, left to right = slots 6
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus_06.png`: slot 6 (drunk: tilted, loose grin) in 4 existing families (pc02, pc04, pc06, pc36): the wanted look for that slot.
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 1 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1024x1024 or larger:

- slot 6: drunk: tilted, loose grin, as in `consensus_06.png`, with the head as in input 1's window 1.

Hair, horns and ears kept as close to the head as in the identity master.

Slot 6 must read as tipsy at a glance: head tilted as in input 1, a loose, lopsided open-mouthed grin showing
some upper teeth, heavy relaxed eyelids, slightly unfocused gaze; not a polite closed smile. No earrings or studs.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
