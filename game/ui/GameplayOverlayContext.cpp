#include "game/ui/GameplayOverlayContext.h"

#include "game/gameplay/GameplayDialogContextBuilder.h"
#include "game/gameplay/GameplayDialogUiFlow.h"
#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/party/SpellSchool.h"
#include "game/StringUtils.h"
#include "game/ui/SpellbookUiLayout.h"

#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
bool isBodyEquipmentVisualSlot(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::Armor:
        case EquipmentSlot::Helm:
        case EquipmentSlot::Belt:
        case EquipmentSlot::Cloak:
        case EquipmentSlot::Gauntlets:
        case EquipmentSlot::Boots:
            return true;
        default:
            return false;
    }
}

bool usesAlternateCloakBeltEquippedVariant(EquipmentSlot slot)
{
    return slot == EquipmentSlot::Cloak || slot == EquipmentSlot::Belt;
}
} // namespace

GameplayOverlayContext::GameplayOverlayContext(
    GameSession &session,
    GameAudioSystem *pAudioSystem,
    GameSettings *pSettings,
    IGameplayOverlaySceneAdapter &sceneAdapter)
    : m_session(session)
    , m_pAudioSystem(pAudioSystem)
    , m_pSettings(pSettings)
    , m_sceneAdapter(sceneAdapter)
{
}

GameplayUiController &GameplayOverlayContext::uiController() const
{
    return m_session.gameplayUiController();
}

GameplayUiRuntime &GameplayOverlayContext::uiRuntime() const
{
    return m_session.gameplayUiRuntime();
}

GameplayOverlayInteractionState &GameplayOverlayContext::interactionState() const
{
    return m_session.overlayInteractionState();
}

GameplayDialogUiFlowState GameplayOverlayContext::dialogUiFlowState()
{
    return {
        uiController(),
        interactionState(),
        m_session.gameplayDialogController(),
        eventDialogSelectionIndex()
    };
}

GameplayDialogController::Context GameplayOverlayContext::buildDialogContext(EventRuntimeState &eventRuntimeState)
{
    GameplayDialogController::Callbacks callbacks = {};
    callbacks.playSpeechReaction =
        [this](size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
        {
            playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
        };
    callbacks.playHouseSound =
        [this](uint32_t soundId)
        {
            if (m_pAudioSystem != nullptr)
            {
                m_pAudioSystem->playSound(soundId, GameAudioSystem::PlaybackGroup::HouseSpeech);
            }
        };
    callbacks.cancelMapTransition =
        [this]()
        {
            if (IGameplayWorldRuntime *pWorldRuntime = worldRuntime())
            {
                pWorldRuntime->cancelPendingMapTransition();
            }
        };

    const MapStatsEntry *pCurrentMap = m_session.hasCurrentMapFileName()
        ? m_session.data().mapStats().findByFileName(m_session.currentMapFileName())
        : nullptr;

    return buildGameplayDialogContext(
        uiController(),
        eventRuntimeState,
        activeEventDialog(),
        eventDialogSelectionIndex(),
        party(),
        worldRuntime(),
        nullptr,
        houseTable(),
        classSkillTable(),
        npcDialogTable(),
        pCurrentMap,
        &m_session.data().mapEntries(),
        rosterTable(),
        &m_session.data().arcomageLibrary(),
        currentHudScreenState() == GameplayHudScreenState::Dialogue,
        std::move(callbacks));
}

void GameplayOverlayContext::presentPendingEventDialogShared(size_t previousMessageCount, bool allowNpcFallbackContent)
{
    GameplayDialogUiFlowState state = dialogUiFlowState();
    GameplayDialogUiFlowPresentOptions options = {};
    options.suppressInitialAcceptIfActivationKeysHeld = m_session.currentSceneKind() == SceneKind::Outdoor;

    ::OpenYAMM::Game::presentPendingEventDialog(
        state,
        worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr,
        [this](EventRuntimeState &eventRuntimeState)
        {
            return buildDialogContext(eventRuntimeState);
        },
        previousMessageCount,
        allowNpcFallbackContent,
        options);
}

void GameplayOverlayContext::closeActiveEventDialogShared()
{
    GameplayDialogUiFlowState state = dialogUiFlowState();
    ::OpenYAMM::Game::closeActiveEventDialog(
        state,
        worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr);
}

void GameplayOverlayContext::returnToHouseBankMainDialogShared()
{
    GameplayDialogUiFlowState state = dialogUiFlowState();
    const GameplayDialogController::Result result = ::OpenYAMM::Game::returnToHouseBankMainDialog(
        state,
        worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr,
        [this](EventRuntimeState &eventRuntimeState)
        {
            return buildDialogContext(eventRuntimeState);
        });

    if (result.shouldOpenPendingEventDialog)
    {
        presentPendingEventDialogShared(result.previousMessageCount, result.allowNpcFallbackContent);
    }
}

IGameplayWorldRuntime *GameplayOverlayContext::worldRuntime() const
{
    return m_session.activeWorldRuntime();
}

Party *GameplayOverlayContext::party() const
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->party() : nullptr;
}

const Party *GameplayOverlayContext::partyReadOnly() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->party() : nullptr;
}

float GameplayOverlayContext::partyX() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->partyX() : 0.0f;
}

float GameplayOverlayContext::partyY() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->partyY() : 0.0f;
}

float GameplayOverlayContext::partyFootZ() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->partyFootZ() : 0.0f;
}

GameAudioSystem *GameplayOverlayContext::audioSystem() const
{
    return m_pAudioSystem;
}

const ItemTable *GameplayOverlayContext::itemTable() const
{
    return &m_session.data().itemTable();
}

const StandardItemEnchantTable *GameplayOverlayContext::standardItemEnchantTable() const
{
    return &m_session.data().standardItemEnchantTable();
}

const SpecialItemEnchantTable *GameplayOverlayContext::specialItemEnchantTable() const
{
    return &m_session.data().specialItemEnchantTable();
}

const ClassSkillTable *GameplayOverlayContext::classSkillTable() const
{
    return &m_session.data().classSkillTable();
}

const CharacterDollTable *GameplayOverlayContext::characterDollTable() const
{
    return &m_session.data().characterDollTable();
}

const CharacterInspectTable *GameplayOverlayContext::characterInspectTable() const
{
    return &m_session.data().characterInspectTable();
}

const RosterTable *GameplayOverlayContext::rosterTable() const
{
    return &m_session.data().rosterTable();
}

const ReadableScrollTable *GameplayOverlayContext::readableScrollTable() const
{
    return &m_session.data().readableScrollTable();
}

const ItemEquipPosTable *GameplayOverlayContext::itemEquipPosTable() const
{
    return &m_session.data().itemEquipPosTable();
}

const SpellTable *GameplayOverlayContext::spellTable() const
{
    return &m_session.data().spellTable();
}

const HouseTable *GameplayOverlayContext::houseTable() const
{
    return &m_session.data().houseTable();
}

const ChestTable *GameplayOverlayContext::chestTable() const
{
    return &m_session.data().chestTable();
}

const NpcDialogTable *GameplayOverlayContext::npcDialogTable() const
{
    return &m_session.data().npcDialogTable();
}

const MonsterTable *GameplayOverlayContext::monsterTable() const
{
    return &m_session.data().monsterTable();
}

GameplayUiController::CharacterScreenState &GameplayOverlayContext::characterScreen() const
{
    return uiController().characterScreen();
}

GameplayUiController::HeldInventoryItemState &GameplayOverlayContext::heldInventoryItem() const
{
    return uiController().heldInventoryItem();
}

GameplayUiController::ItemInspectOverlayState &GameplayOverlayContext::itemInspectOverlay() const
{
    return uiController().itemInspectOverlay();
}

GameplayUiController::CharacterInspectOverlayState &GameplayOverlayContext::characterInspectOverlay() const
{
    return uiController().characterInspectOverlay();
}

GameplayUiController::BuffInspectOverlayState &GameplayOverlayContext::buffInspectOverlay() const
{
    return uiController().buffInspectOverlay();
}

GameplayUiController::CharacterDetailOverlayState &GameplayOverlayContext::characterDetailOverlay() const
{
    return uiController().characterDetailOverlay();
}

GameplayUiController::ActorInspectOverlayState &GameplayOverlayContext::actorInspectOverlay() const
{
    return uiController().actorInspectOverlay();
}

GameplayUiController::SpellInspectOverlayState &GameplayOverlayContext::spellInspectOverlay() const
{
    return uiController().spellInspectOverlay();
}

GameplayUiController::ReadableScrollOverlayState &GameplayOverlayContext::readableScrollOverlay() const
{
    return uiController().readableScrollOverlay();
}

GameplayUiController::SpellbookState &GameplayOverlayContext::spellbook() const
{
    return uiController().spellbook();
}

GameplayUiController::UtilitySpellOverlayState &GameplayOverlayContext::utilitySpellOverlay() const
{
    return uiController().utilitySpellOverlay();
}

GameplayUiController::InventoryNestedOverlayState &GameplayOverlayContext::inventoryNestedOverlay() const
{
    return uiController().inventoryNestedOverlay();
}

GameplayUiController::HouseShopOverlayState &GameplayOverlayContext::houseShopOverlay() const
{
    return uiController().houseShopOverlay();
}

GameplayUiController::HouseBankState &GameplayOverlayContext::houseBankState() const
{
    return uiController().houseBankState();
}

GameplayUiController::JournalScreenState &GameplayOverlayContext::journalScreenState() const
{
    return uiController().journalScreen();
}

GameplayUiController::RestScreenState &GameplayOverlayContext::restScreenState() const
{
    return uiController().restScreen();
}

GameplayUiController::MenuScreenState &GameplayOverlayContext::menuScreenState() const
{
    return uiController().menuScreen();
}

GameplayUiController::ControlsScreenState &GameplayOverlayContext::controlsScreenState() const
{
    return uiController().controlsScreen();
}

