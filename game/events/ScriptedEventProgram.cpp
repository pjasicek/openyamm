#include "game/events/ScriptedEventProgram.h"

#include "engine/scripting/LuaStateOwner.h"

#include <algorithm>
#include <atomic>

extern "C"
{
#include <lauxlib.h>
}

namespace OpenYAMM::Game
{
namespace
{
constexpr char LuaScopeMap[] = "map";
constexpr char LuaScopeGlobal[] = "global";
constexpr char LuaScopeCanShowTopic[] = "CanShowTopic";

std::atomic<uint64_t> NextScriptedEventProgramCacheId{1};

const char *luaScopeName(ScriptedEventScope scope)
{
    return scope == ScriptedEventScope::Global ? LuaScopeGlobal : LuaScopeMap;
}

void registerMetadataBindings(lua_State *pLuaState)
{
    lua_newtable(pLuaState);

    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeGlobal);

    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeMap);

    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeCanShowTopic);

    lua_newtable(pLuaState);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeGlobal);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeMap);
    lua_setfield(pLuaState, -2, "meta");

    lua_setglobal(pLuaState, "evt");
}

bool pushEvtSubtable(lua_State *pLuaState, const char *pFieldName)
{
    lua_getglobal(pLuaState, "evt");

    if (!lua_istable(pLuaState, -1))
    {
        lua_pop(pLuaState, 1);
        return false;
    }

    lua_getfield(pLuaState, -1, pFieldName);

    if (!lua_istable(pLuaState, -1))
    {
        lua_pop(pLuaState, 2);
        return false;
    }

    return true;
}

bool pushEvtMetaScope(lua_State *pLuaState, ScriptedEventScope scope)
{
    lua_getglobal(pLuaState, "evt");

    if (!lua_istable(pLuaState, -1))
    {
        lua_pop(pLuaState, 1);
        return false;
    }

    lua_getfield(pLuaState, -1, "meta");

    if (!lua_istable(pLuaState, -1))
    {
        lua_pop(pLuaState, 2);
        return false;
    }

    lua_getfield(pLuaState, -1, luaScopeName(scope));

    if (!lua_istable(pLuaState, -1))
    {
        lua_pop(pLuaState, 3);
        return false;
    }

    return true;
}

template <typename TValue>
void sortAndUnique(std::vector<TValue> &values)
{
    std::sort(values.begin(), values.end());
    values.erase(std::unique(values.begin(), values.end()), values.end());
}

std::vector<uint16_t> readHandlerIds(lua_State *pLuaState, const char *pTableName)
{
    std::vector<uint16_t> eventIds;

    if (!pushEvtSubtable(pLuaState, pTableName))
    {
        return eventIds;
    }

    lua_pushnil(pLuaState);

    while (lua_next(pLuaState, -2) != 0)
    {
        if (lua_isinteger(pLuaState, -2) && lua_isfunction(pLuaState, -1))
        {
            eventIds.push_back(static_cast<uint16_t>(lua_tointeger(pLuaState, -2)));
        }

        lua_pop(pLuaState, 1);
    }

    lua_pop(pLuaState, 2);
    sortAndUnique(eventIds);
    return eventIds;
}

template <typename TValue>
std::vector<TValue> readIntegerArrayFromField(
    lua_State *pLuaState,
    int tableIndex,
    const char *pFieldName,
    bool preserveOrder = false)
{
    std::vector<TValue> values;
    lua_getfield(pLuaState, tableIndex, pFieldName);

    if (lua_istable(pLuaState, -1))
    {
        const size_t entryCount = lua_rawlen(pLuaState, -1);
        values.reserve(entryCount);

        for (size_t index = 1; index <= entryCount; ++index)
        {
            lua_geti(pLuaState, -1, static_cast<lua_Integer>(index));

            if (lua_isinteger(pLuaState, -1))
            {
                values.push_back(static_cast<TValue>(lua_tointeger(pLuaState, -1)));
            }

            lua_pop(pLuaState, 1);
        }
    }

    lua_pop(pLuaState, 1);
    if (!preserveOrder)
    {
        sortAndUnique(values);
    }
    return values;
}

