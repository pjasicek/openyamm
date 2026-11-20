# Codex brief: HD modelling references for the MM7 Peasant Elf Male (m332)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m332_claude/references_hd/` and
`level_generation/creatures/mm7_m332_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing.png` — ORIGINAL native MM7 standing sprite, five stored views left to right, top row
   left to right: front, front three-quarter, his right profile, rear three-quarter, back. Native palette 59
   (burgundy trousers, blonde hair). The magenta/grey background is not part of the creature. Design, anatomy, proportions and
   colour authority.
2. `references_native/fidget.png` — native fidget frames (front): his hands, vest and belt seen from the front.
3. `references_native/tiers.png` — the front sprite in all nine palettes. Only the trousers and the hair change
   colour; generate the BURGUNDY trousers / BLONDE hair version (palette 59, first image).
4. `../mm7_m332/aligned_2x/m332sa0.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body from the top of the head to the shoe soles, unresized returns,
1024x1536 portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and one side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera |

No prop reference: he carries nothing in his hands (the dagger stays sheathed on the belt).

Head turnaround in `references_head/`, bust only (hair, ponytail, pointed ears, face, neck and top of the shoulders), 1254x1254 (or the
closest square size), transparent background, same face and hair as the body masters, neutral expression, mouth
closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face toward image right),
`03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII peasant elf man (a male elf villager) from the supplied original sprites, as a 3D modelling reference. Not a
new design. Use case: faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft neutral
studio light (no dramatic lighting, no rim light, no strong shadows: the light is baked into the texture),
semi-realistic game materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): an adult male elf villager, tall, lean but muscular (broad shoulders, defined bare
arms), about 7.5 heads tall. Fair skin, angular face, clean-shaven, long pointed elf ears. Pale golden-blonde hair
combed back from the forehead and tied into a ponytail that hangs down the back to the shoulder blades. A sleeveless
dark brown leather vest, open in a deep V over the bare chest and laced across with leather thongs, with two rows of
round brass studs down the front, its shoulders slightly darker. Brown leather wrist bracers on both forearms. A
brass/gold belt with a dark leather backing at the waist; a sheathed dagger (dark leather sheath with brass fittings,
the grip up) hangs from the belt on his RIGHT hip. Tight burgundy-red trousers (hose) down to the ankles, plain brown
leather shoes.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs,
EMPTY HANDS. Legs straight, feet shoulder-width apart with a clear gap between the legs, soles flat. Head level,
looking forward.

Do NOT: add a shirt under the vest, sleeves, a cloak, a hat, armour, a bow or a weapon in the hands; draw the dagger out
of its sheath; change the colours (blonde hair, brown leather vest with brass studs, burgundy trousers, brass belt,
brown shoes); make him stocky; crop the head, hands or shoes; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand, separated; blonde hair with a ponytail down the back;
pointed ears; sleeveless laced brown vest with brass studs over the bare chest; bare arms with bracers; brass belt with
the sheathed dagger on his right hip; burgundy tights; brown shoes; lean tall elf proportions; empty hands; A-pose;
transparent background; for 01–04 the same elf, pose and proportions as the primary; side views: in `03_left` his face
points to image left, in `04_right` to image right.
Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the
four head views, with the selected primary as an extra input.
