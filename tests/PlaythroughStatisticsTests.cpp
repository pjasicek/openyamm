#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/party/PlaythroughNames.h"
#include "game/party/PlaythroughSeal.h"
#include "game/party/PlaythroughStatistics.h"
#include "game/rules/ExperienceRules.h"

#include <doctest/doctest.h>

#include <chrono>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
std::filesystem::path freshDirectory(const std::string &name)
{
    const uint64_t ticks = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    const std::filesystem::path directory =
        std::filesystem::temp_directory_path() / ("openyamm_statistics_" + name + "_" + std::to_string(ticks));
    std::filesystem::create_directories(directory);
    return directory;
}

StatMemberRef member(uint64_t id, const std::string &name)
{
    return {id, name, "Knight"};
}

std::filesystem::path sidecarPath(const std::filesystem::path &directory, const std::string &id)
{
    return directory / (id + "." + PlaythroughSeal::sealingKeyVersion() + ".oystats");
}

std::string readFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    std::stringstream bytes;
    bytes << file.rdbuf();
    return bytes.str();
}

void writeFile(const std::filesystem::path &path, const std::string &bytes)
{
    std::ofstream file(path, std::ios::binary | std::ios::trunc);
    file << bytes;
}
}

TEST_CASE("playthrough counters survive their YAML round trip")
{
    PlaythroughStatistics statistics;
    statistics.beginNewPlaythrough("mm8", "maw", "hard");
    statistics.setContext(3000.0f, "oute3.odm", "mm8", false);
    const StatMemberRef kareth = member(0x1234, "Kareth");
    statistics.recordMonsterKilled("Lizardman", 12);
    statistics.recordKillCredit(&kareth, StatKillMethod::Melee);
    statistics.recordDamageDealt(&kareth, 1, 812, true, "melee", "Lizardman");
    statistics.recordDamageTaken(kareth, StatDamageTakenKind::Spell, 40, "Lich");
    statistics.recordDeath(kareth, false, "Lich");
    statistics.recordExperience(kareth, ExperienceReason::Monster, 500);
    statistics.recordGold(250, GoldReason::LootCorpse);
    statistics.recordGold(-90, GoldReason::Shop);
    statistics.recordMapEntered("OutE3.odm");
    statistics.recordChestOpened("oute3.odm", 7);
    statistics.recordChestOpened("oute3.odm", 7);
    statistics.recordArtifactFound(512, "Mash");

    PlaythroughCounters parsed;
    PlaythroughTrackingInfo info;
    const std::optional<PlaythroughSeal::Opened> opened = PlaythroughSeal::open(
        PlaythroughSeal::Kind::Timeline, statistics.playthroughId(), statistics.serializedTimeline());
    REQUIRE(opened.has_value());
    REQUIRE(parsePlaythroughCounters(opened->text, parsed, info));
    CHECK_FALSE(info.partial);
    CHECK(parsed.kills == 1);
    CHECK(parsed.killsByMonster.at("Lizardman") == 1);
    CHECK(parsed.strongestKill == "Lizardman");
    CHECK(parsed.strongestKillLevel == 12);
    CHECK(parsed.killsByMethod[size_t(StatKillMethod::Melee)] == 1);
    CHECK(parsed.damageDealtBySchool[1] == 812);
    CHECK(parsed.criticalHits == 1);
    REQUIRE(parsed.largestHits.size() == 1);
    CHECK(parsed.largestHits.front().target == "Lizardman");
    CHECK(parsed.damageTaken[size_t(StatDamageTakenKind::Spell)] == 40);
    CHECK(parsed.deaths == 1);
    REQUIRE(parsed.deathLog.size() == 1);
    CHECK(parsed.deathLog.front().cause == "Lich");
    CHECK(parsed.deathLog.front().map == "oute3.odm");
    CHECK(parsed.experience[size_t(ExperienceReason::Monster)] == 500);
    CHECK(parsed.goldLooted() == 250);
    CHECK(parsed.goldSpentTotal() == 90);
    CHECK(parsed.mapsVisited.count("oute3.odm") == 1);
    CHECK(parsed.chestsOpened.size() == 1);
    REQUIRE(parsed.artifactsFound.size() == 1);
    CHECK(parsed.artifactsFound.front().name == "Mash");
    const PlaythroughMemberCounters &counters = parsed.members.at(PlaythroughStatistics::memberKey(0x1234));
    CHECK(counters.name == "Kareth");
    CHECK(counters.kills == 1);
    CHECK(counters.damageDealt == 812);
    CHECK(counters.deaths == 1);
    CHECK(counters.experience == 500);
}

