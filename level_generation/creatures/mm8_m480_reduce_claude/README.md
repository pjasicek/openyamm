# MM8 Troll Peasant (`m480`, Troll Pesant A/B/C) reduction (2026-10-19)

User: "OK do these ones" (MM8 batch: m420, m416, m500, m508, m480). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant (UVs kept, so the shared atlas, the three
material variants and the region ramps stay valid). No Meshy credits. Scripts copied from the installed Troll
reduction [mm8_m476_reduce_claude](../mm8_m476_reduce_claude/README.md) (per-region groups, UV weights, error lock,
dark-sliver lock), adapted to the peasant, who holds its club in the right hand.

Source: installed `assets_source/worlds/mm8/models/mm8_m480.glb`, identical (sha1) to `mm8_m480_claude/export/`;
copied to `work/mm8_m480_source_pre_reduce.glb` (rollback source). One material `TrollPeasant_A` (B/C are variants),
mesh node `TrollPeasant`, 53 joints, 4 influences, 8 clips, a full-detail shadow mesh plus shadow LOD1-3.

**Club.** The peasant binds `mm8_m480_club.glb` to node `Club` (`actors.yml`, three tiers; the Troll binds
`mm8_m476_club.glb`). At 1,668 triangles it is light and left unchanged; the review viewer merges the installed club.

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| body installed | 9,744 | 4,869 | 2,424 | 1,205 |
| body reduced | **7,598** | 3,788 | 1,888 | 935 |

Body -22 % (club unchanged, LOD0 total 11,412 -> 9,266). LODs use the production build's ratios and influence
budget (`tools/build_actor_lods.py`, 0.5 / 0.25 / 0.125, 4 influences), shadow LOD1-3 tucked inside with the
production `shrink_shadow_lods.py`, variants carried to every LOD and shadow primitive (`carry_variants.py`).
`export/mm8_m480.glb`, 5.0 MB (installed 5.3 MB). Clips byte-identical, materials, extras, node list and the
`openyamm_lods` / `openyamm_shadow_lods` layout as installed; `check_winding.py`: 0 inverted closed parts.

## Ladder

The head texture set is 60 % of the mesh (5,850 of 9,744 faces: face, ears, scalp, the crest of hair locks and the
horns); the body (belly, arms, legs, loincloth) has only about 1,400 faces outside the hands. Limits scaled to the
1.756 m height: p99 5.27 mm, max 26.3 mm.

- Kept exactly (3,810 faces): small separate pieces up to 160 faces except the crest locks (horns, small hair
  locks, toenails), the right-hand finger faces (the fitted club grip), soles (below 6 cm), the face pieces (eyes,
  teeth, gums, tongue: pieces up to 200 faces in front of the face) with the skin within 1.5 cm of the mouth
  (`lip_keep.py`), 3 cm patches around 16 source vertices the transfer missed by over 15 mm (two `err_lock.py`
  rounds: torso side under the left arm, both clavicles at the upper back, the left forearm) and one lock round
  around the strong dark slivers (eye rims and left-hand fingers; `dark_slivers.py` with 5 of 48 samples,
  `drift_lock.py` with `REA_LOCK_AREA=0`).
- Groups (`decimate_tex.py`): body skin and loincloth 90 %, hands 50 %, the 19 crest locks of 30-160 faces 70 %,
  head skin (face, ears, scalp, larger hair masses) takes the rest of the budget.
- Weights: UV-based (`REA_WEIGHTS=component`, `uv_weights.py`).

| ladder | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| f70 (face 70 %, body takes the cut) | 80 % | 7,792 | 7.1 / 49.9 | 0.984 | 0.985 | fail (belly collapses) |
| b90 (body 90 %, head takes the cut) | 80 % | 7,792 | 2.91 / 52.2 | 0.994 | 0.994 | fail (weights at the torso side) |
| e2 (+ two error locks) | 80 % | 7,792 | 2.75 / 15.0 | 0.995 | 0.995 | pass |
| e2 | 76 % | 7,402 | 3.22 / 24.8 | 0.995 | 0.994 | pass, face soft (rejected) |
| v4 (+ crest locks 70 %) | 76 % | 7,402 | 5.22 / 18.6 | 0.994 | 0.994 | pass |
| **v5 (+ dark-sliver lock)** | **78 %** | **7,598** | 5.18 / 24.8 | 0.993 | 0.994 | **pick** |
| v5 | 76 % | 7,402 | 5.34 / 33.0 | 0.993 | 0.994 | fail (p99, max) |

The face is the limit: at 73-76 % of the e2 ladder the brow and cheek folds flattened and the nose picked up dark
texture drift (`review/glb/sheet_face.png`, source / 80 / 76 / 73). Cutting the crest locks at 70 % instead gives
the face the same budget as e2's 80 % step with no visible change to the crest (`review/glb/sheet_v4.png`). The
pick's largest remaining miss (24.9 mm, Hit) is at the nape under the crest; the face misses at most 15 mm.

Close-ups straight from the GLBs (own normals), source | pick, textured and clay: `review/glb/sheet_pick.png` (face,
side, mouth, crest, club hand from both sides, free hand, torso front and back, feet, the attack wind-up from below
and from the side, Death). Face, mouth, teeth, eyes, horns, crest, both hands, belly, loincloth and toes match; the
brow and cheek folds are a little softer in clay and unchanged in texture.

