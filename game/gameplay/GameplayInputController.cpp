#include "game/gameplay/GameplayInputController.h"
#include "game/ui/GameplaySoloTalentsPage.h"
#include "engine/Localization.h"
#include "game/ui/GameplayBattleOrders.h"
#include "game/ui/GameplayFormationBuilder.h"
#include "game/ui/GameplaySoloBarSelector.h"
#include "game/ui/GameplayLootSummaryRenderer.h"

#include "game/audio/SoundIds.h"
#include "game/gameplay/GameplayActionController.h"
#include "game/app/GameSettings.h"
#include "game/gameplay/GameplayHudInputController.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/gameplay/GameplayScreenController.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/party/Party.h"
#include "game/party/SpeechIds.h"
#include "game/tables/SpellTable.h"
#include "game/ui/GameplayQuickItems.h"
#include "game/ui/GameplaySoloHud.h"

#include <SDL3/SDL.h>

#include <array>
#include <optional>

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

    const SDL_Scancode scancode = context.mutableSettings().keyboard.keyboardBinding(action);

    if (scancode <= SDL_SCANCODE_UNKNOWN || scancode >= SDL_SCANCODE_COUNT)
    {
        return false;
    }

    return pKeyboardState[scancode] && context.previousKeyboardState()[scancode] == 0;
}

bool isActionNewlyPressed(
    GameplayScreenRuntime &context,
    KeyboardAction action,
    const GameplayInputFrame *pInputFrame,
    const bool *pKeyboardState)
{
    if (pInputFrame != nullptr)
    {
        return pInputFrame->action(action).pressed;
    }

    return isActionNewlyPressed(context, action, pKeyboardState);
}

bool isActionHeld(
    GameplayScreenRuntime &context,
    KeyboardAction action,
    const GameplayInputFrame *pInputFrame,
    const bool *pKeyboardState)
{
    if (pInputFrame != nullptr)
    {
        return pInputFrame->action(action).held;
    }

    return context.mutableSettings().keyboard.isPressed(action, pKeyboardState);
}

bool isScancodeHeld(
    SDL_Scancode scancode,
    const GameplayInputFrame *pInputFrame,
    const bool *pKeyboardState)
{
    if (pInputFrame != nullptr)
    {
        return pInputFrame->isScancodeHeld(scancode);
    }

    return pKeyboardState != nullptr
        && scancode > SDL_SCANCODE_UNKNOWN
        && scancode < SDL_SCANCODE_COUNT
        && pKeyboardState[scancode];
}

bool isEscapeNewlyPressed(GameplayScreenRuntime &context, const bool *pKeyboardState)
{
    return pKeyboardState != nullptr
        && pKeyboardState[SDL_SCANCODE_ESCAPE]
        && context.previousKeyboardState()[SDL_SCANCODE_ESCAPE] == 0;
}

bool closeActiveLootViewFromEscape(GameplayScreenRuntime &context, IGameplayWorldRuntime &worldRuntime)
{
    if (worldRuntime.activeChestView() == nullptr && worldRuntime.activeCorpseView() == nullptr)
    {
        return false;
    }

    if (context.inventoryNestedOverlay().active)
    {
        context.closeInventoryNestedOverlay();
    }
    else
    {
        worldRuntime.closeActiveChestView();
        worldRuntime.closeActiveCorpseView();
        context.interactionState().activateInspectLatch = true;
        context.interactionState().chestSelectionIndex = 0;
    }

    context.interactionState().menuToggleLatch = true;
    context.interactionState().closeOverlayLatch = true;
    return true;
}

std::optional<size_t> nextSelectableMemberIndex(const Party &party, bool requireGameplayReady)
{
    const size_t memberCount = party.members().size();

    for (size_t offset = 1; offset <= memberCount; ++offset)
    {
        const size_t memberIndex = (party.activeMemberIndex() + offset) % memberCount;

        if (!requireGameplayReady || party.canSelectMemberInGameplay(memberIndex))
        {
            return memberIndex;
        }
    }

    return std::nullopt;
}

GameplaySpellActionController::TargetQueries buildSpellActionTargetQueries(
    const GameplayScreenState &screenState,
    const GameplaySharedInputFrameConfig &config)
{
    const GameplayScreenState::GameplayMouseLookState &mouseLookState = screenState.gameplayMouseLookState();

    GameplaySpellActionController::TargetQueries targetQueries = {};
    targetQueries.useCrosshairTarget =
        mouseLookState.mouseLookActive
        && !mouseLookState.cursorModeActive
        && config.screenWidth > 0
        && config.screenHeight > 0;
    targetQueries.cursorX = config.pointerX;
    targetQueries.cursorY = config.pointerY;
    targetQueries.screenWidth = static_cast<float>(config.screenWidth);
    targetQueries.screenHeight = static_cast<float>(config.screenHeight);
    return targetQueries;
}
} // namespace

bool GameplayInputController::updateAutoWalk(bool active, const GameplayAutoWalkInput &input)
{
    if (!input.canWalk || input.turnBased || input.forwardPressed || input.backwardPressed)
    {
        return false;
    }

    return input.togglePressed ? !active : active;
}

GameplayMouseLookPolicyResult GameplayInputController::updateGameplayMouseLookPolicy(
    GameplayScreenState::GameplayMouseLookState &state,
    const GameplayMouseLookPolicyConfig &config)
{
    const bool cursorModeActive = config.mouseLookAllowed && config.rightMousePressed;
    const bool mouseLookActive = config.mouseLookAllowed && !cursorModeActive;

    state.cursorModeActive = cursorModeActive;
    state.mouseLookActive = mouseLookActive;

    GameplayMouseLookPolicyResult result = {};
    result.cursorModeActive = cursorModeActive;
    result.mouseLookActive = mouseLookActive;
    result.allowGameplayPointerInput = !config.mouseLookAllowed || cursorModeActive;
    return result;
}

