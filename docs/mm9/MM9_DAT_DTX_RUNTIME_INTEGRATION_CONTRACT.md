# MM9 DAT + DTX Runtime Integration Contract

This document is the implementation contract for MM9 DAT/DTX loading, generated sidecars, generated Lua, editor
inspection, and game runtime wiring in OpenYAMM.

The goal is lossless MM9 source preservation with an incremental runtime. Existing MM6-MM8 ODM/BLV behavior must remain
unchanged unless a loaded map explicitly declares MM9 DAT/event metadata.

Implementation sequence is editor-first. Shared DAT/DTX/source-resolution code may live under reusable engine/game
modules when it is runtime-neutral, but the editor must prove lossless loading, rendering, inspection, picking,
validation, and source-reference coverage before MM9 DAT maps become a playable game-world target. Game runtime wiring
should consume the same services after they are proven by editor tests, not grow a separate shortcut path.

## Authority And Scope

MM9 maps are LithTech DAT v66 worlds using DTX v2 textures. For MM9, the DAT world and DTX textures are source truth.
Generated ODM/BLV files are compatibility outputs and may remain useful for short-term rendering or tests, but they are
not the authoritative MM9 world representation.

Authority order:

1. Local extracted MM9 files under `mm9/extracted/` are byte-level truth.
2. OpenYAMM's locally verified parser behavior in `docs/mm9/MM9_DAT_FORMAT_NOTES.md` and
   `tools/mm9_import_discovery/` is the current parser truth.
3. `mm9/lithtech` is the primary semantic reference for LithTech world, DTX, world-model movement, collision, and
   texture flags.
4. `mm9/godot-dat-reader`, `mm9/DAT-Reader`, `mm9/DTX-Meta-Transfer`, `mm9/io_scene_lithtech`, `mm9/mm9_tools`,
   `mm9/nolf1-modernizer`, and `mm9/ltjs` are cross-check references only.

Do not copy code from local references. Use them to understand structure and behavior.

This document covers:

- DAT world source structure and runtime representation.
- DTX source texture handling and generated texture caches.
- Per-map sidecar YAML files.
- Generated per-map Lua and script IR.
- Editor/game load wiring.
- Validation rules that prevent silent data loss.

For the editor-specific document/view, inspector, asset-graph, and headless-test checklist, see
`docs/mm9/MM9_EDITOR_DAT_DTX_INTEGRATION_CHECKLIST.md`.

For LithTech lighting, shadows, DAT render-data research, and legacy `.ed` editor source handling, see
`docs/mm9/MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md`.

For DAT world physics, collision, movement, raycasts, contact reporting, and LithTech-compatible resolver semantics, see
`docs/mm9/MM9_DAT_PHYSICS_COLLISION_CONTRACT.md`.

This document does not cover full ABC/LTB model format details, actor combat AI, dialogue content, or complete MM9
quest implementation except where those systems intersect DAT objects and map events.

## Verified DAT Facts

The local MM9 corpus currently contains 45 extracted world DAT files under `mm9/extracted/WORLDS/WORLDS/*.dat`.

Confirmed parser facts:

- All 45 local DATs are little-endian DAT version `66`.
- The all-map scan parses successfully with OpenYAMM's MM9-adjusted v66 parser.
- Current corpus totals:
  - DAT files parsed: `45`
  - world models: `12671`
  - object instances: `32288`
  - user portals: `460`
  - decoded BSP leaf polygon references: `672656`
  - invalid decoded world-model references: `0`
  - invalid decoded polygon references: `0`
- MM9's `UserPortal` record layout differs from common public NOLF/LithTech v66 references. The locally verified
  layout omits the second `uint32` sometimes shown by public templates.
- `Surface.UseEffects` must be treated as enabled when greater than zero, not only when equal to one.
- Object payload boundaries are authoritative. Preserve declared property lengths, consumed lengths, raw bytes, and
  trailing bytes.

Top-level DAT layout:

```text
uint32 version                  // 66
uint32 object_data_pos
uint32 render_data_pos
uint32 dummy[8]
WorldInfo
WorldTree
WorldModelHeader
WorldModel[]
ObjectData at object_data_pos
```

WorldBSP layout used by the current parser:

```text
uint32 world_info_flags
uint32 unknown_value
LTString world_name

uint32 point_count
uint32 plane_count
uint32 surface_count
uint32 user_portal_count
uint32 poly_count
uint32 leaf_count
uint32 vert_count
uint32 total_vis_list_size
uint32 leaf_list_count
uint32 node_count

uint32 unknown_value_2
uint32 unknown_value_3

vec3 min_box
vec3 max_box
vec3 world_translation

uint32 texture_name_length
uint32 texture_count
null_string texture_names[texture_count]

poly_vertex_count_record poly_vertex_counts[poly_count]
Leaf leaves[leaf_count]
Plane planes[plane_count]
Surface surfaces[surface_count]
Poly polies[poly_count]
Node nodes[node_count]
UserPortal user_portals[user_portal_count]
Point points[point_count]       // MM9 v66 stores position plus normal
PBlockTable pblock_table
uint32 root_node_index
uint32 section_count
```

Lossless DAT loader requirements:

- Preserve every world model, including helper models named `PhysicsBSP`, `VisBSP`, sky models, water models,
  invisible brushes, AI/perception blockers, trigger volumes, and movable world models.
- Preserve every BSP surface, polygon, node, leaf, point, plane, user portal, PBlock table, root node, section count,
  texture name, effect string, and unknown field.
