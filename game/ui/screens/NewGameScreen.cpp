#include "game/ui/screens/NewGameScreen.h"

#include "game/audio/GameAudioSystem.h"
#include "game/audio/SoundIds.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameMechanics.h"
#include "game/party/SkillData.h"
#include "game/party/SpeechIds.h"

#include <algorithm>
#include <array>
#include <cassert>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <optional>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
using StatId = NewGameScreen::StatId;
using CreationCandidate = NewGameScreen::CreationCandidate;

constexpr float RootWidth = 640.0f;
constexpr float RootHeight = 480.0f;
constexpr const char *CharacterCreationLayoutPath = "Data/ui/gameplay/character_creation.yml";
constexpr const char *ContinentSelectionLayoutPath = "Data/ui/gameplay/continent_selection.yml";
constexpr const char *PcNamesTablePath = "engine/data_tables/english/pc_names.txt";
constexpr uint32_t DefaultCreationCharacterDataId = 1;
constexpr const char *DefaultCreationClassName = "Knight";
constexpr const char *DefaultNewGameContinentKey = "jadame";
constexpr uint32_t DebugGodLichCharacterDataId = 27;
constexpr uint32_t CharacterCreationVoicePreviewSpeakerKey = 0x43525650u;
constexpr int StartingBonusPool = 15;
constexpr int NeutralBaseStatValue = 11;
constexpr int MinimumStatOffset = 2;
constexpr int MaximumStatValue = 25;
constexpr int BoostedMaximumStatValue = 34;
constexpr float InspectPopupWidth = 425.0f;
constexpr float InspectPopupGap = 12.0f;
constexpr float NameBackspaceInitialRepeatDelaySeconds = 0.35f;
constexpr float NameBackspaceRepeatIntervalSeconds = 0.065f;
constexpr float CreationCompletionErrorDurationSeconds = 4.0f;
constexpr float CreationCompletionErrorBoxX = 140.0f;
constexpr float CreationCompletionErrorBoxWidth = 360.0f;
constexpr size_t MaximumOptionalSkillSelections = 2;
constexpr size_t MaximumNameLength = 15;
constexpr const char *CreationCompletionErrorText =
    "Create Party cannot be completed unless you have assigned all characters 2 extra skills and have spent all of "
    "your bonus points.";
constexpr uint32_t WhiteColor = 0xffffffffu;
constexpr uint32_t YellowColor = 0xff00ffffu;
constexpr uint32_t BlueColor = 0xffffd830u;
constexpr uint32_t GreenColor = 0xff00ff00u;
constexpr uint32_t RedColor = 0xff0000ffu;
constexpr uint32_t InspectTitleColor = 0xff9bffffu;

struct RaceStatRule
{
    int baseStep = 1;
    int droppedStep = 1;
    int maximumValue = MaximumStatValue;
};

struct DebugEquipmentItem
{
    uint32_t CharacterEquipment::*pItemId = &CharacterEquipment::mainHand;
    EquippedItemRuntimeState CharacterEquipmentRuntimeState::*pRuntimeState = &CharacterEquipmentRuntimeState::mainHand;
    uint32_t itemId = 0;
};

struct SkillSlotPosition
{
    float x = 0.0f;
    float y = 0.0f;
};

struct ResolvedLayoutElement
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    float scale = 1.0f;
};

constexpr std::array<const char *, static_cast<size_t>(StatId::Count)> StatLabels = {
    "Might",
    "Intellect",
    "Personality",
    "Endurance",
    "Accuracy",
    "Speed",
    "Luck",
};

const CreationCandidate DebugGodLichCandidate = {
    DebugGodLichCharacterDataId,
    45,
    0,
    "God",
    "Lich",
    "Human",
    {},
    true,
    {11, 11, 11, 11, 11, 11, 11},
    {{"", ""}},
};

constexpr std::array<DebugEquipmentItem, 11> DebugGodLichEquipment = {{
    {&CharacterEquipment::mainHand, &CharacterEquipmentRuntimeState::mainHand, 527},   // Spiritslayer
    {&CharacterEquipment::offHand, &CharacterEquipmentRuntimeState::offHand, 534},     // Herondale's Lost Shield
    {&CharacterEquipment::bow, &CharacterEquipmentRuntimeState::bow, 531},             // Tournament Bow
    {&CharacterEquipment::armor, &CharacterEquipmentRuntimeState::armor, 515},         // Supreme Plate
    {&CharacterEquipment::helm, &CharacterEquipmentRuntimeState::helm, 520},           // Drogg's Helm
    {&CharacterEquipment::belt, &CharacterEquipmentRuntimeState::belt, 537},           // Berserker Belt
    {&CharacterEquipment::cloak, &CharacterEquipmentRuntimeState::cloak, 522},         // Archangel Wings
    {&CharacterEquipment::gauntlets, &CharacterEquipmentRuntimeState::gauntlets, 517}, // Fleetfingers
    {&CharacterEquipment::boots, &CharacterEquipmentRuntimeState::boots, 518},         // Herald's Boots
    {&CharacterEquipment::ring1, &CharacterEquipmentRuntimeState::ring1, 519},         // Ring of Planes
    {&CharacterEquipment::ring2, &CharacterEquipmentRuntimeState::ring2, 535},         // Ring of Fusion
}};

constexpr std::array<SkillSlotPosition, 4> SelectedSkillPositions = {{
    {274.0f, 121.0f},
    {374.0f, 121.0f},
    {274.0f, 154.0f},
    {385.0f, 154.0f},
}};

constexpr std::array<SkillSlotPosition, 9> AvailableSkillPositions = {{
    {295.0f, 252.0f},
    {396.0f, 252.0f},
    {294.0f, 289.0f},
    {397.0f, 289.0f},
    {302.0f, 325.0f},
    {385.0f, 323.0f},
    {292.0f, 353.0f},
    {395.0f, 353.0f},
    {323.0f, 385.0f},
}};

constexpr std::array<float, static_cast<size_t>(StatId::Count)> StatValueY = {{
    295.0f, 320.0f, 345.0f, 370.0f, 395.0f, 420.0f, 445.0f
}};

constexpr std::array<const char *, static_cast<size_t>(StatId::Count)> StatLabelLayoutIds = {{
    "CharacterCreationMightLabel",
    "CharacterCreationIntellectLabel",
    "CharacterCreationPersonalityLabel",
    "CharacterCreationEnduranceLabel",
    "CharacterCreationAccuracyLabel",
    "CharacterCreationSpeedLabel",
    "CharacterCreationLuckLabel",
}};

constexpr std::array<const char *, static_cast<size_t>(StatId::Count)> StatMinusButtonLayoutIds = {{
    "CharacterCreationMightMinusButton",
    "CharacterCreationIntellectMinusButton",
    "CharacterCreationPersonalityMinusButton",
    "CharacterCreationEnduranceMinusButton",
    "CharacterCreationAccuracyMinusButton",
    "CharacterCreationSpeedMinusButton",
    "CharacterCreationLuckMinusButton",
}};

constexpr std::array<const char *, static_cast<size_t>(StatId::Count)> StatValueLayoutIds = {{
    "CharacterCreationMightValue",
    "CharacterCreationIntellectValue",
    "CharacterCreationPersonalityValue",
    "CharacterCreationEnduranceValue",
    "CharacterCreationAccuracyValue",
    "CharacterCreationSpeedValue",
    "CharacterCreationLuckValue",
}};

constexpr std::array<const char *, static_cast<size_t>(StatId::Count)> StatPlusButtonLayoutIds = {{
    "CharacterCreationMightPlusButton",
    "CharacterCreationIntellectPlusButton",
    "CharacterCreationPersonalityPlusButton",
    "CharacterCreationEndurancePlusButton",
    "CharacterCreationAccuracyPlusButton",
    "CharacterCreationSpeedPlusButton",
    "CharacterCreationLuckPlusButton",
}};

constexpr std::array<const char *, 4> SelectedSkillLayoutIds = {{
    "CharacterCreationSelectedSkill01",
    "CharacterCreationSelectedSkill02",
    "CharacterCreationSelectedSkill03",
    "CharacterCreationSelectedSkill04",
}};

constexpr std::array<const char *, 9> AvailableSkillLayoutIds = {{
    "CharacterCreationAvailableSkill01",
    "CharacterCreationAvailableSkill02",
    "CharacterCreationAvailableSkill03",
    "CharacterCreationAvailableSkill04",
    "CharacterCreationAvailableSkill05",
    "CharacterCreationAvailableSkill06",
    "CharacterCreationAvailableSkill07",
    "CharacterCreationAvailableSkill08",
    "CharacterCreationAvailableSkill09",
}};

constexpr std::array<const char *, 5> PartySlotButtonLayoutIds = {{
    "CharacterCreationPartySlot1Button",
    "CharacterCreationPartySlot2Button",
    "CharacterCreationPartySlot3Button",
    "CharacterCreationPartySlot4Button",
    "CharacterCreationPartySlot5Button",
}};

constexpr std::array<const char *, 39> OrderedSkillNames = {{
    "Staff",
    "Sword",
    "Dagger",
    "Axe",
    "Spear",
    "Bow",
    "Mace",
    "Blaster",
    "Shield",
    "LeatherArmor",
    "ChainArmor",
    "PlateArmor",
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
    "DragonAbility",
    "IdentifyItem",
    "Merchant",
    "RepairItem",
    "Bodybuilding",
    "Meditation",
    "Perception",
    "Regeneration",
    "DisarmTraps",
    "Dodging",
    "Unarmed",
    "IdentifyMonster",
    "Armsmaster",
    "Stealing",
    "Alchemy",
    "Learning",
}};

