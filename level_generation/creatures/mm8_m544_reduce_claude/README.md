# MM8 Unicorn (`m544`, Unicorn A/B/C: Foal, Unicorn, Herd Leader) reduction (2026-10-18)

User: "pick 5 more to do" after the first MM8 batch. Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
including its MM8 batch lessons; scripts copied from [`mm8_m492_reduce_claude/`](../mm8_m492_reduce_claude/README.md)
(parent-transform fix, coincident-vertex handling, `lod_check.py`, `glb_close.py`). No retexture, no Meshy credits.
Not installed.

Source: the installed `assets_source/worlds/mm8/models/mm8_m544.glb`, identical to `mm8_m544_claude/export/`
(md5 `916cfbda…`), copied to `work/mm8_m544_source_pre_reduce.glb` (rollback source). Mesh node `Unicorn`, one
material `Unicorn_UNICORN` (shared 2K coat, region mask, one `unicorn` variant; the three tiers share colours and
differ only in scale), a separate 4-triangle `BreathCloud` mesh (kept), 9 clips, 4 influences.

## Source facts

- The production already ran its own Blender reduction before UVs (`mm8_m544_claude/scripts/reduce_uv.py`), so the
  body is lean: 11,513 triangles, a third of them head-weighted (the face was protected there).
- Weld 6,643 -> 2,163 open edges: 43 real boundary loops (mane and tail sheets, the largest 483 and 380 edges), not
  seams; every step keeps them (`preserveboundary`). One degenerate face drops on import (11,513 -> 11,512); no
  two-sided sheet pairs (the material is double-sided).
- Only 3 coincident vertex pairs; no split mouth seam. No face stretches in Attack at any step.
- Pieces: body 7,695 faces, mane 980, tail 794, horn 243, ears ~170 each, 32 small mane/tail locks.
- Normals: rendered straight from the GLBs (`scripts/glb_close.py`), the installed model shades smooth, so the
  reduction keeps plain smooth normals (no transfer from the welded `source.blend`).

## Ladder (uniform, limits scaled to the 1.04 m body length: p99 3.12 mm, max 15.6 mm)

| step | triangles | p99 / max mm | IoU (front) | SSIM | |
|---|---:|---|---|---|---|
| source | 11,513 | | | | |
| 70 % | 8,058 | 1.36 / 10.81 | 0.992 | 0.999 | pass |
| **60 %** | **6,906** | 2.00 / 11.21 | 0.987 | 0.997 | **auto-pick** |
| 50 % | 5,756 | 2.98 / 13.98 | 0.977 | 0.994 | fail (IoU) |
| 40 % | 4,604 | 4.71 / 14.72 | 0.961 | 0.988 | fail |

Close-ups (`review/close/sheet_uni_{a,b}.png`, geometry only; shading there is from the welded `source.blend`):
horn spiral, ears, eyes, muzzle and the Attack head pose hold to 50 %; at 50 % the mane loses some lock tips. The
horn is clean, so it was kept, not rebuilt. GLB close-ups of 60 % against the installed model match for head, mane,
tail, legs and hooves, body, belly, chest, rump and the Dead pose (`review/glbclose/sheet_head.png`,
`sheet_body.png`, `sheet_body2.png`).

## Build

