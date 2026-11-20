#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/SpellIds.h"
#include "game/scene/IndoorSceneRuntime.h"

#include <array>
#include <cmath>
#include <filesystem>
#include <limits>
#include <optional>
#include <set>
#include <utility>

using namespace OpenYAMM::Game;

namespace
{
constexpr float Step = 1.0f / 128.0f;

struct OutdoorFixture
{
    OpenYAMM::Engine::AssetFileSystem assets;
    GameDataLoader data;
    MonsterTable monsters;
    GameplayProjectileService projectiles;
    std::optional<OutdoorWorldRuntime> world;
    const MapAssetInfo *pMap = nullptr;

    bool load(const char *pWorld, const char *pMapFile)
    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        if (!assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, pWorld)
            || !data.loadForHeadlessGameplay(assets) || !data.loadMapByFileNameForHeadlessGameplay(assets, pMapFile))
        {
            return false;
        }
        pMap = &*data.getSelectedMap();
        monsters = data.getMonsterTable();
        return pMap->outdoorMapData.has_value();
    }

    void start()
    {
        world.emplace();
        world->initialize(pMap->map, monsters, data.getMonsterProjectileTable(), data.getObjectTable(),
            data.getSpellTable(), data.getItemTable(), nullptr, nullptr, data.getStandardItemEnchantTable(),
            data.getSpecialItemEnchantTable(), &data.getChestTable(), pMap->outdoorMapData, std::nullopt,
            std::nullopt, std::nullopt, std::nullopt, std::nullopt, pMap->outdoorDecorationCollisionSet,
            std::nullopt, std::nullopt, std::nullopt, nullptr, &projectiles);
    }

    float ground(float x, float y) const
    {
        return sampleOutdoorTerrainHeight(*pMap->outdoorMapData, x, y);
    }
};

// A building with open ground on two sides: a source off one side, a party spot in the open off to the source's side
// and one hidden behind the building.
struct Bounds
{
    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();
};

Bounds boundsOf(const OutdoorBModel &bModel)
{
    Bounds bounds;

    for (const OutdoorBModelVertex &vertex : bModel.vertices)
    {
        bounds.minX = std::min(bounds.minX, float(vertex.x));
        bounds.minY = std::min(bounds.minY, float(vertex.y));
        bounds.minZ = std::min(bounds.minZ, float(vertex.z));
        bounds.maxX = std::max(bounds.maxX, float(vertex.x));
        bounds.maxY = std::max(bounds.maxY, float(vertex.y));
        bounds.maxZ = std::max(bounds.maxZ, float(vertex.z));
    }

    return bounds;
}

struct CoverSetup
{
    bx::Vec3 source = {0.0f, 0.0f, 0.0f};
    bx::Vec3 open = {0.0f, 0.0f, 0.0f};
    bx::Vec3 hidden = {0.0f, 0.0f, 0.0f};
    Bounds building;
};

std::optional<CoverSetup> findCover(const OutdoorFixture &fixture)
{
    const OutdoorMapData &map = *fixture.pMap->outdoorMapData;
    constexpr float PartyEye = 96.0f;
    const auto dry = [&](const bx::Vec3 &point)
    {
        return !isOutdoorTerrainWater(map, point.x, point.y) && !outdoorTerrainSlopeTooHigh(map, point.x, point.y);
    };
    const auto at = [&](float x, float y)
    {
        return bx::Vec3{x, y, fixture.ground(x, y) + PartyEye};
    };

    for (const OutdoorBModel &bModel : map.bmodels)
    {
        const Bounds bounds = boundsOf(bModel);
        const float halfWidth = (bounds.maxX - bounds.minX) * 0.5f;
        const float halfDepth = (bounds.maxY - bounds.minY) * 0.5f;
        const float centerX = (bounds.minX + bounds.maxX) * 0.5f;
        const float centerY = (bounds.minY + bounds.maxY) * 0.5f;

        if (halfWidth < 200.0f || halfDepth < 200.0f || halfWidth > 1500.0f || halfDepth > 1500.0f
            || bounds.maxZ - bounds.minZ < 300.0f)
        {
            continue;
        }

        // The source on one side of the building, the hidden spot just past the opposite side, the open spot off to
        // the source's side.
        for (const std::array<float, 2> &direction :
            {std::array<float, 2>{1.0f, 0.0f}, {-1.0f, 0.0f}, {0.0f, 1.0f}, {0.0f, -1.0f}})
        {
            const float half = direction[0] != 0.0f ? halfWidth : halfDepth;

            for (const float side : {1.0f, -1.0f})
            {
                CoverSetup setup = {};
                setup.building = bounds;
                const float sourceX = centerX + direction[0] * (half + 1400.0f);
                const float sourceY = centerY + direction[1] * (half + 1400.0f);
                setup.source = at(sourceX, sourceY);
                setup.open = at(sourceX - direction[1] * side * 1600.0f, sourceY + direction[0] * side * 1600.0f);
                setup.hidden = at(centerX - direction[0] * (half + 260.0f), centerY - direction[1] * (half + 260.0f));
                const bx::Vec3 front = {centerX + direction[0] * (half + 60.0f),
                    centerY + direction[1] * (half + 60.0f), setup.source.z};

                if (dry(setup.source) && dry(setup.open) && dry(setup.hidden)
                    && std::abs(setup.source.z - setup.hidden.z) < 200.0f
                    && std::abs(setup.source.z - setup.open.z) < 200.0f
                    && setup.source.z + 120.0f < bounds.maxZ
                    && fixture.world->hasClearOutdoorLineOfSight(setup.source, setup.open)
                    && !fixture.world->hasClearOutdoorLineOfSight(setup.source, setup.hidden)
                    && fixture.world->hasClearOutdoorLineOfSight(setup.source, front)
                    && fixture.world->hasClearOutdoorLineOfSight(
                        {setup.source.x + (setup.open.x - setup.source.x) * 0.35f,
                            setup.source.y + (setup.open.y - setup.source.y) * 0.35f, setup.source.z},
                        front))
                {
                    return setup;
                }
            }
        }
    }

    return std::nullopt;
}

