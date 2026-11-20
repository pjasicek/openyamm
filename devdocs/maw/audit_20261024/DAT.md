# DAT — data tables and the patch generator

Method. I reimplemented the loader's composition in Python exactly as `GameDataLoader::applyActiveRulesetTable` +
`ContentTableComposer.cpp` do it (TextTable quoting rules, trimmed keys, header-name/`#index` columns, row-number keys,
append, appendColumns, contributions in `ruleset.yml` order) and composed every patched table from the current engine
tables. I then compared every MAW cell, not a sample (items 35k cells, monsters 24k, map stats 6.5k, random items 15k,
class skills 2.8k, spells, specials, potion settings, place_mon, class, class extra/multipliers/starting skills and
stats), mapped through the generator's own column/key/value tables, against MAW `ef23ee17` (`zMaw.T.lod` and
`Data/Tables`). With only the generated contributions applied, every MAW cell matches except the groups explained
below; the hand-written contributions were then checked against MAW's run-time Lua one by one. Scripts:
`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/ff95062f-c7c8-4a63-bccd-089ec5bf6da6/scratchpad/dat/compose.py`,
`.../dat/compare.py`, output `.../dat/compare_gen.txt` (generated only) and `.../dat/compare_out.txt` (with content).

### DAT-1: The map_stats.txt contributions never reach the game: loadMapStats skips the ruleset
Severity: P1
Confidence: confirmed (read both sides; the composed table is right, the runtime never applies it)
MAW: `zMaw.T.lod/mapstats.txt` — MAW's own map table: Treasure level ("Tres", col 11, header `0-6`) is 6 on all 128
maps that differ, plus 43 `Mon 1`, 49 `Mon 2`, 23 `Mon 3` encounter names, 18/25/7 `MonN Pic` pictures, and encounter
difficulty/count cells (#18, #19, #22, #23, #26, #27); `zzMaw-Monsters.lua:904-908` adds the Hall under the Hill
(map 96) Wisp/Unicorn. MAW's `AdjustMonsterDensity` (`zzMaw-Monsters.lua:797-900`) and level code
(`zzMaw-Monsters.lua:449-458`, "MonsterNPic .. ' B'") read this table.
OpenYAMM: `game/data/GameDataLoader.cpp:2413-2441` `loadMapStats` reads `engine/data_tables/map_stats.txt` with
`readTextFile` + `parseTabSeparated` and calls `m_mapStats.loadFromRows` directly; it never calls
`applyActiveRulesetTable` (every other patched table goes through `loadTextTableRows`/`loadFirstTextTableRows`/
`readRulesetDataFile`). So `patches/map_stats.txt` (342 cells) and `content/map_stats_patch.txt` (map 96) are dead in a
MAW game: Standard treasure levels (out01 is 0 instead of 6 — feeds `request.treasureLevel` →
`MawItemRules.cpp:967` loot grade), Standard encounter monsters, difficulties and counts (feed
`MawMonsterRules.cpp:1335-1397` density and `MawRules.cpp:588` map-level inputs), and no Wisp/Unicorn in 7d22.
`tests/RulesetTests.cpp:712` composes the table from the files itself, so it passes while the game never applies it.
Not covered by: no related row in DEVIATIONS or GAPS; HANDOFF.md §6 phase 8 lists "the Hall under the Hill's monsters
(`content/map_stats_patch.txt`)" as done.
Suggested fix: build `rows` in `loadMapStats` and call `applyActiveRulesetTable(assetFileSystem, mapStatsPath, rows)`
before `loadFromRows`. Also make the loader record which contributions it consumed and fail (or warn) when an active
ruleset lists a table nobody read, so this cannot recur silently.

### DAT-2: MAW makes every caster's SP stat Personality; OpenYAMM keeps the table's Intellect/Mixed stat
Severity: P1 (SP of every Intellect and Mixed caster scales with the wrong stat)
Confidence: confirmed for the table edit and our formula; the engine's use of SPStats is standard MM8 (OpenEnroth
`Character::GetMaxMana` uses the class mana stat)
MAW: `Scripts/General/zzMaw-Items.lua:4427-4433` (GameInitialized2): every class with `SPStats > 0` gets
`SPStats = 2` (Personality). The engine's own SP then adds SPFactor x E(Personality), and `addMana`
(`zzMaw-Items.lua:3131-3146`) adds a second SPFactor x E(Personality) — which is why its Enlightenment base
`totalMana` counts `effect*2`. Net: SPFactor x (level + 2·E(Per) + Meditation) for every caster, Intellect never
counts. (It also overrides zzClasses' Dragon/Great Wyrm `SPStats = 3`, `zzClasses.lua:322-325`, which runs first.)
OpenYAMM: `game/rules/maw/MawClassRules.cpp:192-222` `baseMaxSpellPoints` switches on `entry.manaMode` from
`class_multipliers.txt` (`Intellect`/`Personality`/`Mixed`), then adds `mawStatEffect(personality)`. Intellect classes
(Sorcerer line, Archer, Dark Elf, Elementalist, ...) get E(Int)+E(Per); Mixed classes (Druid, Ranger...) get
E(Int)+2·E(Per); MAW gives both 2·E(Per). The composed `class_multipliers.txt` still has `Intellect`/`Mixed`
(MAW's `Class HP SP.txt` does too — the change is only in Lua).
Not covered by: DEVIATIONS 25 describes the formula as "class stat effect + Personality effect" (that row is the
misread); TRAINERS_SKILLS.md:842 notes the forcing but it was never implemented; no GAPS row.
Suggested fix: in `baseMaxSpellPoints` use the Personality effect as the class stat for every class whose mana mode is
not None (or add a content patch setting `ManaStat` to `Personality` for those rows), and correct DEVIATIONS 25.

### DAT-3: Standard's raised spellbook drop weights carry into MAW (about 3x MAW's spellbook share)
Severity: P2
Confidence: confirmed (table values); MAW drops come from the same weights (`ItemGenerator.cpp:248` picks by
`random_items.txt`, `MawItemRules::rollPlainItem` only post-processes)
MAW: `zMaw.T.lod/rnditems.txt` rows 400-497, 1202-1300, 1904-2018 keep MMMerge's spellbook weights (e.g. 400 Torch
Light 0/0/0/0/0/0, 404 Haste 0/0/2/0/0/0).
OpenYAMM: `assets_dev/engine/data_tables/random_items.txt` (commit `59072f7b1`, 2026-10-15, 300 rows) raised them
(400 0/2/0/0/0/0, 404 0/0/4/1/0/0). The generator treats every cell where ours differs from MMMerge and MAW does not as
"our fix" (`tools/maw/generate_ruleset_patches.py:221-236`), so 394 cells stay Standard under MAW. Spellbook share of
random drops per treasure level 1-6: MAW 0/1.4/5.0/2.4/2.3/2.4 %, composed MAW ruleset 0/4.0/13.7/6.9/6.3/6.8 %.
Not covered by: HANDOFF.md:66-67 names only 418/1220 as kept fixes; no DEVIATIONS/GAPS row.
Suggested fix: decide whether this is a fix or a Standard rebalance; if the latter, have the generator emit MAW's
values for these rows (a "force MAW" list), or add a DEVIATIONS row.

### DAT-4: MAW's collision shrink for Behemoths, Minotaurs and MM6 demons is not ported
Severity: P3
Confidence: confirmed (absent in our data and code)
MAW: `zzMaw-Monsters.lua:3615-3630` (GameInitialized2) multiplies `MonListBin` Height and Radius by 0.75 for monsters
207-209, 300-302, 578-580, 498-503 ("monsters that tend to get stuck"). Not in MMMerge's scripts.
OpenYAMM: no ruleset contribution for `monster_descriptors.txt`; nothing in `game/rules/maw` scales actor radius or
height.
Not covered by: no related row.
Suggested fix: a `content/monster_descriptors_patch.txt` override (radius/height x0.75 for those ids), added to
`ruleset.yml`, or a deviation row if our pathing does not need it.

### DAT-5: Small MAW run-time item table edits not carried
Severity: P3 (display only)
Confidence: confirmed
MAW: `zzMaw-Items.lua:406-407` renames the unidentified names of 67 (Flail → "Mace") and 804 (Saber → "Longsword");
`zzAlchemy.lua:1324` sets the Endless Potion (1069) ground sprite to 130.
OpenYAMM: composed `items.txt` keeps "Flail"/"Saber" in `Not identified name` (the ladder rungs in `data/items.yml`
already account for the rename); `content/items_patch.txt` sets 1069 `Sprite Index` 60.
Not covered by: ITEMS_DATA.md §2.3 mentions the rename only for rungs.
Suggested fix: add the two `Not identified name` cells to `content/items_patch.txt`; 1069's sprite is a choice.

### DAT-6: appendTableColumns drops cells of rows wider than the header
Severity: P3 (latent; no current table is affected)
Confidence: confirmed (code read; `class_skills.txt` rows are all 54 wide today)
MAW: n/a
OpenYAMM: `game/content/ContentTableComposer.cpp:477-480`: `row.resize(max(row.size(), width))`, insert at `width`,
then `row.resize(width + count)` — any cells a row has past the header width are pushed right and then cut off.
Not covered by: no related row.
Suggested fix: insert at `width` without the final truncating resize (or fail on rows wider than the header).

### DAT-7: m_mawTextData is not reset when the ruleset goes back to Standard
Severity: P3 (harmless today: `createMawRules` returns null without map levels)
Confidence: confirmed
OpenYAMM: `game/data/GameDataLoader.cpp:3916-3921` resets the other five MAW data members and the extra houses but not
`m_mawTextData` (set at 4013); after MAW → Standard in one process `mawTextData()` still returns MAW's texts.
Not covered by: no related row.
Suggested fix: add `m_mawTextData.reset();` with the others.

### DAT-8: Declared monster-name id range does not cover MAW's added names
Severity: P3
Confidence: confirmed
OpenYAMM: `ruleset.yml` `idRanges.monster_names: 220-301`, but `content/place_mon_names.txt` appends 205 (Naga Empress)
and 211-214 (Baa clergy). A world that claims 205-214 passes the overlap check and then fails `appendTableRows`
("key already exists") only when MAW is chosen.
Suggested fix: declare 205-301 (or 205-214 as a second range).

### Question: generator drops repeated source keys silently
`keyed_rows` (`generate_ruleset_patches.py:150-163`) discards keys that repeat (Spells2 `Charm`, `Unused!!!`) without
reporting them; Charm is handled by `content/spells_patch.txt`, so nothing is lost today, but REPORT.md should list
such rows so future MAW updates do not lose cells unnoticed.

## Checked and matching

- Generated patches vs MAW tables, all cells (generated contributions only): items, monster_data (typo fixes 5/6 as
  documented), special_item_enchants, place_mon, class, class_extra, class_multipliers (incl. ManaStat mapping),
  class_skills (incl. 12 appended columns, S→G, the four new skill rows), class_starting_skills, class_starting_stats,
  complex_item_pictures (user decision D.7), potion_settings, spells (mana/recovery by id; DamageBase/DiceMin/DiceSides
  from `spellPowers`, Fire Spike 133/167 %, Lifedrain 167/233 % match MAW's CalcSpellDamage). Only differences:
  "ours kept" cells (items capitalisation/Bow→Missile 11, monster Blood 133, map `in area`/Track 208, random items
  394 = DAT-3), and the documented 418/1220 conflicts.
- `english/potion.txt` and `english/potnotes.txt` replacements equal MAW's files row for row.
- Rows MAW has that we lack are all accounted for (monsters 649-651 Cactus and maps 204-206 Breach are absent in
  Standard too; place_mon 163-1000 are numeric placeholders; potion_settings 1041-1066 → potion_effects.yml; Seraphim
  starting row → content).
- MAW run-time Lua edits vs content: Halberds two-handed (12 ids), potion names/pictures 252-299, Dimension Map 290,
  Greater Heal 473/1275/1989, all spellbook values (simulated MAW's `zzMaw-Items.lua:2227-2287` loop: 0 differences),
  crafting items 1041-1070 values/names, SpecialItems prices (516, 539-541, 1439, 2118, 2119, 2199), special texts
  (SpcItemsTxt 0-based → row id+3, all 12 right), Steal→BrkItem (no `Steal` left), AI Type non-Wimp→Suicidal (516/139),
  Zombie/Ghoul hostility (rows 143/152 = Zombie/Ghoul), houses opening at 6→5 (no 6 left), spellbook shop tiers
  (rows 277/281, test-covered), Mind Charm / Chain Lightning / Lifedrain costs, Dragon Fear and Flame Blast costs
  (code, `MawSpellRules.cpp:492-501`), Dragon SPBase 60 and Elemental Adept HP 2.5 (code), Minotaur HP 6/12 (table),
  Elder/Ultimate factors (code), Dragon/Great Wyrm Dodging/Unarmed caps (table), weapon/shield/artifact upscaler
  (precomputed in `data/items.yml`), Austerity potion names (code), NPC respec/Druid Circlet/Arena topics (slots were
  empty), skill/Perception texts (`texts.yml`). Map-script HostileTxt edits are MMMerge's own (identical in
  `reference/mmerge_datapatch`).
- Override machinery: trimmed key matching, repeated keys fail only when patched, ambiguous header names need `#n`,
  key column cannot be patched, a cell patched twice in one file fails, empty value cells (`key\tcol\t`) apply as
  empty, quoted cells with `""`, tabs and newlines round-trip between the generator's csv writer and
  `TextTable::parseTabSeparated`; no hand-written file starts a cell with a quote. Row-number keys extend the table;
  row-keyed tables (specials, class_starting_stats) align row for row with MMMerge. Several contributions to one table
  apply in file order and each sees the previous one's rows (content overrides of generated cells win, e.g. spells by
  id after spells by name); replace then override works; appendColumns fills unlisted rows with empty cells (only
  `Throwing`, which MAW lacks — DEVIATIONS 69).
- Ruleset switch: `activateRuleset` clears the session and reloads all common data from disk; every loader touched by
  the ruleset clears its containers first (checked ClassSkillTable, ClassMultiplierTable, ItemTable, MonsterTable
  stats/names/relations, NpcDialogTable, JournalQuestTable, HouseTable, CharacterDollTable, SpellTable,
  SpecialItemEnchantTable, Potion tables, RaceStartingStats, merged class extra/selection/race skills/potion
  settings/house rules); skill display names and NPC extra houses reset. Standard tables come back unchanged (apart
  from DAT-7).
- Standard isolation: `standardRulesetDefinition()` has no tables, so `findTables` returns nothing and
  `readRulesetDataFile` reads the engine file; overlay directories are added only when `activeRulesetRoot()` is
  non-empty; `rulesets/` is mounted at its own root, so engine/world enumerations never see it; no game code reads
  `rulesets/maw/...` directly. The editor reads raw engine tables (expected).
- `./build/tests/openyamm_unit_tests --test-case='*generated MAW patches*'` passes (binary may be stale).
