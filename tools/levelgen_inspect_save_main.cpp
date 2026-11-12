#include "game/maps/SaveGame.h"

#include <iostream>
#include <set>

#include <yaml-cpp/yaml.h>

using namespace OpenYAMM::Game;

namespace
{
YAML::Node itemsNode(const std::vector<InventoryItem> &items)
{
    YAML::Node result(YAML::NodeType::Sequence);
    for (const InventoryItem &item : items)
    {
        YAML::Node entry;
        entry["item_id"] = item.objectDescriptionId;
        entry["quantity"] = item.quantity;
        entry["standard_enchant"] = item.standardEnchantId;
        entry["standard_power"] = item.standardEnchantPower;
        entry["special_enchant"] = item.specialEnchantId;
        result.push_back(entry);
    }
    return result;
}

YAML::Node chestNode(const GameplayChestViewState &view)
{
    YAML::Node result;
    result["id"] = view.chestId;
    result["flags"] = view.flags;
    result["grid_width"] = uint32_t(view.gridWidth);
    result["grid_height"] = uint32_t(view.gridHeight);
    for (const bool hidden : {false, true})
    {
        YAML::Node items(YAML::NodeType::Sequence);
        for (const GameplayChestItemState &item : hidden ? view.hiddenItems : view.items)
        {
            YAML::Node entry;
            entry["item_id"] = item.itemId;
            entry["quantity"] = item.quantity;
            entry["gold"] = item.goldAmount;
            entry["is_gold"] = item.isGold;
            entry["standard_enchant"] = item.item.standardEnchantId;
            entry["standard_power"] = item.item.standardEnchantPower;
            entry["special_enchant"] = item.item.specialEnchantId;
            entry["x"] = uint32_t(item.gridX);
            entry["y"] = uint32_t(item.gridY);
            items.push_back(entry);
        }
        result[hidden ? "hidden_items" : "items"] = items;
    }
    return result;
}

YAML::Node projectilesNode(const GameplayProjectileService::Snapshot &state)
{
    YAML::Node projectiles(YAML::NodeType::Sequence);
    for (const GameplayProjectileService::ProjectileState &projectile : state.projectiles)
    {
        YAML::Node entry;
        entry["source_kind"] = uint32_t(projectile.sourceKind);
        entry["source_id"] = projectile.sourceId;
        entry["spell_id"] = projectile.spellId;
        entry["damage"] = projectile.damage;
        entry["source"] = std::vector<float>{projectile.sourceX, projectile.sourceY, projectile.sourceZ};
        entry["position"] = std::vector<float>{projectile.x, projectile.y, projectile.z};
        entry["velocity"] = std::vector<float>{projectile.velocityX, projectile.velocityY, projectile.velocityZ};
        entry["sector_id"] = projectile.sectorId;
        entry["expired"] = projectile.isExpired;
        projectiles.push_back(entry);
    }
    return projectiles;
}

template<typename World>
YAML::Node worldNode(const World &world)
{
    YAML::Node result;
    result["game_minutes"] = world.gameMinutes;
    result["chest_seed"] = world.sessionChestSeed;
    YAML::Node chests(YAML::NodeType::Sequence);
    for (const std::optional<GameplayChestViewState> &view : world.materializedChestViews)
    {
        if (view)
        {
            chests.push_back(chestNode(*view));
        }
    }
    result["materialized_chests"] = chests;
    if (world.activeChestView)
    {
        result["active_chest"] = chestNode(*world.activeChestView);
    }
    return result;
}
}

