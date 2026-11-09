# MM8 Bone Dragon (`m616`, Skeletal Dragon / Bone Dragon / Undead Dragon) reduction (2026-10-19)

User: "OK go ahead" (MM8 triangle-reduction batch of openyamm-f6: m536, m616, m568, m628, m412; claims coordinated
with openyamm-b4, -4f and -f9). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture
variant: no part needed rebuilding, so the installed textures, the three material variants and the (zero-coverage)
region mask stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m616.glb`, byte-identical to
`../mm8_m616_claude/export/mm8_m616.glb` (the `assets_dev` runtime copy is its cook from the same time), copied to
`work/mm8_m616_source_pre_reduce.glb` (rollback source). One material per tier, one `BoneDragon` node, 44 bones,
4 influences, six clips (Attack, Cast, Dead, Death, Fly, Hit). The materials are double-sided, so the wing membranes
are single sheets (no reversed face pairs; the weld keeps all 12,635 triangles). Scripts are copied from
`../mm8_m624_reduce_claude/scripts/` (fixed parent order in `reduce_ladder.py`, exact source weights).

## Keep sets

- Weld 17,179 -> 395 open edges (unchanged by every step); 49 coincident vertices with other weights (wing-finger tips,
  ribs, tail tip; no split mouth). `seam_keep.py` keeps every face within 1 cm of one (413 faces).
- Small pieces kept exactly (`REA_SMALL=90 small_pieces.py`, 1,317 faces in 79 pieces): the separate vertebrae along
  neck, back and tail, the teeth, the two 79/85-face wing claws and other loose bones. Total kept: 1,730 faces.
- Head (Head/Jaw weights, 1,217 faces) decimated on its own at 80 % (`REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.8`):
  horns, eye sockets and the teeth rows stay as installed.

## Ladder

Limits for the 0.84 m flying height (Fly pose, same as the README's 256 game units at tier A): p99 2.52 mm,
max 12.6 mm.

| config | step | triangles | p99 / max mm | IoU min | |
|---|---|---:|---|---|---|
| source | | 12,635 | | | |
| uniform + keeps, head 80 % | 75 % | 9,475 | 1.87 / 5.93 | 0.978 | |
| **uniform + keeps, head 80 %** | **70 %** | **8,843** | 2.21 / 5.93 | 0.971 | **pick** |
| uniform + keeps, head 80 % | 65 % | 8,211 | 2.66 / 7.84 | 0.967 | fail (p99) |
| uniform + keeps, head 80 % | 60 % | 7,581 | 3.12 / 13.01 | 0.957 | fail (p99, max at wing finger 3) |
| wings 75 %, feet 70 % groups | 60 % | 7,579 | 4.20 / 19.51 | 0.957 | fail: the ribs and spine absorb the cut |
| wings 55 % group | 65 % | 8,211 | 2.61 / 13.01 | 0.964 | fail |

The silhouette IoU fails at every step, as on the MM6 Skeleton: in the side views (0.97 at 70 %) the thin ribs,
claws and wing-finger tips move by a pixel. The silhouette-difference images show only single-pixel rims at the
claw tips. The pick is therefore by the surface error (pass at 70 %) and close-ups.

Texture drift at the pick: 20 faces over 40 (6.8 cm²), no drift lock. Close-ups from the GLBs with their own normals
(`review/glbclose/sheet_a.png`: head front/three-quarter/side, open jaw, ribs side/front, spine, tail;
`sheet_b.png`: both wings front and back, fore and hind claws, tail tip, Attack and Death; rows installed / 70 %
textured, then clay) show no visible change in horns, teeth, ribs, vertebrae, claws, torn membrane edges or the
tail spikes. `review/close/` comes from the welded `source.blend`, whose custom normals are scrambled (fake
wrinkles on the source clay), so judge shading only from `review/glbclose/`.

## Build

`export_cand.py` (Cand_70, from `work/ladder_u.blend`) -> `swap_lod0.py` -> `build_lods.py` (the m616 ratios:
0.5 / 0.25 / 0.125, 4 influences) -> `../mm8_m616_claude/scripts/shrink_shadow_lods.py` (shadow LOD1-3 0.3/0.5/0.7 mm
inside the surface, as installed) -> `carry_variants.py` (variants on all 7 LOD/shadow primitives) ->
`check_winding.py` (0 inverted closed parts): `export/mm8_m616.glb`, 7.5 MB (installed 8.5 MB), six clips.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 12,635 | 6,306 | 3,124 | 1,532 |
| reduced | 8,843 | 4,408 | 2,168 | 1,056 |

`work/lod_check_{src,r70}.json`: every LOD keeps the 0.549 m rest height; no face stretches over 20x in any frame of
any clip; Death/Dead stay above the floor in every LOD (lowest 2.8 mm, as installed). Fly dips to -18 mm at LOD0 in
both (wing tips on the downstroke; actor flight supplies altitude). LOD3 ends 1.5 cm short at the left wing tip
(installed LOD3: 0.6 cm) and its rest feet sit 2.3 cm up (installed LOD3: 1.1 cm). `review/lods/sheet.png`:
installed / reduced, LOD0-3, Fly three-quarter, Attack and Dead.

No `gates.json` in `../mm8_m616_claude/` (no shared gate run needed).

Viewer: <http://127.0.0.1:8912/level_generation/creatures/mm8_m616_reduce_claude/review/viewer/> (installed vs 70 %,
three tiers); `python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m616_reduce_claude
check`: 36 clip switches, no console errors.

## Status

Installed 2026-10-19 after user review ("ok") with `tools/install_model.py --world mm8`; actor regression `mm8_bone_dragon_actor_models_keep_native_tiers_and_motion` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Install (from the repository root):
`python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m616_reduce_claude/export/mm8_m616.glb`,
then `OPENYAMM_REGRESSION_FILTER=mm8_bone_dragon_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_bone_dragon_actor_models_keep_native_tiers_and_motion`) and add the ledger row.
Rollback: `python3 tools/install_model.py --world mm8
level_generation/creatures/mm8_m616_reduce_claude/work/mm8_m616_source_pre_reduce.glb`.

Reproduce: `REA_GLB=<abs path of the rollback source> REA_NODE=BoneDragon blender -b -P scripts/import_source.py` ->
`dump_mesh.py` -> `REA_SMALL=90 small_pieces.py` (copy to `work/keep_small90.npy`) ->
`seam_keep.py work/keep_small90.npy work/keep_s.npy` -> `REA_KEEP_FACES=work/keep_s.npy REA_PROTECT_HEAD=1
REA_PROTECT_RATIO=0.8 run_ladder.sh u 0.75,0.70,0.65,0.60` -> `close_ladder.py`, `glb_close.py`,
`texture_drift.py r70` (needs `work/basecolor.png` from the GLB) -> build as above -> `lod_check.py`, `lod_views.py`.

## Floor fix — 2026-10-21

`--hover 0.018007 Death Dead`: the wings cut 18 mm under the floor; every living clip is raised by that, eased out over Death. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m616.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.
