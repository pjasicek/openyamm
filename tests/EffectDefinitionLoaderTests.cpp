#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/TextTable.h"
#include "engine/models/GltfModelLoader.h"
#include "engine/render/CookedTexture.h"
#include "game/fx/EffectSystem.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ProjectileEffectBindings.h"
#include "game/fx/ProjectileModelBindings.h"
#include "game/fx/SpellAuraEffectBindings.h"
#include "game/fx/import/EffectDefinitionLoader.h"
#include "game/fx/import/EffectResourceLibrary.h"
#include "game/tables/ItemModelBindings.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <chrono>
#include <memory>
#include <set>
#include <sstream>
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
    // 42 of the 48 FXF groups (the six with visible deforming models are not imported), the melee blood and the
    // Sparks projectile explosion.
    REQUIRE_EQ(definitions->size(), 44);
    for (const std::string id : {"mm9:redyeldots", "mm9:LichKingRes", "mm9:skullcurse", "mm9:explosion_sparks"})
    {
        INFO(id);
        CHECK(std::any_of(definitions->begin(), definitions->end(),
            [&id](const std::shared_ptr<const Game::EffectDefinition> &definition)
            {
                return definition->id == id;
            }));
    }
    // A body-anchored recipe the scripts play (Wizard's Lab): both hand emitters at the effect's origin.
    const auto blueDotsIterator = std::find_if(definitions->begin(), definitions->end(),
        [](const std::shared_ptr<const Game::EffectDefinition> &definition)
        {
            return definition->id == "mm9:bluedots";
        });
    REQUIRE(blueDotsIterator != definitions->end());
    CHECK_EQ((*blueDotsIterator)->spriteEmitters.size(), 2);
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
    CHECK_EQ(resources.spriteCount(), 37); // The FXF sprites, the melee blood two and the explosion sphere.
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

    // Every imported recipe spawns: its sprites, sounds and model paths resolve (a model path plays the model's own
    // first clip, which is not always named after the model: pathup.abc's is wormpath).
    for (const std::shared_ptr<const Game::EffectDefinition> &definition : *definitions)
    {
        INFO(definition->id);
        for (const Game::EffectSpriteEmitterDefinition &emitter : definition->spriteEmitters)
        {
            CHECK(resources.findSprite(emitter.spriteResource) != nullptr);
        }
        for (const Game::EffectSpriteDefinition &sprite : definition->sprites)
        {
            CHECK(resources.findSprite(sprite.spriteResource) != nullptr);
        }
        const Game::EffectHandle spawned = effects.spawn(definition->id);
        CHECK(effects.contains(spawned));
        effects.update(0.5f);
        effects.stop(spawned, Game::EffectStopMode::Immediate);
    }
    CHECK_EQ(models.size(), 0);
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
        // Eighteen authored recipes (three showcase, three creature hand/staff emitters, the behaviour ward sparks,
        // five ground item sparkles, two beams, four destructibles breaking), the 122 generated projectile flight, settled, impact and aura
        // effects, the 63 melee effects (nine blows, three misses, 18 element accents, eleven material contacts in
        // three strengths), the MM8 wisp stars and the MM9 library.
        REQUIRE_EQ(definitions->size(), 248);
        Game::EffectLibrary library;
        REQUIRE(library.replace(*definitions, error));
        REQUIRE(library.find("mm9:spell_reaver") != nullptr);
        REQUIRE(library.find("openyamm:fx/creature_dark_staff") != nullptr);
        REQUIRE(library.find("openyamm:fx/energy_beam") != nullptr);
        CHECK(library.find("openyamm:fx/arc_beam")->ribbons.front().beam);
        Game::EffectResourceLibrary resources;
        Engine::ModelAssetCache models;
        REQUIRE(resources.load(assets, "engine/effects/resource_bindings.yml", *definitions, error, &models));
        REQUIRE(resources.findSprite("mm9:effect-sprite/fire/torchflame4") != nullptr);
        // MM9's additive light ignores the texture's alpha (LithTech ONE/ONE); OpenYAMM's effects keep it, also
        // where they draw MM9's sprites.
        for (const Game::EffectSpriteDefinition &sprite : library.find("mm9:sparklies")->sprites)
        {
            CHECK_FALSE(sprite.additiveTextureAlpha);
        }
        const Game::EffectDefinition &fireHand = *library.find("openyamm:fx/creature_fire_hand");
        CHECK_EQ(fireHand.spriteEmitters.front().spriteResource, "mm9:effect-sprite/weapons/firebolt");
        CHECK(fireHand.spriteEmitters.front().additiveTextureAlpha);
        CHECK(fireHand.sprites.front().additiveTextureAlpha);
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
        // Melee sprites are cooked atlases (tools/cook_effect_textures.py) whose size matches their descriptors.
        const Game::EffectSpriteResource *pArc = resources.findSprite("openyamm:effect-sprite/melee_arc");
        REQUIRE(pArc != nullptr);
        CHECK(pArc->framePaths.empty());
        CHECK_EQ(pArc->frameCount, 6);
        CHECK_EQ(pArc->atlasColumns, 3);
        const std::optional<std::vector<uint8_t>> atlasBytes = assets.readBinaryFile(pArc->atlasPath);
        REQUIRE(atlasBytes.has_value());
        const Engine::CookedTexture atlas = Engine::decodeCookedTexture(*atlasBytes);
        CHECK_EQ(atlas.codec, Engine::TextureBlockCodec::Bc7);
        CHECK_EQ(atlas.levels, 1);
        CHECK_EQ(atlas.width, 3 * pArc->frameWidth);
        CHECK_EQ(atlas.height, 2 * pArc->frameHeight);
        std::vector<std::string> meleeIds;
        for (const std::string name : {"slash", "thrust", "crush"})
        {
            for (const std::string suffix : {"_light", "", "_heavy", "_miss", "_element_fire", "_element_air",
                "_element_water", "_element_body", "_element_light", "_element_dark"})
            {
                meleeIds.push_back("openyamm:fx/melee/" + name + suffix);
            }
        }
        // Every material's contact effect exists (engine/data_tables/melee_hit_materials.txt).
        const std::optional<std::string> materials = assets.readTextFile("engine/data_tables/melee_hit_materials.txt");
        REQUIRE(materials.has_value());
        const std::optional<Engine::TextTable> materialTable = Engine::TextTable::parseTabSeparated(*materials);
        REQUIRE(materialTable.has_value());
        for (size_t row = 0; row < materialTable->getRowCount(); ++row)
        {
            const std::vector<std::string> &cells = materialTable->getRow(row);
            if (cells.size() > 5 && !cells[0].empty() && cells[0][0] != '#' && !cells[5].empty())
            {
                for (const std::string suffix : {"_light", "", "_heavy"})
                {
                    meleeIds.push_back(cells[5] + suffix);
                }
            }
        }
        for (const std::string &id : meleeIds)
        {
            {
                CAPTURE(id);
                Game::EffectSystem system(&library);
                const Game::EffectHandle handle = system.spawn(id);
                REQUIRE(system.contains(handle));
                system.update(1.0f / 60.0f);
                CHECK((!system.fixedSprites().empty() || !system.particles().empty()));
                for (const Game::EffectFixedSprite &sprite : system.fixedSprites())
                {
                    CHECK(resources.findSprite(std::string(sprite.spriteResource)) != nullptr);
                }
                for (const Game::EffectParticle &particle : system.particles())
                {
                    CHECK(resources.findSprite(std::string(particle.spriteResource)) != nullptr);
                }
                for (uint32_t tick = 0; tick < 70; ++tick)
                {
                    system.update(1.0f / 60.0f);
                }
                CHECK_FALSE(system.contains(handle));
            }
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

TEST_CASE("EffectDefinitionLoader parses ribbons, velocity-aligned sprites and distance emitters")
{
    using namespace OpenYAMM::Game;
    std::string error;
    const std::optional<std::vector<std::shared_ptr<const EffectDefinition>>> parsed = EffectDefinitionLoader::parse(R"(
schema: openyamm.effectLibrary.v1
effects:
  - id: test:bolt
    duration_seconds: 30
    compatibility_profile: predictable
    components:
      - {id: 1, type: sprite, start_seconds: 0, end_seconds: 30, sprite_resource: test:glow, alignment: velocity,
         stretch_u: 2, color_keys: [], scale_keys: [], motion_keys: []}
      - id: 2
        type: ribbon
        start_seconds: 0
        end_seconds: 30
        sprite_resource: test:noise
        lifetime_seconds: 0.25
        max_length: 200
        width: 30
        fill: 0
        erosion: 0.5
        jitter: 6
        jitter_rate: 20
        beam: true
        width_keys: [{time: 0, value: 1}, {time: 1, value: 0.2}]
        color_keys: [{time: 0, rgb: [255, 200, 100], transparency: 0}]
      - {id: 3, type: sprite_system, start_seconds: 0, end_seconds: 30, sprite_resource: test:flame,
         emission_shape: point, emission_distance: 12, particle_lifetime_seconds: 0.2, random_roll: true,
         spin_speed: 2.5, color_keys: [], scale_keys: [], motion_keys: []}
)", error);
    INFO(error);
    REQUIRE(parsed.has_value());
    const EffectDefinition &definition = *parsed->front();
    REQUIRE_EQ(definition.sprites.size(), 1);
    CHECK_EQ(definition.sprites[0].alignment, EffectSpriteAlignment::Velocity);
    REQUIRE_EQ(definition.ribbons.size(), 1);
    const EffectRibbonDefinition &ribbon = definition.ribbons[0];
    CHECK_EQ(ribbon.blendMode, EffectBlendMode::Additive);
    CHECK(ribbon.maxLength == doctest::Approx(200.0f));
    CHECK(ribbon.fill == doctest::Approx(0.0f));
    CHECK(ribbon.jitter == doctest::Approx(6.0f));
    CHECK(ribbon.beam);
    CHECK_EQ(ribbon.widthKeys.size(), 2);
    REQUIRE_EQ(definition.spriteEmitters.size(), 1);
    CHECK(definition.spriteEmitters[0].emissionDistance == doctest::Approx(12.0f));
    CHECK(definition.spriteEmitters[0].randomRoll);
    CHECK(definition.spriteEmitters[0].spinSpeed == doctest::Approx(2.5f));

    EffectLibrary library;
    std::shared_ptr<EffectDefinition> broken = std::make_shared<EffectDefinition>(definition);
    broken->id = "test:broken";
    broken->ribbons[0].erosion = 1.5f;
    CHECK_FALSE(library.add(broken, error));
    CHECK(error.find("ribbon component 2") != std::string::npos);

    // Distance emission follows the emitter through the world, so it cannot shed in local space.
    std::shared_ptr<EffectDefinition> local = std::make_shared<EffectDefinition>(definition);
    local->id = "test:local";
    local->spriteEmitters[0].particleSpace = EffectParticleSpace::Local;
    CHECK_FALSE(library.add(local, error));
    CHECK(error.find("sprite component 3") != std::string::npos);
}

TEST_CASE("Projectile effect bindings name existing effects and resolve monster variants")
{
    using namespace OpenYAMM;
    using Game::FxRecipes::ProjectileRecipe;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    Game::EffectDefinitionLoader loader(&assets);
    std::string error;
    const auto definitions = loader.load("engine/effects/library.yml", error);
    REQUIRE_MESSAGE(definitions.has_value(), error);
    Game::EffectLibrary library;
    REQUIRE(library.replace(*definitions, error));
    Game::ProjectileEffectBindings bindings;
    REQUIRE_MESSAGE(Game::loadProjectileEffectBindings(assets, "engine/effects/projectiles.yml", library, bindings,
        error), error);
    const Game::ProjectileEffectBinding *pFireBolt = bindings.find(ProjectileRecipe::FireBolt, "");
    REQUIRE(pFireBolt != nullptr);
    CHECK_EQ(pFireBolt->flight, "openyamm:fx/projectile/fire_bolt");
    CHECK_EQ(pFireBolt->impact, "openyamm:fx/impact/fire_small");
    CHECK(bindings.contains(ProjectileRecipe::MindBlast));
    CHECK(bindings.contains(ProjectileRecipe::Sparks));
    CHECK(bindings.contains(ProjectileRecipe::Arrow));
    CHECK_FALSE(bindings.contains(ProjectileRecipe::Stun));
    const Game::ProjectileEffectBinding *pSwarm = bindings.find(ProjectileRecipe::DeadlySwarm, "");
    REQUIRE(pSwarm != nullptr);
    REQUIRE(pSwarm->nativeSprite.has_value());
    CHECK_FALSE(*pSwarm->nativeSprite);
    CHECK(pSwarm->impactFollowsTarget);
    const Game::ProjectileEffectBinding *pSoulDrinker = bindings.find(ProjectileRecipe::SoulDrinker, "");
    REQUIRE(pSoulDrinker != nullptr);
    CHECK_EQ(pSoulDrinker->returnFlight, "openyamm:fx/projectile/soul_drain");
    const std::vector<std::string> effectIds = bindings.effectIds();
    CHECK(std::find(effectIds.begin(), effectIds.end(), "openyamm:fx/projectile/soul_drain") != effectIds.end());
    for (const ProjectileRecipe recipe : {ProjectileRecipe::Implosion, ProjectileRecipe::Inferno,
             ProjectileRecipe::Immolation, ProjectileRecipe::MassDistortion, ProjectileRecipe::SpiritLash,
             ProjectileRecipe::PrismaticLight, ProjectileRecipe::Lifedrain, ProjectileRecipe::ShrinkingRay,
             ProjectileRecipe::Armageddon, ProjectileRecipe::FireTrap, ProjectileRecipe::ElecTrap,
             ProjectileRecipe::ColdTrap, ProjectileRecipe::PoisonTrap})
    {
        INFO(Game::FxRecipes::projectileRecipeName(recipe));
        const Game::ProjectileEffectBinding *pBinding = bindings.find(recipe, "");
        REQUIRE(pBinding != nullptr);
        CHECK_FALSE(pBinding->impact.empty());
    }
    CHECK_FALSE(bindings.find(ProjectileRecipe::ShrinkingRay, "")->flight.empty());

    // Spell auras: each kind has a default, spells may override it, and every aura effect is bound.
    Game::SpellAuraEffectBindings auras;
    REQUIRE_MESSAGE(Game::loadSpellAuraEffectBindings(assets, "engine/effects/spell_auras.yml", library, auras, error),
        error);
    CHECK_EQ(auras.find(Game::SpellAuraKind::CreatureDebuff, 34), "openyamm:fx/aura/stun");
    CHECK_EQ(auras.find(Game::SpellAuraKind::CreatureDebuff, 59), "openyamm:fx/aura/debuff");
    CHECK_EQ(auras.find(Game::SpellAuraKind::PartyBuff, 17), "openyamm:fx/aura/party_ward");
    CHECK_EQ(auras.find(Game::SpellAuraKind::CreatureBuff, 17), "openyamm:fx/aura/shield");
    CHECK_EQ(auras.find(Game::SpellAuraKind::Heal, 68), "openyamm:fx/aura/heal");
    std::set<std::string> boundAuras;
    for (const std::string &id : auras.effectIds())
    {
        boundAuras.insert(id);
    }
    for (const auto &definition : *definitions)
    {
        if (definition->id.starts_with("openyamm:fx/aura/"))
        {
            INFO(definition->id);
            CHECK(boundAuras.contains(definition->id));
        }
    }
    const auto parseAuras = [&](const std::string &body)
    {
        Game::SpellAuraEffectBindings parsed;
        return Game::parseSpellAuraEffectBindings(
            "schema: openyamm.spellAuraEffects.v1\n" + body, "test.yml", library, parsed, error);
    };
    CHECK(parseAuras("defaults: {heal: openyamm:fx/aura/heal}\n"));
    CHECK_FALSE(parseAuras("defaults: {cure: openyamm:fx/aura/heal}\n"));
    CHECK_FALSE(parseAuras("spells: {34: {creature_debuff: openyamm:fx/aura/missing}}\n"));
    CHECK_FALSE(parseAuras("spells: {0: {heal: openyamm:fx/aura/heal}}\n"));
    CHECK_FALSE(parseAuras("extra: 1\n"));
    const Game::ProjectileEffectBinding *pFireSpike = bindings.find(ProjectileRecipe::FireSpike, "");
    REQUIRE(pFireSpike != nullptr);
    CHECK_EQ(pFireSpike->settled, "openyamm:fx/projectile/fire_spike_mine");

    // A monster variant overrides the recipe's fields for the monsters it names (any case), and only for them.
    const Game::ProjectileEffectBinding *pSpat = bindings.find(ProjectileRecipe::MonsterFireBolt, "Lich A");
    const Game::ProjectileEffectBinding *pDragon = bindings.find(ProjectileRecipe::MonsterFireBolt, "dragon a");
    REQUIRE(pSpat != nullptr);
    REQUIRE(pDragon != nullptr);
    CHECK_EQ(pSpat->flight, "openyamm:fx/projectile/monster_fire_bolt");
    CHECK_EQ(pDragon->flight, "openyamm:fx/projectile/dragon_fire");
    CHECK_EQ(pDragon->impact, "openyamm:fx/impact/fire_large");
    REQUIRE(pDragon->light.has_value());
    CHECK(pDragon->light->radius == doctest::Approx(260.0f));
    const Game::ProjectileEffectBinding *pLiving =
        bindings.find(ProjectileRecipe::MonsterFireBolt, "Elemental Fire C");
    REQUIRE(pLiving != nullptr);
    CHECK_EQ(pLiving->flight, "openyamm:fx/projectile/living_flame");
    CHECK_EQ(pLiving->impact, "openyamm:fx/impact/fire_small");
    CHECK_EQ(bindings.find(ProjectileRecipe::Blaster, "Robot A")->flight, "openyamm:fx/projectile/blaster");

    // Every monster a variant names exists in the merged monster table (its Picture column).
    std::ifstream monsterData(sourceRoot / "assets_dev/engine/data_tables/monster_data.txt");
    REQUIRE(monsterData.good());
    std::set<std::string> pictures;
    std::string line;
    while (std::getline(monsterData, line))
    {
        std::vector<std::string> columns;
        std::stringstream row(line);
        std::string column;
        while (std::getline(row, column, '\t'))
        {
            columns.push_back(column);
        }
        if (columns.size() > 2)
        {
            pictures.insert(Game::ProjectileEffectBindings::normalizeMonsterPicture(columns[2]));
        }
    }
    for (const std::string &picture : bindings.variantMonsterPictures())
    {
        INFO(picture);
        CHECK(pictures.contains(picture));
    }

    Game::ProjectileEffectBindings none;
    CHECK(Game::loadProjectileEffectBindings(assets, "engine/effects/missing_projectiles.yml", library, none, error));
    CHECK(none.empty());
    Game::EffectLibrary empty;
    CHECK_FALSE(Game::loadProjectileEffectBindings(assets, "engine/effects/projectiles.yml", empty, none, error));
    CHECK(error.find("unknown water_splash effect") != std::string::npos);
    const auto parse = [&](const std::string &projectiles)
    {
        Game::ProjectileEffectBindings parsed;
        return Game::parseProjectileEffectBindings(
            "schema: openyamm.projectileEffects.v1\nprojectiles:\n" + projectiles, "test", library, parsed, error);
    };
    CHECK(parse("  fire_bolt: {impact: openyamm:fx/impact/fireball, sprite: hidden}\n"));
    CHECK_FALSE(parse("  fire_bolt: {flihgt: openyamm:fx/projectile/fire_bolt}\n"));
    CHECK(error.find("unknown key flihgt") != std::string::npos);
    CHECK_FALSE(parse("  fire_bolt: {flight: openyamm:fx/projectile/fire_bolt, sprite: shown}\n"));
    CHECK(parse("  fire_bolt: {sprite: hidden}\n"));
    CHECK_FALSE(parse("  fire_bolt: {impact_follows_target: true}\n"));
    CHECK_FALSE(parse("  fire_bolt: {flight: openyamm:fx/projectile/fire_bolt, light: {rgb: [1, 2], radius: 5}}\n"));
    CHECK_FALSE(parse("  fire_bolt: {flight: openyamm:fx/projectile/fire_bolt, variants: [{flight: x}]}\n"));

    // Every bound flight and settled effect draws while it moves, then drains completely once stopped; every
    // impact plays out and finishes on its own.
    std::set<std::string> flights;
    std::set<std::string> impacts;
    for (const auto &definition : *definitions)
    {
        if (definition->id.starts_with("openyamm:fx/projectile/"))
        {
            flights.insert(definition->id);
        }
        // Auras play out and finish on their own, as impacts do.
        else if (definition->id.starts_with("openyamm:fx/impact/") || definition->id.starts_with("openyamm:fx/aura/"))
        {
            impacts.insert(definition->id);
        }
    }
    CHECK_EQ(flights.size(), 50);
    CHECK_EQ(impacts.size(), 72);
    for (const std::string &id : impacts)
    {
        INFO(id);
        Game::EffectSystem effects(&library);
        const Game::EffectHandle handle = effects.spawn(id);
        REQUIRE(effects.contains(handle));
        bool drew = false;
        for (int tick = 0; tick < 60 * 4 && effects.contains(handle); ++tick)
        {
            effects.update(1.0f / 60.0f);
            drew = drew || !effects.fixedSprites().empty() || !effects.particles().empty();
        }
        CHECK(drew);
        CHECK_FALSE(effects.contains(handle));
        CHECK(effects.particles().empty());
    }
    // Each flight effect draws a trail (a ribbon or shed particles) while it moves, then drains completely once
    // stopped.
    for (const std::string &id : flights)
    {
        Game::EffectSystem effects(&library);
        const Game::EffectHandle handle = effects.spawn(id);
        REQUIRE(effects.contains(handle));
        for (int tick = 1; tick <= 30; ++tick)
        {
            REQUIRE(effects.setTransform(handle, {tick * 40.0f, 0.0f, 100.0f}, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f));
            effects.update(1.0f / 60.0f);
        }
        INFO(id);
        CHECK((!effects.ribbons().empty() || effects.particles().size() >= 5));
        CHECK((!effects.fixedSprites().empty() || !effects.ribbons().empty()));
        effects.stop(handle, Game::EffectStopMode::Drain);
        for (int tick = 0; tick < 120; ++tick)
        {
            effects.update(1.0f / 60.0f);
        }
        CHECK_FALSE(effects.contains(handle));
        CHECK(effects.ribbons().empty());
        CHECK(effects.particles().empty());
    }
}

TEST_CASE("Projectile model bindings parse object ids, models and lengths")
{
    using namespace OpenYAMM;
    std::string error;
    Game::ProjectileModelBindings bindings;
    const auto parse = [&](const std::string &projectiles)
    {
        bindings.clear();
        return Game::parseProjectileModelBindings(
            "schema: openyamm.projectileModels.v1\nprojectiles:\n" + projectiles, "test", bindings, error);
    };
    REQUIRE(parse("  - {object: 545, model: engine/models/projectile_arrow.glb, length: 130}\n"));
    REQUIRE(bindings.contains(545));
    CHECK_EQ(bindings.at(545).model, "engine/models/projectile_arrow.glb");
    CHECK_EQ(bindings.at(545).length, doctest::Approx(130.0f));
    REQUIRE(parse("  - {object: 4070, model: a.glb, length: 85, spin: {axis: side, degrees_per_second: -540}}\n"));
    CHECK(bindings.at(4070).spinAxis == Game::ProjectileModelSpinAxis::Side);
    CHECK_EQ(bindings.at(4070).spinDegreesPerSecond, doctest::Approx(-540.0f));
    CHECK_FALSE(parse("  - {object: 545, model: a.glb, length: 130, spin: 3}\n"));
    CHECK_FALSE(parse("  - {object: 545, model: a.glb, length: 130, spin: {axis: roll, degrees_per_second: 3}}\n"));
    CHECK_FALSE(parse("  - {object: 545, model: a.glb, length: 130, tint: 3}\n"));
    CHECK(error.find("unknown key tint") != std::string::npos);
    CHECK_FALSE(parse("  - {object: 545, model: a.glb}\n"));
    CHECK_FALSE(parse("  - {object: 545, model: a.glb, length: 0}\n"));
    CHECK_FALSE(parse("  - {object: 0, model: a.glb, length: 10}\n"));
    CHECK_FALSE(parse("  - {object: 545, model: a.glb, length: 10}\n  - {object: 545, model: b.glb, length: 10}\n"));
    CHECK(error.find("bound twice") != std::string::npos);
}

TEST_CASE("Projectile model bindings name installed models")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    Game::ProjectileModelBindings bindings;
    std::string error;
    REQUIRE_MESSAGE(Game::loadProjectileModelBindings(
        assetFileSystem, "engine/models/projectiles.yml", bindings, error), error);
    CHECK(bindings.contains(545));
    for (const auto &[objectId, binding] : bindings)
    {
        INFO("object " << objectId << ": " << binding.model);
        CHECK(assetFileSystem.exists(binding.model));
    }
}

