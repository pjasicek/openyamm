# Codex brief: HD HEAD turnaround for MM9 Krohn, skin KROHN (mm9_krohn_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_krohn_claude/references_head/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no
native sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_k.png` — close renders of the ORIGINAL Might and Magic IX model's head (front,
   profile facing left, three-quarter, profile facing right, back): FACE, CROWN, HAIR AND BEARD AUTHORITY. Its low
   resolution, faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this man: exact identity, face
   structure, crown, hair, beard and colour authority for the HD look. The heads you make must be THIS man.
3. `references_hd/01_front.png` — the approved HD front master (same man, front).
4. `references_hd/mm9_skin_x4_k.png` — the original skin texture enlarged, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust: he looks toward IMAGE RIGHT and toward the viewer, as in input 2; eye level |
| `02_profile.png` | pure 90-degree profile: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head and shoulders |

Generate 01 first; then make 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING
Might and Magic IX character (inputs 1-3). Not a new design. Output ONE bust only: the whole head with the crown, all
the hair and the whole beard, the neck and the top of the shoulders, centred with generous margins, never cropped.
Near-orthographic camera at eye level, head level. Expression: CALM, WARM and KINDLY, a wise old king at ease - NOT
angry, NOT fierce, NOT stern, NOT sad: relaxed brows, a gentle closed-mouth hint of a smile under the moustache (the
lips just visible, natural, not pouting, no teeth), eyes clearly OPEN and relaxed with the pale BLUE irises and
pupils visible, natural lids with no red rims and no dark bags. Even soft neutral studio lighting, no dramatic light,
no rim light, no strong shadows (the image is baked into a texture). Sharp fine detail: weathered tanned skin pores,
fine lines at the eyes, brows, lashes, beard and hair strands, embossed gold. ONE brow above each eye and nothing else
between brow and eye: no light outlined band, no second brow line. Clean edges between skin and hair: no pale band
along the hairline or the beard line. ONE nose with one pair of nostrils.

## Identity
Krohn (inputs 1-2), an old Norse warrior god-king of about sixty: a broad strong face, a straight strong nose, high
cheekbones, deep-set eyes, tanned weathered fair skin with warm ruddy cheeks; thick grey-brown brows. A FULL long
beard and moustache, brown streaked with grey and white (whiter at the chin), reaching the upper chest. Long straight
dark-brown hair from a centre parting, covering the ears, falling behind the shoulders and down the back. A GOLD CROWN
on the forehead: an embossed gold band set with small jewels, three tall pointed gold spikes (front centre with a
diamond-shaped jewel, and one above each temple) with small points between. At the bottom edge: the brown fur
mantle on the shoulders and the top of the blue-grey chain mail at the chest.

Per-image checks (re-run before selecting): same man as input 2; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); whole head, crown, hair and beard inside the frame; eyes open with irises; calm warm expression;
one brow line; true transparent background; square.

## Do NOT
- change the face, crown, hair, beard, colours or age; make him young; give him a fierce, angry, stern or cold look;
  shorten the hair or beard; bring the hair forward over the chest; add a helmet, hood, earrings or other jewellery
  than the crown; stylise as a cartoon; add text, a floor, a background or a shadow; crop.
