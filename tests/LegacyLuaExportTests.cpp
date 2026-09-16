#include "doctest/doctest.h"

#include "tools/LegacyLuaExport.h"
#include "game/events/ScriptedEventProgram.h"

#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

namespace
{
std::vector<uint8_t> readBinaryFixture(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    REQUIRE_MESSAGE(stream.good(), path.string().c_str());
    return std::vector<uint8_t>(
        std::istreambuf_iterator<char>(stream),
        std::istreambuf_iterator<char>());
}

std::string extractLuaEvent(const std::string &lua, const std::string &eventRegistration)
{
    const size_t eventStart = lua.find(eventRegistration);
    REQUIRE(eventStart != std::string::npos);

    size_t eventEnd = lua.find("\n\nRegister", eventStart + eventRegistration.size());

    if (eventEnd == std::string::npos)
    {
        eventEnd = lua.size();
    }

    return lua.substr(eventStart, eventEnd - eventStart);
}

std::string extractTimerMetadata(
    const std::string &lua,
    uint16_t sourceEventId,
    size_t occurrence = 0)
{
    const std::string sourceText = "sourceEventId = " + std::to_string(sourceEventId);
    size_t sourcePosition = 0;

    for (size_t index = 0; index <= occurrence; ++index)
    {
        sourcePosition = lua.find(sourceText, sourcePosition);
        REQUIRE(sourcePosition != std::string::npos);
        ++sourcePosition;
    }

    const size_t lineStart = lua.rfind('{', sourcePosition);
    const size_t lineEnd = lua.find('\n', sourcePosition);
    REQUIRE(lineStart != std::string::npos);
    REQUIRE(lineEnd != std::string::npos);
    return lua.substr(lineStart, lineEnd - lineStart);
}

void appendTimerRecord(
    std::vector<uint8_t> &evtBytes,
    uint16_t eventId,
    uint8_t step,
    OpenYAMM::Game::EvtOpcode opcode,
    const std::array<uint8_t, 10> &descriptor)
{
    evtBytes.push_back(14);
    evtBytes.push_back(static_cast<uint8_t>(eventId & 0xffu));
    evtBytes.push_back(static_cast<uint8_t>(eventId >> 8));
    evtBytes.push_back(step);
    evtBytes.push_back(static_cast<uint8_t>(opcode));
    evtBytes.insert(evtBytes.end(), descriptor.begin(), descriptor.end());
}

void appendExitRecord(std::vector<uint8_t> &evtBytes, uint16_t eventId, uint8_t step)
{
    evtBytes.push_back(4);
    evtBytes.push_back(static_cast<uint8_t>(eventId & 0xffu));
    evtBytes.push_back(static_cast<uint8_t>(eventId >> 8));
    evtBytes.push_back(step);
    evtBytes.push_back(static_cast<uint8_t>(OpenYAMM::Game::EvtOpcode::Exit));
}

OpenYAMM::Game::ScriptedEventProgram exportPressureTrapProgram(
    const std::vector<uint8_t> &bytes,
    OpenYAMM::Game::LegacyEventVersion version,
    const std::string &mapName = "test.blv")
{
    using namespace OpenYAMM::Game;
    EvtProgram legacyProgram;
    REQUIRE(legacyProgram.loadFromBytes(bytes));
    LegacyLuaExportLookups lookups;
    lookups.sourceMapFile = mapName;
    const std::string lua = generateLegacyEventLuaChunk(
        legacyProgram, StrTable{}, lookups, LegacyLuaExportScope::Map, version);
    const std::vector<uint8_t> supportBytes = readBinaryFixture(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/scripts/common/event_support.lua");
    std::string error;
    const std::optional<ScriptedEventProgram> program = ScriptedEventProgram::loadFromLuaText(
        std::string(supportBytes.begin(), supportBytes.end()) + "\n" + lua,
        "pressure-trap-test", ScriptedEventScope::Map, error);
    REQUIRE_MESSAGE(program.has_value(), error);
    return *program;
}
}

TEST_CASE("levitate pressure trap export respects each worlds event semantics")
{
    using namespace OpenYAMM::Game;
    const std::filesystem::path worlds = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds";
    const ScriptedEventProgram mm7 = exportPressureTrapProgram(
        readBinaryFixture(worlds / "mm7/_legacy/events/7d10.EVT"), LegacyEventVersion::Mm7);
    CHECK(mm7.isLevitateSensitivePressurePlate(451, 0x84000102));
    CHECK(mm7.isLevitateSensitivePressurePlate(452, 0x84000100));
    CHECK_FALSE(mm7.isLevitateSensitivePressurePlate(501, 0x8c000100));

    const ScriptedEventProgram mm6 = exportPressureTrapProgram(
        readBinaryFixture(worlds / "mm6/_legacy/events/6D03.EVT"), LegacyEventVersion::Mm6, "6d03.blv");
    CHECK(mm6.isLevitateSensitivePressurePlate(21, 0x84000100));
    CHECK_FALSE(mm6.isLevitateSensitivePressurePlate(22, 0x8c000100));

    const ScriptedEventProgram puzzle = exportPressureTrapProgram(
        readBinaryFixture(worlds / "mm6/_legacy/events/6D08.EVT"), LegacyEventVersion::Mm6, "6d08.blv");
    for (uint16_t eventId : {22, 23, 25, 32, 34, 35, 36, 39, 40, 41, 42})
    {
        CHECK(puzzle.isLevitateSensitivePressurePlate(eventId, 0x84000100));
    }
    CHECK_FALSE(puzzle.isLevitateSensitivePressurePlate(24, 0x84000100));

    const ScriptedEventProgram encounter = exportPressureTrapProgram(
        readBinaryFixture(worlds / "mm7/_legacy/events/7out02.EVT"), LegacyEventVersion::Mm7);
    CHECK_FALSE(encounter.isLevitateSensitivePressurePlate(236, 0x04000100));

    const ScriptedEventProgram mm8 = exportPressureTrapProgram(
        readBinaryFixture(worlds / "mm8/_legacy/events/D26.EVT"), LegacyEventVersion::Mm8);
    CHECK(mm8.isLevitateSensitivePressurePlate(101, 0x8c000102));
    CHECK_FALSE(mm8.isLevitateSensitivePressurePlate(101, 0x84000102));
}

TEST_CASE("levitate pressure trap inference rejects benefits and reachable side effects")
{
    using namespace OpenYAMM::Game;
    std::vector<uint8_t> bytes;
    const auto appendRecord = [&](uint16_t eventId, uint8_t step, EvtOpcode opcode, std::vector<uint8_t> payload)
    {
        bytes.push_back(static_cast<uint8_t>(4 + payload.size()));
        bytes.push_back(static_cast<uint8_t>(eventId));
        bytes.push_back(0);
        bytes.push_back(step);
        bytes.push_back(static_cast<uint8_t>(opcode));
        bytes.insert(bytes.end(), payload.begin(), payload.end());
    };
    std::vector<uint8_t> fireball(27, 0);
    fireball[0] = 6;
    fireball[2] = 5;
    std::vector<uint8_t> wizardEye = fireball;
    wizardEye[0] = 12;
    appendRecord(1, 0, EvtOpcode::CastSpell, fireball);
    appendExitRecord(bytes, 1, 1);
    appendRecord(1, 2, EvtOpcode::Set, {0x75, 0, 1, 0, 0, 0}); // Unreachable state change.
    appendRecord(2, 0, EvtOpcode::CastSpell, wizardEye);
    appendExitRecord(bytes, 2, 1);
    appendRecord(3, 0, EvtOpcode::CastSpell, fireball);
    appendRecord(3, 1, EvtOpcode::Set, {0x75, 0, 1, 0, 0, 0});
    appendExitRecord(bytes, 3, 2);
    appendRecord(4, 0, EvtOpcode::Compare, {0x75, 0, 1, 0, 0, 0, 3});
    appendRecord(4, 1, EvtOpcode::CastSpell, fireball);
    appendExitRecord(bytes, 4, 2);
    appendRecord(4, 3, EvtOpcode::Set, {0x75, 0, 1, 0, 0, 0});
    appendExitRecord(bytes, 4, 4);
    appendRecord(5, 0, EvtOpcode::CastSpell, fireball);
    appendRecord(5, 1, EvtOpcode::CastSpell, wizardEye);
    appendExitRecord(bytes, 5, 2);

    const ScriptedEventProgram program = exportPressureTrapProgram(bytes, LegacyEventVersion::Mm7);
    CHECK(program.isLevitateSensitivePressurePlate(1, 0x04000000));
    for (uint16_t eventId : {2, 3, 4, 5})
    {
        CHECK_FALSE(program.isLevitateSensitivePressurePlate(eventId, 0x04000000));
    }
}

TEST_CASE("legacy lua exporter preserves return for castle gloaming soul jar chest")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm7/_legacy/events/d03.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm7/_legacy/events/d03.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "Castle Gloaming";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm7);

    const size_t eventStart = lua.find("RegisterEvent(176");
    REQUIRE(eventStart != std::string::npos);
    const size_t eventEnd = lua.find("RegisterEvent(177", eventStart);
    REQUIRE(eventEnd != std::string::npos);
    const std::string eventLua = lua.substr(eventStart, eventEnd - eventStart);
    INFO(eventLua);

    const size_t chest0 = eventLua.find("evt.OpenChest(0)");
    const size_t qbit743 = eventLua.find("SetQBit(QBit(743))", chest0);
    const size_t qbit662 = eventLua.find("SetQBit(QBit(662))", qbit743);
    const size_t branchReturn = eventLua.find("return", qbit662);
    const size_t laterChest1 = eventLua.find("evt.OpenChest(1)", qbit662);

    REQUIRE(chest0 != std::string::npos);
    REQUIRE(qbit743 != std::string::npos);
    REQUIRE(qbit662 != std::string::npos);
    REQUIRE(branchReturn != std::string::npos);
    REQUIRE(laterChest1 != std::string::npos);
    CHECK(chest0 < qbit743);
    CHECK(qbit743 < qbit662);
    CHECK(qbit662 < branchReturn);
    CHECK(branchReturn < laterChest1);
}

