# CMB — Combat and damage audit

Auditor scope: party weapon/missile/spell damage onto monsters, monster damage onto the party, mitigation, hit/dodge/
crit, recovery, leech, traps/environment, status line. MAW at `Maw-Mod-MMMerge` `ef23ee17`; OpenYAMM working tree.
Paths: DM = `Scripts/Modules/MawCore/Damage.lua`, ST = `Scripts/General/zzMaw-Stats.lua`, S = `Scripts/General/zzMAW-Skills.lua`,
IT = `Scripts/General/zzMaw-Items.lua`, SP = `Scripts/General/zzMaw-Spells.lua`, ART = `Scripts/General/zzzMaw_Artifacts.lua`,
MCR = `game/rules/maw/MawCombatRules.cpp`. Read-only; no build or test was run.

Ordered by severity.

### CMB-1: Standard's "×2 vs monster kind" still doubles MAW weapon and bow hits (artifacts and relics)
Severity: P2
Confidence: confirmed (read both sides)
MAW: DM:420-461 (`stage_weaponRecompute`) rebuilds every melee/bow hit from `GetMeleeDamageMin/Max` / `GetRangedDamageMin/Max`;
the engine's slaying multiplier never reaches the result. ART:65-160: "their on-hit effects were hardcoded in the engine
and died when Maw zeroed ItemAdditionalDamage" — Judicious Measure (503), Wyrm Spitter (506), Mace of the Sun (538),
Ebonest (539), Whistlebone (540) get their ×2 only on the artifact's on-hit damage (`MultVs`). Relics such as
Ghoulsbane 1309/1329, 1310, 1319/1333, Conan 2022, 2023 have no MAW on-hit entry at all, so no kind bonus.
OpenYAMM: `game/gameplay/GameplayActionController.cpp:719-750` multiplies the MAW-resolved blow
(`hit.amount = appliedDamage * multiplier`) by `ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster`
for every ruleset; `GameplayProjectileService.cpp:1519-1541, 1658` does the same for arrows. That reads
`rareItemDamageMultiplierAgainstMonster` (`game/items/ItemEnchantRuntime.cpp:155-196`: 503, 506, 538-540, 1309, 1310,
1319, 1329, 1333, 2022, 2023). Under MAW the base blow (and, for arrows, the bow's aura/enchant/artifact add-ons riding
in `projectile.damage`) is doubled, and for 503/506/538-540 the on-hit part is doubled again by `artifactHitRange`
(MCR:662-696). Net: these weapons deal about 2× MAW's damage against their kind.
Not covered by: DEVIATIONS 72/73 (spells and buffs only), GAPS L4.3 ("on-hit damage ... done") — no row on the base multiplier.
Suggested fix: make the kind multiplier a ruleset question (CombatRules hook, MAW returns 1) and keep only
`artifactHitRange`'s versus factor under MAW.

### CMB-2: Legendary 11 (kill halves recovery) never works on melee kills
Severity: P2
Confidence: confirmed (read both sides)
MAW: DM:1099-1116 — on a non-area, non-arrow kill, `RunNextTick` halves `pl.RecoveryDelay`, i.e. the recovery the
killing blow just set.
OpenYAMM: MCR:2753-2757 halves `killer.recoverySecondsRemaining` inside `applyPartyHitEffects`, which
`GameplayActionController.cpp:1154` calls before the blow's recovery is applied at `:1434`
(`applyRecoveryToActiveMember` takes `max(current, recovery)`, `Party.cpp:6474`). The acting member had 0 recovery,
so the halving is lost and the full delay follows. Turn-based combat stores `attack.recoverySeconds` (`:1427-1430`) and is
equally unaffected. Spell kills on later projectile impacts do work.
Not covered by: GAPS L4.1 (Legendary 11 listed as done).
Suggested fix: halve `attack.recoverySeconds` for a melee kill (e.g. return a flag from applyPartyHitEffects, or apply
L11 in executePartyAttack after `killed` is known).

