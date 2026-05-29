# MM9 Dialogue Integration Research

This document records the current understanding of Might and Magic IX dialogue data and the recommended preservation
strategy for importing it into OpenYAMM. The goal is not to force MM9 content into the MM6-MM8 dialogue model, but to
transcode every authored dialogue row, branch, service hook, script hook, and state reference into OpenYAMM-owned data
without losing information.

## Scope And Sources

Local sources used:

- `docs/mm9/MM9_DAT_FORMAT_NOTES.md`
- `mm9/extracted/RUDE/RUDE/*.rude`
- `mm9/extracted/SCRIPTS/SCRIPTS/*.scr`
- `mm9/extracted/SCRIPTS/SCRIPTS/*.inc`
- `mm9/extracted/DATA/DATA/JOURNAL.txt`
- `mm9/extracted/DATA/DATA/MAPSTATS.txt`
- `assets_dev/worlds/mm9/maps/*.raw_objects.yml`
- `mm9/extract_work/*/*.raw_objects.yml`
- `docs/dialogue-system-data-handoff.md`
- `docs/dialogue-system-assumptions.md`
- MM9 LithTech reference/import attempts under `mm9/*`, especially the DAT reader/extraction work.

The MM9 DAT format notes matter because map object metadata is generated from a locally verified DAT v66 variant. Object
properties such as script names, script parameters, and NPC dialogue bindings must be treated as original content data,
not as incidental extraction output.

## High-Level Findings

MM9 dialogue is built around the RUDE system. The authored narrative dialogue is concentrated in NPC interactions, but
the broader game interaction model is not dialogue-only. Doors, triggers, props, hirelings, shops, banks, training,
transport, arena flows, promotion rewards, and map logic are all connected through LithTech scripts and object
properties.

Important consequences:

- RUDE appears to be a homegrown MM9/NWC dialogue subsystem, not an industry-standard format. Local script command
  docs describe `DoRUDE` and `OnRUDEExit` as MMIX scripting additions that start and leave a RUDE dialogue.
- RUDE files are graph data, not simple flat topic tables.
- RUDE rows include dialogue text, branch targets, service opcodes, and sparse numeric state fields.
- State is not only in RUDE files. Scripts use global key bits, inventory items, console variables, object properties,
  local script variables, map triggers, and `OnRudeExit` callbacks.
- The current MM6-MM8 OpenYAMM dialogue table shape is not expressive enough for MM9 without losing graph structure or
  service/script coupling.
- MM9 import should preserve original row ids and raw numeric fields first, then layer validated semantics over them.
- The intended final OpenYAMM form is generated `.yml` for RUDE dialogue data and generated `.lua` for MM9 scripts,
  both mechanically regenerated from the original extracted files.

## Source Inventory

The extracted RUDE directory contains:

- 439 numbered `NPC<number>.rude` files.
- 4,504 numbered RUDE rows across those files.
- 1,869 distinct numbered `(npc_id, node_id)` pairs.
- 436 normal interactive NPC dialogue files after excluding pseudo-NPC files `NPC997.rude`, `NPC998.rude`, and
  `NPC999.rude`.
- 4,215 normal interactive NPC dialogue rows.
- 1,864 distinct normal interactive `(npc_id, node_id)` pairs.
- `NPCNAME.rude`, with 439 NPC id to display-name rows.
- `TOPBLURB.rude`, with 439 NPC id/top-blurb rows.
- `NPC997.rude`, with 143 rows of current quest/journal-like text.
- `NPC998.rude`, with 91 rows of autonote, trainer, and hint-like text.
- `NPC999.rude`, with 55 rows of award/completed-achievement text.

The extracted script directory contains:

- 715 `.scr` files.
- 87 `.inc` files.
- Frequent dialogue-relevant operations:
  - `DoRude`
  - `OnRudeExit`
  - `GiveKey`
  - `TakeKey`
  - `HasKey`
  - `GiveItem`
  - `TakeItem`
  - `HasItem`
  - `GiveGold`
  - `GiveExp`
  - `SetConsoleNumVar`
  - `GetConsoleNumVar`
  - `SetConsoleStrVar`
  - `GetConsoleStrVar`

