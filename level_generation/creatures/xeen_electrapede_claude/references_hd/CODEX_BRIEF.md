# Codex brief: HD modelling references for the Electrapede (World of Xeen, Darkside)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_electrapede_claude/references_hd/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Electrapede** of Might and Magic V: Darkside of Xeen (1993), a giant electric centipede, rebuilt as a 3D
creature for an MM6-8-style first-person RPG. The original game drew it only from the FRONT, as small low-resolution
sprites. Your job is a faithful high-definition reconstruction of that creature as a 3D modelling reference, not a
new design.

## Inputs (attached)

1. `native/sheet_codex.png`: three ORIGINAL frames, enlarged 4x with hard pixels, on flat grey (the grey is NOT part
   of the creature). Identity, proportion and colour authority:
   - top: standing (the head faces the viewer, the long body recedes behind it to the upper right);
   - middle: attacking, the mouth open with small teeth. The YELLOW LIGHTNING around it is a spell effect, NOT part of
     the creature: never draw lightning;
   - bottom: the body curled up, showing the round green segment plates from the side and the many purple legs
     underneath.
2. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature inside the frame with at least 60 px of
margin on every side (antenna tips and every leg included), unresized returns, **1536x1024 LANDSCAPE**, true
transparent background, no floor, no ground shadow, no lightning, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from above: the body lies in one STRAIGHT line from the tail at image LEFT to the head at image RIGHT, the whole creature turned about 35 degrees toward the camera so we see the face and the creature's LEFT side with all its left legs; camera about 30 degrees above the ground |
| `01_front.png` | straight front: the face toward the camera, symmetric (the view of the original sprite); the body hidden behind the head except the legs at the sides |
| `02_back.png` | straight back: the tail end toward the camera, the body receding to the head |
| `03_left.png` | the creature's LEFT side: strict 90 degree profile at body height, the head toward image LEFT |
| `04_right.png` | the creature's RIGHT side: strict 90 degree profile at body height, the head toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as input 2. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Electrapede from the 1993 game
Might and Magic V: Darkside of Xeen, reconstructed from its original low-resolution front sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail, a credible fully three-dimensional creature.

Identity (from the original frames): a GIANT CENTIPEDE about 2.2 m long, lying low on the ground. BODY: about 14
rounded, glossy, bright LEAF-GREEN segment plates (each a smooth domed arch, slightly overlapping the next, with a
darker green rim and dark green creases between the plates), the body about 0.30 m wide and 0.22 m high behind the
head and tapering slowly toward a blunt tail end; the UNDERSIDE dark teal-blue slate grey. HEAD: broad, flat and wider
than the body (about 0.42 m), shaped like a rounded shield narrowing to the mouth, green plates outlined in dark green;
two HUGE glossy MAGENTA compound EYES (bright pink-magenta with a white-pink highlight, dark rims) covering the upper
half of the face; small green mandibles at the mouth (mouth closed); thin short green palps sticking out at the sides
of the head. ANTENNAE: thin, segmented, dark purple-magenta antennae rising from the top of the head and curving up
and outward (an inner short pair curving up like hooks and an outer longer pair sweeping up and out, as in the
frames). LEGS: one pair of legs per body segment (about 14 pairs), thin and jointed (thigh, shin and a pointed foot),
MAGENTA-VIOLET with dark purple joint bands, splayed out sideways from under the plates and bending down to the ground.

Pose (identical in all five views): the body lies in ONE STRAIGHT LINE, low, belly just above the ground; the head
level and facing straight forward along the body; ALL legs splayed out to the sides with clear air gaps between
neighbouring legs, every foot on ONE level ground plane; the antennae raised; the mouth closed.

Do NOT: draw lightning, sparks or glow; curl, coil or bend the body; open the mouth; add wings, a stinger, pincers,
extra eyes, horns or armour spikes; change the colours (the plates stay bright green, the eyes magenta, the legs and
antennae magenta-violet, the underside dark slate); make it cute or a cartoon; crop the antennae, legs or tail; draw
a floor, a ground shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole centipede inside the frame with margins; straight body of about 14 domed bright-green plates tapering to the
tail; broad head with two huge magenta eyes; thin magenta-violet legs, one pair per segment, separated by air gaps,
all feet on one level; purple antennae; no lightning; transparent background; landscape 1536x1024; for 01-04 the same
creature, pose, proportions, leg count and colours as the primary; side views: in `03_left` the head points to image
LEFT, in `04_right` to image RIGHT; the front view symmetric.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected views), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the corrective render of run 1) as the primary: a straight body of 15 domed
glossy leaf-green plates with dark green creases and a dark slate underside, tapering to a blunt tail; a green head
about as wide as the body with two huge pebbled magenta eyes, a closed green mouth with small mandibles and short green
palps (spikes) at the sides; four magenta-violet segmented antennae (an inner short pair curving up like hooks, an outer
longer pair sweeping up and out); one magenta-violet leg per plate on each side, each leg leaving the side of its plate
from a ring socket and reaching down and outward to a pointed foot. In 01-04 keep exactly this creature: the same
proportions, plate count, leg count and shape, colours and antennae. `01_front`: straight on the face, legs of both
sides fanning out symmetrically left and right, the body hidden behind the head. `02_back`: straight on the tail end,
the body receding to the head, the antennae visible above. Side views: strict 90 degree profiles at body height
(camera level with the body, not from above), the whole length with every leg of the near side, feet on one level.
The body is long: keep the whole body inside the 1536 px width with at least 60 px margin at both ends (draw it
smaller if needed). Keep at least 60 px of margin everywhere and no faint alpha pixels at the canvas edges.
