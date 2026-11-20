# Codex brief: HD reference views for the MM6 Demon (texture pass, 2026-11-11)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_demon_texpass_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

The 3D model already exists; it was modelled from input 1. These views are for a Meshy RETEXTURE of that existing
mesh, so the pose and proportions must match input 1 exactly, seen from four orthographic directions.

Attached inputs, in order:
1. `references_hd/00_three_quarter.png` — the FROZEN primary (already selected, do not regenerate it): the HD image
   the 3D model was built from. Authority for pose, proportions, anatomy, materials and fine surface detail.
2. `mm6_demon_meshy_reference_20261004/dmnstda0_native.png` — ORIGINAL native front sprite (black/transparent background
   is not creature). Palette and identity authority.
3. `mm6_demon_meshy_reference_20261004/dmnstda2_native.png` — ORIGINAL native profile sprite.
4. `mm6_demon_meshy_reference_20261004/dmnstda4_native.png` — ORIGINAL native back sprite.

## Deliverables (4 images, transparent background, 1024 x 1536 portrait, unresized returns)
- `01_front.png` — camera straight in front of the creature.
- `02_back.png` — camera straight behind.
- `03_left.png` — the creature's LEFT side: camera on the creature's own left; its left arm is nearest the camera and its nose points to image-LEFT.
- `04_right.png` — the creature's RIGHT side: camera on the creature's right, creature faces image-RIGHT.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet of 00-04. One corrective regeneration per view at most.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition orthographic views of the EXISTING Might
and Magic VI walking Demon exactly as in the supplied HD three-quarter image (input 1), as a 3D texturing reference.
Not a new design. ONE complete creature, full body including spikes, every claw, both feet and the whole tail, centred,
about 70 % of the canvas height, generous margins, near-orthographic camera at chest height, transparent background,
no floor, no shadow, no scenery, no text. Even soft neutral studio light (no dramatic or rim light) that still shows
form. Sharp fine detail everywhere: interlocking slate-charcoal scales, pale-grey abdominal scutes, ivory bone.

Identity (input 1 and the native sprites): tall wiry dark charcoal-grey reptilian humanoid with a small head; compact
angular head with pointed bat-like ears, pinkish-red eyes with dark pupils, broad mouth with ivory teeth and corner
fangs. Fine interlocking charcoal scales with faint bluish-grey sheen and thin brownish edges; pale-grey horizontal
scutes on the chest and belly down to the groin. THREE tall curved ivory spikes on EACH shoulder; a row of short ivory
spikes along the OUTER edge of each forearm. Jade-green harness over the chest and shoulders with a small ivory skull
clasp centred on the chest; narrow green straps continue over the back. Very long arms, huge hands with long separated
fingers ending in curved ivory claws, plus a thumb. Three-toed taloned feet with ivory claws. ONE long thin tail from
the base of the spine with a pointed tip. No wings.

Pose (identical to input 1 in all four views): symmetrical A-pose, arms straight-ish and angled about 45 degrees
down and out from the shoulders, hands curled loosely with claws visible, legs straight and apart, feet flat, tail
hanging in a gentle curve behind/beside the legs as in input 1. Head level, looking forward.

Do NOT: add armour, belt, trousers, weapon, wings, extra horns or limbs, jewellery, glow, blood; do not change the
colours (charcoal scales, pale-grey scutes, jade-green harness, ivory spikes/claws/teeth, pinkish-red eyes); do not
change the pose, the arm angle or the proportions; do not crop any claw, spike, foot or the tail.

Checks per image: whole figure inside the frame; three shoulder spikes per side; forearm spike rows; skull clasp at
the chest (front) and straps on the back (back); tail present; correct facing direction for 03/04; transparent
background; same pose and proportions as input 1.
