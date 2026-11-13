#include "doctest/doctest.h"
#include "game/events/EventRuntime.h"
#include "game/events/ISceneEventContext.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/events/ScriptedEventTimer.h"
#include "game/gameplay/GameplayMonsterSpawn.h"
#include "game/gameplay/ScriptedActorMoves.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/indoor/IndoorMapData.h"
#include "game/party/Party.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <optional>
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

TEST_CASE("a map script's local faction relations reach its program, and malformed rows fail the load")
{
    std::string error;
    const std::optional<ScriptedEventProgram> program = ScriptedEventProgram::loadFromLuaText(
        eventSupportText() + "\nSetLocalFactionRelations({{211, 0, 0}, {211, 173, 2}})\n"
            "SetLocalFactionRelations({{173, 211, 1}})\n",
        "@faction_relations_test.lua",
        ScriptedEventScope::Map,
        error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    const std::vector<ScriptedEventProgram::FactionRelation> &relations = program->factionRelations();
    REQUIRE_EQ(relations.size(), 3);
    CHECK_EQ(relations[0].faction, 211u);
    CHECK_EQ(relations[0].otherFaction, 0u);
    CHECK_EQ(relations[0].relation, 0);
    CHECK_EQ(relations[1].otherFaction, 173u);
    CHECK_EQ(relations[1].relation, 2);
    CHECK_EQ(relations[2].faction, 173u);

    CHECK_FALSE(ScriptedEventProgram::loadFromLuaText(
        eventSupportText() + "\nSetLocalFactionRelations({{211, 0, 7}})\n",
        "@faction_relations_bad.lua",
        ScriptedEventScope::Map,
        error));
    CHECK(error.find("factionRelations entry 1") != std::string::npos);
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

TEST_CASE("an item an event gives waits for the hand-over through the events that run before it")
{
    // A dialogue's close gives the item in the frame's input step; the world step's timers run events before the game
    // hands it over (GameplayHeldItemController::applyGrantedEventItemsToHeldInventory). They lost it (MM9 Johannes's
    // Book Key, 2026-11-08).
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9020, \"Give\", function()\n"
        "    GiveItem(244)\n"
        "end)\n"
        "RegisterGlobalEvent(9021, \"A timer\", function()\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@granted_items_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9020, runtimeState, nullptr));
    CHECK_EQ(runtimeState.grantedItems.size(), 1u);
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9021, runtimeState, nullptr));
    REQUIRE_EQ(runtimeState.grantedItems.size(), 1u);
    CHECK_EQ(runtimeState.grantedItems.front().objectDescriptionId, 244u);
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

TEST_CASE("evt.PlayDecorationClip plays, loops, ends and clears a decoration part's clip")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9020, \"Open\", function() evt.PlayDecorationClip(315, \"open\") end)\n"
        "RegisterGlobalEvent(9021, \"Spin\", function() evt.PlayDecorationClip(316, \"spin\", \"loop\") end)\n"
        "RegisterGlobalEvent(9022, \"Left open\", function() evt.PlayDecorationClip(317, \"open\", \"end\") end)\n"
        "RegisterGlobalEvent(9023, \"Shut\", function() evt.PlayDecorationClip(315, \"\") end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@decoration_clip_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};

    for (const uint16_t eventId : {9020, 9021, 9022})
    {
        REQUIRE(eventRuntime.executeEventById(std::nullopt, program, eventId, runtimeState, nullptr, nullptr));
    }
    advanceDecorationClips(runtimeState, 0.75f);
    const EventRuntimeState::DecorationClip &open = runtimeState.decorationClips.at(315);
    CHECK_EQ(open.clip, "open");
    CHECK_FALSE(open.loop);
    CHECK_EQ(open.seconds, doctest::Approx(0.75f));
    CHECK(runtimeState.decorationClips.at(316).loop);
    // "end" stands at the clip's last frame whatever its length, and stays there.
    CHECK_EQ(runtimeState.decorationClips.at(317).seconds, std::numeric_limits<float>::max());
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9023, runtimeState, nullptr, nullptr));
    CHECK_FALSE(runtimeState.decorationClips.contains(315));
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

