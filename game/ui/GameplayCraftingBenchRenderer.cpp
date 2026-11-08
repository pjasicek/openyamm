#include "game/ui/GameplayCraftingBenchRenderer.h"
#include "engine/Localization.h"

#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/rules/GameRules.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/ui/GameplayAlchemyBenchView.h"
#include "game/ui/GameplayBenchPainter.h"
#include "game/ui/GameplayCraftingBenchView.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
using namespace GameplayBenchColors;
using Rect = GameplayResolvedHudLayoutElement;
using TargetFilter = GameplayUiController::CraftingTargetFilter;
using MaterialFilter = GameplayUiController::CraftingMaterialFilter;

uint32_t abgrFromRgb(uint32_t rgb)
{
    return 0xff000000u | ((rgb & 0xffu) << 16) | (rgb & 0xff00u) | ((rgb >> 16) & 0xffu);
}

struct CompareLine
{
    std::string text;
    uint32_t color = DimTextColor;
};

// What the item inspect popup says about an item, line by line, for the before and after comparison.
std::vector<CompareLine> itemLines(const GameplayScreenRuntime &context, const InventoryItem &item)
{
    std::vector<CompareLine> lines;
    const ItemDefinition *pDefinition =
        context.itemTable() != nullptr ? context.itemTable()->get(item.objectDescriptionId) : nullptr;

    if (pDefinition == nullptr)
    {
        return lines;
    }

    const Party *pParty = context.partyReadOnly();
    const ItemRules &itemRules = gameRulesFor(pParty).items;
    const Character *pViewer = pParty != nullptr ? pParty->member(pParty->activeMemberIndex()) : nullptr;
    lines.push_back({GameplayCraftingBenchView::itemDisplayName(context, item), GameplayUiSkin::Ivory});

    // Like the inspect popup, an unidentified item tells nothing beyond its generic name.
    if (!item.identified && ItemRuntime::requiresIdentification(*pDefinition))
    {
        lines.push_back({Engine::tr("Not identified"), WarningTextColor});
        return lines;
    }

    if (const std::optional<ItemBaseStats> stats =
            itemRules.baseStats(*pDefinition, item.rulesetFields, pViewer != nullptr ? int(pViewer->level) : 1))
    {
        if (stats->maximumDamage > 0)
        {
            lines.push_back({Engine::tr("Damage {minimum}-{maximum}", {{"minimum", int64_t(stats->minimumDamage)},
                {"maximum", int64_t(stats->maximumDamage)}})});
        }
        else if (stats->armorClass > 0)
        {
            lines.push_back({Engine::tr("Armour {armour}", {{"armour", int64_t(stats->armorClass)}})});
        }
    }

    for (const ItemInspectLine &line : itemRules.inspectLines(
             item, *pDefinition, context.standardItemEnchantTable(), context.specialItemEnchantTable(), pViewer))
    {
        lines.push_back({line.text, abgrFromRgb(line.color)});
    }

    const MergedPotionSettingTable *pPotions = context.mergedPotionSettingTable();
    const PotionDefinition *pPotion =
        pPotions != nullptr ? pPotions->effects().find(item.objectDescriptionId) : nullptr;

    if (pPotion != nullptr && pPotion->charges > 1)
    {
        const int uses = item.currentCharges > 0 ? int(item.currentCharges) : pPotion->charges;
        lines.push_back({Engine::tr("Uses {uses}", {{"uses", int64_t(uses)}})});
    }

    if (item.rulesetFields.qualityPercent > 0)
    {
        lines.push_back({Engine::tr("Quality +{percent} %",
            {{"percent", int64_t(item.rulesetFields.qualityPercent)}})});
    }

    lines.push_back({Engine::tr("Value {value}", {{"value", int64_t(itemRules.itemValue(item, *pDefinition,
        context.standardItemEnchantTable(), context.specialItemEnchantTable(), 1))}})});
    return lines;
}

