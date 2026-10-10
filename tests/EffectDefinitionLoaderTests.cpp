#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/models/GltfModelLoader.h"
#include "game/fx/EffectSystem.h"
#include "game/fx/import/EffectDefinitionLoader.h"
#include "game/fx/import/EffectResourceLibrary.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <chrono>
#include <memory>
#include <string>
#include <vector>

TEST_CASE("EffectDefinitionLoader loads shared MM9-derived effects for any active world")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        Engine::AssetScaleTier::X1,
        "mm6"));

    Game::EffectDefinitionLoader loader(&assetFileSystem);
    std::string error;
    const std::optional<std::vector<std::shared_ptr<const Game::EffectDefinition>>> definitions =
        loader.load("engine/effects/mm9/library.yml", error);
    INFO(error);
    REQUIRE(definitions.has_value());
    REQUIRE_EQ(definitions->size(), 37);
    const auto columnIterator = std::find_if(
        definitions->begin(),
        definitions->end(),
        [](const std::shared_ptr<const Game::EffectDefinition> &definition)
        {
            return definition->id == "mm9:column_of_fire";
        });
    REQUIRE(columnIterator != definitions->end());
    const Game::EffectDefinition &column = **columnIterator;
    CHECK_EQ(column.id, "mm9:column_of_fire");
    CHECK(column.durationSeconds == doctest::Approx(3.5f));
    CHECK_EQ(column.timingProfile, Game::EffectTimingProfile::Mm9Native);
    REQUIRE_EQ(column.spriteEmitters.size(), 4);
    REQUIRE_EQ(column.sounds.size(), 1);
    CHECK_EQ(column.spriteEmitters[0].emissionShape, Game::EffectEmissionShape::PlaneIn);
    CHECK_EQ(column.spriteEmitters[2].emissionShape, Game::EffectEmissionShape::Plane);
    CHECK_EQ(column.spriteEmitters[3].emissionShape, Game::EffectEmissionShape::Sphere);
    CHECK_EQ(column.sounds[0].soundResource, "mm9:sound/spells/column03");

    const auto fireflyIterator = std::find_if(
        definitions->begin(),
        definitions->end(),
        [](const std::shared_ptr<const Game::EffectDefinition> &definition)
        {
            return definition->id == "mm9:firefly";
        });
    REQUIRE(fireflyIterator != definitions->end());
    const Game::EffectDefinition &firefly = **fireflyIterator;
    REQUIRE_EQ(firefly.models.size(), 1);
    REQUIRE_EQ(firefly.sprites.size(), 1);
    CHECK_EQ(firefly.models[0].modelResource, "mm9:model/spells/bugpath");
    CHECK_FALSE(firefly.models[0].visible);
    REQUIRE(firefly.sprites[0].link.componentId.has_value());
    CHECK_EQ(*firefly.sprites[0].link.componentId, 15);
    CHECK_EQ(firefly.sprites[0].link.nodeName, "Xend");

    const auto elementalIterator = std::find_if(
        definitions->begin(),
        definitions->end(),
        [](const std::shared_ptr<const Game::EffectDefinition> &definition)
        {
            return definition->id == "mm9:elemental_blast";
        });
    REQUIRE(elementalIterator != definitions->end());
    REQUIRE_EQ((*elementalIterator)->nulls.size(), 1);
    CHECK_EQ((*elementalIterator)->nulls[0].componentId, 6);

    const auto spellReaverIterator = std::find_if(
        definitions->begin(),
        definitions->end(),
        [](const std::shared_ptr<const Game::EffectDefinition> &definition)
        {
            return definition->id == "mm9:spell_reaver";
        });
    REQUIRE(spellReaverIterator != definitions->end());
    const Game::EffectDefinition &spellReaver = **spellReaverIterator;
    REQUIRE_EQ(spellReaver.spriteEmitters.size(), 3);
    REQUIRE_EQ(spellReaver.sprites.size(), 1);
    REQUIRE_EQ(spellReaver.sounds.size(), 1);
    CHECK_EQ(spellReaver.sounds[0].soundResource, "mm9:sound/spells/spellreaver");
    CHECK_EQ(spellReaver.spriteEmitters[0].alignment, Game::EffectSpriteAlignment::WorldPlane);
    CHECK_EQ(spellReaver.spriteEmitters[0].planeRight, std::array<float, 3>{0.0f, 1.0f, 0.0f});
    CHECK_EQ(spellReaver.spriteEmitters[0].planeUp, std::array<float, 3>{1.0f, 0.0f, 0.0f});
    CHECK_EQ(spellReaver.spriteEmitters[1].alignment, Game::EffectSpriteAlignment::CameraFacing);
    CHECK_EQ(spellReaver.sprites[0].alignment, Game::EffectSpriteAlignment::WorldPlane);
    CHECK_EQ(spellReaver.sprites[0].planeRight, std::array<float, 3>{0.0f, 1.0f, 0.0f});
    CHECK_EQ(spellReaver.sprites[0].planeUp, std::array<float, 3>{1.0f, 0.0f, 0.0f});

    const auto townPortalIterator = std::find_if(
        definitions->begin(),
        definitions->end(),
        [](const std::shared_ptr<const Game::EffectDefinition> &definition)
        {
            return definition->id == "mm9:town_portal";
        });
    REQUIRE(townPortalIterator != definitions->end());
    const Game::EffectDefinition &townPortal = **townPortalIterator;
    REQUIRE_EQ(townPortal.spriteEmitters.size(), 2);
    REQUIRE_EQ(townPortal.sprites.size(), 1);
    CHECK_EQ(townPortal.spriteEmitters[0].alignment, Game::EffectSpriteAlignment::WorldPlane);
    CHECK_EQ(townPortal.spriteEmitters[0].planeRight, std::array<float, 3>{1.0f, 0.0f, 0.0f});
    CHECK_EQ(townPortal.spriteEmitters[0].planeUp, std::array<float, 3>{0.0f, 0.0f, 1.0f});

    size_t worldPlaneComponents = 0;
    for (const std::shared_ptr<const Game::EffectDefinition> &definition : *definitions)
    {
        worldPlaneComponents += static_cast<size_t>(std::count_if(
            definition->spriteEmitters.begin(),
            definition->spriteEmitters.end(),
            [](const Game::EffectSpriteEmitterDefinition &emitter)
            {
                return emitter.alignment == Game::EffectSpriteAlignment::WorldPlane;
            }));
        worldPlaneComponents += static_cast<size_t>(std::count_if(
            definition->sprites.begin(),
            definition->sprites.end(),
            [](const Game::EffectSpriteDefinition &sprite)
            {
                return sprite.alignment == Game::EffectSpriteAlignment::WorldPlane;
            }));
    }
    CHECK_EQ(worldPlaneComponents, 12);

    Game::EffectResourceLibrary resources;
    Engine::ModelAssetCache modelAssets;
    REQUIRE(resources.load(
        assetFileSystem,
        "engine/effects/mm9/resource_bindings.yml",
        *definitions,
        error,
        &modelAssets));
    CHECK_EQ(resources.spriteCount(), 36);
    const Game::EffectSpriteResource *pSprite =
        resources.findSprite("mm9:effect-sprite/fire/torchflame4");
    REQUIRE(pSprite != nullptr);
    CHECK_EQ(pSprite->framesPerSecond, 15);
    CHECK_EQ(pSprite->logicalWidth, 64);
    CHECK_EQ(pSprite->logicalHeight, 64);
    CHECK_EQ(pSprite->framePaths.size(), 15);
    CHECK(resources.findAssetPath("mm9:sound/spells/column03") ==
        std::optional<std::string>("engine/effects/mm9/audio/spells/column03.wav"));

    const Game::EffectSpriteResource *pBloodHit =
        resources.findSprite("mm9:effect-sprite/bloodhit1");
    REQUIRE(pBloodHit != nullptr);
    CHECK_EQ(pBloodHit->logicalWidth, 32);
    CHECK_EQ(pBloodHit->logicalHeight, 32);
    const Game::EffectSpriteResource *pBloodSpray =
        resources.findSprite("mm9:effect-sprite/bloodspray1");
    REQUIRE(pBloodSpray != nullptr);
    CHECK_EQ(pBloodSpray->logicalWidth, 16);
    CHECK_EQ(pBloodSpray->logicalHeight, 16);

    Game::EffectLibrary library;
    REQUIRE(library.replace(*definitions, error));
    Game::EffectSystem effects(&library);
    Engine::ModelInstanceSystem models;
    effects.setModelRuntime(
        &models,
        [&](const std::string &id)
        {
            return resources.findModel(id);
        });
    const Game::EffectHandle handle = effects.spawn("mm9:column_of_fire");
    REQUIRE(effects.contains(handle));
    effects.update(1.0f / 60.0f);
    CHECK_EQ(effects.particles().size(), 2);

    const Game::EffectHandle bloodHandle = effects.spawn("mm9:melee_blood");
    REQUIRE(effects.contains(bloodHandle));
    REQUIRE_EQ(effects.fixedSprites().size(), 1);
    effects.update(2.0f / 60.0f);
    CHECK_EQ(static_cast<size_t>(std::count_if(
        effects.particles().begin(),
        effects.particles().end(),
        [&](const Game::EffectParticle &particle)
        {
            return particle.owner == bloodHandle;
        })), 10);
    REQUIRE(effects.stop(bloodHandle, Game::EffectStopMode::Immediate));

    const Game::EffectHandle fireflyHandle = effects.spawn("mm9:firefly");
    REQUIRE(effects.contains(fireflyHandle));
    REQUIRE_EQ(models.size(), 1);
    REQUIRE_EQ(effects.fixedSprites().size(), 1);
    const std::array<float, 3> initialPosition = effects.fixedSprites()[0].position;
    const std::vector<Engine::ModelInstanceHandle> modelHandles = models.handles();
    REQUIRE_EQ(modelHandles.size(), 1);
    const Engine::ModelMatrix *pEndMatrix = models.nodeMatrix(modelHandles[0], "Xend");
    REQUIRE(pEndMatrix != nullptr);
    REQUIRE_FALSE(firefly.sprites[0].motionKeys.empty());
    for (size_t axis = 0; axis < 3; ++axis)
    {
        const float expected = (*pEndMatrix)[12 + axis] + firefly.sprites[0].offset[axis] +
            firefly.sprites[0].motionKeys.front().value[axis];
        CHECK(initialPosition[axis] == doctest::Approx(expected));
    }
    effects.update(1.0f / 60.0f);
    REQUIRE_EQ(effects.fixedSprites().size(), 1);
    CHECK(effects.fixedSprites()[0].position != initialPosition);
    REQUIRE(effects.stop(fireflyHandle, Game::EffectStopMode::Immediate));
    CHECK_EQ(models.size(), 0);
    CHECK(effects.fixedSprites().empty());
}

