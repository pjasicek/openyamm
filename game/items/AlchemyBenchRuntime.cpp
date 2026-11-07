#include "game/items/AlchemyBenchRuntime.h"

#include "engine/Utf8Text.h"
#include "game/items/InventoryBags.h"
#include "game/rules/GameRules.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/PotionMixingTable.h"
#include "game/tables/PotionNoteTable.h"

#include <algorithm>
#include <cctype>
#include <functional>
#include <tuple>
#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
struct ItemLocation
{
    size_t memberIndex = 0;
    uint8_t bag = 0;
    uint8_t gridX = 0;
    uint8_t gridY = 0;

    bool operator==(const ItemLocation &) const = default;
};

int bagCountOf(const Party &party)
{
    return std::max(1, party.rules().items.bagCount(party));
}

// Every item in the members' bags (InventoryBags), member by member and bag by bag.
void forEachCarriedItem(
    const Party &party,
    const std::function<void(const ItemLocation &, const InventoryItem &)> &visit)
{
    const int bagCount = bagCountOf(party);

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        for (int bag = 0; bag < bagCount; ++bag)
        {
            for (const InventoryItem &item : InventoryBags::itemsInBag(party.members()[memberIndex], uint8_t(bag)))
            {
                visit(ItemLocation{memberIndex, uint8_t(bag), item.gridX, item.gridY}, item);
            }
        }
    }
}

const InventoryItem *itemAt(const Party &party, const ItemLocation &location)
{
    const Character *pMember = party.member(location.memberIndex);
    return pMember != nullptr
        ? InventoryBags::itemInBagAt(*pMember, location.bag, location.gridX, location.gridY)
        : nullptr;
}

InventoryItem *itemAt(Party &party, const ItemLocation &location)
{
    Character *pMember = party.member(location.memberIndex);
    return pMember != nullptr
        ? InventoryBags::itemInBagAt(*pMember, location.bag, location.gridX, location.gridY)
        : nullptr;
}

std::optional<ItemLocation> findStrongestItem(
    const Party &party,
    uint32_t itemId,
    const std::optional<ItemLocation> &excluded)
{
    std::optional<ItemLocation> best;
    uint16_t bestPower = 0;
    forEachCarriedItem(party,
        [&](const ItemLocation &location, const InventoryItem &item)
        {
            if (item.objectDescriptionId != itemId || location == excluded)
            {
                return;
            }

            if (!best.has_value() || item.standardEnchantPower > bestPower)
            {
                best = location;
                bestPower = item.standardEnchantPower;
            }
        });
    return best;
}

uint8_t requiredMasteryFor(uint32_t resultItemId, const AlchemyBenchTables &tables)
{
    const MergedPotionSettingEntry *pSetting = tables.potionSettingTable.getByItemId(resultItemId);
    return pSetting != nullptr && pSetting->requiredMastery.has_value()
        ? static_cast<uint8_t>(std::min<uint32_t>(*pSetting->requiredMastery, 255))
        : 0;
}

// A reagent and a bottle mix into the bottle, whatever order they were picked in: the potion keeps the target's
// inventory footprint, and a reagent's is too small for it.
AlchemyRecipe bottleAsTarget(const AlchemyRecipe &recipe, const AlchemyBenchTables &tables)
{
    if (recipe.heldItemId == tables.potionSettingTable.emptyBottleItemId()
        && tables.reagentSettingTable.resultItemIdForReagent(recipe.targetItemId).has_value())
    {
        return {recipe.heldItemId, recipe.targetItemId};
    }

    return recipe;
}

InventoryItemMixResult simulateMix(
    InventoryItem heldItem,
    InventoryItem &targetItem,
    SkillMastery mastery,
    uint32_t level,
    const AlchemyBenchTables &tables)
{
    return InventoryItemMixingRuntime::mixItems(
        heldItem,
        targetItem,
        mastery,
        level,
        tables.itemTable,
        tables.potionMixingTable,
        tables.potionSettingTable,
        tables.reagentSettingTable);
}

// A recipe makes a new potion. Diluting a potion or boosting it with a catalyst hands back one of the inputs.
std::optional<uint32_t> potionRecipeResult(
    uint32_t targetItemId,
    uint32_t heldItemId,
    const AlchemyBenchTables &tables)
{
    InventoryItem heldItem = {};
    heldItem.objectDescriptionId = heldItemId;
    InventoryItem targetItem = {};
    targetItem.objectDescriptionId = targetItemId;
    const InventoryItemMixResult result =
        simulateMix(heldItem, targetItem, SkillMastery::Grandmaster, 0, tables);

    if (!result.success
        || result.action != InventoryItemMixAction::PotionMix
        || targetItem.objectDescriptionId == targetItemId
        || targetItem.objectDescriptionId == heldItemId)
    {
        return std::nullopt;
    }

    return targetItem.objectDescriptionId;
}

