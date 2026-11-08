#include "game/ui/GameplayCraftingBenchView.h"
#include "engine/Localization.h"

#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/items/AlchemyBenchRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/rules/GameRules.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/ui/GameplayAlchemyBenchView.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
using Filter = GameplayUiController::CraftingTargetFilter;
using MaterialFilter = GameplayUiController::CraftingMaterialFilter;

std::string slotName(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return Engine::tr("off hand");
        case EquipmentSlot::MainHand:
            return Engine::tr("main hand");
        case EquipmentSlot::Bow:
            return Engine::tr("bow");
        case EquipmentSlot::Armor:
            return Engine::tr("armour");
        case EquipmentSlot::Helm:
            return Engine::tr("helm");
        case EquipmentSlot::Belt:
            return Engine::tr("belt");
        case EquipmentSlot::Cloak:
            return Engine::tr("cloak");
        case EquipmentSlot::Gauntlets:
            return Engine::tr("gauntlets");
        case EquipmentSlot::Boots:
            return Engine::tr("boots");
        case EquipmentSlot::Amulet:
            return Engine::tr("amulet");
        default:
            return Engine::tr("ring");
    }
}

bool materialVisible(
    const GameplayScreenRuntime &context,
    const CraftMaterialEntry &material,
    MaterialFilter filter)
{
    const CraftingRules &rules = GameplayCraftingBenchView::rules(context);
    const MergedPotionSettingTable *pPotions = context.mergedPotionSettingTable();
    const bool gem = rules.gemTier(material.key.itemId) > 0;
    const bool potion = pPotions != nullptr && pPotions->effects().find(material.key.itemId) != nullptr;

    switch (filter)
    {
        case MaterialFilter::Gems:
            return gem;
        case MaterialFilter::Potions:
            return potion;
        case MaterialFilter::Special:
            return !gem && !potion;
        default:
            return true;
    }
}
}

std::optional<CraftingTables> GameplayCraftingBenchView::tables(const GameplayScreenRuntime &context)
{
    if (context.itemTable() == nullptr)
    {
        return std::nullopt;
    }

    CraftingTables result;
    result.pItemTable = context.itemTable();
    result.pStandardEnchantTable = context.standardItemEnchantTable();
    result.pSpecialEnchantTable = context.specialItemEnchantTable();
    result.pPotionEffects =
        context.mergedPotionSettingTable() != nullptr ? &context.mergedPotionSettingTable()->effects() : nullptr;
    return result;
}

const CraftingRules &GameplayCraftingBenchView::rules(const GameplayScreenRuntime &context)
{
    return gameRulesFor(context.partyReadOnly()).crafting;
}

bool GameplayCraftingBenchView::available(const GameplayScreenRuntime &context)
{
    return rules(context).hasCrafting();
}

std::string GameplayCraftingBenchView::itemDisplayName(const GameplayScreenRuntime &context, const InventoryItem &item)
{
    const ItemDefinition *pDefinition =
        context.itemTable() != nullptr ? context.itemTable()->get(item.objectDescriptionId) : nullptr;

    if (pDefinition == nullptr)
    {
        return {};
    }

    return ItemRuntime::displayName(
        item, *pDefinition, context.standardItemEnchantTable(), context.specialItemEnchantTable());
}

std::string GameplayCraftingBenchView::operationName(const GameplayScreenRuntime &context, uint32_t materialItemId)
{
    const std::string action = rules(context).materialAction(materialItemId);
    return action.empty() ? Engine::tr("Crafting") : action;
}