TEST_CASE("a quickload puts the timeline back and keeps the lifetime")
{
    const std::filesystem::path directory = freshDirectory("quickload");
    PlaythroughStatistics statistics;
    statistics.setDirectory(directory);
    statistics.beginNewPlaythrough("mm6", "standard", "");
    const std::string id = statistics.playthroughId();
    statistics.recordMonsterKilled("Goblin", 3);

    // Quicksave here: the save carries the timeline.
    const std::string savedTimeline = statistics.serializedTimeline();
    statistics.recordSave(StatSaveKind::Quick);

    // The fight is played, then undone by a quickload, then played again.
    statistics.recordMonsterKilled("Goblin", 3);
    statistics.recordDamageDealt(nullptr, 0, 100, false, "melee", "Goblin");
    statistics.attachLoadedSave(id, 0, savedTimeline, StatLoadKind::Quick, "mm6", "standard", "");
    statistics.recordMonsterKilled("Goblin", 3);
    statistics.recordDamageDealt(nullptr, 0, 100, false, "melee", "Goblin");

    CHECK(statistics.playthroughId() == id);
    CHECK(statistics.timeline().kills == 2);
    CHECK(statistics.timeline().damageDealtTotal() == 100);
    CHECK(statistics.lifetime().kills == 3);
    CHECK(statistics.lifetime().damageDealtTotal() == 200);
    CHECK(statistics.lifetime().quickSaves == 1);
    CHECK(statistics.lifetime().quickLoads == 1);
    // Reloading the same playthrough is the same session.
    CHECK(statistics.lifetime().sessions == 1);

    statistics.endPlaythrough();
    REQUIRE(std::filesystem::exists(sidecarPath(directory, id)));
    std::filesystem::remove_all(directory);
}

TEST_CASE("the sidecar keeps the lifetime between sessions and a party wipe's reload counts")
{
    const std::filesystem::path directory = freshDirectory("sidecar");
    std::string id;
    std::string savedTimeline;

    {
        PlaythroughStatistics statistics;
        statistics.setDirectory(directory);
        statistics.beginNewPlaythrough("mm7", "standard", "");
        id = statistics.playthroughId();
        savedTimeline = statistics.serializedTimeline();
        statistics.recordMonsterKilled("Ogre", 20);
        statistics.recordPartyWipe();
        statistics.addPlayTime(30.0, false);
        statistics.endPlaythrough();
    }

    PlaythroughStatistics statistics;
    statistics.setDirectory(directory);
    statistics.attachLoadedSave(id, 0, savedTimeline, StatLoadKind::Menu, "mm7", "standard", "");
    CHECK(statistics.timeline().kills == 0);
    CHECK(statistics.lifetime().kills == 1);
    CHECK(statistics.lifetime().partyWipes == 1);
    CHECK(statistics.lifetime().playedSeconds == doctest::Approx(30.0));
    CHECK(statistics.lifetime().sessions == 2);
    CHECK(statistics.lifetime().menuLoads == 1);
    CHECK_FALSE(statistics.lifetimeInfo().partial);
    statistics.endPlaythrough();
    std::filesystem::remove_all(directory);
}

