#include "game/ui/GameplayLootSummaryRenderer.h"
#include "engine/Localization.h"
#include "engine/Utf8Text.h"

#include "game/items/InventoryBags.h"
#include "game/items/ItemRuntime.h"
#include "game/rules/GameRules.h"
#include "game/tables/ItemTable.h"
#include "game/ui/GameplayBenchPainter.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
using Rect = GameplayResolvedHudLayoutElement;

constexpr float RowHeight = 22.0f;
constexpr float ListPadding = 3.0f;
constexpr float ColumnGap = 4.0f;
constexpr float ScrollbarRoom = 6.0f;
constexpr float IconSize = 18.0f;
constexpr int WheelRows = 3;
// A sold item's icon, dimmed.
constexpr uint8_t SoldIconAlpha = 110;
// The HUD's gold icon (gameplay.yml OutdoorGoldIcon) in front of the gold amount.
constexpr const char *GoldIconAsset = "scorebg_gold";
constexpr float GoldIconWidth = 19.733333f;
constexpr float GoldIconHeight = 14.4f;
// The gold icon in front of a sold item's gold, smaller than the summary's own.
constexpr float RowCoinScale = 0.75f;

// An item of the list, and where it went in the bags (none for one left behind or sold), or the gold the loot filter
// sold it for.
struct SummaryEntry
{
    const InventoryItem *pItem = nullptr;
    const GameplayUiController::LootedItemPlace *pPlace = nullptr;
    std::optional<int> soldGold;
};

// A line of the list: a header across both columns, or up to two items.
struct SummaryLine
{
    std::string header;
    std::array<SummaryEntry, 2> entries = {};
};

void appendEntryLines(const std::vector<SummaryEntry> &entries, std::vector<SummaryLine> &lines)
{
    for (size_t index = 0; index < entries.size(); index += 2)
    {
        SummaryLine line;
        line.entries = {entries[index], index + 1 < entries.size() ? entries[index + 1] : SummaryEntry{}};
        lines.push_back(line);
    }
}

void appendItemLines(const std::vector<InventoryItem> &items, std::vector<SummaryLine> &lines)
{
    std::vector<SummaryEntry> entries;

    for (const InventoryItem &item : items)
    {
        entries.push_back({&item, nullptr, std::nullopt});
    }

    appendEntryLines(entries, lines);
}

std::string groupedNumber(int value)
{
    std::string digits = std::to_string(std::abs(value));

    for (int index = int(digits.size()) - 3; index > 0; index -= 3)
    {
        digits.insert(size_t(index), ",");
    }

    return value < 0 ? "-" + digits : digits;
}

std::vector<SummaryLine> buildLines(const GameplayUiController::LootSummaryOverlayState &state)
{
    std::vector<SummaryLine> lines;
    std::vector<SummaryEntry> looted;

    for (const GameplayUiController::LootedItem &item : state.items)
    {
        looted.push_back(item.sold ? SummaryEntry{&item.item, nullptr, item.soldGold}
                                   : SummaryEntry{&item.item, &item.place, std::nullopt});
    }

    appendEntryLines(looted, lines);

    if (!state.leftItems.empty())
    {
        SummaryLine header;
        header.header = Engine::tr("Left in satchels: no room in the bags");
        lines.push_back(header);
        appendItemLines(state.leftItems, lines);
    }

    if (!state.leftGroundItems.empty())
    {
        SummaryLine header;
        header.header = Engine::tr("Left on the ground: no room in the bags");
        lines.push_back(header);
        appendItemLines(state.leftGroundItems, lines);
    }

    return lines;
}

// The looted item as it lies in its bag now (identified, repaired), when it still lies where it went.
const InventoryItem *itemInPlace(const GameplayScreenRuntime &context, const SummaryEntry &entry)
{
    const Party *pParty = context.partyReadOnly();
    const Character *pMember =
        entry.pPlace != nullptr && pParty != nullptr ? pParty->member(entry.pPlace->memberIndex) : nullptr;

    if (pMember == nullptr)
    {
        return nullptr;
    }

    const InventoryItem *pItem = InventoryBags::itemInBagAt(
        *pParty, entry.pPlace->memberIndex, entry.pPlace->bag, entry.pPlace->gridX, entry.pPlace->gridY);
    return pItem != nullptr && pItem->objectDescriptionId == entry.pItem->objectDescriptionId ? pItem : nullptr;
}

