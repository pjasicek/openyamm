#pragma once

#include "game/audio/GameAudioSystem.h"
#include "game/app/GameSettings.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemEquipPosTable.h"
#include "game/party/SpeechIds.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/CharacterInspectTable.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/JournalAutonoteTable.h"
#include "game/tables/JournalHistoryTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/UiLayoutManager.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class IGameplayWorldRuntime;
struct HouseEntry;

struct GameplayOverlaySharedServices
{
    IGameplayWorldRuntime *pWorldRuntime = nullptr;
    GameAudioSystem *pAudioSystem = nullptr;
    const ItemTable *pItemTable = nullptr;
    const StandardItemEnchantTable *pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr;
    const ClassSkillTable *pClassSkillTable = nullptr;
    const CharacterDollTable *pCharacterDollTable = nullptr;
    const CharacterInspectTable *pCharacterInspectTable = nullptr;
    const RosterTable *pRosterTable = nullptr;
    const ReadableScrollTable *pReadableScrollTable = nullptr;
    const ItemEquipPosTable *pItemEquipPosTable = nullptr;
    const SpellTable *pSpellTable = nullptr;
    const std::optional<HouseTable> *pHouseTable = nullptr;
    const std::optional<ChestTable> *pChestTable = nullptr;
    const std::optional<NpcDialogTable> *pNpcDialogTable = nullptr;
    const JournalQuestTable *pJournalQuestTable = nullptr;
    const JournalHistoryTable *pJournalHistoryTable = nullptr;
    const JournalAutonoteTable *pJournalAutonoteTable = nullptr;
    GameplayUiController *pUiController = nullptr;
    GameplayOverlayInteractionState *pInteractionState = nullptr;
    GameSettings *pSettings = nullptr;
    const std::array<uint8_t, SDL_SCANCODE_COUNT> *pPreviousKeyboardState = nullptr;
};

class GameplayOverlayStateAccess
{
public:
    virtual ~GameplayOverlayStateAccess() = default;

    virtual GameplayUiController &uiController() = 0;
    virtual const GameplayUiController &uiController() const = 0;
    virtual GameplayOverlayInteractionState &overlayInteractionState() = 0;
    virtual const GameplayOverlayInteractionState &overlayInteractionState() const = 0;

    GameplayUiController::CharacterScreenState &characterScreen()
    {
        return uiController().characterScreen();
    }

    GameplayUiController::HeldInventoryItemState &heldInventoryItem()
    {
        return uiController().heldInventoryItem();
    }

    GameplayUiController::ItemInspectOverlayState &itemInspectOverlay()
    {
        return uiController().itemInspectOverlay();
    }

    GameplayUiController::CharacterInspectOverlayState &characterInspectOverlay()
    {
        return uiController().characterInspectOverlay();
    }

    GameplayUiController::BuffInspectOverlayState &buffInspectOverlay()
    {
        return uiController().buffInspectOverlay();
    }

    GameplayUiController::CharacterDetailOverlayState &characterDetailOverlay()
    {
        return uiController().characterDetailOverlay();
    }

    GameplayUiController::ActorInspectOverlayState &actorInspectOverlay()
    {
        return uiController().actorInspectOverlay();
    }

    GameplayUiController::SpellInspectOverlayState &spellInspectOverlay()
    {
        return uiController().spellInspectOverlay();
    }

    GameplayUiController::ReadableScrollOverlayState &readableScrollOverlay()
    {
        return uiController().readableScrollOverlay();
    }

    GameplayUiController::SpellbookState &spellbook()
    {
        return uiController().spellbook();
    }

    GameplayUiController::UtilitySpellOverlayState &utilitySpellOverlay()
    {
        return uiController().utilitySpellOverlay();
    }

    GameplayUiController::InventoryNestedOverlayState &inventoryNestedOverlay()
    {
        return uiController().inventoryNestedOverlay();
    }

    GameplayUiController::HouseShopOverlayState &houseShopOverlay()
    {
        return uiController().houseShopOverlay();
    }

    GameplayUiController::HouseBankState &houseBankState()
    {
        return uiController().houseBankState();
    }

    GameplayUiController::JournalScreenState &journalScreenState()
    {
        return uiController().journalScreen();
    }

    GameplayUiController::RestScreenState &restScreenState()
    {
        return uiController().restScreen();
    }

    GameplayUiController::MenuScreenState &menuScreenState()
    {
        return uiController().menuScreen();
    }

    GameplayUiController::ControlsScreenState &controlsScreenState()
    {
        return uiController().controlsScreen();
    }

