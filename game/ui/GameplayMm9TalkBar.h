#pragma once

#include <cstddef>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct EventDialogContent;

// The MM9 talk (RUDE) conversation bar (level_generation/ui/mm9_talk_dialogue_study_20261102, proposal A, user
// 2026-11-04): a Carved Obsidian panel standing on the party basebar and growing upward with its content, the world
// and the speaker live above it. A monogram medallion and the speaker's name head it, then the party's last sentence,
// the reply, and the choices: number keys, new and visited marks, service tags, the exit row last on Esc. Seven or more
// choices take two columns; past the height limit (just under half the screen) the choices scroll with the selection.
// The renderer and the input share the one layout below.
namespace GameplayMm9TalkBar
{
void render(GameplayScreenRuntime &context, int width, int height, float mouseX, float mouseY);
// The action under the point, if any.
std::optional<size_t> actionAtPoint(GameplayScreenRuntime &context, int width, int height, float x, float y);
// The order of the rows on the bar: the talk's rows as given, its exit rows last.
std::vector<size_t> displayOrder(const EventDialogContent &dialog);
// The action a number key chooses: 1-9, and 0 for the tenth, counted over the rows other than the exit row.
std::optional<size_t> actionForNumberKey(const EventDialogContent &dialog, size_t number);
// The row Esc takes: the first exit row (or Back), if the talk has one.
std::optional<size_t> exitAction(const EventDialogContent &dialog);
}
}
