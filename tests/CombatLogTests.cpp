#include "doctest/doctest.h"
#include "game/gameplay/CombatLog.h"
#include "game/party/Party.h"
#include "game/rules/DamagePipeline.h"
#include "game/rules/CombatRules.h"

#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
CombatLogEntry hit(CombatLogKind kind, int amount, bool critical = false)
{
    CombatLogEntry entry;
    entry.kind = kind;
    entry.attacker = kind == CombatLogKind::Dealt ? "Blade" : "Goblin";
    entry.verb = "hits";
    entry.target = kind == CombatLogKind::Dealt ? "Goblin" : "Blade";
    entry.amount = amount;
    entry.critical = critical;
    return entry;
}
}

TEST_CASE("the combat log keeps nothing while off and pairs each hit with its damage stages")
{
    CombatLog log;
    const std::vector<DamageStageRecord> rolled = {{"Rolled", 0, 120}, {"Monster resistance", 120, 100}};
    log.recordStages(false, 100, rolled);
    log.add(hit(CombatLogKind::Dealt, 100));
    CHECK(log.entries().empty());

    log.setRecording(true);
    // A miss's stages (never worded), then the worded hit, then a hit taken.
    log.recordStages(false, 7, {{"Rolled", 0, 7}});
    log.recordStages(false, 100, rolled);
    log.recordStages(true, 40, {{"Armour", 55, 40}});
    log.setGameMinutes(9 * 60 + 39);
    log.add(hit(CombatLogKind::Dealt, 100, true));
    log.add(hit(CombatLogKind::Taken, 40));
    REQUIRE_EQ(log.entries().size(), 2u);
    REQUIRE_EQ(log.entries()[0].stages.size(), 2u);
    CHECK_EQ(log.entries()[0].stages[1].name, "Monster resistance");
    CHECK_EQ(log.entries()[0].stages[1].after, 100);
    CHECK(log.entries()[0].critical);
    CHECK_EQ(log.entries()[0].gameMinutes, doctest::Approx(9 * 60 + 39));
    REQUIRE_EQ(log.entries()[1].stages.size(), 1u);
    CHECK_EQ(log.entries()[1].stages[0].before, 55);

    // The miss's stages were dropped with the claimed hit: a later 7 takes none.
    log.add(hit(CombatLogKind::Dealt, 7));
    CHECK(log.entries().back().stages.empty());

    // An area spell's total takes no stages, even when an amount matches.
    log.recordStages(false, 30, {{"Rolled", 0, 30}});
    log.add(hit(CombatLogKind::Dealt, 30), false);
    CHECK(log.entries().back().stages.empty());

    // Capped at the newest entries; every change moves the revision.
    const uint64_t revision = log.revision();

    for (int index = 0; index < int(CombatLog::MaxEntries) + 10; ++index)
    {
        CombatLogEntry entry = hit(CombatLogKind::Taken, 1);
        entry.attacker = "hit " + std::to_string(index);
        log.add(std::move(entry));
    }

    CHECK_EQ(log.entries().size(), CombatLog::MaxEntries);
    CHECK_EQ(log.entries().back().attacker, "hit " + std::to_string(int(CombatLog::MaxEntries) + 9));
    CHECK_GT(log.revision(), revision);
    log.clear();
    CHECK(log.entries().empty());
}

TEST_CASE("sparring damage previews leave no entries or pending stages for the next real hit")
{
    CombatLog log;
    struct RestoreLog
    {
        CombatLog *previous = boundCombatLog();
        ~RestoreLog() { bindCombatLog(previous); }
    } restore;
    bindCombatLog(&log);
    log.setRecording(true);
    CombatRules rules;
    std::mt19937 rng(123);
    MonsterDamageHit outgoing;
    outgoing.amount = 27;
    outgoing.pRng = &rng;
    CharacterDamageHit incoming;
    const Character member;
    incoming.amount = 19;
    incoming.type = CombatDamageType::Irresistible;
    incoming.pCharacter = &member;
    incoming.pRng = &rng;
    CHECK_EQ(rules.damageToMonster(outgoing, false), 27);
    CHECK_EQ(rules.damageToCharacter(incoming, false), 19);
    CHECK(log.entries().empty());

    log.recordStages(false, 27, {{"real outgoing", 30, 27}});
    log.recordStages(true, 19, {{"real incoming", 21, 19}});
    log.add(hit(CombatLogKind::Dealt, 27));
    log.add(hit(CombatLogKind::Taken, 19));
    REQUIRE_EQ(log.entries()[0].stages.size(), 1);
    CHECK_EQ(log.entries()[0].stages[0].name, "real outgoing");
    REQUIRE_EQ(log.entries()[1].stages.size(), 1);
    CHECK_EQ(log.entries()[1].stages[0].name, "real incoming");
}
