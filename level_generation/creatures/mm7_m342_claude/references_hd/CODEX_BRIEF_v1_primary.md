# Codex brief (run 1): HD primary for the MM7 Peasant Human1 Female (m342)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m342_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m342_claude/source/native_standing_views.png` — the ORIGINAL native MM7 standing sprite in five views, left to
   right: front, front three-quarter, right-side profile, back three-quarter, back. Enlarged 3x with nearest-neighbour
   pixels on a flat grey background (the grey is not part of the character). The magenta tint in the hair shadows is a
   palette artefact, not part of the design. IDENTITY EVIDENCE, not an image to upscale.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m342_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII female human peasant (a village woman) shown in the attached original sprite views, as a 3D modelling
reference. Not a new design. Exactly ONE whole figure from the top of the head to the shoe soles, front three-quarter
view (the body turned about 35 degrees toward image right, so her right side is nearer the camera, as in the native
second view), camera near orthographic at chest height, slightly above. Generous margins. Even soft neutral studio
light. Transparent background, no floor, no shadow, no scenery, no text.

Identity (all from the native views): an adult woman of normal human proportions, light skin, long thick wavy
chestnut-brown hair falling over the shoulders and down the back to the shoulder blades, large gold hoop earrings.
A white off-the-shoulder linen blouse (chemise) with a gathered neckline and full puffed sleeves gathered just below
the elbow into a ruffled cuff, the forearms bare. Over it a fitted FOREST-GREEN bodice with green shoulder straps,
laced up the front with brown cord through two rows of small gold eyelets. A long full FOREST-GREEN skirt from the
waist to the ankles, open at the front in a narrow split that shows a white underskirt, with a white ruffled
petticoat hem showing below the green hem all round. A black leather belt with a square gold buckle at the waist; from
the belt on her LEFT hip hangs a dagger in a black scabbard with gold fittings, reaching to about knee height. Black
flat shoes.

Pose: neutral A-pose, standing upright, feet slightly apart under the skirt, feet flat. Arms hanging down and out at
about 35 degrees from vertical, elbows nearly straight, a clear gap of air between each arm and the body and between
each hand and the skirt. BOTH HANDS EMPTY, fully OPEN and relaxed, palms toward the body, five straight fingers
visibly spread apart, thumb clearly separated. Head level, looking forward.

Do NOT: put anything in the hands, add a weapon in the hands, an apron, shawl, hat, headscarf, cape or jewellery
other than the hoop earrings; change any colour (green bodice and skirt, white blouse and petticoat, black belt and
scabbard, gold buckle and eyelets, chestnut hair); shorten the hair or the skirt; turn the head; crop the head or
feet; add a floor, shadow or text.

## Checks before selecting (re-run each)

- One figure, front three-quarter, whole figure inside the frame with margins, 1024 x 1536, true transparent alpha.
- Long chestnut hair, gold hoops; white puffed off-shoulder blouse with ruffled cuffs below the elbow; green laced
  bodice; long green skirt with the white front split and white petticoat hem; black belt with gold buckle; the
  sheathed dagger on her LEFT hip.
- Empty open hands with five spread fingers each, clear gaps arm/body and hand/skirt.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
