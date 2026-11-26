#pragma once

#include "game/ui/GameplayOverlayTypes.h"

#include <cstddef>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct PartySpellCastRequest;

// The Web of Worlds page of Town Portal (level_generation/projects/hesper_hive/concept, "Web of Worlds"): the star
// chart of the mounted planets (web_of_worlds contributions) drawn over the Town Portal page, 640 x 480 page units,
// and the tab that opens it.
namespace GameplayWebOfWorlds
{
enum class TargetType
{
    None,
    Planet,
    Signal,
    KnownWorld,
    Beacon,
    Travel,
    Close,
};

struct Target
{
    TargetType type = TargetType::None;
    size_t index = 0;

    bool operator==(const Target &other) const = default;
};

// A chart target as the Town Portal screen's pointer target (type WebOfWorlds), and back.
GameplayUtilitySpellPointerTarget pointerTarget(const Target &target);
Target fromPointerTarget(const GameplayUtilitySpellPointerTarget &target);

// Whether the Town Portal pages have a Web of Worlds page, and whether it is the one shown.
bool hasPage(const GameplayScreenRuntime &context);
bool pageShown(const GameplayScreenRuntime &context);
// Whether the party may open it (an unlock QBit, or standing on a planet).
bool unlocked(const GameplayScreenRuntime &context);
// Play and remember the world contribution's first-opening greeting while the chart is open.
void greetOnFirstOpen(GameplayScreenRuntime &context);
// English hint for the tooltip or status bar. Each localizes it at its display boundary.
std::string tabHint(const GameplayScreenRuntime &context);

// The tab beside the continent buttons (`TownPortalWebButton`), and its hint above it while hovered.
void renderTab(GameplayScreenRuntime &context, int width, int height, float mouseX, float mouseY, bool pressed);
// The chart over the Town Portal page.
void renderChart(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &page, float mouseX,
    float mouseY, bool leftPressed);
Target targetAt(const GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &page, float x, float y);

// A click on the chart: selects, travels (fills the request and returns true) or leaves the page.
bool activate(GameplayScreenRuntime &context, const Target &target, PartySpellCastRequest &request);
}
}
