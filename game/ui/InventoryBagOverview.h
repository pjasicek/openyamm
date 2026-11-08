#pragma once

#include "engine/Localization.h"
#include "game/items/InventoryBags.h"
#include "game/party/Party.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
// The inventory's bag overview (rulesets with several bags, desktop): the four bags of the open bag's tab at once, two
// by two, at about half size inside the full-size grid's rectangle, a divider between them so no item lies across two
// bags. The 1-4 buttons zoom a bag to full size; a party of one's tab buttons show another tab.
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
};

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
    const float cellWidth = bag.width / float(Character::InventoryWidth);
    const float cellHeight = bag.height / float(Character::InventoryHeight);
    const float spanWidth = float(std::max<uint8_t>(1, itemWidthCells)) * cellWidth;
    const float spanHeight = float(std::max<uint8_t>(1, itemHeightCells)) * cellHeight;
    const int gridX =
        int(std::floor((drawX + iconWidth * 0.5f - bag.x - spanWidth * 0.5f + cellWidth * 0.5f) / cellWidth));
    const int gridY =
        int(std::floor((drawY + iconHeight * 0.5f - bag.y - spanHeight * 0.5f + cellHeight * 0.5f) / cellHeight));
    return {gridX, gridY};
}

// The cell of the bag's grid under the point, clamped to the grid.
inline std::pair<uint8_t, uint8_t> cellAt(const Slot &bag, float x, float y)
{
    const float cellWidth = bag.width / float(Character::InventoryWidth);
    const float cellHeight = bag.height / float(Character::InventoryHeight);
    const int gridX = std::clamp(int((x - bag.x) / cellWidth), 0, Character::InventoryWidth - 1);
    const int gridY = std::clamp(int((y - bag.y) / cellHeight), 0, Character::InventoryHeight - 1);
    return {uint8_t(gridX), uint8_t(gridY)};
}

// The cell a click with a held item drops it at, as on the full-size grid: on an item, that item's first cell (the
// two swap); elsewhere where the shrunken icon's centre falls. The pointer is inside the bag's grid.
inline std::pair<int, int> dropCell(
    const Slot &bag,
    const Character &character,
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

    if (const InventoryItem *pItem = InventoryBags::itemInBagAt(character, bagIndex, cellX, cellY))
    {
        return {pItem->gridX, pItem->gridY};
    }

    return heldPlacement(bag, held.width, held.height, iconWidth, iconHeight,
        pointerX - grabOffsetX * bag.fraction, pointerY - grabOffsetY * bag.fraction);
}
}
}
