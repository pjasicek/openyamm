#include "game/ui/GameplayHouseShopLedgerRenderer.h"

#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/rules/GameRules.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/ui/GameplayBenchPainter.h"
#include "game/ui/GameplayPartyOverlayRenderer.h"
#include "game/ui/GameplayUiSkin.h"

#include "engine/Localization.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
using Rect = GameplayResolvedHudLayoutElement;
using namespace HouseShopLedgerMetrics;

// The approved study's colours (ABGR): dim ivory, brass rules and wells, the amber price.
constexpr uint32_t DimText = 0xff8b9da5u;
constexpr uint32_t PriceText = 0xff6cc3e6u;
constexpr uint32_t AlternateRow = 0x2e000000u;
constexpr uint32_t HoverFill = 0x2493c7e4u;
constexpr uint32_t HoverLine = 0x9093c7e4u;
constexpr uint32_t WellFill = 0x59000000u;
constexpr uint32_t WellLine = 0x3393c7e4u;
constexpr uint32_t RuleLine = 0x4d65a4c9u;
constexpr uint32_t ChipOnFill = 0xb21a303au;
constexpr uint32_t ChipOnLine = 0xff5694b9u;
constexpr uint32_t ChipOffFill = 0x8c0c0e0au;
constexpr uint32_t ChipOffLine = 0x4765a4c9u;

int effectiveReputation(const GameplayScreenRuntime &context)
{
    const IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    return pWorldRuntime != nullptr
        ? effectivePartyReputation(pWorldRuntime->currentLocationReputation(), pWorldRuntime->eventRuntimeState())
        : 0;
}

float textScale(const GameplayScreenRuntime &context, const char *pStyleId, float rectScale)
{
    const UiLayoutManager::LayoutElement *pStyle = context.findHudLayoutElement(pStyleId);
    return pStyle != nullptr ? rectScale * std::max(0.1f, pStyle->textScale) : rectScale;
}

float textWidth(const GameplayScreenRuntime &context, const char *pStyleId, const std::string &text, float rectScale)
{
    const UiLayoutManager::LayoutElement *pStyle = context.findHudLayoutElement(pStyleId);
    return pStyle != nullptr ? context.measureHudTextWidth(pStyle->fontName, text) * textScale(context, pStyleId,
        rectScale) : 0.0f;
}

// Shortens text with an ellipsis until it fits the width.
std::string fitted(const GameplayScreenRuntime &context, const char *pStyleId, std::string text, float width,
    float rectScale)
{
    if (textWidth(context, pStyleId, text, rectScale) <= width)
    {
        return text;
    }

    while (!text.empty() && textWidth(context, pStyleId, text + "...", rectScale) > width)
    {
        text.pop_back();
    }

    while (!text.empty() && text.back() == ' ')
    {
        text.pop_back();
    }

    return text + "...";
}

const InventoryItem *rowItem(const GameplayHouseShopLedgerView &view, size_t rowIndex)
{
    if (view.pStock == nullptr || rowIndex >= view.model.rows.size())
    {
        return nullptr;
    }

    return &(*view.pStock)[view.model.rows[rowIndex].stockIndices.front()];
}

// The inspect popup's detail line split where it puts its three-space gaps: "Attack: +2", "Damage: 2d4".
std::vector<std::string> statLines(const std::string &detail)
{
    std::vector<std::string> lines;
    size_t start = 0;

    while (start < detail.size())
    {
        const size_t gap = detail.find("   ", start);
        lines.push_back(detail.substr(start, gap == std::string::npos ? std::string::npos : gap - start));

        if (gap == std::string::npos)
        {
            break;
        }

        start = gap + 3;
    }

    return lines;
}

// The type line under an item's name: a spellbook's school and mastery ("Fire Magic - Expert"), else its kind.
std::string rowTypeText(const InventoryItem &item, const ItemDefinition &definition)
{
    const std::string spellbookLine = houseShopLedgerSpellbookLine(definition);
    return !spellbookLine.empty() ? spellbookLine : resolveItemInspectTypeText(&item, definition);
}

// A shop with one list (MM9's merchants) shows its wares; one with Standard and Special lists names the open one.
std::string stockHeading(const GameplayHouseShopLedgerView &view, bool byType)
{
    if (view.pHouseEntry->deterministicSpecialStockPages.empty())
    {
        return byType ? Engine::tr("Wares by type") : Engine::tr("Wares");
    }

    if (view.stockMode == HouseStockMode::ShopSpecial)
    {
        return byType ? Engine::tr("Special stock by type") : Engine::tr("Special stock");
    }

    return byType ? Engine::tr("Standard stock by type") : Engine::tr("Standard stock");
}

