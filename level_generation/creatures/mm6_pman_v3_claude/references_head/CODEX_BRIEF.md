# Codex brief: HD HEAD turnaround for the MM6 Male Peasant, v3 (mm6_pman_v3_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_pman_v3_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why: these views become a separate head-only 3D model (Meshy multi-image to 3D), grafted onto the body at the
neck. The previous 3D head was weak (soft, heavy-browed, stern). This head must be a better, well-defined,
likeable face while staying the same character: the New Sorpigal peasant man of Might and Magic VI.

Use your built-in image generation. Record format as in
`level_generation/creatures/mm6_pman_claude/references_head/generation_runs.json`. Attached inputs, in order:
1. `level_generation/creatures/mm6_pman/native/pmansta0.png` — ORIGINAL low-res game sprite, front: identity
   authority for hair colour, haircut and costume colours. The black/magenta background is not part of the
   character.
2. `references_hd/01_front.png` — accepted full-body HD front view of this character: head proportions, hair and
   neck.
3. `references_hd/04_right.png` — the same character from his right: skull depth and hair volume.
4. (Runs for 01–04 only) the selected `references_head/00_front.png` as the identity authority for the face.

## Deliverables (5 images, transparent background, square 1024 x 1024, unresized returns)
- `00_front.png` — head straight on (primary; generate first, in its own run)
- `01_three_quarter.png` — front three-quarter, turned 45 degrees toward the character's RIGHT (his right cheek
  toward the camera, so his face points to image LEFT)
- `02_left.png` — the character's LEFT profile: pure side view, his nose points to image RIGHT
- `03_back.png` — straight from behind
- `04_right.png` — the character's RIGHT profile: pure side view, his nose points to image LEFT
Generate 01–04 in a SEPARATE run with the selected 00 as input so all five are the SAME head, expression, hair.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Allow at most ONE corrective regeneration per view.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME CHARACTER, HD HEAD MODELLING REFERENCE: head-and-neck reference of the EXISTING
Might and Magic VI male peasant (New Sorpigal villager), for building his 3D head. Same character as the inputs,
shown large, with a strong, well-defined, likeable face.

Framing: head and neck only, like a sculpted bust WITHOUT shoulders. The neck ends in a clean straight horizontal
cut a little below the jaw (no shoulders, no collar, no clothing). The head including all hair fills about 75% of
the frame height, centred, generous transparent margins. Near-orthographic camera at eye height, head level, no
tilt. Transparent background, no floor, no shadow, no text. Even soft neutral studio light that still shows the
form (no dramatic shadows, nothing baked into colour). Realistic, finely detailed game character sculpt and
texture: skin with natural pores, individual hair strands.

Face (the important part): a good-looking working man of about 30, honest and friendly, the kind of villager a
player trusts. Clearly defined bone structure: straight brows of moderate weight (not a heavy frown), clear
blue-grey eyes with relaxed lids, straight nose, defined cheekbones, clean squared jaw and chin, natural lips
closed with a calm, faintly pleasant expression. Healthy lightly tanned skin from outdoor work, clean-shaven with at
most a faint shadow of stubble. Symmetric, alert, not stern, not tired, not scowling. Ears natural and neat.

Identity kept from the inputs: short tousled copper-auburn hair, fuller on top, short at the sides and back,
ears uncovered.

Do NOT: change the expression between views; change hair colour or cut; add a beard or moustache; open the mouth or
show teeth; add jewellery, scars, hats or clothing; make him look older, gaunt or angry; crop the hair.

Checks per image (re-run before selecting): likeable defined face, not stern; short copper-auburn hair, ears
visible; clean-shaven; closed lips; neck cut cleanly below the jaw with no clothing; transparent background; for
01–04 the same face as 00 and the profile facing the stated side.
