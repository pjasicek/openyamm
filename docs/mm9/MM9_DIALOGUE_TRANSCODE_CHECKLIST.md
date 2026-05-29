# MM9 Dialogue Transcode Checklist

Sidecar checklist for `docs/mm9/MM9_DIALOGUE_INTEGRATION_RESEARCH.md`.

The goal is lossless, mechanically regenerable transcoding:

```text
*.rude       -> generated dialogue *.yml
*.scr/*.inc  -> source-preserving IR -> generated *.lua
```

Every phase must have tests that prove two things:

1. No authored information was dropped.
2. The decoded/transcoded behavior matches the original source semantics as far as currently validated.

## Ground Rules

- [x] Treat extracted MM9 files as source inputs, not as runtime implementation details.
- [x] Generated YAML/Lua must be deterministic from the same inputs.
- [x] Preserve raw source references in every generated artifact: file path, row/line number, original id, and original
      ordering.
- [x] Keep unknown fields explicitly represented instead of dropping or guessing them.
- [x] Add tests before broad importer expansion. A parser that silently drops fields is worse than no parser.
- [x] Keep semantic decoding separate from raw preservation. A failed semantic inference must not prevent raw import.

## Source Inventory Tests

- [x] Unit test enumerates all expected RUDE source files under `mm9/extracted/RUDE/RUDE/`.
- [x] Unit test asserts numbered `NPC<number>.rude` file count.
- [x] Unit test asserts numbered RUDE total row count.
- [x] Unit test asserts distinct numbered RUDE NPC id count.
- [x] Unit test asserts distinct numbered `(npc_id, node_id)` count.
- [x] Unit test asserts normal interactive `NPC<number>.rude` file count after excluding pseudo-NPC files.
- [x] Unit test asserts normal interactive RUDE total row count.
- [x] Unit test asserts distinct normal interactive RUDE NPC id count.
- [x] Unit test asserts distinct normal interactive `(npc_id, node_id)` count.
- [x] Unit test asserts `NPCNAME.rude` row count.
- [x] Unit test asserts `TOPBLURB.rude` row count.
- [x] Unit test asserts `NPC997.rude`, `NPC998.rude`, and `NPC999.rude` row counts.
- [x] Unit test enumerates all `.scr` and `.inc` files under `mm9/extracted/SCRIPTS/SCRIPTS/`.
- [x] Unit test asserts script and include file counts.
- [x] Unit test emits a clear failure when source files move, disappear, or duplicate ids appear.

Current baseline from research:

- [x] 439 numbered `NPC<number>.rude` files.
- [x] 4,504 numbered RUDE rows.
- [x] 439 numbered RUDE ids.
- [x] 1,869 distinct numbered `(npc_id, node_id)` pairs.
- [x] 436 normal interactive `NPC<number>.rude` files.
- [x] 4,215 normal interactive dialogue rows.
- [x] 436 normal interactive NPC ids.
- [x] 1,864 distinct normal interactive `(npc_id, node_id)` pairs.
- [x] `NPCNAME.rude`: 439 rows.
- [x] `TOPBLURB.rude`: 439 rows.
- [x] `NPC997.rude`: 143 rows.
- [x] `NPC998.rude`: 91 rows.
- [x] `NPC999.rude`: 55 rows.
- [x] 715 `.scr` files.
- [x] 87 `.inc` files.

## RUDE Parser Losslessness Tests

- [x] Unit test parses representative normal `NPC<number>.rude` rows as exactly 30 columns.
- [x] Unit test parses `NPCNAME.rude` as its expected 2-column shape.
- [x] Unit test parses `TOPBLURB.rude` as its expected top-blurb shape.
- [x] Unit test parses `NPC997.rude`, `NPC998.rude`, and `NPC999.rude` without special-case data loss.
- [x] Unit test round-trips every parsed RUDE row back to equivalent CSV fields.
- [x] Unit test compares original column strings to parsed raw-column strings.
- [x] Unit test preserves empty strings, quoted strings, embedded punctuation, whitespace that is semantically present,
      and zero numeric fields.
- [x] Unit test preserves original row order within each file.
- [x] Unit test preserves original file name and row number for every row.
- [x] Unit test records parse errors with file and row context.
- [x] Unit test rejects malformed rows unless the importer has an explicit documented recovery rule.

## RUDE YAML Generation Tests

- [x] Unit test generates YAML for every normal RUDE file.
- [x] Unit test asserts generated YAML contains every source row exactly once for representative files.
- [x] Unit test asserts generated YAML stores all raw columns for representative normal rows.
- [x] Unit test asserts decoded fields match raw columns:
      `npc_id`, `node_id`, `choice_slot`, `prompt`, `response`, and `next`.
