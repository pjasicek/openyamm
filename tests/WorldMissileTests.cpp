#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/data/GameDataLoader.h"
#include "game/fx/EffectSystem.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ProjectileEffectBindings.h"
#include "game/fx/import/EffectDefinitionLoader.h"
#include "game/tables/MonsterProjectileTable.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/ObjectTable.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <filesystem>
#include <sstream>
#include <string>
#include <vector>

using namespace OpenYAMM;
using namespace OpenYAMM::Game;
using FxRecipes::ProjectileRecipe;

namespace
{
const char *HesperMissiles = R"(schema: openyamm.monsterProjectiles.v1
missiles:
  HesBolt: {object: 21000, impact_object: 556, tier: classic_blaster}
  KrPlasma: {object: 21011, impact_object: 556, tier: kreegan_energy}
  CrawlerAcid: {object: 21030, impact_object: 0}
)";

MonsterProjectileTable engineMissiles()
{
    MonsterProjectileTable table;
    REQUIRE(table.loadFromRows({{"Token", "ObjectId", "ImpactObjectId"}, {"Ener", "555", "556"},
        {"Body", "520", "0"}}));
    return table;
}

std::vector<std::string> tabRow(const std::string &line)
{
    std::vector<std::string> cells;
    std::stringstream stream(line);
    std::string cell;
    while (std::getline(stream, cell, '\t'))
    {
        cells.push_back(cell);
    }
    return cells;
}
}

TEST_CASE("world missile tokens load within the world's objects range and leave MM's tokens alone")
{
    MonsterProjectileTable table = engineMissiles();
    std::string error;
    REQUIRE_MESSAGE(table.loadWorldYaml(HesperMissiles, "hesper", 21000, 21999, error), error);
    CHECK_EQ(table.entries().size(), 5);

    const MonsterProjectileEntry *pBolt = table.findByToken("hesbolt");
    REQUIRE(pBolt != nullptr);
    CHECK_EQ(pBolt->objectId, 21000);
    CHECK_EQ(pBolt->impactObjectId, 556);
    REQUIRE(pBolt->shieldTier.has_value());
    CHECK(*pBolt->shieldTier == ShieldAttackTier::ClassicBlaster);
    CHECK(*table.findByToken("KrPlasma")->shieldTier == ShieldAttackTier::KreeganEnergy);
    // Without a tier a missile follows its attack's damage type, as MM's do.
    CHECK_FALSE(table.findByToken("CrawlerAcid")->shieldTier.has_value());
    const MonsterProjectileEntry *pEner = table.findByToken("Ener");
    REQUIRE(pEner != nullptr);
    CHECK_EQ(pEner->objectId, 555);
    CHECK_FALSE(pEner->shieldTier.has_value());

    const auto rejects = [&](const std::string &missiles, const char *pReason)
    {
        MonsterProjectileTable fresh = engineMissiles();
        std::string reason;
        CHECK_FALSE(fresh.loadWorldYaml("schema: openyamm.monsterProjectiles.v1\nmissiles:\n" + missiles, "hesper",
            21000, 21999, reason));
        INFO(reason);
        CHECK(reason.find(pReason) != std::string::npos);
        CHECK_EQ(fresh.entries().size(), 2);
        CHECK_EQ(fresh.findByToken("Ener")->objectId, 555);
    };
    rejects("  ener: {object: 21000}\n", "a missile token must be a new name");
    rejects("  HesBolt: {object: 21000}\n  hesbolt: {object: 21001}\n", "a missile token must be a new name");
    rejects("  HesBolt: {object: 555}\n", "outside the world's objects range");
    rejects("  HesBolt: {object: 21000, tier: laser}\n", "tier must be");
    rejects("  HesBolt: {object: 21000, speed: 9000}\n", "unknown key speed");
    MonsterProjectileTable fresh = engineMissiles();
    CHECK_FALSE(fresh.loadWorldYaml("missiles: {}\n", "hesper", 21000, 21999, error));
}

TEST_CASE("a world's party guns fire their own missiles and shot sounds; other guns keep MM's bolt")
{
    MonsterProjectileTable table = engineMissiles();
    std::string error;
    REQUIRE_MESSAGE(table.loadWorldYaml(std::string(HesperMissiles)
        + "party:\n  11000: {missile: KrPlasma, shot_sound_id: 60010}\n  11420: {missile: Ener}\n",
        "hesper", 21000, 21999, error), error);

    const std::optional<PartyGunMissile> pistol = table.findPartyGun(11000);
    REQUIRE(pistol.has_value());
    CHECK_EQ(pistol->pMissile->objectId, 21011);
    CHECK_EQ(pistol->shotSoundId, 60010);
    const std::optional<PartyGunMissile> repeater = table.findPartyGun(11420);
    REQUIRE(repeater.has_value());
    CHECK_EQ(repeater->pMissile->objectId, 555);
    CHECK_EQ(repeater->shotSoundId, 0);
    CHECK_FALSE(table.findPartyGun(64).has_value());

    MonsterProjectileTable unknown = engineMissiles();
    CHECK_FALSE(unknown.loadWorldYaml(std::string(HesperMissiles) + "party:\n  11000: {missile: Nope}\n",
        "hesper", 21000, 21999, error));
    CHECK(error.find("unknown missile Nope") != std::string::npos);
    CHECK_EQ(unknown.entries().size(), 2);
}

