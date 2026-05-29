# MMMerge Transport And Town Portal Audit

This audit covers the merged travel stack used by MM6/MM7/MM8:

- Town Portal and Dimension Door continent destinations.
- Outdoor edge travel.
- Stable/boat/arena house travel.
- Lua/runtime route overrides used by MMMerge fixups.

The audit deliberately treats `House rules.txt` plus `Transport Locations.txt` as the runtime authority for stable and
boat routes. `Transport Index.txt` is tracked as reference data only; it must not become a second runtime route source.

## Reference Surfaces

| Surface | MMMerge reference | OpenYAMM authority | Status |
| --- | --- | --- | --- |
| Town Portal continent sets | `reference/mmmerge/Data/Tables/TownPortalSwitch.txt` | `assets_dev/engine/data_tables/town_portal_switch.txt` | Byte-identical, loaded, consumed |
| Outdoor edge travel | `reference/mmmerge/Data/Tables/Outdoor travels.txt` | `assets_dev/engine/data_tables/outdoor_travels.txt` | Byte-identical, loaded, consumed |
| House route targets | `reference/mmmerge/Data/Tables/Transport Locations.txt` | `assets_dev/engine/data_tables/transport_locations.txt` | Byte-identical, loaded, consumed |
| Legacy route slot table | `reference/mmmerge/Data/Tables/Transport Index.txt` | `assets_dev/engine/data_tables/transport_index.txt` | Byte-identical, parsed for reference only |
| Transport index disabling | `reference/mmmerge/Scripts/Structs/After/RemoveTravelLocationsLimits.lua` | OpenYAMM route construction in `HouseTable` | Covered by design |
| Erathia runtime route mutation | `reference/mmmerge/Scripts/Maps/7out03.lua` | `assets_dev/worlds/mm7/events/maps/7out03_mmmerge.lua` | Implemented and tested |
| Dimension Door generation | `reference/mmmerge/Scripts/General/2_OutdoorTravels.lua` | `GameplayUiRuntime` plus `GameplayPartyOverlayInputController` | Implemented with OpenYAMM landing policy |

Commands used for the table identity check:

```sh
cmp -s assets_dev/engine/data_tables/town_portal_switch.txt reference/mmmerge/Data/Tables/TownPortalSwitch.txt
cmp -s assets_dev/engine/data_tables/transport_locations.txt reference/mmmerge/Data/Tables/Transport\ Locations.txt
cmp -s assets_dev/engine/data_tables/outdoor_travels.txt reference/mmmerge/Data/Tables/Outdoor\ travels.txt
cmp -s assets_dev/engine/data_tables/transport_index.txt reference/mmmerge/Data/Tables/Transport\ Index.txt
```

All four comparisons passed.

## Runtime Consumers

`GameDataLoader` loads all four tables. The active runtime application is:

- `Outdoor travels.txt` is applied to `MapStats` during `GameDataLoader::applyMergedRuntimeTables`.
- `House rules.txt` and `Transport Locations.txt` are applied to `HouseTable` during the same runtime-table pass.
- `TownPortalSwitch.txt` is used by `GameplayUiRuntime` for Town Portal and Dimension Door overlays.
- `Transport Index.txt` is exposed through `MergedTransportIndexTable` only for tracking/reference tests.

House transport routes are built once from route-location ids in `House rules.txt`. Each referenced location id must
resolve in `Transport Locations.txt`; unresolved ids fail data loading instead of falling back.

At runtime, `HouseInteraction` applies a persistent route override after selecting the base house route. This keeps the
normal data path authoritative while still allowing MMMerge-style scripted route changes.

## MM7 Parity Results

| Behavior | MMMerge behavior | OpenYAMM result | Coverage |
| --- | --- | --- | --- |
| Antagarich Town Portal | Uses `TownPortalSwitch.txt` group `Antagrich`, QBits `718-723` | Same group and QBits are loaded and used by the overlay | `tests/MergedBaseTablesTests.cpp` |
| MM7 outdoor edge travel | Uses `Outdoor travels.txt` rows for `7out02`, `7out03`, `7out04`, `7out05`, `7out06`, `out11`, `7out13`, `out14`, `7out15` | Same rows are applied to map transitions | `tests/MapStatsRegressionTests.cpp` plus loader failure on bad rows |
| MM7 house transports | Uses transport location rows `25-59`, plus long route rows `79` and `97` | Routes are built from house rules and transport locations | `tests/HouseDialogueRegressionTests.cpp` |
| Erathia route slot change | `Game.TransportIndex[34][4]` switches between Emerald Island and Bracada Desert based on QBit `519` | House `462`, route `4` receives a persistent route override on map load | `tests/ScriptedMapRegressionTests.cpp` |
| Route schedule and QBit gates | Weekday and QBit fields hide/show routes | Weekday and QBit filters are applied before options are shown | `tests/HouseDialogueRegressionTests.cpp` |
| Travel days and NPC reductions | Transport duration can be reduced by hired NPC professions | Route days are clamped and NPC reductions are applied | `tests/HouseDialogueRegressionTests.cpp` |
| Temple in a Bottle return | Stores previous map/position and returns from `7nwc.blv` | Saved runtime location persists in save data | `tests/HouseDialogueRegressionTests.cpp`, `tests/ScriptedMapRegressionTests.cpp` |
| Dimension Door scroll | Opens the Dimension Door Town Portal screen | Data exists, but use path is incomplete: item `190` is random-generated as a high-tier scroll-like item, yet it is marked `Gem`, so item-use classification does not reach the Dimension Door special case. | Missing targeted item-use regression |