TEST_CASE("legacy lua exporter separates timer continuation from direct event body")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm7/_legacy/events/7d35.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm7/_legacy/events/7d35.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "Nighon Tunnels";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm7);

    const size_t timerLineMatch = lua.find("intervalHalfMinutes = 5");
    REQUIRE(timerLineMatch != std::string::npos);
    const size_t timerLineStart = lua.rfind('{', timerLineMatch);
    const size_t timerLineEnd = lua.find('\n', timerLineMatch);
    REQUIRE(timerLineStart != std::string::npos);
    REQUIRE(timerLineEnd != std::string::npos);
    const std::string timerLine = lua.substr(timerLineStart, timerLineEnd - timerLineStart);
    INFO(timerLine);
    CHECK(timerLine.find("eventId = 452") == std::string::npos);

    const size_t timerEventIdStart = timerLine.find("eventId = ");
    REQUIRE(timerEventIdStart != std::string::npos);
    const size_t timerEventIdValueStart = timerEventIdStart + std::string("eventId = ").size();
    const size_t timerEventIdValueEnd = timerLine.find(',', timerEventIdValueStart);
    REQUIRE(timerEventIdValueEnd != std::string::npos);
    const std::string timerEventIdText =
        timerLine.substr(timerEventIdValueStart, timerEventIdValueEnd - timerEventIdValueStart);

    const size_t directEventStart = lua.find("RegisterEvent(452");
    REQUIRE(directEventStart != std::string::npos);
    const size_t directEventEnd = lua.find("RegisterEvent(454", directEventStart);
    REQUIRE(directEventEnd != std::string::npos);
    const std::string directEventLua = lua.substr(directEventStart, directEventEnd - directEventStart);
    INFO(directEventLua);
    CHECK(directEventLua.find("evt.MoveToMap(1232, 6896, -384") != std::string::npos);
    CHECK(directEventLua.find("evt.CastSpell(6") == std::string::npos);

    const std::string syntheticRegistration = "RegisterEvent(" + timerEventIdText;
    const size_t timerEventStart = lua.find(syntheticRegistration);
    REQUIRE(timerEventStart != std::string::npos);
    const size_t timerEventEnd = lua.find("\n\n", timerEventStart);
    REQUIRE(timerEventEnd != std::string::npos);
    const std::string timerEventLua = lua.substr(timerEventStart, timerEventEnd - timerEventStart);
    INFO(timerEventLua);
    CHECK(timerEventLua.find("evt.MoveToMap(1232, 6896, -384") == std::string::npos);
    CHECK(timerEventLua.find("evt.CastSpell(6, 7, 4, 13891") != std::string::npos);
    CHECK(timerEventLua.find("evt.CastSpell(6, 7, 4, 14618") != std::string::npos);
}

