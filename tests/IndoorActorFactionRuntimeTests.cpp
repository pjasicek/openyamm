#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "engine/TextTable.h"
#include "game/data/GameDataLoader.h"
#include "game/events/EventRuntime.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/indoor/IndoorPartyRuntime.h"
#include "game/indoor/IndoorWorldRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MonsterTable.h"
#include "game/maps/IndoorSceneYml.h"
#include "tests/RegressionGameData.h"

#include <filesystem>
#include <fstream>
#include <iterator>

using namespace OpenYAMM::Game;

namespace
{
constexpr uint32_t DetectionAttributes = uint32_t(EvtActorAttribute::Nearby)
    | uint32_t(EvtActorAttribute::Active) | uint32_t(EvtActorAttribute::FullAi);

std::vector<uint8_t> readFixture(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    REQUIRE(stream.good());
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

std::vector<std::vector<std::string>> readTable(const std::filesystem::path &path)
{
    const std::vector<uint8_t> bytes = readFixture(path);
    const std::optional<OpenYAMM::Engine::TextTable> table =
        OpenYAMM::Engine::TextTable::parseTabSeparated(std::string(bytes.begin(), bytes.end()));
    REQUIRE(table);
    std::vector<std::vector<std::string>> rows;
    for (size_t row = 0; row < table->getRowCount(); ++row)
    {
        rows.push_back(table->getRow(row));
    }
    return rows;
}

struct FixtureActor
{
    int16_t monsterId = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    int16_t sectorId = -1;
    uint32_t attributes = 0;
};

// GW_3's victim upstairs and allies in the sealed lower room. Start without its bad cached detection.
const std::vector<FixtureActor> Gw3Actors = {
    {487, -152, 4225, 0, 3, 0},
    {487, 1671, 3845, -632, 24, 0},
    {488, 1595, 3807, -632, 24, DetectionAttributes | uint32_t(EvtActorAttribute::Aggressor)},
    {487, 6665, 7033, 128, 44, 0},
    {550, 2300, 3750, -768, 24, 0},
};

// Mist villagers of one class: A to B is 2650, B to C 3544 and A to C 5420, beyond the 4096 alert range.
constexpr int16_t Villager = 596;
constexpr FixtureActor VillagerA = {Villager, -152, 4225, 0, 3, 0};
constexpr FixtureActor VillagerB = {Villager, 2300, 3750, -768, 24, 0};
constexpr FixtureActor VillagerC = {Villager, 3641, 431, -768, -1, 0};

struct GoblinwatchFactionFixture
{
    const OpenYAMM::Tests::RegressionGameData &data = OpenYAMM::Tests::regressionGameData();
    MonsterTable monsters = data.monsterTable;
    IndoorMapData map;
    std::optional<MapDeltaData> delta = MapDeltaData{};
    std::optional<EventRuntimeState> events = EventRuntimeState{};
    ObjectTable objects;
    ChestTable chests;
    GameplayActorService actorService;
    std::unique_ptr<IndoorPartyRuntime> partyRuntime;
    IndoorWorldRuntime world;

    explicit GoblinwatchFactionFixture(const std::vector<FixtureActor> &actors = Gw3Actors)
    {
        REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure());
        const std::filesystem::path tables =
            std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/data_tables";
        REQUIRE(monsters.loadEntriesFromRows(readTable(tables / "monster_descriptors.txt")));
        REQUIRE(monsters.loadStatsFromRows(readTable(tables / "monster_data.txt")));
        const std::filesystem::path root = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm6/maps";
        std::optional<IndoorMapData> loadedMap = IndoorMapDataLoader{}.loadFromBytes(readFixture(root / "6d01.blv"));
        REQUIRE(loadedMap);
        map = std::move(*loadedMap);
        const std::vector<uint8_t> sceneBytes = readFixture(root / "6d01.scene.yml");
        std::string error;
        const std::optional<IndoorSceneData> scene =
            IndoorSceneYmlLoader{}.loadFromText(std::string(sceneBytes.begin(), sceneBytes.end()), error);
        REQUIRE_MESSAGE(scene, error);
        REQUIRE_MESSAGE(buildIndoorMapStateFromScene(*scene, map, *delta, error), error);
        map.spawns.clear();
        delta->actors.clear();

        for (const FixtureActor &fixtureActor : actors)
        {
            const MonsterTable::MonsterStatsEntry *pStats = monsters.findStatsById(fixtureActor.monsterId);
            REQUIRE(pStats != nullptr);
            MapDeltaActor actor = {};
            actor.monsterId = fixtureActor.monsterId;
            actor.monsterInfoId = fixtureActor.monsterId;
            actor.hp = pStats->hitPoints;
            actor.x = fixtureActor.x;
            actor.y = fixtureActor.y;
            actor.z = fixtureActor.z;
            actor.sectorId = fixtureActor.sectorId;
            actor.attributes = fixtureActor.attributes;
            delta->actors.push_back(actor);
        }

        EventRuntime{}.initializeMapRuntimeState(*delta, *events);
        partyRuntime = std::make_unique<IndoorPartyRuntime>(
            IndoorMovementController(map, &delta, &events), data.itemTable);
        partyRuntime->initializePartyPosition(1356.65f, 4589.76f, 0.0f);
        REQUIRE_EQ(partyRuntime->movementState().sectorId, 45);
        partyRuntime->party().applyPartyBuff(PartyBuffId::WizardEye, 3600.0f, 1, 0, 1, SkillMastery::Normal, 0);
        actorService.bindTables(&monsters, &data.spellTable);
        MapStatsEntry mapStats = {};
        mapStats.fileName = "6d01.blv";
        mapStats.worldId = "mm6";
        mapStats.name = "Goblinwatch";
        world.initialize(mapStats, monsters, objects, data.itemTable, chests,
            &partyRuntime->party(), partyRuntime.get(), &delta, &events, &actorService, nullptr, &map);
        REQUIRE_EQ(world.mapActorCount(), actors.size());
        REQUIRE_EQ(world.snapshot().mapActorAiStates[1].sectorId, 24);
    }

    bool hostile(size_t actorIndex) const
    {
        return world.snapshot().mapActorAiStates[actorIndex].hostileToParty;
    }

    void hit(size_t actorIndex)
    {
        REQUIRE(world.applyPartyAttackMeleeDamage(
            actorIndex, 1, {1356.65f, 4589.76f, 96.0f}, ShieldAttackTier::Physical));
    }

    void checkUndetectedAlly() const
    {
        const IndoorWorldRuntime::MapActorAiState ally = world.snapshot().mapActorAiStates[1];
        CHECK(ally.hostileToParty);
        CHECK_FALSE(ally.hasDetectedParty);
        CHECK_FALSE(ally.spellEffects.hasDetectedParty);
        CHECK_EQ(delta->actors[1].attributes & DetectionAttributes, 0u);
        CHECK_NE(ally.motionState, ActorAiMotionState::Pursuing);
        CHECK_NE(ally.motionState, ActorAiMotionState::Attacking);
    }
};
}

