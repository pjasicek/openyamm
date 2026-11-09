# Codex brief: HD HEAD turnarounds for the MM9 elf peasant woman, two faces (mm9_peasantf8_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf8_claude/references_head/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is
the ORIGINAL MM9 3D model with its two skins, shown in renders of that model.

The same body carries two faces in the original game: face **B** (a young blonde elf woman, the common one) and face **A** (an older,
smiling elf woman with grey-white hair). Make face B first, then face A on the SAME head shape, pose, scarf and ears.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png`: close renders of the ORIGINAL model's head with skin B, five views (three-quarter from her
   right, front, her left side facing IMAGE LEFT, back, her right side facing IMAGE RIGHT): FACE B, HAIR AND SCARF AUTHORITY. Low
   resolution, faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter_clean.png`: the approved HD body master with face B: identity, face structure, scarf and colours of the HD look.
3. `references_hd/01_front_clean.png`: the approved HD front master (face B, front).
4. `references_hd/mm9_skin_x4_b.png`: skin B enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, ear and hair texels at the top left).
5. `references_hd/mm9_head_views_a.png`: the same five views with skin A: FACE A AND HAIR A AUTHORITY.
6. `references_hd/mm9_skin_x4_a.png`: skin A enlarged, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `b_01_front.png` | face B: perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `b_00_three_quarter.png` | face B: front three-quarter bust from her RIGHT side (she looks toward IMAGE RIGHT, as input 2), eye level |
| `b_02_profile.png` | face B: pure 90-degree profile of her LEFT side: the face points to IMAGE LEFT |
| `b_03_back.png` | face B: straight BACK of the head and shoulders |
| `a_01_front.png`, `a_00_three_quarter.png`, `a_02_profile.png`, `a_03_back.png` | face A, the same four views, made with the selected B view of the same name as an extra input (same framing, head shape, scarf, ears and pose; only face, hair and age change) |

Generate b_01 first; then b_00, b_02, b_03 with the selected b_01 as an extra input. Then the a_ views, each with the B view of the same
name. At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png` contact sheet of the
eight selected views.

## Common prompt content
TASK CONTEXT, GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character
(inputs 1-3, 5). Not a new design. Output ONE bust only: the whole head with the headscarf and both ears, the neck, and the top of the
shoulders with the round embroidered neckline of the red bodice, centred with generous margins, never cropped. Near-orthographic camera at eye
level, head level, calm neutral expression, MOUTH CLOSED, lips relaxed (face A: a gentle closed-mouth smile). Even soft neutral studio
lighting, no dramatic light, no rim light, no strong shadows (the image is baked into a texture). Sharp fine detail: skin pores, brows,
lashes, lips, hair strands, cloth weave. The neck and the skin under the jaw are visible and continuous with the face. Clean edges between
skin, hair and scarf: each keeps its own colour, no skin tone in the scarf or hair.

## Identity (both faces)
- An adult female ELF villager. LONG POINTED ELF EARS, about 8 cm long, skin coloured, rising from the sides of the head at ear height and
  pointing OUTWARD, UP and slightly BACK at about 45 degrees, both clearly visible in front of the scarf's side edges.
- HEADSCARF: a soft ochre / honey-brown cloth kerchief covering the top and back of the head, framing the face with a soft rolled front edge
  above the forehead, falling straight down behind the head to the shoulders. It does not cover the face, the neck front or the ears.
- Hair shows only at the forehead and temples, parted in the middle and swept to the sides under the scarf.
- Face B: about 25 years old, fair skin, soft round face, green-grey eyes, straight nose, small closed mouth with natural pink lips, BLONDE hair.
- Face A: about 60 years old, the same head shape, fair skin with soft wrinkles and crow's feet, rosy cheeks, blue-grey eyes, a warm
  closed-mouth smile, GREY-WHITE hair (as input 5 and 6).

Per-image checks (re-run before selecting): the right face; the requested view (b_02 / a_02 face IMAGE LEFT); two pointed ears where the
view shows them; mouth closed; whole head, scarf and ears inside the frame; true transparent background; square.

## Do NOT
change the colours of the scarf; add jewellery, a veil, braids or a hat; open the mouth or show teeth; hide the ears; stylise as a cartoon;
add text, a floor, a background or a shadow; crop.
