# MM6 Spider (`spi1`, BSpider A/B/C) reduction (installed 2026-10-14)

User: "do the spider now". RETOPOLOGY_PLAYBOOK.md default route, no-rebuild branch:
`../reduce_installed.sh spi1 Spider "MM6 Spider"` on the installed `assets_source/worlds/mm6/models/mm6_spi1.glb`.
No Meshy. `scripts/close_views.py` centres on `Fang_R` and the leg tips `Tarsus_R1`/`Tarsus_R4` (no head bone).

## Ladder

Limits for the 1.0 m model (p99 3.0 mm, max 15 mm); 550 open edges remain after the weld (separate pieces).

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| r70 | 6,694 | 1.7 / 11.6 | 0.992 | 0.998 | pass |
| **r55** | **5,260** | 2.5 / 12.7 | 0.985 | 0.995 | pass, **auto-pick, confirmed visually** |
| r45 | 4,302 | 3.4 / 13.1 | 0.978 | 0.992 | fail |
| r40 | 3,824 | 3.9 / 13.1 | 0.975 | 0.989 | fail |

`review/close/sheet4_{head,hand,whole}.png` (rows r100 / r70 / r55 / r45): fangs, palps and leg segments match at
r55; r45 makes the leg joints angular.

## Result

`export/mm6_spi1.glb`: LODs **5,260 / 2,629 / 945 / 314** (installed 9,564 / 4,781 / 1,721 / 572). Textures,
variants (carried to every LOD/shadow primitive), clips and sockets unchanged; no collapsed meshes. Viewer
`review/viewer/` (installed vs r55, A/B/C, all clips): `check_viewer.mjs` 48 loads, no errors.

## Installed

User accepted r55 (2026-10-14). Previous source backed up to `work/mm6_spi1_source_pre_reduce.glb`; installed with
`tools/install_model.py` (runtime back-face pass: 385 back copies). No spider-specific regression case exists; the
`actor_model` regression cases were run after install: 53 pass; the 3 failures (guard, mage, ooze) predate this change.

## Gait pass (2026-10-21)

`export/mm6_spi1_gait.glb` is `export/mm6_spi1.glb` with `Walk2` and `Run2` grafted on; it is installed as
`mm6_spi1.glb`. The clips come from `../mm6_spi1_claude/scripts/gait2_spi1.py` (see
[its README](../mm6_spi1_claude/README.md#gait-pass-walk2-and-run2-2026-10-21)).
- Meshes, LODs, variants and the old clips are byte-for-byte the same as before.
- Binding: `walking: Walk2`, `run: Run2`, `stride_length: 0.4845`, `run_stride_length: 0.6998`.
- `check_winding.py`: 0 inverted.
- The viewer is now revision `gait-1`: tier A/B/C with the old and the new clips. The previous manifest is
  `review/viewer/manifest_reduce-1.json`.
- Recordings: `review/playback/` (every clip at ×1 and ×0.5, webm plus frames) and `review/shots/` (front and quarter
  views of Walk2/Run2).
