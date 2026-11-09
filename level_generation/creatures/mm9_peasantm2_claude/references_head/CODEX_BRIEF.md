# Codex brief: HD HEAD turnarounds for MM9's PeasantM2 townsman, tiers A and B (mm9_peasantm2_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm2_claude/references_head/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is
the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

The two tiers are two different elderly townsmen who share ONE head model (same skull, same hair volume and length, same neck); only the
painted face, hair colour and collar differ. The heads are painted onto one 3D head, so both must have the SAME head shape, hair outline,
pose, camera and framing.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a_half.png` - tier A's ORIGINAL model head (five views: three-quarter, front, left, back, right).
2. `references_hd/mm9_head_views_b_half.png` - tier B's ORIGINAL model head, same five views.
3. `references_hd/00_three_quarter_clean.png` - the approved HD body master (tier A): identity, head shape, hair volume authority.
4. `references_hd/01_front.png` - the approved HD front master (tier A).
5. (tier B runs only) your selected tier A `a_01_front.png`.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `a_01_front.png` | tier A, perfectly straight FRONT bust (generate FIRST) |
| `a_00_three_quarter.png` | tier A, front three-quarter bust, the character's RIGHT side toward the camera (he looks toward image right as in input 3), eye level |
| `a_02_profile.png` | tier A, pure 90-degree profile of the character's LEFT side: the face points to IMAGE LEFT |
| `a_03_back.png` | tier A, straight BACK of the head and shoulders |
| `b_01_front.png`, `b_00_three_quarter.png`, `b_02_profile.png`, `b_03_back.png` | tier B, the same four views, the SAME framing, scale and pose as tier A's |

Order: a_01 first; then a_00, a_02, a_03 with a_01 as an extra input; then b_01 with a_01 as an extra input (same head shape, hair outline
and framing, repainted as tier B); then b_00, b_02, b_03 with b_01 and the matching tier A view as extra inputs. At most ONE corrective
regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png` contact sheet of the eight selected views (A row, B row).

## Common prompt content
TASK CONTEXT - GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character.
Not a new design. Output ONE bust only: the whole head with all hair, the neck, and the top of the shoulders, centred with generous margins,
never cropped (hair fully inside the frame). Near-orthographic camera at eye level, head level and straight, mouth CLOSED (lips together, no
teeth), a gentle friendly smile. Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows (the image is baked into
a texture). Sharp fine detail: skin pores, wrinkles, brows, lashes, lips, hair strands, cloth weave. The neck skin and the skin under the jaw
and chin clearly visible and continuous with the face (no collar hiding the jaw line). Clean edges between skin and hair: the hair has its own
colour with no skin tone bleeding into it.

Shared head (both tiers): an elderly man about 60-65, lean weathered face, long straight nose, high cheekbones, crow's feet; thick long wavy
hair swept back from the forehead with no fringe, covering the ears, falling to the shoulders at the sides and to between the shoulder blades
at the back, as in inputs 1-3.

Tier A (input 1, inputs 3-4): blue eyes, ruddy tanned skin, WHITE-GREY hair, a short neat WHITE beard and moustache following the jaw and
chin (the neck skin under it visible). An olive-green wool tunic with a gold-brown embroidered braid round the V neck at the bottom edge.

Tier B (input 2): a DIFFERENT man on the same head: clean-shaven (NO beard, NO moustache, faint grey stubble at most), deeper wrinkles and
furrowed brow lines, hazel-brown eyes, ruddy tanned skin, ASH-GREY / dirty-blond-grey hair (a warmer, darker grey than tier A's white). A
plain cream-white linen tunic with a thin dark leather cord round the neck at the bottom edge.

Per-image checks (re-run before selecting): requested view (02 faces IMAGE LEFT); whole head and hair inside the frame; true transparent
background; square; lips closed; tier A bearded, tier B clean-shaven; tier B the same head outline and framing as tier A.

## Do NOT
- change the age, hair length or head shape; add a hat, jewellery other than tier B's neck cord, or headwear; stylise as a cartoon; add text,
  a floor, a background or a shadow; crop; show teeth.
