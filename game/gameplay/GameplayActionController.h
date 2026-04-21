#pragma once

#include "game/gameplay/GameplayScreenState.h"

#include <functional>

namespace OpenYAMM::Game
{
class GameplayActionController
{
public:
    enum class QuickCastActionResult
    {
        Failed,
        CastStarted,
        AttackFallback
    };

    struct QuickCastActionConfig
    {
        bool canRunAction = false;
        bool quickCastPressed = false;
        bool hasReadyMember = false;
        std::function<QuickCastActionResult()> beginQuickCast;
    };

    struct AttackActionConfig
    {
        bool attackPressed = false;
        bool hasReadyMember = false;
    };

    struct AttackActionDecision
    {
        bool shouldAttemptAttack = false;
        bool pressedThisFrame = false;
    };

    static constexpr float HeldActionRepeatDebounceSeconds = 0.14f;

    static void updateCooldowns(GameplayScreenState &screenState, float deltaSeconds);
    static void updateQuickCastAction(
        GameplayScreenState::QuickSpellState &quickSpellState,
        const QuickCastActionConfig &config);
    static AttackActionDecision updateAttackAction(
        GameplayScreenState::AttackActionState &attackActionState,
        GameplayScreenState::QuickSpellState &quickSpellState,
        const AttackActionConfig &config);
};
} // namespace OpenYAMM::Game
