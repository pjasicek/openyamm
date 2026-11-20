# Codex brief: HD HEAD turnaround for the MM9 young elf shopkeeper PeasantM2d, person D (skin PeasantM2D) (mm9_peasantm2d_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm2d_claude/references_head/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

PeasantM2d is the SAME head mesh as the already-built human PeasantM2 PLUS two pointed ELF EARS. Our 3D head exists and
will be RE-PAINTED from your images, so every image must keep EXACTLY the outline, framing and camera of the matching
PeasantM2 head view (inputs 4-7): the same skull, jaw, neck, nose, eyes and mouth positions, the same long hair VOLUME
and outline. Add the two elf ears exactly where and how input 3 shows them (red pieces on a grey clay render of our real
3D head, in the same four views). Treat inputs 4-7 as EDIT TARGETS; inputs 1-2 are the identity.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_d.png` — close renders of the ORIGINAL Might and Magic IX model's head with this
   person's skin (front, profile, three-quarter, profile, back): FACE, HAIR COLOUR AND EAR authority. Low resolution and
   faceting are not the design.
2. `references_hd/mm9_skin_x4_d.png` — the original skin texture enlarged 4x: SURFACE MATERIAL AND COLOUR ONLY.
3. `references_head/ear_shape_views.png` — grey clay renders of our 3D head with the elf ears in RED, four panels: front,
   three-quarter, profile (face to IMAGE LEFT), back. EAR SHAPE, SIZE, ANGLE AND POSITION authority (the red is NOT
   their colour).
4. `mm9_peasantm2_claude/references_head/b_01_front.png` — edit target for `01_front.png`.
5. `.../b_00_three_quarter.png` — edit target for `00_three_quarter.png`.
6. `.../b_02_profile.png` — edit target for `02_profile.png` (faces IMAGE LEFT).
7. `.../b_03_back.png` — edit target for `03_back.png`.

## Deliverables (true transparent RGBA background, 1254x1254 like inputs 4-7, unresized returns)
| File | View |
|---|---|
| `01_front.png` | straight FRONT bust (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust, as input 5 |
| `02_profile.png` | pure profile, face to IMAGE LEFT, as input 6 |
| `03_back.png` | back of the head and shoulders, as input 7 |

Generate 01 first; then 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME person. At most
ONE corrective regeneration per view; keep raw returns in `references_head/raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet. Background fully transparent (alpha 0), NO glow or halo.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition TEXTURING head reference of an EXISTING Might and Magic IX character.
Keep the edit target's head outline and feature placement; repaint as the young elf man of inputs 1-2 and add the elf
ears of input 3. Near-orthographic camera at eye level, even soft neutral studio light, no rim light, no strong shadows
(baked into a texture). Sharp fine detail: skin pores, brows, lashes, lips, hair strands, cloth weave. The neck skin and
the skin under the jaw are clearly visible and continuous with the face. A calm, warm, friendly expression, mouth
closed, eyes open with visible irises. ONE set of brows; ONE nose with two nostrils; lips painted once (no second lip
line); no pale crescent under the lower lids; no light band between brows and eyes; no make-up lines, no red eye rims.

## Identity (person D)
- A YOUNG ELF man of about 25, clean-shaven (no stubble, no beard, no moustache), smooth fair skin with a light warm
  peach tone, fine regular features, a straight narrow nose, light green-grey eyes, fine light-brown brows, a gentle
  closed-mouth calm smile. No wrinkles (he is young: remove the edit target's age lines and furrows completely).
- HAIR: honey / dark-golden blond, straight, with a centre parting, in the edit target's long hair VOLUME and outline
  (falling past the ears to the shoulders at the sides and down the back). The hair edge at the forehead and temples is
  clean and natural: individual strands on skin, NO pale band, gap or light line between hair and skin, no skin tone
  inside the hair.
- EARS: two long POINTED ELF EARS, skin-coloured (the face's own skin tone with a slightly pinker inner bowl and rim),
  each rising from the side of the head out of the hair, pointing out, back and up exactly as the red pieces of input
  3. The ear surfaces show only skin: no hair strands, beads, rings or jewellery painted on them. NO second, human ear
  anywhere: under and in front of each elf ear there is only smooth cheek/temple skin or hair.
- At the bottom: a sleeveless dark forest-GREEN finely speckled wool tunic over cream linen sleeves; the tunic's V-shaped
  neckline (as the edit target's opening) is edged with a narrow brown-and-gold woven braid; the neck and throat skin
  show inside the V.

Per-image checks: outline matches the edit target; ears match input 3 in position, size and angle, only one ear per
side; same person as inputs 1-2; young, clean-shaven; blond hair with a clean hairline; correct view; true transparent
background; square 1254x1254.

## Do NOT
- change the head outline, hair volume, framing or feature positions; make the ears short, human, droopy or hidden in the
  hair; leave a human ear; add a beard or stubble, a hat, jewellery, earrings, beads, a circlet; make him old; stylise as
  a cartoon; add text, a floor, a background, a glow or a shadow; crop; a stern, fierce or cold expression.
