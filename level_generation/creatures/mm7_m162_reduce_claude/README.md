# MM7 Behemoth (`m162`, Young Behemoth / Behemoth / Ancient Behemoth) reduction (2026-10-20)

User request after accepting batch E: "do tris reduction now". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part needed rebuilding, so the textures,
region mask, tier ramps and clips stay as exported. No Meshy credits. Scripts are copied from
`mm8_m452_reduce_claude/` (ladder, UV weights, error lock, LODs, LOD check) and `mm8_m492_reduce_claude/`
(`carry_variants.py`); the gate scripts `outliers.py`, `g6_claws.py`, `sole_probe.py` and `shrink_shadow_lods.py`
are copies from `mm7_m162_claude/scripts/`. Batch E rules apply: nothing installed, nothing in `assets_dev/` or
`assets_source/`, `mm7_m162_claude/` untouched.

Source: `../mm7_m162_claude/export/mm7_m162.glb` (not installed), copied to
`work/mm7_m162_source_pre_reduce.glb` (rollback source). One material `M162_A` (body and head merged into a 2080×1024
atlas) with the tier variants `M162_B` / `M162_C` (`KHR_materials_variants`, one region: mane + beard), one `M162`
node, 52 `B_*` bones plus twist bones, 4 influences. The export is flat-shaded (every triangle has its own vertices).

Pieces: one skin piece (8,509 faces: body, head, ears and the three sickle claws of each paw) and 337 small pieces
(6,242 faces): about 240 mane shingles on the clavicles and spine; on the head the teeth, upper and lower tusks, eyes
and the beard/crown shingles.

## Ladder

Weld 44,142 -> 1,416 open edges (unchanged by every step); 294 coincident vertices with other weights (mane shingles
touching the skin or each other) are separated for MeshLab and keep their exact source weights. Limits scaled to the
2.2 m height: p99 6.6 mm, max 33 mm.

Region budgets (`make_groups.py`, dominant bone):
- **Kept exactly:** every small piece (mane shingles, teeth, tusks, eyes, beard and crown shingles).
- **Head and neck:** 60 %. **Paws and claws:** 55 %. **Feet and toes:** 50 %.
- **Torso, arms and legs:** fill the rest.

| step | config | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a | head/paws 70 %, feet 60 % | 11,799 (80 %) | 5.10 / 30.0 | 0.997 | 0.987 | pass |
| a | | 11,061 (75 %) | 7.26 / 52.7 | 0.996 | 0.983 | fail |
| b | + mane shingles at 60 % | 10,323 (70 %) | 20.0 / 115 | 0.991 | 0.983 | fail |
| c | head 60 %, paws 55 %, feet 50 % | 11,357 (77 %) | 5.45 / 30.8 | 0.995 | 0.986 | pass |
| **c** | | **11,063 (75 %)** | **6.08 / 32.3** | **0.995** | **0.985** | **picked** |
| c | | 10,767 (73 %) | 6.85 / 52.7 | 0.995 | 0.983 | fail |
| e1 | c + error lock (136 vertices over 15 mm, 2.5 cm) | 10,767 (73 %) | 12.9 / 58.4 | 0.992 | 0.976 | fail |
| s | c + sole faces kept | 11,061 (75 %) | 8.30 / 52.7 | 0.995 | 0.982 | fail |

- **Mane shingles cannot be cut.** Decimated at 60 % (b) they collapsed into flat slivers (p99 20 mm at every step).
  Kept exactly, they are 42 % of the reduced model, which is what stops the cut near 75 %.
- **Where the error is:** spread over the torso and limbs, not the head or claws (`region_error.py`); the worst
  frames are the Attack crouch and the Death fall, where the belly folds onto the thighs. Moving budget from the head,
  paws and feet to the torso (c) passed 75 %.
- **Error lock and sole lock:** both took budget from the torso and made it worse (e1, s), as the playbook warns.
- **Soles:** the collapse placed 17 new sole vertices up to 1.8 mm under the rest floor; `export_cand.py` lifts
  vertices below z = 0 onto it (Standing back to 0.0 cm).

