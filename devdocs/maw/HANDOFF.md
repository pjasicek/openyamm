# MAW ruleset: implementation handoff

Start here when picking up the MAW work in a new session. This file states what was decided, what to build in which
order, how to check each step, and when to stop and ask the user. The analysis behind it is in [README.md](README.md)
and the spec documents it lists.

Status (2026-10-25): phases 1-9, the gap pass, the 2026-10-24 audit and the user's interface requests that followed
are built. §0 is the complete state at handoff; read it first. Keep §0, the progress table (§6), GAPS.md and
[DEVIATIONS.md](DEVIATIONS.md) up to date.

## 0. State at handoff (2026-10-25)

### 0.1 The working tree

- **Nothing of the MAW work is committed.** HEAD is `7fdb25667` ("Fix eating all items containing apple"), the
  pre-MAW Standard baseline. Every MAW file is an unstaged change on top of it: 289 modified tracked files and the
  new directories (`game/rules/`, `game/rules/maw/`, `assets_dev/engine/rulesets/maw/`, `devdocs/maw/`,
  `tests/scenarios/rulesets/`, many new `tests/*.cpp`, `tools/maw/`, `level_generation/ui/maw_*`). The staging area
  is empty. Never run `git add`, `commit`, `stash`, `restore`, `reset` or `clean`: one of them loses days of work. The
  user reviews and commits.
- The tree also carries unrelated uncommitted work of other sessions (assets, tools, third_party). Leave it alone.
- Build trees: `build/` (the coordinator's), `build-b/` and `build-c/` (the two worker sessions'). One session per
  build tree. When another session edits a shared header (`Party.h`, `Character`, `QuickItemSlot.h`, overlay types)
  during your build, objects go stale (symptoms: crashes in `Party::operator=`, or every scenario failing). Touch the
  header and rebuild.
- Save version: **128**. The next free version is **129**. Versions 115-128 were all added in this work and are
  unreleased, so a block may still be widened within its own version while nothing is committed. Once the user
  commits, add a new version instead. The table is in §0.6.

### 0.2 Test state (2026-10-25, `build/`)

