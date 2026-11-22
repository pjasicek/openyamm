# Codex brief: HD modelling references for the Giant Scorpion (World of Xeen)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_scorpion_claude/references_hd/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Giant Scorpion** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an
MM6-8-style first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites. Your job
is a faithful high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached)

1. `native/sheet_codex.png`: two ORIGINAL frames, enlarged 4x with hard pixels, on flat grey (the grey is NOT part
   of the creature, and the black blobs under it are its painted ground shadow, also NOT part of it): standing (left)
   and attacking with its right pincer thrust toward the viewer (right). Identity, proportion and colour authority.
2. (views 01-04 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature (tail and stinger included) inside the frame
with at least 60 px of margin on every side, unresized returns, **1536x1024 LANDSCAPE**, true transparent background,
no floor, no ground shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the head toward image RIGHT and turned about 35 degrees toward the camera (we see the face, both pincers and the creature's RIGHT flank), camera a little above the back so the curled tail and the leg layout read |
| `01_front.png` | straight front: the face toward the camera, symmetric (the view of the original sprite) |
| `02_back.png` | straight back: the tail base and the rear of the body toward the camera, the tail rising toward the camera's top |
| `03_left.png` | the creature's LEFT side: strict 90 degree profile, the head toward image LEFT |
| `04_right.png` | the creature's RIGHT side: strict 90 degree profile, the head toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Later runs: one view each (01, 02, 03 or 04, as the run's instruction names it), with the selected `00` as input 2.
At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Giant Scorpion from the 1992 game
Might and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail, a credible fully three-dimensional giant scorpion.

Identity (from the original frames): a GIANT scorpion, about 2 m long and 1 m tall to the top of its raised tail,
low and wide.
- CHITIN: GLOSSY DARK-BROWN exoskeleton everywhere (warm chestnut brown, with orange-tan glossy highlights along the
  plate ridges and darker brown in the creases), smooth hard shell, no hair, no spikes.
- BODY: a broad flat segmented body: the front shield (carapace) over the head, then about seven overlapping
  horizontal back plates, each with a darker seam.
- HEAD: at the front of the carapace, two round dark EYES with a thin pale ring, set wide on the front edge, and below
  them small dark mouthparts (two short stubby chelicerae). No teeth, no open jaw.
- PINCERS: TWO big pedipalp arms reaching forward from the sides of the head, each ending in a large BULBOUS CLAW
  (a swollen round palm with two curved fingers, a fixed finger and a movable finger, their tips curving toward each
  other). The claws are big: each palm about as wide as the head.
- LEGS: EIGHT thin jointed walking legs, FOUR per side, splayed wide like a spider's, each with a high knee and a thin
  pointed foot.
- TAIL: a long segmented TAIL (FIVE rounded tail segments, each a little longer than the last) rising from the back
  end of the body, curving UP and FORWARD in a high arc over the back, ending in a BULBOUS STINGER: a swollen glossy
  bulb, lighter tan-orange than the body, with a dark curved sharp sting point at its tip aiming forward.

Pose (identical in all five views): standing on its eight legs on level ground in a neutral star pose: the body level
and low (belly a little above the ground), all eight foot tips on ONE flat plane with clear air gaps between every leg
and between the legs and the pincer arms; the two pincer arms reach forward and a little outward, the claws resting
low just above the ground in front of the head, with a clear air gap between each claw and the head and between the
claws; each claw slightly OPEN (a clear gap between the fixed and the movable finger); the tail raised high in its arc
over the back with a clear air gap between the tail and the back plates, the stinger bulb above the middle of the body.

Do NOT: add wings, hair, spikes, armour, weapons, extra legs, extra pincers or a second tail; make it a small real
scorpion or a cartoon; change the colours (glossy dark-brown chitin, lighter tan-orange stinger bulb, dark eyes);
let legs, claws or the tail touch each other or the body; crop the tail, the stinger, the claws or the feet; draw a
floor, a ground shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole creature inside the frame with margins (stinger and claws included); glossy dark-brown chitin; two dark eyes;
exactly TWO pincer arms each with ONE bulbous two-fingered claw, slightly open; exactly EIGHT walking legs (four per
side) with air gaps, all foot tips on one plane; ONE tail of five segments arching over the back with an air gap,
ending in ONE lighter tan stinger bulb with a dark sting point; transparent background; landscape 1536x1024; for
01-04 the same creature, pose, proportions and colours as the primary; side views: in `03_left` the head points to
image LEFT, in `04_right` to image RIGHT; the front view symmetric.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Each run adds its entries; do not remove other runs' entries.

## View runs notes (after run 1)

Claude accepted `00_three_quarter.png` (the second render of run 1) as the primary: glossy chestnut-brown chitin with
tan highlights, broad carapace with seven back plates, two dark eyes with a pale ring, two dark stubby chelicerae, two
big bulbous claws slightly open, a five-segment tail arching up and forward with a lighter tan-orange stinger bulb and
a dark sting point. In 01-04 keep exactly this creature: same proportions, colours, claws, tail and legs, and show
**all eight legs, four per side**, clearly separated (the primary hides one far-side leg; the views must not drop it).
`01_front`: straight on the face, symmetric, both claws forward low, the four legs of each side splayed outward, the
tail rising behind the body above the carapace with the stinger bulb on top (as in the original sprite). `02_back`:
the rear of the body with the tail base toward the camera and the tail rising and arching away from the camera, all
eight legs and both claws visible past the body. Side views: strict profiles at body height, all four near-side legs
with air gaps, the far legs seen between them, the tail arc and the stinger in profile, the near claw clear of the
head. Keep at least 60 px between the creature and every edge, and a clean transparent cutout (no glow or haze).

Each view run writes its record to `references_hd/generation_runs_<view>.json` (for example
`generation_runs_01_front.json`), not to `generation_runs.json`, because the four views run in parallel. Write only
your own view's PNG.
