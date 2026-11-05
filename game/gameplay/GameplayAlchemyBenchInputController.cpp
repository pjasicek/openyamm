#include "game/gameplay/GameplayAlchemyBenchInputController.h"

#include "engine/Utf8Text.h"
#include "game/gameplay/GameplayCraftingBenchInputController.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayAlchemyBenchView.h"
#include "game/ui/GameplayCraftingBenchView.h"
#include "game/ui/GameplayUiSkin.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
using TargetType = GameplayAlchemyBenchPointerTargetType;

GameplayAlchemyBenchPointerTarget findTarget(
    const GameplayScreenRuntime &context,
    const GameplayAlchemyBenchModel &model,
    const GameplayInputFrame &input)
{
    const auto inside =
        [&context, &input](const char *pLayoutId) -> std::optional<GameplayResolvedHudLayoutElement>
        {
            const std::optional<GameplayResolvedHudLayoutElement> area =
                context.resolveHudLayoutElement(pLayoutId, input.screenWidth, input.screenHeight, 0, 0);
            return area && context.isPointerInsideResolvedElement(*area, input.pointerX, input.pointerY)
                ? area
                : std::nullopt;
        };

    struct ButtonTarget
    {
        const char *pLayoutId;
        TargetType type;
    };

    static constexpr ButtonTarget Buttons[] = {
        {"AlchemyBenchCloseButton", TargetType::CloseButton},
        {"CharacterAlchemyButton", TargetType::CloseButton},
        {"AlchemyBenchMixButton", TargetType::MixButton},
        {"AlchemyBenchMixAllButton", TargetType::MixAllButton},
        {"AlchemyBenchClearButton", TargetType::ClearButton},
        {"AlchemyBenchRecipeSearch", TargetType::RecipeSearch},
        {"AlchemyBenchRecipeFilterBrewable", TargetType::RecipeFilterBrewable},
        {"AlchemyBenchRecipeFilterAll", TargetType::RecipeFilterAll},
        {"AlchemyBenchIngredientFilterAll", TargetType::IngredientFilterAll},
        {"AlchemyBenchIngredientFilterPotions", TargetType::IngredientFilterPotions},
        {"AlchemyBenchIngredientFilterReagents", TargetType::IngredientFilterReagents},
    };

    for (const ButtonTarget &button : Buttons)
    {
        if (inside(button.pLayoutId))
        {
            return {button.type, 0};
        }
    }

    if (GameplayCraftingBenchView::available(context) && inside("WorkbenchTabCrafting"))
    {
        return {TargetType::CraftingTab, 0};
    }

    const GameplayUiController::AlchemyBenchState &state = context.characterScreenReadOnly().alchemyBench;

    if (inside("AlchemyBenchTargetSlot"))
    {
        return {TargetType::TargetSlot, state.targetItemId};
    }

    if (inside("AlchemyBenchHeldSlot"))
    {
        return {TargetType::HeldSlot, state.heldItemId};
    }

    if (const std::optional<GameplayResolvedHudLayoutElement> list = inside("AlchemyBenchRecipeList"))
    {
        const float scroll = std::clamp(state.recipeScrollOffset, 0.0f,
            GameplayAlchemyBenchView::maximumRecipeScroll(model, *list));

        for (const GameplayAlchemyBenchRowRect &row : GameplayAlchemyBenchView::visibleRows(model, *list, scroll))
        {
            const GameplayAlchemyBenchRow &modelRow = model.rows[row.rowIndex];

            if (modelRow.kind == GameplayAlchemyBenchRowKind::Entry
                && context.isPointerInsideResolvedElement(row.rect, input.pointerX, input.pointerY))
            {
                return {TargetType::RecipeRow, model.book.entries[modelRow.entryIndex].resultItemId};
            }
        }
    }

    if (const std::optional<GameplayResolvedHudLayoutElement> grid = inside("AlchemyBenchIngredientGrid"))
    {
        const size_t scrollRow = std::min(state.ingredientScrollRow,
            GameplayAlchemyBenchView::maximumIngredientScrollRow(model, *grid));

        for (const GameplayAlchemyBenchCellRect &cell : GameplayAlchemyBenchView::visibleCells(model, *grid, scrollRow))
        {
            if (context.isPointerInsideResolvedElement(cell.rect, input.pointerX, input.pointerY))
            {
                return {TargetType::Ingredient, model.ingredients[cell.ingredientIndex].itemId};
            }
        }
    }

    return {};
}

