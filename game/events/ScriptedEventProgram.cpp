#include "game/events/ScriptedEventProgram.h"

#include "engine/scripting/LuaStateOwner.h"

#include <algorithm>

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
std::vector<TValue> readIntegerArrayFromField(lua_State *pLuaState, int tableIndex, const char *pFieldName)
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
    sortAndUnique(values);
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

std::vector<ScriptedEventProgram::TimerTrigger> readTimerTriggers(lua_State *pLuaState, int tableIndex)
{
    std::vector<ScriptedEventProgram::TimerTrigger> timers;
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

                lua_getfield(pLuaState, -1, "eventId");
                if (lua_isinteger(pLuaState, -1))
                {
                    timer.eventId = static_cast<uint16_t>(lua_tointeger(pLuaState, -1));
                }
                lua_pop(pLuaState, 1);

                lua_getfield(pLuaState, -1, "repeating");
                timer.repeating = lua_toboolean(pLuaState, -1) != 0;
                lua_pop(pLuaState, 1);

                lua_getfield(pLuaState, -1, "targetHour");
                if (lua_isinteger(pLuaState, -1))
                {
                    timer.targetHour = static_cast<int>(lua_tointeger(pLuaState, -1));
                }
                lua_pop(pLuaState, 1);

                lua_getfield(pLuaState, -1, "intervalGameMinutes");
                if (lua_isnumber(pLuaState, -1))
                {
                    timer.intervalGameMinutes = static_cast<float>(lua_tonumber(pLuaState, -1));
                }
                lua_pop(pLuaState, 1);

                lua_getfield(pLuaState, -1, "remainingGameMinutes");
                if (lua_isnumber(pLuaState, -1))
                {
                    timer.remainingGameMinutes = static_cast<float>(lua_tonumber(pLuaState, -1));
                }
                lua_pop(pLuaState, 1);

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

    program.m_onLoadEventIds = readIntegerArrayFromField<uint16_t>(pLuaState, -1, "onLoad");
    program.m_hints = readStringMapFromField(pLuaState, -1, "hint");
    program.m_summaries = readStringMapFromField(pLuaState, -1, "title");

    if (program.m_summaries.empty())
    {
        program.m_summaries = readStringMapFromField(pLuaState, -1, "summary");
    }

    program.m_openedChestIdsByEventId = readOpenedChestIds(pLuaState, -1);
    program.m_textureNames = readStringArrayFromField(pLuaState, -1, "textureNames");
    program.m_spriteNames = readStringArrayFromField(pLuaState, -1, "spriteNames");
    program.m_castSpellIds = readIntegerArrayFromField<uint32_t>(pLuaState, -1, "castSpellIds");
    program.m_timerTriggers = readTimerTriggers(pLuaState, -1);
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
}
