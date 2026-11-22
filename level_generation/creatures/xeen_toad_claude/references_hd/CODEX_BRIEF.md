# Codex brief: HD modelling references for the Giant Toad (World of Xeen)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_toad_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Giant Toad** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites. Your job is a
faithful high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached in this order)

1. `native/sheet_standing_front.png`: two ORIGINAL standing frames (front view), enlarged 4x with hard pixels. This is
   the identity, proportion and colour authority. The flat grey background is NOT part of the creature. In the left
   frame the eyes are olive (lids half closed, a blink); the right frame shows the normal open dark eyes.
2. `native/sheet_attack_tongue.png`: two ORIGINAL attack frames (front view): the toad shoots a thick, translucent
   turquoise tongue at the viewer. Use it ONLY to understand the mouth; the tongue must NOT appear in your images.
3. `native/sheet_leap.png`: one ORIGINAL attack frame: the toad leaps at the viewer, front legs raised and spread.
   Use it for the hands (long fingers with round sticky pads) and the dome-shaped eyes; the dark blob below it is a
   drawn ground shadow, not part of the creature.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature inside the frame with at least 60 px of margin
on every side, unresized returns, **1536x1024 LANDSCAPE**, true transparent background, no floor, no ground shadow,
no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the face toward image RIGHT and turned about 35 degrees toward the camera (we see the face and the toad's LEFT flank), camera a little above the back so the top of the head, both eye domes and the folded hind leg read |
| `01_front.png` | straight front: the face toward the camera, both sides symmetric (the view of the original sprite) |
| `02_back.png` | straight back (the rump toward the camera) |
| `03_left.png` | the toad's LEFT side: strict 90 degree profile, the head toward image LEFT |
| `04_right.png` | the toad's RIGHT side: strict 90 degree profile, the head toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as input 4. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Giant Toad from the 1992 game
Might and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail, a credible fully three-dimensional animal.

Identity (from the original frames): an enormous, squat, very BROAD toad, about 1 m tall when sitting and about
1.6 m long, much wider than tall. No neck: the huge flat head merges straight into a round, heavy body. SKIN: warm
tan-brown to reddish-brown, entirely covered with rounded, flattened WARTS and bumpy tubercles of varied size, each
outlined by darker brown-black creases (like a cane toad's pebbled hide); slightly lighter tan on the bulging cheeks
and throat, darker brown on the back. HEAD: wide, flat, blunt snout with two small nostrils; a VERY WIDE mouth that
runs from side to side across the whole face, lips closed, the lip line a dark brown-black seam; two large bulging
EYE DOMES on top of the head, set wide apart, glossy dark brown-black eyeballs with a small bright highlight, framed by
heavy warty brow ridges; behind each eye a raised gland ridge. FRONT LEGS: short, very thick, muscular arms planted
wide apart in front of the body, the elbows out; each HAND has FOUR long, separate, slightly splayed fingers ending in
round, bulbous, lighter tan STICKY PADS (no claws, no webbing). HIND LEGS: huge, powerful, folded tightly at the sides
of the body (the big rounded thigh lobes beside the shoulders in the front view), the long hind FEET flat on the
ground beside and slightly behind the front hands, each with FIVE long toes ending in round pads, a little webbing
between the toes at the base only. No tail.

Pose (identical in all five views): the classic sitting toad posture on level ground, body tilted slightly up at the
front, chin about 0.35 m above the ground; front arms straight and planted wide; hind legs folded at the sides; all
fingers and toes spread flat on ONE level ground plane and **separated from each other by clear air gaps** (no finger
on top of another). Mouth CLOSED. Eyes open.

Do NOT: show the tongue; open the mouth; add teeth, horns, spikes, a tail, claws, armour or any object; make it a
cute cartoon frog, a smooth green frog or a tree frog; change the colours (no green skin); make the legs thin; crop
the fingers, toes or the rump; draw a floor, a ground shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole toad inside the frame with margins; squat and much wider than tall; tan to reddish-brown warty hide with dark
creases; two large glossy dark eye domes on top of the head; a closed, very wide mouth; FOUR fingers with round pads
on each hand and FIVE toes with round pads on each hind foot, all separated and flat on one level; hind legs folded
at the sides; no tongue, no teeth, no tail; transparent background; landscape 1536x1024; for 01-04 the same toad,
pose, proportions and colours as the primary; side views: in `03_left` the head points to image LEFT, in `04_right`
to image RIGHT; the front view symmetric. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected views), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the first render) as the primary: identity, warty tan-brown hide, dark eye
domes, closed wide mouth, four padded fingers per hand. In 01-04 keep exactly this toad: same proportions (much wider
than tall, the big folded hind thigh at each side), same colours and wart pattern, same eye domes, mouth closed. Hind
feet: show the long toes with round pads spread flat beside and behind the front hands (five per foot if possible,
never fewer than four). Side views: strict 90 degree profiles at body height; the front and back views straight on,
camera slightly above. In `02_back` show the warty rump and the backs of both folded hind legs with the feet visible
at the sides. Keep at least 60 px between the toad and every edge.
