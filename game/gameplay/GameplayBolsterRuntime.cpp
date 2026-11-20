#include "game/gameplay/GameplayBolsterRuntime.h"

#include "game/party/Party.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cctype>
#include <limits>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MaximumBolsteredHitPoints = 5000;
constexpr int BolsteredHitPointSoftCapStart = 3000;
constexpr int BolsterLevelEaseOutStart = 130;
constexpr double BolsterLevelEaseOutMultiplier = 0.6;
constexpr double BolsterLevelCatchUpMultiplier = 0.7;
constexpr float MaximumBolsterRewardMultiplier = 10.0f;

struct BolsteredHitPointResult
{
    int combatHitPoints = 1;
    int effectiveLevel = 1;
};

std::string lowercaseCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

bool isDisabledBolsterKind(const std::string &kind)
{
    const std::string normalized = lowercaseCopy(kind);
    return normalized.empty()
        || normalized == "0"
        || normalized == "-"
        || normalized == "nobolster";
}

bool isOriginalStatsBolsterKind(const std::string &kind)
{
    return lowercaseCopy(kind) == "originalstats";
}

bool isAllToEqualBolsterKind(const std::string &kind)
{
    return lowercaseCopy(kind) == "alltoequal";
}

bool isStyle(const MergedBolsterMonsterEntry *pMonsterSettings, const char *style)
{
    return pMonsterSettings != nullptr && lowercaseCopy(pMonsterSettings->style) == lowercaseCopy(style);
}

uint32_t monsterKindBaseId(uint32_t monsterId)
{
    return monsterId > 0 ? ((monsterId - 1u) / 3u) * 3u + 1u : 0u;
}

int monsterLevelShift(const MergedBolsterMonsterEntry *pMonsterSettings)
{
    return pMonsterSettings != nullptr && pMonsterSettings->extraPoints
        ? static_cast<int>(*pMonsterSettings->extraPoints)
        : 0;
}

int monsterFamilyLevel(
    const MonsterTable &monsterTable,
    const MergedBolsterMonsterTable *pMonsterSettingsTable,
    uint32_t monsterId)
{
    const uint32_t baseId = monsterKindBaseId(monsterId);

    if (baseId == 0)
    {
        return 3;
    }

    int levelSum = 0;
    int levelCount = 0;

    for (uint32_t offset = 0; offset < 3; ++offset)
    {
        const uint32_t familyMonsterId = baseId + offset;
        const MonsterTable::MonsterStatsEntry *pStats =
            monsterTable.findStatsById(static_cast<int16_t>(familyMonsterId));

        if (pStats == nullptr)
        {
            continue;
        }

        const MergedBolsterMonsterEntry *pMonsterSettings =
            pMonsterSettingsTable != nullptr ? pMonsterSettingsTable->findById(familyMonsterId) : nullptr;
        levelSum += pStats->level + monsterLevelShift(pMonsterSettings);
        ++levelCount;
    }

    if (levelCount == 0)
    {
        return 3;
    }

    return std::max(3, static_cast<int>(std::ceil(static_cast<double>(levelSum) / levelCount)));
}

uint32_t masteryValue(SkillMastery mastery)
{
    return static_cast<uint32_t>(mastery);
}

SkillMastery masteryFromValue(uint32_t value)
{
    switch (std::clamp<uint32_t>(value, 0, 4))
    {
        case 1:
            return SkillMastery::Normal;
        case 2:
            return SkillMastery::Expert;
        case 3:
            return SkillMastery::Master;
        case 4:
            return SkillMastery::Grandmaster;
        default:
            return SkillMastery::None;
    }
}

int defaultMonsterLevelForHitPoints(int hitPoints)
{
    if (hitPoints <= 0)
    {
        return 1;
    }

    const double rawLevel =
        (-30.0 + std::sqrt(900.0 + 40.0 * static_cast<double>(hitPoints))) / 2.0;
    return std::max(1, static_cast<int>(std::lround(rawLevel)));
}

uint32_t defaultMonsterExperienceForHitPoints(int hitPoints)
{
    const int level = defaultMonsterLevelForHitPoints(hitPoints);
    const uint64_t experience =
        static_cast<uint64_t>(level) * static_cast<uint64_t>(level + 10);
    return static_cast<uint32_t>(std::min<uint64_t>(
        experience,
        static_cast<uint64_t>(std::numeric_limits<uint32_t>::max())));
}

