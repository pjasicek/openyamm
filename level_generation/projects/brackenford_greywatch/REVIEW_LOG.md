# Generation review log

## Ordinary party, staged encounters and driver balance guidance — 2026-09-06

The driver returned and explicitly asked for best-guess difficulty from comparable dungeon density/placement; final
balance tuning belongs to them. Both copies of the goal record this clarification. Do not spend future turns trying
to prove a fixed stationary attack sequence wins every random fight. Keep active AI, sane placement and functional
combat/LOS, mechanisms, safe-town and escape-route checks. `BASELINE_PARTY.md` describes the fixture and the actual
reference reasoning: Naga Vault has 18 spawn records, four initial actors and additional door summons, not a measured
22-monster total. Greywatch keeps 24 fixed mercenaries in chamber-sized groups; both arrival rooms remain empty.

Scenario `new_game_flow.party` now creates fresh explicit characters, validates class/skill caps and shared equipment
restrictions, and preserves ordinary resources and gear across save/load. The canonical five-member level25 source
is `source/baseline_party.json`; `build_baseline_tests.py` embeds it reproducibly. No default GM200 skill seed,
enchantments, invisibility, invulnerability or recurring heal is inherited. Attack input uses GameSession's normal
selection, targeting, recovery and damage path, with normal world/actor updates. Read-only observations now report
actor HP/position and bounded party event variables. Invalid fixtures and invalid action durations are rejected.

A stationary records-room fight pulled the barracks and lower passage into the same encounter. New native doors
7/8 and events107/108 separate those approaches, retaining all earlier IDs and 24 actors. Fixed controls work on
both sides. Native rebuild: 604 faces, 847 vertices, 25 sectors including empty zero, 24 portals, 294 BSP nodes,
353 outlines, eight movers, 22 decorations and 22 lights. Every closed door endpoint still matches native vertices.

`review/baseline_and_encounter_doors.json`: **11 scenarios / 187 steps pass**, with current native, scene, Lua,
scenario, settings and game-binary hashes. Coverage includes explicit party gear before/after save, all five levels
and full HP, shared attack experience gain, both new doors' closed collision/fixed controls/saved open state,
existing door/shortcut controls, basic lift rides and lower-landing recovery, plate contact persistence, two-entry
map transfers and original MM6/MM7/MM8 exits. The current entrance observation killed all four guards; HP ended
260/90/115/214/49. These are observed outcomes, not hardcoded expected kills or final balance claims.

`review/baseline_party_validation.json`: **eight invalid-input cases pass by being rejected**, including illegal
classes/skills/equipment, zero/overflow levels, an impossible live HP bound and a negative action duration.
`cmake --build build --target openyamm -j25` passes. Changed Python files compile and the focused changed-file
whitespace check passes. The whole-worktree check reports unrelated trailing whitespace in
`assets_editor_dev/engine/data_tables/map_stats.txt`; it was not changed as cleanup.

Combat diagnostics starting inside records were inconsistent, including unconscious members and retreating
low-health enemies outside the fixed aim cone. They are not a continuous both-entry playthrough. Attempts to
prepend that stationary combat to the long lift route did not establish full route completion. The shorter native
lift/recovery scenarios do pass with AI/collision enabled. Do not claim the complete combat route from those checks.

The authoring script now saves Greywatch as a full standalone `.blend`. A separate Blender process reopened it
and reported the correct scene, 147 objects and zero linked libraries. This replaces the old scene-library handoff
limitation for `lg02.blend`. Blender MCP reconnected by the driver passed live inspection; the disconnect cause is
unknown. The current BLV was reimported and both refreshed opposite cutaways inspected. They show the new closed
doors and connected elevations, using study lighting and omitting ceilings/actors; they do not prove runtime lighting.

Remaining work includes outdoor services/travel/timed safety, chest refill/loot and trap/Perception behavior, complete
route checks, outdoor visual refinement, native gameplay views/performance and final package/reproducibility audit.

## Native mechanisms, floor plates and first gameplay view — 2026-09-06

