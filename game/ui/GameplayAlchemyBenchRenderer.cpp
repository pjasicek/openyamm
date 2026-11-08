#include "game/ui/GameplayAlchemyBenchRenderer.h"
#include "engine/Localization.h"

#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/rules/GameRules.h"
#include "game/rules/ItemRules.h"
#include "game/tables/ItemTable.h"
#include "game/ui/GameplayAlchemyBenchView.h"
#include "game/ui/GameplayBenchPainter.h"
#include "game/ui/GameplayCraftingBenchRenderer.h"
#include "game/ui/GameplayCraftingBenchView.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayUiSkin.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
using namespace GameplayBenchColors;
using Rect = GameplayResolvedHudLayoutElement;

std::string itemName(const ItemTable &itemTable, uint32_t itemId)
{
    const ItemDefinition *pDefinition = itemTable.get(itemId);
    return pDefinition != nullptr ? Engine::localize(pDefinition->name) : "";
}

std::string statusHeadline(const GameplayAlchemyBenchModel &model)
{
    switch (model.preview.outcome)
    {
        case AlchemyPreviewOutcome::Incomplete:
            return Engine::tr("Choose two ingredients or a recipe.");
        case AlchemyPreviewOutcome::MissingIngredient:
            return Engine::tr("Not enough ingredients.");
        case AlchemyPreviewOutcome::Unknown:
            return Engine::tr("Untried mixture");
        case AlchemyPreviewOutcome::Known:
            return Engine::tr("Known recipe");
        case AlchemyPreviewOutcome::TooDifficult:
            return Engine::tr("Too difficult");
        case AlchemyPreviewOutcome::KnownExplosive:
            return Engine::tr("Known to explode");
    }

    return "";
}

std::string statusBody(const GameplayAlchemyBenchModel &model)
{
    const std::string alchemist = model.alchemistName.empty() ? Engine::tr("Nobody in the party") : model.alchemistName;
    const std::string mastery = model.alchemist.mastery == SkillMastery::None
        ? Engine::tr("no Alchemy skill")
        : GameplayAlchemyBenchView::masteryName(static_cast<uint8_t>(model.alchemist.mastery));

    switch (model.preview.outcome)
    {
        case AlchemyPreviewOutcome::Unknown:
            return model.alchemist.mastery == SkillMastery::None
                ? Engine::tr("Potions that clash explode, and without Alchemy skill so does any real recipe.")
                : Engine::tr("Potions that clash explode, and so does a recipe beyond {mastery} Alchemy.",
                    {{"mastery", mastery}});
        case AlchemyPreviewOutcome::Known:
        {
            std::string body = model.preview.requiredMastery > 1
                ? Engine::tr("Needs {mastery} Alchemy. Safe for {alchemist}.",
                    {{"mastery", GameplayAlchemyBenchView::masteryName(model.preview.requiredMastery)},
                        {"alchemist", alchemist}})
                : Engine::tr("Safe to mix.");
            if (model.preview.returnsBottle)
            {
                body += " " + Engine::tr("The empty bottle is returned.");
            }

            if (model.preview.charges > 1)
            {
                body += " " + Engine::trn("{count} drink.", "{count} drinks.", uint64_t(model.preview.charges),
                    {{"count", int64_t(model.preview.charges)}});
            }

            if (model.preview.resultPower < model.preview.minimumPower)
            {
                body += " " + Engine::tr("Works from power {power}.", {{"power", int64_t(model.preview.minimumPower)}});
            }

            return body;
        }
        case AlchemyPreviewOutcome::TooDifficult:
            return Engine::tr("Needs {mastery} Alchemy; {alchemist} has {current}.",
                {{"mastery", GameplayAlchemyBenchView::masteryName(model.preview.requiredMastery)},
                    {"alchemist", alchemist}, {"current", mastery}});
        case AlchemyPreviewOutcome::KnownExplosive:
            return Engine::tr("This mixture blew up before, and {alchemist} would fail it again.",
                {{"alchemist", alchemist}});
        default:
            return "";
    }
}

std::string countList(const std::vector<AlchemyItemCount> &counts, const ItemTable &itemTable)
{
    std::string list;

    for (const AlchemyItemCount &count : counts)
    {
        list += (list.empty() ? "" : Engine::tr(", "))
            + Engine::tr("{count} {item}",
                {{"count", int64_t(count.count)}, {"item", itemName(itemTable, count.itemId)}});
    }

    return list;
}

