#include "game/gameplay/GameplayScreenHotkeyController.h"

#include "game/gameplay/GameplayScreenRuntime.h"

namespace OpenYAMM::Game
{
namespace
{
bool isActionNewlyPressed(GameplayScreenRuntime &context, KeyboardAction action, const bool *pKeyboardState)
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
    GameplayScreenRuntime &context,
    const bool *pKeyboardState,
    const GameplayScreenHotkeyConfig &config)
{
    if (pKeyboardState != nullptr)
    {
        const bool escapePressed = pKeyboardState[SDL_SCANCODE_ESCAPE];

        if (config.canToggleMenu)
        {
            if (escapePressed)
            {
                if (!context.menuToggleLatch())
                {
                    context.openMenuOverlay();
                    context.menuToggleLatch() = true;
                }
            }
            else
            {
                context.menuToggleLatch() = false;
            }
        }

        if (config.canOpenRest)
        {
            if (context.mutableSettings().keyboard.isPressed(KeyboardAction::Rest, pKeyboardState))
            {
                if (!context.restToggleLatch())
                {
                    context.openRestOverlay();
                    context.restToggleLatch() = true;
                }
            }
            else
            {
                context.restToggleLatch() = false;
            }
        }
        else
        {
            context.restToggleLatch() = false;
        }
    }
    else
    {
        context.menuToggleLatch() = false;
        context.restToggleLatch() = false;
    }

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
