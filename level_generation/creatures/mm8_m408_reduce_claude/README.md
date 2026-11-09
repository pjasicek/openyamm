# MM8 Couatl (`m408`, Couatl A/B/C) reduction (2026-10-18)

User: "OK do those 5" (MM8 triangle-reduction batch, coordinated with sessions openyamm-b4 and openyamm-f9). Default
route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part needed rebuilding, so the
installed textures, palette variants (`KHR_materials_variants`) and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m408.glb`, byte-identical to
`../mm8_m408_claude/export/mm8_m408.glb`; the runtime copy has the same nine clips (not stale). It is copied to
`work/mm8_m408_source_pre_reduce.glb` (rollback source). One material, one `Couatl` node, 36 deformation bones.
Scripts are copied from `../mm8_m492_reduce_claude/scripts/` (split lip seam handling, exact source weights).

## Keep sets

- **Mouth seam** (`mouth_keep.py`, 2,023 faces with the small pieces): the m408 build split and capped the mouth
  (upper on Head, lower on Jaw); `import_source.py` reports 338 coincident vertices with other weights (168 Head/Jaw
  pairs, one wing pair). The oral cap is two-sided: 67 reversed face pairs on coincident vertices. Every face within
  1.2 cm of a seam vertex is kept exactly, which includes the whole cap.
- **Small pieces** (`REA_SMALL=95 small_pieces.py`, 1,052 faces in 14 pieces): eyes (90 / 94 faces), the two fangs
  and the ten smallest separate wing feathers.
- **Head** (`REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.8`): the rest of the Head/Jaw-weighted faces decimated gently on
  their own (1,009 faces at every step).

## Ladder

Weld 7,210 -> 825 open edges (unchanged by every step); one zero-area sliver and one duplicate drop on import
(12,952 -> 12,950). Limits for a 1 m model (standing height 1.0 m, rest length 1.47 m): p99 3 mm, max 15 mm.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| source | 12,952 | | | | |
| 70 % | 9,064 | 1.32 / 7.63 | 0.997 | 0.998 | pass |
| **55 %** | **7,122** | 2.43 / 11.21 | 0.991 | 0.997 | **pick** (lowest passing) |
| 45 % | 5,826 | 4.12 / 14.12 | 0.981 | 0.995 | fail (p99) |
| 40 % | 5,180 | 5.48 / 14.36 | 0.977 | 0.994 | fail |

Texture drift (`texture_drift.py`) at 55 %: one face over 40 (0.7 cm2), so no drift lock. Close-ups
(`review/close/sheet_a.png`, `sheet_b.png`: open mouth, fangs, eyes, head fins, feathers from both sides, tail fan,
belly) show no visible change at 55 %. Shading was judged on renders of the GLBs themselves
(`glb_close.py`, `review/glbclose/sheet_clay.png`, `sheet_tex.png`): the welded `source.blend` scrambles custom
normals, so its clay renders show false dark slits on the source head.

## Build

`export_cand.py` (Cand_55) -> `swap_lod0.py` -> `build_lods.py` (as `mm8_m408_claude`: 0.5 / 0.25 / 0.125,
4 influences) -> `shrink_shadow_lods.py` (copied from `mm8_m408_claude`, shadow LOD1-3 tucked inside the surface) ->
`carry_variants.py`: `export/mm8_m408.glb`, 7.9 MB (installed 8.8 MB), 9 clips, palette variants on all 7 LOD and
shadow primitives. `check_winding.py`: 0 inverted closed parts.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 12,952 | 6,473 | 3,236 | 1,614 |
| reduced | 7,122 | 3,560 | 1,779 | 886 |

`work/lod_check_{src,r55}.json`: every LOD keeps the source bounds (height 1.00 m, length 1.47 m; LOD3's left wing
tip is 1.3 cm shorter and the top 0.7 cm lower). The lowest point over every frame of every clip is -0.6 mm (LOD1),
against -2.3 mm for installed LOD3. No face stretches over 20x in any clip at any LOD. `review/lods/sheet.png` compares
all LODs at rest and during the attack gape.

Viewer: `review/viewer/` (installed A vs reduced A/B/C, tiers baked by `viewer_variants.py`);
`tools/run_creature_review.py --project level_generation/creatures/mm8_m408_reduce_claude check`: 36 switches, no
console errors.

## Attack v2

User review: "couatl - attack anim - check his original one, he like 'stands up' then he attacks then he goes back
down". The installed and reduced Attack were identical, so the clip itself was re-authored in `../mm8_m408_claude/`
(README, "Attack v2"): rear up on the lifted fore-body (head joint 0.53 -> 0.84 m), gape, strike forward and down
to the ground at the 0.9 s impact marker (mouth 4.6 cm above the ground), back in the held pose by 1.2 s. The reduced
export was rebuilt from the new full export with the same chain (`swap_lod0.py` -> `build_lods.py` ->
`shrink_shadow_lods.py` -> `carry_variants.py`): every mesh, skin, material and variant is byte-identical to the
reduction candidate above, only Attack changed (`work/attack_v1/` keeps the attack-v1 export). `lod_check.py`
(`work/lod_check_r55_attack2.json`): Attack lowest point -0.1 mm (LOD3), no stretched faces at any LOD; winding 0.
Sheet (native / new / installed, front and side, native frame times matched by phase to the clip: full rear at 0.6 s,
low point at the 0.9 s impact): `review/attack_v2/sheet_native_new_installed.png`. The viewer opens on Attack:
installed A (old Attack) vs reduced A/B/C (new Attack); `run_creature_review.py check`: 36 switches, no errors.

## Status

Installed 2026-10-18 after user review (reduction and Attack v2: "ok thats fine") with `tools/install_model.py --world mm8 export/mm8_m408.glb`.
`OPENYAMM_REGRESSION_FILTER=mm8_couatl_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_couatl_actor_models_keep_native_tiers_and_motion` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m408_source_pre_reduce.glb` with `tools/install_model.py --world mm8` (old Attack, unreduced).

