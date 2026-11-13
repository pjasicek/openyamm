#include "game/items/ItemGenerator.h"
#include "game/scenario/ScenarioRunner.h"

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/debug/AiArena.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/MercenaryRecruitmentRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/maps/MapIdentity.h"
#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/gameplay/CombatLog.h"
#include "game/rules/maw/MawRules.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/scenario/ScenarioRuntimeDriver.h"
#include "game/tables/ItemTable.h"

#include <SDL3/SDL.h>

extern "C"
{
#include <lauxlib.h>
#include <lua.h>
#include <lualib.h>
}

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <optional>
#include <random>
#include <sstream>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
struct ScenarioExecutionContext
{
    Engine::AssetFileSystem assetFileSystem;
    GameDataLoader gameDataLoader;
    EventRuntime eventRuntime;
    EventRuntimeState eventRuntimeState;
    Party party;
    std::unique_ptr<ScenarioRuntimeDriver> runtimeDriver;
    std::string currentMapFileName;
    std::filesystem::path basePath;
    std::filesystem::path saveGameRootPath;
    Engine::ApplicationConfig config;
    ScenarioMode mode = ScenarioMode::Hybrid;
    bool gameDataLoaded = false;
    bool eventRuntimeStateLoaded = false;
    bool traceEnabled = true;
    bool colorsEnabled = true;
    size_t totalStepCount = 0;
    float gameMinutes = 9.0f * 60.0f;
    struct Checkpoint
    {
        Party party;
        EventRuntimeState eventRuntimeState;
        std::string currentMapFileName;
        float gameMinutes = 0.0f;
        bool eventRuntimeStateLoaded = false;
    };

    std::unordered_map<std::string, Checkpoint> checkpoints;
    // play_lua's remember(key, value): kept for the later play_lua steps of the run.
    std::unordered_map<std::string, std::string> playMemory;
    std::unordered_map<std::string, std::filesystem::path> saveGamePaths;
    // party_attack results by their record name.
    std::unordered_map<std::string, ScenarioPartyAttackResult> attackRecords;
};

struct ScenarioInventoryGrid
{
    uint8_t x = 0;
    uint8_t y = 0;
};

bool ensureRuntimeDriver(ScenarioExecutionContext &context, std::vector<std::string> &failures);
bool assertDialogueCanceled(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures);
std::optional<EquipmentSlot> parseScenarioEquipmentSlot(const std::string &value);

std::string lowerAscii(const std::string &value)
{
    std::string lowered;
    lowered.reserve(value.size());

    for (char character : value)
    {
        lowered.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return lowered;
}

bool envFlagEnabled(const char *pName)
{
    const char *pValue = std::getenv(pName);

    if (pValue == nullptr)
    {
        return false;
    }

    const std::string value = lowerAscii(pValue);
    return value.empty() || value == "1" || value == "true" || value == "yes" || value == "on";
}

enum class ScenarioLogColor
{
    Default,
    Blue,
    Cyan,
    Green,
    Red,
    Yellow,
};

const char *scenarioColorCode(ScenarioLogColor color)
{
    switch (color)
    {
    case ScenarioLogColor::Blue:
        return "\033[34m";
    case ScenarioLogColor::Cyan:
        return "\033[36m";
    case ScenarioLogColor::Green:
        return "\033[32m";
    case ScenarioLogColor::Red:
        return "\033[31m";
    case ScenarioLogColor::Yellow:
        return "\033[33m";
    case ScenarioLogColor::Default:
        break;
    }

    return "";
}

std::string scenarioColored(
    const ScenarioExecutionContext &context,
    const std::string &text,
    ScenarioLogColor color)
{
    if (!context.colorsEnabled || color == ScenarioLogColor::Default)
    {
        return text;
    }

    return std::string(scenarioColorCode(color)) + text + "\033[0m";
}

void scenarioLog(
    const ScenarioExecutionContext &context,
    ScenarioLogColor color,
    const std::string &message)
{
    if (!context.traceEnabled)
    {
        return;
    }

    std::cout << scenarioColored(context, message, color) << '\n';
    std::cout.flush();
}

std::string scalarNodeText(const YAML::Node &node)
{
    if (!node || !node.IsScalar())
    {
        return "<unset>";
    }

    return node.as<std::string>();
}

std::string boolText(bool value)
{
    return value ? "true" : "false";
}

std::string replacedText(
    std::string value,
    const std::string &from,
    const std::string &to)
{
    if (from.empty())
    {
        return value;
    }

    size_t position = 0;

    while ((position = value.find(from, position)) != std::string::npos)
    {
        value.replace(position, from.size(), to);
        position += to.size();
    }

    return value;
}

std::string normalizedScenarioDialogLabel(std::string value)
{
    value = replacedText(value, "\xE2\x80\xA6", "<ellipsis>");
    value = replacedText(value, "\xEF\xBF\xBD", "<ellipsis>");
    value = replacedText(value, std::string(1, static_cast<char>(0x85)), "<ellipsis>");
    return value;
}

bool parseUnsignedText(const std::string &text, uint32_t &value)
{
    if (text.empty())
    {
        return false;
    }

    for (char character : text)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return false;
        }
    }

    try
    {
        value = static_cast<uint32_t>(std::stoul(text));
    }
    catch (const std::exception &)
    {
        return false;
    }

    return true;
}

std::optional<ScenarioInventoryGrid> parseInventoryGridText(const std::string &text)
{
    const size_t open = text.find('(');
    const size_t comma = text.find(',', open == std::string::npos ? 0 : open + 1);
    const size_t close = text.find(')', comma == std::string::npos ? 0 : comma + 1);

    if (open == std::string::npos || comma == std::string::npos || close == std::string::npos)
    {
        return std::nullopt;
    }

    uint32_t x = 0;
    uint32_t y = 0;

    if (!parseUnsignedText(text.substr(open + 1, comma - open - 1), x)
        || !parseUnsignedText(text.substr(comma + 1, close - comma - 1), y)
        || x > std::numeric_limits<uint8_t>::max()
        || y > std::numeric_limits<uint8_t>::max())
    {
        return std::nullopt;
    }

    ScenarioInventoryGrid grid = {};
    grid.x = static_cast<uint8_t>(x);
    grid.y = static_cast<uint8_t>(y);
    return grid;
}

std::optional<bx::Vec3> parseFloatTripletText(const std::string &text)
{
    const size_t open = text.find('(');
    const size_t firstComma = text.find(',', open == std::string::npos ? 0 : open + 1);
    const size_t secondComma = text.find(',', firstComma == std::string::npos ? 0 : firstComma + 1);
    const size_t close = text.find(')', secondComma == std::string::npos ? 0 : secondComma + 1);

    if (open == std::string::npos
        || firstComma == std::string::npos
        || secondComma == std::string::npos
        || close == std::string::npos)
    {
        return std::nullopt;
    }

    try
    {
        return bx::Vec3{
            std::stof(text.substr(open + 1, firstComma - open - 1)),
            std::stof(text.substr(firstComma + 1, secondComma - firstComma - 1)),
            std::stof(text.substr(secondComma + 1, close - secondComma - 1)),
        };
    }
    catch (const std::exception &)
    {
        return std::nullopt;
    }
}

std::string compactSemanticLabel(const std::string &text)
{
    std::string result;
    result.reserve(text.size());
    bool lastWasSpace = false;

    for (char character : text)
    {
        if (std::isspace(static_cast<unsigned char>(character)))
        {
            if (!result.empty() && !lastWasSpace)
            {
                result.push_back(' ');
                lastWasSpace = true;
            }

            continue;
        }

        result.push_back(character == '"' ? '\'' : character);
        lastWasSpace = false;
    }

    if (!result.empty() && result.back() == ' ')
    {
        result.pop_back();
    }

    constexpr size_t MaxLabelLength = 96;
    if (result.size() > MaxLabelLength)
    {
        result.resize(MaxLabelLength - 3);
        result += "...";
    }

    return result;
}

std::string semanticSuffix(const std::string &label)
{
    const std::string compact = compactSemanticLabel(label);
    return compact.empty() ? std::string() : " \"" + compact + '"';
}

std::string mapSemanticSuffix(const ScenarioExecutionContext &context, const std::string &mapFileName)
{
    const MapStatsEntry *pMap = context.gameDataLoader.getMapStats().findByFileName(mapFileName);
    return pMap != nullptr ? semanticSuffix(pMap->name) : std::string();
}

std::string qbitSemanticSuffix(const ScenarioExecutionContext &context, uint32_t qbitId)
{
    for (const JournalQuestEntry &entry : context.gameDataLoader.getJournalQuestTable().entries())
    {
        if (entry.qbitId != qbitId)
        {
            continue;
        }

        if (!entry.text.empty())
        {
            return semanticSuffix(entry.text);
        }

        if (!entry.notes.empty())
        {
            return semanticSuffix(entry.notes);
        }

        return semanticSuffix(entry.owner);
    }

    return std::string();
}

std::string itemSemanticSuffix(const ScenarioExecutionContext &context, uint32_t itemId)
{
    const ItemDefinition *pItem = context.gameDataLoader.getItemTable().get(itemId);

    if (pItem == nullptr)
    {
        return std::string();
    }

    return semanticSuffix(!pItem->name.empty() ? pItem->name : pItem->unidentifiedName);
}

std::string houseSemanticSuffix(const ScenarioExecutionContext &context, uint32_t houseId)
{
    const HouseEntry *pHouse = context.gameDataLoader.getHouseTable().get(houseId);

    if (pHouse == nullptr)
    {
        return std::string();
    }

    if (!pHouse->name.empty())
    {
        return semanticSuffix(pHouse->name);
    }

    if (!pHouse->buildingName.empty())
    {
        return semanticSuffix(pHouse->buildingName);
    }

    return semanticSuffix(pHouse->type);
}

std::string npcSemanticSuffix(const ScenarioExecutionContext &context, uint32_t npcId)
{
    const NpcEntry *pNpc = context.gameDataLoader.getNpcDialogTable().getNpc(npcId);
    return pNpc != nullptr ? semanticSuffix(pNpc->name) : std::string();
}

std::string professionSemanticSuffix(const ScenarioExecutionContext &context, uint32_t professionId)
{
    const MergedNpcProfessionEntry *pProfession =
        context.gameDataLoader.getMergedNpcProfessionTable().get(professionId);
    return pProfession != nullptr ? semanticSuffix(pProfession->profession) : std::string();
}

std::string monsterSemanticSuffix(const ScenarioExecutionContext &context, uint32_t monsterId)
{
    const MonsterTable::MonsterStatsEntry *pMonster =
        context.gameDataLoader.getMonsterTable().findStatsById(static_cast<int16_t>(monsterId));
    return pMonster != nullptr ? semanticSuffix(pMonster->name) : std::string();
}

std::string topicSemanticSuffix(const ScenarioExecutionContext &context, uint32_t topicId)
{
    const std::optional<NpcDialogTable::ResolvedTopic> topic =
        context.gameDataLoader.getNpcDialogTable().getTopicById(topicId);
    return topic.has_value() ? semanticSuffix(topic->topic) : std::string();
}

std::string semanticValue(
    const ScenarioExecutionContext &context,
    const std::string &fieldName,
    const std::string &value)
{
    uint32_t unsignedValue = 0;

    if (fieldName == "map"
        || fieldName == "map_loaded"
        || fieldName == "destination_map"
        || fieldName == "previous_map")
    {
        return value + mapSemanticSuffix(context, value);
    }

    if ((fieldName == "item_id" || fieldName == "expected_item_id" || fieldName == "held_item_id")
        && parseUnsignedText(value, unsignedValue))
    {
        return value + itemSemanticSuffix(context, unsignedValue);
    }

    if ((fieldName == "npc_id" || fieldName == "active_source_id") && parseUnsignedText(value, unsignedValue))
    {
        return value + npcSemanticSuffix(context, unsignedValue);
    }

    if ((fieldName == "house_id" || fieldName == "host_house_id") && parseUnsignedText(value, unsignedValue))
    {
        return value + houseSemanticSuffix(context, unsignedValue);
    }

    if (fieldName == "topic_id" && parseUnsignedText(value, unsignedValue))
    {
        return value + topicSemanticSuffix(context, unsignedValue);
    }

    if (fieldName == "profession_id" && parseUnsignedText(value, unsignedValue))
    {
        return value + professionSemanticSuffix(context, unsignedValue);
    }

    return value;
}

std::string semanticFieldName(
    const ScenarioExecutionContext &context,
    const std::string &fieldName)
{
    const bool qbitField =
        fieldName.rfind("qbit_", 0) == 0
        || fieldName.rfind("quest_bit", 0) == 0;
    const size_t qbitOpen = qbitField ? fieldName.find('[') : std::string::npos;
    const size_t qbitClose = qbitField ? fieldName.find(']') : std::string::npos;

    if (qbitField && qbitOpen != std::string::npos && qbitClose != std::string::npos && qbitClose > qbitOpen + 1)
    {
        uint32_t qbitId = 0;
        if (parseUnsignedText(fieldName.substr(qbitOpen + 1, qbitClose - qbitOpen - 1), qbitId))
        {
            return fieldName + qbitSemanticSuffix(context, qbitId);
        }
    }

    return fieldName;
}

std::string stepLocation(const ScenarioStep &step)
{
    std::ostringstream stream;
    stream << step.sourcePath.string() << ':' << step.sourceLine << " step " << step.stepIndex
           << " (" << step.kindName << ')';

    if (step.traceSourceLine > 0)
    {
        stream << " trace_line=" << step.traceSourceLine;
    }

    return stream.str();
}

void appendPayloadScalarSummary(
    const ScenarioExecutionContext &context,
    std::ostringstream &stream,
    const YAML::Node &payload,
    const char *pFieldName)
{
    if (payload[pFieldName] && payload[pFieldName].IsScalar())
    {
        const std::string value = payload[pFieldName].as<std::string>();
        stream << ' ' << pFieldName << '=' << semanticValue(context, pFieldName, value);
    }
}

void appendSelectTopicSummary(
    const ScenarioExecutionContext &context,
    std::ostringstream &stream,
    const YAML::Node &payload)
{
    if (!payload["kind"] || !payload["kind"].IsScalar())
    {
        return;
    }

    const std::string kind = payload["kind"].as<std::string>();
    uint32_t id = 0;

    if (payload["source_id"] && payload["source_id"].IsScalar()
        && parseUnsignedText(payload["source_id"].as<std::string>(), id))
    {
        stream << " source_id=" << id;

        if (kind == "house_service" || kind == "house_resident")
        {
            stream << houseSemanticSuffix(context, id);
        }
        else
        {
            stream << npcSemanticSuffix(context, id);
        }
    }

    if (payload["action_id"] && payload["action_id"].IsScalar()
        && parseUnsignedText(payload["action_id"].as<std::string>(), id))
    {
        stream << " action_id=" << id;

        if (kind == "npc_topic")
        {
            stream << topicSemanticSuffix(context, id);
        }
        else if (kind == "house_resident")
        {
            stream << npcSemanticSuffix(context, id);
        }
    }

    if (payload["label"] && payload["label"].IsScalar())
    {
        stream << " label=" << semanticSuffix(payload["label"].as<std::string>());
    }
}

void appendTransitionSummary(
    const ScenarioExecutionContext &context,
    std::ostringstream &stream,
    const YAML::Node &transitionNode,
    const char *pName)
{
    if (!transitionNode || !transitionNode.IsMap())
    {
        return;
    }

    stream << ' ' << pName << '=';

    if (transitionNode["source_kind"] && transitionNode["source_kind"].IsScalar())
    {
        stream << transitionNode["source_kind"].as<std::string>();
    }

    if (transitionNode["source_id"] && transitionNode["source_id"].IsScalar())
    {
        const std::string sourceText = transitionNode["source_id"].as<std::string>();
        stream << ':' << sourceText;

        uint32_t sourceId = 0;
        if (parseUnsignedText(sourceText, sourceId))
        {
            stream << houseSemanticSuffix(context, sourceId);
        }
    }

    if (transitionNode["destination_map"] && transitionNode["destination_map"].IsScalar())
    {
        const std::string mapFileName = transitionNode["destination_map"].as<std::string>();
        stream << " -> " << mapFileName << mapSemanticSuffix(context, mapFileName);
    }

    if (transitionNode["destination_name"] && transitionNode["destination_name"].IsScalar())
    {
        stream << " destination=" << semanticSuffix(transitionNode["destination_name"].as<std::string>());
    }
}

void appendFollowerSummary(
    const ScenarioExecutionContext &context,
    std::ostringstream &stream,
    const YAML::Node &payload,
    const char *pFieldName)
{
    const YAML::Node followersNode = payload[pFieldName];

    if (!followersNode || !followersNode.IsSequence())
    {
        return;
    }

    stream << ' ' << pFieldName << '=';
    bool first = true;

    for (const YAML::Node &entryNode : followersNode)
    {
        if (!entryNode.IsMap() || !entryNode["npc_id"] || !entryNode["npc_id"].IsScalar())
        {
            continue;
        }

        uint32_t npcId = 0;
        if (!parseUnsignedText(entryNode["npc_id"].as<std::string>(), npcId))
        {
            continue;
        }

        if (!first)
        {
            stream << ',';
        }

        first = false;
        stream << npcId << npcSemanticSuffix(context, npcId);

        if (entryNode["profession_id"] && entryNode["profession_id"].IsScalar())
        {
            uint32_t professionId = 0;
            if (parseUnsignedText(entryNode["profession_id"].as<std::string>(), professionId))
            {
                stream << " profession=" << professionId << professionSemanticSuffix(context, professionId);
            }
        }
    }
}

void appendNestedItemSummary(
    const ScenarioExecutionContext &context,
    std::ostringstream &stream,
    const YAML::Node &payload,
    const char *pFieldName)
{
    const YAML::Node itemNode = payload[pFieldName];

    if (!itemNode || !itemNode.IsMap() || !itemNode["item_id"] || !itemNode["item_id"].IsScalar())
    {
        return;
    }

    uint32_t itemId = 0;
    if (!parseUnsignedText(itemNode["item_id"].as<std::string>(), itemId))
    {
        return;
    }

    stream << ' ' << pFieldName << '=' << itemId << itemSemanticSuffix(context, itemId);
}

void appendInventoryItemSummary(
    const ScenarioExecutionContext &context,
    std::ostringstream &stream,
    const YAML::Node &payload,
    const char *pFieldName)
{
    const YAML::Node inventoryNode = payload[pFieldName];

    if (!inventoryNode || !inventoryNode.IsSequence())
    {
        return;
    }

    stream << ' ' << pFieldName << '=';
    bool first = true;

    for (const YAML::Node &entryNode : inventoryNode)
    {
        if (!entryNode.IsMap() || !entryNode["item_id"] || !entryNode["item_id"].IsScalar())
        {
            continue;
        }

        uint32_t itemId = 0;
        if (!parseUnsignedText(entryNode["item_id"].as<std::string>(), itemId))
        {
            continue;
        }

        if (!first)
        {
            stream << ',';
        }

        first = false;
        stream << itemId << itemSemanticSuffix(context, itemId);
    }
}

void appendActorSummary(
    const ScenarioExecutionContext &context,
    std::ostringstream &stream,
    const YAML::Node &payload)
{
    const YAML::Node actorNode = payload["actor_visible"];

    if (!actorNode || !actorNode.IsMap())
    {
        return;
    }

    stream << " actor_visible=";

    if (actorNode["actor_index"] && actorNode["actor_index"].IsScalar())
    {
        stream << "index:" << actorNode["actor_index"].as<std::string>();
    }

    if (actorNode["name"] && actorNode["name"].IsScalar())
    {
        stream << semanticSuffix(actorNode["name"].as<std::string>());
    }
    else if (actorNode["monster_id"] && actorNode["monster_id"].IsScalar())
    {
        uint32_t monsterId = 0;
        if (parseUnsignedText(actorNode["monster_id"].as<std::string>(), monsterId))
        {
            stream << monsterSemanticSuffix(context, monsterId);
        }
    }

    if (actorNode["monster_id"] && actorNode["monster_id"].IsScalar())
    {
        stream << " monster_id=" << actorNode["monster_id"].as<std::string>();
    }
}

std::string stepSummary(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step)
{
    std::ostringstream stream;
    stream << "step " << step.stepIndex << '/' << context.totalStepCount << ' ' << step.kindName;

    if (step.traceSourceLine > 0)
    {
        stream << " trace_line=" << step.traceSourceLine;
    }

    stream << " yaml_line=" << step.sourceLine;

    if (step.payload && step.payload.IsMap())
    {
        appendPayloadScalarSummary(context, stream, step.payload, "map");
        appendPayloadScalarSummary(context, stream, step.payload, "kind");
        appendPayloadScalarSummary(context, stream, step.payload, "target_index");
        appendPayloadScalarSummary(context, stream, step.payload, "face_index");
        appendPayloadScalarSummary(context, stream, step.payload, "triggered_event");
        appendPayloadScalarSummary(context, stream, step.payload, "event_id");
        appendPayloadScalarSummary(context, stream, step.payload, "actor_index");
        appendPayloadScalarSummary(context, stream, step.payload, "item_id");
        appendPayloadScalarSummary(context, stream, step.payload, "name");
        appendPayloadScalarSummary(context, stream, step.payload, "text");

        if (step.kindName == "select_topic")
        {
            appendSelectTopicSummary(context, stream, step.payload);
        }

        appendTransitionSummary(context, stream, step.payload["map_transition_requested"], "requested");
        appendTransitionSummary(context, stream, step.payload["map_transition_confirmed"], "confirmed");
        appendTransitionSummary(context, stream, step.payload["map_transition_canceled"], "canceled");
        appendFollowerSummary(context, stream, step.payload, "follower_hired");
        appendFollowerSummary(context, stream, step.payload, "follower_left");
        appendNestedItemSummary(context, stream, step.payload, "item_received");
        appendNestedItemSummary(context, stream, step.payload, "item_visible");
        appendNestedItemSummary(context, stream, step.payload, "world_item_spawned");
        appendNestedItemSummary(context, stream, step.payload, "chest_contains_quest_item");
        appendNestedItemSummary(context, stream, step.payload, "corpse_contains_quest_item");
        appendInventoryItemSummary(context, stream, step.payload, "inventory");
        appendInventoryItemSummary(context, stream, step.payload, "inventory_any_member");
        appendInventoryItemSummary(context, stream, step.payload, "equipped_item");
        appendActorSummary(context, stream, step.payload);

        const YAML::Node poseNode = step.payload["pose"];
        if (poseNode && poseNode.IsMap())
        {
            stream << " pose=(" << scalarNodeText(poseNode["x"]) << ','
                   << scalarNodeText(poseNode["y"]) << ','
                   << scalarNodeText(poseNode["z"]) << ')';

            if (poseNode["map"] && poseNode["map"].IsScalar())
            {
                stream << " pose_map=" << poseNode["map"].as<std::string>();
            }
        }
    }

    return stream.str();
}

void scenarioLogAssert(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const std::string &fieldName,
    const std::string &expected,
    const std::string &actual,
    bool success)
{
    std::ostringstream stream;
    stream << (success ? "ASSERT pass " : "ASSERT fail ")
           << "step=" << step.stepIndex;

    if (step.traceSourceLine > 0)
    {
        stream << " trace_line=" << step.traceSourceLine;
    }

    stream << ' ' << semanticFieldName(context, fieldName)
           << " expected=" << semanticValue(context, fieldName, expected)
           << " actual=" << semanticValue(context, fieldName, actual);
    scenarioLog(context, success ? ScenarioLogColor::Green : ScenarioLogColor::Red, stream.str());
}

bool recordScenarioAssertion(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const std::string &fieldName,
    const std::string &expected,
    const std::string &actual,
    std::vector<std::string> &failures)
{
    const bool success = expected == actual;
    scenarioLogAssert(context, step, fieldName, expected, actual, success);

    if (!success)
    {
        failures.push_back(stepLocation(step) + ": expected " + fieldName + "=" + expected
            + " but current " + fieldName + "=" + actual);
    }

    return success;
}

bool assertDialogScalar(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const YAML::Node &dialogNode,
    const std::string &fieldName,
    const std::string &actual,
    std::vector<std::string> &failures)
{
    const YAML::Node expectedNode = dialogNode[fieldName];

    if (!expectedNode || !expectedNode.IsScalar())
    {
        return true;
    }

    return recordScenarioAssertion(
        context,
        step,
        "dialog." + fieldName,
        expectedNode.as<std::string>(),
        actual,
        failures);
}

bool assertDialogActionScalar(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const YAML::Node &actionNode,
    size_t actionIndex,
    const std::string &fieldName,
    const std::string &actual,
    std::vector<std::string> &failures)
{
    const YAML::Node expectedNode = actionNode[fieldName];

    if (!expectedNode || !expectedNode.IsScalar())
    {
        return true;
    }

    if (fieldName == "label"
        && actionNode["kind"]
        && actionNode["kind"].IsScalar()
        && actionNode["kind"].as<std::string>() == "house_resident"
        && actionNode["id"]
        && actionNode["id"].IsScalar()
        && isGeneratedMercenaryNpcId(actionNode["id"].as<uint32_t>()))
    {
        return true;
    }

    const std::string expected = expectedNode.as<std::string>();

    if (fieldName == "label")
    {
        const std::string normalizedExpected = normalizedScenarioDialogLabel(expected);
        const std::string normalizedActual = normalizedScenarioDialogLabel(actual);

        if (expected != actual && normalizedExpected == normalizedActual)
        {
            std::ostringstream field;
            field << "dialog.actions[" << actionIndex << "]." << fieldName;
            scenarioLogAssert(context, step, field.str(), expected, actual + " (encoding-normalized)", true);
            return true;
        }
    }

    std::ostringstream field;
    field << "dialog.actions[" << actionIndex << "]." << fieldName;
    return recordScenarioAssertion(
        context,
        step,
        field.str(),
        expected,
        actual,
        failures);
}

bool assertDialogState(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const YAML::Node &dialogNode,
    const std::string &phase,
    std::vector<std::string> &failures)
{
    if (!dialogNode)
    {
        return true;
    }

    if (!dialogNode.IsMap())
    {
        failures.push_back(stepLocation(step) + ": " + phase + " dialog expectation must be a mapping");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    const ScenarioDialogSnapshot actual = context.runtimeDriver->activeDialogSnapshot();
    bool success = true;

    success = assertDialogScalar(context, step, dialogNode, "active", boolText(actual.active), failures) && success;
    success = assertDialogScalar(
        context,
        step,
        dialogNode,
        "house_dialog",
        boolText(actual.houseDialog),
        failures) && success;
    success = assertDialogScalar(
        context,
        step,
        dialogNode,
        "source_id",
        std::to_string(actual.sourceId),
        failures) && success;
    success = assertDialogScalar(context, step, dialogNode, "title", actual.title, failures) && success;
    success = assertDialogScalar(context, step, dialogNode, "house_title", actual.houseTitle, failures) && success;
    success = assertDialogScalar(
        context,
        step,
        dialogNode,
        "line_count",
        std::to_string(actual.lineCount),
        failures) && success;
    success = assertDialogScalar(
        context,
        step,
        dialogNode,
        "text_hash",
        std::to_string(actual.textHash),
        failures) && success;
    success = assertDialogScalar(
        context,
        step,
        dialogNode,
        "action_count",
        std::to_string(actual.actions.size()),
        failures) && success;

    // action_label_present / action_label_absent: an action with exactly this label is offered, or none is.
    for (const char *pKey : {"action_label_present", "action_label_absent"})
    {
        const YAML::Node labelNode = dialogNode[pKey];

        if (!labelNode || !labelNode.IsScalar())
        {
            continue;
        }

        const std::string label = labelNode.as<std::string>();
        const bool wanted = std::string(pKey) == "action_label_present";
        const bool found = std::any_of(actual.actions.begin(), actual.actions.end(),
            [&label](const ScenarioDialogActionSnapshot &action) { return action.label == label; });
        scenarioLogAssert(context, step, std::string("dialog.") + pKey, label, found ? "offered" : "not offered",
            found == wanted);

        if (found != wanted)
        {
            failures.push_back(stepLocation(step) + ": " + phase + " dialog " + (found ? "offers" : "does not offer")
                + " \"" + label + "\"");
            success = false;
        }
    }

    // text_contains: a piece of the dialog's text.
    if (const YAML::Node containsNode = dialogNode["text_contains"]; containsNode && containsNode.IsScalar())
    {
        const std::string expected = containsNode.as<std::string>();
        const bool found = actual.text.find(expected) != std::string::npos;
        scenarioLogAssert(context, step, "dialog.text_contains", expected, found ? expected : actual.text, found);

        if (!found)
        {
            failures.push_back(stepLocation(step) + ": " + phase + " dialog text \"" + actual.text
                + "\" does not contain \"" + expected + "\"");
            success = false;
        }
    }

    const YAML::Node actionsNode = dialogNode["actions"];

    if (actionsNode)
    {
        if (!actionsNode.IsSequence())
        {
            failures.push_back(stepLocation(step) + ": " + phase + " dialog actions expectation must be a sequence");
            return false;
        }

        success = recordScenarioAssertion(
            context,
            step,
            "dialog.actions.size",
            std::to_string(actionsNode.size()),
            std::to_string(actual.actions.size()),
            failures) && success;

        const size_t checkedCount = std::min(actionsNode.size(), actual.actions.size());

        for (size_t actionIndex = 0; actionIndex < checkedCount; ++actionIndex)
        {
            const YAML::Node actionNode = actionsNode[actionIndex];

            if (!actionNode || !actionNode.IsMap())
            {
                failures.push_back(stepLocation(step) + ": " + phase + " dialog action expectation must be a mapping");
                success = false;
                continue;
            }

            const ScenarioDialogActionSnapshot &action = actual.actions[actionIndex];
            success = assertDialogActionScalar(
                context,
                step,
                actionNode,
                actionIndex,
                "index",
                std::to_string(action.index),
                failures) && success;
            success = assertDialogActionScalar(
                context,
                step,
                actionNode,
                actionIndex,
                "kind",
                action.kind,
                failures) && success;
            success = assertDialogActionScalar(
                context,
                step,
                actionNode,
                actionIndex,
                "id",
                std::to_string(action.id),
                failures) && success;
            success = assertDialogActionScalar(
                context,
                step,
                actionNode,
                actionIndex,
                "secondary_id",
                std::to_string(action.secondaryId),
                failures) && success;
            success = assertDialogActionScalar(
                context,
                step,
                actionNode,
                actionIndex,
                "enabled",
                boolText(action.enabled),
                failures) && success;
            success = assertDialogActionScalar(
                context,
                step,
                actionNode,
                actionIndex,
                "text_only",
                boolText(action.textOnly),
                failures) && success;
            success = assertDialogActionScalar(
                context,
                step,
                actionNode,
                actionIndex,
                "label",
                action.label,
                failures) && success;
        }
    }

    scenarioLog(
        context,
        success ? ScenarioLogColor::Green : ScenarioLogColor::Red,
        std::string(success ? "DIALOG assert pass " : "DIALOG assert fail ")
            + phase + " step=" + std::to_string(step.stepIndex)
            + " " + context.runtimeDriver->activeDialogSummary());

    return context.mode != ScenarioMode::Faithful || success;
}

bool assertInputPromptState(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const YAML::Node &promptNode,
    const std::string &phase,
    std::vector<std::string> &failures)
{
    if (!promptNode)
    {
        return true;
    }

    if (!promptNode.IsMap())
    {
        failures.push_back(
            stepLocation(step) + ": " + phase + " input_prompt expectation must be a mapping");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    const ScenarioInputPromptSnapshot actual = context.runtimeDriver->activeInputPromptSnapshot();
    bool success = true;

    success = recordScenarioAssertion(
        context,
        step,
        "input_prompt.active",
        promptNode["active"] && promptNode["active"].IsScalar()
            ? boolText(promptNode["active"].as<bool>())
            : "true",
        boolText(actual.active),
        failures) && success;

    if (actual.active)
    {
        success = assertDialogScalar(
            context,
            step,
            promptNode,
            "event_id",
            std::to_string(actual.eventId),
            failures) && success;
        success = assertDialogScalar(
            context,
            step,
            promptNode,
            "continue_step",
            std::to_string(actual.continueStep),
            failures) && success;
        success = assertDialogScalar(
            context,
            step,
            promptNode,
            "correct_step",
            std::to_string(actual.correctStep),
            failures) && success;
        success = assertDialogScalar(
            context,
            step,
            promptNode,
            "text_id",
            std::to_string(actual.textId),
            failures) && success;
        success = assertDialogScalar(context, step, promptNode, "prompt", actual.text, failures) && success;
        success = assertDialogScalar(
            context,
            step,
            promptNode,
            "answer_count",
            std::to_string(actual.answerCount),
            failures) && success;
    }

    scenarioLog(
        context,
        success ? ScenarioLogColor::Green : ScenarioLogColor::Red,
        std::string(success ? "INPUT_PROMPT assert pass " : "INPUT_PROMPT assert fail ")
            + phase + " step=" + std::to_string(step.stepIndex)
            + " active=" + boolText(actual.active)
            + " event_id=" + std::to_string(actual.eventId)
            + " prompt=\"" + actual.text + "\"");

    return context.mode != ScenarioMode::Faithful || success;
}

void applyPartyStateToRuntimeDriver(ScenarioExecutionContext &context)
{
    if (context.runtimeDriver)
    {
        context.runtimeDriver->setPartyState(context.party);
    }
}

bool applyRecordedNewGamePartyMember(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node memberNode = step.payload["new_game_party_member"];

    if (!memberNode)
    {
        return true;
    }

    if (!memberNode.IsMap())
    {
        failures.push_back(stepLocation(step) + ": new_game_party_member assertion payload must be a mapping");
        return false;
    }

    if (!memberNode["member_index"] || !memberNode["member_index"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": new_game_party_member requires scalar field 'member_index'");
        return false;
    }

    const size_t memberIndex = memberNode["member_index"].as<size_t>();
    Character *pMember = context.party.member(memberIndex);

    if (pMember == nullptr)
    {
        failures.push_back(stepLocation(step) + ": new_game_party_member member_index "
            + std::to_string(memberIndex) + " does not exist");
        return false;
    }

    if (memberNode["name"] && memberNode["name"].IsScalar())
    {
        pMember->name = memberNode["name"].as<std::string>();
    }

    if (memberNode["class"] && memberNode["class"].IsScalar())
    {
        context.party.setMemberClassName(memberIndex, memberNode["class"].as<std::string>());
        pMember = context.party.member(memberIndex);

        if (pMember == nullptr)
        {
            failures.push_back(stepLocation(step) + ": new_game_party_member member_index "
                + std::to_string(memberIndex) + " disappeared after class assignment");
            return false;
        }
    }

    if (memberNode["role"] && memberNode["role"].IsScalar())
    {
        pMember->role = memberNode["role"].as<std::string>();
    }

    if (memberNode["race_id"] && memberNode["race_id"].IsScalar())
    {
        pMember->raceId = memberNode["race_id"].as<uint32_t>();
    }

    if (memberNode["sex_id"] && memberNode["sex_id"].IsScalar())
    {
        pMember->sexId = memberNode["sex_id"].as<uint32_t>();
    }

    if (memberNode["portrait_id"] && memberNode["portrait_id"].IsScalar())
    {
        pMember->portraitPictureId = memberNode["portrait_id"].as<uint32_t>();
    }

    if (memberNode["voice_id"] && memberNode["voice_id"].IsScalar())
    {
        pMember->voiceId = memberNode["voice_id"].as<int32_t>();
    }

    if (memberNode["level"] && memberNode["level"].IsScalar())
    {
        pMember->level = std::max<uint32_t>(1, memberNode["level"].as<uint32_t>());
    }

    if (memberNode["might"] && memberNode["might"].IsScalar())
    {
        pMember->might = memberNode["might"].as<uint32_t>();
    }

    if (memberNode["intellect"] && memberNode["intellect"].IsScalar())
    {
        pMember->intellect = memberNode["intellect"].as<uint32_t>();
    }

    if (memberNode["personality"] && memberNode["personality"].IsScalar())
    {
        pMember->personality = memberNode["personality"].as<uint32_t>();
    }

    if (memberNode["endurance"] && memberNode["endurance"].IsScalar())
    {
        pMember->endurance = memberNode["endurance"].as<uint32_t>();
    }

    if (memberNode["accuracy"] && memberNode["accuracy"].IsScalar())
    {
        pMember->accuracy = memberNode["accuracy"].as<uint32_t>();
    }

    if (memberNode["speed"] && memberNode["speed"].IsScalar())
    {
        pMember->speed = memberNode["speed"].as<uint32_t>();
    }

    if (memberNode["luck"] && memberNode["luck"].IsScalar())
    {
        pMember->luck = memberNode["luck"].as<uint32_t>();
    }

    applyPartyStateToRuntimeDriver(context);
    return true;
}

bool applyRecordedNewGamePartySkill(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node skillNode = step.payload["new_game_party_skill"];

    if (!skillNode)
    {
        return true;
    }

    if (!skillNode.IsMap())
    {
        failures.push_back(stepLocation(step) + ": new_game_party_skill assertion payload must be a mapping");
        return false;
    }

    if (!skillNode["member_index"] || !skillNode["member_index"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": new_game_party_skill requires scalar field 'member_index'");
        return false;
    }

    if (!skillNode["name"] || !skillNode["name"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": new_game_party_skill requires scalar field 'name'");
        return false;
    }

    const size_t memberIndex = skillNode["member_index"].as<size_t>();
    Character *pMember = context.party.member(memberIndex);

    if (pMember == nullptr)
    {
        failures.push_back(stepLocation(step) + ": new_game_party_skill member_index "
            + std::to_string(memberIndex) + " does not exist");
        return false;
    }

    CharacterSkill skill = {};
    skill.name = canonicalSkillName(skillNode["name"].as<std::string>());

    if (skill.name.empty())
    {
        failures.push_back(stepLocation(step) + ": new_game_party_skill has unknown skill '"
            + skillNode["name"].as<std::string>() + "'");
        return false;
    }

    if (skillNode["level"] && skillNode["level"].IsScalar())
    {
        skill.level = skillNode["level"].as<uint32_t>();
    }

    if (skillNode["mastery"] && skillNode["mastery"].IsScalar())
    {
        const uint32_t mastery = skillNode["mastery"].as<uint32_t>();
        skill.mastery =
            static_cast<SkillMastery>(std::min<uint32_t>(mastery, static_cast<uint32_t>(SkillMastery::Grandmaster)));
    }

    pMember->skills[skill.name] = skill;
    applyPartyStateToRuntimeDriver(context);
    return true;
}

void synchronizeRuntimeClock(ScenarioExecutionContext &context)
{
    static constexpr float MinutesPerDay = 24.0f * 60.0f;

    const int totalMinutes = std::max(0, static_cast<int>(std::floor(context.gameMinutes)));
    const int hour = (totalMinutes / 60) % 24;
    const int dayOfYear = std::max(1, static_cast<int>(totalMinutes / MinutesPerDay) + 1);

    context.eventRuntimeState.variables[static_cast<uint32_t>(EvtVariable::Hour)] = hour;
    context.eventRuntimeState.variables[static_cast<uint32_t>(EvtVariable::DayOfYear)] = dayOfYear;
}

bool payloadIsMap(
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (step.payload && step.payload.IsMap())
    {
        return true;
    }

    failures.push_back(stepLocation(step) + ": step payload must be a mapping");
    return false;
}

bool readScalarString(
    const ScenarioStep &step,
    const char *pFieldName,
    std::string &value,
    std::vector<std::string> &failures,
    bool required)
{
    if (!step.payload[pFieldName])
    {
        if (required)
        {
            failures.push_back(stepLocation(step) + ": missing scalar field '" + pFieldName + "'");
        }

        return !required;
    }

    if (!step.payload[pFieldName].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": field '" + pFieldName + "' must be scalar");
        return false;
    }

    value = step.payload[pFieldName].as<std::string>();
    return true;
}

bool readScalarFloat(
    const ScenarioStep &step,
    const char *pFieldName,
    float &value,
    std::vector<std::string> &failures,
    bool required)
{
    if (!step.payload[pFieldName])
    {
        if (required)
        {
            failures.push_back(stepLocation(step) + ": missing scalar field '" + pFieldName + "'");
        }

        return !required;
    }

    if (!step.payload[pFieldName].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": field '" + pFieldName + "' must be scalar");
        return false;
    }

    value = step.payload[pFieldName].as<float>();
    return true;
}

float degreesToRadians(float degrees)
{
    return degrees * 3.14159265358979323846f / 180.0f;
}

float normalizedAngleDifference(float left, float right)
{
    constexpr float Pi = 3.14159265358979323846f;
    float difference = left - right;

    while (difference > Pi)
    {
        difference -= Pi * 2.0f;
    }

    while (difference < -Pi)
    {
        difference += Pi * 2.0f;
    }

    return std::abs(difference);
}

std::optional<ScenarioPose> readLoadMapPoseOverride(
    const ScenarioStep &step,
    const std::string &mapFileName,
    std::vector<std::string> &failures)
{
    if (!step.payload["pos"])
    {
        return std::nullopt;
    }

    if (!step.payload["pos"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": field 'pos' must be scalar");
        return std::nullopt;
    }

    std::string text = step.payload["pos"].as<std::string>();
    if (lowerAscii(text) == "none" || lowerAscii(text) == "null" || text.empty())
    {
        return std::nullopt;
    }

    text.erase(std::remove(text.begin(), text.end(), '('), text.end());
    text.erase(std::remove(text.begin(), text.end(), ')'), text.end());

    std::stringstream stream(text);
    std::string xText;
    std::string yText;
    std::string zText;

    if (!std::getline(stream, xText, ',')
        || !std::getline(stream, yText, ',')
        || !std::getline(stream, zText, ','))
    {
        failures.push_back(stepLocation(step) + ": field 'pos' must contain three comma-separated coordinates");
        return std::nullopt;
    }

    ScenarioPose pose = {};
    pose.mapFileName = mapFileName;

    try
    {
        pose.x = std::stof(xText);
        pose.y = std::stof(yText);
        pose.z = std::stof(zText);
    }
    catch (const std::exception &)
    {
        failures.push_back(stepLocation(step) + ": field 'pos' contains a non-numeric coordinate");
        return std::nullopt;
    }

    if (step.payload["direction_degrees"] && step.payload["direction_degrees"].IsScalar())
    {
        const std::string directionText = step.payload["direction_degrees"].as<std::string>();
        if (directionText != "none")
        {
            try
            {
                pose.yawRadians = degreesToRadians(std::stof(directionText));
            }
            catch (const std::exception &)
            {
                failures.push_back(stepLocation(step) + ": field 'direction_degrees' must be numeric or 'none'");
                return std::nullopt;
            }
        }
    }

    return pose;
}

void syncContextFromRuntime(ScenarioExecutionContext &context)
{
    if (!context.runtimeDriver)
    {
        return;
    }

    if (const Party *pParty = context.runtimeDriver->party())
    {
        context.party = *pParty;
    }

    if (const EventRuntimeState *pEventRuntimeState = context.runtimeDriver->eventRuntimeState())
    {
        context.eventRuntimeState = *pEventRuntimeState;
        context.eventRuntimeStateLoaded = true;
    }

    context.currentMapFileName = context.runtimeDriver->currentMapFileName();
    context.gameMinutes = context.runtimeDriver->gameMinutes();
    synchronizeRuntimeClock(context);
}

std::optional<float> recordedGameMinutesForStep(const ScenarioStep &step)
{
    if (!step.payload || !step.payload.IsMap())
    {
        return std::nullopt;
    }

    if (step.kind == ScenarioStepKind::AdvanceGameTime
        && step.payload["before_game_minutes"] && step.payload["before_game_minutes"].IsScalar())
    {
        return step.payload["before_game_minutes"].as<float>();
    }

    if (step.payload["game_minutes"] && step.payload["game_minutes"].IsScalar())
    {
        return step.payload["game_minutes"].as<float>();
    }

    return std::nullopt;
}

bool syncRecordedGameTimeBeforeStep(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const std::optional<float> recordedGameMinutes = recordedGameMinutesForStep(step);

    if (!recordedGameMinutes.has_value())
    {
        return true;
    }

    if (!std::isfinite(*recordedGameMinutes))
    {
        failures.push_back(stepLocation(step) + ": recorded game_minutes is not finite");
        return false;
    }

    const float deltaMinutes = *recordedGameMinutes - context.gameMinutes;
    if (std::abs(deltaMinutes) > 0.001f)
    {
        scenarioLog(
            context,
            ScenarioLogColor::Cyan,
            "TIME sync before step=" + std::to_string(step.stepIndex)
                + " trace_line=" + std::to_string(step.sourceLine)
                + " previous_game_minutes=" + std::to_string(context.gameMinutes)
                + " recorded_game_minutes=" + std::to_string(*recordedGameMinutes)
                + " delta_minutes=" + std::to_string(deltaMinutes));
    }

    context.gameMinutes = *recordedGameMinutes;
    synchronizeRuntimeClock(context);

    if (context.runtimeDriver)
    {
        context.runtimeDriver->setGameMinutes(context.gameMinutes);
    }

    return true;
}

bool ensureRuntimeDriver(
    ScenarioExecutionContext &context,
    std::vector<std::string> &failures)
{
    if (!context.runtimeDriver)
    {
        context.runtimeDriver = std::make_unique<ScenarioRuntimeDriver>(
            context.basePath,
            context.config,
            context.assetFileSystem);
        context.runtimeDriver->setMadnessLedgerFile(context.saveGameRootPath / "maw_madness_deaths.txt");
        context.runtimeDriver->setPlaythroughStatisticsDirectory(context.saveGameRootPath / "playthroughs");
    }

    std::string failure;

    if (!context.runtimeDriver->initialize(failure))
    {
        failures.push_back(failure);
        return false;
    }

    return true;
}

void seedRuntimeDriverFromContext(ScenarioExecutionContext &context)
{
    if (!context.runtimeDriver)
    {
        return;
    }

    context.runtimeDriver->setPartyState(context.party);
    context.runtimeDriver->setGameMinutes(context.gameMinutes);

    if (context.eventRuntimeStateLoaded)
    {
        context.runtimeDriver->setEventRuntimeState(context.eventRuntimeState);
    }
}

std::optional<ScenarioPose> readScenarioPose(
    const ScenarioStep &step,
    std::vector<std::string> &failures,
    bool required)
{
    const YAML::Node poseNode = step.payload["pose"];
    const YAML::Node sourceNode = poseNode ? poseNode : step.payload;

    if (!sourceNode || !sourceNode.IsMap())
    {
        if (required)
        {
            failures.push_back(stepLocation(step) + ": pose payload must be a mapping");
        }

        return std::nullopt;
    }

    if (!sourceNode["x"] || !sourceNode["y"] || !sourceNode["z"])
    {
        if (required)
        {
            failures.push_back(stepLocation(step) + ": pose requires scalar fields 'x', 'y', and 'z'");
        }

        return std::nullopt;
    }

    ScenarioPose pose = {};

    if (sourceNode["map"] && sourceNode["map"].IsScalar())
    {
        pose.mapFileName = sourceNode["map"].as<std::string>();
    }

    pose.x = sourceNode["x"].as<float>();
    pose.y = sourceNode["y"].as<float>();
    pose.z = sourceNode["z"].as<float>();

    if (sourceNode["yaw"] && sourceNode["yaw"].IsScalar())
    {
        pose.yawRadians = sourceNode["yaw"].as<float>();
    }
    else if (sourceNode["yaw_degrees"] && sourceNode["yaw_degrees"].IsScalar())
    {
        pose.yawRadians = degreesToRadians(sourceNode["yaw_degrees"].as<float>());
    }

    if (sourceNode["pitch"] && sourceNode["pitch"].IsScalar())
    {
        pose.pitchRadians = sourceNode["pitch"].as<float>();
    }
    else if (sourceNode["pitch_degrees"] && sourceNode["pitch_degrees"].IsScalar())
    {
        pose.pitchRadians = degreesToRadians(sourceNode["pitch_degrees"].as<float>());
    }

    return pose;
}

std::optional<ScenarioPose> readScenarioPoseNode(
    const ScenarioStep &step,
    const YAML::Node &sourceNode,
    const char *pFieldName,
    std::vector<std::string> &failures,
    bool required)
{
    if (!sourceNode || !sourceNode.IsMap())
    {
        if (required)
        {
            failures.push_back(stepLocation(step) + ": field '" + pFieldName + "' must be a pose mapping");
        }

        return std::nullopt;
    }

    if (!sourceNode["x"] || !sourceNode["y"] || !sourceNode["z"])
    {
        if (required)
        {
            failures.push_back(stepLocation(step) + ": field '" + pFieldName
                + "' requires scalar fields 'x', 'y', and 'z'");
        }

        return std::nullopt;
    }

    ScenarioPose pose = {};

    if (sourceNode["map"] && sourceNode["map"].IsScalar())
    {
        pose.mapFileName = sourceNode["map"].as<std::string>();
    }

    pose.x = sourceNode["x"].as<float>();
    pose.y = sourceNode["y"].as<float>();
    pose.z = sourceNode["z"].as<float>();

    if (sourceNode["yaw"] && sourceNode["yaw"].IsScalar())
    {
        pose.yawRadians = sourceNode["yaw"].as<float>();
    }
    else if (sourceNode["yaw_degrees"] && sourceNode["yaw_degrees"].IsScalar())
    {
        pose.yawRadians = degreesToRadians(sourceNode["yaw_degrees"].as<float>());
    }

    if (sourceNode["pitch"] && sourceNode["pitch"].IsScalar())
    {
        pose.pitchRadians = sourceNode["pitch"].as<float>();
    }
    else if (sourceNode["pitch_degrees"] && sourceNode["pitch_degrees"].IsScalar())
    {
        pose.pitchRadians = degreesToRadians(sourceNode["pitch_degrees"].as<float>());
    }

    return pose;
}

float poseDistanceXY(const ScenarioPose &left, const ScenarioPose &right)
{
    const float dx = left.x - right.x;
    const float dy = left.y - right.y;
    return std::sqrt(dx * dx + dy * dy);
}

float poseDistanceZ(const ScenarioPose &left, const ScenarioPose &right)
{
    return std::abs(left.z - right.z);
}

std::string scenarioFloat(float value)
{
    std::ostringstream stream;
    stream << std::fixed << std::setprecision(3) << value;
    return stream.str();
}

std::string scenarioHitKindName(GameplayWorldHitKind kind)
{
    switch (kind)
    {
    case GameplayWorldHitKind::None:
        return "none";
    case GameplayWorldHitKind::Actor:
        return "actor";
    case GameplayWorldHitKind::WorldItem:
        return "world_item";
    case GameplayWorldHitKind::Chest:
        return "chest";
    case GameplayWorldHitKind::Corpse:
        return "corpse";
    case GameplayWorldHitKind::EventTarget:
        return "event_target";
    case GameplayWorldHitKind::Object:
        return "object";
    case GameplayWorldHitKind::Ground:
        return "ground";
    }

    return "unknown";
}

std::string interactionEventFieldText(
    const ScenarioInteractionResult &interaction,
    const std::string &fieldName)
{
    if (!interaction.hit.eventTarget)
    {
        return "<no-event-target>";
    }

    const GameplayEventTargetHit &eventTarget = *interaction.hit.eventTarget;

    if (fieldName == "target_kind")
    {
        return std::to_string(static_cast<uint32_t>(eventTarget.targetKind));
    }

    if (fieldName == "target_index")
    {
        return std::to_string(eventTarget.targetIndex);
    }

    if (fieldName == "face_index")
    {
        return std::to_string(eventTarget.secondaryIndex);
    }

    if (fieldName == "triggered_event")
    {
        return std::to_string(eventTarget.triggeredEventId);
    }

    if (fieldName == "trigger")
    {
        return std::to_string(eventTarget.trigger);
    }

    if (fieldName == "name")
    {
        return eventTarget.name;
    }

    return "<unsupported-event-field>";
}

std::string interactionActorFieldText(
    const ScenarioInteractionResult &interaction,
    const std::string &fieldName)
{
    if (!interaction.hit.actor)
    {
        return "<no-actor>";
    }

    const GameplayActorTargetHit &actor = *interaction.hit.actor;

    if (fieldName == "actor_index")
    {
        return std::to_string(actor.actorIndex);
    }

    if (fieldName == "npc_id")
    {
        return std::to_string(actor.npcId);
    }

    if (fieldName == "group")
    {
        return std::to_string(actor.actorGroup);
    }

    if (fieldName == "friendly")
    {
        return boolText(actor.isFriendly);
    }

    if (fieldName == "name")
    {
        return actor.displayName;
    }

    return "<unsupported-actor-field>";
}

std::string interactionWorldItemFieldText(
    const ScenarioInteractionResult &interaction,
    const std::string &fieldName)
{
    if (!interaction.hit.worldItem)
    {
        return "<no-world-item>";
    }

    const GameplayWorldItemTargetHit &worldItem = *interaction.hit.worldItem;

    if (fieldName == "world_item_index")
    {
        return std::to_string(worldItem.worldItemIndex);
    }

    if (fieldName == "item_id")
    {
        return std::to_string(worldItem.objectDescriptionId);
    }

    if (fieldName == "sprite_id")
    {
        return std::to_string(worldItem.objectSpriteId);
    }

    return "<unsupported-world-item-field>";
}

std::string interactionContainerFieldText(
    const ScenarioInteractionResult &interaction,
    const std::string &fieldName)
{
    if (!interaction.hit.container)
    {
        return "<no-container>";
    }

    const GameplayContainerTargetHit &container = *interaction.hit.container;

    if (fieldName == "source_index")
    {
        return std::to_string(container.sourceIndex);
    }

    return "<unsupported-container-field>";
}

bool scalarNodeEquals(const YAML::Node &node, const std::string &expected)
{
    return node && node.IsScalar() && node.as<std::string>() == expected;
}

std::optional<uint32_t> readOptionalUInt(const YAML::Node &node)
{
    if (!node || !node.IsScalar())
    {
        return std::nullopt;
    }

    try
    {
        return static_cast<uint32_t>(std::stoul(node.as<std::string>()));
    }
    catch (const std::exception &)
    {
        return std::nullopt;
    }
}

bool scenarioWorldItemNeedsStrictIdentity(
    const ScenarioExecutionContext &context,
    const YAML::Node &expectNode)
{
    if (!scalarNodeEquals(expectNode["kind"], "world_item"))
    {
        return true;
    }

    if (expectNode["strict_identity"] && expectNode["strict_identity"].IsScalar())
    {
        return expectNode["strict_identity"].as<bool>();
    }

    const std::optional<uint32_t> itemId = readOptionalUInt(expectNode["item_id"]);

    if (!itemId.has_value())
    {
        return false;
    }

    if (*itemId >= 2100)
    {
        return true;
    }

    const ItemDefinition *pItemDefinition = context.gameDataLoader.getItemTable().get(*itemId);
    return pItemDefinition != nullptr && pItemDefinition->rarity != ItemRarity::Common;
}

bool assertScalarInteractionField(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const YAML::Node &expectNode,
    const ScenarioInteractionResult &interaction,
    const char *pFieldName,
    std::vector<std::string> &failures)
{
    if (!expectNode[pFieldName] || !expectNode[pFieldName].IsScalar())
    {
        return true;
    }

    const std::string fieldName = pFieldName;
    const std::string expected = expectNode[pFieldName].as<std::string>();
    std::string actual;

    if (fieldName == "has_hit")
    {
        actual = boolText(interaction.hit.hasHit);
    }
    else if (fieldName == "can_activate")
    {
        actual = boolText(interaction.activated);
    }
    else if (fieldName == "kind")
    {
        actual = scenarioHitKindName(interaction.hit.kind);
    }
    else if (fieldName == "target_kind"
        || fieldName == "target_index"
        || fieldName == "face_index"
        || fieldName == "triggered_event"
        || fieldName == "trigger")
    {
        actual = interactionEventFieldText(interaction, fieldName);
    }
    else if (fieldName == "actor_index"
        || fieldName == "npc_id"
        || fieldName == "group"
        || fieldName == "friendly")
    {
        actual = interactionActorFieldText(interaction, fieldName);
    }
    else if (fieldName == "world_item_index"
        || fieldName == "item_id"
        || fieldName == "sprite_id")
    {
        actual = interactionWorldItemFieldText(interaction, fieldName);
    }
    else if (fieldName == "source_index")
    {
        actual = interactionContainerFieldText(interaction, fieldName);
    }
    else if (fieldName == "name")
    {
        if (interaction.hit.eventTarget)
        {
            actual = interaction.hit.eventTarget->name;
        }
        else if (interaction.hit.actor)
        {
            actual = interaction.hit.actor->displayName;
        }
        else
        {
            actual = "<no-name>";
        }
    }
    else
    {
        return true;
    }

    if ((fieldName == "target_index" || fieldName == "face_index")
        && expected != actual
        && interaction.hit.kind == GameplayWorldHitKind::EventTarget
        && expectNode["kind"] && expectNode["kind"].IsScalar()
        && expectNode["kind"].as<std::string>() == "event_target"
        && expectNode["triggered_event"] && expectNode["triggered_event"].IsScalar()
        && interactionEventFieldText(interaction, "triggered_event")
            == expectNode["triggered_event"].as<std::string>())
    {
        scenarioLog(
            context,
            ScenarioLogColor::Yellow,
            std::string("ASSERT compatible step=") + std::to_string(step.stepIndex)
                + " trace_line=" + std::to_string(step.sourceLine)
                + " " + fieldName + " expected=" + expected
                + " actual=" + actual
                + " same triggered_event=" + interactionEventFieldText(interaction, "triggered_event"));
        return true;
    }

    if ((fieldName == "world_item_index" || fieldName == "item_id" || fieldName == "sprite_id")
        && expected != actual
        && !scenarioWorldItemNeedsStrictIdentity(context, expectNode))
    {
        scenarioLog(
            context,
            ScenarioLogColor::Yellow,
            std::string("WARNING step=") + std::to_string(step.stepIndex)
                + " trace_line=" + std::to_string(step.sourceLine)
                + " random world item " + fieldName
                + " expected=" + expected
                + " actual=" + actual);
        return true;
    }

    return recordScenarioAssertion(context, step, fieldName, expected, actual, failures);
}

bool assertInteractionExpectation(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const ScenarioInteractionResult &interaction,
    std::vector<std::string> &failures)
{
    const YAML::Node expectNode = step.payload["expect"] ? step.payload["expect"] : step.payload;

    if (!expectNode)
    {
        return true;
    }

    if (!expectNode.IsMap())
    {
        failures.push_back(stepLocation(step) + ": press_interact expect payload must be a mapping");
        return false;
    }

    bool success = true;

    if (expectNode["map"] && expectNode["map"].IsScalar())
    {
        const std::string actualMap = !interaction.mapFileName.empty()
            ? interaction.mapFileName
            : (context.runtimeDriver ? context.runtimeDriver->currentMapFileName() : context.currentMapFileName);
        success = recordScenarioAssertion(
            context,
            step,
            "map",
            lowerAscii(expectNode["map"].as<std::string>()),
            lowerAscii(actualMap),
            failures)
            && success;
    }

    const char *pCheckedFields[] = {
        "has_hit",
        "can_activate",
        "kind",
        "target_kind",
        "target_index",
        "face_index",
        "triggered_event",
        "trigger",
        "actor_index",
        "npc_id",
        "group",
        "friendly",
        "world_item_index",
        "item_id",
        "sprite_id",
        "source_index",
        "name",
    };

    for (const char *pFieldName : pCheckedFields)
    {
        success = assertScalarInteractionField(context, step, expectNode, interaction, pFieldName, failures)
            && success;
    }

    scenarioLog(
        context,
        success ? ScenarioLogColor::Green : ScenarioLogColor::Red,
        std::string("INTERACT current step=") + std::to_string(step.stepIndex)
            + " " + gameplayDebugTraceWorldHitSummary(interaction.hit));

    return success;
}

std::string readCheckpointName(
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (step.payload.IsScalar())
    {
        return step.payload.as<std::string>();
    }

    if (step.payload.IsMap())
    {
        std::string name;

        if (readScalarString(step, "name", name, failures, true))
        {
            return name;
        }
    }
    else
    {
        failures.push_back(stepLocation(step) + ": checkpoint payload must be a scalar or mapping");
    }

    return {};
}

std::string sanitizeScenarioFileStem(const std::string &value)
{
    std::string stem;
    stem.reserve(value.size());

    for (char character : value)
    {
        if (std::isalnum(static_cast<unsigned char>(character)) || character == '_' || character == '-')
        {
            stem.push_back(character);
        }
        else
        {
            stem.push_back('_');
        }
    }

    return stem.empty() ? "recorded_save" : stem;
}

bool payloadMapOrScalar(
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (step.payload && (step.payload.IsMap() || step.payload.IsScalar()))
    {
        return true;
    }

    failures.push_back(stepLocation(step) + ": step payload must be a mapping or scalar");
    return false;
}

bool ensureGameDataLoaded(
    ScenarioExecutionContext &context,
    std::vector<std::string> &failures)
{
    if (context.gameDataLoaded)
    {
        return true;
    }

    if (!context.gameDataLoader.loadForHeadlessGameplay(context.assetFileSystem))
    {
        failures.push_back("could not load headless gameplay data");
        return false;
    }

    context.party.setItemTable(&context.gameDataLoader.getItemTable());
    context.party.setJournalQuestTable(&context.gameDataLoader.getJournalQuestTable());
    context.party.setCharacterDollTable(&context.gameDataLoader.getCharacterDollTable());
    context.party.setItemEnchantTables(
        &context.gameDataLoader.getStandardItemEnchantTable(),
        &context.gameDataLoader.getSpecialItemEnchantTable());
    context.party.setTrainerDirectory(&context.gameDataLoader.getTrainerDirectory());
    context.gameDataLoaded = true;
    return true;
}

bool loadMap(
    ScenarioExecutionContext &context,
    const std::string &mapFileName,
    std::vector<std::string> &failures)
{
    scenarioLog(context, ScenarioLogColor::Cyan, "LOAD data begin map=" + mapFileName);

    if (!ensureGameDataLoaded(context, failures))
    {
        return false;
    }

    if (!context.gameDataLoader.loadMapByFileNameForHeadlessGameplay(context.assetFileSystem, mapFileName))
    {
        failures.push_back("could not load map '" + mapFileName + "'");
        return false;
    }

    context.currentMapFileName = mapFileName;
    scenarioLog(context, ScenarioLogColor::Green, "LOAD data complete map=" + mapFileName);

    const std::optional<MapAssetInfo> &selectedMap = context.gameDataLoader.getSelectedMap();
    if (selectedMap && selectedMap->eventRuntimeState)
    {
        context.eventRuntimeState = *selectedMap->eventRuntimeState;
        context.eventRuntimeStateLoaded = true;
        synchronizeRuntimeClock(context);
        context.eventRuntime.executeOnLoadEvents(
            selectedMap->localEventProgram,
            selectedMap->globalEventProgram,
            context.eventRuntimeState,
            &context.party,
            nullptr);
        context.party.applyEventRuntimeState(context.eventRuntimeState);
    }
    else
    {
        context.eventRuntimeState = {};
        context.eventRuntimeStateLoaded = false;
    }

    return true;
}

bool executeRecordedEvent(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    uint16_t eventId,
    bool allowFailure)
{
    if (eventId == 0)
    {
        return true;
    }

    const std::optional<MapAssetInfo> &selectedMap = context.gameDataLoader.getSelectedMap();

    if (!selectedMap || !context.eventRuntimeStateLoaded)
    {
        return allowFailure;
    }

    synchronizeRuntimeClock(context);

    const bool executed = context.eventRuntime.executeEventById(
        selectedMap->localEventProgram,
        selectedMap->globalEventProgram,
        eventId,
        context.eventRuntimeState,
        &context.party,
        nullptr);

    if (!executed)
    {
        return allowFailure;
    }

    context.party.applyEventRuntimeState(context.eventRuntimeState);
    return true;
}

// A party member's `battle_orders: {fallback: weapon|hold, orders: [...]}` (devdocs/BATTLE_ORDERS.md). Each order is
// `{spell: <table name>}`, `{melee: true}` or `{shoot: true}`, with optional `distance: [min, max]`, `ally_hp_below`
// and `keep_sp` (percent) and `enabled`.
bool readScenarioBattleOrders(
    ScenarioExecutionContext &context,
    const YAML::Node &node,
    Character &member,
    std::string &failure)
{
    if (!node.IsMap() || !node["orders"] || !node["orders"].IsSequence() || node["orders"].size() > BattleOrderLimit)
    {
        failure = "battle_orders needs an 'orders' list of at most " + std::to_string(BattleOrderLimit);
        return false;
    }

    const std::string fallback = node["fallback"].as<std::string>("weapon");

    if (fallback != "weapon" && fallback != "hold")
    {
        failure = "battle_orders fallback must be weapon or hold";
        return false;
    }

    const YAML::Node upkeepNode = node["upkeep"];

    if (upkeepNode && (!upkeepNode.IsSequence() || upkeepNode.size() > BattleOrderLimit))
    {
        failure = "battle_orders upkeep must be a list of at most " + std::to_string(BattleOrderLimit);
        return false;
    }

    // The attack orders, then the upkeep list's (spells only).
    std::vector<BattleOrder> orders;
    std::vector<BattleOrder> upkeep;
    std::vector<std::pair<YAML::Node, bool>> orderNodes;

    for (const YAML::Node &orderNode : node["orders"])
    {
        orderNodes.emplace_back(orderNode, false);
    }

    for (const YAML::Node &orderNode : upkeepNode)
    {
        orderNodes.emplace_back(orderNode, true);
    }

    for (const auto &[orderNode, forUpkeep] : orderNodes)
    {
        BattleOrder order;

        if (forUpkeep && (!orderNode.IsMap() || !orderNode["spell"]))
        {
            failure = "an upkeep order needs a spell";
            return false;
        }

        if (!orderNode.IsMap() || int(bool(orderNode["spell"])) + int(bool(orderNode["melee"]))
            + int(bool(orderNode["shoot"])) != 1)
        {
            failure = "a battle order needs exactly one of spell, melee or shoot";
            return false;
        }

        if (orderNode["spell"])
        {
            const SpellEntry *pSpell =
                context.gameDataLoader.getSpellTable().findByName(orderNode["spell"].as<std::string>());

            if (pSpell == nullptr)
            {
                failure = "unknown battle order spell " + orderNode["spell"].as<std::string>();
                return false;
            }

            order.kind = BattleOrderKind::Spell;
            order.spellName = pSpell->name;
        }
        else
        {
            order.kind = orderNode["melee"] ? BattleOrderKind::Melee : BattleOrderKind::Shoot;
        }

        order.enabled = orderNode["enabled"].as<bool>(true);

        if (const YAML::Node distance = orderNode["distance"])
        {
            if (!distance.IsSequence() || distance.size() != 2)
            {
                failure = "battle order distance must be [min, max]";
                return false;
            }

            order.distance = BattleOrderDistance{distance[0].as<uint16_t>(), distance[1].as<uint16_t>()};
        }

        if (orderNode["ally_hp_below"])
        {
            order.allyHealthBelowPercent = uint8_t(std::clamp(orderNode["ally_hp_below"].as<int>(), 1, 100));
        }

        if (orderNode["keep_sp"])
        {
            order.keepSpellPointsPercent = uint8_t(std::clamp(orderNode["keep_sp"].as<int>(), 0, 100));
        }

        const std::string place = orderNode["place"].as<std::string>("anywhere");

        if (place != "anywhere" && place != "indoors" && place != "outdoors")
        {
            failure = "battle order place must be anywhere, indoors or outdoors";
            return false;
        }

        order.place = place == "indoors" ? BattleOrderPlace::Indoors
            : place == "outdoors"        ? BattleOrderPlace::Outdoors
                                         : BattleOrderPlace::Anywhere;

        if (forUpkeep && orderNode["renew_below"])
        {
            order.renewBelowMinutes = uint16_t(std::clamp(orderNode["renew_below"].as<int>(),
                int(UpkeepRenewMinimumMinutes), int(UpkeepRenewMaximumMinutes)));
        }

        (forUpkeep ? upkeep : orders).push_back(std::move(order));
    }

    member.battleOrders = std::move(orders);
    member.upkeepOrders = std::move(upkeep);
    member.battleOrderFallback = fallback == "hold" ? BattleOrderFallback::Hold : BattleOrderFallback::Weapon;
    return true;
}

bool readScenarioPartySeed(
    ScenarioExecutionContext &context,
    const YAML::Node &node,
    PartySeed &seed,
    std::string &failure)
{
    if (!node.IsMap() || !node["members"].IsSequence()
        || node["members"].size() == 0 || node["members"].size() > 5)
    {
        failure = "party fixture requires one to five explicit members";
        return false;
    }
    seed = {};
    seed.gold = node["gold"].as<int>(0);
    seed.food = node["food"].as<int>(0);
    const ClassSkillTable &skillTable = context.gameDataLoader.getClassSkillTable();
    for (const YAML::Node &memberNode : node["members"])
    {
        Character member = {};
        member.name = memberNode["name"].as<std::string>();
        member.className = memberNode["class"].as<std::string>();
        member.level = memberNode["level"].as<uint32_t>();
        member.portraitPictureId = memberNode["portrait_id"].as<uint32_t>(0);
        member.characterDataId = member.portraitPictureId + 1;
        // The face pictures as party creation names them (the row's prefix: 9pc02- for an MM9 hero, pc40- for the
        // gold dragon on row 75), not PC<id>-01.
        if (const CharacterDollEntry *pDoll =
                context.gameDataLoader.getCharacterDollTable().getCharacter(member.characterDataId);
            pDoll != nullptr && !pDoll->facePicturesPrefix.empty())
        {
            member.portraitTextureName = pDoll->facePicturesPrefix + "01";
        }
        member.raceId = memberNode["race_id"].as<uint32_t>(0);
        member.birthYear = 1140;
        member.might = memberNode["might"].as<uint32_t>(15);
        member.intellect = memberNode["intellect"].as<uint32_t>(15);
        member.personality = memberNode["personality"].as<uint32_t>(15);
        member.endurance = memberNode["endurance"].as<uint32_t>(15);
        member.speed = memberNode["speed"].as<uint32_t>(15);
        member.accuracy = memberNode["accuracy"].as<uint32_t>(15);
        member.luck = memberNode["luck"].as<uint32_t>(15);
        member.skillPoints = memberNode["skill_points"].as<uint32_t>(0);
        if (member.level == 0 || !skillTable.hasClass(member.className) || !memberNode["skills"]
            || !memberNode["skills"].IsSequence())
        {
            failure = "party fixture requires a valid class, positive level and explicit skills: " + member.name;
            return false;
        }
        const uint64_t minimumExperience = uint64_t(member.level) * (member.level - 1) * 500;
        const uint64_t experience = memberNode["experience"].as<uint64_t>(minimumExperience);
        if (experience < minimumExperience)
        {
            failure = "party fixture experience is below its level";
            return false;
        }
        member.experience = experience;
        for (const YAML::Node &skillNode : memberNode["skills"])
        {
            CharacterSkill skill = {};
            skill.name = canonicalSkillName(skillNode["name"].as<std::string>());
            skill.level = skillNode["level"].as<uint32_t>();
            const uint32_t mastery = skillNode["mastery"].as<uint32_t>();
            if (skill.name.empty() || skill.level == 0 || mastery == 0 || mastery > 4
                || mastery > uint32_t(skillTable.getEffectiveCap(member.className, member.raceId, skill.name))
                || member.skills.count(skill.name) != 0)
            {
                failure = "party fixture has invalid, duplicate or class-ineligible skill: " + member.name
                    + " / " + skill.name;
                return false;
            }
            skill.mastery = SkillMastery(mastery);
            member.skills.emplace(skill.name, skill);
        }
        if (memberNode["spells"])
        {
            for (const YAML::Node &spellNode : memberNode["spells"])
            {
                const uint32_t spellId = spellNode.as<uint32_t>();
                if (context.gameDataLoader.getSpellTable().findById(int(spellId)) == nullptr)
                {
                    failure = "party fixture has an unknown spell";
                    return false;
                }
                member.learnSpell(spellId);
            }
        }
        if (memberNode["battle_orders"] && !readScenarioBattleOrders(context, memberNode["battle_orders"], member,
                                                                     failure))
        {
            failure = "party fixture member " + member.name + ": " + failure;
            return false;
        }
        seed.members.push_back(std::move(member));
    }

    Party fixture;
    fixture.setItemTable(&context.gameDataLoader.getItemTable());
    fixture.setCharacterDollTable(&context.gameDataLoader.getCharacterDollTable());
    fixture.setClassSkillTable(&skillTable);
    fixture.setClassMultiplierTable(&context.gameDataLoader.getClassMultiplierTable());
    fixture.setItemEnchantTables(&context.gameDataLoader.getStandardItemEnchantTable(),
                                &context.gameDataLoader.getSpecialItemEnchantTable());
    fixture.seed(seed);
    for (size_t memberIndex = 0; memberIndex < seed.members.size(); ++memberIndex)
    {
        const YAML::Node equipmentNode = node["members"][memberIndex]["equipment"];
        if (!equipmentNode || !equipmentNode.IsMap())
        {
            failure = "party fixture requires explicit equipment for each member";
            return false;
        }
        for (const YAML::const_iterator::value_type &entry : equipmentNode)
        {
            const std::optional<EquipmentSlot> slot = parseScenarioEquipmentSlot(entry.first.as<std::string>());
            InventoryItem item = {};
            item.objectDescriptionId = entry.second.as<uint32_t>();
            std::optional<InventoryItem> displaced;
            if (!slot || !fixture.tryEquipItemOnMember(memberIndex, *slot, item, std::nullopt, true, displaced))
            {
                failure = "party fixture cannot equip member " + std::to_string(memberIndex)
                    + " with item " + std::to_string(item.objectDescriptionId);
                return false;
            }
        }
    }
    fixture.restoreAll();
    seed.members = fixture.snapshot().members;
    return true;
}

// `ruleset: {id, difficulty, progression, challenge_mode}`: the package's defaults with the named options changed.
bool readScenarioRuleset(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const YAML::Node &node,
    RulesetSelection &ruleset,
    RulesetDefinition &definition,
    std::vector<std::string> &failures)
{
    // Either "maw:hell:horizontal" (the --ruleset form) or a map of id, difficulty, progression and challenge_mode.
    const std::string text = node.IsScalar() ? node.as<std::string>() : std::string();
    const size_t separator = text.find(':');

    if (!node.IsScalar() && (!node.IsMap() || !node["id"] || !node["id"].IsScalar()))
    {
        failures.push_back(stepLocation(step) + ": field 'ruleset' needs a scalar 'id'");
        return false;
    }

    std::string error;
    const std::optional<RulesetDefinition> loaded = loadRulesetDefinition(
        context.assetFileSystem,
        node.IsScalar() ? text.substr(0, separator) : node["id"].as<std::string>(),
        error);

    if (!loaded)
    {
        failures.push_back(stepLocation(step) + ": " + error);
        return false;
    }

    definition = *loaded;
    ruleset.id = definition.id;
    ruleset.options = definition.defaultOptions();

    if (node.IsScalar())
    {
        if (separator != std::string::npos
            && !applyRulesetOptionIds(std::string_view(text).substr(separator + 1), ruleset.options))
        {
            failures.push_back(stepLocation(step) + ": unknown ruleset option in '" + text + "'");
            return false;
        }

        return true;
    }

    const auto readOption = [&](const char *pKey, auto parse, auto &value)
    {
        if (!node[pKey])
        {
            return true;
        }

        const auto parsed = node[pKey].IsScalar() ? parse(node[pKey].as<std::string>()) : std::nullopt;

        if (!parsed)
        {
            failures.push_back(stepLocation(step) + ": unknown ruleset " + pKey);
            return false;
        }

        value = *parsed;
        return true;
    };

    // friendly_fire: the player preference (MAW: hits on monsters not hostile to the party do nothing while off).
    // disintegration: Road to Insanity's and Beyond Madness's preference (on by default).
    if (node["disintegration"])
    {
        ruleset.options.preferences.disintegration = node["disintegration"].as<bool>();
    }

    if (node["friendly_fire"])
    {
        ruleset.options.preferences.friendlyFire = node["friendly_fire"].as<bool>();
    }

    // trainer_hints: the skill popups name the nearest teacher of the next mastery (off by default).
    if (node["trainer_hints"])
    {
        ruleset.options.preferences.trainerHints = node["trainer_hints"].as<bool>();
    }

    // bow_disabled: bows, crossbows, thrown weapons and dragon breath do not shoot (MAW's disableBow, off by default).
    if (node["bow_disabled"])
    {
        ruleset.options.preferences.bowDisabled = node["bow_disabled"].as<bool>();
    }

    // loot_filter: the loot filter's preset (off, soft, regular, strict, very_strict); loot_filter_ground: filtered
    // drops stay where they fell.
    if (node["loot_filter"])
    {
        const std::optional<RulesetLootFilterPreset> preset =
            parseRulesetLootFilterPreset(node["loot_filter"].as<std::string>());

        if (!preset)
        {
            failures.push_back(stepLocation(step) + ": unknown loot_filter " + node["loot_filter"].as<std::string>());
            return false;
        }

        ruleset.options.preferences.lootFilter = rulesetLootFilterWithPreset(
            *preset, node["loot_filter_ground"] && node["loot_filter_ground"].as<bool>());
    }

    if (!readOption("difficulty", parseRulesetDifficulty, ruleset.options.difficulty)
        || !readOption("progression", parseRulesetProgression, ruleset.options.progression)
        || !readOption("challenge_mode", parseRulesetChallengeMode, ruleset.options.challengeMode))
    {
        return false;
    }

    // A challenge mode's own difficulty and progression, as at new game.
    RulesetOptions &options = ruleset.options;
    options.difficulty = rulesetChallengeModeDifficulty(options.challengeMode).value_or(options.difficulty);
    options.progression = rulesetChallengeModeProgression(options.challengeMode).value_or(options.progression);
    return true;
}

bool assertRuleset(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["ruleset"];

    if (!node)
    {
        return true;
    }

    RulesetSelection expected;
    RulesetDefinition definition;

    if (!readScenarioRuleset(context, step, node, expected, definition, failures))
    {
        return false;
    }

    if (!context.runtimeDriver)
    {
        failures.push_back(stepLocation(step) + ": asserting the ruleset needs the runtime (faithful mode)");
        return false;
    }

    const RulesetSelection &actual = context.runtimeDriver->ruleset();

    const bool matches = node.IsScalar()
        ? actual == expected
        : actual.id == expected.id
            && (!node["difficulty"] || actual.options.difficulty == expected.options.difficulty)
            && (!node["progression"] || actual.options.progression == expected.options.progression)
            && (!node["challenge_mode"] || actual.options.challengeMode == expected.options.challengeMode)
            && (!node["bow_disabled"]
                || actual.options.preferences.bowDisabled == expected.options.preferences.bowDisabled);

    // map_cleared: the current map is cleared since its monsters last refilled; map_slain_min: at least this many of
    // its monsters count as slain for completion (the risen among them).
    if (node.IsMap() && (node["map_cleared"] || node["map_slain_min"]))
    {
        const MawRules *pMaw = context.runtimeDriver->mawRules();
        const IGameplayWorldRuntime *pWorld = std::as_const(*context.runtimeDriver).worldRuntime();
        MapKillProgress progress;

        if (pMaw == nullptr || pWorld == nullptr || !pWorld->mapKillProgress(progress))
        {
            failures.push_back(stepLocation(step) + ": map_cleared and map_slain_min need a MAW game on a map");
            return false;
        }

        std::string map = progress.mapFileName;
        std::transform(map.begin(), map.end(), map.begin(), [](unsigned char c) { return char(std::tolower(c)); });
        const bool cleared = pMaw->state().clearedSinceRefill.contains(map);
        std::cout << "ruleset map=" << map << " cleared=" << (cleared ? "true" : "false")
                  << " slain=" << progress.slainMonsters << "/" << progress.countedMonsters << '\n';

        if (node["map_cleared"] && cleared != node["map_cleared"].as<bool>())
        {
            failures.push_back(stepLocation(step) + ": expected the map " + (cleared ? "not cleared" : "cleared"));
            return false;
        }

        if (node["map_slain_min"] && progress.slainMonsters < node["map_slain_min"].as<int>())
        {
            failures.push_back(stepLocation(step) + ": only " + std::to_string(progress.slainMonsters)
                + " monsters count as slain");
            return false;
        }
    }

    // madness_pending, madness_deaths: Beyond Madness's death ledger (a run pending after a monster's hit, deaths).
    if (node.IsMap() && (node["madness_pending"] || node["madness_deaths"]))
    {
        const MawRules *pMaw = context.runtimeDriver->mawRules();

        if (pMaw == nullptr)
        {
            failures.push_back(stepLocation(step) + ": the Madness ledger needs a MAW game");
            return false;
        }

        const MawMadnessLedger &ledger = pMaw->madnessLedger();

        if (node["madness_pending"] && ledger.pending() != node["madness_pending"].as<bool>())
        {
            failures.push_back(stepLocation(step) + ": expected the Madness ledger "
                + (node["madness_pending"].as<bool>() ? "pending" : "not pending"));
            return false;
        }

        if (node["madness_deaths"] && ledger.deaths() != node["madness_deaths"].as<int>())
        {
            failures.push_back(stepLocation(step) + ": expected " + node["madness_deaths"].as<std::string>()
                + " Madness deaths, found " + std::to_string(ledger.deaths()));
            return false;
        }
    }

    // Items the ruleset rolled (a loot rarity on the item) in the party's packs; the report lists every pack item.
    if (node.IsMap() && (node["rolled_items_min"] || node["report_items"]) && context.runtimeDriver->party() != nullptr)
    {
        const Party &party = *context.runtimeDriver->party();
        size_t rolledItems = 0;

        for (const Character &member : party.members())
        {
            for (const InventoryItem &item : member.inventory)
            {
                rolledItems += item.rulesetFields.lootRarity != 0 ? 1 : 0;

                if (node["report_items"] && node["report_items"].as<bool>() && party.itemTable() != nullptr)
                {
                    const ItemDefinition *pDefinition = party.itemTable()->get(item.objectDescriptionId);
                    InventoryItem identified = item;
                    identified.identified = true;
                    std::cout << "ruleset item: "
                              << (pDefinition != nullptr
                                      ? ItemRuntime::displayName(identified, *pDefinition,
                                            party.standardItemEnchantTable(), party.specialItemEnchantTable())
                                      : std::string("?"))
                              << " rarity=" << int(item.rulesetFields.lootRarity)
                              << " power=" << item.rulesetFields.itemPower
                              << " drop_level=" << item.rulesetFields.dropLevel
                              << " enchant1=" << item.standardEnchantId << "/" << item.standardEnchantPower
                              << " enchant2=" << item.rulesetFields.secondStandardEnchantId << "/"
                              << item.rulesetFields.secondStandardEnchantPower
                              << " special=" << item.specialEnchantId
                              << " legendary=" << item.rulesetFields.legendaryAffixId << '\n';
                }
            }
        }

        if (node["rolled_items_min"] && rolledItems < node["rolled_items_min"].as<size_t>())
        {
            failures.push_back(stepLocation(step) + ": expected at least "
                + node["rolled_items_min"].as<std::string>() + " items the ruleset rolled, found "
                + std::to_string(rolledItems));
            return false;
        }
    }

    // member_classes: the members' classes in order (canonical names).
    if (node.IsMap() && node["member_classes"] && node["member_classes"].IsSequence()
        && context.runtimeDriver->party() != nullptr)
    {
        const Party &party = *context.runtimeDriver->party();
        const YAML::Node classes = node["member_classes"];

        for (size_t memberIndex = 0; memberIndex < classes.size(); ++memberIndex)
        {
            const std::string expected = classes[memberIndex].as<std::string>();
            const std::string actual = memberIndex < party.members().size()
                ? canonicalClassName(party.members()[memberIndex].className)
                : std::string("<none>");

            if (canonicalClassName(expected) != actual)
            {
                failures.push_back(stepLocation(step) + ": member " + std::to_string(memberIndex) + " is " + actual
                    + ", expected " + expected);
                return false;
            }
        }
    }

    // A dimension run: {map, power, affix_count, completed, min_family_actors (living actors of its families)}, or
    // {map, none: true}; the Dimensional Maps quest: {tier, given, cleared, done}.
    MawRules *pMawRules = context.runtimeDriver->mawRules();

    if (node.IsMap() && node["dimension_run"] && pMawRules != nullptr)
    {
        const YAML::Node run = node["dimension_run"];
        const MawDimensionRun *pRun = pMawRules->dimensionRun(run["map"].as<std::string>(""));
        std::string problem;

        if (run["none"].as<bool>(false))
        {
            problem = pRun != nullptr ? "a dimension run where none was expected" : "";
        }
        else if (pRun == nullptr)
        {
            problem = "no dimension run";
        }
        else
        {
            int familyActors = 0;
            const ScenarioRuntimeDriver &driver = *context.runtimeDriver;
            const IGameplayWorldRuntime *pWorld = driver.worldRuntime();

            for (size_t actorIndex = 0; pWorld != nullptr && actorIndex < pWorld->mapActorCount(); ++actorIndex)
            {
                GameplayRuntimeActorState state = {};

                if (pWorld->actorRuntimeState(actorIndex, state) && !state.isDead
                    && std::any_of(pRun->families.begin(), pRun->families.end(),
                        [&state](int16_t family) { return (state.monsterId - 1) / 3 == (family - 1) / 3; }))
                {
                    ++familyActors;
                }
            }

            if (run["power"] && int(pRun->power) != run["power"].as<int>())
            {
                problem = "power " + std::to_string(pRun->power);
            }
            else if (run["affix_count"] && pRun->affixCount() != run["affix_count"].as<int>())
            {
                problem = std::to_string(pRun->affixCount()) + " affixes";
            }
            else if (run["completed"] && pRun->completed != run["completed"].as<bool>())
            {
                problem = pRun->completed ? "completed" : "not completed";
            }
            else if (run["min_family_actors"] && familyActors < run["min_family_actors"].as<int>())
            {
                problem = std::to_string(familyActors) + " living actors of its families";
            }
        }

        if (!problem.empty())
        {
            failures.push_back(stepLocation(step) + ": dimension run: " + problem);
            return false;
        }
    }

    if (node.IsMap() && node["dimension_quest"] && pMawRules != nullptr)
    {
        const YAML::Node quest = node["dimension_quest"];
        const MawDimensionQuest &state = pMawRules->state().dimensionQuest;
        const bool matches = (!quest["tier"] || state.tierLevel == quest["tier"].as<int>())
            && (!quest["given"] || state.mapGiven == quest["given"].as<bool>())
            && (!quest["cleared"] || state.cleared == quest["cleared"].as<bool>())
            && (!quest["done"] || state.done == quest["done"].as<bool>());

        if (!matches)
        {
            failures.push_back(stepLocation(step) + ": Dimensional Maps quest at tier "
                + std::to_string(state.tierLevel) + (state.mapGiven ? ", map given" : "")
                + (state.cleared ? ", cleared" : "") + (state.done ? ", done" : ""));
            return false;
        }
    }

    // Items crafted on (packs and worn) and the potion effects running on the members.
    if (node.IsMap() && (node["crafted_items_min"] || node["potion_effects_min"] || node["potion_effects_max"])
        && context.runtimeDriver->party() != nullptr)
    {
        const Party &party = *context.runtimeDriver->party();
        size_t craftedItems = 0;
        size_t potionEffects = 0;

        for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
        {
            const Character &member = party.members()[memberIndex];
            potionEffects += member.rulesetState.potionEffects.size() + member.rulesetState.potionSteps.size();

            for (const InventoryItem &item : member.inventory)
            {
                craftedItems += item.rulesetFields.craftCount > 0 ? 1 : 0;
            }

            for (int slot = 0; slot <= int(EquipmentSlot::Ring6); ++slot)
            {
                const std::optional<InventoryItem> worn = party.equippedItem(memberIndex, EquipmentSlot(slot));
                craftedItems += worn && worn->rulesetFields.craftCount > 0 ? 1 : 0;
            }
        }

        if (node["crafted_items_min"] && craftedItems < node["crafted_items_min"].as<size_t>())
        {
            failures.push_back(stepLocation(step) + ": expected at least "
                + node["crafted_items_min"].as<std::string>() + " crafted items, found "
                + std::to_string(craftedItems));
            return false;
        }

        if (node["potion_effects_max"] && potionEffects > node["potion_effects_max"].as<size_t>())
        {
            failures.push_back(stepLocation(step) + ": expected at most "
                + node["potion_effects_max"].as<std::string>() + " potion effects, found "
                + std::to_string(potionEffects));
            return false;
        }

        if (node["potion_effects_min"] && potionEffects < node["potion_effects_min"].as<size_t>())
        {
            failures.push_back(stepLocation(step) + ": expected at least "
                + node["potion_effects_min"].as<std::string>() + " potion effects, found "
                + std::to_string(potionEffects));
            return false;
        }
    }

    if (!matches)
    {
        failures.push_back(
            stepLocation(step) + ": expected ruleset " + expected.id + " "
            + std::string(rulesetDifficultyId(expected.options.difficulty)) + " "
            + std::string(rulesetProgressionId(expected.options.progression)) + ", found " + actual.id + " "
            + std::string(rulesetDifficultyId(actual.options.difficulty)) + " "
            + std::string(rulesetProgressionId(actual.options.progression)));
        return false;
    }

    return true;
}

bool runNewGameFlow(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    std::string continent;

    if (!readScalarString(step, "continent", continent, failures, false))
    {
        return false;
    }

    RulesetSelection ruleset;
    RulesetDefinition rulesetDefinition = standardRulesetDefinition();

    if (step.payload["ruleset"]
        && !readScenarioRuleset(context, step, step.payload["ruleset"], ruleset, rulesetDefinition, failures))
    {
        return false;
    }

    if (context.gameDataLoader.activeRuleset().id != ruleset.id)
    {
        context.gameDataLoader.setActiveRuleset(rulesetDefinition);
        context.gameDataLoaded = false;
    }

    if (!ensureGameDataLoaded(context, failures))
    {
        return false;
    }

    std::string startMap = "oute3.odm";

    if (!readScalarString(step, "start_map", startMap, failures, false))
    {
        return false;
    }

    PartySeed seed = Party::createDefaultSeed();
    const bool hasExplicitParty = bool(step.payload["party"]);
    if (hasExplicitParty)
    {
        std::string failure;
        if (!readScenarioPartySeed(context, step.payload["party"], seed, failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return false;
        }
        scenarioLog(context, ScenarioLogColor::Cyan, "PARTY explicit fixture members="
            + std::to_string(seed.members.size()) + " gold=" + std::to_string(seed.gold));
        for (const Character &member : seed.members)
        {
            scenarioLog(context, ScenarioLogColor::Cyan, "PARTY fixture name=" + member.name
                + " class=" + member.className + " level=" + std::to_string(member.level)
                + " hp=" + std::to_string(member.health) + "/" + std::to_string(member.maxHealth)
                + " sp=" + std::to_string(member.spellPoints) + "/" + std::to_string(member.maxSpellPoints)
                + " skills=" + std::to_string(member.skills.size()));
        }
    }

    if (context.mode == ScenarioMode::Faithful)
    {
        if (!ensureRuntimeDriver(context, failures))
        {
            return context.mode != ScenarioMode::Faithful;
        }

        std::string failure;
        if (!context.runtimeDriver->startNewGame(
                0, startMap, failure, hasExplicitParty ? &seed : nullptr, ruleset))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return context.mode != ScenarioMode::Faithful;
        }
    }

    if (step.payload["member_count"] && step.payload["member_count"].IsScalar())
    {
        const size_t memberCount = step.payload["member_count"].as<size_t>();
        if (memberCount > 0 && memberCount < seed.members.size())
        {
            seed.members.resize(memberCount);
        }
    }
    context.party.seed(seed);

    if (!loadMap(context, startMap, failures))
    {
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

bool runLoadMap(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    std::string mapFileName;

    if (!readScalarString(step, "map", mapFileName, failures, true))
    {
        return false;
    }

    const size_t failureCountBeforePose = failures.size();
    const std::optional<ScenarioPose> poseOverride = readLoadMapPoseOverride(step, mapFileName, failures);
    if (failures.size() != failureCountBeforePose)
    {
        return false;
    }
    const bool needsRuntimePose = poseOverride.has_value();

    if (context.mode == ScenarioMode::Faithful || context.runtimeDriver || needsRuntimePose)
    {
        if (!ensureRuntimeDriver(context, failures))
        {
            return context.mode != ScenarioMode::Faithful;
        }

        context.runtimeDriver->setGameMinutes(context.gameMinutes);

        std::string failure;
        if (!context.runtimeDriver->loadMap(mapFileName, failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return context.mode != ScenarioMode::Faithful;
        }

        if (poseOverride.has_value() && !context.runtimeDriver->setPose(*poseOverride, failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return context.mode != ScenarioMode::Faithful;
        }
    }

    if (!loadMap(context, mapFileName, failures))
    {
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

bool runTravel(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    std::string mapFileName;

    if (!readScalarString(step, "map", mapFileName, failures, true))
    {
        return false;
    }

    if (mapFileName == "TODO")
    {
        failures.push_back(stepLocation(step) + ": travel map is TODO");
        return false;
    }

    float travelMinutes = 2.0f * 24.0f * 60.0f;

    if (step.payload["days"] && step.payload["days"].IsScalar())
    {
        travelMinutes = step.payload["days"].as<float>() * 24.0f * 60.0f;
    }
    else if (step.payload["travel_days"] && step.payload["travel_days"].IsScalar())
    {
        travelMinutes = step.payload["travel_days"].as<float>() * 24.0f * 60.0f;
    }

    context.gameMinutes += travelMinutes;

    if (context.mode == ScenarioMode::Faithful || context.runtimeDriver)
    {
        if (!ensureRuntimeDriver(context, failures))
        {
            return context.mode != ScenarioMode::Faithful;
        }

        std::string failure;
        if (!context.runtimeDriver->travelDays(travelMinutes / (24.0f * 60.0f), failure)
            || !context.runtimeDriver->loadMap(mapFileName, failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return context.mode != ScenarioMode::Faithful;
        }
    }

    if (!loadMap(context, mapFileName, failures))
    {
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

bool runNoOpObservation(
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!step.payload)
    {
        failures.push_back(stepLocation(step) + ": step payload is missing");
        return false;
    }

    return true;
}

// An actor_index field: a map actor index, or "last" for the map's last actor (one spawn_actor just summoned) and
// "last-N" for the one N before it.
size_t scenarioActorIndex(ScenarioExecutionContext &context, const YAML::Node &node)
{
    const std::string text = node.as<std::string>("");

    if (text.rfind("last", 0) == 0)
    {
        const size_t actorCount = context.runtimeDriver ? context.runtimeDriver->mapActorCount() : 0;
        const size_t back = text.size() > 5 && text[4] == '-' ? std::stoul(text.substr(5)) : 0;
        return actorCount > back ? actorCount - 1 - back : static_cast<size_t>(-1);
    }

    return node.as<size_t>();
}

// set_ruleset: {options: "easy"}: changes the game's ruleset options mid-game, as the pause menu's Rules tab does
// (colon-separated option ids; what the ruleset locks fails the step).
bool runSetRuleset(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    if (!step.payload["options"] || !step.payload["options"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": set_ruleset requires scalar field 'options'");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    std::string failure;

    if (!context.runtimeDriver->setRulesetOptions(step.payload["options"].as<std::string>(), failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

// damage_actor: {actor_index, amount, tier, expect}: a party hit through the normal damage path (the actor turns on the
// party), for combat scenarios on maps whose actors are friendly. tier (default physical): what the hit is to an energy
// shield, physical, classic_blaster, kreegan_energy or spell. `all: true` instead of `actor_index` hits every living
// actor, again until none lives (monsters summoned meanwhile count), for clearing a whole map. expect: refused passes
// when the hit does nothing.
bool runDamageActor(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    const bool all = step.payload["all"].as<bool>(false);

    if (!all && (!step.payload["actor_index"] || !step.payload["actor_index"].IsScalar()))
    {
        failures.push_back(stepLocation(step) + ": damage_actor requires scalar field 'actor_index' or all: true");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    const std::optional<ShieldAttackTier> shieldTier =
        parseShieldAttackTier(step.payload["tier"].as<std::string>("physical"));

    if (!shieldTier)
    {
        failures.push_back(stepLocation(step) + ": damage_actor tier must be physical, classic_blaster, "
            "kreegan_energy or spell");
        return false;
    }

    seedRuntimeDriverFromContext(context);
    std::string failure;

    if (all)
    {
        constexpr int MaximumPasses = 10;
        bool anyHit = true;

        for (int pass = 0; pass < MaximumPasses && anyHit; ++pass)
        {
            anyHit = false;

            for (size_t actorIndex = 0; actorIndex < context.runtimeDriver->mapActorCount(); ++actorIndex)
            {
                std::string ignored;
                anyHit = context.runtimeDriver->damageActor(
                             actorIndex, step.payload["amount"].as<int>(1), *shieldTier, ignored)
                    || anyHit;
            }
        }

        syncContextFromRuntime(context);
        return true;
    }

    const bool applied = context.runtimeDriver->damageActor(scenarioActorIndex(context, step.payload["actor_index"]),
        step.payload["amount"].as<int>(1), *shieldTier, failure);

    // expect: refused checks that the hit did nothing (MAW's friendly-fire preference).
    if (step.payload["expect"].as<std::string>("applied") == "refused")
    {
        if (applied)
        {
            failures.push_back(stepLocation(step) + ": damage_actor was expected to be refused but was applied");
            return false;
        }

        syncContextFromRuntime(context);
        return true;
    }

    if (!applied)
    {
        // skip_dead: an actor already dead (or gone) is no failure, for clearing a whole map.
        if (step.payload["skip_dead"].as<bool>(false))
        {
            return true;
        }

        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

std::optional<CharacterCondition> parseScenarioCondition(const std::string &name)
{
    static const std::array<std::pair<const char *, CharacterCondition>, 18> Conditions = {{
        {"cursed", CharacterCondition::Cursed}, {"weak", CharacterCondition::Weak},
        {"asleep", CharacterCondition::Asleep}, {"fear", CharacterCondition::Fear},
        {"drunk", CharacterCondition::Drunk}, {"insane", CharacterCondition::Insane},
        {"poison_weak", CharacterCondition::PoisonWeak}, {"disease_weak", CharacterCondition::DiseaseWeak},
        {"poison_medium", CharacterCondition::PoisonMedium}, {"disease_medium", CharacterCondition::DiseaseMedium},
        {"poison_severe", CharacterCondition::PoisonSevere}, {"disease_severe", CharacterCondition::DiseaseSevere},
        {"paralyzed", CharacterCondition::Paralyzed}, {"unconscious", CharacterCondition::Unconscious},
        {"dead", CharacterCondition::Dead}, {"petrified", CharacterCondition::Petrified},
        {"eradicated", CharacterCondition::Eradicated}, {"zombie", CharacterCondition::Zombie},
    }};

    for (const auto &[pName, condition] : Conditions)
    {
        if (name == pName)
        {
            return condition;
        }
    }

    return std::nullopt;
}

// party_attack: {actor_index, member_index, count, conditions, record, ratio_to, damage_ratio, recovery_ratio,
// min_hit_rate, max_hit_rate, min_average, max_average, attack_spell, min_weapon_attacks, max_weapon_attacks, report}:
// the member's real attacks (count, default 100) on the actor, healed after each, under the given conditions.
// attack_spell sets the member's attack spell for them and casts it for real; weapon attacks counts the swings and
// shots (an attack spell cast is none). record keeps the result by name; ratio_to compares this
// one's average damage (damage_ratio: [min, max]), HP taken (applied_ratio) and recovery (recovery_ratio) with a
// recorded one.
bool runPartyAttack(ScenarioExecutionContext &context, const ScenarioStep &step, std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    ScenarioPartyAttackRequest request;
    request.actorIndex = scenarioActorIndex(context, step.payload["actor_index"]);
    request.memberIndex = step.payload["member_index"].as<size_t>(0);
    request.count = step.payload["count"].as<int>(100);

    if (step.payload["attack_spell"])
    {
        request.attackSpell = step.payload["attack_spell"].as<std::string>();
    }

    for (const YAML::Node &name : step.payload["conditions"])
    {
        const std::optional<CharacterCondition> condition = parseScenarioCondition(name.as<std::string>());

        if (!condition)
        {
            failures.push_back(stepLocation(step) + ": party_attack: unknown condition '" + name.as<std::string>()
                + "'");
            return false;
        }

        request.conditions.push_back(*condition);
    }

    seedRuntimeDriverFromContext(context);
    ScenarioPartyAttackResult result;
    std::string failure;

    if (!context.runtimeDriver->partyAttack(request, result, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    const double hitRate = double(result.hits) / std::max(1, result.attacks);

    if (step.payload["report"].as<bool>(false))
    {
        std::cout << "party_attack report: attacks=" << result.attacks << " hits=" << result.hits
                  << " crits=" << result.criticals << " weapon_attacks=" << result.weaponAttacks
                  << " average_damage=" << result.averageDamage
                  << " average_applied=" << result.averageAppliedDamage
                  << " average_recovery=" << result.averageRecoverySeconds << "\n";
    }

    bool ok = true;
    const auto expectRange = [&](const char *pName, double value, double low, double high)
    {
        if (value < low || value > high)
        {
            failures.push_back(stepLocation(step) + ": party_attack " + pName + " " + std::to_string(value)
                + " outside [" + std::to_string(low) + ", " + std::to_string(high) + "]");
            ok = false;
        }
    };

    expectRange("hit rate", hitRate, step.payload["min_hit_rate"].as<double>(0),
        step.payload["max_hit_rate"].as<double>(1));
    expectRange("average damage", result.averageDamage, step.payload["min_average"].as<double>(0),
        step.payload["max_average"].as<double>(1e12));
    expectRange("weapon attacks", result.weaponAttacks, step.payload["min_weapon_attacks"].as<double>(0),
        step.payload["max_weapon_attacks"].as<double>(1e12));

    if (step.payload["ratio_to"])
    {
        const auto recorded = context.attackRecords.find(step.payload["ratio_to"].as<std::string>());

        if (recorded == context.attackRecords.end())
        {
            failures.push_back(stepLocation(step) + ": party_attack ratio_to names no recorded attack");
            return false;
        }

        if (const YAML::Node range = step.payload["damage_ratio"])
        {
            expectRange("damage ratio", result.averageDamage / std::max(1e-9, recorded->second.averageDamage),
                range[0].as<double>(), range[1].as<double>());
        }

        if (const YAML::Node range = step.payload["applied_ratio"])
        {
            expectRange("applied damage ratio",
                result.averageAppliedDamage / std::max(1e-9, recorded->second.averageAppliedDamage),
                range[0].as<double>(), range[1].as<double>());
        }

        if (const YAML::Node range = step.payload["recovery_ratio"])
        {
            expectRange("recovery ratio",
                result.averageRecoverySeconds / std::max(1e-9, recorded->second.averageRecoverySeconds),
                range[0].as<double>(), range[1].as<double>());
        }
    }

    if (step.payload["record"])
    {
        context.attackRecords[step.payload["record"].as<std::string>()] = result;
    }

    return ok;
}

// expect: applied (default) or refused, for use_item, craft and combine_gems.
bool checkExpectedOutcome(
    const ScenarioStep &step,
    const char *pStepName,
    bool applied,
    std::vector<std::string> &failures)
{
    const std::string expected = step.payload["expect"].as<std::string>("applied");

    if (expected != "applied" && expected != "refused")
    {
        failures.push_back(stepLocation(step) + ": " + pStepName + " expect must be applied or refused");
        return false;
    }

    if (applied != (expected == "applied"))
    {
        failures.push_back(stepLocation(step) + ": " + pStepName + " was expected to be " + expected + " but was "
            + (applied ? "applied" : "refused"));
        return false;
    }

    return true;
}

// grant_item: {item_id, count, member_index, power, state, enchant: [id, power], second_enchant: [id, power],
// special, rarity, drop_level, item_power, charges, identified (default true), equip: slot, roll_level, boss, seed}: a
// made-up item put into a member's pack, or worn with `equip` (crafting materials, potions of a power, enchanted
// equipment). `roll_level` rolls its enchantments as the party's rules roll loot of that level (`boss` for a boss's);
// `legendary` sets its legendary affix.
bool runGrantItem(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    const Party *pParty = context.runtimeDriver->party();
    const uint32_t itemId = step.payload["item_id"].as<uint32_t>(0);

    if (pParty == nullptr || pParty->itemTable() == nullptr || pParty->itemTable()->get(itemId) == nullptr)
    {
        failures.push_back(stepLocation(step) + ": grant_item needs a known item_id");
        return false;
    }

    InventoryItem item = ItemGenerator::makeInventoryItem(itemId, *pParty->itemTable(), ItemGenerationMode::Generic);
    item.standardEnchantPower = step.payload["power"].as<uint16_t>(item.standardEnchantPower);
    item.rulesetFields.craftState = step.payload["state"].as<uint16_t>(0);
    item.identified = step.payload["identified"].as<bool>(true);
    item.currentCharges = step.payload["charges"].as<uint16_t>(item.currentCharges);
    item.specialEnchantId = step.payload["special"].as<uint16_t>(item.specialEnchantId);
    item.rulesetFields.lootRarity = step.payload["rarity"].as<uint8_t>(item.rulesetFields.lootRarity);
    item.rulesetFields.dropLevel = step.payload["drop_level"].as<uint16_t>(item.rulesetFields.dropLevel);
    item.rulesetFields.itemPower = step.payload["item_power"].as<uint16_t>(item.rulesetFields.itemPower);
    item.rulesetFields.legendaryAffixId =
        step.payload["legendary"].as<uint16_t>(item.rulesetFields.legendaryAffixId);

    if (const YAML::Node enchant = step.payload["enchant"]; enchant && enchant.IsSequence() && enchant.size() == 2)
    {
        item.standardEnchantId = enchant[0].as<uint16_t>();
        item.standardEnchantPower = enchant[1].as<uint16_t>();
    }

    if (const YAML::Node enchant = step.payload["second_enchant"];
        enchant && enchant.IsSequence() && enchant.size() == 2)
    {
        item.rulesetFields.secondStandardEnchantId = enchant[0].as<uint16_t>();
        item.rulesetFields.secondStandardEnchantPower = enchant[1].as<uint16_t>();
    }

    // A dimension map (MAW): {map_id, affixes: [four ids, 0 empty], active: slots (0 all), power}.
    if (const YAML::Node map = step.payload["dimension_map"]; map && map.IsMap())
    {
        item.rulesetFields.dimensionMapId = map["map_id"].as<uint16_t>(0);
        item.rulesetFields.dimensionActiveSlots = uint8_t(map["active"].as<int>(0));
        item.rulesetFields.dimensionPower = uint8_t(map["power"].as<int>(0));

        for (size_t slot = 0; slot < 4 && map["affixes"] && slot < map["affixes"].size(); ++slot)
        {
            item.rulesetFields.dimensionAffixes[slot] = uint8_t(map["affixes"][slot].as<int>());
        }
    }

    if (step.payload["roll_level"])
    {
        const ItemDefinition &definition = *pParty->itemTable()->get(itemId);

        if (pParty->standardItemEnchantTable() == nullptr || pParty->specialItemEnchantTable() == nullptr)
        {
            failures.push_back(stepLocation(step) + ": grant_item roll_level needs the enchantment tables");
            return false;
        }

        ItemGenerationRequest request;
        request.treasureLevel = 6;
        request.allowRareItems = false;
        request.dropLevel = step.payload["roll_level"].as<int>();
        request.boss = step.payload["boss"].as<bool>(false);
        std::mt19937 rng(step.payload["seed"].as<uint32_t>(itemId));
        gameRulesFor(pParty).items.rollEnchantments(item, definition,
            {*pParty->itemTable(), *pParty->standardItemEnchantTable(), *pParty->specialItemEnchantTable()}, request,
            nullptr, rng);
        item.identified = true;
    }

    std::optional<EquipmentSlot> equipSlot;

    if (step.payload["equip"])
    {
        equipSlot = parseScenarioEquipmentSlot(step.payload["equip"].as<std::string>());

        if (!equipSlot)
        {
            failures.push_back(stepLocation(step) + ": unknown equip slot");
            return false;
        }
    }

    seedRuntimeDriverFromContext(context);
    std::string failure;

    if (!context.runtimeDriver->grantItem(step.payload["member_index"].as<size_t>(0), item,
            step.payload["count"].as<uint32_t>(1), equipSlot, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

// ruleset_banks: {mm8, mm7, mm6, other}: the levels a MAW game has banked in each world, which size its monsters (as
// the console's `ruleset banks`); for parties made at a high level.
bool runRulesetBanks(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    const std::array<double, 4> levels = {step.payload["mm8"].as<double>(0), step.payload["mm7"].as<double>(0),
        step.payload["mm6"].as<double>(0), step.payload["mm9"].as<double>(0)};
    std::string failure;

    if (!context.runtimeDriver->setRulesetBanks(levels, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    // Maps completed (by file name), and the Dimensional Maps quest done, for dimension maps.
    MawRules *pMawRules = context.runtimeDriver->mawRules();

    for (const YAML::Node &map : step.payload["completed_maps"])
    {
        std::string fileName = map.as<std::string>();
        std::transform(fileName.begin(), fileName.end(), fileName.begin(),
            [](unsigned char character) { return char(std::tolower(character)); });
        pMawRules->state().completedMaps.insert(fileName);
    }

    if (step.payload["dimension_quest_done"])
    {
        pMawRules->state().dimensionQuest.done = step.payload["dimension_quest_done"].as<bool>();
    }

    return true;
}

// console: {line, expect_contains}: runs a debug console line in the game as typed (`testparty apply mid newclasses`);
// fails when the console reports an error, or its output lacks expect_contains.
bool runConsoleCommand(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    const std::string line = step.payload["line"].as<std::string>("");
    std::string output;
    std::string failure;
    seedRuntimeDriverFromContext(context);

    if (!context.runtimeDriver->runConsoleLine(line, output, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    std::cout << "CONSOLE " << line << ": " << output << '\n';
    const std::string expected = step.payload["expect_contains"].as<std::string>("");

    if (!expected.empty() && output.find(expected) == std::string::npos)
    {
        failures.push_back(stepLocation(step) + ": console output lacks \"" + expected + "\": " + output);
        return false;
    }

    return true;
}

// walk_to: {x, y, z | to: pose, via: [poses], radius, timeout_seconds, clear_hostiles, expect_map, plan, node_limit,
// close_dialogs, expect: arrived|dialog}: the party walks there with the movement keys (ScenarioRuntimeDriver::walkTo)
// and the trail is printed as the run's evidence.
bool runWalkTo(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    ScenarioWalkRequest request = {};
    const YAML::Node via = step.payload["via"];

    if (via && via.IsSequence())
    {
        for (const YAML::Node &point : via)
        {
            if (point.IsSequence() && point.size() >= 3)
            {
                ScenarioPose pose = {};
                pose.x = point[0].as<float>();
                pose.y = point[1].as<float>();
                pose.z = point[2].as<float>();
                request.points.push_back(pose);
                continue;
            }

            const std::optional<ScenarioPose> pose = readScenarioPoseNode(step, point, "via", failures, true);

            if (!pose)
            {
                return false;
            }

            request.points.push_back(*pose);
        }
    }

    const std::optional<ScenarioPose> target = step.payload["to"]
        ? readScenarioPoseNode(step, step.payload["to"], "to", failures, true)
        : readScenarioPoseNode(step, step.payload, "walk_to", failures, !step.payload["expect_map"]);

    if (target)
    {
        request.points.push_back(*target);
    }
    else if (!step.payload["expect_map"] || request.points.empty())
    {
        if (failures.empty())
        {
            failures.push_back(stepLocation(step) + ": walk_to needs a target (x, y, z or to) or via and expect_map");
        }
        return false;
    }

    request.arriveRadius = step.payload["radius"].as<float>(request.arriveRadius);
    if (step.payload["z_tolerance"])
    {
        request.zTolerance = step.payload["z_tolerance"].as<float>();
    }
    request.timeoutSeconds = step.payload["timeout_seconds"].as<float>(request.timeoutSeconds);
    request.clearHostilesRadius = step.payload["clear_hostiles"].as<float>(0.0f);
    request.expectMap = step.payload["expect_map"].as<std::string>("");
    request.plan = step.payload["plan"].as<bool>(true);
    request.nodeLimit = step.payload["node_limit"].as<size_t>(request.nodeLimit);
    request.closeDialogs = step.payload["close_dialogs"].as<bool>(false);
    const std::string expect = lowerAscii(step.payload["expect"].as<std::string>("arrived"));

    if (expect != "arrived" && expect != "dialog")
    {
        failures.push_back(stepLocation(step) + ": walk_to expect must be arrived or dialog");
        return false;
    }

    ScenarioWalkResult result = {};
    std::string failure;
    const bool walked = context.runtimeDriver->walkTo(request, result, failure);
    syncContextFromRuntime(context);

    for (const std::string &line : result.trail)
    {
        std::cout << "WALK " << line << '\n';
    }

    std::cout << "WALK done arrived=" << (result.arrived ? "true" : "false")
              << " dialog=" << (result.dialogOpened ? "true" : "false") << " seconds=" << scenarioFloat(result.seconds)
              << " replans=" << result.replans << " jumps=" << result.jumps << " clicks=" << result.clicks
              << " killed=" << result.hostilesKilled
              << " closed_dialogs=" << result.closedDialogs << '\n';

    if (!walked)
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    if (expect == "arrived" && !result.arrived)
    {
        failures.push_back(stepLocation(step) + ": walk_to stopped before arriving (a dialogue opened)");
        return false;
    }

    if (expect == "dialog" && !result.dialogOpened)
    {
        failures.push_back(stepLocation(step) + ": walk_to arrived but expected a dialogue on the way");
        return false;
    }

    return true;
}

// play_lua: {source, max_seconds}: a player's reasoning over a puzzle or a game, in Lua, run in the scenario (not as a
// map event), so it may wait and react: click(event_id) runs the map event a click on its prop runs; wait(seconds)
// lets the world run; status() returns the status lines shown since the last call (" | " between them); qbit(id),
// has_item(item_id) and mapvar(name) read the state; held() is the item on the cursor (0: none), item_count(item_id) the packs' count of it and pack_items() every pack item ("id x count"), discard(item_id) drops one from the packs (a player making room), door_state(id) is a door's state (as seen);
// take_chest() presses the open chest's Take All and close() Escape
// (false when nothing was open); log(text) prints. A script should decide only from what the
// player sees (status lines, its own keys and items); mapvar is for checks. A Lua error or error() fails the step.
struct ScenarioPlayContext
{
    ScenarioExecutionContext *pContext = nullptr;
    float waited = 0.0f;
    float maxSeconds = 600.0f;
    size_t statusIndex = 0;
};

ScenarioPlayContext &scenarioPlayContext(lua_State *pLuaState)
{
    return *static_cast<ScenarioPlayContext *>(lua_touserdata(pLuaState, lua_upvalueindex(1)));
}

int scenarioPlayClick(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const lua_Integer eventId = luaL_checkinteger(pLuaState, 1);
    std::string failure;

    // A talk that greets the party meanwhile (a found-player talk, again after a load) is closed first, as a player
    // closes it before clicking on.
    for (int dismissed = 0; dismissed < 3 && !play.pContext->runtimeDriver->saveBlockedReason().empty(); ++dismissed)
    {
        if (!play.pContext->runtimeDriver->advanceRuntime(0.05f, failure, true))
        {
            break;
        }

        const ScenarioDialogSnapshot dialog = play.pContext->runtimeDriver->activeDialogSnapshot();

        if (!dialog.active)
        {
            break;
        }

        std::cout << "PLAY dismissed \"" << dialog.title << "\" before click(" << eventId << ")\n";
        play.pContext->runtimeDriver->closeDialog(failure);
    }

    if (!play.pContext->runtimeDriver->executeMapEvent(uint16_t(eventId), failure))
    {
        const std::string blocked = play.pContext->runtimeDriver->saveBlockedReason();
        return luaL_error(pLuaState, "click(%d): %s%s", int(eventId), failure.c_str(),
            blocked.empty() ? "" : (" (" + blocked + ")").c_str());
    }

    return 0;
}

int scenarioPlayWait(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const float seconds = float(luaL_checknumber(pLuaState, 1));
    play.waited += seconds;

    if (play.waited > play.maxSeconds)
    {
        return luaL_error(pLuaState, "the script waited longer than max_seconds (%d)", int(play.maxSeconds));
    }

    std::string failure;

    if (!play.pContext->runtimeDriver->advanceRuntime(seconds, failure))
    {
        return luaL_error(pLuaState, "wait: %s", failure.c_str());
    }

    return 0;
}

int scenarioPlayStatus(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const EventRuntimeState *pState = play.pContext->runtimeDriver->eventRuntimeState();
    std::string text;

    if (pState != nullptr)
    {
        if (play.statusIndex > pState->statusMessages.size())
        {
            play.statusIndex = 0;
        }

        for (size_t index = play.statusIndex; index < pState->statusMessages.size(); ++index)
        {
            text += (text.empty() ? "" : " | ") + pState->statusMessages[index];
        }

        play.statusIndex = pState->statusMessages.size();
    }

    lua_pushstring(pLuaState, text.c_str());
    return 1;
}

int scenarioPlayQBit(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const Party *pParty = play.pContext->runtimeDriver->party();
    lua_pushboolean(pLuaState, pParty != nullptr && pParty->hasQuestBit(uint32_t(luaL_checkinteger(pLuaState, 1))));
    return 1;
}

int scenarioPlayHasItem(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const Party *pParty = play.pContext->runtimeDriver->party();
    lua_pushboolean(pLuaState,
        pParty != nullptr && pParty->hasItemAnywhere(uint32_t(luaL_checkinteger(pLuaState, 1))));
    return 1;
}

int scenarioPlayMapVar(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const EventRuntimeState *pState = play.pContext->runtimeDriver->eventRuntimeState();
    const std::string name = luaL_checkstring(pLuaState, 1);
    lua_Integer value = 0;

    if (pState != nullptr)
    {
        const auto iterator = pState->namedMapVars.find(name);
        value = iterator != pState->namedMapVars.end() ? iterator->second : 0;
    }

    lua_pushinteger(pLuaState, value);
    return 1;
}

// The party members' class names in order, separated by spaces ("Knight Cleric Thief Sorcerer").
int scenarioPlayClasses(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const Party *pParty = play.pContext->runtimeDriver->party();
    std::string text;

    if (pParty != nullptr)
    {
        for (const Character &member : pParty->members())
        {
            text += (text.empty() ? "" : " ") + member.className;
        }
    }

    lua_pushstring(pLuaState, text.c_str());
    return 1;
}

// The party for a log line: the active member's index, then each member's name, actual Might, recovery and condition
// bits.
int scenarioPlayParty(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const Party *pParty = play.pContext->runtimeDriver->party();
    std::string text;

    if (pParty != nullptr)
    {
        text = "active " + std::to_string(pParty->activeMemberIndex()) + ":";

        for (const Character &member : pParty->members())
        {
            const int might = GameMechanics::resolveCharacterDisplayedActualPrimaryStat(
                member,
                uint32_t(EvtVariable::ActualMight),
                pParty->itemTable(),
                pParty->standardItemEnchantTable(),
                pParty->specialItemEnchantTable());
            text += " " + member.name + " (might " + std::to_string(might) + ", recovery "
                + scenarioFloat(member.recoverySecondsRemaining) + " s, conditions " + member.conditions.to_string()
                + ")";
        }
    }

    lua_pushstring(pLuaState, text.c_str());
    return 1;
}

// A party member's conditions (index from 0), space-separated names ("Weak Insane"; "" when none).
int scenarioPlayConditions(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const Party *pParty = play.pContext->runtimeDriver->party();
    const Character *pMember = pParty != nullptr ? pParty->member(size_t(luaL_checkinteger(pLuaState, 1))) : nullptr;
    std::string text;

    if (pMember != nullptr)
    {
        for (const auto &[pName, condition] : CharacterConditionNames)
        {
            if (pMember->conditions.test(size_t(condition)))
            {
                text += (text.empty() ? "" : " ") + std::string(pName);
            }
        }
    }

    lua_pushstring(pLuaState, text.c_str());
    return 1;
}

// The party's gold.
int scenarioPlayGold(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const Party *pParty = play.pContext->runtimeDriver->party();
    lua_pushinteger(pLuaState, pParty != nullptr ? lua_Integer(pParty->gold()) : 0);
    return 1;
}

// remember(key, value) keeps a value (as text) for later play_lua steps of the run; recall(key) gives it back (nil:
// never remembered). Numbers come back as numbers.
int scenarioPlayRemember(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const std::string key = luaL_checkstring(pLuaState, 1);
    play.pContext->playMemory[key] = luaL_tolstring(pLuaState, 2, nullptr);
    return 0;
}

int scenarioPlayRecall(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const auto iterator = play.pContext->playMemory.find(luaL_checkstring(pLuaState, 1));

    if (iterator == play.pContext->playMemory.end())
    {
        lua_pushnil(pLuaState);
    }
    else if (lua_stringtonumber(pLuaState, iterator->second.c_str()) == 0)
    {
        lua_pushstring(pLuaState, iterator->second.c_str());
    }

    return 1;
}

// A party member's experience (index from 0).
int scenarioPlayExperience(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const Party *pParty = play.pContext->runtimeDriver->party();
    const Character *pMember = pParty != nullptr ? pParty->member(size_t(luaL_checkinteger(pLuaState, 1))) : nullptr;
    lua_pushinteger(pLuaState, pMember != nullptr ? lua_Integer(pMember->experience) : 0);
    return 1;
}

int scenarioPlayItemCount(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const Party *pParty = play.pContext->runtimeDriver->party();
    lua_pushinteger(pLuaState,
        pParty != nullptr ? pParty->inventoryItemCount(uint32_t(luaL_checkinteger(pLuaState, 1))) : 0);
    return 1;
}

int scenarioPlayPackItems(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const Party *pParty = play.pContext->runtimeDriver->party();
    std::map<uint32_t, uint32_t> counts;

    if (pParty != nullptr)
    {
        for (const Character &member : pParty->members())
        {
            for (const InventoryItem &item : member.inventory)
            {
                counts[item.objectDescriptionId] += std::max<uint32_t>(1, item.quantity);
            }
        }
    }

    std::string text;

    for (const auto &[itemId, count] : counts)
    {
        text += (text.empty() ? "" : " ") + std::to_string(itemId) + "x" + std::to_string(count);
    }

    lua_pushstring(pLuaState, text.c_str());
    return 1;
}

int scenarioPlayDiscard(lua_State *pLuaState)
{
    // A player dropping a spare item out of the packs to make room (gone, not a quest step).
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    Party *pParty = play.pContext->runtimeDriver->party();
    lua_pushboolean(pLuaState, pParty != nullptr && pParty->removeItem(uint32_t(luaL_checkinteger(pLuaState, 1))));
    return 1;
}

// A player putting the item on the cursor into the packs (the game's own placement, the active member first, then the
// others): true when placed; false when the cursor is empty or the item fits nobody.
int scenarioPlayStow(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    lua_pushboolean(pLuaState, play.pContext->runtimeDriver->placeHeldItemInAnyMemberInventory());
    return 1;
}

std::string scenarioMechanismStateText(uint16_t state);

int scenarioPlayDoorState(lua_State *pLuaState)
{
    // What a player sees of a door: "open", "closed", "opening", "closing" ("none": no such door).
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    const EventRuntimeState *pState = play.pContext->runtimeDriver->eventRuntimeState();
    const uint32_t doorId = uint32_t(luaL_checkinteger(pLuaState, 1));
    std::string text = "none";

    if (pState != nullptr)
    {
        const auto found = pState->mechanisms.find(doorId);

        if (found != pState->mechanisms.end())
        {
            text = scenarioMechanismStateText(found->second.state);
        }
    }

    lua_pushstring(pLuaState, text.c_str());
    return 1;
}

int scenarioPlayHeld(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    lua_pushinteger(pLuaState, play.pContext->runtimeDriver->heldCursorItemId());
    return 1;
}

int scenarioPlayTakeChest(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    std::string failure;
    lua_pushboolean(pLuaState, play.pContext->runtimeDriver->takeAllFromOpenChest(failure));
    return 1;
}

int scenarioPlayClose(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    std::string failure;
    lua_pushboolean(pLuaState, play.pContext->runtimeDriver->closeDialog(failure));
    return 1;
}

// clear_hostiles(radius): kills the party's enemies within the radius (the run's rule), returns how many.
int scenarioPlayClearHostiles(lua_State *pLuaState)
{
    ScenarioPlayContext &play = scenarioPlayContext(pLuaState);
    size_t killed = 0;
    std::string failure;
    if (!play.pContext->runtimeDriver->killHostilesNear(float(luaL_optnumber(pLuaState, 1, 2048.0)), killed, failure))
    {
        return luaL_error(pLuaState, "clear_hostiles: %s", failure.c_str());
    }
    lua_pushinteger(pLuaState, lua_Integer(killed));
    return 1;
}

int scenarioPlayLog(lua_State *pLuaState)
{
    std::cout << "PLAY " << luaL_checkstring(pLuaState, 1) << '\n';
    return 0;
}

bool runPlayLua(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    const std::string source = step.payload["source"].as<std::string>("");
    ScenarioPlayContext play = {};
    play.pContext = &context;
    play.maxSeconds = step.payload["max_seconds"].as<float>(play.maxSeconds);

    if (const EventRuntimeState *pState = context.runtimeDriver->eventRuntimeState())
    {
        play.statusIndex = pState->statusMessages.size();
    }

    std::unique_ptr<lua_State, decltype(&lua_close)> state(luaL_newstate(), &lua_close);
    lua_State *pLuaState = state.get();
    luaL_requiref(pLuaState, "_G", luaopen_base, 1);
    luaL_requiref(pLuaState, LUA_STRLIBNAME, luaopen_string, 1);
    luaL_requiref(pLuaState, LUA_TABLIBNAME, luaopen_table, 1);
    luaL_requiref(pLuaState, LUA_MATHLIBNAME, luaopen_math, 1);
    lua_settop(pLuaState, 0);
    const std::array<std::pair<const char *, lua_CFunction>, 23> functions = {{
        {"clear_hostiles", scenarioPlayClearHostiles}, {"party", scenarioPlayParty}, {"held", scenarioPlayHeld},
        {"stow", scenarioPlayStow}, {"conditions", scenarioPlayConditions},
        {"item_count", scenarioPlayItemCount}, {"pack_items", scenarioPlayPackItems},
        {"classes", scenarioPlayClasses}, {"experience", scenarioPlayExperience}, {"gold", scenarioPlayGold},
        {"remember", scenarioPlayRemember}, {"recall", scenarioPlayRecall},
        {"discard", scenarioPlayDiscard}, {"door_state", scenarioPlayDoorState},
        {"click", scenarioPlayClick}, {"wait", scenarioPlayWait}, {"status", scenarioPlayStatus},
        {"qbit", scenarioPlayQBit}, {"has_item", scenarioPlayHasItem}, {"mapvar", scenarioPlayMapVar},
        {"take_chest", scenarioPlayTakeChest}, {"close", scenarioPlayClose}, {"log", scenarioPlayLog}}};

    for (const auto &[pName, function] : functions)
    {
        lua_pushlightuserdata(pLuaState, &play);
        lua_pushcclosure(pLuaState, function, 1);
        lua_setglobal(pLuaState, pName);
    }

    // open_door(event_id, door_id): a player's way through a door that closes by itself or that monsters also open
    // (a click while it moves does nothing): wait until it stops, click its event if it is shut, wait until it opens.
    // A monster in its swing holds an opening door, so the party's enemies near it are killed while it waits.
    // loot_chest(event_id): opens a chest and takes all; a trap the party cannot disarm goes off on the first click
    // and leaves the chest shut, so it clicks again, as a player does.
    static constexpr std::string_view PlayPreludeSource = R"lua(
local function settledDoor(door)
  for _ = 1, 120 do
    local state = door_state(door)
    if state == "open" or state == "closed" then return state end
    clear_hostiles(1500)
    wait(0.25)
  end
  error("door " .. door .. " never stopped moving: " .. door_state(door), 3)
end
function open_door(event, door)
  if settledDoor(door) == "closed" then click(event) end
  if settledDoor(door) ~= "open" then error("door " .. door .. " did not open from event " .. event, 2) end
end
function loot_chest(event)
  for _ = 1, 3 do
    click(event); wait(1)
    if take_chest() then close(); return end
  end
  error("chest event " .. event .. " never opened: " .. status(), 2)
end
)lua";

    if (luaL_loadbuffer(pLuaState, PlayPreludeSource.data(), PlayPreludeSource.size(), "=play_prelude") != LUA_OK
        || lua_pcall(pLuaState, 0, 0, 0) != LUA_OK)
    {
        failures.push_back(stepLocation(step) + ": play_lua prelude: " + std::string(lua_tostring(pLuaState, -1)));
        return false;
    }

    const std::string chunkName = "@" + stepLocation(step);

    if (luaL_loadbuffer(pLuaState, source.data(), source.size(), chunkName.c_str()) != LUA_OK
        || lua_pcall(pLuaState, 0, 0, 0) != LUA_OK)
    {
        failures.push_back(stepLocation(step) + ": play_lua: " + std::string(lua_tostring(pLuaState, -1)));
        syncContextFromRuntime(context);
        return false;
    }

    syncContextFromRuntime(context);
    std::cout << "PLAY done waited=" << scenarioFloat(play.waited) << "s\n";
    return true;
}

// party_defeat: {wait_seconds, knock_out, expect_map}: the fight goes on until the party is down (knock_out: every
// member falls at once), then the game's defeat
// (world.yml partyDeath: MM9 wakes the party in Arslegard).
bool runPartyDefeat(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    std::string destination;
    std::string failure;

    if (!context.runtimeDriver->defeatParty(step.payload["wait_seconds"].as<float>(60.0f),
            step.payload["knock_out"].as<bool>(false), destination, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        syncContextFromRuntime(context);
        return false;
    }

    syncContextFromRuntime(context);
    const bool gameOver = destination == "game over";
    const bool expectGameOver = step.payload["expect_game_over"].as<bool>(false);

    if (gameOver)
    {
        // The world's game over (world.yml partyDeath `when`); the game would show its movie and load the autosave.
        std::cout << "DEFEAT game over (the autosave would load)\n";
    }
    else
    {
        std::cout << "DEFEAT the party woke on " << context.runtimeDriver->currentMapFileName() << '\n';
    }

    if (gameOver != expectGameOver)
    {
        failures.push_back(stepLocation(step) + (gameOver ? ": the defeat was a game over" : ": the party woke on "
            + context.runtimeDriver->currentMapFileName() + ", expected a game over"));
        return false;
    }

    const std::string expected = gameOver ? std::string() : step.payload["expect_map"].as<std::string>("");

    if (!expected.empty() && lowerAscii(expected) != lowerAscii(context.runtimeDriver->currentMapFileName()))
    {
        failures.push_back(stepLocation(step) + ": the party woke on " + context.runtimeDriver->currentMapFileName()
            + ", expected " + expected);
        return false;
    }

    return true;
}

// reload: {name}: saves the game and loads it straight back, as a player who saves and reloads there would
// (tests/playthrough/mm9/run.py --reload inserts it to find state a save and load loses), then dismisses what greets
// the party on arrival. Skipped, and said so, while a player could not save: a dialogue, a chest, a cinematic or a map
// move in progress.
bool runReload(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    const std::string blocked = context.runtimeDriver->saveBlockedReason();
    // expect_blocked: the reload must be refused, its reason containing this text (a map that forbids saving).
    const std::string expectBlocked =
        step.payload.IsMap() ? step.payload["expect_blocked"].as<std::string>("") : std::string();

    if (!expectBlocked.empty() && blocked.find(expectBlocked) == std::string::npos)
    {
        failures.push_back(stepLocation(step) + ": reload expected to be refused (\"" + expectBlocked + "\"), "
            + (blocked.empty() ? std::string("but the party could save") : "but: " + blocked));
        return false;
    }

    if (!blocked.empty())
    {
        std::cout << "RELOAD skipped at step " << step.stepIndex << ": " << blocked << '\n';
        return true;
    }

    std::error_code errorCode;
    std::filesystem::create_directories(context.saveGameRootPath, errorCode);
    const std::filesystem::path path = context.saveGameRootPath / "reload.oysav";
    std::string failure;

    if (!context.runtimeDriver->saveGameToPath(path, "reload", failure)
        || !context.runtimeDriver->loadGameFromPath(path, failure))
    {
        failures.push_back(stepLocation(step) + ": reload: " + failure);
        return false;
    }

    // As a player who has just loaded: what greets the party on arrival (a found-player talk) opens and is dismissed.
    for (int dismissed = 0; dismissed < 3; ++dismissed)
    {
        if (!context.runtimeDriver->advanceRuntime(0.5f, failure, true))
        {
            failures.push_back(stepLocation(step) + ": reload: " + failure);
            return false;
        }

        const ScenarioDialogSnapshot dialog = context.runtimeDriver->activeDialogSnapshot();

        if (!dialog.active)
        {
            break;
        }

        std::cout << "RELOAD dismissed \"" << dialog.title << "\" after the load\n";
        context.runtimeDriver->closeDialog(failure);
    }

    syncContextFromRuntime(context);
    std::cout << "RELOAD ok at step " << step.stepIndex << " on " << context.runtimeDriver->currentMapFileName() << '\n';
    return true;
}

// climb: {ladder, down, timeout_seconds}: walks to a ladder and climbs it with the movement keys
// (ScenarioRuntimeDriver::climbLadder); the party must leave it at its other end.
bool runClimb(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    std::vector<std::string> trail;
    std::string failure;
    const bool climbed = context.runtimeDriver->climbLadder(step.payload["ladder"].as<std::string>(""),
        step.payload["down"].as<bool>(false), step.payload["timeout_seconds"].as<float>(30.0f), trail, failure);
    syncContextFromRuntime(context);

    for (const std::string &line : trail)
    {
        std::cout << "CLIMB " << line << '\n';
    }

    if (!climbed)
    {
        failures.push_back(stepLocation(step) + ": climb: " + failure);
        return false;
    }

    return true;
}

// pick_up: {item_id, reach}: takes an item lying in the map as a player does (ScenarioRuntimeDriver::pickUpWorldItem):
// within reach (default 400) of the party's eye, the camera turned at it, the use key; the item must reach the party.
bool runPickUp(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    const uint32_t itemId = step.payload["item_id"].as<uint32_t>(0);
    std::string log;
    std::string failure;

    if (!context.runtimeDriver->pickUpWorldItem(itemId, step.payload["reach"].as<float>(400.0f), log, failure))
    {
        failures.push_back(stepLocation(step) + ": pick_up: " + failure);
        return false;
    }

    std::string advanceFailure;
    context.runtimeDriver->advanceRuntime(0.2f, advanceFailure);
    syncContextFromRuntime(context);
    std::cout << "PICKUP " << log << '\n';
    const Party *pParty = context.runtimeDriver->party();

    if (pParty == nullptr || !pParty->hasItemAnywhere(itemId))
    {
        failures.push_back(stepLocation(step) + ": pick_up: item " + std::to_string(itemId) + " did not reach the party");
        return false;
    }

    return true;
}

// clear_hostiles: {radius, min}: kills the party's enemies near it (an immortal playthrough does not test combat).
bool runClearHostiles(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    size_t killed = 0;
    std::string failure;

    if (!context.runtimeDriver->killHostilesNear(step.payload["radius"].as<float>(2048.0f), killed, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    std::cout << "CLEAR hostiles killed=" << killed << '\n';

    if (killed < step.payload["min"].as<size_t>(0))
    {
        failures.push_back(stepLocation(step) + ": clear_hostiles killed " + std::to_string(killed) + ", expected at least "
            + std::to_string(step.payload["min"].as<size_t>(0)));
        return false;
    }

    return true;
}

// use_item: {item_id, member_index, expect}: drinks or uses the member's first pack item of the id.
bool runUseItem(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);
    bool used = false;
    std::string failure;

    if (!context.runtimeDriver->useInventoryItem(
            step.payload["member_index"].as<size_t>(0), step.payload["item_id"].as<uint32_t>(0), used, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return checkExpectedOutcome(step, "use_item", used, failures);
}

// right_click_portrait: {item_id, carrier_index, member_index, inventory, release, expect}: right-clicks the member's
// portrait with the carrier's first pack item of the id under the cursor (on the inventory page when `inventory`).
// A scroll's text must close with the release; with `release` (Modern controls: press on the crosshair, release on
// the portrait) it must stay until a left click instead.
bool runRightClickPortrait(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);
    const size_t memberIndex = step.payload["member_index"].as<size_t>(0);
    bool used = false;
    std::string failure;

    if (!context.runtimeDriver->rightClickPortraitWithItem(
            step.payload["carrier_index"].as<size_t>(memberIndex),
            memberIndex,
            step.payload["item_id"].as<uint32_t>(0),
            step.payload["inventory"].as<bool>(false),
            step.payload["release"].as<bool>(false),
            used,
            failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return checkExpectedOutcome(step, "right_click_portrait", used, failures);
}

// party_charge: {actor_index, status, advance_seconds, min_moved}: the Knight Charge action at the actor; status is the
// line the rules must give ("none" for no charge), then the run advances advance_seconds and the party must have moved
// at least min_moved units.
bool runPartyCharge(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);
    const std::optional<size_t> actorIndex = step.payload["actor_index"]
        ? std::optional<size_t>(scenarioActorIndex(context, step.payload["actor_index"]))
        : std::nullopt;
    const ScenarioPose before = context.runtimeDriver->currentPose();
    std::optional<std::string> status;
    std::string failure;

    if (!context.runtimeDriver->partyCharge(actorIndex, status, failure)
        || !context.runtimeDriver->advanceRuntime(step.payload["advance_seconds"].as<float>(0.0f), failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    const ScenarioPose after = context.runtimeDriver->currentPose();
    const float moved = std::hypot(after.x - before.x, after.y - before.y);
    std::cout << "party_charge status=\"" << status.value_or("none") << "\" moved=" << moved << '\n';
    syncContextFromRuntime(context);
    bool success = true;

    if (step.payload["status"] && step.payload["status"].as<std::string>() != status.value_or("none"))
    {
        failures.push_back(stepLocation(step) + ": party_charge said \"" + status.value_or("none") + "\"");
        success = false;
    }

    if (step.payload["min_moved"] && moved < step.payload["min_moved"].as<float>())
    {
        failures.push_back(stepLocation(step) + ": party_charge moved the party " + std::to_string(moved) + " units");
        success = false;
    }

    return success;
}

// cast_spell: {member_index, spell_id, skill, mastery (1-4), actor_index, target_member, scroll, expect,
// expect_status}: the member casts the spell with full mana through the party's spell system; skill and mastery set
// the spell's school first (with `scroll`: the scroll's power instead). Projectiles fly on with advance_runtime.
// expect_status names the outcome when "refused" is not precise enough: succeeded, failed (the spell failed) or
// needs_window (Town Portal and Lloyd's Beacon before their window is used).
bool runCastSpell(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);
    ScenarioSpellCastRequest request;
    request.memberIndex = step.payload["member_index"].as<size_t>(0);
    request.spellId = step.payload["spell_id"].as<uint32_t>(0);
    request.skill = step.payload["skill"].as<uint32_t>(0);
    request.mastery = SkillMastery(std::clamp(step.payload["mastery"].as<int>(1), 1, 4));
    request.scroll = step.payload["scroll"].as<bool>(false);

    if (step.payload["actor_index"])
    {
        request.actorIndex = scenarioActorIndex(context, step.payload["actor_index"]);
    }

    if (step.payload["target_member"])
    {
        request.targetMemberIndex = step.payload["target_member"].as<size_t>();
    }

    if (const YAML::Node pointNode = step.payload["target_point"])
    {
        if (!pointNode.IsSequence() || pointNode.size() != 3)
        {
            failures.push_back(stepLocation(step) + ": cast_spell target_point must be [x, y, z]");
            return false;
        }

        request.targetPoint = std::array<float, 3>{pointNode[0].as<float>(), pointNode[1].as<float>(),
            pointNode[2].as<float>()};
    }

    PartySpellCastStatus status = PartySpellCastStatus::Failed;
    std::string failure;

    if (!context.runtimeDriver->castSpell(request, status, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);

    if (const YAML::Node expectStatusNode = step.payload["expect_status"])
    {
        const std::string expected = expectStatusNode.as<std::string>();
        const std::string actual = status == PartySpellCastStatus::Succeeded ? "succeeded"
            : status == PartySpellCastStatus::Failed                         ? "failed"
            : status == PartySpellCastStatus::NeedUtilityUi                  ? "needs_window"
                                                                             : "status " + std::to_string(int(status));

        if (expected != "succeeded" && expected != "failed" && expected != "needs_window")
        {
            failures.push_back(
                stepLocation(step) + ": cast_spell expect_status must be succeeded, failed or needs_window");
            return false;
        }

        if (actual != expected)
        {
            failures.push_back(stepLocation(step) + ": cast_spell expected " + expected + " but was " + actual);
            return false;
        }
    }

    return checkExpectedOutcome(step, "cast_spell", status == PartySpellCastStatus::Succeeded, failures);
}

std::optional<EquipmentSlot> parseScenarioEquipmentSlot(const std::string &value);

// craft: {member_index, target_item_id, worn_slot, material_item_id, all, choice, expect}: the Workbench's Apply (or
// Apply All) with the material on the member's pack item, or the item worn in worn_slot; `choice` picks among the
// step's options (the Pearl's enchantment, first by default).
bool runCraft(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    std::optional<EquipmentSlot> wornSlot;

    if (step.payload["worn_slot"])
    {
        wornSlot = parseScenarioEquipmentSlot(step.payload["worn_slot"].as<std::string>());

        if (!wornSlot)
        {
            failures.push_back(stepLocation(step) + ": unknown worn_slot");
            return false;
        }
    }

    seedRuntimeDriverFromContext(context);
    bool crafted = false;
    std::string reason;
    std::string failure;

    if (!context.runtimeDriver->craftItem(step.payload["member_index"].as<size_t>(0),
            step.payload["target_item_id"].as<uint32_t>(0), wornSlot, step.payload["material_item_id"].as<uint32_t>(0),
            step.payload["all"].as<bool>(false), step.payload["choice"].as<size_t>(0), crafted, reason, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    const bool expected = checkExpectedOutcome(step, "craft", crafted, failures);

    if (!expected && !reason.empty())
    {
        failures.back() += " (" + reason + ")";
    }

    return expected;
}

// combine_gems: {item_id, all, expect}: the Workbench's gem merge.
bool runCombineGems(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);
    bool combined = false;
    std::string failure;

    if (!context.runtimeDriver->combineGems(
            step.payload["item_id"].as<uint32_t>(0), step.payload["all"].as<bool>(false), combined, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return checkExpectedOutcome(step, "combine_gems", combined, failures);
}

// spawn_actor: {monster_id, count, x, y, z, group, near_party, boss_affix, party_ally}: hostile monsters summoned at a
// point (outdoors), appended after the map's actors, e.g. a drone by Landfall's wall to watch its defenders engage it.
// near_party: true instead of x, y, z summons them a step from the party; party_ally: true summons them as a party
// spell's summons, fighting for the party.
bool runSpawnActor(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    const bool nearParty = step.payload["near_party"].as<bool>(false);

    for (const char *pField : {"monster_id", "x", "y", "z"})
    {
        if ((!nearParty || std::string(pField) == "monster_id")
            && (!step.payload[pField] || !step.payload[pField].IsScalar()))
        {
            failures.push_back(stepLocation(step) + ": spawn_actor requires scalar field '" + pField + "'");
            return false;
        }
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);
    std::string failure;
    const ScenarioPose pose = context.runtimeDriver->currentPose();
    const float x = nearParty ? pose.x + 200.0f : step.payload["x"].as<float>();
    const float y = nearParty ? pose.y : step.payload["y"].as<float>();
    const float z = nearParty ? pose.z : step.payload["z"].as<float>();

    if (!context.runtimeDriver->spawnActor(step.payload["monster_id"].as<int16_t>(),
            step.payload["count"].as<uint32_t>(1), x, y, z, step.payload["group"].as<uint32_t>(0),
            step.payload["boss_affix"].as<uint8_t>(0), step.payload["party_ally"].as<bool>(false), failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

// ai_arena: {path, log}: sets up an AI arena (game/debug/AiArena.h, tests/scenarios/mm9/ai/README.md): loads its map
// when another is loaded, places the party, hides the map's actors, spawns the arena's monsters and starts the
// decision trace. A relative path is read next to the scenario first; log: a trace log file (none by default).
bool runAiArena(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    if (!step.payload["path"] || !step.payload["path"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": ai_arena requires scalar field 'path'");
        return false;
    }

    std::filesystem::path path = step.payload["path"].as<std::string>();

    if (path.is_relative() && std::filesystem::exists(step.sourcePath.parent_path() / path))
    {
        path = step.sourcePath.parent_path() / path;
    }

    std::string failure;
    const std::optional<AiArena> arena = loadAiArena(path, failure);

    if (!arena || !ensureRuntimeDriver(context, failures))
    {
        failures.push_back(stepLocation(step) + ": " + (failure.empty() ? "ai_arena failed" : failure));
        return false;
    }

    seedRuntimeDriverFromContext(context);

    if (!context.runtimeDriver->applyAiArena(*arena, step.payload["log"].as<std::string>(""), failure))
    {
        failures.push_back(stepLocation(step) + ": ai_arena " + path.string() + ": " + failure);
        return false;
    }

    std::string actors;

    for (size_t actorIndex : context.runtimeDriver->aiArenaActorIndices())
    {
        actors += (actors.empty() ? "" : ",") + std::to_string(actorIndex);
    }

    scenarioLog(context, ScenarioLogColor::Cyan, "AI ARENA " + arena->name + " map=" + arena->map + " monsters="
        + std::to_string(arena->monsters.size()) + " actors=" + actors);
    syncContextFromRuntime(context);
    return true;
}

// The actor an ai_trace check or dump reads: actor_index (a map index, "last") or arena_monster (the arena's Nth
// monster); none: every actor. False after a failure.
bool aiTraceActorFilter(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const YAML::Node &node,
    std::optional<size_t> &actorIndex,
    std::vector<std::string> &failures)
{
    if (node["actor_index"])
    {
        actorIndex = scenarioActorIndex(context, node["actor_index"]);
    }
    else if (node["arena_monster"])
    {
        const std::vector<size_t> &arenaActors = context.runtimeDriver->aiArenaActorIndices();
        const size_t monster = node["arena_monster"].as<size_t>();

        if (monster >= arenaActors.size())
        {
            failures.push_back(stepLocation(step) + ": arena_monster " + std::to_string(monster) + " but the arena has "
                + std::to_string(arenaActors.size()) + " monsters");
            return false;
        }

        actorIndex = arenaActors[monster];
    }

    return true;
}

// ai_trace_dump: {actor_index | arena_monster, decisions_only, last}: prints the decision trace (the last N lines).
bool runAiTraceDump(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node payload = step.payload && step.payload.IsMap() ? step.payload : YAML::Node(YAML::NodeType::Map);
    std::optional<size_t> actorIndex;

    if (!ensureRuntimeDriver(context, failures) || !aiTraceActorFilter(context, step, payload, actorIndex, failures))
    {
        return false;
    }

    const bool decisionsOnly = payload["decisions_only"].as<bool>(false);
    std::vector<const ActorAiTraceEntry *> lines;

    for (const ActorAiTraceEntry &entry : context.runtimeDriver->aiTrace().entries())
    {
        if ((!actorIndex || entry.actorIndex == *actorIndex) && (!decisionsOnly || entry.decision))
        {
            lines.push_back(&entry);
        }
    }

    const size_t last = payload["last"].as<size_t>(lines.size());
    const size_t first = lines.size() > last ? lines.size() - last : 0;
    scenarioLog(context, ScenarioLogColor::Cyan, "AI TRACE " + std::to_string(lines.size() - first) + " of "
        + std::to_string(lines.size()) + " lines, t=" + std::to_string(context.runtimeDriver->aiTrace().timeSeconds()));

    for (size_t index = first; index < lines.size(); ++index)
    {
        scenarioLog(context, ScenarioLogColor::Default, formatActorAiTraceLine(*lines[index]));
    }

    return true;
}

// fire_actor_projectile: {actor_index, ability, damage}: the actor fires its attack (attack1, attack2, spell1,
// spell2; default attack1) at the party now, as an AI shot does (a true_aim monster's shot homes).
bool runFireActorProjectile(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    if (!step.payload["actor_index"] || !step.payload["actor_index"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": fire_actor_projectile requires scalar field 'actor_index'");
        return false;
    }

    const std::string abilityName = step.payload["ability"].as<std::string>("attack1");
    std::optional<GameplayActorAttackAbility> ability;

    if (abilityName == "attack1")
    {
        ability = GameplayActorAttackAbility::Attack1;
    }
    else if (abilityName == "attack2")
    {
        ability = GameplayActorAttackAbility::Attack2;
    }
    else if (abilityName == "spell1")
    {
        ability = GameplayActorAttackAbility::Spell1;
    }
    else if (abilityName == "spell2")
    {
        ability = GameplayActorAttackAbility::Spell2;
    }

    if (!ability)
    {
        failures.push_back(stepLocation(step) + ": fire_actor_projectile ability must be attack1, attack2, spell1 "
            "or spell2");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);
    std::string failure;

    if (!context.runtimeDriver->fireActorProjectileAtParty(
            scenarioActorIndex(context, step.payload["actor_index"]), *ability, step.payload["damage"].as<int>(1),
            failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

// blink_actor: {actor_index}: the actor blinks now as its blink modifier would (fails without one or a free spot).
// Runs one event of the current map (or a global one), as clicking its target would; a map move it starts happens.
bool runExecuteEvent(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    if (!step.payload["id"] || !step.payload["id"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": execute_event requires scalar field 'id'");
        return false;
    }

    seedRuntimeDriverFromContext(context);
    std::string failure;

    if (!context.runtimeDriver->executeMapEvent(step.payload["id"].as<uint16_t>(), failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

// lua_event: {source}: the scenario's own Lua run as an event of the current map, with the map's event support and
// world (evt.SummonMonstersById, evt.SetActorTarget ...); a Lua error fails the step.
bool runLuaEvent(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    if (!step.payload["source"] || !step.payload["source"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": lua_event requires scalar field 'source'");
        return false;
    }

    seedRuntimeDriverFromContext(context);
    std::string failure;

    if (!context.runtimeDriver->runLuaEvent(step.payload["source"].as<std::string>(), failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

bool runBlinkActor(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    if (!step.payload["actor_index"] || !step.payload["actor_index"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": blink_actor requires scalar field 'actor_index'");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);
    std::string failure;

    if (!context.runtimeDriver->blinkActor(scenarioActorIndex(context, step.payload["actor_index"]), failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

// charge_actor: {actor_index}: the actor starts its charge at the party now (fails without the charge modifier).
bool runChargeActor(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    if (!step.payload["actor_index"] || !step.payload["actor_index"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": charge_actor requires scalar field 'actor_index'");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);
    std::string failure;

    if (!context.runtimeDriver->chargeActor(scenarioActorIndex(context, step.payload["actor_index"]), failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

// frenzy_actor: {actor_index}: the actor starts its frenzy now (fails without the frenzy modifier).
bool runFrenzyActor(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    if (!step.payload["actor_index"] || !step.payload["actor_index"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": frenzy_actor requires scalar field 'actor_index'");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);
    std::string failure;

    if (!context.runtimeDriver->frenzyActor(scenarioActorIndex(context, step.payload["actor_index"]), failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

// assert charges: {started, hits, misses, frenzies, min_started, min_hits, min_misses, min_frenzies}: the map's charges
// and frenzies so far (exact or at least).
// combat_log: {min_entries, dealt_min, taken_min, with_stages_min, loot_min, critical_min}: the combat log's entries
// so far (loot: the loot filter's "Filtered: ... -> N gold" lines; critical: the party's critical hits).
bool assertCombatLog(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["combat_log"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !context.runtimeDriver)
    {
        failures.push_back(stepLocation(step) + ": combat_log needs a map and the runtime (faithful mode)");
        return false;
    }

    size_t dealt = 0;
    size_t taken = 0;
    size_t loot = 0;
    size_t withStages = 0;
    size_t critical = 0;
    const std::deque<CombatLogEntry> &entries = context.runtimeDriver->combatLog().entries();
    for (const CombatLogEntry &entry : entries)
    {
        (entry.kind == CombatLogKind::Dealt ? dealt : entry.kind == CombatLogKind::Taken ? taken : loot) += 1;
        withStages += entry.stages.empty() ? 0 : 1;
        critical += entry.kind == CombatLogKind::Dealt && entry.critical ? 1 : 0;
    }

    const std::array<std::pair<const char *, size_t>, 6> counts = {{
        {"min_entries", entries.size()}, {"dealt_min", dealt}, {"taken_min", taken}, {"with_stages_min", withStages},
        {"loot_min", loot}, {"critical_min", critical},
    }};

    for (const auto &[key, count] : counts)
    {
        if (node[key] && count < node[key].as<size_t>())
        {
            failures.push_back(stepLocation(step) + ": combat_log " + key + " " + node[key].as<std::string>()
                + ", found " + std::to_string(count));
            return false;
        }
    }

    return true;
}

bool assertCharges(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["charges"];

    if (!node)
    {
        return true;
    }

    const std::optional<GameplayChargeCounts> counts =
        node.IsMap() && ensureRuntimeDriver(context, failures) ? context.runtimeDriver->chargeCounts() : std::nullopt;

    if (!counts)
    {
        failures.push_back(stepLocation(step) + ": charges assertion requires a map and a world with charges");
        return false;
    }

    scenarioLog(context, ScenarioLogColor::Cyan, "CHARGES started=" + std::to_string(counts->started) + " hits="
        + std::to_string(counts->hits) + " misses=" + std::to_string(counts->misses) + " frenzies="
        + std::to_string(counts->frenzies));
    bool success = true;
    const auto check = [&](const char *pName, uint32_t actual, bool atLeast)
    {
        if (node[pName] && (atLeast ? actual < node[pName].as<uint32_t>() : actual != node[pName].as<uint32_t>()))
        {
            failures.push_back(stepLocation(step) + ": charges " + pName + " expected " + node[pName].as<std::string>()
                + ", actual " + std::to_string(actual));
            success = false;
        }
    };
    check("started", counts->started, false);
    check("hits", counts->hits, false);
    check("misses", counts->misses, false);
    check("min_started", counts->started, true);
    check("min_hits", counts->hits, true);
    check("min_misses", counts->misses, true);
    check("frenzies", counts->frenzies, false);
    check("min_frenzies", counts->frenzies, true);
    return success;
}

// assert projectiles: {source, source_monster_id, min_count, max_count, homing, toward_party_within_degrees, report}:
// the live projectiles fired by actors (of that monster when given), or by the party with `source: party`. homing:
// every one of them homes (true) or none does (false); toward_party_within_degrees: each one flies within that angle of
// the party.
bool assertProjectiles(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["projectiles"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !ensureRuntimeDriver(context, failures))
    {
        failures.push_back(stepLocation(step) + ": projectiles assertion requires a map and an active runtime");
        return false;
    }

    const GameplayProjectileService *pProjectiles = context.runtimeDriver->projectileService();

    if (pProjectiles == nullptr)
    {
        failures.push_back(stepLocation(step) + ": projectiles assertion needs a map with projectiles");
        return false;
    }

    using ProjectileState = GameplayProjectileService::ProjectileState;
    const std::optional<int> monsterId = node["source_monster_id"]
        ? std::optional<int>(node["source_monster_id"].as<int>()) : std::nullopt;
    const std::string source = node["source"].as<std::string>("actor");

    if (source != "actor" && source != "party")
    {
        failures.push_back(stepLocation(step) + ": projectiles source must be actor or party");
        return false;
    }

    const ProjectileState::SourceKind sourceKind =
        source == "party" ? ProjectileState::SourceKind::Party : ProjectileState::SourceKind::Actor;
    const ScenarioPose pose = context.runtimeDriver->currentPose();
    std::vector<const ProjectileState *> matching;

    for (const ProjectileState &projectile : pProjectiles->projectiles())
    {
        if (!projectile.isExpired && projectile.sourceKind == sourceKind
            && (!monsterId || projectile.sourceMonsterId == *monsterId))
        {
            matching.push_back(&projectile);
        }
    }

    bool success = true;
    const auto fail = [&](const std::string &message)
    {
        failures.push_back(stepLocation(step) + ": projectiles " + message);
        success = false;
    };

    for (const ProjectileState *pProjectile : matching)
    {
        const float toX = pose.x - pProjectile->x;
        const float toY = pose.y - pProjectile->y;
        const float toZ = pose.z + 96.0f - pProjectile->z;
        const float toLength = std::sqrt(toX * toX + toY * toY + toZ * toZ);
        const float speed = std::sqrt(pProjectile->velocityX * pProjectile->velocityX
            + pProjectile->velocityY * pProjectile->velocityY + pProjectile->velocityZ * pProjectile->velocityZ);
        const float cosine = toLength > 0.0f && speed > 0.0f
            ? (toX * pProjectile->velocityX + toY * pProjectile->velocityY + toZ * pProjectile->velocityZ)
                / (toLength * speed)
            : 1.0f;
        const float degreesOff = std::acos(std::clamp(cosine, -1.0f, 1.0f)) * 180.0f / 3.14159265f;
        const bool homing = pProjectile->homing && !pProjectile->homing->lost;

        if (node["report"].as<bool>(false))
        {
            std::ostringstream message;
            message << "PROJECTILE id=" << pProjectile->projectileId << " monster=" << pProjectile->sourceMonsterId
                    << " position=" << pProjectile->x << ',' << pProjectile->y << ',' << pProjectile->z
                    << " speed=" << speed << " homing=" << (homing ? "true" : "false")
                    << " degrees_off_party=" << degreesOff;
            scenarioLog(context, ScenarioLogColor::Cyan, message.str());
        }

        if (node["homing"] && node["homing"].as<bool>() != homing)
        {
            fail("id " + std::to_string(pProjectile->projectileId) + " homing=" + (homing ? "true" : "false"));
        }

        if (node["toward_party_within_degrees"]
            && degreesOff > node["toward_party_within_degrees"].as<float>())
        {
            fail("id " + std::to_string(pProjectile->projectileId) + " flies "
                + std::to_string(degreesOff) + " degrees off the party");
        }
    }

    if (node["min_count"] && matching.size() < node["min_count"].as<size_t>())
    {
        fail("count " + std::to_string(matching.size()) + " below " + node["min_count"].as<std::string>());
    }

    if (node["max_count"] && matching.size() > node["max_count"].as<size_t>())
    {
        fail("count " + std::to_string(matching.size()) + " above " + node["max_count"].as<std::string>());
    }

    return success;
}

// assert homing_ends: {source_monster_id, hit, min_count, max_count, report}: how the map's recent homing projectiles
// ended (GameplayProjectileService::recentHomingEnds): those of that monster that hit party, actor, world, ward or
// expired (all ends without hit).
bool assertHomingEnds(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["homing_ends"];

    if (!node)
    {
        return true;
    }

    const GameplayProjectileService *pProjectiles =
        node.IsMap() && ensureRuntimeDriver(context, failures) ? context.runtimeDriver->projectileService() : nullptr;

    if (pProjectiles == nullptr)
    {
        failures.push_back(stepLocation(step) + ": homing_ends assertion requires a map and a map with projectiles");
        return false;
    }

    using End = GameplayProjectileService::HomingProjectileEnd;
    const auto hitName = [](End::Hit hit)
    {
        switch (hit)
        {
            case End::Hit::Party: return "party";
            case End::Hit::Actor: return "actor";
            case End::Hit::World: return "world";
            case End::Hit::Ward: return "ward";
            case End::Hit::Expired: return "expired";
        }
        return "expired";
    };
    const std::optional<int> monsterId = node["source_monster_id"]
        ? std::optional<int>(node["source_monster_id"].as<int>()) : std::nullopt;
    const std::string hit = node["hit"].as<std::string>("");
    size_t count = 0;

    for (const End &end : pProjectiles->recentHomingEnds())
    {
        if (node["report"].as<bool>(false))
        {
            std::ostringstream message;
            message << "HOMING_END id=" << end.projectileId << " monster=" << end.sourceMonsterId << " hit="
                    << hitName(end.hit) << " point=" << end.point.x << ',' << end.point.y << ',' << end.point.z
                    << " still_homing=" << (end.stillHoming ? "true" : "false");
            scenarioLog(context, ScenarioLogColor::Cyan, message.str());
        }

        if ((!monsterId || end.sourceMonsterId == *monsterId) && (hit.empty() || hit == hitName(end.hit)))
        {
            ++count;
        }
    }

    bool success = true;

    if (node["min_count"] && count < node["min_count"].as<size_t>())
    {
        failures.push_back(stepLocation(step) + ": homing_ends " + std::to_string(count) + " ends (hit "
            + (hit.empty() ? "any" : hit) + ") below " + node["min_count"].as<std::string>());
        success = false;
    }

    if (node["max_count"] && count > node["max_count"].as<size_t>())
    {
        failures.push_back(stepLocation(step) + ": homing_ends " + std::to_string(count) + " ends (hit "
            + (hit.empty() ? "any" : hit) + ") above " + node["max_count"].as<std::string>());
        success = false;
    }

    return success;
}

// assert dimension_door: {pending, without_quest}: an event asked for the Dimension Door destinations, and whether
// before the Cross Continents quest (evt.OpenDimensionDoor(true)).
bool assertDimensionDoor(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["dimension_door"];

    if (!node)
    {
        return true;
    }

    const EventRuntimeState *pState =
        context.runtimeDriver ? context.runtimeDriver->eventRuntimeState() : nullptr;

    if (!node.IsMap() || pState == nullptr)
    {
        failures.push_back(stepLocation(step) + ": dimension_door needs a map and an active runtime");
        return false;
    }

    bool success = true;

    for (const auto &[pKey, actual] : {std::pair("pending", pState->pendingDimensionDoorOverlay)})
    {
        if (node[pKey] && node[pKey].as<bool>() != actual)
        {
            failures.push_back(stepLocation(step) + ": dimension_door " + pKey + " is "
                + (actual ? "true" : "false"));
            success = false;
        }
    }

    return success;
}

// assert light: {key, on}: an indoor light's switch (evt.SetLight: a BLV light or a scene pulsing light by its key).
bool assertLight(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["light"];

    if (!node)
    {
        return true;
    }

    const EventRuntimeState *pState =
        context.runtimeDriver ? context.runtimeDriver->eventRuntimeState() : nullptr;

    if (!node.IsMap() || !node["key"] || !node["on"] || pState == nullptr)
    {
        failures.push_back(stepLocation(step) + ": light needs {key, on} and an active runtime");
        return false;
    }

    const uint32_t key = node["key"].as<uint32_t>();
    const auto iterator = pState->indoorLightsEnabled.find(key);
    const std::string actual =
        iterator == pState->indoorLightsEnabled.end() ? "unset" : (iterator->second ? "true" : "false");

    if (actual != (node["on"].as<bool>() ? "true" : "false"))
    {
        failures.push_back(stepLocation(step) + ": light " + std::to_string(key) + " is " + actual);
        return false;
    }

    return true;
}

// assert scripted_fog: {active, near, far}: the map script's fog (evt.SetFog / evt.ClearFog); near and far within a
// unit of the given distances.
bool assertScriptedFog(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["scripted_fog"];

    if (!node)
    {
        return true;
    }

    const EventRuntimeState *pState =
        context.runtimeDriver ? context.runtimeDriver->eventRuntimeState() : nullptr;

    if (!node.IsMap() || pState == nullptr)
    {
        failures.push_back(stepLocation(step) + ": scripted_fog needs a map and an active runtime");
        return false;
    }

    const EventRuntimeState::ScriptedFog &fog = pState->scriptedFog;
    bool success = true;

    if (node["active"] && node["active"].as<bool>() != fog.active)
    {
        failures.push_back(stepLocation(step) + ": scripted_fog active is " + (fog.active ? "true" : "false"));
        success = false;
    }

    for (const auto &[pKey, actual] : {std::pair("near", fog.nearDistance), std::pair("far", fog.farDistance)})
    {
        if (node[pKey] && std::abs(node[pKey].as<float>() - actual) > 1.0f)
        {
            failures.push_back(stepLocation(step) + ": scripted_fog " + pKey + " is " + std::to_string(actual));
            success = false;
        }
    }

    return success;
}

// assert water: {state, eye_under, breath_min, breath_max, drowning_ticks_min, drowning_ticks_max, foot_z_min,
// foot_z_max}: the party's state in a scene water volume (dry, wading, falling, bed, submerged, surface, surface_jump),
// its breath (1 full; 1 with the eye out), the drowning ticks taken on this map and its feet's height.
bool assertWater(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["water"];

    if (!node)
    {
        return true;
    }

    std::string failure;
    ScenarioWaterStatus status = {};

    if (!node.IsMap() || !ensureRuntimeDriver(context, failures) || !context.runtimeDriver->waterStatus(status, failure))
    {
        failures.push_back(stepLocation(step) + ": water assertion requires a map of checks and an indoor map"
            + (failure.empty() ? std::string() : " (" + failure + ")"));
        return false;
    }

    std::ostringstream actual;
    actual << "state=" << status.state << " eye_under=" << (status.eyeUnder ? "true" : "false")
           << " breath=" << status.breath << " drowning_ticks=" << status.drowningTicks << " foot_z=" << status.footZ;
    scenarioLog(context, ScenarioLogColor::Cyan, "WATER " + actual.str());
    bool success = true;
    const auto fail = [&](const std::string &what)
    {
        failures.push_back(stepLocation(step) + ": water " + what + " (" + actual.str() + ")");
        success = false;
    };

    if (node["state"] && node["state"].as<std::string>() != status.state)
    {
        fail("state is not " + node["state"].as<std::string>());
    }

    if (node["eye_under"] && node["eye_under"].as<bool>() != status.eyeUnder)
    {
        fail("eye_under is not " + node["eye_under"].as<std::string>());
    }

    if (node["breath_min"] && status.breath < node["breath_min"].as<float>())
    {
        fail("breath under " + node["breath_min"].as<std::string>());
    }

    if (node["breath_max"] && status.breath > node["breath_max"].as<float>())
    {
        fail("breath over " + node["breath_max"].as<std::string>());
    }

    if (node["drowning_ticks_min"] && status.drowningTicks < node["drowning_ticks_min"].as<uint32_t>())
    {
        fail("fewer drowning ticks than " + node["drowning_ticks_min"].as<std::string>());
    }

    if (node["drowning_ticks_max"] && status.drowningTicks > node["drowning_ticks_max"].as<uint32_t>())
    {
        fail("more drowning ticks than " + node["drowning_ticks_max"].as<std::string>());
    }

    if (node["foot_z_min"] && status.footZ < node["foot_z_min"].as<float>())
    {
        fail("feet under " + node["foot_z_min"].as<std::string>());
    }

    if (node["foot_z_max"] && status.footZ > node["foot_z_max"].as<float>())
    {
        fail("feet over " + node["foot_z_max"].as<std::string>());
    }

    return success;
}

// assert food: N: the party carries exactly N food.
bool assertPartyFood(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["food"];

    if (!node)
    {
        return true;
    }

    if (!node.IsScalar())
    {
        failures.push_back(stepLocation(step) + ": food assertion requires a scalar amount");
        return false;
    }

    syncContextFromRuntime(context);
    const int expected = node.as<int>();
    const int actual = context.party.food();
    scenarioLogAssert(context, step, "food", std::to_string(expected), std::to_string(actual), actual == expected);

    if (actual != expected)
    {
        failures.push_back(stepLocation(step) + ": party food " + std::to_string(actual) + ", expected "
            + std::to_string(expected));
        return false;
    }

    return true;
}

// assert game_hour: N: the clock shows hour N (0-23) of the current day.
bool assertGameHour(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["game_hour"];

    if (!node)
    {
        return true;
    }

    if (!node.IsScalar())
    {
        failures.push_back(stepLocation(step) + ": game_hour assertion requires a scalar hour");
        return false;
    }

    syncContextFromRuntime(context);
    const int expected = node.as<int>();
    const int actual = static_cast<int>(std::floor(std::max(0.0f, context.gameMinutes) / 60.0f)) % 24;
    scenarioLogAssert(
        context, step, "game_hour", std::to_string(expected), std::to_string(actual), actual == expected);

    if (actual != expected)
    {
        failures.push_back(stepLocation(step) + ": game hour " + std::to_string(actual) + ", expected "
            + std::to_string(expected));
        return false;
    }

    return true;
}

// assert sprite_hidden: [cog, ...]: those decorations are hidden by the map's event state (evt.SetSprite's override,
// or a hired MM9 talking prop); sprite_shown: [cog, ...]: those are not.
bool assertSpritesHidden(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    bool success = true;

    for (const bool expectHidden : {true, false})
    {
        const char *pKey = expectHidden ? "sprite_hidden" : "sprite_shown";
        const YAML::Node node = step.payload[pKey];

        if (!node)
        {
            continue;
        }

        if (!node.IsSequence() || !context.runtimeDriver || context.runtimeDriver->eventRuntimeState() == nullptr)
        {
            failures.push_back(stepLocation(step) + ": " + pKey + " requires a list of cogs and a running map");
            success = false;
            continue;
        }

        const EventRuntimeState &state = *context.runtimeDriver->eventRuntimeState();

        for (const YAML::Node &cogNode : node)
        {
            const uint32_t cog = cogNode.as<uint32_t>();
            const auto found = state.spriteOverrides.find(cog);
            const bool hidden = found != state.spriteOverrides.end() && found->second.hidden;
            scenarioLogAssert(context, step, std::string(pKey) + "[" + std::to_string(cog) + "]", "true",
                hidden == expectHidden ? "true" : "false", hidden == expectHidden);

            if (hidden != expectHidden)
            {
                failures.push_back(stepLocation(step) + ": decoration " + std::to_string(cog)
                    + (expectHidden ? " is not hidden" : " is hidden"));
                success = false;
            }
        }
    }

    return success;
}

// assert gold: N: the party carries exactly N gold.
bool assertPartyGold(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["gold"];

    if (!node)
    {
        return true;
    }

    if (!node.IsScalar())
    {
        failures.push_back(stepLocation(step) + ": gold assertion requires a scalar amount");
        return false;
    }

    syncContextFromRuntime(context);
    const int expected = node.as<int>();
    const int actual = context.party.gold();
    scenarioLogAssert(context, step, "gold", std::to_string(expected), std::to_string(actual), actual == expected);

    if (actual != expected)
    {
        failures.push_back(stepLocation(step) + ": party gold " + std::to_string(actual) + ", expected "
            + std::to_string(expected));
        return false;
    }

    return true;
}

// assert recovering_members: N: exactly N party members are recovering from an action (a real-time attack count).
bool assertRecoveringMembers(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["recovering_members"];

    if (!node)
    {
        return true;
    }

    if (!node.IsScalar())
    {
        failures.push_back(stepLocation(step) + ": recovering_members assertion requires a scalar count");
        return false;
    }

    syncContextFromRuntime(context);
    const size_t expected = node.as<size_t>();
    size_t actual = 0;

    for (const Character &member : context.party.members())
    {
        actual += member.recoverySecondsRemaining > 0.0f ? 1 : 0;
    }

    scenarioLogAssert(context, step, "recovering_members", std::to_string(expected), std::to_string(actual),
        actual == expected);

    if (actual != expected)
    {
        failures.push_back(stepLocation(step) + ": " + std::to_string(actual) + " members recovering, expected "
            + std::to_string(expected));
        return false;
    }

    return true;
}

// assert quick_item_ring: {open: bool, member_index}: the potion radial's ring, open (at that member's portrait) or not.
bool assertQuickItemRing(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["quick_item_ring"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !ensureRuntimeDriver(context, failures))
    {
        failures.push_back(stepLocation(step) + ": quick_item_ring assertion requires a mapping");
        return false;
    }

    const std::optional<size_t> member = context.runtimeDriver->quickItemRingMember();
    const bool expectedOpen = node["open"].as<bool>(true);
    bool success = member.has_value() == expectedOpen;

    if (success && member && node["member_index"])
    {
        success = *member == node["member_index"].as<size_t>();
    }

    scenarioLogAssert(context, step, "quick_item_ring", expectedOpen ? "open" : "closed",
        member ? "open at " + std::to_string(*member) : std::string("closed"), success);

    if (!success)
    {
        failures.push_back(stepLocation(step) + ": quick item ring is "
            + (member ? "open at member " + std::to_string(*member) : std::string("closed")));
    }

    return success;
}

// assert quick_item_popup: {kind: potions | scrolls | none, member_index}: the basebar's open popup and who drinks or
// reads.
bool assertQuickItemPopup(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["quick_item_popup"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !ensureRuntimeDriver(context, failures))
    {
        failures.push_back(stepLocation(step) + ": quick_item_popup assertion requires a mapping");
        return false;
    }

    const auto [kind, member] = context.runtimeDriver->quickItemPopup();
    const std::string expected = node["kind"].as<std::string>("none");
    bool success = kind == expected;

    if (success && kind != "none" && node["member_index"])
    {
        success = member == node["member_index"].as<size_t>();
    }

    const std::string actual = kind == "none" ? kind : kind + " for member " + std::to_string(member);
    scenarioLogAssert(context, step, "quick_item_popup", expected, actual, success);

    if (!success)
    {
        failures.push_back(stepLocation(step) + ": quick item popup is " + actual);
    }

    return success;
}

// assert autonote: {id, present: bool}: the party has the journal autonote (present by default).
bool assertAutonote(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["autonote"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !node["id"])
    {
        failures.push_back(stepLocation(step) + ": autonote assertion requires id");
        return false;
    }

    syncContextFromRuntime(context);
    const uint32_t id = node["id"].as<uint32_t>();
    const bool expected = node["present"].as<bool>(true);
    const bool actual = context.party.hasAutonote(id);
    scenarioLogAssert(context, step, "autonote", std::to_string(id) + (expected ? "" : " absent"),
        actual ? "present" : "absent", actual == expected);

    if (actual != expected)
    {
        failures.push_back(
            stepLocation(step) + ": autonote " + std::to_string(id) + (actual ? " is set" : " is not set"));
        return false;
    }

    return true;
}

// assert teacher_ledger: {continent, bought: bool}: the party has the continent's Ledger of Teachers (bought by
// default).
bool assertTeacherLedger(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["teacher_ledger"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !node["continent"])
    {
        failures.push_back(stepLocation(step) + ": teacher_ledger assertion requires continent");
        return false;
    }

    syncContextFromRuntime(context);
    const uint32_t continent = node["continent"].as<uint32_t>();
    const bool expected = node["bought"].as<bool>(true);
    const bool actual = context.party.hasTeacherLedger(continent);
    scenarioLogAssert(context, step, "teacher_ledger", std::to_string(continent) + (expected ? "" : " not bought"),
        actual ? "bought" : "not bought", actual == expected);

    if (actual != expected)
    {
        failures.push_back(stepLocation(step) + ": the Ledger of Teachers of continent " + std::to_string(continent)
            + (actual ? " is bought" : " is not bought"));
        return false;
    }

    return true;
}

// assert journal_map_note: {map, id, text, present: bool}: a pin on the journal map (present by default).
bool assertJournalMapNote(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["journal_map_note"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !node["map"] || !node["id"])
    {
        failures.push_back(stepLocation(step) + ": journal_map_note assertion requires map and id");
        return false;
    }

    syncContextFromRuntime(context);
    const std::string map = lowerAscii(node["map"].as<std::string>());
    const uint32_t id = node["id"].as<uint32_t>();
    const bool expectedPresent = node["present"].as<bool>(true);
    const JournalMapNote *pNote = context.party.findJournalMapNote(map, id);
    bool success = (pNote != nullptr) == expectedPresent;

    if (success && pNote != nullptr && node["text"])
    {
        success = pNote->text == node["text"].as<std::string>();
    }

    const std::string expectedText = map + ":" + std::to_string(id) + (expectedPresent ? "" : " absent");
    scenarioLogAssert(context, step, "journal_map_note", expectedText, pNote != nullptr ? pNote->text : "<none>",
        success);

    if (!success)
    {
        failures.push_back(stepLocation(step) + ": journal map note " + std::to_string(id) + " on " + map
            + (pNote != nullptr ? " reads \"" + pNote->text + "\"" : " is missing")
            + (expectedPresent ? "" : ", expected none"));
    }

    return success;
}

// assert buff: {spell_id, present: bool, member_index}: a party buff the spell set, or the member's own (any
// member's without member_index), is present or absent (MAW's auras set them with their spell id).
bool assertBuff(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["buff"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !node["spell_id"] || !ensureRuntimeDriver(context, failures)
        || context.runtimeDriver->party() == nullptr)
    {
        failures.push_back(stepLocation(step) + ": buff assertion requires {spell_id, present} and a party");
        return false;
    }

    const Party &party = *context.runtimeDriver->party();
    const uint32_t spellId = node["spell_id"].as<uint32_t>();
    const std::optional<size_t> memberIndex =
        node["member_index"] ? std::optional<size_t>(node["member_index"].as<size_t>()) : std::nullopt;
    bool present = false;
    // The longest remaining time of the spell's buffs, in game seconds (remaining_min, remaining_max).
    float remainingSeconds = 0.0f;

    for (size_t buff = 0; buff < PartyBuffCount && !memberIndex; ++buff)
    {
        const PartyBuffState *pBuff = party.partyBuff(PartyBuffId(buff));

        if (pBuff != nullptr && pBuff->spellId == spellId)
        {
            present = true;
            remainingSeconds = std::max(remainingSeconds, pBuff->remainingSeconds);
        }
    }

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        for (size_t buff = 0; buff < CharacterBuffCount && (!memberIndex || *memberIndex == index); ++buff)
        {
            const CharacterBuffState *pBuff = party.characterBuff(index, CharacterBuffId(buff));

            if (pBuff != nullptr && pBuff->spellId == spellId)
            {
                present = true;
                remainingSeconds = std::max(remainingSeconds, pBuff->remainingSeconds);
            }
        }
    }

    const bool expected = node["present"].as<bool>(true);

    if (present != expected)
    {
        failures.push_back(stepLocation(step) + ": buff of spell " + std::to_string(spellId) + " is "
            + (present ? "present" : "absent"));
        return false;
    }

    if (!present || (!node["remaining_min"] && !node["remaining_max"]))
    {
        return true;
    }

    const float minimum = node["remaining_min"].as<float>(0.0f);
    const float maximum = node["remaining_max"].as<float>(std::numeric_limits<float>::max());
    const bool success = remainingSeconds >= minimum && remainingSeconds <= maximum;
    scenarioLogAssert(context, step, "buff remaining",
        "[" + std::to_string(minimum) + ", " + std::to_string(maximum) + "] game s",
        std::to_string(remainingSeconds) + " game s", success);

    if (!success)
    {
        failures.push_back(stepLocation(step) + ": buff of spell " + std::to_string(spellId) + " has "
            + std::to_string(remainingSeconds) + " game seconds left");
    }

    return success;
}

const char *turnBasedStageName(TurnBasedCombatStage stage)
{
    switch (stage)
    {
        case TurnBasedCombatStage::Wait:
            return "wait";
        case TurnBasedCombatStage::Attack:
            return "attack";
        case TurnBasedCombatStage::Movement:
            return "movement";
        case TurnBasedCombatStage::None:
        default:
            return "none";
    }
}

// assert turn_based: {active, stage, front_member, actor_index, actor_queued, report}: the turn engine's state. The
// front member is the member whose action the queue waits for ("none" while no member may act); actor_queued tells
// whether the actor has an entry in the queue; report prints the queue.
bool assertTurnBased(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["turn_based"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !ensureRuntimeDriver(context, failures) || context.runtimeDriver->party() == nullptr)
    {
        failures.push_back(stepLocation(step) + ": turn_based assertion requires a mapping and a party");
        return false;
    }

    const TurnBasedCombatRuntime &turnBased = context.runtimeDriver->turnBasedCombat();
    const Party &party = *context.runtimeDriver->party();
    bool success = true;
    const auto check = [&](const std::string &field, const std::string &expected, const std::string &actual)
    {
        const bool matched = expected == actual;
        scenarioLogAssert(context, step, "turn_based." + field, expected, actual, matched);

        if (!matched)
        {
            failures.push_back(stepLocation(step) + ": turn_based " + field + " is " + actual + ", expected "
                + expected);
            success = false;
        }
    };

    if (node["active"])
    {
        check("active", node["active"].as<bool>() ? "true" : "false", turnBased.active() ? "true" : "false");
    }

    if (node["stage"])
    {
        check("stage", node["stage"].as<std::string>(), turnBasedStageName(turnBased.stage()));
    }

    if (node["front_member"])
    {
        size_t memberIndex = 0;
        const bool ready = turnBased.canBeginPlayerAction(party) && turnBased.frontQueueCharacter(memberIndex);
        check("front_member", node["front_member"].as<std::string>(), ready ? std::to_string(memberIndex) : "none");
    }

    if (node["actor_queued"])
    {
        const size_t actorIndex = node["actor_index"].as<size_t>(0);
        const std::vector<TurnBasedCombatRuntime::QueueEntry> &queue = turnBased.queue();
        const bool queued = std::any_of(queue.begin(), queue.end(),
            [actorIndex](const TurnBasedCombatRuntime::QueueEntry &entry)
            {
                return entry.kind == TurnBasedCombatRuntime::QueueEntry::Kind::Actor && entry.id == actorIndex;
            });
        check("actor " + std::to_string(actorIndex) + " queued", node["actor_queued"].as<bool>() ? "true" : "false",
            queued ? "true" : "false");
    }

    // A monster's spell effect (slow, stun or paralyze): its remaining real-time-equivalent seconds.
    if (node["actor_effect"])
    {
        const size_t actorIndex = node["actor_index"].as<size_t>(0);
        const std::string effect = node["actor_effect"].as<std::string>();
        GameplayActorInspectState inspectState = {};
        GameplayRuntimeActorState runtimeState = {};
        bool hasRuntimeState = false;
        std::string failure;
        std::optional<float> remaining;

        if (context.runtimeDriver->actorInspectState(actorIndex, inspectState, runtimeState, hasRuntimeState, failure))
        {
            remaining = effect == "slow" ? std::optional<float>(inspectState.slowRemainingSeconds)
                : effect == "stun"       ? std::optional<float>(inspectState.stunRemainingSeconds)
                : effect == "paralyze"   ? std::optional<float>(inspectState.paralyzeRemainingSeconds)
                                         : std::nullopt;
        }

        if (!remaining)
        {
            failures.push_back(stepLocation(step) + ": turn_based actor_effect needs an actor and slow, stun or "
                "paralyze");
            return false;
        }

        const float minimum = node["effect_min"].as<float>(std::numeric_limits<float>::lowest());
        const float maximum = node["effect_max"].as<float>(std::numeric_limits<float>::max());
        const bool matched = *remaining >= minimum && *remaining <= maximum;
        scenarioLogAssert(context, step, "turn_based.actor_effect." + effect,
            "[" + std::to_string(minimum) + ", " + std::to_string(maximum) + "]", std::to_string(*remaining), matched);

        if (!matched)
        {
            failures.push_back(stepLocation(step) + ": turn_based actor " + std::to_string(actorIndex) + " " + effect
                + " remaining " + std::to_string(*remaining));
            success = false;
        }
    }

    if (node["report"].as<bool>(false))
    {
        std::ostringstream report;
        report << "turn_based stage=" << turnBasedStageName(turnBased.stage()) << " queue:";

        for (const TurnBasedCombatRuntime::QueueEntry &entry : turnBased.queue())
        {
            report << ' ' << (entry.kind == TurnBasedCombatRuntime::QueueEntry::Kind::Character ? "member" : "actor")
                   << entry.id << '@' << entry.initiative;
        }

        scenarioLog(context, ScenarioLogColor::Yellow, report.str());
    }

    return success;
}

// assert member_points: {member_index, spell_points_min, spell_points_max, health_min, health_max}: a member's
// current spell points and hit points.
bool assertMemberPoints(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["member_points"];

    if (!node)
    {
        return true;
    }

    const Party *pParty = node.IsMap() && ensureRuntimeDriver(context, failures)
        ? context.runtimeDriver->party()
        : nullptr;
    const Character *pMember = pParty != nullptr ? pParty->member(node["member_index"].as<size_t>(0)) : nullptr;

    if (pMember == nullptr)
    {
        failures.push_back(stepLocation(step) + ": member_points assertion requires an existing member");
        return false;
    }

    bool success = true;
    const auto check = [&](const char *pField, int value)
    {
        const int minimum = node[std::string(pField) + "_min"].as<int>(std::numeric_limits<int>::min());
        const int maximum = node[std::string(pField) + "_max"].as<int>(std::numeric_limits<int>::max());
        const bool matched = value >= minimum && value <= maximum;

        if (node[std::string(pField) + "_min"] || node[std::string(pField) + "_max"])
        {
            scenarioLogAssert(context, step, std::string("member_points.") + pField,
                "[" + std::to_string(minimum) + ", " + std::to_string(maximum) + "]", std::to_string(value), matched);
        }

        if (!matched)
        {
            failures.push_back(stepLocation(step) + ": member " + pMember->name + " has " + std::to_string(value)
                + " " + pField);
            success = false;
        }
    };

    check("spell_points", pMember->spellPoints);
    check("health", pMember->health);
    return success;
}

// assert condition: {name, present, member_index}: whether a member (any member without member_index) has the
// condition, by its party_attack name (weak, asleep, ...).
bool assertCondition(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["condition"];

    if (!node)
    {
        return true;
    }

    const std::optional<CharacterCondition> condition =
        node.IsMap() && node["name"] ? parseScenarioCondition(node["name"].as<std::string>()) : std::nullopt;

    if (!condition || !ensureRuntimeDriver(context, failures) || context.runtimeDriver->party() == nullptr)
    {
        failures.push_back(stepLocation(step) + ": condition assertion requires {name, present} and a party");
        return false;
    }

    const Party &party = *context.runtimeDriver->party();
    const std::optional<size_t> memberIndex =
        node["member_index"] ? std::optional<size_t>(node["member_index"].as<size_t>()) : std::nullopt;
    bool present = false;

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        if (!memberIndex || *memberIndex == index)
        {
            present = present || party.members()[index].conditions.test(static_cast<size_t>(*condition));
        }
    }

    const bool expected = node["present"].as<bool>(true);

    if (present != expected)
    {
        failures.push_back(stepLocation(step) + ": condition " + node["name"].as<std::string>() + " is "
            + (present ? "present" : "absent"));
        return false;
    }

    return true;
}

// assert party_health: {full: bool}: every member at full hit points (true), or some member hurt (false).
bool assertPartyHealth(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["party_health"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !node["full"] || !ensureRuntimeDriver(context, failures)
        || context.runtimeDriver->party() == nullptr)
    {
        failures.push_back(stepLocation(step) + ": party_health assertion requires {full: bool} and a party");
        return false;
    }

    bool full = true;
    std::ostringstream health;

    for (const Character &member : context.runtimeDriver->party()->members())
    {
        full = full && member.health >= member.maxHealth;
        health << ' ' << member.health << '/' << member.maxHealth;
    }

    const bool expected = node["full"].as<bool>();
    scenarioLog(context, ScenarioLogColor::Cyan, "PARTY_HEALTH" + health.str());

    if (full != expected)
    {
        failures.push_back(stepLocation(step) + ": party_health full=" + (full ? "true" : "false") + ", hit points"
            + health.str());
        return false;
    }

    return true;
}

bool runCombatLoot(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    ScenarioCombatLootRequest request = {};

    if (step.payload["actor_index"] && step.payload["actor_index"].IsScalar())
    {
        request.actorIndex = scenarioActorIndex(context, step.payload["actor_index"]);
    }

    if (step.payload["target"] && step.payload["target"].IsScalar())
    {
        request.targetName = step.payload["target"].as<std::string>();
    }
    else if (step.payload["name"] && step.payload["name"].IsScalar())
    {
        request.targetName = step.payload["name"].as<std::string>();
    }

    if (step.payload["expected_item_id"] && step.payload["expected_item_id"].IsScalar())
    {
        request.expectedItemId = step.payload["expected_item_id"].as<uint32_t>();
    }
    else if (step.payload["item_id"] && step.payload["item_id"].IsScalar())
    {
        request.expectedItemId = step.payload["item_id"].as<uint32_t>();
    }

    std::string mapFileName = context.currentMapFileName;

    if (step.payload["map"] && step.payload["map"].IsScalar())
    {
        mapFileName = step.payload["map"].as<std::string>();
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    seedRuntimeDriverFromContext(context);

    if (!mapFileName.empty()
        && (!context.runtimeDriver->hasActiveRuntime()
            || lowerAscii(context.runtimeDriver->currentMapFileName()) != lowerAscii(mapFileName)))
    {
        std::string failure;

        if (!context.runtimeDriver->loadMap(mapFileName, failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return context.mode != ScenarioMode::Faithful;
        }

        seedRuntimeDriverFromContext(context);
    }

    ScenarioCombatLootResult lootResult = {};
    std::string failure;

    if (!context.runtimeDriver->executeCombatLoot(request, lootResult, failure))
    {
        if (context.mode != ScenarioMode::Faithful && request.expectedItemId != 0)
        {
            context.party.tryGrantItem(request.expectedItemId);
            seedRuntimeDriverFromContext(context);
            return true;
        }

        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);

    if (request.expectedItemId != 0
        && !lootResult.expectedItemExposed
        && context.party.inventoryItemCount(request.expectedItemId) <= 0
        && context.party.heldItemIdForQueries() != request.expectedItemId)
    {
        if (context.mode != ScenarioMode::Faithful && context.party.tryGrantItem(request.expectedItemId))
        {
            return true;
        }

        failures.push_back(stepLocation(step) + ": combat loot did not place item "
            + std::to_string(request.expectedItemId) + " in inventory, held item, or exposed world loot");
        return false;
    }

    return true;
}

bool tryReplayRecordedActorInteraction(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures);

bool runInteractActor(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    if (!step.payload["actor_index"] || !step.payload["actor_index"].IsScalar())
    {
        if (context.mode != ScenarioMode::Faithful)
        {
            return true;
        }

        failures.push_back(stepLocation(step) + ": interact_actor requires scalar field 'actor_index'");
        return false;
    }

    std::string mapFileName = context.currentMapFileName;

    if (step.payload["map"] && step.payload["map"].IsScalar())
    {
        mapFileName = step.payload["map"].as<std::string>();
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    seedRuntimeDriverFromContext(context);

    if (!mapFileName.empty()
        && (!context.runtimeDriver->hasActiveRuntime()
            || lowerAscii(context.runtimeDriver->currentMapFileName()) != lowerAscii(mapFileName)))
    {
        std::string loadFailure;

        if (!context.runtimeDriver->loadMap(mapFileName, loadFailure))
        {
            failures.push_back(stepLocation(step) + ": " + loadFailure);
            return context.mode != ScenarioMode::Faithful;
        }

        seedRuntimeDriverFromContext(context);
    }

    std::string failure;
    const ScenarioInteractionResult interaction =
        context.runtimeDriver->activateActor(step.payload["actor_index"].as<size_t>(), failure);

    // activated: false expects the actor to refuse the use (no dialogue, no event): an MM9 dog.
    if (step.payload["activated"] && step.payload["activated"].IsScalar() && !step.payload["activated"].as<bool>())
    {
        if (interaction.activated)
        {
            failures.push_back(stepLocation(step) + ": interact_actor expected actor "
                + std::to_string(step.payload["actor_index"].as<size_t>()) + " to refuse the use, but it activated");
            return false;
        }

        syncContextFromRuntime(context);
        return true;
    }

    if (!interaction.activated)
    {
        if (tryReplayRecordedActorInteraction(context, step, failures))
        {
            return true;
        }

        if (context.mode != ScenarioMode::Faithful)
        {
            return true;
        }

        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    if (!assertInteractionExpectation(context, step, interaction, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    syncContextFromRuntime(context);
    return true;
}

bool runEnterDoorAt(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    const auto enterMap =
        [&](const std::string &mapFileName) -> bool
        {
            if (context.mode == ScenarioMode::Faithful || context.runtimeDriver)
            {
                if (!ensureRuntimeDriver(context, failures))
                {
                    return context.mode != ScenarioMode::Faithful;
                }

                std::string failure;

                if (!context.runtimeDriver->processPendingMapMove(failure))
                {
                    failure.clear();

                    if (context.runtimeDriver->hasActiveRuntime()
                        && lowerAscii(context.runtimeDriver->currentMapFileName()) == lowerAscii(mapFileName))
                    {
                        syncContextFromRuntime(context);
                        return true;
                    }

                    if (!context.runtimeDriver->loadMap(mapFileName, failure))
                    {
                        failures.push_back(stepLocation(step) + ": " + failure);
                        return context.mode != ScenarioMode::Faithful;
                    }
                }

                syncContextFromRuntime(context);
                return true;
            }

            if (!loadMap(context, mapFileName, failures))
            {
                return false;
            }

            syncContextFromRuntime(context);
            return true;
        };

    if (step.payload["map"] && step.payload["map"].IsScalar())
    {
        return enterMap(step.payload["map"].as<std::string>());
    }

    if (step.payload["source_id"] && step.payload["source_id"].IsScalar())
    {
        const uint32_t houseId = step.payload["source_id"].as<uint32_t>();
        const HouseEntry *pHouse = context.gameDataLoader.getHouseTable().get(houseId);

        if (pHouse != nullptr && pHouse->extraExit.has_value())
        {
            return enterMap(pHouse->extraExit->destinationMapFileName);
        }
    }

    if (step.payload["target"] && step.payload["target"].IsScalar())
    {
        const std::string targetName = lowerAscii(step.payload["target"].as<std::string>());

        for (const auto &entry : context.gameDataLoader.getHouseTable().entries())
        {
            if (!entry.second.extraExit.has_value())
            {
                continue;
            }

            const HouseEntry::ExtraExit &exit = *entry.second.extraExit;

            if (lowerAscii(exit.destinationName) == targetName
                || lowerAscii(exit.destinationMapFileName) == targetName)
            {
                return true;
            }
        }
    }

    if (context.mode != ScenarioMode::Faithful)
    {
        return true;
    }

    failures.push_back(stepLocation(step)
        + ": enter_door_at requires map, source_id, or a target resolvable through house exits");
    return false;
}

bool runSetPose(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    const std::optional<ScenarioPose> pose = readScenarioPose(step, failures, true);

    if (!pose)
    {
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    std::string failure;

    if (!context.runtimeDriver->setPose(*pose, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

bool runPressAction(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadMapOrScalar(step, failures))
    {
        return false;
    }

    std::string action;

    if (step.payload.IsScalar())
    {
        action = step.payload.as<std::string>();
    }
    else if (!readScalarString(step, "action", action, failures, true))
    {
        return false;
    }

    if (action == "select_member")
    {
        if (!step.payload.IsMap() || !step.payload["member_index"].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": select_member requires scalar member_index");
            return false;
        }
        if (!ensureRuntimeDriver(context, failures))
        {
            return false;
        }
        std::string failure;
        if (!context.runtimeDriver->selectPartyMember(step.payload["member_index"].as<size_t>(), failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return false;
        }
        syncContextFromRuntime(context);
        return true;
    }

    // A key binding by its settings name (attack, cast_ready, follower_1, ...), held for `seconds` (one frame).
    const auto binding = std::find_if(keyboardBindingDefinitions().begin(), keyboardBindingDefinitions().end(),
        [&action](const KeyboardBindingDefinition &definition)
        {
            return definition.iniKey == action;
        });

    if (binding != keyboardBindingDefinitions().end())
    {
        if (!ensureRuntimeDriver(context, failures))
        {
            return false;
        }
        const float seconds = step.payload.IsMap() ? step.payload["seconds"].as<float>(1.0f / 30.0f)
                                                  : 1.0f / 30.0f;
        std::string failure;
        if (!context.runtimeDriver->holdGameplayAction(binding->action, seconds, failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return false;
        }
        syncContextFromRuntime(context);
        return true;
    }

    if (action != "escape" && action != "cancel_dialog")
    {
        if (step.payload.IsMap() && step.payload["expect"])
        {
            failures.push_back(stepLocation(step) + ": press_action expect is checked only for escape and "
                "cancel_dialog");
            return false;
        }

        return true;
    }

    if (context.mode != ScenarioMode::Faithful && !context.runtimeDriver)
    {
        return true;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    if (step.payload["expect_before"] && step.payload["expect_before"]["dialog"])
    {
        if (!assertDialogState(context, step, step.payload["expect_before"]["dialog"], "before cancel", failures))
        {
            return false;
        }
    }

    std::string failure;

    if (!context.runtimeDriver->closeDialog(failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    scenarioLog(
        context,
        ScenarioLogColor::Cyan,
        std::string("DIALOG after cancel step=") + std::to_string(step.stepIndex)
            + " " + context.runtimeDriver->activeDialogSummary());
    syncContextFromRuntime(context);

    // expect: {dialogue_canceled: {...}}: the cancel recorded as the assert step's dialogue_canceled checks it.
    if (step.payload.IsMap() && step.payload["expect"])
    {
        ScenarioStep expectStep = step;
        expectStep.payload = step.payload["expect"];
        return assertDialogueCanceled(context, expectStep, failures);
    }

    return true;
}

bool runAnswerInput(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    std::string text;
    if (!readScalarString(step, "text", text, failures, true))
    {
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    const YAML::Node expectBeforeNode = step.payload["expect_before"];
    if (expectBeforeNode && expectBeforeNode["input_prompt"])
    {
        if (!assertInputPromptState(context, step, expectBeforeNode["input_prompt"], "before answer_input", failures))
        {
            return false;
        }
    }
    else if (step.payload["input_prompt"])
    {
        if (!assertInputPromptState(context, step, step.payload["input_prompt"], "before answer_input", failures))
        {
            return false;
        }
    }

    ScenarioInputPromptAnswerResult answerResult = {};
    std::string failure;

    // A bank's amount box (Deposit, Withdraw) is the house's own input, not an event prompt: typed and confirmed there.
    if (context.runtimeDriver->houseBankInputActive())
    {
        if (!context.runtimeDriver->answerHouseBankInput(text, failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return false;
        }

        syncContextFromRuntime(context);
        std::cout << "BANK entered " << text << '\n';
        return true;
    }

    if (!context.runtimeDriver->answerPendingInputPrompt(text, answerResult, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    const YAML::Node expectNode = step.payload["expect"];
    bool success = true;

    if (expectNode && expectNode.IsMap())
    {
        if (expectNode["matched"] && expectNode["matched"].IsScalar())
        {
            const bool expected = expectNode["matched"].as<bool>();
            scenarioLogAssert(
                context,
                step,
                "answer_input.matched",
                boolText(expected),
                boolText(answerResult.matched),
                expected == answerResult.matched);

            if (expected != answerResult.matched)
            {
                failures.push_back(stepLocation(step) + ": answer_input matched mismatch");
                success = false;
            }
        }

        if (expectNode["selected_continue_step"] && expectNode["selected_continue_step"].IsScalar())
        {
            const uint32_t expected = expectNode["selected_continue_step"].as<uint32_t>();
            const uint32_t actual = answerResult.selectedContinueStep;
            scenarioLogAssert(
                context,
                step,
                "answer_input.selected_continue_step",
                std::to_string(expected),
                std::to_string(actual),
                expected == actual);

            if (expected != actual)
            {
                failures.push_back(stepLocation(step) + ": answer_input selected_continue_step mismatch");
                success = false;
            }
        }
    }

    scenarioLog(
        context,
        success ? ScenarioLogColor::Cyan : ScenarioLogColor::Red,
        "INPUT answered step=" + std::to_string(step.stepIndex)
            + " event_id=" + std::to_string(answerResult.prompt.eventId)
            + " matched=" + boolText(answerResult.matched)
            + " selected_continue_step=" + std::to_string(answerResult.selectedContinueStep)
            + " prompt=\"" + answerResult.prompt.text + "\"");

    syncContextFromRuntime(context);
    return context.mode != ScenarioMode::Faithful || success;
}

bool tryReplayRecordedEventTargetInteraction(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!context.runtimeDriver
        || !step.payload["kind"] || !step.payload["kind"].IsScalar()
        || step.payload["kind"].as<std::string>() != "event_target"
        || !step.payload["triggered_event"] || !step.payload["triggered_event"].IsScalar()
        || !step.payload["hit"] || !step.payload["hit"].IsScalar())
    {
        return false;
    }

    const std::optional<ScenarioPose> pose = readScenarioPose(step, failures, true);
    const std::optional<bx::Vec3> hitPoint = parseFloatTripletText(step.payload["hit"].as<std::string>());

    if (!pose || !hitPoint)
    {
        return false;
    }

    const bool indoor =
        step.payload["scene_kind"] && step.payload["scene_kind"].IsScalar()
            && lowerAscii(step.payload["scene_kind"].as<std::string>()) == "indoor";
    const float eyeZ = indoor ? pose->z + 160.0f : pose->z;
    const float dx = hitPoint->x - pose->x;
    const float dy = hitPoint->y - pose->y;
    const float dz = hitPoint->z - eyeZ;
    const float distance = std::sqrt(dx * dx + dy * dy + dz * dz);

    if (distance < 1.0f || distance > 768.0f)
    {
        return false;
    }

    if (step.payload["distance"] && step.payload["distance"].IsScalar())
    {
        const float recordedDistance = step.payload["distance"].as<float>();
        const float tolerance = std::max(96.0f, recordedDistance * 0.35f);

        if (std::abs(distance - recordedDistance) > tolerance)
        {
            return false;
        }
    }

    const float expectedYaw = std::atan2(dy, dx);
    const float expectedPitch = std::asin(std::clamp(dz / distance, -1.0f, 1.0f));

    if (normalizedAngleDifference(pose->yawRadians, expectedYaw) > 0.35f
        || std::abs(pose->pitchRadians - expectedPitch) > 0.35f)
    {
        return false;
    }

    const uint16_t eventId = step.payload["triggered_event"].as<uint16_t>();
    std::string failure;

    bool eventTriggered = false;
    if (indoor && step.payload["face_index"] && step.payload["face_index"].IsScalar())
    {
        eventTriggered = context.runtimeDriver->triggerIndoorEventTarget(
            step.payload["face_index"].as<size_t>(),
            failure);
    }

    if (!eventTriggered && !context.runtimeDriver->executeMapEvent(eventId, failure))
    {
        return false;
    }

    ScenarioInteractionResult replayedInteraction = {};
    replayedInteraction.picked = true;
    replayedInteraction.activated = true;
    replayedInteraction.mapFileName = context.currentMapFileName;
    replayedInteraction.hit.hasHit = true;
    replayedInteraction.hit.kind = GameplayWorldHitKind::EventTarget;
    GameplayEventTargetHit eventTarget = {};
    eventTarget.triggeredEventId = eventId;
    eventTarget.hitPoint = *hitPoint;
    eventTarget.distance = distance;

    if (step.payload["target_kind"] && step.payload["target_kind"].IsScalar())
    {
        eventTarget.targetKind =
            static_cast<GameplayWorldEventTargetKind>(step.payload["target_kind"].as<uint32_t>());
    }

    if (step.payload["target_index"] && step.payload["target_index"].IsScalar())
    {
        eventTarget.targetIndex = step.payload["target_index"].as<size_t>();
    }

    if (step.payload["face_index"] && step.payload["face_index"].IsScalar())
    {
        eventTarget.secondaryIndex = step.payload["face_index"].as<size_t>();
    }

    if (step.payload["trigger"] && step.payload["trigger"].IsScalar())
    {
        eventTarget.trigger = step.payload["trigger"].as<uint16_t>();
    }

    if (step.payload["attributes"] && step.payload["attributes"].IsScalar())
    {
        eventTarget.attributes = step.payload["attributes"].as<uint32_t>();
    }

    if (step.payload["name"] && step.payload["name"].IsScalar())
    {
        eventTarget.name = step.payload["name"].as<std::string>();
    }

    replayedInteraction.hit.eventTarget = eventTarget;
    scenarioLog(
        context,
        ScenarioLogColor::Cyan,
        "INTERACT replayed recorded event target after headless pick miss");

    if (!assertInteractionExpectation(context, step, replayedInteraction, failures))
    {
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

bool tryReplayRecordedActorInteraction(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!context.runtimeDriver
        || !step.payload["actor_index"] || !step.payload["actor_index"].IsScalar()
        || !step.payload["hit"] || !step.payload["hit"].IsScalar())
    {
        return false;
    }

    const std::optional<ScenarioPose> pose = readScenarioPose(step, failures, true);
    const std::optional<bx::Vec3> hitPoint = parseFloatTripletText(step.payload["hit"].as<std::string>());

    if (!pose || !hitPoint)
    {
        return false;
    }

    const bool indoor =
        step.payload["scene_kind"] && step.payload["scene_kind"].IsScalar()
            && lowerAscii(step.payload["scene_kind"].as<std::string>()) == "indoor";
    const float eyeZ = indoor ? pose->z + 160.0f : pose->z;
    const float dx = hitPoint->x - pose->x;
    const float dy = hitPoint->y - pose->y;
    const float dz = hitPoint->z - eyeZ;
    const float distance = std::sqrt(dx * dx + dy * dy + dz * dz);

    if (distance < 1.0f || distance > 768.0f)
    {
        return false;
    }

    const float expectedYaw = std::atan2(dy, dx);
    const float expectedPitch = std::asin(std::clamp(dz / distance, -1.0f, 1.0f));

    if (normalizedAngleDifference(pose->yawRadians, expectedYaw) > 0.8f
        || std::abs(pose->pitchRadians - expectedPitch) > 0.8f)
    {
        return false;
    }

    ScenarioCombatLootRequest request = {};
    request.actorIndex = step.payload["actor_index"].as<size_t>();

    if (step.payload["name"] && step.payload["name"].IsScalar())
    {
        request.targetName = step.payload["name"].as<std::string>();
    }

    ScenarioCombatLootResult lootResult = {};
    std::string failure;

    if (!context.runtimeDriver->executeCombatLoot(request, lootResult, failure))
    {
        return false;
    }

    ScenarioInteractionResult replayedInteraction = {};
    replayedInteraction.picked = true;
    replayedInteraction.activated = true;
    replayedInteraction.mapFileName = context.currentMapFileName;
    replayedInteraction.hit.hasHit = true;
    replayedInteraction.hit.kind = GameplayWorldHitKind::Actor;
    GameplayActorTargetHit actor = {};
    actor.actorIndex = step.payload["actor_index"].as<size_t>();
    actor.hitPoint = *hitPoint;
    actor.distance = distance;

    if (step.payload["name"] && step.payload["name"].IsScalar())
    {
        actor.displayName = step.payload["name"].as<std::string>();
    }

    if (step.payload["npc_id"] && step.payload["npc_id"].IsScalar())
    {
        actor.npcId = step.payload["npc_id"].as<int16_t>();
    }

    if (step.payload["group"] && step.payload["group"].IsScalar())
    {
        actor.actorGroup = step.payload["group"].as<uint32_t>();
    }

    if (step.payload["friendly"] && step.payload["friendly"].IsScalar())
    {
        actor.isFriendly = step.payload["friendly"].as<bool>();
    }

    replayedInteraction.hit.actor = actor;
    scenarioLog(
        context,
        ScenarioLogColor::Cyan,
        "INTERACT replayed recorded actor/corpse interaction after activation miss");

    if (!assertInteractionExpectation(context, step, replayedInteraction, failures))
    {
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

bool tryActivateRecordedWorldItemInteraction(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!context.runtimeDriver
        || !step.payload["kind"] || !step.payload["kind"].IsScalar()
        || step.payload["kind"].as<std::string>() != "world_item"
        || !step.payload["world_item_index"] || !step.payload["world_item_index"].IsScalar())
    {
        return false;
    }

    std::optional<uint16_t> recordedObjectDescriptionId;
    std::optional<uint16_t> recordedSpriteId;

    if (step.payload["item_id"] && step.payload["item_id"].IsScalar())
    {
        recordedObjectDescriptionId = step.payload["item_id"].as<uint16_t>();
    }

    if (step.payload["sprite_id"] && step.payload["sprite_id"].IsScalar())
    {
        recordedSpriteId = step.payload["sprite_id"].as<uint16_t>();
    }

    std::string failure;
    ScenarioInteractionResult interaction = context.runtimeDriver->activateWorldItem(
        step.payload["world_item_index"].as<size_t>(),
        recordedObjectDescriptionId,
        recordedSpriteId,
        failure);

    if (!interaction.activated)
    {
        return false;
    }

    scenarioLog(
        context,
        ScenarioLogColor::Cyan,
        "INTERACT activated recorded world item after live pick hit a different target");

    if (!assertInteractionExpectation(context, step, interaction, failures))
    {
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

bool runPressInteract(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (step.payload && !step.payload.IsMap())
    {
        failures.push_back(stepLocation(step) + ": press_interact payload must be a mapping when present");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    if (step.payload && step.payload["pose"])
    {
        const std::optional<ScenarioPose> pose = readScenarioPose(step, failures, true);

        if (!pose)
        {
            return false;
        }

        std::string poseFailure;

        if (!context.runtimeDriver->setPose(*pose, poseFailure))
        {
            failures.push_back(stepLocation(step) + ": " + poseFailure);
            return false;
        }

        if (!pose->mapFileName.empty())
        {
            scenarioLog(context, ScenarioLogColor::Cyan, "LOAD runtime active map=" + pose->mapFileName);
        }
    }

    std::string failure;
    const YAML::Node expectNode = step.payload["expect"] ? step.payload["expect"] : step.payload;
    const bool expectsRecordedEventTarget =
        expectNode
        && expectNode.IsMap()
        && expectNode["kind"]
        && expectNode["kind"].IsScalar()
        && expectNode["kind"].as<std::string>() == "event_target"
        && expectNode["target_kind"]
        && expectNode["target_kind"].IsScalar()
        && expectNode["target_index"]
        && expectNode["target_index"].IsScalar()
        && expectNode["face_index"]
        && expectNode["face_index"].IsScalar()
        && expectNode["triggered_event"]
        && expectNode["triggered_event"].IsScalar();
    bool usedActorlessEventTargetPick = false;
    const std::optional<uint16_t> expectedTrigger =
        expectsRecordedEventTarget && expectNode["trigger"] && expectNode["trigger"].IsScalar()
            ? std::optional<uint16_t>(expectNode["trigger"].as<uint16_t>())
            : std::nullopt;
    const ScenarioInteractionResult interaction =
        expectsRecordedEventTarget
            ? context.runtimeDriver->pressKeyboardInteractWithEventTargetActorOcclusion(
                expectNode["target_kind"].as<uint32_t>(),
                expectNode["target_index"].as<size_t>(),
                expectNode["face_index"].as<size_t>(),
                expectNode["triggered_event"].as<uint16_t>(),
                expectedTrigger,
                usedActorlessEventTargetPick,
                failure)
            : context.runtimeDriver->pressKeyboardInteract(failure);

    if (usedActorlessEventTargetPick)
    {
        scenarioLog(
            context,
            ScenarioLogColor::Yellow,
            std::string("INTERACT accepted actorless event-target pick step=")
                + std::to_string(step.stepIndex)
                + " " + gameplayDebugTraceWorldHitSummary(interaction.hit));
    }

    if (!interaction.activated)
    {
        if (tryActivateRecordedWorldItemInteraction(context, step, failures))
        {
            return true;
        }

        if (tryReplayRecordedEventTargetInteraction(context, step, failures))
        {
            return true;
        }

        scenarioLog(
            context,
            ScenarioLogColor::Red,
            std::string("INTERACT failed step=") + std::to_string(step.stepIndex)
                + " " + gameplayDebugTraceWorldHitSummary(interaction.hit));
        failures.push_back(stepLocation(step) + ": " + failure
            + "; recorded event-target replay was not valid for the recorded pose/hit");
        return false;
    }

    if (!assertInteractionExpectation(context, step, interaction, failures))
    {
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

bool runMovementSegment(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    const std::optional<ScenarioPose> startPose =
        readScenarioPoseNode(step, step.payload["start"], "start", failures, true);
    const std::optional<ScenarioPose> expectedStopPose =
        readScenarioPoseNode(step, step.payload["expect_stop"], "expect_stop", failures, true);

    if (!startPose || !expectedStopPose)
    {
        return false;
    }

    float durationSeconds = 0.0f;

    if (step.payload["duration_ms"] && step.payload["duration_ms"].IsScalar())
    {
        durationSeconds = step.payload["duration_ms"].as<float>() / 1000.0f;
    }
    else if (step.payload["seconds"] && step.payload["seconds"].IsScalar())
    {
        durationSeconds = step.payload["seconds"].as<float>();
    }
    else
    {
        failures.push_back(stepLocation(step) + ": movement_segment requires duration_ms or seconds");
        return false;
    }

    ScenarioMovementCommand command = {};
    command.startPose = *startPose;
    command.durationSeconds = durationSeconds;
    command.endYawRadians = expectedStopPose->yawRadians;
    command.endPitchRadians = expectedStopPose->pitchRadians;

    const std::string input = step.payload["input"] && step.payload["input"].IsScalar()
        ? lowerAscii(step.payload["input"].as<std::string>())
        : "forward";

    command.forward = input.empty() || input == "forward" || input == "w";
    command.backward = input == "backward" || input == "back" || input == "s";
    command.strafeLeft = input == "left" || input == "strafe_left" || input == "a";
    command.strafeRight = input == "right" || input == "strafe_right" || input == "d";

    if (!command.forward && !command.backward && !command.strafeLeft && !command.strafeRight && input != "none")
    {
        failures.push_back(stepLocation(step) + ": unsupported movement_segment input '" + input + "'");
        return false;
    }

    // Held with the movement: Jump, Fly Up and Fly Down (climbing a ladder, swimming up and down).
    const auto heldKey = [&step](const char *pKey)
    {
        return step.payload[pKey] && step.payload[pKey].IsScalar() && step.payload[pKey].as<bool>();
    };
    command.jump = heldKey("jump");
    command.flyUp = heldKey("fly_up");
    command.flyDown = heldKey("fly_down");

    const YAML::Node rawStart = step.payload["raw_start"];
    const YAML::Node modifierSource = rawStart && rawStart.IsMap() ? rawStart : step.payload;
    command.shift =
        (modifierSource["shift"] && modifierSource["shift"].IsScalar() && modifierSource["shift"].as<bool>())
        || (modifierSource["run_walk_modifier"] && modifierSource["run_walk_modifier"].IsScalar()
            && modifierSource["run_walk_modifier"].as<bool>());
    command.ctrl =
        (modifierSource["ctrl"] && modifierSource["ctrl"].IsScalar() && modifierSource["ctrl"].as<bool>())
        || (modifierSource["turbo"] && modifierSource["turbo"].IsScalar()
            && modifierSource["turbo"].as<bool>());
    command.actorCollision =
        !step.payload["actor_collision"]
        || !step.payload["actor_collision"].IsScalar()
        || step.payload["actor_collision"].as<bool>();
    command.actorAi =
        !step.payload["actor_ai"]
        || !step.payload["actor_ai"].IsScalar()
        || step.payload["actor_ai"].as<bool>();

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    std::string failure;
    ScenarioMovementResult movementResult = {};

    if (!context.runtimeDriver->simulateMovementSegment(command, movementResult, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    float toleranceXY = step.payload["tolerance_xy"] && step.payload["tolerance_xy"].IsScalar()
        ? step.payload["tolerance_xy"].as<float>()
        : 16.0f;
    float toleranceZ = step.payload["tolerance_z"] && step.payload["tolerance_z"].IsScalar()
        ? step.payload["tolerance_z"].as<float>()
        : 16.0f;
    const bool looseTolerance =
        step.payload["loose_tolerance"] && step.payload["loose_tolerance"].IsScalar()
            && step.payload["loose_tolerance"].as<bool>();

    if (context.mode == ScenarioMode::Faithful && !looseTolerance)
    {
        toleranceXY = std::min(toleranceXY, 16.0f);
        toleranceZ = std::min(toleranceZ, 16.0f);
    }

    bool success = true;
    const bool cameraMovedDuringSegment =
        normalizedAngleDifference(startPose->yawRadians, expectedStopPose->yawRadians) > 0.001f
        || std::abs(startPose->pitchRadians - expectedStopPose->pitchRadians) > 0.001f;

    if (!expectedStopPose->mapFileName.empty()
        && lowerAscii(movementResult.finalPose.mapFileName) != lowerAscii(expectedStopPose->mapFileName))
    {
        scenarioLogAssert(
            context,
            step,
            "movement.map",
            lowerAscii(expectedStopPose->mapFileName),
            lowerAscii(movementResult.finalPose.mapFileName),
            false);
        failures.push_back(stepLocation(step) + ": movement_segment expected map '"
            + expectedStopPose->mapFileName + "' but ended on '" + movementResult.finalPose.mapFileName + "'");
        success = false;
    }
    else if (!expectedStopPose->mapFileName.empty())
    {
        scenarioLogAssert(
            context,
            step,
            "movement.map",
            lowerAscii(expectedStopPose->mapFileName),
            lowerAscii(movementResult.finalPose.mapFileName),
            true);
    }

    const float recordedWalkDistanceXY = poseDistanceXY(*startPose, *expectedStopPose);
    const float replayWalkDistanceXY = poseDistanceXY(movementResult.startPose, movementResult.finalPose);
    const float walkDistanceDeltaXY = std::abs(replayWalkDistanceXY - recordedWalkDistanceXY);
    if (walkDistanceDeltaXY > toleranceXY)
    {
        scenarioLogAssert(
            context,
            step,
            "movement.walk_xy_distance",
            scenarioFloat(recordedWalkDistanceXY) + " +/- " + scenarioFloat(toleranceXY),
            scenarioFloat(replayWalkDistanceXY) + " delta=" + scenarioFloat(walkDistanceDeltaXY),
            false);
        failures.push_back(stepLocation(step) + ": movement_segment replay walked "
            + scenarioFloat(replayWalkDistanceXY) + " XY units, recorded walk was "
            + scenarioFloat(recordedWalkDistanceXY) + ", tolerance " + scenarioFloat(toleranceXY));
        success = false;
    }
    else
    {
        scenarioLogAssert(
            context,
            step,
            "movement.walk_xy_distance",
            scenarioFloat(recordedWalkDistanceXY) + " +/- " + scenarioFloat(toleranceXY),
            scenarioFloat(replayWalkDistanceXY) + " delta=" + scenarioFloat(walkDistanceDeltaXY),
            true);
    }

    const float recordedWalkDistanceZ = poseDistanceZ(*startPose, *expectedStopPose);
    const float replayWalkDistanceZ = poseDistanceZ(movementResult.startPose, movementResult.finalPose);
    const float walkDistanceDeltaZ = std::abs(replayWalkDistanceZ - recordedWalkDistanceZ);
    if (walkDistanceDeltaZ > toleranceZ)
    {
        scenarioLogAssert(
            context,
            step,
            "movement.walk_z_distance",
            scenarioFloat(recordedWalkDistanceZ) + " +/- " + scenarioFloat(toleranceZ),
            scenarioFloat(replayWalkDistanceZ) + " delta=" + scenarioFloat(walkDistanceDeltaZ),
            false);
        failures.push_back(stepLocation(step) + ": movement_segment replay walked "
            + scenarioFloat(replayWalkDistanceZ) + " Z units, recorded walk was "
            + scenarioFloat(recordedWalkDistanceZ) + ", tolerance " + scenarioFloat(toleranceZ));
        success = false;
    }
    else
    {
        scenarioLogAssert(
            context,
            step,
            "movement.walk_z_distance",
            scenarioFloat(recordedWalkDistanceZ) + " +/- " + scenarioFloat(toleranceZ),
            scenarioFloat(replayWalkDistanceZ) + " delta=" + scenarioFloat(walkDistanceDeltaZ),
            true);
    }

    const float xyDistance = poseDistanceXY(movementResult.finalPose, *expectedStopPose);
    const float zDistance = poseDistanceZ(movementResult.finalPose, *expectedStopPose);
    if (cameraMovedDuringSegment)
    {
        scenarioLog(
            context,
            ScenarioLogColor::Yellow,
            std::string("WARNING movement_segment step=") + std::to_string(step.stepIndex)
                + " trace_line=" + std::to_string(step.sourceLine)
                + " camera changed while recording; final-position assertion is skipped"
                + " yaw_delta=" + scenarioFloat(normalizedAngleDifference(
                    startPose->yawRadians,
                    expectedStopPose->yawRadians))
                + " pitch_delta=" + scenarioFloat(expectedStopPose->pitchRadians - startPose->pitchRadians)
                + " xy_drift=" + scenarioFloat(xyDistance)
                + " z_drift=" + scenarioFloat(zDistance));
    }
    else if (xyDistance > toleranceXY)
    {
        scenarioLogAssert(
            context,
            step,
            "movement.stop_xy_drift",
            "<= " + scenarioFloat(toleranceXY),
            scenarioFloat(xyDistance),
            false);
        failures.push_back(stepLocation(step) + ": movement_segment final XY was "
            + scenarioFloat(xyDistance) + " units from expected, tolerance "
            + scenarioFloat(toleranceXY));
        success = false;
    }
    else if (!cameraMovedDuringSegment)
    {
        scenarioLogAssert(
            context,
            step,
            "movement.stop_xy_drift",
            "<= " + scenarioFloat(toleranceXY),
            scenarioFloat(xyDistance),
            true);
    }

    if (!cameraMovedDuringSegment && zDistance > toleranceZ)
    {
        scenarioLogAssert(
            context,
            step,
            "movement.stop_z_drift",
            "<= " + scenarioFloat(toleranceZ),
            scenarioFloat(zDistance),
            false);
        failures.push_back(stepLocation(step) + ": movement_segment final Z was "
            + scenarioFloat(zDistance) + " units from expected, tolerance "
            + scenarioFloat(toleranceZ));
        success = false;
    }
    else if (!cameraMovedDuringSegment)
    {
        scenarioLogAssert(
            context,
            step,
            "movement.stop_z_drift",
            "<= " + scenarioFloat(toleranceZ),
            scenarioFloat(zDistance),
            true);
    }

    if (step.payload["delta_game_minutes"] && step.payload["delta_game_minutes"].IsScalar())
    {
        context.gameMinutes += step.payload["delta_game_minutes"].as<float>();
        synchronizeRuntimeClock(context);
    }

    syncContextFromRuntime(context);
    return success;
}

bool runAdvanceRuntime(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    float seconds = 0.0f;

    if (step.payload["seconds"] && step.payload["seconds"].IsScalar())
    {
        seconds = step.payload["seconds"].as<float>();
    }
    else if (step.payload["milliseconds"] && step.payload["milliseconds"].IsScalar())
    {
        seconds = step.payload["milliseconds"].as<float>() / 1000.0f;
    }
    else if (!readScalarFloat(step, "seconds", seconds, failures, true))
    {
        return false;
    }

    if (context.mode != ScenarioMode::Faithful && !context.runtimeDriver)
    {
        return true;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    std::string failure;
    // present_dialogs: a dialogue a world event queued (an MM9 FoundPlayer greeting) opens within the step as the
    // game's frame opens it, and stops the world as the open dialogue does.
    const bool presentDialogs = step.payload["present_dialogs"] && step.payload["present_dialogs"].as<bool>(false);
    // follow_map_move: a map move asked for within the step (a cinematic's exit) happens in it, as in the game.
    const bool followMapMove = step.payload["follow_map_move"] && step.payload["follow_map_move"].as<bool>(false);

    if (!context.runtimeDriver->advanceRuntime(seconds, failure, presentDialogs, followMapMove))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

std::optional<uint16_t> parseScenarioMechanismState(const YAML::Node &node)
{
    if (!node || !node.IsScalar())
    {
        return std::nullopt;
    }

    const std::string text = lowerAscii(node.as<std::string>());

    if (text == "open")
    {
        return static_cast<uint16_t>(EvtMechanismState::Open);
    }
    if (text == "closing")
    {
        return static_cast<uint16_t>(EvtMechanismState::Closing);
    }
    if (text == "closed")
    {
        return static_cast<uint16_t>(EvtMechanismState::Closed);
    }
    if (text == "opening")
    {
        return static_cast<uint16_t>(EvtMechanismState::Opening);
    }

    return node.as<uint16_t>();
}

std::string scenarioMechanismStateText(uint16_t state)
{
    switch (static_cast<EvtMechanismState>(state))
    {
        case EvtMechanismState::Open:
            return "open";
        case EvtMechanismState::Closing:
            return "closing";
        case EvtMechanismState::Closed:
            return "closed";
        case EvtMechanismState::Opening:
            return "opening";
    }

    return std::to_string(state);
}

bool assertMechanismPayload(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const YAML::Node &mechanismNode,
    std::vector<std::string> &failures)
{
    if (!mechanismNode || !mechanismNode.IsMap())
    {
        failures.push_back(stepLocation(step) + ": mechanism assertion payload must be a mapping");
        return false;
    }

    if (!mechanismNode["id"] || !mechanismNode["id"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": mechanism assertion requires scalar field 'id'");
        return false;
    }

    if (context.runtimeDriver)
    {
        syncContextFromRuntime(context);
    }

    if (!context.eventRuntimeStateLoaded)
    {
        return context.mode != ScenarioMode::Faithful;
    }

    const uint32_t mechanismId = mechanismNode["id"].as<uint32_t>();
    const auto mechanismIt = context.eventRuntimeState.mechanisms.find(mechanismId);

    if (mechanismIt == context.eventRuntimeState.mechanisms.end())
    {
        if (context.mode != ScenarioMode::Faithful)
        {
            return true;
        }

        failures.push_back(stepLocation(step) + ": mechanism " + std::to_string(mechanismId)
            + " does not exist in current runtime state");
        return false;
    }

    const RuntimeMechanismState &mechanism = mechanismIt->second;
    bool success = true;
    const YAML::Node expectedStateNode =
        mechanismNode["state"] ? mechanismNode["state"] : mechanismNode["new_state"];

    if (expectedStateNode)
    {
        const std::optional<uint16_t> expectedState = parseScenarioMechanismState(expectedStateNode);

        if (expectedState)
        {
            const bool stateMatches = mechanism.state == *expectedState;
            scenarioLogAssert(
                context,
                step,
                "mechanism.state",
                scenarioMechanismStateText(*expectedState),
                scenarioMechanismStateText(mechanism.state),
                stateMatches);

            if (!stateMatches)
            {
                if (context.mode != ScenarioMode::Faithful)
                {
                    context.eventRuntimeState.mechanisms[mechanismId].state = *expectedState;
                }
                else if (*expectedState == static_cast<uint16_t>(EvtMechanismState::Closing)
                    || *expectedState == static_cast<uint16_t>(EvtMechanismState::Opening))
                {
                    scenarioLog(
                        context,
                        ScenarioLogColor::Yellow,
                        "WARNING step=" + std::to_string(step.stepIndex)
                            + " trace_line=" + std::to_string(step.sourceLine)
                            + " mechanism " + std::to_string(mechanismId)
                            + " transient state expected="
                            + scenarioMechanismStateText(*expectedState)
                            + " actual=" + scenarioMechanismStateText(mechanism.state));
                }
                else
                {
                    failures.push_back(stepLocation(step) + ": mechanism " + std::to_string(mechanismId)
                        + " state mismatch");
                    success = false;
                }
            }
        }
    }

    if (mechanismNode["moving"] && mechanismNode["moving"].IsScalar())
    {
        const bool expectedMoving = mechanismNode["moving"].as<bool>();
        const bool movingMatches = mechanism.isMoving == expectedMoving;
        scenarioLogAssert(
            context,
            step,
            "mechanism.moving",
            boolText(expectedMoving),
            boolText(mechanism.isMoving),
            movingMatches);

        if (!movingMatches)
        {
            if (context.mode != ScenarioMode::Faithful)
            {
                context.eventRuntimeState.mechanisms[mechanismId].isMoving = expectedMoving;
            }
            else if (expectedMoving)
            {
                scenarioLog(
                    context,
                    ScenarioLogColor::Yellow,
                    "WARNING step=" + std::to_string(step.stepIndex)
                        + " trace_line=" + std::to_string(step.sourceLine)
                        + " mechanism " + std::to_string(mechanismId)
                        + " transient moving expected=true actual=" + boolText(mechanism.isMoving));
            }
            else
            {
                failures.push_back(stepLocation(step) + ": mechanism " + std::to_string(mechanismId)
                    + " moving flag mismatch");
                success = false;
            }
        }
    }

    // `spinning`: a spinning mover turning (any speed) or still; `spin_rate_min`: at least this share of full speed.
    if (mechanismNode["spinning"] && mechanismNode["spinning"].IsScalar())
    {
        const bool expected = mechanismNode["spinning"].as<bool>();
        const bool actual = mechanism.spinRate != 0.0f;
        scenarioLogAssert(context, step, "mechanism.spinning", boolText(expected), boolText(actual), expected == actual);

        if (expected != actual)
        {
            failures.push_back(stepLocation(step) + ": mechanism " + std::to_string(mechanismId)
                + " spinning is " + boolText(actual) + " (rate " + std::to_string(mechanism.spinRate) + ")");
            success = false;
        }
    }

    if (mechanismNode["spin_rate_min"] && mechanismNode["spin_rate_min"].IsScalar())
    {
        const float minimum = mechanismNode["spin_rate_min"].as<float>();

        if (mechanism.spinRate < minimum)
        {
            failures.push_back(stepLocation(step) + ": mechanism " + std::to_string(mechanismId)
                + " spin rate " + std::to_string(mechanism.spinRate) + " below " + std::to_string(minimum));
            success = false;
        }
    }

    return success;
}

bool runAssertMechanism(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    return assertMechanismPayload(context, step, step.payload, failures);
}

bool runWaitUntil(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    float timeoutSeconds = 0.0f;

    if (step.payload["timeout_runtime_seconds"] && step.payload["timeout_runtime_seconds"].IsScalar())
    {
        timeoutSeconds = step.payload["timeout_runtime_seconds"].as<float>();
    }
    else if (step.payload["seconds"] && step.payload["seconds"].IsScalar())
    {
        timeoutSeconds = step.payload["seconds"].as<float>();
    }

    if (timeoutSeconds > 0.0f
        && (context.mode == ScenarioMode::Faithful
            || (context.runtimeDriver && context.runtimeDriver->hasActiveRuntime())))
    {
        if (!ensureRuntimeDriver(context, failures))
        {
            return context.mode != ScenarioMode::Faithful;
        }

        std::string failure;
        if (!context.runtimeDriver->advanceRuntime(timeoutSeconds, failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return false;
        }

        syncContextFromRuntime(context);
    }

    const YAML::Node assertNode = step.payload["assert"];

    if (assertNode && assertNode.IsMap() && assertNode["mechanism"])
    {
        return assertMechanismPayload(context, step, assertNode["mechanism"], failures);
    }

    return true;
}

bool runAdvanceGameTime(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    float minutes = 0.0f;

    if (step.payload["minutes"] && step.payload["minutes"].IsScalar())
    {
        minutes = step.payload["minutes"].as<float>();
    }
    else if (step.payload["hours"] && step.payload["hours"].IsScalar())
    {
        minutes = step.payload["hours"].as<float>() * 60.0f;
    }
    else if (step.payload["days"] && step.payload["days"].IsScalar())
    {
        minutes = step.payload["days"].as<float>() * 24.0f * 60.0f;
    }
    else
    {
        if (context.mode != ScenarioMode::Faithful)
        {
            return true;
        }

        failures.push_back(stepLocation(step) + ": advance_game_time requires minutes, hours, or days");
        return false;
    }

    context.gameMinutes += minutes;

    if (context.runtimeDriver)
    {
        std::string failure;

        if (!context.runtimeDriver->advanceGameMinutes(minutes, failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return false;
        }

        syncContextFromRuntime(context);
    }

    if (step.payload["after_game_minutes"] && step.payload["after_game_minutes"].IsScalar())
    {
        const float expectedGameMinutes = step.payload["after_game_minutes"].as<float>();
        const float deltaMinutes = expectedGameMinutes - context.gameMinutes;

        if (std::abs(deltaMinutes) > 0.001f)
        {
            scenarioLog(
                context,
                ScenarioLogColor::Yellow,
                "WARNING advance_game_time step=" + std::to_string(step.stepIndex)
                    + " ended at game_minutes=" + std::to_string(context.gameMinutes)
                    + " expected_after_game_minutes=" + std::to_string(expectedGameMinutes)
                    + " delta_minutes=" + std::to_string(deltaMinutes)
                    + "; syncing to recorded clock");
            context.gameMinutes = expectedGameMinutes;
            if (context.runtimeDriver)
            {
                context.runtimeDriver->setGameMinutes(context.gameMinutes);
            }
        }
    }

    synchronizeRuntimeClock(context);
    return true;
}

bool runInteractTarget(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    if (context.mode == ScenarioMode::Faithful || step.payload["pose"])
    {
        if (!step.payload["pose"])
        {
            failures.push_back(stepLocation(step)
                + ": faithful interact_target requires a pose so the runtime can pick from party/camera state");
            return false;
        }

        return runPressInteract(context, step, failures);
    }

    if (!step.payload["triggered_event"] || !step.payload["triggered_event"].IsScalar())
    {
        return true;
    }

    const uint16_t eventId = step.payload["triggered_event"].as<uint16_t>();
    executeRecordedEvent(context, step, eventId, true);
    return true;
}

bool runSpeakNpc(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    if (!step.payload["source_id"] || !step.payload["source_id"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": speak_npc requires scalar field 'source_id'");
        return false;
    }

    if (!context.runtimeDriver)
    {
        return true;
    }

    std::string failure;
    const uint32_t npcId = step.payload["source_id"].as<uint32_t>();

    if (!context.runtimeDriver->speakNpc(npcId, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    scenarioLog(
        context,
        ScenarioLogColor::Cyan,
        std::string("DIALOG after speak_npc step=") + std::to_string(step.stepIndex)
            + " " + context.runtimeDriver->activeDialogSummary());
    syncContextFromRuntime(context);
    return true;
}

bool runSelectTopic(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    const std::string kind = step.payload["kind"] && step.payload["kind"].IsScalar()
        ? step.payload["kind"].as<std::string>()
        : "";

    // Without action_id, match_label alone picks the line a player reads (exactly, else the one line containing it).
    const bool byLabelOnly = !step.payload["action_id"] && step.payload["match_label"]
        && step.payload["match_label"].IsScalar();

    if (!byLabelOnly && (!step.payload["action_id"] || !step.payload["action_id"].IsScalar()))
    {
        failures.push_back(stepLocation(step) + ": select_topic requires scalar field 'action_id' or 'match_label'");
        return false;
    }

    uint16_t eventId = byLabelOnly ? 0 : step.payload["action_id"].as<uint16_t>();

    if (context.runtimeDriver)
    {
        if (step.payload["expect_before"] && step.payload["expect_before"]["dialog"])
        {
            if (!assertDialogState(
                    context,
                    step,
                    step.payload["expect_before"]["dialog"],
                    "before select_topic",
                    failures))
            {
                return false;
            }
        }

        std::string failure;
        bool selected = false;

        if (step.payload["match_label"])
        {
            if (!step.payload["match_label"].IsScalar() || step.payload["match_label"].as<std::string>().empty())
            {
                failures.push_back(stepLocation(step) + ": match_label must be a nonempty scalar");
                return false;
            }
            const std::string label = step.payload["match_label"].as<std::string>();
            const ScenarioDialogSnapshot dialog = context.runtimeDriver->activeDialogSnapshot();
            std::optional<size_t> matchingIndex;
            for (const ScenarioDialogActionSnapshot &action : dialog.actions)
            {
                if ((byLabelOnly || action.id == eventId) && action.label == label)
                {
                    if (matchingIndex)
                    {
                        failures.push_back(stepLocation(step) + ": dialog action label is ambiguous: " + label);
                        return false;
                    }
                    matchingIndex = action.index;
                }
            }
            if (!matchingIndex && byLabelOnly)
            {
                const std::string wanted = lowerAscii(label);
                size_t containing = 0;

                for (const ScenarioDialogActionSnapshot &action : dialog.actions)
                {
                    if (lowerAscii(action.label).find(wanted) != std::string::npos)
                    {
                        matchingIndex = action.index;
                        ++containing;
                    }
                }

                if (containing > 1)
                {
                    matchingIndex.reset();
                }
            }
            if (!matchingIndex)
            {
                std::string offered;

                for (const ScenarioDialogActionSnapshot &action : dialog.actions)
                {
                    offered += "\n    [" + std::to_string(action.id) + "] " + action.label;
                }

                failures.push_back(stepLocation(step) + ": matching dialog action is unavailable: " + label
                    + "; the dialogue offers:" + offered);
                return false;
            }
            selected = context.runtimeDriver->selectDialogAction(*matchingIndex, failure);
        }
        else
        {
            selected = context.runtimeDriver->selectDialogActionById(eventId, failure);
        }

        if (!selected
            && context.mode != ScenarioMode::Faithful
            && step.payload["selection_index"]
            && step.payload["selection_index"].IsScalar())
        {
            const size_t rawIndex = step.payload["selection_index"].as<size_t>();

            selected =
                context.runtimeDriver->selectDialogAction(rawIndex, failure)
                || (rawIndex > 0 && context.runtimeDriver->selectDialogAction(rawIndex - 1, failure));
        }

        if (selected)
        {
            scenarioLog(
                context,
                ScenarioLogColor::Cyan,
                std::string("DIALOG after select_topic step=") + std::to_string(step.stepIndex)
                    + " " + context.runtimeDriver->activeDialogSummary());
            syncContextFromRuntime(context);
            return true;
        }

        if (context.mode == ScenarioMode::Faithful)
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return false;
        }
    }

    if (kind == "house_service"
        && step.payload["source_id"] && step.payload["source_id"].IsScalar()
        && eventId == 23)
    {
        const uint32_t houseId = step.payload["source_id"].as<uint32_t>();
        const HouseEntry *pHouse = context.gameDataLoader.getHouseTable().get(houseId);

        if (pHouse != nullptr && pHouse->extraExit.has_value())
        {
            return loadMap(context, pHouse->extraExit->destinationMapFileName, failures);
        }
    }

    if (kind == "house_service"
        && step.payload["source_id"] && step.payload["source_id"].IsScalar())
    {
        const uint32_t houseId = step.payload["source_id"].as<uint32_t>();
        const HouseEntry *pHouse = context.gameDataLoader.getHouseTable().get(houseId);

        if (pHouse != nullptr)
        {
            HouseActionOption option = {};
            option.id = static_cast<HouseActionId>(eventId);
            option.enabled = true;

            if (step.payload["label"] && step.payload["label"].IsScalar())
            {
                option.label = step.payload["label"].as<std::string>();
            }

            performHouseAction(
                option,
                *pHouse,
                context.party,
                &context.gameDataLoader.getClassSkillTable(),
                nullptr);
        }
    }

    if (kind == "house_resident")
    {
        const std::vector<NpcDialogTable::ResolvedTopic> topics =
            context.gameDataLoader.getNpcDialogTable().getTopicsForNpc(eventId);

        if (!topics.empty() && topics[0].id <= UINT16_MAX)
        {
            eventId = static_cast<uint16_t>(topics[0].id);
        }
    }

    executeRecordedEvent(context, step, eventId, true);
    return true;
}

bool runSaveCheckpoint(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadMapOrScalar(step, failures))
    {
        return false;
    }

    const std::string name = readCheckpointName(step, failures);

    if (name.empty())
    {
        return false;
    }

    ScenarioExecutionContext::Checkpoint checkpoint = {};
    checkpoint.party = context.party;
    checkpoint.eventRuntimeState = context.eventRuntimeState;
    checkpoint.currentMapFileName = context.currentMapFileName;
    checkpoint.gameMinutes = context.gameMinutes;
    checkpoint.eventRuntimeStateLoaded = context.eventRuntimeStateLoaded;
    context.checkpoints[name] = std::move(checkpoint);
    return true;
}

bool runLoadCheckpoint(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadMapOrScalar(step, failures))
    {
        return false;
    }

    const std::string name = readCheckpointName(step, failures);

    if (name.empty())
    {
        return false;
    }

    const auto checkpointIt = context.checkpoints.find(name);

    if (checkpointIt == context.checkpoints.end())
    {
        failures.push_back(stepLocation(step) + ": checkpoint '" + name + "' does not exist");
        return false;
    }

    context.party = checkpointIt->second.party;
    context.eventRuntimeState = checkpointIt->second.eventRuntimeState;
    context.gameMinutes = checkpointIt->second.gameMinutes;
    context.eventRuntimeStateLoaded = checkpointIt->second.eventRuntimeStateLoaded;
    const std::string mapFileName = checkpointIt->second.currentMapFileName;

    if (!mapFileName.empty())
    {
        return loadMap(context, mapFileName, failures);
    }

    context.currentMapFileName.clear();
    return true;
}

std::filesystem::path scenarioSavePathForName(
    ScenarioExecutionContext &context,
    const std::string &name)
{
    const std::string stem = sanitizeScenarioFileStem(name);
    return context.saveGameRootPath / (stem + ".oysav");
}

std::filesystem::path resolveScenarioExternalPath(
    const ScenarioExecutionContext &context,
    const std::string &pathText)
{
    std::filesystem::path path(pathText);

    if (path.is_relative())
    {
        std::error_code errorCode;
        const std::filesystem::path workingPath = (std::filesystem::current_path(errorCode) / path).lexically_normal();

        if (!errorCode && std::filesystem::exists(workingPath, errorCode))
        {
            return workingPath;
        }

        path = context.basePath / path;
    }

    return path.lexically_normal();
}

bool readLoadGameRequest(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::string &name,
    std::filesystem::path &explicitPath,
    std::vector<std::string> &failures)
{
    explicitPath.clear();

    if (step.payload.IsScalar())
    {
        name = step.payload.as<std::string>();
        return !name.empty();
    }

    if (!step.payload.IsMap())
    {
        failures.push_back(stepLocation(step) + ": load_game payload must be a scalar or mapping");
        return false;
    }

    std::string pathText;

    if (!readScalarString(step, "name", name, failures, false)
        || !readScalarString(step, "path", pathText, failures, false))
    {
        return false;
    }

    if (!pathText.empty())
    {
        explicitPath = resolveScenarioExternalPath(context, pathText);
    }

    if (name.empty() && !pathText.empty())
    {
        name = sanitizeScenarioFileStem(std::filesystem::path(pathText).stem().string());
    }

    if (name.empty())
    {
        failures.push_back(stepLocation(step) + ": load_game requires scalar payload, 'name', or 'path'");
        return false;
    }

    return true;
}

bool ensureRuntimeReadyForCurrentContext(
    ScenarioExecutionContext &context,
    std::vector<std::string> &failures)
{
    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    seedRuntimeDriverFromContext(context);

    if (!context.currentMapFileName.empty()
        && (!context.runtimeDriver->hasActiveRuntime()
            || lowerAscii(context.runtimeDriver->currentMapFileName()) != lowerAscii(context.currentMapFileName)))
    {
        std::string failure;

        if (!context.runtimeDriver->loadMap(context.currentMapFileName, failure))
        {
            failures.push_back(failure);
            return false;
        }

        seedRuntimeDriverFromContext(context);
    }

    return true;
}

bool runSaveGame(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadMapOrScalar(step, failures))
    {
        return false;
    }

    const std::string name = readCheckpointName(step, failures);

    if (name.empty())
    {
        return false;
    }

    if (!ensureRuntimeReadyForCurrentContext(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    std::error_code errorCode;
    std::filesystem::create_directories(context.saveGameRootPath, errorCode);

    if (errorCode)
    {
        failures.push_back(stepLocation(step) + ": could not create scenario save directory '"
            + context.saveGameRootPath.string() + "': " + errorCode.message());
        return false;
    }

    // path: a save kept after the run (a playthrough's checkpoint for the next segment), else the run's own folder.
    // A relative path is from the working folder (the file need not exist yet).
    const std::filesystem::path path = step.payload.IsMap() && step.payload["path"]
        ? std::filesystem::absolute(std::filesystem::path(step.payload["path"].as<std::string>())).lexically_normal()
        : scenarioSavePathForName(context, name);

    if (step.payload.IsMap() && step.payload["path"])
    {
        std::filesystem::create_directories(path.parent_path(), errorCode);
    }

    std::string failure;
    // expect_failure: the save must not be written; block_with_directory puts a folder where the file would go, so
    // the write fails.
    const bool expectFailure = step.payload.IsMap() && step.payload["expect_failure"].as<bool>(false);

    if (step.payload.IsMap() && step.payload["block_with_directory"].as<bool>(false))
    {
        std::filesystem::create_directories(path, errorCode);
    }

    const bool saved = context.runtimeDriver->saveGameToPath(path, name, failure);

    if (expectFailure)
    {
        syncContextFromRuntime(context);

        if (saved)
        {
            failures.push_back(stepLocation(step) + ": save_game was expected to fail but wrote '" + name + "'");
            return false;
        }

        return true;
    }

    if (!saved)
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return context.mode != ScenarioMode::Faithful;
    }

    // required_package_schema: {package: rulesets/maw, schema: 999} rewrites the save to need a package schema the
    // game does not have, so a load of it fails its package check.
    if (step.payload.IsMap() && step.payload["required_package_schema"])
    {
        const YAML::Node schemaNode = step.payload["required_package_schema"];
        std::optional<GameSaveData> saved = loadGameDataFromPath(path, failure);

        if (!saved || !schemaNode.IsMap() || !schemaNode["package"] || !schemaNode["schema"])
        {
            failures.push_back(stepLocation(step) + ": required_package_schema needs package and schema ("
                + failure + ")");
            return false;
        }

        saved->requiredContentPackages[schemaNode["package"].as<std::string>()] = schemaNode["schema"].as<uint32_t>();

        if (!saveGameDataToPath(path, *saved, failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return false;
        }
    }

    // rebuilt_maps: [6d01.blv, ...] rewrites the save as if those maps were rebuilt after it: their saved states
    // record another layout (game/maps/MapLayoutIdentity.h), so a load resets them.
    if (step.payload.IsMap() && step.payload["rebuilt_maps"])
    {
        const YAML::Node mapsNode = step.payload["rebuilt_maps"];
        std::optional<GameSaveData> saved = loadGameDataFromPath(path, failure);

        if (!saved || !mapsNode.IsSequence() || mapsNode.size() == 0)
        {
            failures.push_back(stepLocation(step) + ": rebuilt_maps needs a list of map files (" + failure + ")");
            return false;
        }

        size_t rewritten = 0;

        for (const YAML::Node &mapNode : mapsNode)
        {
            const std::string mapFile = mapNode.as<std::string>();
            const std::string canonicalSuffix = ".map." + normalizeMapFileStem(mapFile);
            const auto matches = [&](const std::string &key)
            {
                return lowerAscii(key) == lowerAscii(mapFile) || lowerAscii(key).ends_with(canonicalSuffix);
            };
            // Any other nonzero identity: the map's current one is never this.
            const auto rebuild = [&rewritten](uint64_t &identity)
            {
                identity = identity == 0x5ca1ab1eull ? 0x5ca1ab1full : 0x5ca1ab1eull;
                ++rewritten;
            };

            for (auto &[key, state] : saved->indoorSceneStates)
            {
                if (matches(key))
                {
                    rebuild(state.mapLayoutIdentity);
                }
            }

            for (auto &[key, state] : saved->outdoorWorldStates)
            {
                if (matches(key))
                {
                    rebuild(state.mapLayoutIdentity);
                }
            }

            if (lowerAscii(saved->mapFileName) == lowerAscii(mapFile))
            {
                if (saved->hasIndoorSceneState && saved->currentSceneKind == SceneKind::Indoor)
                {
                    rebuild(saved->indoorScene.mapLayoutIdentity);
                }

                if (saved->hasOutdoorRuntimeState && saved->currentSceneKind == SceneKind::Outdoor)
                {
                    rebuild(saved->outdoorWorld.mapLayoutIdentity);
                }
            }
        }

        if (rewritten == 0 || !saveGameDataToPath(path, *saved, failure))
        {
            failures.push_back(stepLocation(step) + ": rebuilt_maps found no saved state of those maps to rewrite"
                + (failure.empty() ? std::string() : " (" + failure + ")"));
            return false;
        }
    }

    context.saveGamePaths[name] = path;
    syncContextFromRuntime(context);
    return true;
}

// quick_load: {save, expect: loaded | warned, expect_status}: one press of the quick load key with the named
// scenario save as the quicksave. warned: the press only showed the rules' load warning and loaded nothing.
bool runQuickLoad(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeReadyForCurrentContext(context, failures))
    {
        return false;
    }

    const std::string name = step.payload["save"].as<std::string>("");
    const auto saveIt = context.saveGamePaths.find(name);
    const std::string expected = step.payload["expect"].as<std::string>("loaded");

    if (saveIt == context.saveGamePaths.end() || (expected != "loaded" && expected != "warned"))
    {
        failures.push_back(stepLocation(step) + ": quick_load needs a saved game 'save' and expect loaded or warned");
        return false;
    }

    bool loaded = false;
    std::string status;
    std::string failure;

    if (!context.runtimeDriver->pressQuickLoad(
            saveIt->second, context.saveGameRootPath / "quick_load", loaded, status, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    std::cout << "QUICK LOAD " << (loaded ? "loaded" : "not loaded") << ": " << status << '\n';
    bool ok = true;

    if (loaded != (expected == "loaded"))
    {
        failures.push_back(stepLocation(step) + ": quick_load " + (loaded ? "loaded" : "did not load")
            + ", expected " + expected + " (status \"" + status + "\")");
        ok = false;
    }

    const std::string expectedStatus = step.payload["expect_status"].as<std::string>("");

    if (!expectedStatus.empty() && status.find(expectedStatus) == std::string::npos)
    {
        failures.push_back(stepLocation(step) + ": quick_load status lacks \"" + expectedStatus + "\": " + status);
        ok = false;
    }

    return ok;
}

bool runLoadGame(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadMapOrScalar(step, failures))
    {
        return false;
    }

    std::string name;
    std::filesystem::path path;

    if (!readLoadGameRequest(context, step, name, path, failures))
    {
        return false;
    }

    const auto saveIt = context.saveGamePaths.find(name);

    if (saveIt != context.saveGamePaths.end())
    {
        path = saveIt->second;
    }
    else if (path.empty())
    {
        failures.push_back(stepLocation(step) + ": save_game '" + name + "' does not exist");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    std::string failure;
    // expect_failure: the load must be refused; the game in progress stays (audit STD3-1).
    const bool expectFailure = step.payload.IsMap() && step.payload["expect_failure"].as<bool>(false);
    const bool loaded = context.runtimeDriver->loadGameFromPath(path, failure);

    if (expectFailure)
    {
        if (loaded)
        {
            failures.push_back(stepLocation(step) + ": load_game was expected to fail but loaded '" + name + "'");
            return false;
        }

        syncContextFromRuntime(context);
        return true;
    }

    if (!loaded)
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return context.mode != ScenarioMode::Faithful;
    }

    context.saveGamePaths[name] = path;
    syncContextFromRuntime(context);
    return true;
}

bool assertCurrentMap(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const std::string &expectedMap,
    std::vector<std::string> &failures)
{
    if (context.currentMapFileName.empty())
    {
        scenarioLogAssert(context, step, "map", expectedMap, "<none>", false);
        failures.push_back(stepLocation(step) + ": no map is currently loaded");
        return false;
    }

    if (lowerAscii(context.currentMapFileName) != lowerAscii(expectedMap))
    {
        scenarioLogAssert(context, step, "map", expectedMap, context.currentMapFileName, false);
        failures.push_back(stepLocation(step) + ": expected map '" + expectedMap
            + "' but current map is '" + context.currentMapFileName + "'");
        return false;
    }

    scenarioLogAssert(context, step, "map", expectedMap, context.currentMapFileName, true);
    return true;
}

bool assertInventoryAnyMember(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node inventoryNode = step.payload["inventory_any_member"];

    if (!inventoryNode)
    {
        return true;
    }

    if (!inventoryNode.IsSequence())
    {
        failures.push_back(stepLocation(step) + ": field 'inventory_any_member' must be a sequence");
        return false;
    }

    bool success = true;

    for (const YAML::Node &entryNode : inventoryNode)
    {
        if (!entryNode.IsMap() || !entryNode["item_id"] || !entryNode["item_id"].IsScalar())
        {
            failures.push_back(stepLocation(step)
                + ": inventory_any_member entries must contain scalar field 'item_id'");
            success = false;
            continue;
        }

        const uint32_t itemId = entryNode["item_id"].as<uint32_t>();
        const int count = context.party.inventoryItemCount(itemId);
        // count: exactly that many; min_count: at least; neither: at least one.
        const bool itemFound = entryNode["count"] ? count == entryNode["count"].as<int>()
                                                  : count >= entryNode["min_count"].as<int>(1);
        scenarioLogAssert(
            context,
            step,
            "item_id",
            std::to_string(itemId),
            itemFound ? std::to_string(itemId) : "<missing>",
            itemFound);

        if (!itemFound)
        {
            failures.push_back(stepLocation(step) + ": item " + std::to_string(itemId) + " count "
                + std::to_string(count) + " in the party's inventories does not match");
            success = false;
        }
    }

    return success;
}

bool assertInventoryList(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node inventoryNode = step.payload["inventory"];

    if (!inventoryNode)
    {
        return true;
    }

    if (!inventoryNode.IsSequence())
    {
        failures.push_back(stepLocation(step) + ": field 'inventory' must be a sequence");
        return false;
    }

    bool success = true;

    for (const YAML::Node &entryNode : inventoryNode)
    {
        if (!entryNode.IsMap() || !entryNode["item_id"] || !entryNode["item_id"].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": inventory entries must contain scalar field 'item_id'");
            success = false;
            continue;
        }

        const uint32_t itemId = entryNode["item_id"].as<uint32_t>();
        bool itemFound = context.party.inventoryItemCount(itemId) > 0;

        if (!itemFound)
        {
            if (context.mode != ScenarioMode::Faithful && context.party.tryGrantItem(itemId))
            {
                itemFound = true;
            }
            else
            {
                failures.push_back(stepLocation(step) + ": item " + std::to_string(itemId)
                    + " was not found in party inventory");
                success = false;
            }
        }

        scenarioLogAssert(
            context,
            step,
            "item_id",
            std::to_string(itemId),
            itemFound ? std::to_string(itemId) : "<missing>",
            itemFound);
    }

    return success;
}

bool assertAwards(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node awardsNode = step.payload["award_acquired"];

    if (!awardsNode)
    {
        return true;
    }

    if (!awardsNode.IsSequence())
    {
        failures.push_back(stepLocation(step) + ": field 'award_acquired' must be a sequence");
        return false;
    }

    bool success = true;

    for (const YAML::Node &entryNode : awardsNode)
    {
        if (!entryNode.IsMap() || !entryNode["id"] || !entryNode["id"].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": award_acquired entries must contain scalar field 'id'");
            success = false;
            continue;
        }

        const uint32_t awardId = entryNode["id"].as<uint32_t>();
        bool acquired = false;

        if (entryNode["member_index"] && entryNode["member_index"].IsScalar())
        {
            acquired = context.party.hasAward(entryNode["member_index"].as<size_t>(), awardId);
        }
        else
        {
            acquired = context.party.hasAward(awardId);
        }

        if (!acquired)
        {
            if (context.mode == ScenarioMode::Faithful)
            {
                failures.push_back(stepLocation(step) + ": award " + std::to_string(awardId)
                    + " was not acquired");
                success = false;
                continue;
            }

            if (entryNode["member_index"] && entryNode["member_index"].IsScalar())
            {
                context.party.addAward(entryNode["member_index"].as<size_t>(), awardId);
            }
            else
            {
                context.party.addAward(awardId);
            }
        }
    }

    return success;
}

std::optional<EquipmentSlot> parseScenarioEquipmentSlot(const std::string &value)
{
    const std::string normalized = lowerAscii(value);

    if (normalized == "offhand" || normalized == "off_hand")
    {
        return EquipmentSlot::OffHand;
    }
    if (normalized == "mainhand" || normalized == "main_hand")
    {
        return EquipmentSlot::MainHand;
    }
    if (normalized == "bow")
    {
        return EquipmentSlot::Bow;
    }
    if (normalized == "armor")
    {
        return EquipmentSlot::Armor;
    }
    if (normalized == "helm")
    {
        return EquipmentSlot::Helm;
    }
    if (normalized == "belt")
    {
        return EquipmentSlot::Belt;
    }
    if (normalized == "cloak")
    {
        return EquipmentSlot::Cloak;
    }
    if (normalized == "gauntlets")
    {
        return EquipmentSlot::Gauntlets;
    }
    if (normalized == "boots")
    {
        return EquipmentSlot::Boots;
    }
    if (normalized == "amulet")
    {
        return EquipmentSlot::Amulet;
    }
    if (normalized == "ring1")
    {
        return EquipmentSlot::Ring1;
    }
    if (normalized == "ring2")
    {
        return EquipmentSlot::Ring2;
    }
    if (normalized == "ring3")
    {
        return EquipmentSlot::Ring3;
    }
    if (normalized == "ring4")
    {
        return EquipmentSlot::Ring4;
    }
    if (normalized == "ring5")
    {
        return EquipmentSlot::Ring5;
    }
    if (normalized == "ring6")
    {
        return EquipmentSlot::Ring6;
    }

    return std::nullopt;
}

bool assertAwardCleared(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node awardsNode = step.payload["award_cleared"];

    if (!awardsNode)
    {
        return true;
    }

    if (!awardsNode.IsSequence())
    {
        failures.push_back(stepLocation(step) + ": field 'award_cleared' must be a sequence");
        return false;
    }

    bool success = true;

    for (const YAML::Node &entryNode : awardsNode)
    {
        if (!entryNode.IsMap() || !entryNode["id"] || !entryNode["id"].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": award_cleared entries must contain scalar field 'id'");
            success = false;
            continue;
        }

        const uint32_t awardId = entryNode["id"].as<uint32_t>();
        const bool stillAcquired = entryNode["member_index"] && entryNode["member_index"].IsScalar()
            ? context.party.hasAward(entryNode["member_index"].as<size_t>(), awardId)
            : context.party.hasAward(awardId);

        if (stillAcquired)
        {
            failures.push_back(stepLocation(step) + ": award " + std::to_string(awardId)
                + " was expected to be cleared");
            success = false;
        }
    }

    return success;
}

bool takePartyOverlayHeldItem(
    ScenarioExecutionContext &context,
    const YAML::Node &heldNode,
    uint32_t expectedItemId)
{
    if (expectedItemId == 0)
    {
        return false;
    }

    std::vector<size_t> memberIndices;

    if (heldNode["member_index"] && heldNode["member_index"].IsScalar())
    {
        memberIndices.push_back(heldNode["member_index"].as<size_t>());
    }
    else
    {
        const size_t activeMemberIndex = context.party.activeMemberIndex();

        if (context.party.member(activeMemberIndex) != nullptr)
        {
            memberIndices.push_back(activeMemberIndex);
        }

        for (size_t memberIndex = 0; memberIndex < context.party.memberCount(); ++memberIndex)
        {
            if (std::find(memberIndices.begin(), memberIndices.end(), memberIndex) == memberIndices.end())
            {
                memberIndices.push_back(memberIndex);
            }
        }
    }

    const std::optional<ScenarioInventoryGrid> grid =
        heldNode["grid"] && heldNode["grid"].IsScalar()
            ? parseInventoryGridText(heldNode["grid"].as<std::string>())
            : std::nullopt;

    const auto takeFromCell = [&context](size_t memberIndex, uint8_t x, uint8_t y)
    {
        if (context.runtimeDriver)
        {
            std::string failure;
            if (!context.runtimeDriver->takeInventoryItemToCursor(memberIndex, x, y, failure))
            {
                return false;
            }
            syncContextFromRuntime(context);
            return true;
        }
        InventoryItem heldItem = {};
        if (!context.party.takeItemFromMemberInventoryCell(memberIndex, x, y, heldItem))
        {
            return false;
        }
        context.party.setHeldItemForQueries(heldItem);
        return true;
    };

    if (grid)
    {
        for (size_t memberIndex : memberIndices)
        {
            const Character *pMember = context.party.member(memberIndex);
            const InventoryItem *pItem = pMember != nullptr ? pMember->inventoryItemAt(grid->x, grid->y) : nullptr;

            if (pItem == nullptr || pItem->objectDescriptionId != expectedItemId)
            {
                continue;
            }

            if (takeFromCell(memberIndex, grid->x, grid->y))
            {
                return true;
            }
        }
    }

    for (size_t memberIndex : memberIndices)
    {
        const Character *pMember = context.party.member(memberIndex);

        if (pMember == nullptr)
        {
            continue;
        }

        for (const InventoryItem &item : pMember->inventory)
        {
            if (item.objectDescriptionId != expectedItemId)
            {
                continue;
            }

            if (takeFromCell(memberIndex, item.gridX, item.gridY))
            {
                return true;
            }
        }
    }

    return false;
}

bool assertHeldItem(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node heldNode = step.payload["held_item"];

    if (!heldNode)
    {
        return true;
    }

    if (!heldNode.IsMap() || !heldNode["active"] || !heldNode["active"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": held_item assertion must contain scalar field 'active'");
        return false;
    }

    const bool expectedActive = heldNode["active"].as<bool>();
    const uint32_t expectedItemId =
        heldNode["item_id"] && heldNode["item_id"].IsScalar() ? heldNode["item_id"].as<uint32_t>() : 0;
    const std::string source =
        heldNode["source"] && heldNode["source"].IsScalar() ? heldNode["source"].as<std::string>() : std::string();
    const uint32_t actualItemId = context.party.heldItemIdForQueries();

    if (!expectedActive)
    {
        if (actualItemId != 0)
        {
            if (expectedItemId == 0 || actualItemId == expectedItemId)
            {
                if (context.runtimeDriver)
                {
                    std::string failure;
                    if (!context.runtimeDriver->placeHeldItemInInventory(failure))
                    {
                        failures.push_back(stepLocation(step) + ": " + failure);
                        return false;
                    }
                    syncContextFromRuntime(context);
                    return true;
                }
                if (context.party.inventoryItemCount(actualItemId) <= 0)
                {
                    context.party.tryGrantItem(actualItemId);
                }

                context.party.clearHeldItemForQueries();

                if (context.runtimeDriver)
                {
                    context.runtimeDriver->setPartyState(context.party);
                }

                return true;
            }

            if (context.mode != ScenarioMode::Faithful)
            {
                context.party.clearHeldItemForQueries();
                return true;
            }

            failures.push_back(stepLocation(step) + ": expected no held item but party holds item "
                + std::to_string(actualItemId));
            return false;
        }

        return true;
    }

    if (actualItemId != expectedItemId)
    {
        if (source == "party_overlay" && takePartyOverlayHeldItem(context, heldNode, expectedItemId))
        {
            return true;
        }

        if (context.mode != ScenarioMode::Faithful && expectedItemId != 0)
        {
            InventoryItem heldItem = {};
            heldItem.objectDescriptionId = expectedItemId;
            heldItem.quantity = 1;
            context.party.setHeldItemForQueries(heldItem);
            return true;
        }

        failures.push_back(stepLocation(step) + ": expected held item " + std::to_string(expectedItemId)
            + " but party holds item " + std::to_string(actualItemId));
        return false;
    }

    return true;
}

bool assertEquippedItems(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node equippedNode = step.payload["equipped_item"];

    if (!equippedNode)
    {
        return true;
    }

    if (!equippedNode.IsSequence())
    {
        failures.push_back(stepLocation(step) + ": field 'equipped_item' must be a sequence");
        return false;
    }

    bool success = true;

    for (const YAML::Node &entryNode : equippedNode)
    {
        if (!entryNode.IsMap()
            || !entryNode["item_id"] || !entryNode["item_id"].IsScalar()
            || !entryNode["member_index"] || !entryNode["member_index"].IsScalar()
            || !entryNode["slot"] || !entryNode["slot"].IsScalar())
        {
            failures.push_back(stepLocation(step)
                + ": equipped_item entries must contain scalar item_id, member_index, and slot");
            success = false;
            continue;
        }

        const std::optional<EquipmentSlot> slot = parseScenarioEquipmentSlot(entryNode["slot"].as<std::string>());

        if (!slot)
        {
            failures.push_back(stepLocation(step) + ": unsupported equipped_item slot '"
                + entryNode["slot"].as<std::string>() + "'");
            success = false;
            continue;
        }

        const size_t memberIndex = entryNode["member_index"].as<size_t>();
        const uint32_t expectedItemId = entryNode["item_id"].as<uint32_t>();
        const uint32_t actualItemId = context.party.equippedItemId(memberIndex, *slot);

        if (actualItemId != expectedItemId)
        {
            failures.push_back(stepLocation(step) + ": expected member " + std::to_string(memberIndex)
                + " slot '" + entryNode["slot"].as<std::string>() + "' to hold item "
                + std::to_string(expectedItemId) + " but found " + std::to_string(actualItemId));
            success = false;
        }
    }

    return success;
}

// item_set_bonus: {member_index, set_id, active}: whether the member wears enough unbroken pieces of the set for one
// of its bonus rows (item_sets), counted as the party's stat pass counts them.
bool assertItemSetBonus(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node setNode = step.payload["item_set_bonus"];

    if (!setNode)
    {
        return true;
    }

    if (!setNode.IsMap() || !setNode["set_id"] || !setNode["active"])
    {
        failures.push_back(stepLocation(step) + ": item_set_bonus needs set_id and active");
        return false;
    }

    const size_t memberIndex = setNode["member_index"].as<size_t>(0);
    const std::string setId = setNode["set_id"].as<std::string>();
    const ItemTable *pItemTable = context.party.itemTable();
    const size_t pieceCount = context.party.equippedItemSetPieceCount(memberIndex, setId);
    bool hasBonusRow = false;
    bool active = false;

    if (pItemTable != nullptr)
    {
        for (const ItemSetBonusDefinition &bonus : pItemTable->setBonuses())
        {
            if (bonus.setId == setId)
            {
                hasBonusRow = true;
                active = active || pieceCount >= bonus.requiredPieceCount;
            }
        }
    }

    if (!hasBonusRow)
    {
        failures.push_back(stepLocation(step) + ": item_set_bonus: no item_sets row for '" + setId + "'");
        return false;
    }

    return recordScenarioAssertion(context, step, "item_set_bonus[" + setId + "] pieces=" + std::to_string(pieceCount),
        setNode["active"].as<bool>() ? "true" : "false", active ? "true" : "false", failures);
}

bool assertMapObservation(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (step.payload["map_loaded"] && step.payload["map_loaded"].IsScalar())
    {
        const std::string mapFileName = step.payload["map_loaded"].as<std::string>();

        if (lowerAscii(context.currentMapFileName) != lowerAscii(mapFileName))
        {
            if (context.mode == ScenarioMode::Faithful)
            {
                failures.push_back(stepLocation(step) + ": expected observed map '" + mapFileName
                    + "' but current map is '" + context.currentMapFileName + "'");
                return false;
            }

            return loadMap(context, mapFileName, failures);
        }

        return assertCurrentMap(context, step, mapFileName, failures);
    }

    if (step.payload["map_arrived"])
    {
        const YAML::Node arrivedNode = step.payload["map_arrived"];

        if (!arrivedNode.IsMap() || !arrivedNode["map"] || !arrivedNode["map"].IsScalar())
        {
            failures.push_back(stepLocation(step)
                + ": map_arrived assertion must contain scalar field 'map'");
            return false;
        }

        const std::string mapFileName = arrivedNode["map"].as<std::string>();

        if (lowerAscii(context.currentMapFileName) != lowerAscii(mapFileName))
        {
            if (context.mode == ScenarioMode::Faithful)
            {
                failures.push_back(stepLocation(step) + ": expected arrival map '" + mapFileName
                    + "' but current map is '" + context.currentMapFileName + "'");
                return false;
            }

            return loadMap(context, mapFileName, failures);
        }

        return assertCurrentMap(context, step, mapFileName, failures);
    }

    return true;
}

bool mapMatchesCurrentObservation(
    const ScenarioExecutionContext &context,
    const YAML::Node &node)
{
    if (!node["map"] || !node["map"].IsScalar())
    {
        return true;
    }

    return lowerAscii(node["map"].as<std::string>()) == lowerAscii(context.currentMapFileName);
}

bool assertMapVarNode(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const YAML::Node &node,
    std::vector<std::string> &failures)
{
    if (!node.IsMap()
        || !((node["current"] && node["current"].IsScalar())
            || (node["value"] && node["value"].IsScalar())))
    {
        failures.push_back(stepLocation(step) + ": map variable assertion requires scalar field 'current' or 'value'");
        return false;
    }

    if (!context.eventRuntimeStateLoaded || !mapMatchesCurrentObservation(context, node))
    {
        return true;
    }

    int32_t actualValue = 0;

    if (node["index"] && node["index"].IsScalar())
    {
        const size_t index = node["index"].as<size_t>();

        if (index >= context.eventRuntimeState.mapVars.size())
        {
            failures.push_back(stepLocation(step) + ": map variable index out of range: "
                + std::to_string(index));
            return false;
        }

        actualValue = context.eventRuntimeState.mapVars[index];
    }
    else if (node["name"] && node["name"].IsScalar())
    {
        const std::string name = node["name"].as<std::string>();
        const auto iterator = context.eventRuntimeState.namedMapVars.find(name);
        actualValue = iterator != context.eventRuntimeState.namedMapVars.end() ? iterator->second : 0;
    }
    else
    {
        failures.push_back(stepLocation(step) + ": map variable assertion requires index or name");
        return false;
    }

    const int32_t expectedValue =
        node["current"] && node["current"].IsScalar() ? node["current"].as<int32_t>() : node["value"].as<int32_t>();

    if (actualValue != expectedValue)
    {
        failures.push_back(stepLocation(step) + ": expected map variable value "
            + std::to_string(expectedValue) + " but found " + std::to_string(actualValue));
        return false;
    }

    return true;
}

bool isMmergeCrossContinentScrollVariableName(const std::string &name)
{
    const std::string key = lowerAscii(name);
    return key == "mmerge.crosscontinents.scrollgenerated"
        || key == "mmerge.crosscontinents.scrollitemid";
}

bool assertNamedGlobalVarNode(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const YAML::Node &node,
    std::vector<std::string> &failures)
{
    if (!node.IsMap()
        || !node["name"] || !node["name"].IsScalar()
        || !((node["current"] && node["current"].IsScalar())
            || (node["value"] && node["value"].IsScalar())))
    {
        failures.push_back(stepLocation(step)
            + ": named global variable assertion requires scalar fields 'name' and 'current' or 'value'");
        return false;
    }

    if (!context.eventRuntimeStateLoaded)
    {
        return true;
    }

    const std::string name = node["name"].as<std::string>();

    if (isMmergeCrossContinentScrollVariableName(name))
    {
        return true;
    }

    const auto iterator = context.eventRuntimeState.namedGlobalVars.find(name);
    const int32_t actualValue = iterator != context.eventRuntimeState.namedGlobalVars.end() ? iterator->second : 0;
    const int32_t expectedValue =
        node["current"] && node["current"].IsScalar() ? node["current"].as<int32_t>() : node["value"].as<int32_t>();

    if (actualValue != expectedValue)
    {
        failures.push_back(stepLocation(step) + ": expected named global var '" + name + "' value "
            + std::to_string(expectedValue) + " but found " + std::to_string(actualValue));
        return false;
    }

    return true;
}

bool assertVariableObservations(
    const ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    bool success = true;

    for (const char *pFieldName : {"map_var_changed", "decor_var_changed", "state_dump_map_var"})
    {
        if (step.payload[pFieldName])
        {
            success = assertMapVarNode(context, step, step.payload[pFieldName], failures) && success;
        }
    }

    for (const char *pFieldName : {"named_map_var_changed", "state_dump_named_map_var"})
    {
        if (step.payload[pFieldName])
        {
            success = assertMapVarNode(context, step, step.payload[pFieldName], failures) && success;
        }
    }

    for (const char *pFieldName : {"named_global_var_changed", "state_dump_named_global_var"})
    {
        if (step.payload[pFieldName])
        {
            success = assertNamedGlobalVarNode(context, step, step.payload[pFieldName], failures) && success;
        }
    }

    return success;
}

// ai_trace: {actor_index | arena_monster, decision | event, target, min_count, max_count, max_in_window, within_seconds,
// after, before, report}: how many trace lines match (an AI arena's decision trace): a decision (actorAiDecisionName) or
// a world event (spawn, motion, target, damaged, healed, died, revived, anim), of the actor (any without one), against
// the target ("party", "actor:N"), whose detail contains `detail`, in the last within_seconds of the trace clock or
// between after and before (trace seconds). Without bounds at least one must match. max_in_window: {count, seconds}:
// no span of that many trace seconds holds more than count of them (an animation's crossfades flickering).
bool assertAiTrace(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["ai_trace"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !ensureRuntimeDriver(context, failures))
    {
        failures.push_back(stepLocation(step) + ": ai_trace must be a map");
        return false;
    }

    // `decision` is one name or a list of them (any of which matches: detect or taunt_detect, a notice either way).
    std::vector<std::string> decisions;

    if (node["decision"] && node["decision"].IsSequence())
    {
        for (const YAML::Node &name : node["decision"])
        {
            decisions.push_back(name.as<std::string>(""));
        }
    }
    else if (node["decision"])
    {
        decisions.push_back(node["decision"].as<std::string>(""));
    }

    const std::string event = node["event"].as<std::string>("");

    if (decisions.empty() == event.empty())
    {
        failures.push_back(stepLocation(step) + ": ai_trace needs one of 'decision' or 'event'");
        return false;
    }

    for (const std::string &decision : decisions)
    {
        if (!actorAiDecisionFromName(decision))
        {
            failures.push_back(stepLocation(step) + ": ai_trace: unknown decision '" + decision + "'");
            return false;
        }
    }

    if (!event.empty()
        && std::find(ActorAiTraceEventNames.begin(), ActorAiTraceEventNames.end(), event)
            == ActorAiTraceEventNames.end())
    {
        failures.push_back(stepLocation(step) + ": ai_trace: unknown event '" + event + "'");
        return false;
    }

    std::optional<size_t> actorIndex;

    if (!aiTraceActorFilter(context, step, node, actorIndex, failures))
    {
        return false;
    }

    const ActorAiTrace &trace = context.runtimeDriver->aiTrace();
    const std::string target = node["target"].as<std::string>("");
    const std::string detail = node["detail"].as<std::string>("");
    const float after = node["within_seconds"]
        ? trace.timeSeconds() - node["within_seconds"].as<float>()
        : node["after"].as<float>(-1.0f);
    const float before = node["before"].as<float>(std::numeric_limits<float>::max());
    std::vector<const ActorAiTraceEntry *> matches;

    for (const ActorAiTraceEntry &entry : trace.entries())
    {
        const bool nameMatches = decisions.empty()
            ? entry.name == event
            : std::find(decisions.begin(), decisions.end(), entry.name) != decisions.end();

        if ((!actorIndex || entry.actorIndex == *actorIndex) && entry.decision == !decisions.empty() && nameMatches
            && (target.empty() || entry.target == target || entry.target.starts_with(target + ":"))
            && (detail.empty() || entry.detail.find(detail) != std::string::npos)
            && entry.timeSeconds >= after && entry.timeSeconds <= before)
        {
            matches.push_back(&entry);
        }
    }

    const bool bounded = node["min_count"] || node["max_count"] || node["max_in_window"];
    const size_t minCount = node["min_count"].as<size_t>(bounded ? 0 : 1);
    const size_t maxCount = node["max_count"].as<size_t>(std::numeric_limits<size_t>::max());
    std::string decisionNames;

    for (const std::string &decision : decisions)
    {
        decisionNames += (decisionNames.empty() ? "" : "|") + decision;
    }

    const std::string what = (decisions.empty() ? "event " + event : "decision " + decisionNames)
        + (actorIndex ? " actor " + std::to_string(*actorIndex) : std::string()) + (target.empty() ? "" : " " + target)
        + (detail.empty() ? "" : " \"" + detail + "\"");
    scenarioLog(context, ScenarioLogColor::Cyan, "AI TRACE " + what + ": " + std::to_string(matches.size())
        + " matching lines, trace t=" + std::to_string(trace.timeSeconds()));

    if (node["report"].as<bool>(false))
    {
        for (const ActorAiTraceEntry *pEntry : matches)
        {
            scenarioLog(context, ScenarioLogColor::Default, formatActorAiTraceLine(*pEntry));
        }
    }

    if (matches.size() < minCount || matches.size() > maxCount)
    {
        failures.push_back(stepLocation(step) + ": ai_trace " + what + ": " + std::to_string(matches.size())
            + " matching lines, expected " + std::to_string(minCount) + (maxCount == std::numeric_limits<size_t>::max()
                ? std::string(" or more") : " to " + std::to_string(maxCount)));
        return false;
    }

    if (const YAML::Node window = node["max_in_window"])
    {
        if (!window.IsMap() || !window["count"] || !window["seconds"])
        {
            failures.push_back(stepLocation(step) + ": ai_trace max_in_window needs 'count' and 'seconds'");
            return false;
        }

        const size_t windowCount = window["count"].as<size_t>();
        const float windowSeconds = window["seconds"].as<float>();
        size_t first = 0;

        // The matches are in trace order: slide a window ending at each one.
        for (size_t last = 0; last < matches.size(); ++last)
        {
            while (matches[last]->timeSeconds - matches[first]->timeSeconds > windowSeconds)
            {
                ++first;
            }

            if (last - first + 1 > windowCount)
            {
                failures.push_back(stepLocation(step) + ": ai_trace " + what + ": "
                    + std::to_string(last - first + 1) + " matching lines within " + std::to_string(windowSeconds)
                    + " s from t=" + std::to_string(matches[first]->timeSeconds) + ", expected at most "
                    + std::to_string(windowCount));
                return false;
            }
        }
    }

    return true;
}

// actor_count: {name, monster_id, boss, shrunk, hurt, hostile, near: [x, y, radius], min, max}: the living actors of the
// map that match; `near` keeps those standing within `radius` of (x, y).
bool assertActorCount(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node countNode = step.payload["actor_count"];

    if (!countNode)
    {
        return true;
    }

    if (!countNode.IsMap() || !ensureRuntimeDriver(context, failures))
    {
        failures.push_back(stepLocation(step) + ": actor_count must be a map");
        return false;
    }

    const std::string name = countNode["name"].as<std::string>("");
    const int monsterId = countNode["monster_id"].as<int>(0);
    const auto optionalFlag = [&countNode](const char *pKey)
    {
        return countNode[pKey] ? std::optional<bool>(countNode[pKey].as<bool>()) : std::nullopt;
    };
    const std::optional<bool> boss = optionalFlag("boss");
    // Shrunk by Shrinking Ray, or below full health.
    const std::optional<bool> shrunk = optionalFlag("shrunk");
    const std::optional<bool> hurt = optionalFlag("hurt");
    // Hostile to the party.
    const std::optional<bool> hostile = optionalFlag("hostile");
    const YAML::Node nearNode = countNode["near"];

    if (nearNode && (!nearNode.IsSequence() || nearNode.size() != 3))
    {
        failures.push_back(stepLocation(step) + ": actor_count near must be [x, y, radius]");
        return false;
    }

    size_t matches = 0;

    for (size_t actorIndex = 0; actorIndex < context.runtimeDriver->mapActorCount(); ++actorIndex)
    {
        GameplayActorInspectState inspectState = {};
        GameplayRuntimeActorState runtimeState = {};
        bool hasRuntimeState = false;
        std::string failure;

        if (!context.runtimeDriver->actorInspectState(actorIndex, inspectState, runtimeState, hasRuntimeState, failure)
            || inspectState.isDead || inspectState.currentHp <= 0)
        {
            continue;
        }

        if ((name.empty() || inspectState.displayName == name)
            && (monsterId == 0 || inspectState.monsterId == monsterId)
            && (!boss || (inspectState.rulesetFacts.bossAffix != 0) == *boss)
            && (!shrunk || (inspectState.shrinkRemainingSeconds > 0.0f) == *shrunk)
            && (!hurt || (inspectState.currentHp < inspectState.maxHp) == *hurt)
            && (!hostile || (hasRuntimeState && runtimeState.hostileToParty == *hostile))
            && (!nearNode || (hasRuntimeState
                && std::hypot(runtimeState.preciseX - nearNode[0].as<float>(),
                    runtimeState.preciseY - nearNode[1].as<float>()) <= nearNode[2].as<float>())))
        {
            ++matches;
        }
    }

    const size_t minimum = countNode["min"].as<size_t>(0);
    const size_t maximum = countNode["max"].as<size_t>(std::numeric_limits<size_t>::max());

    if (matches < minimum || matches > maximum)
    {
        failures.push_back(stepLocation(step) + ": actor_count found " + std::to_string(matches) + " living actors"
            + (name.empty() ? std::string() : " named '" + name + "'")
            + (monsterId != 0 ? " of monster " + std::to_string(monsterId) : std::string()));
        return false;
    }

    return true;
}

bool assertActorVisible(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node actorNode = step.payload["actor_visible"];

    if (!actorNode)
    {
        return true;
    }

    if (!actorNode.IsMap() || !actorNode["actor_index"] || !actorNode["actor_index"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": actor_visible assertion requires scalar field 'actor_index'");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    if (actorNode["map"] && actorNode["map"].IsScalar())
    {
        const std::string mapFileName = actorNode["map"].as<std::string>();

        if (lowerAscii(context.runtimeDriver->currentMapFileName()) != lowerAscii(mapFileName))
        {
            std::string loadFailure;
            if (!context.runtimeDriver->loadMap(mapFileName, loadFailure))
            {
                failures.push_back(stepLocation(step) + ": " + loadFailure);
                return false;
            }
        }
    }

    GameplayActorInspectState inspectState = {};
    GameplayRuntimeActorState runtimeState = {};
    bool hasRuntimeState = false;
    std::string failure;
    const size_t actorIndex = scenarioActorIndex(context, actorNode["actor_index"]);

    if (!context.runtimeDriver->actorInspectState(actorIndex, inspectState, runtimeState, hasRuntimeState, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    if (actorNode["report_state"].as<bool>(false))
    {
        std::ostringstream message;
        message << "ACTOR index=" << actorIndex << " name=" << inspectState.displayName
                << " hp=" << inspectState.currentHp << '/' << inspectState.maxHp
                << " dead=" << boolText(inspectState.isDead)
                << " risen=" << boolText(inspectState.rulesetFacts.risen)
                << " boss=" << int(inspectState.rulesetFacts.bossAffix);
        if (hasRuntimeState)
        {
            message << " position=" << runtimeState.preciseX << ',' << runtimeState.preciseY
                    << ',' << runtimeState.preciseZ
                    << " yaw_degrees=" << runtimeState.yawRadians * 180.0f / 3.14159265f
                    << " animation=" << static_cast<int>(runtimeState.animationState)
                    << " hostile=" << boolText(runtimeState.hostileToParty)
                    << " targeting_party=" << boolText(runtimeState.combatTargetingParty)
                    << " aim_target=" << boolText(runtimeState.hasAimTarget);
            if (!runtimeState.scriptedClip.empty())
            {
                message << " scripted_clip=" << runtimeState.scriptedClip;
            }
            if (runtimeState.shield.present)
            {
                message << " shield=" << runtimeState.shield.fraction
                        << " shield_raised=" << boolText(runtimeState.shield.raised);
            }
        }
        scenarioLog(context, ScenarioLogColor::Default, message.str());
    }

    bool success = true;

    if (actorNode["monster_id"] && actorNode["monster_id"].IsScalar()
        && inspectState.monsterId != actorNode["monster_id"].as<uint32_t>())
    {
        failures.push_back(stepLocation(step) + ": actor_visible monster_id mismatch");
        success = false;
    }

    if (actorNode["name"] && actorNode["name"].IsScalar()
        && inspectState.displayName != actorNode["name"].as<std::string>())
    {
        failures.push_back(stepLocation(step) + ": actor_visible name mismatch");
        success = false;
    }

    if (actorNode["dead"] && actorNode["dead"].IsScalar()
        && inspectState.isDead != actorNode["dead"].as<bool>())
    {
        failures.push_back(stepLocation(step) + ": actor_visible dead state mismatch");
        success = false;
    }

    // hidden: the actor is invisible (a script removed or hid it), or shown.
    if (actorNode["hidden"] && actorNode["hidden"].IsScalar()
        && (!hasRuntimeState || runtimeState.isInvisible != actorNode["hidden"].as<bool>()))
    {
        failures.push_back(stepLocation(step) + ": actor_visible hidden state mismatch");
        success = false;
    }

    const auto checkRuntimeField = [&](const char *pKey, const std::string &actual)
    {
        const YAML::Node expected = actorNode[pKey];

        if (!expected)
        {
            return true;
        }

        if (!expected.IsScalar())
        {
            failures.push_back(stepLocation(step) + ": actor_visible requires scalar field " + pKey);
            return false;
        }

        return recordScenarioAssertion(
            context, step, std::string("actor_visible.") + pKey, expected.as<std::string>(), actual, failures);
    };
    success = checkRuntimeField("current_hp", std::to_string(inspectState.currentHp)) && success;
    success = checkRuntimeField("max_hp", std::to_string(inspectState.maxHp)) && success;

    for (const char *pKey : {"hostile_to_party", "has_detected_party", "combat_targeting_party"})
    {
        if (!actorNode[pKey])
        {
            continue;
        }

        if (!hasRuntimeState)
        {
            failures.push_back(stepLocation(step) + ": actor_visible requires live runtime state for " + pKey);
            success = false;
            continue;
        }

        const bool value = std::string(pKey) == "hostile_to_party" ? runtimeState.hostileToParty
            : std::string(pKey) == "has_detected_party" ? runtimeState.hasDetectedParty
            : runtimeState.combatTargetingParty;
        success = checkRuntimeField(pKey, boolText(value)) && success;
    }

    // near: {x, y, max_distance, min_z}: the actor stands within max_distance of a point (horizontally), its feet at
    // least min_z high when given (on a ledge); far: {x, y, min_distance}: at least that far from it; faces: {x, y,
    // within_degrees}: its yaw points at it.
    for (const char *pKey : {"near", "far", "faces"})
    {
        const YAML::Node pointNode = actorNode[pKey];

        if (!pointNode)
        {
            continue;
        }

        const char *pLimitKey = std::string(pKey) == "near" ? "max_distance"
            : std::string(pKey) == "far" ? "min_distance" : "within_degrees";

        if (!hasRuntimeState || !pointNode.IsMap() || !pointNode["x"] || !pointNode["y"] || !pointNode[pLimitKey])
        {
            failures.push_back(stepLocation(step) + ": actor_visible " + pKey + " needs live state, x, y and "
                + pLimitKey);
            success = false;
            continue;
        }

        const float dx = pointNode["x"].as<float>() - runtimeState.preciseX;
        const float dy = pointNode["y"].as<float>() - runtimeState.preciseY;
        const float limit = pointNode[pLimitKey].as<float>();
        const float distance = std::hypot(dx, dy);
        const float offDegrees = std::abs(std::remainder(std::atan2(dy, dx) - runtimeState.yawRadians,
            2.0f * 3.14159265f)) * 180.0f / 3.14159265f;
        const bool highEnough = !pointNode["min_z"] || runtimeState.preciseZ >= pointNode["min_z"].as<float>();
        const bool passed = std::string(pKey) == "near" ? distance <= limit && highEnough
            : std::string(pKey) == "far" ? distance >= limit : offDegrees <= limit;

        if (!passed)
        {
            std::ostringstream message;
            message << stepLocation(step) << ": actor_visible " << pKey << " failed: distance=" << distance
                    << " z=" << runtimeState.preciseZ << " off_degrees=" << offDegrees << " limit=" << limit;
            failures.push_back(message.str());
            success = false;
        }
    }

    if (actorNode["has_aim_target"])
    {
        success = hasRuntimeState
            && checkRuntimeField("has_aim_target", boolText(runtimeState.hasAimTarget)) && success;
    }

    // Hit points (inspect state) and the energy shield (GameplayActorShieldView): exact HP, HP below a value, the
    // shield raised or not, and the shield's share of its pool within [min, max].
    if (actorNode["hp"] && inspectState.currentHp != actorNode["hp"].as<int>())
    {
        failures.push_back(
            stepLocation(step) + ": actor_visible hp mismatch: " + std::to_string(inspectState.currentHp));
        success = false;
    }

    if (actorNode["hp_below"] && inspectState.currentHp >= actorNode["hp_below"].as<int>())
    {
        failures.push_back(
            stepLocation(step) + ": actor_visible hp_below failed: " + std::to_string(inspectState.currentHp));
        success = false;
    }

    if (actorNode["shield_raised"])
    {
        success = hasRuntimeState && runtimeState.shield.present
            && checkRuntimeField("shield_raised", boolText(runtimeState.shield.raised)) && success;
    }

    if (const YAML::Node fractionNode = actorNode["shield_fraction"])
    {
        const float minimum = fractionNode[0].as<float>();
        const float maximum = fractionNode[1].as<float>();

        if (!hasRuntimeState || !runtimeState.shield.present || runtimeState.shield.fraction < minimum - 0.0001f
            || runtimeState.shield.fraction > maximum + 0.0001f)
        {
            failures.push_back(stepLocation(step) + ": actor_visible shield_fraction failed: "
                + (hasRuntimeState && runtimeState.shield.present ? std::to_string(runtimeState.shield.fraction)
                    : std::string("no shield")));
            success = false;
        }
    }
    syncContextFromRuntime(context);
    return success;
}

bool partyHasScenarioItem(const Party &party, uint32_t itemId)
{
    return itemId != 0 && (party.inventoryItemCount(itemId) > 0 || party.heldItemIdForQueries() == itemId);
}

bool isMmergeCrossContinentScrollItemId(uint32_t itemId)
{
    return itemId >= 770 && itemId <= 772;
}

bool isMmergeCrossContinentScrollItemNode(const YAML::Node &node)
{
    if (!node || !node.IsMap())
    {
        return false;
    }

    if (node["item_id"] && node["item_id"].IsScalar()
        && isMmergeCrossContinentScrollItemId(node["item_id"].as<uint32_t>()))
    {
        return true;
    }

    return node["item_name"] && node["item_name"].IsScalar()
        && node["item_name"].as<std::string>() == "Letter for YOU.";
}

bool assertQuestItemLocationObservation(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const char *pFieldName,
    std::vector<std::string> &failures)
{
    const YAML::Node observationNode = step.payload[pFieldName];

    if (!observationNode)
    {
        return true;
    }

    if (!observationNode.IsMap() || !observationNode["item_id"] || !observationNode["item_id"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": " + pFieldName
            + " observation must contain scalar field 'item_id'");
        return false;
    }

    const uint32_t itemId = observationNode["item_id"].as<uint32_t>();

    if (std::string(pFieldName) == "chest_contains_quest_item"
        && isMmergeCrossContinentScrollItemNode(observationNode))
    {
        return true;
    }

    if (partyHasScenarioItem(context.party, itemId))
    {
        scenarioLogAssert(
            context,
            step,
            "item_id",
            std::to_string(itemId),
            std::to_string(itemId),
            true);
        return true;
    }

    std::string mapFileName = context.currentMapFileName;

    if (observationNode["map"] && observationNode["map"].IsScalar())
    {
        mapFileName = observationNode["map"].as<std::string>();
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    seedRuntimeDriverFromContext(context);

    if (!mapFileName.empty()
        && (!context.runtimeDriver->hasActiveRuntime()
            || lowerAscii(context.runtimeDriver->currentMapFileName()) != lowerAscii(mapFileName)))
    {
        std::string loadFailure;

        if (!context.runtimeDriver->loadMap(mapFileName, loadFailure))
        {
            failures.push_back(stepLocation(step) + ": " + loadFailure);
            return context.mode != ScenarioMode::Faithful;
        }

        seedRuntimeDriverFromContext(context);
    }

    bool containsItem = false;
    std::string failure;
    bool inspected = false;

    if (std::string(pFieldName) == "world_item_spawned")
    {
        std::optional<size_t> worldItemIndex;

        if (observationNode["world_item_index"] && observationNode["world_item_index"].IsScalar())
        {
            worldItemIndex = observationNode["world_item_index"].as<size_t>();
        }

        inspected = context.runtimeDriver->worldItemContainsItem(worldItemIndex, itemId, containsItem, failure);
    }
    else if (std::string(pFieldName) == "chest_contains_quest_item")
    {
        std::optional<uint32_t> chestId;

        if (observationNode["chest_id"] && observationNode["chest_id"].IsScalar())
        {
            chestId = observationNode["chest_id"].as<uint32_t>();
        }

        inspected = context.runtimeDriver->activeChestContainsItem(chestId, itemId, containsItem, failure);
    }
    else if (std::string(pFieldName) == "corpse_contains_quest_item")
    {
        std::optional<uint32_t> corpseIndex;

        if (observationNode["corpse_index"] && observationNode["corpse_index"].IsScalar())
        {
            corpseIndex = observationNode["corpse_index"].as<uint32_t>();
        }
        else if (observationNode["actor_index"] && observationNode["actor_index"].IsScalar())
        {
            corpseIndex = observationNode["actor_index"].as<uint32_t>();
        }

        inspected = context.runtimeDriver->activeCorpseContainsItem(corpseIndex, itemId, containsItem, failure);
    }

    syncContextFromRuntime(context);

    if (containsItem || partyHasScenarioItem(context.party, itemId))
    {
        scenarioLogAssert(
            context,
            step,
            "item_id",
            std::to_string(itemId),
            std::to_string(itemId),
            true);
        return true;
    }

    if (context.mode != ScenarioMode::Faithful && context.party.tryGrantItem(itemId))
    {
        scenarioLogAssert(
            context,
            step,
            "item_id",
            std::to_string(itemId),
            std::to_string(itemId),
            true);
        return true;
    }

    scenarioLogAssert(
        context,
        step,
        "item_id",
        std::to_string(itemId),
        "<missing>",
        false);

    if (!inspected)
    {
        failures.push_back(stepLocation(step) + ": " + failure);
    }
    else
    {
        failures.push_back(stepLocation(step) + ": " + pFieldName + " did not expose item "
            + std::to_string(itemId));
    }

    return false;
}

bool assertItemVisible(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node itemNode = step.payload["item_visible"];

    if (!itemNode)
    {
        return true;
    }

    if (!itemNode.IsMap() || !itemNode["item_id"] || !itemNode["item_id"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": item_visible assertion requires scalar field 'item_id'");
        return false;
    }

    const uint32_t itemId = itemNode["item_id"].as<uint32_t>();
    const std::string source = itemNode["source"] && itemNode["source"].IsScalar()
        ? lowerAscii(itemNode["source"].as<std::string>())
        : "";

    if (source == "chest" && isMmergeCrossContinentScrollItemNode(itemNode))
    {
        return true;
    }

    if (partyHasScenarioItem(context.party, itemId))
    {
        return true;
    }

    if (source == "inventory" || source == "equipment" || source == "held")
    {
        if (context.mode != ScenarioMode::Faithful && context.party.tryGrantItem(itemId))
        {
            return true;
        }

        failures.push_back(stepLocation(step) + ": item_visible did not find item "
            + std::to_string(itemId) + " in party-visible item state");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return context.mode != ScenarioMode::Faithful;
    }

    seedRuntimeDriverFromContext(context);

    bool containsItem = false;
    std::string failure;
    bool inspected = true;

    if (source == "world_item")
    {
        std::optional<size_t> worldItemIndex;

        if (itemNode["world_item_index"] && itemNode["world_item_index"].IsScalar())
        {
            worldItemIndex = itemNode["world_item_index"].as<size_t>();
        }

        inspected = context.runtimeDriver->worldItemContainsItem(worldItemIndex, itemId, containsItem, failure);
    }
    else if (source == "chest")
    {
        std::optional<uint32_t> chestId;

        if (itemNode["chest_id"] && itemNode["chest_id"].IsScalar())
        {
            chestId = itemNode["chest_id"].as<uint32_t>();
        }

        inspected = context.runtimeDriver->activeChestContainsItem(chestId, itemId, containsItem, failure);
    }
    else if (source == "corpse")
    {
        std::optional<uint32_t> corpseIndex;

        if (itemNode["corpse_index"] && itemNode["corpse_index"].IsScalar())
        {
            corpseIndex = itemNode["corpse_index"].as<uint32_t>();
        }

        inspected = context.runtimeDriver->activeCorpseContainsItem(corpseIndex, itemId, containsItem, failure);
    }
    else if (context.mode != ScenarioMode::Faithful)
    {
        return true;
    }

    syncContextFromRuntime(context);

    if (containsItem || partyHasScenarioItem(context.party, itemId))
    {
        return true;
    }

    if (context.mode != ScenarioMode::Faithful)
    {
        return true;
    }

    failures.push_back(stepLocation(step) + ": item_visible did not expose item "
        + std::to_string(itemId) + (inspected ? "" : ": " + failure));
    return false;
}

bool appendStringMismatch(
    const ScenarioStep &step,
    const char *pAssertionName,
    const char *pFieldName,
    const std::string &actual,
    const YAML::Node &node,
    std::vector<std::string> &failures)
{
    if (!node[pFieldName] || !node[pFieldName].IsScalar())
    {
        return true;
    }

    const std::string expected = node[pFieldName].as<std::string>();
    if (lowerAscii(actual) == lowerAscii(expected))
    {
        return true;
    }

    failures.push_back(stepLocation(step) + ": " + pAssertionName + ' ' + pFieldName
        + " expected '" + expected + "' but found '" + actual + "'");
    return false;
}

bool appendUIntMismatch(
    const ScenarioStep &step,
    const char *pAssertionName,
    const char *pFieldName,
    uint32_t actual,
    const YAML::Node &node,
    std::vector<std::string> &failures)
{
    if (!node[pFieldName] || !node[pFieldName].IsScalar())
    {
        return true;
    }

    const uint32_t expected = node[pFieldName].as<uint32_t>();
    if (actual == expected)
    {
        return true;
    }

    failures.push_back(stepLocation(step) + ": " + pAssertionName + ' ' + pFieldName
        + " expected " + std::to_string(expected) + " but found " + std::to_string(actual));
    return false;
}

bool appendBoolMismatch(
    const ScenarioStep &step,
    const char *pAssertionName,
    const char *pFieldName,
    bool actual,
    const YAML::Node &node,
    std::vector<std::string> &failures)
{
    if (!node[pFieldName] || !node[pFieldName].IsScalar())
    {
        return true;
    }

    const bool expected = node[pFieldName].as<bool>();
    if (actual == expected)
    {
        return true;
    }

    failures.push_back(stepLocation(step) + ": " + pAssertionName + ' ' + pFieldName
        + " expected " + (expected ? "true" : "false") + " but found " + (actual ? "true" : "false"));
    return false;
}

bool assertMapTransitionTrace(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const char *pFieldName,
    const std::optional<EventRuntimeState::MapTransitionTrace> EventRuntimeState::*pMember,
    std::vector<std::string> &failures)
{
    const YAML::Node transitionNode = step.payload[pFieldName];

    if (!transitionNode)
    {
        return true;
    }

    if (context.runtimeDriver)
    {
        syncContextFromRuntime(context);
    }

    if (!context.eventRuntimeStateLoaded || !(context.eventRuntimeState.*pMember).has_value())
    {
        if (context.mode == ScenarioMode::Faithful)
        {
            failures.push_back(stepLocation(step) + ": expected " + pFieldName
                + " trace but no transition trace was recorded");
        }

        return context.mode != ScenarioMode::Faithful;
    }

    const EventRuntimeState::MapTransitionTrace &trace = *(context.eventRuntimeState.*pMember);
    bool success = true;
    success = appendStringMismatch(step, pFieldName, "source_kind", trace.sourceKind, transitionNode, failures)
        && success;
    success = appendUIntMismatch(step, pFieldName, "source_id", trace.sourceId, transitionNode, failures)
        && success;
    success = appendUIntMismatch(step, pFieldName, "action_id", trace.actionId, transitionNode, failures)
        && success;
    success = appendUIntMismatch(step, pFieldName, "event_id", trace.eventId, transitionNode, failures)
        && success;
    success = appendBoolMismatch(
        step,
        pFieldName,
        "confirmation_required",
        trace.confirmationRequired,
        transitionNode,
        failures) && success;
    success = appendStringMismatch(step, pFieldName, "destination_map", trace.destinationMap, transitionNode, failures)
        && success;
    success =
        appendStringMismatch(step, pFieldName, "destination_name", trace.destinationName, transitionNode, failures)
        && success;
    success = appendUIntMismatch(step, pFieldName, "travel_days", trace.travelDays, transitionNode, failures)
        && success;
    if (transitionNode["use_start_position"] && transitionNode["use_start_position"].IsScalar())
    {
        const bool expectedUseStartPosition = transitionNode["use_start_position"].as<bool>();
        if (trace.useStartPosition != expectedUseStartPosition)
        {
            scenarioLog(
                context,
                ScenarioLogColor::Yellow,
                "WARNING step=" + std::to_string(step.stepIndex)
                    + " trace_line=" + std::to_string(step.sourceLine)
                    + " " + pFieldName + ".use_start_position expected="
                    + boolText(expectedUseStartPosition)
                    + " actual=" + boolText(trace.useStartPosition));
        }
    }

    if (transitionNode["route_index"] && transitionNode["route_index"].IsScalar())
    {
        const uint32_t expected = transitionNode["route_index"].as<uint32_t>();
        if (!trace.routeIndex.has_value() || *trace.routeIndex != expected)
        {
            failures.push_back(stepLocation(step) + ": " + pFieldName + " route_index mismatch");
            success = false;
        }
    }

    if (transitionNode["direction_degrees"] && transitionNode["direction_degrees"].IsScalar())
    {
        const std::string expectedText = transitionNode["direction_degrees"].as<std::string>();
        if (expectedText == "none")
        {
            if (trace.directionDegrees.has_value())
            {
                failures.push_back(stepLocation(step) + ": " + pFieldName + " direction_degrees mismatch");
                success = false;
            }
        }
        else if (!trace.directionDegrees.has_value()
                 || *trace.directionDegrees != transitionNode["direction_degrees"].as<int32_t>())
        {
            failures.push_back(stepLocation(step) + ": " + pFieldName + " direction_degrees mismatch");
            success = false;
        }
    }

    if (transitionNode["pos"] && transitionNode["pos"].IsScalar())
    {
        const std::string actualPos = "(" + std::to_string(trace.x) + "," + std::to_string(trace.y)
            + "," + std::to_string(trace.z) + ")";
        if (transitionNode["pos"].as<std::string>() != actualPos)
        {
            failures.push_back(stepLocation(step) + ": " + pFieldName + " pos mismatch");
            success = false;
        }
    }

    return context.mode != ScenarioMode::Faithful || success;
}

bool assertChestOpened(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node chestNode = step.payload["chest_opened"];

    if (!chestNode)
    {
        return true;
    }

    if (context.runtimeDriver)
    {
        syncContextFromRuntime(context);
    }

    // `absent: true`: no chest has opened since the map loaded (a chest the rules keep shut).
    if (chestNode["absent"].as<bool>(false))
    {
        if (context.eventRuntimeStateLoaded && context.eventRuntimeState.lastChestOpened.has_value())
        {
            failures.push_back(stepLocation(step) + ": chest_opened expected none, chest "
                + std::to_string(context.eventRuntimeState.lastChestOpened->chestId) + " opened");
            return context.mode != ScenarioMode::Faithful;
        }

        return true;
    }

    if (!context.eventRuntimeStateLoaded || !context.eventRuntimeState.lastChestOpened.has_value())
    {
        return context.mode != ScenarioMode::Faithful;
    }

    const EventRuntimeState::ChestOpenedTrace &trace = *context.eventRuntimeState.lastChestOpened;
    bool success = true;
    success = appendStringMismatch(step, "chest_opened", "scene_kind", trace.sceneKind, chestNode, failures)
        && success;
    success = appendStringMismatch(step, "chest_opened", "map", trace.map, chestNode, failures) && success;
    success = appendUIntMismatch(step, "chest_opened", "chest_id", trace.chestId, chestNode, failures) && success;
    success = appendUIntMismatch(
        step,
        "chest_opened",
        "item_count",
        static_cast<uint32_t>(trace.itemCount),
        chestNode,
        failures) && success;
    success = appendUIntMismatch(
        step,
        "chest_opened",
        "hidden_item_count",
        static_cast<uint32_t>(trace.hiddenItemCount),
        chestNode,
        failures) && success;
    return context.mode != ScenarioMode::Faithful || success;
}

// chest_view: {open, chest_id}: whether a chest's loot screen is open now (and which chest).
bool assertChestView(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["chest_view"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !ensureRuntimeDriver(context, failures))
    {
        failures.push_back(stepLocation(step) + ": chest_view assertion requires a map and a live runtime");
        return false;
    }

    const ScenarioRuntimeDriver &runtimeDriver = *context.runtimeDriver;
    const IGameplayWorldRuntime *pWorldRuntime = runtimeDriver.worldRuntime();
    const GameplayChestViewState *pChestView = pWorldRuntime != nullptr ? pWorldRuntime->activeChestView() : nullptr;
    const bool expectedOpen = node["open"].as<bool>(true);
    const bool open = pChestView != nullptr;
    scenarioLogAssert(
        context,
        step,
        "chest_view.open",
        expectedOpen ? "true" : "false",
        open ? "true" : "false",
        open == expectedOpen);

    if (open != expectedOpen)
    {
        failures.push_back(stepLocation(step) + ": chest view " + (open ? "open" : "closed") + ", expected "
            + (expectedOpen ? "open" : "closed"));
        return false;
    }

    if (open && node["chest_id"] && pChestView->chestId != node["chest_id"].as<uint32_t>())
    {
        failures.push_back(stepLocation(step) + ": chest view shows chest " + std::to_string(pChestView->chestId)
            + ", expected " + node["chest_id"].as<std::string>());
        return false;
    }

    return true;
}

// party_position: {x, y, radius, z_min, z_max}: the party stands within `radius` (default 64) of (x, y), its feet
// between z_min and z_max when given.
bool assertPartyPosition(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["party_position"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !node["x"] || !node["y"] || !ensureRuntimeDriver(context, failures))
    {
        failures.push_back(stepLocation(step) + ": party_position assertion requires x, y and a live runtime");
        return false;
    }

    const ScenarioPose pose = context.runtimeDriver->currentPose();
    const float dx = pose.x - node["x"].as<float>();
    const float dy = pose.y - node["y"].as<float>();
    const float radius = node["radius"].as<float>(64.0f);
    const bool inside = dx * dx + dy * dy <= radius * radius
        && (!node["z_min"] || pose.z >= node["z_min"].as<float>())
        && (!node["z_max"] || pose.z <= node["z_max"].as<float>());
    const std::string actual =
        "(" + std::to_string(pose.x) + ", " + std::to_string(pose.y) + ", " + std::to_string(pose.z) + ")";
    scenarioLogAssert(
        context,
        step,
        "party_position",
        "(" + node["x"].as<std::string>() + ", " + node["y"].as<std::string>() + ")",
        actual,
        inside);

    if (!inside)
    {
        failures.push_back(stepLocation(step) + ": party at " + actual + ", expected within "
            + std::to_string(radius) + " of (" + node["x"].as<std::string>() + ", " + node["y"].as<std::string>()
            + ")");
        return false;
    }

    return true;
}

bool assertActorDialogStarted(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node dialogNode = step.payload["actor_dialog_started"];

    if (!dialogNode)
    {
        return true;
    }

    if (context.runtimeDriver)
    {
        syncContextFromRuntime(context);
    }

    if (!context.eventRuntimeStateLoaded || !context.eventRuntimeState.lastActorDialogStarted.has_value())
    {
        return context.mode != ScenarioMode::Faithful;
    }

    const EventRuntimeState::ActorDialogStartedTrace &trace =
        *context.eventRuntimeState.lastActorDialogStarted;
    bool success = true;
    success = appendStringMismatch(step, "actor_dialog_started", "kind", trace.kind, dialogNode, failures)
        && success;
    success = appendStringMismatch(step, "actor_dialog_started", "map", trace.map, dialogNode, failures) && success;
    success = appendUIntMismatch(step, "actor_dialog_started", "npc_id", trace.npcId, dialogNode, failures)
        && success;
    success = appendUIntMismatch(step, "actor_dialog_started", "source_id", trace.sourceId, dialogNode, failures)
        && success;
    success = appendUIntMismatch(
        step,
        "actor_dialog_started",
        "host_house_id",
        trace.hostHouseId,
        dialogNode,
        failures) && success;

    if (dialogNode["actor_index"] && dialogNode["actor_index"].IsScalar())
    {
        const std::string expectedText = dialogNode["actor_index"].as<std::string>();
        if (expectedText == "none")
        {
            if (trace.actorIndex.has_value())
            {
                failures.push_back(stepLocation(step) + ": actor_dialog_started actor_index mismatch");
                success = false;
            }
        }
        else if (!trace.actorIndex.has_value() || *trace.actorIndex != dialogNode["actor_index"].as<uint32_t>())
        {
            failures.push_back(stepLocation(step) + ": actor_dialog_started actor_index mismatch");
            success = false;
        }
    }

    return context.mode != ScenarioMode::Faithful || success;
}

bool assertPressurePlateTriggered(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node pressureNode = step.payload["pressure_plate_triggered"];

    if (!pressureNode)
    {
        return true;
    }

    if (context.runtimeDriver)
    {
        syncContextFromRuntime(context);
    }

    bool shouldTriggerExpectedFace = !context.eventRuntimeStateLoaded
        || !context.eventRuntimeState.lastPressurePlateTrigger.has_value();

    if (pressureNode["force_replay"] && pressureNode["force_replay"].IsScalar()
        && pressureNode["force_replay"].as<bool>())
    {
        shouldTriggerExpectedFace = true;
    }

    if (!shouldTriggerExpectedFace && pressureNode["face_index"] && pressureNode["face_index"].IsScalar())
    {
        const EventRuntimeState::PressurePlateTrigger &trigger =
            *context.eventRuntimeState.lastPressurePlateTrigger;

        if (trigger.faceIndex != pressureNode["face_index"].as<size_t>())
        {
            shouldTriggerExpectedFace = true;
        }
    }

    if (!shouldTriggerExpectedFace && pressureNode["event_id"] && pressureNode["event_id"].IsScalar())
    {
        const EventRuntimeState::PressurePlateTrigger &trigger =
            *context.eventRuntimeState.lastPressurePlateTrigger;

        if (trigger.eventId != pressureNode["event_id"].as<uint32_t>())
        {
            shouldTriggerExpectedFace = true;
        }
    }

    if (!shouldTriggerExpectedFace && pressureNode["world"] && pressureNode["world"].IsScalar())
    {
        const EventRuntimeState::PressurePlateTrigger &trigger =
            *context.eventRuntimeState.lastPressurePlateTrigger;

        if (lowerAscii(trigger.world) != lowerAscii(pressureNode["world"].as<std::string>()))
        {
            shouldTriggerExpectedFace = true;
        }
    }

    if (shouldTriggerExpectedFace)
    {
        if (pressureNode["world"] && pressureNode["world"].IsScalar()
            && lowerAscii(pressureNode["world"].as<std::string>()) == "indoor"
            && pressureNode["face_index"] && pressureNode["face_index"].IsScalar())
        {
            if (!ensureRuntimeDriver(context, failures))
            {
                return context.mode != ScenarioMode::Faithful;
            }

            if (!context.currentMapFileName.empty()
                && (!context.runtimeDriver->hasActiveRuntime()
                    || lowerAscii(context.runtimeDriver->currentMapFileName()) != lowerAscii(context.currentMapFileName)))
            {
                std::string loadFailure;

                if (!context.runtimeDriver->loadMap(context.currentMapFileName, loadFailure))
                {
                    failures.push_back(stepLocation(step) + ": " + loadFailure);
                    return context.mode != ScenarioMode::Faithful;
                }
            }

            seedRuntimeDriverFromContext(context);

            std::string failure;
            const size_t faceIndex = pressureNode["face_index"].as<size_t>();

            if (context.runtimeDriver->triggerIndoorPressurePlate(faceIndex, failure))
            {
                syncContextFromRuntime(context);
                std::cout << "PRESSURE replayed indoor face_index=" << faceIndex << "\n";
            }
            else if (pressureNode["event_id"] && pressureNode["event_id"].IsScalar())
            {
                const uint16_t eventId = pressureNode["event_id"].as<uint16_t>();
                std::string eventFailure;

                if (!context.runtimeDriver->executeMapEvent(eventId, eventFailure))
                {
                    if (context.mode == ScenarioMode::Faithful)
                    {
                        failures.push_back(stepLocation(step) + ": " + failure + "; fallback event "
                            + std::to_string(eventId) + " also failed: " + eventFailure);
                        return false;
                    }
                }
                else
                {
                    syncContextFromRuntime(context);

                    EventRuntimeState::PressurePlateTrigger trigger = {};
                    trigger.world = pressureNode["world"] && pressureNode["world"].IsScalar()
                        ? pressureNode["world"].as<std::string>()
                        : "indoor";
                    trigger.eventId = eventId;
                    trigger.faceIndex = faceIndex;
                    if (pressureNode["attributes"] && pressureNode["attributes"].IsScalar())
                    {
                        trigger.attributes = pressureNode["attributes"].as<uint32_t>();
                    }
                    context.eventRuntimeState.lastPressurePlateTrigger = trigger;
                    context.eventRuntimeStateLoaded = true;
                    if (context.runtimeDriver->eventRuntimeState() != nullptr)
                    {
                        context.runtimeDriver->eventRuntimeState()->lastPressurePlateTrigger = trigger;
                    }

                    scenarioLog(
                        context,
                        ScenarioLogColor::Yellow,
                        "WARNING pressure_plate step=" + std::to_string(step.stepIndex)
                            + " face_index=" + std::to_string(faceIndex)
                            + " could not be retriggered directly; replayed event_id="
                            + std::to_string(eventId));
                }
            }
            else if (context.mode == ScenarioMode::Faithful)
            {
                failures.push_back(stepLocation(step) + ": " + failure);
                return false;
            }
        }
    }

    if (!context.eventRuntimeStateLoaded || !context.eventRuntimeState.lastPressurePlateTrigger.has_value())
    {
        if (context.mode == ScenarioMode::Faithful)
        {
            failures.push_back(stepLocation(step) + ": expected pressure_plate_triggered event but none was recorded");
        }

        return context.mode != ScenarioMode::Faithful;
    }

    const EventRuntimeState::PressurePlateTrigger &trigger =
        *context.eventRuntimeState.lastPressurePlateTrigger;
    bool success = true;

    if (pressureNode["world"] && pressureNode["world"].IsScalar()
        && lowerAscii(trigger.world) != lowerAscii(pressureNode["world"].as<std::string>()))
    {
        failures.push_back(stepLocation(step) + ": pressure_plate_triggered world mismatch");
        success = false;
    }

    if (pressureNode["event_id"] && pressureNode["event_id"].IsScalar()
        && trigger.eventId != pressureNode["event_id"].as<uint32_t>())
    {
        failures.push_back(stepLocation(step) + ": pressure_plate_triggered event_id mismatch");
        success = false;
    }

    if (pressureNode["face_index"] && pressureNode["face_index"].IsScalar()
        && trigger.faceIndex != pressureNode["face_index"].as<size_t>())
    {
        failures.push_back(stepLocation(step) + ": pressure_plate_triggered face_index mismatch");
        success = false;
    }

    if (pressureNode["bmodel_index"] && pressureNode["bmodel_index"].IsScalar()
        && trigger.bmodelIndex != pressureNode["bmodel_index"].as<size_t>())
    {
        failures.push_back(stepLocation(step) + ": pressure_plate_triggered bmodel_index mismatch");
        success = false;
    }

    if (pressureNode["attributes"] && pressureNode["attributes"].IsScalar()
        && trigger.attributes != pressureNode["attributes"].as<uint32_t>())
    {
        failures.push_back(stepLocation(step) + ": pressure_plate_triggered attributes mismatch");
        success = false;
    }

    return context.mode != ScenarioMode::Faithful || success;
}

bool assertDialogueCanceled(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node cancelNode = step.payload["dialogue_canceled"];

    if (!cancelNode)
    {
        return true;
    }

    if (context.runtimeDriver)
    {
        syncContextFromRuntime(context);
    }

    if (!context.eventRuntimeStateLoaded || !context.eventRuntimeState.lastDialogueCanceled.has_value())
    {
        if (context.mode == ScenarioMode::Faithful)
        {
            scenarioLogAssert(context, step, "dialogue_canceled", "present", "<none>", false);
            failures.push_back(stepLocation(step) + ": expected dialogue_canceled event but none was recorded");
        }

        return context.mode != ScenarioMode::Faithful;
    }

    const EventRuntimeState::DialogueCanceled &canceled = *context.eventRuntimeState.lastDialogueCanceled;
    bool success = true;

    if (cancelNode["kind"] && cancelNode["kind"].IsScalar()
        && canceled.kind != cancelNode["kind"].as<std::string>())
    {
        failures.push_back(stepLocation(step) + ": dialogue_canceled kind mismatch");
        success = false;
    }

    if (cancelNode["active_source_id"] && cancelNode["active_source_id"].IsScalar()
        && canceled.activeSourceId != cancelNode["active_source_id"].as<uint32_t>())
    {
        failures.push_back(stepLocation(step) + ": dialogue_canceled active_source_id mismatch");
        success = false;
    }

    if (cancelNode["source_id"] && cancelNode["source_id"].IsScalar()
        && canceled.sourceId != cancelNode["source_id"].as<uint32_t>())
    {
        failures.push_back(stepLocation(step) + ": dialogue_canceled source_id mismatch");
        success = false;
    }

    if (cancelNode["house_dialog"] && cancelNode["house_dialog"].IsScalar()
        && canceled.houseDialog != cancelNode["house_dialog"].as<bool>())
    {
        failures.push_back(stepLocation(step) + ": dialogue_canceled house_dialog mismatch");
        success = false;
    }

    if (cancelNode["action_count"] && cancelNode["action_count"].IsScalar()
        && canceled.actionCount != cancelNode["action_count"].as<size_t>())
    {
        failures.push_back(stepLocation(step) + ": dialogue_canceled action_count mismatch");
        success = false;
    }

    return context.mode != ScenarioMode::Faithful || success;
}

bool applyItemReceivedObservation(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node itemNode = step.payload["item_received"];

    if (!itemNode)
    {
        return true;
    }

    if (!itemNode.IsMap() || !itemNode["item_id"] || !itemNode["item_id"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": item_received assertion must contain scalar field 'item_id'");
        return false;
    }

    const uint32_t itemId = itemNode["item_id"].as<uint32_t>();
    const bool receivedToHeld =
        itemNode["destination"] && itemNode["destination"].IsScalar()
        && itemNode["destination"].as<std::string>() == "held";
    const std::string source = itemNode["source"] && itemNode["source"].IsScalar()
        ? lowerAscii(itemNode["source"].as<std::string>())
        : "";

    if (receivedToHeld)
    {
        if (context.party.heldItemIdForQueries() != itemId)
        {
            if (source == "chest")
            {
                if (!ensureRuntimeDriver(context, failures))
                {
                    return context.mode != ScenarioMode::Faithful;
                }

                seedRuntimeDriverFromContext(context);

                std::optional<uint32_t> chestId;

                if (itemNode["chest_id"] && itemNode["chest_id"].IsScalar())
                {
                    chestId = itemNode["chest_id"].as<uint32_t>();
                }

                GameplayChestItemState chestItem = {};
                std::string failure;

                if (context.runtimeDriver->takeActiveChestItemById(chestId, itemId, chestItem, failure))
                {
                    syncContextFromRuntime(context);
                }
                else if (context.mode == ScenarioMode::Faithful)
                {
                    scenarioLogAssert(
                        context,
                        step,
                        "item_id",
                        std::to_string(itemId),
                        "<missing>",
                        false);
                    failures.push_back(stepLocation(step) + ": " + failure);
                    return false;
                }
            }

            if (context.party.heldItemIdForQueries() == itemId)
            {
                scenarioLogAssert(
                    context,
                    step,
                    "item_id",
                    std::to_string(itemId),
                    std::to_string(itemId),
                    true);
                return true;
            }

            if (context.mode == ScenarioMode::Faithful)
            {
                scenarioLogAssert(
                    context,
                    step,
                    "item_id",
                    std::to_string(itemId),
                    "<missing>",
                    false);
                failures.push_back(stepLocation(step) + ": observed held item " + std::to_string(itemId)
                    + " was not held by the party");
                return false;
            }

            InventoryItem heldItem = {};
            heldItem.objectDescriptionId = itemId;
            heldItem.quantity = 1;
            context.party.setHeldItemForQueries(heldItem);
        }

        scenarioLogAssert(
            context,
            step,
            "item_id",
            std::to_string(itemId),
            std::to_string(itemId),
            true);
        return true;
    }

    bool itemFound = context.party.inventoryItemCount(itemId) > 0;

    if (!itemFound)
    {
        if (context.mode != ScenarioMode::Faithful && context.party.tryGrantItem(itemId))
        {
            itemFound = true;
        }
        else
        {
            scenarioLogAssert(
                context,
                step,
                "item_id",
                std::to_string(itemId),
                "<missing>",
                false);
            failures.push_back(stepLocation(step) + ": observed item " + std::to_string(itemId)
                + " was not in party inventory");
            return false;
        }
    }

    scenarioLogAssert(
        context,
        step,
        "item_id",
        std::to_string(itemId),
        itemFound ? std::to_string(itemId) : "<missing>",
        itemFound);
    return true;
}

bool assertQuestBits(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    const char *pFieldName,
    bool expectedValue,
    std::vector<std::string> &failures)
{
    const YAML::Node qbitNode = step.payload[pFieldName];

    if (!qbitNode)
    {
        return true;
    }

    if (!qbitNode.IsSequence())
    {
        failures.push_back(stepLocation(step) + ": field '" + pFieldName + "' must be a sequence");
        return false;
    }

    bool success = true;

    for (const YAML::Node &entryNode : qbitNode)
    {
        if (!entryNode.IsScalar())
        {
            failures.push_back(stepLocation(step) + ": qbit entries must be scalar");
            success = false;
            continue;
        }

        const uint32_t qbitId = entryNode.as<uint32_t>();
        const bool actualValue = context.party.hasQuestBit(qbitId);
        scenarioLogAssert(
            context,
            step,
            std::string(pFieldName) + "[" + std::to_string(qbitId) + "]",
            boolText(expectedValue),
            boolText(actualValue),
            actualValue == expectedValue);

        if (actualValue != expectedValue)
        {
            if (context.mode == ScenarioMode::Faithful)
            {
                failures.push_back(stepLocation(step) + ": qbit " + std::to_string(qbitId)
                    + " expected " + (expectedValue ? "set" : "clear"));
                success = false;
                continue;
            }

            context.party.setQuestBit(qbitId, expectedValue);
        }
    }

    return success;
}

bool assertRuntimeWorldItemState(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["world_item_state"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !node["item_id"] || !node["item_id"].IsScalar()
        || !node["present"] || !node["present"].IsScalar())
    {
        failures.push_back(stepLocation(step) + ": world_item_state requires scalar item_id and present");
        return false;
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    bool present = false;
    std::string failure;
    const uint32_t itemId = node["item_id"].as<uint32_t>();

    if (!context.runtimeDriver->worldItemContainsItem(std::nullopt, itemId, present, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    return recordScenarioAssertion(
        context, step, "world_item_state[" + std::to_string(itemId) + "]",
        boolText(node["present"].as<bool>()), boolText(present), failures);
}

bool assertRuntimeEventVariable(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    const YAML::Node node = step.payload["runtime_event_variable"];

    if (!node)
    {
        return true;
    }

    if (!node.IsMap() || !node["id"].IsScalar()
        || (!node["value"] && !node["min"] && !node["max"]))
    {
        failures.push_back(stepLocation(step) + ": runtime_event_variable requires id and value, min or max");
        return false;
    }

    for (const char *pKey : {"value", "min", "max"})
    {
        if (node[pKey] && !node[pKey].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": runtime_event_variable requires scalar " + pKey);
            return false;
        }
    }

    if (!ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    const Party *pParty = context.runtimeDriver->party();
    const EventRuntimeState *pRuntimeState = context.runtimeDriver->eventRuntimeState();

    if (pParty == nullptr || pRuntimeState == nullptr)
    {
        failures.push_back(stepLocation(step) + ": runtime_event_variable requires loaded party and event state");
        return false;
    }

    std::optional<size_t> memberIndex;

    if (node["member_index"])
    {
        if (!node["member_index"].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": runtime_event_variable member_index must be scalar");
            return false;
        }

        memberIndex = node["member_index"].as<size_t>();

        if (pParty->member(*memberIndex) == nullptr)
        {
            failures.push_back(stepLocation(step) + ": runtime_event_variable member_index is out of range");
            return false;
        }
    }

    const uint32_t id = node["id"].as<uint32_t>();
    const int32_t actual = EventRuntime::getVariableValue(
        *pRuntimeState, EventRuntime::decodeVariable(id), pParty, memberIndex);
    const std::string field = "runtime_event_variable[" + std::to_string(id) + "]"
        + (memberIndex ? ".member[" + std::to_string(*memberIndex) + "]" : "");
    bool success = true;
    if (node["value"])
    {
        success = recordScenarioAssertion(
            context, step, field, node["value"].as<std::string>(), std::to_string(actual), failures);
    }
    for (const char *pKey : {"min", "max"})
    {
        if (!node[pKey])
        {
            continue;
        }
        const int32_t bound = node[pKey].as<int32_t>();
        const bool isMinimum = std::string(pKey) == "min";
        const bool withinBound = isMinimum ? actual >= bound : actual <= bound;
        const std::string expected = std::string(isMinimum ? ">=" : "<=") + std::to_string(bound);
        scenarioLogAssert(context, step, field, expected, std::to_string(actual), withinBound);
        if (!withinBound)
        {
            failures.push_back(stepLocation(step) + ": expected " + field + expected
                + " but current value=" + std::to_string(actual));
        }
        success = withinBound && success;
    }
    return success;
}

bool runAssert(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    bool success = true;

    if (step.payload["map"])
    {
        if (!step.payload["map"].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": field 'map' must be scalar");
            success = false;
        }
        else
        {
            const std::string expectedMap = step.payload["map"].as<std::string>();
            success = assertCurrentMap(context, step, expectedMap, failures) && success;
        }
    }

    success = assertInventoryAnyMember(context, step, failures) && success;
    success = assertInventoryList(context, step, failures) && success;
    success = assertEquippedItems(context, step, failures) && success;
    success = assertItemSetBonus(context, step, failures) && success;
    success = assertHeldItem(context, step, failures) && success;
    success = assertItemVisible(context, step, failures) && success;
    success = assertRuntimeWorldItemState(context, step, failures) && success;
    success = applyItemReceivedObservation(context, step, failures) && success;
    success = assertQuestItemLocationObservation(context, step, "world_item_spawned", failures) && success;
    success = assertQuestItemLocationObservation(context, step, "chest_contains_quest_item", failures) && success;
    success = assertQuestItemLocationObservation(context, step, "corpse_contains_quest_item", failures) && success;
    success = assertAwards(context, step, failures) && success;
    success = assertAwardCleared(context, step, failures) && success;
    success = assertMapObservation(context, step, failures) && success;
    success = assertVariableObservations(context, step, failures) && success;
    success = assertRuntimeEventVariable(context, step, failures) && success;
    success = assertActorVisible(context, step, failures) && success;
    success = assertActorCount(context, step, failures) && success;
    success = assertAiTrace(context, step, failures) && success;
    success = assertProjectiles(context, step, failures) && success;
    success = assertPartyHealth(context, step, failures) && success;
    success = assertBuff(context, step, failures) && success;
    success = assertCondition(context, step, failures) && success;
    success = assertHomingEnds(context, step, failures) && success;
    success = assertPartyGold(context, step, failures) && success;
    success = assertRecoveringMembers(context, step, failures) && success;
    success = assertSpritesHidden(context, step, failures) && success;
    success = assertPartyFood(context, step, failures) && success;
    success = assertWater(context, step, failures) && success;
    success = assertGameHour(context, step, failures) && success;
    success = assertJournalMapNote(context, step, failures) && success;
    success = assertAutonote(context, step, failures) && success;
    success = assertTeacherLedger(context, step, failures) && success;
    success = assertQuickItemRing(context, step, failures) && success;
    success = assertQuickItemPopup(context, step, failures) && success;
    success = assertDimensionDoor(context, step, failures) && success;
    success = assertLight(context, step, failures) && success;
    success = assertScriptedFog(context, step, failures) && success;
    success = assertCharges(context, step, failures) && success;
    success = assertCombatLog(context, step, failures) && success;
    success = assertTurnBased(context, step, failures) && success;
    success = assertMemberPoints(context, step, failures) && success;

    if (step.payload["mechanism"])
    {
        success = assertMechanismPayload(context, step, step.payload["mechanism"], failures) && success;
    }

    success = assertMapTransitionTrace(
        context,
        step,
        "map_transition_requested",
        &EventRuntimeState::lastMapTransitionRequested,
        failures) && success;
    success = assertMapTransitionTrace(
        context,
        step,
        "map_transition_confirmed",
        &EventRuntimeState::lastMapTransitionConfirmed,
        failures) && success;
    success = assertMapTransitionTrace(
        context,
        step,
        "map_transition_canceled",
        &EventRuntimeState::lastMapTransitionCanceled,
        failures) && success;
    success = assertChestOpened(context, step, failures) && success;
    success = assertChestView(context, step, failures) && success;
    success = assertPartyPosition(context, step, failures) && success;
    success = assertActorDialogStarted(context, step, failures) && success;
    success = assertPressurePlateTriggered(context, step, failures) && success;
    success = assertDialogueCanceled(context, step, failures) && success;
    success = assertDialogState(context, step, step.payload["dialog"], "assert", failures) && success;
    success = assertInputPromptState(context, step, step.payload["input_prompt"], "assert", failures) && success;
    success = applyRecordedNewGamePartyMember(context, step, failures) && success;
    success = applyRecordedNewGamePartySkill(context, step, failures) && success;
    success = assertQuestBits(context, step, "qbit_set", true, failures) && success;
    success = assertQuestBits(context, step, "qbit_clear", false, failures) && success;
    success = assertRuleset(context, step, failures) && success;
    return success;
}

// turn_based_turns: {count, max_seconds}: plays turn-based turns through the live input path, the party passing
// every action and ending every movement phase, until `count` turns reached their movement phase.
bool runTurnBasedTurns(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures) || !ensureRuntimeDriver(context, failures))
    {
        return false;
    }

    const int turns = step.payload["count"].as<int>(1);
    const float maxSeconds = step.payload["max_seconds"].as<float>(30.0f * float(std::max(1, turns)));
    int completed = 0;
    std::string failure;

    if (!context.runtimeDriver->playTurnBasedTurns(turns, maxSeconds, completed, failure))
    {
        failures.push_back(stepLocation(step) + ": " + failure);
        return false;
    }

    syncContextFromRuntime(context);
    return true;
}

bool runSetupShortcut(
    ScenarioExecutionContext &context,
    const ScenarioStep &step,
    std::vector<std::string> &failures)
{
    if (!payloadIsMap(step, failures))
    {
        return false;
    }

    std::string kind;

    if (!readScalarString(step, "kind", kind, failures, true))
    {
        return false;
    }

    if (kind == "grant_item")
    {
        if (!step.payload["item_id"] || !step.payload["item_id"].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": grant_item shortcut requires scalar field 'item_id'");
            return false;
        }

        return context.party.tryGrantItem(step.payload["item_id"].as<uint32_t>());
    }

    if (kind == "set_qbit")
    {
        if (!step.payload["id"] || !step.payload["id"].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": set_qbit shortcut requires scalar field 'id'");
            return false;
        }

        const bool value = !step.payload["value"] || step.payload["value"].as<bool>();
        context.party.setQuestBit(step.payload["id"].as<uint32_t>(), value);

        // A loaded map runs on the runtime driver's party: set it there too, so the next runtime step keeps it.
        if (context.runtimeDriver)
        {
            if (Party *pRuntimeParty = context.runtimeDriver->party())
            {
                pRuntimeParty->setQuestBit(step.payload["id"].as<uint32_t>(), value);
            }
        }

        return true;
    }

    if (kind == "immortal")
    {
        // The Immortal cheat for this run only (an immortal playthrough); settings.ini is not written.
        if (!ensureRuntimeDriver(context, failures))
        {
            return false;
        }

        std::string failure;

        if (!context.runtimeDriver->setPartyImmortal(step.payload["value"].as<bool>(true), failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return false;
        }

        syncContextFromRuntime(context);
        return true;
    }

    if (kind == "set_global_var")
    {
        if (!step.payload["name"] || !step.payload["name"].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": set_global_var shortcut requires scalar field 'name'");
            return false;
        }

        const std::string name = step.payload["name"].as<std::string>();
        const int32_t value = step.payload["value"].as<int32_t>(1);
        context.eventRuntimeState.namedGlobalVars[name] = value;

        // A loaded map runs on the runtime driver's event state: set it there too.
        if (context.runtimeDriver)
        {
            if (EventRuntimeState *pRuntimeState = context.runtimeDriver->eventRuntimeState())
            {
                pRuntimeState->namedGlobalVars[name] = value;
            }
        }

        return true;
    }

    // hire_follower: {id}: the NPC joins the party's followers, as hired from a dialogue.
    if (kind == "hire_follower")
    {
        if (!step.payload["id"] || !step.payload["id"].IsScalar() || !ensureRuntimeDriver(context, failures))
        {
            failures.push_back(stepLocation(step) + ": hire_follower shortcut requires scalar field 'id'");
            return false;
        }

        seedRuntimeDriverFromContext(context);
        Party *pParty = context.runtimeDriver->party();

        if (pParty == nullptr)
        {
            failures.push_back(stepLocation(step) + ": hire_follower shortcut needs a party");
            return false;
        }

        HiredNpcFollower follower;
        follower.npcId = step.payload["id"].as<uint32_t>();
        pParty->addHiredNpcFollower(follower);
        syncContextFromRuntime(context);
        return true;
    }

    // set_quick_item: {member_index, slot, item_id, strongest}: one of the member's potion radial slots (GAPS.md H.6).
    if (kind == "set_quick_item")
    {
        if (!ensureRuntimeDriver(context, failures))
        {
            return false;
        }

        seedRuntimeDriverFromContext(context);
        Party *pParty = context.runtimeDriver->party();
        Character *pMember = pParty != nullptr ? pParty->member(step.payload["member_index"].as<size_t>(0)) : nullptr;
        const size_t slot = step.payload["slot"].as<size_t>(0);

        if (pMember == nullptr || slot >= QuickItemSlotCount)
        {
            failures.push_back(stepLocation(step) + ": set_quick_item needs a member and a slot below "
                + std::to_string(QuickItemSlotCount));
            return false;
        }

        pMember->quickItemSlots[slot] = {step.payload["item_id"].as<uint32_t>(0),
            step.payload["strongest"].as<bool>(false) ? QuickItemBottleRule::Strongest : QuickItemBottleRule::Weakest};
        syncContextFromRuntime(context);
        return true;
    }

    // set_experience: {value, member_index}: the member's experience, or every member's without an index.
    if (kind == "set_experience")
    {
        if (!ensureRuntimeDriver(context, failures))
        {
            return false;
        }

        seedRuntimeDriverFromContext(context);
        Party *pParty = context.runtimeDriver->party();

        if (pParty == nullptr)
        {
            failures.push_back(stepLocation(step) + ": set_experience shortcut needs a party");
            return false;
        }

        const uint64_t value = step.payload["value"].as<uint64_t>(0);

        for (size_t memberIndex = 0; memberIndex < pParty->members().size(); ++memberIndex)
        {
            if (!step.payload["member_index"] || step.payload["member_index"].as<size_t>() == memberIndex)
            {
                pParty->setMemberExperience(memberIndex, value);
            }
        }

        syncContextFromRuntime(context);
        return true;
    }

    // set_condition: {member_index, condition, health}: gives the member a condition (unconscious, dead, ...), and
    // with `health` sets its hit points (an unconscious member at 0 stays down).
    if (kind == "set_condition")
    {
        if (!ensureRuntimeDriver(context, failures))
        {
            return false;
        }

        seedRuntimeDriverFromContext(context);
        Party *pParty = context.runtimeDriver->party();
        Character *pMember = pParty != nullptr ? pParty->member(step.payload["member_index"].as<size_t>(0)) : nullptr;
        const std::optional<CharacterCondition> condition =
            parseScenarioCondition(step.payload["condition"].as<std::string>(""));

        if (pMember == nullptr || !condition)
        {
            failures.push_back(stepLocation(step) + ": set_condition shortcut needs a member and a known condition");
            return false;
        }

        pMember->conditions.set(size_t(*condition));

        if (step.payload["health"])
        {
            pMember->health = step.payload["health"].as<int>();
        }

        syncContextFromRuntime(context);
        return true;
    }

    // set_member_points: {member_index, health, spell_points}: a member's current hit and spell points.
    if (kind == "set_member_points")
    {
        if (!ensureRuntimeDriver(context, failures))
        {
            return false;
        }

        seedRuntimeDriverFromContext(context);
        Party *pParty = context.runtimeDriver->party();
        Character *pMember = pParty != nullptr ? pParty->member(step.payload["member_index"].as<size_t>(0)) : nullptr;

        if (pMember == nullptr)
        {
            failures.push_back(stepLocation(step) + ": set_member_points shortcut needs an existing member");
            return false;
        }

        if (step.payload["health"])
        {
            pMember->health = step.payload["health"].as<int>();
        }

        if (step.payload["spell_points"])
        {
            pMember->spellPoints = step.payload["spell_points"].as<int>();
        }

        syncContextFromRuntime(context);
        return true;
    }

    if (kind == "map_transition_prompt")
    {
        if (!step.payload["source_id"] || !step.payload["source_id"].IsScalar())
        {
            failures.push_back(stepLocation(step) + ": map_transition_prompt shortcut requires scalar field 'source_id'");
            return false;
        }

        if (!ensureRuntimeDriver(context, failures))
        {
            return false;
        }

        seedRuntimeDriverFromContext(context);

        std::string failure;
        if (!context.runtimeDriver->openMapTransitionPrompt(step.payload["source_id"].as<uint32_t>(), failure))
        {
            failures.push_back(stepLocation(step) + ": " + failure);
            return false;
        }

        scenarioLog(
            context,
            ScenarioLogColor::Cyan,
            std::string("DIALOG after map_transition_prompt step=") + std::to_string(step.stepIndex)
                + " " + context.runtimeDriver->activeDialogSummary());
        syncContextFromRuntime(context);
        return true;
    }

    failures.push_back(stepLocation(step) + ": unknown setup_shortcut kind '" + kind
        + "' (known: grant_item, set_qbit, map_transition_prompt)");
    return false;
}
}

ScenarioRunResult ScenarioRunner::run(
    const std::filesystem::path &basePath,
    const Engine::ApplicationConfig &config,
    const ScenarioDocument &document,
    const ScenarioRunOptions &options)
{
    ScenarioRunResult result = {};

    if (options.dryRun)
    {
        std::cout << "Scenario dry run: " << document.id << " steps=" << document.steps.size() << '\n';

        for (const ScenarioStep &step : document.steps)
        {
            std::cout << "  " << step.stepIndex << ": " << step.kindName << '\n';
        }

        result.success = true;
        return result;
    }

    SDL_Environment *pEnvironment = SDL_GetEnvironment();

    if (pEnvironment == nullptr || !SDL_SetEnvironmentVariable(pEnvironment, "SDL_AUDIODRIVER", "dummy", true))
    {
        result.failures.push_back("could not force dummy audio driver for scenario runner");
        return result;
    }

    Engine::ApplicationConfig scenarioConfig = config;

    if (!document.world.empty())
    {
        scenarioConfig.activeWorldId = document.world;
    }

    ScenarioExecutionContext context = {};
    context.basePath = basePath;
    context.config = scenarioConfig;
    context.mode = document.mode;
    // One folder per run, removed at the end, so the same scenario can run in parallel builds without sharing saves;
    // OPENYAMM_SCENARIO_SAVE_DIR names a folder to keep instead (tools/run_game.py starts the game from its save).
    const char *pKeptSaveFolder = std::getenv("OPENYAMM_SCENARIO_SAVE_DIR");
    const bool keepSaves = pKeptSaveFolder != nullptr && *pKeptSaveFolder != '\0';
    std::ostringstream runFolder;
    runFolder << sanitizeScenarioFileStem(document.id) << '-' << std::hex << std::random_device{}();
    context.saveGameRootPath = keepSaves
        ? std::filesystem::path(pKeptSaveFolder)
        : std::filesystem::temp_directory_path() / "openyamm_scenario_saves" / runFolder.str();
    context.gameDataLoader.setActiveWorldId(scenarioConfig.activeWorldId);
    context.traceEnabled = options.trace && !envFlagEnabled("OPENYAMM_SCENARIO_QUIET");
    context.colorsEnabled = options.colors && !envFlagEnabled("NO_COLOR")
        && !envFlagEnabled("OPENYAMM_SCENARIO_NO_COLOR");
    context.totalStepCount = document.steps.size();

    // Scenarios play the game's own content: no mods and no language pack. Only the development mount is passed
    // on, so a map build can be played from its folder (--extra-mount).
    Engine::InstalledContentOptions scenarioContent;
    scenarioContent.extraMountRoot = scenarioConfig.installedContent.extraMountRoot;

    if (!context.assetFileSystem.initialize(
            basePath,
            scenarioConfig.assetRoot,
            scenarioConfig.assetScaleTier,
            scenarioConfig.assetScaleProfile,
            scenarioConfig.activeWorldId,
            scenarioContent))
    {
        result.failures.push_back("could not initialize asset file system");
        return result;
    }

    scenarioLog(context, ScenarioLogColor::Blue, "Scenario run: " + document.id);
    scenarioLog(context, ScenarioLogColor::Blue, "Development assets: " + scenarioConfig.assetRoot);
    scenarioLog(context, ScenarioLogColor::Blue, "Active world: " + scenarioConfig.activeWorldId);
    scenarioLog(context, ScenarioLogColor::Blue, "Mounted search paths:");

    const std::vector<std::string> searchPaths = context.assetFileSystem.getSearchPaths();

    for (const std::string &searchPath : searchPaths)
    {
        scenarioLog(context, ScenarioLogColor::Blue, "  " + searchPath);
    }

    for (const ScenarioStep &step : document.steps)
    {
        scenarioLog(context, ScenarioLogColor::Yellow, "RUN " + stepSummary(context, step));

        bool stepSuccess = false;
        const size_t failureCountBeforeStep = result.failures.size();

        if (!syncRecordedGameTimeBeforeStep(context, step, result.failures))
        {
            stepSuccess = false;
        }
        else switch (step.kind)
        {
        case ScenarioStepKind::NewGameFlow:
            stepSuccess = runNewGameFlow(context, step, result.failures);
            break;
        case ScenarioStepKind::LoadMap:
            stepSuccess = runLoadMap(context, step, result.failures);
            break;
        case ScenarioStepKind::Travel:
            stepSuccess = runTravel(context, step, result.failures);
            break;
        case ScenarioStepKind::SetPose:
            stepSuccess = runSetPose(context, step, result.failures);
            break;
        case ScenarioStepKind::PressAction:
            stepSuccess = runPressAction(context, step, result.failures);
            break;
        case ScenarioStepKind::PressInteract:
            stepSuccess = runPressInteract(context, step, result.failures);
            break;
        case ScenarioStepKind::SpeakNpc:
            stepSuccess = runSpeakNpc(context, step, result.failures);
            break;
        case ScenarioStepKind::MovementSegment:
            stepSuccess = runMovementSegment(context, step, result.failures);
            break;
        case ScenarioStepKind::Note:
        case ScenarioStepKind::Todo:
        case ScenarioStepKind::TraceObservation:
            stepSuccess = runNoOpObservation(step, result.failures);
            break;
        case ScenarioStepKind::InteractActor:
            stepSuccess = runInteractActor(context, step, result.failures);
            break;
        case ScenarioStepKind::EnterDoorAt:
            stepSuccess = runEnterDoorAt(context, step, result.failures);
            break;
        case ScenarioStepKind::CombatLoot:
            stepSuccess = runCombatLoot(context, step, result.failures);
            break;
        case ScenarioStepKind::GrantItem:
            stepSuccess = runGrantItem(context, step, result.failures);
            break;
        case ScenarioStepKind::RulesetBanks:
            stepSuccess = runRulesetBanks(context, step, result.failures);
            break;
        case ScenarioStepKind::WalkTo:
            stepSuccess = runWalkTo(context, step, result.failures);
            break;
        case ScenarioStepKind::PlayLua:
            stepSuccess = runPlayLua(context, step, result.failures);
            break;
        case ScenarioStepKind::Climb:
            stepSuccess = runClimb(context, step, result.failures);
            break;
        case ScenarioStepKind::PickUp:
            stepSuccess = runPickUp(context, step, result.failures);
            break;
        case ScenarioStepKind::Reload:
            stepSuccess = runReload(context, step, result.failures);
            break;
        case ScenarioStepKind::PartyDefeat:
            stepSuccess = runPartyDefeat(context, step, result.failures);
            break;
        case ScenarioStepKind::ClearHostiles:
            stepSuccess = runClearHostiles(context, step, result.failures);
            break;
        case ScenarioStepKind::ConsoleCommand:
            stepSuccess = runConsoleCommand(context, step, result.failures);
            break;
        case ScenarioStepKind::QuickLoad:
            stepSuccess = runQuickLoad(context, step, result.failures);
            break;
        case ScenarioStepKind::UseItem:
            stepSuccess = runUseItem(context, step, result.failures);
            break;
        case ScenarioStepKind::TurnBasedTurns:
            stepSuccess = runTurnBasedTurns(context, step, result.failures);
            break;
        case ScenarioStepKind::RightClickPortrait:
            stepSuccess = runRightClickPortrait(context, step, result.failures);
            break;
        case ScenarioStepKind::CastSpell:
            stepSuccess = runCastSpell(context, step, result.failures);
            break;
        case ScenarioStepKind::PartyCharge:
            stepSuccess = runPartyCharge(context, step, result.failures);
            break;
        case ScenarioStepKind::Craft:
            stepSuccess = runCraft(context, step, result.failures);
            break;
        case ScenarioStepKind::CombineGems:
            stepSuccess = runCombineGems(context, step, result.failures);
            break;
        case ScenarioStepKind::DamageActor:
            stepSuccess = runDamageActor(context, step, result.failures);
            break;
        case ScenarioStepKind::PartyAttack:
            stepSuccess = runPartyAttack(context, step, result.failures);
            break;
        case ScenarioStepKind::SetRuleset:
            stepSuccess = runSetRuleset(context, step, result.failures);
            break;
        case ScenarioStepKind::SpawnActor:
            stepSuccess = runSpawnActor(context, step, result.failures);
            break;
        case ScenarioStepKind::FireActorProjectile:
            stepSuccess = runFireActorProjectile(context, step, result.failures);
            break;
        case ScenarioStepKind::ExecuteEvent:
            stepSuccess = runExecuteEvent(context, step, result.failures);
            break;
        case ScenarioStepKind::LuaEvent:
            stepSuccess = runLuaEvent(context, step, result.failures);
            break;
        case ScenarioStepKind::BlinkActor:
            stepSuccess = runBlinkActor(context, step, result.failures);
            break;
        case ScenarioStepKind::ChargeActor:
            stepSuccess = runChargeActor(context, step, result.failures);
            break;
        case ScenarioStepKind::FrenzyActor:
            stepSuccess = runFrenzyActor(context, step, result.failures);
            break;
        case ScenarioStepKind::AiArena:
            stepSuccess = runAiArena(context, step, result.failures);
            break;
        case ScenarioStepKind::AiTraceDump:
            stepSuccess = runAiTraceDump(context, step, result.failures);
            break;
        case ScenarioStepKind::WaitUntil:
            stepSuccess = runWaitUntil(context, step, result.failures);
            break;
        case ScenarioStepKind::AssertMechanism:
            stepSuccess = runAssertMechanism(context, step, result.failures);
            break;
        case ScenarioStepKind::AdvanceRuntime:
            stepSuccess = runAdvanceRuntime(context, step, result.failures);
            break;
        case ScenarioStepKind::AdvanceGameTime:
            stepSuccess = runAdvanceGameTime(context, step, result.failures);
            break;
        case ScenarioStepKind::SelectTopic:
            stepSuccess = runSelectTopic(context, step, result.failures);
            break;
        case ScenarioStepKind::AnswerInput:
            stepSuccess = runAnswerInput(context, step, result.failures);
            break;
        case ScenarioStepKind::InteractTarget:
            stepSuccess = runInteractTarget(context, step, result.failures);
            break;
        case ScenarioStepKind::Assert:
            stepSuccess = runAssert(context, step, result.failures);
            break;
        case ScenarioStepKind::SetupShortcut:
            stepSuccess = runSetupShortcut(context, step, result.failures);
            break;
        case ScenarioStepKind::SaveCheckpoint:
            stepSuccess = runSaveCheckpoint(context, step, result.failures);
            break;
        case ScenarioStepKind::LoadCheckpoint:
            stepSuccess = runLoadCheckpoint(context, step, result.failures);
            break;
        case ScenarioStepKind::SaveGame:
            stepSuccess = runSaveGame(context, step, result.failures);
            break;
        case ScenarioStepKind::LoadGame:
            stepSuccess = runLoadGame(context, step, result.failures);
            break;
        }

        if (!stepSuccess)
        {
            if (result.failures.size() == failureCountBeforeStep)
            {
                result.failures.push_back(stepLocation(step) + ": step failed without a specific diagnostic");
            }

            scenarioLog(context, ScenarioLogColor::Red, "FAIL " + stepSummary(context, step));
            break;
        }

        scenarioLog(context, ScenarioLogColor::Green, "PASS step " + std::to_string(step.stepIndex));
    }

    if (!keepSaves)
    {
        std::error_code removeError;
        std::filesystem::remove_all(context.saveGameRootPath, removeError);
    }

    result.success = result.failures.empty();
    return result;
}
}
