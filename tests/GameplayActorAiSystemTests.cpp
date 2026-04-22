#include "doctest/doctest.h"

#include "game/gameplay/GameplayActorAiSystem.h"

using OpenYAMM::Game::ActorAiAnimationState;
using OpenYAMM::Game::ActorAiFacts;
using OpenYAMM::Game::ActorAiFrameFacts;
using OpenYAMM::Game::ActorAiFxRequestKind;
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