std::string trimCopy(const std::string &value)
{
    size_t start = 0;

    while (start < value.size() && std::isspace(static_cast<unsigned char>(value[start])) != 0)
    {
        ++start;
    }

    size_t end = value.size();

    while (end > start && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(start, end - start);
}

std::string canonicalNameToken(const std::string &value)
{
    std::string token;

    for (unsigned char character : value)
    {
        if (std::isalnum(character) != 0)
        {
            token.push_back(static_cast<char>(std::tolower(character)));
        }
    }

    return token;
}

std::vector<std::string> splitTabLine(const std::string &line)
{
    std::vector<std::string> cells;
    size_t start = 0;

    while (start <= line.size())
    {
        const size_t end = line.find('\t', start);

        if (end == std::string::npos)
        {
            cells.push_back(line.substr(start));
            break;
        }

        cells.push_back(line.substr(start, end - start));
        start = end + 1;
    }

    return cells;
}

MenuScreenBase::Rect scaledRect(float rootX, float rootY, float scale, float x, float y, float width, float height)
{
    return {
        rootX + x * scale,
        rootY + y * scale,
        width * scale,
        height * scale
    };
}

ResolvedLayoutElement resolveAttachedLayoutRect(
    UiLayoutManager::LayoutAttachMode attachTo,
    const ResolvedLayoutElement &parent,
    float width,
    float height,
    float gapX,
    float gapY,
    float scale)
{
    ResolvedLayoutElement resolved = {};
    resolved.width = width;
    resolved.height = height;
    resolved.scale = scale;

    switch (attachTo)
    {
        case UiLayoutManager::LayoutAttachMode::None:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::RightOf:
            resolved.x = parent.x + parent.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::LeftOf:
            resolved.x = parent.x - resolved.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::Above:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::Below:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + parent.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::CenterAbove:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::CenterBelow:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + parent.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideTopCenter:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideTopLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideTopRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideBottomLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideBottomCenter:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideBottomRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::CenterIn:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;
    }

    return resolved;
}

std::optional<ResolvedLayoutElement> resolveLayoutElementRecursive(
    const UiLayoutManager &layoutManager,
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight,
    std::unordered_set<std::string> &visited)
{
    if (visited.contains(layoutId))
    {
        return std::nullopt;
    }

    visited.insert(layoutId);
    const UiLayoutManager::LayoutElement *pElement = layoutManager.findElement(layoutId);

    if (pElement == nullptr)
    {
        visited.erase(layoutId);
        return std::nullopt;
    }

    const UiLayoutManager::LayoutElement &element = *pElement;
    const float baseScale = std::min(
        static_cast<float>(screenWidth) / RootWidth,
        static_cast<float>(screenHeight) / RootHeight);
    const float viewportWidth = RootWidth * baseScale;
    const float viewportHeight = RootHeight * baseScale;
    const float viewportX = (static_cast<float>(screenWidth) - viewportWidth) * 0.5f;
    const float viewportY = (static_cast<float>(screenHeight) - viewportHeight) * 0.5f;
    ResolvedLayoutElement resolved = {};

    if (!element.parentId.empty())
    {
        const UiLayoutManager::LayoutElement *pParent = layoutManager.findElement(element.parentId);

        if (pParent == nullptr)
        {
            visited.erase(layoutId);
            return std::nullopt;
        }

        const std::optional<ResolvedLayoutElement> parent = resolveLayoutElementRecursive(
            layoutManager,
            element.parentId,
            screenWidth,
            screenHeight,
            pParent->width,
            pParent->height,
            visited);

        if (!parent.has_value())
        {
            visited.erase(layoutId);
            return std::nullopt;
        }

        resolved.scale = element.hasExplicitScale
            ? std::clamp(baseScale, element.minScale, element.maxScale)
            : parent->scale;
        resolved.width = (element.width > 0.0f ? element.width : fallbackWidth) * resolved.scale;
        resolved.height = (element.height > 0.0f ? element.height : fallbackHeight) * resolved.scale;
        resolved = resolveAttachedLayoutRect(
            element.attachTo,
            *parent,
            resolved.width,
            resolved.height,
            element.gapX,
            element.gapY,
            resolved.scale);
        visited.erase(layoutId);
        return resolved;
    }

    resolved.scale = std::clamp(baseScale, element.minScale, element.maxScale);
    resolved.width = (element.width > 0.0f ? element.width : fallbackWidth) * resolved.scale;
    resolved.height = (element.height > 0.0f ? element.height : fallbackHeight) * resolved.scale;

    switch (element.anchor)
    {
        case UiLayoutManager::LayoutAnchor::TopLeft:
            resolved.x = viewportX + element.offsetX * resolved.scale;
            resolved.y = viewportY + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::TopCenter:
            resolved.x = viewportX + viewportWidth * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = viewportY + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::TopRight:
            resolved.x = viewportX + viewportWidth - resolved.width + element.offsetX * resolved.scale;
            resolved.y = viewportY + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::Left:
            resolved.x = viewportX + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::Center:
            resolved.x = viewportX + viewportWidth * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::Right:
            resolved.x = viewportX + viewportWidth - resolved.width + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::BottomLeft:
            resolved.x = viewportX + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight - resolved.height + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::BottomCenter:
            resolved.x = viewportX + viewportWidth * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight - resolved.height + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::BottomRight:
            resolved.x = viewportX + viewportWidth - resolved.width + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight - resolved.height + element.offsetY * resolved.scale;
            break;
    }

    visited.erase(layoutId);
    return resolved;
}

bool containsUnsigned(const std::vector<uint32_t> &values, uint32_t value)
{
    return std::find(values.begin(), values.end(), value) != values.end();
}

bool containsCanonicalClass(const std::vector<std::string> &classNames, const std::string &className)
{
    const std::string canonicalClassNameToFind = canonicalClassName(className);

    for (const std::string &candidate : classNames)
    {
        if (canonicalClassName(candidate) == canonicalClassNameToFind)
        {
            return true;
        }
    }

    return false;
}

bool portraitIsExcepted(
    const CharacterDollEntry &entry,
    const std::vector<std::string> &portraitExceptions)
{
    for (const std::string &exception : portraitExceptions)
    {
        const std::string normalizedException = trimCopy(exception);

        if (normalizedException.empty())
        {
            continue;
        }

        if (normalizedException == std::to_string(entry.id)
            || normalizedException == entry.facePicturesPrefix
            || normalizedException == entry.bodyAsset
            || normalizedException == entry.headAsset)
        {
            return true;
        }
    }

    return false;
}

uint32_t classIdNear(uint32_t currentClassId, const std::vector<uint32_t> &availableClassIds, int direction)
{
    if (availableClassIds.empty())
    {
        return currentClassId;
    }

    if (std::find(availableClassIds.begin(), availableClassIds.end(), currentClassId) != availableClassIds.end())
    {
        return currentClassId;
    }

    if (direction < 0)
    {
        for (std::vector<uint32_t>::const_reverse_iterator it = availableClassIds.rbegin();
             it != availableClassIds.rend();
             ++it)
        {
            if (*it < currentClassId)
            {
                return *it;
            }
        }

        return availableClassIds.back();
    }

    for (uint32_t classId : availableClassIds)
    {
        if (classId > currentClassId)
        {
            return classId;
        }
    }

    return availableClassIds.front();
}

const MergedCharacterSelectionContinent *findNewGameContinent(
    const MergedCharacterSelectionTable &selectionTable,
    const std::string &continentKey)
{
    for (const MergedCharacterSelectionContinent &continent : selectionTable.continents())
    {
        if (continent.key == continentKey)
        {
            return &continent;
        }
    }

    return nullptr;
}

RaceStatRule raceRuleForBaseStat(int baseStatValue)
{
    if (baseStatValue > NeutralBaseStatValue)
    {
        return {2, 1, BoostedMaximumStatValue};
    }

    if (baseStatValue < NeutralBaseStatValue)
    {
        return {1, 2, MaximumStatValue};
    }

    return {1, 1, MaximumStatValue};
}

std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> raceRulesForStats(
    const std::array<int, static_cast<size_t>(StatId::Count)> &baseStats)
{
    std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> rules = {};

    for (size_t statIndex = 0; statIndex < baseStats.size(); ++statIndex)
    {
        rules[statIndex] = raceRuleForBaseStat(baseStats[statIndex]);
    }

    return rules;
}

std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> raceRulesForData(
    const GameDataRepository *pGameData,
    const std::string &raceName,
    const std::array<int, static_cast<size_t>(StatId::Count)> &baseStats)
{
    std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> rules = raceRulesForStats(baseStats);

    if (pGameData == nullptr)
    {
        return rules;
    }

    const RaceStartingStatsTable::Entry *pEntry = pGameData->raceStartingStatsTable().get(raceName);

    if (pEntry == nullptr)
    {
        return rules;
    }

    for (size_t statIndex = 0; statIndex < static_cast<size_t>(StatId::Count); ++statIndex)
    {
        if (pEntry->addSteps[statIndex] > 0)
        {
            rules[statIndex].baseStep = pEntry->addSteps[statIndex];
        }

        if (pEntry->droppedSteps[statIndex] > 0)
        {
            rules[statIndex].droppedStep = pEntry->droppedSteps[statIndex];
        }

        if (pEntry->maximumStats[statIndex] > 0)
        {
            rules[statIndex].maximumValue = pEntry->maximumStats[statIndex];
        }
    }

    return rules;
}

void equipDebugGodLichItem(Character &character, const ItemTable *pItemTable, const DebugEquipmentItem &equipmentItem)
{
    if (pItemTable == nullptr)
    {
        return;
    }

    const ItemDefinition *pItemDefinition = pItemTable->get(equipmentItem.itemId);

    if (pItemDefinition == nullptr)
    {
        return;
    }

    character.equipment.*equipmentItem.pItemId = equipmentItem.itemId;
    EquippedItemRuntimeState &runtimeState = character.equipmentRuntime.*equipmentItem.pRuntimeState;
    runtimeState = {};
    runtimeState.identified = true;
    runtimeState.rarity = pItemDefinition->rarity;

    if (pItemDefinition->rarity == ItemRarity::Artifact || pItemDefinition->rarity == ItemRarity::Relic)
    {
        runtimeState.artifactId = static_cast<uint16_t>(std::min<uint32_t>(equipmentItem.itemId, 0xFFFFu));
    }
}

void equipDebugGodLichItems(Character &character, const ItemTable *pItemTable)
{
    character.inventory.clear();
    character.equipment = {};
    character.equipmentRuntime = {};

    for (const DebugEquipmentItem &equipmentItem : DebugGodLichEquipment)
    {
        equipDebugGodLichItem(character, pItemTable, equipmentItem);
    }
}

void applyDebugGodLichCharacter(
    Character &character,
    const ClassMultiplierTable *pClassMultiplierTable,
    const ItemTable *pItemTable,
    const SpellTable *pSpellTable)
{
    character.name = "God";
    character.className = "Lich";
    character.role = displayClassName(character.className);
    character.characterDataId = DebugGodLichCharacterDataId;
    character.level = 100;
    character.experience = 100000000;
    character.skillPoints = 0;
    character.might = 100;
    character.intellect = 100;
    character.personality = 100;
    character.endurance = 100;
    character.accuracy = 100;
    character.speed = 100;
    character.luck = 100;
    character.skills.clear();
    character.knownSpellIds.clear();

    for (const std::string &skillName : allCanonicalSkillNames())
    {
        character.skills[skillName] = {skillName, 200, SkillMastery::Grandmaster};
    }

    if (pSpellTable != nullptr)
    {
        for (const SpellEntry &spell : pSpellTable->entries())
        {
            if (spell.id > 0)
            {
                character.learnSpell(static_cast<uint32_t>(spell.id));
            }
        }
    }

    GameMechanics::refreshCharacterBaseResources(character, true, pClassMultiplierTable);
    equipDebugGodLichItems(character, pItemTable);
    character.quickSpellName = "Fire Bolt";
}

uint32_t statLabelColorForStats(const std::array<int, static_cast<size_t>(StatId::Count)> &baseStats, size_t statIndex)
{
    if (statIndex >= baseStats.size())
    {
        return WhiteColor;
    }

    if (baseStats[statIndex] > NeutralBaseStatValue)
    {
        return GreenColor;
    }

    if (baseStats[statIndex] < NeutralBaseStatValue)
    {
        return RedColor;
    }

    return WhiteColor;
}

int maximumStatValueForRule(const RaceStatRule &rule)
{
    return rule.maximumValue;
}

int skillMasteryAvailabilityForCreation(
    const ClassSkillTable *pClassSkillTable,
    const Character &character,
    const std::string &skillName,
    SkillMastery mastery)
{
    if (pClassSkillTable == nullptr)
    {
        return 0;
    }

    if (pClassSkillTable->getEffectiveCap(character.className, character.raceId, skillName) >= mastery)
    {
        return 0;
    }

    if (pClassSkillTable->getHighestPromotionEffectiveCap(character.className, character.raceId, skillName)
        >= mastery)
    {
        return 1;
    }

    return 2;
}

uint32_t inspectAvailabilityColor(int availability)
{
    switch (availability)
    {
        case 1:
            return YellowColor;

        case 2:
            return RedColor;

        case 0:
        default:
            return WhiteColor;
    }
}

std::string portraitTextureNameForEntry(const CharacterDollEntry &entry)
{
    if (!entry.facePicturesPrefix.empty())
    {
        return entry.facePicturesPrefix + "01";
    }

    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-01", entry.id);
    return buffer;
}

bool isPrintableNameCharacter(char character)
{
    return std::isalnum(static_cast<unsigned char>(character)) != 0
        || character == ' '
        || character == '\''
        || character == '-';
}

std::string characterCreationSkillDisplayName(const std::string &skillName)
{
    const std::string canonicalName = canonicalSkillName(skillName);

    if (canonicalName == "LeatherArmor")
    {
        return "Leather";
    }

    if (canonicalName == "ChainArmor")
    {
        return "Chain";
    }

    return displaySkillName(skillName);
}

}

NewGameScreen::NewGameScreen(
    const Engine::AssetFileSystem &assetFileSystem,
    GameAudioSystem *pGameAudioSystem,
    const GameDataRepository &gameData,
    bool debugGodLichRoster,
    bool allowIncompleteCharacterCreation,
    ContinueAction continueAction,
    BackAction backAction)
    : MenuScreenBase(assetFileSystem)
    , m_pGameAudioSystem(pGameAudioSystem)
    , m_pGameData(&gameData)
    , m_debugGodLichRoster(debugGodLichRoster)
    , m_allowIncompleteCharacterCreation(allowIncompleteCharacterCreation)
    , m_continueAction(std::move(continueAction))
    , m_backAction(std::move(backAction))
    , m_nameRng(std::random_device{}())
{
}

AppMode NewGameScreen::mode() const
{
    return AppMode::NewGame;
}

void NewGameScreen::prepareForFirstFrame()
{
    ensureContinentLayoutLoaded();
    ensureLayoutLoaded();
    preloadLayoutAssets(m_continentLayoutManager);
    preloadLayoutAssets(m_layoutManager);
    preloadTexture("selring");
    preloadFont("create");
    preloadFont("SMALLNUM");
}

void NewGameScreen::onEnter()
{
    ensureContinentLayoutLoaded();
    ensureLayoutLoaded();
    m_stage = FlowStage::ContinentSelection;
    m_characterCreationInitialized = false;
    m_selectedContinent = {};
}

void NewGameScreen::initializeCharacterCreationForSelectedContinent()
{
    if (m_characterCreationInitialized)
    {
        return;
    }

    ensureLayoutLoaded();
    rebuildCandidates();
    m_partySize = 1;
    m_activePartySlot = 0;
    m_partyStates.clear();

    size_t defaultCandidateIndex = 0;

    for (size_t index = 0; index < candidateCount(); ++index)
    {
        const CreationCandidate &candidate = candidateAt(index);

        if (candidate.characterDataId == DefaultCreationCharacterDataId
            && canonicalClassName(candidate.className) == canonicalClassName(DefaultCreationClassName))
        {
            defaultCandidateIndex = index;
            break;
        }
    }

    resetStateForCandidate(defaultCandidateIndex);
    ensurePartyStates();
    saveActivePartyState();
    m_characterCreationInitialized = true;
}

void NewGameScreen::onExit()
{
    endNameEditing(true);
}

void NewGameScreen::handleSdlEvent(const SDL_Event &event)
{
    if (event.type == SDL_EVENT_KEY_UP && event.key.key == SDLK_BACKSPACE)
    {
        resetNameBackspaceRepeat();
        return;
    }

    if (event.type == SDL_EVENT_TEXT_INPUT && m_state.nameEditing)
    {
        const char *pText = event.text.text;

        if (pText == nullptr)
        {
            return;
        }

        for (size_t i = 0; pText[i] != '\0' && m_state.nameEditBuffer.size() < MaximumNameLength; ++i)
        {
            if (isPrintableNameCharacter(pText[i]))
            {
                m_state.nameEditBuffer.push_back(pText[i]);
            }
        }

        return;
    }

    if (event.type != SDL_EVENT_KEY_DOWN || event.key.repeat)
    {
        return;
    }

    if (m_stage == FlowStage::ContinentSelection)
    {
        switch (event.key.key)
        {
            case SDLK_ESCAPE:
                m_escapePressed = true;
                break;

            case SDLK_RETURN:
            case SDLK_KP_ENTER:
                m_returnPressed = true;
                break;

            default:
                break;
        }

        return;
    }

    switch (event.key.key)
    {
        case SDLK_ESCAPE:
            m_escapePressed = true;
            break;

        case SDLK_RETURN:
        case SDLK_KP_ENTER:
            m_returnPressed = true;
            break;

        case SDLK_BACKSPACE:
            if (m_state.nameEditing)
            {
                deleteNameEditCharacter();
                m_nameBackspaceHeld = !m_state.nameEditBuffer.empty();
                m_nameBackspaceRepeatTimer = NameBackspaceInitialRepeatDelaySeconds;
            }
            break;

        case SDLK_1:
        case SDLK_2:
        case SDLK_3:
        case SDLK_4:
        case SDLK_5:
            if (!m_state.nameEditing && !m_debugGodLichRoster)
            {
                const size_t slotIndex = static_cast<size_t>(event.key.key - SDLK_1);

                if (slotIndex < m_partySize)
                {
                    switchActivePartySlot(slotIndex);
                }
            }
            break;

        default:
            break;
    }
}

const CreationCandidate &NewGameScreen::selectedCandidate() const
{
    return candidateForState(m_state);
}

const CreationCandidate &NewGameScreen::candidateForState(const CreationState &state) const
{
    return candidateAt(state.selectedCandidateIndex);
}

std::string NewGameScreen::selectedClassName() const
{
    return classNameForState(m_state);
}

std::string NewGameScreen::classNameForState(const CreationState &state) const
{
    if (m_pGameData != nullptr)
    {
        if (const std::optional<std::string> className =
                m_pGameData->classSkillTable().classNameForId(state.selectedClassId))
        {
            return *className;
        }
    }

    return candidateForState(state).className;
}

