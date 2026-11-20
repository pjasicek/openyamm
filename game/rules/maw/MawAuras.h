#pragma once

#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
// MAW's buff rework (devdocs/maw/CLASSES_SPELLS_SPEC.md §3, data/buff_auras.yml): buff spells are party-wide auras
// toggled by their caster, who reserves part of the mana pool while holding them. Pure.

struct MawAura
{
    uint32_t spellId = 0;
    // The reservation: a percent cost divided by the holder's class SP factor, or a flat number of points for the
    // utility auras (Torch Light, Wizard Eye, Water Walk).
    double cost = 0;
    bool utility = false;
    // The holder's skill counts up to 75 for Day of the Gods, Day of Protection and Hour of Power, 50 otherwise.
    double skillCap = 50;
};

// The aura a buff spell becomes, or null for a spell that stays as it is.
const MawAura *mawAura(uint32_t spellId);

// The school skill an aura reads: "FireMagic" .. "DarkMagic" by the spell's school.
std::string mawSpellSchoolSkill(uint32_t spellId);

// The percent of the maximum mana an aura reserves: cost / (class SP factor + Enlightenment mastery / 2).
double mawAuraReservedPercent(double cost, double classSpellFactor, int enlightenmentMastery);
// A utility aura's flat reservation: round(cost x (1 - Enlightenment mastery / 10)).
int mawUtilityAuraReservation(double cost, int enlightenmentMastery);

// A flat aura's strength (resistance, armour, attack): (base + level / 4) x (1 + scaling / 100 x skill).
double mawAuraFlat(double base, double scaling, double level, double skill, double buffScale = 1);
// The stat percent of the resistance auras, min(10 + skill / 5, 20); Day of the Gods min(10 + skill / 7, 20).
double mawAuraStatPercent(double skill, bool dayOfTheGods);

// A drinker's potion copy of an aura (CLASSES_SPELLS_SPEC.md §7.5): with f = 0.75 + 0.75 x min(P, 200) / 200, it casts
// at skill 50 x (f - 1) (70 for Day of the Gods and Day of Protection; negative below power 67) and caster level
// P x f / 2, at Master.
double mawPotionAuraSkill(uint32_t spellId, int power);
double mawPotionAuraLevel(int power);
// buffStrength, which decides between two sources of one aura: base + scaling x skill / 10, plus level / 4 for the
// flat auras (resistances, Stone Skin, Bless, Day of Protection).
double mawAuraStrength(uint32_t spellId, double skill, double level);
}
