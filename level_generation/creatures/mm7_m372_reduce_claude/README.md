# MM7 Peasant Human2 Female (`m372`) reduction (2026-10-20)

User: "do tris reduction on all 5" (the five MM7 batch K peasants; this project is m372 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the six colour looks (`KHR_materials_variants`) and the region ramps stay valid. No Meshy
credits. Scripts from batch J's dress, [`../mm7_m312_reduce_claude/`](../mm7_m312_reduce_claude/README.md). **Not
installed** (batch K: the user installs later).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m372_reduce_claude/review/viewer/) (production
for one look per palette group vs reduced for all six looks, six clips) · [close-ups](review/close/sheet_r80.png) ·
[viewer pair](review/pair_aa.png)

## Source

`../mm7_m372_claude/export/mm7_m372.glb` (after the 2026-10-20 floor/walk fix: legs and shoes on the leg bones, Relax
Walk Forward; sha256 8cccb8168e9a9d29...), copied byte for byte to `work/mm7_m372_source_pre_reduce.glb` (rollback source).
One node `M372`, six variants `m372_aa`…`m372_bc` (outfits B and C share palettes 376–378) sharing one merged body +
head atlas (2080×1024; region mask: gown, veil and sleeve lining, hair), 4 influences at LOD0, 132 joints (the 14 × 4
Robe_ and 2 × 3 × 3 Sleeve_ chains), shadow LODs, clips Standing, Walking, Hit, Death, Dead, Fidget. Height 1.70 m.
Weld (identical weights only): 7,232 -> 729 open edges, 2 coincident vertices with other weights (kept apart by
`decimate_tex.py`), 10,944 triangles. `face_piece.py` maps the production master's `piece` attribute onto the source
faces (max 0.002 mm); `face_bones.py` splits the gown (one Smart Topology shell) by its skin weights. pymeshlab runs
from a scratchpad venv (`REA_VENV` in `run_ladder.sh`).

## Regions (`make_groups.py`)

| label | region | faces | pick ratio |
|---|---|---:|---|
| 1 | head (face, neck) | 2,224 | 55 % |
| 2 | veil | 699 | 75 % |
| 3 | hands | 1,576 | 55 % |
| 4 | headband | 287 | 70 % |
| 5 | skirt (gown faces on the robe chains) | 1,076 | kept |
| 6 | bodice (gown faces on the trunk) | 654 | 85 % |
| 7 | lower legs above the shoes (hidden) | 80 | 80 % |
| 8 | hanging cord | 300 | 70 % |
| 9 | belt | 373 | 75 % |
| 10 | bell sleeves (gown faces on the Sleeve_ chains / arm bones) | 862 | 85 % |

Kept exactly (`work/keep_e.npy`, 2,866 faces): pieces of up to 250 faces (eyes, brows and lashes, belt fittings and
clasp, beads), the shoes (below 15 cm), the skirt hem band (below 12 cm) and one error lock (`err_lock.py` on d's pick,
12 mm, 2 cm: 9 vertices at the left sleeve lining, the right forearm and the veil edge in the Death, 53 faces).

## Ladder (limits for 1.70 m: p99 5.1 mm, max 25.5 mm)

| config | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| a: head 65, veil 70, hands 60, headband 70, skirt kept, bodice 85, legs 70, cord 80, belt 85, sleeves 85 | 8,864 | 2.69 / 24.8 | 0.998 | 0.998 | pass (veil p99 7.3, sleeves max 23.7 in Death) |
| b: head 60, veil 60, hands 55, bodice 80, legs 60, cord 70, belt 80, sleeves 80 | 8,444 | 3.64 / 30.7 | 0.998 | 0.997 | fail (max in Death) |
| c: head 60, veil 80, sleeves 90, legs 50 | 8,800 | 2.37 / 30.7 | 0.999 | 0.998 | fail (hidden legs 29.7 mm) |
| d: c with legs 70 | 8,816 | 2.36 / 24.8 | 0.999 | 0.998 | pass |
| e: + error lock, head 55, veil 75, hands 55, bodice 80, belt 75, sleeves 85 | 8,506 | 2.71 / 23.3 | 0.999 | 0.998 | pass (bodice p99 7.0, legs p99 18.9) |
| **f: e with bodice 85, legs 80** | **8,546** | **2.56 / 23.3** | **0.999** | **0.998** | **picked** |

- **Pick** `Cand_80` of `work/ladder_f.blend`: the production chain had already reduced every garment, and the simulated
  skirt is kept exactly (batch J: a 10 % cut moved a dress hem 38 mm in Death).
