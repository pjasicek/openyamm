# Codex brief: HD HEAD turnaround for the MM9 unique NPC Tryggva Ravenlocks (mm9_tryggva_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_tryggva_claude/references_head/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png` — close renders of the ORIGINAL Might and Magic IX model's head (three-quarter,
   front, left profile, back, right profile): FACE AND HAIR AUTHORITY. Its low resolution, faceting and dark shading
   are NOT the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this character: exact identity,
   face structure, hair and colour authority for the HD look. The heads you make must be THIS man.
3. `references_hd/01_front.png` — the approved HD front master (same man, front).
4. `references_hd/mm9_skin_x4.png` — the original skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY (the face
   painting at top left is the best close view of his face).

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
Near-orthographic camera at eye level, head level, calm expression with a faint closed-mouth smile, lips together and
of natural width. Eyes OPEN and relaxed, light blue irises clearly visible, natural upper lids, no red rims, no dark
sockets. Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows (the image is baked into
a texture). Sharp fine detail: skin pores, fine wrinkles and smile lines, ONE pair of straight dark brows, lashes, lips,
hair strands, fur. The skin between brows and eyes is ordinary skin continuous with the forehead and cheeks: no band,
plate, outline or second brow line round the eyes. The neck skin under the jaw and chin must be clearly visible and
continuous with the face, the same skin tone as the face (no paler or redder panel on the neck). Clean edges between
skin and hair: the hairline is a soft natural transition with dark hair, no pale or jagged band where hair meets the
forehead; hair has its own colour with no skin tone bleeding into it, and skin carries no hair colour.

## Identity
Tryggva Ravenlocks, a Norse jarl about forty-five: fair weathered skin with a warm ruddy tan, a long lean face with
high cheekbones, deep smile lines and fine wrinkles, a long straight nose, light blue eyes under straight dark brows;
clean-shaven. Long straight raven-black hair with a cool grey sheen, centre-parted, falling past the shoulders and down
the back, tucked behind normal human ears; one thin black braid hangs from each temple down in front of each shoulder.
At the bottom edge: the shaggy grey-brown fur mantle with pale cream-gold tips on the shoulders, the cream-gold banded
collar and thin gold torc at the neck, and the top of the old-gold embroidered front panel on a near-black-brown
knitted tunic (as input 2).

Per-image checks (re-run before selecting): same man as input 2; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); whole head and hair inside the frame; eyes open with visible irises, one brow pair, mouth closed;
true transparent background; square.

## Do NOT
- change the face, hair, colours or age; add a beard, moustache, hat, hood, helmet or headwear; make the ears pointed;
  stylise as a cartoon; add text, a floor, a background or a shadow; crop.