std::optional<GameplayCraftingBenchModel> GameplayCraftingBenchView::buildModel(const GameplayScreenRuntime &context)
{
    const Party *pParty = context.partyReadOnly();
    const std::optional<CraftingTables> craftingTables = tables(context);

    if (pParty == nullptr || !craftingTables)
    {
        return std::nullopt;
    }

    const CraftingRules &craftingRules = rules(context);
    const GameplayUiController::CraftingBenchState &state = context.characterScreenReadOnly().alchemyBench.crafting;
    GameplayCraftingBenchModel model;
    model.targets = CraftingRuntime::collectTargets(*pParty, *craftingTables);
    model.materials = CraftingRuntime::collectMaterials(*pParty, craftingRules);

    for (size_t index = 0; index < model.targets.size(); ++index)
    {
        if (state.target && model.targets[index].ref == *state.target)
        {
            model.selectedTarget = index;
        }
    }

    for (size_t index = 0; index < model.materials.size(); ++index)
    {
        if (state.material && model.materials[index].key == *state.material)
        {
            model.selectedMaterial = index;
        }

        if (materialVisible(context, model.materials[index], state.materialFilter))
        {
            model.visibleMaterials.push_back(index);
        }
    }

    CraftingContext craftingContext;
    craftingContext.pItemTable = craftingTables->pItemTable;
    craftingContext.pStandardEnchantTable = craftingTables->pStandardEnchantTable;
    craftingContext.pSpecialEnchantTable = craftingTables->pSpecialEnchantTable;
    craftingContext.pPotionEffects = craftingTables->pPotionEffects;
    const auto possible = [&](const CraftTargetEntry &target, const CraftMaterialEntry &material)
    {
        const Character *pOwner = pParty->member(target.ref.memberIndex);
        craftingContext.ownerLevel = pOwner != nullptr ? int(pOwner->level) : 1;
        return craftingRules.craft(target.item, material.item, craftingContext).possible;
    };

    if (model.selectedTarget)
    {
        const CraftTargetEntry &target = model.targets[*model.selectedTarget];
        const Character *pOwner = pParty->member(target.ref.memberIndex);
        craftingContext.ownerLevel = pOwner != nullptr ? int(pOwner->level) : 1;
        model.outlook = craftingRules.craftOutlook(target.item, craftingContext);
    }

    model.targetUsable.assign(model.targets.size(), true);
    model.materialUsable.assign(model.materials.size(), true);

    if (model.selectedMaterial)
    {
        for (size_t index = 0; index < model.targets.size(); ++index)
        {
            model.targetUsable[index] = possible(model.targets[index], model.materials[*model.selectedMaterial]);
        }
    }

    if (model.selectedTarget)
    {
        for (size_t index = 0; index < model.materials.size(); ++index)
        {
            model.materialUsable[index] = possible(model.targets[*model.selectedTarget], model.materials[index]);
        }
    }

    // Rows: each member's worn items, then each member's pack.
    std::string lastHeader;

    for (size_t index = 0; index < model.targets.size(); ++index)
    {
        const CraftTargetEntry &target = model.targets[index];

        if ((state.targetFilter == Filter::Worn && !target.ref.worn)
            || (state.targetFilter == Filter::Packs && target.ref.worn)
            || !AlchemyBenchRuntime::matchesSearch(itemDisplayName(context, target.item), state.search))
        {
            continue;
        }

        const Character *pOwner = pParty->member(target.ref.memberIndex);
        const std::string header =
            Engine::tr(target.ref.worn ? "WORN - {name}" : "PACK - {name}",
                {{"name", pOwner != nullptr ? pOwner->name : std::string()}});

        if (header != lastHeader)
        {
            model.rows.push_back({GameplayCraftingBenchRowKind::Header, 0, header, model.rowsHeight,
                GameplayAlchemyBenchView::RecipeHeaderHeight});
            model.rowsHeight += GameplayAlchemyBenchView::RecipeHeaderHeight;
            lastHeader = header;
        }

        model.rows.push_back({GameplayCraftingBenchRowKind::Item, index, "", model.rowsHeight,
            GameplayAlchemyBenchView::RecipeRowHeight});
        model.rowsHeight += GameplayAlchemyBenchView::RecipeRowHeight;
    }

    if (model.selectedTarget)
    {
        const CraftTargetEntry &target = model.targets[*model.selectedTarget];
        const Character *pOwner = pParty->member(target.ref.memberIndex);
        if (pOwner != nullptr)
        {
            model.ownerText = target.ref.worn
                ? Engine::tr("{name}, level {level}, {slot}",
                    {{"name", pOwner->name}, {"level", int64_t(pOwner->level)}, {"slot", slotName(target.ref.slot)}})
                : Engine::tr("{name}, level {level}, in the pack",
                    {{"name", pOwner->name}, {"level", int64_t(pOwner->level)}});
        }
        else
        {
            model.ownerText = target.ref.worn ? ", " + slotName(target.ref.slot) : Engine::tr(", in the pack");
        }
    }

    if (model.selectedTarget && model.selectedMaterial)
    {
        const CraftItemRef &target = model.targets[*model.selectedTarget].ref;
        const CraftMaterialKey &material = model.materials[*model.selectedMaterial].key;
        model.step =
            CraftingRuntime::plan(*pParty, target, material, 1, false, state.choice, craftingRules, *craftingTables);
        model.batch = CraftingRuntime::plan(*pParty, target, material, MaxBatchApplications, state.cheapestGems,
            state.choice, craftingRules, *craftingTables);
    }

    if (model.selectedMaterial && craftingRules.gemTier(model.materials[*model.selectedMaterial].key.itemId) > 0)
    {
        const uint32_t gemId = model.materials[*model.selectedMaterial].key.itemId;
        model.combine = CraftingRuntime::planCombine(*pParty, gemId, false, craftingRules);
        model.combineAll = CraftingRuntime::planCombine(*pParty, gemId, true, craftingRules);
    }

    return model;
}