TEST_CASE("Item model bindings parse icons and name installed models")
{
    using namespace OpenYAMM;
    std::string error;
    Game::ItemModelBindings bindings;
    REQUIRE(Game::parseItemModelBindings("schema: openyamm.itemModels.v1\nitems:\n"
        "  - {icon: LSword1, model: engine/models/item_lsword1.glb, length: 129, bounds: [-9, -64.5, 0, 9, 64.5, 12]}\n",
        "test", bindings, error));
    REQUIRE(bindings.contains("lsword1"));
    CHECK_EQ(bindings.at("lsword1").length, doctest::Approx(129.0f));
    CHECK_EQ(bindings.at("lsword1").boundsMin[1], doctest::Approx(-64.5f));
    CHECK_EQ(bindings.at("lsword1").boundsMax[2], doctest::Approx(12.0f));
    bindings.clear();
    CHECK_FALSE(Game::parseItemModelBindings("schema: openyamm.itemModels.v1\nitems:\n"
        "  - {icon: a, model: a.glb, length: 1, bounds: [0, 0, 0, 1, 1, 1], tint: 2}\n", "test", bindings, error));
    bindings.clear();
    CHECK_FALSE(Game::parseItemModelBindings("schema: openyamm.itemModels.v1\nitems:\n"
        "  - {icon: a, model: a.glb, length: 1}\n", "test", bindings, error));
    CHECK(error.find("bounds") != std::string::npos);
    bindings.clear();
    CHECK_FALSE(Game::parseItemModelBindings("schema: openyamm.itemModels.v1\nitems:\n"
        "  - {icon: a, model: a.glb, length: 1, bounds: [0, 0, 0, -1, 1, 1]}\n", "test", bindings, error));
    bindings.clear();
    CHECK_FALSE(Game::parseItemModelBindings("schema: openyamm.itemModels.v1\nitems:\n"
        "  - {icon: a, model: a.glb, length: 1, bounds: [0, 0, 0, 1, 1, 1]}\n"
        "  - {icon: A, model: b.glb, length: 1, bounds: [0, 0, 0, 1, 1, 1]}\n", "test", bindings, error));
    CHECK(error.find("bound twice") != std::string::npos);
    // A world's own bindings (worlds/<id>/world_items/items.yml) add to the engine's; an icon bound in both fails.
    bindings.clear();
    REQUIRE(Game::parseItemModelBindings("schema: openyamm.itemModels.v1\nitems:\n"
        "  - {icon: a, model: a.glb, length: 1, bounds: [0, 0, 0, 1, 1, 1]}\n", "engine", bindings, error));
    REQUIRE(Game::parseItemModelBindings("schema: openyamm.itemModels.v1\nitems:\n"
        "  - {icon: mm9_item_10002, model: worlds/mm9/world_items/models/b.glb, length: 1, bounds: [0, 0, 0, 1, 1, 1]}\n",
        "world", bindings, error));
    CHECK(bindings.size() == 2);
    CHECK_FALSE(Game::parseItemModelBindings("schema: openyamm.itemModels.v1\nitems:\n"
        "  - {icon: A, model: c.glb, length: 1, bounds: [0, 0, 0, 1, 1, 1]}\n", "world", bindings, error));
    CHECK(error.find("bound twice") != std::string::npos);

    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm6"));
    bindings.clear();
    CHECK_FALSE(Game::loadItemModelBindings(assetFileSystem, "engine/world_items/missing.yml", bindings, error));
    Game::ItemModelBindings installed;
    REQUIRE_MESSAGE(Game::loadItemModelBindings(assetFileSystem, "engine/world_items/items.yml", installed, error), error);
    for (const auto &[icon, binding] : installed)
    {
        INFO(icon << ": " << binding.model);
        CHECK(assetFileSystem.exists(binding.model));
    }
    CHECK(assetFileSystem.exists(Game::missingItemModelBinding().model));
}
