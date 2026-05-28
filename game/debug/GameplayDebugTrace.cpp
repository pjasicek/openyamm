#include "game/debug/GameplayDebugTrace.h"

#include "game/events/EvtEnums.h"
#include "game/mm9/Mm9DialogueRuntime.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <atomic>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
thread_local int g_traceSuppressionDepth = 0;

bool environmentFlagEnabled(const char *pName)
{
    const char *pValue = std::getenv(pName);

    if (pValue == nullptr || *pValue == '\0')
    {
        return false;
    }

    const std::string value(pValue);
    return value != "0" && value != "false" && value != "FALSE" && value != "off" && value != "OFF";
}

void appendPoint(std::ostream &out, const bx::Vec3 &point)
{
    out << " hit=(" << point.x << "," << point.y << "," << point.z << ")";
}

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

bool containsInsensitive(const std::string &haystack, const std::string &needle)
{
    return lowerAscii(haystack).find(lowerAscii(needle)) != std::string::npos;
}

std::string environmentString(const char *pName)
{
    const char *pValue = std::getenv(pName);
    return pValue != nullptr ? std::string(pValue) : std::string();
}

std::ofstream *gameplayTraceFileStream()
{
    static std::unique_ptr<std::ofstream> pOutput = []() -> std::unique_ptr<std::ofstream>
    {
        const std::string filePath = environmentString("OPENYAMM_GAMEPLAY_TRACE_FILE");

        if (filePath.empty())
        {
            return nullptr;
        }

        const bool append = environmentFlagEnabled("OPENYAMM_GAMEPLAY_TRACE_APPEND");
        const std::ios::openmode mode = std::ios::out | (append ? std::ios::app : std::ios::trunc);
        std::unique_ptr<std::ofstream> pStream = std::make_unique<std::ofstream>(filePath, mode);

        if (!*pStream)
        {
            std::cerr << "GameplayTrace: failed to open trace file \"" << filePath << "\"\n";
            return nullptr;
        }

        return pStream;
    }();
    return pOutput.get();
}

std::mutex &gameplayTraceOutputMutex()
{
    static std::mutex mutex;
    return mutex;
}

struct GameplayTraceState
{
    std::atomic_bool enabled = false;
    bool append = true;
    std::string filePath;
    std::unique_ptr<std::ofstream> pOutput;
};

GameplayTraceState &gameplayTraceState()
{
    static GameplayTraceState state;
    return state;
}

struct CombatTraceState
{
    bool enabled = false;
    bool append = true;
    std::string filePath;
    std::unique_ptr<std::ofstream> pOutput;
};

CombatTraceState &combatTraceState()
{
    static CombatTraceState state;
    return state;
}

std::mutex &combatTraceOutputMutex()
{
    static std::mutex mutex;
    return mutex;
}
}

bool gameplayDebugTraceEnabled()
{
    static const bool enabled =
        environmentFlagEnabled("OPENYAMM_GAMEPLAY_TRACE")
        || environmentFlagEnabled("OPENYAMM_ROUTE_TRACE")
        || !environmentString("OPENYAMM_GAMEPLAY_TRACE_FILE").empty();
    return enabled || gameplayTraceState().enabled.load();
}

bool gameplayDebugTraceSuppressed()
{
    return g_traceSuppressionDepth > 0;
}

void gameplayDebugTraceWrite(const std::string &message)
{
    const std::string line = "[GameplayTrace] " + message;
    std::lock_guard<std::mutex> lock(gameplayTraceOutputMutex());
    std::cout << line << '\n';

    GameplayTraceState &state = gameplayTraceState();
    if (state.enabled.load() && state.pOutput != nullptr)
    {
        *state.pOutput << line << '\n';
        state.pOutput->flush();
    }

    if (std::ofstream *pOutput = gameplayTraceFileStream())
    {
        *pOutput << line << '\n';
        pOutput->flush();
    }
}

void configureGameplayDebugTrace(bool enabled, const std::string &filePath, bool append)
{
    std::lock_guard<std::mutex> lock(gameplayTraceOutputMutex());
    GameplayTraceState &state = gameplayTraceState();
    state.enabled.store(false);
    state.append = append;
    state.filePath = filePath;
    state.pOutput.reset();

    if (!enabled || state.filePath.empty())
    {
        return;
    }

    const std::filesystem::path path(state.filePath);
    const std::filesystem::path parentPath = path.parent_path();

    if (!parentPath.empty())
    {
        std::error_code errorCode;
        std::filesystem::create_directories(parentPath, errorCode);

        if (errorCode)
        {
            std::cerr << "GameplayTrace: failed to create directory \"" << parentPath.string()
                << "\": " << errorCode.message() << '\n';
            return;
        }
    }

    const std::ios::openmode mode = std::ios::out | (state.append ? std::ios::app : std::ios::trunc);
    state.pOutput = std::make_unique<std::ofstream>(state.filePath, mode);

    if (!*state.pOutput)
    {
        std::cerr << "GameplayTrace: failed to open trace file \"" << state.filePath << "\"\n";
        state.pOutput.reset();
        return;
    }

    state.enabled.store(true);
}