- Preserve every DAT object and every decoded/raw property.
- Preserve source indexes. Runtime/editor ids can be generated, but they must always refer back to source model,
  polygon, surface, object, and property indexes.

## LithTech Semantic References

The following `mm9/lithtech` files are the strongest semantic references:

- `runtime/world/src/de_world.h`
  - Surface flags: `SURF_SOLID`, `SURF_INVISIBLE`, `SURF_SKY`, `SURF_PORTAL`, `SURF_PHYSICSBLOCKER`,
    `SURF_VISBLOCKER`, `SURF_NOTASTEP`, etc.
  - `WIF_MOVEABLE` and `WIF_PHYSICSBSP` world-info flags.
  - `WorldBsp` and `WorldData` ownership model.
- `runtime/world/src/world_shared_bsp.cpp`
  - World load flow.
  - Movable world models load a second BSP for transformed runtime state.
- `runtime/world/src/de_mainworld.cpp`
  - `w_TransformWorldModel` transforms points, planes, and poly centers from original BSP to runtime BSP.
- `runtime/world/src/fullintersectline.cpp`
  - Intersection result surface flags come from texture/user flags.
- `runtime/shared/src/collision.cpp`, `moveplayer.cpp`, `moveobject.cpp`, and
  `runtime/world/src/intersectsweptsphere.cpp`
  - Cylinder, swept sphere, collision response, stair step, blocker, and moving-world-model behavior.
- `libs/dtxmgr/dtxmgr_lib.h` and `.cpp`
  - DTX v2 header, flags, sections, mipmaps, user flags, command string, and extra metadata.
- `tools/PreProcessor/Packer_PC/PCWorldPacker.cpp`
  - DAT version history. Version `66` added visibility and physics BSPs.

Important caveat: `mm9/lithtech` contains later/current LithTech code with DAT v85 packer paths. It explains semantics,
but MM9 DAT v66 remains locally verified by our parser and must win when byte layout differs.

## Surface Flags And Texture/User Flags

DAT `Surface.flags` and DTX `m_UserFlags` are separate source values.

DAT surface flags:

- Control render/collision/visibility properties of world polygons.
- Important bits include solid, invisible, sky, portal, physics blocker, visibility blocker, and not-a-step.
- Must be preserved per surface and copied into generated per-face metadata when producing ODM/BLV compatibility files.

DTX user flags:

- Stored in DTX v2 header as `m_UserFlags`.
- LithTech calls these "flags that go on surfaces."
- Runtime intersection code uses texture/user flags as reported surface flags for gameplay.
- OpenYAMM must preserve these as material metadata and make them available to footsteps, projectiles, damage, movement,
  and scripts later.

Do not collapse DAT surface flags and DTX user flags into one field. Both are source-authored data.

## DTX Contract

DTX source files should be retained as source assets. Generated PNG/BMP/KTX-like files are caches.

DTX v2 header contract from `dtxmgr_lib.h`:

```text
uint32 m_ResType
int32  m_Version              // -5 for DTX v2
uint16 m_BaseWidth
uint16 m_BaseHeight
uint16 m_nMipmaps
uint16 m_nSections
int32  m_IFlags
int32  m_UserFlags
uint8  m_Extra[12]
char   m_CommandString[128]
```

DTX flags to preserve:

- `DTX_FULLBRITE`
- `DTX_PREFER16BIT`
- `DTX_MIPSALLOCED`
- `DTX_SECTIONSFIXED`
- `DTX_NOSYSCACHE`
- `DTX_PREFER4444`
- `DTX_PREFER5551`
- `DTX_32BITSYSCOPY`
- `DTX_CUBEMAP`
- `DTX_BUMPMAP`
- `DTX_LUMBUMPMAP`

`m_Extra` semantics:

- `[0]`: texture group
- `[1]`: mipmaps to use
- `[2]`: BPP identifier
- `[3]`: non-S3TC mipmap offset
- `[4]`: UI/texture-coordinate mipmap offset
- `[5]`: texture priority
- `[6..9]`: detail texture scale as stored float offset
- `[10..11]`: detail texture angle

DTX loader requirements:

- Preserve the original DTX path, header, flags, user flags, extra fields, command string, mip count, section count,
  sections, and raw compressed payloads.
- Decode pixels for editor/game rendering through a cache layer.
- Do not make PNG/BMP the source format.
- Maintain map-local aliases for DAT texture references because DAT maps reuse short texture names and ODM face names
  are limited.
- Preserve detail texture and environment/bump/cubemap references from command strings and sections, even if not yet
  rendered.

Generated texture cache policy:

- Source: `assets_dev/worlds/mm9/textures/**/*.dtx` or packaged original DTX paths.
- Cache: generated images under map-local or shared generated folders.
- Metadata: `*.material_aliases.yml` records source DTX path and header metadata.
- Rebuild: cache is regenerated from DTX plus alias metadata. Cache edits are disposable.

## Coordinate And Unit Contract

Source DAT coordinates are LithTech/MM9 coordinates:

- `X/Z` horizontal.
- `Y` vertical.
- Source units are LithTech/MM9 world units.

OpenYAMM map content currently uses:

```text
source (x, y, z) -> openyamm (x, z, y)
scale = 2.56
```

Rules:

- Every sidecar that stores source coordinates must label them with `_lt` or equivalent source-unit metadata.
- Every sidecar that stores converted coordinates must include coordinate-system metadata and conversion scale.
- Runtime mechanisms should keep source values and compute converted runtime transforms from them.
- Do not bake open/closed mechanism states into static geometry.
- Do not guess speed/rate unit conversions. Preserve source units and add a documented conversion only after targeted
  calibration.

