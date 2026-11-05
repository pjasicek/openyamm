#include "doctest/doctest.h"
#include "game/events/EventRuntime.h"
#include "game/events/ISceneEventContext.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/events/ScriptedEventTimer.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/indoor/IndoorMapData.h"
#include "game/party/Party.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
std::string eventSupportText()
{
    std::ifstream stream(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(stream.good());
    return std::string(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}

// A scene that records the missiles events fire.
class MissileScene : public ISceneEventContext
{
public:
    std::vector<EventMissileRequest> missiles;

    float currentGameMinutes() const override
    {
        return 0.0f;
    }
    const MapDeltaData *mapDeltaData() const override
    {
        return nullptr;
    }
    MapDeltaData *mapDeltaData() override
    {
        return nullptr;
    }
    bool setFacetBit(uint32_t, uint32_t, bool) override
    {
        return false;
    }
    bool fireEventMissile(const EventMissileRequest &request) override
    {
        missiles.push_back(request);
        return request.missile == "CrownIon";
    }
    bool castEventSpell(uint32_t, uint32_t, uint32_t, int32_t, int32_t, int32_t, int32_t, int32_t, int32_t) override
    {
        return false;
    }
    bool summonMonsters(uint32_t, uint32_t, uint32_t, int32_t, int32_t, int32_t, uint32_t, uint32_t) override
    {
        return false;
    }
    bool summonEventItem(uint32_t, int32_t, int32_t, int32_t, int32_t, uint32_t, bool) override
    {
        return false;
    }
    bool summonEventObject(uint32_t, int32_t, int32_t, int32_t, int32_t, uint32_t, bool) override
    {
        return false;
    }
    bool checkMonstersKilled(uint32_t, uint32_t, uint32_t, bool) const override
    {
        return false;
    }
};

// Captures std::cerr for its lifetime.
struct CerrCapture
{
    std::ostringstream text;
    std::streambuf *pPrevious = std::cerr.rdbuf(text.rdbuf());

    ~CerrCapture()
    {
        std::cerr.rdbuf(pPrevious);
    }
};
}

TEST_CASE("a Lua error in an event handler is logged once with its map and event, and ends only that handler")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9002, \"Broken timer\", function()\n"
        "    local missing = nil\n"
        "    missing.call()\n"
        "end)\n"
        "RegisterGlobalEvent(9003, \"Fine\", function()\n"
        "    evt.StatusText(\"fine\")\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@lua_error_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    runtimeState.mapFileName = "hes_test.odm";

    CerrCapture capture;
    CHECK_FALSE(eventRuntime.executeEventById(std::nullopt, program, 9002, runtimeState, nullptr));
    CHECK_FALSE(eventRuntime.executeEventById(std::nullopt, program, 9002, runtimeState, nullptr));
    const std::string logged = capture.text.str();
    CHECK(logged.find("Lua event error: map hes_test.odm event 9002") != std::string::npos);
    CHECK(logged.find("missing") != std::string::npos);
    // A repeating timer that fails each time logs once.
    CHECK(logged.find("Lua event error", logged.find("Lua event error") + 1) == std::string::npos);

    // The session stays usable for the other handlers.
    CHECK(eventRuntime.executeEventById(std::nullopt, program, 9003, runtimeState, nullptr));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 1u);
    CHECK_EQ(runtimeState.statusMessages.front(), "fine");
}

