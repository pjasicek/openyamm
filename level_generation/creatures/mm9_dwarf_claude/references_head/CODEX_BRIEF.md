# Codex brief: head sculpt for the MM9 Dwarf (mm9_dwarf_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dwarf_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a video-game dwarf warrior. Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right. Layout authority: helmet, horns, the beard's wedge. Grey is background.
2. `references_head/in_body_head.png`: the high-definition body master's head: face identity, helmet and horn shapes.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of a helmeted dwarf's head and neck, front three-quarter from the figure's RIGHT (he looks toward image right and toward the viewer), camera at eye level, near-orthographic, even soft light. One complete head from the horn tips to the neck, centred, with margin.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- A rugged old MALE dwarf's face, about 50 years old: broad nose, heavy brow, deep clearly formed eye sockets with eyelids and open eyes, cheekbones clearly formed. Mouth closed and hidden under the moustache.
- BEARD, part of the same sculpture: a full short beard and moustache as one solid carved mass with shallow combed grooves, from the cheeks round the jaw and ending in a blunt rounded point about 12 cm below the chin. No separate locks, no gaps, no braids. It stands clear of the neck, which is under it.
- HELMET, part of the same sculpture: a smooth rounded steel shell covering the crown, the temples, the ears and the whole back of the neck down to the collar, an opening for the face only, framed by a thick smooth raised band about 2 cm wide and 6 mm proud of the shell which runs across the forehead just above the eyebrows, down both sides of the face to the jaw, and round the shell's lower rim. No ornament on the band, no visor, no nasal bar, no cheek plates, no ears visible.
- HORNS, part of the same sculpture: three smooth tapering horns, each rising from a short thick wrapped collar on the shell: one short straight spike on the very top of the crown, and two long horns from the temples which curve outward and then upward, ending in sharp tips, as in input 1 and 2.
- NECK: a short plain cylinder under the beard, cut flat below. No shoulders, no collar, no mail.
- No colour, no texture, no extra straps.