void placeInSlot(
    GameplayScreenRuntime &context,
    const GameplayAlchemyBenchModel &model,
    uint32_t &slotItemId,
    uint32_t otherSlotItemId,
    uint32_t itemId)
{
    const AlchemyIngredient *pIngredient = AlchemyBenchRuntime::findIngredient(model.ingredients, itemId);

    if (itemId == otherSlotItemId && (pIngredient == nullptr || pIngredient->count < 2))
    {
        context.setStatusBarEvent("The party carries only one of those.");
        return;
    }

    slotItemId = itemId;
    context.characterScreen().alchemyBench.selectedResultItemId = 0;
    context.characterScreen().alchemyBench.clearBrewResult();
}

// A clicked ingredient fills the target slot first, then the held slot.
void placeIngredient(
    GameplayScreenRuntime &context,
    const GameplayAlchemyBenchModel &model,
    uint32_t itemId)
{
    GameplayUiController::AlchemyBenchState &state = context.characterScreen().alchemyBench;

    if (state.targetItemId == 0)
    {
        placeInSlot(context, model, state.targetItemId, state.heldItemId, itemId);
    }
    else
    {
        placeInSlot(context, model, state.heldItemId, state.targetItemId, itemId);
    }
}

// Ingredients drop into the slot under the pointer. A slot item dropped on the other slot swaps them, and dropped
// anywhere else leaves its slot empty.
void drop(
    GameplayScreenRuntime &context,
    const GameplayAlchemyBenchModel &model,
    const GameplayAlchemyBenchPointerTarget &source,
    const GameplayAlchemyBenchPointerTarget &destination)
{
    GameplayUiController::AlchemyBenchState &state = context.characterScreen().alchemyBench;
    const bool onTarget = destination.type == TargetType::TargetSlot;
    const bool onHeld = destination.type == TargetType::HeldSlot;

    if (source.type == TargetType::Ingredient)
    {
        if (onTarget)
        {
            placeInSlot(context, model, state.targetItemId, state.heldItemId, source.itemId);
        }
        else if (onHeld)
        {
            placeInSlot(context, model, state.heldItemId, state.targetItemId, source.itemId);
        }

        return;
    }

    const bool fromTarget = source.type == TargetType::TargetSlot;

    if ((fromTarget && onHeld) || (!fromTarget && onTarget))
    {
        std::swap(state.targetItemId, state.heldItemId);
    }
    else if (!onTarget && !onHeld)
    {
        (fromTarget ? state.targetItemId : state.heldItemId) = 0;
    }

    state.selectedResultItemId = 0;
    state.clearBrewResult();
}