The generated MM9 map object YAML files preserve many object properties relevant to dialogue binding, including
properties such as `ScriptName`, `ScriptParams`, `DoRude`, `NPCNbr`, `GreetingSound`, `Filename`, `UsesRails`, and
object class/name metadata.

## RUDE File Shape

Normal `NPC<number>.rude` dialogue files are fixed-width CSV-like records. In the extracted data, normal dialogue rows
have 30 columns.

The first six columns are well established:

| Column | Meaning |
| --- | --- |
| 1 | RUDE/NPC id |
| 2 | Node id |
| 3 | Choice slot/order within the node |
| 4 | Player prompt text |
| 5 | NPC response text |
| 6 | Next node id or service opcode |

Columns 7 through 30 are sparse numeric fields. In the current extracted data, nonzero values appear only in columns
7, 9, 11, 13, 16, 17, 18, 21, 22, 23, 24, and 26. The unused columns should still be preserved because they are part of
the original record layout and may have engine meaning.

Current evidence suggests:

- Columns 7, 9, 11, and 13 are condition-like key fields. Rows often become visible only when these key ids are present.
- Later sparse columns are action-like, reward-like, blocking, journal, award, or state-transition fields.
- Exact polarity and timing for every sparse column is not fully proven from static data alone.

The importer should therefore keep both a raw and semantic view:

```yaml
source:
  file: NPC1.rude
  row: 12
npc_id: 1
node_id: 4
choice_slot: 2
prompt: "..."
response: "..."
next: 999
raw_fields:
  c07: 27
  c09: 1
  c11: 40
  c13: 0
  c16: 499
  c17: 93
  c18: 0
  c21: 29
  c22: 469
  c23: 92
  c24: 0
  c26: 0
semantics:
  conditions: []
  actions: []
  validation: unverified
```

The `semantics` block should be generated only where importer validation has evidence. The `raw_fields` block must
survive unchanged for every row.

OpenYAMM should not runtime-parse raw `.rude` files as the long-term gameplay path. Raw RUDE files should remain source
inputs and audit references. The runtime should consume generated, lossless YAML or a package built from that YAML.

## Dialogue Flow

Dialogue is entered by scripts or object behavior calling `DoRude`. A typical NPC flow is:

1. A world object has NPC-related properties and an attached script or base NPC behavior.
2. The object receives player use/interaction.
3. The script stops or pauses movement/chat behavior.
4. The script calls `DoRude <npc_id>`.
5. The RUDE engine presents choices for the active node.
6. Selecting a choice displays the NPC response, evaluates row conditions/actions, and follows the `next` value.
7. When the dialogue closes, `OnRudeExit` script callbacks may resume movement or perform game logic.

This means dialogue cannot be imported as text alone. A correct import needs:

- the RUDE graph,
- the script entry point,
- the object that owns the script,
- the object properties used by the script,
- the key/item/variable state touched during dialogue,
- and the `OnRudeExit` callback behavior.

## Next Values And Service Opcodes

Column 6 is either a positive/zero node target or a negative service opcode.

Observed values:

- Positive values generally route to another dialogue node. `999` is commonly used as a terminal/goodbye-style node,
  but it is not merely a magic close value because many files define node `999` normally.
- `-1` is the most common explicit close/exit value.
- `0` appears in some pseudo-dialogue and note rows. It should be preserved and validated before assigning a final
  runtime meaning.
- Negative values below `-1` dispatch services or engine actions.

Observed negative opcodes:

| Opcode | Observed count | Current interpretation |
| --- | ---: | --- |
| `-1` | 1004 | Close/exit dialogue |
| `-2` | 48 | Shop/trade service |
| `-3` | 8 | Training hall or training service |
| `-4` | 115 | Skill training/mastery service |
| `-5` | 8 | Travel/transport service |
| `-6` | 7 | Bank service |
| `-7` | 7 | Inn room/rest service |
| `-8` | 8 | Healer/temple service |
| `-10` | 17 | Hire follower/service NPC |
| `-11` | 13 | Dismiss follower/service NPC |
| `-13` | 2 | Item combine/tinker-like service |
| `-14` | 11 | Quest/promotion handoff service; exact behavior needs validation |
| `-15` | 3 | Town portal/follower teleport service |
| `-16` | 7 | Temple donation/service |

