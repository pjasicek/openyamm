#include "game/ui/GameplayHudOverlayRenderer.h"
#include "game/ui/GameplayOverlayContext.h"

#include "game/items/ItemRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <limits>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t BrokenItemTintColorAbgr = 0x800000ffu;
constexpr uint32_t UnidentifiedItemTintColorAbgr = 0x80ff0000u;

enum class ItemTintContext
{
    None,
    ShopIdentify,
    ShopRepair,
};

struct GoldHeapVisual
{
    const char *pTextureName = "item204";
    uint8_t width = 1;
    uint8_t height = 1;
    uint32_t objectDescriptionId = 187;
};

struct InventoryGridMetrics
{
    float x = 0.0f;
    float y = 0.0f;
    float cellWidth = 0.0f;
    float cellHeight = 0.0f;
    float scale = 1.0f;
};

struct InventoryItemScreenRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

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
        case ItemTintContext::ShopIdentify:
            if (isUnidentified)
            {
                return UnidentifiedItemTintColorAbgr;
            }

            break;

        case ItemTintContext::ShopRepair:
            if (isBroken)
            {
                return BrokenItemTintColorAbgr;
            }

            break;

        case ItemTintContext::None:
            break;
    }

    return 0xffffffffu;
}

GoldHeapVisual classifyGoldHeapVisual(uint32_t goldAmount)
{
    if (goldAmount <= 200)
    {
        return {"item204", 1, 1, 187};
    }

    if (goldAmount <= 1000)
    {
        return {"item205", 2, 1, 188};
    }

    return {"item206", 2, 1, 189};
}

InventoryGridMetrics computeInventoryGridMetrics(
    float x,
    float y,
    float width,
    float height,
    float scale,
    int columns,
    int rows)
{
    InventoryGridMetrics metrics = {};
    metrics.x = x;
    metrics.y = y;
    metrics.cellWidth = width / static_cast<float>(std::max(1, columns));
    metrics.cellHeight = height / static_cast<float>(std::max(1, rows));
    metrics.scale = scale;
    return metrics;
}

InventoryGridMetrics computeInventoryGridMetrics(
    float x,
    float y,
    float width,
    float height,
    float scale)
{
    return computeInventoryGridMetrics(x, y, width, height, scale, Character::InventoryWidth, Character::InventoryHeight);
}

InventoryItemScreenRect computeInventoryItemScreenRect(
    const InventoryGridMetrics &gridMetrics,
    const InventoryItem &item,
    float textureWidth,
    float textureHeight)
{
    const float slotSpanWidth = static_cast<float>(item.width) * gridMetrics.cellWidth;
    const float slotSpanHeight = static_cast<float>(item.height) * gridMetrics.cellHeight;
    const float offsetX = (slotSpanWidth - textureWidth) * 0.5f;
    const float offsetY = (slotSpanHeight - textureHeight) * 0.5f;

    InventoryItemScreenRect rect = {};
    rect.x = std::round(
        gridMetrics.x + static_cast<float>(item.gridX) * gridMetrics.cellWidth
        + offsetX);
    rect.y = std::round(
        gridMetrics.y + static_cast<float>(item.gridY) * gridMetrics.cellHeight
        + offsetY);
    rect.width = textureWidth;
    rect.height = textureHeight;
    return rect;
}

bool shouldRenderInCurrentPass(bool renderAboveHud, int hudZThreshold, int zIndex)
{
    return renderAboveHud ? zIndex >= hudZThreshold : zIndex < hudZThreshold;
}

std::string replaceAll(std::string text, const std::string &from, const std::string &to)
{
    size_t position = 0;

    while ((position = text.find(from, position)) != std::string::npos)
    {
        text.replace(position, from.size(), to);
        position += to.size();
    }

    return text;
}
} // namespace