`export_cand.py` (Cand_60) -> `swap_lod0.py` (node `Unicorn`) -> `floor_contacts.py` (vertices within 6 mm of the
floor in any frame of any clip: hoof soles and the Death/Dead body, 79 points; plus the rest-pose bounding extremes
within 1 cm, `work/extremes.json`) -> `build_lods.py` (the creature's own 0.5 / 0.25 / 0.125, 4 influences, those
points protected) -> `mm8_m544_claude/scripts/shrink_shadow_lods.py` (the creature's own shadow inset) ->
`carry_variants.py`. Export `export/mm8_m544.glb`, 7.4 MB (installed 8.2 MB); `check_winding.py`: 0 inverted.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 11,513 | 5,752 | 2,872 | 1,432 |
| reduced | 6,906 | 3,447 | 1,719 | 856 |

`scripts/lod_check.py` (`REA_NODE=Unicorn`): every LOD has exactly the LOD0 bounds (the first build without the
extreme lock lost 7 mm of horn and grew 6 mm wide at LOD3), the lowest point over every frame of every clip is
-0.2 mm at all four LODs (installed: -0.0 / -0.4 / -0.6 / -0.9 mm, Death), and no face stretches. Distance sheet:
`review/lods/sheet.png`.

## Retexture check

One texture set (2K coat with denser head islands; 1K normal, material and region maps); the reduced export carries
the installed images byte-for-byte and keeps the source UVs.
- Drift (`texture_drift.py`, median per face): 3 faces over 40 (3.9 cm²), p99 19.
- Dark slivers (`dark_slivers.py` from the Cyclops): 31 faces with 2-16 of 48 samples darker than the source, ten of
  them over 1 cm². Close-ups at every one of those spots (`review/spots/sheet_r60.png`, installed / reduced pairs)
  show no slash or gutter colour: the dapple pattern trips the sample test. A drift-lock round only moved the flags
  elsewhere, so it was discarded.
- Head vs body: one shared coat; head and neck read the same grey in every view. Existing texture: no Meshy gaps or
  wrong-colour patches found in the close-ups (the production already filled its one missing tail-tip chart).

Verdict: no retexture and no local fix needed.

## Viewer

`review/viewer/` (installed vs reduced 60 %; the three tiers share this look and differ only in scale, which the
native game captures of the production project cover). `tools/run_creature_review.py --project
level_generation/creatures/mm8_m544_reduce_claude check`: 18 clip switches, no console errors.

## Status

Not installed; awaiting user review. To install:

```sh
python3 tools/install_model.py level_generation/creatures/mm8_m544_reduce_claude/export/mm8_m544.glb --world mm8
OPENYAMM_REGRESSION_FILTER=mm8_unicorn ./build/game/openyamm --headless-run-regression-suite actors
```

The regression case is `mm8_unicorn_actor_models_keep_native_tiers_gallop_and_horn`. Then add the row to
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m544_source_pre_reduce.glb` the same way.

Reproduce: `import_source.py` (REA_NODE=Unicorn, REA_GLB=the rollback source) -> `dump_mesh.py` -> `small_pieces.py`
-> `REA_HEIGHT_M=1.04 run_ladder.sh uni 0.70,0.60,0.50,0.40` -> `close_ladder.py` / `close_sheet.py` (Unicorn spots)
-> build as above -> `lod_check.py`, `lod_views.py` (`LOD_CZ=.33 LOD_SCALE=1.25`), `glb_close.py`, `glb_sheet.py`,
`texture_drift.py`, `dark_slivers.py`, `spot_views.py`.


## Installed (2026-10-18)

User accepted the viewer ("ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py export/mm8_m544.glb --world mm8`; regression `mm8_unicorn_actor_models_keep_native_tiers_gallop_and_horn` passes. Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m544_source_pre_reduce.glb` the same way.

## Floor fix — 2026-10-21

`--ground-loop Walking`: the walk lifted every hoof up to 0.027 m off the floor at 11 of 49 keys; it now keeps a hoof down. Running keeps its gallop suspension. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m544.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.

## Gait rollout (2026-10-31, package q4)

**Walk2** (four-beat lateral-sequence walk, hind L at 0 as the gallops; 0.3981 m in 0.8125 s, authored 0.49) grafted onto the installed model by `../gait_rollout_20261031/q4/scripts/gait_m544.py` (the leg machinery of `../mm8_m544_claude/scripts/animate_unicorn.py`). Binding: `walking: Walk2`, `stride_length: 0.3981` for Unicorn A-C (Unicorn C wandered on the gallop Walking at x0.72); the chase stays on Running. Gate window: wander x0.94-1.04, chase Running x1.08-1.19. Head bob 3.1 %, hoof toe-out 0 as every clip.

Rebuild: `../gait_rollout_20261031/q4/README.md` (Rebuild). A far-LOD repair rerun (`lod_repair_claude`) or any rebuild of the installed GLB must re-graft these clips from `../gait_rollout_20261031/q4/work/m544_clips.glb` with `../claude_shared/graft_clips.py`. Rollback source: `../gait_rollout_20261031/q4/work/rollback/mm8_m544.glb`.