int16_t rangedMonsterId(const MonsterTable &monsters, bool flyer)
{
    int16_t best = 0;

    for (const auto &[id, stats] : monsters.statsEntries())
    {
        if (!stats.attack1MissileType.empty() && stats.attack1MissileType != "0" && stats.canFly == flyer
            && (best == 0 || id < best))
        {
            best = int16_t(id);
        }
    }

    return best;
}

// Flies a Fire Bolt from the source at the open spot while the party stands hidden; returns where it ended.
std::optional<bx::Vec3> flyBoltAtHiddenParty(OutdoorFixture &fixture, const CoverSetup &setup, bool homing)
{
    fixture.start();
    OutdoorWorldRuntime &world = *fixture.world;

    if (!world.castEventSpell(spellIdValue(SpellId::FireBolt), 5, 1, int32_t(setup.source.x),
            int32_t(setup.source.y), int32_t(setup.source.z), int32_t(setup.open.x), int32_t(setup.open.y),
            int32_t(setup.open.z))
        || fixture.projectiles.projectiles().size() != 1)
    {
        return std::nullopt;
    }

    if (homing)
    {
        GameplayProjectileService::ProjectileHoming trueAim = {};
        trueAim.turnRadiansPerSecond = 2.0f * 3.14159265f;
        GameplayProjectileService::ProjectileState &bolt = fixture.projectiles.projectiles().front();
        trueAim.speed = std::hypot(bolt.velocityX, bolt.velocityY, bolt.velocityZ);
        bolt.homing = trueAim;
    }

    const uint32_t boltId = fixture.projectiles.projectiles().front().projectileId;
    std::optional<bx::Vec3> last;

    for (int step = 0; step < 6 * 128; ++step)
    {
        world.updateMapActors(Step, setup.hidden.x, setup.hidden.y, setup.hidden.z - 96.0f);
        const GameplayProjectileService::ProjectileState *pBolt = nullptr;

        for (const GameplayProjectileService::ProjectileState &projectile : fixture.projectiles.projectiles())
        {
            pBolt = projectile.projectileId == boltId && !projectile.isExpired ? &projectile : pBolt;
        }

        if (pBolt == nullptr)
        {
            return last;
        }

        last = bx::Vec3{pBolt->x, pBolt->y, pBolt->z};
    }

    return last;
}
}

