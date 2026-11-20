# MM8 Crystal Dragon (`m548`, Crystal Dragon A/B/C) reduction (2026-10-19)

User-picked batch (m484, m548, m452, m588). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md),
no-retexture branch: the installed texture set (2K base colour, 1K normal and ORM), material, clips and the mouth socket
stay byte-identical. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m548.glb` (built in `../mm8_m548_codex/`), copied to
`work/mm8_m548_source_pre_reduce.glb` (rollback source).
- **Structure:** one opaque material and one `CrystalDragon` node, 23 joints, 4 influences.
- **No tiers or ramps:** all three tiers share palette 548 and differ only in scale, so there is no region mask, no
  tier ramp and no `KHR_materials_variants`.
- **No crystal effect mesh:** the crystal is solid, with no transmission, emissive or glass shell, so there is no
  separate crystal mesh to keep with its own LODs.

## Flat shading (new for this creature)

The source is fully flat-shaded: 7,570 triangles on 22,708 vertices, every triangle with its own three vertices and
face normal (the faceted crystal look). The normal map adds the crystal veins on top.
- **Candidates:** `reduce_ladder.py` takes `REA_FLAT=1` and builds the candidates flat (`use_smooth = False`). The glTF
  export then writes per-face normals again (6,132 triangles on 18,396 vertices).
- **LODs:** `tools/build_actor_lods.generate` keeps the flat faces.
- **Weld:** `import_source.py` welds the 22,708 split vertices to 3,853, which leaves 196 open edges (the mouth slit,
  the neck and a few joint seams, unchanged by every step). It finds 3 coincident pairs with different weights, which
  `decimate_tex.py` separates as on the MM8 Dragon.

## Regions

`face_bones.py` and `make_groups.py`. The head and crown hold 3,505 of the 7,570 faces (the codex build protected
their density), so most of the saving comes from them. The body, legs and tail are already lean facets.

| region | faces | budget |
|---|---:|---|
| eyes (two pieces of 96 and 122 faces), one stray face | 219 | kept exactly |
| lip line: faces touching a vertex shared by Head- and Jaw-dominated faces, plus one ring | 742 | kept exactly |
| open borders of head, jaw and neck | 169 | kept exactly |
| fleck lock (below) | 108 | kept exactly |
| rest of the head and crown | 2,861 | 60 % (group 1) |
| rest of the jaw | 36 | 70 % (group 2) |
| body, legs, tail | rest | ladder remainder |

Weights come from the preserved UVs (`dump_weights.py`, `uv_weights.py`, `REA_WEIGHTS=component`, from
`mm8_m592_reduce_claude`). With the nearest-face transfer, single limb vertices in the corpse pose were 22 mm off.

## Ladder

Limits scaled to the 0.80 m height: p99 2.4 mm, max 12 mm, over all clips.

| run | head | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| g1 | 50 % | 80 % | 6,056 | 2.53 / 5.35 | 0.996 | 0.997 | fail (p99) |
| h6 | 60 % | 85 % | 6,414 | 2.00 / 5.74 | 0.997 | 0.998 | pass |
| h6 | 60 % | 80 % | 6,056 | 2.34 / 10.32 | 0.997 | 0.997 | pass |
| h6 | 60 % | 75 % | 5,676 | 3.30 / 21.98 | 0.992 | 0.993 | fail |
| h7 | 70 % | 80 % | 6,056 | 2.90 / 21.98 | 0.992 | 0.994 | fail |
| lock | 60 % | 80 % | 6,056 | 2.45 / 10.32 | 0.996 | 0.997 | fail (p99) |
| lock | 60 % | 82 % | 6,208 | 2.17 / 8.63 | 0.997 | 0.998 | pass |
| **lock** | **60 %** | **81 %** | **6,132** | **2.31 / 10.32** | **0.997** | **0.997** | **pick** |

- **Where the error sits:** below 80 % it is the body and limbs (`region_error.py`, `worst_points.py`). The lean leg
  and dorsal facets lose their shape, and from 75 % one tail spike shrinks (`review/close/sheet_h6_body.png`).
- **Head ratio:** cutting the head harder (50 %) failed. Cutting it less (70 %) moved the cut onto the body and failed
  sooner.
- **Head close-ups:** at 75-85 % the head and crown read the same as the source (`review/close/sheet_h6_head.png`).

Colour checks on the h6 80 % step:
- `texture_drift.py`: no face over 40.
- `fleck_check.py`: one fleck, 8 of 48 samples, a dark face beside the right eye.
- `dark_slivers.py`: four small dark faces at the same spot.

`fleck_check.py ... work/keep.npy work/keep_lock.npy` (REA_LOCK_R 0.02) kept the source faces within 2 cm of the fleck
(108 faces), and the ladder was rerun with that lock. At 81 % there are no flecks and no drift over 40.
`dark_slivers.py` still lists three faces at a 0.54-0.62 brightness ratio:
- face 501 is an unchanged source face (a false positive);
- two new faces at the crown base, 1.1 and 0.8 cm²;
- neither is visible in the close-ups.

## Build

`export_cand.py` (Cand_81, REA_NODE=CrystalDragon) -> `swap_lod0.py` -> `floor_contacts.py` -> `build_lods.py` ->
`shrink_shadow_lods.py` -> `fix_lod_winding.py`, giving `export/mm8_m548.glb` (6.9 MB; installed 7.6 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 7,570 | 3,785 | 1,891 | 945 |
| reduced | **6,132** | 3,065 | 1,532 | 919 |

LOD build:
- **Ratios:** 0.5 / 0.25 / 0.15; LOD3 has 919 triangles.
- **Protected points:** the 28 Death/Dead floor-contact points, and vertices within 5 mm of the side, front, back
  and top extremes.
- **What failed first:** the m592 recipe (2 cm extreme bands, 0.125) protected 1,734 vertices, because every paw sits
  in the floor band and the flat mesh triples each vertex. LOD3 then collapsed into large sheets
  (`review/lods/sheet.png` is the fixed build).
- **Shadow LODs:** the shadows are pushed inside the colour surface by at most 4 mm. The m592 limit of 15 mm hollowed
  the 1 cm crown spikes, and flat facet normals make the distance estimate noisy. The installed shadows had an inward
  correction of the same order.

Checks:
- **`lod_check.py` (REA_NODE=CrystalDragon):**
  - every LOD keeps the LOD0 bounds (0.62 x 0.91 x 0.80 m);
  - the lowest point in every clip is -0.3 mm, as the source;
  - no face stretches in any clip at any LOD.
- **Unchanged from the installed GLB:** the animation accessors, materials, joint list and all three images
  (byte-compared).
- **`check_winding.py`:** 0 inverted closed parts. `fix_lod_winding.py` repaired nothing.

Shading, judged only from GLBs imported directly (`glb_close.py`, `review/glbclose/sheet.png`): head front and side,
open mouth (Attack frame 8, jaw 11.8 deg), crown, forepaw, flank and tail all keep the flat facets and veins of the
installed model. One merged facet beside the right eye catches a slightly larger specular glint from the front.

## Texture

No retexture and no local fix needed: one texture set, no tiers, and no colour fault found in the head or body.
Without tier ramps, the ramp-darkening issue reported on the ratman cannot occur here.

## Animation (unchanged)

`bone_velocity.py` on Attack (also the `cast` alias, 24 Hz keys, release 0.375 s):
- **No dead start:** the first key already moves (173 deg/s at 0.083 s).
- **The lunge:** it accelerates from 120 to 577 deg/s between 0.17 and 0.25 s. The head peaks at 680 deg/s at
  0.29 s, before the release.
- **After the release:** a brief settle (0.42-0.50 s, about 65 deg/s), then a second recovery motion (0.58-0.67 s,
  262 deg/s).
- **Jolts:** no single-key jolt beyond that lunge.

## Viewer

`review/viewer/`: installed and reduced per tier (A, B, C at their native scales), from the codex viewer. The native
reference frames link to the shared packed-outline collection. `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_m548_reduce_claude check`: 48 clip switches, no console errors.

## Status

Installed 2026-10-19 (user: "crystal dragon ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first);
`OPENYAMM_REGRESSION_FILTER=mm8_crystal_dragon ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`:
`mm8_crystal_dragon_actor_models_keep_native_sizes_and_roles` passes (`review/regression.log`). Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m548_source_pre_reduce.glb` with
`tools/install_model.py --world mm8`.

