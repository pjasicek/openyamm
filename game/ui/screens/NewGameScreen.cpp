#include "game/ui/screens/NewGameScreen.h"

#include "game/audio/GameAudioSystem.h"
#include "game/audio/SoundIds.h"
#include "game/gameplay/GameMechanics.h"
#include "game/party/SkillData.h"
#include "game/party/SpeechIds.h"

#include <algorithm>
#include <array>
#include <cctype>
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
using CreationRace = NewGameScreen::CreationRace;
using CreationCandidate = NewGameScreen::CreationCandidate;

constexpr float RootWidth = 640.0f;
constexpr float RootHeight = 480.0f;
constexpr const char *CharacterCreationLayoutPath = "Data/ui/gameplay/character_creation.yml";
constexpr uint32_t DefaultCreationCharacterDataId = 1;
constexpr uint32_t CharacterCreationVoicePreviewSpeakerKey = 0x43525650u;
constexpr int StartingBonusPool = 15;
constexpr int NeutralBaseStatValue = 11;
constexpr int MinimumStatOffset = 2;
constexpr int MaximumStatValue = 25;
constexpr int BoostedMaximumStatValue = 34;
constexpr float InspectPopupWidth = 425.0f;
constexpr float InspectPopupGap = 12.0f;
constexpr size_t MaximumOptionalSkillSelections = 2;
constexpr size_t MaximumNameLength = 15;
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

constexpr std::array<CreationCandidate, 26> CreationCandidates = {{
    {1, "Gareth", "Knight", CreationRace::Human, true, {18, 9, 9, 15, 15, 15, 11}, {{"Bow", "RepairItem"}}},
    {2, "Kiir", "Knight", CreationRace::Human},
    {3, "Gareth", "Knight", CreationRace::Human},
    {4, "Rhea", "Knight", CreationRace::Human},
    {5, "Cedric", "Cleric", CreationRace::Human},
    {6, "Elena", "Cleric", CreationRace::Human},
    {7, "Tomas", "Cleric", CreationRace::Human},
    {8, "Miriam", "Cleric", CreationRace::Human},
    {9, "Morcar", "Necromancer", CreationRace::Human},
    {10, "Selene", "Necromancer", CreationRace::Human},
    {11, "Darian", "Necromancer", CreationRace::Human},
    {12, "Nyra", "Necromancer", CreationRace::Human},
    {13, "Valen", "Vampire", CreationRace::Vampire},
    {14, "Serisa", "Vampire", CreationRace::Vampire},
    {15, "Lucan", "Vampire", CreationRace::Vampire},
    {16, "Mirelle", "Vampire", CreationRace::Vampire},
    {17, "Soryn", "DarkElf", CreationRace::DarkElf},
    {18, "Faelyr", "DarkElf", CreationRace::DarkElf},
    {19, "Vaelis", "DarkElf", CreationRace::DarkElf},
    {20, "Nym", "DarkElf", CreationRace::DarkElf},
    {21, "Arius", "Minotaur", CreationRace::Minotaur},
    {22, "Karn", "Minotaur", CreationRace::Minotaur},
    {23, "Overdune", "Troll", CreationRace::Troll},
    {24, "Brakka", "Troll", CreationRace::Troll},
    {25, "Aleton", "Dragon", CreationRace::Dragon},
    {26, "Beren", "Dragon", CreationRace::Dragon},
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

std::string creationRaceName(CreationRace race)
{
    switch (race)
    {
        case CreationRace::Vampire:
            return "Vampire";

        case CreationRace::DarkElf:
            return "DarkElf";

        case CreationRace::Minotaur:
            return "Minotaur";

        case CreationRace::Troll:
            return "Troll";

        case CreationRace::Dragon:
            return "Dragon";

        case CreationRace::Human:
        default:
            return "Human";
    }
}

RaceStatRule raceRuleForBaseStat(int baseStatValue)
{
    if (baseStatValue > NeutralBaseStatValue)
    {
        return {2, 1};
    }

    if (baseStatValue < NeutralBaseStatValue)
    {
        return {1, 2};
    }

    return {1, 1};
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
    return rule.baseStep > 1 ? BoostedMaximumStatValue : MaximumStatValue;
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

    if (pClassSkillTable->getClassCap(character.className, skillName) >= mastery)
    {
        return 0;
    }

    if (pClassSkillTable->getHighestPromotionCap(character.className, skillName) >= mastery)
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
    ContinueAction continueAction,
    BackAction backAction)
    : MenuScreenBase(assetFileSystem)
    , m_pGameAudioSystem(pGameAudioSystem)
    , m_pGameData(&gameData)
    , m_continueAction(std::move(continueAction))
    , m_backAction(std::move(backAction))
{
}

AppMode NewGameScreen::mode() const
{
    return AppMode::NewGame;
}

void NewGameScreen::onEnter()
{
    ensureLayoutLoaded();

    size_t defaultCandidateIndex = 0;

    for (size_t index = 0; index < CreationCandidates.size(); ++index)
    {
        if (CreationCandidates[index].characterDataId == DefaultCreationCharacterDataId)
        {
            defaultCandidateIndex = index;
            break;
        }
    }

    resetStateForCandidate(defaultCandidateIndex);
}

void NewGameScreen::onExit()
{
    endNameEditing(true);
}

void NewGameScreen::handleSdlEvent(const SDL_Event &event)
{
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
            if (m_state.nameEditing && !m_state.nameEditBuffer.empty())
            {
                m_state.nameEditBuffer.pop_back();
            }
            break;

        default:
            break;
    }
}

const CreationCandidate &NewGameScreen::selectedCandidate() const
{
    return CreationCandidates[m_state.selectedCandidateIndex];
}

std::array<int, static_cast<size_t>(StatId::Count)> NewGameScreen::statsForRace(CreationRace race) const
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

    const RaceStartingStatsTable::Entry *pEntry =
        m_pGameData->raceStartingStatsTable().get(creationRaceName(race));
    return pEntry != nullptr ? pEntry->stats : defaultStats;
}