bool isNoteUnlocked(
    uint32_t targetItemId,
    uint32_t heldItemId,
    const AlchemyBenchTables &tables,
    const AlchemyBenchRuntime::AutonoteLookup &isAutonoteUnlocked)
{
    // Rules that know every recipe (MAW) need no note.
    if (tables.potionSettingTable.effects().allRecipesKnown())
    {
        return true;
    }

    const std::optional<uint32_t> autonoteId = tables.potionNoteTable.autonoteIdForMix(targetItemId, heldItemId);
    return autonoteId.has_value() && isAutonoteUnlocked(*autonoteId);
}

// The result potion's power requirement and drinks per bottle.
void describeResultRules(AlchemyPreview &preview, const AlchemyBenchTables &tables)
{
    if (const PotionDefinition *pPotion = tables.potionSettingTable.effects().find(preview.resultItemId))
    {
        preview.minimumPower = pPotion->minimumPower;
        preview.charges = pPotion->charges;
    }
}

// The note for the reversed order also counts when both orders brew the same potion.
bool isPotionRecipeKnown(
    uint32_t targetItemId,
    uint32_t heldItemId,
    uint32_t resultItemId,
    const AlchemyBenchTables &tables,
    const AlchemyBenchRuntime::AutonoteLookup &isAutonoteUnlocked)
{
    if (isNoteUnlocked(targetItemId, heldItemId, tables, isAutonoteUnlocked))
    {
        return true;
    }

    return potionRecipeResult(heldItemId, targetItemId, tables) == resultItemId
        && isNoteUnlocked(heldItemId, targetItemId, tables, isAutonoteUnlocked);
}

struct NotedRecipe
{
    AlchemyRecipe recipe;
    uint32_t resultItemId = 0;
};

// The mix a potion note records, in the order that brews it.
std::optional<NotedRecipe> notedRecipe(const PotionNoteTable::Entry &note, const AlchemyBenchTables &tables)
{
    AlchemyRecipe recipe = {note.targetItemId, note.heldItemId};
    std::optional<uint32_t> resultItemId = potionRecipeResult(recipe.targetItemId, recipe.heldItemId, tables);

    if (!resultItemId.has_value())
    {
        // Some potions only react when the other one is poured in, such as Recharge Item.
        recipe = {note.heldItemId, note.targetItemId};
        resultItemId = potionRecipeResult(recipe.targetItemId, recipe.heldItemId, tables);
    }

    if (!resultItemId.has_value())
    {
        return std::nullopt;
    }

    return NotedRecipe{recipe, *resultItemId};
}

bool equalsIgnoringCase(const std::string &left, const std::string &right)
{
    return left.size() == right.size()
        && std::equal(left.begin(), left.end(), right.begin(),
            [](unsigned char leftCharacter, unsigned char rightCharacter)
            {
                return std::tolower(leftCharacter) == std::tolower(rightCharacter);
            });
}

uint16_t ingredientPower(
    const InventoryItem &item,
    AlchemyIngredientKind kind,
    const AlchemyBenchTables &tables,
    const AlchemistInfo &alchemist)
{
    if (kind != AlchemyIngredientKind::Reagent)
    {
        return item.standardEnchantPower;
    }

    const ItemDefinition *pDefinition = tables.itemTable.get(item.objectDescriptionId);
    return pDefinition != nullptr
        ? uint16_t(std::max(0,
            boundGameRules().potions.reagentPower(*pDefinition, item, alchemist.mastery, alchemist.level)))
        : 0;
}

std::optional<AlchemyIngredientKind> ingredientKind(uint32_t itemId, const AlchemyBenchTables &tables)
{
    if (itemId == tables.potionSettingTable.emptyBottleItemId())
    {
        return AlchemyIngredientKind::Bottle;
    }

    if (tables.reagentSettingTable.resultItemIdForReagent(itemId).has_value())
    {
        return AlchemyIngredientKind::Reagent;
    }

    if (tables.potionSettingTable.getByItemId(itemId) != nullptr)
    {
        return AlchemyIngredientKind::Potion;
    }

    return std::nullopt;
}
}

AlchemistInfo AlchemyBenchRuntime::resolveAlchemist(const Party &party)
{
    AlchemistInfo alchemist = {};
    alchemist.memberIndex = party.bestPartyWideUtilitySkillMemberIndex("Alchemy");
    const Character *pMember = alchemist.memberIndex ? party.member(*alchemist.memberIndex) : nullptr;
    const CharacterSkill *pSkill = pMember != nullptr ? pMember->findSkill("Alchemy") : nullptr;

    if (pSkill != nullptr)
    {
        alchemist.mastery = pSkill->mastery;
        alchemist.level = gameRulesFor(&party).potions.mixingAlchemyLevel(*pMember);
    }

    return alchemist;
}

