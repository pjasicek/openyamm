# Codex brief: HD reference views for the MM6 Titan (ttn1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_ttn1_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_hyd_claude/references_hd/generation_runs.json`. Attached inputs:
1. `level_generation/creatures/mm6_ttn1/references/standing.png` — ORIGINAL native five-view sheet (front, front
   three-quarter, profile, rear three-quarter, back). Magenta is background, not creature. Design/anatomy/palette
   authority.
2. `level_generation/creatures/mm6_ttn1/native/ttn1sta0.png` — ORIGINAL native front frame (transparent background).
3. `level_generation/creatures/mm6_ttn1/native/ttn1sta1.png` — ORIGINAL native front three-quarter frame.
4. `level_generation/creatures/mm6_ttn1/aligned_2x/ttn1sta0.png` — restored 2x front view, for surface material
   only (it never sets the design).

## Deliverables (5 images, transparent background, 1024 x 1536 portrait, unresized returns)
- `00_three_quarter.png` — front-right three-quarter, camera at chest height, slightly above (primary; generate first)
- `01_front.png`, `02_back.png`, `03_left.png` (the titan's own left side), `04_right.png` (his right side)
Generate 01–04 with 00 as an additional input so all five are the SAME titan, SAME pose, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason) and a
`selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below; record superseded runs.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Titan from the supplied original sprites, as a 3D modelling reference. Not a new design.
Use case: faithful 3D modelling reference. ONE complete figure, full body from crest tip to toes, centred, generous
margins, near-orthographic camera, transparent background, no floor, no shadow, no scenery, no text. Even soft
neutral studio light (no dramatic lighting, no rim light, no glow) that still shows form. Credible fully
three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): a giant, heroic, very muscular man (bodybuilder proportions, broad shoulders,
thick arms and legs, head about one-eighth of body height). Skin cool pale STONE-GREY with darker grey shading and
fine dark hair on the forearms and shins; stern classical face, strong jaw and straight nose, clean-shaven; eyes
pale and blank (white, no visible pupils). Armour in polished LAVENDER-BLUE / periwinkle metal with a hammered,
slightly mottled surface, all edges trimmed with bright GOLD:
- Helmet: Greek Corinthian-style open-face helmet in lavender-blue metal, gold brow band rising to a pointed gold
  triangular ornament over the forehead, gold rims down the cheek guards that frame the face (face fully visible),
  and a tall RED horsehair crest running front to back over the top of the helmet.
- Muscle cuirass in lavender-blue metal sculpted with pecs and a six-pack, a gold collar rim at the neck, a row of
  small gold rivets down each side; the back plate is plain hammered metal.
- Rounded shoulder pauldrons (one plate each) with two gold rims and gold rivets.
- Wide GOLD belt at the waist with a round gold medallion holding a red gem at the front centre.
- Skirt of overlapping rounded scale plates (three rows of large lavender-blue scales, like pteruges) from the belt
  to mid-thigh, all the way round.
- Forearm bracers in lavender-blue metal, from wrist to just below the elbow, with a gold band at each end and gold
  rivets.
- Greaves from the knee to the ankle in darker violet-blue metal, a gold-rimmed knee cap with gold studs, a thin gold
  band at the ankle.
- BAREFOOT: bare grey feet with five toes each. Upper arms, hands, knees above the greaves and thighs below the skirt
  are bare grey skin.

Pose (identical in all five views): standing upright in an A-pose — arms straight down and away from the body at
about 30 to 35 degrees from vertical, elbows very slightly bent, hands open and relaxed with the FIVE fingers
separated and slightly curled, palms facing the thighs, hands clear of the skirt; legs straight and slightly apart
with a visible gap between the thighs and between the greaves, feet flat. Head level, looking forward.

Do NOT: add a weapon, shield, cape, cloak, sandals or boots, a beard, lightning or glowing effects; do not cover the
face; do not change colours (stone-grey skin, lavender-blue armour, gold trim, red crest, red belt gem); do not crop
the crest, hands or feet; do not make the armour black, silver or steel.

Checks per image: whole figure with crest and toes inside the frame; helmet with gold brow ornament, cheek guards and
red front-to-back crest; face visible; muscle cuirass with gold collar; two pauldrons; gold belt with red gem
medallion; three-row scale skirt; bracers with gold bands; greaves with gold knee caps; bare feet with five toes;
five separated fingers on each hand, hands away from the body; transparent background; same pose and proportions as
the primary. In the side views the left/right sides must agree with the front and back.
