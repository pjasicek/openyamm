#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/ui/GameplayBuffHud.h"
#include "game/ui/GameplayFormationBuilder.h"
#include "game/ui/GameplayJournalAuras.h"
#include "game/gameplay/GameplayHudInputController.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/SpellIds.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint64_t PartyPortraitDoubleClickWindowMs = 500;
constexpr size_t VisibleFollowerPanelSlots = 3;

struct HudPointerState
{
    float x = 0.0f;
    float y = 0.0f;
    bool leftButtonPressed = false;
};

template <typename Target, typename ResolveTargetFn, typename ActivateTargetFn>
void handlePointerClickRelease(
    const HudPointerState &pointerState,
    bool &clickLatch,
    Target &pressedTarget,
    const Target &noneTarget,
    ResolveTargetFn resolveTargetFn,
    ActivateTargetFn activateTargetFn)
{
    if (pointerState.leftButtonPressed)
    {
        if (!clickLatch)
        {
            pressedTarget = resolveTargetFn(pointerState.x, pointerState.y);
            clickLatch = true;
        }
    }
    else if (clickLatch)
    {
        const Target currentTarget = resolveTargetFn(pointerState.x, pointerState.y);

        if (currentTarget == pressedTarget)
        {
            activateTargetFn(currentTarget);
        }

        clickLatch = false;
        pressedTarget = noneTarget;
    }
    else
    {
        pressedTarget = noneTarget;
    }
}

const char *activeGameplayButtonLayoutId(
    const GameplayScreenRuntime &context,
    const char *pWideId,
    const char *pStandardId)
{
    return pWideId;
}

size_t hiredFollowerCount(const GameplayScreenRuntime &context)
{
    const IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    const EventRuntimeState *pEventRuntimeState =
        pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;
    const NpcDialogTable *pNpcDialogTable = context.npcDialogTable();
    const MergedNpcProfessionTable *pNpcProfessionTable = context.mergedNpcProfessionTable();
    const Party *pParty = context.partyReadOnly();

    if (pEventRuntimeState == nullptr || pNpcDialogTable == nullptr || pNpcProfessionTable == nullptr)
    {
        return 0;
    }

    return buildHiredNpcFollowerViews(
        *pEventRuntimeState,
        pParty,
        *pNpcDialogTable,
        *pNpcProfessionTable).size();
}

bool pointerInsideHudElement(
    const GameplayScreenRuntime &context,
    const GameplayHudButtonInputConfig &config,
    const char *pLayoutId,
    float pointerX,
    float pointerY)
{
    if (pLayoutId == nullptr || *pLayoutId == '\0')
    {
        return false;
    }

    const GameplayScreenRuntime::HudLayoutElement *pLayout = context.findHudLayoutElement(pLayoutId);

    if (pLayout == nullptr)
    {
        return false;
    }

    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
        context.resolveHudLayoutElement(
            pLayoutId,
            config.screenWidth,
            config.screenHeight,
            pLayout->width,
            pLayout->height);

    return resolved && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY);
}
}

