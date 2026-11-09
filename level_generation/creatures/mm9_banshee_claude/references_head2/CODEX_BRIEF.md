# Codex brief: HD head turnarounds for the MM9 Banshee, version 2 (mm9_banshee_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_banshee_claude/references_head2/`. Do not edit any other file, do not run builds, do not call Meshy.

Why version 2: a 3D head modelled from `references_head/a/00_three_quarter.png` came out wrong: a huge cranium under the hair cap, and a dislocated, stretched jaw from the very wide scream. The face itself (her identity, skin and eyes) is right.
Version 2 keeps that woman and fixes the proportions. A rig will open her jaw further in the animations, so the model only needs a moderately open mouth.

Her tiers share ONE head mesh and differ in paint, from a woman's face to a skull with green eyes: every image of a and e must show the SAME head shape in the SAME position, size and angle: only the painted surface changes.

## Inputs (attached, in order; paths relative to `level_generation/creatures/mm9_banshee_claude/`)
1. `references_head/a/00_three_quarter.png`: the selected face, skin and hair colour. Her IDENTITY authority. NOT the proportions: its cranium is too big and its jaw too long.
2. `references_hd/mm9_views_head_A.png`: renders of the ORIGINAL MM9 model's head (ignore the large hair spikes, they are a separate part; the black band is her open mouth). Views left to right: front three-quarter, front, profile facing image left, back, profile facing image right.
3. `references_hd/mm9_views_head_E.png`: same views, skin E, the green-eyed skull, the E identity.
4. `references_hd/mm9_skin_x4_E.png`: the original skin enlarged, top-left corner: the skull painting. Surface and colour only.
5. (runs 2 and 3) the selected `references_head2/a/00_three_quarter.png`, and in run 3 also `references_head2/a/01_front.png`, `02_back.png`, `03_left.png`, `04_right.png`.

## Deliverables (SQUARE, true transparent background, unresized returns)
Folders `a/` (the woman, the shape authority), `e/` (the skull), each with:
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, about 35 degrees, faces image right and toward the viewer, camera at eye level (only a/ needs this one) |
| `01_front.png` | exact straight-on front |
| `02_back.png` | straight from behind |
| `03_left.png` | pure profile, faces IMAGE LEFT |
| `04_right.png` | pure profile, faces IMAGE RIGHT |

Run 1: `a/00_three_quarter.png` only, then stop. Run 2: `a/01`-`04` with the selected a/00 as an additional input, all the SAME head.
Run 3: `e/01`-`04`: each is an EDIT of the matching a/ image: same head outline, position, size and chin line, only the painted identity changes.
At most ONE targeted corrective regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason, superseded runs) and, after run 3, a
`selected_views_review.png` contact sheet (two rows a, e); raw returns under `raw/`.

## Prompt content (adapt per view)
Use case: identity-preserve. An isolated HD HEAD for the existing MM9 Banshee monster, a 3D modelling and texture reference. ONE head with a length of slim neck, nothing else: the neck ends in a clean flat cut one head-width below the jaw, no shoulders, no collar, no cloth, no necklace.
The head is held level. Centred, the whole head filling at most 62 % of the frame height, at least 12 % margin on every side, near-orthographic camera, even soft neutral studio light, no cast shadows, no floor, no text. Opaque, solid: no transparency, no glow, no mist.

Shape (all identities): NORMAL HUMAN ANATOMY of a slim woman. A normal-sized skull: from the front, the width of the head at the temples is about the width of the face at the cheekbones, and the crown is only a finger above where a bald skull would be. Face height (hairline to chin) is about two thirds of the head height. Slim oval face, high cheekbones, straight nose, a firm jaw line running cleanly from below the ear to a rounded chin; the neck rises from under the jaw with no deep notch, no sagging cheek skin and no strap of skin from ear to chin.
Mouth: OPEN ABOUT TWO FINGER-WIDTHS, a shout rather than a dislocated scream: lips soft and natural around it, the chin directly below the mouth at a normal distance, a dark cavity behind, a neat even row of upper teeth and a neat even row of lower teeth both visible, the mouth about as wide as the space between her pupils.
Eyes: open, with real eyelids and clear sockets, brows drawn together in anger.
Hair: pulled tightly back from the forehead and temples, painted on the skull like a swimming cap of wet combed hair, no thicker than a finger, covering the top, back and sides down to the nape, ears hidden under it, long fine comb lines painted on it, no volume, no bun, no loose strands, no spikes.

Identities (paint only, the shape never changes):
- a, the woman: as input 1: pale warm skin, grey-blue eyes, thin brows, a slightly lined tired face of about forty, thin pale lips. Red-brown hair.
- e, the skull: a real SKULL painted on the same shape: ivory bone with brown shading and cracks, large round black eye sockets, each holding a glowing GREEN eye with a dark pupil as in input 4, a black nose cavity, long ivory teeth over the black mouth. Pale straw-blond hair with dark streaks as in input 4.

Per-image checks: one head; slim neck ending in a flat cut; normal skull size; a real chin and jaw; mouth moderately open with both tooth rows; correct side faces the correct image side; true transparent background; square.

## Do NOT
add shoulders, a collar, a crown, horns, visible ears, loose hair or spikes, jewellery; change the head shape between a and e; crop.
