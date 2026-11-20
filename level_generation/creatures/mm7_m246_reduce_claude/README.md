# MM7 Goblin (`m246`, Goblin / Hobgoblin / Goblin Lord) reduction (2026-10-21)

User request for batch F: "handle batch F ... check if they had their tris reduced". The Goblin had not: LOD0 11,061
(body 10,431 + broadsword 630). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture
branch: no part needed rebuilding, so the textures, region mask, tier ramps, rig and clips stay as exported. No Meshy
credits. Nothing installed, nothing in `assets_dev/` or `assets_source/`, `mm7_m246_claude/` untouched. Every
Blender/Python step runs memory-capped (`scripts/cap.sh`).

Scripts copied from `mm7_m262_reduce_claude/` (ladder, decimation, UV weights, LOD build, LOD check, close-ups,
viewer tiers) and `mm7_m406_reduce_claude/` (`visibility.py`, `region_error.py`, `probe_max.py`, `patch_keep.py`,
`grip_check.py`, `compare_glb.py`, `label_view.py`, `viewer_sword.py`, `extract_basecolor.py`); the gates
`g4_weights.py`, `g5_hand_stretch.py`, `g6_contacts.py`, `g6_head_clearance.py`, `g6_crest.py`, `g4_skirt.py`,
`g6_skirt_poke.py`, `sole_probe.py` are unchanged copies from `mm7_m246_claude/scripts/`. New here: `make_groups.py`,
`dump_attrs.py`, `rest_error.py`, `stretch_cand.py`, `keep_source_lods.py`, `gates.sh`, `gate_summary.py`, and the
`REA_UV_GROUPS` option of `reduce_ladder.py`.

Source: `../mm7_m246_claude/export/mm7_m246.glb` (the latest export, 2026-10-20 14:01, after the attack-legs review;
`export_info.json` and `lods.json` belong to the same build), copied byte for byte to
`work/mm7_m246_source_pre_reduce.glb` (rollback source, sha256 `eb2b6b4b...`), broadsword to
`work/mm7_m246_sword_source_pre_reduce.glb` (`b2369443...`). One material `M246_A` (body + head merged into a
2080x1024 atlas), tier variants `m246_a/b/c` (`M246_A/B/C`), node `M246`, 57 joints incl. `Sword`, 4 influences at
LOD0 and 8 slots at LOD1-3, shadow LODs, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget. Weld:
14,471 -> 821 open edges, 10 coincident vertices with other weights (kept apart), 10,431 triangles in and out.

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| batch F export (body) | 10,431 | 5,214 | 1,822 | 553 |
| **reduced (body)** | **8,603** | 4,301 | 1,752 | 553 (source LOD3, kept) |
| broadsword attachment | 630 (unchanged) | 314 | 112 | 35 |
| LOD0 with the sword | 11,061 | | | -> **9,233** |

Body -17.5 %; with the sword 11,061 -> 9,233 (-16.5 %). **The 25-35 % aim was not reached without damage.** The body
was already reduced once in its own build (Smart Topology 15.6k -> 10.4k with the head, hands and every piece of up
to 40 triangles protected), and 44 % of what is left cannot be cut (below). The remaining torso/arm/trouser surface
already sits at its budget: at 76 % it carries the largest error of all regions (rest-pose p95 5-6 mm, evenly over
torso, arms and trousers, `review/labels/rest_err_81_rest.png`), and every step below 82 % fails the ladder.

## Pieces and budgets (`make_groups.py`, set `i`; `review/labels/groups_a.png`)

Garment labels come from the master (`../mm7_m246_claude/work/rig_v6.blend`, copied per vertex by `gate_attrs.py`;
exact match, 0.0 mm). Face visibility from `visibility.py` (whole body; head band from all and from frontal
directions only).

**Kept exactly (4,623 faces):** the right hand shell (726, the solved broadsword fist), the bracer cuff faces with hand
weight > 0.3 (both sides; a 60-70 % cut moved the right cuff end 13 mm), the 56 spikes and studs (1,338: irregular
8-19-vertex cones, any cut makes them lopsided), the small rigid head pieces (440: eyes, cheek pieces, goatee,
helmet studs, crest base), the visible face front (736, incl. tusks and ears), soles (faces below 6 cm), the ten hip
panels (450: thin strips, p99 7.7 mm at 80 %), the belt and the back strap (247), the shin guards (164: their rim
ring bent at 80 %), a 2.5 cm patch at the vest V crossing (drift 79 at the first pick) and a 3 cm patch at the left
armpit under the pauldron (the only spot where an edge stretched more than the source: 2.81x vs 2.67x).

