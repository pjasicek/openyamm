#include "game/gameplay/MercenaryRecruitmentRuntime.h"

#include "game/gameplay/GameMechanics.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemRuntime.h"
#include "game/StringUtils.h"
#include "game/party/SpellSchool.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/RaceStartingStatsTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <functional>
#include <limits>
#include <random>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t FirstMercenaryNpcId = 303;
constexpr uint32_t LastMercenaryNpcId = 310;
constexpr uint32_t FirstMercenaryRosterId = 42;
constexpr uint32_t PlaceholderNpcProfessionId = 0;
constexpr uint32_t MercenaryStartingGoldEquivalent = 0;
constexpr char MercenaryRefillMonthVariable[] = "MMerge.Mercenaries.RefillMonth";

constexpr std::array<uint32_t, 8> JadameBaseClassIds = {5, 8, 16, 20, 38, 40, 44, 48};
constexpr std::array<uint32_t, 10> AntagarichBaseClassIds = {0, 4, 12, 16, 22, 26, 30, 34, 42, 48};
constexpr std::array<uint32_t, 7> EnrothBaseClassIds = {0, 4, 12, 16, 26, 42, 48};

uint32_t averagePartyLevel(const Party &party)
{
    if (party.members().empty())
    {
        return 1;
    }

    uint32_t totalLevel = 0;

    for (const Character &member : party.members())
    {
        totalLevel += std::max<uint32_t>(1, member.level);
    }

    return std::max<uint32_t>(1, totalLevel / static_cast<uint32_t>(party.members().size()));
}

const ClassMultiplierEntry *classEntryForId(const ClassMultiplierTable *pClassMultiplierTable, uint32_t classId)
{
    if (pClassMultiplierTable == nullptr)
    {
        return nullptr;
    }

    for (const auto &[className, entry] : pClassMultiplierTable->entries())
    {
        (void)className;

        if (entry.classId == classId)
        {
            return &entry;
        }
    }

    return nullptr;
}

const ClassMultiplierEntry *classEntryForName(
    const ClassMultiplierTable *pClassMultiplierTable,
    const std::string &className)
{
    return pClassMultiplierTable != nullptr ? pClassMultiplierTable->get(canonicalClassName(className)) : nullptr;
}

uint32_t classKindForClassId(const ClassMultiplierTable *pClassMultiplierTable, uint32_t classId)
{
    const ClassMultiplierEntry *pEntry = classEntryForId(pClassMultiplierTable, classId);
    return pEntry != nullptr ? pEntry->classKind : 0;
}

std::vector<uint32_t> continentBaseClassIds(
    const MergedCharacterSelectionTable *pCharacterSelectionTable,
    uint32_t continentId)
{
    if (pCharacterSelectionTable != nullptr)
    {
        for (const MergedCharacterSelectionContinent &continent : pCharacterSelectionTable->continents())
        {
            if (continent.id == continentId && !continent.availableClassIds.empty())
            {
                return continent.availableClassIds;
            }
        }
    }

    if (continentId == 1)
    {
        return std::vector<uint32_t>(JadameBaseClassIds.begin(), JadameBaseClassIds.end());
    }

    if (continentId == 2)
    {
        return std::vector<uint32_t>(AntagarichBaseClassIds.begin(), AntagarichBaseClassIds.end());
    }

    return std::vector<uint32_t>(EnrothBaseClassIds.begin(), EnrothBaseClassIds.end());
}

