#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
enum class AwardStateKind : uint8_t
{
    CharacterAward = 0,
    PartyQBit,
    PartyAutonote,
    // The party has won Arcomage at the house with this id.
    PartyArcomageWin,
};

struct AwardDisplayEntry
{
    std::string key;
    AwardStateKind stateKind = AwardStateKind::CharacterAward;
    uint32_t stateId = 0;
    std::string text;
    int priority = 0;
};

class AwardTable
{
  public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &awardRows,
                      const std::vector<std::vector<std::string>> &aliasRows);
    // The active world's wording of engine award rows (a world.yml `award_texts` override contribution, rows as in
    // awards.txt: id, text, optional sort): the loaded texts and sorts first come back, then each row replaces its
    // award's. Rows naming no loaded award stop it (false, the reason in errorMessage); no rows restore the loaded table.
    bool applyTextOverrides(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage);
    const std::vector<AwardDisplayEntry> &entries() const;

  private:
    std::vector<AwardDisplayEntry> m_entries;
    // Each entry's text and sort as loaded, so a world switch can undo another world's overrides.
    std::vector<std::pair<std::string, int>> m_loadedTexts;
};
} // namespace OpenYAMM::Game
