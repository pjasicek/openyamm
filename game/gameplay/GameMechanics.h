#pragma once

#include "game/gameplay/CharacterAttackTuning.h"
#include "game/party/Party.h"
#include "game/rules/ExperienceRules.h"
#include "game/tables/MonsterShields.h"

#include <array>
#include <optional>
#include <random>
#include <string>

namespace OpenYAMM::Game
{
class ItemTable;
class ClassMultiplierTable;
class SpellTable;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
struct EventRuntimeState;
struct MapStatsEntry;
struct ItemDefinition;
struct CharacterDollTypeEntry;

struct CharacterSheetValue
{
    int base = 0;
    int actual = 0;
    bool infinite = false;
};

struct CharacterResourceSummary
{
    int current = 0;
    int maximum = 0;
    int baseMaximum = 0;
};

struct CharacterCombatSummary
{
    int attack = 0;
    std::optional<int> shoot;
    std::string meleeDamageText;
    std::string rangedDamageText;
};

enum class CharacterAttackMode
{
    None,
    Melee,
    Bow,
    Wand,
    Blaster,
    DragonBreath,
};

enum class CombatDamageType
{
    Physical,
    Fire,
    Air,
    Water,
    Earth,
    Spirit,
    Mind,
    Body,
    Light,
    Dark,
    Energy,
    Irresistible,
};

constexpr size_t CombatDamageTypeCount = size_t(CombatDamageType::Irresistible) + 1;

struct ElementalDamageBonuses
{
    int fire = 0;
    int air = 0;
    int water = 0;
    int body = 0;
    int light = 0;
    int dark = 0;