int defaultMonsterHitPointsForLevel(int level)
{
    const int clampedLevel = std::max(1, level);
    return std::max(1, clampedLevel * (clampedLevel + 30) / 10);
}

int applyBolsteredHitPointCap(int hitPoints)
{
    if (hitPoints <= BolsteredHitPointSoftCapStart)
    {
        return std::max(1, hitPoints);
    }

    const int softenedHitPoints =
        BolsteredHitPointSoftCapStart + static_cast<int>(
            std::lround(static_cast<double>(hitPoints - BolsteredHitPointSoftCapStart) * 0.5));
    return std::clamp(softenedHitPoints, 1, MaximumBolsteredHitPoints);
}

int monsterBaseBolsterLevel(const MonsterTable::MonsterStatsEntry &stats)
{
    return std::max(
        std::max(1, stats.level),
        defaultMonsterLevelForHitPoints(stats.hitPoints));
}

int easedBolsterTargetLevel(int targetLevel)
{
    if (targetLevel <= BolsterLevelEaseOutStart)
    {
        return std::max(1, targetLevel);
    }

    return std::max(
        BolsterLevelEaseOutStart,
        static_cast<int>(std::lround(
            static_cast<double>(BolsterLevelEaseOutStart)
            + static_cast<double>(targetLevel - BolsterLevelEaseOutStart) * BolsterLevelEaseOutMultiplier)));
}

double monsterBolsterLevelRatio(int baseLevel, int targetLevel)
{
    return std::max(1.0, static_cast<double>(std::max(1, targetLevel)) / static_cast<double>(std::max(1, baseLevel)));
}

int bolsteredMonsterEffectiveLevel(int baseLevel, int targetLevel)
{
    if (targetLevel <= baseLevel)
    {
        return std::max(1, baseLevel);
    }

    return std::max(
        baseLevel,
        static_cast<int>(std::lround(
            static_cast<double>(baseLevel)
            + static_cast<double>(targetLevel - baseLevel) * BolsterLevelCatchUpMultiplier)));
}

BolsteredHitPointResult bolsteredHitPointsForPseudoLevel(
    int baseHp,
    int baseLevel,
    int targetLevel,
    bool sizeAffectsHp,
    uint16_t monsterHeight,
    const MergedBolsterMonsterEntry *pMonsterSettings)
{
    if (baseHp <= 0)
    {
        return {};
    }

    (void)sizeAffectsHp;
    (void)monsterHeight;

    const int effectiveLevel = bolsteredMonsterEffectiveLevel(baseLevel, targetLevel);
    const int baseDefaultHp = defaultMonsterHitPointsForLevel(baseLevel);
    const int targetDefaultHp = defaultMonsterHitPointsForLevel(effectiveLevel);
    const double customHpRatio =
        static_cast<double>(std::max(1, baseHp)) / static_cast<double>(std::max(1, baseDefaultHp));
    int combatHitPoints =
        std::max(baseHp, static_cast<int>(std::lround(static_cast<double>(targetDefaultHp) * customHpRatio)));

    if (pMonsterSettings != nullptr && pMonsterSettings->maxHpBoostPercent)
    {
        const int cap =
            std::max(1, static_cast<int>(
                std::lround(static_cast<double>(baseHp) * *pMonsterSettings->maxHpBoostPercent / 100.0)));
        combatHitPoints = std::min(combatHitPoints, cap);
    }

    const int finalCombatHitPoints = applyBolsteredHitPointCap(combatHitPoints);
    return {finalCombatHitPoints, defaultMonsterLevelForHitPoints(finalCombatHitPoints)};
}

uint32_t spellSkillTargetForPseudoLevel(int pseudoLevel)
{
    return static_cast<uint32_t>(std::clamp((std::max(1, pseudoLevel) + 2) / 5, 1, 10));
}

SkillMastery spellMasteryTargetForPseudoLevel(int pseudoLevel)
{
    if (pseudoLevel >= 46)
    {
        return SkillMastery::Grandmaster;
    }

    if (pseudoLevel >= 31)
    {
        return SkillMastery::Master;
    }

    if (pseudoLevel >= 16)
    {
        return SkillMastery::Expert;
    }

    return SkillMastery::Normal;
}

uint32_t resolveSpellSkillLevel(
    uint32_t baseSkill,
    int effectivePseudoLevel)
{
    if (baseSkill == 0)
    {
        return 0;
    }

    return std::max(baseSkill, spellSkillTargetForPseudoLevel(effectivePseudoLevel));
}

