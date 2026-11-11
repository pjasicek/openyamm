#include "game/fx/EffectSystem.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <memory>
#include <string>
#include <vector>

namespace
{
std::shared_ptr<OpenYAMM::Game::EffectDefinition> makeDefinition()
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = std::make_shared<EffectDefinition>();
    definition->id = "test:fire";
    definition->durationSeconds = 0.4f;
    definition->timingProfile = EffectTimingProfile::Mm9Native;

    EffectSpriteEmitterDefinition emitter;
    emitter.componentId = 6;
    emitter.startSeconds = 0.0f;
    emitter.endSeconds = 0.08f;
    emitter.spriteResource = "test:sprite/fire";
    emitter.spritesPerEmission = 1;
    emitter.emissionIntervalSeconds = 0.001f;
    emitter.particleLifetimeSeconds = 0.2f;
    emitter.emissionShape = EffectEmissionShape::PlaneIn;
    emitter.radius = 2.0f;
    emitter.velocity = 0.0f;
    emitter.colorKeys = {
        {.time = 0.0f, .rgb = {255, 128, 0}, .transparency = 100},
        {.time = 1.0f, .rgb = {128, 0, 0}, .transparency = 213},
    };
    emitter.scaleKeys = {{.time = 0.0f, .value = 0.2f}, {.time = 1.0f, .value = 0.4f}};
    definition->spriteEmitters.push_back(std::move(emitter));

    EffectSoundDefinition sound;
    sound.componentId = 10;
    sound.startSeconds = 0.0f;
    sound.endSeconds = 0.1f;
    sound.soundResource = "test:sound/fire";
    sound.pitch = 1.25f;
    sound.innerRadius = 10.0f;
    sound.outerRadius = 50.0f;
    definition->sounds.push_back(std::move(sound));
    return definition;
}

OpenYAMM::Game::EffectLibrary makeLibrary()
{
    OpenYAMM::Game::EffectLibrary library;
    std::string error;
    REQUIRE(library.add(makeDefinition(), error));
    return library;
}
}

TEST_CASE("EffectSystem loading dependencies include delayed sprites only for active effects")
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = makeDefinition();
    definition->spriteEmitters.front().startSeconds = 0.2f;
    definition->spriteEmitters.front().endSeconds = 0.3f;
    EffectSpriteDefinition sprite;
    sprite.componentId = 20;
    sprite.spriteResource = "test:sprite/later";
    sprite.startSeconds = 0.2f;
    sprite.endSeconds = 0.3f;
    definition->sprites.push_back(sprite);
    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(definition, error));
    EffectSystem effects(&library);
    CHECK(effects.activeSpriteResources().empty());
    const EffectHandle first = effects.spawn("test:fire");
    const EffectHandle second = effects.spawn("test:fire");
    REQUIRE(effects.contains(first));
    REQUIRE(effects.contains(second));
    CHECK(effects.particles().empty());
    CHECK(effects.fixedSprites().empty());
    CHECK(effects.activeSpriteResources() == std::vector<std::string>{"test:sprite/fire", "test:sprite/later"});
    effects.stop(first, EffectStopMode::Immediate);
    CHECK_EQ(effects.activeSpriteResources().size(), 2);
    effects.stop(second, EffectStopMode::Immediate);
    CHECK(effects.activeSpriteResources().empty());
}

TEST_CASE("EffectSystem preserves world particles when a moving emitter changes transform")
{
    using namespace OpenYAMM::Game;
    EffectLibrary library = makeLibrary();
    EffectSystem effects(&library);
    const EffectHandle handle = effects.spawn("test:fire");
    REQUIRE(effects.contains(handle));

    std::vector<EffectSoundEvent> soundEvents = effects.consumeSoundEvents();
    REQUIRE_EQ(soundEvents.size(), 1);
    CHECK_EQ(soundEvents[0].kind, EffectSoundEventKind::Start);
    CHECK(soundEvents[0].pitch == doctest::Approx(1.25f));

    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.particles().size(), 1);
    const float firstX = effects.particles()[0].position[0];
    CHECK(effects.particles()[0].color[3] == doctest::Approx(1.0f - 100.0f / 255.0f));

    REQUIRE(effects.setTransform(handle, {10.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f));
    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.particles().size(), 2);
    CHECK(effects.particles()[0].position[0] == doctest::Approx(firstX));
    CHECK(effects.particles()[1].position[0] > 7.0f);
}

