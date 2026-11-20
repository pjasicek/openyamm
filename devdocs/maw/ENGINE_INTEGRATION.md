# OpenYAMM: where an optional MAW ruleset would plug in

First-pass overview. Corrected on 2026-10-22 against the verified specs listed in [README.md](README.md); where they
differ, the spec documents win.

Read-only survey, 2026-10-22. All paths are relative to `/home/pjasicek/github/OpenYAMM`. Line numbers are from the
working tree at the time of writing.

MAW reference: `/home/pjasicek/github/Maw-Mod-MMMerge`. It has 154 Lua files and 73k lines; the largest are
`zzMaw-Item-Sorter` 5.2k, `zzMaw-Items` 4.6k, `zzMaw-Monsters` 4.5k, `zzMaw-Spells` 3.9k, `zzMAW-Skills` 2.7k,
`MawCore/Damage` 2.0k, `zzMaw-Stats` 1.5k and `zzAlchemy` 1.3k. It also ships about 17 `Data/Tables/*.txt` files (class
skills, starting stats, HP/SP, potion settings, race skills, Spells2, …) and LODs; `zMaw.T.lod` overrides ITEMS,
MONSTERS, SPCITEMS, POTION, POTNOTES, rnditems, mapstats, Placemon and class. **MAW is mostly code that hooks events,
with comparatively few tables.** So in OpenYAMM most of it must be new C++ rules. Swapping tables covers only a minority.

---

## 0. Executive summary

| Concern | Today | How a ruleset would plug in |
|---|---|---|
| New game choice | Two stages: continent → character creation. There is no difficulty, ruleset or bolster choice. | Add the choice to the continent stage, `NewGameScreen::drawContinentSelection` (`game/ui/screens/NewGameScreen.cpp:2025`), and extend `ContinueAction`. |
| Stored in save | Nothing. Even the continent is not stored; it is derived from the map. | Add a new `GameSaveData` field gated by the next `SaveVersion` (94 at the analysis date; 95 is taken now) (`game/maps/SaveGame.cpp:24`, `:3811`). |
| Content layering | The flat engine base plus world packages (`world.yml`). Only **Append** and **Distribution** contributions are implemented; **Override** is parsed but never used. There is no mod or ruleset layer. | Either a new "ruleset" package kind mounted before `engine/` (overlay), or implement `Override` contributions. Tables load once, before the main menu, so a ruleset switch means reloading `GameDataLoader`. |
| Difficulty / bolster | Bolster is a **global settings.ini toggle** (`[features] bolster_monsters`), not stored per save. The bolster formulas are C++; the MMerge Lua formula table is loaded but unused. | Move bolster into the per-save ruleset or options. MAW's two bolster modes and six difficulties replace or extend `resolveGameplayMonsterBolster`. |
| Mechanics | Static free functions in `GameMechanics` (`game/gameplay/GameMechanics.cpp`, 3.8k lines) with good choke points. Many call sites are duplicated across `OutdoorWorldRuntime` and `IndoorWorldRuntime`. | Give the formula choke points a `RulesetMechanics` strategy (interface) and add per-ruleset tables. Avoid scattered `if (maw)`; the MM9 `usesMm9ActorRules` ifs are the anti-pattern already present. |
| Items | `InventoryItem` has **one** standard enchant (id + power) and **one** special enchant, plus rarity Common/Artifact/Relic/Special. It is duplicated in `EquippedItemRuntimeState`. | Add extra enchant slots, item level, tier (Ancient/Primordial) and a crafting seed in both structs, their copy helpers and save read/write. |
| Lua | Event Lua per map, with 12 fixed hook kinds (`EventRuntimeHookKind`) and actor behaviour Lua. There is no MMExtension-style memory or event hooking and no formula hooks. | Lua is fit for content scripts such as NPCs, Nightmare dungeon rules and crafting-item use. Hot formulas belong in C++. |
| UI | Menu screens use an immediate-mode `MenuDesignScreen` with YAML layouts. Gameplay overlays combine YAML layouts with C++ renderers and input controllers. Tooltip **text is built in C++**. | Adding a button or label is cheap (YAML element plus one call). New tooltip lines go in C++ renderers. A new screen is medium work. |
| Settings | `settings_catalog.yml` is the data, `tools/generate_settings_layouts.py` generates the layouts, and `MenuSettingsModel.cpp` maps ids to `GameSettings`. | Per-save ruleset options must **not** go in settings.ini. They need their own in-game page or a read-only display. |

---

## 1. New game flow

### 1.1 Entry and screens

- The main menu opens New Game through `GameApplication::openNewGameScreen` (`game/app/GameApplication.cpp:9747`). It
  first calls `ensureCommonGameDataLoaded()` (`:7171`), so **every data table is already loaded before the player picks
  anything**. That function creates `NewGameScreen` with a `ContinueAction` lambda (`:9768`) that calls
  `startNewSessionFromCharacterCreation(characters, continentId, preserveDebugLoadout, true)`.
- The `NewGameScreen` class is in `game/ui/screens/NewGameScreen.h` and `.cpp` (2441 lines).
  - `enum class FlowStage { ContinentSelection, CharacterCreation }` (`NewGameScreen.h:73`).
  - `SelectedContinent { id, key, name }` (`NewGameScreen.h:79`); the default is Jadam, id 1.
  - `ContinueAction = std::function<void(const std::vector<Character>&, uint32_t continentId, bool godLich)>`
    (`NewGameScreen.h:50`). This signature is the obvious thing to widen into a `NewGameOptions` struct carrying the
    ruleset id, difficulty and bolster mode.
  - Layouts are loaded with `loadDesign("gameplay/continent_selection")` and `loadDesign("gameplay/character_creation")`
    (`NewGameScreen.cpp:561`, `:568`). They resolve to `assets_dev/engine/ui/gameplay/continent_selection.yml` (384 lines)
    and `character_creation.yml` (1422 lines) through `MenuDesignScreen::loadDesign` (`game/ui/MenuDesignScreen.cpp:59`).
