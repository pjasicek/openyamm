#include "doctest/doctest.h"

#include "game/events/EventRuntime.h"
#include "game/fx/WorldFxSystem.h"
#include "game/gameplay/GameplayTorchLight.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/MapAssetLoader.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/render/lighting/FxLightClustering.h"
#include "game/render/lighting/LightingStats.h"
#include "game/render/IndoorStaticLighting.h"

#include <algorithm>
#include <vector>

using OpenYAMM::Game::EventRuntimeState;
using OpenYAMM::Game::GameplayTorchLight;
using OpenYAMM::Game::IndoorLight;
using OpenYAMM::Game::IndoorLightingFrame;
using OpenYAMM::Game::IndoorLightingFrameInput;
using OpenYAMM::Game::IndoorLightingRuntime;
using OpenYAMM::Game::IndoorLightingSampleFilter;
using OpenYAMM::Game::IndoorLightSelectionHistory;
using OpenYAMM::Game::IndoorLightSelectionBounds;
using OpenYAMM::Game::IndoorMapData;
using OpenYAMM::Game::IndoorRenderLight;
using OpenYAMM::Game::IndoorRenderLightKind;
using OpenYAMM::Game::IndoorSector;
using OpenYAMM::Game::IndoorVisibilityFrustum;
using OpenYAMM::Game::IndoorVisibilityPlane;
using OpenYAMM::Game::LightingStats;
using OpenYAMM::Game::RenderLightKind;
using OpenYAMM::Game::RenderLight;
using OpenYAMM::Game::DecorationBillboard;
using OpenYAMM::Game::DecorationBillboardSet;
using OpenYAMM::Game::FxLightClusterConfig;
using OpenYAMM::Game::FxLightClusterResult;
using OpenYAMM::Game::MaxIndoorDrawLights;
using OpenYAMM::Game::Party;
using OpenYAMM::Game::PartyBuffId;
using OpenYAMM::Game::gameplayTorchLightBaseRadius;
using OpenYAMM::Game::gameplayTorchLightColorAbgr;
using OpenYAMM::Game::resolveGameplayTorchLight;
using OpenYAMM::Game::SkillMastery;
using OpenYAMM::Game::SpellId;
using OpenYAMM::Game::WorldFxLightEmitter;
using OpenYAMM::Game::addLightingStats;
using OpenYAMM::Game::recordLightingSelection;
using OpenYAMM::Game::resetLightingStats;
using OpenYAMM::Game::spellIdValue;

namespace
{
IndoorMapData makeMapWithOneSector()
{
    IndoorMapData map = {};
    IndoorSector sector = {};
    sector.lightIds.push_back(0);
    map.sectors.push_back(sector);

    IndoorLight light = {};
    light.x = 100;
    light.y = 50;
    light.z = 25;
    light.radius = 400;
    light.red = 255;
    light.green = 128;
    light.blue = 64;
    map.lights.push_back(light);
    return map;
}
}

TEST_CASE("indoor lighting keeps shader draw light budget local to each draw")
{
    CHECK_EQ(MaxIndoorDrawLights, 12u);
}

TEST_CASE("indoor baked lighting finds a small light inside a triangle with unlit corners")
{
    const std::array<bx::Vec3, 3> positions = {
        bx::Vec3{-1024.0f, -1024.0f, 0.0f}, bx::Vec3{1024.0f, -1024.0f, 0.0f}, bx::Vec3{0.0f, 1024.0f, 0.0f}
    };
    OpenYAMM::Game::BakedStaticLightSource light = {};
    light.radius = 64.0f;
    const std::array lights = {light};
    CHECK(OpenYAMM::Game::indoorBakedStaticLightNeedsSubdivision(lights, positions));
}

TEST_CASE("indoor baked lighting refines torch curvature below the legacy mesh spacing")
{
    const std::array<bx::Vec3, 3> positions = {
        bx::Vec3{-64.0f, -64.0f, 0.0f}, bx::Vec3{64.0f, -64.0f, 0.0f}, bx::Vec3{0.0f, 64.0f, 0.0f}
    };
    OpenYAMM::Game::BakedStaticLightSource light = {};
    light.radius = 256.0f;
    const std::array lights = {light};
    CHECK(OpenYAMM::Game::indoorBakedStaticLightNeedsSubdivision(lights, positions));
}

TEST_CASE("indoor baked lighting keeps unlit and nearly flat triangles coarse")
{
    const std::array<bx::Vec3, 3> positions = {
        bx::Vec3{0.0f, 0.0f, 0.0f}, bx::Vec3{64.0f, 0.0f, 0.0f}, bx::Vec3{0.0f, 64.0f, 0.0f}
    };
    OpenYAMM::Game::BakedStaticLightSource light = {};
    light.position = {0.0f, 0.0f, 1024.0f};
    light.radius = 128.0f;
    std::array lights = {light};
    CHECK_FALSE(OpenYAMM::Game::indoorBakedStaticLightNeedsSubdivision(lights, positions));

    lights[0].position = {0.0f, 0.0f, 0.0f};
    lights[0].radius = 1024.0f;
    CHECK_FALSE(OpenYAMM::Game::indoorBakedStaticLightNeedsSubdivision(lights, positions));
}

TEST_CASE("indoor baked lighting budgets the combined curvature of overlapping lights")
{
    const std::array<bx::Vec3, 3> positions = {
        bx::Vec3{-64.0f, -64.0f, 0.0f}, bx::Vec3{64.0f, -64.0f, 0.0f}, bx::Vec3{0.0f, 64.0f, 0.0f}
    };
    OpenYAMM::Game::BakedStaticLightSource light = {};
    light.radius = 400.0f;
    light.alpha = 0.1f;
    std::vector lights = {light};
    CHECK_FALSE(OpenYAMM::Game::indoorBakedStaticLightNeedsSubdivision(lights, positions));
    lights.resize(10, light);
    CHECK(OpenYAMM::Game::indoorBakedStaticLightNeedsSubdivision(lights, positions));
}

