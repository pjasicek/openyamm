# Codex brief: HD HEAD turnaround for the Imp (MM9 monster) (mm9_imp_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_imp_claude/references_head/`. Do not edit
any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png` — close renders of the ORIGINAL Might and Magic IX model's head (front, left
   profile, three-quarter): FACE, HORN, EAR AND MOUTH AUTHORITY. Its low resolution, faceting and dark shading are NOT
   the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this creature: exact identity, face
   structure and colour authority for the HD look. The heads you make must be THIS creature.
3. `references_hd/01_front.png` — the approved HD front master (same creature, front).
4. `references_hd/mm9_skin_x4.png` — the original skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT of the head, face square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter of the head, turned ~35 deg: the creature looks toward IMAGE RIGHT, eye level |
| `02_profile.png` | pure 90-degree profile of the creature's LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head |

Generate 01 first; then make 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head. At
most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt,
inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and
Magic IX monster (inputs 1-3). Not a new design. Output ONE bust only: the whole head with both horns and both ears, the
neck and the top of the shoulders, centred with generous margins, never cropped. Near-orthographic camera at eye level,
head level, the snarl as in inputs 1-2. Even soft neutral studio lighting, no dramatic light, no rim light, no strong
shadows (the image is baked into a texture). Sharp fine detail: wrinkled hide, pores, skin folds, teeth, horn grain.
The neck skin and the skin under the jaw and chin must be clearly visible and continuous with the face.

## Identity
The Imp: a bald devil-goblin with mustard-yellow to olive-gold wrinkled hide and darker ochre folds, a paler tan blaze
down the forehead and nose; a heavy brow ridge with deep wrinkles and black shadowed brows; a long hooked pointed nose;
wide flat cheeks; a jaw narrowing to a pointed chin. Mouth: a wide snarl, lips drawn back, a double row of long jagged
pale fangs on dark gums, with a short black tuft under the lower lip. Two short black conical horns on top of the skull,
pointing up and slightly out. Two pointed bat-like ears standing out sideways and back. Eyes: glowing emerald-green,
almond-shaped, slanted, NO pupil, deep under the brows. Bare head, bare neck, bare shoulders.

Per-image checks (re-run before selecting): same creature as input 2; the requested view (02 faces IMAGE LEFT); whole
head, horns and ears inside the frame; true transparent background; square.

## Do NOT
- change the face, colours or age; add hair, a hat or jewellery; give the eyes pupils; close the mouth; stylise as a
  cartoon; add text, a floor, a background or a shadow; crop.