// A heading that sorts the list: lit under the pointer, amber while it orders the list, with a small triangle before
// the text pointing up (ascending) or down.
void drawSortHeading(GameplayScreenRuntime &context, const GameplayBenchPainter &painter,
    const GameplayHouseShopLedgerView &view, HouseShopLedgerSortKey key, const Rect &area, float textX,
    const std::string &label, std::optional<uint32_t> color)
{
    const float s = area.scale;
    const bool active = view.sort.key == key;

    if (painter.hovered(area))
    {
        painter.fill(area, HoverFill);
    }

    painter.text("DialogueShopLedgerColumn",
        {textX, area.y, textWidth(context, "DialogueShopLedgerColumn", label, s) + s, area.height, s}, label,
        active ? std::optional<uint32_t>(PriceText) : color);

    if (!active)
    {
        return;
    }

    constexpr int TriangleRows = 4;
    const float tipX = textX - 5 * s;
    const float top = area.y + (area.height / s - float(TriangleRows)) * 0.5f * s;

    for (int rowIndex = 0; rowIndex < TriangleRows; ++rowIndex)
    {
        const int widthRow = view.sort.descending ? TriangleRows - 1 - rowIndex : rowIndex;
        const float halfWidth = (float(widthRow) + 0.5f) * s;
        painter.fill({tipX - halfWidth, top + float(rowIndex) * s, 2 * halfWidth, s, s}, PriceText);
    }
}

void drawChips(GameplayScreenRuntime &context, const GameplayBenchPainter &painter,
    const GameplayHouseShopLedgerView &view)
{
    const std::vector<Rect> rects = houseShopLedgerChipRects(view.layout, view.model.chips.size());

    for (size_t index = 0; index < rects.size(); ++index)
    {
        const HouseShopLedgerChip &chip = view.model.chips[index];
        const Rect &area = rects[index];
        const bool active = chip.category == view.model.filter;
        painter.fill(area, active ? ChipOnFill : ChipOffFill);
        painter.frame(area, active ? ChipOnLine : ChipOffLine);

        if (!active && painter.hovered(area))
        {
            painter.fill(area, HoverFill);
        }

        const std::string label = Engine::tr(houseShopLedgerCategoryLabel(chip.category));
        const std::string counted = label + " " + std::to_string(chip.rowCount);
        const bool countFits = textWidth(context, "DialogueShopLedgerChip", counted, area.scale)
            <= area.width - 6 * area.scale;
        painter.text("DialogueShopLedgerChip", area, countFits ? counted : label, active ? PriceText : DimText);
    }
}

