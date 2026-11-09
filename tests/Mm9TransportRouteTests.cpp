#include "doctest/doctest.h"

#include "game/maps/MapRegistry.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/mm9/Mm9RudeDialogue.h"
#include "game/mm9/Mm9TransportRoute.h"
#include "game/party/Party.h"
#include "game/ui/GameplayUiController.h"
#include "tests/PartySpellTestHarness.h"

#include <string>
#include <vector>

namespace
{
std::string rudeRow(uint32_t rudeId = 18, int requiredRawKey = 0, int forbiddenRawKey = 0)
{
    std::vector<std::string> columns(30, "0");
    columns[0] = std::to_string(rudeId);
    columns[1] = std::to_string(rudeId);
    columns[2] = "1";
    columns[3] = "Yes please.";
    columns[4] = "Great!";
    columns[5] = "-5";
    columns[6] = std::to_string(requiredRawKey);
    columns[20] = std::to_string(forbiddenRawKey);
    std::string result;
    for (size_t index = 0; index < columns.size(); ++index)
    {
        if (index != 0)
        {
            result += ',';
        }
        result += columns[index];
    }
    return result + '\n';
}

TEST_CASE("MM9 transport service keeps NPC 209 source quest gate")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC209.rude", rudeRow(209, 73)));
    OpenYAMM::Game::Party party;

    CHECK(rudeTable.visibleRows(209, 209, party).empty());
    party.setQuestBit(90073, true);
    const std::vector<const OpenYAMM::Game::Mm9RudeRow *> visibleRows =
        rudeTable.visibleRows(209, 209, party);
    REQUIRE_EQ(visibleRows.size(), 1);
    CHECK_EQ(visibleRows[0]->next, -5);
}

std::vector<std::string> header()
{
    return {
        "CanonicalId", "DockNpcId", "ShopId", "DockName", "ServiceClassification",
        "SourceRudeRowIndex", "SourceLine", "DestinationName", "DestinationMap", "DestinationMapFile",
        "DestinationStartPoint", "ArrivalX", "ArrivalY", "ArrivalZ", "FacingDegrees", "FacingYawUnits",
        "MovePlayerToFloor", "AvailableWeekday", "SourceDayIndex", "TravelDays", "BasePrice",
        "PriceMultiplier", "RequiredRawKeys", "ForbiddenRawKeys", "RouteOrder", "SourceShop", "SourceRude",
        "ScheduleSource", "ExecutableRva", "ReviewState", "Provenance",
    };
}

std::vector<std::string> row()
{
    return {
        "mm9:transport/18/monday", "18", "18", "Sea's Fang", "dock", "0", "1", "Sturmford",
        "world.mm9.map.sturmford", "sturmford.odm", "StartPoint0", "100", "200", "300", "90", "512",
        "1", "Monday", "2", "2", "20", "3", "73", "", "0", "MMIXSHOPS.txt", "NPC18.rude",
        "BOOK AND SCROLL TEXT.csv", "0x1002a260[2]", "executable_backed",
        "MMIXSHOPS+RUDE+BoatSchedule+cshell.dll",
    };
}

OpenYAMM::Game::MapRegistry mapRegistry()
{
    OpenYAMM::Game::MapStatsEntry target = {};
    target.id = 1;
    target.worldId = "mm9";
    target.canonicalId = "world.mm9.map.sturmford";
    target.fileName = "sturmford.odm";
    OpenYAMM::Game::MapRegistry result;
    result.initialize({target});
    return result;
}
}

TEST_CASE("MM9 transport route table validates RUDE ownership and weekday lookup")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC18.rude", rudeRow()));
    OpenYAMM::Game::Mm9TransportRouteTable table;
    REQUIRE(table.loadFromRows({header(), row()}, mapRegistry(), rudeTable));
    CHECK(table.errors().empty());

    const OpenYAMM::Game::Mm9TransportRoute *pRoute = table.findForServiceDay(18, 2);
    REQUIRE(pRoute != nullptr);
    CHECK_EQ(pRoute->travelDays, 2);
    CHECK_EQ(pRoute->basePrice, 20);
    CHECK_EQ(pRoute->priceMultiplier, doctest::Approx(3.0f));
    CHECK(table.findForServiceDay(18, 3) == nullptr);
    CHECK_EQ(table.forService(18).size(), 1);
}

