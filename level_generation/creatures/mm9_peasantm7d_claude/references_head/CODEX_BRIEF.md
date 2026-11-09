# Codex brief: HD HEAD turnarounds for the MM9 elf townsmen PeasantM7d (skins PeasantM7D and PeasantM7C) (mm9_peasantm7d_claude)

Scope: image generation only. Write ONLY into the output folder named in the run prompt
(`level_generation/creatures/mm9_peasantm7d_claude/references_head/` for person D, `.../references_head_c/` for person C).
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

PeasantM7d is the SAME head mesh as the already-built human PeasantM7 PLUS two pointed ELF EARS. Our 3D head exists and
will be RE-PAINTED from your images, so every image must keep EXACTLY the outline, framing and camera of the matching
PeasantM7 head view (inputs 4-7): the same skull, jaw, neck, nose, eyes and mouth positions, the same hair VOLUME and
outline. Add the two elf ears exactly where and how input 3 shows them (red pieces on a grey clay render of our real 3D
head, in the same four views). Treat inputs 4-7 as EDIT TARGETS; inputs 1-2 are the identity.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_<d|c>.png` — close renders of the ORIGINAL Might and Magic IX model's head with this
   person's skin (front, profile, three-quarter, profile, back): FACE, HAIR COLOUR, EAR AND COLLAR authority. Low
   resolution and faceting are not the design.
2. `references_hd/mm9_skin_x4_<d|c>.png` — the original skin texture enlarged 4x: SURFACE MATERIAL AND COLOUR ONLY.
3. `references_head/ear_shape_views.png` — grey clay renders of our 3D head with the elf ears in RED, four panels:
   front, three-quarter, profile, back. EAR SHAPE, SIZE, ANGLE AND POSITION authority (the red is NOT their colour).
4. `mm9_peasantm7_claude/references_head/01_front.png` — edit target for `01_front.png`.
5. `.../00_three_quarter.png` — edit target for `00_three_quarter.png`.
6. `.../02_profile.png` — edit target for `02_profile.png` (faces IMAGE LEFT).
7. `.../03_back.png` — edit target for `03_back.png`.

## Deliverables (true transparent RGBA background, 1254x1254 like inputs 4-7, unresized returns)
| File | View |
|---|---|
| `01_front.png` | straight FRONT bust (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust, as input 5 |
| `02_profile.png` | pure profile, face to IMAGE LEFT, as input 6 |
| `03_back.png` | back of the head and shoulders, as input 7 |

Generate 01 first; then 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME person. At most
ONE corrective regeneration per view; keep raw returns in `raw/` of the output folder. Write `generation_runs.json`
(id, view, prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet. Background fully transparent (alpha 0), NO glow or halo.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition TEXTURING head reference of an EXISTING Might and Magic IX character.
Keep the edit target's head outline and feature placement; repaint as the elf man of inputs 1-2 and add the elf ears of
input 3. Near-orthographic camera at eye level, even soft neutral studio light, no rim light, no strong shadows (baked
into a texture). Sharp fine detail: skin pores, brows, lashes, lips, hair strands, cloth weave. The neck skin and the
skin under the jaw are clearly visible and continuous with the face. A calm, warm, friendly expression, mouth closed,
eyes open with visible irises. ONE set of brows; ONE nose with two nostrils; lips painted once (no second lip line); no
pale crescent under the lower lids; no light band between brows and eyes; no make-up lines.

## Identity
- A YOUNG ELF townsman, clean-shaven (no stubble, no beard), smooth fair skin with a light peach-pink tone, fine
  features, a straight narrow nose, high cheekbones.
- HAIR: golden-blond (honey/wheat blond with lighter and darker strands), in the edit target's hair VOLUME and outline
  (covering the top, the sides down to the jaw line and the back to the nape), with a short soft blond FRINGE on the
  forehead whose edge is clean and natural: individual strands on skin, NO pale band, gap or light line between the fringe
  and the forehead, no skin tone inside the hair.
- EARS: two long POINTED ELF EARS, skin-coloured (the face's own skin tone with a slightly pinker inner bowl and rim), each
  rising from the side of the head through the hair, pointing out, back and up exactly as the red pieces of input 3. The
  ear surfaces show only skin: no hair strands, beads, rings or jewellery painted on them.
- At the bottom: a tunic collar of GOLD-OCHRE brocade (patterned golden braid) on the shoulders and round the neck.
- Person D (`references_head/`): wide-set grey-blue eyes, soft rounded young face, gentle closed-mouth smile.
- Person C (`references_head_c/`): deep blue eyes with naturally rosy, slightly reddish eyelids (as input 1), a narrower
  face, thin lips, a calm faint smile.

Per-image checks: outline matches the edit target; ears match input 3 in position, size and angle; same person as inputs
1-2; blond hair with a clean fringe edge; clean-shaven; correct view; true transparent background; square.

## Do NOT
- change the head outline, hair volume, framing or feature positions; make the ears short, human, droopy or hidden in the
  hair; add a beard or stubble, a hat, jewellery, earrings, beads, a circlet; stylise as a cartoon; add text, a floor, a
  background, a glow or a shadow; crop.