SkillMastery resolveSpellMastery(
    SkillMastery baseMastery,
    int effectivePseudoLevel)
{
    const uint32_t baseValue = masteryValue(baseMastery);

    if (baseValue == 0)
    {
        return SkillMastery::None;
    }

    const uint32_t targetValue = masteryValue(spellMasteryTargetForPseudoLevel(effectivePseudoLevel));
    return masteryFromValue(std::max(baseValue, targetValue));
}

int bolsteredArmorClass(int armorClass, int baseLevel, int targetLevel)
{
    return std::max(
        0,
        static_cast<int>(std::lround(static_cast<double>(std::max(0, armorClass))
            * monsterBolsterLevelRatio(baseLevel, targetLevel))));
}

MonsterTable::MonsterStatsEntry::DamageProfile bolsteredAttackDamageProfile(
    const MonsterTable::MonsterStatsEntry::DamageProfile &baseDamage,
    int baseLevel,
    int targetLevel)
{
    MonsterTable::MonsterStatsEntry::DamageProfile result = baseDamage;
    const double levelRatio = monsterBolsterLevelRatio(baseLevel, targetLevel);

    if (levelRatio <= 1.0)
    {
        return result;
    }

    const int rolls = std::max(0, baseDamage.diceRolls);
    const int sides = std::max(0, baseDamage.diceSides);
    const double diceAverage = static_cast<double>(rolls) * static_cast<double>(sides + 1) / 2.0;
    const double baseAverage = diceAverage + static_cast<double>(std::max(0, baseDamage.bonus));
    const double scaledAverage = baseAverage * levelRatio;

    if (diceAverage <= 0.0)
    {
        result.bonus = std::max(baseDamage.bonus, static_cast<int>(std::lround(scaledAverage)));
        return result;
    }

    const double diceScale = std::sqrt(levelRatio);
    result.diceRolls = std::clamp(
        static_cast<int>(std::lround(static_cast<double>(rolls) * diceScale)),
        rolls,
        255);
    result.diceSides = std::clamp(
        static_cast<int>(std::lround(static_cast<double>(sides) * diceScale)),
        sides,
        255);

    const double scaledDiceAverage =
        static_cast<double>(result.diceRolls) * static_cast<double>(result.diceSides + 1) / 2.0;
    result.bonus = std::max(
        baseDamage.bonus,
        static_cast<int>(std::lround(scaledAverage - scaledDiceAverage)));
    return result;
}

int generatedSpellSkillLevel(bool magicStyle)
{
    return magicStyle ? 4 : 1;
}

SkillMastery generatedSpellSkillMastery(bool magicStyle)
{
    return magicStyle ? SkillMastery::Expert : SkillMastery::Normal;
}

std::string generatedProjectileToken(
    const MonsterTable::MonsterStatsEntry &stats,
    const MergedBolsterMonsterEntry *pMonsterSettings)
{
    if (!stats.attack1MissileType.empty())
    {
        return stats.attack1MissileType;
    }

    const std::string preferredMagic =
        pMonsterSettings != nullptr ? lowercaseCopy(pMonsterSettings->preferredMagic) : "";

    if (preferredMagic == "fire")
    {
        return "Fire";
    }

    if (preferredMagic == "air")
    {
        return "Air";
    }

    if (preferredMagic == "water")
    {
        return "Water";
    }

    if (preferredMagic == "earth")
    {
        return "Earth";
    }

    if (preferredMagic == "spirit")
    {
        return "Spirit";
    }

    if (preferredMagic == "mind")
    {
        return "Mind";
    }

    if (preferredMagic == "body" || preferredMagic == "self")
    {
        return "Body";
    }

    if (preferredMagic == "light")
    {
        return "Light";
    }

    if (preferredMagic == "dark")
    {
        return "Dark";
    }

    return "Arrow";
}

uint32_t magicSchoolIndex(const MergedBolsterMonsterEntry *pMonsterSettings)
{
    const std::string preferredMagic =
        pMonsterSettings != nullptr ? lowercaseCopy(pMonsterSettings->preferredMagic) : "";

    if (preferredMagic == "fire") return 1;
    if (preferredMagic == "air") return 2;
    if (preferredMagic == "water") return 3;
    if (preferredMagic == "earth") return 4;
    if (preferredMagic == "spirit") return 5;
    if (preferredMagic == "mind") return 6;
    if (preferredMagic == "body") return 7;
    if (preferredMagic == "light") return 8;
    if (preferredMagic == "dark") return 9;
    if (preferredMagic == "self") return 10;

    const uint32_t seed = pMonsterSettings != nullptr ? pMonsterSettings->id : 0;
    return (seed % 9u) + 1u;
}

