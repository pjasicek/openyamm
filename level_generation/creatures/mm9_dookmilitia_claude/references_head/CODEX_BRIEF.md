# Codex brief: head sculpt for the MM9 Half Orc (mm9_dookmilitia_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dookmilitia_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a video-game half-orc soldier in a leather helmet. Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right. Layout authority for the helmet: skull cap with a thick rim, a coif that hangs to the shoulders at the sides and back, flat cheek straps, ears, spikes. Grey is background.
2. `references_hd/mm9_head_views_c.png`: the same helmet with another skin, the captain.
3. `references_head/in_body_head.png`: the high-definition body master's head: face identity.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of the head, helmet and neck, front three-quarter (he looks toward image right and toward the viewer), camera at eye level, near-orthographic, even soft light.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- FACE fully visible, a coarse half-orc: heavy brow ridge, deep clearly formed eye sockets with eyelids and open eyes, broad flat nose with wide nostrils, firm closed lips with a clear parting line, a complete strong chin and heavy jaw. Clean shaven, smooth skin. No tusks, no teeth showing: the mouth is closed.
- SKULL CAP: a smooth rounded leather cap covering the crown and forehead down to just above the eyebrows, with a thick rolled rim all round.
- COIF: a smooth thick solid leather hood mass hanging from the cap, covering the back of the head, the sides behind the jaw, and the nape, falling straight down to a clean rounded lower edge at the base of the neck, about 16 cm below the chin line at the back and sides, standing a little clear of the neck. It is ONE solid mass, like carved wood: no hair, no folds, no strands. At the front it opens with a straight vertical edge on each side just behind the cheeks, so the whole face is free.
- CHEEK STRAPS: on each side, in front of the ear, one flat vertical strap about 3 cm wide and 1 cm thick from the cap's rim down to the jaw line, lying on the coif's front edge.
- EARS: a large POINTED ear on each side comes out through the coif at ear height, standing out sideways and slightly back, about 8 cm long, tip pointing up and outward, a thick simple shape.
- SPIKES: two short conical horn spikes, about 3 cm long, on the sides of the cap above the ears, pointing out sideways and up.
- NECK: a plain thick cylinder inside the coif, cut flat below. No shoulders, no collar.
- No colour, no texture, no chain, no rivets, no hair.
