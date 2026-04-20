#include "game/gameplay/GameplayScreenRuntime.h"

#include "game/app/GameSession.h"
#include "game/gameplay/GameplayDialogContextBuilder.h"
#include "game/gameplay/GameplayDialogUiFlow.h"
#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/party/SpellSchool.h"
#include "game/StringUtils.h"
#include "game/ui/SpellbookUiLayout.h"

#include <cassert>
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

GameplayScreenRuntime::GameplayScreenRuntime(GameSession &session)
    : m_session(session)
{
}

void GameplayScreenRuntime::bindAudioSystem(GameAudioSystem *pAudioSystem)
{
    m_pAudioSystem = pAudioSystem;
}

void GameplayScreenRuntime::bindSettings(GameSettings *pSettings)
{
    m_pSettings = pSettings;
}

void GameplayScreenRuntime::bindSceneAdapter(IGameplayOverlaySceneAdapter *pSceneAdapter)
{
    m_pSceneAdapter = pSceneAdapter;
}

void GameplayScreenRuntime::clearSceneAdapter(IGameplayOverlaySceneAdapter *pSceneAdapter)
{
    if (m_pSceneAdapter == pSceneAdapter)
    {
        m_pSceneAdapter = nullptr;
    }
}

void GameplayScreenRuntime::clearTransientBindings()
{
    m_pAudioSystem = nullptr;
    m_pSettings = nullptr;
    m_pSceneAdapter = nullptr;
}

IGameplayOverlaySceneAdapter &GameplayScreenRuntime::sceneAdapter() const
{
    assert(m_pSceneAdapter != nullptr);
    return *m_pSceneAdapter;
}

GameplayUiController &GameplayScreenRuntime::uiController() const
{
    return m_session.gameplayUiController();
}

GameplayUiRuntime &GameplayScreenRuntime::uiRuntime() const
{
    return m_session.gameplayUiRuntime();
}

GameplayOverlayInteractionState &GameplayScreenRuntime::interactionState() const
{
    return m_session.overlayInteractionState();
}

GameplayDialogUiFlowState GameplayScreenRuntime::dialogUiFlowState()
{
    return {
        uiController(),
        interactionState(),
        m_session.gameplayDialogController(),
        eventDialogSelectionIndex()
    };
}

GameplayDialogController::Context GameplayScreenRuntime::buildDialogContext(EventRuntimeState &eventRuntimeState)
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

void GameplayScreenRuntime::presentPendingEventDialogShared(size_t previousMessageCount, bool allowNpcFallbackContent)
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

void GameplayScreenRuntime::closeActiveEventDialogShared()
{
    GameplayDialogUiFlowState state = dialogUiFlowState();
    ::OpenYAMM::Game::closeActiveEventDialog(
        state,
        worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr);
}

void GameplayScreenRuntime::returnToHouseBankMainDialogShared()
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

IGameplayWorldRuntime *GameplayScreenRuntime::worldRuntime() const
{
    return m_session.activeWorldRuntime();
}

Party *GameplayScreenRuntime::party() const
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->party() : nullptr;
}

const Party *GameplayScreenRuntime::partyReadOnly() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->party() : nullptr;
}

float GameplayScreenRuntime::partyX() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->partyX() : 0.0f;
}

float GameplayScreenRuntime::partyY() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->partyY() : 0.0f;
}

float GameplayScreenRuntime::partyFootZ() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->partyFootZ() : 0.0f;
}

GameAudioSystem *GameplayScreenRuntime::audioSystem() const
{
    return m_pAudioSystem;
}

const ItemTable *GameplayScreenRuntime::itemTable() const
{
    return &m_session.data().itemTable();
}

const StandardItemEnchantTable *GameplayScreenRuntime::standardItemEnchantTable() const
{
    return &m_session.data().standardItemEnchantTable();
}

const SpecialItemEnchantTable *GameplayScreenRuntime::specialItemEnchantTable() const
{
    return &m_session.data().specialItemEnchantTable();
}

const ClassSkillTable *GameplayScreenRuntime::classSkillTable() const
{
    return &m_session.data().classSkillTable();
}

const CharacterDollTable *GameplayScreenRuntime::characterDollTable() const
{
    return &m_session.data().characterDollTable();
}

const CharacterInspectTable *GameplayScreenRuntime::characterInspectTable() const
{
    return &m_session.data().characterInspectTable();
}

const RosterTable *GameplayScreenRuntime::rosterTable() const
{
    return &m_session.data().rosterTable();
}

const ReadableScrollTable *GameplayScreenRuntime::readableScrollTable() const
{
    return &m_session.data().readableScrollTable();
}

const ItemEquipPosTable *GameplayScreenRuntime::itemEquipPosTable() const
{
    return &m_session.data().itemEquipPosTable();
}

const SpellTable *GameplayScreenRuntime::spellTable() const
{
    return &m_session.data().spellTable();
}

