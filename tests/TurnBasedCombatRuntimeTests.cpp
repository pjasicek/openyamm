#include "doctest/doctest.h"

#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/party/Party.h"
#include "tests/PartySpellTestHarness.h"

namespace OpenYAMM::Tests
{
namespace
{
OpenYAMM::Game::Party makeTurnBasedParty(size_t memberCount = 2)
{
    OpenYAMM::Game::PartySeed seed = {};

    for (size_t memberIndex = 0; memberIndex < memberCount; ++memberIndex)
    {
        OpenYAMM::Game::Character member = {};
        member.name = "Member " + std::to_string(memberIndex + 1);
        member.health = 100;
        member.maxHealth = 100;
        seed.members.push_back(member);
    }

    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    return party;
}

OpenYAMM::Game::GameplayRuntimeActorState makeNearbyHostileActor()
{
    OpenYAMM::Game::GameplayRuntimeActorState actor = {};
    actor.monsterId = 1;
    actor.hostileToParty = true;
    actor.preciseX = 128.0f;
    actor.preciseY = 0.0f;
    actor.preciseZ = 0.0f;
    actor.radius = 32;
    return actor;
}
} // namespace

TEST_CASE("turn based runtime enters attack after OE wait and exposes first character action")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty();
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));
    CHECK(runtime.active());
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Wait);
    CHECK(runtime.shouldUpdateActorAi(&party));
    CHECK_FALSE(runtime.canToggleOff(party));

    runtime.update(&party, nullptr, 0.6f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    CHECK(runtime.canBeginPlayerAction(party));
    CHECK_FALSE(runtime.shouldUpdateActorAi(&party));
    CHECK(runtime.canToggleOff(party));

    size_t memberIndex = 99;
    REQUIRE(runtime.frontQueueCharacter(memberIndex));
    CHECK_EQ(memberIndex, 0);
    CHECK_EQ(party.activeMemberIndex(), 0);
}

TEST_CASE("turn based runtime stores player action recovery outside realtime recovery")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));
    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.canBeginPlayerAction(party));

    runtime.storeMemberTurnRecovery(0, 1.0f);
    CHECK(runtime.applyPlayerAction(party, 0, 5.0f));

    const OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    CHECK_EQ(pMember->recoverySecondsRemaining, doctest::Approx(0.0f));
}

TEST_CASE("turn based runtime keeps recovering characters queued until their turn initiative is ready")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->recoverySecondsRemaining = 1.0f;

    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));
    runtime.update(&party, nullptr, 0.6f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    CHECK(runtime.canBeginPlayerAction(party));
    CHECK_EQ(party.activeMemberIndex(), 0);
    CHECK_EQ(pMember->recoverySecondsRemaining, doctest::Approx(0.0f));
}

TEST_CASE("turn based runtime grants a ready actor its attack stage action before a recovering member")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->recoverySecondsRemaining = 1.0f;

    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);
    world.addActor(makeNearbyHostileActor());

    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, &world));
    CHECK(runtime.actorMode() == OpenYAMM::Game::ActorTurnBasedMode::MoveOnly);
    runtime.update(&party, &world, 0.6f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    CHECK(runtime.actorMode() == OpenYAMM::Game::ActorTurnBasedMode::Hold);
    CHECK_EQ(runtime.movementActionPoints(), 0);
    CHECK_FALSE(runtime.canBeginPlayerAction(party));
    CHECK(runtime.shouldUpdateActorAi(&party));
    CHECK_EQ(world.consumeTurnBasedActorActionGrants(), std::vector<size_t>{0});

    runtime.update(&party, &world, 0.016f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    CHECK(runtime.canBeginPlayerAction(party));
    CHECK_FALSE(runtime.shouldUpdateActorAi(&party));
}

TEST_CASE("turn based runtime waits for a granted actor attack to finish")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);
    world.addActor(makeNearbyHostileActor());

    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};
    REQUIRE(runtime.begin(party, &world));
    runtime.update(&party, &world, 0.6f);
    REQUIRE_EQ(world.consumeTurnBasedActorActionGrants(), std::vector<size_t>{0});

    world.setTurnBasedActorActionInProgress(true);
    runtime.update(&party, &world, 0.5f);
    CHECK_FALSE(runtime.canBeginPlayerAction(party));
    CHECK(runtime.shouldUpdateActorAi(&party));

    world.setTurnBasedActorActionInProgress(false);
    runtime.update(&party, &world, 0.016f);
    CHECK(runtime.canBeginPlayerAction(party));
}

