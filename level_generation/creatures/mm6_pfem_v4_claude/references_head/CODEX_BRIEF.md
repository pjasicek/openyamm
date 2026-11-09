# Codex brief: HD HEAD turnaround for the MM6 Female Peasant, v4 (mm6_pfem_v4_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_pfem_v4_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why: these views become a separate head-only 3D model (Meshy multi-image to 3D), grafted onto the existing body at
the neck. The previous 3D face was judged plain and unattractive. This head must be clearly PRETTY while staying the
same character: the New Sorpigal peasant woman of Might and Magic VI.

Use your built-in image generation. Record format as in
`level_generation/creatures/mm6_pfem_claude/references_head/generation_runs.json`. Attached inputs, in order:
1. `level_generation/creatures/mm6_pfem/native/pfemsta0.png` — ORIGINAL low-res game sprite, front: identity
   authority for hair colour, hairstyle, circlet and costume colours. The black/magenta background is not part of
   the character.
2. `references_hd/01_front.png` — accepted full-body HD front view of this character: head proportions, circlet,
   hair parting and neck.
3. `references_hd/04_right.png` — the same character from her right: skull depth, hair volume, the braid behind.
4. (Runs for 01–04 only) the selected `references_head/00_front.png` as the identity authority for the face.

## Deliverables (5 images, transparent background, square 1024 x 1024, unresized returns)
- `00_front.png` — head straight on (primary; generate first, in its own run)
- `01_three_quarter.png` — front three-quarter, turned 45 degrees toward the character's RIGHT (her right cheek
  toward the camera, so her face points to image LEFT)
- `02_left.png` — the character's LEFT profile: pure side view, her nose points to image RIGHT
- `03_back.png` — straight from behind
- `04_right.png` — the character's RIGHT profile: pure side view, her nose points to image LEFT
Generate 01–04 in a SEPARATE run with the selected 00 as input so all five are the SAME head, expression, hair.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Allow at most ONE corrective regeneration per view.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME CHARACTER, HD HEAD MODELLING REFERENCE: head-and-neck reference of the EXISTING
Might and Magic VI female peasant (New Sorpigal villager), for building her 3D head. Same character as the inputs,
shown large and with a clearly beautiful face.

Framing: head and neck only, like a sculpted bust WITHOUT shoulders. The neck ends in a clean straight horizontal
cut a little below the jaw (no shoulders, no clothing). Her braid continues down behind the neck and is cut at the
same height. The head including all hair fills about 75% of the frame height, centred, generous transparent
margins. Near-orthographic camera at eye height, head level, no tilt. Transparent background, no floor, no shadow,
no text. Even soft neutral studio light that still shows the form (no dramatic shadows, nothing baked into colour).
Realistic, finely detailed game character sculpt and texture: clean skin with subtle pores, individual hair strands.

Face (the important part): a beautiful young woman of about 22, kind and gentle, the kind of face a player finds
pretty at first glance. Soft oval face, smooth gently rounded jaw and small softly pointed chin, high soft
cheekbones, slender straight nose with a small rounded tip, large bright almond-shaped hazel-green eyes with clear
whites, light upper lids and soft lashes, gracefully arched natural brows (not heavy), naturally full rosy lips,
closed, with the faintest warm smile. Fair, clear, even skin with a healthy warm glow, only a very light dusting of
freckles across the nose. Symmetric, youthful, no harsh lines, no stern or tired look. Ears small and neat.

Identity kept from the inputs: chestnut-auburn hair parted in the middle and smoothed back over the head, gathered
into ONE long thick braid hanging down the back; a few soft loose wisps at the temples are fine. A thin plain GOLD
circlet band across the forehead and around the head, sitting just above the brows' level on the forehead.

Do NOT: change the expression between views; change hair colour or style; open the mouth or show teeth; add
jewellery other than the circlet, makeup, hats or clothing; make her look older, gaunt, sharp-jawed or masculine;
crop the hair or the braid; loosen the braid.

Checks per image (re-run before selecting): pretty, youthful, gentle face; middle parting; ONE braid at the back;
thin gold circlet; hazel-green eyes; closed lips; neck cut cleanly below the jaw with no clothing; transparent
background; for 01–04 the same face as 00 and the profile facing the stated side.
