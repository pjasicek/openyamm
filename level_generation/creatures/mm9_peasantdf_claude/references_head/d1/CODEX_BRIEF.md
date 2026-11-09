# Codex brief: HD HEAD turnaround for the MM9 dwarf townswoman PeasantDF1, skin pdf1a (mm9_peasantdf_claude, d1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdf_claude/references_head/d1/`. Do not edit any other file, do not run builds,
do not call Meshy. Use your built-in image generation tool.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_pdf1a.png` — close renders of the ORIGINAL Might and Magic IX model's head (front,
   profile facing left, three-quarter, profile facing right, back): FACE AND HAIR/HEADDRESS AUTHORITY. Its low
   resolution, faceting and dark shading are NOT the design.
2. `references_hd/d1/00_three_quarter.png` — the approved HD body master of this character: exact identity, face, hair/headdress and colour authority.
3. `references_hd/d1/01_front.png` — a second approved HD master view of the same character.
4. `references_hd/mm9_skin_x4_pdf1a.png` — the original skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust: she looks toward IMAGE RIGHT and toward the viewer; eye level |
| `02_profile.png` | pure 90-degree profile of the character's LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head and shoulders |

Generate 01 first; then make 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D TEXTURING head reference of an EXISTING Might and Magic IX
character (inputs 1-3). Not a new design. ONE bust only: the whole head with all hair/headdress, the neck and the top
of the shoulders, centred with generous margins, never cropped. Near-orthographic camera at eye level, head level.
A WARM, calm, kindly expression: mouth CLOSED with natural relaxed lips and a faint smile (not pouting, not swollen,
one single pair of lips with no second lip line), eyes clearly OPEN and relaxed with irises and pupils visible (not
staring wide, not fierce, not squinting), natural lids: no red rims, no pale crescent under the lower lid, no dark
wedges at the eye corners, no light band or plate around the eyes. A natural nose with soft shading, no dark
nostril smudges. Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows (the image is
baked into a texture). Sharp fine detail: skin pores, lashes, brows, hair strands, linen weave. Clean edges between
skin and hair/headdress: no stray wisps on the skin, no pale band at the hairline. The neck skin is plain and
continuous with the face, with no line or band across it.

## Identity
A DWARF townswoman about thirty-five (inputs 1-3): fair warm skin with a few faint freckles, a pleasant face,
grey-blue eyes, one fine light-brown brow line above each eye, natural soft rose lips (NOT red lipstick); thick
straight golden-wheat BLONDE hair parted in the centre, falling smoothly to the shoulders in one compact rounded volume
that covers the ears and frames the face (no ears visible); at the back two plaited braids lie flat in the hair and end
at the nape (no clasps or beads). At the bottom edge: bare neck and collarbones down to the wide rounded cream linen
neckline (no necklace on the neck).

Per-image checks (re-run before selecting): same woman as input 2; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); whole head and hair/headdress inside the frame; mouth closed, eyes open with irises; one brow
line; true transparent background; square.

## Do NOT
- change the face, hair/headdress, colours or age; show the ears; add earrings, beads or clasps near the ears, a
  necklace on the neck, a hat, circlet or ribbons; red lipstick; a fierce, cold, staring or sad expression; stylise as
  a cartoon; add text, a floor, a background or a shadow; crop.