void GameplayHudOverlayRenderer::renderChestPanel(GameplayOverlayContext &view, int width, int height, bool renderAboveHud)
{
    if (view.worldRuntime() == nullptr || !view.chestTable().has_value() || width <= 0 || height <= 0)
    {
        return;
    }

    const OutdoorWorldRuntime::ChestViewState *pChestView = view.worldRuntime()->activeChestView();

    if (pChestView == nullptr || view.currentHudScreenState() != GameplayHudScreenState::Chest)
    {
        return;
    }

    float chestMouseX = 0.0f;
    float chestMouseY = 0.0f;
    const SDL_MouseButtonFlags chestMouseButtons = SDL_GetMouseState(&chestMouseX, &chestMouseY);
    const bool isLeftMousePressed = (chestMouseButtons & SDL_BUTTON_LMASK) != 0;
    const ChestEntry *pChestEntry = view.chestTable()->get(pChestView->chestTypeId);
    const std::vector<std::string> orderedChestLayoutIds = view.sortedHudLayoutIdsForScreen("Chest");
    const Party *pParty = view.partyRuntime() != nullptr ? &view.partyRuntime()->party() : nullptr;
    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    for (const std::string &layoutId : orderedChestLayoutIds)
    {
        const GameplayOverlayContext::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);
        const std::string normalizedLayoutId = toLowerCopy(layoutId);

        if (pLayout == nullptr || !pLayout->visible)
        {
            continue;
        }

        if (normalizedLayoutId.rfind("chestnestedinventory", 0) == 0)
        {
            continue;
        }

        if (!shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pLayout->zIndex))
        {
            continue;
        }

        const float fallbackWidth = pLayout->width > 0.0f ? pLayout->width : 0.0f;
        const float fallbackHeight = pLayout->height > 0.0f ? pLayout->height : 0.0f;
        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
            layoutId,
            width,
            height,
            fallbackWidth,
            fallbackHeight);

        if (!resolved)
        {
            continue;
        }

        std::string assetName = pLayout->primaryAsset;

        if (normalizedLayoutId == "chestbackground" && pChestEntry != nullptr && !pChestEntry->textureName.empty())
        {
            assetName = pChestEntry->textureName;
        }
        else if (pLayout->interactive)
        {
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> interactiveResolved =
                view.resolveHudLayoutElement(
                layoutId,
                width,
                height,
                pLayout->width,
                pLayout->height);

            if (interactiveResolved)
            {
                if (const std::string *pInteractiveAsset = view.resolveInteractiveAssetName(
                        *pLayout,
                        *interactiveResolved,
                        chestMouseX,
                        chestMouseY,
                        isLeftMousePressed))
                {
                    assetName = *pInteractiveAsset;
                }
            }
        }

        if (!assetName.empty())
        {
            const std::optional<GameplayOverlayContext::HudTextureHandle> texture = view.ensureHudTextureLoaded(assetName);

            if (texture)
            {
                if (normalizedLayoutId == "chesticonbackground")
                {
                    const std::optional<GameplayOverlayContext::HudTextureHandle> portraitBorder =
                        view.ensureHudTextureLoaded("evtnpc");

                    if (portraitBorder)
                    {
                        const float borderSize = std::min(resolved->width, resolved->height);
                        const float borderX = std::round(resolved->x + (resolved->width - borderSize) * 0.5f);
                        const float borderY = std::round(resolved->y + (resolved->height - borderSize) * 0.5f);
                        view.submitHudTexturedQuad(*portraitBorder, borderX, borderY, borderSize, borderSize);
                    }
                }

                const float renderWidth =
                    pLayout->width > 0.0f ? resolved->width : static_cast<float>(texture->width) * resolved->scale;
                const float renderHeight =
                    pLayout->height > 0.0f ? resolved->height : static_cast<float>(texture->height) * resolved->scale;
                view.submitHudTexturedQuad(*texture, resolved->x, resolved->y, renderWidth, renderHeight);
            }
        }

        if (!pLayout->fontName.empty() && !pLayout->labelText.empty())
        {
            std::string label = pLayout->labelText;

            if (pParty != nullptr)
            {
                label = replaceAll(label, "{gold}", std::to_string(pParty->gold()));
                label = replaceAll(label, "{food}", std::to_string(pParty->food()));
            }

            view.renderLayoutLabel(*pLayout, *resolved, label);
        }

        if (normalizedLayoutId != "chestgridarea")
        {
            continue;
        }

        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedGrid =
            view.resolveChestGridArea(width, height);

        if (!resolvedGrid || pChestView->gridWidth == 0 || pChestView->gridHeight == 0)
        {
            continue;
        }

        const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
            resolvedGrid->x,
            resolvedGrid->y,
            resolvedGrid->width,
            resolvedGrid->height,
            resolvedGrid->scale,
            pChestView->gridWidth,
            pChestView->gridHeight);

        for (const OutdoorWorldRuntime::ChestItemState &item : pChestView->items)
        {
            InventoryItem renderItem = {};
            renderItem.objectDescriptionId = item.itemId;
            renderItem.quantity = item.quantity;
            renderItem.width = item.width;
            renderItem.height = item.height;
            renderItem.gridX = item.gridX;
            renderItem.gridY = item.gridY;

            if (item.isGold)
            {
                const GoldHeapVisual goldVisual = classifyGoldHeapVisual(item.goldAmount);
                renderItem.width = goldVisual.width;
                renderItem.height = goldVisual.height;

                const std::optional<GameplayOverlayContext::HudTextureHandle> goldTexture =
                    view.ensureHudTextureLoaded(goldVisual.pTextureName);

                if (!goldTexture)
                {
                    continue;
                }

                const float itemWidth = static_cast<float>(goldTexture->width) * gridMetrics.scale;
                const float itemHeight = static_cast<float>(goldTexture->height) * gridMetrics.scale;
                const InventoryItemScreenRect itemRect =
                    computeInventoryItemScreenRect(gridMetrics, renderItem, itemWidth, itemHeight);
                view.submitHudTexturedQuad(*goldTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height);

                GameplayRenderedInspectableHudItem inspectableItem = {};
                inspectableItem.objectDescriptionId = goldVisual.objectDescriptionId;
                inspectableItem.textureName = goldVisual.pTextureName;
                inspectableItem.hasValueOverride = true;
                inspectableItem.valueOverride = std::min(item.goldAmount, static_cast<uint32_t>(std::numeric_limits<int>::max()));
                inspectableItem.x = itemRect.x;
                inspectableItem.y = itemRect.y;
                inspectableItem.width = itemRect.width;
                inspectableItem.height = itemRect.height;
                view.addRenderedInspectableHudItem(inspectableItem);
                continue;
            }

            const ItemDefinition *pItemDefinition = view.itemTable() != nullptr ? view.itemTable()->get(item.itemId) : nullptr;

            if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
            {
                continue;
            }

            const std::optional<GameplayOverlayContext::HudTextureHandle> itemTexture =
                view.ensureHudTextureLoaded(pItemDefinition->iconName);

            if (!itemTexture)
            {
                continue;
            }

            const float itemWidth = static_cast<float>(itemTexture->width) * gridMetrics.scale;
            const float itemHeight = static_cast<float>(itemTexture->height) * gridMetrics.scale;
            const InventoryItemScreenRect itemRect =
                computeInventoryItemScreenRect(gridMetrics, renderItem, itemWidth, itemHeight);
            view.submitHudTexturedQuad(*itemTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height);

            if (pItemDefinition->itemId == 0)
            {
                continue;
            }

            GameplayRenderedInspectableHudItem inspectableItem = {};
            inspectableItem.objectDescriptionId = pItemDefinition->itemId;
            inspectableItem.textureName = pItemDefinition->iconName;
            inspectableItem.x = itemRect.x;
            inspectableItem.y = itemRect.y;
            inspectableItem.width = itemRect.width;
            inspectableItem.height = itemRect.height;
            view.addRenderedInspectableHudItem(inspectableItem);
        }
    }
}

