# Codex brief: repair slots 18 and 48 of the MM9 PC03 pilot

Scope: image generation only, built-in image generation tool. Write only into
`level_generation/ui/hud_inventory/mm9_pc03_pilot_20261105/repair_18_48/`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png` — framing target, two 118×158 windows in 156×182 slots: left = slot 18, right = slot 48 of an
   existing game character (a different young man). Copy head size, position, angle and crop (short neck stub,
   no shoulders) from it.
2. `consensus_18.png` — slot 18 in four existing families: a glance. The eyes look toward the CHARACTER'S OWN
   LEFT (the viewer's right side of the image); the head stays nearly frontal or turns only slightly.
3. `consensus_48.png` — slot 48 in four existing families: a pleased, confident closed-mouth smile (smug,
   satisfied), eyes open and relaxed.
4. `../raw_A.png` and 5. `../raw_B.png` — the accepted sheets of the NEW character (transparent; view over a
   solid colour). They are the identity master: same face, hair (volume, wave, parting, colour), skin, lighting
   and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly TWO portraits of the new character side by side on a genuinely transparent RGBA
background (alpha 0 outside the heads), with a wide transparent gap between them, no text or borders,
around 1024×768 or larger:

- left, slot 18: the head as in input 1's left window; eyes clearly glancing to the character's own left
  (viewer's right), mouth relaxed and closed, neutral brows.
- right, slot 48: frontal head as in input 1's right window; confident closed-mouth smile as in input 3.

Hair kept as close to the head as in the identity master, so the head is no wider than in raw_A.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
