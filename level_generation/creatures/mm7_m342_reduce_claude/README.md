# MM7 Peasant Human1 Female (`m342`, descriptors 349-357) reduction (2026-10-20)

User: "do tris reduction on all 5" (the five MM7 batch K peasants; this project is m342 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the nine colour looks (`KHR_materials_variants`) and the region ramps stay valid. No Meshy
credits. **Not installed** (batch K: the user installs later; no REDUCTION_LEDGER row yet).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m342_reduce_claude/review/viewer/) (production
for one look per outfit vs reduced for all nine looks, six clips) · [close-ups](review/close/sheet_f.png) (pick vs
source, textured and clay) / [c and d](review/close/sheet_tex1.png), [2](review/close/sheet_tex2.png) ·
[viewer pair](review/pair_aa.png)

## Source

`../mm7_m342_claude/export/mm7_m342.glb` (after the 2026-10-20 floor/walk fix: legs and shoes on the leg bones, Relax
Walk Forward; sha256 c3254f6cb15df156...), copied byte for byte to `work/mm7_m342_source_pre_reduce.glb` (rollback
source). One node `M342`, nine variants `M342_AA`…`M342_CC` sharing one merged body + head atlas (2080×1024, region mask
R dress, G hair), 4 influences at LOD0, shadow LODs, clips Standing, Walking, Hit, Death, Dead, Fidget; the green skirt
and the petticoat ride 14 × 4 simulated robe chains. Height 1.70 m. Weld (identical weights only): 7,924 -> 1,600 open
edges (the hair strands are open cards), 2 coincident vertices with other weights (kept apart by `decimate_tex.py`),
9,919 triangles. Scripts from batch J's dress, [`../mm7_m312_reduce_claude/`](../mm7_m312_reduce_claude/README.md);
`face_piece.py` maps the production master's `piece` attribute onto the source faces (max 0.001 mm). pymeshlab runs
from a scratchpad venv (`REA_VENV` in `run_ladder.sh`).

## Regions (`make_groups.py`)

| label | region | faces (not kept) | pick ratio |
|---|---|---:|---|
| 1 | head skin above the neck cut (1.43 m) | 666 | 50 % |
| 2 | shoulders + blouse sleeves (skin shell) | 1,211 → 664 after the strap lock | 65 % |
| 4 | hair strands over 80 faces | 517 | kept |
| 5 | green skirt (robe chains, below 0.95 m) | 878 | kept |
| 6 | bodice | 540 | 65 % |
| 7 | petticoat (robe chains) | 670 | kept |
| 8 | hidden legs above the shoes | 365 | 45 % |
| 9 | dagger and scabbard | 300 | 40 % |
| 10 | belt | 248 | 60 % |

Kept exactly (`work/keep_e.npy`, 5,071 faces): pieces of up to 80 faces (small hair locks, lashes, lips, mouth bits,
buckle), both hands with their forearms (fitted fingers), the eyes, the face front (head skin within 7 cm of the face
centre, front half), lips/lashes/teeth pieces, the shoes (legs piece below 15 cm), the petticoat hem band (below
12 cm), the green skirt's hem band (below 25 cm) and **the painted shoulder straps** (`strap_keep.py`: skin-shell faces
sampling dress green, plus their neighbours, 547 faces): ladders c and d cut jagged triangles into the straps' painted
edges.

## Ladder (limits for 1.70 m: p99 5.1 mm, max 25.5 mm)

| config | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| a: head 70, blouse 80, hair 70, skirt + petticoat kept, bodice 80, legs 60, dagger 60, belt 70 | 8,901 | 4.56 / 24.1 | 0.996 | 0.994 | pass, but hair p99 16.9 mm (strands) |
| b: hair 85, skirt + petticoat 90 | 8,605 | 4.87 / 31.1 | 0.996 | 0.994 | fail: Death max; hair p99 14.8, petticoat max 24 |
| c: hair kept, skirt + petticoat kept, head 60, blouse 70, bodice 70, legs 50, dagger 50, belt 70 | 8,715 | 3.82 / 22.9 | 0.999 | 0.995 | pass; strap edges jagged |
| d: c deeper (head 50, blouse 65, bodice 65, legs 45, dagger 40, belt 60) | 8,489 | 4.24 / 24.2 | 0.999 | 0.995 | pass; strap edges jagged |
| e: c + strap lock | 8,881 | 3.72 / 22.9 | 0.999 | 0.996 | pass |
| **f: d + strap lock** | **8,683** | **4.14 / 24.2** | **0.999** | **0.995** | **picked** |

- **Per region** (`group_error.py`, pick): head skin p99 3.4 / max 4.9 mm, shoulders + blouse 5.0 / 10.5, bodice
  3.9 / 6.7, hidden legs 14.3 / 23.6 (under the skirt; they show only at the hem and in the corpse), dagger 3.5 / 4.5,
  belt 7.1 / 8.1; hair, skirt and petticoat unchanged.
- The hair strands are thin open cards (any cut moves their tips 15-17 mm) and the simulated skirt and petticoat move
  their hems 20-24 mm in Death at a 10 % cut, as batch J's dress found: kept whole.
- **Close-ups** (`close_human.py`: face front and three-quarter, collar, lacing, both sleeves, back, hem front and back,
  feet while walking, corpse; textured and clay): no visible change at the pick.