TEST_CASE("saves from before statistics share one record through their random root seed")
{
    const std::filesystem::path directory = freshDirectory("legacy");
    PlaythroughStatistics statistics;
    statistics.setDirectory(directory);
    statistics.attachLoadedSave("", 0xabcdef, "", StatLoadKind::Menu, "mm8", "standard", "");
    CHECK(statistics.playthroughId() == PlaythroughStatistics::legacyPlaythroughId(0xabcdef));
    CHECK(statistics.timelineInfo().partial);
    CHECK(statistics.lifetimeInfo().partial);
    statistics.recordMonsterKilled("Dragonfly", 4);
    statistics.endPlaythrough();

    // Another old save of the same party finds the same record.
    PlaythroughStatistics other;
    other.setDirectory(directory);
    other.attachLoadedSave("", 0xabcdef, "", StatLoadKind::Menu, "mm8", "standard", "");
    CHECK(other.lifetime().kills == 1);
    CHECK(other.lifetime().menuLoads == 2);
    other.endPlaythrough();
    std::filesystem::remove_all(directory);
}

TEST_CASE("the party records gold and experience by reason, and its copies do not record")
{
    PlaythroughStatistics statistics;
    statistics.beginNewPlaythrough("mm6", "standard", "");
    Party party;
    party.seed(Party::createDefaultSeed());
    party.setStatistics(&statistics);
    party.assignStatsMemberIds();
    REQUIRE(party.members().front().statsMemberId != 0);

    party.addGold(300, GoldReason::LootChest);
    party.addGold(-100, GoldReason::Training);
    party.addExperienceToMember(0, 1000, ExperienceReason::Event);

    MonsterKillReward kill;
    kill.baseExperience = 400;
    kill.baseHitPoints = 10;
    party.grantMonsterKillExperience(kill);

    CHECK(statistics.timeline().goldGained[size_t(GoldReason::LootChest)] == 300);
    CHECK(statistics.timeline().goldSpent[size_t(GoldReason::Training)] == 100);
    CHECK(statistics.timeline().experience[size_t(ExperienceReason::Event)] == 1000);
    CHECK(statistics.timeline().experience[size_t(ExperienceReason::Monster)] > 0);
    CHECK(statistics.timeline().experience[size_t(ExperienceReason::Other)] == 0);

    // A trial copy (MAW's equipment comparison) never records.
    Party trial = party;
    CHECK(trial.statistics() == nullptr);
    trial.addGold(5000, GoldReason::LootGround);
    CHECK(statistics.timeline().goldGained[size_t(GoldReason::LootGround)] == 0);

    // Assigning another state keeps the binding.
    party = trial;
    CHECK(party.statistics() == &statistics);
}

TEST_CASE("a member's death from damage is recorded with what hurt them")
{
    PlaythroughStatistics statistics;
    statistics.beginNewPlaythrough("mm6", "standard", "");
    Party party;
    party.seed(Party::createDefaultSeed());
    party.setStatistics(&statistics);
    party.assignStatsMemberIds();

    REQUIRE(party.applyDamageToMember(0, 5, "falling"));
    CHECK(statistics.timeline().damageTaken[size_t(StatDamageTakenKind::Environment)] == 5);

    party.setIncomingDamageSource(StatDamageTakenKind::Melee, "Ogre");
    REQUIRE(party.applyDamageToMember(0, 100000, ""));
    CHECK(statistics.timeline().damageTaken[size_t(StatDamageTakenKind::Melee)] > 0);
    CHECK(statistics.timeline().deaths == 1);
    REQUIRE(statistics.timeline().deathLog.size() == 1);
    CHECK(statistics.timeline().deathLog.front().cause == "Ogre");
    CHECK(statistics.timeline().damageTaken[size_t(StatDamageTakenKind::Environment)] == 5);
}

TEST_CASE("a save keeps the playthrough id, its timeline and the members' statistics identity")
{
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.playthroughId = "9f2c4e0a7d1b4c55a0e3f1d2b6c78e10";
    save.playthroughTimeline = "schema: 1\ncombat: {kills: 3}\n";
    Party party;
    party.seed(Party::createDefaultSeed());
    party.assignStatsMemberIds();
    const uint64_t memberId = party.members().front().statsMemberId;
    save.party = party.snapshot();

    const uint64_t ticks = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / ("openyamm_statistics_save_" + std::to_string(ticks) + ".oysav");
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error);
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    CHECK(loaded->playthroughId == save.playthroughId);
    CHECK(loaded->playthroughTimeline == save.playthroughTimeline);
    REQUIRE_FALSE(loaded->party.members.empty());
    CHECK(loaded->party.members.front().statsMemberId == memberId);
}

