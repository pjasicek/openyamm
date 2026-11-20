# MM8 Lizardman Warrior (`m404`, Soldier / Sergeant / Captain) reduction (2026-10-19)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) including its MM8 batch lessons. Scripts are
copied from `mm8_m604_reduce_claude/` (parent-transform fix, exact weights, coincident-vertex handling, lod_check,
the sword prop chain) and `mm8_m524_reduce_claude/` (`floor_contacts.py`). No Meshy credits. Not installed.

Sources: the installed `assets_source/worlds/mm8/models/mm8_m404.glb` and `mm8_m404_sword.glb`, byte-identical to
`../mm8_m404/3d_claude/export/`; rollback copies `work/mm8_m404_source_pre_reduce.glb` and
`work/mm8_m404_sword_source_pre_reduce.glb`. The Lizardman Peasant reduction (`mm8_lizardman_peasant_reduce_claude/`)
was read as precedent only.

**Animation untouched.** Another session refit this warrior's Attack (Mixamo "Great Sword Slash (2)") onto the Dark
Elf warrior m432 and is waiting on the user's review. This reduction changes geometry, weights, LODs and the region
mask only. The export's clips, nodes, skin and inverse bind matrices hash identically to the installed GLB (all 8
clips, every sampler). Files in the m404 and m432 projects were only read.

Shading is judged from GLBs imported directly (`viewer_views.py`, `sword_views.py`). The welded `source.blend`
renders use `CLOSE_SMOOTH_SRC=1` and compare geometry only. Plain smooth normals: the installed body shades smooth.

## Body

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 11,229 | 5,613 | 2,019 | 670 |
| reduced | **8,981** | 4,489 | 1,616 | 537 |

Weld 7,089 -> 441 open edges; no coincident vertices with different weights. Limits for the 1.90 m figure: p99
5.7 mm, max 28.5 mm. Four influences, as installed. The production build had already reduced the body before
texturing and kept the detailed 3,182-triangle head, the hands and the feet, so most of the headroom is in the head.

Regions (`scripts/face_bones.py`, `make_groups.py`):
- **Kept exactly:**
  - the fingers of both hands and both palms: both hands grip the hilt, and at 50-75 % the back of the right hand
    smeared its scales (`review/close/sheet_h1.png`);
  - ivory claws, toe claws and calf spurs found by base colour, plus one ring of faces;
  - the gold collar, belt and bracer studs, plus one ring;
  - the teeth and the small neck spines. These are head faces within 8 mm of a sharp cone tip below 1.76 m (angle
    deficit over 0.6 rad). At a 45 % head cut they shrank (`review/close/sheet_head_g.png`). The long crest spines
    keep their shape at that cut;
  - soles (faces below 3 cm), the belt-buckle piece, and the drift and fleck locks below.
- **Own budgets:** head 47 %, feet 55 %, mantle and loincloth 70 %, tail 85 % (already coarse).
- **Rest** (torso, arms, thighs, ~2,300 faces) takes the remaining budget. Below ~80 % of the total its error grows
  quickly.

| run | head / palm / feet / cloth | step | triangles | p99 / max mm | |
|---|---|---|---:|---|---|
| g1 (no tip lock) | 55 / 60 / 60 / 65 | 77 % | 8,643 | 4.97 / 28.17 | pass |
| g2 (no tip lock) | 45 / 50 / 55 / 60 | 75 % | 8,417 | 5.08 / 24.11 | pass; teeth and neck spines shrank |
| g4 (tips kept) | 40 / 50 / 55 / 60 | 78 % | 8,755 | 5.46 / 20.31 | pass; brow and cheek softer |
| g6 | 47 / 50 / 55 / 60 | 78 % | 8,755 | 5.43 / 24.11 | pass; flecks at the right knuckle and left collar |
| g10 (+ fleck locks) | 47 / 50 / 55 / 60 | 80 % | 8,981 | 5.35 / 46.14 | fail: mantle front edge lost |
| g12 | 47 / 50 / 55 / 70 | 79 % | 8,867 | 5.35 / 24.11 | pass; right-hand scales smeared |
| g13/g14 (red hem kept) | 47 / 50 / 55 / 70 | 79 % | 8,867 | 5.6 / 28.17 | pass, but 7-12 new flecks; dropped |
| h1 | 47 / 75 / 55 / 70 | 80 % | 8,979 | 4.96 / 24.11 | pass; hand still smeared |
| **h2** | **47 / kept / 55 / 70** | **80 %** | **8,981** | **5.27 / 28.17** | **picked** (IoU 0.9915, SSIM 0.9945) |

The h2 max sits at Attack frame 6, the same spot as in most runs, just under the limit. h2 at 81 % has 9,093
triangles (4.94 / 24.11 mm) if more margin is wanted.

Colour checks:
- `texture_drift.py`: no face over 40 on the pick.
- `scripts/fleck_check.py` (new) compares 48 samples per face with the source surface and flags small slivers
  that the median drift misses. It found a pale chart-border sliver on the left mantle shoulder, two at the neck
  collar and one at the teeth edge.
- Two lock rounds (`work/keep_lock4.npy`: the source faces within 2 cm) leave 0 flecks.

Remaining small difference: a 2-pixel notch in the red mantle hem at the right shoulder (`collar_r` close-up).
Keeping the hem by colour caused more flecks than it removed.