std::vector<std::string> readStringArrayFromField(lua_State *pLuaState, int tableIndex, const char *pFieldName)
{
    std::vector<std::string> values;
    lua_getfield(pLuaState, tableIndex, pFieldName);

    if (lua_istable(pLuaState, -1))
    {
        const size_t entryCount = lua_rawlen(pLuaState, -1);
        values.reserve(entryCount);

        for (size_t index = 1; index <= entryCount; ++index)
        {
            lua_geti(pLuaState, -1, static_cast<lua_Integer>(index));

            if (lua_isstring(pLuaState, -1))
            {
                values.emplace_back(lua_tostring(pLuaState, -1));
            }

            lua_pop(pLuaState, 1);
        }
    }

    lua_pop(pLuaState, 1);
    sortAndUnique(values);
    return values;
}

std::unordered_map<uint16_t, std::string> readStringMapFromField(lua_State *pLuaState, int tableIndex, const char *pFieldName)
{
    std::unordered_map<uint16_t, std::string> values;
    lua_getfield(pLuaState, tableIndex, pFieldName);

    if (lua_istable(pLuaState, -1))
    {
        lua_pushnil(pLuaState);

        while (lua_next(pLuaState, -2) != 0)
        {
            if (lua_isinteger(pLuaState, -2) && lua_isstring(pLuaState, -1))
            {
                values.emplace(
                    static_cast<uint16_t>(lua_tointeger(pLuaState, -2)),
                    std::string(lua_tostring(pLuaState, -1)));
            }

            lua_pop(pLuaState, 1);
        }
    }

    lua_pop(pLuaState, 1);
    return values;
}

std::unordered_map<uint16_t, std::vector<uint32_t>> readOpenedChestIds(lua_State *pLuaState, int tableIndex)
{
    std::unordered_map<uint16_t, std::vector<uint32_t>> values;
    lua_getfield(pLuaState, tableIndex, "openedChestIds");

    if (lua_istable(pLuaState, -1))
    {
        lua_pushnil(pLuaState);

        while (lua_next(pLuaState, -2) != 0)
        {
            if (lua_isinteger(pLuaState, -2) && lua_istable(pLuaState, -1))
            {
                const uint16_t eventId = static_cast<uint16_t>(lua_tointeger(pLuaState, -2));
                std::vector<uint32_t> chestIds;
                const size_t chestCount = lua_rawlen(pLuaState, -1);
                chestIds.reserve(chestCount);

                for (size_t index = 1; index <= chestCount; ++index)
                {
                    lua_geti(pLuaState, -1, static_cast<lua_Integer>(index));

                    if (lua_isinteger(pLuaState, -1))
                    {
                        chestIds.push_back(static_cast<uint32_t>(lua_tointeger(pLuaState, -1)));
                    }

                    lua_pop(pLuaState, 1);
                }

                sortAndUnique(chestIds);
                values.emplace(eventId, std::move(chestIds));
            }

            lua_pop(pLuaState, 1);
        }
    }

    lua_pop(pLuaState, 1);
    return values;
}

std::optional<std::string> readOptionalStringField(lua_State *pLuaState, int tableIndex, const char *pFieldName)
{
    const int absoluteTableIndex = lua_absindex(pLuaState, tableIndex);
    lua_getfield(pLuaState, absoluteTableIndex, pFieldName);

    std::optional<std::string> value;

    if (lua_isstring(pLuaState, -1))
    {
        value = std::string(lua_tostring(pLuaState, -1));
    }

    lua_pop(pLuaState, 1);
    return value;
}

std::optional<uint32_t> readOptionalUnsignedField(lua_State *pLuaState, int tableIndex, const char *pFieldName)
{
    const int absoluteTableIndex = lua_absindex(pLuaState, tableIndex);
    lua_getfield(pLuaState, absoluteTableIndex, pFieldName);

    std::optional<uint32_t> value;

    if (lua_isinteger(pLuaState, -1))
    {
        const lua_Integer rawValue = lua_tointeger(pLuaState, -1);

        if (rawValue >= 0)
        {
            value = static_cast<uint32_t>(rawValue);
        }
    }

    lua_pop(pLuaState, 1);
    return value;
}

