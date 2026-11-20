# FSPS: function inventory of MAW's spell and skill scripts (second pass)

Area FSPS covers five MAW files (`ef23ee17`):
- `Scripts/General/zzMaw-Spells.lua` (3864 lines)
- `Scripts/General/zzMAW-Skills.lua` (2735 lines)
- `Scripts/Modules/MawCore/Skills.lua`
- `Scripts/Global/zzMAWRespec.lua`
- `Scripts/Global/zzMAWPotions.lua`

Method: every function, event handler, timer and top-level statement with side effects was listed. Each was checked
against its OpenYAMM counterpart (`game/rules/maw/*`, the shared rules and world code it lands in,
`assets_dev/rulesets/maw/*`), or against the DEVIATIONS, GAPS or first-pass row that covers it. The full inventory, about 300
rows, is at the end of this file.

The audit was read-only: nothing was built or run. MAW paths are relative to `Maw-Mod-MMMerge/Scripts/`:
- SP = `General/zzMaw-Spells.lua`
- S = `General/zzMAW-Skills.lua`
- DM = `Modules/MawCore/Damage.lua`

OpenYAMM paths are relative to the repository root. The files were split into slices and read in parallel; a spot
check repeated FSPS-2-1, 2, 6, 10 and 11 against both repositories.

## Summary

| Id | Sev | Finding |
|---|---|---|
| FSPS-2-6 | P2 | **SPL-2 is a false positive.** `Global/zzMaw_Mapping.lua:24-57` replaces `buffPower` on every map load (when dimension affix 33 is off), with Base 20 for the six resistance auras and Day of Protection. Our 20 is what MAW plays; only MAW's tooltips print 10. The audit summary's request to ask the user again should be withdrawn |
| FSPS-2-1 | P2 | Sunray cannot be cast indoors under MAW. MAW's `mem.nop(0x426CD3, 6)` (SP:1006, MAW commit `342f34ed` "sunray castable indoors") removes the outdoor-only refusal; we refuse it indoors in every ruleset, and our text says "outdoors" |
| FSPS-2-2 | P2 | Every MAW heal spell (Heal, Remove Curse, Greater Heal, Power Cure, Resurrection on a living target) goes through `Party::healMember`, which clamps HP to 0. A member at −2000 HP wakes after two small heals. Extends SKL-1 |
| FSPS-2-3 | P3 | Heal scrolls apply MAW's heal table with the reader's Ascension and Personality. MAW skips its heal code for scrolls, which then heal the engine amount (Shared Life: the scroll skill without Personality or affix 31) |
| FSPS-2-4 | P3 | Spell texts with Standard's numbers: Invisibility Master/GM durations (the GM text says 20 h where the buff lasts 1 h 45), Fly omits "attacking ends it", Shrinking Ray says its extra targets start at GM (they start at Expert) |
| FSPS-2-5 | P3 | Crowd-control and Elementalist mana costs lack MAW's 65000 cap: they become uncastable from about Ascension 135, and undefined behaviour (double to `int` overflow) at the skill limits |
| FSPS-2-7 | P3 | A released Preservation aura stays on every member, for up to an hour, while any member has a Preservation potion running (the clear is per buff id, not per member) |
| FSPS-2-8 | P3 | The Armsmaster popup's mastery lines are one rank ahead of the code (Expert says 1 % speed, Master 1.5 damage, GM 2 damage) |
| FSPS-2-9 | P3 (question) | MAW's solo Knight Charge cooldown only ticks during multiplayer, so in solo the charge is never usable. DEVIATIONS 48 should say that ours fixes a MAW bug |
| FSPS-2-10 | P3 | Monster-missile homing latches `lost` once a missile leaves the 0.5° cone (MAW re-acquires every tick), and homes the centre missile of monster Sparks, Poison Spray and Ice Blast fans, which MAW excludes |
| FSPS-2-11 | P3 | Roster heroes keep Learning (Ascension) under MAW. MAW strips it from every `PlayersArray` character at the first load and refunds the points; 19 roster heroes have it, Brimstone and Duroth at GM. Extends CHM-1's missing roster hook |

Not reported as findings: the notes below, and MAW branches that are dead code. The buff branches guarded by
`not vars.MAWSETTINGS.buffRework=="ON"` are always false through Lua's operator precedence.

## Findings