TEST_CASE("a save's summary names its playthrough and the time played up to it")
{
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.playthroughId = "9f2c4e0a7d1b4c55a0e3f1d2b6c78e10";
    save.playthroughPlayedSeconds = 22320.0;
    const std::filesystem::path directory = freshDirectory("summary");
    const std::filesystem::path path = directory / "save1.oysav";
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error);

    const std::optional<GameSaveSummary> summary = loadGameSaveSummaryFromPath(path, error);
    REQUIRE_MESSAGE(summary.has_value(), error);
    REQUIRE(summary->playthrough.has_value());
    CHECK(summary->playthrough->id == save.playthroughId);
    CHECK(summary->playthrough->playedSeconds == doctest::Approx(22320.0));

    const std::optional<GameSaveData> loaded = loadGameDataFromPath(path, error);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    CHECK(loaded->playthroughId == save.playthroughId);
    CHECK(loaded->playthroughPlayedSeconds == doctest::Approx(22320.0));

    const std::optional<SavePlaythroughInfo> whole = loadSavePlaythroughInfoFromPath(path, error);
    REQUIRE_MESSAGE(whole.has_value(), error);
    CHECK(whole->id == save.playthroughId);
    CHECK(whole->playedSeconds == doctest::Approx(22320.0));
    std::filesystem::remove_all(directory);
}

TEST_CASE("each playthrough has its own Quicksave and Autosave, and the shared ones move to theirs")
{
    CHECK(quickSavePath("abc") == std::filesystem::path("saves") / "quicksave_abc.oysav");
    CHECK(autosavePath("abc") == std::filesystem::path("saves") / "autosave_abc.oysav");
    CHECK(quickSavePath("") == std::filesystem::path("saves") / "quicksave.oysav");
    CHECK(isQuickSavePath("saves/quicksave.oysav"));
    CHECK(isQuickSavePath("saves/QuickSave_abc.oysav"));
    CHECK_FALSE(isQuickSavePath("saves/quicksaves.oysav"));
    CHECK(isAutosavePath("saves/autosave_legacy-00ff.oysav"));
    CHECK_FALSE(isAutosavePath("saves/save12.oysav"));

    const std::filesystem::path directory = freshDirectory("slots");
    std::string error;
    GameSaveData quick;
    quick.playthroughId = "9f2c4e0a7d1b4c55a0e3f1d2b6c78e10";
    REQUIRE_MESSAGE(saveGameDataToPath(directory / "quicksave.oysav", quick, error), error);
    // A save that names no playthrough stays where it is.
    GameSaveData autosave;
    REQUIRE_MESSAGE(saveGameDataToPath(directory / "autosave.oysav", autosave, error), error);

    migrateSharedSaveSlots(directory);
    CHECK_FALSE(std::filesystem::exists(directory / "quicksave.oysav"));
    CHECK(std::filesystem::exists(directory / "quicksave_9f2c4e0a7d1b4c55a0e3f1d2b6c78e10.oysav"));
    CHECK(std::filesystem::exists(directory / "autosave.oysav"));

    // The playthrough's own file is never replaced by a shared one that turns up later.
    REQUIRE_MESSAGE(saveGameDataToPath(directory / "quicksave.oysav", quick, error), error);
    migrateSharedSaveSlots(directory);
    CHECK(std::filesystem::exists(directory / "quicksave.oysav"));
    std::filesystem::remove_all(directory);
}