namespace
{
// A map whose decoration with cog 404 runs event 304 (Sturmford City's Ake the Righteous).
class TalkingPropScene : public MissileScene
{
public:
    std::optional<uint32_t> decorationSpriteKeyForScriptEvent(uint16_t eventId) const override
    {
        return eventId == 304 ? std::optional<uint32_t>(404) : std::nullopt;
    }
};
}

TEST_CASE("evt.OpenMm9Rude from a decoration's click event records that decoration for the dialogue")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(304, \"Ake\", function() evt.OpenMm9Rude(86) end)\n"
        "RegisterGlobalEvent(305, \"Elsewhere\", function() evt.OpenMm9Rude(43) end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@talking_prop_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    TalkingPropScene scene;

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 304, runtimeState, nullptr, &scene));
    REQUIRE(runtimeState.pendingDialogueContext.has_value());
    CHECK(runtimeState.pendingDialogueContext->kind == DialogueContextKind::Mm9Rude);
    CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 86u);
    CHECK(runtimeState.pendingDialogueContext->sourceDecorationKey == std::optional<uint32_t>(404));

    runtimeState.pendingDialogueContext.reset();
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 305, runtimeState, nullptr, &scene));
    REQUIRE(runtimeState.pendingDialogueContext.has_value());
    CHECK_FALSE(runtimeState.pendingDialogueContext->sourceDecorationKey.has_value());
}

namespace
{
// A scene with actors 0-9 standing at (index * 100, 0, 0), whose spawns are actors 20, 21 ... (standing likewise)
class ActorScene : public MissileScene
{
public:
    std::vector<GameplayMonsterSpawnRequest> spawns;
    std::vector<std::pair<size_t, std::optional<size_t>>> targetOrders;

    bool setMapActorTarget(size_t actorIndex, std::optional<size_t> targetActorIndex) override
    {
        if (actorIndex >= 10 || (targetActorIndex && *targetActorIndex >= 10))
        {
            return false;
        }

        targetOrders.emplace_back(actorIndex, targetActorIndex);
        return true;
    }

    bool mapActorPosition(size_t actorIndex, float &x, float &y, float &z) const override
    {
        if (actorIndex >= 10 && actorIndex < 20)
        {
            return false;
        }

        x = float(actorIndex) * 100.0f;
        y = 0.0f;
        z = 0.0f;
        return true;
    }

    std::vector<size_t> spawnMonsters(const GameplayMonsterSpawnRequest &request) override
    {
        spawns.push_back(request);
        std::vector<size_t> indices;

        for (uint32_t index = 0; index < request.count; ++index)
        {
            indices.push_back(20 + index);
        }

        return indices;
    }
};
}

TEST_CASE("evt.SummonMonstersById plays its effect where each spawned monster stands")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9024, \"Gate\", function()\n"
        "    evt.SummonMonstersById({monster = 9079, x = 1, y = 2, z = 3, count = 2, effect = \"mm9:fireblue\",\n"
        "        effectScale = 0.5})\n"
        "    evt.SummonMonstersById({monster = 9079, x = 1, y = 2, z = 3})\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@summon_effect_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    ActorScene scene;

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9024, runtimeState, nullptr, &scene));
    REQUIRE_EQ(runtimeState.worldEffectRequests.size(), 2u);
    CHECK_EQ(runtimeState.worldEffectRequests[0].id, "mm9:fireblue");
    CHECK_EQ(runtimeState.worldEffectRequests[0].position[0], doctest::Approx(2000.0f));
    CHECK_EQ(runtimeState.worldEffectRequests[1].position[0], doctest::Approx(2100.0f));
    CHECK_EQ(runtimeState.worldEffectRequests[1].scale, doctest::Approx(0.5f));
}