const HouseTable *GameplayScreenRuntime::houseTable() const
{
    return &m_session.data().houseTable();
}

const ChestTable *GameplayScreenRuntime::chestTable() const
{
    return &m_session.data().chestTable();
}

const NpcDialogTable *GameplayScreenRuntime::npcDialogTable() const
{
    return &m_session.data().npcDialogTable();
}

const MonsterTable *GameplayScreenRuntime::monsterTable() const
{
    return &m_session.data().monsterTable();
}

GameplayUiController::CharacterScreenState &GameplayScreenRuntime::characterScreen() const
{
    return uiController().characterScreen();
}

GameplayUiController::HeldInventoryItemState &GameplayScreenRuntime::heldInventoryItem() const
{
    return uiController().heldInventoryItem();
}

GameplayUiController::ItemInspectOverlayState &GameplayScreenRuntime::itemInspectOverlay() const
{
    return uiController().itemInspectOverlay();
}

GameplayUiController::CharacterInspectOverlayState &GameplayScreenRuntime::characterInspectOverlay() const
{
    return uiController().characterInspectOverlay();
}

GameplayUiController::BuffInspectOverlayState &GameplayScreenRuntime::buffInspectOverlay() const
{
    return uiController().buffInspectOverlay();
}

GameplayUiController::CharacterDetailOverlayState &GameplayScreenRuntime::characterDetailOverlay() const
{
    return uiController().characterDetailOverlay();
}

GameplayUiController::ActorInspectOverlayState &GameplayScreenRuntime::actorInspectOverlay() const
{
    return uiController().actorInspectOverlay();
}

GameplayUiController::SpellInspectOverlayState &GameplayScreenRuntime::spellInspectOverlay() const
{
    return uiController().spellInspectOverlay();
}

GameplayUiController::ReadableScrollOverlayState &GameplayScreenRuntime::readableScrollOverlay() const
{
    return uiController().readableScrollOverlay();
}

GameplayUiController::SpellbookState &GameplayScreenRuntime::spellbook() const
{
    return uiController().spellbook();
}

GameplayUiController::UtilitySpellOverlayState &GameplayScreenRuntime::utilitySpellOverlay() const
{
    return uiController().utilitySpellOverlay();
}

GameplayUiController::InventoryNestedOverlayState &GameplayScreenRuntime::inventoryNestedOverlay() const
{
    return uiController().inventoryNestedOverlay();
}

GameplayUiController::HouseShopOverlayState &GameplayScreenRuntime::houseShopOverlay() const
{
    return uiController().houseShopOverlay();
}

GameplayUiController::HouseBankState &GameplayScreenRuntime::houseBankState() const
{
    return uiController().houseBankState();
}

GameplayUiController::JournalScreenState &GameplayScreenRuntime::journalScreenState() const
{
    return uiController().journalScreen();
}

GameplayUiController::RestScreenState &GameplayScreenRuntime::restScreenState() const
{
    return uiController().restScreen();
}

GameplayUiController::MenuScreenState &GameplayScreenRuntime::menuScreenState() const
{
    return uiController().menuScreen();
}

GameplayUiController::ControlsScreenState &GameplayScreenRuntime::controlsScreenState() const
{
    return uiController().controlsScreen();
}

GameplayUiController::KeyboardScreenState &GameplayScreenRuntime::keyboardScreenState() const
{
    return uiController().keyboardScreen();
}

GameplayUiController::VideoOptionsScreenState &GameplayScreenRuntime::videoOptionsScreenState() const
{
    return uiController().videoOptionsScreen();
}

GameplayUiController::SaveGameScreenState &GameplayScreenRuntime::saveGameScreenState() const
{
    return uiController().saveGameScreen();
}

GameplayUiController::LoadGameScreenState &GameplayScreenRuntime::loadGameScreenState() const
{
    return uiController().loadGameScreen();
}

const GameplayUiController::CharacterScreenState &GameplayScreenRuntime::characterScreenReadOnly() const
{
    return uiController().characterScreen();
}

const GameplayUiController::ItemInspectOverlayState &GameplayScreenRuntime::itemInspectOverlayReadOnly() const
{
    return uiController().itemInspectOverlay();
}

const GameplayUiController::CharacterInspectOverlayState &GameplayScreenRuntime::characterInspectOverlayReadOnly() const
{
    return uiController().characterInspectOverlay();
}

const GameplayUiController::BuffInspectOverlayState &GameplayScreenRuntime::buffInspectOverlayReadOnly() const
{
    return uiController().buffInspectOverlay();
}

const GameplayUiController::CharacterDetailOverlayState &GameplayScreenRuntime::characterDetailOverlayReadOnly() const
{
    return uiController().characterDetailOverlay();
}

const GameplayUiController::ActorInspectOverlayState &GameplayScreenRuntime::actorInspectOverlayReadOnly() const
{
    return uiController().actorInspectOverlay();
}

