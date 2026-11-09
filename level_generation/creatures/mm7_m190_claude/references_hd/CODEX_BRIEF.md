# Codex brief: HD modelling references for the MM7 Dwarf warrior (m190)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m190_claude/references_hd/` and
`level_generation/creatures/mm7_m190_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing_191_sheet.png` — ORIGINAL native MM7 standing sprite, five stored views left to right:
   front, front three-quarter, his right profile, rear three-quarter, back. Native palette 191 (dark green cloth).
   Magenta is background, not creature. Design, anatomy, proportions and colour authority.
2. `references_native/tiers.png` — the front sprite in the three tier palettes (green, blue-violet, muted red cloth).
   Only the cloth recolours; generate the GREEN version.
3. `references_native/attack.png` — native attack frames (front and profile): the axe, hands, gauntlets and boots.
4. `../mm7_m190/aligned_2x/m190sa0.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body from the helmet horns to the boot soles, unresized
returns, 1024x1536 portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and one side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera |

Prop reference in `references_hd/`: `axe.png`, 1024x1536 portrait, transparent background: the axe ALONE, standing
vertically, head up, full length inside the frame, seen flat from the side (both blades visible left and right of the
haft), no hand.

Head turnaround in `references_head/`, bust only (helmet with horns, face, beard, neck and top of the shoulders),
1254x1254 (or the closest square size), transparent background, same face, helmet and beard as the body masters,
neutral expression, mouth closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face toward
image right), `03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII Dwarf warrior from the supplied original sprites, as a 3D modelling reference. Not a new design. Use case:
faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), semi-realistic game
materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): an adult male dwarf warrior, short, broad and stocky, barrel chest, thick heavily
muscled arms, short sturdy legs, large hands, about 4 heads tall. Ruddy tanned skin. A round dark steel helmet with a
gold rim band, two large curved ivory horns rising from its sides and a short pointed steel spike on top; the face below
it is visible: heavy brows, broad nose. A very long full ginger-brown beard reaching the belt, braided at the sides,
and a moustache; brown hair falls to the shoulders behind. Sleeveless dark steel chainmail shirt with rounded steel
pauldron-like shoulders, a dark green cloth collar / mantle around the neck and shoulders. Brown leather belt with a
gold buckle. Below it a knee-length skirt of fine silver chainmail over a dark green cloth skirt with a ragged pointed
hem. Bare muscular upper arms, thick brown leather forearm bracers with gold rims. Gold rings / bands at the knees, dark
steel greaves and heavy dark steel boots with gold trim.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs,
EMPTY HANDS (the held axe is a separate prop: do not draw it in the body views). Legs straight, feet shoulder-width
apart with a clear gap between the legs below the skirt, soles flat. Head level, looking forward. The beard hangs
straight down in front of the chest, not covering the arms.

Axe (`axe.png` only): a one-handed double-bitted battle axe about 0.8 m long (as long as the dwarf's legs and torso):
a straight brown wooden haft with gold bands and a gold pommel knob, a short brown leather grip near the bottom, and a
pale silver steel double crescent head (two curved blades back to back) with a gold collar and a short spike on top.

Do NOT: add a cape, a shield, a second weapon or a weapon in the hands; change the colours (ruddy skin, ginger-brown
beard, dark steel and silver mail, green cloth, brown leather, gold trim, ivory horns); make him tall or slim; crop the
horns, hands or boots; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand, separated; two ivory horns and a top spike on the
helmet; long ginger beard to the belt; green collar and green ragged skirt under silver mail; bracers on both forearms;
dark steel boots; stocky dwarf proportions; empty hands; A-pose; transparent background; for 01–04 the same dwarf,
pose and proportions as the primary; side views: in `03_left` his face points to image left, in `04_right` to image
right. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` and `axe.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the
four head views, with the selected primary as an extra input.
