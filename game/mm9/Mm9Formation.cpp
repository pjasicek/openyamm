#include "game/mm9/Mm9Formation.h"

#include "game/party/Party.h"

namespace OpenYAMM::Game
{
std::optional<size_t> mm9FormationOccupant(const std::vector<int32_t> &cells, int32_t cell)
{
    for (size_t combatant = 0; combatant < cells.size(); ++combatant)
    {
        if (cells[combatant] == cell)
        {
            return combatant;
        }
    }

    return std::nullopt;
}

bool mm9FormationMove(std::vector<int32_t> &cells, size_t combatant, int32_t cell)
{
    if (combatant >= cells.size() || cell < 0 || cell >= Mm9FormationCellCount
        || mm9FormationOccupant(cells, cell))
    {
        return false;
    }

    cells[combatant] = cell;
    return true;
}

bool mm9FormationFrontLineCovered(const std::vector<int32_t> &cells)
{
    for (const int32_t cell : cells)
    {
        // Every cell in front of an occupied one, in its column, is held too.
        for (int32_t ahead = cell - Mm9FormationRankSize; ahead >= 0; ahead -= Mm9FormationRankSize)
        {
            if (!mm9FormationOccupant(cells, ahead))
            {
                return false;
            }
        }
    }

    return true;
}

Mm9FormationRect mm9FormationCellRect(const Mm9FormationGrid &grid, int32_t cell)
{
    const int32_t rank = cell / Mm9FormationRankSize;
    const int32_t column = cell % Mm9FormationRankSize;
    const float gapX = (grid.area.width - Mm9FormationRankSize * grid.cellWidth) / (Mm9FormationRankSize - 1);
    const float gapY = (grid.area.height - Mm9FormationRankSize * grid.cellHeight) / (Mm9FormationRankSize - 1);
    return {grid.area.x + float(column) * (grid.cellWidth + gapX), grid.area.y + float(rank) * (grid.cellHeight + gapY),
        grid.cellWidth, grid.cellHeight};
}

std::optional<int32_t> mm9FormationCellAt(const Mm9FormationGrid &grid, float x, float y)
{
    for (int32_t cell = 0; cell < Mm9FormationCellCount; ++cell)
    {
        if (mm9FormationCellRect(grid, cell).contains(x, y))
        {
            return cell;
        }
    }

    return std::nullopt;
}
}
