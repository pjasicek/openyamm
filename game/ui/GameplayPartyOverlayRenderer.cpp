#include "game/ui/GameplayPartyOverlayRenderer.h"

#include "game/ItemRuntime.h"
#include "game/OutdoorGameView.h"
#include "game/SpellbookUiLayout.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <cmath>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t HudViewId = 2;
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr uint32_t BrokenItemTintColorAbgr = 0x800000ffu;
constexpr uint32_t UnidentifiedItemTintColorAbgr = 0x80ff0000u;

struct UiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

enum class ItemTintContext
{
    Held,
};

UiViewportRect computeUiViewportRect(int screenWidth, int screenHeight)
{
    UiViewportRect viewport = {};
    viewport.x = 0.0f;
    viewport.y = 0.0f;
    viewport.width = static_cast<float>(screenWidth);
    viewport.height = static_cast<float>(screenHeight);

    if (screenHeight > 0)
    {
        const float maxWidthForHeight = viewport.height * MaxUiViewportAspect;

        if (viewport.width > maxWidthForHeight)
        {
            viewport.width = maxWidthForHeight;
            viewport.x = (static_cast<float>(screenWidth) - viewport.width) * 0.5f;
        }
    }

    return viewport;
}

float snappedHudFontScale(float scale)
{
    const float roundedScale = std::round(scale);

    if (std::abs(scale - roundedScale) <= HudFontIntegerSnapThreshold)
    {
        return std::max(1.0f, roundedScale);
    }

    return std::max(1.0f, scale);
}

uint32_t itemTintColorAbgr(
    const InventoryItem *pItemState,
    const ItemDefinition *pItemDefinition,
    ItemTintContext context)
{
    if (pItemState == nullptr || pItemDefinition == nullptr)
    {
        return 0xffffffffu;
    }

    const bool isBroken = pItemState->broken;
    const bool isUnidentified = !pItemState->identified && ItemRuntime::requiresIdentification(*pItemDefinition);

    switch (context)
    {
        case ItemTintContext::Held:
            if (isBroken)
            {
                return BrokenItemTintColorAbgr;
            }

            if (isUnidentified)
            {
                return UnidentifiedItemTintColorAbgr;
            }

            break;
    }

    return 0xffffffffu;
}

void setupHudProjection(int width, int height)
{
    float projectionMatrix[16] = {};
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(width),
        static_cast<float>(height),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth);
    bgfx::setViewRect(HudViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewTransform(HudViewId, nullptr, projectionMatrix);
    bgfx::touch(HudViewId);
}

} // namespace