| group | faces | ratio | out |
|---|---:|---|---:|
| 1 hair | 549 | 70 % | 383 |
| 2 crest (plume) | 633 | 45 % | 283 |
| 3 helmet shell | 277 | 60 % | 165 |
| 4 vest | 428 | 85 % (75 %: p99 8.6 mm) | 362 |
| 5 plates (bracers, upper-arm plate, pauldron) | 695 | 70 % | 485 |
| 6 head sides (ears' backs, jaw, neck) | 238 | 65 % | 210 |
| 7 hidden skin (scalp under the helmet, skin under the vest) | 512 | 70 % (40-55 %: the scalp dome flattened 30 mm) | 358 |
| 8 left hand (holds nothing) | 697 | 55 % | 383 |
| 0 torso, arms, trousers, boots | 1,779 | rest of the budget | 1,351 (76 %) |

Weights: piece weights (nearest vertex of the matching source piece; the UV-barycentric `REA_WEIGHTS=component` gave
the thigh under the hip panels 35 mm in Death); new vertices of hair, crest and plates take barycentric UV-triangle
weights (`REA_UV_GROUPS=1,2,5`): nearest-vertex weights stepped the hair's strand-smoothed weights and its edges
stretched 3.84x against the source's 2.40x. Source vertices keep their weights exactly.

## Ladder (REA_HEIGHT_M 1.70: p99 <= 5.1 mm, max <= 25.5 mm, IoU >= 0.98, SSIM >= 0.93)

| set | config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| a | everything but hands/spikes/face cut (vest 65 %, panels 80 %, hidden 40 %) | r76 | 8,059 | 7.74 / 40.1 | 0.986 | 0.977 | fail |
| b | + panels, left hand kept; hidden 55 % | r84 | 8,819 | 5.52 / 35.3 | 0.994 | 0.986 | fail |
| c | + belt, strap, shin guards kept; left hand 70 %, UV weights | r83 | 8,709 | 4.76 / 35.3 | 0.993 | 0.985 | fail (thigh in Death) |
| cp | c with piece weights | r83 | 8,709 | 4.82 / 19.3 | 0.993 | 0.985 | pass |
| d | panels 85 %, crest 35 %, hair 60 % | r82 | 8,619 | 5.49 / 18.5 | 0.992 | 0.986 | fail |
| e | hair 70 %, crest 45 %, helmet 60 %, vest 85 %, left hand 55 % | r81 | 8,501 | 4.99 / 21.5 | 0.992 | 0.984 | pass, vest V drift |
| f | e + drift lock (2 cm) | r83 | 8,709 | 5.66 / 20.5 | 0.990 | 0.985 | fail (drift moved, as the playbook warns) |
| g | e + vest V patch | r81 | 8,499 | 5.05 / 21.5 | 0.992 | 0.984 | pass; hair stretch 3.84x, cuff moved |
| h | g + bracer cuffs kept, UV weights for hair/crest/plates | r82 | 8,603 | 4.89 / 20.1 | 0.993 | 0.985 | pass; armpit edge 2.81x |
| **i** | **h + armpit patch** | **r82** | **8,603** | **4.93 / 20.1** | **0.992** | **0.985** | **picked** (r81 fails 5.36 / 25.0) |

Close-ups (source vs pick, from `work/ladder_i.blend`): `review/close/sheet_i82a_tex.png`, `sheet_i82b_tex.png`
(+ `_clay`): face front, three-quarter and profile, helmet, crest side and back, hair, both hands, the sword fist in
the attack, chest, vest V, vest side, back, pauldron, both arms, belt, legs from behind, knees, boots, Attack, Hit,
Death. Straight from the GLBs (file normals): `review/glbclose/sheet_r82_{a,b}_{tex,clay}.png`. No feature changed.
Texture drift (`texture_drift.py r82`): 10 faces over 40, all large crest-top and back faces under 60, not visible.

## Build

`TOKEN=<lease> REA_KEEP_SOURCE_LODS=3 REA_FLOOR_M=0.01 REA_LOD_RATIOS=0.5,0.21,0.064 scripts/build_export.sh ladder_i.blend Cand_82`:
`export_cand.py` (10 new sole vertices lifted onto the floor) -> `swap_lod0.py` (into the rollback source:
materials, variants, ramps, clips unchanged) -> `build_lods.py` (`tools/build_actor_lods.py`, 8 influence slots as the
source, bounding extremes and every vertex within 1 cm of the floor in Death/Dead protected) ->
`shrink_shadow_lods.py` -> `carry_variants.py` -> `keep_source_lods.py` (LOD3 and its shadow from the source: the
rebuilt LOD3, 479 or 617 triangles, flattened the crest into a ribbon and hid the face under the helmet,
`review/lods/sheet.png`). The broadsword is copied byte for byte (630 triangles, a clean procedural mesh whose grip
must stay exact; not heavy).

## Checks

| check | source | reduced |
|---|---|---|
| G4 arm stretch p99 / max (worst clip) | 1.88 / 2.85 | 1.82 / 2.85 |
| G5 hand stretch right / left | 2.94 / 3.24 | 2.94 / 2.15 |
| G6 contacts (deepest, cm) | Attack R hand 1.1; Death blade 5.9 (known), R hand 1.7 | Attack 0.9; Death blade 5.8, R hand 1.7 |
| head clearance deepest / closest | 0.2 / 0.3 cm (Hit) | 0.0 / 0.1 cm (Hit) |
| crest / hair inside the body | 0 / 0.2 cm | 0 / 0 cm |
| hip panel stretch, crest + hair stretch | 1.95 / 2.40 | 1.95 / 2.40 |
| soles per clip | Standing -1.7, Attack -2.1..-0.8 cm | the same |
| LOD check lowest point Dead LOD0-3 | 0.1 / 0.0 / 0.4 / 0.0 cm | -0.3 / -0.3 / -0.3 / 0.0 cm |
| LOD check stretched faces, bounds | 0, 1.70 m (LOD3 1.684) | 0, 1.70 m (LOD3 1.684, source LOD3) |
| right-hand grip (`GRIP_SIDE=R grip_check.py`) | | 784 vertices: 0.0005 mm, weights identical |
| `compare_glb.py` (nodes, skin, materials, variants, clips, images) | | no differences; variants on all 8 primitives |
| `check_winding.py` body, sword | 0, 0 | 0, 0 |

Gates run on gate copies of both GLBs (`scripts/gates.sh`; `review/gates_source.txt`, `review/gates_reduced.txt`,
summary `review/gates_summary.txt`). The source numbers reproduce the batch F README (blade 5.9 cm in the Death
fall, hand stretch 2.94x / 3.24x). Blade gate: the sword and the rig are unchanged, so its edge share is the batch F
result. `g6_skirt_poke.py` reads 5.0 cm (its search radius) for both, as noted in the batch F README.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m246_reduce_claude/review/viewer/`: batch F export (r100) and
reduced (r82, default) for tiers A, B and C, the unchanged broadsword added under the `Sword` joint for review only
(`viewer_sword.py`). `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m246_reduce_claude
--token <lease> check`: 48 switches, no console errors. `review/shots/sheet_sword.png` (tier A Standing and Attack 1.0 s).

## For the user to review

- 17.5 % off the body (16.5 % with the sword), short of the 25-35 % aim: spikes and studs, the sword hand, face front,
  small head pieces, hip panels, belt, strap, shin guards and cuffs keep 4,623 triangles exact, and the already
  reduced torso/arm/trouser surface fails the ladder below 82 %.
- LOD3 is the source's own LOD3 (553); LOD1/LOD2 are rebuilt (4,301 / 1,752).
- Dead lies 3 mm lower at LOD0-2 (-0.3 cm vs +0.1 cm); Attack and Standing already sit 1.7-2.1 cm under the floor in
  the source.
- The vest V crossing reads very slightly darker in the textured close-up (`sheet_i82a_tex.png`, vest_v).

## Install (not run; user decision)

Replaces the batch F export of `mm7_m246_claude/` (same nodes, materials, variants and clips; sword unchanged):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m246_reduce_claude/export/mm7_m246.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m246_reduce_claude/export/mm7_m246_sword.glb --world mm7
```

then append the staged binding `../mm7_m246_claude/actors_m246_binding.yml` (Goblin A/B/C, unchanged by this
reduction: model `worlds/mm7/models/mm7_m246.glb`, sword attachment on `Sword`) to
`assets_dev/worlds/mm7/models/actors.yml`, and add a [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback:
install `work/mm7_m246_source_pre_reduce.glb` (+ `work/mm7_m246_sword_source_pre_reduce.glb`) the same way.

## Reproduce

```sh
REA_GLB=$PWD/work/mm7_m246_source_pre_reduce.glb REA_NODE=M246 scripts/b.sh import_source.py
scripts/b.sh dump_mesh.py; scripts/b.sh dump_faces.py; scripts/b.sh dump_weights.py
REA_GLB=... REA_NODE=M246 REA_OUT=work/gate_source.blend scripts/b.sh gate_import.py
scripts/b.sh gate_attrs.py $PWD/work/gate_source.blend $PWD/../mm7_m246_claude/work/rig_v6.blend; scripts/b.sh dump_attrs.py
python3 scripts/visibility.py -0.01 1.75 (-> work/visible_all.npy); REA_VIS_OUT=work/visible_head.npy REA_MIN_PIX=6 visibility.py 1.25 1.75
REA_VIS_OUT=work/visible_front.npy REA_YDIR_MAX=-0.3 REA_MIN_PIX=6 visibility.py 1.25 1.75
# work/cuff_keep.npy: faces of non-skin pieces touching a vertex with hand + finger weight > 0.3
M246_EXTRA_KEEP=work/cuff_keep.npy G_LHAND=1 K_PANELS=1 python3 scripts/make_groups.py h0
REA_PATCH_R=0.025 patch_keep.py work/keep_h0.npy work/keep_h.npy -0.028,-0.186,1.163
REA_PATCH_R=0.03 patch_keep.py work/keep_h.npy work/keep_i.npy 0.216,-0.087,1.184   # groups_i = groups_h0 with keep_i at -1
REA_UV_GROUPS=1,2,5 REA_KEEP_FACES=work/keep_i.npy REA_GROUPS=work/groups_i.npy \
  REA_GROUP_RATIOS=1:0.7,2:0.45,3:0.6,4:0.85,5:0.7,6:0.65,7:0.7,8:0.55 scripts/run_ladder.sh i 0.83,0.82,0.81
scripts/b.sh stretch_cand.py ladder_i.blend work/groups_i.npy; texture_drift.py r82; close_m246.py; pair_sheet.py
REA_KEEP_SOURCE_LODS=3 REA_FLOOR_M=0.01 REA_LOD_RATIOS=0.5,0.21,0.064 scripts/build_export.sh ladder_i.blend Cand_82
lod_check.py, lod_views.py, glb_close.py, gates.sh (source, reduced), gate_summary.py, grip_check.py, compare_glb.py
viewer_tiers.py (r100, r82), viewer_sword.py, viewer_manifest.py r82 10431 8603
```

Blender scripts run through `scripts/b.sh` (lease wrapper, `TOKEN`); `run_ladder.sh` takes the pymeshlab venv from
`REA_VENV` (default: the venv the other MM7 reduce projects use).

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -3.2.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m246.glb export/mm7_m246.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m246.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/h12`](../gait_rollout_20261031/h12/README.md) appended Jog (humanoid set Unarmed-Run-Forward,
0.76 s) and Sprint (Unarmed-Sprint, 0.54 s) to the installed `assets_source/worlds/mm7/models/mm7_m246.glb` and
installed it (existing clips, meshes, skins and materials byte-identical). The sword arm is lifted (eased, up to 25 deg)
where the right knee comes through, so the blade clears the thigh. Bindings (`h12/bindings.yml`): run: Jog,
run_stride_length 2.3131, sprint: Sprint, sprint_stride_length 3.7404. `Running` stays in the GLB, no longer bound.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h12/scripts/rebuild.sh m246` (from `h12/work/mm7_m246_pre_gait.glb`, the
rollback source). A far-LOD repair rerun, a floor fix or any re-export of this model must re-graft these clips: copy the
new source over `h12/work/mm7_m246_pre_gait.glb` and rerun the rebuild, then install with `tools/install_model.py`.