TEST_CASE("legacy lua exporter emits New Sorpigal first-visit fountain refill timer")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/OUTE3.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/OutE3.str");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "New Sorpigal";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm6);

    const std::string fountainTimer = extractTimerMetadata(lua, 130);
    INFO(fountainTimer);
    CHECK(fountainTimer.find("eventId = 130") != std::string::npos);
    CHECK(fountainTimer.find("triggerStep = 0") != std::string::npos);
    CHECK(fountainTimer.find("origin = \"legacy\"") != std::string::npos);
    CHECK(fountainTimer.find("triggerKind = \"long\"") != std::string::npos);
    CHECK(fountainTimer.find("scheduleKind = \"daily\"") != std::string::npos);
    CHECK(fountainTimer.find("startHour = 0") != std::string::npos);
    CHECK(fountainTimer.find("startMinute = 0") != std::string::npos);
    CHECK(fountainTimer.find("startSecond = 1") != std::string::npos);

    const std::string dragonTowerTimer = extractTimerMetadata(lua, 230);
    INFO(dragonTowerTimer);
    CHECK(dragonTowerTimer.find("triggerKind = \"timer\"") != std::string::npos);
    CHECK(dragonTowerTimer.find("scheduleKind = \"interval\"") != std::string::npos);
    CHECK(dragonTowerTimer.find("intervalHalfMinutes = 10") != std::string::npos);
}