This entry supersedes the earlier state-only mechanism evidence. A lift ride exposed that authored closed geometry
was being stored as native open-position offsets. Native distance is zero when open and moveLength when closed.
The source compiler now accepts explicit `door.source_pose`, retains native closing-direction semantics, derives the
open offsets for closed source meshes, and rejects endpoint overflow. Existing unspecified source pose remains the
native open baseline. Tests exercise actual native vertex movement, not merely exported numbers or state labels.
All 14 focused compiler cases / 157 assertions pass. The game, editor and compiler build successfully.

Greywatch now compiles to 588 faces / 815 vertices, 25 sectors including empty zero, 24 portals, 291 BSP nodes,
353 outlines and six movers. The builder checks every closed endpoint against the written BLV vertices.
The paired door, gate and secret wall block movement when closed and allow passage when open. Retraction hid the
paired leaves behind corridor walls, making them impossible to click closed. Fixed controls now operate the paired
door from either side, the secret wall from its room, and the shortcut from either approach. The gate button was
moved onto a solid records wall; the lower lift button now sits at the landing rather than inside the shaft.

`review/indoor_checks.json` records 10 faithful scenarios / 162 passing steps, with native/source/binary/settings
hashes. These cover door collision, control recovery, shortcut locking/unlocking, secret and shortcut save/load,
lift travel both ways, lower landing disembarkation/calling with the records gate closed, both plate contacts and
saved map variables, two-entry map transfers, and original MM6/MM7/MM8 exits. Actor AI/collision are enabled in these
new scenarios. Their scope is functional interaction, not the required equipped-party combat or balance validation.

The longer `greywatch_lift_route.yml` is intentionally still failing, with evidence in
`review/indoor_combat_route_pending.json`. It passes 26/27 steps: boarding, saving partway up, loading/resuming to
the upper landing, upper disembarkation/calling, and descent. Pursuing records defenders block the final lower
disembarkation. An earlier diagnostic with actor collision excluded passed the geometry route; that diagnostic is
not acceptance evidence. Three upper-landing sentries moved to the lower junction, retaining semantic IDs/runtime
slots, to keep the top landing clear and give the cave approach more resistance. The remaining full-route test must
clear defenders with the intended ordinary party and validate populated passage/combat, rather than disable actors.

Both original pressure plates were thin overlays above a continuous floor. Walking across them failed to acquire
their support faces, so neither event ran. Each plate now replaces its own floor patch; surrounding quads stop at
the plate boundary. Normal walking triggers events 301/302 without forced face replay. Their one-shot map variables
persist in real saves and remain set on recrossing. This does not yet verify projectile damage, trajectories, refill
reset or low/high Perception highlighting.

There are now 22 native `dec56` torch decorations, from Naga Vault's MM8 art (merged decoration row 299 / index 298).
Markers sit beside solid wall sections, away from doorway centers, with extra clearance from the swollen cave wall.
Intrinsic radius-96 flame light and explicit radius-640 static pools are intentional separate sources, following
the reference's use of both decoration and BLV lights. Their combined brightness/leakage still needs final review.
`review/greywatch_gameplay_startup.png` is an actual native game capture, not a Blender render. Complete ceiling,
masonry, mosaic floor, controls and torch art are visible. Its development startup party is not the level-25 fixture.

That capture also exposed inherited debug defaults: the minimal staged settings left immortality and unlimited mana
enabled. `stage_runtime.py` now explicitly disables both and the god-lich preset, with movement multiplier one.
The final 162-step batch was rerun under those settings. Older functional reports and the first screenshot cannot
establish ordinary combat survival. The equipped level-25 party, real attack controls, complete combat route, remaining
services/travel/rewards, visual refinement and performance comparison are still required before completion.

## Town content and native rewards — 2026-09-06

This entry supersedes the earlier geometry-stage statements that services and outdoor population are absent.
Brackenford now contains 75 BModels / 995 native faces, 43 fixed actors, four chest templates and five loose items.
There are 24 scoped house instances (12000–12023), 16 scoped NPC instances (12000–12015), four existing Master teachers
and twelve ambient residents/civic interactions. Shared NPC/house records and generated legacy Lua remain unchanged.
All 24 native doors open their intended service or resident. Fourteen selected ambient responses match the original
MM8 text byte-for-byte through the runtime dialogue hash. Teacher learning, shop stock/purchases and stable travel
still require separate validation. The existing Gymnasium profile retains its level-15 cap, below the planned party.