void drawRow(GameplayScreenRuntime &context, const GameplayBenchPainter &painter,
    const GameplayHouseShopLedgerView &view, const HouseShopLedgerRowRect &rowRect, bool hovered)
{
    const HouseShopLedgerRow &row = view.model.rows[rowRect.rowIndex];
    const InventoryItem &item = (*view.pStock)[row.stockIndices.front()];
    const ItemDefinition *pDefinition = context.itemTable()->get(item.objectDescriptionId);
    const Party *pParty = context.partyReadOnly();

    if (pDefinition == nullptr || pParty == nullptr)
    {
        return;
    }

    const Rect &area = rowRect.rect;
    const float s = area.scale;

    if (hovered)
    {
        painter.fill(area, HoverFill);
        painter.frame(area, HoverLine);
    }
    else if (rowRect.rowIndex % 2 == 1)
    {
        painter.fill(area, AlternateRow);
    }

    const Rect well = {area.x + 2 * s, area.y + (RowHeight - IconWell) * 0.5f * s, IconWell * s, IconWell * s, s};
    painter.fill(well, WellFill);
    painter.frame(well, WellLine);
    painter.itemIcon(pDefinition, {well.x + 2 * s, well.y + 2 * s, well.width - 4 * s, well.height - 4 * s, s});

    const float statX = area.x + area.width - (PriceWidth + StatWidth + 4) * s;
    const float nameX = well.x + well.width + 6 * s;
    const float nameWidth = statX - nameX - 6 * s;
    const ItemRules &itemRules = gameRulesFor(pParty).items;
    const Character *pViewer = pParty->member(pParty->activeMemberIndex());

    // Name and the number of copies on the list.
    const std::string name = ItemRuntime::displayName(
        item, *pDefinition, context.standardItemEnchantTable(), context.specialItemEnchantTable());
    const std::string count = row.stockIndices.size() > 1 ? "x" + std::to_string(row.stockIndices.size()) : "";
    const float countWidth = count.empty() ? 0.0f : textWidth(context, "DialogueShopLedgerCount", count, s) + 5 * s;
    const std::string shownName = fitted(context, "DialogueShopLedgerName", name, nameWidth - countWidth, s);
    const Rect nameArea = {nameX, area.y + 4 * s, nameWidth, 16 * s, s};
    painter.text("DialogueShopLedgerName", nameArea, shownName);

    if (!count.empty())
    {
        const float countX = nameX + textWidth(context, "DialogueShopLedgerName", shownName, s) + 5 * s;
        painter.text("DialogueShopLedgerCount", {countX, area.y + 6 * s, countWidth, 12 * s, s}, count);
    }

    // Type (a spellbook: its school and the mastery it needs), then the first enchantment line in its own colour.
    const std::string &type = row.typeText;
    const Rect detailArea = {nameX, area.y + 21 * s, nameWidth, 12 * s, s};
    const std::vector<ItemInspectLine> inspect = itemRules.inspectLines(
        item, *pDefinition, context.standardItemEnchantTable(), context.specialItemEnchantTable(), pViewer);
    const std::string shownType = fitted(context, "DialogueShopLedgerDetail", type, nameWidth, s);
    painter.text("DialogueShopLedgerDetail", detailArea, shownType);

    if (!inspect.empty())
    {
        const float typeWidth = textWidth(context, "DialogueShopLedgerDetail", shownType + "  ", s);
        const uint32_t rgb = inspect.front().color;
        const uint32_t abgr = 0xff000000u | ((rgb & 0xffu) << 16) | (rgb & 0xff00u) | ((rgb >> 16) & 0xffu);
        const float enchantWidth = nameWidth - typeWidth;

        if (enchantWidth > 20 * s)
        {
            painter.text("DialogueShopLedgerDetail", {nameX + typeWidth, detailArea.y, enchantWidth, 12 * s, s},
                fitted(context, "DialogueShopLedgerDetail", inspect.front().text, enchantWidth, s), abgr);
        }
    }

    // The main stat, as the inspect popup words it, one part per line.
    const std::string detail = resolveItemInspectDetailText(&item, *pDefinition,
        itemRules.baseStats(*pDefinition, item.rulesetFields, pViewer != nullptr ? int(pViewer->level) : 1),
        nullptr);
    const std::vector<std::string> lines = statLines(detail);
    const float lineHeight = 12 * s;
    float lineY = area.y + (area.height - lineHeight * float(lines.size())) * 0.5f;

    for (const std::string &line : lines)
    {
        painter.text("DialogueShopLedgerStat", {statX, lineY, StatWidth * s, lineHeight, s},
            fitted(context, "DialogueShopLedgerStat", line, StatWidth * s, s));
        lineY += lineHeight;
    }

    const int price = row.price;
    painter.text("DialogueShopLedgerPrice",
        {area.x + area.width - (PriceWidth + 4) * s, area.y, PriceWidth * s, area.height, s},
        std::to_string(price), pParty->gold() >= price ? PriceText : GameplayUiSkin::Penalty);

    GameplayRenderedInspectableHudItem inspectable = {};
    inspectable.objectDescriptionId = item.objectDescriptionId;
    inspectable.hasItemState = true;
    inspectable.itemState = item;
    inspectable.textureName = pDefinition->iconName;
    inspectable.textureUsesItemIconTransparency = true;
    inspectable.x = area.x;
    inspectable.y = area.y;
    inspectable.width = area.width;
    inspectable.height = area.height;
    context.addRenderedInspectableHudItem(inspectable);
}
}

