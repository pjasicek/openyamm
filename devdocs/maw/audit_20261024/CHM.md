# CHM audit: challenge modes, ruleset options and preferences, cross-cutting MAW systems

Scope: every MAW read of `vars.Mode`, `vars.insanityMode`, `vars.madnessMode`, `vars.AusterityMode`,
`vars.trueNightmare`, `Game.BolsterAmount`, `GetDifficulty`, `GetDifficultyExtraPower`, `getCCDiffMult`,
`GetMonsterExpMult`, `masteryThresholds` (290 hits, list in `scratchpad/chm_modeflags.txt`), checked against the
OpenYAMM option reads (`RulesetOptions`, `mawModelConfig`, `mawBolsterAmount`, `lootConfig`, every
`challengeMode`/`difficulty` comparison under `game/rules/maw/`), plus new-game setup, option locks, cache
invalidation, save/load, the new-game Rules panel and the pause menu's Rules tab. MAW paths are relative to
`Maw-Mod-MMMerge/Scripts/`.

### CHM-1: Beyond Madness (and Doom's item bonus) skip the recruitable roster characters
Severity: P2
Confidence: confirmed (read both sides)
MAW: General/MenuExtraSettings.lua:278-301 — the Madness reset loops `Party.PlayersArray` (all 50 player records,
including the recruitable roster that MMMerge keeps there; MenuChooseCharacter.lua:237-267 and NPCMercenaries.lua:195
index it by roster id), setting `LevelBase=1`, `Experience=0`, `SkillPoints=0` and every skill 0-38 to 1. Doom's
starting-item bonus (General/zzMaw-Items.lua:4537-4552) also loops `PlayersArray`, so the roster heroes' items get +2/+4
power. A roster hero recruited later in a Madness run joins at level 1 with skills at 1.
OpenYAMM: game/rules/maw/MawExperienceRules.cpp:355-431 (`prepareNewParty`) touches only `party.members()`; roster
heroes are built at join time from `roster.txt` (game/party/Party.cpp:618-644 `buildCharacterFromRosterEntry`, used by
`recruitRosterMember` :3960 and `addAdventurersInnMember` :4006, GameplayDialogController.cpp:1016) with no ruleset hook.
In Beyond Madness a party can recruit Tempus or Ulbrecht at level 50, Brimstone, Infaustus, Rionel or Verish at 30,
with their full skills and masteries — the level-1 start is bypassed. In the Doom modes their items lack the +2/+4.
Not covered by: PHASE9 P9.D1/P9.M1 (party only), DEVIATIONS (no row), GAPS (no row).
Suggested fix: a ruleset hook when a roster character is built (e.g. `ExperienceRules::prepareRosterCharacter`) that
applies the Madness reset (level 1, experience 0, skill points 0, skills to 1 Normal) and the Doom item power to
characters coming from `roster.txt`; not to characters dismissed from the party and re-hired.

