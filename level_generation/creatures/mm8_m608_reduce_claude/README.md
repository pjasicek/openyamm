# MM8 Juggernaut (`m608`, Charger / Juggernaut / Demolisher) reduction (2026-10-19)

User-picked MM8 triangle-reduction batch 2 (session openyamm-f6). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: the installed textures, tier variants
(`KHR_materials_variants`) and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m608.glb` (SHA-256 `81986d80…`), byte-identical to
`../mm8_m608_codex/export/mm8_m608.glb` and to the source hash in that project's README (moving-shoulder revision,
user-approved 2026-10-18). The `assets_dev` copy differs only by the cook (`tools/cook_models.py`). It is copied to
`work/mm8_m608_source_pre_reduce.glb` (rollback source). `mm8_m608/` holds only the native source inventory.

The file has four skinned meshes on one 78-bone rig: `Juggernaut` (living body, 6,221), `Rubble` (death debris, 2,854:
61 rigid stones on bones `D_00`-`D_62` plus the broken band), `Eyes` (92, unlit) and `Flash` (152, blended palm flash).
Body and rubble swap at 0.25 s of Death: the collapsed one has its bones scaled to nothing and its node scale keyed to
0 (`tools/model_hide_collapsed_meshes.py`), so the alive creature draws body + eyes and the corpse draws the rubble.

## Body

Structure (`analyze.py`): a torso/head piece (2,272), two arm pieces with the big stone hands (1,195 / 1,064), three
rigid rollers (800), the waist band (180), 12 band studs, the two front shoulder caps (80 each) and four finger stones.
The creature's shoulder contract (`../mm8_m608_codex/scripts/shoulder_audit.py`) forbids faces that mix arm and torso
bones and requires the caps fully on their upper arm; the arms are separate pieces, and the piece-aware weights keep it
(`shoulder_rules.py`: 0 mixed faces and 0 non-rigid cap vertices at every colour/shadow LOD, as installed).

Keep sets: every piece up to 180 faces exactly (band, studs, caps, fingers: 890 faces, `REA_SMALL=180`), plus 2 cm
patches around the 14 rest points that carried the error in every frame (`region_err.py`, `patch_keep.py`, mirrored:
1,128 faces in all); the head (1,208 faces) at 80 % on its own.

Ladder (limits for the 1.0 m standing height: p99 3 mm, max 15 mm):

| config | step | triangles | p99 / max mm | |
|---|---|---:|---|---|
| source | | 6,221 | | |
| uniform, small pieces kept, head 80 % | 85 % | 5,287 | 2.74 / 13.76 | pass |
| | 80 % | 4,975 | 3.22 / 13.76 | fail |
| per region (torso 90 %, rollers 60 %, head 65 %) | 80 % | 5,029 | 3.02 / 13.76 | fail |
| **+ error-spot patches** | **82 %** | **5,099** | 2.94 / 7.78 | **pick** |
| | 81 % | 5,037 | 3.08 / 7.78 | fail |
| + rollers kept exactly | 85 % | 5,285 | 3.19 / 7.78 | fail |

The body has little slack: the build already sits at a low density (the stone is faceted by its shading, not by
triangles), and the error is spread over arms (63 %), head (22 %) and torso, not concentrated in spots. The cut stays
gentle (18 %). Texture drift at the pick: 3 faces over 40 (4.5 cm²), no drift lock.

Additions to the picked candidate (`build.sh`):
- **Rollers clamped** (`roller_clamp.py`): 38 vertex moves put new roller vertices back inside the source rollers'
  rolling contour; the reduced rollers otherwise dipped 1.4 mm under the floor in Walking. LOD0 now stays on or above
  the floor in every clip, as installed.
- **Hole closed** (`patch_hole.py`, +24 triangles): the installed body has an open 28-edge loop on the chest behind
  the left shoulder. The engine culls back faces, so the background shows through beside the raised left arm in the
  Attack wind-up (`review/hole/sheet_src.png`, magenta). It is closed with 26 faces from its rim (no new vertices,
  Chest weights) mapped into a stone UV island at the rim's texel density (`review/hole/sheet_r82.png`). The only other
  open loop is a two-edge slit at the left upper arm (zero area).
- **Normals**: the installed body shades smooth up to 45 degrees (`split_angle.py`: 97.6 % of its hard edges); the
  candidate gets the same smooth-by-angle normals in `export_cand.py` (`REA_SHADE=angle:45`), so the stone edges stay
  crisp. Never `REA_NORMALS=transfer`.

## Rubble

Its own sub-project (`rubble/`, same scripts). The stones are flat-shaded and small (12-72 triangles each); pieces of up
to 20 faces are kept. The error is measured only where the rubble shows (Death frames 12-18 and Dead, `rubble_err.py`;
the ladder's own numbers are diluted by the collapsed alive clips and its renders are empty):

| step | triangles | p99 / max mm | |
|---|---:|---|---|
| source | 2,854 | | |
| **80 %** | **2,282** | 2.97 / 4.69 | **pick** |
| 70 % | 1,996 | 3.93 / 11.22 | fail |

Flat normals (`REA_SHADE=flat`). Drift: 1 face over 40 (1.5 cm²).

## Build

`build.sh`: `roller_clamp.py` -> `patch_hole.py` -> `export_cand.py` (body, Cand_82; rubble, Cand_80) -> `swap_lod0.py`
twice -> `rubble_contacts.py` -> `build_lods.py` -> `carry_variants.py` -> `tools/model_hide_collapsed_meshes.py --write`
-> `fix_lod_normals.py` (the creature's own LOD normal repair) -> `check_winding.py` -> `compare_glb.py` ->
`shoulder_rules.py`. The LOD builder follows the creature's `build.py` (body then rubble, 4 influences; body
0.5 / 0.25 / 0.125). The rubble's LOD1-2 take 0.6 / 0.28: at 0.5 the band turned octagonal and lost its studs already at
LOD1, where the installed LOD1 kept it round. Its floor contacts in Death/Dead (35 points, `rubble_contacts.py`) are
locked in every LOD (a first rebuild put LOD3 8.5 mm under the floor in Dead). The glTF importer gives the node names
to empties, so `build_lods.py` and `lod_check.py` look the mesh objects up by mesh name (as m536).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| body installed | 6,221 | 3,110 | 1,554 | 763 |
| body reduced | 5,123 | 2,561 | 1,279 | 627 |
| rubble installed | 2,854 | 1,426 | 706 | 325 |
| rubble reduced | 2,282 | 1,368 | 625 | 252 |
| file total (+ eyes 92, flash 152) | 9,319 → 7,649 | | | |

`export/mm8_m608.glb`, 7.6 MB (installed 8.3 MB). `compare_glb.py`: Eyes and Flash byte-identical (every accessor),
nodes, skins, all seven clips (channel data), materials, variants and images unchanged; collapsed-mesh visibility spans
identical to the installed file. Winding: 0 inverted closed parts.

`work/lod_check_red_{Juggernaut,Rubble}.json` (every frame of every clip): no stretched faces at any LOD. Body: LOD0
lowest point 0.0 mm (Walking +1.0 mm, as installed), LOD1-3 -1.3 / -2.4 / -10 mm in Walking (installed -1.9 / -4.0 /
-11.9); top 1.000 / 1.000 / 0.998 / 1.008 m (installed 1.000 / 1.000 / 1.003 / 0.999). Rubble: Dead 12 mm above the
floor at every LOD (installed LOD3 11.4 mm), Death lowest +2.9 / +2.8 / +1.6 / -4.8 mm (installed +3.0 / +2.2 / -4.0 /
-4.0). `review/lods/sheet.png`: installed / reduced, LOD0-3, body standing and rubble dead.

Close-ups straight from both GLBs (`glb_close.py`, the file's own normals; `review/glbclose/sheet_{a,b,c,d}.png`:
head, torso, back, shoulders, both arms masked out, hands, rollers, band, Attack, Hit, Death, Dead; installed / reduced,
textured then clay) show the face, eyes, brow, hands, fingers, caps, band and studs unchanged. The reduced rollers and
head shade slightly smoother than the installed faceting (45-degree smoothing over larger faces).

## Source animation scan

`clip_scan.py` (48 fps, viewer frame = time × 48; Root, Waist, Chest, Head, hands, rollers): no single-frame pops, no
loop seams (Standing, Walking, Attack, Hit and Fidget close exactly) and no dead start (Attack moves from frame 2,
0.042 s; there is no Cast clip). Walking keeps the head at a constant 0.865 m (the rollers carry the root). The fastest
moves are the Hit recoil (frames 1-6) and recovery (frames 46-51), both 3-frame swings of the hands up to 76 mm per
frame with smooth ramps, and the Death recoil (frames 0-6); they follow the native timing. Not checked numerically:
hands against the torso (the Hit clasp in front of the chest looks clean in `review/glbclose/*_hit_*`).

## Review

Viewer: <http://127.0.0.1:8912/level_generation/creatures/mm8_m608_reduce_claude/review/viewer/> (installed vs reduced
for Charger, Juggernaut and Demolisher; ramps baked into preview copies as in the creature's own viewer; body, rubble,
eyes and flash as the game draws them). `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_m608_reduce_claude check`: 42 model/clip switches, no console errors.

## Status

Installed 2026-10-19 after user review ("juggernaut ok") via `tools/install_model.py --world mm8`; actor regression `mm8_juggernaut_actor_models_keep_rollers_tiers_and_roles` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Install (from the repository root):
`python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m608_reduce_claude/export/mm8_m608.glb`,
then `OPENYAMM_REGRESSION_FILTER=mm8_juggernaut_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_juggernaut_actor_models_keep_rollers_tiers_and_roles`) and add the ledger row.
Rollback: `python3 tools/install_model.py --world mm8
level_generation/creatures/mm8_m608_reduce_claude/work/mm8_m608_source_pre_reduce.glb`.

Reproduce: `REA_GLB=<abs rollback source> REA_NODE=Juggernaut.003 import_source.py` -> `REA_PROTECT=Head dump_mesh.py`
-> `REA_SMALL=180 small_pieces.py` (copied to `work/keep_small180.npy`) -> `dump_groups.py`, `m608_sets.py` ->
`REA_PATCH_R=0.02 patch_keep.py work/keep_small180.npy work/keep_p.npy -0.238,0.184,0.704 -0.234,0.108,0.804
0.217,0.158,0.782 -0.143,0.035,0.548 0.01,0.084,0.958 0.262,0.136,0.525 0.353,0.119,0.532 -0.318,0.087,0.482
0.256,0.072,0.468 0.087,0.125,0.551 -0.171,0.072,0.66 -0.273,0.076,0.726 -0.208,0.102,0.819 -0.009,0.212,0.651`
(the `region_err.py` SPOT points of a first per-region ladder) -> `REA_KEEP_FACES=work/keep_p.npy REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.8 run_ladder.sh p
0.82,...`; rubble: in `rubble/`, `REA_NODE=BandShard import_source.py` -> `dump_mesh.py` -> `REA_SMALL=20
small_pieces.py` (`work/keep_s20.npy`) -> `REA_KEEP_FACES=work/keep_s20.npy run_ladder.sh u 0.8,0.7,0.6,0.5` ->
`rubble_err.py`; then `build.sh`, `lod_check.py` (`REA_NODE=Juggernaut|Rubble`), `lod_views.py`, `glb_close.py`,
`hole_views.py`, `texture_drift.py`, `clip_scan.py`, `viewer_build.py`.

## Floor fix — 2026-10-21

`--ground-death Death Dead`: the rubble corpse rested 12 mm above the floor (4.8 world units); Death now settles onto it. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m608.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.
