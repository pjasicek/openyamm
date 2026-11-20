# MM8 Bedraggled Human — m620

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m620_reduce_claude/`](../mm8_m620_reduce_claude/README.md) (LOD0 15,004 -> 9,000). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m620_reduce_claude/work/`.

The Bedraggled Human now has a separately modelled and textured head. The face retains its eyes, lips, stubble and weathered skin detail instead of the earlier blurred full-body face. The head is fitted to the existing civilian rig through a continuous neck mesh. Clothing, boots, cord positions, three vest palettes and all six civilian clips are retained. No attacks, casting or weapons were added.

[Interactive review](review/viewer/index.html) · [hair turnaround](review/hair_v3_turntable.png) · [head close-up](review/shots/hair_v3_front.png) · [profile](review/shots/hair_v3_left.png) · [half-speed playback](review/playback/0.5x_sheet.jpg).

## Delivered assets

- Full editable model: `export/mm8_m620.blend`; final runtime model: `export/mm8_m620.glb`.
- Independent editable head: `export/mm8_m620_head.blend`; portable head: `export/mm8_m620_head.glb`.
- Dedicated 2K head maps: `textures/bedraggled_head_basecolor_2k.png`, `bedraggled_head_normal_2k.png` and `bedraggled_head_metal_rough_2k.png`.
- Portable painted tiers: `review/viewer/mm8_bedraggled_{a,b,c}.glb`.
- Installed source: `assets_source/worlds/mm8/models/mm8_m620.glb`; cooked runtime: `assets_dev/worlds/mm8/models/mm8_m620.glb`.
- MM8 bindings: Bedraggled Human (peasant) A/B/C, merged monster ids 166/167/168, sprite groups m621/m622/m623 and palettes 621/622/623.
- 56 bones, up to eight normalized weights; colour and shadow LODs: **15,004 / 7,484 / 3,713 / 1,838 triangles**. One colour primitive per LOD.
- Standing 3 s; Walking 35/30 s; Fidget 3.2 s; Hit 0.5 s; Death 1.3 s; Dead 1/30 s. Dead holds the exact final Death pose. Native attack presentation slots retain their existing Walking reuse; gameplay tables and AI are unchanged.
- Native upright height 217.199457 game units; fitted Standing height 1.702266 m, scale 127.594280. Walking stride remains 1.915112 m.

The higher triangle and texture budgets are deliberate exceptions for the requested facial detail. The body retains its established 1K paint, stored at 2K height because the current material merger requires the body maps to be at least as tall as the head maps. The runtime uses 4128×2048 atlases, including a 32-pixel gutter. All three palettes share these maps; only the vest changes colour. LOD reductions remain approximately 50% each.

## Head revision

`meshy/head_geometry_v3` is the selected isolated-head return. Its source is `references_head/04_isolated_head.png`; the generation prompt, input and output hashes are recorded in `references_head/isolated_head_generation.json`. The earlier multi-view bust return (`head_geometry_v2`) incorrectly included a full body and was rejected. The original creature is preserved in `work/checkpoint_before_head_v2/`.

Facial geometry is protected during reduction. The initial scalp was too small, leaving holes among the hair strips. Revision `m620_solid_hair_v3` replaces it with a closed 1,248-triangle hair volume fitted to the existing strands. Its textured lower rim sits inside the head around the temples and nape. A nine-angle turnaround includes both sides, the back and a view from above. All retained geometry, UVs, weights and the six actions are checked against the previous head revision in `review/validation/hair_v3.json`. The neck joins the body at 53 shared vertices; the cranium is rigid on `B_Head`, while the neck blends into the existing body weights. The old neck's baked occlusion is cleared locally and its colour matched to the new head. Facial albedo is preserved.

Seventy-nine folded source UV triangles were translated into unused space without reducing the face charts. There are no unintended UV overlaps. The uniform-colour neck strip intentionally reuses 11 texels of its own chart; its normal map is flat. Material maps use zero metallic, restrained tangent-space normals and the current specular-mask-in-ORM-red contract.

Meshy spend is **80 of 100 credits**: original production 30, rejected multi-view head attempt 35, selected isolated head 15. No new animation was purchased.

## Original body and motion

The body follows the native m620 references: lean build, open ragged vest, bare torso, torn trousers and low boots. Five body and four head masters were generated from decoded originals; `generation_runs.json` and `source/native_inventory.json` retain their receipts. Motion comes from the user-selected [Male Peasant v2](../mm6_pman_claude_20261013/README.md), used read-only (source SHA-256 `bda8d983662e5d5a8326db85d22c69bc942a41a600d422761df1749f5455de82`).

The fitted source-frame rig retains measured wrists/ankles, connected finger weights, twist bones and garment weights copied from skin. Only the head/neck geometry, local neck shading, hair volume and related export data were revised here.

## Validation

- Focused native actor regression passes: all three palettes, native height, four LODs and the six civilian roles.
- Every half-frame of all six clips passes finite geometry, arm/hand deformation, floor contact and Death→Dead parity checks.
- The actual final GLB was reimported: 56 bones, normalized weights, at most eight influences, six clips and an exact held Death pose.
- Connected neck, rigid cranium and unchanged clothing/boot/cord positions are checked in `review/validation/head_v2.json`.
- Viewer: 18/18 palette/clip combinations, no browser errors. The revised hair was inspected from nine angles and during head turns, walking, hit and death poses. The earlier normal/half-speed recordings remain applicable to the unchanged six animation curves; geometry preservation is checked separately.
- Updated cooked model checked indoors and outdoors on NVIDIA/OpenGL, including front close-ups and forced outdoor LODs. Evidence is under `review/ingame/hair_v3/`; hashes are in `review/validation/installed.json`.
- The original broader MM8 run had 48 passes and unrelated Cleric/Dragon Turtle failures; that historical report remains in `review/validation/mm8_regression.log`. This head revision reran the focused m620 case, not that wider suite.

Native checks use isolated fixture maps to preload the m620 sprite groups; production maps are unchanged. The ordinary shared corpse sink remains expected behaviour. Android and Vulkan were not retested. The user accepted the separate head and corrected hair revision `m620_solid_hair_v3` on 2026-10-18: "ok accepted".

## Rebuild

Run `scripts/build_assets.py` through `tools/run_creature_blender.sh --token <lease>`. It uses the selected `work/rig_textured_uv.blend`, composes maps, exports, builds LODs, applies palettes, merges runtime materials and writes the separate head exports. Reinstall using `python3 tools/install_model.py level_generation/creatures/mm8_m620_claude/export/mm8_m620.glb --world mm8`.

To repeat the head fitting from retained inputs, run `fit_head_v2.py`, `repair_head_uv_v2.py`, `finish_head_join.py`, `repair_hair_volume.py`, then `build_assets.py`, each through the same Blender wrapper. Run `verify_head_v2.py` and `verify_hair_volume.py` afterward. The hair repair uses its retained pre-repair colour reference in `work/hair_reference.npz`. These steps do not call paid services.
