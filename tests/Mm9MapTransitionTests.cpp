#include "doctest/doctest.h"

#include "game/gameplay/GameplayDialogController.h"
#include "game/maps/MapRegistry.h"
#include "game/mm9/Mm9MapTransition.h"
#include "game/mm9/Mm9PositionedTransitionRuntime.h"
#include "game/party/Party.h"
#include "game/ui/GameplayUiController.h"
#include "tests/PartySpellTestHarness.h"

#include <string>
#include <vector>

namespace
{
std::vector<std::string> header()
{
    return {
        "CanonicalId", "SourceMap", "SourceMapFile", "SourceObjectIndex", "SourceName", "SourceClass",
        "CenterX", "CenterY", "CenterZ", "HalfExtentX", "HalfExtentY", "HalfExtentZ", "DestinationMap",
        "DestinationMapFile", "SourceStartPoint", "ResolvedStartPoint", "ArrivalX", "ArrivalY", "ArrivalZ",
        "FacingDegrees", "FacingYawUnits", "MovePlayerToFloor", "AskPlayer", "TravelDays",
        "TravelDaysSentinel", "LoadScreen", "SourceDat", "OverrideId", "Provenance",
    };
}

std::vector<std::string> row()
{
    return {
        "mm9:transition/source/7", "world.mm9.map.source", "source.odm", "7", "Exit0", "ExitTrigger",
        "100", "200", "300", "10", "20", "30", "world.mm9.map.target", "target.odm", "SourceTypo",
        "Arrival", "400", "500", "600", "180", "1024", "1", "1", "-1", "source_default",
        "loadscreen.pcx", "WORLDS/SOURCE.dat", "mm9:transition_override/source/7", "dat+reviewed_override",
    };
}

OpenYAMM::Game::MapRegistry mapRegistry()
{
    OpenYAMM::Game::MapStatsEntry source = {};
    source.id = 1;
    source.worldId = "mm9";
    source.canonicalId = "world.mm9.map.source";
    source.fileName = "source.odm";
    OpenYAMM::Game::MapStatsEntry target = {};
    target.id = 2;
    target.worldId = "mm9";
    target.canonicalId = "world.mm9.map.target";
    target.fileName = "target.odm";
    OpenYAMM::Game::MapRegistry result;
    result.initialize({source, target});
    return result;
}
}

TEST_CASE("MM9 positioned transition table parses resolved source records")
{
    OpenYAMM::Game::Mm9MapTransitionTable table;
    REQUIRE(table.loadFromRows({header(), row()}, mapRegistry()));
    CHECK(table.errors().empty());
    REQUIRE_EQ(table.entries().size(), 1);

    const OpenYAMM::Game::Mm9MapTransition *pEntry =
        table.findByCanonicalId("MM9:TRANSITION/SOURCE/7");
    REQUIRE(pEntry != nullptr);
    CHECK_EQ(pEntry->sourceObjectIndex, 7);
    CHECK_EQ(pEntry->travelDays, -1);
    CHECK(pEntry->sourceDefaultTravelDays);
    CHECK(pEntry->askPlayer);
    CHECK_EQ(pEntry->destinationMapFileName, "target.odm");
    CHECK_EQ(table.forSourceMapFile("SOURCE.ODM").size(), 1);
}

TEST_CASE("MM9 positioned transition table rejects duplicate source ownership")
{
    std::vector<std::string> duplicate = row();
    duplicate[0] = "mm9:transition/source/duplicate";
    OpenYAMM::Game::Mm9MapTransitionTable table;

    CHECK_FALSE(table.loadFromRows({header(), row(), duplicate}, mapRegistry()));
    REQUIRE_EQ(table.errors().size(), 1);
    CHECK(table.errors().front().find("duplicate source object ownership") != std::string::npos);
}

TEST_CASE("MM9 positioned transition table rejects unresolved canonical maps")
{
    std::vector<std::string> unresolved = row();
    unresolved[12] = "world.mm9.map.missing";
    unresolved[13] = "missing.odm";
    OpenYAMM::Game::Mm9MapTransitionTable table;

    CHECK_FALSE(table.loadFromRows({header(), unresolved}, mapRegistry()));
    REQUIRE_EQ(table.errors().size(), 1);
    CHECK(table.errors().front().find("map reference is unresolved") != std::string::npos);
}

