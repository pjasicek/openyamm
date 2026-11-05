#include "doctest/doctest.h"

#include "game/gameplay/ActorRepositionRules.h"
#include "game/gameplay/GameplayActorAiSystem.h"
#include "game/gameplay/Mm9ActorRules.h"

#include <array>
#include <optional>
#include <string>
#include <vector>

using OpenYAMM::Game::ActorAiAnimationState;
using OpenYAMM::Game::ActorAiDecision;
using OpenYAMM::Game::ActorAiDecisionKind;
using OpenYAMM::Game::ActorAiFacts;
using OpenYAMM::Game::ActorAiFrameFacts;
using OpenYAMM::Game::ActorAiFrameResult;
using OpenYAMM::Game::ActorAiMotionState;
using OpenYAMM::Game::ActorAiTargetKind;
using OpenYAMM::Game::ActorAiUpdate;
using OpenYAMM::Game::GameplayActorAiSystem;
using OpenYAMM::Game::Mm9AiArchetype;
using OpenYAMM::Game::Mm9AiPlacement;
using OpenYAMM::Game::Mm9AiProfile;
using OpenYAMM::Game::Mm9AiRanged;
using OpenYAMM::Game::Mm9AiWince;
using OpenYAMM::Game::Mm9PerceptionInput;
using OpenYAMM::Game::Mm9RunAwayInput;
using OpenYAMM::Game::Mm9ShotLine;

namespace
{
// An MM9 crawler (a Grey Wolf's numbers) facing +x at the origin, its target the party 1 000 units ahead.
ActorAiFacts makeMm9Walker(Mm9AiArchetype archetype = Mm9AiArchetype::Crawler)
{
    ActorAiFacts actor = {};
    actor.actorIndex = 0;
    actor.actorId = 7;
    actor.identity.actorId = 7;
    actor.identity.monsterId = 9114;
    actor.identity.hostilityType = 4;
    actor.stats.currentHp = 120;
    actor.stats.maxHp = 120;
    actor.stats.radius = 40;
    actor.stats.height = 120;
    actor.runtime.motionState = ActorAiMotionState::Standing;
    actor.runtime.animationState = ActorAiAnimationState::Standing;
    actor.runtime.recoverySeconds = 3.0f;
    actor.runtime.meleeAttackAnimationSeconds = 0.8f;
    actor.runtime.rangedAttackAnimationSeconds = 0.8f;
    actor.status.hostileToParty = true;
    actor.movement.position = {0.0f, 0.0f, 0.0f};
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 300.0f;
    actor.movement.mm9Placement = Mm9AiPlacement{};
    actor.world.active = true;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {1000.0f, 0.0f, 0.0f};
    actor.target.currentDistance = 1000.0f;
    actor.target.currentEdgeDistance = 960.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = true;
    actor.target.partyCanSenseActor = true;
    Mm9AiProfile profile = {};
    profile.archetype = archetype;
    profile.attackReach = 110.0f;
    profile.meleeSweep = 133.0f;
    actor.tactics.mm9Profile = profile;
    return actor;
}

ActorAiFrameFacts makeMm9Frame(const ActorAiFacts &actor)
{
    ActorAiFrameFacts frame = {};
    frame.deltaSeconds = 1.0f / 128.0f;
    frame.fixedStepSeconds = 1.0f / 128.0f;
    frame.party.position = {1000.0f, 0.0f, 0.0f};
    frame.party.collisionRadius = 37.0f;
    frame.activeActors.push_back(actor);
    return frame;
}

ActorAiUpdate stepMm9(const ActorAiFacts &actor)
{
    const GameplayActorAiSystem system = {};
    const ActorAiFrameResult result = system.updateActors(makeMm9Frame(actor));
    REQUIRE(result.actorUpdates.size() == 1);
    return result.actorUpdates.front();
}

// The decision of a kind taken this step (earlier or main), if any.
std::optional<ActorAiDecision> findDecision(const ActorAiUpdate &update, ActorAiDecisionKind kind)
{
    for (const std::optional<ActorAiDecision> &decision :
        {update.state.earlierDecision, update.state.layerDecision, update.state.decision})
    {
        if (decision && decision->kind == kind)
        {
            return decision;
        }
    }

    return std::nullopt;
}
}

TEST_CASE("MM9 retarget chance follows NewTargetCheck")
{
    // 70 %, 45 % in range; a nearer attacker x1.15 (MM9 doubles the target distance first), a farther one halved.
    CHECK(OpenYAMM::Game::mm9RetargetChance(false, 500.0f, 200.0f) == doctest::Approx(0.805f));
    CHECK(OpenYAMM::Game::mm9RetargetChance(false, 500.0f, 900.0f) == doctest::Approx(0.35f));
    CHECK(OpenYAMM::Game::mm9RetargetChance(true, 100.0f, 50.0f) == doctest::Approx(0.5175f));
    CHECK(OpenYAMM::Game::mm9RetargetChance(true, 100.0f, 300.0f) == doctest::Approx(0.225f));
    // The quirk: an attacker as far as the target (not farther) still gets the 1.15.
    CHECK(OpenYAMM::Game::mm9RetargetChance(false, 500.0f, 500.0f) == doctest::Approx(0.805f));
}

TEST_CASE("MM9 ShouldRunAfter times the arrival to the recovery")
{
    // Ready: always runs. Otherwise only when the recovery ends before it arrives.
    CHECK(OpenYAMM::Game::mm9ShouldRunAfter(true, 5.0f, 10.0f, 600.0f));
    CHECK(OpenYAMM::Game::mm9ShouldRunAfter(false, 1.0f, 1200.0f, 600.0f));
    CHECK_FALSE(OpenYAMM::Game::mm9ShouldRunAfter(false, 2.5f, 1200.0f, 600.0f));
    CHECK_FALSE(OpenYAMM::Game::mm9ShouldRunAfter(false, 0.5f, 100.0f, 0.0f));
}

TEST_CASE("MM9 shot checks run on Range.inc's timers and clear-shot chances")
{
    CHECK(OpenYAMM::Game::mm9ShotCheckSeconds(false, 0.0f) == doctest::Approx(1.0f));
    CHECK(OpenYAMM::Game::mm9ShotCheckSeconds(false, 1.0f) == doctest::Approx(2.5f));
    CHECK(OpenYAMM::Game::mm9ShotCheckSeconds(true, 0.0f) == doctest::Approx(0.2f));
    CHECK(OpenYAMM::Game::mm9ShotCheckSeconds(true, 1.0f) == doctest::Approx(0.4f));
    CHECK(OpenYAMM::Game::mm9ShotChance(Mm9ShotLine::Target) == doctest::Approx(1.0f));
    CHECK(OpenYAMM::Game::mm9ShotChance(Mm9ShotLine::Clear) == doctest::Approx(0.2f));
    CHECK(OpenYAMM::Game::mm9ShotChance(Mm9ShotLine::Object) == doctest::Approx(0.15f));
    CHECK(OpenYAMM::Game::mm9ShotChance(Mm9ShotLine::Blocked) == doctest::Approx(0.0f));
    // SightDistance - 5 LT, within the projectile's reach.
    CHECK(OpenYAMM::Game::mm9RangeAttackRange(3379.0f, 5120.0f) == doctest::Approx(3366.2f));
    CHECK(OpenYAMM::Game::mm9RangeAttackRange(9000.0f, 5120.0f) == doctest::Approx(5120.0f));
}

TEST_CASE("MM9 RangeAttack casts by the sequential spell chances, then shoots")
{
    using OpenYAMM::Game::mm9RangedSpellSlot;

    // The Oculus (generated 13 and 43 from Att% 50 and SpellUse%1 25): Paralyze below 0.13, Curse by the rest of the
    // roll rescaled (0.13 + 0.87 x 0.43 = 0.504), its BlueLine above.
    CHECK(mm9RangedSpellSlot(13, 43, 0.0f) == 1);
    CHECK(mm9RangedSpellSlot(13, 43, 0.12f) == 1);
    CHECK(mm9RangedSpellSlot(13, 43, 0.14f) == 2);
    CHECK(mm9RangedSpellSlot(13, 43, 0.50f) == 2);
    CHECK(mm9RangedSpellSlot(13, 43, 0.51f) == 0);
    std::array<int, 3> counts = {};
    constexpr int Rolls = 10000;
    for (int roll = 0; roll < Rolls; ++roll)
    {
        ++counts[size_t(mm9RangedSpellSlot(13, 43, (float(roll) + 0.5f) / float(Rolls)))];
    }
    CHECK(counts[1] == doctest::Approx(1300).epsilon(0.01));
    CHECK(counts[2] == doctest::Approx(3741).epsilon(0.01));
    CHECK(counts[0] == doctest::Approx(4959).epsilon(0.01));

    // A spell 1 it cannot cast (chance 0): spell 2 by its own chance. A sure spell 1 never leaves spell 2 a turn.
    CHECK(mm9RangedSpellSlot(0, 40, 0.39f) == 2);
    CHECK(mm9RangedSpellSlot(0, 40, 0.41f) == 0);
    CHECK(mm9RangedSpellSlot(100, 100, 0.99f) == 1);
    // No spell: always the shot; the "can it shoot at all" query's roll of 1 casts nothing.
    CHECK(mm9RangedSpellSlot(0, 0, 0.0f) == 0);
    CHECK(mm9RangedSpellSlot(50, 100, 1.0f) == 0);
}

TEST_CASE("MM9 ShouldRunAway lets only hurt or stranded runners with a hiding place flee")
{
    Mm9RunAwayInput input = {};
    input.runner = true;
    input.hasHidingPlace = true;
    input.currentHp = 80;
    input.largestHit = 40;
    CHECK(OpenYAMM::Game::mm9ShouldRunAway(input));

    input.currentHp = 81;
    CHECK_FALSE(OpenYAMM::Game::mm9ShouldRunAway(input));

    // Unreachable: only without a ranged attack, and not from a flier.
    input.targetReachable = false;
    CHECK(OpenYAMM::Game::mm9ShouldRunAway(input));
    input.hasRangedAttack = true;
    CHECK_FALSE(OpenYAMM::Game::mm9ShouldRunAway(input));
    input.hasRangedAttack = false;
    input.targetFlies = true;
    CHECK_FALSE(OpenYAMM::Game::mm9ShouldRunAway(input));

    input.currentHp = 10;
    input.hasHidingPlace = false;
    CHECK_FALSE(OpenYAMM::Game::mm9ShouldRunAway(input));
    input.hasHidingPlace = true;
    input.runner = false;
    CHECK_FALSE(OpenYAMM::Game::mm9ShouldRunAway(input));
    input.runner = true;
    input.sinceLastFleeSeconds = 29.0f;
    CHECK_FALSE(OpenYAMM::Game::mm9ShouldRunAway(input));

    // Fear always, even right after a flight.
    input.feared = true;
    CHECK(OpenYAMM::Game::mm9ShouldRunAway(input));
}

TEST_CASE("MM9 runners are rolled once per actor from the placement's chance")
{
    int runners = 0;

    for (uint32_t actorId = 0; actorId < 1000; ++actorId)
    {
        CHECK(OpenYAMM::Game::mm9IsRunner(actorId, 0.25f) == OpenYAMM::Game::mm9IsRunner(actorId, 0.25f));
        runners += OpenYAMM::Game::mm9IsRunner(actorId, 0.25f) ? 1 : 0;
        CHECK_FALSE(OpenYAMM::Game::mm9IsRunner(actorId, 0.0f));
        CHECK(OpenYAMM::Game::mm9IsRunner(actorId, 1.0f));
    }

    CHECK(runners > 200);
    CHECK(runners < 300);
}

