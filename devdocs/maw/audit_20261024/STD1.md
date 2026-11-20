# STD1: Standard (MMMerge) regressions in combat, spells, experience, monster stats, loot and values

**Scope.** I compared the Standard implementations in `game/rules/` against the HEAD code they replaced: CombatRules,
ExperienceRules, MonsterRules, ItemRules, SpellRules, SkillRules, ClassRules, GameRules, RandomStreams and
DamagePipeline. I also checked every modified call site in the task list, the spell numbers that moved into `spells.txt`,
and the other seam call sites in my area: GameplayActionController, ChestRuntime, HouseServiceRuntime,
HouseInteraction, EventRuntime (DamagePlayer, event experience), TurnBasedCombatRuntime, ItemRuntime and the monster
inspect overlay.

Two helper passes compared `IndoorWorldRuntime.cpp` and `OutdoorWorldRuntime.cpp` hunk by hunk against HEAD. I
spot-checked their findings.

**Baseline.** `git show HEAD:<file>` (HEAD 7fdb25667). Nothing was built and no tests were run.

**Result.** I found no P1 or P2 regression. A Standard game resolves combat, spells, experience, monster stats, loot
and item values the same way as at HEAD. The RNG draw counts and orders are unchanged. Every new seam's Standard
default either returns nullopt, false, 0 or the identity, or wraps the HEAD helper with the same arguments and the
same seeded generator. The findings below are P3 items and notes.

---

### STD1-1: Monster HP is no longer clamped to 16 bits indoors, so MM9 monsters above 32767 HP change
Severity: P3 (MM9 content only; MM6-MM8 HP tops out at about 5000 after bolster)
Confidence: confirmed (both sides read)
MAW: n/a (Standard regression)
OpenYAMM:
- `game/maps/MapDeltaData.h:56`: `MapDeltaActor::hp` went from `int16_t` to `int32_t`.
- HEAD clamped indoor actor HP when an actor was spawned or refreshed:
  - `IndoorWorldRuntime.cpp` HEAD:4879 used `static_cast<int16_t>(std::clamp(bolster->maxHp, 1, 30000))`.
  - HEAD:12985, 13077, 15924 and 18104 used `int16_t(std::clamp(pStats->hitPoints, 0, 32767))`.
  - These clamps are gone, as is the clamp in the AI HP update.
- The MM9 Dragon King (`worlds/mm9/data_tables/monster_data.txt`, id 9212, 39000 HP) spawned indoors with
  30000/32767 HP at HEAD while showing a maximum of 39000. He now gets all 39000.
- Outdoor actors were not clamped this way at HEAD.
Not covered by: no related row (DEVIATIONS/GAPS have no row on the HP width).
Suggested fix: if the change is intended (it makes indoors consistent with outdoors), record it as an approved MM9/Standard
change. Otherwise restore the clamp at the spawn and refresh points.

### STD1-2: A stray 16-bit cast on monster HP is left in the indoor area-hit branch
Severity: P3 (harmless under Standard; latent under MAW, where HP can exceed 32767)
Confidence: confirmed
MAW: n/a
OpenYAMM:
- `game/indoor/IndoorWorldRuntime.cpp:7388-7390` (the area-hit branch for projectiles not fired by the party) still does
  `targetActor.hp = static_cast<int16_t>(std::max(0, int(targetActor.hp) - appliedDamage))`.
- The direct-impact twin of this line was already widened to 32 bits.
- An actor with more than 32767 HP wraps to a negative value, which can kill it at once.
Not covered by: no related row.
Suggested fix: `targetActor.hp = std::max(0, targetActor.hp - appliedDamage);`.

### STD1-3: A party missile hit that "did not land" now reports 0 damage
Severity: P3 (no current Standard content reaches it)
Confidence: confirmed code; reachability is plausible only through a Lua damage hook
MAW: n/a
OpenYAMM:
- Where: `IndoorWorldRuntime.cpp:7111-7121` and `:7344-7357`; `OutdoorWorldRuntime.cpp:14486` and `:14599`.
- What changed: `appliedDamage` is set to 0 when `applyPartyAttackMeleeDamage` / `applyPartyAttackToMapActor` returns
  false. HEAD ignored the return value.
