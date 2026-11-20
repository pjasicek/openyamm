# MM8 Wasp Warrior (`m556`, Wasp Warrior A/B/C) reduction (2026-10-19)

User-picked MM8 triangle-reduction batch 2 (coordinated with sessions openyamm-b4, openyamm-f9 and openyamm-4f).
Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part needed
rebuilding, so the installed textures, palette variants (`KHR_materials_variants`) and region ramps stay valid.
No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m556.glb` (with `mm8_m556_sword.glb`,
`mm8_m556_shield.glb`), byte-identical to `../mm8_m556_claude/export/` (sword/slash revision `m556_slash_v2`; the
`assets_dev` copies are the cooked runtime of the same export). Rollback copies: `work/mm8_m556{,_sword,_shield}_source_pre_reduce.glb`.
One body material per tier, one `Wasp` node, 48 bones, seven clips. Scripts are copied from
`../mm8_m624_reduce_claude/scripts/` (fixed `reduce_ladder.py`) and the held-prop chain from `../mm6_figc_reduce_claude/`.

## Keep sets

Weld 13,547 -> 59 open edges, no coincident vertices with other weights and no two-sided faces (`find_doubles.py`:
the wings are closed leaf membranes). The 59 edges are seven small loops, identical in source and pick, at the
shoulder and middle-leg joint balls, a right claw, the right forearm and the thorax; close-ups with back-face culling
from six directions (`hole_views.py`, `review/holes/sheet_loops.png`) show none of them (they sit inside joints and
sockets). The wasp has no armour or headwear over skin.

`m556_sets.py` (pieces from connected components, labels by dominant bone):
- **Kept exactly (5,917 faces):** antennae, mandibles, middle legs, the small joint balls, the arm faces dominated by
  Hand/Claw bones (sword and shield grips), both wings (a 70 % cut notched their outline and dented the membrane),
  the hind tarsi (segmented beads) and the stinger (`Abdomen4`).
- **Head** (Head/Neck weights, 1,509 faces) decimated on its own at 70 %; 60 % (ladder e) faceted the snout.
- **Hind legs** (femur/tibia, 802) and **upper/fore arms** (559) at 60 % each.
- The trunk (thorax and abdomen) takes the rest.

## Ladder

Limits for the 0.95 m model (p99 2.86 mm, max 14.3 mm).

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 9,635 | | | |
| a: wings/legs/arms 70 %, head 80 % | 85 % | 8,189 | 1.95 / 6.40 | 0.987 | pass; wing outline notched |
| b: groups 60 %, head 70 % | 80 % | 7,705 | 2.33 / 6.40 | 0.983 | pass; wing outline notched |
| c: groups 50 %, head 60 % | 78 % | 7,513 | 2.25 / 7.93 | 0.981 | pass; wings notched, eye edge faceted |
| d: wings, tarsi, stinger kept; legs/arms 60 %, head 70 % | 87 % | 8,379 | 1.96 / 6.40 | 0.993 | pass |
| **d** | **85 %** | **8,187** | 2.57 / 7.53 | 0.988 | **pick** |
| d | 83 % | 7,995 | 4.88 / 13.24 | 0.982 | fail (p99) |
| e: as d, legs/arms 50 %, head 60 % | 83 % | 7,995 | 2.57 / 7.93 | 0.991 | pass; snout faceted |

Texture drift at the pick: 19 faces over 40 (20.8 cm²), no drift lock. GLB renders with each file's own normals
(`review/glbclose/sheet_de.png`: installed / d85 / e83, textured and clay; `sheet_a.png`, `sheet_b.png` for the
first ladders) show no change in eyes, mandibles, antennae, wings, claws, tarsi, stinger or the abdomen pattern.

## Props

- **Sword** 1,732 -> **952** (r55, `prop_ladder.py` with the grip kept): every face within 12 mm of the left
  hand's finger vertices taken into the `Sword` joint space (`prop_grip.py`, 398 faces) is kept exactly, the rest
  is decimated with its cut edge preserved; normals by angle (35°). r45 (778) flattened the pommel ball; transferred
  normals left dark streaks. LOD chain 952 / 828 / 326 / 300 (installed LOD1-3 kept). `review/props/sword_compare.png`
  (rows installed, r55, r45, r45 transferred normals).
- **Shield unchanged** (1,488): every step turned the rims polygonal and flattened the dish shading
  (`review/props/shield_compare.png`: installed, r55, r45).

## Build

`export_cand.py` (Cand_85) -> `swap_lod0.py` -> `build_lods.py` (installed ratios 0.5 / 0.18 / 0.06, 4 influences)
-> `../mm8_m556_claude/scripts/shrink_shadow_lods.py` (shadow LOD1-3 tucked inside, thin membranes excluded, as
installed) -> `carry_variants.py` (variants on all 7 LOD/shadow primitives) -> `fix_clips.py export/mm8_m556.glb
export/mm8_m556_sword.glb work/mm8_m556_shield_source_pre_reduce.glb` (Death and Attack fixes below) ->
`check_winding.py` (0 inverted closed parts): `export/mm8_m556.glb`. Sword: `prop_build.py` (PROP_NORMALS_ANGLE=35) -> `prop_swap_glb.py`:
`export/mm8_m556_sword.glb`.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| body installed | 9,635 | 4,816 | 1,734 | 575 |
| body reduced | 8,187 | 4,093 | 1,473 | 488 |
| sword installed | 1,734 | 828 | 326 | 300 |
| sword reduced | 952 | 828 | 326 | 300 |

`work/lod_check_{src,r85,r85fix}.json` (r85fix after the clip fixes, same results): every LOD keeps the installed bounds (0.905 m standing height, 1.0 m wingspan);
no face stretches over 20x in any clip; lowest point per LOD equals the installed (LOD3 4.8 mm above the floor,
installed 1.8 mm below). `review/lods/sheet.png`: installed / reduced per LOD, fly three-quarter, attack and side;
the wing outlines stay whole in every LOD.

## Source-animation scan (`clip_scan.py`, viewer frame = time x 48) and fixes

The scan found two faults in the installed clips (not caused by the reduction); both are fixed on the staged export
by `fix_clips.py` (coordinator request before review). No dead starts: every clip moves from frame 1 (Attack
included). Loops close; no clip goes under the floor.

- **Death, frames 26-34:** the thorax fell to 34.6 cm (frame 26), rose again to 54.7 cm (frame 30), then dropped
  16.4 cm in one frame (frame 33) to 14.4 cm. Cause: during the roll the left wing swung down through vertical (to
  52 cm below the thorax) and the build's floor lock lifted the Root to keep the wingtip on the floor. Fix: the four
  wing bones turn in one eased move from their frame-22 pose to the frame-34 landing pose (slerp path, Hermite in
  angle with the incoming and outgoing speeds; largest step 19.9°, the clip's own flap speed, before 28.6°), and
  the Root height follows a monotonic Hermite fall from frame 25 (its height and speed) to the frame-34 landing
  (speed zero): thorax 38.1 / 32.1 / 27.2 / 23.2 / 20.1 / 17.8 / 16.2 / 15.1 / 14.6 / 14.4 cm over frames 25-34, no
  rise, largest step 6.6 cm (the existing fall before frame 25). Lowest body vertex 2.0 mm and lowest sword/shield
  vertex 16.6 mm over the clip (unchanged; no frame needed the floor raise). Frames 34-42 and Dead are unchanged.
  `review/death/thorax_height.png` (before / after, lowest body and prop vertex), `review/death/filmstrip_f22_38.png`.
- **Attack, frame 55 (1.15 s, recovery):** `Hand_L` turned 30° in one frame (frames 52-59: 12.6, 24.8, 30.0, 21.2,
  13.5°). Fix: frames 47-60 respread along the hand's own path by cumulative angle (Hermite in path length keeping
  the incoming and outgoing speeds): largest step 16.6°. Frames 47 and 60 and the 0.875 s impact (frame 42) are
  unchanged. The sword stays in the hand (child of the joint); the blade keeps at least 35.7 mm from the body in the
  changed frames (before: 25.1 mm; `clip_probe.py`). The blade's nearest pass to the body, 0.1 mm at frame 38 during
  the cut, is unchanged from the installed clip.

Only six animation accessors change (Attack `Hand_L` rotation; Death `Root` translation and the four wing
rotations), rewritten in place; every other clip, the geometry and the images are byte-identical to the pre-fix
export (`work/mm8_m556_r85_prefix.glb`). **A re-export from `../mm8_m556_claude/` (or a rebuild of this export)
needs `fix_clips.py <game.glb> <sword.glb> <shield.glb>` re-run**, or both faults come back.

## Viewer

`review/viewer/` (installed vs 85 %, three tiers), with the sword and shield baked in as children of their joints
(`viewer_variants.py <glb> <tag> <sword.glb>:Sword <shield.glb>:Shield`), so they animate with the body as in game;
`review/viewer_attack_props.png` confirms it. The reduced models carry the fixed Death and Attack clips
(manifest sha256 and `?v=` refreshed). `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_m556_reduce_claude check`: 42 switches, no console errors.
http://127.0.0.1:8912/level_generation/creatures/mm8_m556_reduce_claude/review/viewer/

## Status

Installed 2026-10-19 after user review ("wasp ok"), body and sword, with the Death/Attack clip fixes, via `tools/install_model.py --world mm8`; shield unchanged; actor regression `mm8_wasp_warrior_actor_models_keep_flight_and_equipment` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Install (from the repository root):
```
python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m556_reduce_claude/export/mm8_m556.glb
python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m556_reduce_claude/export/mm8_m556_sword.glb
OPENYAMM_REGRESSION_FILTER=mm8_wasp_warrior_actor_models ./build/game/openyamm --headless-run-regression-suite actors
```
(`mm8_wasp_warrior_actor_models_keep_flight_and_equipment`), then the ledger row.
Rollback: install `work/mm8_m556_source_pre_reduce.glb --name mm8_m556.glb` and
`work/mm8_m556_sword_source_pre_reduce.glb --name mm8_m556_sword.glb` the same way.

Reproduce: `import_source.py` (REA_NODE=Wasp, REA_GLB=the rollback source) -> `REA_PROTECT=Head,Mandible,Neck
dump_mesh.py` -> dominant bones (`work/domgroup.npz`) -> `m556_sets.py` -> `REA_KEEP_FACES=work/keep_b.npy
REA_GROUPS=work/groups_b.npy REA_GROUP_RATIOS=3:0.6,4:0.6 REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.7 run_ladder.sh d
0.89,0.87,0.85,0.83` -> `glb_close.py`, `texture_drift.py r85` -> build as above -> `lod_check.py` (REA_NODE=Wasp),
`lod_views.py`, `hole_views.py`, `clip_scan.py`, `fix_clips.py`, `clip_probe.py`, `death_plot.py`, `death_strip.py`; sword: `prop_dump.py -- sword shield`, `prop_grip.py`,
`PROP_RATIOS=0.7,0.55,0.45,0.35 prop_ladder.py sword shield` (pymeshlab venv), `prop_build.py`, `prop_swap_glb.py`,
`prop_compare.py`/`prop_sheet.py`.
