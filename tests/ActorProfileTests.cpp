#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/content/ContentManifest.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameplayMonsterSpawn.h"
#include "game/maps/SaveGame.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/rules/GameRules.h"
#include "game/rules/maw/MawRules.h"
#include "tests/TestActorProfiles.h"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <tuple>

using namespace OpenYAMM::Game;

namespace
{
std::filesystem::path temporaryOverlayRoot(const std::string &name)
{
    return std::filesystem::temp_directory_path()
        / (name + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
}

std::string readSourceFile(const std::filesystem::path &relativePath)
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath, std::ios::binary);
    REQUIRE(file.good());
    return std::string(std::istreambuf_iterator<char>(file), {});
}

// The mm7 world as shipped plus the test actor profiles, mounted in front of assets_dev so the profiles load through
// the world manifest like a real world's.
void writeProfileWorld(const std::filesystem::path &overlay)
{
    const std::filesystem::path world = overlay / "worlds/mm7";
    std::filesystem::create_directories(world);
    std::ofstream(world / "world.yml", std::ios::binary)
        << readSourceFile("assets_dev/worlds/mm7/world.yml") << "\nactorProfiles: actor_profiles.yml\n";
    std::ofstream(world / "actor_profiles.yml", std::ios::binary) << OpenYAMM::Tests::TestActorProfilesYaml;
}

void mountProfileWorld(OpenYAMM::Engine::AssetFileSystem &assets, const std::filesystem::path &temporaryRoot)
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(temporaryRoot, temporaryRoot / "mods", OpenYAMM::Engine::AssetScaleTier::X1, "mm7"));
    REQUIRE(assets.mountDevelopmentRoot(sourceRoot / "assets_dev"));
}

struct ProfileData
{
    GameDataLoader data;
    ProfileData()
    {
        const std::filesystem::path temporaryRoot = temporaryOverlayRoot("openyamm_actor_profile_world_");
        writeProfileWorld(temporaryRoot / "mods");
        {
            OpenYAMM::Engine::AssetFileSystem assets;
            mountProfileWorld(assets, temporaryRoot);
            REQUIRE(data.loadCommonForGameplay(assets));
        }
        std::filesystem::remove_all(temporaryRoot);
    }
};

ProfileData &profileData()
{
    static ProfileData result;
    return result;
}

struct OutdoorProfileFixture
{
    ProfileData &source = profileData();
    OutdoorWorldRuntime world;
    Party party;
    GameplayActorService actors;
    MapStatsEntry map;

    explicit OutdoorProfileFixture(const std::string &mapFile = "profiletest.odm")
    {
        GameDataLoader &data = source.data;
        map.fileName = mapFile;
        map.worldId = mapFile == "out01.odm" ? "mm8" : "mm7";
        actors.bindTables(&data.getMonsterTable(), &data.getSpellTable());
        world.initialize(map, data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(),
            data.getSpellTable(), data.getItemTable(), &party, nullptr, data.getStandardItemEnchantTable(),
            data.getSpecialItemEnchantTable(), &data.getChestTable(), std::nullopt, std::nullopt, std::nullopt,
            EventRuntimeState{}, std::nullopt, std::nullopt, std::nullopt, std::nullopt, std::nullopt, std::nullopt,
            &actors);
    }

    size_t spawn(int16_t monsterId, const std::string &profile = {}, bool hostile = false, uint32_t group = 0)
    {
        GameplayMonsterSpawnRequest request;
        request.monsterId = monsterId;
        request.actorProfile = profile;
        request.radius = 0;
        request.x = 100;
        request.hostile = hostile;
        request.group = group;
        const std::vector<size_t> spawned = world.spawnMonsters(request);
        REQUIRE_EQ(spawned.size(), 1);
        return spawned.front();
    }
};
}

