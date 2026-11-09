# Codex brief: head sculpt for the MM9 Nosferatu (mm9_nosferatu_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_nosferatu_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a video-game creature. Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right. Layout authority for skull, ears and mouth. Grey is background. Ignore the collar and shoulders.
2. `references_hd/mm9_head_views_c.png`: the same head with another skin.
3. `references_hd/mm9_skin_x4_b.png`: the original skin enlarged; the face at top left is the sharpest evidence for wrinkles, brow, nose and teeth.
4. `references_head/in_body_head.png`: the high-definition body master's head: face identity.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of a creature's head and neck, front three-quarter from the figure's RIGHT (he looks toward image right and toward the viewer), camera at eye level, near-orthographic, even soft light. Both ear tips and the whole chin stay in frame, with margin.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- A gaunt, bald, goblin-faced undead head. A high, long, smooth domed cranium with no hair at all, about 1.3 times as tall as a human skull above the brow, narrowing to a strong narrow chin. A raised vertical vein ridge up the middle of the forehead.
- Heavy angry brow ridges that meet low over a flat wrinkled nose with wide nostrils, deep clearly formed eye sockets with eyelids and open narrow eyes, sunken cheeks with deep folds from the nose to the mouth corners.
- MOUTH: a fixed snarl, lips drawn back and slightly apart, about 1.5 cm open, showing two rows of small jagged sharp teeth with a dark recessed gap between them. The lips are thick real forms, the corners of the mouth pulled down and back. Upper and lower teeth clearly separate from the lips.
- EARS: two very large thin pointed ears, like long leaves, each as long as the head from chin to crown, attached at the sides of the skull at eye level, sweeping outward and upward at about 45 degrees to fine points, with a clear hollow on the front face. They are thin blades with a real rim, standing well clear of the skull.
- NECK: a thin plain cylinder, cut flat below. No shoulders, no collar, no chest.
- No colour, no texture, no hair, no eyebrows hair, no jewellery.