TEST_CASE("evt.SpawnActorEffect and evt.StopActorEffect queue effects carried on an actor, in call order")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9025, \"Carry\", function()\n"
        "    evt.SpawnActorEffect(3, \"mm9:bluedots\", \"palm_left\", 2.5, 0.5)\n"
        "    evt.SpawnActorEffect(4, \"mm9:greenyeldots\")\n"
        "    evt.StopActorEffect(3, \"mm9:bluedots\")\n"
        "    evt.StopActorEffect(4)\n"
        "end)\n"
        "RegisterGlobalEvent(9026, \"Bad\", function()\n"
        "    evt.SpawnActorEffect(3, \"mm9:bluedots\", \"palm_left\", -1)\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@actor_effect_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    ActorScene scene;

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9025, runtimeState, nullptr, &scene));
    REQUIRE_EQ(runtimeState.actorEffectRequests.size(), 4u);
    const EventRuntimeState::ActorEffectRequest &first = runtimeState.actorEffectRequests[0];
    CHECK_EQ(first.actorIndex, 3u);
    CHECK_EQ(first.effectId, "mm9:bluedots");
    CHECK_EQ(first.socket, "palm_left");
    CHECK_EQ(first.seconds, doctest::Approx(2.5f));
    CHECK_EQ(first.scale, doctest::Approx(0.5f));
    CHECK_FALSE(first.stop);
    CHECK(runtimeState.actorEffectRequests[1].socket.empty());
    CHECK_EQ(runtimeState.actorEffectRequests[1].seconds, doctest::Approx(0.0f));
    CHECK(runtimeState.actorEffectRequests[2].stop);
    CHECK_EQ(runtimeState.actorEffectRequests[2].effectId, "mm9:bluedots");
    CHECK(runtimeState.actorEffectRequests[3].stop);
    CHECK(runtimeState.actorEffectRequests[3].effectId.empty());

    runtimeState.actorEffectRequests.clear();
    eventRuntime.executeEventById(std::nullopt, program, 9026, runtimeState, nullptr, &scene);
    CHECK(runtimeState.actorEffectRequests.empty());
}

TEST_CASE("evt.MoveActorTo walks a map actor until it arrives; evt.SummonMonstersById names the spawned actors")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9020, \"Walk\", function()\n"
        "    local walking = evt.MoveActorTo(3, 1000, 50, 0, 9022, true)\n"
        "    local nobody = evt.MoveActorTo(15, 0, 0, 0)\n"
        "    evt.MoveActorTo(4, 400, 0, 0)\n"
        "    if walking and not nobody and evt.IsActorMoving(3) then evt.StatusText(\"walking\") end\n"
        "end)\n"
        "RegisterGlobalEvent(9021, \"Stop\", function()\n"
        "    local stopped = evt.StopActorMove(4)\n"
        "    local again = evt.StopActorMove(4)\n"
        "    if stopped and not again and not evt.IsActorMoving(4) then evt.StatusText(\"stopped\") end\n"
        "end)\n"
        "RegisterGlobalEvent(9023, \"Spawn\", function()\n"
        "    local count, made = evt.SummonMonstersById({monster = 9158, x = 1, y = 2, z = 3, count = 2, hostile = false, yawDegrees = 180})\n"
        "    evt.StatusText(count .. \":\" .. made[1] .. \",\" .. made[2])\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@move_actor_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    ActorScene scene;

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9020, runtimeState, nullptr, &scene));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 1u);
    CHECK_EQ(runtimeState.statusMessages.back(), "walking");
    REQUIRE(runtimeState.scriptedActorMoves.contains(3));
    CHECK_FALSE(runtimeState.scriptedActorMoves.contains(15));
    const EventRuntimeState::ScriptedActorMove &move = runtimeState.scriptedActorMoves.at(3);
    CHECK_EQ(move.point[0], doctest::Approx(1000.0f));
    CHECK_EQ(move.arrivalEventId, 9022);
    CHECK(move.run);
    CHECK_FALSE(runtimeState.scriptedActorMoves.at(4).run);

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9021, runtimeState, nullptr, &scene));
    CHECK_EQ(runtimeState.statusMessages.back(), "stopped");
    CHECK_FALSE(runtimeState.scriptedActorMoves.contains(4));

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9023, runtimeState, nullptr, &scene));
    CHECK_EQ(runtimeState.statusMessages.back(), "2:20,21");
    REQUIRE_EQ(scene.spawns.size(), 1u);
    CHECK_FALSE(scene.spawns.front().hostile);
    REQUIRE(scene.spawns.front().yawRadians.has_value());
    CHECK_EQ(*scene.spawns.front().yawRadians, doctest::Approx(3.1415927f));
}

