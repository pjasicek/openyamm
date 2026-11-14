#include "doctest/doctest.h"

#include "game/gameplay/GameplayCombatController.h"
#include "game/party/Party.h"

using namespace OpenYAMM::Game;

namespace
{
PartySeed shieldBearerSeed(SkillMastery mastery)
{
    PartySeed seed = {};
    Character member = {};
    member.name = "Tester";
    member.className = "Knight";
    member.maxHealth = 500;
    member.health = 500;
    member.skills["Shield"] = {"Shield", 4, mastery};
    seed.members.push_back(member);
    return seed;
}
}

TEST_CASE("a raised shield takes its mastery's share of a physical blow and counts the block")
{
    Party party;
    party.seed(shieldBearerSeed(SkillMastery::Master));
    const Character &member = *party.member(0);

    // Not raised: the blow passes whole.
    CHECK(GameplayCombatController::shieldBlockedDamage(party, member, 0, CombatDamageType::Physical, 100) == 100);
    CHECK(party.shieldBlockSerial() == 0);

    party.setShieldRaisedMember(0);
    CHECK(GameplayCombatController::shieldBlockedDamage(party, member, 0, CombatDamageType::Physical, 100) == 30);
    CHECK(party.shieldBlockSerial() == 1);
    // Magic is not blocked, and nothing is counted for it.
    CHECK(GameplayCombatController::shieldBlockedDamage(party, member, 0, CombatDamageType::Fire, 100) == 100);
    CHECK(party.shieldBlockSerial() == 1);

    Party novice;
    novice.seed(shieldBearerSeed(SkillMastery::Normal));
    novice.setShieldRaisedMember(0);
    CHECK(GameplayCombatController::shieldBlockedDamage(novice, *novice.member(0), 0, CombatDamageType::Physical, 100)
        == 60);
}
