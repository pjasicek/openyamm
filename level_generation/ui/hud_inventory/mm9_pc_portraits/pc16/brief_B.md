# Codex brief: MM9 PC16 as an MM6-MM8 player portrait sheet, sheet B

Scope: image generation only, with your built-in image generation tool. Write only into
`level_generation/ui/hud_inventory/mm9_pc_portraits/pc16`. No builds, no other edits, no scripts that alter pixels.

Sheet B holds portrait slots 29-56.

## Inputs (attached in this order)

1. `template_B.png`: LAYOUT, FRAMING AND STYLE TARGET. 28 transparent portraits of existing game characters
   (not the new character) in 7 columns x 4 rows, read left to right then top to bottom. Sheet 1092x728,
   slots 156x182, each portrait window 118x158 at inset (19,12). For every slot it defines the head size and
   position inside its window, the head angle and tilt, how much of the head is visible (partial heads stay
   partial), the clean cut-out with only a short neck stub and no shoulders, the bright warm pre-rendered
   lighting, and the state treatment (tints, stone, closed eyes, bruises).
2. `source_B.png`: IDENTITY AND EXPRESSION SOURCE. The same layout filled with low-resolution frames of
   the NEW character from another game, one chosen frame per slot. Busts on a coloured background with clothing;
   background, clothing and shoulders are NOT wanted.
3. `identity.png`: the new character's neutral face, larger.
4. `raw_A.png`: the ACCEPTED sheet A of this same character (transparent; view it over a solid colour). It is the
   identity master for this sheet: the same hair (volume, length, wave, parting, colour; not bigger or curlier),
   skin tone, face shape, lighting and rendering as sheet A.

## What to produce

One image: the NEW character (young dwarf woman in her early twenties with a soft youthful face, voluminous near-black hair (very dark espresso brown, much darker than any template hair, never chestnut or medium brown) in tight curls with a soft centre parting, full on top and falling at both sides in long spiral ringlets, small gold hoop earrings in both ears, no headband, smooth oval face with soft jaw and rounded chin, fair skin with rosy cheeks, straight nose, blue-grey eyes, dark straight brows, full lips with a soft red tint, no beard) drawn into the 28 slots of input 1, so the result can replace the
template characters in the same game without looking out of place.

- Identity, hair shape and colour, horns, ears, beard, skin colour and face proportions come from inputs 2
  and 3 and the sheet A identity master. Do not copy the template's face, hair, skin colour or accessories.
- Framing comes from input 1: same head height in its window, same horizontal centre, same lower cut-off with
  only a short neck stub, same head angle, tilt and gaze direction, same partial/low position for ducking slots.
  No shoulders, collar, armour or clothing. Keep hair, horns and ears as close to the head as the native frames
  allow, so the head is no wider than the template's head plus its hair.
- Expression: copy the mouth, eyes and brows of the input 2 frame in the same slot, adjusted to the template's
  head angle. Where input 1 shows a state the source frame does not (sickly green poisoned skin, pustules, grey
  stone, red straining face, closed eyes, bruise, sleeping tilt, head turns and nods, glances), apply the
  template's state to the new character.
- Injury slots (sheet B slots 37-39, the 9th-11th portraits): intact skin with faint bruising and a pained or
  dazed expression. No blood, cuts or open wounds.
- Style: finely detailed pre-rendered fantasy-game portrait matching input 1's lighting and colour (warm, evenly
  lit, natural saturation), not the dark coloured rim lighting of input 2. Fresh high-resolution reconstruction
  with real fine detail; no pixel-art enlargement, blur-only smoothing or square texels.

## Head scale (added after a rejected first sheet B)

- Draw every head at exactly the same pixel size as in `raw_A.png`. In a frontal slot the face (hairline to
  chin) and the cheek-to-cheek width must equal sheet A's frontal faces, and the head with its hair must fill
  the same fraction of its cell (about 170 x 217 px per head on a 1536 x 1024 sheet, as in sheet A).
- The hair keeps sheet A's looser shoulder-length ringlets and the same width beside the face; no tighter,
  bushier or wider curls.
- The rejected first attempt drew every face about 12 % larger than sheet A with wider, tighter curls. Before
  saving, compare a frontal slot of your result with sheet A's first portrait at the same scale.

## Transparency and layout

- Genuinely transparent RGBA background (alpha 0) outside each head. No checkerboard, painted backdrop,
  shadow or halo. Clean thin antialiased edges. Transparency can look brown or grey in a preview: check the
  alpha channel before rejecting a result for its background.
- EXACTLY 7 columns x 4 rows, 28 separate portraits in reading order, generous uniform transparent gutters so
  no two portraits touch. Landscape around 1536x1024. No text, labels, borders, rings or guide marks.

## Records

- Copy the exact generated file, unmodified, to `raw_B.png`. If the result has a wrong grid count,
  touching portraits, no real transparency or the template's face instead of the new one, do ONE corrective
  regeneration and keep the first as `raw_B_rejected.png`.
- Write `generation_B.json`: exact prompt(s), input paths with sha256, output path, sha256, size, mode,
  and a one-paragraph self-check against this brief.
