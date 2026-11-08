#include "game/gameplay/JournalArcomageRuntime.h"
#include "engine/Localization.h"

#include "game/party/Party.h"
#include "game/tables/HouseTable.h"
#include "game/tables/MapStats.h"

#include <algorithm>
#include <map>
#include <tuple>

namespace OpenYAMM::Game
{
namespace
{
std::string continentName(uint32_t continentId)
{
    switch (continentId)
    {
        case 1:
            return Engine::localize("Jadame");
        case 2:
            return Engine::localize("Antagarich");
        case 3:
            return Engine::localize("Enroth");
        default:
            return Engine::localize("Elsewhere");
    }
}

struct ArcomageTavern
{
    std::string town;
    std::string name;
    bool won = false;
    // Whether a win here counts toward Arcomage Champion (Emerald Island's tavern does not: OY-308).
    bool countsForChampion = true;
};
} // namespace

std::vector<std::string> buildArcomageTavernTexts(const HouseTable &houseTable, const MapStats &mapStats,
    const Party &party)
{
    std::map<uint32_t, std::vector<ArcomageTavern>> tavernsByContinent;

    for (const auto &[houseId, house] : houseTable.entries())
    {
        if (!house.arcomageRule)
        {
            continue;
        }

        const MapStatsEntry *pMap = mapStats.findById(house.mapId);
        ArcomageTavern tavern;
        tavern.town = pMap != nullptr ? Engine::localize(pMap->name) : std::string();
        tavern.name = Engine::localize(house.name);
        tavern.won = party.hasArcomageWinAt(houseId);
        tavern.countsForChampion = Party::arcomageTavernCountsForChampion(houseId);
        tavernsByContinent[pMap != nullptr ? pMap->mergedContinentId : 0].push_back(std::move(tavern));
    }

    std::vector<std::string> texts;

    for (auto &[continentId, taverns] : tavernsByContinent)
    {
        std::sort(taverns.begin(), taverns.end(), [](const ArcomageTavern &left, const ArcomageTavern &right)
            {
                return std::tie(left.town, left.name) < std::tie(right.town, right.name);
            });
        const size_t wonCount = size_t(std::count_if(taverns.begin(), taverns.end(),
            [](const ArcomageTavern &tavern) { return tavern.won && tavern.countsForChampion; }));
        const size_t countedCount = size_t(std::count_if(taverns.begin(), taverns.end(),
            [](const ArcomageTavern &tavern) { return tavern.countsForChampion; }));
        texts.push_back(Engine::tr("{continent}: {won} of {total} taverns won.",
                                   {{"continent", continentName(continentId)},
                                    {"won", wonCount},
                                    {"total", countedCount}}));

        for (const ArcomageTavern &tavern : taverns)
        {
            const std::string place = tavern.town.empty() ? tavern.name : tavern.name + ", " + tavern.town;

            if (tavern.countsForChampion)
            {
                texts.push_back(tavern.won ? Engine::tr("{place}: won", {{"place", place}})
                                           : Engine::tr("{place}: not won yet", {{"place", place}}));
            }
            else
            {
                texts.push_back(tavern.won
                        ? Engine::tr("{place}: won (not needed for Champion)", {{"place", place}})
                        : Engine::tr("{place}: not won yet (not needed for Champion)", {{"place", place}}));
            }
        }
    }

    return texts;
}
} // namespace OpenYAMM::Game
