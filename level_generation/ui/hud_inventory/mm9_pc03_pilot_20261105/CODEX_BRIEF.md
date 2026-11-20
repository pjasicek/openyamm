# Codex brief: MM9 PC03 as an MM6–MM8 player portrait sheet (pilot)

Scope: image generation only. Use your built-in image generation tool. Write only into
`level_generation/ui/hud_inventory/mm9_pc03_pilot_20261105/`. No builds, no other edits, no scripts that alter pixels.

You are doing ONE sheet: the sheet letter (A or B) is given in the command. Sheet A holds portrait slots 01–28,
sheet B slots 29–56.

## Inputs (attached in this order)

1. `template_<sheet>.png` — LAYOUT, FRAMING AND STYLE TARGET. 28 transparent portraits of an existing game
   character (a different young man) in 7 columns × 4 rows, read left to right then top to bottom.
   Sheet 1092×728, slots 156×182, each portrait window 118×158 at inset (19,12).
   It defines for every slot: the head size and position inside its window, the head angle and tilt, how much of
   the head is visible (partial heads in dodge states stay partial), the clean cut-out with only a short neck
   stub and no shoulders, the bright warm pre-rendered lighting, and the state treatment (tints, stone, closed eyes).
2. `source_<sheet>.png` — IDENTITY AND EXPRESSION SOURCE. The same 7×4 layout, filled with low-resolution frames
   of the NEW character from another game, one chosen frame per slot. These are busts on a navy background with a
   chain-mail collar; the background, collar and shoulders are NOT wanted.
3. `identity.png` — the new character's neutral face, larger. Use for facial identity detail.

## What to produce

One image: the NEW character (inputs 2 and 3: young man, longish dark-brown swept hair over the ears, long
narrow face, strong straight nose, prominent cheekbones, thin lips, blue eyes) drawn into the 28 slots of input 1,
so the result can replace the template character in the same game without looking out of place.

- Identity, hair shape and colour, and face proportions come from inputs 2 and 3. Do not copy the template's
  face, hairstyle or hair colour.
- Framing comes from input 1: same head height in its window, same horizontal centre, same lower cut-off with
  only a short neck stub, same head angle, tilt and gaze direction, same partial/low position for the dodge slots.
  No shoulders, collar, armour or clothing.
- Expression: copy the mouth, eyes and brows of the input 2 frame in the same slot, adjusted to the template's
  head angle. Where input 1 shows a state the source frame does not (sickly green poisoned skin, pustules,
  grey stone, red enraged face, closed eyes, bruise, sleeping tilt, head turns and nods), apply the template's
  state to the new character.
- Injury slots (sheet B slots 37–39, the 9th–11th portraits): show intact skin with faint bruising and a pained
  or dazed expression. No blood, cuts or open wounds.
- Style: finely detailed pre-rendered fantasy-game portrait matching input 1's lighting and colour (warm, evenly lit
  skin, natural saturation). Not the dark blue-rim lighting of input 2. Fresh high-resolution reconstruction
  with real fine detail; no pixel-art enlargement, blur-only smoothing or square texels.

## Transparency and layout

- Genuinely transparent RGBA background (alpha 0) outside each head. No checkerboard, no painted backdrop,
  no navy, no grey, no shadow, no halo. Clean thin antialiased edges.
- EXACTLY 7 columns × 4 rows, 28 separate portraits in reading order, generous uniform transparent gutters so
  no two portraits touch. Landscape around 1536×1024. No text, labels, borders, rings or guide marks.

## Records

- Copy the exact generated file, unmodified, to `raw_<sheet>.png` in the pilot folder. If the first result has a
  wrong grid count, touching portraits, a non-transparent background or the template's face instead of the new
  one, do ONE corrective regeneration and keep the first as `raw_<sheet>_rejected.png`.
- Write `generation_<sheet>.json`: exact prompt(s) used, input paths with sha256, output path, sha256, size,
  mode, and a one-paragraph self-check against the list above.
