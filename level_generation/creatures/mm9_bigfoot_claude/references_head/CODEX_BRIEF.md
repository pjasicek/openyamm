# Codex brief: head sculpt for the MM9 Bigfoot (mm9_bigfoot_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_bigfoot_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
The image is a modelling reference for a Meshy Smart Topology head model of a fantasy game monster. Geometry only, so it is a sculpture with no colour.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png`: renders of the ORIGINAL low-poly head, four views: front, three-quarter, side, back. Layout authority: crest, brow fringe, ears, jaw.
2. `references_head/in_body_head.png`: the high-definition body master's head: face identity. Follow its face closely.

## Deliverable (true transparent background, no floor, no shadow, no text, unresized return, 1024x1024)
`00_geometry.png`: one matt, plain light-grey clay sculpture of the ape-man's head and neck, front three-quarter from the figure's RIGHT (he looks toward image right and toward the viewer), camera at eye level, near-orthographic, even soft light.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason). At most one corrective regeneration.

## Content
- SKULL: a gorilla's head, tall and pointed: a high sagittal crest rising to a blunt peak over the crown, as input 1's side view. The whole upper head is one smooth solid mass.
- FRINGE: the hair of the crest ends in one heavy straight fringe across the forehead, overhanging the brow like the peak of a thick cap, about 2 cm proud of the face, with a soft rounded edge, as input 1. Only shallow combed grooves running up the crest. No separate locks, no thin strands, no gaps.
- FACE: a bare ape face, wide and flat. A heavy brow ridge under the fringe, small deep-set eyes with clear lids in deep sockets, eyes open, a calm heavy look. A flat broad ape nose with a short bridge and two big round deep nostrils, a long upper lip, a wide CLOSED mouth with two thick clearly formed lips and a clear line between them, corners slightly down. Heavy cheek pads with deep wrinkles from nose to mouth. A complete heavy chin.
- BEARD: one solid short smooth mass under the jaw and round the chin, a little thicker than the jaw, shallow grooves only.
- EARS: two small rounded human-like ears set far back on the sides of the head, thick enough to sculpt (about 1 cm), with a simple inner hollow, standing a little away from the head.
- NECK: a very thick plain cylinder under the jaw, as wide as the head, cut flat below. No shoulders.
- BACK: the back of the head is plain and rounded and flows straight into the neck, no mane, no hair mass.
- No teeth showing. No colour, no texture, no fur strands.