void GameplayHudInputController::activatePartyPortrait(
    GameplayScreenRuntime &context,
    size_t memberIndex,
    const GameplayPartyPortraitInputConfig &config)
{
    if (config.onPortraitActivated && config.onPortraitActivated(memberIndex))
    {
        return;
    }

    if (const Party *pParty = context.partyReadOnly(); pParty != nullptr && pParty->isHirelingCombatant(memberIndex))
    {
        activateHirelingPortrait(context, memberIndex);
        return;
    }

    if (context.heldInventoryItem().active)
    {
        const bool switchCharacterOnFailedPlacement =
            context.characterScreenReadOnly().open
            && context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Inventory;

        if (context.tryAutoPlaceHeldInventoryItemOnPartyMember(memberIndex, !switchCharacterOnFailedPlacement))
        {
            context.interactionState().lastPartyPortraitClickedIndex = std::nullopt;
        }
        else if (switchCharacterOnFailedPlacement)
        {
            GameplayUiController::CharacterScreenState &characterScreen = context.characterScreen();
            characterScreen.source = GameplayUiController::CharacterScreenSource::Party;
            characterScreen.sourceIndex = memberIndex;
            context.trySelectPartyMember(memberIndex, config.requireGameplayReady);
        }

        return;
    }

    const uint64_t nowTicks = SDL_GetTicks();
    const bool isGameplayInventoryDoubleClick =
        config.requireGameplayReady
        && context.interactionState().lastPartyPortraitClickedIndex.has_value()
        && *context.interactionState().lastPartyPortraitClickedIndex == memberIndex
        && nowTicks >= context.interactionState().lastPartyPortraitClickTicks
        && nowTicks - context.interactionState().lastPartyPortraitClickTicks <= PartyPortraitDoubleClickWindowMs;
    const bool isChestInventoryDoubleClick =
        config.hasActiveLootView
        && context.interactionState().lastPartyPortraitClickedIndex.has_value()
        && *context.interactionState().lastPartyPortraitClickedIndex == memberIndex
        && nowTicks >= context.interactionState().lastPartyPortraitClickTicks
        && nowTicks - context.interactionState().lastPartyPortraitClickTicks <= PartyPortraitDoubleClickWindowMs;

    if (context.characterScreenReadOnly().open && !context.isAdventurersInnCharacterSourceActive())
    {
        GameplayUiController::CharacterScreenState &characterScreen = context.characterScreen();
        characterScreen.source = GameplayUiController::CharacterScreenSource::Party;
        characterScreen.sourceIndex = memberIndex;
        context.trySelectPartyMember(memberIndex, config.requireGameplayReady);
        context.interactionState().lastPartyPortraitClickTicks = nowTicks;
        context.interactionState().lastPartyPortraitClickedIndex = memberIndex;
        return;
    }

    const bool selected = context.trySelectPartyMember(memberIndex, config.requireGameplayReady);

    if (!selected && !isGameplayInventoryDoubleClick)
    {
        return;
    }

    if (isGameplayInventoryDoubleClick)
    {
        GameplayUiController::CharacterScreenState &characterScreen = context.characterScreen();
        characterScreen = {};
        characterScreen.open = true;
        characterScreen.page = GameplayUiController::CharacterPage::Inventory;
        characterScreen.source = GameplayUiController::CharacterScreenSource::Party;
        characterScreen.sourceIndex = memberIndex;
    }
    else if (isChestInventoryDoubleClick)
    {
        context.openChestTransferInventoryOverlay();
    }

    context.interactionState().lastPartyPortraitClickTicks = nowTicks;
    context.interactionState().lastPartyPortraitClickedIndex = memberIndex;
}

void GameplayHudInputController::activateHirelingPortrait(GameplayScreenRuntime &context, size_t combatantIndex)
{
    Party *pParty = context.party();
    const Mm9PartyHireling *pHireling = pParty != nullptr ? pParty->hirelingCombatant(combatantIndex) : nullptr;

    // A hireling has no inventory and no character screen: a held item or an open screen takes no click on it.
    if (pHireling == nullptr || context.heldInventoryItem().active || context.characterScreenReadOnly().open)
    {
        return;
    }

    // MM9 (MM9_HIRELINGS.md 7.3): the first click makes the hireling the active member, a click on the active one opens
    // its dialogue; a double click opens it too, also for a hireling that cannot act (to dismiss it).
    const uint64_t nowTicks = SDL_GetTicks();
    const bool doubleClick = context.interactionState().lastPartyPortraitClickedIndex == combatantIndex
        && nowTicks >= context.interactionState().lastPartyPortraitClickTicks
        && nowTicks - context.interactionState().lastPartyPortraitClickTicks <= PartyPortraitDoubleClickWindowMs;
    context.interactionState().lastPartyPortraitClickTicks = nowTicks;
    context.interactionState().lastPartyPortraitClickedIndex = combatantIndex;

    if (doubleClick || pParty->activeCombatantIndex() == combatantIndex)
    {
        context.interactionState().lastPartyPortraitClickedIndex = std::nullopt;
        context.openHirelingDialogue(pHireling->rudeId);
        return;
    }

    if (!pParty->canSelectCombatantInGameplay(combatantIndex))
    {
        return;
    }

    // Turn-based combat: as for a member, the turn's actor stays until it has acted.
    if (context.turnBasedCombatRuntime().active())
    {
        const Character *pActing = pParty->combatant(pParty->activeCombatantIndex());

        if (pActing != nullptr && GameMechanics::canTakeGameplayAction(*pActing)
            && context.turnBasedCombatRuntime().canBeginPlayerAction(*pParty))
        {
            return;
        }
    }

    pParty->setActiveCombatantIndex(combatantIndex);
}

