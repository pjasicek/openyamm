# Codex brief: HD HEAD turnaround, ARM-END SNAKE HEAD of the MM9 Greater Demon (mm9_greaterdemon_claude, 2026-10-30)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_greaterdemon_claude/references_head/`
(files prefixed `arm_`, raw returns in `references_head/raw_arm/`). Do not edit any other file, do not run builds,
do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9.

The Greater Demon's two arms end not in hands but in smaller snake / dragon heads. These four images will be projected
by an AI texturing tool onto OUR 3D mesh of the creature's LEFT arm head (input 1), so the head in every image must
have the SAME SHAPE, POSE, CAMERA and FRAMING as the matching grey view in input 1.

## Inputs (attached, in order)
1. `references_head/shape_arm_views.png` — grey renders of OUR arm-head mesh (cut at the wrist), four views left to
   right: FRONT (looking into the open mouth), THREE-QUARTER (from the outer front, slightly above), OUTER PROFILE (the
   snout points to IMAGE LEFT), BACK (from behind the wrist and above). SHAPE, POSE, SILHOUETTE AND FRAMING
   AUTHORITY: the wrist ring of spikes, the open jaws, teeth and tongue exactly as here. Grey is only the untextured
   mesh; transparent pixels are background. The flat cut at the wrist joins the arm; paint it as the dark armoured
   wrist band.
2. `references_head/hd_master_arm_head_crops.png` — crops of the APPROVED HD body masters showing the arm heads:
   COLOUR, MATERIAL AND DETAIL AUTHORITY. The head you paint must be THIS head.
3. `references_head/mm9_head_views.png` — the ORIGINAL Might and Magic IX low-poly model (bottom row: the arm head):
   design authority only; its blur and faceting are NOT the design.
4. `references_hd/mm9_skin_tier1_x4.png` — the original skin texture x4, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized)
| File | View (match the same view of input 1) |
|---|---|
| `arm_01_front.png` | straight FRONT into the open mouth (generate FIRST) |
| `arm_00_three_quarter.png` | three-quarter from the outer front, slightly above |
| `arm_02_profile.png` | pure outer profile: the snout points to IMAGE LEFT |
| `arm_03_back.png` | from behind the wrist and above: the top of the skull and the spike ring |

Generate `arm_01_front.png` first; then the other three with your selected front as an extra input so all four are
the SAME head. At most ONE corrective regeneration per view; keep raw returns in `raw_arm/`. Write
`generation_runs_arm.json` (id, view, prompt, inputs with sha256, output path, selected flag, reason, superseded runs,
size, alpha extrema) and `selected_views_review_arm.png` (a contact sheet of the four selected views next to the four
grey views of input 1).

## Prompt content
TASK CONTEXT — GAME ASSET TEXTURING REFERENCE: faithful high-definition painted arm-end snake head of an EXISTING
Might and Magic IX monster, the Greater Demon, matching the given 3D mesh view for view. Not a new design. Output ONE
head only, from the wrist forward, centred with the same framing as input 1, never cropped. Near-orthographic camera.
Even soft neutral studio lighting, no dramatic light, no rim light, no cast shadows (the image becomes a texture).
Sharp fine detail.

Identity (from input 2): a reptilian snake / dragon head: olive / khaki-green scaly hide with brown mottling and darker
scale edges; narrow glowing YELLOW eyes; the jaws wide OPEN, dark-red mouth interior, a red tongue, rows of small
sharp YELLOW-IVORY teeth; a ring of long pale ivory-olive spikes around the wrist and the back of the head, set in a
dark silver-grey chitin wrist band. Spikes are pale bone, clearly a different material from the scaly hide.

Per-image checks (re-run before selecting): same head as `arm_01_front.png`; silhouette, spike positions and the jaw
opening match the same view of input 1; the requested view (profile snout to IMAGE LEFT); nothing cropped; true
transparent background; square.

## Do NOT
- change the head shape, the number or direction of the spikes, or close the mouth; add an arm, a hand, a body, text,
  a floor, a background or a shadow; stylise as a cartoon; crop.
