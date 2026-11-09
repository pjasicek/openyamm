# Codex brief: HD modelling references for the MM7 Golem (m254)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m254_claude/references_hd/` and
`level_generation/creatures/mm7_m254_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references/standing_255_sheet.png` — ORIGINAL native MM7 standing sprite, five stored views left to right:
   front, front three-quarter, his right profile (he faces image right), rear three-quarter, back. Native palette 255
   (green stripes). Magenta is background, not creature. Design, anatomy, proportions and colour authority.
2. `references/tiers.png` — the front sprite in the three tier palettes (green, blue/cyan, red/tan stripes). Generate
   the GREEN version (left).
3. `references/attack_front.png` — native attack frames (front): arms raised overhead with open hands, fists, the
   headdress, horns and collar from other angles.
4. `../mm7_m254/aligned_2x/m254sa0.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body from the horn tips and crown top to the soles,
unresized returns, 1024x1536 portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and his right side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera |

Head turnaround in `references_head/`, bust only (headdress with crown and horns, face, false beard, neck and the top
of the collar), 1254x1254 (or the closest square size), transparent background, same face and headdress as the body
masters, neutral expression, mouth closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side,
face toward image right), `03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII Golem from the supplied original sprites, as a 3D modelling reference. Not a new design. Use case: faithful
3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no dramatic
lighting, no rim light, no strong highlights or reflections of an environment, no strong shadows: the light is baked
into the texture), semi-realistic game materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): a living statue of polished GOLD-BRONZE metal in the form of a huge, heavily
muscular Egyptian pharaoh-warrior (heroic proportions, about 7.5 heads tall: very broad shoulders, big arms, thick
thighs and calves, sculpted abdominal muscles). The whole body, face, hands and bare feet are one smooth cast metal
surface of warm gold-bronze (a statue, no human skin, no hair on the body). A stern, calm Egyptian face cast in the
same gold metal, clean-shaven apart from a straight cylindrical FALSE BEARD under the chin with horizontal GREEN
stripes. On the head a NEMES headdress of GREEN cloth with dark-green and light-green horizontal stripes and thin gold
edging: the two front lappets fall behind the ears to the collar on both sides of the face, the back flares down to
the shoulders. On top of it a short cylindrical CROWN (modius) with green stripes and gold rims, and a pair of short,
curved IVORY-WHITE HORNS rising from the sides of the crown. Around the neck a wide, heavy, dark near-black bronze
BROAD COLLAR covering the shoulders, upper chest and upper back, with a rough dark texture and a row of round gold
studs along its edges. Thick BLACK metal cuffs on both wrists and both ankles. A LOINCLOTH (shendyt): a green-striped
belt band, a front apron panel with horizontal dark-green and light-green stripes hanging to mid-thigh, the same
striped panel at the back, and dark black briefs at the hips between the panels. Bare metal feet with toes.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs.
Legs straight, feet shoulder-width apart with a clear gap between the thighs, soles flat. Head level, looking forward.

Do NOT: add a weapon, shield, cape, jewellery, armour plates, robot joints or visible seams/rivets on the body; turn
the body into stone, a robot or a human with skin; change the colours (gold-bronze body, green-striped headdress,
beard and loincloth, black cuffs, dark studded collar, ivory horns); make him slim; crop the horns, hands or feet;
draw a floor, shadow, reflection or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand, separated; gold-bronze metal body; green-striped
nemes, crown with two ivory horns, striped false beard; dark studded broad collar; black cuffs on both wrists and both
ankles; striped front and back loincloth panels; heroic proportions; A-pose; transparent background; for 01–04 the
same figure, pose and proportions as the primary; side views: in `03_left` his face points to image left, in
`04_right` to image right. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side (and
`references_head/selected_views_review.png` for the head).

## Runs

Run 1: `00_three_quarter.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the four head
views, with the selected primary as an extra input.