TEST_CASE("MM9 transport route conditions use mounted raw-key QBits")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC18.rude", rudeRow()));
    OpenYAMM::Game::Mm9TransportRouteTable table;
    REQUIRE(table.loadFromRows({header(), row()}, mapRegistry(), rudeTable));
    const OpenYAMM::Game::Mm9TransportRoute *pRoute = table.findForServiceDay(18, 2);
    REQUIRE(pRoute != nullptr);
    OpenYAMM::Game::Party party;

    CHECK_FALSE(OpenYAMM::Game::mm9TransportRouteConditionsSatisfied(*pRoute, party));
    party.setQuestBit(90073, true);
    CHECK(OpenYAMM::Game::mm9TransportRouteConditionsSatisfied(*pRoute, party));
    // The calendar's week starts on Monday (day 0), MM9's schedule order on Saturday: Monday is its day 2.
    CHECK_EQ(OpenYAMM::Game::mm9TransportDayIndex(0.0f), 2);
    CHECK_EQ(OpenYAMM::Game::mm9TransportDayIndex(2.0f * 24.0f * 60.0f), 4);
    CHECK_EQ(OpenYAMM::Game::mm9TransportDayIndex(5.0f * 24.0f * 60.0f), 0);
    CHECK_EQ(OpenYAMM::Game::mm9TransportWeekday(*pRoute), 0);
}

TEST_CASE("MM9 dock schedule lists the week's boats the party may take")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC18.rude", rudeRow()));
    std::vector<std::string> saturday = row();
    saturday[0] = "mm9:transport/18/saturday";
    saturday[17] = "Saturday";
    saturday[18] = "0";
    saturday[19] = "4";
    saturday[22] = "";
    OpenYAMM::Game::Mm9TransportRouteTable table;
    REQUIRE(table.loadFromRows({header(), row(), saturday}, mapRegistry(), rudeTable));
    OpenYAMM::Game::Party party;

    // Monday's boat needs raw key 73; Saturday's sails for anyone.
    OpenYAMM::Game::TransportSchedule schedule =
        OpenYAMM::Game::buildMm9TransportSchedule(table, 18, &party, nullptr);
    REQUIRE_EQ(schedule.routes.size(), 1);
    CHECK_EQ(schedule.routes[0].routeIndex, 0);
    CHECK(schedule.routes[0].daysAvailable[5]);
    CHECK_FALSE(schedule.routes[0].daysAvailable[0]);
    CHECK_EQ(schedule.routes[0].travelDays, 4);
    CHECK_GT(schedule.fare, 0);

    party.setQuestBit(90073, true);
    schedule = OpenYAMM::Game::buildMm9TransportSchedule(table, 18, &party, nullptr);
    CHECK_EQ(schedule.routes.size(), 2);
    CHECK(OpenYAMM::Game::buildMm9TransportSchedule(table, 60, &party, nullptr).routes.empty());
}

TEST_CASE("MM9 transport route table rejects duplicate service weekday ownership")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC18.rude", rudeRow()));
    std::vector<std::string> duplicate = row();
    duplicate[0] = "mm9:transport/18/monday-duplicate";
    OpenYAMM::Game::Mm9TransportRouteTable table;

    CHECK_FALSE(table.loadFromRows({header(), row(), duplicate}, mapRegistry(), rudeTable));
    REQUIRE_EQ(table.errors().size(), 1);
    CHECK(table.errors().front().find("duplicate service weekday ownership") != std::string::npos);
}

