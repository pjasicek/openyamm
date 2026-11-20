# Codex brief: HD modelling references for the MM7 Peasant Goblin Male (7m452)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_7m452_claude/references_hd/` and
`level_generation/creatures/mm7_7m452_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing.png` — ORIGINAL native MM7 standing sprite, five stored views left to right, top row
   then bottom row: front, front three-quarter, his right profile, rear three-quarter, back. Native palette 497 (red
   tunic, blue-grey trousers, grey topknot). The magenta/grey background is not part of the creature. Design, anatomy, proportions and
   colour authority.
2. `references_native/fidget.png` — native fidget frames (front): his hands, the tunic and the billhook seen from the front.
3. `references_native/tiers.png` — the front sprite in all nine palettes. Only the tunic, the trousers and the topknot change
   colour; the green skin never changes; generate the RED tunic / BLUE-GREY trousers / GREY topknot version (palette 497,
   first image).
4. `../mm7_7m452/aligned_2x/7m452sa0.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body from the topknot tip to the boot soles, unresized returns,
1024x1536 portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and one side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera |

Prop reference in `references_hd/`: `billhook.png`, 1024x1536 portrait, transparent background: the billhook ALONE,
standing vertically, blade up, full length inside the frame, seen flat from the side (the hook curving to one side),
no hand.

Head turnaround in `references_head/`, bust only (bald head with the topknot, ears, face, neck and top of the shoulders with the fur trim), 1254x1254 (or the
closest square size), transparent background, same face, ears and topknot as the body masters, neutral expression, mouth
closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face toward image right),
`03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII peasant goblin man (a male goblin villager) from the supplied original sprites, as a 3D modelling reference.
Not a new design. Use case: faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft
neutral studio light (no dramatic lighting, no rim light, no strong shadows: the light is baked into the texture),
semi-realistic game materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): an adult male goblin villager of MM7 (an orc-like humanoid, NOT a small cartoon
goblin): tall, broad-shouldered and muscular, about 7.5 heads tall, smooth yellow-green skin over the whole body.
A bald head with a single grey topknot (a short tied tuft of hair) on the crown, pointed ears close to the head,
a heavy brow, a broad flat nose, a wide mouth with a strong jaw, no tusks, clean-shaven. A sleeveless knee-short
tunic of red cloth with a darker red woven ornament pattern, open at the sides below the belt, with a pale grey shaggy
fur trim along the shoulder straps and along the hem. A brown leather belt with a brass buckle. Brown leather wrist
bracers with brass studs on both forearms, bare muscular arms. Close-fitting blue-grey trousers with thin darker
vertical stripes, tucked into tall brown leather boots that reach just below the knee.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs,
EMPTY HANDS (the billhook is a separate prop: do not draw it in the body views). Legs straight, feet shoulder-width
apart with a clear gap between the legs, soles flat. Head level, looking forward.

Billhook (`billhook.png` only): a peasant's long billhook / hook-bladed polearm about 1.4 m long: a straight pale
brown wooden shaft, at the top a long dull grey iron blade with a large curved hook bent back at its tip, a small
spur on the back of the blade, bound to the shaft with a short iron socket.

Do NOT: add armour, a helmet, a cape, tusks, a beard, hair other than the topknot, a weapon in the hands; change the
colours (green skin, red tunic, grey fur, blue-grey striped trousers, brown leather, grey topknot); make him small or
stocky; crop the topknot, hands or boots; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand, separated; green skin everywhere; bald head with a
grey topknot; red patterned sleeveless tunic with grey fur trim; belt; bracers on both forearms; blue-grey striped
trousers; tall brown boots; tall muscular proportions; empty hands; A-pose; transparent background; for 01–04 the
same goblin, pose and proportions as the primary; side views: in `03_left` his face points to image left, in
`04_right` to image right.
Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` and `billhook.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the
four head views, with the selected primary as an extra input.