Close-ups of `work/ladder_c.blend` (source vs 75 %): `review/close/sheet_r75_tex.png`, `sheet_r75_clay.png` — face
front, three-quarter and both sides, tusks, crown, mane from behind and the side, both paws, claws raised and in the
slam, both feet, chest, Attack, Death, Running, Walking and the lower back. No feature changed. (The source renders
faceted there because the welded `source.blend` keeps its flat-shading flags; judge shading from the GLB renders.)

Texture checks: `texture_drift.py r75` 0 faces over 40 (p99 19); `dark_slivers.py r75` (`REA_DARK_L=80 REA_DARK_N=4`)
3 faces under 16 cm² (lip line, one toe sole), not visible in the close-ups.

## Shading: smooth (default) or flat

`export/mm7_m162.glb` is **smooth-shaded**: 12,691 vertices for 11,063 triangles (the flat export needs one vertex per
triangle corner), 8.2 MB. `export/mm7_m162_flat.glb` is the same reduction flat-shaded like the batch E export
(`REA_FLAT=1 scripts/build_export.sh`), 11.6 MB. `review/glbclose/sheet_tex.png` and `sheet_clay.png` show source,
smooth and flat straight from the GLBs: textured they look almost the same; smooth rounds the teeth and claws and
softens the faceted look of the mane, with slightly darker shading inside the crown shingles.

## Build

`scripts/build_export.sh [Cand_75]`: `export_cand.py` (Cand_75 of `work/ladder_c.blend` as `work/ladder.blend`,
REA_NODE=M162) -> `swap_lod0.py` (into the rollback source: materials, variants, ramps, clips unchanged) ->
`build_lods.py` -> `shrink_shadow_lods.py` -> `carry_variants.py` (the LOD builder drops the variant mappings from LOD
and shadow primitives; all 7 carried).

`build_lods.py`: ratios 0.5 / 0.22 / 0.08 of LOD0. The tool's 0.5 / 0.18 / 0.06 gave a 466-triangle LOD3 whose mane
fell apart into loose shards and whose head lost its silhouette (`review/lods/sheet.png`, middle row); 0.08 gives a
LOD3 as blocky as the batch E LOD3 (643). Protected points: the bounding extremes (5 mm) and LOD0 vertices within 4 mm
of the floor in any Death/Dead frame.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| batch E export | 14,752 | 7,322 | 2,453 | 643 |
| reduced | **11,063** | 5,461 | 2,207 | 645 |

## Gates

- **`lod_check.py`** (every LOD, every frame of every clip): bounds kept (1.96 × 1.84 × 2.20 m) at every LOD, no
  stretched face, the lowest point is the same at every LOD: Standing/Hit/Dead 0.0, Walking −3.7 mm (source −1.6),
  Running −2.1, Death −1.5 cm and Fidget −3.9 cm as in the source, Attack −12.5 cm (the claws strike into the floor,
  source −12.2). The batch E LOD3 floated up to 2.9 cm; the reduced LODs do not.
- **Edge stretch** (`outliers.py`, K 3, every frame, on GLB imports of both): max per clip source / reduced —
  Standing 1.19 / 1.19, Walking 2.85 / 2.80, Running 2.55 / 2.45, Attack 4.38 / 4.23, Hit 2.72 / 2.72,
  Death 3.82 / 3.52, Dead 3.12 / 3.01, Fidget 3.55 / 3.35.
- **G6 claws** (`g6_claws.py`, every 2nd frame): the same as the source — the known Death transient (right claws
  14.6 cm into the right thigh, source 14.7; batch E open issue), Dead 2.4 cm (2.3), Fidget 2.5 cm into the head
  (3.5); none in Standing, Running, Attack, Hit; Walking no forearm contact (source 0.2 cm).
