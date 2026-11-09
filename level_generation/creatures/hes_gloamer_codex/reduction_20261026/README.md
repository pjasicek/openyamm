# Gloamer triangle reduction — 2026-10-26

User request: “good, reduce tris.” The corrected colours are approved and retained byte-for-byte.
Selected body: **9,070 triangles**, down from 11,342 (20.03%). Existing LOD1–3 remain 5,667 / 2,835 / 1,398;
the small elder sac remains 528 / 264 / 132 / 66. Full-detail shadows now use the reduced mesh.

The 70% and 60% candidates failed silhouette/deformation checks; 80% passed (minimum silhouette IoU 0.9946,
mean textured SSIM 0.995, two-way surface p99 3.99 mm, maximum 24.49 mm across all nine clips).
All 33 maps, materials/ramps, animation sampler data and inverse bind matrices remain identical to the accepted source.
The same weight-safe weld and texture-aware reduction route as `mm8_m492_reduce_claude/` is used.

Selected editable body: `work/selected.blend`. Rollback: `before/hes_gloamer.glb`, with the original sac, authoring
file, textures, viewer and state beside it. Do not overwrite these snapshots on resume.

Reproduction, under the top-level creature lease:

1. Run `scripts/import_source.py`, then `scripts/dump_mesh.py` through `tools/run_creature_blender.sh`.
2. Run the shared `mm8_m492_reduce_claude/scripts/decimate_tex.py` with the existing
   `/tmp/lancer_lod_venv/bin/python`, this branch's `work` directory and ratios `0.80,0.70,0.60`.
   Set `REA_KEEP_FACES` to `work/keep.npy`, `REA_GROUPS` to `work/groups.npy` and
   `REA_GROUP_RATIOS=1:0.75,2:0.65` (paths relative to the invocation directory).
3. Run `scripts/reduce_ladder.py` through the Blender wrapper, then `scripts/compare_ladder.py` with Python.
   Small parts and sole contact faces are kept; head/fingers have separate budgets. Original vertices retain
   exact weights; new vertices take interpolated surface weights, limited to eight influences.
4. `scripts/export_cand.py` exports the selected `Cand_80` and saves a clean authoring file. `scripts/swap_lod0.py`
   replaces the source LOD0 and rebuilds its complete merged shadow, retaining the fitted lower LODs.
5. Root `scripts/prepare_viewer.py`, `validate_runtime.py`, `check_runtime_floor.py`, this branch's
   `check_contacts.py`, LOD/close-up reviews and the reusable viewer wrapper verify the result. Restage under
   the exclusive stage lock and use shared stage/engine locks around native/headless checks.

[Full evidence](review/results.json), [contact gate](review/contacts.json), [close-up comparison](review/close_tex.jpg),
[clay comparison](review/close_clay.jpg), [playback](review/playback/playback.json), [LOD scores](review/lods/scores.tsv).
No retexture, new Meshy charge, engine change or map edit was needed. Full gameplay regression was not repeated.