float maximumScroll(size_t lineCount, const Rect &list)
{
    const float visibleHeight = list.height / std::max(0.01f, list.scale) - 2 * ListPadding;
    return std::max(0.0f, float(lineCount) * RowHeight - visibleHeight);
}


// The rules' rarity colour (0xRRGGBB) as the label's ABGR, else the list's ivory.
uint32_t itemNameColor(const GameplayScreenRuntime &context, const InventoryItem &item)
{
    const std::optional<uint32_t> rgb = gameRulesFor(context.partyReadOnly()).items.nameColor(item);

    if (!rgb)
    {
        return GameplayUiSkin::Ivory;
    }

    return 0xff000000u | ((*rgb & 0xffu) << 16) | (*rgb & 0xff00u) | ((*rgb >> 16) & 0xffu);
}

// The gold amount centred with the HUD's gold icon in front of it.
// The text cut with an ellipsis to fit the width (pixels), measured with the layout element's font and scale.
std::string fittedText(GameplayScreenRuntime &context, const char *pStyleId, const std::string &value, float available,
    float scale)
{
    const UiLayoutManager::LayoutElement *pStyle = context.findHudLayoutElement(pStyleId);

    if (pStyle == nullptr)
    {
        return value;
    }

    const float textScale = scale * std::max(0.1f, pStyle->textScale);
    const auto widthOf = [&](const std::string &text)
    {
        return context.measureHudTextWidth(pStyle->fontName, text) * textScale;
    };

    if (widthOf(value) <= available)
    {
        return value;
    }

    std::string result = value;

    while (result.size() > 1)
    {
        // A whole character: shown names may be translated into letters of several bytes.
        Engine::Utf8::popBack(result);

        while (!result.empty() && result.back() == ' ')
        {
            result.pop_back();
        }

        if (widthOf(result + "...") <= available)
        {
            return result + "...";
        }
    }

    return result;
}

void renderGold(GameplayScreenRuntime &context, const GameplayBenchPainter &painter, int goldAmount,
    int followerGoldShare)
{
    const UiLayoutManager::LayoutElement *pStyle = context.findHudLayoutElement("LootSummaryGold");
    const std::optional<Rect> area = painter.rect("LootSummaryGold");

    if (pStyle == nullptr || !area)
    {
        return;
    }

    const std::string text = followerGoldShare > 0
        ? Engine::tr("{gold} gold (followers took {share})",
            {{"gold", groupedNumber(goldAmount)}, {"share", groupedNumber(followerGoldShare)}})
        : Engine::tr("{gold} gold", {{"gold", groupedNumber(goldAmount)}});
    const float s = area->scale;
    const float textWidth = context.measureHudTextWidth(pStyle->fontName, text) * s * pStyle->textScale;
    const float iconWidth = GoldIconWidth * s;
    const float iconHeight = GoldIconHeight * s;
    const float gap = 4 * s;
    const float x = std::round(area->x + (area->width - (iconWidth + gap + textWidth)) * 0.5f);
    GameplayUiSkin::renderTexture(context, GoldIconAsset,
        {x, std::round(area->y + (area->height - iconHeight) * 0.5f), iconWidth, iconHeight, s});
    painter.text("LootSummaryGold", {x + iconWidth + gap, area->y, textWidth + 2 * s, area->height, s}, text);
}
}

