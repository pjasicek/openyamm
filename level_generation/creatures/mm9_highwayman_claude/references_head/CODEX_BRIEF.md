# Codex brief: head sculpt for the MM9 Highwayman (mm9_highwayman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_highwayman_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a video-game man. Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png`: renders of the ORIGINAL low-poly head, five views: front, three-quarter, figure's left, back, figure's right. Layout authority for the mass of the hair: thick hair parted at the centre, hanging straight past the ears to the jaw line and at the back to the nape. Grey is background.
2. `references_hd/mm9_head_views_b.png`: the same head with another skin, a blond man, no headband: the hair mass again.
3. `references_head/in_body_head.png`: the high-definition body master's head: face identity.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of a man's head and neck, front three-quarter from the figure's RIGHT (he looks toward image right and toward the viewer), camera at eye level, near-orthographic, even soft light.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- A rugged, ordinary MALE human head, 35 years old: straight nose, firm brow, deep clearly formed eye sockets with eyelids and open eyes, firm closed lips with a clear parting line, a complete strong chin and jaw line.
  Modelled ears are NOT needed: the hair covers them. No beard relief: clean shaven jaw, smooth skin (the beard is painted later).
- HAIR as ONE solid smooth mass, like carved wood or a clay helmet: parted at the centre, thin and tight on the crown so the skull shape reads, starting at a natural hairline, then thick at the temples, behind the ears and at the back, hanging straight to end in a clean rounded edge at jaw level at the sides and at the nape. It stands clear of the neck behind and at the sides by 2-3 cm, a closed rounded lower rim. NO separate locks, no thin strands, no gaps, no braid, only very shallow combed grooves. The hair does not cover the cheeks or eyes.
- NECK: a plain cylinder, cut flat below at the collar. No shoulders, no collar.
- No colour, no texture, no headband, no hat, no hood.