### FSPS-2-1: Sunray cannot be cast indoors under MAW; MAW makes it castable indoors at any hour
Severity: P2
Confidence: confirmed (read both sides; MAW commit message confirms the patch's purpose)
MAW: SP:1006 — `mem.nop(0x426CD3, 6)`, added by commit `342f34ed` "sunray castable indoors" (an ancestor of `ef23ee17`),
which removes the engine's outdoor-only refusal for Sunray; the same commit changes the tooltip to "Indoors it can be
cast at any time; outdoors it only works during the day" (now in `ascension()`, outside this slice).
OpenYAMM: `game/party/PartySpellSystem.cpp:253-260` (`isSpellOutdoorOnly` lists Sunray) refuses it indoors through
`spellWorldAvailabilityFailure` (`:298-300`, called at `:1590`) in every ruleset; no `SpellRules` hook. The daylight check
(`:2586`) would also apply indoors. `assets_dev/rulesets/maw/data/texts.yml:463-465` keeps "It only works outdoors during
the day". A Light caster loses MAW's strongest single-target Light spell in every dungeon.
Not covered by: no DEVIATIONS/GAPS row; first-pass SPL lists Sunray only in the damage-table checks.
Suggested fix: a ruleset query (e.g. `SpellRules::spellAllowedIndoors`) that lets Sunray through indoors and skips the
hour check there under MAW; update the 87 text.

### FSPS-2-2: Heal spells lift a member with negative HP to 0 at once (extends SKL-1)
Severity: P2
Confidence: confirmed (read both sides)
MAW: SP:216-219 (Remove Curse), 309-312 (Resurrection on a living target), 368-371 (Heal), 441-446 (Greater Heal),
502-504 (Power Cure): `HP = min(HP + heal, maxHP)` with the member's HP left negative when the heal is smaller than
the deficit; Unconscious is cleared only when HP > 0. A member knocked deep below zero needs the whole deficit healed.
OpenYAMM: every MAW heal goes through `healTracked` → `Party::healMember` (`game/party/PartySpellSystem.cpp:1442-1458,
2047, 2058, 2109-2111`), which does `std::clamp(health + amount, 0, max)` (`game/party/Party.cpp:6815`). A 50-point
heal on a member at −2000 sets 0; the next heal wakes them. (`healMember` clamps the same way at HEAD, so Standard is
unchanged; under MAW the deficit can be thousands of HP.) Shared Life (`MawSpellRules::shareLife`) correctly keeps
negative HP.
Not covered by: SKL-1 names only regeneration through `healMember`; the heal spells share the same clamp. No row.
Suggested fix: the fix SKL-1 proposes (a heal that keeps negative HP, `min` only, then the incapacitation update)
should also serve the spell heals under MAW (or make `healMember` keep negative HP for the ruleset).

### FSPS-2-3: Heal scrolls use MAW's heal formula with the reader's Personality; MAW gives scrolls the engine's heal
Severity: P3
Confidence: confirmed (read both sides)
MAW: SP:144-149 — the PlayerCastSpell handler returns for every scroll before any heal branch ("disable for scrolls"),
so Heal, Remove Curse, Greater Heal (Cure Disease), Resurrection and Power Cure scrolls heal the engine's vanilla amount
at the scroll's skill (7, Master: `ExtraEvents.lua:829-830`). Shared Life from a scroll goes through `doSharedLife`
with the scroll's skill and no Personality multiplier or map affix 31 (SP:836-849).
OpenYAMM: `PartySpellSystem.cpp:1442` asks `spellRules.healAmount(spellCast)` for every cast, scroll or not;
`MawSpellRules::healAmount` (`game/rules/maw/MawSpellRules.cpp:602-636`) applies the heal table, the reader's Ascension,
Personality, the Shaman factor and affix 31. `CharacterSpellCast` carries no scroll flag (`request.fromScroll` exists
only on the request, `PartySpellSystem.h:95`).
Not covered by: GAPS A7.12 (travel scrolls kept) only; no row.
Suggested fix: pass `fromScroll` into the cast and return `std::nullopt` from `healAmount` for scrolls except Shared Life
(which keeps MAW's table at the scroll skill without Personality/affix); or record a DEVIATIONS row if MAW-strength
scroll heals are wanted (MAW's scroll heals are tiny against MAW's HP pools).

### FSPS-2-4: Spell texts left at Standard's numbers: Invisibility durations, Fly's attack rule, Shrinking Ray's splash
Severity: P3
Confidence: confirmed (read both sides)
MAW: SP:749-750 — Invisibility Master "Duration 15+1.5 minutes per point of skill", GM "Duration 30+3 minutes per
point"; SP:1030 — Fly "At higher difficulties, with the exception of few places, attacking monsters will cancel the
effect"; SP:1460-1462 — Shrinking Ray "Each impact covers one monster per mastery nearby ... Base duration %gs at every
mastery".
OpenYAMM: `assets_dev/rulesets/maw/data/texts.yml` has no entries for 19 and 21, so the engine table's texts show
(`assets_dev/engine/data_tables/spells.txt:21`: Master "Duration 10 minutes per point of skill", GM "Duration 1 hour per
point of skill") while the rule gives (15+s)×1.5 and (30+2s)×1.5 minutes (`MawSpellRules::partyBuffSeconds`,
`MawSpellRules.cpp:954-976`, GAPS A7.8): at GM skill 20 the text says 20 hours, the buff lasts 1 h 45 min. Fly's text
does not say attacking ends it (`mawAttackingEndsFly`, `MawCombatRules.cpp:1114-1118`). Shrinking Ray's text
(`texts.yml:482-489`) promises the extra targets only on the Grandmaster line, but `MawSpellRules::spellSplash`
(`MawSpellRules.cpp:883-892`) adds m−1 targets from Expert.
Not covered by: GAPS A7.8 (durations, done) and A7.5 (splash, done) do not mention the texts; no row.
Suggested fix: add 19 (Master/GM lines), 21 (description) to `texts.yml`; move the splash note to the Expert-and-up
lines of 92.

### FSPS-2-5: Crowd-control and Elementalist mana costs have no 65000 cap (and overflow `int` at high Ascension)
Severity: P3
Confidence: confirmed (read both sides)
MAW: SP:2186 — crowd-control cost `min(ceil(base x (1+0.2s) x 1.03^s x (1-0.125m) x P), 65000)`; SP:2272 — the
Elementalist's stacked damage-spell cost is also `min(..., 65000)`. Damage and heal costs are capped the same way
(SP:2269, 2363).
OpenYAMM: `game/rules/maw/MawSpellFormulas.cpp:72-73` (`MawSpellCategory::CrowdControl`) returns
`int(std::ceil(...))` with no cap; `game/rules/maw/MawSpellRules.cpp:510-514` (Elementalist branch of `manaCost`)
likewise. Damage and heal are capped (`MawSpellFormulas.cpp:66-71`). At Ascension about 135-140 a 50-point control
spell already passes 65000 (1.03^140 x 29 x 50 ≈ 90000) and becomes uncastable where MAW's stays at 65000; at the
skill limits (Learning up to 500 base, 1023 effective, GAPS A5.5) the double exceeds INT_MAX and the conversion to
`int` is undefined behaviour (1.03^500 ≈ 2.6e6; 1.04^500 ≈ 3.3e8 for the Elementalist branch).
Not covered by: SPL "Checked and matching" lists the damage cap only; no DEVIATIONS/GAPS row.
Suggested fix: apply `std::min(..., 65000.0)` before the `int` conversion in the CrowdControl case and in the
Elementalist branch (the Mass Distortion GM branch is bounded by its level cap of 255).

### FSPS-2-6: SPL-2 is a false positive: MAW plays the resistance auras and Day of Protection at base 20, not 10 (extends SPL-2)
Severity: P2 (a wrong fix is queued: the audit summary asks the user to reverse a correct decision)
Confidence: confirmed (read both sides)
MAW: SP:2670-2691 defines `buffPower` with Base 10 for 3/14/25/36/58/69 and 85, but `Global/zzMaw_Mapping.lua:24-57`
has an `events.AfterLoadMap` handler that, on every map load without dimension affix 33, replaces the whole global
`buffPower` with a table whose six resistance auras and Day of Protection (85) have Base 20 (every other row is equal
to SP's). So from the first map load on, `buffValueFlat` (SP:3162-3168), `buffStrength` (SP:3192-3202) and the effect
sites (`zzMaw-Items.lua:3035-3079`) all run with 20. Only MAW's own tooltips, built once in `GameInitialized2`
(SP:3221-3269, 3427-3433) before any map load, print "by 10". With affix 33 the handler instead scales the current
table in place (dev 60).
OpenYAMM: `game/rules/maw/MawCombatFormulas.cpp:21-41` (comment: "The live buffPower table
(Global/zzMaw_Mapping.lua)"), `MawSpellRules.cpp:1159-1163, 1176-1182, 1260`, `MawSkillRules.cpp:43-75` and the tooltip
values (`MawSpellRules.cpp:325-334`) use 20, which is what MAW plays. SPL-2's statement "no other assignment" missed
the Global script; HANDOFF §6 phase 5's "the live base 20" was right.
Not covered by: SPL-2 (this corrects it); AUDIT_20261024 lists SPL-2 under P2 and under "decide the questions".
Suggested fix: close SPL-2 as not a gap (no code change); optionally note in DEVIATIONS or BALANCE_MODEL that MAW's
tooltip says 10 while its code applies 20, and that our tooltip shows the applied number.

### FSPS-2-7: A released Preservation aura stays on every member while any member has a Preservation potion running
Severity: P3
Confidence: confirmed (read code)
MAW: SP:2877-2888 — every 0.5 s pass sets every member's Preservation (single buff 11) to expire now unless that
member's own potion keeps it (`vars.buffToIgnore[slot][11]`), then re-applies it only while the aura is held
(SP:2928-2932). Releasing the aura ends it on the next pass for everyone without a potion.
OpenYAMM: `MawSpellRules::updateAuras` (`game/rules/maw/MawSpellRules.cpp:1300-1360`) clears a character buff only
when its id is missing from the frame's applied list, for all members at once. When the Preservation aura is released
while one member has a Preservation potion (`MawRules::potionAura(Preservation, ...)`), the id is still pushed into
`appliedCharacterBuffs` (`:1342-1345`), so the other members keep the released aura's Preservation (applied for
`AuraSeconds` = 3600 game seconds, refreshed below half) until that potion ends or the hour runs out. Preservation
keeps them alive at deep negative HP for that time. The same per-id clearing would affect any future per-member
potion slot.
Not covered by: SPL-3 (PfM), SPL-4 (aura duration), L5.1; no row.
Suggested fix: clear per member: a member whose `memberSlots` lacks a buff id that the previous update applied to
that member loses it (track the applied ids per member, or clear Preservation for members without the potion when
no aura source exists).

### FSPS-2-8: Armsmaster's mastery lines in the popup are one rank ahead of the rules
Severity: P3
Confidence: confirmed (read both sides)
MAW: S:149-153, 912-930 — `armsmasterSkill` is Damage {N 0, E 1, M 1, GM 1.5, Supreme 2}, Speed {N 0, E 0, M 1, GM 1},
Attack 1 at every rank; `armsmasterDesc(m)` prints exactly those: Novice "1 atk", Expert "1 dmg, 1 atk", Master
"1 dmg, 1 atk, 1% speed", GM "1.5 dmg, 1 atk, 1% speed" (Supreme's 2 damage only in the description line, S:934).
OpenYAMM: the code matches MAW (`ArmsmasterDamage = {0, 0, 1, 1, 1.5, 2}`, `MawCharacterSheet.cpp:37`;
`ArmsmasterSpeedPerPoint = {0, 0, 0, 1, 1}`, `MawCombatRules.cpp:374`), but `assets_dev/rulesets/maw/data/texts.yml:822-824`
says Expert "1 damage, 1 attack, 1 % speed", Master "1.5 damage", Grandmaster "2 damage". A player reads +1 % speed at
Expert and Supreme's damage at Grandmaster.
Not covered by: GAPS A5.7 (checks only the Supreme line and the rank colours); no DEVIATIONS row.
Suggested fix: Expert "1 damage, 1 attack", Master "1 damage, 1 attack, 1 % speed", Grandmaster "1.5 damage, 1 attack,
1 % speed" (Supreme's 2 stays in the description).

### FSPS-2-9: Question: MAW's solo Knight Charge never comes off its cooldown (DEVIATIONS 48 describes a working 25 s cooldown)
Severity: P3 (question)
Confidence: plausible (read MAW; a runtime check in MAW would settle it)
MAW: S:1008-1013 sets `vars.chargeCooldown = vars.chargeCooldown or 25` (so 25 on a new game, and 25 after every use,
S:974). The only thing that lowers it is the global `chargeTimer` (S:1014-1018), which `mawTick_ChargeMovement`
registers only when `checkCharge` reaches 0 (S:1025-1027); `checkCharge` is decremented only while
`Multiplayer.in_game` is true (S:1021-1024), and `Multiplayer.init` (the only place setting it, `Modules/
MultiplayerMain.lua:59-64`) has no caller in the scripts. The two later `LoadMap` handlers define local `chargeTimer`s
for the potion cooldowns only (S:1075, 1116). So in solo, the only case Charge is allowed (S:954), the key always answers
"Charge has 25 seconds of cooldown": the ability is dead.
OpenYAMM: `MawClassRules::partyCharge` / `GameplayActionController` give a working charge with a 25 s session cooldown
(DEVIATIONS 48, GAPS L6.1), which follows MAW's evident intent.
Not covered by: DEVIATIONS 48 states MAW's cooldown as "25 s cooldown" and lists only the dash/collision/save
differences; it does not record that MAW's charge cannot be used.
Suggested fix: keep ours, and add to DEVIATIONS 48 that MAW's solo cooldown never ticks (a MAW bug fixed here).

### FSPS-2-10: Monster-missile homing drops its lock for good and ignores MAW's spell exclusions
Severity: P3
Confidence: confirmed (read both sides)
MAW: S:639-743 — every tick, for every object: the spell types Meteor Shower (9), Sparks (15), Starburst (22), Poison
Spray (24), Ice Blast (32) and Shrapmetal (93) never home; a monster-owned (or object-owned, kind 2) missile is turned
onto the party whenever its horizontal heading is within 0.5° of the party, re-tested each tick, so a missile the party
sidestepped re-acquires the party if it walks back into its line.
OpenYAMM: `OutdoorWorldRuntime.cpp:7068-7079` / `IndoorWorldRuntime.cpp:11193-11204` attach a cone homing to every
projectile of a monster attack aimed at the party, whatever the spell; `GameplayProjectileService.cpp:1907-1918` sets
`homing.lost = true` the first frame the heading leaves the cone, so the lock never comes back. A monster's Sparks,
Poison Spray or Ice Blast fan therefore has its centre projectile homing (MAW: none). Party missiles match MAW: the
fanned spells are `MultiProjectile` casts without a target actor (`PartySpellSystem.cpp:2546-2582`), so they get no
homing; Meteor Shower and Starburst are not projectiles.
Not covered by: GAPS L3.5 ("done", no detail); no DEVIATIONS row.
Suggested fix: skip the cone homing for monster spells 9/15/22/24/32/93, and test the cone without latching `lost`
(skip the steer while outside it).

### FSPS-2-11: Roster heroes keep Learning (Ascension) under MAW; MAW removes it at the new game's first map load and refunds the points
Severity: P3
Confidence: confirmed (read both sides; relies on MMMerge keeping the recruitable roster in `Party.PlayersArray` from
the start of a game, which CHM-1 also relies on)
MAW: S:1543-1560 — `events.LoadMap` loops every `Party.PlayersArray` character not yet in `vars.learningFix`, adds
`s + (s-1) + … + 2` skill points for its Learning level and sets Learning to 0 (skill and mastery gone). On a new game
this runs at the first map load and covers the whole recruitable roster (MAW ships no roster.txt, so MMMerge's roster
applies). In MAW Learning is Ascension (S:1562-1568: mana cost −12.5 % per mastery rank, more damage and healing per
point), so no roster hero starts with it.
OpenYAMM: `game/party/Party.cpp:3960-3977` (`recruitRosterMember`) and `:4006-4018` (`addAdventurersInnMember`) build
roster characters with `buildCharacterFromRosterEntry` (`:618`) from `assets_dev/engine/data_tables/roster.txt` with no
ruleset hook. 19 roster heroes have Learning there, e.g. Brimstone (dragon2) and Duroth the Eternal (dragon2)
Grandmaster 10/11, Rionel, Dervish Chevron, Dyson Leyland Expert 4, Vetrinus Taleshire Master 7. Under MAW they join
with that Ascension rank (Grandmaster: −50 % mana cost) and without the refunded points.
Not covered by: DEVIATIONS 27 (starting choices of created characters only); TRAINERS_SKILLS.md §4.4 states the rule
("under MAW nobody starts with Learning/Ascension") but its note (1) reads the early `return` as "characters hired
later keep Learning", while the roster heroes are in `PlayersArray` at that first load; CHM-1 (same missing roster hook,
for Beyond Madness and Doom items). No GAPS row.
Suggested fix: with CHM-1's roster-build hook (`ruleset prepareRosterCharacter`), MAW removes Learning from a roster
character built from `roster.txt` and adds `s + … + 2` skill points (not for characters dismissed and re-hired).

## Notes (differences too small for a finding, and context)

### zzMaw-Spells.lua 1-1473
Context that decides many rows: `vars.MAWSETTINGS.buffRework` defaults to "ON" (`General/zz_Maw-initialize.lua:537`).
Every branch guarded by `not vars.MAWSETTINGS.buffRework=="ON"` parses as `(not x)=="ON"`, which is always false, so
those branches (Heroism SP:225, Regeneration SP:377, Protection from Magic SP:452, `elementalBuffs` SP:1047) are dead
code in MAW whatever the setting. The aura spells' casts (resistances, Day of the Gods, Day of Protection, Hour of
Power) are `t.Handled` by the aura handler (SP:2746-2758) and every party buff is reset by `mawBuffApply` each 0.5 s
(SP:2863-2873), so the PlayerCastSpell branches that set those buffs here are superseded by the aura system (F3's
slice). Also checked: in MAW's `ExtraEvents.lua:879-881` a changed `t.Skill` is written back only for casts with a
preset skill (wands, hirelings), so `t.Skill = 0/1/10` in this file does not change a player's own cast (Power Cure's
engine part stays 10 + 5s, so MAW's total equals its table heal, as ours).

### zzMaw-Spells.lua 1470-2654
- Scripted crowd control cast from the spellbook (SP:1486-1526, 1585-1587): MAW ignores a non-hostile or out-of-range
  (4800) target under the crosshair and falls back to the hostile in sight whose debuff ends soonest; Control Undead
  only takes undead. Same mechanism as SPL-18 (quick-cast target choice); our spellbook cast applies to the clicked
  actor through `tryApplySharedSpellEffect`. Add to SPL-18 if it is fixed.
- Spell tooltip crowd-control seconds: MAW shows them against a monster of the caster's level with resistance
  LevelBase/2 and without the solo ×2 (SP:2199-2231); ours against resistance 0 with the solo ×2
  (`MawSpellRules.cpp:316-320`, `texts.yml:12` documents it). A tooltip choice, not reported.
- Shaman heal multiplier: MAW applies `1 + Σ/400` after the Ascension rounding of base and per-point (SP:2377-2382),
  ours before it (`MawSpellRules.cpp:303-311, 617-623`); differs by at most a rounding step. Which skill the sum reads
  is CLS-2.
- `m_crowdControlHistory` (`MawRules.h:257`) is keyed by map and actor index and never cleared; MAW drops
  `mapvars.ccHistory` on LeaveMap (SP:1758-1760). Returning to a map within 20 s keeps the history; the map grows by one
  small entry per actor ever controlled in the session. Negligible.

### zzMaw-Spells.lua 2576-3864
- SP:3739-3778 (projectile spells re-aimed at the closest visible hostile when the mouse is on no monster): our
  quick-cast already picks the hovered actor, else the closest visible hostile
  (`GameplaySpellService.cpp:275-284`); spellbook casts use the shared pending-target flow in both rulesets. No
  ruleset difference worth a row.
- `mawBuffCast` refuses a legendary-32 wearer with "Not enough Hit Points"; ours says "Not enough mana to hold X"
  (`PartySpellSystem.cpp:1511-1518`). Release text "Buff Disabled" vs "X released". Cosmetic.
- Reservation rounding: MAW subtracts the fractional reservations and ceils the remaining pool (reserved =
  floor(max x pct) + flat); ours ceils the reservation (`MawSpellRules.cpp:843`). At most one point.
- `updateAuras` now runs every frame (`app/GameSession.cpp:1054`) where MAW's pass runs every 0.5 s
  (`zzMaw-Timers.lua:95`); it allocates a few maps/vectors and walks every member's staff each frame. Cheap, and the
  per-frame SP clamp makes MAW's `getMaxMana` caps (Damage.lua 683, 790, 1090, 1305) hold automatically.

### zzMAW-Skills.lua 1-1135
- S:557: the old Haste +20 % speed branch (`not vars.MAWSETTINGS.buffRework=="ON"`) is always false through Lua's
  precedence (`(not x) == "ON"`); ours never adds it either. Matches.
- S:508: the bare-hand Unarmed bonus tests the race of a global `pl`, not `t.Player` (MAW bug); ours tests the attacker
  (`mawIsDragon(character)`, `MawCombatRules.cpp:1213`), MAW's intent (GAPS A6.3).
- S:931: MAW's Dodging Master line is built from the Grandmaster line (copy bug, cosmetic); ours shows the Master
  numbers (`texts.yml` Dodging), which equal GM's anyway (6/point).
- S:1072-1081, 1113-1122: each map load registers another potion cooldown `Timer` (they pile up); the potion hotkeys are
  not ported (GAPS L7.6), so nothing to compare.
- S:322-335 `autoLearnMastery` grants one rank per "+" press; ours grants every rank the level has reached
  (`MawSkillRules.cpp:236-251`). The two differ only when a class cap rises after the thresholds were passed (a
  promotion), where ours gives both ranks on the next raise; negligible, not reported.

### zzMAW-Skills.lua 1125-2735
- S:1316-1335 auto-repair: MAW's knock-out test `ko = v.Eradicated or v.Dead or …` is Lua `or` over game-time numbers,
  so only Eradicated is actually tested (a dead, stoned, asleep or unconscious member's Repair still counts in MAW).
  Ours (`MawCombatRules.cpp:2290-2297`) skips every incapacitated member, the evident intent. Too small for a row; listed
  so the difference is visible.
- S:2598-2620 Supreme Armsmaster: MAW takes `min(skill + ⌊Armsmaster/10⌋, 2 × base)` of the GetSkill result that
  already includes items and Legendary 33 (the racial handler at S:2392 is registered later, in GameInitialized2, so it
  runs after). When items plus Legendary 33 already exceed twice the base, MAW lowers the weapon skill to 2 × base; ours
  (`MawClassRules.cpp:269-283`) only ever adds `clamp(level − bonus, 0, Armsmaster/10)`. An edge of a MAW quirk on
  Knight-line characters with Legendary 33; the known part (base vs effective requirement) is SKL-3.
- S:1388-1403 regeneration wait: MAW's 20-second "recent loss" counter is decremented by the affix-22-scaled time
  (`timeMultiplier`), so with that dimension affix the wait also lasts 20/(1−X/100) s; ours counts real seconds
  (`MawSkillRules.cpp:1178-1198`). Negligible.

### MawCore/Skills.lua, zzMAWRespec.lua, zzMAWPotions.lua
No new findings in these three files. Everything with gameplay effect either matches or is already a known row.
Notes from the check:

- MawCore/Skills.lua is the Lua port of Skillz.dll: storage, persistence and engine patches. At `ef23ee17` the repository
  ships no `ExeMods/Skillz.dll`, so the Lua mode is the one that runs. In that mode `CleanMastery` does nothing, so the
  new-game "needToThankSkillz" mastery refund pays nothing. OpenYAMM has no counterpart, which is correct.
- Race mastery modifiers (`masteryLimitRaw`) reach the trainers through `SkillsUI.lua:515-576`, which swaps the class
  row while a house screen is open. The order is: add the shift, clamp to the maximum, then raise to the minimum, and
  it also applies when the class cap is 0. The race table is read for the 39 base skills only. OpenYAMM does the same:
  `ClassSkillTable::getEffectiveCap` (`game/tables/ClassSkillTable.cpp:376-430`, `shift_without_class_cap: true`) with
  the 28 non-default cells of `content/race_skills.yml`, Dwarf Axe E included. The two "S" cells of
  `Class Skillz.txt` act as Grandmaster in both, because the engine projection clamps to 4.
- Respec (`RespecSkills`): the side-by-side read found only two differences, and neither shows in play.
  - MAW resets only skills above level 1; OpenYAMM also moves level-1 skills to Novice and remembers their masteries.
    Masteries above Novice need level 4 or more, so a level-1 skill never holds one.
  - Under Austerity, MAW gives every member Identify Monster 0 at Grandmaster; OpenYAMM removes the skill until the
    next map. Both refund nothing and leave Identify Monster unusable.
  The hybrid shared set reads the global `pl` (DEVIATIONS 68). The greetings and the two-step topic are CNT-11.
- zzMAWPotions: `PotionEffects[n]` is item 220+n (18 → 238 Enchant Item, 23 → 243, 24 → 244, 35 → 255, 36 → 256;
  16 → 236 Harden Item is commented out as "not working"). OpenYAMM handles these on the Workbench: AddSpecial and
  AddFirstEnchant in `MawCraftingRules.cpp:676-742, 1090-1130` (`potion_effects.yml` `item: {action: crafting}`).
  These match: the power gates (40/40/55/100), base items only (`IsBaseItemId` ↔ `itemData().baseItem`), no existing
  special, weapon skills below 7, and the special ids (5/8/11/14, 6/9/12/15, 59, 41). For Enchant Item: no
  enchantments at all, the type roll (1 in 10 for skill enchants 17-24, rings 1-16, else 1-10), and the skill nerf.
  The fifth-then-ceil rounding is ALC-14, the identification refusal ALC-9, and the reseeding DEVIATIONS 35. The
  MMMerge Harden Item potion stays Standard's `{action: harden}`, since MAW's override is commented out.

## Checked and matching (summary; every row is in the inventory)

- **Spells (SP):**
  - Heal amounts: Personality term, affix 31, the tables and the Insanity tables, Shared Life, legendaries 34 and 35,
    Power Cure.
  - Crowd control: groups, the diminishing-returns window and ratios, boss halving, mastery steps, the Shrinking Ray
    splash, Dragon Fear's cost.
  - Damage: `spellPowers`, `CalcSpellDamage` (Ascension dice, Elementalist stacks, Fire Spike and Lifedrain
    multipliers, Intellect/Personality, crit, enchantments /2.5 on the 17 area spells).
  - Mana: damage and heal cost curves with the 65000 cap, the Personality cost factor, the Ascension source per class.
  - Auras: costs, reservation, utility auras, fixed sources (7/Master/40), potion fractions, skills and levels,
    `buffStrength` and best-source rules, the Hour of Power divisor.
  - Other: unreserved-pool clamp, Meditation pool, sealed spellbooks, the Insanity invisibility strip, the solo travel
    scrolls and the Fly scroll.
- **Skills (S):**
  - Weapon, armour and Armsmaster tables, attack delay (`GetAttackDelay` in full), skill caps and ladders, learning
    requirements by mode, the shared raise cost, mastery restoration on respec, the Cover 30 → Retaliation grant.
  - Cover and Retaliation, regeneration and Meditation (rates, ×2/×4, conditions, items, auras, potions), the dragon
    leech, Learning grants no experience, the Ascension and Perception texts, houses opening at 5.
  - Training time and hall caps, Insanity's training price, teacher prices, speeches and refusals, the horizontal-mode
    masteries, Repair, Identify Item, Disarm, Identify Monster, solo utility masteries.
  - The racial flat skill bonuses, Legendary 33 and 25, the Supreme requirement, the Dwarf and Minotaur axe rules, the
    Seraphim off-hand rule, the Unstuck lift, Cover, Mana Shield and Enlightenment as new skills and where they are
    taught.
- **MawCore/Skills.lua:** race mastery modifiers (shift, then max, then min, also without a class cap; base skills
  only); the 1023 skill-plus-bonus clamp; skill persistence. The DLL bridge, the new-game CleanMastery refund (inert in
  Lua mode) and the presets for an unshipped UI stage do not apply.
- **zzMAWRespec.lua:** cost and gold source, the greedy shared-set refund, the triangular refund, Alchemy kept, the
  custom skills, the Σ(5+⌊i/10⌋) floor, remembered masteries, Austerity's Identify Monster.
- **zzMAWPotions.lua:** the four weapon-special potions (power gates, base items only, weapon skill below 7, special
  ids) and Enchant Item (type roll, power share, skill nerf). Known rows: ALC-9, ALC-14, DEVIATIONS 35.

## Inventory (MAW function → OpenYAMM counterpart → status)

Status values: matches; finding FSPS-2-n; known <id> (DEVIATIONS row, GAPS row or first-pass id); not applicable (why);
not ported (covered by a row); superseded (MAW code that a later MAW system overrides at run time).

### Scripts/General/zzMaw-Spells.lua, lines 1-1473

| MAW line | Function / handler / statement | OpenYAMM counterpart | Status |
|---|---|---|---|
| 1-5 | locals, `MS` alias | — | not applicable (aliases) |
| 7-12 | `mmv` | — | not applicable (version selector helper) |
| 14-20 | `getPartyIndex` | — | not applicable (helper) |
| 22-27 | `events.KeyDown` (R in spellbook clears `vars.mawbuff`) | `MawSpellRules::removeAllBuffs` (`MawSpellRules.cpp:1448-1453`) | known GAPS A7.13 (done, matches) |
| 29-77 | `getSpellQueueData` | — | not applicable (engine spell-queue reader for the Shared Life hook) |
| 80-82 | `getHealPersonalityBonus` P/min(1000+3L, 4000) | `mawHealAmount` via `MawSpellRules::healAmount` | matches (first pass SPL "Heals") |
| 84-100 | `getHealSpellMultiPlier` (crit off, Personality, affix 31) | `MawSpellRules::healAmount` (`:602-636`) | matches |
| 108 | `hopList` {8,9,14,15} | Hour of Power aura | superseded by aura rework (F3) |
| 110-114 | `skipRemoteCast` | — | not applicable (multiplayer) |
| 117-122 | PlayerCastSpell: `mawRefresh` before/after | stat refresh each frame | not applicable (engine refresh) |
| 124-129, 655-670 | PlayerCastSpell: party HP before/after → `vars.healingDone` | — | not ported (DEVIATIONS 136, recount) |
| 132-135 | Assassin casts skip this handler | Assassin class spells (`MawClassSpells`) | matches |
| 136-142 | `ascension()` for the caster | `mawAscension` per cast | matches (F2 covers `ascension`) |
| 144-149 | scrolls skip every MAW heal/buff branch | `PartySpellSystem.cpp:1442` | finding FSPS-2-3 |
| 153-155 | SP < cost → no MAW effect | engine mana check | matches |
| 157-175 | Invisibility: refused branch near enemies, `invisCasted` → `mawBuffs` | `partyBuffSeconds` (`:954-976`), refusal near enemies | known GAPS A7.8 (done, matches); text: FSPS-2-4 |
| 178-222 | Remove Curse (49) heals 12/24/36 + 2/4/6 per point | `healAmount` + `applyCharacterRestoreSpell` (`PartySpellSystem.cpp:2050-2058`) | matches amount; negative HP: FSPS-2-2 |
| 225-248 | Heroism override | — | not applicable (dead code: `not x=="ON"` always false) |
| 250-260 | Raise Dead clears Eradicated only at GM | `Party::reviveMember` | known SPL-15 |
| 262-316 | Resurrection heal; dead target HP = max(hp+heal, heal) next tick | `PartySpellSystem.cpp:2038-2046` (`reviveMember(max(1, heal))`) | known GAPS A7.10 (living target); dead target matches; negative HP: FSPS-2-2 |
| 319-374 | Heal (68): table heal minus engine's 5+(m+1)s, DK skips | `healAmount`; DK 68 is Blood Leech (`MawClassSpells.cpp:21`) | matches; negative HP: FSPS-2-2 |
| 377-394 | Regeneration override | — | not applicable (dead code) |
| 397-449 | Greater Heal (74) heal + engine Cure Disease, DK skips | `healAmount` + restore (`PartySpellSystem.cpp:2050-2058`); DK 74 (`MawClassSpells.cpp:24`) | matches; negative HP: FSPS-2-2 |
| 452-459 | Protection from Magic skill 10 | — | not applicable (dead code); PfM aura: known SPL-3 |
| 461-543 | Power Cure: table heal to every member, L34/L35 on the total | `PartySpellSystem.cpp:2105-2112`, `afterHeal` | matches (engine part stays 10+5s, see header); negative HP: FSPS-2-2 |
| 547-561 | Day of the Gods → `mawBuffs` | DoG aura (`MawSpellRules::updateAuras`) | superseded by aura rework (aura cast is Handled, buffs reset every 0.5 s) |
| 563-584 | Resistance spells: power s×min(m,3), s hours | resistance auras | superseded by aura rework; base 20 vs 10 is known SPL-2 |
| 587-601 | Day of Protection → `mawBuffs` | DoP aura | superseded by aura rework |
| 603-653 | `applyHoP` (Bless, Haste, Heroism, Shield, Stone Skin) | HoP aura (s/1.5 Haste/Shield/Stone Skin/Fate) | superseded by aura rework (first pass SPL checked the aura) |
| 676-685 | `events.DoBadThingToPlayer`: PfM blocks monster Unconscious | `MawCombatRules::blocksMonsterCondition` (`:2656-2659`), `GameplayCombatController.cpp:1140` | known DEVIATIONS 31 / SPL-3 (matches) |
| 692-730 | `mawBuffs` (DoG, DoP, Invisibility, Regeneration timers) | DoG/DoP auras; Invisibility `partyBuffSeconds` | Invisibility matches A7.8; DoG/DoP superseded; Regeneration dead |
| 733-737 | `events.AfterLoadMap` 7d11 Invisibility 10 h | — | known SPL-14 |
| 742-798 | `GameInitialized2` spell texts (18, 19, 49, 51, 74, 75, 25/69/36/3/58/14, 83, 85, 114) | `texts.yml` 18, 49, 74, 75, 83, 85, 114 (aura texts) | matches except 19: FSPS-2-4 |
| 801-805 | `randomizeHP` | — | not applicable (unused debug helper, no callers) |
| 808-822 | `shouldParticipate`, `canParticipate` | `MawSpellRules::shareLife` (`:668-685`) | matches (dead/eradicated/stoned out, unconscious join) |
| 824-985 | `doSharedLife` (s/2, mult, −3s/−4s, healthiest first, even redistribution) | `healAmount` (`:610-631`), `shareLife` (`:668-765`) | known GAPS A7.1 (matches); scroll path: FSPS-2-3 |
| 989-1003 | autohook 0x42A171 replacing Shared Life, `HealingSpellPower` event | `PartySpellSystem.cpp:2082-2085` | matches (`HealingSpellPower` has no handler in MAW) |
| 1006 | `mem.nop(0x426CD3, 6)` Sunray castable indoors | `isSpellOutdoorOnly` | finding FSPS-2-1 |
| 1009-1014 | asmhook Spirit Lash Master range 384 | `PartySpellSystem.cpp` 768 | known SPL-13 |
| 1018 | `flyAllowedMaps` | `mawFlightMap` (`MawCombatRules.cpp:1104-1111`) | matches (11 maps) |
| 1020-1027 | `events.LoadMap` "Fly is allowed without restrictions here" at bolster > 100 | `MawMonsterRules.cpp:1629-1641` (Hard and up) | matches |
| 1029-1031 | `GameInitialized2` Fly description | — | finding FSPS-2-4 |
| 1034-1044 | `schools`, `buffsOrdered`, `schoolToBuff` globals | — | not applicable (only used by dead `elementalBuffs`) |
| 1046-1098 | `elementalBuffs` (GM passive buffs, vampire night, solo Wizard Eye/Torch) | — | not applicable (dead code; the live vampire night and solo freebies are elsewhere: CLS-6, GAPS A7.12) |
| 1101-1122 | PlayerCastSpell solo scrolls 16/21/27/31/33 kept; Fly scroll GM 7 h, recovery 120 | `MawSpellRules::keepsScroll` (`:978-982`), `partyBuffSeconds` Fly 7 h | known GAPS A7.12 (matches) |
| 1128-1144 | commented-out `CanLearnSpell` | — | not applicable (comment) |
| 1147 | `masteryName` global | — | not applicable (helper) |
| 1149-1180 | `processHealLegendaries` L34 mana refund, L35 recovery cut | `MawSpellRules::afterHeal` (`:645-666`) | matches |
| 1182-1247 | `processAutoTargetHeal` | `PartySpellSystem::quickCastCharacterTarget` | known GAPS A7.2 (replaced by the user's rule) |
| 1249-1262 | `checkManaForSpell` | — | known GAPS A7.2 / DEVIATIONS 137 |
| 1264-1331 | `events.Action` 25 auto-target heals (`autoTargetHeals` setting) | quick-cast rule | known GAPS A7.2 / DEVIATIONS 137 (MAW's Resurrection branch indexes the nil global `idx`, a MAW crash not ported) |
| 1337-1351 | `CCMAP` base minutes, schools, debuffs | `mawCrowdControlSpell` (`MawSpellFormulas.cpp:82-108`) | matches (first pass SPL "Crowd control") |
| 1352-1364 | `getCCDiffMult` | used at SP:1635 | F2's slice (caller) |
| 1366-1390 | `events.Action`: Dragon Fear cost 15/15/25/30 (CC cost block commented out) | `content/spells_patch.txt` / mana cost rules | matches (first pass SPL) |
| 1395-1402 | `CC_MASTERY_STEP`, `GetCCMasteryMult` (FlatDuration opt-out) | `mawCrowdControlMinutes` (`MawSpellFormulas.cpp:110-129`) | matches |
| 1406-1427 | `applyCCDebuff` (×1.015^Learning/(1+res/100) except 122, solo ×2, DR, min/max with the engine's) | `MawSpellRules::crowdControlSeconds` (`:1399-1446`) | matches (we clamp negative resistance to 0; MAW lets it lengthen: negligible) |
| 1431-1449 | `scriptedCC` list, `UndeadOnly`, `EffectObj`, `EffectColor` | world runtimes' CC effects | matches for the rule (UndeadOnly: SPL-10); effect objects/colours not applicable (visuals) |
| 1453-1473 | `GameInitialized2` Shrinking Ray and Dark Grasp texts (`damageCut`, `baseSeconds`) | `texts.yml:482-514` | Shrinking Ray splash line: FSPS-2-4; Dark Grasp mechanics per DEVIATIONS 47 |

### Scripts/General/zzMaw-Spells.lua, lines 1470-2654

| MAW line | Function / handler / statement | OpenYAMM counterpart | Status |
|---|---|---|---|
| 1470-1473 | tail of GameInitialized2 (Dark Grasp text into spellDesc) | `texts.yml` spell 96 | not applicable (text; F1's handler) |
| 1475 | `nextReadyPartyMember` (select next ready conscious member after a scripted CC) | engine selection after a cast | not applicable (UI selection) |
| 1486 | `castCCSpell` (scripted CC: mana check, hostile/undead/4800 target, mouse target else soonest expiry, "Spell Failed" + recovery 30, SP paid at school mastery, effect visual, `applyCCDebuff`, recovery `getSpellDelay`) | `GameplaySpellService.cpp:259-265` (quick-cast target), `PartySpellSystem` cast path, `MawSpellRules::crowdControlSeconds` (`MawSpellRules.cpp:1399-1446`) | known SPL-18 (targeting, no-target recovery); duration and cost match |
| 1548 | `aimlessQuickCC` table (Berserk, Enslave) | — | not applicable (engine aim-mode workaround) |
| 1551-1560 | GameInitialized2: wrap `CastQuickSpell` for Berserk/Enslave | quick-cast in `GameplaySpellService` | not applicable (Merge extra quick slots, dev 26) / known SPL-18 |
| 1564 | `events.Action` (Action 25 quick/attack spell → `castCCSpell` for Berserk/Enslave) | `GameplaySpellService.cpp:259-265` | known SPL-18 |
| 1581 | `events.PlayerCastSpell` (CC: Stun and Shrinking Ray elsewhere; scripted → `castCCSpell`; engine CC: resistance 0 / level 0 when DR allows, 65000 when not, non-undead immune to Turn/Control Undead; next tick restore and cap the engine's expiry with `applyCCDebuff(…, true)`) | `GameplayActorService::tryApplySharedSpellEffect` (ruleset seconds skip the resistance roll, `GameplayActorService.cpp:346-363`), `partyCrowdControlSeconds` (`SpellRules.cpp:142-168`) | matches (always lands unless DR immune; duration MAW's); Turn/Control Undead DR on living monsters is known SPL-10 |
| 1630 | nested `events.Tick` (1 or 100 ticks, Dark kind) restoring level/resistance | — | not applicable (engine hack) |
| 1660-1666 | `ccByObjType` {9030}; CCMAP Shrinking Ray BuffPower 2, SplashRadius 512, FlatDuration | `MawSpellRules::spellSplash` (`MawSpellRules.cpp:883-893`), `mawCrowdControlSpell` 92 flat (`MawSpellFormulas.cpp:126`) | matches (30 % damage cut: `MawCombatRules.cpp:933-938`) |
| 1668 | GameInitialized2: `MawEnableProjectileImpact(9030)` | Shrinking Ray impact in the world runtimes | not applicable (MM6 projectile hook) |
| 1674 | `splashTargets` (fresh nearest first, then soonest expiry, hostile, within radius) | `PartySpellSystem.cpp:450-470` (`applySpellSplash` candidates) | matches (first pass SPL checked) |
| 1705 | `events.MonsterAttacked` (Shrinking Ray object: struck + m−1 extra, BuffPower 2) | `PartySpellSystem.cpp:2694-2711` | matches |
| 1738 | GameInitialized2: `debuffGroups` (Slow, ArmorHalved, DamageHalved, MeleeOnly, Shrink = 1; Fear, Charm, Berserk, Enslave = 2; Paralyze = 3) | `MawCrowdControlSpell::group` (`MawSpellFormulas.cpp:117-130`) | matches |
| 1754 | `CC_WINDOW = 10 game minutes` | `MawRules::diminishedCrowdControlSeconds` window 20 s (`MawRules.cpp:63`; game minute = 2 s) | matches |
| 1755 | `events.LoadMap` (init `mapvars.ccHistory`) | `m_crowdControlHistory` | matches |
| 1758 | `events.LeaveMap` (clear history) | none (history keyed by map + actor) | differs, negligible (note) |
| 1761 | `getMonsterCCRatio` | `MawRules.cpp:73-85` | matches |
| 1786 | `getCCDurationMult` (0.6/0.45/0.3/0.15 → 0/0.25/0.5/0.75) | `mawDiminishingReturnsMultiplier` (`MawSpellFormulas.cpp:150-157`) | matches |
| 1801 | `checkDebuffDuration` (pre-check, no record) | `diminishedCrowdControlSeconds` returns 0 when immune | matches |
| 1817 | `calcDebuffDuration` (group 1 exempt, immune → 0 unrecorded, boss NameId 220-299 halved, record) | `MawRules.cpp:59-98` (boss = `bossAffix != 0`) | matches |
| 1855 | `calcEffectChance` (only feeds an unused `hit`) | `mawStunChance` (Stun's own roll) | not applicable here (dead in this handler) |
| 1871-1889 | GameInitialized2: `spellCost` snapshot; Lifedrain 10/15, Chain Lightning 20/30; `spells` list; `lastIndex` | `content/spells_patch.txt`; `DamageSpells` (`MawSpellFormulas.cpp:12-15`) | matches (GAPS A7.6) |
| 1892-1933 | `spellPowers` table (37 spells + 200/201) | patched `spells.txt` dice/add, `MawDamageSpells` (`MawCombatRules.cpp:700-703`) | matches (first pass sampled the table) |
| 1937 | `events.CalcSpellDamage` (Mass Distortion share; Ascension from Learning or the Elementalist average of base skills; Elementalist stacks ×(1+0.1n) on dice and add; roll or fixed per point; Fire Spike ×8/6, ×10/6; Lifedrain ×5/3, ×7/3; dragons and DK skip Intellect, crit and enchantments; Int/Pers ×(1+max/1000); crit; per slot enchant + Fire Aura ×1.015^asc, /2.5 on area spells) | `MawCombatRules::rollSpellDamage` (`MawCombatRules.cpp:1810-1912`), `mawCasterSpellDice` (`:1751-1774`), class spells `classSpellDamage`, Flame Blast branch | Mass Distortion known SPL-1; rest matches (DK damage spells are all class spells; `STAT_DAMAGE_DIVISOR` = 1000) |
| 2043 | `ascendSpellDamage` (Empower on Haste's row × min/max/add, dice ×(1+0.02s)1.025^s, add ×(1+0.01s²)1.025^s, rounded) | `mawAscendedSpellDice` (`MawCombatFormulas.cpp:331-339`) | matches |
| 2063 | `ascendHealingValues` | `mawHealAmount` (`MawSpellFormulas.cpp:197-210`) | matches |
| 2069 | `ascendSpellHealing` | same | matches |
| 2079-2092 | `spellbonusdamage` table | — | not applicable (unused in MAW) |
| 2094 | `aoespells` (17 ids) | `isAreaSpell` (`MawCombatRules.cpp:184-190`) | matches |
| 2097, 2102 | `dmgAddTooltip`, `diceMaxTooltip` | `values["add"]`, `values["dice"]` (`MawSpellRules.cpp:285-292`) | matches |
| 2108-2114 | `healingList`; GameInitialized2 backing up heal tooltips | `texts.yml` | not applicable (text) |
| 2116 | `events.Action` → `ascension()` next tick | costs computed per cast (`MawSpellRules::manaCost`) | not applicable (MAW rewrites the global table per selected member) |
| 2144 | `mawTick_Ascension` (re-ascend for the selected or lowest-recovery member) | same | not applicable |
| 2169 | `healingSpellList` | — | not applicable (unused) |
| 2172 | `getPersonalityManaCostReduction` (0.99^(Pers/(10 + 0.06 min(total level,1000)))) | `mawPersonalityCostFactor` (`MawSpellFormulas.cpp:56-59`) | matches |
| 2182 | `ascendCCSpellCosts` (CC curve, cap 65000; Dragon Fear 15/15/25/30) | `mawSpellManaCost` CrowdControl, `MawSpellRules.cpp:490-494` | finding FSPS-2-5 (cap); curve and Dragon Fear match |
| 2201-2212 | `CC_TOOLTIP_LEVELS_PER_RESISTANCE`, `learnableSpells`, `tierMinMastery`, `GetSpellMinMastery` | engine spell tiers | not applicable (tooltips; tiers are the engine's) |
| 2216 | `ascendCCTooltips` | `values["cc_seconds"]` (`MawSpellRules.cpp:316-320`) | differs in display only (note) |
| 2233 | `ascensionLevel` (Learning; Elementalist average of 4, Shaman of 7, GM) | `mawAscension` (`MawClassRules.cpp:748-785`) | matches |
| 2264 | `ascendSpellCosts` (damage curve, Elementalist stacks, Mass Distortion GM by level) | `MawSpellRules::manaCost` (`MawSpellRules.cpp:470-532`) | finding FSPS-2-5 (Elementalist cap); Mass Distortion order known SPL-12; rest matches |
| 2281 | `ascendDamageTooltips` | `texts.yml` + `mawCasterSpellDice` values | not applicable (text) |
| 2334 | `getBaseHealingSpells` (normal and Insanity tables) | `mawHealSpell` (`MawSpellFormulas.cpp:159-195`), `insanityHeals` | matches (every cell) |
| 2355 | `ascendHealingSpells` (heal cost curve rounded, Ascension heal values, Shaman ×(1+Σ/400) except Power Cure) | `MawSpellRules::manaCost` heal branch, `healAmount` (`MawSpellRules.cpp:602-637`) | matches (Shaman skill choice known CLS-2; rounding order note) |
| 2387 | `ascendHealingTooltips` (writes heal costs into Game.Spells; Raise Dead GM text) | `texts.yml`, `manaCost` | matches (Raise Dead behaviour known SPL-15) |
| 2436 | `ascendRemaining` (aura and utility costs 0, reservation lines, recovery-time lines, "Not Learned"/"Can't learn") | `MawSpellRules::spellTooltip` (`:369-398`), `manaCost` aura → 0 (`:483-486`) | matches (unlearned-spell lines not applicable: our spellbook lists known spells) |
| 2541 | `ascension` (DK/Assassin delegate to class tooltips) | `MawSpellRules::spellTooltip` class-spell values | matches |
| 2576 | GameInitialized2: `spScaling`/`hpScalings` snapshot; DK 3/6/9, Shaman 1/1.5/2, Thief line 7.5 | `classSpellFactor`, `classHealthFactor`, `reservesNothing` (`MawSpellRules.cpp:169-202`) | matches (DK and Thief line reserve nothing, so their overrides only reach MAW's tooltip) |
| 2608-2642 | `buffSpell`, `utilitySpell` tables (costs, sounds, buff slots) | `mawAura` table (`MawAuras.cpp`) | matches (first pass checked the 25 + 3 auras and costs) |
| 2644-2649 | `buffSpellList`, `utilityBuffs`, `mawPartyBuffList`, `mawPartyBuffIgnore`, `mawSingleBuffList` | `MawSpellRules::updateAuras` | covered by F3's slice (aura pass) |

### Scripts/General/zzMaw-Spells.lua, lines 2576-3864

| MAW line | function/handler | OpenYAMM counterpart | status |
|---|---|---|---|
| 2576-2605 | `GameInitialized2`: `spScaling`/`hpScalings` snapshot (DK 3/6/9, Shaman 1/1.5/2, Thief line 7.5); `vars.MAWSETTINGS`, `_maw_local_off` | `classSpellFactor`/`classHealthFactor` (`MawSpellRules.cpp:180-201`, Shaman overrides; DK/Thief line reserve nothing so their 3/6/9/7.5 never matter) | matches |
| 2608-2634 | `buffSpell` table (costs, party/single/multi buff slots) | `MawAuras.cpp:12-19` costs; slot mapping in `updateAuras` | matches (costs checked; Fly and Invisibility not auras, as MAW's commented rows) |
| 2635-2642 | `utilitySpell` (Torch 5, Wizard Eye 5, Water Walk 20) | `MawAuras.cpp:18` | matches |
| 2644-2649 | `buffSpellList`, `utilityBuffs`, `mawPartyBuffList`, `mawPartyBuffIgnore`, `mawSingleBuffList` | `updateAuras` slot sets, `m_appliedPartyBuffs`/`m_appliedCharacterBuffs` | matches (MAW wipes every listed slot each pass, ours only the slots auras set: covered by L5.1/dev 100-101); see FSPS-2-7 |
| 2655 | `GetBuffMultiplier` (Base/100 + Scaling·s/1000) | `mawBuffMultiplier` (`MawCombatFormulas.cpp:190-201`) | matches (mastery-independent table) |
| 2665 | `GetBuffStatPct` min(10+s/5 or s/7, 20) % | `mawAuraStatPercent` (`MawAuras.cpp:63-66`) | matches |
| 2670-2691 | `buffPower` table (resistances/DoP Base 10) | `MawCombatFormulas.cpp:21-41` (Base 20) | finding FSPS-2-6 (live MAW is 20 via `Global/zzMaw_Mapping.lua`; SPL-2 wrong) |
| 2694 | `events.LoadMap`: init `vars.mawbuff`, drop scroll/pedestal auras of other maps on outdoor maps, temples on any change, reapply | `updateAuras` map-change block (`MawSpellRules.cpp:1070-1087`), `MawGameState::fixedAuraMaps` | matches (L5.1) |
| 2730 | `events.LeaveMap`: flag temple removal | same block | matches |
| 2737 | `events.Action` 142: buff/utility cast handled as toggle | `PartySpellSystem.cpp:1505-1537` → `castAura` | matches |
| 2746 | `events.PlayerCastSpell`: scroll/pedestal → aura of the map; member cast → `mawBuffCast` | `castSourceBuff` (`MawSpellRules.cpp:895-928`); `castAura` | known dev 100, 101 (member's hold kept; every map event a source) |
| 2761 | `getBuffCost`: cost/(SPFactor + Enlightenment m/2) % of full SP (HP with Legendary 32); utility flat | `mawAuraReservedPercent`, `mawUtilityAuraReservation`, `castAura` (`MawSpellRules.cpp:1038-1052`) | matches (MAW's cast check uses the utility cost without the Enlightenment cut, its lock with it; ours both with it: ≤2 points) |
| 2788 | `mawBuffCast`: toggle, take over, unreserved-pool check (skipped in houses), recovery, temple donation → "Temple", release without recovery | `castAura`; `PartySpellSystem.cpp:1505-1537`; temples via `BuffSource::Temple` | matches (A7.11); messages cosmetic (notes); `_maw_local_off` multiplayer-only, not applicable |
| 2863 | `mawBuffApply` (0.5 s pass, `zzMaw-Timers.lua:95`): wipe, Torch power m+1, held auras one week, PfM 50/GM, DoP/HoP multibuffs, Immolation caster, vampire night Preservation, solo Wizard Eye/Torch, Cartographer Wizard Eye, Magic Protection potion, Shadow boss blinding, `mawRefresh`, `buffManaLock` | `MawSpellRules::updateAuras` (`:1063-1397`), `MawClassRules.cpp:481-494` (vampires), `MawMonsterRules.cpp:1770-1779` (Shadow) | known SPL-3 (PfM), SPL-4 (duration), SPL-9 (Immolation), CLS-6 (21:00), A7.12 (solo/Cartographer), A3.6 (Shadow); finding FSPS-2-7; rest matches |
| 3010 | `buffManaLock`: SP and HP pools after reservations, DK/Thief line reserve nothing, SP=min(ceil(pool),SP), HP likewise | `reservedPoints` (`:808-844`), clamp at `:1384-1396` | matches (rounding note) |
| 3065 | `GetPlayerFromIndex` | member index holders (`auraHolders`) | not applicable (helper); holder remap A7.3 |
| 3079 | `getSpecialBuffSkill` 7, Master, 40 | `updateAuras` `MawAuraSource{7, 3, 40, 0}` (`:1098`) | matches |
| 3083 | `getCasterBuffSkill`: school 11+ceil(id/11), base skill capped 50/75, LevelBase, 0 if unconscious; `MAW_StrongerRemoteBuff` | `updateAuras` `:1110-1124`, `MawAura::skillCap`, `mawSpellSchoolSkill` | matches; remote buff multiplayer-only, not applicable |
| 3111-3120 | potion constants (Master, 0.75-1.5 over 200, spans 50/70, level 0.5/power, DoP 1.4) | `MawAuras.cpp:69-87` | matches |
| 3122 | `GetPotionBuffFraction` | `mawPotionAuraFraction` | matches |
| 3127 | `GetPotionBuffSkill` | `mawPotionAuraSkill` | matches (negative skill: known SPL-17) |
| 3133 | `GetPotionBuffLevel` | `mawPotionAuraLevel` | matches |
| 3138 | `setPotionBuff` (per drinker expiry and power) | `CharacterRulesetState::potionEffect(Aura, spell)` | matches (alchemy side: ALC area) |
| 3148 | `potionBuffActive` | `MawRules::potionAura` (`MawRules.cpp:527-541`) | matches |
| 3156-3160 | `HOUR_OF_POWER_DIVISOR` 1.5, `buffValueMult` | `MawRules::auraSkill` (`:549-561`) | matches |
| 3162 | `buffValueFlat` (Base + L/4)(1 + Scaling/100·s) | `mawAuraFlat` | matches |
| 3170 | `bestBuffSource` (own vs Hour of Power at s/1.5) | `auraSkill`; Stone Skin in `updateAuras` `:1176-1183`, `addPotionAuraFlats` | matches |
| 3183 | `potionBuffPower` | `potionEffect` power | matches |
| 3188-3202 | `flatBuffs`, `buffStrength` | `mawAuraStrength` (`MawAuras.cpp:89-94`) | matches (spells outside `buffPower` compare as 0 in ours vs skill in MAW; only Preservation/PfM, whose potions apply only without an aura: no effect) |
| 3204 | `getBuffSkill` (potion wins when stronger) | `MawRules::memberAura` (`:511-525`) | matches |
| 3221 | `adjustSpellTooltips` (ON texts; OFF branch restores base texts and school "Grants 3 X" lines) | `MawSpellRules::spellTooltip` + `data/texts.yml` | matches (shows applied numbers; Empower reads Haste's row as MAW's effect does, SP:2046-2048); OFF branch: Buff Rework switch is on MAW's multiplayer-only settings page (`zz_Maw-initialize.lua:536-565`), not applicable |
| 3427 | `GameInitialized2`: tooltips, `oldSpellTooltips` | — | not applicable (UI bookkeeping) |
| 3435 | `PlayerCastSpell` Summon Wisp extra wisps (2m−3) | `PartySpellSystem.cpp` wisp branch | known SPL-8 |
| 3460 | `getReservedManaShare` | `mawMeditationPool` (`MawSkillFormulas.cpp:262-270`) fed `reservedSpellPoints` | matches (0 for DK/Thief line and Legendary 32) |
| 3475 | `getMeditationRegen` | `MawSkillRules` Meditation (`:1020-1060`) | matches (checked by SKL) |
| 3489 | `getMaxMana` (unreserved pool) used by leech/refill caps in Damage.lua | per-frame clamp in `updateAuras` `:1384-1396`; `MawCombatRules.cpp:2989` | matches (clamped each frame) |
| 3511 | `getClosestMonsterInRange` (Chain Lightning leaps, Damage.lua:403) | `GameplayProjectileService::buildChainSpawnRequest` | known dev 44 |
| 3539 | `KeyDown` Tab: next school page | `tabCyclesSpellbookSchools` | known A7.13 (done) |
| 3565-3604 | commented-out Insanity book pictures / `CanLearnSpell` | — | not applicable (dead code) |
| 3607 | `GameInitialized2`: Assassin school text copies, `spellDesc2`; `CalcStatBonusByItems` Thief line SP = Earth mastery ×10 | `MawClassRules.cpp:292-296` (replaces item SP), `MawSpellRules::spellName`/`spellTooltip` | matches |
| 3637-3705 | `GameInitialized2`: spellbook pictures by school/tier, sealed books 971-979 names, notes, "Book", sprite 78 | `content/items_patch.txt` 971-979 | known dev 133 (pictures); names/unidentified name match |
| 3707 | `ItemGenerated`: seal books 400-498/1202-1300/1902-2018 (ceil /11, /13) except shop screens | `MawItemRules::rollPlainItem` (`:794-801`), `sealableBookSchool` (`:729-747`) | matches (A7.14) |
| 3728 | `CanCastTownPortal`: Beyond Madness near enemies | `MawMonsterRules::teleportBlockedNearEnemies` (`:1793-1797`) | known SPL-16 |
| 3739 | `PlayerCastSpell`: re-aim a spell's object at the closest visible hostile when no monster under the mouse | `GameplaySpellService.cpp:275-284` | matches for quick-cast (note) |
| 3781 | `MonsterAttacked`: Lifedrain 111→200, Souldrinker 99→201 | `MawCombatRules` leech (A1.15), `PartySpellSystem.cpp:2616-2657` | known SPL-7, A1.15 |
| 3792-3847 | commented-out ironman `PartyDies` and `mulhook` | — | not applicable (dead code) |
| 3849 | `mawTick_InsanityShieldStrip`: Insanity modes strip Invisibility on red alert | `MawCombatRules.cpp:2483-2489` | matches |
| 3860 | `GameInitialized2`: scheduler (Ascension every frame, strip every 100 ms) | per-frame `updateCombat` | matches (Ascension tick is F2's) |

### Scripts/General/zzMAW-Skills.lua, lines 1-1135

| MAW line | Function / handler / statement | OpenYAMM counterpart | Status |
|---|---|---|---|
| 1 | `UncapSkills` | — | not applicable (engine skill-encoding migration 0x40/0x80/0x100 → 0x400+; our skills store level and mastery apart) |
| 15 | `events.LoadMap` (one-time uncap) | — | not applicable (same) |
| 25 | `baseRecovery` table | `WeaponSkills` `MawCombatRules.cpp:363-372` | matches |
| 37 | `weaponImpair` table | `armorImpairment` `MawCombatRules.cpp:~390-408` | matches |
| 45 | `skillAttack` table | `WeaponAttack/SpearAttack/UnarmedAttack` `MawCharacterSheet.cpp:23-25` | matches |
| 59 | `skillRecovery` table | `WeaponSkills` rows, `UnarmedRecoveryPerPoint` `MawCombatRules.cpp:363-373` | matches |
| 72 | `skillDamage` table | `MawCharacterSheet` damage rows | matches (SKL checked) |
| 86 | `skillAC` table | `StaffArmor/SwordArmor/SpearArmor/DodgingArmor` `MawCharacterSheet.cpp:26-29` | matches |
| 105 | `bodybuildingHP` | `BodybuildingPercent` `MawSkillRules.cpp:381` | matches |
| 107 | `skillResistance` (Staff) | staff party resistance (GAPS L5.6) | matches |
| 125, 132 | `skillItemAC`, `skillItemRes` | `BodyArmorPercent`, `ShieldArmorPercent`, resistance rows `MawCharacterSheet.cpp:30-35` | matches |
| 141 | `twoHandedWeaponDamageBonusByMastery` | — | not applicable (never read in MAW) |
| 149 | `armsmasterSkill` | `ArmsmasterDamage` `MawCharacterSheet.cpp:37`, `ArmsmasterSpeedPerPoint` `MawCombatRules.cpp:374` | matches (code); popup text finding FSPS-2-8 |
| 155 | `dkDamageSkill` | `MawClassRules.cpp:598` | matches (read by zzMaw-Items, CLS/CMB area) |
| 157 | `MawArmsmasterApplies` | `mawCharacterAttackDelay` `MawCombatRules.cpp:1227-1231`, sheet rows | matches |
| 162 | `skillCap` | `mawSkillLevelCap` `MawSkillFormulas.cpp:78-96` | matches |
| 169 | `skillEffectCap` (buff 50, day 75) | aura skill caps (SPL checked-matching) | matches (spell area) |
| 174 | `skillCapExtra` | Alchemy reagent excess, GAPS A4.5 | known A4.5 (alchemy area) |
| 176 | `skillMasteryLadder` | `mawSkillMasteryLadder` `MawSkillFormulas.cpp:98-123` | matches |
| 183-196 | `skillTrainHook[50]` (Cover 30 teaches Retaliation) | `MawSkillRules::afterSkillRaised` `MawSkillRules.cpp:229-234` | matches |
| 198-213 | `GameInitialized2` → `events.GetSkill` (2× cap, extra) | `MawSkillRules::applyStatBonuses` `MawSkillRules.cpp:350-375` | matches (GAPS A5.5) |
| 215-219 | requirement tables, `horizontalSkills` | `mawMasteryRequiredLevel`, `mawIsHorizontalSkill` `MawSkillFormulas.cpp:25-31, 125-134` | matches |
| 221 | `GetLearningRequirements` | `MawSkillRules::skillMode` + `masteryRequiredLevel` `MawSkillRules.cpp:95-111, 1244-1252` | matches (Doom → 6/12/20, Insanity 8/16/25, Madness 10/24/40) |
| 238 | `refundSharedCost` | `MawSkillRules::skillRaiseCost`, `mawSharedRaiseCost`, `mawIsSharedCostSkill` | matches |
| 264 | `restoreMasteries` | `restoreRememberedMastery` `MawSkillRules.cpp:181-212` | matches (respec part); progression part known SKL-5 |
| 300 | `applyCap` | `skillLevelCap` `MawSkillRules.cpp:174-179` | matches |
| 322 | `autoLearnMastery` | `afterSkillRaised` ladder `MawSkillRules.cpp:236-251` | matches (see note) |
| 337 | `armsmasterSupreme` | — | not ported (status-line flourish only; Supreme rule in `mawSupremeArmsmaster`, SKL-3) |
| 348 | `events.Action` 121 ("+") | `afterSkillRaised`; `checkSoloMastery` → `applySoloMasteries` (GAPS L5.3) | matches |
| 366-399 | commented-out party share | — | not applicable (disabled in MAW) |
| 402 | `events.CalcStatBonusBySkills` (zero) | `MawSkillRules::combatRows` replaces the sheet | matches |
| 408 | `SPELL_HASTE_DIVISOR` 20 | `mawSpellDelay` `MawCombatFormulas.cpp` (floor(speed/20)) | matches |
| 410, 420 | `GetSpeedBonusFromStat`, `GetSpeedBonus` | `mawSpeedRecoveryBonus` | matches |
| 424-440 | `ITEM_RECOVERY_LEVEL_CAP`, `getItemRecovery` | `mawItemRecovery` `MawCombatFormulas.cpp` | matches |
| 442-617 | `events.GetAttackDelay` | `mawCharacterAttackDelay` `MawCombatRules.cpp:1120-1253`, `mawAttackDelay` | matches (blaster 40/0.4, swiftness, paid-once skills, off-hand 2h axe, staff GM Unarmed, bare hands, mean base, Armsmaster, DK/Seraph/Assassin, impairment, Haste); broken items known SKL-7; class perks effective skill known CLS-2; disableBow dev 137 |
| 619 | `calculateAngle` | `GameplayProjectileService.cpp:1907-1918` | finding FSPS-2-10 |
| 631, 639 | `unhittableStates`, `navigateMissile` | party: `attachPartyMissileHoming` (both worlds); monsters: `attachTrueAim` cone | finding FSPS-2-10 (party side matches) |
| 735 | `mawTick_HomingProjectiles` (setting) | `partyMissileHomingTurnRate`, `monsterMissileHomingConeRadians` `MawCombatRules.cpp:2041-2051` (preference) | known L3.5; FSPS-2-10 |
| 748 | `GameInitialized2` weapon skill descriptions and tables | `texts.yml` `skills:` Staff…Unarmed, `MawSkillRules::skillTooltip` | matches |
| 829 | `GameInitialized2` armour descriptions, special lines, Armsmaster | `texts.yml` Shield/Leather/Chain/Plate/Dodging/Armsmaster | matches except Armsmaster: finding FSPS-2-8 |
| 946 | `getDistance` | — | not applicable (helper for Charge) |
| 953 | `events.KeyDown` Knight Charge | `MawClassRules::partyCharge`, `dashParty` | known dev 48; question FSPS-2-9 |
| 1008 | `events.LoadMap` (charge state) | — | known dev 48 (cooldown session-only) |
| 1014, 1020 | `chargeTimer`, `mawTick_ChargeMovement` | `IGameplayWorldRuntime::dashParty` | known dev 48; FSPS-2-9 |
| 1042, 1072 | Health potion hotkey and its cooldown `Timer` | — | not ported (GAPS L7.6) |
| 1086, 1113 | Mana potion hotkey and its cooldown `Timer` | — | not ported (GAPS L7.6) |
| 1125 | `checkbonus` | — | not applicable (no caller in MAW) |
| 1135 | `sharedSkills` | `mawIsSharedCostSkill` `MawSkillFormulas.cpp:158-174` | matches |

### Scripts/General/zzMAW-Skills.lua, lines 1125-2735

| MAW line | function/handler | OpenYAMM counterpart | status |
|---|---|---|---|
| 1125 | `checkbonus(enchant, player)` (best standard-enchant strength) | helper; no caller in this slice; items' enchant reading in `MawItemRules` | not applicable (helper) |
| 1135 | global `sharedSkills = {0-7, 12-22}` | `mawIsSharedCostSkill` (`MawSkillFormulas.cpp`), used by respec (zzMAWRespec.lua:62) | matches |
| 1136 | `LoadMap`: `vars.weaponSkillRefunded` (old magic-only discount → shared-set refund, current Party only) | none needed: on a new game every skill is 1, so refund1 − refund2 = 0 | not applicable (save migration; TRAINERS_SKILLS §4.4) |
| 1222 | `PlayerAttacked`: Cover (mastery by attack: physical Novice, other attack Expert, spell Master; chance min(10+s, 40) % + 15 % bonus; highest current HP of the successful rollers; solo halves; Fixator retarget to lowest max HP conscious; Legendary 23 +3 % HP; Retaliation s % per cover, stacks 1 / 3 at GM) | `MawCombatRules::coverMonsterAttack` (`MawCombatRules.cpp:2084-2135`), `mawCoverRequiredMastery`/`mawCoverChance` (`MawSkillFormulas.cpp:33-41`), Fixator `MawCombatRules.cpp:2555-2570`, `GameplayCombatController.cpp:1763`; retaliation window 10 s = MAW's 5 game minutes (DM:880) | matches (dev 20, 21; CMB-20, CMB-23 known) |
| 1316 | `Regeneration` event: auto-repair (best acting Repair s×m ≥ IdRepSt, "Repaired") | `MawCombatRules::updateArtifacts` 5-minute tick (`MawCombatRules.cpp:2286-2320`) | matches (GAPS A5.2; see note on MAW's `or`) |
| 1338-1344 | globals `regenHP/regenSP/lastHP/lastSP/waitHP/waitSP`, `classesWithNoMeditationRegen` {10,11,34-37,56-58} | `RegenerationTrack` per slot (`MawSkillRules.h`), `noMeditationAura` (`MawSkillRules.cpp:33-40`) | matches (SKL-8 known for slot keying) |
| 1346 | `getBuffHealthRegen` (Regeneration rate × √(est×full), GM ×(1+(1−max(HP/full,−1))²), items 0.2 %/s each, aura vs potion max) | `MawSkillRules::regenerationPerSecond` (`MawSkillRules.cpp:1002-1028`), `mawRegenerationHealthPerSecond` (`MawSkillFormulas.cpp:208-230`), aura/potion formulas | matches |
| 1384 | `MawRegen` (0.1 s tick: conditions <14/17/18, affix 22, ×2 after 20 s, ×4 without alert, HP carry, Unconscious cleared at HP>0; SP: Insane stops, artifacts 0.2 %/s of pool, Meditation aura, dragon 0.2/0.5, Assassin energy, cap at unreserved pool) | `MawSkillRules::updateRegeneration` (`MawSkillRules.cpp:1156-1242`), dragon/Assassin refill in `MawClassRules::update` | matches except known SKL-1 (negative HP), SKL-6/CLS-9 (dragon/Assassin gates); recount part not ported (dev 136) |
| 1494 | `getDragonRegenLeech` (Regeneration / expected skill at target level × 5 %, dragon race) | `MawCombatRules.cpp:2883-2889`; tooltip `MawSkillRules.cpp:545-557` | matches |
| 1504 | `GameInitialized2`: capture base Regeneration/Meditation/Ascension descriptions | texts in `rulesets/maw/data/texts.yml` | not applicable (text capture) |
| 1511 | `LoadMap`: `vars.hirelingFix` (skill words > 4864 re-encoded, set on new games by zzMaw-Items.lua:2421) | none | not applicable (engine skill-word encoding of the DLL) |
| 1539 | `GetLearningTotalSkill` → 0 | `MawExperienceRules::learningGrantsExperience` false (`MawExperienceRules.cpp:326`) | matches (GAPS A5.10) |
| 1544 | `LoadMap`: `vars.learningFix` (Learning refunded and removed for every PlayersArray character) | created characters: dev 27; roster heroes: none | finding FSPS-2-11 |
| 1562 | `GameInitialized2`: Ascension name, Learning mastery texts (mana −12.5/25/37.5/50 %), Perception texts (10/30/50/70 %) | `content/skill_des_patch.txt:2-6`, `data/texts.yml:846-855` | matches |
| 1577 | `GameInitialized2`: houses opening at 6 open at 5 | `content/house_data_patch.txt` (352 rows = the 352 houses with Open 6) | matches (GAPS A5.11) |
| 1589 | `LoadMap`: `vars.ChallengeMode` houses always open, NPC 1177 EventB | none | not applicable (online session variable, PHASE9_SCOPE:99) |
| 1606 | `BeforeNewGameAutosave`: `vars.trainings = {0,0,0}` | none | not applicable (only read by the unused `bolster` at 1663 and multiplayer) |
| 1610 | `BeforeLoadMap`: `vars.trainings` default from MMLVL | none | not applicable (same) |
| 1616 | `CalcTrainingTime`: count trainings by continent (stale `currentWorld` global), 2 days, ChallengeMode 0 | `MawExperienceRules::trainingDurationMinutes` 2 days (`MawExperienceRules.cpp:321-324`); `currentWorld` effect dev 75 | matches (dev 75; ChallengeMode online-only) |
| 1627-1641 | `trainingCenters` table, `GameInitialized2`: base hall caps (−1 → 2750, min 10) | `mawTrainingHallCap` (`MawSkillFormulas.cpp:278-282`), `MawExperienceRules::trainingLevelCap` | matches (halls 17-19, which MAW never rescales, are placeholders) |
| 1643 | `Action`: Insanity training price `estimateSkill(level) + 4` | `MawSkillRules::trainingPriceMultiplier` (`MawSkillRules.cpp:813-821`) | matches (P9.I5) |
| 1660 | `LoadMap`: hall caps round(base^1.5/20)×10, Madness /10, continent 4 untouched | `MawExperienceRules::trainingLevelCap` | matches |
| 1678-1784 | commented-out Minotaur axe handlers (`Action`, `Tick`, `CanWearItem`) | — | not applicable (dead code) |
| 1787 | `CanDualWield` (Seraphim no off-hand sword) | `MawItemRules::wield` (`MawItemRules.cpp:1445-1473`) | matches |
| 1796 | `tempSkillForEquip` (fake skill for one equip) | `ItemRules::wield` model | not applicable (engine trick) |
| 1806 | `Action` 133: fake Novice Sword to refuse a Seraphim off-hand | `MawItemRules::wield` | matches |
| 1823 | `GameInitialized2`: `oneHandedAxes`/`twoHandedAxes` lists | `itemDefinition.equipStat` | not applicable (lookup tables) |
| 1841-1874 | price tables, `getReqAndCost` (mode prices × (1 + horizontal skills at mastery or remembered `old−1 > mastery`), requirements) | `mawTeacherBasePrice`, `MawSkillRules::masteryTeacherCost` (`MawSkillRules.cpp:1254-1287`), `masteryRequiredLevel` | matches (dev 18, 67; GAPS A5.1, A5.9) |
| 1882 | `ClickNPCTopic` (remember clicked teacher topic) | `teacherSpeech` takes the topic's text | not applicable (UI plumbing) |
| 1886 | `AfterPopulateNPCDialog`: rewrite teacher text (price ≥ 100, requirement digit, appended line), re-print on member switch | `MawSkillRules::teacherSpeech` (`MawSkillRules.cpp:857-955`) | matches (GAPS A5.8) |
| 1950 | `CanTeachSkillMastery`: base skill < requirement → NPCText 128; Party.Gold < cost → 125; price in text | `MasteryTeacherDialog.cpp:349-370` (base level, engine requirement also applies as in MAW's `t.Allow` gate), `masteryTeacherCost` | matches (dev 67) |
| 1976 | `horizontalModeMasteries` (free → horizontal strips skills 0-23 below requirement, stores; back restores) | `MawSkillRules::applyProgressionMasteries` (`MawSkillRules.cpp:1056-1104`) | matches (GAPS L5.2; SKL-5 known) |
| 2013 | `Action` → `horizontalModeMasteries` (also timer zzMaw-Timers.lua:86) | called from `updateRegeneration` each frame | matches |
| 2019 | `CanRepairItem`: party best Repair s×m > IdRepSt | `Party::canRepairItem` (`Party.cpp:5255-5263`, party best, ≥) | matches (MAW only adds permission) |
| 2034 | `GetMerchantTotalSkill` (7 + best s×m, Glamour skill×power, GM/≥45 → 100) | `MawItemRules::merchantValue`, `PriceCalculator::rulesMerchantMember` | known dev 45 |
| 2058 | `CanIdentifyItem`: party best Identify s×m > IdRepSt | `Party::canIdentifyItem` (`Party.cpp:5244-5253`) | matches |
| 2072 | `GetDisarmTrapTotalSkill`: party best s×m | Standard disarm (first pass SKL: differs only above Lock 20) | matches |
| 2083 | `CanIdentifyMonster` (avg base level, best effective s×m of members with the base skill, GM always; mastery tiers) | `MawSkillRules::identifyMonsterReveal` (`MawSkillRules.cpp:957-1000`) | matches |
| 2126-2168 | `partySharedSkills`, `mawTick_SoloMastery` (utility masteries 1/4/7/10 while solo, raised ones stored and restored when the party grows; `x or true` makes both flags always true, so it runs every second) | `MawSkillRules::applySoloMasteries` (`MawSkillRules.cpp:1106-1154`), every update | matches (GAPS L5.3; lowered masteries are lost in both) |
| 2171 | `GameInitialized2`: Cover skill 50, texts, learned at Training | `extraHouseSkills` "Training" (`MawSkillRules.cpp:159-172`), `content/skill_des_new.txt:1` | matches |
| 2184 | `mawTick_MiscSkillsUI` (Misc label spacing, default Cover / Mana Shield on) | skills page groups (GAPS L5.4); `coverDisabled`/`manaShieldDisabled` default false | matches |
| 2234 | `KeyDown` P / M / R (Cover, Mana Shield, Elementalist rotation toggles on the skills page) | key actions in the MAW bindings group | matches (GAPS E.6, D.18, dev 139) |
| 2278-2290 | commented-out Mana Shield 32 cap refund | — | not applicable (dead code) |
| 2294 | `CanIdentifyItem`: follower profession 4 identifies | `Party::canIdentifyItem` `hiredNpcHasProfession(…, 4)` (Standard) | matches |
| 2303 | `Action`: NPCText 128 "You don't meet the requirements…" | `engine/data_tables/npc_topic_text.txt` 128 already reads so | matches |
| 2307-2346 | commented-out running/sliding (`KeyDown`, `KeyUp`, `Tick`) | — | not applicable (dead code; movement dev 134) |
| 2350/2392 | `GameInitialized2` + `GetSkill`: racial skills +3 + ⌊base/10⌋ (Human armour/Shield, Elf/Dark Elf Bow/Spear/Meditation, Minotaur Axe, Troll Regeneration/Mace/Staff, Goblin Sword/Mace/Dagger/Leather, Dwarf Shield/Bodybuilding) | `MawClassRules::applyClassBonuses` `FlatSkillBonuses` (`MawClassRules.cpp:52-67, 229-246`), after items so the item cap does not see it | matches |
| 2403 | `BeforeNewGameAutosave`: `vars.needToFixCover` | none | not applicable (roster words for skills 50-52; ours have none) |
| 2407 | `BeforeLoadMap`: Cover, Mana Shield, Enlightenment 0 for every PlayersArray character | none | not applicable (same) |
| 2422 | `GameInitialized2`: Mana Shield (armour skill, texts, Magic shop) | `extraHouseSkills` "Magic Shop", `skill_des_new.txt` | matches |
| 2435 | `GameInitialized2`: Enlightenment (magic skill, texts from `enlightenmentManaPerSkill`, Magic shop) | `extraHouseSkills`, `skill_des_new.txt:3`, `applyResourceBonuses` 0.5-2 %/point (`MawSkillRules.cpp:399-403`) | matches |
| 2450 | `GameInitialized2`: Retaliation (armour skill, texts) | `skill_des_new.txt:4`, auto-learned at Cover 30 (`afterSkillRaised`) | matches |
| 2462 | `GameInitialized2`: Regeneration/Meditation mastery texts (+50/+100 %, GM per HP lost; +25/50/100 %) | `data/texts.yml:830-845` | matches |
| 2480 | `GameInitialized2`: disableBow → dragons' DefAttackR 0 | none | not ported (dev 137) |
| 2490 | `ArrowProjectile` (disableBow) | none | not ported (dev 137) |
| 2496 | `PlaySound` 71 → 83 (disableBow) | none | not ported (dev 137) |
| 2502 | `KeyDown` L: lift 100 units every 5 game minutes | `GameplayActionController::tryUnstuckParty`, `ClassRules::unstuckLift` | matches (GAPS D.12; cooldown not saved, recorded there) |
| 2513-2583 | `pl` global fallback block (`GameLoaded`, `LoadMap`, `Action`, `PlayerCastSpell`, `mawTick_PlFallback`) | none | not applicable (Lua global-nil guard) |
| 2587 | `GetArmsmasterSupremeRequirement` 30 / 50 Insanity / 70 Madness | `mawSupremeArmsmaster` (`MawClassRules.cpp:806-816`) | matches |
| 2598 | `GetSkill`: Legendary 33 +10 to skills 0-4, 6; Supreme +⌊Armsmaster/10⌋ capped at 2×base for classes 16-19; Legendary 25 +10 Learning | `MawItemRules::applyItemEffects` (`MawItemRules.cpp:1288-1301`), `MawClassRules::applyClassBonuses` (`:269-283`) | matches (SKL-3 known; cap-quirk note above) |
| 2629 | `LoadMap`: `vars.BBFIX` Bodybuilding mastery clamped to the class limit (all PlayersArray) | none | not applicable (roster Bodybuilding masteries are within the MAW caps: Cleric B1/B3 vs M, War Troll G10 vs G, Minotaur Lord M8 vs G, Great Wyrm M8/M9 vs G) |
| 2644 | `Action` 133: Dwarf/Minotaur axe off-hand via fake Dagger mastery (1h at Expert Axe, Minotaur 2h at Master) | `MawItemRules::wield` (`MawItemRules.cpp:1458-1470`) | matches |
| 2675 | `mawTick_DwarfAxes` (Dwarf: 1h axes as daggers; Minotaur: every axe one-handed) | `MawItemRules::wield` (Minotaur 2h axes not two-handed) | matches |
| 2727 | `GameInitialized2`: scheduler registrations (homing, charge, solo mastery 1 s, misc UI, pl fallback, dwarf axes) | per-frame ruleset updates | matches (homing/charge are F4's) |

### Scripts/Modules/MawCore/Skills.lua

| MAW line | Entry | OpenYAMM counterpart | Status |
|---|---|---|---|
| 46-69 | module tables, constants (OLD_COUNT 39, NEW_COUNT 128, 128 roster players) | `Character::skills` map (no id or roster limit) | not applicable (storage layout) |
| 71 | `dllPresent` | — | not applicable (no DLL at ef23ee17) |
| 83, 89 | `playerPtr`, `playerId` | — | not applicable (engine pointers) |
| 98, 112 | `rawGet`, `rawSet` (extended skills 39-127) | `Character::skills` | matches (structure) |
| 128 | `valueMastery` | `SkillMastery` | not applicable (encoding) |
| 145, 168 | `syncToVars`, `loadFromVars` (save in vars.MawCore.skillz) | character save (skills map) | matches |
| 195, 208 | `readLines`, `cells` | table loaders | not applicable |
| 217, 233, 238 | `parseModifier`, `isDefaultMod`, `applyMod` (add, clamp max, clamp min) | `ClassSkillTable::getEffectiveCap` (shift, max, min) | matches |
| 249 | `idByName` | — | not applicable |
| 264 | `parseTables` (Class Skillz, Race Skillz first 39 rows, Class Extra, Extra Skillz) | `patches/class_skills.txt`, `content/race_skills.yml` | matches (SKL checked cells; Extra Skillz header-only) |
| 336 | `masteryLimitRaw` (Extra Skillz overrides race) | `getEffectiveCap` | matches (no Extra rows) |
| 350 | `Skills.projectEngineTable` (class row to engine, clamp 4) | class cap table | matches ("S" = GM) |
| 365 | `Skills.nextClass` (Class Extra kind run) | promotion tables | not applicable (used by the SkillTooltip "*" mark; GAPS A6.11 shows promoted caps) |
| 380-466 | `stringBuf`, `getName`, `setName`, `getDesc`, `setDesc`, `restoreDesc` | `skill_des_*`, `MawTexts`, `SkillRules::skillTooltip` | not applicable (text plumbing; texts checked in GAPS L5.4) |
| 477-605 | `Skills.API` get/set/get2/set2 (masteries past GM in extraMastery), get_buffed, new_misc/weapon/armor/magic, learn_at, MasteryLimit (portrait race), MasteryTable_get/set, CleanMastery (inert) | skills map, `extraHouseSkills`, `getEffectiveCap` | matches / not applicable (masteries past GM unused: only two "S" cells, clamped to 4) |
| 616 | `dllWrapper` (legacy DLL bridge) | — | not applicable |
| 699 | `GetMaxSkill` (globals GetMaxSkillLevel / GetMaxAvailableSkill for base MMMerge scripts) | `getEffectiveCap` | matches (callers are base MMMerge: ZombiePlayers, MiscTweaks, NPCMercenaries) |
| 714, 718 | `Skills.isActive`, `Skills.describe` | — | not applicable (debug) |
| 731 | `Skills.start`: category and shop presets | engine house skill lists | not applicable (recorded for an unshipped stage 3; the engine lists apply) |
| 731 | `Skills.start`: GetSkill body hook for ids ≥ 39 | skills map | matches |
| 731 | `Skills.start`: skill + item bonus clamp 60 → 1023 | `MawSkillRules` limits | known GAPS A5.5 (done) |
| 865 | `events.BeforeSaveGame` → syncToVars | save | matches |
| 868 | `events.BeforeLoadMap` → loadFromVars | load | matches |
| 874 | `events.GameInitialized2` → projectEngineTable | table load | matches |
| 885 | `startShared`: GetMaxSkillLevel/GetMaxAvailableSkill, JoinSkill2/SplitSkill2 | — | not applicable (helpers) |
| 897 | `GameInitialized2` (DLL mode initPortraits) | — | not applicable |
| 904 | `GameInitialized2` new_misc(127) glitch workaround | — | not applicable |
| 910, 913 | `BeforeNewGameAutosave` / `BeforeLoadMap`: new-game CleanMastery refund × 500 gold | — | not applicable (CleanMastery inert, refund 0) |

### Scripts/Global/zzMAWRespec.lua

| MAW line | Entry | OpenYAMM counterpart | Status |
|---|---|---|---|
| 1 | npc ids 314, 413, 794 | `content/npc_respec_patch.txt` | matches (topic slots DEVIATIONS 61) |
| 3 | `MakeRespecDude` (greeting, "Skill reset info" topic) | `Global_maw.lua:4-10` event 10010 | known CNT-11 (greeting), topic text differs by design |
| 23 | `changeToRespec` (the topic turns into "I want to reset") | event 10011 always listed | known CNT-11 |
| 35 | `events.LoadMap` (re-registers the three NPCs) | static topic patch | matches |
| 41 | `RespecSkills`: cost 1000 × LevelBase, Party.Gold only, "Not enough gold." | `MawSkillRules::skillResetCost`, `Party::resetActiveMemberSkills` (`Party.cpp:3888-3915`) | matches |
| 51-55 | Austerity: Identify Monster 0 GM for every member | `MawSkillRules.cpp:272-277`, `MawClassRules.cpp:341-361` | matches (same effect) |
| 63-65 | hybrid shared set 12-22 (global `pl`) | `mawIsHybridClass`, `mawIsSharedCostSkill` | known DEVIATIONS 68 |
| 66-102 | shared-set greedy refund, triangular refund for the rest, reset to 1 | `mawSharedSetRefund`, `resetSkills` | matches (level-1 skills: no difference in play) |
| 103-105 | Alchemy kept, its cost subtracted from the floor | `resetSkills` alchemyCost | matches |
| 108-114 | custom skills 50-53 refunded and set to 1 | `resetSkills` (all skills in the map) | matches |
| 117-123 | floor Σ(5+⌊i/10⌋) from level 2 | `mawLevelUpPoints` | matches |
| 127 | `respecMastery` (keeps the higher mastery, skills 0-38) | `rememberedMasteries` | matches (GAPS A5.1) |

### Scripts/Global/zzMAWPotions.lua

| MAW line | Entry | OpenYAMM counterpart | Status |
|---|---|---|---|
| 1 | `PotionEffects[36]` (256 Darkness → special 41, power 100) | `addSpecial`, `potion_effects.yml` 256, crafting data | matches |
| 15 | `PotionEffects[35]` (255 → 6/9/12/15, power 55) | `addSpecial` | matches |
| 28 | `PotionEffects[23]` (243 → 5/8/11/14, power 40) | `addSpecial` | matches |
| 41 | `PotionEffects[24]` (244 → 59 Swift, power 40) | `addSpecial` | matches |
| 54-55 | `ENCHANT_POTION_POWER_SHARE` 1/5, `ENCHANT_POTION_MAX_POWER` 500 | `EnchantItemMaxPower`, `/5.0` | matches |
| 56 | `PotionEffects[18]` (238 Enchant Item: type roll, strength, skill nerf, seed list) | `addFirstEnchant` (`MawCraftingRules.cpp:1090-1130`) | matches; rounding known ALC-14, seed DEVIATIONS 35, identification ALC-9 |
| 94 | `PotionEffects[16]` Harden (commented out) | Standard `{action: harden}` | matches (MAW leaves the base effect) |
