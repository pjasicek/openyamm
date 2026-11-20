# Codex brief: HD modelling references for the MM7 Elf Archer (m214)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m214_claude/references_hd/` and
`level_generation/creatures/mm7_m214_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing_216_sheet.png` — ORIGINAL native MM7 standing sprite, five stored views left to right:
   front, front three-quarter, her right profile, rear three-quarter, back. Native palette 216 (green garments, silver
   hair). Magenta is background, not creature. Design, anatomy, proportions and colour authority.
2. `references_native/tiers.png` — the same front sprite in the three tier palettes (olive/blond, green/silver,
   red/brown). Only shows which parts recolour (garments, hair); generate the green/silver version.
3. `references_native/attack.png` — native attack frames (front and profile): bow, string, arrows and quiver detail.
4. `../mm7_m214/aligned_2x/m214sa1.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body head to bare toes, unresized returns, 1024x1536
portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, her body turned about 35° toward image left (we see her front and her right side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | her LEFT side: she faces image LEFT, her left shoulder is nearest the camera |
| `04_right.png` | her RIGHT side: she faces image RIGHT, her right shoulder is nearest the camera |

Prop reference in `references_hd/`: `bow.png`, 1024x1536 portrait, transparent background: the archer's bow ALONE,
standing vertically, seen square-on from the side so the full recurve profile and the string are visible, string on
the image-left side. No hand, no arrow.

Head turnaround in `references_head/`, bust only (head, neck and top of the shoulders, cut below the collarbones),
1254x1254 (or the closest square size your tool returns), transparent background, same face and hair as the body
masters, neutral expression, mouth closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (her right side,
face toward image right), `03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII Elf Archer from the supplied original sprites, as a 3D modelling reference. Not a new design. Use case:
faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), semi-realistic game
materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): an adult female elf archer, tall slender athletic build with long slim legs,
narrow waist, about 7.5 heads tall. Pale pink-beige skin. Stern narrow face, high cheekbones, pointed elf ears
visible through the hair. Short straight silver-white hair close to the head, swept back, reaching the nape.
A dark leaf-green fitted sleeveless leather vest with narrow ivory-white piping along every edge, a high collar at the
back of the neck, the front closed over the chest in a modest deep V neckline, the vest ending below the chest with
two slim horizontal brown leather straps with small buckles across the lower ribs; a small bare midriff below.
Matching dark green close-fitting cropped trousers ending at mid-calf, ivory piping at the low waistband, a small
leather pouch and a thin dark thigh strap on her right thigh, brown criss-cross lacing on the outer lower calves.
BARE FEET with five clearly separated toes, no boots, no sandals. A brown leather bracer on the left forearm (the bow
arm). A long narrow brown leather quiver worn diagonally across the back, top behind her RIGHT shoulder, bottom at the
left hip, with a gold-brown wound ornament along it and small red studs; a bundle of pale grey-white arrow fletchings
sticks out above the right shoulder. A thin diagonal quiver strap crosses the front of the chest from right shoulder
to left hip.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs,
EMPTY HANDS (the bow is a separate prop: do not draw it in the body views). Legs straight, feet shoulder-width apart
with a clear gap between the thighs, soles flat. Head level, looking forward.

Bow (`bow.png` only): a thin dark-brown wooden recurved bow about as tall as her shoulder height (about 1.3 m),
narrow gold metal bands near the grip and limb tips, a leather-wrapped grip, sharply recurved pointed tips, a fine
pale taut string.

Do NOT: add a cape, cloak, armour, boots, gloves, jewellery, a second weapon, a sword or dagger, a bow in the body
views; change the green/ivory/brown colours or the silver hair; make the hair long; crop the head, hands, quiver or
toes; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand and five toes per foot, separated; bare feet; pointed
ears; short silver hair; ivory piping on vest and trousers; two waist straps; quiver diagonal on the back, fletchings
above her RIGHT shoulder; bracer on her LEFT forearm; empty hands; A-pose; transparent background; for 01–04 the same
person, pose and proportions as the primary; side views: in `03_left` her face points to image left, in `04_right`
to image right, and the quiver top sits behind the shoulder on the correct side. Stop after one corrective
regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` and `bow.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the
four head views, with the selected primary as an extra input.
