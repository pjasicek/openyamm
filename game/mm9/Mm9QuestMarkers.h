#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
class ClassSkillTable;
class JournalQuestTable;
class Mm9RudeDialogueTable;
class Mm9SkillTrainerTable;
class NpcDialogTable;
class Party;

// One marker per actor, in priority order: a higher state replaces a lower one.
enum class Mm9QuestMarkerState : uint8_t
{
    None = 0,
    InProgress,
    // A skill trainer with a lesson some party member can take now, gold aside.
    Trainer,
    Available,
    Ready,
};

// The tables a trainer marker needs; without them the resolver gives quest markers only.
struct Mm9TrainerMarkerTables
{
    const Mm9SkillTrainerTable *pSkillTrainerTable = nullptr;
    const ClassSkillTable *pClassSkillTable = nullptr;
    const NpcDialogTable *pNpcDialogTable = nullptr;
};

struct Mm9QuestActorIdentity
{
    std::string mapId;
    uint32_t sourceObjectIndex = 0;
    uint32_t rudeId = 0;
    bool interactable = true;
};

struct Mm9QuestInteractionBinding
{
    std::string mapId;
    uint32_t sourceObjectIndex = 0;
};

// A marker state of a journal-less MM9 quest (source_kind keys): it holds while the party has every required QBit and
// none of the forbidden ones; a state with present false never holds.
struct Mm9QuestKeyState
{
    bool present = false;
    std::vector<uint32_t> requiredQBits;
    std::vector<uint32_t> forbiddenQBits;
};

struct Mm9QuestInteraction
{
    std::string id;
    uint32_t rudeId = 0;
    size_t rudeRowIndex = 0;
    bool scrPredicate = false;
    bool offer = false;
    bool handoff = false;
    std::vector<uint32_t> requiredQBits;
    std::vector<uint32_t> forbiddenQBits;
    std::vector<uint32_t> anyRequiredQBits;
    int minimumGold = 0;
    std::vector<uint32_t> activatedJournalEntries;
    std::vector<uint32_t> completedJournalEntries;
    // source_kind keys: a deal MM9 keeps in quest keys only, with no journal entry (Drangheim Prison's cook): its
    // marker is the first of ready, in progress and available whose keys hold.
    bool keyStates = false;
    Mm9QuestKeyState availableKeys;
    Mm9QuestKeyState inProgressKeys;
    Mm9QuestKeyState readyKeys;
    std::vector<Mm9QuestInteractionBinding> bindings;
};

class Mm9QuestInteractionTable
{
  public:
    bool load(const Engine::AssetFileSystem &assetFileSystem);
    bool loadText(const std::string &sourceName, const std::string &text);
    void clear();

    const std::vector<Mm9QuestInteraction> &interactions() const;
    const std::vector<std::string> &errors() const;

  private:
    std::vector<Mm9QuestInteraction> m_interactions;
    std::vector<std::string> m_errors;
};

class Mm9QuestMarkerResolver
{
  public:
    Mm9QuestMarkerState markerFor(const Mm9QuestActorIdentity &actor, const Party &party,
                                  const JournalQuestTable &journalQuestTable,
                                  const Mm9RudeDialogueTable &rudeDialogueTable,
                                  const Mm9QuestInteractionTable &interactionTable,
                                  const Mm9TrainerMarkerTables *pTrainerTables = nullptr) const;
};

struct Mm9QuestEligibilityStamp
{
    uint64_t partyRevision = 0;
    uint64_t mapRevision = 0;

    bool operator==(const Mm9QuestEligibilityStamp &) const = default;
};

struct Mm9LoadedQuestMarkerActor
{
    uint32_t actorId = 0;
    Mm9QuestActorIdentity identity;
};

class Mm9LoadedLocationQuestMarkerCache
{
  public:
    void loadLocation(bool mm9Active, const std::vector<Mm9LoadedQuestMarkerActor> &actors,
                      Mm9QuestEligibilityStamp stamp, const Party &party, const JournalQuestTable &journalQuestTable,
                      const Mm9RudeDialogueTable &rudeDialogueTable, const Mm9QuestInteractionTable &interactionTable,
                      const Mm9TrainerMarkerTables *pTrainerTables = nullptr);
    bool update(const std::vector<Mm9LoadedQuestMarkerActor> &actors, Mm9QuestEligibilityStamp stamp,
                const Party &party, const JournalQuestTable &journalQuestTable,
                const Mm9RudeDialogueTable &rudeDialogueTable, const Mm9QuestInteractionTable &interactionTable,
                const Mm9TrainerMarkerTables *pTrainerTables = nullptr);
    void clear();

    Mm9QuestMarkerState markerForActor(uint32_t actorId) const;
    bool active() const;
    uint64_t rebuildCount() const;

  private:
    void rebuild(const std::vector<Mm9LoadedQuestMarkerActor> &actors, const Party &party,
                 const JournalQuestTable &journalQuestTable, const Mm9RudeDialogueTable &rudeDialogueTable,
                 const Mm9QuestInteractionTable &interactionTable, const Mm9TrainerMarkerTables *pTrainerTables);

    bool m_active = false;
    Mm9QuestEligibilityStamp m_evaluatedStamp;
    std::unordered_map<uint32_t, Mm9QuestMarkerState> m_markers;
    uint64_t m_rebuildCount = 0;
};
} // namespace OpenYAMM::Game
