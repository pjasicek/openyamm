#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
// The MM9 formation builder (devdocs/mm9/MM9_HIRELINGS_PLAN.md phase 10; the accepted design
// level_generation/ui/mm9_formation_20261106): MM9's grid rules (MM9_HIRELINGS.md section 10.1) over one cell per
// combatant (Party::formationCells: the members, then the hirelings). Cells 0-8 row by row, 0-2 the front rank.

// The combatant standing on a cell, if any.
std::optional<size_t> mm9FormationOccupant(const std::vector<int32_t> &cells, int32_t cell);
// MM9 has no swap: a combatant may be dropped only on an empty cell. False (nothing changes) for an occupied cell,
// its own cell or an invalid one.
bool mm9FormationMove(std::vector<int32_t> &cells, size_t combatant, int32_t cell);
// MM9's "front line must be covered": nobody stands behind an empty cell of the same column. A column may be empty.
bool mm9FormationFrontLineCovered(const std::vector<int32_t> &cells);

struct Mm9FormationRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;

    bool contains(float pointX, float pointY) const
    {
        return pointX >= x && pointX < x + width && pointY >= y && pointY < y + height;
    }
};

// The builder's 3 x 3 grid (mm9_formation.yml Mm9FormationGrid and its Mm9FormationCell): three cells a rank, the
// front rank on top, columns left to right, the cells spread evenly over the grid.
struct Mm9FormationGrid
{
    Mm9FormationRect area;
    float cellWidth = 0.0f;
    float cellHeight = 0.0f;
};

Mm9FormationRect mm9FormationCellRect(const Mm9FormationGrid &grid, int32_t cell);
std::optional<int32_t> mm9FormationCellAt(const Mm9FormationGrid &grid, float x, float y);

enum class Mm9FormationButton : uint8_t
{
    None,
    Cancel,
    Accept,
};

// The open builder: the arrangement being edited (applied on Accept), the face that follows the pointer and the
// control a press began on.
struct Mm9FormationBuilderState
{
    bool open = false;
    std::vector<int32_t> cells;
    std::optional<size_t> dragged;
    // The pointer's offset from the dragged face's top left when it was taken, in pixels.
    float grabOffsetX = 0.0f;
    float grabOffsetY = 0.0f;
    Mm9FormationButton pressedButton = Mm9FormationButton::None;
    // Accept was refused (someone behind an empty cell): the instruction line says so until the next move.
    bool refused = false;
};
}
