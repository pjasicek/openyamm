#include "game/rules/maw/MawMonsterRules.h"
#include "engine/Localization.h"

#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/party/Party.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/MapStats.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <string>
#include <tuple>

namespace OpenYAMM::Game
{
namespace
{
std::string lowercaseName(const std::string &value)
{
    std::string result = value;
    std::transform(result.begin(), result.end(), result.begin(), [](unsigned char c) { return char(std::tolower(c)); });
    return result;
}

int gameDay(float gameMinutes)
{
    return int(std::floor(std::max(0.0f, gameMinutes) / (24.0f * 60.0f))) + 1;
}
}

bool MawMonsterRules::hasProgressTab() const
{
    return true;
}

std::optional<RulesetProgressSummary> MawMonsterRules::progressSummary(const RulesetProgressQuery &query) const
{
    const MapStats *pMapTable = query.pMapTable != nullptr ? query.pMapTable : m_rules.mapTable();

    if (pMapTable == nullptr || query.pMonsterTable == nullptr)
    {
        return std::nullopt;
    }

    const RulesetOptions &options = m_rules.options();
    const MawGameState &state = m_rules.state();
    RulesetProgressSummary summary;
    summary.difficulty = std::string(rulesetDifficultyName(options.difficulty));
    summary.progression = std::string(rulesetProgressionName(options.progression));
    summary.challengeMode = std::string(rulesetChallengeModeName(options.challengeMode));
    summary.totalLevel = int(std::lround(state.totalLevel()));

    if (options.challengeMode == RulesetChallengeMode::BeyondMadness)
    {
        summary.deaths = m_rules.madnessLedger().deaths();
    }

    const std::string currentMap = query.currentMap ? lowercaseName(query.currentMap->mapFileName) : std::string();
    const int today = gameDay(query.gameMinutes);

    // Enroth, Antagarich, Jadame and Chedian, as the worlds came out (map table continents 3, 2, 1 and 5). Chedian's
    // card shows only while it has maps: with MM9 installed and its maps given MAW levels.
    const std::array<std::pair<uint32_t, std::string_view>, 4> continents = {{{3, Engine::trNoop("Enroth")},
        {2, Engine::trNoop("Antagarich")}, {1, Engine::trNoop("Jadame")}, {5, Engine::trNoop("Chedian")}}};
    const std::array<const char *, 4> worlds = {"MM6", "MM7", "MM8", "MM9"};

    for (size_t continentIndex = 0; continentIndex < continents.size(); ++continentIndex)
    {
        const auto [continentId, continentName] = continents[continentIndex];
        RulesetProgressContinent continent;
        continent.name = continentName;
        continent.world = worlds[continentIndex];
        continent.levelsBanked = state.levelOn(continentId);

        for (const MapStatsEntry &map : pMapTable->getEntries())
        {
            const std::string file = lowercaseName(map.fileName);

            // The table's unused rows are named "pending" (zdtl02.blv has a MAW level but nothing leads there: OY-159).
            if (map.mergedContinentId != continentId || !m_rules.mapLevels().lists(file) || map.name == "pending")
            {
                continue;
            }

            RulesetProgressMap entry;
            entry.fileName = file;
            entry.name = map.name;
            std::tie(entry.level, entry.levelFromResets) = m_rules.mapLevelSummary(*query.pMonsterTable, map);

            // Maps without monsters of their own (the Arena, the table's unused "pending" rows) have nothing to clear.
            if (entry.level <= 0)
            {
                continue;
            }
            entry.resets = state.resetCount(file);
            entry.clearedSinceRefill = state.clearedSinceRefill.contains(file);
            entry.completedOnce = state.completedMaps.contains(file);
            entry.resetOffer = mapResetOffer(file);
            entry.current = file == currentMap;
            const auto run = state.dimensionRuns.find(file);
            entry.dimensionRun = run != state.dimensionRuns.end() && !run->second.completed;

            // This month's bounty of the map's town, not yet slain (BountyHuntRuntime's entries by map name).
            if (query.pEventState != nullptr)
            {
                const auto value = [&](const char *pField)
                {
                    const auto found = query.pEventState->namedGlobalVars.find("MMerge.BountyHunt." + map.name + pField);
                    return found != query.pEventState->namedGlobalVars.end() ? found->second : 0;
                };
                entry.bountyTarget = value(".MonsterId") > 0 && value(".Done") == 0
                    && value(".Month") == (today - 1) / 28;
            }

            const auto visit = state.mapVisits.find(file);
            std::optional<int> lastRefillDay;

            if (file == currentMap)
            {
                const MapKillProgress &progress = *query.currentMap;
                entry.slainShare = progress.countedMonsters > 0
                    ? double(progress.slainMonsters) / progress.countedMonsters : 0;
                entry.state = RulesetMapProgressState::InProgress;
                lastRefillDay = m_loadDay;
            }
            else if (visit != state.mapVisits.end())
            {
                entry.slainShare = visit->second.counted > 0
                    ? double(visit->second.slain) / visit->second.counted : 0;
                entry.state = RulesetMapProgressState::InProgress;
                lastRefillDay = visit->second.lastRefillDay;
            }
            else if (entry.completedOnce)
            {
                entry.state = RulesetMapProgressState::InProgress;
            }

            if (entry.clearedSinceRefill)
            {
                entry.state = RulesetMapProgressState::Cleared;
                entry.slainShare = 1;
            }

            const int respawnDays = mapRespawnDays(map);

            if (lastRefillDay && *lastRefillDay > 0 && respawnDays > 0)
            {
                entry.refillInDays = std::max(0, respawnDays - (today - *lastRefillDay));
            }

            continent.mapsCleared += entry.completedOnce ? 1 : 0;
            continent.maps.push_back(std::move(entry));
        }

        std::stable_sort(continent.maps.begin(), continent.maps.end(),
            [](const RulesetProgressMap &left, const RulesetProgressMap &right)
            {
                return left.level < right.level;
            });

        for (const RulesetProgressMap &map : continent.maps)
        {
            if (map.level > 0)
            {
                continent.levelLow = continent.levelLow == 0 ? map.level : std::min(continent.levelLow, map.level);
                continent.levelHigh = std::max(continent.levelHigh, map.level);
            }
        }

        if (continentId != 5 || !continent.maps.empty())
        {
            summary.continents.push_back(std::move(continent));
        }
    }

    const MawDimensionQuest &quest = state.dimensionQuest;
    summary.dimensionQuest = quest.done ? Engine::tr("done")
        : quest.tierLevel == 0 ? Engine::tr("not started")
        : Engine::tr(quest.cleared ? "level {level}, cleared"
                : quest.mapGiven   ? "level {level}, map given"
                                   : "level {level}",
            {{"level", int64_t(quest.tierLevel)}});
    summary.dimensionRunsCleared = state.dimensionRunsCleared;
    summary.currentRun = Engine::tr("none");

    for (const auto &[file, run] : state.dimensionRuns)
    {
        if (!run.completed)
        {
            const MapStatsEntry *pMap = pMapTable->findByFileName(file);
            summary.currentRun = Engine::tr("{map}, power {power}",
                {{"map", pMap != nullptr ? Engine::localize(pMap->name) : file}, {"power", int64_t(run.power)}});
            break;
        }
    }

    summary.bountiesClaimed = state.bountiesClaimed;
    summary.bountyGold = query.pParty != nullptr
        ? query.pParty->eventVariableValue(uint16_t(EvtVariable::NumBounties)) : 0;
    return summary;
}
}
