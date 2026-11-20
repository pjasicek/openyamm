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

TEST_CASE("a map refill keeps the scene actors that do not respawn (MM9's ShouldRepopulate 0) as they were left")
{
    using OpenYAMM::Game::MapDeltaActor;
    OpenYAMM::Game::MapDeltaData saved = {};
    OpenYAMM::Game::MapDeltaData refilled = {};

    for (int index = 0; index < 3; ++index)
    {
        MapDeltaActor actor = {};
        actor.name = index == 2 ? "Count" : "Guard";
        actor.monsterInfoId = int16_t(9100 + index);
        actor.hp = 50;
        actor.respawnsOnRefill = index == 0;
        refilled.actors.push_back(actor);
        actor.hp = 0;                       // the party killed every one
        actor.x = 640;
        saved.actors.push_back(actor);
    }

    saved.actors[1].monsterInfoId = 9300;   // not the same placement any more: placed anew
    CHECK_EQ(OpenYAMM::Game::keepActorsThroughRefill(saved, refilled), 1u);
    CHECK_EQ(refilled.actors[0].hp, 50);    // respawns
    CHECK_EQ(refilled.actors[1].hp, 50);
    CHECK_EQ(refilled.actors[2].hp, 0);     // stays dead where it fell
    CHECK_EQ(refilled.actors[2].x, 640);
    CHECK_FALSE(refilled.actors[2].respawnsOnRefill);
}

TEST_CASE("sprite object keys stay with their objects when an earlier object is taken")
{
    using OpenYAMM::Game::MapDeltaData;
    using OpenYAMM::Game::MapDeltaSpriteObject;

    MapDeltaData data = {};
    data.spriteObjects.resize(3);           // a map's authored objects, or a save from before keys
    data.spriteObjects[1].objectKey = 7;
    OpenYAMM::Game::assignSpriteObjectKeys(data);
    CHECK_EQ(data.spriteObjects[0].objectKey, 8u);
    CHECK_EQ(data.spriteObjects[1].objectKey, 7u);
    CHECK_EQ(data.spriteObjects[2].objectKey, 9u);

    data.spriteObjects.erase(data.spriteObjects.begin());   // the party takes the first
    CHECK_EQ(data.spriteObjects[0].objectKey, 7u);
    CHECK_EQ(data.spriteObjects[1].objectKey, 9u);

    OpenYAMM::Game::appendSpriteObject(data, MapDeltaSpriteObject{});
    CHECK_EQ(data.spriteObjects[2].objectKey, 10u);
}