TEST_CASE("a homing projectile turns after a party gone behind a building and the building stops it")
{
    OutdoorFixture fixture;
    REQUIRE(fixture.load("mm6", "oute3.odm"));
    fixture.start();
    const std::optional<CoverSetup> setup = findCover(fixture);
    REQUIRE(setup);

    // Straight: the bolt flies on past where the party was, toward the open spot, away from the building.
    const std::optional<bx::Vec3> straightEnd = flyBoltAtHiddenParty(fixture, *setup, false);
    REQUIRE(straightEnd);
    CHECK(std::hypot(straightEnd->x - setup->source.x, straightEnd->y - setup->source.y)
        > std::hypot(straightEnd->x - setup->open.x, straightEnd->y - setup->open.y));

    // Homing: it turns after the party, toward the hidden spot, and ends against a building (the one it hides behind
    // or another on the way), short of the party.
    const std::optional<bx::Vec3> homingEnd = flyBoltAtHiddenParty(fixture, *setup, true);
    REQUIRE(homingEnd);
    CHECK(std::hypot(homingEnd->x - setup->hidden.x, homingEnd->y - setup->hidden.y)
        < std::hypot(setup->source.x - setup->hidden.x, setup->source.y - setup->hidden.y));
    CHECK(std::hypot(homingEnd->x - setup->hidden.x, homingEnd->y - setup->hidden.y) > 150.0f);
    bool againstBuilding = false;

    for (const OutdoorBModel &bModel : fixture.pMap->outdoorMapData->bmodels)
    {
        const Bounds bounds = boundsOf(bModel);
        constexpr float Margin = 48.0f;
        againstBuilding = againstBuilding
            || (homingEnd->x >= bounds.minX - Margin && homingEnd->x <= bounds.maxX + Margin
                && homingEnd->y >= bounds.minY - Margin && homingEnd->y <= bounds.maxY + Margin
                && homingEnd->z >= bounds.minZ - Margin && homingEnd->z <= bounds.maxZ + Margin);
    }

    CHECK(againstBuilding);
}

TEST_CASE("an outdoor blink lands on free floor in sight and refuses walls, bodies and hidden spots")
{
    OutdoorFixture fixture;
    REQUIRE(fixture.load("mm6", "oute3.odm"));
    const int16_t monsterId = rangedMonsterId(fixture.monsters, false);
    REQUIRE(monsterId != 0);
    MonsterModifierSet blinker = {};
    blinker.monsterId = monsterId;
    blinker.blink = BlinkModifier{};
    blinker.blink->onHitChance = 1.0f;
    blinker.blink->minDistance = 300.0f;
    blinker.blink->maxDistance = 700.0f;
    fixture.monsters.modifiers().set(blinker);
    fixture.start();
    const std::optional<CoverSetup> setup = findCover(fixture);
    REQUIRE(setup);
    OutdoorWorldRuntime &world = *fixture.world;
    const size_t firstActor = world.mapActorCount();
    REQUIRE(world.summonHostileMonsterById(monsterId, 2, setup->source.x, setup->source.y, setup->source.z - 96.0f, 0));
    REQUIRE(world.mapActorCount() == firstActor + 2);
    const size_t actorIndex = firstActor;
    const OutdoorWorldRuntime::MapActorState &actor = *world.mapActorState(actorIndex);
    const OutdoorWorldRuntime::MapActorState &other = *world.mapActorState(actorIndex + 1);
    const Bounds &building = setup->building;
    const float buildingCenterX = (building.minX + building.maxX) * 0.5f;
    const float buildingCenterY = (building.minY + building.maxY) * 0.5f;

    // Inside the building, behind it (out of sight) and onto another monster: refused, nothing moves.
    const float startX = actor.preciseX;
    CHECK_FALSE(world.blinkMapActorTo(actorIndex, buildingCenterX, buildingCenterY, 256.0f));
    CHECK_FALSE(world.blinkMapActorTo(actorIndex, setup->hidden.x, setup->hidden.y, 256.0f));
    CHECK_FALSE(world.blinkMapActorTo(actorIndex, other.preciseX + 10.0f, other.preciseY, 256.0f));
    CHECK_FALSE(world.blinkMapActorTo(actorIndex, 40000.0f, 0.0f, 256.0f));
    CHECK(actor.preciseX == startX);

    // The open spot off to its side: it lands there, on the ground.
    REQUIRE(world.blinkMapActorTo(actorIndex, setup->open.x, setup->open.y, 256.0f));
    CHECK(actor.preciseX == doctest::Approx(setup->open.x));
    CHECK(actor.preciseY == doctest::Approx(setup->open.y));
    CHECK(actor.preciseZ == doctest::Approx(fixture.ground(setup->open.x, setup->open.y)).epsilon(0.02));

    // Its blink modifier: a spot within its range, in sight of where it stood.
    const bx::Vec3 before = {actor.preciseX, actor.preciseY, actor.preciseZ};
    REQUIRE(world.blinkActor(actorIndex));
    const float jumped = std::hypot(actor.preciseX - before.x, actor.preciseY - before.y);
    CHECK(jumped >= 299.0f);
    CHECK(jumped <= 701.0f);
    CHECK(world.hasClearOutdoorLineOfSight({before.x, before.y, before.z + 40.0f},
        {actor.preciseX, actor.preciseY, actor.preciseZ + 40.0f}));
}