    GameplayUiController::KeyboardScreenState &keyboardScreenState()
    {
        return uiController().keyboardScreen();
    }

    GameplayUiController::VideoOptionsScreenState &videoOptionsScreenState()
    {
        return uiController().videoOptionsScreen();
    }

    GameplayUiController::SaveGameScreenState &saveGameScreenState()
    {
        return uiController().saveGameScreen();
    }

    GameplayUiController::LoadGameScreenState &loadGameScreenState()
    {
        return uiController().loadGameScreen();
    }

    const GameplayUiController::CharacterScreenState &characterScreen() const
    {
        return uiController().characterScreen();
    }

    const GameplayUiController::ItemInspectOverlayState &itemInspectOverlay() const
    {
        return uiController().itemInspectOverlay();
    }

    const GameplayUiController::CharacterInspectOverlayState &characterInspectOverlay() const
    {
        return uiController().characterInspectOverlay();
    }

    const GameplayUiController::BuffInspectOverlayState &buffInspectOverlay() const
    {
        return uiController().buffInspectOverlay();
    }

    const GameplayUiController::CharacterDetailOverlayState &characterDetailOverlay() const
    {
        return uiController().characterDetailOverlay();
    }

    const GameplayUiController::ActorInspectOverlayState &actorInspectOverlay() const
    {
        return uiController().actorInspectOverlay();
    }

    const GameplayUiController::SpellInspectOverlayState &spellInspectOverlay() const
    {
        return uiController().spellInspectOverlay();
    }

    const GameplayUiController::ReadableScrollOverlayState &readableScrollOverlay() const
    {
        return uiController().readableScrollOverlay();
    }

    const GameplayUiController::SpellbookState &spellbook() const
    {
        return uiController().spellbook();
    }

    const GameplayUiController::UtilitySpellOverlayState &utilitySpellOverlay() const
    {
        return uiController().utilitySpellOverlay();
    }

    const GameplayUiController::JournalScreenState &journalScreenState() const
    {
        return uiController().journalScreen();
    }

    const GameplayUiController::RestScreenState &restScreenState() const
    {
        return uiController().restScreen();
    }

    const GameplayUiController::MenuScreenState &menuScreenState() const
    {
        return uiController().menuScreen();
    }

    const GameplayUiController::ControlsScreenState &controlsScreenState() const
    {
        return uiController().controlsScreen();
    }

    const GameplayUiController::KeyboardScreenState &keyboardScreenState() const
    {
        return uiController().keyboardScreen();
    }

    const GameplayUiController::VideoOptionsScreenState &videoOptionsScreenState() const
    {
        return uiController().videoOptionsScreen();
    }

    const GameplayUiController::SaveGameScreenState &saveGameScreenState() const
    {
        return uiController().saveGameScreen();
    }

    const GameplayUiController::LoadGameScreenState &loadGameScreenState() const
    {
        return uiController().loadGameScreen();
    }

    EventDialogContent &activeEventDialog()
    {
        return uiController().eventDialog().content;
    }

    std::string &statusBarEventText()
    {
        return uiController().statusBar().eventText;
    }

    float &statusBarEventRemainingSeconds()
    {
        return uiController().statusBar().eventRemainingSeconds;
    }

    const std::string &statusBarHoverText() const
    {
        return uiController().statusBar().hoverText;
    }

    bool &closeOverlayLatch()
    {
        return overlayInteractionState().closeOverlayLatch;
    }

    bool &restClickLatch()
    {
        return overlayInteractionState().restClickLatch;
    }

    GameplayRestPointerTarget &restPressedTarget()
    {
        return overlayInteractionState().restPressedTarget;
    }

    bool &menuToggleLatch()
    {
        return overlayInteractionState().menuToggleLatch;
    }

    bool &menuClickLatch()
    {
        return overlayInteractionState().menuClickLatch;
    }

    GameplayMenuPointerTarget &menuPressedTarget()
    {
        return overlayInteractionState().menuPressedTarget;
    }

    bool &controlsToggleLatch()
    {
        return overlayInteractionState().controlsToggleLatch;
    }

    bool &controlsClickLatch()
    {
        return overlayInteractionState().controlsClickLatch;
    }

    GameplayControlsPointerTarget &controlsPressedTarget()
    {
        return overlayInteractionState().controlsPressedTarget;
    }

    bool &controlsSliderDragActive()
    {
        return overlayInteractionState().controlsSliderDragActive;
    }

