#include "game/ui/GameplayOverlayContext.h"

#include "game/tables/ChestTable.h"
#include "game/audio/GameAudioSystem.h"
#include "game/tables/HouseTable.h"
#include "game/tables/IconFrameTable.h"
#include "game/items/ItemEnchantTables.h"
#include "game/tables/ItemTable.h"
#include "game/tables/NpcDialogTable.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/ui/HudUiService.h"

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t HudViewId = 2;

GameplayResolvedHudLayoutElement toGameplayResolvedHudLayoutElement(
    const OutdoorGameView::OverlayResolvedHudLayoutElement &resolved)
{
    GameplayResolvedHudLayoutElement result = {};
    result.x = resolved.x;
    result.y = resolved.y;
    result.width = resolved.width;
    result.height = resolved.height;
    result.scale = resolved.scale;
    return result;
}

OutdoorGameView::OverlayResolvedHudLayoutElement toOutdoorResolvedHudLayoutElement(
    const GameplayResolvedHudLayoutElement &resolved)
{
    OutdoorGameView::OverlayResolvedHudLayoutElement result = {};
    result.x = resolved.x;
    result.y = resolved.y;
    result.width = resolved.width;
    result.height = resolved.height;
    result.scale = resolved.scale;
    return result;
}

GameplayHudScreenState toGameplayHudScreenState(OutdoorGameView::OverlayHudScreenState state)
{
    switch (state)
    {
    case OutdoorGameView::OverlayHudScreenState::Gameplay:
        return GameplayHudScreenState::Gameplay;
    case OutdoorGameView::OverlayHudScreenState::Dialogue:
        return GameplayHudScreenState::Dialogue;
    case OutdoorGameView::OverlayHudScreenState::Character:
        return GameplayHudScreenState::Character;
    case OutdoorGameView::OverlayHudScreenState::Chest:
        return GameplayHudScreenState::Chest;
    case OutdoorGameView::OverlayHudScreenState::Spellbook:
        return GameplayHudScreenState::Spellbook;
    case OutdoorGameView::OverlayHudScreenState::Rest:
        return GameplayHudScreenState::Rest;
    case OutdoorGameView::OverlayHudScreenState::Journal:
        return GameplayHudScreenState::Journal;
    }

    return GameplayHudScreenState::Gameplay;
}

} // namespace

GameplayOverlayContext::GameplayOverlayContext(OutdoorGameView &view)
    : m_view(view)
{
}

OutdoorPartyRuntime *GameplayOverlayContext::partyRuntime() const
{
    return m_view.m_pOutdoorPartyRuntime;
}

OutdoorWorldRuntime *GameplayOverlayContext::worldRuntime() const
{
    return m_view.m_pOutdoorWorldRuntime;
}

GameAudioSystem *GameplayOverlayContext::audioSystem() const
{
    return m_view.m_pGameAudioSystem;
}

const ItemTable *GameplayOverlayContext::itemTable() const
{
    return m_view.m_pItemTable;
}

const StandardItemEnchantTable *GameplayOverlayContext::standardItemEnchantTable() const
{
    return m_view.m_pStandardItemEnchantTable;
}

const SpecialItemEnchantTable *GameplayOverlayContext::specialItemEnchantTable() const
{
    return m_view.m_pSpecialItemEnchantTable;
}

const std::optional<HouseTable> &GameplayOverlayContext::houseTable() const
{
    return m_view.m_houseTable;
}

const std::optional<ChestTable> &GameplayOverlayContext::chestTable() const
{
    return m_view.m_chestTable;
}

const std::optional<NpcDialogTable> &GameplayOverlayContext::npcDialogTable() const
{
    return m_view.m_npcDialogTable;
}

GameplayUiController::HeldInventoryItemState &GameplayOverlayContext::heldInventoryItem() const
{
    return m_view.m_heldInventoryItem;
}

GameplayUiController::InventoryNestedOverlayState &GameplayOverlayContext::inventoryNestedOverlay() const
{
    return m_view.m_inventoryNestedOverlay;
}

GameplayUiController::HouseShopOverlayState &GameplayOverlayContext::houseShopOverlay() const
{
    return m_view.m_houseShopOverlay;
}

GameplayUiController::HouseBankState &GameplayOverlayContext::houseBankState() const
{
    return m_view.m_houseBankState;
}

EventDialogContent &GameplayOverlayContext::activeEventDialog() const
{
    return m_view.m_activeEventDialog;
}

std::string &GameplayOverlayContext::statusBarEventText() const
{
    return m_view.m_statusBarEventText;
}

float &GameplayOverlayContext::statusBarEventRemainingSeconds() const
{
    return m_view.m_statusBarEventRemainingSeconds;
}

