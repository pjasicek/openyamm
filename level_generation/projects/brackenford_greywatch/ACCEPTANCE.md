# Final acceptance — 2026-09-07

Latest outdoor content: [road-purpose revision](ROAD_PURPOSE_REVISION.md), with visual review and quick native checks;
fresh God snapshot `playtest-offroad`. Earlier functional and driver acceptance evidence below is historical,
and does not certify combat balance for the newly placed population.


Latest layout: [sketch revision](SKETCH_REVISION.md); fresh God snapshot at
`/tmp/openyamm-brackenford-playtest-sketch`. Previous density/facade results below are historical.

Current outdoor layout: [density revision](DENSITY_REVISION.md), with updated native map, automap and God snapshot
`/tmp/openyamm-brackenford-playtest-density`. Earlier revision evidence below is historical. Use the quick static check
with `--review-directory density_revision`; no exhaustive outdoor scenario suite is required.

**Current outdoor revision:** [FACADE_REVISION.md](FACADE_REVISION.md) records the implemented facade/scale/variety
corrections, quick checks and the new `playtest-calibrated` God-character snapshot. Native outdoor hashes and counts
in the original checklist below belong to the earlier build. The indoor map remains byte-identical.

**Subsequent driver review:** the outdoor visual-quality verdict below is superseded by
[visual calibration](../../VISUAL_CALIBRATION.md). The frozen maps retain functional history, but oversized doors,
crate windows, inappropriate door art/chimneys and road obstruction are rejected for future generation. This
calibration pass updates the catalogue/playbook; it does not claim those frozen map assets have been remodeled.
The long test matrix below is historical and is not the default workflow for future outdoor maps.


The two-map generation brief and the driver's decoration/terrain/interaction revision are implemented and checked.
The package requires the matching OpenYAMM checkout/base assets; it is a playable isolated MM8 test region. Final combat
balance is reserved for the driver, as explicitly clarified in the goal. No required handler or manual map finishing remains.

## Requirement checklist

