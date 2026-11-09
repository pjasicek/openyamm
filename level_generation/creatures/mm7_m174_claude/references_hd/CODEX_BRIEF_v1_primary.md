# Codex brief (run 1): HD primary three-quarter view for the MM7 Cleric of the Sun (m174)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m174_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The other four views are a separate later run.

Use your built-in image generation. Record format: as in
`level_generation/creatures/mm7_m170_claude/references_hd/generation_runs.json` (id, prompt, inputs with sha256,
output path, selected flag, reason, superseded runs). Attached inputs, in order (paths relative to
`level_generation/creatures/`):

1. `mm7_m174/native/m174sa0.png` — ORIGINAL native FRONT frame (256 x 256, transparent background). Design,
   proportions and palette authority.
2. `mm7_m174/native/m174sa1.png` — ORIGINAL native FRONT THREE-QUARTER frame.
3. `mm7_m174/native/m174sa2.png` — ORIGINAL native PROFILE frame.
4. `mm7_m174/native/m174sa4.png` — ORIGINAL native BACK frame (grey skull cap, collar, the two lobes of the mantle).
5. `mm7_m174/aligned_2x/m174sa0.png` — restored 2x front view, SURFACE MATERIAL ONLY (gold, cloth, skin).
   It never sets the design, pose or proportions.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, genuine transparent background, unresized native return. Keep raw
returns under `raw/`. Write `generation_runs.json`.

Accept the first image that passes the checks below. For a failed image do at most ONE targeted corrective
regeneration, then select the better of the two and note any residual fault in its reason. Stop after that.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII "Cleric of the Sun" from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1024 x 1536 portrait PNG, genuine transparent background. ONE complete figure, full body from the
tips of the sun rays above the head down to the robe hem, centred, the figure about 80% of the canvas height with
about 140 px of transparent space above and below, generous side margins. Near-orthographic camera, no floor, no
shadow, no scenery, no text. Even soft neutral studio light (no dramatic or rim light) that still shows form.
Credible fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites):
- A stately adult man of normal build. His FACE is covered by a polished GOLD SUN MASK: a sculpted golden human face
  (calm, stern, closed lips) with a wide sunburst of about twelve WAVY golden rays radiating from its edge around the
  head, the upper rays longest (rising well above the head), the side rays shorter. Behind the mask the back of the
  head is covered by a smooth GREY STEEL skull cap.
- COLLAR: a tall, stiff, flared SCARLET stand-up collar rising behind the neck and the mask's lower edge.
- MANTLE: a large, rounded, puffy GOLD mantle (capelet) over both shoulders and the upper arms, reaching to the waist,
  open at the centre front (a narrow strip of the red robe shows down the middle); its surface is gold silk with
  rippling WAVY parallel ridges (like gold flames or feathers), lighter yellow-gold highlights. Seen from the back
  it is two big rounded lobes.
- ROBE: a floor-length SCARLET robe, flaring toward the hem, with fine vertical stripes of darker red and orange-red
  running from the waist to the hem; the hem touches the ground, the feet are hidden.
- STOLE: a long hanging panel down the front from under the mantle at the waist to about the knees, ending in a
  point: TEAL-GREEN cloth with a pale cream-tan edge and gold border, decorated with a column of small yellow and
  orange-red jewels; a small gold buckle at its top.
- ARMS: the forearms are BARE (tan skin) below the mantle, with a broad polished GOLD band round each wrist; the hands
  are bare, tan skin, no rings.

Pose (the pose for every later view as well): standing upright, relaxed, weight even, legs slightly apart under the
robe. Arms in an A-POSE: the upper arms under the mantle, the forearms hanging down and out away from the body at about
35 degrees from vertical, elbows very slightly bent, with a clear gap of air between each forearm/hand and the robe.
Both hands OPEN and relaxed, palms toward the thighs, fingers gently separated with a slight natural curl, thumb clearly
apart from the index finger. Head level, mask looking forward.

Do NOT: show the man's real face (only the gold mask); draw a staff, weapon or any held object; add a hood, a cape
below the waist, armour or extra jewellery; change colours (gold mask, rays and mantle; grey cap; scarlet collar and
striped robe; teal stole with cream/gold edge and yellow/red jewels; tan skin; gold wrist bands); let the mantle
cover the forearms or hands; crop the rays or the hem; add a floor, shadow, glow, sparkles, spell effect or text.

INPUT ROLES (put these in the prompt):
- Inputs 1–4: ORIGINAL native front, front three-quarter, profile and back frames: anatomy, costume placement and
  silhouette authority. Their transparent background is not part of the character.
- Input 5: restored 2x front view, SURFACE MATERIAL ONLY, never design/pose/proportions authority. Ignore edge
  artefacts.
- Reconstruct the native design in the requested neutral A-pose with open empty hands.

Camera for this PRIMARY view: FRONT THREE-QUARTER, camera 40–45 degrees to one side of straight front (either side),
at chest height and slightly above, near-orthographic with only a subtle downward view. It must show the front and
one flank clearly (real depth: the nearer arm overlaps the body silhouette less than the farther one). Head aligned
with the torso, no separate head turn.

## Checks (re-run before selecting)

- camera: a true three-quarter (40–45 degrees), not near-frontal;
- whole figure inside the frame (all ray tips, hem), true transparent alpha, 1024 x 1536;
- gold sun mask with about twelve wavy rays, grey cap behind, tall flared scarlet collar;
- rounded wavy-ridged gold mantle to the waist, open at the front; striped scarlet floor-length robe;
- teal jewelled stole with pale/gold edge down the front to the knees;
- bare tan forearms with gold wrist bands, A-pose arms clear of the robe, open empty hands; no added object.