bool GameplayHudInputController::useHeldItemOnPortraitAtPointer(
    GameplayScreenRuntime &context,
    int screenWidth,
    int screenHeight,
    float pointerX,
    float pointerY)
{
    if (!context.heldInventoryItem().active || screenWidth <= 0 || screenHeight <= 0)
    {
        return false;
    }

    const std::optional<size_t> memberIndex =
        context.resolvePartyPortraitIndexAtPoint(screenWidth, screenHeight, pointerX, pointerY);

    if (!memberIndex || !context.itemService().tryUseHeldItemOnPartyMember(context, *memberIndex, false))
    {
        return false;
    }

    // The button is already up: a scroll read this way stays open until the next click.
    context.readableScrollOverlay().staysUntilClick = context.readableScrollOverlayReadOnly().active;
    context.interactionState().lastPartyPortraitClickedIndex = std::nullopt;
    return true;
}

void GameplayHudInputController::handlePartyPortraitInput(
    GameplayScreenRuntime &context,
    const GameplayPartyPortraitInputConfig &config)
{
    if (!config.allowInput || config.screenWidth <= 0 || config.screenHeight <= 0)
    {
        context.interactionState().partyPortraitClickLatch = false;
        context.interactionState().partyPortraitRightClickItemUseLatch = false;
        context.interactionState().partyPortraitPressedIndex = std::nullopt;
        context.interactionState().overlayPersonalBuffClickLatch = false;
        context.interactionState().overlayPersonalBuffPressedIndex.reset();
        return;
    }

    if (!config.rightButtonPressed)
    {
        context.interactionState().partyPortraitRightClickItemUseLatch = false;
    }
    else if (!context.interactionState().partyPortraitRightClickItemUseLatch
             && config.rightPressUsesHeldItem
             && context.heldInventoryItem().active)
    {
        context.interactionState().partyPortraitRightClickItemUseLatch = true;

        const std::optional<size_t> memberIndex =
            context.resolvePartyPortraitIndexAtPoint(
                config.screenWidth,
                config.screenHeight,
                config.pointerX,
                config.pointerY);

        const bool keepCharacterScreenOpen =
            context.characterScreenReadOnly().open
            && context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Inventory;

        if (memberIndex
            && context.itemService().tryUseHeldItemOnPartyMember(
                context,
                *memberIndex,
                keepCharacterScreenOpen))
        {
            // The original reads a message scroll on the portrait for as long as the button stays down.
            context.readableScrollOverlay().heldByRightButton = context.readableScrollOverlayReadOnly().active;
            context.interactionState().partyPortraitClickLatch = false;
            context.interactionState().partyPortraitPressedIndex = std::nullopt;
            context.interactionState().lastPartyPortraitClickedIndex = std::nullopt;
            return;
        }
    }

    if (config.touchItemReleased)
    {
        context.interactionState().partyPortraitClickLatch = false;
        context.interactionState().partyPortraitPressedIndex.reset();
        context.interactionState().overlayPersonalBuffClickLatch = false;
        context.interactionState().overlayPersonalBuffPressedIndex.reset();
        const std::optional<size_t> memberIndex = context.resolvePartyPortraitIndexAtPoint(
            config.screenWidth, config.screenHeight, config.pointerX, config.pointerY);
        if (memberIndex && context.heldInventoryItem().active)
        {
            activatePartyPortrait(context, *memberIndex, config);
        }
        return;
    }

    const HudPointerState pointerState = {
        config.pointerX,
        config.pointerY,
        config.leftButtonPressed
    };

    if (context.currentHudScreenState() != GameplayHudScreenState::Gameplay)
    {
        handlePointerClickRelease(pointerState,
            context.interactionState().overlayPersonalBuffClickLatch,
            context.interactionState().overlayPersonalBuffPressedIndex, std::optional<size_t>{},
            [&context, &config](float x, float y) -> std::optional<size_t>
            {
                const GameplayHudPointerTarget target =
                    gameplayBuffHudTarget(context, config.screenWidth, config.screenHeight, x, y);
                return target.type == GameplayHudPointerTargetType::PersonalBuffs
                    ? std::optional<size_t>(target.index) : std::nullopt;
            },
            [&context](const std::optional<size_t> &member)
            {
                if (member)
                {
                    std::optional<size_t> &selected = context.interactionState().personalBuffPopupMember;
                    selected = selected == member ? std::nullopt : member;
                    context.interactionState().partyBuffPopupOpen = false;
                }
            });
    }

    handlePointerClickRelease(
        pointerState,
        context.interactionState().partyPortraitClickLatch,
        context.interactionState().partyPortraitPressedIndex,
        std::optional<size_t>{},
        [&context, &config](float x, float y) -> std::optional<size_t>
        {
            if (gameplayBuffHudTarget(context, config.screenWidth, config.screenHeight, x, y).type
                == GameplayHudPointerTargetType::PersonalBuffs)
            {
                return std::nullopt;
            }
            return context.resolveCombatantPortraitIndexAtPoint(config.screenWidth, config.screenHeight, x, y);
        },
        [&context, &config](const std::optional<size_t> &memberIndex)
        {
            if (!memberIndex)
            {
                return;
            }

            GameplayHudInputController::activatePartyPortrait(context, *memberIndex, config);
        });
}

