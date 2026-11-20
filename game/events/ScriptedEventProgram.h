#pragma once

#include "game/events/ScriptedEventTimer.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

struct lua_State;

namespace OpenYAMM::Game
{
class ScriptedEventProgram
{
public:
    using TimerTrigger = ScriptedEventTimerDefinition;

    struct ContextActionMetadata
    {
        std::string kind;
        std::string source;
        std::optional<uint32_t> houseId;
        std::optional<std::string> targetMap;
        std::optional<std::string> targetName;
        std::vector<uint32_t> chestIds;
        bool hidden = false;
    };

    // An effect the event's hover name shows once the party has the autonote that records it.
    struct LearnedEffect
    {
        uint32_t autonoteId = 0;
        std::string effect;
    };

    // A map's own cell of the faction relation table (hostile.txt), as MMMerge's map scripts patch Game.HostileTxt
    // after LocalHostileTxt(): how faction `faction` treats faction `otherFaction` (0 is the party) on this map.
    // Factions are the table's numbers: monster id m belongs to faction (m - 1) / 3 + 1.
    struct FactionRelation
    {
        uint32_t faction = 0;
        uint32_t otherFaction = 0;
        int relation = 0;
    };

    static std::optional<ScriptedEventProgram> loadFromLuaText(
        const std::string &luaSourceText,
        const std::string &luaSourceName,
        ScriptedEventScope scope,
        std::string &error);

    const std::optional<std::string> &luaSourceText() const;
    const std::optional<std::string> &luaSourceName() const;
    uint64_t cacheId() const;
    ScriptedEventScope scope() const;
    const std::vector<uint16_t> &eventIds() const;
    const std::vector<uint16_t> &canShowTopicEventIds() const;
    const std::vector<uint16_t> &onLoadEventIds() const;
    const std::vector<uint16_t> &onLeaveEventIds() const;
    const std::vector<uint16_t> &monsterKilledHookEventIds() const;
    const std::vector<uint16_t> &monsterDamageHookEventIds() const;
    const std::vector<std::string> &textureNames() const;
    const std::vector<std::string> &spriteNames() const;
    const std::vector<uint32_t> &castSpellIds() const;
    const std::vector<FactionRelation> &factionRelations() const;
    const std::vector<TimerTrigger> &timerTriggers() const;
    bool hasEvent(uint16_t eventId) const;
    bool isLevitateSensitivePressurePlate(uint16_t eventId, uint32_t faceAttributes) const;
    bool isHintOnlyEvent(uint16_t eventId) const;
    std::optional<std::string> getHint(uint16_t eventId) const;
    std::optional<std::string> summarizeEvent(uint16_t eventId) const;
    std::optional<LearnedEffect> learnedEffect(uint16_t eventId) const;
    std::vector<uint32_t> getOpenedChestIds(uint16_t eventId) const;
    std::optional<ContextActionMetadata> getContextActionMetadata(uint16_t eventId) const;

private:
    // A title, hint or target name in the interface language (devdocs/LOCALIZATION.md).
    std::string localizedText(const std::string &english) const;
    static bool populateMetadataFromLua(
        lua_State *pLuaState,
        ScriptedEventScope scope,
        ScriptedEventProgram &program,
        std::string &error);

    std::optional<std::string> m_luaSourceText;
    std::optional<std::string> m_luaSourceName;
    uint64_t m_cacheId = 0;
    ScriptedEventScope m_scope = ScriptedEventScope::Map;
    std::vector<uint16_t> m_eventIds;
    std::vector<uint16_t> m_canShowTopicEventIds;
    std::vector<uint16_t> m_onLoadEventIds;
    std::vector<uint16_t> m_onLeaveEventIds;
    std::vector<uint16_t> m_monsterKilledHookEventIds;
    std::vector<uint16_t> m_monsterDamageHookEventIds;
    std::unordered_map<uint16_t, std::string> m_hints;
    std::unordered_map<uint16_t, std::string> m_summaries;
    std::unordered_map<uint16_t, LearnedEffect> m_learnedEffects;
    std::unordered_map<uint16_t, std::vector<uint32_t>> m_openedChestIdsByEventId;
    std::unordered_map<uint16_t, ContextActionMetadata> m_contextActionsByEventId;
    std::vector<std::string> m_textureNames;
    std::vector<std::string> m_spriteNames;
    std::vector<uint32_t> m_castSpellIds;
    std::vector<FactionRelation> m_factionRelations;
    uint32_t m_levitateTrapFaceMask = 0;
    std::vector<uint16_t> m_levitateTrapEvents;
    std::vector<TimerTrigger> m_timerTriggers;
};

std::vector<ScriptedEventTimerDefinition> scriptedEventTimerDefinitionsFromPrograms(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram);
}