- That 0 now drives:
  - the status line ("hits for N");
  - Hit/Miss speech;
  - the vampiric arrow heal (`GameplayCombatController.cpp` ~1690);
  - the combat log and area-spell totals.
- When Standard can reach it: under Standard the call returns false only for damage ≤ 0 or actors that can't be hit,
  and the earlier filters already exclude those. The one remaining case is a MonsterDamage Lua hook that overrides
  damage to 0, where HEAD still printed the pre-hook number and leeched. No current hook does this
  (`hive_mmmerge.lua:72` sets 2-40).
Not covered by: no related row.
Suggested fix: keep it (it reads as a fix). For strict parity, zero the damage only on the MAW friendly-fire and deflect
refusals.

### STD1-4: The monster inspect effects box can now grow the panel and is drawn as multi-line text
Severity: P3 (cosmetic)
Confidence: plausible (needs a visual check)
MAW: n/a
OpenYAMM:
- `game/ui/GameplayPartyOverlayRenderer.cpp:11030-11036, 11477`.
- At HEAD the effects were a single joined string drawn with `renderTextForLayout`, and the panel height counted only
  the attack, damage and spell lines.
- Now, in Standard, `effectRows = {joined or "None"}` is drawn with `renderMultilineTextForLayout`, and the root grows
  when the effects wrap to more than 4 lines.
- With many effects on one monster, the Standard panel may be taller or wrap differently than at HEAD.
Not covered by: no related row.
Suggested fix: none needed if the growth is wanted; otherwise keep HEAD's single-line rendering when `rulesNumbers` is
empty.

### STD1-note: the spell number migration changed 18 spells, not the 19 the handoff states
Severity: P3 (documentation)
Confidence: confirmed (scripted comparison)
OpenYAMM:
- How I compared: I parsed HEAD's `BackendSpellRule` table (`git show HEAD:game/party/PartySpellSystem.cpp`) and
  evaluated HEAD's effective numbers for all 111 rules × 4 masteries. Mana is the explicit rule value or
  max(table, slot default); recovery is the explicit rule value or the table's; damage is the explicit rule value or
  the table's, with the linear/dice flag; the projectile count includes Sparks 3/5/7/9 and Poison Spray 1/3/5/7.
  I compared these with `spellNumbersAtMastery` over the new `spells.txt`, including the per-mastery percent and the
  DiceMin rule.
- Result: exactly 18 spells differ, and every difference moves to the HEAD `spells.txt` (MMMerge) value, which is the
  approved choice:
  - Fire Spike, Ice Bolt, Blades, Dragon Breath: base 1 → 0.
  - Death Blossom: 20 + 2/pt → 20 + 1/pt.
  - Flying Fist: 30 + d5 → 20 + d10.
  - Shrapmetal: 1 + 6/pt → 6/pt.
  - Telepathy recovery: 90 → 110/100/90/80.
  - Travelers' Boon recovery: 100 → 110.
  - Blind recovery: 120 → 110.
  - Darkfire Bolt recovery: 90 → 120.
  - Lifedrain recovery: 80 → 90 (Expert to Grandmaster).
  - Levitate recovery: 110 → 90/90/80/80.
  - Vampire Charm: mana 20 → 15 and recovery 110 → 100.
  - Fear recovery: 100 → 120.
  - Flame Blast recovery: 100 → 90 at Master and Grandmaster.
  - Flight recovery: 120 → 250.
  - Wing Buffet recovery: 110 → 120.
- Unchanged: required mastery, target and effect kinds, buff ids and projectile counts are identical for all 111
  spells. The slot-default mana floor never mattered because no table mana is below it. Lifedrain's 3/5/7 and Flame
  Blast's 10 + d10, which existed only in code, were carried into the table (3,3 with 100/100/167/233 %; 10,10)
  and give HEAD's numbers.
