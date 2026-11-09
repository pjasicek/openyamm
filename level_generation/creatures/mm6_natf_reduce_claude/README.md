# MM6 female Cannibal (`natf`, PeasantF4 A/B/C: Cannibal / Head Hunter / Witch Doctor) reduction (2026-10-14)

User: "3D tris count reduction playbook - do natf". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the installed `mm6_natf.glb` (11,641 triangles, one body+head material, three variants with region ramps; project
`../mm6_natf_codex/`) and its attachments `mm6_natf_blade.glb` (1,142) and `mm6_natf_shield.glb` (1,636). Scripts
copied from `../mm6_fgt_reduce_claude/`. No Meshy credits. Height 1.639 m, limits p99 4.92 mm, max 24.59 mm.
**Installed 2026-10-14** (round 2-4 exports, user: "accepted"; the blade's back-edge lead in the backhand accepted as is).

## Body: per-region budgets

Parts (`work/comp.npy`, connected components of the welded mesh; `work/regions.npy`, dominant bone): the body and
head skin are one piece (6,215), legs 1,080, skirt 524, hair 514 (two pieces), eyes 325, collar 188, belt 282,
bracers, and about 110 small worn pieces of ~18 faces (necklace teeth, skirt and bracer fringe, anklets).
`scripts/natf_regions.py` writes the keep mask and groups.

| config | triangles | p99 / max mm | texture drift > 40 (p99) | finding |
|---|---:|---|---|---|
| source | 11,641 | | | |
| u: uniform r55 | 6,401 | 6.9 / 26.5 | | face changes: wider jaw, mouth |
| g1: face skin, eyes, pieces <= 80 faces kept; hands 45 %, hair 60 %, collar/belt/bracers 70 % | 8,147 / 7,681 | 5.7 / 34.3, 6.7 / 36.7 | 54 (32.7) / 52 (35.2) | face kept; drift on the bracers and skirt top |
| g2: g1 + one drift-lock round | 7,679 | 13.6 / 46.2 | | lock leaves too little for the shells: collapses |
| **g3: g1 + collar, belt, bracers kept exactly** | **8,147** (r70) | 5.7 / 36.7 | 17 (22.4) | **pick** |
| g3 r74 | 8,613 | 4.6 / 22.0 (auto pass) | 20 (21.0) | same look, 466 more |
| g4: g3 with hands 60 % | 8,147 | 6.5 / 35.9 | 27 (25.1) | no better; the drift is not on the hands |

Pick `g3r70` (`work/keep_g3.npy`, `work/groups_g3.npy`, ratios hands 0.45 / hair 0.6): 4,928 faces kept exactly, the
remaining body, leg and skirt shells about 55 %. It misses the automatic limits only inside and under the skirt
(`scripts/spot_render.py`, `review/spots/`: max error at Death 6 and Running 12 is the hidden inner skirt and thighs).
Open edges 1,331 as in the source (no new holes). Review: `review/close/final_{whole,head,hand}.png` (rows installed,
pick; front, three-quarter, side), `review/close/sheet1_*` (uniform r55 and g1), `sheet2_*` incl. `sheet2_back_head.png`.

LODs are rebuilt from the new LOD0 by `tools/build_actor_lods.py`: 8,147 / 4,051 / 1,384 / 406 (installed 11,641 /
4,699 / 3,077 / 2,707). The installed file carried separate LOD1-3 texture sets (the Codex accepted-look exception);
the rebuilt LODs use the LOD0 material and variants, so `scripts/prune_materials.py` drops the unused L1-L3 materials
and their 12 images (14.9 -> 8.2 MB). The region ramps and mask are unchanged.

## Blade and shield

`scripts/prop_parts.py` decimates chosen parts (connected components) on their own and keeps the rest exactly;
`prop_build.py` with `PROP_NORMALS_ANGLE=35` now uses a hybrid: kept parts take transferred normals, decimated parts
normals by angle. Transferred normals everywhere smeared dark wedges over the shield's back and the blade; angle
normals everywhere made the kept shield grip a flat box. `prop_swap_glb.py` measures the bounds against the longest
dimension (it used the glTF y extent, the shield's 96 mm thickness, and refused a 3 mm tip change).

- **Blade 1,142 -> 898** (`b3h`): blade 70 %, outer strap rings 75 %, inner strap pieces (against the forearm) and
  rivets kept; max 0.53 % of the length. At 45 % the bevel turned jagged. `review/props/blade_b3h_compare.png`.
- **Shield 1,636 -> 1,272** (`s2`): leaf plate 40 %; rims, grip bar and posts, boss, rib and studs kept exactly (the
  hand fit is unchanged). Reducing the rims made the edge wavy (`s1`, `p45h`). Plate error up to 9 mm at the front
  ridge near the tip, away from the arm. `review/props/shield_s1_s2_compare.png`.

Equipped LOD0 14,419 -> 10,317 (-28 %).

## Review and install

Viewer `review/viewer/` (body, installed vs pick per variant A/B/C; `check_viewer.mjs` 54 switches, no console
errors). Exports: `export/mm6_natf.glb` (pruned g3r70), `export/mm6_natf_blade.glb`, `export/mm6_natf_shield.glb`.
Other candidates are in `work/candidates/`.

After user review: `tools/install_model.py export/mm6_natf.glb --world mm6` and the same for the blade and shield, then
the `actors` regression (filter peasant). Rollback sources: `work/mm6_natf_source_pre_reduce.glb`,
`work/mm6_natf_blade_source_pre_reduce.glb`, `work/mm6_natf_shield_source_pre_reduce.glb`.

## Round 2 (2026-10-14): rebuilt on the new clips and skinned skirt

The gate run on round 1 showed the reduction itself broke the shield grip (hands at 45 %) and cloth containment.
Rerun on `../mm6_natf_anim_claude/export/mm6_natf_v2_unreduced.glb` (new Attack/Cast, skirt skinned to swing
helpers): config v3 = g3 plus the left (shield) hand kept exactly, 8 influences; pick r74 (r70 dropped to p99 7.7 mm
with the hand kept). **`export/mm6_natf_v3.glb`: 8,613 / 4,287 / 1,469 / 435.** Props: LOD2 dropped
(`scripts/drop_lod.py`; the kept LOD2 was above the gate's 0.28 ratio of the reduced LOD0):
`export/mm6_natf_blade_v3.glb`, `export/mm6_natf_shield_v3.glb`. Gates and viewer: `../mm6_natf_anim_claude/README.md`.
`export/mm6_natf.glb` (round 1) is superseded.
Round 3/4: rebuilt with the 2x Attack and its hip drive (same triangle counts).

## Floor fix — 2026-10-21

`--ground-death Death Dead`. Before, in world units at tier A: corpse at +3.3.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_natf.glb`), written to `export/mm6_natf_floor.glb` and installed as `mm6_natf.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.

## Gait rollout (2026-10-31, package h05)

New in-place locomotion clips appended to the installed `assets_source/worlds/mm6/models/mm6_natf.glb` (every existing
clip, mesh, skin and material unchanged): Walk2 (Mixamo Walk, 0.83 s, 1.80), Jog (Unarmed-Run-Forward, 0.66 s, 2.85), Sprint (Unarmed-Sprint, 0.56 s, 4.11); the swing-only thigh helpers that carry the skirt are recomputed from the new thighs. Bindings for PeasantF4 A-C (applied by the rollout coordinator from
`../gait_rollout_20261031/h05/bindings.yml`): walking Walk2, stride_length 1.8, run Jog, run_stride_length 2.85, sprint Sprint, sprint_stride_length 4.11. Details, gates and doubts:
[package h05](../gait_rollout_20261031/h05/README.md). Rebuild: `../gait_rollout_20261031/h05/scripts/rebuild.sh natf`
from the pre-gait copy `work/mm6_natf_pre_gait.glb` there. A far-LOD repair (`lod_repair_claude`) or head-bob rerun on
this model must re-graft these clips (copy the repaired source over that pre-gait copy and rerun the rebuild).