TEST_CASE("MM9 wince: never for Always Wince 1, else 20-50 % at 20 % health")
{
    CHECK(OpenYAMM::Game::mm9WinceChance(Mm9AiWince::Never, 1, 100, 0.5f) == 0.0f);
    CHECK(OpenYAMM::Game::mm9WinceChance(Mm9AiWince::LowHealth, 21, 100, 0.5f) == 0.0f);
    CHECK(OpenYAMM::Game::mm9WinceChance(Mm9AiWince::LowHealth, 20, 100, 0.0f) == doctest::Approx(0.20f));
    CHECK(OpenYAMM::Game::mm9WinceChance(Mm9AiWince::LowHealth, 5, 100, 0.999f) == doctest::Approx(0.50f));
}

TEST_CASE("MM9 perception: hearing all round, sight in front, never through walls, doubled after contact")
{
    Mm9PerceptionInput input = {};
    input.sight = 1000.0f;
    input.hearing = 300.0f;
    input.lineOfSight = true;
    input.distance = 250.0f;
    CHECK(OpenYAMM::Game::mm9Perceives(input));
    input.distance = 800.0f;
    CHECK_FALSE(OpenYAMM::Game::mm9Perceives(input));
    input.inFront = true;
    CHECK(OpenYAMM::Game::mm9Perceives(input));
    input.distance = 1500.0f;
    CHECK_FALSE(OpenYAMM::Game::mm9Perceives(input));
    input.doubled = true;
    CHECK(OpenYAMM::Game::mm9Perceives(input));
    input.lineOfSight = false;
    CHECK_FALSE(OpenYAMM::Game::mm9Perceives(input));
}

TEST_CASE("MM9 senses reach beyond the shared ranges, up to the engine's")
{
    // The farther sense, doubled after contact.
    CHECK(OpenYAMM::Game::mm9PerceptionRange(1536.0f, 369.0f, false) == doctest::Approx(1536.0f));
    CHECK(OpenYAMM::Game::mm9PerceptionRange(6144.0f, 922.0f, true) == doctest::Approx(12288.0f));
    CHECK(OpenYAMM::Game::mm9PerceptionRange(300.0f, 900.0f, false) == doctest::Approx(900.0f));
    // The world's 4 096 (MM9 outdoors) or the shared 5 120 (indoors) is raised, never lowered, and capped at 10 240.
    CHECK(OpenYAMM::Game::mm9SenseRange(4096.0f, 1536.0f, 10240.0f) == doctest::Approx(4096.0f));
    CHECK(OpenYAMM::Game::mm9SenseRange(4096.0f, 6144.0f, 10240.0f) == doctest::Approx(6144.0f));
    CHECK(OpenYAMM::Game::mm9SenseRange(5120.0f, 12288.0f, 10240.0f) == doctest::Approx(10240.0f));
    CHECK(OpenYAMM::Game::mm9SenseRange(12000.0f, 6144.0f, 10240.0f) == doctest::Approx(12000.0f));
}

TEST_CASE("MM9 sight lines start at the eye")
{
    // GetEyePos: the top of the body less 2 LT (5.12 units).
    CHECK(OpenYAMM::Game::mm9EyeZ(100.0f, 160.0f, 5.12f) == doctest::Approx(254.88f));
    // Never below the body's centre.
    CHECK(OpenYAMM::Game::mm9EyeZ(0.0f, 6.0f, 5.12f) == doctest::Approx(3.0f));
}

TEST_CASE("MM9 attack reach and sweep are per monster")
{
    // Edge to edge in MM9: the party's radius is added back to OpenYAMM's edge distance.
    CHECK(OpenYAMM::Game::mm9MeleeReach(110.0f, false, 37.0f) == doctest::Approx(147.0f));
    CHECK(OpenYAMM::Game::mm9MeleeReach(110.0f, true, 37.0f) == doctest::Approx(110.0f));
    CHECK(OpenYAMM::Game::mm9MeleeSweepReaches(133.0f, 110.0f, 40.0f, 37.0f, 210.0f));
    CHECK_FALSE(OpenYAMM::Game::mm9MeleeSweepReaches(133.0f, 110.0f, 40.0f, 37.0f, 211.0f));
    // A sweep shorter than the attack range reaches the attack range (no lunge impulse).
    CHECK(OpenYAMM::Game::mm9MeleeSweepReaches(54.0f, 102.0f, 30.0f, 37.0f, 169.0f));
}

TEST_CASE("MM9 walker notices the party and holds it")
{
    const ActorAiUpdate update = stepMm9(makeMm9Walker());
    REQUIRE(update.state.mm9);
    CHECK(update.state.mm9->targetKind == ActorAiTargetKind::Party);
    CHECK(update.state.mm9->partyContact);
    const bool noticed = findDecision(update, ActorAiDecisionKind::Detect).has_value()
        || findDecision(update, ActorAiDecisionKind::TauntDetect).has_value();
    CHECK(noticed);
}

TEST_CASE("MM9 walker waits to arrive as its attack recovers")
{
    ActorAiFacts actor = makeMm9Walker();
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.partyContact = true;
    actor.runtime.attackCooldownSeconds = 5.0f;
    // 960 units at 600 a second: 1.6 s away, its recovery 5 s.
    const ActorAiUpdate waiting = stepMm9(actor);
    CHECK(findDecision(waiting, ActorAiDecisionKind::Throttle).has_value());
    CHECK(waiting.state.motionState == ActorAiMotionState::Standing);

    // The script reads RecoveryTimeLeft 3.03 times too long: 1 s left (3.03 s seen) still waits for a 1.6 s run.
    actor.runtime.attackCooldownSeconds = 1.0f;
    CHECK(findDecision(stepMm9(actor), ActorAiDecisionKind::Throttle).has_value());

    actor.runtime.attackCooldownSeconds = 0.5f;
    const ActorAiUpdate running = stepMm9(actor);
    CHECK(findDecision(running, ActorAiDecisionKind::Pursue).has_value());
    CHECK(running.state.motionState == ActorAiMotionState::Pursuing);
}

TEST_CASE("MM9 walker gives up after 30 s without an attack and loses an unseen target after 8 s")
{
    ActorAiFacts actor = makeMm9Walker();
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.chaseSeconds = 30.0f;
    const ActorAiUpdate gaveUp = stepMm9(actor);
    REQUIRE(findDecision(gaveUp, ActorAiDecisionKind::GiveUp));
    CHECK(std::string(findDecision(gaveUp, ActorAiDecisionKind::GiveUp)->pNote) == "chase_time");
    CHECK(gaveUp.state.mm9->targetKind == ActorAiTargetKind::None);
    CHECK(gaveUp.state.mm9->searchDelaySeconds > 0.0f);

    actor.runtime.mm9.chaseSeconds = 1.0f;
    actor.runtime.mm9.unseenSeconds = 7.999f;
    actor.target.currentHasAttackLineOfSight = false;
    const ActorAiUpdate lost = stepMm9(actor);
    REQUIRE(findDecision(lost, ActorAiDecisionKind::GiveUp));
    CHECK(std::string(findDecision(lost, ActorAiDecisionKind::GiveUp)->pNote) == "lost");
}

TEST_CASE("MM9 walker considers an attacker that is not its target")
{
    ActorAiFacts actor = makeMm9Walker();
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.mm9World.damageSerial = 1;
    actor.mm9World.attackerKind = ActorAiTargetKind::Actor;
    actor.mm9World.attackerActorIndex = 3;
    actor.mm9World.attackerDistance = 100.0f;
    const ActorAiUpdate update = stepMm9(actor);
    const std::optional<ActorAiDecision> retarget = findDecision(update, ActorAiDecisionKind::Retarget);
    REQUIRE(retarget);
    CHECK(retarget->chance == doctest::Approx(0.805f));
    CHECK(update.state.mm9->seenDamageSerial == 1);

    if (retarget->roll < retarget->chance)
    {
        CHECK(update.state.mm9->targetKind == ActorAiTargetKind::Actor);
        CHECK(update.state.mm9->targetActorIndex == 3);
    }
    else
    {
        CHECK(update.state.mm9->targetKind == ActorAiTargetKind::Party);
    }

    // A hit by its own target only counts as one.
    actor.mm9World.attackerKind = ActorAiTargetKind::Party;
    CHECK_FALSE(findDecision(stepMm9(actor), ActorAiDecisionKind::Retarget));
}

TEST_CASE("MM9 ranged walker shoots only at its shot checks, outside melee range")
{
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Skirmisher);
    actor.tactics.mm9Profile->ranged = Mm9AiRanged::Walker;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.stats.attackConstraints.rangedCommitAllowed = true;
    actor.stats.attack2Damage.diceRolls = 2;
    actor.stats.attack2Damage.diceSides = 4;
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.partyContact = true;

    // Its check is not due: it chases.
    actor.runtime.mm9.shotCheckSeconds = 0.5f;
    CHECK_FALSE(findDecision(stepMm9(actor), ActorAiDecisionKind::ShotCheck));

    // Due, clear line: it shoots, and the next check is 1-2.5 s away.
    actor.runtime.mm9.shotCheckSeconds = 0.0f;
    const ActorAiUpdate shot = stepMm9(actor);
    REQUIRE(findDecision(shot, ActorAiDecisionKind::ShotCheck));
    CHECK(findDecision(shot, ActorAiDecisionKind::AttackRanged).has_value());
    CHECK(shot.state.mm9->shotCheckSeconds >= 1.0f);
    CHECK(shot.state.mm9->shotCheckSeconds <= 2.5f);

    // In melee range it strikes (Att% 100 keeps the blow) and never checks a shot.
    actor.target.currentEdgeDistance = 60.0f;
    actor.stats.attack2Chance = 100;
    const ActorAiUpdate blow = stepMm9(actor);
    CHECK_FALSE(findDecision(blow, ActorAiDecisionKind::ShotCheck));
    CHECK(findDecision(blow, ActorAiDecisionKind::AttackMelee).has_value());
}

TEST_CASE("MM9 ranged walker with a projectile casts both its spells at its shot checks")
{
    // An Oculus: attack 1 a BlueLine, Paralyze at 13 and Curse (Dark Grasp) at 43 (generated from Att% 50 and
    // SpellUse%1 25: 12.5 % and 37.5 % of its shots).
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Skirmisher);
    actor.identity.monsterId = 9230;
    actor.tactics.mm9Profile->ranged = Mm9AiRanged::Walker;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.stats.attackConstraints.rangedCommitAllowed = true;
    actor.stats.attack2Damage.diceRolls = 10;
    actor.stats.attack2Damage.diceSides = 20;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Name = "dark grasp";
    actor.stats.spell1UseChance = 13;
    actor.stats.hasSpell2 = true;
    actor.stats.spell2Name = "dark grasp";
    actor.stats.spell2UseChance = 43;
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.partyContact = true;
    actor.runtime.mm9.shotCheckSeconds = 0.0f;

    std::array<int, 3> counts = {};
    constexpr uint32_t Shots = 400;
    for (uint32_t actorId = 1; actorId <= Shots; ++actorId)
    {
        actor.actorId = actorId;
        actor.identity.actorId = actorId;
        const ActorAiUpdate update = stepMm9(actor);
        REQUIRE(update.state.queuedAttackAbility.has_value());
        const OpenYAMM::Game::GameplayActorAttackAbility ability = *update.state.queuedAttackAbility;
        ++counts[ability == OpenYAMM::Game::GameplayActorAttackAbility::Spell1 ? 1
            : ability == OpenYAMM::Game::GameplayActorAttackAbility::Spell2 ? 2 : 0];
    }

    CHECK(counts[1] > 30);
    CHECK(counts[1] < 75);
    CHECK(counts[2] > 120);
    CHECK(counts[2] < 180);
    CHECK(counts[0] > 170);
    CHECK(counts[0] < 230);
}

