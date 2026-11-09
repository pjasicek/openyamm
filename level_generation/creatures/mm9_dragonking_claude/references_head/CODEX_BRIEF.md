# Codex brief: HD HEAD turnaround + mouth interior swatches for the MM9 Dragon King (mm9_dragonking_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dragonking_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are
no native sprites for MM9: the authority is the ORIGINAL MM9 3D model and the approved HD body masters.

## Inputs (attached, in order)
1. `references_head/inputs/render_front.png` — our 3D game model's head, straight FRONT, orthographic.
2. `references_head/inputs/render_three_quarter.png` — the same head, front three-quarter (snout toward IMAGE RIGHT).
3. `references_head/inputs/render_profile.png` — the same head, pure side profile, snout toward IMAGE LEFT.
4. `references_head/inputs/render_back.png` — the same head from straight BEHIND.
   Inputs 1-4 are the SHAPE, SILHOUETTE, PROPORTION AND CAMERA AUTHORITY: the image you paint for a view must line up
   with its render (same head size and position in the frame, same horn, crest, frill, spike and jaw outlines, same
   eye position, same jaw opening). Their blurry blotchy texture and the large dark wing shapes at the image edges
   are NOT the design: leave the wings out (transparent), paint the head with a sharp new texture.
5. `references_hd/00_three_quarter.png` — the approved HD body master: colour, scale pattern, materials and the HD
   look (olive/moss-green scales with darker mottling, yellow-green highlights, yellow eyes with black slit pupils,
   dark green-black frill membranes with spine ribs, pale ivory teeth).
6. `references_hd/mm9_head_tier1.png` — renders of the ORIGINAL Might and Magic IX head: design authority for the
   horns, central crest, side frills, eyes, chin fins and teeth. Its faceting and low resolution are NOT the design.
7. `references_hd/mm9_skin_tier1_x4.png` — the original skin texture x4, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables
| File | Content | Canvas |
|---|---|---|
| `01_front.png` | head turnaround, FRONT, matching input 1 (generate FIRST) | 1254x1254 (or nearest supported square), true transparent background |
| `00_three_quarter.png` | front three-quarter matching input 2: snout toward IMAGE RIGHT | same |
| `02_profile.png` | pure 90-degree profile matching input 3: snout toward IMAGE LEFT | same |
| `03_back.png` | straight back of the head matching input 4 | same |
| `04_mouth_palate.png` | flat texture swatch, ROOF of the mouth (layout below) | 1024x1024, opaque |
| `05_mouth_floor.png` | flat texture swatch, FLOOR of the mouth with the tongue (layout below) | 1024x1024, opaque |

Generate 01 first; then make 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head.
At most ONE corrective regeneration per image; keep raw returns in `raw/`. Write `generation_runs.json` (id, file,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the six selected images.

## Head views: prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition TEXTURING reference of an EXISTING Might and Magic IX monster's
head (the green "Dragon King", final boss). It is projected onto the 3D head of inputs 1-4, so the painted head must
cover exactly the same silhouette in the same place. Not a new design. Show the head with the upper neck down to just
below the jaw and the side frills, centred as in the render, with nothing cropped (horn tips and frill tips inside
the frame). Orthographic camera as in the render. Even soft neutral studio lighting, no dramatic light, no rim
light, no cast shadows, no ambient-occlusion darkening beyond small crevices (the image becomes a texture). Sharp
fine detail: small overlapping green scales on the skull and snout, larger plates on the brow, ridged horns that
darken to near-black tips, the frills as thin dark green-black membranes with lighter green spine ribs, yellow-green
belly plates under the chin and throat, a glowing YELLOW eye with a black vertical slit pupil on each side.
MOUTH: as in the renders, the jaws are almost closed: a narrow dark slit along the mouth line with the rows of pale
ivory pointed teeth visible at the lips. Do NOT open the mouth wider than the render, do NOT paint a red interior
on the lips or the cheeks: the skin of the lips and of the cheek behind the mouth corner is green scaly skin.
Identity: a long narrow reptilian head with a long snout, TWO long horns sweeping up and back plus ONE central crest
spike between them, a large spiky membrane frill on each side behind the jaw, small fins under the chin.
Per-image checks: the silhouette overlays its render; correct view and side (02: snout to IMAGE LEFT; 00: snout to
IMAGE RIGHT); no wings; mouth as narrow as the render; true transparent background; square.

## Mouth swatches: layout and prompt content
These are flat, top-down texture swatches (no perspective, no lighting direction, no shadows, no frame, no
background, the whole square filled), painted to this exact layout. They are mapped onto the inside of the
dragon's mouth: horizontal axis = ACROSS the mouth, vertical axis = ALONG the mouth (TOP edge = front of the mouth
at the lips, BOTTOM edge = deep in the throat).
- `04_mouth_palate.png` (roof of the mouth, seen from below): a band about 12% of the width along the LEFT edge and
  one along the RIGHT edge is the upper GUM (glossy dark pink-red, slightly lumpy, with small darker sockets where
  teeth sit); between them the hard PALATE: darker wine-red with regular transverse ridges (rugae) curving across
  the width, a faint central seam running top to bottom. From about 60% of the height downward everything darkens
  gradually into the throat; the bottom 15% is nearly black (very dark red-brown).
- `05_mouth_floor.png` (floor of the mouth, seen from above): GUM bands along the LEFT and RIGHT edges (about 12% of
  the width each, as in 04); inside each gum a narrow dark groove; in the centre the TONGUE, a long reptile tongue
  from about 8% below the top edge running down to the bottom, about 60% of the width, with a shallow central
  furrow, a slightly forked rounded tip at the top, fine papillae texture, moist pinkish red; the same darkening
  toward the bottom edge (nearly black at the bottom 15%).
Colours: dragon mouth reds as in input 5's open mouth (deep red to dark crimson), never orange, never bright pink.
Per-image checks: flat, top-down, filled, gums along both side edges, front at the top, dark throat at the bottom.

## Do NOT
Add a mouth wider than the render, fire, a background, a floor, wings, extra horns, jewellery or text; change the
colours (no red or gold dragon); crop.
