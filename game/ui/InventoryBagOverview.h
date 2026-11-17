#pragma once

#include "engine/Localization.h"
#include "game/items/InventoryBags.h"
#include "game/party/Party.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <optional>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
// The inventory's bag overview (rulesets with several bags, desktop): the four bags of the open bag's tab at once, two
// by two, at about half size inside the full-size grid's rectangle, a divider between them so no item lies across two
// bags. The 1-4 buttons zoom a bag to full size; a party of one's tab buttons show another tab. The party's pouches
// (rulesets with them) show in the same place, each as one scrolling grid of its own (pouchSlot).
namespace InventoryBagOverview
{
constexpr int Columns = 2;
constexpr int Rows = 2;
constexpr int Bags = Columns * Rows;
static_assert(Bags == InventoryBags::TabBags);
// The divider between the bags, in layout units.
constexpr float DividerUnits = 8.0f;

struct Slot
{
    // The bag's grid.
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    // The bag's size against the full-size grid.
    float fraction = 1.0f;
    // The cells the grid shows, and the bag's row its first row is: a pouch's view scrolls (pouchSlot).
    int columns = Character::InventoryWidth;
    int rows = Character::InventoryHeight;
    int firstRow = 0;

    float cellWidth() const
    {
        return width / float(columns);
    }

    float cellHeight() const
    {
        return height / float(rows);
    }
};

// A pouch's tab (InventoryBags::pouchBag): one grid in the bags' place, as wide and as tall as the four bags of the
// overview without their dividers, at the overview's cell size, with a scrollbar in a gutter at its right. It shows
// InventoryBags::PouchVisibleRows of the pouch's rows from `firstRow` on.
constexpr float PouchScrollGutterUnits = 12.0f;
// Free rows the view scrolls to under the pouch's last item, so there is always room to drop one.
constexpr int PouchSpareRows = 4;

inline Slot pouchSlot(const GameplayResolvedHudLayoutElement &grid, int firstRow)
{
    const float gutter = std::round(PouchScrollGutterUnits * grid.scale);
    const float cell = std::min((grid.width - gutter) / float(InventoryBags::PouchColumns),
        grid.height / float(InventoryBags::PouchVisibleRows));

    Slot result;
    result.x = std::round(grid.x);
    result.y = std::round(grid.y);
    result.width = cell * float(InventoryBags::PouchColumns);
    result.height = cell * float(InventoryBags::PouchVisibleRows);
    result.fraction = cell * float(Character::InventoryWidth) / grid.width;
    result.columns = InventoryBags::PouchColumns;
    result.rows = InventoryBags::PouchVisibleRows;
    result.firstRow = firstRow;
    return result;
}

// The last row the view may start at: the items' rows and PouchSpareRows free ones under them.
inline int pouchMaximumFirstRow(const std::vector<InventoryItem> &items)
{
    int usedRows = 0;

    for (const InventoryItem &item : items)
    {
        usedRows = std::max(usedRows, int(item.gridY) + std::max<int>(1, item.height));
    }

    return std::clamp(usedRows + PouchSpareRows - InventoryBags::PouchVisibleRows, 0,
        InventoryBags::PouchRows - InventoryBags::PouchVisibleRows);
}

// The scrollbar of a pouch's tab: its track in the gutter and its thumb for the view at `firstRow` of
// `maximumFirstRow` (no thumb while everything shows).
struct PouchScrollbar
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    float thumbY = 0.0f;
    float thumbHeight = 0.0f;
};

inline PouchScrollbar pouchScrollbar(const GameplayResolvedHudLayoutElement &grid, int firstRow, int maximumFirstRow)
{
    const Slot slot = pouchSlot(grid, firstRow);
    const float gap = std::round(3.0f * grid.scale);
    PouchScrollbar bar;
    bar.x = slot.x + slot.width + gap;
    bar.y = grid.y;
    bar.width = std::max(1.0f, grid.x + grid.width - bar.x);
    bar.height = grid.height;

    if (maximumFirstRow > 0)
    {
        const float totalRows = float(maximumFirstRow + InventoryBags::PouchVisibleRows);
        bar.thumbHeight =
            std::max(std::round(16.0f * grid.scale), bar.height * float(InventoryBags::PouchVisibleRows) / totalRows);
        bar.thumbY = bar.y
            + (bar.height - bar.thumbHeight) * float(std::clamp(firstRow, 0, maximumFirstRow)) / float(maximumFirstRow);
    }

    return bar;
}

// The first row a thumb whose top is at `thumbY` shows.
inline int pouchFirstRowForThumb(const PouchScrollbar &bar, float thumbY, int maximumFirstRow)
{
    const float travel = bar.height - bar.thumbHeight;

    if (maximumFirstRow <= 0 || travel <= 0.0f)
    {
        return 0;
    }

    return std::clamp(int(std::lround((thumbY - bar.y) / travel * float(maximumFirstRow))), 0, maximumFirstRow);
}

// The divider's thickness on screen.
inline float dividerSize(const GameplayResolvedHudLayoutElement &grid)
{
    return std::round(DividerUnits * grid.scale);
}

