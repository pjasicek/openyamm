# MAW Mod for MMMerge Analysis

This document summarizes the local reference at `reference/Maw-Mod-MMMerge` and outlines how MAW-like functionality
could be implemented in OpenYAMM. The reference should be treated as behavioral and structural evidence only. Do not
copy MAW Lua code or native DLL implementation into OpenYAMM.

## Reference Scope

The inspected checkout is:

- Repository: `https://github.com/Malekitsu/Maw-Mod-MMMerge.git`
- Branch: `main`
- Commit: `b6c20c4a`
- Local path: `reference/Maw-Mod-MMMerge`

The mod's README describes an install order of MM8, MMMerge, Rodril nightly patch, MMerge multiplayer, and then MAW.
That is important: MAW is an overlay on top of MMerge and its multiplayer branch, not a standalone replacement for
MMerge.

## High-Level Purpose

MAW is a total gameplay overhaul for MMMerge. It keeps the merged MM6/MM7/MM8 content model, but changes the
player-facing rules heavily:

- Item generation, loot tiers, item tooltips, crafting, and shop behavior.
- Monster scaling, difficulty modes, density, affixes, boss behavior, and anti-save-scumming loot seeding.
- Stats, resistances, crits, recovery, power/vitality display, damage formulas, and healing formulas.
- Skill progression, mastery limits, shared utility skills, and new skills.
- Classes, races, promotions, and class-specific mechanics.
- Spells, buffs, alchemy, potions, projectiles, and cooldown/recovery behavior.
- Solo-play convenience systems, including multibag inventory and permanent quality-of-life features.
- Compatibility glue for MMerge multiplayer so MAW-specific state can be synchronized.

Classic MMerge is primarily a content merge and compatibility platform. MAW uses that platform to define a new ruleset.

## Packaging

MAW ships as a mixture of tables, assets, Lua scripts, guide documents, and native extensions.

### Data Tables

MAW has 17 replacement or additional table files under `Data/Tables`:

- `Character portraits.txt`
- `Class Extra.txt`
- `Class HP SP.txt`
- `Class Skills.txt`
- `Class Skillz.txt`
- `Class Starting Skills.txt`
- `Class Starting Skillz.txt`
- `Class Starting Stats.txt`
- `Complex item pictures.txt`
- `Extra Skillz.txt`
- `House rules.txt`
- `ObjList.txt`
- `Potion settings.txt`
- `Race Skills.txt`
- `Race Skillz.txt`
- `SFT.txt`
- `Spells2.txt`

These tables are not just balance values. Some add structural concepts that classic MMerge does not have in the same
form, such as expanded skill tables and extra classes.

### Asset Archives

MAW adds several archives under `Data`:

- `zMaw.T.lod`
- `zMaw.games.lod`
- `zMaw.icons.lod`
- `zMaw.sprites.lod`
- `zVex.icons.lod`

The `z*` prefix likely relies on load-order precedence. In OpenYAMM terms these are mod-owned presentation assets and
should live in a mounted content package, not in engine core.

### Native Extensions

MAW includes three native DLLs:

- `Skillz.dll`
- `MAW_Fixes.dll`
- `cave_api.dll`

The Lua wrapper `Scripts/Structs/00Skillz.lua` shows that `Skillz.dll` is central. It exposes APIs for:

- Reading and writing extended skill values.
- Reading and writing skill names and descriptions.
- Adding new misc, weapon, armor, and magic skills.
- Looking up and editing mastery tables.
- Cleaning invalid mastery values.
- Initializing character portraits for the extended skill system.

`MAW_Fixes.dll` and `cave_api.dll` are present but were not reverse engineered. Their existence still matters: a direct
MAW port should not assume all behavior is visible in Lua.

### Lua Script Layout

MAW has 89 Lua files under `Scripts`, compared to 81 in the inspected MMerge multiplayer-stable checkout. The overlap is
small and intentional: MAW adds many new scripts and overrides selected MMerge scripts.

Major added or changed areas:

- `Scripts/General/zz_Maw-initialize.lua`: settings, MAW extra settings UI, helper functions, default `MAWSettings.lua`.
- `Scripts/General/zMaw-hooks.lua`: native memory hooks for movement and sprite scaling.
- `Scripts/General/zzMaw-Items.lua`: item generation, loot, item stats, crafting, shops, item tooltips.
- `Scripts/General/zzMaw-Monsters.lua`: monster scaling, levels, difficulty, density, map restrictions, boss/elite
  logic.
- `Scripts/General/zzMaw-Stats.lua`: crits, damage, resistances, derived stats, spell/attack delay logic.
- `Scripts/General/zzMaw-Spells.lua`: spell and buff rework, healing, remote spell data support.
- `Scripts/General/zzMAW-Skills.lua`: skill rework, new skills, mastery progression, shared utility skills.
- `Scripts/General/zzClasses.lua`: class-specific mechanics and new class behavior.
- `Scripts/General/zzAlchemy.lua`: potion and alchemy rewrite.
- `Scripts/General/zzMaw-MultiBag.lua`: extra bag storage implemented in Lua save vars.
- `Scripts/General/zzMaw-Multiplayer.lua`: MAW-specific multiplayer state synchronization.

## How MAW Works

MAW is not implemented through one clean subsystem. It is a dense set of event hooks and patches that intercept many
gameplay surfaces.

### Event-Driven Rule Overrides

Most behavior is implemented through MMExtension events such as:

- `GameInitialized2`
- `BeforeNewGameAutosave`
- `BeforeLoadMap`
- `LoadMap`
- `AfterLoadMap`
- `GenerateItem`
- `ItemGenerated`
- `PickCorpse`
- `BuildItemInformationBox`
- `CalcItemValue`
- `CalcStatBonusByItems`
- `CalcDamageToMonster`
- `CalcDamageToPlayer`
- `GetAttackDelay`
- `PlayerCastSpell`
- `UseMouseItem`
- `CanWearItem`
- `CanOpenChest`
- `ShopItemsGenerated`
- `GetShopItemTreatment`
- `CanShopOperateOnItem`

For OpenYAMM, this implies that equivalent extension points need to exist as explicit engine APIs if MAW-like mods are
meant to be supported cleanly.

### Persistent State Model

MAW stores large amounts of state in `vars` and `mapvars`:

- MAW settings and difficulty mode.
- Loot seeds and monster counters.
- Per-map unique monster levels.
- Buff state and remote buff owners.
- Multibag inventory contents.
- Boss/elite state.
- Map clear/resurrection data.
- Player-specific permanent potion and legendary item state.

In OpenYAMM this maps to explicit save-schema extensions. A mod should be able to declare save namespaces instead of
writing unstructured global variables.

### Items and Loot

MAW's item system is one of the largest pieces. It changes:

- Generated item strength.
- Corpse loot seeding.
- Monster gold and treasure chance.
- Item tier and item level.
- Ancient and primordial item naming/stats.
- Item value calculation.
- Shop rerolls and shop item treatment.
- Crafting materials and upgrade actions.
- Item tooltip details.
- Equipment stat contribution.
- Item requirements and filters.

The code uses deterministic seeds for bosses and monsters so save-scumming does not trivially reroll loot. This is a
good design idea to preserve if implementing a MAW-like mode.

### Monsters and Difficulty

MAW keeps a copy of base monster data and recalculates live map monsters based on its own progression model. It changes:

- Monster level and HP.
- Damage and attack properties.
- Resistances.
- AI type adjustments.
- Treasure and item generation.
- Boss and unique monster scaling.
- Difficulty modes.
- Monster density and resurrection rules.
- Restrictions such as blocking save/teleport in high difficulty when enemies are nearby.

The original MMerge bolster system remains a base mechanism, but MAW uses it as only one input to a much larger scaling
ruleset.

### Stats, Damage, and Resistances

MAW changes the meaning and presentation of character stats:

- Primary stats add regular flat effects and secondary percentage effects.
- Might can apply to ranged damage.
- Intellect/personality affect spell and healing output.
- Accuracy/luck affect crits.
- Speed affects attack and cast speed.
- Resistance handling is deterministic and percentage-like rather than vanilla random immunity-style behavior.
- Power and vitality are derived display stats.