void addInspectable(GameplayScreenRuntime &context, const InventoryItem &item, const Rect &area)
{
    const ItemDefinition *pDefinition =
        context.itemTable() != nullptr ? context.itemTable()->get(item.objectDescriptionId) : nullptr;

    if (pDefinition == nullptr)
    {
        return;
    }

    GameplayRenderedInspectableHudItem inspectable = {};
    inspectable.objectDescriptionId = item.objectDescriptionId;
    inspectable.hasItemState = true;
    inspectable.itemState = item;
    inspectable.textureName = pDefinition->iconName;
    inspectable.x = area.x;
    inspectable.y = area.y;
    inspectable.width = area.width;
    inspectable.height = area.height;
    context.addRenderedInspectableHudItem(inspectable);
}

std::string itemName(const GameplayScreenRuntime &context, uint32_t itemId)
{
    const ItemDefinition *pDefinition = context.itemTable() != nullptr ? context.itemTable()->get(itemId) : nullptr;
    return pDefinition != nullptr ? pDefinition->name : "";
}

// A short tag on a material cell: the gem tier, or a charged orb or Endless Potion's content.
std::string materialTag(const GameplayScreenRuntime &context, const CraftMaterialEntry &material)
{
    const int tier = GameplayCraftingBenchView::rules(context).gemTier(material.key.itemId);

    if (tier > 0)
    {
        return Engine::tr("T{tier}", {{"tier", tier}});
    }

    if (material.key.power > 0)
    {
        return Engine::tr("p{power}", {{"power", int64_t(material.key.power)}});
    }

    return material.key.state > 0 ? "+" + std::to_string(material.key.state) : "";
}
}

