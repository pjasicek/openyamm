#pragma once

#include "game/ui/GameplayUiController.h"

namespace OpenYAMM::Game
{
class GameplayOverlayContext;
class OutdoorGameView;

class GameplayPartyOverlayRenderer
{
public:
    static void renderUtilitySpellOverlay(const OutdoorGameView &view, int width, int height);
    static void renderCharacterOverlay(GameplayOverlayContext &context, int width, int height, bool renderAboveHud);
    static void renderCharacterOverlay(const OutdoorGameView &view, int width, int height, bool renderAboveHud);
    static void renderHeldInventoryItem(GameplayOverlayContext &context, int width, int height);
    static void renderItemInspectOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderCharacterInspectOverlay(const OutdoorGameView &view, int width, int height);
    static void renderBuffInspectOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderCharacterDetailOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderSpellInspectOverlay(const OutdoorGameView &view, int width, int height);
    static void renderReadableScrollOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderActorInspectOverlay(OutdoorGameView &view, int width, int height);
    static void renderSpellbookOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderRestOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderMenuOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderControlsOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderKeyboardOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderVideoOptionsOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderSaveGameOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderLoadGameOverlay(GameplayOverlayContext &context, int width, int height);
    static void renderJournalOverlay(GameplayOverlayContext &context, int width, int height);

private:
    static void renderSaveLoadOverlay(
        GameplayOverlayContext &context,
        int width,
        int height,
        const char *pScreenName,
        const char *pRootId,
        const char *pThumbId,
        const char *pScrollUpId,
        const char *pScrollDownId,
        const char *pPreviewRectId,
        const char *pSelectedNameId,
        const char *pPreviewLine1Id,
        const char *pPreviewLine2Id,
        const char *pRowPrefix,
        const std::vector<GameplayUiController::SaveSlotSummary> &slots,
        size_t scrollOffset,
        size_t selectedIndex,
        bool renderSelectedDetails,
        const GameplayUiController::SaveGameScreenState *pSaveGameScreen);
};
} // namespace OpenYAMM::Game
