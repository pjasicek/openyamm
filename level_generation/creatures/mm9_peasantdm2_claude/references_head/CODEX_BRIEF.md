# Codex brief: HD HEAD turnaround for the MM9 dwarf townsman PeasantDM2, skin A (mm9_peasantdm2_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdm2_claude/references_head/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png` — close renders of the ORIGINAL Might and Magic IX model's head (front,
   profile facing left, three-quarter, profile facing right, back): FACE, BEARD AND HAIR AUTHORITY. Its low
   resolution, faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this character: exact identity,
   face structure, beard, hair and colour authority for the HD look. The heads you make must be THIS dwarf.
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
`selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING
Might and Magic IX character (inputs 1-3). Not a new design. Output ONE bust only: the whole head with all hair, the
neck, and the top of the shoulders, centred with generous margins, never cropped (hair fully inside the frame).
Near-orthographic camera at eye level, head level, kind calm expression, mouth CLOSED with natural relaxed lips (not
pouting, not swollen), eyes clearly OPEN and relaxed with the blue irises and pupils visible (not staring wide, not
squinting to slits), natural lids with no red rims. Even soft neutral studio lighting, no dramatic light, no rim light,
no strong shadows (the image is baked into a texture). Sharp fine detail: skin pores, fine age wrinkles, brows, lashes,
lips, beard and hair strands, wool knit. ONE bushy white brow above each eye and nothing else between brow and eye:
no light outlined band, no second brow line, no pale plate around the eyes. Clean edges between skin and hair: hair
and beard have their own colour with no skin tone bleeding into them, and the bald forehead and scalp are clean skin
(no stray wisps, no pale band where the hair begins at the sides). The neck skin under the beard is visible and
continuous with the face, plain skin down to the tunic's round neckline.

## Identity
An ELDERLY dwarf townsman about seventy (inputs 1-2): fair ruddy weathered skin, a kind grandfatherly face with gentle
wrinkles at the eyes and forehead, a long straight nose, bright blue eyes, bushy white eyebrows; BALDING: a high bare
forehead and a bare top front of the scalp, the remaining hair growing from the sides and back of the head; long
thick cream-white hair from the sides and back falling straight to the shoulders, covering the ears, with one thick
braid on each side of the face in front of the ear hanging to the jaw; a full white beard and moustache, medium length,
ending a little below the chin in a soft point. At the bottom edge: the dark charcoal-brown ribbed knitted wool tunic
with a plain round neckline (no embroidery, no jewellery).

Per-image checks (re-run before selecting): same dwarf as input 2; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); whole head and hair inside the frame; mouth closed, eyes open with irises; one brow line; true
transparent background; square.

## Do NOT
- change the face, beard, hair, colours or age; give him a full head of hair on top; make the beard very long; add a
  hat, hood, headband or jewellery; stylise as a cartoon; add text, a floor, a background or a shadow; crop.
