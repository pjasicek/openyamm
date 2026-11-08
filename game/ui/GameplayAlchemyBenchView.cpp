#include "game/ui/GameplayAlchemyBenchView.h"
#include "engine/Localization.h"

#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <cmath>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t MaxChainBrews = 99;

// Chain counts depend only on which items the party carries, the known recipes and what the alchemist may mix.
uint64_t chainCountsKey(const GameplayAlchemyBenchModel &model)
{
    uint64_t hash = 1469598103934665603ull;
    const auto mixIn =
        [&hash](uint64_t value)
        {
            hash = (hash ^ value) * 1099511628211ull;
        };

    for (const AlchemyIngredient &ingredient : model.ingredients)
    {
        mixIn((uint64_t(ingredient.itemId) << 32) | ingredient.count);
    }

    for (const AlchemyBookEntry &entry : model.book.entries)
    {
        mixIn((uint64_t(entry.resultItemId) << 32) | (uint64_t(entry.recipes.size()) << 1) | entry.masteryAllows);
    }

    return hash;
}

std::vector<uint32_t> cachedChainCounts(
    GameplayScreenRuntime &context,
    const Party &party,
    const GameplayAlchemyBenchModel &model,
    const AlchemyBenchTables &benchTables)
{
    GameplayUiController::AlchemyBenchState &state = context.characterScreen().alchemyBench;
    const uint64_t key = chainCountsKey(model);

    if (key != state.chainCountsKey || state.chainCounts.size() != model.book.entries.size())
    {
        const AlchemyChainPlanner planner(party, model.book, model.alchemist, benchTables);
        state.chainCounts.clear();

        for (const AlchemyBookEntry &entry : model.book.entries)
        {
            const uint32_t count = entry.masteryAllows ? planner.plan(entry.resultItemId, MaxChainBrews).brewCount : 0;
            state.chainCounts.push_back({entry.resultItemId, count});
        }

        state.chainCountsKey = key;
    }

    std::vector<uint32_t> counts;

    for (const auto &[resultItemId, count] : state.chainCounts)
    {
        counts.push_back(count);
    }

    return counts;
}

std::string tierHeader(const AlchemyBookEntry &entry)
{
    if (entry.reagentRecipe)
    {
        return Engine::tr("BOTTLE + REAGENT");
    }

    switch (entry.requiredMastery)
    {
        case 0:
        case 1:
            return Engine::tr("NORMAL");
        case 2:
            return Engine::tr("EXPERT");
        case 3:
            return Engine::tr("MASTER");
        default:
            return Engine::tr("GRANDMASTER");
    }
}
}

std::optional<AlchemyBenchTables> GameplayAlchemyBenchView::tables(const GameplayScreenRuntime &context)
{
    const ItemTable *pItemTable = context.itemTable();
    const PotionMixingTable *pPotionMixingTable = context.potionMixingTable();
    const PotionNoteTable *pPotionNoteTable = context.potionNoteTable();
    const MergedPotionSettingTable *pPotionSettingTable = context.mergedPotionSettingTable();
    const MergedReagentSettingTable *pReagentSettingTable = context.mergedReagentSettingTable();

    if (pItemTable == nullptr
        || pPotionMixingTable == nullptr
        || pPotionNoteTable == nullptr
        || pPotionSettingTable == nullptr
        || pReagentSettingTable == nullptr)
    {
        return std::nullopt;
    }

    return AlchemyBenchTables{
        *pItemTable, *pPotionMixingTable, *pPotionNoteTable, *pPotionSettingTable, *pReagentSettingTable};
}