const GameplayUiController::SpellInspectOverlayState &GameplayScreenRuntime::spellInspectOverlayReadOnly() const
{
    return uiController().spellInspectOverlay();
}

const GameplayUiController::ReadableScrollOverlayState &GameplayScreenRuntime::readableScrollOverlayReadOnly() const
{
    return uiController().readableScrollOverlay();
}

const GameplayUiController::SpellbookState &GameplayScreenRuntime::spellbookReadOnly() const
{
    return uiController().spellbook();
}

const GameplayUiController::UtilitySpellOverlayState &GameplayScreenRuntime::utilitySpellOverlayReadOnly() const
{
    return uiController().utilitySpellOverlay();
}

const GameplayUiController::JournalScreenState &GameplayScreenRuntime::journalScreenStateReadOnly() const
{
    return uiController().journalScreen();
}

const JournalQuestTable *GameplayScreenRuntime::journalQuestTable() const
{
    return &m_session.data().journalQuestTable();
}

const JournalHistoryTable *GameplayScreenRuntime::journalHistoryTable() const
{
    return &m_session.data().journalHistoryTable();
}

const JournalAutonoteTable *GameplayScreenRuntime::journalAutonoteTable() const
{
    return &m_session.data().journalAutonoteTable();
}

const std::string &GameplayScreenRuntime::currentMapFileName() const
{
    return m_session.currentMapFileName();
}

float GameplayScreenRuntime::gameplayCameraYawRadians() const
{
    return sceneAdapter().gameplayCameraYawRadians();
}

const std::vector<uint8_t> *GameplayScreenRuntime::journalMapFullyRevealedCells() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->journalMapFullyRevealedCells() : nullptr;
}

const std::vector<uint8_t> *GameplayScreenRuntime::journalMapPartiallyRevealedCells() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->journalMapPartiallyRevealedCells() : nullptr;
}

EventDialogContent &GameplayScreenRuntime::activeEventDialog() const
{
    return uiController().eventDialog().content;
}

std::string &GameplayScreenRuntime::statusBarEventText() const
{
    return uiController().statusBar().eventText;
}

float &GameplayScreenRuntime::statusBarEventRemainingSeconds() const
{
    return uiController().statusBar().eventRemainingSeconds;
}

const std::string &GameplayScreenRuntime::statusBarHoverText() const
{
    return uiController().statusBar().hoverText;
}

std::string &GameplayScreenRuntime::mutableStatusBarHoverText() const
{
    return uiController().statusBar().hoverText;
}

size_t &GameplayScreenRuntime::eventDialogSelectionIndex() const
{
    return uiController().eventDialog().selectionIndex;
}

bool GameplayScreenRuntime::trySelectPartyMember(size_t memberIndex, bool requireGameplayReady)
{
    Party *pParty = party();

    if (pParty == nullptr)
    {
        return false;
    }

    if (requireGameplayReady && !pParty->canSelectMemberInGameplay(memberIndex))
    {
        return false;
    }

    if (!pParty->setActiveMemberIndex(memberIndex))
    {
        return false;
    }

    EventRuntimeState *pEventRuntimeState = worldRuntime() != nullptr ? worldRuntime()->eventRuntimeState() : nullptr;

    if (pEventRuntimeState != nullptr && activeEventDialog().isActive)
    {
        presentPendingEventDialogShared(pEventRuntimeState->messages.size(), true);
    }

    return true;
}

size_t GameplayScreenRuntime::selectedCharacterScreenSourceIndex() const
{
    const Party *pParty = partyReadOnly();

    if (pParty == nullptr)
    {
        return 0;
    }

    const GameplayUiController::CharacterScreenState &screen = characterScreenReadOnly();
    return isAdventurersInnCharacterSourceActive() ? screen.sourceIndex : pParty->activeMemberIndex();
}

const Character *GameplayScreenRuntime::selectedCharacterScreenCharacter() const
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

bool GameplayScreenRuntime::isAdventurersInnCharacterSourceActive() const
{
    const GameplayUiController::CharacterScreenState &screen = characterScreenReadOnly();
    return screen.open && screen.source == GameplayUiController::CharacterScreenSource::AdventurersInn;
}

bool GameplayScreenRuntime::isAdventurersInnScreenActive() const
{
    const GameplayUiController::CharacterScreenState &screen = characterScreenReadOnly();
    return isAdventurersInnCharacterSourceActive() && screen.adventurersInnRosterOverlayOpen;
}

bool GameplayScreenRuntime::isReadOnlyAdventurersInnCharacterViewActive() const
{
    return isAdventurersInnCharacterSourceActive() && !characterScreenReadOnly().adventurersInnRosterOverlayOpen;
}

