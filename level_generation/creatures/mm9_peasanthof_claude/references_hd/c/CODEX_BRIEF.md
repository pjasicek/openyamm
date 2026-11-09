# Codex brief: retexture views for the MM9 half-orc woman PeasantHOF2 (skin PeasantHOF1c, row 64) on our variant body (mm9_peasanthof_claude, design C)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasanthof_claude/references_hd/c/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority for the costume is the ORIGINAL MM9 3D model with its skin, shown in renders made from it.

WHY: our 3D body for this woman already exists (a grey clay model, inputs 4-7): the half-orc townswoman's body with a
floor-length dress and a kerchief over the head. These four views are used to PAINT that body, so the figure's
SILHOUETTE, POSE, PROPORTIONS AND EVERY OUTLINE must match inputs 4-7 exactly (same kerchief volume and edges, same
sleeve and skirt outline, same hands, feet and ears); only colours, materials, patterns and the face are yours to draw.

## Inputs (attached, in order)
1. `references_hd/mm9_views_phof2c.png` — renders of the ORIGINAL MM9 low-poly PeasantHOF2 model with its skin, five views
   (front three-quarter, front, side facing IMAGE LEFT, back, side facing IMAGE RIGHT): costume, colour and face
   authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views_phof2c.png` — close renders of its head (front, left profile, three-quarter, right
   profile, back): face and kerchief authority.
3. `references_hd/mm9_skin_x4_phof2c.png` — its original skin texture enlarged 4x: SURFACE MATERIAL AND COLOUR ONLY.
4. `references_hd/c/sil_front.png` — our clay body, front: SILHOUETTE AND POSE authority for 01.
5. `references_hd/c/sil_left.png` — our clay body, profile facing IMAGE LEFT: silhouette authority for 03.
6. `references_hd/c/sil_back.png` — our clay body, back: silhouette authority for 02.
7. `references_hd/c/sil_right.png` — our clay body, profile facing IMAGE RIGHT: silhouette authority for 04.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape, same framing as inputs 4-7)
| File | View |
|---|---|
| `01_front.png` | straight front, exactly input 4's pose and outline; the character's RIGHT arm on IMAGE LEFT (generate FIRST) |
| `03_left.png` | pure profile facing IMAGE LEFT, exactly input 5's outline |
| `02_back.png` | straight back, exactly input 6's outline |
| `04_right.png` | pure profile facing IMAGE RIGHT, exactly input 7's outline |

Generate 01 first; then 03, 02, 04 with your selected 01 as an extra input so all four are the SAME woman and costume.
At most ONE corrective regeneration per view; keep raw returns in `raw/` (inside c/). Write `generation_runs.json`
(id, view, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and a
`selected_views_review.png` contact sheet of the four selected views beside inputs 4-7.

## Common prompt content
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and Magic IX
character as a TEXTURING reference for an existing 3D body. Semi-realistic game materials, sharp fine detail (skin,
face, linen and wool weave, embroidery, leather grain), even soft neutral studio light, no dramatic light, no strong
shadows, near-orthographic camera, genuine transparent background, no floor, no shadow, no text. ONE complete figure,
never cropped. Pose exactly as inputs 4-7 (arms out about 35 degrees below horizontal, open relaxed hands palms down,
legs slightly apart under the dress, head level).

## Identity
A HALF-ORC townswoman about thirty-five, tall and sturdy (the body of inputs 4-7).
- Face (input 2): warm light skin with a faint flush, a broad friendly face with a WARM, gentle closed-mouth smile, blue
  eyes OPEN with visible irises, one fine light-brown brow line above each eye, natural soft lips (not lipstick); two
  SMALL neat ivory lower tusks show just over the upper lip near the mouth corners; a short straight dark-blonde fringe on
  the forehead under the kerchief. Long POINTED skin-coloured ears stand out at the sides in front of the kerchief.
- Kerchief (inputs 1-2): an undyed cream-beige linen KERCHIEF covering the top and back of the head and falling behind
  the ears to the shoulders, exactly the volume of inputs 4-7; along its front edge over the forehead a narrow dark-brown
  embroidered band; soft linen folds.
- Costume (inputs 1, 3): a long dark-brown wool dress of coarse basket weave to the ankles, with LONG sleeves to the
  wrists, each sleeve ending in a broad olive-green and dark-brown patterned cuff band (painted on the sleeve; the
  sleeve follows the arm outline of inputs 4-7, no extra flare); over it a cream-beige linen smock/pinafore bodice: a
  panel on the chest and one on the back, with a dark embroidered band across the top of the chest and a round bronze
  brooch on each shoulder strap, two strands of small amber and green glass beads hanging between the brooches; a
  red-brown leather belt with a round bronze buckle; from the belt a cream-beige linen apron to mid-shin with a dark
  embroidered band near its hem, lying FLAT on the dress; brown leather shoes.

Per-image checks (re-run before selecting): the outline matches the matching clay input (kerchief, sleeves, skirt,
hands, feet, ears); costume and colours as inputs 1-3; correct side faces the correct image side; whole figure in the
frame; true transparent background; 1536x1024; warm, calm expression.

## Do NOT
- change the silhouette, pose or proportions of inputs 4-7; paint the clay grey; add a cloak, shawl, hood, bag, weapon,
  tool, basket or gloves; loose hair strands; jewellery on the ears; a fierce, cold, staring or sad expression; an open
  mouth; big boar tusks; green skin; red lipstick; stylise as a cartoon; crop.
