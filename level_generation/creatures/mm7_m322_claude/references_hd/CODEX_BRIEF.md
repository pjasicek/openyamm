# Codex brief: HD modelling references for the MM7 Peasant Elf Female (m322)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m322_claude/references_hd/` and
`level_generation/creatures/mm7_m322_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing.png` — ORIGINAL native MM7 standing sprite, five stored views left to right, top row
   left to right: front, front three-quarter, her right profile, rear three-quarter, back. Native palette 323
   (green trousers, chestnut-red hair). The magenta/grey background is not part of the creature. Design, anatomy, proportions and
   colour authority.
2. `references_native/fidget.png` — native fidget frames (front): her hands, vest and the staff seen from the front.
3. `references_native/tiers.png` — the front sprite in all nine palettes. Only the trousers and the hair change
   colour; generate the GREEN trousers / CHESTNUT-RED hair version (palette 323, first image).
4. `../mm7_m322/aligned_2x/m322sa0.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body from the top of the head to the shoe soles, unresized returns,
1024x1536 portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see her front and one side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | her LEFT side: she faces image LEFT, her left shoulder nearest the camera |
| `04_right.png` | her RIGHT side: she faces image RIGHT, her right shoulder nearest the camera |

Prop reference in `references_hd/`: `staff.png`, 1024x1536 portrait, transparent background: the staff ALONE, standing
vertically, full length inside the frame, seen from the side, no hand.

Head turnaround in `references_head/`, bust only (long hair, pointed ears, face, neck and top of the shoulders), 1254x1254 (or the
closest square size), transparent background, same face and hair as the body masters, neutral expression, mouth
closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (her right side, face toward image right),
`03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII peasant elf woman (a female elf villager) from the supplied original sprites, as a 3D modelling reference.
Not a new design. Use case: faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft
neutral studio light (no dramatic lighting, no rim light, no strong shadows: the light is baked into the texture),
semi-realistic game materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): an adult female elf villager, tall and slender with an athletic build, about 7.5
heads tall. Fair skin, fine features, long pointed elf ears. Long straight chestnut-red hair parted in the middle,
falling over the shoulders and down the back to the shoulder blades. A short dark brown leather corset-vest laced
across the front with leather thongs (deep neckline), ending above the navel: bare midriff. Bare arms; long dark brown
leather bracers from the wrist to below the elbow. Tight green trousers with a laced front fly and, down the outer side
of each leg, an open criss-cross leather lacing that shows a strip of skin. Brown leather ankle boots.

Staff (`staff.png` only): a crooked, knobbly natural wooden walking staff of dark reddish-brown bark, as tall as her
shoulder (about 1.4 m), slightly wavy along its length, thicker at the top end, no ornaments.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs,
EMPTY HANDS (the staff she carries is a separate prop: do not draw it in the body views). Legs straight, feet
shoulder-width apart with a clear gap between the legs, soles flat. Head level, looking forward. The hair hangs behind
the shoulders, not over the arms.

Do NOT: add a shirt, sleeves, a cloak, a hat, jewellery, armour or anything in the hands; change the colours
(chestnut-red hair, dark brown leather vest and bracers, green trousers, brown boots); make her stocky; crop the head,
hands or boots; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand, separated; long straight chestnut-red hair behind the
shoulders; pointed ears; short laced brown corset-vest with bare midriff; bare arms with long brown bracers; green
trousers with the front lacing and the side lacing down the outer legs; brown ankle boots; slender tall elf
proportions; empty hands; A-pose; transparent background; for 01–04 the same elf, pose and proportions as the primary;
side views: in `03_left` her face points to image left, in `04_right` to image right.
Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` and `staff.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the
four head views, with the selected primary as an extra input.
