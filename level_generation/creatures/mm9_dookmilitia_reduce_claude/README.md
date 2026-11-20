# MM9 Half-Orc (`mm9_dookmilitia`) reduction: fix pass m155b ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set,
"UV chart audit is a hard gate"), ledger row 33. Lease `mm9reduce:dookmilitia` (`mm9:dookmilitia` free). Rollback source
`before/mm9_dookmilitia.glb` (sha256 8a60c4575c2e) = the installed r19 again (cmp-identical after the rollback). No credits.
**Nothing installed.**

| | LOD0 | limbs / torso / head / sword | LOD1 / 2 / 3 |
|---|---:|---|---|
| installed r19 | 12,906 | 3,288 / 5,370 / 3,918 / 330 | 6,442 / 2,314 / 769 |
| **m155b, fix pass (`export/mm9_dookmilitia.glb`, sha256 ebd178434414)** | **10,168 (-21.2 %)** | 2,224 / 4,146 / 3,468 / 330 | 5,071 / 1,822 / 603 |
| c479p, first pass (installed, then rolled back; deleted) | 10,176 | 2,080 / 4,298 / 3,468 / 330 | 5,087 / 1,826 / 604 |

LOD0 alone: `export/mm9_dookmilitia_lod0.glb`. UV audit: `review/uv_audit.json`.

## Fix pass (2026-11-04): chart guard, UV audit 0
The first pass (c479p, MeshLab texture-aware quadric, new vertices with interpolated UVs) was installed and rolled back: the
shared `reduction_uv_audit.py` found **73 LOD0 faces off the painted charts** (limbs 39, torso 29, head 5: inner thighs and
calves, ankles, both fists, the sleeve seam under the shoulder caps, chest/belly seams; colour error up to 52), visible as
1-5 cm texture wedges in close-up (`review/uv_close_old_c479p/closeups.png`).
- Reducer replaced by the pose-aware half-edge collapse with the chart guard (`scripts/mpqem.py`, from
  `mm9_lizardorc_reduce_claude` / `mm9_imp_reduce_claude`, `MP_CHART=1`): every output corner is an installed vertex (position,
  UV, normal, joints, weights exact), every collapse is scored over all 22 clips at 10 Hz plus a 5-D position/UV quadric,
  refused if any sample of a new face's UV triangle leaves the installed charts, and refused by the texture guard when a new
  face samples colours the source does not have there in any of the three tier paints (`scripts/tex_extract.py`;
  MP_TEX_MAX 100, MP_TEX_MEAN 45). UV seams, open boundaries and kept faces are locked; the sword primitive is kept whole.
- Same keep set as the first pass (C4, `make_sets.py` -> `glb_sets.py`): face/eyes/neck, hood rim, graft junction, grip
  contact, linings, small pieces, buckle, shoulder caps, cuffs, boot rims, arm contacts, soles exact; hood 0.6, skirt 0.75,
  hands 0.6 / 0.65 (`MP_GROUPS=1:0.6,2:0.75,3:0.6,4:0.65`); the ladder ratio is the rest (tunic, sleeves, pants, boots, mantle).
- Ladders (`scripts/run_mp.sh`, limits p99 5.96 / max 29.8 mm, IoU .98, SSIM .93):
  - M1 (C4): r70 10,724 p99 3.03, r60 10,338 p99 3.80, **r55 10,146 p99 4.69 / max 17.2 (Cower:45), IoU .993, SSIM .994 PASS**,
    r50 9,972 p99 9.06 fail; M2 r53 p99 6.13 fail, r52 7.05 fail. (GLB counts are 22 higher: the 20 zero-area collar faces and 2 others Blender drops.)
  - MA/MB (relaxed: cuffs, caps, buckle, boot rims cut): r60 9,950 PASS, **r57 9,806 PASS** (p99 4.86), r55 fail. Built as mb57
    (9,828, audit 0) and rejected by eye: GLB clay close-ups show a fold at the right cuff, hard creases along the shoulder caps'
    rims and dents at the boot rims (`review/sheet_detail_clay_mb57.png`); the same parts the first pass had to keep.
  - Picked **M1 r55**: GLB clay and texture close-ups match the installed model at cuffs, caps, buckle, boot rims and fists
    (`review/sheet_detail_clay_m155.png`, `review/sheet_body_tex_m155.png`).
- Export (`scripts/build_mp.sh`): `swap_mp.py` (index buffers into the installed LOD0, attributes byte for byte, unused
  vertices dropped) -> `floor_points.py` -> `build_lods.py` (tools/build_actor_lods.py, 4 influences, default ratios; protected
  soles, top, and the corpse contacts within 3 cm of the floor at the lowest key of Death, Death2 and Dead, each point snapped
  to the imported vertex nearest to it: 78 of 78 mapped, worst 7e-6 m; `CLIPS=Death,Death2,Dead CORPSE_LOW=0.03`) ->
  shrink_shadow_lods -> carry_variants -> fix_winding -> check_winding 0 -> `same_clips.py` (clips, skin, nodes, materials,
  variants, 22 images identical) -> UV audit.