std::string chooseClassName(
    uint32_t continentId,
    const Party &party,
    const MergedCharacterSelectionTable *pCharacterSelectionTable,
    const ClassMultiplierTable *pClassMultiplierTable,
    std::mt19937 &rng)
{
    if (pClassMultiplierTable == nullptr || pClassMultiplierTable->entries().empty())
    {
        return "Knight";
    }

    uint32_t leaderPromotionStep = 0;

    if (!party.members().empty())
    {
        const Character &leader = party.members().front();
        const ClassMultiplierEntry *pLeaderEntry =
            classEntryForName(pClassMultiplierTable, leader.className.empty() ? leader.role : leader.className);

        if (pLeaderEntry != nullptr)
        {
            leaderPromotionStep = pLeaderEntry->promotionStep;
        }
    }

    std::vector<uint32_t> classKinds;

    for (uint32_t classId : continentBaseClassIds(pCharacterSelectionTable, continentId))
    {
        const uint32_t classKind = classKindForClassId(pClassMultiplierTable, classId);

        if (classKind != 0 && std::find(classKinds.begin(), classKinds.end(), classKind) == classKinds.end())
        {
            classKinds.push_back(classKind);
        }
    }

    if (classKinds.empty())
    {
        classKinds = {2, 6, 14};
    }

    std::uniform_int_distribution<size_t> kindDistribution(0, classKinds.size() - 1);

    for (size_t attempt = 0; attempt < classKinds.size(); ++attempt)
    {
        const uint32_t classKind = classKinds[kindDistribution(rng)];
        std::vector<const ClassMultiplierEntry *> candidates;
        std::vector<const ClassMultiplierEntry *> lowestStepCandidates;
        uint32_t lowestStep = std::numeric_limits<uint32_t>::max();

        for (const auto &[className, entry] : pClassMultiplierTable->entries())
        {
            (void)className;

            if (entry.classKind != classKind)
            {
                continue;
            }

            if (entry.promotionStep <= leaderPromotionStep)
            {
                candidates.push_back(&entry);
            }

            if (entry.promotionStep < lowestStep)
            {
                lowestStep = entry.promotionStep;
                lowestStepCandidates.clear();
                lowestStepCandidates.push_back(&entry);
            }
            else if (entry.promotionStep == lowestStep)
            {
                lowestStepCandidates.push_back(&entry);
            }
        }

        const std::vector<const ClassMultiplierEntry *> &choices =
            !candidates.empty() ? candidates : lowestStepCandidates;

        if (!choices.empty())
        {
            std::uniform_int_distribution<size_t> classDistribution(0, choices.size() - 1);
            return canonicalClassName(choices[classDistribution(rng)]->className);
        }
    }

    return "Knight";
}

std::string portraitTextureNameForDoll(const CharacterDollEntry *pDoll)
{
    if (pDoll == nullptr)
    {
        return {};
    }

    if (!pDoll->facePicturesPrefix.empty())
    {
        return pDoll->facePicturesPrefix + "01";
    }

    if (pDoll->id == 0)
    {
        return {};
    }

    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-01", pDoll->id);
    return buffer;
}

bool portraitIsExcluded(
    const MergedCharacterSelectionTable *pCharacterSelectionTable,
    uint32_t continentId,
    const CharacterDollEntry &entry)
{
    if (pCharacterSelectionTable == nullptr)
    {
        return false;
    }

    for (const MergedCharacterSelectionContinent &continent : pCharacterSelectionTable->continents())
    {
        if (continent.id != continentId)
        {
            continue;
        }

        const std::string idToken = std::to_string(entry.id);
        const std::string prefixToken = toLowerCopy(entry.facePicturesPrefix);

        for (const std::string &exception : continent.portraitExceptions)
        {
            const std::string normalized = toLowerCopy(exception);

            if (normalized == idToken || (!prefixToken.empty() && normalized == prefixToken))
            {
                return true;
            }
        }
    }

    return false;
}

bool raceCanStartClass(
    const MergedCharacterSelectionTable *pCharacterSelectionTable,
    uint32_t raceId,
    const std::string &className)
{
    if (pCharacterSelectionTable == nullptr)
    {
        return false;
    }

    const std::vector<std::string> *pAllowedClasses = pCharacterSelectionTable->allowedClassesForRaceId(raceId);

    if (pAllowedClasses == nullptr)
    {
        return false;
    }

    const std::string canonicalTarget = canonicalClassName(className);

    for (const std::string &allowedClass : *pAllowedClasses)
    {
        if (canonicalClassName(allowedClass) == canonicalTarget)
        {
            return true;
        }
    }

    return false;
}

const CharacterDollEntry *chooseDoll(
    const CharacterDollTable *pCharacterDollTable,
    const MergedCharacterSelectionTable *pCharacterSelectionTable,
    const ClassMultiplierTable *pClassMultiplierTable,
    uint32_t continentId,
    const std::string &className,
    std::mt19937 &rng)
{
    if (pCharacterDollTable == nullptr)
    {
        return nullptr;
    }

    std::vector<const CharacterDollEntry *> classMatches;
    std::vector<const CharacterDollEntry *> raceMatches;
    std::vector<const CharacterDollEntry *> fallbackMatches;
    const ClassMultiplierEntry *pClassEntry = classEntryForName(pClassMultiplierTable, className);
    const uint32_t classKind = pClassEntry != nullptr ? pClassEntry->classKind : 0;

    for (const auto &[characterId, entry] : pCharacterDollTable->characters())
    {
        (void)characterId;

        if (!entry.availableAtStart
            || entry.npcPictureId == 0
            || entry.raceId == 10
            || portraitIsExcluded(pCharacterSelectionTable, continentId, entry))
        {
            continue;
        }

        fallbackMatches.push_back(&entry);
        const uint32_t defaultClassKind = classKindForClassId(pClassMultiplierTable, entry.defaultClassId);

        if (entry.defaultClassId == (pClassEntry != nullptr ? pClassEntry->classId : 0)
            || (classKind != 0 && defaultClassKind == classKind))
        {
            classMatches.push_back(&entry);
        }

        if (entry.raceId >= 0
            && pClassEntry != nullptr
            && raceCanStartClass(pCharacterSelectionTable, static_cast<uint32_t>(entry.raceId), pClassEntry->className))
        {
            raceMatches.push_back(&entry);
        }
    }

    std::vector<const CharacterDollEntry *> &choices =
        !classMatches.empty() ? classMatches : (!raceMatches.empty() ? raceMatches : fallbackMatches);

    if (choices.empty())
    {
        return nullptr;
    }

    std::sort(
        choices.begin(),
        choices.end(),
        [](const CharacterDollEntry *pLeft, const CharacterDollEntry *pRight)
        {
            return pLeft->id < pRight->id;
        });

    std::uniform_int_distribution<size_t> distribution(0, choices.size() - 1);
    return choices[distribution(rng)];
}

