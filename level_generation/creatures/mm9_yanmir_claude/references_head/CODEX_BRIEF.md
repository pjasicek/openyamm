# Codex brief: head sculpt for MM9 Yanmir (mm9_yanmir_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_yanmir_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a video-game frost giant king. Geometry only, so it is a sculpture with no colour.
His crown is built separately as its own part, so the sculpture has NO crown.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png`: renders of the ORIGINAL low-poly head, four views: front, three-quarter, figure's left, back. Layout authority for the
   masses: long straight hair hanging behind the ears to the shoulders and as a broad flat panel down the back to the nape; a long beard from the
   cheeks to the upper chest; the crown band sits round the head at the brow line. Grey is background.
2. `references_head/in_body_head.png`: the high-definition body master's head: face identity (ignore its crown).

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of a man's head and neck, front three-quarter from the figure's RIGHT (he looks toward image right
and toward the viewer), camera at eye level, near-orthographic, even soft light.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- A strong, noble MALE human head, about 50 years old: a heavy brow ridge, a straight broad nose, deep clearly formed eye sockets with eyelids and open
  eyes, high cheekbones, firm CLOSED lips with a clear parting line, the mouth corners slightly raised in a cold grim smile.
- BEARD: a long full beard and moustache as ONE solid smooth mass: it follows the cheeks and the jaw, and hangs from the chin down to about the top of
  the breastbone (about one head-height below the chin), narrowing to a blunt rounded point. Only shallow vertical grooves. The lips stay clearly
  modelled and free above it. The beard is thick (3-4 cm) but attached to the chin and the throat, with no gap behind it.
- EARS: two ordinary human ears, thick enough to sculpt (about 1 cm), showing in front of the hair at the sides, as input 1.
- HAIR as ONE solid smooth mass, like carved wood or a clay helmet: close and smooth on the crown so the skull's shape reads (a crown band will sit
  round it at the brow line), starting at a natural hairline on the forehead, then falling straight behind the ears and at the back of the head down
  to the nape and the top of the shoulders, ending in a clean rounded edge. It lies close to the back of the neck (1-2 cm off), a closed rounded lower
  rim. NO separate locks, no thin strands, no gaps, no braids, only very shallow combed grooves. The hair does not cover the cheeks, ears or eyes.
- NECK: a thick muscular plain cylinder, cut flat below at the collar. No shoulders, no collar, no fur.
- No colour, no texture, no crown, no headband, no spikes, no hat, no helmet, no teeth showing.