TEST_CASE("MM9 positioned transition runtime triggers only on a fresh volume entry")
{
    OpenYAMM::Game::Mm9MapTransitionTable table;
    REQUIRE(table.loadFromRows({header(), row()}, mapRegistry()));
    OpenYAMM::Game::Mm9PositionedTransitionRuntime runtime;
    runtime.configure(table.forSourceMapFile("source.odm"));
    OpenYAMM::Game::EventRuntimeState eventRuntimeState = {};

    CHECK_FALSE(runtime.update(0.0f, 0.0f, 0.0f, eventRuntimeState).has_value());
    const std::optional<OpenYAMM::Game::Mm9PositionedTransitionActivation> activation =
        runtime.update(100.0f, 200.0f, 300.0f, eventRuntimeState);
    REQUIRE(activation.has_value());
    CHECK_EQ(activation->pTransition->sourceObjectIndex, 7);
    REQUIRE(eventRuntimeState.pendingDialogueContext.has_value());
    REQUIRE(eventRuntimeState.pendingDialogueContext->transitionMapMove.has_value());
    CHECK(eventRuntimeState.pendingDialogueContext->transitionMapMove->mapName == "target.odm");
    CHECK_EQ(eventRuntimeState.pendingDialogueContext->transitionMapMove->x, 400);
    REQUIRE(eventRuntimeState.lastMapTransitionRequested.has_value());
    CHECK(eventRuntimeState.lastMapTransitionRequested->sourceKind == "mm9_exit_trigger");

    eventRuntimeState.pendingDialogueContext.reset();
    CHECK_FALSE(runtime.update(100.0f, 200.0f, 300.0f, eventRuntimeState).has_value());
    CHECK_FALSE(runtime.update(0.0f, 0.0f, 0.0f, eventRuntimeState).has_value());
    CHECK(runtime.update(100.0f, 200.0f, 300.0f, eventRuntimeState).has_value());
}

TEST_CASE("MM9 positioned transition runtime initializes safely inside and queues automatic moves")
{
    std::vector<std::string> automatic = row();
    automatic[22] = "0";
    automatic[23] = "6";
    automatic[24] = "";
    OpenYAMM::Game::Mm9MapTransitionTable table;
    REQUIRE(table.loadFromRows({header(), automatic}, mapRegistry()));
    OpenYAMM::Game::Mm9PositionedTransitionRuntime runtime;
    runtime.configure(table.forSourceMapFile("source.odm"));
    OpenYAMM::Game::EventRuntimeState eventRuntimeState = {};

    CHECK_FALSE(runtime.update(100.0f, 200.0f, 300.0f, eventRuntimeState).has_value());
    CHECK_FALSE(eventRuntimeState.pendingMapMove.has_value());
    CHECK_FALSE(runtime.update(0.0f, 0.0f, 0.0f, eventRuntimeState).has_value());
    REQUIRE(runtime.update(100.0f, 200.0f, 300.0f, eventRuntimeState).has_value());
    REQUIRE(eventRuntimeState.pendingMapMove.has_value());
    CHECK(eventRuntimeState.pendingMapMove->mapName == "target.odm");
    REQUIRE(eventRuntimeState.lastMapTransitionRequested.has_value());
    CHECK_EQ(eventRuntimeState.lastMapTransitionRequested->travelDays, 6);
    CHECK_FALSE(eventRuntimeState.lastMapTransitionRequested->confirmationRequired);
}