std::string chooseName(const MergedNpcNameTable *pNpcNameTable, uint32_t sexId, std::mt19937 &rng)
{
    if (pNpcNameTable != nullptr)
    {
        const std::vector<std::string> &names = sexId == 1
            ? pNpcNameTable->femaleNames()
            : pNpcNameTable->maleNames();

        if (!names.empty())
        {
            std::uniform_int_distribution<size_t> distribution(0, names.size() - 1);
            return names[distribution(rng)];
        }
    }

    return sexId == 1 ? "Mercenary" : "Mercenary";
}

void applyStartingStats(
    Character &character,
    const MergedCharacterSelectionTable *pCharacterSelectionTable,
    const RaceStartingStatsTable *pRaceStartingStatsTable,
    uint32_t raceId)
{
    const std::optional<std::string> raceName =
        pCharacterSelectionTable != nullptr ? pCharacterSelectionTable->raceNameForId(raceId) : std::nullopt;
    const RaceStartingStatsTable::Entry *pStats =
        pRaceStartingStatsTable != nullptr && raceName && !raceName->empty()
            ? pRaceStartingStatsTable->get(*raceName)
            : nullptr;

    std::array<int, 7> stats = pStats != nullptr ? pStats->stats : std::array<int, 7>{20, 20, 20, 20, 20, 20, 20};

    if (pStats != nullptr)
    {
        for (size_t statIndex = 0; statIndex < stats.size(); ++statIndex)
        {
            const int addStep = pStats->addSteps[statIndex];
            const int droppedStep = pStats->droppedSteps[statIndex];

            if (addStep == 1 && droppedStep <= 1)
            {
                stats[statIndex] = (pStats->stats[statIndex] + pStats->maximumStats[statIndex] + 1) / 2;
            }
            else if (addStep > 1 && addStep >= droppedStep)
            {
                stats[statIndex] = pStats->maximumStats[statIndex];
            }
        }
    }

    int bonusPool = static_cast<int>((character.level * 3 + 1) / 2);
    std::mt19937 rng(character.level * 1103515245u + character.characterDataId * 12345u + character.rosterId);

    while (bonusPool > 0)
    {
        for (int &stat : stats)
        {
            const int bonus = std::uniform_int_distribution<int>(0, 4)(rng);
            stat += bonus;
            bonusPool -= bonus;

            if (bonusPool <= 0)
            {
                break;
            }
        }
    }

    character.might = static_cast<uint32_t>(std::max(1, stats[0]));
    character.intellect = static_cast<uint32_t>(std::max(1, stats[1]));
    character.personality = static_cast<uint32_t>(std::max(1, stats[2]));
    character.endurance = static_cast<uint32_t>(std::max(1, stats[3]));
    character.speed = static_cast<uint32_t>(std::max(1, stats[4]));
    character.accuracy = static_cast<uint32_t>(std::max(1, stats[5]));
    character.luck = static_cast<uint32_t>(std::max(1, stats[6]));
}

uint32_t skillMasteryBucket(SkillMastery mastery)
{
    return static_cast<uint32_t>(mastery);
}

uint32_t skillLevelForBucket(uint32_t bucket)
{
    switch (bucket)
    {
        case 4:
            return 10;

        case 3:
            return 7;

        case 2:
            return 4;

        case 1:
        default:
            return 1;
    }
}

uint32_t skillPointCostForBucket(uint32_t bucket)
{
    switch (bucket)
    {
        case 4:
            return 54;

        case 3:
            return 27;

        case 2:
            return 9;

        case 1:
        default:
            return 0;
    }
}

uint32_t skillScore(const Character &character, const std::string &skillName)
{
    const CharacterSkill *pSkill = character.findSkillByCanonicalName(skillName);

    if (pSkill == nullptr)
    {
        return 0;
    }

    return skillMasteryBucket(pSkill->mastery) * 100 + pSkill->level;
}