void NewGameScreen::ensurePartyStates()
{
    if (m_partySize == 0)
    {
        m_partySize = 1;
    }

    if (m_partySize > 5)
    {
        m_partySize = 5;
    }

    while (m_partyStates.size() < m_partySize)
    {
        m_partyStates.push_back(m_state);
    }

    if (m_partyStates.size() > m_partySize)
    {
        m_partyStates.resize(m_partySize);
    }

    if (m_activePartySlot >= m_partySize)
    {
        m_activePartySlot = m_partySize - 1;
    }
}

void NewGameScreen::saveActivePartyState()
{
    ensurePartyStates();
    m_partyStates[m_activePartySlot] = m_state;
}

void NewGameScreen::switchActivePartySlot(size_t slotIndex)
{
    if (slotIndex >= m_partySize)
    {
        return;
    }

    endNameEditing(true);
    saveActivePartyState();
    m_activePartySlot = slotIndex;
    ensurePartyStates();
    m_state = m_partyStates[m_activePartySlot];
}

void NewGameScreen::addPartySlot()
{
    endNameEditing(true);
    saveActivePartyState();

    if (m_partySize >= 5)
    {
        return;
    }

    m_partySize += 1;
    ensurePartyStates();
    m_activePartySlot = m_partySize - 1;
    resetStateForCandidate(0);
    saveActivePartyState();
}

void NewGameScreen::removePartySlot()
{
    endNameEditing(true);
    saveActivePartyState();

    if (m_partySize <= 1)
    {
        return;
    }

    m_partySize -= 1;
    ensurePartyStates();
    m_state = m_partyStates[m_activePartySlot];
}

void NewGameScreen::rebuildCandidates()
{
    m_candidates.clear();

    if (m_pGameData == nullptr)
    {
        return;
    }

    const MergedCharacterSelectionTable &selectionTable = m_pGameData->mergedCharacterSelectionTable();
    const MergedCharacterSelectionContinent *pContinent =
        findNewGameContinent(selectionTable, m_selectedContinent.key);

    if (pContinent == nullptr)
    {
        pContinent = findNewGameContinent(selectionTable, DefaultNewGameContinentKey);
    }

    if (pContinent == nullptr)
    {
        return;
    }

    std::vector<const CharacterDollEntry *> characterEntries;

    for (const auto &[characterId, entry] : m_pGameData->characterDollTable().characters())
    {
        (void)characterId;
        characterEntries.push_back(&entry);
    }

    std::sort(
        characterEntries.begin(),
        characterEntries.end(),
        [](const CharacterDollEntry *pLeft, const CharacterDollEntry *pRight)
        {
            return pLeft->id < pRight->id;
        });

    for (const CharacterDollEntry *pEntry : characterEntries)
    {
        if (pEntry == nullptr || !pEntry->availableAtStart || pEntry->raceId < 0)
        {
            continue;
        }

        const uint32_t raceId = static_cast<uint32_t>(pEntry->raceId);

        if (!containsUnsigned(pContinent->availableRaceIds, raceId)
            || portraitIsExcepted(*pEntry, pContinent->portraitExceptions))
        {
            continue;
        }

        const std::vector<std::string> *pAllowedClasses = selectionTable.allowedClassesForRaceId(raceId);
        const std::optional<std::string> raceName = selectionTable.raceNameForId(raceId);

        if (pAllowedClasses == nullptr || !raceName.has_value())
        {
            continue;
        }

        std::vector<uint32_t> availableClassIds;

        for (uint32_t classId : pContinent->availableClassIds)
        {
            const std::optional<std::string> className = m_pGameData->classSkillTable().classNameForId(classId);

            if (!className.has_value() || !containsCanonicalClass(*pAllowedClasses, *className))
            {
                continue;
            }

            availableClassIds.push_back(classId);
        }

        if (availableClassIds.empty())
        {
            continue;
        }

        std::sort(availableClassIds.begin(), availableClassIds.end());
        availableClassIds.erase(
            std::unique(availableClassIds.begin(), availableClassIds.end()),
            availableClassIds.end());

        CreationCandidate candidate = {};
        candidate.characterDataId = pEntry->id;
        candidate.raceId = raceId;
        candidate.defaultName = "Player";
        candidate.raceName = *raceName;
        candidate.availableClassIds = std::move(availableClassIds);
        candidate.classId = classIdNear(pEntry->defaultClassId, candidate.availableClassIds, 1);

        if (const std::optional<std::string> className = m_pGameData->classSkillTable().classNameForId(candidate.classId))
        {
            candidate.className = *className;
            m_candidates.push_back(std::move(candidate));
        }
    }
}

size_t NewGameScreen::candidateCount() const
{
    return m_debugGodLichRoster ? 1 : m_candidates.size();
}

const CreationCandidate &NewGameScreen::candidateAt(size_t candidateIndex) const
{
    if (m_debugGodLichRoster)
    {
        return DebugGodLichCandidate;
    }

    assert(!m_candidates.empty());
    return m_candidates[std::min(candidateIndex, m_candidates.size() - 1)];
}

std::array<int, static_cast<size_t>(StatId::Count)> NewGameScreen::statsForRace(const std::string &raceName) const
{
    const std::array<int, static_cast<size_t>(StatId::Count)> defaultStats = {
        NeutralBaseStatValue,
        NeutralBaseStatValue,
        NeutralBaseStatValue,
        NeutralBaseStatValue,
        NeutralBaseStatValue,
        NeutralBaseStatValue,
        NeutralBaseStatValue
    };

    if (m_pGameData == nullptr)
    {
        return defaultStats;
    }

    const RaceStartingStatsTable::Entry *pEntry = m_pGameData->raceStartingStatsTable().get(raceName);
    return pEntry != nullptr ? pEntry->stats : defaultStats;
}

const CharacterDollEntry *NewGameScreen::selectedCharacterEntry() const
{
    return characterEntryForState(m_state);
}

const CharacterDollEntry *NewGameScreen::characterEntryForState(const CreationState &state) const
{
    return m_pGameData != nullptr
        ? m_pGameData->characterDollTable().getCharacter(candidateForState(state).characterDataId)
        : nullptr;
}

void NewGameScreen::resetStateForCandidate(size_t candidateIndex)
{
    m_state = {};
    m_state.selectedCandidateIndex = std::min(candidateIndex, candidateCount() - 1);
    m_state.selectedClassId = selectedCandidate().classId;
    resetCurrentState(true);
}

void NewGameScreen::resetCurrentState(bool applyCandidateDefaults)
{
    const CreationCandidate &candidate = selectedCandidate();
    const std::array<int, static_cast<size_t>(StatId::Count)> baseStats = statsForRace(candidate.raceName);
    m_state.baseStats = baseStats;
    m_state.currentStats = baseStats;
    m_state.name = generateDefaultNameForState(m_state);
    m_state.nameEditBuffer = m_state.name;
    m_state.defaultSkills.clear();
    m_state.optionalSkills.clear();
    m_state.selectedOptionalSkills.clear();
    m_state.statusMessage.clear();

    if (applyCandidateDefaults && candidate.hasCustomDefaultStats)
    {
        m_state.currentStats = candidate.defaultStats;
    }

    refreshSkillChoices(applyCandidateDefaults);

    const CharacterDollEntry *pEntry = selectedCharacterEntry();
    m_state.selectedVoiceId = pEntry != nullptr ? static_cast<int>(pEntry->defaultVoiceId) : 0;

    endNameEditing(false);
}

void NewGameScreen::refreshSkillChoices(bool applyCandidateDefaults)
{
    const CreationCandidate &candidate = selectedCandidate();
    m_state.defaultSkills.clear();
    m_state.optionalSkills.clear();
    m_state.selectedOptionalSkills.clear();

    if (m_pGameData != nullptr)
    {
        for (const char *pSkillName : OrderedSkillNames)
        {
            const StartingSkillAvailability availability =
                m_pGameData->classSkillTable().getEffectiveStartingSkillAvailability(
                    selectedClassName(),
                    candidate.raceId,
                    pSkillName);

            if (availability == StartingSkillAvailability::HasByDefault)
            {
                m_state.defaultSkills.push_back(pSkillName);
            }
            else if (availability == StartingSkillAvailability::CanLearn)
            {
                m_state.optionalSkills.push_back(pSkillName);
            }
        }
    }

    if (applyCandidateDefaults && candidate.hasCustomDefaultStats)
    {
        for (const std::string &skillName : candidate.defaultOptionalSkills)
        {
            if (skillName.empty())
            {
                continue;
            }

            const bool alreadyDefault =
                std::find(m_state.defaultSkills.begin(), m_state.defaultSkills.end(), skillName) != m_state.defaultSkills.end();
            const bool optionalAllowed =
                std::find(m_state.optionalSkills.begin(), m_state.optionalSkills.end(), skillName) != m_state.optionalSkills.end();

            if (!alreadyDefault
                && optionalAllowed
                && std::find(m_state.selectedOptionalSkills.begin(), m_state.selectedOptionalSkills.end(), skillName)
                    == m_state.selectedOptionalSkills.end())
            {
                m_state.selectedOptionalSkills.push_back(skillName);
            }
        }
    }
}

bool NewGameScreen::textInputActive() const
{
    return m_state.nameEditing;
}

void NewGameScreen::beginNameEditing()
{
    if (m_state.nameEditing)
    {
        return;
    }

    resetNameBackspaceRepeat();
    m_state.nameEditing = true;
    m_state.nameEditBuffer = m_state.name;
#if !defined(__ANDROID__)
    SDL_Window *pWindow = SDL_GetKeyboardFocus();

    if (pWindow != nullptr)
    {
        SDL_StartTextInput(pWindow);
    }
#endif
}

void NewGameScreen::endNameEditing(bool commitEdit)
{
    resetNameBackspaceRepeat();

    if (!m_state.nameEditing)
    {
        return;
    }

    if (commitEdit)
    {
        const std::string trimmed = trimCopy(m_state.nameEditBuffer);

        if (!trimmed.empty())
        {
            m_state.name = trimmed;
        }
    }

    m_state.nameEditing = false;
#if !defined(__ANDROID__)
    SDL_Window *pWindow = SDL_GetKeyboardFocus();

    if (pWindow != nullptr)
    {
        SDL_StopTextInput(pWindow);
    }
#endif
}

void NewGameScreen::deleteNameEditCharacter()
{
    if (m_state.nameEditing && !m_state.nameEditBuffer.empty())
    {
        m_state.nameEditBuffer.pop_back();
    }
}

void NewGameScreen::resetNameBackspaceRepeat()
{
    m_nameBackspaceHeld = false;
    m_nameBackspaceRepeatTimer = 0.0f;
}

void NewGameScreen::updateNameBackspaceRepeat(float deltaSeconds)
{
    if (!m_nameBackspaceHeld || !m_state.nameEditing)
    {
        resetNameBackspaceRepeat();
        return;
    }

    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    m_nameBackspaceRepeatTimer -= deltaSeconds;

    while (m_nameBackspaceRepeatTimer <= 0.0f)
    {
        deleteNameEditCharacter();

        if (m_state.nameEditBuffer.empty())
        {
            resetNameBackspaceRepeat();
            return;
        }

        m_nameBackspaceRepeatTimer += NameBackspaceRepeatIntervalSeconds;
    }
}

void NewGameScreen::ensurePcNamesLoaded()
{
    if (m_pcNamesLoaded)
    {
        return;
    }

    m_pcNamesLoaded = true;
    const std::optional<std::string> tableText = assetFileSystem().readTextFile(PcNamesTablePath);

    if (!tableText.has_value())
    {
        return;
    }

    bool headerLine = true;
    size_t lineStart = 0;

    while (lineStart <= tableText->size())
    {
        const size_t lineEnd = tableText->find('\n', lineStart);
        const std::string line = lineEnd == std::string::npos
            ? tableText->substr(lineStart)
            : tableText->substr(lineStart, lineEnd - lineStart);

        if (headerLine)
        {
            headerLine = false;
        }
        else
        {
            const std::vector<std::string> cells = splitTabLine(line);
            const size_t columnCount = std::min(cells.size(), m_pcNameColumns.size());

            for (size_t columnIndex = 0; columnIndex < columnCount; ++columnIndex)
            {
                const std::string name = trimCopy(cells[columnIndex]);

                if (!name.empty() && name != "*end")
                {
                    m_pcNameColumns[columnIndex].push_back(name);
                }
            }
        }

        if (lineEnd == std::string::npos)
        {
            break;
        }

        lineStart = lineEnd + 1;
    }
}

std::string NewGameScreen::generateDefaultNameForState(const CreationState &state)
{
    const CreationCandidate &candidate = candidateForState(state);

    if (m_debugGodLichRoster)
    {
        return candidate.defaultName;
    }

    ensurePcNamesLoaded();

    const size_t columnIndex = pcNameColumnForState(state);
    const std::vector<std::string> &names = m_pcNameColumns[columnIndex];

    if (names.empty())
    {
        return candidate.defaultName.empty() ? "Player" : candidate.defaultName;
    }

    std::vector<const std::string *> unusedNames;

    for (const std::string &name : names)
    {
        if (!partyNameAlreadyUsed(name))
        {
            unusedNames.push_back(&name);
        }
    }

    if (!unusedNames.empty())
    {
        std::uniform_int_distribution<size_t> distribution(0, unusedNames.size() - 1);
        return *unusedNames[distribution(m_nameRng)];
    }

    std::uniform_int_distribution<size_t> distribution(0, names.size() - 1);
    return names[distribution(m_nameRng)];
}

bool NewGameScreen::partyNameAlreadyUsed(const std::string &name) const
{
    const std::string trimmedName = trimCopy(name);

    if (trimmedName.empty())
    {
        return false;
    }

    for (size_t slotIndex = 0; slotIndex < m_partyStates.size(); ++slotIndex)
    {
        if (slotIndex == m_activePartySlot)
        {
            continue;
        }

        if (trimCopy(m_partyStates[slotIndex].name) == trimmedName)
        {
            return true;
        }
    }

    return false;
}

size_t NewGameScreen::pcNameColumnForState(const CreationState &state) const
{
    const CreationCandidate &candidate = candidateForState(state);
    const CharacterDollEntry *pEntry = characterEntryForState(state);
    const bool female = pEntry != nullptr && pEntry->defaultSex == 1;
    const std::string raceName = canonicalNameToken(candidate.raceName);
    const std::string className = canonicalNameToken(classNameForState(state));

    if (raceName == "dragon" || className == "dragon" || className == "greatwyrm")
    {
        return 7;
    }

    if (raceName == "troll" || raceName == "minotaur" || className == "troll" || className == "wartroll"
        || className == "minotaur" || className == "minotaurlord")
    {
        return 4;
    }

    if (raceName == "darkelf" || className == "darkelf")
    {
        return female ? 3 : 2;
    }

    if (raceName == "vampire" || className == "vampire" || className == "nosferatu" || className == "necromancer"
        || className == "lich")
    {
        return female ? 5 : 6;
    }

    return female ? 1 : 0;
}