bool GameplayScreenRuntime::activeMemberKnowsSpell(uint32_t spellId) const
{
    const Character *pMember = partyReadOnly() != nullptr ? partyReadOnly()->activeMember() : nullptr;
    return pMember != nullptr && pMember->knowsSpell(spellId);
}

bool GameplayScreenRuntime::activeMemberHasSpellbookSchool(GameplayUiController::SpellbookSchool school) const
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

void GameplayScreenRuntime::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    uiController().setStatusBarEvent(text, durationSeconds);
}

void GameplayScreenRuntime::openRestOverlay()
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

void GameplayScreenRuntime::openSpellbookOverlay()
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

void GameplayScreenRuntime::openChestTransferInventoryOverlay()
{
    uiController().openInventoryNestedOverlay(GameplayUiController::InventoryNestedOverlayMode::ChestTransfer);
    interactionState().inventoryNestedOverlayItemClickLatch = false;
}

void GameplayScreenRuntime::toggleCharacterInventoryScreen()
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

void GameplayScreenRuntime::handleDialogueCloseRequest()
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

void GameplayScreenRuntime::closeRestOverlay()
{
    uiController().restScreen() = {};
    interactionState().closeOverlayLatch = false;
    interactionState().restClickLatch = false;
    interactionState().restPressedTarget = {};
}

void GameplayScreenRuntime::openMenuOverlay()
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

void GameplayScreenRuntime::closeMenuOverlay()
{
    uiController().menuScreen() = {};
    interactionState().menuToggleLatch = false;
    interactionState().menuClickLatch = false;
    interactionState().menuPressedTarget = {};
    interactionState().closeOverlayLatch = false;
}

void GameplayScreenRuntime::openControlsOverlay()
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

void GameplayScreenRuntime::closeControlsOverlay()
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

void GameplayScreenRuntime::openKeyboardOverlay()
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

void GameplayScreenRuntime::closeKeyboardOverlayToControls()
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

void GameplayScreenRuntime::closeKeyboardOverlayToMenu()
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

void GameplayScreenRuntime::openVideoOptionsOverlay()
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

void GameplayScreenRuntime::closeVideoOptionsOverlay()
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

void GameplayScreenRuntime::openSaveGameOverlay()
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

void GameplayScreenRuntime::closeSaveGameOverlay()
{
    uiController().saveGameScreen() = {};
    interactionState().saveGameToggleLatch = false;
    interactionState().saveGameClickLatch = false;
    interactionState().saveGamePressedTarget = {};
    uiController().menuScreen() = {};
    uiController().menuScreen().active = true;
    interactionState().closeOverlayLatch = false;
}

void GameplayScreenRuntime::requestOpenNewGameScreen()
{
    m_session.requestOpenNewGameScreen();
}

void GameplayScreenRuntime::requestOpenLoadGameScreen()
{
    m_session.requestOpenLoadGameScreen();
}

void GameplayScreenRuntime::openJournalOverlay()
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

void GameplayScreenRuntime::closeJournalOverlay()
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

void GameplayScreenRuntime::ensurePendingEventDialogPresented(bool allowNpcFallbackContent)
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

void GameplayScreenRuntime::executeActiveDialogAction()
{
    sceneAdapter().executeActiveDialogAction();
}

void GameplayScreenRuntime::refreshHouseBankInputDialog()
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

void GameplayScreenRuntime::confirmHouseBankInput()
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

void GameplayScreenRuntime::closeInventoryNestedOverlay()
{
    uiController().closeInventoryNestedOverlay();
    interactionState().inventoryNestedOverlayItemClickLatch = false;
}

bool GameplayScreenRuntime::tryAutoPlaceHeldInventoryItemOnPartyMember(size_t memberIndex, bool showFailureStatus)
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

void GameplayScreenRuntime::closeSpellbookOverlay(const std::string &statusText)
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

bool GameplayScreenRuntime::tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen)
{
    return sceneAdapter().tryUseHeldItemOnPartyMember(memberIndex, keepCharacterScreenOpen);
}