These opcodes should be imported into a `rude_services` table and dispatched by typed OpenYAMM handlers. Unknown or
partially understood opcodes must still have a lossless fallback representation, but the runtime should not silently
pretend they are ordinary node links.

## State Model

MM9 uses several distinct state channels that should not be collapsed into a single QBit table.

### Global Key Bits

Script operations `GiveKey`, `TakeKey`, and `HasKey` manipulate global key-like state. These are the closest equivalent
to MM6-MM8 quest bits. MM9 is treated as core OpenYAMM content, so these keys should use the same underlying QBit
storage and save/load machinery, but the generated data should still preserve MM9 semantics and raw ids.

Required OpenYAMM representation:

```yaml
state_domain: mm9.keys
raw_id: 93
qbit_id: 9093
qbit_mapping: 9000 + raw_id
aliases:
  - YRSAS_QUEST_PENDING
evidence:
  - scripts/THJORGARDGAMESCOMMON.inc
  - rude/NPC1.rude
kind: quest_state
```

The importer should build this registry from both RUDE numeric fields and scripts. Script constants provide names for
some ids, while RUDE rows provide usage evidence even when no constant name is available. Runtime script APIs should
stay semantic:

```lua
ctx:hasKey(93)
ctx:giveKey(93)
ctx:takeKey(93)
```

The MM9 script context maps those calls to the shared QBit backend:

```text
mm9.keys.93 -> qbit 9093
```

This is intentionally not a lossy flattening into anonymous legacy QBits. Generated YAML, generated Lua metadata, and
debug UI should expose the raw MM9 key id and the derived QBit id. Tests must reserve the occupied range, assert that
MM6/MM7/MM8 authored QBits do not collide with it, and force custom/mod content to declare ranges above reserved core
ranges instead of assuming all ids above `10000` are free.

### Inventory Items

Scripts use separate `GiveItem`, `TakeItem`, and `HasItem` operations. These are not key bits. They must bind to the MM9
item registry and party inventory model.

### Console Variables

Scripts use `GetConsoleNumVar`, `SetConsoleNumVar`, `GetConsoleStrVar`, and `SetConsoleStrVar`. These appear to be
global or world-level script variables. Examples include puzzle and quest counters, target levels, game-state flags, and
string variables.

Recommended representation:

```yaml
state_domain: mm9.console_vars
name: WHACK_COUNTER
type: number
scope: global_or_world
evidence:
  - scripts/...
```

The exact persistence and scoping rules should be verified in the LithTech script runtime behavior before gameplay
implementation. For import, preserving variable names, types, operations, and source references is sufficient.

### Object And Script Local State

Script-local variables and object properties drive many interactions. This includes NPC object properties such as
`NPCNbr`, movement settings, sound names, script parameters, and trigger bindings.

Recommended representation:

```yaml
object_binding:
  map: drangheim
  object_name: "..."
  object_class: "..."
  properties:
    ScriptName: "..."
    ScriptParams: "..."
    DoRude: true
    NPCNbr:
      decoded: null
      raw_hex: "..."
  dialogue:
    rude_id: null
    validation: pending_property_decode
```

Some generated object property values are currently decoded as raw float/integer payloads in YAML. The importer should
preserve `raw_hex` and the original property type metadata until the DAT property typing is fully corrected.

## Scripts And RUDE Coupling

RUDE files alone are insufficient. Scripts explicitly call `DoRude` and register `OnRudeExit` callbacks.

Two important patterns:

- Generic NPC behavior pauses movement/chat, faces the player, enters RUDE, then resumes behavior on `OnRudeExit`.
- Quest or service scripts use `OnRudeExit` to apply rewards, resume combat, update key state, or continue map logic.

The import pipeline should build a script index containing:

- every `DoRude` call and its target id,
- every `OnRudeExit` registration and callback label,
- every key operation,
- every item operation,
- every gold/experience/reward operation,
- every console variable operation,
- every object parameter read,
- and every trigger that can lead into dialogue.

Recommended output:

```yaml
script_binding:
  source: SCRIPTS/NPCBASE.inc
  labels:
    - OnUse
    - OnRudeExit
  dialogue_calls:
    - op: DoRude
      npc_id: dynamic_or_constant
  rude_exit_callbacks:
    - label: OnRudeExit
  state_ops:
    - op: HasKey
      key: 93
      evidence: constant_or_literal
```

