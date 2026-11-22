#include "game/party/CampaignState.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/ReputationRuntime.h"

#include <algorithm>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
uint32_t generateHouseStockSeed()
{
    std::random_device randomDevice;
    const uint32_t first = static_cast<uint32_t>(randomDevice());
    const uint32_t second = static_cast<uint32_t>(randomDevice());
    const uint32_t mixed = first ^ (second * 1664525u) ^ 0x9e3779b9u;
    return mixed != 0 ? mixed : 1u;
}
}

CampaignState::Snapshot CampaignState::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.houseStockSeed = m_houseStockSeed;
    snapshot.foundArtifactItems = m_foundArtifactItems;
    snapshot.arcomageWonHouseIds = m_arcomageWonHouseIds;
    snapshot.worldCompletions = m_worldCompletions;
    snapshot.worldCompletionsUntracked = m_worldCompletionsUntracked;
    snapshot.continentReputations = m_continentReputations;
    snapshot.questBits = m_questBits;
    snapshot.autonotes = m_autonotes;
    snapshot.historyEventTimesByContinent = m_historyEventTimesByContinent;
    snapshot.journalMapNotes = m_journalMapNotes;
    snapshot.eventVariables = m_eventVariables;
    snapshot.npcTopicOverrides = m_npcTopicOverrides;
    snapshot.npcGroupNews = m_npcGroupNews;
    snapshot.npcGreetingOverrides = m_npcGreetingOverrides;
    snapshot.npcGreetingDisplayCounts = m_npcGreetingDisplayCounts;
    snapshot.npcHouseOverrides = m_npcHouseOverrides;
    snapshot.npcItemOverrides = m_npcItemOverrides;
    snapshot.unavailableNpcIds = m_unavailableNpcIds;
    snapshot.questPouch = m_questPouch;

    for (const auto &[houseId, state] : m_houseStockStates)
    {
        (void)houseId;
        snapshot.houseStockStates.push_back(state);
    }

    return snapshot;
}

void CampaignState::restoreSnapshot(const Snapshot &snapshot)
{
    m_houseStockSeed = snapshot.houseStockSeed;
    m_foundArtifactItems = snapshot.foundArtifactItems;
    m_arcomageWonHouseIds = snapshot.arcomageWonHouseIds;
    m_worldCompletions = snapshot.worldCompletions;
    m_worldCompletionsUntracked = snapshot.worldCompletionsUntracked;
    m_continentReputations = snapshot.continentReputations;
    m_questBits = snapshot.questBits;
    m_autonotes = snapshot.autonotes;
    m_historyEventTimesByContinent = snapshot.historyEventTimesByContinent;
    m_journalMapNotes = snapshot.journalMapNotes;
    m_eventVariables = snapshot.eventVariables;
    m_npcTopicOverrides = snapshot.npcTopicOverrides;
    m_npcGroupNews = snapshot.npcGroupNews;
    m_npcGreetingOverrides = snapshot.npcGreetingOverrides;
    m_npcGreetingDisplayCounts = snapshot.npcGreetingDisplayCounts;
    m_npcHouseOverrides = snapshot.npcHouseOverrides;
    m_npcItemOverrides = snapshot.npcItemOverrides;
    m_unavailableNpcIds = snapshot.unavailableNpcIds;
    m_questPouch = snapshot.questPouch;
    m_houseStockStates.clear();

    for (const HouseStockState &state : snapshot.houseStockStates)
    {
        m_houseStockStates[state.houseId] = state;
    }

    ++m_questRevision;
}

void CampaignState::resetForNewParty()
{
    m_houseStockSeed = generateHouseStockSeed();
    m_foundArtifactItems.clear();
    m_continentReputations.clear();
    m_questBits.clear();
    m_autonotes.clear();
    m_historyEventTimesByContinent.clear();
    m_journalMapNotes.clear();
    m_eventVariables.clear();
    m_npcTopicOverrides.clear();
    m_npcGroupNews.clear();
    m_npcGreetingOverrides.clear();
    m_npcGreetingDisplayCounts.clear();
    m_npcHouseOverrides.clear();
    m_npcItemOverrides.clear();
    m_unavailableNpcIds.clear();
    m_questPouch.clear();
    m_houseStockStates.clear();
    ++m_questRevision;
}

bool CampaignState::hasQuestBit(uint32_t questBitId) const
{
    return questBitId != 0 && m_questBits.contains(questBitId);
}

