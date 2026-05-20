#pragma once

#include "game/scene/OutdoorSceneRuntime.h"

#include <bx/math.h>

#include <optional>

namespace OpenYAMM::Game
{
struct GameplayInputFrame;
class OutdoorGameView;

class OutdoorGameplayInputController
{
public:
    static void updateCameraFromInput(
        OutdoorGameView &view,
        const GameplayInputFrame &input,
        float deltaSeconds);

private:
    static void applyOutdoorFrameAdvanceResult(
        OutdoorGameView &view,
        const OutdoorSceneRuntime::AdvanceFrameResult &result);
    static std::optional<bx::Vec3> resolveArpgModeMoveClick(
        OutdoorGameView &view,
        const GameplayInputFrame &input);
    static void faceArpgModePointerDirection(
        OutdoorGameView &view,
        const GameplayInputFrame &input);
    static bool updateArpgModeOutdoorFrame(
        OutdoorGameView &view,
        const GameplayInputFrame &input,
        float deltaSeconds);
};
} // namespace OpenYAMM::Game