- **Continent selection:** `NewGameScreen::drawContinentSelection` (`NewGameScreen.cpp:2025`) is immediate-mode code.
  It loops over the hard-coded keys `{"enroth","antagarich","jadame"}` (`:2032`) and draws each as a `world_card` button
  using `ContinentSelection<Name>Button/Illustration/Name/Game/Start` layout elements. It also draws a Cancel button.
  `selectContinent` (`:1996`) resolves the key through `MergedCharacterSelectionTable` (data:
  `assets_dev/engine/data_tables/character_selection.yml`, with race→class availability and per-continent classes) and
  switches to character creation.
  - The layout elements are `ContinentSelectionRoot/Background/Panel/Seal/Wordmark/Subtitle/Title/HeadRule/FooterRule`,
    three cards with five elements each, `ContinentSelectionStep` (`continent_selection.yml:346`) and
    `ContinentSelectionCancelButton` (`:363`).
  - The approved Obsidian menu design calls this screen "Choose Starting Continent"
    (`level_generation/ui/menu_study_20260928/README.md:46`, `:88`). It shows the cards and nothing else.
- **Character creation:** party slots (`addPartySlot` and `removePartySlot`, so 1–5 members and solo is already
  possible), candidate, class, voice, name, stat point pool and optional skills. `confirmCreation` (`:1892`) validates
  the party and calls `m_continueAction(characters, m_selectedContinent.id, godLichParty)` (`:1982`). The class list
  comes from `rebuildCandidates()` in `initializeCharacterCreationForSelectedContinent` (`:582`). The MAW classes
  (Seraphim, Death Knight, Shaman) would need the ruleset known **before** this point; the continent stage comes first,
  so that ordering works.
- **Session start:** `GameApplication::startNewSessionFromCharacterCreation` (`GameApplication.cpp:10025`).
  - It clears the session, resolves the start destination from `continent_settings.txt` "Death map 1"
    (`resolveContinentStartDestination`, `:9810`) and builds a `PartySeed` (gold 200, food 5).
  - It calls `buildFreshCreatedCharacter` (`:2678`) for each member, then `Party::seed`, loads the map and calls
    `applyCurrentSettingsToActiveRuntime()` (`:7026`). That last call pushes `m_settings.bolsterMonsters` into the world
    runtimes (`:7047`, `:7066`).
  - **The ruleset should be applied here: reload or rebind the tables, set a session ruleset object, then seed the
    party.**

### 1.2 Choices that exist today

- Continent (Enroth, Antagarich or Jadame); party size 1–5; per-character race/class/stats/skills/voice/name.
  `newGameGodLich` and `allowIncompleteCharacterCreation` exist only as debug settings.
- **There is no difficulty, ruleset or bolster choice at new game.** The only "difficulty" values in the code are
  unrelated: arena levels (`game/gameplay/ArenaRuntime.cpp:20`, stored in the named global var
  `"OpenYAMM.Arena.Difficulty"`), map encounter difficulty (`MapStats` `Encounter*Difficulty`, used for tier weights at
  `game/outdoor/OutdoorWorldRuntime.cpp:706`, `:3792` and `game/indoor/IndoorWorldRuntime.cpp:1045`, `:1171`), and
  perception or disarm difficulty.
- Bolster is a global option: Settings → Gameplay → "Difficulty: Monster scaling" (`bolster_monsters`,
  `assets_dev/engine/ui/menu/settings_catalog.yml:23`). It lives in `GameSettings::bolsterMonsters`
  (`game/app/GameSettings.h:231`), defaults to false on desktop and true on Android (`GameSettings.cpp:471`), and is
  stored in settings.ini `[features] bolster_monsters` (`GameSettings.cpp:1468`, `:2244`).

### 1.3 How the choice is stored

- The continent id is **not saved**. The save stores `mapFileName`, and the continent and world come from `map_stats`
  (`MapStatsEntry::worldId`, and `mergedContinentId` in the Load screen at `LoadGameScreen.cpp:769`).
- The active world (`m_activeWorldManifest`, `settings.startWorldId`) is a mount concern. It switches with the map
  (`GameApplication::activateWorldForMap`, `:7287`, which calls `AssetFileSystem::switchActiveWorld` and so re-mounts).
  Data tables are **not** reloaded on a world switch because they are merged globally.

---

## 2. Content layering

### 2.1 Mounting

- `engine/AssetFileSystem.{h,cpp}`. `initialize(basePath, assetRoot, tier, profile, activeWorldId)` mounts:
  - for development: `mountDevelopmentPackageRoots` (`AssetFileSystem.cpp:683`), which mounts `assets_dev/engine`, then
    the active world root, then merged per-world sprites, icons, audio, music, video and map roots;
  - for packaged builds: `mountPackagedAssetRoot` and `mountContentPacks`, where the "active world's pack goes in front,
    then the engine's and the other worlds'" (`AssetFileSystem.h:123`) from `assets/*.zip` plus an `AssetPackIndex`;
  - on Android: `mountAndroidApkAssetRoot`.
- `switchActiveWorld` (`AssetFileSystem.cpp:623`) re-runs `initialize`. This is a precedent for re-mounting with a
  different overlay at runtime.
- There is **no mod concept** in code. The only mentions are `GameSettings.h:84`, which keeps unknown INI keys "for a
  newer version or a mod", and AGENTS.md's intent of "mod manifests, declared id ranges".

### 2.2 World manifests and contributions (the only package mechanism)

- `game/content/ContentManifest.{h,cpp}`: `WorldManifest` (`ContentManifest.h:68`) has `id`, `name`, `sourceGame`,
  `start`, `qbits` range, `partyMovement`, `actorAwareness`, `contentSchemaVersion`, `dependencies`, `idRanges` (per
  domain) and `tableContributions`.
- `TableContributionMode { Append, Override, Distribution }` (`ContentManifest.h:44`) is parsed at
  `ContentManifest.cpp:84`. **Override is never handled anywhere.** Item contributions reject non-Append modes
  (`game/data/GameDataLoader.cpp:4179`). Distribution is used only for the MM9 trainers, routes, transitions and
  schedules (`GameDataLoader.cpp:2894`–`3073`).
- `game/content/ContentTableComposer.{h,cpp}`: `composeItemTableRows` and `composeKeyedAppendTableRows` append rows
  inside declared id ranges and reject collisions.
- Only `assets_dev/worlds/mm9/world.yml` uses this. It declares id ranges (items 10000–10999, objects 20000+, monsters
  9000–9999, vendors 30000+) and contributions for items, item_effects, item_sets, monster_data, vendors and so on.
- `loadMountedWorldManifests` (`GameDataLoader.cpp:139`) enumerates `worlds/*/world.yml`. The loaded package schemas
  feed `requiredContentPackages` in saves (§6).

### 2.3 How tables load

