# Scenario Runner Implementation Plan

This document describes the concrete implementation plan for the headless YAML scenario runner used to prove MM6,
then reuse the same runner for MM7/MM8. The runner should stay intentionally scoped under `game/scenario/*` as much as
possible. Integration outside that directory should be limited to CLI dispatch, CMake source registration, and small
runtime hooks where an existing gameplay operation is not externally driveable yet.

The runner is not a second gameplay engine. It is a deterministic test driver over the real OpenYAMM runtime:
world mounting, map loading, party state, interaction picking, dialogue topics, events, inventory, chests, corpses,
mechanisms, time, save/load, and endings.

## Goals

- Consume scenario YAML and execute long playthrough routes in headless mode.
- Prove route milestones with real gameplay state, not hardcoded quest completion.
- Keep route files reusable across MM6/MM7/MM8 via scenario data and aliases.
- Allow explicit, audited shortcuts for travel, combat, training, and setup in `hybrid` scenarios.
- Produce useful failure output: failed step, source line, current map, expected state, actual state, latest checkpoint.
- Keep normal runtime performance unchanged. Scenario code is only active from headless CLI commands.

## Non-Goals

- Do not replay every frame or mouse movement from a real play session.
- Do not add campaign-specific C++ logic such as `completeKilburnQuest()`.
- Do not create a second event/dialogue/inventory implementation.
- Do not require rendering unless a step explicitly asks for real picking from screen coordinates.
- Do not hide missing data/assets with compatibility fallbacks.

## CLI Surface

Add the following headless commands in `game/app/main.cpp`:

```bash
./build/game/openyamm --headless-run-scenario tests/scenarios/mm6/main_story.yml
./build/game/openyamm --headless-run-scenario-suite tests/scenarios/mm6
./build/game/openyamm --headless-validate-scenario tests/scenarios/mm6/main_story.yml
```

Optional flags should be parsed after the command:

```bash
--scenario-filter tag=p0
--scenario-filter id=mm6.council.kilburn
--scenario-stop-after-checkpoint council_complete
--scenario-start-from-checkpoint council_complete
--scenario-report-json /tmp/openyamm-scenario.json
--scenario-report-junit /tmp/openyamm-scenario.xml
--scenario-artifacts-dir /tmp/openyamm-scenario-artifacts
--scenario-strict-shortcuts
--scenario-dry-run
```

Initial implementation can support only:

```bash
--headless-run-scenario <file>
--headless-validate-scenario <file>
--scenario-dry-run
--scenario-artifacts-dir <dir>
```

The CLI entry point should instantiate `ScenarioHeadlessCommand`, not add more code to
`HeadlessOutdoorDiagnostics.cpp`.

## File Layout

```text
game/scenario/
  ScenarioAliasRegistry.h/.cpp
  ScenarioAssertionEngine.h/.cpp
  ScenarioCommandLine.h/.cpp
  ScenarioDocument.h
  ScenarioDrivers.h/.cpp
  ScenarioHeadlessCommand.h/.cpp
  ScenarioReport.h/.cpp
  ScenarioRunner.h/.cpp
  ScenarioStep.h/.cpp
  ScenarioValue.h/.cpp
  ScenarioYamlLoader.h/.cpp

tests/scenarios/
  schema/
    test_scenario.schema.yml
  mm6/
    aliases.yml
    main_story.yml
    council.yml
    oracle.yml
    promotions.yml
    fixtures/
```

Register the new C++ sources in `game/CMakeLists.txt`. `yaml-cpp` is already linked by `openyamm`, so the runner can use
it directly.

## Existing Integration Points

Use these existing systems rather than duplicating behavior:

- `game/app/main.cpp`: add CLI dispatch.
- `game/app/GameApplication.*`: use for full app/session runtime where a step needs screen/runtime behavior.
- `game/data/GameDataLoader.*`: use for base data and map loading.
- `game/gameplay/GameplayScreenRuntime.*`: access party, UI state, dialogue, held item, overlays.
- `game/gameplay/GameplayInteractionController.*`: drive normal interact semantics.
- `game/gameplay/GameplayDialogController.*` and `HouseInteraction.*`: drive dialogue/house topics.
- `game/events/EventRuntime.*`: execute event programs and inspect qbits/mechanisms.
- `game/indoor/*WorldRuntime.*` and `game/outdoor/*WorldRuntime.*`: map-local hooks, runtime updates, party pose.
- `game/maps/SaveGame.*`: save/load checkpoint state once available through app/session helpers.
- `game/outdoor/HeadlessOutdoorDiagnostics.cpp`: reference for helper patterns only. Extract small reusable helpers if
  needed; do not keep growing that file.