- **Flecks:** `texture_drift.py r86` 11 faces over 40 (76.7 cm², p99 8.5); `dark_slivers.py r86` (`REA_DARK_L=80
  REA_DARK_N=4`) 3 faces, all on the black scabbard; none visible in the close-ups or the viewer.

## Build

`export_cand.py` (`REA_CAND=Cand_86 REA_NODE=M342 REA_INFLUENCES=4`) -> `swap_lod0.py work/mm7_m342_source_pre_reduce.glb
work/cand_export.glb work/pick_lod0.glb M342` -> `build_lods.py` (the production settings: `tools/build_actor_lods.py`
ratios 0.5 / 0.18 / 0.06, 8 influences at LOD1-3; protected: the top 5 mm and LOD0 vertices within 1 cm of the floor in
any Death/Dead frame, 184 points) -> `MESH=M342 ../mm7_m342_claude/scripts/shrink_shadow_lods.py` -> `carry_variants.py`:
`export/mm7_m342.glb`, 6.3 MB (production 6.6 MB; sha256 8c8808ee9bd9c6ea...). Textures, variants, region ramps,
clips, palm sockets and node structure are the production ones. `check_winding.py`: 0 inverted closed parts.

| body | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| production | 9,920 | 4,957 | 1,778 | 585 |
| reduced | 8,683 | 4,337 | 1,556 | 512 |

`lod_check.py` (`work/lod_check_{src,r86}.json`): the lowest point per clip equals the production LOD0's at every LOD
(Death −2.6 cm and Walking −2.2 cm as the source; the production LOD3 stood 1.3-2.1 cm above the floor); no face
stretches over 20x in any clip (the production LOD2 had one). LOD3's top is 1.722 m against LOD0's 1.702 m (a hair-strand
vertex; picking bounds use the coarsest LOD).

## Review

`tools/run_creature_review.py --project level_generation/creatures/mm7_m342_reduce_claude check`: 72 model/clip
switches, no console errors. `review/pair_aa.png`: look AA production (top) / reduced (bottom): standing, walking hem
and shoes, corpse, head.

## Status

Not installed; awaiting user review. To adopt it, install `export/mm7_m342.glb` in place of the production export
(the install command and `actors.yml` binding in `../mm7_m342_claude/README.md` are unchanged):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m342_reduce_claude/export/mm7_m342.glb --world mm7
```

Rollback: `work/mm7_m342_source_pre_reduce.glb`. Add the model to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) when it
is installed.

Reproduce: `REA_NODE=M342 REA_GLB=<rollback source> import_source.py` -> `dump_mesh.py` -> `dump_faces.py` ->
`face_piece.py` -> `make_groups.py` -> `strap_keep.py work/keep_base.npy work/keep_e.npy` -> ladder f
(`REA_KEEP_FACES=work/keep_e.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.5,2:0.65,4:1.0,5:1.0,6:0.65,7:1.0,8:0.45,9:0.4,10:0.6 REA_HEIGHT_M=1.70 run_ladder.sh f 0.86`) ->
checks (`group_error.py` with `GE_KEEP=work/keep_e.npy`, `texture_drift.py r86`, `dark_slivers.py r86`,
`close_human.py`, `close_sheet.py`) -> build as above -> `lod_check.py` -> `viewer_variants.py` (export r86, rollback
source r100) -> `viewer_manifest.py`.

## Installed 2026-10-20

`tools/install_model.py export/mm7_m342.glb --world mm7` (winding check 0 inverted closed parts first); the
nine bindings from `../mm7_m342_claude/integration/actors.yml` appended to `assets_dev/worlds/mm7/models/actors.yml`
(explicit scale, no `scale_reference`); ledger row in `../REDUCTION_LEDGER.md`. Boot check on Harmondale with two looks
spawned: no load errors, no missing models (`output/batchK_boot/`). Rollback: reinstall
`work/mm7_m342_source_pre_reduce.glb` (the batch export) the same way.

## Gait rollout (2026-10-31, package h14)

The installed source (`assets_source/worlds/mm7/models/mm7_m342.glb`) gained new in-place locomotion clips appended by
[`../gait_rollout_20261031/h14/`](../gait_rollout_20261031/h14/README.md): Walk2 (humanoid set Relax-Walk-Forward, the source of the installed Walking, slowed to a 1.00 s loop, stride 1.4322) and Jog (Mixamo Running (5), 0.80 s, stride 2.1609); skirt and petticoat re-simulated on each new clip (package h14's numpy port of `scripts/robe_sim.py`, chains from `work/rig_v6.blend`). Existing clips, meshes, skins and
materials are byte-identical (prefix check). Bindings for all nine descriptors (for the coordinator,
`h14/bindings.yml`): walking: Walk2, stride_length 1.4322, run: Jog, run_stride_length 2.1609. Rollback: reinstall `../gait_rollout_20261031/h14/work/mm7_m342_pre_gait.glb`.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h14/scripts/rebuild.sh m342`, then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h14/export/mm7_m342.glb --world mm7
--name mm7_m342.glb`. A far-LOD repair rerun, a head-bob fix or any re-export of this model must re-graft these clips
(copy the new source over the pre-gait copy and rerun the rebuild).
