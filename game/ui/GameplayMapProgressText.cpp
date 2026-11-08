#include "game/ui/GameplayMapProgressBar.h"
#include "engine/Localization.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>

// The map progress bar's texts, apart from its drawing so the unit tests need no HUD.
namespace OpenYAMM::Game
{
std::string GameplayMapProgressBar::percentText(double percent)
{
    const double tenths = std::round(std::clamp(percent, 0.0, 100.0) * 10);
    char text[16] = {};

    if (std::fmod(tenths, 10.0) == 0)
    {
        std::snprintf(text, sizeof(text), "%d %%", int(tenths / 10));
    }
    else
    {
        std::snprintf(text, sizeof(text), "%.1f %%", tenths / 10);
    }

    return text;
}

std::string GameplayMapProgressBar::tabText(const RulesetMapProgress &progress, bool percentOnly)
{
    // The HUD fonts are single-byte: the middle dot is 0xB7.
    const std::string dot = " \xB7 ";
    const std::string percent = percentText(progress.percent);

    if (percentOnly)
    {
        return percent;
    }

    if (progress.kind == RulesetMapProgress::Kind::Arena)
    {
        return Engine::tr("Endless Arena") + dot
            + Engine::tr("Level {level}", {{"level", int64_t(progress.arenaLevel)}}) + dot + percent;
    }

    if (progress.complete)
    {
        return Engine::tr("Cleared") + dot + std::to_string(progress.slain) + " / " + std::to_string(progress.counted);
    }

    return percent + dot + std::to_string(progress.slain) + " / " + std::to_string(progress.needed);
}

std::string GameplayMapProgressBar::popupBody(const RulesetMapProgress &progress)
{
    std::vector<std::string> lines;

    if (progress.kind == RulesetMapProgress::Kind::Arena)
    {
        lines.push_back(Engine::tr("Wave level: {level}", {{"level", int64_t(progress.arenaLevel)}}));
        lines.push_back(Engine::tr("This wave: {percent}", {{"percent", percentText(progress.percent)}}));
        lines.push_back(Engine::tr("The Arena is never completed"));
    }
    else
    {
        if (progress.kind == RulesetMapProgress::Kind::DimensionRun)
        {
            lines.push_back(Engine::trn("Dimension run: power {power}, {affixes} affix",
                "Dimension run: power {power}, {affixes} affixes", uint64_t(int64_t(progress.dimensionAffixes)),
                {{"power", int64_t(progress.dimensionPower)}, {"affixes", int64_t(progress.dimensionAffixes)}}));
        }

        lines.push_back(Engine::tr("Slain: {slain} of {counted}",
            {{"slain", int64_t(progress.slain)}, {"counted", int64_t(progress.counted)}}));
        lines.push_back(Engine::tr("Needed to complete: {needed} ({percent})",
            {{"needed", int64_t(progress.needed)}, {"percent", percentText(progress.requiredShare * 100)}}));
        const int64_t alive = int64_t(std::max(0, progress.counted - progress.slain));
        lines.push_back(progress.hidden > 0
                ? Engine::tr("Alive: {alive}, {hidden} hidden, not counted",
                    {{"alive", alive}, {"hidden", int64_t(progress.hidden)}})
                : Engine::tr("Alive: {alive}", {{"alive", alive}}));

        if (progress.revival)
        {
            lines.push_back(progress.revivalPassed ? Engine::tr("Dead rise again on leaving: no longer")
                : Engine::tr("Dead rise again on leaving: until {slain} slain",
                    {{"slain", int64_t(progress.revivalSlain)}}));
        }

        lines.push_back(progress.rewardPaid ? Engine::tr("Reward: paid")
                                            : Engine::tr("Reward: {reward}", {{"reward", progress.reward}}));
    }

    std::string body;

    for (const std::string &line : lines)
    {
        body += (body.empty() ? "" : "\n") + line;
    }

    return body;
}
}
