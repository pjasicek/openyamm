#include "game/party/Party.h"

#include "game/events/EventRuntime.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/tables/RosterTable.h"
#include "game/party/SpellSchool.h"
#include "game/party/SpellIds.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <optional>
#include <random>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t OeMaxCharacterExperience = 4000000000u;
constexpr uint32_t ArcomageChampionAwardId = 41;
constexpr size_t ArcomageTavernCount = 11;
constexpr uint32_t Mm7ArcomageChampionQBit = 750;
constexpr uint32_t FirstMm7ArcomageHouseId = 240;
constexpr uint32_t LastMm7ArcomageHouseId = 252;
constexpr uint32_t RosterNpcPortraitBaseId = 2901;
constexpr float OeFiveGameMinuteTickRealSeconds = 10.0f;
constexpr float OeFiveGameMinuteTickGameSeconds = 5.0f * 60.0f;
constexpr uint32_t FirstRegularItemId = 1;
constexpr uint32_t LastRegularItemId = 134;
constexpr int GrandmasterUtilitySkillScore = std::numeric_limits<int>::max() / 4;

int utilitySkillMasteryMultiplier(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Normal:
            return 1;
        case SkillMastery::Expert:
            return 2;
        case SkillMastery::Master:
            return 3;
        case SkillMastery::Grandmaster:
            return 5;
        case SkillMastery::None:
        default:
            return 0;
    }
}

std::string canonicalPartyWideUtilitySkillName(std::string_view skillName)
{
    const std::string canonical = canonicalSkillName(std::string(skillName));

    if (canonical == "Repair")
    {
        return "RepairItem";
    }

    if (canonical == "DisarmTrap")
    {
        return "DisarmTraps";
    }

    return canonical;
}

int itemSkillBonusForName(const Character &member, const std::string &skillName)
{
    const auto iterator = member.itemSkillBonuses.find(skillName);
    return iterator != member.itemSkillBonuses.end() ? iterator->second : 0;
}

int genericUtilitySkillScore(const Character &member, const std::string &skillName)
{
    const CharacterSkill *pSkill = member.findSkill(skillName);
    const int itemBonus = itemSkillBonusForName(member, skillName);

    if ((pSkill == nullptr || pSkill->level == 0 || pSkill->mastery == SkillMastery::None) && itemBonus == 0)
    {
        return 0;
    }

    if (pSkill != nullptr && pSkill->mastery == SkillMastery::Grandmaster)
    {
        return GrandmasterUtilitySkillScore + static_cast<int>(pSkill->level) + std::max(0, itemBonus);
    }

    const int level = (pSkill != nullptr ? static_cast<int>(pSkill->level) : 0) + itemBonus;
    const SkillMastery mastery = pSkill != nullptr ? pSkill->mastery : SkillMastery::Normal;
    return std::max(0, level) * utilitySkillMasteryMultiplier(mastery);
}

int partyWideUtilitySkillScore(const Character &member, const std::string &skillName)
{
    if (skillName == "Perception")
    {
        return GameMechanics::resolveCharacterPerceptionValue(member);
    }

    if (skillName == "DisarmTraps")
    {
        return GameMechanics::resolveCharacterDisarmTrapValue(member);
    }

    if (skillName == "Merchant")
    {
        const int merchantScore = genericUtilitySkillScore(member, skillName);
        return merchantScore > 0
            ? merchantScore + std::max(0, member.merchantBonus)
            : std::max(0, member.merchantBonus);
    }

    return genericUtilitySkillScore(member, skillName);
}

bool hasWonAllMm7ArcomageTaverns(const std::unordered_set<uint32_t> &wonHouseIds)
{
    for (uint32_t houseId = FirstMm7ArcomageHouseId; houseId <= LastMm7ArcomageHouseId; ++houseId)
    {
        if (!wonHouseIds.contains(houseId))
        {
            return false;
        }
    }

    return true;
}

uint32_t resolveAdventurersInnPortraitPictureId(const Character &character, uint32_t portraitPictureId)
{
    if (character.rosterId != 0 && portraitPictureId < RosterNpcPortraitBaseId && character.portraitPictureId != 0)
    {
        return RosterNpcPortraitBaseId + character.portraitPictureId;
    }

    return portraitPictureId;
}

uint32_t remapCasterMemberIndexAfterDismiss(uint32_t casterMemberIndex, size_t dismissedMemberIndex)
{
    if (casterMemberIndex > dismissedMemberIndex)
    {
        return casterMemberIndex - 1;
    }

    return casterMemberIndex == dismissedMemberIndex ? 0 : casterMemberIndex;
}

bool characterNeedsTempleHealing(const Character &member)
{
    if (member.health < Party::effectiveMaximumHealth(member)
        || member.spellPoints < Party::effectiveMaximumSpellPoints(member))
    {
        return true;
    }

    for (size_t conditionIndex = 0; conditionIndex < CharacterConditionCount; ++conditionIndex)
    {
        if (member.conditions.test(conditionIndex))
        {
            return true;
        }
    }

    return false;
}

void clearTemporaryEventBonuses(Character &member)
{
    member.armorClassModifier = 0;
    member.levelModifier = 0;
    member.ageModifier = 0;
}

uint32_t primaryStatWithMagicalBonus(uint32_t baseValue, int magicalBonus)
{
    const int64_t adjustedValue = static_cast<int64_t>(baseValue) + magicalBonus;
    return static_cast<uint32_t>(std::clamp<int64_t>(adjustedValue, 0, std::numeric_limits<int>::max()));
}

int currentMaximumHealth(const Character &member)
{
    return Party::effectiveMaximumHealth(member);
}

int currentMaximumSpellPoints(const Character &member)
{
    return Party::effectiveMaximumSpellPoints(member);
}

void applyMagicalPrimaryStatResourceBonuses(
    Character &member,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    Character adjustedMember = member;
    adjustedMember.intellect = primaryStatWithMagicalBonus(member.intellect, member.magicalBonuses.intellect);
    adjustedMember.personality = primaryStatWithMagicalBonus(member.personality, member.magicalBonuses.personality);
    adjustedMember.endurance = primaryStatWithMagicalBonus(member.endurance, member.magicalBonuses.endurance);

    const int baseMaxHealth = GameMechanics::calculateBaseCharacterMaxHealth(member, pClassMultiplierTable);
    const int adjustedMaxHealth = GameMechanics::calculateBaseCharacterMaxHealth(adjustedMember, pClassMultiplierTable);
    member.magicalBonuses.maxHealth += adjustedMaxHealth - baseMaxHealth;

    const int baseMaxSpellPoints = GameMechanics::calculateBaseCharacterMaxSpellPoints(member, pClassMultiplierTable);
    const int adjustedMaxSpellPoints =
        GameMechanics::calculateBaseCharacterMaxSpellPoints(adjustedMember, pClassMultiplierTable);
    member.magicalBonuses.maxSpellPoints += adjustedMaxSpellPoints - baseMaxSpellPoints;
}

void clampCurrentResourcesToMaximum(Character &member)
{
    member.health = std::clamp(member.health, 0, currentMaximumHealth(member));
    member.spellPoints = std::clamp(member.spellPoints, 0, currentMaximumSpellPoints(member));
}

int regenerationSkillMultiplier(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Normal:
            return 1;
        case SkillMastery::Expert:
            return 2;
        case SkillMastery::Master:
            return 3;
        case SkillMastery::Grandmaster:
            return 4;
        case SkillMastery::None:
        default:
            return 0;
    }
}

float regenerationSkillHealthPerSecond(const Character &member)
{
    const CharacterSkill *pSkill = member.findSkill("Regeneration");

    if (pSkill == nullptr || pSkill->level == 0)
    {
        return 0.0f;
    }

    const int multiplier = regenerationSkillMultiplier(pSkill->mastery);
    const float healthPerFiveGameMinutes = static_cast<float>(pSkill->level * multiplier);
    return healthPerFiveGameMinutes / OeFiveGameMinuteTickRealSeconds;
}

void grantSeedSkill(Character &character, const std::string &skillName, uint32_t level = 1)
{
    CharacterSkill skill = {};
    skill.name = canonicalSkillName(skillName);
    skill.level = level;
    skill.mastery = SkillMastery::Normal;
    character.skills[skill.name] = skill;
}

void grantSeedSkill(Character &character, const std::string &skillName, uint32_t level, SkillMastery mastery)
{
    CharacterSkill skill = {};
    skill.name = canonicalSkillName(skillName);
    skill.level = level;
    skill.mastery = mastery;
    character.skills[skill.name] = skill;
}

const std::array<const char *, 12> &seedSpellSkillNames()
{
    static const std::array<const char *, 12> skillNames = {
        "FireMagic",
        "AirMagic",
        "WaterMagic",
        "EarthMagic",
        "SpiritMagic",
        "MindMagic",
        "BodyMagic",
        "LightMagic",
        "DarkMagic",
        "DarkElfAbility",
        "VampireAbility",
        "DragonAbility"
    };

    return skillNames;
}

void grantAllMagicSchools(Character &character, uint32_t level, SkillMastery mastery)
{
    for (const char *pSkillName : seedSpellSkillNames())
    {
        grantSeedSkill(character, pSkillName, level, mastery);
    }
}

void grantAllSkills(Character &character, uint32_t level, SkillMastery mastery)
{
    const std::vector<std::string> skillNames = allCanonicalSkillNames();

    for (const std::string &skillName : skillNames)
    {
        grantSeedSkill(character, skillName, level, mastery);
    }
}

void grantAllSpellsForMagicSkill(Character &character, const std::string &skillName)
{
    const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(skillName);

    if (!spellRange)
    {
        return;
    }

    for (uint32_t spellId = spellRange->first; spellId <= spellRange->second; ++spellId)
    {
        character.learnSpell(spellId);
    }
}

void grantAllSpells(Character &character)
{
    for (const char *pSkillName : seedSpellSkillNames())
    {
        grantAllSpellsForMagicSkill(character, pSkillName);
    }
}

void forgetAllSpellsForMagicSkill(Character &character, const std::string &skillName)
{
    const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(skillName);

    if (!spellRange)
    {
        return;
    }

    for (uint32_t spellId = spellRange->first; spellId <= spellRange->second; ++spellId)
    {
        character.forgetSpell(spellId);
    }
}

void applyRosterSpellKnowledge(Character &character, const RosterEntry &rosterEntry)
{
    for (const auto &[skillName, knownSpellCount] : rosterEntry.knownSpellCounts)
    {
        const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(skillName);

        if (!spellRange || knownSpellCount == 0)
        {
            continue;
        }

        const uint32_t firstSpellId = spellRange->first;
        const uint32_t lastSpellId = spellRange->second;
        const uint32_t spellCountInSchool = lastSpellId - firstSpellId + 1;
        const uint32_t learnedSpellCount = std::min(knownSpellCount, spellCountInSchool);

        for (uint32_t spellOffset = 0; spellOffset < learnedSpellCount; ++spellOffset)
        {
            character.learnSpell(firstSpellId + spellOffset);
        }
    }
}

void grantDefaultEquipmentSkills(Character &character)
{
    static const std::array<const char *, 11> skillNames = {
        "LeatherArmor",
        "ChainArmor",
        "PlateArmor",
        "Spear",
        "Sword",
        "Bow",
        "Dagger",
        "Mace",
        "Axe",
        "Staff",
        "Shield"
    };

    for (const char *pSkillName : skillNames)
    {
        grantSeedSkill(character, pSkillName);
    }
}

void grantSeedInventoryItem(
    Character &character,
    uint32_t itemId,
    bool identified,
    bool broken)
{
    InventoryItem item = {};
    item.objectDescriptionId = itemId;
    item.quantity = 1;
    item.width = 0;
    item.height = 0;
    item.identified = identified;
    item.broken = broken;
    character.inventory.push_back(item);
}

std::string normalizeRoleName(const std::string &className)
{
    const std::string canonicalName = canonicalClassName(className);

    if (canonicalName.empty())
    {
        return "Adventurer";
    }

    return displayClassName(canonicalName);
}

std::string normalizePartyClassName(const std::string &className, const ClassSkillTable *pClassSkillTable)
{
    const std::string canonicalName = canonicalClassName(className);

    if (canonicalName.empty() || pClassSkillTable == nullptr)
    {
        return canonicalName;
    }

    for (char character : canonicalName)
    {
        if (std::isdigit(static_cast<unsigned char>(character)) == 0)
        {
            return canonicalName;
        }
    }

    char *pEnd = nullptr;
    const unsigned long classId = std::strtoul(canonicalName.c_str(), &pEnd, 10);

    if (pEnd == canonicalName.c_str() || *pEnd != '\0')
    {
        return canonicalName;
    }

    const std::optional<std::string> resolvedClassName =
        pClassSkillTable->classNameForId(static_cast<uint32_t>(classId));

    return resolvedClassName ? canonicalClassName(*resolvedClassName) : canonicalName;
}

uint32_t generateHouseStockSeed()
{
    std::random_device randomDevice;
    const uint32_t first = static_cast<uint32_t>(randomDevice());
    const uint32_t second = static_cast<uint32_t>(randomDevice());
    const uint32_t mixed = first ^ (second * 1664525u) ^ 0x9e3779b9u;
    return mixed != 0 ? mixed : 1u;
}

template <size_t N>
SoundId pickRandomSoundId(const std::array<SoundId, N> &soundIds)
{
    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<size_t> distribution(0, N - 1);
    return soundIds[distribution(rng)];
}

bool isPotionExplosionBreakCandidate(const InventoryItem &item)
{
    return item.objectDescriptionId >= FirstRegularItemId
        && item.objectDescriptionId <= LastRegularItemId;
}

void breakPotionExplosionItems(Character &member, uint8_t count)
{
    std::vector<InventoryItem *> candidates;

    for (InventoryItem &item : member.inventory)
    {
        if (isPotionExplosionBreakCandidate(item))
        {
            candidates.push_back(&item);
        }
    }

    if (candidates.empty())
    {
        return;
    }

    if (count == 0)
    {
        for (InventoryItem *pItem : candidates)
        {
            pItem->broken = true;
        }

        return;
    }

    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<size_t> distribution(0, candidates.size() - 1);

    for (uint8_t index = 0; index < count; ++index)
    {
        candidates[distribution(rng)]->broken = true;
    }
}

int potionExplosionDamage(uint8_t damageLevel)
{
    static thread_local std::mt19937 rng(std::random_device{}());

    switch (damageLevel)
    {
        case 1:
            return std::uniform_int_distribution<int>(10, 20)(rng);

        case 2:
            return std::uniform_int_distribution<int>(30, 100)(rng);

        case 3:
            return std::uniform_int_distribution<int>(50, 250)(rng);

        default:
            return 0;
    }
}

std::string portraitTextureNameFromPictureId(uint32_t pictureId)
{
    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-01", pictureId + 1);
    return buffer;
}

std::string portraitTextureNameFromCharacterDollEntry(const CharacterDollEntry &entry)
{
    if (!entry.facePicturesPrefix.empty())
    {
        return entry.facePicturesPrefix + "01";
    }

    return entry.id > 0 ? portraitTextureNameFromPictureId(entry.id - 1) : std::string();
}

std::optional<uint32_t> tryParsePictureIdFromPortraitTextureName(const std::string &portraitTextureName)
{
    if (portraitTextureName.size() < 6)
    {
        return std::nullopt;
    }

    const std::string normalized = toLowerCopy(portraitTextureName);

    if (normalized[0] != 'p' || normalized[1] != 'c'
        || !std::isdigit(static_cast<unsigned char>(normalized[2]))
        || !std::isdigit(static_cast<unsigned char>(normalized[3])))
    {
        return std::nullopt;
    }

    const uint32_t faceNumber = static_cast<uint32_t>((normalized[2] - '0') * 10 + (normalized[3] - '0'));

    if (faceNumber == 0)
    {
        return std::nullopt;
    }

    return faceNumber - 1;
}

Character buildCharacterFromRosterEntry(
    const RosterEntry &rosterEntry,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    Character member = {};
    member.name = rosterEntry.name;
    member.className = canonicalClassName(rosterEntry.className);
    member.role = normalizeRoleName(member.className);
    member.portraitTextureName = portraitTextureNameFromPictureId(rosterEntry.pictureId);
    member.portraitPictureId = rosterEntry.pictureId;
    member.characterDataId = rosterEntry.pictureId + 1;
    member.voiceId = rosterEntry.voiceId;
    member.rosterId = rosterEntry.id;
    member.birthYear = rosterEntry.birthYear;
    member.experience = rosterEntry.experience;
    member.level = std::max<uint32_t>(1, rosterEntry.level);
    member.skillPoints = rosterEntry.skillPoints;
    member.might = rosterEntry.might;
    member.intellect = rosterEntry.intellect;
    member.personality = rosterEntry.personality;
    member.endurance = rosterEntry.endurance;
    member.speed = rosterEntry.speed;
    member.accuracy = rosterEntry.accuracy;
    member.luck = rosterEntry.luck;
    member.baseResistances = rosterEntry.baseResistances;
    member.skills = rosterEntry.skills;
    applyRosterSpellKnowledge(member, rosterEntry);

    GameMechanics::refreshCharacterBaseResources(member, true, pClassMultiplierTable);
    return member;
}

void initializePortraitRuntimeState(Character &member)
{
    const std::optional<uint32_t> parsedPictureId = tryParsePictureIdFromPortraitTextureName(member.portraitTextureName);

    if (parsedPictureId)
    {
        member.portraitPictureId = *parsedPictureId;
    }
    else if (member.portraitTextureName.empty())
    {
        member.portraitTextureName = portraitTextureNameFromPictureId(member.portraitPictureId);
    }

    member.portraitState = PortraitId::Normal;
    member.portraitElapsedTicks = 0;
    member.portraitDurationTicks = 0;
    member.portraitSequenceCounter = 0;
    member.portraitImageIndex = 0;
}

std::optional<std::pair<uint8_t, uint8_t>> findFirstFreeInventorySlot(
    const std::vector<InventoryItem> &inventory,
    uint8_t width,
    uint8_t height)
{
    if (width == 0 || height == 0 || width > Character::InventoryWidth || height > Character::InventoryHeight)
    {
        return std::nullopt;
    }

    std::array<bool, Character::InventoryWidth * Character::InventoryHeight> occupied = {};

    for (const InventoryItem &item : inventory)
    {
        for (uint8_t y = 0; y < item.height; ++y)
        {
            for (uint8_t x = 0; x < item.width; ++x)
            {
                const uint8_t cellX = item.gridX + x;
                const uint8_t cellY = item.gridY + y;

                if (cellX >= Character::InventoryWidth || cellY >= Character::InventoryHeight)
                {
                    continue;
                }

                occupied[static_cast<size_t>(cellY) * Character::InventoryWidth + cellX] = true;
            }
        }
    }

    for (int x = 0; x <= Character::InventoryWidth - width; ++x)
    {
        for (int y = 0; y <= Character::InventoryHeight - height; ++y)
        {
            bool canPlace = true;

            for (uint8_t offsetY = 0; offsetY < height && canPlace; ++offsetY)
            {
                for (uint8_t offsetX = 0; offsetX < width; ++offsetX)
                {
                    const size_t index =
                        static_cast<size_t>(y + offsetY) * Character::InventoryWidth + static_cast<size_t>(x + offsetX);

                    if (occupied[index])
                    {
                        canPlace = false;
                        break;
                    }
                }
            }

            if (canPlace)
            {
                return std::pair<uint8_t, uint8_t>(static_cast<uint8_t>(x), static_cast<uint8_t>(y));
            }
        }
    }

    return std::nullopt;
}

bool inventoryItemContainsCell(const InventoryItem &item, uint8_t gridX, uint8_t gridY)
{
    return gridX >= item.gridX
        && gridX < item.gridX + item.width
        && gridY >= item.gridY
        && gridY < item.gridY + item.height;
}

const char *equipmentSlotName(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::MainHand:
            return "MainHand";
        case EquipmentSlot::OffHand:
            return "OffHand";
        case EquipmentSlot::Bow:
            return "Bow";
        case EquipmentSlot::Armor:
            return "Armor";
        case EquipmentSlot::Helm:
            return "Helm";
        case EquipmentSlot::Belt:
            return "Belt";
        case EquipmentSlot::Cloak:
            return "Cloak";
        case EquipmentSlot::Gauntlets:
            return "Gauntlets";
        case EquipmentSlot::Boots:
            return "Boots";
        case EquipmentSlot::Amulet:
            return "Amulet";
        case EquipmentSlot::Ring1:
            return "Ring1";
        case EquipmentSlot::Ring2:
            return "Ring2";
        case EquipmentSlot::Ring3:
            return "Ring3";
        case EquipmentSlot::Ring4:
            return "Ring4";
        case EquipmentSlot::Ring5:
            return "Ring5";
        case EquipmentSlot::Ring6:
            return "Ring6";
    }

    return "Unknown";
}