TEST_CASE("legacy lua exporter preserves every repeated long timer trigger")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm7/_legacy/events/7d14.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm7/_legacy/events/7d14.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        {},
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm7);

    const std::string weeklyTimer = extractTimerMetadata(lua, 196, 0);
    const std::string firstYearlyTimer = extractTimerMetadata(lua, 196, 1);
    const std::string secondYearlyTimer = extractTimerMetadata(lua, 196, 2);
    INFO(weeklyTimer);
    INFO(firstYearlyTimer);
    INFO(secondYearlyTimer);
    CHECK(weeklyTimer.find("triggerStep = 22") != std::string::npos);
    CHECK(weeklyTimer.find("scheduleKind = \"weekly\"") != std::string::npos);
    CHECK(firstYearlyTimer.find("triggerStep = 25") != std::string::npos);
    CHECK(firstYearlyTimer.find("scheduleKind = \"yearly\"") != std::string::npos);
    CHECK(secondYearlyTimer.find("triggerStep = 26") != std::string::npos);
    CHECK(secondYearlyTimer.find("scheduleKind = \"yearly\"") != std::string::npos);
}

TEST_CASE("legacy lua exporter decodes the complete timer interval word")
{
    const std::vector<uint8_t> evtBytes = {
        14,
        77, 0,
        0, static_cast<uint8_t>(OpenYAMM::Game::EvtOpcode::OnTimer),
        0, 0, 0, 0, 0, 0,
        1, 2,
        0, 0,
    };

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        {},
        {},
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm7);

    const std::string timer = extractTimerMetadata(lua, 77);
    INFO(timer);
    CHECK(timer.find("intervalHalfMinutes = 513") != std::string::npos);
}

