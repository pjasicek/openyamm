# Codex brief: repair slots 6, 44, 56 of MM9 PC01

Scope: image generation only, built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_portraits/pc01/repair_06_44_56`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, 3 windows of 118x158 in 156x182 slots, left to right = slots 6, 44, 56
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus_06.png`: slot 6 (drunk: tilted, loose grin) in 4 existing families (pc05, 7pc01, pc07, 7pc02): the wanted look for that slot.
3. `consensus_44.png`: slot 44 (determined, lips parted) in 4 existing families (pc05, 7pc01, pc07, 7pc02): the wanted look for that slot.
4. `consensus_56.png`: slot 56 (shout, mouth wide open) in 4 existing families (pc05, 7pc01, pc07, 7pc02): the wanted look for that slot.
5. `../raw_A.png` and 6. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly 3 portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around 1536x1024 or larger:

- slot 6: drunk: tilted, loose grin, as in `consensus_06.png`, with the head as in input 1's window 1.
- slot 44: determined, lips parted, as in `consensus_44.png`, with the head as in input 1's window 2.
- slot 56: shout, mouth wide open, as in `consensus_56.png`, with the head as in input 1's window 3.

Hair, horns and ears kept as close to the head as in the identity master.

The thin grey-white braid hangs on his own LEFT side (the VIEWER'S RIGHT in a frontal view), exactly as in the
identity master; never mirror it to the other side. Slot 6 shows a loose, lopsided drunken grin (relaxed, slightly
heavy eyelids), not a scowl. Slot 56: irises and pupils visible, looking straight ahead or slightly down at the
viewer, never rolled up into white eyes.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
