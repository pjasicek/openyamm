# Codex brief: HD modelling references for the Doom Bug (World of Xeen)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_swarm_claude/references_hd_bug/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Doom Bug** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites. Your job is a faithful
high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached in this order)

1. `native/sheet_doombug.png`: one ORIGINAL standing frame enlarged 4x with hard pixels (front three-quarter view). The
   grey background, the dark ground shadow and the green puddle under its jaws are NOT part of the creature.
2. (run 2 only) the selected `references_hd_bug/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd_bug/`, one creature each, the whole creature inside the frame with at least 60 px of margin on every
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
view. Records: `references_hd_bug/generation_runs.json` (id, view, prompt, input paths with sha256, output path, selected flag,
reason, superseded runs) and, in run 2, the contact sheet `references_hd_bug/selected_views_review.png`.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Doom Bug from the 1992 game Might
and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design. Use case: 3D
creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no dramatic lighting,
no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game materials, sharp fine
detail, a credible fully three-dimensional creature.

Identity (from the original frame): a giant CRICKET about 1.4 m long (body), crouched low. Glossy, metallic dark TEAL
blue-green chitin over the whole body with lighter teal highlights. HEAD: big, rounded, smooth teal head facing forward,
two large glossy PURPLE-violet compound eyes at the top sides, two very long, thin, curved BROWN antennae sweeping up and
back from between the eyes, brown mandibles and palps at the mouth. THORAX: a smooth saddle-shaped teal pronotum shield.
ABDOMEN: long, segmented teal abdomen with ribbed plates, resting low. LEGS: six legs in teal chitin: the front and
middle legs short and jointed, standing on the ground; the HIND legs huge cricket jumping legs with massive thighs folded
high above the body (knees higher than the back) and long thin shins reaching back to the ground. No wings visible
(folded flat on the back, teal).

Pose (identical in all five views): standing on level ground, crouched, all six feet on ONE level, legs separated from
each other by air gaps, the antennae up and back, mouth closed.

Do NOT: draw the green puddle or the ground shadow; add spread wings, a stinger or extra legs; change the colours; make
it cartoonish; crop the antennae or the legs; draw a floor, a background or text.

## Per-image checks

Whole cricket inside the frame with margins (antennae included); glossy teal chitin, purple eyes, brown antennae and
mandibles; six legs with the big folded hind jumping legs, all feet on one level; transparent background; landscape
1536x1024; 01-04 identical creature and pose; `03_left` head to image LEFT, `04_right` head to image RIGHT.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the first render) as the primary. In 01-04 keep exactly this creature: the same
proportions, colours, pose and number of legs (and wings). Side views: strict 90 degree profiles; front and back
straight on. Keep at least 60 px of margin and no faint alpha pixels at the canvas edges.