Population: nine existing MM8 Dark Elf guards, twenty Dark Elf/Human peasants and two packs of five Ogre Warriors /
Warleaders plus two Ogre Mages/Magi. Town instances share Ravenshore's friendly local ally type; wilderness instances
are actual aggressors. Nothing changes shared monster relations. Actor indices 0–28 are town residents, 29–42 ogres.
The final authored minimum distance to sampled town activity/perimeter points is 15,388 units. Native loading finds
43 textured actors and no missing actor textures. The thirty-second square observation checks actual HP, hostility,
party detection and targeting for all actors. A separate wilderness approach confirms that ogres detect/target the party.
This is preliminary AI evidence, not the required five-minute equipped-party route or combat tuning.

Four chest models reuse a small Ravenshore chest asset with preserved native UVs. The obelisk and well similarly reuse
their small MM8 model assets, at new locations; no complete reference settlement geometry is imported. Native reimported
close-ups in `brackenford_native_east_chests.png`, `brackenford_native_obelisk.png` and `brackenford_native_well.png` were
inspected. Props are recognizable; terrain transition joins remain visibly crude and need refinement. These are geometry
studies without actor/item sprites or native gameplay lighting.

The well supplies the existing +25 temporary Might effect to the selected character, with no stacking while that bonus
is already active. Normal rest clears temporary event bonuses and makes it available again; the reset path still needs
its focused interaction test. Repeated use and save/load preservation pass. It writes no original campaign autonote.
The obelisk displays the existing `ethesunsh` inscription and records only local MapVar(11); native save/load preserves
discovery while original campaign QBit 187 stays clear. In-game visual confirmation of the inscription is still needed.
All four chest faces open their correct slots. Five loose MM8 items pass actual picking, inventory acquisition and
absence from the world after native save/load. Chest contents across seeds, chest looting and refill remain unverified.

Failures corrected in source/tooling during this iteration:

- Ambient text expectations initially encoded Windows-1252 source as UTF-8; expectations now use the source encoding.
- A southern caster occupied the first chest's footprint. Moving the pack north clears both chests; source validation
  now rejects actors intersecting chest, well or obelisk footprints.
- An absent optional pickup event was written as numeric `0`, which the scene parser correctly reads as nonempty text.
  It is now the empty string, enabling the normal inventory pickup policy without a missing scripted event.
- The scenario Escape helper handled dialogues but rejected chest overlays. It now sends a press/release through the
  shared loot-overlay input path. Chest tests use real picking and closing, with no event-target fallback.
- Added read-only scenario observations for live actor HP/hostility/detection/targeting, runtime event variables and
  world-item presence. World-item absence checks never succeed merely because the item is already in party inventory.

The complete two-map goal remains in progress. See `review/content_checks.json` for the final selected checks and
artifact hashes from this iteration, rather than treating intermediate failing log files under `/tmp` as final results.

## Native maps and traversal — 2026-09-06

Greywatch is now an original native BLV: 577 faces, 25 sectors including empty sector zero, 24 portals, 289 BSP nodes,
353 outlines, six linear movers and 22 light records. Its scene supplies 24 existing MM8 mercenaries and four chest
templates. Authored Lua is separate from generated registrations. Native north/south cutaways were inspected.
Sparse torch decoration art, final lighting, combat, lift/trap/secret behavior and persistence still need work.

Brackenford now has a native 128 × 128 heightfield, 430 connected road cells and 69 BModels with 860 faces. There are
24 original town buildings, a bridge, a four-tower castle composition and a provisional cave facade. Native terrain
height/tile bytes match Blender's grid exactly. The cave facade is still rectangular; it needs irregular sloping rock
and a better hillside fit. The castle needs roof/trim detail, the town needs greater visual distinction and its civic
square, and the landscape needs decoration, bank-tile refinement and route review. All 24 house-service handlers are
currently explicit scaffolding. No outdoor population or rewards are present yet.