TEST_CASE("indoor baked lighting avoids refining large triangles for a dim light skirt")
{
    const std::array<bx::Vec3, 3> positions = {
        bx::Vec3{-1024.0f, -1024.0f, 0.0f}, bx::Vec3{1024.0f, -1024.0f, 0.0f}, bx::Vec3{0.0f, 1024.0f, 0.0f}
    };
    OpenYAMM::Game::BakedStaticLightSource light = {};
    light.radius = 256.0f;
    light.position = {0.0f, 0.0f, 246.0f};
    const std::array lights = {light};
    CHECK_FALSE(OpenYAMM::Game::indoorBakedStaticLightNeedsSubdivision(lights, positions));
}

TEST_CASE("indoor baked lighting does not combine curvature peaks at different probe positions")
{
    const std::array<bx::Vec3, 3> positions = {
        bx::Vec3{-64.0f, -64.0f, 0.0f}, bx::Vec3{64.0f, -64.0f, 0.0f}, bx::Vec3{0.0f, 64.0f, 0.0f}
    };
    OpenYAMM::Game::BakedStaticLightSource first = {};
    first.position = {0.0f, -64.0f, 0.0f};
    first.radius = 64.0f;
    first.alpha = 0.03f;
    OpenYAMM::Game::BakedStaticLightSource second = first;
    second.position = {32.0f, 0.0f, 0.0f};
    const std::array lights = {first, second};
    CHECK_FALSE(OpenYAMM::Game::indoorBakedStaticLightNeedsSubdivision(lights, positions));
}

TEST_CASE("lighting stats accumulate and reset instrumentation counters")
{
    LightingStats stats = {};
    stats.inputLights = 3;
    stats.maxCandidatesPerSelection = 2;
    stats.selectionNanoseconds = 12;

    LightingStats increment = {};
    increment.inputLights = 4;
    increment.maxCandidatesPerSelection = 9;
    increment.selectionNanoseconds = 5;
    addLightingStats(stats, increment);

    CHECK_EQ(stats.inputLights, 7u);
    CHECK_EQ(stats.maxCandidatesPerSelection, 9u);
    CHECK_EQ(stats.selectionNanoseconds, 17u);

    recordLightingSelection(stats, 6, 3, 2);
    CHECK_EQ(stats.selectionCalls, 1u);
    CHECK_EQ(stats.candidateEvaluations, 6u);
    CHECK_EQ(stats.selectedLights, 3u);
    CHECK_EQ(stats.omittedTailLights, 2u);

    resetLightingStats(stats);
    CHECK_EQ(stats.inputLights, 0u);
    CHECK_EQ(stats.selectionNanoseconds, 0u);
}

TEST_CASE("world FX light emitters default to generic render-light metadata")
{
    WorldFxLightEmitter defaultEmitter = {};
    CHECK(defaultEmitter.kind == RenderLightKind::GenericFx);
    CHECK_EQ(defaultEmitter.intensity, 1.0f);
    CHECK_EQ(defaultEmitter.stableId, 0u);
    CHECK_FALSE(defaultEmitter.important);

    WorldFxLightEmitter projectileEmitter = {};
    projectileEmitter.kind = RenderLightKind::Projectile;
    projectileEmitter.sectorId = 7;
    projectileEmitter.stableId = 42;
    projectileEmitter.important = true;

    CHECK(projectileEmitter.kind == RenderLightKind::Projectile);
    CHECK_EQ(projectileEmitter.sectorId, 7);
    CHECK_EQ(projectileEmitter.stableId, 42u);
    CHECK(projectileEmitter.important);
}

TEST_CASE("FX light clustering collapses dense projectile lights in one sector")
{
    std::vector<RenderLight> sourceLights;

    for (uint32_t index = 0; index < 12; ++index)
    {
        RenderLight light = {};
        light.position = {static_cast<float>(index * 8), 0.0f, 0.0f};
        light.radius = 96.0f;
        light.colorAbgr = 0xff6040ffu;
        light.intensity = 1.0f;
        light.sectorId = 2;
        light.kind = RenderLightKind::Projectile;
        light.dynamic = true;
        sourceLights.push_back(light);
    }

    RenderLight torch = {};
    torch.position = {500.0f, 0.0f, 0.0f};
    torch.radius = 500.0f;
    torch.colorAbgr = 0xffffffffu;
    torch.intensity = 1.0f;
    torch.sectorId = 2;
    torch.kind = RenderLightKind::Torch;
    torch.dynamic = true;
    torch.important = true;
    sourceLights.push_back(torch);

    FxLightClusterConfig config = {};
    config.cellSize = 256.0f;
    config.thresholdPerSector = 8;
    config.maxClustersPerSector = 8;
    config.maxRadius = 900.0f;
    config.maxIntensity = 2.5f;

    const FxLightClusterResult result = OpenYAMM::Game::FxLightClustering::clusterSectorFxLights(
        sourceLights,
        config);

    REQUIRE_EQ(result.lights.size(), 2u);
    CHECK_EQ(result.clusteredInputLights, 12u);
    CHECK_EQ(result.outputClusterLights, 1u);

    bool foundCluster = false;
    bool foundTorch = false;

    for (const RenderLight &light : result.lights)
    {
        if (light.kind == RenderLightKind::ClusteredFx)
        {
            foundCluster = true;
            CHECK_EQ(light.sectorId, 2);
            CHECK(light.radius <= 900.0f);
            CHECK(light.intensity <= 2.5f);
            CHECK(light.stableId != 0u);
        }

        if (light.kind == RenderLightKind::Torch)
        {
            foundTorch = true;
        }
    }

    CHECK(foundCluster);
    CHECK(foundTorch);
}

