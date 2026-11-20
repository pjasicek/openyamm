# MM9 Monster And NPC Loot Implementation Goal

## Status

Planning and native-behavior recovery are complete. Implementation is pending.

The current OpenYAMM MM9 conversion is not a faithful approximation of actor death loot. It emits item-only
`25%L...` definitions for item-bearing MM9 monsters, emits no gold for generated MM9 monster profiles, and lets MM9
NPCs inherit unrelated MM6-MM8 loot from the legacy actor ids selected for their temporary visuals.

This document owns the correction of normal MM9 monster and NPC death loot. It does not own authored chests, authored
or destructible treasure bags, bone piles, ordinary world pickups, dialogue rewards, or scripted death actions.

## Goal

Restore source-backed Might and Magic IX death loot for every imported MM9 actor that uses the native
`GiveTreasure` path:

- preserve the original independent gold and item decisions;
- generate gold from MM9 `Treasure Level` exactly;
- preserve the distinct `None`, `Item`, `Weapon`, `Armor`, and `Random` item pools;
- reproduce the Luck-sensitive zero/one/two-item count roll;
- preserve fixed or scripted death items without replacing procedural loot;
- attach loot to the MM9 source actor profile rather than its temporary MM6-MM8 visual replacement id;
- materialize loot once at the source-equivalent lifecycle point and preserve it across save/load; and
- leave MM6, MM7, MM8, and MMerge actor loot unchanged.

Implement this through shared corpse/container, item-generation, party, map-state, and save systems. Do not add an
MM9 ObjectDLL runtime, general SCR runtime, second inventory, second item catalog, or separate corpse UI.

## Ownership Boundaries

This goal complements, but does not duplicate, the following documents:

- `MM9_ITEM_SOURCE_IMPLEMENTATION_PLAN.md` owns authored chests, authored and destructible treasure bags, bone piles,
  world pickups, and the generated census of `GiveTreasure` properties.
- `MM9_SCRIPTED_ACTOR_IMPORT_GOAL.md` owns actor identity, presence, hostility transitions, QBit mutations, scripted
  `OnDeath` actions, and other actor lifecycle behavior.
- `MM9_ITEM_ADDON_INTEGRATION_GOAL.md` owns MM9 item definitions, canonical ids, portable catalog contribution, and
  explicit eligibility for procedural distribution.
- This document owns the ordinary procedural payload produced when an MM9 actor dies with `GiveTreasure` enabled.

A scripted death action and ordinary death loot are independent. Granting a QBit, spawning a quest object, or adding a
fixed death item must not silently disable the normal MM9 gold and item roll.

## Source Authority

Use local sources in this order:

1. `mm9/extracted/DATA/DATA/MONSTERS.txt` in this repository.
2. `/home/pjasicek/github/OpenMM9/assets_dev/source/data/MONSTERS.txt`, which is byte-identical to the local extract.
3. `/home/pjasicek/github/OpenMM9/reference/game/data/object.lto` and its decompiled
   `object.lto.c` representation.
4. Original extracted DAT objects for per-instance `GiveTreasure` and fixed-item properties.
5. Current shared OpenYAMM corpse, item, actor, map-delta, and save systems as the target runtime contract.

Relevant recovered native functions and addresses are:

| Address | Decompiled function | Recovered responsibility |
| --- | --- | --- |
| `0x10042DE0` | `function_10042de0` | Parse `MONSTERS.txt`, including treasure type and level. |
| `0x10052B00` | `function_10052b00` | Build per-actor stats and roll the actor's gold amount. |
| `0x1001AD60` | `function_1001ad60` | Create the normal death `TreasureBag` AIDrop payload. |
| `0x10030580` | `function_10030580` | Create a specialized AIDrop payload with fixed `Item1`. |
| `0x10079AC0` | `function_10079ac0` | Parse a treasure payload and materialize generated/fixed items. |
| `0x10079E60` | `function_10079e60` | Award or transfer the stored gold and generated item list. |
| `0x100B7740` | `function_100b7740` | Roll zero, one, or two AIDrop items and generate them. |
| `0x10046EB0` | `function_10046eb0` | Select an eligible item for the requested type and level. |
| `0x100486A0` | `function_100486a0` | Filter source item categories for the treasure type. |

Do not copy decompiled code. Reimplement the recovered behavior in clear OpenYAMM code and cover every rule with
focused tests.