TEST_CASE("MM9 monster in reach always strikes its blow; only a ranged weapon prop shoots or casts there")
{
    // An Oculus-like walker with a projectile, attack 2 and two spells, Att% 0: CanAttack's roll would pick the spell,
    // but Attack ignores the kind (MM9_AI_NATIVE_RE.md section 7.2.3).
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Skirmisher);
    actor.tactics.mm9Profile->ranged = Mm9AiRanged::Walker;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.stats.attackConstraints.rangedCommitAllowed = true;
    actor.stats.attack2Damage.diceRolls = 2;
    actor.stats.attack2Damage.diceSides = 6;
    actor.stats.attack2Chance = 0;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Name = "dark grasp";
    actor.stats.spell1UseChance = 50;
    actor.stats.hasSpell2 = true;
    actor.stats.spell2Name = "dark grasp";
    actor.stats.spell2UseChance = 100;
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.partyContact = true;
    actor.runtime.mm9.shotCheckSeconds = 0.0f;
    actor.target.currentEdgeDistance = 60.0f;

    std::array<int, 3> counts = {};
    for (uint32_t actorId = 1; actorId <= 100; ++actorId)
    {
        actor.actorId = actorId;
        actor.identity.actorId = actorId;
        const ActorAiUpdate update = stepMm9(actor);
        REQUIRE(update.state.queuedAttackAbility.has_value());
        const OpenYAMM::Game::GameplayActorAttackAbility ability = *update.state.queuedAttackAbility;
        CHECK_FALSE(findDecision(update, ActorAiDecisionKind::ShotCheck));
        ++counts[ability == OpenYAMM::Game::GameplayActorAttackAbility::Attack2 ? 0
            : ability == OpenYAMM::Game::GameplayActorAttackAbility::Attack1 ? 1 : 2];
    }

    CHECK(counts[0] == 100);

    // Holding a ranged weapon prop, its Attack is RangeAttack: a spell (here always, Att% 0) instead of the blow.
    actor.tactics.mm9Profile->rangedWeapon = true;
    counts = {};
    for (uint32_t actorId = 1; actorId <= 100; ++actorId)
    {
        actor.actorId = actorId;
        actor.identity.actorId = actorId;
        const ActorAiUpdate update = stepMm9(actor);
        REQUIRE(update.state.queuedAttackAbility.has_value());
        const OpenYAMM::Game::GameplayActorAttackAbility ability = *update.state.queuedAttackAbility;
        ++counts[ability == OpenYAMM::Game::GameplayActorAttackAbility::Attack2 ? 0
            : ability == OpenYAMM::Game::GameplayActorAttackAbility::Attack1 ? 1 : 2];
    }

    CHECK(counts[0] == 0);
    CHECK(counts[2] == 100);
}

TEST_CASE("MM9 walker with attack 1 alone never shoots")
{
    // CanRangeAttack needs attack 2's damage or a spell: a projectile on attack 1 alone fires no shot.
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Skirmisher);
    actor.tactics.mm9Profile->ranged = Mm9AiRanged::Walker;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.stats.attackConstraints.rangedCommitAllowed = true;
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.partyContact = true;
    actor.runtime.mm9.shotCheckSeconds = 0.0f;
    CHECK_FALSE(findDecision(stepMm9(actor), ActorAiDecisionKind::AttackRanged));

    actor.stats.attack2Damage.diceRolls = 2;
    actor.stats.attack2Damage.diceSides = 4;
    CHECK(findDecision(stepMm9(actor), ActorAiDecisionKind::AttackRanged).has_value());
}

TEST_CASE("MM9 placement script with no AI keeps its monster passive")
{
    // Sturmford's prison guard (Sturmguard.scr): a hit, a call or a target in sight starts nothing.
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Guard);
    actor.tactics.mm9Profile->passive = true;
    actor.runtime.mm9.targetKind = ActorAiTargetKind::None;
    actor.mm9World.damageSerial = 1;
    actor.mm9World.attackerKind = ActorAiTargetKind::Party;
    actor.target.currentEdgeDistance = 60.0f;
    const ActorAiUpdate update = stepMm9(actor);
    CHECK(update.state.mm9->targetKind == ActorAiTargetKind::None);
    CHECK_FALSE(update.state.queuedAttackAbility.has_value());
    CHECK_FALSE(findDecision(update, ActorAiDecisionKind::Detect));
    CHECK_FALSE(findDecision(update, ActorAiDecisionKind::TauntDetect));

    // Without it the same guard takes the party as its target when it notices it.
    actor.tactics.mm9Profile->passive = false;
    actor.mm9World.damageSerial = 0;
    CHECK(stepMm9(actor).state.mm9->targetKind == ActorAiTargetKind::Party);
}

TEST_CASE("MM9 ranged holder keeps its place")
{
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::RangedHolder);
    actor.tactics.mm9Profile->ranged = Mm9AiRanged::Walker;
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.shotCheckSeconds = 0.3f;
    const ActorAiUpdate update = stepMm9(actor);
    CHECK(findDecision(update, ActorAiDecisionKind::Hold).has_value());
    CHECK(update.state.motionState == ActorAiMotionState::Standing);
}

TEST_CASE("MM9 walker flees by ShouldRunAway only, to its hiding place")
{
    const std::vector<std::array<int32_t, 3>> hidingPlaces = {{-2000, 0, 0}};
    ActorAiFacts actor = makeMm9Walker();
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.stats.currentHp = 30;
    actor.mm9World.largestHit = 20;
    actor.movement.mm9HidingPlaces = hidingPlaces;
    actor.mm9World.hidingPlacesUnseen = 1;
    // Not a runner: it fights on whatever its AI type says.
    actor.movement.mm9Placement->runawayChance = 0.0f;
    CHECK_FALSE(findDecision(stepMm9(actor), ActorAiDecisionKind::FleeDecision));

    // A runner whose hiding place its target sees does not flee (FindHidingPlace takes only unseen ones).
    actor.movement.mm9Placement->runawayChance = 1.0f;
    actor.mm9World.hidingPlacesUnseen = 0;
    CHECK_FALSE(findDecision(stepMm9(actor), ActorAiDecisionKind::FleeDecision));

    actor.mm9World.hidingPlacesUnseen = 1;
    const ActorAiUpdate update = stepMm9(actor);
    REQUIRE(findDecision(update, ActorAiDecisionKind::FleeDecision));
    REQUIRE(findDecision(update, ActorAiDecisionKind::Hide));
    CHECK(update.state.mm9->fleeMode == OpenYAMM::Game::Mm9FleeMode::Hide);

    // The flight runs to the hiding place (away from the party here) and ends there.
    actor.runtime.mm9 = *update.state.mm9;
    const ActorAiUpdate running = stepMm9(actor);
    CHECK(running.state.motionState == ActorAiMotionState::Fleeing);
    CHECK(running.movementIntent.moveDirectionX < -0.99f);

    actor.movement.position = {-1990.0f, 0.0f, 0.0f};
    const ActorAiUpdate arrived = stepMm9(actor);
    CHECK(findDecision(arrived, ActorAiDecisionKind::Hide)->pNote == std::string("arrived"));
    REQUIRE(arrived.mm9Request);
    CHECK(arrived.mm9Request->help);
    CHECK(arrived.state.mm9->targetKind == ActorAiTargetKind::None);
}

TEST_CASE("MM9 loop archetypes: walkers, swimmers, fliers, turrets with the Dragon King, and townsfolk")
{
    Mm9AiProfile profile = {};

    for (Mm9AiArchetype archetype : {Mm9AiArchetype::Crawler, Mm9AiArchetype::Skirmisher,
             Mm9AiArchetype::RangedHolder, Mm9AiArchetype::Swimmer, Mm9AiArchetype::Flier, Mm9AiArchetype::Turret})
    {
        profile.archetype = archetype;
        CHECK(OpenYAMM::Game::mm9LoopArchetype(profile));
    }

    CHECK(OpenYAMM::Game::mm9WalkerArchetype(Mm9AiArchetype::Swimmer));
    CHECK_FALSE(OpenYAMM::Game::mm9WalkerArchetype(Mm9AiArchetype::Flier));
    // Phase 5: the Dragon King (a turret boss) runs the turret loop, his attacks chosen by his behaviour script.
    profile.archetype = Mm9AiArchetype::Turret;
    profile.boss = true;
    CHECK(OpenYAMM::Game::mm9LoopArchetype(profile));
    // Phase 4b: townsfolk and guards run MM9 loops too.
    profile.archetype = Mm9AiArchetype::Civilian;
    profile.boss = false;
    CHECK(OpenYAMM::Game::mm9LoopArchetype(profile));
    profile.archetype = Mm9AiArchetype::Guard;
    CHECK(OpenYAMM::Game::mm9LoopArchetype(profile));
}

TEST_CASE("MM9 flier rules follow BaseFly.inc, FlyRange.inc and Banshee.scr")
{
    // GetRandomInt 0, 100 is inclusive: "< 50" passes 50 times in 101, FlyRange shoots unless "< 40".
    CHECK(OpenYAMM::Game::mm9FlierRetargetChance() == doctest::Approx(50.0f / 101.0f));
    CHECK(OpenYAMM::Game::mm9FlyShotChance() == doctest::Approx(61.0f / 101.0f));
    CHECK(OpenYAMM::Game::mm9FlyShotCheckSeconds(0.0f) == doctest::Approx(0.3f));
    CHECK(OpenYAMM::Game::mm9FlyShotCheckSeconds(1.0f) == doctest::Approx(1.3f));

    // A back-off normalises (away, 0.6): rising a little over half its speed; level from a flying target.
    float horizontal = 0.0f;
    float vertical = 0.0f;
    OpenYAMM::Game::mm9FlyBackOffShares(0.6f, false, horizontal, vertical);
    CHECK(horizontal == doctest::Approx(0.857493f));
    CHECK(vertical == doctest::Approx(0.514496f));
    OpenYAMM::Game::mm9FlyBackOffShares(0.6f, true, horizontal, vertical);
    CHECK(horizontal == doctest::Approx(1.0f));
    CHECK(vertical == doctest::Approx(0.0f));

    // A swoop turns 30-50 whole degrees to either side.
    constexpr float Degree = 3.14159265f / 180.0f;
    CHECK(OpenYAMM::Game::mm9SwoopAngleRadians(0.0f, 0.9f) == doctest::Approx(30.0f * Degree));
    CHECK(OpenYAMM::Game::mm9SwoopAngleRadians(0.999f, 0.1f) == doctest::Approx(-50.0f * Degree));
    CHECK(OpenYAMM::Game::mm9SwoopAngleRadians(0.5f, 0.9f) == doctest::Approx(40.0f * Degree));

    // A pass past a still target runs at 0.8 of its speed, at most 200 LT a second.
    CHECK(OpenYAMM::Game::mm9FlyPassSpeedShare(true, 640.0f) == doctest::Approx(1.0f));
    CHECK(OpenYAMM::Game::mm9FlyPassSpeedShare(false, 512.0f) == doctest::Approx(0.8f));
    CHECK(OpenYAMM::Game::mm9FlyPassSpeedShare(false, 896.0f) == doctest::Approx(512.0f / 896.0f));

    // Banshee.scr: the melee window marks it; a 0.6 s back-off rising 0.2, no swoop.
    Mm9AiProfile profile = {};
    profile.archetype = Mm9AiArchetype::Flier;
    CHECK(OpenYAMM::Game::mm9FlierStyle(profile).swoops);
    CHECK(OpenYAMM::Game::mm9FlierStyle(profile).backOffSeconds == doctest::Approx(1.0f));
    profile.meleeWindowSeconds = 5.0f;
    CHECK_FALSE(OpenYAMM::Game::mm9FlierStyle(profile).swoops);
    CHECK(OpenYAMM::Game::mm9FlierStyle(profile).backOffSeconds == doctest::Approx(0.6f));
    CHECK(OpenYAMM::Game::mm9FlierStyle(profile).backOffRise == doctest::Approx(0.2f));
}