TEST_CASE("an indoor blink stays inside the dungeon, in sight, on a floor with headroom")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "hive.blv"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.indoorMapData);
    IndoorMapData map = *loaded.indoorMapData;
    map.spawns.clear();
    std::optional<MapDeltaData> delta = loaded.indoorMapDeltaData;
    REQUIRE(delta);
    delta->actors.clear();

    MonsterTable monsters = data.getMonsterTable();
    const int16_t monsterId = rangedMonsterId(monsters, false);
    REQUIRE(monsterId != 0);
    MonsterModifierSet blinker = {};
    blinker.monsterId = monsterId;
    blinker.blink = BlinkModifier{};
    blinker.blink->onHitChance = 1.0f;
    blinker.blink->minDistance = 200.0f;
    blinker.blink->maxDistance = 600.0f;
    monsters.modifiers().set(blinker);
    const MonsterTable::MonsterStatsEntry *pStats = monsters.findStatsById(monsterId);
    REQUIRE(pStats != nullptr);

    // A walker on the floor the party stands on in the Hive flying-devil test, the party well away.
    MapDeltaActor walker = {};
    walker.monsterId = walker.monsterInfoId = monsterId;
    walker.hp = int16_t(std::min(pStats->hitPoints, 30000));
    walker.x = 712;
    walker.y = 7147;
    walker.z = 0;
    walker.radius = 40;
    walker.height = 160;
    walker.hostilityType = 0;
    delta->actors.push_back(walker);

    Party party;
    party.setItemTable(&data.getItemTable());
    GameplayActorService actorService;
    actorService.bindTables(&monsters, &data.getSpellTable());
    IndoorSceneRuntime scene(loaded.map.fileName, loaded.map, map, monsters, data.getMonsterProjectileTable(),
        data.getObjectTable(), data.getSpellTable(), data.getItemTable(), data.getChestTable(), party, delta,
        loaded.eventRuntimeState, loaded.localEventProgram, std::nullopt, &actorService, nullptr);
    scene.partyRuntime().teleportPartyPosition(712.0f, 6400.0f, 0);
    scene.advanceSimulation(1000.0f / 128);
    IndoorWorldRuntime &world = scene.worldRuntime();
    REQUIRE(world.mapActorCount() == 1);
    const IndoorWorldRuntime::MapActorAiState &state = *world.mapActorAiState(0);
    const float startX = state.preciseX;
    const float startY = state.preciseY;
    const float startZ = state.preciseZ;
    REQUIRE(state.sectorId >= 0);

    // Far outside the map, and on the party: refused.
    CHECK_FALSE(world.blinkMapActorTo(0, startX + 60000.0f, startY, 256.0f));
    CHECK_FALSE(world.blinkMapActorTo(0, 712.0f, 6400.0f, 256.0f));
    CHECK(state.preciseX == startX);

    // Every spot it accepts around it has a floor at its feet in the sector it records, headroom, no wall within its
    // radius and a clear line back; it refuses at least one (the Hive's walls are close).
    const std::vector<IndoorVertex> &vertices = map.vertices;
    int accepted = 0;
    int refused = 0;

    for (int ring = 0; ring < 24; ++ring)
    {
        const float angle = float(ring) * 3.14159265f / 12.0f;
        const float distance = 250.0f + float(ring % 4) * 150.0f;
        const float x = startX + std::cos(angle) * distance;
        const float y = startY + std::sin(angle) * distance;

        if (!world.blinkMapActorTo(0, x, y, 256.0f))
        {
            ++refused;
            continue;
        }

        ++accepted;
        const IndoorFloorSample floor = sampleIndoorFloor(map, vertices, state.preciseX, state.preciseY,
            state.preciseZ + 4.0f, 8.0f, 8.0f);
        CHECK(floor.hasFloor);
        CHECK(floor.height == doctest::Approx(state.preciseZ).epsilon(0.02));
        CHECK(std::abs(state.preciseZ - startZ) <= 264.0f);
        CHECK(state.sectorId >= 0);
        const std::optional<int16_t> sector = findIndoorSectorForPoint(map, vertices,
            {state.preciseX, state.preciseY, state.preciseZ + 80.0f});
        REQUIRE(sector);
        CHECK(*sector == state.sectorId);
        CHECK_FALSE(findIndoorWallContact(map, vertices, {state.preciseX, state.preciseY, state.preciseZ + 80.0f},
            float(state.collisionRadius) - 1.0f));
        const IndoorCeilingSample ceiling = sampleIndoorCeiling(map, vertices, state.preciseX, state.preciseY,
            state.preciseZ + 1.0f, state.sectorId);
        CHECK((!ceiling.hasCeiling || ceiling.height - state.preciseZ >= float(state.collisionHeight)));

        // Back to the start for the next spot.
        REQUIRE(world.blinkMapActorTo(0, startX, startY, 256.0f));
    }

    CHECK(accepted > 0);
    CHECK(refused > 0);

    // The blink modifier jumps within its range.
    REQUIRE(world.blinkActor(0));
    const float jumped = std::hypot(state.preciseX - startX, state.preciseY - startY);
    CHECK(jumped >= 199.0f);
    CHECK(jumped <= 601.0f);
}