## Final Asset Set Per Map

Desired final per-map artifact set:

```text
assets_dev/worlds/mm9/maps/<map>.level.yml
assets_dev/worlds/mm9/maps/<map>.dat_world.yml
assets_dev/worlds/mm9/maps/<map>.raw_objects.yml
assets_dev/worlds/mm9/maps/<map>.material_aliases.yml
assets_dev/worlds/mm9/maps/<map>.events.yml
assets_dev/worlds/mm9/events/<map>.lua
assets_dev/worlds/mm9/events/<map>.script_ir.yml        // optional split if events.yml gets too large
assets_dev/worlds/mm9/events/<map>.mechanisms.lua       // optional split, only if useful
```

Existing compatibility artifacts can remain during migration:

```text
assets_dev/worlds/mm9/maps/<map>.scene.yml
assets_dev/worlds/mm9/maps/<map>.mm9.yml
assets_dev/worlds/mm9/maps/<map>.bsp.yml
assets_dev/worlds/mm9/maps/<map>.geometry.yml
assets_dev/worlds/mm9/maps/<map>.model_assets.yml
assets_dev/worlds/mm9/maps/<map>.odm
assets_dev/worlds/mm9/maps/<map>.blv
assets_dev/worlds/mm9/maps/<map>.source.glb
assets_dev/worlds/mm9/maps/<map>.bitmaps/*
```

Compatibility artifacts are derived products unless explicitly declared otherwise.

## Desired `assets_dev/worlds/mm9` Directory Tree

The MM9 world package should mirror the original REZ asset families enough that source provenance stays obvious, while
separating source-preserved assets from OpenYAMM-generated, OpenYAMM-authored, and compatibility files.

Original extracted REZ families currently observed under `mm9/extracted/`:

```text
ART/ART/
CLIENTFX/CLIENTFX/
DATA/DATA/
LOCALART/LOCALART/
MODELS/MODELS/
RUDE/RUDE/
SCRIPTS/SCRIPTS/
SKINS/SKINS/
SOUNDS/SOUNDS/
SPRITES/SPRITES/
SPRITETEXTURES/SPRITETEXTURES/
TEXTURES/TEXTURES/
VOICES/VOICES/
WORLDS/WORLDS/
```

Desired world package shape:

```text
assets_dev/worlds/mm9/
  world.yml

  source/
    manifest.yml
    art/
    clientfx/
    data/
    localart/
    models/
    rude/
    scripts/
    skins/
    sounds/
    sprites/
    sprite_textures/
    textures/
    voices/
    worlds/

  maps/
    mm9_map_import.yml
    <map>.level.yml
    <map>.dat_world.yml
    <map>.raw_objects.yml
    <map>.material_aliases.yml
    <map>.events.yml
    <map>.scene.yml                 # compatibility/derived during migration
    <map>.mm9.yml                   # compatibility/derived during migration
    <map>.bsp.yml                   # compatibility/derived during migration
    <map>.geometry.yml              # compatibility/derived during migration
    <map>.model_assets.yml          # compatibility/derived model-instance summary
    <map>.odm                       # compatibility/derived only
    <map>.blv                       # compatibility/derived only
    <map>.source.glb                # compatibility/editor geometry cache
    <map>.bitmaps/

  events/
    <map>.lua
    <map>.script_ir.yml
    <map>.mechanisms.lua            # optional split
    includes/
    common/

  textures/
    decoded/                        # shared generated texture cache
    material_registry.yml

  skins/
    decoded/                        # generated PNG/BMP/KTX-like cache
    skin_library.yml

  models/
    props/
    modelprops/
    pickupitems/
    pickups/
    player/
    projectiles/
    spells/
    weapons/
    gibs/
    <root-model>.glb
    <root-model>.model.yml
    <category>/.../<model>.glb
    <category>/.../<model>.model.yml
    registry.yml
    model_registry.yml              # current/generated compatibility name accepted during migration
    import/

  rendering/
    scripted_billboards/
    particles/
    sprites/

  audio/
    sounds/
    voices/
    music/
    sound_registry.yml

  data/
    tables/
    dialogue/
    npcs/
    rude/

  dialogue/
    npcs/
    dialogue_bindings.yml

  ui/
    art/
    localart/
    fonts/
    loading_screens/
    portraits/
    inventory_icons/
    hud/

  clientfx/
    converted/

  import/
    reports/
    validation/
    overrides/
```

Source-preserved folders:

- `source/*` is the immutable mirror of original extracted MM9 assets. Do not hand-edit files under this tree.
- `source/worlds/` mirrors `mm9/extracted/WORLDS/WORLDS/*.dat`.
- `source/textures/` mirrors `mm9/extracted/TEXTURES/TEXTURES/**/*.dtx`.
- `source/skins/` mirrors `mm9/extracted/SKINS/SKINS/**/*.dtx`.
- `source/models/` mirrors `mm9/extracted/MODELS/MODELS/**/*`.
- `source/scripts/` mirrors `mm9/extracted/SCRIPTS/SCRIPTS/*.scr` and `*.inc`.
- `source/rude/` mirrors `mm9/extracted/RUDE/RUDE/**/*`.
- `source/data/` mirrors `mm9/extracted/DATA/DATA/**/*`.
- `source/sounds/` mirrors `mm9/extracted/SOUNDS/SOUNDS/**/*`.
- `source/voices/` mirrors `mm9/extracted/VOICES/VOICES/**/*`.
- `source/sprites/` mirrors `mm9/extracted/SPRITES/SPRITES/**/*`.
- `source/sprite_textures/` mirrors `mm9/extracted/SPRITETEXTURES/SPRITETEXTURES/**/*`.
- `source/art/` and `source/localart/` mirror UI/HUD/loading/portrait/icon art from `ART` and `LOCALART`.
- `source/clientfx/` mirrors `mm9/extracted/CLIENTFX/CLIENTFX/**/*`.