TEST_CASE("MM9 turret rules follow lobber.scr and the native CanLob")
{
    CHECK(OpenYAMM::Game::mm9TurretScanSeconds(0.0f) == doctest::Approx(5.0f));
    CHECK(OpenYAMM::Game::mm9TurretScanSeconds(1.0f) == doctest::Approx(15.0f));
    constexpr float Degree = 3.14159265f / 180.0f;
    CHECK(OpenYAMM::Game::mm9TurretScanTurnRadians(0.0f, 0.9f) == doctest::Approx(20.0f * Degree));
    CHECK(OpenYAMM::Game::mm9TurretScanTurnRadians(1.0f, 0.1f) == doctest::Approx(-120.0f * Degree));
    // CanLob: its attack ready and fewer than five pods; the script's own 5-10 s wait never runs.
    CHECK(OpenYAMM::Game::mm9TurretCanLob(true, 4));
    CHECK_FALSE(OpenYAMM::Game::mm9TurretCanLob(true, 5));
    CHECK_FALSE(OpenYAMM::Game::mm9TurretCanLob(false, 0));
    // Without a clear shot it shoots only when GetRandomInt 0, 100 is not below 75.
    CHECK(OpenYAMM::Game::mm9TurretShotChance(true) == doctest::Approx(1.0f));
    CHECK(OpenYAMM::Game::mm9TurretShotChance(false) == doctest::Approx(26.0f / 101.0f));
}

TEST_CASE("MM9 swimmer land rule follows BaseSwim.inc and AISwimFly")
{
    CHECK(OpenYAMM::Game::mm9SwimmerRunsFrom(false));
    CHECK_FALSE(OpenYAMM::Game::mm9SwimmerRunsFrom(true));
    CHECK(OpenYAMM::Game::mm9SwimmerCanTarget(true, true));
    CHECK_FALSE(OpenYAMM::Game::mm9SwimmerCanTarget(true, false));
    // A swimmer out of water targets anything (and then runs from a dry target: MM9 quirk).
    CHECK(OpenYAMM::Game::mm9SwimmerCanTarget(false, false));
}

namespace
{
// An MM9 flier (a Bird's numbers) holding the party 1 000 units ahead.
ActorAiFacts makeMm9Flier()
{
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Flier);
    actor.identity.monsterId = 9093;
    actor.stats.canFly = true;
    actor.movement.effectiveMoveSpeed = 256.0f;
    actor.tactics.mm9Profile->movement = OpenYAMM::Game::Mm9AiMovement::Fly;
    actor.tactics.mm9Profile->attackReach = 103.0f;
    actor.tactics.mm9Profile->meleeSweep = 154.0f;
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    return actor;
}
}

TEST_CASE("MM9 flier notices the party with a taunt and does not double its senses")
{
    ActorAiFacts actor = makeMm9Flier();
    actor.runtime.mm9.targetKind = ActorAiTargetKind::None;
    const ActorAiUpdate update = stepMm9(actor);
    REQUIRE(findDecision(update, ActorAiDecisionKind::TauntDetect));
    CHECK(std::string(findDecision(update, ActorAiDecisionKind::TauntDetect)->pNote) == "always");
    CHECK(update.state.mm9->targetKind == ActorAiTargetKind::Party);
    CHECK_FALSE(update.state.mm9->partyContact);
}

TEST_CASE("MM9 flier chases, passes when ready in range, backs off upward when not")
{
    ActorAiFacts actor = makeMm9Flier();
    const ActorAiUpdate chase = stepMm9(actor);
    CHECK(findDecision(chase, ActorAiDecisionKind::Pursue).has_value());

    actor.target.currentEdgeDistance = 80.0f;
    actor.movement.inMeleeRange = true;
    const ActorAiUpdate pass = stepMm9(actor);
    REQUIRE(findDecision(pass, ActorAiDecisionKind::FlyPass));
    CHECK(findDecision(pass, ActorAiDecisionKind::AttackMelee).has_value());
    CHECK(pass.state.mm9->flightPhase == OpenYAMM::Game::Mm9FlightPhase::Pass);
    // The pass flies level, 45 degrees off the line to the party.
    CHECK(pass.movementIntent.desiredMoveZ == doctest::Approx(0.0f));
    CHECK(std::abs(pass.movementIntent.moveDirectionY) == doctest::Approx(std::sqrt(0.5f)).epsilon(0.01));

    actor.runtime.attackCooldownSeconds = 2.0f;
    actor.runtime.mm9.chaseSeconds = 20.0f;
    const ActorAiUpdate backOff = stepMm9(actor);
    REQUIRE(findDecision(backOff, ActorAiDecisionKind::BackOff));
    CHECK(backOff.state.mm9->flightPhase == OpenYAMM::Game::Mm9FlightPhase::BackOff);
    CHECK(backOff.state.mm9->flightSeconds == doctest::Approx(1.0f));
    // Away from the party and up; its clock restarts (it never gives up while it waits in range).
    CHECK(backOff.movementIntent.desiredMoveX < 0.0f);
    CHECK(backOff.movementIntent.desiredMoveZ > 0.5f);
    CHECK(backOff.state.mm9->chaseSeconds < 1.0f);
}

TEST_CASE("MM9 flier swoops in after its back-off; a Banshee does not")
{
    ActorAiFacts actor = makeMm9Flier();
    actor.runtime.attackCooldownSeconds = 2.0f;
    actor.runtime.mm9.flightPhase = OpenYAMM::Game::Mm9FlightPhase::BackOff;
    actor.runtime.mm9.flightSeconds = 0.001f;
    const ActorAiUpdate swoop = stepMm9(actor);
    REQUIRE(findDecision(swoop, ActorAiDecisionKind::Swoop));
    CHECK(swoop.state.mm9->flightPhase == OpenYAMM::Game::Mm9FlightPhase::Swoop);
    CHECK(swoop.state.mm9->swooping);
    CHECK(swoop.movementIntent.desiredMoveZ == doctest::Approx(0.0f));

    actor.tactics.mm9Profile->meleeWindowSeconds = 5.0f;
    const ActorAiUpdate banshee = stepMm9(actor);
    CHECK_FALSE(findDecision(banshee, ActorAiDecisionKind::Swoop));
    CHECK(findDecision(banshee, ActorAiDecisionKind::Pursue).has_value());
}

TEST_CASE("MM9 flier never flees, whatever its AI type")
{
    ActorAiFacts actor = makeMm9Flier();
    actor.stats.aiType = OpenYAMM::Game::GameplayActorAiType::Wimp;
    actor.stats.currentHp = 1;
    CHECK(stepMm9(actor).state.motionState != ActorAiMotionState::Fleeing);
}

TEST_CASE("MM9 turret plays Aware, then launches pods while it can lob, then shoots")
{
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Turret);
    actor.identity.monsterId = 9086;
    actor.movement.movementAllowed = false;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.stats.attackConstraints.rangedCommitAllowed = true;
    // Its shot needs attack 2's damage (the Lobber's Dark 2D4+1).
    actor.stats.attack2Damage.diceRolls = 2;
    actor.stats.attack2Damage.diceSides = 4;
    actor.tactics.mm9Profile->podLaunchMonsterId = 9084;

    const ActorAiUpdate detect = stepMm9(actor);
    REQUIRE(findDecision(detect, ActorAiDecisionKind::TauntDetect));
    CHECK(std::string(findDecision(detect, ActorAiDecisionKind::TauntDetect)->pNote) == "aware");
    CHECK(detect.state.mm9->awareSeconds > 1.4f);
    CHECK(detect.state.mm9->shotCheckSeconds > 2.4f);

    actor.runtime.mm9 = *detect.state.mm9;
    actor.runtime.mm9.awareSeconds = 0.0f;
    actor.runtime.mm9.shotCheckSeconds = 0.0f;
    const ActorAiUpdate pod = stepMm9(actor);
    CHECK(findDecision(pod, ActorAiDecisionKind::PodLaunch).has_value());
    CHECK(pod.state.mm9->podLaunchPending);
    CHECK(pod.state.motionState == ActorAiMotionState::Attacking);

    actor.mm9World.livePods = 5;
    const ActorAiUpdate shot = stepMm9(actor);
    CHECK_FALSE(findDecision(shot, ActorAiDecisionKind::PodLaunch));
    CHECK(findDecision(shot, ActorAiDecisionKind::ShotCheck).has_value());
    CHECK(findDecision(shot, ActorAiDecisionKind::AttackRanged).has_value());
}

TEST_CASE("MM9 turret's pod comes at the launch's contact time")
{
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Turret);
    actor.movement.movementAllowed = false;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.tactics.mm9Profile->podLaunchMonsterId = 9084;
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.podLaunchPending = true;
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    // Its contact time is the action's end (no contact frame): this step.
    actor.runtime.actionSeconds = 0.005f;
    const ActorAiUpdate update = stepMm9(actor);
    REQUIRE(update.spawnRequest);
    CHECK(update.spawnRequest->monsterId == 9084);
    CHECK(update.spawnRequest->position.x > 100.0f);
    CHECK_FALSE(update.attackRequest);
    CHECK_FALSE(update.state.mm9->podLaunchPending);
    // The LaunchPod key sets its recovery like a released shot (a wince after it keeps it).
    CHECK(update.state.mm9->hitRecoveryArmed);
}

TEST_CASE("MM9 turret scans by turning while it has no target")
{
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Turret);
    actor.movement.movementAllowed = false;
    actor.target.currentKind = ActorAiTargetKind::None;
    actor.target.currentCanSense = false;
    const ActorAiUpdate armed = stepMm9(actor);
    CHECK(armed.state.mm9->scanArmed);
    CHECK(armed.state.mm9->scanSeconds >= 5.0f);

    actor.runtime.mm9 = *armed.state.mm9;
    actor.runtime.mm9.scanSeconds = 0.001f;
    const ActorAiUpdate turn = stepMm9(actor);
    REQUIRE(findDecision(turn, ActorAiDecisionKind::Scan));
    CHECK(turn.state.mm9->scanTurning);
    CHECK(turn.movementIntent.updateYaw);
    CHECK(std::abs(turn.movementIntent.yawRadians) < 0.03f);
}

TEST_CASE("MM9 swimmer runs at once from a target out of the water")
{
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Swimmer);
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.mm9World.waterKnown = true;
    actor.mm9World.inWater = true;
    actor.mm9World.targetInWater = true;
    CHECK_FALSE(findDecision(stepMm9(actor), ActorAiDecisionKind::FleeDecision));

    actor.mm9World.targetInWater = false;
    const ActorAiUpdate update = stepMm9(actor);
    REQUIRE(findDecision(update, ActorAiDecisionKind::FleeDecision));
    CHECK(std::string(findDecision(update, ActorAiDecisionKind::FleeDecision)->pNote) == "land");

    // Without water facts (outdoors) it is a crawler.
    actor.mm9World.waterKnown = false;
    CHECK_FALSE(findDecision(stepMm9(actor), ActorAiDecisionKind::FleeDecision));
}

TEST_CASE("MM9 FlyRange checks only once armed and never while its swoop flag is set")
{
    ActorAiFacts actor = makeMm9Flier();
    actor.tactics.mm9Profile->ranged = Mm9AiRanged::Flier;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Name = "Ice Bolt";
    actor.stats.spell1Id = 7;
    actor.stats.spell1UseChance = 100;
    actor.stats.attackConstraints.rangedCommitAllowed = true;
    actor.runtime.mm9.shotCheckSeconds = 0.0f;

    // Its target came from a hit (OnDamageDone never starts RangeCheckSetup): no check.
    CHECK_FALSE(findDecision(stepMm9(actor), ActorAiDecisionKind::ShotCheck));

    actor.runtime.mm9.shotChecksArmed = true;
    CHECK(findDecision(stepMm9(actor), ActorAiDecisionKind::ShotCheck).has_value());

    // A swoop cut short leaves its flag set: no check until a later swoop ends.
    actor.runtime.mm9.swooping = true;
    CHECK_FALSE(findDecision(stepMm9(actor), ActorAiDecisionKind::ShotCheck));
}