TEST_CASE("actor profiles keep the kind flags their base monster gets after the profiles load")
{
    // Kind flags come from the merged bolster table, applied after the profiles copied their base rows.
    const MonsterTable &table = profileData().data.getMonsterTable();
    for (const auto &[id, profile] : {std::pair{58, "mm7.test_troll_clubman"},
        std::pair{59, "mm7.test_troll_geomancer"}, std::pair{60, "mm7.test_troll_emberlord"},
        std::pair{10, "mm7.test_freebooter"}, std::pair{405, "mm7.test_stay_friendly"}})
    {
        const auto *pBase = table.findStatsById(int16_t(id));
        const auto *pProfile = table.findStatsById(int16_t(id), profile);
        REQUIRE(pBase != nullptr);
        REQUIRE(pProfile != nullptr);
        CHECK_EQ(pProfile->kindFlags, pBase->kindFlags);
    }
    CHECK(table.findStatsById(58, "mm7.test_troll_clubman")->hasKind(MonsterKind::Ogre));
}

TEST_CASE("actor profiles load through the world manifest without changing shared monster rows")
{
    ProfileData &source = profileData();
    const std::filesystem::path temporaryRoot = temporaryOverlayRoot("openyamm_actor_profile_manifest_");
    writeProfileWorld(temporaryRoot / "mods");
    {
        OpenYAMM::Engine::AssetFileSystem assets;
        mountProfileWorld(assets, temporaryRoot);
        std::string error;
        const auto manifest = loadWorldManifest(assets, "worlds/mm7/world.yml", "mm7", error);
        REQUIRE_MESSAGE(manifest, error);
        CHECK_EQ(manifest->actorProfilesPath, "actor_profiles.yml");
    }
    std::filesystem::remove_all(temporaryRoot);
    const MonsterTable &table = source.data.getMonsterTable();
    const auto *pMichael = table.findStatsById(405, "mm7.test_heroism_caster");
    REQUIRE(pMichael != nullptr);
    CHECK_EQ(pMichael->spell1Name, "heroism");
    CHECK_EQ(pMichael->spell1UseChance, 10);
    CHECK_EQ(pMichael->spell1SkillLevel, 4);
    CHECK_EQ(pMichael->spell1SkillMastery, SkillMastery::Expert);
    CHECK_FALSE(table.findStatsById(405)->hasSpell1);
    CHECK_EQ(table.findStatsById(59)->attack1Type, "Phys");
    CHECK_EQ(table.findStatsById(88)->specialAttackKind, MonsterSpecialAttackKind::Paralyze);
    for (const auto &[id, profile, chance, skill, spell2, level2, mastery2, element] : {
        std::tuple{58, "clubman", 5, 3, "", 0, SkillMastery::None, "Phys"},
        std::tuple{59, "geomancer", 11, 5, "deadly swarm", 10, SkillMastery::Expert, "Earth"},
        std::tuple{60, "emberlord", 20, 7, "fire bolt", 16, SkillMastery::Grandmaster, "Fire"}})
    {
        const auto *pStats = table.findStatsById(id, std::string("mm7.test_troll_") + profile);
        REQUIRE(pStats != nullptr);
        CHECK_EQ(pStats->spell1Name, "power cure");
        CHECK_EQ(pStats->spell1UseChance, chance);
        CHECK_EQ(pStats->spell1SkillLevel, skill);
        CHECK_EQ(pStats->spell1SkillMastery, SkillMastery::Grandmaster);
        CHECK_EQ(pStats->spell2Name, spell2);
        CHECK_EQ(pStats->spell2SkillLevel, level2);
        CHECK_EQ(pStats->spell2SkillMastery, mastery2);
        CHECK_EQ(pStats->attack1Type, element);
    }
    CHECK_EQ(table.findStatsById(88, "mm7.test_bogling")->specialAttackKind, MonsterSpecialAttackKind::None);
    CHECK_EQ(table.findStatsById(89, "mm7.test_bog_dweller")->specialAttackKind, MonsterSpecialAttackKind::None);
    CHECK_EQ(table.findStatsById(90, "mm7.test_bog_elder")->specialAttackKind,
        MonsterSpecialAttackKind::PoisonWeak);
    CHECK_EQ(table.findStatsById(90, "mm7.test_bog_elder")->specialAttackLevel, 1);
    CHECK_FALSE(table.retaliatesAgainstParty("mm7.test_stay_friendly"));
    CHECK(table.retaliatesAgainstParty({}));
    CHECK(table.retaliatesAgainstParty("mm7.test_heroism_caster"));
    CHECK(table.findStatsById(58, "mm7.test_troll_emberlord") == nullptr);
    CHECK(table.findStatsById(405, "mm7.unknown") == nullptr);
    for (const char *pMap : {"7out01.odm", "out01.odm"})
    {
        CHECK(table.defaultActorProfile(pMap, 88).empty());
        CHECK(table.defaultActorProfile(pMap, 10).empty());
    }
    CHECK_EQ(table.defaultActorProfile("PROFILETEST.ODM", 88), "mm7.test_bogling");
    CHECK(table.defaultActorProfile("testlevel.blv", 58).empty());
}