In OpenYAMM this should be represented through formula providers or a rules profile, not hardcoded branches sprinkled
across combat and UI.

### Skills and Classes

MAW expands the skill/class model substantially:

- It uses `Skillz.dll` for extended skill storage and mastery logic.
- It replaces Learning with Ascension.
- It adds skills such as Cover, Mana Shield, Enlightenment, and Retaliation.
- It changes mastery progression and can auto-grant mastery at skill thresholds.
- It makes some utility skills party-shared.
- It adds new class kinds and class behavior, including Seraphim, Death Knight, Shaman, and Elementalist.
- It rewrites class-specific spell school names/descriptions and mechanics dynamically.

For OpenYAMM, the lesson is that the current fixed MM skill enum cannot be the only long-term representation if mods
like MAW are first-class. Skills need canonical ids, table-driven metadata, and save-compatible extension ranges.

### Spells, Buffs, and Alchemy

MAW rewrites many spell and potion mechanics:

- Buff rework with toggleable settings.
- Healing formulas with crit/multiplier support.
- Ascended spells.
- Faster/slower cast recovery based on stats and equipment.
- Spell data carried through multiplayer remote casts.
- Potion buffs with duration, power requirements, and permanent black potion effects.
- Health/mana potion hotkeys.
- Alchemy as a parallel buffing system.

The code demonstrates that spell effects need to be decomposed into data, formula, target selection, and side effects. A
hardcoded spell switch will make this kind of mod expensive.

### Inventory and Solo Play

MAW adds multibag inventory using serialized item copies stored in `vars.mawbags`. It also adds sorting hotkeys and
special handling for solo play. This is an example where OpenYAMM should prefer engine support if the feature is
intended to be robust: inventory pages and bag ownership should be model concepts, not script-level removal/reinsertion
of items.

### Multiplayer Compatibility

MAW does not replace MMerge multiplayer. It patches it.

It includes:

- `Scripts/General/zzMaw-Multiplayer.lua`
- Overrides for selected files under `Scripts/Modules/Multiplayer`

Observed multiplayer-specific behavior:

- MAW modifies the displayed multiplayer version string.
- It registers extra remote events.
- It broadcasts MAW mapvars and buff state.
- It syncs bolster-related state.
- It sends boss data to the host.
- It adjusts multiplayer experience distribution.
- It changes monster ownership behavior.

This confirms that MAW-specific rules need explicit replication if OpenYAMM adds multiplayer. A generic "sync all vars"
model would be fragile; rule systems should declare which state is authoritative and how it replicates.

## Differences From Classic MMerge

Classic MMerge:

- Merges MM6, MM7, and MM8 content into an MM8-based runtime.
- Provides cross-continent quests/travel/content compatibility.
- Preserves much of vanilla gameplay.
- Adds patch systems, data tables, UI additions, and optional multiplayer.
- Uses bolster mostly as a compatibility/scaling mechanism.

MAW:

- Assumes MMerge is already installed.
- Replaces the gameplay ruleset.
- Adds new skill/class capabilities through native extension.
- Changes almost every combat formula.
- Changes item generation and loot economy.
- Adds deterministic loot seeding.
- Adds crafting and item upgrades.
- Adds difficulty and progression modes.
- Adds new UI/tooltips/settings around its systems.
- Adds compatibility glue for MMerge multiplayer.

The main architectural difference is ownership: classic MMerge owns world/content integration, while MAW owns mechanics
and balance.

## OpenYAMM Implementation Options

There are three realistic ways to support MAW-like functionality in OpenYAMM.

### Option 1: Hardcode MAW Into Core

This means adding MAW formulas, items, classes, skills, loot tiers, settings, and UI behavior directly to
engine/gameplay code.

Pros:

- Fastest path to a working MAW-like mode if scope is narrow.
- Easier debugging because everything is C++.
- No mod API design required up front.

Cons:

- Makes OpenYAMM less of an engine and more of one specific overhaul.
- Forces MAW-specific branches into shared gameplay systems.
- Makes vanilla/MMerge behavior harder to preserve.
- Conflicts with the flat base/world/mod architecture.
- Hard to maintain if future mods need similar but different mechanics.

