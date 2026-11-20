# Codex brief: HD HEAD turnaround for the MM9 human boy PeasantBoy1, skin PEASANTBOY1 (mm9_peasantboy_claude, tier A)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantboy_claude/references_head/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no
native sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png` — close renders of the ORIGINAL Might and Magic IX model's head (front,
   profile facing left, three-quarter, profile facing right, back): FACE AND HAIR AUTHORITY. Its low resolution,
   faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this boy: exact identity, face
   structure, hair and colour authority for the HD look. The heads you make must be THIS boy.
3. `references_hd/01_front.png` — the approved HD front master (same boy, front).
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
Near-orthographic camera at eye level, head level, a calm, warm, friendly expression, mouth CLOSED with natural relaxed
lips in a gentle smile (not pouting, not swollen, no teeth), eyes clearly OPEN and relaxed with the blue irises and
pupils visible (not staring wide, not squinting), natural lids with no red rims. Even soft neutral studio lighting, no
dramatic light, no rim light, no strong shadows (the image is baked into a texture). Sharp fine detail: a child's
smooth skin with faint freckles, brows, lashes, lips, hair strands, linen weave. ONE light-brown brow above each eye and
nothing else between brow and eye: no light outlined band, no second brow line, no pale plate around the eyes. Clean
edges between skin and hair: the hair has its own colour with no skin tone bleeding into it, no pale band where the
fringe meets the forehead. The neck skin is visible and continuous with the face, plain skin down to the collar.

## Identity
A medieval village BOY about ten years old (inputs 1-2): fair skin with a little colour in the cheeks, a slim oval
child's face, a small straight nose, blue eyes, light brown brows; thick straight medium chestnut-brown hair in a
page-boy BOB: a fringe across the forehead, the hair falling straight at the sides and back to the jaw line and
COVERING THE EARS completely, cut level at the bottom. At the bottom edge: the small round cream linen shirt collar
and the dark brown ribbed wool vest's laced V neckline with cream cord lacing.

Per-image checks (re-run before selecting): same boy as input 2; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); whole head and hair inside the frame; mouth closed, eyes open with irises; one brow line; ears
hidden by the hair; true transparent background; square.

## Do NOT
- change the face, hair, colours or age; show the ears; make the hair short or long past the jaw; add a hat, hood,
  headband or jewellery; give him a fierce, cold or sad expression; stylise as a cartoon; add text, a floor, a
  background or a shadow; crop.