- `GameDataLoader::loadInternal` (`game/data/GameDataLoader.cpp:1570`) loads, in order:
  - `loadMapStats`, `loadMonsterTable` (`engine/data_tables/monster_data.txt` and `monster_descriptors.txt`, plus world
    append contributions, `:2434`), `loadMonsterProjectileTable`, `loadObjectTable` and `loadSpellTable` (`spells.txt`);
  - `loadItemTable` (`items.txt` and `random_items.txt` plus contributions, `:4141`), `loadItemEnchantTables`
    (`standard_item_enchants.txt`, `special_item_enchants.txt`), `loadChestTable`, `loadHouseTable` and `loadAwardTable`;
  - `loadJournalTables`, `loadClassMultiplierTable` (`class_multipliers.txt`), `loadClassSkillTable` (`class_skills.txt`,
    `class_starting_skills.txt`, `class_extra.txt`) and `loadCharacterInspectTable` (`english/stats.txt` and the skill and
    class texts, `:3344`);
  - `loadRaceStartingStatsTable`, `loadReadableScrollTable`, `loadPotionMixingTable` (`english/potion.txt`, `:3481`),
    `loadPotionNoteTable`, …, `loadRosterTable` and `loadCharacterDollTable`;
  - `loadMergedBaseTables` (the MMerge tables: continent/potion/reagent settings, bolster maps/monsters/formulas, class
    starting stats, house rules, town portal and so on; `:3700`–`3800`; classes in `game/tables/MergedBaseTables.h`).
- Every path is fixed and engine-scoped: `engineDataTablePath(name)` returns `"engine/data_tables/" + name`
  (`GameDataLoader.cpp:690`).
- Loading happens **once per process**, guarded by `m_commonGameDataLoaded` (`GameApplication.cpp:7171`–`7220`). It is
  deferred until after the first main-menu frame (`updateDeferredStartupLoads`, `:7222`). The results are bound into
  `GameDataRepository::bind` (`game/data/GameDataRepository.h:49`) and `GameSession::bindDataRepository`
  (`game/app/GameSession.cpp:196`), which also sets the **global** `GameMechanics::bindClassMultiplierTable`. World
  runtimes take table pointers when they are initialised, per map load.
- **Can a table be swapped per ruleset?** Not today, but it is feasible:
  - (a) Mount a ruleset overlay root at the `engine/` mount point in front of the base, so
    `engine/data_tables/items.txt` resolves to the MAW copy. Then `GameDataLoader::loadInternal` runs again and
    `GameDataRepository`, `GameSession` and the global class-multiplier table are rebound. This must happen at new game
    and at load, before the map loads; `startNewSessionFromCharacterCreation` and `quickLoadFromPath` already clear the
    session and shut down the renderer first.
  - (b) Or implement `TableContributionMode::Override` per table: replace keyed rows and declare a `ruleset.yml`
    manifest, mirroring `world.yml`.
  - Option (a) is simpler for MAW's wholesale table replacements: items, monsters, spcitems, potion, class skills and
    HP/SP. Option (b) is cleaner for small edits.
  - The hidden costs: the main-menu Load list and the New Game screen read the already-loaded tables
    (`mergedCharacterSelectionTable`, continents). The Load screen fully decodes every save (`LoadGameScreen.cpp:294`,
    `:725`) but does not need item tables to list them.

### 2.4 Existing notions of difficulty, mode, ruleset and bolster

- `grep -i "ruleset|gameMode|game_mode"` finds **nothing**. "difficulty" appears only as listed in §1.2.
- Bolster:
  - `game/gameplay/GameplayBolsterRuntime.{h,cpp}` (847 lines). The entry point is `resolveGameplayMonsterBolster`
    (`.cpp:702`). It takes a `GameplayBolsterRuntimeContext { pMap, pMonsterTable, pBolsterMapTable,
    pBolsterMonsterTable, pParty, bolsterMonstersEnabled }` and returns HP, AC, move speed, damage dice, spell
    skill/mastery, generated attacks/spells/summons and `rewardMultiplier`.
  - Map kinds come from `bolster_maps.txt` (`LowerToEqual`, `AllToEqual`, `OriginalStats`, `NoBolster`); monster styles
    come from `bolster_monsters.txt` (Wimpy, Speed, Strength, Magic and so on).
  - **The formulas are hard-coded C++**, with easing constants at `.cpp:5`–`10` and a 5000 HP cap. MMerge's Lua
    formula table `bolster_formulas.txt` is loaded into `MergedBolsterFormulaTable` (`MergedBaseTables.h:551`) but
    nothing reads `getMergedBolsterFormulaTable()`, so it is dead data.
  - MMerge's `BolsterAmount` 0–200 % ("BolsterMul") has no equivalent.
  - Call sites (each builds the context itself):
    - `OutdoorWorldRuntime.cpp:2897`, `:3910`, `:15143`, and contexts at `:5061`, `:15990`, `:18649`, `:18735`;
    - `IndoorWorldRuntime.cpp:9552`, `:11811`, `:11994`, `:13345`.
  - Results are cached per actor in saves (`SaveVersionOutdoorActorBolsterCache` 49, `MonsterBolsterRewards` 59,
    `MonsterBolsterDamageDice` 60). That matters: changing difficulty mid-game must invalidate those caches.
- The one existing rules-tuning struct is `CharacterAttackTuning { blasterSkillScaling, blasterMinimumRecoveryTicks }`
  (`game/gameplay/CharacterAttackTuning.h`). It is built from settings by `characterAttackTuningFromSettings`
  (`GameSettings.cpp:676`) and passed into `GameMechanics::buildCharacterAttackProfile` and related functions. It is a
  precedent, and a seed, for a ruleset parameter object, although it is settings-driven rather than per save.
- World-specific rules precedent: MM9 actors use `usesMm9ActorRules` ifs scattered through `OutdoorWorldRuntime.cpp`
  (`:2801`, `:10839`, `:15194`, `:16205`, …) and `game/mm9/Mm9PrimaryStats.*`. **That scattered-if pattern is the one to
  avoid for MAW.**

---

## 3. Mechanics code

`GameMechanics` (`game/gameplay/GameMechanics.h`, `.cpp` 3823 lines) is a class of static functions plus anonymous
helpers. Nearly every combat and character formula passes through it, which makes it the natural seam for a
`RulesetMechanics` interface. Below, each topic is rated as table, hard-coded or mixed.

### 3.1 Primary stats

- `ParameterBonusThresholds` and `ParameterBonusValues` (`GameMechanics.cpp:38`–`48`) and `parameterBonus()` (`:265`)
  form the vanilla 0..500 → −6..+30 step table. It is **hard-coded**. MAW's "1 effect per 5 points" plus per-stat extras
  needs a strategy function, or at least a ruleset table.