TEST_CASE("Lua ground item removal uses the native outdoor store and remains removed after save restoration")
{
    OutdoorProfileFixture fixture;
    REQUIRE(fixture.world.summonEventItem(992, 100, 0, 0, 0, 1, false));
    REQUIRE(fixture.world.summonEventItem(1009, 200, 0, 0, 0, 1, false));
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR)
        / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(file.good());
    const std::string source = std::string(std::istreambuf_iterator<char>(file), {}) + R"lua(
RegisterEvent(9066, nil, function()
    assert(not evt.RemoveMapItem(0, 1009))
    assert(evt.RemoveMapItem(1, 1009))
end)
)lua";
    std::string error;
    const std::optional<ScriptedEventProgram> program = ScriptedEventProgram::loadFromLuaText(
        source, "@outdoor_remove_item.lua", ScriptedEventScope::Map, error);
    REQUIRE_MESSAGE(program, error);
    EventRuntime runtime;
    REQUIRE(runtime.executeEventById(program, std::nullopt, 9066, *fixture.world.eventRuntimeState(),
        &fixture.party, &fixture.world));
    GameplayWorldItemInspectState item;
    REQUIRE(fixture.world.worldItemInspectState(0, item));
    CHECK_EQ(item.item.objectDescriptionId, 992);
    CHECK_FALSE(fixture.world.worldItemInspectState(1, item));
    CHECK_EQ(fixture.party.inventoryItemCount(1009), 0);
    GameSaveData save;
    save.mapFileName = "profiletest.odm";
    save.hasOutdoorRuntimeState = true;
    save.outdoorWorld = fixture.world.snapshot();
    const std::filesystem::path path = std::filesystem::temp_directory_path()
        / ("openyamm_remove_item_" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())
            + ".oysav");
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error);
    const std::optional<GameSaveData> restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored, error);
    fixture.world.restoreSnapshot(restored->outdoorWorld);
    REQUIRE(fixture.world.worldItemInspectState(0, item));
    CHECK_EQ(item.item.objectDescriptionId, 992);
    CHECK_FALSE(fixture.world.worldItemInspectState(1, item));
}

TEST_CASE("actor profile validation is strict and failed contributions are atomic")
{
    const ProfileData &source = profileData();
    const std::string header = "schema: openyamm.actorProfiles.v1\nprofiles:\n";
    for (const std::string &body : {
        "  mm7.bad: {monster: 405, typo: true}\n",
        "  other.bad: {monster: 405}\n",
        "  mm7.bad: {monster: 32768}\n",
        "  mm7.bad: {monster: 405, party_damage_reaction: immortal}\n",
        "  mm7.bad: {monster: 400, indoor_encounter_radius: 0}\n",
        "  mm7.bad: {monster: 400, indoor_encounter_radius: 65536}\n",
        "  mm7.bad: {monster: 405, on_hit: stone}\n",
        "  mm7.bad: {monster: 405, attack1_element: Stone}\n",
        "  mm7.bad: {monster: 405, spell1: {id: 999999, chance: 10, skill: 4, mastery: 2}}\n",
        "  mm7.bad: {monster: 405, spell1: {id: 51, chance: 101, skill: 4, mastery: 2}}\n",
        "  mm7.bad: {monster: 405, spell1: {id: 51, chance: 10, skill: -1, mastery: 2}}\n",
        "  mm7.bad: {monster: 405, spell1: {id: 51, chance: 10, skill: 4, mastery: 5}}\n",
        "  mm7.bad: {monster: 405, spell1: {id: 0, chance: 10, skill: 4, mastery: 2}}\n",
        "  mm7.bad: {monster: 405}\nmap_defaults: {test.blv: [mm7.absent]}\n",
        "  mm7.bad: {monster: 405}\nmap_defaults: {../test.blv: [mm7.bad]}\n",
        "  mm7.bad: {monster: 405}\nmap_defaults: {test.blv: [mm7.bad, mm7.bad]}\n"})
    {
        CAPTURE(body);
        MonsterTable table = source.data.getMonsterTable();
        std::string error;
        CHECK_FALSE(table.loadActorProfiles(header + "  mm7.good: {monster: 58}\n" + body,
            "mm7", source.data.getSpellTable(), error));
        CHECK_FALSE(error.empty());
        CHECK(table.findStatsById(58, "mm7.good") == nullptr);
        CHECK(table.findStatsById(405, "mm7.test_heroism_caster") != nullptr);
    }
}