void GameplayHudOverlayRenderer::renderInventoryNestedOverlay(
    GameplayOverlayContext &view,
    int width,
    int height,
    bool renderAboveHud)
{
    const bool isChestTransfer =
        view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ChestTransfer
        && view.currentHudScreenState() == GameplayHudScreenState::Chest;
    const bool isInventoryService =
        (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
        && view.currentHudScreenState() == GameplayHudScreenState::Dialogue;

    if (renderAboveHud
        || !view.inventoryNestedOverlay().active
        || (!isChestTransfer && !isInventoryService)
        || view.partyRuntime() == nullptr
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pPageLayout = view.findHudLayoutElement("ChestNestedInventoryPage");
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedPage =
        pPageLayout != nullptr
        ? view.resolveHudLayoutElement(
            "ChestNestedInventoryPage",
            width,
            height,
            pPageLayout->width,
            pPageLayout->height)
        : std::nullopt;

    if (pPageLayout == nullptr || !resolvedPage)
    {
        return;
    }

    if (!pPageLayout->primaryAsset.empty())
    {
        const std::optional<GameplayOverlayContext::HudTextureHandle> pageTexture =
            view.ensureHudTextureLoaded(pPageLayout->primaryAsset);

        if (pageTexture)
        {
            view.submitHudTexturedQuad(*pageTexture, resolvedPage->x, resolvedPage->y, resolvedPage->width, resolvedPage->height);
        }
    }

    const Character *pCharacter = view.partyRuntime()->party().activeMember();
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedInventoryGrid =
        view.resolveInventoryNestedOverlayGridArea(width, height);

    if (pCharacter == nullptr || !resolvedInventoryGrid)
    {
        return;
    }

    const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
        resolvedInventoryGrid->x,
        resolvedInventoryGrid->y,
        resolvedInventoryGrid->width,
        resolvedInventoryGrid->height,
        resolvedInventoryGrid->scale);

    for (const InventoryItem &item : pCharacter->inventory)
    {
        const ItemDefinition *pItemDefinition =
            view.itemTable() != nullptr ? view.itemTable()->get(item.objectDescriptionId) : nullptr;

        if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
        {
            continue;
        }

        const std::optional<GameplayOverlayContext::HudTextureHandle> itemTexture =
            view.ensureHudTextureLoaded(pItemDefinition->iconName);

        if (!itemTexture)
        {
            continue;
        }

        const float itemWidth = static_cast<float>(itemTexture->width) * gridMetrics.scale;
        const float itemHeight = static_cast<float>(itemTexture->height) * gridMetrics.scale;
        const InventoryItemScreenRect itemRect =
            computeInventoryItemScreenRect(gridMetrics, item, itemWidth, itemHeight);
        view.submitHudTexturedQuad(*itemTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height);

        ItemTintContext tintContext = ItemTintContext::None;

        switch (view.inventoryNestedOverlay().mode)
        {
            case GameplayUiController::InventoryNestedOverlayMode::ShopIdentify:
                tintContext = ItemTintContext::ShopIdentify;
                break;

            case GameplayUiController::InventoryNestedOverlayMode::ShopRepair:
                tintContext = ItemTintContext::ShopRepair;
                break;

            default:
                break;
        }

        const bgfx::TextureHandle tintedTextureHandle =
            view.ensureHudTextureColor(*itemTexture, itemTintColorAbgr(&item, pItemDefinition, tintContext));

        if (bgfx::isValid(tintedTextureHandle) && tintedTextureHandle.idx != itemTexture->textureHandle.idx)
        {
            GameplayOverlayContext::HudTextureHandle tintedTexture = *itemTexture;
            tintedTexture.textureHandle = tintedTextureHandle;
            view.submitHudTexturedQuad(tintedTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height);
        }

        GameplayRenderedInspectableHudItem inspectableItem = {};
        inspectableItem.objectDescriptionId = pItemDefinition->itemId;
        inspectableItem.hasItemState = true;
        inspectableItem.itemState = item;
        inspectableItem.sourceType = GameplayUiController::ItemInspectSourceType::Inventory;
        inspectableItem.sourceMemberIndex = view.partyRuntime()->party().activeMemberIndex();
        inspectableItem.sourceGridX = item.gridX;
        inspectableItem.sourceGridY = item.gridY;
        inspectableItem.textureName = pItemDefinition->iconName;
        inspectableItem.x = itemRect.x;
        inspectableItem.y = itemRect.y;
        inspectableItem.width = itemRect.width;
        inspectableItem.height = itemRect.height;
        view.addRenderedInspectableHudItem(inspectableItem);
    }
}
} // namespace OpenYAMM::Game
