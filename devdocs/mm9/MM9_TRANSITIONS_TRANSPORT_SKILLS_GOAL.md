# MM9 Transitions, Transport, And Skill Services Goal

## Status

**Checked 2026-11-06 on the review root (`output/mm9_rework/assets_dev`).**

- Map exits: `map_transitions.txt` (105 rows, 44 source maps) names only maps that exist. The positioned-transition
  runtime runs indoors and outdoors (confirmation, cancel without retrigger, travel days). All 31 rebuilt indoor maps
  pass their `scenario_doors_exits.yml`; Wizard's Lab has exits but no scenario. Of the 46 exits from outdoor maps, 38
  pass `--headless-verify-mm9-positioned-transition` (it needs `--world mm9`, else it cannot find MM9's table); 7 never
  asked for confirmation and Isle of Ashes object 485 retriggered while the party stood inside. Those outdoor maps are
  being rebuilt as open-air BLVs (`devdocs/mm9_rework/OUTDOOR_BLV_ALL.md`), whose converter rewrites their exit rows
  and boat arrivals (`outdoor_blv.py rewrite_transport`) as each map installs; recheck the outdoor exits after that.
- Dock travel stays in the MM9 talk (user decision 2026-11-06): a dock's passage row (one click from the NPC's first
  menu, e.g. Annud's "We'd like passage.") offers today's boat and a **Schedule** row, which opens the shared transport
  Schedule popup (`GameplayTransportSchedule`, centred over the talk) with the dock's week from `transport_routes.txt`
  (`buildMm9TransportSchedule`): a later departure waits for its day and eats a food a day, as at MM6-MM8 docks.
  Route conditions (raw quest keys, NPC 209's ice) apply to both. The routes' MM9 day index now follows the shared
  calendar (Monday is MM9's day 2), so a dock sails its Monday boat on the day the game calls Monday; before, it sailed
  the Saturday boat then.
- Walking between regions (user decision 2026-11-06): an exit with days on the road whose maps are both top-level
  areas in map_stats (area 0; `mm9RegionWalk`), such as Sturmford to Drangheim, is MM6-MM8's journey between outdoor
  maps: it costs `Mm9RegionWalkFood` (5) food whatever its days, guides shorten the road, and the dialogue reads "It
  will take 2 days to travel to Drangheim." / "Do you wish to leave Sturmford?". Other exits with days (Yorwick into
  the Connecting Tunnels) state their days and cost a food a day. On the main assets mid-conversion, the converted
  regions' exit volumes do not yet meet the new geometry (Sturmford object 25 floats about 400 units above the road;
  Mountain Pass object 122 lies off the map), so this was checked by unit tests, not in play.

The original plan follows.

Planned from a source and runtime audit. MM9 DAT import already discovers positioned exit volumes, MM9 item import
already emits most Normal-skill books, and RUDE import already exposes travel and mastery-training service opcodes.
Those records are not yet connected end to end to shared OpenYAMM map-transition, transport, shop, or mastery-training
systems.

This goal is complete only when an MM9 party can:

- enter every valid DAT-defined map exit, confirm or cancel it when requested, and arrive at the correct destination;
- open and pass through city gates without conflating the gate mechanism with the exit volume;
- use every source-supported dock route with the correct schedule, conditions, cost, and elapsed time;
- acquire every permitted MM9 Normal skill through its source skill book or source map pickup;
- train every permitted MM9 skill to every source-supported mastery through the assigned teacher; and
- save, load, remount, and revisit maps without duplicated transitions, missing teachers, repeated charges, or stale
  dialogue state.

The implementation must remain world-scoped. When MM9 is not mounted, these content records add no meaningful
startup, map-loading, update, or memory cost.

## Objective

Convert MM9's original transition and skill-service definitions into explicit OpenYAMM world contributions while
reusing shared gameplay systems.

The source information is distributed across several formats rather than one complete table:

| Concern | MM9 source |
| --- | --- |
| Positioned map exits | DAT `ExitTrigger` objects and their properties |
| Gate movement and activation | DAT Door/Trigger objects and assigned SCR behavior |
| Destination arrival | Named DAT start-point objects in the destination map |
| Dock service identity | `MMIXSHOPS.txt` and the dock NPC/RUDE binding |
| Dock service invocation | RUDE service opcode `-5` |
| Dock availability and quest gates | RUDE conditions and required dialogue-linked SCR |
| Normal skill acquisition | `MASTERITEMLIST.csv`, `SKILLBOOK.scr`, Libraries, and placed skill-book props |
| Mastery training | RUDE service opcode `-4`, teacher RUDE rows, and `NPC998.rude` teacher hints |
| Teacher presence | DAT actors plus mundane-town SCR schedules |
| Class/race eligibility | Shared OpenYAMM class and race skill caps |

Do not force all of this information into `map_stats.txt`, `house_data.txt`, generated event Lua, or one oversized
MM9-specific runtime structure. Generate or author narrowly owned world tables and compose them through the mounted
content package.

## Non-Negotiable Architecture

- Keep MM9 geography, routes, teachers, service bindings, and source overrides under `assets_dev/worlds/mm9/`.
- Reuse `EventRuntimeState::PendingMapMove`, transition confirmation, shared map loading, transport side effects,
  shared item use, class/race skill caps, and `MasteryTeacherDialog` behavior.
- Do not add an MM9 map loader, party skill store, transport clock, dialogue runner, or save subsystem.
- Do not encode positioned MM9 exit volumes as rectangular MapStats boundary transitions.
- Do not make a gate door itself change maps unless its source behavior explicitly requests a transition. In the
  ordinary MM9 city-gate pattern, the door opens and a separate `ExitTrigger` beyond it changes maps.
- Do not treat a Training Arena as a Normal-skill school or mastery teacher. MM9 Training Arenas train character
  levels; Libraries distribute Normal-skill books; named NPC teachers raise mastery.
- Do not directly edit generated map Lua, scene YAML, `events.yml`, or `raw_objects.yml`. Fix the importer/generator or
  use an explicit narrow source override that survives regeneration.
- Do not infer a destination, schedule, price, teacher, or source typo correction from proximity or English prose
  when the source does not establish it. Emit an unresolved audit record and require a reviewed override.
- Retain original map object indexes, RUDE ids, shop ids, item ids, keys, source names, and source-file provenance in
  generated data and diagnostics.
- Validate canonical ids and target references during content composition. Do not add broad runtime fallbacks for
  stale or incomplete generated state.
- Implement shared behavior for indoor and outdoor scenes through common runtime ownership, with world-specific hooks
  limited to spatial representation, picking, collision, mechanisms, and map-local object lookup.

## Source Authority

Use local sources in this order.

### DAT map exits and mechanisms

1. The original extracted DAT object, including class, object index, name, transform, dimensions, properties,
   parameters, and assigned script.
2. The destination DAT's named start-point objects.
3. The assigned SCR and its required reachable behavior for mechanism activation or visibility.
4. The generated raw-object and event discovery data as reproducible importer output, not independent authority.
5. A reviewed MM9 source override for a proven typo or unresolved destination.

### Transport

1. Original dock/shop identity and NPC binding from `MMIXSHOPS.txt`.
2. RUDE service rows, conditions, and dialogue-linked SCR behavior.
3. Recoverable original route/schedule behavior from local MM9 references or executable-backed research.
4. A reviewed authored MM9 route overlay with explicit provenance when the extracted tables do not carry the route
   matrix.

The shop table proves that a service is a Dock, but it does not prove a route destination or weekly schedule. Do not
invent routes from settlement proximity, loading strings, or the order of dock rows.

### Skills and teachers

1. `SKILL AND MASTERY DESC.csv` for the MM9 skill catalogue and behavior description.
2. `MASTERITEMLIST.csv` and `SKILLBOOK.scr` for Normal-skill book identity and operations.
3. Individual `NPC*.rude` service rows for actual trainer operations and conditions.
4. `NPC998.rude` as the canonical teacher-location cross-check.
5. Town mundane-task SCR for dynamically scheduled teacher presence.
6. `MM9_RUDE_SCR_INTEGRATION.md` and shared OpenYAMM skill names/caps as the target operation contract.

MMerge and the local OpenEnroth checkout are behavioral and structural references for shared skill, mastery,
transition, and transport mechanics. They do not override MM9 teacher geography, source item identity, or route data.

## Audited Baseline

The checked-in audit generator must reproduce or deliberately explain changes from this provisional baseline.

### Exit triggers

- 45 imported MM9 maps were inspected.
- 105 `ExitTrigger` objects occur across 44 source maps.
- Every object carrying `DestinationWorld` is an `ExitTrigger`; no other observed DAT class directly owns a
  destination-world property.
- All 105 destination map names resolve.
- 103 of 105 destination start-point names resolve case-insensitively.
- 101 triggers request player confirmation and four do not.
- 84 exported `TravelDays` values are zero.
- 21 exported values currently expose float bit patterns through an unsigned-integer decode. The observed semantic
  values include the `-1.0` sentinel and positive day counts 1, 2, 3, 4, 5, 6, and 8.

The two currently unresolved arrivals are:

| Source | Destination | Source start-point name | Required disposition |
| --- | --- | --- | --- |
| Arslegard City | Dark Passageway | `StartPoint0` | Review an explicit correction to the target's `StartPoint` |
| Arslegard City | Thjorgard | `SkyStart0` | Determine intended arrival; do not guess |

These are explicit content defects or ambiguities, not permission for a runtime "closest start point" fallback.

### Gates

Guberland City is the required gate/exit acceptance example. Its imported source contains:

- paired gate-door mechanisms such as `Gate8L` and `Gate8R`;
- named mechanism triggers such as `Gate8trigger`; and
- an independent `ExitTrigger` volume leading to the adjacent map.

Opening or activating the gate must preserve the door mechanism behavior. Crossing the exit volume after the gate is
open must request the map transition. Clicking the gate must not teleport the party merely because an exit volume is
near it.

### Transport services

`MMIXSHOPS.txt` identifies seven Dock services:

| NPC id | Dock |
| ---: | --- |
| 18 | Sea's Fang |
| 60 | Dragon Passage |
| 103 | The Black Hammer |
| 144 | The Flying Bird |
| 209 | The Racing Fire |
| 257 | The Raider |
| 288 | The Dragon |

The corresponding RUDE selections invoke service opcode `-5`. The extracted shop rows identify the service hosts but
do not contain a complete destination/day/price schedule. The final route inventory must therefore distinguish
source-proven routes from reviewed recovery data.

NPC 209 is a required conditional-service case. Its ice-block/key behavior and dock-schedule reward must remain
effective; implementing the travel menu must not bypass its RUDE/SCR conditions.

### Skills and services

MM9 declares 23 skills:

- combat: Blade, Cudgel, Spear, Bow, Thrown Weapons, Armsmaster, Unarmed, Armor, Shield, and Dodging;
- magic: Elemental, Light, Dark, Spirit, and Meditation; and
- utility: Disarm Trap, Merchant, Perception, Repair Item, Identify Item, Identify Monster, Body Building, and
  Learning.

Normal skills are learned from skill books. Training Arenas are level-training services, not skill-learning halls.
The six source Libraries are Ancient Scrolls, Egil's Rare Books, The Light of Life, Halfdan's Books, Public Library,
and The Bored Reader.

The current item import emits 22 source skill books and connects them to `LearnSkill`. Source item 285, Blade Skill,
is named by `SKILLBOOK.scr` but absent from `MASTERITEMLIST.csv`; items 286 through 307 cover the other 22 skills.
Blade therefore requires an explicit reviewed MM9 item-source override rather than silent omission.

The RUDE audit found:

- 115 mastery-training service rows using opcode `-4`;
- 69 trainer NPCs; and
- coverage of all 23 skills and their source-supported Expert, Master, and Grandmaster assignments.

Teacher geography follows these groups:

| Skill group | Skills | Expert/Master regions | Grandmaster region |
| --- | --- | --- | --- |
| Combat weapons | Blade, Cudgel, Spear, Bow, Thrown, Armsmaster, Unarmed | Sturmford and Drangheim | Thjorgard |
| Combat defense | Armor, Shield, Dodging | Sturmford and Drangheim | Thjorgard |
| Magic | Elemental, Light, Dark, Spirit, Meditation | Guberland and Thronheim | Lindisfarne |
| Utility services | Disarm, Merchant, Perception, Repair | Thjorgard and Frosgard | Yorwick |
| Utility knowledge | Identify Item, Identify Monster, Body Building, Learning | Thjorgard and Frosgard | Yorwick |

Required named examples are:

- Armsmaster Expert/Master: Adotette Haji, NPC 390, and Krej Matlal, NPC 124;
- Armsmaster Grandmaster: NPC 39 in Thjorgard. Source name variants such as Chera Papan and Cihu'aton Pa'pan must be
  retained as provenance but resolve to one teacher identity keyed by NPC id 39;
- Body Building Expert/Master: Toman Yatol, NPC 38, and Lansa Akin, NPC 233; and
- Body Building Grandmaster: Stev Palac, NPC 412, in Yorwick.

Some Grandmasters are not static DAT scene actors. Yorwick's mundane-task script schedules Stev Palac in a rotating
teacher group, and equivalent scheduling affects other town teachers. A trainer record must not synthesize an actor;
teacher placement and availability belong to the map actor/schedule import path.

## Generated Map-Transition Contribution

Add a world contribution with a final name chosen consistently with the table registry, provisionally:

```text
assets_dev/worlds/mm9/data_tables/map_transitions.txt
```

Generate it deterministically from DAT discovery data plus reviewed source overrides. Each record must carry data
equivalent to:

| Field | Meaning |
| --- | --- |
| canonical id | Namespaced stable transition identity |
| source map | Canonical source map id |
| source object index | Original DAT object identity |
| source name/class | Source provenance and diagnostics |
| center/half-extents | Runtime trigger volume in OpenYAMM coordinates |
| destination map | Canonical mounted destination id |
| source start-point name | Original MM9 destination reference |
| resolved arrival | Destination x/y/z and facing resolved at generation time |
| ask player | Whether confirmation is required |
| travel days | Normalized value or explicit source sentinel |
| loading presentation | Source loading screen and text references when supported |
| override/provenance | Generated source and any reviewed correction |

Resolve arrival coordinates during generation/content composition. The source map's runtime must not load or parse the
destination map's generated Lua merely to locate a start point.

The manifest contribution must be validated like other mounted tables. Duplicate canonical ids, duplicate source
object ownership, unresolved maps, unresolved required start points, invalid volumes, and unsupported required
properties are content errors.

## Positioned-Transition Runtime

Build a compact per-loaded-map spatial index from the mounted transition contribution. The shared scene/gameplay path
must:

1. Detect the party entering an active transition volume.
2. Trigger only on outside-to-inside entry, not every update while standing in the volume.
3. Respect source visibility, enablement, and required mechanism/script state.
4. Open the shared confirmation dialogue when `AskPlayer` is true.
5. Leave the party in the source map when canceled.
6. Produce the shared `PendingMapMove` when confirmed or when confirmation is not required.
7. Apply normalized travel-time side effects exactly once.
8. Record a map-transition trace with a source kind such as `mm9_exit_trigger` and the stable source object identity.
9. Arrive at the resolved target position and facing without immediately retriggering the reciprocal exit.

Transition overlap state is transient and map-local. Save/load must not serialize pointers or generated index slots.
Loading a save inside a trigger must not repeatedly open confirmation each frame; the party must leave and re-enter or
the runtime must establish an equivalent safe entry-state rule.

Use the same behavior for indoor and outdoor MM9 maps. Only the scene-specific party-overlap query may differ.

## Transport-Route Contribution

Add a separate world contribution, provisionally:

```text
assets_dev/worlds/mm9/data_tables/transport_routes.txt
```

Each route must carry data equivalent to:

- canonical route id;
- source dock NPC and shop id;
- destination display name and canonical map id;
- destination named start point and resolved arrival;
- available weekdays or equivalent schedule predicate;
- base travel days and price inputs;
- required/forbidden MM9 QBits and other validated service conditions;
- route ordering for dialogue presentation;
- source/recovery provenance; and
- an explicit confidence/review state for behavior not present in extracted TXT tables.

RUDE opcode `-5` must open the shared transport dialogue for the current dock. Route selection must reuse shared price,
availability, time advancement, party-rest, confirmation, trace, and `PendingMapMove` behavior where those mechanics
match MM9. MM9-specific route conditions belong in the world route contribution or compiled RUDE/SCR predicate, not
hardcoded NPC-id branches in the shared transport UI.

The route generator/audit must report every Dock with zero routes, every route with an unresolved destination, every
unreachable route, and every route whose schedule or price provenance remains unresolved.

## Normal-Skill Books And Libraries

Keep Normal skill learning item-driven. The existing MM9 item contribution remains authoritative for imported skill
books.

Complete the path by:

- adding a reviewed source override for missing item 285, Blade Skill;
- preserving its source id and documenting that `SKILLBOOK.scr`, rather than `MASTERITEMLIST.csv`, supplies the
  identity;
- mapping Blade atomically to Sword and Dagger;
- implementing the MM9 Library/shop service so source skill books can enter purchasable stock;
- converting placed `SkillBook.scr` props, including the Ta'Sar Academy objects, into actual item pickups or supported
  searchable sources when their source behavior requests it; and
- retaining ordinary class/race cap checks and already-known-skill handling through shared item-use logic.

Do not make all books globally available at every Library unless the recovered source stock behavior proves that
policy. Random or tiered stock must be represented as content data and use the shared shop generator where possible.

## Mastery-Trainer Contribution

Add a world-owned trainer/service contribution, provisionally:

```text
assets_dev/worlds/mm9/data_tables/skill_trainers.txt
```

Generate records from actual RUDE `-4` service rows and cross-check them against `NPC998.rude`. Each record must retain:

- stable trainer-service id;
- RUDE id and source row index;
- teacher key/topic when present;
- canonical MM9 skill or composite skill group;
- requested mastery;
- required skill rank and cost inputs;
- required and forbidden QBits or other validated conditions;
- expected source map/region for audit purposes;
- source display-name variants; and
- complete source provenance.

RUDE service selection must query this contribution and invoke shared mastery eligibility and application logic. A
teacher row is available only when the active character:

- knows the complete direct or composite skill group;
- has the required rank;
- has not already reached that mastery or higher;
- is permitted that mastery by the shared class/race cap;
- satisfies the row's MM9 dialogue conditions; and
- can pay the single source-defined charge.

Superseded for trainers by the user's decision of 2026-11-05 (`MM9_RUDE_SCR_INTEGRATION.md` "Skills And Mastery"):
each MM9 trainer teaches every separate skill on its own, with no composite transaction. The original plan follows.

Composite skills follow `MM9_RUDE_SCR_INTEGRATION.md`:

| MM9 skill | Shared OpenYAMM operation |
| --- | --- |
| Blade | Sword and Dagger |
| Cudgel | Mace |
| Armor | Leather Armor, Chain Armor, and Plate Armor |
| Elemental | Fire Magic, Air Magic, Water Magic, and Earth Magic |

Learning or raising a composite group is one atomic transaction. It is charged once, never lowers any member, and
fails without mutation when the complete group cannot be granted. Do not partially train a group and then report
failure.

## Teacher Presence And Scheduling

Trainer-service data answers what an existing NPC teaches; it does not own actor creation or placement.

Coordinate with `MM9_SCRIPTED_ACTOR_IMPORT_GOAL.md` or its resulting map actor-profile system to import the required
mundane-town teacher schedules. The combined implementation must ensure:

- every trainer referenced by an available service can appear in the correct source town;
- rotating groups preserve their source availability policy;
- actor identity remains keyed by map/source-object identity and RUDE id where appropriate;
- save/load and time advancement select the same deterministic schedule state; and
- missing scheduled actors appear in the coverage audit rather than being replaced by permanently spawned copies.

Teacher display-name inconsistencies must resolve through id aliases/provenance. They must not create duplicate NPCs or
duplicate trainer services.

## Import And Implementation Phases

### Phase 0: Reproducible Audits

Add deterministic audit output for:

- all DAT `ExitTrigger` objects and destination resolution;
- DAT objects carrying destination properties but not owned by the expected class;
- TravelDays raw type/value decoding;
- gate mechanisms adjacent or linked to exits, without assuming ownership;
- all Dock services and recovered routes;
- all MM9 skill books and Library/placed-book acquisition paths;
- every RUDE `-4` and `-5` service row;
- trainer cross-checks against `NPC998.rude`; and
- trainer NPC presence, static placement, or schedule ownership.

Audit output must be stable and suitable for regression tests. Summary counts alone are insufficient; every unresolved
record needs source identity and a reason.

### Phase 1: Content Schemas And Composition

- Define table schemas for positioned transitions, transport routes, and skill trainers.
- Register the corresponding world contribution types.
- Generate source-proven records and keep reviewed overrides separate.
- Validate ids, maps, start points, source ownership, and references at composition time.
- Add unit coverage for parsing, overlay precedence, duplicate detection, and unmounted-world behavior.

### Phase 2: Positioned Map Exits

- Fix TravelDays property decoding.
- Resolve or explicitly override the two destination-start discrepancies.
- Add the per-map spatial index and common enter/debounce behavior.
- Connect confirmation, travel side effects, trace data, and `PendingMapMove`.
- Validate Guberland City gate separation and representative indoor/dungeon exits.

### Phase 3: Dock Travel

- Recover and review the complete MM9 dock route matrix.
- Connect RUDE `-5` to shared transport presentation and execution.
- Preserve RUDE/SCR conditions, including NPC 209's blocked-service behavior.
- Validate cost, day availability, elapsed time, destination, insufficient-gold behavior, and save/load.

### Phase 4: Normal Skills And Mastery

- Add the Blade Skill source override.
- Make Library skill-book stock and placed books reachable.
- Generate the complete trainer contribution.
- Connect RUDE `-4` to shared mastery training.
- Validate every direct and composite skill, cap, rank, charge, and already-trained result.

### Phase 5: Scheduled Teachers

- Import the required town teacher schedules through the authoritative actor/map profile path.
- Validate Yorwick and Lindisfarne Grandmasters in addition to static trainers.
- Ensure service records never spawn or permanently pin scheduled actors.

### Phase 6: Exhaustive Coverage And Packaging

- Regenerate MM9 content from source.
- Run complete route, transition, book, trainer, and actor-presence audits.
- Exercise representative indoor and outdoor paths headlessly.
- Verify save/load and mounted/unmounted behavior.
- Package the MM9 world and verify no MM6/MM7/MM8 table or gameplay regression.

## Required Tests

### Pure/unit coverage

- DAT TravelDays decoding, including zero, positive days, and the `-1.0` sentinel.
- Transition table parsing, coordinate conversion, id stability, and destination resolution.
- Override application for a named source object without broad fallback behavior.
- Transition enter/debounce/cancel/confirm state transitions.
- Transport schedule availability and route lookup by dock service.
- Trainer generation from RUDE rows and `NPC998.rude` cross-check diagnostics.
- Direct and composite skill eligibility and atomic application.
- Single-charge behavior for composite training.
- Class/race mastery-cap rejection without partial mutation.
- Blade book override and all 23 Normal-skill mappings.
- World contribution absence when MM9 is not mounted.

### Focused runtime/headless coverage

- Open a Guberland City gate, cross its exit volume, cancel once, then confirm and arrive at the named start point.
- Remain inside an exit volume for several updates without repeated confirmation.
- Load a save inside or immediately beside a transition volume without a transition loop.
- Use an automatic `AskPlayer=false` transition exactly once.
- Traverse representative outdoor-to-city, city-to-outdoor, outdoor-to-dungeon, and dungeon-to-outdoor exits.
- Select an available boat route and verify gold, elapsed days, party state, trace, map, and arrival.
- Reject an unavailable-day route and an unaffordable route without charging or moving.
- Verify NPC 209's service remains blocked/unblocked by its source conditions.
- Buy and use Armsmaster and Body Building books with eligible and ineligible characters.
- Acquire and use the Blade book, learning Sword and Dagger atomically.
- Train Armsmaster through an Expert/Master teacher and NPC 39 as Grandmaster.
- Train Body Building through Toman Yatol or Lansa Akin and Stev Palac as Grandmaster.
- Train Armor and Elemental as atomic composite mastery groups.
- Advance time/save/load around Yorwick's rotating teacher schedule and retain deterministic availability.

### Regression coverage

- Existing MM6/MM7/MM8 boundary transitions, Lua `MoveToMap`, house entry, boats, and stables remain unchanged.
- Existing direct and composite-independent OpenYAMM skill learning and mastery teachers remain unchanged.
- MM9 tables do not override global MMerge-owned skills, items, houses, or maps outside declared contributions.
- Mounting no MM9 world performs no MM9 exit-volume scan, RUDE trainer lookup, or teacher-schedule update.

## Completion Gates

This goal is complete only when all of the following are true:

- every source DAT exit has one generated disposition: supported, explicitly overridden, or intentionally unsupported
  with a reviewed reason;
- all supported exits work through shared transition confirmation and `PendingMapMove`;
- the two currently unresolved start points have reviewed, documented dispositions;
- TravelDays values are decoded semantically and no bit-pattern integers enter runtime content;
- gates retain mechanism behavior independently of nearby exit volumes;
- every Dock has a reviewed route inventory and every reachable `-5` row performs a real service or gives a specific
  source-correct unavailable result;
- all 23 Normal skills have a source-backed acquisition path, including Blade item 285;
- every reachable `-4` row invokes real shared mastery behavior;
- direct and composite skill transactions respect rank, cost, already-known state, and class/race caps;
- all referenced teachers can exist under their source placement/schedule rules;
- audit reports have no unexplained duplicate, missing-map, missing-start, missing-route, missing-book, missing-teacher,
  or unbound-service records;
- representative transition, transport, skill, scheduled-teacher, save/load, and package-mount tests pass; and
- relevant MM6/MM7/MM8 transition, transport, dialogue, item-use, mastery, startup, and map-load regressions pass.

Passing compilation or displaying a service name is not completion. A service is complete only when its validated
action is reachable, mutates shared gameplay state correctly, survives save/load, and is covered by reproducible
source-to-runtime evidence.

## Out Of Scope

- Implementing a general MM9 SCR virtual machine.
- Adding MM9-only skill enums, mastery levels, spell identities, or a second class-cap model.
- Replacing shared MM6/MM7/MM8 MapStats boundary travel with MM9 volume semantics.
- Reconstructing unrelated MM9 NPC daily life, combat AI, or quest behavior beyond what is required to make the
  identified transition and service actors function.
- Treating English dialogue or journal prose as authoritative executable route or trainer data.
- Permanently spawning all scheduled teachers as a shortcut.
- Hand-editing generated Lua or map YAML to make individual exits, gates, books, or teachers work.
