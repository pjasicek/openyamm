#include "doctest/doctest.h"

#include "game/events/EventRuntime.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/indoor/IndoorMapData.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"

using OpenYAMM::Game::EventRuntimeState;
using OpenYAMM::Game::IndoorLight;
using OpenYAMM::Game::IndoorLightingFrame;
using OpenYAMM::Game::IndoorLightingFrameInput;
using OpenYAMM::Game::IndoorLightingRuntime;
using OpenYAMM::Game::IndoorMapData;
using OpenYAMM::Game::IndoorRenderLight;
using OpenYAMM::Game::IndoorRenderLightKind;
using OpenYAMM::Game::IndoorSector;
using OpenYAMM::Game::MaxIndoorRenderLights;
using OpenYAMM::Game::Party;
using OpenYAMM::Game::PartyBuffId;
using OpenYAMM::Game::SkillMastery;
using OpenYAMM::Game::SpellId;
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

TEST_CASE("indoor lighting uses OE-sized indoor render light budget")
{
    CHECK_EQ(MaxIndoorRenderLights, 40u);
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

TEST_CASE("indoor lighting gives Torchlight priority and scales radius by buff power")
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
}

TEST_CASE("indoor lighting ranks and truncates BLV lights")
{
    IndoorMapData map = {};
    IndoorSector sector = {};

    for (size_t index = 0; index < MaxIndoorRenderLights + 4; ++index)
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
    const IndoorLightingFrame frame = runtime.buildFrame(input);

    CHECK_EQ(frame.lights.size(), MaxIndoorRenderLights);
    CHECK(frame.lights.front().kind == IndoorRenderLightKind::Static);
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