TEST_CASE("EffectDefinitionLoader rejects unsupported components and duplicate ids atomically")
{
    using namespace OpenYAMM::Game;
    std::string error;
    const std::optional<std::vector<std::shared_ptr<const EffectDefinition>>> unsupported =
        EffectDefinitionLoader::parse(R"(
schema: openyamm.effectLibrary.v1
effects:
  - id: test:bad
    duration_seconds: 1
    compatibility_profile: predictable
    components:
      - type: deforming_mesh
)", error);
    CHECK_FALSE(unsupported.has_value());
    CHECK(error.find("unsupported effect component") != std::string::npos);

    std::shared_ptr<EffectDefinition> original = std::make_shared<EffectDefinition>();
    original->id = "test:original";
    original->durationSeconds = 1.0f;
    EffectLibrary library;
    REQUIRE(library.add(original, error));

    std::shared_ptr<EffectDefinition> duplicate = std::make_shared<EffectDefinition>();
    duplicate->id = "test:duplicate";
    duplicate->durationSeconds = 1.0f;
    const std::vector<std::shared_ptr<const EffectDefinition>> replacements = {duplicate, duplicate};
    CHECK_FALSE(library.replace(replacements, error));
    CHECK_EQ(library.size(), 1);
    CHECK(library.find("test:original") != nullptr);
}

