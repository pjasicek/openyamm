#include "game/ui/GameplayOverlayContext.h"

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

GameplayOverlayContext::GameplayOverlayContext(IGameplayOverlayView &view)
    : m_view(view)
{
}

IGameplayWorldRuntime *GameplayOverlayContext::worldRuntime() const
{
    return m_view.worldRuntime();
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
    return m_view.audioSystem();
}

const ItemTable *GameplayOverlayContext::itemTable() const
{
    return m_view.itemTable();
}

const StandardItemEnchantTable *GameplayOverlayContext::standardItemEnchantTable() const
{
    return m_view.standardItemEnchantTable();
}

const SpecialItemEnchantTable *GameplayOverlayContext::specialItemEnchantTable() const
{
    return m_view.specialItemEnchantTable();
}

const ClassSkillTable *GameplayOverlayContext::classSkillTable() const
{
    return m_view.classSkillTable();
}

const CharacterDollTable *GameplayOverlayContext::characterDollTable() const
{
    return m_view.characterDollTable();
}

const CharacterInspectTable *GameplayOverlayContext::characterInspectTable() const
{
    return m_view.characterInspectTable();
}

const RosterTable *GameplayOverlayContext::rosterTable() const
{
    return m_view.rosterTable();
}

const ReadableScrollTable *GameplayOverlayContext::readableScrollTable() const
{
    return m_view.readableScrollTable();
}

const ItemEquipPosTable *GameplayOverlayContext::itemEquipPosTable() const
{
    return m_view.itemEquipPosTable();
}

const SpellTable *GameplayOverlayContext::spellTable() const
{
    return m_view.spellTable();
}

const std::optional<HouseTable> &GameplayOverlayContext::houseTable() const
{
    return m_view.houseTable();
}

const std::optional<ChestTable> &GameplayOverlayContext::chestTable() const
{
    return m_view.chestTable();
}

const std::optional<NpcDialogTable> &GameplayOverlayContext::npcDialogTable() const
{
    return m_view.npcDialogTable();
}

GameplayUiController::CharacterScreenState &GameplayOverlayContext::characterScreen() const
{
    return m_view.characterScreen();
}

GameplayUiController::HeldInventoryItemState &GameplayOverlayContext::heldInventoryItem() const
{
    return m_view.heldInventoryItem();
}

GameplayUiController::ItemInspectOverlayState &GameplayOverlayContext::itemInspectOverlay() const
{
    return m_view.itemInspectOverlay();
}

GameplayUiController::CharacterInspectOverlayState &GameplayOverlayContext::characterInspectOverlay() const
{
    return m_view.characterInspectOverlay();
}

GameplayUiController::BuffInspectOverlayState &GameplayOverlayContext::buffInspectOverlay() const
{
    return m_view.buffInspectOverlay();
}

GameplayUiController::CharacterDetailOverlayState &GameplayOverlayContext::characterDetailOverlay() const
{
    return m_view.characterDetailOverlay();
}

GameplayUiController::ActorInspectOverlayState &GameplayOverlayContext::actorInspectOverlay() const
{
    return m_view.actorInspectOverlay();
}

GameplayUiController::SpellInspectOverlayState &GameplayOverlayContext::spellInspectOverlay() const
{
    return m_view.spellInspectOverlay();
}

GameplayUiController::ReadableScrollOverlayState &GameplayOverlayContext::readableScrollOverlay() const
{
    return m_view.readableScrollOverlay();
}

GameplayUiController::SpellbookState &GameplayOverlayContext::spellbook() const
{
    return m_view.spellbook();
}

GameplayUiController::UtilitySpellOverlayState &GameplayOverlayContext::utilitySpellOverlay() const
{
    return m_view.utilitySpellOverlay();
}

GameplayUiController::InventoryNestedOverlayState &GameplayOverlayContext::inventoryNestedOverlay() const
{
    return m_view.inventoryNestedOverlay();
}

GameplayUiController::HouseShopOverlayState &GameplayOverlayContext::houseShopOverlay() const
{
    return m_view.houseShopOverlay();
}

GameplayUiController::HouseBankState &GameplayOverlayContext::houseBankState() const
{
    return m_view.houseBankState();
}

GameplayUiController::JournalScreenState &GameplayOverlayContext::journalScreenState() const
{
    return m_view.journalScreenState();
}

