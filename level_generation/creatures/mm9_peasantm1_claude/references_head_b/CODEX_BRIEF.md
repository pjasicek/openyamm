# Codex brief: HD HEAD turnaround for the MM9 prisoner PeasantM1, skin B (mm9_peasantm1_claude, tier B)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm1_claude/references_head_b/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Context: MM9 draws two different men on ONE 3D head mesh by changing only the painted skin. Skin A (a bearded dark-haired
man) already has approved HD head views (inputs 2-5). Skin B is a DIFFERENT man (input 1). These views will be painted
onto the SAME head mesh as A's, so the head and neck SILHOUETTE, size, skull shape, hair volume outline, framing,
camera and lighting must match inputs 2-5 view for view; only the face, skin, hair colour and hair texture change.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png` — close renders of the ORIGINAL Might and Magic IX model's head with skin B
   (front, left profile, three-quarter, back): FACE AND HAIR AUTHORITY for this man. Its low resolution, faceting and
   dark shading are NOT the design.
2. `references_head/01_front.png` — approved skin A front bust: silhouette, framing, camera and light template.
3. `references_head/00_three_quarter.png` — approved skin A three-quarter bust: same role.
4. `references_head/02_profile.png` — approved skin A left profile bust: same role.
5. `references_head/03_back.png` — approved skin A back bust: same role.
6. `references_hd/mm9_skin_x4_b.png` — the original skin B texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, the same size as inputs 2-5, unresized returns)
| File | View (match the corresponding A input exactly in pose, framing and silhouette) |
|---|---|
| `01_front.png` | straight FRONT bust (as input 2; generate FIRST) |
| `00_three_quarter.png` | three-quarter bust looking toward IMAGE RIGHT (as input 3) |
| `02_profile.png` | 90-degree LEFT profile, face points to IMAGE LEFT (as input 4) |
| `03_back.png` | straight BACK of the head and shoulders (as input 5) |

Generate 01 first; then 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME man. At most ONE
corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs
with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Identity (input 1)
A heavy-set, clean-shaven village man in his forties (MM9 "Prisoner", Human2 MaleD): a broad fleshy face with full
jowls and a soft double chin, small light blue eyes under straight light-brown brows, a short straight nose, a small
closed mouth with a serious, tired expression; pale pinkish skin with ruddy cheeks; NO beard and NO moustache (a faint
shave shadow at most); straight thick dark-blond / honey-blond hair in a bowl cut with a short fringe on the forehead,
covering the ears and ending at the nape (input 1). At the bottom edge: a rust-red woven wool jerkin collar around the
neck over a cream linen shirt's laced V opening (input 6 colours).

## Common prompt content
Faithful high-definition TEXTURING reference of an EXISTING Might and Magic IX character. Even soft neutral studio
lighting, no dramatic light, no strong shadows (baked into a texture). Sharp fine detail: skin pores, fine wrinkles,
brows, lashes, lips, hair strands. The neck skin under the jaw is visible and continuous with the face. Clean edges
between skin and hair: no skin tone bleeding into the hair and no hair colour on the skin. Mouth CLOSED.

Per-image checks (re-run before selecting): same man as input 1, clean-shaven, blond; silhouette and framing match
the corresponding A view; the requested view direction; whole head inside the frame; true transparent background.

## Do NOT
- give him a beard or moustache; make the hair dark; change the head size or framing from the A views; add a hat,
  jewellery or headwear; stylise as a cartoon; add text, a floor, a background or a shadow; crop.