void GameplayHudInputController::handleGameplayHudButtonInput(
    GameplayScreenRuntime &context,
    const GameplayHudButtonInputConfig &config)
{
    if (!config.allowInput || config.screenWidth <= 0 || config.screenHeight <= 0)
    {
        context.interactionState().gameplayHudClickLatch = false;
        context.interactionState().gameplayHudPressedTarget = {};
        context.interactionState().gameplayHudPressedContextActionActive = false;
        context.interactionState().gameplayHudPressedContextActionHit = {};
        return;
    }

    // The wheel over the combat log scrolls it: up to older lines.
    if (const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
        pInput != nullptr && pInput->mouseWheelDelta != 0
        && context.combatLogPanel().contains(config.pointerX, config.pointerY))
    {
        context.combatLogPanel().scroll(pInput->mouseWheelDelta > 0 ? 1 : -1, context.combatLog());
    }

    const HudPointerState pointerState = {
        config.pointerX,
        config.pointerY,
        config.leftButtonPressed
    };

    handlePointerClickRelease(
        pointerState,
        context.interactionState().gameplayHudClickLatch,
        context.interactionState().gameplayHudPressedTarget,
        GameplayHudPointerTarget{},
        [&context, &config, &pointerState](float pointerX, float pointerY) -> GameplayHudPointerTarget
        {
            const GameplayHudPointerTarget buffTarget = gameplayBuffHudTarget(
                context, config.screenWidth, config.screenHeight, pointerX, pointerY);
            if (buffTarget.type != GameplayHudPointerTargetType::None)
            {
                return buffTarget;
            }
            if (context.interactionState().partyBuffPopupOpen || context.interactionState().personalBuffPopupMember)
            {
                return {GameplayHudPointerTargetType::DismissBuffs};
            }
            if (context.turnBasedCombatRuntime().active()
                && pointerInsideHudElement(context, config, "ObsidianTurnDock", pointerX, pointerY))
            {
                return {GameplayHudPointerTargetType::TurnBasedToggleButton};
            }
            if (const std::optional<GameplayResolvedHudLayoutElement> passRect =
                    context.resolvePassTurnButton(config.screenWidth, config.screenHeight);
                passRect && context.isPointerInsideResolvedElement(*passRect, pointerX, pointerY))
            {
                return {GameplayHudPointerTargetType::PassTurnButton};
            }
            const GameplayContextActionState &contextActionState = context.contextActionStateReadOnly();
            const bool hasDropHeldItemAction =
                contextActionState.visible
                && contextActionState.primaryIndex < contextActionState.actions.size()
                && contextActionState.actions[contextActionState.primaryIndex].kind
                    == GameplayContextActionKind::DropHeldItem;
            const bool contextActionButtonEnabled =
                context.settingsSnapshot().contextActionPopup || hasDropHeldItemAction;

            if (context.interactionState().gameplayHudPressedTarget.type
                    == GameplayHudPointerTargetType::ContextActionButton
                && contextActionButtonEnabled
                && pointerInsideHudElement(context, config, "OutdoorMobileContextActionButton", pointerX, pointerY))
            {
                return context.interactionState().gameplayHudPressedTarget;
            }

            if (context.combatLogShown()
                && pointerInsideHudElement(context, config, "CombatLogToggle", pointerX, pointerY))
            {
                return {GameplayHudPointerTargetType::CombatLogToggleButton};
            }

            if (context.combatLogPanel().contains(pointerX, pointerY))
            {
                if (const std::optional<CombatLogFilter> filter = context.combatLogPanel().filterAt(pointerX, pointerY))
                {
                    return {GameplayHudPointerTargetType::CombatLogFilter, size_t(*filter)};
                }

                if (const std::optional<uint32_t> entryId = context.combatLogPanel().entryAt(pointerX, pointerY))
                {
                    return {GameplayHudPointerTargetType::CombatLogEntry, *entryId};
                }

                return {GameplayHudPointerTargetType::CombatLogPanel};
            }

            // A world without the MM6-MM8 followers (MM9) has neither their button nor their panel.
            const Party *pParty = context.partyReadOnly();
            const bool followersShown = pParty != nullptr && pParty->npcFollowersActive();
            if (followersShown && pointerInsideHudElement(context, config, "OutdoorFollowerToggle", pointerX, pointerY))
            {
                return {GameplayHudPointerTargetType::FollowerPanelToggleButton};
            }

            // The MM9 world's formation button in the followers' place.
            if (GameplayFormationBuilder::buttonContains(
                    context, config.screenWidth, config.screenHeight, pointerX, pointerY))
            {
                return {GameplayHudPointerTargetType::FormationButton};
            }

            if (followersShown && context.interactionState().followerPanelOpen)
            {
                static constexpr std::array<const char *, VisibleFollowerPanelSlots> FollowerSlots = {{
                    "OutdoorFollowerSlot_1",
                    "OutdoorFollowerSlot_2",
                    "OutdoorFollowerSlot_3"
                }};

                for (size_t slotIndex = 0; slotIndex < FollowerSlots.size(); ++slotIndex)
                {
                    if (pointerInsideHudElement(context, config, FollowerSlots[slotIndex], pointerX, pointerY))
                    {
                        return {GameplayHudPointerTargetType::FollowerPanelPortrait, slotIndex};
                    }
                }

                if (pointerInsideHudElement(context, config, "OutdoorFollowerScrollUp", pointerX, pointerY))
                {
                    return {GameplayHudPointerTargetType::FollowerPanelScrollUpButton};
                }

                if (pointerInsideHudElement(context, config, "OutdoorFollowerScrollDown", pointerX, pointerY))
                {
                    return {GameplayHudPointerTargetType::FollowerPanelScrollDownButton};
                }
            }

            if (contextActionButtonEnabled
                && contextActionState.visible
                && contextActionState.primaryIndex < contextActionState.actions.size()
                && pointerInsideHudElement(context, config, "OutdoorMobileContextActionButton", pointerX, pointerY))
            {
                if (pointerState.leftButtonPressed && !context.interactionState().gameplayHudClickLatch)
                {
                    context.interactionState().gameplayHudPressedContextActionActive = true;
                    context.interactionState().gameplayHudPressedContextActionHit =
                        contextActionState.actions[contextActionState.primaryIndex].worldHit;
                }

                return {GameplayHudPointerTargetType::ContextActionButton, contextActionState.primaryIndex};
            }

            const std::pair<const char *, GameplayHudPointerTargetType> targets[] = {
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorButtonOptions",
                        "OutdoorStandardButtonOptions"),
                    GameplayHudPointerTargetType::MenuButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorMobileButtonPause",
                        ""),
                    GameplayHudPointerTargetType::TurnBasedToggleButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorButtonRest",
                        "OutdoorStandardButtonRest"),
                    GameplayHudPointerTargetType::RestButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorButtonBooks",
                        "OutdoorStandardButtonBooks"),
                    GameplayHudPointerTargetType::BooksButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorMobileButtonInventory",
                        ""),
                    GameplayHudPointerTargetType::InventoryButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorButtonQuickReference",
                        "OutdoorStandardButtonQuickReference"),
                    GameplayHudPointerTargetType::QuickReferenceButton
                },
                {
                    activeGameplayButtonLayoutId(context, "OutdoorButtonStatistics", ""),
                    GameplayHudPointerTargetType::StatisticsButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorMobileButtonQuickCast",
                        ""),
                    GameplayHudPointerTargetType::QuickCastButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorMobileButtonAttack",
                        ""),
                    GameplayHudPointerTargetType::AttackButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorMobileButtonCast",
                        ""),
                    GameplayHudPointerTargetType::CastButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorMinimapZoomIn",
                        "OutdoorStandardMinimapZoomIn"),
                    GameplayHudPointerTargetType::MinimapZoomInButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorMinimapZoomOut",
                        "OutdoorStandardMinimapZoomOut"),
                    GameplayHudPointerTargetType::MinimapZoomOutButton
                }
            };

            for (const auto &[pLayoutId, targetType] : targets)
            {
                if (pLayoutId == nullptr || *pLayoutId == '\0')
                {
                    continue;
                }

                const GameplayScreenRuntime::HudLayoutElement *pLayout = context.findHudLayoutElement(pLayoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                    context.resolveHudLayoutElement(
                        pLayoutId,
                        config.screenWidth,
                        config.screenHeight,
                        pLayout->width,
                        pLayout->height);

                if (resolved && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    return {targetType};
                }
            }

            if (pointerInsideHudElement(context, config, "OutdoorMinimap", pointerX, pointerY))
            {
                return {GameplayHudPointerTargetType::MinimapOpen};
            }
            return {};
        },
        [&context](const GameplayHudPointerTarget &target)
        {
            switch (target.type)
            {
            case GameplayHudPointerTargetType::BuffOverflow:
                context.interactionState().partyBuffPopupOpen = !context.interactionState().partyBuffPopupOpen;
                context.interactionState().personalBuffPopupMember.reset();
                break;
            case GameplayHudPointerTargetType::PersonalBuffs:
                if (context.interactionState().personalBuffPopupMember == target.index)
                {
                    context.interactionState().personalBuffPopupMember.reset();
                }
                else
                {
                    context.interactionState().personalBuffPopupMember = target.index;
                }
                context.interactionState().partyBuffPopupOpen = false;
                break;
            case GameplayHudPointerTargetType::PartyBuff:
                break;
            case GameplayHudPointerTargetType::PartyBuffPanel:
                // Rules with auras (MAW) open the aura panel from the party buff panels.
                if (journalHasAuraPanel(context))
                {
                    openJournalAuraPanel(context);
                }
                break;
            case GameplayHudPointerTargetType::DismissBuffs:
                context.interactionState().partyBuffPopupOpen = false;
                context.interactionState().personalBuffPopupMember.reset();
                break;
            case GameplayHudPointerTargetType::MinimapOpen:
                context.openJournalOverlay();
                context.journalScreenState().view = GameplayUiController::JournalView::Map;
                break;
            case GameplayHudPointerTargetType::MenuButton:
                if (context.pendingSpellTargetActive())
                {
                    context.interactionState().gameplayHudSpellTargetCancelRequested = true;
                }
                else
                {
                    context.openMenuOverlay();
                }
                break;
            case GameplayHudPointerTargetType::RestButton:
                context.openRestOverlay();
                break;
            case GameplayHudPointerTargetType::BooksButton:
                context.openJournalOverlay();
                break;
            case GameplayHudPointerTargetType::InventoryButton:
                context.toggleCharacterInventoryScreen();
                break;
            case GameplayHudPointerTargetType::QuickReferenceButton:
                context.openQuickReferenceOverlay();
                break;
            case GameplayHudPointerTargetType::StatisticsButton:
                context.openQuickReferenceOverlay(GameplayUiController::QuickReferencePage::Statistics);
                break;
            case GameplayHudPointerTargetType::QuickCastButton:
                context.interactionState().gameplayHudQuickCastRequested = true;
                break;
            case GameplayHudPointerTargetType::AttackButton:
                context.interactionState().gameplayHudAttackRequested = true;
                break;
            case GameplayHudPointerTargetType::TriggerButton:
                context.interactionState().gameplayHudTriggerRequested = true;
                break;
            case GameplayHudPointerTargetType::CastButton:
                if (context.pendingSpellTargetActive())
                {
                    context.interactionState().gameplayHudSpellTargetConfirmRequested = true;
                }
                else
                {
                    context.openSpellbookOverlay();
                }
                break;
            case GameplayHudPointerTargetType::TurnBasedToggleButton:
                if (context.pendingSpellTargetActive())
                {
                    context.interactionState().gameplayHudSpellTargetCancelRequested = true;
                }
                else
                {
                    context.toggleTurnBasedMode();
                }
                break;
            case GameplayHudPointerTargetType::PassTurnButton:
                context.passTurnBasedTurn();
                break;
            case GameplayHudPointerTargetType::ContextActionButton:
            {
                GameplayContextActionState &contextActionState = context.contextActionState();
                IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
                const GameplayContextAction *pSelectedAction =
                    target.index < contextActionState.actions.size()
                        ? &contextActionState.actions[target.index]
                        : nullptr;
                const bool dropHeldItemAction =
                    pSelectedAction != nullptr
                    && pSelectedAction->kind == GameplayContextActionKind::DropHeldItem;
                const bool contextActionPopupEnabled =
                    context.settingsSnapshot().contextActionPopup || dropHeldItemAction;
                const bool hasPressedContextAction =
                    contextActionPopupEnabled && context.interactionState().gameplayHudPressedContextActionActive;
                const GameplayWorldHit pressedWorldHit =
                    context.interactionState().gameplayHudPressedContextActionHit;
                GameplayWorldHit activationHit = {};

                if (hasPressedContextAction)
                {
                    activationHit = pressedWorldHit;
                }
                else if (contextActionPopupEnabled
                    && contextActionState.visible
                    && target.index < contextActionState.actions.size())
                {
                    activationHit = contextActionState.actions[target.index].worldHit;
                }

                if (dropHeldItemAction)
                {
                    context.interactionState().gameplayHudDropHeldItemRequested = true;
                }
                else if (pWorldRuntime != nullptr
                    && activationHit.hasHit
                    && pWorldRuntime->canActivateWorldHit(activationHit, GameplayInteractionMethod::Keyboard))
                {
                    pWorldRuntime->activateWorldHit(activationHit);
                }

                context.interactionState().gameplayHudPressedContextActionActive = false;
                context.interactionState().gameplayHudPressedContextActionHit = {};
                context.clearContextActionState();
                break;
            }
            case GameplayHudPointerTargetType::MinimapZoomInButton:
                context.zoomGameplayMinimapIn();
                break;
            case GameplayHudPointerTargetType::MinimapZoomOutButton:
                context.zoomGameplayMinimapOut();
                break;
            case GameplayHudPointerTargetType::FollowerPanelToggleButton:
                context.toggleFollowerPanel();
                break;
            case GameplayHudPointerTargetType::FormationButton:
                GameplayFormationBuilder::open(context);
                break;
            case GameplayHudPointerTargetType::CombatLogToggleButton:
                context.combatLogPanel().toggle();
                break;
            case GameplayHudPointerTargetType::CombatLogEntry:
                context.combatLogPanel().toggleEntry(uint32_t(target.index));
                break;
            case GameplayHudPointerTargetType::CombatLogFilter:
                context.combatLogPanel().setFilter(CombatLogFilter(target.index));
                break;
            case GameplayHudPointerTargetType::CombatLogPanel:
                break;
            case GameplayHudPointerTargetType::FollowerPanelPortrait:
                context.openFollowerNpcDialogue(target.index);
                break;
            case GameplayHudPointerTargetType::FollowerPanelScrollUpButton:
                if (context.interactionState().followerPanelScrollOffset > 0)
                {
                    --context.interactionState().followerPanelScrollOffset;
                }
                break;
            case GameplayHudPointerTargetType::FollowerPanelScrollDownButton:
            {
                const size_t followerCount = hiredFollowerCount(context);
                const size_t maxOffset =
                    followerCount > VisibleFollowerPanelSlots ? followerCount - VisibleFollowerPanelSlots : 0;
                context.interactionState().followerPanelScrollOffset =
                    std::min(context.interactionState().followerPanelScrollOffset + 1u, maxOffset);
                break;
            }
            case GameplayHudPointerTargetType::None:
                break;
        }
        });

    if (!context.interactionState().gameplayHudClickLatch)
    {
        context.interactionState().gameplayHudPressedContextActionActive = false;
        context.interactionState().gameplayHudPressedContextActionHit = {};
    }
}
} // namespace OpenYAMM::Game
