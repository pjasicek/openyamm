#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

struct lua_State;

namespace OpenYAMM::Game
{
enum class ScriptedEventScope
{
    Map,
    Global,
};

class ScriptedEventProgram
{
public:
    struct TimerTrigger
    {
        uint16_t eventId = 0;
        bool repeating = false;
        int targetHour = 0;
        float intervalGameMinutes = 0.0f;
        float remainingGameMinutes = 0.0f;
    };

    static std::optional<ScriptedEventProgram> loadFromLuaText(
        const std::string &luaSourceText,
        const std::string &luaSourceName,
        ScriptedEventScope scope,
        std::string &error);

    const std::optional<std::string> &luaSourceText() const;
    const std::optional<std::string> &luaSourceName() const;
    ScriptedEventScope scope() const;
    const std::vector<uint16_t> &eventIds() const;
    const std::vector<uint16_t> &canShowTopicEventIds() const;
    const std::vector<uint16_t> &onLoadEventIds() const;
    const std::vector<std::string> &textureNames() const;
    const std::vector<std::string> &spriteNames() const;
    const std::vector<uint32_t> &castSpellIds() const;
    const std::vector<TimerTrigger> &timerTriggers() const;
    bool hasEvent(uint16_t eventId) const;
    std::optional<std::string> getHint(uint16_t eventId) const;
    std::optional<std::string> summarizeEvent(uint16_t eventId) const;
    std::vector<uint32_t> getOpenedChestIds(uint16_t eventId) const;

private:
    static bool populateMetadataFromLua(
        lua_State *pLuaState,
        ScriptedEventScope scope,
        ScriptedEventProgram &program,
        std::string &error);

    std::optional<std::string> m_luaSourceText;
    std::optional<std::string> m_luaSourceName;
    ScriptedEventScope m_scope = ScriptedEventScope::Map;
    std::vector<uint16_t> m_eventIds;
    std::vector<uint16_t> m_canShowTopicEventIds;
    std::vector<uint16_t> m_onLoadEventIds;
    std::unordered_map<uint16_t, std::string> m_hints;
    std::unordered_map<uint16_t, std::string> m_summaries;
    std::unordered_map<uint16_t, std::vector<uint32_t>> m_openedChestIdsByEventId;
    std::vector<std::string> m_textureNames;
    std::vector<std::string> m_spriteNames;
    std::vector<uint32_t> m_castSpellIds;
    std::vector<TimerTrigger> m_timerTriggers;
};
}