uint32_t generatedSpellFromSet(
    const std::vector<uint32_t> &spellIds,
    int bolsterStep,
    int spellSlot,
    uint32_t otherSpellId)
{
    if (spellIds.empty())
    {
        return 0;
    }

    const size_t candidateCount = std::min<size_t>(
        spellIds.size(),
        static_cast<size_t>(std::max(1, bolsterStep + spellSlot + 1)));
    uint32_t spellId = spellIds[candidateCount - 1u];

    if (spellId == otherSpellId)
    {
        spellId = spellIds.front() != otherSpellId ? spellIds.front() : 0;
    }

    return spellId;
}

uint32_t generatedSpellId(
    const MergedBolsterMonsterEntry *pMonsterSettings,
    bool magicStyle,
    int bolsterStep,
    int spellSlot,
    uint32_t otherSpellId)
{
    static const std::array<std::vector<uint32_t>, 11> offensiveSpells = {{
        {},
        {2, 6, 11},
        {15, 18},
        {24, 26, 29, 32},
        {39, 41},
        {46, 47, 51, 59},
        {59, 65},
        {68, 70, 76},
        {78, 87},
        {90, 93, 95},
        {68, 71, 77},
    }};
    static const std::array<std::vector<uint32_t>, 11> defensiveSpells = {{
        {},
        {5},
        {17},
        {26},
        {38},
        {46, 47, 51, 52},
        {59, 65},
        {68, 71, 77},
        {86},
        {95},
        {68, 71, 77},
    }};

    const uint32_t schoolIndex = std::clamp<uint32_t>(magicSchoolIndex(pMonsterSettings), 1u, 10u);
    const bool defensive =
        lowercaseCopy(pMonsterSettings != nullptr ? pMonsterSettings->preferredMagic : "") == "self"
        || (magicStyle && spellSlot > 0);
    return generatedSpellFromSet(
        defensive ? defensiveSpells[schoolIndex] : offensiveSpells[schoolIndex],
        bolsterStep,
        spellSlot,
        otherSpellId);
}

void applyGeneratedAbilities(
    GameplayMonsterBolsterResult &result,
    const MonsterTable::MonsterStatsEntry &stats,
    const MergedBolsterMonsterEntry *pMonsterSettings,
    bool magicStyle)
{
    if (result.monsterAllowsNewRangedAttacks && stats.attack2Chance <= 0)
    {
        result.generatedAttack2 = true;
        result.generatedAttack2IsRanged = true;
        result.copyAttack1DamageToAttack2 = true;
        result.generatedAttack2MissileType = generatedProjectileToken(stats, pMonsterSettings);
        result.generatedAttack2Chance = std::min(result.bolsterStep * 10, 35);
    }

    if (!result.monsterAllowsNewSpells)
    {
        return;
    }

    if (!stats.hasSpell1 && (result.bolsterStep >= 1 || magicStyle))
    {
        result.generatedSpell1Id = generatedSpellId(pMonsterSettings, magicStyle, result.bolsterStep, 0, 0);
        result.generatedSpell1UseChance = magicStyle ? 60 : 35;
        result.spell1SkillLevel = generatedSpellSkillLevel(magicStyle);
        result.spell1SkillMastery = generatedSpellSkillMastery(magicStyle);
    }

    if (!stats.hasSpell2 && (result.bolsterStep >= 2 || (magicStyle && result.bolsterStep >= 1)))
    {
        result.generatedSpell2Id =
            generatedSpellId(pMonsterSettings, magicStyle, result.bolsterStep, 1, result.generatedSpell1Id);
        result.generatedSpell2UseChance = magicStyle ? 35 : 20;
        result.spell2SkillLevel = generatedSpellSkillLevel(magicStyle);
        result.spell2SkillMastery = generatedSpellSkillMastery(magicStyle);
    }
}
}