- Primary stat layers come from `resolveCharacterPrimaryStatBaseValue/PermanentBonusValue/MagicalBonusValue/
  EquippedItemBonusValue` (`:1352`–`1508`).
- The character sheet is `GameMechanics::buildCharacterSheetSummary` (`:2185`): AC, attack, damage ranges, resistances
  and immunities. This is the **single choke point for the stats screen**. MAW's Power and Vitality would be derived
  values computed here or in a sibling function.

### 3.2 HP, SP and level

- `calculateBaseCharacterMaxHealth` (`:1965`) and `calculateBaseCharacterMaxSpellPoints` (`:1986`) are table-driven
  through `class_multipliers.txt` (`BaseHP`, `HPPerLevel`, `BaseMana`, `ManaPerLevel`, `ManaStat`), plus
  `parameterBonus(endurance)` and the Bodybuilding/Meditation `resourceSkillBonus` (`:400`). There is a fallback
  formula when the class is missing.
- Experience: `experienceRequiredForNextLevel` = 1000·L·(L+1)/2, hard-coded at `game/party/Party.cpp:1179` and
  **duplicated** at `game/gameplay/HouseInteraction.cpp:802`. Learning % is computed at `Party.cpp:1186`.
  `Party::grantSharedExperience` (`Party.cpp:3183`) splits experience among eligible members; MAW's solo ×5 belongs
  here.
- Kill rewards are granted in five duplicated places: `OutdoorWorldRuntime.cpp:12706`, `:15246`, `:16253` and
  `IndoorWorldRuntime.cpp:12087`, `:14314`, all through `gameplayBolsterExperienceReward`.

### 3.3 Party attacks, damage, crits and recovery

- `buildCharacterAttackProfile` (`:2427`) and `resolveCharacterAttackAgainstArmorClass` (`:2611`) decide hit or miss and
  roll damage. Skill bonuses come from `resolveMeleeAttackSkillBonus`, `resolveMeleeDamageSkillBonus`,
  `resolveRangedAttackSkillBonus`, `resolveRangedDamageSkillBonus` and `resolveArmorSkillBonus` (`:933`–`1160`), all
  **hard-coded per skill and mastery** as vanilla.
- Item contributions come from `resolveMeleeAttackItemBonus` and its siblings (`:1178`–`1294`) and from
  `resolveEquippedItemStatBonuses` (`:1294`).
- Crits: vanilla has none except the dagger triple-damage proc in `applyMeleeWeaponEffects` (`:1884`, which sets
  `result.criticalDamage` at `:1938`). MAW's crit chance and crit damage are entirely new.
- Recovery: `resolveAttackRecoverySeconds` (`:1609`), `baseRecoveryTicksForSkillName` (`:437`),
  `armorRecoveryMultiplier` (`:492`) and the constants `OeMinimumMeleeRecoveryTicks=30` and
  `OeMinimumRangedRecoveryTicks=5` (`:28`). These match MMerge `Attack.MinimalMeleeAttackDelay` and its ranged
  counterpart. MAW's multiplicative recovery and weapon attack speed are a strategy change here.
- Dual-wield logic is in the same functions. Spell damage is separate (§3.7).
- Hit tests: `characterAttackHitsArmorClass` (`:1793`), `characterRangedAttackHitsArmorClass` (`:2906`) and
  `monsterAttackHitsArmorClass` (`:2926`).

### 3.4 Resistances and incoming damage

- To the party, `resolveCharacterIncomingDamage` (`:3074`) uses the vanilla random halving: up to four rolls against
  `30/(res+luckBonus+30)`. It applies Plate (Master) and Chain (GM) physical reductions, and Spirit/Light/Dark use direct
  resistances. **It receives no attacker level.** MAW's percent formula, `damage / 2^(res/100)` scaled by monster level,
  needs a signature change.
- Callers: `game/gameplay/GameplayCombatController.cpp:513` and traps in `ChestRuntime.cpp:920`.
- To monsters, `resolveMonsterIncomingDamage` (`:3168`) makes resistance ≥200 an immunity and otherwise uses the same
  random halving with the Hour of Power bonus. `resolveMonsterIncomingWeaponDamage` (`:3204`) splits a hit into
  elemental components.
- Callers of the monster path are duplicated in the world runtimes: `OutdoorWorldRuntime.cpp:6600`, `:7268`, `:13563`,
  `:13653`, `:15209`, `:15810`, `:16637` and `IndoorWorldRuntime.cpp:6997`, `:7213`, plus
  `GameplayActionController.cpp:706`. They all call the static function, though, so swapping the implementation behind
  it covers them all.

### 3.5 Monsters