TEST_CASE("indoor faction alerts preserve detection and leave Goblinwatch's unseen allies dormant")
{
    GoblinwatchFactionFixture fixture;
    int damage = 1;
    SUBCASE("surviving victim")
    {
        damage = 1;
    }
    SUBCASE("killed victim")
    {
        damage = 10000;
    }

    const IndoorWorldRuntime::Snapshot before = fixture.world.snapshot();
    const std::vector<MapDeltaActor> actorsBefore = fixture.delta->actors;
    REQUIRE(fixture.world.applyPartyAttackMeleeDamage(
        0, damage, {1356.65f, 4589.76f, 96.0f}, ShieldAttackTier::Physical));
    const IndoorWorldRuntime::Snapshot after = fixture.world.snapshot();

    CHECK(after.mapActorAiStates[0].hostileToParty);
    CHECK(after.mapActorAiStates[0].hasDetectedParty);
    CHECK_EQ(fixture.delta->actors[0].hp == 0, damage == 10000);
    fixture.checkUndetectedAlly();
    CHECK_EQ(fixture.delta->actors[1].hostilityType, 4);
    CHECK_EQ(fixture.delta->actors[1].attributes, uint32_t(EvtActorAttribute::Aggressor));
    CHECK(after.mapActorAiStates[1].spellEffects.hostileToParty);

    // Alerts retain existing encounter memory and do not restart another actor's action.
    CHECK(after.mapActorAiStates[2].hasDetectedParty);
    CHECK(after.mapActorAiStates[2].spellEffects.hasDetectedParty);
    CHECK_EQ(fixture.delta->actors[2].attributes, actorsBefore[2].attributes);
    CHECK_EQ(after.mapActorAiStates[2].motionState, before.mapActorAiStates[2].motionState);
    CHECK_EQ(after.mapActorAiStates[2].actionSeconds, before.mapActorAiStates[2].actionSeconds);
    for (size_t actorIndex : {3u, 4u})
    {
        CAPTURE(actorIndex);
        CHECK_EQ(fixture.delta->actors[actorIndex].attributes, actorsBefore[actorIndex].attributes);
        CHECK_EQ(fixture.delta->actors[actorIndex].hostilityType, actorsBefore[actorIndex].hostilityType);
        CHECK_EQ(after.mapActorAiStates[actorIndex].hasDetectedParty,
            before.mapActorAiStates[actorIndex].hasDetectedParty);
    }

    fixture.world.updateActorAi(0.1f);
    fixture.checkUndetectedAlly();
    std::vector<GameplayMinimapMarkerState> markers;
    fixture.world.collectGameplayMinimapMarkers(markers);
    CHECK_EQ(markers.size(), 2); // Direct victim (or corpse) and the previously detected ally only.
}

