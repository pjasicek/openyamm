#include "game/gameplay/GameplayItemService.h"

#include "game/app/GameSession.h"
#include "game/audio/GameAudioSystem.h"
#include "game/items/ItemRuntime.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/items/InventoryItemUseRuntime.h"

namespace OpenYAMM::Game
{
namespace
{
enum class ActiveLootOperation
{
    ForceIdentify,
    IdentifyWithSkill,
    RepairWithSkill
};

bool applyLootOperation(
    GameplayChestItemState &lootItem,
    const ItemTable &itemTable,
    ActiveLootOperation operation,
    const Character *pInspector,
    std::string &statusText)
{
    statusText.clear();

    if (lootItem.isGold)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = itemTable.get(lootItem.item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        return false;
    }

    switch (operation)
    {
        case ActiveLootOperation::ForceIdentify:
            if (lootItem.item.identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
            {
                statusText = "Already identified.";
                return false;
            }

            lootItem.item.identified = true;
            statusText = "Identified " + ItemRuntime::displayName(lootItem.item, *pItemDefinition) + ".";
            return true;

        case ActiveLootOperation::IdentifyWithSkill:
            if (lootItem.item.identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
            {
                statusText = "Already identified.";
                return false;
            }

            if (pInspector == nullptr || !ItemRuntime::canCharacterIdentifyItem(*pInspector, *pItemDefinition))
            {
                statusText = "Not skilled enough.";
                return false;
            }

            lootItem.item.identified = true;
            statusText = "Identified " + ItemRuntime::displayName(lootItem.item, *pItemDefinition) + ".";
            return true;

        case ActiveLootOperation::RepairWithSkill:
            if (!lootItem.item.broken)
            {
                statusText = "Nothing to repair.";
                return false;
            }

            if (pInspector == nullptr || !ItemRuntime::canCharacterRepairItem(*pInspector, *pItemDefinition))
            {
                statusText = "Not skilled enough.";
                return false;
            }

            lootItem.item.broken = false;
            lootItem.item.identified = true;
            statusText = "Repaired " + ItemRuntime::displayName(lootItem.item, *pItemDefinition) + ".";
            return true;
    }

    return false;
}

Party *activeParty(GameSession &session)
{
    IGameplayWorldRuntime *pWorldRuntime = session.activeWorldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->party() : nullptr;
}

bool applyWorldItemOperation(
    IGameplayWorldRuntime &worldRuntime,
    size_t worldItemIndex,
    const ItemTable &itemTable,
    ActiveLootOperation operation,
    const Character *pInspector,
    std::string &statusText)
{
    GameplayWorldItemInspectState worldItemState = {};

    if (!worldRuntime.worldItemInspectState(worldItemIndex, worldItemState) || worldItemState.isGold)
    {
        return false;
    }

    GameplayChestItemState lootItem = {};
    lootItem.item = worldItemState.item;

    if (!applyLootOperation(lootItem, itemTable, operation, pInspector, statusText))
    {
        return false;
    }

    return worldRuntime.updateWorldItemInspectState(worldItemIndex, lootItem.item);
}
}

GameplayItemService::GameplayItemService(GameSession &session)
    : m_session(session)
{
}

bool GameplayItemService::tryUseHeldItemOnPartyMember(
    GameplayScreenRuntime &runtime,
    size_t memberIndex,
    bool keepCharacterScreenOpen)
{
    GameplayUiController &uiController = m_session.gameplayUiController();
    GameplayUiController::HeldInventoryItemState &heldItem = uiController.heldInventoryItem();
    Party *pParty = runtime.party();
    const ItemTable *pItemTable = m_session.hasDataRepository() ? &m_session.data().itemTable() : nullptr;
    const ReadableScrollTable *pReadableScrollTable =
        m_session.hasDataRepository() ? &m_session.data().readableScrollTable() : nullptr;

    if (!heldItem.active || pParty == nullptr || pItemTable == nullptr)
    {
        return false;
    }

    const InventoryItemUseResult useResult =
        InventoryItemUseRuntime::useItemOnMember(
            *pParty,
            memberIndex,
            heldItem.item,
            *pItemTable,
            pReadableScrollTable);

    if (!useResult.handled)
    {
        return false;
    }

    if (useResult.action == InventoryItemUseAction::CastScroll)
    {
        const SpellTable *pSpellTable = m_session.hasDataRepository() ? &m_session.data().spellTable() : nullptr;

        if (pSpellTable == nullptr)
        {
            runtime.setStatusBarEvent("Spell data missing");
            return true;
        }

        const SpellEntry *pSpellEntry = pSpellTable->findById(useResult.spellId);

        if (pSpellEntry == nullptr)
        {
            runtime.setStatusBarEvent("Unknown scroll spell");
            return true;
        }

        PartySpellCastRequest request = {};
        request.casterMemberIndex = memberIndex;
        request.spellId = useResult.spellId;
        request.skillLevelOverride = useResult.spellSkillLevelOverride;
        request.skillMasteryOverride = useResult.spellSkillMasteryOverride;
        request.spendMana = false;
        request.applyRecovery = true;

        if (!runtime.tryCastSpellRequest(request, pSpellEntry->name))
        {
            return true;
        }

        if (useResult.consumed)
        {
            heldItem = {};
        }
    }
    else if (useResult.action == InventoryItemUseAction::ReadMessageScroll)
    {
        GameplayUiController::ReadableScrollOverlayState &overlay = uiController.readableScrollOverlay();
        overlay.active = true;
        overlay.title = useResult.readableTitle;
        overlay.body = useResult.readableBody;
    }
    else
    {
        if (useResult.consumed)
        {
            heldItem = {};
        }

        if (useResult.action == InventoryItemUseAction::ConsumePotion
            && useResult.consumed
            && runtime.audioSystem() != nullptr)
        {
            runtime.audioSystem()->playCommonSound(SoundId::Drink, GameAudioSystem::PlaybackGroup::Ui);
            runtime.triggerPortraitFaceAnimation(memberIndex, FaceAnimationId::DrinkPotion);
        }

        if (useResult.action == InventoryItemUseAction::UseHorseshoe && useResult.consumed)
        {
            m_session.gameplayFxService().triggerPortraitEventFxWithoutSpeech(
                runtime,
                memberIndex,
                PortraitFxEventKind::QuestComplete);
        }
        else if (useResult.action == InventoryItemUseAction::LearnSpell
                 && !useResult.consumed
                 && useResult.alreadyKnown
                 && runtime.audioSystem() != nullptr)
        {
            runtime.audioSystem()->playCommonSound(SoundId::Error, GameAudioSystem::PlaybackGroup::Ui);
        }

        if (useResult.speechId.has_value())
        {
            runtime.playSpeechReaction(memberIndex, *useResult.speechId, true);
        }
    }

    if (!useResult.statusText.empty())
    {
        runtime.setStatusBarEvent(useResult.statusText);
    }

    const bool closeCharacterScreen =
        !keepCharacterScreenOpen || useResult.action == InventoryItemUseAction::CastScroll;

    if (closeCharacterScreen)
    {
        GameplayUiController::CharacterScreenState &characterScreen = m_session.gameplayScreenState().characterScreen();
        characterScreen.open = false;
        characterScreen.dollJewelryOverlayOpen = false;
    }

    return true;
}

void GameplayItemService::updateReadableScrollOverlayForHeldItem(
    size_t memberIndex,
    const GameplayCharacterPointerTarget &pointerTarget,
    bool isLeftMousePressed)
{
    GameplayUiController &uiController = m_session.gameplayUiController();
    GameplayUiController::ReadableScrollOverlayState &overlay = uiController.readableScrollOverlay();
    overlay = {};

    const ItemTable *pItemTable = m_session.hasDataRepository() ? &m_session.data().itemTable() : nullptr;
    Party *pParty = activeParty(m_session);
    const GameplayUiController::HeldInventoryItemState &heldItem = uiController.heldInventoryItem();
    const ReadableScrollTable *pReadableScrollTable =
        m_session.hasDataRepository() ? &m_session.data().readableScrollTable() : nullptr;

    if (!isLeftMousePressed
        || !heldItem.active
        || pItemTable == nullptr
        || pParty == nullptr
        || (pointerTarget.type != GameplayCharacterPointerTargetType::EquipmentSlot
            && pointerTarget.type != GameplayCharacterPointerTargetType::DollPanel))
    {
        return;
    }

    const InventoryItemUseAction useAction =
        InventoryItemUseRuntime::classifyItemUse(heldItem.item, *pItemTable);

    if (useAction != InventoryItemUseAction::ReadMessageScroll)
    {
        return;
    }

    const InventoryItemUseResult useResult =
        InventoryItemUseRuntime::useItemOnMember(
            *pParty,
            memberIndex,
            heldItem.item,
            *pItemTable,
            pReadableScrollTable);

    if (!useResult.handled || useResult.action != InventoryItemUseAction::ReadMessageScroll)
    {
        return;
    }

    overlay.active = true;
    overlay.title = useResult.readableTitle;
    overlay.body = useResult.readableBody;
}

bool GameplayItemService::identifyInspectedItem(
    const GameplayUiController::ItemInspectOverlayState &overlay,
    std::string &statusText)
{
    statusText.clear();

    Party *pParty = activeParty(m_session);
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    const ItemTable *pItemTable = m_session.hasDataRepository() ? &m_session.data().itemTable() : nullptr;

    if (pParty == nullptr || pItemTable == nullptr)
    {
        return false;
    }

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

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest && pWorldRuntime != nullptr)
    {
        GameplayChestViewState *pChestView = pWorldRuntime->activeChestView();

        if (pChestView == nullptr || overlay.sourceLootItemIndex >= pChestView->items.size())
        {
            return false;
        }

        if (!applyLootOperation(
                pChestView->items[overlay.sourceLootItemIndex],
                *pItemTable,
                ActiveLootOperation::ForceIdentify,
                nullptr,
                statusText))
        {
            return false;
        }

        pWorldRuntime->commitActiveChestView();
        return true;
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse && pWorldRuntime != nullptr)
    {
        GameplayCorpseViewState *pCorpseView = pWorldRuntime->activeCorpseView();

        if (pCorpseView == nullptr || overlay.sourceLootItemIndex >= pCorpseView->items.size())
        {
            return false;
        }

        if (!applyLootOperation(
                pCorpseView->items[overlay.sourceLootItemIndex],
                *pItemTable,
                ActiveLootOperation::ForceIdentify,
                nullptr,
                statusText))
        {
            return false;
        }

        pWorldRuntime->commitActiveCorpseView();
        return true;
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::WorldItem && pWorldRuntime != nullptr)
    {
        return applyWorldItemOperation(
            *pWorldRuntime,
            overlay.sourceWorldItemIndex,
            *pItemTable,
            ActiveLootOperation::ForceIdentify,
            nullptr,
            statusText);
    }

    return false;
}

bool GameplayItemService::tryIdentifyInspectedItem(
    const GameplayUiController::ItemInspectOverlayState &overlay,
    size_t inspectorMemberIndex,
    std::string &statusText)
{
    statusText.clear();

    Party *pParty = activeParty(m_session);
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    const ItemTable *pItemTable = m_session.hasDataRepository() ? &m_session.data().itemTable() : nullptr;

    if (pParty == nullptr || pItemTable == nullptr)
    {
        return false;
    }

    const Character *pInspector = pParty->member(inspectorMemberIndex);

    if (pInspector == nullptr)
    {
        return false;
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory)
    {
        return pParty->tryIdentifyMemberInventoryItem(
            overlay.sourceMemberIndex,
            overlay.sourceGridX,
            overlay.sourceGridY,
            inspectorMemberIndex,
            statusText);
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
    {
        return pParty->tryIdentifyEquippedItem(
            overlay.sourceMemberIndex,
            overlay.sourceEquipmentSlot,
            inspectorMemberIndex,
            statusText);
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest && pWorldRuntime != nullptr)
    {
        GameplayChestViewState *pChestView = pWorldRuntime->activeChestView();

        if (pChestView == nullptr || overlay.sourceLootItemIndex >= pChestView->items.size())
        {
            return false;
        }

        if (!applyLootOperation(
                pChestView->items[overlay.sourceLootItemIndex],
                *pItemTable,
                ActiveLootOperation::IdentifyWithSkill,
                pInspector,
                statusText))
        {
            return false;
        }

        pWorldRuntime->commitActiveChestView();
        return true;
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse && pWorldRuntime != nullptr)
    {
        GameplayCorpseViewState *pCorpseView = pWorldRuntime->activeCorpseView();

        if (pCorpseView == nullptr || overlay.sourceLootItemIndex >= pCorpseView->items.size())
        {
            return false;
        }

        if (!applyLootOperation(
                pCorpseView->items[overlay.sourceLootItemIndex],
                *pItemTable,
                ActiveLootOperation::IdentifyWithSkill,
                pInspector,
                statusText))
        {
            return false;
        }

        pWorldRuntime->commitActiveCorpseView();
        return true;
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::WorldItem && pWorldRuntime != nullptr)
    {
        return applyWorldItemOperation(
            *pWorldRuntime,
            overlay.sourceWorldItemIndex,
            *pItemTable,
            ActiveLootOperation::IdentifyWithSkill,
            pInspector,
            statusText);
    }

    return false;
}

bool GameplayItemService::tryRepairInspectedItem(
    const GameplayUiController::ItemInspectOverlayState &overlay,
    size_t inspectorMemberIndex,
    std::string &statusText)
{
    statusText.clear();

    Party *pParty = m_session.partyState() ? &*m_session.partyState() : nullptr;
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    const ItemTable *pItemTable = m_session.hasDataRepository() ? &m_session.data().itemTable() : nullptr;

    if (pParty == nullptr || pItemTable == nullptr)
    {
        return false;
    }

    const Character *pInspector = pParty->member(inspectorMemberIndex);

    if (pInspector == nullptr)
    {
        return false;
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Inventory)
    {
        return pParty->tryRepairMemberInventoryItem(
            overlay.sourceMemberIndex,
            overlay.sourceGridX,
            overlay.sourceGridY,
            inspectorMemberIndex,
            statusText);
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Equipment)
    {
        return pParty->tryRepairEquippedItem(
            overlay.sourceMemberIndex,
            overlay.sourceEquipmentSlot,
            inspectorMemberIndex,
            statusText);
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Chest && pWorldRuntime != nullptr)
    {
        GameplayChestViewState *pChestView = pWorldRuntime->activeChestView();

        if (pChestView == nullptr || overlay.sourceLootItemIndex >= pChestView->items.size())
        {
            return false;
        }

        if (!applyLootOperation(
                pChestView->items[overlay.sourceLootItemIndex],
                *pItemTable,
                ActiveLootOperation::RepairWithSkill,
                pInspector,
                statusText))
        {
            return false;
        }

        pWorldRuntime->commitActiveChestView();
        return true;
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::Corpse && pWorldRuntime != nullptr)
    {
        GameplayCorpseViewState *pCorpseView = pWorldRuntime->activeCorpseView();

        if (pCorpseView == nullptr || overlay.sourceLootItemIndex >= pCorpseView->items.size())
        {
            return false;
        }

        if (!applyLootOperation(
                pCorpseView->items[overlay.sourceLootItemIndex],
                *pItemTable,
                ActiveLootOperation::RepairWithSkill,
                pInspector,
                statusText))
        {
            return false;
        }

        pWorldRuntime->commitActiveCorpseView();
        return true;
    }

    if (overlay.sourceType == GameplayUiController::ItemInspectSourceType::WorldItem && pWorldRuntime != nullptr)
    {
        return applyWorldItemOperation(
            *pWorldRuntime,
            overlay.sourceWorldItemIndex,
            *pItemTable,
            ActiveLootOperation::RepairWithSkill,
            pInspector,
            statusText);
    }

    return false;
}

void GameplayItemService::closeReadableScrollOverlay()
{
    m_session.gameplayUiController().closeReadableScrollOverlay();
}
}
