#include "game/ui/GameplayDebugOverlayRenderer.h"

#include "game/events/EventDialogContent.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/ChestTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/gameplay/GameplayScreenRuntime.h"

#include <bgfx/bgfx.h>

#include <algorithm>
#include <cstdint>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr int DebugTextCellWidthPixels = 8;
constexpr int DebugTextCellHeightPixels = 16;

void renderCenteredDebugTextLine(int textColumns, int row, uint8_t color, const std::string &text)
{
    const int column = std::max(0, (textColumns - static_cast<int>(text.size())) / 2);
    bgfx::dbgTextPrintf(static_cast<uint16_t>(column), static_cast<uint16_t>(row), color, "%s", text.c_str());
}

std::string lootItemDebugName(
    GameplayScreenRuntime &context,
    const GameplayChestItemState &item)
{
    if (item.isGold)
    {
        std::string name = std::to_string(item.goldAmount) + " gold";

        if (item.goldRollCount > 1)
        {
            name += " (" + std::to_string(item.goldRollCount) + " rolls)";
        }

        return name;
    }

    const ItemTable *pItemTable = context.itemTable();
    const ItemDefinition *pItemDefinition = pItemTable != nullptr ? pItemTable->get(item.itemId) : nullptr;

    if (pItemDefinition != nullptr && !pItemDefinition->name.empty())
    {
        std::string name = pItemDefinition->name;

        if (item.quantity > 1)
        {
            name += " x" + std::to_string(item.quantity);
        }

        return name;
    }

    return "item #" + std::to_string(item.itemId);
}
} // namespace

void GameplayDebugOverlayRenderer::renderChestPanel(GameplayScreenRuntime &context, int width, int height)
{
    if (context.worldRuntime() == nullptr || width <= 0 || height <= 0)
    {
        return;
    }

    const GameplayChestViewState *pChestView = context.worldRuntime()->activeChestView();
    const GameplayCorpseViewState *pCorpseView = context.worldRuntime()->activeCorpseView();

    if (pChestView == nullptr && pCorpseView == nullptr)
    {
        return;
    }

    const int textColumns = std::max(80, width / DebugTextCellWidthPixels);
    const int textRows = std::max(25, height / DebugTextCellHeightPixels);
    int row = std::max(8, textRows / 4);

    std::string title;

    if (pChestView != nullptr)
    {
        std::ostringstream titleStream;
        titleStream << "Chest #" << pChestView->chestId;

        if (context.chestTable() != nullptr)
        {
            const ChestEntry *pChestEntry = context.chestTable()->get(pChestView->chestTypeId);

            if (pChestEntry != nullptr && !pChestEntry->name.empty())
            {
                titleStream << " - " << pChestEntry->name;
            }
        }

        title = titleStream.str();
    }
    else
    {
        title = pCorpseView->title.empty() ? "Corpse" : pCorpseView->title;
    }

    renderCenteredDebugTextLine(textColumns, row++, 0x1f, title);
    renderCenteredDebugTextLine(textColumns, row++, 0x0f, "Up/Down select  Enter/Space loot  Esc close");
    row += 1;

    const std::vector<GameplayChestItemState> &items =
        pChestView != nullptr ? pChestView->items : pCorpseView->items;

    if (items.empty())
    {
        renderCenteredDebugTextLine(textColumns, row, 0x0f, "Empty");
        return;
    }

    constexpr size_t MaxVisibleItems = 14;
    const size_t visibleCount = std::min(items.size(), MaxVisibleItems);

    for (size_t itemIndex = 0; itemIndex < visibleCount; ++itemIndex)
    {
        const bool isSelected = itemIndex == context.chestSelectionIndex();
        const std::string line =
            std::to_string(itemIndex + 1)
            + ". "
            + lootItemDebugName(context, items[itemIndex]);
        const int column = std::max(4, (textColumns / 2) - 20);
        const uint8_t color = isSelected ? 0x0e : 0x0f;
        bgfx::dbgTextPrintf(static_cast<uint16_t>(column), static_cast<uint16_t>(row++), color, "%s", line.c_str());
    }

    if (items.size() > visibleCount)
    {
        renderCenteredDebugTextLine(textColumns, row, 0x0f, "...");
    }
}

void GameplayDebugOverlayRenderer::renderEventDialogPanel(GameplayScreenRuntime &context, int width, int height)
{
    if (!context.activeEventDialog().isActive || width <= 0 || height <= 0)
    {
        return;
    }

    const EventDialogContent &dialog = context.activeEventDialog();
    const int textColumns = std::max(80, width / DebugTextCellWidthPixels);
    const int textRows = std::max(25, height / DebugTextCellHeightPixels);
    int row = std::max(8, textRows / 4);

    renderCenteredDebugTextLine(textColumns, row++, 0x1f, dialog.title);

    const bool hasActions = !dialog.actions.empty();
    const std::string closeHint = hasActions
        ? "Up/Down select  Enter/Space accept  Esc close"
        : "Enter/Space/Esc close";
    renderCenteredDebugTextLine(textColumns, row++, 0x0f, closeHint);
    row += 1;

    const size_t maxVisibleLines = hasActions ? 8u : 12u;
    const size_t visibleCount = std::min(dialog.lines.size(), maxVisibleLines);

    for (size_t lineIndex = 0; lineIndex < visibleCount; ++lineIndex)
    {
        renderCenteredDebugTextLine(textColumns, row++, 0x0f, dialog.lines[lineIndex]);
    }

    if (!hasActions)
    {
        return;
    }

    row += 1;

    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        const EventDialogAction &action = dialog.actions[actionIndex];
        const bool isSelected = actionIndex == context.eventDialogSelectionIndex();
        std::string line = isSelected ? "> " : "  ";
        line += action.label;

        if (!action.enabled)
        {
            line += " [unavailable]";
        }

        const uint8_t color = !action.enabled ? 0x08 : (isSelected ? 0x2f : 0x0f);
        renderCenteredDebugTextLine(textColumns, row++, color, line);
    }
}
} // namespace OpenYAMM::Game
