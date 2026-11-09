# MM8 Ogre Peasant (`m436`, Ogre Pesant Male A/B/C) reduction (2026-10-18)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: the UVs are kept, so the
merged body + head atlas, the three palette variants and the region ramps stay valid. No Meshy credits. Scripts are
copied from [mm8_m560_reduce_claude](../mm8_m560_reduce_claude/README.md), with the m492 coincident-vertex fixes.
Per-region budgets follow the humanoid reductions (`mm6_ogr_reduce_claude`, `mm6_fgt_reduce_claude`).

The source is the installed `assets_source/worlds/mm8/models/mm8_m436.glb`, identical (sha256 `0be515b6…`) to
`mm8_m436_claude/export/mm8_m436.glb` (`m436_civilian_v3`, accepted 2026-10-18). It is copied to
`work/mm8_m436_source_pre_reduce.glb` as the rollback source. It has one material `M436_A` (B/C are variants), mesh
node `M436` and 4 influences. The 1.70 m bind height gives limits of p99 5.1 mm and max 25.5 mm.

## Where the triangles are

Weld 9,876 -> 1,572 open edges. The weld leaves 6 coincident vertices that carry different weights, and nothing
stretches (`stretch_check.py`). `make_groups.py` labels every face:

| part | faces | treatment |
|---|---:|---|
| 340 small pieces (hair tufts of 1-14 faces, eyes, pack details) | 2,425 | kept exactly |
| ragged shorts | 626 | kept exactly: the tatter tips at the inner thighs moved 22 mm even at 90 % |
| fingertips (distal finger bones), toes, soles (below 1 cm) | 1,925 | kept exactly |
| face, scalp and neck skin (head atlas half of the main piece) | 2,026 | 45 % |
| hands and fingers without the tips | 1,539 | 55 % |
| feet above the soles, without the toes | 663 | 65 % |
| vest / pack / straps / belt | 777 / 803 / 436 / 421 | 75 / 65 / 75 / 55 % |
| body skin (arms, legs, torso) | 2,846 | rest of the ladder (60 %) |

The body skin is already sparse: 2,846 faces cover the whole torso, arms and legs. Most of the mesh is the head, the
hands, the feet and the 340 hair tufts. The tufts are 12-14-face spikes that cannot be cut, so the model has less
slack than the dragons.

Skin no ray reaches in the Standing pose is left out of the ladder error (`vis_mask.py` ->
`work/hidden.npy`, `REA_HIDDEN` in `reduce_ladder.py`): 1,713 vertices under the vest, shorts and pack. Poke-through
would still show as candidate-to-source error on visible surfaces. `region_error.py` prints the error per group.

## Ladder

| config | step | triangles | p99 / max mm | IoU | SSIM | finding |
|---|---|---:|---|---|---|---|
| a: clothing all 60 %, head 70 %, hands 50 % | 70 % | 10,279 | 5.33 / 30.98 | 0.995 | 0.987 | fails: shorts tatter tips |
| b: shorts 85 % | 73 % | 10,595 | 4.89 / 22.72 | 0.995 | 0.988 | tatter tip still 22 mm |
| d: shorts kept, head 40 %, hands 40 % | 69 % | 10,001 | 4.36 / 13.53 | 0.995 | 0.990 | fingertips taper to points |
| e: + fingers 65 % | 71 % | 10,421 | 4.83 / 13.53 | 0.995 | 0.989 | tips still pointed, knuckle seam |
| f: fingertips kept, hands 55 % | 72 % | 10,471 | 4.59 / 20.0 | 0.995 | 0.989 | toes turn into spikes at feet 50 % |
| h: + toes kept, head 35 % | 71 % | 10,367 | 5.0 / 20.0 | 0.994 | 0.988 | crease where the kept toes meet the foot; face slightly soft |
| **i: head 45 %, feet 65 %** | **72 %** | **10,527** | 4.98 / 20.6 | 0.995 | 0.989 | **picked** |