std::string chainBody(const GameplayAlchemyBenchModel &model, const ItemTable &itemTable)
{
    const AlchemyChainPlan &chain = *model.chain;

    if (model.chainMode)
    {
        std::string body = Engine::tr("Uses: {items}.", {{"items", countList(chain.used, itemTable)}});

        if (!chain.brewedFirst.empty())
        {
            body += " " + Engine::tr("Brews first: {items}.", {{"items", countList(chain.brewedFirst, itemTable)}});
        }

        return body;
    }

    const std::string name = itemName(itemTable, chain.blockItemId);

    switch (chain.block)
    {
        case AlchemyChainBlock::MissingBottle:
            return Engine::tr("No empty bottle left to fill.");
        case AlchemyChainBlock::MissingReagent:
            return Engine::tr("Missing a reagent for {potion}.", {{"potion", name}});
        case AlchemyChainBlock::UnknownRecipe:
            return Engine::tr("Unknown step: the {potion} recipe.", {{"potion", name}});
        case AlchemyChainBlock::NeedsMastery:
        {
            const auto entry = std::find_if(model.book.entries.begin(), model.book.entries.end(),
                [&chain](const AlchemyBookEntry &candidate)
                {
                    return candidate.resultItemId == chain.blockItemId;
                });
            return entry != model.book.entries.end()
                ? Engine::tr("{potion} needs {mastery} Alchemy.",
                    {{"potion", name}, {"mastery", GameplayAlchemyBenchView::masteryName(entry->requiredMastery)}})
                : Engine::tr("{potion} needs more Alchemy.", {{"potion", name}});
        }
        case AlchemyChainBlock::None:
            break;
    }

    return Engine::tr("Not enough ingredients.");
}

uint32_t statusColor(AlchemyPreviewOutcome outcome)
{
    switch (outcome)
    {
        case AlchemyPreviewOutcome::Known:
            return GameplayUiSkin::Bonus;
        case AlchemyPreviewOutcome::Unknown:
            return WarningTextColor;
        case AlchemyPreviewOutcome::TooDifficult:
        case AlchemyPreviewOutcome::MissingIngredient:
        case AlchemyPreviewOutcome::KnownExplosive:
            return GameplayUiSkin::Penalty;
        default:
            return DimTextColor;
    }
}
}