TEST_CASE("legacy lua exporter preserves calendar precedence and daily offsets")
{
    std::vector<uint8_t> evtBytes;
    appendTimerRecord(
        evtBytes,
        70,
        0,
        OpenYAMM::Game::EvtOpcode::OnLongTimer,
        {2, 3, 4, 25, 61, 59, 0, 0, 0, 0});
    appendTimerRecord(
        evtBytes,
        71,
        0,
        OpenYAMM::Game::EvtOpcode::OnLongTimer,
        {0, 7, 8, 0, 0, 0, 0, 0, 0, 0});
    appendTimerRecord(
        evtBytes,
        72,
        0,
        OpenYAMM::Game::EvtOpcode::OnLongTimer,
        {0, 0, 9, 0, 0, 0, 0, 0, 0, 0});
    appendTimerRecord(
        evtBytes,
        73,
        0,
        OpenYAMM::Game::EvtOpcode::OnLongTimer,
        {0, 0, 0, 27, 61, 59, 0, 0, 0, 0});

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        {},
        {},
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm7);

    CHECK(extractTimerMetadata(lua, 70).find("scheduleKind = \"yearly\"") != std::string::npos);
    CHECK(extractTimerMetadata(lua, 71).find("scheduleKind = \"monthly\"") != std::string::npos);
    CHECK(extractTimerMetadata(lua, 72).find("scheduleKind = \"weekly\"") != std::string::npos);

    const std::string daily = extractTimerMetadata(lua, 73);
    CHECK(daily.find("scheduleKind = \"daily\"") != std::string::npos);
    CHECK(daily.find("startHour = 27") != std::string::npos);
    CHECK(daily.find("startMinute = 61") != std::string::npos);
    CHECK(daily.find("startSecond = 59") != std::string::npos);
}

TEST_CASE("legacy lua exporter emits every mixed timer trigger in one event")
{
    std::vector<uint8_t> evtBytes;
    appendTimerRecord(
        evtBytes,
        80,
        0,
        OpenYAMM::Game::EvtOpcode::OnTimer,
        {0, 0, 0, 0, 0, 0, 2, 0, 0, 0});
    appendExitRecord(evtBytes, 80, 1);
    appendTimerRecord(
        evtBytes,
        80,
        2,
        OpenYAMM::Game::EvtOpcode::OnLongTimer,
        {0, 0, 1, 0, 0, 0, 0, 0, 0, 0});
    appendExitRecord(evtBytes, 80, 3);
    appendTimerRecord(
        evtBytes,
        80,
        4,
        OpenYAMM::Game::EvtOpcode::OnTimer,
        {0, 0, 0, 0, 0, 0, 4, 0, 0, 0});
    appendExitRecord(evtBytes, 80, 5);

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        {},
        {},
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm7);

    const std::string first = extractTimerMetadata(lua, 80, 0);
    const std::string second = extractTimerMetadata(lua, 80, 1);
    const std::string third = extractTimerMetadata(lua, 80, 2);
    CHECK(first.find("triggerStep = 0") != std::string::npos);
    CHECK(first.find("triggerKind = \"timer\"") != std::string::npos);
    CHECK(second.find("triggerStep = 2") != std::string::npos);
    CHECK(second.find("triggerKind = \"long\"") != std::string::npos);
    CHECK(third.find("triggerStep = 4") != std::string::npos);
    CHECK(third.find("triggerKind = \"timer\"") != std::string::npos);
}

TEST_CASE("legacy lua exporter prefers house names over stale mouseover hints for house events")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/OUTB2.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/OUTB2.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "Blackshire";
    lookups.houseNames[34] = "Stout Heart Staff and Spear";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm6);

    const size_t eventStart = lua.find("RegisterEvent(2");
    REQUIRE(eventStart != std::string::npos);
    const size_t eventEnd = lua.find("RegisterEvent(3", eventStart);
    REQUIRE(eventEnd != std::string::npos);
    const std::string eventLua = lua.substr(eventStart, eventEnd - eventStart);
    INFO(eventLua);

    CHECK(eventLua.find("RegisterEvent(2, \"Stout Heart Staff and Spear\"") != std::string::npos);
    CHECK(eventLua.find("end, \"Stout Heart Staff and Spear\")") != std::string::npos);
    CHECK(eventLua.find("You pray at the shrine") == std::string::npos);
}

