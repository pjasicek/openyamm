#include "game/gameplay/JournalQuestRuntime.h"

#include "game/party/Party.h"
#include "game/tables/JournalQuestTable.h"

namespace OpenYAMM::Game
{
std::vector<std::string> buildCurrentQuestTexts(const JournalQuestTable &questTable, const Party &party)
{
    std::vector<std::string> questTexts;

    for (const JournalQuestEntry &entry : questTable.entries())
    {
        if (party.hasQuestBit(entry.qbitId))
        {
            questTexts.push_back(entry.text);
        }
    }

    return questTexts;
}
} // namespace OpenYAMM::Game
