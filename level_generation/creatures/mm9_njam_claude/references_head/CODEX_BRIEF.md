# Codex brief: head sculpt for MM9's Njam the Meddler (mm9_njam_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_njam_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a video-game man. Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right. Layout authority for the mass of the hair: a thick pageboy bob with a straight fringe across the forehead, hanging past the ears to the jaw line at the sides and to the nape at the back. Grey is background.
2. `references_head/in_body_head.png`: the high-definition body master's head: face identity.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of a man's head and neck, front three-quarter from the figure's RIGHT (he looks toward image right and toward the viewer), camera at eye level, near-orthographic, even soft light.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- A lean, ordinary MALE human head, about 35 years old, as in input 2: a long narrow face, high cheekbones, a long straight nose, deep clearly formed eye sockets with eyelids and open eyes, thin lips CLOSED with a clear parting line (a sly slight half-smile, no teeth), a complete narrow chin and a clean jaw line.
  Modelled ears are NOT needed: the hair covers them. No beard or stubble relief: smooth skin (stubble is painted later).
- HAIR as ONE solid smooth mass, like carved wood or a clay helmet: close on the crown so the skull shape reads, a straight blunt FRINGE across the forehead ending just above the eyebrows, then thick at the temples, over the ears and at the back, hanging straight to end in a clean rounded edge at jaw level at the sides and at the nape. It stands clear of the neck behind and at the sides by 2 cm, a closed rounded lower rim. NO separate locks, no thin strands, no gaps, only very shallow combed grooves. The hair does not cover the cheeks or eyes.
- NECK: a plain slim cylinder, cut flat below. No shoulders, no collar.
- No colour, no texture, no hat, no hood, no headband.
