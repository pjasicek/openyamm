#include "game/app/GameSession.h"
#include "game/data/GameDataLoader.h"
#include "game/data/GameDataRepository.h"

#include <doctest/doctest.h>

using namespace OpenYAMM::Game;

// GameSession's half of devdocs/SAVED_MAP_STATE_IDENTITY.md; the identity itself is in MapLayoutIdentityTests.cpp.
TEST_CASE("a map's state is stamped with its layout, and resetting it keeps the party")
{
    GameDataLoader loader;
    GameDataRepository data;
    data.bind(loader);
    GameSession session;
    session.bindDataRepository(&data);
    Party party;
    party.addGold(1234);
    party.setQuestBit(10001, true);

    session.setCurrentMapLayoutIdentity(11);
    session.captureOutdoorRuntimeState(
        "out01.odm", party, OutdoorPartyRuntime::Snapshot{}, OutdoorWorldRuntime::Snapshot{}, 0.5f, 0.1f);
    session.setCurrentMapLayoutIdentity(22);
    IndoorSceneRuntime::Snapshot indoor;
    indoor.mapDeltaData = MapDeltaData{};
    indoor.mapDeltaData->doors.resize(2);
    session.captureIndoorRuntimeState("d01.blv", party, indoor);
    session.setCameraAngles(1.0f, 0.2f);

    REQUIRE(session.outdoorWorldStates().contains("out01.odm"));
    REQUIRE(session.indoorSceneStates().contains("d01.blv"));
    CHECK_EQ(session.outdoorWorldStates().at("out01.odm").mapLayoutIdentity, 11u);
    CHECK_EQ(session.indoorSceneStates().at("d01.blv").mapLayoutIdentity, 22u);

    SUBCASE("a map the party is not in")
    {
        session.discardMapState("out01.odm", false);
        CHECK_FALSE(session.outdoorWorldStates().contains("out01.odm"));
        CHECK(session.indoorSceneStates().contains("d01.blv"));
        CHECK(session.currentIndoorSceneState().has_value());
        CHECK(session.outdoorPartyState().has_value());
        CHECK(session.cameraAnglesValid());
    }
    SUBCASE("the map a loaded save stands in: its place and camera go too")
    {
        session.discardMapState("d01.blv", true);
        CHECK_FALSE(session.indoorSceneStates().contains("d01.blv"));
        CHECK_FALSE(session.currentIndoorSceneState().has_value());
        CHECK(session.outdoorWorldStates().contains("out01.odm"));
        CHECK_FALSE(session.cameraAnglesValid());
    }

    REQUIRE(session.partyState().has_value());
    CHECK_EQ(session.partyState()->gold(), 1234);
    CHECK(session.partyState()->hasQuestBit(10001));
}