## Recovered Original Behavior

### Source columns

The authoritative `MONSTERS.txt` fields are:

- column 12: `TreasureType`;
- column 61: `IsMonster`;
- column 64: `Treasure Level`.

`IsMonster` controls content classification. It does not disable the shared native actor-stats gold calculation.
Killable NPC archetypes and monster archetypes therefore use the same treasure-type and treasure-level rules.

### `GiveTreasure` gate

The native actor property defaults to enabled. Loading `GiveTreasure=false` initializes the actor as though its
treasure had already been produced, preventing the normal death payload. A true value permits the ordinary death
path.

The current source census contains 1,911 explicit `GiveTreasure` properties, all true, across 34 raw map exports. This
is an audit baseline, not a hardcoded gameplay table. Regeneration must continue to report true, false, absent/default,
and invalid values separately.

Per-instance state must remain per-instance. Two actors sharing the same source profile may have different
`GiveTreasure` values without leaking behavior to one another.

### Gold generation

Gold depends only on `Treasure Level`. It does not depend on `TreasureType`.

| Treasure level | Native gold roll | Range | Mean |
| ---: | ---: | ---: | ---: |
| 0 or invalid | none | 0 | 0 |
| 1 | `4d6` | 4-24 | 14 |
| 2 | `10d25` | 10-250 | 130 |
| 3 | `20d30` | 20-600 | 310 |
| 4 | `50d24` | 50-1,200 | 625 |
| 5 | `100d20` | 100-2,000 | 1,050 |
| 6 | `100d40` | 100-4,000 | 2,050 |

The shipped monster rows use levels zero through five, but the recovered engine supports level six. Unknown levels
must not be clamped silently; source validation should reject an unsupported value unless a documented content
override handles it.

The native actor-stats constructor rolls and stores gold when the actor stats instance is initialized. The death path
then copies that stored value into the AIDrop payload. A positive-level actor therefore has positive gold even when its
item roll returns no item.

### Death payload

The normal native death path creates an equivalent payload to:

```text
TreasureBag
TreasureType0_7 <type>
TreasureLevel <level>
Gold <precomputed amount>
AIDrop 1
```

It creates no normal bag when stored gold is zero. Consequently:

- `GiveTreasure=true` plus level zero normally produces no procedural payload;
- `GiveTreasure=true` plus a positive level always produces gold; and
- an item-capable type may produce gold with zero, one, or two items, but never an item-only normal payload.

OpenYAMM may continue to present the equivalent payload through its shared corpse transfer view. It does not need to
spawn a literal MM9 bag model, but the materialized contents, one-shot transfer, and save behavior must be equivalent.

### Treasure-type mapping

The source parser maps treasure tokens as follows:

| Source token | Native value | Required result |
| --- | ---: | --- |
| `None`, empty, unknown legacy `0` | 0 | Gold only; no procedural item generation. |
| `Item` | 1 | Gold plus the MM9 item/accessory/magic pool. |
| `Weapon` | 2 | Gold plus the MM9 weapon pool. |
| `Armor` | 3 | Gold plus the complete MM9 armor pool. |
| `Random` | 8 | Gold plus the broad non-unique regular-item pool. |

The importer must treat the shipped case variations consistently while preserving the original token in provenance.
An unknown nonzero text token is a generation error, not `Random` and not `None`.

The recovered source category membership is:

- `Item`: rings, amulets, skill items, magic runestones, magic scrolls, potions, and general magic items;
- `Weapon`: one-handed weapons, two-handed weapons, and ranged weapons;
- `Armor`: body armor, helms, boots, gloves, shields, and belts; and
- `Random`: regular item categories except artifacts, relics, relic sets, and quest items.

Do not collapse `Item` and `Random` into the same unfiltered pool. Do not interpret `Armor` as body armor only.
Distribution membership must use canonical item definitions or explicit data-owned compatibility mappings, not raw
MM9 ids at runtime.

### Generated item count and Luck

For an item-capable treasure type, native MM9 computes:

```text
adjusted roll = random integer 1..100 + best current party Luck modifier
```

The result selects:

| Adjusted roll | Generated item count |
| ---: | ---: |
| `<= 5` | 0 |
| `6..75` | 1 |
| `> 75` | 2 |