void ensureBasicSkill(Character &character, const ClassSkillTable *pClassSkillTable, const std::string &skillName)
{
    if (pClassSkillTable == nullptr
        || pClassSkillTable->getEffectiveCap(character.className, character.raceId, skillName) == SkillMastery::None)
    {
        return;
    }

    CharacterSkill &skill = character.skills[skillName];

    if (skill.name.empty())
    {
        skill.name = skillName;
    }

    if (skill.mastery == SkillMastery::None || skill.level == 0)
    {
        skill.mastery = SkillMastery::Normal;
        skill.level = 1;
    }
}

void applySkills(Character &character, const ClassSkillTable *pClassSkillTable, std::mt19937 &rng)
{
    if (pClassSkillTable == nullptr)
    {
        return;
    }

    const std::vector<CharacterSkill> defaultSkills =
        pClassSkillTable->getDefaultSkillsForCharacter(character.className, character.raceId);

    for (const CharacterSkill &skill : defaultSkills)
    {
        character.skills[canonicalSkillName(skill.name)] = skill;
    }

    std::vector<std::string> availableSkills;

    for (const std::string &skillName : allCanonicalSkillNames())
    {
        if (pClassSkillTable->getEffectiveCap(character.className, character.raceId, skillName) != SkillMastery::None)
        {
            availableSkills.push_back(skillName);
        }
    }

    if (availableSkills.empty())
    {
        return;
    }

    std::shuffle(availableSkills.begin(), availableSkills.end(), rng);
    uint32_t skillBudget = character.level > 0 ? character.level * 5 - 5 : 0;
    const uint32_t desiredBucket = std::max<uint32_t>(1, (4 * std::max<uint32_t>(1, character.level) + 49) / 50);
    uint32_t baseOnlySkillCount = 0;
    uint32_t minimumBucket = 1;

    for (const std::string &skillName : availableSkills)
    {
        const SkillMastery cap = pClassSkillTable->getEffectiveCap(character.className, character.raceId, skillName);
        uint32_t bucket = skillName == "Blaster"
            ? 0
            : std::min<uint32_t>(desiredBucket, skillMasteryBucket(cap));

        if (bucket == 1)
        {
            ++baseOnlySkillCount;

            if (baseOnlySkillCount >= 4)
            {
                minimumBucket = 2;
            }
        }

        while (bucket >= minimumBucket && bucket > 0)
        {
            const uint32_t cost = skillPointCostForBucket(bucket);

            if (skillBudget >= cost)
            {
                CharacterSkill &skill = character.skills[skillName];
                skill.name = skillName;
                skill.mastery = static_cast<SkillMastery>(bucket);
                skill.level = skillLevelForBucket(bucket);
                skillBudget -= cost;
                break;
            }

            --bucket;
        }

        if (skillBudget == 0)
        {
            break;
        }
    }

    ensureBasicSkill(character, pClassSkillTable, "Merchant");
    ensureBasicSkill(character, pClassSkillTable, "IdentifyItem");
    character.skillPoints = skillBudget;
}

uint32_t &equipmentItemId(CharacterEquipment &equipment, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipment.offHand;

        case EquipmentSlot::MainHand:
            return equipment.mainHand;

        case EquipmentSlot::Bow:
            return equipment.bow;

        case EquipmentSlot::Armor:
            return equipment.armor;

        case EquipmentSlot::Helm:
            return equipment.helm;

        case EquipmentSlot::Belt:
            return equipment.belt;

        case EquipmentSlot::Cloak:
            return equipment.cloak;

        case EquipmentSlot::Gauntlets:
            return equipment.gauntlets;

        case EquipmentSlot::Boots:
            return equipment.boots;

        case EquipmentSlot::Amulet:
            return equipment.amulet;

        case EquipmentSlot::Ring1:
            return equipment.ring1;

        case EquipmentSlot::Ring2:
            return equipment.ring2;

        case EquipmentSlot::Ring3:
            return equipment.ring3;

        case EquipmentSlot::Ring4:
            return equipment.ring4;

        case EquipmentSlot::Ring5:
            return equipment.ring5;

        case EquipmentSlot::Ring6:
            return equipment.ring6;
    }

    return equipment.mainHand;
}