### CHM-2: Beyond Madness death ledger marks only monster hits; MAW marks every damage to a member
Severity: P3
Confidence: confirmed (read both sides)
MAW: Modules/MawCore/Damage.lua:1567-1573, 1985-1986 — `pstage_deathSeedMark` is a stage of the `DamageToPlayer`
pipeline (CalcDamageToPlayer), which every hit on a member goes through: monsters, but also traps, falls, burning,
water, event damage (the same pipeline's `damage-recompute` stage handles those, DM:1623-1652). Any of them makes a
load in the next five game minutes count as a death.
OpenYAMM: game/rules/maw/MawCombatRules.cpp:3207-3208 marks only inside `applyMonsterHitEffects`, which
GameplayCombatController.cpp:2057-2066 calls only for hits with a source actor. A trap or a fall followed by an
immediate reload (the save-scum the ledger is there for) is not counted.
Not covered by: PHASE9 P9.M8 (states "a monster hit", which is narrower than MAW's code), DEVIATIONS, GAPS.
Suggested fix: mark in `MawCombatRules::characterDamaged` (Party.cpp:3057 calls it for every hit that lands), or in
`absorbCharacterDamage` to also count fully absorbed hits as MAW does.

### CHM-3: Road to Insanity's held-back food accumulates across dungeons; MAW keeps only the last excess
Severity: P3
Confidence: confirmed (read both sides)
MAW: General/zzMaw-Monsters.lua:2172-2187 — `vars.refundFood = Party.Food - maxFood` overwrites the stored amount, so
going from one dungeon straight into another loses the first dungeon's held food.
OpenYAMM: game/rules/maw/MawMonsterRules.cpp:1517-1525 — `state.heldFood += ...` (the code comment says "MAW
overwrites it"), a deliberate change without a deviation row.
Not covered by: DEVIATIONS (no row), GAPS (no row), PHASE9 P9.I6.
Suggested fix: add a DEVIATIONS row (MAW loses food dungeon-to-dungeon, a bug), or overwrite as MAW does.

### CHM-4: New-game Rules panel keeps the forced Nightmare (and Horizontal) after leaving a Doom-family mode
Severity: P3
Confidence: confirmed (read the code; behaviour visible only on a runtime check)
MAW: General/MenuExtraSettings.lua:239-301 — the mode spinner and the difficulty slider are independent; choosing Normal
mode leaves the difficulty the player set (default MAW, bolster 100).
OpenYAMM: game/ui/screens/NewGameScreen.cpp:2510-2520 — picking Doom/Insanity/Madness sets `draft.difficulty =
Nightmare` (and Madness `progression = Horizontal`); picking None or Austerity afterwards keeps
`value_or(m_rulesDraft.difficulty)`, i.e. Nightmare and Horizontal. Apply accepts it (`offers` allows Nightmare), so a
player who looks at Doom and backs out starts a locked Nightmare game unless they notice the selected row.
Not covered by: DEVIATIONS 2/3 (UI replacement), GAPS.
Suggested fix: remember the difficulty and progression the draft had before a mode forced them and restore them when
the mode no longer forces them (or reset to the ruleset defaults).

### CHM-5: The `--ruleset` debug new game skips the challenge-mode party setup
Severity: P3 (developer path only)
Confidence: confirmed (read the code)
MAW: General/MenuExtraSettings.lua:272-301 — every Doom-family new game gets 5000 gold and 10000/party experience
(Madness also the level-1 reset).
OpenYAMM: game/app/GameApplication.cpp:10395-10440 — the `--ruleset maw:doom` start accepts the challenge mode (and
PHASE9 §6 lists `--ruleset` as a supported Doom entry) but never calls `experience.prepareNewParty`, unlike the normal
new game (:10579) and scenarios (ScenarioRuntimeDriver.cpp:490). A desktop check of a Doom start through `--ruleset`
sees a party without the Doom setup.
Not covered by: PHASE9 §6, GAPS.
Suggested fix: call `party.rules().experience.prepareNewParty(party)` after the party is seeded on that path.

### CHM-6: The loot-filter text describes a different rule than the one implemented
Severity: P3
Confidence: confirmed (read both sides)
MAW: General/zzMaw-Items.lua:930-970 (chest items converted once per map), 1335-1360 (monster drops converted when
generated).
OpenYAMM: the filter applies to corpse loot and chest items when they are rolled (ChestRuntime.cpp:518, 639;
CorpseLootRuntime.cpp:334; DEVIATIONS 17), but both descriptions say "Monster loot of this rarity or lower turns into
its gold value when picked up" (assets_dev/engine/ui/menu/settings_catalog.yml `ruleset_loot_filter`;
NewGameScreen.cpp:2550 and the confirm text at :2560).
Not covered by: DEVIATIONS 17 (records the behaviour, not the text).
Suggested fix: "Loot of this rarity or lower, from monsters and chests, comes as its gold value instead."

## Questions (MAW behaviour, not clearly bugs)

- MAW's Normal difficulty is bolster 50; `mawBolsterAmount` gives Normal 70 (game/rules/maw/MawCombatFormulas.cpp:373),
  consistent with DEVIATIONS 1 (Normal plays index 2, "bolster 70"). The only raw-bolster read where 50 and 70 differ is
  real-time poison (zzMaw-Items.lua:1515: ×0.5 in MAW's Normal, ×0.7 here, MawCombatRules.cpp:2430). Every other raw
  read (`max(b,100)`, `>100`, `>=150`, CC multiplier, enchant-2 cap) is the same for 50 and 70. If DEVIATIONS 1 is meant
  to cover the poison too, a word there would make it explicit.

## Checked and matching

- Mode encoding: spinner 0/2/4/6/8 → `vars.Mode=2` + `insanityMode` + `madnessMode` nesting, Austerity `Mode=8`
  (MES:239-268) ↔ `mawModelConfig` doom/insanity/madness flags and `RulesetChallengeMode`; Survival (`Game.Mode==1`)
  unreachable (MES:243 initialises 0), randomizer scrapped (DEVIATIONS 138).
- Bolster per state (MON:354-399, 2800-2834): Doom family 600 regardless of slider, `trueNightmare` 300 only outside
  Doom, Madness forces horizontal ↔ `mawBolsterAmount` 0/70/100/150/200/300/600, `rulesetChallengeModeDifficulty`,
  `rulesetChallengeModeProgression`, `config.trueNightmare` excludes the Doom family (MAW never sets it there).
- `GetDifficulty` index 1-9 (zzMaw-Stats.lua:1507-1530) ↔ `int(difficulty)+1`, 7/8/9 for the modes (dev 1 for Normal).
- Every MAW `BolsterAmount==300` exact test (which excludes the Doom family) has a counterpart that also excludes it:
  density (MON:833 ↔ `adjustMapEncounters` `!doom`), drop chance ×0.75 vs Doom ×0.5 (IT:243-247 ↔
  MawMonsterRules.cpp:932), completion monsters ×0.67 vs 600 ×0.5, Insanity ×0.8 (MON:2717-2725 ↔
  MawExperienceRules.cpp:185-186). Every `>=300` / `~=300 and Mode~=2` test includes the Doom family: save food cost,
  Lloyd/Town Portal (MON:2141-2204 ↔ `nightmareRules`), revival and the 65 % weakening (MON:2229, 2785 ↔
  `revivalRules`), death/eradication thresholds (DM:1907 ↔ `mawBolsterAmount >= 300`), wear level −6/−3/−3
  (IT:4362-4370 ↔ `levelRequirement`), Hell ranged attack `>=200` (MON:634), Fly cancel `>100 or Austerity`
  (DM:318 ↔ MawCombatRules.cpp:1116), Fly-map message `>100`, bosses `>=100` (MON:2876 ↔ `MawDifficultyIndex`).
- Density table per index and the Doom/Insanity/Madness overlays, including Insanity's floors gated on slot 1
  (MON:771-893 ↔ MawBalanceModel.cpp MonsterDensity, MawMonsterRules.cpp:1387-1447); kill-experience factor
  √(mean3/mean) for every difficulty (MON:793-795 ↔ `monsterExperienceMultiplier`).
- Hits-to-kill, Austerity tables, drop density, rarity difficulty and band multipliers per index (Estimates.lua:192-202,
  459-460, 679-680; IT:603-665 ↔ MawBalanceModel.cpp:280-292, 187; MawItemFormulas.cpp:32).
- `GetDifficultyExtraPower` 1.2/1.1/1.05 (IT:552-560 ↔ `lootConfig`); enchant-2 cap ×1/1.05/1.1/1.2/1.5 by bolster
  (zzAlchemy.lua:833 ↔ MawCraftingRules.cpp:773); `getCCDiffMult` is dead code in MAW (SP:1366-1384 commented out, the
  SP:1635 result unused), so no counterpart is needed.
- Mastery thresholds by mode (S:215-233 ↔ `skillMode`: Doom 6/12/20 even with free progression, Insanity 8/16/25,
  Madness 10/24/40); Cover/Mana Shield ladders (S:176-181, 327 ↔ `mawSkillMasteryLadder`); teacher prices by mode
  (S:1847-1872 ↔ `priceMode`); Supreme 30/50/70; Madness hall cap /10 (S:1662-1674 ↔ `trainingLevelCap`); Insanity
  training price (S:1643-1656 ↔ `trainingPriceMultiplier`).
- Free → horizontal mastery strip and restore (S:1976-2013 ↔ `applyProgressionMasteries`), including Doom-family games
  where the thresholds never change; switch detection survives loads (MawRules is rebuilt by `GameSession::setRuleset`).
- New game: Doom family 5000 gold (set, not added), 10000/party-size experience, +2/+4 item power except 2020; Madness
  level 1, experience 0, skill points 0, skills 0-38 to 1 Normal before the bonus; Austerity no setup
  (MES:247-301, IT:4537-4552 ↔ `prepareNewParty`) — party members only, see CHM-1.
- Option locks: difficulty locked at Nightmare and in the Doom family, Austerity changeable (Q2), progression locked
  only in Madness (Q3), mode and randomizer never (`difficultyLocked`, `applyRulesetOptions`, `offers`,
  MainMenuScreen `settingEnabled`, console `ruleset difficulty`); Nightmare confirmation in the pause menu.
- Cache invalidation on an option change: `MawRules::setOptions` clears the balance models and monster-level cache,
  `GameSession::setRulesetOptions` re-sizes the live actors (MAW re-levels on Action 113 the same way); density applies
  at the next map fill in both. Other mutable caches are mode-independent or keyed by map.
- Save/load: `RulesetSelection` round-trips every option incl. `disintegration` (v113, default on for older saves),
  `MawGameState` saves `heldFood`, `broodlordPity`, `omnipotentPity`; actors save `doomSpecialAttack`; a load rebuilds
  `MawRules` and re-reads the ledger.
- Preferences: defaults homing on, friendly fire off, loot filter off (zz_Maw-initialize.lua:536-543 defaults applied
  on LoadMap); disintegration only in Insanity/Madness, read live (MawCombatRules.cpp:2491-2504); `enableDisintegrate`
  default true.
- Madness ledger (MON:2289-2534): five game minutes, cut to the last half minute with no enemy near, cleared on leaving
  the map and on a party death (which counts one), a pending run counted on the next load, warning before loading;
  2 real seconds a game minute for the HUD timer. Only the marking source differs (CHM-2).
- Insanity food cap 15 + ⌊High/25⌋ indoors, refund outdoors, re-applied on a save load (MON:2172-2187).
- Mode content gates: outb3 92 (Doom family closes it; else difficulty ≤ MAW or level 255), oute3 104 (Maps/outb3.lua:56-67,
  Maps/oute3.lua:118-125 ↔ `outb3_maw.lua`, `oute3_maw.lua` via `evt.RulesetInfo().challengeMode`).
- Rules panel text: groups and loot columns match MAW's density and rarity tables; mode descriptions match the
  thresholds and new-game bonuses.
- MMMerge's own bolster stays off in MAW (MON:2134-2137 sets `UseMonsterBolster=false`; AdaptiveMonstersStats gates on
  it) ↔ GAPS D.8 row text in Settings.