namespace
{
struct IndoorChargeFixture
{
    OpenYAMM::Engine::AssetFileSystem assets;
    GameDataLoader data;
    MonsterTable monsters;
    std::optional<IndoorMapData> map;
    std::optional<MapDeltaData> delta;
    Party party;
    GameplayActorService actorService;
    GameplayProjectileService projectiles;
    GameplayCombatController combat;
    std::optional<IndoorSceneRuntime> scene;
    int16_t monsterId = 0;

    // The Hive with one walker charger at (712, 7147) and the party at partyX, partyY; with frenzy, a frenzy below
    // half health (a 0.5 s roar, 3 s at double speed and glow 3, a 1 s spent hold) instead of the charge.
    bool start(float partyX, float partyY, bool frenzy = false)
    {
        if (!loadHive())
        {
            return false;
        }

        MonsterModifierSet charger = {};
        charger.monsterId = rangedMonsterId(monsters, false);
        if (frenzy)
        {
            charger.frenzy = FrenzyModifier{};
            charger.frenzy->healthBelow = 0.5f;
            charger.frenzy->windupSeconds = 0.5f;
            charger.frenzy->seconds = 3.0f;
            charger.frenzy->speedMultiplier = 2.0f;
            charger.frenzy->spentSeconds = 1.0f;
            charger.frenzy->glowMultiplier = 3.0f;
        }
        else
        {
            charger.charge = ChargeModifier{};
            charger.charge->windupSeconds = 0.3f;
            charger.charge->speed = 1600.0f;
            charger.charge->knockback = 0.0f;
        }
        return startWith(charger.monsterId, &charger, partyX, partyY);
    }

    bool loadHive()
    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        if (!assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6")
            || !data.loadForHeadlessGameplay(assets) || !data.loadMapByFileNameForHeadlessGameplay(assets, "hive.blv"))
        {
            return false;
        }

        monsters = data.getMonsterTable();
        return true;
    }

    // After loadHive: one walker of the monster (with pModifiers, or none listed) at (712, 7147), the party of one
    // member with partyHealth at partyX, partyY; walkerAttributes as its EvtActorAttribute bits.
    bool startWith(int16_t walkerMonsterId, const MonsterModifierSet *pModifiers, float partyX, float partyY,
        int partyHealth = 500, uint32_t walkerAttributes = 0)
    {
        const MapAssetInfo &loaded = *data.getSelectedMap();
        map = *loaded.indoorMapData;
        map->spawns.clear();
        delta = loaded.indoorMapDeltaData;
        delta->actors.clear();
        monsterId = walkerMonsterId;
        if (pModifiers != nullptr)
        {
            monsters.modifiers().set(*pModifiers);
        }
        const MonsterTable::MonsterStatsEntry *pStats = monsters.findStatsById(monsterId);

        if (pStats == nullptr)
        {
            return false;
        }

        MapDeltaActor walker = {};
        walker.monsterId = walker.monsterInfoId = monsterId;
        walker.hp = int16_t(std::min(pStats->hitPoints, 30000));
        walker.x = 712;
        walker.y = 7147;
        walker.z = 0;
        walker.radius = 40;
        walker.height = 160;
        walker.hostilityType = 0;
        walker.attributes = walkerAttributes;
        delta->actors.push_back(walker);
        party.setItemTable(&data.getItemTable());
        PartySeed seed = {};
        Character member = {};
        member.name = "Charged";
        member.maxHealth = member.health = partyHealth;
        seed.members.push_back(member);
        party.seed(seed);
        actorService.bindTables(&monsters, &data.getSpellTable());
        scene.emplace(loaded.map.fileName, loaded.map, *map, monsters, data.getMonsterProjectileTable(),
            data.getObjectTable(), data.getSpellTable(), data.getItemTable(), data.getChestTable(), party, delta,
            loaded.eventRuntimeState, loaded.localEventProgram, std::nullopt, &actorService, &projectiles, &combat);
        scene->partyRuntime().teleportPartyPosition(partyX, partyY, 0);
        scene->advanceSimulation(1000.0f / 128);
        return scene->worldRuntime().mapActorCount() == 1;
    }