TEST_CASE("outdoor actor profiles apply to spawns and stay local to the maps that declare them")
{
    OutdoorProfileFixture fixture;
    const size_t bogling = fixture.spawn(88);
    const size_t elder = fixture.spawn(90);
    const size_t pirate = fixture.spawn(17);
    const size_t michael = fixture.spawn(405, "mm7.test_heroism_caster", true);
    CHECK_EQ(fixture.world.mapActorState(bogling)->displayName, "Test Bogling");
    CHECK_EQ(fixture.world.mapActorState(elder)->displayName, "Test Bog Elder");
    CHECK_EQ(fixture.world.mapActorState(pirate)->displayName, "Test Pirate Magi");
    CHECK_EQ(fixture.world.mapActorState(michael)->spell1Id, 51);
    CHECK_EQ(fixture.world.mapActorState(michael)->spell1SkillLevel, 4);
    CHECK_EQ(fixture.world.mapActorState(michael)->spell1SkillMastery, SkillMastery::Expert);
    CHECK_EQ(fixture.world.combatActorInfoById(fixture.world.mapActorState(bogling)->actorId)->specialAttackKind,
        MonsterSpecialAttackKind::None);
    CHECK_EQ(fixture.world.combatActorInfoById(fixture.world.mapActorState(elder)->actorId)->specialAttackKind,
        MonsterSpecialAttackKind::PoisonWeak);
    for (const char *pMap : {"7out01.odm", "out01.odm"})
    {
        OutdoorProfileFixture stock(pMap);
        CHECK(stock.world.mapActorState(stock.spawn(88))->actorProfile.empty());
        CHECK_NE(stock.world.mapActorState(0)->displayName, "Test Bogling");
        CHECK(stock.world.mapActorState(stock.spawn(405))->spell1Id == 0);
    }
    GameplayMonsterSpawnRequest invalid;
    invalid.monsterId = 58;
    invalid.actorProfile = "mm7.test_heroism_caster";
    CHECK(fixture.world.spawnMonsters(invalid).empty());
}

TEST_CASE("outdoor friendly reaction takes melee and spell damage without provoking allies")
{
    OutdoorProfileFixture fixture;
    const size_t greene = fixture.spawn(405, "mm7.test_stay_friendly");
    const size_t knight = fixture.spawn(405);
    auto controlled = fixture.world.snapshot();
    controlled.mapActors[greene].fearRemainingSeconds = 10;
    fixture.world.restoreSnapshot(controlled);
    const int hp = fixture.world.mapActorState(greene)->currentHp;
    REQUIRE(fixture.world.applyPartyAttackMeleeDamage(greene, 1, {0, 0, 0}, ShieldAttackTier::Physical));
    CHECK_EQ(fixture.world.mapActorState(greene)->currentHp, hp - 1);
    CHECK_EQ(fixture.world.mapActorState(greene)->fearRemainingSeconds, 0);
    CHECK_FALSE(fixture.world.mapActorState(greene)->hostileToParty);
    CHECK_FALSE(fixture.world.mapActorState(knight)->hostileToParty);
    REQUIRE(fixture.world.applyPartySpellToActor(greene, 39, 10, SkillMastery::Expert, 10, 0, 0, 0));
    CHECK(fixture.world.mapActorState(greene)->currentHp < hp - 1);
    CHECK_FALSE(fixture.world.mapActorState(greene)->hostileToParty);
    CHECK_FALSE(fixture.world.mapActorState(knight)->hostileToParty);
    REQUIRE(fixture.world.applyPartyAttackMeleeDamage(knight, 1, {0, 0, 0}, ShieldAttackTier::Physical));
    CHECK(fixture.world.mapActorState(knight)->hostileToParty);
    CHECK_FALSE(fixture.world.mapActorState(greene)->hostileToParty);
    REQUIRE(fixture.world.applyPartyAttackMeleeDamage(greene, 100000, {0, 0, 0}, ShieldAttackTier::Physical));
    CHECK_EQ(fixture.world.mapActorState(greene)->currentHp, 0);
}

