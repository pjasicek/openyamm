# MM9 DAT Format Notes

These notes document what OpenYAMM has verified about Might and Magic IX world DAT files. Treat this document as the
working contract for MM9 DAT import work until a more formal parser specification replaces it.

For the broader runtime/editor asset contract, sidecar layout, DTX handling, and generated Lua wiring, see
`docs/mm9/MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md`.

For current findings about LithTech lighting, shadows, compiled render data, and legacy `.ed` editor source files, see
`docs/mm9/MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md`.

For LithTech-derived DAT world runtime, rendering, collision, mechanism, and performance findings, see
`docs/mm9/MM9_DAT_WORLD_RUNTIME_LITHTECH_FINDINGS.md`.

## Scope

- Applies to extracted MM9 world files from `WORLDS.REZ`, currently observed under
  `mm9/extracted/WORLDS/WORLDS/*.dat`.
- Covers DAT world/BSP parsing, not ABC/LTB model parsing, DTX texture decoding, script behavior, or MM9 gameplay
  object semantics.
- Covers only the verified structural DAT layout. Lighting/render-data semantics are tracked separately in
  `MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md`.
- The current import tools are in `tools/mm9_import_discovery/`.

## Confirmed Local Facts

- All 45 extracted MM9 world DAT files checked in the local workspace start with little-endian `uint32_t` version `66`.
- The local set parses with the MM9-adjusted v66 world/BSP parser after the `UserPortal` layout correction described
  below.
- Full-world scan result after the correction:
  - DAT files parsed: `45`
  - parse failures: `0`
  - world models: `12671`
  - object instances parsed: `32288`
  - user portals parsed: `460`
  - BSP leaf polygon references decoded: `672656`
  - invalid decoded world-model references: `0`
  - invalid decoded polygon references: `0`
- All currently observed object property codes decode with the MM9 object parser once object record boundaries are
  handled correctly.

## External And Local References

- `mm9/godot-dat-reader/Models/DAT.gd`
  - Lists `DAT_VERSION_NOLF = 66`.
  - Treats version 66 as the LithTech 2.x path.
  - Reads world header, world info, world tree, world models, BSP counts, leaves, planes, surfaces, polygons, nodes,
    user portals, points, PBlock table, root node, and section count in the same broad order OpenYAMM uses.
- `mm9/godot-dat-reader/Research/bspv66.bt`
  - 010 Editor template for NOLF/LithTech v66.
  - Matches MM9's broad BSP layout for header, counts, leaves, planes, surfaces, polygons, nodes, points, PBlock table,
    root node, and section count.
  - Does not exactly match MM9's `UserPortal` record layout.
- `mm9/DTX-Meta-Transfer/README.md`
  - Lists Might and Magic IX as LithTech 1.5 with `DAT v66` and `DTX v2`, with levels/textures packed as LithTech 2.x
    resources.
- `mm9/ltjs`
  - LTJS is LithTech Jupiter, not MM9's branch. Use it for architectural context only, not as an exact MM9 DAT binary
    authority.

## Header And Top-Level Layout

MM9 DAT files use this observed top-level order:

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

`WorldInfo` is:

```text
uint32 property_string_length
char[property_string_length] property_string
float light_map_grid_size
vec3 extents_min
vec3 extents_max
```

The world tree is currently consumed structurally, not converted into runtime data.

## World Model And BSP Layout

Each world model starts with:

```text
uint32 next_world_model_pos
byte[32] model_padding
WorldBSP bsp
```

`WorldBSP` follows the LithTech 2.x/v66-style order:

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
Point points[point_count]       // point position + normal for MM9 v66
PBlockTable pblock_table
uint32 root_node_index
uint32 section_count
```

If `section_count > 0`, seek to `next_world_model_pos` before reading the next world model.

## Important MM9 v66 Deviations

### UserPortal Layout

Public NOLF/LithTech v66 references commonly describe `UserPortal` as:

```text
LTString name
uint32 unknown_int_1
uint32 unknown_int_2
uint16 unknown_short
vec3 center
vec3 dims
```

MM9's observed layout is:

```text
LTString name
uint32 unknown_int_1
uint16 unknown_short
vec3 center
vec3 dims
```

Reading a second `uint32` misaligns every following portal, then overreads the point list and fails at PBlock
dimensions. This was confirmed on `1000TERRORS.dat`, where the public layout caused an implausible PBlock record count
and the MM9 layout parses all 45 local DATs.

### Surface Effects

`Surface.UseEffects` should be treated as enabled when it is greater than zero, not only when it equals `1`:

```text
uint8 use_effects
if use_effects > 0:
    LTString effect_name
    LTString effect_param