TEST_CASE("MM9 wander rules follow BaseWander.inc")
{
    // Waits and walks over the placement's bounds (a zero bound reads as 0.01).
    CHECK(OpenYAMM::Game::mm9WanderSeconds(3.0f, 8.0f, 0.0f) == doctest::Approx(3.0f));
    CHECK(OpenYAMM::Game::mm9WanderSeconds(3.0f, 8.0f, 1.0f) == doctest::Approx(8.0f));
    CHECK(OpenYAMM::Game::mm9WanderSeconds(0.0f, 0.0f, 0.5f) == doctest::Approx(0.01f));
    // A turn of 15-180 degrees, 15-90 after an obstacle, to either side.
    constexpr float Degree = 3.14159265f / 180.0f;
    CHECK(OpenYAMM::Game::mm9WanderTurnRadians(false, 1.0f, 0.2f) == doctest::Approx(180.0f * Degree));
    CHECK(OpenYAMM::Game::mm9WanderTurnRadians(true, 1.0f, 0.7f) == doctest::Approx(-90.0f * Degree));
    CHECK(OpenYAMM::Game::mm9WanderTurnRadians(false, 0.0f, 0.2f) == doctest::Approx(15.0f * Degree));
    // The leash (0: none), measured level.
    CHECK_FALSE(OpenYAMM::Game::mm9BeyondLeash(1000.0f, 0.0f, 0.0f));
    CHECK(OpenYAMM::Game::mm9BeyondLeash(600.0f, 800.0f, 1000.0f));
    CHECK_FALSE(OpenYAMM::Game::mm9BeyondLeash(600.0f, 700.0f, 1000.0f));
    // Markers in turn; random: the other of two, else any other one; the first in random order is never marker 0
    // unless there are two.
    CHECK(OpenYAMM::Game::mm9NextPathMarker(2, 3, false, 0.5f) == 0);
    CHECK(OpenYAMM::Game::mm9NextPathMarker(0, 2, true, 0.9f) == 1);
    CHECK(OpenYAMM::Game::mm9NextPathMarker(1, 4, true, 0.0f) == 0);
    CHECK(OpenYAMM::Game::mm9NextPathMarker(1, 4, true, 0.4f) == 2);
    CHECK(OpenYAMM::Game::mm9NextPathMarker(1, 4, true, 0.99f) == 3);
    CHECK(OpenYAMM::Game::mm9FirstPathMarker(4, false, 0.7f) == 0);
    CHECK(OpenYAMM::Game::mm9FirstPathMarker(4, true, 0.0f) == 1);
}

TEST_CASE("MM9 layer rules: calls, flight, resurrection and doors")
{
    using OpenYAMM::Game::Mm9NewTargetInput;
    using OpenYAMM::Game::Mm9NewTargetOutcome;
    Mm9NewTargetInput input = {};
    CHECK(OpenYAMM::Game::mm9NewTargetCheck(input) == Mm9NewTargetOutcome::Take);
    input.hasTarget = true;
    CHECK(OpenYAMM::Game::mm9NewTargetCheck(input) == Mm9NewTargetOutcome::Roll);
    // Its own target, a friend or a dead one, while it flees or resurrects: nothing.
    input.candidateIsTarget = true;
    CHECK(OpenYAMM::Game::mm9NewTargetCheck(input) == Mm9NewTargetOutcome::Invalid);
    input.candidateIsTarget = false;
    input.fleeing = true;
    CHECK(OpenYAMM::Game::mm9NewTargetCheck(input) == Mm9NewTargetOutcome::Invalid);
    input.fleeing = false;
    input.candidateValid = false;
    CHECK(OpenYAMM::Game::mm9NewTargetCheck(input) == Mm9NewTargetOutcome::Invalid);

    // AlertTick waits the last random number drawn; a wait of 0 (or below) sends no more.
    CHECK(OpenYAMM::Game::mm9AlertRepeatSeconds(57.0f) == doctest::Approx(57.0f));
    CHECK(OpenYAMM::Game::mm9AlertRepeatSeconds(-30.0f) == doctest::Approx(0.0f));
    CHECK(OpenYAMM::Game::mm9HelpRadius(200.0f) == doctest::Approx(1000.0f));

    // BaseRunAway: a cower 10 times in 101; a run 15-45 degrees off, always to the same side; ticks 0.3-0.8 s.
    CHECK(OpenYAMM::Game::mm9CowerChance() == doctest::Approx(10.0f / 101.0f));
    constexpr float Degree = 3.14159265f / 180.0f;
    CHECK(OpenYAMM::Game::mm9RunAwayTurnRadians(0.0f) == doctest::Approx(15.0f * Degree));
    CHECK(OpenYAMM::Game::mm9RunAwayTurnRadians(1.0f) == doctest::Approx(45.0f * Degree));
    CHECK(OpenYAMM::Game::mm9RunAwayTickSeconds(1.0f) == doctest::Approx(0.8f));

    // ResurrectMe: 3-6 s; a lone resurrecter raises itself 2-10 s later; nobody within twice its radius.
    CHECK(OpenYAMM::Game::mm9ResurrectDelaySeconds(0.0f) == doctest::Approx(3.0f));
    CHECK(OpenYAMM::Game::mm9ResurrectDelaySeconds(1.0f) == doctest::Approx(6.0f));
    CHECK(OpenYAMM::Game::mm9SelfRaiseDelaySeconds(1.0f) == doctest::Approx(10.0f));
    CHECK_FALSE(OpenYAMM::Game::mm9CanRaiseNow(70.0f, 40.0f));
    CHECK(OpenYAMM::Game::mm9CanRaiseNow(90.0f, 40.0f));

    // BD_OnDoor: heading into the door within 45 degrees (the door's normal points back at it).
    CHECK(OpenYAMM::Game::mm9DoorAhead(1.0f, 0.0f, -1.0f, 0.0f));
    CHECK(OpenYAMM::Game::mm9DoorAhead(1.0f, 0.9f, -1.0f, 0.0f));
    CHECK_FALSE(OpenYAMM::Game::mm9DoorAhead(1.0f, 1.2f, -1.0f, 0.0f));
    CHECK_FALSE(OpenYAMM::Game::mm9DoorAhead(-1.0f, 0.0f, -1.0f, 0.0f));
}

TEST_CASE("MM9 walker walks its marker path and alerts on noticing a target")
{
    const std::vector<std::array<int32_t, 3>> path = {{0, 500, 0}, {500, 500, 0}};
    ActorAiFacts actor = makeMm9Walker();
    actor.target = {};
    actor.movement.mm9PathPoints = path;
    actor.movement.mm9Placement->wander = OpenYAMM::Game::Mm9AiWanderMode::Path;
    actor.movement.mm9Placement->wanderWaitMinSeconds = 0.0f;
    actor.movement.mm9Placement->wanderWaitMaxSeconds = 0.0f;
    actor.runtime.mm9.wanderSeconds = 0.0f;

    // The startup ends; the wait (0.01 s: below 0.2 s it goes at once) and the first marker, walked to.
    ActorAiUpdate update = stepMm9(actor);
    REQUIRE(findDecision(update, ActorAiDecisionKind::Patrol));
    CHECK(findDecision(update, ActorAiDecisionKind::Patrol)->marker == 0);
    actor.runtime.mm9 = *update.state.mm9;
    update = stepMm9(actor);
    CHECK(update.state.motionState == ActorAiMotionState::Wandering);
    CHECK(update.movementIntent.moveDirectionY > 0.99f);

    // Touching it: a wait, then the next marker.
    actor.movement.position = {0.0f, 480.0f, 0.0f};
    update = stepMm9(actor);
    CHECK(findDecision(update, ActorAiDecisionKind::MarkerReached).has_value());
    actor.runtime.mm9 = *update.state.mm9;
    update = stepMm9(actor);
    CHECK(findDecision(update, ActorAiDecisionKind::Patrol)->marker == 1);

    // Noticing the party it stops wandering and alerts its friends at once.
    actor.runtime.mm9 = *update.state.mm9;
    actor.target = makeMm9Walker().target;
    update = stepMm9(actor);
    REQUIRE(update.mm9Request);
    CHECK(update.mm9Request->alert);
    CHECK(update.mm9Request->callTargetKind == ActorAiTargetKind::Party);
    CHECK(update.state.mm9->wanderPhase == OpenYAMM::Game::Mm9WanderPhase::Off);
}

TEST_CASE("MM9 walker takes the target of a friend's alert")
{
    ActorAiFacts actor = makeMm9Walker();
    actor.target = {};
    actor.mm9World.callSerial = 1;
    actor.mm9World.callTargetKind = ActorAiTargetKind::Party;
    actor.mm9World.callTargetValid = true;
    actor.mm9World.callTargetDistance = 2000.0f;
    const ActorAiUpdate update = stepMm9(actor);
    const std::optional<ActorAiDecision> alert = findDecision(update, ActorAiDecisionKind::Alert);
    REQUIRE(alert);
    CHECK(alert->pNote == std::string("take"));
    CHECK(update.state.mm9->targetKind == ActorAiTargetKind::Party);

    // A help call reaches only a monster holding no target.
    actor.runtime.mm9 = *update.state.mm9;
    actor.mm9World.callSerial = 2;
    actor.mm9World.callIsHelp = true;
    const ActorAiUpdate busy = stepMm9(actor);
    CHECK_FALSE(findDecision(busy, ActorAiDecisionKind::Help).has_value());
    CHECK(busy.state.mm9->seenCallSerial == 2);
}

TEST_CASE("MM9 corpse asks to be raised and rises")
{
    ActorAiFacts actor = makeMm9Walker();
    actor.target = {};
    actor.tactics.mm9Profile->raiseSeconds = 2.0f;
    actor.movement.mm9Placement->canBeResurrected = true;
    actor.runtime.motionState = ActorAiMotionState::Dead;
    actor.runtime.animationState = ActorAiAnimationState::Dead;
    actor.status.dead = true;
    actor.stats.currentHp = 0;
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.dyingSeen = true;

    const auto stepCorpse = [](const ActorAiFacts &corpse)
    {
        ActorAiFrameFacts frame = makeMm9Frame(corpse);
        frame.activeActors.clear();
        frame.backgroundActors.push_back(corpse);
        const GameplayActorAiSystem system = {};
        return system.updateActors(frame).actorUpdates.front();
    };

    // A corpse the map loaded dead (no death seen this session) never asks.
    ActorAiFacts loaded = actor;
    loaded.runtime.mm9.dyingSeen = false;
    CHECK_FALSE(stepCorpse(loaded).mm9Request.has_value());

    // OnDeathDone: it remembers its target and asks at once.
    ActorAiUpdate update = stepCorpse(actor);
    REQUIRE(update.mm9Request);
    CHECK(update.mm9Request->askResurrection);
    CHECK(update.state.mm9->deathTargetKind == ActorAiTargetKind::Party);

    // A resurrecter's key raises it; with nobody near it rises with full health and its Resurrect clip.
    actor.runtime.mm9 = *update.state.mm9;
    actor.mm9World.resurrecterFound = true;
    actor.mm9World.raiseSerial = 1;
    update = stepCorpse(actor);
    REQUIRE(update.mm9Request);
    CHECK(update.mm9Request->revive);
    CHECK(update.state.mm9->raiseSeconds == doctest::Approx(2.0f));
}

