#pragma once

#include "game/tables/ChestTable.h"
#include "game/events/EventDialogContent.h"
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
class OutdoorGameView;
class OutdoorPartyRuntime;
class OutdoorWorldRuntime;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
struct HouseEntry;
struct ItemDefinition;

enum class GameplayHudScreenState
{
    Gameplay,
    Dialogue,
    Character,
    Chest,
    Spellbook
};

struct GameplayResolvedHudLayoutElement
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    float scale = 1.0f;
};

enum class GameplayDialoguePointerTargetType
{
    None,
    Action,
    CloseButton
};

struct GameplayDialoguePointerTarget
{
    GameplayDialoguePointerTargetType type = GameplayDialoguePointerTargetType::None;
    size_t index = 0;

    bool operator==(const GameplayDialoguePointerTarget &other) const = default;
};

enum class GameplayChestPointerTargetType
{
    None,
    CloseButton
};

struct GameplayChestPointerTarget
{
    GameplayChestPointerTargetType type = GameplayChestPointerTargetType::None;

    bool operator==(const GameplayChestPointerTarget &other) const = default;
};

struct GameplayRenderedInspectableHudItem
{
    uint32_t objectDescriptionId = 0;
    bool hasItemState = false;
    InventoryItem itemState = {};
    GameplayUiController::ItemInspectSourceType sourceType = GameplayUiController::ItemInspectSourceType::None;
    size_t sourceMemberIndex = 0;
    uint8_t sourceGridX = 0;
    uint8_t sourceGridY = 0;
    EquipmentSlot equipmentSlot = EquipmentSlot::MainHand;
    size_t sourceLootItemIndex = 0;
    std::string textureName;
    bool hasValueOverride = false;
    int valueOverride = 0;
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

class GameplayOverlayContext
{
public:
    using HudLayoutElement = UiLayoutManager::LayoutElement;
    using ResolvedHudLayoutElement = GameplayResolvedHudLayoutElement;

    struct HudTextureHandle
    {
        std::string textureName;
        int width = 0;
        int height = 0;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    };

    struct HudFontHandle
    {
        std::string fontName;
        int fontHeight = 0;
        bgfx::TextureHandle mainTextureHandle = BGFX_INVALID_HANDLE;
        bgfx::TextureHandle shadowTextureHandle = BGFX_INVALID_HANDLE;
    };

    explicit GameplayOverlayContext(OutdoorGameView &view);

    OutdoorPartyRuntime *partyRuntime() const;
    OutdoorWorldRuntime *worldRuntime() const;
    GameAudioSystem *audioSystem() const;
    const ItemTable *itemTable() const;
    const StandardItemEnchantTable *standardItemEnchantTable() const;
    const SpecialItemEnchantTable *specialItemEnchantTable() const;
    const std::optional<HouseTable> &houseTable() const;
    const std::optional<ChestTable> &chestTable() const;
    const std::optional<NpcDialogTable> &npcDialogTable() const;

    GameplayUiController::HeldInventoryItemState &heldInventoryItem() const;
    GameplayUiController::InventoryNestedOverlayState &inventoryNestedOverlay() const;
    GameplayUiController::HouseShopOverlayState &houseShopOverlay() const;
    GameplayUiController::HouseBankState &houseBankState() const;
    EventDialogContent &activeEventDialog() const;
    std::string &statusBarEventText() const;
    float &statusBarEventRemainingSeconds() const;

    bool &closeOverlayLatch() const;
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
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void handleDialogueCloseRequest();
    void executeActiveDialogAction();
    void refreshHouseBankInputDialog();
    void confirmHouseBankInput();
    void closeInventoryNestedOverlay();
    void playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation);
    void resetInventoryNestedOverlayInteractionState();
    void resetLootOverlayInteractionState();

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
    OutdoorGameView &m_view;
    mutable std::optional<std::string> m_resolvedInteractiveAssetName;
};
} // namespace OpenYAMM::Game