OpenYAMM-authored and generated folders outside `source/`:

- Everything outside `source/` is either OpenYAMM-authored metadata, deterministic generated metadata/cache, or a
  temporary compatibility artifact.
- Runtime and editor entrypoints live under `maps/`. A native MM9 map opens through `maps/<map>.level.yml`, which
  references the original DAT under `source/worlds/`, original DTX textures under `source/textures/` and
  `source/skins/`, original models under `source/models/`, and OpenYAMM sidecars under `maps/` and `events/`.
- Original DTX, ABC/LTB, SCR/INC, RUDE, DAT, sound, sprite, and art files should not be duplicated into top-level
  `textures/`, `models/`, `data/`, or `clientfx/` source subfolders. Those top-level folders are for decoded caches,
  converted runtime assets, registries, bindings, and authored OpenYAMM data.

Generated-cache folders:

- `maps/*.dat_world.yml`, `maps/*.raw_objects.yml`, `maps/*.material_aliases.yml`, and `maps/*.events.yml` are
  generated source indexes. They are deterministic and rebuildable, but they are not disposable because they are the
  human-reviewable contract for runtime/editor work.
- `maps/*.odm`, `maps/*.blv`, `maps/*.scene.yml`, `maps/*.mm9.yml`, `maps/*.bsp.yml`, `maps/*.geometry.yml`,
  `maps/*.source.glb`, and `maps/*.bitmaps/` are migration compatibility products.
- `textures/decoded/`, generated PNG skin previews under `skins_preview/`, generated GLBs under `models/**`, and
  billboard frames under `rendering/scripted_billboards/` are generated caches.
- `skins/**/*.dtx` holds runtime DTX skin copies; PNG previews are caches, not source truth.
- `import/reports/` and `import/validation/` hold deterministic reports and validation output.
- `import/overrides/` holds explicit manual import/binding overrides. Overrides are source-authored OpenYAMM data and
  are not disposable.

Current generated assets already use some of these names directly and some transitional names:

- `assets_dev/worlds/mm9/maps/*.events.yml` already exists.
- `assets_dev/worlds/mm9/events/*.lua` already exists.
- `assets_dev/worlds/mm9/maps/*.material_aliases.yml` already exists.
- `assets_dev/worlds/mm9/maps/*.raw_objects.yml` already exists.
- `assets_dev/worlds/mm9/models/model_registry.yml` already exists and can remain as the compatibility registry name
  until renamed or aliased to `models/registry.yml`.
- `assets_dev/worlds/mm9/scripts/*.lua` currently contains generated/transcoded script-like Lua files. Long term,
  executable per-map event Lua should live under `events/`, while `source/scripts/` preserves original `.scr`/`.inc`
  and generated script caches are clearly marked.

Packaging rule:

- Runtime packages may omit original extracted REZ paths only if the packaged DAT/DTX/model/script source payloads and
  sidecar indexes remain lossless and reproducible.
- Development assets should keep original source assets or exact source-preserving copies available under
  `assets_dev/worlds/mm9/source/`.
- Generated caches can be regenerated and should never be the only copy of source data.

## Map Entry Point: `<map>.level.yml`

`<map>.level.yml` should be the MM9 map's editor/game entry point. It replaces ambiguity about whether a map should be
opened as ODM, BLV, scene, or DAT.

Required fields:

```yaml
format_version: 1
kind: mm9_level
map_id: thjorgardcity
display_name: Thjorgard City

source:
  dat: mm9/extracted/WORLDS/WORLDS/THJORGARDCITY.dat
  source_game: mm9
  dat_version: 66
  content_hash: "<sha256>"

runtime:
  world_backend: dat_world
  classification: dat_bsp_portal_like
  visibility: dat_bsp_portal
  collision: dat_physics_bsp
  render: dat_render_world
  sky: true

sidecars:
  dat_world: thjorgardcity.dat_world.yml
  raw_objects: thjorgardcity.raw_objects.yml
  materials: thjorgardcity.material_aliases.yml
  events: thjorgardcity.events.yml
  scene_compat: thjorgardcity.scene.yml
  source_metadata_compat: thjorgardcity.mm9.yml

scripts:
  level: ../events/thjorgardcity.lua
  script_ir: ../events/thjorgardcity.script_ir.yml

generated:
  tool: tools/mm9_import_discovery/generate_mm9_maps_from_manifest.py
  generated_at: "<deterministic-or-omitted>"
```

Runtime classification values:

- `outdoor_like`
- `dat_bsp_portal_like`
- `dat_bsp_like`
- `indoor_like`
- `needs_review`

This classification is MM9 metadata only. It must not change MM6-MM8 ODM/BLV behavior.

## DAT World Sidecar: `<map>.dat_world.yml`

Purpose: compact, deterministic index over the DAT world for editor/game inspection and validation. It does not need
to duplicate all vertex arrays if the runtime loads the DAT directly, but it must preserve stable source ids, checksums,
counts, flags, names, and runtime classification.

