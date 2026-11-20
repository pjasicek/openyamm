# Codex brief (run 1): HD primary for the MM7 Peasant Human1 Male (m352)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m352_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m352_claude/source/native_standing_views.png` — the ORIGINAL native MM7 standing sprite in five views, left to
   right: front, front three-quarter, right-side profile, back three-quarter, back. Enlarged 3x with nearest-neighbour
   pixels on a flat grey background (the grey is not part of the character). IDENTITY EVIDENCE, not an image to upscale.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m352_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII male human peasant (a villager) shown in the attached original sprite views, as a 3D modelling reference.
Not a new design. Exactly ONE whole figure from the top of the head to the shoe soles, front three-quarter view (the
body turned about 35 degrees toward image right, so his right side is nearer the camera, as in the native second
view), camera near orthographic at chest height, slightly above. Generous margins. Even soft neutral studio light.
Transparent background, no floor, no shadow, no scenery, no text.

Identity (all from the native views): an ordinary adult man of normal human proportions, lean build, light tan skin,
long straight BLACK hair parted in the middle and falling past the shoulders at the back and sides, a black
moustache and a short trimmed full black beard along the jaw and chin. A loose FOREST-GREEN woven wool tunic reaching to
mid-thigh, plain round neckline with a row of small brass studs around the neck opening, wide three-quarter sleeves
ending at mid-forearm in a cuff band with a ring of small brass studs, the wrists and hands bare. The tunic's bottom hem is
cut into ragged rectangular tabs (a dagged, tattered hem). A tan-brown leather belt with small round studs and a small
silver buckle at the waist, a thin strap end hanging down at his left hip. Close-fitting pale grey-beige linen
trousers (hose, softly wrinkled) tucked into short brown leather ankle shoes.

Pose: neutral A-pose, standing upright, legs straight and slightly apart with a clear gap between the legs and
shoes, feet flat. Arms hanging down and out at about 35 degrees from vertical, elbows nearly straight, a clear gap of
air between each arm and the body and between each hand and the thigh. BOTH HANDS EMPTY, fully OPEN and relaxed,
palms toward the thighs, five straight fingers visibly spread apart, thumb clearly separated. Head level, looking
forward.

Do NOT: put anything in the hands, add a weapon, tool, bag, hat, hood, cape, cloak, armour or jewellery; change any
colour (forest-green tunic, brown belt, pale grey-beige trousers, brown shoes, black hair and beard); shorten the
hair; turn the head; crop the head or feet; add a floor, shadow or text.

## Checks before selecting (re-run each)

- One figure, front three-quarter, whole figure inside the frame with margins, 1024 x 1536, true transparent alpha.
- Long black hair, moustache and short beard; green tunic with studded neckline and studded mid-forearm cuffs, ragged tabbed hem
  at mid-thigh; brown belt; pale close-fitting trousers; brown shoes; bare wrists and hands.
- Empty open hands with five spread fingers each, clear gaps arm/body and hand/thigh, legs apart.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