EquippedItemRuntimeState &equipmentRuntimeState(CharacterEquipmentRuntimeState &equipmentRuntime, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipmentRuntime.offHand;

        case EquipmentSlot::MainHand:
            return equipmentRuntime.mainHand;

        case EquipmentSlot::Bow:
            return equipmentRuntime.bow;

        case EquipmentSlot::Armor:
            return equipmentRuntime.armor;

        case EquipmentSlot::Helm:
            return equipmentRuntime.helm;

        case EquipmentSlot::Belt:
            return equipmentRuntime.belt;

        case EquipmentSlot::Cloak:
            return equipmentRuntime.cloak;

        case EquipmentSlot::Gauntlets:
            return equipmentRuntime.gauntlets;

        case EquipmentSlot::Boots:
            return equipmentRuntime.boots;

        case EquipmentSlot::Amulet:
            return equipmentRuntime.amulet;

        case EquipmentSlot::Ring1:
            return equipmentRuntime.ring1;

        case EquipmentSlot::Ring2:
            return equipmentRuntime.ring2;

        case EquipmentSlot::Ring3:
            return equipmentRuntime.ring3;

        case EquipmentSlot::Ring4:
            return equipmentRuntime.ring4;

        case EquipmentSlot::Ring5:
            return equipmentRuntime.ring5;

        case EquipmentSlot::Ring6:
            return equipmentRuntime.ring6;
    }

    return equipmentRuntime.mainHand;
}

void copyInventoryItemToEquipmentRuntime(const InventoryItem &item, EquippedItemRuntimeState &runtimeState)
{
    runtimeState.identified = item.identified;
    runtimeState.broken = item.broken;
    runtimeState.stolen = item.stolen;
    runtimeState.standardEnchantId = item.standardEnchantId;
    runtimeState.standardEnchantPower = item.standardEnchantPower;
    runtimeState.specialEnchantId = item.specialEnchantId;
    runtimeState.artifactId = item.artifactId;
    runtimeState.rarity = item.rarity;
    runtimeState.currentCharges = item.currentCharges;
    runtimeState.maxCharges = item.maxCharges;
    runtimeState.temporaryBonusRemainingSeconds = item.temporaryBonusRemainingSeconds;
}

bool tryEquipGeneratedItem(
    Character &character,
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const ItemTable *pItemTable,
    const CharacterDollTypeEntry *pDollType,
    std::optional<EquipmentSlot> slot)
{
    const std::optional<CharacterEquipPlan> equipPlan = GameMechanics::resolveCharacterEquipPlan(
        character,
        itemDefinition,
        pItemTable,
        pDollType,
        slot,
        false);

    if (!equipPlan || equipPlan->displacedSlot.has_value())
    {
        return false;
    }

    equipmentItemId(character.equipment, equipPlan->targetSlot) = item.objectDescriptionId;
    copyInventoryItemToEquipmentRuntime(
        item,
        equipmentRuntimeState(character.equipmentRuntime, equipPlan->targetSlot));
    return true;
}

std::optional<InventoryItem> generateEquipmentItem(
    const MercenaryRecruitmentTables &tables,
    uint32_t itemQuality,
    Party &party,
    std::mt19937 &rng,
    const std::function<bool(const ItemDefinition &)> &filter)
{
    if (tables.pItemTable == nullptr
        || tables.pStandardItemEnchantTable == nullptr
        || tables.pSpecialItemEnchantTable == nullptr)
    {
        return std::nullopt;
    }

    const ItemGenerationRequest request = {
        .treasureLevel = static_cast<int>(std::clamp<uint32_t>(itemQuality, 1, 6)),
        .mode = ItemGenerationMode::Generic,
        .allowRareItems = false,
        .rareItemsOnly = false,
    };

    std::optional<InventoryItem> item = ItemGenerator::generateRandomInventoryItem(
        *tables.pItemTable,
        *tables.pStandardItemEnchantTable,
        *tables.pSpecialItemEnchantTable,
        request,
        &party,
        rng,
        filter);

    if (item)
    {
        item->identified = true;
    }

    return item;
}

std::optional<std::string> highestKnownSkill(const Character &character, const std::vector<std::string> &skills)
{
    uint32_t bestScore = 0;
    std::optional<std::string> result;

    for (const std::string &skillName : skills)
    {
        const uint32_t score = skillScore(character, skillName);

        if (score > bestScore)
        {
            bestScore = score;
            result = skillName;
        }
    }

    return result;
}

bool generateAndEquipBySkill(
    Character &character,
    Party &party,
    const MercenaryRecruitmentTables &tables,
    const CharacterDollTypeEntry *pDollType,
    uint32_t itemQuality,
    std::mt19937 &rng,
    const std::string &skillName,
    std::optional<EquipmentSlot> slot)
{
    const std::optional<InventoryItem> item = generateEquipmentItem(
        tables,
        itemQuality,
        party,
        rng,
        [&skillName](const ItemDefinition &definition)
        {
            return canonicalSkillName(definition.skillGroup) == skillName
                && definition.equipStat != "0"
                && !definition.equipStat.empty();
        });

    if (!item || tables.pItemTable == nullptr)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = tables.pItemTable->get(item->objectDescriptionId);

    if (pItemDefinition == nullptr
        || !tryEquipGeneratedItem(character, *item, *pItemDefinition, tables.pItemTable, pDollType, slot))
    {
        return character.addInventoryItem(*item);
    }

    return true;
}