TEST_CASE("applyScriptedActorMoves steers a walker, queues its arrival and drops a dead walker's move")
{
    EventRuntimeState state = {};
    state.scriptedActorMoves[1] = {{1000.0f, 0.0f, 0.0f}, 77, true};
    state.scriptedActorMoves[2] = {{500.0f, 0.0f, 0.0f}, 78, false};
    state.scriptedActorMoves[3] = {{0.0f, 0.0f, 0.0f}, 79, false};
    state.scriptedActorMoves[5] = {{0.0f, 0.0f, 0.0f}, 80, false};

    const auto actorAt = [](size_t index, float x)
    {
        ActorAiFacts actor = {};
        actor.actorIndex = index;
        actor.stats.currentHp = 10;
        actor.stats.radius = 40;
        actor.movement.position = {x, 0.0f, 0.0f};
        return actor;
    };
    ActorAiFrameFacts facts = {};
    facts.activeActors = {actorAt(0, 0.0f), actorAt(1, 0.0f), actorAt(2, 430.0f)};
    ActorAiFacts dead = actorAt(3, 600.0f);
    dead.stats.currentHp = 0;
    facts.backgroundActors = {dead};
    applyScriptedActorMoves(state, facts);

    // Actor 1 walks on; actor 2 is within its radius and 32 of its point and arrives.
    REQUIRE(facts.activeActors[1].movement.scriptedMoveTarget.has_value());
    CHECK_EQ(facts.activeActors[1].movement.scriptedMoveTarget->x, doctest::Approx(1000.0f));
    CHECK(facts.activeActors[1].movement.scriptedMoveRun);
    CHECK_FALSE(facts.activeActors[0].movement.scriptedMoveTarget.has_value());
    CHECK_FALSE(facts.activeActors[2].movement.scriptedMoveTarget.has_value());
    REQUIRE_EQ(state.pendingActorArrivals.size(), 1u);
    CHECK_EQ(state.pendingActorArrivals.front().actorIndex, 2u);
    CHECK_EQ(state.pendingActorArrivals.front().eventId, 78);
    // The dead one's move ends without its event; actor 5, in neither list, keeps its move.
    CHECK(state.scriptedActorMoves.contains(1));
    CHECK_FALSE(state.scriptedActorMoves.contains(2));
    CHECK_FALSE(state.scriptedActorMoves.contains(3));
    CHECK(state.scriptedActorMoves.contains(5));
}

TEST_CASE("applyScriptedActorMoves ends a walk that gets nowhere without its arrival")
{
    EventRuntimeState state = {};
    state.scriptedActorMoves[1] = {{1000.0f, 0.0f, 0.0f}, 77, false};
    state.scriptedActorMoves[2] = {{1000.0f, 0.0f, 0.0f}, 78, false};
    state.scriptedActorMoves[3] = {{1000.0f, 0.0f, 0.0f}, 79, false};

    const auto walkerAt = [](size_t index, float x, ActorAiMotionState motion)
    {
        ActorAiFacts actor = {};
        actor.actorIndex = index;
        actor.stats.currentHp = 10;
        actor.stats.radius = 40;
        actor.movement.position = {x, 0.0f, 0.0f};
        actor.runtime.motionState = motion;
        actor.runtime.animationState =
            motion == ActorAiMotionState::Wandering ? ActorAiAnimationState::Walking : ActorAiAnimationState::Standing;
        return actor;
    };
    constexpr float StepSeconds = 1.0f / 128.0f;
    const int steps = int(ScriptedActorMoveGiveUpSeconds / StepSeconds) + 2;

    for (int step = 0; step < steps; ++step)
    {
        ActorAiFrameFacts facts = {};
        facts.fixedStepSeconds = StepSeconds;
        // Actor 1 walks into a wall for good; actor 2 walks on; actor 3 stands (an attack, a status, a hold).
        facts.activeActors = {walkerAt(1, 0.0f, ActorAiMotionState::Wandering),
            walkerAt(2, 0.5f * float(step), ActorAiMotionState::Wandering),
            walkerAt(3, 0.0f, ActorAiMotionState::Standing)};
        applyScriptedActorMoves(state, facts);

        if (step == 0)
        {
            CHECK_EQ(facts.activeActors[0].movement.scriptedMoveArrivalDistance,
                doctest::Approx(40.0f + ScriptedActorMoveArrivalDistance));
        }
    }

    CHECK_FALSE(state.scriptedActorMoves.contains(1));
    CHECK(state.scriptedActorMoves.contains(2));
    CHECK(state.scriptedActorMoves.contains(3));
    CHECK(state.pendingActorArrivals.empty());
}