Reproduce:
1. Import and dump: `REA_NODE=CrystalDragon REA_GLB=<rollback source> import_source.py`, then `dump_mesh.py`,
   `face_bones.py`, `dump_weights.py`, `small_pieces.py`, `make_groups.py`.
2. Ladder: `REA_FLAT=1 REA_WEIGHTS=component REA_KEEP_FACES=work/keep.npy REA_GROUPS=work/groups.npy
   REA_GROUP_RATIOS=1:0.6,2:0.7 run_ladder.sh h6 0.85,0.80,0.75,0.70`.
3. Fleck lock: `fleck_check.py r80 work/keep.npy work/keep_lock.npy` (REA_LOCK_R=0.02); clear the locked faces from
   the groups (`work/groups_lock.npy`); rerun the ladder (label `lock`, steps 0.82,0.81) with the lock files.
4. Build as above with `LOD_RATIOS=0.5,0.25,0.15`.

Material (2026-10-19): the installed model now has the gem-crystal material from [`../mm8_crystal_material_claude/`](../mm8_crystal_material_claude/README.md) (gloss and per-facet colour; rollback there).

## Gait rollout (2026-10-31, package q4)

**Walk2** (trot as Walking, front L + hind R at 0; 0.4933 m in 0.6667 s, authored 0.74) and **Run2** (transverse gallop, front L at 0; 0.8213 m in 0.5625 s, authored 1.46) grafted onto the installed model by `../gait_rollout_20261031/q4/scripts/gait_m548.py` (imports `../mm8_m548_codex/scripts/motion.py` on `../mm8_m548_codex/export/mm8_m548.blend`). Binding for Crystal Dragon A-C: `walking: Walk2`, `stride_length: 0.4933`, `run: Run2`, `run_stride_length: 0.8213` (it wandered on Running x1.25-1.47 and chased on it x2.48-2.92). Gate window: wander x0.96-1.13, chase x0.98-1.15. Head bob 0.6 % / 8.9 %; toe-out front +11.3, hind +5.7 as every clip.

Rebuild: `../gait_rollout_20261031/q4/README.md` (Rebuild). A far-LOD repair rerun (`lod_repair_claude`) or any rebuild of the installed GLB must re-graft these clips from `../gait_rollout_20261031/q4/work/m548_clips.glb` with `../claude_shared/graft_clips.py`. Rollback source: `../gait_rollout_20261031/q4/work/rollback/mm8_m548.glb`.
