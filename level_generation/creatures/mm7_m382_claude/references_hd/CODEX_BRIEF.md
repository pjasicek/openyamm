# Codex brief: HD reference views for the MM7 Rat (mm7_m382_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m382_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_rat_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite standing views, enlarged 3x with nearest neighbour,
   left to right: front, front three-quarter, profile (facing image right), rear three-quarter, back. Magenta is
   background. Design, anatomy and colour authority (tier A colouring).
2. `references_hd/native_palettes.png` — the three-quarter view in the three native palettes (the bare skin and the
   eyes change colour). Use the LEFT (mint-green skin, black eyes) colouring.
3. `references_hd/native_actions.png` — native walk and attack frames (side, front): legs and tail in motion. Anatomy
   evidence only.
4. `level_generation/creatures/mm7_m382/trimmed_2x/m382sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY (never the design).

## Deliverables (5 images, transparent background, 1536 x 1024 LANDSCAPE, unresized returns)
- `00_three_quarter.png` — front three-quarter from the rat's right (it faces toward image left-front), camera
  slightly above (primary; generate first; this image alone becomes the 3D mesh, so all four legs and the whole tail
  must be readable)
- `01_front.png`, `02_back.png`, `03_left.png` (its LEFT side: it faces image LEFT), `04_right.png` (its RIGHT side:
  it faces image RIGHT)
Freeze 00 once it passes the checks; then generate 01–04 in a separate step with 00 as the FIRST input so all five
show the same rat, pose and proportions. At most one corrective regeneration per view. Also write
`generation_runs.json` (id, prompt, inputs with sha256, output, selected flag, reason, superseded runs) and a
`selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII giant rat from the supplied original sprites, as a 3D modelling reference. Not a new design. Beautifully
detailed, credible fully three-dimensional creature with semi-realistic game materials and sharp fine detail (coarse
fur, bare wrinkled skin, claws, teeth), even soft neutral studio light, near-orthographic camera, the whole rat inside
the frame with margins (tail tip and claws included), transparent background, no floor, no cast shadow, no scenery,
no text.

Identity (from the native sprites): a monstrous giant rat. A large hunched BODY covered in coarse, matted DARK
CHARCOAL-GREY fur with a ridge of short spiky tufts along the spine, higher at the shoulders. The HEAD, the large
pointed EARS, all four LEGS (thin, bony, with long-clawed rat feet and dark claws) and the very long NAKED segmented
TAIL are bare wrinkled skin in a pale MINT-GREEN / greenish-white colour. A long pointed snout with long whiskers,
big glossy BLACK eyes, and an open mouth showing sharp white incisors and fangs.

Pose (identical in all five views, a neutral rigging pose based on the native standing sprite): standing on all four
legs, body low and hunched (back arched highest at the shoulders), legs slightly apart with clear gaps between them and
between left and right, feet flat; head forward, slightly raised, mouth open; the tail lying straight back and
slightly to one side along the ground behind, clear of the hind legs.

Do NOT: add armour, extra limbs, wings, horns, a second tail or glowing effects; do not make the fur brown or the skin
pink (pink is another tier); do not crop the tail or claws.

Checks per image (re-run before selecting): whole rat with the tail tip inside the frame; four separated legs; dark
grey fur body with a spiky ridge; mint-green bare head, ears, legs and tail; black eyes; incisors and fangs;
transparent background; same pose and proportions as the primary; side views facing the stated direction.
