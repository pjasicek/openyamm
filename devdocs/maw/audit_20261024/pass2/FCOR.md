# FCOR: function inventory of MAW's core, damage, class, alchemy, map and global scripts

Second-pass audit, area FCOR, method: function inventory. Every function, event handler, pipeline stage, scheduler/timer
task, engine patch and table-level statement with side effects in the files below was listed and matched against
OpenYAMM (`game/rules/maw/*`, `assets_dev/rulesets/maw/*` and the shared code they hook), or against the DEVIATIONS,
GAPS or first-pass row that already covers it. Pure UI drawing (tooltips, stats-page rendering) and
multiplayer/online branches are marked "skipped".

MAW `ef23ee17` files: `Scripts/Modules/MawCore/` Damage, DamageState, Pipeline, Formulas, MonsterHP, Classes, Engine,
Fixes, Scheduler, Save; `Scripts/General/` zzClasses, zzAlchemy, zzMaw-Maps, zzMaw-Stats, zzzMaw_Experience,
zzMaw-Survival, zzMaw-Timers, zz_Maw-initialize, zMaw-hooks, zzzzzMaw_Core, zzMaw-TownPortalClickFix;
`Scripts/Global/` zzzzzMaw_Damage, zzMaw_Arena, zzMaw_DimensionalMapsQuest, zzMaw_Mapping, zzMAW_MoveTrainers,
zzMAW_PotionQuests, zzMAW_DruidCircletQuest, GLOBAL.

Read-only; no builds or tests were run. The work was split into five slices (A: damage pipeline, B: classes, formulas,
engine patches, hooks, timers, C: alchemy, survival, initialise, experience, D: maps and stats, E: Global scripts);
finding numbers keep each slice's range (A 1-19, B 20-39, C 40-59, D 60-79, E 80-99). The working tree changed during the
audit: `MawCombatRules.cpp` line numbers drifted by 30-60 lines, so references also name the function or stage.
FCOR-2-1 and FCOR-2-80/81 were re-checked by hand on both sides after the slices finished.

## Summary

