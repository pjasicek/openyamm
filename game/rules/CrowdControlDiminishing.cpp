#include "game/rules/CrowdControlDiminishing.h"

#include "game/party/SpellIds.h"
#include "game/rules/SpellRules.h"
#include "game/rules/maw/MawSpellFormulas.h"

#include <algorithm>

namespace OpenYAMM::Game
{
double CrowdControlDiminishingReturns::apply(
    uint64_t targetKey,
    int group,
    double nowSeconds,
    double seconds,
    bool boss)
{
    constexpr double WindowSeconds = 20.0;

    if (group < ControlGroup || group > ParalyzeGroup)
    {
        return seconds;
    }

    std::vector<std::pair<double, double>> &history = m_history[targetKey][size_t(group - ControlGroup)];
    const double windowStart = nowSeconds - WindowSeconds;
    std::erase_if(
        history,
        [windowStart](const std::pair<double, double> &entry)
        {
            return entry.second <= windowStart;
        });
    double recent = 0;

    for (const auto &[start, end] : history)
    {
        recent += std::max(0.0, std::min(end, nowSeconds) - std::max(start, windowStart));
    }

    const double multiplier = mawDiminishingReturnsMultiplier(recent / WindowSeconds);

    if (multiplier <= 0)
    {
        return 0;
    }

    // A boss holds half, but the history counts the whole (MAW's CC rework changelog; its code records the half, see
    // DEVIATIONS.md).
    seconds *= multiplier;
    history.emplace_back(nowSeconds, nowSeconds + seconds);
    return seconds * (boss ? 0.5 : 1);
}

void CrowdControlDiminishingReturns::clear()
{
    m_history.clear();
}

std::optional<float> bossCrowdControlSeconds(const CrowdControlCast &cast, std::mt19937 &rng)
{
    if (cast.pBossHistory == nullptr)
    {
        return std::nullopt;
    }

    CrowdControlDiminishingReturns &history = *cast.pBossHistory;
    const MawCrowdControlSpell *pSpell = mawCrowdControlSpell(cast.spellId);
    const bool stun = cast.spellId == spellIdValue(SpellId::Stun);

    if (!stun && (pSpell == nullptr || pSpell->group < CrowdControlDiminishingReturns::ControlGroup))
    {
        return std::nullopt;
    }

    // Standard's immunity stands.
    if (cast.resistance >= 200)
    {
        return 0.0f;
    }

    // Stun: MAW's roll, then one game minute plus skill x mastery ticks of paralysis (TW:50-58).
    if (stun)
    {
        const double chance = mawStunChance(cast.targetLevel, cast.resistance, cast.skillLevel, true);

        if (std::uniform_real_distribution<double>(0.0, 1.0)(rng) >= chance)
        {
            return 0.0f;
        }

        const double seconds = 2.0 + double(cast.skillLevel) * std::max(1, int(cast.mastery)) / 128.0;
        return float(history.apply(
            cast.targetKey, CrowdControlDiminishingReturns::ParalyzeGroup, cast.nowSeconds, seconds, true));
    }

    // A game minute is two real seconds.
    const double minutes = mawCrowdControlMinutes(*pSpell, cast.mastery, 0.0, cast.resistance, cast.partySize <= 1);
    return float(history.apply(cast.targetKey, pSpell->group, cast.nowSeconds, minutes * 2, true));
}

float bossBlowCrowdControlSeconds(CrowdControlDiminishingReturns &history, uint64_t targetKey, double nowSeconds,
    bool grandmaster)
{
    return float(history.apply(
        targetKey, CrowdControlDiminishingReturns::ParalyzeGroup, nowSeconds, grandmaster ? 4.0 : 2.0, true));
}

float bossBlowControlSeconds(CrowdControlDiminishingReturns &history, uint64_t targetKey, double nowSeconds,
    uint32_t spellId, SkillMastery mastery)
{
    const MawCrowdControlSpell *pSpell = mawCrowdControlSpell(spellId);

    if (pSpell == nullptr)
    {
        return 0.0f;
    }

    // A game minute is two real seconds.
    const double minutes = mawCrowdControlMinutes(*pSpell, mastery, 0.0, 0, false);
    return float(history.apply(targetKey, pSpell->group, nowSeconds, minutes * 2, true));
}
}