- [x] Unit test asserts all sparse columns are preserved, including zeros, for representative rows.
- [x] Unit test asserts source metadata is present on every row for representative files.
- [x] Unit test asserts YAML generation is deterministic by comparing output from two consecutive generations.
- [x] Regression fixture covers representative NPC files:
      `NPC1.rude`, a shop NPC, a trainer NPC, a healer NPC, a bank NPC, a travel NPC, a hireling NPC, and an arena NPC.
- [x] Regression fixture covers pseudo-NPC files:
      `NPC997.rude`, `NPC998.rude`, and `NPC999.rude`.
- [x] Test fixture contains at least one row with each observed negative `next` opcode.

## RUDE Semantic Decode Tests

- [x] Unit test detects every observed negative `next` opcode.
- [x] Unit test asserts `999` is treated as a normal node target when a node `999` exists.
- [x] Unit test asserts `-1` is treated as dialogue close.
- [x] Unit test keeps `next == 0` explicit and does not silently reinterpret it.
- [x] Unit test builds the set of all nonzero sparse RUDE numeric fields.
- [x] Unit test asserts no sparse numeric value disappears during semantic enrichment.
- [x] Unit test classifies condition/action fields only where validation exists.
- [x] Unit test preserves raw fields when semantic classification is unknown.
- [x] Unit test checks representative branch visibility against known key states.
- [x] Unit test checks representative side-effect decoding against known script/key evidence.

Observed negative opcode coverage to test:

- [x] `-1` close.
- [x] `-2` shop/trade.
- [x] `-3` training service.
- [x] `-4` skill training/mastery.
- [x] `-5` travel/transport.
- [x] `-6` bank.
- [x] `-7` inn/rest.
- [x] `-8` healer/temple.
- [x] `-10` hire follower.
- [x] `-11` dismiss follower.
- [x] `-13` item combine/tinker-like service.
- [x] `-14` preserved and flagged pending exact validation.
- [x] `-15` town portal/follower teleport service.
- [x] `-16` donation/service.

## Key Registry Tests

- [x] Unit test extracts key constants from `.inc` and `.scr` files.
- [x] Unit test extracts all literal key ids used by `GiveKey`, `TakeKey`, and `HasKey`.
- [x] Unit test extracts all nonzero candidate key ids from RUDE sparse fields.
- [x] Unit test builds a namespaced `mm9.keys` registry.
- [x] Unit test detects and segregates conflicting constant definitions.
- [x] Unit test allows aliases when multiple names intentionally refer to the same id.
- [x] Unit test records evidence for each key id: script source, RUDE source, journal/award source, or unknown source.
- [x] Unit test asserts MM9 key ids are not merged into MM6-MM8 QBit ids.
- [x] Unit test verifies generated key registry is deterministic.

## Journal, Notes, And Awards Tests

- [x] Unit test imports `NPC997.rude` into generated quest/journal YAML.
- [x] Unit test imports `NPC998.rude` into generated note/autonote YAML.
- [x] Unit test imports `NPC999.rude` into generated award YAML.
- [x] Unit test preserves original ids, row order, text, `next`, and all sparse fields for pseudo-NPC rows.
- [x] Unit test cross-references pseudo-NPC key ids against the generated key registry.
- [x] Unit test fails when a pseudo-NPC row references a key id that is neither registered nor explicitly marked unknown.

## Script Parser And IR Tests

- [x] Unit test parses every `.scr` file into source-preserving IR.
- [x] Unit test parses every `.inc` file into source-preserving IR.
- [x] Unit test preserves labels, commands, parameters, comments needed for source mapping, and include relationships.
- [x] Unit test preserves original file and line number for every command.
- [x] Unit test indexes every `DoRude`/`DoRUDE` call.
- [x] Unit test indexes every `OnRudeExit`/`OnRUDEExit` registration.
- [x] Unit test indexes every `GiveKey`, `TakeKey`, and `HasKey`.
- [x] Unit test indexes every `GiveItem`, `TakeItem`, and `HasItem`.
- [x] Unit test indexes every gold, experience, and reward operation.
- [x] Unit test indexes every console variable get/set operation.
- [x] Unit test indexes every object parameter/property read that can affect dialogue.
- [x] Unit test fails on unknown script commands unless the command is preserved as an explicit opaque IR node.

## Lua Generation Tests

