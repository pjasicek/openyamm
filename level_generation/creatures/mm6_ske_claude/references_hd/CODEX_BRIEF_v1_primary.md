# Codex brief (run 1): HD three-quarter primary for the MM6 Skeleton (ske)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_ske_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The four orthographic views are a later, separate run.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_thf_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):

1. `mm6_ske/references/standing.png` — ORIGINAL native five-view standing sheet (top row: front, front
   three-quarter, profile; bottom row: rear three-quarter, back). Magenta is background, not creature. Design,
   proportions and palette authority.
2. `mm6_ske/native/skesta0.png` — ORIGINAL native front frame (transparent background).
3. `mm6_ske/native/skesta1.png` — ORIGINAL native front three-quarter frame.
4. `mm6_ske/native/skesta2.png` — ORIGINAL native profile frame (shows the neck and spine curve and the foot shape).
5. `mm6_ske/aligned_2x/skesta0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (bone finish, skull and
   rib detail). It never sets the design, pose or proportions.

The sprites show a short curved sword in the skeleton's right hand. The 3D model gets that sword as a separate
prop later, so the reference must show the skeleton EMPTY-HANDED.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45° toward the skeleton's own RIGHT side), camera at chest height, slightly above; 1024 x 1536 portrait, true transparent background, unresized return |

Keep raw returns under `raw/` (`ske_three_quarter_v1.png`, ...). Write `generation_runs.json` (id, family `ske`,
role `primary`, prompt, inputs with sha256, output path, selected flag, reason, superseded runs). If the first
return fails a check below, do ONE targeted corrective regeneration, then select the better of the two and note any
residual fault in its reason. Do not chase minor differences.

## Prompt content

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Skeleton monster from the supplied original sprites, as a 3D modelling reference. Not a new design.
Use case: faithful 3D modelling reference. Output: exactly ONE 1024 x 1536 portrait PNG with a genuine transparent
background. ONE complete figure, full body from the top of the skull to the foot bones, centred, generous margins,
near-orthographic camera, no floor, no shadow, no scenery, no text. Even soft neutral studio light (no dramatic
lighting, no rim light) that still shows form. Credible, fully three-dimensional sculpt, semi-realistic game
materials, sharp fine detail.

Identity (from the native sprites): an anatomically plausible, complete adult human skeleton, standing upright
by itself, tall and lanky (skull about one-seventh of the body height), long thin limbs, narrow ribcage, wide pelvis.
- SKULL: smooth rounded cranium, large deep round eye sockets with a small bright glowing RED point (a red pupil
  light) sitting deep in each socket, dark triangular nasal opening, prominent cheekbones, a full row of upper and
  lower teeth in a slight grin, a separate lower jaw closed. No skin, no hair.
- NECK: a short column of cervical vertebrae, the head carried slightly forward as in the native profile.
- RIBCAGE: a sternum down the centre front and about twelve pairs of separate, thin, curved ribs with clearly visible
  dark gaps between them; clavicles across the top of the chest to the shoulders; shoulder blades (scapulae) on the
  back. Seen through the rib gaps the inside of the ribcage is empty and dark.
- SPINE: the spine is visible as a single column of vertebrae from the ribcage down to the pelvis, with open space
  on both sides of it at the waist (no belly, no flesh).
- PELVIS: a broad bowl-shaped pelvis with hip bones flaring to both sides.
- ARMS: upper arm bone, the two thin forearm bones side by side, knobbly elbows; bony hands with five fingers each
  (thumb plus four fingers made of small finger bones).
- LEGS: long femurs, knobbly knees with kneecaps, the two lower-leg bones, bony ankles and long flat bony feet with
  five toes each.
- MATERIAL AND COLOUR: clean, smooth, dry bone in a pale IVORY / off-white with a faint warm cream tint, soft grey
  shading in the joints and crevices, slight satin sheen. Exactly the colour of the native front sprite (the Skeleton
  A palette). No dirt, no moss, no cracks, no blood, no rust.

Pose: a neutral A-pose for rigging. Standing upright, weight even, legs straight and apart with a clear gap of air
between the legs and between the feet (feet about shoulder width apart, flat on the ground, toes forward). Arms hang
down and out to the sides at about 35 degrees from vertical, elbows very slightly bent, with a clear gap of air
between each arm and the ribcage/pelvis and between each hand and the thigh. Both hands relaxed, fingers slightly
curled and held together side by side (not splayed), thumbs relaxed, palms facing the thighs. Head level, looking
forward (keep only the slight forward neck carry of the native profile).

Do NOT: draw the sword or any weapon, a shield, armour, a helmet, clothing, rags, a cape, a belt, jewellery or any
equipment; add flesh, skin, muscles, organs or a solid torso; fill the gaps between the ribs; add extra ribs, extra
fingers or toes, horns, spikes or a tail; make it cartoonish, chunky or small-headed-and-muscular; change the colour
(no yellow, no grey-white plastic, no dark brown); add glowing aura, smoke or magic effects; crop the skull or the
feet; add a floor, shadow or text.

## Checks before selecting

- the camera is a front-right three-quarter (the skeleton's own right side turned toward the camera) at chest
  height, near-orthographic, the whole figure inside the frame with margins, 1024 x 1536, true transparent
  background (not a checkerboard drawn into the pixels);
- empty hands, no weapon or equipment of any kind;
- five fingers per hand and five toes per foot, separate ribs with dark gaps, visible spine column at the waist,
  pelvis, kneecaps;
- red glowing points in the eye sockets, full teeth, lower jaw;
- ivory bone colour matching input 2; A-pose with the stated gaps.