void activate(
    GameplayScreenRuntime &context,
    const GameplayAlchemyBenchModel &model,
    const GameplayAlchemyBenchPointerTarget &target)
{
    GameplayUiController::AlchemyBenchState &state = context.characterScreen().alchemyBench;
    state.recipeSearchActive = target.type == TargetType::RecipeSearch;

    switch (target.type)
    {
        case TargetType::RecipeSearch:
            break;
        case TargetType::CloseButton:
            state.active = false;
            break;
        case TargetType::MixButton:
            if (model.chainMode)
            {
                context.itemService().brewAlchemyChain(context, false);
            }
            else if (GameplayAlchemyBenchView::mixEnabled(model))
            {
                context.itemService().mixAlchemyBench(context, false);
            }
            break;
        case TargetType::MixAllButton:
            if (model.mixAllCount > 1 && model.chainMode)
            {
                context.itemService().brewAlchemyChain(context, true);
            }
            else if (model.mixAllCount > 1)
            {
                context.itemService().mixAlchemyBench(context, true);
            }
            break;
        case TargetType::ClearButton:
            state.clearBrewResult();
            state.targetItemId = 0;
            state.heldItemId = 0;
            state.selectedResultItemId = 0;
            break;
        case TargetType::TargetSlot:
            state.clearBrewResult();
            state.targetItemId = 0;
            state.selectedResultItemId = 0;
            break;
        case TargetType::HeldSlot:
            state.clearBrewResult();
            state.heldItemId = 0;
            state.selectedResultItemId = 0;
            break;
        case TargetType::RecipeFilterBrewable:
        case TargetType::RecipeFilterAll:
            state.showAllRecipes = target.type == TargetType::RecipeFilterAll;
            state.recipeScrollOffset = 0;
            break;
        case TargetType::IngredientFilterAll:
            state.ingredientFilter = GameplayUiController::AlchemyIngredientFilter::All;
            state.ingredientScrollRow = 0;
            break;
        case TargetType::IngredientFilterPotions:
            state.ingredientFilter = GameplayUiController::AlchemyIngredientFilter::Potions;
            state.ingredientScrollRow = 0;
            break;
        case TargetType::IngredientFilterReagents:
            state.ingredientFilter = GameplayUiController::AlchemyIngredientFilter::Reagents;
            state.ingredientScrollRow = 0;
            break;
        case TargetType::RecipeRow:
            for (const AlchemyBookEntry &entry : model.book.entries)
            {
                if (entry.resultItemId != target.itemId)
                {
                    continue;
                }

                // Carried ingredients first; otherwise the slots show the pair a chain would finally mix.
                std::optional<AlchemyRecipe> recipe = AlchemyBenchRuntime::pickRecipe(entry, model.ingredients);

                if (recipe && AlchemyBenchRuntime::brewableCount(*recipe, model.ingredients) == 0)
                {
                    const AlchemyChainPlan chain =
                        GameplayAlchemyBenchView::planChain(context, model, entry.resultItemId, 1);

                    if (chain.brewCount > 0)
                    {
                        recipe = chain.finalRecipe;
                    }
                }

                if (recipe)
                {
                    state.targetItemId = recipe->targetItemId;
                    state.heldItemId = recipe->heldItemId;
                }

                state.selectedResultItemId = entry.resultItemId;
                state.clearBrewResult();
                break;
            }
            break;
        case TargetType::Ingredient:
            placeIngredient(context, model, target.itemId);
            break;
        case TargetType::CraftingTab:
            state.craftingTab = true;
            break;
        default:
            break;
    }
}