Recommendation: avoid this except for truly generic infrastructure that MAW exposes as a need.

### Option 2: Implement MAW as a Pure Content Mod

This means expressing MAW only through tables/assets/scripts mounted as a mod package, with minimal engine changes.

Pros:

- Best content isolation.
- Keeps OpenYAMM core clean.
- Aligns with the desired engine/world/mod architecture.

Cons:

- Not feasible with the current kind of mechanics unless OpenYAMM already exposes many extension points.
- MAW requires formula overrides, event hooks, dynamic skills, UI tooltip changes, save namespaces, and multiplayer
  replication hooks.
- Pure data cannot represent enough of MAW's behavior without a scripting or rules-plugin layer.

Recommendation: long-term target, but only after the engine supports ruleset extension points.

### Option 3: Build Generic Ruleset Infrastructure, Then Port MAW as a Mod

This means adding reusable engine capabilities that vanilla, MMerge, and MAW can all use. MAW then becomes a mounted mod
that provides tables, assets, formulas, scripts, and settings.

Pros:

- Preserves OpenYAMM as an engine.
- Supports future overhauls without copying MAW-specific branches.
- Lets vanilla/MMerge and MAW coexist as separate rules profiles.
- Encourages testable gameplay systems.
- Enables explicit save migrations and content ownership.

Cons:

- More upfront design work.
- Requires careful API boundaries.
- Some features need engine work before visible MAW behavior can be ported.

Recommendation: best approach.

## Recommended Architecture for OpenYAMM

The right split is:

- Core engine: generic data model, systems, extension points, save support, asset mounting, UI primitives, and
  deterministic runtime hooks.
- MMerge/default content: vanilla/MMerge tables and default rules profile.
- MAW mod package: MAW tables, assets, settings, formulas, classes, skills, loot rules, difficulty profile, and optional
  multiplayer replication declarations.

### Core Features Needed

To support MAW well, OpenYAMM should add or strengthen these generic systems.

#### 1. Rules Profiles

Add a first-class rules profile concept, selected by mounted content/mods:

- `default_mmerge`
- `maw`
- future custom profiles

The profile should provide formula hooks for:

- Damage to monsters.
- Damage to players.
- Attack delay.
- Cast delay.
- Stat contribution.
- Resistance reduction.
- Crit chance and crit multiplier.
- Healing.
- Item value.
- Item generation.
- Monster scaling.
- Experience gain.
- Skill mastery progression.

This can start as C++ interfaces implemented by registered profile objects. Later it can become data/script-driven.

#### 2. Declarative Skills

Move toward skill definitions by id:

- Canonical id.
- Display name.
- Category.
- Mastery availability.
- Descriptions per mastery.
- Learn locations.
- Starting availability.
- Save storage.
- Optional formula tags.

The engine should support mod-defined skill ids in a safe range. MAW's `Skillz.dll` behavior maps naturally to this, but
OpenYAMM should implement it natively rather than emulate the DLL.

#### 3. Declarative Classes and Races

Classes and races should be data-owned:

- Class kind and promotion step.
- HP/SP base and scaling.
- Starting skills.
- Skill mastery table.
- Race modifiers.
- Class-specific passive/active rule hooks.
- Promotion qbit/award requirements.

MAW's new classes and cross-world promotion behavior should be implemented as data plus small rule hooks.

#### 4. Deterministic Loot Generation

Loot generation should be deterministic from explicit seeds:

- Save id.
- Map id/name.
- Monster instance id.
- Monster type id.
- Boss spawn counter.
- Chest id.
- Shop generation epoch.

This supports anti-save-scumming behavior cleanly and makes multiplayer/server validation easier.

#### 5. Item Affix and Upgrade Model

Support item metadata beyond vanilla fields:

- Item level.
- Loot tier.
- Base affixes.
- Special affix.
- Upgrade history.
- Crafting material effects.
- Generated seed.
- Display power/vitality delta.

This should not be encoded only through legacy `Bonus`, `Bonus2`, and `MaxCharges` if OpenYAMM wants robust mods.

