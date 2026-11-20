# Codex brief: HD HEAD turnaround for the MM9 commoner PeasantM1, skin A (mm9_peasantm1_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm1_claude/references_head/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png` — close renders of the ORIGINAL Might and Magic IX model's head (front, left
   profile, three-quarter, back): FACE AND HAIR AUTHORITY. Its low resolution, faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this character: exact identity,
   face structure, hair and colour authority for the HD look. The heads you make must be THIS man.
3. `references_hd/01_front.png` — the approved HD front master (same man, front).
4. `references_hd/mm9_skin_x4_a.png` — the original skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust from the character's RIGHT side: he looks toward IMAGE RIGHT and toward the viewer, as in input 2; eye level |
| `02_profile.png` | pure 90-degree profile of the character's LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head and shoulders |

Generate 01 first; then make 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING
Might and Magic IX character (inputs 1-3). Not a new design. Output ONE bust only: the whole head with all hair, the
neck, and the top of the shoulders, centred with generous margins, never cropped (hair fully inside the frame).
Near-orthographic camera at eye level, head level, calm expression with the slight half-smile of input 2, mouth
CLOSED. Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows (the image is baked into
a texture). Sharp fine detail: skin pores, fine wrinkles, brows, lashes, lips, beard and hair strands, wool weave.
The neck skin under the jaw and chin must be clearly visible and continuous with the face (the beard follows the jaw
line; the neck below it is skin; no collar hiding the jaw line). Clean edges between skin and hair: hair has its own
colour with no skin tone bleeding into it, and skin carries no hair colour except the beard.

## Identity
An ordinary village man in his late thirties: a long face, straight nose, light blue eyes, fair skin with ruddy
cheeks; a full short dark-brown beard and moustache trimmed close along the jaw; thick wavy dark-brown hair covering
the ears and falling to the nape (input 1 profile and back). At the bottom edge: the olive-brown wool jacket's soft
shawl collar around the neck and the cream linen shirt's laced V opening (as input 2).

Per-image checks (re-run before selecting): same man as input 2; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); whole head and hair inside the frame; mouth closed; true transparent background; square.

## Do NOT
- change the face, hair, colours or age; add a hat, hood worn up, jewellery or headwear; stylise as a cartoon; add
  text, a floor, a background or a shadow; crop.
