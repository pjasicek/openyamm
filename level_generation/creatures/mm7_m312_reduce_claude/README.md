# MM7 Peasant Dwarf Female (`m312`) reduction (2026-10-20)

User: "OK reduce tris count now" (the five MM7 batch J peasants; this project is m312 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the nine colour looks (`KHR_materials_variants`) and the region ramps stay valid. No Meshy
credits. **Not installed** (batch J: the user installs later).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m312_reduce_claude/review/viewer/) (production
for one look per outfit vs reduced for all nine looks, six clips) · [close-ups](review/close/sheet_d.png) /
[2](review/close/sheet_d2.png) · [viewer pair](review/pair_a1.png)

## Source

`../mm7_m312_claude/export/mm7_m312.glb` (after the 2026-10-20 walk fix; sha256 b7fe0f7cbb98037b...), copied byte for
byte to `work/mm7_m312_source_pre_reduce.glb` (rollback source). One node `M312`, nine variants `M312_A1`…`M312_C3`
sharing one merged body + head atlas (2080×1024, region mask R dress, G hair), 4 influences at LOD0, shadow LODs, clips
Standing, Walking, Hit, Death, Dead, Fidget; the dress is 12 × 4 simulated robe chains. Height 1.70 m (chain units).
Weld (identical weights only): 7,007 -> 571 open edges, 4 coincident vertices with other weights (kept apart by
`decimate_tex.py`), 10,591 triangles. Scripts start from `../mm7_m274_reduce_claude/scripts/` (the Mage, same robe
route); `face_piece.py` maps the production master's `piece` attribute onto the source faces (max 0.001 mm).
pymeshlab runs from a scratchpad venv (`REA_VENV` in `run_ladder.sh`).

## Regions (`make_groups.py`)

| label | region | faces | pick ratio |
|---|---|---:|---|
| 1 | head piece (face, neck, chest) | 2,114 | 65 % |
| 2 | bun | 700 | 60 % |
| 3 | hands (rigid, open) | 885 | 60 % |
| 4 | ringlets | 518 | 75 % |
| 5 | skirt (robe chains) | 1,145 | kept |
| 6 | bodice + sleeves | 2,000 | 85 % |
| 7 | hidden legs above the shoes | 509 | 70 % |
| 8 | apron bow | 300 | 70 % |
| 9 | bow tails | 332 | 80 % |

