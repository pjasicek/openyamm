#include "game/ui/GameplayHudOverlayRenderer.h"
#include "engine/Localization.h"
#include "game/ui/GameplayHudOverlaySupport.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"

#include "game/items/InventoryBags.h"
#include "game/items/ItemRuntime.h"
#include "game/rules/GameRules.h"
#include "game/ui/GameplayUiSkin.h"
#include "game/ui/InventoryBagOverview.h"
#include "game/tables/ItemTable.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <limits>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t BrokenItemTintColorAbgr = 0xff0000ffu;
constexpr uint32_t ShopUnidentifiedItemTintColorAbgr = 0xff00e100u;

enum class ItemTintContext
{
    Inventory,
    ShopInventory,
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

struct PointerRenderInput
{
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    bool isLeftMousePressed = false;
};

PointerRenderInput pointerRenderInput(const GameplayScreenRuntime &view)
{
    PointerRenderInput input = {};
    const GameplayInputFrame *pInputFrame = view.currentGameplayInputFrame();

    if (pInputFrame == nullptr)
    {
        return input;
    }

    input.mouseX = pInputFrame->pointerX;
    input.mouseY = pInputFrame->pointerY;
    input.isLeftMousePressed = pInputFrame->leftMouseButton.held;
    return input;
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

    if (isBroken)
    {
        return BrokenItemTintColorAbgr;
    }

    if (context == ItemTintContext::ShopInventory && isUnidentified)
    {
        return ShopUnidentifiedItemTintColorAbgr;
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

void renderViewportParchmentSidePanels(GameplayScreenRuntime &view, int width, int height)
{
    view.renderViewportSidePanels(width, height, "obsidian_reading_surface");
}
// Several bags (MAW): a button per bag over a chest's or shop's party inventory, the active member's open bag
// selected (none while a shop shows the bag overview), with its tags in the corners; the bag that takes what is moved
// there.
void renderPartyBagButtons(GameplayScreenRuntime &view, int width, int height)
{
    const Party *pParty = view.partyReadOnly();
    const Character *pCharacter = pParty != nullptr ? pParty->activeMember() : nullptr;
    const int bagCount = pParty != nullptr ? gameRulesFor(pParty).items.bagCount(*pParty) : 1;
    // The buttons name the bags of the open bag's tab.
    const int firstBag = pCharacter != nullptr ? InventoryBagOverview::firstBag(*pCharacter) : 0;

    for (int bag = firstBag; pCharacter != nullptr && bagCount > 1 && bag < std::min(bagCount,
             firstBag + InventoryBagOverview::Bags); ++bag)
    {
        const std::string id = "ChestInventoryBag" + std::to_string(bag - firstBag + 1);
        const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(id);

        if (pLayout == nullptr)
        {
            continue;
        }

        GameplayUiSkin::renderButton(view, id, width, height,
            !GameplayHudOverlaySupport::shopBagOverviewActive(view) && pCharacter->rulesetState.currentBag == bag,
            true);
        const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> button =
            view.resolveHudLayoutElement(id, width, height, pLayout->width, pLayout->height);

        if (button)
        {
            const float markSize = std::round(11.0f * button->scale);
            GameplayHudOverlaySupport::renderBagTagMarks(view, *pCharacter, uint8_t(bag),
                button->x - 2.0f * button->scale, button->y + button->height - markSize + 3.0f * button->scale,
                button->width + 4.0f * button->scale, markSize);
        }
    }
}
} // namespace

void GameplayHudOverlayRenderer::renderChestPanel(GameplayScreenRuntime &view, int width, int height, bool renderAboveHud)
{
    if (view.worldRuntime() == nullptr || view.chestTable() == nullptr || width <= 0 || height <= 0)
    {
        return;
    }

    const GameplayChestViewState *pChestView = view.worldRuntime()->activeChestView();

    if (pChestView == nullptr || view.currentHudScreenState() != GameplayHudScreenState::Chest)
    {
        return;
    }

    const PointerRenderInput pointerInput = pointerRenderInput(view);
    const float chestMouseX = pointerInput.mouseX;
    const float chestMouseY = pointerInput.mouseY;
    const bool isLeftMousePressed = pointerInput.isLeftMousePressed;
    const ChestEntry *pChestEntry = view.chestTable()->get(pChestView->chestTypeId);
    const std::vector<std::string> orderedChestLayoutIds = view.sortedHudLayoutIdsForScreen("Chest");
    const Party *pParty = view.partyReadOnly();
    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (!renderAboveHud)
    {
        renderViewportParchmentSidePanels(view, width, height);
    }

    for (const std::string &layoutId : orderedChestLayoutIds)
    {
        const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);
        const std::string normalizedLayoutId = toLowerCopy(layoutId);

        if (pLayout == nullptr || !pLayout->visible)
        {
            continue;
        }

        if (normalizedLayoutId.rfind("chestnestedinventory", 0) == 0
            || normalizedLayoutId.rfind("chestinventorybag", 0) == 0)
        {
            continue;
        }

        if (!shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pLayout->zIndex))
        {
            continue;
        }

        const float fallbackWidth = pLayout->width > 0.0f ? pLayout->width : 0.0f;
        const float fallbackHeight = pLayout->height > 0.0f ? pLayout->height : 0.0f;
        const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
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
            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> interactiveResolved =
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
            const std::optional<GameplayScreenRuntime::HudTextureHandle> texture = view.gameplayUiRuntime().ensureHudTextureLoaded(assetName);

            if (texture)
            {
                if (normalizedLayoutId == "chesticonbackground")
                {
                    const std::optional<GameplayScreenRuntime::HudTextureHandle> portraitBorder =
                        view.gameplayUiRuntime().ensureHudTextureLoaded("evtnpc");

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

            if (normalizedLayoutId == "chestinventorybutton" && view.inventoryNestedOverlay().active)
            {
                label = Engine::tr("Chest");
            }

            view.renderLayoutLabel(*pLayout, *resolved, label);
        }

        if (normalizedLayoutId != "chestgridarea")
        {
            continue;
        }

        const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedGrid =
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

        for (size_t itemIndex = 0; itemIndex < pChestView->items.size(); ++itemIndex)
        {
            const GameplayChestItemState &item = pChestView->items[itemIndex];
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

                const std::optional<GameplayScreenRuntime::HudTextureHandle> goldTexture =
                    view.gameplayUiRuntime().ensureHudTextureLoaded(goldVisual.pTextureName);

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

            const std::optional<GameplayScreenRuntime::HudTextureHandle> itemTexture =
                view.gameplayUiRuntime().ensureItemIconTextureLoaded(pItemDefinition->iconName);

            if (!itemTexture)
            {
                continue;
            }

            const float itemWidth =
                static_cast<float>(itemTexture->width) * gridMetrics.scale * pItemDefinition->inventoryDrawScale;
            const float itemHeight =
                static_cast<float>(itemTexture->height) * gridMetrics.scale * pItemDefinition->inventoryDrawScale;
            const InventoryItemScreenRect itemRect =
                computeInventoryItemScreenRect(gridMetrics, renderItem, itemWidth, itemHeight);
            GameplayHudOverlaySupport::renderItemRarityGlow(
                view, item.item, *itemTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height,
                gridMetrics.scale);
            view.submitHudTexturedQuad(*itemTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height);

            if (pItemDefinition->itemId == 0)
            {
                continue;
            }

            GameplayRenderedInspectableHudItem inspectableItem = {};
            inspectableItem.objectDescriptionId = pItemDefinition->itemId;
            inspectableItem.hasItemState = true;
            inspectableItem.itemState = item.item;
            inspectableItem.sourceType = GameplayUiController::ItemInspectSourceType::Chest;
            inspectableItem.sourceLootItemIndex = itemIndex;
            inspectableItem.textureName = pItemDefinition->iconName;
            inspectableItem.textureUsesItemIconTransparency = true;
            inspectableItem.x = itemRect.x;
            inspectableItem.y = itemRect.y;
            inspectableItem.width = itemRect.width;
            inspectableItem.height = itemRect.height;
            view.addRenderedInspectableHudItem(inspectableItem);
        }
    }

    // The bag that takes what is moved out of the chest (the nested inventory draws its own buttons).
    if (renderAboveHud && !view.inventoryNestedOverlay().active)
    {
        renderPartyBagButtons(view, width, height);
    }
}

void GameplayHudOverlayRenderer::renderInventoryNestedOverlay(
    GameplayScreenRuntime &view,
    int width,
    int height,
    bool renderAboveHud)
{
    const bool isChestTransfer =
        view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ChestTransfer
        && view.currentHudScreenState() == GameplayHudScreenState::Chest;
    const bool isShopInventory =
        (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopDisplay
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
        && view.currentHudScreenState() == GameplayHudScreenState::Dialogue;

    if (renderAboveHud
        || !view.inventoryNestedOverlay().active
        || (!isChestTransfer && !isShopInventory)
        || view.party() == nullptr
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const GameplayScreenRuntime::HudLayoutElement *pPageLayout = view.findHudLayoutElement("ChestNestedInventoryPage");
    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedPage =
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

    renderViewportParchmentSidePanels(view, width, height);

    if (!pPageLayout->primaryAsset.empty())
    {
        const std::optional<GameplayScreenRuntime::HudTextureHandle> pageTexture =
            view.gameplayUiRuntime().ensureHudTextureLoaded(pPageLayout->primaryAsset);

        if (pageTexture)
        {
            view.submitHudTexturedQuad(*pageTexture, resolvedPage->x, resolvedPage->y, resolvedPage->width, resolvedPage->height);
        }
    }

    const Character *pCharacter = view.partyReadOnly()->activeMember();
    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedInventoryGrid =
        view.resolveInventoryNestedOverlayGridArea(width, height);

    if (pCharacter == nullptr || !resolvedInventoryGrid)
    {
        return;
    }

    // The grid shows the active member's open bag, or a shop the four bags at once; several bags have a button each.
    renderPartyBagButtons(view, width, height);

    // Sell trash's pick (the sell screen): the picked items' cells are lit in gold under the icon and outlined over it,
    // and the other items are dimmed.
    const GameplayUiController::InventoryNestedOverlayState &overlay = view.inventoryNestedOverlay();
    const bool sellTrashPicking =
        overlay.mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell && overlay.sellTrashPicking;
    const size_t activeMemberIndex = view.partyReadOnly()->activeMemberIndex();
    const auto fillRect = [&view](float x, float y, float rectWidth, float rectHeight, uint32_t colorAbgr)
    {
        char name[40] = {};
        std::snprintf(name, sizeof(name), "__sell_trash_%08x__", colorAbgr);
        const std::optional<GameplayScreenRuntime::HudTextureHandle> texture =
            view.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colorAbgr);

        if (texture)
        {
            view.submitHudTexturedQuad(*texture, x, y, rectWidth, rectHeight);
        }
    };

    // One bag's items on its grid, each inspected in the bag it lies in.
    const auto renderBagItems =
        [&](const std::vector<InventoryItem> &items, const InventoryGridMetrics &gridMetrics, uint8_t bag)
        {
            for (const InventoryItem &item : items)
            {
                const bool picked = sellTrashPicking
                    && std::find(overlay.sellTrashItems.begin(), overlay.sellTrashItems.end(),
                           BagItemRef{activeMemberIndex, bag, item.gridX, item.gridY})
                        != overlay.sellTrashItems.end();
                const float cellsX = std::round(gridMetrics.x + float(item.gridX) * gridMetrics.cellWidth);
                const float cellsY = std::round(gridMetrics.y + float(item.gridY) * gridMetrics.cellHeight);
                const float cellsWidth = std::round(float(item.width) * gridMetrics.cellWidth);
                const float cellsHeight = std::round(float(item.height) * gridMetrics.cellHeight);
                const float line = std::max(1.0f, std::round(2.0f * gridMetrics.scale));

                if (picked)
                {
                    fillRect(cellsX, cellsY, cellsWidth, cellsHeight, 0x6030a0d8u);
                }

                const ItemDefinition *pItemDefinition =
                    view.itemTable() != nullptr ? view.itemTable()->get(item.objectDescriptionId) : nullptr;

                if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
                {
                    continue;
                }

                const std::optional<GameplayScreenRuntime::HudTextureHandle> itemTexture =
                    view.gameplayUiRuntime().ensureItemIconTextureLoaded(pItemDefinition->iconName);

                if (!itemTexture)
                {
                    continue;
                }

                const float itemWidth =
                    static_cast<float>(itemTexture->width) * gridMetrics.scale * pItemDefinition->inventoryDrawScale;
                const float itemHeight =
                    static_cast<float>(itemTexture->height) * gridMetrics.scale * pItemDefinition->inventoryDrawScale;
                const InventoryItemScreenRect itemRect =
                    computeInventoryItemScreenRect(gridMetrics, item, itemWidth, itemHeight);

                // OE keeps status tints unchanged between Display, Sell, Identify, and Repair.
                const ItemTintContext tintContext =
                    isShopInventory ? ItemTintContext::ShopInventory : ItemTintContext::Inventory;
                uint32_t tintColor = itemTintColorAbgr(&item, pItemDefinition, tintContext);

                // While picking, what stays is dimmed and faded so that the pick stands out.
                if (sellTrashPicking && !picked)
                {
                    const auto scaled = [tintColor](int shift, uint32_t percent)
                    {
                        return (((tintColor >> shift) & 0xffu) * percent / 100u) << shift;
                    };
                    tintColor = scaled(24, 60) | scaled(16, 40) | scaled(8, 40) | scaled(0, 40);
                }

                const bgfx::TextureHandle tintedTextureHandle =
                    view.gameplayUiRuntime().ensureHudTextureColorModulated(*itemTexture, tintColor);

                GameplayScreenRuntime::HudTextureHandle renderedTexture = *itemTexture;
                if (bgfx::isValid(tintedTextureHandle))
                {
                    renderedTexture.textureHandle = tintedTextureHandle;
                }

                // What stays loses its rarity glow too: a bright outline would outshine the pick.
                if (!sellTrashPicking || picked)
                {
                    GameplayHudOverlaySupport::renderItemRarityGlow(
                        view, item, *itemTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height,
                        gridMetrics.scale);
                }

                view.submitHudTexturedQuad(renderedTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height);

                if (picked)
                {
                    const uint32_t gold = 0xff4cc0f0u;
                    fillRect(cellsX, cellsY, cellsWidth, line, gold);
                    fillRect(cellsX, cellsY + cellsHeight - line, cellsWidth, line, gold);
                    fillRect(cellsX, cellsY + line, line, cellsHeight - 2 * line, gold);
                    fillRect(cellsX + cellsWidth - line, cellsY + line, line, cellsHeight - 2 * line, gold);
                }

                GameplayRenderedInspectableHudItem inspectableItem = {};
                inspectableItem.objectDescriptionId = pItemDefinition->itemId;
                inspectableItem.hasItemState = true;
                inspectableItem.itemState = item;
                inspectableItem.sourceType = GameplayUiController::ItemInspectSourceType::Inventory;
                inspectableItem.sourceMemberIndex = view.partyReadOnly()->activeMemberIndex();
                inspectableItem.sourceGridX = item.gridX;
                inspectableItem.sourceGridY = item.gridY;
                inspectableItem.sourceBag = bag;
                inspectableItem.textureName = pItemDefinition->iconName;
                inspectableItem.textureUsesItemIconTransparency = true;
                inspectableItem.x = itemRect.x;
                inspectableItem.y = itemRect.y;
                inspectableItem.width = itemRect.width;
                inspectableItem.height = itemRect.height;
                view.addRenderedInspectableHudItem(inspectableItem);
            }
        };

    if (GameplayHudOverlaySupport::shopBagOverviewActive(view))
    {
        const GameplayScreenRuntime::ResolvedHudLayoutElement &grid = *resolvedInventoryGrid;
        GameplayHudOverlaySupport::renderBagOverview(view, grid, *pCharacter,
            [&](const InventoryBagOverview::Slot &slot, uint8_t bag)
            {
                renderBagItems(InventoryBags::itemsInBag(*pCharacter, bag),
                    computeInventoryGridMetrics(slot.x, slot.y, slot.width, slot.height, grid.scale * slot.fraction),
                    bag);
            });
        return;
    }

    renderBagItems(pCharacter->inventory,
        computeInventoryGridMetrics(resolvedInventoryGrid->x, resolvedInventoryGrid->y, resolvedInventoryGrid->width,
            resolvedInventoryGrid->height, resolvedInventoryGrid->scale),
        pCharacter->rulesetState.currentBag);
}
} // namespace OpenYAMM::Game
