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

    static void updateCharacterInspectOverlay(
        GameplayOverlayContext &context,
        int width,
        int height);

    static void updateBuffInspectOverlay(
        GameplayOverlayContext &context,
        int width,
        int height,
        bool showGameplayHud);

    static void updateCharacterDetailOverlay(
        GameplayOverlayContext &context,
        int width,
        int height);

    static void updateSpellInspectOverlay(
        GameplayOverlayContext &context,
        int width,
        int height);

    static void renderGameplayMouseLookOverlay(
        GameplayOverlayContext &context,
        int width,
        int height,
        bool active);
};
} // namespace OpenYAMM::Game
