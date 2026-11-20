# Codex brief: HD reference views for the MM7 Manticore (mm7_m278_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m278_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_rat_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite standing views, enlarged 3x with nearest neighbour,
   left to right: front, front three-quarter, profile (facing image right), rear three-quarter, back. Magenta is
   background. Design, anatomy and colour authority (tier A colouring).
2. `references_hd/native_palettes.png` — the three-quarter view in the three native palettes. Use the LEFT colouring.
3. `references_hd/native_actions.png` — native walk (side) and attack frames: tail and leg positions in motion.
   Anatomy evidence only.
4. `level_generation/creatures/mm7_m278/trimmed_2x/m278sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY (never the design).

## Deliverables (5 images, transparent background, 1536 x 1024 LANDSCAPE, unresized returns)
- `00_three_quarter.png` — front three-quarter from the manticore's right (it faces toward image left-front), camera
  slightly above (primary; generate first; this image alone becomes the 3D mesh, so all four legs and the whole tail
  must be readable)
- `01_front.png`, `02_back.png`, `03_left.png` (its LEFT side: it faces image LEFT), `04_right.png` (its RIGHT side:
  it faces image RIGHT)
Freeze 00 once it passes the checks; then generate 01–04 in a separate step with 00 as the FIRST input so all five
show the same manticore, pose and proportions. At most one corrective regeneration per view. Also write
`generation_runs.json` (id, prompt, inputs with sha256, output, selected flag, reason, superseded runs) and a
`selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII manticore from the supplied original sprites, as a 3D modelling reference. Not a new design. Beautifully
detailed, credible fully three-dimensional creature with semi-realistic game materials and sharp fine detail (short
fur, shaggy mane hair, glossy segmented chitin), even soft neutral studio light, near-orthographic camera, the whole
creature inside the frame with margins (tail tip and paws included), transparent background, no floor, no cast
shadow, no scenery, no text.

Identity (from the native sprites): a lion's body with a monstrous, almost human-like lion face and a giant SCORPION
TAIL. Body: lean muscular lion, short smooth pale TAN / greyish-beige fur, lighter belly, four lion legs with large
paws and dark claws. Head: broad flat face with a dark snout, small pointed ears, deep-set eyes, a wide open mouth full
of long white FANGS (upper and lower). A huge shaggy MANE of long coarse hair in pale SAGE-GREY-GREEN with dark MAROON
streaks and tufts underneath, covering the head, neck, chest and shoulders, hanging in jagged locks. Tail: a long
segmented scorpion tail of glossy brown-grey CHITIN plates (about eight bulbous segments, getting smaller toward the
tip), rising from the rump, arching high over the back and curving forward, ending in a curved STINGER that hangs down
above the shoulders.

Pose (identical in all five views, a neutral rigging pose based on the native standing sprite): standing square on
all four legs, legs straight and slightly apart with clear gaps between the legs and between left and right, paws
flat; head level, looking forward, mouth open showing the fangs; the tail arches up and over the back in a clean
C-shape in the body's middle plane (not to one side), the stinger hanging above and behind the head, clear of the
mane and the back.

Do NOT: add wings (the native manticore has none), horns, a second tail, armour or a rider; do not change colours
(pale tan body, sage mane with maroon streaks, brown-grey chitin tail, white fangs); do not crop the tail or paws;
do not let the tail touch the body except at its root.

Checks per image (re-run before selecting): whole creature with tail and stinger inside the frame; no wings; four lion
legs with separated paws; segmented scorpion tail arched over the back in the middle plane with a stinger; shaggy sage
mane with maroon streaks; open fanged mouth; tier-A colours; transparent background; same pose and proportions as the
primary; side views facing the stated direction.