bool generateAndEquipByEquipStat(
    Character &character,
    Party &party,
    const MercenaryRecruitmentTables &tables,
    const CharacterDollTypeEntry *pDollType,
    uint32_t itemQuality,
    std::mt19937 &rng,
    const std::string &equipStat,
    EquipmentSlot slot)
{
    const std::optional<InventoryItem> item = generateEquipmentItem(
        tables,
        itemQuality,
        party,
        rng,
        [&equipStat](const ItemDefinition &definition)
        {
            return definition.equipStat == equipStat;
        });

    if (!item || tables.pItemTable == nullptr)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = tables.pItemTable->get(item->objectDescriptionId);

    if (pItemDefinition == nullptr
        || !tryEquipGeneratedItem(character, *item, *pItemDefinition, tables.pItemTable, pDollType, slot))
    {
        return character.addInventoryItem(*item);
    }

    return true;
}

void addGeneratedInventory(
    Character &character,
    Party &party,
    const MercenaryRecruitmentTables &tables,
    const CharacterDollEntry *pDoll,
    std::mt19937 &rng)
{
    if (tables.pItemTable == nullptr
        || tables.pStandardItemEnchantTable == nullptr
        || tables.pSpecialItemEnchantTable == nullptr)
    {
        return;
    }

    const CharacterDollTypeEntry *pDollType =
        pDoll != nullptr && tables.pCharacterDollTable != nullptr
            ? tables.pCharacterDollTable->getDollType(pDoll->dollTypeId)
            : nullptr;
    const uint32_t itemQuality = std::min<uint32_t>(
        5,
        (std::max<uint32_t>(1, character.level) + 7) / 8 + std::uniform_int_distribution<uint32_t>(0, 1)(rng));

    if (pDollType == nullptr || pDollType->canEquipWeapon)
    {
        const std::optional<std::string> weaponSkill =
            highestKnownSkill(character, {"Staff", "Sword", "Dagger", "Axe", "Spear", "Mace"});

        if (weaponSkill)
        {
            generateAndEquipBySkill(character, party, tables, pDollType, itemQuality, rng, *weaponSkill, std::nullopt);
        }
    }

    if (pDollType == nullptr || pDollType->canEquipBow)
    {
        if (skillScore(character, "Bow") > 0)
        {
            generateAndEquipBySkill(character, party, tables, pDollType, itemQuality, rng, "Bow", EquipmentSlot::Bow);
        }
    }

    if (pDollType == nullptr || pDollType->canEquipArmor)
    {
        const std::optional<std::string> armorSkill =
            highestKnownSkill(character, {"LeatherArmor", "ChainArmor", "PlateArmor"});

        if (armorSkill)
        {
            generateAndEquipBySkill(
                character,
                party,
                tables,
                pDollType,
                itemQuality,
                rng,
                *armorSkill,
                EquipmentSlot::Armor);
        }
    }

    std::vector<std::pair<std::string, EquipmentSlot>> apparel = {
        {"Helm", EquipmentSlot::Helm},
        {"Belt", EquipmentSlot::Belt},
        {"Cloak", EquipmentSlot::Cloak},
        {"Gauntlets", EquipmentSlot::Gauntlets},
        {"Boots", EquipmentSlot::Boots},
        {"Amulet", EquipmentSlot::Amulet},
        {"Ring", EquipmentSlot::Ring1},
    };
    std::shuffle(apparel.begin(), apparel.end(), rng);

    for (uint32_t itemIndex = 0; itemIndex < std::min<uint32_t>(itemQuality, static_cast<uint32_t>(apparel.size()));
         ++itemIndex)
    {
        const std::string &equipStat = apparel[itemIndex].first;

        if ((equipStat == "Helm" && pDollType != nullptr && !pDollType->canEquipHelm)
            || (equipStat == "Belt" && pDollType != nullptr && !pDollType->canEquipBelt)
            || (equipStat == "Cloak" && pDollType != nullptr && !pDollType->canEquipCloak)
            || (equipStat == "Boots" && pDollType != nullptr && !pDollType->canEquipBoots))
        {
            continue;
        }

        generateAndEquipByEquipStat(
            character,
            party,
            tables,
            pDollType,
            itemQuality,
            rng,
            equipStat,
            apparel[itemIndex].second);
    }

    (void)MercenaryStartingGoldEquivalent;
}