TEST_CASE("indoor faction alert survives restore without granting detection and allows a later encounter")
{
    GoblinwatchFactionFixture fixture;
    REQUIRE(fixture.world.applyPartyAttackMeleeDamage(0, 1, {1356.65f, 4589.76f, 96.0f}, ShieldAttackTier::Physical));
    const IndoorWorldRuntime::Snapshot saved = fixture.world.snapshot();
    fixture.world.restoreSnapshot(saved);
    fixture.world.updateActorAi(0.1f);
    fixture.checkUndetectedAlly();

    fixture.partyRuntime->teleportPartyPosition(2300.0f, 3400.0f, -768.0f);
    REQUIRE_EQ(fixture.partyRuntime->movementState().sectorId, 24);
    fixture.world.updateActorAi(0.1f);
    const IndoorWorldRuntime::Snapshot encountered = fixture.world.snapshot();
    CHECK(encountered.mapActorAiStates[1].hasDetectedParty);
    CHECK((fixture.delta->actors[1].attributes & uint32_t(EvtActorAttribute::FullAi)) != 0);
    CHECK((fixture.delta->actors[1].attributes & uint32_t(EvtActorAttribute::Nearby)) != 0);
}

TEST_CASE("indoor first visit gives placed monsters hostile to the party their Hst and leaves friendly ones at 0")
{
    // Placed actors load with no hostility (MapDeltaData); outdoors and spawned monsters already take Hst.
    GoblinwatchFactionFixture fixture({VillagerA, Gw3Actors[1], VillagerB});
    const int goblinHostility = fixture.monsters.findStatsById(Gw3Actors[1].monsterId)->hostility;
    REQUIRE_GT(goblinHostility, 0);
    REQUIRE(fixture.hostile(1));
    REQUIRE_FALSE(fixture.hostile(0));

    CHECK_EQ(fixture.delta->actors[0].hostilityType, 0);
    CHECK_EQ(fixture.delta->actors[1].hostilityType, goblinHostility);
    CHECK_EQ(fixture.delta->actors[2].hostilityType, 0);
}

