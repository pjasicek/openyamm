#pragma once

#include "game/gameplay/HouseServiceRuntime.h"
#include "game/ui/HouseShopLedger.h"

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct HouseEntry;

// The open Buy Standard or Buy Special list of a Ledger shop this frame, shared by its renderer and its input.
struct GameplayHouseShopLedgerView
{
    const HouseEntry *pHouseEntry = nullptr;
    HouseStockMode stockMode = HouseStockMode::ShopStandard;
    const std::vector<InventoryItem> *pStock = nullptr;
    // Rows in the order the overlay's column headings chose (HouseShopLedgerSort).
    HouseShopLedgerModel model;
    HouseShopLedgerSort sort;
    HouseShopLedgerLayout layout;
    // The overlay's top row, clamped to the list.
    size_t firstRow = 0;
};

namespace GameplayHouseShopLedgerRenderer
{
// None unless a Buy list of a shop whose buy_view is Ledger is open.
std::optional<GameplayHouseShopLedgerView> resolve(GameplayScreenRuntime &context, int width, int height);
// The stock entry a click on the row under the pointer buys: the row's first remaining copy.
std::optional<size_t> stockIndexAt(const GameplayHouseShopLedgerView &view, float x, float y);
// Draws the list; returns whether the pointer is over a row.
bool render(GameplayScreenRuntime &context, const GameplayHouseShopLedgerView &view, float mouseX, float mouseY);
// The merchant's line about the item under the pointer, as on the shelves, or what a column heading does.
std::optional<std::string> hoverText(
    GameplayScreenRuntime &context,
    const GameplayHouseShopLedgerView &view,
    float mouseX,
    float mouseY);
}
}