GameplayUiController::KeyboardScreenState &GameplayOverlayContext::keyboardScreenState() const
{
    return uiController().keyboardScreen();
}

GameplayUiController::VideoOptionsScreenState &GameplayOverlayContext::videoOptionsScreenState() const
{
    return uiController().videoOptionsScreen();
}

GameplayUiController::SaveGameScreenState &GameplayOverlayContext::saveGameScreenState() const
{
    return uiController().saveGameScreen();
}

GameplayUiController::LoadGameScreenState &GameplayOverlayContext::loadGameScreenState() const
{
    return uiController().loadGameScreen();
}

const GameplayUiController::CharacterScreenState &GameplayOverlayContext::characterScreenReadOnly() const
{
    return uiController().characterScreen();
}

const GameplayUiController::ItemInspectOverlayState &GameplayOverlayContext::itemInspectOverlayReadOnly() const
{
    return uiController().itemInspectOverlay();
}

const GameplayUiController::CharacterInspectOverlayState &GameplayOverlayContext::characterInspectOverlayReadOnly() const
{
    return uiController().characterInspectOverlay();
}

const GameplayUiController::BuffInspectOverlayState &GameplayOverlayContext::buffInspectOverlayReadOnly() const
{
    return uiController().buffInspectOverlay();
}

const GameplayUiController::CharacterDetailOverlayState &GameplayOverlayContext::characterDetailOverlayReadOnly() const
{
    return uiController().characterDetailOverlay();
}

const GameplayUiController::ActorInspectOverlayState &GameplayOverlayContext::actorInspectOverlayReadOnly() const
{
    return uiController().actorInspectOverlay();
}

const GameplayUiController::SpellInspectOverlayState &GameplayOverlayContext::spellInspectOverlayReadOnly() const
{
    return uiController().spellInspectOverlay();
}

const GameplayUiController::ReadableScrollOverlayState &GameplayOverlayContext::readableScrollOverlayReadOnly() const
{
    return uiController().readableScrollOverlay();
}

const GameplayUiController::SpellbookState &GameplayOverlayContext::spellbookReadOnly() const
{
    return uiController().spellbook();
}

const GameplayUiController::UtilitySpellOverlayState &GameplayOverlayContext::utilitySpellOverlayReadOnly() const
{
    return uiController().utilitySpellOverlay();
}

const GameplayUiController::JournalScreenState &GameplayOverlayContext::journalScreenStateReadOnly() const
{
    return uiController().journalScreen();
}

const JournalQuestTable *GameplayOverlayContext::journalQuestTable() const
{
    return &m_session.data().journalQuestTable();
}

const JournalHistoryTable *GameplayOverlayContext::journalHistoryTable() const
{
    return &m_session.data().journalHistoryTable();
}

const JournalAutonoteTable *GameplayOverlayContext::journalAutonoteTable() const
{
    return &m_session.data().journalAutonoteTable();
}

const std::string &GameplayOverlayContext::currentMapFileName() const
{
    return m_sceneAdapter.currentMapFileName();
}

float GameplayOverlayContext::gameplayCameraYawRadians() const
{
    return m_sceneAdapter.gameplayCameraYawRadians();
}

const std::vector<uint8_t> *GameplayOverlayContext::journalMapFullyRevealedCells() const
{
    return m_sceneAdapter.journalMapFullyRevealedCells();
}

const std::vector<uint8_t> *GameplayOverlayContext::journalMapPartiallyRevealedCells() const
{
    return m_sceneAdapter.journalMapPartiallyRevealedCells();
}

EventDialogContent &GameplayOverlayContext::activeEventDialog() const
{
    return uiController().eventDialog().content;
}

std::string &GameplayOverlayContext::statusBarEventText() const
{
    return uiController().statusBar().eventText;
}

float &GameplayOverlayContext::statusBarEventRemainingSeconds() const
{
    return uiController().statusBar().eventRemainingSeconds;
}

const std::string &GameplayOverlayContext::statusBarHoverText() const
{
    return uiController().statusBar().hoverText;
}

std::string &GameplayOverlayContext::mutableStatusBarHoverText() const
{
    return uiController().statusBar().hoverText;
}

bool &GameplayOverlayContext::closeOverlayLatch() const
{
    return interactionState().closeOverlayLatch;
}

bool &GameplayOverlayContext::restToggleLatch() const
{
    return interactionState().restToggleLatch;
}

bool &GameplayOverlayContext::restClickLatch() const
{
    return interactionState().restClickLatch;
}

GameplayRestPointerTarget &GameplayOverlayContext::restPressedTarget() const
{
    return interactionState().restPressedTarget;
}

bool &GameplayOverlayContext::gameplayHudClickLatch() const
{
    return interactionState().gameplayHudClickLatch;
}

GameplayHudPointerTarget &GameplayOverlayContext::gameplayHudPressedTarget() const
{
    return interactionState().gameplayHudPressedTarget;
}

bool &GameplayOverlayContext::menuToggleLatch() const
{
    return interactionState().menuToggleLatch;
}

bool &GameplayOverlayContext::menuClickLatch() const
{
    return interactionState().menuClickLatch;
}

GameplayMenuPointerTarget &GameplayOverlayContext::menuPressedTarget() const
{
    return interactionState().menuPressedTarget;
}

bool &GameplayOverlayContext::controlsToggleLatch() const
{
    return interactionState().controlsToggleLatch;
}

bool &GameplayOverlayContext::controlsClickLatch() const
{
    return interactionState().controlsClickLatch;
}

GameplayControlsPointerTarget &GameplayOverlayContext::controlsPressedTarget() const
{
    return interactionState().controlsPressedTarget;
}

bool &GameplayOverlayContext::controlsSliderDragActive() const
{
    return interactionState().controlsSliderDragActive;
}

GameplayControlsPointerTargetType &GameplayOverlayContext::controlsDraggedSlider() const
{
    return interactionState().controlsDraggedSlider;
}

bool &GameplayOverlayContext::keyboardToggleLatch() const
{
    return interactionState().keyboardToggleLatch;
}

bool &GameplayOverlayContext::keyboardClickLatch() const
{
    return interactionState().keyboardClickLatch;
}

GameplayKeyboardPointerTarget &GameplayOverlayContext::keyboardPressedTarget() const
{
    return interactionState().keyboardPressedTarget;
}

bool &GameplayOverlayContext::videoOptionsToggleLatch() const
{
    return interactionState().videoOptionsToggleLatch;
}

bool &GameplayOverlayContext::videoOptionsClickLatch() const
{
    return interactionState().videoOptionsClickLatch;
}

GameplayVideoOptionsPointerTarget &GameplayOverlayContext::videoOptionsPressedTarget() const
{
    return interactionState().videoOptionsPressedTarget;
}

bool &GameplayOverlayContext::saveGameToggleLatch() const
{
    return interactionState().saveGameToggleLatch;
}

bool &GameplayOverlayContext::saveGameClickLatch() const
{
    return interactionState().saveGameClickLatch;
}

GameplaySaveLoadPointerTarget &GameplayOverlayContext::saveGamePressedTarget() const
{
    return interactionState().saveGamePressedTarget;
}

bool &GameplayOverlayContext::characterClickLatch() const
{
    return interactionState().characterClickLatch;
}

GameplayCharacterPointerTarget &GameplayOverlayContext::characterPressedTarget() const
{
    return interactionState().characterPressedTarget;
}

bool &GameplayOverlayContext::characterMemberCycleLatch() const
{
    return interactionState().characterMemberCycleLatch;
}

std::optional<size_t> &GameplayOverlayContext::pendingCharacterDismissMemberIndex() const
{
    return interactionState().pendingCharacterDismissMemberIndex;
}

uint64_t &GameplayOverlayContext::pendingCharacterDismissExpiresTicks() const
{
    return interactionState().pendingCharacterDismissExpiresTicks;
}

bool &GameplayOverlayContext::spellbookClickLatch() const
{
    return interactionState().spellbookClickLatch;
}

GameplaySpellbookPointerTarget &GameplayOverlayContext::spellbookPressedTarget() const
{
    return interactionState().spellbookPressedTarget;
}

uint64_t &GameplayOverlayContext::lastSpellbookSpellClickTicks() const
{
    return interactionState().lastSpellbookSpellClickTicks;
}

uint32_t &GameplayOverlayContext::lastSpellbookClickedSpellId() const
{
    return interactionState().lastSpellbookClickedSpellId;
}

bool &GameplayOverlayContext::utilitySpellClickLatch() const
{
    return interactionState().utilitySpellClickLatch;
}

GameplayUtilitySpellPointerTarget &GameplayOverlayContext::utilitySpellPressedTarget() const
{
    return interactionState().utilitySpellPressedTarget;
}

std::array<bool, 39> &GameplayOverlayContext::saveGameEditKeyLatches() const
{
    return interactionState().saveGameEditKeyLatches;
}

bool &GameplayOverlayContext::saveGameEditBackspaceLatch() const
{
    return interactionState().saveGameEditBackspaceLatch;
}

uint64_t &GameplayOverlayContext::lastSaveGameSlotClickTicks() const
{
    return interactionState().lastSaveGameSlotClickTicks;
}

std::optional<size_t> &GameplayOverlayContext::lastSaveGameClickedSlotIndex() const
{
    return interactionState().lastSaveGameClickedSlotIndex;
}

bool &GameplayOverlayContext::journalToggleLatch() const
{
    return interactionState().journalToggleLatch;
}

bool &GameplayOverlayContext::journalClickLatch() const
{
    return interactionState().journalClickLatch;
}

GameplayJournalPointerTarget &GameplayOverlayContext::journalPressedTarget() const
{
    return interactionState().journalPressedTarget;
}

bool &GameplayOverlayContext::journalMapKeyZoomLatch() const
{
    return interactionState().journalMapKeyZoomLatch;
}

bool &GameplayOverlayContext::dialogueClickLatch() const
{
    return interactionState().dialogueClickLatch;
}

