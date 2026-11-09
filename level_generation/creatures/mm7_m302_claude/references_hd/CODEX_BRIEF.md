# Codex brief: HD modelling references for the MM7 Peasant Dwarf Male (m302)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m302_claude/references_hd/` and
`level_generation/creatures/mm7_m302_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing.png` — ORIGINAL native MM7 standing sprite, five stored views left to right, top row
   then bottom row: front, front three-quarter, his right profile, rear three-quarter, back. Native palette 58 (green
   cloth, brown beard). The magenta/grey background is not part of the creature. Design, anatomy, proportions and
   colour authority.
2. `references_native/fidget.png` — native fidget frames (front): his hands, the beard and the club seen from the front.
3. `references_native/tiers.png` — the front sprite in all nine palettes. Only the cap/shirt cloth and the hair/beard
   change colour; generate the GREEN cloth / BROWN beard version (palette 58, first image).
4. `../mm7_m302/aligned_2x/m302sa0.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body from the cap tip to the boot soles, unresized returns,
1024x1536 portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and one side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera |

Prop reference in `references_hd/`: `club.png`, 1024x1536 portrait, transparent background: the club ALONE, standing
vertically, thick knobbly head up, full length inside the frame, seen from the side, no hand.

Head turnaround in `references_head/`, bust only (cap, face, beard, neck and top of the shoulders), 1254x1254 (or the
closest square size), transparent background, same face, cap and beard as the body masters, neutral expression, mouth
closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face toward image right),
`03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII peasant dwarf (a male dwarf villager) from the supplied original sprites, as a 3D modelling reference. Not a
new design. Use case: faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft neutral
studio light (no dramatic lighting, no rim light, no strong shadows: the light is baked into the texture),
semi-realistic game materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): an adult male dwarf villager, short, broad and stocky, thick arms, big hands, short
sturdy legs, about 4 heads tall. Fair ruddy skin, heavy brows, broad nose. A soft green knitted stocking cap that sits
snug on the head and whose long tip folds over and hangs down at the back of the head. A very long full straight brown
beard and moustache reaching the belt, brown hair at the nape. A long-sleeved green shirt (loose sleeves) under a brown
leather vest whose edges, armholes and bottom hem are trimmed with thick cream-white fleece. A green shirt band shows
between the vest and a brown leather belt with silver rivets and a round silver buckle. Brown leather forearm bracers
over the sleeves at the wrists. Loose beige-grey woollen trousers to below the knee, thick cream-white fleece cuffs
around the tops of the boots, tall brown leather boots.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs,
EMPTY HANDS (the held club is a separate prop: do not draw it in the body views). Legs straight, feet shoulder-width
apart with a clear gap between the legs, soles flat. Head level, looking forward. The beard hangs straight down in
front of the chest, not covering the arms.

Club (`club.png` only): a crude wooden cudgel about 0.6 m long (from his hand to below his knee): a gnarled brown
branch, thin round grip at the bottom widening to a heavy knobbly bulbous head with knots and bark texture.

Do NOT: add a hood, cape, armour, helmet, a weapon or tool in the hands; change the colours (green cap and shirt, brown
beard, brown leather vest, cream fleece trim, beige trousers, brown boots); make him tall or slim; crop the cap, hands
or boots; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand, separated; green stocking cap with its tip hanging
at the back; long brown beard to the belt; green sleeves; brown vest with cream fleece trim; beige trousers; fleece
boot cuffs; stocky dwarf proportions; empty hands; A-pose; transparent background; for 01–04 the same dwarf, pose and
proportions as the primary; side views: in `03_left` his face points to image left, in `04_right` to image right.
Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` and `club.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the
four head views, with the selected primary as an extra input.
