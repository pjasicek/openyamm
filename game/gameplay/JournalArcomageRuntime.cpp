#include "game/gameplay/JournalArcomageRuntime.h"
#include "engine/Localization.h"

#include "game/gameplay/TrainerDirectory.h"
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
    const TrainerDirectory *pDirectory, const Party &party)
{
    // By the continent's card rank (the new-game cards' order); taverns of no card's continent last, as Elsewhere.
    static const std::vector<TrainerContinent> NoContinents;
    const std::vector<TrainerContinent> &continents = pDirectory != nullptr ? pDirectory->continents() : NoContinents;
    const auto rankOf = [&](uint32_t continentId)
    {
        const std::optional<uint32_t> card =
            pDirectory != nullptr ? pDirectory->cardContinent(continentId) : std::nullopt;
        size_t rank = 0;

        while (rank < continents.size() && (!card || continents[rank].id != *card))
        {
            ++rank;
        }

        return rank;
    };
    std::map<size_t, std::vector<ArcomageTavern>> tavernsByContinent;

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
        tavern.won = party.campaign().hasArcomageWinAt(houseId);
        tavern.countsForChampion = Party::arcomageTavernCountsForChampion(houseId);
        tavernsByContinent[pMap != nullptr ? rankOf(pMap->mergedContinentId) : continents.size()].push_back(
            std::move(tavern));
    }

    std::vector<std::string> texts;

    for (auto &[rank, taverns] : tavernsByContinent)
    {
        const std::string continentName =
            Engine::localize(rank < continents.size() ? continents[rank].name : std::string("Elsewhere"));
        std::sort(taverns.begin(), taverns.end(), [](const ArcomageTavern &left, const ArcomageTavern &right)
            {
                return std::tie(left.town, left.name) < std::tie(right.town, right.name);
            });
        const size_t wonCount = size_t(std::count_if(taverns.begin(), taverns.end(),
            [](const ArcomageTavern &tavern) { return tavern.won && tavern.countsForChampion; }));
        const size_t countedCount = size_t(std::count_if(taverns.begin(), taverns.end(),
            [](const ArcomageTavern &tavern) { return tavern.countsForChampion; }));
        texts.push_back(Engine::tr("{continent}: {won} of {total} taverns won.",
                                   {{"continent", continentName},
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
