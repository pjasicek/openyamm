#include "game/ui/GameplayMm9TalkBar.h"

#include <algorithm>

// The talk bar's scroll window, kept apart from its renderer so the unit tests link it alone.
namespace OpenYAMM::Game
{
GameplayMm9TalkBar::ScrollWindow GameplayMm9TalkBar::scrollWindow(const std::vector<float> &lineHeights,
    const std::vector<bool> &exitLines, float lineGap, float exitGap, float room, size_t selectedLine,
    size_t minimumLines)
{
    const size_t lineCount = std::min(lineHeights.size(), exitLines.size());
    ScrollWindow window;
    window.scrollLines = lineCount;

    while (window.scrollLines > 0 && exitLines[window.scrollLines - 1])
    {
        --window.scrollLines;
    }

    if (window.scrollLines == 0)
    {
        window.scrollLines = lineCount;
    }

    if (window.scrollLines == 0)
    {
        return window;
    }

    // The pinned exit lines take their room first; at least a few lines show, the pinned ones counted.
    float pinned = 0;

    for (size_t line = window.scrollLines; line < lineCount; ++line)
    {
        pinned += lineGap + exitGap + lineHeights[line];
    }

    const size_t pinnedLines = lineCount - window.scrollLines;
    const size_t minimum = minimumLines > pinnedLines + 1 ? minimumLines - pinnedLines : 1;
    float used = 0;

    for (size_t line = 0; line < window.scrollLines; ++line)
    {
        const float next = used + lineHeights[line] + (line > 0 ? lineGap : 0);

        if (next > room - pinned && window.visibleLines >= minimum)
        {
            break;
        }

        used = next;
        ++window.visibleLines;
    }

    // The window ends at the selection's line once it has scrolled; a selected exit line shows the list's end.
    const size_t last = std::min(selectedLine, window.scrollLines - 1);
    window.firstLine = last >= window.visibleLines ? last - window.visibleLines + 1 : 0;

    if (window.firstLine > 0)
    {
        window.upLine = window.firstLine + window.visibleLines - 2;
    }

    if (window.firstLine + window.visibleLines < window.scrollLines)
    {
        window.downLine = window.firstLine + window.visibleLines;
    }

    return window;
}
}
