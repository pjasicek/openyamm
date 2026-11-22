#include "game/gameplay/SearchableLootPropRuntime.h"

#include "game/items/ItemGenerator.h"
#include "game/tables/ItemTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MinimumGeneratedTreasureLevel = 1;
constexpr int MaximumGeneratedTreasureLevel = 6;
}

bool searchableLootPropHazardTriggers(const MapSearchableLootPropSource &source, uint32_t rollOneToOneHundred)
{
    if (source.hazardCondition != "disease"
        || source.hazardComparison != "roll_1_100_strictly_less_than"
        || source.hazardChance <= 0)
    {
        return false;
    }

    const uint32_t normalizedRoll = std::clamp<uint32_t>(rollOneToOneHundred, 1, 100);
    return normalizedRoll < static_cast<uint32_t>(source.hazardChance);
}

uint32_t searchableLootPropSeed(uint32_t sessionSeed, const std::string &sourceId)
{
    uint32_t hash = 2166136261u;
    for (unsigned char value : sourceId)
    {
        hash ^= value;
        hash *= 16777619u;
    }
    return sessionSeed ^ hash;
}

SearchableLootPropResult applySearchableLootPropResult(
    const MapSearchableLootPropSource &source,
    SearchableLootPropState &state,
    uint32_t hazardRollOneToOneHundred,
    const std::optional<InventoryItem> &generatedItem,
    Party &party)
{
    SearchableLootPropResult result = {};

    if (source.sourceId.empty() || source.kind != "bone_pile")
    {
        return result;
    }

    result.handled = true;
    if (state.searchedSourceIds.contains(source.sourceId))
    {
        result.alreadySearched = true;
        return result;
    }

    // Native MM9 commits the one-shot searched flag before applying disease or generating the item.
    state.searchedSourceIds.insert(source.sourceId);

    if (searchableLootPropHazardTriggers(source, hazardRollOneToOneHundred))
    {
        result.diseaseApplied = party.applyBlockableMemberCondition(
            party.activeMemberIndex(),
            CharacterCondition::DiseaseWeak,
            party.gameMinutes());
    }

    if (!generatedItem.has_value())
    {
        return result;
    }

    result.generatedItem = generatedItem;
    result.itemGenerated = true;
    result.itemAwarded = party.tryGrantInventoryItem(*generatedItem);
    result.inventoryFull = !result.itemAwarded;
    return result;
}

SearchableLootPropResult searchLootProp(
    const MapSearchableLootPropSource &source,
    SearchableLootPropState &state,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    Party &party,
    const std::string &worldId,
    std::mt19937 &rng)
{
    if (state.searchedSourceIds.contains(source.sourceId))
    {
        SearchableLootPropResult result = {};
        result.handled = source.kind == "bone_pile" && !source.sourceId.empty();
        result.alreadySearched = result.handled;
        return result;
    }

    const uint32_t hazardRoll = std::uniform_int_distribution<uint32_t>(1, 100)(rng);
    std::optional<InventoryItem> generatedItem;
    if (source.lootRolls > 0 && source.randomTreasureLevel > 0)
    {
        generatedItem = ItemGenerator::generateRandomInventoryItem(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            ItemGenerationRequest{
                .treasureLevel = std::clamp(
                    source.randomTreasureLevel,
                    MinimumGeneratedTreasureLevel,
                    MaximumGeneratedTreasureLevel),
                .mode = ItemGenerationMode::ChestLoot,
                .worldId = worldId,
            },
            &party,
            rng);
    }

    return applySearchableLootPropResult(source, state, hazardRoll, generatedItem, party);
}
}