    GameplayControlsPointerTargetType &controlsDraggedSlider()
    {
        return overlayInteractionState().controlsDraggedSlider;
    }

    bool &keyboardToggleLatch()
    {
        return overlayInteractionState().keyboardToggleLatch;
    }

    bool &keyboardClickLatch()
    {
        return overlayInteractionState().keyboardClickLatch;
    }

    GameplayKeyboardPointerTarget &keyboardPressedTarget()
    {
        return overlayInteractionState().keyboardPressedTarget;
    }

    bool &videoOptionsToggleLatch()
    {
        return overlayInteractionState().videoOptionsToggleLatch;
    }

    bool &videoOptionsClickLatch()
    {
        return overlayInteractionState().videoOptionsClickLatch;
    }

    GameplayVideoOptionsPointerTarget &videoOptionsPressedTarget()
    {
        return overlayInteractionState().videoOptionsPressedTarget;
    }

    bool &saveGameToggleLatch()
    {
        return overlayInteractionState().saveGameToggleLatch;
    }

    bool &saveGameClickLatch()
    {
        return overlayInteractionState().saveGameClickLatch;
    }

    GameplaySaveLoadPointerTarget &saveGamePressedTarget()
    {
        return overlayInteractionState().saveGamePressedTarget;
    }

    bool &characterClickLatch()
    {
        return overlayInteractionState().characterClickLatch;
    }

    GameplayCharacterPointerTarget &characterPressedTarget()
    {
        return overlayInteractionState().characterPressedTarget;
    }

    bool &characterMemberCycleLatch()
    {
        return overlayInteractionState().characterMemberCycleLatch;
    }

    std::optional<size_t> &pendingCharacterDismissMemberIndex()
    {
        return overlayInteractionState().pendingCharacterDismissMemberIndex;
    }

    uint64_t &pendingCharacterDismissExpiresTicks()
    {
        return overlayInteractionState().pendingCharacterDismissExpiresTicks;
    }

    bool &spellbookClickLatch()
    {
        return overlayInteractionState().spellbookClickLatch;
    }

    GameplaySpellbookPointerTarget &spellbookPressedTarget()
    {
        return overlayInteractionState().spellbookPressedTarget;
    }

    uint64_t &lastSpellbookSpellClickTicks()
    {
        return overlayInteractionState().lastSpellbookSpellClickTicks;
    }

    uint32_t &lastSpellbookClickedSpellId()
    {
        return overlayInteractionState().lastSpellbookClickedSpellId;
    }

    std::array<bool, 39> &saveGameEditKeyLatches()
    {
        return overlayInteractionState().saveGameEditKeyLatches;
    }

    bool &saveGameEditBackspaceLatch()
    {
        return overlayInteractionState().saveGameEditBackspaceLatch;
    }

    uint64_t &lastSaveGameSlotClickTicks()
    {
        return overlayInteractionState().lastSaveGameSlotClickTicks;
    }

    std::optional<size_t> &lastSaveGameClickedSlotIndex()
    {
        return overlayInteractionState().lastSaveGameClickedSlotIndex;
    }

    bool &journalToggleLatch()
    {
        return overlayInteractionState().journalToggleLatch;
    }

    bool &journalClickLatch()
    {
        return overlayInteractionState().journalClickLatch;
    }

    GameplayJournalPointerTarget &journalPressedTarget()
    {
        return overlayInteractionState().journalPressedTarget;
    }

    bool &journalMapKeyZoomLatch()
    {
        return overlayInteractionState().journalMapKeyZoomLatch;
    }

    bool &dialogueClickLatch()
    {
        return overlayInteractionState().dialogueClickLatch;
    }

    GameplayDialoguePointerTarget &dialoguePressedTarget()
    {
        return overlayInteractionState().dialoguePressedTarget;
    }

    bool &houseShopClickLatch()
    {
        return overlayInteractionState().houseShopClickLatch;
    }

    size_t &houseShopPressedSlotIndex()
    {
        return overlayInteractionState().houseShopPressedSlotIndex;
    }

    bool &chestClickLatch()
    {
        return overlayInteractionState().chestClickLatch;
    }

    bool &chestItemClickLatch()
    {
        return overlayInteractionState().chestItemClickLatch;
    }

    GameplayChestPointerTarget &chestPressedTarget()
    {
        return overlayInteractionState().chestPressedTarget;
    }

    bool &inventoryNestedOverlayItemClickLatch()
    {
        return overlayInteractionState().inventoryNestedOverlayItemClickLatch;
    }

