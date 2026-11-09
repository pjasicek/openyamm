# Codex brief: HD modelling references for the MM7 Minotaur (m286)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m286_claude/references_hd/` and
`level_generation/creatures/mm7_m286_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing_287_sheet.png` — ORIGINAL native MM7 standing sprite, five stored views left to right:
   front, front three-quarter, his right profile, rear three-quarter, back. Native palette 287 (olive-green fur cloth).
   Magenta is background, not creature. Design, anatomy, proportions and colour authority.
2. `references_native/tiers.png` — the front sprite in the three tier palettes (olive green, teal, red loincloth and
   wrist bands). Only the loincloth and wrist bands recolour; generate the OLIVE-GREEN version.
3. `references_native/axe_frames.png` — native frames enlarged (profile, three-quarter, attack): the axe, the hands,
   the wrist bands, the legs and hooves. Magenta is background.
4. `../mm7_m286/aligned_2x/m286sa1.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body from the horn tips to the hooves, unresized returns,
1024x1536 portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and one side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera |

Prop reference in `references_hd/`: `axe.png`, 1024x1536 portrait, transparent background: the axe ALONE, standing
vertically, head up, full length inside the frame, seen flat from the side (both crescent blades visible left and right
of the haft), no hand.

Head turnaround in `references_head/` (second run), bust only (horns, head, mane, neck and top of the shoulders),
1254x1254 (or the closest square size), transparent background, same head, horns, nose ring and mane as the body
masters, mouth closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face toward image
right), `03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII Minotaur from the supplied original sprites, as a 3D modelling reference. Not a new design. Use case:
faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), semi-realistic game
materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): a tall, heavily muscled bull-headed humanoid. Human-shaped muscular torso and arms
with short grey-brown skin/hide (defined pecs and abdominal muscles, not furry on the chest), broad shoulders. Bull head:
dark brown short-haired bovine head with a broad muzzle, a black nose with a GOLD nose ring, glowing RED eyes, small
bovine ears, and exactly TWO very large smooth pale ivory-grey horns that sweep sideways and curve upward, ending in
dark RED tips. A long shaggy dark-brown mane runs from the back of the head down the neck and the upper back. Hands are
human with four fingers and a thumb, dark grey-brown, short dark nails. **Goat (satyr) legs**: from the hips down the
legs are covered in long shaggy dark-brown fur, with the animal joint structure seen in the profile frames — the knee
bends forward, then a backward-bent hock high above the ground, a long slender lower leg, and a black cloven HOOF on
each foot (two toe halves); NO human feet, NO boots. A loincloth / short kilt of shaggy OLIVE-GREEN fur with a ragged
hem around the hips (to mid-thigh), held by a narrow gold belt studded with small blue-and-gold beads. On each forearm
a wide OLIVE-GREEN padded wrist band with gold rims and three or four short pointed silver spikes sticking outward.
No other clothing, no harness, no chest armour, no tail.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs,
EMPTY HANDS (the held axe is a separate prop: do not draw it in the body views). Legs standing straight but with their
natural goat-leg knee and hock bends, hooves flat on an imaginary floor about shoulder width apart, a clear gap
between the legs. Head level, looking forward. Horns fully inside the frame.

Axe (`axe.png` only): a long two-handed-length but one-hand-carried double-bitted battle axe about 1.6 m long (as tall
as the minotaur's shoulder): a straight dark bronze-brown haft wrapped with a spiral of lighter copper bands, a round
copper pommel knob at the bottom with a short grip, and at the top a large double head of two broad CRESCENT blades
back to back (each blade a deep curved half-moon, pale pinkish polished copper-steel), a small copper collar between
them and a short pointed spike on top.

Do NOT: add a cape, armour, a harness, a shield, a second weapon or a weapon in the hands; give him human feet or boots;
add a tail; change the colours (grey-brown skin, dark-brown fur legs and mane, olive-green fur loincloth and wrist
bands, gold belt with blue beads, gold nose ring, ivory horns with red tips, red eyes, black hooves); crop the horns,
hands or hooves; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand, separated; exactly two horns with red tips; gold
nose ring; red eyes; mane down the neck; goat legs with forward knee, backward hock and black cloven hooves (no human
feet); olive-green fur loincloth; gold beaded belt; green spiked wrist bands on BOTH forearms; empty hands; A-pose;
transparent background; for 01–04 the same minotaur, pose and proportions as the primary; side views: in `03_left` his
face points to image left, in `04_right` to image right. Stop after one corrective regeneration per view and record
what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` and `axe.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the
four head views, with the selected primary as an extra input.
