# Codex brief: HD modelling references for the Flying Feet (World of Xeen, magic construct)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_feet_claude/references_hd/`. Do not edit
any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Flying Feet** monster of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an
MM6-8-style first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites. Your job is
a faithful high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

The original sprite shows a PAIR of disembodied winged feet. The 3D model will use ONE foot and a mirrored copy, so
draw exactly ONE foot: a **RIGHT** foot (big toe on the creature's left/inner side, little toe on its right/outer side).

## Inputs (attached in this order)

1. `native/sheet_codex.png`: two ORIGINAL frames enlarged 4x with hard pixels (left: the idle pair; right: the attack,
   the near foot kicking its sole at the viewer). The grey background and the dark drop shadows are NOT part of the
   creature.
2. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one foot each, the whole foot and both wings inside the frame with at least 80 px of
margin on every side, unresized returns, **1536x1024 LANDSCAPE**, true transparent background, no floor, no ground
shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: toes toward image RIGHT, the foot turned about 35 degrees toward the camera (we see the toes, the top of the foot and its INNER / big-toe side), camera a little above |
| `01_front.png` | straight front: looking at the tips of the toes, the wings spread symmetrically to both sides |
| `02_back.png` | straight back: looking at the heel, the wings spread to both sides |
| `03_left.png` | the foot's LEFT (inner, big-toe, arch) side: strict 90 degree profile, toes toward image LEFT |
| `04_right.png` | the foot's RIGHT (outer, little-toe) side: strict 90 degree profile, toes toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as the last input. At most one corrective regeneration
per view. Records: `references_hd/generation_runs.json` (id, view, prompt, input paths with sha256, output path,
selected flag, reason, superseded runs) and, in run 2, the contact sheet `references_hd/selected_views_review.png`.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Flying Feet from the 1992 game Might
and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design. Use case:
3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no dramatic
lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game materials,
sharp fine detail, a credible fully three-dimensional object.

Identity (from the original frames): ONE disembodied bare human RIGHT foot, adult size (about 26 cm long), magically
flying like the winged sandals of Hermes. SKIN: warm tan / peach (light 228,184,160, mid 212,160,128, shade 192,132,92,
deep creases 128,80,44), smooth, with realistic toes, toenails, knuckle creases, an arch, a rounded heel and ankle
bones. Five toes, the big toe largest, toenails pale and clean. The foot ENDS just above the ankle bones: a short
stump, its top closed by a smooth, rounded, skin-covered cap (no blood, no bone, no wound, no cut flesh). WINGS: exactly
TWO small white bird wings, one on each side of the ankle (one on the inner side, one on the outer side), attached
just above the ankle bones, each wing about as long as the foot, layered white feathers with pale grey shading, the
feather tips fanned and curled slightly upward; both wings spread out sideways and a little up and back, clear of the
foot and of each other.

Pose (identical in all five views): hovering level, the sole flat and horizontal (as if standing on an invisible
floor), toes relaxed and straight, the two wings spread wide to the sides.

Do NOT: draw two feet, a leg, a shin, a sandal or a shoe, a strap, blood or a wound, a glow or a halo, motion blur,
extra wings or more than five toes; crop the wings; draw a floor, a shadow, a background or text.

## Per-image checks

One right foot only, whole inside the frame with margins; five toes, big toe on the foot's inner side; the ankle ends
in a smooth skin cap; exactly two white feathered wings, one per ankle side, clear of the foot; warm tan skin;
transparent background; landscape 1536x1024; 01-04 identical foot, wings and pose; `03_left` toes to image LEFT showing
the arch and big toe, `04_right` toes to image RIGHT showing the little toe side.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the first render: a right foot seen from its OUTER side, toes toward image
right and the camera, the outer ankle bone visible, the flat-topped skin-covered ankle stump, one wing from each side
of the ankle) as the primary. In 01-04 keep exactly this foot: the same proportions, skin, veins, toenails, stump and
the same two wings (size, shape, feather layers, the same spread angle: out sideways and up). Side views: strict 90
degree profiles (the two wings then overlap each other, mostly seen edge-on to three-quarter); front and back
straight on, the wings spread symmetrically to both sides. Keep at least 80 px of margin and no faint alpha pixels at
the canvas edges. Remember: `03_left` is the foot's INNER (big toe, arch) side with the toes to image LEFT;
`04_right` is the OUTER (little toe) side with the toes to image RIGHT.