void GameplayScreenRuntime::updateReadableScrollOverlayForHeldItem(
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

void GameplayScreenRuntime::closeReadableScrollOverlay()
{
    uiController().closeReadableScrollOverlay();
}

void GameplayScreenRuntime::resetDialogueOverlayInteractionState()
{
    interactionState().eventDialogSelectUpLatch = false;
    interactionState().eventDialogSelectDownLatch = false;
    interactionState().eventDialogAcceptLatch = false;
    interactionState().eventDialogPartySelectLatches.fill(false);
    interactionState().dialogueClickLatch = false;
    interactionState().dialoguePressedTarget = {};
}

void GameplayScreenRuntime::resetSpellbookOverlayInteractionState()
{
    interactionState().spellbookClickLatch = false;
    interactionState().spellbookPressedTarget = {};
}

void GameplayScreenRuntime::resetCharacterOverlayInteractionState()
{
    interactionState().characterClickLatch = false;
    interactionState().characterMemberCycleLatch = false;
    interactionState().characterPressedTarget = {};
}

void GameplayScreenRuntime::triggerPortraitFaceAnimation(size_t memberIndex, FaceAnimationId animationId)
{
    sceneAdapter().triggerPortraitFaceAnimation(memberIndex, animationId);
}

void GameplayScreenRuntime::playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
{
    sceneAdapter().playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
}

bool GameplayScreenRuntime::tryCastSpellFromMember(size_t casterMemberIndex, uint32_t spellId, const std::string &spellName)
{
    return sceneAdapter().tryCastSpellFromMember(casterMemberIndex, spellId, spellName);
}

bool GameplayScreenRuntime::tryCastSpellRequest(
    const PartySpellCastRequest &request,
    const std::string &spellName)
{
    return sceneAdapter().tryCastSpellRequest(request, spellName);
}

void GameplayScreenRuntime::resetUtilitySpellOverlayInteractionState()
{
    interactionState().utilitySpellClickLatch = false;
    interactionState().utilitySpellPressedTarget = {};
}

void GameplayScreenRuntime::resetInventoryNestedOverlayInteractionState()
{
    interactionState().inventoryNestedOverlayClickLatch = false;
    interactionState().inventoryNestedOverlayPressedTarget = {};
    interactionState().inventoryNestedOverlayItemClickLatch = false;
}

void GameplayScreenRuntime::resetLootOverlayInteractionState()
{
    interactionState().closeOverlayLatch = false;
    interactionState().chestClickLatch = false;
    interactionState().chestItemClickLatch = false;
    interactionState().chestPressedTarget = {};
    closeInventoryNestedOverlay();
    interactionState().lootChestItemLatch = false;
    interactionState().chestSelectUpLatch = false;
    interactionState().chestSelectDownLatch = false;
    interactionState().chestSelectionIndex = 0;
    resetInventoryNestedOverlayInteractionState();
}

GameSettings &GameplayScreenRuntime::mutableSettings() const
{
    return *m_pSettings;
}

const std::array<uint8_t, SDL_SCANCODE_COUNT> &GameplayScreenRuntime::previousKeyboardState() const
{
    return m_session.previousKeyboardState();
}

void GameplayScreenRuntime::commitSettingsChange()
{
    if (m_pSettings != nullptr)
    {
        m_session.notifySettingsChanged(*m_pSettings);
    }
}

bool GameplayScreenRuntime::trySaveToSelectedGameSlot()
{
    return sceneAdapter().trySaveToSelectedGameSlot();
}

int GameplayScreenRuntime::restFoodRequired() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->restFoodRequired() : 2;
}

const GameSettings &GameplayScreenRuntime::settingsSnapshot() const
{
    return *m_pSettings;
}

void GameplayScreenRuntime::bindAssetFileSystem(const Engine::AssetFileSystem *pAssetFileSystem)
{
    uiRuntime().bindAssetFileSystem(pAssetFileSystem);
}

void GameplayScreenRuntime::clearUiControllerRuntimeState()
{
    uiController().clearRuntimeState();
}

bool GameplayScreenRuntime::ensureGameplayLayoutsLoaded()
{
    return uiRuntime().ensureGameplayLayoutsLoaded(uiController());
}

void GameplayScreenRuntime::preloadReferencedAssets()
{
    uiRuntime().preloadReferencedAssets();
}

bool GameplayScreenRuntime::ensurePortraitRuntimeLoaded()
{
    return uiRuntime().ensurePortraitRuntimeLoaded();
}

void GameplayScreenRuntime::resetPortraitFxStates(size_t memberCount)
{
    uiRuntime().resetPortraitFxStates(memberCount);
}

void GameplayScreenRuntime::resetOverlayInteractionState()
{
    interactionState() = {};
}

bool GameplayScreenRuntime::initializeHouseVideoPlayer()
{
    return uiRuntime().initializeHouseVideoPlayer();
}

void GameplayScreenRuntime::shutdownHouseVideoPlayer()
{
    uiRuntime().shutdownHouseVideoPlayer();
}

void GameplayScreenRuntime::stopHouseVideoPlayback()
{
    uiRuntime().stopHouseVideoPlayback();
}

bool GameplayScreenRuntime::playHouseVideo(const std::string &videoStem)
{
    return uiRuntime().playHouseVideo(videoStem);
}

void GameplayScreenRuntime::queueBackgroundHouseVideoPreload(const std::string &videoStem)
{
    uiRuntime().queueBackgroundHouseVideoPreload(videoStem);
}

void GameplayScreenRuntime::updateHouseVideoBackgroundPreloads()
{
    uiRuntime().updateHouseVideoBackgroundPreloads();
}

void GameplayScreenRuntime::updateHouseVideoPlayback(float deltaSeconds)
{
    uiRuntime().updateHouseVideoPlayback(deltaSeconds);
}