```

Consuming effect strings only for `1` can misalign later BSP data.

### Surface Flags And Helper BSPs

For PC DAT v66, surfaces follow the order in `mm9/godot-dat-reader/Research/bspv66.bt`:

```text
vec3 uv_origin
vec3 uv_u
vec3 uv_v
uint16 texture_index
uint32 unknown
uint32 flags
uint32 unknown2
uint8 use_effects
optional effect strings
uint16 texture_flags
```

The surface `flags` field uses LithTech render/collision bits. The locally important bit is `0x00000004`, which marks
invisible helper surfaces. `PhysicsBSP` and intentional invisible wall faces are exported hidden but still collidable.
`VisBSP`, AI/pathing helpers, sound-only helpers, and other non-collision helper surfaces are exported hidden and
`Untouchable`. Do not use `Untouchable` merely because a face is invisible; it disables collision in classic runtime
paths.

`Surface.texture_flags` matches the DTX v2 header `surface_flag` for the referenced texture. For example, Thronheim
terrain has `THRONHEIMCLIFF.dtx` as surface flag `13` and `THRONHEIMGRASS.dtx` as surface flag `14`. Treat this as
source material metadata for later footstep/surface behavior rather than as an ODM texture name.

### Texture Decoding And Sidecars

Map-local generated bitmaps under `assets_dev/worlds/mm9/maps/<map>.bitmaps/` are derived from DTX v2 source pixels and
must be regenerated with the DAT transcoder when aliases change. Keep these aliases map-local because MM9 DAT maps reuse
short material names such as `THRONHE002` for different source textures. The `.material_aliases.yml` sidecar preserves
the original LithTech texture path plus DTX header metadata such as `dtx_surface_flag`, `dtx_texture_group`, `dtx_bpp`,
and detail texture parameters.

For local MM9 DTX v2 files, the header matches LithTech's `DtxHeader` layout from
`mm9/lithtech/runtime/shared/src/dtxmgr.h`:

```text
uint32 resource_type              // 0 for DTX
int32 version                     // -5
uint16 base_width
uint16 base_height
uint16 mipmap_count
uint16 section_count
int32 internal_flags              // DTX_* flags
int32 user_flags                  // stored in generated sidecars as dtx_surface_flag
uint8 extra[12]                   // texture group, mipmaps used, BPP, mip offsets, priority, detail data
char command_string[128]
```

OpenYAMM editor metadata exposes both `user_flags` and the legacy `surface flag` alias so older generated sidecars
remain readable while the inspector shows the actual LithTech field name.

## BSP Leaves And Polygon References

Leaf records are:

```text
uint16 leaf_list_count
if leaf_list_count == 0xFFFF:
    uint16 leaf_list_index
else:
    LeafPortalData data[leaf_list_count]

uint32 polygon_count
uint32 polygon_entries[polygon_count]
uint32 unknown
```

`LeafPortalData` is:

```text
uint16 portal_id
uint16 size
byte[size] contents
```

For MM9's VisBSP leaf geometry references, each `polygon_entry` is decoded as:

```text
world_model_index = polygon_entry & 0xFFFF
poly_index        = polygon_entry >> 16
```

This decode is empirically validated across all local worlds:

- `672656` decoded references
- `0` invalid world-model indices
- `0` invalid polygon indices

## Object Data Notes

Object data starts at `object_data_pos`:

```text
uint32 object_count
Object objects[object_count]
```

Each object starts with a `uint16` payload length. The length applies to the object payload after the length field, not
including the length field itself:

```text
uint16 object_payload_length
LTString class_name
uint32 property_count
ObjectProperty properties[property_count]
byte trailing_payload[object_end - current_offset]
```

The object payload boundary is authoritative. Some string properties declare a data length that is larger than the
actual LTString value consumed by the decoder. Do not blindly skip the difference after decoded known properties; doing
so misaligns later properties and can make the next property name look like code `128`. Instead:

- decode known property values by their typed representation,
- preserve the consumed raw bytes,
- preserve the declared property data length separately,
- after all properties, preserve any object trailing bytes up to `object_end`.

The importer currently emits this preservation data in `*.raw_objects.yml`:

- object `data_length`
- object `trailing_hex`
- per-property `declared_data_length`
- per-property `consumed_data_length`
- per-property `raw_hex`
- decoded value JSON

The C++ `Mm9DatWorld` parser now exposes the same `ObjectData` block to game/runtime code as `Mm9DatObject` and
`Mm9DatObjectProperty` records. `*.raw_objects.yml` should stay an importer/editor/losslessness artifact; game runtime
loading should use `.level.yml` to find the source DAT and then read object records directly from the DAT.

## Coordinate And Geometry Notes

- LithTech DAT coordinates are treated as `X/Z` horizontal and `Y` vertical.
- OpenYAMM ODM/BLV conversion maps LithTech `(x, y, z)` to OpenYAMM `(x, z, y)`.
- Polygon winding and plane normals must be checked during conversion. Current tools reverse emitted triangles where
  required so OpenYAMM planes face the same side as the source DAT geometry.
- MM9 world models include special named models such as `PhysicsBSP` and `VisBSP`. These should be interpreted as
  source structures/hints, not ordinary visible props.

## Importer Rules

- Do not assume all DAT v66 files from all LithTech games share the same exact binary layout. MM9 uses a close
  LithTech 2.x-style v66 layout with at least the `UserPortal` difference above.
- The local MM9 files are the authoritative source for MM9 import behavior.
- Cross-check against `godot-dat-reader` and `bspv66.bt`, but prefer local MM9 validation when they disagree.
- Preserve unknown fields and object properties in sidecar metadata. Do not discard data just because the semantic name
  is not known yet.
- Add parser tests for every newly decoded structure or MM9-specific deviation.
- For all-world validation, require:
  - every extracted DAT parses without geometry/BSP failure,
  - all decoded leaf polygon references resolve to existing world models and polygons,
  - generated diagnostics report counts for leaves, portals, objects, and unresolved/unknown object data.

## Known Open Work

- Keep all-world validation reporting object-property code coverage as new MM9 data sets are tested.
- Promote all-world DAT validation into a repeatable test or tool command.
- Use parsed MM9 `UserPortal` data as stronger hints for generated BLV sector/portal structure.
- Continue keeping raw DAT metadata sidecars until every field has an OpenYAMM-native representation.
