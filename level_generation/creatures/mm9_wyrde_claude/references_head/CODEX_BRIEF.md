# Codex brief: HD HEAD turnarounds for the MM9 Wyrdes Morgan and Verdandi, two faces on one body (mm9_wyrde_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_wyrde_claude/references_head/`. Do not edit any other file, do not
run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL
MM9 3D model with its two skins, shown in renders of that model.

The same body carries two faces in the original game: face **Y** (Morgan, the Wyrde of the Unknown: a serene young blonde woman of about 25
in a royal-blue hood) and face **M** (Verdandi, the Wyrde of the Knowing: a kindly smiling woman of about 60 with brown hair in a moss-green
patterned hood). Make face Y first, then face M on the SAME head shape, pose, hood shape and jewellery.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_y.png`: close renders of the ORIGINAL model's head with skin Y, five views (three-quarter from her right,
   front, her left side facing IMAGE LEFT, back, her right side facing IMAGE RIGHT): FACE Y, HAIR, HOOD AND CIRCLET AUTHORITY. Low
   resolution, faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter_clean.png`: the approved HD body master with face Y: identity, face structure, hood, circlet and colours of the HD look.
3. `references_hd/01_front_clean.png`: the approved HD front master (face Y, front).
4. `references_hd/mm9_skin_x4_y.png`: skin Y enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, hair and circlet texels at the top left).
5. `references_hd/mm9_head_views_m.png`: the same five views with skin M: FACE M, HAIR M AND GREEN HOOD AUTHORITY (her hood is the same shape
   as face Y's, in moss / olive-green cloth with a subtle darker damask pattern).
6. `references_hd/mm9_skin_x4_m.png`: skin M enlarged, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `y_01_front.png` | face Y: perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `y_00_three_quarter.png` | face Y: front three-quarter bust from her RIGHT side (she looks toward IMAGE RIGHT, as input 2), eye level |
| `y_02_profile.png` | face Y: pure 90-degree profile of her LEFT side: the face points to IMAGE LEFT |
| `y_03_back.png` | face Y: straight BACK of the head and shoulders |
| `m_01_front.png`, `m_00_three_quarter.png`, `m_02_profile.png`, `m_03_back.png` | face M, the same four views, made with the selected Y view of the same name as an extra input (same framing, head shape, hood shape, circlet, necklace and pose; only face, hair, age and the hood colour change) |

Generate y_01 first; then y_00, y_02, y_03 with the selected y_01 as an extra input. Then the m_ views, each with the Y view of the same
name. At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png` contact sheet of the
eight selected views.

## Common prompt content
TASK CONTEXT, GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character
(inputs 1-3, 5). Not a new design. Output ONE bust only: the whole head in its hood, the neck with the pearl choker and gold pectoral, and the
top of the shoulders with the hood's drape, centred with generous margins, never cropped. Near-orthographic camera at eye level, head level,
a calm warm expression, LIPS CLOSED (no teeth showing). Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows
(the image is baked into a texture). Sharp fine detail: skin pores, brows, lashes, lips, hair strands, cloth weave, gold filigree. The neck
and the skin under the jaw are visible, continuous with the face, and evenly lit (no dark shadow under the lower lip or on the chin). ONE
natural brow per eye, ONE natural lip line, no pale band under the lower lids, no makeup lines. Clean edges between skin, hair and hood: each
keeps its own colour, no skin tone in the hood or hair, a soft natural hairline (no pale band between hair and forehead).

## Identity (both faces)
- HOOD: a soft wool hood covering the top, sides and back of the head and the ears, rising to a soft rounded peak on top, framing the face
  closely, its front edge folded softly, falling down behind the head and draping in soft folds round the neck onto the shoulders. It does
  not cover the face or the front of the neck. No ears visible.
- CIRCLET: a gold filigree diadem worn over the hood's front edge across the forehead, a red cabochon gem at its centre with a small pearl
  drop below it, identical for both faces.
- NECK: a choker of pearls and small gold beads; below it at the base of the throat a broad gold filigree pectoral with an amber oval stone
  and a small green gem, identical for both faces.
- Face Y (Morgan): about 25 years old, fair skin, oval face, blue-grey eyes, soft natural light-brown brows, rose lips, a calm gentle
  closed-lips smile; long straight GOLDEN-BLONDE hair parted in the middle, falling at both sides of the face inside the hood onto the chest
  (as inputs 1 and 4). Hood ROYAL BLUE.
- Face M (Verdandi): about 60 years old, the same head shape with softer, slightly fuller cheeks, fair rosy skin with soft wrinkles,
  crow's feet and smile lines, blue eyes, a broad warm closed-lips smile, BROWN hair with some grey, parted in the middle and drawn back at
  the temples into soft braids, small pearl earrings may show just at the hood edge (as inputs 5 and 6). Hood MOSS / OLIVE GREEN with a
  subtle darker damask pattern.

Per-image checks (re-run before selecting): the right face; the requested view (y_02 / m_02 face IMAGE LEFT); lips closed; whole head and
hood inside the frame; true transparent background; square; one brow per eye; no dark smudge under the lower lip.

## Do NOT
change the hood colours (Y royal blue, M moss green); make either face stern, fierce, cold or mysterious; show teeth; add a veil, a crown or
extra jewellery beyond the circlet, choker, pectoral (and M's small earrings); show the ears; stylise as a cartoon; add text, a floor, a
background or a shadow; crop.