TEST_CASE("indoor faction alert: a monster hostile on its own turns no friendly actor of its class")
{
    // Mount Nighon's raiding warlocks share their class with the town's.
    FixtureActor raider = VillagerA;
    raider.attributes = uint32_t(EvtActorAttribute::Aggressor);
    GoblinwatchFactionFixture fixture({raider, VillagerB});
    REQUIRE(fixture.hostile(0));
    REQUIRE_FALSE(fixture.hostile(1));

    fixture.hit(0);
    CHECK_FALSE(fixture.hostile(1));
    CHECK_FALSE(fixture.world.snapshot().mapActorAiStates[0].angeredByParty);
}

TEST_CASE("indoor faction alert: a monster the party angered still alerts its class, also after a restore")
{
    GoblinwatchFactionFixture fixture({VillagerA, VillagerB, VillagerC});
    REQUIRE_FALSE(fixture.hostile(0));
    REQUIRE_FALSE(fixture.hostile(1));
    REQUIRE_FALSE(fixture.hostile(2));

    fixture.hit(0);
    CHECK(fixture.hostile(0));
    CHECK(fixture.hostile(1));
    CHECK_FALSE(fixture.hostile(2)); // Beyond the alert range of the first victim.
    CHECK(fixture.world.snapshot().mapActorAiStates[0].angeredByParty);
    CHECK(fixture.world.snapshot().mapActorAiStates[1].angeredByParty);

    const IndoorWorldRuntime::Snapshot saved = fixture.world.snapshot();
    fixture.world.restoreSnapshot(saved);
    fixture.hit(1);
    CHECK(fixture.hostile(2));
}

TEST_CASE("MM9 CanDamage off: no hit hurts an indoor actor until evt.SetMm9ActorCanReceiveDamage turns it on")
{
    GoblinwatchFactionFixture fixture;
    IndoorWorldRuntime &world = fixture.world;
    std::ifstream supportStream(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportStream.good());
    const std::string source = std::string(std::istreambuf_iterator<char>(supportStream),
        std::istreambuf_iterator<char>()) + "\n"
        "RegisterGlobalEvent(9101, \"Off\", function()\n"
        "    if evt.SetMm9ActorCanReceiveDamage(0, false) and not evt.SetMm9ActorCanReceiveDamage(99, false) then\n"
        "        evt.StatusText(\"off\")\n"
        "    end\n"
        "end)\n"
        "RegisterGlobalEvent(9102, \"On\", function() evt.SetMm9ActorCanReceiveDamage(0, 1) end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@can_damage_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9101, runtimeState, nullptr, &world));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 1u);
    CHECK_EQ(runtimeState.statusMessages.front(), "off");
    CHECK_FALSE(fixture.delta->actors[0].mm9CanReceiveDamage);

    // Melee, missiles, spells and reflected damage land and do nothing; no stun takes hold.
    const int hp = fixture.delta->actors[0].hp;
    const GameplayWorldPoint party = {1356.65f, 4589.76f, 96.0f};
    CHECK(world.applyPartyAttackMeleeDamage(0, 10000, party, ShieldAttackTier::Physical));
    CHECK(world.applyPartyAttackMeleeDamage(0, 10000, CombatDamageType::Fire, party, ShieldAttackTier::Spell));
    CHECK(world.applyPartySpellToActor(0, 2, 10, SkillMastery::Master, 10000, party.x, party.y, party.z, 0, false));
    CHECK(world.applyReflectedDamageToActor(0, 10000, CombatDamageType::Physical, 0));
    CHECK_FALSE(world.stunActor(0, 5.0f));
    CHECK_EQ(fixture.delta->actors[0].hp, hp);

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9102, runtimeState, nullptr, &world));
    CHECK(fixture.delta->actors[0].mm9CanReceiveDamage);
    REQUIRE(world.applyPartyAttackMeleeDamage(0, 1, party, ShieldAttackTier::Physical));
    CHECK_LT(fixture.delta->actors[0].hp, hp);
}