With a zero Luck modifier, the probabilities are therefore 5% zero items, 70% one item, and 25% two items. Positive
Luck reduces zero-item outcomes and increases two-item outcomes; negative Luck does the reverse.

Use the same centralized MM9-to-shared Luck projection as other MM9 gameplay. Do not read a raw MM9 stat id directly
inside corpse code. The roll must use an injected gameplay RNG so tests and saved materialization are deterministic;
do not use a hidden `thread_local` generator seeded from `std::random_device`.

### Item-tier selection

For each generated item, native MM9 converts treasure level to a normalized source item tier using these
probabilities:

| Treasure level | Target-tier distribution |
| ---: | --- |
| 1 | tier 1: 50%, tier 2: 40%, tier 3: 10% |
| 2 | tier 1: 25%, tier 2: 50%, tier 3: 25% |
| 3 | tier 1: 15%, tier 2: 40%, tier 3: 30%, tier 4: 15% |
| 4 | tier 2: 20%, tier 3: 40%, tier 4: 30%, tier 5: 10% |
| 5 | tier 3: 15%, tier 4: 50%, tier 5: 35% |
| 6 | tier 6: 100% |

It then selects among items eligible for both the requested treasure type and target tier. The current shared
MM6-MM8 `ItemGenerationRequest{treasureLevel}` path does not by itself represent this two-stage distribution.

Phase 0 must finish the focused native audit of post-selection enchantment and special-item behavior before declaring
full item-generation parity. Known gold, count, category, and tier rules must not be weakened while that remaining
behavior is recovered.

### Fixed and scripted items

The specialized recovered actor path can add `Item1` to the same AIDrop payload as generated contents. TreasureBase
also recognizes fixed `Item1` through `Item5` fields.

Therefore, a fixed carried or scripted item is not general evidence that procedural MM9 items should be disabled. The
current shared corpse builder suppresses its random item roll whenever any guaranteed item is present; preserve that
behavior for worlds that depend on it, but do not apply it to MM9 when the source path combines fixed and procedural
contents.

Before implementing this corner, complete a focused audit of the native zero-generated-list path and every MM9 actor
class that emits a fixed AIDrop item. Record whether each fixed item is unconditional or conditional. Do not relabel a
conditional native item as universally guaranteed.

### Materialization and persistence

Native timing is:

1. Roll and store actor gold during actor-stats initialization.
2. On eligible death, create the AIDrop and materialize its generated item list.
3. Open or transfer the already materialized contents without rerolling.

OpenYAMM must preserve the same observable lifetime:

- saving and loading a living actor must not reroll initialized gold;
- saving immediately after death but before opening the corpse must retain gold and items;
- reopening, stealing, auto-looting, closing, map transitions, and process restart must not reroll remaining contents;
- resurrection must not duplicate already transferred rewards; and
- actual source-backed repopulation may create a new actor instance and therefore a new loot state.

The existing serialized corpse-view state should remain the owner after death. Add only the minimal pre-death actor
loot state needed for native timing. Do not serialize the same materialized payload independently in actor state,
corpse state, and Lua.

## Source Census And Current Defects

### MM9 monster profiles

The current source contains 134 rows with `IsMonster=1`:

| Native profile outcome | Count |
| --- | ---: |
| Level zero, intentionally no normal procedural payload | 3 |
| Positive level with `None` or `0`: gold only | 25 |
| Positive level with `Item`, `Weapon`, `Armor`, or `Random`: gold plus item-count roll | 106 |

The current `generate_mm9_monster_tables.py` instead emits:

- 28 zero-loot definitions;
- 106 item-only `25%L...` definitions; and
- no gold dice for any generated MM9 monster profile.

The invented 25% chance must be removed. It is not a conservative native approximation: 25% is the normal chance of
two items after gold has already been included, not the chance of receiving one item without gold.

Required representative corrections include:

| Source actor | Source treasure | Current result | Required result |
| --- | --- | --- | --- |
| 75, Dragonfly Mite | `None`, level 1 | empty | `4d6` gold only |
| 77, Fire Dragonfly | `Item`, level 1 | 25% one L1 item, no gold | `4d6` gold plus MM9 item roll |
| 84, Lobber Pod | `None`, level 0 | empty | empty |
| 204, Plain Giant | `0`, level 5 | empty | `100d20` gold only |
| 212, Dragon King | `0`, level 5 | empty | `100d20` gold only |

### MM9 NPC profiles

