#pragma once

#include "game/gameplay/CharacterAttackTuning.h"
#include "game/party/Party.h"

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
    int wandSpellId = 0;
    int rangedSpellId = 0;
    float meleeRecoverySeconds = 1.0f;
    float rangedRecoverySeconds = 1.0f;
};

struct CharacterAttackResult
{
    CharacterAttackMode mode = CharacterAttackMode::None;
    bool canAttack = false;
    bool hit = false;
    bool resolvesOnImpact = false;
    int damage = 0;
    int attackBonus = 0;
    int targetArmorClass = 0;
    float targetDistance = 0.0f;
    float recoverySeconds = 0.0f;
    uint32_t skillLevel = 0;
    uint32_t skillMastery = 0;
    uint8_t projectileCount = 1;
    int spellId = 0;
    CombatDamageType damageType = CombatDamageType::Physical;
    bool criticalDamage = false;
    bool stunTarget = false;
    bool paralyzeTarget = false;
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

class GameMechanics
{
public:
    static void bindClassMultiplierTable(const ClassMultiplierTable *pClassMultiplierTable);
    static uint64_t experienceRequiredForNextLevel(uint32_t currentLevel);
    static uint32_t maximumTrainableLevelFromExperience(const Character &character);
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
    static std::string buildExperienceInspectSupplement(const Character &character);
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
    static CharacterSheetSummary buildCharacterSheetSummary(
        const Character &character,
        const ItemTable *pItemTable,
        const StandardItemEnchantTable *pStandardItemEnchantTable = nullptr,
        const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr,
        CharacterAttackTuning attackTuning = {});
    static CharacterAttackProfile buildCharacterAttackProfile(
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
    static bool characterRangedAttackHitsArmorClass(
        int targetArmorClass,
        int attackBonus,
        float targetDistance,
        std::mt19937 &rng);
    static SpeechId resolveIdentifyMonsterSpeech(const Character &character, int monsterLevel);
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
