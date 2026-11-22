# Codex brief: HD modelling references for the Witch (World of Xeen, Witch Tower)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_witch_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Wicked Witch / Head Witch** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for
an MM6-8-style first-person RPG. The original game drew her only from the FRONT, as small low-resolution sprites. Your
job is a faithful high-definition reconstruction of that character as a 3D modelling reference, not a new design.

## Inputs (attached in this order)

1. `native/sheet_standing_front.png`: two ORIGINAL standing frames (front view), enlarged 4x with hard pixels. This is
   the identity, proportion and colour authority. The flat grey background is NOT part of the character.
2. `native/sheet_attack.png`: two ORIGINAL casting frames (the green ring is a spell effect: do NOT draw it).
3. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Six images in `references_hd/`, the whole figure inside the frame with at least 60 px of margin on every side,
unresized returns, true transparent background, no floor, no ground shadow, no text:

| File | Canvas | View |
|---|---|---|
| `00_three_quarter.png` | 1024x1536 portrait | the body in A-pose, front three-quarter: the face toward image RIGHT and turned about 35 degrees toward the camera (we see the face and her LEFT side), camera at chest height, slightly above |
| `01_front.png` | 1024x1536 portrait | straight front, symmetric A-pose |
| `02_back.png` | 1024x1536 portrait | straight back |
| `03_left.png` | 1024x1536 portrait | her LEFT side: strict 90 degree profile, the face toward image LEFT |
| `04_right.png` | 1024x1536 portrait | her RIGHT side: strict 90 degree profile, the face toward image RIGHT |
| `05_staff.png` | 1536x1024 landscape | her fork-staff ALONE, lying horizontally, crystal head to image LEFT, prongs to image RIGHT, seen from the side, no hand |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`05` with the selected `00` as input 3. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Witch from the 1992 game Might
and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design. Use case:
3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no dramatic
lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game materials,
sharp fine detail.

Identity (from the original frames): a tall, lean, menacing witch, about 1.8 m. SKIN: pale ash-grey (arms, legs). FACE:
completely covered by an ornate polished GOLD MASK with two tall upswept horn-like points at the top (like a stylised
crown or insect wings), a faceted BLUE GEM set in the middle of the forehead, narrow slanted eye holes with glowing
green eyes, and a dark open mouth slot with small white fangs at the bottom of the mask; under the chin a dark blue
metal collar with round blue rings at the throat. HAIR: a big wild mane of long, tangled WHITE-grey hair around the
mask, falling to the shoulders. CLOTHES: a long blood-RED coat-robe with short sleeves, wide open at the front from
the waist down and reaching the shins, its edges ragged; under it a tight black leather bodice / long black apron
of horizontal BLACK banded panels with thin gold studs, running from under the chest to the knees; a row of three
round BLUE beads across the chest above the bodice; a thin brown leather cord across the chest from the shoulder.
ARMS: bare grey arms. Her RIGHT hand (image left in the front view) is a bare grey hand with FIVE long thin fingers
ending in long pointed BLACK claw nails, a small silver ring-shaped tattoo or eye on the palm; her LEFT hand wears a
black leather gauntlet with a small blue gem on the back. LEGS: grey legs, knee-high brown leather boots with rows of
small black spikes down the back of the shaft, dark soles.

Pose for 00-04 (identical in all five): neutral A-pose standing, arms straight and about 35 degrees from the body,
both hands open with the fingers separated and visible, palms facing forward-down, a small gap between the legs, feet
flat on one level. She holds NOTHING (the staff is drawn separately in 05).

Staff (05 only): a straight staff about 1.4 m long. The HEAD is a faceted glowing MAGENTA crystal held by a dark metal
cap; the shaft is WHITE / ivory with thin RED rings and bands; at the other end a RED-and-black three-pronged FORK
(three long straight dark metal tines, like a pitchfork or trident).

Do NOT: draw the staff in her hands in 00-04; draw any spell effect, glow ring or lightning; add a pointed hat, a
cape, a broom, wings, armour plates, a second mask or extra jewellery; show her real face (the gold mask covers it);
change the colours; crop the hands, the hair or the boots; draw a floor, ground shadow, background or text.

## Per-image checks (re-run before you select a view)

Whole figure inside the frame with margins; gold mask with the two upswept points, the blue forehead gem, green eyes,
fanged mouth slot; white wild hair; red open coat-robe over the black banded bodice/apron; three blue chest beads;
pale grey bare arms and legs; right hand bare with five black-clawed fingers, left hand in a black gauntlet; brown
spiked boots; A-pose with open hands and separated fingers; nothing held; transparent background; for 01-04 the same
character, pose, proportions and colours as the primary; side views: in `03_left` the face points to image LEFT, in
`04_right` to image RIGHT; the front view symmetric (apart from the bare and the gloved hand). Stop after one
corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the six
selected images), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` as the primary (the red wrist wrap on the bare right hand is correct: the
original sprite has it). In 01-05 keep exactly this character: the same gold mask, white mane, red robe with the
ragged hem and the slit showing the grey legs, black banded centre panel with gold studs, three blue beads, brown
leather cord, brown spiked boots, bare clawed right hand with the red wrist wrap, black gauntlet on the left hand.
Same A-pose and proportions. Side views: strict 90 degree profiles; front and back straight on. In `02_back` the
white mane falls over the back of the red robe; no cape. `05_staff`: the staff alone, horizontal, as specified.
Keep at least 60 px of margin and make sure no faint alpha pixels reach the canvas edges.