## Architecture

### `ScenarioHeadlessCommand`

Owns command-level orchestration.

Responsibilities:

- Parse scenario CLI options already split by `main.cpp`.
- Create `Engine::AssetFileSystem`.
- Create and configure headless `GameApplication` or lower-level data loader session.
- Force dummy audio/video-safe settings where existing headless commands do.
- Load and validate YAML.
- Run one scenario or a suite.
- Return process exit codes:
  - `0`: success.
  - `1`: scenario assertion/runtime failure.
  - `2`: CLI/schema/config error.

Suggested API:

```cpp
class ScenarioHeadlessCommand
{
public:
    explicit ScenarioHeadlessCommand(const Engine::ApplicationConfig &config);

    int runScenario(const std::filesystem::path &basePath, const ScenarioCommandLine &commandLine) const;
    int validateScenario(const std::filesystem::path &basePath, const ScenarioCommandLine &commandLine) const;

private:
    Engine::ApplicationConfig m_config;
};
```

### `ScenarioYamlLoader`

Converts YAML into typed scenario documents while preserving source locations where practical.

Responsibilities:

- Parse YAML with `yaml-cpp`.
- Validate top-level fields: `id`, `world`, `mode`, `steps`.
- Convert each step into `ScenarioStep`.
- Preserve source file and approximate line/step index for diagnostics.
- Reject unknown step types unless `allowUnknown` is set for draft conversion experiments.

Avoid implementing a full JSON-schema engine in phase 1. A small explicit validator is enough.

### `ScenarioDocument`

Plain data model for a loaded scenario.

```cpp
enum class ScenarioMode
{
    Faithful,
    Hybrid,
    Unitized,
};

struct ScenarioDocument
{
    std::string id;
    std::string title;
    std::string world;
    ScenarioMode mode = ScenarioMode::Hybrid;
    uint32_t seed = 0;
    std::vector<std::string> tags;
    std::vector<ScenarioStep> steps;
};
```

### `ScenarioStep`

Represents one atomic executable command.

```cpp
enum class ScenarioStepKind
{
    NewGameFlow,
    LoadMap,
    SetPose,
    Travel,
    PressAction,
    SelectTopic,
    InteractTarget,
    EnterDoorAt,
    AdvanceRuntime,
    AdvanceGameTime,
    WaitUntil,
    SaveCheckpoint,
    LoadCheckpoint,
    Assert,
    AssertMechanism,
    CombatLoot,
    SetupShortcut,
};

struct ScenarioStep
{
    ScenarioStepKind kind;
    ScenarioValue payload;
    std::filesystem::path sourceFile;
    int sourceLine = 0;
    size_t stepIndex = 0;
};
```

Use `ScenarioValue` as a small typed YAML value wrapper, not a loose `YAML::Node` stored everywhere. The runner should
access values through helpers like `requiredString`, `optionalInt`, `listOfUInt32`.

### `ScenarioRunner`

Executes steps against the current scenario context.

Responsibilities:

- Initialize `ScenarioContext`.
- Execute steps sequentially.
- Fail fast with rich diagnostics.
- Enforce mode rules:
  - `faithful`: no direct state mutation shortcuts.
  - `hybrid`: shortcuts allowed only with `reason`.
  - `unitized`: direct setup allowed.
- Manage checkpoints.
- Call reporting hooks before/after each step.

Suggested API:

```cpp
struct ScenarioRunOptions
{
    bool dryRun = false;
    bool strictShortcuts = false;
    std::optional<std::string> stopAfterCheckpoint;
    std::optional<std::string> startFromCheckpoint;
    std::filesystem::path artifactsDirectory;
};

class ScenarioRunner
{
public:
    ScenarioRunResult run(const ScenarioDocument &document, const ScenarioRunOptions &options);

private:
    ScenarioStepResult executeStep(ScenarioContext &context, const ScenarioStep &step);
};
```

### `ScenarioContext`

Mutable execution state shared by drivers.

Fields:

- `Engine::ApplicationConfig config`.
- `Engine::AssetFileSystem assetFileSystem`.
- `GameDataLoader gameDataLoader`.
- `std::unique_ptr<GameApplication> application` for app-backed steps.
- Current `IGameplayWorldRuntime *`.
- Current `GameplayScreenRuntime *`.
- `ScenarioAliasRegistry aliases`.
- `ScenarioReport report`.
- Current scenario id/mode.
- Last checkpoint name/path.
- Last active dialogue/house/selection state if needed.

