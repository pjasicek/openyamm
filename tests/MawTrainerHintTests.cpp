#include "doctest/doctest.h"
#include "game/party/Party.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawTexts.h"
#include "game/rules/maw/MawTrainerHints.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
// The synthetic world of TrainerHint.lua's selfTest: maps 1 (Alpha, outdoors, continent 1), 2 (Beta, outdoors, 2),
// 3 (Cave, indoors, 1) and 4 (Gamma, outdoors, continent unknown).
TrainerDirectorySource syntheticSource(bool moves)
{
    TrainerDirectorySource source;
    source.maps[1] = {"Alpha", "out01.odm", 1};
    source.maps[2] = {"Beta", "out02.odm", 2};
    source.maps[3] = {"Cave", "d01.blv", 1};
    source.maps[4] = {"Gamma", "out03.odm", std::nullopt};
    // House 104 has no map; house 0 is never a place even when it maps.
    source.houses[0] = {"Nowhere", 1};
    source.houses[101] = {"Hunter's Hovel", 1};
    source.houses[102] = {"House", 2};
    source.houses[103] = {"  ", 3};
    source.houses[104] = {"Lost", 0};
    source.houses[105] = {"Gamma Hall", 4};
    source.topics[10] = {"Bow", SkillMastery::Expert};
    source.topics[11] = {"Bow", SkillMastery::Master};
    source.topics[12] = {"Sword", SkillMastery::Expert};
    // A topic nobody has.
    source.topics[13] = {"Bow", SkillMastery::Grandmaster};
    source.npcs = {
        {1, "Ann", 101, {10, 0, 0, 0, 0, 0}},
        {2, "Bob", 0, {10}},
        {3, "Cy", 104, {10}},
        {4, "Di", 102, {11, 12}},
        {5, "Ed", 103, {10}},
        {6, "Flo", 105, {10}},
        {7, "Gus", 102, {99}},
    };

    if (moves)
    {
        source.extraHouses[1] = {102, 103, 103, 101};
        source.extraHouses[7] = {101};
    }

    return source;
}

std::string show(const std::vector<TrainerEntry> &entries, bool sorted)
{
    std::vector<std::string> names;

    for (const TrainerEntry &entry : entries)
    {
        names.push_back(entry.name + "@" + std::to_string(entry.houseId));
    }

    if (sorted)
    {
        std::sort(names.begin(), names.end());
    }

    std::string text;

    for (const std::string &name : names)
    {
        text += (text.empty() ? "" : ",") + name;
    }

    return text;
}

std::string show(const std::vector<PickedTrainer> &picked)
{
    std::vector<TrainerEntry> entries;

    for (const PickedTrainer &trainer : picked)
    {
        entries.push_back(trainer.entry);
    }

    return show(entries, false);
}

std::string ranks(const std::vector<PickedTrainer> &picked)
{
    std::string text;

    for (const PickedTrainer &trainer : picked)
    {
        text += std::to_string(trainer.rank);
    }

    return text;
}

PickedTrainer trainer(const std::string &name, const std::string &houseName, const std::string &mapName,
    std::optional<uint32_t> continent, int rank, std::optional<TrainerLink> link = std::nullopt,
    bool outside = false)
{
    PickedTrainer picked;
    picked.entry.name = name;
    picked.entry.houseName = houseName;
    picked.entry.mapName = mapName;
    picked.entry.continent = continent;
    picked.rank = rank;
    picked.link = link;
    picked.outside = outside;
    return picked;
}

MawTrainerHintInfo trainersInfo(MawTrainerHintKind kind, SkillMastery next, uint32_t need, uint32_t have,
    std::optional<uint32_t> continent, std::optional<std::vector<PickedTrainer>> trainers)
{
    MawTrainerHintInfo info;
    info.kind = kind;
    info.nextMastery = next;
    info.requiredLevel = need;
    info.level = have;
    info.currentContinent = continent;
    info.trainers = std::move(trainers);
    return info;
}
}

