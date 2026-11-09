#!/usr/bin/env python3
"""Codex briefs for the paint designs 2-4 (PeasantDF2b, DF3a, DF4a) on design 1's body: four retexture views (01-04)
drawn on the SAME silhouette as design 1's selected views (one Meshy body, four paints)."""
import sys
P = 'level_generation/creatures/mm9_peasantdf_claude'
D = {
 'd2': ('PeasantDF2', 'pdf2b', '''A DWARF townswoman (commoner) about fifty, short and sturdy (the same body as inputs 4-7).
- Face (input 2): fair rosy skin, a round friendly face with soft cheeks, a WARM kind smile with the mouth closed, light
  blue eyes OPEN with visible irises, calm brows; a short ash-blonde fringe shows at the forehead under the kerchief.
- Headdress: a cream-white linen KERCHIEF covering the head and falling to the shoulders all round, its hem edged with a
  narrow dark embroidered band; it fills EXACTLY the volume design 1's hair fills (inputs 4-7): same outline, same
  length at the sides and back, framing the face the same way.
- Costume: a dark olive-brown wool dress with a fine woven check, its sleeves end just ABOVE THE ELBOW with a cream
  cuff band (same length and shape as design 1's sleeves); the forearms are bare with a thin bracelet at each wrist;
  a cream linen chemise shows at the neckline as a small high collar with a little green embroidery and a small
  pendant; a dark red-brown sash belt at the waist; a cream linen apron from waist to below the knee, lying FLAT on
  the skirt, with an embroidered band near its hem; the ankle-length skirt; brown leather ankle boots.'''),
 'd3': ('PeasantDF3', 'pdf3a', '''A DWARF townswoman about forty, short and sturdy (the same body as inputs 4-7).
- Face (input 2): fair warm skin with light freckles, a pleasant calm face with a WARM gentle expression and a faint
  closed-mouth smile, blue-green eyes OPEN with visible irises, natural soft lips (no red lipstick).
- Headdress: a golden-ochre linen HOOD over the head, falling to the shoulders, open around the face; ginger-blonde
  hair shows at the forehead, and two thin ginger plaits lie FLAT against the hood's front edges down to the
  collarbones. The hood fills EXACTLY the volume design 1's hair fills (inputs 4-7): same outline and length.
- Costume: a golden-ochre underdress with short sleeves ending just ABOVE THE ELBOW (same length and shape as design
  1's sleeves); over it a dark olive-green sleeveless pinafore dress with fine vertical pleats, front and back panels
  open at the sides where the ochre underdress shows, its straps held by two round silver brooches below the
  shoulders; a brown leather belt with a small metal buckle; a silver heart-shaped pendant on a short chain; NO
  apron; bare forearms with brown leather wrist cuffs wrapped with silver bands; the ankle-length skirt; brown
  leather shoes with laces.'''),
 'd4': ('PeasantDF4', 'pdf4a', '''A DWARF townswoman (shopkeeper) about fifty-five, short and sturdy (the same body as inputs 4-7).
- Face (input 2): fair warm skin with soft smile lines, a kindly cheerful face with a WARM closed-mouth smile,
  grey-blue eyes OPEN with visible irises, calm brows; short dark-brown curly hair shows across the forehead under the
  hood.
- Headdress: an ochre-brown linen HOOD with a softly pointed top, falling to the shoulders, open around the face. It
  fills EXACTLY the volume design 1's hair fills (inputs 4-7): same outline and length.
- Costume: a rust-brown wool dress whose sleeves are rust from shoulder to elbow and continue as FITTED cream-beige
  sleeves to the wrist with a patterned cuff band (the sleeve hugs the forearm as closely as design 1's bare forearm:
  the same slim silhouette, no flare); a cream linen yoke at the bodice top with several strands of small amber beads
  hanging across the chest between two round bronze brooches; a brown leather belt; a cream linen apron from waist to
  below the knee lying FLAT on the skirt, with a patterned band near its hem; the ankle-length rust skirt; brown leather
  shoes.'''),
}
for d, (model, skin, ident) in D.items():
    txt = f'''# Codex brief: retexture views for the MM9 dwarf townswoman {model} (skin {skin}) on design 1's body (mm9_peasantdf_claude, {d})

Scope: image generation only. Write ONLY into `{P}/references_hd/{d}/`. Do not edit any other file, do not run builds,
do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority for the
costume is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

WHY: one 3D body is shared by four MM9 townswomen whose original models are the SAME mesh with different paint. The 3D
body is already made from design 1 (inputs 4-7). These four views are used to PAINT that same body as {model}: so the
figure's SILHOUETTE, POSE, PROPORTIONS AND EVERY OUTLINE must match inputs 4-7 exactly (same head/hair volume, same
sleeve length and shape, same skirt outline, same hands and feet); only the costume's colours, patterns, headdress
material and the face differ.

## Inputs (attached, in order)
1. `references_hd/mm9_views_{skin}.png` — renders of the ORIGINAL MM9 low-poly {model} model with its skin, five views
   (front three-quarter, front, side facing IMAGE LEFT, back, side facing IMAGE RIGHT): costume, colour and face
   authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views_{skin}.png` — close renders of its head (front, left profile, three-quarter, right
   profile, back): face and headdress authority.
3. `references_hd/mm9_skin_x4_{skin}.png` — its original skin texture enlarged 4x: SURFACE MATERIAL AND COLOUR ONLY.
4. `references_hd/d1/01_front.png` — design 1 front: SILHOUETTE AND POSE authority for 01.
5. `references_hd/d1/03_left.png` — design 1 left profile: silhouette authority for 03.
6. `references_hd/d1/02_back.png` — design 1 back: silhouette authority for 02.
7. `references_hd/d1/04_right.png` — design 1 right profile: silhouette authority for 04.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape, same framing as inputs 4-7)
| File | View |
|---|---|
| `01_front.png` | straight front, exactly input 4's pose and outline; the character's RIGHT arm on IMAGE LEFT (generate FIRST) |
| `03_left.png` | pure profile of the character's LEFT side, faces IMAGE LEFT, exactly input 5's outline |
| `02_back.png` | straight back, exactly input 6's outline |
| `04_right.png` | pure profile of the character's RIGHT side, faces IMAGE RIGHT, exactly input 7's outline |

Generate 01 first; then 03, 02, 04 with your selected 01 as an extra input so all four are the SAME woman and costume.
At most ONE corrective regeneration per view; keep raw returns in `raw/` (inside {d}/). Write `generation_runs.json`
(id, view, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and a
`selected_views_review.png` contact sheet of the four selected views beside inputs 4-7.

## Common prompt content
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and Magic IX
character as a TEXTURING reference for an existing 3D body. Semi-realistic game materials, sharp fine detail (skin,
face, linen and wool weave, embroidery, leather grain), even soft neutral studio light, no dramatic light, no strong
shadows, near-orthographic camera, genuine transparent background, no floor, no shadow, no text. ONE complete figure,
never cropped. Pose exactly as inputs 4-7 (arms out about 25 degrees below horizontal, open relaxed hands palms down,
legs slightly apart, head level).

## Identity
{ident}

Per-image checks (re-run before selecting): the outline matches the matching design-1 input (head volume, sleeve ends,
skirt, hands, feet); costume and colours as inputs 1-3; correct side faces the correct image side; whole figure in the
frame; true transparent background; 1536x1024; warm, calm expression.

## Do NOT
- change the silhouette, pose or proportions of inputs 4-7; add a cloak, shawl, bag, weapon, tool, basket or gloves;
  loose hair strands or locks standing off the headdress; jewellery or beads on the ears; a fierce, cold, staring or sad
  expression; red lipstick; stylise as a cartoon; crop.
'''
    open(f'references_hd/{d}/CODEX_BRIEF.md', 'w').write(txt)
print('BRIEFS written')
