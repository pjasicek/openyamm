#pragma once

#include <vector>

namespace OpenYAMM::Game
{
// MAW's surcharge: past level 100 each level costs 0.5 % more per level above 100 (MAW ba572ec2; 1 % before).
constexpr double MawExperienceSurcharge = 0.005;

// MAW's experience curve (devdocs/maw/data/exp_curve.yml): the vanilla 1000 x L per level to 100, then 1000 x L x
// (1 + (L - 100) x surcharge). Levels are fractional inside a step.
class MawExperienceCurve
{
public:
    explicit MawExperienceCurve(double surchargePerLevel);

    double experienceForLevel(double level) const;
    double levelForExperience(double experience) const;
    double surchargePerLevel() const;

private:
    // Experience to go from `level` to the next.
    double step(double level) const;

    double m_surchargePerLevel = MawExperienceSurcharge;
    // Experience to reach each whole level, from 0 at levels 0 and 1.
    std::vector<double> m_table;
};

// MAW's own curve, the one every conversion goes through except a solo run's character (MawRules::characterCurve).
const MawExperienceCurve &mawExperienceCurve();
double mawExperienceForLevel(double level);
double mawLevelForExperience(double experience);

// Climbs `levels` vanilla levels' worth of experience (500 L (L - 1)) on top of the MAW curve at `floorLevel`, so above
// level 100 a monster family gains fewer levels than it is offset by (zzMaw-Monsters.lua bolsteredLevel).
double mawBolsteredLevel(double floorLevel, double levels);
}