The current NPC replacement table contains 121 source-profile rows. Their source treasure behavior is:

| Native profile outcome | Count |
| --- | ---: |
| Level zero | 25 |
| Positive level, gold only | 77 |
| Positive level, gold plus item-count roll | 19 |

OpenYAMM currently emits the selected `legacy_actor_id` as the NPC's `monster_id`. Loot lookup consequently uses the
MM6-MM8 replacement's treasure definition. Forty of the 121 unique replacement rows currently disagree even on the
broad empty/gold/item outcome category; most apparent category matches still use the wrong gold dice, item tier, or
item pool.

Legacy replacement ids are temporary visual/animation compatibility choices. They must not own MM9 NPC combat
rewards. For example:

- source NPC 1, Commoner, is `None`, level 1 and should use `4d6` gold, not the mapped peasant's `2d6`;
- source NPC 123, Initiate, is `Item`, level 2 and should use `10d25` plus the MM9 item roll, not an item-only legacy
  amulet chance; and
- source profile 261, Njam the Meddler, is level zero and should not acquire a legacy swordsman's loot merely because
  that actor supplies a temporary visual replacement.

The generated audit must distinguish unique source profiles from instantiated actors so duplicated actors do not hide
an unbound profile and shared profiles do not inflate coverage.

## Target Architecture

### Typed, package-owned death-loot profiles

Add a generic typed death-loot profile capability that mounted content can reference, while keeping the MM9 profile
data under `assets_dev/worlds/mm9/`. A representation equivalent to the following is sufficient:

```yaml
actor_death_loot_profiles:
  - canonical_id: mm9:actor-loot/77
    package_id: mm9
    source_actor_number: 77
    generation_policy: mm9_ai_drop
    source_treasure_type: Item
    treasure_type: item
    treasure_level: 1
    gold_dice: 4d6
    item_count_policy: mm9_party_luck
    max_generated_items: 2
```

The exact table format may use the established package-contribution conventions, but it must preserve:

- stable canonical profile identity;
- owning package and source row provenance;
- original treasure token and normalized type;
- treasure level and derived gold formula;
- item-count and item-selection policy; and
- an importer/schema version for stale-generation checks.

Generate one profile per required source actor row, including NPC rows. Do not duplicate the same rules into generated
scene YAML, MM9 monster-data treasure strings, and handwritten C++ tables.

### Actor and monster-profile binding

An actor may resolve its death-loot profile from:

1. an explicit source-actor binding on the map/runtime actor; or
2. the actor's content-owned monster-stat/template profile when no per-actor binding exists.

The explicit binding is required for MM9 NPCs that retain a legacy `monster_id` for visual compatibility. Generated
MM9 monster-stat rows should reference the same canonical profile so dynamically spawned source monsters inherit it.
The profile definition remains singular; multiple actors and templates may reference it.

Generated bindings must use stable MM9 source actor number and source-object provenance. They must not infer MM9 loot
at runtime from display name, model name, temporary legacy id, `9000 + source number`, or active-world string tests.

MM6-MM8 actors without a typed profile continue to use the existing classic `MonsterTable::LootPrototype` path.

### Shared materializer with explicit policies

Refactor corpse construction around a shared materialization input rather than adding a parallel MM9 corpse system.
The shared materializer should accept:

- the resolved death-loot profile or classic loot prototype;
- per-instance `GiveTreasure` state;
- fixed/carried/scripted item records;
- party context required by the selected policy;
- source-stable RNG/state; and
- item, enchantment, and distribution registries.

Classic and MM9 policies may select different gold, count, and item algorithms, but both must produce the same
`GameplayCorpseViewState` and use the same transfer, held-item, auto-loot, stealing, empty-corpse, and save systems.

Do not add MM9 conditionals independently to `IndoorWorldRuntime` and `OutdoorWorldRuntime`. Resolve and materialize
through one shared gameplay service; indoor/outdoor code should supply world representation and persistent actor
identity only.

### MM9 item distribution contribution

This goal is the explicit consumer that enables accepted MM9 items for actor-drop distribution. Generate or maintain
a data-owned distribution index keyed by:

- MM9 treasure pool;
- normalized source item tier; and
- canonical global item id.

The index must classify every source item row relevant to used death-loot pools as one of:

- eligible imported MM9 item;
- explicit mapping to an existing shared equivalent;
- excluded unique/quest content;
- intentionally unsupported category with a blocking reason; or
- invalid source data.

