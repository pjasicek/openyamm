#include "doctest/doctest.h"
#include "engine/TextTable.h"
#include "game/gameplay/TrainerDirectory.h"
#include "game/party/Party.h"
#include "game/rules/maw/MawNpcPresence.h"
#include "game/rules/maw/MawTrainerHints.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <set>
#include <sstream>
#include <unordered_map>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
std::vector<std::vector<std::string>> rowsOf(const std::string &text)
{
    const std::optional<OpenYAMM::Engine::TextTable> table = OpenYAMM::Engine::TextTable::parseTabSeparated(text);
    std::vector<std::vector<std::string>> rows;

    for (size_t index = 0; table && index < table->getRowCount(); ++index)
    {
        rows.push_back(table->getRow(index));
    }

    return rows;
}

std::string readSourceFile(const std::string &relativePath)
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath);
    std::stringstream text;
    text << file.rdbuf();
    return text.str();
}

// Maps 1 (Alpha, outdoors, continent 1), 2 (Beta, outdoors, 3), 3 (Cave, indoors, 1), 4 (Gamma, outdoors, 2).
TrainerDirectorySource syntheticSource()
{
    TrainerDirectorySource source;
    source.maps[1] = {"Alpha", "out01.odm", 1};
    source.maps[2] = {"Beta", "OUT02.odm", 3};
    source.maps[3] = {"Cave", "d01.blv", 1};
    source.maps[4] = {"Gamma", "out03.odm", 2};
    source.houses[101] = {"Hunter's Hovel", 1};
    source.houses[102] = {"House", 2};
    // House 103's row names Alpha, but the Cave's script enters it: the place wins.
    source.houses[103] = {"Deep Hall", 1};
    source.houses[104] = {"Gamma Hall", 4};
    source.topics[10] = {"Bow", SkillMastery::Expert, 5, 0, 0};
    source.topics[11] = {"Bow", SkillMastery::Master, 5, 4000, 8};
    source.topics[12] = {"Sword", SkillMastery::Expert, 1, 0, 0};
    source.topics[13] = {"Sword", SkillMastery::Grandmaster, 1, 0, 0};
    source.npcs = {
        {1, "Ann", 101, {10, 0, 0}},
        {2, "Bob", 102, {12}},
        {3, "Cy", 103, {11}},
        {4, "Di", 104, {10}},
        // Ed teaches nothing in npc.txt; a script gives him Grand Master Sword.
        {5, "Ed", 102, {0, 0, 0, 0}},
    };
    source.extraHouses[1] = {104};
    source.autonotes[uint64_t(10) << 32 | 1] = 501;
    source.autonotes[uint64_t(11) << 32 | 3] = 502;
    source.autonotes[uint64_t(10) << 32 | 4] = 503;
    std::string error;
    REQUIRE(source.places.loadFromRows(rowsOf(
        "House\tMap\tKind\tMarker map\tX\tY\tEntrance chain\n"
        "101\tout01.odm\tdoor\tout01.odm\t100\t-200\t\n"
        "103\td01.blv\tentrance\tout01.odm\t-300\t400\tout01.odm>d01.blv\n"
        "104\tout03.odm\tindoor\t\t\t\t\n"),
        error));
    return source;
}

std::string names(const std::vector<TrainerEntry> &entries)
{
    std::vector<std::string> list;

    for (const TrainerEntry &entry : entries)
    {
        list.push_back(entry.name + "@" + std::to_string(entry.houseId));
    }

    std::sort(list.begin(), list.end());
    std::string text;

    for (const std::string &name : list)
    {
        text += (text.empty() ? "" : ",") + name;
    }

    return text;
}

const TrainerEntry *findEntry(const TrainerDirectory &directory, const std::string &skill, size_t mastery,
    uint32_t npcId, uint32_t houseId)
{
    const auto *pSkill = directory.find(skill);

    if (pSkill == nullptr)
    {
        return nullptr;
    }

    for (const TrainerEntry &entry : (*pSkill)[mastery])
    {
        if (entry.npcId == npcId && entry.houseId == houseId)
        {
            return &entry;
        }
    }

    return nullptr;
}
}