### CMB-3: Dimension affix 12 ("Monster resistances +X") is not implemented
Severity: P2 (dimension maps only; X = 30 + 2·power, e.g. +130 at power 50 → hits ÷2^1.3)
Confidence: confirmed (read both sides)
MAW: `General/zzMaw-Monsters.lua:600-605` — every monster resistance column becomes
`min(base + X, 200 + X, 999)`; devdocs/maw/data/dimension_affixes.yml row 12 status "works".
OpenYAMM: `MawMapAffix::MonsterResistance` (`MawDimensionMaps.h:39`) is never read (no `mapAffix(...MonsterResistance)`
anywhere); hit resistances come straight from the monster table (`GameplayActionController.cpp:752-763`,
`GameplayProjectileService::monsterDamageResistances`), and `mawCappedMonsterResistance` (MCR:711-714) also caps at 200,
which would cut the affix's extra off even if it were added.
Not covered by: DEVIATIONS 59/60 (60 lists only affixes 25 and 33 as not ported), GAPS L8.2.
Suggested fix: add the affix to each resistance in the MAW resistance stage (and the inspect text) and cap at 200 + X.

### CMB-4: An Assassin's Mass Distortion takes Mass Distortion's difficulty scale (GAPS L6.3 "done" is wrong here)
Severity: P2 on Hell/Nightmare/Doom (×0.75 Hell, ×0.58 Nightmare, far less in Doom), P3 below
Confidence: confirmed (read both sides)
MAW: DM:362-391 `stage_massDistortion` scales `t.Result`, but `stage_assassinAttack` (DM:820-866) runs later and replaces
`t.Result` outright (`t.Result=damage*mult`), then ×DamageMult and a second Earth division. The scale is discarded for
Assassins.
OpenYAMM: MCR:770-777 (resistance stage) multiplies the Assassin's blow-based Mass Distortion by
`massDistortionScale(m_rules.options(), &hit.targetFacts)` after the two Earth divisions.
Not covered by: GAPS L6.3 ("divided by the target's Earth resistance twice, at the map's distortion scale") — that row
is done but the scale is not MAW's.
Suggested fix: drop `massDistortionScale` from the Assassin branch.

### CMB-5: A Death Knight's bow hits give no SP, Blood Leech or Death Grasp
Severity: P3
Confidence: confirmed (read both sides)
MAW: DM:745-791 runs the Blood Leech heal/SP cost, Dark Grasp and the per-hit SP refill (`spRegen`, ×1.5 on a kill) for
every `t.DamageKind==4` hit of a DK, arrows included (COMBAT_SPEC §3 "kind Phys (melee or arrows)").
OpenYAMM: MCR:3024-3047 returns for every non-melee DK hit after the spell effects, and the DK block at MCR:3121-3155 sits
behind `if (!meleeBlow) return;`.
Not covered by: no related row.
Suggested fix: run the DK SP/Blood Leech/Grasp block for `meleeBlow || arrow`.

### CMB-6: Dimension affix 26 (slower attacks) only changes the HUD number
Severity: P3
Confidence: confirmed (read both sides)
MAW: `Global/zzMaw_Mapping.lua:19-23` divides every `GetAttackDelay` result by (1 − X/100) — real attacks, the leech
floor and the DK/Assassin spell delays all read it.
OpenYAMM: only `characterAttackRecoveryTicks` (MCR:1315-1331, used by `GameplayHudOverlaySupport.cpp:134`) applies it;
`resolveCharacterAttack` sets `attack.recoverySeconds` from `mawCharacterAttackDelay` without it (MCR:1347-1350, 1375-1377).
Not covered by: DEVIATIONS 59/60, GAPS L8.2.
Suggested fix: apply the affix inside `mawCharacterAttackDelay` (or in resolveCharacterAttack) so every reader sees it.

### CMB-7: Legendary 15 is checked before Mana Shield
Severity: P3
Confidence: confirmed (read both sides)
MAW: DM:1859-1886 — `t.Result = calcManaShield(pl, t.Result)` first, then Legendary 15 fires only if the shielded hit is
still lethal; Divine Protection after it.
OpenYAMM: MCR:2137-2157 runs `legendaryProtection` on the unshielded damage, then Mana Shield. A hit Mana Shield would make
survivable still spends L15's 150-minute cooldown (and resets HP to a quarter, which may be below the HP the member
would have kept).
Not covered by: DEVIATIONS 71 (moves the shields to every hit, not their order).
Suggested fix: Mana Shield, then L15, then Divine Protection.

### CMB-8: The Seraphim/Shaman flat damage cut uses the solo balance model in every party
Severity: P3
Confidence: confirmed (read both sides)
MAW: ST:742-759 `flatClassReduction` uses `getMonsterDamage(false, lvl+1)` and `getPlayerEstimatedVitality`, whose
cover multiplier depends on `Party.Count` (Estimates.lua:424-437: solo ratio 2, party `1 + 6L/(L+240)`).
OpenYAMM: `mawClassDefense` (`game/rules/maw/MawClassRules.cpp:667-675`) always uses `rules.model(1)`; in a 5-member party at
L200 the reduction comes out roughly 10-15 % off MAW's.
Not covered by: no related row.
Suggested fix: pass the party size into `characterMitigation`/`mawClassDefense` and use `rules.model(partyCount)`.