void CampaignState::setQuestBit(uint32_t questBitId, bool value)
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
            ++m_questRevision;
            GAMEPLAY_DEBUG_TRACE("qbit_set id=" + std::to_string(questBitId));
        }
    }
    else
    {
        const size_t erased = m_questBits.erase(questBitId);
        if (erased != 0)
        {
            ++m_questRevision;
            GAMEPLAY_DEBUG_TRACE("qbit_cleared id=" + std::to_string(questBitId));
        }
    }
}

uint64_t CampaignState::questRevision() const
{
    return m_questRevision;
}

bool CampaignState::hasAutonote(uint32_t autonoteId) const
{
    return autonoteId != 0 && m_autonotes.contains(autonoteId);
}

void CampaignState::setAutonote(uint32_t autonoteId, bool value)
{
    if (autonoteId == 0)
    {
        return;
    }

    if (value)
    {
        m_autonotes.insert(autonoteId);
    }
    else
    {
        m_autonotes.erase(autonoteId);
    }
}

const std::unordered_map<uint32_t, int32_t> &CampaignState::historyEventTimes(uint32_t continentId) const
{
    static const std::unordered_map<uint32_t, int32_t> EmptyHistory;
    const auto continentIt = m_historyEventTimesByContinent.find(continentId);
    return continentIt != m_historyEventTimesByContinent.end() ? continentIt->second : EmptyHistory;
}

void CampaignState::recordHistoryEvent(uint32_t continentId, uint32_t historyId, int32_t gameMinutes)
{
    if (historyId != 0)
    {
        m_historyEventTimesByContinent[continentId].try_emplace(historyId, gameMinutes);
    }
}

void CampaignState::clearHistoryEvent(uint32_t continentId, uint32_t historyId)
{
    const auto continentIt = m_historyEventTimesByContinent.find(continentId);

    if (continentIt != m_historyEventTimesByContinent.end())
    {
        continentIt->second.erase(historyId);
    }
}

const std::vector<JournalMapNote> &CampaignState::journalMapNotes() const
{
    return m_journalMapNotes;
}

const JournalMapNote *CampaignState::findJournalMapNote(const std::string &mapFileName, uint32_t noteId) const
{
    for (const JournalMapNote &note : m_journalMapNotes)
    {
        if (note.id == noteId && note.mapFileName == mapFileName)
        {
            return &note;
        }
    }

    return nullptr;
}

void CampaignState::setJournalMapNote(const JournalMapNote &note)
{
    for (JournalMapNote &existing : m_journalMapNotes)
    {
        if (existing.id == note.id && existing.mapFileName == note.mapFileName)
        {
            existing = note;
            return;
        }
    }

    m_journalMapNotes.push_back(note);
}

bool CampaignState::removeJournalMapNote(const std::string &mapFileName, uint32_t noteId)
{
    const auto note = std::find_if(m_journalMapNotes.begin(), m_journalMapNotes.end(),
        [&mapFileName, noteId](const JournalMapNote &existing)
        {
            return existing.id == noteId && existing.mapFileName == mapFileName;
        });

    if (note == m_journalMapNotes.end())
    {
        return false;
    }

    m_journalMapNotes.erase(note);
    return true;
}

int32_t CampaignState::eventVariableValue(uint16_t variableId) const
{
    const auto iterator = m_eventVariables.find(variableId);
    return iterator != m_eventVariables.end() ? iterator->second : 0;
}

void CampaignState::setEventVariableValue(uint16_t variableId, int32_t value)
{
    if (value == 0)
    {
        m_eventVariables.erase(variableId);
        return;
    }

    m_eventVariables[variableId] = value;
}

void CampaignState::addEventVariableValue(uint16_t variableId, int32_t value)
{
    if (value == 0)
    {
        return;
    }

    setEventVariableValue(variableId, eventVariableValue(variableId) + value);
}

void CampaignState::subtractEventVariableValue(uint16_t variableId, int32_t value)
{
    if (value == 0)
    {
        return;
    }

    setEventVariableValue(variableId, eventVariableValue(variableId) - value);
}

void CampaignState::applyNpcStateTo(EventRuntimeState &runtimeState) const
{
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

    runtimeState.unavailableNpcIds = m_unavailableNpcIds;
}

void CampaignState::setNpcTopicOverride(uint32_t npcId, uint32_t topicSlotIndex, uint32_t topicId)
{
    m_npcTopicOverrides[npcId][topicSlotIndex] = topicId;
}

void CampaignState::setNpcGroupNews(uint32_t groupId, uint32_t newsId)
{
    m_npcGroupNews[groupId] = newsId;
}

void CampaignState::setNpcGreetingOverride(uint32_t npcId, uint32_t greetingId)
{
    m_npcGreetingOverrides[npcId] = greetingId;
    m_npcGreetingDisplayCounts[npcId] = 0;
}