TEST_CASE("evt.SetSectorAmbient overrides a sector's ambient level until a negative level restores the map's")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9004, \"Power off\", function()\n"
        "    evt.SetSectorAmbient(2, 28)\n"
        "end)\n"
        "RegisterGlobalEvent(9005, \"Power on\", function()\n"
        "    evt.SetSectorAmbient(2, -1)\n"
        "end)\n"
        "RegisterGlobalEvent(9006, \"Out of range\", function()\n"
        "    evt.SetSectorAmbient(2, 40)\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@sector_ambient_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    IndoorMapData map = {};
    map.sectors.resize(3);
    map.sectors[2].minAmbientLightLevel = 16;
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};

    CHECK_EQ(IndoorLightingRuntime::sectorAmbientLevel(map, &runtimeState, 2), 16);
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9004, runtimeState, nullptr));
    CHECK_EQ(IndoorLightingRuntime::sectorAmbientLevel(map, &runtimeState, 2), 28);
    CHECK_EQ(IndoorLightingRuntime::sectorAmbientLevel(map, nullptr, 2), 16);
    CHECK_EQ(runtimeState.indoorLightRevision, 1u);
    // Setting the same level again changes nothing.
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9004, runtimeState, nullptr));
    CHECK_EQ(runtimeState.indoorLightRevision, 1u);
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9005, runtimeState, nullptr));
    CHECK_EQ(IndoorLightingRuntime::sectorAmbientLevel(map, &runtimeState, 2), 16);
    CHECK_EQ(runtimeState.indoorLightRevision, 2u);

    CerrCapture capture;
    CHECK_FALSE(eventRuntime.executeEventById(std::nullopt, program, 9006, runtimeState, nullptr));
    CHECK(capture.text.str().find("SetSectorAmbient") != std::string::npos);
    CHECK_EQ(IndoorLightingRuntime::sectorAmbientLevel(map, &runtimeState, 2), 16);
}

TEST_CASE("evt.FireMissile hands the scene its missile; evt.AimDecoration and evt.RecoilDecoration pose a decoration")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9007, \"Fire\", function()\n"
        "    local fired = evt.FireMissile(\"CrownIon\", 1, 2, 3, 400, 500, 600, 1500, \"Energy\", 600, 0.15)\n"
        "    local unknown = evt.FireMissile(\"Nothing\", 0, 0, 0, 1, 1, 1, 1, \"Fire\", 0)\n"
        "    if fired and not unknown then evt.StatusText(\"fired\") end\n"
        "end)\n"
        "RegisterGlobalEvent(9008, \"Aim\", function()\n"
        "    evt.AimDecoration(9311, 90, 45)\n"
        "    evt.RecoilDecoration(9311, 350, 1.0)\n"
        "end)\n"
        "RegisterGlobalEvent(9009, \"Read\", function()\n"
        "    evt.StatusText(string.format(\"%.0f\", evt.DecorationAim(9311)))\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@missile_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    MissileScene scene;

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9007, runtimeState, nullptr, &scene));
    REQUIRE_EQ(scene.missiles.size(), 2u);
    const EventMissileRequest &missile = scene.missiles.front();
    CHECK_EQ(missile.missile, "CrownIon");
    CHECK_EQ(missile.fromZ, doctest::Approx(3.0f));
    CHECK_EQ(missile.toY, doctest::Approx(500.0f));
    CHECK_EQ(missile.damage, 1500);
    CHECK_EQ(missile.damageType, "Energy");
    CHECK_EQ(missile.radius, doctest::Approx(600.0f));
    CHECK_EQ(missile.flightSeconds, doctest::Approx(0.15f));
    CHECK_EQ(scene.missiles.back().flightSeconds, doctest::Approx(0.0f));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 1u);

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9008, runtimeState, nullptr, &scene));
    REQUIRE(runtimeState.decorationAims.contains(9311));
    // 45 degrees a second: half way after a second, there after two, and no further.
    advanceDecorationAims(runtimeState, 1.0f);
    const EventRuntimeState::DecorationAim &aim = runtimeState.decorationAims.at(9311);
    CHECK_EQ(aim.currentRadians, doctest::Approx(0.7853982f));
    CHECK_EQ(aim.back(), doctest::Approx(0.0f));
    advanceDecorationAims(runtimeState, 1.5f);
    CHECK_EQ(aim.currentRadians, doctest::Approx(1.5707964f));
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9009, runtimeState, nullptr, &scene));
    CHECK_EQ(runtimeState.statusMessages.back(), "90");

    // The recoil kicks out over its first tenth, then eases home.
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9008, runtimeState, nullptr, &scene));
    advanceDecorationAims(runtimeState, 0.1f);
    CHECK_EQ(aim.back(), doctest::Approx(350.0f));
    advanceDecorationAims(runtimeState, 0.45f);
    CHECK_EQ(aim.back(), doctest::Approx(87.5f));
    advanceDecorationAims(runtimeState, 0.5f);
    CHECK_EQ(aim.back(), doctest::Approx(0.0f));
}