- Unit suite: 2214 cases, 2209 pass. The 5 failures are known and none is MAW's: the darkmoor actor previews, the
  mm8 slime/Ogre/Vampire bindings and the demon LOD (asset owners' work in progress). "mm6 Dragoons Caverns flour
  sack" failed earlier the same day on another session's event text change and passes again.
- Ruleset scenarios: all 41 in `tests/scenarios/rulesets/` pass. `combat_log.yml` fails now and then ("actor died
  on attack 1") and passes on a rerun.
- All scenarios: the 14 MM6 story scenarios fail at HEAD too. Everything else passes.
- Runtime tests (`openyamm_runtime_tests`): 28/29. The New Sorpigal temple brazier test fails at HEAD too: it expects
  sprites, but the decorations are 3D models now.
- Packaging tests (`tools/test_runtime_packs.py`, `packaging/test_publish_release.py`) pass. The editor links.
- Commands: build `cmake --build build --target openyamm openyamm_unit_tests -j25`; unit
  `./build/tests/openyamm_unit_tests --test-case='*pattern*'`; scenario
  `./build/game/openyamm --headless-run-scenario tests/scenarios/rulesets/<name>.yml` (never put `--set` before
  `--headless-run-scenario`: that opens the real game); all ruleset scenarios in parallel:
  `ls tests/scenarios/rulesets/*.yml | xargs -P8 -I{} ./build/game/openyamm --headless-run-scenario {}`.
- Desktop runs: `./tools/run_game.sh --isolated <name> --ruleset maw:hell:horizontal ...`, only when the user's game
  is not running (`pgrep -x openyamm -a | grep -v headless` must print nothing). Captures go through the engine's own
  screenshot keys (AGENTS.md).

### 0.3 What was built after phase 9

In order. GAPS.md and DEVIATIONS.md hold the details of each row.

1. **The 2026-10-24 audit** ([AUDIT_20261024.md](AUDIT_20261024.md), nine reviewers) was verified and planned in
   [AUDIT_20261024_PLAN.md](AUDIT_20261024_PLAN.md). The user approved every recommendation (D1-D17, Q1-Q19). Three
   streams fixed every P1, P2 and assigned P3 row, each with a test or a DEVIATIONS row (142-177). The plan file has
   each stream's progress, the state at the end and the user's decisions of 2026-10-25.
2. **Rulesets in the engine package** (D15): `assets_dev/engine/rulesets/<id>/`, packed as an `engine` pack mounted at
   `/engine/rulesets/<id>`, because released updaters up to 1.10 refuse any other mount. `RulesetsRoot` and
   `rulesetPackageRoot()` (`game/content/RulesetDefinition`), `AssetFileSystem`, `AssetPackIndex`,
   `tools/runtime_packs.py`, `tools/packaging/packs.yml`, and a publish-time check (`released_updaters_accept` in
   `packaging/publish_release.py`). Saves still name the package `rulesets/<id>`.
3. **Combat log** (GAPS H.3, both rulesets, desktop only): a docked panel in the bottom-left corner beside the party
   frame, in the study's colours. Its lines are short ("Thalia kills Goblin 197": the kill word in red, "!" on a crit).
   It scrolls, has the All / Dealt / Taken filters, and a click opens a hit's damage steps. Its cost: nothing while the
   setting is off; while on, the layout is cached and the fills are palette quads. `game/ui/GameplayCombatLogPanel.*`,
   `CombatLog`, `gameplay.yml` `CombatLogPanel`. On Android the setting is hidden and never read. Left: the "+" log
   window (layout B), moving and resizing.
4. **Inventory: four bags shown together** (H.1a, DEVIATIONS 141, session C): all four bags 2x2 at half size with
   dividers; 1-4 buttons and the Bag 1-4 keys zoom one. Save 121 fits older saves' five or 25 bags into four.
5. **Bag tags** (H.10, DEVIATIONS 178, C): crafting and alchemy bags take what the party picks up. Shift+B, the hammer
   and potion buttons, save 123.
6. **Bounty presentation** (H.11, session B): a map note on the target, the boss named in the texts, and the bounty
   cancelled when someone other than the party kills the target.
7. **Party allies** (B): summons, enslaved, controlled and reanimated monsters fight for the party
   (`gameplayActorFightsForParty`); in MAW an ally's kill pays the conscious members and killing an ally pays nothing
   (`MonsterKillReward::partyAlly/byPartyAlly`); Standard unchanged. **Party-ally scenario step** (FMON-2-2, B: `maw_ally_kills.yml`, `standard_ally_kills.yml`) and the failed
   cross-ruleset load (STD3-1: scenario steps `save_game {required_package_schema}` and
   `load_game {expect_failure}`, `cross_ruleset_load_failure.yml`).
8. **Interface review of MAW against MMMerge**: about 50 visible changes, almost all already ported, done
   differently or decided against. The missing ones were then built:
   - MMMerge's four extra quick spells, in both rulesets (N8.8, save 122): spellbook buttons 1-4 and keys F5-F8.
   - Resistance rows showing the share of damage they remove, labels coloured by element (MAW, B):
     `SkillRules::resistanceCut`.
   - Bag number keys 1-4 (C).
   - Follower keys (MMMerge; `follower_keys.yml`): 0 opens the panel, 6-9 pick followers 1-4.
   - Event `GiveItem` takes `{identified=}` (FCOR-2-82, `luaGiveItem`).
   The aura-reserved share (2026-10-25, the user chose option A of the
   [study](../../level_generation/ui/maw_aura_reserve_20261025/README.md)): the held end of a portrait's mana arc (HP
   arc for Legendary 32) is a dark hatched band with a gold mark where the free pool ends
   (`GameplayUiSkin::renderReservedArc`/`renderReservedMark`, `SpellRules::reservedHitPoints` now a hook with a
   Standard 0), and the portrait popup's HP and SP lines add "(N held)". Captured; console `ruleset aura <member>
   <spell>` holds an aura for testing. The potion-slot button moved outside the mana arc (the user's report).
9. **Standard changes the user approved** (N8.6, N8.7, N8.8, N8.9): MM9 indoor HP above 32767, MM6 `SetTexture` and its
   save migration, refused projectile hits report 0, the Alchemy bench keys, the once-per-character potion text,
   Summon Wisp as MM8 has it (1/3/5 per caster by mastery, save 120), the extra quick spells, outdoor strafing at half
   the walking speed as indoors (`OutdoorMovementTuning::strafeMultiplier`), 64-bit experience (save 115), indoor
   floor items keeping their whole `InventoryItem` (save 116). Standard layout: U3 and U5 kept, U4's class label
   shrinks to fit at 145.
10. **H.6 pieces, each from a browser study the user approved** (D.16: study first, then native):
    - The **Progress tab**: the Journal's fifth tab, MAW games only (B, save 124 `MawGameState::mapVisits`,
      `game/ui/GameplayJournalProgress.cpp`, `MawMonsterRules::progressSummary`), with flags, element colours and the
      Alegreya font. The user dropped the "you are here" flag.
      [Study and native notes](../../level_generation/ui/maw_loot_progress_20261025/README.md).
    - The **loot filter presets** (C, save 126, DEVIATIONS 17 and 179): Settings → Rules → Loot filter opens a large
      window with five presets, a rarity grid for weapons, armour and jewellery with a level rule, checkmarks for the
      kinds without rarity, gold or a greyed drop, and the preset tried on this session's last 50 drops. Its small
      text is Alegreya SemiBold (the user's request, 2026-10-25; `isIndependentOutlineFont` in
      `game/ui/MenuScreenBase.cpp`). The custom rules (view A2) are not started.
    - **Potion quick-slots** (the radial, both rulesets, potions and scrolls only, weakest bottle first;
      [study](../../level_generation/ui/maw_potion_radial_20261025/README.md)). Core (A): `Character::quickItemSlots`
      (six `QuickItemSlot {itemId, bottleRule}`, save 125); `game/items/QuickItemSlots.*` (`canHold`, `findItem`,
      `countItems`, and since 2026-10-25 `findPartyItem` and `countPartyItems`: a slot draws from its owner's bags
      first, then every other member's in party order); `GameplayItemService::useQuickItemSlot` (takes the item from
      the member carrying it, uses it on the slot's owner through the held-item path, puts what is left back in the
      carrier's bag). Keys: Potion Wheel **V**, "Quick Potion (Slot 1)" **N**, Potion Slots 2-6 unbound (the user,
      2026-10-25). HUD (B): `game/ui/GameplayQuickItems.cpp`. Its state is in §0.4.

11. **MAW test parties for the debug console** (A, 2026-10-25, the user's request: let MAW's authors test any part
    of the game without grinding). `testparty <stage> [party] [+kit ...] [difficulty progression mode ...]` starts a
    new MAW game with the party at a stage; `testparty apply ...` replaces the party of the MAW game being played;
    `testparty kit <kit>` adds a kit; `testparty` lists everything. Stages start, early (20), mid (50, promoted),
    late (100), endgame (200, every map completed, dimension maps), extreme (500, Celestial) and op (1000); parties
    classic, newclasses, specials (dragon, vampire, minotaur, troll, dark elf), hybrids, casters, solo, solo_caster;
    kits healing, potions, strong_potions, reagents, gems, crafting, legendary (one item per affix 11-35), dimension,
    artifacts, scrolls. A stage sets level, experience, stats, every class skill at its level and best mastery,
    spells, MAW gear of one rarity in every slot (rolled lower or a lower rung until the level requirement fits),
    banks, gold, food, Town Portal bits and completed maps. Data: `assets_dev/engine/rulesets/maw/debug/test_parties.yml`
    (its header is the user guide); code: `game/debug/MawTestParties.*` (the console command and the pending new
    game in `GameApplication`), `MawItemRules::rollEnchantmentsAtRarity` (a roll at a chosen rarity and legendary
    affix that leaves the loot counters alone). Tests: `RulesetTests` (the catalog parses), scenario
    `maw_test_parties.yml` (every stage and party applies, fights, saves and loads) through the new scenario step
    `console: {line, expect_contains}`. Checked on the desktop: `testparty mid newclasses hell` starts the game on
    out05 with the gear worn. Portraits are picked by class (or `race:`), so the new classes get MMMerge faces.

12. **2026-10-25 follow-ups (this session)**: the aura-reserved share (option A, item 8); the potion button moved
    outside the mana arc; L8.1 used barrels and L8.2 dimension affixes 25 and 33 (DEVIATIONS 57, 60; save 127);
    console `ruleset aura <member> <spell>`. The user approved the aura panel (A), combo gems (B, smaller and
    closer to the HP arc), the map progress bar (A) and the four class icons with a three-column Choose Class grid;
    their native work records are in each study's README. A read-only readiness audit found five differences from
    MAW, all fixed to match it: a boss's loot grade reads its re-drawn level (or a unique's level, else the row's
    level, at least the map's low one; IT:283-293); boss and unique armour stays the row's (MON:751); legendaries 18
    and 22 cut traps inside the mitigation before the class's flat cut, and neither they nor Mist Form touch falls or
    drowning (ST:761-776, DM:1622-1692); a utility aura needs its full cost free, before Enlightenment (SP:2779-2794);
    two weapons average their recoveries unrounded (S:514-524). GAPS H.8 is in fact done.
    Character screen speed: the two render passes share one computation per frame (`CharacterOverlayFrameData`),
    the rules' stat rows and resistance cuts are worked out only on the Stats page and in one go
    (`SkillRules::statRows`, `resistanceCuts`; MAW from one power report and one sheet), and item skill bonuses are
    kept under canonical skill names so `Character::skillBonus` is one lookup (about 500 to 900+ FPS on a late MAW
    party). A saving audit (food cost, Beyond Madness death count) found three differences, all fixed: F10 quick load
    warns first and loads on a second press within ten seconds (as MAW's block-once); the death count is kept in the
    save too (save 128) and seeds the ledger when its file has no line for the run (zzMaw-Monsters.lua:2385-2400); a
    save that is not written gives its food back. Loading a MAW save now installs the ruleset and its state before the
    party is restored, and `Party::setClassSkillTable` rebuilds the derived state after refreshing base HP and SP:
    before, a loaded party had Standard-sized maximums (its HP and SP clamped to them) until the next rebuild. A
    refused attack spell (an Assassin short of combo points) attacks with the weapon instead, as quick cast does.
    Peasant has its own class icon (a straw hat, `maw_class_icons_20261025/`). A player's guide for MAW is hosted at
    https://jasicek.net/openyamm/maw-guide/ (`/var/www/html/openyamm/maw-guide/` on the server); `ruleset.yml`'s
    `guide_url` links it from the Rules panel (top right) and the journal's Progress tab header.

13. **Map progress bar** (2026-10-25, the user approved option A of the
    [study](../../level_generation/ui/maw_map_progress_20261025/README.md#native-integration-2026-10-25)): a 5 px
    channel in the party frame's top band, the numbers ("38.5 % · 112 / 292", slain of needed) on a tab at the
    right corner, gold and full once cleared until the refill, the 65 % revival mark only where the dead can rise,
    dimension runs (teal-violet, "Dimension · Power N" tab) and the Endless Arena; a hover popup through the
    buff-inspect tooltip. `MonsterRules::mapProgress` (Standard none) replaces `mapProgressText`; MAW's pure
    `mawMapProgress`; `game/ui/GameplayMapProgressBar.*`, `GameplayMapProgressText.cpp`; layout
    `MapProgressChannel` under `OutdoorGameplayBasebar`. The minimap plate is gone. Tests `MawMapProgressTests.cpp`,
    MON-16. DEVIATIONS 180. Captured; a dimension run is not captured natively.

### 0.4 In flight at handoff

- **Potion radial HUD (B): built, waiting for the user's approval of the picker, the miniature and the socket.**
  - Portrait button (upper right of each portrait): a miniature of slot 1's item with the party-wide count, greyed
    and red when the party has none; with slot 1 empty, a black inner socket (the user asked for it over a dot). A
    click opens or closes that member's ring.
  - Ring above the portrait: six slots with party-wide counts (`countPartyItems`), a key badge only on bound slots
    (by default only slot 1, "N"); a left click uses the slot, an empty slot or a right click opens the picker; the
    hub says ready, recovering, "next fed by X" or nobody ready.
  - Inline picker beside the ring (gameplay continues): one row per kind and strength from every member's every bag
    (icon, name, xN, "strength P · carriers"), potions first, then scrolls, wheel and scrollbar; Weakest first /
    Strongest first, Clear slot, Close. Escape or a click away closes the picker, then the ring. The inventory assign
    mode is gone.
  - Clicks on the ring never reach the world (the user's report "assigning with LMB the party attacks"):
    `GameplayQuickItems::takesPointer` / `takesPointerAction` keep world LMB, and Attack, Use, Trigger, CastReady and
    Quick Spell 1-4 when bound to a mouse button or the wheel, out of world interaction while the ring is open or a
    click on it is held. Gates in `GameplayInteractionController::updateWorldInteractionFrame` and the quick-cast
    block of `GameplayInputController.cpp`. Keyboard-bound actions still work; whether keyboard Attack should also be
    blocked while the ring is open is an open question for the user.
  - Captures: `level_generation/ui/maw_potion_radial_20261025/native/` (ring_empty, picker_full, ring_assigned,
    buttons). Not captured: the greyed none-left miniature (needs a party whose last bottle of a kind runs out).
  - Next: show the user these captures; a scenario for the picker (open from an empty slot, assign a row another
    member carries, check the party-wide use and that a mouse-bound Attack does not fire); it needs a
    `quick_item_picker` assert or a pointer step in the scenario runner.

- **Loot filter, step 2: the custom rules (view A2 of the study). Not started.** `RulesetLootFilterPreset::Custom`
  exists; the window shows it disabled ("Coming next"). `evaluateLootFilter` treats it as a preset with empty columns.
  To build: an ordered rule list on `RulesetLootFilter`, each rule a rarity ceiling, item types (Other included), an
  optional level gap below the party and an action (Keep, Gold or Ground). The first row (Legendary, Celestial or
  artifact → Keep) can be switched off but not moved; the last ("Everything else") changes only its action. An editor
  moves, removes and adds rows; "Customize rules…" and the Custom preset start from the current preset; the recent
  drops name the rule that decided each. Store it in save 126's block while nothing is committed, else in 127. Add
  tests and a capture.
  The code lives in `game/rules/LootFilter.*` (presets, `evaluateLootFilter`, `RecentLootDrops`),
  `game/content/RulesetOptions.*` (`RulesetLootFilter`, the legacy migration), `game/gameplay/GameplayLootFilter.*`
  (`filterDroppedLoot` at the corpse and the two chest points), `game/ui/screens/MainMenuLootFilter.cpp` (the window),
  `MawItemRules::lootFilterFacts`, and the scenario `maw_loot_filter.yml`.
- Not captured: a greyed filtered drop in a real corpse or bag view. The flag is unit-tested; the desktop attempt was
  killed by corsairs.

### 0.5 Open work and questions, the whole list

Questions to put to the user (the current behaviour stays until they answer):
- Loot filter: are the five presets and their thresholds right? Regular is MAW's filter at Uncommon plus the level
  rule. Are the rarity groups and the kinds without rarity right?
- Potion radial: approval of the picker, the slot-1 miniature and the empty socket (§0.4); should keyboard Attack
  also be blocked while the ring is open?

Open rows (GAPS.md ids):
- H.6: the loot filter's custom rules (§0.4); it needs a browser study the user approves first (D.16). Wands on the
  radial are a later option the user left open. The aura panel is native since 2026-10-25 (option A of the
  [study](../../level_generation/ui/maw_aura_panel_20261025/README.md#native-integration-2026-10-25):
  `SpellRules::auraReport`, `game/rules/maw/MawAuraReport.cpp`, `game/ui/GameplayJournalAuras.cpp`, key Open Auras).
- H.3: the combat log's "+" window (layout B), moving and resizing.
- H.8: mercenaries' skill points Σ(4+⌊i/10+1⌋) and class kinds by continent.
- H.9: wider value cells in `character.yml` for numbers below 10000 that are cut ("1417 - 14").
- Not ported by decision, do not build: H.5 damage recount, the randomizer (DEVIATIONS 138), the solo potion keys,
  disableBow, ColouredStats, the Alt item view, a loot-odds page, Saving Goobers.
- Android: the new UI art is not cooked for Android: bag tag icons, the loot filter and Progress art, the radial.
  Cook only when the user asks (`tools/cook_android.sh`). The radial and the Progress tab have no Android check.
- Before a release or commit: `tools/lighting/stale_bakes.py` (AGENTS.md).

Then play-testing: every system is unit- and scenario-tested, but MAW games have had little real play. Bugs the user
reports in play come first.

### 0.6 Save versions of the MAW work

| Version | Constant (`game/maps/SaveGame.h/.cpp`) | What |
|---|---|---|
| 96 | `SaveVersionRuleset` | ruleset id and options |
| 97 | `SaveVersionItemRulesetFields`, `RandomRootSeed` | item ruleset fields, random root seed |
| 98 | `SaveVersionActorRulesetFacts` | per-actor MAW facts, 32-bit indoor HP |
| 99 | `SaveVersionMawLootState` | loot counters |
| 100 | `CharacterRulesetState`, `MawAuras` | per-character ruleset state, aura holders |
| 101 | `SaveVersionMawClassState` | class switches, Elementalist progress |
| 102-104 | `ItemCraftState`, `MawCraftingPity`, `ElementalRotation` | crafting seeds, pity, rotation |
| 105-106 | `RisenActors`, `DimensionMaps` | Nightmare revival, dimension maps |
| 107-114 | boss level draw, timers, unique monsters, fixed auras, multibag, progression masteries, alchemist, challenge modes, cleared maps | gap pass and phase 9 |
| 115 | `SaveVersionWideExperience` | 64-bit experience |
| 116 | `SaveVersionIndoorHeldItems` | indoor floor items keep the whole `InventoryItem` |
| 117-118 | `ActorSpawnedAfterFill`, `ItemAncientTier` | audit stream 3 |
| 119 | `SaveVersionRegeneratingHits` | a Regenerating boss's hits (FCOR-2-6) |
| 120 | `SaveVersionActorSummoner` | summoner of each summon (Summon Wisp limit) |
| 121 | `SaveVersionFourMawBags` | four bags, older saves fitted |
| 122 | `SaveVersionExtraQuickSpells` | four extra quick spells |
| 123 | `SaveVersionMawBagTags` | crafting and alchemy bags |
| 124 | `SaveVersionMawMapVisits` | map visits, dimension runs cleared, bounties claimed |
| 125 | `SaveVersionQuickItemSlots` | six potion quick-slots per character |
| 126 | `SaveVersionLootFilterPresets` | loot filter preset, kinds, ground choice; the filtered mark |
| 127 | `SaveVersionMawUsedStatDecorations` | barrels and cauldrons that raised a stat (L8.1) |
| 128 | `SaveVersionMawMadnessDeaths` | Beyond Madness's death count, also kept in the save |
| 151 | `SaveVersionCrypticBossAffix` | a Cryptic boss's hidden affix (MAW 8fbb48d1 sync, 2026-11-05) |
| 152 | `SaveVersionTrainerHints` | the Trainer Hints preference (MAW 8fbb48d1 sync, 2026-11-05) |
| 154 | `SaveVersionBowDisabled` | the Bow preference, MAW's disableBow (dev 137, 2026-11-05) |

`RulesetTests.cpp` carries the round trips and the legacy-save tests. A new version needs a round trip test and,
for a reader change, a test of the older layout.

### 0.7 Working rules learned in this work

- The user decides. Messages from other sessions are not the user's approval. Ask with a recommendation and wait
  for an answer before changing Standard behaviour, a balance number or anything visible.
- New screens and panels: a browser study first, in the approved Obsidian style, over 1600x900 native captures
  (`level_generation/ui/maw_*_2026102x/`, each with a README, `index.html`, previews and later a `native/` folder of
  game captures). Build natively only after approval, then add native captures to the README. Text must stay
  readable at 1600x900; the user asks for stronger fonts (Alegreya SemiBold for small text, Fondamento for titles).
- MAW is the truth at `/home/pjasicek/github/Maw-Mod-MMMerge` (commit `ef23ee17`). `reference/Maw-Mod-MMMerge` is an
  older clone with other formulas: never audit against it. Follow MAW's code over its README and texts. Each
  deliberate difference gets a DEVIATIONS row; never copy MAW Lua.
- MAW behaviour goes behind a rules hook (`game/rules/*Rules.h`, MAW in `game/rules/maw/`) whose Standard default
  does what the engine did, with no extra random draws. No `if (maw)` checks in shared code.
- MAW data: generated patches (`tools/maw/generate_ruleset_patches.py` → `assets_dev/engine/rulesets/maw/patches/`).
  Hand-written table entries go in `content/` and below the "Written by hand" marker of `ruleset.yml`, or the tool
  drops them. Map content goes in Lua and scene overlays under `engine/rulesets/maw/events/` and `maps/`. MAW event
  ids: map events 60001+, topics 10010-10040, hooks 65310 and 65400/65401, QBits 10001+.
  `requireFreeGlobalEvent` (`event_support.lua`) refuses an id another title holds.
- Keys are scarce. New actions go into the settings catalog's groups (`settings_catalog.yml`, `ruleset: maw` for MAW
  only) and `KeyboardBindings.cpp`; give a default key only where one is free, else leave it unbound.
- Android gets no combat log and no new controls unless the user asks.
- Scenario steps added in this work: `console {line, expect_contains}`, `grant_item`, `use_item`, `craft`, `combine_gems`, `set_ruleset`,
  `ruleset_banks`, `damage_actor {all, skip_dead}`, `save_game {required_package_schema}`, `load_game {expect_failure}`,
  `setup_shortcut {kind: set_quick_item, member_index, slot, item_id, strongest}`, `setup_shortcut set_experience`,
  `setup_shortcut hire_follower`, `spawn_actor {party_ally}`, the asserts `dialog.text_contains` and
  `journal_map_note`, the ruleset keys `loot_filter` and
  `loot_filter_ground`, and the asserts `combat_log {loot_min}`, `quick_item_ring`, `crafted_items_min`,
  `potion_effects_min/max`, `member_classes`. See `tests/scenarios/README.md`. Scenarios run with a fixed root seed
  (`ScenarioRuntimeDriver`), so their rolls repeat.
- Desktop runs started with `--map` get a one-member party; use `--save saves/maw_classic_heroes.oysav` (five
  members) for party-wide checks. A tour's `wheel: N` step is one wheel event whatever N is.

### 0.8 Where things are

| Need | Look in |
|---|---|
| What MAW does, per area | [README.md](README.md) and its specs: COMBAT_SPEC, BALANCE_MODEL, ITEMS(_DATA), RANDOMS, TRAINERS_SKILLS, CLASSES_SPELLS_SPEC, SKILLS_SPELLS_ALCHEMY, CRAFTING(_BENCH_DESIGN), MAPS_CONTENT, MONSTER_TABLE_DIFF, UI_CONTENT, `data/*.yml` (drafts; MAW's code wins) |
| What is missing or done, by id | [GAPS.md](GAPS.md) (§11: every decision the user made) |
| What we do differently on purpose | [DEVIATIONS.md](DEVIATIONS.md) (rows 1-180) |
| The audit and its fixes | [AUDIT_20261024.md](AUDIT_20261024.md), `audit_20261024/` (per-area reports), [AUDIT_20261024_PLAN.md](AUDIT_20261024_PLAN.md) |
| Challenge modes | [PHASE9_SCOPE.md](PHASE9_SCOPE.md) |
| How the three sessions split work | `parallel/` (README, SESSION_B, SESSION_C) |
| Engine seams | [ENGINE_INTEGRATION.md](ENGINE_INTEGRATION.md), `game/rules/` |
| The ruleset package | `assets_dev/engine/rulesets/maw/` (`ruleset.yml`, `patches/`, `content/`, `data/`, `events/`, `maps/`) |
| UI studies and captures | `level_generation/ui/ruleset_choice_20261023/` and `maw_*_2026102x/` |
| Test parties for MAW's authors | `assets_dev/engine/rulesets/maw/debug/test_parties.yml`, console `testparty` |
| Desktop runs with a ruleset | [tools/RUN_GAME.md](../../tools/RUN_GAME.md#rulesets) (`--ruleset maw:hell:horizontal`) |
| Pre-MAW Standard comparison | build HEAD `7fdb25667` in a private tree and run the same scenarios on both |

## 1. Decisions taken (2026-10-23)

| Topic | Decision |
|---|---|
| Permission | The MAW author agrees to the integration. Reimplement behaviour as new code; never copy MAW Lua. Credit the MAW team (MAW README credits list) in the ruleset description |
| Ruleset identity | **One shared identity** for MAW, the future vanilla modes ([../vanilla/README.md](../vanilla/README.md)) and hardcore ([../plans/HARDCORE_MODE_INVESTIGATION.md](../plans/HARDCORE_MODE_INVESTIGATION.md)): ruleset id `mmerge` (default) or `maw` now, `mm6`/`mm7`/`mm8` later, plus an options record. Do not implement vanilla or hardcore rules; only keep the identity generic enough for them |
| Where the choice lives | **Continent screen plus a Rules panel**: a Standard/MAW switch above the three continent cards; "Rules…" opens one panel with difficulty, progression, challenge mode, randomizer and preferences ([README.md](README.md) §4.1) |
| Difficulty changes | **Like MAW**: changeable during play from an in-game "Current game" page, except that Nightmare and the challenge modes lock. A change must invalidate cached per-actor monster stats |
| First target | **A playable MAW: phases 1–7** ([README.md](README.md) §4.6). Phases 8 (content) and 9 (challenge modes, randomizer) come after |
| MAW version | Port the behaviour of MAW commit `ef23ee17` (`/home/pjasicek/github/Maw-Mod-MMMerge`). Follow the code, not MAW's README |
| MAW bugs | Default: fix each bug listed in [README.md](README.md) §6 and in the specs, and record it as a deviation (§4). Ask the user only where a fix changes balance noticeably |
| Crafting (2026-10-23) | The Mirror copies no artifacts; the Emerald of Power sells; every alchemist and magic shop may stock crafting items; dimension-map drops get 4/3/2 affixes at 10/20/70 %; Doom's caps use exact arithmetic (138); the Workbench opens from the inventory only; crafting is instant and Apply ×N runs the whole batch; our own crafting item icons through the icon pipeline |

Still open: the decisions owed in [GAPS.md](GAPS.md) §11 (ask the user; do not guess).

## 2. Ground rules

These come from `AGENTS.md`, `CLAUDE.md` and the user's global instructions; they override anything here.

- Never `git add`, `commit`, `stash`, `restore --staged` or `reset` unless the user asks. The user reviews unstaged
  changes in VS Code; review notes are `AI:` comments (follow the `address-review-notes` skill).
- Build: `cmake --build build --target openyamm -j25`. Unit tests: `cmake --build build --target openyamm_unit_tests
  -j25`, then `./build/tests/openyamm_unit_tests --test-case='*pattern*'`. Headless runtime checks:
  `./build/game/openyamm --headless-run-scenario <scenario.yml>` (examples in `tests/scenarios/`). No Vulkan builds.
- Coding style: C++20, 120 columns, braces on new lines, `m_` members, `p` pointers, explicit types over `auto`, no
  `[[nodiscard]]`, `override` everywhere. Match the surrounding code.
- Never hand-edit generated event Lua (`-- generated from legacy EVT/STR`); MAW map content goes into overlays.
- No adapter layers that only forward calls, no scattered `if (maw)` checks (the MM9 `usesMm9ActorRules` pattern is
  the anti-example), no compatibility fallbacks that hide broken state.
- Line numbers in the MAW docs are from the analysis date. OpenYAMM has moved since (for example `SaveVersion` was 93
  in the docs and is 95 now); re-locate code by name before editing.
- Standard MMMerge must not change behaviour. Every phase ends with the existing unit tests and scenarios passing.

## 3. Architecture contracts

Keep to these so the phases fit together. Details: [ENGINE_INTEGRATION.md](ENGINE_INTEGRATION.md) §8 and
[README.md](README.md) §4.2–4.5.

1. **Ruleset identity in the save.** `GameSaveData` gains a ruleset id string (default `mmerge`) and a
   `RulesetOptions` record, written behind the next `SaveVersion` gate and read before anything that needs ruleset
   tables. Older saves load as `mmerge`. The Load screen shows a badge (`MAW · Hell difficulty · Horizontal
   progression`) and filters saves by ruleset.
   - Options for MAW: difficulty (Easy, Normal, MAW, Hard, Hell, Nightmare), progression (free or horizontal),
     challenge mode (none, Doom, Insanity, Madness, Austerity), randomizer flag, locked flags (true Nightmare,
     challenge mode), preferences (homing, friendly fire, loot filter).
   - Mutable after creation: difficulty within the locks, progression, preferences. Immutable: ruleset id, challenge
     mode, randomizer.
2. **Ruleset package.** `assets_dev/engine/rulesets/maw/` with `ruleset.yml` (id, name, description, credits, schema
   version, declared id ranges, option definitions), `patches/`, `tables/` (new YAML tables), `events/` (overlays).
   `assets_dev/engine/data_tables/` stays the Standard ruleset and is never edited for MAW. Packaged builds get a
   separate `assets/rulesets/maw.zip`, mounted only for MAW games, at no cost to Standard players.
3. **Table loading.** Implement the parsed-but-unused `TableContributionMode::Override` (keyed row and cell
   overrides, and whole-table replacement for `english/potion.txt` and `english/potnotes.txt`), reusing the existing
   `Append` machinery. Common data reloads and rebinds when the ruleset changes: at new game after the choice, and at
   load after reading the save's ruleset id.
4. **Generated patches.** A tool (precedent: `tools/export_mm6_world_tables.py`) builds `patches/` from MAW
   `ef23ee17` against the MMMerge base, cell by cell, in our table formats. Never hand-copy whole MAW rows: they
   would undo our fixes (items 1307, 2030, 2045). Spellbook drop weights, random items 418 and 1220 included, take
   MAW's values in the MAW ruleset by the user's D4 of 2026-10-24 (audit DAT-3); Standard keeps ours. [ITEMS_DATA.md](ITEMS_DATA.md),
   [MONSTER_TABLE_DIFF.md](MONSTER_TABLE_DIFF.md) and [TRAINERS_SKILLS.md](TRAINERS_SKILLS.md) §6 list the expected
   output; use them as the tool's acceptance test.
5. **Rules interfaces owned by the session.** One interface per rules area (combat formulas, monster stats, item
   generation and value, skills and teachers, spells, potions, experience). The Standard implementation wraps
   today's code unchanged; the MAW implementation overrides only what MAW changes. Where only numbers differ (spell
   costs, recipes, class tables, mastery thresholds), keep one code path that reads per-ruleset data.
6. **Damage as ordered stages.** A pipeline of named stages that records each stage's input and output (the concept
   of MAW's `Modules/MawCore/Pipeline.lua`, not its code). Standard is one implementation of the stages; the
   recording feeds the damage breakdown and combat log for both rulesets.
7. **Item record.** Extend `InventoryItem` and `EquippedItemRuntimeState` (and their copy helpers and save code)
   with: second base enchant, stored loot rarity (separate from today's `ItemRarity`), legendary affix, item power,
   drop level, quality %, craft seed, potion charges. Store rarity; never derive it.
8. **Deterministic random streams.** One save-level seed and named streams keyed by stable ids (domain, map, actor or
   chest, counter), per [RANDOMS.md](RANDOMS.md) §6. Loot is rolled at kill time and keyed by the drop. Combat rolls
   stay on plain randomness.
9. **Per-character MAW state** (Ascension, aura reservations, Cover/Mana Shield toggles, remembered masteries) lives
   in an optional ruleset block on `Character`, so Standard saves stay lean.

## 4. Deviations log

Every place where OpenYAMM's MAW deliberately differs from MAW `ef23ee17` (bug fixes, engine-workaround removals,
UI replacements) gets one line in `devdocs/maw/DEVIATIONS.md`: what MAW does, what we do, why, and the spec section.
Create the file with the first deviation. Unit tests encode our behaviour, not MAW's bug.

## 5. Phases

Each phase: read the listed documents first, implement, add tests, build, run the unit tests and relevant scenarios,
update §6, then stop and summarise for the user before starting the next phase. Phases 3–5 depend on each other
through the balance model (monster numbers are defined against the expected player), so test them against the
golden data rather than by feel.

### Phase 1 — Ruleset identity and choice

Read: README §4.1–4.2, ENGINE_INTEGRATION §1–2 and §6, [../vanilla/ENGINE.md](../vanilla/ENGINE.md) "What a ruleset
needs".

- `RulesetDefinition` loaded from `assets_dev/engine/rulesets/<id>/ruleset.yml`; `mmerge` is implicit with no overlay.
- Save field and options (§3.1); Load-screen badge; refusing a save whose ruleset package is missing (the existing
  `requiredContentPackages` check is the model).
- Mount the ruleset overlay and reload/rebind common data on ruleset change (§3.3). The precedent for re-mounting is
  `AssetFileSystem::switchActiveWorld`.
- New-game flow: widen `NewGameScreen::ContinueAction` into a `NewGameOptions` struct carrying ruleset and options
  into `startNewSessionFromCharacterCreation`.
- UI: **first** a browser mockup of the continent screen with the ruleset switch and the Rules panel in the approved
  Carved Obsidian style (see the menu study referenced in `AGENTS.md`, `level_generation/ui/menu_study_20260928/`),
  shown to the user for approval; then native integration in `continent_selection.yml` and
  `NewGameScreen::drawContinentSelection`. The in-game "Current game" page (read-only ruleset, mutable difficulty)
  can come with phase 3.
- Add a short `AGENTS.md` pointer: rulesets live in `assets_dev/engine/rulesets/`, override named engine tables, and are the
  agreed exception to "worlds must not own gameplay tables" (show the wording to the user).
- Tests: save round trip with and without a ruleset; loading a pre-ruleset save; table override unit tests; a
  headless scenario starting a MAW new game with an empty ruleset package.

### Phase 2 — Rules seams and engine gaps (Standard unchanged)

Read: README §4.3, ENGINE_INTEGRATION §3, [CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §1 (spell table blocker).

- Rules interfaces with Standard implementations wrapping current code (§3.5). De-duplicate first: the experience
  formula (two copies) and the five kill-reward call sites.
- Damage stage pipeline with recording (§3.6).
- Engine gaps from README §4.3: move every `BackendSpellRule` number into `spells.txt` (and resolve the ~20 existing
  disagreements with the user if any change Standard behaviour); potion effects as data with a Standard
  `potion_effects.yml` reproducing today's switch; potion ids out of `InventoryItemMixingRuntime.cpp`; monster-table
  parsing fixes; special-enchant footer rows; the `house_data.txt` map-column bug (ask before fixing data).
- Item record extension (§3.7) and save support, unused by Standard.
- Deterministic random streams (§3.8), used by Standard only where behaviour is unchanged.
- The patch generator tool (§3.4) producing `assets_dev/engine/rulesets/maw/patches/`.
- Tests: every existing test still passes; a Standard golden check that spell numbers, potion effects and combat
  results are unchanged before and after the move to data.

### Phase 3 — MAW combat, monsters, difficulty, progression

Read: [COMBAT_SPEC.md](COMBAT_SPEC.md), [BALANCE_MODEL.md](BALANCE_MODEL.md),
[MONSTER_TABLE_DIFF.md](MONSTER_TABLE_DIFF.md); data `difficulty.yml`, `monster_scaling.yml`, `map_levels.yml`,
`bosses.yml`, `exp_curve.yml`, `balance_golden.csv`.

- MAW combat formulas: stat effects, mitigation, crit, hit and dodge, recovery, leech, homing as a projectile property.
- Monster stat resolver plus the balance model, computed per spawn (never by rewriting the shared monster table);
  replaces `GameplayBolsterRuntime` under MAW.
- Difficulty, density, bosses with affixes (consider the actor behaviour system), progression banks (free and
  horizontal), mastery thresholds by mode, map completion and Nightmare respawn rules, experience.
- The "Current game" page with difficulty changes and cache invalidation.
- Tests: `balance_golden.csv` rows and the `COMBAT_SPEC.md` §11 worked examples as doctest cases.
- Monster spell formulas were not covered by the analysis; investigate them at the start of this phase.

### Phase 4 — MAW items and loot

Read: [ITEMS_DATA.md](ITEMS_DATA.md), [RANDOMS.md](RANDOMS.md), [ITEMS.md](ITEMS.md); data `loot.yml`,
`legendary_affixes.yml`, `artifacts.yml`, `special_enchants.yml`, `rarity_golden.csv`.

- Rarity roller with bad-luck protection, 2+1 enchants, item level, level requirement, value, Celestial, legendary
  affixes, artifacts, shop rules with a visible reroll button, loot filter, item tooltip per the spec.
- Tests: `rarity_golden.csv` (it reproduces MAW's loot-guide PDF), the computed damage/AC/strength tables in
  `ITEMS_DATA.md`.

### Phase 5 — MAW skills and spells

Read: [TRAINERS_SKILLS.md](TRAINERS_SKILLS.md), [CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §1–4; data
`skill_rules.yml`, `mastery_requirements.yml`, `spells.yml`, `buff_auras.yml`, `crowd_control.yml`.

- Skill rules, shared-cost discount, continuous regeneration and meditation, Ascension replacing Learning, buff auras
  with mana reservation (the largest systemic change), crowd control with diminishing returns, the four new skills,
  respec, teacher prices, trainer relocation as a static data overlay.
- Tests: the Ascension, aura and crowd-control tables in `CLASSES_SPELLS_SPEC.md`; the respec worked example in
  `TRAINERS_SKILLS.md`.

### Phase 6 — MAW classes and races

Read: [CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §5–6; data `class_perks.yml`, `promotions.yml`,
`race_bonuses.yml`.

- Seraphim, Death Knight, Shaman, Elementalist, the Assassin rework; promotions (cross-world, random, Elder/Ultimate
  per character, not by mutating the class table); race bonuses; class perk cards in character creation.
- Portraits and paperdolls for the new classes reuse existing art (MAW adds one portrait, 77).

### Phase 7 — Alchemy and crafting

Read: [CRAFTING.md](CRAFTING.md), [CRAFTING_BENCH_DESIGN.md](CRAFTING_BENCH_DESIGN.md), CLASSES_SPELLS_SPEC §7; data
`crafting_items.yml`, `potion_effects.yml`, `potion_recipes.yml`.

- MAW recipe tables in the existing alchemy bench (all recipes known, power requirements, charges, effect-at-power
  preview); the Workbench Crafting tab per the design (preview equals apply, batch gems, Combine 3 → 1, dropping a
  crafting item on equipment opens the bench). Ask the open crafting questions (§1) before this phase.
- Crafting item icons: generate our own through the usual icon pipeline rather than reusing MAW's LOD art.

After phase 7: a full MAW playthrough smoke test (headless scenarios for new game, combat, loot, crafting, save and
load), then report to the user and agree phases 8 and 9 ([MAPS_CONTENT.md](MAPS_CONTENT.md), data
`map_overlays.yml`, `dimension_affixes.yml`).

## 6. Progress

The "Left" notes below are what each phase left at the time; [GAPS.md](GAPS.md) is the maintained list (ids L, A, N).

| Phase | Status | Notes |
|---|---|---|
| 1 Ruleset identity and choice | done (2026-10-23) | `RulesetDefinition`/`RulesetOptions` (`game/content/`), `assets_dev/engine/rulesets/maw/ruleset.yml` (no tables yet; its `rulesPanel` holds the Rules panel text), override and replace table contributions applied in `GameDataLoader::loadTextTableRows`, SaveVersion 96, `GameApplication::activateRuleset` at new game and load, `NewGameOptions`, Load-screen badge. UI: ruleset switch on the continent screen and the scrolling Rules panel (`ruleset_rules.yml`, `NewGameScreen::drawRulesPanel`) from the approved [mockup](../../level_generation/ui/ruleset_choice_20261023/README.md); each control is enabled only for choices `ruleset.yml` offers, so challenge modes and the randomizer show disabled until phase 9 lists them. Testing: `--ruleset maw:hell:horizontal` ([Desktop game runs](../../tools/RUN_GAME.md#rulesets)), `RulesetTests.cpp`, `tests/scenarios/rulesets/`. [DEVIATIONS.md](DEVIATIONS.md) 1–4 agreed. Release packages carry the `rulesets` package since the gap pass (GAPS.md E.1) |
| 2 Rules seams and engine gaps | done (2026-10-23) | Spell numbers (mana, recovery, damage, projectiles, required mastery, per-mastery damage scale) live only in `spells.txt` (`spellNumbersAtMastery`); the user chose MMMerge's numbers where code and table disagreed (19 spells). Potion effects and the item-potion ids live in `engine/data_tables/potion_effects.yml` (`PotionEffectTable`, on the potion settings table). Monster table: spreadsheet numbers and MM6/MM7 letter preferences (user-approved Standard change). Special enchantments end at the first blank row. `house_data.txt` map column fixed for 180 houses (`data/house_map_fixes.tsv`, user-approved). Rules: `game/rules/` (`GameRules` on the party: `ExperienceRules`, `CombatRules` with the damage stage pipeline traced to the combat log); the level formula and kill experience exist once. Item `ItemRulesetFields`, random root seed and `RandomStreams` (SaveVersion 97). Patches: `tools/maw/generate_ruleset_patches.py` writes `assets_dev/engine/rulesets/maw/patches/` and `REPORT.md` (new MAW rows are listed, appended in phases 4-7). Golden tests: `tests/StandardRulesGoldenTests.cpp` and `tests/data/`. Monster stats, items and skills get their rules objects in the phases that change them (no forwarding layers before then) |
| 3 Combat, monsters, difficulty, progression | done (2026-10-23), see the notes for what is left | `game/rules/maw/`: `MawRules` (owned by `GameSession`, installed on the party; options, `MawGameState` level banks, seeded rolls), `MawMonsterRules` (MMMerge bolster off; per-spawn level from `map_levels.yml` and the banks, HP/damage/AC/experience from `MawBalanceModel` against the family's B level, saved per actor as `ActorRulesetFacts`; density; bosses with 12 of the 14 affixes, the per-frame boss effects in `updateMonsters`; Nightmare's food for saving and teleport block), `MawCombatRules` (monster hits: Speed roll and GM Dodging, model damage with the ±25 % spread, hyperbolic mitigation, disease, deep overkill from Nightmare; party weapon attacks: MAW hit chance, two-roll damage × speed multiplier, crits, MAW recovery; missiles hit-rolled at impact and homing with the preference; spells: `spellPowers` dice in the spells patch, Ascension, Int/Per, spell crits; monster resistances ÷2^(res/100) capped at 200; map-event traps; monster against monster), `MawExperienceRules` (MAW curve, per-member kill experience, banks, map completion). Indoor actor HP is 32-bit; SaveVersion 98. Difficulty changes from the pause menu's Settings → Rules tab (the `game` section of `settings_catalog.yml`, ruleset games only, sharing the Updates tab's slot); the current map re-sizes at once, every other map on load (`GameSession::setRulesetOptions`; console `ruleset difficulty <id>`, `ruleset banks`; scenario step `set_ruleset`). Tests: `MawCombatFormulaTests.cpp` (all COMBAT_SPEC §11 examples), `MawMonsterLevelTests.cpp`, `RulesetTests.cpp`, `tests/scenarios/rulesets/maw_*.yml`. DEVIATIONS 8-11. **Left:** the Swapper and Puller affixes (they move the party), Broodlord and Omnipotent; Nightmare's revival of uncleared dungeons (indoor actors cannot be resurrected yet); chest traps under MAW; MAW's monster-missile homing; leech (its table comes from item specials, phase 4); the character-sheet rows of COMBAT_SPEC §3 (with phases 4-6) |
| 4 Items and loot | done (2026-10-23), see the notes for what is left | `ItemRules` (`game/rules/ItemRules.h`, in `GameRules`; Standard wraps the old roll, value, name and stat code; the session also binds it with `bindItemRules` for reads without a party: character sheet, values, names). `MawItemRules` (`game/rules/maw/`): every enchantable drop rolls a loot tier, a rarity with bad-luck protection (`mawRollRarity`; shops no Primordial and up, Austerity no Legendary), item power from its drop level (monster level; chests the map's median native level; shops 0.75 x the banked levels), 2 base enchantments (slot multipliers, skill enchantments, sync) and the special of its grade's pool with the melee/caster swap, a legendary affix (least found first) on Legendary and Celestial; 0.5 % of non-shop drops become an artifact (pity, least found first). Reads: weapon damage and armour by item power and ladder rung, artifacts as top-rung items at the party's level with their stat budget, the second enchantment and the read transforms (HP/SP, resistances +10 and halved on rings, skills capped by the trained skill, hats x1.5), Celestial items rescaled to the wearer, level requirement (refused at equip), MAW value (x0.4 to sell, buy screens value^(1+0.08 n)), rarity names and colours, inspect lines (enchantments, legendary text, attack speed, item level, level required). `MonsterRules::corpseLoot`: MAW drop chance, grade and gold by level, bosses always drop, rolls keyed by map visit and actor. Loot filter on corpses and chests (the item's 0.4 value as gold). Shops roll through the party's rules and show a "New stock" button with its price (`HouseServiceRuntime::tryRerollStock`). Data: `engine/rulesets/maw/data/items.yml` (bases, artifacts, legendary texts, generated from the devdocs data). SaveVersion 99 keeps the loot counters. Console `item roll <tl> [count] [drop level]`. Tests: `MawItemFormulaTests.cpp` (golden rarity table analytically and by simulation, strength, level requirement, damage, armour, attack speed, values, MAW item rules), `tests/scenarios/rulesets/maw_loot.yml`. DEVIATIONS 12-17. **Left:** legendary affix effects other than 12 and 16 (they hook combat, the sheet and recovery); special enchantments scaled by item power (MAW's bonusEffects, school and meditation skills; the damage specials are done, see the gameplay-gaps row) and the leech specials; artifact behaviour tables (on-hit, drain, wear rules, buffs; artifacts keep Standard's powers for now); resistance enchantments as the best per element rather than a sum; Doom's unidentified items; the per-slot reroll strength and crafting materials in shops (phase 7); chest gold rewrite and potion remaps; the Power/Vitality comparison and a loot-odds page |
| 5 Skills and spells | done (2026-10-23), see the notes for what is left | `SkillRules` and `SpellRules` (`game/rules/`, in `GameRules`; the session binds the whole set with `bindGameRules`). `MawSkillRules`: shared raise cost of weapons, schools and racial abilities (hybrids: magic only), level caps (Alchemy 60, Cover 30, Mana Shield and Retaliation 50), masteries a respec took returning one rank per raise, the ladders of the four new skills, teacher requirement and price by mode and by the masteries held, respec (1000 gold per level, shared-set and triangular refunds, Alchemy kept, the level-up floor) through Oracle, Judge Grey and the Seer (`events/Global_maw.lua`, `content/npc_*`), training-hall caps and 2-day training, continuous Regeneration and Meditation (×2 after 20 s without loss, ×4 with no enemy near; the aura pools), the aura stat percents, Endurance, Bodybuilding and Enlightenment, and the character sheet's combat rows (`MawCharacterSheet`: weapon and Armsmaster damage, attack, AC and resistances from the MAW items and skills). `MawSpellRules`: Ascension costs, delays and heals (Learning shows as Ascension, `skillNames` in `ruleset.yml`; nobody picks it at creation), the Personality factor, buff auras (`MawAuras`: casting holds or releases, the reservation clamps SP, auras drive the party and member buff slots; Hour of Power, Day of Protection, Day of the Gods, Haste, Shield, Bless, Fate, Heroism, Hammerhands, Empower Magic read the holder's skill), crowd control durations with diminishing returns per monster and group (`partyCrowdControlSeconds`, both worlds). The four new skills (ids 44-47, `FirstRulesetSkillId`): caps from MAW's `Class Skillz.txt` (the patch tool now reads it: 503 cells and the four rows), learned at training halls (Cover) and magic shops (Mana Shield, Enlightenment), P and M switch Cover and Mana Shield on the skills page; Cover moves single-target monster attacks to the member with the most HP among those whose roll succeeds (alone: halves the hit), Mana Shield spends SP on every hit, Retaliation stores stacks on covers and spends them on the next melee hit (damage by power and vitality, paralysis, faster recovery). A table may now have several ruleset contributions, applied in order; the patch tool keeps the hand-written ones in `content/`. SaveVersion 100 (remembered masteries, switches, aura holders). Tests: `MawSkillTests.cpp` (shared cost, teachers, the respec worked example, training, ladders and caps, Cover and Mana Shield), `MawSpellTests.cpp` (the Fire Bolt Ascension example, heals, the reservation and aura tables, Meditation and Regeneration auras, the CC table and both DR simulations). DEVIATIONS 18-22. Kept as MAW plays (user's call, 2026-10-23): the live `buffPower` base 20 of the resistance auras and Day of Protection (CLASSES_SPELLS_SPEC's tables use 10), Empower Magic on Haste's numbers, Dragon Fear's flat 4 s. **Left:** scroll, temple and pedestal buffs as fixed-caster auras; potions competing with auras; Vampiric Aura and Immolation effects and leech; Staff's party-wide resistance; the free → horizontal mastery stripping; solo utility masteries; the respec's Austerity rule; legendary affixes 20, 25 and 32 and the item-power scaling of the school and Meditation specials; the SP formula and class terms (phase 6); the skill tooltips' live numbers (TRAINERS_SKILLS.md §7) |
| 6 Classes and races | done (2026-10-23), see the notes for what is left | `ClassRules` (`game/rules/`, in `GameRules`): base HP and SP, class bonuses after items, spell books, and a per-frame update. Tables: the 12 new classes (ids 53-64, `CanonicalClassNames`) come from the patch tool, which now reads MAW's `Class Skillz.txt` (new class columns through the new `appendColumns` contribution; its Supreme reads as Grandmaster) and appends class rows; `content/` adds their starting skills and descriptions (shown by right-clicking the class at creation) and MAW's free selection (`character_selection.yml`: any unpromoted class for any portrait). `MawClassRules`: HP and SP from MAW's stat effects (Personality adds to every class's mana), fixed pools for Death Knights, Dragons and Assassins, cross-world promotions (`data/promotions.yml`: the first world promotes to the final step, picked once per character; MAW's own kinds take the mid step; two and three worlds give Elder and Ultimate per-level gains), race skill bonuses (+3 and +1 per 10), resistances and immunities, the race limits of `Race Skillz.txt` (`content/race_skills.yml`, new `max_mastery` and `shift_without_class_cap`), Supreme Armsmaster's weapon bonus, vampires' night Preservation. Class perks: flat melee damage the Armsmaster way, melee multipliers and attack speed (Seraphim, Shaman, Death Knight, Assassin), class cuts and the flat reduction on hits taken, on-hit heals and SP (Seraphim Body, Shaman Mind and Body, Death Knight SP and Blood Leech), Shaman Fire and Assassin Poisons elemental adds, Divine Protection, leech (items, Vampiric aura, vampires, Death Knights, dragons' Regeneration), the wield rules (`ItemRules::wield`: Seraphim two-handed swords in one hand, no sword in the off hand; Dwarf and Minotaur axes). Class spells (`MawClassSpells`): Death Knights and Assassins know theirs by school mastery under their own names (spells and schools), at fixed costs and their weapon's pace, dealing a share of a weapon blow; Blood Leech and Death Grasp are switches; Assassins' energy, combo points and Subtlety stacks; Elementalists learn the elements by casting and build stacks; Shaman and Elementalist Ascension; dragons' fangs, breath and scales, SP refills, Flame Blast. SaveVersion 101 (switches, Elementalist progress). Tests: `MawClassTests.cpp`, `RulesetTests.cpp` (column appends, the composed class tables). DEVIATIONS 23-29. **Left:** Knight Charge (solo E key: a dash of 500-3000 units to the target and 3-5 s of paralysis, 25 s cooldown; needs a party dash in both worlds and a free key, E is Use); the Assassin's crowd cut and the lost Assassination bonus without energy; Assassin Lightning Bolt chaining and Mass Distortion's second Earth division; dragons' items x3 and knockback; Elder and Ultimate class names; the Lich reset migration; class icons of their own (done 2026-10-25, GAPS L6.7) |
| 7 Alchemy and crafting | done (2026-10-23), see the notes for what is left | Potions: `engine/rulesets/maw/content/potion_effects.yml` replaces the Standard file (power cap 500, 6 h plus 6 min per Alchemy point of the best Grandmaster, drink recovery 60 near monsters paid by the drinker or the next ready member, power requirements, five-drink bottles in `currentCharges`, timed immunities, aura potions per drinker that compete with the party aura (`MawRules::memberAura`, flat values in `addPotionAuraFlats`, Preservation and Magic Protection in `MawSpellRules::updateAuras`), Meditation skill bonus, Regeneration potion, best-step black potions, set age, pool-share heals by `PotionRules::estimatedPool`). Reagent power by item level and mastery (`MawPotionRules::reagentPower`, top reagents 30/45 in `content/items_patch.txt`); the Alchemy tab knows every recipe of the matrix and shows drinks and power requirements. Crafting: `CraftingRules` in `GameRules` (Standard none), `MawCraftingRules` with all eleven operations and the five item-target potions, seeded per item (`craftSeed`/`craftCount`, domain CraftApply), `engine/rulesets/maw/data/crafting.yml` (`MawCraftingData`), item rows 1041-1070 in `content/items_patch.txt`. `CraftingRuntime` (party targets and materials, plans, batches with cheapest gems, apply with worn write-back via `Party::replaceEquippedItem`, gem merges). Workbench: the alchemy bench with Alchemy and Crafting tabs (`GameplayCraftingBench{View,Renderer}`, `GameplayCraftingBenchInputController`, `GameplayBenchPainter`), right-click with a material on a pack item opens it filled. Sources: kill drops with bad-luck counters (`MawGameState::craftingPity`, SaveVersion 103), Endless Potions and reagents by the party's Alchemy, magic shops and alchemists (`ItemRules::adjustShopStock`), a Crafting Cube and two gems on map completion. Icons: 30 masters in `level_generation/ui/maw_crafting_icons_20261023/` (runtime sizes in `runtime_x2/`), approved and installed as `engine/icons_x2/maw_craft_*.png`. Tests: `MawPotionTests.cpp`, `MawCraftingTests.cpp`, save round trips in `RulesetTests.cpp`. DEVIATIONS 30-43. **Left:** the hero panel does not show potion auras; the materials routing setting and K pull; open-from-drop on worn items (only pack items; worn ones are in the list); keyboard shortcuts of the design (§7); the effect-at-power preview in the Alchemy tab; the solo G/V hotkeys (not ported by design) |
| Smoke test | done (2026-10-23) | Headless MAW scenarios in `tests/scenarios/rulesets/`: new game, combat outdoors and indoors, loot, difficulty change, the new classes (`maw_classes`), potions (`maw_potions`), crafting (`maw_crafting`), map completion reward (`maw_map_completion`), and MM7/MM8 worlds (`maw_mm7_smoke`, `maw_mm8_smoke`), each through save and load. New scenario steps `grant_item`, `use_item`, `craft`, `combine_gems`, `damage_actor.skip_dead`; ruleset asserts `crafted_items_min`, `potion_effects_min/max`, `member_classes`; `inventory_any_member` takes `count` and `min_count`. `advance_game_time` now runs the party's timers as the game's own time skips do. |
| Tooltip audit | done (2026-10-23), see the notes for what is left | Every rules-dependent number the UI shows was checked in both rulesets. Fixed through hooks: the spellbook tooltip (cost the caster pays, class spell and school names), the Quick Reference level and quick spell, the skill popup title, the recovery time, Identify Monster (`SkillRules::identifyMonsterReveal`: MAW's party rule against the actor's level), monster resistances (`MonsterRules::monsterResistanceText`: MAW has no immunities), held auras (`SpellRules::heldBuffText`: "Held by Name" instead of a timer). The Load and Save screens filter saves by ruleset. Spell texts: `engine/rulesets/maw/data/texts.yml` (`MawTextData`, `SpellRules::spellTooltip`) gives MAW's names and descriptions with the caster's numbers (ascended dice, heals, control seconds, aura strengths, Death Knight and Assassin shares), and the rules add the aura's reservation and holder, combo points and recovery time; Death Knights, Elementalists and Assassins are told they cannot learn from books. Cleanup pass (2026-10-23): Mass Distortion takes MAW's share of the target's hit points (`CombatRules::spellDamageOnTarget`), Chain Lightning leaps (`CombatRules::spellChainMastery`, DEVIATIONS 44), Vampiric Aura and Fire Aura show as member buffs, Empower Magic and Meditation in every member's buff popup (`SpellRules::heldAurasWithoutBuffSlot`), Fire Aura burns on melee blows (`mawFireAuraDamage`, `mawBolsterAmount`), a refused quick spell attacks instead, `damage_actor: {all: true}` clears a map in scenarios. Merchant: MAW's party-wide value prices every house deal (`ItemRules::merchantValue`, DEVIATIONS 45). Texts: `engine/rulesets/maw/data/texts.yml` (`MawTextData`, was spell_text.yml) also holds the skill popups (`SkillRules::skillTooltip`: weapon and armour rows, Regeneration and Meditation now and next, Ascension, Cover, Mana Shield, ladders, the class schools of Death Knights, Assassins, Shamans, Seraphim and Elementalists) and the stat popups (`SkillRules::statTooltip`: damage bonuses, crits, haste, avoidance, hit chance, armour and resistance cuts, regeneration, banked levels, against the party's total level); teachers speak MAW's requirement and price (`SkillRules::teacherSpeech`). Scenarios gained `ruleset_banks` and `grant_item` `equip`/`roll_level`. Popups colour live values as MAW does: HUD text reads Might and Magic's inline colour codes (`\f` and five digits of an R5G6B5 colour, `GameplayHudCommon`), which texts.yml writes as `<good>`, `<bad>`, `<value>`, `<mana>` and `</>`. MAW's weapon enchantment damage and Fire Aura on arrows and spells were found here and ported in the gameplay-gaps pass. Dragons' Fangs and Scales are named and explained. **Left:** the per-item armour numbers of the armour skill popups; the reserved SP of auras is not shown |
| Gameplay gaps | done (2026-10-24), see the notes for what is left | MAW's weapon enchantment damage (`calcEnchantDamage`): the elemental specials 4-15, 39 (spells) and 46 (weapons) roll a range set by the weapon's level damage (`MawBalanceModel::weaponLevelDamage`, `mawEnchantDamageRange`, `mawDamageEnchant`), x 1.5 with Legendary 19, at the hands' base pace; melee blows add each hand's enchantment and Fire Aura by element and drop the table's flat enchantment damage (`CharacterAttackResult::rulesWeaponElements`); arrows and blaster shots add the bow slot's to their range (DEVIATIONS 46); damage spells add every slot's at 1.015^Ascension, 40 % on area spells; Death Knight and Assassin class spells add both hands' average. Fire Aura follows the current MAW formula (a share of the weapon's level damage with a floor, `mawFireAuraDamage`). Item popups show the rolled range. Mace (15 %) and Staff (10 %) paralyse from Master for 2 s, 4 s at Grandmaster, instead of Standard's stuns, through Paralyze's diminishing returns, now shared by spells and blows (`MawRules::diminishedCrowdControlSeconds`, `mapActorKey`). Shrinking Ray and Dark Grasp cut a monster's MAW damage by 30 % (`CharacterDamageHit::attackerDebuffed`). Protection from Magic keeps members conscious against monster attacks (`CombatRules::blocksMonsterCondition`). Death Knights: Icy Touch slows from Frost Expert and Death Grasp spends 15 SP a melee hit to hold the target in Dark Grasp for 2 s (`IGameplayWorldRuntime::debuffActor`, DEVIATIONS 47); the attack switches are one at a time. Elementalists: the quick and attack spells rotate within the kind of the bound spell (single target, shotgun, area by world), R on the skills page switches it and its stacks off (SaveVersion 104, DEVIATIONS 26). The portraits show an Assassin's combo points and an Elementalist's stacks (`ClassRules::portraitCounter`, `ObsidianPc*Counter`). Tests: `MawSpellTests.cpp`, `MawClassTests.cpp`, `MawSkillTests.cpp`. **Left:** Knight Charge (phase 6 notes); Legendary 26's enchantment and aura crits; the viewer's Legendary 19 in the popup range |
| 8 Content | done (2026-10-24), see the notes for what is left | Ruleset map content loads after the world's, in MAW games only: `engine/rulesets/maw/events/maps/<map>_maw.lua` (Lua overlays) and `engine/rulesets/maw/maps/<map>_zz_maw.scene.yml` (scene overlays: entities and spawns without an index append, `removals.entities`/`removals.spawns` by position, `initial_state.actor_overrides`; `SceneOverlayOperations`). Event ids: MAW map events 60001+, global topics 10010-10040 (respec 10010/10011, Druid Circlet 10020, dragon release 10021/10022, Endless Arena 10030/10031, Dimensional Maps 10040), NPC enter hook 65310, QBits 10001+. Content: teleporters in New Sorpigal, Ravenshore and Harmondale; stat shrines in any month; the Bootleg Bay well; the znwc gate; the edited maps' monsters and faces (elemf, out05, d04, d08, d12, d18, 7d12, 7d33, 7d37, d42); ambushes and scripted spawns (7out02, 7d06, 7d21, 7d24, 7d29, 7d37, 7out05) through `evt.SummonMonstersById` (`GameplayMonsterSpawn`, `spawnMonsters` in both worlds); the quest changes of MAPS_CONTENT.md §4 (potion quests from every world's reagents, Galvinus, Rust, circus caps, Druid Circlet, hatchling); the Hall under the Hill's monsters (`content/map_stats_patch.txt`). Systems (MonsterRules hooks, Standard does nothing): event experience and quest gold scaling, never-refilling outdoor maps (`mapRespawnDays`), dungeon reset at the entrance (`mapResetOffer`/`resetMap`, dialog action Reset), Nightmare revival (`leaveMap`, `reviveSlainMonsters`, `ActorRulesetFacts::risen`, SaveVersion 105), the map progress bar in the party frame (`mapProgress`, DEVIATIONS 180; formerly a minimap plate), the Endless Arena (`arenaWaveMonster`, d42 levels and +20 enchant tier), bounty hunts (reward, refusal, boss target with kin), boss badges beside the floating health bar (`actorBadges`, `engine/icons_x2/maw_boss_*.png`). Dimension maps: `engine/rulesets/maw/data/dimension_maps.yml` (`MawDimensionData`), item 290 fields in `ItemRulesetFields` and runs, the quest and the drop counter in `MawGameState` (SaveVersion 106); using a map (`ItemRules::useTravelItem`) starts a run that refills the target (`mapRefillForced`/`mapLoaded`) with three random families (`MonsterRules::enterMap`, before the asset load), denser groups, levels power x 10 + 20 without party bolster, and 31 of the 33 affixes; kill drops with bad-luck protection, the next map on clearing, Workbench crafting on maps (Eye, Hourglass, Emerald, Crafting Cube), the Dimensional Maps topic (`MonsterRules::rulesTopic`, `evt.RulesTopic`). Tests: `MawDimensionMapTests.cpp`; scenarios `maw_content`, `maw_quests`, `maw_map_scripts`, `maw_nightmare_revival`, `maw_endless_arena`, `maw_bounty`, `maw_dimension_maps`. DEVIATIONS 48-63. **Left:** Knight Charge (48), used barrels (57), dimension affixes 25 and 33 (60), Doom-mode content and Beyond Madness's dimension rules (phase 9), Saving Goobers (no base quest) |
| Gap pass | done (2026-10-24), see GAPS.md for what is left | Three sessions worked through [GAPS.md](GAPS.md) (briefs in `parallel/`): its rows carry what was built, tested and decided (§11), and the new deviations are in DEVIATIONS.md. Save versions 107-111. Tests: `MawGapTests.cpp`, `MawSpecExampleTests.cpp` (the spec's worked examples through the real code), the 22 ruleset scenarios. |
| 9 Challenge modes | done (2026-10-24) | [PHASE9_SCOPE.md](PHASE9_SCOPE.md): every P9 row, decisions Q1-Q8 and what each session built. Doom, Road to Insanity, Beyond Madness and Austerity are offered; the Doom modes play at Nightmare; new-game setups (`ExperienceRules::prepareNewParty`); Beyond Madness's death ledger (`MawMadnessLedger`); save version 113. The randomizer is not ported (DEVIATIONS 138, its author's call). Tests: `MawChallengeModeTests.cpp`, `MawMadnessLedgerTests.cpp`, the P9 cases in `MawGapTests.cpp` and `MawSpellClassTests.cpp`, the balance check in `MawBalanceModelTests.cpp`, scenarios `maw_challenge_modes`, `maw_madness_ledger`, `maw_doom_items`, `maw_doom_content`, `maw_knight_charge` |
| Audit and follow-ups | done (2026-10-25), see §0 | The 2026-10-24 audit's P1, P2 and assigned P3 rows, the ruleset move into the engine package, the combat log, four bags with tags, bounty presentation, extra quick spells, the Progress tab, the loot filter presets, potion quick-slots and the approved Standard changes (§0.3). Save versions 115-126 |

## 7. Prompt for the next session

> Read `devdocs/maw/HANDOFF.md` §0 first, then §1-§3, and follow them. Phases 1-9, the gap pass, the 2026-10-24
> audit and the follow-up interface work are done and uncommitted; never touch git's index or history. Finish what
> §0.4 lists as in flight, ask the user the questions in §0.5, then work through §0.5's open rows and fix what the
> user finds in play. Keep §0, GAPS.md and DEVIATIONS.md current.
