# Codex brief: HD head turnarounds for the MM9 Ghost, three identities on ONE head shape (mm9_ghost_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ghost_claude/references_head/`. Do not edit
any other file, do not run builds, do not call Meshy.

Purpose: the MM9 Ghost's head is a separate floating rigid piece: no neck, no body. One 3D head mesh is modelled from `b/00_three_quarter.png`.
All three tiers share that mesh and differ in paint, as MM9's three skins share one low-poly head. So every image of a, b and c must show the SAME head
shape in the SAME position, size and angle: only the painted surface changes.

## Inputs (attached, in order; paths relative to `level_generation/creatures/mm9_ghost_claude/`)
1. `references_hd/mm9_head_views_t2.png`: renders of the ORIGINAL MM9 model's head, Apparition, the head shape and the B identity authority.
   Row order of views: front three-quarter, front, profile facing image left, back, profile facing image right.
2. `references_hd/mm9_head_views_t1.png`: same views, Shadow, the A identity.
3. `references_hd/mm9_head_views_t3.png`: same views, Specter, the C identity.
4. `references_hd/00_three_quarter.png`: the selected HD body master.
5. `references_hd/mm9_skin_x4_t2.png`: the original skin enlarged, top-left corner: the face and hair painting. Surface and colour only.
6. (run 2 and 3 only) the selected `references_head/b/00_three_quarter.png`, and in run 3 also `references_head/b/01_front.png`, `02_back.png`, `03_left.png`, `04_right.png`.

## Deliverables (1024x1024 SQUARE, true transparent background, unresized returns)
Folders `b/` (Apparition, the shape authority), `a/` (Shadow), `c/` (Specter), each with:
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, faces image right and toward the viewer, camera slightly above eye level (only b/ needs this one) |
| `01_front.png` | exact straight-on front |
| `02_back.png` | straight from behind |
| `03_left.png` | pure profile, faces IMAGE LEFT |
| `04_right.png` | pure profile, faces IMAGE RIGHT |

Run 1: `b/00_three_quarter.png` only, then stop. Run 2: `b/01`-`04` with the selected b/00 as an additional input, all the SAME head.
Run 3: `a/01`-`04` and `c/01`-`04`: each is an EDIT of the matching b/ image: same head outline, position, size, ear and chin line, only the painted identity changes.
At most ONE targeted corrective regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason, superseded runs) and, after run 3, a
`selected_views_review.png` contact sheet (three rows a, b, c); raw returns under `raw/`.

## Prompt content (adapt per view)
Use case: identity-preserve. An isolated HD disembodied HEAD for the existing MM9 Ghost monster, a 3D modelling and texture reference, not a new
design. ONE head, nothing else: it ends just below the chin and jaw in a smooth rounded base, with NO neck, no shoulders, no collar, no cloth. Centred, level, filling about 75 % of the frame height,
generous transparent margins, near-orthographic camera, even soft neutral studio light, no cast shadows, no floor, no text. Opaque, solid: no transparency, no glow, no mist.

Shape (all tiers, as input 1): a tall, narrow, egg-shaped head, higher and longer than a living head; a long gaunt face, deep eye sockets, hollow cheeks, a thin nose, a long jaw with a real
chin, mouth open about two finger-widths in a dark grin. White hair brushed straight back from the temples, lying close to the skull as ONE smooth solid mass that covers the back and sides and tapers
to a rounded point at the nape: long fine comb lines painted on it, no loose strands, no locks standing free. No ears visible, no beard, no eyebrow tufts standing free.

Identities (paint only, the shape never changes):
- b, Apparition: an old man's face, pale grey-green skin, heavy wrinkles, angry brows, sunken eyes with small bright GREEN irises, worn teeth in a dark mouth. Silver-white hair.
- a, Shadow: a pale, featureless, blue-white face like a mask of wet plaster: no wrinkles, two round pure-black hollow eye sockets, a wide black gaping mouth with no teeth showing. White hair fading to the same blue-white.
- c, Specter: a real SKULL painted on the same shape: blue-grey bone, black eye sockets with small glowing BLUE irises, a black nose cavity, a full row of long narrow teeth over the black mouth. Grey-white hair.

Per-image checks: one head; no neck; same outline as the b/ image of that view; a real chin and jaw; correct side faces the correct image side; true transparent background; 1024x1024.

## Do NOT
add a neck, shoulders, a hood, a crown, horns, ears, loose hair, a beard; change the head shape between a, b and c; crop.

## Correction after run 1 (Claude, applies to every image)
The first b/00 was cropped at the chin and copied the original's flat facets. The WHOLE head must be inside the frame with at least 10 % margin on every side: the head fills at most 65 % of
the frame height, chin to crown. The surface is smooth and organic: a rounded skull and rounded cheeks, NOT the flat polygon facets of input 1. Keep that face, its teeth and its eyes, and show a complete chin and jaw.