GameplayUiController::RestScreenState &GameplayOverlayContext::restScreenState() const
{
    return m_view.restScreenState();
}

GameplayUiController::MenuScreenState &GameplayOverlayContext::menuScreenState() const
{
    return m_view.menuScreenState();
}

GameplayUiController::ControlsScreenState &GameplayOverlayContext::controlsScreenState() const
{
    return m_view.controlsScreenState();
}

GameplayUiController::KeyboardScreenState &GameplayOverlayContext::keyboardScreenState() const
{
    return m_view.keyboardScreenState();
}

GameplayUiController::VideoOptionsScreenState &GameplayOverlayContext::videoOptionsScreenState() const
{
    return m_view.videoOptionsScreenState();
}

GameplayUiController::SaveGameScreenState &GameplayOverlayContext::saveGameScreenState() const
{
    return m_view.saveGameScreenState();
}

GameplayUiController::LoadGameScreenState &GameplayOverlayContext::loadGameScreenState() const
{
    return m_view.loadGameScreenState();
}

const GameplayUiController::CharacterScreenState &GameplayOverlayContext::characterScreenReadOnly() const
{
    return m_view.characterScreen();
}

const GameplayUiController::ItemInspectOverlayState &GameplayOverlayContext::itemInspectOverlayReadOnly() const
{
    return m_view.itemInspectOverlay();
}

const GameplayUiController::CharacterInspectOverlayState &GameplayOverlayContext::characterInspectOverlayReadOnly() const
{
    return m_view.characterInspectOverlay();
}

const GameplayUiController::BuffInspectOverlayState &GameplayOverlayContext::buffInspectOverlayReadOnly() const
{
    return m_view.buffInspectOverlay();
}

const GameplayUiController::CharacterDetailOverlayState &GameplayOverlayContext::characterDetailOverlayReadOnly() const
{
    return m_view.characterDetailOverlay();
}

const GameplayUiController::ActorInspectOverlayState &GameplayOverlayContext::actorInspectOverlayReadOnly() const
{
    return m_view.actorInspectOverlay();
}

const GameplayUiController::SpellInspectOverlayState &GameplayOverlayContext::spellInspectOverlayReadOnly() const
{
    return m_view.spellInspectOverlay();
}

const GameplayUiController::ReadableScrollOverlayState &GameplayOverlayContext::readableScrollOverlayReadOnly() const
{
    return m_view.readableScrollOverlay();
}

const GameplayUiController::SpellbookState &GameplayOverlayContext::spellbookReadOnly() const
{
    return m_view.spellbook();
}

const GameplayUiController::UtilitySpellOverlayState &GameplayOverlayContext::utilitySpellOverlayReadOnly() const
{
    return m_view.utilitySpellOverlay();
}

const GameplayUiController::JournalScreenState &GameplayOverlayContext::journalScreenStateReadOnly() const
{
    return m_view.journalScreenState();
}

const JournalQuestTable *GameplayOverlayContext::journalQuestTable() const
{
    return m_view.journalQuestTable();
}

const JournalHistoryTable *GameplayOverlayContext::journalHistoryTable() const
{
    return m_view.journalHistoryTable();
}

const JournalAutonoteTable *GameplayOverlayContext::journalAutonoteTable() const
{
    return m_view.journalAutonoteTable();
}

const std::string &GameplayOverlayContext::currentMapFileName() const
{
    return m_view.currentMapFileName();
}

float GameplayOverlayContext::gameplayCameraYawRadians() const
{
    return m_view.gameplayCameraYawRadians();
}

const std::vector<uint8_t> *GameplayOverlayContext::journalMapFullyRevealedCells() const
{
    return m_view.journalMapFullyRevealedCells();
}

const std::vector<uint8_t> *GameplayOverlayContext::journalMapPartiallyRevealedCells() const
{
    return m_view.journalMapPartiallyRevealedCells();
}

EventDialogContent &GameplayOverlayContext::activeEventDialog() const
{
    return m_view.activeEventDialog();
}

std::string &GameplayOverlayContext::statusBarEventText() const
{
    return m_view.statusBarEventText();
}

float &GameplayOverlayContext::statusBarEventRemainingSeconds() const
{
    return m_view.statusBarEventRemainingSeconds();
}