TEST_CASE("FX light clustering supports sectorless outdoor dynamic lights")
{
    std::vector<RenderLight> sourceLights;

    for (uint32_t index = 0; index < 20; ++index)
    {
        RenderLight light = {};
        light.position = {static_cast<float>(index * 10), 32.0f, 64.0f};
        light.radius = 128.0f;
        light.colorAbgr = 0xff6040ffu;
        light.intensity = 1.0f;
        light.sectorId = -1;
        light.kind = RenderLightKind::Projectile;
        light.dynamic = true;
        sourceLights.push_back(light);
    }

    FxLightClusterConfig config = {};
    config.cellSize = 512.0f;
    config.thresholdPerSector = 8;
    config.maxClustersPerSector = 4;
    config.maxRadius = 1400.0f;
    config.maxIntensity = 2.5f;
    config.allowSectorlessLights = true;

    const FxLightClusterResult result = OpenYAMM::Game::FxLightClustering::clusterSectorFxLights(
        sourceLights,
        config);

    REQUIRE_EQ(result.lights.size(), 1u);
    CHECK_EQ(result.clusteredInputLights, 20u);
    CHECK_EQ(result.outputClusterLights, 1u);
    CHECK_EQ(result.lights.front().sectorId, -1);
    CHECK(result.lights.front().kind == RenderLightKind::ClusteredFx);
    CHECK(result.lights.front().stableId != 0u);
}

TEST_CASE("FX light clustering collapses dense indoor spark lights before draw selection")
{
    std::vector<RenderLight> sourceLights;

    for (uint32_t index = 0; index < 35; ++index)
    {
        RenderLight light = {};
        light.position = {
            static_cast<float>((index % 7) * 48),
            static_cast<float>((index / 7) * 36),
            static_cast<float>((index % 3) * 24)
        };
        light.radius = 112.0f;
        light.colorAbgr = 0xff6040ffu;
        light.intensity = 1.0f;
        light.sectorId = -1;
        light.kind = RenderLightKind::Projectile;
        light.dynamic = true;
        sourceLights.push_back(light);
    }

    FxLightClusterConfig config = {};
    config.cellSize = 512.0f;
    config.thresholdPerSector = 4;
    config.maxClustersPerSector = 7;
    config.maxRadius = 640.0f;
    config.maxIntensity = 2.5f;
    config.allowSectorlessLights = true;

    const FxLightClusterResult result = OpenYAMM::Game::FxLightClustering::clusterSectorFxLights(
        sourceLights,
        config);

    REQUIRE_EQ(result.lights.size(), 1u);
    CHECK_EQ(result.clusteredInputLights, 35u);
    CHECK_EQ(result.outputClusterLights, 1u);
    CHECK_EQ(result.lights.front().sectorId, -1);
    CHECK(result.lights.front().kind == RenderLightKind::ClusteredFx);
    CHECK(result.lights.front().radius <= 640.0f);
    CHECK(result.lights.front().stableId != 0u);
}

TEST_CASE("indoor lighting resolves BLV light enabled state from attributes and runtime overrides")
{
    CHECK(IndoorLightingRuntime::isBlvLightEnabledByState(0, nullptr, 3));
    CHECK_FALSE(IndoorLightingRuntime::isBlvLightEnabledByState(0x08, nullptr, 3));

    EventRuntimeState state = {};
    state.indoorLightsEnabled[3] = true;
    CHECK(IndoorLightingRuntime::isBlvLightEnabledByState(0x08, &state, 3));

    state.indoorLightsEnabled[3] = false;
    CHECK_FALSE(IndoorLightingRuntime::isBlvLightEnabledByState(0, &state, 3));
}

TEST_CASE("indoor lighting maps sector ambient level to darker ambient")
{
    const float bright = IndoorLightingRuntime::ambientFromMinAmbientLightLevel(0);
    const float dark = IndoorLightingRuntime::ambientFromMinAmbientLightLevel(24);

    CHECK(bright > dark);
    CHECK(bright <= 1.0f);
    CHECK(dark >= 0.18f);
}

TEST_CASE("indoor lighting builds BLV lights and respects runtime SetLight state")
{
    IndoorMapData map = makeMapWithOneSector();
    EventRuntimeState state = {};
    IndoorLightingFrameInput input = {};
    input.pMapData = &map;
    input.pEventRuntimeState = &state;
    input.cameraPosition = {0.0f, 0.0f, 0.0f};

    IndoorLightingRuntime runtime;
    IndoorLightingFrame frame = runtime.buildFrame(input);

    REQUIRE_EQ(frame.lights.size(), 1u);
    CHECK(frame.lights.front().kind == IndoorRenderLightKind::Static);
    CHECK_EQ(frame.lights.front().radius, 400.0f);

    state.indoorLightsEnabled[0] = false;
    frame = runtime.buildFrame(input);
    CHECK(frame.lights.empty());
}