TEST_CASE("evt.SetActorTarget hands the world a party or actor target; SummonMonstersById keeps patrol and mm9")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9030, \"Loose\", function()\n"
        "    local a = evt.SetActorTarget(2, \"party\")\n"
        "    local b = evt.SetActorTarget(3, 5)\n"
        "    local c = evt.SetActorTarget(12, \"party\")\n"
        "    if a and b and not c then evt.StatusText(\"targets\") end\n"
        "end)\n"
        "RegisterGlobalEvent(9031, \"Demon\", function()\n"
        "    evt.SummonMonstersById({monster = 9158, x = 1, y = 2, z = 3, patrol = {{10, 20, 30}, {40, 50.4, 60}},\n"
        "        mm9 = {script_params = \"1\", path = {{100, 200, 0}, {300, 400, 0}}, path_random = true}})\n"
        "end)\n"
        "RegisterGlobalEvent(9032, \"Bad\", function()\n"
        "    evt.SummonMonstersById({monster = 9158, x = 1, y = 2, z = 3, mm9 = {wander_speed = 5}})\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@actor_target_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    ActorScene scene;

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9030, runtimeState, nullptr, &scene));
    CHECK_EQ(runtimeState.statusMessages.back(), "targets");
    REQUIRE_EQ(scene.targetOrders.size(), 2u);
    CHECK_EQ(scene.targetOrders[0].first, 2u);
    CHECK_FALSE(scene.targetOrders[0].second.has_value());
    CHECK_EQ(scene.targetOrders[1].second, std::optional<size_t>(5));

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9031, runtimeState, nullptr, &scene));
    REQUIRE_EQ(scene.spawns.size(), 1u);
    const GameplayMonsterSpawnRequest &demon = scene.spawns.front();
    REQUIRE_EQ(demon.patrolPoints.size(), 2u);
    CHECK_EQ(demon.patrolPoints[1][1], 50);
    CHECK_EQ(demon.patrolPoints[1][2], 60);
    REQUIRE(demon.mm9Ai.has_value());
    CHECK(mm9SpawnedWithParam(*demon.mm9Ai));
    REQUIRE_EQ(demon.mm9Ai->pathPoints.size(), 2u);
    CHECK_EQ(demon.mm9Ai->pathPoints[1][0], 300);
    CHECK(demon.mm9Ai->settings.pathRandom);

    // An unknown mm9 key is the script's error, as in a scene.
    CHECK_FALSE(eventRuntime.executeEventById(std::nullopt, program, 9032, runtimeState, nullptr, &scene));
    CHECK_EQ(scene.spawns.size(), 1u);
}