Failures found and corrected:

- Moving secret surfaces lost their source attributes/event binding. They now use the same authored surface metadata
  as static triggers. The focused compiler suite passes 11 cases and 107 assertions.
- The headless scenario driver skipped deferred common-data loading, so faithful new-game map resolution failed.
  It now completes that load before activating a world. Original MM6/MM7/MM8 outdoor load checks pass.
- Outdoor source building did not bake scene event bindings or party-start entities into ODM. The editor build now
  assembles these through the existing runtime scene assembler before native serialization.
- The outdoor importer's floor-orientation heuristic inverted authored underside faces. Explicit
  `preserve_source_winding` metadata now preserves source winding and classifies transformed native floors, ceilings
  and walls from signed normals. A small export fixture verifies types 5/3/4/6/1, native event 321, the native party
  start, metadata round trip, exact terrain and byte-identical rebuilding.
- Headless dialogue confirmation checked event state after the normal UI had transferred the pending map move into
  `GameSession`. The driver now also processes that session queue. Both generated entrance/exit routes pass through
  actual picked faces and normal confirmation dialogue, including the requested return-coordinate trace.
- Initial door UVs repeated a complete door texture vertically. Door/window panels now use one full texture span.
- The bridge deck overlapped the level bank pads, producing black strips in Cycles at each end. Shortening it to the
  pad boundaries removes the overlap. Compare `brackenford_bridge_before_overlap_fix.png` with
  `brackenford_native_bridge.png`. The rebuilt bridge still passes the full native crossing test.

Current runtime evidence:

- `greywatch_smoke.yml`: actual interaction opens both halves of the paired door.
- `greywatch_stairs_probe.yml`: full 384-unit descent and ascent pass. This intentionally excludes actor AI/collision
  to isolate geometry. The initial populated return walk was obstructed/slowed by mercenaries; populated passage
  clearance and balanced combat still require the level-25 test party.
- `two_map_arrivals.yml`: 16 faithful steps pass, covering castle entry/exit and cave entry/exit. It verifies return
  request coordinates through transition traces; independent landing pose/clearance and facing review remain.
- `brackenford_bridge_probe.yml`: a 5632-unit walking segment across both bridge approaches passes within four XY
  units and one Z unit. The outdoor map is currently unpopulated; this is not town-safety evidence.
- The isolated editor `outdoor-source-only-package-load` regression passes after the export changes.
- Original faithful exit-confirmation checks pass for MM8 Naga Vault → Garrote Gorge, MM6 6t1 → Castle Ironfist,
  and MM7 Erathian Sewer → Erathia. These exercise the corrected session travel queue.

The images are native geometry inspections under study lighting. They do not establish in-game water rendering,
torch lighting, performance or populated gameplay quality. The complete two-map goal remains active.

## Native compiler calibration — 2026-09-06

Blender MCP saved/exported a textured two-room source; the compiler wrote BLV; the independent Python reader and Blender
reimport inspected the written native result. Bounds are `[0,0,0]` through `[2048,1024,768]`, sectors 1/2 connect through
one portal, and event 101 has the correct 64-by-64 texture pixel span. The compiler generated 13 BSP nodes and eight
outline segments. The divider appears at Y 0–384 and 640–1024, with no minimap line across the doorway.

Failures found and corrected:

- A stale editor regression expected 20 vertices where the existing interner produces four shared static and four
  independent moving vertices. Both source and serialized expectations now match the intentional ownership.
- Native non-BSP faces must form the prefix of the sector face list. The round-trip test exposed the wrong ordering;
  the compiler now writes the prefix and adjusts BSP offsets.
- Exact edge matching lost short wall segments beside a portal when the floor used a longer edge. Outline generation
  now splits at collinear native vertices before computing adjacency and suppressing coplanar seams.
- Room metadata previously ignored missing room IDs. It now rejects unknown rooms and missing source nodes.

