# Codex brief: fresh HD HEAD turnaround for the MM9 townsman PeasantM3, skin A (mm9_peasantm3_claude, r5)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm3_claude/references_head_r5a/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Purpose: the views become the multi-view input of a fresh 3D texture paint of this man's head, so they must show THIS 3D
head (shape, size, hair silhouette, ears, neck, framing) with a clean, calm, natural face.

## Inputs (attached, in order)
1. `references_head_r5a/viewer_head_a.png` - renders of the CURRENT 3D head (left to right: front, three-quarter from the
   character's RIGHT, the character's RIGHT side profile (faces IMAGE RIGHT), back): SHAPE, FRAMING AND SILHOUETTE
   AUTHORITY - the hair volume and outline, the head and jaw shape, the ears, the neck and the collar line. Its painted face
   is a FAULTY earlier paint (smeared lopsided lips, dark nostrils): do NOT copy the face paint. Its MOUTH SHAPE is right: the lips are closed and meet on ONE gentle, symmetric, slightly upturned line - paint the lips exactly there.
2. `references_hd/mm9_head_views_a.png` - the ORIGINAL Might and Magic IX model's head with skin A (front, left profile,
   three-quarter, right profile, back): IDENTITY AND COLOUR AUTHORITY (blond man, blue eyes, short golden-ginger beard).
   Its low resolution and faceting are NOT the design.
3. `references_head_a2/01_front.png` - the previous HD front bust of this same man (calm face, natural brows): HD look of the face, hair, beard and skin.
4. `references_hd/mm9_skin_x4_a.png` - the original skin texture enlarged 4x: surface material and colour only.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest square, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust (generate FIRST), framed like input 1 view 1 |
| `00_three_quarter.png` | front three-quarter from the character's RIGHT side: he looks toward IMAGE RIGHT and toward the viewer, as input 1 view 2 |
| `02_profile.png` | pure 90-degree profile of the character's LEFT side: the face points to IMAGE LEFT (mirror of input 1 view 3) |
| `03_back.png` | straight BACK of the head and shoulders, as input 1 view 4 |

Generate 01 first; then 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head. At most ONE
corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (view, prompt, inputs with
sha256, output, selected flag, reason) and a `selected_views_review.png` contact sheet.

## Prompt content
TASK CONTEXT - GAME ASSET TEXTURING REFERENCE: a faithful high-definition head of an EXISTING Might and Magic IX
character (identity from inputs 2-3) on the exact 3D head of input 1 (same head shape, same hair outline and volume, same
ears, same neck, same framing). ONE bust: whole head with all hair, the neck and the top of the shoulders with the
wine-red velvet tunic and its round gold brocade neckline, centred, never cropped. Near-orthographic camera at eye level,
head level. Even soft neutral studio light, no dramatic light, no rim light, no strong shadows (baked into a texture).

Face, calm and friendly: a relaxed, kind expression; eyes OPEN with clear blue irises and visible whites, relaxed upper lids,
no squint, no glare, no frown; ONE natural brow over each eye, a soft light-brown/dark-blond brow made of fine hairs (NOT a
pale painted band, NOT a makeup arch), sitting naturally above the eye, inner ends level (not knitted); the MOUTH CLOSED and
relaxed, the same width and line as input 1's mouth: the lips meet in one soft natural line, both halves identical (symmetric), natural muted lip colour, no parted lips, no teeth, no pale inner area, no
pout; a natural nose with two small nostrils in soft shadow (not a dark blob); a short neatly trimmed golden-ginger full beard
and moustache close to the face along the jaw and chin, blending softly into the neck skin under the jaw (no hard edge);
the neck one even skin tone down to the brocade neckline; straight golden-blond hair as input 1's silhouette; the ears
skin-coloured where they show under the hair edge. Sharp fine detail: skin pores, brow hairs, lashes, beard and hair strands.

Per-image checks (re-run before selecting): same head shape, hair outline and framing as input 1; the identity of inputs
2-3; calm open eyes; one natural brow per eye; closed relaxed mouth; small nostrils; the requested view (02 faces IMAGE
LEFT; 00 looks toward IMAGE RIGHT); nothing cropped; true transparent background; square.

## Do NOT
- copy input 1's faulty face paint; paint pale brow bands or arches; draw a second brow line, a light band between brow and
  eye, a pale crescent under the lower lid or heavy red eye rims; part the lips or show teeth; make the beard long; add a hat,
  jewellery or headwear; change the hair colour, the age or the head shape; stylise as a cartoon; add text, a floor, a
  background or a shadow; crop.
