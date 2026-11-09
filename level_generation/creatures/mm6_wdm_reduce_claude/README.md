# MM6 Flying Demon (`wdm`) reduction (2026-10-13)

User: "move on to the flying mm6 demon - the tris optimalization routine". Same no-retexture route as
`../mm6_demon_reduce_claude/` (scripts copied, model/node now parameters: `REA_GLB`, `REA_NODE=Demon`).
Source: installed `assets_source/worlds/mm6/models/mm6_wdm.glb` (DemonFly A/B/C), 1.69 m, two texture sets
(body+wings, grafted HD head). Weld: 18,754 open edges -> 135. Limits scaled by `REA_HEIGHT_M=1.69`.

| step | total | body | head | p99 / max mm | IoU min | SSIM | |
|---|---:|---:|---:|---|---|---|---|
| source | 16,086 | 9,845 | 6,241 | | | | |
| 70 % | 11,260 | 6,691 | 4,569 | 3.0 / 15.3 | 0.990 | 0.994 | pass |
| **55 %** | **8,846** | 5,285 | 3,561 | 4.3 / 16.8 | 0.983 | 0.993 | **auto-pick** |
| 45 % | 7,238 | 4,379 | 2,859 | 5.4 / 23.0 | 0.976 | 0.991 | fail |
| 35 % | 5,630 | 3,487 | 2,143 | 7.1 / 21.1 | 0.966 | 0.988 | fail |
| 25 % | 4,020 | 2,585 | 1,435 | 9.3 / 27.9 | 0.946 | 0.982 | fail |

Build: `export_cand.py` -> `swap_lod0.py ... Demon` -> `tools/build_actor_lods.py --mesh-node Demon` ->
`carry_variants.py` (10 primitives): `export/mm6_wdm.glb`, LODs 8,846 / 4,421 / 1,589 / 530 (installed 16,086 /
8,040 / 2,895 / 962). Ladder 36 s, build 6 s. Viewer `review/viewer/` (36 loads pass `check_viewer.mjs`),
close renders `review/close/sheet_*.png`. Not installed yet.

## Installed with the burn death (2026-10-13)

User: "looks good, doesnt even need the retexture ... same death anim or similar anim as the demon ... effects based
on the color". The old Death shrank the hips to 0.005 from 0.42 s (disintegration). `scripts/hold_death.py
export/mm6_wdm.glb export/mm6_wdm_death.glb 0.416667 --drop-scale mixamorig:Hips`: Death keeps its first 0.417 s
(arms and wings flung out, the widest hand span before the shrink) and holds it to 1 s; Dead holds the same pose;
the hips scale channel is gone (`review/death/sheet_new.png`). Burn maps (`claude_shared/bake_burn_maps.py`: wing rims
open, hands, toes, head, wing tips) -> `scripts/embed_burn.py` (base + variant materials) -> `export/mm6_wdm_burn.glb`,
installed as `mm6_wdm.glb`. Bindings: DemonFly A violet, B yellow-gold, C crimson; burn 0-0.75 s as the ground demon.
Previous source: `../mm6_wdm_claude/review/pre_reduce/mm6_wdm_source_pre_reduce.glb`.

## Floor fix — 2026-10-21

`--hover 0.041315 Death Dead` (flier rule). Before, in world units at tier A: living lowest at -5.4 (suggested hover 0.041315).
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_wdm.glb`), written to `export/mm6_wdm_floor.glb` and installed as `mm6_wdm.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.
