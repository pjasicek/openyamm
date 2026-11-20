# OVR2 — MAW's modified copies of MMMerge files (second pass)

Method: for each file, `diff --strip-trailing-cr -w reference/mmmerge/<path> Maw-Mod-MMMerge/<path>` (CRLF made the
plain diff report whole files), each hunk classified with `git log --follow` on the MAW side, and every MAW change
looked up in OpenYAMM (`game/rules/maw`, `assets_dev/rulesets/maw`, map overlays, `tools/maw/generate_ruleset_patches.py`)
and in DEVIATIONS, GAPS, PHASE9 and the first-pass files. MAW paths relative to `Maw-Mod-MMMerge/Scripts/` unless
they start with `Data/`. Read-only; nothing built.

Already-known items found again and not re-reported: CNT-1, CNT-6, CNT-7, CNT-8/MON-15, CNT-9, CNT-12, CHM-1,
SKL-4, H.8, A4.8, A5.4, P9.D1, P9.D6, P9.M7, DEVIATIONS 3, 20, 49, 53, 54, D.8.

---

### OVR2-2-1: MAW's "M&M6 Projectiles" restore drives elemental monster missiles past the engine's hit function: no special attack, no Pain Reflection, random target — ours keeps all three
Severity: P2
Confidence: confirmed for the special attack and the target (read both sides); plausible for Pain Reflection and
hit recovery (engine side read in OpenEnroth, not in MM8)
MAW: `General/zzMaw-Monsters.lua:3809-3829, 3850-3883, 4474` — every tick, a monster-owned missile object with
`Spell == 0` of type 500/505/510/515/535/540/555/1010 (Air, Earth, Fire, Water, Light, Dark, Energy/laser, Fire
Bolt) is swapped to one of MAW's new ObjList rows 712-740 (`Data/Tables/ObjList.txt:541-585`). The setting
`restoreProjectiles` defaults to ON (`General/zz_Maw-initialize.lua:538`) and only multiplayer skips it. On impact
`events.PlayerAttacked` (`:3884-4008`) sets `t.Handled = true`, picks the target itself (uniform random conscious
member; Fixator: lowest full HP), runs its own Cover and Retaliation, and calls `DoDamage(10000, Attack1.Type)` for
the pipeline to recompute. With `Handled`, `Core/events.lua:2628-2632` never calls the engine's hit function, so for
these missiles: the monster's special attack (`Bonus`) never lands, Pain Reflection does not reflect, the engine's
recovery-after-hit is not applied, and the damage is attack 1's unless only attack 2 carries a missile
(`MonsterAction` 0/1 at `:3891-3894`, `Modules/MawCore/Damage.lua:1702-1724`). The pipeline itself (`damage-recompute`,
boss affixes, map affixes, legendaries) applies no `mon.Bonus` condition (grep of `Damage.lua`).
OpenYAMM: `shouldApplyMonsterSpecialAttack` (`game/gameplay/GameplayCombatController.cpp:1028-1050`) lands the special
attack on every Attack1 projectile with `spellId == 0`, whatever the missile token; `applyPainReflection` runs on
every damaged member (`:2090`); the target is chosen by the monster's preferences unless
`MawCombatRules::monsterAttackTarget` (Fixator only, `MawCombatRules.cpp:2592-2615`) overrides it. 57 rows of
`engine/data_tables/monster_data.txt` have an Attack1 missile token in {Air, Earth, Fire, Water, Light, Dark, Ener}
and a special attack, e.g. Blood Titan (Dead), Tolberti / Robert the Wise / Mega-Dragons (Eradicate), Lich King and
Evil Eyes (Insane), Manticores and Wyrms (Poison), Devil Workers/Warriors (Disease), Titans and Red Dragon (break
armour/weapon), Floating Eyes (Asleep). In MAW none of these ranged hits gives the condition; in ours they do, at
level × strength % (and D.20's Doom-rolled specials also land through these missiles in ours, never in MAW).
Not covered by: DEVIATIONS 20 (unifies only the Cover rule), GAPS L3.5 (homing), D.20; COMBAT_SPEC.md §7.1 and
COMBAT.md:709 describe the random target but not the lost special attack; README.md:469 and the patch tool's
`NOT_MAPPED` treat ObjList 700-743 / SFT as visual only.
Suggested fix: decide with the user (it is a side effect of a cosmetic MAW setting, but it is how MAW plays by
default). To match MAW: a `CombatRules` hook, MAW override true for monster non-spell projectiles whose token maps to
objects 500/505/510/515/535/540/555, that skips the special attack and Pain Reflection and picks a uniform random
conscious member (Fixator kept). Otherwise record a DEVIATIONS row ("special attacks land through elemental
missiles").

### OVR2-2-2: MM7 Arena (Page to Lord) collapses to Red Dragons at MAW party levels; MAW's 12-nearest-types fallback is not ported (extends CNT's checked list)
Severity: P3
Confidence: confirmed (read both sides and the data)
MAW: `General/AdaptiveMonstersStats.lua:983-995` comments out MMMerge's `GenerateArenaMonster` handler (its
party-level list, reference `AdaptiveMonstersStats.lua:937-1000`), so the engine's own draw runs: types whose Level
lies in the tier's range from the party's highest level (Page L/2..L, Squire L/2..1.5L, Knight L/2..2L, Lord L..2L,
all clamped to 2..100). `Modules/MawCore/Fixes.lua:87-107` with `Engine.lua:280-311` then replaces an empty draw by
the 12 types nearest to the range (random tie-break), from which the engine draws up to 6.
OpenYAMM: `generateArenaChallenge` (`game/gameplay/ArenaRuntime.cpp:74-95`, shared by both rulesets) uses the same
clamped ranges over unscaled table levels and has no fallback. MAW characters pass level 100 and 200: from the
highest member's level 100 a Lord bout, and from 200 every tier, has the range 100..100, and the only arena-eligible
table monster of 7d05's id range 199-474 at level 100 is Red Dragon (225; Mega-Dragons 460-462 are NoArena,
`bolster_monsters.txt`). Every bout is then 6-20 Red Dragons. CNT's checked list says the fallback "does not apply
because OpenYAMM's arena reads unscaled table levels and refuses an empty draw"; the draw is not empty, it is one type.
Not covered by: no related row (DEVIATIONS 50 is the Endless Arena).
Suggested fix: when the range yields fewer than 6 (or 12) types, add the types nearest to the range as MAW's fallback
does; at least under MAW (a Standard party past level 100 hits the same collapse, which would need the user's call).

### OVR2-2-3: The bounty target is not marked on the map
Severity: P3
Confidence: confirmed (read both sides)
MAW: `General/BountyHunt.lua:41-57, 224-231, 259-263` — each town's entry keeps a free `Map.Notes` slot; on spawning
the hunt it activates a note "Bounty" (Id 9999) at the spawn point, and the target's death clears it.
OpenYAMM: `performBountyHuntInteraction` / `MawMonsterRules::spawnBountyTarget` (`BountyHuntRuntime.cpp:385-405`,
`MawMonsterRules.cpp:1164-1220`) add no map note; `Party::setJournalMapNote` exists.
Not covered by: MON-15, CNT-8 (other bounty details), no DEVIATIONS/GAPS row.
Suggested fix: under MAW, write a journal map note "Bounty" at the spawn point with the entry and remove it when the
entry is marked done (or dropped).

### OVR2-2-4: Bounty texts name the table monster, not the boss MAW spawned
Severity: P3
Confidence: confirmed (read both sides)
MAW: `General/BountyHunt.lua:216-218` stores `Entry.MonName = Game.PlaceMonTxt[Hunt.NameId]`, the boss's own name
"<affix> <monster>" (`zzMaw-Monsters.lua:3067-3068`, e.g. "Omnipotent Thunder Lizard"), and every hunt and reward
text prints it (`:167-185, 243`); the kill credit compares the same name (`:255-258`).
OpenYAMM: `bountyHuntTargetText` / `bountyHuntRewardText` (`BountyHuntRuntime.cpp:446-481`) print `stats.name` of the
target id, so the town hall never says which of the 6-16 same-family monsters is the bounty or that it is
Omnipotent.
Not covered by: MON-15 (kill credit by name), no text row.
Suggested fix: keep the spawned boss's display name in the entry (a named global var beside `.MonsterId`) and print it
in the MAW texts.

### OVR2-2-5 (question): Road to Insanity withholds a finished bounty while another town's is open — MAW quirk not ported, no row
Severity: P3
Confidence: confirmed (read both sides)
MAW: `General/BountyHunt.lua:150-156` checks for another town's open bounty this month before looking at this town's
own entry, so with town A's bounty done but unclaimed and town B's open, A's town hall names B's hunt and does not
pay until B's target is dead.
OpenYAMM: `performBountyHuntInteraction` (`BountyHuntRuntime.cpp:330-367`) asks `bountyElsewhere` only when this town
has no entry for the month, so A pays at once.
Not covered by: P9.I8, MON text, DEVIATIONS checked.
Suggested fix: probably keep ours (MAW's order looks unintended) and add a DEVIATIONS row; or move the check first to
copy MAW.

---

## Doc notes (no finding)

- DEVIATIONS 54 groups d07 under "lose their quest checks"; MAW's only d07 change is that wererat group 8 is no longer
  made visible when the wererats turn hostile (`Maps/d07.lua:21` commented). MAPS_CONTENT.md:457-459, 524 and
  UI_CONTENT.md:332 describe it correctly; the DEVIATIONS wording could follow them.
- README.md:469 and `NOT_MAPPED` ("ObjList/SFT not ported: projectile sprites") are right for the tables themselves;
  OVR2-2-1 is the gameplay side of the same MAW feature.

## Checked and matching

Per-file enumeration (hunks after CR/whitespace normalisation; "drift" = MMMerge version difference, not MAW):

- **Global/ExtraArtifacts.lua** (MAW ships it empty, commit e63a8130; the effects moved to MAW's own
  `zzzMaw_Artifacts.lua` / `zzMaw-Items.lua`): wear conditions, buffs, immunities, attack speed, Cycle of Life, Ethric's
  drain, on-hit table — all verified by ITM (ITM.md:507-524; ITM-A5 is Medusa's Mirror). Dropped with the file and
  checked here: artifact uniqueness (`vars.GotArtifact`, ItemGenerated/ArtifactGenerated remap to 177-186, two-year
  recount) — `MawItemRules::rollEnchantments` (MawItemRules.cpp:924-952) never consults found artifacts and
  `levelSevenGivesRareItem` is false, so Standard's uniqueness does not leak; Hades' flat −3 HP/tick and the flat
  HP/SP regen of artifacts and specials — `applyStandardItemEffects` restores the regen fields after Standard's
  effects (MawItemRules.cpp:470-490); Ullyses' object 3030 arrows — Standard OpenYAMM never had them, MAW drops them:
  same; the min attack delay 30 (5 for blasters) — MAW recomputes the delay (CMB area).
- **General/ExtraEvents.lua**: MAW 0905eac4 (Space on facets above 8191, a 16-bit object-ref fix) — engine only, n/a;
  the other hunks (SkillBySpell for 135/137, temporary spell-skill override, `>=` vs `>` count, u2/u4 store) are drift:
  MAW's b37afa78 kept an older copy to preserve `PlayerCastSpell`. Nothing to port.
- **General/BountyHunt.lua**: reward round(table level + bank(4)) × 100, map name in the Insanity text, Insanity one
  open bounty, "clear the area COMPLETELY first" gate, `monTbl` target, `mawBounty` level, boss + 5-15 escorts at
  55/30/15, speed 350, group 2, NPC 0 hostile, reputation −ceil(gold/2000), award 44 — match (`MawMonsterRules.cpp:
  1145-1225, 1368-1380`, `BountyHuntRuntime.cpp:270-344`). Boss spawn has no tier weights, so it is the C id itself
  (`GameplayMonsterSpawn.h:14-17`). New: OVR2-2-3, -4, -5; known: MON-15/CNT-8, MON-3 (completion never cleared).
- **General/AdaptiveMonstersStats.lua**: MAW SETTINGS page with the bolster regulators commented (DEVIATIONS 3/137);
  `SpellChance > 0` guard dropped and `PrepareMapMon` only at table FullHP — dead with bolster off (MAW forces
  `UseMonsterBolster = false`, zzMaw-Monsters.lua:2133-2137; D.8); arena handler commented — OVR2-2-2; the PlayerAC
  penalty hook changes (`NewCode` vs `NewCode+2`, slot guard) — bolster-only engine code.
- **General/MenuExtraSettings.lua**: mode spinner (Normal/Doom/Insanity/Madness/Austerity), new-game setup (5000 gold
  set, 10000/count XP, Madness level-1 reset; Austerity gets neither), mode reset on menu actions 124/132, bolster
  slider 0-250 step 50 with MAW names, free progression in the bolster tumbler's place — CHM (CHM.md:14-129), P9.D1,
  DEVIATIONS 1-3. Our setup gives 5000 by `addGold(5000 - gold)` (MawExperienceRules.cpp:430).
- **General/ZombiePlayers.lua** (MAW c9e24546/0e0bcca4/ae83130a, portrait and voice restoration after a cure,
  creature zombie faces 68/70/76): OpenYAMM swaps no portrait on the Zombie condition at all
  (`PortraitEnums.cpp:302-304`), so neither the base swap nor MAW's fix applies.
- **General/NPCMercenaries.lua**: class kinds by continent (matches `MawClassRules::mercenaryClassKinds`,
  MawClassRules.cpp:983-995), skill points Σ(4+⌊i/10+1⌋) (SKL), Master of Elements kind cap 31 (engine table bound,
  n/a), gear half-enchant and `BonusExpireTime = 0` (SKL-4, H.8), no mercenaries in Beyond Madness (P9.M7,
  `offersMercenaries`), the continent-switch bugfix and the default {2, 6, 14} removed (ours keeps {2, 6, 14} only as
  an unreachable fallback: the MAW lists are never empty), LastClass storing kinds (Standard OpenYAMM has no
  recent-class exclusion in either ruleset; MAW's version also mutates its global list — not worth porting).
- **General/NPCFollowers.lua**: hiring refused in the Doom family except houses 1466/1486, both hire topics renamed —
  `MawClassRules::followerHireRefusal` (MawClassRules.cpp:969-981), `doomMode` set for Doom, Insanity and Madness
  (MawBalanceModel.cpp:323-331).
- **Global/NPCFollowersSkills.lua**: follower skill bonuses take the max — `followerSkillBonusesStack` false
  (MawSkillRules.cpp:1289, Party.cpp:7207); the `vars.NPCFollowers` nil guard is Lua-only.
- **General/MiscTweaks.lua**: Unarmed GM dodge off (`MawCombatRules::characterEvades` has no Unarmed roll,
  MawCombatRules.cpp:3362-3382), MM7 regeneration and Meditation SP off (`MawSkillRules` overrides
  `regenerationHealthPerSecond` / `meditationSpellPointsPerTick`), catalyst mixing = A4.8
  (`MawPotionRules::catalystMixPower`, MawPotionRules.cpp:73-83, same formula and caps), random MM6 music off (no
  Standard counterpart).
- **General/SpellsTweaks.lua**: Slow / Mass Distortion always land (MAW's CC system and Mass Distortion share replace
  the engine roll; SPL checked list), philosopher-stone Enchant Item removed (OpenYAMM has none).
- **Global/Quest_DragonHatchling.lua**: feed/hungry/days-left texts and the release topic ported in
  `Global_maw.lua:405-469` (texts match; known issues CNT-1, CNT-6, DEVIATIONS 53, N8.5); the dialog redraw is a
  UI-engine fix; the grown-dragon-to-inn part does not apply because OpenYAMM's base makes the grown dragon follower
  NPC 396, not a roster character (MAPS_CONTENT §4.5).
- **Maps** — 24 MAW overrides of base scripts, each checked against its overlay or a row:
  7d06 (397 skeletons 3 A + 1 B, once: `7d06_maw.lua`, tiers as pseudoSpawnpoint's powerChances), 7d24 (CNT-7,
  CNT-12), 7d29 (CNT checked, CNT-12), 7d34 (DEVIATIONS 54), 7d37 (CNT-7), 7out01 (CNT-12, inert without Redone),
  7out02 (CNT checked, CNT-7, CNT-12), 7out05 (CNT-9, DEVIATIONS 52), BrBase (multiplayer sync plus the commented
  monster level filter: OpenYAMM has no Breach maze or map, README.md:432), d07 (DEVIATIONS 54, see doc note), d19
  (CNT-12), out01 (CNT checked), out02 (teleporters 2666/1777 → DEVIATIONS 49, `out02_maw.lua` and its scene overlay),
  outb1 (well and shrine, CNT checked), outb2, outb3 (event 92: Doom family closed, `difficulty > 2` = bolster > 100,
  member 0 base level 255 — matches), outc1, outc2 (shrine 261 compared line by line: QBit 1230/1235, +10 then +3),
  outc3, outd1, outd3, oute2, oute3 (shrines, 104, teleporters: CNT checked, DEVIATIONS 49, 55), pyramid
  (DEVIATIONS 54). The 13 MAW-only map scripts are outside this slice.
- **Data/Tables/Spells2.txt**: composed `engine/data_tables/spells.txt` + `patches/spells.txt` +
  `content/spells_patch.txt` equals MAW's Spells2 in all 8 mana/recovery columns for every spell (script comparison);
  the only differences are MAW's Lua costs on top (Chain Lightning = spell 18 at Master 20 / GM 30, Mind Charm 60 at 5,
  A7.6/A7.7). The generator reads `tables:Spells2.txt` against our base (generate_ruleset_patches.py:101).
- **Data/Tables/ObjList.txt**: no speed, lifetime or flag change to any existing object (only the Arrow SFT group's
  case); rows 700-707 (unused by MAW's Lua) and 708-743 (MM6 projectile and explosion sprites) are new — visual, not
  read by the generator (`NOT_MAPPED`); their gameplay side is OVR2-2-1.
- **Data/Tables/SFT.txt**: scale changes of air07, earthX10, mslX04, mslX05, the `mcryst` crystal light radius 64 → 150-300,
  and the new n*-groups — visual only, not read (`NOT_MAPPED`).
