# MM9 Dialogue Runtime Pipeline Checklist

This checklist follows `MM9_DIALOGUE_INTEGRATION_RESEARCH.md` and
`MM9_DIALOGUE_TRANSCODE_CHECKLIST.md`. The transcode proof established that RUDE rows, script source, key evidence,
object bindings, and generated Lua can be preserved. This document tracks the remaining production pipeline and runtime
integration needed for a player to interact with an MM9 dialogue-capable object and see the correct OpenYAMM dialogue
flow.

The target pipeline is:

```text
mm9/extracted/RUDE/RUDE/*.rude
mm9/extracted/SCRIPTS/SCRIPTS/*.scr
mm9/extracted/SCRIPTS/SCRIPTS/*.inc
assets_dev/worlds/mm9/maps/*.raw_objects.yml
    -> deterministic generator
    -> assets_dev/worlds/mm9/dialogue/*.yml
    -> assets_dev/worlds/mm9/scripts/*.lua
    -> assets_dev/worlds/mm9/state/*.yml
    -> assets_dev/worlds/mm9/maps/* dialogue binding data
    -> OpenYAMM runtime loaders/providers
```

Current generator command:

```text
./build/tools/mm9_dialogue_pipeline mm9/extracted assets_dev/worlds/mm9/maps assets_dev/worlds/mm9
./build/tools/mm9_dialogue_pipeline --check mm9/extracted assets_dev/worlds/mm9/maps assets_dev/worlds/mm9
```

## Ground Rules

- [x] Treat extracted MM9 files and generated raw object YAML as source inputs, not as runtime-only implementation
      details.
- [x] Regeneration must be deterministic and idempotent: running the generator twice with unchanged inputs produces no
      diff.
- [x] The generator may write generated MM9 content only under `assets_dev/worlds/mm9/*`.
- [x] Engine changes are allowed only where shared runtime support is required: package loading, state domains,
      dialogue provider dispatch, script context APIs, interaction routing, services, and save/load.
- [x] Do not hand-edit generated `assets_dev/worlds/mm9/dialogue/*`, `scripts/*`, or `state/*` files as authoritative
      fixes. Fix the generator or add an explicit overlay file with tests.
      Current check mode verifies the generated tree is authoritative and unchanged when rerun.
- [x] Preserve source metadata in generated artifacts: original file, row or line number, raw id, generated id, and
      original ordering.
- [x] Unknown or partially decoded behavior must remain visible in generated YAML/Lua and validation output.
- [x] All runtime behavior must be backed by focused tests before broad map coverage is enabled.

## Generator Entry Point

- [x] Add a single documented command for regenerating MM9 dialogue/script data.
- [x] The command reads RUDE, scripts, includes, generated map raw object YAML, and MM9 data tables from their canonical
      locations.
- [x] The command writes all generated dialogue YAML under `assets_dev/worlds/mm9/dialogue/`.
- [x] The command writes all generated script Lua under `assets_dev/worlds/mm9/scripts/`.
- [x] The command writes generated state registries under `assets_dev/worlds/mm9/state/`.
- [x] The command writes object dialogue binding outputs under `assets_dev/worlds/mm9/maps/` or a world-local generated
      index path.
- [x] The command fails on parse errors, duplicate canonical ids, missing required inputs, or source inventory drift
      unless the drift is intentionally accepted in updated tests.
- [x] The command has a dry-run/check mode for CI that verifies the workspace already matches generated output.
- [x] Current generated output is materialized under `assets_dev/worlds/mm9/` and check mode reports it unchanged.

## Generated Dialogue Content

- [x] Generate `dialogue/npcs/<id>.yml` from every normal `NPC<number>.rude`.
- [x] Generate `dialogue/npc_names.yml` from `NPCNAME.rude`.
- [x] Generate `dialogue/top_blurbs.yml` from `TOPBLURB.rude`.
- [x] Generate `dialogue/services.yml` for every observed negative RUDE opcode.
- [x] Generate `dialogue/journal_quests.yml` from `NPC997.rude`.
- [x] Generate `dialogue/journal_notes.yml` from `NPC998.rude`.
- [x] Generate `dialogue/awards.yml` from `NPC999.rude`.
- [x] Preserve every raw RUDE column in generated YAML, including zeros and unknown sparse fields.
- [x] Preserve row order, node id, choice slot, prompt, response, `next`, and source metadata.
- [x] Include semantic blocks only for validated conditions, actions, services, and state references.
- [x] Include explicit unresolved blocks for `next == 0`, unknown sparse fields, and partially validated service
      behavior.