// Drags a scrollbar thumb or pages its track. Returns true while the scrollbar owns the pointer.
bool handleScrollbars(
    GameplayScreenRuntime &context,
    const GameplayAlchemyBenchModel &model,
    const GameplayInputFrame &input,
    bool press)
{
    GameplayOverlayInteractionState &interaction = context.interactionState();
    GameplayUiController::AlchemyBenchState &state = context.characterScreen().alchemyBench;
    const std::optional<GameplayResolvedHudLayoutElement> list =
        context.resolveHudLayoutElement("AlchemyBenchRecipeList", input.screenWidth, input.screenHeight, 0, 0);
    const std::optional<GameplayResolvedHudLayoutElement> grid =
        context.resolveHudLayoutElement("AlchemyBenchIngredientGrid", input.screenWidth, input.screenHeight, 0, 0);

    if (!list || !grid)
    {
        return false;
    }

    const float recipeMaximum = GameplayAlchemyBenchView::maximumRecipeScroll(model, *list);
    const float recipeVisible = list->height / list->scale - 2 * GameplayAlchemyBenchView::RecipeListPadding;
    const size_t ingredientMaximum = GameplayAlchemyBenchView::maximumIngredientScrollRow(model, *grid);
    const size_t ingredientVisible = GameplayAlchemyBenchView::ingredientVisibleRows(*grid);
    const auto recipeThumb =
        [&]()
        {
            return GameplayUiSkin::scrollbarThumb(*list,
                recipeMaximum > 0 ? std::clamp(state.recipeScrollOffset, 0.0f, recipeMaximum) / recipeMaximum : 0.0f,
                model.rowsHeight > 0 ? recipeVisible / model.rowsHeight : 1.0f);
        };
    const auto ingredientThumb =
        [&]()
        {
            return GameplayUiSkin::scrollbarThumb(*grid,
                ingredientMaximum > 0 ? float(std::min(state.ingredientScrollRow, ingredientMaximum))
                    / float(ingredientMaximum) : 0.0f,
                float(ingredientVisible) / float(ingredientVisible + ingredientMaximum));
        };
    const auto fractionAt =
        [&input, &interaction](
            const GameplayResolvedHudLayoutElement &track,
            const GameplayResolvedHudLayoutElement &thumb)
        {
            const float travel = std::max(1.0f, track.height - thumb.height);
            return std::clamp((input.pointerY - track.y - interaction.alchemyBenchScrollGrab) / travel, 0.0f, 1.0f);
        };

    if (interaction.alchemyBenchScrollDrag != 0)
    {
        if (!input.leftMouseButton.held)
        {
            interaction.alchemyBenchScrollDrag = 0;
        }
        else if (interaction.alchemyBenchScrollDrag == 1)
        {
            state.recipeScrollOffset = fractionAt(*list, recipeThumb()) * recipeMaximum;
        }
        else
        {
            state.ingredientScrollRow =
                static_cast<size_t>(std::lround(fractionAt(*grid, ingredientThumb()) * float(ingredientMaximum)));
        }

        return true;
    }

    if (!press)
    {
        return false;
    }

    const auto onTrack =
        [&context, &input](const GameplayResolvedHudLayoutElement &area)
        {
            return context.isPointerInsideResolvedElement(area, input.pointerX, input.pointerY)
                && input.pointerX >= area.x + area.width - 8 * area.scale;
        };

    if (recipeMaximum > 0 && onTrack(*list))
    {
        const GameplayResolvedHudLayoutElement thumb = recipeThumb();

        if (input.pointerY >= thumb.y && input.pointerY <= thumb.y + thumb.height)
        {
            interaction.alchemyBenchScrollDrag = 1;
            interaction.alchemyBenchScrollGrab = input.pointerY - thumb.y;
        }
        else
        {
            const float page = input.pointerY < thumb.y ? -recipeVisible : recipeVisible;
            state.recipeScrollOffset = std::clamp(state.recipeScrollOffset + page, 0.0f, recipeMaximum);
        }

        return true;
    }

    if (ingredientMaximum > 0 && onTrack(*grid))
    {
        const GameplayResolvedHudLayoutElement thumb = ingredientThumb();
        const size_t row = std::min(state.ingredientScrollRow, ingredientMaximum);

        if (input.pointerY >= thumb.y && input.pointerY <= thumb.y + thumb.height)
        {
            interaction.alchemyBenchScrollDrag = 2;
            interaction.alchemyBenchScrollGrab = input.pointerY - thumb.y;
        }
        else
        {
            state.ingredientScrollRow = input.pointerY < thumb.y
                ? (row > ingredientVisible ? row - ingredientVisible : 0)
                : std::min(row + ingredientVisible, ingredientMaximum);
        }

        return true;
    }

    return false;
}

void scrollBrewedIntoView(GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    GameplayUiController::AlchemyBenchState &state = context.characterScreen().alchemyBench;
    state.brewedScrollPending = false;
    const std::optional<GameplayAlchemyBenchModel> model = GameplayAlchemyBenchView::buildModel(context);
    const std::optional<GameplayResolvedHudLayoutElement> grid =
        context.resolveHudLayoutElement("AlchemyBenchIngredientGrid", input.screenWidth, input.screenHeight, 0, 0);

    if (!model || !grid)
    {
        return;
    }

    for (size_t visibleIndex = 0; visibleIndex < model->visibleIngredients.size(); ++visibleIndex)
    {
        if (model->ingredients[model->visibleIngredients[visibleIndex]].itemId != state.brewedItemId)
        {
            continue;
        }

        const size_t row = visibleIndex / GameplayAlchemyBenchView::ingredientColumns(*grid);
        const size_t visibleRows = GameplayAlchemyBenchView::ingredientVisibleRows(*grid);

        if (row < state.ingredientScrollRow || row >= state.ingredientScrollRow + visibleRows)
        {
            state.ingredientScrollRow =
                std::min(row, GameplayAlchemyBenchView::maximumIngredientScrollRow(*model, *grid));
        }

        return;
    }
}

