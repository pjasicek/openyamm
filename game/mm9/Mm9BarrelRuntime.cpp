#include "game/mm9/Mm9BarrelRuntime.h"

#include "engine/Localization.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/mm9/Mm9PrimaryStats.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t Mm9NativePartyMemberCount = 4;
constexpr uint32_t StatReward = 2;
constexpr uint32_t MaximumStat = 500;

std::optional<Mm9PrimaryStat> barrelStat(Mm9BarrelType type)
{
    switch (type)
    {
        case Mm9BarrelType::RedMight: return Mm9PrimaryStat::Might;
        case Mm9BarrelType::BlueMagic: return Mm9PrimaryStat::Magic;
        case Mm9BarrelType::GreenEndurance: return Mm9PrimaryStat::Endurance;
        case Mm9BarrelType::PurpleSpeed: return Mm9PrimaryStat::Speed;
        case Mm9BarrelType::WhiteLuck: return Mm9PrimaryStat::Luck;
        case Mm9BarrelType::YellowAccuracy: return Mm9PrimaryStat::Accuracy;
        case Mm9BarrelType::Swamp:
        case Mm9BarrelType::Water:
            return std::nullopt;
    }
    return std::nullopt;
}

int bestPartyLuckModifier(const Party &party)
{
    uint32_t bestLuck = 0;
    for (const Character &member : party.members())
    {
        bestLuck = std::max(bestLuck, member.luck);
    }
    return static_cast<int>(std::min<uint32_t>(bestLuck, static_cast<uint32_t>(INT32_MAX)));
}
}

uint32_t mm9BarrelSeed(uint32_t sessionSeed, const std::string &sourceId)
{
    uint32_t hash = 2166136261u;
    for (unsigned char value : sourceId)
    {
        hash ^= value;
        hash *= 16777619u;
    }
    return sessionSeed ^ hash ^ 0x42415252u;
}

MapDeltaMm9BarrelState &ensureMm9BarrelState(
    std::vector<MapDeltaMm9BarrelState> &states,
    uint32_t sourceObjectIndex,
    std::mt19937 &rng)
{
    const auto stateIt = std::find_if(
        states.begin(),
        states.end(),
        [sourceObjectIndex](const MapDeltaMm9BarrelState &state)
        {
            return state.sourceObjectIndex == sourceObjectIndex;
        });
    if (stateIt != states.end())
    {
        return *stateIt;
    }
    states.push_back(MapDeltaMm9BarrelState{
        sourceObjectIndex,
        static_cast<Mm9BarrelType>(std::uniform_int_distribution<int>(1, 8)(rng)),
        false,
    });
    return states.back();
}

size_t mm9BarrelLiquidTextureIndex(const MapDeltaMm9BarrelState &state)
{
    return state.used ? 7 : static_cast<size_t>(state.type) - 1;
}

std::optional<InventoryItem> generateMm9TreasureLevelOneItem(
    const ItemTable &itemTable,
    int bestPartyLuckModifier,
    std::mt19937 &rng)
{
    (void)bestPartyLuckModifier;
    const uint8_t tier = static_cast<uint8_t>(std::uniform_int_distribution<int>(1, 2)(rng));
    std::vector<uint32_t> candidates;
    for (const ItemDefinition &entry : itemTable.entries())
    {
        if (entry.itemId != 0
            && entry.packageId == "mm9"
            && entry.normalizedTier == tier
            && !entry.hasContentFlag("NoRandom")
            && !ItemRuntime::isRareItem(entry))
        {
            candidates.push_back(entry.itemId);
        }
    }
    if (candidates.empty())
    {
        return std::nullopt;
    }
    const uint32_t itemId = candidates[std::uniform_int_distribution<size_t>(0, candidates.size() - 1)(rng)];
    return ItemGenerator::makeInventoryItem(itemId, itemTable, ItemGenerationMode::ChestLoot);
}

Mm9BarrelResult useMm9Barrel(
    MapDeltaMm9BarrelState &state,
    Party &party,
    const ItemTable &itemTable,
    std::mt19937 &rng)
{
    Mm9BarrelResult result = {};
    result.handled = true;
    const size_t memberIndex = party.activeMemberIndex();
    Character *pMember = memberIndex < Mm9NativePartyMemberCount ? party.member(memberIndex) : nullptr;
    if (pMember == nullptr)
    {
        result.invalidCharacter = true;
        result.soundName = "sounds/events/error.wav";
        return result;
    }
    if (state.used)
    {
        result.alreadyUsed = true;
        return result;
    }

    state.used = true;
    const std::optional<Mm9PrimaryStat> stat = barrelStat(state.type);
    if (stat.has_value())
    {
        result.statRaised = addMm9PermanentPrimaryStat(*pMember, *stat, StatReward, MaximumStat);
        result.statusMessage = Engine::tr("{name} gains +{amount} {stat}!",
            {{"name", pMember->name}, {"amount", StatReward}, {"stat", Engine::tr(mm9PrimaryStatName(*stat))}});
        result.soundName = "sounds/events/quest.wav";
        return result;
    }
    if (state.type == Mm9BarrelType::Swamp)
    {
        // The native barrel constructs disease condition kind 2 at severity 1. The shared condition projection for
        // that least-severe MM9 disease state is DiseaseWeak.
        result.diseaseApplied = party.applyMemberCondition(memberIndex, CharacterCondition::DiseaseWeak);
        result.generatedItem = generateMm9TreasureLevelOneItem(itemTable, bestPartyLuckModifier(party), rng);
        result.itemGenerated = result.generatedItem.has_value();
        if (result.generatedItem.has_value())
        {
            result.itemAwarded = party.tryGrantInventoryItemToMember(memberIndex, *result.generatedItem);
            result.inventoryFull = !result.itemAwarded;
        }
        result.statusMessage = Engine::tr("{name} becomes diseased, but gains an item!", {{"name", pMember->name}});
        result.soundName = "sounds/events/quest.wav";
    }
    return result;
}
}