- **Soles** (`sole_probe.py`): Standing 0.0 every frame; Walking −0.4..1.2 cm (source −0.2..1.1), Attack −0.6..2.2
  (−0.6..1.8), Hit 0.0..0.4, Fidget −0.1..1.2.
- **Winding** (`check_winding.py`): 0 inverted closed parts in both exports.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m162_reduce_claude/review/viewer/index.html`: batch E export
(r100), reduced smooth (r75, default) and reduced flat (r75f), each for tiers A, B and C (`viewer_tiers.py` bakes the
tier ramps for three.js into this project only; `viewer_manifest.py`). `run_creature_review.py check`: 72 switches, no
console errors. Shots: `review/shots/`.

## For the user to review

- Smooth or flat shading (both exported; the viewer has both).
- The crown/beard shingles read a little darker with smooth shading.
- LOD3 (645) is as coarse as before.

## Install later (not run)

Replaces the batch E export of `mm7_m162_claude/` (same binding, same clips, nodes and materials):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m162_reduce_claude/export/mm7_m162.glb --world mm7
```

For flat shading install `export/mm7_m162_flat.glb` with `--name mm7_m162`. Rollback: `work/mm7_m162_source_pre_reduce.glb`.

Reproduce:
1. `REA_NODE=M162 REA_GLB=level_generation/creatures/mm7_m162_reduce_claude/work/mm7_m162_source_pre_reduce.glb blender -b -P scripts/import_source.py`;
2. `dump_mesh.py`, `dump_faces.py`, `dump_weights.py` (blender), `make_groups.py`;
3. `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_small.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.6,2:0.55,3:0.5 run_ladder.sh c 0.77,0.75,0.73`
   (`run_ladder.sh` defaults to `REA_HEIGHT_M=2.2`);
4. `close_m162.py -- ladder_c.blend Cand_75`, `pair_sheet.py`, `texture_drift.py r75`, `dark_slivers.py r75`;
5. `scripts/build_export.sh` and `REA_FLAT=1 scripts/build_export.sh`;
6. `lod_check.py`, `lod_views.py`, `glb_close.py`; gates on `gate_import.py` copies (`work/gates.sh`);
7. `viewer_tiers.py <glb> <label>` for r100 / r75 / r75f, `viewer_manifest.py`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Attack sinks to -16.6; Attack sinks to -18.3; Attack sinks to -20.8; Fidget sinks to -4.8; Fidget sinks to -5.3; Fidget sinks to -6.0.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m162.glb export/mm7_m162.glb --lift-joints Fidget --lift-only 'B_Skirt*,Robe_*,…' --raise Fidget`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m162.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).
The Attack is left as it was: the left claw strikes up to 16.6 world units (14 cm) into the ground at the blow, and raising the root would hop the whole body (open for the user).

## Gait rollout (2026-10-31)

Package [h10](../gait_rollout_20261031/h10/README.md) appended `Sprint` (humanoid-set sprint on the hunched pose, 0.62 s, stride 4.0863) to the installed `assets_source/worlds/mm7/models/mm7_m162.glb`
(existing clips, meshes, skins and materials byte-identical; pre-gait copy `../gait_rollout_20261031/h10/work/mm7_m162_pre_gait.glb`)
and installed it; the bindings (`sprint: Sprint` for MAW's chase; the `Attack` floor fault above stays open) are applied by the rollout coordinator from `h10/bindings.yml`. Rebuild:
`level_generation/creatures/gait_rollout_20261031/h10/scripts/rebuild.sh m162`. A far-LOD repair, head-bob, reduction or
texture rerun that rebuilds this source must keep or re-graft these clips (copy the new source over the pre-gait copy
and rebuild).

## Anim fix (2026-11-11, MM6–MM8 audit)

Attack's left claw no longer strikes into the floor (left upper arm lifted at most 9.4° around the blow; floor audit
passes). Details: [mm7_m162_animfix_claude](../mm7_m162_animfix_claude/README.md).