TEST_CASE("MM9 RUDE transport route charges advances time and queues an exact arrival")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC18.rude", rudeRow()));
    OpenYAMM::Game::Mm9TransportRouteTable routeTable;
    REQUIRE(routeTable.loadFromRows({header(), row()}, mapRegistry(), rudeTable));
    OpenYAMM::Game::Party party;
    party.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    party.setQuestBit(90073, true);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime;
    worldRuntime.bindParty(&party);
    // Day 0 is a Monday, the route's weekday; the party boards at 15:30.
    worldRuntime.advanceGameMinutes(15.5f * 60.0f);
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    worldRuntime.bindEventRuntimeState(&eventRuntimeState);
    OpenYAMM::Game::GameplayUiController uiController;
    OpenYAMM::Game::EventDialogContent dialog = {};
    size_t selectionIndex = 0;
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pWorldRuntime = &worldRuntime,
        .pMm9RudeDialogueTable = &rudeTable,
        .pMm9TransportRouteTable = &routeTable,
    };
    const OpenYAMM::Game::GameplayDialogController controller;
    controller.openMm9RudeDialogue(context, 18);
    REQUIRE_EQ(dialog.actions.size(), 1);

    controller.executeActiveDialogAction(context);
    // Today's boat, the Schedule, Back.
    REQUIRE_EQ(dialog.actions.size(), 3);
    CHECK(dialog.actions[0].kind == OpenYAMM::Game::EventDialogActionKind::Mm9RudeTransportRoute);
    CHECK(dialog.actions[1].kind == OpenYAMM::Game::EventDialogActionKind::Mm9RudeTransportSchedule);
    const int goldBefore = party.gold();

    const OpenYAMM::Game::GameplayDialogController::Result result =
        controller.executeActiveDialogAction(context);
    CHECK(result.shouldCloseActiveDialog);
    CHECK(party.gold() < goldBefore);
    // Two days at sea: Wednesday at 6:00.
    CHECK_EQ(worldRuntime.gameMinutes(), doctest::Approx(2.0f * 24.0f * 60.0f + 6.0f * 60.0f));
    REQUIRE(eventRuntimeState.pendingMapMove.has_value());
    CHECK(eventRuntimeState.pendingMapMove->mapName == "sturmford.odm");
    CHECK_EQ(eventRuntimeState.pendingMapMove->x, 100);
    CHECK_EQ(eventRuntimeState.pendingMapMove->y, 200);
    CHECK_EQ(eventRuntimeState.pendingMapMove->z, 300);
    REQUIRE(eventRuntimeState.lastMapTransitionRequested.has_value());
    CHECK(eventRuntimeState.lastMapTransitionRequested->sourceKind == "mm9_boat_route");
    CHECK_EQ(eventRuntimeState.lastMapTransitionRequested->travelDays, 2);
}

TEST_CASE("MM9 RUDE transport rejects unavailable and unaffordable routes without mutation")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC18.rude", rudeRow()));
    OpenYAMM::Game::Mm9TransportRouteTable routeTable;
    REQUIRE(routeTable.loadFromRows({header(), row()}, mapRegistry(), rudeTable));
    OpenYAMM::Game::Party party;
    party.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    party.setQuestBit(90073, true);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime;
    worldRuntime.bindParty(&party);
    // A Tuesday: no boat today, the week's Monday boat in the Schedule.
    worldRuntime.advanceGameMinutes(24.0f * 60.0f);
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    worldRuntime.bindEventRuntimeState(&eventRuntimeState);
    OpenYAMM::Game::GameplayUiController uiController;
    OpenYAMM::Game::EventDialogContent dialog = {};
    size_t selectionIndex = 0;
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pWorldRuntime = &worldRuntime,
        .pMm9RudeDialogueTable = &rudeTable,
        .pMm9TransportRouteTable = &routeTable,
    };
    const OpenYAMM::Game::GameplayDialogController controller;
    controller.openMm9RudeDialogue(context, 18);
    controller.executeActiveDialogAction(context);
    REQUIRE_EQ(dialog.actions.size(), 2);
    CHECK(dialog.actions[0].kind == OpenYAMM::Game::EventDialogActionKind::Mm9RudeTransportSchedule);
    CHECK(dialog.actions[1].kind == OpenYAMM::Game::EventDialogActionKind::Mm9RudeTransportBack);
    CHECK_FALSE(eventRuntimeState.pendingMapMove.has_value());

    // The next Monday.
    worldRuntime.advanceGameMinutes(6.0f * 24.0f * 60.0f);
    selectionIndex = 1;
    controller.executeActiveDialogAction(context);
    REQUIRE_EQ(dialog.actions.size(), 1);
    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    REQUIRE_EQ(dialog.actions.size(), 3);
    party.addGold(-party.gold());
    const float minutesBefore = worldRuntime.gameMinutes();
    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    CHECK_EQ(party.gold(), 0);
    CHECK_EQ(worldRuntime.gameMinutes(), minutesBefore);
    CHECK_FALSE(eventRuntimeState.pendingMapMove.has_value());
}