bool GameplayScreenRuntime::isControlsRenderButtonPressed(GameplayControlsRenderButton button) const
{
    if (!interactionState().controlsClickLatch)
    {
        return false;
    }

    switch (button)
    {
        case GameplayControlsRenderButton::TurnRate16:
            return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::TurnRate16Button;
        case GameplayControlsRenderButton::TurnRate32:
            return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::TurnRate32Button;
        case GameplayControlsRenderButton::TurnRateSmooth:
            return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::TurnRateSmoothButton;
        case GameplayControlsRenderButton::WalkSound:
            return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::WalkSoundButton;
        case GameplayControlsRenderButton::ShowHits:
            return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::ShowHitsButton;
        case GameplayControlsRenderButton::AlwaysRun:
            return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::AlwaysRunButton;
        case GameplayControlsRenderButton::FlipOnExit:
            return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::FlipOnExitButton;
    }

    return false;
}

bool GameplayScreenRuntime::isVideoOptionsRenderButtonPressed(GameplayVideoOptionsRenderButton button) const
{
    if (!interactionState().videoOptionsClickLatch)
    {
        return false;
    }

    switch (button)
    {
        case GameplayVideoOptionsRenderButton::BloodSplats:
            return interactionState().videoOptionsPressedTarget.type == GameplayVideoOptionsPointerTargetType::BloodSplatsButton;
        case GameplayVideoOptionsRenderButton::ColoredLights:
            return interactionState().videoOptionsPressedTarget.type == GameplayVideoOptionsPointerTargetType::ColoredLightsButton;
        case GameplayVideoOptionsRenderButton::Tinting:
            return interactionState().videoOptionsPressedTarget.type == GameplayVideoOptionsPointerTargetType::TintingButton;
    }

    return false;
}

void GameplayScreenRuntime::clearHudLayoutRuntimeHeightOverrides()
{
    uiRuntime().clearHudLayoutRuntimeHeightOverrides();
}

void GameplayScreenRuntime::setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height)
{
    uiRuntime().setHudLayoutRuntimeHeightOverride(layoutId, height);
}

const HouseEntry *GameplayScreenRuntime::findHouseEntry(uint32_t houseId) const
{
    return houseTable() != nullptr ? houseTable()->get(houseId) : nullptr;
}

const GameplayScreenRuntime::HudLayoutElement *GameplayScreenRuntime::findHudLayoutElement(
    const std::string &layoutId) const
{
    return uiRuntime().findHudLayoutElement(layoutId);
}

int GameplayScreenRuntime::defaultHudLayoutZIndexForScreen(const std::string &screen) const
{
    return uiRuntime().defaultHudLayoutZIndexForScreen(screen);
}

GameplayHudScreenState GameplayScreenRuntime::currentHudScreenState() const
{
    return resolveGameplayHudScreenState(uiController(), activeEventDialog(), worldRuntime());
}

std::vector<std::string> GameplayScreenRuntime::sortedHudLayoutIdsForScreen(const std::string &screen) const
{
    return uiRuntime().sortedHudLayoutIdsForScreen(screen);
}

std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> GameplayScreenRuntime::resolveHudLayoutElement(
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight) const
{
    return uiRuntime().resolveHudLayoutElement(layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight);
}