void GameplayLootSummaryRenderer::render(GameplayScreenRuntime &context, int width, int height)
{
    const GameplayUiController::LootSummaryOverlayState &state = context.lootSummaryOverlayReadOnly();
    const ItemTable *pItemTable = context.itemTable();

    if (!state.active || !context.hasHudRenderResources() || pItemTable == nullptr || width <= 0 || height <= 0)
    {
        return;
    }

    const GameplayBenchPainter painter(context, width, height);
    const std::optional<Rect> panel = painter.rect("LootSummaryPanel");

    if (!panel)
    {
        return;
    }

    context.prepareHudView(width, height);
    // The HUD under the summary must not answer item inspection; its own items do.
    context.gameplayUiRuntime().clearRenderedInspectableHudItems();
    GameplayUiSkin::renderPanel(context, *panel, false, 0.75f);
    painter.label("LootSummaryTitle", Engine::tr("Map Looted"));
    const std::string satchels = Engine::trn("{count} satchel", "{count} satchels", state.satchelCount,
        {{"count", state.satchelCount}});
    const size_t keptCount = state.items.size() - state.soldItemCount;
    const std::string items = Engine::trn("{count} item", "{count} items", keptCount, {{"count", keptCount}});
    const std::string groundItems = Engine::trn("{count} ground item", "{count} ground items", state.groundItemCount,
        {{"count", state.groundItemCount}});
    // Only spotted ground items are sold here: the satchels' drops were filtered when they were rolled.
    painter.label("LootSummaryOverview",
        state.groundItemCount == 0 ? Engine::tr("{satchels} emptied, {items} taken",
            {{"satchels", satchels}, {"items", items}})
        : state.satchelCount == 0 && state.soldItemCount == 0 ? Engine::tr("{ground} picked up, {items} taken",
            {{"ground", groundItems}, {"items", items}})
        : state.satchelCount == 0 ? Engine::tr("{ground} picked up: {kept} kept, {sold} sold",
            {{"ground", groundItems}, {"kept", keptCount}, {"sold", state.soldItemCount}})
        : state.soldItemCount == 0 ? Engine::tr("{satchels} emptied, {ground} picked up, {items} taken",
            {{"satchels", satchels}, {"ground", groundItems}, {"items", items}})
        : Engine::tr("{satchels} emptied, {ground} picked up: {kept} kept, {sold} sold",
            {{"satchels", satchels}, {"ground", groundItems}, {"kept", keptCount}, {"sold", state.soldItemCount}}));
    renderGold(context, painter, state.goldAmount, state.followerGoldShare);

    if (const std::optional<Rect> list = painter.rect("LootSummaryList"))
    {
        painter.well(*list);
        const std::vector<SummaryLine> lines = buildLines(state);
        const float maximum = maximumScroll(lines.size(), *list);
        const float scroll = std::clamp(state.scrollOffset, 0.0f, maximum);
        const float s = list->scale;
        const float top = list->y + ListPadding * s;
        const float bottom = list->y + list->height - ListPadding * s;
        const float left = list->x + ListPadding * s;
        const float innerWidth = list->width - (2 * ListPadding + ScrollbarRoom) * s;
        const float columnWidth = (innerWidth - ColumnGap * s) * 0.5f;

        for (size_t lineIndex = 0; lineIndex < lines.size(); ++lineIndex)
        {
            const float y = top + (float(lineIndex) * RowHeight - scroll) * s;

            // Lines are whole or hidden, so text never spills past the well.
            if (y < top - 0.5f || y + RowHeight * s > bottom + 0.5f)
            {
                continue;
            }

            const SummaryLine &line = lines[lineIndex];

            if (line.entries[0].pItem == nullptr)
            {
                painter.text("LootSummaryRowHeader", {left + 2 * s, y, innerWidth, RowHeight * s, s}, line.header);
                continue;
            }

            for (size_t column = 0; column < line.entries.size(); ++column)
            {
                const SummaryEntry &entry = line.entries[column];

                if (entry.pItem == nullptr)
                {
                    continue;
                }

                const InventoryItem *pInBag = itemInPlace(context, entry);
                const InventoryItem *pItem = pInBag != nullptr ? pInBag : entry.pItem;
                const ItemDefinition *pDefinition = pItemTable->get(pItem->objectDescriptionId);

                if (pDefinition == nullptr)
                {
                    continue;
                }

                const Rect cell = {left + float(column) * (columnWidth + ColumnGap * s), y, columnWidth,
                    RowHeight * s, s};

                if (painter.hovered(cell))
                {
                    painter.fill(cell, GameplayBenchColors::HoverColor);
                }

                // An item the loot filter sold is dimmed, with the gold icon and its gold at the row's end.
                float priceWidth = 0.0f;

                if (entry.soldGold)
                {
                    const std::string price = groupedNumber(*entry.soldGold);

                    if (const UiLayoutManager::LayoutElement *pPriceStyle =
                            context.findHudLayoutElement("LootSummaryRowPrice"))
                    {
                        const float textWidth = std::ceil(
                            context.measureHudTextWidth(pPriceStyle->fontName, price) * s * pPriceStyle->textScale);
                        const float coinWidth = GoldIconWidth * RowCoinScale * s;
                        const float coinHeight = GoldIconHeight * RowCoinScale * s;
                        priceWidth = coinWidth + textWidth + 9 * s;
                        GameplayUiSkin::renderTexture(context, GoldIconAsset,
                            {std::round(cell.x + cell.width - priceWidth + 3 * s),
                                std::round(cell.y + (cell.height - coinHeight) * 0.5f), coinWidth, coinHeight, s});
                        // Right-aligned over the whole row, so that the font's snapped scale never clips it.
                        painter.text("LootSummaryRowPrice", {cell.x + (IconSize + 6) * s, cell.y,
                            cell.width - (IconSize + 8) * s, cell.height, s}, price);
                    }
                }

                painter.itemIcon(pDefinition,
                    {cell.x + 2 * s, cell.y + (RowHeight - IconSize) * 0.5f * s, IconSize * s, IconSize * s, s},
                    entry.soldGold ? SoldIconAlpha : 255);
                const std::string name = ItemRuntime::displayName(
                    *pItem, *pDefinition, context.standardItemEnchantTable(), context.specialItemEnchantTable());
                const float nameWidth = cell.width - (IconSize + 8) * s - priceWidth;
                painter.text("LootSummaryRowLabel", {cell.x + (IconSize + 6) * s, cell.y, nameWidth, cell.height, s},
                    fittedText(context, "LootSummaryRowLabel", name, nameWidth, s),
                    entry.soldGold ? GameplayBenchColors::DisabledTextColor : itemNameColor(context, *pItem));

                // An item in the bags inspects as the inventory's own: right-click identifies or repairs it when
                // the party can.
                GameplayRenderedInspectableHudItem inspectable = {};
                inspectable.objectDescriptionId = pItem->objectDescriptionId;
                inspectable.hasItemState = true;
                inspectable.itemState = *pItem;

                if (pInBag != nullptr)
                {
                    inspectable.sourceType = GameplayUiController::ItemInspectSourceType::Inventory;
                    inspectable.sourceMemberIndex = entry.pPlace->memberIndex;
                    inspectable.sourceBag = entry.pPlace->bag;
                    inspectable.sourceGridX = entry.pPlace->gridX;
                    inspectable.sourceGridY = entry.pPlace->gridY;
                }

                inspectable.x = cell.x;
                inspectable.y = cell.y;
                inspectable.width = cell.width;
                inspectable.height = cell.height;
                inspectable.wholeAreaHits = true;
                context.addRenderedInspectableHudItem(inspectable);
            }
        }

        if (lines.empty())
        {
            painter.text("LootSummaryRowLabel", {left + 4 * s, top, innerWidth, RowHeight * s, s},
                Engine::tr("The satchels held only gold."), GameplayBenchColors::DimTextColor);
        }

        const float visibleHeight = list->height / s - 2 * ListPadding;
        const float linesHeight = float(lines.size()) * RowHeight;
        GameplayUiSkin::renderScrollbar(context, *list, maximum > 0 ? scroll / maximum : 0.0f,
            linesHeight > 0 ? visibleHeight / linesHeight : 1.0f, false);
    }

    painter.button("LootSummaryCloseButton", Engine::tr("Close"), true);
}

bool GameplayLootSummaryRenderer::handleInput(
    GameplayScreenRuntime &context,
    const GameplayInputFrame &input,
    int width,
    int height)
{
    GameplayUiController::LootSummaryOverlayState &state = context.lootSummaryOverlay();

    if (!state.active)
    {
        return false;
    }

    if (input.mouseWheelDelta != 0)
    {
        if (const std::optional<Rect> list = context.resolveHudLayoutElement("LootSummaryList", width, height, 0, 0))
        {
            const float maximum = maximumScroll(buildLines(state).size(), *list);
            state.scrollOffset = std::clamp(
                state.scrollOffset - input.mouseWheelDelta * RowHeight * WheelRows, 0.0f, maximum);
        }
    }

    if (input.leftMouseButton.released)
    {
        const std::optional<Rect> close =
            context.resolveHudLayoutElement("LootSummaryCloseButton", width, height, 0, 0);

        if (close && GameplayHudCommon::isPointerInsideResolvedElement(*close, input.pointerX, input.pointerY))
        {
            GameplayLootSummaryRenderer::close(context);
        }
    }

    return true;
}

void GameplayLootSummaryRenderer::close(GameplayScreenRuntime &context)
{
    context.lootSummaryOverlay() = {};
}
}
