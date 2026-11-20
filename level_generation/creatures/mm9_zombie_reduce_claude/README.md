# MM9 Zombie (`mm9_zombie`, Rotter / Dripper / Zombie) reduction: candidate i r55 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 monster,
relaxed keep set), ledger row 51 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:zombie` (owner
zombie-reduce-20261104). Source: the installed `assets_source/worlds/mm9/models/mm9_zombie.glb` (sha256 cabff291d0b6, identical
to `../mm9_zombie_claude/export/mm9_zombie.glb`), copied to `before/` (the rollback source). No Meshy, no credits, no repaint.
**Not installed.** `../mm9_zombie_claude/` was only read.

| | LOD0 | body `Zombie_A` (limbs, hands, trousers, bones) | head `ZombieHead_A` | torso `ZombieTorso` | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 11,060 | 3,628 | 4,694 | 2,738 | 5,505 | 1,951 | 621 |
| **i r55 (`export/mm9_zombie.glb`, sha256 918c4e53bf57)** | **8,570 (-22.5 %)** | 2,440 | 4,310 | 1,820 | 4,255 | 1,503 | 493 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips, skin, nodes, materials, `KHR_materials_variants` (every LOD and shadow primitive), all 15 images:
byte-identical (`same_clips.py`). The face is the installed triangles: `scripts/face_exact.py` finds every face-skin (1,250),
teeth (760), eyes (96), skull plug (80), neck-ring (44) and rope (240) triangle unchanged with identical attributes; the face diff
sheets are black on the face in every tier and view.

## Labels and keep set (`scripts/glb_parts.py`, `make_sets.py`; `review/class_sheet_a.png`)
Classes per connected piece of each primitive (faces3.npz part labels by majority; the head moved after faces3, so pieces, not
faces, carry the label): body = trousers 1,400, arms 508, hands 976, bony right foot 460, shin bone 240, neck bits 44; head =
skin 3,241 split by the head region mask (G skin -> **face** 1,250: face, ears, jaw, chin, neck; R hair / B crown -> **scalp**
1,991, the painted hair mass), hair locks 517, teeth 760, eyes 96, plug 80; torso = chest 1,460, tatter 519, its lining 519
(export_zombie's reversed copy 1.5 mm inside), rope 240.
- **Exact:** face, teeth, eyes, plug, neck bits, rope, pieces of up to 60 faces, soles (below 2 cm), the neck seam (2 cm round
  the head ring welded onto the body), the hairline (scalp/hair within 8 mm of the face), hand faces that touch the other hand in
  any frame (3.5 cm, `hand_hand.py`, 105), trousers under the hands (3 cm in every clip, 6 cm in Death2: `hand_contact.py`, 121).
- **Groups:** hands 0.65 (every finger kept), hair locks 0.65, scalp 0.8, tatter 0.7 (lining re-emitted from the cut outer
  faces' twins: position - 1.5 mm x normal, same UV; at ratio 1 the rule rebuilds all 519 installed lining faces exactly),
  bones 0.75; trousers, arms, chest take the ladder ratio.
- **Texture guard** (mpqem `tex_ok`, 100 / 45): body and head on base colour + region mask (tiers are ramps on one image),
  torso on its three tier base colours.

## Ladders (`scripts/mpqem.py`, pose-aware half-edge collapse over 10 Hz poses of every clip; limits for 1.795 m: p99 <= 5.38 mm,
max <= 26.9 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | step | LOD0 | p99 / max mm (worst) | | result |
|---|---|---|---:|---|---|---|
| a | scalp 0.7 | r60 / r50 / r40 | 8,474 / 8,162 / 7,942 | 4.56/15.3, 6.52/34.6, 10.8/42.7 | | r60 pass: a hard shading step on the side of the hair in profile; arm/hand Taunt L 0 -> 3.1 cm, ResurrectSpell L 3.4, Death2 L 2.1, Taunt/ResurrectSpell R 1.4 |
| b | scalp 0.8 | r60 / r55 | 8,636 / 8,478 | 4.17/15.3, 5.01/20.1 | | pass; hair as installed; same arm/hand regressions |
| c, d, e | + all body faces near the hands, + knee/hip helper faces | r55-r40 | 8,700-9,114 | max 26.95-35.5 | | fail: the keeps moved the error to the knee backs and groin (`*_h` helpers) |
| f | b + head faces near the hands | r55 | 8,568 | 5.0/20.1 | | pass, no gain: the Taunt depth was the left pinky against a merged right ring-finger tip |
| g | b + hand-to-hand faces | r55 | 8,514 | 5.02/20.1 | | pass; Death2 L 2.1 cm (hand behind the left knee) left |
| **i** | **g + trousers under the hands** | **r55** | **8,570** | **5.26/24.5 (AttackRanged:12)** | IoU .989, SSIM .996 | **PASS, picked**: every arm/hand value equal or better |

## Gates, installed -> i r55 (`scripts/gates.sh`: the Zombie's own gate scripts; `review/gates_before/`, `review/gates_i55/`, `review/gates_compare_i55.txt`)
- Arm/hand (`--outer-only --exact`): hand depth equal in every clip; forearm Wakeup L 0.4 -> 0.0, R 5.2 -> 5.1, Wakeup2 L 0.7 -> 0.0,
  R 2.7 -> 2.6 cm; finger stretch equal or lower.
- Collapse face-frames 21,925 -> 17,319 (groin/knee/ankle counts down in most clips); worst-frame counts up by one or two:
  armpit_L 0 -> 1 (Hit2, Death2), elbow_R 0 -> 1 (Resurrect, Death2), AttackRanged body 7 -> 9; Taunt 1,912 -> 1,936,
  ResurrectSpell 1,155 -> 1,169 face-frames.
- Cloth (thighs through the tatter): AttackMelee and AttackRanged2 0.2 cm (7 f) -> 0; script clips Death2 24 -> 27 frames
  (19.9 -> 19.7 cm), Wakeup 94 -> 90, Wakeup2 94 -> 91 frames (19.9 -> 20.0 cm): the installed model's own Wakeup/Death2 failure.
- Jitter 8 fails before and after (clips identical). Bone lengths 0 stretching. Winding 0. Flat shading 0.00 / 0.00 / 0.00
  (torso 0.01 before). Detached: the same three shallow parts. Texture quality: body stretch p90 1.09 -> 1.13; head density
  spread 1.50 -> 1.78 (p10 440 -> 373 px/m: larger scalp triangles), torso unchanged.
- LODs (`lod_check.py`, every frame of every clip; `work/lod_check_{installed,i55}.json`, protected sole/crown/corpse points,
  `scripts/build_lods.py`): height 1.7947 m at every LOD (installed 1.7947 / 1.7926 / 1.7924 / 1.8016); faces stretched over 20x
  4 / 0 / 0 / 0 (installed 4 / 0 / 1 / 0); Dead 0.0 cm at every LOD (installed LOD1-3 +0.1 / +0.2 / +0.2); every LOD's lowest
  point now equals LOD0's (installed LOD2/3 sat up to 0.9 cm higher in Standing/Walking).

## Review
Viewer (installed and reduced, every tier, all 19 clips; `run_creature_review.py check`: 114 switches, 0 failed, 0 console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_zombie_reduce_claude/review/viewer/ (models `inst_a/b/c`, `red_a/b/c`;
ramps baked into the viewer copies by `scripts/viewer_tiers.py` as the creature's own viewer does).
Sheets read: `review/sheet_face_diff_i55.png` (front close-up, 3/4, profile, low 3/4, party; installed | reduced | diff x4; every
tier), `review/sheet_body_i55_{a,b,c}.png` (Standing front/3-4/back, Walking, AttackMelee, Death), `review/close_i55_{a,c}_{1,2}.png`
(hands, tatter front/back/Walking, bony foot and shin, back of the head, nape, Death torso), `review/hair_i55_a.png`,
`review/taunt_hands.png` (a60/b55 history), `review/ladder_sheet_i.png`. Written, not read: `review/sheet_face_i55.png` (same shots as the diff sheet).
Look at: the hair mass in profile (scalp at 0.8: a faint shading line remains on the side, much weaker than ladder a's step), the
chest and vest pattern (larger triangles interpolate the normal-map tangent frame a little differently), the hands at 65 %.

## Build
`scripts/reproduce.sh` (import_source -> dump_mesh -> glb_parts -> tex_extract -> make_sets a -> hand_hand / hand_contact ->
make_sets i -> run_mp.sh i 0.55 -> build_mp.sh: swap_mp -> build_lods (protected points) -> the creature's shrink_shadow_lods ->
carry_variants -> the creature's fix_winding -> check_winding). Gates: `scripts/gates.sh export/mm9_zombie.glb <tag>`,
`gate_compare.py <tag>`; LODs: `REA_NODE=Zombie blender -b -P scripts/lod_check.py -- <glb> <label>`; viewer: `viewer_tiers.py`,
`make_viewer_manifest.py`, `shots.sh`, `close_shots.sh` (own `viewer_shots.mjs` copy with a 180 s ready timeout: the 42 MB
viewer GLBs did not load within 30 s on the loaded machine), `shot_sheets.py`, `face_diff_sheet.py`, `pair_sheet.py`.

Install (on the user's OK only): `check_winding.py export/mm9_zombie.glb` (0), `python3 tools/install_model.py
level_generation/creatures/mm9_zombie_reduce_claude/export/mm9_zombie.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, the ledger row, and the line in `../mm9_zombie_claude/README.md`:
"LOD0 reduced post-install on <date> by `mm9_zombie_reduce_claude`; a rebuild from this project must re-run that reduction".
Rollback: `before/mm9_zombie.glb`.

## Not checked
In game (not installed; the binding regression and floor audit read the installed file); motion at normal speed (frames,
gates and viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); the Dripper's close-ups by eye (body and face diff
sheets only); the bony foot and shin rebuilt low-poly with a bake (cut at 0.75 instead: 700 faces, a rebuild would
save at most ~300).
