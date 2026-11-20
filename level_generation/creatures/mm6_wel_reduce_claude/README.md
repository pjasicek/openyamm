# MM6 Water Elemental (`wel`, ElemWater A/B/C) reduction (installed 2026-10-14)

User: "ok do mm6_wel". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the installed
`assets_source/worlds/mm6/models/mm6_wel.glb` (`../mm6_wel_codex/`, water_v6). Scripts from `mm6_djn_reduce_claude/`
(piece-aware weights, `fix_uv_seams.py`). The `Body` node is reduced; the separate `Foam` node (480 tris, alpha mask)
is kept byte-for-byte. Same 2080x1024 atlas as the djinn: body set u < 0.5, head set u > 0.5 (6,912 faces, from
1.57 m up: face, beard, hair mass, crown).

## Ladder (limits scaled to the 1.98 m height: p99 5.9 mm, max 29.7 mm)

- Head protection by `B_Head`/`Hair` weights covers half the mesh (6,732 faces), so it would push the whole cut onto
  the torso and tail: not used. A uniform cut keeps the face (checked below).
- Every step from 62 % down failed on one 37.7 mm spot in the tail during Death frames 15+, where the Death clip has
  sunk the body below the floor (z -1.5 to -3.3 m, never visible). `reduce_ladder.py` takes `REA_FLOOR_Z=0`: vertices
  below the floor are left out of the error.

| step | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| source | 13,128 | | | | |
| 70 % | 9,188 | 2.9 / 22.5 | 0.997 | 0.997 | pass |
| 55 % | 7,220 | 4.4 / 21.7 | 0.994 | 0.994 | pass |
| **45 %** | **5,906** | 5.2 / 28.0 | 0.991 | 0.991 | **auto-pick** |
| 40 % | 5,250 | 6.2 / 28.0 | 0.989 | 0.989 | fail (p99) |

Open edges 348 as the source. `fix_uv_seams.py` (`UV_HEAD_Z=1.571`) re-mapped 5 body faces. Build
`scripts/build_cand.sh Cand_45 r45` (shadow LODs by `mm6_med_claude/scripts/shrink_shadow_lods.py`, as the wel
project): `export/mm6_wel.glb`, LODs 5,906 / 2,952 / 1,060 / 349 at first, now 5,906 / 2,952 / 1,476 / 764 (installed 13,128 / 6,564 / 2,361 / 784). No Meshy.

Review: `review/close/sheet_r45.png` (whole and head, installed / 45 %), `sheet_parts.png` (left bracer and hand,
right side fin, tail and fluke), `sheet_tiers.png` (B and C). Crown prongs slightly more faceted, nose slightly softer;
everything else matches. Viewer installed vs 45 % per tier, 54 loads pass.

## Installed (2026-10-14)

User: "good enough, install this". Previous source backed up to `work/mm6_wel_source_pre_reduce.glb` (rollback: install
that file with `tools/install_model.py --world mm6`); `export/mm6_wel.glb` installed with `tools/install_model.py`.
Regression `mm6_water_elemental_actor_tiers_trident_and_native_scale`: first FAIL (posed height 187.88, limit 188-201;
the original passes). The headless test measures the far LOD, and the default 6 % LOD3 (349 tris) had lost the crown
prongs (8 cm lower). `scripts/build_lods_ratios.py` builds the LODs at 50 / 25 / 13 %: LODs 2,952 / 1,476 / 764, every
LOD within 2 cm of the original height; reinstalled, the regression passes.
Dev assets only; `assets/worlds/mm6.zip` and Android not repacked.
