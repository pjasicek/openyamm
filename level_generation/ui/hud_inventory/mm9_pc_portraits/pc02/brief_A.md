# Codex brief: MM9 PC02 as an MM6-MM8 player portrait sheet, sheet A

Scope: image generation only, with your built-in image generation tool. Write only into
`level_generation/ui/hud_inventory/mm9_pc_portraits/pc02`. No builds, no other edits, no scripts that alter pixels.

Sheet A holds portrait slots 01-28.

## Inputs (attached in this order)

1. `template_A.png`: LAYOUT, FRAMING AND STYLE TARGET. 28 transparent portraits of existing game characters
   (not the new character) in 7 columns x 4 rows, read left to right then top to bottom. Sheet 1092x728,
   slots 156x182, each portrait window 118x158 at inset (19,12). For every slot it defines the head size and
   position inside its window, the head angle and tilt, how much of the head is visible (partial heads stay
   partial), the clean cut-out with only a short neck stub and no shoulders, the bright warm pre-rendered
   lighting, and the state treatment (tints, stone, closed eyes, bruises).
2. `source_A.png`: IDENTITY AND EXPRESSION SOURCE. The same layout filled with low-resolution frames of
   the NEW character from another game, one chosen frame per slot. Busts on a coloured background with clothing;
   background, clothing and shoulders are NOT wanted.
3. `identity.png`: the new character's neutral face, larger.

## What to produce

One image: the NEW character (young woman in her twenties, straight shoulder-length ash-blonde hair, darker light-brown at the crown and lighter towards the ends, with a slight side parting and a few strands lifted at the top, falling past the ears to just above the shoulders; pale fair skin, oval face with a softly pointed chin, high cheekbones, slim straight nose, full lips, dark blue eyes with dark lashes, slender arched brows, no jewellery) drawn into the 28 slots of input 1, so the result can replace the
template characters in the same game without looking out of place.

- Identity, hair shape and colour, horns, ears, beard, skin colour and face proportions come from inputs 2
  and 3. Do not copy the template's face, hair, skin colour or accessories.
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

## Transparency and layout

- Genuinely transparent RGBA background (alpha 0) outside each head. No checkerboard, painted backdrop,
  shadow or halo. Clean thin antialiased edges. Transparency can look brown or grey in a preview: check the
  alpha channel before rejecting a result for its background.
- EXACTLY 7 columns x 4 rows, 28 separate portraits in reading order, generous uniform transparent gutters so
  no two portraits touch. Landscape around 1536x1024. No text, labels, borders, rings or guide marks.

## Records

- Copy the exact generated file, unmodified, to `raw_A.png`. If the result has a wrong grid count,
  touching portraits, no real transparency or the template's face instead of the new one, do ONE corrective
  regeneration and keep the first as `raw_A_rejected.png`.
- Write `generation_A.json`: exact prompt(s), input paths with sha256, output path, sha256, size, mode,
  and a one-paragraph self-check against this brief.
