# Nine-item finish record

Completed all nine icons reserved in `remaining_split.json`, with no additional Meshy spending. See `review/texture_finish_accepted_9.png` and `review/texture_finish_native.json` for static and native evidence.

Material boundaries are authored on actual mesh faces, independently of albedo brightness. `finish_material_masks.py` retains the reviewed component assignments, exact silhouette renders and face-class receipts. `codex_texture.py` carries those classes into PBR maps, including through physical thickness. Its UV rasterizer no longer accepts extrapolated points outside triangles. `check_mask_bake.py` covers the triangle domain, face labels, lining and exported material roundtrip.

Paladin Boots' two reversed back panels were repaired without moving the source geometry or its UVs. Physical thickness follows the exterior bake so new reverse faces retain the exterior UV frame and explicit leather lining. Sun Cloak uses the same late-thickness sequence to preserve dyed pattern detail. Defender Helm has its source-icon ivory forehead stone in `work/codex_tex/equipment_6helm4_finished.blend`.

The Lucky Hat retains original front/back painted cells. Left/right/top were generated as individual exact-guide views; the first right replacement remains retained but superseded by its corrected second version. All current view bounds pass the original registration gate. No generated output was manually painted over or discarded.

`merge_owned_bounds.py --apply` changes only bindings for coordinator-installed, hash-verified models. It preserves every binding length and all other model rows. `review/bounds_merge_applied.json` records the final 64-model integration. The 13 delegated geometry items remain owned by the other session; its results are not claimed complete here.

Native captures cover all nine indoors/outdoors and the Paladin Boots' decorated front. Six existing logic tests passed 975 assertions. No build or release validation was performed.
