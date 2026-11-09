# Codex brief: HD reference views for the MM7 Hydra (mm7_m266_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m266_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_rat_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite standing views enlarged 3x with nearest neighbour,
   left to right: front, front three-quarter (the hydra faces image RIGHT), profile (faces image RIGHT), rear
   three-quarter, back. Magenta is background ONLY. Design, anatomy and colour authority.
2. `references_hd/native_palettes.png` — the three-quarter view in the three native palettes. Use the MIDDLE
   (blue-grey) colouring.
3. `references_hd/native_actions.png` — native attack and hit frames: anatomy evidence only (mouths, horns, how the
   necks bend).
4. `level_generation/creatures/mm7_m266/trimmed_2x/m266sa0.png` — restored 2x front frame, SURFACE MATERIAL and head
   detail ONLY (never the pose).

## Deliverables (5 images, transparent background, 1536 x 1024 LANDSCAPE, unresized returns)
- `00_three_quarter.png` — front three-quarter from the hydra's RIGHT side (the hydra faces toward image RIGHT-front,
  like native view 2 of input 1), camera at chest height, slightly above (primary; generate first; this image alone
  becomes the 3D mesh, so all five heads, all four legs and the tail must be readable and separated by air)
- `01_front.png`, `02_back.png`, `03_left.png` (the hydra's LEFT side: it faces image LEFT), `04_right.png` (its RIGHT
  side: it faces image RIGHT)

Generate ONLY `00_three_quarter.png` in the first run unless told otherwise. Views 01–04 come in a separate run with
00 as the FIRST input, so all five show the same hydra, pose and proportions. At most one corrective regeneration per
view. Also write `generation_runs.json` (id, prompt, inputs with sha256, output, selected flag, reason, superseded
runs) and, once all five exist, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII hydra from the supplied original sprites, as a 3D modelling reference. Not a new design. Beautifully
detailed, credible fully three-dimensional creature with semi-realistic game materials and sharp fine detail (scales,
ventral plates, teeth, horns), even soft neutral studio light, near-orthographic camera, the WHOLE hydra inside the
frame with generous margins (every head, horn, crest, claw and the tail tip included), transparent background, no
floor, no cast shadow, no scenery, no text.

Identity (from the native sprites): a squat, heavy, four-legged reptile with FIVE long serpentine necks rising from
its broad chest, each ending in a different horned dragon head. Body and legs: dark BLUE-GREY scaly hide with darker
mottling, thick bowed legs, each foot with WHITE/IVORY claws. A row of ivory spikes runs down the spine and along the
whole tail. Every neck and the chest/belly carry PALE SILVER segmented ventral plates (large horizontal plates with
dark grooves between them) on the front/underside; the backs of the necks are scaly like the body. The thick tail
lies on the ground behind the body.

The five heads, listed from the hydra's RIGHT to its LEFT (image left to right in the front view):
1. Outer right: dark blue dragon head with TWO LARGE swept-back ribbed fins/crests (like bat-wing frills, blue
   membrane between dark ribs) rising above and behind the skull, ivory horns, mouth open showing a RED mouth and
   ivory teeth.
2. Inner right: smaller violet-blue head with a SPIKY dark crest/mane of short spines along the top and back of the
   skull, small ivory horns, mouth open (red mouth, ivory teeth).
3. Centre: the TALLEST neck, nearly straight and upright; dark navy head with a crown of dark spikes and small ivory
   horn nubs, mouth open facing forward (red mouth, ivory teeth).
4. Inner left: grey-teal/blue-grey head with a RUST-BROWN fin/frill along the top of the skull, mouth open (red mouth,
   ivory teeth).
5. Outer left: RUST-BROWN head with several LARGE CURVED IVORY HORNS sweeping back and up, mouth open (red mouth,
   ivory teeth); its neck is mottled rust-brown and blue-grey on the back, silver plates on the front.
All five mouths open about as wide as in the native standing frames. Eyes small and fierce.

Pose (identical in all five views; a neutral rigging pose based on the native standing frame): the body stands
square on all four legs, legs slightly apart and clearly separated from each other and from the tail; the five necks
rise from the chest and FAN OUT like an open hand: the centre neck straight up and tallest, the inner necks
diverging about 20 degrees to each side, the outer necks about 40 degrees, each with a gentle S-curve, all heads
looking forward. Every head and neck is separated from its neighbours by a clear air gap (no head overlaps another
head or neck; the necks do not cross or touch above the chest). The tail lies on the ground behind the body and curls
in a gentle arc around toward the hydra's RIGHT side, its tip clear of the hind feet.

Do NOT: add wings, a rider, armour, extra legs, extra tails or extra heads (exactly five heads, five necks, four
legs, one tail); do not merge heads or cross the necks; do not change colours (blue-grey hide, silver ventral plates,
ivory horns/claws/spikes, red mouths, rust-brown head 5 and the rust frill of head 4); do not crop horns, crests,
claws or the tail.

Checks per image (re-run before selecting): exactly five heads, each with its own neck, in the stated order and with
its own crest/horn design; heads and necks separated by air; four legs with ivory claws; one tail on the ground with
a spike row; silver ventral plates on the necks and chest; spine spikes; transparent background; nothing cropped;
1536 x 1024; same pose and proportions as the primary; side views facing the stated direction (03_left faces image
LEFT, 04_right faces image RIGHT).
