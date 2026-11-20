# Codex brief: HD reference views for the MM9 Troglodyte (mm9_troglodyte_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_troglodyte_claude/references_hd/` (run 3: `references_hd/tierC/`, run 4:
`references_head/`). Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a non-human fantasy cave monster from a 2002 video game, restored for a game mod.

## Inputs (attached, in order)
1. `mm9_views_b.png`: renders of the ORIGINAL low-poly model with its green skin, five views left to right: front three-quarter from the figure's RIGHT,
   front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE, proportions and
   colour authority. Faceting, blur, the shiny white streaks and low resolution are NOT the design (those streaks are render artefacts).
2. `mm9_head_views_b.png`: close renders of the head and shoulders, same five views. Eye, mouth and teeth authority.
3. `mm9_skin_x4_b.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
4. (run 2, 3, 4) the selected `references_hd/00_three_quarter.png`.
Run 3 and 4 also get: `mm9_views_c.png`, `mm9_head_views_c.png`, `mm9_skin_x4_c.png` (the leather-wearing skin) and the selected 01-04.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 portrait; the figure is wide: fill the width)
| Run | File | View |
|---|---|---|
| 1 | `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| 2 | `01_front.png` | straight front |
| 2 | `02_back.png` | straight back |
| 2 | `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| 2 | `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |
| 3 | `tierC/01_front.png`, `02_back.png`, `03_left.png`, `04_right.png` | same four views of the leather-wearing figure |
| 4 | `../references_head/00_q34.png`, `01_front.png`, `02_left.png`, `03_back.png`, `04_right.png`: 1254x1254, head only, MOUTH WIDE OPEN, see run 4 below |

Run 1: generate `00_three_quarter.png` only, then stop. Later runs (separate runs): use the selected 00 as an additional input so all views are the SAME figure, SAME pose,
SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Troglodyte" from the supplied renders of its original 3D model, as a 3D modelling and
texturing reference. Not a new design. A credible, fully three-dimensional creature with semi-realistic game materials and sharp fine detail (wet amphibian skin, pores, fine scales,
raised veins). ONE complete figure from the crown to the toes and the tail tip, centred, generous margins, never cropped.

Identity (exactly the layout of inputs 1-3):
- A hunched, frog-like cave predator about 1.3 m tall as it stands. NOT a human, NOT a lizard man, no hair, no ears, no horns.
- HEAD: a huge smooth blunt egg-shaped dome that carries straight on from the hump of the back, with no neck at all; it juts FORWARD horizontally and is as wide as the chest. Blunt
  rounded snout, wide as the head. Seen from the side the top line runs from the hump over the skull almost level, then rounds down to the snout.
- EYES: small, set wide apart low on the sides of the dome, narrow slanted reptile eyes with a slit pupil and a heavy lid, a dark socket around them.
- MOUTH: a wide lipless slit right across the underside of the snout, from side to side, slightly open as in input 1. Below it a flat shelf of lower jaw sticks forward past the
  snout, with one row of big separate yellow-ivory teeth standing along its front edge. Blood-red gums and an orange-red mouth lining visible inside. No fangs from the upper jaw.
- BODY: a short curved barrel torso bent forward, pale olive belly and chest, a hump at the shoulders.
- ARMS: very long and thin with stringy muscle, hanging down and out from the shoulders to below the knees, slight elbow bend. A thin dark band round the wrist.
- HANDS: CORRECTION after checking the original mesh: exactly THREE long skeletal fingers on each hand and NO thumb, as in the selected 00_three_quarter.png. Each is long, thin, knuckled, and tapers into a long sharp
  claw continuous with the finger. Spread wide with clear air between them.
- LEGS: bowed, wide apart, bent at the knee in a crouch, strong thighs, thin shins.
- FEET: long flat frog feet, three long toes in front with a small pointed claw each, flat on the ground, turned outward.
- TAIL: one long thick tail growing from the base of the spine, hanging straight DOWN behind and between the legs to the floor, tapering into a sharp point. Same skin as the back.
- A few short thin spines stick out backward from each thigh and calf, as in the side views of input 1, if you can see them.
- SKIN: wet olive green and moss green; dark, almost black round blotches on the back, thighs and shoulders with tiny pale speckles around them; fine dark-green scale
  ridges on the top of the head; a pale tan-olive belly and inner arms. On the back of the arms, the shins and the digits, a pattern of raised pink-orange vein ribs like a rib cage
  over dark green, as in input 3. Claws dark brown at the tip, tan at the root.
