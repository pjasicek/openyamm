# Codex brief: HD HEAD turnaround for the MM9 dwarf boy, boy B, skin DWARFBOY2 (row 68 Townsfolk Child) (mm9_peasantdboy_claude, tier B)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdboy_claude/references_head_b/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Context: MM9 draws two different dwarf boys on ONE 3D body and head mesh by changing only the painted skin. Boy A
already has approved HD head views (inputs 2-5). This is a DIFFERENT boy (input 1). These views will be painted onto
the SAME head mesh as A's, so the head and neck SILHOUETTE, size, skull shape, hair volume and outline (a page-boy bob
to the jaw over the tops of the ears), framing, camera and lighting must match inputs 2-5 view for view; only the face, skin,
hair colour, hair texture and the collar change.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png` — close renders of the ORIGINAL Might and Magic IX model's head with this
   boy's skin (front, left profile, three-quarter, right profile, back): FACE AND HAIR AUTHORITY for this boy. Its low
   resolution, faceting and dark shading are NOT the design.
2. `references_head/01_front.png` — approved boy A front bust: silhouette, framing, camera and light template.
3. `references_head/00_three_quarter.png` — approved boy A three-quarter bust: same role.
4. `references_head/02_profile.png` — approved boy A left profile bust: same role.
5. `references_head/03_back.png` — approved boy A back bust: same role.
6. `references_hd/mm9_skin_x4_b.png` — the original skin texture enlarged, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, the same size as inputs 2-5, unresized returns)
| File | View (match the corresponding A input exactly in pose, framing and silhouette) |
|---|---|
| `01_front.png` | straight FRONT bust (as input 2; generate FIRST) |
| `00_three_quarter.png` | three-quarter bust looking toward IMAGE RIGHT (as input 3) |
| `02_profile.png` | 90-degree LEFT profile, face points to IMAGE LEFT (as input 4) |
| `03_back.png` | straight BACK of the head and shoulders (as input 5) |

Generate 01 first; then 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME boy. At most
ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt,
inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Identity (input 1)
A DIFFERENT dwarf boy about eight: a round, chubby face with full rosy cheeks and a big cheerful smile kept
closed-mouthed (MM9 shows teeth: do NOT show teeth), friendly crinkled eyes (still open, blue-grey irises visible), light
ginger-blond brows, a small snub nose, fair freckled skin; strawberry-blond / light ginger hair in the same jaw-length bob
outline as A's, with a shaggier straight fringe over the brows (lighter and redder than A's chestnut hair). At the bottom
edge: the stand-up collar of a plain DARK BROWN ribbed wool tunic (no embroidery), a glimpse of a cream shirt with dark
brown lacing at the throat (input 6 colours).

## Common prompt content
Faithful high-definition TEXTURING reference of an EXISTING Might and Magic IX character. A calm, warm, friendly
expression. Even soft neutral studio lighting, no dramatic light, no strong shadows (baked into a texture). Sharp fine
detail: a child's smooth skin, brows, lashes, lips, hair strands, cloth weave. The neck skin under the jaw is visible and
continuous with the face. Clean edges between skin and hair: no skin tone bleeding into the hair, no hair colour on the
skin, no pale band where the fringe meets the forehead. Mouth CLOSED with natural relaxed lips in a gentle smile (not
pouting, no teeth), eyes OPEN and relaxed with the irises visible (not staring, not slits), no red rims; ONE brow line
above each eye and no light band or plate between brow and eye. The ears stay under the hair as in A's views.

Per-image checks (re-run before selecting): this boy's face and colours (input 1) on A's silhouette (inputs 2-5); the
requested view; whole head and hair inside the frame; mouth closed, eyes open with irises; ears mostly under the hair; true
transparent background; the same size as inputs 2-5.

## Do NOT
- change the silhouette, hair outline or framing from A's; add a hat, hood, headband or jewellery; give
  him a fierce, cold or sad expression; make him older than about eight; add a beard; stylise as a cartoon; add text, a floor, a
  background or a shadow; crop.