| Id | Sev | Conf | Finding |
|---|---|---|---|
| FCOR-2-80 | P2 | confirmed | SPL-2 is a false positive: `zzMaw_Mapping.lua:25-58` resets `buffPower` to base 20 on every map load without affix 33, so live MAW uses 20 for the resistance auras and Day of Protection; our 20 is right. Withdraw SPL-2 and keep HANDOFF's "live base 20" decision |
| FCOR-2-1 | P2 | confirmed | Pain Reflection on a monster returns the party's full hit to the active member (`OutdoorWorldRuntime.cpp` ~17350, `IndoorWorldRuntime.cpp` ~15826); MAW returns `Result^0.85` (Damage.lua:1593-1598) |
| FCOR-2-81 | P2 | confirmed | Endless Arena (`d42_maw.lua:25`, `CheckMonstersKilled(Any)`) never completes while a party summon (ally 999) is alive; MAW skips allies (zzMaw_Arena.lua:226) |
| FCOR-2-2 | P3 | plausible | The party's own area spells hitting the party take trap/Standard damage, not MAW's dice × (1 − d/512) at the caster's level |
| FCOR-2-3 | P3 | question | Boss on-hit affixes fire on dodged hits in MAW (pipeline quirk); we skip them; needs a decision or DEVIATIONS row |
| FCOR-2-4 | P3 | question | Legendary 30 death threshold: MAW's code `max(HP, SP) × eff`, ours follows the text `max(HP, SP × eff)` |
| FCOR-2-5 | P3 | plausible | Elementalist learn-by-casting: MAW counts every spell 1-44 hit on a hostile (zero damage too); ours 19 offensive spells with damage, no hostility check |
| FCOR-2-6 | P3 | confirmed | Regenerating boss hit counter counts every HP drop (monster hits, DoT) and is not saved |
| FCOR-2-20 | P3 | confirmed | Extends CLS-4: the Elementalist idle window comes from whichever spell's recovery was last computed (stats page, Workbench preview, leech floor, utility casts) |
| FCOR-2-21 | P3 | confirmed | Assassins pay energy and build combo points/Subtlety stacks on non-hostile targets (friendly fire on); MAW requires a hostile target (Classes.lua:396) |
| FCOR-2-40 | P3 | confirmed | Dimension affix 9 (summon on death) only on party-member kills, and also for risen/reanimated monsters and rewardless maps |
| FCOR-2-41 | P3 | confirmed | Potion condition immunities (224-227, 239, 246) block conditions from every source (Haste-end Weak, travel, MAW's own Weak); MAW only blocks monster attacks |
| FCOR-2-60 | P3 | confirmed | Worn HP/SP regeneration specials' ~1 % per 5-minute regeneration tick (zzMaw-Stats.lua:670-689) is missing; GAPS A2.3's "SP specials off" text is wrong |
| FCOR-2-61 | P3 | question | Road to Insanity/Beyond Madness: MAW's no-refill BeforeLoadMap likely cancels a dimension map's refill too; we refill (`mapRefillForced`); add a DEVIATIONS row |
| FCOR-2-82 | P3 | confirmed | The Druid Circlet reward amulet arrives unidentified (MAW identifies it in an ItemGenerated hook) |

## Findings

### FCOR-2-1: Pain Reflection on a monster sends the full hit back, unmitigated (MAW: `^0.85`)
Severity: P2
Confidence: confirmed (read both sides)
MAW: `Damage.lua:503-511` (`stage_painReflectionFlag`) flags a hit on a monster whose Pain Reflection buff (monster
buff 19) is up; the engine's reflected hit then enters the player pipeline, where `pstage_damageRecompute`
(`Damage.lua:1593-1598`) replaces it with `Result^0.85` (Result being the engine's resisted value) and returns; mana
shield, legendary 15 and Divine Protection still run after it. COMBAT_SPEC.md §7 (line 1098) specifies the same.
OpenYAMM: `OutdoorWorldRuntime.cpp:17350-17355` and `IndoorWorldRuntime.cpp:15826-15831` call
`Party::applyDamageToActiveMember(damage, "pain reflection")` with the full damage the party just dealt (MAW-sized,
monster-HP scale), with no `^0.85`, no resistance and no ruleset hook; only `absorbCharacterDamage` runs
(`Party.cpp:3023-3044`). Monsters that cast Pain Reflection (Master Necromancer, Lich King, Queen of the Dead and
others in `monster_data.txt`) can kill the active member with one reflected blow (a 5000-damage hit returns 5000
instead of ~1400). The reflection also goes to the active member, not the member who struck (as at HEAD; MAW's
engine returns it to the attacker).
Not covered by: DEVIATIONS 71 (shields on every hit), CMB-9 (Thorn/Reflecting order); the Thorn/Reflecting/affix-5/6
reflects do apply `^0.85` (`MawCombatRules.cpp:2810-2850`), pain reflection was left out. No GAPS row.
Suggested fix: a combat-rules hook for reflected damage (Standard: identity; MAW: Standard resistance then `^0.85`, as
`applyPartyHitEffects`' `reflect` lambda does), used by both worlds' pain-reflection branch, aimed at the striking
member.

### FCOR-2-2: The party's own area spells hitting the party take trap damage, not MAW's friendly-fire formula
Severity: P3
Confidence: plausible (the source resolution was traced by reading; needs a runtime check)
MAW: `Damage.lua:1607-1621` — a party spell (1-132) that hits a party member (own Fireball/Meteor too close) deals
`(add + Σ SpellSkill rolls of the Ascension dice) × max(1 − distance(party, object)/512, 0)`, mitigated by
`calcMawDamage` at the caster's `LevelBase`, no crit or Intellect. Party arrows (Spell 133) keep the engine value.
COMBAT_SPEC.md:1101-1104 specifies it.
OpenYAMM: a party projectile's area impact hits the party with `projectile.damage`, no distance falloff
(`GameplayProjectileService.cpp:1555-1571`), recorded as a `PartyProjectileImpact` (`IndoorWorldRuntime.cpp:7262-7271`,
`OutdoorWorldRuntime.cpp:14537-14545`). The source does not resolve to a sized monster, so `mawMonsterHit` is false
and MAW's "mitigation" stage (`MawCombatRules.cpp:950-975`) replaces it with `trapDamage` (model damage at the party's
level × Perception) indoors and for non-physical, non-water kinds outdoors; outdoors a physical or water splash takes
Standard mitigation. Neither matches MAW.
Not covered by: GAPS A1.6/L3.4 (traps), A1.13 (friendly fire on monsters); no row for party-on-party.
Suggested fix: in the MAW damage-to-character pipeline, recognise a party-sourced hit (carry the caster index and
spell) and apply the spec's formula; zero beyond 512 units.

### FCOR-2-3: Boss on-hit affixes on dodged hits (question: MAW quirk)
Severity: P3
Confidence: confirmed (read both sides)
MAW: `Damage.lua:1659-1676` — a Grandmaster Dodging dodge (any monster hit) or a Speed dodge of a spell or missile
sets `Result = 0` and returns without `Stop`, so `pstage_bossAffixesPlayer` (`:1803-1841`) still runs: Venomous,
Plagueborn and Fixator apply their condition, Summoner calls a family member, Swapper swaps and Puller pulls on a hit
the member dodged.
OpenYAMM: `GameplayCombatController.cpp:1915, 1974` skip an evaded member entirely; `applyMonsterHitEffects` runs only
for members with `applyDamageToMember` true (`:2069-2101`).
Not covered by: DEVIATIONS 10 (immunities), dev 74 (Swapper), CMB-20; no row.
Suggested fix: decide with the user; most likely keep ours and add a DEVIATIONS row ("a dodged hit carries no boss
affix"), since MAW's behaviour falls out of pipeline order rather than design.

### FCOR-2-4: Legendary 30 death threshold: MAW multiplies the larger of HP and SP by the efficiency (question)
Severity: P3
Confidence: confirmed (read both sides)
MAW: `Damage.lua:1911-1916` — `fullHP = max(FullHP, FullSP) × manaShieldManaEfficiency(pl)`: the efficiency (up to 5)
multiplies HP too when HP is the larger. The legendary's text (`zzMaw-Items.lua:1595`) says "SP multiplied by mana
shield efficiency instead, if higher".
OpenYAMM: `MawCombatRules.cpp:3302-3313` — `max(FullHP, FullSP × efficiency)`, the text's reading. A holder with HP
1000, SP 500, efficiency 5 dies below −2500 here, below −5000 in MAW.
Not covered by: CMB "checked and matching" lists the L30 threshold as matching; no DEVIATIONS row.
Suggested fix: user decision (MAW code or its text); record the choice as a DEVIATIONS row if the text stays.

### FCOR-2-5: Elementalist learn-by-casting differs on non-damaging and friendly hits
Severity: P3
Confidence: plausible
MAW: `Damage.lua:156-196` — progress is added for every hit of an Elementalist's spell 1-44 on a hostile-looking
monster (`Hostile or ShowAsHostile`), whatever its damage: Stun (34) included (the pipeline sees it, `:334-357`), a
fully resisted or zero hit included; non-hostile monsters give none.
OpenYAMM: `MawCombatRules.cpp:3041-3055` adds progress only for the 19 spells of `mawElementalistOffensiveSpell`
(no Stun) and only when `hit.damage > 0` (`applyPartyHitEffects` returns early at its top), and does not look at
hostility (with the friendly-fire preference on, hits on peasants teach).
Not covered by: GAPS A6.9 (stack reset), DEVIATIONS 26 (stacks/rotation; the offensive list is about stacks), CLS-4.
Suggested fix: feed progress from the hit before the damage gate, for any spell 1-44 on a hostile target.

### FCOR-2-6: Regenerating boss: hit count kept per world instance and counted from every HP drop
Severity: P3
Confidence: confirmed (read both sides)
MAW: `Damage.lua:944-954` counts party hits only (`t.Player`) per monster in `mapvars.regenerating` (saved with the
map); `zzMaw-Monsters.lua:3585-3600` regenerates `1 % × 0.99^hits / (1 + L/50)` per tick once hit.
OpenYAMM: `MawMonsterRules.cpp:1706-1730` counts each frame in which the boss's HP fell (monster-on-monster hits,
damage over time, several hits in one frame count once) in `m_bossTracks`, a runtime map cleared whenever the world
instance changes (`:1544-1549`) and never saved: after a load a wounded Regenerating boss stops regenerating until hit
again, and its 0.99^hits slowdown restarts.
Not covered by: MON "checked" lists the formula only; no row.
Suggested fix: count in `applyPartyHitEffects` (party hits) into `ActorRulesetFacts` (saved with the actor), as the
spear and legendary-29 stacks are.

### FCOR-2-20: The Elementalist's idle window uses whichever spell's recovery was last computed, not the last offensive cast
Severity: P3
Confidence: confirmed (read both sides; the size of the effect depends on what the player has open)
MAW: `Modules/MawCore/Classes.lua:533`. `eleCastRotation` sets `eleTimer = Game.Time + max(getSpellDelay(pl, spell)*4,
128)` only inside the offensive-cast branch (rotation on, spell in `eleOffSpellsOut/In`). Nothing else writes
`eleTimer` except the decay itself (`Classes.lua:300-315`). The window is therefore always that of the last offensive
spell cast.
OpenYAMM: `MawSpellRules::baseRecoveryTicks` (`game/rules/maw/MawSpellRules.cpp` ~586-596) writes
`runtime.elementalLastDelayTicks = stacked` every time it is evaluated for an Elementalist, whatever the spell and
whatever the purpose. `MawClassRules::update` (`MawClassRules.cpp:418`) reads it as the window. Other callers of the
same path change the window:
- `mawPowerReport` (`MawCombatRules.cpp` ~1741, "spell" row for the quick or attack spell). It is called by the stats
  page's power rows (`MawSkillRules.cpp:635, 1307`) whenever that page is drawn, and by the Workbench's before/after
  preview (`MawItemRules.cpp:2285`).
- `MawCombatRules::spellRecoveryTicks` (`MawCombatRules.cpp` ~2887), used by the leech floor of every spell hit (~2954).
- `PartySpellSystem.cpp:1440`, for every cast, including non-offensive ones (Town Portal, Fly, buffs), which neither
  build a stack nor reset the idle clock (`MawSpellRules::afterCast`).

So with the stats page open, or after a utility cast, the window follows the quick/attack spell (which the rotation
keeps changing) or the utility spell, not the last offensive cast. The Workbench preview evaluates copies of the
character, so it also creates throw-away `m_classRuntime` entries keyed by the copies' addresses (see CLS-11).
Not covered by: extends CLS-4. CLS-4 covers the ×2.1333 factor and the late first halving, not where the delay comes
from.
Suggested fix: make `baseRecoveryTicks` free of side effects. Record the delay in `afterCast` for offensive casts (the
cast already has it as `baseSpellRecoveryTicks`), next to the existing `elementalIdleSeconds = 0`.

### FCOR-2-21: Assassins pay energy and build combo points and Subtlety stacks on non-hostile targets
Severity: P3 (only when the friendly-fire preference is on)
Confidence: confirmed
MAW: `Modules/MawCore/Classes.lua:396`. The energy payment, the combo point, the `AttackSpeedStack` and the reduced
crowd cut all sit under `if pl.SP>=manaCost and mon.ShowAsHostile`. A blow on a monster that is not shown hostile pays
nothing, builds nothing and returns the whole `assassinDamage`, so the Assassination bonus is fully removed. The kill
refund (`:388-395`) is outside that test.
OpenYAMM: `MawCombatRules::applyAssassinHit` (`MawCombatRules.cpp` ~3196-3230) pays the cost, rolls the refund and adds
the combo point and Subtlety stack whenever `spellPoints >= cost`. `resolveCharacterAttack` (~1406-1413) applies the
crowd share on the same test only. Neither looks at hostility. With friendly fire off, a non-hostile hit does 0 damage
and `applyPartyHitEffects` returns early, so the gap only shows with the preference on (A1.13). In that case, hitting a
peasant or a guard drains energy, builds finisher points and speed stacks, and keeps the bonus.
Not covered by: GAPS L6.2 (crowd cut, done), A1.13 (friendly-fire preference), DEVIATIONS 28 (paid by landed blows),
CLS-7 (refund outside the payment).
Suggested fix: pass the target's hostility in `PartyHitOnMonster` and `CharacterAttackOnMonster`. For a non-hostile
target, skip the payment, the stacks and the combo point, and use share 1.0. Keep the kill refund.

### FCOR-2-40: Dimension affix 9 (summon on death) fires only on kills by a party member, and also for risen monsters
Severity: P3
Confidence: confirmed
MAW: zzAlchemy.lua:1118-1148. The handler is `events.MonsterKilled`, so it runs on every monster death: a kill by a
party member, a summoned ally, a reanimated or charmed monster, another monster's spell, a damage-over-time effect or
the environment. It returns first for reanimated monsters (`Ally == 9999`), for risen Nightmare monsters
(`NameId > 300`) and, in Beyond Madness, for bounty maps, zarena, d42 and 7d05. Only after those checks does it roll
`getMapAffixPower(9)/100` to spawn a family member (tier weights 55/30/15, radius 128).
OpenYAMM: MawCombatRules.cpp:2807-2824 rolls the summon inside `applyPartyHitEffects`, which only the party's own hits
reach (GameplayCombatController.cpp:1697-1722, GameplayActionController.cpp:1154). So:
(a) Monsters killed by summons, allies, other monsters or periodic damage never summon in a dimension run.
(b) A risen monster killed on a Nightmare or Doom dimension map does summon (no `pFacts->risen` check), and so does
a reanimated one.
(c) There is no check for Madness's rewardless maps.
Not covered by: DEVIATIONS 59/60 (affix bugs and unported affixes), MON-11 (revival of affix-9 summons, the opposite
direction), ALC-12 (reagents for risen monsters). No row covers which deaths trigger affix 9.
Suggested fix: roll the summon where the world records a monster's death (the same place that rolls the corpse's
crafting drops, `MawMonsterRules::lootWithoutCorpse`/`corpseLoot`, which runs for every death). Skip it for
`facts.risen`, reanimated monsters and `madnessRewardlessMap`.

### FCOR-2-41: Potion condition immunities block the condition from every source; MAW blocks only monster attacks
Severity: P3
Confidence: confirmed
MAW: zzAlchemy.lua:356-417. The immunities of potions 224-227, 239 and 246 (`vars.PlayerAlchemyBuffs`) are checked
only in `events.DoBadThingToPlayer`, the engine's monster special-attack path. Drinking also cures the condition
(zzAlchemy.lua:165-171). Conditions the engine sets directly still land while the potion lasts: Weak when Haste wears
off, after travel, after a resurrection or from days without rest; Asleep; Unconscious from other causes.
OpenYAMM: the potion's timed `Immunity` effect (InventoryItemUseRuntime.cpp:433-438) is read by
`hasConditionImmunity` (Party.cpp:1094-1109). `Party::applyMemberCondition` (Party.cpp:6755-6762) checks that
immunity for every caller, so an Energy Potion (224) or Divine Restoration (246) also prevents:
- Weak from Haste ending (Party.cpp:6251, 6289);
- Weak from travel (TravelRuntime.cpp:48);
- Weak from days without rest (Party.cpp:3681);
- the Weak a resurrection leaves (Party.cpp:6860);
- Weak from MAW's own `MawCombatRules.cpp:3240`.
246's Unconscious immunity also blocks the self-knockout of the 70 % failed-stun item (GameplayActionController.cpp:1416).
HP-based unconsciousness is not affected (`updateMemberIncapacitatedCondition` sets it directly). This mainly matters
with SPL-4: under MAW, a party whose held Haste lapses becomes Weak, but with 224 or 246 it does not.
Not covered by: DEVIATIONS 30-34 (other potion behaviour), GAPS A4.x, L7.x, ALC checked list ("immunities and cures …
match", which compares lists, not sources).
Suggested fix: either add a DEVIATIONS row ("potion immunities block the condition from every source"), or check the
potion part of the immunity only on the monster-attack path (`MawCombatRules::blocksMonsterCondition` /
the special-attack application) and keep `applyMemberCondition`'s immunity to items and permanent ones.

### FCOR-2-60: The 1 % per regeneration tick from worn HP and SP regeneration specials is not ported
Severity: P3
Confidence: confirmed (read both sides)
MAW: `zzMaw-Stats.lua:670-689` (`events.Regeneration`, the engine's 5-game-minute regeneration tick, the same event
MAW's auto-repair uses, `zzMAW-Skills.lua:1316`): for each worn item with special 37, 44, 50 or 54 the member gains
`max(1 % of full HP − 1, 0)` HP, and for each worn item with special 38, 47 or 55 `max(1 % of full SP − 1, 0)` SP, each
tick (the −1 offsets the engine's own +1, so each item gives about 1 % of the bar per tick, ≈0.1 %/s at 10 s a tick).
It comes on top of the continuous 0.2 %/s of `zzMAW-Skills.lua:1358-1362` (HP specials) and on top of the SP specials'
Meditation bonus (the commented-out block at `zzMAW-Skills.lua:1455-1459` only disables the continuous SP part).
OpenYAMM: `MawSkillRules::regenerationPerSecond` (`game/rules/maw/MawSkillRules.cpp:1024-1043`) has the continuous
0.2 %/s for HP specials and artifacts and SP only from the mana artifacts; the MAW 5-minute tick
(`MawCombatRules::updateArtifacts`, `MawCombatRules.cpp:2264-2399`) does auto-repair, Ethric's Staff and Cycle of Life
only. `MawSkillRules::regenerationHealthPerSecond` and `meditationSpellPointsPerTick` return 0
(`MawSkillRules.cpp:419-425`), so nothing else adds it. An "of Regeneration" item thus gives 0.2 %/s instead of about
0.3 %/s, and "of Mana"-type SP specials give no SP regeneration at all.
Not covered by: GAPS A2.3 (done) says "SP specials off", which reads only the zzMAW-Skills block; no DEVIATIONS row.
Suggested fix: on the existing 5-minute tick in `MawCombatRules::updateArtifacts`, add `max(0.01 × full − 1, 0)` HP per
worn special 37/44/50/54 and SP per worn special 38/47/55 to each member not dead or eradicated (affix 22 question: MAW's
handler does not apply it); correct the GAPS A2.3 text.

### FCOR-2-61: Question: in Road to Insanity and Beyond Madness MAW's dimension maps do not refill their target; we do
Severity: P3
Confidence: plausible (rests on MMExt calling BeforeLoadMap before the engine reads RefillDays, which MAW's own dungeon
reset also relies on)
MAW: `zzMaw-Maps.lua:959-966` sets the target's `RefillDays = 0` and loads it, but the insanity handler
`zzMaw-Maps.lua:80-86` (BeforeLoadMap) sets every map's `RefillDays` to 10^9 before the load, so in both modes an
already visited target (every pool map is a completed one, `getDimensionMapPool` 793-802) keeps its dead monsters; only
the affixes in `mapvars` change. The same handler is why the reset is refused there (`canResetDungeon` 183-188).
OpenYAMM: `MawMonsterRules::mapRespawnDays` returns 0 in both modes but `mapRefillForced` (`MawMonsterRules.cpp:1238-1291`)
still refills a dimension run's target, as its comment says ("a dimension map run still refills its target").
Not covered by: DEVIATIONS 63 (run lifetime), CHM rows; no row records the Insanity case.
Suggested fix: keep our behaviour (a dimension map into an empty cleared dungeon is useless) and add a DEVIATIONS row
"MAW bug: Insanity's no-refill override also stops dimension maps refilling".

### FCOR-2-80: SPL-2 is a false positive — live MAW resistance auras and Day of Protection use base 20, not 10 (extends SPL-2, refutes it)
Severity: P2 (prevents a wrong balance "fix")
Confidence: confirmed
MAW: `Global/zzMaw_Mapping.lua:25-58` — `events.AfterLoadMap` runs on every map load; when the map has no affix 33 it
reassigns the global `buffPower` table with Base 20 / Scaling 2 for 3, 14, 25, 36, 58, 69 and 85 (and the same values
as `zzMaw-Spells.lua:2670-2690` for every other id). `zzMaw-Spells.lua:2670` (General/, runs once at startup) is the
only other assignment, and its "halved base" 10 is overwritten at the first map load of every game. Nothing else
writes `buffPower` (grep: only `zzMaw_Mapping.lua:31` mutates entries, the affix-33 branch). So in play MAW's
resistance auras and Day of Protection are base 20.
OpenYAMM: `game/rules/maw/MawCombatFormulas.cpp:22-41` (`BuffPowers`, commented "The live buffPower table
(Global/zzMaw_Mapping.lua)") and every `mawAuraFlat(20, 2, ...)` call (`MawSpellRules.cpp:325-333, 1159-1180`,
`MawSkillRules.cpp:46`) use 20 — matching live MAW. HANDOFF §6 phase 5's "kept the live base 20 as MAW plays" is
correct.
Not covered by: SPL-2 (pass 1) asserts "no other assignment" and suggests changing to 10; AUDIT summary asks to
re-ask the user.
Suggested fix: none in code. Withdraw SPL-2 in `AUDIT_20261024.md`/`audit_20261024/SPL.md`; optionally note in
CLASSES_SPELLS_SPEC §3.3 / `data/buff_auras.yml` that the 10 is dead in MAW because `zzMaw_Mapping.lua` resets it.

### FCOR-2-81: Endless Arena never completes while a party summon or other ally is alive
Severity: P2
Confidence: confirmed (read both sides; runtime check advisable for which summons carry the ally mark)
MAW: `Global/zzMaw_Arena.lua:221-229` — the level counts as cleared when every monster is removed, a multiplayer
puppet, or `Ally == 9999` (the engine's mark for party summons). Summoned/reanimated allies never block the reward.
OpenYAMM: `assets_dev/rulesets/maw/events/maps/d42_maw.lua:25` uses `evt.CheckMonstersKilled(ActorKillCheck.Any, 0, 0,
false)`, which (`IndoorWorldRuntime.cpp:17730-17805`) counts every actor of the map, allies included; only `hp <= 0` or
invisible counts as defeated. A living party summon (Summon Wisp, Reanimate, a controlled undead, an Ascension
summon) keeps `cleared` false: the waves still come on the timer, but the final branch (`d42_maw.lua:26-33`, gold
L × 20000, `MawArenaBest`) never fires until the ally dies. The native arena already avoids this
(`ArenaRuntime.cpp:154-160`: "Party summons do not block victory", `actor.ally != 999u`).
Not covered by: GAPS A3.13 (map completion, d42 excluded), CNT-4/CNT-5, MON-4/MON-5, DEVIATIONS 50.
Suggested fix: a kill check that skips party allies (ally 999, as `ArenaRuntime` does), e.g. a hostile-only variant
of `CheckMonstersKilled` or an arena-specific query, used by `d42_maw.lua`.

### FCOR-2-82: The Druid Circlet reward amulet arrives unidentified
Severity: P3
Confidence: confirmed
MAW: `Global/zzMAW_DruidCircletQuest.lua:7-21` — the reward goes through the generator with an `ItemGenerated` hook
that sets `Identified = true` for that one roll.
OpenYAMM: `assets_dev/rulesets/maw/events/Global_maw.lua:398` `evt.GiveItem(5, ItemType.Amulet)` →
`createGrantedEventItem` (`EventRuntime.cpp:347-398`) → `ItemGenerator::generateRandomInventoryItem`, whose
`defaultIdentifiedState` (`ItemGenerator.cpp:17-32`) leaves items that need identification (amulets) unidentified.
Not covered by: no DEVIATIONS/GAPS row (CNT checked the quest's text, gold and experience only).
Suggested fix: identify the granted item for this topic (an `identified` flag on `evt.GiveItem`, or identify after
granting).

## Notes (no finding)

### Part A: MawCore damage pipeline
- extends CMB-14/CHM-2: nothing new; the death-seed mark (`Damage.lua:1568-1573`) runs on every player hit in MAW
  (CHM-2 already reports that ours marks monster hits only).
- Survival gates (`Damage.lua:960-965`, `1844-1849`): dead code in MAW (PHASE9_SCOPE.md line 15, 103).
- `stage_publish` (`MawMonsterDamage`) has a listener only in `Modules/Multiplayer` — skipped.


### Part B: function inventory of the MAW class, formula, engine-patch, hook and timer files

- **Timer cadence.** `zzMaw-Timers.lua` drives every MawTimer from `Game.Time` at 128 ticks per second, with a cap of 2
  seconds per frame and at most 2 steps per frame in real time (20 in turn-based mode). In OpenYAMM the rules' updates
  run only when actor AI runs (`app/GameSession.cpp:1040-1058`: not while the world is paused or during the party's
  turn-based phase). In real time the cadences are equivalent, either continuous with carries or the same intervals
  (table below). I did not check whether MM8's game clock advances during the party's turn-based phase, so I make no
  claim about turn-based regeneration and decay.
- **Map completion.** The check runs every 1 s in OpenYAMM (`MawMonsterRules::updateMonsters`); MAW checks every 10 s
  (`zzMaw-Timers.lua:92`). GAPS A3.13 records "checked every second". This only changes how quickly the completion is
  noticed.
- **`elementalBuffs`** (`zzMaw-Spells.lua:1046`, registered at `zzMaw-Timers.lua:94`) is dead code in MAW (`not
  x=="ON"`), as SKILLS_SPELLS_ALCHEMY.md:32-36 records. It is correctly not ported: the GM school party buffs, its
  vampire Preservation copy and the solo Torch/Wizard Eye are all inside the dead branch. The live vampire path is the
  one CLS-6 covers.
- **Arena fallback (`Fixes.lua` 5).** For MM7 (199-474) and MM8 (1-198), OpenYAMM's `generateArenaChallenge`
  (`game/gameplay/ArenaRuntime.cpp:58-118`) clamps the level range to 2..100, and the composed MAW monster table has
  level-100 types in both ranges (225, 460-462 and 72, 113, 150). So the empty pool that MAW's patch fixes does not
  happen. An empty pool only refuses with a message; it does not crash.
- **Recovery floor (`Fixes.lua` 2, 30 → 1).** MAW's attack delay (`mawCharacterAttackDelay`, set as
  `attack.recoverySeconds` in `MawCombatRules::resolveCharacterAttack`) bypasses Standard's `OeMinimumMeleeRecoveryTicks
  = 30` (`GameMechanics.cpp:29`), as the patch intends. There is no floor of 1, but a delay of 0 would need a speed
  bonus of about +19900 %, so this does not matter in practice.


### Part C: zzAlchemy, zzMaw-Survival, zz_Maw-initialize, zzzMaw_Experience, zzMaw-TownPortalClickFix

- zzzMaw_Experience.lua:198: on the very first kill of a game the bank's total level is 0, so MAW computes the member's
  level as min(calcLevel(exp), 0) = 0. `mawMemberKillExperience` (MawExperienceRules.cpp:127-128) clamps it to 1. This
  affects only the first kill, and the award is capped at (level+1)×1000 anyway, so it is not reported.
- zzAlchemy.lua:641-652 (`ItemGenerated`: reagent level = party level / 5) is dead in MAW. zzMaw-Items.lua:1097-1122
  loads later (`zzMaw-Items` sorts after `zzAlchemy`) and overwrites the reagent's Bonus with
  round(min(drop level, total level)/3), which is what we port (GAPS A4.2).
- Event experience continent: MAW uses `MapOfContinent`, which falls back to the current Town Portal switch for a map
  with no continent. We use the map's `mergedContinentId`, normalised from 0 to 1 (EventRuntime.cpp:76-79). This
  matters only for maps without a continent; not reported.
- `Game.PatchOptions.FixMonstersBlockingShots=true` (zz_Maw-initialize.lua:303) is repeated in MawCore/Fixes.lua:67-78,
  which part B of this audit covers.


### Part E: MAW Global scripts (function inventory)

- Arena, MAW `zzMaw_Arena.lua:222-224`: dead non-unique corpses are removed (AIState 11) every tick, and the C-tier
  boss (given a NameId by `generateBoss`, `zzMaw-Monsters.lua:2996`) only stops blocking completion once its corpse is
  looted empty. OpenYAMM pays as soon as everything is dead and keeps corpses. A MAW quirk; ours is the better rule.
- Arena slot A (the base arena topic) stays visible during a run in OpenYAMM; MAW hides slots A and B (`:121-132`).
  Already part of CNT-5.
- Circus trades (`GLOBAL.lua:547-797`): MAW only checks members 0-3 and says "We have no more items to trade for
  pyramids/kegs"; ours checks every member and has one wording. Cosmetic.
- Reagent counting (`GLOBAL.lua:110-128`) includes the item held on the cursor; `evt.CountItems` was not checked for
  that. Negligible.
- Dimensional Maps stamp (`zzMaw_DimensionalMapsQuest.lua:115-124`): MAW stamps any uncompleted dimension run loaded
  while the quest map is out (also a run begun before the quest map was given); ours stamps the run when the map is
  used (`MawItemRules.cpp:2031-2034`). Only differs for a run already in progress when the quest map is taken.
- `vars.ownedMaps` (`zzMaw_DimensionalMapsQuest.lua:75-77`): its only reader, `zzMaw-Maps.lua:857`, is a disabled
  branch; no effect to port.


## Checked and matching

- **Damage pipeline (A):** every Damage.lua stage was walked against the `MawCombatRules` stages; apart from the
  findings above, each matches or is a known row (CMB-2/4/5/7/9/13/14/15/16/18/22/23, CHM-2, SPL-1, CLS-2/3). The
  Thorn, Reflecting and dimension affix 5/6 reflects apply `^0.85` as MAW does. Survival gates are dead code in MAW;
  `stage_publish` and the remote-owner stages are multiplayer only. MonsterHP (real HP past 16 bits) maps to our 32-bit
  actor HP (STD1-1, STD3-2 cover the leftovers).
- **Classes, formulas, patches, timers (B):** all `Formulas.lua` constants match our formula code (one function is
  unused in MAW too). Each `zzMaw-Timers.lua` task has a counterpart at an equivalent real-time cadence; map completion
  every 1 s versus 10 s is GAPS A3.13; `checkOutOfBound` (engine pathing workaround) and `elementalBuffs` (dead code in
  MAW) are rightly not ported. Engine patches: the recovery floor bypass holds (MAW delay skips the 30-tick floor), the
  arena empty-pool fix is not needed with MAW's tables, the rest fix original-engine bugs absent here. Dimension affix
  27 on class casts is SPL-11.
- **Alchemy, initialise, experience (C):** zzAlchemy's mixing, reagent drops, potion effects and pity counters match
  or are known ALC rows; zzAlchemy's own `ItemGenerated` reagent level is overwritten later by zzMaw-Items.lua:1120 in
  MAW, and we port the effective rule (GAPS A4.2). Experience: matches apart from a negligible first-kill level 0 vs 1
  clamp (capped either way). zzMaw-Survival is unreachable in MAW (README §6). `FixMonstersBlockingShots` is part B's.
- **Maps and stats (D):** respawn lists and Insanity no-refill, reset count, dimension map pool, level, drop formula
  (apart from ALC-4, DEVIATIONS 58), affix table and draw order, density multiplier, family lists, map use; crit
  chance and multiplier (dagger, axe, Fate, affixes 20/21, Legendary 14); spell delay (apart from SPL-11); chance to be
  hit; damage-kind to resistance mapping; mitigation order (apart from DEVIATIONS 8, ITM-L2); race resistances; Unarmed
  dodge removal; spear and Legendary 29 stack reset; stat effect breakpoints; gradual mastery thresholds. MM6 sprite
  name restore needs no port (3D models). Madness pick-up counter and MAW's density "restore" have no live effect.
- **Global scripts (E):** quest gold bonus (gold × L/100 + 250·L, member 0's experience); arena wave table, spawn
  points and the L × 20000 reward; Dimensional Maps quest tiers, map rolls, rewards and clear detection; map affix 8
  (ignores the condition resistance roll); all 21 moved trainers (every target house is in `npc_extra_houses.yml`);
  black potion quests 181/203/212/234/244/246, Rust potions 207/571-576, circus trades 1442-1447 with the cap of 10.
  Small differences logged in part E's notes but not reported: arena paid before the boss corpse is looted, circus
  trades check members 0-3 only in MAW, reagent count includes the cursor item, dimension run stamped at entry versus
  at map use.

## Full inventory: MAW function → OpenYAMM counterpart → status

### Part A: MawCore damage pipeline

| MAW file:line function | OpenYAMM counterpart or covering row | Status |
|---|---|---|
| zzzzzMaw_Damage.lua:8 `events.CalcDamageToMonster` | `CombatRules::damageToMonster` stages (MawCombatRules.cpp:716-1097) + `resolveCharacterAttack`, `applyPartyHitEffects` | match (structure) |
| zzzzzMaw_Damage.lua:12 `events.CalcDamageToPlayer` | `damageToCharacter` stages (MawCombatRules.cpp:861-1096), `absorbCharacterDamage`, `applyMonsterHitEffects` | match (structure) |
| Pipeline.lua `new/addStage/on/remove/run/describe` | `CombatRules` stage lists (`m_damageToMonster.add`) | match (infrastructure) |
| Save.lua (vars.MawCore) | SaveVersion ruleset state (HANDOFF §3.1) | out of fork scope (other fork) |
| DamageState.lua:16 `setCoverBonus` / `takeCoverBonus` | `m_coverStates[&member].coverBonus` (MawCombatRules.cpp:1526-1529, 2101-2103) | match; keyed by address = known CMB-23 |
| DamageState.lua:30 `setSoloCover` / `takeSoloCover` | `CoverOutcome::halved` → `coverHalved` stage (MawCombatRules.cpp:983-991) | match |
| DamageState.lua:44-56 custom attacker | monster missiles through the engine; homing L3.5 | known L3.5 |
| DamageState.lua:63-71 crit tag | `partyHitStatusText` (H.4) | known DEVIATIONS 104 |
| DamageState.lua:76-84 push queue | `pushActor` (MawCombatRules.cpp:2643-2662) | known DEVIATIONS 102 |
| MonsterHP.lua `ledger/reconcile/current/max/scale` | 32-bit actor HP (STD1-1) | match (no proxy needed) |
| MonsterHP.lua:66 `apply` (keep HP fraction, ≥1 HP) | re-level keeps the fraction (GAPS A3.2) | known A3.2 |
| MonsterHP.lua:98 `stage` (Mass Distortion proxy scale) | Mass Distortion on real HP | known SPL-1 |
| MonsterHP.lua:118 `events.LoadMap` / `events.MonsterKilled` ledger wipe | n/a (no ledger) | match |
| Damage.lua:32 `rollDice` | `mawAverageOfTwoRolls` | match (CMB) |
| Damage.lua:39 `resDivide` (res % 1000) | `resisted` / `mawCappedMonsterResistance` | match (CMB) |
| Damage.lua:44 `hasLegendary`, :50 `affixCut`, :59 `track`, :67 `partyHPSum`, :78 `slotByIndex` | helpers; `track` → recount | match; recount = DEVIATIONS 136 |
| Damage.lua:89 `stage_context` | n/a | match |
| Damage.lua:93 `stage_puppetZero` | — | skipped: MP |
| Damage.lua:1169 `stage_remoteOwnerZero` | — | skipped: MP |
| Damage.lua:108 `stage_seraphOnHitHeal` | `applyClassHitEffects` seraphim (MawCombatRules.cpp:3065-3108) | match; stats without bonuses = known CMB-13, effective skill = CLS-2; online branch skipped |
| Damage.lua:156 `stage_elementalistLearning` | `mawElementalistProgress` (MawClassSpells.cpp:161-182), MawCombatRules.cpp:3008-3016, `mawElementalistKnownSpells` | formula match (tier^1.5·√L·√n, /3 area, insanity GM Invisibility); differs → FCOR-2-5 |
| Damage.lua:199 `stage_elementalistStackReset` | MawCombatRules.cpp:3006-3011 | match |
| Damage.lua:214 `stage_engineReset` | rules recompute from raw (`resolveCharacterAttack`) | match |
| Damage.lua:220 `stage_revealNearby` | `revealActorsAround` (MawCombatRules.cpp:2664-2670) | match (P9.D8) |
| Damage.lua:233 `stage_monsterVsMonster` | stage "monster-vs-monster" (MawCombatRules.cpp:720-729) | known DEVIATIONS 11 |
| Damage.lua:245 `stage_coverFlag` | MawCombatRules.cpp:1526-1529 | match |
| Damage.lua:272 `stage_weaponStun` | `applyWeaponStun` (MawCombatRules.cpp:583-612) | match (CMB) |
| Damage.lua:305 `stage_stunDeathCleanup` | world clears a dead actor's states | match |
| Damage.lua:317 `stage_flyRemoval` | MawCombatRules.cpp:2763-2772 | known A3.3 (done) |
| Damage.lua:334 `stage_stunSpellPrime` | `crowdControlSeconds` Stun + `mawStunChance` (MawSpellRules.cpp:1413-1424, MawSpellFormulas.cpp:140-146) | match; affix 13 = DEVIATIONS 59 |
| Damage.lua:373 `stage_massDistortion` | `massDistortionScale` (MawCombatRules.cpp:112-140) | match; SPL-1/CMB-4 known |
| Damage.lua:399 `stage_sparksChain` (spell 18 chain, mastery −1, 768) | `spellChainMastery` (MawCombatRules.cpp:1798-1808) | known DEVIATIONS 44 |
| Damage.lua:432 `mightLevelSwap` | none needed: `GetMightDamageMultiplier` ignores the level (zzMaw-Stats.lua:265) | match (no-op) |
| Damage.lua:444 `stage_weaponRecompute` | `resolveCharacterAttack` (MawCombatRules.cpp:1333-1592) | match (CMB); Carnage ×0.25 = CMB-16/D.5 |
| Damage.lua:503 `stage_painReflectionFlag` | none (world runtimes reflect raw) | differs → FCOR-2-1 |
| Damage.lua:517 `stage_resAndRetaliation` | stages "damage-taken-stacks", "resistance"; GM bow A1.9; Blades A1.10; spear A1.8 | match (CMB); order = CMB-9 |
| Damage.lua:597 `stage_dragonAttack` | `resolveCharacterAttack` breath branch, `dragonBreathDamage`, `pushActor`, `applyClassHitEffects` dragon SP | known A6.1/A6.2, CMB-11, CMB-12, DEVIATIONS 102 |
| Damage.lua:674 `stage_shamanOnHit` | `applyClassHitEffects` shaman (MawCombatRules.cpp:3109-3128) | match (CMB) |
| Damage.lua:698 `stage_dkAttack` (spell melee, Blood Leech, Grasp, SP regen 10/15/20 ×1.5 kill, Icy Touch slow, 76 paralysis) | `classSpellDamage`, `applyClassHitEffects` DK (MawCombatRules.cpp:3023-3060, 3134-3155) | match; bow = CMB-5; Grasp = DEVIATIONS 47; 76 = DEVIATIONS 29 |
| Damage.lua:822 `stage_assassinAttack` | `classSpellDamage`, `applyAssassinHit` | known L6.3, CMB-4, CLS-3 |
| Damage.lua:876 `stage_retaliation` | `applyRetaliation` (MawCombatRules.cpp:2053-2082) | match (stun 25 %·stacks, 2/1 s, no DR; recovery ×(1−0.3·stacks)); any-hit spend = DEVIATIONS 22 |
| Damage.lua:907 `stage_bossAffixes` Thorn/Reflecting | `applyPartyHitEffects` `reflect` (MawCombatRules.cpp:2752-2786) | match (^0.85); order = CMB-9 |
| Damage.lua:907 Adamantite | stage "boss-affixes" (MawCombatRules.cpp:835-844) | match; order CMB-9 |
| Damage.lua:907 Swapper | `deflectsPartyHit` | known DEVIATIONS 74 |
| Damage.lua:907 Regenerating counter | `MawMonsterRules.cpp:1706-1730` | differs → FCOR-2-6 |
| Damage.lua:960 `stage_survivalGate` | — | skipped: dead code (PHASE9_SCOPE) |
| Damage.lua:973 `stage_legendaries` enchant/aura adds | `resolveCharacterAttack` elements | match; bow = DEVIATIONS 46 |
| Damage.lua:1021 L17 | stage "legendary-blows" (MawCombatRules.cpp:785-822) | match |
| Damage.lua:1047 Shaman fire / Assassin water add | MawCombatRules.cpp:1482-1497 | match (skill read = CLS-2) |
| Damage.lua:1063 L21 | stage "legendary-blows" melee only | known (GAPS §11 D.11) |
| Damage.lua:1076 L14 | `critInputs.overcrit` | known CMB-9 (order) |
| Damage.lua:1083 L24 | `applyPartyHitEffects` kill branch (MawCombatRules.cpp:2744-2752) | match (0.10/0.05) |
| Damage.lua:1099 L11 | same branch | known CMB-2 |
| Damage.lua:1117 Shaman spell multiplier | spell damage (CMB checked) | match |
| Damage.lua:1134 `stage_damageTaken` (L29) | stage "damage-taken-stacks" + `applyPartyHitEffects` L29 | match; order CMB-9 |
| Damage.lua:1532 `artifact-on-hit` → `MawArtifactOnHit` | `artifactHitRange`, `updateArtifacts` | known L4.3, CMB-18, DEVIATIONS 72 |
| Damage.lua:1142 `stage_mapAffixes` 23/24/30 | stage "map-affixes" (MawCombatRules.cpp:847-867) | match |
| Damage.lua:1142 affix 5/6 reflect | `reflect` with share | known DEVIATIONS 59 |
| Damage.lua:1197 `stage_friendlyFireZero` | `harmsFriendlyActors` | known A1.13 (done) |
| Damage.lua:1207 `stage_leech` | `applyLeech`, `leechBarShare` (MawCombatRules.cpp:2837-2972) | match (CMB); affix 32 = CMB-15; Souldrinker CMB-22 |
| Damage.lua:1333 `stage_trackAndClamp` (recount, status line) | `partyHitStatusText` | UI: H.4, DEVIATIONS 104/136 |
| Damage.lua:1449 `stage_monsterHP`, :1453 `stage_finalClamp` | 32-bit HP, no cap | match |
| Damage.lua:1561 `pstage_itemRefresh` | equipment state read live | match (n/a) |
| Damage.lua:1568 `pstage_deathSeedMark` | `markMadnessHit` | known CHM-2 |
| Damage.lua:1583 `pstage_damageRecompute` reflected `^0.85` | `reflect` lambda | match for Thorn/Reflecting/affix 5/6 |
| Damage.lua:1593 pain-reflection `^0.85` | — | differs → FCOR-2-1 |
| Damage.lua:1601 player Pain Reflection flag | `applyPainReflection` (GameplayCombatController.cpp:1207-1228) | match (engine reflect) |
| Damage.lua:1604 party arrow on party | engine value | match |
| Damage.lua:1607 party spell friendly fire | — | differs → FCOR-2-2 |
| Damage.lua:1623 traps / no attacker | stage "mitigation" trap branch, `trapDamage` | known A1.6/L3.4 (done) |
| Damage.lua:1659 dodge (GM Dodging, Speed for spells/missiles) | `characterEvades` (MawCombatRules.cpp:3362-3381) | match (CMB); side effects → FCOR-2-3 |
| Damage.lua:1694 attack 2 ratio, monster spells ×list, round, spread, debuff 0.7 | stage "damage-recompute" (MawCombatRules.cpp:829-860) | match (CMB) |
| Damage.lua:1714 Mist Form ×0.25 | stage "mist-form" | known A1.14 |
| Damage.lua:1720 affix 14 energy | stage "map-energy" | known DEVIATIONS 59 |
| Damage.lua:1748 `calcMawDamage` | stage "mitigation" `mawMitigatedDamage` | match (CMB) |
| Damage.lua:1756 solo Cover ×0.5 | stage "solo-cover" | match |
| Damage.lua:1760 disease ×1.25/1.5/2, solo half | stage "disease" | match |
| Damage.lua:1773 Exploding | stage "boss-affixes" + `applyMonsterHitEffects` | match (shields = DEVIATIONS 71) |
| Damage.lua:1803 `pstage_bossAffixesPlayer` Summoner/Venomous/Plagueborn/Fixator/Swapper/Puller/Omnipotent | `applyMonsterHitEffects`, `summonBossFamilyMember` (MawCombatRules.cpp:3195-3270, 2019-2039) | match; immunities = DEVIATIONS 10; Swapper facing = DEVIATIONS 74; dodged → FCOR-2-3 |
| Damage.lua:1844 `pstage_survivalGatePlayer` | — | skipped: dead code |
| Damage.lua:1859 Mana Shield | `absorbCharacterDamage`, `mawManaShield` | match (CMB); order vs L15 = CMB-7 |
| Damage.lua:1869 L15 | `legendaryProtection` | match (FullHP/4, 150 min); order CMB-7 |
| Damage.lua:1888 Divine Protection | `divineProtection` | match (A6.8) |
| Damage.lua:1906 bolster ≥ 300 death/eradication | `characterDamaged`, `deathThreshold` | match except L30 → FCOR-2-4 |
| Damage.lua:1923 Disintegrate | `updateCombat` | known DEVIATIONS 103 |
| Damage.lua:1938 `pstage_mapAffixesPlayer` 1/2/10 | stage "map-affixes" (MawCombatRules.cpp:1052-1096) | match; traps affix 2 = CMB-14 |
| Damage.lua:1959 `pstage_remoteOwnerZeroPlayer` | — | skipped: MP |
| Damage.lua:2000 `Damage.start` → `events.PlayerAttacked` | — | skipped: MP |
| Damage.lua:1534 `pipe:on("publish")` → `MawMonsterDamage` | — | skipped: MP listener only |
| Damage.lua:1549 `Damage.describe` | — | skipped: debug |

### Part B: function inventory of the MAW class, formula, engine-patch, hook and timer files

Status keys: **match** (read both sides), **known <id>** (covered by DEVIATIONS, GAPS or a first-pass id),
**FCOR-2-n** (new finding above), **n/a** (an engine workaround or a MAW mechanism OpenYAMM does not need),
**skipped: UI** or **skipped: MP**.

#### Modules/MawCore/Classes.lua

| MAW file:line, function | OpenYAMM counterpart or covering row | Status |
|---|---|---|
| Classes.lua:17 `spRegen` (DK SP on hit 10/15/20) | `MawCombatRules::applyClassHitEffects` DK branch | known CLS-8 (arrows); values match |
| :23 `DKDamageMult` | `MawClassSpells.cpp:16-29` multipliers | match |
| :32 `DKSpellList` (spells by Frost/Blood/Unholy mastery) | `MawClassSpells.cpp:14-30`, `mawKnownClassSpells` | match |
| :43 `spellRequirements` (Elementalist tier thresholds) | `MawClassSpells.cpp:186-188` | match |
| :45-50 `eleOffSpellsOut/In` | `mawElementalistOffensiveSpell` (union of both, as MAW's `or`) | match |
| :55-61 `singleTarget`, `shotGun`, `aoeIn`, `aoeOut` | `MawSpellRules.cpp:57-60` | match |
| :69 `assassinSpells` (Cost, StackCost, DamageMult) | `MawClassSpells.cpp:32-58` | match (all 21 rows) |
| :96 `assassinSpellList` (m+1, Subtlety m+2) | `MawClassSpells.cpp` mastery column | match |
| :111 `DKManaCost` | `MawClassSpells.cpp` cost column; toggles cost 0 to cast (`MawSpellRules::manaCost`) | match |
| :124 `dkSkills` (costs, spell texts, skill names) | costs: `MawSpellRules::manaCost`; names: `mawClassSchoolName` | match; texts skipped: UI |
| :227 `elementalistSkills` (per-school progress init) | `CharacterRulesetState::elementalProgress` | match |
| :239 `assassinSkills` (cost 1000 below StackCost; names, texts) | `MawSpellRules::castRefusal` ("Not enough combo points"); `mawClassSchoolName` | match; texts skipped: UI |
| :300 `elementalistStacksDecay` (timer 0.1 s) | `MawClassRules::update` (MawClassRules.cpp:398-431) | known CLS-4; window source FCOR-2-20 |
| :317 `elementalistRandomizer` (indoor/outdoor area lists) | `randomElementalistSpell` (MawSpellRules.cpp:84-122) | match; empty kind known DEV 26 |
| :351 `mawTick_ElementalistStacks` | `MawClassRules::portraitCounter` | skipped: UI (counter shown) |
| :365 `assassinationDamage`: cost 50−5m, refund 0.1+0.01s, ×½ arrows, 0 for spells | `MawCombatRules::applyAssassinHit` | match; known CLS-7 (refund), CLS-3 (spell kills) |
| :388-395 kill refund (1+Air m)×5 SP and a combo point | `applyAssassinHit` `hit.killed` branch | match (melee/arrows); spells known CLS-3 |
| :396 payment gated on `mon.ShowAsHostile` | none | FCOR-2-21 |
| :397-413 combo point and AttackSpeedStack +1 (+0.5 arrows), decay 4 game minutes | `runtime.comboPoints`, `subtletyStacks`, `subtletySeconds = 8` | match |
| :414-430 crowd count within 384 (any live monster), min(0.8, 0.2(n−1)), all of it when unpaid | `resolveCharacterAttack` (~1406-1413), `GameplayActionController.cpp:1072-1081`, spells `PartySpellSystem.cpp:1345-1358` | known L6.2 (done), match |
| :434 `mawTick_AssassinStacks` | `portraitCounter` | skipped: UI |
| :448 `GetAssassinSpellDelay` = 2 × melee attack delay | `MawSpellRules::baseRecoveryTicks` (assassin ×2) | match; Subtlety known CMB-19; affix 27 known SPL-11 |
| :458 `Classes.dkSpellbook` (clear 1-99, grant by mastery) | `MawClassRules::update` known-spell sync (keeps ≥100) | match |
| :482 `dkLearnSpell`, :589 `assassinLearnSpell`, :488 `eleLearnSpell` (no books) | `MawClassRules::learnsSpellsFromBooks`, `InventoryItemUseRuntime.cpp:1118` | match (message text differs: UI) |
| :495 `eleSpellbook` (2, 15, 24, 37 always known) | `mawElementalistKnownSpells` AlwaysKnown | match |
| :509 `eleCastRotation` (stack +1, slot rotation, disable switch, timer) | `MawSpellRules::afterCast`, `rotateElementalistSpells` | known DEV 26; timer FCOR-2-20 |
| :541 `eleBindQuick` (spellbook cast resets stacks) | `afterCast` `fromSpellbook ? 1` | known A6.9 (done), match |
| :555 `eleBindScreen` (slot kinds on spellbook close) | kinds from the binding | known DEV 26 |
| :595 `assassinSpellbook` (clear 1-99, m+1 / m+2) | known-spell sync | match |
| :627 `assassinCastStacks` (refuse, else pay StackCost) | `castRefusal` and `afterCast` combo payment | match (MAW pays at cast start, we pay after a successful cast) |
| :646-662 `Classes.List` and class-id globals | `mawClassLine` (MawClassRules.cpp:122-157) | match (Thief/Rogue/Assassin/Spy; dragons by race, known A6.1) |
| :665-700 `is`, `of`, `present`, `describe` | the presentation swap | skipped: UI (cost part covered above) |
| :715-726 `dragonFang`, `dragonBreath`, `dragonScales` | `MawCharacterSheet.cpp:94-98` | match |
| :730 `dragonEffLevel` (×1.2 rule, cap 600/900) | `dragonLevel` (MawCharacterSheet.cpp:74-87) | known CLS-10 (fourth continent); rest match |
| :742 `dragonFangDamage`, :749 `dragonBreathDamage` | `MawCharacterSheet.cpp:110-120` | match (CLS checked) |
| :764 CalcStatBonusByItems (dragon): fang rows, attack +fang·s+10, breath rows, Scales AC replacing Dodging, resistances, item SP 0 | `MawCharacterSheet.cpp:89-127`; item SP 0 in `MawClassRules::applyClassBonuses` | match; race-versus-class known A6.1 |
| :804 GetAttackDelay (dragon ×(1+0.015 s), bite Unarmed / breath Dragon Ability) | `mawCharacterAttackDelay` (MawCombatRules.cpp ~1242-1250) | match |
| :817 PlaySound 18080 (breath flag for the next delay) | split by `CharacterAttackMode::DragonBreath` | match (mechanism not needed) |
| :823 CalcStatBonusByItems (DK item SP 0) | `applyClassBonuses` | match |
| :843 Action 142/25 (DK toggles 68, 74, 96) | DK toggle spells (`MawClassSpell::toggle`) | match; quick-cast quirk known (CLS question) |
| :877 PlayerCastSpell (DK delay = melee delay; 68/74 handled) | `baseRecoveryTicks` DK branch; toggles | match; affix 27 known SPL-11 |

#### General/zzClasses.lua

| MAW file:line, function | OpenYAMM counterpart or covering row | Status |
|---|---|---|
| zzClasses.lua:7 `promotionList`, :51 `midPromo` | `data/promotions.yml` | match (CLS checked) |
| :62 GameInitialized2 (keeps old names and factors) | `MawClassRules::promotionFactor`, `displayName` | known DEV 24 |
| :74 `checkPromo` (Elder/Ultimate factors and names, final and mid promotion, random pick, Party[0] awards) | `MawClassRules::updatePromotions` (every 0.25 s) | known DEV 23/24, CLS-5; match otherwise |
| :149 LoadMap → checkPromo, :153 EvtGlobal → checkPromo | `MawClassRules::update` polling | match (cadence finer) |
| :163 Seraphim description | — | skipped: UI |
| :171 `twoHandedSwords`, :180 Action 133 (Seraphim one-handed 2H sword, not in the off hand) | Seraphim one-handing (CLS "checked and matching") | match |
| :229 `indexof`, :238 `pickLowestPartyMember` (skip Dead/Eradicated) | Seraphim heal target in `applyClassHitEffects` | match |
| :259-281 Seraphim damage handler | commented out in MAW | n/a (dead) |
| :283 LoadMap `divineProtectionCooldown` init | Divine Protection cooldown | known A6.8 |
| :293-300 `MawSchoolDescBase` | — | skipped: UI |
| :306 dragon init: Flame Blast costs 25/40/50/60, texts, SPBase 60/120, SPFactor 0, Fangs/Scales caps M/G | `MawSpellRules::manaCost` FlameBlastCosts; `baseMaxSpellPoints`; `class_skills` patch | match |
| :346 LoadMap `dragonMeditationRemoved` (refund Meditation) | none | n/a: a migration for old saves; MAW dragons cannot learn Meditation (`class_skills.txt:313-314` "-") and start without it |
| :363 Action 114/110/176 → `dragonSkill` | auto-learn in `MawClassRules::update` | known A6.4 (done), match |
| :400 `mawTick_DragonCharScreen` (100 ms), :414 `dragonSkill` (Fangs/Scales/Dragon Ability at 1, labels) | same; names `mawClassSchoolName` | match; labels skipped: UI |
| :455-468 `directionToRadians`, `directionToUnitVector` | helpers | n/a |
| :471 `mawTick_MonsterPush` (per-frame dragon push) | `IGameplayWorldRuntime::pushActor` | known DEV 102 |
| :491 Shaman description; :496 Shaman damage (commented out) | — | skipped: UI / n/a (dead) |
| :521 DK description | — | skipped: UI |
| :534 Action → `dkSpellbook`; :539 CanLearnSpell → `dkLearnSpell` | see Classes.lua | match |
| :545 `spellDesc` capture | — | skipped: UI |
| :565-574 Tick tooltip hook | commented out in MAW | n/a (dead) |
| :576 Action 114/110/176 → `checkSkills` (presentation and DK/Assassin costs) | per-caster cost in `MawSpellRules::manaCost` | match (OpenYAMM keys the cost to the caster, not the selected member) |
| :604 Elementalist description, HPFactor[63] = 2.5 | `healthPerLevel` 2.5 | known CLS-5 |
| :610-634 Elementalist event stubs | see Classes.lua | match / known as above |
| :639 Elementalist stack text, :694 Assassin stack text | `portraitCounter` | skipped: UI |
| :652 `checkSkills` | `Classes.present` | skipped: UI |
| :668 Minotaur HPFactor 6/12 | class_multipliers patch | match (CLS checked) |
| :683 CanLearnSpell, :689 Action, :707 PlayerCastSpell (Assassin stubs) | see Classes.lua | match |
| :723 BeforeLoadMap `LichFix` (level-1 Lich → Necromancer) | none | known L6.6 (no port) |
| :736-741 Scheduler registrations (dragon screen 100 ms, push per frame, two stack texts 100 ms) | `MawClassRules::update` (0.25 s), `pushActor`, `portraitCounter` | match / known DEV 102 / skipped: UI |

#### Modules/MawCore/Formulas.lua

The functions are pure; they are applied by files other auditors cover. I checked the constants and shapes against
OpenYAMM's formula code.

| MAW file:line, function | OpenYAMM counterpart | Status |
|---|---|---|
| Formulas.lua:10 `gameMinuteSeconds` = 2 | `GameplayActionController.cpp:1069` (×2), `MawRealtimeRecoveryScale` | match |
| :14 `resistanceEnchantPower` (rings ×100/200) | `MawItemRules.cpp:704` | match |
| :21 `skillEnchantPower` ceil(max(√r, r/10)) | `MawCraftingRules::gemCap` (`:401`) | match; the Enchant Item path follows `zzMAWPotions.lua:83` instead (known ALC-14) |
| :27 `vitalityEnchantPower` r(1+min(r/50/slot, 5)) | `MawItemRules.cpp:699` | match |
| :35 `reductionPercent` | — | skipped: UI |
| :42 `damageFloor` 0.1 | `mawMitigatedDamage` withFloor (MawCombatFormulas.cpp:225-229) | match |
| :44 `soloCoverDamageTaken` 0.5 | Cover rules | known DEV 20 (one Cover rule) |
| :49-56 `retaliationCoefficients` and `retaliationDamage` (round(p^¼)·round(v^¼)·s) | `MawCombatRules.cpp` ~2070 | match |
| :60 `armorDamageTaken` 1/(AC/(200+6L)+1) | `MawCombatFormulas.cpp:234` | match |
| :67 `resistanceDamageTaken` (100+12L), :72 `enchantResistanceDamageTaken` | `MawCombatFormulas.cpp:266` | match |
| :77 `chanceToBeHit` 1/(1+speed/(100+stat(L))·0.5) | `mawChanceToBeHit` (MawCombatFormulas.cpp:210-213) | match |
| :83 `physicalVitalityShare` | power report | match (CMB/L4.5) |
| :92-110 `blessHitBonusForSkill`, `blessHitBonus` (0.05-0.10, buff cap 50) | `mawPartyHitChance` blessBonus | match; source known DEV 73 |
| :113 `mawHitChance` ((7.5+atk)/(exp+10)−1, slope 0.5, clamp 0.25-1) | `mawPartyHitChance` (MawCombatFormulas.cpp:203-208) | match |
| :124 `hitCapLevel` | — | skipped: UI |
| :148 `mawPlayerHitChance` (melee or ranged attack + bonus vs the monster's MAW level) | `MawCombatRules.cpp` ~1385, ~3350 | match |
| :157 `spellDiceScale`, :161 `spellAddScale` (1.025^s, 0.02 s, 0.01 s²) | `mawAscendedSpellDice` (MawCombatFormulas.cpp:331-339) | match |
| :165-183 `critCap`, `critChance`, `critDiminishingLevel`, `critDamageMult` (spells ÷4) | `mawCrit` (MawCombatFormulas.cpp:155-188), rounding to 1/100 | match |
| :185 `hpRegenRate`, :187 `hpRegenPerSec` | `mawRegenerationHealthPerSecond` (MawSkillFormulas.cpp:208-230) | match (the GM missing-HP term comes from MawRegen, SKL) |
| :196 `spRegenRate`, :198 `spRegenPerSec` | `mawMeditationSpellPerSecond` | match |
| :207 `meditationRegenPerSec` (pool ceil(full·√(1−r)), Legendary 20 ×(1+r)) | `mawMeditationPool`, `MawSkillRules::regenerationPerSecond` | match |
| :220 `enlightenmentManaPerSkill` 0.5/1/1.5/2 % | `MawSkillRules.cpp:382-403` | match |
| :231-234 `legendary24*`, `legendary29DamageTaken` | legendary affixes | known ITM-L* / L4.1 |
| :237 `bodyLeech`, :242 `mindLeech`, :248 `bloodLeech`, :254 `dkBloodLeech` | `MawCombatRules.cpp` ~3101-3139, `MawSpellRules.cpp:350`, `mawLeech` DK +0.10/+0.05 | match |
| :257 `hpRegenBuffPerSec` √F·s^1.25·(m+1)/1000 | `mawRegenerationPotionHealthPerSecond` (0.005: the potion's buff is stored at mastery 4) | match |
| :262 `assassinEnergyPerSec` | `MawClassRules::update` assassin branch | match; conditions known CLS-9 |
| :272 `chargesStatMult` min(1+c/25, 5) | `MawItemRules.cpp:273, 389` | match |
| :277 `chargesDamageScale` | no caller in MAW | n/a (dead) |
| :282 `chargesSchoolSkill`, :287 `chargesMeditationSkill` | `MawItemRules.cpp:283-284, 403, 409` | match |
| :292 `chargesArmorAC` | `MawItemFormulas.cpp:372` | match |
| :297 `chargesWeaponBonus` (weapon-skill AC/res, staff party res) | `MawCharacterSheet.cpp:388-410, 437-457` | consumer in zzMaw-Items (ITM, L5.6); not re-audited |

#### Modules/MawCore/Engine.lua, Fixes.lua, Scheduler.lua, Save.lua, General/zzzzzMaw_Core.lua

| MAW file:line, function | What it changes in play | OpenYAMM | Status |
|---|---|---|---|
| Engine.lua:4-60 `Addr` table, :105 `patch`, :112 `asmpatch`, :118 `asmproc`, :123 `alloc`, :132 `writePtr`, :332 `describe` | ledger and memory helpers | — | n/a |
| Engine.lua:141 `showItemEffect` | item glow when crafting | Workbench effects | skipped: UI |
| Engine.lua:154 `setShopItemFilter` (special items: sell, identify, repair) | used by SpecialItems.lua | `content/` shop rules | known A2.13 |
| Engine.lua:252 `setBackpackItemCap` | engine item-record search | own inventory model | n/a (engine bug) |
| Engine.lua:288 `setArenaPoolFallback` | MM7/8 arena with no type in range | `ArenaRuntime.cpp:58-118` never empty under MAW (see notes) | n/a |
| Engine.lua:314/323 `snapshotPlayerBuffs`, `restorePlayerBuffs` | Endless Arena buff snapshot (zzMaw_Arena.lua) | — | covered by the zzMaw_Arena auditor |
| Fixes.lua:19 skill-hint row format | skill popup layout | — | skipped: UI |
| Fixes.lua:32 attack recovery floor 30 → 1 | faster attacks than 30 ticks | MAW delay bypasses `OeMinimumMeleeRecoveryTicks` | match (see notes) |
| Fixes.lua:51 backpack item cap per doll | engine records | — | n/a |
| Fixes.lua:71 `FixMonstersBlockingShots=1` (shots stuck in the air indoors; risen monsters unable to hit their own kind) | GrayFace engine bug | own projectile and monster-vs-monster code | n/a (engine bug) |
| Fixes.lua:92 arena pool fallback | see Engine.lua:288 | — | n/a |
| Scheduler.lua:16 `every`, :26 `now`, :36 `remove`, :47 `describe`, :60 `start` (one Tick, real-time intervals) | task runner | per-rule accumulators | n/a (mechanism) |
| Save.lua:24 `data`, :32 `isGreenfieldSave` | `vars.MawCore` namespace stamp | ruleset id and options in saves | n/a (DEV 4) |
| zzzzzMaw_Core.lua:12-13 `require "MawCoreMain"; MawCore.start()` | load order | — | n/a |

#### General/zMaw-hooks.lua

| MAW file:line, function | OpenYAMM counterpart or covering row | Status |
|---|---|---|
| zMaw-hooks.lua:2-36 MonsterSpriteScale hooks (outdoor 0x47AC26/46, indoor 0x43D02E/4D) | `MonsterRules::actorDrawScale` | known A3.12 (done) |
| :39-163 `fasterStrafing`, `fasterBackpedaling`, `slowerBackpedaling` (HookManager switches) | engine movement | known DEV 134 (user decision) |
| :165 `safeGet` | helper | n/a |
| :176-197 hit-or-miss hook 0x4256DB → `mawPlayerHitChance`, then the PlayerHitOrMiss event | `mawPartyHitChance` in `resolveCharacterAttack` and missiles | match |
| :200-206 temple topic divide-by-zero guard | engine bug | n/a |
| :208-229 UI message-loop register guard | engine bug | n/a |

#### General/zzMaw-Timers.lua (tick tasks and cadence)

The driver (`:16 mawTick_TimerDriver`, `:66 MawTimer`, `:51-63` helpers, `:102-105` registration) runs on game time:
128 ticks per second, at most 2 s per frame, and at most 2 steps per frame in real time (20 in turn-based mode). The
task bodies live in other files; here I only checked that each has a counterpart running at the same rate.

| Task (interval) | MAW body | OpenYAMM counterpart and cadence | Status |
|---|---|---|---|
| `horizontalModeMasteries` (0.5 s) | zzMAW-Skills.lua:1976 | `MawSkillRules::applyProgressionMasteries` and `applySoloMasteries`, every frame (`updateRegeneration`) | known L5.2/L5.3 (done); cadence finer |
| `MawRegen` (0.1 s) | zzMAW-Skills.lua:1384 | `MawSkillRules::updateRegeneration`, every frame with carries | match (rate equivalent; formulas SKL) |
| `leecher` (0.5 s) | zzMaw-Monsters.lua:3390 | `MawMonsterRules::updateMonsters` aura tick 0.5 s | cadence match; behaviour known MON (Leecher bosses) |
| `checkOutOfBound` (2 s) | zzMaw-Monsters.lua:3536 | none | n/a: an engine pathing workaround, listed in COMBAT.md:1346 as not to port |
| `eliteRegen` (0.1 s) | zzMaw-Monsters.lua:3585 | `updateMonsters` Regenerating affix, 0.1 s ticks | match |
| `mappingRegen` (1 s) | zzMaw-Monsters.lua:3604 | `updateMonsters` map regeneration, 1 s | known DEV 59 (MAW bug fixed) |
| `checkMapCompletition` (10 s) | zzMaw-Monsters.lua:2568 | `updateMonsters` every 1 s | known A3.13 (see notes) |
| `nightmare` (0.5 s): difficulty prompts, Doom bolster 600, introductions | zzMaw-Monsters.lua:2799 | Rules panel, `mawBolsterAmount` | known DEV 2/3; messages skipped: UI |
| `elementalBuffs` (1 s) | zzMaw-Spells.lua:1046 | none | n/a: dead code in MAW (see notes) |
| `mawBuffApply` (0.5 s) | zzMaw-Spells.lua:2863 | `MawSpellRules::updateAuras`, every frame | known L5.1, SPL-3 (Protection from Magic recharge) |
| `elementalistStacksDecay` (0.1 s) | Classes.lua:300 | `MawClassRules::update` (0.25 s, carries) | known CLS-4, FCOR-2-20 |
| `poisonTimer` (1 s) | zzMaw-Items.lua:1513 | `MawCombatRules::updateCombat` real-time poison | known A1.5 (done) |
| `chargeTimer` (1 s, Knight Charge cooldown) | zzMAW-Skills.lua:1014 | `ClassRules::partyCharge` cooldown | known L6.1, DEV 48 |
| `timers/driver` (Scheduler, per frame) | zzMaw-Timers.lua:104 | `GameSession.cpp:1050-1058` | match in real time; turn-based not verified (see notes) |

### Part C: zzAlchemy, zzMaw-Survival, zz_Maw-initialize, zzzMaw_Experience, zzMaw-TownPortalClickFix

| MAW file:line function | OpenYAMM counterpart (file:line) or covering row | Status |
|---|---|---|
| zzAlchemy:4 `ShowCraftedItemEffect` | Workbench craft effect/sound (CraftingRuntime) | skipped: UI |
| zzAlchemy:9 GameInitialized2: potion names, 252-263 → item182, 264-299 "Deleted in MAW" | content/items_patch.txt:472-481 and the 264-299 names (GAPS A4.9) | match (262/263 already item182 in the base table) |
| zzAlchemy:22 LoadMap: Austerity renames 232-237, 252-256, 261-263 | MawItemRules.cpp:1602-1609 `displayName` | match (names only, drinking not blocked, as in MAW) |
| zzAlchemy:40 LoadMap: Austerity Identify Monster 10 GM | MawClassRules.cpp:341-361, MawSkillRules.cpp:272-276 | match |
| zzAlchemy:48 LoadMap: PlayerAlchemyBuffs / BlackPotions init | CharacterRulesetState `potionEffects`, `potionSteps` (saved) | match |
| zzAlchemy:62 `events.UseMouseItem` (drinking 221-299) | InventoryItemUseRuntime.cpp (drink), content/potion_effects.yml | match (ALC checked list); 221 → DEVIATIONS 32; 237 → ALC-3/DEVIATIONS 31; 240-242 → DEVIATIONS 30 |
| zzAlchemy:62 recovery payer, 60 ticks near enemies, "must be active" | InventoryItemUseRuntime.cpp `potionRecoveryPayer` | match (GAPS A4.7) |
| zzAlchemy:62 233/232 newest drink replaces the older | `setTimedPotionEffect` (InventoryItemUseRuntime.cpp:285-294) erases then adds | match |
| zzAlchemy:62 black potions / Transcendence best-step | potion_effects.yml 252-262, 259; `bestStepGain` | match (SKL-2 known for HP/SP effects) |
| zzAlchemy:62 Twilight/Dawn ages | InventoryItemUseRuntime.cpp:411-415 (fixed reference year, age shown the same way) | match |
| zzAlchemy:273 GetSkill: Meditation potion bonus | TimedPotionEffect SkillBonus | match |
| zzAlchemy:300 `GetTranscendenceSkillPoints` 5s²+15s | potion_effects.yml 259 `step_quadratic` | match |
| zzAlchemy:304-352 tables (blackPermanentBuffs, itemBuffMapping, potionBuffSpells, itemImmunityMapping) | potion_effects.yml (stat t.Stat+1 mapping checked: 262 → Mind/Body) | match |
| zzAlchemy:356 `events.DoBadThingToPlayer` potion immunities | Party.cpp:1094 `hasConditionImmunity` via `applyMemberCondition` | differs → FCOR-2-41 |
| zzAlchemy:419 `GetPotionHeal` | potion_effects.yml `pool_share`, MawPotionRules.cpp:85-89 | match (ALC) |
| zzAlchemy:426-472 potionText, 474 GameInitialized2 tooltips, potionRecipeText | potion popups (another auditor) | skipped: UI |
| zzAlchemy:584 reagentList | MawPotionRules `mawReagentBasePower`, crafting.yml | match |
| zzAlchemy:601 `mawTick_ReagentPower` (reagent power, Master/GM bonus, cap 255, excess to Alchemy) | MawPotionRules.cpp:30-62 | match (GAPS A4.5) |
| zzAlchemy:634 GameInitialized2 skillCapExtra Alchemy | `mixingAlchemyLevel` | match (GAPS A4.5/A4.6) |
| zzAlchemy:641 `events.ItemGenerated` reagent level = party level/5 | (overwritten in MAW by zzMaw-Items.lua:1120) | dead in MAW; GAPS A4.2 ports the live rule |
| zzAlchemy:654 `events.MonsterKilled` reagents ((m−2) %, tier, level round(outside/2), potion above 200) | MawMonsterRules.cpp:185-206 | match; known ALC-11 (>200 test), ALC-12 (risen/rewardless) |
| zzAlchemy:654 Endless Potion 0.2 % at GM, min(s+10,100) | MawMonsterRules.cpp:173-183 | match |
| zzAlchemy:706 GameInitialized2 Alchemy skill texts | content/skill_des_patch.txt | skipped: UI |
| zzAlchemy:715 `GetGemCap`, 726 `upgradeGem`, 761 PotionEffects[71-90] gems | MawCraftingRules `raiseEnchant`, `gemCap` | match (ALC checked; DEVIATIONS 36, 40, 66) |
| zzAlchemy:786/789 craft cooldown (60 frames) | none | known DEVIATIONS 36 |
| zzAlchemy:800 PotionEffects[91] Eye (special, reseeded) | MawCraftingRules `addSpecial` | match / DEVIATIONS 35 |
| zzAlchemy:826 PotionEffects[92] Hourglass | `addSecondEnchant` | match (ALC) / DEVIATIONS 35 |
| zzAlchemy:845 PotionEffects[93] Pandora's Cube | `refineQuality` | match / DEVIATIONS 37 |
| zzAlchemy:866 PotionEffects[94] Mirror | `duplicateItem` | DEVIATIONS 38 |
| zzAlchemy:880 PotionEffects[95] Emerald | `upgradeBaseType` | DEVIATIONS 39 |
| zzAlchemy:936 PotionEffects[96] Pearl | `removeRandomEnchant` | match (ALC) |
| zzAlchemy:964 PotionEffects[97] Orb of Creation | `transferLegendaryAffix` | match; ALC-8 for rarity |
| zzAlchemy:983 PotionEffects[98] Celestial Orb | `transferCelestial` | match; ALC-8 |
| zzAlchemy:1015 `GetCraftingCubeCap`, 1019 `craftingCubeOnItem` | `addItemPower` | match (ALC) |
| zzAlchemy:1037 `UseItem` maps (1061/1062 open slot, 1065 power +5, 1070 move) | MawCraftingRules.cpp:536-600 `craftDimensionMap` | match / DEVIATIONS 62 |
| zzAlchemy:1037 `UseItem` Endless Potion on charge potions | `addPotionCharges`, potion_effects.yml `rechargeable` (same eight ids) | match |
| zzAlchemy:1105 `normal_random` | MawMonsterRules.cpp:137-140 Box-Muller | match |
| zzAlchemy:1118 `events.MonsterKilled`: risen/reanimated/Madness exits, seeding | MawMonsterRules.cpp:111 (risen, rewardless) | match; seeding DEVIATIONS 14 |
| zzAlchemy:1146 affix 9 summon on death | MawCombatRules.cpp:2807-2824 | differs → FCOR-2-40 |
| zzAlchemy:1150-1186 gem drop (level bonus, boss ×10, Broodling, dimension, no-corpse ×3, Austerity 0, Insanity ×1.5) | MawMonsterRules.cpp:116-141 | match (ALC; A4.1 for the MP divisor) |
| zzAlchemy:1196-1201, 1222-1226 water monsters to inventory | MawMonsterRules.cpp:835-855 `lootWithoutCorpse.toParty` | match |
| zzAlchemy:1204 specials with pity | MawMonsterRules.cpp:143-169 | match (ALC) |
| zzAlchemy:1297 GameInitialized2 crafting item names, pictures, notes, cube data | content/items_patch.txt 1041-1070 (1070 value 15000) | match (art and texts are our own) |
| zzAlchemy:1345 scheduler registration | per-frame rules updates | n/a |
| zzMaw-Survival:2 survivalMaps, 6-31 switch, 34 LoadMap, 63 `survivalSpawns`, 100 LoadMap timer, 107 sprite scale, 113 DeathMap, 124 BeforeNewGameAutosave (Game.Mode==1), 131 teleport tick, 140 `survivalMonsterTable`, 307 CanOpenChest/PickCorpse, 341 scheduler | none | known: unreachable, do not port (README §6 line 578, UI_CONTENT 113; Damage.lua survival gates COMBAT_SPEC 26) |
| zz_Maw-initialize:4 `createDefaultSettingsFile`, 241 `loadMAWSettings`, global setting assignments | RulesetPreferences (RulesetOptions.h:54-63), keyboard settings | DEVIATIONS 3, 137, 139; GAPS H.7 |
| zz_Maw-initialize:298 LoadMap vars.MAWINITSETTINGS | none | n/a |
| zz_Maw-initialize:303 FixMonstersBlockingShots | see MawCore/Fixes.lua (part B) | out of scope here |
| zz_Maw-initialize:305 GameInitialized2 (isRedone, skill desc newlines) | none | skipped: UI |
| zz_Maw-initialize:315 `round` (half up) | `mawRound` = floor(x+0.5) (MawBalanceModel.cpp:124) | match |
| zz_Maw-initialize:324/362 `shortenNumber` | GAPS H.9 | skipped: UI |
| zz_Maw-initialize:438 `RunNextTick` | engine scheduling | n/a |
| zz_Maw-initialize:446 `GetMaxHP` (buff-rework HP pool) | MawCharacterSheet HP | match (buff rework always on, README §6) |
| zz_Maw-initialize:461-543 SimpleText, CustomSwitch, defaults (buffRework ON, restoreProjectiles ON, homing ON, friendly OFF, lootFilter OFF, extraItemTooltip OFF) | RulesetPreferences defaults: homing true, friendlyFire false, lootFilter Off, disintegration true | match; buffRework fixed on (README:569); restoreProjectiles is zzMaw-Monsters scope |
| zz_Maw-initialize:546 MultiplayerInitialized settings page | Rules panel | skipped: MP/UI (DEVIATIONS 3) |
| zz_Maw-initialize:581 Action 113 / 602 LoadMap settings commit and reload | options saved with the save (DEVIATIONS 4) | n/a |
| zz_Maw-initialize:627 Action 168 inventory+exit fix | none | n/a (engine UI bug) |
| zz_Maw-initialize:643 KeyDown O disableBow, dragon DefAttackR | none | known DEVIATIONS 137 |
| zzzMaw_Experience:7 `expStep`, 17 `calcLevel`, 36 `calcExp` | MawExperienceCurve.cpp:14-77 | match |
| zzzMaw_Experience:66/77/81 engine level-up hooks (cap 2^31−1) | `MawExperienceRules::experienceForNextLevel`, GameMechanics.cpp:77 (portrait indicator), 2042, 2214 | match; cap is DEVIATIONS 9 |
| zzzMaw_Experience:100 `flushEventBolster`, 109 `EventExperience`, 129 AddVariable hook | MawExperienceRules.cpp:63-77, EventRuntime.cpp:3790-3803 (per target member) | match |
| zzzMaw_Experience:141 `addExpNoBolster` (outb1) | EventRuntime `unscaledExperience` | match |
| zzzMaw_Experience:148 `events.MonsterKillExp` | MawExperienceRules.cpp:79-136 | match; MON-1 (NameId>300), MON-5 (d42 bank), MON-10 (maxHp vs model HP) known |
| zzzMaw_Experience:229 BeforeNewGameAutosave MMLVL reset | MawGameState defaults | match |
| zzzMaw_Experience:235 BeforeLoadMap save migration | none | n/a (old MAW saves) |
| zzzMaw_Experience:250 `addBolsterExp` | MawGameState.cpp:24-30 | match (Sync client branch skipped: MP) |
| zzzMaw_Experience:262/274/278/292 total/party level and exp | MawGameState `totalLevel`, `levelOutside` | match |
| zzMaw-TownPortalClickFix:11-18 TP window mouse-flag patch | none | n/a (MM8 engine bug) |

### Part D: zzMaw-Maps.lua and zzMaw-Stats.lua (function inventory)

ST = zzMaw-Stats.lua, MP = zzMaw-Maps.lua. "UI" rows are skipped as asked (tooltips and the stats page are another
auditor's).

| MAW file:line function | OpenYAMM counterpart or covering row | Status |
|---|---|---|
| MP:6-71 `spriteMappings` + AfterLoadMap: MM6 maps (stats 137-203) rename rock/flower/corpse decorations to MM6 sprites | `assets_dev/engine/models/indoor_decorations.yml`/`decorations.yml` already bind `rock01` to `mm6_deco_boulder01.glb` and `6rock01` to `mm6_deco_rock01.glb` (3D MM6 decorations); MAPS_CONTENT §3.4 "likely obsolete" | obsolete (presentation handled by the engine's MM6 models) |
| MP:74-79 `outSideMaps` + GameInitialized2: outdoor maps never refill | `MawMonsterRules::mapRespawnDays` (`MawMonsterRules.cpp:1238-1262`): ids 1-8, 13, 62-70, 72-74, 99-100, 140-141, 143-151 | match |
| MP:80-87 BeforeLoadMap: Insanity/Madness, no map refills | `mapRespawnDays` returns 0 for RoadToInsanity/BeyondMadness | match (dimension maps: FCOR-2-61) |
| MP:89-94 GameInitialized2 `dungeonResetList` (store refill days) | engine map table is not mutated; `mapRespawnDays` per map | match (structure) |
| MP:96-104 LoadMap: `mapResetCount` +1 on the reset map | `MawMonsterRules::resetMap` → `MawGameState::mapResetCounts` (`:1280-1285`), read by monster levels (+20 per reset) | match |
| MP:108-110 `dungeonCompletedKey` (file name keys) | `completedMaps` keyed by lowercase file name | match |
| MP:115-157 `migrateDungeonCompletedList` (old saves) | not needed (no MAW saves to migrate; DEVIATIONS 4) | n/a |
| MP:159-161 BeforeLoadMap migrate | n/a | n/a |
| MP:164-180 AfterLoadMap restore refill days; "resetting"→"resetted" state machine | `mapLoaded`/`m_forcedRefills`; per-visit completion | known MON-3 / CNT-3 |
| MP:183-188 `canResetDungeon` | `MawMonsterRules::mapResetOffer` (`:1264-1278`): completed .blv, not Insanity/Madness | known CNT-3 (no re-clear needed) |
| MP:191-212 `resetTxt`, `tryResetDungeon` typed yes/no, once per load | Reset button in the transition dialog (`EventDialogContent.cpp:1197-1208`), any entry into a .blv from outside a dungeon | match (UI replacement; MAPS_CONTENT §3.4 design) |
| MP:216-218 `resetMap` (legacy wrapper) | `resetMap` | match |
| MP:224-240 `addDungeonEntrance` (rewrites 110 entrance events) | not rewritten by design (MAPS_CONTENT §3.4); dropped base checks are CNT-13 (outa1 90, out11 505) | known |
| MP:242-283 barrels: EvtMap ≥20000 stat watch + AfterLoadMap "Empty Barrel" | none | known DEVIATIONS 57 / GAPS L8.1 |
| MP:285-748 per-map entrance list (out01-out14, 7out*, out*a-e MM6), hand-written out02 504, out07 504, out13 503/506, 7out03 504, 7out04 503, 7out05 503, outb1, oute3 101 | base events kept; reset via the dialog | known (MAPS_CONTENT §3.4, CNT-13) |
| MP:752-789 GameInitialized2 `monTbl` (arena monster order) | `MawMonsterRules::arenaWaveMonster` | covered by CNT/MON arena rows, DEVIATIONS 50 |
| MP:791 `mapDungeons` | `dimension_maps.yml` `dungeons` (same 151 ids) | match |
| MP:793-802 `getDimensionMapPool` | `MawRules::dimensionMapPool` (`MawRules.cpp:258-272`) | match |
| MP:804-807 `getDimensionMapLevel` | `mawDimensionMapLevel` (`MawDimensionMaps.cpp:293-296`) | match |
| MP:809-812 `dimensionMapsUnlocked` | `state.dimensionQuest.done` | match |
| MP:815-822 `getUniqueAffix` (1-33, distinct) | `MawDimensionData::rollAffixes` (same draw order slot 2, 3, 4, 1) | match |
| MP:824-939 MonsterKilled map drop (risen skip, Madness 950 gate and ×2/÷2, level 100/70, pity, ×10 bosses, Broodling /(5−tier), ÷(dropped+1), power, Insanity ≥30) | `rollDimensionMapDrop` (`MawMonsterRules.cpp:212-279`), `bossDropShare` (`:90-99`), `mawPityChance` | match; uncapped level known ALC-4; affix count known DEVIATIONS 58; seeding DEVIATIONS 14/RANDOMS |
| MP:941-958 `possibleMonstersIn/Out` | `dimension_maps.yml` `families_indoor/outdoor` (same lists) | match |
| MP:959-1027 UseMouseItem: use map 290 (refill, families seeded by fields, density 1+(P+20)n/300, consume, go to Party Start, Madness `ownedMaps`−1) | `MawItemRules::useTravelItem` (`MawItemRules.cpp:1998-2038`), `tryUseTravelItem` (`GameplayItemService.cpp:374-407`, map start position), `adjustMapEncounters` density (`MawMonsterRules.cpp:1449-1458`), `enterMap` families | match (`ownedMaps` vestigial: its cap is disabled in MAW, `MP:868-871`) |
| MP:1029-1039 GameInitialized2 `baseSpawnMonsters`, item 290 renamed "Dimension Map" | `content/items_patch.txt:482` | match |
| MP:1041-1057 BeforeLoadMap: map affixes to mapvars, monster pictures swapped | `MawMonsterRules::enterMap` (`:1323-1343`) | match |
| MP:1059-1069 LoadMap: affixes to mapvars | `dimensionRuns` | match (lifetime DEVIATIONS 63) |
| MP:1071-1082 AfterLoadMap: restore refill days, `Mon*Hi = oldDensity*` (globals never set: nil writes) | not needed | MAW bug, no effect to port |
| MP:1085-1112 `affixPowerTable`, `calculateAffixPower` (reduction via `reductionPercent` 2 decimals, procs ≤100) | `dimension_maps.yml` `affixes`, `MawDimensionData::affixValue` (`MawDimensionMaps.cpp:182-202`) | match (all 33 base/scale and kinds checked) |
| MP:1114-1130 `getMapAffixPower` | `MawRules::mapAffix` | match |
| MP:1132 `totalMapAffixes=33` | 33 affixes in the yml | match |
| MP:1134-1139 LoadMap: Madness `ownedMaps` floor 0 | none | vestigial (no cap uses it) |
| MP:1143-1164 LeaveMap (commented out) | — | dead code |
| MP:1166-1190 Action 14 (Madness): a dropped map 290 comes back to the hand with its fields | none | not ported, vestigial (served the disabled `ownedMaps` cap); ground items losing fields is ITM-1 |
| MP:1193-1196 Action 23/25 cancel the above | none | vestigial |
| ST:2, 14-19, 21-49 KeyDown R/Y on the stats page: reset the map damage recount | none | known DEVIATIONS 136 |
| ST:5-12 `safeGetMonsterLevel` shim | n/a | n/a |
| ST:52 `AXE_CRIT_DAMAGE_PER_SKILL` | `mawCrit` `0.01 * grandmasterAxeSkill` | match |
| ST:54-59 `MawReferenceLevel` | `MawCritInputs::referenceLevel` (callers pass total level for spells) | match |
| ST:61-144 `getCritInfo` (luck/(500+5L)+5 %, mult accuracy/min(250+2.5L, 2000/3000)+1.5, spell intellect/(4·dim)+1.5, round 2 dp, Master dagger per hand, GM axe once, Fate max(47, 86/1.5), affixes 20/21, L14 +10 % uncapped, heals never crit) | `mawCrit` (`MawCombatFormulas.cpp:155-188`), inputs `MawCombatRules.cpp:1416-1444`, `MawRules::auraSkill` (`:549-563`); heals: no crit in `MawSpellRules::healAmount` | match (L14 placement known ITM-L2) |
| ST:147-155 GameInitialized2 `oldTable` (spell delays) | spell table recovery at mastery | match |
| ST:156-160 PlayerCastSpell → `getSpellDelay` | `PartySpellSystem.cpp:1440` → `MawSpellRules::recoveryTicks` | match |
| ST:162-243 `getSpellDelay` (Assassin ×2 weapon, 122 → 120, CC 1.015^(asc−s), haste floor(speed/20), 1.015^asc, Haste buff, special 40 ×1.1, armour impair, Elementalist ×1.5/(1+0.05 stacks), 123 = 1.5 × ranged delay, affix 27) | `MawSpellRules::baseRecoveryTicks` (`MawSpellRules.cpp:541-600`), `mawSpellDelay` (`MawCombatFormulas.cpp:318-329`) | match; affix 27 on CC/122/class casts and Elementalist CC Ascension known SPL-11 / CMB; DK weapon pace (Classes.start handler runs last) matches |
| ST:246-250 PlayerAttacked: global `mon` | n/a | n/a |
| ST:253-255 `CalcHitOrMiss` (`chanceToBeHit` = 1/(1+speed/(100+stat(L))·0.5)) | `MawCombatRules::characterEvades` → `mawChanceToBeHit` (`MawCombatFormulas.cpp:210-213`) | match |
| ST:258-261 GameInitialized2 Bodybuilding description | skill text | UI (skipped) |
| ST:263-269 `STAT_DAMAGE_DIVISOR`, `GetMightDamageMultiplier` (might/1000) | `MawCharacterSheet.cpp:349`, combat might terms | match |
| ST:271-294 `leechAllText` | Power tooltip | UI (skipped) |
| ST:296-298 `getIntellectDamageMultiplier` (intellect/1000) | `MawCombatRules.cpp:1706, 1905` (max of Int/Per) | match (Int-vs-Per choice is zzMaw-Spells', not this file's) |
| ST:300-668 `BuildStatInformationBox` (stat popups, recount, healing recount) | `MawSkillRules::statRowText` etc. | UI (skipped); recount DEVIATIONS 136 |
| ST:670-689 `events.Regeneration` (1 % per tick per regen special, HP and SP) | none | differs → FCOR-2-60 |
| ST:705-721 mist form PlayerAttacked (engine rule off, ×0.25 physical in the pipeline) | Mist Form ×0.25 | known GAPS A1.14 (done) |
| ST:723-740 `legendaryCrowdMultiplier` (L22) | `MawCombatRules.cpp:1001-1015, 2410-2421` | known ITM-L2/ITM.md:340 |
| ST:742-759 `flatClassReduction` (Shaman Water / Seraphim Spirit) | `MawMitigationInputs::flatReduction` | known CMB (solo model) / CLS.md:36 |
| ST:761-776 `applyPostMitigation` (floor 10 %, L18, L22, flat cut ≥25 %) | `mawMitigatedDamage` `withFloor` (`MawCombatFormulas.cpp:226-230`) | match for floor/flat; L18/L22 order known ITM-L2 |
| ST:778-787 `classDamageReduction` (Shaman Air; DK Body physical, Dark magic) | `physicalCutSkill` / `magicCutSkill` | match (trained vs effective known CLS-2) |
| ST:795-825 `mawTick_LabelWatch` | — | UI (skipped) |
| ST:827-846 Action 94 HP/Mana pool labels | — | UI (skipped) |
| ST:848-908 `mawTick_PoolLabels` (resistance % on the stats page) | stats page | UI (skipped) |
| ST:910-920 BeforeLoadMap `resListBackup` | — | UI |
| ST:922-933 `damageKindMap` | `CombatDamageType` mapping | match |
| ST:936-945 MonsterKilled: reset spear and legendary-29 stacks | stacks live in the actor's facts, zeroed on revival (`IndoorWorldRuntime.cpp:15686-15687`) | match |
| ST:947-951 GetStatisticEffect floor(v/5) from 25 | `mawStatEffect` (`MawCombatFormulas.cpp:122-...`) | match |
| ST:955-975 crit message hook (attack/shoot/kill text) | `CombatRules::partyHitStatusText` | known GAPS H.4, DEVIATIONS 104 |
| ST:977-1015 `damageKindResistance`, `buffToResistance`, `buffToSpell` | `resistancesAgainst` (`MawCombatFormulas.cpp:85-114`: Spirit→Mind, Light min(Mind,Body), Dark four elements, Energy all six); resistance auras | match; aura base known SPL-2 |
| ST:1017-1035 `compute_damage` | — | commented out ("UNUSED") |
| ST:1037-1158 `calcMawDamage` (GM shield, AC with affix 28, class cut, Shielding ×0.85, Shield buff ≥0.7, best-of resistances with item enchant and L16 and affix 29, immunity 65000, randomisation) | `mawMitigatedDamage` (`MawCombatFormulas.cpp:220-281`) | match; double GM shield DEVIATIONS 8; item resistances GAPS A1.1; randomisation unreachable per COMBAT_SPEC §1.4 note |
| ST:1161-1180 `mawTick_PowerLabels` | stats-page rows | known DEVIATIONS 132 |
| ST:1183-1187 GameInitialized2 skill descriptions newline | — | UI |
| ST:1189-1346 `calcPowerVitality` | `mawPowerReport` | known GAPS L4.5 (done) |
| ST:1349-1383 CalcStatBonusByItems: race resistances (Lich Mind/Body immune, Vampire Mind, elves, trolls, goblins, dwarves +25+L, dragon Fire +100+2L) | race resistances | match (CLS.md:195) |
| ST:1385-1397 PlayerAttacked/GetSkill: Unarmed reads 0 for two calls after an attack (no engine GM Unarmed dodge) | `MawCombatRules::characterEvades` (`:3400-3420`) has no Unarmed dodge | match |
| ST:1399-1460 `GetHealParams` | — | debug print helper, no gameplay effect |
| ST:1462-1469 `masteryForSkill` | `MawBalanceModel::masteryForSkill` (`MawBalanceModel.cpp:361-372`) | match |
| ST:1471-1473 `masteryPerLevel` | balance model | match |
| ST:1480-1495 `GetGradualMasteryValue` | `MawBalanceModel::gradualMasteryValue` (`:375-396`) | match |
| ST:1497-1505 `masteryThresholds` (0/4/7/10, 0/8/16/25, 0/10/24/40) | `MawBalanceModel::masteryThreshold` (`:351-359`) | match |
| ST:1507-1530 `GetDifficulty` | `int(difficulty)+1`, 7/8/9 modes | known CHM.md:106, DEVIATIONS 1 |
| ST:1533-1538 GameInitialized2 scheduler tasks | — | UI |


#### Checked and matching (part D)

Respawn lists and Insanity no-refill; reset count; dimension map pool, level, drop formula (apart from known ALC-4 and
DEVIATIONS 58), affix table and draw order, density multiplier, family lists, map use; crit chance and multiplier with
dagger, axe, Fate, affixes 20/21 and Legendary 14; spell delay (apart from known SPL-11); chance to be hit; damage-kind
to resistance mapping; mitigation order (apart from known DEVIATIONS 8, ITM-L2); race resistances; Unarmed dodge
removal; spear and legendary-29 stack reset; stat effect breakpoints; gradual mastery thresholds.

### Part E: MAW Global scripts (function inventory)

| MAW file:line function | OpenYAMM counterpart (file:line) or covering row | Status |
|---|---|---|
| Arena:1-5 `QuestNPC`/`Greeting` NPC 313 | — | known CNT (MAW NPC greetings not ported) |
| Arena:7-26 MP locals, `allow_remote_event`, `online`, `myId` | — | skipped (multiplayer) |
| Arena:28-33 `resetArenaState` | `d42_maw.lua:28` (completion only) | match on completion; abort paths known CNT-5 |
| Arena:35-38 `arenaOwnerPresent` | — | skipped (multiplayer) |
| Arena:40-45 `setArenaProgress` | `d42_maw.lua:58-59` `MawArenaProgress` | match (percent formula) |
| Arena:47-53 `rewardArena` | `d42_maw.lua:26-33` | match (L × 20000 gold, best = max, slot B reset, message) |
| Arena:55-59 `abortArena` | — | known CNT-5 |
| Arena:61-78 `events.LoadMap` (timer 2.5 game min; reset elsewhere) | `d42_maw.lua:20` (150 game s = 2.5 game min) | match; reset on leaving known CNT-5 |
| Arena:80-91 `arenaTopic` | `Global_maw.lua:474-480` (10030), `npc_respec_patch.txt` 313 #11 | match |
| Arena:93-103 `startArena` | `Global_maw.lua:482-493` (10031) | match |
| Arena:105-119 `reloadArena` (buff snapshot, MoveToMap 3850,5776,1 dir 512) | `Global_maw.lua:492` | match (OpenYAMM keeps buffs over MoveToMap; no snapshot needed) |
| Arena:121-136 `beginArena` (hide slots A and B) | `Global_maw.lua:490` (slot B only) | known CNT-5 |
| Arena:138-161 `arenaRequest`, `arenaStarted` | `Global_maw.lua:482-493` | solo path match; MP branches skipped |
| Arena:163-182 `monsterSpawnLocation` | `d42_maw.lua:6-9` | match (same 14 points, z 1) |
| Arena:184-197 `startGeneratingWaves` | `Global_maw.lua:483-489` | match (wave 3L−2, 3 families, step 1) |
| Arena:199-209 `events.AfterLoadMap` (restore buffs, MP announce) | — | n/a (no snapshot needed) |
| Arena:211-291 `arenaSpawns` (wave table, counts, tiers, speed 350, boss on wave 6, waits 1/12) | `d42_maw.lua:20-60`, `MawMonsterRules::arenaWaveMonster` (`MawMonsterRules.cpp:1108-1143`) | waves match; family past the list DEVIATIONS 50; completion check differs → FCOR-2-81; corpse removal/boss-loot quirk noted |
| Arena:293-300 `events.PickCorpse` (empty NameId 0 corpses) | `d42_maw.lua:47` `loot = false` | known MON-4 / CNT-4 / ALC-1 |
| Arena:302-307 `endArena` | `d42_maw.lua:26-33` | match |
| Arena:309-338 `MawArenaRequest/Start/Progress/End` | — | skipped (multiplayer) |
| Arena:340-344 `events.ProcessGameData` (abort on load) | — | known CNT-5 |
| DimMaps:1 `ORACLES` (314 E, 413 E, 794 A) | `npc_respec_patch.txt` 314 #14, 413 #15, 794 #15 | DEVIATIONS 61 |
| DimMaps:3-27 tiers, `nextTier`, `migrate` | `dimension_maps.yml` quest (first 100, unlock 500, steps), `MawDimensionData::nextQuestTier` | match; legacy migration n/a |
| DimMaps:34-40 `highestLevel` | `MawMonsterRules.cpp:1857-1862` | match |
| DimMaps:42-64 `rollQuestMap` | `MawMonsterRules.cpp:1868-1880`, `MawRules::rollDimensionMap` | match (pool fallback, 4 affixes, active 4/3/2 at ≤0.1/<0.3, power (L−20)/10 ≤ 255); seeding RANDOMS |
| DimMaps:66-78 `giveMap` (+ Madness `ownedMaps`) | `MawMonsterRules.cpp:1888-1898` | match; `ownedMaps` has no live reader |
| DimMaps:80-113 `dimensionalMapsTopic` | `MawMonsterRules::rulesTopic` (`MawMonsterRules.cpp:1843-1932`), `Global_maw.lua:498-500` | match (texts, L × 1000 gold and experience, Done at ≥ 500, next tier) |
| DimMaps:115-124 `events.LoadMap` (stamp run) | `MawItemRules.cpp:2031-2034` | match (stamped at use; edge noted) |
| DimMaps:126-143 `events.LeaveMap` (mark cleared, level, name) | `MawExperienceRules::completeDimensionRun` (`MawExperienceRules.cpp:270-283`) | match |
| DimMaps:145-154 `Quest{}` per oracle | `npc_topic_respec.txt` 10040 | match (slots: DEVIATIONS 61) |
| Mapping:1-6 `events.DoBadThingToPlayer` (affix 8) | `MawCombatRules::piercesConditionSave` (`MawCombatRules.cpp:2578-2583`), `GameplayCombatController.cpp:1119-1127` | match (no "Resistance Ignored" status text) |
| Mapping:7-18 `events.Tick` (affix 25 push-back) | — | DEVIATIONS 60 |
| Mapping:19-23 `events.GetAttackDelay` (affix 26) | `MawCombatRules.cpp:1329` | known CMB-6 |
| Mapping:25-34 `events.AfterLoadMap` affix 33 | — | DEVIATIONS 60 |
| Mapping:35-56 `events.AfterLoadMap` `buffPower` reset | `MawCombatFormulas.cpp:22-41`, `mawAuraFlat(20, 2, ...)` callers | match → FCOR-2-80 (refutes SPL-2) |
| MoveTrainers:7-66 `npcMovesByMap` + `events.LoadMap` (`enableAllTrainers`, default on) | `data/npc_extra_houses.yml` | match (all 21 NPCs: every non-home house MAW moves them to is listed; home houses kept; 531/534 home 987) |
| PotionQuests:6-12 remove `StdQuestsFunctions` handlers of 181/203/212/234/246 | `ReplaceGlobalEvent` in `mawBrewQuest` (`Global_maw.lua:45-62`) | match |
| DruidCirclet:7-11 `events.ItemGenerated` (identify reward) | — | differs → FCOR-2-82 |
| DruidCirclet:13-21 `reward` (strength 5 amulet) | `Global_maw.lua:398` | match apart from FCOR-2-82 |
| DruidCirclet:23-39 `Quest{}` (NPC 41 slot B, item 638, 3000 gold, 10000 exp, texts) | `Global_maw.lua:374-403`, `npc_respec_patch.txt` 41 #11, `quests_maw.txt` 10001 | match (QBit 10001 instead of 299: custom range) |
| GLOBAL:5-17 `events.ClickNPCTopic` + 51-75 `events.EvtGlobal`, `calculateGold` | `GameplayDialogController.cpp:1466-1487`, `MawExperienceRules::questGoldBonus` (`:57-61`) | match (gold × L/100 + 250 L when gold and member 0's experience rose; L = other continents' bank) |
| GLOBAL:19-36 `events.Action` 405 (level/experience display hack) | — | skipped (engine display hack; curve belongs to `zzzMaw_Experience.lua`) |
| GLOBAL:38-49 `events.EvtGlobal` Insanity one-time trade goods | `Global_maw.lua:512-544` | match (1946 typo known CNT) |
| GLOBAL:77-95 globals 2666, 1777, 1888 (teleports) | `oute3_maw.lua:5-7` etc. | DEVIATIONS 49 |
| GLOBAL:98-102 `questRemoveList` | `ReplaceGlobalEvent` calls | match |
| GLOBAL:104-146 `REAGENT_COLORS`, `countItemsInRange`, `hasReagents`, `takeReagents` | `Global_maw.lua:20-42` | match (cursor item: note) |
| GLOBAL:147-248 globals 181, 203, 212, 234 | `Global_maw.lua:65-83` | match (reagents, QBits, items 254/254/254/253, XP 1000/5000, topic 2 cleared) |
| GLOBAL:250-292 `CanShowTopic` 244/246, globals 244/246 (Galvinus 132 → 133) | `Global_maw.lua:81-99` | match |
| GLOBAL:294-305 global 207 (three item 249) | `Global_maw.lua:103-110` | match |
| GLOBAL:307-545 globals 571-576 | `Global_maw.lua:126-334` | match (1000 each, 7500 at house 1 / 1500 elsewhere); 208 kept as base in both |
| GLOBAL:547-797 globals 1442-1447 (cap 10 per map, pyramid/keg counters) | `Global_maw.lua:337-370` | match (members 0-3 vs all, wording: cosmetic) |
| GLOBAL:799-803 Mode 2 circus traders removed | `Global_maw.lua:503-510` | match in effect; event id 65311 clash known CNT-1 |