TEST_CASE("trainer places read door, entrance and indoor rows and refuse broken ones")
{
    TrainerPlaceTable table;
    std::string error;
    REQUIRE(table.loadFromRows(rowsOf(
        "# generated\n"
        "House\tMap\tKind\tMarker map\tX\tY\tEntrance chain\n"
        "7\tOUT01.ODM\tdoor\tOUT01.ODM\t12.5\t-8\t\n"
        "8\td01.blv\tentrance\tout02.odm\t1\t2\tout02.odm>d01.blv\n"
        "9\td02.blv\tindoor\t\t\t\t\n"),
        error));
    CHECK_EQ(table.size(), 3u);
    REQUIRE(table.find(7) != nullptr);
    CHECK(table.find(7)->kind == TrainerPlaceKind::Door);
    CHECK_EQ(table.find(7)->mapFileName, "out01.odm");
    CHECK_EQ(table.find(7)->x, doctest::Approx(12.5));
    CHECK(table.find(8)->kind == TrainerPlaceKind::Entrance);
    CHECK_EQ(table.find(8)->markerMapFileName, "out02.odm");
    CHECK(table.find(9)->kind == TrainerPlaceKind::Indoor);
    CHECK(table.find(10) == nullptr);

    // A world's later row replaces the engine's.
    REQUIRE(table.loadFromRows(rowsOf("7\tout05.odm\tdoor\tout05.odm\t1\t1\t\n"), error));
    CHECK_EQ(table.find(7)->mapFileName, "out05.odm");

    TrainerPlaceTable broken;
    CHECK_FALSE(broken.loadFromRows(rowsOf("7\tout01.odm\twindow\t\t\t\t\n"), error));
    CHECK_NE(error.find("window"), std::string::npos);
    CHECK_FALSE(broken.loadFromRows(rowsOf("7\tout01.odm\tdoor\t\t\t\t\n"), error));
}

TEST_CASE("the trainer directory lists teachers with their place, note and requirement")
{
    const TrainerDirectory directory = TrainerDirectory::build(syntheticSource());
    REQUIRE(directory.find("Bow") != nullptr);
    CHECK_EQ(names((*directory.find("Bow"))[0]), "Ann@101,Ann@104,Di@104");
    CHECK_EQ(names((*directory.find("Bow"))[1]), "Cy@103");
    CHECK_EQ(names((*directory.find("Sword"))[0]), "Bob@102");
    // A topic nobody teaches still lists its skill.
    CHECK((*directory.find("Sword"))[2].empty());
    CHECK(directory.find("Axe") == nullptr);

    const TrainerEntry *pAnn = findEntry(directory, "Bow", 0, 1, 101);
    REQUIRE(pAnn != nullptr);
    CHECK_EQ(pAnn->houseName, "Hunter's Hovel");
    CHECK_EQ(pAnn->mapName, "Alpha");
    CHECK_EQ(pAnn->mapFileName, "out01.odm");
    CHECK(pAnn->continent == 1u);
    CHECK(pAnn->outdoor);
    CHECK(pAnn->autonoteId == 501u);
    CHECK_FALSE(pAnn->extraHouse);
    CHECK_EQ(pAnn->skillId, 5u);
    REQUIRE(pAnn->place.has_value());
    CHECK(pAnn->place->kind == TrainerPlaceKind::Door);
    CHECK_EQ(pAnn->markerMapName, "Alpha");

    // A moved teacher (MAW's extra houses) is listed there too, marked, with the same note.
    const TrainerEntry *pMoved = findEntry(directory, "Bow", 0, 1, 104);
    REQUIRE(pMoved != nullptr);
    CHECK(pMoved->extraHouse);
    CHECK(pMoved->continent == 2u);
    CHECK(pMoved->autonoteId == 501u);
    REQUIRE(pMoved->place.has_value());
    CHECK(pMoved->place->kind == TrainerPlaceKind::Indoor);

    // The house the Cave's script enters is in the Cave, marked on Alpha's entrance.
    const TrainerEntry *pCy = findEntry(directory, "Bow", 1, 3, 103);
    REQUIRE(pCy != nullptr);
    CHECK_EQ(pCy->mapName, "Cave");
    CHECK_FALSE(pCy->outdoor);
    CHECK(pCy->place->kind == TrainerPlaceKind::Entrance);
    CHECK_EQ(pCy->markerMapName, "Alpha");
    CHECK_EQ(pCy->requiredGold, 4000u);
    CHECK_EQ(pCy->requiredSkill, 8u);

    // "House" is no name; a house with no place row has no marker.
    const TrainerEntry *pBob = findEntry(directory, "Sword", 0, 2, 102);
    REQUIRE(pBob != nullptr);
    CHECK(pBob->houseName.empty());
    CHECK_FALSE(pBob->place.has_value());
    CHECK_EQ(pBob->mapFileName, "out02.odm");

    // The continent's notes, without the moved teachers' copies elsewhere.
    CHECK_EQ(directory.continentAutonotes(1), std::vector<uint32_t>{501, 502});
    CHECK_EQ(directory.continentAutonotes(2), std::vector<uint32_t>{503});
    CHECK(directory.continentAutonotes(3).empty());
    CHECK(directory.mapContinent(2) == 3u);
    CHECK_FALSE(directory.mapContinent(99).has_value());
}