Ten focused tests pass with 99 assertions, including BSP branching, back-sector portal orientation, crossing/moving
faces, deterministic regeneration, native serialization, non-planar rejection and outline seam removal. The actual
calibration verifier passes. Both `indoor-map-package-load` and `outdoor-source-only-package-load` pass against isolated
MM8 staging assets. The game, editor and compiler CLI build successfully.

Visual review: floor/wall textures and doorway proportions are visible in `calibration/native_cutaway.png`. The central
zero-thickness calibration wall has coincident opposite faces and looks black under the Blender inspection lighting.
This is not acceptable as final presentation evidence; production room shells and inspection materials/culling must
avoid that artifact. The image does not test native torch lighting, collision or interaction.

## Layout draft — 2026-09-06

Inspected `layout_plan.png`: town buildings are separated from the two wilderness reward groups; castle and cave have
distinct approaches east of the river. Indoor branches and the three proposed floor levels fit without footprint
overlap. The cave can reach the records route and the upper arrival through the unlockable shortcut.

Remaining design work: the outdoor drawing only contains the main road; add all service lanes, trails and terrain
contours. Enlarge civic/castle footprints in the actual geometry. Indoor boxes are room budgets, not finished polygons;
author bends, chamfers, stairs, portals and lift boarding geometry. Calibrate all clearance with native movement.
Detailed interactions, actual MM8 registry identities, scoped registrations, Lua and actors are still unimplemented.
Neither `lg01.odm` nor `lg02.blv` is a completed playable map yet.

## 2026-09-07 — services, town safety and new visual brief

Twelve focused scenarios pass in `review/town_services_and_regressions.json`; nine negative fixture checks pass. Teacher mastery purchases/eligibility and real level25→26 training through Lehava are verified. Fixed scenario fresh-session teardown so an old runtime party cannot overwrite a newly seeded party. `review/town_safety_check.json` passes 344 nominal active-world seconds:104 seconds of continuous perimeter walking and24 ten-second service observations reached by explicit poses. No party/actor damage or hostile detection. This is not continuous walking between every house.

Driver requests comprehensive decoration/reference screenshots, architecture variety and stronger terrain screening/terraces without changing view distance, plus direct-click doors and entrance texture continuity. Added to GOAL.md and `/tmp` goal. Blender MCP responds after reboot with default cube/light/camera; editable authored files remain on disk. Previous `/tmp` playtest snapshot is gone. Visual and remaining functional gates are still pending.

### 2026-09-07: reference population and outdoor composition revision

Completed all 30 original reference decoration studies plus Harmondale, Alvar and Murmurwoods. The validator passes 33 inventories/plans, 53 annotated captures, 292 decoded native frames, hashes and links. Case studies now distinguish sprite decoration from modeled detail, initial hidden state and inspection-lighting limitations. See ../../POPULATION_AND_COMPOSITION.md.

Brackenford source now has eight related architectural forms, varied footprint/height/orientation, gradual northern town elevation, wilderness screening spurs, shaped cave rock and castle roofs/trim. Road planning considers slope. Native decoration source contains 264 trees, 216 plants, 72 rocks and 11 props, with native ground sampling and clearance around roads, actors, doors and landmarks. Current visual/runtime acceptance is pending; previous service/safety reports predate these changes.

### Native revision verification and lift floor

Brackenford exports75BModels/1390faces/563decorations, with exact native terrain and decoration records. Six focused scenarios pass: doors, topics, population, wilderness AI, town safety and two-map arrivals. Regional overview still leaves broad open ground between the landforms; further approach/terrain review remains. Castle and town close-ups show the new roof/footprint variety and garden clusters.

Static indoor furnishing objects initially disappeared because their prefix was not a compiler geometry category. Added STATIC_ with mandatory explicit room ownership, preserving native sector ownership even for overlapping rooms. Fifteen compiler tests/168assertions pass. Greywatch now has778faces/34native decorations/22lights; both native cutaways were inspected. The first separate trigger-floor experiment was rejected because it was not in the mover vertex set. The final platform mesh owns pressure event105 and moves as a single native door. Automatic boarding, stationary latch, saved mid-travel state, both landings and manual recovery pass24steps with the ordinary party. The old lower-landing test expected no automatic descent and failed as expected; its revised boarding test verifies the new behavior.