TEST_CASE("actor profiles round-trip with wounded HP and temporary buffs and survive refresh")
{
    OutdoorProfileFixture fixture;
    const size_t michael = fixture.spawn(405, "mm7.test_heroism_caster", true);
    auto snapshot = fixture.world.snapshot();
    auto &actor = snapshot.mapActors[michael];
    actor.currentHp = actor.maxHp / 2;
    actor.heroismRemainingSeconds = 120;
    actor.heroismPower = 9;
    fixture.world.restoreSnapshot(snapshot);
    GameSaveData save;
    save.mapFileName = "profiletest.odm";
    save.hasOutdoorRuntimeState = true;
    save.outdoorWorld = fixture.world.snapshot();
    save.hasIndoorSceneState = true;
    save.indoorScene.mapDeltaData = MapDeltaData{};
    MapDeltaActor indoor;
    indoor.monsterInfoId = 59;
    indoor.actorProfile = "mm7.test_troll_geomancer";
    indoor.hp = 17;
    save.indoorScene.mapDeltaData->actors.push_back(indoor);
    GameplayActorSpellEffectState buff;
    buff.heroismRemainingSeconds = 88;
    buff.heroismPower = 9;
    IndoorWorldRuntime::MapActorAiState indoorAi;
    indoorAi.spellEffects = buff;
    save.indoorScene.worldRuntime.mapActorAiStates.push_back(indoorAi);
    const std::filesystem::path path = std::filesystem::temp_directory_path()
        / ("openyamm_actor_profiles_" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())
            + ".oysav");
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error);
    const auto restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored, error);
    CHECK_EQ(restored->indoorScene.mapDeltaData->actors[0].actorProfile, "mm7.test_troll_geomancer");
    CHECK_EQ(restored->indoorScene.mapDeltaData->actors[0].hp, 17);
    REQUIRE_EQ(restored->indoorScene.worldRuntime.mapActorAiStates.size(), 1);
    CHECK_EQ(restored->indoorScene.worldRuntime.mapActorAiStates[0].spellEffects.heroismRemainingSeconds, 88);
    fixture.world.restoreSnapshot(restored->outdoorWorld);
    fixture.world.refreshRulesetMonsters();
    const auto *pActor = fixture.world.mapActorState(michael);
    REQUIRE(pActor != nullptr);
    CHECK_EQ(pActor->actorProfile, "mm7.test_heroism_caster");
    CHECK_EQ(pActor->currentHp, actor.currentHp);
    CHECK_EQ(pActor->spell1Id, 51);
    CHECK_EQ(pActor->spell1SkillMastery, SkillMastery::Expert);
    CHECK_EQ(pActor->heroismRemainingSeconds, 120);
    CHECK_EQ(pActor->heroismPower, 9);
    fixture.world.applyMapReentryReset();
    CHECK_EQ(fixture.world.mapActorState(michael)->currentHp, pActor->maxHp);
}

TEST_CASE("outdoor explicit duel hostility overrides a friendly species relation across save and load")
{
    OutdoorProfileFixture fixture;
    const size_t michael = fixture.spawn(405, "mm7.test_heroism_caster", true, 901);
    const size_t knight = fixture.spawn(405);
    EventRuntimeState *pEvents = fixture.world.eventRuntimeState();
    REQUIRE(pEvents != nullptr);
    pEvents->monsterRelationOverrides[EventRuntime::monsterRelationOverrideKey(405, 0)] = 0;
    fixture.world.applyEventRuntimeState();
    CHECK_FALSE(fixture.world.mapActorState(michael)->hostileToParty);
    pEvents->actorGroupSetMasks[901] = uint32_t(EvtActorAttribute::Hostile);
    pEvents->actorGroupHostilityRequests[901] = true;
    fixture.world.applyEventRuntimeState();
    CHECK(fixture.world.mapActorState(michael)->hostileToParty);
    CHECK_FALSE(fixture.world.mapActorState(knight)->hostileToParty);
    pEvents->actorGroupHostilityRequests.clear();
    fixture.world.applyEventRuntimeState();
    CHECK(fixture.world.mapActorState(michael)->hostileToParty);
    const auto snapshot = fixture.world.snapshot();
    fixture.world.restoreSnapshot(snapshot);
    CHECK(fixture.world.mapActorState(michael)->hostileToParty);
    CHECK_FALSE(fixture.world.mapActorState(knight)->hostileToParty);
}

