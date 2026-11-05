#pragma once

#include "game/rules/CombatRules.h"
#include "game/rules/maw/MawCombatFormulas.h"

#include <random>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class MawRules;
struct RulesetOptions;
struct MawClassSpell;
struct GameplayRuntimeActorState;

// MAW's combat (devdocs/maw/COMBAT_SPEC.md §5, §7). Monster attacks: every attack rolls against the target's Speed
// and a Grandmaster's Dodging instead of armour; the hit is the model damage of the attacker's family with a ±25 %
// spread, mitigated hyperbolically against the attacker's level. Hits on monsters are divided by 2^(resistance / 100).
// Other hits (traps, chest traps, event missiles, and monsters the ruleset did not resolve) take MAW's trap damage indoors
// and for anything but physical and water hits outdoors; the rest keep the Standard mitigation (DM:1623-1652).
class MawCombatRules : public CombatRules
{
public:
    explicit MawCombatRules(MawRules &rules);

    bool monsterAttackLands(const MonsterAttackOnCharacter &attack) const override;
    bool characterEvades(const MonsterAttackOnCharacter &attack) const override;
    void resolveCharacterAttack(CharacterAttackResult &attack, const CharacterAttackOnMonster &context) const override;
    std::optional<int> characterAttackRecoveryTicks(
        const Character &character,
        CharacterAttackMode mode,
        const ItemTable &itemTable,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable) const override;
    bool characterMissileHits(const CharacterMissileOnMonster &missile) const override;
    // With the homing preference on, party missiles re-aim at their target as they fly.
    float partyMissileHomingTurnRate() const override;
    // The Bow preference (MAW's disableBow).
    bool bowDisabled() const override;
    // With the homing preference on, a monster missile keeps re-aiming at the party while the party moves across its
    // flight slower than 300° a second (COMBAT.md §2.10, DEVIATIONS.md #181).
    // None for Meteor Shower, Sparks, Starburst, Poison Spray, Ice Blast and Shrapmetal (S:639-743).
    float monsterMissileHomingLockRate(uint32_t spellId) const override;
    // Traps and hazards hit as hard as a monster of the party's banked level (Damage.lua stage 4), less with
    // Perception and legendaries 18 and 22; outdoor falls and drowning keep their own numbers. Dimension affix 2
    // doubles any of them now and then.
    int environmentDamage(
        const Party &party,
        size_t memberIndex,
        int damage,
        CombatDamageType type,
        bool indoor) const override;
    int rollSpellDamage(const CharacterSpellCast &cast, bool *pCritical = nullptr) const override;
    // Mass Distortion: 15 % + 0.5 % per point of the target's hit points, less on harder difficulties and bosses, more
    // on monsters above level 250 (SP:1714-1718, 1819-1850).
    std::optional<int> spellDamageOnTarget(const CharacterSpellCast &cast, const SpellTargetState &target) const override;
    bool weaponKindMultiplierApplies() const override;
    std::optional<int> worldSpellDamage(const CharacterSpellCast &cast) const override;
    bool usesPartyHitEffects() const override;
    bool callerHalvesWeakMissile(CharacterAttackMode mode) const override;
    bool monsterShieldHalvesPartyMissile(uint32_t spellId) const override;
    bool lifedrainHealsCasterThird() const override;
    float killRecoveryScale(const Character &killer) const override;
    MonsterMissileRules monsterMissileRules(const std::string &missileToken) const override;
    int reflectedDamage(const Party &party, size_t memberIndex, int damage, CombatDamageType type) const override;
    // Chain Lightning leaps on with one mastery less until Novice: Novice hits once, Grandmaster four times (DM:399-428).
    std::optional<SkillMastery> spellChainMastery(int spellId, SkillMastery mastery) const override;
    std::optional<size_t> monsterAttackTarget(const Party &party, const ActorRulesetFacts &attacker) const override;
    // Members with Cover switched on and the mastery the attack needs each roll their chance; of those who succeed,
    // the one with the most HP takes the hit, and may store a Retaliation stack (COMBAT_SPEC.md §7.3).
    std::optional<CoverOutcome> coverMonsterAttack(Party &party, const MonsterAttackCover &attack) const override;
    // Mana Shield, when switched on, takes its share of the hit from the member's spell points; a Seraphim's Divine
    // Protection turns a killing blow into a heal of a quarter of their HP and leaves them 1 HP, once every five
    // minutes (§7.6).
    int absorbCharacterDamage(Party &party, size_t memberIndex, int damage) const override;
    // Retaliation stacks lapse 10 seconds after the cover that stored them.
    // Also MAW's real-time poison (IT:1495-1569): every second a poisoned member loses ceil(full HP x 1, 0.5 or
    // 0.25 %) by the poison's strength, x bolster / 100 (x2 in Road to Insanity and Beyond Madness, /2 alone), never
    // below 1 HP, until the poison wears off after 20-50 seconds. Road to Insanity and Beyond Madness end Invisibility
    // while an enemy is in melee range and, with the preference on, dismiss a member left below -10 x full HP
    // (SP:3849-3857, DM:1923-1932).
    void updateCombat(Party &party, IGameplayWorldRuntime &world, float deltaSeconds) const override;
    // A poisoning sets the poison's time to 25 seconds, or adds 5 up to 50.
    void characterConditionApplied(Party &party, size_t memberIndex, CharacterCondition condition) const override;
    void characterDamaged(Party &party, size_t memberIndex) const override;
    // Thorn and Reflecting bosses return the hit; leech heals the attacker (COMBAT_SPEC.md §8.1); the Seraphim's
    // Body heals the most wounded member, a Shaman's Mind and Body return SP and HP, a Death Knight's hits refill
    // their spell points (§8.2, CLASSES_SPELLS_SPEC.md §5).
    void applyPartyHitEffects(Party &party, const PartyHitOnMonster &hit) const override;
    // Protection from Magic also keeps members conscious, at no charge (SP:674-685).
    bool blocksMonsterCondition(const Party &party, CharacterCondition condition) const override;
    // A dimension map's "ignore status resistance" (zzMaw_Mapping.lua:1-6).
    bool piercesConditionSave(const Party &party) const override;
    // Legendary 13: no special attack of a monster takes hold (zzMaw_Legendaries.lua:35-42).
    bool immuneToMonsterSpecialAttacks(const Character &member) const override;
    // With the preference off (the default), hits on monsters not hostile to the party do nothing (DM:1197-1202).
    bool harmsFriendlyActors() const override;
    // A Swapper boss swaps places with every other living, visible, hostile monster in reach in turn and takes no
    // damage, while there is one (Damage.lua:933-941).
    bool deflectsPartyHit(IGameplayWorldRuntime &world, size_t actorIndex) const override;
    // Mist Form cuts physical damage taken by 75 % (DM:1729-1731).
    float mistFormPhysicalShare() const override;
    // The Doom modes and Austerity: 370 units a movement phase (MON:3663-3679).
    std::optional<float> turnBasedWalkLimit() const override;
    // The party's Blades are physical (DM:519-522).
    CombatDamageType partySpellDamageType(uint32_t spellId, CombatDamageType tableType) const override;
    void applyMonsterHitEffects(
        Party &party,
        IGameplayWorldRuntime *pWorld,
        size_t memberIndex,
        const ActorRulesetFacts &attacker,
        uint32_t attackerActorId,
        int appliedDamage,
        CombatDamageType type) const override;
    // "Name hits Target for N points!", "shoots" for missiles, "inflicts N points killing Target!", an area spell's
    // "Spell hits for a total of N points!", with the spell named as the attacker, "(CRIT!)" and MAW's short numbers
    // (Damage.lua:1365-1430).
    std::optional<std::string> partyHitStatusText(const PartyHitStatus &status) const override;

private:
    // A spell an artifact casts on the monster its wielder struck, cast on the next update.
    struct ArtifactCast
    {
        size_t memberIndex = 0;
        uint32_t spellId = 0;
        uint32_t skillLevel = 0;
        SkillMastery mastery = SkillMastery::None;
        size_t actorIndex = 0;
    };

