# Codex brief: HD HEAD turnaround for the MM9 Jarl Sven Svenssen (mm9_sven_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_sven_claude/references_head/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png` — close renders of the ORIGINAL Might and Magic IX model's head (three-quarter,
   front, left profile, back, right profile): FACE, EXPRESSION AND HAIR AUTHORITY. Its low resolution, faceting and
   dark shading are NOT the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this character: exact identity,
   face structure, hair and colour authority for the HD look. The heads you make must be THIS man.
3. `references_hd/01_front.png` — the approved HD front master (same man, front).
4. `references_hd/mm9_skin_x4.png` — the original skin texture enlarged 4x (the face painting with the braids is top
   left), SURFACE MATERIAL AND COLOUR ONLY.

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
Near-orthographic camera at eye level, head level and straight (no tilt), a warm friendly expression: a gentle smile
with the LIPS CLOSED (no teeth, no open mouth, lips relaxed and natural, not pushed forward). Even soft neutral studio
lighting, no dramatic light, no rim light, no strong shadows (the image is baked into a texture). Sharp fine detail:
skin pores, fine wrinkles, brows, lashes, lips, beard and hair strands.

EYES AND BROWS (important, the texture is seen up close and from slightly above): the eyes clearly OPEN, natural almond
shape, NOT squinting despite the smile, with visible light-blue irises and pupils, natural upper lids and lashes, the
whites only a little visible, only a faint natural warm tone at the lid rims (no red or pink rims, no bags drawn as
rings); laugh lines only at the outer corners. ONE brow per side: a single thick brown brow, relaxed (not knitted, not
angry); the skin between the brow and the upper lid is ordinary skin of the same tone as the forehead, with no pale or
outlined band, no second brow line and no makeup look. The nostrils are soft natural shading, not dark holes. The
hairline meets the forehead with natural fine hairs, no pale or jagged band at the edge.

## Identity
Sven Svenssen ("Sven Forkbeard"), Jarl of Arslegard, a big human Norse chieftain of about forty-five: fair weathered skin
with a warm tan and ruddy cheeks, a broad strong face, a straight strong nose, light blue eyes; thick brown brows; a FULL
brown beard and moustache, thick and trimmed, a little longer at the chin (the beard covers the chin, jaw and upper lip
edge; the cheeks above it are bare skin; the lips show between moustache and beard); long thick wavy brown hair parted
in the middle, falling past the ears to the shoulders, with a thin plaited BRAID hanging at each side of the face in
front of the ears down to the collarbones. The neck under the beard is skin. At the bottom edge: the tawny fur mantle
over the shoulders, a necklace of amber-gold plaques and the top of the grey chain mail (as input 2).

Per-image checks (re-run before selecting): same man as input 2; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); eyes open with irises; one relaxed brow per side; lips closed; head not tilted; whole head and hair
inside the frame; true transparent background; square.

## Do NOT
- change the face, hair, colours or age; remove the beard or braids; open the mouth or show teeth; add a hat, helmet,
  horns, crown, hood or headwear; stylise as a cartoon; add text, a floor, a background or a shadow; crop.