- Side effect on monsters: monster spell damage reads `damageBase` and `damageDiceSides` too, but no monster casts
  Lifedrain or Flame Blast. Monster spells ignore the new DiceMin and percent columns.
Not covered by: HANDOFF.md:204 says "19 spells".
Suggested fix: correct the count in HANDOFF, or name the 19th if there is one.

---

## Approved Standard changes found (not findings)
- **The 19 (18 by my count) spell-number choices.** See STD1-note. Approved by HANDOFF.md:204.
- **Quick-cast heal and cure target rule for both rulesets.** GAPS A7.2 records it as "Replaced 2026-10-24 at the
  user's request ... (a Standard change)". This approval is clear.
  - Implemented in `PartySpellSystem::quickCastCharacterTarget`.
  - Heal goes to the lowest-share member at or below a third of their maximum, else to the member who gains the most
    HP.
  - Cures go to a member with the condition; with nobody to cure the quick cast now fails, where HEAD targeted the
    most wounded member.
  - Revivals go to the dead; HEAD never targeted the dead.
  - Buff spells keep HEAD's "most wounded" rule.
  - It matches the A7.2 text.
- **Carnage arrows explode in Standard.** GAPS §11 D.5 says "Carnage arrows explode in Standard too, as in MM7".
  - `ItemEnchantRuntime.cpp` Carnage → `ExplosiveArrows`.
  - `GameMechanics.cpp:2981` makes the arrow fire damage.
  - `GameplayActionController.cpp:1317-1330` makes it never miss and gives it the Fireball impact radius and object.
  - This matches OpenEnroth's MM7 behaviour (fire element, no hit roll, explodes; `SpriteObject.cpp:786-818`,
    `Actor.cpp:3086-3094`).
- **Monster table parsing fixes.**
  - Spreadsheet numbers: `parseTableInteger`.
  - MM6/MM7 letter preferences: `parseAttackPreferences`. The letters match OpenEnroth's map, f/o female, x male.
  - Approved in HANDOFF.md:204.
- **Other approved changes in the brief, outside my code paths.** House map column fix, special enchantments ending at
  the first blank row, the apple food fix and Dragon Hatchling (GAPS N8.5, "The user approved changing Standard").
- **Other "Standard too" rows, outside my slice.**
  - GAPS N8.1 and N8.4 (6d18 lava wall, d26 sarcophagus), approved through §11 D.19.
  - D.8 changes only the Settings row text.
  - I found no unclear approvals.

## Checked and matching
- **CombatRules Standard stages and helpers.**
  - `monsterAttackLands` is the same call with the same RNG seed.
  - `characterEvades`:
    - Only melee and the party-projectile impact events reach it, so `singlePhysicalMissile` matches HEAD's
      `canEvadeProjectile`.
    - The mastery check and the level-plus-bonus are the same, and the seed is `^0x9e3779b9u`.
  - Damage-to-character stages: missile-shield → physical-taken → resistance-and-armor matches HEAD's order and
    conditions. Traps (`monsterAttack=false`) skip the first two, like HEAD's direct `resolveCharacterIncomingDamage`.
  - Damage-to-monster "resistance" stage: same weapon and non-weapon calls, Hour of Power and RNG.
  - Melee `resolveMeleeAppliedDamage`: same additional elemental damage; `rulesElementalDamage` is zero and
    `rulesWeaponElements` false in Standard.
  - `characterMissileHits` gives the same result as HEAD's roll.
  - `rollSpellDamage`:
    - Equivalent to HEAD's dice and linear forms, including `max(1, sides)`.
    - A skill of 0 returns the base, as at HEAD.
  - Logging: `runRecorded` only adds trace and combat-log output.
- **CombatRules hooks that are no-ops in Standard.** None of these draw from a shared RNG.
  - Cover, Fixator target, absorb, characterDamaged, condition hooks, special-attack immunity and pierce, ManaDrain and
    Aging immunity flags (set only by MAW), partyHitStatusText, applyPartyHitEffects and applyMonsterHitEffects.
  - Homing (0), chain, friendly fire (true), deflect (false), environmentDamage (identity), turnBasedWalkLimit (none).
  - Mist Form share is 0, which keeps `physicalDamageImmune=true`.
  - The DamagePlayer type argument: every Lua call passes a defined `const.Damage` name, so `luaL_checkinteger(2)`
    cannot throw.
