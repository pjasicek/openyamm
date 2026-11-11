#pragma once

#include "game/mm9/Mm9RudeDialogue.h"
#include "game/gameplay/TrainerDirectory.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9SkillTrainerService
{
    std::string canonicalId;
    uint32_t rudeId = 0;
    size_t rudeRowIndex = 0;
    size_t sourceLine = 0;
    int32_t choiceSlot = 0;
    std::string mm9Skill;
    Mm9RudeSkillTrainerTopic topic;
    uint32_t requiredSkillRank = 0;
    uint32_t requiredGold = 0;
    std::vector<int32_t> requiredRawKeys;
    std::vector<int32_t> forbiddenRawKeys;
    std::string expectedRegion;
    std::vector<std::string> sourceDisplayNames;
    std::string npc998Hint;
    std::string actorOwnership;
    std::vector<std::string> actorSources;
    std::string sourceRude;
    std::string provenance;
};

class Mm9SkillTrainerTable
{
public:
    void clear();
    bool loadFromRows(
        const std::vector<std::vector<std::string>> &rows,
        const Mm9RudeDialogueTable &rudeDialogueTable);
    const Mm9SkillTrainerService *find(uint32_t rudeId, size_t rudeRowIndex) const;
    const Mm9SkillTrainerService *findByCanonicalId(const std::string &canonicalId) const;
    const std::vector<Mm9SkillTrainerService> &entries() const;
    const std::vector<std::string> &errors() const;

private:
    void addError(size_t rowNumber, const std::string &message);

    std::vector<Mm9SkillTrainerService> m_entries;
    std::unordered_map<std::string, size_t> m_entryIndexByCanonicalId;
    std::unordered_map<uint64_t, size_t> m_entryIndexByRudeRow;
    std::vector<std::string> m_errors;
};
class MapStats;
bool buildMm9JournalTeachers(const std::vector<std::vector<std::string>> &places,
    const Mm9SkillTrainerTable &lessons, const Mm9RudeDialogueTable &dialogue, const MapStats &maps,
    const std::string &mapCatalog, std::vector<TrainerEntry> &entries, std::string &error);

}
