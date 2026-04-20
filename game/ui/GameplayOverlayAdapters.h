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

class IGameplayOverlaySceneAdapter
{
public:
    virtual ~IGameplayOverlaySceneAdapter() = default;

    virtual const std::string &currentMapFileName() const = 0;
    virtual float gameplayCameraYawRadians() const = 0;
    virtual const std::vector<uint8_t> *journalMapFullyRevealedCells() const = 0;
    virtual const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const = 0;

    virtual bool trySelectPartyMember(size_t memberIndex, bool requireGameplayReady) = 0;
    virtual void executeActiveDialogAction() = 0;
    virtual bool tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen) = 0;
    virtual void playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation) = 0;
    virtual bool tryCastSpellFromMember(
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName) = 0;
    virtual bool tryCastSpellRequest(
        const PartySpellCastRequest &request,
        const std::string &spellName) = 0;
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