int main(int argc, char **argv)
{
    if (argc != 2)
    {
        std::cerr << "Usage: openyamm_levelgen_inspect_save SAVE.oysav\n";
        return 2;
    }
    std::string error;
    const std::optional<GameSaveData> save = loadGameDataFromPath(argv[1], error);
    if (!save)
    {
        std::cerr << error << '\n';
        return 1;
    }
    YAML::Node result;
    result["map"] = save->mapFileName;
    result["game_minutes"] = save->savedGameMinutes;
    result["gold"] = save->party.gold;
    result["food"] = save->party.food;
    result["house_stock_seed"] = save->party.houseStockSeed;
    result["held_item_active"] = save->heldInventoryItemActive;
    result["held_item_id"] = save->heldInventoryItem.objectDescriptionId;
    const std::set<uint32_t> questBits(save->party.questBits.begin(), save->party.questBits.end());
    result["quest_bits"] = YAML::Node(YAML::NodeType::Sequence);
    result["quest_bits"].SetStyle(YAML::EmitterStyle::Flow);
    for (const uint32_t questBit : questBits)
    {
        result["quest_bits"].push_back(questBit);
    }
    for (const Character &member : save->party.members)
    {
        YAML::Node entry;
        entry["name"] = member.name;
        entry["health"] = member.health;
        entry["inventory"] = itemsNode(member.inventory);
        result["party"].push_back(entry);
    }
    for (const Party::HouseStockState &stock : save->party.houseStockStates)
    {
        YAML::Node entry;
        entry["house_id"] = stock.houseId;
        entry["next_refresh_minutes"] = stock.nextRefreshGameMinutes;
        entry["standard"] = itemsNode(stock.standardStock);
        entry["special"] = itemsNode(stock.specialStock);
        result["house_stocks"].push_back(entry);
    }
    if (save->hasOutdoorRuntimeState)
    {
        result["outdoor"] = worldNode(save->outdoorWorld);
        result["outdoor"]["projectile_count"] = save->outdoorWorld.projectiles.size();
        result["outdoor"]["actor_count"] = save->outdoorWorld.mapActors.size();
        YAML::Node actors(YAML::NodeType::Sequence);
        for (const OutdoorWorldRuntime::MapActorState &actor : save->outdoorWorld.mapActors)
        {
            YAML::Node entry;
            entry["actor_id"] = actor.actorId;
            entry["monster_id"] = actor.monsterId;
            entry["name"] = actor.displayName;
            entry["position"] = std::vector<int>{actor.x, actor.y, actor.z};
            entry["home"] = std::vector<int>{actor.homeX, actor.homeY, actor.homeZ};
            entry["hp"] = actor.currentHp;
            entry["max_hp"] = actor.maxHp;
            entry["dead"] = actor.isDead;
            entry["invisible"] = actor.isInvisible;
            entry["hostile"] = actor.hostileToParty;
            entry["ai_state"] = int(actor.aiState);
            entry["spawned_at_runtime"] = actor.spawnedAtRuntime;
            entry["summoner_member"] = actor.summonerMemberIndex;
            actors.push_back(entry);
        }
        result["outdoor"]["actors"] = actors;
        result["outdoor"]["timer_count"] = save->outdoorWorld.timers.size();
        YAML::Node timers(YAML::NodeType::Sequence);
        for (const ScriptedEventTimerState &timer : save->outdoorWorld.timers)
        {
            YAML::Node entry;
            entry["event_id"] = timer.definition.eventId;
            entry["scope"] = timer.definition.scope == ScriptedEventScope::Global ? "global" : "map";
            entry["next_alarm_minutes"] = timer.nextAlarmGameMinutes;
            timers.push_back(entry);
        }
        result["outdoor"]["timers"] = timers;
        result["outdoor"]["world_item_count"] = save->outdoorWorld.worldItems.size();
        const OutdoorMoveState &movement = save->outdoorParty.movementState;
        result["outdoor"]["party_position"] = std::vector<float>{movement.x, movement.y, movement.footZ};
    }
    if (save->hasIndoorSceneState)
    {
        result["indoor"] = worldNode(save->indoorScene.worldRuntime);
        result["indoor"]["projectiles"] = projectilesNode(save->indoorScene.worldRuntime.projectileState);
        result["indoor"]["projectile_count"] = save->indoorScene.worldRuntime.projectileState.projectiles.size();
        const IndoorMoveState &movement = save->indoorScene.partyRuntime.movementState;
        result["indoor"]["party_position"] = std::vector<float>{movement.x, movement.y, movement.footZ};
        if (save->indoorScene.mapDeltaData)
        {
            const std::vector<IndoorWorldRuntime::MapActorAiState> &aiStates =
                save->indoorScene.worldRuntime.mapActorAiStates;
            YAML::Node actors(YAML::NodeType::Sequence);
            for (size_t index = 0; index < save->indoorScene.mapDeltaData->actors.size(); ++index)
            {
                const MapDeltaActor &actor = save->indoorScene.mapDeltaData->actors[index];
                YAML::Node entry;
                entry["index"] = index;
                entry["monster_id"] = actor.monsterId;
                entry["name"] = actor.name;
                entry["position"] = std::vector<int>{actor.x, actor.y, actor.z};
                entry["sector"] = actor.sectorId;
                entry["hp"] = actor.hp;
                entry["attributes"] = actor.attributes;
                entry["spawned_after_fill"] = actor.spawnedAfterFill;
                entry["summoner_member"] = actor.summonerMemberIndex;
                if (index < aiStates.size())
                {
                    const IndoorWorldRuntime::MapActorAiState &ai = aiStates[index];
                    entry["ai_name"] = ai.displayName;
                    entry["ai_position"] = std::vector<float>{ai.preciseX, ai.preciseY, ai.preciseZ};
                    entry["hostile"] = ai.hostileToParty;
                    entry["motion_state"] = int(ai.motionState);
                }
                actors.push_back(entry);
            }
            result["indoor"]["actors"] = actors;
        }
    }
    std::cout << result << '\n';
    return 0;
}