int NewGameScreen::currentBonusPool() const
{
    return bonusPoolForState(m_state);
}

int NewGameScreen::bonusPoolForState(const CreationState &state) const
{
    int remainingPoints = StartingBonusPool;
    const CreationCandidate &candidate = candidateForState(state);
    const std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> rules =
        raceRulesForData(m_pGameData, candidate.raceName, state.baseStats);

    for (size_t statIndex = 0; statIndex < static_cast<size_t>(StatId::Count); ++statIndex)
    {
        const int currentValue = state.currentStats[statIndex];
        const int baseValue = state.baseStats[statIndex];
        int penaltyMultiplier = 0;
        int bonusMultiplier = 0;

        if (currentValue >= baseValue)
        {
            penaltyMultiplier = rules[statIndex].droppedStep;
            bonusMultiplier = rules[statIndex].baseStep;
        }
        else
        {
            penaltyMultiplier = rules[statIndex].baseStep;
            bonusMultiplier = rules[statIndex].droppedStep;
        }

        if (bonusMultiplier > 0)
        {
            remainingPoints += penaltyMultiplier * (baseValue - currentValue) / bonusMultiplier;
        }
    }

    return remainingPoints;
}

std::vector<std::string> NewGameScreen::wrapTextToWidth(
    const std::string &fontName,
    const std::string &text,
    float maxWidth,
    float scale)
{
    std::vector<std::string> lines;

    if (text.empty())
    {
        return lines;
    }

    size_t paragraphStart = 0;

    while (paragraphStart <= text.size())
    {
        const size_t paragraphEnd = text.find('\n', paragraphStart);
        const std::string paragraph = paragraphEnd == std::string::npos
            ? text.substr(paragraphStart)
            : text.substr(paragraphStart, paragraphEnd - paragraphStart);

        if (paragraph.empty())
        {
            lines.push_back({});
        }
        else
        {
            std::string currentLine;
            size_t wordStart = 0;

            while (wordStart < paragraph.size())
            {
                while (wordStart < paragraph.size() && paragraph[wordStart] == ' ')
                {
                    ++wordStart;
                }

                if (wordStart >= paragraph.size())
                {
                    break;
                }

                size_t wordEnd = paragraph.find(' ', wordStart);

                if (wordEnd == std::string::npos)
                {
                    wordEnd = paragraph.size();
                }

                std::string word = paragraph.substr(wordStart, wordEnd - wordStart);

                while (!word.empty() && measureTextWidth(fontName, word, scale) > maxWidth)
                {
                    size_t splitLength = 1;

                    while (splitLength < word.size()
                        && measureTextWidth(fontName, word.substr(0, splitLength + 1), scale) <= maxWidth)
                    {
                        ++splitLength;
                    }

                    lines.push_back(word.substr(0, splitLength));
                    word.erase(0, splitLength);
                }

                if (word.empty())
                {
                    wordStart = wordEnd + 1;
                    continue;
                }

                const std::string candidate = currentLine.empty() ? word : currentLine + " " + word;

                if (!currentLine.empty() && measureTextWidth(fontName, candidate, scale) > maxWidth)
                {
                    lines.push_back(currentLine);
                    currentLine = word;
                }
                else
                {
                    currentLine = candidate;
                }

                wordStart = wordEnd + 1;
            }

            if (!currentLine.empty())
            {
                lines.push_back(currentLine);
            }
        }

        if (paragraphEnd == std::string::npos)
        {
            break;
        }

        paragraphStart = paragraphEnd + 1;
    }

    return lines;
}

bool NewGameScreen::tryIncreaseStat(StatId statId)
{
    const size_t index = static_cast<size_t>(statId);
    const std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> rules =
        raceRulesForData(m_pGameData, selectedCandidate().raceName, m_state.baseStats);
    const int baseValue = m_state.baseStats[index];
    const int currentValue = m_state.currentStats[index];
    int amount = rules[index].baseStep;
    int cost = rules[index].droppedStep;

    if (currentValue < baseValue)
    {
        amount = rules[index].droppedStep;
        cost = rules[index].baseStep;
    }

    if (currentBonusPool() < cost || currentValue + amount > maximumStatValueForRule(rules[index]))
    {
        return false;
    }

    m_state.currentStats[index] += amount;
    m_state.statusMessage.clear();
    return true;
}

bool NewGameScreen::tryDecreaseStat(StatId statId)
{
    const size_t index = static_cast<size_t>(statId);
    const std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> rules =
        raceRulesForData(m_pGameData, selectedCandidate().raceName, m_state.baseStats);
    const int baseValue = m_state.baseStats[index];
    const int currentValue = m_state.currentStats[index];
    int amount = rules[index].baseStep;

    if (currentValue <= baseValue)
    {
        amount = rules[index].droppedStep;
    }

    if (currentValue - amount < baseValue - MinimumStatOffset)
    {
        return false;
    }

    m_state.currentStats[index] -= amount;
    m_state.statusMessage.clear();
    return true;
}

bool NewGameScreen::tryToggleOptionalSkill(const std::string &skillName)
{
    const std::vector<std::string>::iterator existingIt =
        std::find(m_state.selectedOptionalSkills.begin(), m_state.selectedOptionalSkills.end(), skillName);

    if (existingIt != m_state.selectedOptionalSkills.end())
    {
        m_state.selectedOptionalSkills.erase(existingIt);
        m_state.statusMessage.clear();
        return true;
    }

    if (m_state.selectedOptionalSkills.size() >= MaximumOptionalSkillSelections)
    {
        m_state.statusMessage = "Only two additional skills can be selected.";
        return false;
    }

    m_state.selectedOptionalSkills.push_back(skillName);
    m_state.statusMessage.clear();
    return true;
}

std::vector<int> NewGameScreen::availableVoiceIdsForSelectedCandidate() const
{
    std::vector<int> voiceIds;
    const CharacterDollEntry *pSelectedEntry = selectedCharacterEntry();

    if (pSelectedEntry == nullptr || m_pGameData == nullptr)
    {
        return voiceIds;
    }

    std::unordered_set<int> seenVoiceIds;

    for (size_t candidateIndex = 0; candidateIndex < candidateCount(); ++candidateIndex)
    {
        const CreationCandidate &candidate = candidateAt(candidateIndex);
        const CharacterDollEntry *pEntry = m_pGameData->characterDollTable().getCharacter(candidate.characterDataId);

        if (pEntry == nullptr || pEntry->defaultSex != pSelectedEntry->defaultSex)
        {
            continue;
        }

        const int voiceId = static_cast<int>(pEntry->defaultVoiceId);

        if (seenVoiceIds.insert(voiceId).second)
        {
            voiceIds.push_back(voiceId);
        }
    }

    std::sort(voiceIds.begin(), voiceIds.end());
    return voiceIds;
}

void NewGameScreen::cycleCandidate(int direction)
{
    endNameEditing(true);
    const int count = static_cast<int>(candidateCount());

    if (count <= 0)
    {
        return;
    }

    const uint32_t previousClassId = m_state.selectedClassId;
    int nextIndex = static_cast<int>(m_state.selectedCandidateIndex) + direction;

    if (nextIndex < 0)
    {
        nextIndex += count;
    }
    else if (nextIndex >= count)
    {
        nextIndex -= count;
    }

    resetStateForCandidate(static_cast<size_t>(nextIndex));
    m_state.selectedClassId = classIdNear(previousClassId, selectedCandidate().availableClassIds, 1);
    refreshSkillChoices(false);
}

void NewGameScreen::cycleClass(int direction)
{
    endNameEditing(true);

    if (m_debugGodLichRoster || m_candidates.empty() || m_pGameData == nullptr)
    {
        return;
    }

    const CreationCandidate &candidate = selectedCandidate();

    if (candidate.availableClassIds.empty())
    {
        return;
    }

    const std::vector<uint32_t>::const_iterator currentIt =
        std::find(candidate.availableClassIds.begin(), candidate.availableClassIds.end(), m_state.selectedClassId);
    int currentIndex = currentIt != candidate.availableClassIds.end()
        ? static_cast<int>(currentIt - candidate.availableClassIds.begin())
        : 0;
    currentIndex += direction;

    if (currentIndex < 0)
    {
        currentIndex = static_cast<int>(candidate.availableClassIds.size()) - 1;
    }
    else if (currentIndex >= static_cast<int>(candidate.availableClassIds.size()))
    {
        currentIndex = 0;
    }

    m_state.selectedClassId = candidate.availableClassIds[static_cast<size_t>(currentIndex)];
    refreshSkillChoices(false);
    m_state.statusMessage.clear();
}

void NewGameScreen::cycleVoice(int direction)
{
    endNameEditing(true);
    std::vector<int> voiceIds = availableVoiceIdsForSelectedCandidate();

    if (voiceIds.empty())
    {
        return;
    }

    auto currentIt = std::find(voiceIds.begin(), voiceIds.end(), m_state.selectedVoiceId);
    int currentIndex = currentIt != voiceIds.end() ? static_cast<int>(currentIt - voiceIds.begin()) : 0;
    currentIndex += direction;

    if (currentIndex < 0)
    {
        currentIndex = static_cast<int>(voiceIds.size()) - 1;
    }
    else if (currentIndex >= static_cast<int>(voiceIds.size()))
    {
        currentIndex = 0;
    }

    m_state.selectedVoiceId = voiceIds[static_cast<size_t>(currentIndex)];
    m_state.statusMessage.clear();
}

Character NewGameScreen::buildVoicePreviewCharacter() const
{
    Character character = {};
    const CreationCandidate &candidate = selectedCandidate();
    const CharacterDollEntry *pEntry = selectedCharacterEntry();

    character.name = candidate.defaultName;
    character.className = selectedClassName();
    character.role = displayClassName(character.className);
    character.characterDataId = candidate.characterDataId;
    character.voiceId = m_state.selectedVoiceId;

    if (pEntry != nullptr)
    {
        character.portraitTextureName = portraitTextureNameForEntry(*pEntry);
        character.portraitPictureId = pEntry->id > 0 ? (pEntry->id - 1) : 0;
        character.sexId = pEntry->defaultSex;
        character.raceId = pEntry->raceId >= 0 ? static_cast<uint32_t>(pEntry->raceId) : 0;
    }

    return character;
}

void NewGameScreen::playUiClickSound(SoundId soundId) const
{
    if (m_pGameAudioSystem == nullptr || soundId == SoundId::None)
    {
        return;
    }

    m_pGameAudioSystem->playCommonSound(soundId, GameAudioSystem::PlaybackGroup::Ui);
}

void NewGameScreen::playVoicePreview()
{
    if (m_pGameAudioSystem == nullptr)
    {
        return;
    }

    m_pGameAudioSystem->playSpeech(
        buildVoicePreviewCharacter(),
        SpeechId::SelectCharacter,
        0,
        CharacterCreationVoicePreviewSpeakerKey);
}

