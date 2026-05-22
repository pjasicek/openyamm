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

TEST_CASE("turn based runtime does not enter movement just because actors are ready after wait")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    pMember->recoverySecondsRemaining = 1.0f;

    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);

    OpenYAMM::Game::GameplayRuntimeActorState actor = {};
    actor.monsterId = 1;
    actor.hostileToParty = true;
    actor.preciseX = 128.0f;
    actor.preciseY = 0.0f;
    actor.preciseZ = 0.0f;
    actor.radius = 32;
    world.addActor(actor);

    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, &world));
    runtime.update(&party, &world, 0.6f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    CHECK(runtime.canBeginPlayerAction(party));
    CHECK_EQ(runtime.movementActionPoints(), 0);
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

TEST_CASE("turn based runtime spends OE movement actions only while movement is held")
{
    constexpr float MovementStepSeconds = 26.0f / 128.0f;

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
    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = true;
    input.keyboardHeld[SDL_SCANCODE_W] = true;

    CHECK(runtime.noteMovementInput(input));
    CHECK_EQ(runtime.movementActionPoints(), 104);
    CHECK_EQ(runtime.movementDeltaSecondsForFrame(0.016f), doctest::Approx(MovementStepSeconds));
    CHECK(input.turnBasedMovementStep);

    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = true;
    input.keyboardHeld[SDL_SCANCODE_W] = true;
    CHECK(runtime.noteMovementInput(input));
    CHECK_EQ(runtime.movementActionPoints(), 78);
    CHECK_EQ(runtime.movementDeltaSecondsForFrame(0.016f), doctest::Approx(MovementStepSeconds));

    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = false;
    input.keyboardHeld[SDL_SCANCODE_W] = false;
    CHECK_FALSE(runtime.noteMovementInput(input));
    CHECK_EQ(runtime.movementActionPoints(), 78);
    runtime.update(&party, nullptr, 0.016f);
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);

    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = true;
    input.keyboardHeld[SDL_SCANCODE_W] = true;
    CHECK(runtime.noteMovementInput(input));
    CHECK_EQ(runtime.movementActionPoints(), 52);
    CHECK_EQ(runtime.movementDeltaSecondsForFrame(0.016f), doctest::Approx(MovementStepSeconds));

    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = true;
    input.keyboardHeld[SDL_SCANCODE_W] = true;
    CHECK(runtime.noteMovementInput(input));
    CHECK_EQ(runtime.movementActionPoints(), 26);
    CHECK_EQ(runtime.movementDeltaSecondsForFrame(0.016f), doctest::Approx(MovementStepSeconds));

    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = true;
    input.keyboardHeld[SDL_SCANCODE_W] = true;
    CHECK(runtime.noteMovementInput(input));
    CHECK_EQ(runtime.movementActionPoints(), 0);
    CHECK_EQ(runtime.movementDeltaSecondsForFrame(0.016f), doctest::Approx(MovementStepSeconds));

    runtime.update(&party, nullptr, 0.016f);

    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Wait);
    CHECK_EQ(runtime.movementActionPoints(), 0);
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

TEST_CASE("turn based runtime yields to movement when actors become ready before character recovery")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);

    OpenYAMM::Game::GameplayRuntimeActorState actor = {};
    actor.monsterId = 1;
    actor.hostileToParty = true;
    actor.preciseX = 128.0f;
    actor.preciseY = 0.0f;
    actor.preciseZ = 0.0f;
    actor.radius = 32;
    world.addActor(actor);

    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};
    REQUIRE(runtime.begin(party, &world));
    runtime.update(&party, &world, 0.6f);
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);
    REQUIRE(runtime.canBeginPlayerAction(party));

    CHECK(runtime.applyPlayerAction(party, 0, 5.0f));
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Movement);
    CHECK_EQ(runtime.movementActionPoints(), 130);
}

TEST_CASE("turn based runtime blocks movement input until OE movement phase")
{
    OpenYAMM::Game::Party party = makeTurnBasedParty(1);
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};

    REQUIRE(runtime.begin(party, nullptr));

    OpenYAMM::Game::GameplayInputFrame input = {};
    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = true;
    input.keyboardHeld[SDL_SCANCODE_W] = true;

    CHECK_FALSE(runtime.noteMovementInput(input));
    CHECK(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Wait);

    input.actions[OpenYAMM::Game::keyboardActionIndex(OpenYAMM::Game::KeyboardAction::Forward)].held = true;
    input.keyboardHeld[SDL_SCANCODE_W] = true;
    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.stage() == OpenYAMM::Game::TurnBasedCombatStage::Attack);

    CHECK_FALSE(runtime.noteMovementInput(input));
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
} // namespace OpenYAMM::Tests
