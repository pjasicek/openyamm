#include "game/ui/GameplayOverlayContext.h"

#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/party/SpellSchool.h"
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
    IGameplayOverlaySceneAdapter &sceneAdapter,
    IGameplayOverlayHudAdapter &hudAdapter)
    : m_session(session)
    , m_pAudioSystem(pAudioSystem)
    , m_pSettings(pSettings)
    , m_sceneAdapter(sceneAdapter)
    , m_hudAdapter(hudAdapter)
{
}

GameplayUiController &GameplayOverlayContext::uiController() const
{
    return m_session.gameplayUiController();
}

GameplayOverlayInteractionState &GameplayOverlayContext::interactionState() const
{
    return m_session.overlayInteractionState();
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

bool &GameplayOverlayContext::closeOverlayLatch() const
{
    return interactionState().closeOverlayLatch;
}

bool &GameplayOverlayContext::restClickLatch() const
{
    return interactionState().restClickLatch;
}

GameplayRestPointerTarget &GameplayOverlayContext::restPressedTarget() const
{
    return interactionState().restPressedTarget;
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
    m_sceneAdapter.handleDialogueCloseRequest();
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
    m_sceneAdapter.requestOpenNewGameScreen();
}

void GameplayOverlayContext::requestOpenLoadGameScreen()
{
    m_sceneAdapter.requestOpenLoadGameScreen();
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

void GameplayOverlayContext::executeActiveDialogAction()
{
    m_sceneAdapter.executeActiveDialogAction();
}

void GameplayOverlayContext::refreshHouseBankInputDialog()
{
    m_sceneAdapter.refreshHouseBankInputDialog();
}

void GameplayOverlayContext::confirmHouseBankInput()
{
    m_sceneAdapter.confirmHouseBankInput();
}

void GameplayOverlayContext::closeInventoryNestedOverlay()
{
    uiController().closeInventoryNestedOverlay();
    interactionState().inventoryNestedOverlayItemClickLatch = false;
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

void GameplayOverlayContext::resetInventoryNestedOverlayInteractionState()
{
    m_sceneAdapter.resetInventoryNestedOverlayInteractionState();
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
    m_sceneAdapter.commitSettingsChange();
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
    m_hudAdapter.clearHudLayoutRuntimeHeightOverrides();
}

void GameplayOverlayContext::setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height)
{
    m_hudAdapter.setHudLayoutRuntimeHeightOverride(layoutId, height);
}

const HouseEntry *GameplayOverlayContext::findHouseEntry(uint32_t houseId) const
{
    return houseTable() != nullptr ? houseTable()->get(houseId) : nullptr;
}

const GameplayOverlayContext::HudLayoutElement *GameplayOverlayContext::findHudLayoutElement(
    const std::string &layoutId) const
{
    return m_hudAdapter.findHudLayoutElement(layoutId);
}

int GameplayOverlayContext::defaultHudLayoutZIndexForScreen(const std::string &screen) const
{
    return m_hudAdapter.defaultHudLayoutZIndexForScreen(screen);
}

GameplayHudScreenState GameplayOverlayContext::currentHudScreenState() const
{
    return m_hudAdapter.currentGameplayHudScreenState();
}

std::vector<std::string> GameplayOverlayContext::sortedHudLayoutIdsForScreen(const std::string &screen) const
{
    return m_hudAdapter.sortedHudLayoutIdsForScreen(screen);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveHudLayoutElement(
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight) const
{
    return m_hudAdapter.resolveHudLayoutElement(layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveChestGridArea(
    int width,
    int height) const
{
    return m_hudAdapter.resolveGameplayChestGridArea(width, height);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>
GameplayOverlayContext::resolveInventoryNestedOverlayGridArea(
    int width,
    int height) const
{
    return m_hudAdapter.resolveGameplayInventoryNestedOverlayGridArea(width, height);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveHouseShopOverlayFrame(
    int width,
    int height) const
{
    return m_hudAdapter.resolveGameplayHouseShopOverlayFrame(width, height);
}

bool GameplayOverlayContext::isPointerInsideResolvedElement(
    const ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY) const
{
    return m_hudAdapter.isPointerInsideResolvedElement(resolved, pointerX, pointerY);
}

const std::string *GameplayOverlayContext::resolveInteractiveAssetName(
    const HudLayoutElement &layout,
    const ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY,
    bool isLeftMousePressed) const
{
    const std::optional<std::string> assetName =
        m_hudAdapter.resolveInteractiveAssetName(layout, resolved, pointerX, pointerY, isLeftMousePressed);

    if (!assetName)
    {
        return nullptr;
    }

    m_resolvedInteractiveAssetName = *assetName;
    return &*m_resolvedInteractiveAssetName;
}

std::optional<GameplayOverlayContext::HudTextureHandle> GameplayOverlayContext::ensureHudTextureLoaded(
    const std::string &textureName)
{
    return m_hudAdapter.ensureHudTextureLoaded(textureName);
}

std::optional<GameplayOverlayContext::HudTextureHandle> GameplayOverlayContext::ensureSolidHudTextureLoaded(
    const std::string &textureName,
    uint32_t abgrColor)
{
    return m_hudAdapter.ensureSolidHudTextureLoaded(textureName, abgrColor);
}

std::optional<GameplayOverlayContext::HudTextureHandle> GameplayOverlayContext::ensureDynamicHudTexture(
    const std::string &textureName,
    int width,
    int height,
    const std::vector<uint8_t> &bgraPixels)
{
    return m_hudAdapter.ensureDynamicHudTexture(textureName, width, height, bgraPixels);
}

const std::vector<uint8_t> *GameplayOverlayContext::hudTexturePixels(
    const std::string &textureName,
    int &width,
    int &height)
{
    return m_hudAdapter.hudTexturePixels(textureName, width, height);
}

bool GameplayOverlayContext::ensureHudTextureDimensions(const std::string &textureName, int &width, int &height)
{
    return m_hudAdapter.ensureHudTextureDimensions(textureName, width, height);
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
    return m_hudAdapter.tryGetOpaqueHudTextureBounds(
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
    m_hudAdapter.submitHudTexturedQuad(texture, x, y, quadWidth, quadHeight);
}

bgfx::TextureHandle GameplayOverlayContext::ensureHudTextureColor(const HudTextureHandle &texture, uint32_t colorAbgr) const
{
    return m_hudAdapter.ensureHudTextureColor(texture, colorAbgr);
}

void GameplayOverlayContext::renderLayoutLabel(
    const HudLayoutElement &layout,
    const ResolvedHudLayoutElement &resolved,
    const std::string &label) const
{
    m_hudAdapter.renderLayoutLabel(layout, resolved, label);
}

std::optional<GameplayOverlayContext::HudFontHandle> GameplayOverlayContext::findHudFont(const std::string &fontName) const
{
    return m_hudAdapter.findHudFont(fontName);
}

float GameplayOverlayContext::measureHudTextWidth(const HudFontHandle &font, const std::string &text) const
{
    return m_hudAdapter.measureHudTextWidth(font, text);
}

std::vector<std::string> GameplayOverlayContext::wrapHudTextToWidth(
    const HudFontHandle &font,
    const std::string &text,
    float maxWidth) const
{
    return m_hudAdapter.wrapHudTextToWidth(font, text, maxWidth);
}

bgfx::TextureHandle GameplayOverlayContext::ensureHudFontMainTextureColor(
    const HudFontHandle &font,
    uint32_t colorAbgr) const
{
    return m_hudAdapter.ensureHudFontMainTextureColor(font, colorAbgr);
}

void GameplayOverlayContext::renderHudFontLayer(
    const HudFontHandle &font,
    bgfx::TextureHandle textureHandle,
    const std::string &text,
    float textX,
    float textY,
    float fontScale) const
{
    m_hudAdapter.renderHudFontLayer(font, textureHandle, text, textX, textY, fontScale);
}

bool GameplayOverlayContext::hasHudRenderResources() const
{
    return m_hudAdapter.hasHudRenderResources();
}

void GameplayOverlayContext::prepareHudView(int width, int height) const
{
    m_hudAdapter.prepareHudView(width, height);
}

void GameplayOverlayContext::submitHudQuadBatch(
    const std::vector<GameplayHudBatchQuad> &quads,
    int screenWidth,
    int screenHeight) const
{
    m_hudAdapter.submitHudQuadBatch(quads, screenWidth, screenHeight);
}

std::string GameplayOverlayContext::resolvePortraitTextureName(const Character &character) const
{
    return m_hudAdapter.resolvePortraitTextureName(character);
}

void GameplayOverlayContext::consumePendingPortraitEventFxRequests()
{
    m_hudAdapter.consumePendingPortraitEventFxRequests();
}

void GameplayOverlayContext::renderPortraitFx(
    size_t memberIndex,
    float portraitX,
    float portraitY,
    float portraitWidth,
    float portraitHeight) const
{
    m_hudAdapter.renderPortraitFx(memberIndex, portraitX, portraitY, portraitWidth, portraitHeight);
}

bool GameplayOverlayContext::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    return m_hudAdapter.tryGetGameplayMinimapState(state);
}

void GameplayOverlayContext::collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const
{
    m_hudAdapter.collectGameplayMinimapMarkers(markers);
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
    m_hudAdapter.addRenderedInspectableHudItem(item);
}

const std::vector<GameplayRenderedInspectableHudItem> &GameplayOverlayContext::renderedInspectableHudItems() const
{
    return m_hudAdapter.renderedInspectableHudItems();
}

bool GameplayOverlayContext::isOpaqueHudPixelAtPoint(
    const GameplayRenderedInspectableHudItem &item,
    float x,
    float y) const
{
    return m_hudAdapter.isOpaqueHudPixelAtPoint(item, x, y);
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
    m_hudAdapter.submitWorldTextureQuad(textureHandle, x, y, quadWidth, quadHeight, u0, v0, u1, v1);
}

bool GameplayOverlayContext::renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const
{
    return m_hudAdapter.renderHouseVideoFrame(x, y, quadWidth, quadHeight);
}
} // namespace OpenYAMM::Game