void CampaignState::setNpcHouseOverride(uint32_t npcId, uint32_t houseId)
{
    m_npcHouseOverrides[npcId] = houseId;
}

void CampaignState::clearNpcHouseOverride(uint32_t npcId)
{
    m_npcHouseOverrides.erase(npcId);
}

void CampaignState::setNpcItemOverride(uint32_t npcId, uint32_t itemId)
{
    m_npcItemOverrides[npcId] = itemId;
}

void CampaignState::setNpcUnavailable(uint32_t npcId, bool unavailable)
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

const std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> &CampaignState::npcTopicOverrides() const
{
    return m_npcTopicOverrides;
}

const std::unordered_map<uint32_t, uint32_t> &CampaignState::npcHouseOverrides() const
{
    return m_npcHouseOverrides;
}

const std::unordered_set<uint32_t> &CampaignState::unavailableNpcIds() const
{
    return m_unavailableNpcIds;
}

int32_t CampaignState::continentReputation(uint32_t continentId) const
{
    const std::unordered_map<uint32_t, int32_t>::const_iterator it = m_continentReputations.find(continentId);
    return it != m_continentReputations.end() ? it->second : 0;
}

void CampaignState::setContinentReputation(uint32_t continentId, int32_t value)
{
    if (continentId == 0)
    {
        return;
    }

    m_continentReputations[continentId] = clampReputation(value);
}

uint32_t CampaignState::houseStockSeed() const
{
    return m_houseStockSeed;
}

CampaignState::HouseStockState *CampaignState::houseStockState(uint32_t houseId)
{
    const std::unordered_map<uint32_t, HouseStockState>::iterator stateIt = m_houseStockStates.find(houseId);
    return stateIt != m_houseStockStates.end() ? &stateIt->second : nullptr;
}

const CampaignState::HouseStockState *CampaignState::houseStockState(uint32_t houseId) const
{
    const std::unordered_map<uint32_t, HouseStockState>::const_iterator stateIt = m_houseStockStates.find(houseId);
    return stateIt != m_houseStockStates.end() ? &stateIt->second : nullptr;
}

CampaignState::HouseStockState &CampaignState::ensureHouseStockState(uint32_t houseId)
{
    HouseStockState &state = m_houseStockStates[houseId];
    state.houseId = houseId;
    return state;
}

void CampaignState::clearHouseStockStates()
{
    m_houseStockStates.clear();
}

const std::vector<InventoryItem> &CampaignState::questPouch() const
{
    return m_questPouch;
}

std::vector<InventoryItem> &CampaignState::questPouch()
{
    return m_questPouch;
}

bool CampaignState::questPouchShared() const
{
    return m_questPouchShared;
}

void CampaignState::setQuestPouchShared(bool shared)
{
    m_questPouchShared = shared;
}

bool CampaignState::hasFoundArtifactItem(uint32_t itemId) const
{
    return itemId != 0 && m_foundArtifactItems.contains(itemId);
}

void CampaignState::markArtifactItemFound(uint32_t itemId)
{
    if (itemId != 0)
    {
        m_foundArtifactItems.insert(itemId);
    }
}

void CampaignState::clearFoundArtifactItems()
{
    m_foundArtifactItems.clear();
}

bool CampaignState::hasArcomageWinAt(uint32_t houseId) const
{
    return houseId != 0 && m_arcomageWonHouseIds.contains(houseId);
}

bool CampaignState::markArcomageWinAt(uint32_t houseId)
{
    return houseId != 0 && m_arcomageWonHouseIds.insert(houseId).second;
}

const std::unordered_set<uint32_t> &CampaignState::arcomageWonHouseIds() const
{
    return m_arcomageWonHouseIds;
}

const std::vector<WorldCompletionRecord> &CampaignState::worldCompletions() const
{
    return m_worldCompletions;
}

const WorldCompletionRecord *CampaignState::findWorldCompletion(const std::string &certificateId) const
{
    for (const WorldCompletionRecord &record : m_worldCompletions)
    {
        if (record.certificateId == certificateId)
        {
            return &record;
        }
    }

    return nullptr;
}

void CampaignState::addWorldCompletion(const WorldCompletionRecord &record)
{
    if (findWorldCompletion(record.certificateId) == nullptr)
    {
        m_worldCompletions.push_back(record);
    }
}

bool CampaignState::worldCompletionsUntracked() const
{
    return m_worldCompletionsUntracked;
}

void CampaignState::clearWorldCompletionsUntracked()
{
    m_worldCompletionsUntracked = false;
}
}