    int total() const
    {
        return fire + air + water + body + light + dark;
    }
};

struct MonsterDamageResistances
{
    int fire = 0;
    int air = 0;
    int water = 0;
    int earth = 0;
    int spirit = 0;
    int mind = 0;
    int body = 0;
    int light = 0;
    int dark = 0;
    int physical = 0;
};

struct CharacterAttackProfile
{
    bool canMelee = false;
    bool canShoot = false;
    bool hasBow = false;
    bool hasWand = false;
    bool hasBlaster = false;
    bool hasDragonBreath = false;
    int meleeAttackBonus = 0;
    int meleeMinDamage = 0;
    int meleeMaxDamage = 0;
    uint32_t meleeSkillLevel = 0;
    uint32_t meleeSkillMastery = 0;
    std::optional<int> rangedAttackBonus;
    int rangedMinDamage = 0;
    int rangedMaxDamage = 0;
    uint32_t rangedSkillLevel = 0;
    uint32_t rangedSkillMastery = 0;
    uint8_t rangedProjectileCount = 1;
    // Non-zero fans the projectiles evenly across this horizontal arc instead of firing them side by side.
    float rangedSpreadArcRadians = 0.0f;
    int wandSpellId = 0;
    int rangedSpellId = 0;
    float meleeRecoverySeconds = 1.0f;
    float rangedRecoverySeconds = 1.0f;
    // What the attacks are to an energy shield: EnergyBlade weapons and Energy Guns items are Kreegan energy.
    ShieldAttackTier meleeShieldTier = ShieldAttackTier::Physical;
    ShieldAttackTier rangedShieldTier = ShieldAttackTier::Physical;
    // Energy Blades Grandmaster with an energy blade: melee hits may overload a raised shield
    // (MonsterShieldTable::overloadRules).
    bool meleeShieldOverload = false;
    // A world enchantment's chance per melee hit to overload the target's shield (Hesper's Overloading), 0-1.
    float meleeShieldOverloadChance = 0.0f;
    // What Energy Blades and Energy Guns masteries and the weapon's ShieldDamage<percent> flag add to its shield hits.
    ShieldHitModifiers meleeShieldModifiers;
    ShieldHitModifiers rangedShieldModifiers;
    // Energy Guns Grandmaster with an energy gun (not a scatter gun): its shots home onto their target.
    bool rangedHoming = false;
};

struct CharacterAttackResult
{
    CharacterAttackMode mode = CharacterAttackMode::None;
    bool canAttack = false;
    bool hit = false;
    bool resolvesOnImpact = false;
    int damage = 0;
    // Range of `damage`; fanned projectiles each roll their own damage from it.
    int minimumDamage = 0;
    int maximumDamage = 0;
    int attackBonus = 0;
    int targetArmorClass = 0;
    float targetDistance = 0.0f;
    float recoverySeconds = 0.0f;
    uint32_t skillLevel = 0;
    uint32_t skillMastery = 0;
    uint8_t projectileCount = 1;
    float projectileSpreadArcRadians = 0.0f;
    int spellId = 0;
    CombatDamageType damageType = CombatDamageType::Physical;
    ShieldAttackTier shieldTier = ShieldAttackTier::Physical;
    // A melee hit that may overload a raised shield (CharacterAttackProfile::meleeShieldOverload), or does so at this
    // chance (meleeShieldOverloadChance).
    bool shieldOverload = false;
    float shieldOverloadChance = 0.0f;
    ShieldHitModifiers shieldModifiers;
    // Its projectiles home (CharacterAttackProfile::rangedHoming).
    bool homing = false;
    bool criticalDamage = false;
    // Elemental damage the rules add to the blow, each part resisted by its own element (MAW's Shaman Fire).
    ElementalDamageBonuses rulesElementalDamage;
    // The rules' elemental damage replaces the item table's weapon enchantments (MAW's level-scaled enchantments).
    bool rulesWeaponElements = false;
    // Damage the rules add after the monster's other stages, by damage type, each resisted by its own (MAW's artifact
    // on-hit damage).
    std::array<int, CombatDamageTypeCount> rulesLateDamage = {};
    // The rules fire this arrow burning: the fire-arrow object, resisted by the weaker of physical and fire (MAW's
    // Grandmaster bow).
    bool fireArrow = false;
    // A Carnage bow's arrow: fire, it cannot miss, and it explodes like a fireball where it strikes.
    bool explosiveArrow = false;
    bool stunTarget = false;
    // Whether the weapon's item effects stunned, before the weapon skill's own roll (rules that replace it keep this).
    bool itemStunTarget = false;
    bool paralyzeTarget = false;
    // How long the paralysis lasts when the rules set it (MAW's Retaliation); otherwise the skill level in minutes.
    std::optional<float> paralyzeSeconds;
    bool fearTarget = false;
    bool enrageTarget = false;
    bool halveTargetArmorClass = false;
    std::string attackSoundHook;
    std::string damageSoundHook;
    std::string voiceHook;
};

struct CharacterSheetSummary
{
    CharacterSheetValue might = {};
    CharacterSheetValue intellect = {};
    CharacterSheetValue personality = {};
    CharacterSheetValue endurance = {};
    CharacterSheetValue accuracy = {};
    CharacterSheetValue speed = {};
    CharacterSheetValue luck = {};
    CharacterResourceSummary health = {};
    CharacterResourceSummary spellPoints = {};
    CharacterSheetValue armorClass = {};
    CharacterSheetValue level = {};
    CharacterSheetValue fireResistance = {};
    CharacterSheetValue airResistance = {};
    CharacterSheetValue waterResistance = {};
    CharacterSheetValue earthResistance = {};
    CharacterSheetValue mindResistance = {};
    CharacterSheetValue bodyResistance = {};
    std::string ageText;
    std::string experienceText;
    bool canTrainToNextLevel = false;
    std::string conditionText;
    std::string quickSpellText;
    CharacterCombatSummary combat = {};
};

struct CharacterEquipPlan
{
    EquipmentSlot targetSlot = EquipmentSlot::MainHand;
    std::optional<EquipmentSlot> displacedSlot;
    bool autoStoreDisplacedItem = false;
};

// Sections of the monster inspect popup revealed by the Identify Monster skill.
struct IdentifyMonsterReveal
{
    bool hasSkill = false;
    bool hitPointsAndArmorClass = false;
    bool attackAndDamage = false;
    bool spellsAndEffects = false;
    bool resistances = false;