std::vector<AlchemyIngredient> AlchemyBenchRuntime::collectIngredients(
    const Party &party,
    const AlchemyBenchTables &tables)
{
    std::vector<AlchemyIngredient> ingredients;
    const AlchemistInfo alchemist = resolveAlchemist(party);

    forEachCarriedItem(party,
        [&](const ItemLocation &, const InventoryItem &item)
        {
            const std::optional<AlchemyIngredientKind> kind = ingredientKind(item.objectDescriptionId, tables);

            if (!kind.has_value())
            {
                return;
            }

            const uint16_t power = ingredientPower(item, *kind, tables, alchemist);
            const auto found = std::find_if(ingredients.begin(), ingredients.end(),
                [&item](const AlchemyIngredient &ingredient)
                {
                    return ingredient.itemId == item.objectDescriptionId;
                });

            if (found == ingredients.end())
            {
                ingredients.push_back({item.objectDescriptionId, *kind, 1, power});
            }
            else
            {
                ++found->count;
                found->bestPower = std::max(found->bestPower, power);
            }
        });

    const auto sortKey =
        [&tables](const AlchemyIngredient &ingredient)
        {
            const uint32_t group = ingredient.kind == AlchemyIngredientKind::Reagent
                ? tables.reagentSettingTable.resultItemIdForReagent(ingredient.itemId).value_or(0)
                : 0;
            return std::tuple(static_cast<uint8_t>(ingredient.kind), group, ingredient.itemId);
        };
    std::sort(ingredients.begin(), ingredients.end(),
        [&sortKey](const AlchemyIngredient &left, const AlchemyIngredient &right)
        {
            return sortKey(left) < sortKey(right);
        });
    return ingredients;
}

const AlchemyIngredient *AlchemyBenchRuntime::findIngredient(
    const std::vector<AlchemyIngredient> &ingredients,
    uint32_t itemId)
{
    const auto found = std::find_if(ingredients.begin(), ingredients.end(),
        [itemId](const AlchemyIngredient &ingredient)
        {
            return ingredient.itemId == itemId;
        });
    return found != ingredients.end() ? &*found : nullptr;
}

uint32_t AlchemyBenchRuntime::brewableCount(
    const AlchemyRecipe &recipe,
    const std::vector<AlchemyIngredient> &ingredients)
{
    const AlchemyIngredient *pTarget = findIngredient(ingredients, recipe.targetItemId);
    const AlchemyIngredient *pHeld = findIngredient(ingredients, recipe.heldItemId);

    if (pTarget == nullptr || pHeld == nullptr)
    {
        return 0;
    }

    return recipe.targetItemId == recipe.heldItemId ? pTarget->count / 2 : std::min(pTarget->count, pHeld->count);
}

bool AlchemyBenchRuntime::matchesSearch(const std::string &name, const std::string &search)
{
    return search.empty() || Engine::Utf8::lower(name).find(Engine::Utf8::lower(search)) != std::string::npos;
}

std::optional<uint32_t> AlchemyBenchRuntime::recipeScrollPotionItemId(
    uint32_t scrollItemId,
    const AlchemyBenchTables &tables)
{
    static const std::string RecipeSuffix = " Recipe";
    const ItemDefinition *pScroll = tables.itemTable.get(scrollItemId);

    if (pScroll == nullptr
        || pScroll->equipStat != "Mscroll"
        || pScroll->name.size() <= RecipeSuffix.size()
        || !pScroll->name.ends_with(RecipeSuffix))
    {
        return std::nullopt;
    }

    const std::string potionName = pScroll->name.substr(0, pScroll->name.size() - RecipeSuffix.size());

    for (const MergedPotionSettingEntry &setting : tables.potionSettingTable.entries())
    {
        const ItemDefinition *pPotion = tables.itemTable.get(setting.itemId);

        if (pPotion != nullptr && equalsIgnoringCase(pPotion->name, potionName))
        {
            return setting.itemId;
        }
    }

    return std::nullopt;
}

std::vector<uint32_t> AlchemyBenchRuntime::potionNoteIds(uint32_t potionItemId, const AlchemyBenchTables &tables)
{
    std::vector<uint32_t> autonoteIds;

    for (const PotionNoteTable::Entry &note : tables.potionNoteTable.entries())
    {
        const std::optional<NotedRecipe> noted = notedRecipe(note, tables);

        if (noted.has_value()
            && noted->resultItemId == potionItemId
            && std::find(autonoteIds.begin(), autonoteIds.end(), note.autonoteId) == autonoteIds.end())
        {
            autonoteIds.push_back(note.autonoteId);
        }
    }

    return autonoteIds;
}