TEST_CASE("the trainer directory follows the party's scripted topics and houses")
{
    const TrainerDirectory directory = TrainerDirectory::build(syntheticSource());
    Party party;
    // Nothing changed: the directory itself.
    CHECK(&directory.forParty(party) == &directory);

    // A map-load script gives Ed Grand Master Sword (as MMMerge's Enroth Grand Masters) and takes Bob's lesson.
    party.setNpcTopicOverride(5, 3, 13);
    party.setNpcTopicOverride(2, 0, 0);
    const TrainerDirectory &scripted = directory.forParty(party);
    CHECK(&scripted != &directory);
    CHECK_EQ(names((*scripted.find("Sword"))[2]), "Ed@102");
    CHECK((*scripted.find("Sword"))[0].empty());
    // The same state reuses the directory built for it.
    CHECK(&directory.forParty(party) == &scripted);

    // A moved NPC teaches from its new house; one gone for good teaches nowhere.
    party.setNpcHouseOverride(4, 101);
    party.setNpcUnavailable(3, true);
    const TrainerDirectory &moved = directory.forParty(party);
    CHECK_EQ(names((*moved.find("Bow"))[0]), "Ann@101,Ann@104,Di@101");
    CHECK((*moved.find("Bow"))[1].empty());
}

TEST_CASE("a trainer is known by its note, its map pin or the continent's ledger")
{
    const TrainerDirectory directory = TrainerDirectory::build(syntheticSource());
    const TrainerEntry &ann = *findEntry(directory, "Bow", 0, 1, 101);
    const TrainerEntry &bob = *findEntry(directory, "Sword", 0, 2, 102);
    Party party;
    CHECK_FALSE(trainerKnown(ann, party));
    CHECK_FALSE(trainerKnown(bob, party));

    party.setAutonote(501, true);
    CHECK(trainerKnown(ann, party));

    // Bob has no note: talking to him pins the lesson on the map he stood on (continent 3, Expert, skill 1).
    CHECK_EQ(teacherMapNoteId(3, SkillMastery::Expert, 1), 3101u);
    CHECK_EQ(teacherMapNoteId(1, SkillMastery::Grandmaster, 38), 1338u);
    JournalMapNote pin;
    pin.id = 3101;
    pin.mapFileName = "out02.odm";
    party.setJournalMapNote(pin);
    CHECK(trainerKnown(bob, party));

    Party ledger;
    ledger.addTeacherLedger(1);
    CHECK(trainerKnown(ann, ledger));
    CHECK_FALSE(trainerKnown(bob, ledger));
    CHECK(trainerKnown(*findEntry(directory, "Bow", 1, 3, 103), ledger));
}

