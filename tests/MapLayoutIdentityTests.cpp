#include "game/maps/MapLayoutIdentity.h"
#include "game/maps/SaveGame.h"

#include <doctest/doctest.h>

#include <chrono>
#include <filesystem>
#include <optional>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
IndoorMapData smallIndoorMap()
{
    IndoorMapData map;
    map.vertices = {{0, 0, 0}, {512, 0, 0}, {512, 512, 0}, {0, 512, 0}, {0, 0, 256}, {512, 0, 256}};
    IndoorFace floor;
    floor.vertexIndices = {0, 1, 2, 3};
    floor.textureName = "floor01";
    IndoorFace wall;
    wall.vertexIndices = {0, 1, 5, 4};
    wall.cogNumber = 7;
    wall.textureName = "wall01";
    map.faces = {floor, wall};
    map.sectors.resize(2);
    IndoorEntity torch;
    torch.decorationListId = 12;
    torch.x = 100;
    torch.y = 100;
    map.entities = {torch};
    IndoorLight light;
    light.radius = 256;
    map.lights = {light};
    return map;
}

MapDeltaData smallIndoorState()
{
    MapDeltaData state;
    MapDeltaDoor gate;
    gate.doorId = 3;
    gate.directionZ = 65536;
    gate.moveLength = 256;
    gate.vertexIds = {4, 5};
    gate.faceIds = {1};
    state.doorSlotCount = 1;
    state.doors = {gate};
    state.chests.resize(2);
    state.actors.resize(4);
    return state;
}

OutdoorMapData smallOutdoorMap()
{
    OutdoorMapData map;
    map.heightMap.assign(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight, 10);
    OutdoorBModel house;
    house.vertices = {{0, 0, 0}, {256, 0, 0}, {256, 256, 0}, {0, 256, 256}};
    OutdoorBModelFace face;
    face.vertexIndices = {0, 1, 2, 3};
    face.textureName = "roof01";
    house.faces = {face};
    map.bmodels = {house};
    return map;
}

std::optional<GameSaveData> roundTrip(const GameSaveData &save, std::string &error)
{
    const uint64_t ticks = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / ("openyamm_map_layout_" + std::to_string(ticks) + ".oysav");
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error);
    std::optional<GameSaveData> restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    return restored;
}
}

TEST_CASE("an indoor map's layout identity follows its geometry and doors, not its textures or lights")
{
    const IndoorMapData map = smallIndoorMap();
    const std::optional<MapDeltaData> state = smallIndoorState();
    const uint64_t identity = computeIndoorMapLayoutIdentity(map, state);
    CHECK_NE(identity, 0u);
    CHECK_EQ(computeIndoorMapLayoutIdentity(smallIndoorMap(), smallIndoorState()), identity);

    SUBCASE("unchanged by texture names, lights and actor stats")
    {
        IndoorMapData retextured = map;
        retextured.faces[0].textureName = "floor02";
        retextured.lights[0].radius = 1024;
        std::optional<MapDeltaData> restatted = state;
        restatted->actors[0].hp = 999;
        restatted->actors[0].monsterId = 40;
        CHECK_EQ(computeIndoorMapLayoutIdentity(retextured, restatted), identity);
    }
    SUBCASE("a moved vertex")
    {
        IndoorMapData moved = map;
        moved.vertices[2].x += 1;
        CHECK_NE(computeIndoorMapLayoutIdentity(moved, state), identity);
    }
    SUBCASE("a vertex more (the reconverted Anskram Keep)")
    {
        IndoorMapData grown = map;
        grown.vertices.push_back({0, 512, 256});
        CHECK_NE(computeIndoorMapLayoutIdentity(grown, state), identity);
    }
    SUBCASE("a face's vertex list or event")
    {
        IndoorMapData rewired = map;
        rewired.faces[1].vertexIndices = {1, 2, 5, 4};
        CHECK_NE(computeIndoorMapLayoutIdentity(rewired, state), identity);
        IndoorMapData reevented = map;
        reevented.faces[1].cogNumber = 8;
        CHECK_NE(computeIndoorMapLayoutIdentity(reevented, state), identity);
    }
    SUBCASE("a door's vertices, travel or count")
    {
        std::optional<MapDeltaData> door = state;
        door->doors[0].vertexIds = {4};
        CHECK_NE(computeIndoorMapLayoutIdentity(map, door), identity);
        door = state;
        door->doors[0].moveLength = 512;
        CHECK_NE(computeIndoorMapLayoutIdentity(map, door), identity);
        door = state;
        door->doors.push_back(door->doors[0]);
        CHECK_NE(computeIndoorMapLayoutIdentity(map, door), identity);
    }
    SUBCASE("the chest, actor and decoration counts")
    {
        std::optional<MapDeltaData> chests = state;
        chests->chests.resize(3);
        CHECK_NE(computeIndoorMapLayoutIdentity(map, chests), identity);
        std::optional<MapDeltaData> actors = state;
        actors->actors.resize(5);
        CHECK_NE(computeIndoorMapLayoutIdentity(map, actors), identity);
        IndoorMapData decorated = map;
        decorated.entities.push_back(decorated.entities[0]);
        CHECK_NE(computeIndoorMapLayoutIdentity(decorated, state), identity);
    }
}