std::optional<double> readOptionalNumberField(lua_State *pLuaState, int tableIndex, const char *pFieldName)
{
    const int absoluteTableIndex = lua_absindex(pLuaState, tableIndex);
    lua_getfield(pLuaState, absoluteTableIndex, pFieldName);

    std::optional<double> value;

    if (lua_isnumber(pLuaState, -1))
    {
        value = static_cast<double>(lua_tonumber(pLuaState, -1));
    }

    lua_pop(pLuaState, 1);
    return value;
}

bool readBooleanField(lua_State *pLuaState, int tableIndex, const char *pFieldName)
{
    const int absoluteTableIndex = lua_absindex(pLuaState, tableIndex);
    lua_getfield(pLuaState, absoluteTableIndex, pFieldName);
    const bool value = lua_toboolean(pLuaState, -1) != 0;
    lua_pop(pLuaState, 1);
    return value;
}

std::optional<ScriptedEventProgram::ContextActionMetadata> readContextActionMetadata(
    lua_State *pLuaState,
    int tableIndex)
{
    if (!lua_istable(pLuaState, tableIndex))
    {
        return std::nullopt;
    }

    ScriptedEventProgram::ContextActionMetadata metadata = {};
    const int absoluteTableIndex = lua_absindex(pLuaState, tableIndex);

    metadata.kind = readOptionalStringField(pLuaState, absoluteTableIndex, "kind").value_or("");
    metadata.source = readOptionalStringField(pLuaState, absoluteTableIndex, "source").value_or("");
    metadata.houseId = readOptionalUnsignedField(pLuaState, absoluteTableIndex, "houseId");
    metadata.targetMap = readOptionalStringField(pLuaState, absoluteTableIndex, "targetMap");
    metadata.targetName = readOptionalStringField(pLuaState, absoluteTableIndex, "targetName");
    metadata.chestIds = readIntegerArrayFromField<uint32_t>(pLuaState, absoluteTableIndex, "chestIds");

    lua_getfield(pLuaState, absoluteTableIndex, "hidden");
    metadata.hidden = lua_toboolean(pLuaState, -1) != 0;
    lua_pop(pLuaState, 1);

    if (metadata.kind.empty())
    {
        return std::nullopt;
    }

    return metadata;
}

std::unordered_map<uint16_t, ScriptedEventProgram::ContextActionMetadata> readContextActionMetadataByEventId(
    lua_State *pLuaState,
    int tableIndex)
{
    std::unordered_map<uint16_t, ScriptedEventProgram::ContextActionMetadata> values;
    lua_getfield(pLuaState, tableIndex, "contextActions");

    if (lua_istable(pLuaState, -1))
    {
        lua_pushnil(pLuaState);

        while (lua_next(pLuaState, -2) != 0)
        {
            if (lua_isinteger(pLuaState, -2) && lua_istable(pLuaState, -1))
            {
                const std::optional<ScriptedEventProgram::ContextActionMetadata> metadata =
                    readContextActionMetadata(pLuaState, -1);

                if (metadata)
                {
                    values.emplace(static_cast<uint16_t>(lua_tointeger(pLuaState, -2)), *metadata);
                }
            }

            lua_pop(pLuaState, 1);
        }
    }

    lua_pop(pLuaState, 1);
    return values;
}

ScriptedEventTimerScheduleKind timerScheduleKindFromString(const std::string &value)
{
    if (value == "interval")
    {
        return ScriptedEventTimerScheduleKind::Interval;
    }

    if (value == "daily")
    {
        return ScriptedEventTimerScheduleKind::Daily;
    }

    if (value == "weekly")
    {
        return ScriptedEventTimerScheduleKind::Weekly;
    }

    if (value == "monthly")
    {
        return ScriptedEventTimerScheduleKind::Monthly;
    }

    if (value == "yearly")
    {
        return ScriptedEventTimerScheduleKind::Yearly;
    }

    return ScriptedEventTimerScheduleKind::Relative;
}

