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

// Every item in the members' bags (InventoryBags), member by member and bag by bag; the party's pouches come with the
// first member, where a ruleset keeps its potions and reagents.
void forEachCarriedItem(
    const Party &party,
    const std::function<void(const ItemLocation &, const InventoryItem &)> &visit)
{
    const int bagCount = bagCountOf(party);

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        for (const uint8_t bag : InventoryBags::carriedBags(party, bagCount, memberIndex == 0))
        {
            for (const InventoryItem &item : InventoryBags::itemsInBag(party, memberIndex, bag))
            {
                visit(ItemLocation{memberIndex, bag, item.gridX, item.gridY}, item);
            }
        }
    }
}

const InventoryItem *itemAt(const Party &party, const ItemLocation &location)
{
    return party.member(location.memberIndex) != nullptr
        ? InventoryBags::itemInBagAt(party, location.memberIndex, location.bag, location.gridX, location.gridY)
        : nullptr;
}

InventoryItem *itemAt(Party &party, const ItemLocation &location)
{
    return party.member(location.memberIndex) != nullptr
        ? InventoryBags::itemInBagAt(party, location.memberIndex, location.bag, location.gridX, location.gridY)
        : nullptr;
}

// The carried copies of an item the bench sets aside: one copy of each kept power. Copies of one item and power are
// interchangeable, so which of them stays does not matter.
std::vector<ItemLocation> keptCopies(const Party &party, uint32_t itemId, std::span<const AlchemyItemPower> kept)
{
    std::vector<uint16_t> powers;

    for (const AlchemyItemPower &copy : kept)
    {
        if (copy.itemId == itemId)
        {
            powers.push_back(copy.power);
        }
    }

    std::vector<ItemLocation> copies;

    if (powers.empty())
    {
        return copies;
    }

    forEachCarriedItem(party,
        [&](const ItemLocation &location, const InventoryItem &item)
        {
            const auto found = item.objectDescriptionId == itemId
                ? std::find(powers.begin(), powers.end(), item.standardEnchantPower)
                : powers.end();

            if (found != powers.end())
            {
                powers.erase(found);
                copies.push_back(location);
            }
        });
    return copies;
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

// What a carried copy counts as on the bench: a potion's power, and what a reagent adds for the party's alchemist.
class CopyPower
{
public:
    CopyPower(const Party &party, const AlchemyBenchTables &tables)
        : m_tables(tables)
        , m_alchemist(AlchemyBenchRuntime::resolveAlchemist(party))
    {
    }

    uint16_t operator()(const InventoryItem &item) const
    {
        const AlchemyIngredientKind kind =
            ingredientKind(item.objectDescriptionId, m_tables).value_or(AlchemyIngredientKind::Potion);
        return ingredientPower(item, kind, m_tables, m_alchemist);
    }

private:
    const AlchemyBenchTables &m_tables;
    AlchemistInfo m_alchemist;
};

// The carried copy of an item a slot mixes, past the kept copies: the first of the chosen power, or the strongest.
std::optional<ItemLocation> findCopy(
    const Party &party,
    uint32_t itemId,
    const std::optional<uint16_t> &chosenPower,
    const std::optional<ItemLocation> &excluded,
    const CopyPower &copyPower,
    std::span<const AlchemyItemPower> kept = {})
{
    const std::vector<ItemLocation> keptLocations = keptCopies(party, itemId, kept);
    std::optional<ItemLocation> best;
    uint16_t bestPower = 0;
    forEachCarriedItem(party,
        [&](const ItemLocation &location, const InventoryItem &item)
        {
            if (item.objectDescriptionId != itemId || location == excluded
                || std::find(keptLocations.begin(), keptLocations.end(), location) != keptLocations.end())
            {
                return;
            }

            const uint16_t power = copyPower(item);

            if (chosenPower ? (!best && power == *chosenPower) : (!best || power > bestPower))
            {
                best = location;
                bestPower = power;
            }
        });
    return best;
}

std::optional<ItemLocation> findStrongestItem(
    const Party &party,
    uint32_t itemId,
    const std::optional<ItemLocation> &excluded,
    const CopyPower &copyPower,
    std::span<const AlchemyItemPower> kept = {})
{
    return findCopy(party, itemId, std::nullopt, excluded, copyPower, kept);
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

struct MixLocations
{
    std::optional<ItemLocation> target;
    std::optional<ItemLocation> held;
};

// The copies a recipe mixes: the chosen ones, and otherwise the strongest of each, except that a catalyst boosts the
// copy of the potion it raises most, the stronger result between equal gains. The strongest copy gains nothing once
// the alchemist's limit or the catalyst's own power caps the result (Discord, 2026-11-14: a weak potion could not be
// boosted on the bench while a stronger copy of it was carried). Chosen copies are found first, so a slot left to the
// bench takes what remains. Empty when a chosen power has no copy.
MixLocations findMixItems(
    const Party &party,
    const AlchemyRecipe &recipe,
    const AlchemyBenchTables &tables,
    std::span<const AlchemyItemPower> kept = {},
    const AlchemyPowerChoice &choice = {})
{
    const CopyPower copyPower(party, tables);
    MixLocations locations;

    if (choice.targetPower)
    {
        locations.target = findCopy(party, recipe.targetItemId, choice.targetPower, std::nullopt, copyPower, kept);

        if (!locations.target)
        {
            return {};
        }
    }

    if (choice.heldPower)
    {
        locations.held = findCopy(party, recipe.heldItemId, choice.heldPower, locations.target, copyPower, kept);

        if (!locations.held)
        {
            return {};
        }
    }

    const uint32_t catalystItemId = tables.potionSettingTable.catalystPotionItemId();
    const bool catalystTarget = recipe.targetItemId == catalystItemId;

    if (catalystItemId == 0 || catalystTarget == (recipe.heldItemId == catalystItemId))
    {
        if (!locations.target)
        {
            locations.target = findStrongestItem(party, recipe.targetItemId, locations.held, copyPower, kept);
        }

        if (!locations.held)
        {
            locations.held = findStrongestItem(party, recipe.heldItemId, locations.target, copyPower, kept);
        }

        return locations;
    }

    std::optional<ItemLocation> &catalyst = catalystTarget ? locations.target : locations.held;
    std::optional<ItemLocation> &best = catalystTarget ? locations.held : locations.target;

    if (!catalyst)
    {
        catalyst = findStrongestItem(party, catalystItemId, std::nullopt, copyPower, kept);
    }

    const InventoryItem *pCatalyst = catalyst ? itemAt(party, *catalyst) : nullptr;

    if (pCatalyst == nullptr)
    {
        return {};
    }

    if (best)
    {
        return locations;
    }

    const uint32_t potionItemId = catalystTarget ? recipe.heldItemId : recipe.targetItemId;
    const AlchemistInfo alchemist = AlchemyBenchRuntime::resolveAlchemist(party);
    const std::vector<ItemLocation> keptLocations = keptCopies(party, potionItemId, kept);
    int bestGain = 0;
    int bestResult = 0;
    forEachCarriedItem(party,
        [&](const ItemLocation &location, const InventoryItem &potion)
        {
            if (potion.objectDescriptionId != potionItemId
                || std::find(keptLocations.begin(), keptLocations.end(), location) != keptLocations.end())
            {
                return;
            }

            InventoryItem result = catalystTarget ? *pCatalyst : potion;
            const InventoryItem &held = catalystTarget ? potion : *pCatalyst;

            if (!simulateMix(held, result, alchemist.mastery, alchemist.level, tables).success)
            {
                return;
            }

            const int resultPower = result.standardEnchantPower;
            const int gain = resultPower - int(potion.standardEnchantPower);

            if (!best || gain > bestGain || (gain == bestGain && resultPower > bestResult))
            {
                best = location;
                bestGain = gain;
                bestResult = resultPower;
            }
        });

    if (!best)
    {
        best = findStrongestItem(party, potionItemId, std::nullopt, copyPower, kept);
    }

    return locations;
}

// The choice in the order bottleAsTarget put the recipe in.
AlchemyPowerChoice choiceFor(
    const AlchemyRecipe &pickedRecipe,
    const AlchemyRecipe &recipe,
    const AlchemyPowerChoice &choice)
{
    return recipe.targetItemId == pickedRecipe.targetItemId
        ? choice
        : AlchemyPowerChoice{choice.heldPower, choice.targetPower};
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

std::vector<AlchemyPowerOption> AlchemyBenchRuntime::powerOptions(
    const Party &party,
    uint32_t itemId,
    const AlchemyBenchTables &tables)
{
    std::vector<AlchemyPowerOption> options;
    const CopyPower copyPower(party, tables);
    forEachCarriedItem(party,
        [&](const ItemLocation &, const InventoryItem &item)
        {
            if (item.objectDescriptionId != itemId)
            {
                return;
            }

            const uint16_t power = copyPower(item);
            const auto found = std::find_if(options.begin(), options.end(),
                [power](const AlchemyPowerOption &option)
                {
                    return option.power == power;
                });

            if (found == options.end())
            {
                options.push_back({power, 1});
            }
            else
            {
                ++found->count;
            }
        });
    std::sort(options.begin(), options.end(),
        [](const AlchemyPowerOption &left, const AlchemyPowerOption &right)
        {
            return left.power > right.power;
        });
    return options;
}

AlchemyPowerChoice AlchemyBenchRuntime::availableChoice(
    const Party &party,
    const AlchemyRecipe &recipe,
    const AlchemyPowerChoice &choice,
    const AlchemyBenchTables &tables)
{
    const auto copies =
        [&party, &tables](uint32_t itemId, uint16_t power) -> uint32_t
        {
            for (const AlchemyPowerOption &option : powerOptions(party, itemId, tables))
            {
                if (option.power == power)
                {
                    return option.count;
                }
            }

            return 0;
        };
    AlchemyPowerChoice available = choice;

    if (available.targetPower && (recipe.targetItemId == 0 || copies(recipe.targetItemId, *available.targetPower) == 0))
    {
        available.targetPower.reset();
    }

    if (available.heldPower)
    {
        const bool sameCopies =
            recipe.heldItemId == recipe.targetItemId && available.heldPower == available.targetPower;

        if (recipe.heldItemId == 0 || copies(recipe.heldItemId, *available.heldPower) < (sameCopies ? 2u : 1u))
        {
            available.heldPower.reset();
        }
    }

    return available;
}

uint32_t AlchemyBenchRuntime::brewableCount(
    const Party &party,
    const AlchemyRecipe &recipe,
    const AlchemyPowerChoice &choice,
    const AlchemyBenchTables &tables)
{
    if (recipe.targetItemId == 0 || recipe.heldItemId == 0)
    {
        return 0;
    }

    const auto copyPowers =
        [&party, &tables](uint32_t itemId)
        {
            std::vector<uint16_t> powers;

            for (const AlchemyPowerOption &option : powerOptions(party, itemId, tables))
            {
                powers.insert(powers.end(), option.count, option.power);
            }

            return powers;
        };
    // Strongest first, as powerOptions lists them.
    const auto take =
        [](std::vector<uint16_t> &powers, const std::optional<uint16_t> &chosenPower)
        {
            const auto found = chosenPower ? std::find(powers.begin(), powers.end(), *chosenPower) : powers.begin();

            if (found == powers.end())
            {
                return false;
            }

            powers.erase(found);
            return true;
        };
    const bool sameItem = recipe.targetItemId == recipe.heldItemId;
    std::vector<uint16_t> targetPowers = copyPowers(recipe.targetItemId);
    std::vector<uint16_t> otherPowers = sameItem ? std::vector<uint16_t>() : copyPowers(recipe.heldItemId);
    std::vector<uint16_t> &heldPowers = sameItem ? targetPowers : otherPowers;
    // The chosen copy is taken first, as the mix finds it first.
    const bool heldFirst = choice.heldPower.has_value() && !choice.targetPower.has_value();
    uint32_t count = 0;

    while (heldFirst
        ? take(heldPowers, choice.heldPower) && take(targetPowers, choice.targetPower)
        : take(targetPowers, choice.targetPower) && take(heldPowers, choice.heldPower))
    {
        ++count;
    }

    return count;
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
    const AutonoteLookup &isAutonoteUnlocked,
    bool keepMixedPotions)
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
            book.mixedPotionItemIds.insert(*resultItemId);
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
        book.mixedPotionItemIds.insert(noted->resultItemId);

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

    // The basic potions stay usable, even where a mixing recipe also makes one.
    for (const MergedReagentSettingEntry &reagent : tables.reagentSettingTable.entries())
    {
        book.mixedPotionItemIds.erase(reagent.resultItemId);
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
            if (!keepMixedPotions || !book.usesMixedPotion(recipe))
            {
                entry.brewableCount = std::max(entry.brewableCount, brewableCount(recipe, ingredients));
            }
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

std::vector<AlchemyIngredient> AlchemyBenchRuntime::withoutMixedPotions(
    const std::vector<AlchemyIngredient> &ingredients,
    const AlchemyBook &book)
{
    std::vector<AlchemyIngredient> kept;

    for (const AlchemyIngredient &ingredient : ingredients)
    {
        if (!book.isMixedPotion(ingredient.itemId))
        {
            kept.push_back(ingredient);
        }
    }

    return kept;
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
    const AutonoteLookup &isAutonoteUnlocked,
    const AlchemyPowerChoice &choice)
{
    AlchemyPreview preview = {};
    const AlchemyRecipe recipe = bottleAsTarget(pickedRecipe, tables);

    if (recipe.targetItemId == 0 || recipe.heldItemId == 0)
    {
        return preview;
    }

    const MixLocations locations = findMixItems(party, recipe, tables, {}, choiceFor(pickedRecipe, recipe, choice));
    const std::optional<ItemLocation> &targetLocation = locations.target;
    const std::optional<ItemLocation> &heldLocation = locations.held;
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

    // The powers are told by the slots as the player filled them.
    if (recipe.targetItemId != pickedRecipe.targetItemId)
    {
        std::swap(preview.targetPower, preview.heldPower);
    }

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
    Party &party,
    const AlchemyRecipe &pickedRecipe,
    const AlchemyBenchTables &tables,
    std::span<const AlchemyItemPower> kept,
    const AlchemyPowerChoice &choice)
{
    AlchemyMixOutcome outcome = {};
    const AlchemyRecipe recipe = bottleAsTarget(pickedRecipe, tables);
    const MixLocations locations = findMixItems(party, recipe, tables, kept, choiceFor(pickedRecipe, recipe, choice));
    const std::optional<ItemLocation> &targetLocation = locations.target;
    const std::optional<ItemLocation> &heldLocation = locations.held;
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
// The most powers a chain offers to aim at, and the most plans made to find them.
constexpr int ChainPowerOptionCount = 16;
constexpr int MaxChainPowerPlans = 32;
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

    // The weakest copy that has the needed power.
    std::optional<uint16_t> weakestAtLeast(uint32_t itemId, int need) const
    {
        const auto found = m_items.find(itemId);

        if (found == m_items.end())
        {
            return std::nullopt;
        }

        const auto copy = std::find_if(found->second.begin(), found->second.end(),
            [need](uint16_t power)
            {
                return int(power) >= need;
            });
        return copy != found->second.end() ? std::optional<uint16_t>(*copy) : std::nullopt;
    }

    uint16_t take(uint32_t itemId)
    {
        std::vector<uint16_t> &powers = m_items[itemId];
        const uint16_t power = powers.back();
        powers.pop_back();
        m_undo.push_back({false, itemId, power});
        return power;
    }

    // Takes a copy of the given power, which the stock must have.
    void takePower(uint32_t itemId, uint16_t power)
    {
        std::vector<uint16_t> &powers = m_items[itemId];
        powers.erase(std::find(powers.begin(), powers.end(), power));
        m_undo.push_back({false, itemId, power});
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
    // The plan aims at a power: its steps name the copies they mix.
    bool namesCopies = false;
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
    const AlchemyBenchTables &tables,
    bool keepMixedPotions,
    std::span<const AlchemyItemCount> reserved)
    : m_book(book)
    , m_tables(tables)
    , m_alchemistLevel(alchemist.level)
    , m_bottleItemId(tables.potionSettingTable.emptyBottleItemId())
{
    // The reserved items' copies, strongest first: the first `count` of each are kept.
    std::unordered_map<uint32_t, std::vector<std::pair<uint16_t, uint16_t>>> reservable;

    forEachCarriedItem(party,
        [&](const ItemLocation &, const InventoryItem &item)
        {
            const std::optional<AlchemyIngredientKind> kind = ingredientKind(item.objectDescriptionId, tables);
            const bool reservedItem = std::any_of(reserved.begin(), reserved.end(),
                [&item](const AlchemyItemCount &count) { return count.itemId == item.objectDescriptionId; });

            if (keepMixedPotions && book.isMixedPotion(item.objectDescriptionId))
            {
                m_kept.push_back({item.objectDescriptionId, item.standardEnchantPower});
            }
            else if (kind.has_value() && reservedItem)
            {
                reservable[item.objectDescriptionId].push_back(
                    {item.standardEnchantPower, ingredientPower(item, *kind, tables, alchemist)});
            }
            else if (kind.has_value())
            {
                m_carried.push_back({item.objectDescriptionId, ingredientPower(item, *kind, tables, alchemist)});
            }
        });

    for (const AlchemyItemCount &count : reserved)
    {
        const auto found = reservable.find(count.itemId);

        if (found == reservable.end())
        {
            continue;
        }

        std::vector<std::pair<uint16_t, uint16_t>> &copies = found->second;
        std::sort(copies.begin(), copies.end(), std::greater<>());

        for (size_t index = 0; index < copies.size(); ++index)
        {
            if (index < count.count)
            {
                m_kept.push_back({count.itemId, copies[index].first});
            }
            else
            {
                m_carried.push_back({count.itemId, copies[index].second});
            }
        }

        reservable.erase(found);
    }
}

bool AlchemyChainPlanner::obtain(
    uint32_t itemId,
    const Need &need,
    Stock &stock,
    Search &search,
    int depth,
    uint16_t &power) const
{
    if (!need)
    {
        if (stock.count(itemId) == 0 && !brew(itemId, need, stock, search, depth))
        {
            return false;
        }

        power = stock.strongest(itemId);
        return true;
    }

    // The weakest carried copy that is strong enough; without one a copy is brewed, unless that comes out no
    // stronger than what is carried.
    if (const std::optional<uint16_t> carried = stock.weakestAtLeast(itemId, *need))
    {
        power = *carried;
        return true;
    }

    const bool carried = stock.count(itemId) > 0;
    const uint16_t carriedPower = stock.strongest(itemId);
    const size_t stockMark = stock.mark();
    const size_t stepMark = search.steps.size();
    const bool brewed = brew(itemId, need, stock, search, depth);

    if (brewed && (!carried || search.lastPower > carriedPower))
    {
        power = search.lastPower;
        return true;
    }

    stock.rollback(stockMark);
    search.steps.resize(stepMark);
    power = carriedPower;
    return carried;
}

bool AlchemyChainPlanner::brew(
    uint32_t resultItemId,
    const Need &need,
    Stock &stock,
    Search &search,
    int depth) const
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

    if (found->reagentRecipe && need)
    {
        return fillBottle(*found, *need, stock, search);
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
    const AlchemyRecipe *pStrongest = nullptr;
    uint16_t strongestPower = 0;

    for (const AlchemyRecipe &recipe : recipes)
    {
        const size_t stockMark = stock.mark();
        const size_t stepMark = search.steps.size();

        if (tryRecipe(*found, recipe, need, stock, search, depth))
        {
            if (!need || int(search.lastPower) >= *need)
            {
                search.brewing.erase(resultItemId);
                return true;
            }

            if (pStrongest == nullptr || search.lastPower > strongestPower)
            {
                pStrongest = &recipe;
                strongestPower = search.lastPower;
            }
        }

        stock.rollback(stockMark);
        search.steps.resize(stepMark);
    }

    // No recipe reaches the needed power: the one that came nearest is brewed, and the caller judges it.
    const bool brewed = pStrongest != nullptr && tryRecipe(*found, *pStrongest, need, stock, search, depth);
    search.brewing.erase(resultItemId);
    return brewed;
}

// Fills a bottle with the weakest carried reagent that gives the potion the needed power, of any reagent that makes
// it; with none strong enough, the strongest.
bool AlchemyChainPlanner::fillBottle(const AlchemyBookEntry &entry, int need, Stock &stock, Search &search) const
{
    if (stock.count(m_bottleItemId) == 0)
    {
        search.blockOn(AlchemyChainBlock::MissingBottle, m_bottleItemId);
        return false;
    }

    const AlchemyRecipe *pBest = nullptr;
    uint16_t bestPower = 0;
    bool bestReaches = false;

    for (const AlchemyRecipe &recipe : entry.recipes)
    {
        if (stock.count(recipe.heldItemId) == 0)
        {
            continue;
        }

        const std::optional<uint16_t> enough = stock.weakestAtLeast(recipe.heldItemId, need - int(m_alchemistLevel));
        const bool reaches = enough.has_value();
        const uint16_t power = reaches ? *enough : stock.strongest(recipe.heldItemId);

        if (pBest == nullptr || (reaches && !bestReaches)
            || (reaches == bestReaches && (reaches ? power < bestPower : power > bestPower)))
        {
            pBest = &recipe;
            bestPower = power;
            bestReaches = reaches;
        }
    }

    if (pBest == nullptr)
    {
        search.blockOn(AlchemyChainBlock::MissingReagent, entry.resultItemId);
        return false;
    }

    stock.take(m_bottleItemId);
    stock.takePower(pBest->heldItemId, bestPower);
    search.lastPower = static_cast<uint16_t>(std::min<uint32_t>(m_alchemistLevel + bestPower, 0xFFFFu));
    stock.add(entry.resultItemId, search.lastPower);
    search.steps.push_back({*pBest, entry.resultItemId, {std::nullopt, bestPower}});
    return true;
}

bool AlchemyChainPlanner::mixPotions(
    const AlchemyBookEntry &entry,
    const AlchemyRecipe &recipe,
    const Need &targetNeed,
    const Need &need,
    Stock &stock,
    Search &search,
    int depth) const
{
    // The target is set aside while the held ingredient is found, so brewing one cannot use up the other.
    uint16_t targetPower = 0;

    if (!obtain(recipe.targetItemId, targetNeed, stock, search, depth + 1, targetPower))
    {
        return false;
    }

    stock.takePower(recipe.targetItemId, targetPower);
    // The mix has the average power: the held ingredient makes up what the target lacks or leaves over.
    const Need heldNeed = need ? Need(std::max(0, 2 * *need - int(targetPower))) : Need();
    uint16_t heldPower = 0;

    if (!obtain(recipe.heldItemId, heldNeed, stock, search, depth + 1, heldPower))
    {
        return false;
    }

    stock.takePower(recipe.heldItemId, heldPower);
    search.lastPower = static_cast<uint16_t>((uint32_t(targetPower) + heldPower) / 2u);
    stock.add(entry.resultItemId, search.lastPower);
    stock.add(m_bottleItemId, 0);
    search.steps.push_back({recipe, entry.resultItemId,
        search.namesCopies ? AlchemyPowerChoice{targetPower, heldPower} : AlchemyPowerChoice{}});
    return true;
}

bool AlchemyChainPlanner::tryRecipe(
    const AlchemyBookEntry &entry,
    const AlchemyRecipe &recipe,
    const Need &need,
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
        const uint16_t reagentPower = stock.take(recipe.heldItemId);
        const uint32_t power = m_alchemistLevel + reagentPower;
        search.lastPower = static_cast<uint16_t>(std::min<uint32_t>(power, 0xFFFFu));
        stock.add(entry.resultItemId, search.lastPower);
        search.steps.push_back({recipe, entry.resultItemId,
            search.namesCopies ? AlchemyPowerChoice{std::nullopt, reagentPower} : AlchemyPowerChoice{}});
        return true;
    }

    if (!need)
    {
        return mixPotions(entry, recipe, need, need, stock, search, depth);
    }

    const size_t stockMark = stock.mark();
    const size_t stepMark = search.steps.size();

    if (mixPotions(entry, recipe, need, need, stock, search, depth) && int(search.lastPower) >= *need)
    {
        return true;
    }

    // A weak second ingredient may still do beside the strongest first one.
    stock.rollback(stockMark);
    search.steps.resize(stepMark);
    return mixPotions(entry, recipe, std::nullopt, need, stock, search, depth);
}

AlchemyChainPlan AlchemyChainPlanner::plan(
    uint32_t resultItemId,
    uint32_t maxBrews,
    const std::optional<uint16_t> &aim) const
{
    AlchemyChainPlan plan = {};
    plan.kept = m_kept;
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

    const Need need = aim ? Need(int(*aim)) : Need();

    while (plan.brewCount < maxBrews && plan.steps.size() < MaxChainSteps)
    {
        Search search;
        search.namesCopies = aim.has_value();
        const size_t stockMark = stock.mark();
        bool brewed = brew(resultItemId, need, stock, search, 0);

        if (aim && !(brewed && search.lastPower >= *aim))
        {
            // What the weakest copies miss, the strongest may still reach.
            stock.rollback(stockMark);
            search.steps.clear();
            brewed = brew(resultItemId, std::nullopt, stock, search, 0) && search.lastPower >= *aim;

            if (!brewed)
            {
                stock.rollback(stockMark);
            }
        }

        if (!brewed)
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

std::vector<AlchemyChainPowerOption> AlchemyChainPlanner::powerOptions(uint32_t resultItemId) const
{
    std::vector<AlchemyChainPowerOption> options;
    const AlchemyChainPlan strongest = plan(resultItemId, 1);
    const AlchemyChainPlan weakest = plan(resultItemId, 1, uint16_t(0));

    if (strongest.brewCount == 0 || weakest.brewCount == 0)
    {
        return options;
    }

    // Each aim is one past the power the last one gave, or a stride past it in a wide range.
    const int top = strongest.resultPower;
    const int stride = std::max(1, (top - int(weakest.resultPower)) / (ChainPowerOptionCount - 1));
    int aim = 0;

    for (int planned = 0; planned < MaxChainPowerPlans && aim <= 0xFFFF; ++planned)
    {
        const AlchemyChainPlan aimed = planned == 0 ? weakest : plan(resultItemId, 1, uint16_t(aim));

        if (aimed.brewCount == 0)
        {
            break;
        }

        const int power = aimed.resultPower;
        options.push_back({aimed.resultPower, uint16_t(aim)});
        aim = power >= top ? power + 1 : std::min(power + stride, top);
    }

    return options;
}

std::optional<uint16_t> AlchemyChainPlanner::aimForPower(uint32_t resultItemId, uint16_t power) const
{
    for (const AlchemyChainPowerOption &option : powerOptions(resultItemId))
    {
        if (option.power == power)
        {
            return option.aim;
        }
    }

    return std::nullopt;
}

uint64_t AlchemyChainPlanner::stockKey() const
{
    uint64_t hash = 1469598103934665603ull;
    const auto mixIn =
        [&hash](uint64_t value)
        {
            hash = (hash ^ value) * 1099511628211ull;
        };
    mixIn(m_alchemistLevel);

    for (const auto &[itemId, power] : m_carried)
    {
        mixIn((uint64_t(itemId) << 16) | power);
    }

    mixIn(m_kept.size());
    return hash;
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
        outcome.lastMix = mix(party, step.recipe, tables, plan.kept, step.choice);

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