void logItemInteractionResult(
    const char *pAction,
    const Character *pInspector,
    const Character *pOwner,
    const ItemDefinition *pItemDefinition,
    const std::string &location,
    bool success,
    const std::string &statusText)
{
    std::cout << "Item " << pAction
              << ": inspector=\"" << (pInspector != nullptr ? pInspector->name : "")
              << "\" owner=\"" << (pOwner != nullptr ? pOwner->name : "")
              << "\" item=\"" << (pItemDefinition != nullptr ? pItemDefinition->name : "")
              << "\" location=" << location
              << " result=" << (success ? "success" : "failed");

    if (!statusText.empty())
    {
        std::cout << " status=\"" << statusText << "\"";
    }

    std::cout << '\n';
}

constexpr uint32_t AttackPreferenceKnight = 0x0001;
constexpr uint32_t AttackPreferencePaladin = 0x0002;
constexpr uint32_t AttackPreferenceArcher = 0x0004;
constexpr uint32_t AttackPreferenceDruid = 0x0008;
constexpr uint32_t AttackPreferenceCleric = 0x0010;
constexpr uint32_t AttackPreferenceSorcerer = 0x0020;
constexpr uint32_t AttackPreferenceRanger = 0x0040;
constexpr uint32_t AttackPreferenceThief = 0x0080;
constexpr uint32_t AttackPreferenceMonk = 0x0100;
constexpr uint32_t AttackPreferenceMale = 0x0200;
constexpr uint32_t AttackPreferenceFemale = 0x0400;
constexpr uint32_t AttackPreferenceHuman = 0x0800;
constexpr uint32_t AttackPreferenceElf = 0x1000;
constexpr uint32_t AttackPreferenceDwarf = 0x2000;
constexpr uint32_t AttackPreferenceGoblin = 0x4000;
constexpr uint32_t CharacterSexMale = 0;
constexpr uint32_t CharacterSexFemale = 1;
constexpr uint32_t CharacterRaceHuman = 0;
constexpr uint32_t CharacterRaceMinotaur = 3;
constexpr uint32_t CharacterRaceTroll = 4;
constexpr uint32_t CharacterRaceDragon = 5;
constexpr uint32_t CharacterRaceUndead = 6;
constexpr uint32_t CharacterRaceDarkElf = 2;
constexpr uint32_t CharacterRaceElf = 7;
constexpr uint32_t CharacterRaceGoblin = 8;
constexpr uint32_t CharacterRaceDwarf = 9;
constexpr uint32_t MaleLichCharacterDataId = 27;
constexpr uint32_t FemaleLichCharacterDataId = 28;
constexpr uint32_t MaleDwarfLichCharacterDataId = 66;
constexpr uint32_t FemaleDwarfLichCharacterDataId = 67;
constexpr uint32_t DragonLichCharacterDataId = 68;
constexpr uint32_t MinotaurLichCharacterDataId = 70;
constexpr uint32_t TrollLichCharacterDataId = 76;

void applyCharacterIdentityFromDollTable(Character &member, const CharacterDollTable *pCharacterDollTable)
{
    if (member.characterDataId == 0
        && (member.rosterId != 0 || !member.portraitTextureName.empty() || member.portraitPictureId != 0))
    {
        member.characterDataId = member.portraitPictureId + 1;
    }

    if (pCharacterDollTable == nullptr || member.characterDataId == 0)
    {
        return;
    }

    const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(member.characterDataId);

    if (pEntry == nullptr)
    {
        return;
    }

    if (member.voiceId < 0)
    {
        member.voiceId = static_cast<int32_t>(pEntry->defaultVoiceId);
    }

    member.sexId = pEntry->defaultSex;

    if (pEntry->raceId >= 0)
    {
        member.raceId = static_cast<uint32_t>(pEntry->raceId);
    }
}

void applyCharacterDollIdentity(Character &member, const CharacterDollTable *pCharacterDollTable, bool forceVoice)
{
    if (pCharacterDollTable == nullptr || member.characterDataId == 0)
    {
        return;
    }

    const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(member.characterDataId);

    if (pEntry == nullptr)
    {
        return;
    }

    if (forceVoice || member.voiceId < 0)
    {
        member.voiceId = static_cast<int32_t>(pEntry->defaultVoiceId);
    }

    member.sexId = pEntry->defaultSex;

    if (pEntry->raceId >= 0)
    {
        member.raceId = static_cast<uint32_t>(pEntry->raceId);
    }
}

void applyLichIdentity(Character &member, const CharacterDollTable *pCharacterDollTable)
{
    if (member.raceId == CharacterRaceUndead)
    {
        return;
    }

    const bool female = member.sexId == CharacterSexFemale;

    switch (member.raceId)
    {
        case CharacterRaceDragon:
            member.characterDataId = DragonLichCharacterDataId;
            break;
        case CharacterRaceMinotaur:
            member.characterDataId = MinotaurLichCharacterDataId;
            break;
        case CharacterRaceTroll:
            member.characterDataId = TrollLichCharacterDataId;
            break;
        case CharacterRaceDwarf:
            member.characterDataId = female ? FemaleDwarfLichCharacterDataId : MaleDwarfLichCharacterDataId;
            break;
        default:
            member.characterDataId = female ? FemaleLichCharacterDataId : MaleLichCharacterDataId;
            break;
    }

    const CharacterDollEntry *pLichEntry = pCharacterDollTable != nullptr
        ? pCharacterDollTable->getCharacter(member.characterDataId)
        : nullptr;
    member.portraitPictureId = member.characterDataId - 1;
    member.portraitTextureName = pLichEntry != nullptr
        ? portraitTextureNameFromCharacterDollEntry(*pLichEntry)
        : portraitTextureNameFromPictureId(member.portraitPictureId);
    member.portraitState = PortraitId::Normal;
    member.portraitElapsedTicks = 0;
    member.portraitDurationTicks = 0;
    member.portraitImageIndex = 0;
    applyCharacterDollIdentity(member, pCharacterDollTable, true);
}

void refundAndClearSkill(Character &member, const std::string &skillName)
{
    const std::unordered_map<std::string, CharacterSkill>::iterator skillIt = member.skills.find(skillName);

    if (skillIt == member.skills.end())
    {
        return;
    }

    const uint32_t level = skillIt->second.level;

    if (level > 0)
    {
        const uint32_t spentSkillPoints = level * (level + 1) / 2;
        member.skillPoints += spentSkillPoints > 0 ? spentSkillPoints - 1 : 0;
    }

    member.skills.erase(skillIt);
}

void applyLichState(Character &member)
{
    member.baseResistances.fire = std::max(member.baseResistances.fire, 20);
    member.baseResistances.air = std::max(member.baseResistances.air, 20);
    member.baseResistances.water = std::max(member.baseResistances.water, 20);
    member.baseResistances.earth = std::max(member.baseResistances.earth, 20);
    member.baseResistances.light = std::max(member.baseResistances.light, 65000);
    member.baseResistances.dark = std::max(member.baseResistances.dark, 65000);
    member.permanentImmunities.light = true;
    member.permanentImmunities.dark = true;
    refundAndClearSkill(member, "ChainArmor");
    refundAndClearSkill(member, "RepairItem");
}

bool isValidMonsterAttackTarget(const Character &member)
{
    return member.health > 0
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Paralyzed))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated));
}

bool matchesMonsterAttackPreference(const Character &member, uint32_t preferenceFlag)
{
    const std::string className = canonicalClassName(member.className.empty() ? member.role : member.className);
    const bool hasCharacterIdentity = member.characterDataId != 0;
    const std::string normalizedRole = toLowerCopy(member.role);
    const std::string normalizedClassName = toLowerCopy(className);

    switch (preferenceFlag)
    {
        case AttackPreferenceKnight:
            return className == "Knight";

        case AttackPreferencePaladin:
            return className == "Paladin";

        case AttackPreferenceArcher:
            return className == "Archer";

        case AttackPreferenceDruid:
            return className == "Druid";

        case AttackPreferenceCleric:
            return className == "Cleric";

        case AttackPreferenceSorcerer:
            return className == "Sorcerer";

        case AttackPreferenceRanger:
            return className == "Ranger";

        case AttackPreferenceThief:
            return className == "Thief";

        case AttackPreferenceMonk:
            return className == "Monk";

        case AttackPreferenceMale:
            return hasCharacterIdentity ? member.sexId == CharacterSexMale : false;

        case AttackPreferenceFemale:
            return hasCharacterIdentity ? member.sexId == CharacterSexFemale : false;

        case AttackPreferenceHuman:
            return hasCharacterIdentity
                ? member.raceId == CharacterRaceHuman
                : className == "Knight"
                || className == "Paladin"
                || className == "Archer"
                || className == "Druid"
                || className == "Cleric"
                || className == "Sorcerer"
                || className == "Ranger"
                || className == "Thief"
                || className == "Monk";

        case AttackPreferenceElf:
            return hasCharacterIdentity
                ? member.raceId == CharacterRaceDarkElf || member.raceId == CharacterRaceElf
                : className == "DarkElf";

        case AttackPreferenceDwarf:
            return normalizedClassName.find("dwarf") != std::string::npos
                || normalizedRole.find("dwarf") != std::string::npos;

        case AttackPreferenceGoblin:
            return hasCharacterIdentity
                ? member.raceId == CharacterRaceGoblin
                : className == "Goblin";

        default:
            return false;
    }
}

bool hasConditionImmunity(const Character &member, CharacterCondition condition)
{
    const size_t conditionIndex = static_cast<size_t>(condition);

    return conditionIndex < CharacterConditionCount
        && (member.permanentConditionImmunities.test(conditionIndex)
            || member.magicalConditionImmunities.test(conditionIndex));
}

bool conditionAffectedByProtectionFromMagic(CharacterCondition condition)
{
    switch (condition)
    {
        case CharacterCondition::Weak:
        case CharacterCondition::PoisonWeak:
        case CharacterCondition::DiseaseWeak:
        case CharacterCondition::PoisonMedium:
        case CharacterCondition::DiseaseMedium:
        case CharacterCondition::PoisonSevere:
        case CharacterCondition::DiseaseSevere:
        case CharacterCondition::Paralyzed:
        case CharacterCondition::Dead:
        case CharacterCondition::Petrified:
        case CharacterCondition::Eradicated:
            return true;

        default:
            return false;
    }
}

bool conditionRequiresGrandmasterProtectionFromMagic(CharacterCondition condition)
{
    return condition == CharacterCondition::Dead || condition == CharacterCondition::Eradicated;
}

uint64_t experienceRequiredForNextLevel(uint32_t currentLevel)
{
    return 1000ull * currentLevel * (currentLevel + 1) / 2;
}

int learningPercentForExperienceGain(const Character &member)
{
    const CharacterSkill *pSkill = member.findSkill("Learning");

    if (pSkill == nullptr || pSkill->level == 0)
    {
        return 0;
    }

    switch (pSkill->mastery)
    {
        case SkillMastery::Normal:
            return 9 + static_cast<int>(pSkill->level);

        case SkillMastery::Expert:
            return 9 + 2 * static_cast<int>(pSkill->level);

        case SkillMastery::Master:
            return 9 + 3 * static_cast<int>(pSkill->level);

        case SkillMastery::Grandmaster:
            return 9 + 5 * static_cast<int>(pSkill->level);

        case SkillMastery::None:
        default:
            return 0;
    }
}

bool canReceiveSharedExperience(const Character &member)
{
    return !member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated));
}

bool canReceiveUnconsciousAoeDamage(const Character &member)
{
    return member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated));
}

size_t countActingMembers(const std::vector<Character> &members)
{
    size_t count = 0;

    for (const Character &member : members)
    {
        if (GameMechanics::canAct(member))
        {
            ++count;
        }
    }

    return count;
}

std::optional<size_t> firstActingMemberIndex(const std::vector<Character> &members)
{
    for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
    {
        if (GameMechanics::canAct(members[memberIndex]))
        {
            return memberIndex;
        }
    }

    return std::nullopt;
}

void updateMemberIncapacitatedCondition(Character &member, bool preservationActive)
{
    if (member.health > 0)
    {
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Unconscious)] = 0.0f;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Dead)] = 0.0f;
        return;
    }

    if (member.health + static_cast<int>(member.endurance) >= 1 || preservationActive)
    {
        const size_t unconsciousIndex = static_cast<size_t>(CharacterCondition::Unconscious);
        if (!member.conditions.test(unconsciousIndex))
        {
            member.conditionStartGameMinutes[unconsciousIndex] = 0.0f;
        }
        member.conditions.set(unconsciousIndex);
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Dead)] = 0.0f;
    }
    else
    {
        const size_t deadIndex = static_cast<size_t>(CharacterCondition::Dead);
        if (!member.conditions.test(deadIndex))
        {
            member.conditionStartGameMinutes[deadIndex] = 0.0f;
        }
        member.conditions.set(deadIndex);
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Unconscious)] = 0.0f;
    }
}

bool inventoryItemFitsAt(const InventoryItem &item, uint8_t gridX, uint8_t gridY)
{
    return item.width > 0
        && item.height > 0
        && gridX + item.width <= Character::InventoryWidth
        && gridY + item.height <= Character::InventoryHeight;
}

bool inventoryItemsOverlap(const InventoryItem &left, const InventoryItem &right)
{
    return left.gridX < right.gridX + right.width
        && left.gridX + left.width > right.gridX
        && left.gridY < right.gridY + right.height
        && left.gridY + left.height > right.gridY;
}

uint32_t &equippedItemId(CharacterEquipment &equipment, EquipmentSlot slot)
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

uint32_t equippedItemId(const CharacterEquipment &equipment, EquipmentSlot slot)
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

    return 0;
}

EquippedItemRuntimeState &equippedItemRuntimeState(CharacterEquipmentRuntimeState &equipmentRuntime, EquipmentSlot slot)
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

const EquippedItemRuntimeState &equippedItemRuntimeState(
    const CharacterEquipmentRuntimeState &equipmentRuntime,
    EquipmentSlot slot)
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

InventoryItem makeInventoryItem(
    const ItemTable *pItemTable,
    uint32_t objectDescriptionId,
    ItemGenerationMode mode = ItemGenerationMode::Generic)
{
    if (pItemTable == nullptr)
    {
        InventoryItem item = {};
        item.objectDescriptionId = objectDescriptionId;
        item.quantity = 1;
        return item;
    }

    return ItemGenerator::makeInventoryItem(objectDescriptionId, *pItemTable, mode);
}

InventoryItem makeInventoryItem(
    const ItemTable *pItemTable,
    uint32_t objectDescriptionId,
    const EquippedItemRuntimeState &runtimeState)
{
    InventoryItem item = makeInventoryItem(pItemTable, objectDescriptionId, ItemGenerationMode::Generic);
    item.identified = runtimeState.identified;
    item.broken = runtimeState.broken;
    item.stolen = runtimeState.stolen;
    item.standardEnchantId = runtimeState.standardEnchantId;
    item.standardEnchantPower = runtimeState.standardEnchantPower;
    item.specialEnchantId = runtimeState.specialEnchantId;
    item.artifactId = runtimeState.artifactId;
    item.rarity = runtimeState.rarity;
    item.currentCharges = runtimeState.currentCharges;
    item.maxCharges = runtimeState.maxCharges;
    item.temporaryBonusRemainingSeconds = runtimeState.temporaryBonusRemainingSeconds;

    if (pItemTable != nullptr)
    {
        const ItemDefinition *pItemDefinition = pItemTable->get(objectDescriptionId);

        if (pItemDefinition != nullptr)
        {
            if (item.rarity == ItemRarity::Common)
            {
                item.rarity = pItemDefinition->rarity;
            }

            if (item.artifactId == 0 && ItemRuntime::isRareItem(*pItemDefinition))
            {
                item.artifactId = static_cast<uint16_t>(std::min<uint32_t>(pItemDefinition->itemId, 0xFFFFu));
            }
        }
    }

    return item;
}

uint32_t rosterItemSeed(const RosterEntry &rosterEntry, const RosterEntry::StartingItem &rosterItem, size_t itemIndex)
{
    uint32_t seed = 0x9e3779b9u;
    seed ^= rosterEntry.id + 0x85ebca6bu + (seed << 6) + (seed >> 2);
    seed ^= rosterItem.rawValue + 0xc2b2ae35u + (seed << 6) + (seed >> 2);
    seed ^= static_cast<uint32_t>(itemIndex) + 0x27d4eb2fu + (seed << 6) + (seed >> 2);
    return seed;
}

InventoryItem makeRosterInventoryItem(
    const RosterEntry &rosterEntry,
    const RosterEntry::StartingItem &rosterItem,
    size_t itemIndex,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    InventoryItem item = makeInventoryItem(pItemTable, rosterItem.itemId);
    item.identified = true;

    if (pItemTable == nullptr
        || pStandardEnchantTable == nullptr
        || pSpecialEnchantTable == nullptr
        || rosterItem.enchantmentLevel == 0)
    {
        return item;
    }

    const ItemDefinition *pItemDefinition = pItemTable->get(rosterItem.itemId);

    if (pItemDefinition == nullptr
        || ItemRuntime::isRareItem(*pItemDefinition)
        || !ItemEnchantRuntime::isEnchantable(*pItemDefinition))
    {
        return item;
    }

    const int treasureLevel = std::clamp(static_cast<int>(rosterItem.enchantmentLevel), 1, 6);
    const bool canHaveStandardEnchant = ItemEnchantRuntime::canHaveStandardEnchant(*pItemDefinition);
    const bool canHaveSpecialEnchant = ItemEnchantRuntime::canHaveSpecialEnchant(*pItemDefinition);
    const int standardChance =
        canHaveStandardEnchant ? ItemEnchantRuntime::standardEnchantChance(treasureLevel) : 0;
    const int specialChance =
        canHaveSpecialEnchant ? ItemEnchantRuntime::specialEnchantChance(*pItemDefinition, treasureLevel) : 0;

    if (standardChance <= 0 && specialChance <= 0)
    {
        return item;
    }

    std::mt19937 rng(rosterItemSeed(rosterEntry, rosterItem, itemIndex));
    const int roll = std::uniform_int_distribution<int>(0, 99)(rng);

    if (roll < standardChance)
    {
        const std::optional<uint16_t> standardEnchantId =
            ItemEnchantRuntime::chooseStandardEnchantId(*pItemDefinition, *pStandardEnchantTable, rng);

        if (standardEnchantId)
        {
            item.standardEnchantId = *standardEnchantId;

            const StandardItemEnchantEntry *pEntry = pStandardEnchantTable->get(*standardEnchantId);

            if (pEntry != nullptr)
            {
                item.standardEnchantPower =
                    static_cast<uint16_t>(ItemEnchantRuntime::generateStandardEnchantPower(
                        pEntry->kind,
                        treasureLevel,
                        rng));
            }
        }

        return item;
    }

    if (roll < standardChance + specialChance)
    {
        const std::optional<uint16_t> specialEnchantId =
            ItemEnchantRuntime::chooseSpecialEnchantId(*pItemDefinition, *pSpecialEnchantTable, treasureLevel, rng);

        if (specialEnchantId)
        {
            item.specialEnchantId = *specialEnchantId;
        }
    }

    return item;
}

void copyItemToEquippedRuntimeState(const InventoryItem &item, EquippedItemRuntimeState &runtimeState)
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

void grantRosterInventoryToCharacter(
    Character &character,
    const RosterEntry &rosterEntry,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    const auto tryEquipRosterItem =
        [pItemTable](Character &targetCharacter, const InventoryItem &item) -> bool
        {
            if (pItemTable == nullptr)
            {
                return false;
            }

            const ItemDefinition *pItemDefinition = pItemTable->get(item.objectDescriptionId);

            if (pItemDefinition == nullptr || pItemDefinition->equipStat.empty() || pItemDefinition->equipStat == "0")
            {
                return false;
            }

            const std::optional<CharacterEquipPlan> equipPlan = GameMechanics::resolveCharacterEquipPlan(
                targetCharacter,
                *pItemDefinition,
                pItemTable,
                nullptr,
                std::nullopt,
                false);

            if (!equipPlan || equipPlan->displacedSlot.has_value())
            {
                return false;
            }

            equippedItemId(targetCharacter.equipment, equipPlan->targetSlot) = item.objectDescriptionId;
            EquippedItemRuntimeState &runtimeState =
                equippedItemRuntimeState(targetCharacter.equipmentRuntime, equipPlan->targetSlot);
            copyItemToEquippedRuntimeState(item, runtimeState);
            return true;
        };

    for (size_t itemIndex = 0; itemIndex < rosterEntry.startingItems.size(); ++itemIndex)
    {
        const InventoryItem item = makeRosterInventoryItem(
            rosterEntry,
            rosterEntry.startingItems[itemIndex],
            itemIndex,
            pItemTable,
            pStandardEnchantTable,
            pSpecialEnchantTable);

        if (tryEquipRosterItem(character, item))
        {
            continue;
        }

        character.addInventoryItem(item);
    }
}

InventoryItem *inventoryItemAtMutable(Character &character, uint8_t gridX, uint8_t gridY)
{
    for (InventoryItem &item : character.inventory)
    {
        if (inventoryItemContainsCell(item, gridX, gridY))
        {
            return &item;
        }
    }

    return nullptr;
}