The context should provide small accessors:

```cpp
GameApplication &requireApplication();
IGameplayWorldRuntime &requireWorldRuntime();
Party &requireParty();
EventRuntimeState &requireEventRuntimeState();
```

### `ScenarioDrivers`

Keep driver code split by concern but initially colocated in `ScenarioDrivers.*` if that keeps the first patch smaller.
Split later if the file grows too much.

#### `ScenarioWorldDriver`

Responsibilities:

- Initialize app/game data for headless scenario runs.
- `newGameFlow(continent, partyPreset)`.
- `loadMap(map, reason)`.
- `setPose(map, x, y, z, directionDegrees?, lookAngle?)`.
- `travel(target/map/method)` using real route where supported, direct load where marked shortcut.
- `advanceRuntime(seconds, fixedDeltaSeconds)`.
- `advanceGameTime(days/minutes/until)`.
- `saveCheckpoint(name)`.
- `loadCheckpoint(name)`.

Implementation notes:

- Phase 1 can implement `newGameFlow` as "create normal party + load starting map for requested world" if full UI
  continent/party screen automation is not ready. Mark this as a runner limitation until UI-level new-game flow exists.
- `setPose` should use world runtime party teleport helpers, not raw Party object fields.
- `advanceRuntime` ticks normal world/app update loops with fixed delta, never wall-clock sleeps.
- `loadMap` with `reason` is a shortcut in `hybrid` mode.

#### `ScenarioInteractionDriver`

Responsibilities:

- `pressAction(interact/escape/confirm/attack/rest/etc)`.
- `interactTarget`.
- `interactAt`.
- `enterDoorAt`.
- `combatLoot`.

Implementation notes:

- Prefer normal `GameplayInteractionController`/world pick APIs.
- For initial route conversion, `interactTarget` may target by raw `target_index`, `face_index`, and `triggered_event`
  using map event target lookup if available.
- Longer term, use generated aliases so YAML does not rely on raw face indices.
- `combatLoot` should:
  1. Place party near actor if pose is provided.
  2. Kill the actor through a bounded route shortcut or execute a real attack loop if `method=real_combat`.
  3. Interact with the dead actor/corpse through normal activation.
  4. Assert `item_received source=corpse item_id=...` or inventory contains item.

#### `ScenarioDialogueDriver`

Responsibilities:

- Select NPC/house topics by `source_id` + `action_id` or alias.
- Assert topic availability.
- Cancel dialogue.
- Enter/exit house service where supported.

Implementation notes:

- Reuse `GameplayDialogController`, `HouseInteraction`, and existing dialogue structures.
- The runner should not synthesize quest effects. Topic selection must call the same event/service code as gameplay.

#### `ScenarioInventoryDriver`

Responsibilities:

- Assert inventory/held item.
- Grant/remove items for setup shortcuts.
- Move held item to inventory if needed.
- Loot active chest/corpse where the scenario chooses a loot index.

Implementation notes:

- Normal loot should use existing active chest/corpse paths.
- `grant_item` must be a shortcut and require `reason` in `hybrid`.

#### `ScenarioShortcutDriver`

Responsibilities:

- `setup_shortcut` payloads:
  - `train_levels`
  - `set_skill`
  - `grant_gold`
  - `grant_item`
  - `clear_actor_group`
  - `set_calendar_time`
- Enforce reason and mode policy.
- Log shortcut usage into report.

Keep all direct mutation commands here so they are auditable.

### `ScenarioAssertionEngine`

Centralized state assertions.

Initial assertion families:

- Map/world:
  - `map`
  - `scene_kind`
  - `map_loaded`
  - `map_arrived`
  - party position approximate comparison.
- QBits:
  - `qbit_set`
  - `qbit_clear`
- Awards:
  - `award_acquired`
  - `award_any_member`
- Inventory:
  - `inventory`
  - `inventory_any_member`
  - `item_received`
  - `item_held_or_inventory`
- Followers:
  - `follower_hired`
  - `follower_left`
  - current follower roster.
- Dialogue:
  - active source id.
  - topic available/unavailable.
  - dialogue canceled.
- Mechanisms:
  - mechanism id/state/moving.
  - optional collision/passable later.
- Actor:
  - alive/dead.
  - hostile/friendly.
  - actor exists by index/name.
