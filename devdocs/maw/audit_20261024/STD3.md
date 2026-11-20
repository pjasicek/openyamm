# STD3 — Standard (MMMerge) regressions: world runtimes, actors, events, map loading, save/load, data loading, lifecycle

Baseline: git HEAD `7fdb25667` (SaveVersion 94 at HEAD, not 95). All findings read on both sides unless marked
plausible. Unit tests were not run (other sessions were building).

### STD3-1: A cross-ruleset load that fails after the ruleset switch destroys the game in progress
Severity: P2
Confidence: plausible (code read; the end state after the failure needs a runtime check)
MAW: n/a (engine lifecycle)
OpenYAMM: `game/app/GameApplication.cpp:9893` calls `activateRuleset(saveData->ruleset.id)` before
`validateRequiredContentPackages` (`:9903`). When the save's ruleset differs from the loaded one, `activateRuleset`
(`:7573-7580`) tears down first: `clearSharedUiRuntime()`, `shutdownRenderer()` (resets `m_pMapSceneRuntime` and both
world runtimes, `:9359-9361`) and `m_gameSession.clear()` (party, ruleset, MAW state). If validation then fails (a save
needing a world/ruleset package at another schema, an unknown item/house), or the ruleset's tables fail to load (the
fallback at `:7589-7594` reloads Standard and returns false), `quickLoadFromPath` just returns false. At HEAD a failed
validation left the current game untouched. Now a Standard game that tries to load a MAW save which fails validation
(or a MAW game loading a bad Standard save) is left with no session and no scene: F11 keeps playing nothing, and the
in-game Load screen's Cancel goes to `openPauseMenuScreen()` (`:10183`) whose Resume has no runtime behind it.
Same-ruleset loads (Standard to Standard) do not tear down and keep HEAD behaviour.
Not covered by: DEVIATIONS 1-4, GAPS E.1 (packaging); HANDOFF §6 phase 1 (activateRuleset) does not mention it
Suggested fix: run the package/schema validation that does not depend on the ruleset's tables before tearing down; after
any failure that follows a teardown, re-activate the previous ruleset or send the player to the main menu instead of
returning to a session-less gameplay state.

### STD3-2: Indoor monster-on-monster area damage still narrows actor HP to int16 (MAW HP above 32767 wraps)
Severity: P2
Confidence: confirmed (read both sides)
MAW: monster HP is unbounded by design (MAW keeps its own HP ledger because the engine's is 16-bit,
`devdocs/maw/UI_CONTENT.md:41,498`); OpenYAMM widened `MapDeltaActor::hp` to int32 for this (SaveVersion 98).
OpenYAMM: `game/indoor/IndoorWorldRuntime.cpp:7388-7390` (non-party projectile area hit on an actor) still does
`targetActor.hp = static_cast<int16_t>(std::max(0, int(targetActor.hp) - appliedDamage))`. Every other HP write in the
diff dropped the 16-bit cast/clamp. A MAW actor with more than 32767 HP caught in another monster's area missile (a
charmed or hostile-faction monster's fireball, an arena wave) wraps to a negative or small value and dies or loses
most of its health at once. Standard is unaffected (no Standard monster exceeds 30000 HP; `monster_data.txt` max checked).
Not covered by: no related row
Suggested fix: `targetActor.hp = std::max(0, targetActor.hp - appliedDamage);` as in the neighbouring branches.

### STD3-3: Projectile hits that `applyParty…` refuses now report 0 damage in Standard too (miss reaction, no hit line)
Severity: P3
Confidence: confirmed (read both sides)
MAW: friendly-fire refusal (GAPS A1.13) motivated it
OpenYAMM: `game/outdoor/OutdoorWorldRuntime.cpp:14486-14496` and `:~14580` (area hits), `game/indoor/
IndoorWorldRuntime.cpp:7112-7122` and `:7395-7403` set `appliedDamage = 0` whenever the apply call returns false. In
Standard the friendly-fire/deflect checks never refuse, but the call also returns false at HEAD in other cases:
outdoors for an actor that is already dead/invisible (`isActorUnavailableForCombat`, e.g. two missiles of one volley
in one frame), indoors whenever HP did not change (`return actor.hp != previousHp`), i.e. an actor whose
`applyMonsterDamageEventHooks` (scripted boss phases, actor scripting) cancelled the damage. HEAD passed the resolved
damage to `recordPartyProjectileActorImpact`; now 0 reaches `GameplayCombatController.cpp:1601-1641`, so Standard
shows the AttackMiss face and miss speech and no "hits for N" status where HEAD showed a hit.
Not covered by: GAPS A1.13 (done) — the zeroing is not limited to the friendly-fire refusal
Suggested fix: zero the damage only when the rules refused the hit (e.g. return a distinct refusal result, or check
`harmsFriendlyActors()`/`deflectsPartyHit()` at the call site), keeping HEAD's reporting otherwise.