TEST_CASE("EffectSystem MM9 timing emits at most once per compatibility tick and expires early")
{
    using namespace OpenYAMM::Game;
    EffectLibrary library = makeLibrary();
    EffectSystem effects(&library);
    const EffectHandle handle = effects.spawn("test:fire");

    effects.update(3.0f / 60.0f);
    CHECK_EQ(effects.particles().size(), 3);
    effects.update(4.0f / 60.0f);
    CHECK_EQ(effects.particles().size(), 3);
    CHECK(effects.elapsedSeconds(handle) == doctest::Approx(7.0f / 60.0f));

    const std::vector<EffectSoundEvent> soundEvents = effects.consumeSoundEvents();
    REQUIRE_EQ(soundEvents.size(), 2);
    CHECK_EQ(soundEvents[0].kind, EffectSoundEventKind::Start);
    CHECK_EQ(soundEvents[1].kind, EffectSoundEventKind::Stop);
}

TEST_CASE("EffectSystem exposes 30 60 and 120 Hz MM9 diagnostic policies")
{
    using namespace OpenYAMM::Game;
    EffectLibrary library = makeLibrary();
    for (const std::pair<uint32_t, size_t> expectation : {
             std::pair<uint32_t, size_t>{30, 1},
             std::pair<uint32_t, size_t>{60, 3},
             std::pair<uint32_t, size_t>{120, 6}})
    {
        EffectSystem effects(&library);
        REQUIRE(effects.setReferenceUpdateRate(expectation.first));
        CHECK_EQ(effects.referenceUpdateRate(), expectation.first);
        REQUIRE(effects.contains(effects.spawn("test:fire")));
        effects.update(0.05f);
        CHECK_EQ(effects.particles().size(), expectation.second);
    }

    EffectSystem effects(&library);
    CHECK_FALSE(effects.setReferenceUpdateRate(59));
    CHECK_EQ(effects.referenceUpdateRate(), 60u);
}

TEST_CASE("EffectSystem immediate and drain stops have distinct lifecycle behavior")
{
    using namespace OpenYAMM::Game;
    EffectLibrary library = makeLibrary();
    EffectSystem effects(&library);
    const EffectHandle immediate = effects.spawn("test:fire");
    effects.update(1.0f / 60.0f);
    REQUIRE_FALSE(effects.particles().empty());
    REQUIRE(effects.stop(immediate, EffectStopMode::Immediate));
    CHECK_FALSE(effects.contains(immediate));
    CHECK(effects.particles().empty());

    const EffectHandle draining = effects.spawn("test:fire");
    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.particles().size(), 1);
    REQUIRE(effects.stop(draining, EffectStopMode::Drain));
    effects.update(1.0f / 60.0f);
    CHECK_EQ(effects.particles().size(), 1);
    effects.update(10.0f / 60.0f);
    CHECK(effects.particles().empty());
    CHECK_FALSE(effects.contains(draining));
}

TEST_CASE("EffectSystem rejects duplicate definitions and stale handles")
{
    using namespace OpenYAMM::Game;
    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(makeDefinition(), error));
    CHECK_FALSE(library.add(makeDefinition(), error));
    CHECK(error.find("duplicate") != std::string::npos);

    EffectSystem effects(&library);
    const EffectHandle oldHandle = effects.spawn("test:fire");
    REQUIRE(effects.stop(oldHandle, EffectStopMode::Immediate));
    const EffectHandle replacement = effects.spawn("test:fire");
    CHECK_EQ(oldHandle.index, replacement.index);
    CHECK_NE(oldHandle.generation, replacement.generation);
    CHECK_FALSE(effects.pause(oldHandle, true));
}