### Regional connections and current regression batch

Native west road leads to Ravenshore (1day), north road to Alvar (2days), arriving outside their existing stables. The isolated installation clones stable profiles for original houses452/453, retaining all old destinations and appending a daily Brackenford return. Brackenford retains Wayland's original scheduled routes. Paid Alvar/return fares42+63gold and native saves pass. Both boundary walks, immediate destination stable picking, returns and saved states pass. Native boundary travel consumes the shared5food cost. Navigation heading0 is an unspecified sentinel; explicit360faces east. The scenario driver now refreshes the normal movement/view hook after a map transfer before immediate picking. It also supports exact match_label for multiple visible actions sharing ID22.

review/travel_and_revision_checks.json passes all9scenarios against current hashes, including344seconds town safety and originalMM6/MM7/MM8exits. Further long approach, reward/shop/trap and final gameplay/presentation/package gates remain. Current cave close-up shows the repaired facade joining the native hillside; earlier gap images were rejected. Source library isolates each authored scene, then verify_blend.py --finalize produces a normal standalone mainfile. Independent opens have no linked libraries and all file textures packed.

## Native UI and reward persistence review

The current outdoor automap was baked in Blender and viewed in the native HUD. Added explicit map-local MM8 chest pools with 27 unit tests / 337 assertions passing. All 24 generated chests across three sessions per map have the intended fixed and random MM8 equipment; traps discharge once before opening for the ordinary Expert-disarm party. All eight actual held-item removals survive save/load, inventory placement and map revisit without duplicate rewards. The scenario adapter now uses actual shared held-item state, rather than only its derived query cache. Weapon purchase through native UI spends 127 gold for item 46; original house 2 and scoped house 12001 stock are independent. Native screenshot selection, remaining services/lifecycle/lighting checks and final handoff remain pending. Expanded art mounts now copy original files because PhysicsFS rejects child file symlinks.

## Ambient, lifecycle and native UI checks

All three shops complete actual UI purchases and persist bought items/enchantments. Chest snapshots retain removed rewards at335days and regenerate at337days, matching336day refill. The well resets after native UI Rest & Heal8hours and can grant25Might again. Obelisk inscription appears in the HUD. Greywatch had fully lit default sectors: added bounded source ambient metadata,16compiler tests/182assertions pass, and every occupied sector now uses reference value22. Controlled native torch-off/on and low/high Perception images show local illumination and red detection tint. See lighting_perception.json. Projectile traces revealed scenario movement/advanceRuntime skipped shared pending-combat processing; correction and affected regressions remain in progress.

## Shared simulation and approach revision

Movement and elapsed-runtime checks now consume real shared combat events: both plate projectiles damage the ordinary party by20HP.344seconds town safety still passes; original MM6/MM7/MM8 exits, transfers and stables pass. A post-dialog neutral shared frame fixes stale headless input gating on regional arrivals. The manual lift-route fixture predates automatic boarding and is superseded by greywatch_combat_lift.yml: six records/junction enemies defeated through normal combat, then gate opened and complete automatic lift roundtrip/recovery passes. Four watch mercenaries crossed the opened doorway and were defeated in the entrance test. Long west/north approaches pass; north climbs512units. Rejected flat cave front capture and replaced it with tapered faceted rock; only models65–68 change, native terrain and other71models/entities/spawns remain identical. New cave capture and both entrance checks pass.

## Final native routes, performance and package handoff — 2026-09-07

Both lower records stairs and the complete 24-riser shortcut pass in both directions with the ordinary party,
active actors and normal collision (58-step `greywatch_remaining_routes.yml`). The reverse stair fixture was
extended onto the landing so it no longer samples the party while descending the final step; ascent duration
accounts for step traversal. Earlier failures were fixture endpoint/timing assertions, not manual map repairs.

The four serial native 1600x1200 software-display captures use the same binary/settings/party. Inspected final
frames show real active gameplay. Median FPS: Brackenford 44.6, Ravenshore 40.0, Greywatch 43.9, Naga Vault 24.2.
This is a short workload sample, not isolated terrain cost or a hardware prediction.