int gameplayBolsterAveragePartyLevel(const Party *pParty)
{
    if (pParty == nullptr || pParty->members().empty())
    {
        return 1;
    }

    uint32_t levelSum = 0;

    for (const Character &member : pParty->members())
    {
        levelSum += std::max<uint32_t>(1, member.level);
    }

    return std::max(1, static_cast<int>(std::ceil(
        static_cast<double>(levelSum) / static_cast<double>(pParty->members().size()))));
}

int gameplayBolsterPlayerArmorClass(
    int armorClass,
    int monsterLevel,
    int playerBaseLevel,
    bool bolsterAffectsArmorClass)
{
    if (!bolsterAffectsArmorClass)
    {
        return std::max(0, armorClass);
    }

    const double levelRatio =
        std::min(
            static_cast<double>(std::max(0, monsterLevel)) / static_cast<double>(std::max(1, playerBaseLevel)),
            1.0);
    return std::max(0, static_cast<int>(std::lround(static_cast<double>(std::max(0, armorClass)) * levelRatio)));
}

float gameplayBolsterRewardMultiplier(int baseMaxHp, int bolsteredMaxHp, bool statsEnabled)
{
    if (!statsEnabled || baseMaxHp <= 0 || bolsteredMaxHp <= baseMaxHp)
    {
        return 1.0f;
    }

    const float ratio = static_cast<float>(bolsteredMaxHp) / static_cast<float>(baseMaxHp);
    return std::clamp(ratio, 1.0f, MaximumBolsterRewardMultiplier);
}

uint32_t gameplayBolsterExperienceReward(int baseExperience, int baseHitPoints, float rewardMultiplier)
{
    if (baseExperience <= 0)
    {
        return 0;
    }

    const float multiplier = std::max(1.0f, rewardMultiplier);

    if (baseHitPoints <= 0 || multiplier <= 1.0f)
    {
        return static_cast<uint32_t>(baseExperience);
    }

    const uint32_t baseDefaultExperience = defaultMonsterExperienceForHitPoints(baseHitPoints);
    const int effectiveHitPoints = std::max(
        baseHitPoints,
        static_cast<int>(std::lround(static_cast<float>(baseHitPoints) * multiplier)));
    const uint32_t effectiveDefaultExperience = defaultMonsterExperienceForHitPoints(effectiveHitPoints);

    if (baseDefaultExperience == 0)
    {
        const double scaledExperience =
            static_cast<double>(baseExperience) * static_cast<double>(multiplier);
        return static_cast<uint32_t>(std::min<double>(
            std::lround(scaledExperience),
            static_cast<double>(std::numeric_limits<uint32_t>::max())));
    }

    const double scaledExperience =
        static_cast<double>(baseExperience)
        * static_cast<double>(effectiveDefaultExperience)
        / static_cast<double>(baseDefaultExperience);
    return static_cast<uint32_t>(std::min<double>(
        std::lround(scaledExperience),
        static_cast<double>(std::numeric_limits<uint32_t>::max())));
}

int gameplayBolsterEffectiveHitPoints(int baseHitPoints, float rewardMultiplier)
{
    if (baseHitPoints <= 0)
    {
        return 0;
    }

    const float multiplier = std::max(1.0f, rewardMultiplier);
    return std::max(
        baseHitPoints,
        static_cast<int>(std::lround(static_cast<float>(baseHitPoints) * multiplier)));
}

MonsterTable::LootPrototype gameplayBolsterLootPrototype(
    const MonsterTable::LootPrototype &loot,
    int baseHitPoints,
    float rewardMultiplier)
{
    const float multiplier = std::clamp(rewardMultiplier, 1.0f, MaximumBolsterRewardMultiplier);

    if (multiplier <= 1.0f)
    {
        return loot;
    }

    MonsterTable::LootPrototype result = loot;
    const int baseLevel = defaultMonsterLevelForHitPoints(baseHitPoints);
    const int effectiveLevel = defaultMonsterLevelForHitPoints(
        gameplayBolsterEffectiveHitPoints(baseHitPoints, multiplier));
    const float levelMultiplier =
        static_cast<float>(std::max(1, effectiveLevel)) / static_cast<float>(std::max(1, baseLevel));

    if (result.goldDiceRolls > 0 && result.goldDiceSides > 0)
    {
        result.goldDiceSides = std::max(
            result.goldDiceSides,
            static_cast<int>(std::lround(static_cast<float>(result.goldDiceSides) * levelMultiplier)));
    }

    if (result.itemChance > 0)
    {
        const float chanceMultiplier = std::min(multiplier, 3.0f);
        result.itemChance = std::clamp(
            static_cast<int>(std::lround(static_cast<float>(result.itemChance) * chanceMultiplier)),
            1,
            100);
    }

    if (result.itemLevel > 0)
    {
        const int itemLevelBonus = std::clamp((effectiveLevel - baseLevel) / 10, 0, 3);
        result.itemLevel = std::clamp(result.itemLevel + itemLevelBonus, 1, 6);
    }

    return result;
}

