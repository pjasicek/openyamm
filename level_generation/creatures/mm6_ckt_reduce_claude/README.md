# MM6 Cockatrice (`ckt`, Cockatrice A/B/C) reduction (2026-10-14)

User: "do cockatrice next". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the
installed `assets_source/worlds/mm6/models/mm6_ckt.glb` (8,672 tris: body 6,174, head set 2,498; double-sided
materials, three variants, four influences at full detail; from `../mm6_ckt_claude/`). Started with
`REA_PROTECT_HEAD=1 ../reduce_installed.sh ckt Cockatrice "MM6 Cockatrice"`; limits for the 1.008 m size (wingspan):
p99 3.02 mm, max 15.12 mm. No Meshy credits.

## Cockatrice-specific changes
- **Small pieces kept.** The neck ruff and back are ~120 separate small pieces (scale plates and spikes, 1,222 faces
  in pieces under 200 faces, including the two wing leading-edge bones). The plain r70 auto-pick flattened the ruff
  plates into shards (clay renders). `work/keep_c.npy` keeps them, the head (`Head` weights, 2,061 faces) and the one
  two-sided pair exactly (3,283 faces); the same 70 % step then has a lower error (p99 1.95 vs 2.14 mm).
- **No drift lock.** The fine feather texture gives many small drifted faces (median source face 0.32 cm2). A lock
  round at 1 cm2 / 1.5 cm kept 4,288 faces and wrecked the rest (r70 p99 6.3 mm), so it was dropped;
  `drift_lock.py` takes `REA_LOCK_AREA` for smaller creatures. The pick's drift (70 cm2) is not visible in the renders.
- `face_views.py`: `REA_VIEW_SCALE` scales the camera distances (0.4 here), the facing is head ahead of chest when
  there are no toes or gaze socket, and the chest/hand bones accept bird names.
- One two-sided pair (`find_doubles.py`) restored on export, as for the harpy (the materials are double-sided anyway).

## Ladder

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 8,672 | | | |
| head kept | 70 % | 6,069 | 2.1 / 6.4 | 0.985 | auto pass; ruff plates flattened |
| head kept | 60 % | 5,201 | 2.9 / 7.3 | 0.975 | |
| head + drift lock | 70 % | 6,069 | 6.3 / 21.0 | 0.945 | lock too large |
| **head + small pieces kept** | **70 %** | **6,069 (+1 copy)** | 2.0 / 6.3 | 0.982 | **pick** (auto pass) |
| head + small pieces kept | 65 % | 5,635 | 2.5 / 7.3 | 0.976 | IoU fail |

## Result
`export/mm6_ckt.glb` (= `mm6_ckt_cr70.glb`): LODs 6,070 / 2,941 / 989 / 277 (installed 8,672 / 4,269 / 1,456 /
416); body 3,608, head 2,462; variants carried to all 7 LOD/shadow primitives; socket and clips unchanged.
Review: `review/sheet_a.png` (+ `_clay`; installed, head-kept r70, r60), `review/sheet_c.png` (installed, head-kept r70,
pick), `review/sheet_clips.png` (installed vs pick in Attack, Death and Walking). Viewer `review/viewer/` (installed /
pick per variant, every clip; `check_viewer.mjs` 48 switches, no console errors).

## Installed (2026-10-14)

User: "accepted". Previous source backed up to `work/mm6_ckt_source_pre_reduce.glb` (rollback: install that file),
`tools/install_model.py export/mm6_ckt.glb --world mm6`. Lease released.

## Cast wind-up retimed (2026-10-15)

Timing review pick: Cast's first 0.4 s at 1.5x, easing back over 0.1 s (`../timing_review/retime_clip.py`, which now
copies key times Cast shared with Attack and Walking so only Cast changes). Cast 0.75 -> 0.631 s; impact 0.494 -> 0.375.
Unretimed export: `export/mm6_ckt_unretimed.glb` (rollback: install it and restore the cast impact).

## Gait rollout: Run2 and Sprint (2026-10-31)

[Gait rollout package q1](../gait_rollout_20261031/q1/README.md) added `Run2` and `Sprint`. Before, the Cockatrice
chased on Walking at ×1.67-1.95, and under MAW it was held at 2× with sliding feet.

The script `../gait_rollout_20261031/q1/scripts/gait_ckt.py` executes `../mm6_ckt_claude/scripts/anim_ckt.py` up to
its clip table, so it uses the same leg IK, wings, head, tail and floor helpers.

| clip | length | stride | authored speed | duty | gait |
|---|---|---|---|---|---|
| Run2 | 0.5833 s | 0.665 | 1.14 | 0.45 | bird run |
| Sprint | 0.5 s | 0.945 | 1.89 | 0.32 | wing-assisted bounding sprint |

- Both keep Walking's 0.30 m stance sweep. Left foot down at 0.
- Keys at 48 fps.

The clips were grafted onto the installed source; the existing clips are byte-identical. Binding: `run: Run2`,
`run_stride_length: 0.665`, `sprint: Sprint`, `sprint_stride_length: 0.945`. The gate passed:
- Standard chase ×0.98-1.15
- MAW chase ×1.04-1.09

```sh
cd ../gait_rollout_20261031/q1
blender -b --factory-startup ../../mm6_ckt_claude/work/anim_v1.blend -P scripts/gait_ckt.py -- work/ckt_clips.glb
python3 ../../claude_shared/graft_clips.py work/rollback/mm6_ckt.glb work/ckt_clips.glb export/mm6_ckt.glb \
  --clip Run2 --clip Sprint
```

A far-LOD repair rerun (`lod_repair_claude`) must re-graft these clips. `anim_ckt.py`'s `STRIDE` (0.30) is the stance
sweep; the walking stride is 0.503.