TEST_CASE("turn based runtime schedules actors by their own monster recovery")
{
    constexpr float HundredTickRecoverySeconds = 100.0f / 128.0f * 2.133333333333333f;

    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);
    world.setTurnBasedActorRecoveryTicks(90);
    world.addActor(makeNearbyHostileActor());

    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};
    REQUIRE(runtime.begin(party, &world));
    runtime.update(&party, &world, 0.6f);

    // The actor starts at initiative 1, ahead of the ready member at 2.
    REQUIRE_EQ(world.consumeTurnBasedActorActionGrants(), std::vector<size_t>{0});
    runtime.update(&party, &world, 0.016f);
    REQUIRE(runtime.canBeginPlayerAction(party));

    // Member waits 100 ticks, the actor 90: the actor acts again within the first 100-tick turn.
    REQUIRE(runtime.applyPlayerAction(party, 0, HundredTickRecoverySeconds));
    runtime.update(&party, &world, 0.016f);
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    CHECK_EQ(world.consumeTurnBasedActorActionGrants(), std::vector<size_t>{0});

    runtime.update(&party, &world, 0.016f);
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);
    CHECK_FALSE(world.turnBasedActorActionGrantPending());
}

TEST_CASE("turn based runtime carries actor initiative into realtime recovery on exit")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);
    world.setTurnBasedActorRecoveryTicks(90);
    world.addActor(makeNearbyHostileActor());

    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};
    REQUIRE(runtime.begin(party, &world));
    runtime.update(&party, &world, 0.6f);
    REQUIRE_EQ(world.consumeTurnBasedActorActionGrants(), std::vector<size_t>{0});
    runtime.update(&party, &world, 0.016f);
    REQUIRE(runtime.canBeginPlayerAction(party));

    REQUIRE(runtime.toggle(party, &world));
    CHECK_FALSE(runtime.active());
    CHECK(world.turnBasedActorMode() == OpenYAMM::Game::ActorTurnBasedMode::RealTime);

    // 90 recovery ticks less the 1-tick step that readied the member.
    const std::optional<float> cooldownSeconds = world.actorAttackCooldownSeconds(0);
    REQUIRE(cooldownSeconds.has_value());
    CHECK_EQ(*cooldownSeconds, doctest::Approx(89.0f / 128.0f * 2.133333333333333f));
}

TEST_CASE("turn based runtime keeps actor AI live while resolving already-started monster attacks")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    world.bindParty(&party);
    world.setTurnBasedActorActionInProgress(true);

    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, &world));
    runtime.update(&party, &world, 0.6f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Wait);
    CHECK(runtime.shouldUpdateActorAi(&party));
    CHECK_EQ(world.stopTurnBasedActorMovementCount(), 0);

    world.setTurnBasedActorActionInProgress(false);
    runtime.update(&party, &world, 0.016f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    CHECK(runtime.canBeginPlayerAction(party));
    CHECK_EQ(world.stopTurnBasedActorMovementCount(), 1);
}

TEST_CASE("turn based runtime pending actions block player actions until resolved")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));
    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.canBeginPlayerAction(party));

    runtime.registerPendingAction();
    CHECK(runtime.hasPendingActions());
    CHECK_FALSE(runtime.beginPlayerActionOrFinishMovement(party));
    CHECK_FALSE(runtime.applyPlayerAction(party, 0, 1.0f));

    runtime.resolvePendingAction();
    CHECK_FALSE(runtime.hasPendingActions());
    CHECK(runtime.beginPlayerActionOrFinishMovement(party));
}

