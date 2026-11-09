# MM6 Minotaur (`min1`) reduction on Codex round 3, closed hips (installed 2026-10-15)

User: "minotaur - do the reduce on the newest codex export". The first reduction (`../mm6_min1_reduce_claude/`) was
built on Codex round 2 (`../mm6_min1_codex/review/round3/before/`), because `assets_source` never received round 3
(closed hips: 7,995 / 1,743 / 1,660 / 781, open edges 504 -> 441). Same recipe as that project, scripts copied from
it (`build_keep.sh` / `build_pick.sh` now read `../mm6_min1_codex/export/mm6_min1.glb`):

- Masks rebuilt from bone weights with `dump_mesh.py`: `REA_PROTECT=_Hand,Finger` -> `work/hands.npy` (1,521, kept
  exactly), `REA_PROTECT=B_Head` -> `work/head.npy` (2,454, reduced at 70 %). On the round-2 mesh this reproduces
  the first project's masks exactly.
- `REA_KEEP_FACES=work/hands.npy REA_PROTECT_FACES=work/head.npy REA_PROTECT_RATIO=0.7 scripts/run_ladder.sh h70
  0.85,0.80,0.75` (limits p99 5.55, max 27.75 mm for 1.85 m):

| step | tris | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| r85 | 6,793 | 2.71 / 21.95 | 0.998 | 0.997 | pass |
| **r80** | **6,393** | 3.66 / 24.07 | 0.996 | 0.996 | **pick** |
| r75 | 5,993 | 4.92 / 32.0 (Dead) | 0.992 | 0.994 | fail |

- `build_keep.sh r80 h70`: LOD0 and its shadow swapped, round-3 LOD1-3 kept (closed hips). Open edges 441 as in the
  source (no new loops), 0 flipped faces, texture drift > 40 on 2 faces (3.1 cm2).
- Then the accepted runtime edits of the first project: `retime_glb.py` Attack and Death 2x (0.979 / 1.2 s) and
  `copy_clip.py` Cast = Attack. Against the previous install only the meshes differ (clips, textures, materials and
  variants byte-identical), so `actors.yml` is unchanged. Axe: the installed reduced axe stays (round 3 did not touch it).

Result `export/mm6_min1.glb`: LODs 6,393 / 1,743 / 1,660 / 781. Pre-retime step `export/mm6_min1_h70r80.glb`.
Render `review/close/sheet_whole_old_vs_r3.png` (top: previous install, bottom: this). Previous source:
`../mm6_min1_reduce_claude/export/mm6_min1.glb` (rollback: install it). Minotaur, Jackalman and actor-model unit tests pass.

## Gait rollout — 2026-10-31

The [gait rollout package h02](../gait_rollout_20261031/h02/README.md) appended Run2 (0.70 s, stride 3.0383) and Sprint (0.58 s, 3.7452); Walking unchanged to the installed
`assets_source/worlds/mm6/models/mm6_min1.glb` (existing clips, meshes, skins and materials byte-identical; installed
with `tools/install_model.py`). Bindings for BMinotaur A/B/C, applied by the rollout coordinator from
`../gait_rollout_20261031/h02/bindings.yml`: run: Run2, sprint: Sprint (Standard chase played Running at x1.7-1.9, MAW at x2.6-3.2). Both arms are raised as one unit so the two-handed axe grip is unchanged. Every tier passes `gait_gate.py` under Standard and MAW.
Rebuild: `../gait_rollout_20261031/h02/scripts/rebuild.sh min1` (from the pre-gait source kept in
`../gait_rollout_20261031/h02/work/`). Any later re-export of this model, including a far-LOD repair rerun
(`../lod_repair_claude/`) or a floor fix, starts from a source without these clips unless it starts from the installed
one: re-graft them (rerun the rebuild on the new source) and keep the bindings.
