# MAW upstream sync: 8967ae88 → 7ddb228c

Our MAW ruleset followed MAW `8967ae88` (2026-11-12, [UPSTREAM_SYNC_8967ae88.md](UPSTREAM_SYNC_8967ae88.md)). MAW
`origin/main` is now `7ddb228c` (2026-11-18): 16 commits (12 without merges), 295 files, +149,157/−820 lines. Almost
all of it is one commit (`c93865e5`) that puts Rodril's MMMerge patch and Multiplayer module into the MAW repository;
the gameplay changes are about 150 lines. The local MAW clone (`/home/pjasicek/github/Maw-Mod-MMMerge`) is
fast-forwarded to `7ddb228c`. Paths on the MAW side are relative to `Maw-Mod-MMMerge/Scripts/`. Status 2026-11-18:
everything marked **Port** is built.

Legend as in the previous syncs: **Port** = changed our code or data to match; **Have** = we already match or never
had the problem; **N/A** = engine or MMExtension plumbing with no equivalent.

| # | MAW change | Commit | Action and where |
|---|---|---|---|
| 1 | Balance model (`Modules/MawCore/Estimates.lua`). The legendary ramp is full at level 500 (was 420). The expected base item climbs the ladder with the level: `estimateBaseTier(L) = 1 + 5 min(L / 100, 1)`, so the weapon's flat damage is `16 min(L / 100, 1)` (was `min(0.5 L, 16)`) and the worn armour is `armorTierAC(tier) + 116 c / 40 x geared` with `armorTierAC = 116 (0.21 + 0.79 (tier - 1) / 5)` (was `(116 + 116 c / 40) x geared`). The expected weapon is a bare one plus the geared share of the Primordial weapon of the level (`estimateWeapon`, item level `GetPrimordialCharges(L) x 5`; was a weapon of item level L), and the enchant base is that weapon's level damage times the geared share (`estimateWeaponLevelDamage`). The ring resistance enchantment counts by the geared share | f1ffd3b1 | **Port**: `MawBalanceModel.cpp` (`legendaryRamp`, `baseTier`, `weaponFlat`, `primordialCharges`, `referenceWeaponLevel`, `armorTierArmorClass`, `wornArmor`, `enchantResistance`, `expectedWeapon`, `expectedWeaponLevelDamage`; `attack`, `power` and `spellPower` read the last two). The Python copy `tests/scenarios/solo_balance/model/mawmodel.py` got the same changes. BALANCE_MODEL.md §3 |
| 2 | A character's resistance is divided by `100 + 2 x monster level` (`Formulas.resistanceDivisorPerLevel = 2`, was 1), in the model and in every hit | f1ffd3b1 | **Port**: `mawResistanceDivisor` (`MawBalanceModel.h`), which the model and `mawMitigatedDamage` both read |
| 3 | The Arena (d42) is sized by the Endless Arena's level A (the one being fought, else `highestArenaWave + 1`): a B row at `step + A x step` with step 6 (8 in Beyond Madness), 2 higher for the family of the level's second wave and 4 for its third; the other tiers at `+ 1.2 (base - B level)`. Gone: six times the table level, and the 600 levels plus 3.5 a wave once the waves ran past the family list. `arenaWaveMonster(wave)` is shared by the spawner and the level table | 2f172096 | **Port**: `MawMonsterLevelInputs::arenaLevel` and the d42 branch of `resolveMawMonsterLevels`; `mawArenaFamilies` and `mawArenaWaveMonster` moved to `MawMonsterLevels`; `MawRules::arenaLevel` (runtime copy, part of the level cache's key), set by `MawMonsterRules::updateMonsters` from the global variables `MawArenaLevel` and `MawArenaBest` while the party is in d42, with `refreshRulesetMonsters`. The ordinary arena bouts (Page to Lord) draw by these levels too (`arenaDrawLevel`). DEVIATIONS 50 is no longer a deviation |
| 4 | An Assassin's Mass Distortion (a weapon blow) takes Earth's resistance once; the extra division is gone. The spell's "proxy units" flag (`t.ProxyUnits`) replaces the `Spell == 44` tests, so the Assassin's blow is no longer rescaled by the monster's HP proxy pool | 21275f61 | **Port**: the Assassin's special case left the resistance stage (`MawCombatRules.cpp`); the blow is resisted as any class spell. **N/A** for the proxy pool: our actors keep full HP |
| 5 | Sniper: Learning (Ascension) up to Grandmaster (was Master) | f5bd8bb2 | **Port**: `patches/class_skills.txt` regenerated (`Learning Sniper G`) |
| 6 | Quest gold scaling: the first load of a session paid quest gold unscaled, because MAW's handler ran before MMExtension's reward; it now judges the reward on the next tick | ef1c1d84, 33da70f6 | **Have**: `payQuestGoldBonus` compares the party's gold and experience after the topic's event has run |
| 7 | Item sorter and multi-bag rewritten around the engine's own backpack placement (`Engine.putInBackpack`), after sorting lost items; an item on the cursor with a body location is cleared. The sort order is unchanged | 6e579e8c, 8f4ea52a | **Have**: our inventory and bags are our own code |
| 8 | Indoor backpedal: the hook halved the walk-forward store instead of the second walk-backward one | 0c801b53, f47f291f | **N/A**: MAW's movement patches are not ported (GAPS D.9) |
| 9 | Rodril's MMMerge patch (nightly build) and Multiplayer module ship inside the MAW repository: 276 files under `Data/`, `ExeMods/` and `Scripts/`; two installation steps left the README | c93865e5 | **N/A**: 218 of the files are in `reference/mmmerge`, identical (49) or different in line endings only (169), and one more is identical to `reference/mmerge_datapatch`'s; 6 are the multiplayer branch's versions (multiplayer hooks, a final newline in `DecList.txt`); `Character selection.txt` differs in one cell (row 6); the other 49 are multiplayer-only files. `tools/maw/generate_ruleset_patches.py` gives the same patches but for change 5 |
| 10 | File integrity check (`MAW_Manifest.txt`, `zzMaw_IntegrityCheck.lua`, a workflow that writes the manifest); the death timer hidden in the main menu; `os.mkdir` instead of a shell command; the guidebook's class skill matrix | 7e118093, 7ddb228c, 99bf1935 | **N/A** |

## What the model change does

`data/balance_golden.csv` is regenerated from MAW's own Lua; monster health follows the expected character's power
and monster damage its vitality, so both moved at every level. Party of 5, B-tier monster, old → new:

| Level | MAW: health | physical | magic | Nightmare: health | physical | magic | Beyond Madness: health | physical | magic |
|---|---|---|---|---|---|---|---|---|---|
| 10 | −21 % | +9 % | −2 % | −18 % | +6 % | −3 % | −16 % | +3 % | −3 % |
| 30 | −29 % | +12 % | −7 % | −26 % | +9 % | −8 % | −26 % | +5 % | −6 % |
| 50 | −29 % | +17 % | −9 % | −26 % | +13 % | −10 % | −20 % | +8 % | −9 % |
| 100 | −22 % | +29 % | −11 % | −18 % | +25 % | −13 % | −13 % | +16 % | −15 % |
| 150 | −20 % | +21 % | −20 % | −16 % | +17 % | −21 % | −10 % | +10 % | −22 % |
| 200 | −19 % | +15 % | −26 % | −14 % | +11 % | −27 % | −8 % | +6 % | −27 % |
| 300 | −18 % | +8 % | −35 % | −13 % | +4 % | −35 % | −9 % | +1 % | −35 % |
| 500 | −14 % | +7 % | −39 % | −9 % | +5 % | −38 % | −5 % | +3 % | −30 % |
| 1000 | −12 % | +5 % | −39 % | −8 % | +3 % | −37 % | −6 % | +2 % | −29 % |

- Health falls because the expected weapon is weaker: its flat damage reaches 16 at level 100 instead of 32, and its
  power is the geared share of a Primordial item's instead of a whole item of the character's level.
- Physical damage rises because the expected character wears more armour (the base item's armour no longer shrinks
  with the geared share): 370 instead of 219 at level 100.
- Magic damage falls because resistances count for less (change 2) and the ring enchantment by the geared share
  only. On a real character the same change raises what gets through: with the old expected resistance, a magic hit
  lands about 1 % lower at level 50, 4 % higher at 100 and 11 % lower at 300.
- The expected attack is lower (−23 % at level 10, −11 % at 50, −5 % at 100), so the party hits more often:
  `mawPartyHitChance` reads it as par.
- The difficulties moved apart in health and together in damage (`data/difficulty.yml` `relative_to_maw`, level 100):
  Hard 1.29/1.11 (was 1.27/1.12), Hell 1.60/1.22 (1.55/1.24), Nightmare 1.99/1.42 (1.90/1.45), Doom 2.48/1.68
  (2.30/1.75), Road to Insanity 2.61/1.72 (2.36/1.85), Beyond Madness 2.19/1.27 (1.97/1.39). The new-game Rules panel
  (`ruleset.yml`) shows the first three.

## Checks

- `data/balance_golden.csv`: rebuilding the old file from `8967ae88` with the previous harness reproduced the
  committed one first. The harness at `7ddb228c` (`harness/mawmon/lua/harness.lua`, `Estimates.lua` now 781 lines)
  wrote the new file: 12 of the 23 value columns changed (armour, both resistances, the physical, magic and
  legendary damage taken, vitality, attack, power, spell power, monster health and damage). The golden test passes at every level and configuration.
- `tests/scenarios/solo_balance/model/mawmodel.py` matches the new file to 5e-6 (monster health and damage, MAW to
  Doom, parties of 5 and 1), as it matched the old one before the change.
- Tests: `MawBalanceModelTests` (golden rows, `relative_to_maw`), `MawCombatFormulaTests` (the Champion's hit chances
  and the monster hits, new numbers), `MawGapTests` (resistance divisor), new `MawMonsterLevelTests` "MAW sizes the
  Arena's monsters by the Endless Arena's level", `ArenaRuntimeTests` (the Squire bout draws by the new Arena levels),
  `MawAuditCombatSpellTests` and `MawSpellClassTests` (Mass Distortion takes Earth once). The whole unit suite passes
  but for `WorldMissileTests` "the staged Hesper missiles ...", which fails on the Hesper stage's own `talents.yml`
  and has nothing to do with MAW.
- Scenarios: `rulesets/maw_endless_arena`, `maw_endless_arena_level`, `maw_assassin_attack_spell`, `maw_combat_rules`,
  `maw_classes`, `maw_mm8_smoke`, `maw_challenge_modes`, `maw_bounty`, `maw_bosses` pass. In a new game the first
  wave of Endless Arena level 1 brings Pirate Seers with 34 hit points.
- `tools/maw/mm9_balance.py --check`: unchanged (MM9's numbers do not read the model's constants).

## Not done

- BALANCE_MODEL.md's printed tables (section 2) are older than this sync and the two before it; the CSV is current.
- The solo-run documents (`devdocs/solo_action/`, `devdocs/maw/solo_sim/`) quote numbers of the model at `8967ae88`.
  Their Python model is current; the quoted figures and anything tuned against them are not rechecked.