Final outdoor source independently reopens in Blender with 693 objects and packed images, no external libraries.
The content archive contains 15 verified files and installs into a fresh matching-base mount. Both map entrances,
24 house doors and the scheduled stable trip pass against that installation. Corrupted content, traversal paths
and mismatched base hashes reject before content writes. The frozen `/tmp/openyamm-brackenford-playtest-final`
contains the copied executable/content and separately verified ordinary level25 starts. Current results/limitations
and exact hashes are indexed in ACCEPTANCE.md; README.md and REBUILD.md replace stale pending-work instructions.

## Facade calibration revision — 2026-09-07

Implemented smaller coherent facades, native door/window panels and service signs, no chimneys, a joined shop block and an off-road well. Matched residential repetition to Ravenshore: 15/5 versus 44/13 instances/forms. Native reimport and two normal game views inspected; quick source/wiring checks pass. New God starts load in `playtest-calibrated`; indoor unchanged. Details and evidence: [FACADE_REVISION.md](FACADE_REVISION.md).

## 2026-09-07 — settlement density

Driver accepted the house kit but rejected wide plot spacing. Measured Ravenshore house assemblies and separate Garrote
Gorge village/compound samples; confirmed stone paths inside the compound. Regrouped 24 doors/23 structures along shared
streets, with closer terrain shoulders, narrower dirt margins and relocated town population/gardens/well. Native gap
median 1,866 → 832; settlement envelope 214.9M → 92.0M square units. Inspected native game street and Blender native
overview; the new plan is still more regular than Ravenshore. Native readback and short static binding/clearance checks
pass; indoor hash unchanged. See [density revision](DENSITY_REVISION.md) for images and fresh God snapshot.

## 2026-09-07 — driver sketch composition

Replaced the regular street grid using `test_img/1221.png`: unequal loop, native diagonal half-tiles, smaller southern
lane, raised manor for existing Myles Greydawn, rotated raised temple, two wells, assembled native fountain and four
stat barrels. Added a local fountain handler (15 HP +15 mana, 40 shared uses/day); its focused Lua checks pass.
Source and native review caught an exposed manor foundation apron, corrected to follow recessed wings. The Blender
connection closed during an earlier minimap request; the driver restarted it and MCP resumed successfully. No original
world tables/events or indoor geometry were changed. Current sources/evidence: [SKETCH_REVISION.md](SKETCH_REVISION.md).

## 2026-09-07 — street frontage, tile corners and town infill

Addressed screenshots 1222–1230: direct street frontage for ordinary houses, rotated west-house movement, aligned
inn/manor/temple approaches, five additional inhabited buildings and native town gardens/rocks/trees. The real artwork
shows that X-corner transitions mean one dirt corner; the old selector used them for three. Independent bitmap-derived
native edge checks improve from 3,258 mismatches to zero, including dirt collars at river/rock/road interfaces.
Ordinary door-to-shared-road-cell-center median improves from 688 to 371 units. Native house bindings and clearances
pass; three native Blender views and two eye-height gameplay images were opened and inspected. In the court game view,
foliage fills gaps between the new houses while the fountain remains accessible; the northern game view shows the short
doorstep-to-stone verge. No engine changes or broad outdoor scenario suite. Both new God starts reload in the frozen
`/tmp/openyamm-brackenford-playtest-frontage` snapshot. Blender MCP remained connected. See [FRONTAGE_REVISION.md](FRONTAGE_REVISION.md).

## 2026-09-07 — Wilderness calibration and revision

Compared Ravenshore regular spawn markers with conditional invasion actors, measured wolf patch and centaur spacing,
entrance guarding, and local scenery coverage against Ravage Roaming, Shadowspire and Brackenford. Added the reusable
wilderness guide, focused Ravage Roaming study, source-hashed measurements and same-scale plans; linked the lessons
from the main workflow, reference notes, brief and review checklist.