bool &GameplayOverlayContext::closeOverlayLatch() const
{
    return m_view.m_closeOverlayLatch;
}

bool &GameplayOverlayContext::dialogueClickLatch() const
{
    return m_view.m_dialogueClickLatch;
}

GameplayDialoguePointerTarget &GameplayOverlayContext::dialoguePressedTarget() const
{
    return m_view.m_dialoguePressedTarget;
}

bool &GameplayOverlayContext::houseShopClickLatch() const
{
    return m_view.m_houseShopClickLatch;
}

size_t &GameplayOverlayContext::houseShopPressedSlotIndex() const
{
    return m_view.m_houseShopPressedSlotIndex;
}

bool &GameplayOverlayContext::chestClickLatch() const
{
    return m_view.m_chestClickLatch;
}

bool &GameplayOverlayContext::chestItemClickLatch() const
{
    return m_view.m_chestItemClickLatch;
}

GameplayChestPointerTarget &GameplayOverlayContext::chestPressedTarget() const
{
    return m_view.m_chestPressedTarget;
}

bool &GameplayOverlayContext::inventoryNestedOverlayItemClickLatch() const
{
    return m_view.m_inventoryNestedOverlayItemClickLatch;
}

std::array<bool, 10> &GameplayOverlayContext::houseBankDigitLatches() const
{
    return m_view.m_houseBankDigitLatches;
}

bool &GameplayOverlayContext::houseBankBackspaceLatch() const
{
    return m_view.m_houseBankBackspaceLatch;
}

bool &GameplayOverlayContext::houseBankConfirmLatch() const
{
    return m_view.m_houseBankConfirmLatch;
}

bool &GameplayOverlayContext::lootChestItemLatch() const
{
    return m_view.m_lootChestItemLatch;
}

bool &GameplayOverlayContext::chestSelectUpLatch() const
{
    return m_view.m_chestSelectUpLatch;
}

bool &GameplayOverlayContext::chestSelectDownLatch() const
{
    return m_view.m_chestSelectDownLatch;
}

bool &GameplayOverlayContext::eventDialogSelectUpLatch() const
{
    return m_view.m_eventDialogSelectUpLatch;
}

bool &GameplayOverlayContext::eventDialogSelectDownLatch() const
{
    return m_view.m_eventDialogSelectDownLatch;
}

bool &GameplayOverlayContext::eventDialogAcceptLatch() const
{
    return m_view.m_eventDialogAcceptLatch;
}

std::array<bool, 5> &GameplayOverlayContext::eventDialogPartySelectLatches() const
{
    return m_view.m_eventDialogPartySelectLatches;
}

bool &GameplayOverlayContext::activateInspectLatch() const
{
    return m_view.m_activateInspectLatch;
}

size_t &GameplayOverlayContext::chestSelectionIndex() const
{
    return m_view.m_chestSelectionIndex;
}

size_t &GameplayOverlayContext::eventDialogSelectionIndex() const
{
    return m_view.m_eventDialogSelectionIndex;
}

bool GameplayOverlayContext::trySelectPartyMember(size_t memberIndex, bool requireGameplayReady)
{
    return m_view.trySelectPartyMember(memberIndex, requireGameplayReady);
}

void GameplayOverlayContext::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    m_view.setStatusBarEvent(text, durationSeconds);
}

void GameplayOverlayContext::handleDialogueCloseRequest()
{
    OutdoorInteractionController::handleDialogueCloseRequest(m_view);
}

void GameplayOverlayContext::executeActiveDialogAction()
{
    OutdoorInteractionController::executeActiveDialogAction(m_view);
}

void GameplayOverlayContext::refreshHouseBankInputDialog()
{
    OutdoorInteractionController::refreshHouseBankInputDialog(m_view);
}

void GameplayOverlayContext::confirmHouseBankInput()
{
    OutdoorInteractionController::confirmHouseBankInput(m_view);
}

void GameplayOverlayContext::closeInventoryNestedOverlay()
{
    m_view.closeInventoryNestedOverlay();
}

void GameplayOverlayContext::playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
{
    m_view.playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
}

void GameplayOverlayContext::resetInventoryNestedOverlayInteractionState()
{
    m_view.m_inventoryNestedOverlayClickLatch = false;
    m_view.m_inventoryNestedOverlayItemClickLatch = false;
    m_view.m_inventoryNestedOverlayPressedTarget = {};
}

void GameplayOverlayContext::resetLootOverlayInteractionState()
{
    m_view.m_closeOverlayLatch = false;
    m_view.m_chestClickLatch = false;
    m_view.m_chestItemClickLatch = false;
    m_view.m_chestPressedTarget = {};
    m_view.closeInventoryNestedOverlay();
    m_view.m_lootChestItemLatch = false;
    m_view.m_chestSelectUpLatch = false;
    m_view.m_chestSelectDownLatch = false;
    m_view.m_chestSelectionIndex = 0;
    resetInventoryNestedOverlayInteractionState();
}