- Time:
  - date/month/hour.
  - game minutes.
- Ending:
  - main menu active.
  - good/bad ending state.

Every assertion failure should include:

- Scenario id.
- Step index.
- YAML source line.
- Assertion path.
- Expected.
- Actual.
- Current map.
- Current party position.

### `ScenarioAliasRegistry`

Responsible for mapping route-friendly names to raw data ids.

Sources:

- `tests/scenarios/mm6/aliases.yml`.
- Optional generated aliases.

Alias categories:

```yaml
maps:
  mm6.map.kriegspire: { file: outb1.odm }
items:
  mm6.item.sulmans_letter: { raw: 2125 }
qbits:
  mm6.main.letter.show_to_potbello: { raw: 1105 }
npcs:
  mm6.npc.wilbur_humphrey: { raw: 789 }
topics:
  mm6.topic.wilbur.letter: { source_id: 789, action_id: 1322 }
mechanisms:
  mm6.oracle.door_1: { map: oracle.blv, id: 1 }
actors:
  mm6.superior_baa.key_priest: { map: 6t7.blv, actor_index: 0 }
```

Phase 1 can allow raw ids directly. Phase 2 should add alias loading and validation. Phase 3 should migrate scenario
files toward aliases.

### `ScenarioReport`

Produces human-readable stdout plus optional JSON/JUnit.

Minimum phase 1 output:

```text
[Scenario] id=mm6.smoke.new_game_letter steps=42 mode=hybrid
[Scenario] step=12 source=main_story.yml:88 kind=select_topic ok
[Scenario] FAILED step=13 source=main_story.yml:94 kind=assert
  map=outd3.odm party=(17139,17032,2376)
  assertion=qbit_clear[1206]
  expected=false actual=true
```

JSON report fields:

- scenario id/title/world/mode.
- seed.
- elapsed ms.
- steps total/passed/failed/skipped.
- failed step kind/source.
- failure kind: `schema_error`, `runtime_error`, `assertion_failure`, `timeout`, `shortcut_policy`.
- latest checkpoint.
- touched maps.
- shortcut list.

## YAML Step Contract

The runner should support the sanitized converter output first, then polished scenario files.

Example:

```yaml
id: mm6.main_story.council_draft
world: mm6
mode: hybrid
tags: [mm6, council]

steps:
  - new_game_flow:
      continent: enroth
      party: mm6_story_any

  - assert:
      map: oute3.odm
      inventory_any_member:
        - item_id: 2125

  - travel:
      target: Kriegspire
      map: outb1.odm
      method: route_shortcut
      shortcut: true
      reason: manual route note predates enhanced map/pose trace

  - load_map:
      target: Silver Helm Outpost
      map: 6d07.blv
      scene_kind: indoor
      reason: manual route shortcut to recorded dungeon segment

  - combat_loot:
      target: Priest of Baa
      expected_item_id: 2187
      method: manual_kill_then_loot
      reason: script should turn this actor into a lootable monster that drops the key
```

## Step Semantics

### `new_game_flow`

Inputs:

- `continent`
- `party`

Phase 1:

- Create a normal party using a preset.
- Load the appropriate world start map.
- Assert start map and starting items.

Later:

- Drive actual main menu -> new game -> continent UI -> party creation screen.

### `load_map`

Inputs:

- `map`
- `scene_kind`
- `reason` required in `hybrid` if this skips a normal transition.

Behavior:

- Load map through app/session map-load path.
- Initialize world runtime and gameplay screen runtime.
- Assert selected world runtime exists.

### `travel`

Inputs:

- `target`
- `map`
- `method`
- `shortcut`
- `reason`

Behavior:

- If `method` is `house_service`, `stable`, `boat`, `town_portal`, or `edge_transition`, use the real runtime path when
  the source interaction is known.
- If `method` is `route_shortcut`, call `load_map` but record shortcut.

### `set_pose`

Inputs:

- `map`
- `x`, `y`, `z`
- optional `direction_degrees`, `look_angle`

Behavior:

- Ensure current map matches or load map if explicitly allowed.
- Teleport party with world runtime movement helpers.
- Validate floor/collision if available.

### `interact_target`

Inputs:

- `map`
- `scene_kind`
- `party`
- raw target fields from trace or alias target.

Behavior:

- If a `party` pose exists, set pose.
- Rebuild/pick the target where possible.
- Call normal interaction activation path.
- Report mismatch if expected target is not under crosshair.

