#pragma once

#include "game/rules/MonsterRules.h"

#include <array>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct GameplayResolvedHudLayoutElement;

// The map progress bar (level_generation/ui/maw_map_progress_20261025, option A, the inlaid channel): a glowing
// channel in the party frame's top stone band filled by MonsterRules::mapProgress, the numbers on a tab rising from the
// frame's right corner (a dimension run's power on a second tab at the left), and the 65 % revival mark where the dead
// can rise. Drawn only while the rules give a progress (never in Standard) and on plain gameplay.
namespace GameplayMapProgressBar
{
// The channel and its tabs, over the party frame.
void renderHud(GameplayScreenRuntime &context, int width, int height);
// The tabs' bounds (left, top, right, bottom) while they show: a solo run's status plate rises above them, and its
// buff rows move down under the tab.
std::optional<std::array<float, 4>> tabBounds(GameplayScreenRuntime &context, int width, int height);

// The hover popup over the channel or a tab: its title and body lines, and the rect it rises above.
struct Popup
{
    std::string title;
    std::string body;
    float x = 0;
    float y = 0;
    float width = 0;
    float height = 0;
    // Above that rect, or below it (a solo HUD's channel at the top of the screen).
    bool above = true;
};
std::optional<Popup> popupAt(GameplayScreenRuntime &context, int width, int height, float pointerX, float pointerY);

// The percent as the rules round it, without a trailing ".0" ("38.5 %", "100 %").
std::string percentText(double percent);
// The right tab's text: "38.5 % \xB7 112 / 292", "Cleared \xB7 292 / 300", "Endless Arena \xB7 Level 5 \xB7 60 %"; the
// percent alone when `percentOnly` (a tab too narrow for the whole).
std::string tabText(const RulesetMapProgress &progress, bool percentOnly);
// The popup's body lines, one per line.
std::string popupBody(const RulesetMapProgress &progress);
}
}
