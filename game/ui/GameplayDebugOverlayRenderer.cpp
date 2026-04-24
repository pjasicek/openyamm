#include "game/ui/GameplayDebugOverlayRenderer.h"

#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameplayScreenRuntime.h"

#include <bgfx/bgfx.h>

#include <algorithm>
#include <cstdint>
#include <string>

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

} // namespace

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