bool identifyInventoryItemInstance(InventoryItem &item, const ItemDefinition &itemDefinition, std::string &statusText)
{
    if (item.identified || !ItemRuntime::requiresIdentification(itemDefinition))
    {
        statusText = "Already identified.";
        return false;
    }

    item.identified = true;
    statusText = "Identified " + ItemRuntime::displayName(item, itemDefinition) + ".";
    return true;
}

bool repairInventoryItemInstance(InventoryItem &item, const ItemDefinition &itemDefinition, std::string &statusText)
{
    if (!item.broken)
    {
        statusText = "Nothing to repair.";
        return false;
    }

    item.broken = false;
    item.identified = true;
    statusText = "Repaired " + ItemRuntime::displayName(item, itemDefinition) + ".";
    return true;
}

bool identifyEquippedItemInstance(EquippedItemRuntimeState &runtimeState, const ItemDefinition &itemDefinition, std::string &statusText)
{
    if (runtimeState.identified || !ItemRuntime::requiresIdentification(itemDefinition))
    {
        statusText = "Already identified.";
        return false;
    }

    runtimeState.identified = true;
    InventoryItem displayItem = {};
    displayItem.identified = runtimeState.identified;
    displayItem.broken = runtimeState.broken;
    displayItem.stolen = runtimeState.stolen;
    displayItem.standardEnchantId = runtimeState.standardEnchantId;
    displayItem.standardEnchantPower = runtimeState.standardEnchantPower;
    displayItem.specialEnchantId = runtimeState.specialEnchantId;
    displayItem.artifactId = runtimeState.artifactId;
    displayItem.rarity = runtimeState.rarity;
    statusText = "Identified " + ItemRuntime::displayName(displayItem, itemDefinition) + ".";
    return true;
}

bool repairEquippedItemInstance(EquippedItemRuntimeState &runtimeState, const ItemDefinition &itemDefinition, std::string &statusText)
{
    if (!runtimeState.broken)
    {
        statusText = "Nothing to repair.";
        return false;
    }

    runtimeState.broken = false;
    runtimeState.identified = true;
    InventoryItem displayItem = {};
    displayItem.identified = runtimeState.identified;
    displayItem.broken = runtimeState.broken;
    displayItem.stolen = runtimeState.stolen;
    displayItem.standardEnchantId = runtimeState.standardEnchantId;
    displayItem.standardEnchantPower = runtimeState.standardEnchantPower;
    displayItem.specialEnchantId = runtimeState.specialEnchantId;
    displayItem.artifactId = runtimeState.artifactId;
    displayItem.rarity = runtimeState.rarity;
    statusText = "Repaired " + ItemRuntime::displayName(displayItem, itemDefinition) + ".";
    return true;
}
}

bool Character::addInventoryItem(const InventoryItem &item)
{
    InventoryItem placedItem = item;
    placedItem.width = std::max<uint8_t>(1, item.width);
    placedItem.height = std::max<uint8_t>(1, item.height);

    const std::optional<std::pair<uint8_t, uint8_t>> placement =
        findFirstFreeInventorySlot(inventory, placedItem.width, placedItem.height);

    if (!placement)
    {
        return false;
    }

    return addInventoryItemAt(placedItem, placement->first, placement->second);
}

bool Character::addInventoryItemAt(const InventoryItem &item, uint8_t gridX, uint8_t gridY)
{
    InventoryItem placedItem = item;
    placedItem.width = std::max<uint8_t>(1, item.width);
    placedItem.height = std::max<uint8_t>(1, item.height);
    placedItem.gridX = gridX;
    placedItem.gridY = gridY;

    if (!inventoryItemFitsAt(placedItem, placedItem.gridX, placedItem.gridY))
    {
        return false;
    }

    for (const InventoryItem &existingItem : inventory)
    {
        if (inventoryItemsOverlap(existingItem, placedItem))
        {
            return false;
        }
    }

    inventory.push_back(placedItem);
    return true;
}

bool Character::removeInventoryItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    for (size_t itemIndex = 0; itemIndex < inventory.size(); ++itemIndex)
    {
        InventoryItem &item = inventory[itemIndex];

        if (item.objectDescriptionId != objectDescriptionId)
        {
            continue;
        }

        if (item.quantity < quantity)
        {
            return false;
        }

        item.quantity -= quantity;

        if (item.quantity == 0)
        {
            inventory.erase(inventory.begin() + itemIndex);
        }

        return true;
    }

    return false;
}

const InventoryItem *Character::inventoryItemAt(uint8_t gridX, uint8_t gridY) const
{
    for (const InventoryItem &item : inventory)
    {
        if (inventoryItemContainsCell(item, gridX, gridY))
        {
            return &item;
        }
    }

    return nullptr;
}

bool Character::takeInventoryItemAt(uint8_t gridX, uint8_t gridY, InventoryItem &item)
{
    for (size_t itemIndex = 0; itemIndex < inventory.size(); ++itemIndex)
    {
        if (!inventoryItemContainsCell(inventory[itemIndex], gridX, gridY))
        {
            continue;
        }

        item = inventory[itemIndex];
        inventory.erase(inventory.begin() + itemIndex);
        return true;
    }

    return false;
}

bool Character::tryPlaceInventoryItemAt(
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY,
    std::optional<InventoryItem> &replacedItem)
{
    replacedItem.reset();

    InventoryItem placedItem = item;
    placedItem.width = std::max<uint8_t>(1, item.width);
    placedItem.height = std::max<uint8_t>(1, item.height);
    placedItem.gridX = gridX;
    placedItem.gridY = gridY;

    if (!inventoryItemFitsAt(placedItem, gridX, gridY))
    {
        return false;
    }

    std::optional<size_t> targetItemIndex;

    for (size_t itemIndex = 0; itemIndex < inventory.size(); ++itemIndex)
    {
        if (inventoryItemContainsCell(inventory[itemIndex], gridX, gridY))
        {
            targetItemIndex = itemIndex;
            break;
        }
    }

    if (!targetItemIndex)
    {
        return addInventoryItemAt(placedItem, gridX, gridY);
    }

    replacedItem = inventory[*targetItemIndex];
    inventory.erase(inventory.begin() + *targetItemIndex);

    const bool placedAtReplacedItemOrigin =
        addInventoryItemAt(placedItem, replacedItem->gridX, replacedItem->gridY);
    const bool placedInFirstFreeSlot =
        !placedAtReplacedItemOrigin && addInventoryItem(placedItem);

    if (!placedAtReplacedItemOrigin && !placedInFirstFreeSlot)
    {
        inventory.push_back(*replacedItem);
        replacedItem.reset();
        return false;
    }

    return true;
}

bool Character::hasSkill(const std::string &skillName) const
{
    const std::string canonicalName = canonicalSkillName(skillName);
    return hasCanonicalSkill(canonicalName);
}

bool Character::hasCanonicalSkill(const std::string &canonicalSkillName) const
{
    return !canonicalSkillName.empty() && skills.contains(canonicalSkillName);
}

const CharacterSkill *Character::findSkill(const std::string &skillName) const
{
    const std::string canonicalName = canonicalSkillName(skillName);

    if (canonicalName.empty())
    {
        return nullptr;
    }

    return findSkillByCanonicalName(canonicalName);
}

const CharacterSkill *Character::findSkillByCanonicalName(const std::string &canonicalSkillName) const
{
    if (canonicalSkillName.empty())
    {
        return nullptr;
    }

    const std::unordered_map<std::string, CharacterSkill>::const_iterator it = skills.find(canonicalSkillName);
    return it != skills.end() ? &it->second : nullptr;
}

CharacterSkill *Character::findSkill(const std::string &skillName)
{
    const std::string canonicalName = canonicalSkillName(skillName);

    if (canonicalName.empty())
    {
        return nullptr;
    }

    return findSkillByCanonicalName(canonicalName);
}

CharacterSkill *Character::findSkillByCanonicalName(const std::string &canonicalSkillName)
{
    if (canonicalSkillName.empty())
    {
        return nullptr;
    }

    const std::unordered_map<std::string, CharacterSkill>::iterator it = skills.find(canonicalSkillName);
    return it != skills.end() ? &it->second : nullptr;
}

bool Character::setSkillMastery(const std::string &skillName, SkillMastery mastery)
{
    CharacterSkill *pSkill = findSkill(skillName);

    if (pSkill == nullptr)
    {
        return false;
    }

    pSkill->mastery = mastery;

    if (canonicalSkillName(skillName) == "DragonAbility")
    {
        learnSpell(spellIdValue(SpellId::Fear));

        if (mastery >= SkillMastery::Expert)
        {
            learnSpell(spellIdValue(SpellId::FlameBlast));
        }

        if (mastery >= SkillMastery::Master)
        {
            learnSpell(spellIdValue(SpellId::Flight));
        }

        if (mastery >= SkillMastery::Grandmaster)
        {
            learnSpell(spellIdValue(SpellId::WingBuffet));
        }
    }

    GameMechanics::refreshCharacterBaseResources(*this);
    return true;
}

bool Character::knowsSpell(uint32_t spellId) const
{
    return spellId != 0 && knownSpellIds.contains(spellId);
}

bool Character::learnSpell(uint32_t spellId)
{
    if (spellId == 0)
    {
        return false;
    }

    return knownSpellIds.insert(spellId).second;
}

bool Character::forgetSpell(uint32_t spellId)
{
    if (spellId == 0)
    {
        return false;
    }

    return knownSpellIds.erase(spellId) > 0;
}

size_t Character::inventoryItemCount() const
{
    return inventory.size();
}

size_t Character::usedInventoryCells() const
{
    size_t usedCells = 0;

    for (const InventoryItem &item : inventory)
    {
        usedCells += static_cast<size_t>(item.width) * item.height;
    }

    return usedCells;
}

size_t Character::inventoryCapacity() const
{
    return static_cast<size_t>(InventoryWidth) * InventoryHeight;
}

PartySeed Party::createDefaultSeed()
{
    PartySeed seed = {};
    seed.gold = 10000;
    seed.food = 7;

    auto grantSeedEquippedItem = [](
        Character &character,
        EquipmentSlot slot,
        uint32_t itemId,
        uint16_t standardEnchantId = 0,
        uint16_t standardEnchantPower = 0,
        uint16_t specialEnchantId = 0)
    {
        ::OpenYAMM::Game::equippedItemId(character.equipment, slot) = itemId;
        EquippedItemRuntimeState &runtimeState = equippedItemRuntimeState(character.equipmentRuntime, slot);
        runtimeState = {};
        runtimeState.identified = true;
        runtimeState.standardEnchantId = standardEnchantId;
        runtimeState.standardEnchantPower = standardEnchantPower;
        runtimeState.specialEnchantId = specialEnchantId;
    };

    auto grantSeedSpellAccess = [](Character &character)
    {
        grantAllMagicSchools(character, 10, SkillMastery::Grandmaster);
        grantAllSpells(character);
    };

    Character cleric = {};
    cleric.name = "Ariel";
    cleric.className = "Cleric";
    cleric.role = "Cleric";
    cleric.portraitTextureName = "PC03-01";
    cleric.portraitPictureId = 2;
    cleric.characterDataId = 3;
    cleric.birthYear = 1148;
    cleric.experience = 10000;
    cleric.level = 5;
    cleric.skillPoints = 30;
    cleric.might = 12;
    cleric.intellect = 20;
    cleric.personality = 20;
    cleric.endurance = 15;
    cleric.speed = 12;
    cleric.accuracy = 12;
    cleric.luck = 14;
    cleric.maxHealth = 100;
    cleric.health = 100;
    cleric.maxSpellPoints = 120;
    cleric.spellPoints = 120;
    grantDefaultEquipmentSkills(cleric);
    grantSeedSkill(cleric, "IdentifyItem", 10, SkillMastery::Grandmaster);
    grantSeedSkill(cleric, "RepairItem", 10, SkillMastery::Grandmaster);
    grantSeedEquippedItem(cleric, EquipmentSlot::MainHand, 79, 0, 0, 16);
    grantSeedEquippedItem(cleric, EquipmentSlot::Armor, 90, 0, 0, 1);
    grantSeedEquippedItem(cleric, EquipmentSlot::Helm, 111, 2, 8);
    grantSeedEquippedItem(cleric, EquipmentSlot::Boots, 135, 0, 0, 72);
    grantSeedEquippedItem(cleric, EquipmentSlot::Amulet, 151, 0, 0, 26);
    grantSeedEquippedItem(cleric, EquipmentSlot::Ring1, 145, 0, 0, 17);
    grantSeedEquippedItem(cleric, EquipmentSlot::Ring2, 146, 9, 12);
    grantSeedInventoryItem(cleric, 137, false, false);
    grantSeedInventoryItem(cleric, 137, true, true);
    grantSeedInventoryItem(cleric, 138, false, false);
    grantSeedInventoryItem(cleric, 138, true, true);
    grantSeedInventoryItem(cleric, 145, false, false);
    grantSeedInventoryItem(cleric, 145, true, true);
    grantSeedInventoryItem(cleric, 401, true, false);
    grantSeedInventoryItem(cleric, 410, true, false);
    grantSeedInventoryItem(cleric, 411, true, false);
    grantSeedInventoryItem(cleric, 400, true, false);
    grantSeedInventoryItem(cleric, 741, true, false);
    grantSeedInventoryItem(cleric, 222, true, false);
    grantSeedInventoryItem(cleric, 223, true, false);
    grantSeedInventoryItem(cleric, 266, true, false);
    grantSeedInventoryItem(cleric, 253, true, false);
    grantSeedInventoryItem(cleric, 656, true, false);
    grantSeedInventoryItem(cleric, 2106, true, false);
    grantSeedInventoryItem(cleric, 2125, true, false);
    grantSeedSpellAccess(cleric);
    grantAllSkills(cleric, 200, SkillMastery::Grandmaster);
    seed.members.push_back(cleric);

    return seed;
}

void Party::reset()
{
    seed(createDefaultSeed());
}

void Party::setItemTable(const ItemTable *pItemTable)
{
    m_pItemTable = pItemTable;
}

void Party::setJournalQuestTable(const JournalQuestTable *pJournalQuestTable)
{
    m_pJournalQuestTable = pJournalQuestTable;
}

void Party::setCharacterDollTable(const CharacterDollTable *pCharacterDollTable)
{
    m_pCharacterDollTable = pCharacterDollTable;

    for (Character &member : m_members)
    {
        applyCharacterIdentityFromDollTable(member, m_pCharacterDollTable);
    }

    for (AdventurersInnMember &member : m_adventurersInnMembers)
    {
        applyCharacterIdentityFromDollTable(member.character, m_pCharacterDollTable);
    }
}

void Party::setItemEnchantTables(
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    m_pStandardItemEnchantTable = pStandardItemEnchantTable;
    m_pSpecialItemEnchantTable = pSpecialItemEnchantTable;
}

const ItemTable *Party::itemTable() const
{
    return m_pItemTable;
}

const JournalQuestTable *Party::journalQuestTable() const
{
    return m_pJournalQuestTable;
}

const StandardItemEnchantTable *Party::standardItemEnchantTable() const
{
    return m_pStandardItemEnchantTable;
}

const SpecialItemEnchantTable *Party::specialItemEnchantTable() const
{
    return m_pSpecialItemEnchantTable;
}

int32_t Party::eventVariableValue(uint16_t variableId) const
{
    const auto iterator = m_eventVariables.find(variableId);
    return iterator != m_eventVariables.end() ? iterator->second : 0;
}

void Party::setEventVariableValue(uint16_t variableId, int32_t value)
{
    if (value == 0)
    {
        m_eventVariables.erase(variableId);
        return;
    }

    m_eventVariables[variableId] = value;
}

void Party::addEventVariableValue(uint16_t variableId, int32_t value)
{
    if (value == 0)
    {
        return;
    }

    setEventVariableValue(variableId, eventVariableValue(variableId) + value);
}

void Party::subtractEventVariableValue(uint16_t variableId, int32_t value)
{
    if (value == 0)
    {
        return;
    }

    setEventVariableValue(variableId, eventVariableValue(variableId) - value);
}

int Party::fineGold() const
{
    return m_fineGold;
}

void Party::addFineGold(int amount)
{
    if (amount == 0)
    {
        return;
    }

    m_fineGold = std::clamp(m_fineGold + amount, 0, 4000000);
}

void Party::clearFineGold()
{
    m_fineGold = 0;
}

int32_t Party::continentReputation(uint32_t continentId) const
{
    const std::unordered_map<uint32_t, int32_t>::const_iterator it = m_continentReputations.find(continentId);
    return it != m_continentReputations.end() ? it->second : 0;
}

void Party::setContinentReputation(uint32_t continentId, int32_t value)
{
    if (continentId == 0)
    {
        return;
    }

    m_continentReputations[continentId] = clampReputation(value);
}

void Party::setClassSkillTable(const ClassSkillTable *pClassSkillTable)
{
    m_pClassSkillTable = pClassSkillTable;

    for (Character &member : m_members)
    {
        member.className = normalizePartyClassName(
            member.className.empty() ? member.role : member.className,
            m_pClassSkillTable);

        if (member.skills.empty())
        {
            applyDefaultStartingSkills(member);
        }

        if (m_pClassMultiplierTable != nullptr)
        {
            GameMechanics::refreshCharacterBaseResources(member, false, m_pClassMultiplierTable);
        }

        initializePortraitRuntimeState(member);
    }

    for (AdventurersInnMember &member : m_adventurersInnMembers)
    {
        member.character.className = normalizePartyClassName(
            member.character.className.empty() ? member.character.role : member.character.className,
            m_pClassSkillTable);

        if (member.character.skills.empty())
        {
            applyDefaultStartingSkills(member.character);
        }

        initializePortraitRuntimeState(member.character);
        member.portraitPictureId = resolveAdventurersInnPortraitPictureId(member.character, member.portraitPictureId);
    }
}

const ClassSkillTable *Party::classSkillTable() const
{
    return m_pClassSkillTable;
}

void Party::setClassMultiplierTable(const ClassMultiplierTable *pClassMultiplierTable)
{
    m_pClassMultiplierTable = pClassMultiplierTable;
}

const ClassMultiplierTable *Party::classMultiplierTable() const
{
    return m_pClassMultiplierTable;
}

Party::Snapshot Party::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.members = m_members;
    snapshot.adventurersInnMembers = m_adventurersInnMembers;
    snapshot.activeMemberIndex = m_activeMemberIndex;
    snapshot.partyBuffs = m_partyBuffs;
    snapshot.characterBuffs = m_characterBuffs;
    snapshot.gold = m_gold;
    snapshot.bankGold = m_bankGold;
    snapshot.food = m_food;
    snapshot.fineGold = m_fineGold;
    snapshot.waterDamageTicks = m_waterDamageTicks;
    snapshot.burningDamageTicks = m_burningDamageTicks;
    snapshot.splashCount = m_splashCount;
    snapshot.landingSoundCount = m_landingSoundCount;
    snapshot.hardLandingSoundCount = m_hardLandingSoundCount;
    snapshot.monsterTargetSelectionCounter = m_monsterTargetSelectionCounter;
    snapshot.houseStockSeed = m_houseStockSeed;
    snapshot.lastFallDamageDistance = m_lastFallDamageDistance;
    snapshot.foundArtifactItems = m_foundArtifactItems;
    snapshot.arcomageWonHouseIds = m_arcomageWonHouseIds;
    snapshot.arcomageWinCount = m_arcomageWinCount;
    snapshot.arcomageLossCount = m_arcomageLossCount;
    snapshot.everOwnedItemIds = m_everOwnedItemIds;
    snapshot.continentReputations = m_continentReputations;
    snapshot.questBits = m_questBits;
    snapshot.eventVariables = m_eventVariables;
    snapshot.npcTopicOverrides = m_npcTopicOverrides;
    snapshot.npcGroupNews = m_npcGroupNews;
    snapshot.npcGreetingOverrides = m_npcGreetingOverrides;
    snapshot.npcGreetingDisplayCounts = m_npcGreetingDisplayCounts;
    snapshot.npcHouseOverrides = m_npcHouseOverrides;
    snapshot.npcItemOverrides = m_npcItemOverrides;
    snapshot.unavailableNpcIds = m_unavailableNpcIds;
    snapshot.hiredNpcFollowers = m_hiredNpcFollowers;

    for (const auto &[houseId, state] : m_houseStockStates)
    {
        (void)houseId;
        snapshot.houseStockStates.push_back(state);
    }

    return snapshot;
}