TEST_CASE("EffectSystem samples predictable emitters and applies per-tick rotation")
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = std::make_shared<EffectDefinition>();
    definition->id = "test:rotating";
    definition->durationSeconds = 0.2f;
    definition->timingProfile = EffectTimingProfile::Predictable;
    EffectSpriteEmitterDefinition emitter;
    emitter.componentId = 1;
    emitter.spriteResource = "test:sprite/particle";
    emitter.endSeconds = 0.1f;
    emitter.emissionIntervalSeconds = 0.001f;
    emitter.particleLifetimeSeconds = 1.0f;
    emitter.emissionShape = EffectEmissionShape::Plane;
    emitter.planeDirection = {1.0f, 0.0f, 0.0f};
    emitter.velocity = 4.0f;
    emitter.rotationPerTick = {0.0f, 0.0f, 1.57079632679f};
    definition->spriteEmitters.push_back(emitter);

    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(definition, error));
    EffectSystem effects(&library);
    REQUIRE(effects.contains(effects.spawn(definition->id)));
    effects.update(2.0f / 60.0f);

    REQUIRE_EQ(effects.particles().size(), 2);
    CHECK(effects.particles()[0].velocity[0] == doctest::Approx(4.0f));
    CHECK(effects.particles()[0].velocity[1] == doctest::Approx(0.0f));
    CHECK(effects.particles()[1].velocity[0] == doctest::Approx(0.0f).epsilon(0.001));
    CHECK(effects.particles()[1].velocity[1] == doctest::Approx(4.0f));
}

TEST_CASE("EffectSystem local particles follow later root transforms")
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = std::make_shared<EffectDefinition>();
    definition->id = "test:local";
    definition->durationSeconds = 0.2f;
    EffectSpriteEmitterDefinition emitter;
    emitter.componentId = 2;
    emitter.spriteResource = "test:sprite/particle";
    emitter.endSeconds = 0.02f;
    emitter.emissionIntervalSeconds = 1.0f;
    emitter.particleLifetimeSeconds = 1.0f;
    emitter.offset = {2.0f, 0.0f, 0.0f};
    emitter.particleSpace = EffectParticleSpace::Local;
    definition->spriteEmitters.push_back(emitter);

    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(definition, error));
    EffectSystem effects(&library);
    const EffectHandle handle = effects.spawn(definition->id);
    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.particles().size(), 1);
    CHECK(effects.particles()[0].position[0] == doctest::Approx(2.0f));

    REQUIRE(effects.setTransform(handle, {10.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 0.0f, 1.0f}, 2.0f));
    effects.update(1.0f / 60.0f);
    CHECK(effects.particles()[0].position[0] == doctest::Approx(14.0f));
}

