#pragma once

#include "core/OutdoorModel.h"
#include "core/Project.h"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// `kind: waterfall`: a stream falling off a lip into a pool, built as the shipped falls are (Alvar's
// WaterfallC1test/C2test/C4 on out03, 2,880 down a sheer face; Emerald Island's CaveFall1a-4_E on 7out01, a channel
// stepping 684 then 448). The method is told at the top of OutdoorFalls.cpp.

struct OutdoorFallPlan
{
    std::string id;
    // structures[i], for messages.
    std::string path;
    // The lip's middle and the way the water falls (a unit vector), world units.
    std::array<double, 2> lip = {0.0, 0.0};
    std::array<double, 2> along = {0.0, 1.0};
    // The stream's water at the lip and the pool's at the foot, map units.
    double top = 0.0;
    double foot = 0.0;
    // Across the sheet at the lip; the foot's width over the lip's.
    double width = 512.0;
    double spread = 1.3;
    // How far the sheet's foot stands out beyond the lip (0: upright).
    double lean = 0.0;
    // How far the top water reaches back up the stream from the lip, and the foot water out into the pool.
    double back = 1088.0;
    double pool = 512.0;
    // Rock sides: on or off, their top over the stream's water, their size.
    bool rocks = true;
    double rise = 160.0;
    double rockSize = 384.0;
    uint32_t seed = 0;
    // Low banks along the top water's sides.
    bool banks = true;
    std::string waterTexture;
    std::string rockTexture;
    std::string bankTexture;
};

// The sketch's waterfalls, checked. Messages go to `issues`.
std::vector<OutdoorFallPlan> readOutdoorFalls(
    const Project &project,
    const std::string &world,
    std::vector<ProjectIssue> &issues);

// Cuts the land for each: every node whose cell the sheet or the lip's last cell crosses is set no higher than the
// sheet one cell further down (the foot's level for an upright fall), so no land stands in front of the sheet; water
// nodes so lowered become dry and are added to `dried` (the lowering then takes them out of the water's tiles).
// `ground` and `waterNode` per node (index y * 128 + x), map units, NaN where dry.
void shapeOutdoorFallLand(
    const std::vector<OutdoorFallPlan> &falls,
    std::vector<double> &ground,
    std::vector<double> &waterNode,
    std::vector<size_t> &dried,
    std::vector<std::string> &warnings);

// The faces of one: the top water from up the stream to the lip, the sheet (let through, its picture running down),
// the foot water, the rock sides and the banks. The sheet's faces are added to `sheetFaces`, the level water's to
// `waterFaces`.
void raiseOutdoorFall(
    const OutdoorFallPlan &fall,
    OutdoorModelBuilder &builder,
    uint16_t event,
    std::vector<int> &sheetFaces,
    std::vector<int> &waterFaces);
}