Kept exactly (`work/keep_e.npy`, 2,255 faces): pieces of up to 250 faces (lacing ×6, cuff ruffles, earrings, pocket,
scissors, eyes, lips), the apron panel (painted stains), the shoes (below 15 cm), the skirt hem band (below 12 cm) and
one error lock (`err_lock.py` on b's pick, 12 mm, 2 cm: 34 vertices at the sleeve undersides and armpits, 167 faces).

## Ladder (limits for 1.727 m: p99 5.18 mm, max 25.9 mm)

| config | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| a: head 70, bun 60, hands 60, ringlets 75, skirt 90, bodice 80, legs 40, bow 70, tails 80 | 8,211 | 6.56 / 38.4 | 0.996 | 0.996 | fail: skirt 38 mm in Death, bodice p99 5.9, legs p99 20 |
| b: skirt kept, bodice 88, legs 60 | 8,589 | 4.56 / 25.2 | 0.998 | 0.997 | pass at the limit (sleeve undersides 25 mm in the walk) |
| c: + error lock, head 65, hands 55, bodice 85 | 8,431 | 4.48 / 28.9 | 0.997 | 0.996 | fail: legs 29 mm in Death, hands p99 5.35 |
| **d: hands 60, legs 70** | **8,517** | **4.01 / 22.4** | **0.997** | **0.996** | **picked** |

- **Pick 80 %** (`Cand_81` of `work/ladder_d.blend`): the production chain had already reduced every garment
  (`reduce_rigged.py`), and the simulated skirt cannot take any cut (a 10 % cut moved its hem 38 mm in Death, as the
  Mage's robe). The savings come from the head, bun, hands, bodice and sleeves and the hidden legs.
- **Per region** (`group_error.py`): head p99 1.8 mm, bun 4.4, hands 4.5, ringlets 2.3, bodice 4.2 / max 11.2,
  hidden legs 12.6 / max 19.4 (they show only in the corpse, painted as the dress), bow 4.0, bow tails 3.2.
- **Close-ups** (`close_human.py` spots face front and three-quarter, bun, back of the head, lacing, both sleeves,
  apron, bow, both hands, hem, walk side, corpse; textured and clay): no visible change. The painted sleeve stripes
  read the same.
- **Flecks:** `texture_drift.py` 3 faces over 40 (17.7 cm², p99 11.3); `dark_slivers.py` (`REA_DARK_L=80
  REA_DARK_N=4`) 24 candidate faces, all at the painted sleeve stripes; none visible in the close-ups or the viewer.

## Build

`export_cand.py` (`REA_CAND=Cand_81 REA_NODE=M312 REA_INFLUENCES=4`) -> `swap_lod0.py ... M312` -> `build_lods.py`
(the production settings: `tools/build_actor_lods.py` ratios 0.5 / 0.18 / 0.06, 8 influences at LOD1-3; protected:
the bun top and LOD0 vertices within 1 cm of the floor in any Death/Dead frame, 177 points) ->
`MESH=M312 ../mm7_m312_claude/scripts/shrink_shadow_lods.py` -> `carry_variants.py`: `export/mm7_m312.glb`, 7.2 MB
(production 7.6 MB). Textures, variants, region ramps, clips, palm sockets and node structure are the production
ones. `check_winding.py`: 0 inverted closed parts.

| body | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| production | 10,591 | 5,294 | 1,898 | 623 |
| reduced | 8,517 | 4,257 | 1,522 | 499 |

`lod_check.py` (`work/lod_check_{src,r81}.json`): every LOD keeps the 1.70 m height; the lowest point per clip equals
the source's at LOD0-2 (Death -12.6 cm and Dead -8 cm are the flattened dress, as in the source); at LOD3 the standing
soles sit 0.3 cm above the floor (the production LOD3: 1.2 cm under); no face stretches over 20x in any clip.

## Review

`tools/run_creature_review.py --project level_generation/creatures/mm7_m312_reduce_claude check`: 72 model/clip
switches, no console errors. `review/pair_a1.png`: look A1 production / reduced (standing, head, corpse).

## Status

Not installed; awaiting user review. To adopt it, install `export/mm7_m312.glb` in place of the production export
(the install command and `actors.yml` binding in `../mm7_m312_claude/README.md` are unchanged):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m312_reduce_claude/export/mm7_m312.glb --world mm7
```

Rollback: `work/mm7_m312_source_pre_reduce.glb`. Add the model to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) when it
is installed.

Reproduce: `REA_NODE=M312 REA_GLB=<rollback source> import_source.py` -> `dump_mesh.py` -> `dump_faces.py` ->
`face_piece.py` -> `make_groups.py` -> ladder b (`REA_KEEP_FACES=work/keep_base.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.7,2:0.6,3:0.6,4:0.75,5:1.0,6:0.88,7:0.6,8:0.7,9:0.8 REA_HEIGHT_M=1.727 run_ladder.sh b 0.82`) ->
`REA_CAND=Cand_82 REA_ERR_MM=12 REA_LOCK_R=0.02 err_lock.py -- work/keep_base.npy work/keep_e.npy` -> ladder d
(`REA_KEEP_FACES=work/keep_e.npy`, `REA_GROUP_RATIOS=1:0.65,2:0.6,3:0.6,4:0.75,5:1.0,6:0.85,7:0.7,8:0.7,9:0.8`,
`run_ladder.sh d 0.81`) -> checks (`group_error.py`, `texture_drift.py r81`, `dark_slivers.py r81`, `close_human.py`,
`close_sheet.py`) -> build as above -> `lod_check.py` -> `viewer_variants.py` (export r81, rollback source r100) ->
`viewer_manifest.py`.

## Installed (2026-10-20)

User: "OK accept all, to assets_source, assets_dev". `check_winding.py` 0 inverted closed parts; installed with
`tools/install_model.py ... --world mm7` (sources in `assets_source/worlds/mm7/models/` equal the exports; cooked
runtime copies in `assets_dev/worlds/mm7/models/`). Nine `actors.yml` bindings added to
`assets_dev/worlds/mm7/models/actors.yml` from the production README's template (descriptor -> palette -> skin from
`../mm7_m312/variants.json` and the ramps file); every skin, clip, look node and attachment checked against both GLBs.
Boot check: `7out02.odm` (Harmondale) with spawned peasants of all five batch J models, 185 outdoor actors textured,
no missing models and no errors in the log (`output/batchJ_boot/`). Ledger row added to `../REDUCTION_LEDGER.md`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Hit sinks to -2.9; Walking sinks to -4.3; corpse at -6.0; dying sinks to -7.0; walking sinks to -4.3.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m312.glb export/mm7_m312.glb --lift-joints Dead Death Hit Walking --lift-only 'B_Skirt*,Robe_*,…' --ground-loop Walking --raise Hit --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m312.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [h13](../gait_rollout_20261031/h13/README.md) appended one clip to the installed source
`assets_source/worlds/mm7/models/mm7_m312.glb` (every existing clip, mesh, skin and material byte-identical): `Jog`
(humanoid set Unarmed-Run-Forward legs; arms from Walking; 0.62 s; the dress chains re-simulated on the new motion with h08's numpy port of robe_sim.py), bound for the peasants' flight (Wimps flee at 2x Spd in both rulesets) as `run: Jog`,
`run_stride_length: 2.395` (the package's `bindings.yml`, applied by the coordinator). A short, low run (swing height 0.25) keeps the shoes under the floor-length dress.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h13/scripts/rebuild.sh m312`, then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h13/export/mm7_m312.glb --world mm7
--name mm7_m312.glb`. A far-LOD repair, head-bob or reduction rerun that re-exports this model must re-graft the Jog: copy
the new source over `h13/work/mm7_m312_pre_gait.glb` and rerun the rebuild.