TEST_CASE("MAW trainer hints index the teachers by skill and mastery")
{
    const TrainerDirectory index = TrainerDirectory::build(syntheticSource(true));
    const auto *pBow = index.find("Bow");
    REQUIRE(pBow != nullptr);
    // House 0 and a house without a map are left out; moved teachers are listed at every house, once.
    CHECK_EQ(show((*pBow)[0], true), "Ann@101,Ann@102,Ann@103,Ed@103,Flo@105");
    CHECK_EQ(show((*pBow)[1], true), "Di@102");
    // A topic nobody has still makes the skill known.
    CHECK((*pBow)[2].empty());
    REQUIRE(index.find("Sword") != nullptr);
    CHECK_EQ(show((*index.find("Sword"))[0], true), "Di@102");
    CHECK(index.find("Axe") == nullptr);
    CHECK_EQ(show((*TrainerDirectory::build(syntheticSource(false)).find("Bow"))[0], true),
        "Ann@101,Ed@103,Flo@105");

    for (const TrainerEntry &entry : (*pBow)[0])
    {
        if (entry.name == "Ann" && entry.houseId == 101)
        {
            CHECK_EQ(entry.houseName, "Hunter's Hovel");
            CHECK_EQ(entry.mapName, "Alpha");
            CHECK_EQ(entry.mapId, 1u);
            CHECK(entry.outdoor);
        }

        // "House" and a blank name are no names.
        if (entry.houseId == 102 || entry.houseId == 103)
        {
            CHECK(entry.houseName.empty());
        }

        if (entry.name == "Ed")
        {
            CHECK_FALSE(entry.outdoor);
        }

        if (entry.name == "Flo")
        {
            CHECK_FALSE(entry.continent.has_value());
        }
    }

    // Padded NPC names are trimmed, and a topic named twice lists the NPC once.
    TrainerDirectorySource padded = syntheticSource(false);
    padded.npcs = {{9, "Pat  ", 101, {10, 10}}};
    const TrainerDirectory paddedIndex = TrainerDirectory::build(padded);
    REQUIRE_EQ((*paddedIndex.find("Bow"))[0].size(), 1u);
    CHECK_EQ((*paddedIndex.find("Bow"))[0][0].name, "Pat");
}

TEST_CASE("MAW trainer hints rank the party's map, one step, the continent, then the rest")
{
    const TrainerDirectory index = TrainerDirectory::build(syntheticSource(true));
    const std::vector<TrainerEntry> &expert = (*index.find("Bow"))[0];
    const TrainerNeighbours none;

    CHECK_EQ(show(pickTrainers(expert, 1, 1, 3, none, std::nullopt)), "Ann@101,Ed@103,Flo@105");
    CHECK_EQ(ranks(pickTrainers(expert, 1, 1, 3, none, std::nullopt)), "023");
    CHECK_EQ(show(pickTrainers(expert, 2, 2, 2, none, std::nullopt)), "Ann@102,Flo@105");
    // Outdoor maps before indoor ones, an unknown continent last.
    CHECK_EQ(show(pickTrainers(expert, 99, std::nullopt, 3, none, std::nullopt)), "Ann@101,Flo@105,Ed@103");
    CHECK_EQ(show(pickTrainers(expert, 3, 1, 3, none, std::nullopt)), "Ann@103,Ed@103,Flo@105");
    CHECK_EQ(pickTrainers(expert, 99, std::nullopt, 1, none, std::nullopt).size(), 1u);
    CHECK(pickTrainers({}, 1, 1, 3, none, std::nullopt).empty());

    // A walk neighbour beats a teacher elsewhere on the continent; neighbours come before the rest of it.
    CHECK_EQ(show(pickTrainers(expert, 99, 1, 1, {{4, TrainerLink::Walk}}, std::nullopt)), "Flo@105");
    CHECK_EQ(show(pickTrainers(expert, 99, 1, 1, none, std::nullopt)), "Ann@101");
    const std::vector<PickedTrainer> linked =
        pickTrainers(expert, 99, 1, 3, {{2, TrainerLink::Route}, {4, TrainerLink::Walk}}, std::nullopt);
    CHECK_EQ(show(linked), "Ann@102,Flo@105,Ed@103");
    CHECK_EQ(ranks(linked), "112");
    CHECK(linked[0].link == TrainerLink::Route);
    CHECK(linked[1].link == TrainerLink::Walk);
    CHECK_FALSE(linked[2].link.has_value());
    CHECK_EQ(show(pickTrainers(expert, 1, 1, 2, {{2, TrainerLink::Route}}, std::nullopt)), "Ann@101,Ed@103");

    // Indoors, the outdoor map the party came from counts as its own, "outside".
    const std::vector<PickedTrainer> indoors = pickTrainers(expert, 3, 1, 3, {{4, TrainerLink::Walk}}, 1);
    CHECK_EQ(show(indoors), "Ann@101,Ed@103,Flo@105");
    CHECK_EQ(ranks(indoors), "001");
    CHECK(indoors[0].outside);
    CHECK_FALSE(indoors[1].outside);
}

