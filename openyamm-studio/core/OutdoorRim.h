#pragma once

#include "core/Polygon.h"
#include "core/Project.h"

#include <yaml-cpp/yaml.h>

#include <array>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// The land beyond the square the party can walk: the rim. What it is on the shipped maps and how a sketch's
// `frame.rim` and `frame.edge` become heights is told at the top of OutdoorRim.cpp.

// The nodes of the square the party can walk (the game's own: 23143 units from the map's middle): 19 to 109 on both
// axes. The rim is the nodes outside it: 19 rows in the north and west, 18 in the south and east.
constexpr int OutdoorPlayableFirstNode = 19;
constexpr int OutdoorPlayableLastNode = 109;

enum class OutdoorRimSide
{
    North = 0,
    East,
    South,
    West,
};

enum class OutdoorRimForm
{
    Level,
    Ridge,
};

struct OutdoorRimEntry
{
    OutdoorRimSide side = OutdoorRimSide::North;
    OutdoorRimForm form = OutdoorRimForm::Level;
    // Along the side, in cells: x for north and south, y for east and west.
    double spanFrom = 0.0;
    double spanTo = 128.0;
    // Level: the ground lies between the two. Ridge: the crest's saddles stand at the first, its tops reach the
    // second.
    double low = 0.0;
    double high = 0.0;
    // Ridge: the ground between the square and the crest.
    double floor = 0.0;
    // Ridge: cells out from the square to the line of tops.
    double crest = 12.0;
    // Level: cells out from the square over which the land at the square's edge runs into the form.
    double meet = 4.0;
    double roughness = 0.0;
    uint32_t seed = 1;
    // The plan space the strip shows (a reader's link to plan.yml; the land does not depend on it).
    std::string space;
};

// A line a valley follows out through the rim: a road or a river.
struct OutdoorRimValley
{
    std::vector<Point2> line;
    // Half the road's or river's own width, in cells.
    double halfWidth = 0.5;
    // The floor's height at each point of the line (a road's bed, a river's level); empty: the land's height where
    // the line leaves the square, all the way out.
    std::vector<double> floor;
};

struct OutdoorRim
{
    std::vector<OutdoorRimEntry> entries;
    // The height the outermost row of nodes stands at, by side (north, east, south, west).
    std::array<std::optional<double>, 4> edge;
    std::vector<OutdoorRimValley> valleys;

    bool shapesAnything() const;
};

// Reads `frame.rim` (the entries with a `form`), `frame.edge` and the roads and rivers that run out through the
// rim. What cannot be built is added to `issues` with what to change; what is read and has no effect (an entry
// without a form, the retired `depth`) to `warnings`.
void readOutdoorRim(const YAML::Node &sketch, OutdoorRim &rim, std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings);

// Shapes the rim of a field of base heights (128 x 128, index y * 128 + x): the nodes outside the square the party
// can walk take the heights of the entries that cover them; valleys stay open along roads and rivers; the outermost
// rows take the edge heights. Nodes inside the square are never changed. With `pShaped`, it is set to 1 for every
// node a form shaped (left empty when the rim shapes nothing).
void shapeOutdoorRim(const OutdoorRim &rim, std::vector<double> &base, std::vector<uint8_t> *pShaped = nullptr);

// Sets the outermost row of nodes of each side that `frame.edge` gives to its height (a node in a corner of two such
// sides to the mean of the two). Smoothing may have moved them since the rim was shaped.
void holdOutdoorRimEdge(const OutdoorRim &rim, std::vector<double> &field);

// How far a node stands out from the square on one side, in cells (0 or less: not on that side's strip).
int outdoorRimDistance(OutdoorRimSide side, int x, int y);

// A number from 0 to 1 (never 1) for a seed and three whole numbers, the same on every machine.
double outdoorChance(uint32_t seed, int32_t first, int32_t second, int32_t third);

// A value from 0 to 1 that changes smoothly from place to place, level over about `cells` cells (between whole
// multiples of `cells` it runs smoothly from one chance to the next).
double outdoorWave(uint32_t seed, double x, double y, double cells);
}