std::vector<ScriptedEventProgram::TimerTrigger> readTimerTriggers(
    lua_State *pLuaState,
    int tableIndex,
    ScriptedEventScope scope)
{
    std::vector<ScriptedEventProgram::TimerTrigger> timers;
    std::unordered_map<uint16_t, uint32_t> nativeRegistrationCounts;
    lua_getfield(pLuaState, tableIndex, "timers");

    if (lua_istable(pLuaState, -1))
    {
        const size_t timerCount = lua_rawlen(pLuaState, -1);
        timers.reserve(timerCount);

        for (size_t index = 1; index <= timerCount; ++index)
        {
            lua_geti(pLuaState, -1, static_cast<lua_Integer>(index));

            if (lua_istable(pLuaState, -1))
            {
                ScriptedEventProgram::TimerTrigger timer = {};
                const int timerTableIndex = lua_absindex(pLuaState, -1);
                timer.scope = scope;

                if (const std::optional<uint32_t> eventId =
                        readOptionalUnsignedField(pLuaState, timerTableIndex, "eventId"))
                {
                    timer.eventId = static_cast<uint16_t>(*eventId);
                }

                if (const std::optional<uint32_t> sourceEventId =
                        readOptionalUnsignedField(pLuaState, timerTableIndex, "sourceEventId"))
                {
                    timer.sourceEventId = static_cast<uint16_t>(*sourceEventId);
                }
                else
                {
                    timer.sourceEventId = timer.eventId;
                }

                const std::string origin =
                    readOptionalStringField(pLuaState, timerTableIndex, "origin").value_or("native");
                timer.origin = origin == "legacy"
                    ? ScriptedEventTimerOrigin::Legacy
                    : ScriptedEventTimerOrigin::Native;

                const std::string scheduleKind =
                    readOptionalStringField(pLuaState, timerTableIndex, "scheduleKind").value_or("relative");
                timer.scheduleKind = timerScheduleKindFromString(scheduleKind);

                if (timer.origin == ScriptedEventTimerOrigin::Legacy)
                {
                    if (timer.scheduleKind == ScriptedEventTimerScheduleKind::Relative)
                    {
                        timer.scheduleKind = ScriptedEventTimerScheduleKind::Daily;
                    }

                    const std::string triggerKind =
                        readOptionalStringField(pLuaState, timerTableIndex, "triggerKind").value_or("timer");
                    timer.triggerKind = triggerKind == "long"
                        ? ScriptedEventTimerTriggerKind::LongTimer
                        : ScriptedEventTimerTriggerKind::Timer;
                    timer.repeating = true;

                    if (const std::optional<uint32_t> triggerStep =
                            readOptionalUnsignedField(pLuaState, timerTableIndex, "triggerStep"))
                    {
                        timer.triggerStep = static_cast<uint8_t>(*triggerStep);
                    }

                    if (const std::optional<uint32_t> intervalHalfMinutes =
                            readOptionalUnsignedField(pLuaState, timerTableIndex, "intervalHalfMinutes"))
                    {
                        timer.intervalHalfMinutes = static_cast<uint16_t>(*intervalHalfMinutes);
                    }

                    timer.startHour = static_cast<int>(
                        readOptionalUnsignedField(pLuaState, timerTableIndex, "startHour").value_or(0));
                    timer.startMinute = static_cast<int>(
                        readOptionalUnsignedField(pLuaState, timerTableIndex, "startMinute").value_or(0));
                    timer.startSecond = static_cast<int>(
                        readOptionalUnsignedField(pLuaState, timerTableIndex, "startSecond").value_or(0));
                }
                else
                {
                    timer.registrationIndex = ++nativeRegistrationCounts[timer.sourceEventId];
                    timer.repeating = readBooleanField(pLuaState, timerTableIndex, "repeating");
                    timer.intervalGameMinutes =
                        readOptionalNumberField(pLuaState, timerTableIndex, "intervalGameMinutes").value_or(0.0);
                    timer.initialDelayGameMinutes =
                        readOptionalNumberField(pLuaState, timerTableIndex, "initialDelayGameMinutes")
                            .value_or(
                                readOptionalNumberField(
                                    pLuaState,
                                    timerTableIndex,
                                    "remainingGameMinutes").value_or(timer.intervalGameMinutes));
                }

                if (timer.eventId != 0)
                {
                    timers.push_back(std::move(timer));
                }
            }

            lua_pop(pLuaState, 1);
        }
    }

    lua_pop(pLuaState, 1);
    return timers;
}

}

