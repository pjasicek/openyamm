#include "PartySpellTestHarness.h"
#include "doctest/doctest.h"
#include "game/rules/ExperienceRules.h"
#include "game/rules/maw/MawGameState.h"
#include "game/rules/maw/MawMonsterRules.h"
#include "game/ui/GameplayMapProgressBar.h"

#include <string>

using namespace OpenYAMM::Game;

namespace
{
MapKillProgress kills(const std::string &map, bool indoor, int counted, int slain, int hidden = 0)
{
    MapKillProgress progress;
    progress.mapFileName = map;
    progress.indoor = indoor;
    progress.countedMonsters = counted;
    progress.slainMonsters = slain;
    progress.hiddenMonsters = hidden;
    return progress;
}
}

TEST_CASE("MAW map progress: the normalised percent, slain of needed and the revival mark (maw_map_progress)")
{
    MawMapProgressFacts facts;
    facts.revivalRules = true;

    // 300 monsters need 0.99^3 of them: 292. 112 slain is MAW's 38.5 %, the revival line at 65 % of the counted.
    std::optional<RulesetMapProgress> progress = mawMapProgress(kills("d05.blv", true, 300, 112, 3), facts);
    REQUIRE(progress);
    CHECK_EQ(progress->kind, RulesetMapProgress::Kind::Map);
    CHECK(progress->percent == doctest::Approx(38.5));
    CHECK_EQ(progress->needed, 292);
    CHECK(progress->requiredShare == doctest::Approx(0.970299));
    CHECK_EQ(progress->hidden, 3);
    CHECK(progress->revival);
    CHECK_EQ(progress->revivalSlain, 195);
    CHECK(progress->revivalPosition == doctest::Approx(0.65 / 0.970299));
    CHECK_FALSE(progress->revivalPassed);
    CHECK_FALSE(progress->complete);
    CHECK_EQ(GameplayMapProgressBar::tabText(*progress, false), "38.5 % \xB7 112 / 292");
    CHECK_EQ(GameplayMapProgressBar::tabText(*progress, true), "38.5 %");

    // Past 65 % the mark is passed; so it is once the map is weakened, though summons thin the share again.
    progress = mawMapProgress(kills("d05.blv", true, 300, 210), facts);
    CHECK(progress->percent == doctest::Approx(72.1));
    CHECK(progress->revivalPassed);
    facts.weakened = true;
    CHECK(mawMapProgress(kills("d05.blv", true, 400, 210), facts)->revivalPassed);
    facts.weakened = false;

    // 292 of 300 completes: full, no mark, the count of all.
    progress = mawMapProgress(kills("d05.blv", true, 300, 292), facts);
    CHECK(progress->complete);
    CHECK(progress->percent == doctest::Approx(100.0));
    CHECK_FALSE(progress->revival);
    CHECK_EQ(GameplayMapProgressBar::tabText(*progress, false), "Cleared \xB7 292 / 300");
    CHECK_EQ(GameplayMapProgressBar::tabText(*progress, true), "100 %");

    // Cleared since the refill stays full and gold when summons add monsters.
    facts.cleared = true;
    progress = mawMapProgress(kills("d05.blv", true, 320, 292), facts);
    CHECK(progress->complete);
    CHECK(progress->percent == doctest::Approx(100.0));
    facts.cleared = false;

    // No mark outdoors or without the revival rules.
    CHECK_FALSE(mawMapProgress(kills("out05.odm", false, 300, 112), facts)->revival);
    facts.revivalRules = false;
    CHECK_FALSE(mawMapProgress(kills("d05.blv", true, 300, 112), facts)->revival);

    // 180 outdoors need 179; every one in Road to Insanity and Beyond Madness.
    progress = mawMapProgress(kills("out05.odm", false, 180, 0), facts);
    CHECK_EQ(GameplayMapProgressBar::tabText(*progress, false), "0 % \xB7 0 / 179");
    facts.insanityRules = true;
    CHECK_EQ(mawMapProgress(kills("out05.odm", false, 180, 0), facts)->needed, 180);
    facts.insanityRules = false;

    // No counted monsters: no bar.
    CHECK_FALSE(mawMapProgress(kills("d09.blv", true, 0, 0), facts));
}