void NewGameScreen::renderSkillInspectPopup(
    const SkillInspectEntry &entry,
    const std::string &skillName,
    const MenuScreenBase::Rect &sourceRect,
    const Character &character,
    float scale)
{
    const float popupScale = scale;
    const float rootWidth = InspectPopupWidth * popupScale;
    const float popupGap = InspectPopupGap * popupScale;
    const float rightOverhang = 7.0f * popupScale;
    const float bottomOverhang = 7.0f * popupScale;
    const float totalWidth = rootWidth + rightOverhang;
    const float viewportWidth = static_cast<float>(frameWidth());
    const float viewportHeight = static_cast<float>(frameHeight());
    const float bodyX = 20.0f * popupScale;
    const float bodyWidth = std::max(1.0f, 377.0f * popupScale);
    const float bodyLineHeight = static_cast<float>(fontHeight("SMALLNUM")) * popupScale;
    const std::vector<std::string> bodyLines = wrapTextToWidth("SMALLNUM", entry.description, bodyWidth, popupScale);
    const std::vector<std::string> expertLines = entry.expertDescription.empty()
        ? std::vector<std::string>{}
        : wrapTextToWidth("SMALLNUM", "Expert: " + entry.expertDescription, bodyWidth, popupScale);
    const std::vector<std::string> masterLines = entry.masterDescription.empty()
        ? std::vector<std::string>{}
        : wrapTextToWidth("SMALLNUM", "Master: " + entry.masterDescription, bodyWidth, popupScale);
    const std::vector<std::string> grandmasterLines = entry.grandmasterDescription.empty()
        ? std::vector<std::string>{}
        : wrapTextToWidth("SMALLNUM", "Grandmaster: " + entry.grandmasterDescription, bodyWidth, popupScale);
    const float bodyHeight =
        bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    float masteryHeight = 0.0f;
    bool hasAnyMastery = false;

    for (const std::vector<std::string> *pLines : {&expertLines, &masterLines, &grandmasterLines})
    {
        if (pLines->empty())
        {
            continue;
        }

        if (hasAnyMastery)
        {
            masteryHeight += 2.0f * popupScale;
        }

        masteryHeight += bodyLineHeight * static_cast<float>(pLines->size());
        hasAnyMastery = true;
    }

    const float rootHeight =
        (42.0f + 15.0f) * popupScale
        + bodyHeight
        + (hasAnyMastery ? 10.0f * popupScale + masteryHeight : 0.0f);
    const float totalHeight = rootHeight + bottomOverhang;
    float popupX = sourceRect.x + sourceRect.width + popupGap;

    if (popupX + totalWidth > viewportWidth)
    {
        popupX = sourceRect.x - totalWidth - popupGap;
    }

    popupX = std::clamp(popupX, 0.0f, std::max(0.0f, viewportWidth - totalWidth));
    float popupY = sourceRect.y + (sourceRect.height - rootHeight) * 0.5f;
    popupY = std::clamp(popupY, 0.0f, std::max(0.0f, viewportHeight - totalHeight));
    const MenuScreenBase::Rect popupRect = {
        std::round(popupX),
        std::round(popupY),
        std::round(rootWidth),
        std::round(rootHeight)
    };

    drawTexture("parchment", popupRect);
    drawTexture("edge_top", {popupRect.x, popupRect.y, popupRect.width, 10.0f * popupScale});
    drawTexture(
        "edge_btm",
        {popupRect.x,
         popupRect.y + popupRect.height - 16.0f * popupScale + 7.0f * popupScale,
         popupRect.width,
         16.0f * popupScale});
    drawTexture("edge_lf", {popupRect.x, popupRect.y, 11.0f * popupScale, popupRect.height});
    drawTexture(
        "edge_rt",
        {popupRect.x + popupRect.width - 16.0f * popupScale + 6.0f * popupScale,
         popupRect.y,
         16.0f * popupScale,
         popupRect.height});
    drawTexture("cornr_UL", {popupRect.x, popupRect.y, 33.0f * popupScale, 32.0f * popupScale});
    drawTexture(
        "cornr_UR",
        {popupRect.x + popupRect.width - 39.0f * popupScale + 7.0f * popupScale,
         popupRect.y,
         39.0f * popupScale,
         32.0f * popupScale});
    drawTexture(
        "cornr_LL",
        {popupRect.x,
         popupRect.y + popupRect.height - 38.0f * popupScale + 7.0f * popupScale,
         33.0f * popupScale,
         38.0f * popupScale});
    drawTexture(
        "cornr_LR",
        {popupRect.x + popupRect.width - 39.0f * popupScale + 7.0f * popupScale,
         popupRect.y + popupRect.height - 38.0f * popupScale + 7.0f * popupScale,
         39.0f * popupScale,
         38.0f * popupScale});

    const float titleY = popupRect.y + 12.0f * popupScale;
    const float titleWidth = measureTextWidth("Create", entry.name, popupScale);
    drawText("Create", entry.name, popupRect.x + (popupRect.width - titleWidth) * 0.5f, titleY, InspectTitleColor, popupScale);

    float textY = popupRect.y + 42.0f * popupScale;

    for (const std::string &line : bodyLines)
    {
        drawText("SMALLNUM", line, popupRect.x + bodyX, textY, WhiteColor, popupScale);
        textY += bodyLineHeight;
    }

    if (hasAnyMastery)
    {
        textY += 10.0f * popupScale;
    }

    bool renderedMasteryBlock = false;
    const auto renderMasteryBlock =
        [this, &popupRect, popupScale, bodyX, bodyLineHeight, &textY](
            const std::vector<std::string> &lines,
            uint32_t color,
            bool &renderedBlock)
        {
            if (lines.empty())
            {
                return;
            }

            if (renderedBlock)
            {
                textY += 2.0f * popupScale;
            }

            for (const std::string &line : lines)
            {
                drawText("SMALLNUM", line, popupRect.x + bodyX, textY, color, popupScale);
                textY += bodyLineHeight;
            }

            renderedBlock = true;
        };

    renderMasteryBlock(
        expertLines,
        inspectAvailabilityColor(skillMasteryAvailabilityForCreation(
            m_pGameData != nullptr ? &m_pGameData->classSkillTable() : nullptr,
            character,
            skillName,
            SkillMastery::Expert)),
        renderedMasteryBlock);
    renderMasteryBlock(
        masterLines,
        inspectAvailabilityColor(skillMasteryAvailabilityForCreation(
            m_pGameData != nullptr ? &m_pGameData->classSkillTable() : nullptr,
            character,
            skillName,
            SkillMastery::Master)),
        renderedMasteryBlock);
    renderMasteryBlock(
        grandmasterLines,
        inspectAvailabilityColor(skillMasteryAvailabilityForCreation(
            m_pGameData != nullptr ? &m_pGameData->classSkillTable() : nullptr,
            character,
            skillName,
            SkillMastery::Grandmaster)),
        renderedMasteryBlock);
}

void NewGameScreen::renderStatInspectPopup(
    const StatInspectEntry &entry,
    const MenuScreenBase::Rect &sourceRect,
    float scale)
{
    const float popupScale = scale;
    const float rootWidth = InspectPopupWidth * popupScale;
    const float popupGap = InspectPopupGap * popupScale;
    const float rightOverhang = 7.0f * popupScale;
    const float bottomOverhang = 7.0f * popupScale;
    const float totalWidth = rootWidth + rightOverhang;
    const float viewportWidth = static_cast<float>(frameWidth());
    const float viewportHeight = static_cast<float>(frameHeight());
    const float bodyX = 20.0f * popupScale;
    const float bodyWidth = std::max(1.0f, 377.0f * popupScale);
    const float bodyLineHeight = static_cast<float>(fontHeight("SMALLNUM")) * popupScale;
    const std::vector<std::string> bodyLines = wrapTextToWidth("SMALLNUM", entry.description, bodyWidth, popupScale);
    const float bodyHeight =
        bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    const float rootHeight = (42.0f + 15.0f) * popupScale + bodyHeight;
    const float totalHeight = rootHeight + bottomOverhang;
    float popupX = sourceRect.x + sourceRect.width + popupGap;

    if (popupX + totalWidth > viewportWidth)
    {
        popupX = sourceRect.x - totalWidth - popupGap;
    }

    popupX = std::clamp(popupX, 0.0f, std::max(0.0f, viewportWidth - totalWidth));
    float popupY = sourceRect.y + (sourceRect.height - rootHeight) * 0.5f;
    popupY = std::clamp(popupY, 0.0f, std::max(0.0f, viewportHeight - totalHeight));
    const MenuScreenBase::Rect popupRect = {
        std::round(popupX),
        std::round(popupY),
        std::round(rootWidth),
        std::round(rootHeight)
    };

    drawTexture("parchment", popupRect);
    drawTexture("edge_top", {popupRect.x, popupRect.y, popupRect.width, 10.0f * popupScale});
    drawTexture(
        "edge_btm",
        {popupRect.x,
         popupRect.y + popupRect.height - 16.0f * popupScale + 7.0f * popupScale,
         popupRect.width,
         16.0f * popupScale});
    drawTexture("edge_lf", {popupRect.x, popupRect.y, 11.0f * popupScale, popupRect.height});
    drawTexture(
        "edge_rt",
        {popupRect.x + popupRect.width - 16.0f * popupScale + 6.0f * popupScale,
         popupRect.y,
         16.0f * popupScale,
         popupRect.height});
    drawTexture("cornr_UL", {popupRect.x, popupRect.y, 33.0f * popupScale, 32.0f * popupScale});
    drawTexture(
        "cornr_UR",
        {popupRect.x + popupRect.width - 39.0f * popupScale + 7.0f * popupScale,
         popupRect.y,
         39.0f * popupScale,
         32.0f * popupScale});
    drawTexture(
        "cornr_LL",
        {popupRect.x,
         popupRect.y + popupRect.height - 38.0f * popupScale + 7.0f * popupScale,
         33.0f * popupScale,
         38.0f * popupScale});
    drawTexture(
        "cornr_LR",
        {popupRect.x + popupRect.width - 39.0f * popupScale + 7.0f * popupScale,
         popupRect.y + popupRect.height - 38.0f * popupScale + 7.0f * popupScale,
         39.0f * popupScale,
         38.0f * popupScale});

    const float titleY = popupRect.y + 12.0f * popupScale;
    const float titleWidth = measureTextWidth("Create", entry.name, popupScale);
    drawText("Create", entry.name, popupRect.x + (popupRect.width - titleWidth) * 0.5f, titleY, InspectTitleColor, popupScale);

    float textY = popupRect.y + 42.0f * popupScale;

    for (const std::string &line : bodyLines)
    {
        drawText("SMALLNUM", line, popupRect.x + bodyX, textY, WhiteColor, popupScale);
        textY += bodyLineHeight;
    }
}

void NewGameScreen::renderClassInspectPopup(
    const ClassInspectEntry &entry,
    const MenuScreenBase::Rect &sourceRect,
    float scale)
{
    StatInspectEntry statEntry = {};
    statEntry.name = entry.name;
    statEntry.description = entry.description;
    renderStatInspectPopup(statEntry, sourceRect, scale);
}

void NewGameScreen::showCreationCompletionError()
{
    m_state.statusMessage.clear();
    m_creationCompletionErrorSeconds = CreationCompletionErrorDurationSeconds;
}

void NewGameScreen::renderCreationCompletionErrorMessageBox(
    const MenuScreenBase::Rect &rootRect,
    float scale)
{
    if (m_creationCompletionErrorSeconds <= 0.0f)
    {
        return;
    }

    const MenuScreenBase::Rect popupRect = scaledRect(
        rootRect.x,
        rootRect.y,
        scale,
        CreationCompletionErrorBoxX,
        140.0f,
        CreationCompletionErrorBoxWidth,
        100.0f);
    const float popupScale = scale;
    const float rightOverhang = 7.0f * popupScale;
    const float bottomOverhang = 7.0f * popupScale;

    drawTexture("parchment", popupRect);
    drawTexture("edge_top", {popupRect.x, popupRect.y, popupRect.width, 10.0f * popupScale});
    drawTexture(
        "edge_btm",
        {popupRect.x,
         popupRect.y + popupRect.height - 16.0f * popupScale + bottomOverhang,
         popupRect.width,
         16.0f * popupScale});
    drawTexture("edge_lf", {popupRect.x, popupRect.y, 11.0f * popupScale, popupRect.height});
    drawTexture(
        "edge_rt",
        {popupRect.x + popupRect.width - 16.0f * popupScale + rightOverhang,
         popupRect.y,
         16.0f * popupScale,
         popupRect.height});
    drawTexture("cornr_UL", {popupRect.x, popupRect.y, 33.0f * popupScale, 32.0f * popupScale});
    drawTexture(
        "cornr_UR",
        {popupRect.x + popupRect.width - 39.0f * popupScale + rightOverhang,
         popupRect.y,
         39.0f * popupScale,
         32.0f * popupScale});
    drawTexture(
        "cornr_LL",
        {popupRect.x,
         popupRect.y + popupRect.height - 38.0f * popupScale + bottomOverhang,
         33.0f * popupScale,
         38.0f * popupScale});
    drawTexture(
        "cornr_LR",
        {popupRect.x + popupRect.width - 39.0f * popupScale + rightOverhang,
         popupRect.y + popupRect.height - 38.0f * popupScale + bottomOverhang,
         39.0f * popupScale,
         38.0f * popupScale});

    const float textWidth = std::max(1.0f, popupRect.width - 32.0f * popupScale);
    const std::vector<std::string> lines = wrapTextToWidth(
        "SMALLNUM",
        CreationCompletionErrorText,
        textWidth,
        popupScale);
    const float lineHeight = static_cast<float>(fontHeight("SMALLNUM")) * popupScale;
    const float textHeight = lineHeight * static_cast<float>(lines.size());
    float textY = popupRect.y + (popupRect.height - textHeight) * 0.5f;

    for (const std::string &line : lines)
    {
        const float lineWidth = measureTextWidth("SMALLNUM", line, popupScale);
        drawText(
            "SMALLNUM",
            line,
            popupRect.x + (popupRect.width - lineWidth) * 0.5f,
            textY,
            WhiteColor,
            popupScale);
        textY += lineHeight;
    }
}

std::optional<MenuScreenBase::TexturePixelsBgra> NewGameScreen::buildCreationPreviewDollPixels(
    const CharacterDollEntry &entry,
    const CharacterDollTypeEntry *pDollType)
{
    const std::optional<TexturePixelsBgra> background = texturePixelsBgra(entry.backgroundAsset);

    if (!background.has_value()
        || background->physicalWidth <= 0
        || background->physicalHeight <= 0
        || background->logicalWidth <= 0
        || background->logicalHeight <= 0)
    {
        return std::nullopt;
    }

    TexturePixelsBgra composite = *background;
    const float physicalScaleX =
        static_cast<float>(composite.physicalWidth) / static_cast<float>(std::max(1, composite.logicalWidth));
    const float physicalScaleY =
        static_cast<float>(composite.physicalHeight) / static_cast<float>(std::max(1, composite.logicalHeight));
    const auto compositeLayer =
        [this, &composite, physicalScaleX, physicalScaleY](
            const std::string &assetName,
            int logicalX,
            int logicalY)
        {
            if (assetName.empty() || assetName == "none" || assetName == "null")
            {
                return;
            }

            const std::optional<TexturePixelsBgra> layer = texturePixelsBgra(assetName);

            if (!layer.has_value()
                || layer->physicalWidth <= 0
                || layer->physicalHeight <= 0
                || layer->pixels.empty())
            {
                return;
            }

            const int targetX = static_cast<int>(std::lround(static_cast<float>(logicalX) * physicalScaleX));
            const int targetY = static_cast<int>(std::lround(static_cast<float>(logicalY) * physicalScaleY));

            for (int sourceY = 0; sourceY < layer->physicalHeight; ++sourceY)
            {
                const int destinationY = targetY + sourceY;

                if (destinationY < 0 || destinationY >= composite.physicalHeight)
                {
                    continue;
                }

                for (int sourceX = 0; sourceX < layer->physicalWidth; ++sourceX)
                {
                    const int destinationX = targetX + sourceX;

                    if (destinationX < 0 || destinationX >= composite.physicalWidth)
                    {
                        continue;
                    }

                    const size_t sourceOffset =
                        (static_cast<size_t>(sourceY) * static_cast<size_t>(layer->physicalWidth)
                         + static_cast<size_t>(sourceX)) * 4;
                    const uint8_t sourceAlpha = layer->pixels[sourceOffset + 3];

                    if (sourceAlpha == 0)
                    {
                        continue;
                    }

                    const size_t destinationOffset =
                        (static_cast<size_t>(destinationY) * static_cast<size_t>(composite.physicalWidth)
                         + static_cast<size_t>(destinationX)) * 4;

                    if (sourceAlpha == 255)
                    {
                        composite.pixels[destinationOffset + 0] = layer->pixels[sourceOffset + 0];
                        composite.pixels[destinationOffset + 1] = layer->pixels[sourceOffset + 1];
                        composite.pixels[destinationOffset + 2] = layer->pixels[sourceOffset + 2];
                        composite.pixels[destinationOffset + 3] = 255;
                        continue;
                    }

                    const uint32_t inverseAlpha = 255u - sourceAlpha;

                    for (size_t channel = 0; channel < 3; ++channel)
                    {
                        composite.pixels[destinationOffset + channel] = static_cast<uint8_t>(
                            (static_cast<uint32_t>(layer->pixels[sourceOffset + channel]) * sourceAlpha
                             + static_cast<uint32_t>(composite.pixels[destinationOffset + channel]) * inverseAlpha)
                            / 255u);
                    }

                    composite.pixels[destinationOffset + 3] = static_cast<uint8_t>(
                        std::min<uint32_t>(
                            255u,
                            sourceAlpha
                            + static_cast<uint32_t>(composite.pixels[destinationOffset + 3]) * inverseAlpha / 255u));
                }
            }
        };

    compositeLayer(entry.bodyAsset, entry.bodyOffsetX, entry.bodyOffsetY);

    if (pDollType != nullptr)
    {
        compositeLayer(entry.leftHandOpenAsset, pDollType->leftHandFingersX, pDollType->leftHandFingersY);
        compositeLayer(entry.rightHandOpenAsset, pDollType->rightHandOpenX, pDollType->rightHandOpenY);
    }

    return composite;
}

