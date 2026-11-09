# Codex brief (run 2): four HD front/back/side views for the MM7 Zombie (m438)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m438_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (see `generation_runs.json`; earlier brief:
`CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new runs to the existing
`generation_runs.json` (same record format), keep raw returns under `raw/` (`m438_front_v1.png`, ...), and at the end
write `selected_views_review.png` (all five selected views side by side).

## Refusals (user decision 2026-10-20, overrides the earlier no-rewording rule)

If the image service refuses or blocks a request for a view, retry THAT view with the benign wording variants below,
in order, one attempt each, and record every attempt (prompt, refusal text) in `generation_runs.json`:
- Variant R1: replace the identity paragraph's injury wording with: "a stylised fantasy-game undead with weathered
  grey-green skin; a few small dark reddish-brown stains or patches on the chest, the right flank and the right shin
  (no open wounds, no gore); the right forearm is missing below the elbow, ending in a rounded, dark-stained stump".
- Variant R2: as R1, and describe the stump as "the right arm is short, ending just below the elbow in a rounded
  stump wrapped in dark reddish-brown stained cloth"; the shin as "the right trouser leg torn off at the knee, the
  lower leg stained dark reddish-brown".
- Variant R3: as R2, and add "clean stylised game-art look, painted fantasy video-game character, no blood".
If all three variants are refused for a view, stop the whole run and record it. Note in each view's reason which
wording produced the selected image.

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m438_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same zombie, face, headband, skin, trousers, rope belt, right-arm stump, empty left hand, bare feet, colours,
   pose, proportions, light and render style.
2. `mm7_m438/native/m438sa0.png` — ORIGINAL native front.
3. `mm7_m438/native/m438sa2.png` — ORIGINAL native right profile.
4. `mm7_m438/native/m438sa4.png` — ORIGINAL native back.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" means the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of it | face, chest; its RIGHT arm (the stump) on IMAGE LEFT |
| `02_back.png` | straight behind it | back, back of the head with the headband knot; its RIGHT arm (the stump) on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its whole LEFT arm with the empty hand and its LEFT leg nearest the camera |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm stump and its RIGHT lower leg nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in stains or small surface spots.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same zombie as input 1 (a
faithful HD reconstruction of the existing Might and Magic VII Zombie monster), as a 3D modelling reference. Not a new
design. ONE complete figure, head to soles, centred, generous margins, near-orthographic camera at chest height,
transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same render style
and materials as input 1. Restrained game illustration.

Identity (as in input 1): slim, upright, lean adult male undead; gray-green skin; narrow gaunt face, sunken dark eyes,
short dark cropped hair, a narrow olive cloth headband; bare torso and arms with the original small flat dark red and
ivory accents only where input 1 has them; the LEFT arm whole with an empty five-fingered hand; the RIGHT arm ending
just below the elbow as a short stump with a dark red end and two small pale bone tips; worn dark olive-brown cloth
trousers with torn cuffs at mid-shin, a thin pale gray rope belt tied at the front with two short hanging ends; bare
feet; the RIGHT lower leg with the small red and ivory accents as in input 1.

Pose (identical in all views, as in input 1): standing upright, legs straight and apart with a clear gap, feet flat
with toes forward; both arms down and out to the sides at about 35 degrees, elbows very slightly bent, a clear gap of
air between each arm and the body; the left hand open and empty, fingers slightly apart. Head level, looking forward.

Do NOT: draw any held object or weapon; give the right arm a hand; add a shirt, shoes or any accessory; add new
wounds, extra blood or gore detail, or effects; enlarge or intensify the red accents; change the colours; change the
pose; crop the head or feet; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same figure, proportions, pose and colours as input 1;
- whole figure inside the frame with margins, true transparent background, 1024 x 1536;
- right arm a stump on the correct side, left hand empty with five fingers wherever visible;
- in profile, the arm nearest the camera hangs clear of the torso and the far arm is mostly hidden behind it.