void Party::restoreSnapshot(const Snapshot &snapshot)
{
    m_members = snapshot.members;
    m_adventurersInnMembers = snapshot.adventurersInnMembers;
    m_activeMemberIndex = snapshot.activeMemberIndex;
    m_partyBuffs = snapshot.partyBuffs;
    m_characterBuffs = snapshot.characterBuffs;
    m_gold = snapshot.gold;
    m_bankGold = snapshot.bankGold;
    m_food = snapshot.food;
    m_fineGold = snapshot.fineGold;
    m_waterDamageTicks = snapshot.waterDamageTicks;
    m_burningDamageTicks = snapshot.burningDamageTicks;
    m_splashCount = snapshot.splashCount;
    m_landingSoundCount = snapshot.landingSoundCount;
    m_hardLandingSoundCount = snapshot.hardLandingSoundCount;
    m_monsterTargetSelectionCounter = snapshot.monsterTargetSelectionCounter;
    m_houseStockSeed = snapshot.houseStockSeed;
    m_lastFallDamageDistance = snapshot.lastFallDamageDistance;
    m_foundArtifactItems = snapshot.foundArtifactItems;
    m_arcomageWonHouseIds = snapshot.arcomageWonHouseIds;
    m_arcomageWinCount = snapshot.arcomageWinCount;
    m_arcomageLossCount = snapshot.arcomageLossCount;
    m_everOwnedItemIds = snapshot.everOwnedItemIds;
    m_continentReputations = snapshot.continentReputations;
    m_questBits = snapshot.questBits;
    m_eventVariables = snapshot.eventVariables;
    m_npcTopicOverrides = snapshot.npcTopicOverrides;
    m_npcGroupNews = snapshot.npcGroupNews;
    m_npcGreetingOverrides = snapshot.npcGreetingOverrides;
    m_npcGreetingDisplayCounts = snapshot.npcGreetingDisplayCounts;
    m_npcHouseOverrides = snapshot.npcHouseOverrides;
    m_npcItemOverrides = snapshot.npcItemOverrides;
    m_unavailableNpcIds = snapshot.unavailableNpcIds;
    m_hiredNpcFollowers = snapshot.hiredNpcFollowers;
    m_houseStockStates.clear();

    for (const HouseStockState &state : snapshot.houseStockStates)
    {
        m_houseStockStates[state.houseId] = state;
    }

    for (Character &member : m_members)
    {
        applyCharacterIdentityFromDollTable(member, m_pCharacterDollTable);
        initializePortraitRuntimeState(member);
    }

    for (AdventurersInnMember &member : m_adventurersInnMembers)
    {
        applyCharacterIdentityFromDollTable(member.character, m_pCharacterDollTable);
        initializePortraitRuntimeState(member.character);
        member.portraitPictureId = resolveAdventurersInnPortraitPictureId(member.character, member.portraitPictureId);
    }

    if (m_members.empty())
    {
        m_activeMemberIndex = 0;
    }
    else
    {
        m_activeMemberIndex = std::min(m_activeMemberIndex, m_members.size() - 1);
    }

    m_lastStatus.clear();
    m_heldItemIdForQueries = 0;
    m_pendingAudioRequests.clear();
    recordEverOwnedItemsFromCurrentState();
    rebuildMagicalBonusesFromBuffs();
}

void Party::seed(const PartySeed &seed)
{
    m_members = seed.members;
    m_adventurersInnMembers.clear();
    m_activeMemberIndex = 0;
    m_partyBuffs = {};
    m_characterBuffs = {};
    m_gold = std::max(0, seed.gold);
    m_bankGold = 0;
    m_food = std::max(0, seed.food);
    m_fineGold = 0;
    m_monsterTargetSelectionCounter = 0;
    m_houseStockSeed = generateHouseStockSeed();
    m_foundArtifactItems.clear();
    m_everOwnedItemIds.clear();
    m_continentReputations.clear();
    m_questBits.clear();
    m_eventVariables.clear();
    m_npcTopicOverrides.clear();
    m_npcGroupNews.clear();
    m_npcGreetingOverrides.clear();
    m_npcGreetingDisplayCounts.clear();
    m_npcHouseOverrides.clear();
    m_npcItemOverrides.clear();
    m_unavailableNpcIds.clear();
    m_hiredNpcFollowers.clear();
    m_houseStockStates.clear();

    for (Character &member : m_members)
    {
        const std::vector<InventoryItem> seededInventory = member.inventory;
        applyCharacterIdentityFromDollTable(member, m_pCharacterDollTable);
        member.className = canonicalClassName(member.className.empty() ? member.role : member.className);
        member.role = normalizeRoleName(member.className);
        member.level = std::max<uint32_t>(1, member.level);
        member.skillPoints = std::max<uint32_t>(0u, member.skillPoints);
        member.maxHealth = std::max(1, member.maxHealth);
        member.health = std::clamp(member.health, 0, member.maxHealth);
        member.maxSpellPoints = std::max(0, member.maxSpellPoints);
        member.spellPoints = std::clamp(member.spellPoints, 0, member.maxSpellPoints);
        member.inventory.clear();

        for (const InventoryItem &seededItem : seededInventory)
        {
            InventoryItem resolvedItem = makeInventoryItem(m_pItemTable, seededItem.objectDescriptionId);
            resolvedItem.quantity = seededItem.quantity;
            resolvedItem.gridX = seededItem.gridX;
            resolvedItem.gridY = seededItem.gridY;
            resolvedItem.identified = seededItem.identified;
            resolvedItem.broken = seededItem.broken;
            resolvedItem.stolen = seededItem.stolen;
            resolvedItem.standardEnchantId = seededItem.standardEnchantId;
            resolvedItem.standardEnchantPower = seededItem.standardEnchantPower;
            resolvedItem.specialEnchantId = seededItem.specialEnchantId;
            resolvedItem.artifactId = seededItem.artifactId;
            resolvedItem.rarity = seededItem.rarity;
            resolvedItem.temporaryBonusRemainingSeconds = seededItem.temporaryBonusRemainingSeconds;

            if (seededItem.currentCharges != 0 || seededItem.maxCharges != 0)
            {
                resolvedItem.currentCharges = seededItem.currentCharges;
                resolvedItem.maxCharges = seededItem.maxCharges;
            }

            resolvedItem.width = resolveInventoryWidth(seededItem.objectDescriptionId);
            resolvedItem.height = resolveInventoryHeight(seededItem.objectDescriptionId);

            const bool placed = (seededItem.width > 0 && seededItem.height > 0)
                ? member.addInventoryItemAt(resolvedItem, seededItem.gridX, seededItem.gridY)
                : member.addInventoryItem(resolvedItem);

            if (!placed)
            {
                continue;
            }

            markArtifactItemFoundIfRelevant(resolvedItem);
            recordEverOwnedItemIfRelevant(resolvedItem);
        }

        if (member.skills.empty())
        {
            applyDefaultStartingSkills(member);
        }

        for (EquipmentSlot slot : {
                 EquipmentSlot::OffHand,
                 EquipmentSlot::MainHand,
                 EquipmentSlot::Bow,
                 EquipmentSlot::Armor,
                 EquipmentSlot::Helm,
                 EquipmentSlot::Belt,
                 EquipmentSlot::Cloak,
                 EquipmentSlot::Gauntlets,
                 EquipmentSlot::Boots,
                 EquipmentSlot::Amulet,
                 EquipmentSlot::Ring1,
                 EquipmentSlot::Ring2,
                 EquipmentSlot::Ring3,
                 EquipmentSlot::Ring4,
                 EquipmentSlot::Ring5,
                 EquipmentSlot::Ring6})
        {
            const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(member.equipment, slot);

            if (itemId == 0)
            {
                continue;
            }

            markArtifactItemFoundIfRelevant(
                makeInventoryItem(m_pItemTable, itemId, equippedItemRuntimeState(member.equipmentRuntime, slot)));
        }

        if (m_pClassMultiplierTable != nullptr)
        {
            GameMechanics::refreshCharacterBaseResources(member, false, m_pClassMultiplierTable);
        }

        initializePortraitRuntimeState(member);
    }

    if (m_members.empty())
    {
        Character fallbackMember = {};
        fallbackMember.name = "Adventurer";
        fallbackMember.className = "Knight";
        fallbackMember.role = "Knight";
        fallbackMember.level = 1;
        fallbackMember.skillPoints = 0;
        fallbackMember.maxHealth = 100;
        fallbackMember.health = 100;
        m_members.push_back(fallbackMember);
    }

    for (const InventoryItem &item : seed.inventory)
    {
        grantItem(item.objectDescriptionId, std::max<uint32_t>(1, item.quantity));
    }

    m_waterDamageTicks = 0;
    m_burningDamageTicks = 0;
    m_splashCount = 0;
    m_landingSoundCount = 0;
    m_hardLandingSoundCount = 0;
    m_lastFallDamageDistance = 0.0f;
    m_lastStatus.clear();
    m_heldItemIdForQueries = 0;
    m_pendingAudioRequests.clear();
    recordEverOwnedItemsFromCurrentState();
    rebuildMagicalBonusesFromBuffs();
}

void Party::applyMovementEffects(const OutdoorMovementEffects &effects)
{
    for (uint32_t i = 0; i < effects.waterDamageTicks; ++i)
    {
        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            if (m_members[memberIndex].waterWalking)
            {
                continue;
            }

            const int damage = std::max(1, m_members[memberIndex].maxHealth / 10);
            applyDamageToMember(memberIndex, damage, "");
        }

        m_waterDamageTicks += 1;
        m_lastStatus = "water damage";
    }

    for (uint32_t i = 0; i < effects.burningDamageTicks; ++i)
    {
        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            const int damage = std::max(1, m_members[memberIndex].maxHealth / 10);
            applyDamageToMember(memberIndex, damage, "");
        }

        m_burningDamageTicks += 1;
        m_lastStatus = "burning damage";
    }

    if (effects.maxFallDamageDistance > 0.0f)
    {
        m_lastFallDamageDistance = std::max(m_lastFallDamageDistance, effects.maxFallDamageDistance);

        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            if (m_members[memberIndex].featherFalling)
            {
                continue;
            }

            const int fallDistance = std::max(0, static_cast<int>(effects.maxFallDamageDistance));
            const int healthFactor = std::max(0, m_members[memberIndex].maxHealth) / 10;
            const int damage = static_cast<int>(
                std::min<int64_t>(
                    std::numeric_limits<int>::max(),
                    static_cast<int64_t>(fallDistance) * healthFactor / 256));
            applyDamageToMember(memberIndex, damage, "falling");
        }

        m_lastStatus = "fall damage";
    }

    if (effects.playSplashSound)
    {
        m_splashCount += 1;
        m_lastStatus = "splash";
        queueSound(SoundId::Splash);
    }

    if (effects.playLandingSound)
    {
        m_landingSoundCount += 1;
        m_lastStatus = "landing";
    }

    if (effects.playHardLandingSound)
    {
        m_hardLandingSoundCount += 1;
        m_lastStatus = "hard landing";
    }
}

void Party::applyEventRuntimeState(const EventRuntimeState &runtimeState, bool grantItemsToInventory)
{
    for (const InventoryItem &item : runtimeState.grantedItems)
    {
        if (grantItemsToInventory)
        {
            size_t recipientMemberIndex = 0;
            if (tryGrantInventoryItem(item, &recipientMemberIndex))
            {
                queueSound(SoundId::Gold);
                GAMEPLAY_DEBUG_TRACE(
                    "item_received destination=inventory source=event item_id="
                    + std::to_string(item.objectDescriptionId)
                    + gameplayDebugTraceItemSummary(item.objectDescriptionId, m_pItemTable)
                    + " member_index=" + std::to_string(recipientMemberIndex));
            }
        }
        else if (item.objectDescriptionId != 0)
        {
            markArtifactItemFoundIfRelevant(item);
        }

        m_lastStatus = "item granted";
    }

    for (uint32_t itemId : runtimeState.grantedItemIds)
    {
        if (grantItemsToInventory)
        {
            if (tryGrantItem(itemId))
            {
                queueSound(SoundId::Gold);
                GAMEPLAY_DEBUG_TRACE(
                    "item_received destination=inventory source=event item_id="
                    + std::to_string(itemId)
                    + gameplayDebugTraceItemSummary(itemId, m_pItemTable));
            }
        }
        else if (itemId != 0)
        {
            markArtifactItemFoundIfRelevant(makeInventoryItem(m_pItemTable, itemId));
        }

        m_lastStatus = "item granted";
    }

    for (uint32_t itemId : runtimeState.removedItemIds)
    {
        if (removeItem(itemId))
        {
            m_lastStatus = "item removed";
        }
    }

    for (uint32_t awardId : runtimeState.grantedAwardIds)
    {
        addAward(awardId);
        m_lastStatus = "award granted";
    }

    for (uint32_t awardId : runtimeState.removedAwardIds)
    {
        removeAward(awardId);
        m_lastStatus = "award removed";
    }

    for (const HiredNpcFollower &follower : runtimeState.hiredNpcFollowers)
    {
        if (follower.npcId == 0)
        {
            continue;
        }

        const auto followerIt = std::find_if(
            m_hiredNpcFollowers.begin(),
            m_hiredNpcFollowers.end(),
            [&follower](const HiredNpcFollower &existingFollower)
            {
                return existingFollower.npcId == follower.npcId;
            });

        if (followerIt == m_hiredNpcFollowers.end())
        {
            m_hiredNpcFollowers.push_back(follower);
        }
        else
        {
            *followerIt = follower;
        }
    }

    for (const HiredNpcFollower &follower : m_hiredNpcFollowers)
    {
        if (follower.npcId != 0)
        {
            m_unavailableNpcIds.insert(follower.npcId);
        }
    }
}

bool Party::applyDamageToActiveMember(int damage, const std::string &status)
{
    if (damage <= 0 || m_members.empty())
    {
        return false;
    }

    size_t targetIndex = std::min(m_activeMemberIndex, m_members.size() - 1);

    if (m_members[targetIndex].health <= 0)
    {
        bool foundLivingMember = false;

        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            if (m_members[memberIndex].health > 0)
            {
                targetIndex = memberIndex;
                foundLivingMember = true;
                break;
            }
        }

        if (!foundLivingMember)
        {
            return false;
        }
    }

    return applyDamageToMember(targetIndex, damage, status);
}

bool Party::applyPotionExplosionToMember(size_t memberIndex, uint8_t damageLevel)
{
    if (memberIndex >= m_members.size() || damageLevel == 0)
    {
        return false;
    }

    if (damageLevel >= 4)
    {
        applyMemberCondition(memberIndex, CharacterCondition::Eradicated);
        breakPotionExplosionItems(m_members[memberIndex], 0);
        return true;
    }

    bool applied = applyDamageToMember(memberIndex, potionExplosionDamage(damageLevel), "");

    if (damageLevel == 2)
    {
        breakPotionExplosionItems(m_members[memberIndex], 1);
        applied = true;
    }
    else if (damageLevel == 3)
    {
        breakPotionExplosionItems(m_members[memberIndex], 5);
        applied = true;
    }

    return applied;
}

void Party::setDebugDamageImmune(bool enabled)
{
    m_debugDamageImmune = enabled;
}

void Party::setDebugUnlimitedMana(bool enabled)
{
    m_debugUnlimitedMana = enabled;
}

bool Party::applyDamageToMember(
    size_t memberIndex,
    int damage,
    const std::string &status,
    bool allowUnconscious)
{
    if (damage <= 0 || memberIndex >= m_members.size())
    {
        return false;
    }

    Character &member = m_members[memberIndex];
    const int previousHealth = member.health;
    const size_t actingMembersBeforeDamage = countActingMembers(m_members);

    if (member.health <= 0 && (!allowUnconscious || !canReceiveUnconsciousAoeDamage(member)))
    {
        return false;
    }

    if (!m_debugDamageImmune)
    {
        member.health -= damage;
        const bool preservationActive =
            m_characterBuffs[memberIndex][static_cast<size_t>(CharacterBuffId::Preservation)].active();
        updateMemberIncapacitatedCondition(member, preservationActive);

        if (preservationActive && previousHealth > 0 && member.health <= 0)
        {
            queueSpeech(memberIndex, SpeechId::CheatedDeath);
        }
    }

    const bool crossedMajorDamageThreshold =
        member.maxHealth > 0
        && previousHealth > member.maxHealth / 4
        && member.health > 0
        && member.health <= member.maxHealth / 4;

    if (status == "falling")
    {
        queueSpeech(memberIndex, SpeechId::Falling);
    }
    else if (GameMechanics::canAct(member))
    {
        queueSpeech(memberIndex, SpeechId::DamageMinor);
    }

    if (member.health <= 0)
    {
        queueSpeech(memberIndex, SpeechId::Dying);
    }
    else if (crossedMajorDamageThreshold)
    {
        queueSpeech(memberIndex, SpeechId::DamageMajor);
    }

    if (actingMembersBeforeDamage > 1 && countActingMembers(m_members) == 1)
    {
        const std::optional<size_t> remainingMemberIndex = firstActingMemberIndex(m_members);

        if (remainingMemberIndex)
        {
            queueSpeech(*remainingMemberIndex, SpeechId::LastPersonStanding);
        }
    }

    if (!status.empty())
    {
        m_lastStatus = status;
    }

    return true;
}

bool Party::applyDamageToAllLivingMembers(int damage, const std::string &status)
{
    if (damage <= 0 || m_members.empty())
    {
        return false;
    }

    bool applied = false;
    size_t appliedCount = 0;

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        if (m_members[memberIndex].health <= 0 && !canReceiveUnconsciousAoeDamage(m_members[memberIndex]))
        {
            continue;
        }

        if (applyDamageToMember(memberIndex, damage, "", true))
        {
            applied = true;
            ++appliedCount;
        }
    }

    if (appliedCount > 1)
    {
        queueSpeech(activeMemberIndex(), SpeechId::DamagedParty);
    }

    if (applied && !status.empty())
    {
        m_lastStatus = status;
    }

    return applied;
}

uint32_t Party::addExperienceToMember(size_t memberIndex, int64_t amount)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return 0;
    }

    const int64_t clampedExperience = std::clamp<int64_t>(
        static_cast<int64_t>(pMember->experience) + amount,
        0,
        static_cast<int64_t>(OeMaxCharacterExperience));
    pMember->experience = static_cast<uint32_t>(clampedExperience);
    return pMember->experience;
}

uint32_t Party::setMemberExperience(size_t memberIndex, uint32_t experience)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return 0;
    }

    pMember->experience = std::min(experience, OeMaxCharacterExperience);
    return pMember->experience;
}

uint32_t Party::grantSharedExperience(uint32_t totalExperience)
{
    if (totalExperience == 0)
    {
        return 0;
    }

    size_t eligibleMemberCount = 0;

    for (const Character &member : m_members)
    {
        if (canReceiveSharedExperience(member))
        {
            ++eligibleMemberCount;
        }
    }

    if (eligibleMemberCount == 0)
    {
        return 0;
    }

    const uint32_t experiencePerEligibleMember = totalExperience / eligibleMemberCount;
    uint32_t totalGrantedExperience = 0;

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        const Character &member = m_members[memberIndex];

        if (!canReceiveSharedExperience(member))
        {
            continue;
        }

        const int learningPercent = learningPercentForExperienceGain(member);
        const uint32_t grantedExperience =
            experiencePerEligibleMember
            + experiencePerEligibleMember * std::max(0, learningPercent) / 100;
        addExperienceToMember(memberIndex, grantedExperience);
        totalGrantedExperience += grantedExperience;
    }

    return totalGrantedExperience;
}

std::optional<size_t> Party::chooseMonsterAttackTarget(uint32_t attackPreferences, uint32_t seedHint)
{
    std::vector<size_t> candidates;
    candidates.reserve(m_members.size());

    static constexpr std::array<uint32_t, 15> PreferenceFlags = {{
        AttackPreferenceKnight,
        AttackPreferencePaladin,
        AttackPreferenceArcher,
        AttackPreferenceDruid,
        AttackPreferenceCleric,
        AttackPreferenceSorcerer,
        AttackPreferenceRanger,
        AttackPreferenceThief,
        AttackPreferenceMonk,
        AttackPreferenceMale,
        AttackPreferenceFemale,
        AttackPreferenceHuman,
        AttackPreferenceElf,
        AttackPreferenceDwarf,
        AttackPreferenceGoblin,
    }};

    if (attackPreferences != 0)
    {
        for (uint32_t preferenceFlag : PreferenceFlags)
        {
            if ((attackPreferences & preferenceFlag) == 0)
            {
                continue;
            }

            for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
            {
                const Character &member = m_members[memberIndex];

                if (!isValidMonsterAttackTarget(member) || !matchesMonsterAttackPreference(member, preferenceFlag))
                {
                    continue;
                }

                candidates.push_back(memberIndex);
            }
        }
    }

    if (candidates.empty())
    {
        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            if (isValidMonsterAttackTarget(m_members[memberIndex]))
            {
                candidates.push_back(memberIndex);
            }
        }
    }

    if (candidates.empty())
    {
        return std::nullopt;
    }

    const uint32_t selectionSeed =
        seedHint * 1103515245u + m_monsterTargetSelectionCounter * 2654435761u + 12345u;
    ++m_monsterTargetSelectionCounter;
    return candidates[selectionSeed % candidates.size()];
}

void Party::addGold(int amount)
{
    const int previousGold = m_gold;
    m_gold = std::max(0, m_gold + amount);

    if (m_gold != previousGold)
    {
        queueSound(SoundId::Gold);
    }
}

void Party::addFood(int amount)
{
    m_food = std::max(0, m_food + amount);

    if (amount > 0)
    {
        queueSound(SoundId::Eat);
    }
}

void Party::requestSound(SoundId soundId)
{
    queueSound(soundId);
}

void Party::requestDamageImpactSoundForMember(size_t memberIndex)
{
    queueSound(resolveDamageImpactSoundForMember(memberIndex));
}

