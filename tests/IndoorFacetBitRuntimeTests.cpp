#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/scene/IndoorSceneRuntime.h"

#include <filesystem>
#include <vector>

using namespace OpenYAMM::Game;

TEST_CASE("indoor SetFacetBit takes a cog group, or one face by a face reference, never the face of that index")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm8"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "d24.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    IndoorMapData map = *loaded.indoorMapData;
    map.spawns.clear();
    std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
    REQUIRE(delta);
    delta->actors.clear();

    // Balthazar Lair's lever event 11 hides cog 1, the water floor face 1030; face 1 is a wall without a cog.
    constexpr size_t CogOneFace = 1030;
    constexpr size_t WallFace = 1;
    REQUIRE_GT(map.faces.size(), CogOneFace);
    REQUIRE_EQ(map.faces[CogOneFace].cogNumber, 1u);
    REQUIRE_EQ(map.faces[WallFace].cogNumber, 0u);

    Party party;
    party.setItemTable(&data.getItemTable());
    GameplayActorService actorService;
    actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, delta, loaded.eventRuntimeState,
        loaded.localEventProgram, std::nullopt, &actorService, nullptr);
    IndoorWorldRuntime &world = scene.worldRuntime();
    const uint32_t invisible = faceAttributeBit(FaceAttribute::Invisible);
    const auto hidden = [&world, invisible](size_t faceIndex)
    {
        return (world.mapDeltaData()->faceAttributes[faceIndex] & invisible) != 0;
    };

    CHECK(world.setFacetBit(1, invisible, true));
    CHECK(hidden(CogOneFace));
    CHECK_FALSE(hidden(WallFace));

    // A face reference (MMerge's MM6 maps) names the face of that index and no cog group.
    CHECK(world.setFacetBit(1, invisible, false));
    CHECK(world.setFacetBit(EventRuntime::indoorFaceReferenceKey(WallFace), invisible, true));
    CHECK(hidden(WallFace));
    CHECK_FALSE(hidden(CogOneFace));
    CHECK_FALSE(world.setFacetBit(EventRuntime::indoorFaceReferenceKey(uint32_t(map.faces.size())), invisible, true));
}

TEST_CASE("an MM6 map's SetFacetBit face reference changes that one face when its event runs")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "6d06.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    IndoorMapData map = *loaded.indoorMapData;
    map.spawns.clear();
    std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
    REQUIRE(delta);
    delta->actors.clear();

    Party party;
    party.setItemTable(&data.getItemTable());
    GameplayActorService actorService;
    actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, delta, loaded.eventRuntimeState,
        loaded.localEventProgram, std::nullopt, &actorService, nullptr);
    IndoorWorldRuntime &world = scene.worldRuntime();
    const uint32_t untouchable = faceAttributeBit(FaceAttribute::Untouchable);
    const std::vector<uint32_t> before = world.mapDeltaData()->faceAttributes;
    REQUIRE_GT(before.size(), 2667u);
    REQUIRE_EQ(before[2667] & untouchable, 0u);

    // Lever event 12 runs evt.SetFacetBit(-2667, FacetBits.Untouchable, 1): face 2667 alone becomes passable.
    REQUIRE(scene.activateEvent(12, "face", 0));
    const std::vector<uint32_t> &after = world.mapDeltaData()->faceAttributes;
    REQUIRE_EQ(after.size(), before.size());
    CHECK_NE(after[2667] & untouchable, 0u);

    for (size_t faceIndex = 0; faceIndex < after.size(); ++faceIndex)
    {
        if (faceIndex != 2667 && after[faceIndex] != before[faceIndex])
        {
            FAIL_CHECK("face " << faceIndex << " changed");
        }
    }

    // Pulled again, the lever clears it.
    REQUIRE(scene.activateEvent(12, "face", 0));
    CHECK_EQ(world.mapDeltaData()->faceAttributes[2667] & untouchable, 0u);
}

TEST_CASE("an indoor map state restored from a save without sprite object keys gets one key per object")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm8"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "d24.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    IndoorMapData map = *loaded.indoorMapData;
    map.spawns.clear();
    std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
    REQUIRE(delta);
    delta->actors.clear();

    Party party;
    party.setItemTable(&data.getItemTable());
    GameplayActorService actorService;
    actorService.bindTables(&data.getMonsterTable(), &data.getSpellTable());
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, delta, loaded.eventRuntimeState,
        loaded.localEventProgram, std::nullopt, &actorService, nullptr);

    // Saves older than version 171 load their objects with key 0; unkeyed, ground items shared one model and were
    // refitted to the floor every frame (MM9's Sturmford at 8 FPS).
    IndoorSceneRuntime::Snapshot saved = scene.snapshot();
    REQUIRE(saved.mapDeltaData);
    saved.mapDeltaData->spriteObjects.resize(3);
    for (MapDeltaSpriteObject &spriteObject : saved.mapDeltaData->spriteObjects)
    {
        spriteObject.objectKey = 0;
    }
    scene.restoreSnapshot(saved);

    const std::vector<MapDeltaSpriteObject> &objects = scene.worldRuntime().mapDeltaData()->spriteObjects;
    REQUIRE_EQ(objects.size(), 3u);
    CHECK_NE(objects[0].objectKey, 0u);
    CHECK_NE(objects[0].objectKey, objects[1].objectKey);
    CHECK_NE(objects[1].objectKey, objects[2].objectKey);
    CHECK_NE(objects[0].objectKey, objects[2].objectKey);
}