GameplayDialoguePointerTarget &GameplayOverlayContext::dialoguePressedTarget() const
{
    return interactionState().dialoguePressedTarget;
}

bool &GameplayOverlayContext::houseShopClickLatch() const
{
    return interactionState().houseShopClickLatch;
}

size_t &GameplayOverlayContext::houseShopPressedSlotIndex() const
{
    return interactionState().houseShopPressedSlotIndex;
}

bool &GameplayOverlayContext::chestClickLatch() const
{
    return interactionState().chestClickLatch;
}

bool &GameplayOverlayContext::chestItemClickLatch() const
{
    return interactionState().chestItemClickLatch;
}

GameplayChestPointerTarget &GameplayOverlayContext::chestPressedTarget() const
{
    return interactionState().chestPressedTarget;
}

bool &GameplayOverlayContext::inventoryNestedOverlayItemClickLatch() const
{
    return interactionState().inventoryNestedOverlayItemClickLatch;
}

std::array<bool, 10> &GameplayOverlayContext::houseBankDigitLatches() const
{
    return interactionState().houseBankDigitLatches;
}

bool &GameplayOverlayContext::houseBankBackspaceLatch() const
{
    return interactionState().houseBankBackspaceLatch;
}

bool &GameplayOverlayContext::houseBankConfirmLatch() const
{
    return interactionState().houseBankConfirmLatch;
}

bool &GameplayOverlayContext::lootChestItemLatch() const
{
    return interactionState().lootChestItemLatch;
}

bool &GameplayOverlayContext::chestSelectUpLatch() const
{
    return interactionState().chestSelectUpLatch;
}

bool &GameplayOverlayContext::chestSelectDownLatch() const
{
    return interactionState().chestSelectDownLatch;
}

bool &GameplayOverlayContext::eventDialogSelectUpLatch() const
{
    return interactionState().eventDialogSelectUpLatch;
}

bool &GameplayOverlayContext::eventDialogSelectDownLatch() const
{
    return interactionState().eventDialogSelectDownLatch;
}

bool &GameplayOverlayContext::eventDialogAcceptLatch() const
{
    return interactionState().eventDialogAcceptLatch;
}

std::array<bool, 5> &GameplayOverlayContext::eventDialogPartySelectLatches() const
{
    return interactionState().eventDialogPartySelectLatches;
}

bool &GameplayOverlayContext::activateInspectLatch() const
{
    return interactionState().activateInspectLatch;
}

size_t &GameplayOverlayContext::chestSelectionIndex() const
{
    return interactionState().chestSelectionIndex;
}

size_t &GameplayOverlayContext::eventDialogSelectionIndex() const
{
    return uiController().eventDialog().selectionIndex;
}

bool &GameplayOverlayContext::partyPortraitClickLatch() const
{
    return interactionState().partyPortraitClickLatch;
}

std::optional<size_t> &GameplayOverlayContext::partyPortraitPressedIndex() const
{
    return interactionState().partyPortraitPressedIndex;
}

uint64_t &GameplayOverlayContext::lastPartyPortraitClickTicks() const
{
    return interactionState().lastPartyPortraitClickTicks;
}

std::optional<size_t> &GameplayOverlayContext::lastPartyPortraitClickedIndex() const
{
    return interactionState().lastPartyPortraitClickedIndex;
}

bool GameplayOverlayContext::trySelectPartyMember(size_t memberIndex, bool requireGameplayReady)
{
    return m_sceneAdapter.trySelectPartyMember(memberIndex, requireGameplayReady);
}

size_t GameplayOverlayContext::selectedCharacterScreenSourceIndex() const
{
    const Party *pParty = partyReadOnly();

    if (pParty == nullptr)
    {
        return 0;
    }

    const GameplayUiController::CharacterScreenState &screen = characterScreenReadOnly();
    return isAdventurersInnCharacterSourceActive() ? screen.sourceIndex : pParty->activeMemberIndex();
}

const Character *GameplayOverlayContext::selectedCharacterScreenCharacter() const
{
    const Party *pParty = partyReadOnly();

    if (pParty == nullptr)
    {
        return nullptr;
    }

    if (isAdventurersInnCharacterSourceActive())
    {
        return pParty->adventurersInnCharacter(characterScreenReadOnly().sourceIndex);
    }

    return pParty->activeMember();
}

bool GameplayOverlayContext::isAdventurersInnCharacterSourceActive() const
{
    const GameplayUiController::CharacterScreenState &screen = characterScreenReadOnly();
    return screen.open && screen.source == GameplayUiController::CharacterScreenSource::AdventurersInn;
}

bool GameplayOverlayContext::isAdventurersInnScreenActive() const
{
    const GameplayUiController::CharacterScreenState &screen = characterScreenReadOnly();
    return isAdventurersInnCharacterSourceActive() && screen.adventurersInnRosterOverlayOpen;
}

bool GameplayOverlayContext::isReadOnlyAdventurersInnCharacterViewActive() const
{
    return isAdventurersInnCharacterSourceActive() && !characterScreenReadOnly().adventurersInnRosterOverlayOpen;
}

bool GameplayOverlayContext::activeMemberKnowsSpell(uint32_t spellId) const
{
    const Character *pMember = partyReadOnly() != nullptr ? partyReadOnly()->activeMember() : nullptr;
    return pMember != nullptr && pMember->knowsSpell(spellId);
}

bool GameplayOverlayContext::activeMemberHasSpellbookSchool(GameplayUiController::SpellbookSchool school) const
{
    const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(school);
    const Character *pMember = partyReadOnly() != nullptr ? partyReadOnly()->activeMember() : nullptr;

    if (pDefinition == nullptr || pMember == nullptr)
    {
        return false;
    }

    const std::optional<std::string> skillName = resolveMagicSkillName(pDefinition->firstSpellId);

    if (!skillName)
    {
        return false;
    }

    const CharacterSkill *pSkill = pMember->findSkill(*skillName);
    return pSkill != nullptr && pSkill->level > 0 && pSkill->mastery != SkillMastery::None;
}

void GameplayOverlayContext::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    uiController().setStatusBarEvent(text, durationSeconds);
}

void GameplayOverlayContext::openRestOverlay()
{
    if (party() == nullptr || worldRuntime() == nullptr)
    {
        return;
    }

    closeSpellbookOverlay();
    closeMenuOverlay();
    closeReadableScrollOverlay();
    closeInventoryNestedOverlay();
    uiController().characterScreen() = {};
    uiController().restScreen() = {};
    uiController().restScreen().active = true;
    interactionState().restClickLatch = false;
    interactionState().restPressedTarget = {};
}

void GameplayOverlayContext::openSpellbookOverlay()
{
    GameplayUiController::SpellbookSchool school = GameplayUiController::SpellbookSchool::Fire;

    for (const SpellbookSchoolUiDefinition &definition : spellbookSchoolUiDefinitions())
    {
        if (activeMemberHasSpellbookSchool(definition.school))
        {
            school = definition.school;
            break;
        }
    }

    const Character *pCaster = partyReadOnly() != nullptr ? partyReadOnly()->activeMember() : nullptr;

    if (pCaster != nullptr && !pCaster->quickSpellName.empty() && spellTable() != nullptr)
    {
        const SpellEntry *pSpellEntry = spellTable()->findByName(pCaster->quickSpellName);

        if (pSpellEntry != nullptr)
        {
            const SpellbookSchoolUiDefinition *pDefinition =
                findSpellbookSchoolUiDefinitionForSpellId(uint32_t(pSpellEntry->id));

            if (pDefinition != nullptr && activeMemberHasSpellbookSchool(pDefinition->school))
            {
                school = pDefinition->school;
            }
        }
    }

    uiController().openSpellbook(school);
    uiController().spellbook().selectedSpellId = 0;
    interactionState().spellbookClickLatch = false;
    interactionState().spellbookPressedTarget = {};
    interactionState().lastSpellbookSpellClickTicks = 0;
    interactionState().lastSpellbookClickedSpellId = 0;

    if (m_pAudioSystem != nullptr)
    {
        m_pAudioSystem->playCommonSound(SoundId::OpenBook, GameAudioSystem::PlaybackGroup::Ui);
    }
}

void GameplayOverlayContext::openChestTransferInventoryOverlay()
{
    uiController().openInventoryNestedOverlay(GameplayUiController::InventoryNestedOverlayMode::ChestTransfer);
    interactionState().inventoryNestedOverlayItemClickLatch = false;
}

void GameplayOverlayContext::toggleCharacterInventoryScreen()
{
    GameplayUiController::CharacterScreenState &characterScreen = uiController().characterScreen();
    characterScreen.open = !characterScreen.open;

    if (characterScreen.open)
    {
        characterScreen.page = GameplayUiController::CharacterPage::Inventory;
        characterScreen.source = GameplayUiController::CharacterScreenSource::Party;
        characterScreen.sourceIndex = 0;
        characterScreen.dollJewelryOverlayOpen = false;
        characterScreen.adventurersInnRosterOverlayOpen = false;
        closeSpellbookOverlay();
    }
    else
    {
        characterScreen.dollJewelryOverlayOpen = false;
        characterScreen.adventurersInnRosterOverlayOpen = false;
    }
}

void GameplayOverlayContext::handleDialogueCloseRequest()
{
    if (houseBankState().inputActive())
    {
        returnToHouseBankMainDialogShared();
        return;
    }

    if (inventoryNestedOverlay().active && currentHudScreenState() == GameplayHudScreenState::Dialogue)
    {
        closeInventoryNestedOverlay();
        return;
    }

    if (houseShopOverlay().active)
    {
        uiController().closeHouseShopOverlay();
        return;
    }

    EventRuntimeState *pEventRuntimeState = worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr)
    {
        closeActiveEventDialogShared();
        interactionState().activateInspectLatch = true;
        return;
    }

    GameplayDialogController::Context context = buildDialogContext(*pEventRuntimeState);
    const GameplayDialogController::CloseDialogRequestResult result =
        m_session.gameplayDialogController().handleDialogueCloseRequest(context);

    if (result.shouldOpenPendingEventDialog)
    {
        presentPendingEventDialogShared(result.previousMessageCount, result.allowNpcFallbackContent);
    }
    else if (result.shouldCloseActiveDialog)
    {
        closeActiveEventDialogShared();
        interactionState().activateInspectLatch = true;
    }
}

