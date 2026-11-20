# MM6 Rat (`rat`, BRat A/B/C) reduction (installed 2026-10-14)

User: "now do Rat". RETOPOLOGY_PLAYBOOK.md default route, no-rebuild branch:
`../reduce_installed.sh rat Rat "MM6 Rat"` on the installed `assets_source/worlds/mm6/models/mm6_rat.glb`. No Meshy.
`scripts/close_views.py` takes the quadruped's `FrontPaw_R`/`HindPaw_R` and closer framing.

## Ladder

Limits scaled to the 1.0 m model (p99 3.0 mm, max 14.9 mm); the weld closes every seam (0 open edges).

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| r70 | 5,804 | 1.4 / 8.1 | 0.994 | 0.998 | pass |
| **r55** | **4,560** | 1.9 / 8.4 | 0.987 | 0.996 | pass, **picked (visual)** |
| r45 | 3,730 | 2.4 / 10.5 | 0.981 | 0.994 | pass, auto-pick |
| r40 | 3,316 | 2.7 / 9.6 | 0.979 | 0.992 | fail |
| r35 | 2,902 | 3.2 / 11.7 | 0.976 | 0.991 | fail |

`review/close/sheet4_{head,hand,whole}.png` (rows r100 / r55 / r45 / r35): from r45 the serrated back crest
flattens, the white collar studs facet and a sliver shows by the hind knee in the rear view; r55 keeps them.

## Result

`export/mm6_rat.glb`: LODs **4,560 / 2,280 / 818 / 256** (installed 8,292 / 4,146 / 1,491 / 482). Textures,
variants (carried to every LOD/shadow primitive), clips and sockets unchanged; no collapsed meshes. Viewer
`review/viewer/` (installed vs r55, A/B/C, all clips): `check_viewer.mjs` 48 loads, no errors.

## Installed

User accepted r55 (2026-10-14). Previous source backed up to `work/mm6_rat_source_pre_reduce.glb`; installed with
`tools/install_model.py` (runtime back-face pass: 17 back copies). No rat-specific regression case exists; the
`actor_model` regression cases were run after install.

## Floor fix — 2026-10-21

`--ground-loop Walking --raise Attack`. Before, in world units at tier A: walking sinks to -3.8; Attack sinks to -2.9; Walking sinks to -3.8.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_rat.glb`), written to `export/mm6_rat_floor.glb` and installed as `mm6_rat.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.

## Gait pass (2026-10-21)

`export/mm6_rat_gait.glb` is the floor-fixed `export/mm6_rat_floor.glb` with `Walk2` (trot) and `Run2` (half-bound)
grafted on; it is installed as `mm6_rat.glb`. The clips come from `../mm6_rat_claude/scripts/gait2_rat.py` (see
[its README](../mm6_rat_claude/README.md#gait-pass-walk2-trot-and-run2-half-bound-2026-10-21)).
- Meshes, LODs, variants and the old clips are unchanged.
- Binding: `walking: Walk2`, `run: Run2`, `stride_length: 0.30`, `run_stride_length: 0.51`.
- `check_winding.py`: 0 inverted.
- The viewer is now revision `gait-1`: tier A/B/C with the old and the new clips; the previous manifest is
  `review/viewer/manifest_reduce-1.json`.
- Recordings: `review/playback/` and `review/shots/`.

## Sprint (2026-10-31)

`export/mm6_rat_sprint.glb` is the installed source before this pass (`work/mm6_rat_source_pre_sprint.glb`: gait
export plus `lod_repair_claude` far LODs) with `Sprint` appended by `../claude_shared/graft_clips.py`. The clip comes
from `../mm6_rat_claude/scripts/sprint_rat.py` (see
[its README](../mm6_rat_claude/README.md#sprint-bounding-gallop-for-the-maw-chase-2026-10-31)). It is installed as
`mm6_rat.glb` with `tools/install_model.py export/mm6_rat_sprint.glb --world mm6 --name mm6_rat.glb`.
- Append only: all 550 original accessors, the 10 existing clips, meshes, LODs and variants are byte-identical.
- Binding (to apply for every BRat descriptor): `sprint: Sprint`, `sprint_stride_length: 0.8533`.
- `check_winding.py`: 0 inverted.
- Trap: `lod_repair_claude/scripts/repair.py` starts from its own `originals/`/`export/`, which have no Sprint. After
  rerunning it on the rat, graft Sprint again (and Walk2/Run2 if they are missing).

Gate: `gait_gate.py --world mm6 --model mm6_rat.glb --candidate export/mm6_rat_sprint.glb --set sprint=Sprint`
PASSED. Strides are trusted:

```
1. stride
  Walk2                measured 0.300 feet 0.299 trusted True  binding 0.300
  Run2                 measured 0.510 feet 0.498 trusted True  binding 0.510
  Sprint               measured 0.853 feet 0.826 trusted True  binding 0.853
2. window
  standard BRat A      wander: Walk2 x1.19  chase: Run2 x1.19
  standard BRat B      wander: Walk2 x1.06  chase: Run2 x1.06
  standard BRat C      wander: Walk2 x0.95  chase: Run2 x0.95
  maw      BRat A      wander: Run2 x1.01  chase: Sprint x1.14
  maw      BRat B      wander: Run2 x0.90  chase: Sprint x1.01
  maw      BRat C      wander: Walk2 x1.61  chase: Sprint x0.91
3. floor  BRat A/B/C ok
```

MAW wandering of BRat C (1.45) picks Walk2 at ×1.61. The gate does not hold MAW wandering, and the sprint does not
change it: it is a walk/run selection matter.

Review: viewer revision `sprint-1` (`scripts/viewer_sprint.py`: page from `mm6_fmp_reduce_claude`, tiers baked by
`viewer_variants.py`; the previous manifest is `review/viewer/manifest_gait-1.json`). `run_creature_review.py check`:
33 switches, no errors. Recordings are in `review/playback/` (`Sprint-1.webm`, `Sprint-0.5.webm`, `Run2-*.webm`).
Stills are in `review/shots/`: `sheet_run2_vs_sprint_left.png` (8 phases each, side), `sheet_sprint_quarter.png` and
`sheet_hip_run2_vs_sprint.png` (hip and knee close-ups).
