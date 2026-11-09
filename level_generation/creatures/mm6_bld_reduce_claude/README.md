# MM6 Bloodsucker (`bld`, Bloodsucker A/B/C) reduction (installed 2026-10-14)

User: "now do bloodsucker". RETOPOLOGY_PLAYBOOK.md default route, no-rebuild branch:
`../reduce_installed.sh bld Bld "MM6 Bloodsucker"` on the installed `assets_source/worlds/mm6/models/mm6_bld.glb`.
No Meshy. `scripts/close_views.py` uses `HindLeg_R` for the whole view and the `Fly` clip.

## Ladder

Limits for the 1.0 m model (p99 3.0 mm, max 14.9 mm); 195 open edges remain after the weld.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| r70 | 7,742 | 1.2 / 6.6 | 0.993 | 0.997 | pass |
| r55 | 6,084 | 1.7 / 8.2 | 0.986 | 0.996 | pass |
| **r45** | **4,976** | 2.2 / 8.2 | 0.981 | 0.995 | pass, **auto-pick, confirmed visually** |
| r40 | 4,424 | 2.5 / 9.4 | 0.976 | 0.995 | fail |
| r35 | 3,870 | 2.9 / 9.4 | 0.971 | 0.994 | fail; wing claws blobby |

`review/close/sheet4_{head,hand,whole}.png` (rows r100 / r55 / r45 / r35): neck spines, mouth tendrils, wing
fingers and claws match at r45.

## Result

`export/mm6_bld.glb`: LODs **4,976 / 2,482 / 853 / 246** (installed 11,062 / 5,531 / 1,985 / 617). Textures,
variants (carried to every LOD/shadow primitive), clips and sockets unchanged; no collapsed meshes. Viewer
`review/viewer/` (installed vs r45, A/B/C, all clips): `check_viewer.mjs` 36 loads, no errors.

## Installed

User accepted r45 (2026-10-14). Previous source backed up to `work/mm6_bld_source_pre_reduce.glb`; installed with
`tools/install_model.py`. Follow-up agreed the same day: maw disc fix and a separate head texture set (below).

## Floor fix — 2026-10-21

`--hover 0.193200 Death Dead`, then `--lift-joints Death Dead` with `--lift-only 'Tail*'` and `'Hand*,Finger*'` (tail top 30, wing hand 28 degrees at most as it falls). Before, in world units at tier A: living lowest at -30.9 (suggested hover 0.193200); dying sinks to -45.1.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_bld.glb`), written to `export/mm6_bld_floor.glb` and installed as `mm6_bld.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.
