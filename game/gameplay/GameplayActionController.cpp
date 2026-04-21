#include "game/gameplay/GameplayActionController.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
void resetQuickCastRepeatState(GameplayScreenState::QuickSpellState &quickSpellState)
{
    quickSpellState.castRepeatCooldownSeconds = 0.0f;
    quickSpellState.castLatch = false;
    quickSpellState.readyMemberAvailableWhileHeld = false;
}
} // namespace

void GameplayActionController::updateCooldowns(GameplayScreenState &screenState, float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    GameplayScreenState::AttackActionState &attackActionState = screenState.attackActionState();
    GameplayScreenState::QuickSpellState &quickSpellState = screenState.quickSpellState();

    attackActionState.inspectRepeatCooldownSeconds =
        std::max(0.0f, attackActionState.inspectRepeatCooldownSeconds - deltaSeconds);
    quickSpellState.castRepeatCooldownSeconds =
        std::max(0.0f, quickSpellState.castRepeatCooldownSeconds - deltaSeconds);
}

void GameplayActionController::updateQuickCastAction(
    GameplayScreenState::QuickSpellState &quickSpellState,
    const QuickCastActionConfig &config)
{
    if (!config.canRunAction)
    {
        resetQuickCastRepeatState(quickSpellState);
        return;
    }

    bool readyMemberTransitionWhileHeld = false;

    if (config.quickCastPressed)
    {
        readyMemberTransitionWhileHeld =
            !quickSpellState.readyMemberAvailableWhileHeld && config.hasReadyMember;
        quickSpellState.readyMemberAvailableWhileHeld = config.hasReadyMember;
    }
    else
    {
        quickSpellState.readyMemberAvailableWhileHeld = false;
    }

    const bool pressedThisFrame = config.quickCastPressed && !quickSpellState.castLatch;
    const bool repeatReady =
        config.quickCastPressed
        && quickSpellState.castLatch
        && (quickSpellState.castRepeatCooldownSeconds <= 0.0f || readyMemberTransitionWhileHeld);

    if (pressedThisFrame || repeatReady)
    {
        const QuickCastActionResult result =
            config.beginQuickCast ? config.beginQuickCast() : QuickCastActionResult::Failed;
        quickSpellState.attackFallbackRequested = result == QuickCastActionResult::AttackFallback;
        quickSpellState.castLatch = true;
        quickSpellState.castRepeatCooldownSeconds = HeldActionRepeatDebounceSeconds;
        return;
    }

    if (!config.quickCastPressed)
    {
        resetQuickCastRepeatState(quickSpellState);
    }
}

GameplayActionController::AttackActionDecision GameplayActionController::updateAttackAction(
    GameplayScreenState::AttackActionState &attackActionState,
    GameplayScreenState::QuickSpellState &quickSpellState,
    const AttackActionConfig &config)
{
    const bool attackTriggeredByQuickCastFallback = quickSpellState.attackFallbackRequested;
    bool readyMemberTransitionWhileHeld = false;

    if (config.attackPressed)
    {
        readyMemberTransitionWhileHeld =
            !attackActionState.readyMemberAvailableWhileHeld && config.hasReadyMember;
        attackActionState.readyMemberAvailableWhileHeld = config.hasReadyMember;
    }
    else
    {
        attackActionState.readyMemberAvailableWhileHeld = false;
    }

    const bool pressedThisFrame =
        (config.attackPressed || attackTriggeredByQuickCastFallback) && !attackActionState.inspectLatch;
    const bool repeatReady =
        (config.attackPressed || attackTriggeredByQuickCastFallback)
        && attackActionState.inspectLatch
        && (attackActionState.inspectRepeatCooldownSeconds <= 0.0f || readyMemberTransitionWhileHeld);

    quickSpellState.attackFallbackRequested = false;

    if (pressedThisFrame || repeatReady)
    {
        attackActionState.inspectLatch = true;
        attackActionState.inspectRepeatCooldownSeconds = HeldActionRepeatDebounceSeconds;

        return AttackActionDecision{
            .shouldAttemptAttack = true,
            .pressedThisFrame = pressedThisFrame,
        };
    }

    if (!config.attackPressed)
    {
        attackActionState.clear();
    }

    return {};
}
} // namespace OpenYAMM::Game
