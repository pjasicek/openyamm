# Codex brief: HD HEAD turnaround for the MM9 half-orc shopkeeper PeasantHOM2 (skin PeasantHOM2a) (mm9_peasanthom2_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasanthom2_claude/references_head/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

PeasantHOM2 has the SAME head mesh as the already-built PeasantHOM1; our 3D head exists and will be RE-PAINTED from your
images. Each image must keep EXACTLY the outline, framing and camera of the matching PeasantHOM1 head view (inputs 3-6):
the same head, hair-bowl, horn and ear silhouettes, eyes, nose and mouth at the same places. Only the painted surface
changes. Treat inputs 3-6 as EDIT TARGETS for the shape; inputs 1-2 are the identity.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_h2.png` — close renders of the ORIGINAL Might and Magic IX model's head with skin
   PeasantHOM2a (front, profile, three-quarter, profile, back): FACE, HAIR, HORN, EAR AND COLLAR authority. Its low
   resolution and faceting are not the design.
2. `references_hd/mm9_skin_x4_h2.png` — the original skin texture enlarged 4x: SURFACE MATERIAL AND COLOUR ONLY (the face
   is painted at top left).
3. `mm9_peasanthom1_claude/v2/references_head/clean/01_front.png` — edit target for `01_front.png`.
4. `.../clean/00_three_quarter.png` — edit target for `00_three_quarter.png`.
5. `.../clean/02_profile.png` — edit target for `02_profile.png` (faces IMAGE LEFT).
6. `.../clean/03_back.png` — edit target for `03_back.png`.

## Deliverables (true transparent RGBA background, 1254x1254 like inputs 3-6, unresized returns)
| File | View |
|---|---|
| `01_front.png` | straight FRONT bust (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust, as input 4 |
| `02_profile.png` | pure profile of the character's LEFT side: faces IMAGE LEFT, as input 5 |
| `03_back.png` | back of the head and shoulders, as input 6 |

Generate 01 first; then 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME person. At most
ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs
with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png`
contact sheet. Background fully transparent (alpha 0), NO glow or halo.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition TEXTURING head reference of an EXISTING Might and Magic IX character.
Keep the edit target's exact outline and feature placement; repaint as the PeasantHOM2a man of inputs 1-2. Near-orthographic
camera at eye level, even soft neutral studio light, no rim light, no strong shadows. Sharp fine detail: skin pores, brows,
lashes, lips, individual hair strands, horn ridges, cloth weave. The neck skin and the skin under the jaw are clearly
visible and continuous with the face. HAIRLINE: the fringe ends in a clean, soft, natural edge of hair strands on the
forehead skin, with NO pale band, gap or light line between fringe and brow. ONE set of brows; ONE nose with two nostrils
only; lips painted once (no second lip line); no pale crescent under the lower lids; no light band between brows and eyes.

## Identity
- A middle-aged half-orc SHOPKEEPER: broad fleshy face, ruddy pink skin, a warm, friendly, cheerful smile with the MOUTH
  CLOSED (lips together, smiling corners), small kind blue-grey eyes with crow's feet, eyes open with visible irises; a
  broad nose; a short dark-brown moustache and a small dark goatee/chin tuft, light dark stubble on the cheeks; only the
  two small pale lower tusk tips show over the upper lip at the mouth corners. Calm and warm, never fierce or cold.
- Hair: thick DARK BROWN slightly wavy hair with a few lighter strands, in the edit target's heavy bowl shape (fringe low
  on the forehead, sides down in front of the ears to the jaw, back down to the nape).
- Horns: the edit target's shape, DARK purple-brown with lighter tan rings at the base.
- Ears: large pointed, skin-coloured, sticking out sideways, as the edit target.
- At the bottom: a DARK CHARCOAL doublet collar closed at the throat, edged with a fine teal-and-purple woven trim, a small
  gold clasp at the centre front; NO cream shirt, no rust leather vest border.

Per-image checks: outline matches the edit target; same person as inputs 1-2; mouth closed smiling with the tusk tips;
moustache and goatee; dark hair and dark horns; clean hairline; correct view; true transparent background; square.

## Do NOT
- change outline, framing or feature positions; open the mouth or show a toothy grin; add a hat, jewellery, earrings,
  nose rings or beads; stylise as a cartoon; add text, a floor, a background, a glow or a shadow; crop.
