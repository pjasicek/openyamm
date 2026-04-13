#pragma once

#include <lua.h>

#include <memory>
#include <optional>
#include <string>

namespace OpenYAMM::Engine
{
class LuaStateOwner
{
public:
    LuaStateOwner();
    ~LuaStateOwner();

    LuaStateOwner(const LuaStateOwner &) = delete;
    LuaStateOwner &operator=(const LuaStateOwner &) = delete;

    LuaStateOwner(LuaStateOwner &&other) noexcept;
    LuaStateOwner &operator=(LuaStateOwner &&other) noexcept;

    lua_State *state() const;
    bool isValid() const;

    void openApprovedLibraries();

    bool runChunk(
        const std::string &chunkText,
        const std::string &chunkName,
        std::optional<std::string> &errorMessage) const;

    bool call(
        int argumentCount,
        int resultCount,
        std::optional<std::string> &errorMessage) const;

    int createRegistryReference() const;
    void releaseRegistryReference(int reference) const;
    void pushRegistryReference(int reference) const;

private:
    static int traceback(lua_State *pLuaState);

    std::unique_ptr<lua_State, void (*)(lua_State *)> m_state;
};
}
