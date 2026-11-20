# Codex brief: HD modelling references for the MM7 Elf Spearman (m218)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m218_claude/references_hd/` and
`level_generation/creatures/mm7_m218_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing_220_sheet.png` — ORIGINAL native MM7 standing sprite, five stored views left to right:
   front, front three-quarter, his right profile, rear three-quarter, back. Native palette 220 (blue-violet loincloth).
   Magenta is background, not creature. Design, anatomy, proportions and colour authority.
2. `references_native/tiers.png` — the front sprite in the three tier palettes (green, blue-violet, red loincloth).
   Only the loincloth recolours; generate the blue-violet version.
3. `references_native/attack.png` — native attack frames (front and profile): spear, hands and vines detail.
4. `../mm7_m218/aligned_2x/m218sa1.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body head to bare toes, unresized returns, 1024x1536
portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and one side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera |

Prop reference in `references_hd/`: `spear.png`, 1024x1536 portrait, transparent background: the spear ALONE, standing
vertically, tip up, full length inside the frame, seen from the side, no hand.

Head turnaround in `references_head/`, bust only (head with the leaf crown, neck and top of the shoulders), 1254x1254
(or the closest square size), transparent background, same face, hair and leaf sprigs as the body masters, neutral
expression, mouth closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face toward image
right), `03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII Elf Spearman from the supplied original sprites, as a 3D modelling reference. Not a new design. Use case:
faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), semi-realistic game
materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): an adult male woodland elf warrior, tall, slender and lightly muscular, long slim
legs, about 7.5 heads tall. Pale grey-pink skin. Narrow stern angular face, pointed elf ears, dark brown-black hair
swept back to the nape. Two thin branching sprigs of small bright green leaves rise from either side of the head,
forming a small asymmetric leaf crown. Bright green leafy vines (small leaf clusters with yellow-green highlights)
wind diagonally around the bare chest, shoulders, both arms and both legs, sparsely: most of the pale skin stays
visible. A short dark blue-violet loincloth of narrow pointed overlapping fabric tabs hangs front and back from a thin
brown leather waist belt; green vines cross the waist above it. Brown leather forearm bracers on both forearms with
green vine accents. A green vine band below each knee. BARE FEET with five separated toes. A second spear shaft
(plain dark ochre wood, no visible point) is slung diagonally across his back, its upper end above his RIGHT shoulder
and its lower end at his LEFT hip.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs,
EMPTY HANDS (the held spear is a separate prop: do not draw it in the body views). Legs straight, feet shoulder-width
apart with a clear gap between the thighs, soles flat. Head level, looking forward.

Spear (`spear.png` only): a long thin straight dark ochre-brown wooden spear about 2.0 m long (taller than the elf),
shaft about 3 cm thick, a small pale silver leaf-shaped steel point, a short brown leather grip binding at mid-shaft
and a few subtle green vine wraps near the point.

Do NOT: add a shirt, cape, cloak, armour, boots, sandals, jewellery, a bow, a shield, a sword or extra weapons in the
hands; change the colours (pale skin, green vines and leaves, blue-violet loincloth, brown belt and bracers); make the
vines cover the whole body; crop the head, leaf crown, hands or toes; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand and five toes per foot, separated; bare feet; pointed
ears; dark hair; two leaf sprigs on the head; sparse vines with skin visible; blue-violet tabbed loincloth with brown
belt; bracers on both forearms; back shaft from his RIGHT shoulder to his LEFT hip; empty hands; A-pose; transparent
background; for 01–04 the same person, pose and proportions as the primary; side views: in `03_left` his face points to
image left, in `04_right` to image right. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` and `spear.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the
four head views, with the selected primary as an extra input.