Close-ups (clay with the source's scrambled custom normals cleared, and textured) are in `review/close/`:
`sheet_d_*` (first look), `sheet_e_hands`, `sheet_f_hands`, `sheet_feet` (toe spikes), `sheet_h_*` and `sheet_i`
(the pick). The final shading is judged from the GLBs themselves, with their own normals (`glb_close.py`):
`review/glbclose/sheet_clay.png` and `sheet_tex.png` compare installed and reduced. Face, hair, hands, toes, torso,
pack, shorts and corpse match. Texture drift (`texture_drift.py`): 2 faces over 40, 0.5 cm² in total; no lock.
The 20.6 mm max is the chest front (`B_Spine`) in Running frame 12, from skinning against the swinging arm. At
rest the error there is under 1 mm.

## Build

`scripts/build_export.sh`: `export_cand.py` (Cand_72 of `work/ladder_i.blend`) -> `swap_lod0.py` ->
`build_lods.py` -> `shrink_shadow_lods.py` -> `carry_variants.py` -> shared gates. The m436 project's LOD settings
are kept: 4 influences, protected sole and wrist vertices and the shadow tuck. LOD3 uses ratio 0.117 instead of
0.10, because the gate runner needs LOD3 at 10 % of LOD0 or less and a hand edge region in every LOD. Ratios 0.10
and 0.11 collapsed the hands (938 and 973 triangles). The result is `export/mm8_m436.glb`, 5.86 MB (installed
6.69 MB), with 7 clips and 3 variants on all 8 colour/shadow meshes.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 14,488 | 7,174 | 3,311 | 1,272 |
| reduced | 10,527 | 5,152 | 2,344 | 1,047 |

Checks:
- **Shared gate runner:** `claude_shared/gates/run_gates.sh` with `mm8_m436_claude/gates.json` gives **PASS**, with
  5,210 checks, the same count as the installed model (`review/gates/gates.md`).
- **LOD bounds:** `lod_check.py` (`work/lod_check_{src,r72}.json`) shows LOD0-2 keep the source bounds, and LOD0
  matches exactly. LOD3 is 2.5 cm narrower at the T-pose fingertips (installed LOD3 0.4 cm).
- **Floor:** every frame stays above the floor as in the source, except LOD3 in Death, which dips to -26 mm
  (installed LOD3 -6.6 mm).
- **Stretched faces:** one face in Death/Walking on LOD1-3, as in the installed LODs.

Viewer: `review/viewer/` shows installed (r100) and reduced (r72) for each tier
(`http://127.0.0.1:8912/level_generation/creatures/mm8_m436_reduce_claude/review/viewer/`). The ramps are baked for
the browser by `viewer_tiers.py`, with clips and native anchors from the m436 viewer. The wrapper check
(`tools/run_creature_review.py ... check`) made 42 switches with no console errors.

**Viewer bake fix (user review, 2026-10-18).** The user saw a camouflage patchwork in the viewer: green face, brown
and green patches over the skin, and vest and shorts lost in it. The model was not at fault. The first
`viewer_tiers.py`, copied from the m436 project, baked the tiers from that project's 1K **body-only** base colour and
region mask (`textures/m436_basecolor_1k.png`). The runtime GLB, installed and reduced alike, uses the merged
2080x1024 **body + head atlas**, so every UV sampled the wrong texture. The installed entries in the viewer were
broken the same way. `viewer_tiers.py` now bakes from the GLB's own runtime material: the embedded base colour, the
`openyamm_region_mask` texture and each variant material's ramps. `review/tiers/sheet.png` shows, front and back,
the old bake (`oldbake_a`, reproducing the screenshot) and then installed and reduced for tiers A, B and C. Installed
and reduced match, so no retexture is needed. After the fix, the viewer check made 42 switches with no console
errors, and the gates still pass (5,210 checks).

## Status

Installed 2026-10-18 (user: "ogre peasant ok") with `tools/install_model.py --world mm8`; both Ogre peasant unit tests pass. Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Commands used:
`python3 tools/install_model.py level_generation/creatures/mm8_m436_reduce_claude/export/mm8_m436.glb --world mm8`.
Then build `openyamm_unit_tests` and run `--test-case='*Ogre peasant*'` (`ModelAnimation mm8 Ogre peasant keeps
civilian motion and a grounded corpse`, `mm8 Ogre peasant bindings resolve all civilian tiers…`), and add the row to
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m436_source_pre_reduce.glb`.

Reproduce:
1. `import_source.py` (`REA_NODE=M436`, `REA_GLB` = the rollback source)
2. `dump_mesh.py` (`REA_PROTECT=B_Head`), `dump_weights.py`, `vis_mask.py`, `make_groups.py`
3. `REA_HIDDEN=work/hidden.npy REA_HEIGHT_M=1.70 REA_GROUP_RATIOS=1:0.45,2:0.55,3:0.55,4:0.65,6:0.75,7:0.65,8:0.75,9:0.55 run_groups.sh i 0.7,0.6`
4. `stretch_check.py`, `close_ladder.py`, `close_sheet.py`, `texture_drift.py`, `region_error.py`
5. `cp work/ladder_i.blend work/ladder.blend`, then `build_export.sh`
6. `REA_NODE=M436 lod_check.py`, `glb_close.py`, `viewer_tiers.py` (installed r100, reduced r72), `viewer_manifest.py`, `tier_front.py`

## Gait rollout (2026-10-31)

Package h19 of the [gait rollout](../gait_rollout_20261031/h19/README.md) appended new clips to the installed source
for Ogre Pesant Male A/B/C: `Walk2` (a slower stroll for wandering: Mixamo Orc Walk (1) legs on this model's `Walking` arms, 1.2 s, wider track). Existing clips, meshes and skins are unchanged (binary prefix identical). Installed 2026-10-31
with `tools/install_model.py --world mm8`; bindings for the coordinator (`../gait_rollout_20261031/h19/bindings.yml`):
walking: Walk2, stride_length: 1.2383; the walk-as-run flight keeps run: Walking, run_stride_length: 1.695. `gait_gate.py` passed for every tier under Standard and MAW
(`../gait_rollout_20261031/h19/review/m436_gait_gate.txt`). Rebuild: `../gait_rollout_20261031/h19/scripts/rebuild.sh
m436` (from the pre-gait copy `../gait_rollout_20261031/h19/work/mm8_m436_pre_gait.glb`). A far-LOD repair, head-bob or
reduction rerun replaces the source without these clips: copy the new source over that pre-gait copy and rerun the
rebuild before installing. Rollback: install the pre-gait copy and drop the bindings.