Phase 1 fallback:

- Execute event/house/dialogue target by raw id only when no pickable target can be reconstructed, but mark as
  lower-fidelity in report.

### `select_topic`

Inputs:

- `kind`
- `source_id`
- `action_id`
- `secondary_id`
- `selection_index`

Behavior:

- Validate active dialogue/house source if possible.
- Select matching action.
- Execute the same event/service code as UI selection.

### `advance_runtime` / `wait_until`

Behavior:

- Tick app/world update at fixed timestep.
- Never sleep wall-clock time.
- Stop when assertion passes or timeout is reached.

### `advance_game_time`

Behavior:

- Advance calendar/game time through party/world time systems.
- Process timers/refills as gameplay would.

### `combat_loot`

Behavior:

- Resolve actor by alias, actor index, or nearest matching name.
- Kill actor through a shortcut or real attack loop based on `method`.
- Interact with corpse.
- Assert expected loot event or inventory item.

### `setup_shortcut`

Behavior:

- Execute direct mutation only if mode allows.
- Require `reason`.
- Emit report shortcut entry.
- Usually followed by assertions.

## Implementation Phases

### Phase 0: Keep Authoring Pipeline Stable

Already started:

- Raw notes: `tests/playthrough_scenarios/mm6.txt`.
- Sanitized notes: `tests/playthrough_scenarios/mm6_sanitized.txt`.
- Converter: `tools/playthrough_trace_to_scenario.py`.
- Enhanced `[GameplayTrace]` lines for route context and corpse loot.

Next:

- Generate a draft YAML file under `/tmp` during authoring.
- Manually promote stable segments to `tests/scenarios/mm6/*.yml`.

### Phase 1: Loader, Validator, Dry Run

Files:

- `ScenarioValue.*`
- `ScenarioDocument.h`
- `ScenarioStep.*`
- `ScenarioYamlLoader.*`
- `ScenarioCommandLine.*`
- `ScenarioHeadlessCommand.*`

Features:

- Parse YAML.
- Validate step kinds and required fields.
- Print dry-run step list.
- CLI: `--headless-validate-scenario`, `--headless-run-scenario --scenario-dry-run`.

Acceptance:

```bash
./build/game/openyamm --headless-validate-scenario tests/scenarios/mm6/smoke.yml
```

passes/fails with useful schema messages.

### Phase 2: App Session And Basic Assertions

Files:

- `ScenarioRunner.*`
- `ScenarioDrivers.*`
- `ScenarioAssertionEngine.*`
- `ScenarioReport.*`

Features:

- Initialize headless app/data.
- `load_map`.
- `assert` for map/qbits/items/basic inventory.
- `save_checkpoint` as report-only marker initially.
- `setup_shortcut` policy enforcement.

Acceptance:

- Scenario can load `oute3.odm`.
- Scenario can assert current map and starting item if party is seeded.

### Phase 3: Dialogue/Event Route Slice

Features:

- `new_game_flow` minimal implementation.
- `select_topic` for active dialogue.
- `interact_target` for event target / house entry enough for Potbello/Wilbur.
- QBit and award assertions.
- Checkpoint save/load if app save APIs are ready; otherwise serialize canonical snapshot first.

Acceptance:

- `mm6.smoke.new_game_letter.yml` passes:
  - start New Sorpigal.
  - Sulman's letter item exists.
  - Potbello topic sets/clears expected qbits.
  - Wilbur letter turn-in grants award and clears qbit.

### Phase 4: Travel, Poses, Chests, Corpses

Features:

- `travel`.
- `set_pose`.
- `enter_door_at`.
- `combat_loot`.
- chest/corpse/item assertions.
- mechanism `wait_until` assertions.

Acceptance:

- Convert and run the current council route draft through Oracle entry up to crystal-location qbits.
- Use `6d07.blv` and `6t7.blv` route segments.
- Assert corpse key loot for item ids `2187` and `2112`.

### Phase 5: Checkpoint/Resume

Features:

- Save canonical snapshots at checkpoints.
- Optionally write real save files.
- `--scenario-stop-after-checkpoint`.
- `--scenario-start-from-checkpoint`.
- Snapshot diff on failure.

Acceptance:

- Can resume at `council_complete` without replaying New Sorpigal.
- Save/load equivalence catches missing qbits/items/followers.

### Phase 6: MM6 Council Scenario

Files:

- `tests/scenarios/mm6/council.yml`.
- `tests/scenarios/mm6/main_story.yml` includes or references it.