TEST_CASE("EffectSystem applies effect rotation to world-plane sprite bases")
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = std::make_shared<EffectDefinition>();
    definition->id = "test:world_plane";
    definition->durationSeconds = 1.0f;

    EffectSpriteDefinition sprite;
    sprite.componentId = 1;
    sprite.endSeconds = 1.0f;
    sprite.spriteResource = "test:sprite/fixed";
    sprite.alignment = EffectSpriteAlignment::WorldPlane;
    sprite.planeRight = {1.0f, 0.0f, 0.0f};
    sprite.planeUp = {0.0f, 0.0f, 1.0f};
    definition->sprites.push_back(sprite);

    EffectSpriteEmitterDefinition emitter;
    emitter.componentId = 2;
    emitter.endSeconds = 0.02f;
    emitter.spriteResource = "test:sprite/particle";
    emitter.emissionIntervalSeconds = 1.0f;
    emitter.particleLifetimeSeconds = 1.0f;
    emitter.particleSpace = EffectParticleSpace::Local;
    emitter.alignment = EffectSpriteAlignment::WorldPlane;
    emitter.planeRight = {1.0f, 0.0f, 0.0f};
    emitter.planeUp = {0.0f, 0.0f, 1.0f};
    definition->spriteEmitters.push_back(emitter);

    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(definition, error));
    EffectSystem effects(&library);
    const EffectHandle handle = effects.spawn(definition->id);
    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.particles().size(), 1);
    REQUIRE_EQ(effects.fixedSprites().size(), 1);
    CHECK_EQ(effects.particles()[0].planeRight, std::array<float, 3>{1.0f, 0.0f, 0.0f});
    CHECK_EQ(effects.fixedSprites()[0].planeUp, std::array<float, 3>{0.0f, 0.0f, 1.0f});

    const float halfRoot = std::sqrt(0.5f);
    REQUIRE(effects.setTransform(handle, {}, {0.0f, 0.0f, halfRoot, halfRoot}, 1.0f));
    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.particles().size(), 1);
    REQUIRE_EQ(effects.fixedSprites().size(), 1);
    CHECK(effects.particles()[0].planeRight[0] == doctest::Approx(0.0f).epsilon(0.0001));
    CHECK(effects.particles()[0].planeRight[1] == doctest::Approx(1.0f).epsilon(0.0001));
    CHECK(effects.fixedSprites()[0].planeRight[0] == doctest::Approx(0.0f).epsilon(0.0001));
    CHECK(effects.fixedSprites()[0].planeRight[1] == doctest::Approx(1.0f).epsilon(0.0001));
}

TEST_CASE("EffectSystem restart and seek rebuild deterministic instance state")
{
    using namespace OpenYAMM::Game;
    EffectLibrary library = makeLibrary();
    EffectSystem effects(&library);
    const EffectHandle handle = effects.spawn("test:fire", {.seed = 123});
    effects.consumeSoundEvents();
    effects.update(3.0f / 60.0f);
    REQUIRE_EQ(effects.particles().size(), 3);
    const std::array<float, 3> expectedPosition = effects.particles()[0].position;

    REQUIRE(effects.seek(handle, 3.0f / 60.0f));
    REQUIRE_EQ(effects.particles().size(), 3);
    CHECK(effects.elapsedSeconds(handle) == doctest::Approx(3.0f / 60.0f));
    CHECK_EQ(effects.particles()[0].position, expectedPosition);

    REQUIRE(effects.restart(handle));
    CHECK(effects.particles().empty());
    CHECK(effects.elapsedSeconds(handle) == doctest::Approx(0.0f));
}

TEST_CASE("EffectLibrary rejects non-finite fixed-sprite track values")
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = std::make_shared<EffectDefinition>();
    definition->id = "test:invalid_fixed_sprite";
    definition->durationSeconds = 1.0f;
    EffectSpriteDefinition sprite;
    sprite.componentId = 1;
    sprite.endSeconds = 1.0f;
    sprite.spriteResource = "test:sprite";
    sprite.scaleKeys.push_back({.time = 0.0f, .value = std::numeric_limits<float>::infinity()});
    definition->sprites.push_back(std::move(sprite));

    EffectLibrary library;
    std::string error;
    CHECK_FALSE(library.add(definition, error));
    CHECK(error.find("finite") != std::string::npos);

    std::shared_ptr<EffectDefinition> invalidPlane = std::make_shared<EffectDefinition>();
    invalidPlane->id = "test:invalid_sprite_plane";
    invalidPlane->durationSeconds = 1.0f;
    EffectSpriteDefinition planeSprite;
    planeSprite.componentId = 1;
    planeSprite.endSeconds = 1.0f;
    planeSprite.spriteResource = "test:sprite";
    planeSprite.alignment = EffectSpriteAlignment::WorldPlane;
    planeSprite.planeRight = {1.0f, 0.0f, 0.0f};
    planeSprite.planeUp = {2.0f, 0.0f, 0.0f};
    invalidPlane->sprites.push_back(planeSprite);
    error.clear();
    CHECK_FALSE(library.add(invalidPlane, error));
    CHECK(error.find("invalid sprite component") != std::string::npos);
}

