# Codex brief: HD modelling references for the Stinger (World of Xeen, Insect Swarm)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_swarm_claude/references_hd/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Stinger (one insect of the Insect Swarm)** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites. Your job is a faithful
high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

The original sprite shows a SWARM: several identical flying insects. The 3D swarm will be made of copies of ONE insect,
so draw exactly ONE insect.

## Inputs (attached in this order)

1. `native/sheet_swarm.png`: two ORIGINAL frames enlarged 3x with hard pixels (left: the idle swarm; right: the attack,
   the yellow lines are a venom effect: do NOT draw them). The grey background is not part of the creature.
2. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature inside the frame with at least 60 px of margin on every
side, unresized returns, **1536x1024 LANDSCAPE**, true transparent background, no floor, no ground shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the head toward image RIGHT and turned about 35 degrees toward the camera (we see the face and the creature's LEFT side), camera a little above |
| `01_front.png` | straight front, symmetric |
| `02_back.png` | straight back |
| `03_left.png` | the creature's LEFT side: strict 90 degree profile, the head toward image LEFT |
| `04_right.png` | the creature's RIGHT side: strict 90 degree profile, the head toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as the last input. At most one corrective regeneration per
view. Records: `references_hd/generation_runs.json` (id, view, prompt, input paths with sha256, output path, selected flag,
reason, superseded runs) and, in run 2, the contact sheet `references_hd/selected_views_review.png`.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Stinger, one insect of the Insect Swarm from the 1992 game Might
and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design. Use case: 3D
creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no dramatic lighting,
no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game materials, sharp fine
detail, a credible fully three-dimensional creature.

Identity (from the original frames): a big stinging fly-wasp, about 25 cm long. HEAD: round, dark brown-black, with two
large glossy black-brown compound eyes and short black antennae; small dark mandibles. THORAX: rounded, rusty
orange-brown, finely hairy. ABDOMEN: tapered, orange-brown with darker brown bands, ending in a short black STINGER.
WINGS: one large pair (plus a smaller hind pair close behind it), translucent smoky grey with darker grey veins, spread
out flat to the sides in flight, clearly separated from the body. LEGS: six thin black jointed legs hanging down below
the body in flight. Colours: rusty orange-brown body, black legs and eyes, smoky grey wings.

Pose (identical in all five views): hovering in flight, body horizontal, wings spread flat and straight out to the
sides (seen from above they form a wide X), legs hanging down and slightly forward, all six legs separated.

Do NOT: draw more than one insect; draw venom, glow or motion blur; make it a cartoon bee with stripes of yellow and
black; add extra wings or legs; crop the wings; draw a floor, a shadow, a background or text.

## Per-image checks

One insect only, whole inside the frame with margins; six black legs; two pairs of translucent grey wings spread to the
sides; orange-brown hairy thorax, banded abdomen with a black stinger; dark compound eyes; transparent background (the
wings may be partly transparent); landscape 1536x1024; 01-04 identical creature and pose; `03_left` head to image LEFT,
`04_right` head to image RIGHT.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the first render) as the primary. In 01-04 keep exactly this creature: the same
proportions, colours, pose and number of legs (and wings). Side views: strict 90 degree profiles; front and back
straight on. Keep at least 60 px of margin and no faint alpha pixels at the canvas edges.