void Party::requestSpeech(size_t memberIndex, SpeechId speechId)
{
    queueSpeech(memberIndex, speechId);
}

bool Party::tryGrantItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    std::vector<Character> testMembers = m_members;

    if (testMembers.empty())
    {
        m_lastStatus = "inventory full";
        return false;
    }

    for (uint32_t itemCount = 0; itemCount < quantity; ++itemCount)
    {
        InventoryItem item = makeInventoryItem(m_pItemTable, objectDescriptionId);

        bool added = false;

        const size_t firstIndex = std::min(activeMemberIndex(), testMembers.size() - 1);

        for (size_t offset = 0; offset < testMembers.size(); ++offset)
        {
            Character &member = testMembers[(firstIndex + offset) % testMembers.size()];

            if (member.addInventoryItem(item))
            {
                added = true;
                break;
            }
        }

        if (!added)
        {
            m_lastStatus = "inventory full";
            return false;
        }
    }

    m_members = std::move(testMembers);
    const InventoryItem recordedItem = makeInventoryItem(m_pItemTable, objectDescriptionId);
    markArtifactItemFoundIfRelevant(recordedItem);
    recordEverOwnedItemIfRelevant(recordedItem);
    return true;
}

bool Party::tryGrantInventoryItem(const InventoryItem &item, size_t *pRecipientMemberIndex)
{
    return tryGrantInventoryItemStartingAt(activeMemberIndex(), item, pRecipientMemberIndex);
}

bool Party::tryGrantInventoryItemStartingAt(
    size_t firstMemberIndex,
    const InventoryItem &item,
    size_t *pRecipientMemberIndex)
{
    if (item.objectDescriptionId == 0 || item.quantity == 0)
    {
        return false;
    }

    std::vector<Character> testMembers = m_members;

    if (testMembers.empty())
    {
        m_lastStatus = "inventory full";
        return false;
    }

    const size_t firstIndex = std::min(firstMemberIndex, testMembers.size() - 1);

    for (size_t offset = 0; offset < testMembers.size(); ++offset)
    {
        const size_t memberIndex = (firstIndex + offset) % testMembers.size();
        Character &member = testMembers[memberIndex];

        if (member.addInventoryItem(item))
        {
            m_members = std::move(testMembers);
            markArtifactItemFoundIfRelevant(item);
            recordEverOwnedItemIfRelevant(item);

            if (pRecipientMemberIndex != nullptr)
            {
                *pRecipientMemberIndex = memberIndex;
            }

            return true;
        }
    }

    m_lastStatus = "inventory full";
    return false;
}

void Party::grantItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (!tryGrantItem(objectDescriptionId, quantity))
    {
        return;
    }
}

bool Party::removeItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    uint32_t availableCount = 0;

    for (const Character &member : m_members)
    {
        for (const InventoryItem &item : member.inventory)
        {
            if (item.objectDescriptionId == objectDescriptionId)
            {
                availableCount += item.quantity;
            }
        }
    }

    if (availableCount < quantity)
    {
        return false;
    }

    uint32_t removedCount = 0;

    for (Character &member : m_members)
    {
        while (removedCount < quantity && member.removeInventoryItem(objectDescriptionId))
        {
            removedCount += 1;
        }
    }

    return removedCount == quantity;
}

int Party::effectiveMaximumHealth(const Character &member)
{
    return GameMechanics::calculateEffectiveCharacterMaxHealth(member);
}

int Party::effectiveMaximumSpellPoints(const Character &member)
{
    return GameMechanics::calculateEffectiveCharacterMaxSpellPoints(member);
}

bool Party::needsHealing() const
{
    for (const Character &member : m_members)
    {
        if (characterNeedsTempleHealing(member))
        {
            return true;
        }
    }

    return false;
}

bool Party::activeMemberNeedsHealing() const
{
    const Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    return characterNeedsTempleHealing(*pMember);
}

void Party::restoreAll()
{
    restAndHealAll();
}

void Party::reviveAndRestoreAll()
{
    m_partyBuffs = {};
    m_characterBuffs = {};
    rebuildMagicalBonusesFromBuffs();

    for (Character &member : m_members)
    {
        clearTemporaryEventBonuses(member);
        member.conditions.reset();
        member.conditionStartGameMinutes.fill(0.0f);
        member.recoverySecondsRemaining = 0.0f;
        member.healthRegenAccumulator = 0.0f;
        member.spellRegenAccumulator = 0.0f;
        member.health = currentMaximumHealth(member);
        member.spellPoints = currentMaximumSpellPoints(member);
    }

    if (!canSelectMemberInGameplay(m_activeMemberIndex))
    {
        m_activeMemberIndex = 0;
        switchToNextReadyMember();
    }
}

void Party::restAndHealAll()
{
    m_partyBuffs = {};
    m_characterBuffs = {};
    rebuildMagicalBonusesFromBuffs();

    for (Character &member : m_members)
    {
        clearTemporaryEventBonuses(member);

        if (member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
        {
            continue;
        }

        member.conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Unconscious)] = 0.0f;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Drunk));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Drunk)] = 0.0f;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Fear));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Fear)] = 0.0f;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Asleep));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Asleep)] = 0.0f;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Weak));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Weak)] = 0.0f;
        member.recoverySecondsRemaining = 0.0f;

        member.health = currentMaximumHealth(member);
        member.spellPoints = currentMaximumSpellPoints(member);

        if (member.conditions.test(static_cast<size_t>(CharacterCondition::Zombie)))
        {
            member.health = std::max(1, member.health / 2);
            member.spellPoints = 0;
        }
        else if (member.conditions.test(static_cast<size_t>(CharacterCondition::PoisonSevere))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::DiseaseSevere)))
        {
            member.health = std::max(1, member.health / 4);
            member.spellPoints /= 4;
        }
        else if (member.conditions.test(static_cast<size_t>(CharacterCondition::PoisonMedium))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::DiseaseMedium)))
        {
            member.health = std::max(1, member.health / 3);
            member.spellPoints /= 3;
        }
        else if (member.conditions.test(static_cast<size_t>(CharacterCondition::PoisonWeak))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::DiseaseWeak)))
        {
            member.health = std::max(1, member.health / 2);
            member.spellPoints /= 2;
        }

        if (member.conditions.test(static_cast<size_t>(CharacterCondition::Insane)))
        {
            member.spellPoints = 0;
        }
    }
}

void Party::restoreActiveMember()
{
    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return;
    }

    pMember->health = effectiveMaximumHealth(*pMember);
    pMember->spellPoints = effectiveMaximumSpellPoints(*pMember);
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Unconscious)] = 0.0f;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Dead)] = 0.0f;
}

bool Party::trainLeader(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned)
{
    newLevel = 0;
    skillPointsEarned = 0;

    if (m_members.empty())
    {
        return false;
    }

    Character &leader = m_members.front();

    if (maxLevel > 0 && leader.level >= maxLevel)
    {
        return false;
    }

    if (leader.experience < experienceRequiredForNextLevel(leader.level))
    {
        return false;
    }

    leader.level += 1;
    skillPointsEarned = 5 + leader.level / 10;
    leader.skillPoints += skillPointsEarned;
    GameMechanics::refreshCharacterBaseResources(leader, true, m_pClassMultiplierTable);
    newLevel = leader.level;
    return true;
}

bool Party::trainActiveMember(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned)
{
    newLevel = 0;
    skillPointsEarned = 0;

    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    if (maxLevel > 0 && pMember->level >= maxLevel)
    {
        return false;
    }

    if (pMember->experience < experienceRequiredForNextLevel(pMember->level))
    {
        return false;
    }

    pMember->level += 1;
    skillPointsEarned = 5 + pMember->level / 10;
    pMember->skillPoints += skillPointsEarned;
    GameMechanics::refreshCharacterBaseResources(*pMember, true, m_pClassMultiplierTable);
    newLevel = pMember->level;
    return true;
}

bool Party::canActiveMemberLearnSkill(const std::string &skillName) const
{
    const Character *pMember = activeMember();
    const std::string canonicalSkill = canonicalSkillName(skillName);

    if (pMember == nullptr || canonicalSkill.empty() || m_pClassSkillTable == nullptr || pMember->hasSkill(canonicalSkill))
    {
        return false;
    }

    return m_pClassSkillTable->getEffectiveCap(pMember->className, pMember->raceId, canonicalSkill)
        != SkillMastery::None;
}

bool Party::learnActiveMemberSkill(const std::string &skillName)
{
    if (!canActiveMemberLearnSkill(skillName))
    {
        return false;
    }

    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    CharacterSkill skill = {};
    skill.name = canonicalSkillName(skillName);
    skill.level = 1;
    skill.mastery = SkillMastery::Normal;
    pMember->skills[skill.name] = skill;
    GameMechanics::refreshCharacterBaseResources(*pMember, false, m_pClassMultiplierTable);
    return true;
}

bool Party::canIncreaseActiveMemberSkillLevel(const std::string &skillName) const
{
    const Character *pMember = activeMember();
    const std::string canonicalSkill = canonicalSkillName(skillName);

    if (pMember == nullptr || canonicalSkill.empty())
    {
        return false;
    }

    const CharacterSkill *pSkill = pMember->findSkill(canonicalSkill);

    if (pSkill == nullptr)
    {
        return false;
    }

    return pMember->skillPoints > pSkill->level;
}

bool Party::increaseActiveMemberSkillLevel(const std::string &skillName)
{
    if (!canIncreaseActiveMemberSkillLevel(skillName))
    {
        return false;
    }

    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    CharacterSkill *pSkill = pMember->findSkill(skillName);

    if (pSkill == nullptr)
    {
        return false;
    }

    const uint32_t newSkillLevel = pSkill->level + 1;
    pSkill->level = newSkillLevel;
    pMember->skillPoints -= newSkillLevel;
    GameMechanics::refreshCharacterBaseResources(*pMember, false, m_pClassMultiplierTable);
    return true;
}

int Party::depositGoldToBank(int amount)
{
    const int transferableGold = std::clamp(amount, 0, m_gold);

    if (transferableGold <= 0)
    {
        return 0;
    }

    addGold(-transferableGold);
    m_bankGold += transferableGold;
    return transferableGold;
}

int Party::withdrawBankGold(int amount)
{
    const int transferableGold = std::clamp(amount, 0, m_bankGold);

    if (transferableGold <= 0)
    {
        return 0;
    }

    m_bankGold -= transferableGold;
    addGold(transferableGold);
    return transferableGold;
}

int Party::depositAllGoldToBank()
{
    return depositGoldToBank(m_gold);
}

int Party::withdrawAllBankGold()
{
    return withdrawBankGold(m_bankGold);
}

bool Party::isFull() const
{
    return m_members.size() >= MaxMembers;
}

bool Party::recruitRosterMember(const RosterEntry &rosterEntry)
{
    if (isFull())
    {
        return false;
    }

    m_members.push_back(buildCharacterFromRosterEntry(rosterEntry, m_pClassMultiplierTable));
    initializePortraitRuntimeState(m_members.back());
    grantRosterInventoryToCharacter(
        m_members.back(),
        rosterEntry,
        m_pItemTable,
        m_pStandardItemEnchantTable,
        m_pSpecialItemEnchantTable);

    m_lastStatus = "party member recruited";
    return true;
}

bool Party::recruitCharacter(const Character &character)
{
    if (isFull())
    {
        return false;
    }

    m_members.push_back(character);
    applyCharacterIdentityFromDollTable(m_members.back(), m_pCharacterDollTable);
    m_members.back().className = canonicalClassName(
        m_members.back().className.empty() ? m_members.back().role : m_members.back().className);
    m_members.back().role = normalizeRoleName(m_members.back().className);

    if (m_members.back().skills.empty() && m_pClassSkillTable != nullptr)
    {
        applyDefaultStartingSkills(m_members.back());
    }

    GameMechanics::refreshCharacterBaseResources(m_members.back(), true, m_pClassMultiplierTable);
    initializePortraitRuntimeState(m_members.back());
    m_lastStatus = "party member recruited";
    return true;
}

bool Party::addAdventurersInnMember(const RosterEntry &rosterEntry, uint32_t portraitPictureId)
{
    Character character = buildCharacterFromRosterEntry(rosterEntry, m_pClassMultiplierTable);
    grantRosterInventoryToCharacter(
        character,
        rosterEntry,
        m_pItemTable,
        m_pStandardItemEnchantTable,
        m_pSpecialItemEnchantTable);
    const uint32_t resolvedPortraitPictureId = resolveAdventurersInnPortraitPictureId(character, portraitPictureId);
    return addAdventurersInnMember(character, resolvedPortraitPictureId);
}

bool Party::addAdventurersInnMember(const Character &character, uint32_t portraitPictureId)
{
    AdventurersInnMember member = {};
    member.character = character;
    applyCharacterIdentityFromDollTable(member.character, m_pCharacterDollTable);
    member.character.className = canonicalClassName(
        member.character.className.empty() ? member.character.role : member.character.className);
    member.character.role = normalizeRoleName(member.character.className);

    if (member.character.skills.empty() && m_pClassSkillTable != nullptr)
    {
        applyDefaultStartingSkills(member.character);
    }

    initializePortraitRuntimeState(member.character);
    member.portraitPictureId = resolveAdventurersInnPortraitPictureId(member.character, portraitPictureId);
    m_adventurersInnMembers.push_back(std::move(member));
    m_lastStatus = "adventurer moved to inn";
    return true;
}

bool Party::hireAdventurersInnMember(size_t innIndex)
{
    if (isFull() || innIndex >= m_adventurersInnMembers.size())
    {
        return false;
    }

    m_members.push_back(m_adventurersInnMembers[innIndex].character);
    applyCharacterIdentityFromDollTable(m_members.back(), m_pCharacterDollTable);
    m_adventurersInnMembers.erase(m_adventurersInnMembers.begin() + innIndex);
    m_lastStatus = "adventurer hired from inn";
    return true;
}

bool Party::dismissMemberToAdventurersInn(size_t memberIndex)
{
    if (memberIndex == 0 || memberIndex >= m_members.size())
    {
        return false;
    }

    const Character dismissedMember = m_members[memberIndex];
    const uint32_t portraitPictureId =
        resolveAdventurersInnPortraitPictureId(dismissedMember, dismissedMember.portraitPictureId);

    if (!addAdventurersInnMember(dismissedMember, portraitPictureId))
    {
        return false;
    }

    m_members.erase(m_members.begin() + memberIndex);

    for (size_t index = memberIndex; index + 1 < m_characterBuffs.size(); ++index)
    {
        m_characterBuffs[index] = m_characterBuffs[index + 1];
    }

    m_characterBuffs.back() = {};

    for (PartyBuffState &buff : m_partyBuffs)
    {
        buff.casterMemberIndex = remapCasterMemberIndexAfterDismiss(buff.casterMemberIndex, memberIndex);
    }

    for (auto &memberBuffs : m_characterBuffs)
    {
        for (CharacterBuffState &buff : memberBuffs)
        {
            buff.casterMemberIndex = remapCasterMemberIndexAfterDismiss(buff.casterMemberIndex, memberIndex);
        }
    }

    m_pendingAudioRequests.erase(
        std::remove_if(
            m_pendingAudioRequests.begin(),
            m_pendingAudioRequests.end(),
            [memberIndex](PendingAudioRequest &request)
            {
                if (request.kind != PendingAudioRequest::Kind::Speech)
                {
                    return false;
                }

                if (request.memberIndex == memberIndex)
                {
                    return true;
                }

                if (request.memberIndex > memberIndex)
                {
                    request.memberIndex -= 1;
                }

                return false;
            }),
        m_pendingAudioRequests.end());

    if (m_members.empty())
    {
        m_activeMemberIndex = 0;
    }
    else if (m_activeMemberIndex > memberIndex)
    {
        m_activeMemberIndex -= 1;
    }
    else if (m_activeMemberIndex >= m_members.size())
    {
        m_activeMemberIndex = m_members.size() - 1;
    }

    rebuildMagicalBonusesFromBuffs();
    m_lastStatus = "party member dismissed";
    return true;
}

bool Party::replaceMemberWithRosterEntry(size_t memberIndex, const RosterEntry &rosterEntry)
{
    if (memberIndex >= m_members.size())
    {
        return false;
    }

    m_members[memberIndex] = buildCharacterFromRosterEntry(rosterEntry, m_pClassMultiplierTable);
    applyCharacterIdentityFromDollTable(m_members[memberIndex], m_pCharacterDollTable);
    initializePortraitRuntimeState(m_members[memberIndex]);
    grantRosterInventoryToCharacter(
        m_members[memberIndex],
        rosterEntry,
        m_pItemTable,
        m_pStandardItemEnchantTable,
        m_pSpecialItemEnchantTable);

    rebuildMagicalBonusesFromBuffs();
    m_lastStatus = "party member replaced from roster";
    return true;
}

bool Party::hasRosterMember(uint32_t rosterId) const
{
    if (rosterId == 0)
    {
        return false;
    }

    for (const Character &member : m_members)
    {
        if (member.rosterId == rosterId)
        {
            return true;
        }
    }

    for (const AdventurersInnMember &member : m_adventurersInnMembers)
    {
        if (member.character.rosterId == rosterId)
        {
            return true;
        }
    }

    return false;
}

bool Party::hasQuestBit(uint32_t questBitId) const
{
    return questBitId != 0 && m_questBits.contains(questBitId);
}

void Party::setQuestBit(uint32_t questBitId, bool value)
{
    if (questBitId == 0)
    {
        return;
    }

    if (value)
    {
        const bool inserted = m_questBits.insert(questBitId).second;
        if (inserted)
        {
            GAMEPLAY_DEBUG_TRACE("qbit_set id=" + std::to_string(questBitId));
        }
    }
    else
    {
        const size_t erased = m_questBits.erase(questBitId);
        if (erased != 0)
        {
            GAMEPLAY_DEBUG_TRACE("qbit_cleared id=" + std::to_string(questBitId));
        }
    }
}

void Party::applyGlobalNpcStateTo(EventRuntimeState &runtimeState) const
{
    std::unordered_set<uint32_t> partyFollowerIds;
    partyFollowerIds.reserve(m_hiredNpcFollowers.size());

    for (const HiredNpcFollower &follower : m_hiredNpcFollowers)
    {
        if (follower.npcId != 0)
        {
            partyFollowerIds.insert(follower.npcId);
        }
    }

    const auto staleFollowerIt = std::remove_if(
        runtimeState.hiredNpcFollowers.begin(),
        runtimeState.hiredNpcFollowers.end(),
        [&partyFollowerIds](const HiredNpcFollower &follower)
        {
            return follower.npcId != 0 && !partyFollowerIds.contains(follower.npcId);
        });

    if (staleFollowerIt != runtimeState.hiredNpcFollowers.end())
    {
        for (auto iterator = staleFollowerIt; iterator != runtimeState.hiredNpcFollowers.end(); ++iterator)
        {
            runtimeState.unavailableNpcIds.erase(iterator->npcId);
        }

        runtimeState.hiredNpcFollowers.erase(staleFollowerIt, runtimeState.hiredNpcFollowers.end());
    }

    for (const auto &[npcId, topicOverrides] : m_npcTopicOverrides)
    {
        for (const auto &[topicSlotIndex, topicId] : topicOverrides)
        {
            runtimeState.npcTopicOverrides[npcId][topicSlotIndex] = topicId;
        }
    }

    for (const auto &[groupId, newsId] : m_npcGroupNews)
    {
        runtimeState.npcGroupNews[groupId] = newsId;
    }

    for (const auto &[npcId, greetingId] : m_npcGreetingOverrides)
    {
        runtimeState.npcGreetingOverrides[npcId] = greetingId;
    }

    for (const auto &[npcId, displayCount] : m_npcGreetingDisplayCounts)
    {
        runtimeState.npcGreetingDisplayCounts[npcId] = displayCount;
    }

    for (const auto &[npcId, houseId] : m_npcHouseOverrides)
    {
        runtimeState.npcHouseOverrides[npcId] = houseId;
    }

    for (const auto &[npcId, itemId] : m_npcItemOverrides)
    {
        runtimeState.npcItemOverrides[npcId] = itemId;
    }

    for (uint32_t npcId : m_unavailableNpcIds)
    {
        runtimeState.unavailableNpcIds.insert(npcId);
    }

    for (const HiredNpcFollower &follower : m_hiredNpcFollowers)
    {
        const auto existingFollowerIt = std::find_if(
            runtimeState.hiredNpcFollowers.begin(),
            runtimeState.hiredNpcFollowers.end(),
            [&follower](const HiredNpcFollower &runtimeFollower)
            {
                return runtimeFollower.npcId == follower.npcId;
            });

        if (existingFollowerIt == runtimeState.hiredNpcFollowers.end())
        {
            runtimeState.hiredNpcFollowers.push_back(follower);
        }
        else
        {
            *existingFollowerIt = follower;
        }

        if (follower.npcId != 0)
        {
            runtimeState.unavailableNpcIds.insert(follower.npcId);
        }
    }
}

void Party::setNpcTopicOverride(uint32_t npcId, uint32_t topicSlotIndex, uint32_t topicId)
{
    m_npcTopicOverrides[npcId][topicSlotIndex] = topicId;
}

