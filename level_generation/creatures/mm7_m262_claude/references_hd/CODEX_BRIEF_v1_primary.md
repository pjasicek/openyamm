# Codex brief (run 1): HD three-quarter primary and knife prop sheet for the MM7 Harpy (m262)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m262_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces the primary `00_three_quarter.png` and one prop sheet `knife.png`. The four orthographic views are
a later, separate run. Use your built-in image generation. Record format: like
`level_generation/creatures/mm7_m398_claude/references_hd/generation_runs.json` (id, family `m262`, role `primary` /
`prop`, prompt, inputs with sha256, output path, selected flag, reason, superseded runs). Raw returns under `raw/`.

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m262/native/m262wa0.png` — ORIGINAL native front frame (she always hovers; this is her standing frame).
   Design, proportions and palette authority.
2. `mm7_m262/native/m262wa1.png` — ORIGINAL native front three-quarter.
3. `mm7_m262/native/m262wa2.png` — ORIGINAL native side profile (curved knife in her right hand, tail feathers).
4. `mm7_m262/native/m262wa3.png` — ORIGINAL native rear three-quarter.
5. `mm7_m262/native/m262wa4.png` — ORIGINAL native back.
6. `mm7_m262/aligned_2x/m262wa1.png` — restored 2x three-quarter view, for SURFACE MATERIAL ONLY (feathers, skin,
   metal finish). It never sets the design, pose or proportions.

The sprites show a short curved knife in her RIGHT hand. The 3D model gets the knife as a separate prop, so the body
reference must show her EMPTY-HANDED.

## Deliverable 1: `00_three_quarter.png` (primary)

Landscape 1536 x 1024, true transparent background, unresized return. Front-right three-quarter (camera 40-45 deg
toward the figure's own RIGHT side), chest height, slightly above, near-orthographic.

### Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Harpy monster from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1536 x 1024 landscape PNG with a genuine transparent background. ONE complete figure, from the
top of the hair to the talons AND both complete wings to their tips, centred, generous margins, near-orthographic
camera, no floor, no shadow, no scenery, no text. Even soft neutral studio light (no dramatic or rim light, no glow)
that still shows form. Credible, fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): a lean, wiry, middle-aged harpy woman: human upper body, bird lower body.
- HEAD: a gaunt stern face with a sharp nose and high cheekbones, tan-olive skin, dark eyes; long silver-white hair
  swept straight back from the forehead into a crest down the back of the head and the nape.
- TORSO: bare lean tan-olive human torso and shoulders; a silver metal bodice of two cups with gold edges and a gold
  band under the bust, covering the breasts; a narrow gold belt band at the waist.
- ARMS: two human arms, lean and sinewy, tan-olive skin; a long teal-green metal bracer with gold rims on each forearm;
  bare human hands with five fingers each (long fingers).
- LOWER BODY: from the hips down a BIRD: thick dark brown mottled feathers cover the hips and thighs like feathered
  trousers down to the knees, a short fan of dark brown tail feathers behind; below the feathers long bare orange
  scaly bird legs (tarsi) and big orange bird feet, each with three long forward toes and one back toe, curved dark
  talons.
- WINGS: two large feathered bird wings attached at the shoulder blades behind the shoulders: dark brown mottled
  coverts near the body, long teal-green flight feathers (primaries and secondaries) with a metallic sheen, as in the
  native sprites.

Pose: a neutral A-pose for rigging. Standing upright on the toes of both bird feet, legs straight down and apart with
a clear gap of air between the legs and between the feet, talons spread. Arms hang down and out to the sides at about
35 degrees from vertical, elbows very slightly bent, a clear gap of air between each arm and the body. Both hands
EMPTY, open and relaxed, five fingers slightly apart. Head level, looking forward. WINGS spread wide and raised in an
open V (leading edges rising about 30-40 degrees above horizontal from the shoulders), feathers fully open, the
trailing edge of each wing above the elbows and clear of the arms and the head.

Do NOT: draw the knife or any weapon; add armour beyond the bodice, bracers and belt band; add clothing on the bird
legs; add extra arms, extra wings, a beak or bird head; show nipples or nudity (the bodice covers the breasts); change
the colours; make her young or cartoonish; crop the wing tips, hair or talons; add a floor, shadow or text.

INPUT ROLES: Inputs 1–5 are the native views (front, front three-quarter, side, rear three-quarter, back): design,
proportions and palette authority; magenta/black/transparent pixels are background, not part of the harpy. Input 6
is the restored three-quarter: SURFACE MATERIAL ONLY.
CAMERA: FRONT-RIGHT THREE-QUARTER (face and toes toward SCREEN-LEFT), chest height slightly above. FRAMING / ALPHA:
whole figure and both wings inside the frame with margins, genuine RGBA alpha. Return exactly 1536 x 1024 unresized.

### Checks before selecting

- front-right three-quarter camera, whole figure and both wing tips inside the frame, 1536 x 1024, true alpha;
- empty hands with five fingers; human arms AND separate wings on the back;
- silver-white swept-back hair, silver bodice covering the bust, teal bracers;
- brown feathered thighs, orange scaly bird legs and feet with four toes and talons, short tail fan;
- A-pose with the stated gaps; wings in an open V clear of the arms and head.
If the first return fails a check, do ONE targeted corrective regeneration, then select the better of the two and
note any residual fault. Do not chase minor differences.

## Deliverable 2: `knife.png` (prop sheet)

Landscape 1536 x 1024, transparent background, flat diffuse studio light, no ground, shadow or text, no hand.
Two large views of the SAME prop side by side, uncropped: the harpy's RIGHT-hand curved knife only: a short, strongly
curved single-edged blade (like a small scimitar / kukri, about 30 cm), pale ivory-white polished steel with a
serrated or notched back near the tip as the native shows, a small gold guard, a dark wrapped grip and a round gold
pommel. One broad flat side view (the curve visible, blade up) and one edge-on / three-quarter view.
Checks: prop alone, complete, both views of the same object, transparent background.
