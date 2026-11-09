#include "game/maps/MapItemSourceYml.h"

#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <exception>
#include <algorithm>
#include <limits>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
template <typename ValueType>
bool readScalar(
    const YAML::Node &parentNode,
    const char *key,
    ValueType &value,
    std::string &errorMessage,
    bool required = true)
{
    const YAML::Node childNode = parentNode[key];
    if (!childNode)
    {
        if (required)
        {
            errorMessage = std::string("missing item-source field: ") + key;
            return false;
        }
        return true;
    }
    if (!childNode.IsScalar())
    {
        errorMessage = std::string("item-source field must be scalar: ") + key;
        return false;
    }

    try
    {
        value = childNode.as<ValueType>();
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse item-source field ") + key + ": " + exception.what();
        return false;
    }
    return true;
}

bool readPosition(const YAML::Node &node, MapItemSourcePosition &position, std::string &errorMessage)
{
    if (!node || !node.IsMap())
    {
        errorMessage = "item-source position must be a map";
        return false;
    }
    return readScalar(node, "x", position.x, errorMessage)
        && readScalar(node, "y", position.y, errorMessage)
        && readScalar(node, "z", position.z, errorMessage);
}

bool readKind(const YAML::Node &node, LootContainerKind &kind, std::string &errorMessage)
{
    std::string value;
    if (!readScalar(node, "kind", value, errorMessage))
    {
        return false;
    }

    value = toLowerCopy(value);
    if (value == "chest")
    {
        kind = LootContainerKind::Chest;
        return true;
    }
    if (value == "treasure_bag")
    {
        kind = LootContainerKind::TreasureBag;
        return true;
    }
    errorMessage = "item-source kind must be chest or treasure_bag";
    return false;
}

bool readFixedItems(
    const YAML::Node &parentNode,
    std::vector<MapFixedContainerItem> &fixedItems,
    std::string &errorMessage)
{
    const YAML::Node itemsNode = parentNode["fixed_items"];
    if (!itemsNode || !itemsNode.IsSequence())
    {
        errorMessage = "item-source fixed_items must be a sequence";
        return false;
    }

    fixedItems.reserve(itemsNode.size());
    for (const YAML::Node &itemNode : itemsNode)
    {
        MapFixedContainerItem item = {};
        if (!itemNode.IsMap()
            || !readScalar(itemNode, "slot", item.slot, errorMessage)
            || !readScalar(itemNode, "raw_mm9_item_id", item.rawMm9ItemId, errorMessage)
            || !readScalar(itemNode, "item_id", item.itemId, errorMessage))
        {
            return false;
        }
        if (item.slot == 0 || item.itemId == 0)
        {
            errorMessage = "item-source fixed item slot and item_id must be positive";
            return false;
        }
        fixedItems.push_back(item);
    }
    return true;
}

bool readSourceIdentity(
    const YAML::Node &node,
    std::string &sourceId,
    uint32_t &sourceObjectIndex,
    std::string &sourceName,
    MapItemSourcePosition &position,
    std::string &errorMessage)
{
    return readScalar(node, "source_id", sourceId, errorMessage)
        && readScalar(node, "source_object_index", sourceObjectIndex, errorMessage)
        && readScalar(node, "source_name", sourceName, errorMessage)
        && readPosition(node["position"], position, errorMessage);
}