// A tab's numeral (0-based), as its button shows it.
inline std::string tabNumeral(int tab)
{
    static constexpr std::array<const char *, 5> Numerals = {"I", "II", "III", "IV", "V"};
    return tab >= 0 && tab < int(Numerals.size()) ? Numerals[size_t(tab)] : std::to_string(tab + 1);
}

// "bag 3", or with several tabs "tab II, bag 3": the bag as the tab and bag buttons name it, translated.
inline std::string bagName(int bag, int bagCount)
{
    return InventoryBags::tabCount(bagCount) > 1
        ? Engine::tr("tab {tab}, bag {bag}", {{"tab", tabNumeral(bag / Bags)}, {"bag", bag % Bags + 1}})
        : Engine::tr("bag {bag}", {{"bag", bag + 1}});
}

// The first bag the overview shows: that of the character's open bag's tab.
inline uint8_t firstBag(const Character &character)
{
    return InventoryBags::tabFirstBag(character.rulesetState.currentBag);
}

// The place of `bag` (0-based) in its tab, row by row: square cells as large as the four grids and the dividers
// allow, the whole centred in the full-size grid's rectangle.
inline Slot slot(const GameplayResolvedHudLayoutElement &grid, int bag)
{
    const int index = bag % Bags;
    const float divider = dividerSize(grid);
    const float cell = std::min((grid.width - divider * float(Columns - 1)) / float(Columns * Character::InventoryWidth),
        (grid.height - divider * float(Rows - 1)) / float(Rows * Character::InventoryHeight));
    const float width = cell * float(Character::InventoryWidth);
    const float height = cell * float(Character::InventoryHeight);
    const float left = grid.x + (grid.width - width * float(Columns) - divider * float(Columns - 1)) * 0.5f;
    const float top = grid.y + (grid.height - height * float(Rows) - divider * float(Rows - 1)) * 0.5f;

    Slot result;
    result.x = std::round(left + float(index % Columns) * (width + divider));
    result.y = std::round(top + float(index / Columns) * (height + divider));
    result.width = width;
    result.height = height;
    result.fraction = width / grid.width;
    return result;
}

inline bool insideGrid(const Slot &bag, float x, float y)
{
    return x >= bag.x && x < bag.x + bag.width && y >= bag.y && y < bag.y + bag.height;
}

// The cell a held item would be dropped at: where the shrunken icon's centre falls, as on the full-size grid (it may
// lie off the grid: an item never crosses a divider). iconWidth and iconHeight are the icon's size on this bag's grid,
// drawX and drawY its top left.
inline std::pair<int, int> heldPlacement(
    const Slot &bag,
    uint8_t itemWidthCells,
    uint8_t itemHeightCells,
    float iconWidth,
    float iconHeight,
    float drawX,
    float drawY)
{
    const float cellWidth = bag.cellWidth();
    const float cellHeight = bag.cellHeight();
    const float spanWidth = float(std::max<uint8_t>(1, itemWidthCells)) * cellWidth;
    const float spanHeight = float(std::max<uint8_t>(1, itemHeightCells)) * cellHeight;
    const int gridX =
        int(std::floor((drawX + iconWidth * 0.5f - bag.x - spanWidth * 0.5f + cellWidth * 0.5f) / cellWidth));
    const int gridY =
        int(std::floor((drawY + iconHeight * 0.5f - bag.y - spanHeight * 0.5f + cellHeight * 0.5f) / cellHeight));
    // Above the first row shown stays off the grid.
    return {gridX, gridY < 0 ? gridY : gridY + bag.firstRow};
}

// The cell of the bag's grid under the point, clamped to the grid.
inline std::pair<uint8_t, uint8_t> cellAt(const Slot &bag, float x, float y)
{
    const int gridX = std::clamp(int((x - bag.x) / bag.cellWidth()), 0, bag.columns - 1);
    const int gridY = std::clamp(int((y - bag.y) / bag.cellHeight()), 0, bag.rows - 1) + bag.firstRow;
    return {uint8_t(gridX), uint8_t(gridY)};
}

// The cell a click with a held item drops it at, as on the full-size grid: on an item, that item's first cell (the
// two swap); elsewhere where the shrunken icon's centre falls. The pointer is inside the bag's grid.
inline std::pair<int, int> dropCell(
    const Slot &bag,
    const Party &party,
    size_t memberIndex,
    uint8_t bagIndex,
    const InventoryItem &held,
    float iconWidth,
    float iconHeight,
    float pointerX,
    float pointerY,
    float grabOffsetX,
    float grabOffsetY)
{
    const auto [cellX, cellY] = cellAt(bag, pointerX, pointerY);

    if (const InventoryItem *pItem = InventoryBags::itemInBagAt(party, memberIndex, bagIndex, cellX, cellY))
    {
        return {pItem->gridX, pItem->gridY};
    }

    return heldPlacement(bag, held.width, held.height, iconWidth, iconHeight,
        pointerX - grabOffsetX * bag.fraction, pointerY - grabOffsetY * bag.fraction);
}
}
}