TEST_CASE("a monster naming a world missile token gets its ranged attack; MM's tokens are unchanged")
{
    // The draft rows' layout: attack 1 type, dice, missile in columns 17-19, attack 2 chance, type, dice, missile in
    // 20-23. A Trooper with its rifle butt, an MM-style robot and a melee brute.
    const std::string trooper = "10010\tTrooper\thes_trooper\t100\t1300\t70\t16000\t0\t1\tN\tMed\tNormal\t4\t250\t50\t0"
        "\t0\tEner\t6D8+20\tKrPlasma\t30\tPhys\t3D10+15\t0\t0\t0\t0\t0\tImm\t30\t30\t30\tImm\t30\t30\t30\t30\t10\t0";
    const std::string robot = "200\tRobot\tRobot A\t20\t100\t10\t500\t0\t0\tN\tMed\tNormal\t4\t250\t50\t0"
        "\t0\tEner\t2D8\tEner\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0";
    const std::string brute = "10001\tBrute\thes_brute\t85\t1100\t60\t1000\t0\t1\tN\tMed\tNormal\t4\t250\t50\t0"
        "\t0\tPhys\t4D10\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0";
    MonsterTable table;
    REQUIRE(table.loadStatsFromRows({tabRow(trooper), tabRow(robot), tabRow(brute)}));
    REQUIRE(table.findStatsById(10010) != nullptr);
    CHECK_FALSE(table.findStatsById(10010)->attack1HasMissile);
    CHECK(table.findStatsById(200)->attack1HasMissile);
    const MonsterTable::MonsterAttackStyle robotStyle = table.findStatsById(200)->attackStyle;

    table.acceptWorldMissileTokens({});
    CHECK_FALSE(table.findStatsById(10010)->attack1HasMissile);
    table.acceptWorldMissileTokens({"krplasma", "HesBolt"});
    const MonsterTable::MonsterStatsEntry &stats = *table.findStatsById(10010);
    CHECK(stats.attack1HasMissile);
    CHECK_FALSE(stats.attack2HasMissile);
    CHECK(stats.attackStyle == MonsterTable::MonsterAttackStyle::Ranged);
    CHECK_EQ(stats.attack1MissileType, "KrPlasma");
    CHECK(table.findStatsById(200)->attackStyle == robotStyle);
    CHECK_FALSE(table.findStatsById(10001)->attack1HasMissile);
    CHECK(table.findStatsById(10001)->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly);
}

TEST_CASE("MM's monster missiles load as before without a world add-on")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    for (const char *pWorld : {"mm6", "mm8"})
    {
        INFO(pWorld);
        Engine::AssetFileSystem assets;
        REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, pWorld));
        GameDataLoader data;
        REQUIRE(data.loadForHeadlessGameplay(assets));
        const MonsterProjectileTable &missiles = data.getMonsterProjectileTable();
        CHECK_EQ(missiles.entries().size(), 20);
        for (const MonsterProjectileEntry &entry : missiles.entries())
        {
            INFO(entry.token);
            CHECK_FALSE(entry.shieldTier.has_value());
            CHECK(entry.objectId < 21000);
        }
        CHECK_EQ(missiles.findByToken("Ener")->objectId, 555);
        CHECK_EQ(missiles.findByToken("Ener")->impactObjectId, 556);
        CHECK(data.getObjectTable().findByObjectId(21000) == nullptr);
    }
}

