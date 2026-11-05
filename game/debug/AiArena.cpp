#include "game/debug/AiArena.h"

#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/gameplay/GameplayMonsterSpawn.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <fstream>
#include <initializer_list>
#include <sstream>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;

bool checkKeys(const YAML::Node &node, std::initializer_list<std::string_view> keys, const std::string &context,
    std::string &error)
{
    for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
    {
        const std::string key = iterator->first.as<std::string>("");

        if (std::find(keys.begin(), keys.end(), key) == keys.end())
        {
            std::string known;

            for (std::string_view name : keys)
            {
                known += (known.empty() ? "" : ", ") + std::string(name);
            }

            error = context + ": unknown key '" + key + "' (known: " + known + ")";
            return false;
        }
    }

    return true;
}

bool readPosition(const YAML::Node &node, const std::string &context, float &x, float &y, float &z,
    std::string &error, const char *pKey = "position")
{
    const YAML::Node position = node[pKey];

    if (!position || !position.IsSequence() || position.size() != 3)
    {
        error = context + ": " + pKey + " must be [x, y, z]";
        return false;
    }

    x = position[0].as<float>();
    y = position[1].as<float>();
    z = position[2].as<float>();
    return true;
}

// yaw (radians) or yaw_degrees; the same for pitch.
std::optional<float> readAngle(const YAML::Node &node, const char *pRadiansKey, const char *pDegreesKey)
{
    if (node[pRadiansKey])
    {
        return node[pRadiansKey].as<float>();
    }

    if (node[pDegreesKey])
    {
        return node[pDegreesKey].as<float>() * Pi / 180.0f;
    }

    return std::nullopt;
}

bool parseMonster(const YAML::Node &node, size_t index, AiArenaMonster &monster, std::string &error)
{
    const std::string context = "monsters[" + std::to_string(index) + "]";

    if (!node.IsMap())
    {
        error = context + " must be a map";
        return false;
    }

    if (!checkKeys(node, {"monster_id", "position", "yaw", "yaw_degrees", "hostile", "group", "party_ally", "mm9_ai",
            "overrides", "note"}, context, error))
    {
        return false;
    }

    if (!node["monster_id"] || !readPosition(node, context, monster.x, monster.y, monster.z, error))
    {
        error = error.empty() ? context + ": monster_id is required" : error;
        return false;
    }

    monster.monsterId = node["monster_id"].as<int16_t>();
    monster.yawRadians = readAngle(node, "yaw", "yaw_degrees");
    monster.hostile = node["hostile"].as<bool>(true);
    monster.group = node["group"].as<uint32_t>(0);
    monster.partyAlly = node["party_ally"].as<bool>(false);

    if (const YAML::Node mm9Ai = node["mm9_ai"])
    {
        Mm9AiPlacementRecord record = {};
        std::string placementError;

        if (!parseMm9AiPlacementNode(mm9Ai, record, placementError))
        {
            error = context + ": mm9_ai: " + placementError;
            return false;
        }

        monster.mm9Ai = std::move(record);
    }

    if (const YAML::Node overrides = node["overrides"])
    {
        if (!overrides.IsMap())
        {
            error = context + ": overrides must be a map";
            return false;
        }

        for (YAML::const_iterator iterator = overrides.begin(); iterator != overrides.end(); ++iterator)
        {
            std::string fieldError;

            if (!monster.overrides.setField(iterator->first.as<std::string>(), iterator->second.as<std::string>(),
                    fieldError))
            {
                error = context + ": " + fieldError;
                return false;
            }
        }
    }

    return true;
}