void GameplayPartyOverlayRenderer::renderSpellbookOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_spellbook.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = view.findHudLayoutElement("SpellbookRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedRoot = view.resolveHudLayoutElement(
        "SpellbookRoot",
        width,
        height,
        pRootLayout->width,
        pRootLayout->height);

    if (!resolvedRoot)
    {
        return;
    }

    const auto loadHudTexture =
        [&view](const std::string &textureName) -> const OutdoorGameView::HudTextureHandle *
        {
            return const_cast<OutdoorGameView &>(view).ensureHudTextureLoaded(textureName);
        };

    setupHudProjection(width, height);

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;

    const auto submitTexturedQuad =
        [&view](const OutdoorGameView::HudTextureHandle &texture, float x, float y, float quadWidth, float quadHeight)
        {
            view.submitHudTexturedQuad(texture, x, y, quadWidth, quadHeight);
        };

    const auto renderLayoutPrimaryAsset =
        [&view, width, height, &loadHudTexture, &submitTexturedQuad](const std::string &layoutId)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

            if (pLayout == nullptr || pLayout->primaryAsset.empty())
            {
                return;
            }

            const OutdoorGameView::HudTextureHandle *pTexture = loadHudTexture(pLayout->primaryAsset);

            if (pTexture == nullptr)
            {
                return;
            }

            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
                layoutId,
                width,
                height,
                pLayout->width > 0.0f ? pLayout->width : static_cast<float>(pTexture->width),
                pLayout->height > 0.0f ? pLayout->height : static_cast<float>(pTexture->height));

            if (!resolved)
            {
                return;
            }

            submitTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
        };

    const SpellbookSchoolUiDefinition *pSchoolDefinition = findSpellbookSchoolUiDefinition(view.m_spellbook.school);

    if (pSchoolDefinition == nullptr || !view.activeMemberHasSpellbookSchool(view.m_spellbook.school))
    {
        return;
    }

    renderLayoutPrimaryAsset(pSchoolDefinition->pPageLayoutId);

    for (const SpellbookSchoolUiDefinition &definition : spellbookSchoolUiDefinitions())
    {
        if (!view.activeMemberHasSpellbookSchool(definition.school))
        {
            continue;
        }

        const OutdoorGameView::HudLayoutElement *pLayout = view.findHudLayoutElement(definition.pButtonLayoutId);

        if (pLayout == nullptr || pLayout->primaryAsset.empty())
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pDefaultTexture = loadHudTexture(pLayout->primaryAsset);

        if (pDefaultTexture == nullptr)
        {
            continue;
        }

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
            definition.pButtonLayoutId,
            width,
            height,
            pLayout->width > 0.0f ? pLayout->width : static_cast<float>(pDefaultTexture->width),
            pLayout->height > 0.0f ? pLayout->height : static_cast<float>(pDefaultTexture->height));

        if (!resolved)
        {
            continue;
        }

        const bool isActive = definition.school == view.m_spellbook.school;
        const std::string *pInteractiveAssetName =
            view.resolveInteractiveAssetName(*pLayout, *resolved, mouseX, mouseY, isLeftMousePressed);
        const std::string *pSelectedAssetName =
            !pLayout->pressedAsset.empty()
                ? &pLayout->pressedAsset
                : (!pLayout->hoverAsset.empty() ? &pLayout->hoverAsset : &pLayout->primaryAsset);
        const std::string *pAssetName = isActive ? pSelectedAssetName : pInteractiveAssetName;
        const OutdoorGameView::HudTextureHandle *pTexture =
            pAssetName != nullptr ? loadHudTexture(*pAssetName) : pDefaultTexture;

        if (pTexture != nullptr)
        {
            submitTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
        }
    }

    const auto renderInteractiveButton =
        [&view, width, height, mouseX, mouseY, isLeftMousePressed, &loadHudTexture, &submitTexturedQuad](
            const std::string &layoutId)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

            if (pLayout == nullptr || pLayout->primaryAsset.empty())
            {
                return;
            }

            const OutdoorGameView::HudTextureHandle *pDefaultTexture = loadHudTexture(pLayout->primaryAsset);

            if (pDefaultTexture == nullptr)
            {
                return;
            }

            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
                layoutId,
                width,
                height,
                pLayout->width > 0.0f ? pLayout->width : static_cast<float>(pDefaultTexture->width),
                pLayout->height > 0.0f ? pLayout->height : static_cast<float>(pDefaultTexture->height));

            if (!resolved)
            {
                return;
            }

            const std::string *pAssetName =
                view.resolveInteractiveAssetName(*pLayout, *resolved, mouseX, mouseY, isLeftMousePressed);
            const OutdoorGameView::HudTextureHandle *pTexture =
                pAssetName != nullptr ? loadHudTexture(*pAssetName) : pDefaultTexture;

            if (pTexture != nullptr)
            {
                submitTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
            }
        };

    renderInteractiveButton("SpellbookCloseButton");
    renderInteractiveButton("SpellbookQuickCastButton");

    for (uint32_t spellOffset = 0; spellOffset < pSchoolDefinition->spellCount; ++spellOffset)
    {
        const uint32_t spellOrdinal = spellOffset + 1;
        const uint32_t spellId = pSchoolDefinition->firstSpellId + spellOffset;

        if (!view.activeMemberKnowsSpell(spellId))
        {
            continue;
        }

        const std::string layoutId = spellbookSpellLayoutId(view.m_spellbook.school, spellOrdinal);
        const OutdoorGameView::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

        if (pLayout == nullptr)
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pDefaultTexture = loadHudTexture(pLayout->primaryAsset);

        if (pDefaultTexture == nullptr)
        {
            continue;
        }

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
            layoutId,
            width,
            height,
            pLayout->width > 0.0f ? pLayout->width : static_cast<float>(pDefaultTexture->width),
            pLayout->height > 0.0f ? pLayout->height : static_cast<float>(pDefaultTexture->height));

        if (!resolved)
        {
            continue;
        }

        const bool isSelected = view.m_spellbook.selectedSpellId == spellId;
        const std::string *pInteractiveAssetName =
            view.resolveInteractiveAssetName(*pLayout, *resolved, mouseX, mouseY, isLeftMousePressed);
        const std::string *pSelectedAssetName =
            !pLayout->pressedAsset.empty()
                ? &pLayout->pressedAsset
                : (!pLayout->hoverAsset.empty() ? &pLayout->hoverAsset : &pLayout->primaryAsset);
        const std::string *pAssetName = isSelected ? pSelectedAssetName : pInteractiveAssetName;
        const OutdoorGameView::HudTextureHandle *pTexture =
            pAssetName != nullptr ? loadHudTexture(*pAssetName) : pDefaultTexture;

        if (pTexture != nullptr)
        {
            submitTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
        }
    }
}

void GameplayPartyOverlayRenderer::renderHeldInventoryItem(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_heldInventoryItem.active
        || view.m_pItemTable == nullptr
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const ItemDefinition *pItemDefinition = view.m_pItemTable->get(view.m_heldInventoryItem.item.objectDescriptionId);

    if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
    {
        return;
    }

    const OutdoorGameView::HudTextureHandle *pTexture =
        const_cast<OutdoorGameView &>(view).ensureHudTextureLoaded(pItemDefinition->iconName);

    if (pTexture == nullptr)
    {
        return;
    }

    setupHudProjection(width, height);

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float scale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    SDL_GetMouseState(&mouseX, &mouseY);
    const float itemX = std::round(mouseX - view.m_heldInventoryItem.grabOffsetX);
    const float itemY = std::round(mouseY - view.m_heldInventoryItem.grabOffsetY);
    const float itemWidth = static_cast<float>(pTexture->width) * scale;
    const float itemHeight = static_cast<float>(pTexture->height) * scale;

    view.submitHudTexturedQuad(*pTexture, itemX, itemY, itemWidth, itemHeight);

    const bgfx::TextureHandle tintedTextureHandle =
        const_cast<OutdoorGameView &>(view).ensureHudTextureColor(
            *pTexture,
            itemTintColorAbgr(&view.m_heldInventoryItem.item, pItemDefinition, ItemTintContext::Held));

    if (bgfx::isValid(tintedTextureHandle) && tintedTextureHandle.idx != pTexture->textureHandle.idx)
    {
        OutdoorGameView::HudTextureHandle tintedTexture = *pTexture;
        tintedTexture.textureHandle = tintedTextureHandle;
        view.submitHudTexturedQuad(tintedTexture, itemX, itemY, itemWidth, itemHeight);
    }
}
} // namespace OpenYAMM::Game