    void run(float seconds)
    {
        for (float elapsed = 0.0f; elapsed < seconds; elapsed += 1.0f / 64.0f)
        {
            scene->worldRuntime().updateActorAi(1.0f / 64.0f);
        }
    }
};
}

TEST_CASE("an indoor charge dashes along the floor onto the party and hits it")
{
    // The party 450 south of the charger, the floor clear between (a pillar stands further south).
    IndoorChargeFixture fixture;
    REQUIRE(fixture.start(712.0f, 6700.0f));
    IndoorWorldRuntime &world = fixture.scene->worldRuntime();
    const IndoorWorldRuntime::MapActorAiState &state = *world.mapActorAiState(0);
    const float startY = state.preciseY;
    REQUIRE(world.chargeActor(0));
    CHECK_FALSE(world.chargeActor(0));
    fixture.run(0.2f);
    // Still winding up: it holds where it stood.
    CHECK(state.preciseY == doctest::Approx(startY).epsilon(0.01));
    fixture.run(1.5f);
    const std::optional<GameplayChargeCounts> counts = world.chargeCounts();
    REQUIRE(counts);
    CHECK(counts->started == 1);
    CHECK(counts->hits == 1);
    CHECK(counts->misses == 0);
    // It stopped against the party, on the floor, in a sector.
    CHECK(state.preciseY < startY - 300.0f);
    CHECK(state.preciseY > 6700.0f);
    CHECK(state.sectorId >= 0);
    // The hit: one monster melee impact from the charger (the combat controller rolls it against the party).
    const std::vector<GameplayCombatController::CombatEvent> &events = fixture.combat.pendingCombatEvents();
    REQUIRE(events.size() == 1);
    CHECK(events[0].type == GameplayCombatController::CombatEventType::MonsterMeleeImpact);
    CHECK(events[0].sourceId == state.actorId);
    CHECK(events[0].damage >= 1);
}

TEST_CASE("a monster's melee blow lands on a party that steps back during the swing")
{
    // An aggressive walker with only a melee blow (no missiles, no spells), the party 200 south of it.
    IndoorChargeFixture fixture;
    REQUIRE(fixture.loadHive());
    int16_t meleeMonsterId = 0;

    for (const auto &[id, stats] : fixture.monsters.statsEntries())
    {
        if (!stats.attack1HasMissile && !stats.attack2HasMissile && !stats.hasSpell1 && !stats.hasSpell2
            && !stats.canFly && stats.aiType == MonsterTable::MonsterAiType::Aggressive
            && (meleeMonsterId == 0 || id < meleeMonsterId))
        {
            meleeMonsterId = int16_t(id);
        }
    }

    REQUIRE(meleeMonsterId != 0);
    const uint32_t hostile = uint32_t(EvtActorAttribute::Hostile) | uint32_t(EvtActorAttribute::Aggressor)
        | uint32_t(EvtActorAttribute::Active) | uint32_t(EvtActorAttribute::FullAi);
    REQUIRE(fixture.startWith(meleeMonsterId, nullptr, 712.0f, 6950.0f, 500, hostile));
    IndoorWorldRuntime &world = fixture.scene->worldRuntime();
    const IndoorWorldRuntime::MapActorAiState &state = *world.mapActorAiState(0);

    for (float elapsed = 0.0f; elapsed < 5.0f && state.motionState != ActorAiMotionState::Attacking;
         elapsed += 1.0f / 64.0f)
    {
        fixture.run(1.0f / 64.0f);
    }

    REQUIRE(state.motionState == ActorAiMotionState::Attacking);
    REQUIRE(fixture.combat.pendingCombatEvents().empty());

    // Mid-swing the party is 450 away, well beyond the 307 the monster needs to start a blow, still in sight
    // (the floor between is clear). As in MM8 the blow still lands when the swing ends.
    fixture.scene->partyRuntime().teleportPartyPosition(712.0f, 6700.0f, 0.0f);

    for (float elapsed = 0.0f; elapsed < 3.0f && state.motionState == ActorAiMotionState::Attacking;
         elapsed += 1.0f / 64.0f)
    {
        fixture.run(1.0f / 64.0f);
    }

    CHECK(state.motionState != ActorAiMotionState::Attacking);
    const std::vector<GameplayCombatController::CombatEvent> &events = fixture.combat.pendingCombatEvents();
    REQUIRE(events.size() == 1);
    CHECK(events[0].type == GameplayCombatController::CombatEventType::MonsterMeleeImpact);
    CHECK(events[0].sourceId == state.actorId);
}

