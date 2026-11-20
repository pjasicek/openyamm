#include "game/gameplay/GameplayCraftingBenchInputController.h"

#include "engine/Utf8Text.h"
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
using Rect = GameplayResolvedHudLayoutElement;

GameplayAlchemyBenchPointerTarget findTarget(
    const GameplayScreenRuntime &context,
    const GameplayCraftingBenchModel &model,
    const GameplayInputFrame &input)
{
    const auto inside = [&context, &input](const char *pLayoutId) -> std::optional<Rect>
    {
        const std::optional<Rect> area =
            context.resolveHudLayoutElement(pLayoutId, input.screenWidth, input.screenHeight, 0, 0);
        return area && context.isPointerInsideResolvedElement(*area, input.pointerX, input.pointerY) ? area
                                                                                                     : std::nullopt;
    };

    struct ButtonTarget
    {
        const char *pLayoutId;
        TargetType type;
    };

    static constexpr ButtonTarget Buttons[] = {
        {"WorkbenchTabAlchemy", TargetType::AlchemyTab},
        {"WorkbenchTabCrafting", TargetType::CraftingTab},
        {"CraftingBenchCloseButton", TargetType::CloseButton},
        {"CharacterAlchemyButton", TargetType::CloseButton},
        {"CraftingBenchApplyButton", TargetType::CraftApplyButton},
        {"CraftingBenchApplyManyButton", TargetType::CraftApplyManyButton},
        {"CraftingBenchClearButton", TargetType::CraftClearButton},
        {"CraftingBenchItemSearch", TargetType::CraftSearch},
        {"CraftingBenchItemFilterAll", TargetType::CraftItemFilterAll},
        {"CraftingBenchItemFilterWorn", TargetType::CraftItemFilterWorn},
        {"CraftingBenchItemFilterPacks", TargetType::CraftItemFilterPacks},
        {"CraftingBenchMaterialFilterAll", TargetType::CraftMaterialFilterAll},
        {"CraftingBenchMaterialFilterGems", TargetType::CraftMaterialFilterGems},
        {"CraftingBenchMaterialFilterSpecial", TargetType::CraftMaterialFilterSpecial},
        {"CraftingBenchMaterialFilterPotions", TargetType::CraftMaterialFilterPotions},
        {"CraftingBenchCheapestGems", TargetType::CraftCheapestGems},
    };

    for (const ButtonTarget &button : Buttons)
    {
        if (inside(button.pLayoutId))
        {
            return {button.type, 0, 0};
        }
    }

    const GameplayUiController::CraftingBenchState &state = context.characterScreenReadOnly().alchemyBench.crafting;

    if (const std::optional<Rect> compare = inside("CraftingBenchCompare"))
    {
        for (const GameplayCraftingBenchChoiceRect &choice : GameplayCraftingBenchView::choiceRows(model, *compare))
        {
            if (context.isPointerInsideResolvedElement(choice.rect, input.pointerX, input.pointerY))
            {
                return {TargetType::CraftChoice, 0, choice.choiceIndex};
            }
        }
    }

    if (inside("CraftingBenchItemSlot"))
    {
        return {TargetType::CraftItemSlot,
            model.selectedTarget ? model.targets[*model.selectedTarget].item.objectDescriptionId : 0, 0};
    }

    if (inside("CraftingBenchMaterialSlot"))
    {
        return {TargetType::CraftMaterialSlot, state.material ? state.material->itemId : 0, 0};
    }

    if (const std::optional<Rect> list = inside("CraftingBenchItemList"))
    {
        const float scroll =
            std::clamp(state.listScrollOffset, 0.0f, GameplayCraftingBenchView::maximumListScroll(model, *list));

        for (const GameplayCraftingBenchRowRect &row : GameplayCraftingBenchView::visibleRows(model, *list, scroll))
        {
            const GameplayCraftingBenchRow &modelRow = model.rows[row.rowIndex];

            if (modelRow.kind == GameplayCraftingBenchRowKind::Item
                && context.isPointerInsideResolvedElement(row.rect, input.pointerX, input.pointerY))
            {
                return {TargetType::CraftItemRow, model.targets[modelRow.targetIndex].item.objectDescriptionId,
                    modelRow.targetIndex};
            }
        }
    }

    if (const std::optional<Rect> grid = inside("CraftingBenchMaterialGrid"))
    {
        const size_t scrollRow =
            std::min(state.materialScrollRow, GameplayCraftingBenchView::maximumMaterialScrollRow(model, *grid));

        for (const GameplayCraftingBenchCellRect &cell :
            GameplayCraftingBenchView::visibleCells(model, *grid, scrollRow))
        {
            if (context.isPointerInsideResolvedElement(cell.rect, input.pointerX, input.pointerY))
            {
                return {TargetType::CraftMaterial, model.materials[cell.materialIndex].key.itemId, cell.materialIndex};
            }
        }
    }

    return {};
}