AlchemyBook AlchemyBenchRuntime::buildBook(
    const AlchemyBenchTables &tables,
    const std::vector<AlchemyIngredient> &ingredients,
    SkillMastery alchemistMastery,
    const AutonoteLookup &isAutonoteUnlocked)
{
    AlchemyBook book = {};
    std::unordered_map<uint32_t, size_t> entryIndices;
    std::unordered_set<uint32_t> resultItemIds;
    const auto entryFor =
        [&book, &entryIndices, &tables](uint32_t resultItemId, bool reagentRecipe) -> AlchemyBookEntry &
        {
            const auto found = entryIndices.find(resultItemId);

            if (found != entryIndices.end())
            {
                return book.entries[found->second];
            }

            entryIndices.emplace(resultItemId, book.entries.size());
            AlchemyBookEntry &entry = book.entries.emplace_back();
            entry.resultItemId = resultItemId;
            entry.reagentRecipe = reagentRecipe;
            entry.requiredMastery = requiredMasteryFor(resultItemId, tables);
            return entry;
        };

    const uint32_t bottleItemId = tables.potionSettingTable.emptyBottleItemId();

    for (const MergedReagentSettingEntry &reagent : tables.reagentSettingTable.entries())
    {
        resultItemIds.insert(reagent.resultItemId);
        entryFor(reagent.resultItemId, true).recipes.push_back({bottleItemId, reagent.itemId});
    }

    // Rules that know every recipe (MAW) list the whole mixing table.
    if (tables.potionSettingTable.effects().allRecipesKnown())
    {
        for (const auto &[heldItemId, targetItemId] : tables.potionMixingTable.brewingPairs())
        {
            const std::optional<uint32_t> resultItemId = potionRecipeResult(targetItemId, heldItemId, tables);

            if (!resultItemId)
            {
                continue;
            }

            resultItemIds.insert(*resultItemId);
            AlchemyBookEntry &entry = entryFor(*resultItemId, false);
            const bool duplicate = std::any_of(entry.recipes.begin(), entry.recipes.end(),
                [heldItemId, targetItemId](const AlchemyRecipe &known)
                {
                    return (known.targetItemId == targetItemId && known.heldItemId == heldItemId)
                        || (known.targetItemId == heldItemId && known.heldItemId == targetItemId);
                });

            if (!duplicate)
            {
                entry.recipes.push_back({targetItemId, heldItemId});
            }
        }
    }

    for (const PotionNoteTable::Entry &note : tables.potionNoteTable.entries())
    {
        const std::optional<NotedRecipe> noted = notedRecipe(note, tables);

        if (!noted.has_value())
        {
            continue;
        }

        resultItemIds.insert(noted->resultItemId);

        if (!tables.potionSettingTable.effects().allRecipesKnown() && !isAutonoteUnlocked(note.autonoteId))
        {
            continue;
        }

        const AlchemyRecipe &recipe = noted->recipe;
        AlchemyBookEntry &entry = entryFor(noted->resultItemId, false);
        const bool duplicate = std::any_of(entry.recipes.begin(), entry.recipes.end(),
            [&recipe](const AlchemyRecipe &known)
            {
                return (known.targetItemId == recipe.targetItemId && known.heldItemId == recipe.heldItemId)
                    || (known.targetItemId == recipe.heldItemId && known.heldItemId == recipe.targetItemId);
            });

        if (!duplicate)
        {
            entry.recipes.push_back(recipe);
        }
    }

    const AlchemyIngredient *pBottles = findIngredient(ingredients, bottleItemId);
    const uint32_t bottleCount = pBottles != nullptr ? pBottles->count : 0;

    for (AlchemyBookEntry &entry : book.entries)
    {
        entry.masteryAllows = static_cast<uint32_t>(alchemistMastery) >= entry.requiredMastery;

        if (entry.reagentRecipe)
        {
            uint32_t reagentCount = 0;

            for (const AlchemyRecipe &recipe : entry.recipes)
            {
                const AlchemyIngredient *pReagent = findIngredient(ingredients, recipe.heldItemId);
                reagentCount += pReagent != nullptr ? pReagent->count : 0;
            }

            entry.brewableCount = std::min(bottleCount, reagentCount);
            continue;
        }

        for (const AlchemyRecipe &recipe : entry.recipes)
        {
            entry.brewableCount = std::max(entry.brewableCount, brewableCount(recipe, ingredients));
        }
    }

    std::stable_sort(book.entries.begin(), book.entries.end(),
        [](const AlchemyBookEntry &left, const AlchemyBookEntry &right)
        {
            return std::tuple(!left.reagentRecipe, left.requiredMastery, left.resultItemId)
                < std::tuple(!right.reagentRecipe, right.requiredMastery, right.resultItemId);
        });
    book.totalResultCount = resultItemIds.size();
    return book;
}