Sheets in `review/close/`:
- `sheet_h2_body.png` and `sheet_h2_hands.png` (source / pick);
- `sheet_head_g6.png` (head clay).

Build: `export_cand.py` (Cand_80) -> `swap_lod0.py` -> `floor_contacts.py` -> `build_lods.py` (the installed
model's own ratios 0.5 / 0.18 / 0.06, 4 influences) -> `../mm8_m404/3d_claude/scripts/shrink_shadow_lods.py` ->
`carry_variants.py` -> `mask_fix.py` + `swap_mask.py`.
- **Protected points:** only the exact bounding-extreme vertices plus the 53 Death/Dead floor contacts. The m604 2 cm
  extreme band (549 points) broke LOD3 into shards (`review/lods/sheet_tries.png`). Without the floor contacts, LOD3
  sank 5 cm into the floor in Death.
- **`lod_check.py`** (`work/lod_check_r80.json`): no stretched faces in any clip at any LOD. Floor minimum is -1.5 mm
  in Death at every LOD (installed: +2.0 mm at LOD0, -1.5 mm at LOD2/3); every other clip is at least +0.8 mm.
- **Bounds:** LOD0 and LOD1 keep the full bounds. LOD3 is 3 cm shorter at the -x extreme, as the installed LOD3 was
  (2.5 cm).
- `review/lods/sheet.png` compares all LODs at rest, at the attack impact and as a corpse.

## Sword

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 932 | 466 | 166 | 54 |
| reduced | **660** | 466 | 166 | 54 |

Parts: blade 444, guard 284, grip and pommel 204. `prop_parts.py sword c55_75 0:0.55,1:0.75` keeps the grip
exactly, so the fitted grip in both hands is unchanged. Blade is at 55 % and guard at 75 %, with a max deviation of
0.168 % of the 1.65 m length (2.8 mm). The blade at 45 % and the guard at 60 % each moved 1 % or more: the wave
crests and the guard tips.

Normals: by angle at 20 degrees (`PROP_NORMALS_ANGLE=20`); the grip keeps transferred normals. Transferred normals
on the reduced blade broke into dark blocks (`review/sword/sheet.png`). LOD1-3 are kept.
`review/sword/sheet_export.png` compares source and export.

## Retexture check

- **Texture set:** one material per tier (`M404_A/B/C`) over a shared 2080x1024 atlas (body half, head half), with
  a region mask using the R channel for the mantle and one ramp per tier. The reduction keeps the UVs; base colour,
  normal and metal-roughness are byte-identical.
- **Mask fix (fault in the installed model):** Meshy painted the torso under the mantle green (neck, collarbones,
  upper back; 308 faces), outside the mantle mask. Tiers B and C showed green patches beside the blue / red mantle
  at the shoulders and chest. `scripts/mask_fix.py` adds the green texels of the faces that are over 25 % unmasked
  green to channel R (36,180 texels). The base colour is unchanged. Those patches now take the tier colour, lighter
  than the mantle, as tier A's lighter green: `review/tiers/sheet_maskfix.png` (installed / reduced + fix per tier).
  The export before the fix is `work/mm8_m404_r80_pre_maskfix.glb`.
- **Head and body:** no other faults. Eyes, teeth, crest colours and scale detail match the installed model in every
  tier. No Meshy retexture is needed.

## Viewer

`review/viewer/`: installed / reduced per tier, sword included (`viewer_build.py`, tier ramps baked as in
`../mm8_m404/3d_claude/scripts/viewer_tiers.py`). `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_m404_reduce_claude check`: 48 switches, no console errors.

## Status

Installed 2026-10-19 (user: "lizardman warrior ok"). `check_winding.py`: 0 inverted closed parts (body and sword).
Installed both with `tools/install_model.py ... --world mm8` (the rollback sources matched the installed GLBs byte for
byte first). `OPENYAMM_REGRESSION_FILTER=mm8_lizardman_warrior ./build/game/openyamm --world mm8
--headless-run-regression-suite actors`: `mm8_lizardman_warrior_actor_models_keep_tiers_sword_and_native_roles`
passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install
`work/mm8_m404_source_pre_reduce.glb` and `work/mm8_m404_sword_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce:
1. `REA_NODE=M404 REA_GLB=<rollback source> import_source.py`;
2. `dump_mesh.py`, `face_bones.py`, `small_pieces.py`;
3. `REA_TIP_R=0.008 REA_EXTRA_KEEP=work/keep_lock4.npy make_groups.py` (`keep_lock4` = drift / fleck locks from
   runs g7-g12; `work/keep_pick.npy`, `groups_pick.npy` are the final sets);
4. `REA_HEIGHT_M=1.90 REA_KEEP_FACES=work/keep.npy REA_GROUPS=work/groups.npy
   REA_GROUP_RATIOS=1:0.47,2:1.0,3:0.55,4:0.7,5:0.85 run_ladder.sh h2 0.82,0.81,0.80`;
5. `texture_drift.py r80`, `fleck_check.py r80`, `close_ladder.py`;
6. build as above.

Sword:
1. `prop_dump.py -- sword` and the component labels in `work/sword_comp.npy`;
2. `prop_parts.py sword c55_75 0:0.55,1:0.75`;
3. `PROP_NORMALS_ANGLE=20 prop_build.py -- sword:c55_75`;
4. `prop_swap_glb.py`.
