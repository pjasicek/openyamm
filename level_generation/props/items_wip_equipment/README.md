# Equipment ground items — coordinator finish complete

The resumed nine-item texture/bake scope is complete. All nine replacements are installed and reviewed indoors and outdoors. Their collision/picking bounds, together with the previous accepted models, are merged into `assets_dev/engine/world_items/items.yml`. The later user size correction below changes only two binding lengths and their bounds.

## Boot size correction — 2026-10-18

Paladin Boots (`7item119`) were 95.8 units tall and Seven League Boots (`7item312`) were 84.4, visibly oversized beside the other tall boots. Uniformly reduced Paladin's binding length from 69.3 to 45 (35.1% smaller), and Seven League from 77 to 52 (32.5% smaller). Their new heights are 62.2 and 57 units; foot depths now match neighbouring boots. Collision/picking bounds were recomputed from the runtime GLBs at the corrected scale. Models and textures are unchanged. Current design, ledger and handoff lengths match the installed bindings.

Native comparison: [before](review/boot_scale_20261018/before/01-boots_row.png), [after](review/boot_scale_20261018/after/01-boots_row.png), and [validation](review/boot_scale_20261018/validation.json). Both views use the same save and camera; a second oblique view checks the feet and ground placement.

| Current assignment result | Icons |
| --- | ---: |
| Accepted and installed by this session | 64 |
| Concurrent amulets/gauntlets installations preserved | 18 |
| Geometry repairs delegated to the other session | 13 |
| Total examined | 95 |

[Per-icon ledger](ledger.csv), [structured handoff](handoff.json), and [remaining ownership split](remaining_split.json) are authoritative. The six original KEEP designs are outside this assignment and remain untouched.

## Nine repairs finished

Sun Cloak `7item347`, Archangel Wings `item260`, Defender Helm `6helm4`, Angelic Helm `6helm5`, Noble Crown `7item098`, Phynaxian Crown `7item241`, Lucky Hat `item115`, Drogg's Helm `item256`, and Paladin Boots `7item119`.

Open the [nine-item accepted gallery](review/texture_finish_accepted_9.png), [export validation](review/texture_finish_validation.json), [native capture records](review/texture_finish_native.json), and [applied bounds report](review/bounds_merge_applied.json). All 64 installed coordinator models currently match their runtime bounds. Each replacement was installed individually through the normal per-model installer.

The baker now restricts texel samples to actual UV triangles and supports reviewed material classes from mesh faces. The exact rendered material masks remain visual evidence. Lucky Hat's three misregistered views were repainted separately, preserving the two valid original views. Two reversed boot panels were corrected; Paladin Boots retain their front gold scrollwork, metal exterior and separate leather lining. Adding thickness after the exterior bake preserves the boot and Sun Cloak UVs. Defender Helm's ivory forehead stone has a separate dielectric material and a preserved finished author scene.

## Validation and provenance

- Nine final exports passed finite attribute, normalized normal, UV, embedded PBR map, triangle budget and winding checks; five angles were reviewed with explicit back-face culling.
- All nine were inspected in native MM7 outdoor and MM6 indoor captures on NVIDIA/OpenGL. Paladin Boots also have a separate decorated-front capture. Native runs completed without game errors; these are visual checks, not performance measurements.
- Five focused Blender material/bake/lining/triangle-domain regressions passed. Six existing item binding/collision/picking test cases passed, with 975 assertions.
- 83 historical Meshy jobs succeeded for exactly 415 approved credits. This finish used no new Meshy jobs or credits.
- 219 original generated image outputs are retained with hashes and provenance in the [image receipt index](review/atlas_receipt_index.json). Paintings, masks, .blend author scenes, exports, source baselines and review evidence remain in this WIP project.

## Other session

The [geometry handoff](../items_claude/parallel_20261018/07_equipment_geometry_finish.txt) owns exactly 13 icons in `items_wip_equipment_geometry_finish`. That worker owns its models, scenes, receipts and ledger. This session did not repair or install those icons. Its handoff remains to be integrated when ready. The 18 concurrent gauntlet installations were hash-verified and preserved.

No engine changes, full build, Vulkan build, global model cook, staging, commits or release promotion were performed. This subtree remains WIP and excluded from release packages. The scoped reusable Blender wrapper approval remains available.
