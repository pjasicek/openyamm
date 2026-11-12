#include "game/rules/maw/MawExperienceCurve.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MaxTableLevel = 2000;

// Experience to go from `level` to the next.
double experienceStep(double level)
{
    return 1000 * level * std::max(1 + (level - 100) * 0.005, 1.0);
}

const std::array<double, MaxTableLevel + 1> &experienceTable()
{
    static const std::array<double, MaxTableLevel + 1> Table = []
    {
        std::array<double, MaxTableLevel + 1> table = {};

        for (int level = 2; level <= MaxTableLevel; ++level)
        {
            table[size_t(level)] = table[size_t(level - 1)] + experienceStep(level - 1);
        }

        return table;
    }();
    return Table;
}
}

double mawExperienceForLevel(double level)
{
    if (level <= 1)
    {
        return 0;
    }

    const std::array<double, MaxTableLevel + 1> &table = experienceTable();

    if (level >= MaxTableLevel)
    {
        return table[MaxTableLevel] + (level - MaxTableLevel) * experienceStep(MaxTableLevel);
    }

    const double whole = std::floor(level);
    return table[size_t(whole)] + (level - whole) * experienceStep(whole);
}

double mawLevelForExperience(double experience)
{
    if (experience <= 0)
    {
        return 1;
    }

    const std::array<double, MaxTableLevel + 1> &table = experienceTable();

    if (experience >= table[MaxTableLevel])
    {
        return MaxTableLevel + (experience - table[MaxTableLevel]) / experienceStep(MaxTableLevel);
    }

    // The highest level whose requirement does not exceed the experience.
    const auto above = std::upper_bound(table.begin() + 1, table.end(), experience);
    const int level = int(above - table.begin()) - 1;
    return level + (experience - table[size_t(level)]) / experienceStep(level);
}

double mawBolsteredLevel(double floorLevel, double levels)
{
    floorLevel = std::max(floorLevel, 0.0);

    if (levels <= 0)
    {
        return floorLevel + levels;
    }

    const double top = floorLevel + levels;
    const double vanillaClimb = 500 * (top * (top - 1) - floorLevel * (floorLevel - 1));
    return mawLevelForExperience(mawExperienceForLevel(floorLevel) + vanillaClimb);
}
}
