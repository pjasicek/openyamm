#include "game/rules/maw/MawGameState.h"

#include "game/rules/maw/MawExperienceCurve.h"

namespace OpenYAMM::Game
{
int MawDimensionRun::affixCount() const
{
    int count = 0;

    for (uint8_t affix : affixes)
    {
        count += affix != 0 ? 1 : 0;
    }

    return count;
}

std::optional<size_t> MawGameState::continentIndex(uint32_t continentId)
{
    switch (continentId)
    {
        case 1:
        case 2:
        case 3:
            return continentId - 1;
        case 5:
            return 3;
        default:
            return std::nullopt;
    }
}

void MawGameState::addBankedExperience(double experience, uint32_t continentId)
{
    bankedExperience += experience;
    const double level = mawLevelForExperience(bankedExperience);
    // Experience earned off the four continents (no map) goes to Jadame's bank, the map table's default continent.
    continentLevels[continentIndex(continentId).value_or(0)] += level - bankedLevel;
    bankedLevel = level;
}

double MawGameState::totalLevel() const
{
    double total = 0;

    for (double level : continentLevels)
    {
        total += level;
    }

    return total;
}

double MawGameState::levelOn(uint32_t continentId) const
{
    const std::optional<size_t> index = continentIndex(continentId);
    return index ? continentLevels[*index] : 0;
}

double MawGameState::levelOutside(uint32_t continentId) const
{
    return totalLevel() - levelOn(continentId);
}

int MawGameState::resetCount(const std::string &mapFileName) const
{
    const auto it = mapResetCounts.find(mapFileName);
    return it != mapResetCounts.end() ? it->second : 0;
}
}
