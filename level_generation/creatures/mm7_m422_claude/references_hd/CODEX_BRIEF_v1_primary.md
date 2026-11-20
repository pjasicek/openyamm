# Codex brief (run 1): HD primary three-quarter view for the MM7 Vampire (m422)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m422_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. Record format: as in
`level_generation/creatures/mm7_m274_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):

1. `mm7_m422/native/m422sa0.png` — ORIGINAL native FRONT frame (256 x 256, transparent background). Design,
   proportions and palette authority.
2. `mm7_m422/native/m422sa1.png` — ORIGINAL native FRONT THREE-QUARTER frame.
3. `mm7_m422/native/m422sa2.png` — ORIGINAL native PROFILE frame.
4. `mm7_m422/native/m422sa4.png` — ORIGINAL native BACK frame (the burgundy cape and the tall collar from behind).
5. `mm7_m422/aligned_2x/m422sa1.png` — restored 2x three-quarter view, SURFACE MATERIAL ONLY (cloth, gold, leather).

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, genuine transparent background, unresized native return; raw returns
under `raw/`; `generation_runs.json`. Accept the first image that passes the checks; at most ONE targeted corrective
regeneration for a failed image, then select the better and note residual faults. Stop after that.
If the image tool declines a request, do NOT reword it to try again: record the refusal text in
`generation_runs.json` and in your last message, and stop.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII "Vampire" nobleman monster from the supplied original sprites, as a 3D modelling reference. Not a new
design. Output: exactly ONE 1024 x 1536 portrait PNG, genuine transparent background. ONE complete figure, full body
from the tips of the collar down to the boot soles, centred, about 80% of the canvas height with about 140 px of
transparent space above and below, generous side margins. Near-orthographic camera, no floor, no shadow, no scenery,
no text. Even soft neutral studio light (no dramatic or rim light). Credible fully three-dimensional sculpt,
semi-realistic game materials, sharp fine detail.

Identity (from the native sprites):
- A tall, lean adult man with very pale ivory-grey skin; a narrow, stern, angular face with high cheekbones, dark
  eyes, a slightly open mouth showing two small ivory fangs; short, neatly swept-back dark charcoal-grey hair with a
  sharp widow's peak.
- COLLAR: a tall stiff dark wine-red (burgundy) stand-up cape collar that flares outward behind and beside the head
  into pointed tips at about ear height, edged with a thin gold line.
- COAT: a long royal-blue long-sleeved coat, fitted at the chest and waist, flaring into a wide skirt that ends at
  mid-shin (above the boot tops); a narrow white shirt V at the neck with a small gold neck ornament; a vertical gold
  embroidered fastening strip down the centre front with a row of gold clasps/loops; a thin gold hem band; small
  white shirt cuffs at the wrists.
- BELT: a broad ornate GOLD waist belt with a large oval centre buckle and winglike gold scrolls on each side.
- CAPE: a dark wine-red (burgundy) cape hanging from the shoulders behind the arms down to about the knees/coat hem,
  closed across the back, with a scalloped (gently wavy) lower edge trimmed with a thin gold band; from the front only
  its edges show behind the arms.
- Black fitted trousers and plain black calf-high leather boots with small heels.
- Bare pale hands with long slender fingers. No weapon.

Pose (the pose for every later view as well): standing upright, relaxed, legs slightly apart with a gap between the
boots. Arms in an A-POSE: hanging down and out from the body at about 40 degrees from vertical, elbows very slightly
bent, with a clear gap of air between each arm/sleeve and the body; the arms in FRONT of the cape, never on it. Both
hands OPEN and relaxed, palms facing the thighs, fingers gently separated. Both hands empty. Head level, looking
forward.

Do NOT: add a weapon, armour, jewellery, cape clasps or symbols; add bats, glowing eyes, blood, magic effects or
particles; change the colours (royal-blue coat, burgundy cape and collar, gold strip/belt/trim, pale skin, charcoal
hair, black boots); let the cape cover the arms or hands; crop the collar tips or the boots; add a floor, shadow,
glow or text.

INPUT ROLES (put these in the prompt): inputs 1–4 are the ORIGINAL native frames (anatomy, costume and silhouette
authority; the transparent background is not part of the character); input 5 is SURFACE MATERIAL ONLY.

Camera for this PRIMARY view: a TRUE FRONT THREE-QUARTER view, 40–45 degrees to one side of straight front, at chest
height and slightly above, near-orthographic. It must show real depth (the front and one flank of the coat, part of
the cape at the back). Head aligned with the torso.

## Checks (re-run before selecting)

- true three-quarter camera (40–45 degrees), not near-frontal;
- whole figure inside the frame (collar tips, boots), true transparent alpha, 1024 x 1536;
- pale face with small fangs and swept dark hair; tall burgundy collar; royal-blue coat to mid-shin with the gold
  front strip, clasps and hem band; broad gold belt with oval buckle; white cuffs; burgundy cape with gold scalloped
  hem behind; black boots;
- A-pose arms clear of the body and the cape; both hands open, five fingers each, empty.
