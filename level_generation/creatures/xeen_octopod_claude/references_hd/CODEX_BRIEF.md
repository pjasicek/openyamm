# Codex brief: HD modelling references for the Octopod (World of Xeen, Darkside)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_octopod_claude/references_hd/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Octopod** of Might and Magic V: Darkside of Xeen (1993), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites, rising out of a lake.
Your job is a faithful high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached)

1. `native/sheet_codex.png`: four ORIGINAL frames, enlarged 4x with hard pixels, on flat grey (the grey is NOT part
   of the creature). Top left, top right, bottom left: the octopod at rest in the water, its domed head and face
   above the surface and its tentacles rising out of the water around it in arches. Bottom right: the head ducked
   lower with the tentacles over it. Identity, proportion and colour authority. The teal water and splash at the
   bottom are the lake, NOT the creature: leave them out.
2. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature inside the frame with at least 80 px of
margin on every side, unresized returns, **1536x1024 LANDSCAPE**, true transparent background, no water, no floor
plane, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the face turned about 35 degrees toward image RIGHT, camera a little above the top of the head looking slightly down (so the star of tentacles is seen in depth) |
| `01_front.png` | straight front (the view of the original sprite): the face toward the camera, camera level with the eyes, a little above |
| `02_back.png` | straight back: the back of the dome toward the camera |
| `03_left.png` | the creature's LEFT side: strict 90 degree profile, the face toward image LEFT |
| `04_right.png` | the creature's RIGHT side: strict 90 degree profile, the face toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocations): `01`-`04` with the selected `00` as input 2. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Octopod from the 1993 game
Might and Magic V: Darkside of Xeen, reconstructed from its original low-resolution sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail, a credible fully three-dimensional creature. Show the WHOLE creature as if the water had
been removed: everything that would be under the surface is visible too.

Identity (from the original frames): a GIANT OCTOPUS monster. HEAD: one big smooth rounded DOME (the mantle), a little
taller than wide, glossy saturated crimson-scarlet RED with a soft pale highlight on top and darker maroon-red in the
creases. FACE (on the front of the dome, low down): two big round BLUE EYES (bright cerulean irises, a dark navy rim,
a small black pupil, a white catch-light) set wide apart under heavy furrowed red BROW RIDGES that give a stern,
skull-like frown; between and below the eyes the face narrows into a short "beard" of FIVE thick vertical ridged
folds (short stubby mouth tentacles) hanging straight down to the base of the head. No beak visible, no teeth.
TENTACLES: exactly EIGHT long thick tentacles, the same red as the head with paler pink-red highlights along their
tops, smooth and glossy, tapering from a thick root (about a third of the head's width) to a thin pointed tip. Along
the UNDERSIDE of every tentacle (the side facing the head and the inside of each arch) runs a row of round
YELLOW-OLIVE (mustard) RING SUCKERS, each a raised ring with a darker hollow centre, from the root to near the tip.

Pose (identical in all five views): the octopus floats level, the dome upright, the face looking straight forward;
the base of the head and the roots of the tentacles lie on one invisible horizontal plane (the water surface). The
eight tentacles radiate out from under the head in an even STAR, like the spokes of a wheel, 45 degrees apart, none
pointing straight forward (the front two leave the face clear, one to each side of it). Each tentacle first runs out
level along the plane for about a head-width, then rises in a tall smooth ARCH up to about the height of the top of
the head, and its last third curls over OUTWARD (away from the head) into a hook with the pointed tip hanging down.
Every tentacle is clearly separated from its neighbours and from the head by open air gaps; they do not cross or
touch. The whole star is about 4.5 head-widths across (tip of the left arch to tip of the right arch); the dome rises
about 1.1 head-widths above the plane.

Do NOT: draw water, waves, foam, splashes or ink; add more or fewer than eight tentacles; add a beak, teeth, horns,
spikes, armour, fins or extra eyes; tangle or cross the tentacles; let a tentacle hide the face; change the colours
(red head and tentacles, blue eyes, yellow-olive suckers); make it cute or a cartoon; crop any tentacle tip; draw a
floor plane, a shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole creature inside the frame with at least 80 px margins; one red domed head with the stern face (two blue eyes,
brow ridges, the five-fold beard) facing the stated direction; exactly eight red tentacles in an even star, each
level near the head then arching up and curling outward at the tip, all separated by air gaps; a row of yellow-olive
ring suckers on each tentacle's underside; no water or splash; transparent background; landscape 1536x1024; in
`01`-`04` the same creature, pose, proportions, tentacle count and colours as the primary; the front view symmetric;
in `03_left` the face toward image LEFT, in `04_right` toward image RIGHT; `02_back` shows the smooth back of the dome
(no face) with the tentacle star around it.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Run-2 workers write `references_hd/generation_runs_<view>.json`
instead and do not write a contact sheet (Claude makes `selected_views_review.png`).

## Run 1b notes (Claude's gate on run 1)

Run 1's selected image (`raw/00_three_quarter_run1_selected.png`, attached as input 2) has the right HEAD, face, red
skin and ring suckers: keep exactly that head and those materials. It fails on: only seven tentacles readable (the
back ones hide behind the dome), a near-frontal camera, and a faint red/yellow halo in the transparent margin. Make a
new `00_three_quarter.png` (move the run-1 image aside, it is already copied to `raw/`):

- Camera HIGHER: about 40 degrees above the horizontal, looking down at the creature, the face turned about 35
  degrees toward image RIGHT, so all EIGHT tentacles and the ring they form round the head are seen from above.
- The eight tentacles in an even star round the head, 45 degrees apart: front-right and front-left (one to each side
  of the face, low, leaving the face clear), right and left, back-right and back-left, and two at the back. Every
  tentacle's root at the base of the head, every tentacle's whole length and its pointed TIP clearly visible and
  separate (count them: eight tips). Each one runs out from the head low and nearly level, then rises in an arch and
  hooks its tip over outward and down, as in input 2.
- A clean cut-out: fully transparent background, NO glow, haze, halo or coloured fringe in the transparent area.

One generation, at most one corrective regeneration; append the entries to `generation_runs.json`.

## Run 2 notes (after run 1b)

Claude accepted the run-1b `00_three_quarter.png` (input 2) as the primary: the red dome with the stern brow ridges,
the two blue eyes and the five-fold beard; eight red tentacles in an even star round the base of the head, each
running out low, rising in an arch and hooking its pointed tip outward and down, a row of mustard ring suckers on each
underside. In 01-04 keep exactly this creature: the same head, face, proportions, tentacle count, tentacle shape and
spacing, suckers and colours. Near-orthographic straight views, camera level with the eyes and a little above
(about 15 degrees) so the star of tentacles still reads. `01_front`: the face toward the camera, symmetric, two
tentacles low to each side of the face (front-left and front-right), the others round and behind. `02_back`: the
smooth back of the dome, the two back tentacles in front of it to each side, no face. `03_left`: strict 90 degree
profile, the face toward image LEFT. `04_right`: strict 90 degree profile, the face toward image RIGHT. Clean cut-out
on true transparency (no glow, haze or halo), 1536x1024 landscape, at least 80 px of margin.

Each run-2 worker generates ONE view only (named in its prompt). Write its record to
`references_hd/generation_runs_<view>.json` (same fields as generation_runs.json), not to generation_runs.json, and do
not write the contact sheet (Claude makes it). Keep a rejected draft as `raw/<view>_rejected_<n>.png`.