## Dimension Door Notes

MMMerge's `GenDimDoor` mutates the global Town Portal set with day-based candidate maps. OpenYAMM uses the same
`TPGlobal` table group for the fullscreen UI, then applies explicit landing rules when the player clicks a continent:

- Jadame: Dagger Wound by default, Ravenshore after the Dadeross letter QBit.
- Antagarich: Emerald Island by default, Harmondale after Emerald Island completion QBit `519`.
- Enroth: New Sorpigal start.

This matches the agreed OpenYAMM behavior for cross-continent travel rather than copying MMMerge's daily rotating
destination list. The UI still uses the merged `TPGlobal` row ids and artwork positions as the selection surface.

CrossContinents gating is intentionally runtime state driven: Dimension Door is unavailable until
`MMerge.CrossContinents.GotMainQuest` is set. This is stored in persistent Lua runtime state.

### Missing Dimension Door Trigger Work

These are actionable gaps found during the Verdant/CrossContinents audit:

| Item | Status | Required fix | Notes |
| --- | --- | --- | --- |
| Town Portal near a magical place opens Dimension Door | Implemented | Shared Town Portal cast override checks configured MMMerge Dimension Door magical-place triggers before opening the normal Town Portal UI. | `GameplayScreenRuntime::shouldTownPortalCastOpenDimensionDoor` covers the imported radius/tile trigger sites and `GameplaySpellService` opens Dimension Door instead of Town Portal there. |
| Dimension Door scroll item `190` use | Implemented | Item `190` now classifies as a usable Dimension Door scroll before generic equip-stat handling. | `InventoryItemUseRuntime` exposes `UseDimensionDoorScroll`; `GameplayItemService` opens the Dimension Door overlay and only removes the held scroll when the overlay opens successfully. Covered by `tests/InventoryEquipRegressionTests.cpp`. |
| Verdant first-contact letters `770/771/772` | Implemented as separate path | Keep separate from item `190`; they should remain readable/message-scroll first-contact items unless the design changes. | These are generated by `CrossContinents.TryGenerateScrollForChest`, not random loot Dimension Door scrolls. |

## Transport Index Decision

MMMerge includes `RemoveTravelLocationsLimits.lua`, which disables the original `Transport Index.txt` load path and
expands travel locations. That is consistent with OpenYAMM's current model:

- Parse `Transport Index.txt` for audit/reference visibility.
- Do not use it as active route authority.
- Build routes from house rules and transport locations.
- Use Lua route overrides for script-only route mutations.

This avoids stale dual ownership. The only MM7 route mutation found in the audited MMMerge scripts is Erathia's
QBit-dependent slot, and it is already represented by the override API.

## Save And Lua API

The route override API is intentionally narrow:

- `evt.SetTransportRouteOverride(houseId, routeIndex, route)`
- `evt.ClearTransportRouteOverride(houseId, routeIndex)`
- `support.setTransportRouteOverride(houseId, routeIndex, route)`
- `support.clearTransportRouteOverride(houseId, routeIndex)`

The override payload supports destination label, map name, weekdays, travel days, coordinates, direction, required
QBit, and map-start-position mode. Overrides are saved in `EventRuntimeState::transportRouteOverrides`.

Temple in a Bottle uses the same persistent runtime-state slice through saved locations.

## Remaining Deltas And Risks

| Item | Status | Notes |
| --- | --- | --- |
| `Transport Index.txt` runtime consumer | Not needed | Keep parsed as reference only. Do not wire it into runtime route selection unless a concrete divergence is found. |
| Exact MMMerge Dimension Door daily rotation | Intentional delta | Current OpenYAMM behavior follows the agreed continent landing policy. Implement daily rotation only if the design changes back to strict MMMerge behavior. |
| Town Portal cast override at magical places | Implemented | Town Portal casts at configured MMMerge Dimension Door magical-place triggers now open the Dimension Door overlay before the normal Town Portal UI. |
| Dimension Door scroll item `190` use | Implemented | Item `190` has an explicit item-use action and the held scroll is consumed only after the Dimension Door overlay opens. |
| CrossContinents custom bridge maps/content | Deferred | This is custom-content work, not a missing transport-table consumer. The first Dimension Door gate and rewards are already implemented. |
| Route table completeness | Covered by loader | Bad house-rule location ids fail during table application. Add a targeted regression only if a specific house route diverges in play. |
| Outdoor straight-travel feel | Covered by table consumer | Existing MapStats tests cover representative straight and coordinate-preserving travel. Add more per-map tests only for a reported bad edge. |

## Conclusion

The current architecture is correct for the user's requested direction:

- active route data comes from `House rules.txt` plus `Transport Locations.txt`;
- outdoor edge travel comes from `Outdoor travels.txt`;
- Town Portal and Dimension Door use `TownPortalSwitch.txt`;
- `Transport Index.txt` remains reference-only;
- MMMerge's MM7 Erathia route mutation is implemented through persistent Lua route overrides and save data.
