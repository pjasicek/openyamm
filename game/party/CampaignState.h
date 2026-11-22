#pragma once

#include "game/party/InventoryItem.h"

#include <cstdint>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
struct EventRuntimeState;

// A pin on the journal map of mapFileName (lowercase); ids are unique within one map.
struct JournalMapNote
{
    uint32_t id = 0;
    int32_t x = 0;
    int32_t y = 0;
    std::string mapFileName;
    std::string text;
    // Teacher pins without an autonote of their own also appear in the journal's trainer notes.
    bool listedWithTrainerNotes = false;
    // The player's own note (right click on the journal map): editable and removable there, ids from
    // PersonalJournalMapNoteIdBase.
    bool personal = false;
};

// Personal journal map notes take ids from here up, clear of event and quest pins.
constexpr uint32_t PersonalJournalMapNoteIdBase = 1000000;

// A story the party finished (world.yml completion; "grand" for every world of the grand certificate), recorded once
// when its certificate is given.
struct WorldCompletionRecord
{
    std::string certificateId;
    float gameMinutes = 0.0f;
    uint64_t score = 0;
    // Real time of the completion, seconds since 1970.
    int64_t completedAtUnixSeconds = 0;
    // False for a story finished before the game kept these records: no time, score or certificate.
    bool timed = true;
};

// What belongs to the game being played and not to the adventurers playing it: quest progress, the journal, what
// events and NPCs remember, shop stock, reputation, the artifacts found and the stories finished. A party reaches it
// through Party::campaign(). It is kept apart from the party so that several parties can play in one game
// (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "Who owns what"; the design calls it the world's record,
// and the code says campaign because "world" already names a content package such as MM8).
class CampaignState
{
public:
    struct HouseStockState
    {
        uint32_t houseId = 0;
        float nextRefreshGameMinutes = 0.0f;
        uint32_t refreshSequence = 0;
        uint32_t generationVersion = 0;
        std::vector<InventoryItem> standardStock;
        std::vector<InventoryItem> specialStock;
        // A guild's shelves, one per school it teaches (HouseServiceRuntime::spellbookShelfSchools), one after another.
        std::vector<InventoryItem> spellbookStock;
    };

    struct Snapshot
    {
        uint32_t houseStockSeed = 0;
        std::unordered_set<uint32_t> foundArtifactItems;
        std::unordered_set<uint32_t> arcomageWonHouseIds;
        std::vector<WorldCompletionRecord> worldCompletions;
        // A save from before the completion records: the stories it already finished get untimed records, no
        // certificate (CompletionCertificates::recordNewCompletions).
        bool worldCompletionsUntracked = false;
        std::vector<HouseStockState> houseStockStates;
        std::unordered_map<uint32_t, int32_t> continentReputations;
        std::unordered_set<uint32_t> questBits;
        std::unordered_set<uint32_t> autonotes;
        // History entry id -> game minute it was recorded, per history continent.
        std::unordered_map<uint32_t, std::unordered_map<uint32_t, int32_t>> historyEventTimesByContinent;
        std::vector<JournalMapNote> journalMapNotes;
        std::unordered_map<uint16_t, int32_t> eventVariables;
        std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> npcTopicOverrides;
        std::unordered_map<uint32_t, uint32_t> npcGroupNews;
        std::unordered_map<uint32_t, uint32_t> npcGreetingOverrides;
        std::unordered_map<uint32_t, uint32_t> npcGreetingDisplayCounts;
        std::unordered_map<uint32_t, uint32_t> npcHouseOverrides;
        std::unordered_map<uint32_t, uint32_t> npcItemOverrides;
        std::unordered_set<uint32_t> unavailableNpcIds;
        // Saved where the party's pouches are, as the third of them (SaveGame.cpp, readPouches).
        std::vector<InventoryItem> questPouch;
    };

    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    // What a new party starts from: no progress, a new shop stock seed. The stories already finished and the Arcomage
    // taverns already won stay, as they did when the party kept them.
    void resetForNewParty();

    bool hasQuestBit(uint32_t questBitId) const;
    void setQuestBit(uint32_t questBitId, bool value);
    // Counts up with every quest bit that changes and every restore or reset; dialogue eligibility caches read it
    // through Party::dialogueEligibilityRevision.
    uint64_t questRevision() const;
    bool hasAutonote(uint32_t autonoteId) const;
    void setAutonote(uint32_t autonoteId, bool value);
    const std::unordered_map<uint32_t, int32_t> &historyEventTimes(uint32_t continentId) const;
    void recordHistoryEvent(uint32_t continentId, uint32_t historyId, int32_t gameMinutes);
    void clearHistoryEvent(uint32_t continentId, uint32_t historyId);
    const std::vector<JournalMapNote> &journalMapNotes() const;
    const JournalMapNote *findJournalMapNote(const std::string &mapFileName, uint32_t noteId) const;
    // Adds the note, or replaces the one with the same map and id.
    void setJournalMapNote(const JournalMapNote &note);
    // Removes the note with this map and id; false when there is none.
    bool removeJournalMapNote(const std::string &mapFileName, uint32_t noteId);

