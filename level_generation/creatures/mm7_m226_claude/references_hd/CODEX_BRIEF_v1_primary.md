# Codex brief (run 1): HD primary for the MM7 Leather Fighter (m226)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m226_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m226_claude/source/native_standing_views.png` — the ORIGINAL native MM7 standing sprite in five views, left to
   right: front, front three-quarter, right-side profile, back three-quarter, back. Enlarged 3x with nearest-neighbour
   pixels on a flat grey background (the grey is not part of the character). IDENTITY EVIDENCE, not an image to upscale.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m226_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII "Leather Fighter" (robber / bandit) shown in the attached original sprite views, as a 3D modelling
reference. Not a new design. Exactly ONE whole figure from the top of the head to the boot soles, front three-quarter
view (the body turned about 35 degrees toward image right, so his right side is nearer the camera, as in the native
second view), camera near orthographic at chest height, slightly above. Generous margins. Even soft neutral studio
light. Transparent background, no floor, no shadow, no scenery, no text.

Identity (all from the native views): a broad-shouldered, muscular adult man of normal human proportions, pale skin,
stern face, dark brown-black hair swept back into a ponytail at the nape. A fitted GREEN quilted/padded leather
jerkin with long sleeves and a high soft green collar around the neck. Over the shoulders a dark brown leather yoke
(a wide shoulder mantle of stiff leather plates) with silver rivets and short steel spikes along its edge and a
silver-edged rim. A dark leather strap down the centre of the chest with small silver fittings. Dark studded leather
bracers on both forearms with a few short spikes. A dark leather belt with a large ornate silver buckle plate at the
front. Brown pebbled leather trousers; on the front of his LEFT thigh a green panel with criss-cross lacing. A gold
dagger sheath on his RIGHT hip. Tall black leather boots with several silver buckles. A sword grip with a dark
handle sticks up behind his RIGHT shoulder (a sheathed weapon on his back).

Pose: neutral A-pose, standing upright, legs straight and slightly apart with a clear gap between the legs and
boots, feet flat. Arms hanging down and out at about 35 degrees from vertical, elbows nearly straight, a clear gap of
air between each arm and the body and between each hand and the thigh. BOTH HANDS EMPTY, fully OPEN and relaxed,
palms toward the thighs, five straight fingers visibly spread apart, thumb clearly separated. Head level, looking
forward.

Do NOT: draw the falchion or any weapon in the hands (the sword is modelled separately), a shield, cape, cloak or
helmet; add armour plates; change any colour (green jerkin and collar, dark brown yoke, brown trousers, black boots,
silver fittings); turn the head; crop the head or boots; add a floor, shadow or text.

## Checks before selecting (re-run each)

- One figure, front three-quarter, whole figure inside the frame with margins, 1024 x 1536, true transparent alpha.
- Green jerkin + high collar, spiked dark leather shoulder yoke, studded bracers, silver belt buckle, brown trousers
  with the laced green panel on his LEFT thigh, gold dagger sheath on his RIGHT hip, black buckled boots, ponytail.
- Empty open hands with five spread fingers each, clear gaps arm/body and hand/thigh, legs apart.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
