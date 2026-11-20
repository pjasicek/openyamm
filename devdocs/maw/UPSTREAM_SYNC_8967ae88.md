# MAW upstream sync: 8fbb48d1 → 8967ae88

Our MAW ruleset followed MAW `8fbb48d1` (2026-11-04, [UPSTREAM_SYNC_8fbb48d1.md](UPSTREAM_SYNC_8fbb48d1.md)). MAW
`origin/main` is now `8967ae88` (2026-11-12): 13 commits, 21 files, +247/−250 lines, half of it a code cleanup
(`GetWeaponSkillFor`, `GetItemEquipStat` replacing copied axe checks). The local MAW clone
(`/home/pjasicek/github/Maw-Mod-MMMerge`) is fast-forwarded to `8967ae88`. Paths on the MAW side are relative to
`Maw-Mod-MMMerge/Scripts/`. Status 2026-11-12: everything marked **Port** is built.

Legend as in the previous sync: **Port** = changed our code or data to match; **Have** = we already match or never had
the problem; **N/A** = engine or MMExtension plumbing with no equivalent.

| # | MAW change | Commit | Action and where |
|---|---|---|---|
| 1 | Experience curve: `expStep(L) = 1000 L max(1 + (L - 100) x 0.005, 1)` (was x 0.01): above level 100 a level costs less, e.g. level 500 needs 270.9 M (was 417.1 M) | ba572ec2 | **Port**: `MawExperienceCurve.cpp`. Every bolstered level above 100 moves too (`bolsteredLevel`, the Ravenshore worked example at party level 100: 105, 110, 115, 107, 110, 114, 106, 113, 119). `data/exp_curve.yml` regenerated; the 2^31 requirement clamp MAW has is now first reached at 1040 → 1041 (DEVIATIONS 9) |
| 2 | Item level requirement: `ItemLevel.WearLevel(drop, tier) = min(L - (10 + 0.09 L), 0.8 drop)` with `L = drop + tier levels`: a high ladder rung no longer raises the requirement above 80 % of the drop level | 57162f8b | **Port**: `mawLevelRequirement` (`MawItemFormulas.cpp`); `data/loot.yml` `level_requirement_by_drop_level` regenerated |
| 3 | Spells: every damage spell's mana cost by mastery now lives in `spellPowers` (`cost`, zzMaw-Spells.lua:1910-1958) and is written to `Game.Spells`; the old Lua overrides (Lifedrain, Lightning Bolt, Flame Blast) folded into it. Damage: Incinerate 20 + 1d20 (was 19 + 1d21), Poison Spray d5 (d3), Ice Bolt d5 (d7), Flying Fist d10 (d5), Prismatic Light 20 + 2d10 (30 + 2d6), Sunray 40 + 1d40 (60 + 1d60), Armageddon 30 (50), Lifedrain d15 (d22). Lightning Bolt recovery 100 at every mastery (`Spells2.txt`) | 13f89c9e | **Port**: `tools/maw/generate_ruleset_patches.py` reads `cost` (also for Mass Distortion, whose dice stay unused) and regenerates `patches/spells.txt`. Costs that change: Inferno 25 (was 50), Poison Spray 2/4/6/8 (2/4/5/6), Lightning Bolt 10/10/15/20 (10/10/20/30), Flame Blast 25/40/50/60 (10: MAW set it in `zzClasses.lua` before, which we had missed). The id-keyed Lightning Bolt and Lifedrain rows left `content/spells_patch.txt` |
| 4 | Halberds (46-50, 507, 838-840, 1638-1640) are wielded with Spear or Axe, whichever is higher (level, then mastery; `GetWeaponSkillFor`): their recovery, damage multiplier, attack, Axe crit damage, the skill's armour and resistance, the Spear stack. They always count as two-handed axes for the two-axe damage cut and the Minotaur's off-hand speed rule. A character with Axe and no Spear may equip one; a Minotaur holds one in one hand, and in the off hand from Master Axe, as a two-handed axe | a1789e54, edb03f42, 13f89c9e | **Port**: `ItemRules::weaponSkill` (Standard: the item's skill), which the equip check asks; `mawWeaponSkill`/`mawIsHalberd` (`MawItemRules`) in the attack delay, crit inputs, weapon pace, Spear stack and its percent, the character sheet's weapon rows and guard, the Assassination bonus, the item popup's attack speed and the skill popups' guard; `MawItemRules::wield` |
| 5 | Map completion pays by the level of the map's monsters: outside Beyond Madness and dimension runs, `exp = ceil(m^0.7 (C x 20 + C^1.8) / 3 / 1000) x 1000` with C the map's own B-row middle level (`mapMonsterLevel`), else the average level of its hostile monsters; the gem tier reads C too. The horizontal-progression `bolster = 2 x map level` is gone | 5a15a808 | **Port**: `MawRules::mapMonsterLevel` (split out of `mapDropLevel`), `MapKillProgress::monsterLevelSum`/`levelledMonsters` (both world runtimes), `MawExperienceRules::rewardMapProgress` |
| 6 | A Skilled boss's four Horseshoes are marked, and the gather key (K) teleports them with the crafting items | 8967ae88 | **Have**: our Horseshoes are corpse loot (`MawMonsterRules` extra items), which the gather key brings with the corpse |
| 7 | Monster info box: with Detect Life (or identified HP) the bottom line shows the real HP instead of the engine's 16-bit copy; the "Current Health" line left the effects text | e4ce3de7 | **Have**: our actors keep full HP and the panel never had the 16-bit copy or that line |
| 8 | The Seer (794): Dimensional Maps moved from topic slot 0 to 2, the Seer's own topics went under a "Guidance" submenu with "Back"; the respec topics take `Branch = ""` | fb82cb63 | **Have**: our Seer shows its three own topics (A-C) and MAW's three (D-F, `content/npc_respec_patch.txt`); no slot was ever covered |
| 9 | Dungeon entrances: out11 505 (Barrow VII) to `mdk01.blv` and the Hall under the Hill to `7d22.blv` | ee234432 | **Have**: we kept our own entrance events and never had MAW's wrong targets (MAPS_CONTENT.md §3.4) |
| 10 | `Skillz.dll` bridge removed (an old install with the DLL now stops with a message); the Detect Life line drawn by a binary patch; `GetLevelRquirement` and tooltip clean-ups | 588ce215, c58f086c | **N/A** |

## Checks

- `data/balance_golden.csv`: the harness (`harness/mawmon/lua/harness.lua`, line ranges moved to `8967ae88`) gives a
  byte-identical file, so the balance model did not change: it reads levels directly, not through the curve.
  Rebuilding the old one from `8fbb48d1` with the previous harness reproduced the committed file first.
- Tests: `MawBalanceModelTests` (curve samples, bolstered levels), `MawItemFormulaTests` (level requirements),
  `MawMonsterLevelTests` (Ravenshore example, level banks), `RulesetTests` (generated spell costs), new
  `MawClassTests` "MAW halberds are wielded with Spear or Axe, whichever is higher" and `MawMonsterItemAuditTests`
  "MAW pays a map clear by the level of its monsters, else by the map's level".