std::optional<AlchemyRecipe> AlchemyBenchRuntime::pickRecipe(
    const AlchemyBookEntry &entry,
    const std::vector<AlchemyIngredient> &ingredients)
{
    std::optional<AlchemyRecipe> best;
    uint32_t bestCount = 0;
    uint32_t bestPower = 0;

    for (const AlchemyRecipe &recipe : entry.recipes)
    {
        const uint32_t count = brewableCount(recipe, ingredients);
        const AlchemyIngredient *pTarget = findIngredient(ingredients, recipe.targetItemId);
        const AlchemyIngredient *pHeld = findIngredient(ingredients, recipe.heldItemId);
        const uint32_t power =
            (pTarget != nullptr ? pTarget->bestPower : 0) + (pHeld != nullptr ? pHeld->bestPower : 0);
        // Reagents only ever fill one bottle each, so the strongest one wins over the most plentiful.
        const bool better = entry.reagentRecipe
            ? count > 0 && (bestCount == 0 || power > bestPower)
            : count > bestCount || (count == bestCount && count > 0 && power > bestPower);

        if (better)
        {
            best = recipe;
            bestCount = count;
            bestPower = power;
        }
    }

    if (!best.has_value() && !entry.recipes.empty())
    {
        best = entry.recipes.front();
    }

    return best;
}

AlchemyPreview AlchemyBenchRuntime::preview(
    const Party &party,
    const AlchemyRecipe &pickedRecipe,
    const AlchemyBenchTables &tables,
    const AutonoteLookup &isAutonoteUnlocked)
{
    AlchemyPreview preview = {};
    const AlchemyRecipe recipe = bottleAsTarget(pickedRecipe, tables);

    if (recipe.targetItemId == 0 || recipe.heldItemId == 0)
    {
        return preview;
    }

    const std::optional<ItemLocation> targetLocation = findStrongestItem(party, recipe.targetItemId, std::nullopt);
    const std::optional<ItemLocation> heldLocation = findStrongestItem(party, recipe.heldItemId, targetLocation);
    const InventoryItem *pTarget = targetLocation ? itemAt(party, *targetLocation) : nullptr;
    const InventoryItem *pHeld = heldLocation ? itemAt(party, *heldLocation) : nullptr;

    if (pTarget == nullptr || pHeld == nullptr)
    {
        preview.outcome = AlchemyPreviewOutcome::MissingIngredient;
        return preview;
    }

    const std::optional<AlchemyIngredientKind> targetKind = ingredientKind(recipe.targetItemId, tables);
    const std::optional<AlchemyIngredientKind> heldKind = ingredientKind(recipe.heldItemId, tables);
    const AlchemistInfo alchemist = resolveAlchemist(party);
    preview.targetPower =
        ingredientPower(*pTarget, targetKind.value_or(AlchemyIngredientKind::Potion), tables, alchemist);
    preview.heldPower = ingredientPower(*pHeld, heldKind.value_or(AlchemyIngredientKind::Potion), tables, alchemist);
    InventoryItem result = *pTarget;
    const InventoryItemMixResult mixResult = simulateMix(*pHeld, result, alchemist.mastery, alchemist.level, tables);
    const uint32_t catalystItemId = tables.potionSettingTable.catalystPotionItemId();
    const bool catalystBoost = mixResult.success
        && mixResult.action == InventoryItemMixAction::PotionMix
        && (recipe.targetItemId == catalystItemId || recipe.heldItemId == catalystItemId);
    preview.outcome = AlchemyPreviewOutcome::Unknown;

    if (mixResult.success
        && (mixResult.action == InventoryItemMixAction::ReagentBottleMix || catalystBoost))
    {
        preview.outcome = AlchemyPreviewOutcome::Known;
        preview.resultItemId = result.objectDescriptionId;
        preview.resultPower = result.standardEnchantPower;
        preview.returnsBottle = mixResult.returnsBottle;
        describeResultRules(preview, tables);
        return preview;
    }

    const std::optional<uint32_t> recipeResult = potionRecipeResult(recipe.targetItemId, recipe.heldItemId, tables);
    const bool knownToExplode = mixResult.failureDamageLevel != 0
        && party.isExplosiveMixKnown(recipe.targetItemId, recipe.heldItemId);

    if (knownToExplode && !(recipeResult.has_value()
        && isPotionRecipeKnown(recipe.targetItemId, recipe.heldItemId, *recipeResult, tables, isAutonoteUnlocked)))
    {
        preview.outcome = AlchemyPreviewOutcome::KnownExplosive;
        return preview;
    }

    if (!recipeResult.has_value()
        || !isPotionRecipeKnown(recipe.targetItemId, recipe.heldItemId, *recipeResult, tables, isAutonoteUnlocked))
    {
        return preview;
    }

    preview.resultItemId = *recipeResult;
    preview.requiredMastery = requiredMasteryFor(*recipeResult, tables);
    preview.returnsBottle = true;

    if (!mixResult.success)
    {
        preview.outcome = AlchemyPreviewOutcome::TooDifficult;
        return preview;
    }

    preview.outcome = AlchemyPreviewOutcome::Known;
    preview.resultPower = result.standardEnchantPower;
    describeResultRules(preview, tables);
    return preview;
}