TEST_CASE("the save lists read a playthrough's statistics file and the name the player gave it")
{
    const std::filesystem::path directory = freshDirectory("catalog");
    std::string id;

    {
        PlaythroughStatistics statistics;
        statistics.setDirectory(directory);
        statistics.beginNewPlaythrough("mm6", "maw", "nightmare");
        statistics.addPlayTime(125.0, false);
        id = statistics.playthroughId();
        statistics.endPlaythrough();
    }

    const std::optional<PlaythroughStatistics::StoredSummary> stored =
        PlaythroughStatistics::readStoredSummary(directory, id);
    REQUIRE(stored.has_value());
    CHECK(stored->header.startWorld == "mm6");
    CHECK(stored->header.ruleset == "maw");
    CHECK(stored->header.difficulty == "nightmare");
    CHECK_FALSE(stored->header.createdUtc.empty());
    CHECK(stored->playedSeconds == doctest::Approx(125.0));
    CHECK_FALSE(PlaythroughStatistics::readStoredSummary(directory, "0000").has_value());

    CHECK(readPlaythroughNames(directory).empty());
    REQUIRE(writePlaythroughName(directory, id, "Knights: \"no magic\" run"));
    REQUIRE(writePlaythroughName(directory, "legacy-00000000000000ff", "Old party"));
    std::unordered_map<std::string, std::string> names = readPlaythroughNames(directory);
    CHECK(names.size() == 2);
    CHECK(names[id] == "Knights: \"no magic\" run");
    // An empty name takes the playthrough back to its automatic one.
    REQUIRE(writePlaythroughName(directory, id, ""));
    names = readPlaythroughNames(directory);
    CHECK(names.size() == 1);
    CHECK(names["legacy-00000000000000ff"] == "Old party");

    PlaythroughStatistics::removeStored(directory, id);
    CHECK_FALSE(PlaythroughStatistics::readStoredSummary(directory, id).has_value());
    std::filesystem::remove_all(directory);
}

TEST_CASE("a save from before statistics is named a playthrough by its random root seed")
{
    CHECK(PlaythroughStatistics::playthroughIdOfSave("abc", 7) == "abc");
    CHECK(PlaythroughStatistics::playthroughIdOfSave("", 255) == PlaythroughStatistics::legacyPlaythroughId(255));
    CHECK(PlaythroughStatistics::playthroughIdOfSave("", 0).empty());
    CHECK(PlaythroughStatistics::timelinePlayedSeconds("abc", "") == doctest::Approx(0.0));
}

TEST_CASE("a sealed record refuses edits, another kind and another playthrough")
{
    const std::string sealed = PlaythroughSeal::seal(PlaythroughSeal::Kind::Lifetime, "abc", "schema: 1\n");
    CHECK(PlaythroughSeal::looksSealed(sealed));
    CHECK(sealed.find("schema") == std::string::npos);
    REQUIRE(PlaythroughSeal::open(PlaythroughSeal::Kind::Lifetime, "abc", sealed).has_value());
    CHECK(PlaythroughSeal::open(PlaythroughSeal::Kind::Lifetime, "abc", sealed)->text == "schema: 1\n");
    CHECK_FALSE(PlaythroughSeal::open(PlaythroughSeal::Kind::Timeline, "abc", sealed).has_value());
    CHECK_FALSE(PlaythroughSeal::open(PlaythroughSeal::Kind::Lifetime, "abd", sealed).has_value());

    std::string changed = sealed;
    changed.back() = char(changed.back() ^ 1);
    CHECK_FALSE(PlaythroughSeal::open(PlaythroughSeal::Kind::Lifetime, "abc", changed).has_value());
    // Two seals of the same text differ (a fresh nonce each time).
    CHECK(PlaythroughSeal::seal(PlaythroughSeal::Kind::Lifetime, "abc", "schema: 1\n") != sealed);
}

TEST_CASE("a changed sidecar restarts the record from the save and says so")
{
    const std::filesystem::path directory = freshDirectory("tampered");
    std::string id;
    std::string savedTimeline;

    {
        PlaythroughStatistics statistics;
        statistics.setDirectory(directory);
        statistics.beginNewPlaythrough("mm6", "standard", "");
        id = statistics.playthroughId();
        statistics.recordMonsterKilled("Goblin", 3);
        savedTimeline = statistics.serializedTimeline();
        statistics.endPlaythrough();
    }

    std::string bytes = readFile(sidecarPath(directory, id));
    bytes[bytes.size() / 2] = char(bytes[bytes.size() / 2] ^ 0x40);
    writeFile(sidecarPath(directory, id), bytes);

    PlaythroughStatistics statistics;
    statistics.setDirectory(directory);
    statistics.attachLoadedSave(id, 0, savedTimeline, StatLoadKind::Menu, "mm6", "standard", "");
    CHECK(statistics.lifetimeInfo().unverified);
    CHECK(statistics.lifetimeInfo().partial);
    CHECK_FALSE(statistics.lifetimeInfo().clean());
    CHECK(statistics.lifetime().kills == 1);
    statistics.endPlaythrough();
    std::filesystem::remove_all(directory);
}