TEST_CASE("turn based runtime spends the movement budget by walking time while movement is held")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));
    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.canBeginPlayerAction(party));
    CHECK(runtime.applyPlayerAction(party, 0, 5.0f));
    runtime.update(&party, nullptr, 0.016f);
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);
    CHECK_FALSE(runtime.shouldUpdateActorAi(&party));
    CHECK_EQ(runtime.movementActionPoints(), 130);

    OpenYAMM::Game::GameplayInputFrame input = {};
    const auto holdForward = [&input](bool held)
    {
        input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = held;
        input.keyboardHeld[SDL_SCANCODE_W] = held;
    };

    // A held key walks for each frame's time and spends one point per tick.
    holdForward(true);
    CHECK(runtime.noteMovementInput(input, 0.25f));
    CHECK_EQ(runtime.movementActionPoints(), 98);
    CHECK_EQ(runtime.movementDeltaSecondsForFrame(0.25f), doctest::Approx(0.25f));
    CHECK(input.turnBasedMovementStep);

    holdForward(true);
    CHECK(runtime.noteMovementInput(input, 0.25f));
    CHECK_EQ(runtime.movementActionPoints(), 66);

    holdForward(false);
    CHECK_FALSE(runtime.noteMovementInput(input, 0.25f));
    CHECK_EQ(runtime.movementActionPoints(), 66);
    CHECK_EQ(runtime.movementDeltaSecondsForFrame(0.25f), doctest::Approx(0.0f));
    runtime.update(&party, nullptr, 0.016f);
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);

    // The last step is clamped to the remaining budget, then the movement stage ends.
    holdForward(true);
    CHECK(runtime.noteMovementInput(input, 1.0f));
    CHECK_EQ(runtime.movementActionPoints(), 0);
    CHECK_EQ(runtime.movementDeltaSecondsForFrame(1.0f), doctest::Approx(66.0f / 128.0f));

    holdForward(true);
    CHECK_FALSE(runtime.noteMovementInput(input, 0.016f));
    runtime.update(&party, nullptr, 0.016f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Wait);
    CHECK_EQ(runtime.movementActionPoints(), 0);
}

TEST_CASE("turn based runtime lets classic turn keys turn freely in every stage")
{
    using OpenYAMM::Game::KeyboardAction;
    using OpenYAMM::Game::keyboardActionIndex;

    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));
    REQUIRE(runtime.stage() != OpenYAMM::Game::TurnBasedCombatStage::Movement);

    OpenYAMM::Game::GameplayInputFrame input = {};
    input.actions[keyboardActionIndex(KeyboardAction::Left)].held = true;
    input.actions[keyboardActionIndex(KeyboardAction::Forward)].held = true;

    // Outside the movement stage walking is blocked, but turning stays available.
    CHECK_FALSE(runtime.noteMovementInput(input, 0.25f, true));
    CHECK(input.action(KeyboardAction::Left).held);
    CHECK_FALSE(input.action(KeyboardAction::Forward).held);

    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.canBeginPlayerAction(party));
    CHECK(runtime.applyPlayerAction(party, 0, 5.0f));
    runtime.update(&party, nullptr, 0.016f);
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);

    // Turning alone costs no movement points; the A key (Attack in the classic scheme) is not a strafe.
    input = {};
    input.actions[keyboardActionIndex(KeyboardAction::Right)].held = true;
    input.keyboardHeld[SDL_SCANCODE_A] = true;
    CHECK_FALSE(runtime.noteMovementInput(input, 0.25f, true));
    CHECK(input.action(KeyboardAction::Right).held);
    CHECK_EQ(runtime.movementActionPoints(), 130);

    // The modern scheme still treats Left/Right as strafing movement.
    input = {};
    input.actions[keyboardActionIndex(KeyboardAction::Right)].held = true;
    CHECK(runtime.noteMovementInput(input, 0.25f));
    CHECK_EQ(runtime.movementActionPoints(), 98);
}

TEST_CASE("turn based runtime cycles party actions before OE movement phase")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(2);
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));
    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);

    size_t memberIndex = 99;
    REQUIRE(runtime.frontQueueCharacter(memberIndex));
    CHECK_EQ(memberIndex, 0);
    CHECK(runtime.applyPlayerAction(party, 0, 5.0f));
    runtime.update(&party, nullptr, 0.016f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    REQUIRE(runtime.frontQueueCharacter(memberIndex));
    CHECK_EQ(memberIndex, 1);
    CHECK_EQ(party.activeMemberIndex(), 1);

    CHECK(runtime.applyPlayerAction(party, 1, 5.0f));
    runtime.update(&party, nullptr, 0.016f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);
    CHECK_EQ(runtime.movementActionPoints(), 130);
}

