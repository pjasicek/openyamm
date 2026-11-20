# MM7 Bat (`m158`, Giant / Vampire / Inferno Bat) reduction (2026-10-21)

User: "all 3 are good, reduce tris". [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) default route, no-retexture
branch, with the scripts of [mm8_m552_reduce_claude](../mm8_m552_reduce_claude/README.md) (texture-aware MeshLab
ladder, parent-fixed `reduce_ladder.py`, floor-contact LOD lock, stretch/drift/dark-sliver checks). No Meshy credits.
Not installed (Batch H rule).

## Source

The accepted [mm7_m158_claude](../mm7_m158_claude/README.md) export had been reduced with Blender's edit-mode
decimate (15,216 -> 8,818), which the playbook rules out (it slides UVs across seams). This project starts again from
the unreduced Smart Topology mesh: `scripts/build_source.sh` exports `../mm7_m158_claude/work/uv_master.blend` with the
bat project's own chain (material contract, prepare, LODs, shadow fix, tier ramps) to `work/mm7_m158_source.glb`
(15,216 triangles, sha256 `ce783a8e…`). Same textures, ramps, rig and clips as the accepted bat.

`import_source.py`: weld 15,760 -> 637 open edges; 15,210 triangles after the weld (6 duplicate faces merged; the
membrane is one sheet with a double-sided material, so no reversed copies are lost); 120 coincident vertices with
other weights kept apart. Thresholds scaled to the 0.95 m wingspan (p99 2.85 mm, max 14.25 mm), as the m552
reduction scaled to its span.

## Ladder

| config | step | triangles | p99 / max mm | IoU (min) | SSIM | |
|---|---|---:|---|---|---|---|
| head + ears at 60 % (`h60`) | r60 | 9,124 | 1.20 / 3.68 | 0.991 | 0.996 | pass |
| | r50 | 7,602 | 1.78 / 5.10 | 0.983 | 0.995 | pass |
| | r40 | 6,082 | 2.87 / 9.41 | 0.973 | 0.992 | fail |
| uniform (`uni`, `uni2`) | r50 | 7,604 | 1.52 / 4.63 | 0.986 | 0.995 | pass |
| | r45 | 6,844 | 1.77 / 5.10 | 0.985 | 0.995 | pass |
| | **r40** | **6,084** | 1.99 / 6.80 | 0.980 | 0.994 | **auto-pick** |
| | r35 | 5,322 | 2.31 / 6.80 | 0.974 | 0.993 | fail (IoU) |
| | r30 | 4,562 | 2.76 / 9.41 | 0.971 | 0.992 | fail |

A gentler head cut only moved the loss onto the wings; the uniform cut keeps the head as well
(`review/close/sheet_uni.png`: eyes, fangs, ears, face from front, three-quarter and side; feet, wing tip, corpse) and
the membrane on both sides (`review/close/sheet_uni_wing.png`). Sheets: `review/ladder_sheet_{h60,uni,uni2}.png`.

Checks on r40:
- Stretch (`stretch_check.py`, every 2nd frame of every clip): 0 faces in source, r45 and r40.
- Texture drift (`texture_drift.py`): 57 faces over 40, all under 2 cm² (the lock rule only acts on faces over 3 cm²),
  so no drift lock round.
- Dark slivers (`dark_slivers.py`): 109 / 127 / 136 flagged faces at r50 / r45 / r40, all thin pink finger bones on
  the green membrane; the worst five spots render the same as the source from above and below at 9 cm
  (`review/spots/sheet_dark.png`). The count rises slowly with the cut, a noise floor of thin painted lines.
- Tiers B and C (`review/shots/sheet_tiers_bc.png`) and A (close-ups) match the source.

## Result

`scripts/build_export.sh`: `export_cand.py` (Cand_40) -> `swap_lod0.py` (into the source GLB) -> `floor_contacts.py`
(Death/Dead, 352 vertices, 111 points) -> `build_lods.py` (0.5 / 0.25 / 0.125, 4 influences, contacts protected) ->
the bat project's `shrink_shadow_lods.py` (≤ 1 mm) -> `carry_variants.py` -> `check_winding.py`.

| | LOD0 | LOD1 | LOD2 | LOD3 | file |
|---|---:|---:|---:|---:|---:|
| unreduced source | 15,216 | 7,603 | 3,786 | 1,882 | 8.1 MB |
| accepted export (Blender decimate) | 8,818 | 4,395 | 2,186 | 1,083 | 6.5 MB |
| **this reduction** | **6,084** | **3,024** | **1,503** | **739** | **5.9 MB** |

`export/mm7_m158.glb`, sha256 `0ed555635ddecf16ae2b84287de0995d496a7efc568722bcb6aad89663053077`; 3 variants on all
8 colour/shadow meshes; winding 0 inverted closed parts. `lod_check.py` (every frame of every clip, every LOD):
Dead rests at −0.2 mm at all four LODs (source LOD1–2 −0.3 mm), no stretched faces at any LOD (the source's LOD2 had
one), bounds kept (LOD2/3 wing span about 1.5 cm shorter at the right tip). Flight clips go below the origin by design.

## Viewer

[review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m158_reduce_claude/review/viewer/): three tiers,
source vs r40 (ramps baked per tier by `viewer_variants.py`). `python3 tools/run_creature_review.py --project
level_generation/creatures/mm7_m158_reduce_claude check`: 30 clip switches, no console errors.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m158_reduce_claude/export/mm7_m158.glb --world mm7
```

Binding unchanged (see the bat project README). Rollback / higher-detail sources: `work/mm7_m158_source.glb`
(unreduced) or `../mm7_m158_claude/export/mm7_m158.glb` (8,818).

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -3.8; dying sinks to -4.1; dying sinks to -4.5; living lowest at -49.7 (suggested hover 0.234281); living lowest at -54.6 (suggested hover 0.234281); living lowest at -59.6 (suggested hover 0.234281).
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m158.glb export/mm7_m158.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --hover 0.234281 Death Dead --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m158.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).