void configureGameplayCombatTrace(bool enabled, const std::string &filePath, bool append)
{
    std::lock_guard<std::mutex> lock(combatTraceOutputMutex());
    CombatTraceState &state = combatTraceState();
    state.enabled = enabled;
    state.append = append;
    state.filePath = filePath;
    state.pOutput.reset();

    if (!state.enabled || state.filePath.empty())
    {
        state.enabled = false;
        return;
    }

    const std::filesystem::path path(state.filePath);
    const std::filesystem::path parentPath = path.parent_path();

    if (!parentPath.empty())
    {
        std::error_code errorCode;
        std::filesystem::create_directories(parentPath, errorCode);

        if (errorCode)
        {
            std::cerr << "CombatTrace: failed to create directory \"" << parentPath.string()
                << "\": " << errorCode.message() << '\n';
            state.enabled = false;
            return;
        }
    }

    const std::ios::openmode mode = std::ios::out | (state.append ? std::ios::app : std::ios::trunc);
    state.pOutput = std::make_unique<std::ofstream>(state.filePath, mode);

    if (!*state.pOutput)
    {
        std::cerr << "CombatTrace: failed to open trace file \"" << state.filePath << "\"\n";
        state.pOutput.reset();
        state.enabled = false;
    }
}

bool gameplayCombatTraceEnabled()
{
    return combatTraceState().enabled;
}

void gameplayCombatTraceWrite(const std::string &message)
{
    std::lock_guard<std::mutex> lock(combatTraceOutputMutex());
    CombatTraceState &state = combatTraceState();

    if (!state.enabled || state.pOutput == nullptr)
    {
        return;
    }

    *state.pOutput << "[CombatTrace] " << message << '\n';
    state.pOutput->flush();
}

std::string gameplayDebugTraceWorldHitSummary(const GameplayWorldHit &hit)
{
    std::ostringstream out;
    out << "has_hit=" << (hit.hasHit ? "true" : "false");

    switch (hit.kind)
    {
        case GameplayWorldHitKind::None:
            out << " kind=none";
            break;
        case GameplayWorldHitKind::Actor:
            out << " kind=actor";
            if (hit.actor)
            {
                out << " actor_index=" << hit.actor->actorIndex
                    << " name=\"" << hit.actor->displayName << "\""
                    << " npc_id=" << hit.actor->npcId
                    << " group=" << hit.actor->actorGroup
                    << " friendly=" << (hit.actor->isFriendly ? "true" : "false")
                    << " distance=" << hit.actor->distance;
                appendPoint(out, hit.actor->hitPoint);
            }
            break;
        case GameplayWorldHitKind::WorldItem:
            out << " kind=world_item";
            if (hit.worldItem)
            {
                out << " world_item_index=" << hit.worldItem->worldItemIndex
                    << " item_id=" << hit.worldItem->objectDescriptionId
                    << " sprite_id=" << hit.worldItem->objectSpriteId
                    << " distance=" << hit.worldItem->distance;
                appendPoint(out, hit.worldItem->hitPoint);
            }
            break;
        case GameplayWorldHitKind::Chest:
        case GameplayWorldHitKind::Corpse:
            out << (hit.kind == GameplayWorldHitKind::Chest ? " kind=chest" : " kind=corpse");
            if (hit.container)
            {
                out << " source_index=" << hit.container->sourceIndex
                    << " distance=" << hit.container->distance;
            }
            break;
        case GameplayWorldHitKind::EventTarget:
            out << " kind=event_target";
            if (hit.eventTarget)
            {
                out << " target_kind=" << static_cast<uint32_t>(hit.eventTarget->targetKind)
                    << " target_index=" << hit.eventTarget->targetIndex
                    << " face_index=" << hit.eventTarget->secondaryIndex
                    << " event_primary=" << hit.eventTarget->eventIdPrimary
                    << " event_secondary=" << hit.eventTarget->eventIdSecondary
                    << " triggered_event=" << hit.eventTarget->triggeredEventId
                    << " trigger=" << hit.eventTarget->trigger
                    << " var_primary=" << hit.eventTarget->variablePrimary
                    << " var_secondary=" << hit.eventTarget->variableSecondary
                    << " special_trigger=" << hit.eventTarget->specialTrigger
                    << " attributes=" << hit.eventTarget->attributes
                    << " name=\"" << hit.eventTarget->name << "\""
                    << " distance=" << hit.eventTarget->distance;
                appendPoint(out, hit.eventTarget->hitPoint);
            }
            break;
        case GameplayWorldHitKind::Object:
            out << " kind=object";
            if (hit.object)
            {
                out << " object_index=" << hit.object->objectIndex
                    << " item_id=" << hit.object->objectDescriptionId
                    << " sprite_id=" << hit.object->objectSpriteId
                    << " spell_id=" << hit.object->spellId
                    << " distance=" << hit.object->distance;
                appendPoint(out, hit.object->hitPoint);
            }
            break;
        case GameplayWorldHitKind::Ground:
            out << " kind=ground";
            if (hit.ground)
            {
                out << " valid=" << (hit.ground->isValid ? "true" : "false")
                    << " distance=" << hit.ground->distance;
                appendPoint(out, hit.ground->worldPoint);
            }
            break;
    }

    return out.str();
}