| Requirement | Result and evidence |
| --- | --- |
| Reference research and feedback loop | **Pass.** 33 MM6/MM7/MM8 cases, 33 decoration inventories/plans, 53 highlighted contextual captures, 292 decoded native frames; source hashes/local links pass `validate_references.py`. See [population/composition guide](../../POPULATION_AND_COMPOSITION.md). Design-intent interpretations are distinguished from measured records. |
| Original native outdoor/indoor | **Pass.** [ODM build](brackenford_build.json), [BLV build](greywatch_build.json), [source compiler checks](review/lighting_perception.json), [native outdoor fixture](review/outdoor_source_verification.json). New geometry, native 128² terrain, explicit sectors/portals/BSP/outlines; no copied reference layout or binary repairs. |
| Terrain, roads, water, variety, decoration | **Pass.** 24 buildings in nine related forms/four orientations; town shelves, river/bridge, screened wilderness and regional passes; 563 native decorations. [Outdoor overview](review/brackenford_native_region.png), [town](review/gameplay/perf_brackenford.png), [bridge](review/gameplay/bridge.png), [north pass](review/gameplay/north_pass.png), [bridge movement](review/current_bridge.json). Draw distance unchanged. |
| Castle and cave approaches | **Pass.** New roofed keep/towers and faceted rock mouth. [Castle](review/gameplay/castle_approach.png), [final cave](review/gameplay/cave_facets.png), [cave revision scope](review/cave_revision_scope.json). Latest revision changes only four cave BModels; terrain/entities/other 71 models are identical to the wider validated revision. |
| Two entrances and correct returns | **Pass.** Exactly `lg01.odm` and `lg02.blv`, two approaches into the connected vault. Native picks/confirmation/arrival returns pass [clean package checks](review/package_install_checks.json). Named/default arrival markers are in both semantic manifests. |
| Services, teachers, existing MM8 dialogue | **Pass.** 24 doors, scoped services, four successful teacher purchases plus eligibility/repeat checks, level-25→26 training, 14 ambient topic responses. [Town reuse](TOWN_REUSE.md), [service checks](review/town_services_and_regressions.json), [topics](review/content_checks.json). City hall uses MM8 Merchant Guildhouse/Myles Greydawn content. |
| Actual shop transactions and isolation | **Pass.** Native UI weapon/armor/magic purchases, real gold/stock/inventory and preserved enchantments. [Purchases](review/gameplay/shop_purchases.json), [armor UI](review/gameplay/armor_buy_purchased.png). Original house 2 and scoped weapon stock remain independent; armor/magic use the same house-state path. |
| Guards/villagers and safe town | **Pass.** 9 guards + 20 villagers, 14 remote active ogres. 344 simulated active-world seconds, continuous perimeter legs and 24 service observations: party/43 actors unharmed, remote packs unaware. [Safety check](review/shared_simulation_checks.json) contains the passing `town_safety` and wilderness-control entries; [earlier complete safety report](review/town_safety_check.json). |
| Regional and scheduled travel | **Pass.** West→Ravenshore, north→Alvar; original stable profiles privately extended with paid daily return. [Travel](review/shared_travel_followup.json), [installed stable trip](review/package_install_checks.json), [off-day refusal](review/stable_off_day.json), [5,824/8,896-unit approaches](review/route_followup.json), passing `regional_approaches` entry. |
| Two guarded loot sites, chest quality and pickup | **Pass.** Four outdoor/four indoor chests, five loose MM8 items, treasure levels 6/5. [24 generated chests across three sessions/map](review/rewards/generation.json), [all-eight cursor/inventory/save/revisit checks](review/rewards/persistence.json), [loose pickup](review/current_rewards_smoke.json), [reward provenance](source/reward_registry.json). |
| Refill, obelisk and well | **Pass.** Loot absent at 335 days, regenerated at 337 around 336-day refill: [native snapshots](review/rewards/refill.json). [Well/obelisk](review/well_obelisk.json): nonstacking +25 Might, native save/reload, real eight-hour rest reset; visible reused inscription, local discovery without original QBit 187. |
| Dungeon progression, doors, secret and stairs | **Pass.** 11 chambers/three elevations, optional branches, secret chest room, paired door and gated shortcut. [Both-sided controls/persistence](review/baseline_and_encounter_doors.json), [final lower stairs and complete shortcut both ways](review/remaining_routes.json). Earlier main stair diagnostic explicitly isolates geometry; active actor passage/combat has separate evidence. |
| Automatic/button lift and recovery | **Pass.** One trip on boarding, no stationary oscillation, both landings, saved mid-travel state, manual recovery, open records gate after combat. [Current 48-step route](review/combat_lift_followup.json), [closed-gate automatic route](review/lift_automatic_check.json). |
| Active combat, traps and Perception | **Pass.** Four watch mercenaries crossed an open doorway; six records/junction enemies defeated in ordinary-party observations. [Combat entries](review/approaches_and_combat.json). Both walked-on plates fire existing spells and deal 20 HP in saved ordinary-party snapshots: [trap damage](review/trap_damage.json); one-shot state persists. [High/low native Perception](review/lighting_perception.json). |
| Native lighting and entrance consistency | **Pass.** 22 authored light pools + torches; all occupied sectors ambient 22, matching MM8 d18/d48. [On/off native review](review/lighting_perception.json), [complete-ceiling gameplay](review/gameplay/perf_greywatch.png). Upper hall shares main masonry; lower cave keeps rock. |
| Build, original behavior and packaging | **Pass.** Game/editor/tools built; 16 compiler cases/182 assertions and 27 reward/ChestRegression cases/337 assertions passed. Original MM6/MM7/MM8 exit paths pass [shared travel regressions](review/shared_travel_followup.json). [Archive validation](review/package_validation.json) and [fresh installation checks](review/package_install_checks.json) pass. Both frozen starts reload under the copied executable: [snapshot manifest](review/playtest_snapshot.json). |

## Visual review and performance