const CharacterDollEntry *NewGameScreen::selectedCharacterEntry() const
{
    return m_pGameData != nullptr
        ? m_pGameData->characterDollTable().getCharacter(selectedCandidate().characterDataId)
        : nullptr;
}

void NewGameScreen::resetStateForCandidate(size_t candidateIndex)
{
    m_state = {};
    m_state.selectedCandidateIndex = std::min(candidateIndex, CreationCandidates.size() - 1);
    resetCurrentState(true);
}

void NewGameScreen::resetCurrentState(bool applyCandidateDefaults)
{
    const CreationCandidate &candidate = selectedCandidate();
    const std::array<int, static_cast<size_t>(StatId::Count)> baseStats = statsForRace(candidate.race);
    m_state.baseStats = baseStats;
    m_state.currentStats = baseStats;
    m_state.name = candidate.pDefaultName;
    m_state.nameEditBuffer = m_state.name;
    m_state.defaultSkills.clear();
    m_state.optionalSkills.clear();
    m_state.selectedOptionalSkills.clear();
    m_state.statusMessage.clear();

    if (m_pGameData != nullptr)
    {
        for (const char *pSkillName : OrderedSkillNames)
        {
            const StartingSkillAvailability availability =
                m_pGameData->classSkillTable().getStartingSkillAvailability(candidate.pClassName, pSkillName);

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

    const CharacterDollEntry *pEntry = selectedCharacterEntry();
    m_state.selectedVoiceId = pEntry != nullptr ? static_cast<int>(pEntry->defaultVoiceId) : 0;

    if (applyCandidateDefaults && candidate.hasCustomDefaultStats)
    {
        m_state.currentStats = candidate.defaultStats;

        for (const char *pSkillName : candidate.defaultOptionalSkills)
        {
            if (pSkillName == nullptr || *pSkillName == '\0')
            {
                continue;
            }

            const std::string skillName = pSkillName;
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

    endNameEditing(false);
}

void NewGameScreen::beginNameEditing()
{
    if (m_state.nameEditing)
    {
        return;
    }

    m_state.nameEditing = true;
    m_state.nameEditBuffer = m_state.name;
    SDL_Window *pWindow = SDL_GetKeyboardFocus();

    if (pWindow != nullptr)
    {
        SDL_StartTextInput(pWindow);
    }
}

void NewGameScreen::endNameEditing(bool commitEdit)
{
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
    SDL_Window *pWindow = SDL_GetKeyboardFocus();

    if (pWindow != nullptr)
    {
        SDL_StopTextInput(pWindow);
    }
}

int NewGameScreen::currentBonusPool() const
{
    int remainingPoints = StartingBonusPool;
    const std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> rules = raceRulesForStats(m_state.baseStats);

    for (size_t statIndex = 0; statIndex < static_cast<size_t>(StatId::Count); ++statIndex)
    {
        const int currentValue = m_state.currentStats[statIndex];
        const int baseValue = m_state.baseStats[statIndex];
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
    const std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> rules = raceRulesForStats(m_state.baseStats);
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
    const std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> rules = raceRulesForStats(m_state.baseStats);
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

    for (const CreationCandidate &candidate : CreationCandidates)
    {
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
    const int count = static_cast<int>(CreationCandidates.size());
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

    character.name = candidate.pDefaultName;
    character.className = candidate.pClassName;
    character.role = displayClassName(candidate.pClassName);
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

Character NewGameScreen::buildCharacter() const
{
    Character character = {};
    const CreationCandidate &candidate = selectedCandidate();
    const CharacterDollEntry *pEntry = selectedCharacterEntry();

    character.name = trimCopy(m_state.name);
    character.className = candidate.pClassName;
    character.role = displayClassName(candidate.pClassName);
    character.characterDataId = candidate.characterDataId;
    character.voiceId = m_state.selectedVoiceId;
    character.birthYear = 1150;
    character.level = 1;
    character.skillPoints = 0;
    character.might = static_cast<uint32_t>(m_state.currentStats[static_cast<size_t>(StatId::Might)]);
    character.intellect = static_cast<uint32_t>(m_state.currentStats[static_cast<size_t>(StatId::Intellect)]);
    character.personality = static_cast<uint32_t>(m_state.currentStats[static_cast<size_t>(StatId::Personality)]);
    character.endurance = static_cast<uint32_t>(m_state.currentStats[static_cast<size_t>(StatId::Endurance)]);
    character.accuracy = static_cast<uint32_t>(m_state.currentStats[static_cast<size_t>(StatId::Accuracy)]);
    character.speed = static_cast<uint32_t>(m_state.currentStats[static_cast<size_t>(StatId::Speed)]);
    character.luck = static_cast<uint32_t>(m_state.currentStats[static_cast<size_t>(StatId::Luck)]);

    if (pEntry != nullptr)
    {
        character.portraitTextureName = portraitTextureNameForEntry(*pEntry);
        character.portraitPictureId = pEntry->id > 0 ? (pEntry->id - 1) : 0;
        character.sexId = pEntry->defaultSex;
        character.raceId = pEntry->raceId >= 0 ? static_cast<uint32_t>(pEntry->raceId) : 0;
    }

    for (const std::string &skillName : m_state.defaultSkills)
    {
        character.skills[skillName] = {skillName, 1, SkillMastery::Normal};
    }

    for (const std::string &skillName : m_state.selectedOptionalSkills)
    {
        character.skills[skillName] = {skillName, 1, SkillMastery::Normal};
    }

    character.maxHealth = GameMechanics::calculateBaseCharacterMaxHealth(character);
    character.health = character.maxHealth;
    character.maxSpellPoints = GameMechanics::calculateBaseCharacterMaxSpellPoints(character);
    character.spellPoints = character.maxSpellPoints;

    return character;
}

void NewGameScreen::confirmCreation()
{
    endNameEditing(true);

    if (currentBonusPool() != 0)
    {
        m_state.statusMessage = "All bonus points must be assigned.";
        return;
    }

    if (trimCopy(m_state.name).empty())
    {
        m_state.statusMessage = "Character name cannot be empty.";
        return;
    }

    if (m_continueAction)
    {
        m_continueAction(buildCharacter());
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

void NewGameScreen::drawScreen(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);

    ensureLayoutLoaded();

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

    drawText(
        fontName,
        displayClassName(selectedCandidate().pClassName),
        classValueRect.x,
        classValueRect.y,
        WhiteColor,
        scale);

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
        const auto drawDollLayerAtNativeSize =
            [this, scale](const std::string &assetName, float layerX, float layerY)
            {
                if (assetName.empty() || assetName == "none" || assetName == "null")
                {
                    return;
                }

                const std::optional<MenuScreenBase::TextureSize> size = textureSize(assetName);

                if (!size.has_value())
                {
                    return;
                }

                drawTexture(
                    assetName,
                    {
                        std::round(layerX),
                        std::round(layerY),
                        std::round(size->width * scale),
                        std::round(size->height * scale)
                    });
            };

        if (!pEntry->backgroundAsset.empty() && pEntry->backgroundAsset != "none")
        {
            drawDollLayerAtNativeSize(pEntry->backgroundAsset, dollAnchorX, dollAnchorY);
        }

        const float bodyBaseX = dollAnchorX + static_cast<float>(pEntry->bodyOffsetX) * scale;
        const float bodyBaseY = dollAnchorY + static_cast<float>(pEntry->bodyOffsetY) * scale;

        if (!pEntry->bodyAsset.empty() && pEntry->bodyAsset != "none")
        {
            drawDollLayerAtNativeSize(pEntry->bodyAsset, bodyBaseX, bodyBaseY);
        }

        if (pDollType != nullptr && !pEntry->leftHandOpenAsset.empty() && pEntry->leftHandOpenAsset != "none")
        {
            drawDollLayerAtNativeSize(
                pEntry->leftHandOpenAsset,
                dollAnchorX + static_cast<float>(pDollType->leftHandFingersX) * scale,
                dollAnchorY + static_cast<float>(pDollType->leftHandFingersY) * scale);
        }

        if (pDollType != nullptr && !pEntry->rightHandOpenAsset.empty() && pEntry->rightHandOpenAsset != "none")
        {
            drawDollLayerAtNativeSize(
                pEntry->rightHandOpenAsset,
                dollAnchorX + static_cast<float>(pDollType->rightHandOpenX) * scale,
                dollAnchorY + static_cast<float>(pDollType->rightHandOpenY) * scale);
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
        return;
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
            return;
        }
    }

    if (!m_state.statusMessage.empty())
    {
        const MenuScreenBase::Rect statusMessageRect =
            resolveRect("CharacterCreationStatusMessage", 210.0f, 446.0f, 0.0f, 0.0f);
        drawText(fontName, m_state.statusMessage, statusMessageRect.x, statusMessageRect.y, RedColor, scale);
    }
}
}