const HouseEntry *GameplayOverlayContext::findHouseEntry(uint32_t houseId) const
{
    return m_view.m_houseTable ? m_view.m_houseTable->get(houseId) : nullptr;
}

const GameplayOverlayContext::HudLayoutElement *GameplayOverlayContext::findHudLayoutElement(
    const std::string &layoutId) const
{
    return HudUiService::findHudLayoutElement(m_view, layoutId);
}

int GameplayOverlayContext::defaultHudLayoutZIndexForScreen(const std::string &screen) const
{
    return HudUiService::defaultHudLayoutZIndexForScreen(screen);
}

GameplayHudScreenState GameplayOverlayContext::currentHudScreenState() const
{
    return toGameplayHudScreenState(m_view.currentHudScreenState());
}

std::vector<std::string> GameplayOverlayContext::sortedHudLayoutIdsForScreen(const std::string &screen) const
{
    return HudUiService::sortedHudLayoutIdsForScreen(m_view, screen);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveHudLayoutElement(
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight) const
{
    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
        HudUiService::resolveHudLayoutElement(m_view, layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight);

    if (!resolved)
    {
        return std::nullopt;
    }

    return toGameplayResolvedHudLayoutElement(*resolved);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveChestGridArea(
    int width,
    int height) const
{
    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = m_view.resolveChestGridArea(width, height);

    if (!resolved)
    {
        return std::nullopt;
    }

    return toGameplayResolvedHudLayoutElement(*resolved);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>
GameplayOverlayContext::resolveInventoryNestedOverlayGridArea(
    int width,
    int height) const
{
    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
        m_view.resolveInventoryNestedOverlayGridArea(width, height);

    if (!resolved)
    {
        return std::nullopt;
    }

    return toGameplayResolvedHudLayoutElement(*resolved);
}

std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> GameplayOverlayContext::resolveHouseShopOverlayFrame(
    int width,
    int height) const
{
    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
        m_view.resolveHouseShopOverlayFrame(width, height);

    if (!resolved)
    {
        return std::nullopt;
    }

    return toGameplayResolvedHudLayoutElement(*resolved);
}

bool GameplayOverlayContext::isPointerInsideResolvedElement(
    const ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY) const
{
    return HudUiService::isPointerInsideResolvedElement(toOutdoorResolvedHudLayoutElement(resolved), pointerX, pointerY);
}

const std::string *GameplayOverlayContext::resolveInteractiveAssetName(
    const HudLayoutElement &layout,
    const ResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY,
    bool isLeftMousePressed) const
{
    m_resolvedInteractiveAssetName.reset();
    const std::string *pAssetName = HudUiService::resolveInteractiveAssetName(
        layout,
        toOutdoorResolvedHudLayoutElement(resolved),
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
    const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(m_view, textureName);

    if (pTexture == nullptr)
    {
        return std::nullopt;
    }

    HudTextureHandle textureHandle = {};
    textureHandle.textureName = pTexture->textureName;
    textureHandle.width = pTexture->width;
    textureHandle.height = pTexture->height;
    textureHandle.textureHandle = pTexture->textureHandle;
    return textureHandle;
}

std::optional<GameplayOverlayContext::HudTextureHandle> GameplayOverlayContext::ensureSolidHudTextureLoaded(
    const std::string &textureName,
    uint32_t abgrColor)
{
    const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureSolidHudTextureLoaded(
        m_view,
        textureName,
        abgrColor);

    if (pTexture == nullptr)
    {
        return std::nullopt;
    }

    HudTextureHandle textureHandle = {};
    textureHandle.textureName = pTexture->textureName;
    textureHandle.width = pTexture->width;
    textureHandle.height = pTexture->height;
    textureHandle.textureHandle = pTexture->textureHandle;
    return textureHandle;
}

bool GameplayOverlayContext::ensureHudTextureDimensions(const std::string &textureName, int &width, int &height)
{
    const std::optional<HudTextureHandle> texture = ensureHudTextureLoaded(textureName);

    if (!texture)
    {
        return false;
    }

    width = texture->width;
    height = texture->height;
    return true;
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
    return HudUiService::tryGetOpaqueHudTextureBounds(
        m_view,
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
    OutdoorGameView::HudTextureHandle resolvedTexture = {};
    resolvedTexture.textureName = texture.textureName;
    resolvedTexture.width = texture.width;
    resolvedTexture.height = texture.height;
    resolvedTexture.textureHandle = texture.textureHandle;
    m_view.submitHudTexturedQuad(resolvedTexture, x, y, quadWidth, quadHeight);
}

bgfx::TextureHandle GameplayOverlayContext::ensureHudTextureColor(const HudTextureHandle &texture, uint32_t colorAbgr) const
{
    OutdoorGameView::HudTextureHandle resolvedTexture = {};
    resolvedTexture.textureName = texture.textureName;
    resolvedTexture.width = texture.width;
    resolvedTexture.height = texture.height;
    resolvedTexture.textureHandle = texture.textureHandle;
    return HudUiService::ensureHudTextureColor(m_view, resolvedTexture, colorAbgr);
}

void GameplayOverlayContext::renderLayoutLabel(
    const HudLayoutElement &layout,
    const ResolvedHudLayoutElement &resolved,
    const std::string &label) const
{
    HudUiService::renderLayoutLabel(m_view, layout, toOutdoorResolvedHudLayoutElement(resolved), label);
}

std::optional<GameplayOverlayContext::HudFontHandle> GameplayOverlayContext::findHudFont(const std::string &fontName) const
{
    const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(m_view, fontName);

    if (pFont == nullptr)
    {
        return std::nullopt;
    }

    HudFontHandle fontHandle = {};
    fontHandle.fontName = pFont->fontName;
    fontHandle.fontHeight = pFont->fontHeight;
    fontHandle.mainTextureHandle = pFont->mainTextureHandle;
    fontHandle.shadowTextureHandle = pFont->shadowTextureHandle;
    return fontHandle;
}

float GameplayOverlayContext::measureHudTextWidth(const HudFontHandle &font, const std::string &text) const
{
    const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(m_view, font.fontName);
    return pFont != nullptr ? HudUiService::measureHudTextWidth(m_view, *pFont, text) : 0.0f;
}

std::vector<std::string> GameplayOverlayContext::wrapHudTextToWidth(
    const HudFontHandle &font,
    const std::string &text,
    float maxWidth) const
{
    const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(m_view, font.fontName);
    return pFont != nullptr
        ? HudUiService::wrapHudTextToWidth(m_view, *pFont, text, maxWidth)
        : std::vector<std::string>{text};
}

bgfx::TextureHandle GameplayOverlayContext::ensureHudFontMainTextureColor(
    const HudFontHandle &font,
    uint32_t colorAbgr) const
{
    const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(m_view, font.fontName);

    if (pFont != nullptr)
    {
        return HudUiService::ensureHudFontMainTextureColor(m_view, *pFont, colorAbgr);
    }

    bgfx::TextureHandle invalidHandle = BGFX_INVALID_HANDLE;
    return invalidHandle;
}

void GameplayOverlayContext::renderHudFontLayer(
    const HudFontHandle &font,
    bgfx::TextureHandle textureHandle,
    const std::string &text,
    float textX,
    float textY,
    float fontScale) const
{
    const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(m_view, font.fontName);

    if (pFont == nullptr)
    {
        return;
    }

    HudUiService::renderHudFontLayer(m_view, *pFont, textureHandle, text, textX, textY, fontScale);
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
    m_view.m_renderedInspectableHudItems.push_back(item);
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
    bgfx::TransientVertexBuffer vertexBuffer;
    bgfx::TransientIndexBuffer indexBuffer;

    if (!bgfx::allocTransientBuffers(
            &vertexBuffer,
            OutdoorGameView::TexturedTerrainVertex::ms_layout,
            4,
            &indexBuffer,
            6))
    {
        return;
    }

    auto *pVertices = reinterpret_cast<OutdoorGameView::TexturedTerrainVertex *>(vertexBuffer.data);
    pVertices[0] = {x, y, 0.0f, u0, v0};
    pVertices[1] = {x + quadWidth, y, 0.0f, u1, v0};
    pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1};
    pVertices[3] = {x, y + quadHeight, 0.0f, u0, v1};

    auto *pIndices = reinterpret_cast<uint16_t *>(indexBuffer.data);
    pIndices[0] = 0;
    pIndices[1] = 1;
    pIndices[2] = 2;
    pIndices[3] = 0;
    pIndices[4] = 2;
    pIndices[5] = 3;

    bgfx::setVertexBuffer(0, &vertexBuffer);
    bgfx::setIndexBuffer(&indexBuffer);
    bgfx::setTexture(0, m_view.m_terrainTextureSamplerHandle, textureHandle);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(HudViewId, m_view.m_texturedTerrainProgramHandle);
}

bool GameplayOverlayContext::renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const
{
    if (!m_view.m_houseVideoPlayer.hasActiveFrame())
    {
        return false;
    }

    submitWorldTextureQuad(m_view.m_houseVideoPlayer.textureHandle(), x, y, quadWidth, quadHeight, 0.0f, 0.0f, 1.0f, 1.0f);
    return true;
}
} // namespace OpenYAMM::Game