TEST_CASE("MAW trainer hints link maps by walking and by coach or boat")
{
    TrainerLinks links;
    links.addWalk(1, 4);
    links.addRoute(1, 4);
    links.addRoute(1, 2);
    links.addRoute(1, 1);
    links.addRoute(2, 1);
    links.addRoute(1, 5, 77);
    links.addRoute(3, 2);
    links.addWalk(3, 6);
    const auto hasQBit = [](uint32_t qbit) { return qbit == 77; };

    const TrainerNeighbours one = links.neighbours(1, std::nullopt, {});
    CHECK(one.at(4) == TrainerLink::Walk);
    CHECK(one.at(2) == TrainerLink::Route);
    CHECK_FALSE(one.contains(1));
    // A route behind a QBit counts once the party has it.
    CHECK_FALSE(one.contains(5));
    CHECK(links.neighbours(1, std::nullopt, hasQBit).contains(5));
    // Routes are one-way.
    CHECK(links.neighbours(2, std::nullopt, {}).at(1) == TrainerLink::Route);
    CHECK(links.neighbours(4, std::nullopt, {}).empty());
    // The party's map and the reference map merged, walking wins.
    const TrainerNeighbours merged = links.neighbours(1, 3, {});
    CHECK(merged.at(2) == TrainerLink::Route);
    CHECK(merged.at(6) == TrainerLink::Walk);
    CHECK(links.neighbours(9, 3, {}).at(6) == TrainerLink::Walk);
    CHECK(links.neighbours(std::nullopt, std::nullopt, {}).empty());
}

TEST_CASE("MAW trainer hints say the next mastery and the nearest teacher")
{
    const PickedTrainer jasp = trainer("Jasp Hunter", "Hunter's Hovel", "Ravenshore", 1, 0);
    const PickedTrainer dalin = trainer("Dalin Keenedge", "Keenedge Residence", "The Pit", 2, 2);
    const PickedTrainer rexella = trainer("Rexella", "", "Paradise Valley", 3, 2);
    const PickedTrainer zed = trainer("Zed", "", "Harmondale", 2, 1);

    CHECK_EQ(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Trainers, SkillMastery::Master, 7, 3, 1,
                 std::vector<PickedTrainer>{jasp, dalin})),
        "<value>Next mastery: Master (skill </><bad>7</><value> required)</>\n"
        " Jasp Hunter - Hunter's Hovel, Ravenshore <good>(this map)</>\n"
        " Dalin Keenedge - Keenedge Residence, The Pit (Antagarich)");
    CHECK_EQ(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Trainers, SkillMastery::Master, 7, 9, 1,
                 std::vector<PickedTrainer>{rexella})),
        "<value>Next mastery: Master (skill </><good>7</><value> required)</>\n Rexella - Paradise Valley (Enroth)");
    // The same continent shows no name; an unknown current continent shows every one.
    CHECK_EQ(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Trainers, SkillMastery::Expert, 4, 4, 2,
                 std::vector<PickedTrainer>{trainer("Zed", "", "Harmondale", 2, 2)})),
        "<value>Next mastery: Expert (skill </><good>4</><value> required)</>\n Zed - Harmondale");
    CHECK_EQ(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Trainers, SkillMastery::Expert, 4, 4,
                 std::nullopt, std::vector<PickedTrainer>{trainer("Zed", "", "Harmondale", 2, 2)})),
        "<value>Next mastery: Expert (skill </><good>4</><value> required)</>\n Zed - Harmondale (Antagarich)");
    CHECK(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Trainers, SkillMastery::Master, 7, 7, 2,
              std::vector<PickedTrainer>{trainer("A", "", "M1", 2, 1, TrainerLink::Walk)}))
              .ends_with("\n A - M1 (next map)"));
    CHECK(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Trainers, SkillMastery::Master, 7, 7, 1,
              std::vector<PickedTrainer>{trainer("A", "", "M1", 2, 1, TrainerLink::Route)}))
              .ends_with("\n A - M1 (coach/boat, Antagarich)"));
    CHECK(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Trainers, SkillMastery::Master, 7, 7, 1,
              std::vector<PickedTrainer>{trainer("A", "", "M1", 1, 0, std::nullopt, true)}))
              .ends_with("\n A - M1 <good>(outside)</>"));
    static_cast<void>(zed);

    // Nobody to name, learned without a teacher, a promotion first, the class's best, the last mastery.
    CHECK_EQ(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::None, SkillMastery::Grandmaster, 10, 3,
                 std::nullopt, std::nullopt)),
        "<value>Next mastery: Grandmaster</>\n No trainer found.");
    CHECK_EQ(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Trainers, SkillMastery::Grandmaster, 10, 3,
                 std::nullopt, std::vector<PickedTrainer>{})),
        "<value>Next mastery: Grandmaster</>\n No trainer found.");
    CHECK_EQ(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Automatic, SkillMastery::Master, 12, 3,
                 std::nullopt, std::nullopt)),
        "<value>Next mastery: Master</>\n Learned automatically at skill 12.");
    CHECK_EQ(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Promotion, SkillMastery::Master, 7, 7, 1,
                 std::vector<PickedTrainer>{jasp})),
        "<value>Next mastery: Master (skill </><good>7</><value> required)</>\n Requires a class promotion first.\n"
        " Jasp Hunter - Hunter's Hovel, Ravenshore <good>(this map)</>");
    CHECK_EQ(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Promotion, SkillMastery::Master, 7, 3,
                 std::nullopt, std::vector<PickedTrainer>{})),
        "<value>Next mastery: Master (skill </><bad>7</><value> required)</>\n Requires a class promotion first.\n"
        " No trainer found.");
    CHECK_EQ(mawComposeTrainerHint(trainersInfo(MawTrainerHintKind::Promotion, SkillMastery::Master, 12, 14,
                 std::nullopt, std::nullopt)),
        "<value>Next mastery: Master (skill </><good>12</><value> required)</>\n Requires a class promotion first.");
    CHECK_EQ(mawComposeTrainerHint({MawTrainerHintKind::ClassMaximum}),
        "<value>Highest mastery for this class reached.</>");
    CHECK_EQ(mawComposeTrainerHint({MawTrainerHintKind::Grandmaster}), "<value>Grandmaster reached.</>");

    // Upstream's colours: the heading (255, 255, 100), met (0, 255, 0) and missing (255, 0, 0) as R5G6B5 codes.
    CHECK_EQ(mawFillText("<value>a</><good>b</><bad>c</>", {}), "\f65516a\f00000\f02016b\f00000\f63488c\f00000");
}

