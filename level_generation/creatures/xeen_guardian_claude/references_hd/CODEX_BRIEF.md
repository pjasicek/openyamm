# Codex brief: HD modelling references for the Guardian (World of Xeen)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_guardian_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Guardian** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites. Your job is a
faithful high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached in this order)

1. `native/sheet_standing_front.png`: two ORIGINAL idle frames (front view), enlarged 4x with hard pixels. This is the
   identity, proportion and colour authority. The flat grey background is NOT part of the creature. In the left frame
   the jaw is closed; in the right frame the jaw is slightly open with a dark gap between the tooth rows (the mouth
   we want) and the green eye glints are brighter.
2. `native/sheet_attack_jaw.png`: one ORIGINAL attack frame (front view): the eyes flare and yellow-green lightning
   forks spring from them. Use it ONLY to understand the jaw and the eye sockets; the lightning must NOT appear in
   your images.
3. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one skull each, the whole skull inside the frame with at least 80 px of margin on
every side, unresized returns, **1024x1536 PORTRAIT**, true transparent background, no floor, no ground shadow, no
text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the face toward image RIGHT and turned about 35 degrees toward the camera (we see the face, both eye sockets, the gem and the skull's LEFT side with its cheekbone, temple and jaw hinge), camera a little above eye level so the top of the cranium reads |
| `01_front.png` | straight front: the face toward the camera, symmetric (the view of the original sprite) |
| `02_back.png` | straight back (the back of the cranium toward the camera) |
| `03_left.png` | the skull's LEFT side: strict 90 degree profile, the face toward image LEFT |
| `04_right.png` | the skull's RIGHT side: strict 90 degree profile, the face toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as input 3. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Guardian from the 1992 game
Might and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no coloured reflections, no strong shadows: the light is baked into the texture),
painterly-realistic game materials, sharp fine detail, a credible fully three-dimensional object.

Identity (from the original frames): a GIANT disembodied HUMAN SKULL, a magical guardian construct, about 0.8 m tall,
with NO body, no neck and no spine: the skull alone floats in the air. MATERIAL: polished CHROME-SILVER metal over the
whole skull and all the teeth, bright silver-grey with soft white highlights on the dome and cheekbones and medium
grey in the hollows (temples, around the nose and the sockets, under the cheekbones); a smooth, cast, slightly worn
metal surface, NOT white bone, not gold, not rusty. SHAPE: a large, rounded, slightly tall cranium (wider at the
temples than at the jaw), a strong brow ridge, high pronounced cheekbones, a triangular dark nasal cavity, and a
full HUMAN JAW: the lower jaw (mandible) is a SEPARATE bone hinged under the cheekbones, with a rounded chin. TEETH:
complete upper and lower rows of square, even, human teeth in the same chrome silver, the individual teeth clearly
separated by dark grooves. GEM: one ROUND, polished, faceted RUBY-RED gem (deep red with a bright red-orange
highlight) set high in the middle of the forehead, about the width of an eye socket, sitting in a slightly raised
silver mount. EYES: the eye sockets are deep and DARK (black-grey inside), and in the centre of each socket floats a
small round GREEN glint (an emerald-green spark with a lighter green centre, about a third of the socket's width).
No pupils, no eyeballs, no eyelids.

Pose (identical in all five views): the skull upright and level, as if looking straight ahead. The MOUTH SLIGHTLY
OPEN: the lower jaw dropped a little so that a clear DARK GAP (about one tooth height) separates the upper and the
lower tooth row along the whole mouth, as in the right frame of input 1. Both tooth rows fully visible.

Do NOT: add a body, neck, spine, ribs, horns, a crown, a helmet, cracks, runes, armour, tubes, wires or any object;
add lightning, sparks, flames, smoke or any effect; make the gem any colour but red; make the eye glints any colour
but green, or fill the sockets with eyeballs; change the silver to white bone, gold or rust; close the mouth; open
the mouth wide; drop the lower jaw off the skull; make it a cartoon skull; crop any part; draw a floor, a ground
shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole skull inside the frame with margins; polished chrome-silver everywhere, no white bone; round red gem high in the
middle of the forehead (seen in 00 and 01; seen edge-on or partly in 03 and 04; hidden in 02); dark sockets each with
a small green glint; triangular nasal cavity; complete upper and lower human tooth rows with a clear dark gap
between them; a separate lower jaw with its hinge under the cheekbone (visible in 00, 03 and 04); no body, no neck,
no lightning; transparent background; portrait 1024x1536; for 01-04 the same skull, pose, jaw opening, proportions
and colours as the primary; side views: in `03_left` the face points to image LEFT, in `04_right` to image RIGHT;
the front view symmetric. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected views), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the first render) as the primary: chrome-silver skull, round faceted ruby in a
raised silver mount high on the forehead, dark sockets with small green glints, full upper and lower tooth rows with a
clear dark gap, separate lower jaw with its hinge under the cheekbone, clean alpha. In 01-04 keep exactly this skull:
same proportions (cranium wider than the jaw, strong cheekbones), same chrome-silver material and highlights, same
gem and mount, same green glints, the SAME slightly open jaw with the dark gap between the tooth rows. Side views:
strict 90 degree profiles at eye height, showing the gem's mount in profile on the forehead, the jaw hinge and the
whole mandible with its chin; the front view straight on, symmetric, like the original sprite; in `02_back` show the
smooth back of the cranium and the back of the jaw (the gem is not visible). No lightning, no body, no neck. Keep at
least 80 px between the skull and every edge, and a true transparent background.
