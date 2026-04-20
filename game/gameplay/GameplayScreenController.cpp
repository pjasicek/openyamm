#include "game/gameplay/GameplayScreenController.h"

#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/items/ItemRuntime.h"
#include "game/ui/GameplayHudOverlaySupport.h"
#include "game/ui/GameplayHudOverlayRenderer.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayPartyOverlayRenderer.h"

#include <algorithm>

namespace OpenYAMM::Game
{
void GameplayScreenController::updateSharedFrameState(
    GameplayScreenRuntime &context,
    int width,
    int height,
    float deltaSeconds,
    const GameplayScreenFrameUpdateConfig &config)
{
    float &statusBarRemainingSeconds = context.statusBarEventRemainingSeconds();

    if (statusBarRemainingSeconds > 0.0f)
    {
        statusBarRemainingSeconds = std::max(0.0f, statusBarRemainingSeconds - deltaSeconds);

        if (statusBarRemainingSeconds <= 0.0f)
        {
            context.statusBarEventText().clear();
        }
    }

    updateRestOverlayProgress(context, deltaSeconds);
    GameplayHudOverlaySupport::updateCharacterInspectOverlay(context, width, height);
    GameplayHudOverlaySupport::updateCharacterDetailOverlay(context, width, height);
    GameplayHudOverlaySupport::updateSpellInspectOverlay(context, width, height);

    if (config.updateBuffInspectOverlay)
    {
        GameplayHudOverlaySupport::updateBuffInspectOverlay(context, width, height, true);
    }
    else
    {
        context.buffInspectOverlay() = {};
    }
}

bool GameplayScreenController::updateRenderedHudItemInspectOverlay(
    GameplayScreenRuntime &context,
    int width,
    int height,
    bool requireOpaqueHitTest)
{
    return GameplayHudOverlaySupport::tryPopulateItemInspectOverlayFromRenderedHudItems(
        context,
        width,
        height,
        requireOpaqueHitTest);
}

void GameplayScreenController::applySharedItemInspectSkillInteraction(
    GameplayScreenRuntime &context)
{
    GameplayUiController::ItemInspectOverlayState &overlay = context.itemInspectOverlay();
    Party *pParty = context.party();
    const ItemTable *pItemTable = context.itemTable();

    if (!overlay.active
        || !overlay.hasItemState
        || pParty == nullptr
        || pItemTable == nullptr
        || overlay.sourceType == GameplayUiController::ItemInspectSourceType::None
        || overlay.sourceType == GameplayUiController::ItemInspectSourceType::WorldItem)
    {
        return;
    }

    uint64_t interactionKey = uint64_t(overlay.objectDescriptionId);
    interactionKey ^= uint64_t(overlay.sourceMemberIndex + 1) << 16;
    interactionKey ^= uint64_t(overlay.sourceGridX) << 24;
    interactionKey ^= uint64_t(overlay.sourceGridY) << 32;
    interactionKey ^= uint64_t(overlay.sourceEquipmentSlot) << 40;
    interactionKey ^= uint64_t(overlay.sourceLootItemIndex) << 48;
    interactionKey ^= uint64_t(overlay.sourceType) << 56;

    if (context.itemInspectInteractionLatch() && context.itemInspectInteractionKey() == interactionKey)
    {
        return;
    }

    context.itemInspectInteractionLatch() = true;
    context.itemInspectInteractionKey() = interactionKey;

    const Character *pActiveMember = pParty->activeMember();
    const ItemDefinition *pItemDefinition = pItemTable->get(overlay.objectDescriptionId);

    if (pActiveMember == nullptr || pItemDefinition == nullptr)
    {
        return;
    }

    const size_t activeMemberIndex = pParty->activeMemberIndex();
    bool reactionPlayed = false;
    const auto playSingleReaction =
        [&context, activeMemberIndex, &reactionPlayed](SpeechId speechId)
        {
            if (reactionPlayed)
            {
                return;
            }

            context.playSpeechReaction(activeMemberIndex, speechId, true);
            reactionPlayed = true;
        };

    const auto refreshOverlayItemState =
        [&context, pParty, &overlay]()
        {
            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory)
            {
                const Character *pSourceMember = pParty->member(overlay.sourceMemberIndex);

                if (pSourceMember == nullptr)
                {
                    return;
                }

                const InventoryItem *pItem = pSourceMember->inventoryItemAt(overlay.sourceGridX, overlay.sourceGridY);

                if (pItem != nullptr)
                {
                    overlay.itemState = *pItem;
                }
            }
            else if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
            {
                const std::optional<InventoryItem> item =
                    pParty->equippedItem(overlay.sourceMemberIndex, overlay.sourceEquipmentSlot);

                if (item.has_value())
                {
                    overlay.itemState = *item;
                }
            }
            else if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest)
            {
                IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
                const GameplayChestViewState *pChestView =
                    pWorldRuntime != nullptr ? pWorldRuntime->activeChestView() : nullptr;

                if (pChestView != nullptr && overlay.sourceLootItemIndex < pChestView->items.size())
                {
                    overlay.itemState = pChestView->items[overlay.sourceLootItemIndex].item;
                }
            }
            else if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse)
            {
                IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
                const GameplayCorpseViewState *pCorpseView =
                    pWorldRuntime != nullptr ? pWorldRuntime->activeCorpseView() : nullptr;

                if (pCorpseView != nullptr && overlay.sourceLootItemIndex < pCorpseView->items.size())
                {
                    overlay.itemState = pCorpseView->items[overlay.sourceLootItemIndex].item;
                }
            }
        };

    const auto forceIdentifyWithoutReaction =
        [&context, pParty, &overlay](std::string &statusText) -> bool
        {
            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory)
            {
                return pParty->identifyMemberInventoryItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceGridX,
                    overlay.sourceGridY,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
            {
                return pParty->identifyEquippedItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceEquipmentSlot,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->identifyActiveChestItem(overlay.sourceLootItemIndex, statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->identifyActiveCorpseItem(overlay.sourceLootItemIndex, statusText);
            }

            return false;
        };

    const auto tryIdentifyWithSkill =
        [&context, pParty, activeMemberIndex, pActiveMember, &overlay](std::string &statusText) -> bool
        {
            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory)
            {
                return pParty->tryIdentifyMemberInventoryItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceGridX,
                    overlay.sourceGridY,
                    activeMemberIndex,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
            {
                return pParty->tryIdentifyEquippedItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceEquipmentSlot,
                    activeMemberIndex,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->tryIdentifyActiveChestItem(
                    overlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->tryIdentifyActiveCorpseItem(
                    overlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            return false;
        };

    const auto tryRepairWithSkill =
        [&context, pParty, activeMemberIndex, pActiveMember, &overlay](std::string &statusText) -> bool
        {
            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory)
            {
                return pParty->tryRepairMemberInventoryItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceGridX,
                    overlay.sourceGridY,
                    activeMemberIndex,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
            {
                return pParty->tryRepairEquippedItem(
                    overlay.sourceMemberIndex,
                    overlay.sourceEquipmentSlot,
                    activeMemberIndex,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->tryRepairActiveChestItem(
                    overlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse
                && context.worldRuntime() != nullptr)
            {
                return context.worldRuntime()->tryRepairActiveCorpseItem(
                    overlay.sourceLootItemIndex,
                    *pActiveMember,
                    statusText);
            }

            return false;
        };

    if (!overlay.itemState.identified)
    {
        std::string statusText;

        if (!ItemRuntime::requiresIdentification(*pItemDefinition))
        {
            if (forceIdentifyWithoutReaction(statusText))
            {
                refreshOverlayItemState();
            }
        }
        else if (tryIdentifyWithSkill(statusText))
        {
            refreshOverlayItemState();
            const SpeechId speechId =
                pItemDefinition->value < 100 * (int(pActiveMember->level) + 5)
                    ? SpeechId::IdentifyWeakItem
                    : SpeechId::IdentifyGreatItem;
            playSingleReaction(speechId);
        }
        else if (statusText == "Not skilled enough.")
        {
            context.setStatusBarEvent("Identify failed.");
            playSingleReaction(SpeechId::IdentifyFailItem);
        }
    }

    if (overlay.itemState.broken)
    {
        std::string statusText;

        if (tryRepairWithSkill(statusText))
        {
            refreshOverlayItemState();
            playSingleReaction(SpeechId::RepairSuccess);
        }
        else if (statusText == "Not skilled enough.")
        {
            context.setStatusBarEvent("Repair failed.");
            playSingleReaction(SpeechId::RepairFail);
        }
    }
}

void GameplayScreenController::updateRestOverlayProgress(
    GameplayScreenRuntime &context,
    float deltaSeconds)
{
    GameplayUiController::RestScreenState &restScreen = context.restScreenState();

    if (!restScreen.active)
    {
        return;
    }

    const float safeDeltaSeconds = std::max(0.0f, deltaSeconds);
    restScreen.hourglassElapsedSeconds += safeDeltaSeconds;

    if (restScreen.mode == GameplayUiController::RestMode::None || context.worldRuntime() == nullptr)
    {
        return;
    }

    constexpr float ShortestRestAnimationSeconds = 0.25f;
    constexpr float LongestRestAnimationSeconds = 2.0f;
    constexpr float RestMinutesPerAnimationSecond = 360.0f;
    const float animationDurationSeconds = std::clamp(
        restScreen.totalMinutes / RestMinutesPerAnimationSecond,
        ShortestRestAnimationSeconds,
        LongestRestAnimationSeconds);
    const float gameMinutesPerSecond = animationDurationSeconds > 0.0f
        ? restScreen.totalMinutes / animationDurationSeconds
        : restScreen.totalMinutes;
    const float advancedMinutes = std::min(
        restScreen.remainingMinutes,
        gameMinutesPerSecond * safeDeltaSeconds);

    if (advancedMinutes > 0.0f)
    {
        context.worldRuntime()->advanceGameMinutes(advancedMinutes);
        restScreen.remainingMinutes = std::max(0.0f, restScreen.remainingMinutes - advancedMinutes);
    }

    if (restScreen.remainingMinutes > 0.0f)
    {
        return;
    }

    const GameplayUiController::RestMode completedMode = restScreen.mode;
    restScreen.mode = GameplayUiController::RestMode::None;
    restScreen.totalMinutes = 0.0f;
    restScreen.remainingMinutes = 0.0f;

    if (completedMode == GameplayUiController::RestMode::Heal && context.party() != nullptr)
    {
        context.party()->restAndHealAll();
    }

    if (completedMode == GameplayUiController::RestMode::Heal)
    {
        context.closeRestOverlay();
    }
}

void GameplayScreenController::handlePartyPortraitInput(
    GameplayScreenRuntime &context,
    const GameplayPartyPortraitInputConfig &config)
{
    GameplayHudInputController::handlePartyPortraitInput(context, config);
}

void GameplayScreenController::handleGameplayHudButtonInput(
    GameplayScreenRuntime &context,
    const GameplayHudButtonInputConfig &config)
{
    GameplayHudInputController::handleGameplayHudButtonInput(context, config);
}

GameplayUiOverlayInputResult GameplayScreenController::handleSharedOverlayInput(
    GameplayScreenRuntime &context,
    const bool *pKeyboardState,
    int width,
    int height,
    const GameplayUiOverlayInputConfig &config)
{
    GameplayUiOverlayInputResult result = GameplayUiOverlayOrchestrator::handleStandardOverlayInput(
        context,
        pKeyboardState,
        width,
        height,
        config);

    if (result.journalInputConsumed && !config.activeEventDialog)
    {
        context.resetDialogueOverlayInteractionState();
    }

    return result;
}

void GameplayScreenController::handleSharedHotkeys(
    GameplayScreenRuntime &context,
    const bool *pKeyboardState,
    const GameplayScreenHotkeyConfig &config)
{
    GameplayScreenHotkeyController::handleGameplayScreenHotkeys(context, pKeyboardState, config);
}

void GameplayScreenController::handleUtilitySpellOverlayInput(
    GameplayScreenRuntime &context,
    const bool *pKeyboardState,
    int width,
    int height)
{
    GameplayPartyOverlayInputController::handleUtilitySpellOverlayInput(
        context,
        pKeyboardState,
        width,
        height);
}

void GameplayScreenController::renderSharedOverlays(
    GameplayScreenRuntime &context,
    int width,
    int height,
    const GameplayScreenRenderConfig &config)
{
    GameplayUiOverlayOrchestrator::renderStandardOverlays(context, width, height, config.base);

    if (!config.base.canRenderHudOverlays)
    {
        return;
    }

    if (config.renderDeferredInventoryOverlay)
    {
        GameplayHudOverlayRenderer::renderInventoryNestedOverlay(context, width, height, false);
    }

    if (config.renderUtilitySpellOverlay)
    {
        GameplayPartyOverlayRenderer::renderUtilitySpellOverlay(context, width, height);
    }

    if (config.renderCharacterInspectOverlay)
    {
        GameplayPartyOverlayRenderer::renderCharacterInspectOverlay(context, width, height);
    }

    if (config.renderBuffInspectOverlay)
    {
        GameplayPartyOverlayRenderer::renderBuffInspectOverlay(context, width, height);
    }

    if (config.renderCharacterDetailOverlay)
    {
        GameplayPartyOverlayRenderer::renderCharacterDetailOverlay(context, width, height);
    }

    if (config.renderActorInspectOverlay)
    {
        GameplayPartyOverlayRenderer::renderActorInspectOverlay(context, width, height);
    }

    if (config.renderSpellInspectOverlay)
    {
        GameplayPartyOverlayRenderer::renderSpellInspectOverlay(context, width, height);
    }

    if (config.renderReadableScrollOverlay)
    {
        GameplayPartyOverlayRenderer::renderReadableScrollOverlay(context, width, height);
    }
}
} // namespace OpenYAMM::Game
