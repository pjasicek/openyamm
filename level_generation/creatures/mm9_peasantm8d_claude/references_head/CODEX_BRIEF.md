# Codex brief: HD HEAD turnaround for the MM9 old elf commoner PeasantM8d (mm9_peasantm8d_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm8d_claude/references_head/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no
native sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

The heads will be PAINTED onto an existing 3D head (built for another character on the same MM9 mesh): keep that
head's shape, framing and hair VOLUME (input 4), with this character's face, hair colour and ears.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png` — close renders of the ORIGINAL Might and Magic IX model's head (front, left
   profile, three-quarter, right profile, back): FACE, HAIR AND EAR AUTHORITY. Its low resolution and faceting are NOT
   the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this character: exact identity,
   face, hair, ears and colour authority for the HD look. The heads you make must be THIS person.
3. `references_hd/mm9_skin_x4.png` — the original skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.
4. `mm9_forad_claude/v2/references_head/selected_views_review.png` — HEAD SHAPE, FRAMING AND HAIR VOLUME AUTHORITY
   ONLY (another man): the four views to make, in the same framing; the hair swept back from the face into a low
   ponytail at the nape. Do NOT copy his face, scar, goatee, dark hair, skin tone, necklace or black-and-gold vest.

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
and the top of the shoulders, centred with generous margins, never cropped (both ear tips fully inside the frame).
Near-orthographic camera at eye level, head level and straight (not tilted or turned except as the view requires),
neutral calm and warm expression, mouth closed. Even soft neutral studio lighting, no dramatic light, no rim light,
no strong shadows (the image is baked into a texture). Sharp fine detail: skin pores and wrinkles, brows, lashes,
moustache and hair strands, cloth weave. One clean set of features: a single brow line above each eye, natural eye
lids without pale bands, one nose with two nostrils, the lips closed under the moustache. The neck skin and the skin
under the jaw and chin clearly visible and continuous with the face. Clean edges between skin and hair: the hair has
its own colour with no skin tone bleeding into it.

## Identity
An OLD ELF townsman: fair rosy-tan weathered skin with fine wrinkles; clear light blue eyes under bushy WHITE brows;
a straight nose; a full white WALRUS MOUSTACHE drooping round the corners of the mouth; clean-shaven chin and cheeks
(no beard); a gentle, kindly, calm face. Thick WHITE / silver-grey hair swept straight back from a high forehead,
gathered at the nape into a short low ponytail. Long POINTED ELF EARS, skin coloured, sticking out sideways and up
and back from the sides of the head, clear of the hair. At the bottom edge: the round collar of a mossy olive-green
flecked tweed tunic with a short V slit at the throat laced with a thin brown cord, a cream linen undershirt showing
in the slit.

Per-image checks (re-run before selecting): same person as input 2; the requested view (02 faces IMAGE LEFT);
whole head, hair and both ears inside the frame; true transparent background with no halo; square.

## Do NOT
- change the face, hair, ears, colours or age; add a beard, earrings, beads, braids with beads, a hat or jewellery;
  stylise as a cartoon; add text, a floor, a background, a glow or a shadow; crop; make the expression stern or cold.
