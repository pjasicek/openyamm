# Codex brief: head sculpt for the MM9 Colloidal Warrior (mm9_colloidalwarrior_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_colloidalwarrior_claude/references_head/`. No builds, no Meshy.
Use your built-in image generation tool. The image is a modelling reference for a Meshy Smart Topology head model of a fantasy game monster
(a humanoid made of living slime). Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png`: renders of the ORIGINAL low-poly head, four views: front, three-quarter, side, back. Layout authority:
   the dome, the brow nubs, the slit eyes, the beak nose, the wide grin, the throat folds.
2. `references_head/in_body_head.png`: the high-definition body master's head: face identity. Follow its face closely.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of the creature's head and throat, front three-quarter from the figure's RIGHT
(it looks toward image right and toward the viewer), camera at eye level, near-orthographic, even soft light.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- DOME: a smooth rounded dome of thick slime, wider than tall, slightly pointed on top, as input 1. No skull shape, no ears, no hair.
- BROW: a heavy overhanging brow ridge across the whole face, and above it on the top of the dome a short row of four or five small blunt
  rounded nubs (like knuckles) running front to back along the middle, as input 2. No horns, no spikes.
- EYES: two narrow slanted almond SLITS under the brow, angled down toward the nose, about 7 cm long and 1.5 cm high, set in deep dark sockets
  with a thick lower lid. The eye surface inside each slit is smooth and flush with the lids: NO round eyeballs bulging out.
- NOSE: a short hooked beak-like nose pointing down between the eyes, with two small nostrils underneath.
- MOUTH: a very wide evil GRIN reaching almost from cheek to cheek, corners turned up, lips pulled back and slightly apart, showing ONE row of
  small even pointed teeth in the upper jaw and one in the lower, sculpted shallow (the teeth sit just behind the lips, no deep mouth hole).
- CHEEKS: thick puffy cheek folds round the grin.
- THROAT: under the chin, three or four thick horizontal rolls of slime stacked one under the other like a toad's throat, each wrapping round
  the front and sides of the throat, as inputs 1 and 2.
- NECK BASE: below the rolls the sculpture continues as a very thick plain cylinder as wide as the dome, cut flat below. No shoulders.
- BACK: the back of the dome is plain and rounded with two or three soft horizontal folds, flowing straight into the cylinder.
- No colour, no texture.
