#include "game/ui/screens/NewGameScreen.h"

#include "engine/Localization.h"
#include "engine/Utf8Text.h"

#include "game/audio/GameAudioSystem.h"
#include "game/content/ContentManifest.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameMechanics.h"
#include "game/party/SkillData.h"
#include "game/party/SpeechIds.h"
#include "game/rules/GameRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawRulesFactory.h"
#include "game/ui/GameplayUiSkin.h"
#include "game/ui/screens/PartyCreationSheet.h"

#include <algorithm>
#include <array>
#include <cassert>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
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
constexpr int32_t UndeadRaceId = 6;
constexpr int StartingBonusPool = 15;
constexpr int NeutralBaseStatValue = 11;
constexpr int MinimumStatOffset = 2;
constexpr int MaximumStatValue = 25;
constexpr int BoostedMaximumStatValue = 34;
constexpr float NameBackspaceInitialRepeatDelaySeconds = 0.35f;
constexpr float NameBackspaceRepeatIntervalSeconds = 0.065f;
constexpr size_t MaximumOptionalSkillSelections = 2;
constexpr size_t MaximumNameLength = 15;
constexpr std::string_view CreationCompletionErrorText =
    Engine::trNoop("Create Party cannot be completed unless you have assigned all characters 2 extra skills and have "
                   "spent all of your bonus points.");

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

// A Vampire, Dark Elf or Dragon by race starts with the race's ability whatever the class: no shop teaches it, so it
// is a fixed starting skill and never takes one of the two choices.
const char *racialAbilityForRace(uint32_t raceId)
{
    switch (raceId)
    {
    case 1:
        return "VampireAbility";
    case 2:
        return "DarkElfAbility";
    case 5:
        return "DragonAbility";
    default:
        return nullptr;
    }
}

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
        // The home-world debug Lich keeps the classic skills; `skill set` grants technology and ruleset skills.
        if (!isTechnologySkill(skillName) && !isRulesetSkill(skillName))
        {
            character.skills[skillName] = {skillName, 200, SkillMastery::Grandmaster};
        }
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
        return Engine::tr("Leather");
    }

    if (canonicalName == "ChainArmor")
    {
        return Engine::tr("Chain");
    }

    return Engine::localize(displaySkillName(skillName));
}

}

NewGameScreen::NewGameScreen(const Engine::AssetFileSystem &assetFileSystem, GameAudioSystem *pGameAudioSystem,
                             const GameDataRepository &gameData, bool debugGodLichRoster, bool includeGodLichCandidate,
                             bool allowIncompleteCharacterCreation, ContinueAction continueAction,
                             ActivateRulesetAction activateRulesetAction, BackAction backAction)
    : MenuDesignScreen(assetFileSystem, false, pGameAudioSystem), m_pGameAudioSystem(pGameAudioSystem),
      m_pGameData(&gameData), m_debugGodLichRoster(debugGodLichRoster),
      m_includeGodLichCandidate(includeGodLichCandidate),
      m_allowIncompleteCharacterCreation(allowIncompleteCharacterCreation), m_continueAction(std::move(continueAction)),
      m_activateRulesetAction(std::move(activateRulesetAction)), m_backAction(std::move(backAction)),
      m_nameRng(std::random_device{}())
{
}

NewGameScreen::~NewGameScreen() = default;

AppMode NewGameScreen::mode() const
{
    return AppMode::NewGame;
}

void NewGameScreen::prepareForFirstFrame()
{
    loadDesign("gameplay/continent_selection");
    loadDesign("gameplay/character_creation");
    loadDesign("gameplay/ruleset_rules");
    preloadLayoutAssets(m_designLayouts);
}

void NewGameScreen::onEnter()
{
    loadDesign("gameplay/continent_selection");
    loadDesign("gameplay/character_creation");
    m_stage = FlowStage::ContinentSelection;
    m_characterCreationInitialized = false;
    m_selectedContinent = {};
    m_rulesPanelOpen = false;
    loadRulesets();
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

    // The new adventurer starts from the first portrait nobody in the party has.
    size_t candidateIndex = 0;

    for (size_t index = 0; index < m_candidates.size(); ++index)
    {
        const bool used = std::any_of(m_partyStates.begin(), m_partyStates.end(),
            [this, index](const CreationState &state)
            {
                return candidateForState(state).characterDataId == m_candidates[index].characterDataId;
            });

        if (!used)
        {
            candidateIndex = index;
            break;
        }
    }

    m_partySize += 1;
    ensurePartyStates();
    m_activePartySlot = m_partySize - 1;
    resetStateForCandidate(candidateIndex);
    saveActivePartyState();
}

