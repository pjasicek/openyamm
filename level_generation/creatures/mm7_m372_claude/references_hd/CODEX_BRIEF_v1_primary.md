# Codex brief (run 1): HD primary for the MM7 Peasant Human2 Female (m372)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m372_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m372_claude/source/native_standing_views.png` — the ORIGINAL native MM7 standing sprite in five views, left to
   right: front, front three-quarter, right-side profile, back three-quarter, back. Enlarged 3x with nearest-neighbour
   pixels on a flat grey background (the grey is not part of the character). IDENTITY EVIDENCE, not an image to upscale.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m372_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII female human peasant (a village woman in a long gown and veil) shown in the attached original sprite views,
as a 3D modelling reference. Not a new design. Exactly ONE whole figure from the top of the head to the shoe soles,
front three-quarter view (the body turned about 35 degrees toward image right, so her right side is nearer the
camera, as in the native second view), camera near orthographic at chest height, slightly above. Generous margins.
Even soft neutral studio light. Transparent background, no floor, no shadow, no scenery, no text.

Identity (all from the native views): an adult woman of normal human proportions, light skin, red lips, short
auburn-brown hair with a fringe visible at the forehead, a thin gold circlet across the forehead. A pale sage-green
linen veil covers the top and back of the head and drapes in soft folds around the neck and over the shoulders like a
cowl, its edge framing the face trimmed with a row of small dark-green beads. A long FOREST-GREEN woollen gown from
the shoulders to the floor, fitted at the bodice with a round neckline edged with small dark beads, the skirt falling
straight to the ground and hiding the feet except the toes of brown shoes. Very wide medieval BELL SLEEVES: fitted at
the upper arm, opening into long hanging bell cuffs that reach about knee height, lined with the same pale sage-green
as the veil. A thin twisted gold cord belt at the waist, tied at her LEFT hip with a small dark-blue gem clasp, the
cord ends hanging down along the left side of the skirt.

Pose: neutral A-pose, standing upright, feet slightly apart under the gown. Arms out at about 35 degrees from
vertical, elbows nearly straight, a clear gap of air between each arm, its hanging bell sleeve and the gown, and
between each hand and the gown. BOTH HANDS EMPTY, fully OPEN and relaxed, coming out of the sleeves, palms toward the
body, five straight fingers visibly spread apart, thumb clearly separated. Head level, looking forward.

Do NOT: put anything in the hands, add a weapon, apron, cape, cloak, crown or jewellery other than the thin circlet;
change any colour (forest-green gown and sleeves, pale sage-green veil and sleeve lining, gold cord belt, auburn
hair); shorten the gown or the sleeves; uncover the hair completely; turn the head; crop the head or feet; add a
floor, shadow or text.

## Checks before selecting (re-run each)

- One figure, front three-quarter, whole figure inside the frame with margins, 1024 x 1536, true transparent alpha.
- Pale sage veil/cowl with beaded edge, auburn fringe and gold circlet; floor-length green gown; very wide bell
  sleeves to knee height lined pale sage; gold cord belt tied at her LEFT hip.
- Empty open hands with five spread fingers, clear gaps arm/sleeve/body and hand/gown.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
