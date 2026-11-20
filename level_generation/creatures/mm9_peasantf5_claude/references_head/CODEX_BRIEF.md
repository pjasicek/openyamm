# Codex brief: HD HEAD turnarounds for the MM9 human peasant woman PeasantF5, two faces (mm9_peasantf5_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf5_claude/references_head/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is
the ORIGINAL MM9 3D model with its two skins, shown in renders of that model.

The same body carries two faces in the original game: face **B** (an older grey-haired woman, the common villager) and face **A** (a
younger, broad-faced, smiling woman with auburn hair, the shopkeeper). Make face B first, then face A on the SAME head shape, pose, coif and
collar.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png`: close renders of the ORIGINAL model's head with skin B, five views (three-quarter from her
   right, front, her left side facing IMAGE LEFT, back, her right side facing IMAGE RIGHT): FACE B, HAIR AND COIF AUTHORITY. Low
   resolution, faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter_clean.png`: the approved HD body master with face B: identity, face structure, coif and colours of the HD look.
3. `references_hd/01_front_clean.png`: the approved HD front master (face B, front).
4. `references_hd/mm9_skin_x4_b.png`: skin B enlarged, SURFACE MATERIAL AND COLOUR ONLY (face and hair texels at the top left).
5. `references_hd/mm9_head_views_a.png`: the same five views with skin A: FACE A AND HAIR A AUTHORITY.
6. `references_hd/mm9_skin_x4_a.png`: skin A enlarged, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `b_01_front.png` | face B: perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `b_00_three_quarter.png` | face B: front three-quarter bust from her RIGHT side (she looks toward IMAGE RIGHT, as input 2), eye level |
| `b_02_profile.png` | face B: pure 90-degree profile of her LEFT side: the face points to IMAGE LEFT |
| `b_03_back.png` | face B: straight BACK of the head and shoulders |
| `a_01_front.png`, `a_00_three_quarter.png`, `a_02_profile.png`, `a_03_back.png` | face A, the same four views, made with the selected B view of the same name as an extra input (same framing, head shape, coif, collar and pose; only face, hair and age change) |

Generate b_01 first; then b_00, b_02, b_03 with the selected b_01 as an extra input. Then the a_ views, each with the B view of the same
name. At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png` contact sheet of the
eight selected views.

## Common prompt content
TASK CONTEXT, GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character
(inputs 1-3, 5). Not a new design. Output ONE bust only: the whole head in its coif, the neck with the standing embroidered collar, and the
top of the shoulders, centred with generous margins, never cropped. Near-orthographic camera at eye level, head level, a warm friendly
expression with the MOUTH CLOSED (a gentle closed-lip smile, no teeth). EYES WIDE OPEN and clearly readable: visible irises and whites,
upper lids not drooping, no squint (the face is seen from slightly above in the game, so open eyes matter). Even soft neutral studio
lighting, no dramatic light, no rim light, no strong shadows, NO dark shadow under the lower lip or on the chin (the image is baked into a
texture). Sharp fine detail: skin pores, brows, lashes, lips, hair strands, linen weave, embroidery. The neck and the skin under the jaw are
visible, evenly lit and continuous with the face down to the collar. Clean edges between skin, hair and coif: each keeps its own colour, no
skin tone in the coif, no pale band between the hairline and the forehead skin.

## Identity (both faces)
- An adult human village woman with a broad, soft, round face.
- COIF: a cream / off-white linen hood-like headdress that rises to a TALL POINTED PEAK above the crown (a stiff folded kerchief), frames the
  face closely at the forehead and cheeks, covers the ears completely, and falls straight down at the back and sides to the nape and
  shoulders. It does not cover the face or the front of the neck.
- COLLAR: a narrow high standing collar round the neck in dark red and black folk embroidery.
- Hair shows only at the forehead and temples, parted in the middle and swept to the sides under the coif.
- Face B: about 60 years old, fair skin with soft wrinkles and crow's feet, rosy cheeks, blue-grey eyes, a warm closed-mouth smile,
  GREY-WHITE hair (as inputs 1 and 4).
- Face A: about 45 years old, the same head shape, fuller cheeks, fair skin with rosy cheeks and a few freckles, blue eyes, a broad warm
  closed-mouth smile, AUBURN / copper-red hair (as inputs 5 and 6).

Per-image checks (re-run before selecting): the right face; the requested view (b_02 / a_02 face IMAGE LEFT); eyes open; mouth closed; no
ears visible; pointed coif peak inside the frame; whole head, coif and collar inside the frame; true transparent background; square.

## Do NOT
change the colour of the coif; add jewellery, a veil, braids or a hat; open the mouth or show teeth; show ears; stylise as a cartoon;
add text, a floor, a background or a shadow; crop.