void selectTarget(GameplayScreenRuntime &context, const GameplayCraftingBenchModel &model, size_t index)
{
    GameplayUiController::CraftingBenchState &state = context.characterScreen().alchemyBench.crafting;

    if (index < model.targets.size())
    {
        state.target = model.targets[index].ref;
        state.choice = 0;
        state.clearResult();
    }
}

void selectMaterial(GameplayScreenRuntime &context, const GameplayCraftingBenchModel &model, size_t index)
{
    GameplayUiController::CraftingBenchState &state = context.characterScreen().alchemyBench.crafting;

    if (index < model.materials.size())
    {
        state.material = model.materials[index].key;
        state.choice = 0;
        state.clearResult();
    }
}

// A row or material dropped on either slot goes where it belongs (an item into the item slot, a material into the
// material slot); a slot dragged off empties.
void drop(
    GameplayScreenRuntime &context,
    const GameplayCraftingBenchModel &model,
    const GameplayAlchemyBenchPointerTarget &source,
    const GameplayAlchemyBenchPointerTarget &destination)
{
    GameplayUiController::CraftingBenchState &state = context.characterScreen().alchemyBench.crafting;

    const bool onSlot =
        destination.type == TargetType::CraftItemSlot || destination.type == TargetType::CraftMaterialSlot;

    if (source.type == TargetType::CraftItemRow && onSlot)
    {
        selectTarget(context, model, source.index);
    }
    else if (source.type == TargetType::CraftMaterial && onSlot)
    {
        selectMaterial(context, model, source.index);
    }
    else if (source.type == TargetType::CraftItemSlot && destination.type != TargetType::CraftItemSlot)
    {
        state.target.reset();
        state.clearResult();
    }
    else if (source.type == TargetType::CraftMaterialSlot && destination.type != TargetType::CraftMaterialSlot)
    {
        state.material.reset();
        state.clearResult();
    }
}

