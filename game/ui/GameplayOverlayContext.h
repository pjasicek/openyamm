#pragma once

#include "game/tables/ChestTable.h"
#include "game/app/GameSession.h"
#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/ui/GameplayOverlayAdapters.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/tables/HouseTable.h"
#include "game/tables/NpcDialogTable.h"
#include "game/party/Party.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/UiLayoutManager.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameAudioSystem;
class ItemTable;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
struct HouseEntry;
struct ItemDefinition;

class GameplayOverlayContext
{
public:
    using HudLayoutElement = UiLayoutManager::LayoutElement;
    using ResolvedHudLayoutElement = GameplayResolvedHudLayoutElement;
    using HudTextureHandle = GameplayHudTextureHandle;
    using HudFontHandle = GameplayHudFontHandle;

    GameplayOverlayContext(
        GameSession &session,
        GameAudioSystem *pAudioSystem,
        GameSettings *pSettings,
        IGameplayOverlaySceneAdapter &sceneAdapter,
        IGameplayOverlayHudAdapter &hudAdapter);

    IGameplayWorldRuntime *worldRuntime() const;
    Party *party() const;
    const Party *partyReadOnly() const;
    float partyX() const;
    float partyY() const;
    float partyFootZ() const;
    GameAudioSystem *audioSystem() const;
    const ItemTable *itemTable() const;
    const StandardItemEnchantTable *standardItemEnchantTable() const;
    const SpecialItemEnchantTable *specialItemEnchantTable() const;
    const ClassSkillTable *classSkillTable() const;
    const CharacterDollTable *characterDollTable() const;
    const CharacterInspectTable *characterInspectTable() const;
    const RosterTable *rosterTable() const;
    const ReadableScrollTable *readableScrollTable() const;
    const ItemEquipPosTable *itemEquipPosTable() const;
    const SpellTable *spellTable() const;
    const HouseTable *houseTable() const;
    const ChestTable *chestTable() const;
    const NpcDialogTable *npcDialogTable() const;

    GameplayUiController::CharacterScreenState &characterScreen() const;
    GameplayUiController::HeldInventoryItemState &heldInventoryItem() const;
    GameplayUiController::ItemInspectOverlayState &itemInspectOverlay() const;
    GameplayUiController::CharacterInspectOverlayState &characterInspectOverlay() const;
    GameplayUiController::BuffInspectOverlayState &buffInspectOverlay() const;
    GameplayUiController::CharacterDetailOverlayState &characterDetailOverlay() const;
    GameplayUiController::ActorInspectOverlayState &actorInspectOverlay() const;
    GameplayUiController::SpellInspectOverlayState &spellInspectOverlay() const;
    GameplayUiController::ReadableScrollOverlayState &readableScrollOverlay() const;
    GameplayUiController::SpellbookState &spellbook() const;
    GameplayUiController::UtilitySpellOverlayState &utilitySpellOverlay() const;
    GameplayUiController::InventoryNestedOverlayState &inventoryNestedOverlay() const;
    GameplayUiController::HouseShopOverlayState &houseShopOverlay() const;
    GameplayUiController::HouseBankState &houseBankState() const;
    GameplayUiController::JournalScreenState &journalScreenState() const;
    GameplayUiController::RestScreenState &restScreenState() const;
    GameplayUiController::MenuScreenState &menuScreenState() const;
    GameplayUiController::ControlsScreenState &controlsScreenState() const;
    GameplayUiController::KeyboardScreenState &keyboardScreenState() const;
    GameplayUiController::VideoOptionsScreenState &videoOptionsScreenState() const;
    GameplayUiController::SaveGameScreenState &saveGameScreenState() const;
    GameplayUiController::LoadGameScreenState &loadGameScreenState() const;
    const GameplayUiController::CharacterScreenState &characterScreenReadOnly() const;
    const GameplayUiController::ItemInspectOverlayState &itemInspectOverlayReadOnly() const;
    const GameplayUiController::CharacterInspectOverlayState &characterInspectOverlayReadOnly() const;
    const GameplayUiController::BuffInspectOverlayState &buffInspectOverlayReadOnly() const;
    const GameplayUiController::CharacterDetailOverlayState &characterDetailOverlayReadOnly() const;
    const GameplayUiController::ActorInspectOverlayState &actorInspectOverlayReadOnly() const;
    const GameplayUiController::SpellInspectOverlayState &spellInspectOverlayReadOnly() const;
    const GameplayUiController::ReadableScrollOverlayState &readableScrollOverlayReadOnly() const;
    const GameplayUiController::SpellbookState &spellbookReadOnly() const;
    const GameplayUiController::UtilitySpellOverlayState &utilitySpellOverlayReadOnly() const;
    const GameplayUiController::JournalScreenState &journalScreenStateReadOnly() const;
    const JournalQuestTable *journalQuestTable() const;
    const JournalHistoryTable *journalHistoryTable() const;
    const JournalAutonoteTable *journalAutonoteTable() const;
    const std::string &currentMapFileName() const;
    float gameplayCameraYawRadians() const;
    const std::vector<uint8_t> *journalMapFullyRevealedCells() const;
    const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const;
    EventDialogContent &activeEventDialog() const;
    std::string &statusBarEventText() const;
    float &statusBarEventRemainingSeconds() const;
    const std::string &statusBarHoverText() const;