TEST_CASE("an older sidecar put back next to a newer save is flagged")
{
    const std::filesystem::path directory = freshDirectory("rollback");
    std::string id;
    std::string olderSidecar;
    std::string newerTimeline;

    {
        PlaythroughStatistics statistics;
        statistics.setDirectory(directory);
        statistics.beginNewPlaythrough("mm6", "standard", "");
        id = statistics.playthroughId();
        statistics.writeNow();
        olderSidecar = readFile(sidecarPath(directory, id));
        statistics.recordDeath(member(1, "A"), false, "Lich");
        statistics.writeNow();
        newerTimeline = statistics.serializedTimeline();
        statistics.endPlaythrough();
    }

    writeFile(sidecarPath(directory, id), olderSidecar);
    PlaythroughStatistics statistics;
    statistics.setDirectory(directory);
    statistics.attachLoadedSave(id, 0, newerTimeline, StatLoadKind::Menu, "mm6", "standard", "");
    CHECK(statistics.lifetimeInfo().restoredOlder);
    statistics.endPlaythrough();

    // The flag is sticky: a later session still shows it.
    PlaythroughStatistics later;
    later.setDirectory(directory);
    later.attachLoadedSave(id, 0, newerTimeline, StatLoadKind::Menu, "mm6", "standard", "");
    CHECK(later.lifetimeInfo().restoredOlder);
    later.endPlaythrough();
    std::filesystem::remove_all(directory);
}

TEST_CASE("an assisted playthrough stays assisted in the save and the sidecar")
{
    const std::filesystem::path directory = freshDirectory("assisted");
    std::string id;
    std::string savedTimeline;

    {
        PlaythroughStatistics statistics;
        statistics.setDirectory(directory);
        statistics.beginNewPlaythrough("mm6", "standard", "");
        id = statistics.playthroughId();
        statistics.markAssisted("immortal");
        statistics.markAssisted("immortal");
        statistics.markAssisted("debug console", "gold");
        statistics.markAssisted("debug console", "gold");
        savedTimeline = statistics.serializedTimeline();
        statistics.endPlaythrough();
    }

    PlaythroughStatistics statistics;
    statistics.setDirectory(directory);
    statistics.attachLoadedSave(id, 0, savedTimeline, StatLoadKind::Menu, "mm6", "standard", "");
    CHECK(statistics.lifetimeInfo().assists.count("immortal") == 1);
    CHECK(statistics.timelineInfo().assists.count("immortal") == 1);
    // Once per session, and the console's commands by name.
    CHECK(statistics.lifetimeInfo().assists.at("immortal").sessions == 1);
    CHECK(statistics.lifetimeInfo().assists.at("debug console").commands.at("gold") == 2);
    CHECK_FALSE(statistics.lifetimeInfo().assists.at("immortal").firstUtc.empty());
    CHECK_FALSE(statistics.lifetimeInfo().clean());
    statistics.endPlaythrough();
    std::filesystem::remove_all(directory);
}

TEST_CASE("a changed timeline in a save is not trusted")
{
    PlaythroughStatistics statistics;
    statistics.beginNewPlaythrough("mm6", "standard", "");
    const std::string id = statistics.playthroughId();
    statistics.recordMonsterKilled("Goblin", 3);
    std::string timeline = statistics.serializedTimeline();
    timeline.back() = char(timeline.back() ^ 1);

    PlaythroughStatistics other;
    other.attachLoadedSave(id, 0, timeline, StatLoadKind::Menu, "mm6", "standard", "");
    CHECK(other.timeline().kills == 0);
    CHECK(other.timelineInfo().partial);
    CHECK(other.timelineInfo().unverified);
}
