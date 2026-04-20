#include "game/gameplay/GameplayScreenHotkeyController.h"

#include "game/ui/GameplayOverlayContext.h"

namespace OpenYAMM::Game
{
namespace
{
bool isActionNewlyPressed(GameplayOverlayContext &context, KeyboardAction action, const bool *pKeyboardState)
{
    if (pKeyboardState == nullptr)
    {
        return false;
    }

    const SDL_Scancode scancode = context.mutableSettings().keyboard.binding(action);

    if (scancode <= SDL_SCANCODE_UNKNOWN || scancode >= SDL_SCANCODE_COUNT)
    {
        return false;
    }

    return pKeyboardState[scancode] && context.previousKeyboardState()[scancode] == 0;
}
}

void GameplayScreenHotkeyController::handleGameplayScreenHotkeys(
    GameplayOverlayContext &context,
    const bool *pKeyboardState,
    const GameplayScreenHotkeyConfig &config)
{
    if (isActionNewlyPressed(context, KeyboardAction::Cast, pKeyboardState))
    {
        if (context.spellbookReadOnly().active)
        {
            context.closeSpellbookOverlay();
        }
        else if (config.canToggleSpellbook)
        {
            context.openSpellbookOverlay();
        }
    }

    if (isActionNewlyPressed(context, KeyboardAction::Quest, pKeyboardState) && config.canToggleInventory)
    {
        if (config.hasActiveLootView)
        {
            if (context.inventoryNestedOverlay().active)
            {
                context.closeInventoryNestedOverlay();
            }
            else
            {
                context.openChestTransferInventoryOverlay();
            }
        }
        else
        {
            context.toggleCharacterInventoryScreen();
        }
    }

    if (!config.canCyclePartyMember || !isActionNewlyPressed(context, KeyboardAction::CharCycle, pKeyboardState))
    {
        return;
    }

    Party *pParty = context.party();

    if (pParty == nullptr || pParty->members().empty())
    {
        return;
    }

    const size_t nextMemberIndex = (pParty->activeMemberIndex() + 1) % pParty->members().size();
    context.trySelectPartyMember(nextMemberIndex, config.requireGameplayReadyForPartySelection);
}
} // namespace OpenYAMM::Game
