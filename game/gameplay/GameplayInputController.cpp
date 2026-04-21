#include "game/gameplay/GameplayInputController.h"

#include "game/gameplay/GameplayScreenRuntime.h"

#include <SDL3/SDL.h>

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

bool isEscapeNewlyPressed(GameplayScreenRuntime &context, const bool *pKeyboardState)
{
    return pKeyboardState != nullptr
        && pKeyboardState[SDL_SCANCODE_ESCAPE]
        && context.previousKeyboardState()[SDL_SCANCODE_ESCAPE] == 0;
}
} // namespace

void GameplayInputController::handleStandardUiHotkeys(
    GameplayScreenRuntime &context,
    const GameplayStandardUiHotkeyConfig &config)
{
    IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
    const bool activeEventDialog = context.activeEventDialog().isActive;
    const bool characterScreenOpen = context.characterScreenReadOnly().open;
    const bool spellbookActive = context.spellbookReadOnly().active;
    const bool restActive = context.restScreenState().active;
    const bool menuActive = context.menuScreenState().active;
    const bool controlsActive = context.controlsScreenState().active;
    const bool keyboardActive = context.keyboardScreenState().active;
    const bool videoOptionsActive = context.videoOptionsScreenState().active;
    const bool saveGameActive = context.saveGameScreenState().active;
    const bool loadGameActive = context.loadGameScreenState().active;
    const bool journalActive = context.journalScreenState().active;
    const bool houseShopActive = context.houseShopOverlay().active;
    const bool houseBankInputActive = context.houseBankState().inputActive();

    if (isEscapeNewlyPressed(context, config.pKeyboardState))
    {
        if (spellbookActive)
        {
            context.closeSpellbookOverlay();
            context.interactionState().menuToggleLatch = true;
            return;
        }

        if (characterScreenOpen)
        {
            context.characterScreen().open = false;
            context.characterScreen().dollJewelryOverlayOpen = false;
            context.characterScreen().adventurersInnRosterOverlayOpen = false;
            context.interactionState().menuToggleLatch = true;
            return;
        }

        if (activeEventDialog || houseShopActive || houseBankInputActive)
        {
            context.handleDialogueCloseRequest();
            context.interactionState().menuToggleLatch = true;
            return;
        }
    }

    const bool canToggleMenu =
        !activeEventDialog
        && !hasActiveLootView
        && !characterScreenOpen
        && !spellbookActive
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !context.inventoryNestedOverlay().active
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockMenuToggle;

    if (config.pKeyboardState != nullptr)
    {
        const bool escapePressed = config.pKeyboardState[SDL_SCANCODE_ESCAPE];

        if (canToggleMenu)
        {
            if (escapePressed)
            {
                if (!context.interactionState().menuToggleLatch)
                {
                    context.openMenuOverlay();
                    context.interactionState().menuToggleLatch = true;
                }
            }
            else
            {
                context.interactionState().menuToggleLatch = false;
            }
        }

        if (config.canOpenRest)
        {
            if (context.mutableSettings().keyboard.isPressed(KeyboardAction::Rest, config.pKeyboardState))
            {
                if (!context.interactionState().restToggleLatch)
                {
                    context.openRestOverlay();
                    context.interactionState().restToggleLatch = true;
                }
            }
            else
            {
                context.interactionState().restToggleLatch = false;
            }
        }
        else
        {
            context.interactionState().restToggleLatch = false;
        }
    }
    else
    {
        context.interactionState().menuToggleLatch = false;
        context.interactionState().restToggleLatch = false;
    }

    const bool canToggleSpellbook =
        !activeEventDialog
        && !characterScreenOpen
        && !hasActiveLootView
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockSpellbookToggle;

    if (isActionNewlyPressed(context, KeyboardAction::Cast, config.pKeyboardState))
    {
        if (context.spellbookReadOnly().active)
        {
            context.closeSpellbookOverlay();
        }
        else if (canToggleSpellbook)
        {
            context.openSpellbookOverlay();
        }
    }

    const bool canToggleInventory =
        !activeEventDialog
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !config.blockInventoryToggle;

    if (isActionNewlyPressed(context, KeyboardAction::Quest, config.pKeyboardState) && canToggleInventory)
    {
        if (hasActiveLootView)
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

    const bool canCyclePartyMember =
        !spellbookActive
        && !restActive
        && !menuActive
        && !controlsActive
        && !keyboardActive
        && !videoOptionsActive
        && !saveGameActive
        && !loadGameActive
        && !journalActive
        && !houseBankInputActive
        && !config.blockPartyCycle;

    if (!canCyclePartyMember || !isActionNewlyPressed(context, KeyboardAction::CharCycle, config.pKeyboardState))
    {
        return;
    }

    Party *pParty = context.party();

    if (pParty == nullptr || pParty->members().empty())
    {
        return;
    }

    const size_t nextMemberIndex = (pParty->activeMemberIndex() + 1) % pParty->members().size();
    const bool requireGameplayReady =
        config.requireGameplayReadyForPartySelection
        && !activeEventDialog
        && !hasActiveLootView
        && !houseShopActive;
    context.trySelectPartyMember(nextMemberIndex, requireGameplayReady);
}
} // namespace OpenYAMM::Game