Do not let all imported items enter random loot automatically. Do not choose unrelated MM6-MM8 items merely because
an MM9 category has no candidate. Spellbooks, spell scrolls, potions, runestones, wands, and other categories governed
by `MM9_ITEM_ADDON_INTEGRATION_GOAL.md` require its explicit mapping/exclusion policy.

Selection must preserve the recovered category and target-tier rules. If a required pool/tier has no eligible item,
generation must fail in tests and diagnostics rather than silently changing the treasure type or dropping the item
roll.

### Difficulty and bolster behavior

The default MM9 fidelity profile uses the native gold dice, item-count thresholds, and tier distributions unchanged.
Do not pass MM9 AIDrop profiles through the current generic bolster transformation implicitly.

If the flat base later defines a difficulty profile that scales MM9 rewards, that change must be explicit,
data-owned, separately tested, and applied after the recovered base profile is established. It must not change
MM6-MM8 reward scaling or make source-parity tests depend on current party difficulty.

### Runtime and package cost

The typed profile registry may be generic, but MM9 profile rows and distribution indexes load only when the MM9
package is mounted. With MM9 absent:

- classic table parsing and corpse materialization remain unchanged;
- no MM9 profile audit or source lookup runs;
- no MM9 item distribution is composed; and
- there is no meaningful startup, map-load, memory, or per-frame cost.

## Implementation Phases

### Phase 0: Close the native item-path audit

- Record the known gold, count, category, and tier rules in focused recovery tests or fixtures.
- Recover the remaining post-selection enchantment/special-item behavior used by AIDrop.
- Audit `function_10030580` and every fixed-item actor class/binding that reaches it.
- Confirm the source-equivalent Luck modifier projection and boundary values.
- Emit a deterministic source census for all actor treasure type/level combinations and DAT `GiveTreasure` values.

Do not block the exact gold fix on unrelated MM9 systems, but do not declare complete item-generation parity while a
reachable native mutation remains unknown.

### Phase 1: Typed profile schema and importer

- Add the generic package-contributed death-loot profile schema and loader.
- Extend `generate_mm9_monster_tables.py` or a single authoritative companion generator to emit profiles from
  `MONSTERS.txt`.
- Remove the invented `25%L...` output from MM9-generated monster definitions.
- Emit deterministic profile and census reports with source hashes and regeneration commands.
- Fail generation on unknown nonzero type tokens, unsupported levels, duplicate canonical ids, or stale profile data.

Do not hand-edit generated MM9 monster tables or scene actors.

### Phase 2: Actor binding

- Reference the canonical profile from every generated MM9 monster template.
- Attach the source profile explicitly to MM9 NPC actors independently of `legacy_actor_id`.
- Carry the profile through supported dynamic/source spawn paths.
- Preserve per-instance `GiveTreasure` and fixed-item data.
- Ensure scripted actor profiles reference ordinary loot rather than cloning its contents.

### Phase 3: Shared native-policy materialization

- Add injected-RNG gold initialization and persistent pre-death state.
- Add the Luck-sensitive zero/one/two-item policy.
- Add MM9 target-tier selection and distinct item-pool filtering.
- Materialize the corpse payload on eligible death and serialize it through existing corpse-view state.
- Keep classic materialization behavior byte-for-byte or behaviorally unchanged through focused regression tests.

### Phase 4: Distribution and fixed-item closure

- Generate the explicit MM9 actor-drop distribution contribution.
- Resolve every used category/tier combination to eligible canonical items.
- Implement recovered fixed-plus-procedural semantics without globally changing classic guaranteed-item behavior.
- Validate enchantments, identification, charges, quantity, and other item-instance fields against recovered native
  behavior and normalized shared item rules.

### Phase 5: Regeneration and runtime closure

- Regenerate all MM9 monster tables, maps, actor bindings, and audit reports from source.
- Run unit, importer, save-roundtrip, indoor, outdoor, dynamic-spawn, and headless MM9 scenarios.
- Validate representative MM6, MM7, and MM8 corpse-loot paths in the same build.
- Package MM9 and verify mounted and unmounted startup/map-load behavior.

## Required Verification

### Pure logic tests

Add deterministic tests for:

- every treasure-level gold formula, including invalid/zero handling;
- source-token normalization and rejection of unknown nonzero tokens;
- the Luck-adjusted item-count thresholds at rolls 1, 5, 6, 75, 76, and 100;
- negative, zero, and positive Luck modifiers;
- every target-tier distribution boundary;
- `Item`, `Weapon`, `Armor`, and `Random` category membership;
- exclusion of artifacts, relics, sets, and quest items from `Random`;
- zero, one, and two generated item results;
- fixed-plus-procedural behavior after its source audit; and
- deterministic replay from an injected RNG sequence.

### Importer and data tests

The generated audit must prove at least:

- 134 current `IsMonster=1` source profiles are accounted for;
- their baseline split remains 3 level-zero, 25 positive-level gold-only, and 106 item-capable profiles unless the
  authoritative source file changes;
- all 121 current NPC replacement rows have a source death-loot profile;
- their baseline split remains 25 level-zero, 77 gold-only, and 19 item-capable profiles unless source changes;
- the DAT census reports the current 1,911 explicit true `GiveTreasure` values and any future false/default values;
- no generated MM9 monster uses an invented `25%L...` treasure definition;
- no MM9 NPC death-loot decision depends on its `legacy_actor_id`;
- every used item pool/tier has eligible canonical candidates; and
- regeneration is deterministic and fails when generated output is stale.

Counts are guarded source baselines, not runtime constants. A legitimate source-data update should require an explicit
reviewed expectation update.

### Runtime acceptance cases

Cover at least these actors with deterministic rolls:

1. Dragonfly Mite, source 75: `4d6` gold and no random item.
2. Fire Dragonfly, source 77: `4d6` gold plus zero, one, and two `Item` outcomes across controlled rolls.
3. Lobber Pod, source 84: no normal procedural payload at level zero.
4. Plain Giant, source 204: `100d20` gold despite source treasure type `0`.
5. Dragon King, source 212: `100d20` gold and no procedural item.
6. Commoner, source 1: native level-1 gold rather than the temporary legacy peasant's dice.
7. Initiate, source 123: level-2 gold plus native item roll rather than the legacy item-only amulet chance.
8. A `GiveTreasure=false` fixture: fixed/scripted behavior may remain, but no ordinary procedural payload appears.
9. A fixed-item fixture: recovered fixed and procedural contents coexist exactly as the source path requires.
10. A dynamically spawned MM9 monster: it inherits the same canonical profile as a map-authored instance.

For representative indoor and outdoor actors, prove:

- death materializes loot before first interaction;
- save before death retains initialized gold;
- save after death but before opening retains the exact payload;
- partial transfer and save retain the exact remainder;
- close/reopen, map transition, and process restart do not reroll;
- resurrection or repeated death callbacks do not duplicate transferred rewards; and
- empty corpses follow existing cleanup and visibility rules.

### Regression gates

- Existing MM6-MM8 gold and item probabilities remain unchanged.
- Classic guaranteed-item suppression remains unchanged unless a separate source-backed goal changes it.
- Existing corpse stealing, held-item fallback, auto-loot, follower gold adjustment, item transfer, and save behavior
  continue to pass.
- MM9-specific content adds no meaningful cost when MM9 is not mounted.
- `cmake --build build --target openyamm -j25` succeeds.
- Focused unit tests and representative headless MM9 plus MM6-MM8 scenarios pass in the same build.

## Completion Standard

This goal is complete only when:

- every imported MM9 monster, NPC, scripted actor, and supported dynamic source actor resolves the correct canonical
  source death-loot profile;
- every positive-level `GiveTreasure` actor produces native gold independently of its item result;
- level-zero actors produce no normal procedural payload unless a separately recovered fixed/scripted path requires
  one;
- MM9 item count, category, tier, and remaining reachable post-selection behavior are implemented or a specific
  unsupported source binding prevents completion visibly;
- fixed/scripted items do not suppress ordinary MM9 loot unless native evidence requires that exact case;
- materialized payloads never reroll across interaction or save/load;
- no MM9 NPC borrows loot from a temporary MM6-MM8 visual replacement;
- generated audits account for all source profiles, all actor bindings, all `GiveTreasure` values, and all procedural
  distribution candidates;
- full MM9 regeneration is deterministic and contains no invented `25%L...` actor-loot definitions; and
- affected MM6, MM7, MM8, save/load, startup, and map-loading paths pass their regression gates.
