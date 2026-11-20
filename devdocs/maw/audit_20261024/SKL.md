# SKL audit: skills, trainers, respec, regeneration, NPC followers

Auditor area SKL. MAW paths relative to `/home/pjasicek/github/Maw-Mod-MMMerge/` (S = `Scripts/General/zzMAW-Skills.lua`,
IT = `Scripts/General/zzMaw-Items.lua`, F = `Scripts/Modules/MawCore/Formulas.lua`). OpenYAMM paths relative to the
repository root. Read-only audit of the working tree; no build or tests run.

### SKL-1: MAW regeneration lifts an unconscious member from any negative HP to 0, then awake, in one tick
Severity: P2
Confidence: confirmed (read both sides); the in-play size needs a runtime check
MAW: S:1409-1428 — `MawRegen` runs while unconscious (main condition < 14) and does `pl.HP = min(FHP, pl.HP +
floor(regen))`; a member knocked to −X HP stays unconscious until regeneration has restored X HP (`if pl.HP>0 then
Unconscious=0`).
OpenYAMM: `game/rules/maw/MawSkillRules.cpp:1156-1163` heals through `Party::healMember`, which does
`std::clamp(health + amount, 0, max)` (`game/party/Party.cpp:6815`). The first whole point of regeneration (any
Regeneration skill, aura, potion or regeneration item; every 0.1-1 s) jumps the member from −X to 0, the next to 1,
which clears Unconscious. Knock-outs last a fraction of a second for anyone with regeneration, out of combat and in it.
Related, pre-existing: `clampCurrentResourcesToMaximum` (`game/party/Party.cpp:281-285`) also clamps HP to ≥ 0 on every
`rebuildMagicalBonusesFromBuffs`, which MAW's aura pass triggers regularly.
Not covered by: GAPS A1.7 (death thresholds), L5.4; no DEVIATIONS row.
Suggested fix: add regeneration with a heal that keeps negative HP (as `adjustMemberHealth` does: `min` only, then the
incapacitation update) and, for MAW at least, stop the rebuild clamp from raising negative HP to 0.

### SKL-2: Black-potion stats (stored as permanent bonuses) give no HP or SP
Severity: P2
Confidence: confirmed (read both sides)
MAW: IT:2566-2583 — Pure Power/Wisdom/Resilience (252-254) add +20 per step through `CalcStatBonusByItems`, so
`GetEndurance`/`GetIntellect`/`GetPersonality` include them; the engine's HP (HPFactor × stat effect of Endurance) and
MAW's `addMana` (IT:3132-3146, `pl:GetPersonality()`) count them.
OpenYAMM: `content/potion_effects.yml:216-229` writes them `into: bonus` → `Character::permanentBonuses`
(`game/items/InventoryItemUseRuntime.cpp:213-262`). HP/SP only read base + magical stats:
`MawClassRules::baseMaxHealth`/`baseMaxSpellPoints` use `character.endurance/intellect/personality`
(`game/rules/maw/MawClassRules.cpp:182-225`), `applyMagicalPrimaryStatResourceBonuses` adds only `magicalBonuses`
(`game/party/Party.cpp:262-279`), and `MawSkillRules::applyResourceBonuses` uses `endurance + magicalBonuses.endurance`
(`game/rules/maw/MawSkillRules.cpp:391`). The sheet shows the higher stat; HP and SP ignore it. (MAW's own 1/1000
Endurance HP share excludes black potions too, IT:3102, so only the stat-effect terms differ.) No effect on Standard
(its `into: bonus` potions are Luck and Speed only).
Not covered by: GAPS L7.5 (popups only), dev 25 (SP formula); no row.
Suggested fix: feed `permanentBonuses` of the primary stats into the HP/SP stat-effect terms (the adjusted member in
`applyMagicalPrimaryStatResourceBonuses`, or the MAW base formulas).

### SKL-3: Supreme Armsmaster's damage rank reads the base skill; MAW reads the effective one
Severity: P3
Confidence: confirmed (read both sides)
MAW: IT:2829-2833 — the weapon-row Armsmaster rank becomes 5 (Supreme, 2 damage/point) when `GetSkill(Armsmaster)`,
items and followers included, reaches 30/50/70 at GM for classes 16-19. Only the +⌊s/10⌋ weapon-skill bonus checks
the base level (S:2612-2617).
OpenYAMM: `mawSupremeArmsmaster` (`game/rules/maw/MawClassRules.cpp:805-815`) checks `pSkill->level` (base) and is used
for both: the weapon-skill bonus (`MawClassRules.cpp:269-282`, correct) and the damage rank (`armsmasterMastery`,
`game/rules/maw/MawCharacterSheet.cpp:68-72`). A Knight with +Armsmaster items gets the Supreme damage later than in
MAW.
Not covered by: GAPS A5.6 ("done"; its effective-skill part covers only the bonus amount).
Suggested fix: give `mawSupremeArmsmaster` an "effective level" variant (level + `skillBonus`) for the damage rank.

