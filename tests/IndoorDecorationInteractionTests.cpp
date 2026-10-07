#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/maps/SaveGame.h"

#include <algorithm>
#include <filesystem>

using namespace OpenYAMM::Game;

TEST_CASE("New Sorpigal temple braziers toggle and retain their light state across save and reentry")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForGameplay(assets, "6d02.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    REQUIRE(loaded.indoorDecorationBillboardSet);
    const IndoorMapData &map = *loaded.indoorMapData;
    const DecorationBillboardSet &billboards = *loaded.indoorDecorationBillboardSet;
    const auto brazier = std::find_if(billboards.billboards.begin(), billboards.billboards.end(),
        [](const DecorationBillboard &value) { return value.name == "brazir2f" && value.eventIdSecondary == 0; });
    REQUIRE(brazier != billboards.billboards.end());
    const size_t index = brazier->entityIndex;
    const uint32_t key = brazier->spriteOverrideKey();
    const DecorationEntry *lit = billboards.decorationTable.findByInternalName("brzier00");
    REQUIRE(lit != nullptr);
    const SpriteFrameEntry *frame = billboards.spriteFrameTable.getFrame(lit->spriteId, 0);
    REQUIRE(frame != nullptr);
    // No lit brazier is initially placed in this map; all six alternate animation frames must still be loaded.
    for (int animationFrame = 0; animationFrame < 6; ++animationFrame)
    {
        const std::string name = "brzier0" + std::to_string(animationFrame);
        CHECK(std::any_of(billboards.textures.begin(), billboards.textures.end(),
            [&](const OutdoorBitmapTexture &texture) { return texture.textureName == name && texture.paletteId == frame->paletteId; }));
    }

    Party party;
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, loaded.indoorMapDeltaData, loaded.eventRuntimeState,
        loaded.localEventProgram, std::nullopt, nullptr, nullptr, nullptr, nullptr, nullptr, &billboards);
    EventRuntimeState *state = scene.eventRuntimeState();
    REQUIRE(state != nullptr);
    const auto originalDecorVars = state->decorVars;
    IndoorLightingRuntime lighting;
    lighting.rebuildStaticCache(map, &billboards, state);
    IndoorLightingFrameInput input;
    input.pMapData = &map;
    input.pDecorationBillboardSet = &billboards;
    input.pEventRuntimeState = state;
    const auto hasBrazierLight = [&]()
    {
        const IndoorLightingFrame lights = lighting.buildFrame(input);
        return std::any_of(lights.lights.begin(), lights.lights.end(),
            [&](const IndoorRenderLight &light) { return light.kind == IndoorRenderLightKind::Decoration && light.stableId == key; });
    };
    CHECK_FALSE(hasBrazierLight());
    REQUIRE(scene.activateEvent(0, "entity", index));
    CHECK_EQ(state->spriteOverrides.at(key).textureName, "brzier00");
    CHECK_EQ(state->decorVars, originalDecorVars);
    CHECK(hasBrazierLight());

    GameSaveData save;
    save.currentSceneKind = SceneKind::Indoor;
    save.mapFileName = loaded.map.fileName;
    save.hasIndoorSceneState = true;
    save.indoorScene = scene.snapshot();
    save.indoorSceneStates[save.mapFileName] = save.indoorScene;
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_temple_brazier.oysav";
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error.c_str());
    const auto restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error.c_str());
    scene.restoreSnapshot(restored->indoorSceneStates.at(save.mapFileName));
    scene.applyMapReentryReset();
    state = scene.eventRuntimeState();
    input.pEventRuntimeState = state;
    REQUIRE(state != nullptr);
    lighting.rebuildStaticCache(map, &billboards, state);
    CHECK_EQ(state->spriteOverrides.at(key).textureName, "brzier00");
    CHECK(hasBrazierLight());
    const auto savedLights = state->indoorLightsEnabled;
    REQUIRE(scene.activateEvent(0, "entity", index));
    CHECK_EQ(state->spriteOverrides.at(key).textureName, "brazir2f");
    CHECK_FALSE(hasBrazierLight());
    for (const auto &[lightId, enabled] : savedLights)
    {
        CHECK(enabled);
        CHECK_FALSE(state->indoorLightsEnabled.at(lightId));
    }
    CHECK_EQ(state->decorVars, originalDecorVars);
}