TEST_CASE("evt.StopTimer stops an event's timer until evt.StartTimer runs it again after its delay")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9010, \"Stop\", function() evt.StopTimer(77) end)\n"
        "RegisterGlobalEvent(9011, \"Start\", function() evt.StartTimer(77, 120) end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@timer_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};

    ScriptedEventTimerState timer = {};
    timer.definition.eventId = 77;
    timer.definition.repeating = true;
    timer.definition.intervalGameMinutes = 1.0;
    timer.nextAlarmGameMinutes = 1.0;
    std::vector<ScriptedEventTimerState> timers = {timer};
    int fired = 0;
    const auto run = [&](double now)
    {
        updateScriptedEventTimers(
            timers, now, [&](const ScriptedEventTimerDefinition &) { return ++fired > 0; },
            &runtimeState.timerControls);
    };

    run(1.0);
    CHECK_EQ(fired, 1);
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9010, runtimeState, nullptr));
    run(2.0);
    run(5.0);
    CHECK_EQ(fired, 1);
    CHECK(timers.front().stopped);
    // 120 game seconds: two game minutes after the start.
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9011, runtimeState, nullptr));
    run(6.0);
    CHECK_EQ(fired, 1);
    run(8.0);
    CHECK_EQ(fired, 2);
    run(9.0);
    CHECK_EQ(fired, 3);
}

TEST_CASE("evt.SpendAction gives the active character the console's recovery")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9012, \"Console\", function() evt.SpendAction(2.5) end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@action_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    Party party = {};
    PartySeed seed = {};
    Character member = {};
    member.name = "Ada";
    member.maxHealth = 10;
    member.health = 10;
    seed.members = {member, member};
    party.seed(seed);

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9012, runtimeState, &party));
    REQUIRE(party.activeMember() != nullptr);
    CHECK_EQ(party.activeMember()->recoverySecondsRemaining, doctest::Approx(2.5f));
}

TEST_CASE("AdvanceGameMinutes runs out the party's buffs with the clock")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9013, \"Cast Off\", function() AdvanceGameMinutes(14 * 24 * 60) end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@advance_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    Party party = {};
    PartySeed seed = {};
    Character member = {};
    member.name = "Ada";
    member.maxHealth = 10;
    member.health = 10;
    seed.members = {member};
    party.seed(seed);
    party.applyPartyBuff(PartyBuffId::DayOfGods, 50.0f * 3600.0f, 30, 83, 10, SkillMastery::Grandmaster, 0);
    REQUIRE(party.hasPartyBuff(PartyBuffId::DayOfGods));

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9013, runtimeState, &party));
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::DayOfGods));
}

TEST_CASE("Cmp of a character variable under ForPlayer All passes when any member passes")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9014, \"Check\", function()\n"
        "    evt.ForPlayer(Players.All)\n"
        "    if IsAtLeast(BlasterSkill, 1) then evt.StatusText(\"blaster\") else evt.StatusText(\"none\") end\n"
        "    if IsAtLeast(BaseLevel, 20) then evt.StatusText(\"veteran\") else evt.StatusText(\"novice\") end\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@cmp_all_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    Party party = {};
    PartySeed seed = {};
    Character member = {};
    member.name = "Ada";
    member.level = 5;
    member.maxHealth = 10;
    member.health = 10;
    seed.members = {member, member, member};
    party.seed(seed);

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9014, runtimeState, &party));
    CHECK_EQ(runtimeState.statusMessages, std::vector<std::string>{"none", "novice"});

    // The last member alone has Blaster and the level: the party passes both checks.
    party.member(2)->skills["Blaster"] = {"Blaster", 7, SkillMastery::Master};
    party.member(2)->level = 25;
    runtimeState.statusMessages.clear();
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9014, runtimeState, &party));
    CHECK_EQ(runtimeState.statusMessages, std::vector<std::string>{"blaster", "veteran"});
}