TEST_CASE("map loading rejects a placed actor with an unknown profile instead of losing its content")
{
    // The Erathian Sewer's one placed actor, given a profile no world declares.
    const std::filesystem::path temporaryRoot = temporaryOverlayRoot("openyamm_bad_actor_profile_");
    const std::filesystem::path scenePath = temporaryRoot / "mods/worlds/mm7/maps/7d11.scene.yml";
    writeProfileWorld(temporaryRoot / "mods");
    std::filesystem::create_directories(scenePath.parent_path());
    std::string text = readSourceFile("assets_dev/worlds/mm7/maps/7d11.scene.yml");
    const std::string actor = "    - actor_index: 0\n";
    const size_t at = text.find(actor);
    REQUIRE_NE(at, std::string::npos);
    text.insert(at + actor.size(), "      actor_profile: mm7.unknown_profile\n");
    {
        OpenYAMM::Engine::AssetFileSystem assets;
        mountProfileWorld(assets, temporaryRoot);
        GameDataLoader data;
        REQUIRE(data.loadCommonForGameplay(assets));
        CHECK(data.loadMapByFileNameForHeadlessGameplay(assets, "7d11.blv"));
    }
    std::ofstream(scenePath, std::ios::binary) << text;
    {
        OpenYAMM::Engine::AssetFileSystem assets;
        mountProfileWorld(assets, temporaryRoot);
        GameDataLoader data;
        REQUIRE(data.loadCommonForGameplay(assets));
        const auto overridden = assets.readTextFile("worlds/mm7/maps/7d11.scene.yml");
        REQUIRE(overridden);
        REQUIRE(overridden->find("mm7.unknown_profile") != std::string::npos);
        CHECK_FALSE(data.loadMapByFileNameForHeadlessGameplay(assets, "7d11.blv"));
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("actor profiles and MM9 placement settings survive the same save")
{
    Mm9AiPlacementRecord placement;
    placement.settings.sight = 1536.0f;
    placement.script = "ll_flyingcreature.scr";

    GameSaveData save;
    save.mapFileName = "profiletest.odm";
    save.hasOutdoorRuntimeState = true;
    auto &outdoor = save.outdoorWorld.mapActors.emplace_back();
    outdoor.actorProfile = "mm7.test_heroism_caster";
    outdoor.mm9Ai = placement;
    save.hasIndoorSceneState = true;
    auto &indoor = save.indoorScene.mapDeltaData.emplace().actors.emplace_back();
    indoor.actorProfile = "mm7.test_troll_geomancer";
    indoor.mm9Ai = placement;

    const auto path = std::filesystem::temp_directory_path() / "openyamm_profiles_and_mm9_placement.oysav";
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error);
    const auto restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored, error);
    REQUIRE(restored->indoorScene.mapDeltaData);
    REQUIRE_EQ(restored->indoorScene.mapDeltaData->actors.size(), 1);
    REQUIRE_EQ(restored->outdoorWorld.mapActors.size(), 1);
    const auto &loadedIndoor = restored->indoorScene.mapDeltaData->actors.front();
    const auto &loadedOutdoor = restored->outdoorWorld.mapActors.front();
    CHECK_EQ(loadedIndoor.actorProfile, indoor.actorProfile);
    CHECK_EQ(loadedOutdoor.actorProfile, outdoor.actorProfile);
    REQUIRE(loadedIndoor.mm9Ai);
    REQUIRE(loadedOutdoor.mm9Ai);
    CHECK(*loadedIndoor.mm9Ai == placement);
    CHECK(*loadedOutdoor.mm9Ai == placement);
}
