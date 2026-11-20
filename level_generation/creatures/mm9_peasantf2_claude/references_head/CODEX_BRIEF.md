# Codex brief: HD HEAD turnarounds for the MM9 human townswoman PeasantF2, two faces (mm9_peasantf2_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf2_claude/references_head/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is
the ORIGINAL MM9 3D model with its two skins, shown in renders of that model.

The same body carries two faces in the original game: face **A** (a young woman of about 30 with golden-blonde hair and light freckles)
and face **B** (a woman of about 45 with copper-red hair). Make face A first, then face B on the SAME head shape, pose, hair shape and braid.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png`: close renders of the ORIGINAL model's head with skin A, five views (three-quarter from her
   right, front, her left side facing IMAGE LEFT, back, her right side facing IMAGE RIGHT): FACE A, HAIR AND BRAID AUTHORITY. Low
   resolution, faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter_clean.png`: the approved HD body master with face A: identity, face structure, hair and colours.
3. `references_hd/01_front_clean.png`: the approved HD front master (face A, front).
4. `references_hd/mm9_skin_x4_a.png`: skin A enlarged, SURFACE MATERIAL AND COLOUR ONLY (face and hair texels at the top left).
5. `references_hd/mm9_head_views_b.png`: the same five views with skin B: FACE B AND HAIR B AUTHORITY.
6. `references_hd/mm9_skin_x4_b.png`: skin B enlarged, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `a_01_front.png` | face A: perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `a_00_three_quarter.png` | face A: front three-quarter bust from her RIGHT side (she looks toward IMAGE RIGHT, as input 2), eye level |
| `a_02_profile.png` | face A: pure 90-degree profile of her LEFT side: the face points to IMAGE LEFT |
| `a_03_back.png` | face A: straight BACK of the head, the braid and the shoulders |
| `b_01_front.png`, `b_00_three_quarter.png`, `b_02_profile.png`, `b_03_back.png` | face B, the same four views, made with the selected A view of the same name as an extra input (same framing, head shape, hair shape, braid and pose; only face, hair colour and age change) |

Generate a_01 first; then a_00, a_02, a_03 with the selected a_01 as an extra input. Then the b_ views, each with the A view of the same
name. At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png` contact sheet of the
eight selected views.

## Common prompt content
TASK CONTEXT, GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character
(inputs 1-3, 5). Not a new design. FRAMING: the whole head with all its hair, the neck, the shoulders and the upper chest down to just below
the necklace, and in the back view the braid down to its tied end between the shoulder blades; centred with margins, never cropped.
Near-orthographic camera at eye level, head level. A calm, warm, friendly expression with the MOUTH CLOSED (a gentle closed-lip smile, no
teeth, no pout, natural lip colour, no lipstick). EYES OPEN and clearly readable: visible irises, upper lids relaxed so they just touch the
top of the iris, no squint, no stare. Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows, no dark shadow
under the lower lip, the nose or the eyes (the image is baked into a texture). Sharp fine detail: skin pores, light freckles, brows,
lashes, natural lips, hair strands, the plaited braid. The neck is visible, evenly lit and continuous with the face down to the neckline.
Clean edges between skin and hair: no pale band at the hairline.
Clothing as the body master (inputs 2, 3), simple and even: the gold-brocade scoop neckline over the cream chemise, the bead necklace.

## Identity (both faces)
- An adult human woman with a soft oval face, a straight nose, a rounded chin.
- HAIR: parted in the middle, combed smoothly and closely back over the skull, COVERING THE EARS COMPLETELY and the sides of the head down
  to the jaw line, gathered at the nape into ONE thick plait that hangs down the middle of the back (as inputs 1 and 5). Neat, close to
  the head, not big, no fringe.
- Face A: about 30, fair skin with light freckles on the nose and cheeks, green-grey eyes, natural rose lips, GOLDEN-BLONDE /
  strawberry-blond hair; a short copper bead necklace (as inputs 1, 4). Calm and warm, not fierce.
- Face B: about 45, the same head shape, fair skin with soft lines at the eyes, grey-blue eyes, a kind closed-mouth smile, COPPER-RED hair,
  a necklace of small green and blue stones (as inputs 5, 6). Calm and warm, not cold.

Per-image checks (re-run before selecting): the right face; the requested view (a_02 / b_02 face IMAGE LEFT); eyes open; mouth closed;
no ears visible; the braid complete; true transparent background; square.