TEST_CASE("indoor decoration light is hidden when consumable decoration is cleared")
{
    IndoorMapData map = {};
    map.sectors.push_back({});

    OpenYAMM::Game::IndoorEntity campfire = {};
    campfire.decorationListId = 0;
    campfire.x = 100;
    campfire.y = 200;
    campfire.z = 300;
    campfire.name = "dec24";
    map.entities.push_back(campfire);

    DecorationBillboardSet billboardSet = {};
    REQUIRE(billboardSet.decorationTable.loadRows({
        {"1", "dec24", "campfire", "0", "52", "56", "128", "200", "30", "30", "0", "0", "216"}
    }));

    DecorationBillboard billboard = {};
    billboard.entityIndex = 0;
    billboard.decorationId = 0;
    billboard.spriteId = 216;
    billboard.height = 56;
    billboard.x = 100;
    billboard.y = 200;
    billboard.z = 300;
    billboard.sectorId = 0;
    billboard.name = "dec24";
    billboardSet.billboards.push_back(billboard);

    IndoorLightingRuntime runtime;
    runtime.rebuildStaticCache(map, &billboardSet);

    EventRuntimeState state = {};
    IndoorLightingFrameInput input = {};
    input.pMapData = &map;
    input.pDecorationBillboardSet = &billboardSet;
    input.pEventRuntimeState = &state;

    IndoorLightingFrame frame = runtime.buildFrame(input);
    REQUIRE_EQ(frame.lights.size(), 1u);
    CHECK(frame.lights.front().kind == IndoorRenderLightKind::Decoration);

    state.decorVars[0] = 2;
    frame = runtime.buildFrame(input);
    CHECK(frame.lights.empty());
}

TEST_CASE("indoor decoration light toggles update cached light and preserve authored interactions")
{
    using namespace OpenYAMM::Game;
    DecorationBillboardSet billboards;
    REQUIRE(billboards.decorationTable.loadRows({
        {"1", "brazir2f", "brazier", "0", "30", "40", "0", "0", "0", "0", "0", "0", "1"},
        {"2", "brzier00", "brazier", "0", "30", "40", "256", "0", "0", "0", "0", "0", "2"},
        {"3", "nwtrchnf", "torch", "0", "30", "40", "0", "0", "0", "0", "0", "0", "3"},
        {"4", "TrchB00", "torch", "0", "30", "40", "256", "0", "0", "0", "0", "0", "4"}
    }));
    for (const char *name : {"brazir2f", "nwtrchnf"})
    {
        IndoorMapData map;
        map.sectors.resize(1);
        IndoorEntity entity;
        entity.name = name;
        entity.eventIdPrimary = 42;
        map.entities.push_back(entity);
        IndoorLight light;
        light.x = light.y = light.z = 100;
        light.radius = 400;
        light.attributes = 8;
        map.lights.push_back(light);
        light.x = 101;
        map.lights.push_back(light);
        map.sectors[0].lightIds = {0, 1};
        DecorationBillboard billboard;
        billboard.name = name;
        billboard.decorationId = *billboards.decorationTable.findIdByInternalName(name);
        billboard.spriteId = billboards.decorationTable.get(billboard.decorationId)->spriteId;
        billboard.eventIdPrimary = 42;
        billboard.sectorId = 0;
        billboard.height = 40;
        billboards.billboards = {billboard};
        EventRuntimeState state;
        state.decorVars.fill(7);
        IndoorLightingRuntime lighting;
        lighting.rebuildStaticCache(map, &billboards, &state);
        IndoorLightingFrameInput input;
        input.pMapData = &map;
        input.pDecorationBillboardSet = &billboards;
        input.pEventRuntimeState = &state;
        CHECK(lighting.buildFrame(input).lights.empty());
        REQUIRE(toggleIndoorDecorationLight(map, billboards.decorationTable, 0, state));
        CHECK_EQ(state.indoorLightRevision, 1u);
        CHECK(state.indoorLightsEnabled.at(0));
        CHECK_FALSE(state.indoorLightsEnabled.contains(1));
        REQUIRE_EQ(lighting.buildFrame(input).lights.size(), 2u);
        CHECK_EQ(lighting.buildFrame(input).lights.back().radius, 256.0f);
        REQUIRE(toggleIndoorDecorationLight(map, billboards.decorationTable, 0, state));
        CHECK_EQ(state.spriteOverrides.at(42).textureName, name);
        CHECK_FALSE(state.indoorLightsEnabled.at(0));
        CHECK(lighting.buildFrame(input).lights.empty());
        CHECK(std::all_of(state.decorVars.begin(), state.decorVars.end(), [](uint8_t value) { return value == 7; }));
        map.entities[0].eventIdSecondary = 12;
        CHECK_FALSE(toggleIndoorDecorationLight(map, billboards.decorationTable, 0, state));
        map.entities[0].eventIdSecondary = 0;
        state.spriteOverrides.at(42).hidden = true;
        CHECK_FALSE(toggleIndoorDecorationLight(map, billboards.decorationTable, 0, state));
        CHECK_FALSE(toggleIndoorDecorationLight(map, billboards.decorationTable, 1, state));
    }
}

TEST_CASE("indoor lighting gives Torchlight priority and boosts indoor intensity")
{
    IndoorMapData map = makeMapWithOneSector();
    Party party = {};
    party.applyPartyBuff(
        PartyBuffId::TorchLight,
        120.0f,
        3,
        spellIdValue(SpellId::TorchLight),
        1,
        SkillMastery::Expert,
        0);

    IndoorLightingFrameInput input = {};
    input.pMapData = &map;
    input.pParty = &party;
    input.cameraPosition = {10.0f, 20.0f, 30.0f};

    IndoorLightingRuntime runtime;
    const IndoorLightingFrame frame = runtime.buildFrame(input);

    REQUIRE_FALSE(frame.lights.empty());
    CHECK(frame.lights.front().kind == IndoorRenderLightKind::Torch);
    CHECK_EQ(frame.lights.front().radius, 2400.0f);
    CHECK_EQ(frame.lights.front().intensity, 1.5f);
    CHECK_EQ(frame.lights.front().colorAbgr, gameplayTorchLightColorAbgr());
}