TEST_CASE("MM9 positioned transition runtime fires when the party's body touches the volume")
{
    // the volume: centre (100, 200, 300), half extents (10, 20, 30): z 270..330, floating over a floor at z 200
    OpenYAMM::Game::Mm9MapTransitionTable table;
    REQUIRE(table.loadFromRows({header(), row()}, mapRegistry()));
    OpenYAMM::Game::Mm9PositionedTransitionRuntime runtime;
    runtime.configure(table.forSourceMapFile("source.odm"));
    OpenYAMM::Game::EventRuntimeState eventRuntimeState = {};

    CHECK_FALSE(runtime.update(0.0f, 0.0f, 200.0f, eventRuntimeState, 37.0f, 160.0f).has_value());
    // the feet below the volume, the body reaching into it, beside it within the radius: MM9's touch
    CHECK(runtime.update(140.0f, 200.0f, 200.0f, eventRuntimeState, 37.0f, 160.0f).has_value());

    // as a point the same spot misses
    OpenYAMM::Game::Mm9PositionedTransitionRuntime pointRuntime;
    pointRuntime.configure(table.forSourceMapFile("source.odm"));
    OpenYAMM::Game::EventRuntimeState pointState = {};
    CHECK_FALSE(pointRuntime.update(0.0f, 0.0f, 200.0f, pointState).has_value());
    CHECK_FALSE(pointRuntime.update(140.0f, 200.0f, 200.0f, pointState).has_value());
}

TEST_CASE("MM9 positioned transition runtime skips an exit a map script turned off")
{
    OpenYAMM::Game::Mm9MapTransitionTable table;
    REQUIRE(table.loadFromRows({header(), row()}, mapRegistry()));
    OpenYAMM::Game::Mm9PositionedTransitionRuntime runtime;
    runtime.configure(table.forSourceMapFile("source.odm"));
    OpenYAMM::Game::EventRuntimeState eventRuntimeState = {};
    eventRuntimeState.namedMapVars["Mm9ExitDisabled7"] = 1;

    CHECK_FALSE(runtime.update(0.0f, 0.0f, 0.0f, eventRuntimeState).has_value());
    CHECK_FALSE(runtime.update(100.0f, 200.0f, 300.0f, eventRuntimeState).has_value());
    // turned on while the party stands in it: it fires
    eventRuntimeState.namedMapVars["Mm9ExitDisabled7"] = 0;
    CHECK(runtime.update(100.0f, 200.0f, 300.0f, eventRuntimeState).has_value());
}

namespace
{
OpenYAMM::Game::MapStatsEntry mm9Map(int id, const std::string &stem, const std::string &name, int areaId)
{
    OpenYAMM::Game::MapStatsEntry entry = {};
    entry.id = id;
    entry.worldId = "mm9";
    entry.canonicalId = "world.mm9.map." + stem;
    entry.name = name;
    entry.fileName = stem + ".blv";
    entry.areaId = areaId;
    return entry;
}

std::vector<std::string> exitRow(uint32_t objectIndex, const std::string &destinationStem, int travelDays)
{
    std::vector<std::string> result = row();
    result[0] = "mm9:transition/sturmford/" + std::to_string(objectIndex);
    result[1] = "world.mm9.map.sturmford";
    result[2] = "sturmford.blv";
    result[3] = std::to_string(objectIndex);
    result[6] = std::to_string(1000 * objectIndex);
    result[12] = "world.mm9.map." + destinationStem;
    result[13] = destinationStem + ".blv";
    result[23] = std::to_string(travelDays);
    result[24] = "";
    result[27] = "";
    return result;
}

struct ExitWalkResult
{
    std::vector<std::string> lines;
    int foodSpent = 0;
    float daysSpent = 0.0f;
};

// Walks into the Sturmford exit with the given source object index, then confirms the dialogue it asks.
ExitWalkResult walkThroughSturmfordExit(uint32_t objectIndex)
{
    const std::vector<OpenYAMM::Game::MapStatsEntry> mapEntries = {
        mm9Map(9004, "sturmford", "Sturmford", 0),
        mm9Map(9006, "drangheim", "Drangheim", 0),
        mm9Map(9036, "anskramkeep", "Anskram Keep", 9004),
    };
    OpenYAMM::Game::MapRegistry registry;
    registry.initialize(mapEntries);
    OpenYAMM::Game::Mm9MapTransitionTable table;
    REQUIRE(table.loadFromRows({header(), exitRow(25, "drangheim", 2), exitRow(23, "anskramkeep", 1)}, registry));

    OpenYAMM::Game::Party party;
    party.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    party.addFood(20 - party.food());
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime;
    worldRuntime.bindParty(&party);
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    worldRuntime.bindEventRuntimeState(&eventRuntimeState);

    OpenYAMM::Game::Mm9PositionedTransitionRuntime runtime;
    runtime.configure(table.forSourceMapFile("sturmford.blv"));
    const float exitX = 1000.0f * static_cast<float>(objectIndex);
    runtime.update(0.0f, 0.0f, 0.0f, eventRuntimeState);
    REQUIRE(runtime.update(exitX, 200.0f, 300.0f, eventRuntimeState).has_value());

    OpenYAMM::Game::GameplayUiController uiController;
    // The game presents into the UI controller's dialogue, as here.
    OpenYAMM::Game::EventDialogContent &dialog = uiController.eventDialog().content;
    size_t &selectionIndex = uiController.eventDialog().selectionIndex;
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pWorldRuntime = &worldRuntime,
        .pMm9MapTransitionTable = &table,
        .pCurrentMap = &mapEntries[0],
        .pMapEntries = &mapEntries,
    };
    const OpenYAMM::Game::GameplayDialogController controller;
    REQUIRE(controller.presentPendingEventDialog(context, 0, false, false).dialogOpened);
    REQUIRE_FALSE(dialog.actions.empty());
    CHECK(dialog.actions[0].kind == OpenYAMM::Game::EventDialogActionKind::MapTransitionConfirm);