    int32_t eventVariableValue(uint16_t variableId) const;
    void setEventVariableValue(uint16_t variableId, int32_t value);
    void addEventVariableValue(uint16_t variableId, int32_t value);
    void subtractEventVariableValue(uint16_t variableId, int32_t value);

    // Copies what the game remembers of NPCs (topics, news, greetings, houses, items, who is away) over a map's event
    // state. The unavailable set replaces the map's: a map's saved state can keep an NPC unavailable after the party
    // let them go elsewhere (Sir Charles Quixote, hidden from his residence after the Crusader promotion in
    // Wromthrax's cave).
    void applyNpcStateTo(EventRuntimeState &runtimeState) const;
    void setNpcTopicOverride(uint32_t npcId, uint32_t topicSlotIndex, uint32_t topicId);
    void setNpcGroupNews(uint32_t groupId, uint32_t newsId);
    void setNpcGreetingOverride(uint32_t npcId, uint32_t greetingId);
    void setNpcHouseOverride(uint32_t npcId, uint32_t houseId);
    void clearNpcHouseOverride(uint32_t npcId);
    void setNpcItemOverride(uint32_t npcId, uint32_t itemId);
    void setNpcUnavailable(uint32_t npcId, bool unavailable);
    const std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> &npcTopicOverrides() const;
    const std::unordered_map<uint32_t, uint32_t> &npcHouseOverrides() const;
    const std::unordered_set<uint32_t> &unavailableNpcIds() const;

    int32_t continentReputation(uint32_t continentId) const;
    void setContinentReputation(uint32_t continentId, int32_t value);

    uint32_t houseStockSeed() const;
    HouseStockState *houseStockState(uint32_t houseId);
    const HouseStockState *houseStockState(uint32_t houseId) const;
    HouseStockState &ensureHouseStockState(uint32_t houseId);
    void clearHouseStockStates();

    // The quest pouch (ItemPouch::Quest, in rulesets with pouches): quest items lie here and not with a party, so every
    // party of the game sees them and an event takes one once. Party::pouchItems reaches it, each item at its cell of
    // the pouch's grid.
    const std::vector<InventoryItem> &questPouch() const;
    std::vector<InventoryItem> &questPouch();
    // A game of several players (a co-op session): quest items are the world's under any ruleset, so every party of
    // the campaign keeps them in the quest pouch, also where the ruleset has no pouches (Party::hasPouch). The
    // session sets it; it is no part of a save.
    bool questPouchShared() const;
    void setQuestPouchShared(bool shared);

    bool hasFoundArtifactItem(uint32_t itemId) const;
    void markArtifactItemFound(uint32_t itemId);
    void clearFoundArtifactItems();

    bool hasArcomageWinAt(uint32_t houseId) const;
    // Notes a win at the tavern; true when it is the first there.
    bool markArcomageWinAt(uint32_t houseId);
    const std::unordered_set<uint32_t> &arcomageWonHouseIds() const;

    const std::vector<WorldCompletionRecord> &worldCompletions() const;
    const WorldCompletionRecord *findWorldCompletion(const std::string &certificateId) const;
    void addWorldCompletion(const WorldCompletionRecord &record);
    bool worldCompletionsUntracked() const;
    void clearWorldCompletionsUntracked();

private:
    uint32_t m_houseStockSeed = 0;
    std::unordered_set<uint32_t> m_foundArtifactItems;
    std::unordered_set<uint32_t> m_arcomageWonHouseIds;
    std::vector<WorldCompletionRecord> m_worldCompletions;
    bool m_worldCompletionsUntracked = false;
    std::unordered_map<uint32_t, int32_t> m_continentReputations;
    std::unordered_set<uint32_t> m_questBits;
    uint64_t m_questRevision = 0;
    std::unordered_set<uint32_t> m_autonotes;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, int32_t>> m_historyEventTimesByContinent;
    std::vector<JournalMapNote> m_journalMapNotes;
    std::unordered_map<uint32_t, HouseStockState> m_houseStockStates;
    std::unordered_map<uint16_t, int32_t> m_eventVariables;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> m_npcTopicOverrides;
    std::unordered_map<uint32_t, uint32_t> m_npcGroupNews;
    std::unordered_map<uint32_t, uint32_t> m_npcGreetingOverrides;
    std::unordered_map<uint32_t, uint32_t> m_npcGreetingDisplayCounts;
    std::unordered_map<uint32_t, uint32_t> m_npcHouseOverrides;
    std::unordered_map<uint32_t, uint32_t> m_npcItemOverrides;
    std::unordered_set<uint32_t> m_unavailableNpcIds;
    std::vector<InventoryItem> m_questPouch;
    bool m_questPouchShared = false;
};
}