TEST_CASE("gameplay Torchlight follows OE indoor and outdoor light distances")
{
    Party party = {};
    party.applyPartyBuff(
        PartyBuffId::TorchLight,
        120.0f,
        4,
        spellIdValue(SpellId::TorchLight),
        1,
        SkillMastery::Master,
        0);

    const std::optional<GameplayTorchLight> indoorLight = resolveGameplayTorchLight(party, false, true);
    const std::optional<GameplayTorchLight> outdoorNightLight = resolveGameplayTorchLight(party, true, true);
    const std::optional<GameplayTorchLight> outdoorDayLight = resolveGameplayTorchLight(party, true, false);

    REQUIRE(indoorLight.has_value());
    REQUIRE(outdoorNightLight.has_value());
    CHECK_EQ(gameplayTorchLightBaseRadius(false), 800.0f);
    CHECK_EQ(gameplayTorchLightBaseRadius(true), 1024.0f);
    CHECK_EQ(indoorLight->radius, 3200.0f);
    CHECK_EQ(indoorLight->intensity, 1.0f);
    CHECK_EQ(outdoorNightLight->radius, 4096.0f);
    CHECK_FALSE(outdoorDayLight.has_value());
}

TEST_CASE("indoor Torchlight visibly raises sampled lighting near the party")
{
    Party party = {};
    party.applyPartyBuff(
        PartyBuffId::TorchLight,
        120.0f,
        2,
        spellIdValue(SpellId::TorchLight),
        1,
        SkillMastery::Normal,
        0);

    IndoorLightingFrameInput input = {};
    input.pParty = &party;
    input.cameraPosition = {0.0f, 0.0f, 0.0f};

    IndoorLightingRuntime runtime;
    const IndoorLightingFrame frame = runtime.buildFrame(input);
    const std::array<float, 3> atParty = IndoorLightingRuntime::sampleLightingRgb(frame, {0.0f, 0.0f, 0.0f});
    const std::array<float, 3> farFromParty = IndoorLightingRuntime::sampleLightingRgb(frame, {5000.0f, 0.0f, 0.0f});

    CHECK(atParty[0] > farFromParty[0] + 0.4f);
    CHECK(atParty[1] > farFromParty[1] + 0.4f);
    CHECK(atParty[2] > farFromParty[2] + 0.4f);
}

