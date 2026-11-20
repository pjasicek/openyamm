# Codex brief: head sculpt for the MM9 Monk (mm9_monk_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_monk_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a video-game man. Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png`: renders of the ORIGINAL low-poly head in its hood, five views: three-quarter, front, figure's left, back, figure's right. Proportion and facial layout authority. Grey is background. Ignore the hood.
2. `references_hd/mm9_head_views_b.png`: the same head with another skin.
3. `references_hd/mm9_head_views_c.png`: the same head with a third skin.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of a man's bare head and neck, front three-quarter from the figure's RIGHT (he looks toward image right and toward the viewer), camera at eye level, near-orthographic, even soft light. The complete head stays in frame, with margin.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- A stern, lean MALE human head, about 45 years old: long straight nose, firm brow ridge, deep clearly formed eye sockets with eyelids and open eyes, firm closed lips with a clear parting line, a complete strong chin and jaw line, hollow cheeks with clear cheekbones, real ears fully modelled, as inputs 1-3.
- HAIR: a smooth, close, low-relief skull cap of short hair, one solid mass with a clear low hairline across the forehead, no parting, no spikes, no individual strands, no ponytail.
- Clean-shaven in the sculpture: smooth skin on the jaw and chin (beards and goatees are painted later).
- NECK: a plain cylinder, cut flat below just above the collarbones. No shoulders, no collar, no chest.
- No hood, no colour, no texture, no beard, no long hair, no jewellery.