AlchemyMixOutcome AlchemyBenchRuntime::mix(
    Party &party, const AlchemyRecipe &pickedRecipe, const AlchemyBenchTables &tables)
{
    AlchemyMixOutcome outcome = {};
    const AlchemyRecipe recipe = bottleAsTarget(pickedRecipe, tables);
    const std::optional<ItemLocation> targetLocation = findStrongestItem(party, recipe.targetItemId, std::nullopt);
    const std::optional<ItemLocation> heldLocation = findStrongestItem(party, recipe.heldItemId, targetLocation);
    const int bagCount = bagCountOf(party);
    InventoryItem heldItem = {};

    if (!targetLocation
        || !heldLocation
        || !InventoryBags::takeFromBag(
            party,
            heldLocation->memberIndex,
            heldLocation->bag,
            bagCount,
            heldLocation->gridX,
            heldLocation->gridY,
            heldItem))
    {
        return outcome;
    }

    // Looked up after the held item is out, which may move the bag's other items.
    InventoryItem *pTarget = itemAt(party, *targetLocation);
    const AlchemistInfo alchemist = resolveAlchemist(party);

    if (pTarget != nullptr)
    {
        outcome.result = InventoryItemMixingRuntime::mixItems(
            heldItem,
            *pTarget,
            alchemist.mastery,
            alchemist.level,
            tables.itemTable,
            tables.potionMixingTable,
            tables.potionSettingTable,
            tables.reagentSettingTable,
            &tables.potionNoteTable);
    }

    if (!outcome.result.handled || !outcome.result.heldItemConsumed)
    {
        std::optional<InventoryItem> replaced;
        InventoryBags::placeInBag(party, heldLocation->memberIndex, heldLocation->bag, bagCount, heldItem,
            heldLocation->gridX, heldLocation->gridY, replaced);
        return outcome;
    }

    if (outcome.result.failureDamageLevel != 0)
    {
        party.recordExplosiveMix(recipe.targetItemId, recipe.heldItemId);
    }

    if (outcome.result.success)
    {
        outcome.resultItem = *pTarget;
    }

    // The potion takes its own size in the bag, not the bottle's (OY-240).
    if (outcome.result.targetItemChanged && !outcome.result.targetItemRemoved)
    {
        InventoryBags::refitChangedItem(party, targetLocation->memberIndex, targetLocation->bag, bagCount,
            targetLocation->gridX, targetLocation->gridY, tables.itemTable);
    }

    if (outcome.result.targetItemRemoved)
    {
        InventoryItem removedItem = {};
        InventoryBags::takeFromBag(
            party,
            targetLocation->memberIndex,
            targetLocation->bag,
            bagCount,
            targetLocation->gridX,
            targetLocation->gridY,
            removedItem);
    }

    if (outcome.result.returnsBottle)
    {
        const InventoryItem bottle =
            InventoryItemMixingRuntime::makeBottleItem(tables.itemTable, tables.potionSettingTable.emptyBottleItemId());

        if (!party.tryGrantInventoryItemStartingAt(targetLocation->memberIndex, bottle))
        {
            outcome.overflowItem = bottle;
        }
    }

    return outcome;
}
}

namespace OpenYAMM::Game
{
namespace
{
constexpr int MaxChainDepth = 8;
constexpr size_t MaxChainSteps = 400;
}

// Carried ingredients by item, each kind's powers kept ascending so the strongest is taken first. Changes are logged
// so a failed branch of the search can be undone without copying the stock.
class AlchemyChainPlanner::Stock
{
public:
    uint32_t count(uint32_t itemId) const
    {
        const auto found = m_items.find(itemId);
        return found != m_items.end() ? static_cast<uint32_t>(found->second.size()) : 0;
    }

    uint16_t strongest(uint32_t itemId) const
    {
        const auto found = m_items.find(itemId);
        return found != m_items.end() && !found->second.empty() ? found->second.back() : 0;
    }

    uint16_t take(uint32_t itemId)
    {
        std::vector<uint16_t> &powers = m_items[itemId];
        const uint16_t power = powers.back();
        powers.pop_back();
        m_undo.push_back({false, itemId, power});
        return power;
    }

    void add(uint32_t itemId, uint16_t power)
    {
        insert(itemId, power);
        m_undo.push_back({true, itemId, power});
    }