TEST_CASE("MM9 dock Schedule opens the popup and a later departure waits for its weekday")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC18.rude", rudeRow()));
    OpenYAMM::Game::Mm9TransportRouteTable routeTable;
    REQUIRE(routeTable.loadFromRows({header(), row()}, mapRegistry(), rudeTable));
    OpenYAMM::Game::Party party;
    party.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    party.setQuestBit(90073, true);
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime;
    worldRuntime.bindParty(&party);
    // A Saturday at 3:00: the Monday boat is two days away.
    worldRuntime.advanceGameMinutes(5.0f * 24.0f * 60.0f + 3.0f * 60.0f);
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    worldRuntime.bindEventRuntimeState(&eventRuntimeState);
    OpenYAMM::Game::GameplayUiController uiController;
    OpenYAMM::Game::EventDialogContent dialog = {};
    size_t selectionIndex = 0;
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pWorldRuntime = &worldRuntime,
        .pMm9RudeDialogueTable = &rudeTable,
        .pMm9TransportRouteTable = &routeTable,
    };
    const OpenYAMM::Game::GameplayDialogController controller;
    controller.openMm9RudeDialogue(context, 18);
    controller.executeActiveDialogAction(context);
    REQUIRE_EQ(dialog.actions.size(), 2);
    REQUIRE(dialog.actions[0].kind == OpenYAMM::Game::EventDialogActionKind::Mm9RudeTransportSchedule);
    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    CHECK(uiController.transportSchedule().active);
    CHECK_EQ(uiController.transportSchedule().mm9DockId, 18);

    // The popup's Travel: Monday's boat, waiting two days (two food), then two days at sea.
    OpenYAMM::Game::EventDialogAction departure = {};
    departure.kind = OpenYAMM::Game::EventDialogActionKind::Mm9RudeTransportRoute;
    departure.argument = "mm9:transport/18/monday";
    departure.secondaryId = 1;
    dialog.actions = {departure};
    selectionIndex = 0;
    const int foodBefore = party.food();
    const OpenYAMM::Game::GameplayDialogController::Result result = controller.executeActiveDialogAction(context);
    CHECK(result.shouldCloseActiveDialog);
    CHECK_EQ(party.food(), foodBefore - 2);
    // Saturday, two days' wait to Monday, two days at sea: Wednesday (day 9) at 6:00.
    CHECK_EQ(worldRuntime.gameMinutes(), doctest::Approx(9.0f * 24.0f * 60.0f + 6.0f * 60.0f));
    REQUIRE(eventRuntimeState.pendingMapMove.has_value());
    CHECK(eventRuntimeState.pendingMapMove->mapName == "sturmford.odm");

    // A departure for a weekday the route does not sail on is refused.
    eventRuntimeState.pendingMapMove.reset();
    controller.openMm9RudeDialogue(context, 18);
    departure.secondaryId = 3;
    dialog.actions = {departure};
    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    CHECK_FALSE(eventRuntimeState.pendingMapMove.has_value());
}