    bool identified() const
    {
        return hitPointsAndArmorClass;
    }
};

// Recovery ticks (128 per second of the original real-time pace) as real-time recovery seconds.
float ticksToRecoverySeconds(int ticks);

class GameMechanics
{
public:
    static void bindClassMultiplierTable(const ClassMultiplierTable *pClassMultiplierTable);
    static uint32_t maximumTrainableLevelFromExperience(
        const Character &character,
        const ExperienceRules &experienceRules = standardExperienceRules());
    static int calculateBaseCharacterMaxHealth(
        const Character &character,
        const ClassMultiplierTable *pClassMultiplierTable = nullptr);
    static int calculateBaseCharacterMaxSpellPoints(
        const Character &character,
        const ClassMultiplierTable *pClassMultiplierTable = nullptr);
    static int calculateEffectiveCharacterMaxHealth(
        const Character &character,
        const ClassMultiplierTable *pClassMultiplierTable = nullptr);
    static int calculateEffectiveCharacterMaxSpellPoints(
        const Character &character,
        const ClassMultiplierTable *pClassMultiplierTable = nullptr);
    static void refreshCharacterBaseResources(
        Character &character,
        bool restoreCurrentToMaximum = false,
        const ClassMultiplierTable *pClassMultiplierTable = nullptr);
    static std::string buildExperienceInspectSupplement(
        const Character &character,
        const ExperienceRules &experienceRules = standardExperienceRules());
    // The bonus of a primary stat's value (MM8's table: 13 gives 0, 15 +1, 500 and over +30).
    static int primaryStatBonus(int value);
    // The lowest value with a higher bonus than `value`'s; nothing at the top of the table.
    static std::optional<int> nextPrimaryStatBonusValue(int value);
    // The share of a hit's damage resistance takes off on average, 0 to 1. `resistance` is the damage type's resistance
    // plus the Luck bonus; above 0, each of up to four rolls halves the hit with chance resistance / (resistance + 30).
    static float averageResistedDamageShare(int resistance);
    // The chance to resist a monster's curse, poison, disease or other effect, 0 to 1. `bonus` is the Luck bonus plus
    // the effect's stat bonus or resistance; the save rolls rand() % (bonus + 30) and holds on 30 or more.
    static float monsterEffectResistChance(int bonus);
    // The HP an Endurance of `endurance` adds through the character's class: its bonus counts as that many levels of
    // the class's HP per level.
    static int enduranceHealthBonus(const Character &character, int endurance);
    // The SP an Intellect or Personality ("Intellect", "Personality") of `value` adds the same way, or nothing when
    // the class's SP do not grow with that stat.
    static std::optional<int> primaryStatSpellPointBonus(
        const Character &character,
        const std::string &statName,
        int value);
    static int resolveCharacterItemSkillBonus(const Character &character, const std::string &skillName);
    static int resolveCharacterDisplayedBasePrimaryStat(
        const Character &character,
        uint32_t rawStatId,
        const ItemTable *pItemTable,
        const StandardItemEnchantTable *pStandardItemEnchantTable = nullptr,
        const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr);
    static int resolveCharacterDisplayedActualPrimaryStat(
        const Character &character,
        uint32_t rawStatId,
        const ItemTable *pItemTable,
        const StandardItemEnchantTable *pStandardItemEnchantTable = nullptr,
        const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr);
    // The training fields use `experienceRules`: the party's rules where the sheet is shown.
    static CharacterSheetSummary buildCharacterSheetSummary(
        const Character &character,
        const ItemTable *pItemTable,
        const StandardItemEnchantTable *pStandardItemEnchantTable = nullptr,
        const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr,
        CharacterAttackTuning attackTuning = {},
        const ExperienceRules &experienceRules = standardExperienceRules());
    static CharacterAttackProfile buildCharacterAttackProfile(
        const Character &character,
        const ItemTable *pItemTable,
        const SpellTable *pSpellTable,
        CharacterAttackTuning attackTuning = {});
    // What the caster's Lattice Resonator adds to its spells' hits on raised shields.
    static ShieldHitModifiers spellShieldModifiers(const Character &character);
    // The profile without the per-cent damage of Hesper's item effects (buildCharacterAttackProfile adds it).
    static CharacterAttackProfile buildBaseCharacterAttackProfile(
        const Character &character,
        const ItemTable *pItemTable,
        const SpellTable *pSpellTable,
        CharacterAttackTuning attackTuning = {});
    static CharacterAttackResult resolveCharacterAttackAgainstArmorClass(
        const Character &character,
        const ItemTable *pItemTable,
        const SpellTable *pSpellTable,
        int targetArmorClass,
        float targetDistance,
        std::mt19937 &rng,
        CharacterAttackTuning attackTuning = {});
    static SoundId resolveCharacterAttackSoundId(
        const Character &character,
        const ItemTable *pItemTable,
        CharacterAttackMode attackMode);
    static float actorTargetHeight(uint16_t actorHeight);
    // Yaw offset of fan member `projectileIndex` when `projectileCount` projectiles spread evenly across
    // `arcRadians`, centred on the aim direction.
    static float projectileFanYawOffsetRadians(uint32_t projectileCount, uint32_t projectileIndex, float arcRadians);
    static bool characterRangedAttackHitsArmorClass(
        int targetArmorClass,
        int attackBonus,
        float targetDistance,
        std::mt19937 &rng);
    static IdentifyMonsterReveal resolveIdentifyMonsterReveal(
        int identifySkillLevel,
        SkillMastery mastery,
        int monsterLevel);
    static IdentifyMonsterReveal resolveIdentifyMonsterReveal(const Character &character, int monsterLevel);
    static SpeechId resolveIdentifyMonsterSpeech(const Character &character, int monsterLevel);
    // The speaker's comment on what the party learned (the rules' reveal) about a monster of this level.
    static SpeechId resolveIdentifyMonsterSpeech(
        const IdentifyMonsterReveal &reveal,
        const Character &speaker,
        int monsterLevel);
    static CombatDamageType parseCombatDamageType(const std::string &value);
    static CombatDamageType spellCombatDamageType(uint32_t spellId, const SpellTable *pSpellTable);
    static int resolveCharacterIncomingDamage(
        const Character &character,
        const ItemTable *pItemTable,
        const StandardItemEnchantTable *pStandardItemEnchantTable,
        const SpecialItemEnchantTable *pSpecialItemEnchantTable,
        int damage,
        CombatDamageType damageType,
        std::mt19937 &rng);
    static int resolveMonsterIncomingDamage(
        int damage,
        CombatDamageType damageType,
        int resistance,
        int hourOfPowerResistanceBonus,
        std::mt19937 &rng);
    static int resolveMonsterIncomingWeaponDamage(
        int damage,
        CombatDamageType damageType,
        const ElementalDamageBonuses &additionalDamage,
        const MonsterDamageResistances &resistances,
        int hourOfPowerResistanceBonus,
        std::mt19937 &rng);
    static int rollMonsterAttackDamage(int diceRolls, int diceSides, int damageBonus, std::mt19937 &rng);
    static int resolveShieldedPhysicalProjectileDamage(int damage);
    static bool monsterAttackHitsArmorClass(
        int targetArmorClass,
        int monsterLevel,
        int attackBonus,
        std::mt19937 &rng);
    static std::optional<CharacterCondition> displayedCondition(const Character &character);
    // The condition as the character sheet names it ("Poisoned" for every poison).
    static std::string conditionName(CharacterCondition condition);
    static bool canAct(const Character &character);
    static int resolveCharacterPerceptionValue(const Character &character);
    static int resolvePartyPerceptionValue(const Party &party);
    static int resolveCharacterDisarmTrapValue(const Character &character);
    static bool partyDetectsSecretFaces(const Party &party, const MapStatsEntry &map);
    static bool canSelectInGameplay(const Character &character);
    static bool canTakeGameplayAction(const Character &character);
    static bool canCharacterEquipItem(
        const Character &character,
        const ItemDefinition &itemDefinition,
        const CharacterDollTypeEntry *pCharacterDollType);
    // Why canCharacterEquipItem refuses, when the reason is the character's (skill, class, race, stat).
    static std::optional<std::string> equipRefusalReason(
        const Character &character,
        const ItemDefinition &itemDefinition,
        const CharacterDollTypeEntry *pCharacterDollType);
    static std::optional<CharacterEquipPlan> resolveCharacterEquipPlan(
        const Character &character,
        const ItemDefinition &itemDefinition,
        const ItemTable *pItemTable,
        const CharacterDollTypeEntry *pCharacterDollType,
        std::optional<EquipmentSlot> explicitSlot,
        bool preferOffHand);
    static bool isEquipmentAllowedWithWetsuit(
        const Character &character,
        const ItemTable *pItemTable,
        EquipmentSlot targetSlot,
        uint32_t targetItemId,
        std::optional<EquipmentSlot> displacedSlot);
};
}