TEST_CASE("MAW map progress: the reward line, dimension runs and the Endless Arena (maw_map_progress)")
{
    MawMapProgressFacts facts;
    std::optional<RulesetMapProgress> progress = mawMapProgress(kills("d05.blv", true, 300, 10), facts);
    CHECK_FALSE(progress->rewardPaid);
    CHECK_EQ(progress->reward, "experience, gold, materials");
    facts.austerity = true;
    CHECK_EQ(mawMapProgress(kills("d05.blv", true, 300, 10), facts)->reward, "experience and gold");
    facts.austerity = false;
    facts.completedBefore = true;
    CHECK(mawMapProgress(kills("d05.blv", true, 300, 10), facts)->rewardPaid);

    // A dimension run on the completed map: its power and affixes; it counts for the quest.
    MawDimensionRun run;
    run.power = 12;
    run.affixes = {4, 9, 17, 0};
    facts.pDimensionRun = &run;
    progress = mawMapProgress(kills("d05.blv", true, 240, 151), facts);
    CHECK_EQ(progress->kind, RulesetMapProgress::Kind::DimensionRun);
    CHECK_EQ(progress->dimensionPower, 12);
    CHECK_EQ(progress->dimensionAffixes, 3);
    CHECK(progress->percent == doctest::Approx(64.2));
    CHECK_EQ(progress->needed, 236);
    CHECK_FALSE(progress->rewardPaid);
    CHECK_EQ(progress->reward, "counts for the Dimensional Maps quest");
    facts.beyondMadness = true;
    CHECK_EQ(mawMapProgress(kills("d05.blv", true, 240, 151), facts)->reward,
        "experience, gold, materials");
    facts.beyondMadness = false;
    run.completed = true;
    CHECK(mawMapProgress(kills("d05.blv", true, 240, 151), facts)->rewardPaid);
    facts.pDimensionRun = nullptr;

    // The Arena: the wave's level and progress, nothing between bouts.
    facts.arenaLevel = 5;
    facts.arenaPercent = 60;
    progress = mawMapProgress(kills("d42.blv", true, 40, 12), facts);
    REQUIRE(progress);
    CHECK_EQ(progress->kind, RulesetMapProgress::Kind::Arena);
    CHECK_EQ(GameplayMapProgressBar::tabText(*progress, false), "Endless Arena \xB7 Level 5 \xB7 60 %");
    CHECK_EQ(GameplayMapProgressBar::tabText(*progress, true), "60 %");
    CHECK_NE(GameplayMapProgressBar::popupBody(*progress).find("Wave level: 5"), std::string::npos);
    facts.arenaLevel = 0;
    CHECK_FALSE(mawMapProgress(kills("d42.blv", true, 40, 12), facts));
}

TEST_CASE("Map progress popup and Standard rules (maw_map_progress)")
{
    MawMapProgressFacts facts;
    facts.revivalRules = true;
    const std::optional<RulesetMapProgress> progress = mawMapProgress(kills("d05.blv", true, 300, 112, 3), facts);
    REQUIRE(progress);
    CHECK_EQ(GameplayMapProgressBar::popupBody(*progress),
        "Slain: 112 of 300\n"
        "Needed to complete: 292 (97 %)\n"
        "Alive: 188, 3 hidden, not counted\n"
        "Dead rise again on leaving: until 195 slain\n"
        "Reward: experience, gold, materials");
    CHECK_EQ(GameplayMapProgressBar::percentText(97.0299), "97 %");
    CHECK_EQ(GameplayMapProgressBar::percentText(98.01), "98 %");

    // Standard shows no bar.
    const MonsterRules standard;
    const OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    CHECK_FALSE(standard.mapProgress(world));
}