TEST_CASE("MM9 phase 4b rules: townsfolk, guards, dormant starts")
{
    using namespace OpenYAMM::Game;
    // GetRandomInt 0, n - 1 picks the guard.
    CHECK(mm9PickRefuge(0, 0.5f) == -1);
    CHECK(mm9PickRefuge(3, 0.0f) == 0);
    CHECK(mm9PickRefuge(3, 0.999f) == 2);
    // NPCBase.inc: a townsperson that runs from (or talks to) the party ignores a hit.
    CHECK_FALSE(mm9CivilianRunsFromHit(true));
    CHECK(mm9CivilianRunsFromHit(false));
    // PoliceMan.inc: a monster's alert is ignored; a fellow guard's alert or a friend's help call about the party makes
    // the party its enemy; an alert from anyone else changes nothing.
    Mm9PoliceCallInput call = {};
    call.senderIsMonster = true;
    CHECK(mm9PoliceCall(call).ignored);
    call.help = true;
    call.targetIsFriend = true;
    CHECK_FALSE(mm9PoliceCall(call).ignored);
    CHECK(mm9PoliceCall(call).targetBecomesEnemy);
    call = {};
    call.senderIsGuard = true;
    call.targetIsFriend = true;
    CHECK(mm9PoliceCall(call).targetBecomesEnemy);
    call.senderIsGuard = false;
    CHECK_FALSE(mm9PoliceCall(call).targetBecomesEnemy);
    CHECK_FALSE(mm9GuardTurnsOnParty(2));
    CHECK(mm9GuardTurnsOnParty(3));
    // Dormant starts: a trigger and a hit always; disturbed also calls, a hanging one sights only while it fidgets.
    CHECK(mm9DormantWakes(Mm9AiDormantUntil::Trigger, Mm9AiDormantPose::Coffin, Mm9DormantEvent::Hit, false));
    CHECK_FALSE(mm9DormantWakes(Mm9AiDormantUntil::Trigger, Mm9AiDormantPose::Coffin, Mm9DormantEvent::Alert, false));
    CHECK_FALSE(mm9DormantWakes(Mm9AiDormantUntil::Trigger, Mm9AiDormantPose::Coffin, Mm9DormantEvent::Sighted, false));
    CHECK(mm9DormantWakes(Mm9AiDormantUntil::Disturbed, Mm9AiDormantPose::Hang, Mm9DormantEvent::Alert, false));
    CHECK_FALSE(mm9DormantWakes(Mm9AiDormantUntil::Disturbed, Mm9AiDormantPose::Hang, Mm9DormantEvent::Sighted, false));
    CHECK(mm9DormantWakes(Mm9AiDormantUntil::Disturbed, Mm9AiDormantPose::Hang, Mm9DormantEvent::Sighted, true));
    CHECK(mm9DormantWakes(Mm9AiDormantUntil::Disturbed, Mm9AiDormantPose::Sleep, Mm9DormantEvent::Sighted, false));
    CHECK(mm9DormantWakes(Mm9AiDormantUntil::Sighted, Mm9AiDormantPose::Hidden, Mm9DormantEvent::Sighted, false));
    CHECK_FALSE(mm9DormantWakes(Mm9AiDormantUntil::Sighted, Mm9AiDormantPose::Hidden, Mm9DormantEvent::Help, false));
    CHECK(mm9HangFidgetWaitSeconds(0.0f) == doctest::Approx(2.0f));
    CHECK(mm9HangFidgetWaitSeconds(1.0f) == doctest::Approx(10.0f));
    CHECK(mm9IdleFidgetWaitSeconds(0.0f) == doctest::Approx(5.0f));
    CHECK(mm9IdleFidgetWaitSeconds(1.0f) == doctest::Approx(12.0f));
    CHECK(mm9FidgetVariant(0.0f, 3) == 0);
    CHECK(mm9FidgetVariant(0.5f, 3) == 1);
    CHECK(mm9FidgetVariant(0.999f, 3) == 2);
    CHECK(mm9FidgetVariant(1.0f, 3) == 2);
    CHECK(mm9FidgetVariant(0.7f, 0) == 0);
    // ScriptParams 1 on the row's own script marks MM9's spawns.
    Mm9AiPlacementRecord record = {};
    record.scriptParams = "1";
    CHECK(mm9SpawnedWithParam(record));
    record.scriptParams = "10";
    CHECK_FALSE(mm9SpawnedWithParam(record));
    record.scriptParams = "1";
    record.script = "lesserdemon.scr";
    CHECK_FALSE(mm9SpawnedWithParam(record));
    // Townsfolk and guards run MM9 loops; a guard is a walker.
    CHECK(mm9LoopArchetype(mm9StandInCivilianProfile()));
    CHECK(mm9WalkerArchetype(Mm9AiArchetype::Guard));
    CHECK_FALSE(mm9WalkerArchetype(Mm9AiArchetype::Civilian));
}

TEST_CASE("MM9 townsperson runs to a guard from a hit and ignores the party's next hits")
{
    using namespace OpenYAMM::Game;
    ActorAiFacts actor = makeMm9Walker();
    actor.tactics.mm9Profile = mm9StandInCivilianProfile();
    actor.status.hostileToParty = false;
    actor.target = {};
    actor.mm9World.damageSerial = 1;
    actor.mm9World.attackerKind = ActorAiTargetKind::Party;
    actor.mm9World.attackerPosition = {1000.0f, 0.0f, 0.0f};
    actor.mm9World.refugeCount = 1;
    actor.mm9World.refugeActorIndices[0] = 4;
    actor.mm9World.refugePositions[0] = {-2000.0f, 0.0f, 0.0f};
    actor.mm9World.refugeRadii[0] = 40.0f;
    const ActorAiUpdate update = stepMm9(actor);
    REQUIRE(update.state.mm9);
    CHECK(update.state.mm9->fleeMode == Mm9FleeMode::Hide);
    CHECK(update.state.mm9->refugeActorIndex == 4);
    const std::optional<ActorAiDecision> hide = findDecision(update, ActorAiDecisionKind::Hide);
    REQUIRE(hide);
    CHECK(hide->pNote == std::string("guard"));
    CHECK_FALSE(update.attackRequest.has_value());

    // Running from the party it ignores the party's next hit (no new flight decision).
    actor.runtime.mm9 = *update.state.mm9;
    actor.mm9World.damageSerial = 2;
    const ActorAiUpdate again = stepMm9(actor);
    CHECK_FALSE(findDecision(again, ActorAiDecisionKind::FleeDecision).has_value());

    // Without a guard it runs and stops at its first tick (ShouldRunAway says no: not a runner).
    ActorAiFacts alone = makeMm9Walker();
    alone.tactics.mm9Profile = mm9StandInCivilianProfile();
    alone.status.hostileToParty = false;
    alone.target = {};
    alone.movement.mm9Placement->runawayChance = 0.0f;
    alone.mm9World.damageSerial = 1;
    alone.mm9World.attackerKind = ActorAiTargetKind::Party;
    ActorAiUpdate run = stepMm9(alone);
    CHECK(run.state.mm9->fleeMode == Mm9FleeMode::Run);
    alone.runtime.mm9 = *run.state.mm9;
    alone.runtime.mm9.fleeTickSeconds = 0.0f;
    run = stepMm9(alone);
    CHECK(run.state.mm9->fleeMode == Mm9FleeMode::None);
    const std::optional<ActorAiDecision> stop = findDecision(run, ActorAiDecisionKind::GiveUp);
    REQUIRE(stop);
    CHECK(stop->pNote == std::string("fled"));
}

TEST_CASE("MM9 guard turns on the party at its third hit")
{
    using namespace OpenYAMM::Game;
    ActorAiFacts guard = makeMm9Walker(Mm9AiArchetype::Guard);
    guard.status.hostileToParty = false;
    guard.target = {};
    guard.mm9World.attackerKind = ActorAiTargetKind::Party;

    for (uint32_t hit = 1; hit <= 3; ++hit)
    {
        guard.mm9World.damageSerial = hit;
        const ActorAiUpdate update = stepMm9(guard);
        guard.runtime.mm9 = *update.state.mm9;
        const bool turned = update.mm9Request && update.mm9Request->turnOnParty;
        const bool third = hit == 3;
        const bool takesParty = update.state.mm9->targetKind == ActorAiTargetKind::Party;
        CHECK(turned == third);
        CHECK(takesParty == third);
    }

    // A friend's help call about the party turns it at once.
    ActorAiFacts other = makeMm9Walker(Mm9AiArchetype::Guard);
    other.status.hostileToParty = false;
    other.target = {};
    other.mm9World.callSerial = 1;
    other.mm9World.callIsHelp = true;
    other.mm9World.callTargetKind = ActorAiTargetKind::Party;
    const ActorAiUpdate helped = stepMm9(other);
    REQUIRE(helped.mm9Request);
    CHECK(helped.mm9Request->turnOnParty);
    CHECK(helped.state.mm9->targetKind == ActorAiTargetKind::Party);

    // A monster's alert is ignored.
    other.mm9World.callIsHelp = false;
    other.mm9World.callFromMonster = true;
    const ActorAiUpdate ignored = stepMm9(other);
    const bool turnedByMonster = ignored.mm9Request.has_value() && ignored.mm9Request->turnOnParty;
    CHECK_FALSE(turnedByMonster);
}

TEST_CASE("MM9 hanging Icky wakes on an alert and launches")
{
    using namespace OpenYAMM::Game;
    ActorAiFacts icky = makeMm9Walker(Mm9AiArchetype::Flier);
    icky.tactics.mm9Profile->movement = Mm9AiMovement::Fly;
    icky.tactics.mm9Profile->dormantUntil = Mm9AiDormantUntil::Disturbed;
    icky.tactics.mm9Profile->dormantPose = Mm9AiDormantPose::Hang;
    icky.tactics.mm9Profile->wakeSeconds = 1.0f;
    icky.tactics.mm9Profile->dormantFidgetSeconds = 2.6f;
    icky.movement.dormant = true;
    // Out of a fidget it notices nothing it sees.
    ActorAiUpdate update = stepMm9(icky);
    CHECK_FALSE(findDecision(update, ActorAiDecisionKind::Wake).has_value());
    icky.runtime.mm9 = *update.state.mm9;
    // An alert naming the party wakes it; it launches.
    icky.mm9World.callSerial = 1;
    icky.mm9World.callTargetKind = ActorAiTargetKind::Party;
    icky.mm9World.callTargetValid = true;
    update = stepMm9(icky);
    const std::optional<ActorAiDecision> wake = findDecision(update, ActorAiDecisionKind::Wake);
    REQUIRE(wake);
    CHECK(wake->pNote == std::string("alert"));
    REQUIRE(update.mm9Request);
    CHECK(update.mm9Request->wake);
    CHECK(update.state.mm9->wakeSeconds == doctest::Approx(1.0f));
    CHECK(update.state.mm9->targetKind == ActorAiTargetKind::Party);
}

TEST_CASE("MM9 recovery counts from the clip's end, a cast from its cast; a cut attack keeps only its hit's recovery")
{
    using OpenYAMM::Game::mm9AttackStartCooldown;
    using OpenYAMM::Game::mm9CutAttackCooldown;
    using OpenYAMM::Game::mm9ScriptRecoveryTimeLeft;

    // Recovery 30 (0.99 s) after a 1.03 s clip: ready 2.02 s after the blow or shot began, no random factor.
    CHECK_EQ(mm9AttackStartCooldown(false, 1.03f, 0.5f, 0.99f), doctest::Approx(2.02f));
    // A cast: its spell's recovery from the cast key (0.8 s into a 2 s clip), the clip's end adds nothing.
    CHECK_EQ(mm9AttackStartCooldown(true, 2.0f, 0.8f, 2.97f), doctest::Approx(3.77f));

    // A wince before the hit (or after a missed blow): no recovery.
    CHECK_EQ(mm9CutAttackCooldown(false, false, 1.5f, 0.5f), doctest::Approx(0.0f));
    // After a blow that connected with 0.5 s of its clip left: hit time + recovery, the clip's end not counted.
    CHECK_EQ(mm9CutAttackCooldown(true, false, 1.3f, 0.5f), doctest::Approx(0.8f));
    // After a cast: its recovery stands.
    CHECK_EQ(mm9CutAttackCooldown(true, true, 2.5f, 1.2f), doctest::Approx(2.5f));

    // The scripts' RecoveryTimeLeft is 3.03 times the real time left.
    CHECK_EQ(mm9ScriptRecoveryTimeLeft(0.99f), doctest::Approx(3.0f));
    CHECK_EQ(mm9ScriptRecoveryTimeLeft(-1.0f), doctest::Approx(0.0f));
}