    size_t mark() const
    {
        return m_undo.size();
    }

    void rollback(size_t mark)
    {
        while (m_undo.size() > mark)
        {
            const Change change = m_undo.back();
            m_undo.pop_back();

            if (change.added)
            {
                std::vector<uint16_t> &powers = m_items[change.itemId];
                powers.erase(std::find(powers.begin(), powers.end(), change.power));
            }
            else
            {
                insert(change.itemId, change.power);
            }
        }
    }

    void insert(uint32_t itemId, uint16_t power)
    {
        std::vector<uint16_t> &powers = m_items[itemId];
        powers.insert(std::upper_bound(powers.begin(), powers.end(), power), power);
    }

    const std::unordered_map<uint32_t, std::vector<uint16_t>> &items() const
    {
        return m_items;
    }

private:
    struct Change
    {
        bool added = false;
        uint32_t itemId = 0;
        uint16_t power = 0;
    };

    std::unordered_map<uint32_t, std::vector<uint16_t>> m_items;
    std::vector<Change> m_undo;
};

struct AlchemyChainPlanner::Search
{
    std::vector<AlchemyChainStep> steps;
    std::unordered_set<uint32_t> brewing;
    uint16_t lastPower = 0;
    AlchemyChainBlock block = AlchemyChainBlock::None;
    uint32_t blockItemId = 0;