## Generated Script Content

- [x] Generate a Lua file for every runtime `.scr` file.
- [x] Generate Lua include modules or explicit expanded dependency output for every `.inc` file.
- [x] Preserve source file, line number, label, command name, raw argument text, and include relationship in generated
      Lua metadata.
- [x] Generate `scripts/script_index.yml` with all `DoRude`, `OnRudeExit`, key, item, reward, console variable, object
      property, trigger, and opaque command references.
- [x] Generated Lua should call stable runtime APIs such as `ctx:doRude`, `ctx:onRudeExit`, `ctx:hasKey`,
      `ctx:giveKey`, `ctx:takeKey`, `ctx:getConsoleNumVar`, and object/property APIs.
- [x] Opaque or unimplemented commands must remain explicit Lua calls or metadata entries; they must not disappear.

## MM9 Key To QBit Mapping

- [x] Treat MM9 script keys as core qbit-backed state with semantic ids `mm9.keys.<raw_id>`.
- [x] Map every raw MM9 key id to OpenYAMM QBit id `9000 + raw_id`.
- [x] Generate `state/keys.yml` with raw id, qbit id, aliases, constants, conflicts, evidence, and source locations.
- [x] Runtime `ctx:hasKey(N)`, `ctx:giveKey(N)`, and `ctx:takeKey(N)` operate on QBit `9000 + N`.
- [x] Dialogue row key checks operate through the same `mm9.keys` API, not through ad hoc provider-local state.
- [x] Save/load persists mapped MM9 keys through the shared QBit backend.
- [x] Tests assert mapped MM9 QBits do not collide with MM6/MM7/MM8 authored QBits.
- [x] Tests assert custom/mod qbit ranges cannot silently overlap the reserved MM9 key range.
- [x] Tests assert generated YAML preserves both raw MM9 key ids and derived QBit ids.

## Other MM9 State Domains

- [x] Keep map variables typed and scoped; do not flatten non-boolean map state into QBits.
- [x] Implement or reuse map-local variable storage for MM9 script/map state.
- [x] Implement or reuse global/world console variable storage for `GetConsoleNumVar`, `SetConsoleNumVar`,
      `GetConsoleStrVar`, and `SetConsoleStrVar`.
- [x] Preserve object-local properties and script-local variables separately from global keys.
- [x] Save/load persists MM9 script-local variables, object handle variables, object number property mutations, trigger
      registrations, and trigger dispatches with stable names and scopes.
- [x] Save/load persists MM9 map variables with stable map-local scopes.
- [x] Tests prove MM9 keys, console variables, map variables, object properties, and inventory operations do not alias
      each other accidentally.

## Asset Loading And World Mounting

- [x] Add MM9 dialogue/script/state generated outputs to the world package manifest or asset mount path.
- [x] Add a loader for generated MM9 dialogue YAML.
- [x] Add a loader for generated MM9 services YAML.
- [x] Add a loader for generated MM9 key/state registries.
- [x] Add a loader for generated MM9 script index and Lua files.
- [x] Add a loader for object dialogue binding data.
- [x] Loaders must reject malformed generated files with source-aware diagnostics.
- [x] Loaders must preserve enough metadata for debug tools and failing tests to point back to original RUDE/script
      source.

## Object Interaction Entry

- [x] Generated runtime object bindings expose imported MM9 properties relevant to interaction: `DoRude`, `NPCNbr`,
      `ScriptName`, `ScriptParams`, `GreetingSound`, object class, object name, and object index.
- [x] Runtime map object instances expose imported MM9 interaction properties through router metadata.
      Covered fields: map id, object id, source object index, class/name, visual id, script name, and script params.
- [x] Authored `ScriptName` values are preserved as imported, while runtime script lookup resolves generated Lua
      case-insensitively so `SvenArena.scr` can find `SVENARENA.lua`.
- [x] Player use/click interaction resolves the selected MM9 object hit to a generated dialogue/script binding.
- [x] Outdoor generated MM9 scripted billboard interaction resolves the selected source object index to the generated
      MM9 dialogue/script binding.
- [x] Runtime object activation resolves a selected MM9 map id/object index to its generated dialogue/script binding.
- [x] Objects with a linked script run the generated `OnUse` script entry point before dialogue when the original object
      path requires it.