TEST_CASE("EffectSystem clear tears down models particles sprites and sound ownership")
{
    using namespace OpenYAMM;
    std::shared_ptr<Game::EffectDefinition> definition = std::make_shared<Game::EffectDefinition>();
    definition->id = "test:teardown";
    definition->durationSeconds = 10.0f;
    definition->models.push_back({
        .componentId = 1,
        .startSeconds = 0.0f,
        .endSeconds = 10.0f,
        .modelResource = "test:model",
        .visible = true,
    });
    definition->sprites.push_back({
        .componentId = 2,
        .startSeconds = 0.0f,
        .endSeconds = 10.0f,
        .spriteResource = "test:sprite",
    });
    definition->spriteEmitters.push_back({
        .componentId = 3,
        .startSeconds = 0.0f,
        .endSeconds = 10.0f,
        .spriteResource = "test:particle",
        .emissionIntervalSeconds = 1.0f,
        .particleLifetimeSeconds = 10.0f,
    });
    definition->sounds.push_back({
        .componentId = 4,
        .startSeconds = 0.0f,
        .endSeconds = 10.0f,
        .soundResource = "test:sound",
        .loop = true,
    });

    Game::EffectLibrary library;
    std::string error;
    REQUIRE(library.add(definition, error));
    Engine::ModelInstanceSystem models;
    const std::shared_ptr<Engine::ModelAsset> modelAsset = std::make_shared<Engine::ModelAsset>();
    modelAsset->sourcePath = "test:model";
    Game::EffectSystem effects(&library);
    effects.setModelRuntime(
        &models,
        [&](const std::string &id)
        {
            return id == "test:model" ? modelAsset : nullptr;
        });

    const Game::EffectHandle handle = effects.spawn(definition->id);
    REQUIRE(effects.contains(handle));
    REQUIRE_EQ(models.size(), 1u);
    REQUIRE_EQ(effects.fixedSprites().size(), 1u);
    REQUIRE_EQ(effects.consumeSoundEvents().size(), 1u);
    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.particles().size(), 1u);

    effects.clear();
    CHECK_EQ(effects.size(), 0u);
    CHECK_EQ(models.size(), 0u);
    CHECK(effects.particles().empty());
    CHECK(effects.fixedSprites().empty());
    const std::vector<Game::EffectSoundEvent> teardownEvents = effects.consumeSoundEvents();
    REQUIRE_EQ(teardownEvents.size(), 1u);
    CHECK_EQ(teardownEvents.front().kind, Game::EffectSoundEventKind::Stop);
    CHECK_FALSE(effects.contains(handle));
}

namespace
{
std::shared_ptr<OpenYAMM::Game::EffectDefinition> makeRibbonDefinition()
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = std::make_shared<EffectDefinition>();
    definition->id = "test:bolt";
    definition->durationSeconds = 30.0f;
    EffectSpriteDefinition head;
    head.componentId = 1;
    head.endSeconds = 30.0f;
    head.spriteResource = "test:sprite/glow";
    head.alignment = EffectSpriteAlignment::Velocity;
    definition->sprites.push_back(head);
    EffectRibbonDefinition ribbon;
    ribbon.componentId = 2;
    ribbon.endSeconds = 30.0f;
    ribbon.spriteResource = "test:sprite/noise";
    ribbon.lifetimeSeconds = 0.5f;
    ribbon.maxLength = 100.0f;
    ribbon.sampleDistance = 10.0f;
    ribbon.width = 20.0f;
    ribbon.widthKeys = {{.time = 0.0f, .value = 1.0f}, {.time = 1.0f, .value = 0.0f}};
    ribbon.colorKeys = {{.time = 0.0f, .rgb = {255, 255, 255}, .transparency = 0}};
    definition->ribbons.push_back(ribbon);
    return definition;
}
}

