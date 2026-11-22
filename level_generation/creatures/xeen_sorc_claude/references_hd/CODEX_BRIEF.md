# Codex brief: HD modelling references for the Sorceress (World of Xeen, Clouds image 31)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_sorc_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Sorceress** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew her only from the FRONT, as small low-resolution sprites. Your job is a
faithful high-definition reconstruction of that character as a 3D modelling reference, not a new design.

## Inputs (attached in this order)

1. `native/sheet_standing_front.png`: two ORIGINAL standing frames (front view), enlarged 4x with hard pixels. This is
   the identity, proportion and colour authority. The flat grey background is NOT part of the character. The green
   swirls and sparks around her hands are a spell effect: do NOT draw them.
2. `native/sheet_attack.png`: three ORIGINAL casting frames (the round bubbles round her hands are a spell effect: do
   NOT draw them). They show her bare face and arms more clearly.
3. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five images in `references_hd/`, 1024x1536 portrait, the whole figure inside the frame with at least 60 px of margin
on every side, unresized returns, true transparent background, no floor, no ground shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | the body in A-pose, front three-quarter: the face toward image RIGHT and turned about 35 degrees toward the camera (we see the face and her LEFT side), camera at chest height, slightly above |
| `01_front.png` | straight front, symmetric A-pose |
| `02_back.png` | straight back |
| `03_left.png` | her LEFT side: strict 90 degree profile, the face toward image LEFT |
| `04_right.png` | her RIGHT side: strict 90 degree profile, the face toward image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as input 3. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Sorceress from the 1992 game Might
and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design. Use case:
3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no dramatic
lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game materials,
sharp fine detail. Tasteful heroic-fantasy costume as in the original, non-sexualised presentation, neutral stance.

Identity (from the original frames): a tall, strong, athletic adult woman, about 1.75 m, warm medium-brown skin. HAIR:
a big voluminous mane of tight black curls with deep PURPLE highlights, falling to the shoulders, framing the face.
HEAD: a thin gold circlet across the forehead with a round GREEN gem in the middle; glowing bright GREEN eyes; dark
eyebrows; red lips. EARRINGS: a small RED drop earring on her right ear, a small white pearl on her left ear.
NECK: a dark choker necklace with a small green gem and a little gold crescent pendant on the breastbone.
TOP: a WHITE cloth halter top (two wide triangular cups, fully covering, white straps over the shoulders), with
small curved WHITE shoulder guards (stiff leather or cloth caps) on top of both shoulders. MIDRIFF bare.
BELT: a low silver-grey jewelled girdle round the hips set with small GREEN gems and dark studs, a large round GREEN
gem on a gold mount at the front centre.
LOINCLOTH: from the belt hangs a long WHITE cloth panel at the front, knee length, straight-cut with soft folds, and a
shorter white panel at the back; the hips and outer thighs are bare between the panels.
GLOVES: BLACK leather opera gloves to just below the elbows, flared at the cuffs, five slender fingers each.
BOOTS: BLACK leather thigh-high boots reaching mid-thigh, with a small dark-brown turned cuff at the top, low heels,
brown soles.

Pose for 00-04 (identical in all five): neutral A-pose standing, arms straight and about 35 degrees from the body,
both hands open with the fingers separated and visible, palms facing forward-down, a small gap between the legs (not
the original's wide fighting stance), feet flat on one level. She holds nothing.

Do NOT: draw any spell effect, glow, swirl, bubble or sparks; add a staff, wand, cape, hat, robe, sleeves, armour
plates or extra jewellery; change the colours (white top and loincloth, black gloves and boots, green gems, purple-black
hair); crop the hands, the hair or the boots; draw a floor, ground shadow, background or text.

## Per-image checks (re-run before you select a view)

Whole figure inside the frame with margins; voluminous purple-black curly hair; gold circlet with the green gem; green
eyes; red and white earrings on the correct sides; white halter top and white shoulder guards; bare midriff; jewelled
girdle with the big green front gem; long white front panel; black elbow gloves with five fingers each; black
thigh-high boots; A-pose with open hands and separated fingers; nothing held; transparent background; for 01-04 the
same character, pose, proportions and colours as the primary; side views: in `03_left` the face points to image LEFT,
in `04_right` to image RIGHT; the front view symmetric. Stop after one corrective regeneration per view and record what
remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected images), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` as the primary. In 01-04 keep exactly this character: the same purple-black
curly mane, gold circlet with the green gem, green eyes, red drop earring on her right ear and pearl on her left, black
choker with the green gem and gold crescent, white halter top with the white shoulder caps and gold rivets, the
silver-grey girdle with green gems, dark studs and the big green front gem, the long white front panel (and a shorter
white back panel), black flared elbow gloves, black thigh-high boots with the brown turned cuffs. Same A-pose,
proportions and muscular build. Side views: strict 90 degree profiles; front and back straight on. In `02_back` the
curly mane falls to the shoulder blades; the halter ties and a short white back panel show. Keep at least 60 px of
margin and make sure no faint alpha pixels reach the canvas edges.