void activate(
    GameplayScreenRuntime &context,
    const GameplayCraftingBenchModel &model,
    const GameplayAlchemyBenchPointerTarget &target)
{
    GameplayUiController::AlchemyBenchState &bench = context.characterScreen().alchemyBench;
    GameplayUiController::CraftingBenchState &state = bench.crafting;
    state.searchActive = target.type == TargetType::CraftSearch;
    const bool possible = model.step && model.step->result.possible;

    // Anything but Apply (Merge) drops a pending Apply (Merge) confirmation.
    const bool wasConfirming = state.confirmPending || state.mergePending;

    if (target.type != TargetType::CraftApplyButton)
    {
        state.confirmPending = false;
    }

    // With only a gem chosen, Apply merges one set and Apply All every set (after a confirmation).
    const bool gemOnly = !model.selectedTarget && !model.combine.steps.empty();
    const uint32_t merges = model.combine.steps.empty() ? 0 : model.combine.steps.front().merges;
    const bool mergeConfirmed = target.type == TargetType::CraftApplyManyButton && state.mergePending;

    if (target.type != TargetType::CraftApplyManyButton)
    {
        state.mergePending = false;
    }

    switch (target.type)
    {
        case TargetType::AlchemyTab:
            bench.craftingTab = false;
            break;
        case TargetType::CloseButton:
            bench.active = false;
            break;
        case TargetType::CraftApplyButton:
            if (gemOnly)
            {
                context.itemService().combineGems(context, false);
            }
            else if (possible && !model.step->result.confirmation.empty() && !state.confirmPending)
            {
                state.confirmPending = true;
            }
            else if (possible)
            {
                context.itemService().applyCraft(context, false);
            }
            break;
        case TargetType::CraftApplyManyButton:
            if (gemOnly && merges > 1)
            {
                // The first press says which gems merge; the second merges them.
                state.mergePending = !mergeConfirmed;

                if (mergeConfirmed)
                {
                    context.itemService().combineGems(context, true);
                }
            }
            else if (possible && model.step->result.confirmation.empty() && model.batch
                && model.batch->applications > 1)
            {
                context.itemService().applyCraft(context, true);
            }
            break;
        case TargetType::CraftClearButton:
            // Clear is Cancel while a confirmation waits.
            if (!wasConfirming)
            {
                state.target.reset();
                state.material.reset();
            }

            state.clearResult();
            break;
        case TargetType::CraftItemSlot:
            state.target.reset();
            state.clearResult();
            break;
        case TargetType::CraftMaterialSlot:
            state.material.reset();
            state.clearResult();
            break;
        case TargetType::CraftItemFilterAll:
            state.targetFilter = GameplayUiController::CraftingTargetFilter::All;
            state.listScrollOffset = 0;
            break;
        case TargetType::CraftItemFilterWorn:
            state.targetFilter = GameplayUiController::CraftingTargetFilter::Worn;
            state.listScrollOffset = 0;
            break;
        case TargetType::CraftItemFilterPacks:
            state.targetFilter = GameplayUiController::CraftingTargetFilter::Packs;
            state.listScrollOffset = 0;
            break;
        case TargetType::CraftMaterialFilterAll:
            state.materialFilter = GameplayUiController::CraftingMaterialFilter::All;
            state.materialScrollRow = 0;
            break;
        case TargetType::CraftMaterialFilterGems:
            state.materialFilter = GameplayUiController::CraftingMaterialFilter::Gems;
            state.materialScrollRow = 0;
            break;
        case TargetType::CraftMaterialFilterSpecial:
            state.materialFilter = GameplayUiController::CraftingMaterialFilter::Special;
            state.materialScrollRow = 0;
            break;
        case TargetType::CraftMaterialFilterPotions:
            state.materialFilter = GameplayUiController::CraftingMaterialFilter::Potions;
            state.materialScrollRow = 0;
            break;
        case TargetType::CraftCheapestGems:
            state.cheapestGems = !state.cheapestGems;
            break;
        case TargetType::CraftItemRow:
            selectTarget(context, model, target.index);
            break;
        case TargetType::CraftMaterial:
            selectMaterial(context, model, target.index);
            break;
        case TargetType::CraftChoice:
            // Picking again drops a pending confirmation (above), so Confirm always names the current pick.
            state.choice = target.index;
            break;
        default:
            break;
    }
}

// The Workbench's keys (CRAFTING_BENCH_DESIGN.md §7): Enter applies, Shift+Enter applies ×N (with a gem alone: merges
// one set, or all), Delete clears the slots, Up/Down step through the items and Left/Right through the materials.
// Key presses come once per press, so a held key steps once.
bool handleKeys(GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    const auto newlyPressed = [&input](SDL_Scancode scancode) { return input.scancodePressCount(scancode) > 0; };
    const bool enterPressed = newlyPressed(SDL_SCANCODE_RETURN) || newlyPressed(SDL_SCANCODE_KP_ENTER);
    const bool deletePressed = newlyPressed(SDL_SCANCODE_DELETE);
    const int itemStep = newlyPressed(SDL_SCANCODE_DOWN) ? 1 : newlyPressed(SDL_SCANCODE_UP) ? -1 : 0;
    const int materialStep = newlyPressed(SDL_SCANCODE_RIGHT) ? 1 : newlyPressed(SDL_SCANCODE_LEFT) ? -1 : 0;

    if (!enterPressed && !deletePressed && itemStep == 0 && materialStep == 0)
    {
        return false;
    }

    const std::optional<GameplayCraftingBenchModel> model = GameplayCraftingBenchView::buildModel(context);

    if (!model)
    {
        return true;
    }

    GameplayUiController::CraftingBenchState &state = context.characterScreen().alchemyBench.crafting;
    const auto stepIndex =
        [](auto current, const auto &entries, int step, const auto &selected) -> std::optional<size_t>
        {
            if (entries.empty())
            {
                return std::nullopt;
            }

            for (size_t index = 0; index < entries.size(); ++index)
            {
                if (current && selected(entries[index]) == *current)
                {
                    return size_t(std::clamp<int64_t>(int64_t(index) + step, 0, int64_t(entries.size()) - 1));
                }
            }

            return step > 0 ? size_t(0) : entries.size() - 1;
        };

    if (itemStep != 0)
    {
        if (const std::optional<size_t> index = stepIndex(state.target, model->targets, itemStep,
                [](const CraftTargetEntry &entry) { return entry.ref; }))
        {
            selectTarget(context, *model, *index);
        }
    }
    else if (materialStep != 0)
    {
        if (const std::optional<size_t> index = stepIndex(state.material, model->materials, materialStep,
                [](const CraftMaterialEntry &entry) { return entry.key; }))
        {
            selectMaterial(context, *model, *index);
        }
    }
    else
    {
        const bool shiftHeld = input.isScancodeHeld(SDL_SCANCODE_LSHIFT) || input.isScancodeHeld(SDL_SCANCODE_RSHIFT);
        activate(context, *model,
            {!enterPressed ? TargetType::CraftClearButton
                : shiftHeld ? TargetType::CraftApplyManyButton : TargetType::CraftApplyButton});
    }

    return true;
}