    ExitWalkResult result;
    result.lines = dialog.lines;
    const int foodBefore = party.food();
    const float minutesBefore = worldRuntime.gameMinutes();
    selectionIndex = 0;
    CHECK(controller.executeActiveDialogAction(context).shouldCloseActiveDialog);
    CHECK(eventRuntimeState.pendingMapMove.has_value());
    result.foodSpent = foodBefore - party.food();
    result.daysSpent = (worldRuntime.gameMinutes() - minutesBefore) / (24.0f * 60.0f);
    return result;
}
}

TEST_CASE("MM9 walk between two regions states its days and costs five food")
{
    const ExitWalkResult walk = walkThroughSturmfordExit(25);
    REQUIRE_EQ(walk.lines.size(), 2);
    CHECK_EQ(walk.lines[0], "It will take 2 days to travel to Drangheim.");
    CHECK_EQ(walk.lines[1], "Do you wish to leave Sturmford?");
    CHECK_EQ(walk.foodSpent, OpenYAMM::Game::Mm9RegionWalkFood);
    CHECK_EQ(walk.daysSpent, doctest::Approx(2.0f));
}

TEST_CASE("MM9 exit into a dungeon with days on the road costs a food a day")
{
    const ExitWalkResult walk = walkThroughSturmfordExit(23);
    REQUIRE_EQ(walk.lines.size(), 2);
    CHECK_EQ(walk.lines[0], "It will take 1 day to travel to Anskram Keep.");
    CHECK_EQ(walk.lines[1], "Do you wish to enter Anskram Keep?");
    CHECK_EQ(walk.foodSpent, 1);
    CHECK_EQ(walk.daysSpent, doctest::Approx(1.0f));
}

TEST_CASE("MM9 region walk needs days on the road and two top-level areas")
{
    const std::vector<OpenYAMM::Game::MapStatsEntry> mapEntries = {
        mm9Map(9004, "sturmford", "Sturmford", 0),
        mm9Map(9006, "drangheim", "Drangheim", 0),
        mm9Map(9036, "anskramkeep", "Anskram Keep", 9004),
    };
    CHECK(OpenYAMM::Game::mm9RegionWalk(2, &mapEntries, "sturmford.blv", "DRANGHEIM.BLV"));
    CHECK_FALSE(OpenYAMM::Game::mm9RegionWalk(0, &mapEntries, "sturmford.blv", "drangheim.blv"));
    CHECK_FALSE(OpenYAMM::Game::mm9RegionWalk(1, &mapEntries, "sturmford.blv", "anskramkeep.blv"));
    CHECK_FALSE(OpenYAMM::Game::mm9RegionWalk(2, &mapEntries, "sturmford.blv", "missing.blv"));
    CHECK_FALSE(OpenYAMM::Game::mm9RegionWalk(2, nullptr, "sturmford.blv", "drangheim.blv"));
}
