# Codex brief: HD head turnarounds for the MM9 Banshee, two identities on ONE head shape (mm9_banshee_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_banshee_claude/references_head/`. Do not edit any other file, do not run builds, do not call Meshy.

Purpose: one 3D head mesh is modelled from `a/00_three_quarter.png`. Her tiers share that mesh and differ in paint, as MM9's skins share one low-poly head: from a woman's face to a skull with green eyes.
So every image of a and e must show the SAME head shape in the SAME position, size and angle: only the painted surface changes.

## Inputs (attached, in order; paths relative to `level_generation/creatures/mm9_banshee_claude/`)
1. `references_hd/mm9_views_head_A.png`: renders of the ORIGINAL MM9 model's head, the woman, the shape and the A identity authority. Views left to right: front three-quarter, front, profile facing image left, back, profile facing image right.
   Ignore the large hair spikes: they are a separate part. The black band under her upper teeth is her wide-open MOUTH, not a collar.
2. `references_hd/mm9_views_head_E.png`: same views, skin E, the green-eyed skull, the E identity.
3. `references_hd/mm9_skin_x4_E.png`: the original skin enlarged, top-left corner: the skull painting. Surface and colour only.
4. `references_hd/mm9_skin_x4_A.png`: same, the woman's face painting. Surface and colour only.
5. (run 2 and 3 only) the selected `references_head/a/00_three_quarter.png`, and in run 3 also `references_head/a/01_front.png`, `02_back.png`, `03_left.png`, `04_right.png`.

## Deliverables (1024x1024 SQUARE, true transparent background, unresized returns)
Folders `a/` (the woman, the shape authority), `e/` (the skull), each with:
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, faces image right and toward the viewer, camera at eye level (only a/ needs this one) |
| `01_front.png` | exact straight-on front |
| `02_back.png` | straight from behind |
| `03_left.png` | pure profile, faces IMAGE LEFT |
| `04_right.png` | pure profile, faces IMAGE RIGHT |

Run 1: `a/00_three_quarter.png` only, then stop. Run 2: `a/01`-`04` with the selected a/00 as an additional input, all the SAME head.
Run 3: `e/01`-`04`: each is an EDIT of the matching a/ image: same head outline, position, size and chin line, only the painted identity changes.
At most ONE targeted corrective regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason, superseded runs) and, after run 3, a
`selected_views_review.png` contact sheet (two rows a, e); raw returns under `raw/`.

## Prompt content (adapt per view)
Use case: identity-preserve. An isolated HD HEAD for the existing MM9 Banshee monster, a 3D modelling and texture reference, not a new design. ONE head with a short length of thin neck, nothing else: the neck ends in a clean flat
cut about one head-width below the jaw, with no shoulders, no collar, no cloth, no necklace. The head is held level, looking straight along its own axis. Centred, filling at most 62 % of the frame height, at least 12 % margin on
every side, near-orthographic camera, even soft neutral studio light, no cast shadows, no floor, no text. Opaque, solid: no transparency, no glow, no mist.

Shape (all identities, as input 1): a slim woman's head, narrow oval face, high cheekbones, straight nose, a real rounded chin on a long jaw. Her mouth is OPEN WIDE in a scream, the gap between the upper and the lower teeth about as tall as her nose is
long, lips drawn back, a dark round cavity behind, a full even row of upper teeth and a full even row of lower teeth, both clearly visible. The surface is smooth and organic with a rounded skull and rounded cheeks, NOT the flat polygon facets of input 1.
Hair: pulled tightly back from the forehead and temples into ONE smooth close-fitting cap lying on the skull, covering the top, the back and the sides down to the nape, no ears visible, long fine comb lines painted on it, no loose strands, no bun, no spikes, no locks standing free.

Identities (paint only, the shape never changes):
- a, the woman: pale warm skin, grey-blue eyes, thin brows, a slightly lined tired face of about forty, thin pale lips. Red-brown hair as input 1 and 4.
- e, the skull: a real SKULL painted on the same shape: ivory bone with brown shading and cracks, large round black eye sockets, each holding a glowing GREEN eye with a dark pupil as in input 3, a black nose cavity, long ivory teeth over the black mouth. Pale straw-blond hair with dark streaks as in input 3.

Per-image checks: one head; a short neck ending in a flat cut; same outline as the a/ image of that view; a real chin and jaw; mouth wide open with both tooth rows; correct side faces the correct image side; true transparent background; 1024x1024.

## Do NOT
add shoulders, a collar, a crown, horns, visible ears, loose hair or spikes, jewellery; change the head shape between a and e; close the mouth; crop.
