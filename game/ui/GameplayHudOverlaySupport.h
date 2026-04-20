#pragma once

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

class GameplayHudOverlaySupport
{
public:
    static bool tryPopulateItemInspectOverlayFromRenderedHudItems(
        GameplayOverlayContext &context,
        int width,
        int height,
        bool requireOpaqueHitTest);

    static void renderGameplayMouseLookOverlay(
        GameplayOverlayContext &context,
        int width,
        int height,
        bool active);
};
} // namespace OpenYAMM::Game
