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

// A slot's power button: the powers its item is carried at and the player's choice among them.
struct GameplayAlchemyBenchSlotPowers
{
    // Strongest first, without the copy the other slot's choice takes. The button shows with two or more; empty
    // while the slots mix nothing directly (an empty or missing ingredient, a chain). The result slot's are the
    // powers a chain can aim at, without counts, and empty unless the bench brews a chain.
    std::vector<AlchemyPowerOption> options;
    // The player's choice, while a carried copy has that power (or the chain reaches it); otherwise the bench picks.
    std::optional<uint16_t> chosen;
    // The power of the copy the mix takes, or of the potion the chain brews.
    uint16_t power = 0;
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
    // The copies the player chose for the slots (their power buttons), as the preview and the mix use them.
    AlchemyPowerChoice powerChoice;
    GameplayAlchemyBenchSlotPowers targetPowers;
    GameplayAlchemyBenchSlotPowers heldPowers;
    GameplayAlchemyBenchSlotPowers resultPowers;
    // The slot whose power list is open: 0 none, 1 target, 2 held, 3 result.
    uint8_t powerListSlot = 0;
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

// A row of an open power list: row 0 is Automatic, row n the slot's option n - 1.
struct GameplayAlchemyBenchPowerRowRect
{
    size_t rowIndex = 0;
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
constexpr float PowerListRowHeight = 11.0f;
constexpr float PowerListPadding = 2.0f;
constexpr size_t PowerListVisibleRows = 9;

std::optional<AlchemyBenchTables> tables(const GameplayScreenRuntime &context);
// Not const: the bench state caches the book's chain counts.
std::optional<GameplayAlchemyBenchModel> buildModel(GameplayScreenRuntime &context);
// The chain that brews the potion from the strongest ingredients, or at the power chosen from the result slot's list
// (AlchemyChainPlanner::powerOptions); a power the chain no longer reaches plans as no choice.
AlchemyChainPlan planChain(
    const GameplayScreenRuntime &context,
    const GameplayAlchemyBenchModel &model,
    uint32_t resultItemId,
    uint32_t maxBrews,
    const std::optional<uint16_t> &power = std::nullopt);
std::string masteryName(uint8_t mastery);
bool mixEnabled(const GameplayAlchemyBenchModel &model);

float maximumRecipeScroll(const GameplayAlchemyBenchModel &model, const GameplayResolvedHudLayoutElement &list);
std::vector<GameplayAlchemyBenchRowRect> visibleRows(
    const GameplayAlchemyBenchModel &model,
    const GameplayResolvedHudLayoutElement &list,
    float scrollOffset);

// The slots with a power list, by number: 1 target, 2 held, 3 result.
constexpr uint8_t PowerListSlotCount = 3;
const char *powerListSlotLayoutId(uint8_t slot);
const GameplayAlchemyBenchSlotPowers &slotPowers(const GameplayAlchemyBenchModel &model, uint8_t slot);
// The button under a slot that tells the power its copy has and opens the list of the powers carried.
bool powerButtonShown(const GameplayAlchemyBenchSlotPowers &powers);
GameplayResolvedHudLayoutElement powerButton(const GameplayResolvedHudLayoutElement &slot);
// The open list under that button: Automatic, then one row per power. The wheel scrolls a long one by rows.
size_t maximumPowerListScroll(const GameplayAlchemyBenchSlotPowers &powers);
GameplayResolvedHudLayoutElement powerList(
    const GameplayAlchemyBenchSlotPowers &powers,
    const GameplayResolvedHudLayoutElement &slot);
std::vector<GameplayAlchemyBenchPowerRowRect> powerListRows(
    const GameplayAlchemyBenchSlotPowers &powers,
    const GameplayResolvedHudLayoutElement &slot,
    size_t scrollRow);

size_t ingredientColumns(const GameplayResolvedHudLayoutElement &grid);
size_t ingredientVisibleRows(const GameplayResolvedHudLayoutElement &grid);
size_t maximumIngredientScrollRow(const GameplayAlchemyBenchModel &model, const GameplayResolvedHudLayoutElement &grid);
std::vector<GameplayAlchemyBenchCellRect> visibleCells(
    const GameplayAlchemyBenchModel &model,
    const GameplayResolvedHudLayoutElement &grid,
    size_t scrollRow);
}
}