### SKL-4: Mercenary gear keeps its rarity, legendary affix, drop level and quality
Severity: P3
Confidence: confirmed (read both sides)
MAW: `Scripts/General/NPCMercenaries.lua:348` sets `item.BonusExpireTime=0` on every generated merc item before the
enchantment trim; that field holds the rarity tier, legendary affix, Celestial flag, drop level (wear gate) and cube
quality (`Scripts/General/zMaw_ItemBits.lua:78-100`).
OpenYAMM: `MawItemRules::trimMercenaryItem` (`game/rules/maw/MawItemRules.cpp:2369-2385`) only drops the special or
the second enchantment; the item went through `rollEnchantments` (rarity, legendary affix, `dropLevel` from the
party's level) in `generateEquipmentItem` (`game/gameplay/MercenaryRecruitmentRuntime.cpp:774-810`). Mercenaries can
join with Legendary/Primordial gear and may fail the wear gate on their own items.
Not covered by: GAPS H.8 (lists the enchantment trim only).
Suggested fix: in `trimMercenaryItem` also clear `lootRarity`, `legendaryAffixId`, `dropLevel` and `qualityPercent`.

### SKL-5: Raising a skill in horizontal progression does not return the masteries the switch stored
Severity: P3 (unreachable in normal play: progression cannot change mid-game, only through scenario option changes)
Confidence: confirmed (read both sides)
MAW: S:284-291 — on each "+" click in horizontal mode, masteries stored by the free→horizontal switch come back, as
many ranks as the new level reaches (`while` loop), without a teacher. The switch itself strips every roster
character (`Party.PlayersArray`, S:1983-1996).
OpenYAMM: `afterSkillRaised` restores only `rememberedMasteries` (respec), never `progressionStoredMasteries`
(`game/rules/maw/MawSkillRules.cpp:181-212`); `applyProgressionMasteries` strips only current party members
(`MawSkillRules.cpp:998-1046`), so inn characters keep free-mode masteries.
Not covered by: GAPS L5.2 ("done").
Suggested fix: in `restoreRememberedMastery` also consult `progressionStoredMasteries` (all reachable ranks); or, since
the switch cannot happen in play, note L5.2 as scenario-only.

### SKL-6: Dragon and Assassin SP refill ignores conditions and the slower-regeneration map affix
Severity: P3
Confidence: confirmed (read both sides)
MAW: S:1433-1481 — the Dragon (0.2/0.5 per 0.1 s × mult) and Assassin energy refills sit inside the SP loop: skipped
for Dead/Stoned/Eradicated/Insane members, scaled by dimension affix 22 (`timeMultiplier`), and capped at the pool
left after aura reservations.
OpenYAMM: `MawClassRules::update` (`game/rules/maw/MawClassRules.cpp:443-477`) refills both with no condition check,
no `mapAffix(PlayerRegeneration)` and a cap of the full maximum.
Not covered by: GAPS A6.10 ("done").
Suggested fix: apply the same condition gate, affix factor and reserved-pool cap as `updateRegeneration`.

### SKL-7: Broken weapons and armour still set attack recovery and armour impairment
Severity: P3
Confidence: confirmed (read both sides)
MAW: S:452-588 — recovery and `weaponImpair` read `GetActiveItem`, which returns nil for a broken item
(MMExtension `Structs/00 structs.lua:1713-1719`): a broken weapon attacks at bare-hand pace, broken armour adds no
delay.
OpenYAMM: `mawCharacterAttackDelay` (`game/rules/maw/MawCombatRules.cpp:1137-1139`) and
`mawCharacterArmorImpairment` (`MawCombatRules.cpp:1255-1272`) take the equipment ids without the `broken` check that
`mawCombatRows` uses (`MawCharacterSheet.cpp:156-160`). Rare in practice (MAW auto-repairs, A5.2).
Not covered by: no related row.
Suggested fix: skip broken slots as `mawCombatRows` does.

### SKL-8: Regeneration timers are kept by member slot
Severity: P3
Confidence: confirmed (read code)
MAW: S:1338-1342 — `lastHP/waitHP` by party slot too, so MAW shares this.
OpenYAMM: `m_regeneration` (`MawSkillRules.h:134`) and `m_dragonRefills` are indexed by member index and only
resized; after a dismissal or a swap a member inherits another's 20-second wait and carry. A missed or extra ×2 for at
most 20 s. Listed for the brief's "member index after party changes" check; low value.
Suggested fix: key by character identity, or reset the track when the member at a slot changes.

### Notes (documentation)
- GAPS H.8 says "Left: the skill points and class kinds"; both are implemented (`MawClassRules::mercenarySkillPoints`,
  `mercenaryClassKinds`, `MawClassRules.cpp:823-833, 983-995`, matching NPCMercenaries.lua:13-17, 196-199). The row's
  status is stale; with SKL-4 it is still incomplete.
- `skillCap` comment in MAW says Mana Shield and Enlightenment are learned at the "alchemy shop"; the code passes house
  type 3, which is Magic Shop (MMExtension `const.HouseTypeInv`). Ours follows the code (correct).

## Checked and matching
- Shared raise cost (S:238-262): set {0-7, 12-22}, hybrids (Seraph, DK, Shaman, Thief line = `assassinClass`) only
  12-22, ceil(new/n) with n counting other set skills ≥ new level, no discount above 1000 (`skillRaiseCost`,
  `mawSharedRaiseCost`, `mawIsSharedCostSkill`, `mawIsHybridClass`).
- Skill caps: Alchemy 60, Cover 30, Mana Shield and Retaliation 50, base 500, effective 1023 / 2×cap (S:162-212,
  RemoveSkillValueLimits.lua:24-27).
- Mastery ladders (Cover 6/12/20 or 8/20/30, Mana Shield 6/12/20 or 8/20/32, Enlightenment 6/12/20, Retaliation
  10/24/40), bounded by the class cap; Cover 30 teaches Retaliation (S:176-196, 322-335). Class Skillz rows 50 and 53
  are identical, so our Retaliation class-cap check changes nothing.
- Mastery requirements by mode (4/7/10, 6/12/20 for horizontal or Doom, 8/16/25, 10/24/40) for the horizontal list
  only (S:215-233); Standard 4/7/10 otherwise.
- Teacher prices by mode and escalation (S:1841-1874, dev 18, 67); text rewrite rules (S:1886-1949, A5.8); refusals.
- Respec (zzMAWRespec.lua): 1000 × base level, Party gold only, greedy shared-set refund equals `mawSharedSetRefund`,
  triangular refunds for the rest and the four new skills, Alchemy kept and subtracted from the floor, floor
  Σ(5+⌊i/10⌋), masteries remembered and returned one rank per raise at the mode's requirement.
- Solo utility masteries (S:2126-2168): skills 24,25,26,29,31,34,37, thresholds 1/4/7/10, set up or down, restored on
  growth.
- Identify Monster (S:2083-2124): average base level, best s×m of members with the base skill, GM always.
- Merchant formula 7 + best s×m, GM or ≥45 → 100, no reputation (MMExtension hooks the whole GetMerchant; dev 45).
- Identify Item / Repair: MAW only adds permission at s×m > difficulty, which the Standard check already grants.
  Disarm Traps: MAW's party-best s×m (GM ×4) vs Standard GM = always differs only above Lock 20, the table's maximum.
- Regeneration and Meditation per second (F:185-215): rates, estimated HP/mana at skill^1.4, GM missing-HP factor,
  reserved-pool sqrt, legendary 20, item 0.2 %/s (specials 37/44/50/54/66, artifacts 509/520/1337/1331/1335/2027 HP;
  513/1334/1331/2024/2032-2034 SP), Regeneration aura (Base 5) and potion (GM, skill power/2), Meditation aura (Base 10,
  Scaling 2), no aura for classes 10/11/34-37/56-58, ×2 after 20 s without loss (separate HP and SP), ×4 without
  yellow/red alert, Insane stops SP only, Dead/Stoned/Eradicated stop both. Standard's tick regeneration and Meditation
  values are unchanged from HEAD.
- Weapon and armour skill rows (S:45-153, IT:2820-2995, 3150-3320): attack per point (Spear 2-8, Unarmed 2/2/3/3),
  damage +2 %/point (Bow, Blaster 4 %), Bow +1 flat per point and GM refund, Staff GM half-Unarmed armsmaster,
  armsmaster halved with an off-hand weapon, per-skill damage floor, Staff/Sword/Spear AC from weapon attack × (s+10),
  staff party resistance, body armour 3-6 % AC and Leather/Chain/Plate resistance rows, Shield 4-10 %, Dodging flat
  4/5/6/6 without armour or Master+ in leather, Armsmaster damage 0/1/1/1.5/2, speed 0/0/1/1, attack 1 (not staves),
  recovery rows per weapon, armour impairment rows, Bodybuilding 0.5-2 %/point and HPFactor × s × m (GM 5).
- Perception: trap damage × min((11−2m)/10, 1) by the victim's own mastery.
- Class Skillz.txt: every cell of skill rows 0-38 and 50-53 for all 65 columns equals our patched `class_skills.txt`
  (script check; S read as G). Race Skillz.txt: all 28 non-default cells match `content/race_skills.yml`; Extra
  Skillz.txt is header-only.
- Trainer relocation (zzMAW_MoveTrainers.lua): all 43 relocations equal `data/npc_extra_houses.yml`; cleared for
  Standard (`GameDataLoader.cpp:3921`).
- Cover at Training halls, Mana Shield and Enlightenment at Magic shops (S:2180, 2431, 2446; Skills.lua:750-764).
- Training: 2 days, hall caps round(base^1.5/20)×10 (Madness /10), min 10, unlimited stays unlimited; Insanity price
  multiplier estimateSkill(level)+4 (S:1616-1675).
- NPC follower skill bonuses take the strongest (NPCFollowersSkills.lua:40-48); other follower bonuses still add, as in
  MAW. Mercenary skill points and class kinds match.
- Learning grants no experience; Ascension name; Learning followers add to Ascension in both.
- Standard: `SkillRules` defaults reproduce HEAD's regeneration, Meditation, raise cost (level+1), teacher thresholds
  and prices, training price; display-name overrides and extra NPC houses reset for Standard.