TEST_CASE("EffectDefinitionLoader composes authored showcase with MM9 for all legacy worlds")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    for (const std::string world : {"mm6", "mm7", "mm8"})
    {
        Engine::AssetFileSystem assets;
        REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, world));
        Game::EffectDefinitionLoader loader(&assets);
        std::string error;
        const auto definitions = loader.load("engine/effects/library.yml", error);
        INFO(world, ": ", error);
        REQUIRE(definitions.has_value());
        // Five authored recipes (three showcase, two creature hand/staff emitters) and the MM9 library.
        REQUIRE_EQ(definitions->size(), 42);
        Game::EffectLibrary library;
        REQUIRE(library.replace(*definitions, error));
        REQUIRE(library.find("mm9:spell_reaver") != nullptr);
        REQUIRE(library.find("openyamm:fx/creature_dark_staff") != nullptr);
        Game::EffectResourceLibrary resources;
        Engine::ModelAssetCache models;
        REQUIRE(resources.load(assets, "engine/effects/resource_bindings.yml", *definitions, error, &models));
        REQUIRE(resources.findSprite("mm9:effect-sprite/fire/torchflame4") != nullptr);
        const Game::EffectSpriteResource *pFire = resources.findSprite("openyamm:effect-sprite/fireball");
        REQUIRE(pFire != nullptr);
        CHECK_EQ(pFire->framePaths.size(), 16);
        for (const std::string id : {"openyamm:fx/healing_bloom", "openyamm:fx/ember_impact",
            "openyamm:fx/arcane_pulse"})
        {
            Game::EffectSystem system(&library);
            const Game::EffectHandle handle = system.spawn(id);
            REQUIRE(system.contains(handle));
            CHECK_EQ(library.find(id)->timingProfile, Game::EffectTimingProfile::Predictable);
            system.update(1.0f / 60.0f);
            CHECK_FALSE(system.particles().empty());
            CHECK_FALSE(system.fixedSprites().empty());
            for (uint32_t tick = 0; tick < 300; ++tick)
            {
                system.update(1.0f / 60.0f);
            }
            CHECK_FALSE(system.contains(handle));
            CHECK(system.particles().empty());
            CHECK(system.fixedSprites().empty());
        }
    }
}