TEST_CASE("EffectSystem ribbons sample the path by distance, cap their length and drain")
{
    using namespace OpenYAMM::Game;
    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(makeRibbonDefinition(), error));
    EffectSystem effects(&library);
    const EffectHandle handle = effects.spawn("test:bolt");
    REQUIRE(effects.contains(handle));
    CHECK(effects.activeSpriteResources() == std::vector<std::string>{"test:sprite/glow", "test:sprite/noise"});

    // 30 units per tick along +Y: one sample per tick, but never more than 100 units of trail.
    for (int tick = 1; tick <= 20; ++tick)
    {
        REQUIRE(effects.setTransform(handle, {0.0f, tick * 30.0f, 0.0f}, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f));
        effects.update(1.0f / 60.0f);
    }
    REQUIRE_EQ(effects.ribbons().size(), 1);
    const EffectRibbon &ribbon = effects.ribbons().front();
    REQUIRE(ribbon.points.size() >= 3);
    const EffectRibbonPoint &head = ribbon.points.back();
    CHECK(head.position[1] == doctest::Approx(600.0f));
    CHECK(head.phase == doctest::Approx(0.0f));
    CHECK(head.width == doctest::Approx(20.0f));
    CHECK(head.distance - ribbon.points.front().distance <= 100.0f + 30.0f);
    CHECK(ribbon.points.front().phase > 0.6f);
    for (size_t index = 1; index < ribbon.points.size(); ++index)
    {
        CHECK(ribbon.points[index].distance >= ribbon.points[index - 1].distance);
        CHECK(ribbon.points[index].phase <= ribbon.points[index - 1].phase);
    }

    // The velocity-aligned head follows the direction of travel.
    REQUIRE_EQ(effects.fixedSprites().size(), 1);
    CHECK(effects.fixedSprites()[0].planeRight[1] == doctest::Approx(1.0f));

    // Draining removes the head at once and freezes the trail, whose samples then age out.
    REQUIRE(effects.stop(handle, EffectStopMode::Drain));
    effects.update(1.0f / 60.0f);
    CHECK(effects.fixedSprites().empty());
    REQUIRE_EQ(effects.ribbons().size(), 1);
    CHECK(effects.ribbons().front().points.back().position[1] == doctest::Approx(600.0f));
    for (int tick = 0; tick < 40; ++tick)
    {
        effects.update(1.0f / 60.0f);
    }
    CHECK(effects.ribbons().empty());
    CHECK_FALSE(effects.contains(handle));
}

TEST_CASE("EffectSystem ribbon jitter leaves the head in place and is deterministic")
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = makeRibbonDefinition();
    definition->ribbons[0].jitter = 8.0f;
    definition->ribbons[0].jitterRate = 20.0f;
    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(definition, error));
    const auto run = [&]()
    {
        EffectSystem effects(&library);
        const EffectHandle handle = effects.spawn("test:bolt");
        for (int tick = 1; tick <= 6; ++tick)
        {
            effects.setTransform(handle, {tick * 15.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f);
            effects.update(1.0f / 60.0f);
        }
        std::vector<float> offsets;
        for (const EffectRibbonPoint &point : effects.ribbons().front().points)
        {
            offsets.push_back(point.jitterOffset);
        }
        return offsets;
    };
    const std::vector<float> first = run();
    REQUIRE(first.size() >= 3);
    CHECK(first.back() == doctest::Approx(0.0f));
    bool anyOffset = false;
    for (const float offset : first)
    {
        CHECK(std::abs(offset) <= 8.0f);
        anyOffset = anyOffset || std::abs(offset) > 0.01f;
    }
    CHECK(anyOffset);
    CHECK(run() == first);
}