TEST_CASE("the trainer finder's search matches every word in any field")
{
    const std::vector<std::string> fields = {"Sword", "Grand Master", "Grandmaster", "Bart the Fair", "Free Haven"};
    CHECK(trainerSearchMatches("", fields));
    CHECK(trainerSearchMatches("sword", fields));
    CHECK(trainerSearchMatches("SWORD  grand", fields));
    CHECK(trainerSearchMatches("haven bart", fields));
    CHECK_FALSE(trainerSearchMatches("sword expert", fields));
    CHECK_FALSE(trainerSearchMatches("axe", fields));
    // Words do not run across fields.
    CHECK_FALSE(trainerSearchMatches("fairfree", fields));
}

TEST_CASE("the Ledger of Teachers takes its price and names the continent's teachers")
{
    TrainerDirectorySource source = syntheticSource();
    const TrainerDirectory plain = TrainerDirectory::build(source);
    TeacherLedgerSettings settings;
    std::string error;
    REQUIRE(settings.loadFromYaml("price: 1500\nbought: The ledger of {continent}, {price} gold.\n", error));
    CHECK_EQ(settings.price, 1500);
    CHECK_EQ(settings.fill(settings.bought, "Jadame"), "The ledger of Jadame, 1500 gold.");
    CHECK_FALSE(TeacherLedgerSettings{}.loadFromYaml("price: -1\n", error));

    Party party;
    party.addGold(1999);
    CHECK_EQ(plain.ledger().price, 2000);
    CHECK_FALSE(buyTeacherLedger(party, plain, 1));
    CHECK_EQ(party.gold(), 1999);
    CHECK_FALSE(party.hasTeacherLedger(1));

    party.addGold(1);
    REQUIRE(buyTeacherLedger(party, plain, 1));
    CHECK_EQ(party.gold(), 0);
    CHECK(party.hasTeacherLedger(1));
    CHECK(party.hasAutonote(501));
    CHECK(party.hasAutonote(502));
    // Another continent's notes stay unfound, and a second ledger of the same continent is not sold.
    CHECK_FALSE(party.hasAutonote(503));
    party.addGold(5000);
    CHECK_FALSE(buyTeacherLedger(party, plain, 1));
    CHECK_EQ(party.gold(), 5000);

    // The ledger survives the party's snapshot (saves keep Party::Snapshot).
    Party restored;
    restored.restoreSnapshot(party.snapshot());
    CHECK(restored.hasTeacherLedger(1));
    CHECK_FALSE(restored.hasTeacherLedger(2));
}

TEST_CASE("MAW trainer hints name only the teachers the party knows")
{
    const TrainerDirectory directory = TrainerDirectory::build(syntheticSource());
    MawTrainerHintQuery query;
    query.skill = "Bow";
    query.level = 5;
    query.mastery = SkillMastery::Normal;
    query.classCap = SkillMastery::Grandmaster;
    query.promotionCap = SkillMastery::Grandmaster;
    query.requiredLevel = 4;
    query.currentMap = 1;
    query.currentContinent = 1;
    Party party;
    query.known = [&party](const TrainerEntry &entry) { return trainerKnown(entry, party); };

    std::optional<MawTrainerHintInfo> info = mawExplainTrainerHint(directory, query);
    REQUIRE(info);
    CHECK(info->unknownTrainers);
    CHECK_EQ(mawComposeTrainerHint(*info),
        "<value>Next mastery: Expert (skill </><good>4</><value> required)</>\n"
        " No trainer known yet: a tavern sells the Ledger of Teachers.");

    // Di's note names Di, though Ann stands nearer.
    party.setAutonote(503, true);
    info = mawExplainTrainerHint(directory, query);
    REQUIRE(info->trainers);
    REQUIRE_EQ(info->trainers->size(), 1u);
    CHECK_EQ(info->trainers->front().entry.name, "Di");
    CHECK_FALSE(info->unknownTrainers);

    party.addTeacherLedger(1);
    info = mawExplainTrainerHint(directory, query);
    CHECK_EQ(info->trainers->front().entry.name, "Ann");
}

