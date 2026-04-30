#pragma once

#include "tools/legacy_events/EvtProgram.h"
#include "tools/legacy_events/StrTable.h"

#include <functional>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
enum class LegacyLuaExportScope
{
    Map,
    Global,
};

struct LegacyLuaExportLookups
{
    std::optional<std::string> mapName;
    std::unordered_map<std::string, std::string> mapNamesByFile;
    std::unordered_map<uint32_t, std::string> eventTitles;
    std::unordered_map<uint32_t, std::string> houseNames;
    std::unordered_map<uint32_t, std::string> npcTexts;
    std::unordered_map<uint32_t, std::string> npcNames;
    std::unordered_map<uint32_t, std::string> rosterNames;
    std::unordered_map<uint32_t, std::string> npcTopicNames;
    std::unordered_map<uint32_t, std::string> npcGreetingTexts;
    std::unordered_map<uint32_t, std::string> npcGroupNames;
    std::unordered_map<uint32_t, std::string> npcNewsTexts;
    std::unordered_map<uint32_t, std::string> itemNames;
    std::unordered_map<uint32_t, std::string> objectPayloadNames;
    std::unordered_map<uint32_t, std::string> monsterNames;
    std::unordered_map<uint32_t, std::string> placedMonsterNames;
    std::unordered_map<uint32_t, std::string> actorGroupNames;
    std::unordered_map<uint32_t, std::string> mapEncounterNames;
    std::unordered_map<uint32_t, std::string> spellNames;
    std::unordered_map<uint32_t, std::string> questNotes;
    std::unordered_map<uint32_t, std::string> autonoteTexts;
    std::unordered_map<uint32_t, std::string> awardTexts;
    std::unordered_map<uint32_t, std::string> inputStringAnswerTexts;
};

std::string generateLegacyEventLuaChunk(
    const EvtProgram &evtProgram,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups,
    LegacyLuaExportScope scope);
}