Character NewGameScreen::buildCharacter() const
{
    return buildCharacterFromState(m_state);
}

Character NewGameScreen::buildCharacterFromState(const CreationState &state) const
{
    Character character = {};
    const CreationCandidate &candidate = candidateForState(state);
    const CharacterDollEntry *pEntry = characterEntryForState(state);

    character.name = trimCopy(state.name);
    character.className = classNameForState(state);
    character.role = displayClassName(character.className);
    character.characterDataId = candidate.characterDataId;
    character.voiceId = state.selectedVoiceId;
    character.birthYear = 1150;
    character.level = 1;
    character.skillPoints = 0;
    character.might = static_cast<uint32_t>(state.currentStats[static_cast<size_t>(StatId::Might)]);
    character.intellect = static_cast<uint32_t>(state.currentStats[static_cast<size_t>(StatId::Intellect)]);
    character.personality = static_cast<uint32_t>(state.currentStats[static_cast<size_t>(StatId::Personality)]);
    character.endurance = static_cast<uint32_t>(state.currentStats[static_cast<size_t>(StatId::Endurance)]);
    character.accuracy = static_cast<uint32_t>(state.currentStats[static_cast<size_t>(StatId::Accuracy)]);
    character.speed = static_cast<uint32_t>(state.currentStats[static_cast<size_t>(StatId::Speed)]);
    character.luck = static_cast<uint32_t>(state.currentStats[static_cast<size_t>(StatId::Luck)]);

    if (pEntry != nullptr)
    {
        character.portraitTextureName = portraitTextureNameForEntry(*pEntry);
        character.portraitPictureId = pEntry->id > 0 ? (pEntry->id - 1) : 0;
        character.sexId = pEntry->defaultSex;
        character.raceId = pEntry->raceId >= 0 ? static_cast<uint32_t>(pEntry->raceId) : 0;
    }

    for (const std::string &skillName : state.defaultSkills)
    {
        character.skills[skillName] = {skillName, 1, SkillMastery::Normal};
    }

    for (const std::string &skillName : state.selectedOptionalSkills)
    {
        character.skills[skillName] = {skillName, 1, SkillMastery::Normal};
    }

    GameMechanics::refreshCharacterBaseResources(
        character,
        true,
        m_pGameData != nullptr ? &m_pGameData->classMultiplierTable() : nullptr);

    if (m_debugGodLichRoster)
    {
        applyDebugGodLichCharacter(
            character,
            m_pGameData != nullptr ? &m_pGameData->classMultiplierTable() : nullptr,
            m_pGameData != nullptr ? &m_pGameData->itemTable() : nullptr,
            m_pGameData != nullptr ? &m_pGameData->spellTable() : nullptr);
    }

    return character;
}

std::vector<Character> NewGameScreen::buildPartyCharacters() const
{
    std::vector<Character> characters;
    const size_t count = m_debugGodLichRoster ? 1 : std::min<size_t>(m_partySize, m_partyStates.size());
    characters.reserve(count);

    for (size_t slotIndex = 0; slotIndex < count; ++slotIndex)
    {
        characters.push_back(buildCharacterFromState(m_partyStates[slotIndex]));
    }

    return characters;
}

void NewGameScreen::confirmCreation()
{
    endNameEditing(true);
    saveActivePartyState();

    for (size_t slotIndex = 0; slotIndex < (m_debugGodLichRoster ? 1 : m_partySize); ++slotIndex)
    {
        if (trimCopy(m_partyStates[slotIndex].name).empty())
        {
            switchActivePartySlot(slotIndex);
            m_state.statusMessage = "Character name cannot be empty.";
            return;
        }
    }

    if (!m_allowIncompleteCharacterCreation)
    {
        for (size_t slotIndex = 0; slotIndex < (m_debugGodLichRoster ? 1 : m_partySize); ++slotIndex)
        {
            const CreationState &state = m_partyStates[slotIndex];

            if (bonusPoolForState(state) > 0)
            {
                switchActivePartySlot(slotIndex);
                showCreationCompletionError();
                return;
            }

            const size_t requiredSkillCount =
                std::min(MaximumOptionalSkillSelections, state.optionalSkills.size());

            if (state.selectedOptionalSkills.size() < requiredSkillCount)
            {
                switchActivePartySlot(slotIndex);
                showCreationCompletionError();
                return;
            }
        }
    }

    if (m_continueAction)
    {
        const std::vector<Character> characters = buildPartyCharacters();
        GAMEPLAY_DEBUG_TRACE(
            "new_game_party_created continent_id=" + std::to_string(m_selectedContinent.id)
            + " continent_key=\"" + m_selectedContinent.key + "\""
            + " continent_name=\"" + m_selectedContinent.name + "\""
            + " member_count=" + std::to_string(characters.size()));

        for (size_t memberIndex = 0; memberIndex < characters.size(); ++memberIndex)
        {
            const Character &member = characters[memberIndex];
            GAMEPLAY_DEBUG_TRACE(
                "new_game_party_member member_index=" + std::to_string(memberIndex)
                + " name=\"" + member.name + "\""
                + " class=\"" + member.className + "\""
                + " role=\"" + member.role + "\""
                + " race_id=" + std::to_string(member.raceId)
                + " sex_id=" + std::to_string(member.sexId)
                + " portrait_id=" + std::to_string(member.portraitPictureId)
                + " voice_id=" + std::to_string(member.voiceId)
                + " might=" + std::to_string(member.might)
                + " intellect=" + std::to_string(member.intellect)
                + " personality=" + std::to_string(member.personality)
                + " endurance=" + std::to_string(member.endurance)
                + " accuracy=" + std::to_string(member.accuracy)
                + " speed=" + std::to_string(member.speed)
                + " luck=" + std::to_string(member.luck));

            std::vector<std::pair<std::string, CharacterSkill>> skills(member.skills.begin(), member.skills.end());
            std::sort(
                skills.begin(),
                skills.end(),
                [](const std::pair<std::string, CharacterSkill> &left,
                    const std::pair<std::string, CharacterSkill> &right)
                {
                    return left.first < right.first;
                });

            for (const auto &[skillName, skill] : skills)
            {
                GAMEPLAY_DEBUG_TRACE(
                    "new_game_party_skill member_index=" + std::to_string(memberIndex)
                    + " name=\"" + skillName + "\""
                    + " level=" + std::to_string(skill.level)
                    + " mastery=" + std::to_string(static_cast<uint32_t>(skill.mastery)));
            }
        }

        m_continueAction(characters, m_selectedContinent.id);
    }
}

void NewGameScreen::cancelCreation()
{
    endNameEditing(true);

    if (m_backAction)
    {
        m_backAction();
    }
}

void NewGameScreen::selectContinent(const std::string &continentKey)
{
    if (m_pGameData == nullptr)
    {
        return;
    }

    const MergedCharacterSelectionTable &selectionTable = m_pGameData->mergedCharacterSelectionTable();
    const MergedCharacterSelectionContinent *pContinent = findNewGameContinent(selectionTable, continentKey);

    if (pContinent == nullptr)
    {
        return;
    }

    m_selectedContinent = {
        .id = pContinent->id,
        .key = pContinent->key,
        .name = pContinent->name,
    };
    GAMEPLAY_DEBUG_TRACE(
        "new_game_continent_selected continent_id=" + std::to_string(m_selectedContinent.id)
        + " continent_key=\"" + m_selectedContinent.key + "\""
        + " continent_name=\"" + m_selectedContinent.name + "\"");
    m_stage = FlowStage::CharacterCreation;
    m_characterCreationInitialized = false;
    initializeCharacterCreationForSelectedContinent();
}

bool NewGameScreen::ensureLayoutLoaded()
{
    if (m_layoutLoaded)
    {
        return true;
    }

    m_layoutManager.clear();
    m_layoutLoaded = m_layoutManager.loadLayoutFile(assetFileSystem(), CharacterCreationLayoutPath);
    return m_layoutLoaded;
}

bool NewGameScreen::ensureContinentLayoutLoaded()
{
    if (m_continentLayoutLoaded)
    {
        return true;
    }

    m_continentLayoutManager.clear();
    m_continentLayoutLoaded =
        m_continentLayoutManager.loadLayoutFile(assetFileSystem(), ContinentSelectionLayoutPath);
    return m_continentLayoutLoaded;
}

std::optional<MenuScreenBase::Rect> NewGameScreen::resolveLayoutRect(
    const std::string &layoutId,
    float fallbackWidth,
    float fallbackHeight) const
{
    if (!m_layoutLoaded)
    {
        return std::nullopt;
    }

    std::unordered_set<std::string> visited;
    const std::optional<ResolvedLayoutElement> resolved = resolveLayoutElementRecursive(
        m_layoutManager,
        layoutId,
        frameWidth(),
        frameHeight(),
        fallbackWidth,
        fallbackHeight,
        visited);

    if (!resolved.has_value())
    {
        return std::nullopt;
    }

    return MenuScreenBase::Rect{
        std::round(resolved->x),
        std::round(resolved->y),
        std::round(resolved->width),
        std::round(resolved->height)
    };
}

std::optional<MenuScreenBase::Rect> NewGameScreen::resolveContinentLayoutRect(
    const std::string &layoutId,
    float fallbackWidth,
    float fallbackHeight) const
{
    if (!m_continentLayoutLoaded)
    {
        return std::nullopt;
    }

    std::unordered_set<std::string> visited;
    const std::optional<ResolvedLayoutElement> resolved = resolveLayoutElementRecursive(
        m_continentLayoutManager,
        layoutId,
        frameWidth(),
        frameHeight(),
        fallbackWidth,
        fallbackHeight,
        visited);

    if (!resolved.has_value())
    {
        return std::nullopt;
    }

    return MenuScreenBase::Rect{
        std::round(resolved->x),
        std::round(resolved->y),
        std::round(resolved->width),
        std::round(resolved->height)
    };
}

MenuScreenBase::ButtonVisualSet NewGameScreen::resolveButtonVisuals(
    const std::string &layoutId,
    const ButtonVisualSet &fallbackVisuals) const
{
    if (!m_layoutLoaded)
    {
        return fallbackVisuals;
    }

    const UiLayoutManager::LayoutElement *pLayout = m_layoutManager.findElement(layoutId);

    if (pLayout == nullptr)
    {
        return fallbackVisuals;
    }

    ButtonVisualSet visuals = fallbackVisuals;

    if (!pLayout->primaryAsset.empty())
    {
        visuals.defaultTextureName = pLayout->primaryAsset;
    }

    if (!pLayout->hoverAsset.empty())
    {
        visuals.highlightedTextureName = pLayout->hoverAsset;
    }

    if (!pLayout->pressedAsset.empty())
    {
        visuals.pressedTextureName = pLayout->pressedAsset;
    }

    return visuals;
}

MenuScreenBase::ButtonVisualSet NewGameScreen::resolveContinentButtonVisuals(
    const std::string &layoutId,
    const ButtonVisualSet &fallbackVisuals) const
{
    if (!m_continentLayoutLoaded)
    {
        return fallbackVisuals;
    }

    const UiLayoutManager::LayoutElement *pLayout = m_continentLayoutManager.findElement(layoutId);

    if (pLayout == nullptr)
    {
        return fallbackVisuals;
    }

    ButtonVisualSet visuals = fallbackVisuals;

    if (!pLayout->primaryAsset.empty())
    {
        visuals.defaultTextureName = pLayout->primaryAsset;
    }

    if (!pLayout->hoverAsset.empty())
    {
        visuals.highlightedTextureName = pLayout->hoverAsset;
    }

    if (!pLayout->pressedAsset.empty())
    {
        visuals.pressedTextureName = pLayout->pressedAsset;
    }

    return visuals;
}

std::string NewGameScreen::resolveAssetName(const std::string &layoutId, const std::string &fallbackAssetName) const
{
    if (!m_layoutLoaded)
    {
        return fallbackAssetName;
    }

    const UiLayoutManager::LayoutElement *pLayout = m_layoutManager.findElement(layoutId);

    if (pLayout == nullptr || pLayout->primaryAsset.empty())
    {
        return fallbackAssetName;
    }

    return pLayout->primaryAsset;
}

std::string NewGameScreen::resolveContinentAssetName(
    const std::string &layoutId,
    const std::string &fallbackAssetName) const
{
    if (!m_continentLayoutLoaded)
    {
        return fallbackAssetName;
    }

    const UiLayoutManager::LayoutElement *pLayout = m_continentLayoutManager.findElement(layoutId);

    if (pLayout == nullptr || pLayout->primaryAsset.empty())
    {
        return fallbackAssetName;
    }

    return pLayout->primaryAsset;
}

MenuScreenBase::ButtonState NewGameScreen::drawEllipseButton(const ButtonVisualSet &visuals, const Rect &rect)
{
    const float radiusX = rect.width * 0.5f;
    const float radiusY = rect.height * 0.5f;
    const float centerX = rect.x + radiusX;
    const float centerY = rect.y + radiusY;
    ButtonState state = {};

    if (radiusX > 0.0f && radiusY > 0.0f)
    {
        const float normalizedX = (mouseX() - centerX) / radiusX;
        const float normalizedY = (mouseY() - centerY) / radiusY;
        state.hovered = normalizedX * normalizedX + normalizedY * normalizedY <= 1.0f;
    }

    state.pressed = state.hovered && leftMouseDown();
    state.clicked = state.hovered && leftMouseJustReleased();

    const std::string *pTextureName = &visuals.defaultTextureName;

    if (state.pressed && !visuals.pressedTextureName.empty())
    {
        pTextureName = &visuals.pressedTextureName;
    }
    else if (state.hovered && !visuals.highlightedTextureName.empty())
    {
        pTextureName = &visuals.highlightedTextureName;
    }

    if (!pTextureName->empty())
    {
        drawTexture(*pTextureName, rect);
    }

    return state;
}

