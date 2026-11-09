# Codex brief: HD master views of the standard Harrower warglaive (2026-10-24)

Scope: image generation only. Write ONLY into
`level_generation/creatures/hes_harrower_codex/warglaives/harrower/references_hd/`. Do not edit any other file, do not
run builds, do not call Meshy.

Use your built-in image generation. Attached inputs:
1. `design/kreegan_world/concepts/monsters/warglaive_harrower.png`: the APPROVED concept sheet, design authority. Use its
   flat views (the pair at the top left, the edge-on view, the grip study); the figure on the right only shows scale.
2. `design/kreegan_world/concepts/08_tech_gear_sheet.png`: material and painting reference only (bone, resin, glow).

Identity (from image 1, `warglaive_harrower.png`, candidate 1 "the bow", approved by the user): a twin-bladed
glaive about 1.1 m tip to tip. Centre grip: black resin wound with SIX ivory bone rings; at each end of the grip a
pair of curved ivory chitin crescent guards facing each other, forming an open ring around the fist, with a fine gold
band on each guard and a thin gold rod closing the ring's lower side. From each end of the grip a long blade: a
black-violet resin core (twisted, scaled texture) clad in ivory chitin-ceramic plates; the blade widens toward a
sweeping hooked ivory tip that curves up (the bow shape); along its outer curved edge a continuous ORANGE energy seam
from near the tip toward the grip; on each blade TWO short backswept ivory spurs on the edge side and ONE
short barbed ivory fin below near the tip (as image 1 shows). Fine gold edging only on the guards. The two blades
mirror each other across the grip.

## Deliverables (5 images, transparent background, 1024 x 1536 portrait, unresized returns)

| File | View | Use |
|---|---|---|
| `00_three_quarter.png` | the glaive's front face turned about 35 degrees to the viewer's right, camera slightly above (shows the blade thickness and the energy seam's channel) | Meshy Smart Topology image (primary; generate first) |
| `01_front.png` | front face, square on | texture paint reference |
| `02_back.png` | back face, square on (the glaive turned 180 degrees about its long axis' vertical: the reverse face) | texture paint reference |
| `03_left.png` | edge-on profile seen from the viewer's left (90 degrees from the front): a thin, nearly straight silhouette showing thickness, the resin core and the edge seam | profile reference |
| `04_right.png` | edge-on profile from the viewer's right | profile reference |

**Orientation, the same in all five:** the glaive stands UPRIGHT, its long axis vertical, centred, filling about 85 %
of the canvas height with margins; the centre grip at the canvas centre; one blade above the grip, one below. "Front
face" is the face the concept's flat pair view (top left of image 1) shows; in the upright front view the curved
blades bend toward the viewer's RIGHT at both ends (the concept's upward curve, turned a quarter turn clockwise), so
the glowing edges are on the RIGHT side of the blades. Keep that in 00 (turned from the front) and mirror it
correctly in 02.

Generate 01-04 with your selected 00 as an additional input, so all five are the SAME weapon, proportions and details.
Write `generation_runs.json` here (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and a `selected_views_review.png` contact sheet of the five. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT: a faithful high-definition rendering of an APPROVED original concept weapon (image 1) as a 3D modelling
reference. Not a new design: same silhouette, blade count, spur count and positions, guard, grip rings, materials and
colours as image 1's flat views. ONE weapon alone, no hand, no figure, near-orthographic camera, transparent
background, no floor, no shadow, no scenery, no text. Even soft neutral studio light that shows form (Meshy and the
paint bake take the albedo from it, so no dramatic light, no strong specular highlights). The energy edge is drawn as
a bright constrained seam in its resin channel, without glow spilling onto the background (a thin halo at most).
Credible solid 3D object with semi-realistic game materials and sharp fine detail.

Checks per image: the whole glaive, both tips, inside the frame; upright; the blade and spur counts of image 1; the
edge seam on the correct side; transparent background; 1024 x 1536; same proportions as 00.

Do NOT: add or remove blades, spurs, guards or rings; add gems, runes, glyphs, flames, smoke, green or blue light;
draw a hand or figure; crop a tip; change colours.
