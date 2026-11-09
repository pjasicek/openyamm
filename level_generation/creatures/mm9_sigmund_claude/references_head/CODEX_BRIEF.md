# Codex brief: HD HEAD turnaround for MM9 Sigmund the Stressed, skin SIGMUND (mm9_sigmund_claude, tier A)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_sigmund_claude/references_head/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no
native sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png` — close renders of the ORIGINAL Might and Magic IX model's head (front,
   profile facing left, three-quarter, profile facing right, back): FACE AND HAIR AUTHORITY. Its low resolution,
   faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this man: exact identity, face
   structure, hair and colour authority for the HD look. The heads you make must be THIS man.
3. `references_hd/01_front.png` — the approved HD front master (same man, front).
4. `references_hd/mm9_skin_x4_a.png` — the original skin texture enlarged, SURFACE MATERIAL AND COLOUR ONLY.

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
Near-orthographic camera at eye level, head level. Expression: a calm, kind but careworn, slightly worried man (brows
gently raised and drawn together, faint forehead lines) - NOT angry, NOT fierce, NOT sad; mouth CLOSED with natural
relaxed lips (not pouting, no teeth, no lipstick), eyes clearly OPEN and relaxed with the pale blue-grey irises and pupils
visible, natural lids with no red rims and no dark bags. Even soft neutral studio lighting, no dramatic light, no rim
light, no strong shadows (the image is baked into a texture). Sharp fine detail: weathered skin pores, faint lines,
brows, lashes, lips, hair strands, mail rings. ONE brow above each eye and nothing else between brow and eye: no light
outlined band, no second brow line. Clean edges between skin and hair: no skin tone bleeding into the hair, no pale band
along the hairline. The neck skin is visible and continuous with the face down to the collar. Clean-shaven: no beard,
no stubble shadow.

## Identity
Sigmund (inputs 1-2), a Norse-styled man in his forties: a long narrow face, high cheekbones, a straight long nose, a
firm clean-shaven chin, fair weathered skin; thick wavy golden-blond hair parted in the middle, swept back from the
forehead and the temples and falling behind the ears to the shoulders, longer at the back; both ears visible beside the
hair. At the bottom edge: the grey riveted chain mail of his hauberk and the broad ivory-and-gold torc collar of short
bars round the base of the neck with a round grey stone medallion.

Per-image checks (re-run before selecting): same man as input 2; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); whole head and hair inside the frame; mouth closed, eyes open with irises; one brow line; ears
visible; true transparent background; square.

## Do NOT
- change the face, hair, colours or age; add a beard, moustache or stubble; give him a fierce, angry or cold look; make the hair short; add a hat, hood,
  headband or other jewellery than the torc; give him a fierce, cold or sad expression; stylise as a cartoon; add text, a floor, a
  background or a shadow; crop.