std::optional<GameplayAlchemyBenchModel> GameplayAlchemyBenchView::buildModel(GameplayScreenRuntime &context)
{
    const Party *pParty = context.partyReadOnly();
    const std::optional<AlchemyBenchTables> benchTables = tables(context);

    if (pParty == nullptr || !benchTables)
    {
        return std::nullopt;
    }

    const GameplayUiController::AlchemyBenchState &state = context.characterScreenReadOnly().alchemyBench;
    std::unordered_map<uint32_t, bool> unlockedAutonotes;
    const AlchemyBenchRuntime::AutonoteLookup isAutonoteUnlocked =
        [&context, &unlockedAutonotes](uint32_t autonoteId)
        {
            auto found = unlockedAutonotes.find(autonoteId);

            if (found == unlockedAutonotes.end())
            {
                found = unlockedAutonotes.emplace(autonoteId, context.isAutonoteUnlocked(autonoteId)).first;
            }

            return found->second;
        };

    GameplayAlchemyBenchModel model = {};
    model.alchemist = AlchemyBenchRuntime::resolveAlchemist(*pParty);
    const Character *pAlchemist = model.alchemist.memberIndex ? pParty->member(*model.alchemist.memberIndex) : nullptr;
    model.alchemistName = pAlchemist != nullptr ? pAlchemist->name : "";
    model.ingredients = AlchemyBenchRuntime::collectIngredients(*pParty, *benchTables);

    for (size_t index = 0; index < model.ingredients.size(); ++index)
    {
        const AlchemyIngredientKind kind = model.ingredients[index].kind;
        const bool visible = state.ingredientFilter == GameplayUiController::AlchemyIngredientFilter::All
            || (state.ingredientFilter == GameplayUiController::AlchemyIngredientFilter::Potions
                && kind == AlchemyIngredientKind::Potion)
            || (state.ingredientFilter == GameplayUiController::AlchemyIngredientFilter::Reagents
                && kind != AlchemyIngredientKind::Potion);

        if (visible)
        {
            model.visibleIngredients.push_back(index);
        }
    }

    model.book =
        AlchemyBenchRuntime::buildBook(*benchTables, model.ingredients, model.alchemist.mastery, isAutonoteUnlocked);
    const AlchemyRecipe currentRecipe = {state.targetItemId, state.heldItemId};
    model.preview = AlchemyBenchRuntime::preview(*pParty, currentRecipe, *benchTables, isAutonoteUnlocked);
    model.chainCounts = cachedChainCounts(context, *pParty, model, *benchTables);
    const bool previewNamesResult = model.preview.outcome == AlchemyPreviewOutcome::Known
        || model.preview.outcome == AlchemyPreviewOutcome::TooDifficult;
    const uint32_t selectedResultItemId = previewNamesResult ? model.preview.resultItemId : state.selectedResultItemId;
    std::string lastHeader;

    for (size_t index = 0; index < model.book.entries.size(); ++index)
    {
        const AlchemyBookEntry &entry = model.book.entries[index];

        if (entry.resultItemId == selectedResultItemId)
        {
            model.selectedEntryIndex = index;
        }

        const ItemDefinition *pResult = benchTables->itemTable.get(entry.resultItemId);

        const bool brewable = entry.masteryAllows && (entry.brewableCount > 0 || model.chainCounts[index] > 0);

        if ((!state.showAllRecipes && !brewable)
            || !AlchemyBenchRuntime::matchesSearch(
                pResult != nullptr ? Engine::localize(pResult->name) : std::string(), state.recipeSearch))
        {
            continue;
        }

        const std::string header = tierHeader(entry);

        if (header != lastHeader)
        {
            model.rows.push_back(
                {GameplayAlchemyBenchRowKind::Header, 0, header, model.rowsHeight, RecipeHeaderHeight});
            model.rowsHeight += RecipeHeaderHeight;
            lastHeader = header;
        }

        model.rows.push_back({GameplayAlchemyBenchRowKind::Entry, index, "", model.rowsHeight, RecipeRowHeight});
        model.rowsHeight += RecipeRowHeight;
    }

    const size_t undiscovered = model.book.totalResultCount > model.book.entries.size()
        ? model.book.totalResultCount - model.book.entries.size()
        : 0;

    if (state.showAllRecipes && state.recipeSearch.empty() && undiscovered > 0)
    {
        model.rows.push_back({GameplayAlchemyBenchRowKind::Undiscovered, 0,
            Engine::tr("??? ({count} undiscovered)", {{"count", int64_t(undiscovered)}}), model.rowsHeight, RecipeRowHeight});
        model.rowsHeight += RecipeRowHeight;
    }

    if (model.selectedEntryIndex && model.preview.outcome == AlchemyPreviewOutcome::Known)
    {
        const AlchemyBookEntry &entry = model.book.entries[*model.selectedEntryIndex];

        if (entry.masteryAllows && entry.resultItemId == model.preview.resultItemId)
        {
            model.mixAllCount = entry.reagentRecipe
                ? entry.brewableCount
                : AlchemyBenchRuntime::brewableCount(currentRecipe, model.ingredients);
        }
    }

    // A chosen recipe the slots cannot mix directly is brewed as a chain, or explains what blocks it.
    const bool directMixPossible = model.preview.outcome == AlchemyPreviewOutcome::Known
        || model.preview.outcome == AlchemyPreviewOutcome::TooDifficult
        || model.preview.outcome == AlchemyPreviewOutcome::Unknown
        || model.preview.outcome == AlchemyPreviewOutcome::KnownExplosive;

    if (model.selectedEntryIndex && !directMixPossible
        && state.selectedResultItemId == model.book.entries[*model.selectedEntryIndex].resultItemId)
    {
        model.chain = planChain(context, model, state.selectedResultItemId, 1);
        model.chainMode = model.chain->brewCount > 0;

        if (model.chainMode)
        {
            model.mixAllCount = model.chainCounts[*model.selectedEntryIndex];
        }
    }

    return model;
}