TEST_CASE("MM9 dormant wake holds for the Launch of a hanging start and the Wakeup of a lying one")
{
    using OpenYAMM::Game::Mm9AiDormantPose;
    using OpenYAMM::Game::mm9WakeHoldSeconds;
    using OpenYAMM::Game::mm9WakesWithWakeup;
    CHECK(mm9WakeHoldSeconds(Mm9AiDormantPose::Hang, 1.2f, 2.0f) == doctest::Approx(1.2f));
    CHECK(mm9WakeHoldSeconds(Mm9AiDormantPose::Coffin, 1.2f, 2.0f) == doctest::Approx(2.0f));
    CHECK(mm9WakeHoldSeconds(Mm9AiDormantPose::Sleep, 1.2f, 2.0f) == doctest::Approx(2.0f));
    // A model without Wakeup, and a start that does not lie, get up at once.
    CHECK(mm9WakeHoldSeconds(Mm9AiDormantPose::Coffin, 1.2f, 0.0f) == 0.0f);
    CHECK(mm9WakeHoldSeconds(Mm9AiDormantPose::Stand, 1.2f, 2.0f) == 0.0f);
    CHECK(mm9WakesWithWakeup(Mm9AiDormantPose::Lie));
    CHECK_FALSE(mm9WakesWithWakeup(Mm9AiDormantPose::Hang));
    CHECK_FALSE(mm9WakesWithWakeup(Mm9AiDormantPose::Caged));
}

TEST_CASE("reposition rules: candidates within the leash nearest first, back-off spots, a rush, lost sight")
{
    using OpenYAMM::Game::ActorRepositionMaxCandidates;
    using OpenYAMM::Game::GameplayWorldPoint;
    using OpenYAMM::Game::RepositionModifier;
    using OpenYAMM::Game::repositionDistance2d;

    RepositionModifier settings = {};
    std::array<GameplayWorldPoint, ActorRepositionMaxCandidates> spots = {};
    const GameplayWorldPoint post = {0.0f, 0.0f, 0.0f};

    // At its post: eight spots, alternately at 320 and 640, nearest first.
    size_t count = OpenYAMM::Game::repositionCandidates(post, post, settings, 0.1f, spots);
    REQUIRE(count == 8);
    for (size_t index = 0; index < count; ++index)
    {
        CHECK(repositionDistance2d(post, spots[index]) == doctest::Approx(index < 4 ? 320.0f : 640.0f));
    }

    // Near its leash's edge every spot is pulled inside it, and those that end next to it are dropped.
    const GameplayWorldPoint edge = {1000.0f, 0.0f, 0.0f};
    count = OpenYAMM::Game::repositionCandidates(edge, post, settings, 0.0f, spots);
    REQUIRE(count > 0);
    for (size_t index = 0; index < count; ++index)
    {
        CHECK(repositionDistance2d(post, spots[index]) <= settings.leashRadius + 0.01f);
        CHECK(repositionDistance2d(edge, spots[index]) >= OpenYAMM::Game::RepositionMinimumMove);
        if (index > 0)
        {
            CHECK(repositionDistance2d(edge, spots[index - 1]) <= repositionDistance2d(edge, spots[index]) + 0.01f);
        }
    }
    settings.candidates = 3;
    CHECK(OpenYAMM::Game::repositionCandidates(post, post, settings, 0.5f, spots) == 3);
    settings.candidates = 8;

    // Back-off: straight away from the target first, then turned, all farther from the target.
    const GameplayWorldPoint target = {500.0f, 0.0f, 0.0f};
    count = OpenYAMM::Game::repositionBackOffCandidates(post, target, post, settings, 1.0f, spots);
    REQUIRE(count == 5);
    CHECK(spots[0].x == doctest::Approx(-384.0f));
    CHECK(spots[0].y == doctest::Approx(0.0f).epsilon(0.001));
    CHECK(spots[1].y < 0.0f);
    for (size_t index = 0; index < count; ++index)
    {
        CHECK(repositionDistance2d(target, spots[index]) >= 500.0f + 0.5f * settings.backOffDistance);
    }

    // At its leash's far side a back-off away from the target has no room.
    const GameplayWorldPoint farSide = {-1024.0f, 0.0f, 0.0f};
    CHECK(OpenYAMM::Game::repositionBackOffCandidates(farSide, {-500.0f, 0.0f, 0.0f}, post, settings, 1.0f, spots)
        == 0);

    // A rush: outside its reach, inside the trigger distance, closing at the trigger speed.
    CHECK(OpenYAMM::Game::repositionClosingSpeed(post, target, -300.0f, 0.0f) == doctest::Approx(300.0f));
    CHECK(OpenYAMM::Game::repositionClosingSpeed(post, target, 0.0f, 300.0f) == doctest::Approx(0.0f));
    CHECK(OpenYAMM::Game::repositionRushed(settings, 400.0f, 112.0f, 300.0f));
    CHECK_FALSE(OpenYAMM::Game::repositionRushed(settings, 100.0f, 112.0f, 300.0f));
    CHECK_FALSE(OpenYAMM::Game::repositionRushed(settings, 700.0f, 112.0f, 300.0f));
    CHECK_FALSE(OpenYAMM::Game::repositionRushed(settings, 400.0f, 112.0f, 150.0f));

    CHECK_FALSE(OpenYAMM::Game::repositionLostSight(settings, 1.9f));
    CHECK(OpenYAMM::Game::repositionLostSight(settings, 2.0f));
}

TEST_CASE("reposition: a holder that lost sight asks for a spot, walks there and stops once it sees")
{
    using OpenYAMM::Game::Mm9RepositionPhase;

    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::RangedHolder);
    actor.tactics.mm9Profile->ranged = Mm9AiRanged::Walker;
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.shotCheckSeconds = 0.3f;
    actor.target.currentHasAttackLineOfSight = false;
    actor.runtime.mm9.unseenSeconds = 2.5f;

    // Without the modifier: MM9's holder holds, asking nothing.
    ActorAiUpdate update = stepMm9(actor);
    CHECK(findDecision(update, ActorAiDecisionKind::Hold).has_value());
    CHECK_FALSE(update.mm9Request.has_value());

    // With it, but never having seen its target (it only heard it): nowhere to look.
    actor.tactics.reposition = OpenYAMM::Game::RepositionModifier{};
    update = stepMm9(actor);
    CHECK_FALSE(update.mm9Request.has_value());

    // It saw the target at (900, 300): the spots must see there, not where the target is now (the world's facts).
    actor.runtime.mm9.hasLastSeen = true;
    actor.runtime.mm9.lastSeenTarget = {900.0f, 300.0f, 96.0f};
    update = stepMm9(actor);
    REQUIRE(update.mm9Request);
    REQUIRE(update.mm9Request->reposition);
    CHECK(update.mm9Request->reposition->needsSight);
    CHECK(update.mm9Request->reposition->target.x == doctest::Approx(900.0f));
    CHECK(update.mm9Request->reposition->target.y == doctest::Approx(300.0f));
    CHECK(update.mm9Request->reposition->minTargetDistance == doctest::Approx(640.0f));
    CHECK(update.mm9Request->reposition->count == 8);
    CHECK(update.mm9Request->reposition->maxSightChecks == 12);
    CHECK(update.state.mm9->repositionPhase == Mm9RepositionPhase::SightQuery);
    CHECK(update.state.motionState == ActorAiMotionState::Standing);

    // The world found a spot: it walks there, tracing the spot.
    actor.runtime.mm9 = *update.state.mm9;
    actor.mm9World.repositionSerial = 1;
    actor.mm9World.repositionFound = true;
    actor.mm9World.repositionSpot = {0.0f, 400.0f, 0.0f};
    actor.mm9World.repositionSightChecks = 3;
    update = stepMm9(actor);
    const std::optional<ActorAiDecision> chosen = findDecision(update, ActorAiDecisionKind::Reposition);
    REQUIRE(chosen);
    CHECK(chosen->pNote == std::string("spot"));
    CHECK(chosen->hasPoint);
    CHECK(chosen->checks == 3);
    CHECK(update.state.mm9->repositionPhase == Mm9RepositionPhase::Moving);
    CHECK(update.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(update.movementIntent.targetPosition.y == doctest::Approx(400.0f));

    // On the way it sees its target: it stops, its shot check due at once.
    actor.runtime.mm9 = *update.state.mm9;
    actor.movement.position = {0.0f, 200.0f, 0.0f};
    actor.target.currentHasAttackLineOfSight = true;
    update = stepMm9(actor);
    const std::optional<ActorAiDecision> arrived = findDecision(update, ActorAiDecisionKind::RepositionArrived);
    REQUIRE(arrived);
    CHECK(arrived->pNote == std::string("sight"));
    CHECK(update.state.mm9->repositionPhase == Mm9RepositionPhase::None);
    CHECK(update.state.mm9->shotCheckSeconds == 0.0f);
    // Seen, the target's place is noted again (the prelude).
    CHECK(update.state.mm9->hasLastSeen);
    CHECK(update.state.mm9->lastSeenTarget.x == doctest::Approx(1000.0f));
}

TEST_CASE("reposition: on a spot that sees where the target was, without the target there, it searches no more")
{
    using OpenYAMM::Game::Mm9RepositionPhase;

    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::RangedHolder);
    actor.tactics.mm9Profile->ranged = Mm9AiRanged::Walker;
    actor.tactics.reposition = OpenYAMM::Game::RepositionModifier{};
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.target.currentHasAttackLineOfSight = false;
    actor.runtime.mm9.unseenSeconds = 3.0f;
    actor.runtime.mm9.hasLastSeen = true;
    actor.runtime.mm9.lastSeenTarget = {900.0f, 300.0f, 96.0f};
    actor.runtime.mm9.repositionPhase = Mm9RepositionPhase::Moving;
    actor.runtime.mm9.repositionSpot = {0.0f, 400.0f, 0.0f};
    actor.runtime.mm9.repositionSeconds = 3.0f;
    actor.movement.position = {0.0f, 396.0f, 0.0f};

    ActorAiUpdate update = stepMm9(actor);
    CHECK(findDecision(update, ActorAiDecisionKind::RepositionArrived)->pNote == std::string("spot"));
    CHECK(update.state.mm9->lastSeenSearched);

    // Its retry wait over, it still asks nothing for that place: it holds until it sees the target or loses it.
    actor.runtime.mm9 = *update.state.mm9;
    actor.runtime.mm9.repositionSearchWaitSeconds = 0.0f;
    update = stepMm9(actor);
    CHECK_FALSE(update.mm9Request.has_value());
    CHECK(update.state.mm9->repositionPhase == Mm9RepositionPhase::None);
}