- **PartySpellSystem.**
  - Mana, recovery, required mastery and the projectile count of multi-projectile spells are equivalent, apart from
    the approved spell numbers.
  - Mastery is never None at cast time.
  - The Standard SpellRules hooks change nothing:
    - aura, scroll, refusal and teleport-block hooks;
    - partyBuffSeconds, healAmount (only Heal uses `standardHealAmount`, which is unchanged), shareLife and PowerCure;
    - splash, afterCast and afterHeal.
  - `actorInspectState` is now always queried, but it is a pure query.
  - The damage roll is only moved before the call; the draw count is the same.
- **Experience.**
  - The `experienceForNextLevel` formula is identical, and so are training, the character sheet and the inspect
    supplement.
  - `trainingPrice` no longer returns 0 for a member short of experience. Every caller checks the shortfall first
    (`HouseInteraction.cpp`), so prices and messages are unchanged.
  - Kill experience: `gameplayBolsterExperienceReward` plus `grantSharedExperience` is the same indoors and outdoors,
    as the helper passes confirmed.
  - `learningGrantsExperience` is true, and `eventExperience` is the identity.
  - Regeneration and Meditation give the same per-tick amounts, since `SkillMastery` values are 1-4.
- **Monster stats.**
  - `resolveMonster` is `resolveGameplayMonsterBolster`, and `GameplayBolsterRuntime.cpp` is unchanged, so
    `rulesetFacts` stays empty and every "facts level > 0 ? : table level" fallback gives HEAD's value.
  - Inspect: the reveal uses the same best Identify Monster member, and the resistance text is the same "Imm"
    threshold.
  - Bounty reward is level × 100.
  - Bounty spawn: `spawnBountyTarget` returns nothing, so the HEAD spawn path is used. The spawn point is now chosen
    earlier from the same seed; `chooseBountyHuntSpawnPoint` is a const pure function.
  - Attack preference constants are identical.
- **Loot generation.**
  - `rollsRareItem`: the same short-circuit and the same draw.
  - `rollEnchantments`: the same branches and draws as HEAD's inline code, including the special-only early-out.
  - `rollPlainItem` does nothing; the `boss` filter and `filtersLoot` are off; corpse loot has no seed (the same
    static RNG).
  - `keepsDeathDrop` and `placedItemId` draw nothing.
  - Chest gold falls back to `generateGoldAmount` with the same RNG.
  - Chest potion seed: the potion RNG is the same, only constructed earlier.
  - Shops: stock generation now passes the party, but shop requests cannot reach the rare path, so nothing changes.
    `adjustShopStock` does nothing.
- **Values.**
  - `itemValue` and `shopBuyValue` reduce to `calculateItemValue(..., 1 or 0)`.
  - The merchant member is the same (`rulesMerchantMember` returns null).
  - `shopServiceMultiplier` is the identity; `displayName` and `enchantDescription` wrap the HEAD functions.
- **Equipment and the character sheet.**
  - `baseStats`, `combatRows`, `baseMaxHealth` and `baseMaxSpellPoints` return nothing, so the HEAD formulas apply.
  - `wield()` reproduces `isTwoHandedWeapon` and the Dagger Expert / Sword Master off-hand rule.
  - `applyEquippedEnchantEffects` wraps the HEAD function; Carnage is the approved change.
- **Crowd control.** `crowdControlSeconds` returns nothing, so every `tryApplySharedSpellEffect` branch takes the HEAD
  path.
- **Binding and defaults.**
  - `Party::rules()` and `gameRulesFor(nullptr)` return Standard, and `boundGameRules()` defaults to Standard.
  - `GameSession` resets the binding to null and rebinds it on `setRuleset`.
  - Editor and tests with nothing bound get Standard.
- **RandomStreams** is used only under `game/rules/maw`.
