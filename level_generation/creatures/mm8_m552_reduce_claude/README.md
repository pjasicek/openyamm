# MM8 Thunderbird (`m552`, Mist Hawk / Storm Eagle / Thunderbird) reduction (2026-10-18)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) (including its MM8 batch lessons), no-retexture
variant, with the scripts of [mm8_m572_reduce_claude](../mm8_m572_reduce_claude/README.md) (Phoenix: floor-contact
LOD lock, stretch check, tier viewer) and the parent-transform-fixed `reduce_ladder.py` of
[mm8_m492_reduce_claude](../mm8_m492_reduce_claude/README.md). No Meshy credits.

Source: installed `assets_source/worlds/mm8/models/mm8_m552.glb` (identical to `mm8_m552_claude/export/`), copied to
`work/mm8_m552_source_pre_reduce.glb` (rollback source). One double-sided material (`Thunderbird_A`, variants B/C),
mesh node `Thunderbird`, 4 influences, no effect meshes.

## Ladder

Weld 12,814 -> 237 open edges, no coincident vertices with other weights (the beak is not split), one duplicate face
merges on import (11,448 -> 11,447; the material is double-sided, so no reversed copies are needed). The mesh is a
3,155-face body, two wings of about 2,270 faces and 41 separate pieces of up to 92 faces (primaries, secondaries,
tail feathers, talons, eyes; 3,750 faces). Limits scaled to the 0.69 m wing span (p99 2.07 mm, max 10.35 mm).

| step (uniform) | triangles | p99 / max mm | IoU (front) | SSIM | |
|---|---:|---|---|---|---|
| source | 11,448 | | | | |
| 70 % | 8,011 | 1.30 / 9.33 | 0.985 | 0.994 | pass |
| **60 %** | **6,867** | 1.70 / 9.33 | 0.981 | 0.993 | **auto-pick** |
| 50 % | 5,723 | 2.14 / 15.66 | 0.976 | 0.991 | fail (max, IoU) |
| 40 % | 4,577 | 2.73 / 15.66 | 0.968 | 0.990 | fail |

The max error sits at the thighs and belly in the Attack talon strike (`probe_max.py`); 50 % adds a 15.7 mm miss
there. No face stretches in any clip at any step (`stretch_check.py`). Close-ups (`review/close/sheet_uni_a.png`,
`sheet_uni_b.png`; source / 70 / 60 / 50): beak, eyes, head, talons in the strike, belly, tail fan, both wing
surfaces, back and corpse match at 60 %. Texture drift at 60 %: 1 face over 40 (0.0 cm2); no drift lock.

## Build

`export_cand.py` (Cand_60) -> `swap_lod0.py` -> `floor_contacts.py` (Death/Dead, 39 points) -> `build_lods.py`
(0.5 / 0.25 / 0.125, 4 influences, as the m552 project, contacts protected) -> the m552 project's
`shrink_shadow_lods.py` (0.3-0.7 mm inward margin, capped at 1 mm) -> `carry_variants.py`: `export/mm8_m552.glb`,
8.3 MB (installed 9.4 MB), 6 clips, 3 variants on all 8 colour/shadow meshes, region ramps unchanged.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 11,448 | 5,723 | 2,860 | 1,419 |
| reduced | 6,867 | 3,432 | 1,704 | 822 |

`work/lod_check_{src,r60}.json`: every LOD keeps the source bounds (the LOD2/3 tail tip is 5 mm shorter); Death and
Dead stay 0.9 mm above the floor at every LOD (the installed LOD3 dipped 0.4 mm under it in Death). Flight clips go
below the actor origin by design, as the source. No face stretches. `check_winding.py`: 0 inverted closed parts.

## Retexture check

Verdict: **no retexture needed**; no local fix needed. No credits.

- One texture set: shared 2K base colour, 1K normal, metal-rough and region mask (brown body and olive feather
  regions), images byte-identical in the reduced export, so the UVs stay valid. No separate head set.
- Normals: the installed GLB shades smooth; clay renders of the installed and reduced GLBs (direct imports, never the
  welded `source.blend`) match (`review/retexture/sheet_head.png`, `sheet_body.png`, clay columns).
- Per tier (`review/retexture/sheet_head.png`, `sheet_body.png`): head, beak, eyes, neck, flanks, belly, both wing
  surfaces, talons and tail match the installed model in all three tiers. The head takes the body's brown, as the
  native sprites do.
- Dark slivers (`scripts/dark_slivers.py`: the 25th-percentile luminance of 24 samples per face against that of
  same-facing source samples, so banded feathers compare like with like): 53 flagged faces at 60 %, 48 at 70 %, a
  noise floor of faces hidden between stacked feathers. The three worst spots render identically in the source and
  the reduction from above and below (`review/retexture/sheet_dark_spots.png`).
- Tiers: the three ramps differ only at the dark end of the olive ramp, so Mist Hawk, Storm Eagle and Thunderbird
  look alike, as the native palettes 553-555 do. Both native and model tiers are shown in the m552 project's
  `review/ingame/` captures. The model reads lighter and greener than the native sprites (tan body, lime feathers
  against dark brown and dark olive); that is the m552 production's colour direction, unchanged here.

## Viewer

`review/viewer/`: three tiers, installed vs 60 % (region ramps baked per tier by `viewer_variants.py`).
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m552_reduce_claude check`: 36 clip
switches, no console errors.

## Status

Not installed. Install: `python3 tools/install_model.py
level_generation/creatures/mm8_m552_reduce_claude/export/mm8_m552.glb --world mm8`; regression:
`OPENYAMM_REGRESSION_FILTER=mm8_thunderbird_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_thunderbird_actor_models_keep_native_tiers_and_motion`). Rollback: install
`work/mm8_m552_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_NODE=Thunderbird, REA_GLB=rollback source) -> `dump_mesh.py` ->
`small_pieces.py` -> `run_ladder.sh uni 0.70,0.60,0.50,0.40` -> `stretch_check.py`, `probe_max.py`,
`close_ladder.py`, `close_sheet.py`, `texture_drift.py r60` -> build as above (REA_NODE=Thunderbird for
`export_cand.py`, `floor_contacts.py`, `lod_check.py`) -> `viewer_variants.py`, `retex_views.py`, `retex_sheet.py`,
`dark_slivers.py`, `spot_views.py`.


## Installed (2026-10-18)

User accepted the viewer ("ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py export/mm8_m552.glb --world mm8`; regression `mm8_thunderbird_actor_models_keep_native_tiers_and_motion` passes. Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m552_source_pre_reduce.glb` the same way.

## Floor fix — 2026-10-21

`--hover 0.266206 Death Dead`: the Fly loop's wing strokes cut 0.266 m (151 world units) under the floor of an actor at floor height. Every living clip is raised so the lowest stroke meets the floor; Death eases it out. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m552.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.
