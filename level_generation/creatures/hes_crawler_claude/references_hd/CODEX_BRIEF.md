# Codex brief: HD modelling references for the Acid Crawler (Hesper)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_crawler_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is a new creature of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style), not an MM sprite:
its design authority is the user-approved concept sheet `design/kreegan_world/concepts/monsters/fam_crawlers.png`
(copied as `references_hd/concept.png`).

## Inputs (attached in this order)

1. `references_hd/concept.png` — the APPROVED concept sheet. The LARGE creature on the right (pale bone-grey
   carapace) is tier A, the **Acid Crawler**, and is the design, proportion, material and colour authority. The small
   pale one at the lower left is the same creature in strict side view (use it for the segment count and leg
   placement). The rust-brown one with yellow egg pods (upper left) and the violet one (middle left) are other tiers:
   do NOT draw their colours, egg pods or swollen sacs. The dark grey background is not part of the creature.
2. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature inside the frame with generous margins,
unresized returns, **1536x1024 LANDSCAPE**, true transparent background, no floor, no ground shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the head toward image RIGHT and turned about 35° toward the camera (we see the face and the creature's LEFT flank), camera a little above the back so the top of the carapace and the leg gaps read |
| `01_front.png` | straight front: the face toward the camera, both sides symmetric |
| `02_back.png` | straight back (rear end toward the camera) |
| `03_left.png` | the creature's LEFT side: strict 90° profile, the head toward image LEFT |
| `04_right.png` | the creature's RIGHT side: strict 90° profile, the head toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`–`04` with the selected `00` as input 2. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT — GAME ASSET: a faithful high-definition 3D modelling reference of an approved creature concept, for an
MM6-8-style first-person RPG. Not a new design. Use case: 3D creature modelling reference sheet view.
Near-orthographic camera, even soft neutral studio light (no dramatic lighting, no rim light, no strong shadows: the
light is baked into the texture), painterly-realistic game materials like the concept, sharp fine detail, a credible
fully three-dimensional creature.

Identity (from the concept, tier A): a low, long, eight-legged alien arthropod about 1 m long, like a pill-bug
crossed with a scorpion WITHOUT a tail. BODY: an arched, segmented carapace of about SEVEN overlapping transverse
dorsal plates plus a larger rounded HEAD SHIELD at the front; each plate is pale bone-grey / ivory with darker grey
mottling and small pits, its lower edge flaring slightly outward over the flank, a small backward-pointing ridge
spike on the top midline of each plate. Under and between the plates the soft body shows: a glossy, faintly glowing
**acid-green** underside and flanks made of rounded swollen lobes, olive-green ringed joints. The rear end is
rounded and blunt (no tail, no stinger). HEAD: blunt and wide under the head shield, with TWO glossy dark-olive EYES
on EACH side of the head shield's front edge (four in all, the upper pair larger); a pair of large curved, hooked
bone-grey MANDIBLES at the sides of the mouth pointing forward-down, smaller brown inner mouthparts with short
fangs, and directly UNDER the jaw a rounded, translucent, glowing acid-green ACID SAC (about the size of a fist)
hanging from the throat. LEGS: eight short, sturdy jointed legs, four per side, evenly spaced along the body; each leg
has a pale bone-grey armoured upper segment (thigh plate), an olive-green ringed knee joint, a darker grey-brown
armoured lower segment and a hooked dark claw tip. Colours: pale bone-grey carapace, acid-green underside and joints,
dark olive eyes, the claw tips dark grey-brown.

Pose (identical in all five views): standing square and neutral on level ground, the body horizontal and low (the
carapace top about 0.45 m above the ground), legs splayed slightly OUTWARD to the sides so that **every leg is
separated from its neighbours and from the body by clear air gaps** (no leg in front of another in the side views as
far as possible; the knees a little higher than the hips' outer edge), all eight claw tips on ONE level ground plane.
Mandibles slightly open, the acid sac hanging below the jaw.

Do NOT: draw long hanging drips or strands of acid (only a glossy wet sheen and at most tiny beads on the mandible
tips); add egg pods, extra sacs, a tail, a stinger, wings, antennae or extra legs; change the colours; make the legs
long and spidery; tuck the legs out of sight under the plates; crop any leg, the head or the rear; draw a floor,
ground shadow, background or text.

## Per-image checks (re-run before you select a view)

Whole creature inside the frame with margins; exactly eight legs (four per side), each separated by air gaps, all
claw tips on one level; about seven dorsal plates plus the head shield, pale bone-grey with mottling and the small
midline spikes; acid-green glossy underside and joints; four eyes (two per side); a pair of hooked mandibles; the
round translucent green acid sac under the jaw; no long drips, no tail, no egg pods; transparent background;
landscape 1536x1024; for 01–04 the same creature, pose, proportions and colours as the primary; side views: in
`03_left` the head points to image LEFT, in `04_right` to image RIGHT; the front view symmetric. Stop after one
corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected views), written in run 2.

## Run 2 notes (after run 1)

Claude selected `00_three_quarter_run1_initial.png` as the primary (copied to `00_three_quarter.png`): it shows
exactly eight legs. `00_three_quarter_run1_correction.png` was rejected (nine leg forms): do not use it. In 01–04 count
the legs: the side views show the four near legs clearly separated (the far legs may peek out between them, but never
more than four far feet), the front and back views show all eight legs splayed symmetrically, four to each side.
Margins: keep at least 60 px between the creature and every edge. Side views are strict 90° profiles (camera at body
height, level), the front and back views straight on with the camera at body height, slightly above.