TEST_CASE("EffectDefinitionLoader rejects broken imports and resource collisions without replacing resources")
{
    using namespace OpenYAMM;
    struct TemporaryFiles
    {
        std::filesystem::path root = std::filesystem::temp_directory_path() /
            ("openyamm_fx_imports_" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        ~TemporaryFiles() { std::filesystem::remove_all(root); }
    } files;
    const std::filesystem::path directory = files.root / "engine/effects";
    std::filesystem::create_directories(directory);
    const auto write = [&](const std::string &name, const std::string &text)
    {
        std::ofstream stream(directory / name);
        stream << text;
    };
    write("root.yml", "schema: openyamm.effectLibrary.v1\nimports: [engine/effects/root.yml]\neffects: []\n");
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(OPENYAMM_SOURCE_DIR, files.root, Engine::AssetScaleTier::X1, "mm6"));
    Game::EffectDefinitionLoader loader(&assets);
    std::string error;
    CHECK_FALSE(loader.load("engine/effects/root.yml", error));
    CHECK(error.find("repeated effect library") != std::string::npos);
    write("root.yml", "schema: openyamm.effectLibrary.v1\nimports: [engine/effects/missing.yml]\neffects: []\n");
    error.clear();
    CHECK_FALSE(loader.load("engine/effects/root.yml", error));
    CHECK(error.find("failed to read") != std::string::npos);
    const std::string effect = "effects: [{id: test:duplicate, duration_seconds: 1, "
        "compatibility_profile: predictable, components: []}]\n";
    write("child.yml", "schema: openyamm.effectLibrary.v1\n" + effect);
    write("root.yml", "schema: openyamm.effectLibrary.v1\nimports: [engine/effects/child.yml]\n" + effect);
    error.clear();
    CHECK_FALSE(loader.load("engine/effects/root.yml", error));
    CHECK(error.find("duplicate") != std::string::npos);

    const std::string resource = "bindings: [{resource: 'test:frame', asset: test.png, status: bound}]\n";
    write("bindings.yml", "schema: openyamm.effectResourceBindings.v1\n" + resource);
    Game::EffectResourceLibrary resources;
    error.clear();
    REQUIRE(resources.load(assets, "engine/effects/bindings.yml", {}, error));
    write("child.yml", "schema: openyamm.effectResourceBindings.v1\n" + resource);
    write("bindings.yml", "schema: openyamm.effectResourceBindings.v1\nimports: [engine/effects/child.yml]\n" + resource);
    CHECK_FALSE(resources.load(assets, "engine/effects/bindings.yml", {}, error));
    CHECK(error.find("duplicate effect resource") != std::string::npos);
    CHECK(resources.findAssetPath("test:frame") == std::optional<std::string>("test.png"));
    write("bindings.yml", "schema: openyamm.effectResourceBindings.v1\nimports: [engine/effects/bindings.yml]\nbindings: []\n");
    error.clear();
    CHECK_FALSE(resources.load(assets, "engine/effects/bindings.yml", {}, error));
    CHECK(error.find("repeated effect resource") != std::string::npos);
    CHECK(resources.findAssetPath("test:frame") == std::optional<std::string>("test.png"));
}