namespace GameplayHouseShopLedgerRenderer
{
std::optional<GameplayHouseShopLedgerView> resolve(GameplayScreenRuntime &context, int width, int height)
{
    const GameplayUiController::HouseShopOverlayState &overlay = context.houseShopOverlay();

    if (!overlay.active
        || (overlay.mode != GameplayUiController::HouseShopMode::BuyStandard
            && overlay.mode != GameplayUiController::HouseShopMode::BuySpecial)
        || context.party() == nullptr
        || context.worldRuntime() == nullptr
        || context.itemTable() == nullptr
        || context.houseTable() == nullptr
        || context.standardItemEnchantTable() == nullptr
        || context.specialItemEnchantTable() == nullptr)
    {
        return std::nullopt;
    }

    const HouseEntry *pHouseEntry = context.houseTable()->get(overlay.houseId);

    // MM9's merchants always list their stock; the other shops do with the Shops as lists setting (OY-590).
    if (pHouseEntry == nullptr
        || (pHouseEntry->shopBuyView != ShopBuyView::Ledger && !context.settingsSnapshot().shopListView))
    {
        return std::nullopt;
    }

    const std::optional<GameplayResolvedHudLayoutElement> frame = context.resolveHouseShopOverlayFrame(width, height);

    if (!frame)
    {
        return std::nullopt;
    }

    GameplayHouseShopLedgerView view = {};
    view.pHouseEntry = pHouseEntry;
    view.stockMode = overlay.mode == GameplayUiController::HouseShopMode::BuySpecial ? HouseStockMode::ShopSpecial
                                                                                     : HouseStockMode::ShopStandard;
    view.pStock = &HouseServiceRuntime::ensureStock(*context.party(), *context.itemTable(),
        *context.standardItemEnchantTable(), *context.specialItemEnchantTable(), *pHouseEntry,
        context.worldRuntime()->gameMinutes(), view.stockMode);
    view.model = buildHouseShopLedgerModel(*view.pStock,
        HouseServiceRuntime::slotCountForStockMode(*pHouseEntry, view.stockMode), *context.itemTable(),
        overlay.ledgerFilter);
    const Party &party = *context.party();
    const int reputation = effectiveReputation(context);

    for (HouseShopLedgerRow &row : view.model.rows)
    {
        const InventoryItem &item = (*view.pStock)[row.stockIndices.front()];
        const ItemDefinition *pDefinition = context.itemTable()->get(item.objectDescriptionId);
        row.typeText = rowTypeText(item, *pDefinition);
        row.price = HouseServiceRuntime::buyPrice(party, *context.itemTable(), *context.standardItemEnchantTable(),
            *context.specialItemEnchantTable(), *pHouseEntry, item, reputation);
    }

    view.sort = overlay.ledgerSort;
    sortHouseShopLedgerRows(view.model.rows, view.sort);
    view.layout = buildHouseShopLedgerLayout(*frame);
    view.firstRow = std::min(overlay.ledgerFirstRow, houseShopLedgerMaximumFirstRow(view.layout,
        view.model.rows.size()));
    return view;
}

std::optional<size_t> stockIndexAt(const GameplayHouseShopLedgerView &view, float x, float y)
{
    const std::optional<size_t> row = houseShopLedgerRowAt(view.layout, view.model.rows.size(), view.firstRow, x, y);

    if (!row)
    {
        return std::nullopt;
    }

    return view.model.rows[*row].stockIndices.front();
}

bool render(GameplayScreenRuntime &context, const GameplayHouseShopLedgerView &view, float mouseX, float mouseY)
{
    const GameplayBenchPainter painter(context, 0, 0);
    const HouseShopLedgerLayout &layout = view.layout;
    const float s = layout.list.scale;
    GameplayUiSkin::renderPanel(context, layout.panel, false, PanelBorderScale);
    drawChips(context, painter, view);

    // Column headings over a brass rule; Wares and Price sort the list.
    const HouseShopLedgerColumnRects columns = houseShopLedgerColumnRects(layout);
    const std::string waresHeading = stockHeading(view, view.sort.key == HouseShopLedgerSortKey::Type);
    drawSortHeading(context, painter, view, HouseShopLedgerSortKey::Type, columns.wares, columns.wares.x,
        waresHeading, GameplayUiSkin::Gold);
    painter.text("DialogueShopLedgerColumn", columns.stat, Engine::tr("Stat"));
    // Prices are right-aligned, so is their heading.
    const std::string priceHeading = Engine::tr("Price");
    const float priceHeadingWidth = textWidth(context, "DialogueShopLedgerColumn", priceHeading, s);
    drawSortHeading(context, painter, view, HouseShopLedgerSortKey::Price, columns.price,
        columns.price.x + columns.price.width - priceHeadingWidth, priceHeading, std::nullopt);
    painter.fill({layout.columns.x, layout.columns.y + layout.columns.height + s, layout.columns.width,
        std::max(1.0f, std::round(0.6f * s)), s}, RuleLine);

    const std::optional<size_t> hoveredRow =
        houseShopLedgerRowAt(layout, view.model.rows.size(), view.firstRow, mouseX, mouseY);

    for (const HouseShopLedgerRowRect &rowRect :
        houseShopLedgerVisibleRows(layout, view.model.rows.size(), view.firstRow))
    {
        drawRow(context, painter, view, rowRect, hoveredRow == rowRect.rowIndex);
    }

    if (view.model.rows.empty())
    {
        painter.text("DialogueShopLedgerName", {layout.list.x + 8 * s, layout.list.y + 8 * s, layout.list.width,
            16 * s, s}, Engine::tr("Nothing left for sale."), DimText);
    }

    const size_t maximumFirstRow = houseShopLedgerMaximumFirstRow(layout, view.model.rows.size());
    GameplayUiSkin::renderScrollbar(context, layout.list,
        maximumFirstRow > 0 ? float(view.firstRow) / float(maximumFirstRow) : 0.0f,
        view.model.rows.empty() ? 1.0f : float(layout.visibleRows) / float(view.model.rows.size()),
        context.interactionState().houseShopLedgerScrollDrag);

    // Footer: what is left, and when the stock turns over.
    const std::string forSale = view.model.copiesGrouped > 0
        ? Engine::tr("{count} for sale - {copies} copies grouped",
                     {{"count", view.model.itemsForSale}, {"copies", view.model.copiesGrouped}})
        : Engine::tr("{count} for sale", {{"count", view.model.itemsForSale}});

    painter.text("DialogueShopLedgerFooter", layout.footer, forSale);
    const Party *pParty = context.partyReadOnly();
    const Party::HouseStockState *pStockState =
        pParty != nullptr ? pParty->houseStockState(view.pHouseEntry->id) : nullptr;

    if (pStockState != nullptr && context.worldRuntime() != nullptr)
    {
        const float minutesLeft = pStockState->nextRefreshGameMinutes - context.worldRuntime()->gameMinutes();
        const int days = std::max(1, int(std::ceil(minutesLeft / (24.0f * 60.0f))));
        const std::string restock = days == 1
            ? Engine::tr("New stock tomorrow")
            : Engine::trn("New stock in {days} day", "New stock in {days} days", uint64_t(days), {{"days", days}});
        const float restockWidth = textWidth(context, "DialogueShopLedgerFooter", restock, s);
        painter.text("DialogueShopLedgerFooter", {layout.footer.x + layout.footer.width - restockWidth,
            layout.footer.y, restockWidth + s, layout.footer.height, s}, restock);
    }

    return hoveredRow.has_value();
}

std::optional<std::string> hoverText(
    GameplayScreenRuntime &context,
    const GameplayHouseShopLedgerView &view,
    float mouseX,
    float mouseY)
{
    // A heading says what a click on it does.
    if (const std::optional<HouseShopLedgerSortKey> column = houseShopLedgerColumnAt(view.layout, mouseX, mouseY))
    {
        const HouseShopLedgerSort next = nextHouseShopLedgerSort(view.sort, *column);

        if (next.key == HouseShopLedgerSortKey::Stock)
        {
            return Engine::tr("Show the shop's own order");
        }

        if (next.key == HouseShopLedgerSortKey::Price)
        {
            return next.descending ? Engine::tr("Sort by price, dearest first")
                                   : Engine::tr("Sort by price, cheapest first");
        }

        return next.descending ? Engine::tr("Sort by type, in reverse") : Engine::tr("Sort by type");
    }

    const std::optional<size_t> row =
        houseShopLedgerRowAt(view.layout, view.model.rows.size(), view.firstRow, mouseX, mouseY);
    const InventoryItem *pItem = row ? rowItem(view, *row) : nullptr;

    if (pItem == nullptr || context.partyReadOnly() == nullptr)
    {
        return std::nullopt;
    }

    return HouseServiceRuntime::buildBuyHoverText(*context.partyReadOnly(), *context.itemTable(),
        *context.standardItemEnchantTable(), *context.specialItemEnchantTable(), *view.pHouseEntry, *pItem,
        effectiveReputation(context));
}
}
}
