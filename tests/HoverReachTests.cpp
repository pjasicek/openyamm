#include "game/gameplay/GameplayInteractionController.h"

#include <doctest/doctest.h>

using namespace OpenYAMM::Game;

namespace
{
GameplayHoverStatusPayload eventTargetHover(GameplayWorldEventTargetKind kind, float distance, uint16_t nameEventId)
{
    GameplayHoverStatusPayload payload = {};
    payload.worldHit.hasHit = true;
    payload.worldHit.kind = GameplayWorldHitKind::EventTarget;
    GameplayEventTargetHit target = {};
    target.targetKind = kind;
    target.distance = distance;
    target.nameEventId = nameEventId;
    payload.worldHit.eventTarget = target;
    payload.eventTargetStatusText = "Great nest";
    return payload;
}
}

// D-153 (F65, XD-26's nest): a usable face, decoration or mechanism is named only within the click's reach, so a
// name never shows where the click does nothing. Decorations without an event keep their name at any distance.
TEST_CASE("a usable target's hover name shows only within the interaction depth")
{
    using Controller = GameplayInteractionController;
    const float depth = 512.0f;

    for (const GameplayWorldEventTargetKind kind : {GameplayWorldEventTargetKind::Surface,
             GameplayWorldEventTargetKind::Entity, GameplayWorldEventTargetKind::Decoration,
             GameplayWorldEventTargetKind::Mechanism})
    {
        CAPTURE(static_cast<int>(kind));
        CHECK(Controller::resolveHoverStatusText(eventTargetHover(kind, 400.0f, 9), false, depth).has_value());
        CHECK_FALSE(Controller::resolveHoverStatusText(eventTargetHover(kind, 600.0f, 9), false, depth).has_value());
        // A larger configured depth reaches further.
        CHECK(Controller::resolveHoverStatusText(eventTargetHover(kind, 600.0f, 9), false, 1024.0f).has_value());
    }
}

TEST_CASE("a decoration without an event keeps its hover name beyond the interaction depth")
{
    using Controller = GameplayInteractionController;

    for (const GameplayWorldEventTargetKind kind :
             {GameplayWorldEventTargetKind::Entity, GameplayWorldEventTargetKind::Decoration})
    {
        CAPTURE(static_cast<int>(kind));
        CHECK(Controller::resolveHoverStatusText(eventTargetHover(kind, 400.0f, 0), false, 512.0f).has_value());
        CHECK(Controller::resolveHoverStatusText(eventTargetHover(kind, 600.0f, 0), false, 512.0f).has_value());
        CHECK(Controller::resolveHoverStatusText(eventTargetHover(kind, 3000.0f, 0), false, 512.0f).has_value());
    }
}