GameplayMonsterBolsterResult resolveGameplayMonsterBolster(
    const GameplayBolsterRuntimeContext &context,
    const MonsterTable::MonsterStatsEntry &stats,
    const MonsterEntry *pMonsterEntry)
{
    GameplayMonsterBolsterResult result = {};
    result.maxHp = std::max(1, stats.hitPoints);
    result.armorClass = stats.armorClass;
    result.moveSpeed = static_cast<uint16_t>(std::max(0, stats.speed));
    result.attack1DamageDiceRolls = stats.attack1Damage.diceRolls;
    result.attack1DamageDiceSides = stats.attack1Damage.diceSides;
    result.attack1DamageBonus = stats.attack1Damage.bonus;
    result.attack2DamageDiceRolls = stats.attack2Damage.diceRolls;
    result.attack2DamageDiceSides = stats.attack2Damage.diceSides;
    result.attack2DamageBonus = stats.attack2Damage.bonus;
    result.spell1SkillLevel = stats.spell1SkillLevel;
    result.spell1SkillMastery = stats.spell1SkillMastery;
    result.spell2SkillLevel = stats.spell2SkillLevel;
    result.spell2SkillMastery = stats.spell2SkillMastery;
    // MM8's Immobile kind (trees, boulders, reactors) never moves, on every map, as does a Stationary monster.
    const bool immobile =
        (stats.kindFlags & monsterKindFlag(MonsterKind::Immobile)) != 0
        || stats.movementType == MonsterTable::MonsterMovementType::Stationary;
    result.immobile = immobile;

    if (context.pMap == nullptr
        || context.pMonsterTable == nullptr
        || context.pBolsterMapTable == nullptr
        || context.pBolsterMonsterTable == nullptr
        || !context.bolsterMonstersEnabled
        || stats.id == 0)
    {
        return result;
    }

    const MergedBolsterMapEntry *pMapSettings = context.pBolsterMapTable->findById(context.pMap->id);

    if (pMapSettings == nullptr || isDisabledBolsterKind(pMapSettings->bolsterKind))
    {
        return result;
    }

    const uint32_t monsterId = static_cast<uint32_t>(std::max(0, stats.id));
    const MergedBolsterMonsterEntry *pMonsterSettings = context.pBolsterMonsterTable->findById(monsterId);
    const uint16_t monsterHeight = pMonsterEntry != nullptr ? pMonsterEntry->height : uint16_t(160);
    const int basePartyLevel =
        gameplayBolsterAveragePartyLevel(context.pParty) + static_cast<int>(pMapSettings->bolsterExtra);
    const int familyLevel = monsterFamilyLevel(*context.pMonsterTable, context.pBolsterMonsterTable, monsterId);
    const int baseMonsterLevel = monsterBaseBolsterLevel(stats);
    const int targetMonsterLevel = std::max(baseMonsterLevel, easedBolsterTargetLevel(basePartyLevel));
    const double partyToMonsterRatio =
        static_cast<double>(std::max(1, basePartyLevel)) / static_cast<double>(std::max(1, familyLevel));
    const bool allToEqual = isAllToEqualBolsterKind(pMapSettings->bolsterKind);
    const bool shouldBolsterMonster = allToEqual || basePartyLevel > baseMonsterLevel;
    const bool statsEnabled =
        shouldBolsterMonster
        && targetMonsterLevel > baseMonsterLevel
        && !isOriginalStatsBolsterKind(pMapSettings->bolsterKind);
    const bool magicStyle = isStyle(pMonsterSettings, "magic");

    result.mapEnabled = shouldBolsterMonster;
    result.statsEnabled = statsEnabled;
    result.mapAllowsSpells = pMapSettings->spells;
    result.mapAllowsSummons = pMapSettings->summons;
    result.partyLevel = basePartyLevel;
    result.monsterFamilyLevel = familyLevel;
    result.bolsterStep =
        std::clamp<int>(static_cast<int>(std::floor(partyToMonsterRatio)), 0, 4);

    if (pMonsterSettings != nullptr)
    {
        result.monsterAllowsNewRangedAttacks =
            shouldBolsterMonster && pMonsterSettings->newRangedAttacks && result.bolsterStep > 0;
        result.monsterAllowsNewSpells =
            shouldBolsterMonster
            && pMapSettings->spells
            && pMonsterSettings->newSpells
            && partyToMonsterRatio > 2.0;
        result.monsterAllowsSummons =
            shouldBolsterMonster
            && pMapSettings->summons
            && pMonsterSettings->newSummons
            && partyToMonsterRatio > 2.0;
        result.monsterAllowsReplicate =
            shouldBolsterMonster
            && pMapSettings->summons
            && pMonsterSettings->replicate
            && partyToMonsterRatio > 2.0;
        result.stationarySummonAsSpawnPoint = result.monsterAllowsSummons && immobile;
        result.summonMonsterId =
            pMonsterSettings->summonId ? *pMonsterSettings->summonId : monsterId;
        applyGeneratedAbilities(result, stats, pMonsterSettings, magicStyle);
    }

    if (!statsEnabled)
    {
        return result;
    }

    const BolsteredHitPointResult bolsteredHitPoints = bolsteredHitPointsForPseudoLevel(
        std::max(1, stats.hitPoints),
        baseMonsterLevel,
        targetMonsterLevel,
        pMonsterSettings != nullptr && pMonsterSettings->sizeAffectsHp,
        monsterHeight,
        pMonsterSettings);

    result.maxHp = bolsteredHitPoints.combatHitPoints;
    const int cappedTargetMonsterLevel = std::max(
        baseMonsterLevel,
        std::min(targetMonsterLevel, bolsteredHitPoints.effectiveLevel));
    result.armorClass = bolsteredArmorClass(stats.armorClass, baseMonsterLevel, cappedTargetMonsterLevel);
    const MonsterTable::MonsterStatsEntry::DamageProfile attack1Damage =
        bolsteredAttackDamageProfile(stats.attack1Damage, baseMonsterLevel, cappedTargetMonsterLevel);
    result.attack1DamageDiceRolls = attack1Damage.diceRolls;
    result.attack1DamageDiceSides = attack1Damage.diceSides;
    result.attack1DamageBonus = attack1Damage.bonus;
    const MonsterTable::MonsterStatsEntry::DamageProfile attack2Damage =
        bolsteredAttackDamageProfile(stats.attack2Damage, baseMonsterLevel, cappedTargetMonsterLevel);
    result.attack2DamageDiceRolls = attack2Damage.diceRolls;
    result.attack2DamageDiceSides = attack2Damage.diceSides;
    result.attack2DamageBonus = attack2Damage.bonus;

    if (isStyle(pMonsterSettings, "speed") || isStyle(pMonsterSettings, "strength"))
    {
        const double speedLimit = static_cast<double>(std::max(0, stats.speed))
            * (isStyle(pMonsterSettings, "speed") ? 3.0 : 1.75);
        const double scaledSpeed =
            static_cast<double>(std::max(0, stats.speed))
            * monsterBolsterLevelRatio(baseMonsterLevel, cappedTargetMonsterLevel);
        result.moveSpeed =
            static_cast<uint16_t>(std::clamp<int>(static_cast<int>(std::lround(
                std::min(scaledSpeed, speedLimit))), 0, 65535));
    }

    const int effectiveSpellPseudoLevel = bolsteredHitPoints.effectiveLevel;
    result.spell1SkillLevel = resolveSpellSkillLevel(stats.spell1SkillLevel, effectiveSpellPseudoLevel);
    result.spell1SkillMastery = resolveSpellMastery(stats.spell1SkillMastery, effectiveSpellPseudoLevel);
    result.spell2SkillLevel = resolveSpellSkillLevel(stats.spell2SkillLevel, effectiveSpellPseudoLevel);
    result.spell2SkillMastery = resolveSpellMastery(stats.spell2SkillMastery, effectiveSpellPseudoLevel);
    applyGeneratedAbilities(result, stats, pMonsterSettings, magicStyle);
    result.rewardMultiplier =
        gameplayBolsterRewardMultiplier(stats.hitPoints, result.maxHp, result.statsEnabled);

    return result;
}
}