### CMB-9: Post-resistance stage order differs (Adamantite, Legendary 29, Legendary 14, Thorn)
Severity: P3
Confidence: confirmed (read both sides)
MAW (DM:1484-1504 stage list): res division → class overrides → retaliation → boss affixes (Thorn reflects `t.Result`,
Adamantite cuts it) → legendaries (weapon enchant and Fire Aura added, L17, Shaman fire, ×L21, ×max(crit,1) for L14 on
the whole hit) → artifact on-hit → ×(1 + L29 stacks) on the whole hit (DM:1131-1137) → map affixes.
OpenYAMM (MCR:720-870): ×(L29 + spear stacks) before resistance on the base amount only → resistance (base + weapon
elements) → L17/L21 → Adamantite on everything → map affixes; L14's ×max(chance,1) is folded into the base crit
(`critFactor`, MCR:250-254, 1438) so it misses enchant/aura/L17; Thorn/Reflecting return the final `hit.damage`
(elements and artifact damage included, after Adamantite) as physical (MCR:2790-2817). Also the in-pipeline L29 "+1 for
this hit" (MCR:744) is added for every area-spell hit, while MAW adds it only 40 % of the time (DM:569-577; the persistent
stack at MCR:2681-2690 does roll 40 %).
Not covered by: DEVIATIONS 8/11 (other stages), GAPS L4.1.
Suggested fix: move L29 to a final multiplier over the whole hit, run Adamantite before elemental/L17 additions, and apply
the L14 factor after the additions; reflect only the base part for Thorn.

### CMB-10: Elementalist crowd-control spells recover against Learning instead of their school average
Severity: P3
Confidence: confirmed (read both sides)
MAW: ST:178-188, 211-216 — for Elementalists `ascensionSkill = floor(mean of Fire/Air/Water/Earth base skills)` for every
spell category, CC included; CC delay = `round(table · 1.015^(ascension − school skill))`.
OpenYAMM: `MawSpellRules::baseRecoveryTicks` (`MawSpellRules.cpp:571-575`) uses `mawAscension(caster, CrowdControl)`,
which for Elementalists returns Learning (`MawClassRules.cpp:769` excludes CrowdControl from the school average). With
Learning 0 and Earth 50, Slow recovers at 1.015^-50 ≈ 0.48× the table instead of ≈ 1×.
Not covered by: no related row.
Suggested fix: use the CastTime ascension (floored school mean) for the CC delay; keep Learning for CC chance/duration.

### CMB-11: Dragon breath and Flame Blast roll once instead of the two-roll mean, and skip Legendary 14
Severity: P3
Confidence: confirmed (read both sides)
MAW: DM:647-656 `rollDice(low, high)` (mean of two rolls) for breath and Flame Blast; `getCritInfo` includes L14's +10 %
and the legendaries stage multiplies by max(crit, 1) (DM:1074-1080); COMBAT_SPEC §11 table also writes the two-roll mean.
OpenYAMM: `dragonBreathDamage` (MCR:259-283) draws one `uniform_int_distribution(min, max)` and builds `MawCritInputs`
without `overcrit`.
Not covered by: GAPS A6.2.
Suggested fix: use `mawAverageOfTwoRolls` and set `critInputs.overcrit` from Legendary 14.

### CMB-12: Undocumented dragon fixes (question)
Severity: P3
Confidence: confirmed (read both sides)
MAW: stage 20 (DM:597-627) overwrites stage 17's result, so a Weak dragon's bite is not halved; the bite sets
`SP = min(SP + 10, 60)` / `min(SP + 20, 120)`, lowering SP above the cap (COMBAT_SPEC §13 item 8 lists both).
OpenYAMM: MCR:1452-1458 halves a Weak dragon's bite ("a dragon's bite too"); MCR:3115-3119 adds 10/20 SP up to the full
pool. Both are deliberate fixes of MAW bugs but have no DEVIATIONS row (A1.4 is about Weak in general).
Not covered by: DEVIATIONS (none), GAPS A1.4, A6.10.
Suggested fix: add a deviation row, or follow MAW.