- Base stats come from `monster_data.txt` (`MonsterTable`; table-driven, and MAW's MONSTERS.txt maps to it).
- Spawning, bolster and caching are in the world runtimes. Encounter counts and tier weights are hard-coded tables
  (`OutdoorWorldRuntime.cpp:706`, `IndoorWorldRuntime.cpp:1045`), which matters for MAW's monster density per
  difficulty.
- Attack damage rolls go through `GameplayActorAiSystem.cpp:468` → `GameMechanics::rollMonsterAttackDamage` (`:2940`)
  with the bolstered dice.
- Monster speed comes from the table plus bolster `moveSpeed`.
- There are no homing projectiles: `grep homing` finds nothing in `game/`. MAW homing would be new code in
  `GameplayProjectileService`.
- Per-actor Lua behaviours (§4.2) could provide MAW's Nightmare elite abilities.

### 3.6 Item generation, enchants and price

- `ItemGenerator::generateRandomInventoryItem` (`game/items/ItemGenerator.cpp:156`–`308`) works in this order: a 5 %
  rare/artifact roll, a base item by treasure level (weights from `random_items.txt`, filtered by world), wand charges
  and potion power, then **either one standard enchant or one special enchant**.
- Enchant chances are hard-coded: `StandardEnchantChanceByTreasureLevel` and the
  `SpecialEnchantChanceFor{Equipment,Weapons}ByTreasureLevel` arrays (`ItemEnchantRuntime.cpp:18`–`20`).
  `generateStandardEnchantPower`, `isSpecialRarityAllowed` (`:1544`) and the treasure level clamp of 1..6 are also
  hard-coded. Enchant definitions are table-driven (`standard_item_enchants.txt`, `special_item_enchants.txt`).
- Equipped effects: `ItemEnchantRuntime::applyEquippedEnchantEffects` (`:1789`) and `GameMechanics`'
  `resolveEquippedItemStatBonuses`.
- Display: `ItemEnchantRuntime::displayName`, `buildEnchantDescription`, `itemValue` (`:1744`) and `itemInspectValue`.
- `game/items/PriceCalculator.{h,cpp}` holds the buy, sell, identify, repair, skill, training, temple, tavern and
  transport prices with merchant discount. It is hard-coded vanilla. MAW's "gold cost depends on loot power" belongs
  in `itemValue`.
- **Item struct:** `InventoryItem` (`game/party/Party.h:45`) has `objectDescriptionId`, quantity, w/h, grid xy, the
  identified/broken/stolen/hardened flags, `standardEnchantId` (u16), `standardEnchantPower` (u16), `specialEnchantId`
  (u16), `artifactId`, `ItemRarity rarity` (`Common/Artifact/Relic/Special`, `game/tables/ItemTable.h:26`), charges
  and `temporaryBonusRemainingSeconds`.
  - It is mirrored by `EquippedItemRuntimeState` (`game/party/CharacterState.h:128`), one per equipment slot, with the
    copy helpers `makeInventoryItem(…, runtimeState)` (`Party.cpp:1538`) and `copyItemToEquippedRuntimeState`
    (`Party.cpp:1670`).
  - `InventoryItem` is the universal item instance, also used in world items
    (`OutdoorWorldRuntime.h:459`), chests and corpses (`GameplayRuntimeInterfaces.h:73`, `:106`, `:441`), house stock
    (`Party.h:324`) and the held cursor item.
  - **There is no free room** for extra enchants, item level, tier or a crafting seed. Adding them means extending both
    structs and the two copy helpers, the save read/write (§6, `SaveGame.cpp:535`, `:729`) and every place that
    displays or compares enchants (`standardEnchantPower` appears in about 19 files; `Party.cpp` 11,
    `InventoryItemMixingRuntime` 6, `ItemGenerator` 5, `AlchemyBenchRuntime` 5, `IndoorWorldRuntime` 5, …).
  - A cleaner design keeps the current fields as enchant slot 0 and adds a small `std::vector` or fixed array of
    `ItemAffix { id, power }` plus `uint16_t itemLevel` and `uint8_t tier`.
- `ItemDefinition` (`ItemTable.h:74`) already has extensible columns (`content_flags`, `normalizedTier`, `effectProfile`,
  `balanceProfile`, `requiredMight/Accuracy`, `allowedClassRoots`, `ItemContentEffect`, set bonuses through MM9's
  `item_sets`). MAW's crafting items (gems, cube, hourglass, eye, mirror) fit as new rows with a `useAction`.

### 3.7 Skills, masteries, spells, classes, races and promotions

- **Skills are a hard-coded list:** `CanonicalSkillNames` is a `std::array<std::string, 40>` (`game/party/SkillData.cpp`
  ~`:102`–`143`) with aliases. "Learning" is a fixed member. MAW's **Ascension** replacing Learning means code changes
  here plus `Party.cpp:1186` (learning percent).
  - The skill raise cost is `skillPoints -= newSkillLevel` (`Party.cpp:3873`); MAW's halved cost for a second school
    changes this.
  - Mastery thresholds are hard-coded (`game/gameplay/MasteryTeacherDialog.cpp:342`–`421`: 4, 7, 10 plus stat
    requirements). MAW's horizontal mode needs 6, 12 and 20.
  - Class caps are table-driven (`class_skills.txt` → `ClassSkillTable`, including `getHighestPromotionCap` at
    `ClassSkillTable.cpp:412`). Race overrides come from `race_skills.yml`. Starting stats come from
    `class_starting_stats.txt`.
- **Classes** are table-driven by *name* (`class_multipliers.txt`, `class_skills.txt` columns, `class_extra.txt` kind
  and step, `character_selection.yml`). However:
  - promotions are partly hard-coded in `promotionClassNames` (`SkillData.cpp:479`) and `mm8ClassIdForClassName`
    (`:606`);
  - there are about 32 `className == "…"` checks, for example monster target preference at `Party.cpp:1062`–`1130`;
  - `startingCasterClassId` hard-codes ids 4/5 and 42/44 (`NewGameScreen.cpp:305`).
  - New MAW classes are therefore table rows plus a handful of code touches: promotion graph, portraits and dolls,
    class descriptions in `english/class` text.
  - Lua already has `GetClassId`, `GetPlayerClass`, `SetPlayerClass`, `GetClassSkillCap` and related functions for
    promotion events.
- **Spells:**
  - Costs, recovery, base damage and dice come from `spells.txt` (`SpellTable`). Effects are hard-coded in
    `game/party/PartySpellSystem.cpp` (3018 lines, about 191 `case SpellId::` labels). It has a C++ `BackendSpellRule`
    table (`:371`) with mana, recovery, damage and multi-projectile values per spell, `rollSpellDamage` (`:1036`) and
    buff power and duration switches (`:1164`).
  - `game/gameplay/GameplaySpellService.cpp` (903 lines) handles casting flow and targeting only.
  - MAW's spell rework (new heals, ascension tiers, crit, item damage bonus applied to spells) is therefore mostly C++.
    Numeric changes could become table-driven by moving `BackendSpellRule` numbers into a ruleset `spells.txt`.
- **Potions/alchemy:** recipes are table-driven (`english/potion.txt` → `PotionMixingTable`, plus `potion_notes`,
  `potion_settings.txt` and `reagent_settings.txt`). Potion **effects** are hard-coded switches by item id in
  `game/items/InventoryItemUseRuntime.cpp` (`boostPotionBuff` `:234`, `applyExtraPotionEffect` `:286`, about 119 cases).
  MAW's charges, 6-hour buffs and power requirements are code changes there.

### 3.8 The alchemy bench today

- It is an **OpenYAMM-original QoL modal panel**, not an MM mechanic. It is opened by `CharacterAlchemyButton` on the
  character screen (`GameplayPartyOverlayInputController.cpp:2101`) and covers the pages above the party bar
  (`assets_dev/engine/ui/gameplay/alchemy_bench.yml`, a "Carved Obsidian" full-width study from 2026-10-13).
- Its parts:
  - a **recipe book** of known recipes with Brewable/All filters and search (`AlchemyBenchRecipeList`, `…Search`);
  - a **mix row** of target + held = result slots, with the alchemist's name, preview power and outcome
    (Unknown, Known, TooDifficult, KnownExplosive, MissingIngredient);
  - **Mix**, **Mix All**, **Clear** and **Close** buttons;
  - an **ingredient grid** of party-wide bottles, reagents and potions, aggregated with best power, with filters.
- Logic lives in `game/items/AlchemyBenchRuntime.{h,cpp}` (1038 lines): `AlchemyBook`, `AlchemistInfo`, `AlchemyPreview`
  and `AlchemyChainPlan`, which auto-brews missing intermediate potions from known recipes, plus party-wide strongest
  ingredient lookup. Underneath it uses the vanilla drop-onto mixing in `InventoryItemMixingRuntime`.
- The view model is `game/ui/GameplayAlchemyBenchView.cpp`, the renderer `game/ui/GameplayAlchemyBenchRenderer.cpp` and
  the input `game/gameplay/GameplayAlchemyBenchInputController.cpp`. The party remembers explosive pairs
  (`Party::Snapshot::explosiveMixes`).
- For MAW the bench keeps working if the recipe tables are swapped. MAW's recipe list would show up automatically. Its
  "power requirement" is an extra preview outcome.

### 3.9 Summary of how each MAW area would plug in

| MAW area | Plug-in kind |
|---|---|
| Item tables (ITEMS, SPCITEMS, rnditems), monsters, class skills, starting stats, HP/SP, potion recipes, race skills, stat/skill/class texts | **Table swap** (overlay) |
| 3 enchants, ancient/primordial, item level, crafting items | **Data model + generator strategy** (`InventoryItem`, `ItemGenerator`, `ItemEnchantRuntime`, save) |
| Stat effects, crits, % resistances, recovery and attack speed, dual-wield, armour magic resist | **Strategy object** behind `GameMechanics` statics |
| Monster ×2 HP, damage scaling, difficulties, Free/Horizontal bolster | **Strategy** in `GameplayBolsterRuntime` + ruleset params; spawn density in world runtimes |
| Skills: Ascension, shared misc skills, continuous regen/meditation, mastery thresholds, skill reset | Hard-coded list changes + strategy |
| Spells rebalance | `BackendSpellRule` numbers to a table + strategy for new effects |
| Alchemy charges and durations | `InventoryItemUseRuntime` strategy |
| Homing projectiles | New code in `GameplayProjectileService` (ruleset flag) |
| Sorting hotkeys, shop reroll, potion quick-use (G/V) | UI/input (§5); inventory sort already exists (`CharacterInventorySortButton`) |
| Nightmare: no save near monsters, dungeon resurrect, elites | Session rules + Lua map hooks + actor behaviours |

---

## 4. Scripting

### 4.1 Event Lua

- `engine/scripting/LuaStateOwner.{h,cpp}` wraps a `lua_State` with `openApprovedLibraries()` (a sandbox), `runChunk`,
  `call` and registry refs.
- `game/events/EventRuntime.{h,cpp}` (10k lines) owns a per-map `LuaSessionCache` (`EventRuntime.cpp:4663`, rebuilt
  around `:8746`–`8800`) with a `globalScope` (`assets_dev/engine/events/Global*.lua`) and a `localScope` (map events).
  Generated files must not be hand-edited; see AGENTS.md.
- The bindings are registered in `registerEventBindings` (`:8374`). The table holds roughly 150 `evt.*` functions:
  - quest bits, variables and global vars;
  - items (`GiveItem`, `SummonItem`, `PartyMemberHasItem`, …), classes (`SetPlayerClass`, `GetClassSkillCap`, …), NPC,
    house and map control, sounds, effects and weather;
  - `CastSpell`, `SummonMonsters`, `DamagePlayer`, `ApplyPartyPrimaryStatBuff`, …
- **Hooks:** `EventRuntimeHookKind` (`game/events/EventRuntime.h:68`) has a fixed set of 12: `NpcEnter`, `NpcExit`,
  `HouseTopicFilter`, `HouseTopicClick`, `RestFoodCost`, `GameplayAction`, `MapRefill`, `MapTransition`,
  `MonsterKilled`, `MonsterDamage`, `ChestOpen` and `InventoryOpen`.
  - Lua registers them with helpers in `assets_dev/engine/scripts/common/event_support.lua` (`RegisterMonsterDamageHook`
    and `RegisterGlobalMonsterDamageHook` at `:1186`; `RegisterRestFoodCostHook`, …). It handles them through
    `GetHookContext`, `SetHookBlocked`, `SetHookDamage`, `SetHookRestFoodCost` and `SetHookHouseTopics`
    (`EventRuntime.cpp:5838`–`5941`).
  - C++ fires them, for example `IndoorWorldRuntime.cpp:11160` (MonsterDamage), `OutdoorSceneRuntime.cpp:731`
    (MonsterKilled), `HouseInteraction.cpp:1542`, `GameplayDialogController.cpp:1290` and
    `GameplayScreenController.cpp:154`.
- **Is MMExtension-style hooking supported? No.**
  - There is no memory, struct or offset access and no `events.CalcDamageToMonster`, `CalcStatBonusByItems`,
    `GetAttackDelay`, `ItemGenerated`, `CalcSpellDamage` and so on. Damage to the party, item generation, stats, the UI
    and save data have no hooks.
  - The Lua state exists only while a map runtime is loaded, so there is no session-wide script state for rules.
  - The supported model is event scripts plus the fixed hooks above, and per-actor behaviours.

### 4.2 Actor behaviours

- `devdocs/ACTOR_SCRIPTING_INVESTIGATION.md` covers this: per-monster Lua behaviour scripts on top of the shared AI,
  with the boss mage, monster 307, as the demo.
- The runtime is `game/gameplay/ActorBehaviorRuntime.cpp` (1941 lines). The library is
  `assets_dev/engine/behaviors/behavior.lua` (`Behavior.define`, cooldowns, …), the registry
  `engine/behaviors/behaviors.yml`, and worlds attach behaviours in `worlds/<id>/behaviors.yml`. Behaviour state is saved
  (`SaveVersionActorBehaviors` 86).
- This is a good fit for MAW's Nightmare elite monsters with unique abilities.

### 4.3 Could ruleset logic be partly Lua?

- **Content-level rules:** yes.
  - Nightmare "monsters resurrect if you leave early" uses `MapTransition`, `MonsterKilled` and map vars.
  - Crafting-item use needs a new hook kind or `useAction`.
  - Shop reroll uses `HouseTopicClick`.
  - Kill bonuses (exp, gold, crafting drop) use `MonsterKilled`.
  - Starting-teleporter NPCs are events.
- **Formula-level rules:** not without a new design, and not advisable for per-hit math. That covers damage, stats,
  resistances, crit, recovery, item generation and the stats screen. It would need a session-lifetime Lua state, a
  stable rules API and per-call marshalling.
- If wanted, a narrow "ruleset Lua" could own coarse parameters loaded once, such as difficulty multiplier tables.
  Hot paths stay in C++ strategy code.

---

## 5. UI system

### 5.1 Two families

1. **Menu screens** (`IScreen` → `MenuScreenBase` → `MenuDesignScreen`, `game/ui/MenuDesignScreen.cpp`). They are
   immediate mode: `loadDesign("<path>")` loads `ui/<path>.yml`, then `beginDesign`, `drawDesign`,
   `button(id, rect, label, skin, enabled, hover)`, `label(id, text)`, `action(id)` and `designRect(id)`.
   - Screens: `game/ui/screens/{MainMenu,NewGame,LoadGame,LoadingOverlay,WinGame,Arcomage,CutsceneVideo}Screen`.
   - The YAML files are layout only (anchors, offsets, sizes, z, assets, label text, fonts).
   - **Adding a ruleset selector to continent selection** means a few elements in `continent_selection.yml` (button
     group or toggle cards, plus a description label) and about 20 lines in `drawContinentSelection`. That is cheap.
2. **Gameplay overlays**: inventory/character, item inspect, spellbook, journal, rest, alchemy bench, dialogue, shops.
   - Layouts are listed in `GameplayLayoutFiles` (`game/ui/GameplayUiController.cpp:12`–`41`), for example
     `ui/gameplay/item_inspect.yml`, `character.yml`, `character_detail.yml` and `character_inspect.yml`.
   - State lives in `GameplayUiController`; rendering in `GameplayPartyOverlayRenderer.cpp` (11k lines) and
     `GameplayHudOverlayRenderer.cpp`; input in `Gameplay*InputController.cpp`; composition in
     `GameplayUiOverlayOrchestrator.cpp`.
   - **Tooltip and stats text is assembled in C++:**
     - `GameplayPartyOverlayRenderer::renderItemInspectOverlay` (`:5944`) builds the "Attack: +N   Damage: …" and
       "Armor: +N" lines (`:2583`–`2636`), the enchant text through `ItemEnchantRuntime::buildEnchantDescription`
       (`:5998`) and "Value:" (`:6593`).
     - `renderCharacterOverlay` (`:8264`) draws the stats page from `CharacterSheetSummary`.
     - Right-click stat, skill and class descriptions are table text (`english/stats.txt` and related, through
       `CharacterInspectTable`), so they can be swapped per ruleset.
   - Adding MAW item lines (item level, three enchants, tier, power/vitality delta) means C++ in those functions,
     ideally fed by a ruleset "describe item" function. A new gameplay overlay means state + renderer + input
     controller + YAML + orchestrator wiring: medium work, with the alchemy bench as the template.

### 5.2 Hotkeys

- `game/app/KeyboardBindings.{h,cpp}`: `enum class KeyboardAction` (`KeyboardBindings.h:26`, 29 actions, `Count`), the
  `KeyboardBindingDefinition` table (`KeyboardBindings.cpp`, for example `DoubleSpeed` at `:76`: ini key, label, page,
  default), and one binding per action.
- The Settings rows come from the `bindings:` list in `settings_catalog.yml` (`:459`). Handlers read
  `inputFrame.action(KeyboardAction::X).pressed` (for example `GameApplication.cpp:9034`).
- Adding the MAW hotkeys (sort R/T/E, potion G/V, shop reroll R) means an enum value, a definition row, a catalog row
  and a handler. That is straightforward.

### 5.3 Settings screen (approved Obsidian menus)

- `assets_dev/engine/ui/menu/settings_catalog.yml` holds the sections (gameplay, interface, video, audio, controls,
  keyboard, updates) and setting rows (`id`, section, group, name, `type: toggle|select|steps|action`, options, desc,
  depends, desktop_only, updater_only) plus the bindings.
- `python3 tools/generate_settings_layouts.py` regenerates `ui/gameplay/settings_<section>.yml`.
- `MainMenuScreen::drawSettings` (`game/ui/screens/MainMenuScreen.cpp:825`) renders them and reads the catalog at `:80`.
- `game/ui/MenuSettingsModel.cpp` `menuSettingValue` and `setMenuSettingValue` map ids to `GameSettings` fields (for
  example `bolster_monsters` at `:51`, `:314`).
- `GameSettings` (`game/app/GameSettings.h`) is parsed from and written to settings.ini (`GameSettings.cpp` ~`1460`,
  `~2240`).
- **Settings are global, per installation.** MAW's per-campaign options (difficulty, bolster mode, homing on/off) should
  live in the save (§6). If they are shown in Settings, show them read-only or as a "Current game" group that writes to
  the session rather than the INI. The same Settings screen is used from Pause.

---

## 6. Save format

- `game/maps/SaveGame.{h,cpp}` (4526 lines). It is a custom binary stream: magic `OYSAVE1` and `uint32 version`
  (`SaveVersion = 93`, `SaveGame.cpp:24`), then `GameSaveData` written field by field in **fixed order with no tags or
  sections**.
- Every addition is a `constexpr uint32_t SaveVersionX = N` with read-side gates such as
  `(reader.version() < SaveVersionX || readValue(reader, field))` (`:25`–`105`, 70+ versions so far). Saves from newer
  versions are rejected (`SaveFromNewerVersionError`, `SaveGame.h:57`). Migration helpers exist
  (`migrateLegacy*`, `SaveGame.h:51`–`55`).
- The top level is `GameSaveData` (`SaveGame.h:21`), written at `SaveGame.cpp:3811` and read at `:3838`: scene kind,
  map, `Party::Snapshot`, `namedGlobalVars`, outdoor and indoor states per map, game minutes, camera, held item,
  `requiredContentPackages`, name and preview.
- Party: `Party::Snapshot` (`game/party/Party.h:329`), written at `SaveGame.cpp:1061` and read at `:1107`.
  Character: `:813` and `:876`. `InventoryItem`: `:535` and `:557`. `EquippedItemRuntimeState`: `:729` and `:745`.
  `Character` itself is at `Party.h:88`.
- Build and restore: `GameSession::buildSaveData` (`game/app/GameSession.cpp:1579`) and `restoreFromSaveData`
  (`:1664`). Save and load in the app: `GameApplication::quickSaveToPath` (`:9354`) and `quickLoadFromPath` (`:9436`).
  Load runs `loadGameDataFromPath`, then `validateRequiredContentPackages`, then `restoreFromSaveData`, then the map
  load. Tables are already loaded at that point; a ruleset-aware load must read the ruleset id first and reload tables
  if it differs.
- `requiredContentPackages` (`SaveGame.cpp:4301`, `:4339`) records the non-engine packages whose items or vendors the
  save uses, with their schema version, and refuses to load if one is missing. A MAW package would register here
  naturally, so a MAW save without the MAW content fails cleanly.
- **Adding a ruleset:**
  1. The next `SaveVersion` (94 at the analysis date; 95 is taken now) adds `std::string rulesetId` (default
     `"mmerge"`) and a `RulesetOptions` struct (difficulty, progression, flags) to `GameSaveData`. They can be read
     anywhere in the sequence behind the version gate; read them early if the loader must reload tables before
     decoding package-dependent data. Older saves default to `mmerge`.
  2. Per-item fields: extend the `InventoryItem` and `EquippedItemRuntimeState` read/write behind the same gate. They
     are reused everywhere items are stored, including world items, chests, corpses, house stock and the held item.
  3. Per-character fields, such as Ascension state, spent-skill bookkeeping for the MAW reset, and MAW buff charges:
     extend `Character` read/write.
  4. Party or session fields, such as Free Progression bolster offsets per continent and Nightmare kill counters per
     dungeon, go in `Party::Snapshot`. Nightmare counters could also use `namedGlobalVars`, which Arena already uses.
  5. The bolster caches already saved per actor must be invalidated if difficulty changes mid-game. MAW forbids
     changing out of Nightmare.
- The Load list fully decodes each save (`LoadGameScreen.cpp:294`, `:725`; `GameplaySaveLoadUiSupport.cpp:172`), so
  the ruleset can be shown per slot cheaply.

---

## 7. Existing MMerge-specific settings

- MMerge "Extra settings" (`reference/mmmerge/Scripts/General/MenuExtraSettings.lua:159`) stores `UseMonsterBolster`,
  `BolsterAmount` (0–200 %), `ShowWeatherEffects`, `ImprovedPathfinding` and `FrameLimit`.
  `reference/mmmerge/Scripts/Structs/10_MergeSettings.lua` adds `Attack.Minimal*AttackDelay`,
  `Character.AutolearnRacialSkills` and `ForceZombieToUndeadRace`, `Conversions.*`, `Skills.BowDamageIncludeItemsBonus`
  and `LearningIncrease*`, `Stealing.ShopBanDuration` and `BaseFine`, and `DimensionDoor.RestrictMaps`.
- OpenYAMM equivalents:
  - `bolster_monsters` toggle, in the menu (Gameplay → Difficulty). There is **no BolsterAmount**.
  - `indoor_pathfinding` and `outdoor_pathfinding` (`[features]`, INI only, `GameSettings.cpp:1478`).
  - Weather has its own quality settings (Video).
  - `blaster_skill_scaling` and `blaster_min_recovery` (`[features]`, INI only, `GameSettings.cpp:1498`+), fed into
    `CharacterAttackTuning`.
  - The minimum attack delays are hard-coded constants (`GameMechanics.cpp:28`).
  - Stealing `BaseFine = 50` is a constant (`game/gameplay/StealingRuntime.cpp:13`).
  - The others are implemented as fixed behaviour or not at all.
- OpenYAMM-specific gameplay toggles in the menu: melee hit feedback, camera kick, skip cutscenes, combat text, health
  bars, quest markers and the context action menu.
- The MMerge bolster *tables* (`bolster_maps.txt`, `bolster_monsters.txt`) are used. The *formula* table is loaded but
  ignored (§2.4).

---

## 8. Recommended shape (for planning)

1. **Ruleset identity.** Add a `RulesetDefinition` (id, name, description, overlay root, schema version, default
   options), loaded from `assets_dev/engine/rulesets/<id>/ruleset.yml` (new) or as an `engine`-level manifest. Keep
   `mmerge` (Standard) as the implicit default with no overlay.
2. **Choice UI.** Add a ruleset selector to the continent screen: two cards or a toggle, an options sub-row for MAW
   (difficulty Easy..Nightmare, bolster Free/Horizontal) and the `ContinentSelectionStep` text. Pass a
   `NewGameOptions` struct through `ContinueAction` → `startNewSessionFromCharacterCreation`. The MAW classes appear in
   character creation only when MAW is selected (`character_selection.yml` per ruleset).
3. **Tables.** Re-mount with the ruleset overlay in front of `engine/` (precedent: `switchActiveWorld` re-initialises
   mounts), then run `GameDataLoader::loadInternal` again and rebind the repository, session and global table pointers.
   Alternatively implement `TableContributionMode::Override`. Do this at new game (after the choice) and at load
   (after reading the save's ruleset id, before `validateRequiredContentPackages`).
4. **Code.** Add an `IRulesetMechanics` interface (or a struct of function pointers plus parameter tables) owned by
   `GameSession`. It covers stat bonus, max HP/SP, attack profile, crit, recovery, incoming damage both ways, monster
   scaling and difficulty, item generation and description, value, potion effects, skill costs and thresholds, and
   experience. Route the existing `GameMechanics` statics, `ItemGenerator`, `ItemEnchantRuntime`,
   `GameplayBolsterRuntime`, `PriceCalculator`, `InventoryItemUseRuntime`, `MasteryTeacherDialog` thresholds and
   `PartySpellSystem` numbers through it. "Standard" wraps the current code unchanged.
   - Fold `CharacterAttackTuning` into it.
   - De-duplicate the experience formula (`Party.cpp:1179` and `HouseInteraction.cpp:802`) and the five kill-reward
     sites first.
5. **Data model.** Extend `InventoryItem` and `EquippedItemRuntimeState` with extra affixes, item level and tier
   (behind the next `SaveVersion`), and `GameSaveData` with the ruleset id and options.
6. **Lua** only for content-level MAW features (Nightmare dungeon rules, kill rewards, teleporter NPCs, shop reroll),
   using the existing hooks plus perhaps one or two new hook kinds (ItemUse, ShopOpen).
7. **Tests.** Use doctest for the formula strategies (`tests/`) and headless scenarios (`tests/scenarios/`) for a MAW
   new game, a save round trip and a load of a pre-ruleset save.
