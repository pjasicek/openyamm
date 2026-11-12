#pragma once

#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct RulesetProgressMap;

// The Journal's Progress tab (MAW, level_generation/ui/maw_loot_progress_20261025 B): the game's mode, each continent's
// card, its maps by level with a filter (or every continent's in one list, with "All continents" on), the chosen map's
// details and the dimension and bounty records, laid out in the JournalProgressPage area. The renderer and the journal
// input share the layout below.
enum class JournalProgressTargetKind : uint8_t
{
    None,
    Continent,
    Filter,
    Map,
    // The link to the ruleset's player's guide, at the header's right.
    Guide,
    // The "All continents" chip beside the filters: every continent's maps in one list by level.
    AllContinents,
};

struct JournalProgressTarget
{
    JournalProgressTargetKind kind = JournalProgressTargetKind::None;
    // The continent, the filter, or the map's index in journalProgressMaps.
    size_t index = 0;
};

// The map list's filters: All, Cleared, In progress, Not visited.
constexpr size_t JournalProgressFilterCount = 4;
constexpr size_t JournalProgressVisibleRows = 13;

// Whether the game's rules give the Journal the Progress tab (MAW games).
bool journalHasProgressTab(const GameplayScreenRuntime &context);
// Builds the tab's summary when it has none (the tab was opened): false when the rules have none.
bool ensureJournalProgress(GameplayScreenRuntime &context, GameplayUiController::JournalScreenState &journal);
// The maps of the shown continent (of every continent with "All continents" on) that pass the filter, by level.
std::vector<const RulesetProgressMap *> journalProgressMaps(const GameplayUiController::JournalScreenState &journal);
JournalProgressTarget journalProgressTargetAt(
    const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float x,
    float y);
// `pointerX`/`pointerY`: the pointer, which names the map flag under it.
void renderJournalProgress(
    GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float pointerX,
    float pointerY);
}
