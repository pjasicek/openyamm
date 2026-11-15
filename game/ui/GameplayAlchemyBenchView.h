#pragma once

#include "game/items/AlchemyBenchRuntime.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

enum class GameplayAlchemyBenchRowKind : uint8_t
{
    Header,
    Entry,
    Undiscovered
};

struct GameplayAlchemyBenchRow
{
    GameplayAlchemyBenchRowKind kind = GameplayAlchemyBenchRowKind::Entry;
    size_t entryIndex = 0;
    std::string text;
    float offsetY = 0;
    float height = 0;
};

// What the bench shows this frame, shared by its renderer and its input.
struct GameplayAlchemyBenchModel
{
    AlchemistInfo alchemist;
    std::string alchemistName;
    std::vector<AlchemyIngredient> ingredients;
    // What the book's recipes are picked from: the ingredients, without the mixed potions while the Workbench keeps
    // them (GameSettings::workbenchKeepMixedPotions).
    bool keepMixedPotions = false;
    std::vector<AlchemyIngredient> mixingIngredients;
    std::vector<size_t> visibleIngredients;
    AlchemyBook book;
    std::vector<GameplayAlchemyBenchRow> rows;
    float rowsHeight = 0;
    AlchemyPreview preview;
    std::optional<size_t> selectedEntryIndex;
    uint32_t mixAllCount = 0;
    // Potions each book entry can brew when missing ingredients are brewed first.
    std::vector<uint32_t> chainCounts;
    // The selected recipe needs ingredients brewed first; chain is the plan for one potion.
    bool chainMode = false;
    std::optional<AlchemyChainPlan> chain;
    // The slots hold a book recipe that would use carried mixed potions the Workbench keeps, and no chain can brew
    // them: Mix stays off.
    bool keptPotionsBlockMix = false;
};

struct GameplayAlchemyBenchRowRect
{
    size_t rowIndex = 0;
    GameplayResolvedHudLayoutElement rect;
};

struct GameplayAlchemyBenchCellRect
{
    size_t ingredientIndex = 0;
    GameplayResolvedHudLayoutElement rect;
};

namespace GameplayAlchemyBenchView
{
constexpr float RecipeRowHeight = 17.0f;
constexpr float RecipeHeaderHeight = 10.0f;
constexpr float RecipeListPadding = 3.0f;
constexpr float IngredientCellWidth = 44.0f;
constexpr float IngredientCellHeight = 56.0f;
constexpr float IngredientCellGap = 3.0f;
constexpr float IngredientGridPadding = 3.0f;

std::optional<AlchemyBenchTables> tables(const GameplayScreenRuntime &context);
// Not const: the bench state caches the book's chain counts.
std::optional<GameplayAlchemyBenchModel> buildModel(GameplayScreenRuntime &context);
AlchemyChainPlan planChain(
    const GameplayScreenRuntime &context,
    const GameplayAlchemyBenchModel &model,
    uint32_t resultItemId,
    uint32_t maxBrews);
std::string masteryName(uint8_t mastery);
bool mixEnabled(const GameplayAlchemyBenchModel &model);

float maximumRecipeScroll(const GameplayAlchemyBenchModel &model, const GameplayResolvedHudLayoutElement &list);
std::vector<GameplayAlchemyBenchRowRect> visibleRows(
    const GameplayAlchemyBenchModel &model,
    const GameplayResolvedHudLayoutElement &list,
    float scrollOffset);

size_t ingredientColumns(const GameplayResolvedHudLayoutElement &grid);
size_t ingredientVisibleRows(const GameplayResolvedHudLayoutElement &grid);
size_t maximumIngredientScrollRow(const GameplayAlchemyBenchModel &model, const GameplayResolvedHudLayoutElement &grid);
std::vector<GameplayAlchemyBenchCellRect> visibleCells(
    const GameplayAlchemyBenchModel &model,
    const GameplayResolvedHudLayoutElement &grid,
    size_t scrollRow);
}
}
