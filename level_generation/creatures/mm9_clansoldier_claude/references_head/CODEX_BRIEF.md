# Codex brief: head sculpt for the MM9 Horde Soldier (mm9_clansoldier_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_clansoldier_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a video-game soldier. Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right. Layout authority: dome helmet, nasal bar, ears, the mass behind the neck. Grey is background.
2. `references_hd/mm9_head_views_b.png`: the same head with another skin: here the mass behind the neck is a laminated neck guard. Same geometry.
3. `references_head/in_body_head.png`: the high-definition body master's head: face identity.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of a helmeted man's head and neck, front three-quarter from the figure's RIGHT (he looks toward image right and toward the viewer), camera at eye level, near-orthographic, even soft light.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- A rugged, ordinary MALE human face, about 35 years old: straight nose, firm brow, deep clearly formed eye sockets with eyelids and open eyes, firm closed lips with a clear parting line, a complete strong chin and jaw line, ordinary human ears clear of the head. No beard relief: clean shaven jaw, smooth skin (beard and moustache are painted later).
- HELMET, part of the same sculpture, sitting low on the brow just above the eyebrows: a simple conical dome with a slightly pointed top and a low raised ridge from the front to the top, a thick smooth brim band round its lower third that stands about 1 cm proud of the dome all round, level round the head, and from the middle of the brim a narrow straight flat NASAL bar down the front of the nose to the nose tip, standing about 5 mm clear of the nose. No visor, no cheek guards, no ornament, no horns, no rivets, no fur relief.
- NAPE: from under the helmet brim behind the ears a solid smooth curtain like a thick leather hood back, as wide as the head from ear to ear, hanging straight down behind the neck to the base of the neck and standing clear of the neck behind by 2 cm, its front edges just behind the ears, its lower edge a clean rounded rim. It reads as one solid mass, like carved wood. NO separate locks or strands, no gaps, no plates.
- NECK: a plain cylinder in front of the curtain, cut flat below at the collar. No shoulders, no collar, no mail.
- No colour, no texture, no extra straps.
