#include "doctest/doctest.h"

#include "game/gameplay/GameplayProjectileService.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"

#include <string>
#include <vector>

using namespace OpenYAMM::Game;

TEST_CASE("indoor scene destructibles parse, sorted by id")
{
    const std::string yaml = R"(
- {id: 41, name: glass1, cog: 20041, hp: 1, sound: Events/glass_smash.wav, effect: openyamm:fx/destructible/glass,
   effect_scale: 0.75, center: [10, 20, 30], destroyed_event: 340}
- {id: 7, name: Crate2, decoration_cog: 407, hp: 100, damage_enabled: false, trigger_destroy_only: true,
   damaged_event: 341}
)";
    std::vector<IndoorDestructible> destructibles;
    std::string error;
    REQUIRE_MESSAGE(parseIndoorSceneDestructibles(yaml, destructibles, error), error);
    REQUIRE(destructibles.size() == 2);

    const IndoorDestructible &crate = destructibles[0];
    CHECK(crate.id == 7);
    CHECK(crate.cog == 0);
    CHECK(crate.decorationCog == 407);
    CHECK(crate.hp == 100);
    CHECK_FALSE(crate.damageEnabled);
    CHECK(crate.triggerDestroyOnly);
    CHECK(crate.damagedEvent == 341);
    CHECK(crate.effect.empty());

    const IndoorDestructible &glass = destructibles[1];
    CHECK(glass.id == 41);
    CHECK(glass.name == "glass1");
    CHECK(glass.cog == 20041);
    CHECK(glass.damageEnabled);
    CHECK_FALSE(glass.triggerDestroyOnly);
    CHECK(glass.sound == "Events/glass_smash.wav");
    CHECK(glass.effect == "openyamm:fx/destructible/glass");
    CHECK(glass.effectScale == doctest::Approx(0.75f));
    CHECK(glass.center[0] == doctest::Approx(10.0f));
    CHECK(glass.center[2] == doctest::Approx(30.0f));
    CHECK(glass.destroyedEvent == 340);
}

TEST_CASE("indoor scene destructibles reject bad entries")
{
    std::vector<IndoorDestructible> destructibles;
    std::string error;
    CHECK_FALSE(parseIndoorSceneDestructibles("- {id: 1, hp: 5}", destructibles, error));
    CHECK_FALSE(parseIndoorSceneDestructibles("- {id: 1, cog: 3, hp: 0}", destructibles, error));
    CHECK_FALSE(parseIndoorSceneDestructibles("- {id: 1, cog: 3, colour: red}", destructibles, error));
    CHECK_FALSE(parseIndoorSceneDestructibles("- {id: 1, cog: 3}\n- {id: 1, cog: 4}", destructibles, error));
    CHECK_FALSE(parseIndoorSceneDestructibles("{id: 1, cog: 3}", destructibles, error));
}

TEST_CASE("indoor scene pulsing lights parse")
{
    const std::string yaml = R"(
- {key: 40007, position: [1, 2, 3], color: [255, 172, 47], intensity: [0.3, 1, 3, 0], radius: [128, 512, 4, 0.25],
   start_on: false}
)";
    std::vector<IndoorPulsingLight> lights;
    std::string error;
    REQUIRE_MESSAGE(parseIndoorScenePulsingLights(yaml, lights, error), error);
    REQUIRE(lights.size() == 1);
    CHECK(lights[0].lightKey == 40007);
    CHECK(lights[0].color[1] == 172);
    CHECK(lights[0].intensity[0] == doctest::Approx(0.3f));
    CHECK(lights[0].radius[1] == doctest::Approx(512.0f));
    CHECK(lights[0].radius[3] == doctest::Approx(0.25f));
    CHECK_FALSE(lights[0].startOn);

    CHECK_FALSE(parseIndoorScenePulsingLights("- {key: 1, position: [0, 0, 0], color: [1, 2, 3], intensity: [1, 1, 0, 0], "
                                              "radius: [0, 0, 0, 0]}", lights, error));
    CHECK_FALSE(parseIndoorScenePulsingLights("- {key: 1, position: [0, 0, 0], color: [1, 2], intensity: [1, 1, 0, 0], "
                                              "radius: [1, 2, 0, 0]}", lights, error));
}

TEST_CASE("an area impact damages the destructibles its radius reaches, by their boxes")
{
    using Service = GameplayProjectileService;
    Service::ProjectileState fireball = {};
    fireball.sourceKind = Service::ProjectileState::SourceKind::Party;
    fireball.damage = 30;
    const auto box = [](uint32_t id, float x, bool direct = false)
    {
        Service::ProjectileAreaImpactDestructibleFacts fact = {};
        fact.id = id;
        fact.boundsMin = {x, -50.0f, 0.0f};
        fact.boundsMax = {x + 100.0f, 50.0f, 200.0f};
        fact.directImpact = direct;
        return fact;
    };
    // A wall face starting 400 from the blast, a barrel at 700, the struck board, a box beyond reach above.
    std::vector<Service::ProjectileAreaImpactDestructibleFacts> destructibles = {
        box(1, 400.0f), box(2, 700.0f), box(3, -50.0f, true), box(4, 100.0f)};
    destructibles[3].boundsMin.z = 700.0f;
    destructibles[3].boundsMax.z = 800.0f;

    const std::vector<Service::ProjectileAreaImpactDestructibleHit> hits =
        Service::buildProjectileAreaDestructibleHits(fireball, {0.0f, 0.0f, 100.0f}, 512.0f, 0, destructibles);
    REQUIRE_EQ(hits.size(), 1u);
    CHECK_EQ(hits[0].id, 1u);
    CHECK_EQ(hits[0].damage, 30);

    // An event's blast deals its own damage; a monster's breaks nothing; no radius, nothing.
    Service::ProjectileState trap = fireball;
    trap.sourceKind = Service::ProjectileState::SourceKind::Event;
    const std::vector<Service::ProjectileAreaImpactDestructibleHit> trapHits =
        Service::buildProjectileAreaDestructibleHits(trap, {0.0f, 0.0f, 100.0f}, 512.0f, 12, destructibles);
    REQUIRE_EQ(trapHits.size(), 1u);
    CHECK_EQ(trapHits[0].damage, 12);
    Service::ProjectileState monsterBlast = fireball;
    monsterBlast.sourceKind = Service::ProjectileState::SourceKind::Actor;
    CHECK(Service::buildProjectileAreaDestructibleHits(
        monsterBlast, {0.0f, 0.0f, 100.0f}, 512.0f, 12, destructibles).empty());
    CHECK(Service::buildProjectileAreaDestructibleHits(fireball, {0.0f, 0.0f, 100.0f}, 0.0f, 0, destructibles).empty());
}