bool readUInt32Sequence(
    const YAML::Node &parentNode,
    const char *key,
    std::vector<uint32_t> &values,
    std::string &errorMessage)
{
    const YAML::Node sequenceNode = parentNode[key];
    if (!sequenceNode || !sequenceNode.IsSequence())
    {
        errorMessage = std::string("item-source ") + key + " must be a sequence";
        return false;
    }
    values.reserve(sequenceNode.size());
    try
    {
        for (const YAML::Node &valueNode : sequenceNode)
        {
            values.push_back(valueNode.as<uint32_t>());
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse item-source sequence ") + key + ": " + exception.what();
        return false;
    }
    return true;
}

bool readStringSequence(
    const YAML::Node &parentNode,
    const char *key,
    std::vector<std::string> &values,
    std::string &errorMessage)
{
    const YAML::Node sequenceNode = parentNode[key];
    if (!sequenceNode || !sequenceNode.IsSequence())
    {
        errorMessage = std::string("item-source ") + key + " must be a sequence";
        return false;
    }
    values.reserve(sequenceNode.size());
    try
    {
        for (const YAML::Node &valueNode : sequenceNode)
        {
            values.push_back(valueNode.as<std::string>());
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse item-source sequence ") + key + ": " + exception.what();
        return false;
    }
    return true;
}

bool readWorldItem(const YAML::Node &node, MapWorldItemSource &source, std::string &errorMessage)
{
    if (!node.IsMap()
        || !readSourceIdentity(
            node,
            source.sourceId,
            source.sourceObjectIndex,
            source.sourceName,
            source.position,
            errorMessage)
        || !readScalar(node, "item_id", source.itemId, errorMessage)
        || !readUInt32Sequence(node, "random_item_pool", source.randomItemPool, errorMessage)
        || !readUInt32Sequence(node, "required_qbits", source.requiredQBits, errorMessage)
        || !readUInt32Sequence(node, "forbidden_qbits", source.forbiddenQBits, errorMessage)
        || (node["pickup_qbits"] && !readUInt32Sequence(node, "pickup_qbits", source.pickupQBits, errorMessage))
        || !readUInt32Sequence(node, "set_qbits", source.setQBits, errorMessage)
        || !readScalar(node, "pickup_event", source.pickupEvent, errorMessage))
    {
        return false;
    }

    if (const YAML::Node poseNode = node["pose"])
    {
        std::array<float, 3> pose = {};
        if (!poseNode.IsMap()
            || !readScalar(poseNode, "yaw", pose[0], errorMessage)
            || !readScalar(poseNode, "pitch", pose[1], errorMessage)
            || !readScalar(poseNode, "roll", pose[2], errorMessage))
        {
            errorMessage = "world item pose needs yaw, pitch and roll";
            return false;
        }
        source.poseDegrees = pose;
    }

    if (source.itemId == 0 && source.randomItemPool.empty())
    {
        errorMessage = "world item requires item_id or random_item_pool";
        return false;
    }
    return true;
}

bool readLootContainer(
    const YAML::Node &node,
    MapLootContainerSource &source,
    std::string &errorMessage)
{
    const bool parsed = node.IsMap()
        && readSourceIdentity(
            node,
            source.sourceId,
            source.sourceObjectIndex,
            source.sourceName,
            source.position,
            errorMessage)
        && readScalar(node, "container_id", source.containerId, errorMessage)
        && readKind(node, source.kind, errorMessage)
        && readScalar(node, "presentation", source.presentation, errorMessage)
        && readScalar(node, "random_treasure_level", source.randomTreasureLevel, errorMessage)
        && readScalar(node, "treasure_type", source.treasureType, errorMessage)
        && readScalar(node, "gold", source.gold, errorMessage)
        && readScalar(node, "gold_only", source.goldOnly, errorMessage)
        && readScalar(node, "random", source.random, errorMessage)
        && readScalar(node, "ai_drop", source.aiDrop, errorMessage)
        && readScalar(node, "trap_level", source.trapLevel, errorMessage)
        && readScalar(node, "should_repopulate", source.shouldRepopulate, errorMessage)
        && readFixedItems(node, source.fixedItems, errorMessage)
        && readScalar(node, "remove_when_empty", source.removeWhenEmpty, errorMessage)
        && readScalar(node, "random_records", source.randomRecords, errorMessage, false);
    if (!parsed)
    {
        return false;
    }
    if (source.randomRecords == 0 || source.randomRecords + source.fixedItems.size() > 81)
    {
        errorMessage = "loot container random_records must be positive and fit the chest";
        return false;
    }
    if (!node["random_item_pool"] && !node["random_item_count"])
    {
        return true;
    }
    if (!readUInt32Sequence(node, "random_item_pool", source.randomItemPool, errorMessage)
        || !readScalar(node, "random_item_count", source.randomItemCount, errorMessage))
    {
        return false;
    }
    std::vector<uint32_t> sortedPool = source.randomItemPool;
    std::sort(sortedPool.begin(), sortedPool.end());
    if (!source.random || source.goldOnly || sortedPool.empty() || sortedPool.front() == 0
        || sortedPool.back() > uint32_t(std::numeric_limits<int32_t>::max())
        || std::adjacent_find(sortedPool.begin(), sortedPool.end()) != sortedPool.end()
        || source.randomItemCount == 0 || source.randomItemCount > sortedPool.size()
        || source.randomItemCount + source.fixedItems.size() + (source.gold > 0 ? 1 : 0) > 81)
    {
        errorMessage = "random chest pool requires unique positive item IDs, random=true, gold_only=false, "
            "and a positive count within the pool and chest capacity";
        return false;
    }
    return true;
}

bool readSearchableLootProp(
    const YAML::Node &node,
    MapSearchableLootPropSource &source,
    std::string &errorMessage)
{
    const YAML::Node hazardNode = node["hazard"];
    return node.IsMap()
        && readSourceIdentity(
            node,
            source.sourceId,
            source.sourceObjectIndex,
            source.sourceName,
            source.position,
            errorMessage)
        && readScalar(node, "kind", source.kind, errorMessage)
        && readScalar(node, "random_treasure_level", source.randomTreasureLevel, errorMessage)
        && readScalar(node, "loot_rolls", source.lootRolls, errorMessage)
        && hazardNode && hazardNode.IsMap()
        && readScalar(hazardNode, "condition", source.hazardCondition, errorMessage)
        && readScalar(hazardNode, "chance", source.hazardChance, errorMessage)
        && readScalar(hazardNode, "comparison", source.hazardComparison, errorMessage)
        && readScalar(node, "source_disease_power", source.sourceDiseasePower, errorMessage)
        && readScalar(node, "keep_visual_after_search", source.keepVisualAfterSearch, errorMessage);
}

bool readSpawnedLootContainer(
    const YAML::Node &node,
    MapSpawnedLootContainerSource &source,
    std::string &errorMessage)
{
    return node.IsMap()
        && readSourceIdentity(
            node,
            source.sourceId,
            source.sourceObjectIndex,
            source.sourceName,
            source.position,
            errorMessage)
        && readKind(node, source.kind, errorMessage)
        && readScalar(node, "presentation", source.presentation, errorMessage)
        && readScalar(node, "random_treasure_level", source.randomTreasureLevel, errorMessage)
        && readScalar(node, "treasure_type", source.treasureType, errorMessage)
        && readScalar(node, "gold", source.gold, errorMessage)
        && readScalar(node, "gold_only", source.goldOnly, errorMessage)
        && readScalar(node, "random", source.random, errorMessage)
        && readScalar(node, "ai_drop", source.aiDrop, errorMessage)
        && readFixedItems(node, source.fixedItems, errorMessage)
        && readScalar(node, "remove_when_empty", source.removeWhenEmpty, errorMessage);
}

bool readPersistentItemMechanism(
    const YAML::Node &node,
    MapPersistentItemMechanismSource &source,
    std::string &errorMessage)
{
    const YAML::Node grantsNode = node["grant_items"];
    if (!node.IsMap()
        || !readSourceIdentity(
            node,
            source.sourceId,
            source.sourceObjectIndex,
            source.sourceName,
            source.position,
            errorMessage)
        || !readScalar(node, "kind", source.kind, errorMessage)
        || !readScalar(node, "handler", source.handler, errorMessage)
        || !readUInt32Sequence(node, "required_items", source.requiredItems, errorMessage)
        || !readUInt32Sequence(node, "random_item_pool", source.randomItemPool, errorMessage)
        || !grantsNode || !grantsNode.IsSequence()
        || !readStringSequence(node, "model_variants", source.modelVariants, errorMessage)
        || !readStringSequence(node, "model_variant_skins", source.modelVariantSkins, errorMessage))
    {
        return false;
    }
    if (source.modelVariants.size() != source.modelVariantSkins.size())
    {
        errorMessage = "persistent item-mechanism model variant and skin counts must match";
        return false;
    }

    source.grantItems.reserve(grantsNode.size());
    for (const YAML::Node &grantNode : grantsNode)
    {
        MapWorldItemGrant grant = {};
        if (!grantNode.IsMap()
            || !readScalar(grantNode, "raw_mm9_item_id", grant.rawMm9ItemId, errorMessage)
            || !readScalar(grantNode, "item_id", grant.itemId, errorMessage)
            || !readScalar(grantNode, "quantity", grant.quantity, errorMessage))
        {
            return false;
        }
        if (grant.itemId == 0 || grant.quantity == 0)
        {
            errorMessage = "persistent item-mechanism grants must have positive item_id and quantity";
            return false;
        }
        source.grantItems.push_back(grant);
    }
    return true;
}

bool readMm9Barrel(const YAML::Node &node, MapMm9BarrelSource &source, std::string &errorMessage)
{
    if (!node.IsMap()
        || !readSourceIdentity(
            node,
            source.sourceId,
            source.sourceObjectIndex,
            source.sourceName,
            source.position,
            errorMessage)
        || !readScalar(node, "interaction_event_id", source.interactionEventId, errorMessage)
        || !readScalar(node, "liquid_texture_cog", source.liquidTextureCog, errorMessage)
        || !readScalar(node, "bmodel_index", source.bmodelIndex, errorMessage)
        || !readUInt32Sequence(node, "liquid_faces", source.liquidFaces, errorMessage)
        || !readStringSequence(node, "liquid_texture_aliases", source.liquidTextureAliases, errorMessage))
    {
        return false;
    }
    if (source.interactionEventId == 0 || source.liquidTextureCog == 0
        || source.liquidTextureAliases.size() != 8)
    {
        errorMessage = "MM9 barrel requires valid event/cog ids and exactly eight liquid texture aliases";
        return false;
    }
    return true;
}

template <typename SourceType, typename Reader>
bool readSequence(
    const YAML::Node &rootNode,
    const char *key,
    std::vector<SourceType> &sources,
    Reader reader,
    std::string &errorMessage)
{
    const YAML::Node sequenceNode = rootNode[key];
    if (!sequenceNode)
    {
        return true;
    }
    if (!sequenceNode.IsSequence())
    {
        errorMessage = std::string(key) + " must be a sequence";
        return false;
    }

    sources.reserve(sequenceNode.size());
    for (const YAML::Node &sourceNode : sequenceNode)
    {
        SourceType source = {};
        if (!reader(sourceNode, source, errorMessage))
        {
            return false;
        }
        sources.push_back(std::move(source));
    }
    return true;
}
}

bool parseMapItemSourceData(
    const YAML::Node &rootNode,
    MapItemSourceData &itemSources,
    std::string &errorMessage)
{
    if (!readSequence(
            rootNode,
            "world_items",
            itemSources.worldItems,
            readWorldItem,
            errorMessage)
        || !readSequence(
            rootNode,
            "loot_containers",
            itemSources.lootContainers,
            readLootContainer,
            errorMessage)
        || !readSequence(
            rootNode,
            "searchable_loot_props",
            itemSources.searchableLootProps,
            readSearchableLootProp,
            errorMessage)
        || !readSequence(
            rootNode,
            "spawned_loot_containers",
            itemSources.spawnedLootContainers,
            readSpawnedLootContainer,
            errorMessage)
        || !readSequence(
            rootNode,
            "persistent_item_mechanisms",
            itemSources.persistentItemMechanisms,
            readPersistentItemMechanism,
            errorMessage)
        || !readSequence(
            rootNode,
            "barrels",
            itemSources.mm9Barrels,
            readMm9Barrel,
            errorMessage))
    {
        return false;
    }

    const YAML::Node actorOverridesNode = rootNode["actor_loot_overrides"];
    if (!actorOverridesNode)
    {
        return true;
    }
    if (!actorOverridesNode.IsSequence())
    {
        errorMessage = "actor_loot_overrides must be a sequence";
        return false;
    }

    itemSources.actorLootOverrides.reserve(actorOverridesNode.size());
    for (const YAML::Node &overrideNode : actorOverridesNode)
    {
        MapActorLootOverride overrideEntry = {};
        if (!overrideNode.IsMap()
            || !readScalar(
                overrideNode,
                "source_object_index",
                overrideEntry.sourceObjectIndex,
                errorMessage)
            || !readScalar(
                overrideNode,
                "procedural_death_loot",
                overrideEntry.proceduralDeathLoot,
                errorMessage))
        {
            return false;
        }
        itemSources.actorLootOverrides.push_back(overrideEntry);
    }
    return true;
}
}