    void summonBossFamilyMember(IGameplayWorldRuntime &world, const GameplayRuntimeActorState &summoner,
        std::mt19937 &rng) const;
    // MAW's artifact effects on the regeneration tick (every 5 game minutes) and its 2-second buff refresh.
    void updateArtifacts(Party &party, IGameplayWorldRuntime &world) const;
    // The full HP the Nightmare death thresholds count in: the member's, or Legendary 30's SP x Mana Shield efficiency.
    int deathThreshold(const Character &member) const;
    int legendaryProtection(Party &party, size_t memberIndex, int damage) const;
    // Legendary 18 (x0.9) and 22 (x0.97 per monster within 512, at least x0.5) on a hit the character takes
    // (zzMaw-Stats.lua:724-768).
    double legendaryDefense(const Character &character) const;
    int divineProtection(Party &party, size_t memberIndex, int damage) const;
    // What a hit is worth to leech: the share of a B-tier monster of the family's HP it took, as a share of the
    // attacker's full HP (overkill left out).
    double leechBarShare(const Party &party, const PartyHitOnMonster &hit) const;
    // The recovery the caster would have after this spell, in ticks.
    std::optional<int> spellRecoveryTicks(const Party &party, const Character &caster, uint32_t spellId) const;
    // MAW's trap damage (DM:1623-1652): the model damage at the party's total level, cut by Perception (x (11 - 2 m)
    // / 10, at most 1), then the member's armour and resistances at their own level.
    int trapDamage(
        const Character &member,
        const ItemTable *pItemTable,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        CombatDamageType type,
        int partyCount) const;
    // A Death Knight's or Assassin's damage spell: a share of a weapon blow.
    int classSpellDamage(const CharacterSpellCast &cast, const MawClassSpell &spell, bool &critical) const;
    void applyLeech(Party &party, const PartyHitOnMonster &hit) const;
    void applyClassHitEffects(Party &party, const PartyHitOnMonster &hit) const;
    void applyAssassinHit(Party &party, const PartyHitOnMonster &hit, bool arrow) const;
    // A kill by an Assassin, blow or class spell: (1 + Subtlety mastery) x 5 energy and a combo point.
    void rewardAssassinKill(Character &member) const;
    // Spends the attacker's Retaliation stacks on a melee hit: damage, a chance to paralyse, faster recovery.
    void applyRetaliation(CharacterAttackResult &attack, const CharacterAttackOnMonster &context) const;