TEST_CASE("MAW trainer hints follow TrainerHint.explain's rules")
{
    const TrainerDirectory index = TrainerDirectory::build(syntheticSource(false));
    MawTrainerHintQuery query;
    query.skill = "Bow";
    query.level = 5;
    query.mastery = SkillMastery::Normal;
    query.classCap = SkillMastery::Grandmaster;
    query.promotionCap = SkillMastery::Grandmaster;
    query.requiredLevel = 4;
    query.currentMap = 3;
    query.currentContinent = 1;
    query.referenceMap = 1;

    std::optional<MawTrainerHintInfo> info = mawExplainTrainerHint(index, query);
    REQUIRE(info);
    CHECK(info->kind == MawTrainerHintKind::Trainers);
    CHECK(info->nextMastery == SkillMastery::Expert);
    REQUIRE(info->trainers);
    REQUIRE_EQ(info->trainers->size(), 1u);
    CHECK_EQ(info->trainers->front().entry.name, "Ann");
    CHECK(info->trainers->front().outside);

    // An unlearned skill, and one nobody teaches with no ladder, say nothing.
    MawTrainerHintQuery unlearned = query;
    unlearned.level = 0;
    CHECK_FALSE(mawExplainTrainerHint(index, unlearned));
    MawTrainerHintQuery untaught = query;
    untaught.skill = "Axe";
    CHECK_FALSE(mawExplainTrainerHint(index, untaught));
    untaught.mastery = SkillMastery::Grandmaster;
    CHECK_FALSE(mawExplainTrainerHint(index, untaught));

    // Grandmaster: nothing left, for a taught or laddered skill.
    MawTrainerHintQuery grand = query;
    grand.mastery = SkillMastery::Grandmaster;
    CHECK(mawExplainTrainerHint(index, grand)->kind == MawTrainerHintKind::Grandmaster);
    untaught.ladder = std::array<uint32_t, 3>{6, 12, 20};
    CHECK(mawExplainTrainerHint(index, untaught)->kind == MawTrainerHintKind::Grandmaster);

    // A party of one masters its utility skills by level, whatever the class.
    MawTrainerHintQuery solo = query;
    solo.soloMastery = true;
    solo.classCap = SkillMastery::Normal;
    solo.promotionCap = SkillMastery::Normal;
    CHECK(mawExplainTrainerHint(index, solo)->kind == MawTrainerHintKind::Automatic);

    // The class and its promotions.
    MawTrainerHintQuery capped = query;
    capped.classCap = SkillMastery::Normal;
    capped.promotionCap = SkillMastery::Normal;
    CHECK(mawExplainTrainerHint(index, capped)->kind == MawTrainerHintKind::ClassMaximum);
    capped.promotionCap = SkillMastery::Expert;
    info = mawExplainTrainerHint(index, capped);
    CHECK(info->kind == MawTrainerHintKind::Promotion);
    CHECK_EQ(info->trainers->size(), 1u);

    // A ladder: learned at its level, or after a promotion.
    MawTrainerHintQuery ladder = query;
    ladder.skill = "Cover";
    ladder.mastery = SkillMastery::Expert;
    ladder.ladder = std::array<uint32_t, 3>{6, 12, 20};
    info = mawExplainTrainerHint(index, ladder);
    CHECK(info->kind == MawTrainerHintKind::Automatic);
    CHECK_EQ(info->requiredLevel, 12u);
    CHECK_EQ(mawComposeTrainerHint(*info), "<value>Next mastery: Master</>\n Learned automatically at skill 12.");
    ladder.classCap = SkillMastery::Expert;
    CHECK(mawExplainTrainerHint(index, ladder)->kind == MawTrainerHintKind::Promotion);
    CHECK_FALSE(mawExplainTrainerHint(index, ladder)->trainers.has_value());

    // A known skill whose mastery nobody teaches.
    MawTrainerHintQuery master = query;
    master.mastery = SkillMastery::Master;
    master.requiredLevel = 10;
    CHECK_EQ(mawComposeTrainerHint(*mawExplainTrainerHint(index, master)),
        "<value>Next mastery: Grandmaster</>\n No trainer found.");
}

