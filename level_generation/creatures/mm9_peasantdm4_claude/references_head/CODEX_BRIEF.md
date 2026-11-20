# Codex brief: HD HEAD turnaround for the MM9 dwarf townsman PeasantDM4, skin A (mm9_peasantdm4_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdm4_claude/references_head/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png` — close renders of the ORIGINAL Might and Magic IX model's head (front,
   profile facing left, three-quarter, profile facing right, back): FACE, CAP, BEARD AND HAIR AUTHORITY. Its low
   resolution, faceting and shading are NOT the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this character: exact identity,
   face structure, cap, beard, hair and colour authority for the HD look. The heads you make must be THIS dwarf.
3. `references_hd/01_front.png` — the approved HD front master (same dwarf, front).
4. `references_hd/mm9_skin_x4_a.png` — the original skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust: he looks toward IMAGE RIGHT and toward the viewer, as in input 2; eye level |
| `02_profile.png` | pure 90-degree profile of the character's LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head and shoulders |

Generate 01 first; then make 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views. A hard-edged opaque figure, no glow or halo.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING
Might and Magic IX character (inputs 1-3). Not a new design. Output ONE bust only: the whole head with the cap and all
hair, the neck and the top of the shoulders, centred with generous margins, never cropped.
Near-orthographic camera at eye level, head level, a calm, warm, friendly expression: mouth CLOSED with natural relaxed
lips under the moustache (one pair of lips only, no second lip line, not pouting, not swollen), eyes clearly OPEN and
relaxed with the green-grey irises and pupils visible (not staring wide, not squinting to slits), natural lids with no
red rims and no pale crescent under the lower lid. Even soft neutral studio lighting, no dramatic light, no rim light,
no strong shadows (the image is baked into a texture). Sharp fine detail: skin pores, fine wrinkles at the eyes, brows,
lashes, lips, beard and hair strands, woven wool, embroidery. ONE natural ginger brow above each eye and nothing else
between brow and eye: no light outlined band, no second brow line, no pale plate around the eyes. A natural nose with
one pair of nostrils seen from below, clean skin under it. Clean edges between skin and hair: hair and beard have their
own colour with no skin tone bleeding into them; the beard and hair are soft natural strands (no net or mesh pattern of
thin crossing lines). The neck skin under the beard is plain skin.

## Identity
A middle-aged dwarf townsman about fifty (inputs 1-2): fair skin with rosy cheeks, a broad friendly face, a broad nose,
calm warm green-grey eyes, natural ginger eyebrows; NO visible ears: thick copper-red hair falls straight from under the
cap over the ears to the shoulders at the sides and back; a full copper-red wavy beard and moustache, medium length,
ending a little below the chin. The cap: a snug rounded brimless skullcap of ochre-brown woven wool with a slightly
peaked crown, a band round its lower edge of dark blue cloth embroidered with a gold-tan running knotwork pattern, and a
small silver Celtic-knot medallion on the front of the crown. At the bottom edge: the ochre-brown woven tunic's
shoulders with the dark blue knotwork-banded vest edges and the cream linen shirt at the neck, as in input 2.

Per-image checks (re-run before selecting): same dwarf as input 2; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); whole head, cap and hair inside the frame; mouth closed, eyes open with irises; one brow line; no
ears visible; nothing in the hair or beard; true transparent background; square.

## Do NOT
- change the face, beard, hair, cap, colours or age; show the ears; add beads, rings, ties, clasps or braids to the
  hair or beard; make the beard very long; add jewellery; give him a fierce, frowning, cold or staring look; stylise
  as a cartoon; add text, a floor, a background or a shadow; crop.