For runtime implementation, the end goal should be generated Lua scripts. The safe path is still a two-step pipeline:

```text
*.scr / *.inc -> script IR -> generated *.lua
```

The IR should preserve labels, commands, parameters, include relationships, and source locations. The generated Lua can
then call OpenYAMM services such as `ctx:doRude(...)`, `ctx:onRudeExit(...)`, `ctx:giveKey(...)`, and
`ctx:getConsoleNumVar(...)`. Hand-copying behavior into ad hoc Lua should be avoided because it will lose source
correspondence and make future validation difficult.

## Pseudo-NPC Dialogue Files

`NPC997.rude`, `NPC998.rude`, and `NPC999.rude` are not normal people to talk to. They are RUDE-shaped content tables
for journal and status UI.

Recommended treatment:

- `NPC997.rude`: current quest/journal entries.
- `NPC998.rude`: autonotes, trainer notes, location hints, and similar reference text.
- `NPC999.rude`: awards or completed-achievement text.

These should be imported with the same row-preservation rules as normal RUDE files, then exposed through OpenYAMM
journal/autonote/award systems. They should not be discarded just because they are not normal NPC conversations.

The rows in these files also provide key usage evidence. For example, completed-award rows are often keyed by the same
global key ids that scripts set after quest completion.

## Map Object Dialogue Binding

Dialogue entry is tied to placed objects. In generated MM9 map object YAML, NPC-like objects can include properties such
as:

- `NPCNbr`
- `Filename`
- `GreetingSound`
- `UsesRails`
- `DoRude`
- `ScriptName`
- `ScriptParams`

The importer should build a map-level dialogue binding table:

```yaml
map: drangheim
objects:
  - object_index: 123
    object_class: WorldObject
    object_name: "..."
    script_name: "..."
    script_params: "..."
    rude:
      enabled: true
      npc_id:
        value: null
        raw_property: NPCNbr
        decode_status: pending
    greeting_sound: "..."
    source:
      raw_objects_yml: assets_dev/worlds/mm9/maps/drangheim.raw_objects.yml
```

This table is important for validation. Every placed dialogue-capable NPC should resolve to a RUDE id, a name row, a top
blurb row, and any script behavior needed for interaction.

One verified runtime wrinkle is script-name casing. Object bindings preserve authored values such as `SvenArena.scr`,
while generated script assets may be keyed as `SVENARENA.scr` / `SVENARENA.lua`. The runtime should therefore resolve
script references case-insensitively, but generated YAML must still preserve the original authored string for
round-trip/debug fidelity.

## Doors, Triggers, And Non-NPC Interaction

The statement that MM9 likely has no interaction with doors or other map objects is not correct. Dialogue is heavily
NPC-centered, but the extracted maps and scripts include many interactive doors, rotating doors, triggers, props,
buttons, locked doors, exit triggers, puzzle scripts, and object-use scripts.

For dialogue integration, the practical rule is:

- import RUDE as the primary dialogue graph system,
- import map/object scripts separately,
- preserve cross-links where scripts enter RUDE or where RUDE exit returns to script logic.

Door and trigger scripts do not need to be modeled as dialogue, but they do need to share the same MM9 state domains.
A door script may depend on an item, key, console variable, or quest key that was affected by dialogue.

## Recommended OpenYAMM Transcode Outputs

The intended end state is:

```text
mm9/extracted/RUDE/RUDE/*.rude       -> assets_dev/worlds/mm9/dialogue/**/*.yml
mm9/extracted/SCRIPTS/SCRIPTS/*.scr  -> assets_dev/worlds/mm9/scripts/**/*.lua
mm9/extracted/SCRIPTS/SCRIPTS/*.inc  -> generated Lua include modules or expanded dependencies
```

Generated files should be treated as OpenYAMM-authored derived data. The original extracted files remain the source
inputs, and regeneration should be deterministic.

Suggested generated files under `assets_dev/worlds/mm9/dialogue/`:

- `npc_names.yml`
  - Generated from `NPCNAME.rude`.
- `top_blurbs.yml`
  - Generated from `TOPBLURB.rude`.
