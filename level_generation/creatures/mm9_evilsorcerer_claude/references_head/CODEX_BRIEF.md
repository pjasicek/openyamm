# Codex brief: head sculpt for the MM9 Evil Sorcerer (mm9_evilsorcerer_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_evilsorcerer_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a video-game man. Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right. Layout authority for the crown and the nape flap. Grey is background.
2. `references_hd/mm9_head_views_c.png`: the same head with another skin: an old man. The crown and flap again.
3. `references_head/in_body_head.png`: the high-definition body master's head: face identity and crown shape.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of a man's head and neck wearing a crown and a nape flap, front three-quarter from the figure's RIGHT (he looks toward image right and toward the viewer), camera at eye level, near-orthographic, even soft light. The complete crown top and the complete flap end stay in frame, with margin.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- A cruel, sharp-browed MALE human head, about 45 years old: strong straight nose, firm brow ridge, deep clearly formed eye sockets with eyelids and open eyes, firm closed lips with a clear parting line, a complete strong chin and jaw line, real ears fully modelled and visible below the crown, as input 3.
  No beard relief: clean shaven jaw, smooth skin (beard, moustache and sideburns are painted later). Short hair at the temples as smooth shallow relief only.
- CROWN: a stiff tall crown with a brow band round the head at the top of the forehead, a tall centre point over the forehead with a shallow oval boss, four shorter points round the head (two at the temples, two at the back), thick clean edges, open at the top with a dark recessed inner cap (a shallow bowl, not empty space). It sits on the head like a real rigid object, a deep clear step between crown and forehead.
- NAPE FLAP: from the crown's rim behind the temples, a stiff thick padded panel hangs behind the ears and the neck, ending in a straight blunt lower edge at the base of the neck, level with the top of the shoulders and NO lower, as input 1. It stands clear of the neck by 2 cm. Its front edges run behind the ears. The ears, cheeks and the front and sides of the neck stay clear.
- NECK: a plain cylinder, cut flat below at the collar. No shoulders, no collar, no chest.
- No colour, no texture, no beard, no long hair.