void editRecipeSearch(
    GameplayUiController::AlchemyBenchState &state,
    const GameplayInputFrame &input,
    bool enterPressed)
{
    constexpr size_t MaxSearchLength = 24;
    const std::string before = state.recipeSearch;

    Engine::Utf8::appendPrintable(state.recipeSearch, input.textInput, MaxSearchLength);

    for (uint16_t count = input.scancodePressCount(SDL_SCANCODE_BACKSPACE); count > 0; --count)
    {
        if (!state.recipeSearch.empty())
        {
            Engine::Utf8::popBack(state.recipeSearch);
        }
    }

    if (enterPressed)
    {
        state.recipeSearchActive = false;
    }

    if (state.recipeSearch != before)
    {
        state.recipeScrollOffset = 0;
    }
}
}

void GameplayAlchemyBenchInputController::handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    GameplayOverlayInteractionState &interaction = context.interactionState();
    GameplayUiController::AlchemyBenchState &state = context.characterScreen().alchemyBench;
    const auto newlyPressed =
        [&context, &input](SDL_Scancode scancode)
        {
            return input.scancodePressCount(scancode) > 0
                || (input.isScancodeHeld(scancode) && context.previousKeyboardState()[scancode] == 0);
        };

    const bool crafting = state.craftingTab && GameplayCraftingBenchView::available(context);
    bool &searchActive = crafting ? state.crafting.searchActive : state.recipeSearchActive;

    if (newlyPressed(SDL_SCANCODE_ESCAPE))
    {
        // Escape first leaves the search field, then closes the bench.
        if (searchActive)
        {
            searchActive = false;
        }
        else
        {
            state.active = false;
        }

        interaction.menuToggleLatch = true;
        interaction.alchemyBenchEscapeLatch = true;
        return;
    }

    if (!searchActive && newlyPressed(SDL_SCANCODE_E))
    {
        // The inventory key closes the whole character screen, as it does without the bench.
        context.closeCharacterScreen();
        interaction.menuToggleLatch = true;
        interaction.closeOverlayLatch = true;
        return;
    }

    // Tab switches the Workbench's tabs (CRAFTING_BENCH_DESIGN.md §7). Toggles and steps count key presses, which
    // come once per press.
    if (!searchActive && input.scancodePressCount(SDL_SCANCODE_TAB) > 0
        && GameplayCraftingBenchView::available(context))
    {
        state.craftingTab = !crafting;
        return;
    }

    if (crafting)
    {
        GameplayCraftingBenchInputController::handleInput(context, input);
        return;
    }

    if (state.brewedScrollPending)
    {
        scrollBrewedIntoView(context, input);
    }

    const bool enterPressed = newlyPressed(SDL_SCANCODE_RETURN) || newlyPressed(SDL_SCANCODE_KP_ENTER);

    if (state.recipeSearchActive)
    {
        editRecipeSearch(state, input, enterPressed);
    }
    else if (input.scancodePressCount(SDL_SCANCODE_RETURN) > 0 || input.scancodePressCount(SDL_SCANCODE_KP_ENTER) > 0
        || input.scancodePressCount(SDL_SCANCODE_DELETE) > 0)
    {
        // Enter mixes, Shift+Enter mixes all, Delete clears the slots.
        const std::optional<GameplayAlchemyBenchModel> model = GameplayAlchemyBenchView::buildModel(context);
        const bool shiftHeld = input.isScancodeHeld(SDL_SCANCODE_LSHIFT) || input.isScancodeHeld(SDL_SCANCODE_RSHIFT);

        const bool mix = input.scancodePressCount(SDL_SCANCODE_DELETE) == 0;

        if (model)
        {
            activate(context, *model,
                {!mix ? TargetType::ClearButton : shiftHeld ? TargetType::MixAllButton : TargetType::MixButton});
        }

        return;
    }

    const bool wheel = input.mouseWheelDelta != 0;
    const bool press = input.leftMouseButton.held && !interaction.alchemyBenchClickLatch;
    const bool release = !input.leftMouseButton.held && interaction.alchemyBenchClickLatch;
    const bool holding = input.leftMouseButton.held && interaction.alchemyBenchClickLatch;

    if (holding && !interaction.alchemyBenchDragging && interaction.alchemyBenchScrollDrag == 0)
    {
        const GameplayAlchemyBenchPointerTarget &source = interaction.alchemyBenchPressedTarget;
        const bool draggable = source.itemId != 0
            && (source.type == TargetType::Ingredient
                || source.type == TargetType::TargetSlot
                || source.type == TargetType::HeldSlot);
        const std::optional<GameplayResolvedHudLayoutElement> panel =
            context.resolveHudLayoutElement("AlchemyBenchPanel", input.screenWidth, input.screenHeight, 0, 0);
        const float threshold = 6.0f * (panel ? panel->scale : 1.0f);

        if (draggable
            && std::hypot(input.pointerX - interaction.alchemyBenchPressX,
                input.pointerY - interaction.alchemyBenchPressY) > threshold)
        {
            interaction.alchemyBenchDragging = true;
        }
    }

    if (!wheel && !press && !release && interaction.alchemyBenchScrollDrag == 0)
    {
        return;
    }

    const std::optional<GameplayAlchemyBenchModel> model = GameplayAlchemyBenchView::buildModel(context);

    if (!model)
    {
        return;
    }

    if (handleScrollbars(context, *model, input, press))
    {
        interaction.alchemyBenchClickLatch = input.leftMouseButton.held;
        interaction.alchemyBenchPressedTarget = {};
        return;
    }

    if (wheel)
    {
        const std::optional<GameplayResolvedHudLayoutElement> list =
            context.resolveHudLayoutElement("AlchemyBenchRecipeList", input.screenWidth, input.screenHeight, 0, 0);
        const std::optional<GameplayResolvedHudLayoutElement> grid =
            context.resolveHudLayoutElement("AlchemyBenchIngredientGrid", input.screenWidth, input.screenHeight, 0, 0);

        if (list && context.isPointerInsideResolvedElement(*list, input.pointerX, input.pointerY))
        {
            state.recipeScrollOffset = std::clamp(
                state.recipeScrollOffset - input.mouseWheelDelta * GameplayAlchemyBenchView::RecipeRowHeight * 3,
                0.0f,
                GameplayAlchemyBenchView::maximumRecipeScroll(*model, *list));
        }
        else if (grid && context.isPointerInsideResolvedElement(*grid, input.pointerX, input.pointerY))
        {
            const size_t maximumRow = GameplayAlchemyBenchView::maximumIngredientScrollRow(*model, *grid);
            const size_t row = std::min(state.ingredientScrollRow, maximumRow);
            state.ingredientScrollRow = input.mouseWheelDelta > 0
                ? (row > 0 ? row - 1 : 0)
                : std::min(row + 1, maximumRow);
        }
    }

    if (press)
    {
        interaction.alchemyBenchClickLatch = true;
        interaction.alchemyBenchPressedTarget = findTarget(context, *model, input);
        interaction.alchemyBenchPressX = input.pointerX;
        interaction.alchemyBenchPressY = input.pointerY;
        interaction.alchemyBenchDragging = false;
    }
    else if (release)
    {
        const GameplayAlchemyBenchPointerTarget target = findTarget(context, *model, input);
        const GameplayAlchemyBenchPointerTarget source = interaction.alchemyBenchPressedTarget;
        const bool dragged = interaction.alchemyBenchDragging;
        interaction.alchemyBenchClickLatch = false;
        interaction.alchemyBenchPressedTarget = {};
        interaction.alchemyBenchDragging = false;

        if (dragged)
        {
            drop(context, *model, source, target);
        }
        else if (target == source)
        {
            activate(context, *model, target);
        }
    }
}
}