### STD3-4: Every party projectile hit scans all actors for an index that Standard never uses
Severity: P3
Confidence: plausible (cost not measured)
MAW: n/a
OpenYAMM: `game/gameplay/GameplayCombatController.cpp:1663-1687`: for each `PartyProjectileActorImpact` with damage > 0
it loops over `mapActorCount()` calling `actorRuntimeState()` (builds the full runtime state incl. shield view,
`applyPresentation`, attack-impact lookup; `OutdoorWorldRuntime.cpp:15358-15405`) to find `hit.targetActorIndex`, then
calls `applyPartyHitEffects`, which is an empty function in Standard (`CombatRules.cpp`). An area spell hitting many
monsters on a crowded map does hits × actors state builds in one frame, new per-frame work in Standard.
Not covered by: no related row
Suggested fix: carry the actor index in the combat event (the world has it at record time), or look it up only when
the rules need it.

### STD3-5: `loadRulesetData` does not reset the MAW text data on a switch back to Standard
Severity: P3
Confidence: confirmed (read both sides)
MAW: n/a
OpenYAMM: `game/data/GameDataLoader.cpp:3916-3921` resets `m_mawMapLevels`, `m_mawItemData`, `m_mawPromotionData`,
`m_mawCraftingData`, `m_mawDimensionData` and the NPC extra houses, but not `m_mawTextData`; after MAW → Standard,
`GameDataRepository::mawTextData()` still returns MAW's texts although `GameDataRepository.h:111` documents "Null unless the
MAW ruleset is active". Harmless today (only `MawRulesFactory.cpp:20` reads it), but any Standard code that tests it
for "is MAW" would leak. `GameDataRepository::clear()` (`GameDataRepository.cpp:70`) likewise nulls only `m_pMawMapLevels`.
Not covered by: no related row
Suggested fix: add `m_mawTextData.reset();` with the others (and null all six pointers in `GameDataRepository::clear`).

