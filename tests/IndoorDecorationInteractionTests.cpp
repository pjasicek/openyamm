#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/maps/SaveGame.h"

#include <algorithm>
#include <array>
#include <filesystem>
#include <set>

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

TEST_CASE("Ironfist Temple of Baa gold bags clear rewards and collision across save and reentry")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForGameplay(assets, "6t1.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    REQUIRE(loaded.indoorDecorationBillboardSet);
    const IndoorMapData &map = *loaded.indoorMapData;
    const DecorationBillboardSet &billboards = *loaded.indoorDecorationBillboardSet;
    Party party;
    party.seed(Party::createDefaultSeed());
    const auto primaryAttributes = [](const Character &member)
    {
        return std::array<uint32_t, 7>{member.might, member.intellect, member.personality, member.endurance,
            member.speed, member.accuracy, member.luck};
    };
    std::vector<std::array<uint32_t, 7>> attributes;
    for (const Character &member : party.members())
    {
        attributes.push_back(primaryAttributes(member));
    }
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map,
        data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(), data.getSpellTable(),
        data.getItemTable(), data.getChestTable(), party, loaded.indoorMapDeltaData, loaded.eventRuntimeState,
        loaded.localEventProgram, loaded.globalEventProgram, nullptr, nullptr, nullptr, nullptr, nullptr, &billboards);
    EventRuntimeState *pState = scene.eventRuntimeState();
    REQUIRE(pState != nullptr);
    std::vector<size_t> bagIndices;
    const auto hasCollider = [&](size_t entityIndex)
    {
        const std::vector<IndoorCylinderCollision> colliders = scene.worldRuntime().decorationMovementColliders();
        return std::any_of(colliders.begin(), colliders.end(),
            [&](const IndoorCylinderCollision &collider) { return collider.sourceIndex == entityIndex; });
    };

    size_t decorVarIndex = 0;
    std::set<int> rewards;
    for (size_t entityIndex = 0; entityIndex < map.entities.size(); ++entityIndex)
    {
        const IndoorEntity &entity = map.entities[entityIndex];
        if (entity.scriptEventId() != 0)
        {
            continue;
        }
        const DecorationEntry *pDecoration =
            billboards.decorationTable.resolveMapDecoration(entity.decorationListId, entity.name).pEntry;
        if (pDecoration == nullptr)
        {
            continue;
        }
        const std::optional<InteractiveDecorationBindingSpec> spec =
            resolveInteractiveDecorationBindingSpec(*pDecoration, entity.name);
        if (!spec || decorVarIndex >= pState->decorVars.size())
        {
            continue;
        }
        const size_t index = decorVarIndex++;
        if (entity.name != "bag_A")
        {
            continue;
        }
        CAPTURE(entityIndex);
        REQUIRE_EQ(spec->family, InteractiveDecorationFamily::GoldBag);
        // Exercise every state written by the previous item-bag binding.
        pState->decorVars[index] = static_cast<uint8_t>(bagIndices.size() % 5);
        const std::optional<uint16_t> eventId = interactiveDecorationEventId(
            pState->decorVars[index], spec->baseEventId, spec->eventCount, spec->hideWhenCleared, spec->fixedEvent);
        REQUIRE(eventId.has_value());
        CHECK(hasCollider(entityIndex));
        EventRuntimeState::ActiveDecorationContext context = {};
        context.decorVarIndex = static_cast<uint8_t>(index);
        context.baseEventId = spec->baseEventId;
        context.currentEventId = *eventId;
        context.eventCount = spec->eventCount;
        context.hideWhenCleared = spec->hideWhenCleared;
        const int before = scene.party().gold();
        REQUIRE(scene.activateEvent(*eventId, "entity", entityIndex, context));
        const int reward = scene.party().gold() - before;
        CHECK_GE(reward, 51);
        CHECK_LE(reward, 250);
        rewards.insert(reward);
        CHECK(pState->grantedItems.empty());
        CHECK_FALSE(hasCollider(entityIndex));
        CHECK_FALSE(interactiveDecorationEventId(
            pState->decorVars[index], spec->baseEventId, spec->eventCount, spec->hideWhenCleared, spec->fixedEvent));
        bagIndices.push_back(entityIndex);
    }
    REQUIRE_EQ(bagIndices.size(), 63u);
    CHECK_GT(rewards.size(), 1u);
    for (size_t index = 0; index < scene.party().members().size(); ++index)
    {
        CHECK_EQ(primaryAttributes(scene.party().members()[index]), attributes[index]);
    }

    const std::vector<IndoorCylinderCollision> remaining = scene.worldRuntime().decorationMovementColliders();
    REQUIRE_FALSE(remaining.empty());
    const size_t otherDecoration = remaining.front().sourceIndex;
    CHECK_EQ(std::count(bagIndices.begin(), bagIndices.end(), otherDecoration), 0);
    const uint32_t overrideKey = map.entities[otherDecoration].spriteOverrideKey(otherDecoration);
    pState->spriteOverrides[overrideKey].hidden = true;
    CHECK_FALSE(hasCollider(otherDecoration));
    pState->spriteOverrides.erase(overrideKey);
    CHECK(hasCollider(otherDecoration));

    GameSaveData save;
    save.currentSceneKind = SceneKind::Indoor;
    save.mapFileName = loaded.map.fileName;
    save.hasIndoorSceneState = true;
    save.indoorScene = scene.snapshot();
    save.indoorSceneStates[save.mapFileName] = save.indoorScene;
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_baa_gold_bags.oysav";
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error.c_str());
    const std::optional<GameSaveData> restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error.c_str());
    scene.restoreSnapshot(restored->indoorSceneStates.at(save.mapFileName));
    scene.applyMapReentryReset();
    pState = scene.eventRuntimeState();
    REQUIRE(pState != nullptr);
    const std::vector<bool> hidden = hiddenIndoorDecorationEntities(map.entities, billboards.decorationTable, *pState);
    for (size_t entityIndex : bagIndices)
    {
        CHECK(hidden[entityIndex]);
        CHECK_FALSE(hasCollider(entityIndex));
    }
}