bool parseArena(const YAML::Node &root, AiArena &arena, std::string &error)
{
    if (!root.IsMap())
    {
        error = "the arena must be a map";
        return false;
    }

    if (!checkKeys(root, {"schema", "name", "note", "world", "map", "asset_root", "party", "clear_actors", "trace",
            "trace_animation", "seed", "monsters", "events"}, "arena", error))
    {
        return false;
    }

    if (!root["map"])
    {
        error = "arena: map is required";
        return false;
    }

    arena.name = root["name"].as<std::string>(arena.sourcePath.stem().string());
    arena.world = root["world"].as<std::string>("");
    arena.map = root["map"].as<std::string>();
    arena.assetRoot = root["asset_root"].as<std::string>("");
    arena.clearActors = root["clear_actors"].as<bool>(true);
    arena.trace = root["trace"].as<bool>(true);
    arena.traceAnimation = root["trace_animation"].as<bool>(false);
    arena.seed = root["seed"].as<uint64_t>(1);

    const YAML::Node party = root["party"];

    if (!party || !party.IsMap())
    {
        error = "arena: party with a position is required";
        return false;
    }

    if (!checkKeys(party, {"position", "yaw", "yaw_degrees", "pitch", "pitch_degrees", "invulnerable", "members"},
            "party", error)
        || !readPosition(party, "party", arena.party.x, arena.party.y, arena.party.z, error))
    {
        return false;
    }

    arena.party.yawRadians = readAngle(party, "yaw", "yaw_degrees").value_or(0.0f);
    arena.party.pitchRadians = readAngle(party, "pitch", "pitch_degrees").value_or(0.0f);
    arena.party.invulnerable = party["invulnerable"].as<bool>(true);

    if (party["members"])
    {
        const size_t members = party["members"].as<size_t>();

        if (members < 1)
        {
            error = "party: members must be at least 1";
            return false;
        }

        arena.party.members = members;
    }

    const YAML::Node monsters = root["monsters"];

    if (monsters && !monsters.IsSequence())
    {
        error = "arena: monsters must be a list";
        return false;
    }

    for (size_t index = 0; monsters && index < monsters.size(); ++index)
    {
        AiArenaMonster monster = {};

        if (!parseMonster(monsters[index], index, monster, error))
        {
            return false;
        }

        arena.monsters.push_back(std::move(monster));
    }

    const YAML::Node events = root["events"];

    if (events && !events.IsSequence())
    {
        error = "arena: events must be a list";
        return false;
    }

    for (size_t index = 0; events && index < events.size(); ++index)
    {
        const YAML::Node node = events[index];
        const std::string context = "events[" + std::to_string(index) + "]";
        AiArenaEvent event = {};

        if (!node.IsMap()
            || !checkKeys(node, {"at", "wake", "relation", "trigger", "door", "party_walk", "note"}, context, error))
        {
            error = error.empty() ? context + " must be a map" : error;
            return false;
        }

        event.atSeconds = node["at"].as<float>(0.0f);

        const int kinds = (node["wake"] ? 1 : 0) + (node["relation"] ? 1 : 0) + (node["trigger"] ? 1 : 0)
            + (node["door"] ? 1 : 0) + (node["party_walk"] ? 1 : 0);

        if (kinds == 1 && node["trigger"] && node["trigger"].IsSequence() && node["trigger"].size() == 2)
        {
            // trigger: [arena monster, message]: MM9's Trigger <object>, <message> to its behaviour script.
            event.kind = ActorAiArenaAction::Kind::Trigger;
            event.monster = node["trigger"][0].as<size_t>();
            event.message = node["trigger"][1].as<std::string>();

            if (event.monster >= arena.monsters.size())
            {
                error = context + ": trigger names no arena monster";
                return false;
            }
        }
        else if (kinds == 1 && node["door"])
        {
            // door: <door id>: the map door opens, as a click on it.
            event.kind = ActorAiArenaAction::Kind::Door;
            event.doorId = node["door"].as<uint32_t>();
        }
        else if (kinds == 1 && node["party_walk"] && node["party_walk"].IsMap())
        {
            // party_walk: {to: [x, y, z], seconds}: the party walks in a straight line to the point.
            const YAML::Node walk = node["party_walk"];
            event.kind = ActorAiArenaAction::Kind::PartyWalk;
            event.walkSeconds = walk["seconds"].as<float>(0.0f);

            if (!checkKeys(walk, {"to", "seconds"}, context + ".party_walk", error)
                || !readPosition(walk, context + ".party_walk", event.walkTo.x, event.walkTo.y, event.walkTo.z,
                    error, "to"))
            {
                return false;
            }
        }
        else if (kinds == 1 && node["wake"])
        {
            event.kind = ActorAiArenaAction::Kind::Wake;
            event.monster = node["wake"].as<size_t>();

            if (event.monster >= arena.monsters.size())
            {
                error = context + ": wake names no arena monster";
                return false;
            }
        }
        else if (kinds == 1 && node["relation"] && node["relation"].IsSequence() && node["relation"].size() == 3)
        {
            event.kind = ActorAiArenaAction::Kind::Relation;
            event.fromMonsterId = node["relation"][0].as<int16_t>();
            event.toMonsterId = node["relation"][1].as<int16_t>();
            event.relation = node["relation"][2].as<int>();
        }
        else
        {
            error = context + ": give one of wake: <arena monster>, relation: [from id, to id, level], trigger: "
                "[arena monster, message], door: <door id> or party_walk: {to: [x, y, z], seconds}";
            return false;
        }

        arena.events.push_back(event);
    }

    return true;
}
}