Features needed:

- All council quest starts/turn-ins.
- Nicolai kidnap/recovery.
- Stable price-fixing.
- Silvertongue cure.
- Oracle unlock.

Acceptance:

- Scenario reaches `oracle.blv`.
- Asserts council awards and Oracle/crystal-location qbits.

### Phase 7: MM6 Oracle/VARN/Control Center/Hive

Features:

- More robust indoor mechanism assertions.
- Route shortcuts for long combat.
- Quest item acquisition/turn-in.
- Good/bad ending assertions.

Acceptance:

- Good ending and bad ending are reachable from checkpoints.
- Bad ending exits to main menu.

### Phase 8: Promotion Suite

Files:

- `tests/scenarios/mm6/promotions.yml`.

Features:

- Party preset with real and honorary class coverage.
- Refusal assertions.
- Time/date setup for druid promotions.
- Required follower/item paths.

Acceptance:

- All MM6 promotion families pass.
- Save/load after completion preserves class/awards/qbits.

### Phase 9: MM7/MM8 Reuse

Features:

- Alias files for MM7/MM8.
- Scenario route files only; avoid runner branching.
- Add missing world hooks only where shared runtime cannot drive an action.

Acceptance:

- Same runner executes at least one MM7 and MM8 smoke route.

## Mode And Shortcut Policy

`faithful`:

- No direct mutation.
- No direct map load except initial new-game/load-checkpoint.
- Must use gameplay interactions and transitions.

`hybrid`:

- Allows direct travel/map load/combat/training setup with `reason`.
- Final story qbits, awards, promotions, and endings must come from real event/dialogue/interaction steps.

`unitized`:

- Allows direct setup for focused event/mechanic tests.

Runner enforcement:

- Any step with `shortcut: true`, `setup_shortcut`, `grant_item`, `set_skill`, `train_levels`, `clear_actor_group`, or
  direct `load_map` after scenario start must include `reason` in `hybrid`.
- `--scenario-strict-shortcuts` can fail the run if a shortcut lacks a matching assertion within the next N steps.

## Failure Diagnostics

On failure, emit:

```text
Scenario failed: mm6.council
Step: 128 select_topic
Source: tests/scenarios/mm6/council.yml:233
Map: outd3.odm
Party: (17139,17032,2376)
Expected: topic source_id=789 action_id=1324 enabled=true
Actual: topic missing; active source_id=798
Latest checkpoint: nicolai_recovered
```

Write artifacts when `--scenario-artifacts-dir` is provided:

```text
scenario-report.json
state-before.yml
state-after.yml
latest-checkpoint.yml
shortcut-report.yml
```

## Testing Strategy

Unit tests:

- YAML loader accepts valid documents and rejects bad fields.
- Step required-field validation.
- Alias resolution.
- Assertion engine over small synthetic Party/EventRuntimeState objects where practical.

Headless smoke:

- `mm6.smoke.new_game_letter.yml`.
- one indoor `load_map` + mechanism `wait_until`.
- one `combat_loot` corpse key scenario.

Manual/nightly:

- full MM6 council route.
- full MM6 main story.
- full promotions.

## First Patch Sequence

1. Add `game/scenario/ScenarioValue.*`, `ScenarioDocument.h`, `ScenarioStep.*`, `ScenarioYamlLoader.*`.
2. Add `ScenarioHeadlessCommand.*` and CLI dispatch in `main.cpp`.
3. Add CMake entries.
4. Add `tests/scenarios/mm6/smoke_new_game_letter.yml` as a small target file.
5. Implement dry-run output.
6. Implement `load_map` and `assert map`.
7. Implement minimal `new_game_flow`.
8. Implement `select_topic` enough for Potbello/Wilbur.
9. Implement qbit/award/item assertions.
10. Extend from smoke to current sanitized council route.

This order keeps each patch reviewable and prevents the runner from becoming a large untested blob.

## Open Decisions

- Whether to implement true UI-driven New Game first or allow the initial `new_game_flow` to seed a normal party and
  load the start map. Recommendation: seed first, add UI-driven flow later as a separate faithful smoke.
- Whether checkpoint save/load should use real save files immediately or canonical snapshots first. Recommendation:
  start with canonical snapshots, then add real save files once the route is stable.
- Whether raw ids are allowed in committed scenario files. Recommendation: raw ids allowed for the first MM6 draft,
  but migrate stable milestones to aliases before calling the route proven.