### CMB-13: Seraphim on-hit heal and the leech floor read stats without item and permanent bonuses
Severity: P3
Confidence: confirmed (read both sides)
MAW: DM:118-120 heal ×(1 + `pl:GetPersonality()`/1000); DM:1240-1251 floor from `pl:GetAttackDelay()` (full Speed).
OpenYAMM: MCR:3065-3069 uses `member.personality + member.magicalBonuses.personality` and `member.speed +
member.magicalBonuses.speed`; MCR:2913-2917 the same Speed for the leech floor. Item stat bonuses (large in MAW) and
permanent bonuses are left out (the sheet's `.actual` values in `buildCharacterSheetSummary` include them).
Not covered by: no related row.
Suggested fix: read `characterSheet(...).personality.actual` / `.speed.actual` as the other MAW paths do.

### CMB-14: Falls, water, lava and evt.DamagePlayer skip Legendary 18/22 and the monster-crit affix
Severity: P3
Confidence: confirmed (read both sides)
MAW: the trap branch uses `calcMawDamage`, whose `applyPostMitigation` (ST:761-776) applies L18 ×0.9 and L22; the
`map-affixes-player` stage (DM:1934-1951) doubles any hit with affix 2's chance, environment hits included.
OpenYAMM: `environmentDamage` → `trapDamage` (MCR:1980-2017) only runs `mawMitigatedDamage`; the pipeline's
`legendary-defense` and `map-affixes` stages are not reached for `Party::applyMovementEffects` (`Party.cpp:2766-2818`) or
`luaDamagePlayer` (`EventRuntime.cpp:6206-6216`). Chest traps go through the pipeline and do get them.
Not covered by: GAPS A1.6/L3.4.
Suggested fix: route environment hits through `damageToCharacter` (trap branch) or apply the two stages in `trapDamage`.

### CMB-15: Dimension affix 32 (less leech) also cuts the leech floor
Severity: P3
Confidence: confirmed (read both sides)
MAW: DM:1229-1230 cuts `baselineHeal`/`elementalHeal` before the floor; `max(totalHeal, minLeech)` keeps the uncut floor.
OpenYAMM: MCR:2931-2938 takes `max(heal, floor)` first and then multiplies by (1 − X/100).
Not covered by: DEVIATIONS 59.
Suggested fix: apply the cut to `heal` before the floor.

### CMB-16: A bow's aura/enchant/artifact add-ons are halved by Weak and quartered by Carnage
Severity: P3
Confidence: confirmed (read both sides)
MAW: Weak ×0.5 and Carnage ×0.25 apply in `stage_weaponRecompute` (DM:451-459) to the base roll only; the bow slot's
Fire Aura and enchantment (DM:1003-1015) and the artifact on-hit (ART:528-541) are added later, unscaled.
OpenYAMM: MCR:1545-1590 adds `(lowAdd + highAdd)/2` to `attack.damage`, then quarters the total for Carnage
(MCR:1584-1590); `GameplayActionController.cpp:1089-1094` halves the whole `attack.damage` for Weak. (Fanned arrows add the
range after `weakness`, so they are not halved — inconsistent with the single arrow.)
Not covered by: DEVIATIONS 46, GAPS A1.4, D.5.
Suggested fix: add the bow add-ons after the Weak and Carnage factors (pre-scale them by 2 and 4 or move the halving).

### CMB-17: Extra arrows and area-spell targets share one roll and one crit
Severity: P3 (variance only; means are equal)
Confidence: confirmed (read both sides)
MAW: every object hit runs the pipeline: each Master/GM arrow re-rolls `rollDice` and `getCritInfo` (DM:420-449), and
each monster in a fireball's blast gets its own `CalcSpellDamage` roll and crit (SP:1937-2040).
OpenYAMM: the second arrow reuses `projectileRequest.damage` (`GameplayActionController.cpp:1362-1374`); area spells roll
once per cast (`PartySpellSystem.cpp:2533`). DEVIATIONS 44 covers this only for Chain Lightning.
Not covered by: DEVIATIONS 44.
Suggested fix: re-roll per extra arrow; or record the per-cast roll as a deviation.

### CMB-18: Artifact on-hit damage is paced by the artifact alone, not the hands' mean
Severity: P3 (dual-wielding only)
Confidence: confirmed (read both sides)
MAW: ART:451-460 `MawArtifactOnHitDamage` × `GetPlayerBaseRecovery(pl, it)/100` (IT:2106-2122: the mean recovery of both
held weapons, a bow's own).
OpenYAMM: `artifactHitRange` (MCR:690) uses `weaponRecovery(rules, weapon)` (the artifact's own); `enchantPace` already
implements MAW's mean.
Suggested fix: use `enchantPace` in `artifactHitRange`.
Not covered by: GAPS L4.3.

### CMB-19: Assassin spell recovery ignores Subtlety stacks
Severity: P3
Confidence: confirmed (read both sides)
MAW: `GetAssassinSpellDelay` = `pl:GetAttackDelay()*2` (Classes.lua:448-450); `GetAttackDelay` adds `s·stacks/2` for
Assassins (S:540-550).
OpenYAMM: `MawSpellRules::baseRecoveryTicks` (`MawSpellRules.cpp:550-556`) calls `mawCharacterAttackDelay` without the
`extraSpeedPercent` that `resolveCharacterAttack` passes (MCR:1370-1374). The leech floor (MCR:2913) and Seraph heal also
omit it, which only matters for Assassins.
Not covered by: GAPS L6.2.
Suggested fix: pass the Subtlety term in both places.

### CMB-20: Cover against a monster's second spell (question, MAW quirk)
Severity: P3
Confidence: confirmed (read both sides)
MAW: S:1222-1230 — `MonsterAction==2` (Spell 1) needs Master Cover; everything else that is not a physical attack,
including `MonsterAction==3` (Spell 2), needs only Expert.
OpenYAMM: `mawCoverRequiredMastery(spell, physical)` (`MawSkillFormulas.cpp:38-41`) requires Master for every spell.
Not covered by: DEVIATIONS 20 (missile cover only).
Suggested fix: keep ours and add a deviation row (MAW's split looks accidental), or require Expert for Spell 2.

### CMB-21: A Shielded monster still halves MAW arrows and spells (plausible)
Severity: P3
Confidence: plausible (needs a check of where MM8 halves; MAW's weapon recompute discards the engine's damage for arrows)
MAW: DM:420-449 rebuilds arrow damage from the ranged rows, so an engine-side halving of missiles on a monster under
Shield never reaches the result.
OpenYAMM: `GameplayProjectileService::buildProjectileDirectActorImpact` (`:1660-1663`) halves every party projectile
(spells included) when `halveIncomingMissileDamage` is set, for both rulesets.
Not covered by: no related row.
Suggested fix: ask the rules whether the monster Shield halving applies (MAW: not for arrows; check spells).

### CMB-22: Souldrinker's extra 10 % leech goes to every caster (plausible)
Severity: P3
Confidence: plausible (depends on whether OpenYAMM ever casts the vampire objects 200/201 separately)
MAW: DM:1258-1270 adds `baselineHeal·0.1` only for objects with Spell 200 or 201 (the vampires' Lifedrain and
Souldrinker); a Dark mage's Souldrinker is Spell 99 and gets only the spell leech.
OpenYAMM: MCR:2881 `drainSpell = spellId == 111 || spellId == 99` gives the bonus to any Souldrinker caster.
Not covered by: GAPS A1.15.
Suggested fix: limit the 99 case to vampire casters (race Vampire), as MAW's object 201 is theirs.

### CMB-23: Cover state is keyed by member address
Severity: P3
Confidence: plausible (needs a runtime check)
MAW: `vars.retaliation[playerIndex]` (roster index), cover bonus by slot.
OpenYAMM: `m_coverStates` (`MawCombatRules.h:243`) is keyed by `const Character *`. When a member leaves and the vector
shifts, or after a load, another character can sit at the same address and inherit Retaliation stacks (≤10 s) and the
GM cover bonus flag (no expiry).
Not covered by: GAPS A7.3 (auras and class runtime remapping).
Suggested fix: key by a stable member id, or clear the map on party changes and loads.

## Checked and matching

- Monster resistance divisor 2^(res%1000/100), 200 cap (= MAW's `p12 + 200` with no affix); Energy and Irresistible
  unresisted; GM-bow min(Fire, Physical); dragon breath lowest resistance.
- Crit: chance `luck/min(500+5L,3000)+0.05`, multiplier accuracy/intellect÷4 over `min(250+2.5L, 2000|3000)` + 1.5 rounded
  to 0.01, dagger per hand at Master+, axe once at GM, Fate, affixes 20/21, L14 +10 % uncapped; dagger/axe also on arrows
  (MAW quirk §13.20, matched).
- Party hit chance (0.75 at par, slope 0.5, clamp 0.25-1, Bless 5-10 % to skill 50); monster hit = Speed roll
  `1/(1+speed/(100+stat(L))·0.5)` plus GM Dodging `1−1/(1+(s+10)/200)`, dragons never dodge; melee rolls Speed once.
- Attack delay: item recovery `round(base·(0.75+min(L,600)/500)/10)·10`, ×1.25 two-handed; skill/Armsmaster/Unarmed/
  Staff-GM bonuses paid once; swiftness 0.15/0.3; armour impairment; Haste aura; damage multiplier = delay/round(100·scale);
  blaster 40 / ×0.4; Speed bonus curve.
- Spell delay formula (non-CC), Flame Blast 1.5× breath delay, Dragon Fear 120, DK = attack delay, Assassin = 2×.
- Mitigation: armour `1/(AC/(200+6L)+1)` rounded, class cuts (Shaman Air; DK Body/Dark), "of Shielding" ×0.85, Shield
  buff ≥0.7, GM shield once (dev 8), weakest of the listed resistances with item enchant `1/(item/100+1)`, 65000 immunity,
  10 % floor, flat class cut after the floor, L18, L22, affixes 28/29.
- Monster hit: attack 2 by the dice-average ratio, player-school spells ×`monsterSpellMultiplierList` (Ice Blast 0.75),
  monster-only spells keep their roll, round then (R(75,125)+R(75,125))/200, Dark Grasp/Shrinking Ray 0.7 once, disease
  ×1.25/1.5/2 (half extra solo), Exploding halving, solo Cover ×0.5, Mist Form ×0.25, map affixes 1/2/10/14.
- Mana Shield (25-100 %, efficiency 1+s^1.4/60, 5 at 50, cost rounded before the cap), Divine Protection (25 %, 1 HP left,
  150 min), Nightmare death/eradication thresholds with L30.
- Trap damage: model damage at the banked level, Perception `min((11−2m)/10,1)`, own level for armour, Sparks ÷3,
  indoor-all / outdoor-non-physical-non-water rule.
- Real-time poison (1/0.5/0.25 %, ×bolster/100, ×2 insanity, ÷2 solo, 20 s start, 25/+5/50 on repeat).
- Weapon recompute: two-roll mean, Assassination subtraction, ×speed multiplier, crit, Weak on melee/arrows; Mace/Staff
  paralysis chance and 4/2 s durations; Retaliation damage (rounded fourth roots), 25 %·stacks paralysis 2/1 s, recovery
  ×(1−0.3·stacks), 10 s lifetime; Cover chance min(0.1+0.01s,0.4)+0.15, highest-HP coverer, L23, Retaliation stack gain.
- Spell damage: MAW dice/add per spell (spells patch), Ascension scaling, Empower (Haste numbers, §13.1), Elementalist
  stacks ×(1+0.1n), Fire Spike/Lifedrain mastery percents, Int/Per ÷1000, spell crit vs banked level, weapon
  enchant/aura on spells ×1.015^Asc, ÷2.5 on area spells; Shaman ×(1+Σ7 schools/200) except 44 and ≥99.
- DK and Assassin class spells (roll, crit vs target, average enchant+aura, ×speed multiplier, Weak, ×share);
  Death Coil 0.2/0.3, Asphyxiate, Icy Touch slow; Shaman Mind/Body on-hit; Seraph heal target (lowest share, alive).
- Leech: B-tier family HP reference, overkill capped at max HP, elemental part at the spell rate, floor share/5·delay/100,
  ÷2.5 area, ÷4 for 9/22/43, drain spells +10 %, L31 half to SP, L27 overheal, Hades negative leech, vampire/Vampiric
  Aura/DK sources.
- Mass Distortion (non-Assassin): (0.15+0.005s)·current HP, ÷√mult by bolster (Normal 70 → 1), Doom/boss terms on
  capped level, Austerity ×4, (L/250)², then Earth resistance.
- L17 (2 % current HP, ÷(1+phys/100), half on arrows/area, speed or 1.015^Learning), L21 melee-only (D.11), L24, L26,
  spear stacks (2+0.02s)·mult·1.5 halberd on physical hits; friendly-fire zero; Fly → Feather Fall from Hard up.
- Status line wording, short numbers, area total, spell as attacker; Standard keeps its own text (nullopt).
- Standard pipeline equivalence: `CombatRules()` stages reproduce HEAD's `adjustedIncomingDamageForMember` (half missile,
  physical multiplier, `resolveCharacterIncomingDamage`) and HEAD's GM-Unarmed evade; `environmentDamage`,
  `absorbCharacterDamage`, `harmsFriendlyActors`, `partyHitStatusText` are identity/no-op for Standard.