The screenshots above are native game views with real geometry, actors and decoration. Native Blender reimports also
provide [opposite indoor cutaways](review/greywatch_native_south.png) and [outdoor terrain overview](review/brackenford_native_region.png).
Before/after failures remain visible in [review history](REVIEW_LOG.md): early bland geometry, flat cave facade, bridge
lip, lift interaction, sector ambient and shared scenario simulation issues were corrected at their sources.
The [flat cave capture](review/gameplay/cave_front.png) and [faceted result](review/gameplay/cave_facets.png) show the last
local revision. Reference annotations are contextual evidence; they do not claim access to original designers' thoughts.

[Performance report](review/performance.json): same binary, settings, ordinary party and 1600×1200 software display,
VSync off; serial captures without concurrent builds/tests. Median of three one-second samples after warmup:

| Sampled scene | Median FPS |
| --- | ---: |
| Brackenford town | 44.6 |
| Ravenshore service street | 40.0 |
| Greywatch active encounter | 43.9 |
| Naga Vault active encounter | 24.2 |

All four final images were inspected: actual native gameplay, complete indoor ceilings, active actors, living party
members, no menu/defeat-screen substitution. These are short sampled workloads with different visible geometry/actors,
not a controlled isolation of terrain cost, a broad benchmark, or a prediction of the driver's GPU performance.

## Exact delivered artifacts

| Artifact | SHA-256 |
| --- | --- |
| `lg01.odm` | `1eec2ce5a7be8f3f853190bf4f3476af82f50502e1355c9324b6d31d2debce00` |
| `lg02.blv` | `b227608891142f1982f2cd6039124eaab2310775b6760760a8570baff8679fec` |
| Copied game executable | `27e70c9d748a13309d09aab9d2e65771e79388a8d826e717f90044817520859e` |
| Content ZIP | `000f60e15b0b49929bfad5639c46880c5504726acd66e23c691605225587a936` |

Editable Blender files independently reopen with 693 outdoor / 199 indoor objects, packed images and zero external
libraries. [Rebuild instructions](REBUILD.md) preserve authored Lua and regenerate native content without finishing in
an external map editor. The archive includes seven runtime files and eight isolated registration tables; existing art
remains in the local MM8/base installation.

## Practical limits and retained history

- The driver owns final balance. Stationary records combat left three members unconscious; checks establish functioning
  combat, collision, mechanisms and escape segments, not a single continuous full-dungeon victory or survival rate.
- Town safety covers 104 seconds of continuous perimeter movement plus 24 ten-second service observations, with explicit
  repositioning between services. Deliberately dragging a hostile pack into town is outside the no-aggro promise.
- Shops reuse MM8 service profiles under OpenYAMM's merged global item pool. They can stock a merged item (the tested armor
  purchase was item 1698); generated chest equipment is explicitly restricted to the audited MM8 pool. Existing global
  MMerge CrossContinents first-chest letter 770 remains normal base behavior and is excluded from authored reward totals.
- High/low screenshots directly compare the secret pressure plate. The secret wall additionally has checked native flags,
  moving collision, controls and its chest; a separate low/high wall screenshot is not claimed. Torch-off is a diagnostic
  copy with lights/sprites disabled, excluded from delivery; these torches are not presented as player-switchable.
- Indoor save loading currently resets viewing yaw/pitch in the shared engine. Captures use actual mouse movement after
  load; this does not prevent gameplay or map transitions and was not broadened into a save-format change.
- Reports include their own build hashes. The final cave-only revision preserves all terrain/entities and other models;
  the native ambient revision preserves gameplay geometry. Wider checks on those earlier matching components remain
  relevant. All package/arrival checks match the final delivered native hashes.
- Historical failed batches are retained. `shared_travel_followup.json` resolves the earlier regional travel failure;
  `combat_lift_followup.json` resolves the obsolete manual-lift/initial timing fixture; `remaining_routes.json` is the
  passing final stair/shortcut fixture. Do not read an old aggregate `false` as an unresolved current feature.
