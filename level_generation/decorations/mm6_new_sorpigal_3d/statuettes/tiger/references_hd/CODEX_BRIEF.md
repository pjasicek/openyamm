# Codex brief: HD reference views for the MM6 Tiger Statuette (ped02)

Scope: image generation only. Write ONLY into `level_generation/decorations/mm6_new_sorpigal_3d/statuettes/tiger/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool (prompt style and record format as in
`level_generation/creatures/mm6_wdm_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `level_generation/decorations/mm6_new_sorpigal_3d/statuettes/tiger/references_hd/native_statuette_x8.png` — the ORIGINAL native MM6 sprite's gold statuette, cropped and enlarged 8x with
   nearest neighbour. The design, pose, proportions and silhouette authority. Magenta is background; the grey strip
   at the bottom is the top of the pedestal it stands on, not part of the statuette.
2. `level_generation/decorations/mm6_new_sorpigal_3d/statuettes/tiger/references_hd/native_full_x3.png` — the whole native sprite (statuette on its marble pedestal), enlarged 3x, for context.
   The sprite shows the statuette from its LEFT side, head toward the left of the image.

## Deliverables (transparent background, LANDSCAPE 1536 x 1024, unresized returns)
- `00_three_quarter.png` — the statuette from its front-left three-quarter (camera turned 40 degrees from the
  sprite's side view toward the animal's face), slightly above (about 20 degrees), whole figure in frame (primary;
  generate first; this image alone is sent to a 3D generator)
- `01_left.png` — the exact left side profile as in the sprite, camera level with the body
- `02_front.png` — straight from the front (the face toward the camera), camera level with the body
Generate 01 and 02 with 00 as an additional input so all three show the SAME statuette and pose. Also write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and a
`selected_views_review.png` contact sheet. Regenerate a view if it fails the checks.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI quest item "Tiger Statuette", a small solid cast-gold animal figurine, from the supplied original
sprite, as a 3D modelling reference. Not a new design. ONE statuette, centred, generous margins, near-orthographic
camera, transparent background, NO base, NO plinth, NO pedestal, NO floor, NO shadow, no text: the feet (or talons,
tail tip) end on an invisible flat ground plane. Even soft neutral studio light (no dramatic light), so the form
reads clearly; polished, slightly worn yellow gold with crisp sculpted detail, as a museum bronze-casting.

Identity (from the native sprite): a lean big cat (tiger) standing on all four legs in a stalking stride, long low body, head forward and slightly raised, rounded ears, long thin tail curving down and back to touch the ground behind it; no stripes are sculpted (plain polished gold). Keep the sprite's proportions and pose exactly; sculpted, slightly
stylised forms like a cast figurine, not a photo of a real animal.

Do NOT: add a base, a pedestal, a stand, gems, armour, saddle, text, extra limbs or animals; do not change the pose;
do not colour it other than gold; do not crop it.

Checks per image: one statuette, pose and silhouette as the sprite, all legs / talons / tail present and separated
as drawn, transparent background, nothing cropped, same statuette in all three views.
