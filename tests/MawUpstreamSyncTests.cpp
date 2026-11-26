#include "doctest/doctest.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/rules/CombatRules.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/maw/MawBalanceModel.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/SpellTable.h"

#include <string>

using namespace OpenYAMM::Game;

// The rules of the MAW 88a9d7b4 sync (devdocs/maw/UPSTREAM_SYNC_88a9d7b4.md) that no other suite covers.
TEST_CASE("MAW's denser difficulties cut area damage (sync 88a9d7b4 item 6)")
{
    CHECK_EQ(mawDensityAreaMultiplier(1), doctest::Approx(1));
    CHECK_EQ(mawDensityAreaMultiplier(3), doctest::Approx(1));
    CHECK_EQ(mawDensityAreaMultiplier(4), doctest::Approx(0.9));
    CHECK_EQ(mawDensityAreaMultiplier(5), doctest::Approx(0.9));
    CHECK_EQ(mawDensityAreaMultiplier(6), doctest::Approx(0.8));
    CHECK_EQ(mawDensityAreaMultiplier(7), doctest::Approx(0.7));
    CHECK_EQ(mawDensityAreaMultiplier(8), doctest::Approx(0.65));
    CHECK_EQ(mawDensityAreaMultiplier(9), doctest::Approx(0.6));
    CHECK_EQ(MawCarnageDamageMultiplier, doctest::Approx(0.4));
}

TEST_CASE("Under MAW a missile or spell staggers a monster once per 3 game minutes, a blow always (item 15)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const MonsterRules &monsters = rules.gameRules().monsters;
    const uint64_t goblin = mapActorKey("out01.odm", 4);
    const uint64_t other = mapActorKey("out01.odm", 5);

    CHECK(monsters.allowsHitReaction(goblin, false, 100.0f));
    CHECK_FALSE(monsters.allowsHitReaction(goblin, false, 101.0f));
    // A blow still staggers it, and does not restart the wait.
    CHECK(monsters.allowsHitReaction(goblin, true, 101.5f));
    CHECK_FALSE(monsters.allowsHitReaction(goblin, false, 102.9f));
    CHECK(monsters.allowsHitReaction(goblin, false, 103.0f));
    // Each monster waits on its own.
    CHECK(monsters.allowsHitReaction(other, false, 103.0f));
    // A map load forgets them all.
    monsters.mapLoaded("out01.odm", false);
    CHECK(monsters.allowsHitReaction(goblin, false, 103.5f));

    const MonsterRules standard;
    CHECK(standard.allowsHitReaction(goblin, false, 1.0f));
    CHECK(standard.allowsHitReaction(goblin, false, 1.0f));
}

TEST_CASE("MAW's ordinary Arena bouts pay a million gold in a game, Standard's every reward (item 16)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const MonsterRules &monsters = rules.gameRules().monsters;

    CHECK_EQ(monsters.arenaWinGold(600000), 600000);
    CHECK_EQ(monsters.arenaWinGold(600000), 400000);
    CHECK_EQ(monsters.arenaWinGold(5000), 0);
    CHECK_EQ(rules.state().arenaGoldPaid, 1000000u);

    const MonsterRules standard;
    CHECK_EQ(standard.arenaWinGold(600000), 600000);
    CHECK_EQ(standard.arenaWinGold(600000), 600000);
}

TEST_CASE("Under MAW each caster may cast Divine Intervention once a game day (item 14)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;
    const uint32_t divineIntervention = spellIdValue(SpellId::DivineIntervention);
    Character priest;
    priest.name = "Priest";
    priest.className = "Cleric";
    priest.level = 50;
    Character other = priest;
    other.name = "Other";
    PartySeed seed;
    seed.members = {priest, other};
    Party party;
    party.seed(seed);
    party.setGameMinutes(1000.0f);

    CHECK_FALSE(spells.castRefusal(party, 0, divineIntervention).has_value());
    spells.afterCast(party, 0, divineIntervention, SpellTable{}, false, false);
    CHECK(spells.castRefusal(party, 0, divineIntervention).has_value());
    // The other member's day is their own, and other spells are free.
    CHECK_FALSE(spells.castRefusal(party, 1, divineIntervention).has_value());
    CHECK_FALSE(spells.castRefusal(party, 0, 68).has_value());

    party.setGameMinutes(1000.0f + 24 * 60 - 1);
    CHECK(spells.castRefusal(party, 0, divineIntervention).has_value());
    party.setGameMinutes(1000.0f + 24 * 60);
    CHECK_FALSE(spells.castRefusal(party, 0, divineIntervention).has_value());
}