TEST_CASE("an indoor charge stops at a wall and stumbles")
{
    IndoorChargeFixture fixture;
    REQUIRE(fixture.start(712.0f, 6700.0f));
    IndoorWorldRuntime &world = fixture.scene->worldRuntime();
    const IndoorWorldRuntime::MapActorAiState &state = *world.mapActorAiState(0);
    const float startX = state.preciseX;
    const float startY = state.preciseY;

    // A direction from the charger with a wall 300-1200 units away; the party just beyond it.
    const std::vector<IndoorVertex> &vertices = fixture.map->vertices;
    std::optional<std::array<float, 3>> wallLine;

    for (int ring = 0; ring < 32 && !wallLine; ++ring)
    {
        const float angle = float(ring) * 3.14159265f / 16.0f;
        for (float distance = 120.0f; distance <= 1200.0f; distance += 20.0f)
        {
            if (findIndoorWallContact(*fixture.map, vertices,
                    {startX + std::cos(angle) * distance, startY + std::sin(angle) * distance, 80.0f}, 40.0f))
            {
                if (distance >= 300.0f)
                {
                    wallLine = std::array<float, 3>{std::cos(angle), std::sin(angle), distance};
                }
                break;
            }
        }
    }

    REQUIRE(wallLine);
    const float wallDistance = (*wallLine)[2];
    fixture.scene->partyRuntime().teleportPartyPosition(startX + (*wallLine)[0] * (wallDistance + 250.0f),
        startY + (*wallLine)[1] * (wallDistance + 250.0f), 0);
    REQUIRE(world.chargeActor(0));
    fixture.run(2.0f);
    const std::optional<GameplayChargeCounts> counts = world.chargeCounts();
    REQUIRE(counts);
    CHECK(counts->hits == 0);
    CHECK(counts->misses == 1);
    // It stopped short of the wall, not through it.
    const float travelled = std::hypot(state.preciseX - startX, state.preciseY - startY);
    CHECK(travelled > 50.0f);
    CHECK(travelled < wallDistance + 1.0f);
    CHECK_FALSE(findIndoorWallContact(*fixture.map, vertices, {state.preciseX, state.preciseY, state.preciseZ + 80.0f},
        float(state.collisionRadius) - 1.0f));
}

TEST_CASE("an indoor frenzy roars, plays its clips, glows and speeds the actor up")
{
    // The party down the hall so the actor pursues it.
    IndoorChargeFixture fixture;
    REQUIRE(fixture.start(712.0f, 6700.0f, true));
    IndoorWorldRuntime &world = fixture.scene->worldRuntime();
    const IndoorWorldRuntime::MapActorAiState &state = *world.mapActorAiState(0);
    const auto view = [&world]()
    {
        GameplayRuntimeActorState actorView = {};
        REQUIRE(world.actorRuntimeState(0, actorView));
        return actorView;
    };

    // Its own pursuit first.
    const auto travelOver = [&](float seconds)
    {
        const float fromX = state.preciseX;
        const float fromY = state.preciseY;
        fixture.run(seconds);
        return std::hypot(state.preciseX - fromX, state.preciseY - fromY);
    };
    fixture.run(0.3f);
    const float plainTravel = travelOver(0.4f);
    CHECK(plainTravel > 20.0f);

    CHECK_FALSE(world.chargeActor(0));
    REQUIRE(world.frenzyActor(0));
    CHECK_FALSE(world.frenzyActor(0));
    const float roarX = state.preciseX;
    const float roarY = state.preciseY;
    fixture.run(0.3f);

    // The roar: it holds where it stood and plays the frenzy clip.
    CHECK(view().scriptedClip == "frenzy");
    CHECK(view().emissionMultiplier == doctest::Approx(1.0f));
    CHECK(std::hypot(state.preciseX - roarX, state.preciseY - roarY) < 1.0f);

    // The frenzy: the glow, and (once its pursuit resumes after the hold) double speed.
    fixture.run(0.4f);
    CHECK(view().scriptedClip.empty());
    CHECK(view().emissionMultiplier == doctest::Approx(3.0f));
    fixture.run(0.4f);
    const float frenzyTravel = travelOver(0.4f);
    CHECK(frenzyTravel == doctest::Approx(plainTravel * 2.0f).epsilon(0.1));

    // Spent: it holds again with the spent clip.
    fixture.run(2.1f);
    CHECK(view().scriptedClip == "spent");
    CHECK(view().emissionMultiplier == doctest::Approx(1.0f));
    REQUIRE(world.chargeCounts());
    CHECK(world.chargeCounts()->frenzies == 1);
}