void Party::setNpcGroupNews(uint32_t groupId, uint32_t newsId)
{
    m_npcGroupNews[groupId] = newsId;
}

void Party::setNpcGreetingOverride(uint32_t npcId, uint32_t greetingId)
{
    m_npcGreetingOverrides[npcId] = greetingId;
    m_npcGreetingDisplayCounts[npcId] = 0;
}

void Party::setNpcHouseOverride(uint32_t npcId, uint32_t houseId)
{
    m_npcHouseOverrides[npcId] = houseId;
}

void Party::clearNpcHouseOverride(uint32_t npcId)
{
    m_npcHouseOverrides.erase(npcId);
}

void Party::setNpcItemOverride(uint32_t npcId, uint32_t itemId)
{
    m_npcItemOverrides[npcId] = itemId;
}

void Party::setNpcUnavailable(uint32_t npcId, bool unavailable)
{
    if (unavailable)
    {
        m_unavailableNpcIds.insert(npcId);
    }
    else
    {
        m_unavailableNpcIds.erase(npcId);
    }
}

void Party::addHiredNpcFollower(const HiredNpcFollower &follower)
{
    if (follower.npcId == 0)
    {
        return;
    }

    const auto followerIt = std::find_if(
        m_hiredNpcFollowers.begin(),
        m_hiredNpcFollowers.end(),
        [&follower](const HiredNpcFollower &existingFollower)
        {
            return existingFollower.npcId == follower.npcId;
        });

    if (followerIt == m_hiredNpcFollowers.end())
    {
        m_hiredNpcFollowers.push_back(follower);
        GAMEPLAY_DEBUG_TRACE(
            "hireling_hired npc_id=" + std::to_string(follower.npcId)
            + " profession_id=" + std::to_string(follower.professionId)
            + " weekly_cost=" + std::to_string(follower.weeklyCost));
    }
    else
    {
        *followerIt = follower;
    }

    m_unavailableNpcIds.insert(follower.npcId);
}

void Party::removeHiredNpcFollower(uint32_t npcId)
{
    const auto followerIt = std::remove_if(
        m_hiredNpcFollowers.begin(),
        m_hiredNpcFollowers.end(),
        [npcId](const HiredNpcFollower &follower)
        {
            return follower.npcId == npcId;
        });

    if (followerIt != m_hiredNpcFollowers.end())
    {
        for (auto iterator = followerIt; iterator != m_hiredNpcFollowers.end(); ++iterator)
        {
            GAMEPLAY_DEBUG_TRACE(
                "hireling_left npc_id=" + std::to_string(iterator->npcId)
                + " profession_id=" + std::to_string(iterator->professionId)
                + " weekly_cost=" + std::to_string(iterator->weeklyCost));
        }

        m_hiredNpcFollowers.erase(followerIt, m_hiredNpcFollowers.end());
    }
}

void Party::setHiredNpcFollowerAbilityUsedDay(uint32_t npcId, uint32_t day)
{
    for (HiredNpcFollower &follower : m_hiredNpcFollowers)
    {
        if (follower.npcId == npcId)
        {
            follower.abilityUsedDay = day;
            return;
        }
    }
}

bool Party::hasAward(uint32_t awardId) const
{
    if (awardId == 0)
    {
        return false;
    }

    for (const Character &member : m_members)
    {
        if (member.awards.contains(awardId))
        {
            return true;
        }
    }

    return false;
}

bool Party::hasAward(size_t memberIndex, uint32_t awardId) const
{
    const Character *pMember = member(memberIndex);
    return pMember != nullptr && awardId != 0 && pMember->awards.contains(awardId);
}

void Party::addAward(uint32_t awardId)
{
    if (awardId == 0)
    {
        return;
    }

    bool acquired = false;
    for (Character &member : m_members)
    {
        acquired = member.awards.insert(awardId).second || acquired;
    }

    if (acquired)
    {
        GAMEPLAY_DEBUG_TRACE("award_acquired id=" + std::to_string(awardId) + " scope=party");
    }
}

void Party::addAward(size_t memberIndex, uint32_t awardId)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || awardId == 0)
    {
        return;
    }

    const bool acquired = pMember->awards.insert(awardId).second;
    if (acquired)
    {
        GAMEPLAY_DEBUG_TRACE(
            "award_acquired id=" + std::to_string(awardId)
            + " member_index=" + std::to_string(memberIndex));
    }
}

void Party::removeAward(uint32_t awardId)
{
    if (awardId == 0)
    {
        return;
    }

    bool cleared = false;
    for (Character &member : m_members)
    {
        cleared = member.awards.erase(awardId) != 0 || cleared;
    }

    if (cleared)
    {
        GAMEPLAY_DEBUG_TRACE("award_cleared id=" + std::to_string(awardId) + " scope=party");
    }
}

void Party::removeAward(size_t memberIndex, uint32_t awardId)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || awardId == 0)
    {
        return;
    }

    const bool cleared = pMember->awards.erase(awardId) != 0;
    if (cleared)
    {
        GAMEPLAY_DEBUG_TRACE(
            "award_cleared id=" + std::to_string(awardId)
            + " member_index=" + std::to_string(memberIndex));
    }
}

int Party::inventoryItemCount(uint32_t objectDescriptionId, std::optional<size_t> memberIndex) const
{
    if (objectDescriptionId == 0)
    {
        return 0;
    }

    int totalCount = 0;

    auto countMemberItems = [&](const Character &member)
    {
        static constexpr EquipmentSlot EquipmentSlots[] = {
            EquipmentSlot::OffHand,
            EquipmentSlot::MainHand,
            EquipmentSlot::Bow,
            EquipmentSlot::Armor,
            EquipmentSlot::Helm,
            EquipmentSlot::Belt,
            EquipmentSlot::Cloak,
            EquipmentSlot::Gauntlets,
            EquipmentSlot::Boots,
            EquipmentSlot::Amulet,
            EquipmentSlot::Ring1,
            EquipmentSlot::Ring2,
            EquipmentSlot::Ring3,
            EquipmentSlot::Ring4,
            EquipmentSlot::Ring5,
            EquipmentSlot::Ring6,
        };

        for (const InventoryItem &item : member.inventory)
        {
            if (item.objectDescriptionId == objectDescriptionId)
            {
                totalCount += static_cast<int>(item.quantity);
            }
        }

        for (EquipmentSlot slot : EquipmentSlots)
        {
            if (::OpenYAMM::Game::equippedItemId(member.equipment, slot) == objectDescriptionId)
            {
                totalCount += 1;
            }
        }
    };

    if (memberIndex)
    {
        const Character *pMember = member(*memberIndex);

        if (pMember != nullptr)
        {
            countMemberItems(*pMember);
        }

        return totalCount;
    }

    for (const Character &member : m_members)
    {
        countMemberItems(member);
    }

    return totalCount;
}

void Party::recordEverOwnedItem(uint32_t objectDescriptionId)
{
    if (objectDescriptionId == 0)
    {
        return;
    }

    m_everOwnedItemIds.insert(objectDescriptionId);
}

bool Party::hasEverOwnedItem(uint32_t objectDescriptionId) const
{
    return objectDescriptionId != 0 && m_everOwnedItemIds.contains(objectDescriptionId);
}

void Party::setHeldItemForQueries(const InventoryItem &item)
{
    m_heldItemIdForQueries = item.objectDescriptionId;
    recordEverOwnedItemIfRelevant(item);
}

uint32_t Party::heldItemIdForQueries() const
{
    return m_heldItemIdForQueries;
}

void Party::clearHeldItemForQueries()
{
    m_heldItemIdForQueries = 0;
}

bool Party::hasItemAnywhere(uint32_t objectDescriptionId) const
{
    return objectDescriptionId != 0
        && (inventoryItemCount(objectDescriptionId) > 0 || m_heldItemIdForQueries == objectDescriptionId);
}

bool Party::grantItemToMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    for (uint32_t itemIndex = 0; itemIndex < quantity; ++itemIndex)
    {
        InventoryItem item = makeInventoryItem(m_pItemTable, objectDescriptionId);

        if (!pMember->addInventoryItem(item))
        {
            return false;
        }

        markArtifactItemFoundIfRelevant(item);
        recordEverOwnedItemIfRelevant(item);
    }

    m_lastStatus = "item granted";
    return true;
}

bool Party::removeItemFromMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    for (uint32_t itemIndex = 0; itemIndex < quantity; ++itemIndex)
    {
        if (!pMember->removeInventoryItem(objectDescriptionId))
        {
            return false;
        }
    }

    m_lastStatus = "item removed";
    return true;
}

bool Party::takeItemFromMemberInventoryCell(size_t memberIndex, uint8_t gridX, uint8_t gridY, InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    if (!pMember->takeInventoryItemAt(gridX, gridY, item))
    {
        return false;
    }

    m_lastStatus = "item picked up";
    return true;
}

bool Party::tryAutoPlaceItemInMemberInventory(size_t memberIndex, const InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    if (!pMember->addInventoryItem(item))
    {
        m_lastStatus = "inventory full";
        return false;
    }

    recordEverOwnedItemIfRelevant(item);
    m_lastStatus = "item moved";
    return true;
}

bool Party::tryPlaceItemInMemberInventoryCell(
    size_t memberIndex,
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY,
    std::optional<InventoryItem> &replacedItem)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        replacedItem.reset();
        return false;
    }

    if (!pMember->tryPlaceInventoryItemAt(item, gridX, gridY, replacedItem))
    {
        return false;
    }

    recordEverOwnedItemIfRelevant(item);
    m_lastStatus = replacedItem.has_value() ? "item swapped" : "item moved";
    return true;
}

bool Party::takeEquippedItemFromMember(size_t memberIndex, EquipmentSlot slot, InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        return false;
    }

    item = {};
    item = makeInventoryItem(m_pItemTable, itemId, equippedItemRuntimeState(pMember->equipmentRuntime, slot));
    ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot) = 0;
    equippedItemRuntimeState(pMember->equipmentRuntime, slot) = {};
    rebuildMagicalBonusesFromBuffs();
    m_lastStatus = "item unequipped";
    return true;
}

bool Party::tryEquipItemOnMember(
    size_t memberIndex,
    EquipmentSlot targetSlot,
    const InventoryItem &item,
    std::optional<EquipmentSlot> displacedSlot,
    bool autoStoreDisplacedItem,
    std::optional<InventoryItem> &heldReplacement)
{
    heldReplacement.reset();

    Character *pMember = member(memberIndex);

    if (pMember == nullptr || item.objectDescriptionId == 0)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable != nullptr ? m_pItemTable->get(item.objectDescriptionId) : nullptr;

    if (pItemDefinition == nullptr
        || !ItemRuntime::characterMeetsClassRestriction(*pMember, *pItemDefinition)
        || !ItemRuntime::characterMeetsRaceRestriction(*pMember, *pItemDefinition))
    {
        m_lastStatus = "cannot equip";
        return false;
    }

    if (displacedSlot
        && *displacedSlot != targetSlot
        && ::OpenYAMM::Game::equippedItemId(pMember->equipment, targetSlot) != 0)
    {
        return false;
    }

    if (!displacedSlot && ::OpenYAMM::Game::equippedItemId(pMember->equipment, targetSlot) != 0)
    {
        displacedSlot = targetSlot;
    }

    if (!GameMechanics::isEquipmentAllowedWithWetsuit(
            *pMember,
            m_pItemTable,
            targetSlot,
            item.objectDescriptionId,
            displacedSlot))
    {
        m_lastStatus = "cannot equip";
        return false;
    }

    const uint32_t displacedItemId =
        displacedSlot ? ::OpenYAMM::Game::equippedItemId(pMember->equipment, *displacedSlot) : 0;
    const EquippedItemRuntimeState displacedRuntimeState =
        displacedSlot ? equippedItemRuntimeState(pMember->equipmentRuntime, *displacedSlot) : EquippedItemRuntimeState {};

    if (autoStoreDisplacedItem && displacedItemId != 0)
    {
        InventoryItem displacedInventoryItem = makeInventoryItem(
            m_pItemTable,
            displacedItemId,
            displacedRuntimeState);

        if (!pMember->addInventoryItem(displacedInventoryItem))
        {
            m_lastStatus = "inventory full";
            return false;
        }
    }

    if (displacedSlot)
    {
        ::OpenYAMM::Game::equippedItemId(pMember->equipment, *displacedSlot) = 0;
        equippedItemRuntimeState(pMember->equipmentRuntime, *displacedSlot) = {};
    }

    ::OpenYAMM::Game::equippedItemId(pMember->equipment, targetSlot) = item.objectDescriptionId;
    EquippedItemRuntimeState &targetRuntimeState = equippedItemRuntimeState(pMember->equipmentRuntime, targetSlot);
    targetRuntimeState.identified = item.identified;
    targetRuntimeState.broken = item.broken;
    targetRuntimeState.stolen = item.stolen;
    targetRuntimeState.standardEnchantId = item.standardEnchantId;
    targetRuntimeState.standardEnchantPower = item.standardEnchantPower;
    targetRuntimeState.specialEnchantId = item.specialEnchantId;
    targetRuntimeState.artifactId = item.artifactId;
    targetRuntimeState.rarity = item.rarity;
    targetRuntimeState.currentCharges = item.currentCharges;
    targetRuntimeState.maxCharges = item.maxCharges;
    targetRuntimeState.temporaryBonusRemainingSeconds = item.temporaryBonusRemainingSeconds;

    if (targetRuntimeState.rarity == ItemRarity::Common && ItemRuntime::isRareItem(*pItemDefinition))
    {
        targetRuntimeState.rarity = pItemDefinition->rarity;
    }

    if (targetRuntimeState.artifactId == 0 && ItemRuntime::isRareItem(*pItemDefinition))
    {
        targetRuntimeState.artifactId = static_cast<uint16_t>(std::min<uint32_t>(pItemDefinition->itemId, 0xFFFFu));
    }

    if (!autoStoreDisplacedItem && displacedItemId != 0)
    {
        InventoryItem displacedInventoryItem = makeInventoryItem(m_pItemTable, displacedItemId, displacedRuntimeState);
        heldReplacement = displacedInventoryItem;
        m_lastStatus = "item swapped";
    }
    else
    {
        m_lastStatus = "item equipped";
    }

    rebuildMagicalBonusesFromBuffs();
    markArtifactItemFoundIfRelevant(item);
    recordEverOwnedItemIfRelevant(item);
    return true;
}

std::optional<InventoryItem> Party::equippedItem(size_t memberIndex, EquipmentSlot slot) const
{
    const Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return std::nullopt;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        return std::nullopt;
    }

    return makeInventoryItem(m_pItemTable, itemId, equippedItemRuntimeState(pMember->equipmentRuntime, slot));
}

const InventoryItem *Party::memberInventoryItem(size_t memberIndex, uint8_t gridX, uint8_t gridY) const
{
    const Character *pMember = member(memberIndex);
    return pMember != nullptr ? pMember->inventoryItemAt(gridX, gridY) : nullptr;
}

InventoryItem *Party::memberInventoryItemMutable(size_t memberIndex, uint8_t gridX, uint8_t gridY)
{
    Character *pMember = member(memberIndex);
    return pMember != nullptr ? inventoryItemAtMutable(*pMember, gridX, gridY) : nullptr;
}

uint32_t Party::equippedItemId(size_t memberIndex, EquipmentSlot slot) const
{
    const Character *pMember = member(memberIndex);
    return pMember != nullptr ? ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot) : 0;
}

const EquippedItemRuntimeState *Party::equippedItemRuntime(size_t memberIndex, EquipmentSlot slot) const
{
    const Character *pMember = member(memberIndex);
    return pMember != nullptr ? &equippedItemRuntimeState(pMember->equipmentRuntime, slot) : nullptr;
}

EquippedItemRuntimeState *Party::equippedItemRuntimeMutable(size_t memberIndex, EquipmentSlot slot)
{
    Character *pMember = member(memberIndex);
    return pMember != nullptr ? &equippedItemRuntimeState(pMember->equipmentRuntime, slot) : nullptr;
}

bool Party::consumeEquippedWandCharge(size_t memberIndex)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr || pMember->equipment.mainHand == 0)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pMember->equipment.mainHand);

    if (pItemDefinition == nullptr
        || pItemDefinition->equipStat != "WeaponW"
        || pMember->equipmentRuntime.mainHand.broken
        || pMember->equipmentRuntime.mainHand.currentCharges == 0)
    {
        return false;
    }

    --pMember->equipmentRuntime.mainHand.currentCharges;
    return true;
}

void Party::refreshDerivedState()
{
    rebuildMagicalBonusesFromBuffs();
}

bool Party::isPartyWideUtilitySkill(std::string_view skillName)
{
    const std::string canonical = canonicalPartyWideUtilitySkillName(skillName);

    return canonical == "RepairItem"
        || canonical == "DisarmTraps"
        || canonical == "Merchant"
        || canonical == "IdentifyItem"
        || canonical == "IdentifyMonster"
        || canonical == "Alchemy"
        || canonical == "Perception";
}

std::optional<size_t> Party::bestPartyWideUtilitySkillMemberIndex(
    std::string_view skillName,
    bool requireCanAct) const
{
    const std::string canonical = canonicalPartyWideUtilitySkillName(skillName);

    if (!isPartyWideUtilitySkill(canonical))
    {
        return std::nullopt;
    }

    std::optional<size_t> bestMemberIndex;
    int bestScore = 0;

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        const Character &member = m_members[memberIndex];

        if (requireCanAct && !GameMechanics::canAct(member))
        {
            continue;
        }

        const int score = partyWideUtilitySkillScore(member, canonical);

        if (score > bestScore)
        {
            bestScore = score;
            bestMemberIndex = memberIndex;
        }
    }

    return bestMemberIndex;
}

const Character *Party::bestPartyWideUtilitySkillMember(std::string_view skillName, bool requireCanAct) const
{
    const std::optional<size_t> memberIndex = bestPartyWideUtilitySkillMemberIndex(skillName, requireCanAct);
    return memberIndex ? member(*memberIndex) : nullptr;
}

int Party::bestPartyWideUtilitySkillValue(std::string_view skillName, bool requireCanAct) const
{
    const std::optional<size_t> memberIndex = bestPartyWideUtilitySkillMemberIndex(skillName, requireCanAct);
    const Character *pMember = memberIndex ? member(*memberIndex) : nullptr;

    if (pMember == nullptr)
    {
        return 0;
    }

    return partyWideUtilitySkillScore(*pMember, canonicalPartyWideUtilitySkillName(skillName));
}