bool ScriptedEventProgram::populateMetadataFromLua(
    lua_State *pLuaState,
    ScriptedEventScope scope,
    ScriptedEventProgram &program,
    std::string &error)
{
    program.m_eventIds = readHandlerIds(pLuaState, luaScopeName(scope));

    if (scope == ScriptedEventScope::Global)
    {
        program.m_canShowTopicEventIds = readHandlerIds(pLuaState, LuaScopeCanShowTopic);
    }

    if (!pushEvtMetaScope(pLuaState, scope))
    {
        error = "missing evt.meta." + std::string(luaScopeName(scope));
        return false;
    }

    program.m_onLoadEventIds = readIntegerArrayFromField<uint16_t>(pLuaState, -1, "onLoad", true);
    program.m_onLeaveEventIds = readIntegerArrayFromField<uint16_t>(pLuaState, -1, "onLeave", true);
    program.m_monsterKilledHookEventIds =
        readIntegerArrayFromField<uint16_t>(pLuaState, -1, "monsterKilledHooks", true);
    program.m_monsterDamageHookEventIds =
        readIntegerArrayFromField<uint16_t>(pLuaState, -1, "monsterDamageHooks", true);
    program.m_hints = readStringMapFromField(pLuaState, -1, "hint");
    program.m_summaries = readStringMapFromField(pLuaState, -1, "title");

    if (program.m_summaries.empty())
    {
        program.m_summaries = readStringMapFromField(pLuaState, -1, "summary");
    }

    program.m_openedChestIdsByEventId = readOpenedChestIds(pLuaState, -1);
    program.m_contextActionsByEventId = readContextActionMetadataByEventId(pLuaState, -1);
    program.m_textureNames = readStringArrayFromField(pLuaState, -1, "textureNames");
    program.m_spriteNames = readStringArrayFromField(pLuaState, -1, "spriteNames");
    program.m_castSpellIds = readIntegerArrayFromField<uint32_t>(pLuaState, -1, "castSpellIds");
    program.m_levitateTrapFaceMask = readOptionalUnsignedField(pLuaState, -1, "levitateTrapFaceMask").value_or(0);
    program.m_levitateTrapEvents = readIntegerArrayFromField<uint16_t>(pLuaState, -1, "levitateTrapEvents", true);
    program.m_timerTriggers = readTimerTriggers(pLuaState, -1, scope);
    lua_pop(pLuaState, 3);
    return true;
}

std::optional<ScriptedEventProgram> ScriptedEventProgram::loadFromLuaText(
    const std::string &luaSourceText,
    const std::string &luaSourceName,
    ScriptedEventScope scope,
    std::string &error)
{
    error.clear();
    Engine::LuaStateOwner lua = {};

    if (!lua.isValid())
    {
        error = "lua state unavailable";
        return std::nullopt;
    }

    lua.openApprovedLibraries();
    registerMetadataBindings(lua.state());

    std::optional<std::string> runtimeError;

    if (!lua.runChunk(luaSourceText, luaSourceName, runtimeError))
    {
        error = runtimeError.value_or("failed to execute lua chunk");
        return std::nullopt;
    }

    ScriptedEventProgram program = {};
    program.m_luaSourceText = luaSourceText;
    program.m_luaSourceName = luaSourceName;
    program.m_cacheId = NextScriptedEventProgramCacheId.fetch_add(1, std::memory_order_relaxed);
    program.m_scope = scope;

    if (!populateMetadataFromLua(lua.state(), scope, program, error))
    {
        return std::nullopt;
    }

    return program;
}

const std::optional<std::string> &ScriptedEventProgram::luaSourceText() const
{
    return m_luaSourceText;
}