- **UV audit (`claude_shared/reduction_uv_audit.py`, `review/uv_audit.json`): LOD0 0 escaping faces in every primitive.**
  LOD1/2/3 (Blender's decimate, as the creature was built): limbs 133/120/69 (installed 80/113/76), torso 167/133/59 (122/146/71),
  head 74/73/52 (77/85/62), sword 0. LOD1 has about 50 more than the installed LOD1 on limbs and torso; not a gate.
- Close-ups at the first pass's escape clusters, installed vs fix pass, every tier (`review/uv_close_m155_at_old/closeups.png`, rendered
  for mb57 at the same clusters as `review/uv_close_mb57_at_old/closeups.png`): the wedges are gone; the reduced cells match the source.
- `face_exact.py`: all 2,418 face/eye/neck triangles present (positions and UVs exact, normals 0.03 deg); viewer face shots
  front, profile and low 3/4 pixel-identical in every tier (max difference 0), the 3/4 differs only on helmet and mantle.

### Gates, installed r19 -> m155 (`review/gates_before/`, `review/gates_m155/`, `review/gates_compare_m155.txt`)
LOD0 of m155 and m155b is identical (checked); m155b only differs in its LODs.
| Gate | r19 | m155 |
|---|---|---|
| Arm/hand (cloth and skin) | every clip <= 0.6 cm | identical (no clip changes by 0.2 cm) |
| Jitter vs MM9 clips / same mesh | 6 / 6 fails (Running, BackpedalRun, Death) | 6 / 6, values within 0.05 |
| Collapse face-frames | 44,315 | 34,869; no region worse by 3 or newly at 20+ |
| Skirt, cloth through torso, sword | as README of the creature | identical in every clip |
| Grip | inside <= 0.5 cm | inside identical; wrap one 15-deg step less on ring (15 clips), pinky (5), index (1); min pinky 150 -> 135 |
| Detached, bones, winding, flat | 0, 0 of 12, 0, 0.00-0.01 | identical |
| Texture quality | limbs atlas 57.9 %, fragments 0.0 % | 57.9 %, 0.0 % (no new UV islands) |
| Floor | Dead 0.00 cm | Dead +0.23 cm (corpse 2 mm higher); every other clip identical |
| LODs (`lod_check.py`) | LOD3 Standing +3.3 mm, Death -4.0 mm | LOD1-3 lowest point equal to LOD0 (within 0.1 mm) in every clip except LOD3 Death2 -7.7 mm; Standing 0.0 at every LOD; top 1.9863 at every LOD (LOD0 r19 1.9871); LOD0 2 faces stretched over 20x (r19 4), LOD1-3 0 |

Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_dookmilitia_reduce_claude/review/viewer/ (installed and m155b,
every tier; check: 132 switches, 0 failed, 0 console errors).
Sheets read: `review/uv_close_old_c479p/closeups.png`, `review/uv_close_mb57_at_old/closeups.png`,
`review/sheet_viewer_face_{a,b,c}.png`, `review/sheet_viewer_body_{a,b,c}.png` (m155b), `review/sheet_face_tex_m155.png`,
`review/sheet_body_tex_m155.png`, `review/sheet_full_tex_m155.png`, `review/sheet_detail_clay_m155.png`,
`review/sheet_detail_clay_mb57.png`, `review/sheet_body_tex_mb57.png`, `review/sheet_body_clay_mb57.png`, `review/uv_close_m155_at_old/closeups.png`.
Not checked (fix pass): in game; motion at normal speed; LOD1-3 by eye; gates on m155b itself (LOD0 identical to m155).