bool Party::tryIdentifyMemberInventoryItem(
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    size_t inspectorMemberIndex,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);
    const Character *pInspector = bestPartyWideUtilitySkillMember("IdentifyItem");
    const Character *pRequestedInspector = member(inspectorMemberIndex);

    if (pMember == nullptr || pRequestedInspector == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    InventoryItem *pItem = inventoryItemAtMutable(*pMember, gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = "No item there.";
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    if (pItem->identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        statusText = "Already identified.";
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            pItemDefinition,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    if (pInspector == nullptr || !ItemRuntime::canCharacterIdentifyItem(*pInspector, *pItemDefinition))
    {
        statusText = "Identify Failed";
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            pItemDefinition,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const bool identified = identifyInventoryItemInstance(*pItem, *pItemDefinition, statusText);

    if (identified)
    {
        m_lastStatus = "item identified";
    }

    logItemInteractionResult(
        "identify",
        pInspector,
        pMember,
        pItemDefinition,
        "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
        identified,
        statusText);

    return identified;
}

bool Party::tryRepairMemberInventoryItem(
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    size_t inspectorMemberIndex,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);
    const Character *pInspector = bestPartyWideUtilitySkillMember("RepairItem");
    const Character *pRequestedInspector = member(inspectorMemberIndex);

    if (pMember == nullptr || pRequestedInspector == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    InventoryItem *pItem = inventoryItemAtMutable(*pMember, gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = "No item there.";
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    if (!pItem->broken)
    {
        statusText = "Nothing to repair.";
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            pItemDefinition,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    if (pInspector == nullptr || !ItemRuntime::canCharacterRepairItem(*pInspector, *pItemDefinition))
    {
        statusText = "Repair Failed";
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            pItemDefinition,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const bool repaired = repairInventoryItemInstance(*pItem, *pItemDefinition, statusText);

    if (repaired)
    {
        rebuildMagicalBonusesFromBuffs();
        m_lastStatus = "item repaired";
    }

    logItemInteractionResult(
        "repair",
        pInspector,
        pMember,
        pItemDefinition,
        "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
        repaired,
        statusText);

    return repaired;
}

bool Party::identifyMemberInventoryItem(
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    InventoryItem *pItem = inventoryItemAtMutable(*pMember, gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = "No item there.";
        logItemInteractionResult(
            "identify",
            nullptr,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        logItemInteractionResult(
            "identify",
            nullptr,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const bool identified = identifyInventoryItemInstance(*pItem, *pItemDefinition, statusText);

    if (identified)
    {
        m_lastStatus = "item identified";
    }

    logItemInteractionResult(
        "identify",
        nullptr,
        pMember,
        pItemDefinition,
        "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
        identified,
        statusText);

    return identified;
}

bool Party::repairMemberInventoryItem(
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    InventoryItem *pItem = inventoryItemAtMutable(*pMember, gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = "No item there.";
        logItemInteractionResult(
            "repair",
            nullptr,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        logItemInteractionResult(
            "repair",
            nullptr,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const bool repaired = repairInventoryItemInstance(*pItem, *pItemDefinition, statusText);

    if (repaired)
    {
        rebuildMagicalBonusesFromBuffs();
        m_lastStatus = "item repaired";
    }

    logItemInteractionResult(
        "repair",
        nullptr,
        pMember,
        pItemDefinition,
        "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
        repaired,
        statusText);

    return repaired;
}

bool Party::tryIdentifyEquippedItem(
    size_t memberIndex,
    EquipmentSlot slot,
    size_t inspectorMemberIndex,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);
    const Character *pInspector = bestPartyWideUtilitySkillMember("IdentifyItem");
    const Character *pRequestedInspector = member(inspectorMemberIndex);

    if (pMember == nullptr || pRequestedInspector == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        statusText = "No item there.";
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    EquippedItemRuntimeState &runtimeState = equippedItemRuntimeState(pMember->equipmentRuntime, slot);
    const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    if (runtimeState.identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        statusText = "Already identified.";
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            pItemDefinition,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    if (pInspector == nullptr || !ItemRuntime::canCharacterIdentifyItem(*pInspector, *pItemDefinition))
    {
        statusText = "Identify Failed";
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            pItemDefinition,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    const bool identified = identifyEquippedItemInstance(runtimeState, *pItemDefinition, statusText);

    if (identified)
    {
        m_lastStatus = "item identified";
    }

    logItemInteractionResult(
        "identify",
        pInspector,
        pMember,
        pItemDefinition,
        std::string("equipped(") + equipmentSlotName(slot) + ")",
        identified,
        statusText);

    return identified;
}

bool Party::tryRepairEquippedItem(
    size_t memberIndex,
    EquipmentSlot slot,
    size_t inspectorMemberIndex,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);
    const Character *pInspector = bestPartyWideUtilitySkillMember("RepairItem");
    const Character *pRequestedInspector = member(inspectorMemberIndex);

    if (pMember == nullptr || pRequestedInspector == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        statusText = "No item there.";
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    EquippedItemRuntimeState &runtimeState = equippedItemRuntimeState(pMember->equipmentRuntime, slot);
    const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    if (!runtimeState.broken)
    {
        statusText = "Nothing to repair.";
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            pItemDefinition,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    if (pInspector == nullptr || !ItemRuntime::canCharacterRepairItem(*pInspector, *pItemDefinition))
    {
        statusText = "Repair Failed";
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            pItemDefinition,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    const bool repaired = repairEquippedItemInstance(runtimeState, *pItemDefinition, statusText);

    if (repaired)
    {
        m_lastStatus = "item repaired";
    }

    logItemInteractionResult(
        "repair",
        pInspector,
        pMember,
        pItemDefinition,
        std::string("equipped(") + equipmentSlotName(slot) + ")",
        repaired,
        statusText);

    return repaired;
}

bool Party::identifyEquippedItem(size_t memberIndex, EquipmentSlot slot, std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        statusText = "No item there.";
        logItemInteractionResult(
            "identify",
            nullptr,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    EquippedItemRuntimeState &runtimeState = equippedItemRuntimeState(pMember->equipmentRuntime, slot);
    const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        logItemInteractionResult(
            "identify",
            nullptr,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    const bool identified = identifyEquippedItemInstance(runtimeState, *pItemDefinition, statusText);

    if (identified)
    {
        m_lastStatus = "item identified";
    }

    logItemInteractionResult(
        "identify",
        nullptr,
        pMember,
        pItemDefinition,
        std::string("equipped(") + equipmentSlotName(slot) + ")",
        identified,
        statusText);

    return identified;
}

bool Party::repairEquippedItem(size_t memberIndex, EquipmentSlot slot, std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        statusText = "No item there.";
        logItemInteractionResult(
            "repair",
            nullptr,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    EquippedItemRuntimeState &runtimeState = equippedItemRuntimeState(pMember->equipmentRuntime, slot);
    const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        logItemInteractionResult(
            "repair",
            nullptr,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    const bool repaired = repairEquippedItemInstance(runtimeState, *pItemDefinition, statusText);

    if (repaired)
    {
        m_lastStatus = "item repaired";
    }

    logItemInteractionResult(
        "repair",
        nullptr,
        pMember,
        pItemDefinition,
        std::string("equipped(") + equipmentSlotName(slot) + ")",
        repaired,
        statusText);

    return repaired;
}

bool Party::setMemberClassName(size_t memberIndex, const std::string &className)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->className = canonicalClassName(className);
    pMember->role = normalizeRoleName(pMember->className);

    if (pMember->className == "Lich")
    {
        applyLichIdentity(*pMember, m_pCharacterDollTable);
        applyLichState(*pMember);
    }

    GameMechanics::refreshCharacterBaseResources(*pMember, false, m_pClassMultiplierTable);
    m_lastStatus = "class changed";
    return true;
}

bool Party::applyLichTransformation(size_t memberIndex)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->className = "Lich";
    pMember->role = normalizeRoleName(pMember->className);
    applyLichIdentity(*pMember, m_pCharacterDollTable);
    applyLichState(*pMember);
    GameMechanics::refreshCharacterBaseResources(*pMember, false, m_pClassMultiplierTable);
    m_lastStatus = "lich transformation applied";
    return true;
}

const Character *Party::member(size_t memberIndex) const
{
    if (memberIndex >= m_members.size())
    {
        return nullptr;
    }

    return &m_members[memberIndex];
}

Character *Party::member(size_t memberIndex)
{
    if (memberIndex >= m_members.size())
    {
        return nullptr;
    }

    return &m_members[memberIndex];
}

bool Party::canSelectMemberInGameplay(size_t memberIndex) const
{
    const Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    return GameMechanics::canSelectInGameplay(*pMember);
}

bool Party::hasSelectableMemberInGameplay() const
{
    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        if (canSelectMemberInGameplay(memberIndex))
        {
            return true;
        }
    }

    return false;
}

bool Party::hasActableMember() const
{
    for (const Character &member : m_members)
    {
        if (!member.conditions.test(static_cast<size_t>(CharacterCondition::Paralyzed))
            && !member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious))
            && !member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
            && !member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
            && !member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
        {
            return true;
        }
    }

    return false;
}

uint8_t Party::resolveInventoryWidth(uint32_t objectDescriptionId) const
{
    if (m_pItemTable == nullptr)
    {
        return 1;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return 1;
    }

    return std::max<uint8_t>(1, pItemDefinition->inventoryWidth);
}

uint8_t Party::resolveInventoryHeight(uint32_t objectDescriptionId) const
{
    if (m_pItemTable == nullptr)
    {
        return 1;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return 1;
    }

    return std::max<uint8_t>(1, pItemDefinition->inventoryHeight);
}

const std::vector<Character> &Party::members() const
{
    return m_members;
}

size_t Party::memberCount() const
{
    return m_members.size();
}

const std::vector<AdventurersInnMember> &Party::adventurersInnMembers() const
{
    return m_adventurersInnMembers;
}

const AdventurersInnMember *Party::adventurersInnMember(size_t innIndex) const
{
    return innIndex < m_adventurersInnMembers.size() ? &m_adventurersInnMembers[innIndex] : nullptr;
}

AdventurersInnMember *Party::adventurersInnMember(size_t innIndex)
{
    return innIndex < m_adventurersInnMembers.size() ? &m_adventurersInnMembers[innIndex] : nullptr;
}

const Character *Party::adventurersInnCharacter(size_t innIndex) const
{
    const AdventurersInnMember *pMember = adventurersInnMember(innIndex);
    return pMember != nullptr ? &pMember->character : nullptr;
}

Character *Party::adventurersInnCharacter(size_t innIndex)
{
    AdventurersInnMember *pMember = adventurersInnMember(innIndex);
    return pMember != nullptr ? &pMember->character : nullptr;
}

void Party::clearAdventurersInnMembers()
{
    m_adventurersInnMembers.clear();
}

bool Party::setActiveMemberIndex(size_t memberIndex)
{
    if (memberIndex >= m_members.size())
    {
        return false;
    }

    m_activeMemberIndex = memberIndex;
    return true;
}

bool Party::canSpendSpellPoints(size_t memberIndex, int amount) const
{
    if (m_debugUnlimitedMana)
    {
        return true;
    }

    const Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    return amount <= 0 || pMember->spellPoints >= amount;
}

bool Party::spendSpellPoints(size_t memberIndex, int amount)
{
    if (m_debugUnlimitedMana)
    {
        return true;
    }

    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    if (amount <= 0)
    {
        return true;
    }

    if (pMember->spellPoints < amount)
    {
        return false;
    }

    pMember->spellPoints -= amount;
    return true;
}

bool Party::spendSpellPointsOnActiveMember(int amount)
{
    return spendSpellPoints(activeMemberIndex(), amount);
}

void Party::advanceTimedStates(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    bool buffsChanged = false;
    bool itemsChanged = false;

    for (PartyBuffState &buff : m_partyBuffs)
    {
        if (!buff.active())
        {
            continue;
        }

        const float previousRemainingSeconds = buff.remainingSeconds;
        buff.remainingSeconds = std::max(0.0f, buff.remainingSeconds - deltaSeconds);

        if (previousRemainingSeconds > 0.0f && buff.remainingSeconds <= 0.0f)
        {
            buffsChanged = true;

            if (isSpellId(buff.spellId, SpellId::Haste))
            {
                for (Character &member : m_members)
                {
                    const size_t memberIndex = static_cast<size_t>(&member - m_members.data());
                    applyMemberCondition(memberIndex, CharacterCondition::Weak);
                }
            }
        }
    }

    for (size_t memberIndex = 0; memberIndex < m_members.size() && memberIndex < m_characterBuffs.size(); ++memberIndex)
    {
        for (CharacterBuffState &buff : m_characterBuffs[memberIndex])
        {
            if (!buff.active())
            {
                continue;
            }

            const float previousRemainingSeconds = buff.remainingSeconds;
            buff.remainingSeconds = std::max(0.0f, buff.remainingSeconds - deltaSeconds);

            if (isSpellId(buff.spellId, SpellId::Regeneration))
            {
                buff.periodicAccumulatorSeconds += deltaSeconds;
                const int healPerTick = 5 * std::max(1, buff.power);

                while (buff.periodicAccumulatorSeconds >= OeFiveGameMinuteTickGameSeconds)
                {
                    buff.periodicAccumulatorSeconds -= OeFiveGameMinuteTickGameSeconds;
                    healMember(memberIndex, healPerTick);
                }
            }

            if (previousRemainingSeconds > 0.0f && buff.remainingSeconds <= 0.0f)
            {
                buffsChanged = true;
                buff.periodicAccumulatorSeconds = 0.0f;
            }
        }
    }

    const auto updateTimedInventoryItem =
        [&itemsChanged, deltaSeconds](InventoryItem &item)
        {
            if (item.temporaryBonusRemainingSeconds <= 0.0f)
            {
                return;
            }

            item.temporaryBonusRemainingSeconds = std::max(0.0f, item.temporaryBonusRemainingSeconds - deltaSeconds);

            if (item.temporaryBonusRemainingSeconds > 0.0f)
            {
                return;
            }

            item.standardEnchantId = 0;
            item.standardEnchantPower = 0;
            item.specialEnchantId = 0;
            itemsChanged = true;
        };
    const auto updateTimedEquippedItem =
        [&itemsChanged, deltaSeconds](EquippedItemRuntimeState &item)
        {
            if (item.temporaryBonusRemainingSeconds <= 0.0f)
            {
                return;
            }

            item.temporaryBonusRemainingSeconds = std::max(0.0f, item.temporaryBonusRemainingSeconds - deltaSeconds);

            if (item.temporaryBonusRemainingSeconds > 0.0f)
            {
                return;
            }

            item.standardEnchantId = 0;
            item.standardEnchantPower = 0;
            item.specialEnchantId = 0;
            itemsChanged = true;
        };

    for (Character &member : m_members)
    {
        for (InventoryItem &item : member.inventory)
        {
            updateTimedInventoryItem(item);
        }

        updateTimedEquippedItem(member.equipmentRuntime.offHand);
        updateTimedEquippedItem(member.equipmentRuntime.mainHand);
        updateTimedEquippedItem(member.equipmentRuntime.bow);
        updateTimedEquippedItem(member.equipmentRuntime.armor);
        updateTimedEquippedItem(member.equipmentRuntime.helm);
        updateTimedEquippedItem(member.equipmentRuntime.belt);
        updateTimedEquippedItem(member.equipmentRuntime.cloak);
        updateTimedEquippedItem(member.equipmentRuntime.gauntlets);
        updateTimedEquippedItem(member.equipmentRuntime.boots);
        updateTimedEquippedItem(member.equipmentRuntime.amulet);
        updateTimedEquippedItem(member.equipmentRuntime.ring1);
        updateTimedEquippedItem(member.equipmentRuntime.ring2);
        updateTimedEquippedItem(member.equipmentRuntime.ring3);
        updateTimedEquippedItem(member.equipmentRuntime.ring4);
        updateTimedEquippedItem(member.equipmentRuntime.ring5);
        updateTimedEquippedItem(member.equipmentRuntime.ring6);

        for (std::optional<LloydBeacon> &beacon : member.lloydsBeacons)
        {
            if (!beacon.has_value())
            {
                continue;
            }

            beacon->remainingSeconds = std::max(0.0f, beacon->remainingSeconds - deltaSeconds);

            if (beacon->remainingSeconds <= 0.0f)
            {
                beacon.reset();
            }
        }
    }

    if (buffsChanged || itemsChanged)
    {
        rebuildMagicalBonusesFromBuffs();
    }

    if (!canSelectMemberInGameplay(m_activeMemberIndex))
    {
        switchToNextReadyMember();
    }
}

void Party::updateRecovery(float deltaSeconds, float progressScale)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    const float clampedProgressScale = std::max(0.0f, progressScale);

    for (Character &member : m_members)
    {
        const float recoveryDelta =
            deltaSeconds * clampedProgressScale * std::max(0.0f, member.recoveryProgressMultiplier);
        member.recoverySecondsRemaining = std::max(0.0f, member.recoverySecondsRemaining - recoveryDelta);

        if (member.healthRegenPerSecond > 0.0f)
        {
            member.healthRegenAccumulator += member.healthRegenPerSecond * deltaSeconds;
            const int healAmount = std::max(0, static_cast<int>(member.healthRegenAccumulator));

            if (healAmount > 0)
            {
                member.healthRegenAccumulator -= static_cast<float>(healAmount);
                member.health = std::min(currentMaximumHealth(member), member.health + healAmount);
            }
        }

        if (member.spellRegenPerSecond > 0.0f)
        {
            member.spellRegenAccumulator += member.spellRegenPerSecond * deltaSeconds;
            const int spellAmount = std::max(0, static_cast<int>(member.spellRegenAccumulator));

            if (spellAmount > 0)
            {
                member.spellRegenAccumulator -= static_cast<float>(spellAmount);
                member.spellPoints = std::min(currentMaximumSpellPoints(member), member.spellPoints + spellAmount);
            }
        }
    }
}

bool Party::applyRecoveryToMember(size_t memberIndex, float recoverySeconds)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->recoverySecondsRemaining = std::max(pMember->recoverySecondsRemaining, std::max(0.0f, recoverySeconds));
    return true;
}

bool Party::applyRecoveryToActiveMember(float recoverySeconds)
{
    return applyRecoveryToMember(m_activeMemberIndex, recoverySeconds);
}

bool Party::switchToNextReadyMember()
{
    if (m_members.empty())
    {
        return false;
    }

    const size_t currentIndex = std::min(m_activeMemberIndex, m_members.size() - 1);

    for (size_t offset = 1; offset <= m_members.size(); ++offset)
    {
        const size_t candidateIndex = (currentIndex + offset) % m_members.size();

        const Character *pCandidate = member(candidateIndex);

        if (pCandidate != nullptr && GameMechanics::canTakeGameplayAction(*pCandidate))
        {
            m_activeMemberIndex = candidateIndex;
            return true;
        }
    }

    return false;
}

void Party::applyPartyBuff(
    PartyBuffId buffId,
    float durationSeconds,
    int power,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    uint32_t casterMemberIndex)
{
    PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(buffId)];
    buff.remainingSeconds = std::max(buff.remainingSeconds, std::max(0.0f, durationSeconds));
    buff.spellId = spellId;
    buff.skillLevel = skillLevel;
    buff.skillMastery = skillMastery;
    buff.power = power;
    buff.casterMemberIndex = casterMemberIndex;
    rebuildMagicalBonusesFromBuffs();
}

void Party::applyCharacterBuff(
    size_t memberIndex,
    CharacterBuffId buffId,
    float durationSeconds,
    int power,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    uint32_t casterMemberIndex)
{
    if (memberIndex >= m_members.size() || memberIndex >= m_characterBuffs.size())
    {
        return;
    }

    CharacterBuffState &buff = m_characterBuffs[memberIndex][static_cast<size_t>(buffId)];
    buff.remainingSeconds = std::max(buff.remainingSeconds, std::max(0.0f, durationSeconds));
    buff.spellId = spellId;
    buff.skillLevel = skillLevel;
    buff.skillMastery = skillMastery;
    buff.power = power;
    buff.casterMemberIndex = casterMemberIndex;
    rebuildMagicalBonusesFromBuffs();
}

void Party::clearPartyBuff(PartyBuffId buffId)
{
    m_partyBuffs[static_cast<size_t>(buffId)] = {};
    rebuildMagicalBonusesFromBuffs();
}

void Party::clearCharacterBuff(size_t memberIndex, CharacterBuffId buffId)
{
    if (memberIndex >= m_members.size() || memberIndex >= m_characterBuffs.size())
    {
        return;
    }

    m_characterBuffs[memberIndex][static_cast<size_t>(buffId)] = {};
    rebuildMagicalBonusesFromBuffs();
}

bool Party::clearDispellableBuffs()
{
    bool cleared = false;

    for (PartyBuffId buffId : {
             PartyBuffId::TorchLight,
             PartyBuffId::WizardEye,
             PartyBuffId::FeatherFall,
             PartyBuffId::DetectLife,
             PartyBuffId::WaterWalk,
             PartyBuffId::Fly,
             PartyBuffId::Invisibility,
             PartyBuffId::Stoneskin,
             PartyBuffId::DayOfGods,
             PartyBuffId::ProtectionFromMagic,
             PartyBuffId::FireResistance,
             PartyBuffId::WaterResistance,
             PartyBuffId::AirResistance,
             PartyBuffId::EarthResistance,
             PartyBuffId::MindResistance,
             PartyBuffId::BodyResistance,
             PartyBuffId::Shield,
             PartyBuffId::Heroism,
             PartyBuffId::Haste,
             PartyBuffId::Immolation})
    {
        const size_t buffIndex = static_cast<size_t>(buffId);
        cleared = m_partyBuffs[buffIndex].active() || cleared;
        m_partyBuffs[buffIndex] = {};
    }

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        for (CharacterBuffId buffId : {
                 CharacterBuffId::Bless,
                 CharacterBuffId::Fate,
                 CharacterBuffId::Preservation,
                 CharacterBuffId::Regeneration,
                 CharacterBuffId::Hammerhands,
                 CharacterBuffId::PainReflection})
        {
            const size_t buffIndex = static_cast<size_t>(buffId);
            cleared = m_characterBuffs[memberIndex][buffIndex].active() || cleared;
            m_characterBuffs[memberIndex][buffIndex] = {};
        }
    }

    if (cleared)
    {
        rebuildMagicalBonusesFromBuffs();
    }

    return cleared;
}

bool Party::hasDispellableBuffs() const
{
    for (PartyBuffId buffId : {
             PartyBuffId::TorchLight,
             PartyBuffId::WizardEye,
             PartyBuffId::FeatherFall,
             PartyBuffId::DetectLife,
             PartyBuffId::WaterWalk,
             PartyBuffId::Fly,
             PartyBuffId::Invisibility,
             PartyBuffId::Stoneskin,
             PartyBuffId::DayOfGods,
             PartyBuffId::ProtectionFromMagic,
             PartyBuffId::FireResistance,
             PartyBuffId::WaterResistance,
             PartyBuffId::AirResistance,
             PartyBuffId::EarthResistance,
             PartyBuffId::MindResistance,
             PartyBuffId::BodyResistance,
             PartyBuffId::Shield,
             PartyBuffId::Heroism,
             PartyBuffId::Haste,
             PartyBuffId::Immolation})
    {
        if (m_partyBuffs[static_cast<size_t>(buffId)].active())
        {
            return true;
        }
    }

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        for (CharacterBuffId buffId : {
                 CharacterBuffId::Bless,
                 CharacterBuffId::Fate,
                 CharacterBuffId::Preservation,
                 CharacterBuffId::Regeneration,
                 CharacterBuffId::Hammerhands,
                 CharacterBuffId::PainReflection})
        {
            if (m_characterBuffs[memberIndex][static_cast<size_t>(buffId)].active())
            {
                return true;
            }
        }
    }

    return false;
}

bool Party::hasPartyBuff(PartyBuffId buffId) const
{
    return m_partyBuffs[static_cast<size_t>(buffId)].active();
}

bool Party::hasCharacterBuff(size_t memberIndex, CharacterBuffId buffId) const
{
    return characterBuff(memberIndex, buffId) != nullptr;
}

const PartyBuffState *Party::partyBuff(PartyBuffId buffId) const
{
    const PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(buffId)];
    return buff.active() ? &buff : nullptr;
}

const CharacterBuffState *Party::characterBuff(size_t memberIndex, CharacterBuffId buffId) const
{
    if (memberIndex >= m_members.size() || memberIndex >= m_characterBuffs.size())
    {
        return nullptr;
    }

    const CharacterBuffState &buff = m_characterBuffs[memberIndex][static_cast<size_t>(buffId)];
    return buff.active() ? &buff : nullptr;
}

bool Party::blockConditionWithProtectionFromMagic(CharacterCondition condition)
{
    if (!conditionAffectedByProtectionFromMagic(condition))
    {
        return false;
    }

    PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(PartyBuffId::ProtectionFromMagic)];

    if (!buff.active() || buff.power <= 0)
    {
        return false;
    }

    if (conditionRequiresGrandmasterProtectionFromMagic(condition)
        && buff.skillMastery < SkillMastery::Grandmaster)
    {
        return false;
    }

    --buff.power;

    if (buff.power < 1)
    {
        buff = {};
    }

    rebuildMagicalBonusesFromBuffs();
    return true;
}

bool Party::clearMemberCondition(size_t memberIndex, CharacterCondition condition)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->conditions.reset(static_cast<size_t>(condition));
    pMember->conditionStartGameMinutes[static_cast<size_t>(condition)] = 0.0f;
    return true;
}

bool Party::applyMemberCondition(size_t memberIndex, CharacterCondition condition, float gameMinutes)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || hasConditionImmunity(*pMember, condition))
    {
        return false;
    }

    const bool alreadyHadCondition = pMember->conditions.test(static_cast<size_t>(condition));
    pMember->conditions.set(static_cast<size_t>(condition));

    if (!alreadyHadCondition)
    {
        pMember->conditionStartGameMinutes[static_cast<size_t>(condition)] = std::max(0.0f, gameMinutes);

        switch (condition)
        {
            case CharacterCondition::Drunk:
                queueSpeech(memberIndex, SpeechId::Drunk);
                break;

            case CharacterCondition::Insane:
                queueSpeech(memberIndex, SpeechId::Insane);
                break;

            case CharacterCondition::Cursed:
                queueSpeech(memberIndex, SpeechId::Cursed);
                break;

            case CharacterCondition::Fear:
                queueSpeech(memberIndex, SpeechId::AfraidSilent);
                break;

            default:
                break;
        }
    }

    return true;
}

bool Party::hasMemberConditionImmunity(size_t memberIndex, CharacterCondition condition) const
{
    const Character *pMember = member(memberIndex);
    return pMember != nullptr && hasConditionImmunity(*pMember, condition);
}

bool Party::healMember(size_t memberIndex, int amount)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || amount <= 0)
    {
        return false;
    }

    const int maxHealth = effectiveMaximumHealth(*pMember);
    const int previousHealth = pMember->health;
    pMember->health = std::clamp(pMember->health + amount, 0, maxHealth);
    updateMemberIncapacitatedCondition(
        *pMember,
        m_characterBuffs[memberIndex][static_cast<size_t>(CharacterBuffId::Preservation)].active());
    return pMember->health > previousHealth;
}

bool Party::reviveMember(size_t memberIndex, int health, bool applyWeak)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Unconscious)] = 0.0f;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Dead)] = 0.0f;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Petrified));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Petrified)] = 0.0f;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Eradicated));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Eradicated)] = 0.0f;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Zombie));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Zombie)] = 0.0f;
    pMember->health = std::max(1, health);

    if (applyWeak)
    {
        applyMemberCondition(memberIndex, CharacterCondition::Weak);
    }

    return true;
}

