# Codex brief: HD HEAD turnaround for the MM9 dwarf shopkeeper PeasantDM1, skin B (mm9_peasantdm1_claude, tier B)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdm1_claude/references_head_b/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Context: MM9 draws two different dwarves on ONE 3D head mesh by changing only the painted skin. Skin A (a ginger-bearded
dwarf) already has approved HD head views (inputs 2-5). Skin B is a DIFFERENT dwarf (input 1). These views will be
painted onto the SAME head mesh as A's, so the head and neck SILHOUETTE, size, skull shape, hair volume outline,
framing, camera and lighting must match inputs 2-5 view for view; only the face, skin, beard, hair colour, hair texture
and the headband change.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png` — close renders of the ORIGINAL Might and Magic IX model's head with skin B
   (front, left profile, three-quarter, right profile, back): FACE AND HAIR AUTHORITY for this dwarf. Its low
   resolution, faceting and dark shading are NOT the design.
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

Generate 01 first; then 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME dwarf. At most
ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt,
inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Identity (input 1)
A dwarf shopkeeper in his late forties (MM9 "Shopkeeper", Dwarf MaleC B): a broad square weathered face with a strong
jaw and laugh lines, brown eyes, dark brows, a wide friendly grin with the mouth CLOSED; tanned ruddy skin; a short
grey-and-dark-brown stubble beard on the chin and jaw with a thin moustache (salt-and-pepper, close-cropped, not a full
beard); thick dark chestnut-brown hair of the SAME volume and outline as A's, to just above the shoulders, covering the
ears, with a thin braid on each side; a brown leather headband studded with small brass/gold rivets running round the
head across the upper forehead and over the hair at the back. At the bottom edge: an ochre / mustard-brown wool tunic
collar with a thin gold trim (input 6 colours).

## Common prompt content
Faithful high-definition TEXTURING reference of an EXISTING Might and Magic IX character. Even soft neutral studio
lighting, no dramatic light, no strong shadows (baked into a texture). Sharp fine detail: skin pores, wrinkles, brows,
lashes, lips, stubble and hair strands, leather and rivets. The neck skin under the jaw is visible and continuous with
the face. Clean edges between skin and hair: no skin tone bleeding into the hair and no hair colour on the skin; the
forehead skin below the headband is clean. Mouth CLOSED, eyes open.

Per-image checks (re-run before selecting): same dwarf as input 1 (stubble beard, dark hair, studded headband);
silhouette and framing match the corresponding A view; the requested view direction; whole head inside the frame;
true transparent background.

## Do NOT
- give him a long or full ginger beard; make the hair blond; change the head size or framing from the A views; add a
  hat or hood; stylise as a cartoon; add text, a floor, a background or a shadow; crop.