TEST_CASE("projectile bindings by object name win over the recipe and its monster variants")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm8"));
    EffectDefinitionLoader loader(&assets);
    std::string error;
    const auto definitions = loader.load("engine/effects/library.yml", error);
    REQUIRE_MESSAGE(definitions.has_value(), error);
    EffectLibrary library;
    REQUIRE(library.replace(*definitions, error));

    // MM's file has no objects: lookups with an object name are what they were without one.
    ProjectileEffectBindings engine;
    REQUIRE_MESSAGE(loadProjectileEffectBindings(assets, "engine/effects/projectiles.yml", library, engine, error),
        error);
    CHECK(engine.objectNames().empty());
    CHECK_EQ(engine.find(ProjectileRecipe::Blaster, "Robot A", "Laser"), engine.find(ProjectileRecipe::Blaster, "Robot A"));
    CHECK_EQ(engine.find(ProjectileRecipe::Blaster, "Crystal Dragon A", "Laser")->flight,
        "openyamm:fx/projectile/energy_breath");
    CHECK_FALSE(engine.find(ProjectileRecipe::Blaster, "")->impactLight.has_value());

    const auto parse = [&](const std::string &objects, ProjectileEffectBindings &bindings)
    {
        return parseProjectileEffectBindings("schema: openyamm.projectileEffects.v1\nprojectiles:\n"
            "  blaster:\n    flight: openyamm:fx/projectile/blaster\n    impact: openyamm:fx/impact/blaster\n"
            "    variants:\n      - monsters: [Crystal Dragon A]\n        flight: openyamm:fx/projectile/energy_breath\n"
            "objects:\n" + objects, "test", library, bindings, error);
    };
    ProjectileEffectBindings bindings;
    REQUIRE_MESSAGE(parse("  hes_bolt: {flight: openyamm:fx/projectile/air_bolt, impact: openyamm:fx/impact/air_small,"
        " sprite: hidden, light: {rgb: [110, 175, 255], radius: 170}, impact_light: {rgb: [120, 180, 255], "
        "radius: 256}}\n", bindings), error);
    CHECK_EQ(bindings.objectNames(), std::vector<std::string>{"hes_bolt"});
    for (const char *pPicture : {"", "Crystal Dragon A", "hes_ward_turret"})
    {
        INFO(pPicture);
        const ProjectileEffectBinding *pBolt = bindings.find(ProjectileRecipe::Blaster, pPicture, "HES_Bolt");
        REQUIRE(pBolt != nullptr);
        CHECK_EQ(pBolt->flight, "openyamm:fx/projectile/air_bolt");
        CHECK_EQ(pBolt->impact, "openyamm:fx/impact/air_small");
        REQUIRE(pBolt->impactLight.has_value());
        CHECK(pBolt->impactLight->radius == doctest::Approx(256.0f));
        CHECK_EQ(pBolt->impactLight->rgb[2], 255);
        REQUIRE(pBolt->nativeSprite.has_value());
        CHECK_FALSE(*pBolt->nativeSprite);
    }
    // Any recipe: the object decides.
    CHECK_EQ(bindings.find(ProjectileRecipe::MonsterBodyBolt, "", "hes_bolt")->flight,
        "openyamm:fx/projectile/air_bolt");
    CHECK_EQ(bindings.find(ProjectileRecipe::Blaster, "Crystal Dragon A", "Laser")->flight,
        "openyamm:fx/projectile/energy_breath");
    CHECK_EQ(bindings.find(ProjectileRecipe::Blaster, "", "Laser")->flight, "openyamm:fx/projectile/blaster");
    const std::vector<std::string> ids = bindings.effectIds();
    CHECK(std::find(ids.begin(), ids.end(), "openyamm:fx/impact/air_small") != ids.end());

    ProjectileEffectBindings rejected;
    CHECK_FALSE(parse("  hes_bolt: {flight: openyamm:fx/projectile/air_bolt}\n", rejected));
    CHECK(error.find("names a flight and an impact") != std::string::npos);
    CHECK_FALSE(parse("  hes_bolt: {flight: openyamm:fx/projectile/air_bolt, impact: openyamm:fx/impact/air_small, "
        "variants: []}\n", rejected));
    CHECK(error.find("unknown key variants") != std::string::npos);
    CHECK_FALSE(parse("  hes_bolt: {flight: openyamm:fx/projectile/missing, impact: openyamm:fx/impact/air_small}\n",
        rejected));
    CHECK_FALSE(parse("  hes_bolt: {flight: openyamm:fx/projectile/air_bolt, impact: openyamm:fx/impact/air_small, "
        "impact_light: {rgb: [1, 2], radius: 5}}\n", rejected));
    // impact_light belongs to object bindings only: MM's recipe entries keep their recipe's impact light.
    ProjectileEffectBindings recipeLight;
    CHECK_FALSE(parseProjectileEffectBindings("schema: openyamm.projectileEffects.v1\nprojectiles:\n"
        "  blaster: {flight: openyamm:fx/projectile/blaster, impact_light: {rgb: [1, 2, 3], radius: 5}}\n", "test",
        library, recipeLight, error));
}