TEST_CASE("applyScriptedActorTargets gives an active MM9 monster its target and drops orders it cannot use")
{
    EventRuntimeState state = {};
    state.scriptedActorTargets[1] = {};
    state.scriptedActorTargets[2] = {7u};
    state.scriptedActorTargets[3] = {};
    state.scriptedActorTargets[4] = {};
    state.scriptedActorTargets[5] = {};

    const auto actorAt = [](size_t index, bool mm9)
    {
        ActorAiFacts actor = {};
        actor.actorIndex = index;
        actor.stats.currentHp = 10;

        if (mm9)
        {
            actor.tactics.mm9Profile = Mm9AiProfile{};
        }

        return actor;
    };
    ActorAiFrameFacts facts = {};
    ActorAiFacts dead = actorAt(4, true);
    dead.stats.currentHp = 0;
    facts.activeActors = {actorAt(1, true), actorAt(2, true), actorAt(3, false), dead};
    facts.backgroundActors = {actorAt(5, true)};
    applyScriptedActorTargets(state, facts);

    CHECK(facts.activeActors[0].behavior.mm9Script.setTarget);
    CHECK(facts.activeActors[0].behavior.mm9Script.targetKind == ActorAiTargetKind::Party);
    CHECK(facts.activeActors[1].behavior.mm9Script.targetKind == ActorAiTargetKind::Actor);
    CHECK_EQ(facts.activeActors[1].behavior.mm9Script.targetActorIndex, 7u);
    CHECK_FALSE(facts.activeActors[2].behavior.mm9Script.setTarget);
    // Taken, without the MM9 loop, dead: gone; the background one waits.
    CHECK_FALSE(state.scriptedActorTargets.contains(1));
    CHECK_FALSE(state.scriptedActorTargets.contains(2));
    CHECK_FALSE(state.scriptedActorTargets.contains(3));
    CHECK_FALSE(state.scriptedActorTargets.contains(4));
    CHECK(state.scriptedActorTargets.contains(5));
}

namespace
{
// A scene whose evt.KillMapActor runs the map's kill hook at once, as the indoor world does.
class KillHookScene : public ActorScene
{
public:
    const EventRuntime *pRuntime = nullptr;
    const std::optional<ScriptedEventProgram> *pProgram = nullptr;
    EventRuntimeState *pState = nullptr;

    bool killMapActor(size_t) override
    {
        return pRuntime->executeEventById(std::nullopt, *pProgram, 9031, *pState, nullptr, this);
    }
};
}

TEST_CASE("a handler that runs another one from inside keeps its own context afterwards")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9030, \"Outer\", function()\n"
        "    evt.KillMapActor(3)\n"
        "    evt.SetMapVar(\"AfterKill\", 7)\n"
        "    evt.ChangeGroupAlly(2, 0)\n"
        "end)\n"
        "RegisterGlobalEvent(9031, \"Inner\", function() evt.SetMapVar(\"Inner\", 1) end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@nested_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    KillHookScene scene;
    scene.pRuntime = &eventRuntime;
    scene.pProgram = &program;
    scene.pState = &runtimeState;

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9030, runtimeState, nullptr, &scene));
    CHECK_EQ(runtimeState.namedMapVars.at("Inner"), 1);
    CHECK_EQ(runtimeState.namedMapVars.at("AfterKill"), 7);
    REQUIRE(runtimeState.actorGroupAllyOverrides.contains(2));
}

TEST_CASE("an event that gives experience and shows no text of its own says how much (OY-489)")
{
    const std::string source = eventSupportText() + "\n"
        "RegisterGlobalEvent(9030, \"Quiet reward\", function()\n"
        "    AddValue(Experience, 500)\n"
        "end)\n"
        "RegisterGlobalEvent(9031, \"Told reward\", function()\n"
        "    AddValue(Experience, 500)\n"
        "    evt.StatusText(\"+500 Experience.\")\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@experience_notice_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    Party party = {};
    PartySeed seed = {};
    seed.members.resize(2);
    party.seed(seed);
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};
    runtimeState.unscaledExperience = true;

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9030, runtimeState, &party));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 1u);
    CHECK_EQ(runtimeState.statusMessages.front(), "+500 experience");
    CHECK_EQ(runtimeState.handlerExperienceAward, 0);

    runtimeState.statusMessages.clear();
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9031, runtimeState, &party));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 1u);
    CHECK_EQ(runtimeState.statusMessages.front(), "+500 Experience.");
}