- [x] Unit test generates Lua for each parsed `.scr` runtime script.
- [x] Unit test generates Lua include modules or expanded dependencies for each `.inc`.
- [x] Unit test asserts generated Lua preserves source references in comments or metadata tables.
- [x] Unit test asserts generated Lua has deterministic output.
- [x] Unit test compiles every generated Lua file with the chosen Lua parser/runtime.
- [x] Unit test verifies generated Lua calls stable OpenYAMM APIs for dialogue:
      `doRude`, `onRudeExit`, key ops, item ops, rewards, console vars, object handles, and triggers.
- [x] Unit test verifies `DoRude` calls route to existing generated RUDE YAML ids.
- [x] Unit test verifies `OnRudeExit` callbacks route to generated Lua labels/functions.
- [x] Unit test verifies opaque/unimplemented script commands remain explicit and visible in generated output.

## Object Binding Tests

- [x] Unit test scans generated MM9 map raw object YAML for dialogue-relevant properties.
- [x] Unit test indexes objects with `DoRude`, `NPCNbr`, `ScriptName`, `ScriptParams`, and `GreetingSound`.
- [x] Unit test preserves raw object property data, including `raw_hex` where property decoding is incomplete.
- [x] Unit test links dialogue-capable objects to RUDE ids when decoding is validated.
- [x] Unit test flags objects that appear dialogue-capable but cannot be linked to a RUDE id.
- [x] Unit test links object scripts to generated Lua scripts.
- [x] Unit test verifies every linked RUDE id has name/top-blurb/dialogue data or an explicit exception.

## Dialogue Provider Tests

- [x] Unit test builds an MM9 RUDE dialogue provider from generated YAML.
- [x] Unit test enters dialogue by RUDE id.
- [x] Unit test enters dialogue by object/script context.
- [x] Unit test lists visible topics for a node with no keys set.
- [x] Unit test lists visible topics after setting relevant `mm9.keys`.
- [x] Unit test verifies topic ordering by choice slot and source row order.
- [x] Unit test selects a topic and displays the matching response.
- [x] Unit test follows positive `next` values to the next node.
- [x] Unit test closes on `-1`.
- [x] Unit test dispatches negative service opcodes to typed service stubs.
- [x] Unit test preserves and exposes unresolved behavior for `next == 0`.
- [x] Unit test fires generated Lua `OnRudeExit` callbacks when dialogue closes.
- [x] Unit test proves OpenYAMM GUI-facing topic/response data is generated from RUDE YAML, not flattened MM6-MM8 tables.

## Runtime Regression Fixtures

- [x] Fixture for a normal quest NPC with multi-key branching.
- [x] Fixture for a shop service NPC.
- [x] Fixture for a trainer or skill mastery NPC.
- [x] Fixture for a healer/temple NPC.
- [x] Fixture for a bank NPC.
- [x] Fixture for an inn/rest NPC.
- [x] Fixture for a travel NPC.
- [x] Fixture for hire and dismiss services.
- [x] Fixture for town portal service.
- [x] Fixture for arena/scripted dialogue with `OnRudeExit` side effects.
- [x] Fixture for journal/current quest rendering from `NPC997`.
- [x] Fixture for notes/autonotes from `NPC998`.
- [x] Fixture for awards from `NPC999`.

## CI Gates

- [x] Importer unit tests run in normal test target.
- [x] Parser tests fail if row counts, file counts, or opcode counts drift unexpectedly.
- [x] Golden YAML tests fail on nondeterministic output.
- [x] Lua generation tests fail if generated Lua no longer parses.
- [x] Script index tests fail if `DoRude` or `OnRudeExit` references lose source mappings.
- [x] Key registry tests fail if an id is dropped or merged into the wrong namespace.
- [x] Object binding tests fail if dialogue-capable objects become unlinked without an explicit exception.
- [x] Runtime provider tests fail if topic visibility, branching, close behavior, or service dispatch changes.

## Definition Of Done

- [x] All original RUDE rows are present in generated YAML.
- [x] All original RUDE columns are present in generated YAML.
- [x] All original script commands are present in IR or explicitly preserved as opaque commands.
- [x] Generated Lua is deterministic and parseable.
- [x] Every `DoRude` and `OnRudeExit` reference is indexed.
- [x] Every observed negative RUDE opcode is tested.
- [x] MM9 key state is namespaced and tested separately from MM6-MM8 QBits.
- [x] The OpenYAMM dialogue GUI can display topics/responses from the MM9 RUDE provider.
- [x] No hand-written per-NPC fixups are required for representative fixtures.
- [x] Unknown behavior is visible in test output and generated artifacts instead of being silently discarded.
