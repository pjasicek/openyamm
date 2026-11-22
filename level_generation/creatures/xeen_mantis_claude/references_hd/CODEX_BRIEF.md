# Codex brief: HD modelling references for the Mantis Ant (World of Xeen)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_mantis_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Mantis Ant** of Might and Magic V: Darkside of Xeen (1993), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites. Your job is a
faithful high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached)

1. `native/sheet_codex.png`: two ORIGINAL frames, enlarged 4x with hard pixels, on flat grey (the grey is NOT part
   of the creature): standing (left) and attacking with both raptorial forearms thrown out to the sides (right).
   Identity, proportion and colour authority.
2. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature inside the frame with at least 60 px of
margin on every side, unresized returns, **1536x1024 LANDSCAPE**, true transparent background, no floor, no ground
shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the face toward image RIGHT and turned about 35 degrees toward the camera (we see the face and the creature's LEFT side), camera at chest height, a little above |
| `01_front.png` | straight front: the face toward the camera, symmetric (the view of the original sprite) |
| `02_back.png` | straight back (the back of the head, thorax and the abdomen toward the camera) |
| `03_left.png` | the creature's LEFT side: strict 90 degree profile, the face toward image LEFT |
| `04_right.png` | the creature's RIGHT side: strict 90 degree profile, the face toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as input 2. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Mantis Ant from the 1993 game
Might and Magic V: Darkside of Xeen, reconstructed from its original low-resolution front sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail, a credible fully three-dimensional giant insect.

Identity (from the original frames): a GIANT insect, about 1.6 m tall, that stands LOW and UPRIGHT like a crouching
frog crossed with a praying mantis: the body is held vertical, the head on top, the legs splayed wide and bent like a
crouching frog's.
- CHITIN: glossy PURPLE-VIOLET exoskeleton everywhere on the head, thorax, arms and legs (vivid violet with lighter
  lilac highlights and darker purple in the creases), smooth hard shell, no hair.
- HEAD: large, rounded, insect head with a ridged crown; two short thin segmented ANTENNAE rising from the top of the
  head with small round knobs at their tips; two LARGE glowing TEAL-CYAN compound EYES, wide-set and angled
  (angry), on the upper face; below them a round YELLOW-ORANGE RADIAL MOUTH: a ring of short pointed mandible petals
  arranged like a flower or star around a dark centre (about eight petals). No teeth, no jaws hanging open.
- THORAX: a short segmented purple thorax under the head with horizontal rib-like plates down its front, like a
  segmented insect chest.
- ABDOMEN: below the thorax, hanging between the legs, a rounded abdomen whose front/underside is dark charcoal-black
  chitin, ending at the bottom in a pointed RED chevron tip (dark red, like a downward pointing heart shape); the
  abdomen tip stays clear of the ground.
- ARMS: TWO raptorial forearms (like a praying mantis's), one on each side at the top of the thorax: a thick purple
  upper arm rising from the shoulder beside the head, ending in a big curved HOOKED CLAW (a smooth scythe-like hook)
  that curls inward at head height. Only one hook per arm, no fingers.
- LEGS: FOUR thin jointed purple legs (two per side, a front and a rear leg), attached at the sides of the lower
  thorax with round ball joints; each leg goes out sideways to a bulbous knee, then down to the ground; each foot has
  three or four thin spread claw-toes. Splayed wide like a crouching frog.
- No wings, no fins, no tail, no spikes along the back.

Pose (identical in all five views): standing on its four legs on level ground, the body upright, the feet planted
wide on ONE flat plane with clear air gaps between all four legs and between the legs and the abdomen; both arms in
the native standing pose (upper arms raised beside the head, hooks curled inward at head height) but held a little
away from the head and body so there is a clear air gap between each arm, its hook and the head; the antennae up.

Do NOT: add wings, fins, a tail, back spikes, armour, weapons, extra arms or legs, teeth or an open jaw; make it a
real ant or a real praying mantis (keep this upright frog-mantis body); make it cute or a cartoon; change the colours
(purple chitin, teal-cyan eyes, yellow-orange radial mouth, charcoal abdomen with a red tip); let the arms touch the
head; crop the antennae, hooks or feet; draw a floor, a ground shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole creature inside the frame with margins; upright crouching body; purple chitin; two teal-cyan eyes; the
yellow-orange radial mouth; two antennae; exactly TWO arms each with ONE hooked claw, clear of the head; exactly FOUR
legs (two per side) with air gaps, all feet on one plane; charcoal abdomen with a red tip clear of the ground; no
wings; transparent background; landscape 1536x1024; for 01-04 the same creature, pose, proportions and colours as the
primary; side views: in `03_left` the face points to image LEFT, in `04_right` to image RIGHT; the front view
symmetric.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected views), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the second render, after the framing correction) as the primary: glossy
purple chitin, ridged head, two knobbed antennae, two teal-cyan eyes, the eight-petal yellow-orange radial mouth, the
stacked rib plates of the thorax, the charcoal abdomen with its red tip, two raised arms each ending in one crescent
hook clear of the head, four jointed legs with ball knees and clawed feet on one plane. In 01-04 keep exactly this
creature: same proportions, colours, arms, hooks, legs and feet. `01_front`: straight on the face, symmetric, both
arms raised with the hooks curling inward above the shoulders, all four legs splayed with the rear feet visible
between and behind the front feet. `02_back`: the back of the head, the dorsal plates of the thorax and the back of
the abdomen, both arms and all four legs. Side views: strict profiles at chest height, the front and rear leg of the
near side both visible with an air gap, the arm and its hook clear of the head. Keep at least 60 px between the
creature and every edge, and a clean transparent cutout (no glow or haze).
