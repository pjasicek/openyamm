# ROB — robustness of the MAW implementation (second pass)

Scope: `game/rules/maw/*`, `game/rules/*`, `game/content/Ruleset*`, the MAW save code in `game/maps/SaveGame.cpp`, the
session lifecycle in `game/app/GameSession.cpp`, and the call sites they reach (world runtimes, Party, mercenaries,
scenario driver). Read-only; nothing was built or run. Line numbers are from the working tree on 2026-10-24 (it is
changing under other sessions).

No P1 found: the save/load of every MAW field round-trips, version gates match the writers, and all MAW state is
rebuilt on load and new game (the session recreates `MawRules` in `setRuleset`). What follows is mostly lifecycle
edges, unbounded growth and per-frame cost.

### ROB-2-1: Characters hit a hard level cap at 1063; DEVIATIONS 9 says the requirement is unclamped
Severity: P3 (P2 for Beyond Madness / dimension-map endgame players)
Confidence: confirmed (arithmetic over the curve in `MawExperienceCurve.cpp`)
MAW: training is free from level 863 because MAW clamps the requirement below 2^31 (DEVIATIONS 9, BALANCE_MODEL
§10.2), so levels keep rising.
OpenYAMM: `MawExperienceRules.cpp:51-55` returns the 64-bit requirement, but `Character::experience` is `uint32_t`
(`Party.h:94`) and every gain is clamped to `OeMaxCharacterExperience = 4000000000` (`Party.cpp:67`, `3144-3158`).
`mawExperienceForLevel(1064)` > 4.0e9 (level 863 is the 2^31 point), so no character can train past 1063, and
every kill, map-completion and quest experience after the cap is silently lost (`grantKillExperience` still banks
it for monster levels). DEVIATIONS 9's "Not clamped (64-bit requirement)" therefore does not describe what players
get: MAW = unlimited levels, ours = stop at 1063.
Not covered by: DEVIATIONS 9 (describes the requirement, not the storage cap); no GAPS row.
Suggested fix: widen `Character::experience` to 64 bits (save migration), or cap the requirement at the storage cap
so training past it is free as in MAW; update DEVIATIONS 9 either way.

### ROB-2-2: Chest, ground and event loot use the drop level of the last map whose monsters were resolved
Severity: P3
Confidence: confirmed (read both paths)
MAW: `MawMapDropLevel` / `staticMapDropLevel` read the current map.
OpenYAMM: `MawRules::mapDropLevel` (`MawRules.cpp:309-357`) reads `m_monsterLevels`, a cache filled only by
`monsterLevels()` during a monster resolve, and its fallback formula uses `m_monsterLevels.mapFileName`, not
`m_currentMap`. Map restores re-resolve only living actors with facts (`OutdoorWorldRuntime.cpp:17184-17193` via
`8539`, `IndoorWorldRuntime.cpp:15514-15527` via `18886`). So:
- re-entering a cleared dungeon from its in-session snapshot (no living monsters) keeps the previous map's levels:
  chests opened there roll at the previous map's median level;
- after loading a save on such a map, the fresh `MawRules` has an empty cache: `mapFileName` is "", so the band is
  zero and the continent resolves to "other" (`continentIndex(0)` = 3), giving a drop level from the wrong bank.
`rollEnchantments` uses it whenever the request has no `dropLevel` (`MawItemRules.cpp:961-963`): chests, ground
items, event `GiveItem` randoms.
Not covered by: MON (map drop level reads all tiers, GAPS A2.9) is a different defect; no related row.
Suggested fix: resolve the levels of `m_currentMap` on demand in `mapDropLevel` (keep a `MonsterTable` pointer as
for the map table), or prime the cache in `enterMap`/`mapLoaded` and key the fallback by `m_currentMap`.