TEST_CASE("EffectSystem distance emitters space particles along the path at any speed")
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = std::make_shared<EffectDefinition>();
    definition->id = "test:flame";
    definition->durationSeconds = 30.0f;
    EffectSpriteEmitterDefinition emitter;
    emitter.componentId = 1;
    emitter.endSeconds = 30.0f;
    emitter.spriteResource = "test:sprite/flame";
    emitter.emissionDistance = 10.0f;
    emitter.particleLifetimeSeconds = 2.0f;
    definition->spriteEmitters.push_back(emitter);
    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(definition, error));
    EffectSystem effects(&library);
    const EffectHandle handle = effects.spawn("test:flame");
    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.particles().size(), 1u);

    // A stationary emitter sheds nothing more.
    effects.update(1.0f / 60.0f);
    CHECK_EQ(effects.particles().size(), 1u);

    // 35 units per tick along +X: a particle every 10 units, each older the earlier on the path it was passed.
    for (int tick = 1; tick <= 6; ++tick)
    {
        REQUIRE(effects.setTransform(handle, {tick * 35.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f));
        effects.update(1.0f / 60.0f);
    }
    std::vector<EffectParticle> particles(effects.particles().begin(), effects.particles().end());
    REQUIRE_EQ(particles.size(), 22u);
    std::sort(
        particles.begin(),
        particles.end(),
        [](const EffectParticle &left, const EffectParticle &right)
        {
            return left.position[0] < right.position[0];
        });
    for (size_t index = 0; index < particles.size(); ++index)
    {
        CHECK(particles[index].position[0] == doctest::Approx(static_cast<float>(index) * 10.0f));
        if (index > 0)
        {
            CHECK(particles[index].ageSeconds < particles[index - 1].ageSeconds);
        }
    }

    // A jump of many spacings in one step is a teleport: the trail restarts there instead of filling the gap.
    REQUIRE(effects.setTransform(handle, {5000.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f));
    effects.update(1.0f / 60.0f);
    CHECK_EQ(effects.particles().size(), 22u);
    REQUIRE(effects.setTransform(handle, {5030.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f));
    effects.update(1.0f / 60.0f);
    CHECK_EQ(effects.particles().size(), 25u);
}

TEST_CASE("EffectSystem sprite systems can roll and spin their particles")
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = std::make_shared<EffectDefinition>();
    definition->id = "test:smoke";
    definition->durationSeconds = 30.0f;
    EffectSpriteEmitterDefinition emitter;
    emitter.componentId = 1;
    emitter.endSeconds = 30.0f;
    emitter.spriteResource = "test:sprite/smoke";
    emitter.spritesPerEmission = 16;
    emitter.emissionIntervalSeconds = 100.0f;
    emitter.particleLifetimeSeconds = 2.0f;
    emitter.randomRoll = true;
    emitter.spinSpeed = 4.0f;
    definition->spriteEmitters.push_back(emitter);
    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(definition, error));
    EffectSystem effects(&library);
    effects.spawn("test:smoke");
    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.particles().size(), 16u);
    std::vector<float> rolls;
    bool bothWays[2] = {false, false};
    for (const EffectParticle &particle : effects.particles())
    {
        CHECK(particle.roll >= -0.1f);
        CHECK(particle.roll <= 6.4f);
        CHECK(std::abs(particle.rollSpeed) >= 2.0f - 1.0e-4f);
        CHECK(std::abs(particle.rollSpeed) <= 4.0f + 1.0e-4f);
        bothWays[particle.rollSpeed > 0.0f ? 0 : 1] = true;
        rolls.push_back(particle.roll);
    }
    CHECK(bothWays[0]);
    CHECK(bothWays[1]);
    std::sort(rolls.begin(), rolls.end());
    CHECK(rolls.back() - rolls.front() > 1.0f);

    // Rolls turn at their own rate as the particles age.
    const std::vector<EffectParticle> before(effects.particles().begin(), effects.particles().end());
    for (int tick = 0; tick < 30; ++tick)
    {
        effects.update(1.0f / 60.0f);
    }
    for (size_t index = 0; index < before.size(); ++index)
    {
        const EffectParticle &after = effects.particles()[index];
        CHECK(after.roll - before[index].roll == doctest::Approx(before[index].rollSpeed * 0.5f).epsilon(0.02));
    }
}