- `npcs/<id>.yml`
  - Generated from every normal `NPC<number>.rude` file.
  - Preserves all 30 columns, original row order, source file, and row number.
- `services.yml`
  - Defines observed negative opcodes and maps them to typed runtime services.
- `journal_quests.yml`
  - Generated from `NPC997.rude`.
- `journal_notes.yml`
  - Generated from `NPC998.rude`.
- `awards.yml`
  - Generated from `NPC999.rude`.
- `quest_keys.yml`
  - Generated by combining RUDE tail fields, script key operations, and script constants.
- `script_bindings.yml`
  - Generated from `.scr`/`.inc` scans.
- `object_dialogue_bindings.yml`
  - Generated from map raw object YAML and DAT object properties.

Suggested generated files under `assets_dev/worlds/mm9/scripts/`:

- `<script-name>.lua`
  - Generated Lua equivalent for each `.scr` runtime script.
- `includes/<include-name>.lua`
  - Generated Lua modules for reusable `.inc` logic, or generated expanded dependencies where a module is not suitable.
- `script_index.yml`
  - A static operation index for every script.
- `script_ir/*.yml`
  - Intermediate representation used to validate and generate Lua.
- `source/*.scr` and `source/*.inc`, or source references to the extracted originals.
  - Preserve source correspondence. Do not make manual one-off rewrites the authoritative behavior.

## Runtime Model Recommendation

Reuse the OpenYAMM dialogue GUI, but add an MM9 RUDE-backed dialogue provider behind it. The GUI already matches the
visible interaction pattern: show available topics, let the player click a topic, display NPC text, and refresh topics
after state changes. The part that must stay MM9-specific is the backend that decides which topics are visible and what
happens after a choice is selected.

Recommended shape:

```text
OpenYAMM dialogue GUI
    -> DialogueProvider
        -> MM6/MM7/MM8 table provider
        -> MM9 RUDE graph provider
```

Do not extend the MM6-MM8 flat NPC topic table model until it becomes a second RUDE implementation. MM9 should have a
graph resolver that presents rows through the same UI surface.

The resolver should:

1. Enter dialogue from an object/script context, not only from an NPC id.
2. Load the RUDE graph for the selected id.
3. Evaluate rows for the current node against MM9 key state, inventory state, console vars, and any validated row
   conditions.
4. Sort visible choices by choice slot and original row order.
5. Display player prompt and NPC response.
6. Apply validated row side effects at the same interaction point as the original runtime.
7. Dispatch `next`:
   - positive values to graph nodes,
   - `999` as a normal node when present,
   - `-1` as close,
   - other negative values through typed service handlers,
   - `0` through a preserved, validated behavior path.
8. Fire the owning script's `OnRudeExit` callback when dialogue closes.

The resolver should operate on namespaced MM9 state:

- `mm9.keys`
- `mm9.console_vars`
- `mm9.script_locals`
- `mm9.object_properties`
- shared party inventory/gold/experience where original scripts use item or reward operations.

MM9 keys are qbit-backed through the reserved `9000 + raw_mm9_key` mapping. They should still be represented in content
and script APIs as MM9-owned imported state with explicit aliases, not as hand-authored MM6-MM8 quest bits.

Current runtime loading treats validated condition blocks as explicit semantics. Generated rows with
`semantic.conditions.required_keys` map to `mm9.keys`, `required_items` map to shared party inventory,
`required_console_num_equals` maps to numeric console vars, and `required_console_str_equals` maps to string console
vars. Unknown sparse RUDE columns must stay in provenance/validation output until independently decoded; they should
not be guessed into runtime gates.

Lua is still part of the runtime model, but not as hand-maintained dialogue branches for every RUDE row. Generated Lua
should represent original `.scr`/`.inc` behavior and provide script callbacks around dialogue, while generated YAML
remains authoritative for the RUDE graph itself.

## Data Preservation Rules

The importer should be lossless before it is clever.

Required preservation:

- original extracted RUDE and script files as regeneration inputs or traceable source references,
- every RUDE row,
- every column in every RUDE row,
- original file name and row number,
- original NPC id and node id,
- original text fields,
- original `next` value,
- all sparse numeric fields, including zeros,
- original row order,
- every script source file and label,
- every `DoRude` and `OnRudeExit` reference,
- every key/item/console-var operation,
- every object property needed to enter or parameterize dialogue.