Texture: `texture_drift.py r78`: no face over 40, p99 10.5; `dark_slivers.py r78`: none with 5 or more dark samples
(8 faces with 2-4, invisible in the close-ups). No split seams (no coincident vertices with other weights).

## LOD check

`work/lod_check_{src,r78}.json` (`REA_NODE=TrollPeasant lod_check.py`): every LOD keeps the source rest bounds
(1.22 x 0.57 x 1.70 m; LOD3 top 1.706 m, installed 1.709), no face stretches over 20x in any clip at any LOD
(installed LOD2: 1 face in Attack and Running), lowest point per clip as installed (Attack -3.5 mm at LOD0-1, as in
the source; the LOD3 corpse rests 12 mm above the floor, installed 4 mm). `review/lods/sheet.png`: installed and
reduced LOD0-3, standing three-quarter and the attack release; LOD3 keeps the toes better than the installed LOD3.

## Viewer

`review/viewer/` (revision `reduce-r78`): installed and reduced for each tier, the installed club merged under the
`Club` bone for review only (`merge_club.py`), tier ramps baked with the engine rule (`viewer_variants.py`), clips and
native anchors from the production viewer (`viewer_manifest.py`). `node
level_generation/creatures/claude_shared/check_viewer.mjs
http://127.0.0.1:8912/level_generation/creatures/mm8_m480_reduce_claude/review/viewer/`: 48 model/clip switches, no
console errors. `review/viewer_shot.png` is its default view.

Not changed and not checked here: the clips (Walking foot contact, which the Troll m476 needed fixed after review).

## Status

Installed 2026-10-19 (user: "troll peasant ok"); winding 0, the regression passes and the row is in the ledger. Install (after `check_winding.py`):

```sh
python3 tools/install_model.py level_generation/creatures/mm8_m480_reduce_claude/export/mm8_m480.glb --world mm8
OPENYAMM_REGRESSION_FILTER=mm8_troll ./build/game/openyamm --world mm6 --headless-run-regression-suite actors
```

The cases are `mm8_troll_peasant_actor_models_keep_native_tiers_and_bone_club` and
`mm8_troll_actor_models_keep_native_tiers_and_club` (`game/outdoor/HeadlessOutdoorDiagnostics.cpp`). No binding
changes (same scale, clips, impact and club). Then add the row to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m480_source_pre_reduce.glb` the same way.

## Reproduce

`REA_NODE=TrollPeasant REA_GLB=level_generation/creatures/mm8_m480_reduce_claude/work/mm8_m480_source_pre_reduce.glb
blender -b -P scripts/import_source.py` -> `dump_mesh.py`, `dump_bones.py`, `dump_weights.py` (Blender) ->
`REA_SMALL=160 small_pieces.py` (also `work/piece.npy`) -> `make_groups.py` -> `lip_keep.py work/keep.npy
work/keep_lips.npy` -> groups face/body/hands (`work/groups_face0.npy`), ladder, `err_lock.py` twice
(`work/keep_err.npy`, `work/keep_err2.npy`) -> crest locks as group 4 (`work/keep_v3.npy`, `work/groups_v4.npy`) ->
`REA_DARK_N=5 dark_slivers.py r76`, `REA_LOCK_AREA=0 drift_lock.py work/keep_v3.npy work/keep_v5.npy r76` ->
`REA_WEIGHTS=component REA_KEEP_FACES=work/keep_v5.npy REA_GROUPS=work/groups_v4.npy
REA_GROUP_RATIOS=1:0.9,2:0.5,4:0.7 run_ladder.sh v5 0.78,0.76,0.74` (`work/ladder_v5.blend`, copy `work/ladder_pick.blend`)
-> `REA_CAND=Cand_78 REA_NODE=TrollPeasant export_cand.py` -> `swap_lod0.py <source> work/cand_export.glb
work/r78_lod0.glb TrollPeasant` -> `blender -b -P scripts/build_lods.py` -> `shrink_shadow_lods.py work/r78_lods.glb
work/r78_shadow.glb` -> copy to `export/mm8_m480.glb` -> `carry_variants.py export/mm8_m480.glb`. Checks:
`texture_drift.py`, `dark_slivers.py`, `lod_check.py`, `lod_views.py`, `glb_views.py` + `sheet.py`, viewer as above.

## Gait rollout (2026-10-31)

New locomotion clip: `Walk2` (humanoid set Armed-Walk, 1.15 s, stride 1.1977) for wandering at 1.09 u/s (`Walking`
played it at x0.58); flight keeps `run: Walking` (walk-as-run, Froude 0.57). Package
[h20](../gait_rollout_20261031/h20/README.md) appended them to the installed source
(`assets_source/worlds/mm8/models/mm8_m480.glb`; existing clips, meshes, skins and materials byte-identical; pre-gait
copy `../gait_rollout_20261031/h20/work/mm8_m480_pre_gait.glb`) and installed it; the bindings are in
`../gait_rollout_20261031/h20/bindings.yml` for the rollout coordinator. Rebuild:
`level_generation/creatures/gait_rollout_20261031/h20/scripts/rebuild.sh m480`. A far-LOD repair, head-bob, reduction or
texture rerun that rebuilds this source must keep or re-graft these clips (copy the new source over the pre-gait copy
and rebuild).