std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> GameplayScreenRuntime::resolvePartyPortraitRect(
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
        const_cast<GameplayScreenRuntime *>(this)->ensureHudTextureLoaded(pBasebarLayout->primaryAsset);
    const std::optional<HudTextureHandle> faceMaskTexture =
        const_cast<GameplayScreenRuntime *>(this)->ensureHudTextureLoaded(pPartyStripLayout->primaryAsset);

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

std::optional<size_t> GameplayScreenRuntime::resolvePartyPortraitIndexAtPoint(
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

std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> GameplayScreenRuntime::resolveChestGridArea(
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

std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement>
GameplayScreenRuntime::resolveInventoryNestedOverlayGridArea(
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

std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> GameplayScreenRuntime::resolveHouseShopOverlayFrame(
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

bool GameplayScreenRuntime::isPointerInsideResolvedElement(
    const ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY) const
{
    return GameplayHudCommon::isPointerInsideResolvedElement(resolved, pointerX, pointerY);
}

const std::string *GameplayScreenRuntime::resolveInteractiveAssetName(
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

std::optional<GameplayScreenRuntime::HudTextureHandle> GameplayScreenRuntime::ensureHudTextureLoaded(
    const std::string &textureName)
{
    return uiRuntime().ensureHudTextureLoaded(textureName);
}

std::optional<GameplayScreenRuntime::HudTextureHandle> GameplayScreenRuntime::ensureSolidHudTextureLoaded(
    const std::string &textureName,
    uint32_t abgrColor)
{
    return uiRuntime().ensureSolidHudTextureLoaded(textureName, abgrColor);
}

std::optional<GameplayScreenRuntime::HudTextureHandle> GameplayScreenRuntime::ensureDynamicHudTexture(
    const std::string &textureName,
    int width,
    int height,
    const std::vector<uint8_t> &bgraPixels)
{
    return uiRuntime().ensureDynamicHudTexture(textureName, width, height, bgraPixels);
}

std::optional<std::vector<uint8_t>> GameplayScreenRuntime::loadSpriteBitmapPixelsBgraCached(
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height)
{
    return uiRuntime().loadSpriteBitmapPixelsBgraCached(textureName, paletteId, width, height);
}

const std::vector<uint8_t> *GameplayScreenRuntime::hudTexturePixels(
    const std::string &textureName,
    int &width,
    int &height)
{
    return uiRuntime().hudTexturePixels(textureName, width, height);
}

bool GameplayScreenRuntime::ensureHudTextureDimensions(const std::string &textureName, int &width, int &height)
{
    return uiRuntime().ensureHudTextureDimensions(textureName, width, height);
}

bool GameplayScreenRuntime::tryGetOpaqueHudTextureBounds(
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

void GameplayScreenRuntime::submitHudTexturedQuad(
    const HudTextureHandle &texture,
    float x,
    float y,
    float quadWidth,
    float quadHeight) const
{
    uiRuntime().submitHudTexturedQuad(texture.textureHandle, x, y, quadWidth, quadHeight);
}

bgfx::TextureHandle GameplayScreenRuntime::ensureHudTextureColor(const HudTextureHandle &texture, uint32_t colorAbgr) const
{
    return uiRuntime().ensureHudTextureColor(texture, colorAbgr);
}

void GameplayScreenRuntime::renderLayoutLabel(
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

std::optional<GameplayScreenRuntime::HudFontHandle> GameplayScreenRuntime::findHudFont(const std::string &fontName) const
{
    return uiRuntime().findHudFont(fontName);
}

float GameplayScreenRuntime::measureHudTextWidth(const HudFontHandle &font, const std::string &text) const
{
    return uiRuntime().measureHudTextWidth(font, text);
}

std::vector<std::string> GameplayScreenRuntime::wrapHudTextToWidth(
    const HudFontHandle &font,
    const std::string &text,
    float maxWidth) const
{
    return uiRuntime().wrapHudTextToWidth(font, text, maxWidth);
}

bgfx::TextureHandle GameplayScreenRuntime::ensureHudFontMainTextureColor(
    const HudFontHandle &font,
    uint32_t colorAbgr) const
{
    return uiRuntime().ensureHudFontMainTextureColor(font, colorAbgr);
}

void GameplayScreenRuntime::renderHudFontLayer(
    const HudFontHandle &font,
    bgfx::TextureHandle textureHandle,
    const std::string &text,
    float textX,
    float textY,
    float fontScale) const
{
    uiRuntime().renderHudFontLayer(font, textureHandle, text, textX, textY, fontScale);
}

void GameplayScreenRuntime::bindHudRenderBackend(const GameplayHudRenderBackend &backend)
{
    uiRuntime().bindHudRenderBackend(backend);
}

void GameplayScreenRuntime::clearHudRenderBackend()
{
    uiRuntime().clearHudRenderBackend();
}

void GameplayScreenRuntime::releaseHudGpuResources(bool destroyBgfxResources)
{
    uiRuntime().releaseHudGpuResources(destroyBgfxResources);
}

void GameplayScreenRuntime::clearSharedUiRuntime()
{
    uiRuntime().clear();
}

bool GameplayScreenRuntime::hasHudRenderResources() const
{
    return uiRuntime().hasHudRenderResources();
}

void GameplayScreenRuntime::prepareHudView(int width, int height) const
{
    uiRuntime().prepareHudView(width, height);
}

void GameplayScreenRuntime::submitHudQuadBatch(
    const std::vector<GameplayHudBatchQuad> &quads,
    int screenWidth,
    int screenHeight) const
{
    uiRuntime().submitHudQuadBatch(quads, screenWidth, screenHeight);
}

void GameplayScreenRuntime::renderViewportSidePanels(
    int screenWidth,
    int screenHeight,
    const std::string &textureName)
{
    if (screenWidth <= 0 || screenHeight <= 0)
    {
        return;
    }

    const GameplayUiViewportRect viewport = GameplayHudCommon::computeUiViewportRect(screenWidth, screenHeight);

    if (viewport.x <= 0.5f)
    {
        return;
    }

    const std::optional<HudTextureHandle> texture = ensureHudTextureLoaded(textureName);

    if (!texture)
    {
        return;
    }

    submitHudTexturedQuad(*texture, 0.0f, 0.0f, viewport.x, static_cast<float>(screenHeight));

    const float rightX = viewport.x + viewport.width;
    const float rightWidth = static_cast<float>(screenWidth) - rightX;

    if (rightWidth > 0.5f)
    {
        submitHudTexturedQuad(*texture, rightX, 0.0f, rightWidth, static_cast<float>(screenHeight));
    }
}

std::string GameplayScreenRuntime::resolvePortraitTextureName(const Character &character) const
{
    return uiRuntime().resolvePortraitTextureName(character);
}

void GameplayScreenRuntime::consumePendingPortraitEventFxRequests()
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

void GameplayScreenRuntime::renderPortraitFx(
    size_t memberIndex,
    float portraitX,
    float portraitY,
    float portraitWidth,
    float portraitHeight) const
{
    uiRuntime().renderPortraitFx(memberIndex, portraitX, portraitY, portraitWidth, portraitHeight);
}

bool GameplayScreenRuntime::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    state = {};
    return pWorldRuntime != nullptr && pWorldRuntime->tryGetGameplayMinimapState(state);
}

void GameplayScreenRuntime::collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        markers.clear();
        return;
    }

    pWorldRuntime->collectGameplayMinimapMarkers(markers);
}

bool GameplayScreenRuntime::ensureTownPortalDestinationsLoaded()
{
    return uiRuntime().ensureTownPortalDestinationsLoaded();
}

const std::vector<GameplayTownPortalDestination> &GameplayScreenRuntime::townPortalDestinations() const
{
    return uiRuntime().townPortalDestinations();
}

std::string GameplayScreenRuntime::resolveMapLocationName(const std::string &mapFileName) const
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

float GameplayScreenRuntime::measureHudTextWidth(const std::string &fontName, const std::string &text) const
{
    const std::optional<HudFontHandle> font = findHudFont(fontName);
    return font ? measureHudTextWidth(*font, text) : 0.0f;
}

int GameplayScreenRuntime::hudFontHeight(const std::string &fontName) const
{
    const std::optional<HudFontHandle> font = findHudFont(fontName);
    return font ? font->fontHeight : 0;
}

std::vector<std::string> GameplayScreenRuntime::wrapHudTextToWidth(
    const std::string &fontName,
    const std::string &text,
    float maxWidth) const
{
    const std::optional<HudFontHandle> font = findHudFont(fontName);
    return font ? wrapHudTextToWidth(*font, text, maxWidth) : std::vector<std::string>{text};
}

void GameplayScreenRuntime::renderHudTextLine(
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

void GameplayScreenRuntime::resetHudTransientState() const
{
    uiRuntime().clearRenderedInspectableHudItems();
    uiRuntime().clearHudLayoutRuntimeHeightOverrides();
}

void GameplayScreenRuntime::addRenderedInspectableHudItem(const GameplayRenderedInspectableHudItem &item) const
{
    uiRuntime().addRenderedInspectableHudItem(item);
}

const std::vector<GameplayRenderedInspectableHudItem> &GameplayScreenRuntime::renderedInspectableHudItems() const
{
    return uiRuntime().renderedInspectableHudItems();
}

void GameplayScreenRuntime::beginRenderedInspectableHudFrame() const
{
    uiRuntime().clearRenderedInspectableHudItems();
    uiRuntime().setRenderedInspectableHudScreenState(currentHudScreenState());
}

GameplayHudScreenState GameplayScreenRuntime::renderedInspectableHudScreenState() const
{
    return uiRuntime().renderedInspectableHudScreenState();
}

bool GameplayScreenRuntime::isOpaqueHudPixelAtPoint(
    const GameplayRenderedInspectableHudItem &item,
    float x,
    float y) const
{
    return uiRuntime().isOpaqueHudPixelAtPoint(item, x, y);
}

const PortraitFxEventEntry *GameplayScreenRuntime::findPortraitFxEvent(PortraitFxEventKind kind) const
{
    return uiRuntime().findPortraitFxEvent(kind);
}

uint32_t GameplayScreenRuntime::defaultPortraitAnimationLengthTicks(PortraitId portraitId) const
{
    return uiRuntime().defaultPortraitAnimationLengthTicks(portraitId);
}

bool GameplayScreenRuntime::triggerPortraitFxAnimation(
    const std::string &animationName,
    const std::vector<size_t> &memberIndices)
{
    return uiRuntime().triggerPortraitFxAnimation(animationName, memberIndices);
}

void GameplayScreenRuntime::triggerPortraitSpellFx(const PartySpellCastResult &result)
{
    uiRuntime().triggerPortraitSpellFx(result);
}

std::string GameplayScreenRuntime::resolveEquippedItemHudTextureName(
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

std::optional<GameplayResolvedHudLayoutElement> GameplayScreenRuntime::resolveCharacterEquipmentRenderRect(
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

void GameplayScreenRuntime::submitWorldTextureQuad(
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

bool GameplayScreenRuntime::renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const
{
    return uiRuntime().renderHouseVideoFrame(x, y, quadWidth, quadHeight);
}
} // namespace OpenYAMM::Game