const Character *Party::activeMember() const
{
    if (m_members.empty())
    {
        return nullptr;
    }

    return &m_members[std::min(m_activeMemberIndex, m_members.size() - 1)];
}

Character *Party::activeMember()
{
    if (m_members.empty())
    {
        return nullptr;
    }

    return &m_members[std::min(m_activeMemberIndex, m_members.size() - 1)];
}

size_t Party::activeMemberIndex() const
{
    return m_members.empty() ? 0 : std::min(m_activeMemberIndex, m_members.size() - 1);
}

int Party::totalHealth() const
{
    int totalHealth = 0;

    for (const Character &member : m_members)
    {
        totalHealth += member.health;
    }

    return totalHealth;
}

int Party::totalMaxHealth() const
{
    int totalMaxHealth = 0;

    for (const Character &member : m_members)
    {
        totalMaxHealth += currentMaximumHealth(member);
    }

    return totalMaxHealth;
}

int Party::gold() const
{
    return m_gold;
}

int Party::bankGold() const
{
    return m_bankGold;
}

int Party::food() const
{
    return m_food;
}

uint32_t Party::houseStockSeed() const
{
    return m_houseStockSeed;
}

bool Party::hasFoundArtifactItem(uint32_t itemId) const
{
    return itemId != 0 && m_foundArtifactItems.contains(itemId);
}

void Party::markArtifactItemFound(uint32_t itemId)
{
    if (itemId != 0)
    {
        m_foundArtifactItems.insert(itemId);
    }
}

void Party::clearFoundArtifactItems()
{
    m_foundArtifactItems.clear();
}

bool Party::hasArcomageWinAt(uint32_t houseId) const
{
    return houseId != 0 && m_arcomageWonHouseIds.contains(houseId);
}

void Party::recordArcomageWin(uint32_t houseId, int goldReward, uint32_t firstWinAwardId)
{
    ++m_arcomageWinCount;

    if (houseId != 0 && m_arcomageWonHouseIds.insert(houseId).second)
    {
        if (goldReward > 0)
        {
            addGold(goldReward);
        }

        if (firstWinAwardId != 0)
        {
            addAward(firstWinAwardId);
        }

        if (m_arcomageWonHouseIds.size() >= ArcomageTavernCount)
        {
            addAward(ArcomageChampionAwardId);
        }

        if (hasWonAllMm7ArcomageTaverns(m_arcomageWonHouseIds))
        {
            setQuestBit(Mm7ArcomageChampionQBit, true);
        }
    }
}

void Party::recordArcomageLoss()
{
    ++m_arcomageLossCount;
}

uint32_t Party::arcomageWinCount() const
{
    return m_arcomageWinCount;
}

uint32_t Party::arcomageLossCount() const
{
    return m_arcomageLossCount;
}

Party::HouseStockState *Party::houseStockState(uint32_t houseId)
{
    const std::unordered_map<uint32_t, HouseStockState>::iterator stateIt = m_houseStockStates.find(houseId);
    return stateIt != m_houseStockStates.end() ? &stateIt->second : nullptr;
}

const Party::HouseStockState *Party::houseStockState(uint32_t houseId) const
{
    const std::unordered_map<uint32_t, HouseStockState>::const_iterator stateIt = m_houseStockStates.find(houseId);
    return stateIt != m_houseStockStates.end() ? &stateIt->second : nullptr;
}

Party::HouseStockState &Party::ensureHouseStockState(uint32_t houseId)
{
    HouseStockState &state = m_houseStockStates[houseId];
    state.houseId = houseId;
    return state;
}

void Party::clearHouseStockStates()
{
    m_houseStockStates.clear();
}

size_t Party::inventoryItemCount() const
{
    size_t itemCount = 0;

    for (const Character &member : m_members)
    {
        itemCount += member.inventoryItemCount();
    }

    return itemCount;
}

size_t Party::usedInventoryCells() const
{
    size_t usedCells = 0;

    for (const Character &member : m_members)
    {
        usedCells += member.usedInventoryCells();
    }

    return usedCells;
}

size_t Party::inventoryCapacity() const
{
    size_t capacity = 0;

    for (const Character &member : m_members)
    {
        capacity += member.inventoryCapacity();
    }

    return capacity;
}

uint32_t Party::waterDamageTicks() const
{
    return m_waterDamageTicks;
}

uint32_t Party::burningDamageTicks() const
{
    return m_burningDamageTicks;
}

uint32_t Party::splashCount() const
{
    return m_splashCount;
}

uint32_t Party::landingSoundCount() const
{
    return m_landingSoundCount;
}

uint32_t Party::hardLandingSoundCount() const
{
    return m_hardLandingSoundCount;
}

float Party::lastFallDamageDistance() const
{
    return m_lastFallDamageDistance;
}

const std::string &Party::lastStatus() const
{
    return m_lastStatus;
}

const std::vector<Party::PendingAudioRequest> &Party::pendingAudioRequests() const
{
    return m_pendingAudioRequests;
}

void Party::clearPendingAudioRequests()
{
    m_pendingAudioRequests.clear();
}

void Party::queueSound(SoundId soundId)
{
    if (soundId == SoundId::None)
    {
        return;
    }

    PendingAudioRequest request = {};
    request.kind = PendingAudioRequest::Kind::Sound;
    request.soundId = soundId;
    m_pendingAudioRequests.push_back(request);
}

void Party::queueSpeech(size_t memberIndex, SpeechId speechId)
{
    if (speechId == SpeechId::None || memberIndex >= m_members.size())
    {
        return;
    }

    PendingAudioRequest request = {};
    request.kind = PendingAudioRequest::Kind::Speech;
    request.speechId = speechId;
    request.memberIndex = memberIndex;
    m_pendingAudioRequests.push_back(request);
}

SoundId Party::resolveDamageImpactSoundForMember(size_t memberIndex) const
{
    if (memberIndex >= m_members.size() || m_pItemTable == nullptr)
    {
        return SoundId::DullStrike;
    }

    const std::optional<InventoryItem> armor = equippedItem(memberIndex, EquipmentSlot::Armor);

    if (!armor.has_value())
    {
        return SoundId::DullStrike;
    }

    const ItemDefinition *pArmorDefinition = m_pItemTable->get(armor->objectDescriptionId);

    if (pArmorDefinition == nullptr)
    {
        return SoundId::DullStrike;
    }

    if (pArmorDefinition->skillGroup == "Chain")
    {
        static constexpr std::array<SoundId, 4> MetalArmorSounds = {
            SoundId::MetalArmorStrike01,
            SoundId::MetalArmorStrike02,
            SoundId::MetalArmorStrike03,
            SoundId::MetalVsMetal01,
        };
        return pickRandomSoundId(MetalArmorSounds);
    }

    if (pArmorDefinition->skillGroup == "Plate")
    {
        static constexpr std::array<SoundId, 4> PlateArmorSounds = {
            SoundId::MetalArmorStrike03,
            SoundId::MetalArmorStrike02,
            SoundId::MetalArmorStrike01,
            SoundId::MetalVsMetal01,
        };
        return pickRandomSoundId(PlateArmorSounds);
    }

    static constexpr std::array<SoundId, 4> DullArmorSounds = {
        SoundId::DullArmorStrike01,
        SoundId::DullArmorStrike02,
        SoundId::DullArmorStrike03,
        SoundId::DullStrike,
    };
    return pickRandomSoundId(DullArmorSounds);
}

void Party::rebuildMagicalBonusesFromBuffs()
{
    for (Character &member : m_members)
    {
        member.magicalBonuses = {};
        member.magicalImmunities = {};
        member.magicalConditionImmunities = {};
        member.merchantBonus = 0;
        member.weaponEnchantmentDamageBonus = 0;
        member.vampiricHealFraction = 0.0f;
        member.physicalAttackDisabled = false;
        member.physicalDamageImmune = false;
        member.halfMissileDamage = false;
        member.waterWalking = false;
        member.featherFalling = false;
        member.healthRegenPerSecond = 0.0f;
        member.spellRegenPerSecond = 0.0f;
        member.healthRegenAccumulator = 0.0f;
        member.spellRegenAccumulator = 0.0f;
        member.attackRecoveryReductionTicks = 0;
        member.recoveryProgressMultiplier = 1.0f;
        member.itemSkillBonuses.clear();
    }

    for (Character &member : m_members)
    {
        member.healthRegenPerSecond += regenerationSkillHealthPerSecond(member);
    }

    const auto applyResistanceBonus =
        [this](PartyBuffId buffId, auto CharacterResistanceSet::*field)
        {
            const PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(buffId)];

            if (!buff.active())
            {
                return;
            }

            for (Character &member : m_members)
            {
                member.magicalBonuses.resistances.*field += buff.power;
            }
        };

    applyResistanceBonus(PartyBuffId::FireResistance, &CharacterResistanceSet::fire);
    applyResistanceBonus(PartyBuffId::WaterResistance, &CharacterResistanceSet::water);
    applyResistanceBonus(PartyBuffId::AirResistance, &CharacterResistanceSet::air);
    applyResistanceBonus(PartyBuffId::EarthResistance, &CharacterResistanceSet::earth);
    applyResistanceBonus(PartyBuffId::MindResistance, &CharacterResistanceSet::mind);
    applyResistanceBonus(PartyBuffId::BodyResistance, &CharacterResistanceSet::body);

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::Stoneskin))
    {
        for (Character &member : m_members)
        {
            member.magicalBonuses.armorClass += pBuff->power;
        }
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::Heroism))
    {
        for (Character &member : m_members)
        {
            member.magicalBonuses.meleeDamage += pBuff->power;
            member.magicalBonuses.rangedDamage += pBuff->power;
        }
    }

    if (partyBuff(PartyBuffId::Haste) != nullptr)
    {
        for (Character &member : m_members)
        {
            member.attackRecoveryReductionTicks += 25;
        }
    }

    if (partyBuff(PartyBuffId::Shield) != nullptr)
    {
        for (Character &member : m_members)
        {
            member.halfMissileDamage = true;
        }
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::DayOfGods))
    {
        for (Character &member : m_members)
        {
            member.magicalBonuses.might += pBuff->power;
            member.magicalBonuses.intellect += pBuff->power;
            member.magicalBonuses.personality += pBuff->power;
            member.magicalBonuses.endurance += pBuff->power;
            member.magicalBonuses.speed += pBuff->power;
            member.magicalBonuses.accuracy += pBuff->power;
            member.magicalBonuses.luck += pBuff->power;
        }
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::ProtectionFromMagic))
    {
        for (Character &member : m_members)
        {
            member.magicalBonuses.resistances.fire += pBuff->power;
            member.magicalBonuses.resistances.air += pBuff->power;
            member.magicalBonuses.resistances.water += pBuff->power;
            member.magicalBonuses.resistances.earth += pBuff->power;
            member.magicalBonuses.resistances.mind += pBuff->power;
            member.magicalBonuses.resistances.body += pBuff->power;
            member.magicalBonuses.resistances.spirit += pBuff->power;
        }
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::Glamour))
    {
        for (Character &member : m_members)
        {
            member.merchantBonus += pBuff->power;
        }
    }

    for (size_t memberIndex = 0; memberIndex < m_members.size() && memberIndex < m_characterBuffs.size(); ++memberIndex)
    {
        Character &member = m_members[memberIndex];

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::Bless))
        {
            member.magicalBonuses.meleeAttack += pBuff->power;
            member.magicalBonuses.rangedAttack += pBuff->power;
        }

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::Fate))
        {
            member.magicalBonuses.meleeAttack += pBuff->power;
            member.magicalBonuses.rangedAttack += pBuff->power;
        }

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::Hammerhands))
        {
            member.magicalBonuses.meleeDamage += pBuff->power;
        }

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::Mistform))
        {
            static_cast<void>(pBuff);
            member.physicalAttackDisabled = true;
            member.physicalDamageImmune = true;
        }

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::Glamour))
        {
            member.merchantBonus += pBuff->power;
        }
    }

    const auto applyEquippedItemEnchant =
        [this](Character &member, uint32_t itemId, const EquippedItemRuntimeState &runtimeState)
        {
            if (itemId == 0 || runtimeState.broken)
            {
                return;
            }

            const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

            if (pItemDefinition == nullptr)
            {
                return;
            }

            ItemEnchantRuntime::applyEquippedEnchantEffects(
                *pItemDefinition,
                runtimeState,
                m_pStandardItemEnchantTable,
                m_pSpecialItemEnchantTable,
                member);
        };

    if (m_pItemTable != nullptr)
    {
        for (Character &member : m_members)
        {
            if (member.equipment.offHand != 0 && !member.equipmentRuntime.offHand.broken)
            {
                const ItemDefinition *pOffHand = m_pItemTable->get(member.equipment.offHand);
                const CharacterSkill *pShieldSkill = member.findSkill("Shield");

                if (pOffHand != nullptr
                    && pOffHand->skillGroup == "Shield"
                    && pShieldSkill != nullptr
                    && pShieldSkill->mastery >= SkillMastery::Grandmaster)
                {
                    member.halfMissileDamage = true;
                }
            }

            applyEquippedItemEnchant(member, member.equipment.offHand, member.equipmentRuntime.offHand);
            applyEquippedItemEnchant(member, member.equipment.mainHand, member.equipmentRuntime.mainHand);
            applyEquippedItemEnchant(member, member.equipment.bow, member.equipmentRuntime.bow);
            applyEquippedItemEnchant(member, member.equipment.armor, member.equipmentRuntime.armor);
            applyEquippedItemEnchant(member, member.equipment.helm, member.equipmentRuntime.helm);
            applyEquippedItemEnchant(member, member.equipment.belt, member.equipmentRuntime.belt);
            applyEquippedItemEnchant(member, member.equipment.cloak, member.equipmentRuntime.cloak);
            applyEquippedItemEnchant(member, member.equipment.gauntlets, member.equipmentRuntime.gauntlets);
            applyEquippedItemEnchant(member, member.equipment.boots, member.equipmentRuntime.boots);
            applyEquippedItemEnchant(member, member.equipment.amulet, member.equipmentRuntime.amulet);
            applyEquippedItemEnchant(member, member.equipment.ring1, member.equipmentRuntime.ring1);
            applyEquippedItemEnchant(member, member.equipment.ring2, member.equipmentRuntime.ring2);
            applyEquippedItemEnchant(member, member.equipment.ring3, member.equipmentRuntime.ring3);
            applyEquippedItemEnchant(member, member.equipment.ring4, member.equipmentRuntime.ring4);
            applyEquippedItemEnchant(member, member.equipment.ring5, member.equipmentRuntime.ring5);
            applyEquippedItemEnchant(member, member.equipment.ring6, member.equipmentRuntime.ring6);
        }
    }

    for (Character &member : m_members)
    {
        applyMagicalPrimaryStatResourceBonuses(member, m_pClassMultiplierTable);
        clampCurrentResourcesToMaximum(member);
    }
}

void Party::applyDefaultStartingSkills(Character &member) const
{
    if (m_pClassSkillTable == nullptr)
    {
        return;
    }

    const std::vector<CharacterSkill> defaultSkills =
        m_pClassSkillTable->getDefaultSkillsForCharacter(member.className, member.raceId);

    for (const CharacterSkill &skill : defaultSkills)
    {
        member.skills[skill.name] = skill;
    }
}

void Party::markArtifactItemFoundIfRelevant(const InventoryItem &item)
{
    if (item.objectDescriptionId == 0)
    {
        return;
    }

    if (item.artifactId != 0)
    {
        markArtifactItemFound(item.artifactId);
        return;
    }

    if (m_pItemTable == nullptr)
    {
        return;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(item.objectDescriptionId);

    if (pItemDefinition == nullptr || !ItemRuntime::isUniquelyGeneratedRareItem(*pItemDefinition))
    {
        return;
    }

    markArtifactItemFound(pItemDefinition->itemId);
}

void Party::recordEverOwnedItemIfRelevant(const InventoryItem &item)
{
    recordEverOwnedItem(item.objectDescriptionId);
}

void Party::recordEverOwnedItemsFromCurrentState()
{
    static constexpr EquipmentSlot EquipmentSlots[] = {
        EquipmentSlot::OffHand,
        EquipmentSlot::MainHand,
        EquipmentSlot::Bow,
        EquipmentSlot::Armor,
        EquipmentSlot::Helm,
        EquipmentSlot::Belt,
        EquipmentSlot::Cloak,
        EquipmentSlot::Gauntlets,
        EquipmentSlot::Boots,
        EquipmentSlot::Amulet,
        EquipmentSlot::Ring1,
        EquipmentSlot::Ring2,
        EquipmentSlot::Ring3,
        EquipmentSlot::Ring4,
        EquipmentSlot::Ring5,
        EquipmentSlot::Ring6,
    };

    for (const Character &member : m_members)
    {
        for (const InventoryItem &item : member.inventory)
        {
            recordEverOwnedItemIfRelevant(item);
        }

        for (EquipmentSlot slot : EquipmentSlots)
        {
            recordEverOwnedItem(::OpenYAMM::Game::equippedItemId(member.equipment, slot));
        }
    }
}
}