TEST_CASE("an outdoor map's layout identity follows its models, not its terrain heights")
{
    const OutdoorMapData map = smallOutdoorMap();
    const std::optional<MapDeltaData> state = MapDeltaData{};
    const uint64_t identity = computeOutdoorMapLayoutIdentity(map, state);
    CHECK_NE(identity, 0u);
    CHECK_NE(identity, computeIndoorMapLayoutIdentity(IndoorMapData{}, state));

    OutdoorMapData reshaped = map;
    reshaped.heightMap[100] = 50;
    reshaped.bmodels[0].faces[0].textureName = "roof02";
    CHECK_EQ(computeOutdoorMapLayoutIdentity(reshaped, state), identity);

    OutdoorMapData rebuilt = map;
    rebuilt.bmodels[0].vertices[3].z = 300;
    CHECK_NE(computeOutdoorMapLayoutIdentity(rebuilt, state), identity);

    std::optional<MapDeltaData> chests = state;
    chests->chests.resize(1);
    CHECK_NE(computeOutdoorMapLayoutIdentity(map, chests), identity);
}

TEST_CASE("a saved map state is kept only on its own layout; older saves keep only MM6-MM8 maps")
{
    CHECK_EQ(judgeSavedMapState(42, 42, "mm9"), SavedMapStateVerdict::Keep);
    CHECK_EQ(judgeSavedMapState(42, 43, "mm8"), SavedMapStateVerdict::ResetChanged);
    CHECK_EQ(judgeSavedMapState(0, 43, "mm6"), SavedMapStateVerdict::Keep);
    CHECK_EQ(judgeSavedMapState(0, 43, " MM7 "), SavedMapStateVerdict::Keep);
    CHECK_EQ(judgeSavedMapState(0, 43, "mm8"), SavedMapStateVerdict::Keep);
    CHECK_EQ(judgeSavedMapState(0, 43, "mm9"), SavedMapStateVerdict::ResetUnknown);
    CHECK_EQ(judgeSavedMapState(0, 43, "hesper"), SavedMapStateVerdict::ResetUnknown);
}

TEST_CASE("a save keeps each map state's layout identity")
{
    GameSaveData save;
    save.currentSceneKind = SceneKind::Indoor;
    save.mapFileName = "d01.blv";
    save.hasIndoorSceneState = true;
    save.indoorScene.mapLayoutIdentity = 0x1234;
    save.indoorSceneStates["d01.blv"].mapLayoutIdentity = 0x1234;
    save.indoorSceneStates["d02.blv"].mapLayoutIdentity = 0x5678;
    save.outdoorWorldStates["out01.odm"].mapLayoutIdentity = 0x9abc;
    std::string error;
    const std::optional<GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    CHECK_EQ(restored->indoorScene.mapLayoutIdentity, 0x1234u);
    CHECK_EQ(restored->indoorSceneStates.at("d01.blv").mapLayoutIdentity, 0x1234u);
    CHECK_EQ(restored->indoorSceneStates.at("d02.blv").mapLayoutIdentity, 0x5678u);
    CHECK_EQ(restored->outdoorWorldStates.at("out01.odm").mapLayoutIdentity, 0x9abcu);
}

TEST_CASE("a save keeps the indoor party's swim memory, so a load in the water swims on as before")
{
    // Found by the MM9 playthrough's save-and-load run (2026-11-08): a party wading on the Dark Passageway's sunken
    // bridge had never been under water; the load guessed it had, so its jump held it at the surface under the rail.
    GameSaveData save;
    save.currentSceneKind = SceneKind::Indoor;
    save.mapFileName = "d01.blv";
    save.hasIndoorSceneState = true;
    save.indoorScene.partyRuntime.swimMemory = IndoorSwimMemory{.wasSubmerged = false, .surfaceJump = true};
    std::string error;
    const std::optional<GameSaveData> restored = roundTrip(save, error);
    REQUIRE_MESSAGE(restored.has_value(), error);
    REQUIRE(restored->indoorScene.partyRuntime.swimMemory.has_value());
    CHECK_FALSE(restored->indoorScene.partyRuntime.swimMemory->wasSubmerged);
    CHECK(restored->indoorScene.partyRuntime.swimMemory->surfaceJump);
}
