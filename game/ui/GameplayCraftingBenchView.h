#pragma once

#include "game/items/CraftingRuntime.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class CraftingRules;

enum class GameplayCraftingBenchRowKind : uint8_t
{
    Header,
    Item
};

struct GameplayCraftingBenchRow
{
    GameplayCraftingBenchRowKind kind = GameplayCraftingBenchRowKind::Item;
    size_t targetIndex = 0;
    std::string text;
    float offsetY = 0;
    float height = 0;
};

// What the Crafting tab shows this frame, shared by its renderer and its input.
struct GameplayCraftingBenchModel
{
    std::vector<CraftTargetEntry> targets;
    std::vector<GameplayCraftingBenchRow> rows;
    float rowsHeight = 0;
    std::vector<CraftMaterialEntry> materials;
    std::vector<size_t> visibleMaterials;
    std::optional<size_t> selectedTarget;
    std::optional<size_t> selectedMaterial;
    // What crafting can still do to the chosen item (CraftingRules::craftOutlook).
    std::vector<std::string> outlook;
    // With a material chosen, whether it works on each item; with an item chosen, whether each material works on it.
    std::vector<bool> targetUsable;
    std::vector<bool> materialUsable;
    // One application, and as many as the party's materials allow.
    std::optional<CraftPlan> step;
    std::optional<CraftPlan> batch;
    // Merges of the chosen gem's tier, and the whole climb from the lowest tier.
    GemCombinePlan combine;
    GemCombinePlan combineAll;
    std::string ownerText;
};

struct GameplayCraftingBenchRowRect
{
    size_t rowIndex = 0;
    GameplayResolvedHudLayoutElement rect;
};

struct GameplayCraftingBenchCellRect
{
    size_t materialIndex = 0;
    GameplayResolvedHudLayoutElement rect;
};

// One option of a step the player picks (CraftResult::choices), a row at the top of the comparison area.
struct GameplayCraftingBenchChoiceRect
{
    size_t choiceIndex = 0;
    GameplayResolvedHudLayoutElement rect;
};

namespace GameplayCraftingBenchView
{
// Apply All stops after this many steps.
constexpr uint32_t MaxBatchApplications = 999;
// The pick of a step with options: its prompt line, then one row per option.
constexpr float ChoicePromptHeight = 10.0f;
constexpr float ChoiceRowHeight = 12.0f;

std::optional<CraftingTables> tables(const GameplayScreenRuntime &context);
const CraftingRules &rules(const GameplayScreenRuntime &context);
// Whether the Workbench has a Crafting tab under the party's rules.
bool available(const GameplayScreenRuntime &context);
std::optional<GameplayCraftingBenchModel> buildModel(const GameplayScreenRuntime &context);
// What a material does, as the operation header says it.
std::string operationName(const GameplayScreenRuntime &context, uint32_t materialItemId);
// The item's name as the rules show it (rarity and enchantments).
std::string itemDisplayName(const GameplayScreenRuntime &context, const InventoryItem &item);

float maximumListScroll(const GameplayCraftingBenchModel &model, const GameplayResolvedHudLayoutElement &list);
std::vector<GameplayCraftingBenchRowRect> visibleRows(
    const GameplayCraftingBenchModel &model,
    const GameplayResolvedHudLayoutElement &list,
    float scrollOffset);
size_t maximumMaterialScrollRow(const GameplayCraftingBenchModel &model, const GameplayResolvedHudLayoutElement &grid);
std::vector<GameplayCraftingBenchCellRect> visibleCells(
    const GameplayCraftingBenchModel &model,
    const GameplayResolvedHudLayoutElement &grid,
    size_t scrollRow);
// The option rows of the chosen step in the comparison area; none when the step has nothing to pick.
std::vector<GameplayCraftingBenchChoiceRect> choiceRows(
    const GameplayCraftingBenchModel &model,
    const GameplayResolvedHudLayoutElement &compare);
}
}
