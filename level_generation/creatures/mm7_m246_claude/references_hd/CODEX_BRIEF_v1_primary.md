# Codex brief (run 1): HD primary for the MM7 Goblin (m246)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m246_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m246_claude/source/native_standing_views.png` — the ORIGINAL native MM7 goblin standing sprite in five views,
   left to right: front, front three-quarter (his right side nearer), right-side profile, back three-quarter, back.
   Enlarged 3x with nearest-neighbour pixels on a flat grey background (the grey is not part of the character).
   IDENTITY EVIDENCE, not an image to upscale. He holds a sword in the native; it is NOT to be drawn here.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m246_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII "Goblin" warrior shown in the attached original sprite views, as a 3D modelling reference. Not a new design.
Exactly ONE whole figure from the helmet crest to the soles, front three-quarter view (the body turned about 35 degrees
toward image right, so his RIGHT side is nearer the camera, as in the native second view), camera near orthographic at
chest height, slightly above. Generous margins. Even soft neutral studio light. Transparent background, no floor, no
shadow, no scenery, no text.

Identity (all from the native views): an adult male goblin warrior of near-human height with a lean, muscular,
upright build and long arms. Olive-green skin with yellow-green highlights and deep forest-green shadows. A small,
stern, angular face with a heavy brow, narrow yellow eyes, a broad flat nose, a wide mouth with small jutting lower
teeth and a short dark purple chin tuft; pointed green ears. Thin reddish-brown hair hangs from under the back of the
helmet. A tall, narrow, ornate BRASS/GOLD helmet: a crown-like brow band with small upward spikes around it and a tall
swept-back segmented gold crest curling at the top. A sleeveless, close-fitting muted BLUE-TEAL vest with a deep V
neckline and fine gold edge trim, and a dark diagonal strap over his right shoulder. His LEFT shoulder carries one heavy
ornate spiked brass pauldron, and his LEFT arm is covered by dark navy scaled sleeve armour with ornate brass
segmented plates down to the wrist. His RIGHT upper arm is bare green muscle; his RIGHT forearm has a dark navy scaled
bracer with gold trim. A brass belt with gold studs and thin gold straps hanging at the hips. Dark navy-blue scaled
fitted trousers with thin brown leather bands below the knees and small gold stud details down the outer seams.
Tall brown leather knee boots with ornate brass shin guards carrying pointed spikes on the front.

Pose: neutral A-pose, standing upright, legs straight and slightly apart with a clear gap between the legs, feet flat.
Arms hanging down and out at about 35 degrees from vertical, elbows nearly straight, a clear gap between each arm and
the body and between each hand and the thigh. BOTH HANDS EMPTY and OPEN, green fingers straight and visibly spread
apart, thumb separated, palms toward the thighs. Head level, looking forward.

Do NOT: draw the sword or any weapon (modelled separately), a shield, cape or cloak; put the pauldron or arm armour on
the wrong arm (pauldron and sleeve armour on HIS LEFT, the bare arm with the bracer on HIS RIGHT); change any colour
(green skin, brass, blue-teal vest, navy trousers, brown boots); make him short, hunched or cartoonish; turn the head;
crop the crest or feet; add a floor, shadow or text.

## Checks before selecting (re-run each)

- One figure, front three-quarter (his right side nearer the camera), whole figure inside the frame with margins,
  1024 x 1536, true transparent alpha.
- Green goblin face with pointed ears and yellow eyes; tall brass crested spiked helmet; blue-teal vest with gold trim;
  brass pauldron and armoured sleeve on HIS LEFT arm only; bare right upper arm with a navy bracer on the right forearm;
  navy scaled trousers; brown boots with spiked brass shin guards.
- Empty open hands with spread fingers, clear gaps arm/body and hand/thigh, legs apart.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