Required top-level shape:

```yaml
format_version: 1
kind: mm9_dat_world
map_id: thjorgardcity
source_dat: mm9/extracted/WORLDS/WORLDS/THJORGARDCITY.dat
source_hash: "<sha256>"
dat_version: 66

coordinate_system:
  source: lithtech_mm9
  openyamm_mapping: [x, z, y]
  scale: 2.56

world_info:
  property_string: "..."
  light_map_grid_size: 0.0
  extents_min_lt: [0.0, 0.0, 0.0]
  extents_max_lt: [0.0, 0.0, 0.0]

classification:
  recommendation: dat_bsp_portal_like
  confidence: high
  reason: has named UserPortal records plus dense VisBSP leaves

world_models:
  - source_model_index: 0
    source_name: Terrain0
    world_info_flags: 0
    kind: visible_geometry
    point_count: 0
    plane_count: 0
    surface_count: 0
    poly_count: 0
    leaf_count: 0
    node_count: 0
    user_portal_count: 0
    pblock_table:
      preserved: true
      record_count: 0
    bounds_lt:
      min: [0.0, 0.0, 0.0]
      max: [0.0, 0.0, 0.0]
    world_translation_lt: [0.0, 0.0, 0.0]
    textures:
      - texture_index: 0
        source_texture: TEXTURES\\LevelTextures\\Terrain\\c_grass.dtx
    surface_flag_histogram: {}
    texture_user_flag_histogram: {}
    roles:
      visible: true
      physics_bsp: false
      vis_bsp: false
      sky: false
      water: false
      trigger_or_volume: false
      movable: false

user_portals:
  - source_model_index: 0
    portal_index: 0
    name: Portal0
    center_lt: [0.0, 0.0, 0.0]
    dims_lt: [0.0, 0.0, 0.0]
    raw_unknowns:
      unknown_int_1: 0
      unknown_short: 0

leaf_references:
  decode: world_model_index_low16_poly_index_high16
  total_refs: 0
  invalid_refs: 0

validation:
  parse_status: ok
  unknown_field_policy: preserved
```

Runtime use:

- Editor uses this for tree views, source indexes, BSP/portal overlays, helper model filters, and diagnostics.
- Game uses this for map classification, source ids, and prevalidated topology metadata.
- DAT loader still reads the original DAT or packed DAT-derived binary data for actual geometry arrays.

## Raw Object Sidecar: `<map>.raw_objects.yml`

Purpose: lossless DAT object/property preservation. This file already exists and remains source/debug truth.

Required contract:

```yaml
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/THJORGARD.dat
object_count: 704
unknown_property_count: 0
objects:
  - object_index: 1
    name: ShopkeeperHumanMaleA
    property_count: 68
    data_length: 1692
    trailing_hex: ""
    properties:
      - name: ScriptName
        code: 0
        flags: 16384
        declared_data_length: 16
        consumed_data_length: 16
        decoded: true
        raw_hex: "..."
        value_json: "\"shopkeeper.scr\""
```

Rules:

- Preserve every object, not only mechanisms.
- Preserve every property in source order.
- Preserve raw bytes and declared/consumed lengths.
- Preserve object trailing bytes.
- Do not hand-edit this file for behavior fixes. Fix the parser/generator.

## Material Sidecar: `<map>.material_aliases.yml`

Purpose: DAT texture reference, DTX metadata, generated cache, and ODM/BLV compatibility alias mapping.

Required fields per texture:

```yaml
format_version: 1
kind: mm9_material_aliases
source_dat: mm9/extracted/WORLDS/WORLDS/THJORGARD.dat

textures:
  - alias: CGRASS
    source_texture: TEXTURES\\LevelTextures\\Terrain\\c_grass.dtx
    physical_path: mm9/extracted/TEXTURES/TEXTURES/LEVELTEXTURES/TERRAIN/C_GRASS.dtx
    width: 128
    height: 128
    emitted_bitmap: thjorgard.bitmaps/CGRASS.bmp
    emitted_bitmap_mode: dxt1

    dtx:
      version: -5
      res_type: 0
      flags: 8
      user_flags: 14
      texture_group: 0
      bpp: 4
      mipmap_count: 4
      mipmaps_used: 4
      section_count: 0
      non_s3tc_mipmap_offset: 0
      ui_mipmap_offset: 0
      texture_priority: 0
      detail_scale: 5.0
      detail_angle: 0
      command_string: "DetailTex Textures\\detailtextures\\det_04.dtx"
      sections: []
```

Compatibility with current generated files:

- Existing flat fields such as `dtx_surface_flag`, `dtx_texture_group`, `dtx_bpp`, `dtx_flags`, and
  `dtx_command_string` are accepted.
- New code should prefer the nested `dtx` form for clarity.
- `dtx_surface_flag` should be renamed semantically to `dtx.user_flags`, while preserving the old field during
  migration.

Rules:

- Preserve DTX metadata even when a generated image cache exists.
- Missing texture sources must produce explicit placeholders and diagnostics.
- Generated bitmap aliases are not source truth.

## Events Sidecar: `<map>.events.yml`

Purpose: normalized MM9 map behavior graph. This includes mechanisms, trigger volumes, general interactions, script
bindings, message edges, runtime target bindings, and unresolved diagnostics.

This file does not replace `raw_objects.yml`. It indexes and normalizes it.

Required top-level shape:

```yaml
format_version: 1
kind: mm9_events
map_id: thjorgard
source_dat: mm9/extracted/WORLDS/WORLDS/THJORGARD.dat
source_raw_objects: thjorgard.raw_objects.yml

coordinate_system:
  source: lithtech_mm9
  openyamm_mapping: [x, z, y]
  scale: 2.56

generated:
  tool: tools/mm9_import_discovery/generate_mm9_events.py
  lua: ../events/thjorgard.lua
  script_ir: ../events/thjorgard.script_ir.yml

objects: []
mechanisms: []
triggers: []
interactions: []
bindings: []
scripts: []
unresolved: []
validation: {}
```

Object entry:

```yaml
objects:
  - object_id: mm9:thjorgard:object:123
    source_object_index: 123
    source_class: RotatingDoor
    source_name: DoorA
    classifications: [mechanism, interaction]
    raw_object_ref: thjorgard.raw_objects.yml#objects[123]
    raw_property_count: 42
    raw_properties:
      - property_index: 0
        name: Name
        decoded: true
        code: 0
        flags: 0
        raw_ref: properties[0]
    normalized_properties:
      Name: DoorA
      Pos: [0.0, 0.0, 0.0]
      ScriptName: DoorLock.scr
      ScriptParams: "..."
```

Mechanism entry:

```yaml
mechanisms:
  - mechanism_id: mm9:thjorgard:object:123:mechanism
    object_id: mm9:thjorgard:object:123
    source_object_index: 123
    source_class: RotatingDoor
    source_name: DoorA
    mechanism:
      kind: rotating_door
      source_units: lithtech_mm9
      linear:
        move_dir_lt: [0.0, 0.0, 0.0]
        move_dist_lt: 0.0
        speed_lt: 0.0
        closing_speed_lt: 0.0
      rotation:
        rotation_point_lt: [0.0, 0.0, 0.0]
        rotation_angles_raw: [0.0, 90.0, 0.0]
        open_away: false
      timing:
        move_delay_raw: 0.0
        open_wait_time_raw: 0.0
    activation:
      start_open: false
      start_on: true
      locked: false
      push_open: false
      touch_to_open: false
      auto_trigger: false
      reopen_on_contact: false
      double_door_name: ""
    trigger_outputs:
      - phase: open
        slot: 0
        target_name: OtherDoor
        message_name: Open
        resolution: resolved
```

Trigger volume entry:

```yaml
triggers:
  - trigger_id: mm9:thjorgard:object:10:trigger
    object_id: mm9:thjorgard:object:10
    source_object_index: 10
    source_name: RobPlayerTrigger
    pos_lt: [0.0, 0.0, 0.0]
    dims_lt: [64.0, 64.0, 64.0]
    start_on: true
    outputs:
      - phase: trigger
        slot: 1
        target_name: Ken1
        message_name: RobPlayer
        resolution: resolved
```

Interaction entry:

```yaml
interactions:
  - interaction_id: mm9:thjorgard:object:1:interaction
    object_id: mm9:thjorgard:object:1
    source_object_index: 1
    source_class: ShopkeeperHumanMaleA
    source_name: JohnGoodman
    activation:
      use: true
      touch: false
    script_id: shopkeeper.scr
    sends: []
```

Binding entry:

```yaml
bindings:
  - object_id: mm9:thjorgard:object:123
    source_object_index: 123
    targets:
      - target_kind: dat_world_model
        target_id: dat:model:52
        confidence: exact_source_object_index
        source_model_index: 52
        source_model_name: DoorA
      - target_kind: model_instance
        target_id: mm9:thjorgard:object:123
        confidence: exact_source_object_index
```

Required target kinds:

- `dat_world_model`
- `dat_face_group`
- `dat_poly_group`
- `model_instance`
- `trigger_volume`
- `collision_volume`
- `water_volume`
- `ladder_volume`
- `script_object`
- `odm_bmodel` for compatibility output
- `blv_face_group` for compatibility output
- `unresolved`

Rules:

- Every object appears in `objects`.
- Every mechanism-relevant object appears in `mechanisms`.
- Every trigger/volume object appears in `triggers` or a volume target binding.
- General use/touch/dialogue/script interactions appear in `interactions`, not only moving doors.
- Every raw property remains recoverable through `raw_object_ref` and `raw_properties`.
- Ordered trigger slots remain ordered.
- Unresolved targets and missing scripts are explicit diagnostics.
- The generator must never silently drop movement values, sounds, flags, lock state, trigger delays, or script params.

## Script IR And Lua

MM9 source scripts are `.scr` and `.inc` files under `mm9/extracted/SCRIPTS/SCRIPTS/`. They are source references, not
the runtime language we should execute directly.

OpenYAMM should generate:

```text
assets_dev/worlds/mm9/events/<map>.script_ir.yml
assets_dev/worlds/mm9/events/<map>.lua
assets_dev/worlds/mm9/events/<map>.mechanisms.lua   // optional
```

`script_ir.yml` is the lossless parsed script representation. It may be embedded inside `events.yml` while small, but a
split file is cleaner long term.

Required script IR fields:

```yaml
format_version: 1
kind: mm9_script_ir
map_id: thjorgard
scripts:
  - script_id: racingboat.scr
    source_path: RACINGBOAT.scr
    parse_status: parsed_with_unknowns
    includes:
      - line: 5
        path: BaseGlobals.inc
    labels:
      - line: 48
        name: TurnOn
    registered_triggers:
      - line: 48
        message: on
        callback: TurnOn
        arguments_raw: "on, TurnOn"
    trigger_edges:
      - line: 100
        target_expr_raw: hTarget
        message_expr_raw: Done
        resolution: dynamic
    commands:
      - line: 120
        command: MoveDir
        arguments_raw: "dx,0,dz, nDist, nSpeed, StartMoveLoop"
        kind: movement
    unknown_commands:
      - line: 41
        command: GetRandomInt
        arguments_raw: "1, 40 nRandom"
        raw: "..."
```

Generated Lua contract:

- Generated Lua is executable output, not source truth.
- Generated Lua must be marked generated and not hand-edited.
- Generated Lua registers message handlers from `AddTrigger`.
- Generated Lua calls engine APIs for movement, flags, stats, animations, model swaps, item checks, quest/dialogue
  hooks, and message dispatch.
- Unsupported commands log diagnostics with script id and line.

Minimum MM9 Lua API:

```lua
mm9.Trigger(targetName, messageName)
mm9.GetObject(objectName)
mm9.GetPos(objectRef)
mm9.SetPos(objectRef, x, y, z)
mm9.MoveToPos(objectRef, x, y, z, rate, callback)
mm9.MoveDir(objectRef, x, y, z, dist, rate, callback)
mm9.Rotate(objectRef, xAxis, yAxis, zAxis, degrees, rate, callback)
mm9.SetFlag(objectRef, flagName)
mm9.ClearFlag(objectRef, flagName)
mm9.GetStat(objectRef, statName)
mm9.SetStat(objectRef, statName, value)
mm9.PlayAnim(objectRef, animName, callback)
mm9.LoopAnim(objectRef, animName, count, callback)
mm9.SetModelFilenames(objectRef, modelName, skinName)
mm9.DestroyObject(objectRef)
```

## Model And Billboard Assets

DAT world geometry is separate from model instances. Non-DAT objects use LithTech model assets.

Policy:

- ABC/LTB/source model assets remain source references.
- Generated GLB is a runtime/editor cache.
- Actor animated billboards can be generated from actor models and animations as YAML plus PNG/BMP frame caches.
- Generated billboard frames are acceptable runtime assets, but the source mapping must retain model, skin, animation,
  frame, direction, and generation parameters.
- Static props may use generated GLB caches for performance and tooling, while preserving source model/skin refs.

This does not change DAT world geometry source truth.

## Runtime Loading Wiring

MM9 map load flow:

```text
world.yml / map navigation
  -> <map>.level.yml
      -> DAT world source or packaged DAT-derived runtime binary
      -> <map>.dat_world.yml
      -> <map>.material_aliases.yml
      -> DTX source + generated texture cache
      -> <map>.raw_objects.yml
      -> <map>.events.yml
      -> generated Lua / script IR
```

Runtime objects created:

- `DatLevelRuntime`
  - Owns DAT world models, static geometry, helper BSPs, visibility, collision, picking, sky, and material bindings.
- `Mm9EventRuntime`
  - Owns source object registry, message dispatch, mechanisms, trigger volumes, interactions, generated Lua, timers,
    and save/load state.
- `Mm9MaterialRuntime`
  - Owns DTX metadata, decoded texture cache handles, user flags, detail/effect references, and surface material data.

The long-term frontend class can be named `DatLevelView` or equivalent. It should replace the MM9 need to decide
between `OutdoorView` and `IndoorView`, while reusing shared rendering, collision, input, events, audio, and gameplay
systems.

MM6-MM8 guardrails:

- Do not alter normal ODM/BLV loading for maps without `kind: mm9_level` or `kind: mm9_events`.
- Do not route MM6-MM8 EVT face events through the MM9 message registry.
- Do not reinterpret legacy DLV/ODM/BLV saves as MM9 mechanism state.
- New MM9 save chunks must be namespaced and optional.

## Rendering Wiring

Rendering should use DAT source structures directly for MM9:

- Visible world models render as static or movable DAT geometry.
- Helper models such as `PhysicsBSP` and `VisBSP` are not rendered as ordinary visible art.
- `SURF_INVISIBLE`, sky, hull, occluder, AI, sound, rain, ladder, water, and volume textures need semantic filtering.
- Sky-capable DAT maps can render sky even when structurally portalized or BLV-like.
- DTX metadata controls material behavior. Fullbright, alpha, detail textures, bump/cubemap/effect command strings, and
  user flags must remain available even before all are visually implemented.

Performance approach:

- Static world geometry goes into static render buffers and static spatial structures.
- Movable world models and mechanisms use dynamic transform proxies from rest geometry.
- Do not rewrite/restream whole-map geometry per frame.
- Update only dirty dynamic proxy bounds and transforms.
- Visibility should use source DAT BSP/portal data where available; outdoor-like maps can use coarser spatial culling
  until the portal path is implemented.

## Collision And Picking Wiring

Collision source hierarchy:

- `PhysicsBSP` and `SURF_PHYSICSBLOCKER` are primary static collision hints.
- Visible world surfaces with solid/source flags participate when appropriate.
- `SURF_NOTASTEP` affects step-up behavior.
- Moving world models need dynamic collision proxies based on transformed original BSP data.
- Trigger, water, ladder, AI, perception, and invisible brush volumes are runtime volumes, not visible meshes.

Picking/use:

- Raycasts return DAT source model/poly/surface ids plus DTX user flags.
- MM9 interactions resolve from picked target binding to `events.yml` object/message behavior.
- Converted face/bmodel ids are compatibility bindings only.

