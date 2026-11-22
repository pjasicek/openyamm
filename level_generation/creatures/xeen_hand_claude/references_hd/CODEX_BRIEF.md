# Codex brief: HD modelling references for the Carnage Hand (World of Xeen)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_hand_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Carnage Hand** of Might and Magic IV: Clouds of Xeen (1992), a magic construct rebuilt as a 3D creature
for an MM6-8-style first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites.
Your job is a faithful high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached in this order)

1. `native/sheet_codex.png`: three ORIGINAL frames, enlarged 4x with hard pixels, on flat grey (NOT part of the
   creature): the closed fist, the half-open hand with the mouth in its palm, and the fully spread hand. Identity,
   proportion and colour authority.
2. `native/sheet_maw_x6.png`: the fully spread ORIGINAL attack frame at 6x: the detail of the mouth in the palm.
3. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one hand each, the whole hand inside the frame with at least 60 px of margin on
every side, unresized returns, **1536x1024 LANDSCAPE**, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | the PALM toward the camera, the hand turned about 35 degrees to image RIGHT, camera a little above: we see the palm with its mouth, the fingers' inner sides and the thumb |
| `01_front.png` | straight on the PALM (the view of the original sprite), fingers pointing up and a little outward |
| `02_back.png` | straight on the BACK of the hand (knuckles, the backs of the fingers) |
| `03_left.png` | strict 90 degree side view from the thumb side |
| `04_right.png` | strict 90 degree side view from the little-finger side |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as input 3. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Carnage Hand from the 1992 game
Might and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail, a credible fully three-dimensional object.

Identity (from the original frames): a single giant disembodied human RIGHT HAND, about 55 cm from the heel of the
palm to the tip of the middle finger, floating on its own. No wrist and no arm: behind the heel of the palm the hand
simply ends in a smooth, rounded, closed stump of skin (no bone, no blood, no cut). SKIN: warm tan flesh, peach to
light brown, lighter on the finger tips and knuckles, darker tan in the creases. Heavy, powerful, fleshy hand: thick
sausage-like fingers with rounded tips and big knuckles, short blunt nails barely visible, a strong thumb. In the
middle of the PALM a MOUTH about 12 cm wide: a horizontal oval opening with thick dark-red lips, lined all round with
a ring of grey-silver FANGS (an upper and a lower row, long curved canines at both corners), behind them a dark red
gullet with a red tongue. For the 3D reconstruction the mouth is shown CLOSED: the lips meet in a slightly parted
horizontal slit, and only the tips of the grey-silver fangs show between them, overlapping the lips at the corners.

Pose (identical in all five views): the hand open and relaxed, the four fingers spread with clear air gaps between
them and gently curled forward (about 20 degrees at each joint), the thumb spread out to the side, also gently
curled; no finger touches another finger or the palm.

Do NOT: add a wrist, forearm, sleeve, glove, rings, claws, veins that dominate, blood or gore; open the mouth wide;
show lightning or magic effects; make it a cartoon; change the skin colour; crop any finger; draw a floor, a ground
shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole hand inside the frame with margins; a right hand (in the palm view the thumb is on image RIGHT); five thick
fingers, spread and separated; no wrist or arm, a rounded closed end; the closed fanged mouth in the middle of the
palm (visible in 00, 01, 03, 04 as the views allow; 02 shows the plain back of the hand); transparent background;
landscape 1536x1024; for 01-04 the same hand, pose, proportions and colours as the primary; side views strict
profiles. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected views), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the first render) as the primary: warm tan heavy hand, thick separated fingers
gently curled, the thumb spread to image right, the closed dark-red lipped mouth with the fang tips showing in the
middle of the palm, a rounded closed end below the heel. In 01-04 keep exactly this hand: same proportions, finger
spread and curl, skin colour and creases, the same mouth. `01_front`: straight on the palm, fingers up. `02_back`:
straight on the back of the hand, the same finger spread mirrored (thumb on image LEFT), knuckles and the backs of the
fingers, no mouth. `03_left`: strict profile from the thumb side; `04_right`: strict profile from the little-finger
side; in both the palm faces image right or left as the view gives, the lips and fang tips a low bulge on the palm.
Keep at least 60 px between the hand and every edge.