float GameplayCraftingBenchView::maximumListScroll(
    const GameplayCraftingBenchModel &model,
    const GameplayResolvedHudLayoutElement &list)
{
    const float visibleHeight =
        list.height / std::max(0.01f, list.scale) - 2 * GameplayAlchemyBenchView::RecipeListPadding;
    return std::max(0.0f, model.rowsHeight - visibleHeight);
}

std::vector<GameplayCraftingBenchRowRect> GameplayCraftingBenchView::visibleRows(
    const GameplayCraftingBenchModel &model,
    const GameplayResolvedHudLayoutElement &list,
    float scrollOffset)
{
    std::vector<GameplayCraftingBenchRowRect> rects;
    const float padding = GameplayAlchemyBenchView::RecipeListPadding;
    const float top = list.y + padding * list.scale;
    const float bottom = list.y + list.height - padding * list.scale;

    for (size_t index = 0; index < model.rows.size(); ++index)
    {
        const GameplayCraftingBenchRow &row = model.rows[index];
        const float y = top + (row.offsetY - scrollOffset) * list.scale;
        const float height = row.height * list.scale;

        if (y < top - 0.5f || y + height > bottom + 0.5f)
        {
            continue;
        }

        rects.push_back({index, {list.x + padding * list.scale, y, list.width - (2 * padding + 6) * list.scale, height,
            list.scale}});
    }

    return rects;
}

size_t GameplayCraftingBenchView::maximumMaterialScrollRow(
    const GameplayCraftingBenchModel &model,
    const GameplayResolvedHudLayoutElement &grid)
{
    const size_t columns = GameplayAlchemyBenchView::ingredientColumns(grid);
    const size_t rows = (model.visibleMaterials.size() + columns - 1) / columns;
    const size_t visibleRows = GameplayAlchemyBenchView::ingredientVisibleRows(grid);
    return rows > visibleRows ? rows - visibleRows : 0;
}

std::vector<GameplayCraftingBenchCellRect> GameplayCraftingBenchView::visibleCells(
    const GameplayCraftingBenchModel &model,
    const GameplayResolvedHudLayoutElement &grid,
    size_t scrollRow)
{
    using namespace GameplayAlchemyBenchView;
    std::vector<GameplayCraftingBenchCellRect> rects;
    const size_t columns = ingredientColumns(grid);
    const size_t first = scrollRow * columns;
    const size_t last = std::min(model.visibleMaterials.size(), first + columns * ingredientVisibleRows(grid));

    for (size_t visibleIndex = first; visibleIndex < last; ++visibleIndex)
    {
        const size_t column = (visibleIndex - first) % columns;
        const size_t row = (visibleIndex - first) / columns;
        rects.push_back({model.visibleMaterials[visibleIndex], {
            grid.x + (IngredientGridPadding + column * (IngredientCellWidth + IngredientCellGap)) * grid.scale,
            grid.y + (IngredientGridPadding + row * (IngredientCellHeight + IngredientCellGap)) * grid.scale,
            IngredientCellWidth * grid.scale,
            IngredientCellHeight * grid.scale,
            grid.scale}});
    }

    return rects;
}

std::vector<GameplayCraftingBenchChoiceRect> GameplayCraftingBenchView::choiceRows(
    const GameplayCraftingBenchModel &model,
    const GameplayResolvedHudLayoutElement &compare)
{
    std::vector<GameplayCraftingBenchChoiceRect> rects;

    if (!model.step || !model.step->result.possible)
    {
        return rects;
    }

    const float s = compare.scale;

    for (size_t index = 0; index < model.step->result.choices.size(); ++index)
    {
        rects.push_back({index, {compare.x, compare.y + (ChoicePromptHeight + float(index) * ChoiceRowHeight) * s,
            compare.width, ChoiceRowHeight * s, s}});
    }

    return rects;
}
}