Authored 73 hostiles in 11 areas, preserving town/arrival positions and deliberate quiet regions. Broadened woodland and
rock coverage, added a native meadow pond, changed bridge parapets to timber rails, reduced the dirt-matched cave collar
and moved one existing chest beside its approach. Source inspection corrected ten pond corner seams before final
export. A native/normal-game visual iteration corrected the first cave's oversized contrasting mass and sloped chest.

Quick native checks pass; no extended outdoor scenario suite or engine changes. Refreshed packed Blender source,
automap, content ZIP and `/tmp/openyamm-brackenford-playtest-wilderness` with verified God starts.
See [WILDERNESS_REVISION.md](WILDERNESS_REVISION.md) for measurements, captures, hashes and balance limitations.

## 2026-09-07 — Landscape detail and bridge contact

Inspected driver images1236–1242 and native Ravenshore/Alvar terrain/detail and interactive-decoration families.
The earlier bridge gate missed buried banks; full-span triangle sampling and approach profiles now cover the defect.
First revised render exposed overlapping stone/timber tops; corrected abutments and added native nonoverlap checks.
Added sparse compatible stone/grass detail variants, eleven irregular soil patches, town-side tree/rock groups,
six rough-yard refuse heaps, two buff pedestals, one high-tier challenge with a stone border, and humanoid campfires/
cauldron. All102fixedactor positions and accepted town/arrivals preserved. Native87models/3880faces/1166decorations.
Zero tile-corner mismatches; native identity/clearance checks pass in seconds. Six Blender views and three normal-game
captures opened; independent packed Blender reopen and both fresh God starts verified. MCP remains connected.
Ravenshore/Alvar/before/after heatmaps explain local coverage rather than equating global counts. Updated shared
README/calibration/checks/templates and case studies. See [LANDSCAPE_REVISION.md](LANDSCAPE_REVISION.md);
new frozen launcher `/tmp/openyamm-brackenford-playtest-landscape/play.sh outdoor`.

## 2026-09-07 — Regional transition scenery

Driver images1243–1248 prompted native Ravenshore/Alvar edge inspection. Actual travel bounds are inside the rendered
heightfield: original roads continue 8,089–9,625 units beyond the prompts; Garrote's bent valley road ends before the
mesh edge. Added six native reference renders, annotated plans, source-hashed measurements and regional-transition
agent guidance. Brackenford west/north roads now continue 8,192 units beyond their triggers to the mesh, through bent
terrain cuts. Inner heights, all native BModels/entities and accepted arrivals/population are identical to landscape.
Quick road/tile/grade/sightline and frontage checks pass, zero seams. Normal-game forward steps show correct Ravenshore
and Alvar prompts with visible onward bends and screened distant endings. Packed Blender reopen, package integrity and
both God-start reloads pass. See [TRANSITION_REVISION.md](TRANSITION_REVISION.md). New frozen launcher:
`/tmp/openyamm-brackenford-playtest-transitions/play.sh outdoor`. MCP remains connected; default scene restored.

## Driver clarification — exit style is optional

Roads must continue beyond travel prompts, but they need not curve or pass between mountains/hills. Straight open
connections across flat or rolling land are valid. Updated the shared guide, README, checklists, brief and case-study
notes; Brackenford's accepted passes are one example, and their occlusion check is project-specific.

## 2026-09-07 — Cave and camps remain off-road

Driver1249 marks unwanted wilderness roads. Removed cave_trail/east_cache_trail/south_cache_trail and restored82
exclusive road cells to natural terrain; retained every other road path exactly, including castle/regional approaches.
All heights/BModels, actors, chests, loose items and arrivals preserved. Releasing former road clearances changes38
ordinary decoration records; total1166 and native special markers remain stable. Updated road-purpose guidance.
Quick readback/tile/frontage checks pass, zero seams; fixed historical palette lookup in the comparison checker.
Minimap and two written-map wilderness views inspected, packed Blender reopened, verified ZIP and both God starts
reloaded. See [ROAD_PURPOSE_REVISION.md](ROAD_PURPOSE_REVISION.md). Fresh snapshot:
`/tmp/openyamm-brackenford-playtest-offroad/play.sh outdoor`. MCP connected; unrelated Scene restored.
