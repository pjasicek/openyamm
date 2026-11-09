# Native generation pipeline status

**Driver calibration:** the next generation run prioritizes visual authenticity and quick wiring checks.
See [VISUAL_CALIBRATION.md](VISUAL_CALIBRATION.md). The extensive first-project tests below describe historical
coverage, not mandatory work for each outdoor generation or art revision. The driver rejected the first town’s
scale/facade choices; use the Ravenshore building catalogue before copying its authoring defaults.


Updated 2026-09-07 after the [Brackenford/Greywatch test project](projects/brackenford_greywatch/README.md).
That project now delivers two native playable MM8 maps, editable Blender sources, complete Lua, scoped registrations,
a checked content archive and a frozen playtest. Its [acceptance checklist](projects/brackenford_greywatch/ACCEPTANCE.md)
is the authority for executed checks and limitations. This establishes one working source-to-runtime route; it does
not imply a universal exporter for arbitrary Blender scenes or every feature in every MM6/MM7/MM8 map.

## Executed path

| Area | Current working path | Constraint for a new project |
| --- | --- | --- |
| Blender MCP | Python authors create named meshes/markers/materials and packed editable scenes; native reimports provide plans/cutaways | Use explicit semantic data. Blender names alone cannot encode arbitrary event or content ownership. |
| Indoor source | Z-up GLB, real texture dimensions, room/portal/trigger/mover/entity metadata | Reserve empty sector zero explicitly; assign overlapping triggers, furnishings and movers through `rooms[].source_nodes`. |
| Native BLV | Shared compiler/writer produces faces, sectors, portals, linear mechanisms, BSP and automap outlines | Strict planar/range/ID validation; explicit door source pose and ambient level. New geometry still needs runtime review. |
| Outdoor source | 128² quantized height/tile/attribute arrays plus separate OBJ BModels | Follow native terrain triangles and tile families; heights cannot form undercuts. Preserve source winding when authored. |
| Native ODM | Headless editor source-package build, native scene assembly and writer; reopened arrays/bindings verified | Use a fresh source package to avoid stale binary geometry. Review bridge floors, thresholds, foundations and terrain contact. |
| Gameplay | Stable map/house/NPC IDs, scene actors/loot, map-local handlers assembled with registrations | Reuse shared services; keep scoped stock/state. Do not overwrite generated legacy Lua or invent global IDs silently. |
| Rewards | Existing chest system plus optional validated explicit map-local random item pools | Verify actual generated and saved contents, held-item ownership, disarm/trap and refill behavior. |
| Packaging | Checked content ZIP + manifest, isolated matching-base installation, copied executable and separate test saves | Current registration archive contains full test-base table overrides; it is not a generic production mod merge installer. |
| Validation | Compiler units, faithful scenarios, actual native GUI transactions, game screenshots and short reference FPS samples | Distinguish geometry fixtures, gameplay checks, visual evidence and balance claims. Repeat affected checks on changed sources. |

The shared CLI is `build/tools/mm9_compile_indoor_source` despite its historical name. The editor exposes:

```sh
build/editor/openyamm-editor --asset-root /path/to/isolated/assets_dev --world mm8 \
  --headless-build-map /path/to/example.map.yml
```

Indoor source packages may pass their `.scene.yml`. See the project's [exact rebuild sequence](projects/brackenford_greywatch/REBUILD.md).
Sixteen indoor compiler cases / 182 assertions covered current metadata, real native mechanism motion, explicit static
furnishing ownership and ambient. Reward/ChestRegression coverage passed 27 cases / 337 assertions. Those totals describe
this revision, not a permanent substitute for checking the relevant code and tests after future changes.

## Authoritative implementation

- [Indoor metadata](../editor/document/IndoorGeometryMetadata.h),
  [compiler](../editor/import/IndoorSourceGeometryCompiler.cpp),
  [derived geometry](../editor/import/IndoorDerivedGeometry.cpp),
  [native BLV](../game/indoor/IndoorMapData.cpp).
- [Source import](../editor/import/IndoorSourceGeometryImport.cpp),
  [mesh import](../editor/import/ObjModelImport.cpp),
  [document/package build](../editor/document/EditorDocument.cpp).
- [Outdoor terrain metadata](../editor/document/OutdoorTerrainMetadata.h),
  [BModel metadata](../editor/document/OutdoorGeometryMetadata.h),
  [native ODM](../game/outdoor/OutdoorMapData.cpp),
  [terrain geometry](../game/outdoor/OutdoorGeometryUtils.cpp),
  [tile resolution](../game/maps/TerrainTileData.cpp).
- [Asset mounting](../engine/AssetFileSystem.cpp),
  [Lua event runtime](../game/events/EventRuntime.cpp),
  [map item schema](../game/maps/MapItemSourceData.h),
  [loot runtime](../game/gameplay/LootContainerRuntime.cpp).

Use the [authoring contract](AUTHORING_CONTRACT.md), [gameplay guide](GAMEPLAY_AND_SCRIPTING.md) and
[population/composition guide](POPULATION_AND_COMPOSITION.md). The 33 reference cases cover the requested MM6/MM7/MM8
indoor/outdoor spread with additional Harmondale, Alvar and Murmurwoods comparisons. Reference preview lighting and
inferred placement intent are not evidence of native runtime behavior.

## Still project-specific

The shipped author scripts procedurally generate these layouts and accompanying manifests. A future free-form sculpt
or arbitrary imported mesh needs its own bounded export adapter/validation, not an assumption that all names or Blender
modifiers are supported. Blender empties and lamps require conversion into the declared native marker/light records;
review-only geometry must be excluded from runtime collision. Doors are native linear movers; more unusual reference
mechanisms or scripted encounters need a small executed fixture before inclusion in a larger generated map.

Native indoor save loading currently resets viewing yaw/pitch; the visual tool applies real mouse orientation after
load. Performance evidence is a short software-display workload comparison, not a hardware guarantee. The driver's
balance pass remains separate from functional map completion. Keep original-engine behavior and architecture shared;
fix authoritative source/schema/compiler/runtime ownership rather than adding hidden binary repairs or fallback layers.