void GameplayAlchemyBenchRenderer::render(GameplayScreenRuntime &context, int width, int height)
{
    const GameplayUiController::CharacterScreenState &characterScreen = context.characterScreenReadOnly();
    const ItemTable *pItemTable = context.itemTable();

    if (!characterScreen.open
        || !characterScreen.alchemyBench.active
        || context.currentHudScreenState() != GameplayHudScreenState::Character
        || pItemTable == nullptr
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const std::optional<GameplayAlchemyBenchModel> model = GameplayAlchemyBenchView::buildModel(context);
    const GameplayBenchPainter painter(context, width, height);
    const std::optional<Rect> panel = painter.rect("AlchemyBenchPanel");

    if (!model || !panel)
    {
        return;
    }

    const GameplayUiController::AlchemyBenchState &state = characterScreen.alchemyBench;
    const AlchemyPreview &preview = model->preview;
    context.prepareHudView(width, height);
    // The pages under the bench must not answer item inspection.
    context.gameplayUiRuntime().clearRenderedInspectableHudItems();
    GameplayUiSkin::renderPanel(context, *panel, false, 0.75f);

    // With crafting the bench is the Workbench, with its Alchemy and Crafting tabs.
    const bool workbench = GameplayCraftingBenchView::available(context);
    painter.label("AlchemyBenchTitle", Engine::tr(workbench ? "Workbench" : "Alchemy Bench"));

    if (workbench)
    {
        painter.button("WorkbenchTabAlchemy", Engine::tr("Alchemy"), true, !state.craftingTab);
        painter.button("WorkbenchTabCrafting", Engine::tr("Crafting"), true, state.craftingTab);

        if (state.craftingTab)
        {
            GameplayCraftingBenchRenderer::render(context, painter);
            return;
        }
    }

    painter.label("AlchemyBenchRecipeHeader", Engine::tr("Recipes"));
    painter.label("AlchemyBenchRecipeCount", Engine::tr("{known} / {total} known",
        {{"known", int64_t(model->book.entries.size())}, {"total", int64_t(model->book.totalResultCount)}}));
    painter.chip("AlchemyBenchRecipeFilterBrewable", Engine::tr("Can brew"), !state.showAllRecipes);
    painter.chip("AlchemyBenchRecipeFilterAll", Engine::tr("All known"), state.showAllRecipes);

    if (const std::optional<Rect> search = painter.rect("AlchemyBenchRecipeSearch"))
    {
        painter.well(*search, state.recipeSearchActive ? SelectedBorderColor : WellBorderColor);

        if (!state.recipeSearchActive && painter.hovered(*search))
        {
            painter.fill(*search, HoverColor);
        }

        if (state.recipeSearch.empty() && !state.recipeSearchActive)
        {
            painter.text("AlchemyBenchRecipeSearch", *search, Engine::tr("Search recipes"), DisabledTextColor);
        }
        else
        {
            // A steady caret; blinking would need a clock the bench does not otherwise use.
            painter.text("AlchemyBenchRecipeSearch", *search,
                state.recipeSearch + (state.recipeSearchActive ? "_" : ""));
        }
    }

    if (const std::optional<Rect> list = painter.rect("AlchemyBenchRecipeList"))
    {
        painter.well(*list);
        const float maximumScroll = GameplayAlchemyBenchView::maximumRecipeScroll(*model, *list);
        const float scroll = std::clamp(state.recipeScrollOffset, 0.0f, maximumScroll);

        for (const GameplayAlchemyBenchRowRect &rowRect : GameplayAlchemyBenchView::visibleRows(*model, *list, scroll))
        {
            const GameplayAlchemyBenchRow &row = model->rows[rowRect.rowIndex];
            const Rect &area = rowRect.rect;
            const float s = area.scale;

            if (row.kind == GameplayAlchemyBenchRowKind::Header)
            {
                painter.text("AlchemyBenchIngredientHint", {area.x + 4 * s, area.y + s, area.width, area.height, s},
                    row.text, HeaderTextColor);
                continue;
            }

            if (row.kind == GameplayAlchemyBenchRowKind::Undiscovered)
            {
                painter.text("AlchemyBenchIngredientHint", {area.x + 4 * s, area.y + 3 * s, area.width, area.height, s},
                    row.text, DisabledTextColor);
                continue;
            }

            const AlchemyBookEntry &entry = model->book.entries[row.entryIndex];
            const bool selected = model->selectedEntryIndex == row.entryIndex;

            if (selected)
            {
                painter.fill(area, SelectedRowColor);
                painter.frame(area, SelectedBorderColor);
            }
            else if (painter.hovered(area))
            {
                painter.fill(area, HoverColor);
            }

            const uint32_t chainCount = model->chainCounts[row.entryIndex];
            const bool brewable = entry.masteryAllows && (entry.brewableCount > 0 || chainCount > 0);
            const uint32_t color = !entry.masteryAllows ? GameplayUiSkin::Penalty
                : brewable ? GameplayUiSkin::Ivory : DisabledTextColor;
            painter.itemIcon(pItemTable->get(entry.resultItemId), {area.x + 3 * s, area.y + 1.5f * s, 10 * s,
                14 * s, s});
            painter.text("AlchemyBenchRowLabel", {area.x + 17 * s, area.y + 3 * s, area.width - 60 * s,
                area.height, s}, itemName(*pItemTable, entry.resultItemId), color);
            // "1 +3": one from carried ingredients, three more by brewing missing ingredients first.
            const uint32_t extra = chainCount > entry.brewableCount ? chainCount - entry.brewableCount : 0;
            const std::string count = !entry.masteryAllows
                ? GameplayAlchemyBenchView::masteryName(entry.requiredMastery)
                : extra == 0 ? std::to_string(entry.brewableCount)
                : entry.brewableCount > 0 ? std::to_string(entry.brewableCount) + " +" + std::to_string(extra)
                : "+" + std::to_string(extra);

            if (std::find(state.newRecipeResultIds.begin(), state.newRecipeResultIds.end(), entry.resultItemId)
                != state.newRecipeResultIds.end())
            {
                painter.text("AlchemyBenchRowCount", {area.x, area.y + 3 * s, area.width - 24 * s, area.height, s},
                    Engine::tr("NEW"), GameplayUiSkin::Gold);
            }
            painter.text("AlchemyBenchRowCount", {area.x, area.y + 3 * s, area.width - 4 * s, area.height, s},
                count, color);
        }

        if (model->rows.empty())
        {
            painter.text("AlchemyBenchSlotNameLabel", {list->x, list->y + 10 * list->scale, list->width,
                12 * list->scale, list->scale},
                state.showAllRecipes ? Engine::tr("No recipes known yet.") : Engine::tr("Nothing to brew yet."),
                DimTextColor);
        }

        const float visibleHeight = list->height / list->scale - 2 * GameplayAlchemyBenchView::RecipeListPadding;
        GameplayUiSkin::renderScrollbar(context, *list, maximumScroll > 0 ? scroll / maximumScroll : 0.0f,
            model->rowsHeight > 0 ? visibleHeight / model->rowsHeight : 1.0f,
            context.interactionState().alchemyBenchScrollDrag == 1);
    }

    const bool previewNamesResult =
        preview.outcome == AlchemyPreviewOutcome::Known || preview.outcome == AlchemyPreviewOutcome::TooDifficult;
    painter.label("AlchemyBenchMixHeader", previewNamesResult
        ? Engine::tr("Mix: {potion}", {{"potion", itemName(*pItemTable, preview.resultItemId)}})
        : Engine::tr(preview.outcome == AlchemyPreviewOutcome::Unknown ? "Experiment" : "Mix"));

    if (model->alchemistName.empty())
    {
        painter.label("AlchemyBenchAlchemistLabel",
            Engine::tr("No alchemist: only bottle and reagent mixes are safe."));
    }
    else
    {
        painter.label("AlchemyBenchAlchemistLabel", Engine::tr("Alchemist: {name} - {mastery} {level} (best in party)",
            {{"name", model->alchemistName},
            {"mastery", GameplayAlchemyBenchView::masteryName(static_cast<uint8_t>(model->alchemist.mastery))},
            {"level", int64_t(model->alchemist.level)}}));
    }

    const GameplayOverlayInteractionState &interaction = context.interactionState();
    const uint32_t draggedItemId = interaction.alchemyBenchDragging ? interaction.alchemyBenchPressedTarget.itemId : 0;
    const auto addInspectable =
        [&context, pItemTable](uint32_t itemId, uint16_t power, const Rect &area)
        {
            const ItemDefinition *pDefinition = pItemTable->get(itemId);

            if (pDefinition == nullptr)
            {
                return;
            }

            GameplayRenderedInspectableHudItem inspectable = {};
            inspectable.objectDescriptionId = itemId;
            inspectable.hasItemState = true;
            inspectable.itemState.objectDescriptionId = itemId;
            inspectable.itemState.standardEnchantPower = power;
            inspectable.textureName = pDefinition->iconName;
            inspectable.x = area.x;
            inspectable.y = area.y;
            inspectable.width = area.width;
            inspectable.height = area.height;
            context.addRenderedInspectableHudItem(inspectable);
        };
    const uint64_t brewedElapsedTicks = SDL_GetTicks() - state.brewedTicks;
    const auto renderSlot =
        [&](const char *pLayoutId, uint32_t itemId, uint16_t power, bool heldSlot)
        {
            const std::optional<Rect> slot = painter.rect(pLayoutId);

            if (!slot)
            {
                return;
            }

            const float s = slot->scale;
            const bool highlighted = draggedItemId != 0 ? painter.hovered(*slot)
                : itemId != 0 && painter.hovered(*slot);
            painter.well(*slot, highlighted ? SelectedBorderColor : WellBorderColor);

            if (itemId == 0)
            {
                return;
            }

            // A used-up ingredient stays visible, faded, so the player still sees what was mixed.
            const AlchemyIngredient *pIngredient = AlchemyBenchRuntime::findIngredient(model->ingredients, itemId);
            const bool missing = pIngredient == nullptr
                || (heldSlot && state.targetItemId == state.heldItemId && pIngredient->count < 2);
            painter.itemIcon(pItemTable->get(itemId), {slot->x + 8 * s, slot->y + 6 * s, slot->width - 16 * s,
                slot->height - 12 * s, s}, missing ? 100 : 255);
            addInspectable(itemId,
                pIngredient != nullptr && pIngredient->kind == AlchemyIngredientKind::Potion ? power : 0, *slot);

            const Rect nameArea = {slot->x - 12 * s, slot->y + slot->height + 2 * s, slot->width + 24 * s, 11 * s, s};
            painter.text("AlchemyBenchSlotNameLabel", nameArea, itemName(*pItemTable, itemId),
                missing ? DisabledTextColor : GameplayUiSkin::Ivory);
            const bool powerKnown = preview.outcome != AlchemyPreviewOutcome::MissingIngredient
                && preview.outcome != AlchemyPreviewOutcome::Incomplete
                && power > 0;
            const bool brewedFirst = missing && model->chainMode;
            painter.text("AlchemyBenchSlotPowerLabel", {nameArea.x, nameArea.y + 10 * s, nameArea.width, 10 * s, s},
                brewedFirst ? Engine::tr("brewed first") : missing ? Engine::tr("missing")
                : powerKnown ? Engine::tr("power {power}", {{"power", int64_t(power)}}) : "",
                brewedFirst ? GameplayUiSkin::Gold : missing ? GameplayUiSkin::Penalty : DimTextColor);
        };

    renderSlot("AlchemyBenchTargetSlot", state.targetItemId, preview.targetPower, false);
    painter.label("AlchemyBenchPlusLabel", "+");
    renderSlot("AlchemyBenchHeldSlot", state.heldItemId, preview.heldPower, true);
    painter.label("AlchemyBenchEqualsLabel", "=");

    if (const std::optional<Rect> resultSlot = painter.rect("AlchemyBenchResultSlot"))
    {
        const float s = resultSlot->scale;
        const Rect nameArea = {resultSlot->x - 12 * s, resultSlot->y + resultSlot->height + 2 * s,
            resultSlot->width + 24 * s, 11 * s, s};
        const Rect banner = {resultSlot->x + s, resultSlot->y + s, resultSlot->width - 2 * s, 12 * s, s};
        const Rect bannerIconBox = {resultSlot->x + 8 * s, resultSlot->y + 14 * s, resultSlot->width - 16 * s,
            resultSlot->height - 18 * s, s};

        if (state.brewedExploded)
        {
            painter.well(*resultSlot, GameplayUiSkin::Penalty);
            painter.fill(banner, 0xa0000000u);
            painter.text("AlchemyBenchSlotNameLabel", {banner.x, banner.y + s, banner.width, banner.height, s},
                Engine::tr("Exploded!"), GameplayUiSkin::Penalty);
            painter.text("AlchemyBenchPlusLabel", *resultSlot, "!", GameplayUiSkin::Penalty);
            painter.text("AlchemyBenchSlotNameLabel", nameArea, Engine::tr("Exploded"), GameplayUiSkin::Penalty);
        }
        else if (state.brewedItemId != 0)
        {
            // What the last Mix produced, with a short glow; it stays until a slot changes.
            painter.well(*resultSlot, SelectedBorderColor);
            const float glowSeconds = state.brewedDiscovery ? 1.6f : 0.9f;
            const float elapsed = float(brewedElapsedTicks) * 0.001f;

            if (elapsed < glowSeconds)
            {
                const float strength = 1.0f - elapsed / glowSeconds;
                painter.fill(*resultSlot, (uint32_t(std::lround(0x90 * strength)) << 24) | 0x0050c8f0u);
            }

            painter.fill(banner, 0xa0000000u);
            const std::string bannerText = state.brewedDiscovery ? Engine::tr("New recipe!")
                : state.brewedCount > 1 ? Engine::tr("Brewed x{count}", {{"count", int64_t(state.brewedCount)}})
                : Engine::tr("Brewed");
            painter.text("AlchemyBenchSlotNameLabel", {banner.x, banner.y + s, banner.width, banner.height, s},
                bannerText, GameplayUiSkin::Gold);
            painter.itemIcon(pItemTable->get(state.brewedItemId), bannerIconBox);
            addInspectable(state.brewedItemId, state.brewedPower, *resultSlot);
            painter.text("AlchemyBenchSlotNameLabel", nameArea, itemName(*pItemTable, state.brewedItemId));
            painter.text("AlchemyBenchSlotPowerLabel", {nameArea.x, nameArea.y + 10 * s, nameArea.width, 10 * s, s},
                state.brewedPower > 0 ? Engine::tr("power {power}",
                    {{"power", int64_t(state.brewedPower)}}) : "", DimTextColor);
        }
        else if (model->chainMode)
        {
            const uint32_t chainResultItemId = model->chain->steps.back().resultItemId;
            painter.well(*resultSlot, SelectedBorderColor);
            painter.fill(banner, 0xa0000000u);
            painter.text("AlchemyBenchSlotNameLabel", {banner.x, banner.y + s, banner.width, banner.height, s},
                Engine::tr("Chain"), GameplayUiSkin::Gold);
            painter.itemIcon(pItemTable->get(chainResultItemId), bannerIconBox);
            addInspectable(chainResultItemId, model->chain->resultPower, *resultSlot);
            painter.text("AlchemyBenchSlotNameLabel", nameArea, itemName(*pItemTable, chainResultItemId));
            painter.text("AlchemyBenchSlotPowerLabel", {nameArea.x, nameArea.y + 10 * s, nameArea.width, 10 * s, s},
                model->chain->resultPower > 0
                    ? Engine::tr("power ~{power}", {{"power", int64_t(model->chain->resultPower)}}) : "",
                DimTextColor);
        }
        else if (previewNamesResult)
        {
            painter.well(*resultSlot, SelectedBorderColor);
            const bool tooDifficult = preview.outcome == AlchemyPreviewOutcome::TooDifficult;
            painter.itemIcon(pItemTable->get(preview.resultItemId), {resultSlot->x + 8 * s, resultSlot->y + 6 * s,
                resultSlot->width - 16 * s, resultSlot->height - 12 * s, s}, tooDifficult ? 110 : 255);

            if (!tooDifficult)
            {
                addInspectable(preview.resultItemId, preview.resultPower, *resultSlot);
            }

            painter.text("AlchemyBenchSlotNameLabel", nameArea, itemName(*pItemTable, preview.resultItemId));
            painter.text("AlchemyBenchSlotPowerLabel", {nameArea.x, nameArea.y + 10 * s, nameArea.width, 10 * s, s},
                tooDifficult
                    ? Engine::tr("needs {mastery}",
                        {{"mastery", GameplayAlchemyBenchView::masteryName(preview.requiredMastery)}})
                    : preview.resultPower > 0 ? Engine::tr("power {power}",
                        {{"power", int64_t(preview.resultPower)}}) : "",
                tooDifficult || preview.resultPower < preview.minimumPower ? GameplayUiSkin::Penalty : DimTextColor);
        }
        else if (preview.outcome == AlchemyPreviewOutcome::Unknown)
        {
            painter.well(*resultSlot);
            painter.text("AlchemyBenchPlusLabel", *resultSlot, "?");
            painter.text("AlchemyBenchSlotNameLabel", nameArea, Engine::tr("Unknown"));
        }
        else if (preview.outcome == AlchemyPreviewOutcome::KnownExplosive)
        {
            painter.well(*resultSlot, GameplayUiSkin::Penalty);
            painter.text("AlchemyBenchPlusLabel", *resultSlot, "!", GameplayUiSkin::Penalty);
            painter.text("AlchemyBenchSlotNameLabel", nameArea, Engine::tr("Explodes"), GameplayUiSkin::Penalty);
        }
        else
        {
            painter.well(*resultSlot);
        }
    }

    if (const std::optional<Rect> status = painter.rect("AlchemyBenchStatus"))
    {
        if (model->chain)
        {
            const float lineY = painter.paragraph("AlchemyBenchStatus",
                Engine::tr(model->chainMode ? "Brew chain" : "Can't brew yet"),
                model->chainMode ? GameplayUiSkin::Bonus : GameplayUiSkin::Penalty, status->y);
            painter.paragraph("AlchemyBenchStatus", chainBody(*model, *pItemTable), DimTextColor,
                lineY + 3 * status->scale);
        }
        else
        {
            const float lineY = painter.paragraph("AlchemyBenchStatus", statusHeadline(*model),
                statusColor(preview.outcome), status->y);
            const float bodyY =
                painter.paragraph("AlchemyBenchStatus", statusBody(*model), DimTextColor, lineY + 3 * status->scale);

            // What the potion will do at the power it comes out with, when the rules describe it (MAW).
            if (preview.outcome == AlchemyPreviewOutcome::Known && preview.resultItemId != 0)
            {
                InventoryItem result;
                result.objectDescriptionId = preview.resultItemId;
                result.standardEnchantPower = preview.resultPower;

                const std::optional<std::string> effect = boundGameRules().items.itemDescription(result, nullptr);
                float effectY = bodyY;

                if (effect)
                {
                    effectY = painter.paragraph("AlchemyBenchStatus", *effect, DimTextColor, bodyY + 3 * status->scale);
                }

                // A best-step potion (MAW's black potions): the step it reaches and who it would raise.
                const std::optional<AlchemyBenchTables> benchTables = GameplayAlchemyBenchView::tables(context);
                const PotionDefinition *pPotion = benchTables
                    ? benchTables->potionSettingTable.effects().find(preview.resultItemId)
                    : nullptr;
                const auto bestStepEffect = pPotion != nullptr
                    ? std::find_if(pPotion->effects.begin(), pPotion->effects.end(),
                        [](const PotionEffect &potionEffect)
                        {
                            return potionEffect.limit == PotionLimit::BestStep && potionEffect.amount.divisor > 0;
                        })
                    : std::vector<PotionEffect>::const_iterator {};

                if (pPotion != nullptr && bestStepEffect != pPotion->effects.end()
                    && context.partyReadOnly() != nullptr)
                {
                    const int step = preview.resultPower / bestStepEffect->amount.divisor;
                    std::string members;

                    for (const Character &member : context.partyReadOnly()->members())
                    {
                        const auto best = member.rulesetState.potionSteps.find(preview.resultItemId);
                        const int bestStep = best != member.rulesetState.potionSteps.end() ? best->second : 0;
                        members += (members.empty() ? "" : ", ")
                            + (bestStep >= step
                                ? Engine::tr("{name} already at step {step}",
                                    {{"name", member.name}, {"step", bestStep}})
                                : Engine::tr("{name} +{count} steps",
                                    {{"name", member.name}, {"count", step - bestStep}}));
                    }

                    const std::string ladder = members.empty()
                        ? Engine::tr("Step {step}", {{"step", step}})
                        : Engine::tr("Step {step}: {members}", {{"step", step}, {"members", members}});
                    painter.paragraph("AlchemyBenchStatus", ladder, DimTextColor, effectY + 3 * status->scale);
                }
            }
        }
    }

    const std::string mixLabel = model->chainMode ? Engine::tr("Brew chain")
        : preview.outcome == AlchemyPreviewOutcome::Unknown ? Engine::tr("Try Mix") : Engine::tr("Mix");
    const std::string mixAllLabel = model->chainMode
        ? (model->mixAllCount > 1 ? Engine::tr("Brew All ({count})", {{"count", int64_t(model->mixAllCount)}})
                                  : Engine::tr("Brew All"))
        : (model->mixAllCount > 1 ? Engine::tr("Mix All ({count})", {{"count", int64_t(model->mixAllCount)}})
                                  : Engine::tr("Mix All"));
    painter.button("AlchemyBenchMixButton", mixLabel, GameplayAlchemyBenchView::mixEnabled(*model));
    painter.button("AlchemyBenchMixAllButton",
        mixAllLabel,
        model->mixAllCount > 1);
    painter.button("AlchemyBenchClearButton", Engine::tr("Clear"), state.targetItemId != 0 || state.heldItemId != 0);
    painter.button("AlchemyBenchCloseButton", Engine::tr("Close"), true);

    painter.label("AlchemyBenchIngredientHeader", Engine::tr("Ingredients"));
    painter.label("AlchemyBenchIngredientHint", Engine::tr("whole party, click or drag to place"));
    const GameplayUiController::AlchemyIngredientFilter filter = state.ingredientFilter;
    painter.chip("AlchemyBenchIngredientFilterAll", Engine::tr("All"),
        filter == GameplayUiController::AlchemyIngredientFilter::All);
    painter.chip("AlchemyBenchIngredientFilterPotions", Engine::tr("Potions"),
        filter == GameplayUiController::AlchemyIngredientFilter::Potions);
    painter.chip("AlchemyBenchIngredientFilterReagents", Engine::tr("Reagents"),
        filter == GameplayUiController::AlchemyIngredientFilter::Reagents);

    if (const std::optional<Rect> grid = painter.rect("AlchemyBenchIngredientGrid"))
    {
        painter.well(*grid);
        const size_t maximumRow = GameplayAlchemyBenchView::maximumIngredientScrollRow(*model, *grid);
        const size_t scrollRow = std::min(state.ingredientScrollRow, maximumRow);

        const std::vector<GameplayAlchemyBenchCellRect> cells =
            GameplayAlchemyBenchView::visibleCells(*model, *grid, scrollRow);

        for (const GameplayAlchemyBenchCellRect &cell : cells)
        {
            const AlchemyIngredient &ingredient = model->ingredients[cell.ingredientIndex];
            const Rect &area = cell.rect;
            const float s = area.scale;
            const bool placed = ingredient.itemId == state.targetItemId || ingredient.itemId == state.heldItemId;
            painter.well(area, placed ? SelectedBorderColor : WellBorderColor);

            // The freshly brewed potion pulses twice where it landed.
            constexpr float PulseSeconds = 1.2f;
            const float pulseElapsed = float(brewedElapsedTicks) * 0.001f;

            if (ingredient.itemId == state.brewedItemId && pulseElapsed < PulseSeconds)
            {
                const float wave = std::abs(std::sin(pulseElapsed / PulseSeconds * 2.0f * 3.14159265f));
                const float strength = wave * (1.0f - pulseElapsed / PulseSeconds);
                painter.fill(area, (uint32_t(std::lround(0xa0 * strength)) << 24) | 0x0050c8f0u);
                painter.frame(area, GameplayUiSkin::Gold);
            }

            if (painter.hovered(area))
            {
                painter.fill(area, HoverColor);
            }

            const ItemDefinition *pDefinition = pItemTable->get(ingredient.itemId);
            const Rect iconBox = {area.x + 3 * s, area.y + 3 * s, area.width - 6 * s, area.height - 9 * s, s};
            painter.itemIcon(pDefinition, iconBox);
            painter.text("AlchemyBenchRowCount", {area.x, area.y + area.height - 10 * s, area.width - 2 * s,
                10 * s, s}, std::to_string(ingredient.count), GameplayUiSkin::Ivory);

            if (pDefinition != nullptr)
            {
                GameplayRenderedInspectableHudItem inspectable = {};
                inspectable.objectDescriptionId = ingredient.itemId;
                inspectable.hasItemState = true;
                inspectable.itemState.objectDescriptionId = ingredient.itemId;
                inspectable.itemState.standardEnchantPower =
                    ingredient.kind == AlchemyIngredientKind::Potion ? ingredient.bestPower : 0;
                inspectable.textureName = pDefinition->iconName;
                inspectable.x = area.x;
                inspectable.y = area.y;
                inspectable.width = area.width;
                inspectable.height = area.height;
                context.addRenderedInspectableHudItem(inspectable);
            }
        }

        if (model->visibleIngredients.empty())
        {
            painter.text("AlchemyBenchSlotNameLabel", {grid->x, grid->y + 10 * grid->scale, grid->width,
                12 * grid->scale, grid->scale}, Engine::tr("The party carries no bottles, reagents or potions."),
                DimTextColor);
        }

        const size_t visibleRows = GameplayAlchemyBenchView::ingredientVisibleRows(*grid);
        GameplayUiSkin::renderScrollbar(context, *grid, maximumRow > 0 ? float(scrollRow) / float(maximumRow) : 0.0f,
            float(visibleRows) / float(visibleRows + maximumRow), interaction.alchemyBenchScrollDrag == 2);
    }

    if (draggedItemId != 0)
    {
        if (const GameplayInputFrame *pInput = context.currentGameplayInputFrame())
        {
            const float s = panel->scale;
            const float iconWidth = GameplayAlchemyBenchView::IngredientCellWidth * s;
            const float iconHeight = GameplayAlchemyBenchView::IngredientCellHeight * s;
            painter.itemIcon(pItemTable->get(draggedItemId),
                {pInput->pointerX - iconWidth * 0.5f, pInput->pointerY - iconHeight * 0.5f, iconWidth, iconHeight, s});
        }
    }
}
}