const std::string &GameplayOverlayContext::statusBarHoverText() const
{
    return m_view.statusBarHoverText();
}

bool &GameplayOverlayContext::closeOverlayLatch() const
{
    return m_view.closeOverlayLatch();
}

bool &GameplayOverlayContext::restClickLatch() const
{
    return m_view.restClickLatch();
}

GameplayRestPointerTarget &GameplayOverlayContext::restPressedTarget() const
{
    return m_view.restPressedTarget();
}

bool &GameplayOverlayContext::menuToggleLatch() const
{
    return m_view.menuToggleLatch();
}

bool &GameplayOverlayContext::menuClickLatch() const
{
    return m_view.menuClickLatch();
}

GameplayMenuPointerTarget &GameplayOverlayContext::menuPressedTarget() const
{
    return m_view.menuPressedTarget();
}

bool &GameplayOverlayContext::controlsToggleLatch() const
{
    return m_view.controlsToggleLatch();
}

bool &GameplayOverlayContext::controlsClickLatch() const
{
    return m_view.controlsClickLatch();
}

GameplayControlsPointerTarget &GameplayOverlayContext::controlsPressedTarget() const
{
    return m_view.controlsPressedTarget();
}

bool &GameplayOverlayContext::controlsSliderDragActive() const
{
    return m_view.controlsSliderDragActive();
}

GameplayControlsPointerTargetType &GameplayOverlayContext::controlsDraggedSlider() const
{
    return m_view.controlsDraggedSlider();
}

bool &GameplayOverlayContext::keyboardToggleLatch() const
{
    return m_view.keyboardToggleLatch();
}

bool &GameplayOverlayContext::keyboardClickLatch() const
{
    return m_view.keyboardClickLatch();
}

GameplayKeyboardPointerTarget &GameplayOverlayContext::keyboardPressedTarget() const
{
    return m_view.keyboardPressedTarget();
}

bool &GameplayOverlayContext::videoOptionsToggleLatch() const
{
    return m_view.videoOptionsToggleLatch();
}

bool &GameplayOverlayContext::videoOptionsClickLatch() const
{
    return m_view.videoOptionsClickLatch();
}

GameplayVideoOptionsPointerTarget &GameplayOverlayContext::videoOptionsPressedTarget() const
{
    return m_view.videoOptionsPressedTarget();
}

bool &GameplayOverlayContext::saveGameToggleLatch() const
{
    return m_view.saveGameToggleLatch();
}

bool &GameplayOverlayContext::saveGameClickLatch() const
{
    return m_view.saveGameClickLatch();
}

GameplaySaveLoadPointerTarget &GameplayOverlayContext::saveGamePressedTarget() const
{
    return m_view.saveGamePressedTarget();
}

bool &GameplayOverlayContext::characterClickLatch() const
{
    return m_view.characterClickLatch();
}

GameplayCharacterPointerTarget &GameplayOverlayContext::characterPressedTarget() const
{
    return m_view.characterPressedTarget();
}

bool &GameplayOverlayContext::characterMemberCycleLatch() const
{
    return m_view.characterMemberCycleLatch();
}

std::optional<size_t> &GameplayOverlayContext::pendingCharacterDismissMemberIndex() const
{
    return m_view.pendingCharacterDismissMemberIndex();
}

uint64_t &GameplayOverlayContext::pendingCharacterDismissExpiresTicks() const
{
    return m_view.pendingCharacterDismissExpiresTicks();
}

bool &GameplayOverlayContext::spellbookClickLatch() const
{
    return m_view.spellbookClickLatch();
}

GameplaySpellbookPointerTarget &GameplayOverlayContext::spellbookPressedTarget() const
{
    return m_view.spellbookPressedTarget();
}

uint64_t &GameplayOverlayContext::lastSpellbookSpellClickTicks() const
{
    return m_view.lastSpellbookSpellClickTicks();
}

uint32_t &GameplayOverlayContext::lastSpellbookClickedSpellId() const
{
    return m_view.lastSpellbookClickedSpellId();
}

std::array<bool, 39> &GameplayOverlayContext::saveGameEditKeyLatches() const
{
    return m_view.saveGameEditKeyLatches();
}

bool &GameplayOverlayContext::saveGameEditBackspaceLatch() const
{
    return m_view.saveGameEditBackspaceLatch();
}