// Drags a scrollbar thumb or pages its track. Returns true while the scrollbar owns the pointer.
bool handleScrollbars(
    GameplayScreenRuntime &context,
    const GameplayCraftingBenchModel &model,
    const GameplayInputFrame &input,
    bool press)
{
    GameplayOverlayInteractionState &interaction = context.interactionState();
    GameplayUiController::CraftingBenchState &state = context.characterScreen().alchemyBench.crafting;
    const std::optional<Rect> list =
        context.resolveHudLayoutElement("CraftingBenchItemList", input.screenWidth, input.screenHeight, 0, 0);
    const std::optional<Rect> grid =
        context.resolveHudLayoutElement("CraftingBenchMaterialGrid", input.screenWidth, input.screenHeight, 0, 0);

    if (!list || !grid)
    {
        return false;
    }

    const float listMaximum = GameplayCraftingBenchView::maximumListScroll(model, *list);
    const float listVisible = list->height / list->scale - 2 * GameplayAlchemyBenchView::RecipeListPadding;
    const size_t gridMaximum = GameplayCraftingBenchView::maximumMaterialScrollRow(model, *grid);
    const size_t gridVisible = GameplayAlchemyBenchView::ingredientVisibleRows(*grid);
    const auto listThumb = [&]()
    {
        return GameplayUiSkin::scrollbarThumb(*list,
            listMaximum > 0 ? std::clamp(state.listScrollOffset, 0.0f, listMaximum) / listMaximum : 0.0f,
            model.rowsHeight > 0 ? listVisible / model.rowsHeight : 1.0f);
    };
    const auto gridThumb = [&]()
    {
        return GameplayUiSkin::scrollbarThumb(*grid,
            gridMaximum > 0 ? float(std::min(state.materialScrollRow, gridMaximum)) / float(gridMaximum) : 0.0f,
            float(gridVisible) / float(gridVisible + gridMaximum));
    };
    const auto fractionAt = [&input, &interaction](const Rect &track, const Rect &thumb)
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
            state.listScrollOffset = fractionAt(*list, listThumb()) * listMaximum;
        }
        else
        {
            state.materialScrollRow =
                static_cast<size_t>(std::lround(fractionAt(*grid, gridThumb()) * float(gridMaximum)));
        }

        return true;
    }

    if (!press)
    {
        return false;
    }

    const auto onTrack = [&context, &input](const Rect &area)
    {
        return context.isPointerInsideResolvedElement(area, input.pointerX, input.pointerY)
            && input.pointerX >= area.x + area.width - 8 * area.scale;
    };

    if (listMaximum > 0 && onTrack(*list))
    {
        const Rect thumb = listThumb();

        if (input.pointerY >= thumb.y && input.pointerY <= thumb.y + thumb.height)
        {
            interaction.alchemyBenchScrollDrag = 1;
            interaction.alchemyBenchScrollGrab = input.pointerY - thumb.y;
        }
        else
        {
            const float page = input.pointerY < thumb.y ? -listVisible : listVisible;
            state.listScrollOffset = std::clamp(state.listScrollOffset + page, 0.0f, listMaximum);
        }

        return true;
    }

    if (gridMaximum > 0 && onTrack(*grid))
    {
        const Rect thumb = gridThumb();
        const size_t row = std::min(state.materialScrollRow, gridMaximum);

        if (input.pointerY >= thumb.y && input.pointerY <= thumb.y + thumb.height)
        {
            interaction.alchemyBenchScrollDrag = 2;
            interaction.alchemyBenchScrollGrab = input.pointerY - thumb.y;
        }
        else
        {
            state.materialScrollRow = input.pointerY < thumb.y ? (row > gridVisible ? row - gridVisible : 0)
                                                               : std::min(row + gridVisible, gridMaximum);
        }

        return true;
    }

    return false;
}