#### 6. Save Namespaces for Mods

Mods need structured save state:

- Party-scoped mod data.
- Character-scoped mod data.
- Item-scoped mod data.
- Map-scoped mod data.
- Global mod data.

Each namespace should include versioning and migrations. This avoids MAW's script-global `vars` and `mapvars` pattern
becoming unstructured engine state.

#### 7. Extension Events

OpenYAMM needs explicit gameplay events equivalent to the MMExtension hooks MAW relies on:

- Before/after map load.
- Before/after item generation.
- Before/after corpse loot.
- Before/after shop stock generation.
- Item tooltip build.
- Monster tooltip build.
- Damage calculation stages.
- Healing calculation stages.
- Attack/cast delay calculation.
- Skill read/modify.
- Item use.
- Spell cast.
- Potion use.
- Chest/shop access.
- Save/load migration.

These events should carry typed data and clear ownership. For pure logic, prefer deterministic formula providers over a
general mutable event bus.

#### 8. Mod Settings

Support mod-defined settings:

- Defaults.
- Settings UI metadata.
- Save/global persistence.
- Per-profile overrides.
- Validation.

MAW's `MAWSettings.lua` and extra settings page can become a data-driven settings manifest.

#### 9. Inventory Pages

If multibag is desired, implement it in core gameplay:

- Multiple bags/pages per character.
- Item location includes bag id.
- UI can switch bag id.
- Sorting can operate per bag, per character, or party-wide.
- Save format stores bag id directly.

Do not port MAW's script-level item extraction/reinsertion model.

#### 10. Multiplayer Replication Contracts

If OpenYAMM multiplayer is added, MAW-like rules need replication support:

- Which player/server owns boss state.
- Which entity owns monster scaling.
- How buffs are replicated.
- How deterministic loot seeds are assigned.
- How shared mapvars are validated.
- How experience and quest rewards are distributed.
- How item crafting/upgrades are validated.

For an authoritative OpenYAMM server, these should be server-owned decisions. MAW's MMerge multiplayer compatibility
code is useful as a checklist of state that must synchronize, not as an architecture to copy.

## Suggested Implementation Phases

### Phase 1: Document Behavior and Data Ownership

Create an inventory of MAW mechanics and classify each as:

- Table-only.
- Formula override.
- Event hook.
- Save-state extension.
- UI extension.
- Asset-only.
- Multiplayer-relevant.

This phase should produce a migration matrix before code starts.

### Phase 2: Generic Formula Interfaces

Add C++ formula provider interfaces for the current hardcoded gameplay calculations:

- Damage.
- Healing.
- Attack delay.
- Cast delay.
- Resistances.
- Stat bonuses.
- Experience.
- Item value.
- Item generation.
- Monster scaling.

Default implementation must reproduce existing OpenYAMM/MMerge behavior. Tests should lock this down before adding MAW.

### Phase 3: Data-Driven Skills and Classes

Promote class/race/skill tables into content-owned definitions with extension ranges.

Deliverables:

- Mod-defined skill ids.
- Class/race mastery tables.
- Skill descriptions.
- Starting skills.
- Promotion requirements.
- Save/load support.

This phase replaces the need for a `Skillz.dll` equivalent.

### Phase 4: Item and Loot Extension

Implement:

- Item level.
- Affix slots.
- Loot tier.
- Deterministic generation seed.
- Mod-owned item metadata.
- Item tooltip extension.
- Crafting operation API.
- Shop reroll/regeneration policy.

Then implement a small MAW-like loot slice as proof of concept.

### Phase 5: Monster Scaling and Difficulty Profiles

Implement:

- Difficulty profile data.
- Monster scaling formulas.
- Boss/unique monster override data.
- Map progression metadata.
- Save/teleport restrictions from difficulty rules.
- Monster tooltip extension.

Keep the default MMerge bolster as one rules profile, not the only scaling mechanism.

### Phase 6: Spell, Buff, and Alchemy Extension

Implement:

- Spell effect strategy hooks.
- Buff stacking/priority policy.
- Potion effect definitions.
- Healing target policies.
- Cast delay and mana cost formula hooks.
- Buff tooltip extension.

