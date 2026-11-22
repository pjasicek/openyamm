# Codex brief: HD modelling references for Xeen's Guard (World of Xeen)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_guard_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is **Xeen's Guard** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites. Your job is a
faithful high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached in this order)

1. `native/sheet_standing_front.png`: two ORIGINAL idle frames (front view), enlarged 4x with hard pixels. This is the
   identity, proportion and colour authority. The flat grey background is NOT part of the creature. The figure is
   seen from the front; the creature's RIGHT arm is on image LEFT.
2. `native/sheet_attack.png`: two ORIGINAL attack frames (front view). The green vertical beam is a spell effect fired
   from the red gem; it must NOT appear in your images. Use the frames only to understand the body.
3. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one figure each, the whole figure inside the frame with at least 80 px of margin on
every side (feet and hands included), unresized returns, **1024x1536 PORTRAIT**, true transparent background, no
floor, no ground shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the figure faces image RIGHT, turned about 35 degrees toward the camera (we see its chest, the front of the dome with the gem, and its LEFT side), camera at about chest height, slightly above |
| `01_front.png` | straight front, symmetric (the view of the original sprite) |
| `02_back.png` | straight back |
| `03_left.png` | the figure's LEFT side: strict 90 degree profile, the chest toward image LEFT |
| `04_right.png` | the figure's RIGHT side: strict 90 degree profile, the chest toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as input 3. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of Xeen's Guard from the 1992 game
Might and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no coloured reflections, no strong shadows: the light is baked into the texture),
painterly-realistic game materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the original frames): a HEADLESS, massively built humanoid GUARDIAN CONSTRUCT (a magical robot
guard), about 1.9 m tall, with the bulk of a heavyweight wrestler: huge rounded shoulders and deltoids, thick
segmented arms, a broad muscular chest with big pectoral plates, a narrow waist, thick thighs. It has NO head and
NO neck: in their place, sitting low between the shoulders and rising from the top of the chest, is a smooth
EGG-SHAPED DOME (like a featureless helmet, taller than wide, about as wide as the chest's upper third). On the dome:
a thin RED vertical SEAM line running down its middle from the top to where it meets the chest, a ROUND polished
RED GEM set in the seam in the upper third of the dome's front, and a short red vertical stripe on each side of the
dome. No face, no eyes, no visor, no mouth.
MATERIAL: the whole body is plated in polished CHROME-SILVER metal (bright silver-grey with soft white highlights,
medium grey in the creases), sculpted like stylised muscles made of armour plates, with fine dark panel lines
between the plates; a few tiny GREEN rivet lights down the middle of the chest below the dome. A thin RED band
around the right forearm. WAIST: a band of black metal with a thin CYAN ring around it. HIPS and CROTCH: black
metal. Two smooth glossy CYAN-BLUE TUBES run from the crotch diagonally down to the inside of each knee. THIGHS and
SHINS: chrome-silver. KNEES: ribbed black-and-dark-grey metal knee rings. FEET: heavy, rounded, glossy BLACK BOOTS
with a thin red curved stripe on the outer side. HANDS: large chrome hands with FIVE thick segmented fingers ending
in short pointed metal CLAWS (four fingers and a thumb on each hand), a small green dot of light in each palm.

Pose (identical in all five views): standing upright in a relaxed A-POSE: both arms hanging away from the body
about 35 degrees from vertical, elbows very slightly bent, the hands open with the clawed fingers SPREAD and
SEPARATED (a clear gap between every finger and between the hands and the thighs); the legs straight, feet planted
shoulder-width apart with a clear gap between the legs and the cyan tubes visible. The dome upright.

Do NOT: add a head, a face, eyes, a visor, a neck, horns, spikes, a cape, a weapon, a shield, wings, a backpack,
extra arms, belts or pouches; add lightning, a beam, sparks or any effect; make the gem or seam any colour but red;
change the chrome to gold, white, bronze or rust; make the boots anything but black; crop any part; draw a floor, a
ground shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole figure inside the frame with margins (dome top, both hands, both boots); headless: an egg-shaped dome with a
red seam and a round red gem sits where the head would be, no face; chrome-silver plated muscular body; black waist
with a thin cyan ring; black crotch with two cyan tubes running to the inner knees; black ribbed knee rings; black
boots; five clawed fingers per hand, spread; A-pose with clear gaps under the arms and between the legs; transparent
background; portrait 1024x1536; for 01-04 the same figure, pose, proportions and colours as the primary; side views:
in `03_left` the chest points to image LEFT, in `04_right` to image RIGHT; the front view symmetric (apart from the
red band on the right forearm, which is on image LEFT in the front view). Stop after one corrective regeneration per
view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected views), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the corrective render) as the primary: headless chrome-silver brute, egg dome
with the red seam, the round red gem and the red side stripes, three green chest rivets, black waist with the cyan
ring, black briefs with two cyan tubes to the inner knees, ribbed black knee rings, black boots with the red outer
stripe, the red band on the right forearm, five clawed fingers per hand with a green palm dot, A-pose. In 01-04 keep
exactly this figure: the same proportions (huge shoulders, dome sitting low between them, narrow waist, thick
thighs), the same materials and colours, the same A-pose (arms about 35 degrees from vertical, hands open and spread,
legs apart). Side views: strict 90 degree profiles at chest height, showing the dome's profile (the gem on its front
in profile), the depth of the chest and shoulders, the hip tube running to the inner knee, the boot's length; the
arm nearest the camera must not hide the torso (it hangs out to the side and slightly forward as in the A-pose).
In `02_back`: the back of the dome (the red seam continues over the top and down the back of the dome), the back
plates of the shoulders and the back, the black waist band and the black seat, the backs of the boots. Keep at
least 80 px between the figure and every edge, and a true transparent background.
