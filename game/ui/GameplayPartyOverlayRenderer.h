#pragma once

#include "game/ui/GameplayUiController.h"

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

class GameplayPartyOverlayRenderer
{
public:
    static void renderUtilitySpellOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderCharacterOverlay(GameplayScreenRuntime &context, int width, int height, bool renderAboveHud);
    static void renderHeldInventoryItem(GameplayScreenRuntime &context, int width, int height);
    static void renderItemInspectOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderCharacterInspectOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderBuffInspectOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderCharacterDetailOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderSpellInspectOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderReadableScrollOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderActorInspectOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderSpellbookOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderRestOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderMenuOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderControlsOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderKeyboardOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderVideoOptionsOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderSaveGameOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderLoadGameOverlay(GameplayScreenRuntime &context, int width, int height);
    static void renderJournalOverlay(GameplayScreenRuntime &context, int width, int height);

private:
    static void renderSaveLoadOverlay(
        GameplayScreenRuntime &context,
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