    MawRules &m_rules;
    // By party member; members who leave are dropped on the next update.
    // The world's clock (game minutes) as of the last update, for Divine Protection, and what the rules tell the player
    // there next.
    mutable float m_gameMinutes = 0;
    mutable std::vector<std::string> m_statusMessages;
    mutable float m_poisonSeconds = 0;
    mutable std::mt19937 m_legendaryRng{std::random_device{}()};
    mutable std::vector<ArtifactCast> m_artifactCasts;
    // The 5-minute regeneration tick last run, and the artifact buffs' last refresh (game minutes).
    mutable float m_regenerationTickMinutes = -1;
    mutable float m_artifactBuffMinutes = -1;
};

// A monster resistance as MAW reads it: modulo 1000, at most 200, plus dimension affix 12's bonus (at most 999).
int mawCappedMonsterResistance(int resistance, int affixBonus = 0);

// Dimension affix 12's resistance bonus for this monster: unnamed monsters only, as in MAW, where the first
// AfterLoadMap handler resets bosses, uniques and risen monsters to their base resistances (zzMaw-Monsters.lua:107-126).
int mawMonsterResistanceBonus(const MawRules &rules, const ActorRulesetFacts &facts);

// The percent of a hit of this type a monster of `attackerLevel` lands on the character after armour, resistances
// and class cuts (calcMawDamage on 10000, the flat class cut left out).
double mawDamageTakenPercent(
    const MawRules &rules,
    const Character &character,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    CombatDamageType type,
    int attackerLevel);
// The same for several types at once, from one character sheet.
std::vector<double> mawDamageTakenPercents(
    const MawRules &rules,
    const Character &character,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    const std::vector<CombatDamageType> &types,
    int attackerLevel);

