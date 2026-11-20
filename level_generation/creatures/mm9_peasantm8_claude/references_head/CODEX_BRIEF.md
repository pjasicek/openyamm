# Codex brief: HD HEAD turnaround for the MM9 shopkeeper PeasantM8 (mm9_peasantm8_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm8_claude/references_head/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no
native sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

The heads will be PAINTED onto an existing 3D head (built for another character on the same MM9 mesh): keep that
head's shape and framing (input 4), with this character's face and hair. The 3D head is a smooth rounded skull with
NO ponytail: paint the hair flat on the skull.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png` — close renders of the ORIGINAL Might and Magic IX model's head (front, left
   profile, three-quarter, right profile, back): FACE AND HAIR AUTHORITY. Its low resolution and faceting are NOT
   the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this character: exact identity,
   face, hair and colour authority for the HD look. The heads you make must be THIS person.
3. `references_hd/mm9_skin_x4.png` — the original skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.
4. `mm9_forad_claude/v2/references_head/selected_views_review.png` — HEAD SHAPE AND FRAMING AUTHORITY ONLY (another
   man): the four views to make, in the same framing and head size. Do NOT copy his face, scar, goatee, dark hair,
   PONYTAIL, skin tone, necklace or black-and-gold vest.

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
TASK CONTEXT — GAME ASSET: faithful high-definition 3D TEXTURING head reference of an EXISTING Might and Magic IX
character (inputs 1-2). Not a new design. Output ONE bust only: the whole head with all hair and both ears, the neck,
and the top of the shoulders, centred with generous margins, never cropped. Near-orthographic camera at eye level,
head level and straight (not tilted or turned except as the view requires), neutral calm and warm expression, mouth
closed. Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows (the image is baked
into a texture). Sharp fine detail: skin pores, brows, lashes, hair strands, cloth weave. One clean set of features:
a single thin brow line above each eye (no second brow), natural eye lids WITHOUT pale bands, light crescents or
outlines under or around the eyes, clear irises, one nose with exactly two nostrils, ONE pair of thin closed lips
(no second lip line, no pink plate round the mouth). The neck skin and the skin under the jaw and chin clearly
visible and continuous with the face. Clean edges between skin and hair: the hair has its own colour with no skin
tone bleeding into it, and the bare scalp has smooth plain skin with no strand pattern on it.

## Identity
A middle-aged HUMAN shopkeeper (about 45-50): fair pale-pink skin with a little colour in the cheeks; a long oval face,
a straight long nose, light grey-blue eyes under thin light-brown brows, faint lines round the eyes; clean-shaven (no
beard, no moustache, no stubble); thin closed lips, a mild, kind, calm expression. A HIGH BALDING head: the forehead
and the whole top of the head are bare smooth skin back to the crown; short straight dark-blond / light honey-brown
hair covers only the sides and the back of the head, combed back and lying flat against the skull, ending in a
neatly trimmed edge at the nape (no ponytail, no long hair, nothing hanging). Normal human ears, skin coloured, fully
visible, with no hair strands painted across them. At the bottom edge: the round collar of a plain chocolate-brown
wool tunic with a short V slit at the throat laced with a thin brown leather cord, a cream linen undershirt showing
in the slit.

Per-image checks (re-run before selecting): same person as input 2; the requested view (02 faces IMAGE LEFT);
whole head, hair and both ears inside the frame; bald top, short hair only at the sides and back; true transparent
background with no halo; square.

## Do NOT
- change the face, hair, colours or age; add a beard, moustache, ponytail, earrings, beads, a hat or jewellery;
  give him a full head of hair; stylise as a cartoon; add text, a floor, a background, a glow or a shadow; crop;
  make the expression stern, fierce or cold.