void GameplayCraftingBenchRenderer::render(GameplayScreenRuntime &context, const GameplayBenchPainter &painter)
{
    const std::optional<GameplayCraftingBenchModel> model = GameplayCraftingBenchView::buildModel(context);
    const ItemTable *pItemTable = context.itemTable();

    if (!model || pItemTable == nullptr)
    {
        return;
    }

    const GameplayUiController::CraftingBenchState &state = context.characterScreenReadOnly().alchemyBench.crafting;
    const ItemRules &itemRules = gameRulesFor(context.partyReadOnly()).items;

    painter.label("CraftingBenchItemHeader", Engine::tr("Equipment"));
    painter.label("CraftingBenchItemCount", Engine::tr("{count} items", {{"count", model->targets.size()}}));
    painter.chip("CraftingBenchItemFilterAll", Engine::tr("All"), state.targetFilter == TargetFilter::All);
    painter.chip("CraftingBenchItemFilterWorn", Engine::tr("Worn"), state.targetFilter == TargetFilter::Worn);
    painter.chip("CraftingBenchItemFilterPacks", Engine::tr("Packs"), state.targetFilter == TargetFilter::Packs);

    if (const std::optional<Rect> search = painter.rect("CraftingBenchItemSearch"))
    {
        painter.well(*search, state.searchActive ? SelectedBorderColor : WellBorderColor);

        if (!state.searchActive && painter.hovered(*search))
        {
            painter.fill(*search, HoverColor);
        }

        painter.text("CraftingBenchItemSearch", *search,
            state.search.empty() && !state.searchActive ? Engine::tr("Search items")
                                                        : state.search + (state.searchActive ? "_" : ""),
            state.search.empty() && !state.searchActive ? std::optional<uint32_t>(DisabledTextColor) : std::nullopt);
    }

    if (const std::optional<Rect> list = painter.rect("CraftingBenchItemList"))
    {
        painter.well(*list);
        const float maximumScroll = GameplayCraftingBenchView::maximumListScroll(*model, *list);
        const float scroll = std::clamp(state.listScrollOffset, 0.0f, maximumScroll);

        for (const GameplayCraftingBenchRowRect &rowRect :
            GameplayCraftingBenchView::visibleRows(*model, *list, scroll))
        {
            const GameplayCraftingBenchRow &row = model->rows[rowRect.rowIndex];
            const Rect &area = rowRect.rect;
            const float s = area.scale;

            if (row.kind == GameplayCraftingBenchRowKind::Header)
            {
                painter.text("AlchemyBenchIngredientHint", {area.x + 4 * s, area.y + s, area.width, area.height, s},
                    row.text, HeaderTextColor);
                continue;
            }

            const CraftTargetEntry &target = model->targets[row.targetIndex];
            const bool selected = model->selectedTarget == row.targetIndex;

            if (selected)
            {
                painter.fill(area, SelectedRowColor);
                painter.frame(area, SelectedBorderColor);
            }
            else if (painter.hovered(area))
            {
                painter.fill(area, HoverColor);
            }

            const ItemDefinition *pDefinition = pItemTable->get(target.item.objectDescriptionId);
            const std::optional<uint32_t> nameColor = itemRules.nameColor(target.item);
            const uint32_t color = !model->targetUsable[row.targetIndex] ? DisabledTextColor
                : nameColor ? abgrFromRgb(*nameColor)
                            : GameplayUiSkin::Ivory;
            painter.itemIcon(pDefinition, {area.x + 3 * s, area.y + 1.5f * s, 10 * s, 14 * s, s});
            painter.text("AlchemyBenchRowLabel", {area.x + 17 * s, area.y + 3 * s, area.width - 50 * s, area.height,
                s}, GameplayCraftingBenchView::itemDisplayName(context, target.item), color);

            if (pDefinition != nullptr)
            {
                const int level = itemRules.levelRequirement(*pDefinition, target.item.rulesetFields);

                if (level > 1)
                {
                    painter.text("AlchemyBenchRowCount", {area.x, area.y + 3 * s, area.width - 4 * s, area.height, s},
                        Engine::tr("L{level}", {{"level", int64_t(level)}}), color);
                }
            }
        }

        if (model->rows.empty())
        {
            painter.text("AlchemyBenchSlotNameLabel", {list->x, list->y + 10 * list->scale, list->width,
                12 * list->scale, list->scale}, Engine::tr("No equipment to craft on."), DimTextColor);
        }

        const float visibleHeight = list->height / list->scale - 2 * GameplayAlchemyBenchView::RecipeListPadding;
        GameplayUiSkin::renderScrollbar(context, *list, maximumScroll > 0 ? scroll / maximumScroll : 0.0f,
            model->rowsHeight > 0 ? visibleHeight / model->rowsHeight : 1.0f,
            context.interactionState().alchemyBenchScrollDrag == 1);
    }

    const CraftMaterialEntry *pMaterial =
        model->selectedMaterial ? &model->materials[*model->selectedMaterial] : nullptr;
    const CraftTargetEntry *pTarget = model->selectedTarget ? &model->targets[*model->selectedTarget] : nullptr;
    painter.label("CraftingBenchOperationHeader",
        pMaterial != nullptr ? GameplayCraftingBenchView::operationName(context, pMaterial->key.itemId)
                             : Engine::tr("Crafting"));
    painter.label("CraftingBenchOwnerLabel",
        pTarget != nullptr ? model->ownerText : Engine::tr("Choose an item and a material."));

    const GameplayOverlayInteractionState &interaction = context.interactionState();
    const uint64_t craftedElapsedTicks = SDL_GetTicks() - state.craftedTicks;
    const auto slotLabels = [&painter](const Rect &slot, const std::string &name, const std::string &detail,
                                uint32_t detailColor)
    {
        const float s = slot.scale;
        const Rect nameArea = {slot.x - 12 * s, slot.y + slot.height + 2 * s, slot.width + 24 * s, 11 * s, s};
        painter.text("AlchemyBenchSlotNameLabel", nameArea, name, GameplayUiSkin::Ivory);
        painter.text("AlchemyBenchSlotPowerLabel", {nameArea.x, nameArea.y + 10 * s, nameArea.width, 10 * s, s},
            detail, detailColor);
    };
    const auto iconBox = [](const Rect &slot)
    {
        const float s = slot.scale;
        return Rect{slot.x + 8 * s, slot.y + 6 * s, slot.width - 16 * s, slot.height - 12 * s, s};
    };

    if (const std::optional<Rect> slot = painter.rect("CraftingBenchItemSlot"))
    {
        painter.well(*slot, pTarget != nullptr && painter.hovered(*slot) ? SelectedBorderColor : WellBorderColor);

        if (pTarget != nullptr)
        {
            painter.itemIcon(pItemTable->get(pTarget->item.objectDescriptionId), iconBox(*slot));
            addInspectable(context, pTarget->item, *slot);
            slotLabels(*slot,
                pTarget->item.identified ? itemName(context, pTarget->item.objectDescriptionId)
                                         : GameplayCraftingBenchView::itemDisplayName(context, pTarget->item),
                "", DimTextColor);
        }
        else
        {
            painter.text("AlchemyBenchSlotPowerLabel",
                {slot->x, slot->y + slot->height / 2 - 5 * slot->scale, slot->width, 10 * slot->scale, slot->scale},
                Engine::tr("item"), DisabledTextColor);
        }
    }

    painter.label("AlchemyBenchPlusLabel", "+");

    if (const std::optional<Rect> slot = painter.rect("CraftingBenchMaterialSlot"))
    {
        painter.well(*slot, pMaterial != nullptr && painter.hovered(*slot) ? SelectedBorderColor : WellBorderColor);

        if (pMaterial != nullptr)
        {
            painter.itemIcon(pItemTable->get(pMaterial->key.itemId), iconBox(*slot));
            addInspectable(context, pMaterial->item, *slot);
            const std::string tag = materialTag(context, *pMaterial);
            slotLabels(*slot, itemName(context, pMaterial->key.itemId),
                (tag.empty() ? "" : tag + "  ") + "x" + std::to_string(pMaterial->refs.size()), DimTextColor);
        }
        else
        {
            painter.text("AlchemyBenchSlotPowerLabel",
                {slot->x, slot->y + slot->height / 2 - 5 * slot->scale, slot->width, 10 * slot->scale, slot->scale},
                Engine::tr("material"), DisabledTextColor);
        }
    }

    painter.label("AlchemyBenchEqualsLabel", "=");
    const CraftPlan *pStep = model->step ? &*model->step : nullptr;
    const bool possible = pStep != nullptr && pStep->result.possible;
    // A gem chosen without an item: the result is the merged gem, Apply merges one set and Apply All every set.
    const uint32_t merges = model->combine.steps.empty() ? 0 : model->combine.steps.front().merges;
    const bool gemOnly = pTarget == nullptr && merges > 0;

    if (const std::optional<Rect> slot = painter.rect("CraftingBenchResultSlot"))
    {
        painter.well(*slot, possible || gemOnly ? SelectedBorderColor : WellBorderColor);
        const float glowSeconds = 0.9f;
        const float elapsed = float(craftedElapsedTicks) * 0.001f;

        if (!state.craftedText.empty() && elapsed < glowSeconds)
        {
            painter.fill(*slot, (uint32_t(std::lround(0x90 * (1.0f - elapsed / glowSeconds))) << 24) | 0x0050c8f0u);
        }

        if (possible && pStep->result.hiddenOutcome)
        {
            // A gamble: the item, faded, and a question mark until it is applied.
            painter.itemIcon(pItemTable->get(pStep->item.objectDescriptionId), iconBox(*slot), 90);
            painter.text("AlchemyBenchPlusLabel", *slot, "?", GameplayUiSkin::Gold);
            slotLabels(*slot, itemName(context, pStep->item.objectDescriptionId), Engine::tr("random"), DimTextColor);
        }
        else if (possible)
        {
            // The Mirror's result is its copy; everything else shows the item as it will be.
            const InventoryItem &shown = pStep->result.materialAfter && !pStep->result.materialConsumed
                    && pStep->result.materialAfter->objectDescriptionId == pStep->item.objectDescriptionId
                ? *pStep->result.materialAfter
                : pStep->item;
            painter.itemIcon(pItemTable->get(shown.objectDescriptionId), iconBox(*slot));
            addInspectable(context, shown, *slot);
            const uint32_t batch = model->batch ? model->batch->applications : 0;
            slotLabels(*slot, itemName(context, shown.objectDescriptionId),
                batch > 1 ? Engine::tr("{count} possible", {{"count", int64_t(batch)}}) : std::string(), DimTextColor);
        }
        else if (gemOnly)
        {
            const uint32_t mergedId = model->combine.steps.front().toItemId;
            painter.itemIcon(pItemTable->get(mergedId), iconBox(*slot));
            slotLabels(*slot, itemName(context, mergedId), Engine::tr("x{count} possible",
                {{"count", int64_t(merges)}}),
                DimTextColor);
        }
        else if (!state.craftedText.empty())
        {
            slotLabels(*slot, Engine::tr("Done"), state.craftedText, GameplayUiSkin::Gold);
        }
    }

    if (const std::optional<Rect> compare = painter.rect("CraftingBenchCompare"))
    {
        float lineY = compare->y;
        const float gap = 2 * compare->scale;
        const std::vector<GameplayCraftingBenchChoiceRect> choices =
            GameplayCraftingBenchView::choiceRows(*model, *compare);

        // A step with options (the Pearl): the player picks one, the rest of the preview is that pick. The picked row
        // stands for the summary ("Removes ..."), which would push the comparison past the panel.
        if (!choices.empty())
        {
            const float s = compare->scale;
            painter.text("AlchemyBenchIngredientHint",
                {compare->x, compare->y, compare->width, GameplayCraftingBenchView::ChoicePromptHeight * s, s},
                pStep->result.choicePrompt, HeaderTextColor);

            for (const GameplayCraftingBenchChoiceRect &choice : choices)
            {
                const Rect &area = choice.rect;
                const bool picked = choice.choiceIndex == pStep->result.choice;

                if (picked)
                {
                    painter.fill(area, SelectedRowColor);
                    painter.frame(area, SelectedBorderColor);
                }
                else if (painter.hovered(area))
                {
                    painter.fill(area, HoverColor);
                }

                painter.text("AlchemyBenchRowLabel", {area.x + 4 * s, area.y + 2 * s, area.width - 8 * s,
                    area.height, s}, pStep->result.choices[choice.choiceIndex],
                    picked ? GameplayUiSkin::Penalty : DimTextColor);
            }

            lineY = choices.back().rect.y + choices.back().rect.height + gap;
        }

        if (state.mergePending && !model->combine.steps.empty())
        {
            const GemCombinePlan::Step &merge = model->combine.steps.front();
            const uint32_t perMerge = uint32_t(GameplayCraftingBenchView::rules(context).gemCombineCount());
            lineY = painter.paragraph("CraftingBenchCompare",
                Engine::tr("Merge {from_count} x {from} into {to_count} x {to}?",
                    {{"from_count", int64_t(merge.merges * perMerge)},
                    {"from", itemName(context, merge.fromItemId)}, {"to_count", int64_t(merge.merges)},
                    {"to", itemName(context, merge.toItemId)}}),
                GameplayUiSkin::Gold, lineY)
                + gap;
        }
        else if (state.confirmPending && possible && !pStep->result.confirmation.empty())
        {
            lineY = painter.paragraph("CraftingBenchCompare", pStep->result.confirmation, GameplayUiSkin::Gold, lineY)
                + gap;
        }
        else if (pStep != nullptr && !possible)
        {
            lineY = painter.paragraph("CraftingBenchCompare", pStep->result.reason, GameplayUiSkin::Penalty, lineY)
                + gap;
        }
        else if (possible && choices.empty())
        {
            lineY = painter.paragraph("CraftingBenchCompare", pStep->result.summary, GameplayUiSkin::Gold, lineY) + gap;
        }

        if (pTarget != nullptr)
        {
            // A gamble shows the item as it is; the summary names what may change.
            const std::vector<CompareLine> before = itemLines(context, pTarget->item);
            const std::vector<CompareLine> after =
                possible && !pStep->result.hiddenOutcome ? itemLines(context, pStep->item) : before;
            const auto contains = [](const std::vector<CompareLine> &lines, const std::string &text)
            {
                return std::any_of(lines.begin(), lines.end(),
                    [&text](const CompareLine &line)
                    {
                        return line.text == text;
                    });
            };

            for (const CompareLine &line : after)
            {
                lineY = painter.paragraph("CraftingBenchCompare", line.text,
                    contains(before, line.text) ? line.color : GameplayUiSkin::Bonus, lineY);
            }

            for (const CompareLine &line : before)
            {
                if (!contains(after, line.text))
                {
                    lineY = painter.paragraph("CraftingBenchCompare", "- " + line.text, GameplayUiSkin::Penalty, lineY);
                }
            }

            // What crafting can still do to the item, without a material chosen.
            if (pMaterial == nullptr && !model->outlook.empty())
            {
                lineY += gap * 2;

                for (const std::string &line : model->outlook)
                {
                    lineY = painter.paragraph("CraftingBenchCompare", line, DimTextColor, lineY);
                }
            }
        }
        else if (pMaterial != nullptr)
        {
            if (gemOnly && !state.mergePending)
            {
                const GemCombinePlan::Step &merge = model->combine.steps.front();
                const uint32_t perMerge = uint32_t(GameplayCraftingBenchView::rules(context).gemCombineCount());
                lineY = painter.paragraph("CraftingBenchCompare",
                    Engine::tr("Merge {from_count} x {from} into 1 x {to}: {count} possible.",
                        {{"from_count", int64_t(perMerge)},
                        {"from", itemName(context, merge.fromItemId)}, {"to", itemName(context, merge.toItemId)},
                        {"count", int64_t(merges)}}),
                    GameplayUiSkin::Gold, lineY)
                    + gap;
            }

            const ItemDefinition *pDefinition = pItemTable->get(pMaterial->key.itemId);
            painter.paragraph("CraftingBenchCompare",
                pDefinition != nullptr ? Engine::localize(pDefinition->notes) : "", DimTextColor, lineY);
        }
    }

    const bool confirming = state.confirmPending && possible && !pStep->result.confirmation.empty();
    const uint32_t batchCount = model->batch ? model->batch->applications : 0;
    const bool batchUseful = batchCount > 1 && possible && pStep->result.confirmation.empty();

    if (gemOnly)
    {
        painter.button("CraftingBenchApplyButton", Engine::tr("Merge"), true);
        painter.button("CraftingBenchApplyManyButton",
            state.mergePending ? Engine::tr("Confirm") : Engine::tr("Merge x{count}", {{"count", int64_t(merges)}}),
            merges > 1, state.mergePending);
    }
    else
    {
        painter.button("CraftingBenchApplyButton", Engine::tr(confirming ? "Confirm" : "Apply"), possible,
            confirming);
        painter.button("CraftingBenchApplyManyButton",
            batchUseful ? Engine::tr("Apply x{count}", {{"count", int64_t(batchCount)}}) : Engine::tr("Apply All"),
            batchUseful);
    }

    painter.button("CraftingBenchClearButton",
        Engine::tr(confirming || state.mergePending ? "Cancel" : "Clear"),
        state.target.has_value() || state.material.has_value());
    painter.button("CraftingBenchCloseButton", Engine::tr("Close"), true);

    painter.label("CraftingBenchMaterialHeader", Engine::tr("Materials"));
    // With a gem chosen, the hint says what Merge does with it.
    const CraftingRules &craftingRules = GameplayCraftingBenchView::rules(context);
    const int mergeFromTier = pMaterial != nullptr ? craftingRules.gemTier(pMaterial->key.itemId) : 0;
    painter.label("CraftingBenchMaterialHint",
        mergeFromTier > 0 && craftingRules.combinedGem(pMaterial->key.itemId) != 0
            ? Engine::tr("with no item chosen, Merge turns {count} x T{from} into 1 x T{to}",
                {{"count", int64_t(craftingRules.gemCombineCount())},
                {"from", int64_t(mergeFromTier)}, {"to", int64_t(mergeFromTier + 1)}})
            : Engine::tr("whole party, click or drag to place"));
    painter.chip("CraftingBenchMaterialFilterAll", Engine::tr("All"),
        state.materialFilter == MaterialFilter::All);
    painter.chip("CraftingBenchMaterialFilterGems", Engine::tr("Gems"),
        state.materialFilter == MaterialFilter::Gems);
    painter.chip("CraftingBenchMaterialFilterSpecial", Engine::tr("Special"),
        state.materialFilter == MaterialFilter::Special);
    painter.chip("CraftingBenchMaterialFilterPotions", Engine::tr("Potions"),
        state.materialFilter == MaterialFilter::Potions);
    painter.chip("CraftingBenchCheapestGems", Engine::tr("Cheapest gems"), state.cheapestGems);

    if (const std::optional<Rect> grid = painter.rect("CraftingBenchMaterialGrid"))
    {
        painter.well(*grid);
        const size_t maximumRow = GameplayCraftingBenchView::maximumMaterialScrollRow(*model, *grid);
        const size_t scrollRow = std::min(state.materialScrollRow, maximumRow);

        for (const GameplayCraftingBenchCellRect &cell :
            GameplayCraftingBenchView::visibleCells(*model, *grid, scrollRow))
        {
            const CraftMaterialEntry &material = model->materials[cell.materialIndex];
            const Rect &area = cell.rect;
            const float s = area.scale;
            const bool selected = model->selectedMaterial == cell.materialIndex;
            const bool usable = model->materialUsable[cell.materialIndex];
            painter.well(area, selected ? SelectedBorderColor : WellBorderColor);

            if (painter.hovered(area))
            {
                painter.fill(area, HoverColor);
            }

            painter.itemIcon(pItemTable->get(material.key.itemId),
                {area.x + 3 * s, area.y + 3 * s, area.width - 6 * s, area.height - 9 * s, s}, usable ? 255 : 90);
            painter.text("AlchemyBenchRowLabel", {area.x + 2 * s, area.y + area.height - 10 * s, area.width, 10 * s, s},
                materialTag(context, material), GameplayUiSkin::Gold);
            painter.text("AlchemyBenchRowCount", {area.x, area.y + area.height - 10 * s, area.width - 2 * s, 10 * s, s},
                "x" + std::to_string(material.refs.size()), usable ? GameplayUiSkin::Ivory : DisabledTextColor);
            addInspectable(context, material.item, area);
        }

        if (model->visibleMaterials.empty())
        {
            painter.text("AlchemyBenchSlotNameLabel", {grid->x, grid->y + 10 * grid->scale, grid->width,
                12 * grid->scale, grid->scale}, Engine::tr("The party carries no crafting materials."), DimTextColor);
        }

        const size_t visibleRows = GameplayAlchemyBenchView::ingredientVisibleRows(*grid);
        GameplayUiSkin::renderScrollbar(context, *grid, maximumRow > 0 ? float(scrollRow) / float(maximumRow) : 0.0f,
            float(visibleRows) / float(visibleRows + maximumRow), interaction.alchemyBenchScrollDrag == 2);
    }

    // The dragged material or item follows the pointer.
    if (interaction.alchemyBenchDragging && interaction.alchemyBenchPressedTarget.itemId != 0)
    {
        if (const GameplayInputFrame *pInput = context.currentGameplayInputFrame())
        {
            const float s = painter.rect("AlchemyBenchPanel") ? painter.rect("AlchemyBenchPanel")->scale : 1.0f;
            const float iconWidth = GameplayAlchemyBenchView::IngredientCellWidth * s;
            const float iconHeight = GameplayAlchemyBenchView::IngredientCellHeight * s;
            painter.itemIcon(pItemTable->get(interaction.alchemyBenchPressedTarget.itemId),
                {pInput->pointerX - iconWidth * 0.5f, pInput->pointerY - iconHeight * 0.5f, iconWidth, iconHeight, s});
        }
    }
}
}