void editSearch(GameplayUiController::CraftingBenchState &state, const GameplayInputFrame &input, bool enterPressed)
{
    constexpr size_t MaxSearchLength = 24;
    const std::string before = state.search;

    Engine::Utf8::appendPrintable(state.search, input.textInput, MaxSearchLength);

    for (uint16_t count = input.scancodePressCount(SDL_SCANCODE_BACKSPACE); count > 0; --count)
    {
        if (!state.search.empty())
        {
            Engine::Utf8::popBack(state.search);
        }
    }

    if (enterPressed)
    {
        state.searchActive = false;
    }

    if (state.search != before)
    {
        state.listScrollOffset = 0;
    }
}
}

void GameplayCraftingBenchInputController::handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    GameplayOverlayInteractionState &interaction = context.interactionState();
    GameplayUiController::CraftingBenchState &state = context.characterScreen().alchemyBench.crafting;
    const auto newlyPressed = [&context, &input](SDL_Scancode scancode)
    {
        return input.scancodePressCount(scancode) > 0
            || (input.isScancodeHeld(scancode) && context.previousKeyboardState()[scancode] == 0);
    };

    const bool enterPressed = newlyPressed(SDL_SCANCODE_RETURN) || newlyPressed(SDL_SCANCODE_KP_ENTER);

    if (state.searchActive)
    {
        editSearch(state, input, enterPressed);
    }
    else if (handleKeys(context, input))
    {
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
            && (source.type == TargetType::CraftItemRow || source.type == TargetType::CraftMaterial
                || source.type == TargetType::CraftItemSlot || source.type == TargetType::CraftMaterialSlot);
        const std::optional<Rect> panel =
            context.resolveHudLayoutElement("AlchemyBenchPanel", input.screenWidth, input.screenHeight, 0, 0);
        const float threshold = 6.0f * (panel ? panel->scale : 1.0f);

        if (draggable
            && std::hypot(input.pointerX - interaction.alchemyBenchPressX,
                   input.pointerY - interaction.alchemyBenchPressY)
                > threshold)
        {
            interaction.alchemyBenchDragging = true;
        }
    }

    if (!wheel && !press && !release && interaction.alchemyBenchScrollDrag == 0)
    {
        return;
    }

    const std::optional<GameplayCraftingBenchModel> model = GameplayCraftingBenchView::buildModel(context);

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
        const std::optional<Rect> list =
            context.resolveHudLayoutElement("CraftingBenchItemList", input.screenWidth, input.screenHeight, 0, 0);
        const std::optional<Rect> grid =
            context.resolveHudLayoutElement("CraftingBenchMaterialGrid", input.screenWidth, input.screenHeight, 0, 0);

        if (list && context.isPointerInsideResolvedElement(*list, input.pointerX, input.pointerY))
        {
            state.listScrollOffset = std::clamp(
                state.listScrollOffset - input.mouseWheelDelta * GameplayAlchemyBenchView::RecipeRowHeight * 3,
                0.0f,
                GameplayCraftingBenchView::maximumListScroll(*model, *list));
        }
        else if (grid && context.isPointerInsideResolvedElement(*grid, input.pointerX, input.pointerY))
        {
            const size_t maximumRow = GameplayCraftingBenchView::maximumMaterialScrollRow(*model, *grid);
            const size_t row = std::min(state.materialScrollRow, maximumRow);
            state.materialScrollRow =
                input.mouseWheelDelta > 0 ? (row > 0 ? row - 1 : 0) : std::min(row + 1, maximumRow);
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