TEST_CASE("EffectSystem beam ribbons run straight from the effect to its beam target and vanish when it stops")
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = std::make_shared<EffectDefinition>();
    definition->id = "test:beam";
    definition->durationSeconds = 30.0f;
    EffectRibbonDefinition ribbon;
    ribbon.componentId = 1;
    ribbon.endSeconds = 30.0f;
    ribbon.spriteResource = "test:sprite/noise";
    ribbon.lifetimeSeconds = 1.0f;
    ribbon.sampleDistance = 25.0f;
    ribbon.width = 10.0f;
    ribbon.jitter = 6.0f;
    ribbon.jitterRate = 20.0f;
    ribbon.beam = true;
    // Width keys run along a beam: full at its start, tapering to nothing at its target.
    ribbon.widthKeys = {{.time = 0.0f, .value = 1.0f}, {.time = 0.5f, .value = 1.0f}, {.time = 1.0f, .value = 0.0f}};
    ribbon.colorKeys = {{.time = 0.0f, .rgb = {255, 255, 255}, .transparency = 0}};
    definition->ribbons.push_back(ribbon);
    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(definition, error));
    EffectSystem effects(&library);
    EffectSpawnParams params;
    params.position = {100.0f, 0.0f, 50.0f};
    const EffectHandle handle = effects.spawn("test:beam", params);
    REQUIRE(effects.setBeamTarget(handle, {100.0f, 400.0f, 50.0f}));
    effects.update(1.0f / 60.0f);

    REQUIRE_EQ(effects.ribbons().size(), 1);
    const std::vector<EffectRibbonPoint> &points = effects.ribbons().front().points;
    // 400 units in samples of at most 25.
    REQUIRE_EQ(points.size(), 17u);
    CHECK(points.front().position[1] == doctest::Approx(0.0f));
    CHECK(points.back().position[1] == doctest::Approx(400.0f));
    CHECK(points.front().jitterOffset == 0.0f);
    CHECK(points.back().jitterOffset == 0.0f);
    CHECK(std::any_of(points.begin(), points.end(),
        [](const EffectRibbonPoint &point) { return point.jitterOffset != 0.0f; }));
    CHECK(points.front().width == doctest::Approx(10.0f));
    CHECK(points[8].width == doctest::Approx(10.0f));
    CHECK(points[12].width == doctest::Approx(5.0f));
    CHECK(points.back().width == doctest::Approx(0.0f));

    // The target moves and the effect with it: the beam follows, no trail.
    REQUIRE(effects.setTransform(handle, {0.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f));
    REQUIRE(effects.setBeamTarget(handle, {0.0f, 0.0f, 100.0f}));
    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.ribbons().size(), 1);
    CHECK_EQ(effects.ribbons().front().points.size(), 5u);
    CHECK(effects.ribbons().front().points.back().position[2] == doctest::Approx(100.0f));

    REQUIRE(effects.stop(handle, EffectStopMode::Drain));
    effects.update(1.0f / 60.0f);
    effects.update(1.0f / 60.0f);
    CHECK(effects.ribbons().empty());
}

TEST_CASE("EffectSystem spawn with a body anchor keeps only that anchor's emitters")
{
    using namespace OpenYAMM::Game;
    std::shared_ptr<EffectDefinition> definition = makeDefinition();
    definition->spriteEmitters.front().bodyAnchor = "left_hand";
    EffectSpriteEmitterDefinition right = definition->spriteEmitters.front();
    right.componentId = 7;
    right.bodyAnchor = "right_hand";
    definition->spriteEmitters.push_back(right);
    EffectLibrary library;
    std::string error;
    REQUIRE(library.add(definition, error));

    EffectSystem whole(&library);
    whole.spawn("test:fire");
    whole.update(1.0f / 60.0f);
    CHECK_EQ(whole.particles().size(), 2);

    EffectSystem split(&library);
    EffectSpawnParams params;
    params.bodyAnchor = "right_hand";
    const EffectHandle handle = split.spawn("test:fire", params);
    split.update(1.0f / 60.0f);
    REQUIRE_EQ(split.particles().size(), 1);
    CHECK_EQ(split.particles()[0].componentId, 7u);
    REQUIRE(split.restart(handle));
    split.update(1.0f / 60.0f);
    CHECK(std::all_of(split.particles().begin(), split.particles().end(),
        [](const EffectParticle &particle) { return particle.componentId == 7u; }));
}
