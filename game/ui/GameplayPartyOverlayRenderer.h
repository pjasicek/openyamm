#pragma once

namespace OpenYAMM::Game
{
class OutdoorGameView;

class GameplayPartyOverlayRenderer
{
public:
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
    static void renderJournalOverlay(const OutdoorGameView &view, int width, int height);
};
} // namespace OpenYAMM::Game