void GameplayOverlayContext::closeRestOverlay()
{
    uiController().restScreen() = {};
    interactionState().closeOverlayLatch = false;
    interactionState().restClickLatch = false;
    interactionState().restPressedTarget = {};
}

void GameplayOverlayContext::openMenuOverlay()
{
    closeSpellbookOverlay();
    closeReadableScrollOverlay();
    closeInventoryNestedOverlay();
    uiController().characterScreen() = {};
    uiController().restScreen() = {};
    uiController().controlsScreen() = {};
    uiController().keyboardScreen() = {};
    uiController().videoOptionsScreen() = {};
    uiController().saveGameScreen() = {};
    uiController().loadGameScreen() = {};
    uiController().journalScreen().active = false;
    uiController().menuScreen() = {};
    uiController().menuScreen().active = true;
    interactionState().menuToggleLatch = false;
    interactionState().menuClickLatch = false;
    interactionState().menuPressedTarget = {};
    interactionState().controlsToggleLatch = false;
    interactionState().controlsClickLatch = false;
    interactionState().controlsPressedTarget = {};
    interactionState().controlsSliderDragActive = false;
    interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    interactionState().keyboardToggleLatch = false;
    interactionState().keyboardClickLatch = false;
    interactionState().keyboardPressedTarget = {};
    interactionState().videoOptionsToggleLatch = false;
    interactionState().videoOptionsClickLatch = false;
    interactionState().videoOptionsPressedTarget = {};
    interactionState().saveGameToggleLatch = false;
    interactionState().saveGameClickLatch = false;
    interactionState().saveGamePressedTarget = {};
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::closeMenuOverlay()
{
    uiController().menuScreen() = {};
    interactionState().menuToggleLatch = false;
    interactionState().menuClickLatch = false;
    interactionState().menuPressedTarget = {};
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::openControlsOverlay()
{
    uiController().menuScreen().active = false;
    interactionState().menuToggleLatch = false;
    interactionState().menuClickLatch = false;
    interactionState().menuPressedTarget = {};
    uiController().controlsScreen() = {};
    uiController().controlsScreen().active = true;
    interactionState().controlsToggleLatch = false;
    interactionState().controlsClickLatch = false;
    interactionState().controlsPressedTarget = {};
    interactionState().controlsSliderDragActive = false;
    interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    uiController().keyboardScreen() = {};
    interactionState().keyboardToggleLatch = false;
    interactionState().keyboardClickLatch = false;
    interactionState().keyboardPressedTarget = {};
    uiController().videoOptionsScreen() = {};
    interactionState().videoOptionsToggleLatch = false;
    interactionState().videoOptionsClickLatch = false;
    interactionState().videoOptionsPressedTarget = {};
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::closeControlsOverlay()
{
    uiController().controlsScreen() = {};
    interactionState().controlsToggleLatch = false;
    interactionState().controlsClickLatch = false;
    interactionState().controlsPressedTarget = {};
    interactionState().controlsSliderDragActive = false;
    interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    uiController().keyboardScreen() = {};
    interactionState().keyboardToggleLatch = false;
    interactionState().keyboardClickLatch = false;
    interactionState().keyboardPressedTarget = {};
    uiController().videoOptionsScreen() = {};
    interactionState().videoOptionsToggleLatch = false;
    interactionState().videoOptionsClickLatch = false;
    interactionState().videoOptionsPressedTarget = {};
    uiController().menuScreen() = {};
    uiController().menuScreen().active = true;
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::openKeyboardOverlay()
{
    uiController().controlsScreen() = {};
    interactionState().controlsToggleLatch = false;
    interactionState().controlsClickLatch = false;
    interactionState().controlsPressedTarget = {};
    interactionState().controlsSliderDragActive = false;
    interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    uiController().keyboardScreen() = {};
    uiController().keyboardScreen().active = true;
    interactionState().keyboardToggleLatch = false;
    interactionState().keyboardClickLatch = false;
    interactionState().keyboardPressedTarget = {};
    uiController().videoOptionsScreen() = {};
    interactionState().videoOptionsToggleLatch = false;
    interactionState().videoOptionsClickLatch = false;
    interactionState().videoOptionsPressedTarget = {};
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::closeKeyboardOverlayToControls()
{
    uiController().keyboardScreen() = {};
    interactionState().keyboardToggleLatch = false;
    interactionState().keyboardClickLatch = false;
    interactionState().keyboardPressedTarget = {};
    uiController().controlsScreen() = {};
    uiController().controlsScreen().active = true;
    interactionState().controlsToggleLatch = false;
    interactionState().controlsClickLatch = false;
    interactionState().controlsPressedTarget = {};
    interactionState().controlsSliderDragActive = false;
    interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::closeKeyboardOverlayToMenu()
{
    uiController().keyboardScreen() = {};
    interactionState().keyboardToggleLatch = false;
    interactionState().keyboardClickLatch = false;
    interactionState().keyboardPressedTarget = {};
    uiController().controlsScreen() = {};
    interactionState().controlsToggleLatch = false;
    interactionState().controlsClickLatch = false;
    interactionState().controlsPressedTarget = {};
    interactionState().controlsSliderDragActive = false;
    interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    uiController().menuScreen() = {};
    uiController().menuScreen().active = true;
    interactionState().menuToggleLatch = false;
    interactionState().menuClickLatch = false;
    interactionState().menuPressedTarget = {};
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::openVideoOptionsOverlay()
{
    uiController().controlsScreen().active = false;
    interactionState().controlsToggleLatch = false;
    interactionState().controlsClickLatch = false;
    interactionState().controlsPressedTarget = {};
    uiController().keyboardScreen() = {};
    interactionState().keyboardToggleLatch = false;
    interactionState().keyboardClickLatch = false;
    interactionState().keyboardPressedTarget = {};
    interactionState().controlsSliderDragActive = false;
    interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    uiController().videoOptionsScreen() = {};
    uiController().videoOptionsScreen().active = true;
    interactionState().videoOptionsToggleLatch = false;
    interactionState().videoOptionsClickLatch = false;
    interactionState().videoOptionsPressedTarget = {};
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::closeVideoOptionsOverlay()
{
    uiController().videoOptionsScreen() = {};
    interactionState().videoOptionsToggleLatch = false;
    interactionState().videoOptionsClickLatch = false;
    interactionState().videoOptionsPressedTarget = {};
    uiController().keyboardScreen() = {};
    interactionState().keyboardToggleLatch = false;
    interactionState().keyboardClickLatch = false;
    interactionState().keyboardPressedTarget = {};
    uiController().controlsScreen() = {};
    uiController().controlsScreen().active = true;
    interactionState().controlsToggleLatch = false;
    interactionState().controlsClickLatch = false;
    interactionState().controlsPressedTarget = {};
    interactionState().controlsSliderDragActive = false;
    interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::openSaveGameOverlay()
{
    uiController().menuScreen().active = false;
    interactionState().menuToggleLatch = false;
    interactionState().menuClickLatch = false;
    interactionState().menuPressedTarget = {};
    uiController().controlsScreen() = {};
    interactionState().controlsToggleLatch = false;
    interactionState().controlsClickLatch = false;
    interactionState().controlsPressedTarget = {};
    interactionState().controlsSliderDragActive = false;
    interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    uiController().videoOptionsScreen() = {};
    interactionState().videoOptionsToggleLatch = false;
    interactionState().videoOptionsClickLatch = false;
    interactionState().videoOptionsPressedTarget = {};
    uiController().loadGameScreen() = {};
    uiController().saveGameScreen() = {};
    uiController().saveGameScreen().active = true;
    refreshSaveGameSlots(uiController().saveGameScreen(), m_session.data().mapEntries());
    interactionState().saveGameToggleLatch = false;
    interactionState().saveGameClickLatch = false;
    interactionState().saveGamePressedTarget = {};
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::closeSaveGameOverlay()
{
    uiController().saveGameScreen() = {};
    interactionState().saveGameToggleLatch = false;
    interactionState().saveGameClickLatch = false;
    interactionState().saveGamePressedTarget = {};
    uiController().menuScreen() = {};
    uiController().menuScreen().active = true;
    interactionState().closeOverlayLatch = false;
}

void GameplayOverlayContext::requestOpenNewGameScreen()
{
    m_session.requestOpenNewGameScreen();
}

void GameplayOverlayContext::requestOpenLoadGameScreen()
{
    m_session.requestOpenLoadGameScreen();
}

void GameplayOverlayContext::openJournalOverlay()
{
    closeSpellbookOverlay();
    closeMenuOverlay();
    closeReadableScrollOverlay();
    closeInventoryNestedOverlay();
    uiController().characterScreen() = {};
    uiController().restScreen() = {};

    GameplayUiController::JournalScreenState &journalScreen = uiController().journalScreen();
    journalScreen.active = true;
    journalScreen.view = GameplayUiController::JournalView::Map;
    journalScreen.notesCategory = GameplayUiController::JournalNotesCategory::Potion;
    journalScreen.questPage = 0;
    journalScreen.storyPage = 0;
    journalScreen.notesPage = 0;
    journalScreen.hoverAnimationElapsedSeconds = 0.0f;
    journalScreen.mapDragActive = false;
    journalScreen.mapDragStartMouseX = 0.0f;
    journalScreen.mapDragStartMouseY = 0.0f;
    journalScreen.mapDragStartCenterX = 0.0f;
    journalScreen.mapDragStartCenterY = 0.0f;
    journalScreen.cachedMapValid = false;
    journalScreen.mapCenterX = partyX();
    journalScreen.mapCenterY = partyY();
    clampJournalMapState(journalScreen);
    interactionState().journalToggleLatch = false;
    interactionState().journalClickLatch = false;
    interactionState().journalPressedTarget = {};
    interactionState().journalMapKeyZoomLatch = false;
    interactionState().closeOverlayLatch = false;

    if (m_pAudioSystem != nullptr)
    {
        m_pAudioSystem->playCommonSound(SoundId::OpenBook, GameAudioSystem::PlaybackGroup::Ui);
    }
}

void GameplayOverlayContext::closeJournalOverlay()
{
    GameplayUiController::JournalScreenState &journalScreen = uiController().journalScreen();
    const bool wasActive = journalScreen.active;
    journalScreen.active = false;
    journalScreen.hoverAnimationElapsedSeconds = 0.0f;
    journalScreen.mapDragActive = false;
    journalScreen.mapDragStartMouseX = 0.0f;
    journalScreen.mapDragStartMouseY = 0.0f;
    journalScreen.mapDragStartCenterX = 0.0f;
    journalScreen.mapDragStartCenterY = 0.0f;
    journalScreen.cachedMapValid = false;
    interactionState().journalToggleLatch = false;
    interactionState().journalClickLatch = false;
    interactionState().journalPressedTarget = {};
    interactionState().journalMapKeyZoomLatch = false;
    interactionState().closeOverlayLatch = false;

    if (wasActive && m_pAudioSystem != nullptr)
    {
        m_pAudioSystem->playCommonSound(SoundId::CloseBook, GameAudioSystem::PlaybackGroup::Ui);
    }
}

void GameplayOverlayContext::ensurePendingEventDialogPresented(bool allowNpcFallbackContent)
{
    if (activeEventDialog().isActive)
    {
        return;
    }

    EventRuntimeState *pEventRuntimeState = worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr
        || !pEventRuntimeState->pendingDialogueContext
        || pEventRuntimeState->pendingDialogueContext->kind == DialogueContextKind::None)
    {
        return;
    }

    presentPendingEventDialogShared(pEventRuntimeState->messages.size(), allowNpcFallbackContent);
}

void GameplayOverlayContext::executeActiveDialogAction()
{
    m_sceneAdapter.executeActiveDialogAction();
}

void GameplayOverlayContext::refreshHouseBankInputDialog()
{
    GameplayDialogUiFlowState state = dialogUiFlowState();
    ::OpenYAMM::Game::refreshHouseBankInputDialog(
        state,
        worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr,
        [this](EventRuntimeState &eventRuntimeState)
        {
            return buildDialogContext(eventRuntimeState);
        },
        (SDL_GetTicks() / 500u) % 2u == 0u);
}

void GameplayOverlayContext::confirmHouseBankInput()
{
    GameplayDialogUiFlowState state = dialogUiFlowState();
    const GameplayDialogController::Result result = ::OpenYAMM::Game::confirmHouseBankInput(
        state,
        worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr,
        [this](EventRuntimeState &eventRuntimeState)
        {
            return buildDialogContext(eventRuntimeState);
        });

    if (result.shouldOpenPendingEventDialog)
    {
        presentPendingEventDialogShared(result.previousMessageCount, result.allowNpcFallbackContent);
    }
}

void GameplayOverlayContext::closeInventoryNestedOverlay()
{
    uiController().closeInventoryNestedOverlay();
    interactionState().inventoryNestedOverlayItemClickLatch = false;
}

bool GameplayOverlayContext::tryAutoPlaceHeldInventoryItemOnPartyMember(size_t memberIndex, bool showFailureStatus)
{
    GameplayUiController::HeldInventoryItemState &heldItem = uiController().heldInventoryItem();
    Party *pParty = party();

    if (!heldItem.active || pParty == nullptr)
    {
        return false;
    }

    if (!pParty->tryAutoPlaceItemInMemberInventory(memberIndex, heldItem.item))
    {
        if (showFailureStatus)
        {
            setStatusBarEvent(pParty->lastStatus().empty() ? "Inventory full" : pParty->lastStatus());
        }

        return false;
    }

    heldItem = {};
    return true;
}

void GameplayOverlayContext::closeSpellbookOverlay(const std::string &statusText)
{
    const bool wasActive = uiController().spellbook().active;
    uiController().closeSpellbook();
    interactionState().spellbookClickLatch = false;
    interactionState().spellbookPressedTarget = {};
    interactionState().lastSpellbookSpellClickTicks = 0;
    interactionState().lastSpellbookClickedSpellId = 0;

    if (wasActive && m_pAudioSystem != nullptr)
    {
        m_pAudioSystem->playCommonSound(SoundId::CloseBook, GameAudioSystem::PlaybackGroup::Ui);
    }

    if (!statusText.empty())
    {
        setStatusBarEvent(statusText);
    }
}

bool GameplayOverlayContext::tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen)
{
    return m_sceneAdapter.tryUseHeldItemOnPartyMember(memberIndex, keepCharacterScreenOpen);
}

void GameplayOverlayContext::updateReadableScrollOverlayForHeldItem(
    size_t memberIndex,
    const GameplayCharacterPointerTarget &pointerTarget,
    bool isLeftMousePressed)
{
    GameplayUiController::ReadableScrollOverlayState &overlay = uiController().readableScrollOverlay();
    overlay = {};

    if (!isLeftMousePressed
        || !heldInventoryItem().active
        || itemTable() == nullptr
        || party() == nullptr
        || (pointerTarget.type != GameplayCharacterPointerTargetType::EquipmentSlot
            && pointerTarget.type != GameplayCharacterPointerTargetType::DollPanel))
    {
        return;
    }

    const InventoryItemUseAction useAction =
        InventoryItemUseRuntime::classifyItemUse(heldInventoryItem().item, *itemTable());

    if (useAction != InventoryItemUseAction::ReadMessageScroll)
    {
        return;
    }

    const InventoryItemUseResult useResult =
        InventoryItemUseRuntime::useItemOnMember(
            *party(),
            memberIndex,
            heldInventoryItem().item,
            *itemTable(),
            readableScrollTable());

    if (!useResult.handled || useResult.action != InventoryItemUseAction::ReadMessageScroll)
    {
        return;
    }

    overlay.active = true;
    overlay.title = useResult.readableTitle;
    overlay.body = useResult.readableBody;
}

void GameplayOverlayContext::closeReadableScrollOverlay()
{
    uiController().closeReadableScrollOverlay();
}

void GameplayOverlayContext::triggerPortraitFaceAnimation(size_t memberIndex, FaceAnimationId animationId)
{
    m_sceneAdapter.triggerPortraitFaceAnimation(memberIndex, animationId);
}

void GameplayOverlayContext::playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
{
    m_sceneAdapter.playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
}

bool GameplayOverlayContext::tryCastSpellFromMember(size_t casterMemberIndex, uint32_t spellId, const std::string &spellName)
{
    return m_sceneAdapter.tryCastSpellFromMember(casterMemberIndex, spellId, spellName);
}

bool GameplayOverlayContext::tryCastSpellRequest(
    const PartySpellCastRequest &request,
    const std::string &spellName)
{
    return m_sceneAdapter.tryCastSpellRequest(request, spellName);
}

void GameplayOverlayContext::resetUtilitySpellOverlayInteractionState()
{
    interactionState().utilitySpellClickLatch = false;
    interactionState().utilitySpellPressedTarget = {};
}

void GameplayOverlayContext::resetInventoryNestedOverlayInteractionState()
{
    interactionState().inventoryNestedOverlayClickLatch = false;
    interactionState().inventoryNestedOverlayPressedTarget = {};
    interactionState().inventoryNestedOverlayItemClickLatch = false;
}

void GameplayOverlayContext::resetLootOverlayInteractionState()
{
    closeOverlayLatch() = false;
    chestClickLatch() = false;
    chestItemClickLatch() = false;
    chestPressedTarget() = {};
    closeInventoryNestedOverlay();
    lootChestItemLatch() = false;
    chestSelectUpLatch() = false;
    chestSelectDownLatch() = false;
    chestSelectionIndex() = 0;
    resetInventoryNestedOverlayInteractionState();
}

GameSettings &GameplayOverlayContext::mutableSettings() const
{
    return *m_pSettings;
}

const std::array<uint8_t, SDL_SCANCODE_COUNT> &GameplayOverlayContext::previousKeyboardState() const
{
    return m_session.previousKeyboardState();
}

void GameplayOverlayContext::commitSettingsChange()
{
    if (m_pSettings != nullptr)
    {
        m_session.notifySettingsChanged(*m_pSettings);
    }
}

bool GameplayOverlayContext::trySaveToSelectedGameSlot()
{
    return m_sceneAdapter.trySaveToSelectedGameSlot();
}

int GameplayOverlayContext::restFoodRequired() const
{
    return m_sceneAdapter.restFoodRequired();
}

const GameSettings &GameplayOverlayContext::settingsSnapshot() const
{
    return *m_pSettings;
}

bool GameplayOverlayContext::isControlsRenderButtonPressed(GameplayControlsRenderButton button) const
{
    if (!controlsClickLatch())
    {
        return false;
    }

    switch (button)
    {
        case GameplayControlsRenderButton::TurnRate16:
            return controlsPressedTarget().type == GameplayControlsPointerTargetType::TurnRate16Button;
        case GameplayControlsRenderButton::TurnRate32:
            return controlsPressedTarget().type == GameplayControlsPointerTargetType::TurnRate32Button;
        case GameplayControlsRenderButton::TurnRateSmooth:
            return controlsPressedTarget().type == GameplayControlsPointerTargetType::TurnRateSmoothButton;
        case GameplayControlsRenderButton::WalkSound:
            return controlsPressedTarget().type == GameplayControlsPointerTargetType::WalkSoundButton;
        case GameplayControlsRenderButton::ShowHits:
            return controlsPressedTarget().type == GameplayControlsPointerTargetType::ShowHitsButton;
        case GameplayControlsRenderButton::AlwaysRun:
            return controlsPressedTarget().type == GameplayControlsPointerTargetType::AlwaysRunButton;
        case GameplayControlsRenderButton::FlipOnExit:
            return controlsPressedTarget().type == GameplayControlsPointerTargetType::FlipOnExitButton;
    }

    return false;
}

bool GameplayOverlayContext::isVideoOptionsRenderButtonPressed(GameplayVideoOptionsRenderButton button) const
{
    if (!videoOptionsClickLatch())
    {
        return false;
    }

    switch (button)
    {
        case GameplayVideoOptionsRenderButton::BloodSplats:
            return videoOptionsPressedTarget().type == GameplayVideoOptionsPointerTargetType::BloodSplatsButton;
        case GameplayVideoOptionsRenderButton::ColoredLights:
            return videoOptionsPressedTarget().type == GameplayVideoOptionsPointerTargetType::ColoredLightsButton;
        case GameplayVideoOptionsRenderButton::Tinting:
            return videoOptionsPressedTarget().type == GameplayVideoOptionsPointerTargetType::TintingButton;
    }

    return false;
}

void GameplayOverlayContext::clearHudLayoutRuntimeHeightOverrides()
{
    uiRuntime().clearHudLayoutRuntimeHeightOverrides();
}

void GameplayOverlayContext::setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height)
{
    uiRuntime().setHudLayoutRuntimeHeightOverride(layoutId, height);
}

const HouseEntry *GameplayOverlayContext::findHouseEntry(uint32_t houseId) const
{
    return houseTable() != nullptr ? houseTable()->get(houseId) : nullptr;
}

const GameplayOverlayContext::HudLayoutElement *GameplayOverlayContext::findHudLayoutElement(
    const std::string &layoutId) const
{
    return uiRuntime().findHudLayoutElement(layoutId);
}

int GameplayOverlayContext::defaultHudLayoutZIndexForScreen(const std::string &screen) const
{
    return uiRuntime().defaultHudLayoutZIndexForScreen(screen);
}

GameplayHudScreenState GameplayOverlayContext::currentHudScreenState() const
{
    return resolveGameplayHudScreenState(uiController(), activeEventDialog(), worldRuntime());
}

std::vector<std::string> GameplayOverlayContext::sortedHudLayoutIdsForScreen(const std::string &screen) const
{
    return uiRuntime().sortedHudLayoutIdsForScreen(screen);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveHudLayoutElement(
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight) const
{
    return uiRuntime().resolveHudLayoutElement(layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolvePartyPortraitRect(
    int width,
    int height,
    size_t memberIndex) const
{
    const Party *pParty = partyReadOnly();

    if (pParty == nullptr || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const GameplayHudScreenState hudScreenState = currentHudScreenState();
    const bool isLimitedOverlayHud =
        hudScreenState == GameplayHudScreenState::Dialogue
        || hudScreenState == GameplayHudScreenState::Character
        || hudScreenState == GameplayHudScreenState::Chest
        || hudScreenState == GameplayHudScreenState::Spellbook
        || hudScreenState == GameplayHudScreenState::Rest
        || hudScreenState == GameplayHudScreenState::Menu
        || hudScreenState == GameplayHudScreenState::SaveGame
        || hudScreenState == GameplayHudScreenState::LoadGame
        || hudScreenState == GameplayHudScreenState::Journal;
    const bool useGameplayWideHud =
        !isLimitedOverlayHud && settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Widescreen;
    const std::string basebarLayoutId = isLimitedOverlayHud
        ? "OutdoorBasebar"
        : (settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Standard
            ? "OutdoorStandardBasebar"
            : "OutdoorGameplayBasebar");
    const std::string partyStripLayoutId = isLimitedOverlayHud
        ? "OutdoorPartyStrip"
        : (settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Standard
            ? "OutdoorStandardPartyStrip"
            : "OutdoorGameplayPartyStrip");
    const HudLayoutElement *pBasebarLayout = findHudLayoutElement(basebarLayoutId);
    const HudLayoutElement *pPartyStripLayout = findHudLayoutElement(partyStripLayoutId);

    if (pBasebarLayout == nullptr || pPartyStripLayout == nullptr)
    {
        return std::nullopt;
    }

    const std::optional<HudTextureHandle> basebarTexture =
        const_cast<GameplayOverlayContext *>(this)->ensureHudTextureLoaded(pBasebarLayout->primaryAsset);
    const std::optional<HudTextureHandle> faceMaskTexture =
        const_cast<GameplayOverlayContext *>(this)->ensureHudTextureLoaded(pPartyStripLayout->primaryAsset);

    if (!basebarTexture || !faceMaskTexture)
    {
        return std::nullopt;
    }

    const std::optional<ResolvedHudLayoutElement> resolvedBasebar = resolveHudLayoutElement(
        basebarLayoutId,
        width,
        height,
        basebarTexture->width,
        basebarTexture->height);
    const std::optional<ResolvedHudLayoutElement> resolvedPartyStrip = resolveHudLayoutElement(
        partyStripLayoutId,
        width,
        height,
        basebarTexture->width,
        basebarTexture->height);

    if (!resolvedBasebar || !resolvedPartyStrip)
    {
        return std::nullopt;
    }

    const std::vector<Character> &members = pParty->members();

    if (memberIndex >= members.size())
    {
        return std::nullopt;
    }

    const float portraitWidth = static_cast<float>(faceMaskTexture->width) * resolvedBasebar->scale;
    const float portraitHeight = static_cast<float>(faceMaskTexture->height) * resolvedBasebar->scale;
    float portraitStartX = resolvedPartyStrip->x + resolvedPartyStrip->width * (20.0f / 471.0f);
    float portraitY = resolvedPartyStrip->y + resolvedPartyStrip->height * (23.0f / 92.0f);
    const float portraitDeltaX = resolvedPartyStrip->width * (94.0f / 471.0f);

    if (useGameplayWideHud)
    {
        const float basebarCenterX = resolvedBasebar->x + resolvedBasebar->width * 0.5f;
        const float portraitGroupWidth = portraitWidth + static_cast<float>(members.size() - 1) * portraitDeltaX;
        portraitStartX = basebarCenterX - portraitGroupWidth * 0.5f;
        portraitY -= 15.0f * resolvedBasebar->scale;
    }

    return ResolvedHudLayoutElement{
        portraitStartX + static_cast<float>(memberIndex) * portraitDeltaX,
        portraitY,
        portraitWidth,
        portraitHeight,
        resolvedBasebar->scale
    };
}

std::optional<size_t> GameplayOverlayContext::resolvePartyPortraitIndexAtPoint(
    int width,
    int height,
    float x,
    float y) const
{
    const Party *pParty = partyReadOnly();

    if (pParty == nullptr || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    for (size_t memberIndex = 0; memberIndex < pParty->members().size(); ++memberIndex)
    {
        const std::optional<ResolvedHudLayoutElement> portraitRect = resolvePartyPortraitRect(width, height, memberIndex);

        if (!portraitRect)
        {
            continue;
        }

        if (x >= portraitRect->x
            && x < portraitRect->x + portraitRect->width
            && y >= portraitRect->y
            && y < portraitRect->y + portraitRect->height)
        {
            return memberIndex;
        }
    }

    return std::nullopt;
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveChestGridArea(
    int width,
    int height) const
{
    if (width <= 0 || height <= 0 || chestTable() == nullptr)
    {
        return std::nullopt;
    }

    const IGameplayWorldRuntime *pRuntime = worldRuntime();
    const GameplayChestViewState *pChestView = pRuntime != nullptr ? pRuntime->activeChestView() : nullptr;

    if (pChestView == nullptr || pChestView->gridWidth == 0 || pChestView->gridHeight == 0)
    {
        return std::nullopt;
    }

    const ChestEntry *pChestEntry = chestTable()->get(pChestView->chestTypeId);
    const HudLayoutElement *pChestBackgroundLayout = findHudLayoutElement("ChestBackground");

    if (pChestEntry == nullptr || pChestBackgroundLayout == nullptr)
    {
        return std::nullopt;
    }

    const std::optional<ResolvedHudLayoutElement> resolvedBackground = resolveHudLayoutElement(
        "ChestBackground",
        width,
        height,
        pChestBackgroundLayout->width,
        pChestBackgroundLayout->height);

    if (!resolvedBackground)
    {
        return std::nullopt;
    }

    ResolvedHudLayoutElement resolved = {};
    resolved.x = std::round(
        resolvedBackground->x + static_cast<float>(pChestEntry->gridOffsetX) * resolvedBackground->scale);
    resolved.y = std::round(
        resolvedBackground->y + static_cast<float>(pChestEntry->gridOffsetY) * resolvedBackground->scale);
    resolved.width = 32.0f * static_cast<float>(pChestView->gridWidth) * resolvedBackground->scale;
    resolved.height = 32.0f * static_cast<float>(pChestView->gridHeight) * resolvedBackground->scale;
    resolved.scale = resolvedBackground->scale;
    return resolved;
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>
GameplayOverlayContext::resolveInventoryNestedOverlayGridArea(
    int width,
    int height) const
{
    if (!inventoryNestedOverlay().active || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const HudLayoutElement *pGridLayout = findHudLayoutElement("ChestNestedInventoryGrid");

    if (pGridLayout == nullptr)
    {
        return std::nullopt;
    }

    return resolveHudLayoutElement(
        "ChestNestedInventoryGrid",
        width,
        height,
        pGridLayout->width,
        pGridLayout->height);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveHouseShopOverlayFrame(
    int width,
    int height) const
{
    if (!houseShopOverlay().active || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const HudLayoutElement *pFrameLayout = findHudLayoutElement("DialogueShopOverlayFrame");

    if (pFrameLayout == nullptr)
    {
        return std::nullopt;
    }

    return resolveHudLayoutElement(
        "DialogueShopOverlayFrame",
        width,
        height,
        pFrameLayout->width,
        pFrameLayout->height);
}

bool GameplayOverlayContext::isPointerInsideResolvedElement(
    const ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY) const
{
    return GameplayHudCommon::isPointerInsideResolvedElement(resolved, pointerX, pointerY);
}

const std::string *GameplayOverlayContext::resolveInteractiveAssetName(
    const HudLayoutElement &layout,
    const ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY,
    bool isLeftMousePressed) const
{
    const std::string *pAssetName = GameplayHudCommon::resolveInteractiveAssetName(
        layout,
        resolved,
        pointerX,
        pointerY,
        isLeftMousePressed);

    if (pAssetName == nullptr)
    {
        return nullptr;
    }

    m_resolvedInteractiveAssetName = *pAssetName;
    return &*m_resolvedInteractiveAssetName;
}

std::optional<GameplayOverlayContext::HudTextureHandle> GameplayOverlayContext::ensureHudTextureLoaded(
    const std::string &textureName)
{
    return uiRuntime().ensureHudTextureLoaded(textureName);
}

std::optional<GameplayOverlayContext::HudTextureHandle> GameplayOverlayContext::ensureSolidHudTextureLoaded(
    const std::string &textureName,
    uint32_t abgrColor)
{
    return uiRuntime().ensureSolidHudTextureLoaded(textureName, abgrColor);
}

std::optional<GameplayOverlayContext::HudTextureHandle> GameplayOverlayContext::ensureDynamicHudTexture(
    const std::string &textureName,
    int width,
    int height,
    const std::vector<uint8_t> &bgraPixels)
{
    return uiRuntime().ensureDynamicHudTexture(textureName, width, height, bgraPixels);
}

std::optional<std::vector<uint8_t>> GameplayOverlayContext::loadSpriteBitmapPixelsBgraCached(
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height)
{
    return uiRuntime().loadSpriteBitmapPixelsBgraCached(textureName, paletteId, width, height);
}

const std::vector<uint8_t> *GameplayOverlayContext::hudTexturePixels(
    const std::string &textureName,
    int &width,
    int &height)
{
    return uiRuntime().hudTexturePixels(textureName, width, height);
}

bool GameplayOverlayContext::ensureHudTextureDimensions(const std::string &textureName, int &width, int &height)
{
    return uiRuntime().ensureHudTextureDimensions(textureName, width, height);
}

bool GameplayOverlayContext::tryGetOpaqueHudTextureBounds(
    const std::string &textureName,
    int &width,
    int &height,
    int &opaqueMinX,
    int &opaqueMinY,
    int &opaqueMaxX,
    int &opaqueMaxY)
{
    return uiRuntime().tryGetOpaqueHudTextureBounds(
        textureName,
        width,
        height,
        opaqueMinX,
        opaqueMinY,
        opaqueMaxX,
        opaqueMaxY);
}

void GameplayOverlayContext::submitHudTexturedQuad(
    const HudTextureHandle &texture,
    float x,
    float y,
    float quadWidth,
    float quadHeight) const
{
    uiRuntime().submitHudTexturedQuad(texture.textureHandle, x, y, quadWidth, quadHeight);
}

bgfx::TextureHandle GameplayOverlayContext::ensureHudTextureColor(const HudTextureHandle &texture, uint32_t colorAbgr) const
{
    return uiRuntime().ensureHudTextureColor(texture, colorAbgr);
}

void GameplayOverlayContext::renderLayoutLabel(
    const HudLayoutElement &layout,
    const ResolvedHudLayoutElement &resolved,
    const std::string &label) const
{
    GameplayHudCommon::renderLayoutLabel(
        layout,
        resolved,
        label,
        [this](const std::string &fontName) -> const GameplayHudFontData *
        {
            const std::optional<HudFontHandle> font = uiRuntime().findHudFont(fontName);

            if (!font)
            {
                return nullptr;
            }

            return GameplayHudCommon::findHudFont(uiRuntime().hudFontHandles(), font->fontName);
        },
        [this](const GameplayHudFontData &font, uint32_t colorAbgr) -> bgfx::TextureHandle
        {
            HudFontHandle gameplayFont = {};
            gameplayFont.fontName = font.fontName;
            gameplayFont.fontHeight = font.fontHeight;
            gameplayFont.mainTextureHandle = font.mainTextureHandle;
            gameplayFont.shadowTextureHandle = font.shadowTextureHandle;
            return uiRuntime().ensureHudFontMainTextureColor(gameplayFont, colorAbgr);
        },
        [this](const GameplayHudFontData &font,
               bgfx::TextureHandle textureHandle,
               const std::string &text,
               float textX,
               float textY,
               float fontScale)
        {
            HudFontHandle gameplayFont = {};
            gameplayFont.fontName = font.fontName;
            gameplayFont.fontHeight = font.fontHeight;
            gameplayFont.mainTextureHandle = font.mainTextureHandle;
            gameplayFont.shadowTextureHandle = font.shadowTextureHandle;
            renderHudFontLayer(gameplayFont, textureHandle, text, textX, textY, fontScale);
        });
}

std::optional<GameplayOverlayContext::HudFontHandle> GameplayOverlayContext::findHudFont(const std::string &fontName) const
{
    return uiRuntime().findHudFont(fontName);
}

float GameplayOverlayContext::measureHudTextWidth(const HudFontHandle &font, const std::string &text) const
{
    return uiRuntime().measureHudTextWidth(font, text);
}

std::vector<std::string> GameplayOverlayContext::wrapHudTextToWidth(
    const HudFontHandle &font,
    const std::string &text,
    float maxWidth) const
{
    return uiRuntime().wrapHudTextToWidth(font, text, maxWidth);
}

bgfx::TextureHandle GameplayOverlayContext::ensureHudFontMainTextureColor(
    const HudFontHandle &font,
    uint32_t colorAbgr) const
{
    return uiRuntime().ensureHudFontMainTextureColor(font, colorAbgr);
}

void GameplayOverlayContext::renderHudFontLayer(
    const HudFontHandle &font,
    bgfx::TextureHandle textureHandle,
    const std::string &text,
    float textX,
    float textY,
    float fontScale) const
{
    uiRuntime().renderHudFontLayer(font, textureHandle, text, textX, textY, fontScale);
}

bool GameplayOverlayContext::hasHudRenderResources() const
{
    return uiRuntime().hasHudRenderResources();
}

void GameplayOverlayContext::prepareHudView(int width, int height) const
{
    uiRuntime().prepareHudView(width, height);
}

void GameplayOverlayContext::submitHudQuadBatch(
    const std::vector<GameplayHudBatchQuad> &quads,
    int screenWidth,
    int screenHeight) const
{
    uiRuntime().submitHudQuadBatch(quads, screenWidth, screenHeight);
}

std::string GameplayOverlayContext::resolvePortraitTextureName(const Character &character) const
{
    return uiRuntime().resolvePortraitTextureName(character);
}

void GameplayOverlayContext::consumePendingPortraitEventFxRequests()
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    EventRuntimeState *pEventRuntimeState = pWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    for (const EventRuntimeState::PortraitFxRequest &request : pEventRuntimeState->portraitFxRequests)
    {
        const PortraitFxEventEntry *pEntry = uiRuntime().findPortraitFxEvent(request.kind);

        if (pEntry == nullptr)
        {
            continue;
        }

        uiRuntime().triggerPortraitFxAnimation(pEntry->animationName, request.memberIndices);

        if (pEntry->faceAnimationId.has_value())
        {
            for (size_t memberIndex : request.memberIndices)
            {
                triggerPortraitFaceAnimation(memberIndex, *pEntry->faceAnimationId);
            }
        }

        if (request.memberIndices.empty())
        {
            continue;
        }

        switch (request.kind)
        {
            case PortraitFxEventKind::AutoNote:
                if (audioSystem() != nullptr)
                {
                    audioSystem()->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
                }
                break;

            case PortraitFxEventKind::AwardGain:
                if (audioSystem() != nullptr)
                {
                    audioSystem()->playCommonSound(SoundId::Chimes, GameAudioSystem::PlaybackGroup::Ui);
                }
                playSpeechReaction(request.memberIndices.front(), SpeechId::AwardGot, false);
                break;

            case PortraitFxEventKind::QuestComplete:
                if (audioSystem() != nullptr)
                {
                    audioSystem()->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
                }
                playSpeechReaction(request.memberIndices.front(), SpeechId::QuestGot, false);
                break;

            case PortraitFxEventKind::StatIncrease:
                if (audioSystem() != nullptr)
                {
                    audioSystem()->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
                }
                break;

            case PortraitFxEventKind::StatDecrease:
                playSpeechReaction(request.memberIndices.front(), SpeechId::Indignant, false);
                break;

            case PortraitFxEventKind::Disease:
                playSpeechReaction(request.memberIndices.front(), SpeechId::Poisoned, false);
                break;

            case PortraitFxEventKind::None:
                break;
        }
    }

    pEventRuntimeState->portraitFxRequests.clear();

    for (const EventRuntimeState::SpellFxRequest &request : pEventRuntimeState->spellFxRequests)
    {
        uiRuntime().triggerPortraitSpellFx(PartySpellCastResult{
            .spellId = request.spellId,
            .affectedCharacterIndices = request.memberIndices
        });

        if (audioSystem() != nullptr && spellTable() != nullptr)
        {
            const SpellEntry *pSpellEntry = spellTable()->findById(request.spellId);

            if (pSpellEntry != nullptr && pSpellEntry->effectSoundId > 0)
            {
                audioSystem()->playSound(pSpellEntry->effectSoundId, GameAudioSystem::PlaybackGroup::Ui);
            }
        }
    }

    pEventRuntimeState->spellFxRequests.clear();
}

void GameplayOverlayContext::renderPortraitFx(
    size_t memberIndex,
    float portraitX,
    float portraitY,
    float portraitWidth,
    float portraitHeight) const
{
    uiRuntime().renderPortraitFx(memberIndex, portraitX, portraitY, portraitWidth, portraitHeight);
}

bool GameplayOverlayContext::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    state = {};
    return pWorldRuntime != nullptr && pWorldRuntime->tryGetGameplayMinimapState(state);
}

void GameplayOverlayContext::collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        markers.clear();
        return;
    }

    pWorldRuntime->collectGameplayMinimapMarkers(markers);
}

bool GameplayOverlayContext::ensureTownPortalDestinationsLoaded()
{
    return uiRuntime().ensureTownPortalDestinationsLoaded();
}

const std::vector<GameplayTownPortalDestination> &GameplayOverlayContext::townPortalDestinations() const
{
    return uiRuntime().townPortalDestinations();
}

std::string GameplayOverlayContext::resolveMapLocationName(const std::string &mapFileName) const
{
    for (const MapStatsEntry &entry : m_session.data().mapEntries())
    {
        if (toLowerCopy(entry.fileName) == toLowerCopy(mapFileName))
        {
            return entry.name;
        }
    }

    return mapFileName;
}

float GameplayOverlayContext::measureHudTextWidth(const std::string &fontName, const std::string &text) const
{
    const std::optional<HudFontHandle> font = findHudFont(fontName);
    return font ? measureHudTextWidth(*font, text) : 0.0f;
}

int GameplayOverlayContext::hudFontHeight(const std::string &fontName) const
{
    const std::optional<HudFontHandle> font = findHudFont(fontName);
    return font ? font->fontHeight : 0;
}

std::vector<std::string> GameplayOverlayContext::wrapHudTextToWidth(
    const std::string &fontName,
    const std::string &text,
    float maxWidth) const
{
    const std::optional<HudFontHandle> font = findHudFont(fontName);
    return font ? wrapHudTextToWidth(*font, text, maxWidth) : std::vector<std::string>{text};
}

void GameplayOverlayContext::renderHudTextLine(
    const std::string &fontName,
    uint32_t colorAbgr,
    const std::string &text,
    float textX,
    float textY,
    float fontScale) const
{
    const std::optional<HudFontHandle> font = findHudFont(fontName);

    if (!font)
    {
        return;
    }

    bgfx::TextureHandle coloredMainTextureHandle = ensureHudFontMainTextureColor(*font, colorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = font->mainTextureHandle;
    }

    renderHudFontLayer(*font, font->shadowTextureHandle, text, textX, textY, fontScale);
    renderHudFontLayer(*font, coloredMainTextureHandle, text, textX, textY, fontScale);
}

void GameplayOverlayContext::addRenderedInspectableHudItem(const GameplayRenderedInspectableHudItem &item) const
{
    uiRuntime().addRenderedInspectableHudItem(item);
}

const std::vector<GameplayRenderedInspectableHudItem> &GameplayOverlayContext::renderedInspectableHudItems() const
{
    return uiRuntime().renderedInspectableHudItems();
}

void GameplayOverlayContext::beginRenderedInspectableHudFrame() const
{
    uiRuntime().clearRenderedInspectableHudItems();
    uiRuntime().setRenderedInspectableHudScreenState(currentHudScreenState());
}

GameplayHudScreenState GameplayOverlayContext::renderedInspectableHudScreenState() const
{
    return uiRuntime().renderedInspectableHudScreenState();
}

bool GameplayOverlayContext::isOpaqueHudPixelAtPoint(
    const GameplayRenderedInspectableHudItem &item,
    float x,
    float y) const
{
    return uiRuntime().isOpaqueHudPixelAtPoint(item, x, y);
}

std::string GameplayOverlayContext::resolveEquippedItemHudTextureName(
    const ItemDefinition &itemDefinition,
    uint32_t dollTypeId,
    bool hasRightHandWeapon,
    EquipmentSlot slot)
{
    if (!isBodyEquipmentVisualSlot(slot))
    {
        return itemDefinition.iconName;
    }

    std::vector<std::string> candidateSuffixes;

    switch (dollTypeId)
    {
        case 0:
            candidateSuffixes = hasRightHandWeapon
                ? std::vector<std::string>{"v1", "v1a"}
                : std::vector<std::string>{"v1a", "v1"};
            break;

        case 1:
            candidateSuffixes = hasRightHandWeapon
                ? std::vector<std::string>{"v2", "v2a"}
                : std::vector<std::string>{"v2a", "v2"};
            break;

        case 2:
            candidateSuffixes = {usesAlternateCloakBeltEquippedVariant(slot) ? "v1" : "v3"};
            break;

        case 3:
            candidateSuffixes = {usesAlternateCloakBeltEquippedVariant(slot) ? "v1" : "v4"};
            break;

        default:
            break;
    }

    for (const std::string &suffix : candidateSuffixes)
    {
        const std::string candidateName = itemDefinition.iconName + suffix;
        int width = 0;
        int height = 0;

        if (ensureHudTextureDimensions(candidateName, width, height))
        {
            return candidateName;
        }
    }

    return itemDefinition.iconName;
}

std::optional<GameplayResolvedHudLayoutElement> GameplayOverlayContext::resolveCharacterEquipmentRenderRect(
    const UiLayoutManager::LayoutElement &layout,
    const ItemDefinition &itemDefinition,
    const GameplayHudTextureHandle &texture,
    const CharacterDollTypeEntry *pCharacterDollType,
    EquipmentSlot slot,
    int screenWidth,
    int screenHeight) const
{
    const float fallbackWidth = layout.width > 0.0f ? layout.width : static_cast<float>(texture.width);
    const float fallbackHeight = layout.height > 0.0f ? layout.height : static_cast<float>(texture.height);
    const std::optional<GameplayResolvedHudLayoutElement> resolved =
        resolveHudLayoutElement(layout.id, screenWidth, screenHeight, fallbackWidth, fallbackHeight);

    if (!resolved.has_value())
    {
        return std::nullopt;
    }

    const float iconWidth = static_cast<float>(texture.width) * resolved->scale;
    const float iconHeight = static_cast<float>(texture.height) * resolved->scale;

    if (isBodyEquipmentVisualSlot(slot))
    {
        const ItemEquipPosEntry *pEntry =
            itemEquipPosTable() != nullptr ? itemEquipPosTable()->get(itemDefinition.itemId) : nullptr;
        const uint32_t dollTypeId = pCharacterDollType != nullptr ? pCharacterDollType->id : 0;
        int offsetX = 0;
        int offsetY = 0;

        if (pEntry != nullptr && dollTypeId < pEntry->xByDollType.size())
        {
            offsetX = pEntry->xByDollType[dollTypeId];
            offsetY = pEntry->yByDollType[dollTypeId];
        }

        GameplayResolvedHudLayoutElement rect = {};
        rect.x = std::round(resolved->x + static_cast<float>(offsetX) * resolved->scale);
        rect.y = std::round(resolved->y + static_cast<float>(offsetY) * resolved->scale);
        rect.width = iconWidth;
        rect.height = iconHeight;
        rect.scale = resolved->scale;
        return rect;
    }

    if (slot == EquipmentSlot::Bow)
    {
        GameplayResolvedHudLayoutElement rect = {};
        rect.x = std::round(
            resolved->x + static_cast<float>(pCharacterDollType != nullptr ? pCharacterDollType->bowOffsetX : 0)
            * resolved->scale - iconWidth * 0.5f);
        rect.y = std::round(
            resolved->y + static_cast<float>(pCharacterDollType != nullptr ? pCharacterDollType->bowOffsetY : 0)
            * resolved->scale - iconHeight * 0.5f);
        rect.width = iconWidth;
        rect.height = iconHeight;
        rect.scale = resolved->scale;
        return rect;
    }

    if (slot == EquipmentSlot::MainHand || slot == EquipmentSlot::OffHand)
    {
        int offsetX = 0;
        int offsetY = 0;

        if (pCharacterDollType != nullptr)
        {
            if (slot == EquipmentSlot::MainHand)
            {
                offsetX = pCharacterDollType->rightHandFingersX + pCharacterDollType->mainHandOffsetX
                    - itemDefinition.equipX;
                offsetY = pCharacterDollType->rightHandFingersY + pCharacterDollType->mainHandOffsetY
                    - itemDefinition.equipY;
            }
            else if (itemDefinition.equipStat == "Shield")
            {
                offsetX += pCharacterDollType->leftHandClosedX + pCharacterDollType->shieldX - itemDefinition.equipX;
                offsetY += pCharacterDollType->leftHandClosedY + pCharacterDollType->shieldY - itemDefinition.equipY;
            }
            else
            {
                offsetX = pCharacterDollType->rightHandFingersX + pCharacterDollType->offHandOffsetX
                    - itemDefinition.equipX;
                offsetY = pCharacterDollType->rightHandFingersY + pCharacterDollType->offHandOffsetY
                    - itemDefinition.equipY;
            }
        }

        GameplayResolvedHudLayoutElement rect = {};
        rect.x = std::round(resolved->x + static_cast<float>(offsetX) * resolved->scale);
        rect.y = std::round(resolved->y + static_cast<float>(offsetY) * resolved->scale);
        rect.width = iconWidth;
        rect.height = iconHeight;
        rect.scale = resolved->scale;
        return rect;
    }

    GameplayResolvedHudLayoutElement rect = {};
    rect.x = std::round(resolved->x + (resolved->width - iconWidth) * 0.5f);
    rect.y = std::round(resolved->y + (resolved->height - iconHeight) * 0.5f);
    rect.width = iconWidth;
    rect.height = iconHeight;
    rect.scale = resolved->scale;
    return rect;
}

void GameplayOverlayContext::submitWorldTextureQuad(
    bgfx::TextureHandle textureHandle,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    float u0,
    float v0,
    float u1,
    float v1) const
{
    uiRuntime().submitHudTexturedQuad(textureHandle, x, y, quadWidth, quadHeight, u0, v0, u1, v1);
}

bool GameplayOverlayContext::renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const
{
    return uiRuntime().renderHouseVideoFrame(x, y, quadWidth, quadHeight);
}
} // namespace OpenYAMM::Game