uint64_t &GameplayOverlayContext::lastSaveGameSlotClickTicks() const
{
    return m_view.lastSaveGameSlotClickTicks();
}

std::optional<size_t> &GameplayOverlayContext::lastSaveGameClickedSlotIndex() const
{
    return m_view.lastSaveGameClickedSlotIndex();
}

bool &GameplayOverlayContext::journalToggleLatch() const
{
    return m_view.journalToggleLatch();
}

bool &GameplayOverlayContext::journalClickLatch() const
{
    return m_view.journalClickLatch();
}

GameplayJournalPointerTarget &GameplayOverlayContext::journalPressedTarget() const
{
    return m_view.journalPressedTarget();
}

bool &GameplayOverlayContext::journalMapKeyZoomLatch() const
{
    return m_view.journalMapKeyZoomLatch();
}

bool &GameplayOverlayContext::dialogueClickLatch() const
{
    return m_view.dialogueClickLatch();
}

GameplayDialoguePointerTarget &GameplayOverlayContext::dialoguePressedTarget() const
{
    return m_view.dialoguePressedTarget();
}

bool &GameplayOverlayContext::houseShopClickLatch() const
{
    return m_view.houseShopClickLatch();
}

size_t &GameplayOverlayContext::houseShopPressedSlotIndex() const
{
    return m_view.houseShopPressedSlotIndex();
}

bool &GameplayOverlayContext::chestClickLatch() const
{
    return m_view.chestClickLatch();
}

bool &GameplayOverlayContext::chestItemClickLatch() const
{
    return m_view.chestItemClickLatch();
}

GameplayChestPointerTarget &GameplayOverlayContext::chestPressedTarget() const
{
    return m_view.chestPressedTarget();
}

bool &GameplayOverlayContext::inventoryNestedOverlayItemClickLatch() const
{
    return m_view.inventoryNestedOverlayItemClickLatch();
}

std::array<bool, 10> &GameplayOverlayContext::houseBankDigitLatches() const
{
    return m_view.houseBankDigitLatches();
}

bool &GameplayOverlayContext::houseBankBackspaceLatch() const
{
    return m_view.houseBankBackspaceLatch();
}

bool &GameplayOverlayContext::houseBankConfirmLatch() const
{
    return m_view.houseBankConfirmLatch();
}

bool &GameplayOverlayContext::lootChestItemLatch() const
{
    return m_view.lootChestItemLatch();
}

bool &GameplayOverlayContext::chestSelectUpLatch() const
{
    return m_view.chestSelectUpLatch();
}

bool &GameplayOverlayContext::chestSelectDownLatch() const
{
    return m_view.chestSelectDownLatch();
}

bool &GameplayOverlayContext::eventDialogSelectUpLatch() const
{
    return m_view.eventDialogSelectUpLatch();
}

bool &GameplayOverlayContext::eventDialogSelectDownLatch() const
{
    return m_view.eventDialogSelectDownLatch();
}

bool &GameplayOverlayContext::eventDialogAcceptLatch() const
{
    return m_view.eventDialogAcceptLatch();
}

std::array<bool, 5> &GameplayOverlayContext::eventDialogPartySelectLatches() const
{
    return m_view.eventDialogPartySelectLatches();
}

bool &GameplayOverlayContext::activateInspectLatch() const
{
    return m_view.activateInspectLatch();
}

size_t &GameplayOverlayContext::chestSelectionIndex() const
{
    return m_view.chestSelectionIndex();
}

size_t &GameplayOverlayContext::eventDialogSelectionIndex() const
{
    return m_view.eventDialogSelectionIndex();
}

bool GameplayOverlayContext::trySelectPartyMember(size_t memberIndex, bool requireGameplayReady)
{
    return m_view.trySelectPartyMember(memberIndex, requireGameplayReady);
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
    return m_view.activeMemberKnowsSpell(spellId);
}

bool GameplayOverlayContext::activeMemberHasSpellbookSchool(GameplayUiController::SpellbookSchool school) const
{
    return m_view.activeMemberHasSpellbookSchool(school);
}

void GameplayOverlayContext::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    m_view.setStatusBarEvent(text, durationSeconds);
}

void GameplayOverlayContext::handleDialogueCloseRequest()
{
    m_view.handleDialogueCloseRequest();
}