TEST_CASE("an indoor actor no hit can hurt is not turned by its kin's alert")
{
    // Tamur Leng (MM9 Frosgard City) shares Forad Darre's relations; a hit on Forad turned him, and he would not talk.
    // Villager A's alert turns villager B (the test above); not one that no hit can hurt.
    GoblinwatchFactionFixture fixture({VillagerA, VillagerB});
    fixture.delta->actors[1].mm9CanReceiveDamage = false;
    REQUIRE_FALSE(fixture.hostile(1));
    fixture.hit(0);
    CHECK(fixture.hostile(0));
    CHECK_FALSE(fixture.hostile(1));
    CHECK_EQ(fixture.delta->actors[1].attributes & uint32_t(EvtActorAttribute::Aggressor), 0u);
}

TEST_CASE("evt.ReviveMapActor raises a dead indoor actor where the map placed it")
{
    GoblinwatchFactionFixture fixture;
    IndoorWorldRuntime &world = fixture.world;
    world.updateWorld(0.01f);   // the first world update records where the fill placed every actor
    const MapDeltaActor placed = fixture.delta->actors[0];
    const MonsterTable::MonsterStatsEntry *pStats = fixture.monsters.findStatsById(placed.monsterId);
    REQUIRE(pStats != nullptr);

    std::ifstream supportStream(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportStream.good());
    const std::string source = std::string(std::istreambuf_iterator<char>(supportStream),
        std::istreambuf_iterator<char>()) + "\n"
        "RegisterGlobalEvent(9103, \"Revive\", function()\n"
        "    if evt.ReviveMapActor(0) then evt.StatusText(\"risen\") end\n"
        "    if not evt.ReviveMapActor(0) and not evt.ReviveMapActor(99) then evt.StatusText(\"only the dead\") end\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@revive_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    EventRuntimeState runtimeState = {};

    // A living actor is not raised.
    CHECK_FALSE(world.reviveMapActor(0));

    // Killed by the party where it stood, then pushed away (as a corpse flies).
    REQUIRE(world.applyPartyAttackMeleeDamage(0, 100000, {1356.65f, 4589.76f, 96.0f}, ShieldAttackTier::Physical));
    REQUIRE(world.isMapActorDead(0));
    fixture.delta->actors[0].x += 300;
    fixture.delta->actors[0].attributes |= uint32_t(EvtActorAttribute::Invisible);

    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9103, runtimeState, nullptr, &world));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 2u);
    CHECK_EQ(runtimeState.statusMessages[0], "risen");
    CHECK_EQ(runtimeState.statusMessages[1], "only the dead");
    const MapDeltaActor &risen = fixture.delta->actors[0];
    CHECK_FALSE(world.isMapActorDead(0));
    CHECK_EQ(risen.hp, pStats->hitPoints);
    CHECK_EQ(risen.x, placed.x);
    CHECK_EQ(risen.y, placed.y);
    CHECK_EQ(risen.sectorId, placed.sectorId);
    CHECK_EQ(risen.attributes & uint32_t(EvtActorAttribute::Invisible), 0u);
    CHECK_NE(world.snapshot().mapActorAiStates[0].motionState, ActorAiMotionState::Dead);
    CHECK_NE(world.snapshot().mapActorAiStates[0].motionState, ActorAiMotionState::Dying);
    // Its attitude stays as it was: the party's blow made it hostile.
    CHECK(fixture.hostile(0));
}

TEST_CASE("mm6 maps load their own faction relations into the monster table and drop them with the next map")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    const MonsterTable &monsters = data.getMonsterTable();
    // hostile.txt has Guards (553-555, faction 185) and Sorcerers (631-633, faction 211) hostile to the party.
    // MMMerge's oute3.lua makes the guards peaceful in New Sorpigal; outd1.lua makes the sorcerers peaceful in Silver
    // Cove and sets them against Druidesses (517, faction 173).
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "oute3.odm"));
    CHECK_FALSE(monsters.isHostileToParty(553));
    CHECK(monsters.isHostileToParty(631));
    CHECK(monsters.getRelationBetweenMonsters(631, 517) == 0);

    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "outd1.odm"));
    CHECK(monsters.isHostileToParty(553));
    CHECK_FALSE(monsters.isHostileToParty(631));
    CHECK(monsters.getRelationBetweenMonsters(631, 517) == 2);
    CHECK(monsters.getRelationBetweenMonsters(517, 631) == 1);
}

