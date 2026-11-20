# OVR1 — MAW overrides of MMMerge files (second pass)

Files: `Scripts/Core/events.lua`, `Scripts/Structs/After/RemoveSkillValueLimits.lua`, `Scripts/Structs/RacialSkills.lua`,
`Scripts/General/MenuChooseCharacter.lua`, `Scripts/General/ExtraQuickSpells.lua`.
Method: `diff --strip-trailing-cr reference/mmmerge/<path> Maw-Mod-MMMerge/<path>` (MAW files use CRLF, a plain diff
shows every line changed), every hunk classified with `git log -p --follow` in the MAW repo, then grep of
`game/rules/maw`, `assets_dev/rulesets/maw`, DEVIATIONS, GAPS and the pass-1 audit files. Native addresses were
checked with `objdump` on `re_mm8/mm8_orig/mm8.exe` (rizin is not installed on this host at the moment).

## Findings

### OVR1-2-1: Treasure-level-7 chest slots in MAW become boss-path loot, not a plain level-6 item (extends GAPS A2.6)
Severity: P3 (only explicit `-7` chest slots; better loot quality there)
Confidence: plausible (native path read in the binary; load order needs a runtime check)
MAW: GAPS A2.6 rests on `zzMaw-Items.lua:27-28` (`events.GenerateItem` lowers strength 7 to 6). That hook only
covers `GenerateItem` (0x453ECC), which handles ground items and other strength-7 calls. MM8's `GenerateChests`
(0x44D96C) sends a chest slot of level 7 or more (`cmp edx,7; jge 0x44DC3F` at 0x44DA0A) straight to
`GenerateArtifact` (0x44DD43). That path picks id 500 + rand(43) without calling `GenerateItem`, so MAW's clamp never
sees it. It also never fails in MAW: `MiscTweaks.lua:567` NOPs the found-marking, and MAW empties `ExtraArtifacts.lua`,
so nothing remaps the id. The strength-6 always-enchant fallback at 0x44DC51 therefore never runs. On the same load,
`zzMaw-Items.lua:4523-4533` (`AfterLoadMap`) re-rolls every chest artifact that is in `mawArtifacts`, has value ≥ 20000,
MaxCharges 0 and BonusStrength 0 through `LootContext.markBoss()` + `Randomize(6,0)`. The source comment at :142 says
this is intended: "chest artifacts are re-rolled through the boss path". The MM8 artifacts missing from `mawArtifacts`
(516, 532, 538-541) stay as artifacts.
So a MAW `-7` chest slot gives boss-quality strength-6 loot (boss rarity and power, `zzMaw-Items.lua:978, 1135-1209`),
or about 6 times in 43 a real MM8 artifact.
OpenYAMM: `game/rules/maw/MawItemRules.cpp:901` (`levelSevenGivesRareItem` false) and
`game/items/ItemGenerator.cpp:174-180` turn the slot into a plain level-6 request with `boss = false`
(`ChestRuntime.cpp:541-565`, `TreasureRuntime.cpp:133-150`). The result is ordinary non-boss MAW loot, and it can be
a potion, scroll or reagent.
Not covered by: GAPS A2.6 (done; its reasoning "MAW lowers 7 to 6" holds for ground and `GenerateItem` slots but not
for chests). DEVIATIONS 16 covers only *placed* fixed artifacts ("Placed artifacts stay"), not generated level-7 slots.
Suggested fix: for MAW chest slots resolved to level 7, generate at level 6 with `request.boss = true`. Optionally
keep MAW's small chance of a real artifact for the ids missing from `mawArtifacts`. Alternatively, record "level-7
chest slots give plain level-6 loot" as a deviation. Ground `-7` objects are correct as they are.