Allowed semantic enrichment:

- constant names recovered from `.inc` files,
- service names for validated negative opcodes,
- condition/action classification where statically proven,
- references from quest journal rows to key ids,
- references from placed map objects to RUDE ids after object property decoding is validated.

Disallowed import shortcuts:

- flattening RUDE into MM6-MM8 `npc_topic` style rows only,
- making raw `.rude` runtime parsing the only authoritative implementation path,
- hand-writing per-NPC Lua fixups instead of generating Lua from `.scr`/`.inc` through a validated pipeline,
- dropping unknown sparse columns,
- assuming every positive `next` value is a visible node without validating the target,
- treating `999` as a universal close opcode,
- treating `GiveKey`/`HasKey` as inventory,
- applying `OnRudeExit` behavior manually in unrelated gameplay code,
- silently ignoring unknown service opcodes.

## Validation Plan

Static validation should be part of the importer:

- Assert every normal `NPC<number>.rude` row has 30 columns.
- Assert `NPCNAME.rude` has 2 columns per row.
- Assert `TOPBLURB.rude` has its expected id/top-blurb shape.
- Count rows per source file before and after import.
- Count all nonzero sparse numeric fields before and after import.
- Emit a warning for every unknown negative `next` opcode.
- Emit a warning for every positive `next` that has no matching node in the same RUDE file, except for cases validated
  as engine-defined behavior.
- Cross-reference every RUDE id with `NPCNAME.rude` and `TOPBLURB.rude`.
- Cross-reference every placed object with `DoRude` or NPC script behavior to a RUDE id.
- Cross-reference every RUDE key value to script constants, script key operations, journal rows, or an unknown-key
  registry entry.
- Cross-reference every `DoRude` script call to a RUDE file.
- Cross-reference every `OnRudeExit` callback to a script label.

Runtime validation should cover representative interactions:

- a normal quest NPC with branching and quest keys,
- a shop (`-2`),
- a trainer (`-3` or `-4`),
- a healer (`-8`),
- a bank (`-6`),
- an inn (`-7`),
- a travel NPC (`-5`),
- a hire/dismiss service (`-10` and `-11`),
- a town portal service (`-15`),
- an arena or scripted quest NPC with `OnRudeExit` side effects,
- journal/current quest rendering from `NPC997`,
- notes from `NPC998`,
- awards from `NPC999`.

## Open Questions

These need targeted runtime or deeper reference validation:

- Exact semantics and timing for each sparse RUDE tail column.
- Exact behavior of `next == 0`.
- Exact service behavior for `-14`.
- Whether all `999` nodes are authored terminal nodes or whether any file relies on engine fallback behavior.
- Complete DAT property type decoding for NPC id fields such as `NPCNbr`.
- Persistence and scope rules for console variables.
- Whether any dialogue can be entered through non-NPC objects using RUDE ids not present in visible NPC placement data.
- Whether the original engine applies RUDE side effects before response display, after response display, or on node
  exit.

## Implementation Order

Recommended order for future work:

1. Build a RUDE parser that preserves rows exactly and emits YAML.
2. Build script and key scanners for `.scr` and `.inc`.
3. Build a script parser that emits source-preserving IR.
4. Generate Lua from the validated script IR.
5. Build a key registry from scripts plus RUDE numeric fields.
6. Build pseudo-NPC journal/note/award importers.
7. Fix or validate DAT object property decoding for NPC dialogue bindings.
8. Build `object_dialogue_bindings.yml`.
9. Implement a read-only MM9 dialogue graph inspector in tools or editor.
10. Add an MM9 RUDE provider behind the existing OpenYAMM dialogue GUI.
11. Implement the runtime MM9 dialogue resolver with no service side effects.
12. Add typed service handlers for each validated negative opcode.
13. Wire generated Lua script callbacks, especially `OnRudeExit`, into dialogue close behavior.
14. Add focused runtime tests for representative NPCs and services.

The important architectural choice is to make the imported MM9 data authoritative and complete. Semantic mappings can
improve over time, but the raw graph, script links, state ids, and object bindings should be preserved from the first
import so later fixes do not require rediscovering original content.
