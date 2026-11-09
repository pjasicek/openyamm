# Codex brief: HD HEAD turnaround for the female Honk worshipper (MM9 monster, skin HONKF1) (mm9_honkfemale_claude/v2)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_honkfemale_claude/v2/references_head/`. Do not edit
any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png` — close renders of the ORIGINAL Might and Magic IX model's head (front, left
   profile, three-quarter): FACE, HAIR AND HEADWEAR AUTHORITY. Its low resolution, faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this character: exact identity,
   face structure, hair and colour authority for the HD look. The heads you make must be THIS person.
3. `references_hd/01_front.png` — the approved HD front master (same person, front).
4. `references_hd/mm9_skin_x4.png` — the original skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust, the character's RIGHT side toward the camera (face turned ~35 deg toward IMAGE LEFT... i.e. he/she looks toward image right as in input 2), eye level |
| `02_profile.png` | pure 90-degree profile of the character's LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head and shoulders |

Generate 01 first; then make 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING
Might and Magic IX character (inputs 1-3). Not a new design. Output ONE bust only: the whole head with all hair and
headwear, the neck, and the top of the shoulders, centred with generous margins, never cropped (hair, hood and braids
fully inside the frame). Near-orthographic camera at eye level, head level, neutral expression as in the inputs,
mouth as in input 2. Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows (the image
is baked into a texture). Sharp fine detail: skin pores, wrinkles, brows, lashes, lips, beard/hair strands, cloth
weave. The neck skin and the skin under the jaw and chin must be clearly visible and continuous with the face (no
collar hiding the jaw line) so the chin underside and neck read as one surface. Clean edges between skin and hair or
headwear: hair and headwear have their own colours with no skin tone bleeding into them.

## Identity
A Honk priestess, a slim adult human woman about thirty, exactly as input 2: a calm, pretty oval face, a slight
closed-mouth smile (no teeth), blue-grey eyes looking straight ahead, thin arched brows, light skin. Pale ash-blonde hair
parted at the centre framing the forehead. The hat exactly as input 2 (a conical silver goose helmet with embossed folded
wings, a gold knotwork brim and a small gold goose head with a forward-pointing beak on top), level on the head, entirely
inside the frame: leave space above it. A plain cream veil from under the brim down the back of the head and neck. Two
thin plaited honey-brown braids from the temples, hanging straight down in front of the shoulders with a small air gap to
the neck. The neck is visible with the small V neckline, the silver chain and the top of the cream linen robe at the
bottom edge.

Per-image checks (re-run before selecting): same person as input 2; the requested view (02 faces IMAGE LEFT);
whole head, hair and headwear inside the frame; true transparent background; square.