TEST_CASE("legacy lua exporter remaps outdoor dungeon transitions to current map house ids")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/OUTB1.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/OUTB1.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "Kriegspire";
    lookups.mapNamesByFile["6t7.blv"] = "Superior Temple of Baa";
    lookups.currentMapDungeonEntryHouseIdsByName["superior temple of baa"] = 435;

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm6);

    const std::string templeLua = extractLuaEvent(lua, "RegisterEvent(90");
    INFO(templeLua);
    CHECK(templeLua.find("evt.MoveToMap(2094, -19, 177, 337, 0, 0, 435, 1, \"6t7.blv\")")
        != std::string::npos);
    CHECK(templeLua.find("evt.MoveToMap(2094, -19, 177, 337, 0, 0, 179, 1, \"6t7.blv\")")
        == std::string::npos);
}

TEST_CASE("legacy lua exporter omits generated fallback titles")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/6T1.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/6T1.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "Temple of Baa";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm6);

    const std::string eventLua = extractLuaEvent(lua, "RegisterEvent(26");
    INFO(eventLua);
    CHECK(eventLua.find("RegisterEvent(26, nil, function()") != std::string::npos);
    CHECK(eventLua.find("Legacy event 26") == std::string::npos);
}

TEST_CASE("legacy lua exporter emits context action metadata")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/6T1.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/6T1.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "Temple of Baa";
    lookups.sourceMapFile = "6t1.blv";
    lookups.mapNamesByFile["outd3.odm"] = "New Sorpigal";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm6);

    CHECK(lua.find("contextActions = {") != std::string::npos);
    CHECK(lua.find("[1] = { kind = \"open_door\", source = \"title\" }") != std::string::npos);
    CHECK(lua.find("[28] = { kind = \"open_chest\", source = \"opcode\", chestIds = {2} }") != std::string::npos);
    CHECK(lua.find("[34] = { kind = \"fountain\", source = \"title\" }") != std::string::npos);
    CHECK(lua.find("[50] = { kind = \"leave_dungeon\", source = \"opcode\", targetMap = \"outd3.odm\"")
        != std::string::npos);
    CHECK(lua.find("targetName = \"New Sorpigal\"") != std::string::npos);
}

TEST_CASE("legacy lua exporter rewrites unrolled party member rewards to dynamic party loops")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/6T5.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/6T5.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "Temple of Baa";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm6);

    const std::string mightAltarLua = extractLuaEvent(lua, "RegisterEvent(16");
    INFO(mightAltarLua);
    CHECK(mightAltarLua.find("for _, player in ipairs(PartyMembers()) do") != std::string::npos);
    CHECK(mightAltarLua.find("evt.ForPlayer(player)") != std::string::npos);
    CHECK(mightAltarLua.find("evt.ForPlayer(Players.Member0)") == std::string::npos);
    CHECK(mightAltarLua.find("evt.ForPlayer(Players.Current)") == std::string::npos);
}

TEST_CASE("legacy lua exporter keeps the first-member luck altar exception in dynamic party loops")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/6T5.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/6T5.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "Temple of Baa";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm6);

    const std::string luckAltarLua = extractLuaEvent(lua, "RegisterEvent(21");
    INFO(luckAltarLua);
    CHECK(luckAltarLua.find("for _, player in ipairs(PartyMembers()) do") != std::string::npos);
    CHECK(luckAltarLua.find("if player == Players.Member0 then") != std::string::npos);
    CHECK(luckAltarLua.find("AddValue(BaseLuck, 2)") != std::string::npos);
    CHECK(luckAltarLua.find("AddValue(BaseLuck, 5)") != std::string::npos);
    CHECK(luckAltarLua.find("evt.ForPlayer(Players.Current)") == std::string::npos);
}

