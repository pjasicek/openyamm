#include "game/ui/screens/NewGameScreen.h"

#include "game/audio/GameAudioSystem.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameMechanics.h"
#include "game/party/SkillData.h"
#include "game/party/SpeechIds.h"
#include "game/ui/GameplayUiSkin.h"

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

constexpr const char *PcNamesTablePath = "engine/data_tables/english/pc_names.txt";
constexpr uint32_t DefaultCreationCharacterDataId = 1;
constexpr const char *DefaultCreationClassName = "Knight";
constexpr uint32_t DebugGodLichCharacterDataId = 27;
constexpr int DebugGodLichStatValue = 100;
constexpr uint32_t CharacterCreationVoicePreviewSpeakerKey = 0x43525650u;
constexpr int StartingBonusPool = 15;
constexpr int NeutralBaseStatValue = 11;
constexpr int MinimumStatOffset = 2;
constexpr int MaximumStatValue = 25;
constexpr int BoostedMaximumStatValue = 34;
constexpr float NameBackspaceInitialRepeatDelaySeconds = 0.35f;
constexpr float NameBackspaceRepeatIntervalSeconds = 0.065f;
constexpr size_t MaximumOptionalSkillSelections = 2;
constexpr size_t MaximumNameLength = 15;
constexpr const char *CreationCompletionErrorText =
    "Create Party cannot be completed unless you have assigned all characters 2 extra skills and have spent all of "
    "your bonus points.";

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
    {&CharacterEquipment::mainHand, &CharacterEquipmentRuntimeState::mainHand, 1667},  // MM6 Blaster Rifle
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

constexpr std::array<const char *, 5> PartySlotButtonLayoutIds = {{
    "CharacterCreationPartySlot1Button",
    "CharacterCreationPartySlot2Button",
    "CharacterCreationPartySlot3Button",
    "CharacterCreationPartySlot4Button",
    "CharacterCreationPartySlot5Button",
}};