std::optional<AiArena> parseAiArenaText(const std::string &text, const std::filesystem::path &sourcePath,
    std::string &error)
{
    AiArena arena = {};
    arena.sourcePath = sourcePath;

    try
    {
        if (!parseArena(YAML::Load(text), arena, error))
        {
            error = sourcePath.string() + ": " + error;
            return std::nullopt;
        }
    }
    catch (const YAML::Exception &exception)
    {
        error = sourcePath.string() + ": " + exception.what();
        return std::nullopt;
    }

    return arena;
}

std::optional<AiArena> loadAiArena(const std::filesystem::path &path, std::string &error)
{
    std::ifstream stream(path);

    if (!stream)
    {
        error = "cannot read the AI arena " + path.string();
        return std::nullopt;
    }

    std::ostringstream text;
    text << stream.rdbuf();
    return parseAiArenaText(text.str(), path, error);
}

bool applyAiArenaActors(
    const AiArena &arena,
    IGameplayWorldRuntime &world,
    ActorAiTrace &trace,
    std::vector<size_t> &spawnedActorIndices,
    std::string &error)
{
    spawnedActorIndices.clear();

    if (arena.clearActors)
    {
        EventRuntimeState *pEventState = world.eventRuntimeState();

        if (pEventState == nullptr)
        {
            error = "the map has no event state to hide its actors with";
            return false;
        }

        // As SetMonsterBit's invisible bit: the actors leave the map without dying (no loot, experience or events).
        const uint32_t invisible = uint32_t(EvtActorAttribute::Invisible);

        for (size_t actorIndex = 0; actorIndex < world.mapActorCount(); ++actorIndex)
        {
            pEventState->actorSetMasks[uint32_t(actorIndex)] |= invisible;
            pEventState->actorClearMasks[uint32_t(actorIndex)] &= ~invisible;
        }

        world.applyEventRuntimeState();
    }

    trace.reset();
    trace.setRecording(arena.trace);
    trace.setAnimationRecording(arena.traceAnimation);

    for (size_t index = 0; index < arena.monsters.size(); ++index)
    {
        const AiArenaMonster &monster = arena.monsters[index];

        // A party ally is a friendly summon (it stands 96 units east of its position, as a summon spell places it).
        if (monster.partyAlly)
        {
            const size_t actorCount = world.mapActorCount();

            if (!world.summonFriendlyMonsterById(monster.monsterId, 1, 3600.0f, monster.x, monster.y, monster.z, -1)
                || world.mapActorCount() != actorCount + 1)
            {
                error = "could not summon arena party ally " + std::to_string(index) + " (monster "
                    + std::to_string(monster.monsterId) + ")";
                return false;
            }

            spawnedActorIndices.push_back(actorCount);
            trace.traceActor(actorCount);
            trace.setOverride(actorCount, monster.overrides);
            continue;
        }

        GameplayMonsterSpawnRequest request;
        request.monsterId = monster.monsterId;
        request.count = 1;
        request.x = monster.x;
        request.y = monster.y;
        request.z = monster.z;
        request.radius = 0.0f;
        request.group = monster.group;
        request.hostile = monster.hostile;
        request.dropsLoot = false;
        request.seed = arena.seed + index;
        request.yawRadians = monster.yawRadians;
        request.mm9Ai = monster.mm9Ai;
        const std::vector<size_t> spawned = world.spawnMonsters(request);

        if (spawned.size() != 1)
        {
            error = "could not spawn arena monster " + std::to_string(index) + " (monster "
                + std::to_string(monster.monsterId) + ")";
            return false;
        }

        spawnedActorIndices.push_back(spawned.front());
        trace.traceActor(spawned.front());
        trace.setOverride(spawned.front(), monster.overrides);
    }

    for (const AiArenaEvent &event : arena.events)
    {
        ActorAiArenaAction action = {};
        action.atSeconds = event.atSeconds;
        action.kind = event.kind;
        action.actorIndex = event.kind != ActorAiArenaAction::Kind::Relation ? spawnedActorIndices[event.monster] : 0;
        action.fromMonsterId = event.fromMonsterId;
        action.toMonsterId = event.toMonsterId;
        action.relation = event.relation;
        action.message = event.message;
        action.doorId = event.doorId;
        action.walkTo = event.walkTo;
        action.walkSeconds = event.walkSeconds;
        trace.scheduleAction(action);
    }

    world.bindActorAiTrace(&trace);
    return true;
}
}