bool gameplayDebugTraceItemLooksQuestRelevant(uint32_t itemId, const ItemTable *pItemTable)
{
    const ItemDefinition *pItem = pItemTable != nullptr ? pItemTable->get(itemId) : nullptr;

    if (pItem == nullptr)
    {
        return false;
    }

    return containsInsensitive(pItem->notes, "quest item")
        || containsInsensitive(pItem->iconName, "_quest")
        || containsInsensitive(pItem->iconVirtualPath, "_quest")
        || pItem->rarity == ItemRarity::Special
        || pItem->equipStat == "Mscroll"
        || containsInsensitive(pItem->name, " key")
        || containsInsensitive(pItem->name, "key")
        || containsInsensitive(pItem->name, "letter")
        || containsInsensitive(pItem->name, "plans")
        || containsInsensitive(pItem->name, "orders")
        || containsInsensitive(pItem->name, "missive")
        || containsInsensitive(pItem->name, "papers");
}

std::string gameplayDebugTraceItemSummary(uint32_t itemId, const ItemTable *pItemTable)
{
    std::ostringstream out;

    const ItemDefinition *pItem = pItemTable != nullptr ? pItemTable->get(itemId) : nullptr;

    if (pItem != nullptr)
    {
        out << " item_name=\"" << pItem->name << "\""
            << " item_icon=\"" << pItem->iconName << "\""
            << " item_material=" << pItem->material
            << " item_rarity=" << static_cast<uint32_t>(pItem->rarity)
            << " quest_like=" << (gameplayDebugTraceItemLooksQuestRelevant(itemId, pItemTable) ? "true" : "false");
    }
    else
    {
        out << " quest_like=false";
    }

    return out.str();
}

std::string gameplayDebugTraceMm9KeyQbitSummary(uint32_t qbitId)
{
    if (!mm9QbitIdIsKeyMapping(qbitId))
    {
        return {};
    }

    const int32_t rawKeyId = mm9RawKeyIdForQbit(qbitId);
    return "raw_id=" + std::to_string(rawKeyId)
        + " qbit_id=" + std::to_string(qbitId)
        + " state_id=\"mm9.keys." + std::to_string(rawKeyId) + "\"";
}

const char *gameplayDebugTraceMechanismStateName(uint16_t state)
{
    if (state == static_cast<uint16_t>(EvtMechanismState::Open))
    {
        return "open";
    }

    if (state == static_cast<uint16_t>(EvtMechanismState::Closed))
    {
        return "closed";
    }

    if (state == static_cast<uint16_t>(EvtMechanismState::Opening))
    {
        return "opening";
    }

    if (state == static_cast<uint16_t>(EvtMechanismState::Closing))
    {
        return "closing";
    }

    return "unknown";
}

const char *gameplayDebugTraceMechanismActionName(uint32_t action)
{
    if (action == static_cast<uint32_t>(EvtMechanismAction::Open))
    {
        return "open";
    }

    if (action == static_cast<uint32_t>(EvtMechanismAction::Close))
    {
        return "close";
    }

    if (action == static_cast<uint32_t>(EvtMechanismAction::Trigger))
    {
        return "trigger";
    }

    return "unknown";
}

ScopedGameplayDebugTraceSuppression::ScopedGameplayDebugTraceSuppression()
{
    ++g_traceSuppressionDepth;
}

ScopedGameplayDebugTraceSuppression::~ScopedGameplayDebugTraceSuppression()
{
    if (g_traceSuppressionDepth > 0)
    {
        --g_traceSuppressionDepth;
    }
}
}
