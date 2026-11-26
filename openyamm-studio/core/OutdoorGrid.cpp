#include "core/OutdoorGrid.h"

#include "core/SketchRead.h"

#include <charconv>
#include <cmath>

namespace OpenYAMM::Studio
{
namespace
{
constexpr double CellSize = 512.0;

thread_local OutdoorGrid ActiveGrid = {};
}

OutdoorGrid outdoorGridOfSide(int side)
{
    OutdoorGrid grid;

    if (side == OutdoorClassicSide || !outdoorSideAllowed(side))
    {
        return grid;
    }

    grid.side = side;
    grid.partyBounds = OutdoorClassicPartyBounds * side / OutdoorClassicSide;
    const double half = side / 2.0;
    const double reach = grid.partyBounds / CellSize;
    grid.playableFirst = static_cast<int>(std::ceil(half - reach));
    grid.playableLast = static_cast<int>(std::floor(half + reach));
    return grid;
}

const OutdoorGrid &outdoorGrid()
{
    return ActiveGrid;
}

OutdoorGridScope::OutdoorGridScope(int side)
    : m_previous(ActiveGrid)
{
    ActiveGrid = outdoorGridOfSide(side);
}

OutdoorGridScope::OutdoorGridScope(const Project &project)
    : OutdoorGridScope(outdoorProjectSide(project))
{
}

OutdoorGridScope::~OutdoorGridScope()
{
    ActiveGrid = m_previous;
}

bool outdoorSideAllowed(int side)
{
    return side >= 32 && side <= 256 && side % 2 == 0;
}

int outdoorProjectSide(const Project &project)
{
    if (!project.has("project.yml"))
    {
        return OutdoorClassicSide;
    }

    const std::string text = textOf(childOf(project.document("project.yml"), "terrain"), "side", "");
    int side = 0;
    const std::from_chars_result result = std::from_chars(text.data(), text.data() + text.size(), side);

    if (text.empty() || result.ec != std::errc() || result.ptr != text.data() + text.size()
        || !outdoorSideAllowed(side))
    {
        return OutdoorClassicSide;
    }

    return side;
}
}
