#pragma once

#include "core/OutdoorGrid.h"
#include "core/Project.h"

#include <yaml-cpp/yaml.h>

#include <array>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// The outdoor L3 sketch (sketch.yml, schema/sketch.schema.json): the to-scale plan of an outdoor map on the
// terrain's cells, [x, y] with x east and y south from the north-west corner.

// Cells along each side of an outdoor map (128 on a classic map, core/OutdoorGrid).
inline double sketchMapCells()
{
    return static_cast<double>(outdoorNodeCount());
}

// How far a road's line may pass from the point of a junction its link names, in cells.
constexpr double SketchJunctionTolerance = 1.0;

// A cliff line that ends this near another cliff line without touching it is taken for a line that was meant to
// meet it, in cells.
constexpr double SketchCliffGapCells = 3.0;

// How far outside a water body's outline a height point still counts as its shore, in cells.
constexpr double SketchShoreDistance = 2.0;

// The cells a plot covers, [west, north, east, south]: its `at` corner and its building's plan `footprint_cells`
// [front, depth] turned by `facing` (n or s: front runs east-west). False when the plan gives the building (or
// this member of its group) no footprint, or the plot is not readable.
bool sketchPlotRectangle(const YAML::Node &plan, const YAML::Node &plot, std::array<double, 4> &rectangle);

// The checks of sketch.yml against itself, plan.yml and project.yml that need no terrain:
//   reference  every id the sketch names exists in the plan (frame edges: project.yml neighbours) and is of a kind
//              that fits; plots name buildings of their district's space, with an index inside the group;
//   geometry   coordinates inside the map; polygons simple; plots inside their district and not overlapping (for
//              buildings with a footprint); a road's line passes within SketchJunctionTolerance of the point of each
//              junction its link starts or ends at;
//   grid       whole cells everywhere, half cells only for road lines, plot corners and footprints;
//   heights    the height grid is 4 cells or coarser and of the right shape; a height point inside band polygons
//              fits the range of one of them; a water level is not above the height points on its shore; a cliff
//              line does not end within SketchCliffGapCells of another without sharing a point with it;
//   coverage   every plan entrance, point of interest and landmark has a point; every building of a district that
//              has plots has a plot; every junction a drawn road needs has a point.
// Does nothing when the project has no sketch.yml.
void validateSketch(const Project &project, std::vector<ProjectIssue> &issues);
}
