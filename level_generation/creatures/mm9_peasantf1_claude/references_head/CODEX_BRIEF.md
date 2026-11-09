# Codex brief: HD HEAD turnarounds for the MM9 human peasant woman PeasantF1, two faces (mm9_peasantf1_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf1_claude/references_head/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is
the ORIGINAL MM9 3D model with its two skins, shown in renders of that model.

The same body carries two faces in the original game: face **B** (a kindly woman of about 55 with grey-brown hair, the common one) and
face **A** (an older, plumper grandmother of about 65 with white hair, in a WHITE linen hood). Make face B first, then face A on the SAME head shape, pose and hood shape.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png`: close renders of the ORIGINAL model's head with skin B, five views (three-quarter from her
   right, front, her left side facing IMAGE LEFT, back, her right side facing IMAGE RIGHT): FACE B, HAIR AND HOOD AUTHORITY. Low
   resolution, faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter_clean.png`: the approved HD body master with face B: identity, face structure, hood and colours of the HD look.
3. `references_hd/01_front_clean.png`: the approved HD front master (face B, front).
4. `references_hd/mm9_skin_x4_b.png`: skin B enlarged, SURFACE MATERIAL AND COLOUR ONLY (face and hair texels at the top left).
5. `references_hd/mm9_head_views_a.png`: the same five views with skin A: FACE A, HAIR A AND WHITE HOOD AUTHORITY (her hood is the same shape
   as face B's, in white / off-white linen).
6. `references_hd/mm9_skin_x4_a.png`: skin A enlarged, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `b_01_front.png` | face B: perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `b_00_three_quarter.png` | face B: front three-quarter bust from her RIGHT side (she looks toward IMAGE RIGHT, as input 2), eye level |
| `b_02_profile.png` | face B: pure 90-degree profile of her LEFT side: the face points to IMAGE LEFT |
| `b_03_back.png` | face B: straight BACK of the head and shoulders |
| `a_01_front.png`, `a_00_three_quarter.png`, `a_02_profile.png`, `a_03_back.png` | face A, the same four views, made with the selected B view of the same name as an extra input (same framing, head shape, hood shape and pose; only face, hair, age and the hood colour change: her hood is WHITE / off-white linen) |

Generate b_01 first; then b_00, b_02, b_03 with the selected b_01 as an extra input. Then the a_ views, each with the B view of the same
name. At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png` contact sheet of the
eight selected views.

## Common prompt content
TASK CONTEXT, GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character
(inputs 1-3, 5). Not a new design. Output ONE bust only: the whole head in its hood, the neck, and the top of the shoulders with the small
standing collar of the cream blouse, centred with generous margins, never cropped. Near-orthographic camera at eye level, head level, a warm
smile with the LIPS CLOSED (no teeth showing). Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows (the
image is baked into a texture). Sharp fine detail: skin pores, soft wrinkles, brows, lashes, lips, hair strands, cloth weave. The neck and
the skin under the jaw are visible, continuous with the face, and evenly lit (no dark shadow under the lower lip or on the chin). Clean
edges between skin, hair and hood: each keeps its own colour, no skin tone in the hood or hair, a soft natural hairline (no pale band
between hair and forehead).

## Identity (both faces)
- An adult human village woman. HOOD: a stiff cloth hood (face B ochre / honey-brown, face A white / off-white linen) covering the top, sides and back of the head and the ears,
  rising to a soft blunt peak on top, framing the face closely, falling straight down behind the head and at the sides to the shoulders. It
  does not cover the face or the front of the neck. No ears visible.
- Hair shows only as a band at the forehead and temples, combed back from the face in soft waves under the hood's front edge.
- Face B: about 55 years old, fair skin, soft wrinkles at the eyes and smile lines, rosy cheeks, hazel eyes, a broad warm closed-lips smile
  with red lips, GREY-BROWN hair with grey streaks at the temples (as inputs 1 and 4).
- Face A: about 65 years old, the same head shape but fuller, rounder cheeks, fair rosy skin with soft wrinkles and crow's feet, blue-grey
  eyes, a broad warm closed-lips smile, WHITE hair (as inputs 5 and 6).

Per-image checks (re-run before selecting): the right face; the requested view (b_02 / a_02 face IMAGE LEFT); lips closed; whole head and
hood inside the frame; true transparent background; square; no dark smudge under the lower lip.

## Do NOT
change the hood colour (B ochre, A white); add jewellery, a veil, braids or a hat; show teeth; show the ears; stylise as a cartoon; add text, a floor,
a background or a shadow; crop.
