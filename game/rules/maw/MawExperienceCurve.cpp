#include "game/rules/maw/MawExperienceCurve.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MaxTableLevel = 2000;
}

MawExperienceCurve::MawExperienceCurve(double surchargePerLevel)
    : m_surchargePerLevel(surchargePerLevel)
    , m_table(MaxTableLevel + 1, 0.0)
{
    for (int level = 2; level <= MaxTableLevel; ++level)
    {
        m_table[size_t(level)] = m_table[size_t(level - 1)] + step(level - 1);
    }
}

double MawExperienceCurve::step(double level) const
{
    return 1000 * level * std::max(1 + (level - 100) * m_surchargePerLevel, 1.0);
}

double MawExperienceCurve::experienceForLevel(double level) const
{
    if (level <= 1)
    {
        return 0;
    }

    if (level >= MaxTableLevel)
    {
        return m_table[MaxTableLevel] + (level - MaxTableLevel) * step(MaxTableLevel);
    }

    const double whole = std::floor(level);
    return m_table[size_t(whole)] + (level - whole) * step(whole);
}

double MawExperienceCurve::levelForExperience(double experience) const
{
    if (experience <= 0)
    {
        return 1;
    }

    if (experience >= m_table[MaxTableLevel])
    {
        return MaxTableLevel + (experience - m_table[MaxTableLevel]) / step(MaxTableLevel);
    }

    // The highest level whose requirement does not exceed the experience.
    const auto above = std::upper_bound(m_table.begin() + 1, m_table.end(), experience);
    const int level = int(above - m_table.begin()) - 1;
    return level + (experience - m_table[size_t(level)]) / step(level);
}

double MawExperienceCurve::surchargePerLevel() const
{
    return m_surchargePerLevel;
}

const MawExperienceCurve &mawExperienceCurve()
{
    static const MawExperienceCurve Curve(MawExperienceSurcharge);
    return Curve;
}

double mawExperienceForLevel(double level)
{
    return mawExperienceCurve().experienceForLevel(level);
}

double mawLevelForExperience(double experience)
{
    return mawExperienceCurve().levelForExperience(experience);
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
