# Codex brief: head sculpt for the MM9 Giant (mm9_giant_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_giant_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a video-game barbarian giant. Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png`: renders of the ORIGINAL low-poly head, four views: front, three-quarter, figure's left, back. Layout authority for the
   mass of the hair: long loose hair parted at the centre, hanging past the ears to below the jaw at the sides and to the nape behind. Grey is background.
2. `references_hd/mm9_head_views_a.png`: the same head with another skin (red braided hair, headband): the hair mass again and the beard outline.
3. `references_head/in_body_head.png`: the high-definition body master's head: face identity.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of a man's head and neck, front three-quarter from the figure's RIGHT (he looks toward image right
and toward the viewer), camera at eye level, near-orthographic, even soft light.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- A rugged, broad MALE human head, about 40 years old, heavy and strong: a heavy brow ridge, a straight broad nose, deep clearly formed eye sockets with
  eyelids and open eyes, high cheekbones, firm CLOSED lips with a clear parting line, a broad complete jaw and chin.
- BEARD: a short full beard and moustache as ONE shallow smooth mass that follows the jaw and chin, only 1 cm proud of the skin, with a clear lower
  edge under the jaw; the lips stay clearly modelled and free. Only very shallow grooves.
- EARS: two ordinary human ears, thick enough to sculpt (about 1 cm), partly showing between the hair strands at the sides, as input 1.
- HAIR as ONE solid smooth mass, like carved wood or a clay helmet: parted at the centre, close on the crown so the skull shape reads, starting at a
  natural hairline on the forehead, then thick at the temples, behind the ears and at the back, hanging straight to end in a clean rounded edge just
  below jaw level at the sides and at the nape. It stands clear of the neck behind and at the sides by 2-3 cm, a closed rounded lower rim. NO separate
  locks, no thin strands, no gaps, no braids, only very shallow combed grooves. The hair does not cover the cheeks or eyes.
- NECK: a thick muscular plain cylinder, cut flat below at the collar. No shoulders, no collar, no fur.
- No colour, no texture, no headband, no earrings, no hat, no helmet, no teeth showing.
