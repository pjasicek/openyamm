# MM9 Markel the Great (`mm9_markel`, unique NPC, ledger row 76) reduction: candidate b2 r60 ready for review (2026-11-05; lease released)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio 3; user 2026-11-05 "do all": uniques
reduced too, face exact), row 76 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:markel` (owner markel-reduce-20261105);
the creature's own `mm9:markel` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_markel.glb` (sha256 be0bcbda7dd0,
identical to `../mm9_markel_claude/export/mm9_mk.glb`), copied to `before/` (rollback). No Meshy, no credits, no repaint. **Not installed.**
`../mm9_markel_claude/` and `../mm9_peasantm5_reduce_claude/` were only read (Markel's arm/hand, jitter, sleeve poke, shading,
shrink_shadow_lods and mirror scripts run in place). Scripts are copies of PeasantM5's reduction (Markel's body is PeasantM5's source),
renamed to Markel's node/primitives (`Markel`, `MarkelHead`), one skin (no tiers: tex A = B, viewer model `a` only).

| | LOD0 | body prim `Markel` | head prim `MarkelHead` | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 8,169 | 3,594 | 4,575 | 4,079 | 1,461 | 480 |
| **b2 r60 (`export/mm9_markel.glb` = `export/mm9_markel_b2_60.glb`, sha256 3ab2b16b9f08)** | **6,891 (-15.6 %)** | 3,048 | 3,843 | 3,439 | 1,231 | 403 |

Per group (free faces cut): MPFB hands 1,298 -> 778 (0.6, every finger; graft faces exact), hair shell 704 -> 492 (0.7 as PeasantM5's
fix; hairline 2 rings and the bald-crown rims exact), shirt 1,438 -> 1,166 (5 mm distance guard stops it), trousers/boots 1,131 -> 857
(6 mm guard). Every vertex of the candidate is an installed vertex (only index buffers changed); clips (20), skin, nodes, materials and
all 6 images identical (`review/gates_b2_60/same_clips.txt`). Exact (`scripts/exact_head.py`: 0 missing): face shell with the painted
beard 1,790, neck/collar piece 268, eyes 96, the small pieces 641 (torc, medallion, lacing, belt studs), cuffs/graft, soles, collar band,
beard-chest contact.

## Measured first: protected share
`scripts/analyze.py`, `scripts/head_survey_mk.py` (`review/head_survey.png`), `scripts/make_sets_mk.py a` (`review/sets_a_{body,head,hands}.png`):
no linings (`twins.py`: 0 pairs). Protected 3,598 (44.0 %), free 4,571; 15 % of LOD0 (1,225) is 27 % of the free part, so the run went ahead.

## Route
Pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantM5's copy) with the chart guard (`MP_CHART=1`) **and the audit's own chart test
inside each collapse** (`MP_AUDIT=1`, ported from `mm9_peasantm1_reduce_claude`), texture guard, texture weight 4, seam slides on the
hands, scored over all 20 clips at 10 Hz, distance guards 5 mm shirt / 6 mm legs. Two Markel additions:
- `MP_LOCK_DOM=Clavicle,UpperArm`: the 135 shoulder-dominant vertices are never removed. The jitter gate's shoulder-skin term is a 95th
  percentile over exactly those vertices; ladder a removed some and moved the statistic over the limit (Sc2_Markel10 L 1.93 -> 2.05
  mm/f2, FAIL) although every vertex moves as installed. With the lock the jitter report is byte-identical to the installed one.
- `MP_NRM=1` (b2): a collapse whose new face points against its corners' shading normals is refused (b r60 had 2 such faces at the
  hem/thigh fold; installed 0, b2 0).

