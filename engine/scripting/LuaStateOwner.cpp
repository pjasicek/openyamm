#include "engine/scripting/LuaStateOwner.h"

extern "C"
{
#include <lauxlib.h>
#include <lualib.h>
}

namespace OpenYAMM::Engine
{
namespace
{
void closeLuaState(lua_State *pLuaState)
{
    if (pLuaState != nullptr)
    {
        lua_close(pLuaState);
    }
}
}

LuaStateOwner::LuaStateOwner()
    : m_state(luaL_newstate(), closeLuaState)
{
}

LuaStateOwner::~LuaStateOwner() = default;

LuaStateOwner::LuaStateOwner(LuaStateOwner &&other) noexcept
    : m_state(std::move(other.m_state))
{
}

LuaStateOwner &LuaStateOwner::operator=(LuaStateOwner &&other) noexcept
{
    if (this != &other)
    {
        m_state = std::move(other.m_state);
    }

    return *this;
}

lua_State *LuaStateOwner::state() const
{
    return m_state.get();
}

bool LuaStateOwner::isValid() const
{
    return m_state != nullptr;
}

void LuaStateOwner::openApprovedLibraries()
{
    lua_State *pLuaState = state();

    if (pLuaState == nullptr)
    {
        return;
    }

    luaL_requiref(pLuaState, "_G", luaopen_base, 1);
    lua_pop(pLuaState, 1);
    luaL_requiref(pLuaState, LUA_TABLIBNAME, luaopen_table, 1);
    lua_pop(pLuaState, 1);
    luaL_requiref(pLuaState, LUA_STRLIBNAME, luaopen_string, 1);
    lua_pop(pLuaState, 1);
    luaL_requiref(pLuaState, LUA_MATHLIBNAME, luaopen_math, 1);
    lua_pop(pLuaState, 1);
    luaL_requiref(pLuaState, LUA_COLIBNAME, luaopen_coroutine, 1);
    lua_pop(pLuaState, 1);
}

bool LuaStateOwner::runChunk(
    const std::string &chunkText,
    const std::string &chunkName,
    std::optional<std::string> &errorMessage) const
{
    lua_State *pLuaState = state();

    if (pLuaState == nullptr)
    {
        errorMessage = "lua state unavailable";
        return false;
    }

    if (luaL_loadbuffer(pLuaState, chunkText.c_str(), chunkText.size(), chunkName.c_str()) != LUA_OK)
    {
        errorMessage = lua_tostring(pLuaState, -1);
        lua_pop(pLuaState, 1);
        return false;
    }

    return call(0, 0, errorMessage);
}

bool LuaStateOwner::call(
    int argumentCount,
    int resultCount,
    std::optional<std::string> &errorMessage) const
{
    lua_State *pLuaState = state();

    if (pLuaState == nullptr)
    {
        errorMessage = "lua state unavailable";
        return false;
    }

    const int baseIndex = lua_gettop(pLuaState) - argumentCount;
    lua_pushcfunction(pLuaState, traceback);
    lua_insert(pLuaState, baseIndex);

    if (lua_pcall(pLuaState, argumentCount, resultCount, baseIndex) != LUA_OK)
    {
        errorMessage = lua_tostring(pLuaState, -1);
        lua_pop(pLuaState, 1);
        lua_remove(pLuaState, baseIndex);
        return false;
    }

    lua_remove(pLuaState, baseIndex);
    return true;
}

int LuaStateOwner::createRegistryReference() const
{
    return luaL_ref(state(), LUA_REGISTRYINDEX);
}

void LuaStateOwner::releaseRegistryReference(int reference) const
{
    if (reference != LUA_NOREF && reference != LUA_REFNIL)
    {
        luaL_unref(state(), LUA_REGISTRYINDEX, reference);
    }
}

void LuaStateOwner::pushRegistryReference(int reference) const
{
    lua_rawgeti(state(), LUA_REGISTRYINDEX, reference);
}

int LuaStateOwner::traceback(lua_State *pLuaState)
{
    const char *pMessage = lua_tostring(pLuaState, 1);

    if (pMessage == nullptr)
    {
        if (luaL_callmeta(pLuaState, 1, "__tostring") != 0)
        {
            return 1;
        }

        pMessage = "lua error object is not a string";
    }

    luaL_traceback(pLuaState, pLuaState, pMessage, 1);
    return 1;
}
}