### STD3-6: MM6 `evt.SetTexture` with a negative reference now swaps one facet in Standard (undocumented Standard change)
Severity: P3
Confidence: confirmed (question: intended?)
MAW: n/a (MMMerge semantics: a negative SetTexture reference is "the facet itself")
OpenYAMM: `tools/LegacyLuaExport.cpp:833-843` keeps the sign; the regenerated MM6 scripts (18 files, 228 calls, e.g.
`assets_dev/worlds/mm6/events/maps/6d01.lua:163` `evt.SetTexture(-2011, ...)`; all diffs under `assets_dev/worlds/mm6`
are only this) and `game/events/EventRuntime.cpp:8284-8304` (`indoorFaceTextureOverrideKey`) plus
`MapAssetLoader::loadSurfaceTexture` make those levers/switches in MM6 dungeons swap a single face texture. At HEAD the
same calls targeted cog number 2011 etc. This is a Standard fix (matches MMMerge), but unlike the Dragon Hatchling
change (GAPS N8.5, user-approved) it is not recorded as an approved Standard change anywhere in devdocs/maw.
Not covered by: GAPS N8.5 covers only the `Global_mm7_mmmerge.lua` hatchling edit (also in this diff)
Suggested fix: confirm with the user and record it next to N8.5 (or in the exporter's notes); no code change if intended.

## Checked and matching (Standard behaves as at HEAD)
- Save/load: every new field is version-gated (95 tech points, 96 ruleset, 97 item ruleset fields + root seed,
  98 actor facts / 32-bit actor HP / MawGameState, 99-113 MAW additions); gates only increase along each struct; write
  and read orders match field for field for `CharacterRulesetState`, `ItemRulesetFields`, `ActorRulesetFacts`,
  `MawGameState`, `RulesetSelection`. HEAD-era saves (v≤94) read HP as int16 (`readHitPoints`), get the Standard
  ruleset, empty facts/fields/state and a fresh root seed (unused by Standard). Standard saves add one presence byte per
  item/character/actor, the ruleset id+options, the root seed and an empty optional; no MAW block is written. No
  `requiredContentPackages` entry for Standard.
- Actor stats: `MonsterRules::resolveMonster` is `resolveGameplayMonsterBolster` unchanged (`GameplayBolsterRuntime.cpp`
  untouched), so HP/level/AC/damage/speed/reward multipliers are identical; `calmMoveSpeed` and
  `specialAttackKind` are unset in Standard; `rulesetFacts` stay empty; indoor HP clamp removal is moot (bolster caps
  at 5000, table max < 30000).
- Kill experience (`ExperienceRules::grantKillExperience` = HEAD formula, 0-XP guard kept), corpse loot
  (`MonsterRules::corpseLoot` = HEAD prototype, no seed, free RNG as before), `keepsDeathDrop`/`lootWithoutCorpse`/
  `placedItemId`/`spawnTier`/`chestGoldAmount` make no RNG draws in Standard, so spawn, chest, map-item and death-drop
  RNG sequences are unchanged; bounty spawn point/monster use their own seeded RNGs (reordering is harmless).
- Respawn/refill: `mapRespawnDays` = `map.respawnIntervalDays`, `mapRefillForced` false, `mapLoaded`/`enterMap`/
  `adjustMapEncounters`/`placeMapMonsters`/`leaveMap`/`updateMonsters` no-ops; `refreshRulesetMonsters` skips actors
  with empty facts; arena restore rule unchanged.
- Draw scale (×1.0 exact), display names, badges (empty), map progress (none), save food cost (0), teleport block,
  identify-monster speech (same best member), crowd-control durations (`crowdControlSeconds` nullopt keeps every
  HEAD formula and resistance check), immolation damage, missile homing (turn rate/cone 0), friendly fire (Standard
  harms), event experience (`eventExperience` identity), `evt.DamagePlayer` (`environmentDamage` identity; every
  `const.Damage.*` used by scripts is an integer).
- Per-frame: five no-op virtual rules calls in `GameSession::updateGameplay`; no other new per-frame work in Standard
  besides STD3-4 (the energy-shield/modifier/relations updates are a separate feature and early-out when inactive).
- Data loading: ruleset table overrides, `readRulesetDataFile`, Lua/scene overlays, extra NPC houses, skill display
  names, potion effects file and ruleset package schema are all no-ops/Standard files under the Standard definition.
  Common data reloads only when the ruleset id changes (`activateRuleset` early return), so Standard→Standard loads
  and new games cost nothing extra; a MAW save loaded from a cold main menu loads twice (Standard, then MAW).
- MAW → Standard in one process: every table MAW overrides (character_data, class_*, english/class, place_mon, potion,
  potnotes, quests, skill_des, hostile, house_data, house_rules, items, map_stats, monster_data, npc_topic, npc,
  potion_effects, potion_settings, race_skills, random_items, special_item_enchants, spells, character_selection) is
  reloaded by loaders that clear or rebuild their containers; MawRules, MawGameState (auras, bags, crafting/loot pity,
  dimension runs), bound rules pointer and party rules are reset by `GameSession::clear/setRuleset`; no static/global
  MAW state found other than the skill-name override map (reset by `setActiveRuleset`). Exception: STD3-5. The reverse
  (Standard → MAW) builds MawRules after the MAW reload.
- MAW keys (G, A, P, M, R) do nothing in Standard (gated by `lootGathering`, `pickAlchemist`, `toggleSpellRotation`,
  skills Cover/ManaShield that Standard characters lack); P/M keep their HEAD meaning.
- Event scripts: `event_support.lua` adds only technology-skill tags and `itemType.Amulet` (technology feature); the new
  `evt` functions are used only by `assets_dev/rulesets/maw` scripts. World Lua diffs: MM6 = SetTexture sign
  regeneration (STD3-6); `Global_mm7_mmmerge.lua` hatchling = GAPS N8.5 (approved); `mm7_common.lua` `IsFlying` →
  `isFlying` (both aliases exist, no behaviour change).
- Known approved Standard changes not re-reported: letter attack preferences and spreadsheet numbers in
  `monster_data.txt` (HANDOFF §6 phase 2), house map fixes, spell numbers in `spells.txt`.