void GameplayOverlayContext::closeRestOverlay()
{
    m_view.closeRestOverlay();
}

void GameplayOverlayContext::openMenuOverlay()
{
    m_view.openMenuOverlay();
}

void GameplayOverlayContext::closeMenuOverlay()
{
    m_view.closeMenuOverlay();
}

void GameplayOverlayContext::openControlsOverlay()
{
    m_view.openControlsOverlay();
}

void GameplayOverlayContext::closeControlsOverlay()
{
    m_view.closeControlsOverlay();
}

void GameplayOverlayContext::openKeyboardOverlay()
{
    m_view.openKeyboardOverlay();
}

void GameplayOverlayContext::closeKeyboardOverlayToControls()
{
    m_view.closeKeyboardOverlayToControls();
}

void GameplayOverlayContext::closeKeyboardOverlayToMenu()
{
    m_view.closeKeyboardOverlayToMenu();
}

void GameplayOverlayContext::openVideoOptionsOverlay()
{
    m_view.openVideoOptionsOverlay();
}

void GameplayOverlayContext::closeVideoOptionsOverlay()
{
    m_view.closeVideoOptionsOverlay();
}

void GameplayOverlayContext::openSaveGameOverlay()
{
    m_view.openSaveGameOverlay();
}

void GameplayOverlayContext::closeSaveGameOverlay()
{
    m_view.closeSaveGameOverlay();
}

void GameplayOverlayContext::requestOpenNewGameScreen()
{
    m_view.requestOpenNewGameScreen();
}

void GameplayOverlayContext::requestOpenLoadGameScreen()
{
    m_view.requestOpenLoadGameScreen();
}

void GameplayOverlayContext::openJournalOverlay()
{
    m_view.openJournalOverlay();
}

void GameplayOverlayContext::closeJournalOverlay()
{
    m_view.closeJournalOverlay();
}

void GameplayOverlayContext::executeActiveDialogAction()
{
    m_view.executeActiveDialogAction();
}

void GameplayOverlayContext::refreshHouseBankInputDialog()
{
    m_view.refreshHouseBankInputDialog();
}

void GameplayOverlayContext::confirmHouseBankInput()
{
    m_view.confirmHouseBankInput();
}

void GameplayOverlayContext::closeInventoryNestedOverlay()
{
    m_view.closeInventoryNestedOverlay();
}

void GameplayOverlayContext::closeSpellbookOverlay(const std::string &statusText)
{
    m_view.closeSpellbookOverlay(statusText);
}

bool GameplayOverlayContext::tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen)
{
    return m_view.tryUseHeldItemOnPartyMember(memberIndex, keepCharacterScreenOpen);
}

void GameplayOverlayContext::updateReadableScrollOverlayForHeldItem(
    size_t memberIndex,
    const GameplayCharacterPointerTarget &pointerTarget,
    bool isLeftMousePressed)
{
    m_view.updateReadableScrollOverlayForHeldItem(memberIndex, pointerTarget, isLeftMousePressed);
}

void GameplayOverlayContext::closeReadableScrollOverlay()
{
    m_view.closeReadableScrollOverlay();
}

void GameplayOverlayContext::playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
{
    m_view.playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
}

bool GameplayOverlayContext::tryCastSpellFromMember(size_t casterMemberIndex, uint32_t spellId, const std::string &spellName)
{
    return m_view.tryCastSpellFromMember(casterMemberIndex, spellId, spellName);
}

bool GameplayOverlayContext::tryCastSpellRequest(
    const PartySpellCastRequest &request,
    const std::string &spellName)
{
    return m_view.tryCastSpellRequest(request, spellName);
}

void GameplayOverlayContext::resetInventoryNestedOverlayInteractionState()
{
    m_view.resetInventoryNestedOverlayInteractionState();
}

void GameplayOverlayContext::resetLootOverlayInteractionState()
{
    m_view.closeOverlayLatch() = false;
    m_view.chestClickLatch() = false;
    m_view.chestItemClickLatch() = false;
    m_view.chestPressedTarget() = {};
    m_view.closeInventoryNestedOverlay();
    m_view.lootChestItemLatch() = false;
    m_view.chestSelectUpLatch() = false;
    m_view.chestSelectDownLatch() = false;
    m_view.chestSelectionIndex() = 0;
    resetInventoryNestedOverlayInteractionState();
}