TEST_CASE("indoor lighting keeps all visible BLV lights and caps only draw selection")
{
    IndoorMapData map = {};
    IndoorSector sector = {};

    for (size_t index = 0; index < MaxIndoorDrawLights + 4; ++index)
    {
        IndoorLight light = {};
        light.x = static_cast<int16_t>(index * 100);
        light.radius = static_cast<int16_t>(200 + index);
        light.red = 255;
        light.green = 255;
        light.blue = 255;
        map.lights.push_back(light);
        sector.lightIds.push_back(static_cast<uint16_t>(index));
    }

    map.sectors.push_back(sector);

    IndoorLightingFrameInput input = {};
    input.pMapData = &map;
    input.cameraPosition = {0.0f, 0.0f, 0.0f};

    IndoorLightingRuntime runtime;
    runtime.rebuildStaticCache(map, nullptr);
    const IndoorLightingFrame frame = runtime.buildFrame(input);

    CHECK_EQ(frame.lights.size(), MaxIndoorDrawLights + 4u);
    CHECK(frame.lights.front().kind == IndoorRenderLightKind::Static);

    const OpenYAMM::Game::IndoorDrawLightSet drawLights =
        IndoorLightingRuntime::selectDrawLightSetForSectors(frame, {0.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, 0, -1);

    CHECK_EQ(drawLights.lightCount, MaxIndoorDrawLights);
}

TEST_CASE("indoor lighting selects static lights from the requested sector")
{
    IndoorMapData map = {};
    map.sectors.resize(2);

    IndoorLight firstSectorLight = {};
    firstSectorLight.x = 100;
    firstSectorLight.radius = 300;
    firstSectorLight.red = 255;
    firstSectorLight.green = 255;
    firstSectorLight.blue = 255;
    map.lights.push_back(firstSectorLight);
    map.sectors[0].lightIds.push_back(0);

    IndoorLight secondSectorLight = {};
    secondSectorLight.x = 5000;
    secondSectorLight.radius = 300;
    secondSectorLight.red = 255;
    secondSectorLight.green = 255;
    secondSectorLight.blue = 255;
    map.lights.push_back(secondSectorLight);
    map.sectors[1].lightIds.push_back(1);

    IndoorLightingRuntime runtime;
    runtime.rebuildStaticCache(map, nullptr);

    IndoorLightingFrameInput input = {};
    input.pMapData = &map;
    const IndoorLightingFrame frame = runtime.buildFrame(input);
    const OpenYAMM::Game::IndoorDrawLightSet firstSectorDrawLights =
        IndoorLightingRuntime::selectDrawLightSetForSectors(frame, {0.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, 0, -1);

    REQUIRE_EQ(firstSectorDrawLights.lightCount, 1u);
    CHECK_EQ(firstSectorDrawLights.positions[0], doctest::Approx(100.0f));
}

TEST_CASE("indoor lighting samples static detail and dynamic contributions separately")
{
    IndoorLightingFrame frame = {};
    frame.ambient = 0.25f;
    frame.lightIndicesBySector.resize(1);
    frame.dynamicLightIndicesBySector.resize(1);

    IndoorRenderLight staticLight = {};
    staticLight.position = {0.0f, 0.0f, 0.0f};
    staticLight.radius = 256.0f;
    staticLight.colorAbgr = 0xff0000ffu;
    staticLight.intensity = 1.0f;
    staticLight.sectorId = 0;
    staticLight.kind = IndoorRenderLightKind::Static;
    frame.lightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
    frame.lights.push_back(staticLight);

    IndoorRenderLight fxLight = {};
    fxLight.position = {0.0f, 0.0f, 0.0f};
    fxLight.radius = 256.0f;
    fxLight.colorAbgr = 0xffff0000u;
    fxLight.intensity = 1.0f;
    fxLight.sectorId = 0;
    fxLight.kind = IndoorRenderLightKind::Fx;
    frame.dynamicLightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
    frame.lights.push_back(fxLight);

    const std::array<float, 3> staticOnly =
        IndoorLightingRuntime::sampleLightingRgbForSectors(
            frame,
            {0.0f, 0.0f, 0.0f},
            0,
            -1,
            nullptr,
            IndoorLightingSampleFilter::StaticDetailOnly);
    const std::array<float, 3> dynamicOnly =
        IndoorLightingRuntime::sampleLightingRgbForSectors(
            frame,
            {0.0f, 0.0f, 0.0f},
            0,
            -1,
            nullptr,
            IndoorLightingSampleFilter::DynamicOnly);

    CHECK(staticOnly[0] > frame.ambient);
    CHECK(staticOnly[2] == doctest::Approx(frame.ambient));
    CHECK(dynamicOnly[0] == doctest::Approx(frame.ambient));
    CHECK(dynamicOnly[2] > frame.ambient);
}

TEST_CASE("indoor lighting filters visible-sector static lights by clipped frustum")
{
    IndoorMapData map = {};
    map.sectors.resize(2);

    IndoorLight visibleLight = {};
    visibleLight.y = 0;
    visibleLight.radius = 10;
    visibleLight.red = 255;
    visibleLight.green = 255;
    visibleLight.blue = 255;
    map.lights.push_back(visibleLight);
    map.sectors[1].lightIds.push_back(0);

    IndoorLight hiddenLight = {};
    hiddenLight.y = 1000;
    hiddenLight.radius = 10;
    hiddenLight.red = 255;
    hiddenLight.green = 255;
    hiddenLight.blue = 255;
    map.lights.push_back(hiddenLight);
    map.sectors[1].lightIds.push_back(1);

    std::vector<uint8_t> visibleSectorMask = {0, 1};
    std::vector<std::vector<IndoorVisibilityFrustum>> visibleSectorFrustums(2);
    IndoorVisibilityPlane maxY = {};
    maxY.normal = {0.0f, -1.0f, 0.0f};
    maxY.distance = 100.0f;
    IndoorVisibilityPlane minY = {};
    minY.normal = {0.0f, 1.0f, 0.0f};
    minY.distance = 100.0f;
    visibleSectorFrustums[1].push_back({maxY, minY});

    IndoorLightingRuntime runtime;
    runtime.rebuildStaticCache(map, nullptr);

    IndoorLightingFrameInput input = {};
    input.pMapData = &map;
    input.pVisibleSectorMask = &visibleSectorMask;
    input.pVisibleSectorFrustums = &visibleSectorFrustums;
    const IndoorLightingFrame frame = runtime.buildFrame(input);

    REQUIRE_EQ(frame.lights.size(), 1u);
    CHECK_EQ(frame.lights.front().position.y, doctest::Approx(0.0f));
}

TEST_CASE("indoor lighting approximates non-detail lights instead of dropping them")
{
    IndoorLightingFrame frame = {};
    frame.ambient = 0.25f;
    frame.lightIndicesBySector.resize(1);

    for (size_t index = 0; index < MaxIndoorDrawLights + 1; ++index)
    {
        IndoorRenderLight light = {};
        light.position = {static_cast<float>(index * 8), 0.0f, 0.0f};
        light.radius = 250.0f;
        light.colorAbgr = 0xffffffffu;
        light.intensity = 1.0f;
        light.sectorId = 0;
        frame.lightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
        frame.lights.push_back(light);
    }

    IndoorLightSelectionBounds bounds = {};
    bounds.min = {-32.0f, -32.0f, -32.0f};
    bounds.max = {128.0f, 32.0f, 32.0f};
    bounds.valid = true;

    const OpenYAMM::Game::IndoorDrawLightSet drawLights =
        IndoorLightingRuntime::selectDrawLightSetForBounds(
            frame,
            {0.0f, 0.0f, 0.0f},
            {1.0f, 0.0f, 0.0f},
            0,
            -1,
            bounds);

    CHECK_EQ(drawLights.lightCount, MaxIndoorDrawLights);
    CHECK(drawLights.params[1] > frame.ambient);
}

TEST_CASE("indoor lighting keeps static detail lights when many FX lights are present")
{
    IndoorLightingFrame frame = {};
    frame.ambient = 0.25f;
    frame.lightIndicesBySector.resize(1);

    IndoorRenderLight staticLight = {};
    staticLight.position = {100.0f, 0.0f, 0.0f};
    staticLight.radius = 300.0f;
    staticLight.colorAbgr = 0xffffffffu;
    staticLight.intensity = 1.0f;
    staticLight.sectorId = 0;
    staticLight.kind = IndoorRenderLightKind::Static;
    frame.lightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
    frame.lights.push_back(staticLight);

    for (size_t index = 0; index < MaxIndoorDrawLights + 4; ++index)
    {
        IndoorRenderLight fxLight = {};
        fxLight.position = {static_cast<float>(index * 6), 0.0f, 0.0f};
        fxLight.radius = 500.0f;
        fxLight.colorAbgr = 0xffffffffu;
        fxLight.intensity = 1.0f;
        fxLight.kind = IndoorRenderLightKind::Fx;
        frame.globalLightIndices.push_back(static_cast<uint32_t>(frame.lights.size()));
        frame.lights.push_back(fxLight);
    }

    IndoorLightSelectionBounds bounds = {};
    bounds.min = {-32.0f, -32.0f, -32.0f};
    bounds.max = {160.0f, 32.0f, 32.0f};
    bounds.valid = true;

    const OpenYAMM::Game::IndoorDrawLightSet drawLights =
        IndoorLightingRuntime::selectDrawLightSetForBounds(
            frame,
            {0.0f, 0.0f, 0.0f},
            {1.0f, 0.0f, 0.0f},
            0,
            -1,
            bounds);

    bool foundStaticLight = false;

    for (size_t index = 0; index < drawLights.lightCount; ++index)
    {
        const size_t base = index * 4;

        if (drawLights.positions[base] == doctest::Approx(staticLight.position.x))
        {
            foundStaticLight = true;
            break;
        }
    }

    CHECK(foundStaticLight);
}

TEST_CASE("indoor lighting does not scan unrelated sector FX candidates for local draw selection")
{
    IndoorLightingFrame frame = {};
    frame.ambient = 0.25f;
    frame.lightIndicesBySector.resize(3);
    frame.dynamicLightIndicesBySector.resize(3);

    IndoorRenderLight localFxLight = {};
    localFxLight.position = {0.0f, 0.0f, 0.0f};
    localFxLight.radius = 300.0f;
    localFxLight.colorAbgr = 0xffffffffu;
    localFxLight.intensity = 1.0f;
    localFxLight.sectorId = 0;
    localFxLight.kind = IndoorRenderLightKind::Fx;
    frame.dynamicLightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
    frame.fxLightIndices.push_back(static_cast<uint32_t>(frame.lights.size()));
    frame.lights.push_back(localFxLight);

    for (size_t index = 0; index < MaxIndoorDrawLights * 4; ++index)
    {
        IndoorRenderLight unrelatedFxLight = {};
        unrelatedFxLight.position = {static_cast<float>(index * 8), 0.0f, 0.0f};
        unrelatedFxLight.radius = 2000.0f;
        unrelatedFxLight.colorAbgr = 0xffffffffu;
        unrelatedFxLight.intensity = 1.0f;
        unrelatedFxLight.sectorId = 2;
        unrelatedFxLight.kind = IndoorRenderLightKind::Fx;
        frame.dynamicLightIndicesBySector[2].push_back(static_cast<uint32_t>(frame.lights.size()));
        frame.fxLightIndices.push_back(static_cast<uint32_t>(frame.lights.size()));
        frame.lights.push_back(unrelatedFxLight);
    }

    IndoorLightSelectionBounds bounds = {};
    bounds.min = {-32.0f, -32.0f, -32.0f};
    bounds.max = {32.0f, 32.0f, 32.0f};
    bounds.valid = true;

    LightingStats stats = {};
    const OpenYAMM::Game::IndoorDrawLightSet drawLights =
        IndoorLightingRuntime::selectDrawLightSetForBounds(
            frame,
            {0.0f, 0.0f, 0.0f},
            {1.0f, 0.0f, 0.0f},
            0,
            -1,
            bounds,
            &stats);

    CHECK_EQ(drawLights.lightCount, 1u);
    CHECK_EQ(stats.selectionCalls, 1u);
    CHECK_EQ(stats.candidateEvaluations, 1u);
    CHECK_EQ(stats.maxCandidatesPerSelection, 1u);
}

TEST_CASE("indoor lighting can omit baked static lights from live draw selection")
{
    IndoorLightingFrame frame = {};
    frame.ambient = 0.25f;
    frame.lightIndicesBySector.resize(1);
    frame.dynamicLightIndicesBySector.resize(1);

    IndoorRenderLight torchLight = {};
    torchLight.position = {128.0f, 0.0f, 0.0f};
    torchLight.radius = 256.0f;
    torchLight.colorAbgr = 0xffffffffu;
    torchLight.intensity = 1.0f;
    torchLight.sectorId = 0;
    torchLight.kind = IndoorRenderLightKind::Torch;
    torchLight.stableId = 900;
    frame.dynamicLightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
    frame.lights.push_back(torchLight);

    for (size_t index = 0; index < MaxIndoorDrawLights; ++index)
    {
        IndoorRenderLight staticLight = {};
        staticLight.position = {128.0f, 0.0f, 0.0f};
        staticLight.radius = 256.0f;
        staticLight.colorAbgr = 0xffffffffu;
        staticLight.intensity = 20.0f;
        staticLight.sectorId = 0;
        staticLight.kind = IndoorRenderLightKind::Static;
        staticLight.stableId = static_cast<uint32_t>(index + 1);
        frame.lightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
        frame.lights.push_back(staticLight);
    }

    IndoorRenderLight decorationLight = {};
    decorationLight.position = {128.0f, 0.0f, 0.0f};
    decorationLight.radius = 256.0f;
    decorationLight.colorAbgr = 0xffffffffu;
    decorationLight.intensity = 20.0f;
    decorationLight.sectorId = 0;
    decorationLight.kind = IndoorRenderLightKind::Decoration;
    decorationLight.stableId = 950;
    frame.lightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
    frame.lights.push_back(decorationLight);

    for (size_t index = 0; index < 7; ++index)
    {
        IndoorRenderLight fxLight = {};
        fxLight.position = {128.0f, 0.0f, 0.0f};
        fxLight.radius = 256.0f;
        fxLight.colorAbgr = 0xffffffffu;
        fxLight.intensity = 1.0f;
        fxLight.sectorId = 0;
        fxLight.kind = IndoorRenderLightKind::Fx;
        fxLight.stableId = static_cast<uint32_t>(100 + index);
        frame.dynamicLightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
        frame.fxLightIndices.push_back(static_cast<uint32_t>(frame.lights.size()));
        frame.lights.push_back(fxLight);
    }

    IndoorLightSelectionBounds bounds = {};
    bounds.min = {-32.0f, -32.0f, -32.0f};
    bounds.max = {160.0f, 32.0f, 32.0f};
    bounds.valid = true;

    const OpenYAMM::Game::IndoorDrawLightSet drawLights =
        IndoorLightingRuntime::selectDrawLightSetForBounds(
            frame,
            {0.0f, 0.0f, 0.0f},
            {1.0f, 0.0f, 0.0f},
            0,
            -1,
            bounds,
            nullptr,
            nullptr,
            false);

    bool selectedTorch = false;
    size_t selectedStaticCount = 0;
    size_t selectedDecorationCount = 0;
    size_t selectedFxCount = 0;

    for (size_t index = 0; index < drawLights.lightCount; ++index)
    {
        selectedTorch = selectedTorch || drawLights.stableIds[index] == 900;

        if (drawLights.stableIds[index] >= 1 && drawLights.stableIds[index] <= MaxIndoorDrawLights)
        {
            ++selectedStaticCount;
        }
        else if (drawLights.stableIds[index] == 950)
        {
            ++selectedDecorationCount;
        }
        else if (drawLights.stableIds[index] >= 100 && drawLights.stableIds[index] < 107)
        {
            ++selectedFxCount;
        }
    }

    CHECK_EQ(drawLights.lightCount, 8u);
    CHECK(selectedTorch);
    CHECK_EQ(selectedStaticCount, 0u);
    CHECK_EQ(selectedDecorationCount, 0u);
    CHECK_EQ(selectedFxCount, 7u);
}

TEST_CASE("indoor lighting keeps previous stable light selection when scores are close")
{
    IndoorLightingFrame frame = {};
    frame.ambient = 0.25f;
    frame.dynamicLightIndicesBySector.resize(1);

    for (size_t index = 0; index < MaxIndoorDrawLights; ++index)
    {
        IndoorRenderLight light = {};
        light.position = {128.0f, 0.0f, 0.0f};
        light.radius = 256.0f;
        light.colorAbgr = 0xffffffffu;
        light.intensity = 1.0f;
        light.sectorId = 0;
        light.kind = IndoorRenderLightKind::Fx;
        light.stableId = static_cast<uint32_t>(index + 1);
        frame.dynamicLightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
        frame.fxLightIndices.push_back(static_cast<uint32_t>(frame.lights.size()));
        frame.lights.push_back(light);
    }

    IndoorRenderLight previousLight = {};
    previousLight.position = {128.0f, 0.0f, 0.0f};
    previousLight.radius = 256.0f;
    previousLight.colorAbgr = 0xffffffffu;
    previousLight.intensity = 0.9f;
    previousLight.sectorId = 0;
    previousLight.kind = IndoorRenderLightKind::Fx;
    previousLight.stableId = 999;
    frame.dynamicLightIndicesBySector[0].push_back(static_cast<uint32_t>(frame.lights.size()));
    frame.fxLightIndices.push_back(static_cast<uint32_t>(frame.lights.size()));
    frame.lights.push_back(previousLight);

    IndoorLightSelectionBounds bounds = {};
    bounds.min = {-32.0f, -32.0f, -32.0f};
    bounds.max = {160.0f, 32.0f, 32.0f};
    bounds.valid = true;

    const OpenYAMM::Game::IndoorDrawLightSet withoutHistory =
        IndoorLightingRuntime::selectDrawLightSetForBounds(
            frame,
            {0.0f, 0.0f, 0.0f},
            {1.0f, 0.0f, 0.0f},
            0,
            -1,
            bounds);

    bool selectedPreviousWithoutHistory = false;
    for (size_t index = 0; index < withoutHistory.lightCount; ++index)
    {
        selectedPreviousWithoutHistory = selectedPreviousWithoutHistory || withoutHistory.stableIds[index] == 999;
    }
    CHECK_FALSE(selectedPreviousWithoutHistory);

    IndoorLightSelectionHistory history = {};
    history.lightStableIds[0] = 999;
    history.lightCount = 1;
    const OpenYAMM::Game::IndoorDrawLightSet withHistory =
        IndoorLightingRuntime::selectDrawLightSetForBounds(
            frame,
            {0.0f, 0.0f, 0.0f},
            {1.0f, 0.0f, 0.0f},
            0,
            -1,
            bounds,
            nullptr,
            &history);

    bool selectedPreviousWithHistory = false;
    for (size_t index = 0; index < withHistory.lightCount; ++index)
    {
        selectedPreviousWithHistory = selectedPreviousWithHistory || withHistory.stableIds[index] == 999;
    }
    CHECK(selectedPreviousWithHistory);
}

TEST_CASE("indoor lighting samples ambient plus nearby point lights")
{
    IndoorLightingFrame frame = {};
    frame.ambient = 0.25f;
    IndoorRenderLight light = {};
    light.position = {0.0f, 0.0f, 0.0f};
    light.radius = 100.0f;
    light.colorAbgr = 0xffffffffu;
    light.intensity = 1.0f;
    frame.lights.push_back(light);

    const std::array<float, 3> nearLight = IndoorLightingRuntime::sampleLightingRgb(frame, {0.0f, 0.0f, 0.0f});
    const std::array<float, 3> farLight = IndoorLightingRuntime::sampleLightingRgb(frame, {500.0f, 0.0f, 0.0f});

    CHECK(nearLight[0] > farLight[0]);
    CHECK_EQ(farLight[0], doctest::Approx(0.25f));
}