const std::optional<std::string> &ScriptedEventProgram::luaSourceName() const
{
    return m_luaSourceName;
}

uint64_t ScriptedEventProgram::cacheId() const
{
    return m_cacheId;
}

ScriptedEventScope ScriptedEventProgram::scope() const
{
    return m_scope;
}

const std::vector<uint16_t> &ScriptedEventProgram::eventIds() const
{
    return m_eventIds;
}

const std::vector<uint16_t> &ScriptedEventProgram::canShowTopicEventIds() const
{
    return m_canShowTopicEventIds;
}

const std::vector<uint16_t> &ScriptedEventProgram::onLoadEventIds() const
{
    return m_onLoadEventIds;
}

const std::vector<uint16_t> &ScriptedEventProgram::onLeaveEventIds() const
{
    return m_onLeaveEventIds;
}

const std::vector<uint16_t> &ScriptedEventProgram::monsterKilledHookEventIds() const
{
    return m_monsterKilledHookEventIds;
}

const std::vector<uint16_t> &ScriptedEventProgram::monsterDamageHookEventIds() const
{
    return m_monsterDamageHookEventIds;
}

const std::vector<std::string> &ScriptedEventProgram::textureNames() const
{
    return m_textureNames;
}

const std::vector<std::string> &ScriptedEventProgram::spriteNames() const
{
    return m_spriteNames;
}

const std::vector<uint32_t> &ScriptedEventProgram::castSpellIds() const
{
    return m_castSpellIds;
}

const std::vector<ScriptedEventProgram::TimerTrigger> &ScriptedEventProgram::timerTriggers() const
{
    return m_timerTriggers;
}

bool ScriptedEventProgram::isLevitateSensitivePressurePlate(uint16_t eventId, uint32_t faceAttributes) const
{
    return (faceAttributes & m_levitateTrapFaceMask) != 0
        || std::find(m_levitateTrapEvents.begin(), m_levitateTrapEvents.end(), eventId) != m_levitateTrapEvents.end();
}

bool ScriptedEventProgram::hasEvent(uint16_t eventId) const
{
    return std::find(m_eventIds.begin(), m_eventIds.end(), eventId) != m_eventIds.end();
}

bool ScriptedEventProgram::isHintOnlyEvent(uint16_t eventId) const
{
    return !hasEvent(eventId) && getHint(eventId).has_value();
}

std::optional<std::string> ScriptedEventProgram::getHint(uint16_t eventId) const
{
    const auto iterator = m_hints.find(eventId);
    return iterator != m_hints.end() ? std::optional<std::string>(iterator->second) : std::nullopt;
}

std::optional<std::string> ScriptedEventProgram::summarizeEvent(uint16_t eventId) const
{
    const auto iterator = m_summaries.find(eventId);
    return iterator != m_summaries.end() ? std::optional<std::string>(iterator->second) : std::nullopt;
}

std::vector<uint32_t> ScriptedEventProgram::getOpenedChestIds(uint16_t eventId) const
{
    const auto iterator = m_openedChestIdsByEventId.find(eventId);
    return iterator != m_openedChestIdsByEventId.end() ? iterator->second : std::vector<uint32_t>{};
}

std::optional<ScriptedEventProgram::ContextActionMetadata> ScriptedEventProgram::getContextActionMetadata(
    uint16_t eventId) const
{
    const auto iterator = m_contextActionsByEventId.find(eventId);
    return iterator != m_contextActionsByEventId.end()
        ? std::optional<ContextActionMetadata>(iterator->second)
        : std::nullopt;
}

std::vector<ScriptedEventTimerDefinition> scriptedEventTimerDefinitionsFromPrograms(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram)
{
    std::vector<ScriptedEventTimerDefinition> definitions;

    const auto appendDefinitions =
        [&definitions](const std::optional<ScriptedEventProgram> &program)
        {
            if (!program)
            {
                return;
            }

            definitions.insert(
                definitions.end(),
                program->timerTriggers().begin(),
                program->timerTriggers().end());
        };

    appendDefinitions(localProgram);
    appendDefinitions(globalProgram);
    return definitions;
}
}