// The staged Hesper world (level_generation/projects/hesper_stage/stage.py, output/hesper_stage): its missiles merge
// into the engine's, their objects and effect bindings exist, every flight draws a trail and drains, every impact
// finishes. Skipped when no stage has been built (it is git-ignored).
TEST_CASE("the staged Hesper missiles resolve to their objects, tiers and effects")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path stage = sourceRoot / "output/hesper_stage/assets_editor_dev";
    if (!std::filesystem::exists(stage / "worlds/hesper/monster_projectiles.yml"))
    {
        MESSAGE("no Hesper stage with missiles; skipped");
        return;
    }
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, stage, Engine::AssetScaleTier::X1, "hesper"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    const MonsterProjectileTable &missiles = data.getMonsterProjectileTable();
    CHECK_EQ(missiles.findByToken("Ener")->objectId, 555);

    EffectDefinitionLoader loader(&assets);
    std::string error;
    const auto definitions = loader.load("engine/effects/library.yml", error);
    REQUIRE_MESSAGE(definitions.has_value(), error);
    EffectLibrary library;
    REQUIRE(library.replace(*definitions, error));
    ProjectileEffectBindings bindings;
    REQUIRE_MESSAGE(loadProjectileEffectBindings(assets, "engine/effects/projectiles.yml", library, bindings, error),
        error);

    size_t worldMissiles = 0;
    for (const MonsterProjectileEntry &entry : missiles.entries())
    {
        if (entry.objectId < 21000)
        {
            CHECK_FALSE(entry.shieldTier.has_value());
            continue;
        }
        INFO(entry.token);
        ++worldMissiles;
        CHECK(entry.objectId <= 21999);
        const ObjectEntry *pObject = data.getObjectTable().findByObjectId(int16_t(entry.objectId));
        REQUIRE(pObject != nullptr);
        CHECK(data.getObjectTable().findByObjectId(int16_t(entry.impactObjectId)) != nullptr);
        const ProjectileRecipe recipe =
            FxRecipes::classifyProjectileRecipe(0, pObject->internalName, pObject->spriteName, pObject->flags);
        CHECK(recipe == ProjectileRecipe::Blaster);
        const ProjectileEffectBinding *pBinding = bindings.find(recipe, "", pObject->internalName);
        REQUIRE(pBinding != nullptr);
        CHECK(pBinding->flight.starts_with("hesper:fx/projectile/"));
        CHECK(pBinding->impact.starts_with("hesper:fx/impact/"));
        CHECK(pBinding->light.has_value());
        CHECK(pBinding->impactLight.has_value());
    }
    CHECK_EQ(worldMissiles, bindings.objectNames().size());
    CHECK(worldMissiles >= 9);

    // Every staged monster whose row names a world missile fires it.
    size_t rangedHesper = 0;
    for (const auto &[id, stats] : data.getMonsterTable().statsEntries())
    {
        for (const auto &[token, hasMissile] : {std::pair{stats.attack1MissileType, stats.attack1HasMissile},
                 std::pair{stats.attack2MissileType, stats.attack2HasMissile}})
        {
            const MonsterProjectileEntry *pEntry = missiles.findByToken(token);
            if (pEntry != nullptr && pEntry->objectId >= 21000)
            {
                INFO(stats.name);
                CHECK(hasMissile);
                ++rangedHesper;
            }
        }
    }
    CHECK(rangedHesper > 0);

    for (const auto &definition : *definitions)
    {
        if (!definition->id.starts_with("hesper:fx/"))
        {
            continue;
        }
        INFO(definition->id);
        EffectSystem effects(&library);
        const EffectHandle handle = effects.spawn(definition->id);
        REQUIRE(effects.contains(handle));
        if (definition->id.starts_with("hesper:fx/projectile/"))
        {
            for (int tick = 1; tick <= 30; ++tick)
            {
                REQUIRE(effects.setTransform(handle, {tick * 40.0f, 0.0f, 100.0f}, {0.0f, 0.0f, 0.0f, 1.0f}, 1.0f));
                effects.update(1.0f / 60.0f);
            }
            CHECK((!effects.ribbons().empty() || effects.particles().size() >= 5));
            effects.stop(handle, EffectStopMode::Drain);
            for (int tick = 0; tick < 120; ++tick)
            {
                effects.update(1.0f / 60.0f);
            }
        }
        else
        {
            // A beam (hesper:fx/beam/...) lasts until its script stops it.
            if (definition->id.starts_with("hesper:fx/beam/"))
            {
                effects.stop(handle, EffectStopMode::Drain);
            }
            for (int tick = 0; tick < 60 * 4 && effects.contains(handle); ++tick)
            {
                effects.update(1.0f / 60.0f);
            }
        }
        CHECK_FALSE(effects.contains(handle));
        CHECK(effects.particles().empty());
    }
}