    std::array<bool, 10> &houseBankDigitLatches()
    {
        return overlayInteractionState().houseBankDigitLatches;
    }

    bool &houseBankBackspaceLatch()
    {
        return overlayInteractionState().houseBankBackspaceLatch;
    }

    bool &houseBankConfirmLatch()
    {
        return overlayInteractionState().houseBankConfirmLatch;
    }

    bool &lootChestItemLatch()
    {
        return overlayInteractionState().lootChestItemLatch;
    }

    bool &chestSelectUpLatch()
    {
        return overlayInteractionState().chestSelectUpLatch;
    }

    bool &chestSelectDownLatch()
    {
        return overlayInteractionState().chestSelectDownLatch;
    }

    bool &eventDialogSelectUpLatch()
    {
        return overlayInteractionState().eventDialogSelectUpLatch;
    }

    bool &eventDialogSelectDownLatch()
    {
        return overlayInteractionState().eventDialogSelectDownLatch;
    }

    bool &eventDialogAcceptLatch()
    {
        return overlayInteractionState().eventDialogAcceptLatch;
    }

    std::array<bool, 5> &eventDialogPartySelectLatches()
    {
        return overlayInteractionState().eventDialogPartySelectLatches;
    }

    bool &activateInspectLatch()
    {
        return overlayInteractionState().activateInspectLatch;
    }

    size_t &chestSelectionIndex()
    {
        return overlayInteractionState().chestSelectionIndex;
    }

    size_t &eventDialogSelectionIndex()
    {
        return uiController().eventDialog().selectionIndex;
    }
};

class IGameplayOverlaySceneAdapter
{
public:
    virtual ~IGameplayOverlaySceneAdapter() = default;

    virtual const std::string &currentMapFileName() const = 0;
    virtual float gameplayCameraYawRadians() const = 0;
    virtual const std::vector<uint8_t> *journalMapFullyRevealedCells() const = 0;
    virtual const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const = 0;

    virtual bool trySelectPartyMember(size_t memberIndex, bool requireGameplayReady) = 0;
    virtual void handleDialogueCloseRequest() = 0;
    virtual void closeRestOverlay() = 0;
    virtual void openMenuOverlay() = 0;
    virtual void closeMenuOverlay() = 0;
    virtual void openControlsOverlay() = 0;
    virtual void closeControlsOverlay() = 0;
    virtual void openKeyboardOverlay() = 0;
    virtual void closeKeyboardOverlayToControls() = 0;
    virtual void closeKeyboardOverlayToMenu() = 0;
    virtual void openVideoOptionsOverlay() = 0;
    virtual void closeVideoOptionsOverlay() = 0;
    virtual void openSaveGameOverlay() = 0;
    virtual void closeSaveGameOverlay() = 0;
    virtual void requestOpenNewGameScreen() = 0;
    virtual void requestOpenLoadGameScreen() = 0;
    virtual void openJournalOverlay() = 0;
    virtual void closeJournalOverlay() = 0;
    virtual void executeActiveDialogAction() = 0;
    virtual void refreshHouseBankInputDialog() = 0;
    virtual void confirmHouseBankInput() = 0;
    virtual void closeInventoryNestedOverlay() = 0;
    virtual void closeSpellbookOverlay(const std::string &statusText) = 0;
    virtual bool tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen) = 0;
    virtual void resetInventoryNestedOverlayInteractionState() = 0;
    virtual void playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation) = 0;
    virtual bool tryCastSpellFromMember(
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName) = 0;
    virtual bool tryCastSpellRequest(
        const PartySpellCastRequest &request,
        const std::string &spellName) = 0;
    virtual void commitSettingsChange() = 0;
    virtual bool trySaveToSelectedGameSlot() = 0;
    virtual int restFoodRequired() const = 0;
};

class IGameplayOverlayHudAdapter
{
public:
    virtual ~IGameplayOverlayHudAdapter() = default;