TEST_CASE("legacy lua exporter rewrites party loops that reset the selected player afterward")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/6D13.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/6D13.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "The Monolith";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm6);

    const std::string altarLua = extractLuaEvent(lua, "RegisterEvent(24");
    INFO(altarLua);
    CHECK(altarLua.find("for _, player in ipairs(PartyMembers()) do") != std::string::npos);
    CHECK(altarLua.find("evt.ForPlayer(Players.All)") != std::string::npos);
    CHECK(altarLua.find("evt.ForPlayer(Players.Member0)") == std::string::npos);
    CHECK(altarLua.find("evt.ForPlayer(Players.Member3)") == std::string::npos);
}

TEST_CASE("legacy lua exporter rewrites lincoln wetsuit checks to all active party members")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm7/_legacy/events/7d23.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm7/_legacy/events/7d23.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "The Lincoln";
    lookups.itemNames[1406] = "Wetsuit";
    lookups.mapNamesByFile["7out15.odm"] = "Shoals";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm7);

    const std::string leaveLincolnLua = extractLuaEvent(lua, "RegisterEvent(501");
    INFO(leaveLincolnLua);
    CHECK(leaveLincolnLua.find("local hasAllWetsuits = true") != std::string::npos);
    CHECK(leaveLincolnLua.find("for _, player in ipairs(PartyMembers()) do") != std::string::npos);
    CHECK(leaveLincolnLua.find("if not HasItem(1406) then -- Wetsuit") != std::string::npos);
    CHECK(leaveLincolnLua.find("evt.MoveToMap(-7005, 7856, 225, 128") != std::string::npos);
    CHECK(leaveLincolnLua.find("evt.ForPlayer(Players.Member0)") == std::string::npos);
    CHECK(leaveLincolnLua.find("evt.ForPlayer(Players.Current)") == std::string::npos);
}

TEST_CASE("legacy lua exporter rewrites lich ritual checks and promotions to all active party members")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm7/_legacy/events/Global.EVT");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Global,
        OpenYAMM::Game::LegacyEventVersion::Mm7);

    const std::string ritualLua = extractLuaEvent(lua, "RegisterGlobalEvent(847");
    INFO(ritualLua);
    CHECK(ritualLua.find("local hasAllLichJars = true") != std::string::npos);
    CHECK(ritualLua.find("for _, player in ipairs(PartyMembers()) do") != std::string::npos);
    CHECK(ritualLua.find("if not HasItem(1417) then -- Lich Jar") != std::string::npos);
    CHECK(ritualLua.find("SetValue(ClassId, 45)") != std::string::npos);
    CHECK(ritualLua.find("while HasItem(1417) do -- Lich Jar") != std::string::npos);
    CHECK(ritualLua.find("evt.SetNPCGreeting(388, 194)") != std::string::npos);
    CHECK(ritualLua.find("local function Step_0()") == std::string::npos);
    CHECK(ritualLua.find("evt.ForPlayer(Players.Member0)") == std::string::npos);
    CHECK(ritualLua.find("evt.ForPlayer(Players.Member3)") == std::string::npos);
}

TEST_CASE("legacy lua exporter keeps mm8 lich jar checks on necromancers")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm8/_legacy/events/Global.EVT");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.itemNames[628] = "Lich Jar";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Global,
        OpenYAMM::Game::LegacyEventVersion::Mm8);

    const std::string promotionLua = extractLuaEvent(lua, "RegisterGlobalEvent(89");
    INFO(promotionLua);
    CHECK(promotionLua.find("if IsAtLeast(ClassId, 44) then") != std::string::npos);
    CHECK(promotionLua.find("if not HasItem(628) then -- Lich Jar") != std::string::npos);
    CHECK(promotionLua.find("if not IsAtLeast(ClassId, 44) then") == std::string::npos);

    const std::string repeatPromotionLua = extractLuaEvent(lua, "RegisterGlobalEvent(738");
    INFO(repeatPromotionLua);
    CHECK(repeatPromotionLua.find("if IsAtLeast(ClassId, 44) then") != std::string::npos);
    CHECK(repeatPromotionLua.find("if not HasItem(628) then -- Lich Jar") != std::string::npos);
    CHECK(repeatPromotionLua.find("if not IsAtLeast(ClassId, 44) then") == std::string::npos);
}