    bool &closeOverlayLatch() const;
    bool &restClickLatch() const;
    GameplayRestPointerTarget &restPressedTarget() const;
    bool &menuToggleLatch() const;
    bool &menuClickLatch() const;
    GameplayMenuPointerTarget &menuPressedTarget() const;
    bool &controlsToggleLatch() const;
    bool &controlsClickLatch() const;
    GameplayControlsPointerTarget &controlsPressedTarget() const;
    bool &controlsSliderDragActive() const;
    GameplayControlsPointerTargetType &controlsDraggedSlider() const;
    bool &keyboardToggleLatch() const;
    bool &keyboardClickLatch() const;
    GameplayKeyboardPointerTarget &keyboardPressedTarget() const;
    bool &videoOptionsToggleLatch() const;
    bool &videoOptionsClickLatch() const;
    GameplayVideoOptionsPointerTarget &videoOptionsPressedTarget() const;
    bool &saveGameToggleLatch() const;
    bool &saveGameClickLatch() const;
    GameplaySaveLoadPointerTarget &saveGamePressedTarget() const;
    bool &characterClickLatch() const;
    GameplayCharacterPointerTarget &characterPressedTarget() const;
    bool &characterMemberCycleLatch() const;
    std::optional<size_t> &pendingCharacterDismissMemberIndex() const;
    uint64_t &pendingCharacterDismissExpiresTicks() const;
    bool &spellbookClickLatch() const;
    GameplaySpellbookPointerTarget &spellbookPressedTarget() const;
    uint64_t &lastSpellbookSpellClickTicks() const;
    uint32_t &lastSpellbookClickedSpellId() const;
    std::array<bool, 39> &saveGameEditKeyLatches() const;
    bool &saveGameEditBackspaceLatch() const;
    uint64_t &lastSaveGameSlotClickTicks() const;
    std::optional<size_t> &lastSaveGameClickedSlotIndex() const;
    bool &journalToggleLatch() const;
    bool &journalClickLatch() const;
    GameplayJournalPointerTarget &journalPressedTarget() const;
    bool &journalMapKeyZoomLatch() const;
    bool &dialogueClickLatch() const;
    GameplayDialoguePointerTarget &dialoguePressedTarget() const;
    bool &houseShopClickLatch() const;
    size_t &houseShopPressedSlotIndex() const;
    bool &chestClickLatch() const;
    bool &chestItemClickLatch() const;
    GameplayChestPointerTarget &chestPressedTarget() const;
    bool &inventoryNestedOverlayItemClickLatch() const;
    std::array<bool, 10> &houseBankDigitLatches() const;
    bool &houseBankBackspaceLatch() const;
    bool &houseBankConfirmLatch() const;
    bool &lootChestItemLatch() const;
    bool &chestSelectUpLatch() const;
    bool &chestSelectDownLatch() const;
    bool &eventDialogSelectUpLatch() const;
    bool &eventDialogSelectDownLatch() const;
    bool &eventDialogAcceptLatch() const;
    std::array<bool, 5> &eventDialogPartySelectLatches() const;
    bool &activateInspectLatch() const;
    size_t &chestSelectionIndex() const;
    size_t &eventDialogSelectionIndex() const;