TEST_CASE("an indoor frenzy starts by itself when the actor falls below its health share")
{
    IndoorChargeFixture fixture;
    REQUIRE(fixture.start(712.0f, 6700.0f, true));
    IndoorWorldRuntime &world = fixture.scene->worldRuntime();
    fixture.run(1.0f);
    REQUIRE(world.chargeCounts());
    CHECK(world.chargeCounts()->frenzies == 0);
    MapDeltaActor &actor = fixture.scene->worldRuntime().mapDeltaData()->actors[0];
    GameplayRuntimeActorState view = {};
    REQUIRE(world.actorRuntimeState(0, view));
    REQUIRE(view.maxHp > 2);
    actor.hp = int16_t(view.maxHp / 3);
    fixture.run(0.5f);
    CHECK(world.chargeCounts()->frenzies == 1);
}

TEST_CASE("indoors a monster casts Meteor Shower only with the indoor_meteor_shower modifier")
{
    // A Hive Devil Warrior (Spell2 Meteor Shower, 15 %), the party down the hall in sight. The original game drops a
    // monster's Meteor Shower indoors: without the modifier it never picks it, and fights on with its other attacks.
    constexpr int16_t DevilWarrior = 221;
    const auto meteorsAndShots = [](bool indoorMeteorShower)
    {
        IndoorChargeFixture fixture;
        REQUIRE(fixture.loadHive());
        const MonsterTable::MonsterStatsEntry *pStats = fixture.monsters.findStatsById(DevilWarrior);
        REQUIRE(pStats != nullptr);
        REQUIRE(pStats->hasSpell2);
        REQUIRE(pStats->spell2Name == "meteor shower");
        MonsterModifierSet modifiers = {};
        modifiers.monsterId = DevilWarrior;
        modifiers.indoorMeteorShower = true;
        modifiers.names = {"indoor_meteor_shower"};
        REQUIRE(fixture.startWith(DevilWarrior, indoorMeteorShower ? &modifiers : nullptr, 712.0f, 6700.0f, 30000));
        const GameplayProjectileService *pProjectiles = fixture.scene->worldRuntime().projectileServiceView();
        REQUIRE(pProjectiles != nullptr);
        std::set<uint32_t> meteors;
        std::set<uint32_t> shots;

        for (int second = 0; second < 60; ++second)
        {
            fixture.run(1.0f);
            for (const GameplayProjectileService::ProjectileState &projectile : pProjectiles->projectiles())
            {
                (isSpellId(uint32_t(std::max(projectile.spellId, 0)), SpellId::MeteorShower) ? meteors : shots)
                    .insert(projectile.projectileId);
            }
        }

        return std::pair<size_t, size_t>(meteors.size(), shots.size());
    };

    const std::pair<size_t, size_t> without = meteorsAndShots(false);
    CHECK(without.first == 0);
    CHECK(without.second > 0);
    const std::pair<size_t, size_t> with = meteorsAndShots(true);
    CHECK(with.first > 0);
}

TEST_CASE("outdoors MM9's CanDamage turned off at runtime lets no hit hurt the actor until it is on again")
{
    OutdoorFixture fixture;
    REQUIRE(fixture.load("mm6", "oute3.odm"));
    const int16_t monsterId = rangedMonsterId(fixture.monsters, false);
    REQUIRE(monsterId != 0);
    fixture.start();
    OutdoorWorldRuntime &world = *fixture.world;
    const size_t actorIndex = world.mapActorCount();
    REQUIRE(world.summonHostileMonsterById(monsterId, 1, 0.0f, 0.0f, fixture.ground(0.0f, 0.0f), 0));
    const OutdoorWorldRuntime::MapActorState &actor = *world.mapActorState(actorIndex);
    const int hp = actor.currentHp;
    REQUIRE_GT(hp, 1);

    CHECK_FALSE(world.setMm9ActorCanReceiveDamage(actorIndex + 1, false));
    REQUIRE(world.setMm9ActorCanReceiveDamage(actorIndex, false));
    CHECK(world.applyPartyAttackToMapActor(actorIndex, 100000, 0.0f, 300.0f, actor.preciseZ + 96.0f));
    CHECK_FALSE(world.stunActor(actorIndex, 5.0f));
    CHECK_EQ(actor.currentHp, hp);

    REQUIRE(world.setMm9ActorCanReceiveDamage(actorIndex, true));
    REQUIRE(world.applyPartyAttackToMapActor(actorIndex, 1, 0.0f, 300.0f, actor.preciseZ + 96.0f));
    CHECK_LT(actor.currentHp, hp);
}