void NewGameScreen::drawContinentSelection(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);

    ensureContinentLayoutLoaded();

    const float fallbackScale = std::min(
        static_cast<float>(frameWidth()) / RootWidth,
        static_cast<float>(frameHeight()) / RootHeight);
    const float fallbackRootX = (static_cast<float>(frameWidth()) - RootWidth * fallbackScale) * 0.5f;
    const float fallbackRootY = (static_cast<float>(frameHeight()) - RootHeight * fallbackScale) * 0.5f;
    const MenuScreenBase::Rect rootRect =
        resolveContinentLayoutRect("ContinentSelectionRoot", RootWidth, RootHeight).value_or(
            scaledRect(fallbackRootX, fallbackRootY, fallbackScale, 0.0f, 0.0f, RootWidth, RootHeight));
    const float scale = rootRect.width > 0.0f ? rootRect.width / RootWidth : fallbackScale;
    const float rootX = rootRect.x;
    const float rootY = rootRect.y;
    const auto resolveRect =
        [this, rootX, rootY, scale](const std::string &layoutId, float x, float y, float width, float height)
        {
            return resolveContinentLayoutRect(layoutId, width, height).value_or(
                scaledRect(rootX, rootY, scale, x, y, width, height));
        };
    const bool returnPressed = m_returnPressed;
    const bool escapePressed = m_escapePressed;
    m_returnPressed = false;
    m_escapePressed = false;

    if (escapePressed)
    {
        cancelCreation();
        return;
    }

    drawTexture(resolveContinentAssetName("ContinentSelectionBackground", "slbackgr"), rootRect);

    const MenuScreenBase::Rect jadameRect =
        resolveRect("ContinentSelectionJadameButton", 208.0f, 31.0f, 222.0f, 222.0f);
    const MenuScreenBase::Rect antagarichRect =
        resolveRect("ContinentSelectionAntagarichButton", 322.0f, 228.0f, 222.0f, 222.0f);
    const MenuScreenBase::Rect enrothRect =
        resolveRect("ContinentSelectionEnrothButton", 94.0f, 229.0f, 222.0f, 222.0f);
    const ButtonState jadameState = drawEllipseButton(
        resolveContinentButtonVisuals("ContinentSelectionJadameButton", {"sljadamdw", "sljadamup", "sljadamup"}),
        jadameRect);
    const ButtonState antagarichState = drawEllipseButton(
        resolveContinentButtonVisuals("ContinentSelectionAntagarichButton", {"slantagdw", "slantagup", "slantagup"}),
        antagarichRect);
    const ButtonState enrothState = drawEllipseButton(
        resolveContinentButtonVisuals("ContinentSelectionEnrothButton", {"slenrothdw", "slenrothup", "slenrothup"}),
        enrothRect);

    if (jadameState.clicked)
    {
        playUiClickSound(SoundId::ClickIn);
        selectContinent("jadame");
    }
    else if (antagarichState.clicked)
    {
        playUiClickSound(SoundId::ClickIn);
        selectContinent("antagarich");
    }
    else if (enrothState.clicked)
    {
        playUiClickSound(SoundId::ClickIn);
        selectContinent("enroth");
    }
    else if (returnPressed)
    {
        playUiClickSound(SoundId::ClickIn);
        selectContinent(DefaultNewGameContinentKey);
    }
}

