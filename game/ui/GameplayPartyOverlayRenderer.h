#pragma once

#include "game/ui/GameplayUiController.h"

namespace OpenYAMM::Game
{
class OutdoorGameView;

class GameplayPartyOverlayRenderer
{
public:
    static void renderUtilitySpellOverlay(const OutdoorGameView &view, int width, int height);
    static void renderCharacterOverlay(const OutdoorGameView &view, int width, int height, bool renderAboveHud);
    static void renderHeldInventoryItem(const OutdoorGameView &view, int width, int height);
    static void renderItemInspectOverlay(const OutdoorGameView &view, int width, int height);
    static void renderCharacterInspectOverlay(const OutdoorGameView &view, int width, int height);
    static void renderBuffInspectOverlay(const OutdoorGameView &view, int width, int height);
    static void renderCharacterDetailOverlay(const OutdoorGameView &view, int width, int height);
    static void renderSpellInspectOverlay(const OutdoorGameView &view, int width, int height);
    static void renderReadableScrollOverlay(const OutdoorGameView &view, int width, int height);
    static void renderActorInspectOverlay(OutdoorGameView &view, int width, int height);
    static void renderSpellbookOverlay(const OutdoorGameView &view, int width, int height);
    static void renderRestOverlay(const OutdoorGameView &view, int width, int height);
    static void renderMenuOverlay(const OutdoorGameView &view, int width, int height);
    static void renderControlsOverlay(const OutdoorGameView &view, int width, int height);
    static void renderKeyboardOverlay(const OutdoorGameView &view, int width, int height);
    static void renderVideoOptionsOverlay(const OutdoorGameView &view, int width, int height);
    static void renderSaveGameOverlay(const OutdoorGameView &view, int width, int height);
    static void renderLoadGameOverlay(const OutdoorGameView &view, int width, int height);
    static void renderJournalOverlay(const OutdoorGameView &view, int width, int height);

private:
    static void renderSaveLoadOverlay(
        const OutdoorGameView &view,
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
        bool renderSelectedDetails);
};
} // namespace OpenYAMM::Game
