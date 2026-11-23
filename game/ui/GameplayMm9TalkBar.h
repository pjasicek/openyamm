#pragma once

#include <cstddef>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct EventDialogContent;

// The MM9 talk (RUDE) conversation bar (level_generation/ui/mm9_talk_dialogue_study_20261102, proposal A, user
// 2026-11-04): a Carved Obsidian panel standing where the party basebar is (a talk hides the party, user 2026-11-06)
// and growing upward with its content, the world and the speaker live above it. A monogram medallion and the
// speaker's name head it, then the party's last sentence, the reply, and the choices: number keys, new, visited and
// locked marks, service tags, the exit row last on Esc. Seven or more choices take two columns; past the height limit
// (just under half the screen) the choices scroll with the selection, the exit row pinned in view below them, and
// scroll buttons beside them answer a click or a tap (touch has no wheel or keys). The renderer and the input share
// the one layout below.
namespace GameplayMm9TalkBar
{
void render(GameplayScreenRuntime &context, int width, int height, float mouseX, float mouseY);
// The action under the point, if any.
std::optional<size_t> actionAtPoint(GameplayScreenRuntime &context, int width, int height, float x, float y);
// The scroll button under the point: -1 up, 1 down, 0 none (or the list cannot go that way).
int scrollButtonAtPoint(GameplayScreenRuntime &context, int width, int height, float x, float y);
// Scrolls the list one line up (direction < 0) or down (> 0) by moving the selection, which the list follows.
void scroll(GameplayScreenRuntime &context, int width, int height, int direction);

// The lines of a list taller than its room that are in view. A line is one row, or two side by side in two columns.
// The exit lines at the list's end are pinned below the window, so the way out always shows; the lines before them
// scroll. Once scrolled, the window ends at the selection's line.
struct ScrollWindow
{
    // The lines that scroll; the lines after them are pinned.
    size_t scrollLines = 0;
    size_t firstLine = 0;
    size_t visibleLines = 0;
    // The line to select to scroll one line up or down, if the list can go that way.
    std::optional<size_t> upLine;
    std::optional<size_t> downLine;
};
ScrollWindow scrollWindow(const std::vector<float> &lineHeights, const std::vector<bool> &exitLines, float lineGap,
    float exitGap, float room, size_t selectedLine, size_t minimumLines);
// The top edge of the open talk's panel, for the status plate above it.
std::optional<float> panelTop(GameplayScreenRuntime &context, int width, int height);
// The order of the rows on the bar: the talk's rows as given, its exit rows last.
std::vector<size_t> displayOrder(const EventDialogContent &dialog);
// The action a number key chooses: 1-9, and 0 for the tenth, counted over the rows other than the exit row.
std::optional<size_t> actionForNumberKey(const EventDialogContent &dialog, size_t number);
// The row Esc takes: the first exit row (or Back), if the talk has one.
std::optional<size_t> exitAction(const EventDialogContent &dialog);
}
}
