#pragma once

#include "game/ui/GameplayOverlayTypes.h"

#include <cstddef>

namespace OpenYAMM::Game
{
class GameSession;
class GameplayScreenRuntime;

class GameplayItemService
{
public:
    explicit GameplayItemService(GameSession &session);

    bool tryUseHeldItemOnPartyMember(
        GameplayScreenRuntime &runtime,
        size_t memberIndex,
        bool keepCharacterScreenOpen);

    bool tryUseHeldItemOnInventoryItem(
        GameplayScreenRuntime &runtime,
        size_t memberIndex,
        uint8_t targetGridX,
        uint8_t targetGridY);

    void updateReadableScrollOverlayForHeldItem(
        size_t memberIndex,
        const GameplayCharacterPointerTarget &pointerTarget,
        bool isLeftMousePressed);

    bool identifyInspectedItem(
        const GameplayUiController::ItemInspectOverlayState &overlay,
        std::string &statusText);
    bool tryIdentifyInspectedItem(
        const GameplayUiController::ItemInspectOverlayState &overlay,
        size_t inspectorMemberIndex,
        std::string &statusText);
    bool tryRepairInspectedItem(
        const GameplayUiController::ItemInspectOverlayState &overlay,
        size_t inspectorMemberIndex,
        std::string &statusText);

    void closeReadableScrollOverlay();

private:
    GameSession &m_session;
};
}