// A character's damage per second and how much damage it takes to fell them, as MAW's stats screen and item popups
// compare them (calcPowerVitality, zzMaw-Stats.lua:1189-1340), against the party's banked level.
struct MawPowerReport
{
    // Melee and bow blows with their enchantment, Fire Aura and artifact damage, and the attack or quick spell (0 when
    // it is not one of MAW's damage spells).
    double melee = 0;
    double ranged = 0;
    double spell = 0;
    // Maximum HP (with Mana Shield's mana and Grandmaster Dodging) over the share of an average hit that gets through.
    double vitality = 0;
};

// A Seraph's Body heal on a melee blow: round(s^1.3 x m x 2 x the weapon's speed multiplier x (1 + Personality /
// 1000)), from the trained level and the full Speed and Personality (DM:106-150); 0 without Body or item tables.
int mawSeraphBodyHeal(const MawRules &rules, const Character &seraph, const Party &party);
// A Shaman's melee blow returns s^1.25 SP from Mind and max(round(FullHP^0.5 s^1.5 / 70 (0.5 + m/2)), s) HP from Body,
// at the trained levels (DM:673-693).
double mawShamanMindSpellPoints(const Character &shaman);
int mawShamanBodyHeal(const Character &shaman);

// A Mace's (15 %) or Staff's (10 %) chance to paralyse a monster of this level with a blow from Master up, 0 below
// or with another weapon: skill / reference skill x share x speed multiplier / min(1 + L / 150, 3) (DM:599-610).
double mawWeaponStunChance(
    MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    int targetLevel,
    int partyCount,
    double speedMultiplier);

// Retaliation's Melee Power and Vitality coefficients (the rounded fourth roots), whose product times the skill is
// its damage.
std::pair<double, double> mawRetaliationCoefficients(
    MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    int partyCount);

MawPowerReport mawPowerReport(
    MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    int partyCount);

// The dice and flat damage per point a MAW damage spell rolls for the caster (Ascension, Empower Magic, an
// Elementalist's stacks), or nothing for a spell MAW leaves to the engine.
std::optional<MawSpellDice> mawCasterSpellDice(const MawRules &rules, const Character &caster, const SpellEntry &spell);

// A party member's weapon delay under MAW (COMBAT_SPEC §4.1-4.2) from the weapons held, the weapon, Armsmaster and
// Unarmed skills, Speed, the class terms (an Assassin's Subtlety stacks too), swiftness, Haste and armour impairment.
MawAttackDelay mawCharacterAttackDelay(
    const MawRules &rules,
    const Character &character,
    const ItemTable &itemTable,
    CharacterAttackMode mode,
    double speed,
    std::optional<double> hasteSkill = std::nullopt);

// The percent an offhand shield and the body armour slow attacks and casting by, at the character's masteries
// (weaponImpair).
double mawCharacterArmorImpairment(const Character &character, const ItemTable &itemTable);
// What the held Fire Aura adds to every blow of this weapon in `wearer`'s hands (tooltipFireAura), or 0 without it.
int mawFireAuraOnWeapon(
    const MawRules &rules, const Character &wearer, const ItemDefinition &weapon, const InventoryItem &item);
// A Grandmaster spear blow's stack, in percent of physical damage its target takes from then on, until it dies:
// (2 + 0.02 s) x the melee speed multiplier, x 1.5 with a halberd (DM:546-570, SkillTooltip.lua:187-197).
double mawSpearStackPercent(const MawRules &rules, const Character &attacker, const ItemTable &itemTable);
// The maps made for flying, where attacking never ends Fly (flyAllowedMaps, zzMaw-Spells.lua:1018).
bool mawFlightMap(const std::string &mapFileName);
// Whether a blow ends the party's Fly: from Hard up and in Austerity, outside the flight maps (DM:317-329).
bool mawAttackingEndsFly(const RulesetOptions &options, const std::string &mapFileName);
// How far a dragon's bite throws a monster: MAW's push of 800 × mult (mult = fang / level^0.75) fading over 60 × the root
// of mult frames covers 400 × mult^1.5 units at 60 frames a second; at most 2048 here (DM:599-610, zzClasses:471-484).
double mawDragonPushDistance(int fang, int monsterLevel);
}