    bool trySelectPartyMember(size_t memberIndex, bool requireGameplayReady);
    size_t selectedCharacterScreenSourceIndex() const;
    const Character *selectedCharacterScreenCharacter() const;
    bool isAdventurersInnCharacterSourceActive() const;
    bool isAdventurersInnScreenActive() const;
    bool isReadOnlyAdventurersInnCharacterViewActive() const;
    bool activeMemberKnowsSpell(uint32_t spellId) const;
    bool activeMemberHasSpellbookSchool(GameplayUiController::SpellbookSchool school) const;
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void openSpellbookOverlay();
    void openChestTransferInventoryOverlay();
    void toggleCharacterInventoryScreen();
    void handleDialogueCloseRequest();
    void closeRestOverlay();
    void openMenuOverlay();
    void closeMenuOverlay();
    void openControlsOverlay();
    void closeControlsOverlay();
    void openKeyboardOverlay();
    void closeKeyboardOverlayToControls();
    void closeKeyboardOverlayToMenu();
    void openVideoOptionsOverlay();
    void closeVideoOptionsOverlay();
    void openSaveGameOverlay();
    void closeSaveGameOverlay();
    void requestOpenNewGameScreen();
    void requestOpenLoadGameScreen();
    void openJournalOverlay();
    void closeJournalOverlay();
    void executeActiveDialogAction();
    void refreshHouseBankInputDialog();
    void confirmHouseBankInput();
    void closeInventoryNestedOverlay();
    void closeSpellbookOverlay(const std::string &statusText = "");
    bool tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen);
    void updateReadableScrollOverlayForHeldItem(
        size_t memberIndex,
        const GameplayCharacterPointerTarget &pointerTarget,
        bool isLeftMousePressed);
    void closeReadableScrollOverlay();
    void playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation);
    bool tryCastSpellFromMember(
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName);
    bool tryCastSpellRequest(
        const PartySpellCastRequest &request,
        const std::string &spellName);
    void resetInventoryNestedOverlayInteractionState();
    void resetLootOverlayInteractionState();
    GameSettings &mutableSettings() const;
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState() const;
    void commitSettingsChange();
    bool trySaveToSelectedGameSlot();
    int restFoodRequired() const;
    const GameSettings &settingsSnapshot() const;
    bool isControlsRenderButtonPressed(GameplayControlsRenderButton button) const;
    bool isVideoOptionsRenderButtonPressed(GameplayVideoOptionsRenderButton button) const;
    void clearHudLayoutRuntimeHeightOverrides();
    void setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height);

    const HouseEntry *findHouseEntry(uint32_t houseId) const;
    const HudLayoutElement *findHudLayoutElement(const std::string &layoutId) const;
    int defaultHudLayoutZIndexForScreen(const std::string &screen) const;
    GameplayHudScreenState currentHudScreenState() const;
    std::vector<std::string> sortedHudLayoutIdsForScreen(const std::string &screen) const;

    std::optional<ResolvedHudLayoutElement> resolveHudLayoutElement(
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight) const;
    std::optional<ResolvedHudLayoutElement> resolveChestGridArea(int width, int height) const;
    std::optional<ResolvedHudLayoutElement> resolveInventoryNestedOverlayGridArea(int width, int height) const;
    std::optional<ResolvedHudLayoutElement> resolveHouseShopOverlayFrame(int width, int height) const;
    bool isPointerInsideResolvedElement(
        const ResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY) const;
    const std::string *resolveInteractiveAssetName(
        const HudLayoutElement &layout,
        const ResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY,
        bool isLeftMousePressed) const;

    std::optional<HudTextureHandle> ensureHudTextureLoaded(const std::string &textureName);
    std::optional<HudTextureHandle> ensureSolidHudTextureLoaded(const std::string &textureName, uint32_t abgrColor);
    std::optional<HudTextureHandle> ensureDynamicHudTexture(
        const std::string &textureName,
        int width,
        int height,
        const std::vector<uint8_t> &bgraPixels);
    const std::vector<uint8_t> *hudTexturePixels(
        const std::string &textureName,
        int &width,
        int &height);
    bool ensureHudTextureDimensions(const std::string &textureName, int &width, int &height);
    bool tryGetOpaqueHudTextureBounds(
        const std::string &textureName,
        int &width,
        int &height,
        int &opaqueMinX,
        int &opaqueMinY,
        int &opaqueMaxX,
        int &opaqueMaxY);
    void submitHudTexturedQuad(
        const HudTextureHandle &texture,
        float x,
        float y,
        float quadWidth,
        float quadHeight) const;
    bgfx::TextureHandle ensureHudTextureColor(const HudTextureHandle &texture, uint32_t colorAbgr) const;
    void renderLayoutLabel(
        const HudLayoutElement &layout,
        const ResolvedHudLayoutElement &resolved,
        const std::string &label) const;
    std::optional<HudFontHandle> findHudFont(const std::string &fontName) const;
    float measureHudTextWidth(const HudFontHandle &font, const std::string &text) const;
    std::vector<std::string> wrapHudTextToWidth(
        const HudFontHandle &font,
        const std::string &text,
        float maxWidth) const;
    bgfx::TextureHandle ensureHudFontMainTextureColor(const HudFontHandle &font, uint32_t colorAbgr) const;
    void renderHudFontLayer(
        const HudFontHandle &font,
        bgfx::TextureHandle textureHandle,
        const std::string &text,
        float textX,
        float textY,
        float fontScale) const;
    bool hasHudRenderResources() const;
    void prepareHudView(int width, int height) const;
    void submitHudQuadBatch(
        const std::vector<GameplayHudBatchQuad> &quads,
        int screenWidth,
        int screenHeight) const;
    std::string resolvePortraitTextureName(const Character &character) const;
    void consumePendingPortraitEventFxRequests();
    void renderPortraitFx(
        size_t memberIndex,
        float portraitX,
        float portraitY,
        float portraitWidth,
        float portraitHeight) const;
    bool tryGetGameplayMinimapState(GameplayMinimapState &state) const;
    void collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const;
    float measureHudTextWidth(const std::string &fontName, const std::string &text) const;
    int hudFontHeight(const std::string &fontName) const;
    std::vector<std::string> wrapHudTextToWidth(
        const std::string &fontName,
        const std::string &text,
        float maxWidth) const;
    void renderHudTextLine(
        const std::string &fontName,
        uint32_t colorAbgr,
        const std::string &text,
        float textX,
        float textY,
        float fontScale) const;

    void addRenderedInspectableHudItem(const GameplayRenderedInspectableHudItem &item) const;
    const std::vector<GameplayRenderedInspectableHudItem> &renderedInspectableHudItems() const;
    bool isOpaqueHudPixelAtPoint(const GameplayRenderedInspectableHudItem &item, float x, float y) const;
    std::string resolveEquippedItemHudTextureName(
        const ItemDefinition &itemDefinition,
        uint32_t dollTypeId,
        bool hasRightHandWeapon,
        EquipmentSlot slot);
    std::optional<GameplayResolvedHudLayoutElement> resolveCharacterEquipmentRenderRect(
        const UiLayoutManager::LayoutElement &layout,
        const ItemDefinition &itemDefinition,
        const GameplayHudTextureHandle &texture,
        const CharacterDollTypeEntry *pCharacterDollType,
        EquipmentSlot slot,
        int screenWidth,
        int screenHeight) const;
    void submitWorldTextureQuad(
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight,
        float u0,
        float v0,
        float u1,
        float v1) const;
    bool renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const;

private:
    GameplayUiController &uiController() const;
    GameplayOverlayInteractionState &interactionState() const;

    GameSession &m_session;
    GameAudioSystem *m_pAudioSystem = nullptr;
    GameSettings *m_pSettings = nullptr;
    IGameplayOverlaySceneAdapter &m_sceneAdapter;
    IGameplayOverlayHudAdapter &m_hudAdapter;
    mutable std::optional<std::string> m_resolvedInteractiveAssetName;
};
} // namespace OpenYAMM::Game