GameSettings &GameplayOverlayContext::mutableSettings() const
{
    return m_view.mutableSettings();
}

const std::array<uint8_t, SDL_SCANCODE_COUNT> &GameplayOverlayContext::previousKeyboardState() const
{
    return m_view.previousKeyboardState();
}

void GameplayOverlayContext::commitSettingsChange()
{
    m_view.commitSettingsChange();
}

bool GameplayOverlayContext::trySaveToSelectedGameSlot()
{
    return m_view.trySaveToSelectedGameSlot();
}

int GameplayOverlayContext::restFoodRequired() const
{
    return m_view.restFoodRequired();
}

const GameSettings &GameplayOverlayContext::settingsSnapshot() const
{
    return m_view.settingsSnapshot();
}

bool GameplayOverlayContext::isControlsRenderButtonPressed(GameplayControlsRenderButton button) const
{
    return m_view.isControlsRenderButtonPressed(button);
}

bool GameplayOverlayContext::isVideoOptionsRenderButtonPressed(GameplayVideoOptionsRenderButton button) const
{
    return m_view.isVideoOptionsRenderButtonPressed(button);
}

void GameplayOverlayContext::clearHudLayoutRuntimeHeightOverrides()
{
    m_view.clearHudLayoutRuntimeHeightOverrides();
}

void GameplayOverlayContext::setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height)
{
    m_view.setHudLayoutRuntimeHeightOverride(layoutId, height);
}

const HouseEntry *GameplayOverlayContext::findHouseEntry(uint32_t houseId) const
{
    return m_view.findHouseEntry(houseId);
}

const GameplayOverlayContext::HudLayoutElement *GameplayOverlayContext::findHudLayoutElement(
    const std::string &layoutId) const
{
    return m_view.findHudLayoutElement(layoutId);
}

int GameplayOverlayContext::defaultHudLayoutZIndexForScreen(const std::string &screen) const
{
    return m_view.defaultHudLayoutZIndexForScreen(screen);
}

GameplayHudScreenState GameplayOverlayContext::currentHudScreenState() const
{
    return m_view.currentGameplayHudScreenState();
}