    virtual void clearHudLayoutRuntimeHeightOverrides() = 0;
    virtual void setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height) = 0;
    virtual const UiLayoutManager::LayoutElement *findHudLayoutElement(const std::string &layoutId) const = 0;
    virtual int defaultHudLayoutZIndexForScreen(const std::string &screen) const = 0;
    virtual GameplayHudScreenState currentGameplayHudScreenState() const = 0;
    virtual std::vector<std::string> sortedHudLayoutIdsForScreen(const std::string &screen) const = 0;
    virtual std::optional<GameplayResolvedHudLayoutElement> resolveHudLayoutElement(
        const std::string &layoutId,
        int screenWidth,
        int screenHeight,
        float fallbackWidth,
        float fallbackHeight) const = 0;
    virtual std::optional<GameplayResolvedHudLayoutElement> resolveGameplayChestGridArea(int width, int height) const = 0;
    virtual std::optional<GameplayResolvedHudLayoutElement> resolveGameplayInventoryNestedOverlayGridArea(
        int width,
        int height) const = 0;
    virtual std::optional<GameplayResolvedHudLayoutElement> resolveGameplayHouseShopOverlayFrame(
        int width,
        int height) const = 0;
    virtual bool isPointerInsideResolvedElement(
        const GameplayResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY) const = 0;
    virtual std::optional<std::string> resolveInteractiveAssetName(
        const UiLayoutManager::LayoutElement &layout,
        const GameplayResolvedHudLayoutElement &resolved,
        float pointerX,
        float pointerY,
        bool isLeftMousePressed) const = 0;

    virtual std::optional<GameplayHudTextureHandle> ensureHudTextureLoaded(const std::string &textureName) = 0;
    virtual std::optional<GameplayHudTextureHandle> ensureSolidHudTextureLoaded(
        const std::string &textureName,
        uint32_t abgrColor) = 0;
    virtual std::optional<GameplayHudTextureHandle> ensureDynamicHudTexture(
        const std::string &textureName,
        int width,
        int height,
        const std::vector<uint8_t> &bgraPixels) = 0;
    virtual const std::vector<uint8_t> *hudTexturePixels(
        const std::string &textureName,
        int &width,
        int &height) = 0;
    virtual bool ensureHudTextureDimensions(const std::string &textureName, int &width, int &height) = 0;
    virtual bool tryGetOpaqueHudTextureBounds(
        const std::string &textureName,
        int &width,
        int &height,
        int &opaqueMinX,
        int &opaqueMinY,
        int &opaqueMaxX,
        int &opaqueMaxY) = 0;
    virtual void submitHudTexturedQuad(
        const GameplayHudTextureHandle &texture,
        float x,
        float y,
        float quadWidth,
        float quadHeight) const = 0;
    virtual bgfx::TextureHandle ensureHudTextureColor(
        const GameplayHudTextureHandle &texture,
        uint32_t colorAbgr) const = 0;
    virtual void renderLayoutLabel(
        const UiLayoutManager::LayoutElement &layout,
        const GameplayResolvedHudLayoutElement &resolved,
        const std::string &label) const = 0;
    virtual std::optional<GameplayHudFontHandle> findHudFont(const std::string &fontName) const = 0;
    virtual float measureHudTextWidth(const GameplayHudFontHandle &font, const std::string &text) const = 0;
    virtual std::vector<std::string> wrapHudTextToWidth(
        const GameplayHudFontHandle &font,
        const std::string &text,
        float maxWidth) const = 0;
    virtual bgfx::TextureHandle ensureHudFontMainTextureColor(
        const GameplayHudFontHandle &font,
        uint32_t colorAbgr) const = 0;
    virtual void renderHudFontLayer(
        const GameplayHudFontHandle &font,
        bgfx::TextureHandle textureHandle,
        const std::string &text,
        float textX,
        float textY,
        float fontScale) const = 0;
    virtual bool hasHudRenderResources() const = 0;
    virtual void prepareHudView(int width, int height) const = 0;
    virtual void submitHudQuadBatch(
        const std::vector<GameplayHudBatchQuad> &quads,
        int screenWidth,
        int screenHeight) const = 0;
    virtual std::string resolvePortraitTextureName(const Character &character) const = 0;
    virtual void consumePendingPortraitEventFxRequests() = 0;
    virtual void renderPortraitFx(
        size_t memberIndex,
        float portraitX,
        float portraitY,
        float portraitWidth,
        float portraitHeight) const = 0;
    virtual bool tryGetGameplayMinimapState(GameplayMinimapState &state) const = 0;
    virtual void collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const = 0;
    virtual void addRenderedInspectableHudItem(const GameplayRenderedInspectableHudItem &item) = 0;
    virtual const std::vector<GameplayRenderedInspectableHudItem> &renderedInspectableHudItems() const = 0;
    virtual bool isOpaqueHudPixelAtPoint(const GameplayRenderedInspectableHudItem &item, float x, float y) const = 0;
    virtual void submitWorldTextureQuad(
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight,
        float u0,
        float v0,
        float u1,
        float v1) const = 0;
    virtual bool renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const = 0;
};
}