TEST_CASE("reposition: no spot sends it back to its post, and a walk never passes its leash")
{
    using OpenYAMM::Game::Mm9RepositionPhase;

    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::RangedHolder);
    actor.tactics.mm9Profile->ranged = Mm9AiRanged::Walker;
    actor.tactics.reposition = OpenYAMM::Game::RepositionModifier{};
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.target.currentHasAttackLineOfSight = false;
    actor.runtime.mm9.unseenSeconds = 3.0f;
    actor.runtime.mm9.repositionPhase = Mm9RepositionPhase::SightQuery;
    actor.runtime.mm9.repositionSeconds = 0.4f;
    actor.movement.homePosition = {-500.0f, 0.0f, 0.0f};
    actor.mm9World.repositionSerial = 4;
    actor.mm9World.repositionFound = false;
    actor.mm9World.repositionSightChecks = 12;

    ActorAiUpdate update = stepMm9(actor);
    const std::optional<ActorAiDecision> post = findDecision(update, ActorAiDecisionKind::Reposition);
    REQUIRE(post);
    CHECK(post->pNote == std::string("post"));
    CHECK(update.state.mm9->repositionPhase == Mm9RepositionPhase::Returning);
    CHECK(update.state.mm9->repositionSpot.x == doctest::Approx(-500.0f));

    // At its post with no spot: it holds.
    actor.movement.homePosition = {0.0f, 0.0f, 0.0f};
    update = stepMm9(actor);
    CHECK(findDecision(update, ActorAiDecisionKind::Reposition)->pNote == std::string("none"));
    CHECK(update.state.mm9->repositionPhase == Mm9RepositionPhase::None);
    CHECK(update.state.mm9->repositionSearchWaitSeconds == 0.0f);

    // A walk that strays past its leash (a detour) ends there.
    actor.runtime.mm9.repositionPhase = Mm9RepositionPhase::Moving;
    actor.runtime.mm9.repositionSpot = {900.0f, 0.0f, 0.0f};
    actor.runtime.mm9.repositionSeconds = 5.0f;
    actor.runtime.mm9.seenRepositionSerial = 4;
    actor.movement.position = {0.0f, 1200.0f, 0.0f};
    update = stepMm9(actor);
    CHECK(findDecision(update, ActorAiDecisionKind::RepositionArrived)->pNote == std::string("leash"));
}

TEST_CASE("reposition: a rushing target makes the holder back off, then its shot check comes at once")
{
    using OpenYAMM::Game::Mm9RepositionPhase;

    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::RangedHolder);
    actor.tactics.mm9Profile->ranged = Mm9AiRanged::Walker;
    actor.tactics.reposition = OpenYAMM::Game::RepositionModifier{};
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.runtime.mm9.shotCheckSeconds = 0.3f;
    actor.target.currentPosition = {500.0f, 0.0f, 0.0f};
    actor.target.currentDistance = 500.0f;
    actor.target.currentEdgeDistance = 460.0f;

    const auto step = [](const ActorAiFacts &facts, float partyVelocityX)
    {
        ActorAiFrameFacts frame = makeMm9Frame(facts);
        frame.party.position = {500.0f, 0.0f, 0.0f};
        frame.party.velocityX = partyVelocityX;
        const GameplayActorAiSystem system = {};
        const ActorAiFrameResult result = system.updateActors(frame);
        REQUIRE(result.actorUpdates.size() == 1);
        return result.actorUpdates.front();
    };

    // Standing still is no rush.
    ActorAiUpdate update = step(actor, 0.0f);
    CHECK_FALSE(update.mm9Request.has_value());

    update = step(actor, -400.0f);
    REQUIRE(update.mm9Request);
    REQUIRE(update.mm9Request->reposition);
    CHECK_FALSE(update.mm9Request->reposition->needsSight);
    CHECK(update.mm9Request->reposition->candidates[0].x == doctest::Approx(-384.0f));
    CHECK(update.state.mm9->repositionPhase == Mm9RepositionPhase::BackOffQuery);

    // Room behind it: it backpedals (the skirmisher's back-off phase, which the model plays as its backpedal).
    actor.runtime.mm9 = *update.state.mm9;
    actor.mm9World.repositionSerial = 1;
    actor.mm9World.repositionFound = true;
    actor.mm9World.repositionSpot = {-384.0f, 0.0f, 0.0f};
    update = step(actor, -400.0f);
    REQUIRE(findDecision(update, ActorAiDecisionKind::BackOffRush));
    CHECK(findDecision(update, ActorAiDecisionKind::BackOffRush)->pNote == std::string("spot"));
    CHECK(update.state.skirmishPhase == OpenYAMM::Game::ActorSkirmishPhase::BackOff);
    CHECK(update.movementIntent.moveDirectionX < -0.99f);
    CHECK(update.movementIntent.keepYawWhileMoving);

    // At the spot it stops, its next back-off waits, and its shot check is due.
    actor.runtime.mm9 = *update.state.mm9;
    actor.runtime.skirmishPhase = OpenYAMM::Game::ActorSkirmishPhase::BackOff;
    actor.runtime.skirmishSeconds = 0.5f;
    actor.movement.position = {-380.0f, 0.0f, 0.0f};
    actor.movement.moveDirectionX = -1.0f;
    update = step(actor, -400.0f);
    CHECK(update.state.mm9->repositionPhase == Mm9RepositionPhase::None);
    CHECK(update.state.mm9->backOffWaitSeconds == doctest::Approx(5.0f));
    CHECK(update.state.mm9->shotCheckSeconds == 0.0f);
    CHECK(update.state.skirmishPhase == OpenYAMM::Game::ActorSkirmishPhase::None);
}

namespace
{
struct Mm9IdleFidget
{
    float clock = 0.0f;
    int variant = -1;
    float seconds = 0.0f;
};

// Steps an idle MM9 walker for the given time, carrying its state between steps, and returns its fidgets.
std::vector<Mm9IdleFidget> runMm9Idle(ActorAiFacts &actor, float seconds)
{
    constexpr float Step = 1.0f / 128.0f;
    std::vector<Mm9IdleFidget> fidgets;

    for (float clock = 0.0f; clock < seconds; clock += Step)
    {
        const ActorAiUpdate update = stepMm9(actor);

        if (const std::optional<ActorAiDecision> fidget = findDecision(update, ActorAiDecisionKind::Fidget))
        {
            CHECK(update.animation.animationState == ActorAiAnimationState::Bored);
            fidgets.push_back({clock, fidget->variant, fidget->seconds});
        }

        actor.runtime.mm9 = *update.state.mm9;
        actor.runtime.motionState = update.state.motionState.value_or(actor.runtime.motionState);
        actor.runtime.animationState = update.animation.animationState.value_or(actor.runtime.animationState);
        actor.runtime.idleDecisionCount = update.state.idleDecisionCount.value_or(actor.runtime.idleDecisionCount);
    }

    return fidgets;
}
}

TEST_CASE("MM9 idle fidgets 5-12 s after entering idle, once, with a clip picked among its model's")
{
    ActorAiFacts actor = makeMm9Walker();
    actor.target = {};
    actor.runtime.mm9.wanderSeconds = 0.0f;
    actor.runtime.fidgetClips.count = 3;
    actor.runtime.fidgetClips.seconds = {1.5f, 2.0f, 2.5f};
    const std::vector<Mm9IdleFidget> fidgets = runMm9Idle(actor, 90.0f);

    // The first comes 5-12 s after the idle began, each next one 5-12 s after the last ended (AIBase::SetAnimState
    // arms the timer as the fidget's end sets idle again), lasting its clip.
    REQUIRE(fidgets.size() >= 5);
    CHECK(fidgets[0].clock >= 5.0f);
    CHECK(fidgets[0].clock <= 12.05f);
    bool otherVariant = false;

    for (size_t index = 0; index < fidgets.size(); ++index)
    {
        REQUIRE(fidgets[index].variant >= 0);
        REQUIRE(fidgets[index].variant < 3);
        CHECK(fidgets[index].seconds == doctest::Approx(actor.runtime.fidgetClips.seconds[fidgets[index].variant]));
        otherVariant = otherVariant || fidgets[index].variant != fidgets[0].variant;

        if (index > 0)
        {
            const float wait = fidgets[index].clock - (fidgets[index - 1].clock + fidgets[index - 1].seconds);
            CHECK(wait >= 4.95f);
            CHECK(wait <= 12.05f);
        }
    }

    CHECK(otherVariant);
}

TEST_CASE("MM9 idle without fidget variants plays its one fidget for the sprite's length")
{
    ActorAiFacts actor = makeMm9Walker();
    actor.target = {};
    actor.runtime.mm9.wanderSeconds = 0.0f;
    actor.runtime.boredAnimationSeconds = 1.25f;
    const std::vector<Mm9IdleFidget> fidgets = runMm9Idle(actor, 30.0f);
    REQUIRE(fidgets.size() >= 2);

    for (const Mm9IdleFidget &fidget : fidgets)
    {
        CHECK(fidget.variant == 0);
        CHECK(fidget.seconds == doctest::Approx(1.25f));
    }
}

TEST_CASE("MM9 idle arms its fidget anew whenever it returns to idle")
{
    ActorAiFacts actor = makeMm9Walker();
    actor.target = {};
    actor.runtime.mm9.wanderSeconds = 0.0f;
    runMm9Idle(actor, 1.0f);
    REQUIRE(actor.runtime.mm9.idleThisStep);
    const float armed = actor.runtime.mm9.idleFidgetWaitSeconds;
    CHECK(armed >= 4.0f);

    // A fight (a target it sees) leaves idle; back without one, a new wait is rolled.
    actor.target = makeMm9Walker().target;
    actor.runtime.mm9 = *stepMm9(actor).state.mm9;
    CHECK_FALSE(actor.runtime.mm9.idleThisStep);
    actor.target = {};
    actor.runtime.mm9.targetKind = ActorAiTargetKind::None;
    actor.runtime.motionState = ActorAiMotionState::Standing;
    actor.runtime.animationState = ActorAiAnimationState::Standing;
    const ActorAiUpdate update = stepMm9(actor);
    CHECK(update.state.mm9->idleThisStep);
    CHECK(update.state.mm9->idleFidgetWaitSeconds >= 5.0f);
    CHECK(update.state.mm9->idleFidgetWaitSeconds <= 12.0f);
    CHECK(update.state.mm9->idleFidgetWaitSeconds != doctest::Approx(armed));
}

TEST_CASE("MM9 townsperson turns back to its facing after a talk at 180 degrees a second")
{
    constexpr float Pi = 3.14159265f;
    ActorAiFacts actor = makeMm9Walker(Mm9AiArchetype::Civilian);
    actor.target = {};
    actor.runtime.mm9.wanderSeconds = 0.0f;
    actor.runtime.mm9.beginTalk(0.0f);
    // The talk turned it to the party, a quarter turn away.
    actor.runtime.yawRadians = 0.5f * Pi;
    float clock = 0.0f;

    while (actor.runtime.mm9.talkTurnBack && clock < 2.0f)
    {
        const ActorAiUpdate update = stepMm9(actor);
        actor.runtime.mm9 = *update.state.mm9;
        actor.runtime.yawRadians = update.movementIntent.updateYaw ? update.movementIntent.yawRadians
                                                                   : actor.runtime.yawRadians;
        clock += 1.0f / 128.0f;

        if (std::abs(clock - 0.25f) < 0.5f / 128.0f)
        {
            CHECK(actor.runtime.yawRadians == doctest::Approx(0.25f * Pi).epsilon(0.02));
        }
    }

    CHECK_FALSE(actor.runtime.mm9.talkTurnBack);
    CHECK(actor.runtime.yawRadians == doctest::Approx(0.0f).epsilon(0.001));
    CHECK(clock == doctest::Approx(0.5f).epsilon(0.03));

    // A target it notices meanwhile faces it instead: no turn back.
    actor.runtime.mm9.beginTalk(0.0f);
    actor.runtime.mm9.targetKind = ActorAiTargetKind::Party;
    actor.target = makeMm9Walker().target;
    CHECK_FALSE(stepMm9(actor).state.mm9->talkTurnBack);
}
