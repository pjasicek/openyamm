#include "doctest/doctest.h"

#include "tools/LegacyLuaExport.h"

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

    const size_t timerLineMatch = lua.find("intervalGameMinutes = 2.5");
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
