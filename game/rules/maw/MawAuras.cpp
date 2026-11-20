#include "game/rules/maw/MawAuras.h"

#include "game/rules/maw/MawCombatFormulas.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<MawAura, 28> Auras = {{
    {3, 60}, {14, 60}, {25, 60}, {36, 60}, {58, 60}, {69, 60},
    {4, 90}, {5, 120}, {8, 40}, {17, 75}, {28, 150}, {38, 75}, {46, 75}, {47, 75}, {50, 120}, {51, 120},
    {56, 120}, {71, 120}, {73, 75}, {75, 180}, {83, 200, false, 75}, {85, 150, false, 75}, {86, 300, false, 75},
    {91, 150}, {95, 10},
    {1, 5, true}, {12, 5, true}, {27, 20, true},
}};
}

const MawAura *mawAura(uint32_t spellId)
{
    const auto it = std::find_if(
        Auras.begin(),
        Auras.end(),
        [spellId](const MawAura &aura)
        {
            return aura.spellId == spellId;
        });
    return it != Auras.end() ? &*it : nullptr;
}

std::string mawSpellSchoolSkill(uint32_t spellId)
{
    static constexpr std::array<const char *, 9> Schools = {
        "FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic", "BodyMagic", "LightMagic",
        "DarkMagic",
    };
    return spellId >= 1 && spellId <= 99 ? Schools[(spellId - 1) / 11] : std::string();
}

double mawAuraReservedPercent(double cost, double classSpellFactor, int enlightenmentMastery)
{
    const double divisor = classSpellFactor + enlightenmentMastery / 2.0;
    return divisor > 0 ? cost / divisor : cost;
}

int mawUtilityAuraReservation(double cost, int enlightenmentMastery)
{
    return int(std::floor(cost * (1 - enlightenmentMastery / 10.0) + 0.5));
}

double mawAuraFlat(double base, double scaling, double level, double skill, double buffScale)
{
    return (base * buffScale + level / 4) * (1 + scaling * buffScale / 100 * skill);
}

double mawAuraStatPercent(double skill, bool dayOfTheGods)
{
    return std::min(10 + skill / (dayOfTheGods ? 7 : 5), 20.0);
}

namespace
{
double mawPotionAuraFraction(int power)
{
    return 0.75 + 0.75 * std::clamp(power, 0, 200) / 200.0;
}
}

double mawPotionAuraSkill(uint32_t spellId, int power)
{
    const double span = spellId == 83 || spellId == 85 ? 70 : 50;
    return span * (mawPotionAuraFraction(power) - 1);
}

double mawPotionAuraLevel(int power)
{
    return std::max(power, 0) * 0.5 * mawPotionAuraFraction(power);
}

double mawAuraStrength(uint32_t spellId, double skill, double level)
{
    static constexpr std::array<uint32_t, 9> FlatAuras = {3, 14, 25, 36, 38, 46, 58, 69, 85};
    const bool flat = std::find(FlatAuras.begin(), FlatAuras.end(), spellId) != FlatAuras.end();
    return mawBuffMultiplier(int(spellId), skill) * 100 + (flat ? level / 4 : 0);
}
}