void GameplayInputController::handleStandardUiHotkeys(
    GameplayScreenRuntime &context,
    const GameplayStandardUiHotkeyConfig &config)
{
    // Letters typed into the alchemy bench, inventory, journal, Battle Orders or solo bar selector search are text, not
    // hotkeys; each handles Escape itself.
    if (GameplayUiController::characterScreenSearchActive(context.characterScreenReadOnly())
        || GameplayUiController::journalSearchActive(context.journalScreenStateReadOnly())
        || GameplayUiController::spellbookSearchActive(context.spellbookReadOnly())
        || GameplaySoloBarSelector::isOpen(context))
    {
        return;
    }

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
    const bool quickReferenceActive = context.quickReferenceScreenState().active;
    const bool houseShopActive = context.houseShopOverlay().active;
    const bool houseBankInputActive = context.houseBankState().inputActive();
    const bool gameplayHudActive = context.currentHudScreenState() == GameplayHudScreenState::Gameplay;
    const bool formationBuilderOpen = GameplayFormationBuilder::isOpen(context);
    // Play with nothing open: the rest key and MAW's play keys act.
    const bool gameplayIdle =
        gameplayHudActive
        && !activeEventDialog
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
        && !quickReferenceActive
        && !context.inventoryNestedOverlay().active
        && !context.readableScrollOverlayReadOnly().active
        && !context.lootSummaryOverlayReadOnly().active
        && !formationBuilderOpen
        && !GameplaySoloBarSelector::armed(context)
        && !context.utilitySpellOverlayReadOnly().active
        && !houseShopActive
        && !houseBankInputActive;
    const bool canOpenRestFromGameplay = config.canOpenRest && gameplayIdle;

    if (isEscapeNewlyPressed(context, config.pKeyboardState))
    {
        if (pWorldRuntime != nullptr && closeActiveLootViewFromEscape(context, *pWorldRuntime))
        {
            return;
        }

        if (context.readableScrollOverlayReadOnly().active)
        {
            context.itemService().closeReadableScrollOverlay();
            context.interactionState().menuToggleLatch = true;
            return;
        }

        if (context.lootSummaryOverlayReadOnly().active)
        {
            GameplayLootSummaryRenderer::close(context);
            context.interactionState().menuToggleLatch = true;
            return;
        }

        // Escape keeps the old formation, as Cancel.
        if (formationBuilderOpen)
        {
            GameplayFormationBuilder::close(context);
            context.interactionState().menuToggleLatch = true;
            return;
        }

        if (spellbookActive)
        {
            // The Battle Orders window and the spell menu take their own Escape (the spellbook's input).
            if (!GameplayBattleOrders::isOpen(context) && !GameplayBattleOrders::spellMenuOpen(context))
            {
                context.closeSpellbookOverlay();
            }

            context.interactionState().menuToggleLatch = true;
            return;
        }

        if (quickReferenceActive)
        {
            context.closeQuickReferenceOverlay();
            context.interactionState().menuToggleLatch = true;
            return;
        }

        // An open alchemy bench, an inventory item search (cleared by it) and a solo run's Talents page (back to the
        // Skills page) take this Escape themselves and leave the character screen open.
        const GameplayUiController::CharacterScreenState &characterScreen = context.characterScreenReadOnly();

        if (characterScreenOpen && !characterScreen.alchemyBench.active
            && !(characterScreen.page == GameplayUiController::CharacterPage::Inventory
                && !characterScreen.inventorySearch.empty())
            && !GameplaySoloTalentsPage::pageShown(context))
        {
            context.closeCharacterScreen();
            context.interactionState().menuToggleLatch = true;
            return;
        }

        if (activeEventDialog || houseShopActive || houseBankInputActive)
        {
            context.handleDialogueCloseRequest();
            context.interactionState().menuToggleLatch = true;
            context.interactionState().closeOverlayLatch = true;
            return;
        }
    }

    // Escape closes the quick item popup or ring first (GameplayQuickItems).
    const bool canToggleMenu =
        !activeEventDialog
        && !GameplayQuickItems::needsCursor(context)
        && !formationBuilderOpen
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
        && !quickReferenceActive
        && !context.inventoryNestedOverlay().active
        && !houseShopActive
        && !houseBankInputActive
        && !config.blockMenuToggle;

    if (config.pKeyboardState != nullptr)
    {
        const bool escapePressed = config.pKeyboardState[SDL_SCANCODE_ESCAPE];
        const bool turnBasedActive = context.turnBasedCombatRuntime().active();

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

        if (canOpenRestFromGameplay && turnBasedActive)
        {
            if (isActionHeld(context, KeyboardAction::Rest, config.pInputFrame, config.pKeyboardState))
            {
                if (!context.interactionState().restToggleLatch)
                {
                    context.setStatusBarEvent(Engine::tr("You can't rest in turn-based mode!"));
                    context.playCantRestHereReaction();
                    context.interactionState().restToggleLatch = true;
                }
            }
            else
            {
                context.interactionState().restToggleLatch = false;
            }
        }
        else if (canOpenRestFromGameplay)
        {
            if (isActionHeld(context, KeyboardAction::Rest, config.pInputFrame, config.pKeyboardState))
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
        && !quickReferenceActive
        && !houseShopActive
        && !houseBankInputActive
        && !formationBuilderOpen
        && !config.blockSpellbookToggle;

    // The Battle Orders key opens the window over the book (the book with it), and closes it again.
    if (isActionNewlyPressed(context, KeyboardAction::BattleOrders, config.pInputFrame, config.pKeyboardState))
    {
        if (GameplayBattleOrders::isOpen(context))
        {
            GameplayBattleOrders::close(context);
        }
        else if (context.spellbookReadOnly().active)
        {
            GameplayBattleOrders::open(context, false);
        }
        else if (canToggleSpellbook)
        {
            context.openSpellbookOverlay();
            GameplayBattleOrders::open(context, true);
        }
    }

    if (isActionNewlyPressed(context, KeyboardAction::Cast, config.pInputFrame, config.pKeyboardState))
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
        && !quickReferenceActive
        && !formationBuilderOpen
        && !config.blockInventoryToggle;

    if (isActionNewlyPressed(context, KeyboardAction::Inventory, config.pInputFrame, config.pKeyboardState)
        && canToggleInventory)
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

    // MM9's formation key opens the builder over play and closes it again (keeping the old formation).
    if (isActionNewlyPressed(context, KeyboardAction::PartyFormation, config.pInputFrame, config.pKeyboardState))
    {
        if (formationBuilderOpen)
        {
            GameplayFormationBuilder::close(context);
        }
        else if (gameplayIdle && GameplayFormationBuilder::available(context))
        {
            GameplayFormationBuilder::open(context);
        }
    }

    // The gather key closes the loot summary it opened.
    if (context.lootSummaryOverlayReadOnly().active
        && isActionNewlyPressed(context, KeyboardAction::GatherLoot, config.pInputFrame, config.pKeyboardState))
    {
        GameplayLootSummaryRenderer::close(context);
    }

    // MAW's keys (devdocs/maw/GAPS.md §11 D.18), listed in the key bindings of a MAW game only.
    if (Party *pParty = context.party(); gameplayIdle && pParty != nullptr && pWorldRuntime != nullptr)
    {
        if (isActionNewlyPressed(context, KeyboardAction::Unstuck, config.pInputFrame, config.pKeyboardState))
        {
            std::string statusText;

            if (!GameplayActionController::tryUnstuckParty(*pParty, *pWorldRuntime, statusText) && !statusText.empty())
            {
                context.setStatusBarEvent(statusText);
            }
        }

        if (isActionNewlyPressed(context, KeyboardAction::GatherLoot, config.pInputFrame, config.pKeyboardState))
        {
            GameplayActionController::GatherLootResult result =
                GameplayActionController::gatherLoot(*pParty, *pWorldRuntime);

            if (result.summary.active)
            {
                context.lootSummaryOverlay() = std::move(result.summary);
            }
            else if (result.statusText)
            {
                context.setStatusBarEvent(*result.statusText);
            }
        }
    }

    // MMMerge's follower keys (NPCFollowers.lua:345-351): the follower panel, and a word with each of the first four
    // followers; none in a world without followers (MM9).
    const Party *pFollowerParty = context.partyReadOnly();
    if (gameplayIdle && pFollowerParty != nullptr && pFollowerParty->npcFollowersActive())
    {
        if (isActionNewlyPressed(context, KeyboardAction::FollowerPanel, config.pInputFrame, config.pKeyboardState))
        {
            context.toggleFollowerPanel();
        }

        constexpr std::array<KeyboardAction, 4> FollowerActions = {KeyboardAction::Follower1,
            KeyboardAction::Follower2, KeyboardAction::Follower3, KeyboardAction::Follower4};

        for (size_t follower = 0; follower < FollowerActions.size(); ++follower)
        {
            if (isActionNewlyPressed(context, FollowerActions[follower], config.pInputFrame, config.pKeyboardState))
            {
                context.openFollowerNpcDialogueByIndex(follower);
            }
        }
    }

    // The potion radial's slots for the active member (GAPS.md H.6), in every world.
    const Party *pQuickParty = context.partyReadOnly();
    if (gameplayIdle && pQuickParty != nullptr)
    {
        constexpr std::array<KeyboardAction, QuickItemSlotCount> QuickItemActions = {KeyboardAction::QuickItem1,
            KeyboardAction::QuickItem2, KeyboardAction::QuickItem3, KeyboardAction::QuickItem4,
            KeyboardAction::QuickItem5, KeyboardAction::QuickItem6};

        for (size_t slot = 0; slot < QuickItemActions.size(); ++slot)
        {
            if (isActionNewlyPressed(context, QuickItemActions[slot], config.pInputFrame, config.pKeyboardState))
            {
                context.itemService().useQuickItemSlot(context, pQuickParty->activeMemberIndex(), slot);
            }
        }
    }

    if (isActionNewlyPressed(context, KeyboardAction::OpenWorkbench, config.pInputFrame, config.pKeyboardState)
        && canToggleInventory && !hasActiveLootView && !houseShopActive)
    {
        if (!characterScreenOpen)
        {
            context.toggleCharacterInventoryScreen();
        }

        GameplayPartyOverlayInputController::openWorkbench(context);
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
        && !quickReferenceActive
        && !houseBankInputActive
        && !config.blockPartyCycle;

    const bool canToggleQuickReference =
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
        && !context.readableScrollOverlayReadOnly().active
        && !context.lootSummaryOverlayReadOnly().active
        && !formationBuilderOpen
        && !context.utilitySpellOverlayReadOnly().active
        && !houseShopActive
        && !houseBankInputActive;

    // Quick Ref and Statistics open their page of the overlay; the key of the page shown closes it.
    using QuickReferencePage = GameplayUiController::QuickReferencePage;
    const std::array<std::pair<KeyboardAction, QuickReferencePage>, 2> pageKeys = {{
        {KeyboardAction::QuickRef, QuickReferencePage::Party},
        {KeyboardAction::Statistics, QuickReferencePage::Statistics},
    }};

    for (const auto &[action, page] : pageKeys)
    {
        if (!isActionNewlyPressed(context, action, config.pInputFrame, config.pKeyboardState))
        {
            continue;
        }

        if (quickReferenceActive && context.quickReferenceScreenStateReadOnly().page == page)
        {
            context.closeQuickReferenceOverlay();
        }
        else if (quickReferenceActive || canToggleQuickReference)
        {
            context.openQuickReferenceOverlay(page);
        }
    }

    if (!canCyclePartyMember
        || !isActionNewlyPressed(context, KeyboardAction::CharCycle, config.pInputFrame, config.pKeyboardState))
    {
        return;
    }

    Party *pParty = context.party();

    if (pParty == nullptr || pParty->members().empty())
    {
        return;
    }

    const bool requireGameplayReady =
        config.requireGameplayReadyForPartySelection
        && !activeEventDialog
        && !hasActiveLootView
        && !houseShopActive;
    const std::optional<size_t> nextMemberIndex = nextSelectableMemberIndex(*pParty, requireGameplayReady);

    if (nextMemberIndex.has_value())
    {
        context.trySelectPartyMember(*nextMemberIndex, requireGameplayReady);
    }
}

void GameplayInputController::handleSharedGameplayHotkeys(
    GameplayScreenRuntime &context,
    const GameplaySharedGameplayHotkeyConfig &config)
{
    if (config.pKeyboardState == nullptr
        || GameplayUiController::characterScreenSearchActive(context.characterScreenReadOnly())
        || GameplayUiController::journalSearchActive(context.journalScreenStateReadOnly())
        || GameplayUiController::spellbookSearchActive(context.spellbookReadOnly())
        || GameplaySoloBarSelector::isOpen(context))
    {
        context.interactionState().alwaysRunToggleLatch = false;
        context.interactionState().adventurersInnToggleLatch = false;
        context.interactionState().turnBasedToggleLatch = false;
        context.interactionState().yellLatch = false;
        return;
    }

    // Yell: nearby villagers flee for two seconds and the party drops Invisibility; not in turn-based combat
    // (OE Party::yell, Io/KeyboardInputHandler). The active member yells again only once the last yell has finished;
    // each yell restarts the face animation.
    if (config.canToggleAlwaysRun
        && isActionHeld(context, KeyboardAction::Yell, config.pInputFrame, config.pKeyboardState))
    {
        if (!context.interactionState().yellLatch)
        {
            context.interactionState().yellLatch = true;
            Party *pParty = context.party();
            IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();

            if (pParty != nullptr
                && pWorldRuntime != nullptr
                && !context.turnBasedCombatRuntime().active()
                && !context.isMemberSpeechPlaying(pParty->activeMemberIndex(), SpeechId::Yell))
            {
                constexpr float YellRadius = 512.0f;
                constexpr float YellFleeSeconds = 2.0f;
                pParty->clearPartyBuff(PartyBuffId::Invisibility);
                pWorldRuntime->scareNearbyPeasants(YellRadius, YellFleeSeconds);
                const Character *pActive = pParty->activeMember();

                if (pActive != nullptr && GameMechanics::canAct(*pActive))
                {
                    context.playSpeechReaction(pParty->activeMemberIndex(), SpeechId::Yell, true);
                }
            }
        }
    }
    else
    {
        context.interactionState().yellLatch = false;
    }

    if (config.canToggleAlwaysRun
        && isActionHeld(context, KeyboardAction::AlwaysRun, config.pInputFrame, config.pKeyboardState))
    {
        if (!context.interactionState().alwaysRunToggleLatch)
        {
            GameSettings &settings = context.mutableSettings();
            settings.alwaysRun = !settings.alwaysRun;

            if (IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime())
            {
                pWorldRuntime->setAlwaysRunEnabled(settings.alwaysRun);
            }

            context.commitSettingsChange();
            context.interactionState().alwaysRunToggleLatch = true;
        }
    }
    else
    {
        context.interactionState().alwaysRunToggleLatch = false;
    }

    // The keypad's Enter toggles too while the key is the default Enter; a rebound key replaces both.
    const InputBinding combatBinding = context.settingsSnapshot().keyboard.binding(KeyboardAction::Combat);
    const bool combatOnEnter =
        combatBinding.kind == InputBindingKind::Keyboard && combatBinding.scancode == SDL_SCANCODE_RETURN;
    const bool combatKeyHeld =
        isActionHeld(context, KeyboardAction::Combat, config.pInputFrame, config.pKeyboardState)
        || (combatOnEnter && isScancodeHeld(SDL_SCANCODE_KP_ENTER, config.pInputFrame, config.pKeyboardState));
    const bool combatPressed =
        config.canToggleAlwaysRun
        && combatKeyHeld;

    if (!config.canToggleAlwaysRun && combatKeyHeld)
    {
        context.interactionState().turnBasedToggleLatch = true;
        return;
    }

    if (combatPressed)
    {
        if (!context.interactionState().turnBasedToggleLatch)
        {
            Party *pParty = context.party();

            if (pParty != nullptr)
            {
                context.toggleTurnBasedMode();
            }

            context.interactionState().turnBasedToggleLatch = true;
        }
    }
    else
    {
        context.interactionState().turnBasedToggleLatch = false;
    }

    if (config.canToggleAdventurersInn && config.pKeyboardState[SDL_SCANCODE_P]
        && !(isActionHeld(context, KeyboardAction::SkillCover, config.pInputFrame, config.pKeyboardState)
            && GameplayPartyOverlayInputController::skillSwitchForAction(context, KeyboardAction::SkillCover)))
    {
        if (!context.interactionState().adventurersInnToggleLatch)
        {
            GameplayUiController::CharacterScreenState &characterScreen = context.characterScreen();

            if (context.isAdventurersInnCharacterSourceActive())
            {
                characterScreen.open = false;
                characterScreen.dollJewelryOverlayOpen = false;
                characterScreen.adventurersInnRosterOverlayOpen = false;
            }
            else if (context.party() != nullptr && !context.party()->adventurersInnMembers().empty())
            {
                characterScreen.open = true;
                characterScreen.adventurersInnRosterOverlayOpen = true;
                characterScreen.source = GameplayUiController::CharacterScreenSource::AdventurersInn;
                characterScreen.sourceIndex = 0;
                characterScreen.adventurersInnScrollOffset = 0;
                characterScreen.page = GameplayUiController::CharacterPage::Inventory;
                characterScreen.dollJewelryOverlayOpen = false;
            }
            else
            {
                context.setStatusBarEvent(Engine::tr("The Adventurer's Inn is empty."));
            }

            context.interactionState().adventurersInnToggleLatch = true;
        }
    }
    else
    {
        context.interactionState().adventurersInnToggleLatch = false;
    }
}

GameplaySharedInputFrameResult GameplayInputController::updateSharedGameplayInputFrame(
    GameplayScreenState &screenState,
    GameplayScreenRuntime &context,
    GameplaySpellService &spellService,
    const GameplaySharedInputFrameConfig &config)
{
    GameplaySharedInputFrameResult frameResult = {};
    GameplayScreenState::PendingSpellTargetState &pendingSpellCast = screenState.pendingSpellTarget();
    GameplayScreenState::QuickSpellState &quickSpellState = screenState.quickSpellState();
    GameplayScreenState::GameplayMouseLookState &gameplayMouseLookState = screenState.gameplayMouseLookState();

    IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
    const bool hasPendingSpellCast = pendingSpellCast.active;
    const GameplayUiController::HeldInventoryItemState &heldInventoryItem = context.heldInventoryItem();
    const bool blocksUnderlyingMouseInput =
        context.currentHudScreenState() != GameplayHudScreenState::Gameplay
        || config.isModalOverlayActive;
    const GameSettings &settings = context.settingsSnapshot();
    const bool modernControls = settings.controlScheme == ControlScheme::Modern;
    const bool mouseLookPossible =
        modernControls
        && GameplayScreenController::canEnableGameplayMouseLook(
            context,
            GameplayMouseLookEnableConfig{
                .hasPendingSpellTarget = hasPendingSpellCast,
                .blockOnReadableScrollOverlay = true,
                .blockOnUtilitySpellOverlay = true,
            });

    // The Free Cursor key (OY-637, GrayFace's middle button): mouse look off and the cursor free over play, the world
    // running and the party moving as under the classic controls, until pressed again. It acts only over play, where
    // mouse look could be on; screens opened meanwhile keep the mode.
    if (!modernControls)
    {
        gameplayMouseLookState.freeCursorToggled = false;
    }
    else if (mouseLookPossible
        && isActionNewlyPressed(context, KeyboardAction::CursorMode, config.pInputFrame, config.pKeyboardState))
    {
        gameplayMouseLookState.freeCursorToggled = !gameplayMouseLookState.freeCursorToggled;
    }

    const bool gameplayMouseLookAllowed = mouseLookPossible && !gameplayMouseLookState.freeCursorToggled;

    // Holding the right button is the cursor mode under mouse look; this frame lets it go.
    const bool cursorModeReleased = gameplayMouseLookState.cursorModeActive && !config.rightButtonPressed;
    frameResult.mouseLookPolicy =
        updateGameplayMouseLookPolicy(
            gameplayMouseLookState,
            GameplayMouseLookPolicyConfig{
                .mouseLookAllowed = gameplayMouseLookAllowed,
                .rightMousePressed = config.rightButtonPressed,
            });

    const bool canToggleAdventurersInn =
        GameplayScreenController::canRunStandardGameplayAction(
            context,
            GameplayStandardGameplayActionGateConfig{
                .hasActiveLootView = hasActiveLootView,
                .hasPendingSpellCast = hasPendingSpellCast,
                .hasHeldItem = heldInventoryItem.active,
                .blockOnHeldItem = true,
            });

    if (config.processStandardUiInput)
    {
        const GameplayUiOverlayInputResult overlayInputResult =
            GameplayScreenController::processStandardUiInputFrame(
                context,
                GameplayStandardUiInputFrameConfig{
                    .hotkeys =
                        GameplayStandardUiHotkeyConfig{
                            .pKeyboardState = config.pKeyboardState,
                            .pInputFrame = config.pInputFrame,
                            .canOpenRest = true,
                            .blockMenuToggle =
                                hasPendingSpellCast
                                || context.characterScreenReadOnly().open,
                            .blockSpellbookToggle = hasPendingSpellCast || heldInventoryItem.active,
                            .blockInventoryToggle = false,
                            .blockPartyCycle = hasPendingSpellCast || context.characterScreenReadOnly().open,
                            .requireGameplayReadyForPartySelection = true,
                        },
                    .input =
                        GameplayStandardUiInputConfig{
                            .pKeyboardState = config.pKeyboardState,
                            .pInputFrame = config.pInputFrame,
                            .width = config.screenWidth,
                            .height = config.screenHeight,
                            .pointerX = config.pointerX,
                            .pointerY = config.pointerY,
                            .leftButtonPressed = config.leftButtonPressed,
                            .rightButtonPressed = config.rightButtonPressed,
                            .allowGameplayPointerInput = frameResult.mouseLookPolicy.allowGameplayPointerInput,
                            .rightPressUsesHeldItem = !frameResult.mouseLookPolicy.cursorModeActive,
                            .mouseWheelDelta = config.mouseWheelDelta,
                            .blockPortraitInput =
                                config.isUtilitySpellModalActive || config.isModalOverlayActive,
                            .blockHudButtonInput = blocksUnderlyingMouseInput || config.isUtilitySpellModalActive,
                            .blockJournalToggle =
                                hasPendingSpellCast
                                || context.characterScreenReadOnly().open
                                || heldInventoryItem.active
                                || GameplayFormationBuilder::isOpen(context)
                                || GameplaySoloBarSelector::isOpen(context),
                            .requireGameplayReadyForPortraitSelection = !hasPendingSpellCast,
                            .onPortraitActivated =
                                [&screenState, &context, &spellService, &config, hasPendingSpellCast](
                                    size_t memberIndex)
                                {
                                    if (!hasPendingSpellCast)
                                    {
                                        return false;
                                    }

                                    GameplaySpellActionController::PendingTargetSelectionInput pendingTargetInput = {};
                                    pendingTargetInput.confirmPressed = true;
                                    pendingTargetInput.portraitMemberIndex = memberIndex;
                                    pendingTargetInput.targetQueries =
                                        buildSpellActionTargetQueries(screenState, config);

                                    const GameplaySpellActionController::PendingTargetSelectionResult result =
                                        GameplaySpellActionController::updatePendingTargetSelection(
                                            screenState,
                                            context,
                                            spellService,
                                            pendingTargetInput);

                                    if (result.castSucceeded)
                                    {
                                        if (IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime())
                                        {
                                            pWorldRuntime->applyPendingSpellCastWorldEffects(result.castResult);
                                            pWorldRuntime->clearWorldHover();
                                        }
                                    }

                                    return true;
                                },
                        },
                });

        frameResult.journalInputConsumed = overlayInputResult.journalInputConsumed;
    }

    if (frameResult.journalInputConsumed)
    {
        return frameResult;
    }

    if (cursorModeReleased
        && config.processStandardUiInput
        && heldInventoryItem.active
        && !hasPendingSpellCast
        && !hasActiveLootView
        && !config.isUtilitySpellModalActive
        && !config.isModalOverlayActive
        && context.currentHudScreenState() == GameplayHudScreenState::Gameplay)
    {
        GameplayHudInputController::useHeldItemOnPortraitAtPointer(
            context,
            config.screenWidth,
            config.screenHeight,
            config.pointerX,
            config.pointerY);
    }

    const bool canRunStandardGameplayAction =
        GameplayScreenController::canRunStandardGameplayAction(
            context,
            GameplayStandardGameplayActionGateConfig{
                .hasActiveLootView = hasActiveLootView,
                .hasPendingSpellCast = hasPendingSpellCast,
                .blockOnCharacterScreen = true,
            });

    if (config.processSharedGameplayHotkeys)
    {
        handleSharedGameplayHotkeys(
            context,
            GameplaySharedGameplayHotkeyConfig{
                .pKeyboardState = config.pKeyboardState,
                .pInputFrame = config.pInputFrame,
                .canToggleAlwaysRun = canRunStandardGameplayAction,
                .canToggleAdventurersInn = canToggleAdventurersInn,
            });
    }

    GameplayOverlayInteractionState &interactionState = context.interactionState();
    const bool quickCastButtonRequested = interactionState.gameplayHudQuickCastRequested;
    interactionState.gameplayHudQuickCastRequested = false;
    // A solo run's Upkeep bar slot, held: as the Upkeep key held.
    bool heldBarUpkeep = false;

    if (canRunStandardGameplayAction && config.processQuickCast)
    {
        if (context.turnBasedCombatRuntime().active()
            && isActionNewlyPressed(context, KeyboardAction::Pass, config.pInputFrame, config.pKeyboardState))
        {
            context.passTurnBasedTurn();
        }

        // MMMerge's extra quick spells (ExtraQuickSpells.lua) share the quick spell's hold, repeat and attack fallback;
        // the held key's slot decides the spell.
        constexpr std::array<KeyboardAction, ExtraQuickSpellSlotCount> ExtraQuickSpellActions = {
            KeyboardAction::QuickSpell1, KeyboardAction::QuickSpell2, KeyboardAction::QuickSpell3,
            KeyboardAction::QuickSpell4};
        std::optional<size_t> heldExtraSlot;

        for (size_t slot = 0; slot < ExtraQuickSpellActions.size() && !heldExtraSlot; ++slot)
        {
            if (isActionHeld(context, ExtraQuickSpellActions[slot], config.pInputFrame, config.pKeyboardState)
                && !GameplayQuickItems::takesPointerAction(context, ExtraQuickSpellActions[slot]))
            {
                heldExtraSlot = slot;
            }
        }

        // A solo run's action bar (devdocs/solo_action/HUD.md): keys 1-0 use the active member's slot. A spell casts
        // through the quick spell's path (its hold, repeat, recovery and attack fallback), a potion or scroll kind is
        // used as a quick item slot is, the weapon slot attacks. A left click on a key acts as that key held while the
        // button stays down.
        std::string heldBarSpell;
        if (context.soloHud() && config.pInputFrame != nullptr)
        {
            Party *pBarParty = context.party();
            const GameplayInputFrame &barInput = *config.pInputFrame;
            const std::optional<size_t> keySlot = GameplaySoloHud::heldBarSlot(barInput);
            const std::optional<size_t> clickedSlot =
                barInput.leftMouseButton.held ? GameplaySoloBarSelector::clickedBarSlot(context) : std::nullopt;
            const std::optional<size_t> barSlot = keySlot ? keySlot : clickedSlot;
            const Character *pBarMember = pBarParty != nullptr ? pBarParty->activeMember() : nullptr;
            if (barSlot && pBarMember != nullptr)
            {
                const ActionBarSlot &slot = pBarMember->actionBar[*barSlot];
                const bool pressed = keySlot ? GameplaySoloHud::barSlotPressed(barInput, *barSlot)
                                             : barInput.leftMouseButton.pressed;
                if (slot.kind == ActionBarSlotKind::Spell && context.spellTable() != nullptr)
                {
                    if (const SpellEntry *pSpell = context.spellTable()->findById(int(slot.id)))
                    {
                        heldBarSpell = pSpell->name;
                    }
                }
                else if (slot.kind == ActionBarSlotKind::Item && pressed)
                {
                    // A bar key drinks or reads the strongest of its kind first (user, 2026-11-16); the bar has no
                    // weakest-first choice, so a key saved with the old default drinks the strongest too.
                    QuickItemSlot strongest = slot.item;
                    strongest.bottleRule = QuickItemBottleRule::Strongest;
                    context.itemService().useQuickItemKind(context, pBarParty->activeMemberIndex(), strongest);
                }
                else if (slot.kind == ActionBarSlotKind::Weapon && pressed)
                {
                    // Weapon slot 0 attacks; slot id 1 swaps the melee weapon and the bow.
                    (slot.id == ActionBarWeaponSwapId ? context.interactionState().soloWeaponSwapRequested
                                                      : context.interactionState().gameplayHudAttackRequested) = true;
                }
                else if (slot.kind == ActionBarSlotKind::Talent && pressed)
                {
                    context.interactionState().soloTalentRequested = slot.id;
                }
                else if (slot.kind == ActionBarSlotKind::Upkeep)
                {
                    heldBarUpkeep = true;
                }
            }
        }

        const bool mainQuickCastPressed =
            quickCastButtonRequested
            || (isActionHeld(context, KeyboardAction::CastReady, config.pInputFrame, config.pKeyboardState)
                && !GameplayQuickItems::takesPointerAction(context, KeyboardAction::CastReady));
        const bool isQuickCastPressed = mainQuickCastPressed || heldExtraSlot.has_value() || !heldBarSpell.empty();

        if (isQuickCastPressed && !quickSpellState.castLatch)
        {
            quickSpellState.extraSlot = mainQuickCastPressed ? std::nullopt : heldExtraSlot;
            quickSpellState.barSpellName = mainQuickCastPressed || heldExtraSlot ? std::string() : heldBarSpell;
        }

        const GameplayActionController::QuickCastActionDecision quickCastDecision =
            GameplayActionController::updateQuickCastAction(
                quickSpellState,
                GameplayActionController::QuickCastActionConfig{
                    .canRunAction = true,
                    .quickCastPressed = isQuickCastPressed,
                    .hasReadyMember = config.hasReadyMember,
                    .turnBased = context.turnBasedCombatRuntime().active(),
                    .fastRepeat = context.settingsSnapshot().fastAttackRepeat,
                });

        if (quickCastDecision.shouldBeginQuickCast)
        {
            GameplayActionController::QuickCastActionResult quickCastResult =
                GameplayActionController::QuickCastActionResult::Failed;
            bool quickCastHandledByTurnBasedMode = false;

            if (context.turnBasedCombatRuntime().active())
            {
                Party *pParty = context.party();
                if (context.turnBasedCombatRuntime().stage() == TurnBasedCombatStage::Movement)
                {
                    context.turnBasedCombatRuntime().finishMovementPhase();
                    quickCastHandledByTurnBasedMode = true;
                }
                else if (pParty == nullptr || !context.turnBasedCombatRuntime().canBeginPlayerAction(*pParty))
                {
                    quickCastHandledByTurnBasedMode = true;
                }
            }

            // A solo run's arms play the cast first: the spell is cast at the clip's release key (below), its
            // recovery counted from now. A cast or swing already under way takes the press.
            GameplayScreenRuntime::ViewModelLink &viewModel = context.viewModelLink();
            const Party *pCastParty = context.partyReadOnly();
            const Character *pCaster = pCastParty != nullptr ? pCastParty->activeMember() : nullptr;
            const std::string deferredSpell = pCaster == nullptr ? std::string()
                : !quickSpellState.barSpellName.empty() ? quickSpellState.barSpellName
                : quickSpellState.extraSlot && *quickSpellState.extraSlot < ExtraQuickSpellSlotCount
                    ? pCaster->extraQuickSpellNames[*quickSpellState.extraSlot]
                    : pCaster->quickSpellName;
            bool quickCastTakenByArms = false;
            if (!quickCastHandledByTurnBasedMode && viewModel.swingWaiting)
            {
                quickCastTakenByArms = true;
            }
            else if (!quickCastHandledByTurnBasedMode && config.canBeginQuickCast && viewModel.meleeSwings
                && !context.turnBasedCombatRuntime().active() && pCaster != nullptr
                && GameMechanics::canTakeGameplayAction(*pCaster)
                && !screenState.pendingSpellTarget().active
                && GameplaySpellActionController::prepareViewModelCast(context, *pCaster, deferredSpell))
            {
                viewModel.swingWaiting = true;
                viewModel.waitIsCast = true;
                viewModel.quickCastWaiting = true;
                viewModel.quickCastExtraSlot = quickSpellState.extraSlot;
                viewModel.quickCastBarSpell = quickSpellState.barSpellName;
                viewModel.blowReleased = false;
                viewModel.blowDirection.reset();
                viewModel.swingWaitSeconds = 0.0f;
                ++viewModel.swingSerial;
                quickCastResult = GameplayActionController::QuickCastActionResult::CastStarted;
                quickCastTakenByArms = true;
            }

            if (!quickCastHandledByTurnBasedMode && !quickCastTakenByArms && config.canBeginQuickCast
                && context.worldRuntime() != nullptr)
            {
                const GameplaySpellActionController::SpellActionResult spellActionResult =
                    GameplaySpellActionController::tryBeginQuickSpellCast(
                        context,
                        spellService,
                        buildSpellActionTargetQueries(screenState, config),
                        quickSpellState.extraSlot,
                        quickSpellState.barSpellName);

                if (spellActionResult == GameplaySpellActionController::SpellActionResult::AttackFallback)
                {
                    quickCastResult = GameplayActionController::QuickCastActionResult::AttackFallback;
                }
                else if (spellActionResult == GameplaySpellActionController::SpellActionResult::CastStarted)
                {
                    quickCastResult = GameplayActionController::QuickCastActionResult::CastStarted;
                    context.noteViewModelAction(GameplayScreenRuntime::ViewModelAction::Cast);
                }
            }

            GameplayActionController::applyQuickCastActionResult(quickSpellState, quickCastResult);
        }
    }
    else if (config.processQuickCast)
    {
        GameplayActionController::updateQuickCastAction(
            quickSpellState,
            GameplayActionController::QuickCastActionConfig{});
    }

    // A deferred quick or action-bar cast reaches its clip's release key (or the arms never report it): cast it now,
    // its recovery shortened by the time the clip took, so it still counts from the press.
    if (config.processQuickCast)
    {
        constexpr float CastTimeoutSeconds = 2.0f;
        GameplayScreenRuntime::ViewModelLink &viewModel = context.viewModelLink();
        if (viewModel.swingWaiting && viewModel.quickCastWaiting
            && (viewModel.blowReleased || viewModel.swingWaitSeconds > CastTimeoutSeconds))
        {
            const float spent = viewModel.swingWaitSeconds;
            viewModel.swingWaiting = false;
            viewModel.quickCastWaiting = false;
            viewModel.blowReleased = false;
            viewModel.swingWaitSeconds = 0.0f;
            if (context.worldRuntime() != nullptr)
            {
                const GameplaySpellActionController::SpellActionResult released =
                    GameplaySpellActionController::tryBeginQuickSpellCast(
                        context,
                        spellService,
                        buildSpellActionTargetQueries(screenState, config),
                        viewModel.quickCastExtraSlot,
                        viewModel.quickCastBarSpell);
                Party *pParty = context.party();
                Character *pCaster = pParty != nullptr ? pParty->member(pParty->activeMemberIndex()) : nullptr;
                if (released == GameplaySpellActionController::SpellActionResult::CastStarted && pCaster != nullptr)
                {
                    pCaster->recoverySecondsRemaining = std::max(0.0f, pCaster->recoverySecondsRemaining - spent);
                }
            }
        }
    }

    // The Upkeep key (devdocs/BATTLE_ORDERS.md "Upkeep"): a ready member casts the first due spell of their list.
    if (config.processQuickCast)
    {
        const bool turnBased = context.turnBasedCombatRuntime().active();
        const GameplayActionController::UpkeepActionDecision upkeepDecision =
            GameplayActionController::updateUpkeepAction(
                screenState.upkeepActionState(),
                canRunStandardGameplayAction
                    && (heldBarUpkeep
                        || isActionHeld(context, KeyboardAction::Upkeep, config.pInputFrame, config.pKeyboardState)),
                turnBased);

        if (upkeepDecision.shouldAttemptUpkeep && config.canBeginQuickCast)
        {
            if (turnBased && context.turnBasedCombatRuntime().stage() == TurnBasedCombatStage::Movement)
            {
                context.turnBasedCombatRuntime().finishMovementPhase();
            }
            else
            {
                GameplayActionController::executePartyUpkeep(
                    GameplayActionController::PartyUpkeepConfig{
                        .pRuntime = &context,
                        .pSpellService = &spellService,
                        .pWorldRuntime = context.worldRuntime(),
                        .pParty = context.party(),
                        .pSpellTable = context.spellTable(),
                        .pressedThisFrame = upkeepDecision.pressedThisFrame,
                    });
            }
        }
    }

    const GameplayStandardWorldInputGateResult worldInputGateResult =
        GameplayScreenController::gateStandardWorldInput(
            context,
            GameplayStandardWorldInputGateConfig{
                .pKeyboardState = config.pKeyboardState,
                .pInputFrame = config.pInputFrame,
                .width = config.screenWidth,
                .height = config.screenHeight,
            });

    frameResult.worldInputBlocked = hasActiveLootView || worldInputGateResult.blocked;
    return frameResult;
}
} // namespace OpenYAMM::Game