void NewGameScreen::drawScreen(float deltaSeconds)
{
    if (m_stage == FlowStage::ContinentSelection)
    {
        resetNameBackspaceRepeat();
        drawContinentSelection(deltaSeconds);
        return;
    }

    initializeCharacterCreationForSelectedContinent();
    ensureLayoutLoaded();
    updateNameBackspaceRepeat(deltaSeconds);

    if (m_creationCompletionErrorSeconds > 0.0f)
    {
        m_creationCompletionErrorSeconds = std::max(0.0f, m_creationCompletionErrorSeconds - deltaSeconds);
    }

    const float fallbackScale = std::min(
        static_cast<float>(frameWidth()) / RootWidth,
        static_cast<float>(frameHeight()) / RootHeight);
    const float fallbackRootX = (static_cast<float>(frameWidth()) - RootWidth * fallbackScale) * 0.5f;
    const float fallbackRootY = (static_cast<float>(frameHeight()) - RootHeight * fallbackScale) * 0.5f;
    const MenuScreenBase::Rect rootRect = resolveLayoutRect("CharacterCreationRoot", RootWidth, RootHeight).value_or(
        scaledRect(fallbackRootX, fallbackRootY, fallbackScale, 0.0f, 0.0f, RootWidth, RootHeight));
    const float scale = rootRect.width > 0.0f ? rootRect.width / RootWidth : fallbackScale;
    const float rootX = rootRect.x;
    const float rootY = rootRect.y;
    const auto resolveRect =
        [this, rootX, rootY, scale](const std::string &layoutId, float x, float y, float width, float height)
        {
            return resolveLayoutRect(layoutId, width, height).value_or(scaledRect(rootX, rootY, scale, x, y, width, height));
        };
    const bool returnPressed = m_returnPressed;
    const bool escapePressed = m_escapePressed;
    m_returnPressed = false;
    m_escapePressed = false;

    if (escapePressed)
    {
        if (m_state.nameEditing)
        {
            endNameEditing(true);
        }
        else
        {
            cancelCreation();
            return;
        }
    }

    drawTexture(resolveAssetName("CharacterCreationBackground", "makeme"), rootRect);

    const CharacterDollEntry *pEntry = selectedCharacterEntry();
    const std::string fontName = "create";
    const MenuScreenBase::Rect nameFieldRect =
        resolveRect("CharacterCreationNameField", 78.0f, 68.0f, 110.0f, 24.0f);
    const MenuScreenBase::Rect nameValueRect =
        resolveRect("CharacterCreationNameValue", 82.0f, 72.0f, 0.0f, 0.0f);
    const MenuScreenBase::Rect classValueRect =
        resolveRect("CharacterCreationClassValue", 59.0f, 117.0f, 0.0f, 0.0f);
    const MenuScreenBase::Rect classLeftRect =
        resolveRect("CharacterCreationClassLeftButton", 65.0f, 99.0f, 17.0f, 17.0f);
    const MenuScreenBase::Rect classRightRect =
        resolveRect("CharacterCreationClassRightButton", 83.0f, 99.0f, 17.0f, 17.0f);
    const MenuScreenBase::Rect portraitImageRect =
        resolveRect("CharacterCreationPortraitImage", 11.0f, 161.0f, 59.0f, 79.0f);
    const MenuScreenBase::Rect portraitLeftRect =
        resolveRect("CharacterCreationPortraitLeftButton", 73.0f, 160.0f, 31.0f, 17.0f);
    const MenuScreenBase::Rect portraitRightRect =
        resolveRect("CharacterCreationPortraitRightButton", 167.0f, 160.0f, 31.0f, 17.0f);
    const MenuScreenBase::Rect voiceLeftRect =
        resolveRect("CharacterCreationVoiceLeftButton", 73.0f, 188.0f, 31.0f, 17.0f);
    const MenuScreenBase::Rect voiceRightRect =
        resolveRect("CharacterCreationVoiceRightButton", 167.0f, 188.0f, 31.0f, 17.0f);
    const MenuScreenBase::Rect voiceDefaultRect =
        resolveRect("CharacterCreationVoiceDefaultButton", 92.0f, 219.0f, 105.0f, 37.0f);
    const MenuScreenBase::Rect bonusPoolValueRect =
        resolveRect("CharacterCreationBonusPoolValue", 170.0f, 265.0f, 0.0f, 0.0f);

    if (leftMouseJustReleased() && hitTest(nameFieldRect))
    {
        beginNameEditing();
    }

    const std::string displayedName = m_state.nameEditing ? m_state.nameEditBuffer : m_state.name;
    drawText(fontName, displayedName, nameValueRect.x, nameValueRect.y, WhiteColor, scale);

    if (m_state.nameEditing)
    {
        const float cursorX = nameValueRect.x + measureTextWidth(fontName, displayedName, scale) + 2.0f * scale;
        const float cursorY = nameValueRect.y;
        drawText(fontName, "_", cursorX, cursorY, WhiteColor, scale);
    }

    const std::string displayedClassName = displayClassName(selectedClassName());
    drawText(
        fontName,
        displayedClassName,
        classValueRect.x,
        classValueRect.y,
        WhiteColor,
        scale);

    std::optional<std::pair<MenuScreenBase::Rect, const ClassInspectEntry *>> hoveredClassInspect;

    if (rightMouseDown() && m_pGameData != nullptr)
    {
        const float classTextWidth = measureTextWidth(fontName, displayedClassName, scale);
        const float classTextHeight = static_cast<float>(fontHeight(fontName)) * scale;
        const MenuScreenBase::Rect classTextRect = {
            classValueRect.x,
            classValueRect.y,
            classTextWidth,
            classTextHeight + 3.0f * scale
        };

        if (hitTest(classTextRect))
        {
            hoveredClassInspect =
                std::make_pair(classTextRect, m_pGameData->characterInspectTable().getClass(selectedClassName()));
        }
    }

    if (pEntry != nullptr)
    {
        drawTexture(portraitTextureNameForEntry(*pEntry), portraitImageRect);
        drawTexture("selring", portraitImageRect);
    }

    const ButtonState portraitLeftState = drawButton(
        resolveButtonVisuals("CharacterCreationPortraitLeftButton", {"cc_up_L", "cc_ht_L", "cc_dn_L"}),
        portraitLeftRect);
    const ButtonState portraitRightState = drawButton(
        resolveButtonVisuals("CharacterCreationPortraitRightButton", {"cc_up_R", "cc_ht_R", "cc_dn_R"}),
        portraitRightRect);
    const ButtonState classLeftState = drawButton(
        resolveButtonVisuals("CharacterCreationClassLeftButton", {"slclasslu", "slclasslu", "slclassld"}),
        classLeftRect);
    const ButtonState classRightState = drawButton(
        resolveButtonVisuals("CharacterCreationClassRightButton", {"slclassru", "slclassru", "slclassrd"}),
        classRightRect);
    const ButtonState voiceLeftState = drawButton(
        resolveButtonVisuals("CharacterCreationVoiceLeftButton", {"cc_up_L", "cc_ht_L", "cc_dn_L"}),
        voiceLeftRect);
    const ButtonState voiceRightState = drawButton(
        resolveButtonVisuals("CharacterCreationVoiceRightButton", {"cc_up_R", "cc_ht_R", "cc_dn_R"}),
        voiceRightRect);
    const ButtonState defaultVoiceState = drawButton(
        resolveButtonVisuals("CharacterCreationVoiceDefaultButton", {"bt_DfltU", "bt_DfltH", "bt_DfltD"}),
        voiceDefaultRect);

    if (portraitLeftState.clicked)
    {
        playUiClickSound(SoundId::SelectingNewCharacter);
        cycleCandidate(-1);
        playVoicePreview();
    }
    else if (portraitRightState.clicked)
    {
        playUiClickSound(SoundId::SelectingNewCharacter);
        cycleCandidate(1);
        playVoicePreview();
    }
    else if (classLeftState.clicked)
    {
        playUiClickSound(SoundId::SelectingNewCharacter);
        cycleClass(-1);
    }
    else if (classRightState.clicked)
    {
        playUiClickSound(SoundId::SelectingNewCharacter);
        cycleClass(1);
    }
    else if (voiceLeftState.clicked)
    {
        playUiClickSound(SoundId::SelectingNewCharacter);
        cycleVoice(-1);
        playVoicePreview();
    }
    else if (voiceRightState.clicked)
    {
        playUiClickSound(SoundId::SelectingNewCharacter);
        cycleVoice(1);
        playVoicePreview();
    }
    else if (defaultVoiceState.clicked && pEntry != nullptr)
    {
        endNameEditing(true);
        m_state.selectedVoiceId = static_cast<int>(pEntry->defaultVoiceId);
        m_state.statusMessage.clear();
        playUiClickSound(SoundId::SelectingNewCharacter);
        playVoicePreview();
    }

    drawText(
        fontName,
        std::to_string(currentBonusPool()),
        bonusPoolValueRect.x,
        bonusPoolValueRect.y,
        WhiteColor,
        scale);

    std::optional<std::pair<MenuScreenBase::Rect, const StatInspectEntry *>> hoveredStatInspect;

    for (size_t statIndex = 0; statIndex < static_cast<size_t>(StatId::Count); ++statIndex)
    {
        const float y = StatValueY[statIndex];
        const MenuScreenBase::Rect labelRect =
            resolveRect(StatLabelLayoutIds[statIndex], 2.0f, y - 3.0f, 0.0f, 0.0f);
        const float labelX = labelRect.x;
        const float labelY = labelRect.y;
        drawText(
            fontName,
            StatLabels[statIndex],
            labelX,
            labelY,
            statLabelColorForStats(m_state.baseStats, statIndex),
            scale);

        const MenuScreenBase::Rect minusRect =
            resolveRect(StatMinusButtonLayoutIds[statIndex], 100.0f, y, 16.0f, 17.0f);
        const MenuScreenBase::Rect plusRect =
            resolveRect(StatPlusButtonLayoutIds[statIndex], 177.0f, y, 16.0f, 17.0f);
        const ButtonState minusState = drawButton(
            resolveButtonVisuals(StatMinusButtonLayoutIds[statIndex], {"cMinup", "cMinHT", "cMindn"}),
            minusRect);
        const ButtonState plusState = drawButton(
            resolveButtonVisuals(StatPlusButtonLayoutIds[statIndex], {"cPlusup", "cPlusht", "cPlusdn"}),
            plusRect);

        if (minusState.clicked)
        {
            endNameEditing(true);
            playUiClickSound(SoundId::ClickMinus);
            tryDecreaseStat(static_cast<StatId>(statIndex));
        }
        else if (plusState.clicked)
        {
            endNameEditing(true);
            playUiClickSound(SoundId::ClickPlus);
            tryIncreaseStat(static_cast<StatId>(statIndex));
        }

        uint32_t statColor = WhiteColor;

        if (m_state.currentStats[statIndex] > m_state.baseStats[statIndex])
        {
            statColor = GreenColor;
        }
        else if (m_state.currentStats[statIndex] < m_state.baseStats[statIndex])
        {
            statColor = RedColor;
        }

        const std::string statValueText = std::to_string(m_state.currentStats[statIndex]);
        const float fallbackValueX = 145.0f + (m_state.currentStats[statIndex] < 10 ? 3.0f : 0.0f);
        const MenuScreenBase::Rect valueRect =
            resolveRect(StatValueLayoutIds[statIndex], fallbackValueX, y, 0.0f, 0.0f);
        const float valuePixelX = valueRect.x;
        const float valuePixelY = valueRect.y;
        drawText(fontName, statValueText, valuePixelX, valuePixelY, statColor, scale);

        if (rightMouseDown() && m_pGameData != nullptr)
        {
            const float labelWidth = measureTextWidth(fontName, StatLabels[statIndex], scale);
            const float valueWidth = measureTextWidth(fontName, statValueText, scale);
            const float rowHeight = static_cast<float>(fontHeight(fontName)) * scale;
            const MenuScreenBase::Rect rowRect = {
                std::min(labelX, valuePixelX),
                std::min(labelY, valuePixelY),
                std::max(labelX + labelWidth, valuePixelX + valueWidth) - std::min(labelX, valuePixelX),
                rowHeight + 3.0f * scale
            };

            if (hitTest(rowRect))
            {
                hoveredStatInspect =
                    std::make_pair(rowRect, m_pGameData->characterInspectTable().getStat(StatLabels[statIndex]));
            }
        }
    }

    std::vector<std::string> selectedSkills = m_state.defaultSkills;
    struct HoveredSkillInspect
    {
        MenuScreenBase::Rect rect = {};
        const SkillInspectEntry *pEntry = nullptr;
        std::string skillName;
    };
    std::optional<HoveredSkillInspect> hoveredSkillInspect;
    const Character inspectCharacter = buildCharacter();

    for (const std::string &skillName : m_state.optionalSkills)
    {
        if (std::find(m_state.selectedOptionalSkills.begin(), m_state.selectedOptionalSkills.end(), skillName)
            != m_state.selectedOptionalSkills.end())
        {
            selectedSkills.push_back(skillName);
        }
    }

    auto drawCenteredSkillText =
        [this, &fontName, scale](
            const std::string &text,
            float centerX,
            float centerY,
            uint32_t color) -> MenuScreenBase::Rect
        {
            const auto splitLabel =
                [this, &fontName, scale](const std::string &label) -> std::vector<std::string>
                {
                    const float multilineThreshold = measureTextWidth(fontName, "Body Building", scale);

                    if (measureTextWidth(fontName, label, scale) < multilineThreshold)
                    {
                        return {label};
                    }

                    const size_t separator = label.find_last_of(" -");

                    if (separator == std::string::npos || separator == 0 || separator + 1 >= label.size())
                    {
                        return {label};
                    }

                    std::string firstLine = trimCopy(label.substr(0, separator));
                    std::string secondLine = trimCopy(label.substr(separator + 1));

                    if (firstLine.empty() || secondLine.empty())
                    {
                        return {label};
                    }

                    return {std::move(firstLine), std::move(secondLine)};
                };
            const std::vector<std::string> lines = splitLabel(text);

            if (lines.size() > 1)
            {
                const float firstLineWidth = measureTextWidth(fontName, lines[0], scale);
                const float secondLineWidth = measureTextWidth(fontName, lines[1], scale);
                const float width = std::max(
                    firstLineWidth,
                    secondLineWidth);
                const float lineHeight = static_cast<float>(fontHeight(fontName)) * scale;
                const float lineGap = -2.0f * scale;
                const float totalHeight = lineHeight * 2.0f + lineGap;
                const float y = centerY - totalHeight * 0.5f;
                const float firstLineX = centerX - firstLineWidth * 0.5f;
                const float secondLineX = centerX - secondLineWidth * 0.5f;
                drawText(fontName, lines[0], firstLineX, y, color, scale);
                drawText(fontName, lines[1], secondLineX, y + lineHeight + lineGap, color, scale);
                return {centerX - width * 0.5f, y, width, totalHeight};
            }

            const float width = measureTextWidth(fontName, text, scale);
            const float height = static_cast<float>(fontHeight(fontName)) * scale;
            const float x = centerX - width * 0.5f;
            const float y = centerY - height * 0.5f;
            drawText(fontName, text, x, y, color, scale);
            return {x, y, width, height};
        };

    for (size_t slotIndex = 0; slotIndex < SelectedSkillPositions.size(); ++slotIndex)
    {
        const MenuScreenBase::Rect skillAnchorRect = resolveRect(
            SelectedSkillLayoutIds[slotIndex],
            SelectedSkillPositions[slotIndex].x,
            SelectedSkillPositions[slotIndex].y,
            0.0f,
            0.0f);

        if (slotIndex >= selectedSkills.size())
        {
            drawCenteredSkillText("None", skillAnchorRect.x, skillAnchorRect.y, WhiteColor);
            continue;
        }

        const std::string &skillName = selectedSkills[slotIndex];
        const bool isDefaultSkill =
            std::find(m_state.defaultSkills.begin(), m_state.defaultSkills.end(), skillName) != m_state.defaultSkills.end();
        const uint32_t color = isDefaultSkill ? YellowColor : BlueColor;
        const std::string displayName = characterCreationSkillDisplayName(skillName);
        const MenuScreenBase::Rect clickRect =
            drawCenteredSkillText(displayName, skillAnchorRect.x, skillAnchorRect.y, color);

        if (rightMouseDown() && hitTest(clickRect) && m_pGameData != nullptr)
        {
            hoveredSkillInspect = HoveredSkillInspect{
                clickRect,
                m_pGameData->characterInspectTable().getSkill(skillName),
                skillName};
        }

        if (!isDefaultSkill && leftMouseJustReleased() && hitTest(clickRect))
        {
            endNameEditing(true);
            playUiClickSound(SoundId::SelectingNewCharacter);
            tryToggleOptionalSkill(skillName);
        }
    }

    for (size_t slotIndex = 0; slotIndex < AvailableSkillPositions.size() && slotIndex < m_state.optionalSkills.size(); ++slotIndex)
    {
        const std::string &skillName = m_state.optionalSkills[slotIndex];
        const bool isSelected =
            std::find(m_state.selectedOptionalSkills.begin(), m_state.selectedOptionalSkills.end(), skillName)
            != m_state.selectedOptionalSkills.end();
        const MenuScreenBase::Rect skillAnchorRect = resolveRect(
            AvailableSkillLayoutIds[slotIndex],
            AvailableSkillPositions[slotIndex].x,
            AvailableSkillPositions[slotIndex].y,
            0.0f,
            0.0f);
        const std::string displayName = characterCreationSkillDisplayName(skillName);
        const MenuScreenBase::Rect clickRect =
            drawCenteredSkillText(displayName, skillAnchorRect.x, skillAnchorRect.y, isSelected ? BlueColor : WhiteColor);

        if (rightMouseDown() && hitTest(clickRect) && m_pGameData != nullptr)
        {
            hoveredSkillInspect = HoveredSkillInspect{
                clickRect,
                m_pGameData->characterInspectTable().getSkill(skillName),
                skillName};
        }

        if (leftMouseJustReleased() && hitTest(clickRect))
        {
            endNameEditing(true);
            playUiClickSound(SoundId::SelectingNewCharacter);
            tryToggleOptionalSkill(skillName);
        }
    }

    if (pEntry != nullptr)
    {
        const CharacterDollTypeEntry *pDollType =
            m_pGameData != nullptr ? m_pGameData->characterDollTable().getDollType(pEntry->dollTypeId) : nullptr;
        const MenuScreenBase::Rect dollAnchorRect =
            resolveRect("CharacterCreationPreviewAnchor", 451.0f, 80.0f, 0.0f, 0.0f);
        const float dollAnchorX = dollAnchorRect.x;
        const float dollAnchorY = dollAnchorRect.y;
        const std::string compositeKey =
            std::to_string(pEntry->id) + ":"
            + std::to_string(pEntry->dollTypeId) + ":"
            + pEntry->backgroundAsset + ":"
            + pEntry->bodyAsset + ":"
            + pEntry->leftHandOpenAsset + ":"
            + pEntry->rightHandOpenAsset;

        if (m_creationPreviewDollCacheKey != compositeKey)
        {
            m_creationPreviewDollPixels = buildCreationPreviewDollPixels(*pEntry, pDollType);
            m_creationPreviewDollCacheKey = compositeKey;
        }

        if (m_creationPreviewDollPixels.has_value())
        {
            drawPixelsBgra(
                "new_game_creation_doll:" + compositeKey,
                m_creationPreviewDollPixels->physicalWidth,
                m_creationPreviewDollPixels->physicalHeight,
                m_creationPreviewDollPixels->pixels,
                {
                    std::round(dollAnchorX),
                    std::round(dollAnchorY),
                    std::round(static_cast<float>(m_creationPreviewDollPixels->logicalWidth) * scale),
                    std::round(static_cast<float>(m_creationPreviewDollPixels->logicalHeight) * scale)
                });
        }
    }

    if (hoveredSkillInspect.has_value()
        && hoveredSkillInspect->pEntry != nullptr
        && !hoveredSkillInspect->pEntry->description.empty())
    {
        renderSkillInspectPopup(
            *hoveredSkillInspect->pEntry,
            hoveredSkillInspect->skillName,
            hoveredSkillInspect->rect,
            inspectCharacter,
            scale);
    }

    if (hoveredStatInspect.has_value()
        && hoveredStatInspect->second != nullptr
        && !hoveredStatInspect->second->description.empty())
    {
        renderStatInspectPopup(*hoveredStatInspect->second, hoveredStatInspect->first, scale);
    }

    if (hoveredClassInspect.has_value()
        && hoveredClassInspect->second != nullptr
        && !hoveredClassInspect->second->description.empty())
    {
        renderClassInspectPopup(*hoveredClassInspect->second, hoveredClassInspect->first, scale);
    }

    if (!m_debugGodLichRoster)
    {
        const MenuScreenBase::Rect addCharacterRect =
            resolveRect("CharacterCreationAddCharacterButton", 51.0f, 437.0f, 19.0f, 34.0f);
        const MenuScreenBase::Rect removeCharacterRect =
            resolveRect("CharacterCreationRemoveCharacterButton", 72.0f, 437.0f, 19.0f, 34.0f);
        bool addCharacterClicked = false;
        bool removeCharacterClicked = false;

        if (m_partySize < 5)
        {
            const ButtonState addCharacterState = drawButton(
                resolveButtonVisuals("CharacterCreationAddCharacterButton", {"slcharaddu", "slcharaddu", "slcharaddd"}),
                addCharacterRect);
            addCharacterClicked = addCharacterState.clicked;
        }

        if (m_partySize > 1)
        {
            const ButtonState removeCharacterState = drawButton(
                resolveButtonVisuals("CharacterCreationRemoveCharacterButton", {"slcharremu", "slcharremu", "slcharremd"}),
                removeCharacterRect);
            removeCharacterClicked = removeCharacterState.clicked;
        }

        if (addCharacterClicked)
        {
            playUiClickSound(SoundId::ClickIn);
            addPartySlot();
        }
        else if (removeCharacterClicked)
        {
            playUiClickSound(SoundId::ClickIn);
            removePartySlot();
        }

        for (size_t slotIndex = 0; slotIndex < PartySlotButtonLayoutIds.size() && slotIndex < m_partySize; ++slotIndex)
        {
            const float fallbackX = 98.0f + static_cast<float>(slotIndex) * 40.0f;
            const MenuScreenBase::Rect slotRect =
                resolveRect(PartySlotButtonLayoutIds[slotIndex], fallbackX, 439.0f, 32.0f, 32.0f);
            const std::string slotNumber = std::to_string(slotIndex + 1);
            const bool selected = slotIndex == m_activePartySlot;
            const ButtonVisualSet slotVisuals = selected
                ? ButtonVisualSet{"slchar" + slotNumber + "d", "slchar" + slotNumber + "d", "slchar" + slotNumber + "u"}
                : ButtonVisualSet{"slchar" + slotNumber + "u", "slchar" + slotNumber + "u", "slchar" + slotNumber + "d"};
            const ButtonState slotState = drawButton(
                slotVisuals,
                slotRect);

            if (slotState.clicked)
            {
                playUiClickSound(SoundId::SelectingNewCharacter);
                switchActivePartySlot(slotIndex);
            }
        }
    }

    const MenuScreenBase::Rect clearButtonRect =
        resolveRect("CharacterCreationClearButton", 462.0f, 442.0f, 83.0f, 30.0f);
    const MenuScreenBase::Rect cancelButtonRect =
        resolveRect("CharacterCreationCancelButton", 525.0f, 442.0f, 83.0f, 30.0f);
    const MenuScreenBase::Rect okButtonRect =
        resolveRect("CharacterCreationOkButton", 582.0f, 442.0f, 83.0f, 30.0f);
    const ButtonState clearState = drawButton(
        resolveButtonVisuals("CharacterCreationClearButton", {"c_clr_up", "c_clr_ht", "c_clr_dn"}),
        clearButtonRect);
    const ButtonState cancelState = drawButton(
        resolveButtonVisuals("CharacterCreationCancelButton", {"c_cncl_up", "c_cncl_ht", "c_cncl_dn"}),
        cancelButtonRect);
    const ButtonState okState = drawButton(
        resolveButtonVisuals("CharacterCreationOkButton", {"c_ok_up", "c_ok_ht", "c_ok_dn"}),
        okButtonRect);

    if (clearState.clicked)
    {
        playUiClickSound(SoundId::ClickIn);
        resetCurrentState(false);
    }
    else if (cancelState.clicked)
    {
        playUiClickSound(SoundId::ClickIn);
        cancelCreation();
        return;
    }
    else if (okState.clicked)
    {
        playUiClickSound(SoundId::ClickIn);
        confirmCreation();

        if (m_creationCompletionErrorSeconds <= 0.0f)
        {
            return;
        }
    }

    if (returnPressed)
    {
        if (m_state.nameEditing)
        {
            endNameEditing(true);
        }
        else
        {
            confirmCreation();

            if (m_creationCompletionErrorSeconds <= 0.0f)
            {
                return;
            }
        }
    }

    if (!m_state.statusMessage.empty())
    {
        const MenuScreenBase::Rect statusMessageRect =
            resolveRect("CharacterCreationStatusMessage", 210.0f, 446.0f, 0.0f, 0.0f);
        drawText(fontName, m_state.statusMessage, statusMessageRect.x, statusMessageRect.y, RedColor, scale);
    }

    renderCreationCompletionErrorMessageBox(rootRect, scale);
}
}