TEST_CASE("E11: an indoor MonsterDamage hook sees how the hit came and the striking member's weapon")
{
    GoblinwatchFactionFixture fixture;
    IndoorWorldRuntime &world = fixture.world;
    // XD-19's rule as the studio writes a `trigger: monster_damage` event: only a blow of item 12500 hurts.
    std::ifstream supportStream(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportStream.good());
    const std::string source = std::string(std::istreambuf_iterator<char>(supportStream),
        std::istreambuf_iterator<char>()) + "\n"
        "RegisterMonsterDamageHook(65000, \"Lord Xeen\", function(hook)\n"
        "    if not (hook.attack == \"melee\" and hook.weaponItemId == 12500) then evt.SetHookDamage(0) end\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> hook =
        ScriptedEventProgram::loadFromLuaText(source, "@e11_hook_test.lua", ScriptedEventScope::Map, error);
    REQUIRE_MESSAGE(hook.has_value(), error.c_str());
    const std::optional<ScriptedEventProgram> noGlobal;
    EventRuntime eventRuntime = {};
    world.bindEventExecution(&eventRuntime, &hook, &noGlobal);

    const GameplayWorldPoint party = {1356.65f, 4589.76f, 96.0f};
    const int hp = fixture.delta->actors[0].hp;
    REQUIRE_GT(hp, 3);
    world.applyPartyAttackMeleeDamage(0, 1, party, ShieldAttackTier::Physical);
    world.applyPartyAttackMeleeDamage(0, 1, party, ShieldAttackTier::Physical, {}, false, true, 12499);
    world.applyPartyAttackMeleeDamage(0, 1, CombatDamageType::Physical, party, ShieldAttackTier::Physical, {}, false,
        true, "missile", 12500);
    world.applyPartyAttackMeleeDamage(0, 1, CombatDamageType::Fire, party, ShieldAttackTier::Spell, {}, false, true,
        "spell", 12500);
    CHECK_EQ(fixture.delta->actors[0].hp, hp);

    world.applyPartyAttackMeleeDamage(0, 1, party, ShieldAttackTier::Physical, {}, false, true, 12500);
    CHECK_EQ(fixture.delta->actors[0].hp, hp - 1);
}

TEST_CASE("D-2.3: an item's SlayingDemon effect flag doubles its blows against demons only")
{
    CHECK_EQ(itemSlayingKindFlag("SlayingDemon"), monsterKindFlag(MonsterKind::Demon));
    CHECK_EQ(itemSlayingKindFlag("SlayingTitan"), monsterKindFlag(MonsterKind::Titan));
    CHECK_EQ(itemSlayingKindFlag("Slaying"), 0u);
    CHECK_EQ(itemSlayingKindFlag("Vampiric"), 0u);

    std::vector<std::string> swordRow(26);
    swordRow[0] = "60001";
    swordRow[1] = "missing_test_icon";
    swordRow[2] = "Test Slayer Sword";
    swordRow[3] = "100";
    swordRow[4] = "Weapon2";
    swordRow[5] = "Sword";
    swordRow[6] = "3d10";
    swordRow[17] = "test";
    swordRow[18] = "test:item/60001";
    swordRow[19] = "60001";
    swordRow[25] = "test:item_effect/slayer";
    std::vector<std::string> effectRow(30);
    effectRow[0] = "60001";
    effectRow[1] = "test:item_effect/slayer";
    effectRow[29] = "SlayingDemon";
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1));
    ItemTable items;
    REQUIRE(items.load(assetFileSystem, {swordRow}, {}));
    std::string error;
    REQUIRE_MESSAGE(items.loadContentEffectRows({effectRow}, error), error);
    REQUIRE(items.get(60001) != nullptr);

    Character member;
    member.equipment.mainHand = 60001;
    CHECK_EQ(ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
        member, CharacterAttackMode::Melee, &items, nullptr, monsterKindFlag(MonsterKind::Demon)), 2);
    CHECK_EQ(ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
        member, CharacterAttackMode::Melee, &items, nullptr, monsterKindFlag(MonsterKind::Undead)), 1);
}
