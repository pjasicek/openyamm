# Codex brief: HD modelling references for the Tiger Mole (World of Xeen)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_mole_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Tiger Mole** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites. Your job is a
faithful high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached)

1. `native/sheet_codex.png`: two ORIGINAL frames, enlarged 4x with hard pixels, on flat grey (NOT part of the
   creature): standing (left) and attacking with both claws raised (right). Identity, proportion and colour
   authority. The brown dirt mound under it is NOT part of the creature: leave it out.
2. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature inside the frame with at least 60 px of
margin on every side, unresized returns, **1536x1024 LANDSCAPE**, true transparent background, no floor, no ground
shadow, no dirt, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the snout toward image RIGHT and turned about 35 degrees toward the camera (we see the face and the mole's LEFT flank), camera a little above the back |
| `01_front.png` | straight front: the face toward the camera, symmetric (the view of the original sprite) |
| `02_back.png` | straight back (the rump and tail toward the camera) |
| `03_left.png` | the mole's LEFT side: strict 90 degree profile, the snout toward image LEFT |
| `04_right.png` | the mole's RIGHT side: strict 90 degree profile, the snout toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as input 2. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Tiger Mole from the 1992 game
Might and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail, a credible fully three-dimensional animal.

Identity (from the original frames): a GIANT mole, about 1.4 m long and 0.8 m high at the shoulder hump, a heavy
rounded barrel body low to the ground, much longer than tall. FUR: dense, thick, slightly shaggy fur in a deep
TEAL-BLUE (blue-green, darker in the creases, lighter blue-teal on the top of the back, with faint darker streaks);
no stripes of another colour. HEAD: no visible neck, the head grows straight out of the body; a long, tapering,
naked pale grey-pink SNOUT pointing forward and slightly down, ending in a blunt pink nose tip; two small fierce eyes
with RED irises and black pupils under heavy angry fur brows, set on the front of the head above the snout; no
visible ears. FORELIMBS: short, very powerful, set wide at the sides of the head; huge flat spade-like HANDS with
naked pale grey-white skin, palms turned outward, each with FIVE long, thick, curved YELLOW-OLIVE CLAWS (digging
claws, as long as the hand itself). HIND LEGS: short, hidden mostly under the fur, small pale feet with short yellow
claws. TAIL: a thin, short, hairless pale grey-blue tail, curving up behind the rump.

Pose (identical in all five views): standing on all four limbs on level ground, the body low, the front hands
planted wide beside the head with the claws resting on the ground and spread with air gaps between them; the snout
level; the tail curving up behind.

Do NOT: draw the dirt mound; open the mouth; add teeth, horns, armour, stripes of another colour; make it cute, a
cartoon or a small realistic mole; change the colours (the fur stays teal-blue, the claws yellow-olive, the hands
and snout pale grey-pink); crop the claws, tail or rump; draw a floor, a ground shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole mole inside the frame with margins; long, low, heavy body; teal-blue fur; red angry eyes; long pale snout;
huge pale spade hands with five long yellow-olive claws each, spread and separated; thin hairless tail; no dirt;
transparent background; landscape 1536x1024; for 01-04 the same mole, pose, proportions and colours as the primary;
side views: in `03_left` the snout points to image LEFT, in `04_right` to image RIGHT; the front view symmetric.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected views), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the first render) as the primary: shaggy teal-blue barrel body, angry red
eyes, long pale pink snout, huge pale spade hands with five long yellow-olive claws each, small hind feet with yellow
claws, thin hairless grey-blue tail curving up. In 01-04 keep exactly this mole: same proportions, colours, fur, hands
and claws. `01_front`: straight on the face, the two hands planted wide and symmetric, claws spread on the ground.
`02_back`: the rump and the up-curved tail, the hind feet and the claw tips at the sides. Side views: strict profiles
at body height, both hands and all claws visible. Keep at least 60 px between the mole and every edge.
