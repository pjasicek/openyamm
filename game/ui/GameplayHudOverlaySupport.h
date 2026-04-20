#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

class GameplayHudOverlaySupport
{
public:
    static bool tryPopulateItemInspectOverlayFromRenderedHudItems(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool requireOpaqueHitTest);

    static void updateCharacterInspectOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height);

    static void updateBuffInspectOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool showGameplayHud);

    static void updateCharacterDetailOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height);

    static void updateSpellInspectOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height);

    static void renderGameplayMouseLookOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool active);
};
} // namespace OpenYAMM::Game
