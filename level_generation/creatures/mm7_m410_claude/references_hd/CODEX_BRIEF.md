# Codex brief: HD modelling references for the MM7 Thief (m410)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m410_claude/references_hd/` and
`level_generation/creatures/mm7_m410_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing_84_sheet.png` — ORIGINAL native MM7 standing sprite, five stored views left to right:
   front, front three-quarter, his right profile, rear three-quarter, back. Native palette 84 (purple vest and cap,
   green trousers). Magenta is background, not creature. Design, anatomy, proportions and colour authority.
2. `references_native/tiers.png` — the front sprite in the three tier palettes (purple/green, green/orange, red/red).
   Only the vest, cap and trousers recolour; generate the PURPLE vest / GREEN trousers version.
3. `references_native/attack.png` — native attack frames (front and profile): the dagger drawn from the left hip.
4. `../mm7_m410/aligned_2x/m410sa0.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body head to boot soles, unresized returns, 1024x1536
portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and one side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera |

Prop reference in `references_hd/`: `dagger.png`, 1024x1536 portrait, transparent background: the dagger ALONE,
standing vertically, point up, full length inside the frame, seen flat from the side, no hand, no sheath.

Head turnaround in `references_head/`, bust only (cap, masked face, neck and top of the shoulders), 1254x1254 (or the
closest square size), transparent background, same face, cap and mask as the body masters, neutral expression:
`01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face toward image right), `03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII Thief from the supplied original sprites, as a 3D modelling reference. Not a new design. Use case: faithful
3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no dramatic
lighting, no rim light, no strong shadows: the light is baked into the texture), semi-realistic game materials, sharp
fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): an adult male human thief, lean and athletic, average height, about 7.5 heads tall.
Pale grey-pink skin. A snug dark purple knitted cap pulled down to the brows; a dark red cloth mask covering the nose,
mouth and chin, the eyes visible. A sleeveless dark purple quilted leather vest studded with small round silver rivets,
closed down the front, with rounded padded purple shoulder caps. Bare arms. Several thin gold bangles on the left wrist,
a brown leather wristband on the right wrist. A brown leather belt with a small square buckle; a grey cloth coin pouch
hangs on his RIGHT hip; an EMPTY plain brown leather dagger sheath (no dagger in it) hangs on his LEFT hip, angled
slightly forward. Snug dark green leather trousers. Tall brown leather boots to just below the knee, laced at the front.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs,
EMPTY HANDS (the dagger is a separate prop: do not draw it). Legs straight, feet shoulder-width apart with a clear gap
between the thighs, soles flat. Head level, looking forward.

Dagger (`dagger.png` only): a plain steel dagger about 35 cm long: a straight double-edged pale silver blade of about
22 cm, a short dark iron crossguard, a brown leather-wrapped grip and a small round iron pommel.

Do NOT: add a cloak, cape, hood, sleeves, gloves, a shield, a sword, a bow, a dagger in the hand or in the sheath, extra
pouches or weapons; change the colours (purple vest and cap, red mask, green trousers, brown belt, sheath and boots,
gold bangles); crop the cap, hands or boots; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand, separated; purple cap and red mask; studded purple
vest with rounded shoulder caps; bare arms; gold bangles on the LEFT wrist, leather band on the RIGHT wrist; pouch on
the RIGHT hip, empty sheath on the LEFT hip; green trousers; tall brown boots; empty hands; A-pose; transparent
background; for 01–04 the same person, pose and proportions as the primary; side views: in `03_left` his face points to
image left, in `04_right` to image right. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` and `dagger.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and
the four head views, with the selected primary as an extra input.