### OVR1-2-2: MAW never got MMMerge's off-hand dagger fix: base Dagger ≥ 64 dual-wields without Expert (question: MAW bug, no row)
Severity: P3
Confidence: confirmed (read both sides and the native instruction)
MAW: `Scripts/Structs/After/RemoveSkillValueLimits.lua` lacks MMMerge's patch at
`reference/mmmerge/.../RemoveSkillValueLimits.lua:826` (`asmpatch(0x46772E, "test eax, 0xFFFFC00")`, "Prevent offhand
dagger being allowed at base mastery 64 skill level"). The native instruction at 0x46772E is
`test eax, 0xFFFFFFC0` on the raw Dagger word (`[ebx+0x37C]`), MM8's "Expert bit 6" test. With MAW's ExpertBit 10 and
base skill up to 500, any character with Dagger level ≥ 64 passes, even at Normal mastery. The MAW file came from
MMMerge in Jan 2024 (`bd11168e`) and has never had the patch, so this is version drift rather than a MAW feature.
MAW's own tooltip still says "Expert: can dual wield" (`zzMAW-Skills.lua:861`).
OpenYAMM: `game/rules/ItemRules.cpp:139` (used by `MawItemRules::wield`, `MawItemRules.cpp:1445`) requires Dagger
Expert, which matches MMMerge and MAW's stated rule.
Not covered by: no DEVIATIONS or GAPS row.
Suggested fix: none in code. Optionally add a DEVIATIONS row saying the Normal-mastery Dagger ≥ 64 off-hand quirk
(drift from an older MMMerge) is not reproduced.

## Hunk inventory and outcome ("Checked and matching")

### Scripts/Core/events.lua (2644 lines, 1 behavioural hunk)
- Line 2613 `if not slot then slot=0 end` (MAW, `PlayerAttacked`/HitPlayer): a guard for a nil target slot when no
  member is conscious (`Game.Rand() % 0`). It is a Lua robustness fix with no gameplay rule. OpenYAMM picks monster
  targets in C++ and has no such nil path. Nothing to port, and nothing leaks into Standard.
- MAW commit `c1b11bc4` (GenerateItem passes `t.AlwaysEnchant`) brings MAW's copy into line with MMMerge, and it is in
  `ef23ee17`. This is drift, not a MAW feature. Its MAW consequence is OVR1-2-1.
- No other differences (verified with `--strip-trailing-cr`).

### Scripts/Structs/After/RemoveSkillValueLimits.lua
- `MaxSkillVal` 0xFF→0x3FF (base + bonus ≤ 1023) is a MAW feature, ported in `MawSkillRules.cpp:350-378`
  (`EffectiveSkillLimit = 1023`, capped skills 2× cap, item bonuses trimmed before follower bonuses).
- `MaxSkillBase` 0x50→0x1F4 (raise limit 500) is a MAW feature, ported in `MawSkillRules::skillLevelCap`
  (`MawSkillRules.cpp:174-178`). It is enforced in `SkillRules::canRaiseSkill` and `skillRaiseCostDetail`
  (`level < cap`, which matches native `cmp dx, MaxSkillBase`). Standard returns `nullopt` (unchanged from HEAD).
- Mace Stun 0x4371BE, Mace Paralyze 0x4371E9 and 0x4377B8, and Staff Stun 0x437215 become `and ebx, 0`. This is a MAW
  feature (`8c2a83fe`, replaced by `MawCore.Damage.weaponStun`). Ported: `MawCombatRules.cpp:1521-1523` resets
  `stunTarget` to the item-only stun, clears `paralyzeTarget` (so `applyMeleeWeaponEffects` in
  `GameMechanics.cpp:1971-2004` contributes nothing), then runs `applyWeaponStun` (`MawCombatRules.cpp:583-610`).
  Standard keeps the engine stuns.
- Unarmed Evasion 0x4380C4 becomes `and edi, 0`. This is a MAW feature, already covered by the pass-1 CNT line
  (`MawCombatRules::characterEvades`; MAW also comments out MiscTweaks' repair at :599).
- `mem_cstring` local vs `MF.cstring`, `get_player_from_ptr` vs `internal.GetPlayer`, `SplitSkill` using the bit
  constants, and the "Patched in SpellsExtra" comments are drift or refactoring with no behaviour change. The Lloyd's
  Beacon patches are active in both files.
- MMMerge's old-save conversion (`ConvertPlayers`, `ConvertMap`, `vars.SkillValueLimitRemoved`) is missing in MAW.
  This is drift and does not apply to OpenYAMM.
- The missing 0x46772E dagger patch is OVR1-2-2.
- Monster SpellSkill masks to 0x3FF: OpenYAMM's `parseMonsterSpellSkillLevel` (`MonsterTable.cpp:327`) does not
  mask, so values up to 1023 are fine.
- The rest (GM bow item-bonus switch, attack delay, Learning, roster masteries and so on) is identical apart from the
  bit constants.

### Scripts/Structs/RacialSkills.lua
- MAW ships an empty file (`68b49ce1` "substitute racial skills"), which disables MMMerge's `Race Skills.txt` mastery
  limits and `GetMaxSkillLevel`. Ported: `assets_dev/rulesets/maw/ruleset.yml:236-238` replaces `race_skills.yml` with
  `content/race_skills.yml` (`Race Skillz.txt` port, `shift_without_class_cap`). Pass-1 CLS checked the values.
  Standard keeps `engine/data_tables/race_skills.yml` (MMMerge `Race Skills.txt`), so nothing leaks either way.

### Scripts/General/MenuChooseCharacter.lua
- The FreeSelection toggle button is removed and free selection is always on (`0376e66f`): any class with
  `ClassesExtra` Kind ≠ 0 and no lower step of its kind, and every portrait with Race < 255. This is a MAW feature,
  ported by `free_selection: true` (`assets_dev/rulesets/maw/content/character_selection.yml:6`, read in
  `MergedBaseTables.cpp:779` and `NewGameScreen.cpp:879, 906`) and covered by GAPS A6.6 and the CLS pass-1 check.
  Standard's `character_selection.yml` has no `free_selection` (pass-1 STD2:244).

### Scripts/General/ExtraQuickSpells.lua
- In the extra quick-spell slots, the SP check uses the cost at the caster's school mastery instead of the Normal cost
  (`3fab67e9`). This is a MAW fix. OpenYAMM has no extra quick-spell slots in either ruleset (stated in DEVIATIONS
  26). Its single quick spell already checks the real cost through `PartySpellSystem::manaCost` plus the ruleset's
  `castRefusal`, and falls back to an attack (`GameplaySpellService.cpp:121-128`). Nothing to port.

## Out-of-scope note (Standard, pre-existing at HEAD, not MAW)
- With every artifact found, a Standard level-7 chest slot is left empty (`ItemGenerator.cpp:183-195`,
  `chooseRandomRareItem` skips found artifacts). MM8 gives a strength-6 always-enchanted item instead (0x44DC3F-0x44DC5D).
  MMMerge never runs out, because it removes the artifacts-found limit (`MiscTweaks.lua:558-568`). This is
  Standard-only behaviour from before the MAW work; listed only so it is not lost.