std::vector<std::string> GameplayOverlayContext::sortedHudLayoutIdsForScreen(const std::string &screen) const
{
    return m_view.sortedHudLayoutIdsForScreen(screen);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveHudLayoutElement(
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight) const
{
    return m_view.resolveHudLayoutElement(layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveChestGridArea(
    int width,
    int height) const
{
    return m_view.resolveGameplayChestGridArea(width, height);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>
GameplayOverlayContext::resolveInventoryNestedOverlayGridArea(
    int width,
    int height) const
{
    return m_view.resolveGameplayInventoryNestedOverlayGridArea(width, height);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveHouseShopOverlayFrame(
    int width,
    int height) const
{
    return m_view.resolveGameplayHouseShopOverlayFrame(width, height);
}

bool GameplayOverlayContext::isPointerInsideResolvedElement(
    const ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY) const
{
    return m_view.isPointerInsideResolvedElement(resolved, pointerX, pointerY);
}

const std::string *GameplayOverlayContext::resolveInteractiveAssetName(
    const HudLayoutElement &layout,
    const ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY,
    bool isLeftMousePressed) const
{
    const std::optional<std::string> assetName =
        m_view.resolveInteractiveAssetName(layout, resolved, pointerX, pointerY, isLeftMousePressed);

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
    return m_view.ensureHudTextureLoaded(textureName);
}

std::optional<GameplayOverlayContext::HudTextureHandle> GameplayOverlayContext::ensureSolidHudTextureLoaded(
    const std::string &textureName,
    uint32_t abgrColor)
{
    return m_view.ensureSolidHudTextureLoaded(textureName, abgrColor);
}

std::optional<GameplayOverlayContext::HudTextureHandle> GameplayOverlayContext::ensureDynamicHudTexture(
    const std::string &textureName,
    int width,
    int height,
    const std::vector<uint8_t> &bgraPixels)
{
    return m_view.ensureDynamicHudTexture(textureName, width, height, bgraPixels);
}

const std::vector<uint8_t> *GameplayOverlayContext::hudTexturePixels(
    const std::string &textureName,
    int &width,
    int &height)
{
    return m_view.hudTexturePixels(textureName, width, height);
}

bool GameplayOverlayContext::ensureHudTextureDimensions(const std::string &textureName, int &width, int &height)
{
    return m_view.ensureHudTextureDimensions(textureName, width, height);
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
    return m_view.tryGetOpaqueHudTextureBounds(
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
    m_view.submitHudTexturedQuad(texture, x, y, quadWidth, quadHeight);
}

bgfx::TextureHandle GameplayOverlayContext::ensureHudTextureColor(const HudTextureHandle &texture, uint32_t colorAbgr) const
{
    return m_view.ensureHudTextureColor(texture, colorAbgr);
}

void GameplayOverlayContext::renderLayoutLabel(
    const HudLayoutElement &layout,
    const ResolvedHudLayoutElement &resolved,
    const std::string &label) const
{
    m_view.renderLayoutLabel(layout, resolved, label);
}

std::optional<GameplayOverlayContext::HudFontHandle> GameplayOverlayContext::findHudFont(const std::string &fontName) const
{
    return m_view.findHudFont(fontName);
}

float GameplayOverlayContext::measureHudTextWidth(const HudFontHandle &font, const std::string &text) const
{
    return m_view.measureHudTextWidth(font, text);
}

std::vector<std::string> GameplayOverlayContext::wrapHudTextToWidth(
    const HudFontHandle &font,
    const std::string &text,
    float maxWidth) const
{
    return m_view.wrapHudTextToWidth(font, text, maxWidth);
}

bgfx::TextureHandle GameplayOverlayContext::ensureHudFontMainTextureColor(
    const HudFontHandle &font,
    uint32_t colorAbgr) const
{
    return m_view.ensureHudFontMainTextureColor(font, colorAbgr);
}

void GameplayOverlayContext::renderHudFontLayer(
    const HudFontHandle &font,
    bgfx::TextureHandle textureHandle,
    const std::string &text,
    float textX,
    float textY,
    float fontScale) const
{
    m_view.renderHudFontLayer(font, textureHandle, text, textX, textY, fontScale);
}

bool GameplayOverlayContext::hasHudRenderResources() const
{
    return m_view.hasHudRenderResources();
}

void GameplayOverlayContext::prepareHudView(int width, int height) const
{
    m_view.prepareHudView(width, height);
}

void GameplayOverlayContext::submitHudQuadBatch(
    const std::vector<GameplayHudBatchQuad> &quads,
    int screenWidth,
    int screenHeight) const
{
    m_view.submitHudQuadBatch(quads, screenWidth, screenHeight);
}

std::string GameplayOverlayContext::resolvePortraitTextureName(const Character &character) const
{
    return m_view.resolvePortraitTextureName(character);
}

void GameplayOverlayContext::consumePendingPortraitEventFxRequests()
{
    m_view.consumePendingPortraitEventFxRequests();
}

void GameplayOverlayContext::renderPortraitFx(
    size_t memberIndex,
    float portraitX,
    float portraitY,
    float portraitWidth,
    float portraitHeight) const
{
    m_view.renderPortraitFx(memberIndex, portraitX, portraitY, portraitWidth, portraitHeight);
}

bool GameplayOverlayContext::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    return m_view.tryGetGameplayMinimapState(state);
}

void GameplayOverlayContext::collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const
{
    m_view.collectGameplayMinimapMarkers(markers);
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
    m_view.addRenderedInspectableHudItem(item);
}

const std::vector<GameplayRenderedInspectableHudItem> &GameplayOverlayContext::renderedInspectableHudItems() const
{
    return m_view.renderedInspectableHudItems();
}

bool GameplayOverlayContext::isOpaqueHudPixelAtPoint(
    const GameplayRenderedInspectableHudItem &item,
    float x,
    float y) const
{
    return m_view.isOpaqueHudPixelAtPoint(item, x, y);
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
    m_view.submitWorldTextureQuad(textureHandle, x, y, quadWidth, quadHeight, u0, v0, u1, v1);
}

bool GameplayOverlayContext::renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const
{
    return m_view.renderHouseVideoFrame(x, y, quadWidth, quadHeight);
}
} // namespace OpenYAMM::Game