void applyClassResistances(Character &character)
{
    const std::string className = canonicalClassName(character.className);

    if (className == "Lich")
    {
        character.baseResistances.light = 65000;
        character.baseResistances.dark = 65000;
    }
    else if (className == "Vampire" || className == "Nosferatu")
    {
        character.baseResistances.light = 65000;
    }
}

bool spellLearningUsesMasteryCount(const std::string &skillName)
{
    const std::string canonical = canonicalSkillName(skillName);
    return canonical == "DarkElfAbility" || canonical == "VampireAbility" || canonical == "DragonAbility";
}

void applySpells(Character &character, const SpellTable *pSpellTable)
{
    character.knownSpellIds.clear();

    for (const auto &[skillName, skill] : character.skills)
    {
        if (skill.level == 0 || skill.mastery == SkillMastery::None)
        {
            continue;
        }

        const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(skillName);

        if (!spellRange)
        {
            continue;
        }

        const uint32_t availableSpellCount = spellRange->second - spellRange->first + 1;
        const uint32_t learnedSpellCount = std::min<uint32_t>(
            availableSpellCount,
            spellLearningUsesMasteryCount(skillName) ? skillMasteryBucket(skill.mastery) : skill.level);

        for (uint32_t spellOffset = 0; spellOffset < learnedSpellCount; ++spellOffset)
        {
            const uint32_t spellId = spellRange->first + spellOffset;

            if (pSpellTable == nullptr || pSpellTable->findById(static_cast<int>(spellId)) != nullptr)
            {
                character.learnSpell(spellId);
            }
        }
    }
}

EventRuntimeState::GeneratedMercenaryRecruit generateMercenary(
    const MapStatsEntry &map,
    Party &party,
    uint32_t npcId,
    uint32_t houseId,
    const MercenaryRecruitmentTables &tables)
{
    std::mt19937 rng(std::random_device{}());
    const std::string className = chooseClassName(
        map.mergedContinentId,
        party,
        tables.pCharacterSelectionTable,
        tables.pClassMultiplierTable,
        rng);
    const CharacterDollEntry *pDoll = chooseDoll(
        tables.pCharacterDollTable,
        tables.pCharacterSelectionTable,
        tables.pClassMultiplierTable,
        map.mergedContinentId,
        className,
        rng);

    Character character = {};
    character.rosterId = generatedMercenaryRosterIdForNpcId(npcId);
    character.characterDataId = pDoll != nullptr ? pDoll->id : 0;
    character.className = className;
    character.role = character.className;
    character.sexId = pDoll != nullptr ? pDoll->defaultSex : 0;
    character.raceId = pDoll != nullptr && pDoll->raceId >= 0 ? static_cast<uint32_t>(pDoll->raceId) : 0;
    character.voiceId = pDoll != nullptr ? static_cast<int32_t>(pDoll->defaultVoiceId) : -1;
    character.portraitPictureId = pDoll != nullptr && pDoll->id > 0 ? pDoll->id - 1 : 0;
    character.portraitTextureName = portraitTextureNameForDoll(pDoll);

    const uint32_t baseLevel = averagePartyLevel(party);
    std::uniform_int_distribution<int> levelOffset(-5, 8);
    character.level = static_cast<uint32_t>(std::max<int>(1, static_cast<int>(baseLevel) + levelOffset(rng)));
    character.experience = static_cast<uint32_t>(std::min<uint64_t>(
        static_cast<uint64_t>(character.level) * static_cast<uint64_t>(character.level - 1) * 500u,
        std::numeric_limits<uint32_t>::max()));

    applyStartingStats(
        character,
        tables.pCharacterSelectionTable,
        tables.pRaceStartingStatsTable,
        character.raceId);
    character.name = chooseName(tables.pNpcNameTable, character.sexId, rng);
    applySkills(character, tables.pClassSkillTable, rng);
    applySpells(character, tables.pSpellTable);
    addGeneratedInventory(character, party, tables, pDoll, rng);
    applyClassResistances(character);
    GameMechanics::refreshCharacterBaseResources(character, true, tables.pClassMultiplierTable);

    EventRuntimeState::GeneratedMercenaryRecruit recruit = {};
    recruit.npcId = npcId;
    recruit.rosterId = character.rosterId;
    recruit.houseId = houseId;
    recruit.portraitPictureId = character.portraitPictureId;
    recruit.npcPictureId = pDoll != nullptr ? pDoll->npcPictureId : 0;
    recruit.character = std::move(character);
    return recruit;
}