- [x] Objects with direct `DoRude` behavior enter the RUDE provider with the decoded RUDE id.
- [x] Runtime object activation emits a nonblocking `GreetingSound` request with map/object/script context.
- [x] The real audio layer consumes MM9 `GreetingSound` activation requests by authored sound name for the outdoor
      scripted-object activation path.
- [x] Dialogue-capable objects without a resolved RUDE id fail visibly in validation and activation, and do not silently
      open the wrong dialogue.
- [x] Headless tests load a representative generated MM9 object fixture, select known NPC objects, and verify resolved
      RUDE id, script, greeting sound metadata, and provider entry state.

## Dialogue GUI Integration

- [x] Add an MM9 RUDE-backed dialogue provider behind the existing OpenYAMM dialogue GUI surface for outdoor
      scripted-object activation.
- [x] Add an MM9 RUDE-backed adapter that projects runtime topics, responses, close results, and service requests into
      the existing `EventDialogContent` dialogue surface.
- [x] Outdoor MM9 scripted-object activation opens the existing OpenYAMM dialogue overlay with MM9 `EventDialogContent`.
- [x] The dialogue content surface receives topic prompt, NPC response, ordering, availability, and close/service
      results from the MM9 adapter.
- [x] The provider enters dialogue from object/script context, not only from raw RUDE id.
- [x] MM9 topic clicks route through `GameplayDialogController` back into the active MM9 dialogue runtime.
- [x] Topic visibility is recomputed from `mm9.keys`, inventory, console variables, and validated row conditions.
      Runtime package loading supports validated `required_keys`, `required_items`,
      `required_console_num_equals`, and `required_console_str_equals` condition blocks. Real generated RUDE data
      currently emits validated key gates; unresolved sparse columns remain preserved instead of guessed.
- [x] Generated RUDE `semantic.conditions.required_keys` rows are parsed into runtime package data and drive topic
      visibility through MM9 key QBit state, with raw RUDE columns retained as source provenance.
- [x] Topic order uses choice slot first and source row order second.
- [x] Selecting a topic displays the matching response from generated YAML.
- [x] Positive `next` values move to the target node.
- [x] `999` is treated as a normal node when the file defines node `999`.
- [x] `-1` closes dialogue and returns the owning script's `OnRudeExit` callback label for dispatch.
- [x] Other negative values dispatch through typed service handlers.
- [x] `next == 0` stays explicit until exact runtime behavior is validated.
- [x] GUI tests prove MM6-MM8 dialogue providers still behave unchanged after MM9 provider registration.

## Script Runtime Context

- [x] Bind generated Lua scripts into the same runtime that handles map/object interaction.
- [x] Implement `ctx:doRude` to open the MM9 provider with the correct owner object and script context.
- [x] Implement `ctx:onRudeExit` to register callbacks by generated script label.
- [x] Implement key APIs through the `9000 + raw_key` QBit mapping.
- [x] Implement item APIs through the party inventory model.
- [x] Implement gold and experience APIs through shared party state.
- [x] Implement console variable APIs through MM9 console variable storage.
- [x] Implement object lookup/property APIs needed by dialogue scripts.
- [x] Implement `AddTrigger` registration APIs needed by scripts that lead into or exit from dialogue.
- [x] Implement trigger dispatch APIs for generated `Trigger` commands.
- [x] Unknown generated commands call a visible unimplemented-command path that includes source file and line number.
- [x] Tests verify `DoRude` and `OnRudeExit` work end to end from generated Lua, not from hand-written test shims.

## Service Opcode Integration

- [x] `-2` opens a generated MM9 shop/trade service context.
- [x] `-3` opens a generated MM9 training service context.
- [x] `-4` opens a generated MM9 skill training/mastery service context.
- [x] `-5` opens a generated MM9 travel/transport service context.
- [x] `-6` opens a generated MM9 bank service context.
- [x] `-7` opens a generated MM9 inn/rest service context.
- [x] `-8` opens a generated MM9 healer/temple service context.
- [x] `-10` opens a generated MM9 hire service context.
- [x] `-11` opens a generated MM9 dismiss service context.
- [x] `-13` opens a generated MM9 item combine/tinker-like service context.
- [x] `-14` stays preserved and visibly pending until exact behavior is validated.
- [x] `-15` opens a generated MM9 town portal/follower teleport service context.
- [x] `-16` opens a generated MM9 donation/service context.
- [x] Each service handler receives RUDE id, source row, owner object, map id, script context, and raw columns.
- [x] Outdoor MM9 dialogue selections now consume typed service requests through the runtime route and surface pending
      exact service UI visibly.
