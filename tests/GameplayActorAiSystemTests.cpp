#include "doctest/doctest.h"

#include "game/gameplay/GameplayActorAiSystem.h"

#include <cmath>

using OpenYAMM::Game::ActorAiAnimationState;
using OpenYAMM::Game::ActorAiFacts;
using OpenYAMM::Game::ActorAiFrameFacts;
using OpenYAMM::Game::ActorAiFxRequestKind;
using OpenYAMM::Game::ActorAiMovementAction;
using OpenYAMM::Game::ActorAiMotionState;
using OpenYAMM::Game::GameplayActorAiSystem;

namespace
{
ActorAiFacts makeActor(size_t actorIndex, uint32_t actorId)
{
    ActorAiFacts actor = {};
    actor.actorIndex = actorIndex;
    actor.actorId = actorId;
    actor.identity.actorId = actorId;
    actor.stats.currentHp = 10;
    actor.stats.maxHp = 10;
    actor.stats.radius = 32;
    actor.stats.height = 128;
    actor.runtime.motionState = ActorAiMotionState::Standing;
    actor.runtime.animationState = ActorAiAnimationState::Standing;
    actor.movement.position = {100.0f, 200.0f, 0.0f};
    return actor;
}

ActorAiFrameFacts makeFrame()
{
    ActorAiFrameFacts frame = {};
    frame.deltaSeconds = 1.0f / 128.0f;
    frame.fixedStepSeconds = 1.0f / 128.0f;
    frame.party.position = {0.0f, 0.0f, 0.0f};
    frame.party.collisionRadius = 32.0f;
    frame.party.collisionHeight = 128.0f;
    return frame;
}
}

TEST_CASE("shared actor AI marks newly killed active actors dead without outdoor runtime")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(3, 100);
    actor.stats.currentHp = 0;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    CHECK_EQ(update.actorIndex, 3u);
    REQUIRE(update.state.dead.has_value());
    CHECK(*update.state.dead);
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Dead);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Dead);
    REQUIRE_EQ(update.fxRequests.size(), 1u);
    CHECK(update.fxRequests.front().kind == ActorAiFxRequestKind::Death);
}

TEST_CASE("shared actor AI keeps already dead active actors on the dead frame")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(4, 101);
    actor.status.dead = true;
    actor.runtime.motionState = ActorAiMotionState::Dead;
    actor.runtime.animationState = ActorAiAnimationState::Dead;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Dead);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Dead);
    CHECK(update.fxRequests.empty());
}

TEST_CASE("shared actor AI stands briefly when actor movement is crowded after collision")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(6, 103);
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.contactedActorCount = 2;
    actor.movement.meleePursuitActive = true;
    actor.movement.movementBlocked = true;

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Standing);
    REQUIRE(update.state.crowdStandRemainingSeconds.has_value());
    CHECK(*update.state.crowdStandRemainingSeconds > 0.0f);
    CHECK(update.movementIntent.clearVelocity);
}

TEST_CASE("shared actor AI flees briefly after a single hostile actor contact")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(7, 104);
    actor.identity.hostilityType = 4;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.contactedActorCount = 1;
    actor.movement.hasContactedActor = true;
    actor.movement.contactedActorHostilityType = 4;
    actor.movement.contactedActorPosition = {50.0f, 200.0f, 0.0f};

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Fleeing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Walking);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Flee);
    CHECK(update.movementIntent.moveDirectionX > 0.99f);
    CHECK(std::abs(update.movementIntent.moveDirectionY) < 0.01f);
    CHECK(update.movementIntent.clearVelocity);
    REQUIRE(update.state.actionSeconds.has_value());
    CHECK(*update.state.actionSeconds > 0.0f);
}

TEST_CASE("shared actor AI preserves crowd steering instead of overwriting it with contact flee")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(10, 107);
    actor.identity.hostilityType = 4;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.contactedActorCount = 1;
    actor.movement.hasContactedActor = true;
    actor.movement.contactedActorHostilityType = 4;
    actor.movement.contactedActorPosition = {50.0f, 200.0f, 0.0f};
    actor.movement.meleePursuitActive = true;
    actor.movement.allowCrowdSteering = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.target.currentPosition = {300.0f, 200.0f, 0.0f};
    actor.target.currentEdgeDistance = 400.0f;

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Pursuing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Walking);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Pursue);
    const bool hasDesiredMovement =
        update.movementIntent.desiredMoveX != 0.0f || update.movementIntent.desiredMoveY != 0.0f;
    CHECK(hasDesiredMovement);
    CHECK_FALSE(update.movementIntent.clearVelocity);
    REQUIRE(update.state.crowdSideSign.has_value());
    CHECK(*update.state.crowdSideSign != 0);
}

TEST_CASE("shared actor AI scales single hostile contact flee duration by actor move speed")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(9, 106);
    actor.identity.hostilityType = 4;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.movement.contactedActorCount = 1;
    actor.movement.hasContactedActor = true;
    actor.movement.contactedActorHostilityType = 4;
    actor.movement.contactedActorPosition = {-200.0f, 200.0f, 0.0f};

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Fleeing);
    REQUIRE(update.state.actionSeconds.has_value());
    CHECK(*update.state.actionSeconds > 1.4f);
    CHECK(*update.state.actionSeconds < 1.6f);
}

TEST_CASE("shared actor AI faces a single friendly actor contact")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(8, 105);
    actor.identity.hostilityType = 0;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.contactedActorCount = 1;
    actor.movement.hasContactedActor = true;
    actor.movement.contactedActorHostilityType = 0;
    actor.movement.contactedActorPosition = {100.0f, 300.0f, 0.0f};

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Standing);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Stand);
    CHECK(update.movementIntent.updateYaw);
    CHECK(update.movementIntent.clearVelocity);
    REQUIRE(update.state.actionSeconds.has_value());
    CHECK(*update.state.actionSeconds > 0.0f);
}

TEST_CASE("shared actor AI advances dying actors until the final dead frame")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(5, 102);
    actor.stats.currentHp = 0;
    actor.runtime.motionState = ActorAiMotionState::Dying;
    actor.runtime.animationState = ActorAiAnimationState::Dying;
    actor.runtime.actionSeconds = 1.0f / 256.0f;
    actor.runtime.animationTimeTicks = 10.0f;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.dead.has_value());
    CHECK(*update.state.dead);
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Dead);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Dead);
}