- **Per region** (`group_error.py`): head p99 1.6 mm, veil 5.1 / max 9.2, hands 2.4, headband 1.8, bodice 5.0 / max
  11.4, hidden legs 7.9, cord 1.3, belt 2.7, bell sleeves 5.6 / max 23.3 (Fidget, the raised sleeve's lining).
- **Close-ups** (`close_human.py`: face front / three-quarter / side, back of the head, both hands, bodice front and
  back, belt, hem front and back, walking feet, both sleeves, walk side, corpse; textured and clay;
  `review/close/sheet_r80.png`): no visible change. Viewer pair (`review/pair_aa.png`, GLB shading): same.
- **Flecks:** `texture_drift.py` 0 faces over 40 (p99 12.6); `dark_slivers.py` (`REA_DARK_L=80 REA_DARK_N=4`) 12
  candidate faces at the belt fittings and one beside the right cheek; none visible in the close-ups or the viewer.

## Build

`export_cand.py` (`REA_CAND=Cand_80 REA_NODE=M372 REA_INFLUENCES=4`) -> `swap_lod0.py ... M372` -> `build_lods.py`
(the production settings: `tools/build_actor_lods.py` ratios 0.5 / 0.18 / 0.06, 8 influences at LOD1-3; protected:
the veil top and LOD0 vertices within 1 cm of the floor in any Death/Dead frame, 230 points) ->
`MESH=M372 ../mm7_m372_claude/scripts/shrink_shadow_lods.py` -> `carry_variants.py` (7 primitives): `export/mm7_m372.glb`,
7.7 MB (production 8.3 MB). Textures, variants, region ramps, clips, palm sockets and node structure are the
production ones; the head material was already merged in the source, and every UV stays inside 0..1 (the production
build's `clamp_uv.py` issue does not recur). `check_winding.py`: 0 inverted closed parts.

| body | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| production | 10,944 | 5,471 | 1,964 | 650 |
| reduced | 8,546 | 4,272 | 1,534 | 504 |

`lod_check.py` (`work/lod_check_{src,r80}.json`): every LOD keeps the 1.70 m height (production LOD3 1.685 m); the
lowest point per clip equals the source's at LOD0-2 (Death −4.0 cm, the laid-flat skirt, as in the source); LOD3 has
one face over 20x its rest area in the Death (production LOD3: none) and its walking soles sit 0.4 cm higher.

## Review

`tools/run_creature_review.py --project level_generation/creatures/mm7_m372_reduce_claude check`: 48 model/clip
switches, no console errors.

## Status

Not installed; awaiting user review. To adopt it, install `export/mm7_m372.glb` in place of the production export
(the `actors.yml` binding in `../mm7_m372_claude/integration/actors.yml` is unchanged):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m372_reduce_claude/export/mm7_m372.glb --world mm7
```

Rollback: `work/mm7_m372_source_pre_reduce.glb`. Add the model to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) when it
is installed.

Reproduce: `REA_NODE=M372 REA_GLB=<rollback source> import_source.py` -> `dump_mesh.py` -> `face_piece.py` ->
`face_bones.py` -> `make_groups.py` -> ladder d (`REA_INFLUENCES=4 REA_KEEP_FACES=work/keep_base.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.6,2:0.8,3:0.6,4:0.7,5:1.0,6:0.85,7:0.7,8:0.7,9:0.8,10:0.9 REA_HEIGHT_M=1.7 run_ladder.sh d 0.81`) ->
`REA_CAND=Cand_81 REA_ERR_MM=12 REA_LOCK_R=0.02 err_lock.py -- work/keep_base.npy work/keep_e.npy` (on ladder d) -> ladder f
(`REA_KEEP_FACES=work/keep_e.npy`, `REA_GROUP_RATIOS=1:0.55,2:0.75,3:0.55,4:0.7,5:1.0,6:0.85,7:0.8,8:0.7,9:0.75,10:0.85`,
`run_ladder.sh f 0.80`) -> checks (`group_error.py`, `texture_drift.py r80`, `dark_slivers.py r80`, `close_human.py`) ->
build as above -> `lod_check.py` -> `viewer_variants.py` (export r80, rollback source r100) -> `viewer_manifest.py`.

## Installed 2026-10-20

`tools/install_model.py export/mm7_m372.glb --world mm7` (winding check 0 inverted closed parts first); the
nine bindings from `../mm7_m372_claude/integration/actors.yml` appended to `assets_dev/worlds/mm7/models/actors.yml`
(explicit scale, no `scale_reference`); ledger row in `../REDUCTION_LEDGER.md`. Boot check on Harmondale with two looks
spawned: no load errors, no missing models (`output/batchK_boot/`). Rollback: reinstall
`work/mm7_m372_source_pre_reduce.glb` (the batch export) the same way.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -3.3.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m372.glb export/mm7_m372.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m372.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31, package h14)

The installed source (`assets_source/worlds/mm7/models/mm7_m372.glb`) gained new in-place locomotion clips appended by
[`../gait_rollout_20261031/h14/`](../gait_rollout_20261031/h14/README.md): Walk2 (humanoid set Relax-Walk-Forward slowed to 1.00 s, stride 1.3861) and Jog (Mixamo Running (5), 0.80 s, stride 1.9958); gown re-simulated on each new clip (chains from `work/rig_v6.blend`); bell-sleeve chains keep the Walking keys (rigid on the forearm). Existing clips, meshes, skins and
materials are byte-identical (prefix check). Bindings for all nine descriptors (for the coordinator,
`h14/bindings.yml`): walking: Walk2, stride_length 1.3861, run: Jog, run_stride_length 1.9958. Rollback: reinstall `../gait_rollout_20261031/h14/work/mm7_m372_pre_gait.glb`.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h14/scripts/rebuild.sh m372`, then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h14/export/mm7_m372.glb --world mm7
--name mm7_m372.glb`. A far-LOD repair rerun, a head-bob fix or any re-export of this model must re-graft these clips
(copy the new source over the pre-gait copy and rerun the rebuild).