Start with low-risk potion and healing rules before deeper spell rewrites.

### Phase 7: UI and Settings

Implement:

- Mod settings manifest.
- Extra settings screen integration.
- Tooltip extension points.
- Optional power/vitality display.
- Inventory bag UI if multibag is in scope.

Do this after the gameplay model exists, so UI reflects real data rather than driving hidden script state.

### Phase 8: Multiplayer Compatibility

Only after the single-player rules are deterministic:

- Put all MAW-like authoritative decisions on server.
- Replicate derived state where needed.
- Validate crafting, loot, shops, mapvars, and boss state server-side.
- Treat client-side rules as display/prediction only.

Do not start with MAW multiplayer. It depends on too many gameplay systems.

## What Belongs in Core vs Mod

### Core

These should be generic OpenYAMM capabilities:

- Rules profile registration.
- Formula provider interfaces.
- Declarative skill/class/race metadata.
- Mod-defined save namespaces.
- Deterministic RNG streams for gameplay systems.
- Item metadata extension support.
- Typed gameplay events.
- Mod settings schema.
- Asset/content package mounting.
- Tooltip/UI extension points.
- Multiplayer replication contracts.

### MAW Mod

These should stay content/mod-owned:

- MAW item tiers and affix balance.
- Ancient/primordial naming and stat ranges.
- MAW crafting materials and recipes.
- MAW difficulty names and multipliers.
- MAW class names, descriptions, and class-specific abilities.
- MAW race skill bonuses.
- MAW spell formulas.
- MAW potion recipes and alchemy balance.
- MAW map-specific tweaks.
- MAW-specific boss and monster rules.
- MAW UI assets.

### Avoid

Avoid these approaches:

- Hardcoding `if (maw)` branches throughout gameplay systems.
- Encoding new item behavior only in legacy bonus fields.
- Porting Lua global `vars`/`mapvars` directly into untyped OpenYAMM state.
- Treating multiplayer sync as a generic variable broadcast.
- Recreating `Skillz.dll` behavior as an opaque adapter instead of designing native skill extensibility.

## Practical First Slice

The safest first implementation slice is not "port MAW." It is:

1. Add a rules profile abstraction with default behavior.
2. Move attack delay, damage, resistances, item value, and experience into formula providers.
3. Add deterministic item generation seeds.
4. Add mod-owned item metadata and tooltip extension.
5. Implement one small MAW-like feature set:
   - item level display,
   - deterministic corpse loot seed,
   - power/vitality display,
   - one new difficulty profile,
   - one extended skill.

That slice will reveal whether the architecture supports the rest without committing to all of MAW at once.

## Risk Assessment

### High-Risk Areas

- Skills/classes, because MAW uses native DLL support and extended mastery tables.
- Items/crafting, because item metadata exceeds the vanilla structure.
- Monster scaling, because MAW mutates live map monster data and relies on map-specific persistence.
- Spells/buffs, because effects have many side channels and multiplayer data paths.
- Multiplayer, because MAW assumes MMerge's P2P synchronization model, while OpenYAMM should likely use authoritative
  server semantics if multiplayer is built.

### Medium-Risk Areas

- Settings UI.
- Tooltip extensions.
- Potion/alchemy rework.
- Difficulty profiles.
- Inventory sorting.

### Lower-Risk Areas

- Loading MAW-style data tables into content structures.
- Mounting MAW asset archives.
- Exposing guidebook/reference metadata.
- Adding deterministic RNG utilities.

## Conclusion

MAW is best viewed as a demanding test case for OpenYAMM's future mod architecture. It demonstrates that a serious
overhaul needs more than table replacement: it needs extensible formulas, save namespaces, dynamic skills/classes,
deterministic loot, UI extension points, and eventually multiplayer replication contracts.

The recommended path is to implement generic engine support first, keep default MMerge behavior as the baseline rules
profile, and then port MAW behavior incrementally as a mod package. This avoids turning OpenYAMM core into a
MAW-specific fork while still making MAW-like gameplay technically achievable.