constexpr std::array<const char *, 40> OrderedSkillNames = {{
    "Staff",
    "Sword",
    "Dagger",
    "Axe",
    "Spear",
    "Bow",
    "Throwing",
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

std::string classIconTextureName(const std::string &className)
{
    const std::string token = canonicalNameToken(className);
    return "hud_x2/menus/classes/" + (token == "lich" ? "necromancer" : token) + ".png";
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

uint32_t startingCasterClassId(uint32_t classId, const MergedCharacterSelectionContinent &continent)
{
    // Only these two caster families vary by starting continent; other choices remain unrestricted.
    const auto offers = [&continent](uint32_t id)
    {
        return std::find(continent.availableClassIds.begin(), continent.availableClassIds.end(), id)
            != continent.availableClassIds.end();
    };
    if (classId == 4 || classId == 5) // Cleric / Priest
    {
        return offers(5) ? 5 : 4;
    }
    if (classId == 42 || classId == 44) // Sorcerer / Necromancer
    {
        return offers(44) ? 44 : 42;
    }
    return classId;
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
    character.might = DebugGodLichStatValue;
    character.intellect = DebugGodLichStatValue;
    character.personality = DebugGodLichStatValue;
    character.endurance = DebugGodLichStatValue;
    character.accuracy = DebugGodLichStatValue;
    character.speed = DebugGodLichStatValue;
    character.luck = DebugGodLichStatValue;
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

NewGameScreen::NewGameScreen(const Engine::AssetFileSystem &assetFileSystem, GameAudioSystem *pGameAudioSystem,
                             const GameDataRepository &gameData, bool debugGodLichRoster, bool includeGodLichCandidate,
                             bool allowIncompleteCharacterCreation, ContinueAction continueAction,
                             BackAction backAction)
    : MenuDesignScreen(assetFileSystem, false, pGameAudioSystem), m_pGameAudioSystem(pGameAudioSystem),
      m_pGameData(&gameData), m_debugGodLichRoster(debugGodLichRoster),
      m_includeGodLichCandidate(includeGodLichCandidate),
      m_allowIncompleteCharacterCreation(allowIncompleteCharacterCreation), m_continueAction(std::move(continueAction)),
      m_backAction(std::move(backAction)), m_nameRng(std::random_device{}())
{
}

AppMode NewGameScreen::mode() const
{
    return AppMode::NewGame;
}

void NewGameScreen::prepareForFirstFrame()
{
    loadDesign("gameplay/continent_selection");
    loadDesign("gameplay/character_creation");
    preloadLayoutAssets(m_designLayouts);
}

void NewGameScreen::onEnter()
{
    loadDesign("gameplay/continent_selection");
    loadDesign("gameplay/character_creation");
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
    if (modalOpen())
    {
        return;
    }
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
        if (event.key.key == SDLK_ESCAPE)
        {
            m_escapePressed = true;
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
            if (!m_state.nameEditing && !isGodLichSelected())
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

bool NewGameScreen::isGodLichState(const CreationState &state) const
{
    return m_debugGodLichRoster
        || (m_includeGodLichCandidate && state.selectedCandidateIndex >= m_candidates.size());
}

bool NewGameScreen::isGodLichSelected() const
{
    return isGodLichState(m_state);
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

    const MergedCharacterSelectionContinent *pContinent = findNewGameContinent(selectionTable, m_selectedContinent.key);
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

        const std::vector<std::string> *pAllowedClasses = selectionTable.allowedClassesForRaceId(raceId);
        const std::optional<std::string> raceName = selectionTable.raceNameForId(raceId);

        if (pAllowedClasses == nullptr || !raceName.has_value())
        {
            continue;
        }

        std::vector<uint32_t> availableClassIds;

        for (const std::string &className : *pAllowedClasses)
        {
            const std::optional<uint32_t> classId = m_pGameData->classSkillTable().classIdForName(className);

            if (!classId.has_value())
            {
                continue;
            }

            availableClassIds.push_back(startingCasterClassId(*classId, *pContinent));
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
        candidate.classId = classIdNear(startingCasterClassId(pEntry->defaultClassId, *pContinent),
                                       candidate.availableClassIds, 1);

        if (const std::optional<std::string> className = m_pGameData->classSkillTable().classNameForId(candidate.classId))
        {
            candidate.className = *className;
            m_candidates.push_back(std::move(candidate));
        }
    }

    const auto isDragon = [](const CreationCandidate &candidate)
    {
        return candidate.raceName == "Dragon";
    };
    std::stable_partition(std::find_if(m_candidates.begin(), m_candidates.end(), isDragon), m_candidates.end(), isDragon);
}

size_t NewGameScreen::candidateCount() const
{
    if (m_debugGodLichRoster)
    {
        return 1;
    }

    return m_candidates.size() + (m_includeGodLichCandidate ? 1 : 0);
}

const CreationCandidate &NewGameScreen::candidateAt(size_t candidateIndex) const
{
    if (m_debugGodLichRoster
        || (m_includeGodLichCandidate && candidateIndex >= m_candidates.size()))
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

    if (isGodLichState(state))
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

    if (!isGodLichSelected())
    {
        m_state.selectedClassId = classIdNear(previousClassId, selectedCandidate().availableClassIds, 1);
    }

    refreshSkillChoices(false);
}

void NewGameScreen::cycleClass(int direction)
{
    endNameEditing(true);

    if (isGodLichSelected() || m_candidates.empty() || m_pGameData == nullptr)
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

void NewGameScreen::showCreationCompletionError()
{
    m_state.statusMessage = CreationCompletionErrorText;
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

    if (isGodLichState(state))
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
    if (isGodLichSelected())
    {
        return {buildCharacterFromState(m_state)};
    }

    std::vector<Character> characters;
    const size_t count = std::min<size_t>(m_partySize, m_partyStates.size());
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
    const bool godLichParty = isGodLichSelected();

    for (size_t slotIndex = 0; !godLichParty && slotIndex < m_partySize; ++slotIndex)
    {
        if (trimCopy(m_partyStates[slotIndex].name).empty())
        {
            switchActivePartySlot(slotIndex);
            m_state.statusMessage = "Character name cannot be empty.";
            return;
        }
    }

    if (!godLichParty && !m_allowIncompleteCharacterCreation)
    {
        for (size_t slotIndex = 0; slotIndex < m_partySize; ++slotIndex)
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

        m_continueAction(characters, m_selectedContinent.id, godLichParty);
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

void NewGameScreen::drawContinentSelection(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);
    loadDesign("gameplay/continent_selection");
    beginDesign("ContinentSelection");
    drawDesign();
    std::string chosenContinent;
    for (const std::string key : {"enroth", "antagarich", "jadame"})
    {
        std::string name = key;
        name[0] = char(std::toupper(name[0]));
        const std::string prefix = "ContinentSelection" + name;
        const bool available = findNewGameContinent(m_pGameData->mergedCharacterSelectionTable(), key) != nullptr;
        const Rect rect = designRect(prefix + "Button");
        if (button(prefix, rect, "", "world_card", available, available && pointerInside(rect)))
        {
            chosenContinent = key;
        }
        // Cards draw their pictures and lettering above their blank selectable skin.
        const UiLayoutManager::LayoutElement *pImage = m_designLayouts.findElement(prefix + "Illustration");
        drawTexture(pImage->primaryAsset, designRect(prefix + "Illustration"));
        label(prefix + "Name", name);
        label(prefix + "Game", m_designLayouts.findElement(prefix + "Game")->labelText);
        label(prefix + "Start", m_designLayouts.findElement(prefix + "Start")->labelText);
    }
    if (action("ContinentSelectionCancelButton") || m_escapePressed)
    {
        m_escapePressed = false;
        cancelCreation();
        return;
    }
    if (!chosenContinent.empty())
    {
        selectContinent(chosenContinent);
    }
}

void NewGameScreen::drawScreen(float deltaSeconds)
{
    if (m_stage == FlowStage::ContinentSelection)
    {
        drawContinentSelection(deltaSeconds);
        return;
    }
    initializeCharacterCreationForSelectedContinent();
    loadDesign("gameplay/character_creation");
    beginDesign("CharacterCreation");
    drawDesign();
    updateNameBackspaceRepeat(deltaSeconds);
    const bool wasEditing = m_state.nameEditing;
    if (m_escapePressed && !modalOpen())
    {
        m_escapePressed = false;
        if (wasEditing)
        {
            endNameEditing(true);
        }
        else
        {
            cancelCreation();
            return;
        }
    }
    if (m_returnPressed && wasEditing)
    {
        endNameEditing(true);
    }
    m_returnPressed = false;
    m_escapePressed = false;
    std::string continentKey = m_selectedContinent.key;
    continentKey[0] = char(std::toupper(continentKey[0]));
    const UiLayoutManager::LayoutElement *pStart =
        m_designLayouts.findElement("ContinentSelection" + continentKey + "Start");
    label("CharacterCreationContinent", m_selectedContinent.name + " - " + pStart->labelText);
    const Rect nameRect = designRect("CharacterCreationNameField");
    if (m_state.nameEditing && (keyPressed(SDL_SCANCODE_TAB) || (leftMouseJustPressed() && !pointerInside(nameRect))))
    {
        endNameEditing(true);
    }
    if (button("name", nameRect, "", "text_field"))
    {
        beginNameEditing();
    }
    label("CharacterCreationNameField", (m_state.nameEditing ? m_state.nameEditBuffer + "_" : m_state.name));
    setTextEditing(m_state.nameEditing);
    std::string helpTitle, helpBody;
    std::vector<std::pair<std::string, uint32_t>> helpMasteries;
    Rect helpAnchor;
    const auto inspectSkill = [this, &helpTitle, &helpBody, &helpMasteries, &helpAnchor](
                                  const std::string &skill, const Rect &rect)
    {
        if (!rightMouseDown() || modalOpen() || !pointerInside(rect))
        {
            return;
        }
        const SkillInspectEntry *pHelp = m_pGameData->characterInspectTable().getSkill(skill);
        if (pHelp == nullptr)
        {
            return;
        }
        helpTitle = pHelp->name;
        helpBody = pHelp->description;
        helpAnchor = rect;
        const Character character = buildCharacter();
        const auto mastery = [this, &helpMasteries, &character, &skill](
                                 SkillMastery level, const std::string &name, const std::string &description)
        {
            if (description.empty())
            {
                return;
            }
            const int availability =
                skillMasteryAvailabilityForCreation(&m_pGameData->classSkillTable(), character, skill, level);
            const uint32_t color = availability == 1   ? GameplayUiSkin::Low
                                   : availability == 2 ? GameplayUiSkin::Penalty
                                                       : 0xffffffffu;
            helpMasteries.emplace_back(name + ": " + description, color);
        };
        mastery(SkillMastery::Expert, "Expert", pHelp->expertDescription);
        mastery(SkillMastery::Master, "Master", pHelp->masterDescription);
        mastery(SkillMastery::Grandmaster, "Grandmaster", pHelp->grandmasterDescription);
    };
    if (action("CharacterCreationPortraitLeftButton"))
    {
        cycleCandidate(-1);
        playVoicePreview();
    }
    if (action("CharacterCreationPortraitRightButton"))
    {
        cycleCandidate(1);
        playVoicePreview();
    }
    if (action("CharacterCreationVoiceLeftButton"))
    {
        cycleVoice(-1);
        playVoicePreview();
    }
    if (action("CharacterCreationVoiceRightButton"))
    {
        cycleVoice(1);
        playVoicePreview();
    }
    if (action("CharacterCreationResetCharacterButton"))
    {
        resetCurrentState(true);
    }
    if (action("CharacterCreationRemoveCharacterButton", m_partySize > 1 && !isGodLichSelected()))
    {
        removePartySlot();
    }
    if (selectBox("class", designRect("CharacterCreationClassValue"), displayClassName(selectedClassName()),
                  !isGodLichSelected() && !selectedCandidate().availableClassIds.empty(), 12.16f))
    {
        endNameEditing(true);
        const std::vector<uint32_t> choices = selectedCandidate().availableClassIds;
        std::vector<std::string> names;
        std::vector<std::string> icons;
        for (const uint32_t id : choices)
        {
            CreationState state = m_state;
            state.selectedClassId = id;
            const std::string className = classNameForState(state);
            names.push_back(displayClassName(className));
            icons.push_back(classIconTextureName(className));
        }
        confirm("Choose Class", selectedCandidate().raceName, names,
                [this, choices](int index)
                {
                    if (index >= 0)
                    {
                        m_state.selectedClassId = choices[size_t(index)];
                        refreshSkillChoices(true);
                    }
                }, true, true, std::move(icons));
    }
    if (rightMouseDown() && !modalOpen() && pointerInside(designRect("CharacterCreationClassValue")))
    {
        if (const ClassInspectEntry *pHelp = m_pGameData->characterInspectTable().getClass(selectedClassName()))
        {
            helpTitle = pHelp->name;
            helpBody = pHelp->description;
            helpAnchor = designRect("CharacterCreationClassValue");
        }
    }
    label("CharacterCreationVoiceValue",
          "Voice " + std::to_string(m_state.selectedVoiceId) + " - " + selectedCandidate().raceName);
    const CharacterDollEntry *pEntry = selectedCharacterEntry();
    if (pEntry != nullptr)
    {
        drawTexture(portraitTextureNameForEntry(*pEntry), designRect("CharacterCreationPortraitImage"));
        const Rect portrait = designRect("CharacterCreationPortraitImage");
        drawEllipseOutline({portrait.x - 3 * designScale(), portrait.y - 3 * designScale(),
                            portrait.width + 6 * designScale(), portrait.height + 6 * designScale()},
                           designScale(), 0xff61888eu);
        drawEllipseOutline(portrait, 1.1f * designScale(), 0xff85bbd8u);
        drawTexture(classIconTextureName(selectedClassName()), designRect("CharacterCreationClassEmblem"));
        const std::string compositeKey = std::to_string(pEntry->id) + ":" + pEntry->bodyAsset;
        if (compositeKey != m_creationPreviewDollCacheKey)
        {
            m_creationPreviewDollPixels = buildCreationPreviewDollPixels(
                *pEntry, m_pGameData->characterDollTable().getDollType(pEntry->dollTypeId));
            m_creationPreviewDollCacheKey = compositeKey;
        }
        if (m_creationPreviewDollPixels)
        {
            const TexturePixelsBgra &pixels = *m_creationPreviewDollPixels;
            Rect rect = designRect("CharacterCreationDoll");
            const float fit = std::min(rect.width / pixels.logicalWidth, rect.height / pixels.logicalHeight);
            rect.x += (rect.width - pixels.logicalWidth * fit) / 2;
            rect.width = pixels.logicalWidth * fit;
            rect.height = pixels.logicalHeight * fit;
            drawPixelsBgra("new_game_creation_doll:" + compositeKey, pixels.physicalWidth, pixels.physicalHeight,
                           pixels.pixels, rect);
        }
    }
    const bool grantedSkills = isGodLichSelected();
    label("CharacterCreationBonusPoolValue",
          grantedSkills ? "Preset" : std::to_string(currentBonusPool()) + " points left");
    label("CharacterCreationAttributeHelp",
          grantedSkills ? "Attributes are fixed for this preset." : "Spend all bonus points before beginning.");
    for (size_t index = 0; index < size_t(StatId::Count); ++index)
    {
        label(StatValueLayoutIds[index],
              std::to_string(grantedSkills ? DebugGodLichStatValue : m_state.currentStats[index]),
              m_state.currentStats[index] > m_state.baseStats[index]   ? 0xffa4d7b0u
              : m_state.currentStats[index] < m_state.baseStats[index] ? 0xff8c91dcu
                                                                       : 0);
        if (action(StatMinusButtonLayoutIds[index], !grantedSkills))
        {
            tryDecreaseStat(StatId(index));
        }
        if (action(StatPlusButtonLayoutIds[index], !grantedSkills && currentBonusPool() > 0))
        {
            tryIncreaseStat(StatId(index));
        }
        if (rightMouseDown() && !modalOpen() && pointerInside(designRect(StatLabelLayoutIds[index])))
        {
            if (const StatInspectEntry *pHelp = m_pGameData->characterInspectTable().getStat(StatLabels[index]))
            {
                helpTitle = pHelp->name;
                helpBody = pHelp->description;
                helpAnchor = designRect(StatLabelLayoutIds[index]);
            }
        }
    }
    const Rect fixed = designRect("CharacterCreationAssignedSkill0");
    if (grantedSkills)
    {
        const Rect second = designRect("CharacterCreationAssignedSkill1");
        const Rect granted{fixed.x, fixed.y, second.x + second.width - fixed.x, fixed.height};
        skin("assigned_skill", granted, true);
        textInRect({granted.x + 9 * designScale(), granted.y, granted.width - 18 * designScale(), granted.height},
                   "All skills - Grandmaster", "menu_arrus", 14.72f);
        textInRect(
            {granted.x, granted.y + granted.height + 12 * designScale(), granted.width, 75 * designScale()},
            "Every skill is granted at level 200.\nAll spells are learned.\nNo starting skill choices are needed.",
            "menu_arrus", 13.3333f);
    }
    for (size_t index = 0; !grantedSkills && index < m_state.defaultSkills.size(); ++index)
    {
        const Rect rect = index < 2 ? designRect("CharacterCreationAssignedSkill" + std::to_string(index))
                                    : Rect{fixed.x + float(index % 2) * (fixed.width + 5 * designScale()),
                                           fixed.y + float(index / 2) * (fixed.height + 4 * designScale()), fixed.width,
                                           fixed.height};
        skin("assigned_skill", rect, true);
        textInRect({rect.x + 9 * designScale(), rect.y, rect.width - 18 * designScale(), rect.height},
                   displaySkillName(m_state.defaultSkills[index]), "menu_arrus", 14.72f);
        inspectSkill(m_state.defaultSkills[index], rect);
    }
    const size_t required = std::min(MaximumOptionalSkillSelections, m_state.optionalSkills.size());
    const float fixedRows = std::ceil(m_state.defaultSkills.size() / 2.0f);
    const float skillOffset = (fixedRows - 1) * (fixed.height + 4 * designScale());
    if (!grantedSkills)
    {
        label("CharacterCreationSubsection0",
              required == 0   ? "No additional skills to choose"
              : required == 1 ? "Choose one more"
                              : "Choose two more",
              0, skillOffset / designScale());
        if (required > 0)
        {
            label("CharacterCreationSkillCount",
                  std::to_string(m_state.selectedOptionalSkills.size()) + " / " + std::to_string(required), 0,
                  skillOffset / designScale());
        }
    }
    for (size_t index = 0; !grantedSkills && index < m_state.optionalSkills.size(); ++index)
    {
        const std::string &skill = m_state.optionalSkills[index];
        const bool selected = std::find(m_state.selectedOptionalSkills.begin(), m_state.selectedOptionalSkills.end(),
                                        skill) != m_state.selectedOptionalSkills.end();
        Rect first = designRect("CharacterCreationAvailableSkill0");
        first.y += skillOffset;
        const Rect column = designRect("CharacterCreationColumnRule");
        const float rows = std::ceil(m_state.optionalSkills.size() / 2.0f);
        const float gap = 5.33f * designScale();
        const float rowHeight = std::min(first.height, (column.y + column.height - first.y - (rows - 1) * gap) / rows);
        const Rect rect{first.x + float(index % 2) * (first.width + 5.33f * designScale()),
                        first.y + float(index / 2) * (rowHeight + 5.33f * designScale()), first.width, rowHeight};
        if (button("skill-" + skill, rect, "", "skill", selected || m_state.selectedOptionalSkills.size() < required,
                   selected))
        {
            tryToggleOptionalSkill(skill);
        }
        textInRect({rect.x + 8 * designScale(), rect.y, rect.width - 28 * designScale(), rect.height},
                   displaySkillName(skill), "menu_arrus", 14.08f);
        textInRect({rect.x + rect.width - 18 * designScale(), rect.y, 12 * designScale(), rect.height},
                   selected ? "*" : "+", "menu_lucida", 12);
        inspectSkill(skill, rect);
    }
    saveActivePartyState();
    size_t ready = 0;
    for (size_t index = 0; index < m_partySize; ++index)
    {
        const CreationState &state = m_partyStates[index];
        const bool complete =
            isGodLichState(state) || (!trimCopy(state.name).empty() &&
                                      (m_allowIncompleteCharacterCreation ||
                                       (bonusPoolForState(state) <= 0 &&
                                        state.selectedOptionalSkills.size() >=
                                            std::min(MaximumOptionalSkillSelections, state.optionalSkills.size()))));
        if (complete)
        {
            ++ready;
        }
        const Rect rect = designRect(PartySlotButtonLayoutIds[index]);
        if (button("party-" + std::to_string(index), rect, "", "party_slot", true, index == m_activePartySlot))
        {
            switchActivePartySlot(index);
        }
        if (const CharacterDollEntry *pMember = characterEntryForState(m_partyStates[index]))
        {
            drawTexture(portraitTextureNameForEntry(*pMember),
                        {rect.x + 5 * designScale(), rect.y + 3 * designScale(), rect.width - 10 * designScale(),
                         rect.height - 6 * designScale()});
            const float classIconSize = 20 * designScale();
            drawTexture(classIconTextureName(classNameForState(state)),
                        {rect.x + (rect.width - classIconSize) / 2,
                         rect.y - classIconSize - 4 * designScale(), classIconSize, classIconSize});
        }
    }
    if (m_partySize < PartySlotButtonLayoutIds.size() && !isGodLichSelected() &&
        button("add-party", designRect(PartySlotButtonLayoutIds[m_partySize]), "+", "party_slot"))
    {
        addPartySlot();
    }
    Rect summary = designRect("CharacterCreationPartySummary");
    const Rect lastSlot = designRect(PartySlotButtonLayoutIds[std::min(m_partySize, size_t(4))]);
    summary.x = lastSlot.x + lastSlot.width + 15 * designScale();
    textInRect(summary, std::to_string(m_partySize) + " / 5 adventurers\n" + std::to_string(ready) + " ready",
               "menu_lucida", 9.6f, 0xffa6b9b7u);
    label("CharacterCreationReadiness", m_state.statusMessage.empty()
                                            ? ready == m_partySize
                                                  ? "Your party is ready."
                                                  : "Assign bonus points and starting skills to each adventurer."
                                            : m_state.statusMessage);
    if (action("CharacterCreationCancelButton"))
    {
        cancelCreation();
        return;
    }
    if (action("CharacterCreationConfirmButton", ready == m_partySize || isGodLichSelected()))
    {
        confirmCreation();
    }
    if (!helpBody.empty())
    {
        const float scale = designScale();
        const float width = 425 * scale;
        const float horizontalPadding = 32 * scale;
        const float bodyTop = 56 * scale;
        const float lineHeight = (fontHeight("SMALLNUM") + 2) * scale;
        const float bodyWidth = width - 2 * horizontalPadding;
        const std::vector<std::string> lines = wrapTextToWidth("SMALLNUM", helpBody, bodyWidth, scale);
        float height = bodyTop + 28 * scale + lines.size() * lineHeight;
        std::vector<std::pair<std::vector<std::string>, uint32_t>> masteryLines;
        for (const auto &[text, color] : helpMasteries)
        {
            masteryLines.emplace_back(wrapTextToWidth("SMALLNUM", text, bodyWidth, scale), color);
            height += masteryLines.back().first.size() * lineHeight + 6 * scale;
        }
        if (!masteryLines.empty())
        {
            height += 8 * scale;
        }
        const float x = helpAnchor.x + helpAnchor.width + width + 12 * scale < frameWidth()
                            ? helpAnchor.x + helpAnchor.width + 12 * scale
                            : helpAnchor.x - width - 12 * scale;
        const Rect panel{
            std::clamp(x, 8 * scale, std::max(8 * scale, frameWidth() - width - 8 * scale)),
            std::clamp(helpAnchor.y + (helpAnchor.height - height) / 2, 8 * scale,
                       std::max(8 * scale, frameHeight() - height - 8 * scale)),
            width, height};
        skin("modal", panel);
        drawText("Create", helpTitle, panel.x + (width - measureTextWidth("Create", helpTitle, scale)) / 2,
                 panel.y + 22 * scale, GameplayUiSkin::Gold, scale);
        float textY = panel.y + bodyTop;
        for (const std::string &line : lines)
        {
            drawText("SMALLNUM", line, panel.x + horizontalPadding, textY, GameplayUiSkin::Ivory, scale);
            textY += lineHeight;
        }
        textY += 8 * scale;
        for (const auto &[wrappedLines, color] : masteryLines)
        {
            textY += 6 * scale;
            for (const std::string &line : wrappedLines)
            {
                drawText("SMALLNUM", line, panel.x + horizontalPadding, textY, color, scale);
                textY += lineHeight;
            }
        }
    }
    drawConfirmation();
}

} // namespace OpenYAMM::Game
