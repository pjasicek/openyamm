#include "game/gameplay/JournalQuestRuntime.h"

#include "engine/Localization.h"

#include "game/party/Party.h"
#include "game/tables/JournalQuestTable.h"

namespace OpenYAMM::Game
{
std::vector<std::string> buildCurrentQuestTexts(const JournalQuestTable &questTable, const Party &party,
    std::string_view owner)
{
    std::vector<std::string> questTexts;

    for (const JournalQuestEntry &entry : questTable.entries())
    {
        if ((owner.empty() || entry.owner == owner || (owner == "Shared" && entry.owner.empty()))
            && questTable.isVisible(entry, party))
        {
            // Shown in the journal: the interface language's text of quests.txt.
            questTexts.push_back(Engine::localize(entry.text));
        }
    }

    return questTexts;
}
} // namespace OpenYAMM::Game