AlchemyChainPlan GameplayAlchemyBenchView::planChain(
    const GameplayScreenRuntime &context,
    const GameplayAlchemyBenchModel &model,
    uint32_t resultItemId,
    uint32_t maxBrews)
{
    const Party *pParty = context.partyReadOnly();
    const std::optional<AlchemyBenchTables> benchTables = tables(context);

    if (pParty == nullptr || !benchTables)
    {
        return {};
    }

    return AlchemyChainPlanner(*pParty, model.book, model.alchemist, *benchTables).plan(resultItemId, maxBrews);
}

std::string GameplayAlchemyBenchView::masteryName(uint8_t mastery)
{
    switch (mastery)
    {
        case 0:
        case 1:
            return Engine::tr("Normal");
        case 2:
            return Engine::tr("Expert");
        case 3:
            return Engine::tr("Master");
        default:
            return Engine::tr("Grandmaster");
    }
}

bool GameplayAlchemyBenchView::mixEnabled(const GameplayAlchemyBenchModel &model)
{
    return model.chainMode
        || model.preview.outcome == AlchemyPreviewOutcome::Known
        || model.preview.outcome == AlchemyPreviewOutcome::Unknown;
}

float GameplayAlchemyBenchView::maximumRecipeScroll(
    const GameplayAlchemyBenchModel &model,
    const GameplayResolvedHudLayoutElement &list)
{
    const float visibleHeight = list.height / std::max(0.01f, list.scale) - 2 * RecipeListPadding;
    return std::max(0.0f, model.rowsHeight - visibleHeight);
}

std::vector<GameplayAlchemyBenchRowRect> GameplayAlchemyBenchView::visibleRows(
    const GameplayAlchemyBenchModel &model,
    const GameplayResolvedHudLayoutElement &list,
    float scrollOffset)
{
    std::vector<GameplayAlchemyBenchRowRect> rects;
    const float top = list.y + RecipeListPadding * list.scale;
    const float bottom = list.y + list.height - RecipeListPadding * list.scale;

    for (size_t index = 0; index < model.rows.size(); ++index)
    {
        const GameplayAlchemyBenchRow &row = model.rows[index];
        const float y = top + (row.offsetY - scrollOffset) * list.scale;
        const float height = row.height * list.scale;

        // Rows are whole or hidden, so text never spills past the well.
        if (y < top - 0.5f || y + height > bottom + 0.5f)
        {
            continue;
        }

        rects.push_back({index, {list.x + RecipeListPadding * list.scale, y,
            list.width - (2 * RecipeListPadding + 6) * list.scale, height, list.scale}});
    }

    return rects;
}

size_t GameplayAlchemyBenchView::ingredientColumns(const GameplayResolvedHudLayoutElement &grid)
{
    const float width = grid.width / std::max(0.01f, grid.scale) - 2 * IngredientGridPadding + IngredientCellGap;
    return std::max<size_t>(1, static_cast<size_t>(std::floor(width / (IngredientCellWidth + IngredientCellGap))));
}

size_t GameplayAlchemyBenchView::ingredientVisibleRows(const GameplayResolvedHudLayoutElement &grid)
{
    const float height = grid.height / std::max(0.01f, grid.scale) - 2 * IngredientGridPadding + IngredientCellGap;
    return std::max<size_t>(1, static_cast<size_t>(std::floor(height / (IngredientCellHeight + IngredientCellGap))));
}

size_t GameplayAlchemyBenchView::maximumIngredientScrollRow(
    const GameplayAlchemyBenchModel &model,
    const GameplayResolvedHudLayoutElement &grid)
{
    const size_t columns = ingredientColumns(grid);
    const size_t rows = (model.visibleIngredients.size() + columns - 1) / columns;
    const size_t visibleRows = ingredientVisibleRows(grid);
    return rows > visibleRows ? rows - visibleRows : 0;
}

std::vector<GameplayAlchemyBenchCellRect> GameplayAlchemyBenchView::visibleCells(
    const GameplayAlchemyBenchModel &model,
    const GameplayResolvedHudLayoutElement &grid,
    size_t scrollRow)
{
    std::vector<GameplayAlchemyBenchCellRect> rects;
    const size_t columns = ingredientColumns(grid);
    const size_t first = scrollRow * columns;
    const size_t last = std::min(model.visibleIngredients.size(), first + columns * ingredientVisibleRows(grid));

    for (size_t visibleIndex = first; visibleIndex < last; ++visibleIndex)
    {
        const size_t column = (visibleIndex - first) % columns;
        const size_t row = (visibleIndex - first) / columns;
        rects.push_back({model.visibleIngredients[visibleIndex], {
            grid.x + (IngredientGridPadding + column * (IngredientCellWidth + IngredientCellGap)) * grid.scale,
            grid.y + (IngredientGridPadding + row * (IngredientCellHeight + IngredientCellGap)) * grid.scale,
            IngredientCellWidth * grid.scale,
            IngredientCellHeight * grid.scale,
            grid.scale}});
    }

    return rects;
}
}
