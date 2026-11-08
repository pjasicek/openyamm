#pragma once

#include "game/party/InventoryItem.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/HouseShopLedgerCategory.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
struct ItemDefinition;

// MM9's merchant list (MERCHANT-COORDS.txt): one scrolling row per kind of item, filtered by MM9's merchant tabs.
// Shops whose HouseEntry::shopBuyView is Ledger draw their Buy Standard and Buy Special stock this way instead of on
// the MM6-MM8 shelf picture. Design: level_generation/ui/mm9_shop_buy_study_20261105/.

const char *houseShopLedgerCategoryLabel(HouseShopLedgerCategory category);
HouseShopLedgerCategory houseShopLedgerCategoryOf(const ItemDefinition &definition);
// A spellbook's spell (its Mod1 "S<n>", 1-99, eleven per school from Fire to Dark), or none.
std::optional<int> houseShopLedgerSpellNumber(const ItemDefinition &definition);
// A spellbook's school (FireBooks ... DarkBooks), or none.
std::optional<HouseShopLedgerCategory> houseShopLedgerSpellSchoolOf(const ItemDefinition &definition);
// A weapon's or armour's kind (Swords ... Blasters by weapon skill, BodyArmor ... Cloaks by slot), or none.
std::optional<HouseShopLedgerCategory> houseShopLedgerKindOf(const ItemDefinition &definition);
// The school a spellbook's spell belongs to and the mastery it needs ("Fire Magic - Expert"), or empty.
std::string houseShopLedgerSpellbookLine(const ItemDefinition &definition);

// One row: identical stock items (same item, enchantments and state) grouped, first shown first.
struct HouseShopLedgerRow
{
    std::vector<size_t> stockIndices;
    HouseShopLedgerCategory category = HouseShopLedgerCategory::PotionsMisc;
    std::optional<HouseShopLedgerCategory> school;
    // A weapon's or armour's kind: the tabs of a shop that sells only weapons or only armour.
    std::optional<HouseShopLedgerCategory> kind;
    int spellNumber = 0;
    // Sort keys the caller fills in: the type line the row shows and the party's buy price.
    std::string typeText;
    int price = 0;
};

struct HouseShopLedgerChip
{
    HouseShopLedgerCategory category = HouseShopLedgerCategory::All;
    size_t rowCount = 0;
};

struct HouseShopLedgerModel
{
    // All, then each category the stock holds; empty when it holds only one, which then needs no filter. A stock of
    // spellbooks only is filtered by their schools instead, and listed in spell order (school by school); a stock of
    // weapons only or armour only by their kinds.
    std::vector<HouseShopLedgerChip> chips;
    // The requested filter, or All when the stock has nothing of it.
    HouseShopLedgerCategory filter = HouseShopLedgerCategory::All;
    std::vector<HouseShopLedgerRow> rows;
    size_t itemsForSale = 0;
    // Items folded into another row's count.
    size_t copiesGrouped = 0;
};

// The first slotCount stock entries; sold slots (item 0) and items missing from the table are left out.
HouseShopLedgerModel buildHouseShopLedgerModel(
    const std::vector<InventoryItem> &stock,
    size_t slotCount,
    const ItemTable &itemTable,
    HouseShopLedgerCategory requestedFilter);

// A click on a column heading: ascending first, descending on the second click, the stock's order on the third; a
// click on the other column starts it ascending.
HouseShopLedgerSort nextHouseShopLedgerSort(HouseShopLedgerSort current, HouseShopLedgerSortKey clicked);
// Reorders the rows by type (merchant tab, then the type line; spellbooks by school and spell) or price; equal rows
// keep the stock's order.
void sortHouseShopLedgerRows(std::vector<HouseShopLedgerRow> &rows, HouseShopLedgerSort sort);

// Geometry inside the shop overlay frame (DialogueShopOverlayFrame), in pixels; the frame's scale is pixels per
// logical unit of the 640x480 screen.
struct HouseShopLedgerLayout
{
    GameplayResolvedHudLayoutElement panel;
    GameplayResolvedHudLayoutElement chipBar;
    GameplayResolvedHudLayoutElement columns;
    GameplayResolvedHudLayoutElement list;
    GameplayResolvedHudLayoutElement footer;
    float rowHeight = 0.0f;
    size_t visibleRows = 0;
};

struct HouseShopLedgerRowRect
{
    size_t rowIndex = 0;
    GameplayResolvedHudLayoutElement rect;
};

namespace HouseShopLedgerMetrics
{
constexpr float PanelBorderScale = 0.5f;
constexpr float ContentInset = 13.0f;
constexpr float ChipHeight = 14.0f;
constexpr float ChipWidth = 60.0f;
constexpr float MinimumChipWidth = 36.0f;
constexpr float ChipGap = 3.0f;
constexpr float ColumnsHeight = 10.0f;
constexpr float FooterHeight = 11.0f;
constexpr float RowHeight = 36.0f;
constexpr float IconWell = 32.0f;
constexpr float StatWidth = 76.0f;
constexpr float PriceWidth = 56.0f;
constexpr float ScrollbarWidth = 8.0f;
}

HouseShopLedgerLayout buildHouseShopLedgerLayout(const GameplayResolvedHudLayoutElement &frame);
std::vector<GameplayResolvedHudLayoutElement> houseShopLedgerChipRects(
    const HouseShopLedgerLayout &layout,
    size_t chipCount);
// The top row index can be at most this (whole-row scrolling, so no row is ever cut).
size_t houseShopLedgerMaximumFirstRow(const HouseShopLedgerLayout &layout, size_t rowCount);
std::vector<HouseShopLedgerRowRect> houseShopLedgerVisibleRows(
    const HouseShopLedgerLayout &layout,
    size_t rowCount,
    size_t firstRow);
std::optional<size_t> houseShopLedgerRowAt(
    const HouseShopLedgerLayout &layout,
    size_t rowCount,
    size_t firstRow,
    float x,
    float y);
std::optional<size_t> houseShopLedgerChipAt(const HouseShopLedgerLayout &layout, size_t chipCount, float x, float y);
// The column headings over the list: Wares (name and type) and Stat on the left, Price right-aligned before the
// scrollbar. Wares and Price sort the list.
struct HouseShopLedgerColumnRects
{
    GameplayResolvedHudLayoutElement wares;
    GameplayResolvedHudLayoutElement stat;
    GameplayResolvedHudLayoutElement price;
};
HouseShopLedgerColumnRects houseShopLedgerColumnRects(const HouseShopLedgerLayout &layout);
std::optional<HouseShopLedgerSortKey> houseShopLedgerColumnAt(const HouseShopLedgerLayout &layout, float x, float y);
// The scrollbar's track along the list's right edge (GameplayUiSkin::renderScrollbar draws there).
bool houseShopLedgerOnScrollbar(const HouseShopLedgerLayout &layout, float x, float y);
}
