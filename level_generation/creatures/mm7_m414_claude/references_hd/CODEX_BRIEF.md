# Codex brief: HD modelling references for the MM7 Titan (m414)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m414_claude/references_hd/` and
`level_generation/creatures/mm7_m414_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing_91_sheet.png` — ORIGINAL native MM7 standing sprite, five stored views left to right:
   front, front three-quarter, his right profile, rear three-quarter, back. Native palette 91 (dark blue tunic).
   Magenta is background, not creature. Design, anatomy, proportions and colour authority.
2. `references_native/tiers.png` — the front sprite in the three tier palettes (blue, olive, red tunic; white, orange,
   pink crest). Generate the BLUE tunic / WHITE crest version.
3. `references_native/attack.png` — native attack frames (front and profile): the sword, helmet crest and armour.
4. `../mm7_m414/aligned_2x/m414sa0.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body from the crest top to the sandal soles, unresized
returns, 1024x1536 portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and one side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera |

Prop reference in `references_hd/`: `sword.png`, 1024x1536 portrait, transparent background: the sword ALONE, standing
vertically, point up, full length inside the frame, seen flat from the side, no hand, no scabbard.

Head turnaround in `references_head/`, bust only (helmet with crest, face, neck and top of the shoulders), 1254x1254
(or the closest square size), transparent background, same face and helmet as the body masters, neutral expression,
mouth closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face toward image right),
`03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII Titan from the supplied original sprites, as a 3D modelling reference. Not a new design. Use case: faithful
3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no dramatic
lighting, no rim light, no strong shadows: the light is baked into the texture), semi-realistic game materials, sharp
fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): a giant classical warrior with heroic, very muscular proportions (about 8 heads
tall: broad shoulders, big arms and thighs), skin of smooth pale grey stone with a faint warm tint, like a living marble
statue; a stern classical face, clean-shaven. A dark steel Corinthian-style helmet with gold trim, cheek guards and a
gold ornament on the brow, topped by a tall WHITE horsehair crest running front to back. A sleeveless knee-length tunic
of small dark BLUE quilted scales, with rounded padded shoulders edged in gold, a wide gold belt with an ornate buckle,
and a short skirt of the same blue scale ending above the knees. Bare muscular arms; dark blue armoured vambraces with
gold rims on both forearms. Dark blue greaves with a gold lightning-bolt emblem from knee to ankle, and gold sandals.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the thighs,
EMPTY HANDS (the sword is a separate prop: do not draw it). Legs straight, feet shoulder-width apart with a clear gap
between the thighs, soles flat. Head level, looking forward.

Sword (`sword.png` only): a broad short sword (gladius-like, about 0.9 m long at this figure's scale: blade as long as
the forearm and hand twice over), a straight double-edged leaf-shaped blade of pale bronze-steel with a central ridge,
a gold crossguard with small downturned ends, a dark leather-wrapped grip and a round gold pommel.

Do NOT: add a cape, a shield, a spear, a second weapon or a weapon in the hands; change the colours (grey stone skin,
dark blue scale tunic, vambraces and greaves, gold trim, belt and sandals, white crest, dark steel helmet); make him
slim or ordinary; crop the crest, hands or sandals; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand, separated; grey stone skin; helmet with a white
crest; blue scale tunic with gold-edged shoulders and gold belt; vambraces on both forearms; blue greaves with gold
bolts; gold sandals; heroic proportions; empty hands; A-pose; transparent background; for 01–04 the same figure, pose
and proportions as the primary; side views: in `03_left` his face points to image left, in `04_right` to image right.
Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` and `sword.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the
four head views, with the selected primary as an extra input.