TEST_CASE("legacy lua exporter preserves mm8 reagent item ranges")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm8/_legacy/events/Global.EVT");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Global,
        OpenYAMM::Game::LegacyEventVersion::Mm8);

    const std::string pureSpeedLua = extractLuaEvent(lua, "RegisterGlobalEvent(181");
    INFO(pureSpeedLua);
    CHECK(pureSpeedLua.find("evt.CheckItemsCount(200, 204, 4)") != std::string::npos);
    CHECK(pureSpeedLua.find("evt.CheckItemsCount(205, 209, 2)") != std::string::npos);
    CHECK(pureSpeedLua.find("evt.CheckItemsCount(210, 214, 1)") != std::string::npos);
    CHECK(pureSpeedLua.find("evt.RemoveItems(200, 204, 4)") != std::string::npos);
    CHECK(pureSpeedLua.find("evt.RemoveItems(205, 209, 2)") != std::string::npos);
    CHECK(pureSpeedLua.find("evt.RemoveItems(210, 214, 1)") != std::string::npos);
    CHECK(pureSpeedLua.find("DecorVar(") == std::string::npos);
}

TEST_CASE("legacy lua exporter labels mm8 summon item payloads as item ids")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm8/_legacy/events/Out01.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm8/_legacy/events/OUT01.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.itemNames[200] = "Widowsweep Berries";
    lookups.objectPayloadNames[200] = "Fae dust";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm8);

    const std::string palmTreeLua = extractLuaEvent(lua, "RegisterEvent(494");
    INFO(palmTreeLua);
    CHECK(palmTreeLua.find("evt.SummonItem(200, 3896, 8080, 544, 1000, 1, true) -- Widowsweep Berries")
        != std::string::npos);
    CHECK(palmTreeLua.find("-- Fae dust") == std::string::npos);
}

TEST_CASE("legacy lua exporter preserves mm8 indoor light group ids")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm8/_legacy/events/D05.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm8/_legacy/events/D05.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "Abandoned Temple";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm8);

    const std::string buttonLua = extractLuaEvent(lua, "RegisterEvent(106");
    INFO(buttonLua);
    CHECK(buttonLua.find("evt.SetTexture(5, \"t65b11b\")") != std::string::npos);
    CHECK(buttonLua.find("evt.SetLight(5, 0)") != std::string::npos);
    CHECK(buttonLua.find("evt.SetLight(5, 1)") != std::string::npos);
    CHECK(buttonLua.find("evt.SetLight(4, 0)") == std::string::npos);
}

TEST_CASE("legacy lua exporter keeps mm6 indoor light ids zero based")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::vector<uint8_t> evtBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/SEWER.EVT");
    const std::vector<uint8_t> strBytes =
        readBinaryFixture(sourceRoot / "assets_dev/worlds/mm6/_legacy/events/SEWER.STR");

    OpenYAMM::Game::EvtProgram evtProgram = {};
    REQUIRE(evtProgram.loadFromBytes(evtBytes));

    OpenYAMM::Game::StrTable strTable = {};
    REQUIRE(strTable.loadFromBytes(strBytes));

    OpenYAMM::Game::LegacyLuaExportLookups lookups = {};
    lookups.mapName = "Sewer";

    const std::string lua = OpenYAMM::Game::generateLegacyEventLuaChunk(
        evtProgram,
        strTable,
        lookups,
        OpenYAMM::Game::LegacyLuaExportScope::Map,
        OpenYAMM::Game::LegacyEventVersion::Mm6);

    INFO(lua);
    CHECK(lua.find("evt.SetLight(0, 1)") != std::string::npos);
}
