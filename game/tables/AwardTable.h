#pragma once

#include <cstdint>
#include <string>
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
    const std::vector<AwardDisplayEntry> &entries() const;

  private:
    std::vector<AwardDisplayEntry> m_entries;
};
} // namespace OpenYAMM::Game