TEST_CASE("turn based runtime advances OE game time once when a combat turn reaches movement")
{
    constexpr float ExpectedTurnGameMinutes = 213.0f / 256.0f;

    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));
    CHECK_EQ(runtime.consumePendingGameTimeAdvanceMinutes(), doctest::Approx(0.0f));

    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.canBeginPlayerAction(party));
    CHECK_EQ(runtime.consumePendingGameTimeAdvanceMinutes(), doctest::Approx(0.0f));

    REQUIRE(runtime.applyPlayerAction(party, 0, 5.0f));
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);
    CHECK_EQ(runtime.consumePendingGameTimeAdvanceMinutes(), doctest::Approx(ExpectedTurnGameMinutes));
    CHECK_EQ(runtime.consumePendingGameTimeAdvanceMinutes(), doctest::Approx(0.0f));

    runtime.update(&party, nullptr, 0.5f);
    CHECK_EQ(runtime.consumePendingGameTimeAdvanceMinutes(), doctest::Approx(0.0f));
}

TEST_CASE("turn based runtime adds actors that arrive during combat at the next turn")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);

    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};
    REQUIRE(runtime.begin(party, &world));
    runtime.update(&party, &world, 0.6f);
    REQUIRE(runtime.canBeginPlayerAction(party));
    REQUIRE(runtime.applyPlayerAction(party, 0, 5.0f));
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);

    world.addActor(makeNearbyHostileActor());
    REQUIRE(runtime.finishMovementPhase());
    runtime.update(&party, &world, 0.016f);
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Wait);
    runtime.update(&party, &world, 0.6f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    CHECK_EQ(world.consumeTurnBasedActorActionGrants(), std::vector<size_t>{0});
}

TEST_CASE("turn based runtime blocks movement input until OE movement phase")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));

    OpenYAMM::Game::GameplayInputFrame input = {};
    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = true;
    input.keyboardHeld[SDL_SCANCODE_W] = true;

    CHECK_FALSE(runtime.noteMovementInput(input, 0.016f));
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Wait);

    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = true;
    input.keyboardHeld[SDL_SCANCODE_W] = true;
    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);

    CHECK_FALSE(runtime.noteMovementInput(input, 0.016f));
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    CHECK_EQ(runtime.movementActionPoints(), 0);
    CHECK_FALSE(input.turnBasedMovementStep);
}

TEST_CASE("turn based runtime keeps movement phase open until explicit movement finish")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));
    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.canBeginPlayerAction(party));
    CHECK(runtime.applyPlayerAction(party, 0, 5.0f));
    runtime.update(&party, nullptr, 0.016f);
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);

    CHECK_FALSE(runtime.canBeginPlayerAction(party));
    runtime.update(&party, nullptr, 0.5f);
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);
    CHECK_EQ(runtime.movementActionPoints(), 130);

    CHECK(runtime.finishMovementPhase());
    runtime.update(&party, nullptr, 0.016f);
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Wait);
}

TEST_CASE("turn based pass spends the ready member's action and ends movement")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(2);
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    CHECK_FALSE(runtime.canPassTurn(party));
    REQUIRE(runtime.begin(party, nullptr));
    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);

    CHECK(runtime.canPassTurn(party));
    CHECK(runtime.passTurn(party, 5.0f));
    runtime.update(&party, nullptr, 0.016f);
    CHECK_EQ(party.activeMemberIndex(), 1);

    CHECK(runtime.passTurn(party, 5.0f));
    runtime.update(&party, nullptr, 0.016f);
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);

    CHECK(runtime.canPassTurn(party));
    CHECK(runtime.passTurn(party, 5.0f));
    runtime.update(&party, nullptr, 0.016f);
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Wait);
    CHECK_FALSE(runtime.canPassTurn(party));
}
} // namespace OpenYAMM::Tests
