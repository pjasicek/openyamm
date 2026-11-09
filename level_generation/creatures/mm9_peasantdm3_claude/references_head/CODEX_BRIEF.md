# Codex brief: HD HEAD turnaround for the MM9 dwarf PeasantDM3, skin B (mm9_peasantdm3_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdm3_claude/references_head/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Context: these four views are TEXTURE references that will be projected onto an EXISTING 3D head mesh. Inputs 1-4 are
plain grey renders of THAT EXACT MESH from the four cameras: long hair falling to the shoulders, a full pointed beard,
the face, the neck and the top of the tunic. Paint the character ONTO each silhouette: every outline (hair edge,
hairline, beard outline and tip, nose, brows, jaw, shoulders) must stay exactly where the grey render has it, view for
view, at the same size and framing. The painting replaces the grey; nothing may stick out of or fall inside the outline.

## Inputs (attached, in order)
1. `references_head/silhouette/sil_front_white.png` — the mesh, FRONT (template for `01_front.png`).
2. `references_head/silhouette/sil_q34_white.png` — the mesh, three-quarter, the face toward IMAGE RIGHT (template for
   `00_three_quarter.png`).
3. `references_head/silhouette/sil_left_white.png` — the mesh, 90-degree profile, the face toward IMAGE LEFT (template
   for `02_profile.png`).
4. `references_head/silhouette/sil_back_white.png` — the mesh, BACK (template for `03_back.png`).
5. `references_hd/mm9_head_views_b.png` — close renders of the ORIGINAL Might and Magic IX model's head with skin B (front,
   left profile, three-quarter, right profile, back): FACE, HAIR AND BEARD AUTHORITY. Its low resolution, faceting and
   dark shading are NOT the design.
6. `references_hd/mm9_skin_x4_b.png` — the original skin B texture enlarged 4x: SURFACE MATERIAL AND COLOUR ONLY.
7. `../mm9_peasantdm1_claude/references_head/01_front.png` — an approved head view of another dwarf: the QUALITY, LIGHT
   AND RENDERING STYLE to match (not the identity).

## Deliverables (true transparent RGBA background, 1254x1254 like inputs 1-4, unresized returns)
| File | From input | View |
|---|---|---|
| `01_front.png` | 1 | straight front (generate FIRST) |
| `00_three_quarter.png` | 2 | three-quarter, face toward IMAGE RIGHT |
| `02_profile.png` | 3 | 90-degree profile, face toward IMAGE LEFT |
| `03_back.png` | 4 | straight back of the head and shoulders |

Generate 01 first; then 00, 02 and 03 each from its silhouette plus your selected 01 as an extra input, so all four are
the SAME dwarf. At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json`
(id, view, prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Identity (input 5)
A dwarf townsman in his late thirties: a broad, kindly face with a high forehead (slightly receding hairline), brown eyes
with clearly visible irises, thick dark-brown brows, a straight broad nose, a CALM, WARM, friendly look with a gentle
closed-mouth smile; healthy warm tanned skin with even tone. Long thick WAVY DARK-BROWN hair falling to the shoulders,
covering the ears completely, framing the face from the temples down. A full, dense WAVY BROWN beard with a moustache,
covering the cheeks and jaw and ending in a broad point below the chin (exactly the beard outline of the silhouette).
At the bottom edge: the top of a dark charcoal-grey tweed tunic with an ochre-gold braided trim round the collar and a
glimpse of a cream linen shirt at the front opening.

## Common prompt content
Faithful high-definition TEXTURING reference of an EXISTING Might and Magic IX character. Even soft neutral studio light
as in input 7, no dramatic light, no strong shadows (they would be baked into a texture). Sharp fine detail: skin pores,
brows, lashes, natural lips, beard and hair strands. ONE nose, painted exactly where the mesh's nose is, with natural soft
nostrils (no dark holes); ONE pair of lips with the mouth closed (no pink plate, no second lip line); the lower eyelids
plain skin (no pale crescent); one brow line per eye; eyes open and relaxed. Clean edges: no skin colour on the hair, no
hair colour on the skin outside the hair and beard outline; the neck below the beard is skin in shadow.

Per-image checks (re-run before selecting): outline identical to its grey input (hair edge, beard tip, nose, shoulders);
same dwarf in all four; calm warm expression; correct view direction; whole head inside the frame; true transparent
background; 1254x1254.

## Do NOT
- add beads, rings, braids, ties, clasps, earrings, a headband, a hat or a hood; show the ears; give him a fierce, cold,
  staring or frowning look; change any outline from the grey input; make the hair or beard ginger or grey; stylise as a
  cartoon; add text, a floor, a background or a shadow; crop.