void NewGameScreen::removePartySlotAt(size_t slotIndex)
{
    endNameEditing(true);
    saveActivePartyState();

    if (m_partySize <= 1 || slotIndex >= m_partySize)
    {
        return;
    }

    m_partyStates.erase(m_partyStates.begin() + std::ptrdiff_t(slotIndex));
    m_partySize -= 1;

    // The same adventurer stays selected; removing the selected one selects the next.
    if (slotIndex < m_activePartySlot)
    {
        m_activePartySlot -= 1;
    }

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
        if (pEntry == nullptr || (!pEntry->availableAtStart && !selectionTable.freeSelection()) || pEntry->raceId < 0)
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

            availableClassIds.push_back(
                selectionTable.freeSelection() ? *classId : startingCasterClassId(*classId, *pContinent));
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
        const uint32_t defaultClassId = selectionTable.freeSelection()
            ? pEntry->defaultClassId
            : startingCasterClassId(pEntry->defaultClassId, *pContinent);
        candidate.classId = classIdNear(defaultClassId, candidate.availableClassIds, 1);

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

    if (!m_state.nameTyped)
    {
        m_state.name = generateDefaultNameForState(m_state);
    }

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
    m_state.skillPickCount = MaximumOptionalSkillSelections;

    if (m_pGameData != nullptr)
    {
        const char *pRacialAbility = racialAbilityForRace(candidate.raceId);

        for (const char *pSkillName : OrderedSkillNames)
        {
            const StartingSkillAvailability availability =
                m_pGameData->classSkillTable().getEffectiveStartingSkillAvailability(
                    selectedClassName(),
                    candidate.raceId,
                    pSkillName);

            if (availability == StartingSkillAvailability::HasByDefault
                || (pRacialAbility != nullptr && std::string_view(pSkillName) == pRacialAbility))
            {
                m_state.defaultSkills.push_back(pSkillName);
            }
            else if (availability == StartingSkillAvailability::None
                && m_pGameData->classSkillTable().getStartingSkillAvailability(selectedClassName(), pSkillName)
                    == StartingSkillAvailability::HasByDefault)
            {
                // A free skill of the class that the race may not learn is replaced by a pick.
                ++m_state.skillPickCount;
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
#if !defined(__ANDROID__) && !defined(OPENYAMM_IOS)
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
            m_state.nameTyped = m_state.nameTyped || trimmed != m_state.name;
            m_state.name = trimmed;
        }
    }

    m_state.nameEditing = false;
#if !defined(__ANDROID__) && !defined(OPENYAMM_IOS)
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
    if (text.empty())
    {
        return {};
    }

    // The shared wrap breaks between the characters of scripts written without spaces too, and never inside a
    // character or a colour code.
    std::vector<std::string> lines = Engine::Utf8::wrap(text, maxWidth,
        [this, &fontName, scale](const std::string &line)
        {
            return measureTextWidth(fontName, line, scale);
        });
    GameplayHudCommon::carryTextColorsAcrossLines(lines);
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

    if (m_state.selectedOptionalSkills.size() >= m_state.skillPickCount)
    {
        m_state.statusMessage =
            Engine::tr("Only {count} additional skills can be selected.", {{"count", m_state.skillPickCount}});
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

    // A world's own voices (MM9's personalities, character_voices.txt World row) go with its own portraits: such a
    // face is offered every one of them of its sex (the undead ones for a lich), and only those.
    const MergedCharacterVoiceTable &voiceTable = m_pGameData->characterVoiceTable();
    const bool female = pSelectedEntry->defaultSex != 0;
    const char *pSexRow = pSelectedEntry->raceId == UndeadRaceId ? (female ? "Undead Woman" : "Undead Man")
                                                                   : (female ? "Woman" : "Man");

    for (uint32_t voiceSetId : voiceTable.voiceSetsOfWorld(pSelectedEntry->worldId))
    {
        if (voiceTable.voiceSetProperty(voiceSetId, pSexRow) == "x")
        {
            voiceIds.push_back(static_cast<int>(voiceSetId));
        }
    }

    if (!voiceIds.empty())
    {
        return voiceIds;
    }

    std::unordered_set<int> seenVoiceIds;

    for (size_t candidateIndex = 0; candidateIndex < candidateCount(); ++candidateIndex)
    {
        const CreationCandidate &candidate = candidateAt(candidateIndex);
        const CharacterDollEntry *pEntry = m_pGameData->characterDollTable().getCharacter(candidate.characterDataId);

        // A voice is offered when an offered portrait of the same race and sex speaks with it (a world's own voices
        // only to that world's faces, above).
        if (pEntry == nullptr || pEntry->defaultSex != pSelectedEntry->defaultSex
            || pEntry->raceId != pSelectedEntry->raceId)
        {
            continue;
        }

        const int voiceId = static_cast<int>(pEntry->defaultVoiceId);

        if (!voiceTable.voiceSetProperty(pEntry->defaultVoiceId, "World").empty())
        {
            continue;
        }

        if (seenVoiceIds.insert(voiceId).second)
        {
            voiceIds.push_back(voiceId);
        }
    }

    std::sort(voiceIds.begin(), voiceIds.end());
    return voiceIds;
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

void NewGameScreen::showCreationCompletionError()
{
    m_state.statusMessage = Engine::tr(CreationCompletionErrorText);
}

const GameRules &NewGameScreen::creationRules()
{
    if (m_ruleset.id != MawRulesetId || m_pGameData == nullptr)
    {
        m_pCreationRules.reset();
        return standardGameRules();
    }

    if (!m_pCreationRules || m_creationRulesSelection != m_ruleset)
    {
        m_pCreationRules = createMawRules(*m_pGameData, m_ruleset.options);
        m_creationRulesSelection = m_ruleset;
    }

    return m_pCreationRules ? m_pCreationRules->gameRules() : standardGameRules();
}

std::vector<std::pair<std::string, uint32_t>> NewGameScreen::creationSkillMatrixLines(const Character &character) const
{
    std::vector<std::pair<std::string, uint32_t>> lines;

    if (m_pGameData == nullptr)
    {
        return lines;
    }

    const ClassSkillTable &table = m_pGameData->classSkillTable();
    std::array<std::string, 5> skillsByCap;
    bool promoted = false;

    for (const std::string &skill : allCanonicalSkillNames())
    {
        if (isTechnologySkill(skill))
        {
            continue;
        }

        const SkillMastery start = table.getEffectiveCap(character.className, character.raceId, skill);
        const SkillMastery best =
            std::max(start, table.getHighestPromotionEffectiveCap(character.className, character.raceId, skill));

        if (best == SkillMastery::None)
        {
            continue;
        }

        std::string &names = skillsByCap[size_t(best)];
        names += (names.empty() ? "" : ", ") + Engine::localize(displaySkillName(skill)) + (best > start ? "*" : "");
        promoted = promoted || best > start;
    }

    for (const SkillMastery mastery :
         {SkillMastery::Grandmaster, SkillMastery::Master, SkillMastery::Expert, SkillMastery::Normal})
    {
        if (!skillsByCap[size_t(mastery)].empty())
        {
            lines.emplace_back(Engine::tr("{mastery}: {skills}",
                                   {{"mastery", Engine::tr(masteryDisplayName(mastery))},
                                    {"skills", skillsByCap[size_t(mastery)]}}),
                               0xffffffffu);
        }
    }

    if (promoted)
    {
        lines.emplace_back(Engine::tr("* after a promotion"), GameplayUiSkin::Low);
    }

    return lines;
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
            m_state.statusMessage = Engine::tr("Character name cannot be empty.");
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

            const size_t requiredSkillCount = std::min(state.skillPickCount, state.optionalSkills.size());

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

        NewGameOptions options = {};
        options.continentId = m_selectedContinent.id;
        options.preserveDebugLoadout = godLichParty;
        options.ruleset = m_ruleset;
        m_continueAction(characters, options);
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

    std::string rulesetError;

    // The data reloads under the ruleset, so preview rules built on the old tables go.
    m_pCreationRules.reset();

    if (m_activateRulesetAction && !m_activateRulesetAction(m_ruleset.id, rulesetError))
    {
        std::cerr << "New game: " << rulesetError << '\n';
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

namespace
{
// Rules panel geometry in canvas units: the mockup's 1600x900 pixels divided by 1.875
// (level_generation/ui/ruleset_choice_20261023/).
constexpr float RulesPixel = 1 / 1.875f;
constexpr float RulesRowPitch = 50 * RulesPixel;
constexpr float RulesSectionGap = 26 * RulesPixel;
constexpr uint32_t RulesSelectedText = 0xffaedff5u;
constexpr uint32_t RulesWarningText = 0xff8aa9e6u;
constexpr uint32_t RulesDisabledText = 0xff6b777au;
constexpr uint32_t RulesDetailFill = 0x1861abbbu;
constexpr uint32_t RulesDetailEdge = 0xff6396acu;
constexpr uint32_t RulesDivider = 0x2b648680u;
constexpr uint32_t SwitchFill = 0x8c14160bu;
constexpr uint32_t SwitchOutline = 0xff5f818cu;
constexpr std::string_view ContinentHint = Engine::trNoop("Choose a continent to create your party.");

// Headings in capitals, after the lookup: every letter, not only ASCII ones.
std::string upperCopy(const std::string &text)
{
    return Engine::Utf8::upper(text);
}

// "Hell difficulty · Free progression", or the short "Hell · Free · Doom · Randomizer" when more is chosen.
std::string rulesetOptionsSummary(const RulesetOptions &options)
{
    const std::string difficulty = Engine::tr(rulesetDifficultyName(options.difficulty));
    const std::string progression = Engine::tr(rulesetProgressionName(options.progression));
    if (options.challengeMode == RulesetChallengeMode::None && !options.randomizer)
    {
        return Engine::tr("{difficulty} difficulty · {progression} progression",
                          {{"difficulty", difficulty}, {"progression", progression}});
    }
    std::string summary = difficulty + " · " + progression;
    if (options.challengeMode != RulesetChallengeMode::None)
    {
        summary += " · " + Engine::tr(rulesetChallengeModeName(options.challengeMode));
    }
    if (options.randomizer)
    {
        summary += " · " + Engine::tr("Randomizer");
    }
    return summary;
}
} // namespace

void NewGameScreen::loadRulesets()
{
    std::string error;
    if (!loadAvailableRulesets(assetFileSystem(), m_rulesets, error))
    {
        std::cerr << "New game: " << error << '\n';
        m_rulesets = {standardRulesetDefinition()};
    }
    const bool installed = std::any_of(m_rulesets.begin(), m_rulesets.end(),
                                       [this](const RulesetDefinition &ruleset) { return ruleset.id == m_ruleset.id; });
    if (!installed)
    {
        m_ruleset = {};
    }
}

const RulesetDefinition &NewGameScreen::chosenRulesetDefinition() const
{
    for (const RulesetDefinition &ruleset : m_rulesets)
    {
        if (ruleset.id == m_ruleset.id)
        {
            return ruleset;
        }
    }
    static const RulesetDefinition Standard = standardRulesetDefinition();
    return Standard;
}

std::optional<size_t> NewGameScreen::drawSegmentedSwitch(const std::string &id, const Rect &frame,
                                                         const std::vector<std::string> &labels, size_t selected,
                                                         bool enabled)
{
    drawSolidRect(frame, SwitchFill);
    outline(frame, SwitchOutline);
    const float inset = 3 * RulesPixel * designScale();
    const float gap = 2 * RulesPixel * designScale();
    const float count = float(labels.size());
    const float width = (frame.width - 2 * inset - gap * (count - 1)) / count;
    std::optional<size_t> clicked;
    for (size_t index = 0; index < labels.size(); ++index)
    {
        const Rect tab{frame.x + inset + float(index) * (width + gap), frame.y + inset, width,
                       frame.height - 2 * inset};
        if (button(id + std::to_string(index), tab, "", "tab", enabled, index == selected))
        {
            clicked = index;
        }
        // One line that shrinks to fit, where button text would wrap a long name such as "Standard MMMerge".
        constexpr float LabelSize = 25 * RulesPixel;
        const float labelHeight = LabelSize * designScale();
        const uint32_t color = !enabled              ? RulesDisabledText
                               : index == selected   ? RulesSelectedText
                               : pointerInside(tab) ? 0xffa8d7ecu
                                                     : 0xffb2c1bfu;
        textInRect({tab.x + 6 * RulesPixel * designScale(), tab.y + (tab.height - labelHeight) / 2,
                    tab.width - 12 * RulesPixel * designScale(), labelHeight},
                   labels[index], "fondamento", LabelSize, color, true);
    }
    return clicked;
}

void NewGameScreen::drawRulesetSwitch()
{
    if (m_rulesets.size() < 2)
    {
        label("ContinentSelectionFooterNote", Engine::tr(ContinentHint));
        return;
    }
    label("ContinentSelectionRulesetLabel", upperCopy(Engine::tr("Ruleset")));
    std::vector<std::string> names;
    size_t selected = 0;
    for (size_t index = 0; index < m_rulesets.size(); ++index)
    {
        // ruleset.yml texts are English; the shared catalogue translates them.
        names.push_back(Engine::localize(m_rulesets[index].name));
        selected = m_rulesets[index].id == m_ruleset.id ? index : selected;
    }
    const std::optional<size_t> clicked =
        drawSegmentedSwitch("ruleset", designRect("ContinentSelectionRulesetSwitch"), names, selected, true);
    if (clicked && m_rulesets[*clicked].id != m_ruleset.id)
    {
        m_rulesetOptions[m_ruleset.id] = m_ruleset.options;
        const RulesetDefinition &next = m_rulesets[*clicked];
        const auto stored = m_rulesetOptions.find(next.id);
        m_ruleset = {next.id, stored != m_rulesetOptions.end() ? stored->second : next.defaultOptions()};
    }
    const RulesetDefinition &ruleset = chosenRulesetDefinition();
    const std::string summary =
        Engine::localize(ruleset.panel.summary.empty() ? ruleset.description : ruleset.panel.summary);
    if (ruleset.isStandard())
    {
        label("ContinentSelectionRulesetSummary", summary);
        label("ContinentSelectionFooterNote", Engine::tr(ContinentHint));
        return;
    }
    label("ContinentSelectionRulesetOptions", rulesetOptionsSummary(m_ruleset.options));
    label("ContinentSelectionFooterNote", summary);
    if (action("ContinentSelectionRulesButton"))
    {
        m_rulesDraft = m_ruleset.options;
        m_rulesScroll = 0;
        m_rulesContentHeight = 0;
        m_rulesPanelOpen = true;
    }
}

MenuScreenBase::Rect NewGameScreen::rulesRect(const std::string &id, float y) const
{
    Rect rect = designRect(id);
    rect.y += (y - m_rulesScroll) * designScale();
    return rect;
}

float NewGameScreen::drawRulesText(const std::string &id, const std::string &text, float y, uint32_t color)
{
    if (text.empty())
    {
        return 0;
    }
    const UiLayoutManager::LayoutElement *pElement = m_designLayouts.findElement(id);
    const float size = fontHeight(pElement->fontName) * pElement->textScale;
    Rect rect = rulesRect(id, y);
    rect.height = textBlockHeight(text, pElement->fontName, size, rect.width);
    textInRect(rect, text, pElement->fontName, size, color ? color : pElement->textColorAbgr,
               pElement->textAlignX == UiLayoutManager::TextAlignX::Center);
    return rect.height / designScale();
}

float NewGameScreen::drawRulesSetting(const std::string &id, const std::string &name, const std::string &description,
                                      bool select, const std::string &value, bool enabled, bool last, float y,
                                      bool &activated)
{
    const float unit = designScale();
    const float padding = 8 * RulesPixel;
    const float top = y + padding;
    // The name, the description and a select's value come translated; a toggle's value is the English "On" or "Off".
    label("RulesetRulesSettingName", name, enabled ? 0 : RulesDisabledText, top - m_rulesScroll);
    if (select)
    {
        activated = selectBox(id, rulesRect("RulesetRulesSettingSelect", top), value, enabled);
    }
    else
    {
        const Rect rect = rulesRect("RulesetRulesSettingToggle", top);
        activated = button(id, rect, "", value == "On" ? "toggle_on" : "toggle_off", enabled);
        textInRect({rect.x + rect.width * 0.42f, rect.y, rect.width * 0.46f, rect.height},
                   value == "On" ? Engine::tr("On") : Engine::tr("Off"), "menu_lucida", 10,
                   enabled ? 0xffc6dfeau : RulesDisabledText, true);
    }
    float bottom = top + m_designLayouts.findElement("RulesetRulesSettingName")->height + 4 * RulesPixel;
    bottom += drawRulesText("RulesetRulesSettingDescription", description, bottom) + padding;
    if (!last)
    {
        const Rect column = rulesRect("RulesetRulesProgressionSwitch", bottom);
        drawSolidRect({column.x, column.y, column.width, std::max(1.0f, RulesPixel * unit)}, RulesDivider);
    }
    return bottom + RulesPixel;
}

void NewGameScreen::drawRulesPanel()
{
    const RulesetDefinition &ruleset = chosenRulesetDefinition();
    const RulesetChoices &choices = ruleset.choices;
    const RulesetPanelText &panel = ruleset.panel;
    RulesetOptions &draft = m_rulesDraft;
    loadDesign("gameplay/ruleset_rules");
    beginDesign("RulesetRules");
    drawDesign();
    label("RulesetRulesTitle", panel.title.empty()
                                   ? Engine::tr("{ruleset} Rules", {{"ruleset", Engine::localize(ruleset.name)}})
                                   : Engine::localize(panel.title));
    label("RulesetRulesStep", Engine::localize(panel.subtitle));

    // A quiet link to the ruleset's player's guide, when it has one.
    if (!ruleset.guideUrl.empty())
    {
        const Rect guideRect = designRect("RulesetRulesGuideLink");
        const bool hovered = !modalOpen() && pointerInside(guideRect);
        label("RulesetRulesGuideLink", Engine::tr("Player's guide"), hovered ? 0xffc8e6f2u : 0xff91c3d9u);

        if (hovered && leftMouseJustPressed())
        {
            SDL_OpenURL(ruleset.guideUrl.c_str());
        }
    }

    const std::string challengeName = Engine::tr(rulesetChallengeModeName(draft.challengeMode));
    // Doom, Road to Insanity and Beyond Madness set the difficulty; Austerity keeps the chosen one.
    const bool challengeDifficulty = rulesetChallengeModeDifficulty(draft.challengeMode).has_value();
    label("RulesetRulesNote",
          challengeDifficulty
              ? Engine::tr("{challenge} sets the difficulty for the whole adventure; preferences can change.",
                           {{"challenge", challengeName}})
          : draft.difficultyLocked()
              ? Engine::tr("{difficulty} cannot be lowered later; progression and preferences can change.",
                           {{"difficulty", Engine::tr(rulesetDifficultyName(draft.difficulty))}})
              : Engine::tr("Difficulty, progression and preferences can change during play."));
    if (action("RulesetRulesBackButton") || (m_escapePressed && !modalOpen()))
    {
        m_escapePressed = false;
        m_rulesPanelOpen = false;
        return;
    }
    if (action("RulesetRulesDefaultsButton"))
    {
        draft = ruleset.defaultOptions();
    }
    if (action("RulesetRulesApplyButton", ruleset.offers(draft)))
    {
        m_ruleset.options = draft;
        m_rulesetOptions[ruleset.id] = draft;
        m_rulesPanelOpen = false;
        return;
    }

    const float unit = designScale();
    const Rect viewport = designRect("RulesetRulesScrollViewport");
    scrollViewport(viewport, m_rulesContentHeight, m_rulesScroll);
    setDesignClip(viewport);

    // Left column: the difficulty table, the chosen level's rules and the credits.
    label("RulesetRulesDifficultyLabel", upperCopy(Engine::tr("Difficulty")), 0, -m_rulesScroll);
    label("RulesetRulesDifficultyNote",
          challengeDifficulty ? Engine::tr("Fixed by {challenge}", {{"challenge", challengeName}}) : "", 0,
          -m_rulesScroll);
    label("RulesetRulesColumnLevel", upperCopy(Engine::tr("Level")), 0, -m_rulesScroll);
    std::vector<Rect> columns;
    for (size_t column = 0; column < panel.difficultyColumns.size(); ++column)
    {
        const std::string id = "RulesetRulesColumn" + std::to_string(column);
        if (m_designLayouts.findElement(id) == nullptr)
        {
            break;
        }
        label(id, upperCopy(Engine::localize(panel.difficultyColumns[column])), 0, -m_rulesScroll);
        columns.push_back(designRect(id));
    }
    const UiLayoutManager::LayoutElement *pValue = m_designLayouts.findElement("RulesetRulesRowValue");
    const float valueSize = fontHeight(pValue->fontName) * pValue->textScale;
    for (size_t index = 0; index < choices.difficulties.size(); ++index)
    {
        const RulesetDifficulty difficulty = choices.difficulties[index];
        const float y = float(index) * RulesRowPitch;
        const bool selected = draft.difficulty == difficulty;
        const Rect row = rulesRect("RulesetRulesRow", y);
        if (button("difficulty-" + std::string(rulesetDifficultyId(difficulty)), row, "", "save_row",
                   !challengeDifficulty, selected))
        {
            draft.difficulty = difficulty;
        }
        const uint32_t color = selected ? RulesSelectedText : 0;
        label("RulesetRulesRowName", Engine::tr(rulesetDifficultyName(difficulty)), color, y - m_rulesScroll);
        const auto text = panel.difficulties.find(difficulty);
        for (size_t column = 0; text != panel.difficulties.end() && column < columns.size()
                                && column < text->second.values.size();
             ++column)
        {
            textInRect({columns[column].x, row.y, columns[column].width, row.height},
                       Engine::localize(text->second.values[column]),
                       pValue->fontName, valueSize, color ? color : pValue->textColorAbgr, true);
        }
        RulesetOptions probe;
        probe.difficulty = difficulty;
        label("RulesetRulesRowMark",
              difficulty == choices.defaultDifficulty ? Engine::tr("default")
              : probe.difficultyLocked()             ? Engine::tr("locks")
                                                     : "",
              selected ? RulesSelectedText : 0, y - m_rulesScroll);
    }
    const UiLayoutManager::LayoutElement *pRow = m_designLayouts.findElement("RulesetRulesRow");
    const size_t rowCount = std::max<size_t>(1, choices.difficulties.size());
    const float detailY = pRow->gapY + float(rowCount - 1) * RulesRowPitch + pRow->height + 6 * RulesPixel;
    const auto detail = panel.difficulties.find(draft.difficulty);
    const std::string description =
        Engine::localize(detail != panel.difficulties.end() ? detail->second.description : "");
    const std::string warning = Engine::localize(detail != panel.difficulties.end() ? detail->second.warning : "");
    const UiLayoutManager::LayoutElement *pDetailText = m_designLayouts.findElement("RulesetRulesDetailText");
    const float detailSize = fontHeight(pDetailText->fontName) * pDetailText->textScale;
    const float detailWidth = pDetailText->width * unit;
    float detailTextHeight = textBlockHeight(description, pDetailText->fontName, detailSize, detailWidth) / unit;
    if (!warning.empty())
    {
        detailTextHeight +=
            4 * RulesPixel + textBlockHeight(warning, pDetailText->fontName, detailSize, detailWidth) / unit;
    }
    const float detailHeight = std::max(m_designLayouts.findElement("RulesetRulesDetail")->height,
                                        pDetailText->gapY + detailTextHeight + 12 * RulesPixel);
    Rect box = rulesRect("RulesetRulesDetail", detailY);
    box.height = detailHeight * unit;
    drawSolidRect(box, RulesDetailFill);
    drawSolidRect({box.x, box.y, 2 * RulesPixel * unit, box.height}, RulesDetailEdge);
    label("RulesetRulesDetailTitle", Engine::tr(rulesetDifficultyName(draft.difficulty)), 0,
          detailY - m_rulesScroll);
    const float descriptionHeight = drawRulesText("RulesetRulesDetailText", description, detailY);
    drawRulesText("RulesetRulesDetailText", warning, detailY + descriptionHeight + 4 * RulesPixel, RulesWarningText);
    std::string credits;
    for (const std::string &credit : ruleset.credits)
    {
        credits += (credits.empty() ? "" : "; ") + credit;
    }
    if (!credits.empty())
    {
        credits = Engine::tr("Credits: {credits}", {{"credits", credits}});
    }
    const float creditsY = detailY + detailHeight + 12 * RulesPixel;
    const float leftBottom = creditsY + drawRulesText("RulesetRulesCredits", credits, creditsY);

    // Right column: progression, the challenge and the preferences, one under another.
    const auto section = [this](const std::string &name, const std::string &note, float y)
    {
        label("RulesetRulesSectionLabel", upperCopy(name), 0, y - m_rulesScroll);
        label("RulesetRulesSectionNote", note, 0, y - m_rulesScroll);
        return y + 26 * RulesPixel;
    };
    float y = 8 * RulesPixel;
    const std::optional<RulesetProgression> forcedProgression = rulesetChallengeModeProgression(draft.challengeMode);
    if (!choices.progressions.empty())
    {
        y = section(Engine::tr("Progression"),
                    forcedProgression ? Engine::tr("Set by {challenge}", {{"challenge", challengeName}}) : "", y);
        std::vector<std::string> names;
        size_t selected = 0;
        for (size_t index = 0; index < choices.progressions.size(); ++index)
        {
            names.emplace_back(Engine::tr(rulesetProgressionName(choices.progressions[index])));
            selected = choices.progressions[index] == draft.progression ? index : selected;
        }
        const std::optional<size_t> clicked = drawSegmentedSwitch(
            "progression", rulesRect("RulesetRulesProgressionSwitch", y), names, selected, !forcedProgression);
        if (clicked)
        {
            draft.progression = choices.progressions[*clicked];
        }
        y += m_designLayouts.findElement("RulesetRulesProgressionSwitch")->height + 8 * RulesPixel;
        const auto text = panel.progressions.find(draft.progression);
        y += drawRulesText("RulesetRulesProgressionText",
                           Engine::localize(text != panel.progressions.end() ? text->second : ""), y);
        y += RulesSectionGap;
    }
    bool activated = false;
    if (!choices.challengeModes.empty())
    {
        const bool modes = choices.challengeModes.size() > 1;
        y = section(Engine::tr("Challenge"),
                    modes || choices.randomizer ? Engine::tr("Chosen once · fixed for the adventure")
                                                : Engine::tr("Coming in a later update"),
                    y);
        const auto text = panel.challengeModes.find(draft.challengeMode);
        y = drawRulesSetting("challenge", Engine::tr("Challenge mode"),
                             Engine::localize(text != panel.challengeModes.end() ? text->second : ""), true,
                             challengeName, modes, false, y, activated);
        if (activated)
        {
            std::vector<std::string> names;
            for (const RulesetChallengeMode mode : choices.challengeModes)
            {
                names.emplace_back(Engine::tr(rulesetChallengeModeName(mode)));
            }
            confirm(Engine::tr("Challenge Mode"), Engine::tr("Fixed for the whole adventure."), names,
                    [this, modes = choices.challengeModes, defaults = ruleset.defaultOptions()](int index)
                    {
                        if (index < 0)
                        {
                            return;
                        }
                        const RulesetChallengeMode previous = m_rulesDraft.challengeMode;
                        // A mode that forced the difficulty or progression gives back what the player had chosen
                        // (audit CHM-4).
                        if (!rulesetChallengeModeDifficulty(previous))
                        {
                            m_unforcedDifficulty = m_rulesDraft.difficulty;
                        }
                        if (!rulesetChallengeModeProgression(previous))
                        {
                            m_unforcedProgression = m_rulesDraft.progression;
                        }
                        m_rulesDraft.challengeMode = modes[size_t(index)];
                        m_rulesDraft.progression = rulesetChallengeModeProgression(m_rulesDraft.challengeMode)
                                                       .value_or(m_unforcedProgression.value_or(defaults.progression));
                        m_rulesDraft.difficulty = rulesetChallengeModeDifficulty(m_rulesDraft.challengeMode)
                                                      .value_or(m_unforcedDifficulty.value_or(defaults.difficulty));
                    },
                    true);
        }
        // A ruleset without a randomizer (MAW's is not ported) shows no row for it.
        if (choices.randomizer)
        {
            y = drawRulesSetting("randomizer", Engine::tr("Randomizer"), Engine::localize(panel.randomizer), false,
                                 draft.randomizer ? "On" : "Off", true, true, y, activated);
            if (activated)
            {
                draft.randomizer = !draft.randomizer;
            }
        }
        y += RulesSectionGap;
    }
    if (choices.preferences)
    {
        RulesetPreferences &preferences = draft.preferences;
        y = section(Engine::tr("Preferences"), Engine::tr("Change any time"), y);
        y = drawRulesSetting("homing", Engine::tr("Homing projectiles"),
                             Engine::tr("Your missiles follow their target."), false,
                             preferences.homingProjectiles ? "On" : "Off", true, false, y, activated);
        preferences.homingProjectiles = preferences.homingProjectiles != activated;
        y = drawRulesSetting("friendly-fire", Engine::tr("Friendly fire"),
                             Engine::tr("Your attacks and spells can hurt peaceful townsfolk and guards."), false,
                             preferences.friendlyFire ? "On" : "Off", true, false, y, activated);
        preferences.friendlyFire = preferences.friendlyFire != activated;
        y = drawRulesSetting("trainer-hints", Engine::tr("Trainer hints"),
                             Engine::tr("Skill popups name the nearest teacher of the next mastery."), false,
                             preferences.trainerHints ? "On" : "Off", true, false, y, activated);
        preferences.trainerHints = preferences.trainerHints != activated;
        y = drawRulesSetting("bow", Engine::tr("Bow"),
                             Engine::tr("Off: bows, crossbows and dragon breath do not shoot. A melee-only challenge."),
                             false,
                             preferences.bowDisabled ? "Off" : "On", true, false, y, activated);
        preferences.bowDisabled = preferences.bowDisabled != activated;
        // Disintegration happens only in Road to Insanity and Beyond Madness; it closes the list, as in the pause menu.
        const bool disintegration = draft.challengeMode == RulesetChallengeMode::RoadToInsanity
            || draft.challengeMode == RulesetChallengeMode::BeyondMadness;
        y = drawRulesSetting("loot-filter", Engine::tr("Loot filter"),
                             Engine::tr("Drops you would rather not carry turn into gold. The pause menu's Settings "
                                        "show what each preset filters."),
                             true, Engine::tr(rulesetLootFilterPresetName(preferences.lootFilter.preset)), true,
                             !disintegration, y, activated);
        if (activated)
        {
            // The presets; Custom rules are made in the game's Settings.
            std::vector<std::string> names;
            for (size_t index = 0; index < size_t(RulesetLootFilterPreset::Custom); ++index)
            {
                names.emplace_back(Engine::tr(rulesetLootFilterPresetName(RulesetLootFilterPreset(index))));
            }
            confirm(Engine::tr("Loot Filter"),
                    Engine::tr("Drops you would rather not carry turn into gold (40 % of their value)."), names,
                    [this](int index)
                    {
                        if (index >= 0)
                        {
                            m_rulesDraft.preferences.lootFilter = rulesetLootFilterWithPreset(
                                RulesetLootFilterPreset(index), m_rulesDraft.preferences.lootFilter.leaveOnGround);
                        }
                    },
                    true);
        }
        if (disintegration)
        {
            y = drawRulesSetting("disintegrate", Engine::tr("Disintegration"),
                                 Engine::tr("A companion slain far past death leaves the party for the Adventurer's "
                                            "Inn."),
                                 false,
                                 preferences.disintegration ? "On" : "Off", true, true, y, activated);
            preferences.disintegration = preferences.disintegration != activated;
        }
    }
    m_rulesContentHeight = std::max(leftBottom, y) + 16 * RulesPixel;
    setDesignClip(std::nullopt);
    drawConfirmation();
}

bool NewGameScreen::continentOffered(const std::string &continentKey) const
{
    if (m_pGameData == nullptr)
    {
        return false;
    }

    const MergedCharacterSelectionContinent *pContinent =
        findNewGameContinent(m_pGameData->mergedCharacterSelectionTable(), continentKey);
    const MergedContinentSettingEntry *pSetting =
        pContinent != nullptr ? m_pGameData->mergedContinentSettingTable().findById(pContinent->id) : nullptr;

    if (pSetting == nullptr || trimCopy(pSetting->deathMap1).empty())
    {
        return false;
    }

    std::string startMap = trimCopy(pSetting->deathMap1);
    std::transform(startMap.begin(), startMap.end(), startMap.begin(),
                   [](unsigned char character) { return char(std::tolower(character)); });
    // A continent of a world this installation lacks (Chedian without MM9) stays on screen, greyed out.
    const MapStatsEntry *pMap = m_pGameData->mapStats().findByFileName(startMap);
    return pMap != nullptr && isWorldPackageMounted(assetFileSystem(), pMap->worldId)
        && assetFileSystem().exists("worlds/" + pMap->worldId + "/maps/" + startMap);
}

void NewGameScreen::drawContinentSelection(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);
    if (m_rulesPanelOpen)
    {
        drawRulesPanel();
        return;
    }
    loadDesign("gameplay/continent_selection");
    beginDesign("ContinentSelection");
    drawDesign();
    drawRulesetSwitch();
    std::string chosenContinent;
    for (const std::string key : {"enroth", "antagarich", "jadame", "chedian"})
    {
        std::string name = key;
        name[0] = char(std::toupper(name[0]));
        const std::string prefix = "ContinentSelection" + name;
        const bool available = continentOffered(key);
        const Rect rect = designRect(prefix + "Button");
        if (button(prefix, rect, "", "world_card", available, available && pointerInside(rect)))
        {
            chosenContinent = key;
        }
        // Cards draw their pictures and lettering above their blank selectable skin.
        // A card that cannot be chosen is dimmed: faded picture, grey lettering.
        const UiLayoutManager::LayoutElement *pImage = m_designLayouts.findElement(prefix + "Illustration");
        drawTextureColor(pImage->primaryAsset, designRect(prefix + "Illustration"),
                         available ? 0xffffffffu : 0x70a0a0a0u);
        const uint32_t textColor = available ? 0 : RulesDisabledText;
        label(prefix + "Name", Engine::localize(name), textColor);
        label(prefix + "Game", m_designLayouts.findElement(prefix + "Game")->labelText, textColor);
        label(prefix + "Start", m_designLayouts.findElement(prefix + "Start")->labelText, textColor);
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

bool NewGameScreen::stateComplete(const CreationState &state) const
{
    return isGodLichState(state)
        || (!trimCopy(state.name).empty()
            && (m_allowIncompleteCharacterCreation
                || (bonusPoolForState(state) <= 0
                    && state.selectedOptionalSkills.size() >= requiredSkillCount(state))));
}

size_t NewGameScreen::requiredSkillCount(const CreationState &state) const
{
    return std::min(state.skillPickCount, state.optionalSkills.size());
}

std::array<RaceStatLine, CreationStatCount> NewGameScreen::raceStatLinesForState(const CreationState &state) const
{
    const std::array<RaceStatRule, static_cast<size_t>(StatId::Count)> rules =
        raceRulesForData(m_pGameData, candidateForState(state).raceName, state.baseStats);
    std::array<RaceStatLine, CreationStatCount> lines = {};

    for (size_t index = 0; index < CreationStatCount; ++index)
    {
        lines[index] = {state.baseStats[index], rules[index].maximumValue, rules[index].baseStep,
                        rules[index].droppedStep};
    }

    return lines;
}

CreationPartyMember NewGameScreen::creationPartyMember(const CreationState &state) const
{
    CreationPartyMember member;
    member.className = classNameForState(state);
    member.raceId = candidateForState(state).raceId;
    member.fixedSkills = state.defaultSkills;
    member.optionalSkills = state.optionalSkills;
    member.chosenSkills = state.selectedOptionalSkills;
    return member;
}

std::vector<CreationPartyMember> NewGameScreen::creationPartyMembers() const
{
    std::vector<CreationPartyMember> members;

    for (size_t slotIndex = 0; slotIndex < std::min(m_partySize, m_partyStates.size()); ++slotIndex)
    {
        members.push_back(creationPartyMember(slotIndex == m_activePartySlot ? m_state : m_partyStates[slotIndex]));
    }

    return members;
}

void NewGameScreen::chooseCandidateForActiveSlot(size_t candidateIndex)
{
    endNameEditing(true);
    const uint32_t previousClassId = m_state.selectedClassId;
    const std::string typedName = m_state.nameTyped ? m_state.name : std::string();
    resetStateForCandidate(candidateIndex);

    if (!typedName.empty())
    {
        m_state.name = typedName;
        m_state.nameEditBuffer = typedName;
        m_state.nameTyped = true;
    }

    // The new portrait keeps the class when its race offers it, like stepping through portraits did.
    if (!isGodLichSelected())
    {
        m_state.selectedClassId = classIdNear(previousClassId, selectedCandidate().availableClassIds, 1);
        refreshSkillChoices(false);
    }

    saveActivePartyState();
}

bool NewGameScreen::toggleOptionalSkillForSlot(size_t slotIndex, const std::string &skillName)
{
    if (slotIndex == m_activePartySlot)
    {
        return tryToggleOptionalSkill(skillName);
    }

    if (slotIndex >= m_partyStates.size())
    {
        return false;
    }

    // Another adventurer's choice (the party board) follows the same two-choice rule.
    std::swap(m_state, m_partyStates[slotIndex]);
    const bool toggled = tryToggleOptionalSkill(skillName);
    const std::string message = m_state.statusMessage;
    std::swap(m_state, m_partyStates[slotIndex]);
    m_state.statusMessage = message;
    return toggled;
}

void NewGameScreen::playCreationVoiceLine(int voiceId, SpeechId speech)
{
    if (m_pGameAudioSystem == nullptr)
    {
        return;
    }

    Character character = buildVoicePreviewCharacter();
    character.voiceId = voiceId;
    m_pGameAudioSystem->playSpeech(character, speech, 0, CharacterCreationVoicePreviewSpeakerKey);
}

void NewGameScreen::drawScreen(float deltaSeconds)
{
    if (m_stage == FlowStage::ContinentSelection)
    {
        drawContinentSelection(deltaSeconds);
        return;
    }

    drawCharacterCreation(deltaSeconds);
}

} // namespace OpenYAMM::Game
