# Codex brief (run 1): HD primary for the MM7 Chain Fighter (m222)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m222_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m222_claude/source/native_standing_views.png` — the ORIGINAL native MM7 standing sprite in five views, left to
   right: front, front three-quarter, right-side profile, back three-quarter, back. Enlarged 3x with nearest-neighbour
   pixels on a flat grey background (the grey is not part of the character). It is IDENTITY EVIDENCE, not an image to
   upscale or trace.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m222_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII "Chain Fighter" soldier shown in the attached original sprite views, as a 3D modelling reference. Not a new
design. Exactly ONE whole figure from the helmet crest to the boot soles, front three-quarter view (the body turned
about 35 degrees toward image right, so her right side is nearer the camera, as in the native second view), camera near orthographic at chest height,
slightly above. Generous margins. Even soft neutral studio light, no dramatic shading. Transparent background, no
floor, no shadow, no scenery, no text.

Identity (all from the native views): a practical fantasy foot soldier, an athletic adult woman of normal human
proportions, fair skin, calm stern face, long straight light-brown hair hanging down her back to below the shoulder
blades. A rounded steel kettle helmet (open face) with a narrow brim, a short gold crest ridge on top and a gold
rim. Armour: a cropped long-sleeved shirt of bright steel chain mail covering the chest, shoulders and upper arms
to the elbows; a green cloth trim at the V of the neck, a green band around the left upper arm and a green cloth
sash at the lower edge of the mail shirt; a dark brown leather shoulder strap diagonally across the chest; one
rounded gold shoulder guard on her RIGHT shoulder; dark brown leather forearm gauntlets with gold rivets and
separate leather-gloved fingers. Midriff of the mail shirt ends at the lower ribs. Hips: a band of steel chain mail
around the hips (fitted mail briefs) with a gold belt chain; two long ornate GOLD metal plate panels hanging in
front from the belt down to the knees. Legs: dark navy-blue glossy leather leggings; tall polished steel greaves and
boots from mid-shin down with dark horizontal bands. On her back: an empty dark sword scabbard worn diagonally from
the right shoulder to the left hip.

Presentation: neutral, modest, documentation-style game asset turnaround; practical armour, non-sexualised.
If the image tool refuses, retry ONCE with a thin dark brown fitted leather underlayer beneath the mail briefs and
mention that deviation in the run's reason.

Pose: neutral A-pose, standing upright, legs straight and slightly apart with a clear gap between the legs and
boots, feet flat. Arms hanging down and out at about 35 degrees from vertical, elbows very slightly bent, a clear
gap of air between each arm and the body and between each hand and the thigh. Hands open and relaxed with five
separated gloved fingers each, palms facing the thighs. Head level, looking forward.

Do NOT: draw the sword (her hands are EMPTY; the sword is modelled separately), a shield, cape, cloak, skirt,
extra pouches or extra armour pieces; change any colour (green trim, gold panels, steel mail, navy leggings,
brown leather); turn the head; crop the helmet or boots; add a floor, shadow or text.

## Checks before selecting (re-run each)

- One figure, front three-quarter, whole figure inside the frame with margins, 1024 x 1536, true transparent alpha.
- Kettle helmet with gold crest; mail shirt with green trim and one gold shoulder guard on her RIGHT shoulder; gold
  front panels; navy leggings; steel boots; brown gauntlets.
- Empty open hands with five fingers each, clear gaps arm/body and hand/thigh, legs apart.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