## First pass (2026-11-04, superseded): MeshLab ladder, candidate c479p
## Protected share (measured first)
Part labels from the creature's final rest mesh (`../mm9_dookmilitia_claude/work/final_v1.blend`: `part`, `hand`, `lining`,
`graft_s`), triangulated by `scripts/dump_final.py` and matched to the GLB faces exactly (`scripts/glb_parts.py`, centroid
distance 6e-8 m; plot `review/parts_full.png`, `review/parts_head.png`). The body was already cut per garment at the build
(`clean_dook.py`: boots 0.55, pants 0.66, mantle 0.7), so it behaves like the MM6 Dwarf ("already-reduced bodies"): the
surface error spreads evenly over thighs, calves, spine and upper arms (`region_error.py`), and locks only move it.
- Full keep set (face, hands, sword, linings, small pieces, soles): 46 %. Relaxed set with hands as groups: 37.5 %.
- Picked set C4 (`scripts/make_sets.py`, 48 % kept, 6,161 of 12,886 welded faces):
  - **Exact:** face skin with ears and neck (part 20), eyes (22), the old neck V (2); body faces within 3 cm of the face skin
    (neck seam); hood faces within 1 cm of the face skin (the hood's rim round the face); the hand-graft junction (graft_s) and
    the sword grip contact (`scripts/grip_contact.py`, 254 faces); the sword (330, too small to rebuild for gain); soles; every
    lining (mantle, shoulder caps, collar well, 862); small pieces up to 90 faces (cheek bars, helmet spikes, buckle loops);
    the belt buckle (part 10) and the shoulder caps (13) whole; sleeve cuffs within 8 cm of the wrists; the boot rims (top 4 cm);
    arm-to-body contact faces (`scripts/arm_contact.py`: body faces within 2 cm of a forearm/hand and arm faces within 2 cm of
    the body, every 2nd key of every clip; 363).
  - **Own ratio:** hood/helmet shell 0.6, skirt 0.75, left hand 0.6, right hand 0.65 (every finger kept, grip contact exact).
  - **Shared texture-aware cut:** tunic, sleeves, pants, boots, mantle outer strips, belt.
- Weights: source vertices keep their exact weights; new vertices take the source triangle that contains their UV
  (`REA_WEIGHTS=component`, `uv_weights.py`). The import weld merges only identical weights (0 coincident pairs); 20 degenerate
  collar-well faces (zero area) vanish in the weld.

## Ladders (`scripts/run_ladder.sh`; limits for 1.985 m: p99 <= 5.96 mm, max <= 29.8 mm, IoU >= .98, SSIM >= .93)

| set | what changed | passing step | first failing step |
|---|---|---|---|
| A | relaxed set, helm 0.65, hands 0.7, skirt 0.8 | r74 9,532 (p99 5.70, max 27.7) | r70 9,016 (p99 7.83) |
| B | A + cuffs, boot rims, buckle kept, caps 0.85 | r80 10,304 | r77 9,918 (p99 6.09, max 38.7 Running) |
| C | B + arm contact, helm 0.55, L hand 0.65 | r79 10,174 | r78 10,046 (max 38.9 Cower, knees) |
| Ce | C + err-lock 2 cm round 19 knee/groin misses | r79 | r78 p99 6.34: the lock moves the error |
| C2 | C, helm 0.4, hands 0.6/0.65, skirt 0.75, caps 0.8 | r77 9,920 | **rejected by eye:** a notch in the helmet's brim band (front close-up) |
| C3 | C2 with helm 0.6 | r78 10,048 (p99 5.65) | gates: same-mesh jitter Hit2 R 2.02 mm/f2 (limit 2.0), more shoulder folds |
| **C4** | C3 with the shoulder caps kept exactly | **r79 10,176 (p99 5.42, max 25.5 Cower:33; IoU .992, SSIM .994)** | r78 p99 5.96 / max 38.9 |
| C5 | C4 + knees (7 cm round the calf joints) kept | r80 | r79 max 38.7: moves the error |

Why C4 r79 and not A r74 (-26 %): A cut the cuffs, buckle, boot rims and shoulder caps; GLB clay close-ups show dents at both
cuff rims beside the fists, a thinner buckle, a dent at the boot rim and faceted caps (`review/sheet_hands_clay_a74.png`,
`review/sheet_body_clay_a74.png`), and the arm gate's Sleep left forearm went 0.0 -> 1.1 cm into the body (over its 1 cm line).
a74 is kept as the alternative if the user prefers the count.

## Export (`LOD_PROTECT=1 REA_BLEND=ladder_C4.blend scripts/build_export.sh Cand_79 <name>`)
export_cand (floor = the source's lowest point; MM9 rig, the mesh sits 0.9917 m below its rig node: 0 lifted) -> `swap_lod0.py`
(joints written as the installed u8) -> `fix_normals.py` (installed normals on every source vertex; new vertices take the
installed normals interpolated on the source triangle that contains their UV, fallback the nearest same-facing source vertex:
the installed normals are Blender's export, the area-weighted rule is 2-6 deg off them; sword primitive restored byte for byte)
-> `scripts/build_lods.py` (`tools/build_actor_lods.py` generate, 4 influences, default ratios, with the sole contacts and the
Death/Dead corpse contacts protected, `floor_points.py`) -> `shrink_shadow_lods.py` -> `carry_variants.py` (16 primitives) ->
the creature's `fix_winding.py` (3 collapsed bits flipped) -> check_winding 0. `same_clips.py`: clips, skin, nodes, materials,
variants and the 22 images identical to the installed file. `face_exact.py`: all 2,418 face/eye/neck triangles present with the
same positions (2.5e-7 m), UVs (0) and normals (0.03 deg, float round trip); hood/helmet 1,500 -> 1,050.

## Gates, installed r19 -> c479p (`scripts/gates.sh`: the creature's own `gates_run2.sh` set, run from its project;
`review/gates_before/`, `review/gates_c479p/`, comparison `review/gates_compare_c479p.txt` by `scripts/gate_compare.py`)

| Gate | r19 | c479p |
|---|---|---|
| Arm/hand (48 fps, cloth and skin) | every clip 0.0-0.6 cm | identical except **Sleep L forearm 0.0 -> 0.6 cm** (under the 1 cm line; a74 1.1) |
| Jitter vs MM9 clips (`dook_clips0.glb`) | 6 fails (Running, BackpedalRun, Death; shoulder skin) | 8: + AttackMelee R 0.91 -> 2.11, Hit2 L 0.94 -> 3.79 mm/f2 |
| Jitter, same mesh (`ref_swap.py`: each mesh with MM9's clips) | 6 fails | **6, the same**; Hit2 R 1.80 -> 1.82, AttackMelee R 0.91 -> 0.25. The standard gate's two new fails are the 95th percentile of a different vertex population (the Lizard-Orc lesson) |
| Collapse (face-frames, all clips) | 44,315 | 36,391; shoulder counts up 1-7 in most clips (AttackRanged L 15 -> 20, Cower 8/12 -> 15/17, Taunt2 15/8 -> 19/13, Hit R 44 -> 47, Death L 48 -> 50); those at 20+ already failed on r19. Clay at the worst frames (`review/sheet_shoulders_clay_c479p.png`): no tear, slightly more facets on the sleeve under the cap |
| Skirt (thighs through the skirt) | Cower 58/145 frames, 0.9 cm | 53/145, 0.9 cm; every other clip unchanged |
| Cloth through torso | 0.0 everywhere | 0.0 everywhere |
| Sword vs skin (blade gate) | Sleep 0.6 cm, others <= 0.1 | identical |
| Grip | inside <= 0.5 cm | inside identical; wrap one 15-deg step less on the thumb (18 clips) or ring finger (12), min wraps unchanged (thumb 90, ring 165) |
| Detached parts | 0 | 0 |
| Bone length, handedness, orient, winding | 0 of 12, right, -, 0 | identical |
| Flat shading | body 0.00-0.01, sword 0.07 | 0.00, 0.07 |
| Texture quality | limbs atlas 57.9 %, fragments 0.0 % | 56.1 %, 1.3 % (decimated UV islands); head/torso within 1 % |
| Floor (clip_floor) | Dead 0.00 | Dead +0.12 cm (corpse 1 mm higher); the rest equal |
| LODs (`lod_check.py`, every frame) | LOD3 Standing +3.3 mm, Death -4.0 mm under LOD0's low | LOD1/2 lowest points equal to LOD0 in every clip; LOD3 Standing 0.0, **Death -9.3 mm** (mid-fall), Dead 0.0; tops within 5 mm; LOD2 one face over 20x stretch in most clips (r19: LOD1 one) |

## Sheets (read)
Viewer, installed (left) vs c479p, every tier: `review/sheet_viewer_face_{a,b,c}.png` (front close-up, 3/4, true profile, low
3/4, party; the face skin is pixel-identical in the diff `review/diff_face_f1_a.png`, differences only on helmet and mantle) and
`review/sheet_viewer_body_{a,b,c}.png` (Standing front/3-4/back, Walking, AttackMelee). GLB renders (tier A, Blender):
`review/sheet_tex_c479p.png` (face, helmet, full body, walk, attack 3, hit 2, death, cower, sleep), `review/sheet_body_clay_c479p.png`,
`review/sheet_shoulders_clay_c479p.png`, `review/sheet_helm_tex_c3.png` and `review/sheet_helm_clay_c3.png` (helmet at 0.4 vs 0.6),
`review/sheet_hands_clay_a74.png`, `review/sheet_body_clay_a74.png`, `review/ladder_sheet.png` (last ladder run, C5).

Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_dookmilitia_reduce_claude/review/viewer/ (installed r19 and c479p
per tier; `run_creature_review.py check`: 132 switches, 0 failed, 0 console errors).

## Not checked
In game; the binding regression (no install); motion at normal speed; LOD1-3 by eye (numbers only); the shadow meshes by eye;
tiers B and C in Blender close-ups (viewer shots only). Not tried: rebuilding the 330-triangle sword low-poly with a bake (about
150-200 triangles to gain), dropping and rebuilding the linings from the cut outer shell.

## Install (after the user's OK)
`check_winding.py export/mm9_dookmilitia.glb`, `tools/install_model.py export/mm9_dookmilitia.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, and the line in `../mm9_dookmilitia_claude/README.md` that a rebuild must
re-run this reduction.