- No clothes, no armour, no belt, no weapons in runs 1, 2 and 4.

Run 3 only, the "Gnoll" variant: the SAME figure, same pose, skin grey-brown instead of green (input mm9_skin_x4_c), and it WEARS thin dark-brown stitched LEATHER tightly fitted to the body,
as in `mm9_views_c.png`: a leather cap over the top and back of the dome, a jerkin over the whole back and hump, leather shoulder caps, a wide leather bib on the chest under the jaw
and over the lower belly with a stitched border, a leather band at each wrist, a leather greave wrapped round each shin. Elbows, forearms, hands, thighs and the face stay bare hide.
The mouth lining is bright green-yellow here. The leather is smooth, worn, stitched; not metal.

Run 4 only, the open-mouth head study. Extra input `mm9_mouth_views_b.png`: the ORIGINAL model with its mouth fully open, five views (front 3/4, front, its left side, back, front from below). Generate the HEAD ONLY, severed cleanly
at the base of the skull (a simple flat cut with hide colour, no neck, no shoulders, no arms), floating on transparency. Pose: the dome tipped back about 35 degrees, as in that input, jaw dropped: the mouth gapes about 60 degrees, hinged at the mouth corners far back on
each side of the head, so that the whole inside is visible from the front:
- PALATE: the whole underside of the dome is one big concave blood-red fleshy dish, as wide as the head, with ridged wet muscle rings around a round dark THROAT HOLE in its middle (input: the red disc with the dark hole).
- UPPER TEETH: a row of about 20 separate pointed ivory teeth along the front and side rim of the dish, standing on red gums.
- LOWER JAW: a shallow wide spoon of the same width as the mouth, its outside the same pale-olive hide, its inside red-orange, thin at the front; one row of big separate blunt yellow-ivory teeth along its front edge; a short flat orange-red T-shaped TONGUE lying on it.
- Thick rubbery red lips at the mouth corners join the dish and the spoon: a real closed hinge, no long membrane.
- Eyes: as in 00, on the sides of the dome, not on the palate. Same skin as 00: the scale ridges on top, dark blotches.
Views: `00_q34` from the front 3/4 on the head's right, `01_front` straight at the gape, `02_left` pure profile facing IMAGE LEFT, `03_back` from behind, `04_right` pure profile facing IMAGE RIGHT. All five the same head, same gape. Mouth-lining colours from input 3 (the red disk and the orange T).

Pose (identical in all views, the model's bind pose as in input 1): standing in the crouch shown, weight on both feet, feet about 90 cm apart, toes turned outward; back curved, head
thrust forward level; arms held away from the body and down at about 35 degrees from vertical, digits spread, clear air between arms and legs; the tail hanging straight down.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT (runs 1-3): add clothes (except run 3), weapons, a neck, ears, hair; change colours; crop any part; copy the shiny white streaks; add a thumb or extra digits; give it a humanlike face.

Per-image checks (redo at most once): crown to toes and tail tip in frame; true alpha; three fingers, no thumb, on each visible hand with air between them; tail present; wide mouth with one row of
lower teeth; two small side eyes.


## Run 5: the purple "Troglodyte" variant (tier A), `references_hd/tierA/01_front.png`, `02_back.png`, `03_left.png`, `04_right.png`
Inputs: `mm9_views_a.png`, `mm9_head_views_a.png`, `mm9_skin_x4_a.png`, the selected 01_front and 03_left (green figure: SAME figure, pose, silhouette; repaint only). Same rules as run 3 (no leather).
Skin: dusky blue-violet, darker than the green one, wet. The pattern is the identity of this variant: PALE LILAC-WHITE RAISED RIBS AND VEINS over dark violet, like a rib cage drawn on the skin: rows of curved ribs on the flanks, the back, the sides of the head, the thighs and the arms, as in inputs 1 and 3;
speckled pale grey patches between them; dark blotches stay but fade into the violet. Pale lilac inner arms and belly with faint ribs. The mouth lining is teal-blue instead of red, the teeth pale blue-white.
NO EYES: this variant is blind: smooth skin where the green figure has eyes (a faint closed dimple at most). Claws dark teal at the root, pale at the tip. Do not change any outline.