    void blockOn(AlchemyChainBlock reason, uint32_t itemId)
    {
        if (block == AlchemyChainBlock::None)
        {
            block = reason;
            blockItemId = itemId;
        }
    }
};

AlchemyChainPlanner::AlchemyChainPlanner(
    const Party &party,
    const AlchemyBook &book,
    const AlchemistInfo &alchemist,
    const AlchemyBenchTables &tables)
    : m_book(book)
    , m_tables(tables)
    , m_alchemistLevel(alchemist.level)
    , m_bottleItemId(tables.potionSettingTable.emptyBottleItemId())
{
    forEachCarriedItem(party,
        [&](const ItemLocation &, const InventoryItem &item)
        {
            const std::optional<AlchemyIngredientKind> kind = ingredientKind(item.objectDescriptionId, tables);

            if (kind.has_value())
            {
                m_carried.push_back({item.objectDescriptionId, ingredientPower(item, *kind, tables, alchemist)});
            }
        });
}

bool AlchemyChainPlanner::obtain(uint32_t itemId, Stock &stock, Search &search, int depth) const
{
    return stock.count(itemId) > 0 || brew(itemId, stock, search, depth);
}

bool AlchemyChainPlanner::brew(uint32_t resultItemId, Stock &stock, Search &search, int depth) const
{
    const auto found = std::find_if(m_book.entries.begin(), m_book.entries.end(),
        [resultItemId](const AlchemyBookEntry &entry)
        {
            return entry.resultItemId == resultItemId;
        });

    if (found == m_book.entries.end())
    {
        search.blockOn(resultItemId == m_bottleItemId ? AlchemyChainBlock::MissingBottle
            : m_tables.reagentSettingTable.resultItemIdForReagent(resultItemId).has_value()
                ? AlchemyChainBlock::MissingReagent
                : AlchemyChainBlock::UnknownRecipe,
            resultItemId);
        return false;
    }

    if (!found->masteryAllows)
    {
        search.blockOn(AlchemyChainBlock::NeedsMastery, resultItemId);
        return false;
    }

    if (depth > MaxChainDepth || search.steps.size() >= MaxChainSteps || search.brewing.contains(resultItemId))
    {
        return false;
    }

    // Recipes whose ingredients are already carried come first, so brewing stays as short as possible.
    std::vector<AlchemyRecipe> recipes = found->recipes;
    std::stable_sort(recipes.begin(), recipes.end(),
        [&stock, found](const AlchemyRecipe &left, const AlchemyRecipe &right)
        {
            if (found->reagentRecipe)
            {
                return std::tuple(stock.count(left.heldItemId) > 0, stock.strongest(left.heldItemId))
                    > std::tuple(stock.count(right.heldItemId) > 0, stock.strongest(right.heldItemId));
            }

            const auto carried =
                [&stock](const AlchemyRecipe &recipe)
                {
                    return int(stock.count(recipe.targetItemId) > 0) + int(stock.count(recipe.heldItemId) > 0);
                };
            return carried(left) > carried(right);
        });

    search.brewing.insert(resultItemId);

    for (const AlchemyRecipe &recipe : recipes)
    {
        const size_t stockMark = stock.mark();
        const size_t stepMark = search.steps.size();

        if (tryRecipe(*found, recipe, stock, search, depth))
        {
            search.brewing.erase(resultItemId);
            return true;
        }

        stock.rollback(stockMark);
        search.steps.resize(stepMark);
    }

    search.brewing.erase(resultItemId);
    return false;
}

bool AlchemyChainPlanner::tryRecipe(
    const AlchemyBookEntry &entry,
    const AlchemyRecipe &recipe,
    Stock &stock,
    Search &search,
    int depth) const
{
    if (entry.reagentRecipe)
    {
        if (stock.count(m_bottleItemId) == 0)
        {
            search.blockOn(AlchemyChainBlock::MissingBottle, m_bottleItemId);
            return false;
        }

        if (stock.count(recipe.heldItemId) == 0)
        {
            search.blockOn(AlchemyChainBlock::MissingReagent, entry.resultItemId);
            return false;
        }

        stock.take(m_bottleItemId);
        const uint32_t power = m_alchemistLevel + stock.take(recipe.heldItemId);
        search.lastPower = static_cast<uint16_t>(std::min<uint32_t>(power, 0xFFFFu));
        stock.add(entry.resultItemId, search.lastPower);
        search.steps.push_back({recipe, entry.resultItemId});
        return true;
    }

    // The target is set aside while the held ingredient is found, so brewing one cannot use up the other.
    if (!obtain(recipe.targetItemId, stock, search, depth + 1))
    {
        return false;
    }

    const uint16_t targetPower = stock.take(recipe.targetItemId);

    if (!obtain(recipe.heldItemId, stock, search, depth + 1))
    {
        return false;
    }

    const uint16_t heldPower = stock.take(recipe.heldItemId);
    search.lastPower = static_cast<uint16_t>((uint32_t(targetPower) + heldPower) / 2u);
    stock.add(entry.resultItemId, search.lastPower);
    stock.add(m_bottleItemId, 0);
    search.steps.push_back({recipe, entry.resultItemId});
    return true;
}

AlchemyChainPlan AlchemyChainPlanner::plan(uint32_t resultItemId, uint32_t maxBrews) const
{
    AlchemyChainPlan plan = {};
    Stock stock;

    for (const auto &[itemId, power] : m_carried)
    {
        stock.insert(itemId, power);
    }

    std::unordered_map<uint32_t, uint32_t> startCounts;

    for (const auto &[itemId, powers] : stock.items())
    {
        startCounts[itemId] = static_cast<uint32_t>(powers.size());
    }

    while (plan.brewCount < maxBrews && plan.steps.size() < MaxChainSteps)
    {
        Search search;

        if (!brew(resultItemId, stock, search, 0))
        {
            if (plan.brewCount == 0)
            {
                plan.block = search.block;
                plan.blockItemId = search.blockItemId;
            }

            break;
        }

        if (plan.brewCount == 0)
        {
            plan.resultPower = search.lastPower;
            plan.finalRecipe = search.steps.back().recipe;
        }

        plan.steps.insert(plan.steps.end(), search.steps.begin(), search.steps.end());
        ++plan.brewCount;
    }

    for (const auto &[itemId, startCount] : startCounts)
    {
        const uint32_t endCount = stock.count(itemId);

        if (endCount < startCount)
        {
            plan.used.push_back({itemId, startCount - endCount});
        }
    }

    for (const AlchemyChainStep &step : plan.steps)
    {
        if (step.resultItemId == resultItemId)
        {
            continue;
        }

        const auto found = std::find_if(plan.brewedFirst.begin(), plan.brewedFirst.end(),
            [&step](const AlchemyItemCount &count)
            {
                return count.itemId == step.resultItemId;
            });

        if (found == plan.brewedFirst.end())
        {
            plan.brewedFirst.push_back({step.resultItemId, 1});
        }
        else
        {
            ++found->count;
        }
    }

    const auto byItem =
        [](const AlchemyItemCount &left, const AlchemyItemCount &right)
        {
            return left.itemId < right.itemId;
        };
    std::sort(plan.used.begin(), plan.used.end(), byItem);
    return plan;
}

AlchemyChainOutcome AlchemyBenchRuntime::brewChain(
    Party &party,
    const AlchemyChainPlan &plan,
    const AlchemyBenchTables &tables)
{
    AlchemyChainOutcome outcome = {};
    const uint32_t finalItemId = plan.steps.empty() ? 0 : plan.steps.back().resultItemId;

    for (const AlchemyChainStep &step : plan.steps)
    {
        outcome.lastMix = mix(party, step.recipe, tables);

        if (!outcome.lastMix.result.success)
        {
            break;
        }

        ++outcome.stepsDone;

        if (step.resultItemId == finalItemId)
        {
            ++outcome.brewedCount;
            outcome.lastBrewed = outcome.lastMix.resultItem;
        }

        if (outcome.lastMix.overflowItem.has_value())
        {
            break;
        }
    }

    return outcome;
}
}
