# Codex brief: HD HEAD turnaround for the MM9 elf townsman PeasantM1d (skin PeasantM1c) (mm9_peasantm1d_claude/v2)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm1d_claude/v2/references_head/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no
native sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_c.png` — close renders of the ORIGINAL Might and Magic IX model's head (front, left
   profile, three-quarter, right profile, back): FACE, HAIR AND EAR AUTHORITY. Its low resolution and faceting are NOT
   the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this character: exact identity,
   face structure, hair and colour authority for the HD look. The heads you make must be THIS person.
3. `references_hd/mm9_skin_x4_c.png` — the original skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust, the character's RIGHT side toward the camera (he looks toward image right as in input 2), eye level |
| `02_profile.png` | pure 90-degree profile of the character's LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head and shoulders |

Generate 01 first; then make 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views. The background must be fully transparent
(alpha 0), with NO glow or halo around the figure.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING
Might and Magic IX character (inputs 1-2). Not a new design. Output ONE bust only: the whole head with all hair and
both ears, the neck, and the top of the shoulders, centred with generous margins, never cropped (both ear tips fully
inside the frame). Near-orthographic camera at eye level, head level, neutral relaxed expression, mouth closed.
Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows (the image is baked into a
texture). Sharp fine detail: skin pores, brows, lashes, lips, individual hair strands, cloth weave. The neck skin and
the skin under the jaw and chin must be clearly visible and continuous with the face (the tunic's laced V-neck is
open; no collar hiding the jaw line). Clean edges between skin and hair: the hair has its own colour with no skin tone
bleeding into it.

## Identity
A young adult ELF townsman: fair rosy skin, a youthful clean-shaven face with soft cheeks, light blue-grey eyes,
fair brows; short straight BLOND (straw/honey) hair with a fringe over the forehead, covering the top and back of the
head down to the nape; long POINTED ELF EARS sticking out sideways and up through the hair at both sides. The
rust-orange suede tunic with the pale cream laced V-neck is visible at the bottom edge.

Per-image checks (re-run before selecting): same person as input 2; the requested view (02 faces IMAGE LEFT);
whole head, hair and both ears inside the frame; true transparent background with no halo; square.

## Do NOT
- change the face, hair, ears, colours or age; add a hat, jewellery or a beard; stylise as a cartoon; add text, a
  floor, a background, a glow or a shadow; crop.
