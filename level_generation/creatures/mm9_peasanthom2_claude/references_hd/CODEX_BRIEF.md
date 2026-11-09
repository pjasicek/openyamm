# Codex brief: HD reference views for the MM9 half-orc shopkeeper PeasantHOM2 (skin PeasantHOM2a) (mm9_peasanthom2_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasanthom2_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

PeasantHOM2 is the SAME 3D BODY as the already-built PeasantHOM1 (identical mesh in MM9), wearing different clothes and
with a different face. Our 3D mesh of that body already exists and will be RE-PAINTED from your images, so every image
must keep EXACTLY the silhouette, pose, proportions, framing and camera of the matching PeasantHOM1 master (inputs 4-8):
the same outline of head, horns, ears, arms, hands, belly, legs and feet, pixel for pixel as closely as you can. Only the
painted surface changes: clothes, colours, hair colour/texture and the face. Treat inputs 4-8 as EDIT TARGETS for the shape.

## Inputs (attached, in order)
1. `references_hd/mm9_views_h2.png` — renders of the ORIGINAL Might and Magic IX model with skin PeasantHOM2a, five views
   left to right: front three-quarter from the character's RIGHT, front, character's LEFT side (faces IMAGE LEFT), back,
   character's RIGHT side (faces IMAGE RIGHT). Flat grey is background. DESIGN, COSTUME AND COLOUR authority. Its faceting
   and blur are not the design.
2. `references_hd/mm9_head_views_h2.png` — close renders of that model's head (front, profile, three-quarter, profile,
   back): face, hair, horn and ear authority.
3. `references_hd/mm9_skin_x4_h2.png` — the original skin texture enlarged 4x: SURFACE MATERIAL AND COLOUR ONLY.
4. `mm9_peasanthom1_claude/references_hd/clean/00_three_quarter.png` — SHAPE/POSE/FRAMING target for `00_three_quarter.png`.
5. `.../clean/01_front.png` — shape target for `01_front.png`.
6. `.../clean/02_back.png` — shape target for `02_back.png`.
7. `.../clean/03_left.png` — shape target for `03_left.png`.
8. `.../clean/04_right.png` — shape target for `04_right.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape like inputs 4-8)
| File | View | Edit target |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the character's RIGHT (generate FIRST) | input 4 |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT | input 5 |
| `02_back.png` | straight back | input 6 |
| `03_left.png` | pure profile of the character's LEFT side: faces IMAGE LEFT | input 7 |
| `04_right.png` | pure profile of the character's RIGHT side: faces IMAGE RIGHT | input 8 |

Generate 00 first; then 01-04, each with your selected 00 as an extra input so all five are the SAME person in the SAME
costume. At most ONE corrective regeneration per view; select the better and note any residual fault. Keep raw returns
in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with sha256, output path, selected flag, reason,
superseded runs, size, alpha extrema) and a `selected_views_review.png` contact sheet of the five selected views.
Background fully transparent (alpha 0) with no glow or halo.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition repaint of an EXISTING Might and Magic IX
character as a 3D TEXTURING reference. Keep the exact figure outline and pose of the edit target; repaint its surface as
the PeasantHOM2a character of inputs 1-3. Semi-realistic game materials, sharp fine detail (skin pores, hair strands,
horn ridges, fabric weave, leather grain, stitching), even soft neutral studio light, no dramatic light, no strong
shadows (the image is baked into a texture), near-orthographic camera, no floor, no text.

## Identity (inputs 1-3)
The same stocky half-orc build as the edit target (heavy, slightly pot-bellied, thick neck, big hands), but a different
man, a well-to-do SHOPKEEPER:
- Face: broad fleshy face, ruddy pink skin, a warm, friendly, cheerful smile with the mouth closed or nearly closed, small
  kind blue-grey eyes with crow's feet, a broad nose, a short dark moustache and a small dark goatee/chin tuft, dark
  stubble; two small pale lower tusk tips at the corners of the mouth. Large POINTED EARS sticking out sideways (as the
  edit target). Calm, warm expression: never fierce, never cold.
- Hair: thick DARK BROWN, slightly wavy/curly hair in the same heavy bowl shape and outline as the edit target (covering
  top, sides and back to the nape, fringe low on the forehead), with a few lighter brown strands.
- Horns: same shape and size as the edit target, but DARK purple-brown with lighter tan rings at the base.
- Costume: a long-sleeved DARK CHARCOAL-GREY woollen doublet/tunic CLOSED down the front (no cream shirt showing anywhere,
  no open vest), the chest and back panels of dark plum/burgundy pinstripe brocade, a row of small gold toggle clasps /
  laces down the centre front from the collar to the belt; a dark collar edged with a fine teal-and-purple woven trim;
  dark charcoal sleeves with a thin gold band at each cuff; a WIDE RED-BROWN (burgundy) leather belt at the waist with a
  large GOLD heart-shaped buckle in front; the tunic skirt below the belt to the upper thighs; dark grey-green woven wool
  trousers; tall brown leather boots to below the knee with a turned-down top and a small gold ornament on the shin
  (no cream leg wraps, no straps). Bare hands.

Per-image checks (re-run before selecting): outline matches the edit target (overlay it mentally: head, horns, ears, arms,
hands, legs, feet in the same places and sizes); same identity, costume and colours as inputs 1-3 in every view; no cream
shirt anywhere; two horns, two pointed ears, tusk tips; the correct side faces the correct image side; whole figure inside
the frame; true transparent background; 1536x1024.

## Do NOT
- change the pose, outline, proportions or framing of the edit target; add a weapon, apron, bag, hat, cloak, jewellery
  other than the gold clasps and buckle, or gloves; drop the horns, tusks or ears; make him green or monstrous; show
  teeth in a wide grin; add text, a floor or a shadow; crop.
