# Codex brief: HD reference views for the MM7 Behemoth (mm7_m162_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m162_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_rat_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite standing views, enlarged 3x with nearest neighbour,
   left to right: front, front three-quarter, profile (facing image right), rear three-quarter, back. Magenta is
   background, not creature. Design, anatomy and colour authority (tier A, green mane).
2. `references_hd/native_palettes.png` — the same three-quarter view in the three native palettes. Use the LEFT
   (green mane) colouring. Only the mane/beard changes colour between tiers.
3. `references_hd/native_actions.png` — native walk (side) and attack (front) frames: shows the arms, claws and legs
   in motion. Anatomy evidence only.
4. `level_generation/creatures/mm7_m162/trimmed_2x/m162sa1.png` — restored 2x three-quarter frame, for SURFACE
   MATERIAL ONLY (never the design).

## Deliverables (5 images, transparent background, 1024 x 1536 PORTRAIT, unresized returns)
- `00_three_quarter.png` — front three-quarter from the creature's right (it faces toward image left-front), camera at
  chest height, slightly above (primary; generate first; this image alone becomes the 3D mesh)
- `01_front.png` — facing the camera
- `02_back.png` — seen from behind
- `03_left.png` — the creature's LEFT side: it faces image LEFT
- `04_right.png` — the creature's RIGHT side: it faces image RIGHT
Freeze 00 once it passes the checks; then generate 01–04 in a separate step with 00 as the FIRST input so all five
are the SAME creature, SAME pose, SAME proportions. At most one corrective regeneration per view.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Behemoth from the supplied original sprites, as a 3D modelling reference. Not a new design. Beautifully
detailed, credible fully three-dimensional creature with semi-realistic game materials and sharp fine detail, even
soft neutral studio light (no dramatic lighting, no rim light), near-orthographic camera, ONE complete creature from
the top of the mane to the soles of the feet and the claw tips, centred with generous margins, transparent
background, no floor, no cast shadow, no scenery, no text.

Identity (from the native sprites): a huge hunched ape-like beast, heavier than a gorilla. Enormous rounded shoulders
and upper back, the small head set LOW and FORWARD between the shoulders (no visible neck). Broad snout-like face
with a heavy underbite jaw: big curved ivory FANGS/tusks pointing up from the lower jaw and down from the upper jaw,
a dark mouth, a flat dark nose, small deep-set glowing ORANGE-RED eyes under a heavy brow. Long massive arms, each
forearm thick, each hand a short heavy paw ending in THREE very long curved IVORY claws (sickle-shaped, as long as the
forearm, slightly rust-red at the tips), claws clearly separated. Short thick bowed legs, large flat feet with short
ivory toe claws. Skin: thick lumpy grey-beige hide like weathered stone/elephant skin with knobbly folds, paler
highlights on the shoulders and arms; the chest and belly are a darker recessed blue-grey charcoal. A shaggy GREEN
mane of long coarse hair covers the top of the head, the upper back and the tops of the shoulders, and a green beard
hangs under the jaw onto the upper chest. No clothing.

Pose (identical in all five views, a neutral rigging pose based on the native standing sprite): standing on both
feet, feet about shoulder-width apart with a clear gap between the legs, knees only slightly bent; the torso leans
forward about 25 degrees (less hunched than the native sprite, so the chest and belly are visible from the front);
head forward and level, looking ahead. Arms hang DOWN and OUT from the body, about 35 degrees away from the torso
(an A-pose), elbows only slightly bent, hands clear of the legs and torso with air between them, palms facing the
thighs, the three claws fanned slightly apart and pointing down and a little forward; claw tips stay ABOVE the
ground plane (not touching the ground).

Do NOT: add armour, clothing, weapons, a tail, horns, wings, extra limbs, extra claws (exactly three long claws per
hand), glowing effects or blood; do not make it a bear, a minotaur or a juggernaut; do not change colours (grey-beige
hide, dark blue-grey chest, green mane and beard, ivory fangs and claws, orange eyes); do not crop the mane, claws or
feet.

Checks per image (re-run before selecting): whole creature with claw tips and feet inside the frame with margins;
exactly three long claws per hand, separated; arms clear of the body (A-pose); gap between the legs; green mane on
head, back and shoulders plus beard; fangs; orange eyes; grey-beige hide with darker chest; transparent background;
same pose and proportions as the primary; side views facing the stated direction.
