#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class Party;
class PlaythroughStatistics;

// The Statistics page of the Quick Reference overlay (devdocs/PLAYTHROUGH_STATISTICS_PLAN.md): the playthrough's
// Overview and Party tabs, held right-click breakdowns and this session's numbers in the party frame's right panel.
namespace GameplayStatisticsScreen
{
// One line of a breakdown popup.
struct BreakdownLine
{
    enum class Kind
    {
        Row,
        Section,
        Rule,
        Note,
        Bar,
    };

    Kind kind = Kind::Row;
    std::string label;
    std::string value;
    std::string extra;
    // Bar: the fill (0..1) and its colour.
    float fraction = 0.0f;
    uint32_t colorAbgr = 0;
};

struct Breakdown
{
    std::string title;
    std::vector<BreakdownLine> lines;
};

// A breakdown by id (the Overview rows' ids), built from the statistics; empty title when unknown.
Breakdown buildBreakdown(const std::string &id, const PlaythroughStatistics &statistics, const Party *pParty,
    const GameplayScreenRuntime *pContext);

std::string formatCount(uint64_t value);
std::string formatDuration(double seconds);

void render(GameplayScreenRuntime &context, int width, int height);
}
}