- [x] The generated MM9 world package exposes every known service opcode from original generated data with nonzero
      observed counts.
- [x] Each service has at least one focused runtime fixture using original generated MM9 data.

## Save/Load

- [x] New games initialize MM9 key mappings, console variables, map variables, and object/script state from generated
      defaults.
- [x] Saves persist MM9 keys through shared QBits and expose raw id/qbit id in debug output.
- [x] Saves persist MM9 console variables with type and scope.
- [x] Saves persist MM9 map-local variables per map.
- [x] Saves persist object property mutations that affect dialogue or scripts.
- [x] `GameSession` owns MM9 script runtime state, writes it into saves, restores it from saves, and syncs outdoor MM9
      dialogue/script mutations back into the session.
- [x] Loading a save restores visible dialogue topics exactly for covered fixtures.
- [x] Save migration rejects or explicitly upgrades stale MM9 dialogue/state schemas.

## Idempotency And CI Gates

- [x] Generator check mode runs in CI or the normal validation target.
- [x] Check mode fails if generated `assets_dev/worlds/mm9/*` files are stale.
- [x] Running the generator twice produces byte-identical generated output.
- [x] Tests verify generated file ordering is stable across filesystem traversal order.
- [x] Tests verify no generated path escapes `assets_dev/worlds/mm9/*`.
- [x] Tests verify engine integration does not write generated artifacts outside the MM9 world tree.
- [x] Tests verify source inventory counts match the accepted baseline or fail with actionable diagnostics.
- [x] Tests verify every generated Lua file parses.
- [x] Tests verify every object dialogue binding either resolves or has an explicit unresolved reason.
- [x] Tests verify every `DoRude` call targets a known RUDE id or is marked dynamic with evidence.
- [x] Tests verify every `OnRudeExit` callback targets a generated Lua label.

## End-To-End Runtime Fixtures

- [x] Load an MM9 map containing a normal quest NPC and open dialogue from actual object interaction.
- [x] Add a focused headless fixture for the outdoor scripted-billboard interaction route that proves player activation
      opens the expected generated RUDE dialogue through `OutdoorWorldRuntime`.
- [x] Select a branch that depends on an MM9 key and verify visibility changes after the key is set.
- [x] Select a branch that changes MM9 key state and verify the mapped QBit changes.
- [x] Close dialogue and verify `OnRudeExit` callback execution.
- [x] Open a direct `DoRude` NPC from generated object binding data.
- [x] Open a bank NPC from object interaction and dispatch `-6`.
- [x] Dispatch a bank `-6` service from generated MM9 object activation through the dialogue content adapter.
- [x] Open a shop NPC from object interaction and dispatch `-2`.
- [x] Open a trainer or skill mastery NPC from object interaction and dispatch `-3` or `-4`.
- [x] Open a healer NPC from object interaction and dispatch `-8`.
- [x] Open an inn NPC from object interaction and dispatch `-7`.
- [x] Open a travel NPC from object interaction and dispatch `-5`.
- [x] Open hire and dismiss flows from object interaction and dispatch `-10` and `-11`.
- [x] Open an arena/scripted NPC and verify script-side state after dialogue closes.
- [x] Render journal/current quest data generated from `NPC997` through a tested MM9 render-model projection.
- [x] Render note/autonote data generated from `NPC998` through a tested MM9 render-model projection.
- [x] Render award data generated from `NPC999` through a tested MM9 render-model projection.
- [x] Save after an MM9 dialogue state change, reload, and verify the same topics and state are restored.

## Definition Of Done

- [x] One command regenerates all MM9 dialogue, script, state, and object binding outputs.
- [x] Regeneration is deterministic, idempotent, and path-constrained to `assets_dev/worlds/mm9/*`.
- [x] MM9 keys use semantic ids in content and scripts while using QBit `9000 + raw_key` for runtime storage.
- [x] Generated MM9 dialogue YAML, generated Lua, and generated state registries are loaded by the runtime.
- [x] Player interaction with a real MM9 dialogue-capable object opens the correct RUDE dialogue through the existing
      OpenYAMM dialogue GUI.
- [x] Generated Lua can start RUDE dialogue and receive `OnRudeExit` callbacks.
- [x] Representative service opcodes dispatch to typed runtime handlers.
- [x] Save/load preserves MM9 dialogue-affecting state.
- [x] Focused MM6-MM8 dialogue, Lua event, house, and QBit tests still pass.
- [x] No per-NPC hand fixups are required for the covered runtime fixtures.
