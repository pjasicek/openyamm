# MM7 Dragon HD modelling masters

## Scope

Image generation only, with your built-in image generation tool. Write only into
`level_generation/creatures/mm7_m182_claude/references_hd/`. No builds, no scripts outside this folder, no Meshy.

## Context

A faithful high-definition reconstruction of the existing Might and Magic VII Dragon (green tier, palette 183) as a 3D
modelling reference for a game model. Not a new design: the low-resolution original sprites are the authority for
anatomy, proportions and colour. The grey background in the attached sheets is not part of the creature.

## Inputs (attached, in order)

1. `inputs/native_standing_views_183.png`: the original five views, left to right: front, front three-quarter
   (dragon faces image right), right-side profile (head to image right), rear three-quarter, back. Authority.
2. `inputs/native_flight_side_cycle_183.png`: the original flight cycle in profile (wing positions, legs, tail).
3. `inputs/native_flight_front_cycle_183.png`: the original flight cycle from the front (wing span, wing shape).
4. `inputs/native_tier_palettes.png`: the same frames in the three tier palettes (green, blue, red). Reference only:
   generate the GREEN tier; it shows which parts change colour (body, wings) and which stay (gold belly, ivory horns).

## Identity (from the native frames)

- Long, slender, lithe dragon: narrow chest, long S-curved neck, smallish head, very long thin tapering tail (about
  as long as head + neck + body together) ending in a fine point.
- Head: narrow lizard-like snout with a slightly open mouth showing small pale teeth; a crown of several short
  ivory-white horn spikes radiating backward and upward from the back of the skull (a spiky crest, not two long
  horns), with a yellow-green spiny frill behind the jaw.
- A row of short yellow-green dorsal spines from the back of the head along the neck, back and the whole tail.
- Gold/yellow ventral plates (segmented belly scutes) from the chin down the throat, chest and belly and along the
  underside of the tail.
- Body scales dark forest green with lighter green highlights.
- Four separate legs, each with clawed feet, small ivory claws (three to four toes). Forelegs held forward under the
  chest, hind legs bent, as in the native views.
- Two large bat-like wings: a long bony leading arm with an ivory thumb claw at the wrist, four to five long finger
  bones, membranes between them; membrane green with a lighter yellow-green mottled scale pattern, wing bones dark green.
- Matte reptile skin, no metal, no armour, no saddle.

## Pose and camera

- Neutral airborne rest pose, the same in all five images: torso moderately inclined, head raised on the S-curved neck,
  both wings raised and spread out to the sides (as the native front flight frame), membranes not overlapping the body,
  wing roots clearly visible, all four legs separated and visible, tail extended straight back with a slight downward
  curve, nothing overlapping.
- Near-orthographic camera, soft even studio light, no dramatic shading.
- Transparent background, no floor, no shadow, no text, no frame, no other objects.

## Deliverables

Each 1536×1024 landscape, unresized return, true alpha, generous margins: never crop a wingtip, claw or tail tip.

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, camera at chest height slightly above (shows depth); the primary |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | the dragon's LEFT side: head points to image LEFT |
| `04_right.png` | the dragon's RIGHT side: head points to image RIGHT (like the third, profile view of input 1) |

## Procedure

1. Generate `00_three_quarter.png` first from inputs 1–4. Check it (below); at most one corrective regeneration.
2. Then generate `01`–`04` with the selected `00_three_quarter.png` as the first input plus inputs 1–3, so all five
   show the same creature, pose and proportions. At most one corrective regeneration per view.

## Do NOT

- Do not add long backward horns, a horn crown like a different dragon, armour, rider, saddle, chains, fire,
  smoke, scenery, or extra limbs (exactly four legs and two wings).
- Do not change colours (green body and wings, gold belly, ivory horns and claws, yellow-green spines).
- Do not crop, do not add a ground plane or cast shadow.

## Per-image checks

- one dragon, four legs, two wings, one tail, one head; crest of short ivory spikes; gold ventral plates;
- wings spread with membranes clear of the body; whole creature inside the canvas with margins;
- transparent background (true alpha), 1536×1024;
- side views: correct facing (03 head to image left, 04 head to image right); same pose as 00.

## Records

Write `generation_runs.json` (one entry per generation: id, prompt, input file sha256 list, output path, selected
flag, reason, superseded runs) and `selected_views_review.png`, a contact sheet of the five selected views.