bool hasRosterOrInnMember(const Party &party, uint32_t rosterId)
{
    for (const Character &member : party.members())
    {
        if (member.rosterId == rosterId)
        {
            return true;
        }
    }

    for (const AdventurersInnMember &member : party.adventurersInnMembers())
    {
        if (member.character.rosterId == rosterId)
        {
            return true;
        }
    }

    return false;
}
}

bool isGeneratedMercenaryNpcId(uint32_t npcId)
{
    return npcId >= FirstMercenaryNpcId && npcId <= LastMercenaryNpcId;
}

uint32_t generatedMercenaryRosterIdForNpcId(uint32_t npcId)
{
    return isGeneratedMercenaryNpcId(npcId) ? FirstMercenaryRosterId + npcId - FirstMercenaryNpcId : 0;
}

uint32_t generatedMercenaryNpcIdForRosterId(uint32_t rosterId)
{
    if (rosterId < FirstMercenaryRosterId
        || rosterId >= FirstMercenaryRosterId + LastMercenaryNpcId - FirstMercenaryNpcId + 1)
    {
        return 0;
    }

    return FirstMercenaryNpcId + rosterId - FirstMercenaryRosterId;
}

std::optional<uint32_t> findMercenaryRecruitmentHouseId(
    const MapStatsEntry &map,
    const HouseTable &houseTable)
{
    std::optional<uint32_t> bestAdventurersInn;
    std::optional<uint32_t> bestTavern;

    for (const auto &[houseId, house] : houseTable.entries())
    {
        if (house.mapId != static_cast<uint32_t>(std::max(0, map.id)))
        {
            continue;
        }

        const std::string lowerType = toLowerCopy(house.type);
        const std::string lowerName = toLowerCopy(house.name);
        const bool isAdventurersInn =
            lowerName.find("adventurer") != std::string::npos
            || lowerType.find("adventurer") != std::string::npos;
        const bool isTavern =
            lowerType == "tavern"
            || lowerName.find("tavern") != std::string::npos
            || lowerName.find("inn") != std::string::npos;

        if (isAdventurersInn && (!bestAdventurersInn || houseId < *bestAdventurersInn))
        {
            bestAdventurersInn = houseId;
        }
        else if (isTavern && (!bestTavern || houseId < *bestTavern))
        {
            bestTavern = houseId;
        }
    }

    return bestTavern ? bestTavern : bestAdventurersInn;
}

bool refreshMercenaryRecruitmentForCurrentMap(
    const MapStatsEntry &map,
    Party &party,
    EventRuntimeState &runtimeState,
    float gameMinutes,
    const MercenaryRecruitmentTables &tables)
{
    if (tables.pHouseTable == nullptr)
    {
        return false;
    }

    const std::optional<uint32_t> houseId = findMercenaryRecruitmentHouseId(map, *tables.pHouseTable);

    if (!houseId)
    {
        return false;
    }

    const int32_t currentMonth = std::max(0, int32_t(std::floor(gameMinutes / (28 * 24 * 60))));
    const auto [monthIt, firstVisit] =
        runtimeState.namedMapVars.try_emplace(MercenaryRefillMonthVariable, currentMonth);
    const bool refill = firstVisit || monthIt->second != currentMonth;
    monthIt->second = currentMonth;

    for (uint32_t npcId = FirstMercenaryNpcId; npcId <= LastMercenaryNpcId; ++npcId)
    {
        const uint32_t rosterId = generatedMercenaryRosterIdForNpcId(npcId);

        if (rosterId == 0
            || hasRosterOrInnMember(party, rosterId)
            || runtimeState.unavailableNpcIds.contains(npcId))
        {
            continue;
        }

        EventRuntimeState::GeneratedMercenaryRecruit *pRecruit = nullptr;
        const auto recruitIt = runtimeState.generatedMercenaryRecruitsByNpcId.find(npcId);

        if (!refill && recruitIt == runtimeState.generatedMercenaryRecruitsByNpcId.end())
        {
            continue;
        }

        if (!refill)
        {
            pRecruit = &recruitIt->second;
        }
        else
        {
            EventRuntimeState::GeneratedMercenaryRecruit recruit =
                generateMercenary(map, party, npcId, *houseId, tables);
            pRecruit = &runtimeState.generatedMercenaryRecruitsByNpcId
                .insert_or_assign(npcId, std::move(recruit)).first->second;
        }

        pRecruit->houseId = *houseId;
        runtimeState.npcHouseOverrides[npcId] = *houseId;
        runtimeState.npcNameOverrides[npcId] = pRecruit->character.name;
        runtimeState.npcPictureOverrides[npcId] = pRecruit->npcPictureId;
        runtimeState.npcProfessionOverrides[npcId] = PlaceholderNpcProfessionId;
        party.setNpcHouseOverride(npcId, *houseId);
        return true;
    }

    return false;
}
}
