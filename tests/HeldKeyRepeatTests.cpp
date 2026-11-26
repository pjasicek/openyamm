#include "doctest/doctest.h"

#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameplayScreenState.h"

#include <optional>
#include <set>
#include <vector>

// The held Attack and Quick Cast keys' repeat (GameplayActionController) with the fast lane for a member whose recovery
// is shorter than the repeat (the user, 2026-11-26; DECISIONS H-91): every other member keeps the repeat. In the
// runtime tests because GameplayActionController lives in openyamm_game.
namespace
{
using namespace OpenYAMM::Game;

// What a held key did on one frame (GameplayActionController's held-key repeat).
struct HeldAction
{
    int frame = 0;
    std::optional<size_t> quickRecoveryMember;
    float cooldownBefore = 0.0f;
    float cooldownAfter = 0.0f;
};

// An exact binary fraction, so the repeat's frames do not depend on rounding: the first repeat (0.5 s) lands on frame
// 32, each later one (0.14 s) nine frames on.
constexpr float FrameSeconds = 1.0f / 64.0f;
const std::vector<int> PlainRepeatFrames = {0, 32, 41, 50, 59};

// Holds Attack (or Quick Cast) for frameCount frames; on quickFrames a quick member (index 1) is offered.
std::vector<HeldAction> holdKey(bool quickCast, int frameCount, bool turnBased, const std::set<int> &quickFrames)
{
    GameplayScreenState screen;
    std::vector<HeldAction> actions;

    for (int frame = 0; frame < frameCount; ++frame)
    {
        if (frame > 0)
        {
            GameplayActionController::updateCooldowns(screen, FrameSeconds);
        }

        const std::optional<size_t> quick =
            quickFrames.contains(frame) ? std::optional<size_t>(1) : std::nullopt;
        HeldAction action = {};
        action.frame = frame;
        bool acted = false;

        if (quickCast)
        {
            GameplayActionController::QuickCastActionConfig config = {};
            config.canRunAction = true;
            config.quickCastPressed = true;
            config.hasReadyMember = true;
            config.turnBased = turnBased;
            config.quickRecoveryMember = quick;
            action.cooldownBefore = screen.quickSpellState().castRepeatCooldownSeconds;
            const GameplayActionController::QuickCastActionDecision decision =
                GameplayActionController::updateQuickCastAction(screen.quickSpellState(), config);
            action.cooldownAfter = screen.quickSpellState().castRepeatCooldownSeconds;
            acted = decision.shouldBeginQuickCast;
            action.quickRecoveryMember = decision.quickRecoveryMember;
        }
        else
        {
            GameplayActionController::AttackActionConfig config = {};
            config.attackPressed = true;
            config.hasReadyMember = true;
            config.turnBased = turnBased;
            config.quickRecoveryMember = quick;
            action.cooldownBefore = screen.attackActionState().inspectRepeatCooldownSeconds;
            const GameplayActionController::AttackActionDecision decision =
                GameplayActionController::updateAttackAction(
                    screen.attackActionState(), screen.quickSpellState(), config);
            action.cooldownAfter = screen.attackActionState().inspectRepeatCooldownSeconds;
            acted = decision.shouldAttemptAttack;
            action.quickRecoveryMember = decision.quickRecoveryMember;

            if (acted)
            {
                CHECK_EQ(decision.pressedThisFrame, frame == 0);
            }
        }

        if (acted)
        {
            actions.push_back(action);
        }
    }

    return actions;
}

std::vector<int> actionFrames(const std::vector<HeldAction> &actions)
{
    std::vector<int> frames;

    for (const HeldAction &action : actions)
    {
        frames.push_back(action.frame);
    }

    return frames;
}
}

TEST_CASE("held key: a quick member's quick member acts between the repeats in real time only")
{
    REQUIRE_EQ(GameplayActionController::HeldActionFirstRepeatDelaySeconds, doctest::Approx(32 * FrameSeconds));

    for (const bool quickCast : {false, true})
    {
        CAPTURE(quickCast);

        // Nobody quick: the repeat is unchanged (first after 0.5 s, then every 0.14 s).
        const std::vector<HeldAction> plain = holdKey(quickCast, 64, false, {});
        CHECK_EQ(actionFrames(plain), PlainRepeatFrames);

        for (const HeldAction &action : plain)
        {
            CHECK_FALSE(action.quickRecoveryMember.has_value());
        }

        // A quick member while the key repeats: it acts on that frame, the repeat stays where it was. During the
        // first-repeat pause (frame 10) it waits, so a tap still acts once.
        const std::vector<HeldAction> quick = holdKey(quickCast, 64, false, {10, 36, 37});
        CHECK_EQ(actionFrames(quick), std::vector<int>{0, 32, 36, 37, 41, 50, 59});

        for (const HeldAction &action : quick)
        {
            CAPTURE(action.frame);
            const bool quickFrame = action.frame == 36 || action.frame == 37;
            CHECK_EQ(action.quickRecoveryMember.has_value(), quickFrame);

            if (quickFrame)
            {
                CHECK_EQ(*action.quickRecoveryMember, 1u);
                CHECK_EQ(action.cooldownAfter, doctest::Approx(action.cooldownBefore));
                CHECK_GT(action.cooldownAfter, 0.0f);
            }
        }

        // Turn-based: never.
        std::set<int> everyFrame;

        for (int frame = 0; frame < 64; ++frame)
        {
            everyFrame.insert(frame);
        }

        const std::vector<HeldAction> turnBased = holdKey(quickCast, 64, true, everyFrame);
        CHECK_EQ(actionFrames(turnBased), PlainRepeatFrames);

        for (const HeldAction &action : turnBased)
        {
            CHECK_FALSE(action.quickRecoveryMember.has_value());
        }
    }
}