TEST_CASE("every teacher house of the game's tables has a trainer place")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure());
    const OpenYAMM::Tests::RegressionGameData &data = OpenYAMM::Tests::regressionGameData();
    TrainerPlaceTable places;
    std::string error;
    REQUIRE(places.loadFromRows(rowsOf(readSourceFile("assets_dev/engine/data_tables/trainer_places.txt")), error));
    CHECK_GT(places.size(), 300u);

    // MAW's moved teachers too: their extra houses must be located for MAW games.
    NpcDialogTable npcs = data.npcDialogTable;
    std::unordered_map<uint32_t, std::vector<uint32_t>> extraHouses;
    REQUIRE(loadMawNpcExtraHouses(readSourceFile("assets_dev/engine/rulesets/maw/data/npc_extra_houses.yml"),
        extraHouses, error));
    npcs.setExtraHouses(extraHouses);
    const TrainerDirectory directory = TrainerDirectory::build(npcs, data.mergedTeacherTopicTable,
        data.mergedTeacherAutonoteTable, data.houseTable, data.mapStats, places);

    // Houses the tool cannot locate, with why. Rerun `python3 -I tools/trainer_places.py` after a teacher, house or
    // map change; a house missing here and from the file fails below.
    const std::set<uint32_t> skipped = {
        // Poundlin Lotts (Expert Shield, Erathia): no face or entity of 7out03.odm carries door event 74.
        929,
    };
    std::set<uint32_t> missing;
    std::array<size_t, 4> perContinent = {};
    std::array<size_t, 4> withNotes = {};

    for (const auto &[skill, masteries] : directory.skills())
    {
        for (const std::vector<TrainerEntry> &entries : masteries)
        {
            for (const TrainerEntry &entry : entries)
            {
                if (!entry.place && !skipped.contains(entry.houseId))
                {
                    missing.insert(entry.houseId);
                }

                if (entry.continent && *entry.continent < perContinent.size() && !entry.extraHouse)
                {
                    ++perContinent[*entry.continent];
                    withNotes[*entry.continent] += entry.autonoteId ? 1 : 0;
                }
            }
        }
    }

    std::string missingText;

    for (uint32_t houseId : missing)
    {
        missingText += " " + std::to_string(houseId);
    }

    CAPTURE(missingText);
    CHECK(missing.empty());
    // Every continent has its teachers; Jadame's and Antagarich's have teacher notes, Enroth's (MM6) have none.
    CHECK_GT(perContinent[1], 80u);
    CHECK_GT(perContinent[2], 100u);
    CHECK_GT(perContinent[3], 60u);
    CHECK_EQ(withNotes[1], perContinent[1]);
    CHECK_GT(withNotes[2], perContinent[2] * 9 / 10);
    CHECK_EQ(withNotes[3], 0u);
    // Every place row's door is on the map the directory names for the house.
    const TrainerEntry *pDoor = nullptr;

    for (const TrainerEntry &entry : (*directory.find("Sword"))[0])
    {
        if (entry.place && entry.place->kind == TrainerPlaceKind::Door)
        {
            pDoor = &entry;
            CHECK_EQ(entry.place->mapFileName, entry.mapFileName);
        }
    }

    CHECK(pDoor != nullptr);
}
