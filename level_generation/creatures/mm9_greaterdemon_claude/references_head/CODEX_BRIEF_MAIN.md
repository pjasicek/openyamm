# Codex brief: HD HEAD turnaround, MAIN HEAD of the MM9 Greater Demon (mm9_greaterdemon_claude, 2026-10-30 rework)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_greaterdemon_claude/references_head/`
(files prefixed `main_`, raw returns in `references_head/raw_main/`). Do not edit any other file, do not run builds,
do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9.

These four images will be projected by an AI texturing tool onto OUR 3D head mesh (input 1), so the head in every
image must have the SAME SHAPE, POSE, CAMERA and FRAMING as the matching grey view in input 1.

## Inputs (attached, in order)
1. `references_head/shape_main_views.png` — grey renders of OUR head mesh, four views left to right: FRONT,
   THREE-QUARTER (from the creature's RIGHT front), LEFT PROFILE (snout points to IMAGE LEFT), BACK (from behind and
   above). SHAPE, POSE, SILHOUETTE AND FRAMING AUTHORITY: horns, crest spikes, open jaw, tongue, teeth, neck cut
   exactly as here. Grey is only the untextured mesh; transparent pixels are background.
2. `references_head/hd_master_main_head_crops.png` — crops of the APPROVED HD body masters of this creature
   (three-quarter, front, left side): COLOUR, MATERIAL AND DETAIL AUTHORITY for the HD look. The head you paint must
   be THIS head.
3. `references_head/mm9_head_views.png` — the ORIGINAL Might and Magic IX low-poly model (top row: main head; bottom
   row: arm head): design authority only; its blur and faceting are NOT the design.
4. `references_hd/mm9_skin_tier1_x4.png` — the original skin texture x4, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized)
| File | View (match the same view of input 1) |
|---|---|
| `main_01_front.png` | straight FRONT (generate FIRST) |
| `main_00_three_quarter.png` | three-quarter from the creature's RIGHT front, slightly above |
| `main_02_profile.png` | pure LEFT profile: the snout points to IMAGE LEFT |
| `main_03_back.png` | BACK of the head from behind and above (crest spikes, back of the skull and horns) |

Generate `main_01_front.png` first; then the other three with your selected front as an extra input so all four are
the SAME head. At most ONE corrective regeneration per view; keep raw returns in `raw_main/`. Write
`generation_runs_main.json` (id, view, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs, size, alpha extrema) and `selected_views_review_main.png` (a contact sheet of the four selected views next to
the four grey views of input 1).

## Prompt content
TASK CONTEXT — GAME ASSET TEXTURING REFERENCE: faithful high-definition painted head of an EXISTING Might and Magic IX
monster, the Greater Demon, matching the given 3D head mesh view for view. Not a new design. Output ONE head only:
the head with its horns and crest spikes, the open jaw, and the top of the neck as far as input 1 shows it, centred
with the same framing as input 1, never cropped. Near-orthographic camera. Even soft neutral studio lighting, no
dramatic light, no rim light, no cast shadows (the image becomes a texture). Sharp fine detail.

Identity (from input 2): a reptilian dragon-demon head with a long snout, olive / khaki-green scaly hide with brown
mottling and darker scale edges; narrow glowing YELLOW eyes with dark slit pupils under heavy brow ridges; the jaw
wide OPEN, red-pink mouth interior, a long red tongue, rows of small sharp YELLOW-IVORY teeth and longer fangs; two
big curved horns sweeping out sideways from the sides of the skull, pale bone-olive with darker tips; a crest of long
pale spikes along the top of the head and back of the neck; dark silver-grey chitin plates where input 2 shows them at
the neck. Horns and spikes are pale ivory-olive bone, clearly a different material from the scaly hide.

Per-image checks (re-run before selecting): same head as `main_01_front.png`; silhouette, horn and spike positions
and the jaw opening match the same view of input 1; the requested view (profile snout to IMAGE LEFT); nothing cropped;
true transparent background; square.

## Do NOT
- change the head shape, the number or direction of horns and spikes, or close the mouth; add a body, arms, wings,
  armour, text, a floor, a background or a shadow; stylise as a cartoon; crop.