### ROB-2-3: The alchemist preference stays on the slot when a member is dismissed or disintegrated
Severity: P3
Confidence: confirmed
MAW: `vars.alchemyPlayer` (index) — MAW has the same index-based value, but our code remaps the other slot-keyed
state on dismissal.
OpenYAMM: `MawGameState::alchemistMember` is a slot index (`MawGameState.h:96`, used at `MawItemRules.cpp:2154-2179`).
`Party::dismissMemberToAdventurersInn` (`Party.cpp:4080`) calls `MawSpellRules::memberLeaving`
(`MawSpellRules.cpp:768-799`), which remaps aura holders and class runtime but not `alchemistMember`. Dismissing an
earlier member (inn, or Road to Insanity's disintegration at `MawCombatRules.cpp:2533-2541`) hands the preference to
the next character; dismissing the chosen one hands it to whoever moves into the slot.
Not covered by: no row (CLS-11 / SKL "timers by slot" cover other slot-keyed state).
Suggested fix: in `memberLeaving`, clear `alchemistMember` when it equals the index and decrement it when greater.

### ROB-2-4: Regenerating-boss tracks survive map changes (world identity checked by address)
Severity: P3
Confidence: plausible (depends on the allocator reusing the address, which is the usual case)
MAW: map variables are per map.
OpenYAMM: `MawMonsterRules::updateMonsters` clears `m_bossTracks` only when `&world != m_pTrackedWorld`
(`MawMonsterRules.cpp:1544-1550`). The outdoor runtime is destroyed and re-created with `std::make_unique` on every
map load (`GameApplication.cpp:9385`, `7968`) and the indoor one lives in a re-created scene runtime, so the new
runtime very likely has the old address and the tracks (keyed by `actorId`, which restarts per map) carry over. A
Regenerating boss on the next map whose `actorId` matches one hit on the previous map starts with `hits > 0` and
heals without being hit; `lastHp` from the old actor can also count a phantom hit. `m_pTrackedWorld` is also a
dangling pointer between maps.
Not covered by: no row.
Suggested fix: reset `m_bossTracks` (and the second counters) on `m_rules.currentMap()` change, as `m_hatchingBosses`
already does at 1558-1562, and drop the pointer comparison.

### ROB-2-5: Per-frame cost of the MAW updates: up to five full actor scans and container rebuilds every frame
Severity: P3 (performance)
Confidence: confirmed (call chain read; not profiled)
OpenYAMM: `GameSession.cpp:1049-1057` runs, every unpaused frame:
- `MawMonsterRules::updateMonsters`: two loops over all actors through `actorRuntimeState`
  (`MawMonsterRules.cpp:1580-1605`, `1689-1740`), plus `partyHasYellowAlert` (another full scan,
  `PartyHostileAlert.cpp:36-40`) in Beyond Madness (`1538-1542`).
- `MawCombatRules::updateCombat`: a third full scan for `nearbyMonsters` (`MawCombatRules.cpp:2409-2420`), plus
  `partyHasRedAlert` in the Insanity modes while invisible (`2486-2490`).
`actorRuntimeState` is the presentation query (sprite attack timing, shield view, behaviour presentation,
`OutdoorWorldRuntime.cpp:15347-15408`), not a cheap position/HP read. `MawSpellRules::updateAuras`
(`MawSpellRules.cpp:1063-1395`) is not throttled: each frame it builds an `unordered_map` of sources, two
`std::map` slot tables, a `std::map` copy per member, two vectors, a `std::string` per held aura
(`mawSpellSchoolSkill`), scans every member's potion effects and items (`mawStaffPartyResistance`). The HUD's
`mapProgressText` (`MawMonsterRules.cpp:1035-1105`, called from `GameplayUiRenderer.cpp:1168`) builds an
`ostringstream` and lowercase copies every frame. Fine at 50 actors; noticeable on large outdoor maps (300-500
actors) on Android.
Not covered by: STD3-4 (per-projectile-hit rebuild) is a different path.
Suggested fix: one pass per frame with a light accessor (position, hp, hostility, facts) shared by the three users;
run `updateAuras` on the 0.5 s aura tick or when holders/party change; cache the progress text per kill count.

### ROB-2-6: The balance model's caches grow without bound with fractional levels
Severity: P3 (memory)
Confidence: confirmed
OpenYAMM: `MawBalanceModel::stat/gearedFraction/health` memoise in `unordered_map<double, double>` keyed by the exact
level (`MawBalanceModel.cpp:533-595`), never pruned during a session. Callers pass continuously changing fractional
levels: `mawMemberKillExperience` uses `mawLevelForExperience(member.experience)` (`MawExperienceRules.cpp:126-131`;
new value after every kill, for each member), trap damage uses `totalLevel()` (`MawCombatRules.cpp:2011`), the monster
inspect hover reuses the kill formula (`MawMonsterInspect.cpp:174-179`). Each kill adds up to three cache nodes per
receiving member per party size model; a long session accumulates tens of thousands of nodes.
Not covered by: no row.
Suggested fix: cache only integer levels (or round the key), or compute fractional levels without the cache.

### ROB-2-7: Tavern mercenaries' gear moves the Celestial/Legendary/Primordial bad-luck counters (extends SKL / GAPS H.8)
Severity: P3
Confidence: confirmed (call chain)
OpenYAMM: MAW offers mercenaries outside Beyond Madness (`MawClassRules.cpp:818-821`). On the first visit of a tavern
map each game month, `refreshMercenaryRecruitmentForCurrentMap` (`MercenaryRecruitmentRuntime.cpp:1202-1250`) generates
every candidate's equipment with `ItemGenerationMode::Generic` (`778-801`) → `ItemGenerator.cpp:252` →
`MawItemRules::rollEnchantments`, whose rarity roll updates `celestialPity/legendaryPity/primordialPity`
(`MawItemRules.cpp:979-983`; only Shop mode is excluded, `MawItemFormulas.cpp:208-240`). Gear the player never hires
or sees advances, or resets, the loot pity counters on map entry.
Not covered by: SKL (mercenary gear keeps rarity, GAPS H.8) is about the item fields, not the shared counters.
Suggested fix: generate mercenary gear in a mode that leaves the pity counters alone (as Shop does), or give it a
throwaway pity.

### ROB-2-8: MAW scenarios are not reproducible: the scenario driver seeds the streams from system entropy
Severity: P3 (test infrastructure)
Confidence: confirmed
OpenYAMM: `ScenarioRuntimeDriver.cpp:470-475` calls `session.setRandomRootSeed(freshRandomRootSeed())`. Under MAW the
root seed decides bosses and their affixes (`MawMonsterRules.cpp:633-818`), Doom special attacks, corpse loot and
crafting drops, dimension maps and the dimension-quest map, so a ruleset scenario can pass or fail by chance.
Not covered by: no row.
Suggested fix: derive the root seed from the scenario (a fixed default, optionally a `random_root_seed` key).

### ROB-2-9: Two dimension streams can share a key
Severity: P3 (statistical, minor)
Confidence: confirmed
OpenYAMM: the Dimension domain is keyed differently by several users with the same map name key: completing a run
(`MawExperienceRules.cpp:295-296`: map, `mapsDropped`, `power`), BecomeBoss (`MawMonsterRules.cpp:674-676`: map,
resets, 19) and HigherTier (`1358-1359`: map, spawn seed, 17). A run of power 19 completed with `mapsDropped` equal
to the reset count (usually both 0) draws the same numbers as that map's BecomeBoss roll, so the next map's slots
correlate with which monsters became bosses.
Not covered by: no row.
Suggested fix: give each use its own `RandomDomain` value (the enum allows new values without renumbering).

### ROB-2-10: `mawFillText` throws on a malformed placeholder at render time
Severity: P3 (latent; data authoring)
Confidence: confirmed
OpenYAMM: `MawTexts.cpp:320-333` calls `std::stoi`/`std::stod` on `{name:N}` / `{name*F}` tokens from `texts.yml`
while drawing a tooltip; a typo such as `{x:}` throws an uncaught exception during the UI frame. The loader
(`MawTexts.cpp` `loadFromYaml`) does not validate tokens.
Not covered by: no row.
Suggested fix: validate tokens when `texts.yml` loads (reject the file), or parse with `std::from_chars` and ignore
bad tokens.

## Notes, no finding
- The madness ledger: `GameSession::restoreFromSaveData` creates `MawRules` in `setRuleset` with the previous
  session's root seed (`GameSession.cpp:361`) before the save's seed is set (`1809`), so `loadRun` runs on the old
  run first. Traced every case (same run, other run, from the main menu after `clear()`): the outcome matches the
  documented rule ("a run still pending when a save is loaded counts a death"); `startRun` is never called (dead
  code, harmless: `loadRun` of a new seed reads an empty entry).
- `MawDimensionData` load rejects empty family lists (`MawDimensionMaps.cpp:145`), so
  `families[stream.uniform(0, size - 1)]` in `useTravelItem` (`MawItemRules.cpp:2025-2028`) cannot underflow.
- `rewardMapProgress` runs both on each kill and every second (`MawMonsterRules.cpp:1609-1627`); the
  `completedMaps`/`run.completed` checks prevent a double reward.

## Checked and matching (enumeration with outcome)

**Saved state, writer vs reader order and version gates** (`SaveGame.cpp`):
- `MawGameState` (all 22 members: continent banks, banked experience/level, reset counts, completed maps, four loot
  pities, artifact and legendary drop counts, aura holders, crafting pity, dimension runs, the six quest fields, map
  drop pity, maps dropped, sold uniques, fixed aura maps, alchemist, held food, Broodlord/Omnipotent pity): written
  827-857, read 859-892 in the same order, each new block gated by its version (98-113). OK.
- `CharacterRulesetState` (583-721): order matches; gates 100/101/102/104/107/110/111. Lives in `Character`, so it
  follows the character through dismiss, inn, hire, death and the save. OK.
- `ItemRulesetFields` (723-748, 894-921): carried by `InventoryItem`, `EquippedItemRuntimeState` (1119-1133), chest
  and corpse item states (3628-3654), outdoor world items, held cursor item, house stock. Indoor ground items are
  ITM-1 (known). OK otherwise.
- `ActorRulesetFacts` (750-805): outdoor and indoor actors (2861, 3470); gates 105/107/108/113. OK.
- `RulesetSelection` and root seed (4230-4317): options validated (`rulesetOptionsValid`); pre-stream saves get a
  fresh seed. OK.
- Current save version 113 (HEAD 94): 95-112 never shipped.

**Lifecycle** (new game, load, Standard switch, party changes):
- New game and load both run `GameSession::clear()`/`setRuleset`, which destroys and rebuilds `MawRules`: every
  runtime member (`m_classRuntime`, crowd-control history, caches, per-rules `mutable` state in
  MawCombat/Class/Skill/Spell/Monster/ItemRules) starts empty. OK.
- Standard game after MAW: `m_pMawRules` reset, party rules rebound, ruleset data and NPC extra houses reset in
  `GameDataLoader::loadRulesetData` (3914-4012); skill display overrides reset per activation (1522). Text data is
  STD3-5 (known).
- MAW data loading is all-or-nothing (3914-4012); `createMawRules` returns null only without map levels. OK.
- Aura holders on dismissal: remapped in `memberLeaving` (768-799); holders past the party size are dropped in
  `updateAuras` (1104-1108); fixed auras keyed by map, first update after a load does not end them (1070-1088). OK.
- Class runtime by address (CLS-11), cover/retaliation by address (CMB), regeneration timers by slot (SKL): known.
  `m_dragonRefills` (`MawClassRules.cpp:445`) is slot-keyed the same way (same class as the SKL item).
- Horizontal progression switch: `m_horizontalApplied` starts unset after a load, so the first update does not
  re-store masteries (`MawSkillRules.cpp:1063-1104`). OK.
- Unstuck and artifact timers handle a game clock that went back (`MawRules.cpp:463-481`,
  `MawCombatRules.cpp:2235-2262`). OK.
- Hatching bosses, food cap, flight-map announcement and bounty level reset per map name. OK.
- Potion effect timers tick with the engine buffs (`Party.cpp:6336-6346`). OK.
- Forced refills and refill seeds are runtime-only but are consumed on the same map load as the reset. OK.

**Crashes / undefined behaviour**:
- Member index: `applyPartyHitEffects` returns on an invalid member (2662-2669), so the later
  `*party.member(hit.memberIndex)` derefs are safe; artifact casts re-check the index (2213). OK.
- Table pointers: every `spellTable()/itemTable()/mapTable()` use is null-checked or behind a checked caller. OK.
- Array indexes: `Schools[specialId - 26]` (26-34 checked), `elementalProgress[(spellId - 1) / 11]` (1-44 checked),
  `TierDamageMultipliers[tier]` (0-3), dimension affixes (validated at load). OK.
- Integer ranges: monster HP peaks at about 4.3e7 at level 2000 in `balance_golden.csv` (×5 boss stays below 2^31);
  kill experience, map-completion gold/experience, quest gold bonus, bounty reward, item power (`PowerHardCap`) and
  drop level (clamped 2047) stay in range; `addExperienceToMember` clamps; `eventExperience` clamps to int32. The
  negative potion-aura skill cast is SPL-17 (known).
- Divisions: party counts use `max(1, size)`; leech references use `max(1.0, ...)`; Cycle of Life counts from 1. OK.

**RNG and determinism**:
- Named streams (`RandomStreams.cpp`) keyed by root seed, map name, visit seed and actor index: corpse loot, crafting
  drops, dimension drops, boss selection/stats/affix, Doom specials. Corpse loot is rolled at death in actor order
  (`rollPendingCorpseLoot`), not on hover; Telepathy is the known ALC item.
- Shop stock does not touch the rarity pity (`mawRollRarity` with `shop`). OK.
- Tooltips that compute MAW numbers draw no randomness: monster inspect (`MawMonsterInspect.cpp`), item comparison
  (`MawItemRules.cpp:2240-2310`, cached), skill and stat texts. OK.
- Combat randomness uses `thread_local` engines on purpose (RANDOMS.md §7.2). OK.