## Mechanism Runtime Wiring

Mechanisms are source objects with bound runtime targets.

Built-in mechanisms should support, in order:

1. Named message dispatch.
2. Trigger volume touch/use dispatch.
3. Linear `Door` and `WeightedLift`.
4. `RotatingDoor`.
5. Script `MoveToPos`, `MoveDir`, `Rotate`, and `SetPos`.
6. Visibility, solidity, rayhit, and object flag changes.
7. Continuous `RotatingBrush`.
8. Model animation and model/skin swap.
9. Water/ladders/dynamic volumes.
10. Destructibles, shooters, traps, AI barriers, and perception volumes.

Mechanism state to save:

- enabled/on state
- open/closed/toggle state
- current movement progress
- current transform
- locked state
- visible/solid/rayhit flags
- current model/skin
- current animation
- destroyed/removed state
- active timers
- script-local state required by generated Lua

## Editor Wiring

The editor should open `<map>.level.yml` for MM9.

Required editor views:

- DAT world model tree with source indexes, names, flags, counts, bounds, and roles.
- Surface/poly inspector showing DAT surface flags and DTX user flags.
- Texture inspector showing DTX header, command string, sections, decoded cache status, and source path.
- Portal/leaf/BSP overlays for portalized maps.
- Helper model filter toggles: visible art, PhysicsBSP, VisBSP, sky, water, ladder, trigger, AI/perception, invisible.
- Raw object tree from `raw_objects.yml`.
- Event graph from `events.yml`, including objects, mechanisms, triggers, interactions, bindings, and unresolved refs.
- Script IR viewer with source file, line, triggers, movement commands, unknown commands, and generated Lua link.
- Mechanism preview using runtime mechanism code, not a duplicated editor implementation.

Editor save rules:

- Do not edit generated `raw_objects.yml`, `dat_world.yml`, or generated Lua directly.
- Future authored overrides must live in explicit override sidecars, for example `<map>.events.overrides.yml`.
- Manual binding fixes should be data, not code special cases.

## Validation Contract

Validation must distinguish data loss from unimplemented behavior.

Data loss is a failure:

- DAT parse fails.
- Any DAT world model/surface/poly/leaf/node/portal/object/property disappears from source indexes.
- Raw object property bytes are not recoverable.
- DTX header, flags, user flags, command string, sections, or source path are lost.
- Script source lines or unknown commands are dropped.
- Trigger target/message slots are reordered or dropped.
- Bindings reference missing runtime targets without diagnostics.

Unimplemented behavior is allowed only with explicit diagnostics:

- Unknown script command.
- Unresolved dynamic target expression.
- Mechanism class not yet executable.
- DTX feature not yet rendered.
- Portal/visibility path not yet used by runtime.
- Collision feature not yet implemented.

Required validation commands:

```bash
python3 tools/mm9_import_discovery/test_dat_bsp_parser.py
python3 tools/mm9_import_discovery/generate_mm9_events.py --validate-only
python3 tools/mm9_import_discovery/classify_mm9_maps.py
```

Desired new validation command:

```bash
python3 tools/mm9_import_discovery/validate_mm9_dat_dtx_contract.py
```

It should check:

- all 45 DATs parse;
- all sidecars exist for every manifest map;
- `raw_objects.yml` object counts match DAT object counts;
- `events.yml` object indexes match `raw_objects.yml`;
- material aliases resolve DTX files or explicit placeholders;
- DTX metadata matches source files;
- DAT world counts match `dat_world.yml`;
- event bindings reference valid DAT models/polys, model instances, volumes, ODM bmodels, or BLV face groups;
- generated Lua/script IR cover all referenced scripts;
- unresolved diagnostics are deterministic.

## Implementation Order

1. Add `<map>.level.yml` and `<map>.dat_world.yml` generation.
2. Promote DTX parsing to a complete source metadata parser using the `dtxmgr_lib.h` contract.
3. Update material aliases to preserve nested DTX metadata while keeping current flat fields during migration.
4. Add DAT-native editor loader and inspector using DAT plus sidecars.
5. Add DAT-native game loader behind `kind: mm9_level`.
6. Implement DAT static rendering with DTX cache materials.
7. Implement DAT static collision and picking.
8. Wire `events.yml` and generated Lua into `Mm9EventRuntime`.
9. Implement playable mechanism slice: triggers, doors, rotating doors, and collision updates.
10. Expand script command support and dynamic volumes.
11. Keep ODM/BLV compatibility import only as derived fallback/testing output.

## Existing Documents This Supersedes Or Narrows

- `MM9_DAT_FORMAT_NOTES.md` remains the byte-layout notes document.
- `MM9_LOSSLESS_MECHANISM_INTEGRATION.md` remains the mechanism investigation.
- `MM9_EVENTS_IMPLEMENTATION_GOAL.md` remains the event sidecar implementation goal.
- `MM9_RUNTIME_EVENTS_PLAYABLE_SLICE_CHECKLIST.md` remains the short playable slice.
- This document is the broader DAT+DTX runtime/editor wiring contract and should be the entry point for new MM9 DAT
  world implementation work.

## Non-Negotiable Rules

- Source DAT and DTX data must be preserved losslessly.
- MM9 event behavior is source object/message/script based, not legacy EVT id based.
- Generated compatibility ODM/BLV files must not become source truth for MM9.
- Generated texture images must not become source truth for DTX.
- Unknown fields are preserved and diagnosed, not guessed away.
- MM6-MM8 default runtime behavior must remain unchanged.