## Ladders (limits for 1.756 m: p99 <= 5.27 mm, max <= 26.3 mm, IoU >= .98, SSIM >= .93)
| ladder | change | LOD0 | p99 / max mm | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a | set a, hands .6, legs .55, hair .7, shirt r60/r50 (guards stop both at the same count) | 6,871 (-15.9 %) | 3.58 / 10.5 | .9934 / .9942 | pass; jitter 1 FAIL (shoulder-skin statistic) |
| b | a + shoulder-vertex lock | 6,891 (-15.6 %) | 3.55 / 10.5 | .9944 / .9945 | pass; jitter identical; arm gate readings, see below |
| c | b + hand/forearm contact keep (`hand_contact_mk.py`, 2.5 cm, 266 body faces) | 6,997 (-14.3 %) | 3.42 / 10.5 | .9949 / .9950 | pass; forearm depths equal to installed; under ~15 % |
| **b2** | **b + shading-normal guard (fix of b, same parameters)** | **6,891 (-15.6 %)** | **3.51 / 10.5** | **.9944 / .9946** | **PASS, picked** |

`review/ladder_sheet_{a,b,c,b2}.png`. Three ladders plus one guard fix of b; `export/mm9_markel_c60.glb` is kept as the alternate.

## Gates, installed -> b2 r60 (`scripts/gates.sh`, Markel's own gate set; `review/gates_before/`, `review/gates_b2_60/`)
- **UV audit** (`review/uv_audit_b2_60.json`): **0 escaping LOD0 faces in both primitives**. LOD1-3 (LOD tool's decimate) body/head
  130/123, 96/157, 47/104 vs the installed's own 115/90, 113/141, 58/108.
- Jitter vs MM9's clips (on the unmirrored GLB, as the creature ran it): **identical report**, 0 fails. Sleeve poke: 0 mm, 0 frames in all
  20 clips both. Beard (stretch, contact gap, approach): identical. Hair-shell stretch (`hair_stretch_mk.py`): maxima identical in every clip.
- Arm and hand (creature's gate; also `--exact`): hand depths, frame counts, finger stretch and wrists equal except readings the
  gate's sign rule gets wrong: **Talk L hand 0 -> 5.2 cm (5 f), Fidget L forearm 2.4 -> 5.9, Talk R forearm 2.0 -> 5.4 (exact)**. The gate
  signs depth by the one nearest triangle; at a convex vertex shared by several leg/shirt faces it reads a thumb 5.6-6.1 cm out in open air
  as inside (`scripts/arm_probe.py`: Talk f66 thumb tip 6.09 cm from the thigh, axis rays hit nothing in front). Second opinion
  `scripts/arm_inside_check.py` (every 48 fps frame, every clip, both sides; inside only if most of 26 rays cross an odd number of faces;
  `review/gates_{before,b2_60}/arm_inside.txt`): every confirmed depth equal or lower **except three forearm contacts of 1-2 mm,
  each at one frame: AttackMelee R 2.2 -> 2.4 cm (f41), Sc2_Markel15 R 2.2 -> 2.4 (f25), Standing R 2.0 -> 2.1 (f69)**. Ladder c keeps the
  body faces under the forearms and restores those three exactly (2.2 / 2.2 / 2.0), at -14.3 %.
- Detached 0 both (two new "shallow" notes: lacing piece 15 tris rooted -1.6 mm on R Hand in Sc2_markel21 f6, torc rooted 5.1 mm in Death
  f15). Flat shading 0.0 % both; winding 0; bones: R Thigh 11-12.3 % as installed (MM9's hip slide). Texture quality: body 59.3 % both,
  stretch p90 1.09 -> 1.10; head set 39.1 % both, stretch 1.63 -> 1.67, fragments 1.8 -> 2.3 % (hand and hair charts with fewer faces).
- LODs (`scripts/lod_check.py`; `scripts/build_lods.py` 0.5/0.18/0.06, 4 influences, 30 of 30 protected points mapped): height 1.7703 m at
  every LOD (installed 1.7703 / 1.7700 / 1.7696 / 1.7666); LOD0 lowest point per clip identical to installed; LOD1-3 equal to LOD0 in every
  clip (installed LOD3 floated up to +1.4 cm in Dead); LOD0 stretched faces per clip identical to installed (installed's own), LOD1-3 0.

## Review
Viewer (installed and b2 r60, all 20 clips; `run_creature_review.py check` per model: 40 switches, 0 failed, no console errors,
`review/viewer_check_b2_60_{inst_a,red_a}.txt`): http://127.0.0.1:8912/level_generation/creatures/mm9_markel_reduce_claude/review/viewer/
Sheets read (installed left/above): `review/sheet_face_b2_60.png` + `review/sheet_face_diff_b2_60.png` (front close-up, 3/4, profile, low 3/4,
party: face skin, painted beard, ears and eyes black in all five diffs; the hair shell and fur shoulders differ in shading),
`review/crop_hair_profile_b2_60.png`, `review/crown_b2_60.png` (crown from behind above both sides, shoulders from behind: no streak),
`review/sheet_body_b2_60_a.png` (Standing front/3-4/back, Walking, Talk, Death), `review/close_b2_60_{1,2,3}.png` (arms, belt/hem front and
back, Running hem, boots, Talk arms, shoulders from behind, Hit, hem sides, fur sleeve cuff, lacing/medallion), `review/close_b2_60_hands.png`.
Look at: the thumbs (0.6: tips slightly more angular, as PeasantM5), the hem's side edges (`close_b2_60_3.png`), the fur shoulders' shading.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_markel_reduce_claude/before/mm9_markel.glb REA_NODE=Markel $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/make_sets_mk.py a
REA_HEIGHT_M=1.756 MP_NRM=1 MP_LOCK_DOM=Clavicle,UpperArm MP_DMAX_MM=4 MP_DMAX_GROUPS=0:5,3:6 MP_CHART=1 MP_AUDIT=1 MP_W5=4 MP_SEAM_GROUPS=1 \
  SETS=a MP_GROUPS=1:0.6,3:0.55,6:0.7 scripts/run_mp.sh b2 0.6
scripts/build_mp.sh mp_b2_r60 export/mm9_markel_b2_60.glb   # swap_mp -> build_lods -> Markel's shrink_shadow_lods -> carry_variants -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_markel_b2_60.glb before/mm9_markel.glb --json review/uv_audit_b2_60.json
$G scripts/exact_head.py export/mm9_markel_b2_60.glb a
scripts/gates.sh export/mm9_markel_b2_60.glb b2_60; REA_NODE=Markel $BL -P scripts/lod_check.py -- $PWD/export/mm9_markel_b2_60.glb b2_60
$G scripts/hair_stretch_mk.py export/mm9_markel_b2_60.glb review/gates_b2_60/hair_stretch.json; $G scripts/arm_inside_check.py <glb> <clip> all " L "
$G scripts/viewer_tiers.py export/mm9_markel_b2_60.glb red; $G scripts/make_viewer_manifest.py b2-r60 "inst_a=..=work/viewer_inst_th_a.glb" "red_a=..=work/viewer_red_th_a.glb"
HEADUP=0,0.08,0.05 scripts/shots.sh; scripts/close_shots.sh; scripts/hand_shots.sh; scripts/crown_shots.sh; $G scripts/shot_sheets.py b2_60; ...
```
Ladder c: `R=0.025 scripts/hand_contact_mk.py work/hand_contact_mk25.npy` (body faces kept from it), `EXTRA=work/hand_contact_mk25_body.npy
make_sets_mk.py c`, `SETS=c ... run_mp.sh c 0.6` (without MP_NRM). Install (orchestrator, on the OK): `check_winding.py export/mm9_markel.glb` (0),
`tools/install_model.py export/mm9_markel.glb --world mm9 --name mm9_markel.glb`, the `mm9_actor_models_build_every_binding` regression, and add
to `../mm9_markel_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_markel_reduce_claude`; a rebuild from this project must
re-run that reduction". Rollback: `before/mm9_markel.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); see-through (Markel's project has no see-through gate and no
linings); motion at normal speed by eye (stills, gates and viewer check only); the seated/argument clips by eye (numbers only: arm, sleeve,
jitter, floor, LODs); LOD1-3 and shadow meshes by eye (numbers only).