TEST_CASE("MAW trainer hints find the game's teachers in a MAW skill popup")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure());
    const OpenYAMM::Tests::RegressionGameData &data = OpenYAMM::Tests::regressionGameData();
    const TrainerDirectory directory = TrainerDirectory::build(data.npcDialogTable, data.mergedTeacherTopicTable,
        data.mergedTeacherAutonoteTable, data.houseTable, data.mapStats, {});
    const MawTrainerHints hints = {&data.classSkillTable, &data.mapStats};

    // Every weapon skill has Expert teachers somewhere; New Sorpigal's neighbours are walks and routes.
    for (const char *pSkill : {"Sword", "Bow", "Staff", "Mace"})
    {
        CAPTURE(pSkill);
        REQUIRE(directory.find(pSkill) != nullptr);
        CHECK_FALSE((*directory.find(pSkill))[0].empty());
    }

    const MapStatsEntry *pSorpigal = data.mapStats.findByFileName("oute3.odm");
    REQUIRE(pSorpigal != nullptr);
    const TrainerNeighbours sorpigal = directory.links().neighbours(uint32_t(pSorpigal->id), std::nullopt, {});
    CHECK(std::any_of(sorpigal.begin(), sorpigal.end(),
        [](const auto &link) { return link.second == TrainerLink::Walk; }));
    CHECK(std::any_of(sorpigal.begin(), sorpigal.end(),
        [](const auto &link) { return link.second == TrainerLink::Route; }));

    RulesetOptions options;
    options.preferences.trainerHints = true;
    MawRules rules(options, MawMapLevels{});
    rules.setTrainerHints(hints);
    rules.setCurrentMap("oute3.odm");
    PartySeed seed;
    Character knight;
    knight.className = "Knight";
    knight.skills["Sword"] = CharacterSkill{"Sword", 5, SkillMastery::Normal};
    seed.members.push_back(knight);
    seed.members.push_back(knight);
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    party.setTrainerDirectory(&directory);
    const SkillTooltipText table = {"Table.", {"N", "E", "M", "G"}};

    const std::string footer = rules.gameRules().skills.skillTooltip(party, party.members()[0], "Sword", table).footer;
    CAPTURE(footer);
    CHECK(footer.starts_with("\f65516Next mastery: Expert (skill \f00000\f02016"));
    // A party that has met no teacher hears of none; Enroth's Ledger of Teachers names the nearest.
    CHECK_NE(footer.find("\n No trainer known yet"), std::string::npos);
    party.addTeacherLedger(3);
    const std::string named = rules.gameRules().skills.skillTooltip(party, party.members()[0], "Sword", table).footer;
    CAPTURE(named);
    CHECK_EQ(named.find("No trainer"), std::string::npos);
    CHECK_NE(named.find("\n "), std::string::npos);
    // An unlearned skill says nothing; nor does anything with the preference off or before the first map.
    CHECK(rules.gameRules().skills.skillTooltip(party, party.members()[0], "Axe", table).footer.empty());
    options.preferences.trainerHints = false;
    rules.setOptions(options);
    CHECK(rules.gameRules().skills.skillTooltip(party, party.members()[0], "Sword", table).footer.empty());
}
