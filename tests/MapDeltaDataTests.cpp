#include "doctest/doctest.h"

#include "game/maps/MapDeltaData.h"

TEST_CASE("indoor door texture deltas are normalized from face texture deltas")
{
    OpenYAMM::Game::IndoorMapData indoorMapData = {};
    indoorMapData.faces.resize(3);
    indoorMapData.faces[1].textureDeltaU = 17;
    indoorMapData.faces[1].textureDeltaV = -23;

    OpenYAMM::Game::MapDeltaData mapDeltaData = {};
    mapDeltaData.doors.push_back({});
    mapDeltaData.doors[0].faceIds = {1};
    mapDeltaData.doors[0].deltaUs = {111};
    mapDeltaData.doors[0].deltaVs = {222};

    OpenYAMM::Game::normalizeIndoorDoorTextureDeltas(mapDeltaData, indoorMapData);

    REQUIRE_EQ(mapDeltaData.doors.size(), 1u);
    REQUIRE_EQ(mapDeltaData.doors[0].deltaUs.size(), 1u);
    REQUIRE_EQ(mapDeltaData.doors[0].deltaVs.size(), 1u);
    CHECK_EQ(mapDeltaData.doors[0].deltaUs[0], 17);
    CHECK_EQ(mapDeltaData.doors[0].deltaVs[0], -23);
}
