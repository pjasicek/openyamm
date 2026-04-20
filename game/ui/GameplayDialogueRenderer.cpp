#include "game/ui/GameplayDialogueRenderer.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayOverlayContext.h"
#include "game/ui/HudUiService.h"

#include "game/gameplay/HouseServiceRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/StringUtils.h"

#include <bx/math.h>

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <limits>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t HudViewId = 2;
constexpr uint32_t HoveredDialogueTopicTextColorAbgr = 0xff23cde1u;

enum class HouseShopVerticalAlign
{
    Center,
    Top,
    Bottom,
    Baseline
};

struct HouseShopSlotLayout
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    float baselineY = 0.0f;
    HouseShopVerticalAlign verticalAlign = HouseShopVerticalAlign::Center;
};

struct HouseShopVisualLayout
{
    std::string backgroundAsset;
    std::vector<HouseShopSlotLayout> slots;
};

struct HouseShopItemDrawRect
{
    size_t slotIndex = std::numeric_limits<size_t>::max();
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

bool isHouseType(const HouseEntry &houseEntry, const char *pTypeName)
{
    return houseEntry.type == pTypeName;
}

HouseShopVisualLayout buildHouseShopVisualLayout(const HouseEntry &houseEntry, bool spellbookMode)
{
    HouseShopVisualLayout layout = {};

    if (spellbookMode)
    {
        layout.backgroundAsset = "MAGSHELF";

        for (size_t index = 0; index < 6; ++index)
        {
            HouseShopSlotLayout topRowSlot = {};
            topRowSlot.x = 6.0f + static_cast<float>(index) * 75.0f;
            topRowSlot.y = 56.0f;
            topRowSlot.width = 74.0f;
            topRowSlot.height = 132.0f;
            topRowSlot.verticalAlign = HouseShopVerticalAlign::Bottom;
            layout.slots.push_back(topRowSlot);
        }

        for (size_t index = 0; index < 6; ++index)
        {
            HouseShopSlotLayout bottomRowSlot = {};
            bottomRowSlot.x = 6.0f + static_cast<float>(index) * 75.0f;
            bottomRowSlot.y = 199.0f;
            bottomRowSlot.width = 74.0f;
            bottomRowSlot.height = 128.0f;
            bottomRowSlot.verticalAlign = HouseShopVerticalAlign::Bottom;
            layout.slots.push_back(bottomRowSlot);
        }

        return layout;
    }

    if (isHouseType(houseEntry, "Weapon Shop"))
    {
        layout.backgroundAsset = "WEPNTABL";
        constexpr std::array<float, 6> weaponTopOffsets = {88.0f, 34.0f, 112.0f, 58.0f, 128.0f, 46.0f};

        for (size_t index = 0; index < weaponTopOffsets.size(); ++index)
        {
            HouseShopSlotLayout slot = {};
            slot.x = 25.0f + static_cast<float>(index) * 70.0f;
            slot.y = weaponTopOffsets[index];
            slot.width = 70.0f;
            slot.height = 334.0f - weaponTopOffsets[index];
            slot.verticalAlign = HouseShopVerticalAlign::Top;
            layout.slots.push_back(slot);
        }

        return layout;
    }

    if (isHouseType(houseEntry, "Armor Shop"))
    {
        layout.backgroundAsset = "ARMORY";

        for (size_t index = 0; index < 4; ++index)
        {
            HouseShopSlotLayout topRowSlot = {};
            topRowSlot.x = 34.0f + static_cast<float>(index) * 105.0f;
            topRowSlot.y = 8.0f;
            topRowSlot.width = 105.0f;
            topRowSlot.height = 90.0f;
            topRowSlot.verticalAlign = HouseShopVerticalAlign::Bottom;
            layout.slots.push_back(topRowSlot);
        }

        for (size_t index = 0; index < 4; ++index)
        {
            HouseShopSlotLayout bottomRowSlot = {};
            bottomRowSlot.x = 34.0f + static_cast<float>(index) * 105.0f;
            bottomRowSlot.y = 126.0f;
            bottomRowSlot.width = 105.0f;
            bottomRowSlot.height = 190.0f;
            bottomRowSlot.verticalAlign = HouseShopVerticalAlign::Top;
            layout.slots.push_back(bottomRowSlot);
        }

        return layout;
    }

    if (isHouseType(houseEntry, "Magic Shop") || isHouseType(houseEntry, "Alchemist"))
    {
        layout.backgroundAsset = "GENSHELF";

        for (size_t index = 0; index < 6; ++index)
        {
            HouseShopSlotLayout topRowSlot = {};
            topRowSlot.x = 6.0f + static_cast<float>(index) * 75.0f;
            topRowSlot.y = 63.0f;
            topRowSlot.width = 74.0f;
            topRowSlot.height = 132.0f;
            topRowSlot.baselineY = 201.0f;
            topRowSlot.verticalAlign = HouseShopVerticalAlign::Baseline;
            layout.slots.push_back(topRowSlot);
        }

        for (size_t index = 0; index < 6; ++index)
        {
            HouseShopSlotLayout bottomRowSlot = {};
            bottomRowSlot.x = 6.0f + static_cast<float>(index) * 75.0f;
            bottomRowSlot.y = 192.0f;
            bottomRowSlot.width = 74.0f;
            bottomRowSlot.height = 128.0f;
            bottomRowSlot.baselineY = 324.0f;
            bottomRowSlot.verticalAlign = HouseShopVerticalAlign::Baseline;
            layout.slots.push_back(bottomRowSlot);
        }

        return layout;
    }

    if (isHouseType(houseEntry, "Elemental Guild")
        || isHouseType(houseEntry, "Self Guild")
        || isHouseType(houseEntry, "Light Guild")
        || isHouseType(houseEntry, "Dark Guild")
        || isHouseType(houseEntry, "Spell Shop"))
    {
        layout.backgroundAsset = "MAGSHELF";

        for (size_t row = 0; row < 2; ++row)
        {
            for (size_t column = 0; column < 8; ++column)
            {
                HouseShopSlotLayout slot = {};
                slot.x = 14.0f + static_cast<float>(column) * 54.0f;
                slot.y = row == 0 ? 74.0f : 214.0f;
                slot.width = 48.0f;
                slot.height = 92.0f;
                slot.verticalAlign = HouseShopVerticalAlign::Top;
                layout.slots.push_back(slot);
            }
        }

        return layout;
    }

    return layout;
}

HouseShopItemDrawRect resolveHouseShopItemDrawRect(
    float frameX,
    float frameY,
    float frameWidth,
    float frameHeight,
    float frameScale,
    const HouseShopSlotLayout &slot,
    size_t slotIndex,
    int textureWidth,
    int textureHeight,
    int opaqueMinY,
    int opaqueMaxY)
{
    HouseShopItemDrawRect result = {};
    result.slotIndex = slotIndex;

    if (textureWidth <= 0 || textureHeight <= 0)
    {
        return result;
    }

    const float scaleX = frameWidth / 460.0f;
    const float scaleY = frameHeight / 344.0f;
    const float slotX = frameX + slot.x * scaleX;
    const float slotY = frameY + slot.y * scaleY;
    const float slotWidth = slot.width * scaleX;
    const float slotHeight = slot.height * scaleY;
    const float fitScale = std::min(
        slotWidth / static_cast<float>(textureWidth),
        slotHeight / static_cast<float>(textureHeight));
    const float itemScale = std::min(frameScale, fitScale);
    const float itemWidth = static_cast<float>(textureWidth) * itemScale;
    const float itemHeight = static_cast<float>(textureHeight) * itemScale;
    const float opaqueTop = static_cast<float>(std::max(0, opaqueMinY)) * itemScale;
    const float opaqueBottom = static_cast<float>(std::max(0, opaqueMaxY + 1)) * itemScale;

    result.width = itemWidth;
    result.height = itemHeight;
    result.x = std::round(slotX + (slotWidth - itemWidth) * 0.5f);

    switch (slot.verticalAlign)
    {
        case HouseShopVerticalAlign::Top:
            result.y = std::round(slotY - opaqueTop);
            break;

        case HouseShopVerticalAlign::Bottom:
            result.y = std::round(slotY + slotHeight - opaqueBottom);
            break;

        case HouseShopVerticalAlign::Baseline:
            result.y = std::round(frameY + slot.baselineY * scaleY - opaqueBottom);
            break;

        case HouseShopVerticalAlign::Center:
        default:
            result.y = std::round(slotY + (slotHeight - itemHeight) * 0.5f);
            break;
    }

    return result;
}

uint32_t currentDialogueHostHouseId(const EventRuntimeState *pEventRuntimeState)
{
    return pEventRuntimeState != nullptr ? pEventRuntimeState->dialogueState.hostHouseId : 0;
}

bool isResidentSelectionMode(const EventDialogContent &dialog)
{
    return !dialog.actions.empty()
        && std::all_of(
            dialog.actions.begin(),
            dialog.actions.end(),
            [](const EventDialogAction &action)
            {
                return action.kind == EventDialogActionKind::HouseResident;
            });
}

struct InventoryGridMetrics
{
    float x = 0.0f;
    float y = 0.0f;
    float cellWidth = 0.0f;
    float cellHeight = 0.0f;
};

InventoryGridMetrics computeInventoryGridMetrics(
    float x,
    float y,
    float width,
    float height,
    int columns,
    int rows)
{
    InventoryGridMetrics metrics = {};
    metrics.x = x;
    metrics.y = y;
    metrics.cellWidth = width / static_cast<float>(std::max(1, columns));
    metrics.cellHeight = height / static_cast<float>(std::max(1, rows));
    return metrics;
}

float snappedHudFontScale(float scale)
{
    if (scale < 1.0f)
    {
        return std::max(0.5f, scale);
    }

    const float roundedScale = std::round(scale);

    if (std::abs(scale - roundedScale) <= 0.1f)
    {
        return roundedScale;
    }

    return scale;
}
} // namespace

void GameplayDialogueRenderer::renderDialogueOverlay(
    GameplayOverlayContext &view,
    int width,
    int height,
    bool renderAboveHud)
{
    if (view.currentHudScreenState() != GameplayHudScreenState::Dialogue
        || !view.activeEventDialog().isActive
        || !view.hasHudRenderResources()
        || width <= 0
        || height <= 0)
    {
        return;
    }

    view.clearHudLayoutRuntimeHeightOverrides();
    float dialogMouseX = 0.0f;
    float dialogMouseY = 0.0f;
    SDL_GetMouseState(&dialogMouseX, &dialogMouseY);
    const GameplayUiViewportRect uiViewport = GameplayHudCommon::computeUiViewportRect(width, height);

    if (!renderAboveHud && uiViewport.x > 0.5f)
    {
        renderBlackoutBackdrop(view, width, height, uiViewport.x, uiViewport.width);
    }

    const bool residentSelectionMode = isResidentSelectionMode(view.activeEventDialog());
    const EventRuntimeState *pEventRuntimeState =
        view.worldRuntime() != nullptr ? view.worldRuntime()->eventRuntimeState() : nullptr;
    const HouseEntry *pHostHouseEntry =
        (currentDialogueHostHouseId(pEventRuntimeState) != 0 && view.houseTable() != nullptr)
        ? view.houseTable()->get(currentDialogueHostHouseId(pEventRuntimeState))
        : nullptr;
    const bool showDialogueVideoArea = pHostHouseEntry != nullptr;
    const bool hasDialogueParticipantIdentity =
        !view.activeEventDialog().title.empty()
        || view.activeEventDialog().participantPictureId != 0
        || view.activeEventDialog().sourceId != 0;
    const bool showEventDialogPanel =
        residentSelectionMode
        || !view.activeEventDialog().actions.empty()
        || pHostHouseEntry != nullptr
        || hasDialogueParticipantIdentity;
    const std::vector<std::string> &dialogueBodyLines = view.activeEventDialog().lines;
    const bool showDialogueTextFrame = !dialogueBodyLines.empty();
    std::optional<std::string> hoveredHouseServiceTopicText;
    const bool suppressServiceTopicsForShopOverlay =
        (view.houseShopOverlay().active
         && (view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuyStandard
             || view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpecial
             || view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpellbooks))
        || (view.inventoryNestedOverlay().active
            && (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
                || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
                || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair));
    const Party *pParty = view.partyReadOnly();

    updateHouseShopHoverTopicText(
        view,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        hoveredHouseServiceTopicText);

    const GameplayOverlayContext::HudLayoutElement *pDialogueFrameLayout = view.findHudLayoutElement("DialogueFrame");
    const GameplayOverlayContext::HudLayoutElement *pDialogueTextLayout = view.findHudLayoutElement("DialogueText");
    const GameplayOverlayContext::HudLayoutElement *pBasebarLayout = view.findHudLayoutElement("OutdoorBasebar");

    if (showDialogueTextFrame
        && pDialogueFrameLayout != nullptr
        && pDialogueTextLayout != nullptr
        && pBasebarLayout != nullptr
        && toLowerCopy(pDialogueFrameLayout->screen) == "dialogue"
        && toLowerCopy(pDialogueTextLayout->screen) == "dialogue")
    {
        const std::optional<GameplayOverlayContext::HudFontHandle> font =
            view.findHudFont(pDialogueTextLayout->fontName);

        if (font)
        {
            constexpr float DialogueTextTopInset = 2.0f;
            constexpr float DialogueTextBottomInset = 5.0f;
            constexpr float DialogueTextRightInset = 6.0f;
            const float lineHeight = static_cast<float>(font->fontHeight);
            const float textPadY = std::abs(pDialogueTextLayout->textPadY);
            const float textWrapWidth = std::max(
                0.0f,
                pDialogueTextLayout->width
                    - std::abs(pDialogueTextLayout->textPadX) * 2.0f
                    - DialogueTextRightInset);
            size_t wrappedLineCount = 0;

            for (const std::string &line : dialogueBodyLines)
            {
                const std::vector<std::string> wrappedLines =
                    view.wrapHudTextToWidth(*font, line, textWrapWidth);
                wrappedLineCount += std::max<size_t>(1, wrappedLines.size());
            }

            const float rawComputedTextHeight =
                static_cast<float>(wrappedLineCount) * lineHeight
                + textPadY * 2.0f
                + DialogueTextTopInset
                + DialogueTextBottomInset;
            const float authoritativeFrameHeight = pBasebarLayout->height + rawComputedTextHeight;
            view.setHudLayoutRuntimeHeightOverride("DialogueFrame", authoritativeFrameHeight);
            view.setHudLayoutRuntimeHeightOverride("DialogueText", rawComputedTextHeight);
        }
    }

    std::string dialogueResponseHintText =
        view.activeEventDialog().actions.empty()
            ? "Enter/Space/E/Esc close"
            : "Up/Down select  Enter/Space accept  E/Esc close";

    if (view.houseBankState().inputActive())
    {
        dialogueResponseHintText = "Type amount  Enter accept  E/Esc cancel";
    }

    if (view.statusBarEventRemainingSeconds() > 0.0f && !view.statusBarEventText().empty())
    {
        dialogueResponseHintText = view.statusBarEventText();
    }

    if (view.inventoryNestedOverlay().active
        && (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair))
    {
        if (view.statusBarEventRemainingSeconds() <= 0.0f || view.statusBarEventText().empty())
        {
            if (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell)
            {
                dialogueResponseHintText = "Select the Item to Sell";
            }
            else if (view.inventoryNestedOverlay().mode
                == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify)
            {
                dialogueResponseHintText = "Select the Item to Identify";
            }
            else if (view.inventoryNestedOverlay().mode
                == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
            {
                dialogueResponseHintText = "Select the Item to Repair";
            }
        }

        if (pHostHouseEntry != nullptr && view.party() != nullptr && view.itemTable() != nullptr)
        {
            const Character *pActiveCharacter = view.party()->activeMember();
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedInventoryGrid =
                view.resolveInventoryNestedOverlayGridArea(width, height);

            if (pActiveCharacter != nullptr && resolvedInventoryGrid)
            {
                const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                    resolvedInventoryGrid->x,
                    resolvedInventoryGrid->y,
                    resolvedInventoryGrid->width,
                    resolvedInventoryGrid->height,
                    Character::InventoryWidth,
                    Character::InventoryHeight);

                if (dialogMouseX >= resolvedInventoryGrid->x
                    && dialogMouseX < resolvedInventoryGrid->x + resolvedInventoryGrid->width
                    && dialogMouseY >= resolvedInventoryGrid->y
                    && dialogMouseY < resolvedInventoryGrid->y + resolvedInventoryGrid->height)
                {
                    const uint8_t gridX = static_cast<uint8_t>(std::clamp(
                        static_cast<int>((dialogMouseX - resolvedInventoryGrid->x) / gridMetrics.cellWidth),
                        0,
                        Character::InventoryWidth - 1));
                    const uint8_t gridY = static_cast<uint8_t>(std::clamp(
                        static_cast<int>((dialogMouseY - resolvedInventoryGrid->y) / gridMetrics.cellHeight),
                        0,
                        Character::InventoryHeight - 1));
                    const InventoryItem *pItem = pActiveCharacter->inventoryItemAt(gridX, gridY);

                    if (pItem != nullptr)
                    {
                        if (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell)
                        {
                            hoveredHouseServiceTopicText = HouseServiceRuntime::buildSellHoverText(
                                *view.party(),
                                *view.itemTable(),
                                *view.standardItemEnchantTable(),
                                *view.specialItemEnchantTable(),
                                *pHostHouseEntry,
                                *pItem);
                        }
                        else if (view.inventoryNestedOverlay().mode
                            == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify)
                        {
                            hoveredHouseServiceTopicText = HouseServiceRuntime::buildIdentifyHoverText(
                                *view.party(),
                                *view.itemTable(),
                                *view.standardItemEnchantTable(),
                                *view.specialItemEnchantTable(),
                                *pHostHouseEntry,
                                *pItem);
                        }
                        else if (view.inventoryNestedOverlay().mode
                            == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
                        {
                            const std::string hoverText = HouseServiceRuntime::buildRepairHoverText(
                                *view.party(),
                                *view.itemTable(),
                                *view.standardItemEnchantTable(),
                                *view.specialItemEnchantTable(),
                                *pHostHouseEntry,
                                *pItem);

                            if (!hoverText.empty())
                            {
                                hoveredHouseServiceTopicText = hoverText;
                            }
                        }
                    }
                }
            }
        }
    }

    const std::vector<std::string> orderedDialogueLayoutIds = view.sortedHudLayoutIdsForScreen("Dialogue");

    for (const std::string &layoutId : orderedDialogueLayoutIds)
    {
        const GameplayOverlayContext::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

        if (pLayout == nullptr || toLowerCopy(pLayout->screen) != "dialogue")
        {
            continue;
        }

        renderDialogueTextureElement(
            view,
            layoutId,
            width,
            height,
            dialogMouseX,
            dialogMouseY,
            showDialogueTextFrame,
            showDialogueVideoArea,
            showEventDialogPanel,
            renderAboveHud);
    }

    renderHouseShopOverlay(
        view,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        dialogueResponseHintText,
        renderAboveHud);

    renderDialogueLabelById(
        view,
        "DialogueGoodbyeButton",
        (view.activeEventDialog().presentation == EventDialogPresentation::Transition
            && view.activeEventDialog().actions.size() > 1)
            ? view.activeEventDialog().actions[1].label
            : "Close",
        width,
        height,
        renderAboveHud);

    if (view.activeEventDialog().presentation == EventDialogPresentation::Transition
        && !view.activeEventDialog().actions.empty())
    {
        renderDialogueLabelById(
            view,
            "DialogueOkButton",
            view.activeEventDialog().actions[0].label,
            width,
            height,
            renderAboveHud);
    }

    renderDialogueLabelById(
        view,
        "DialogueGoldLabel",
        pParty != nullptr ? std::to_string(pParty->gold()) : "",
        width,
        height,
        renderAboveHud);
    renderDialogueLabelById(
        view,
        "DialogueFoodLabel",
        pParty != nullptr ? std::to_string(pParty->food()) : "",
        width,
        height,
        renderAboveHud);
    renderDialogueLabelById(
        view,
        "DialogueResponseHint",
        dialogueResponseHintText,
        width,
        height,
        renderAboveHud);
    renderDialogueEventPanel(
        view,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        renderAboveHud,
        showEventDialogPanel,
        residentSelectionMode,
        pHostHouseEntry,
        hoveredHouseServiceTopicText,
        suppressServiceTopicsForShopOverlay);
    renderDialogueBodyText(
        view,
        width,
        height,
        renderAboveHud,
        dialogueBodyLines);

    view.clearHudLayoutRuntimeHeightOverrides();
}

bool GameplayDialogueRenderer::shouldRenderInCurrentPass(bool renderAboveHud, int hudZThreshold, int zIndex)
{
    return renderAboveHud ? zIndex >= hudZThreshold : zIndex < hudZThreshold;
}

bool GameplayDialogueRenderer::isDialogueFrameSubtree(GameplayOverlayContext &view, const std::string &layoutId)
{
    std::string currentLayoutId = layoutId;

    while (!currentLayoutId.empty())
    {
        if (toLowerCopy(currentLayoutId) == "dialogueframe")
        {
            return true;
        }

        const GameplayOverlayContext::HudLayoutElement *pCurrentLayout = view.findHudLayoutElement(currentLayoutId);

        if (pCurrentLayout == nullptr || pCurrentLayout->parentId.empty())
        {
            break;
        }

        currentLayoutId = pCurrentLayout->parentId;
    }

    return false;
}

void GameplayDialogueRenderer::renderBlackoutBackdrop(
    GameplayOverlayContext &view,
    int screenWidth,
    int screenHeight,
    float viewportX,
    float viewportWidth)
{
    (void)viewportX;
    (void)viewportWidth;
    HudUiService::renderViewportSidePanels(view, screenWidth, screenHeight, "UI-Parch");
}

void GameplayDialogueRenderer::updateHouseShopHoverTopicText(
    GameplayOverlayContext &view,
    int width,
    int height,
    float dialogMouseX,
    float dialogMouseY,
    std::optional<std::string> &hoveredHouseServiceTopicText)
{
    if (!view.houseShopOverlay().active
        || view.party() == nullptr
        || view.worldRuntime() == nullptr
        || view.itemTable() == nullptr
        || view.houseTable() == nullptr)
    {
        return;
    }

    const HouseEntry *pHouseEntry = view.houseTable()->get(view.houseShopOverlay().houseId);

    if (pHouseEntry == nullptr)
    {
        return;
    }

    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedFrame =
        view.resolveHouseShopOverlayFrame(width, height);

    if (!resolvedFrame)
    {
        return;
    }

    std::optional<HouseStockMode> stockMode;

    switch (view.houseShopOverlay().mode)
    {
        case GameplayUiController::HouseShopMode::BuyStandard:
            stockMode = HouseStockMode::ShopStandard;
            break;

        case GameplayUiController::HouseShopMode::BuySpecial:
            stockMode = HouseStockMode::ShopSpecial;
            break;

        case GameplayUiController::HouseShopMode::BuySpellbooks:
            stockMode = HouseStockMode::GuildSpellbooks;
            break;

        case GameplayUiController::HouseShopMode::None:
        default:
            return;
    }

    Party &party = *view.party();
    const std::vector<InventoryItem> &stock = HouseServiceRuntime::ensureStock(
        party,
        *view.itemTable(),
        *view.standardItemEnchantTable(),
        *view.specialItemEnchantTable(),
        *pHouseEntry,
        view.worldRuntime()->gameMinutes(),
        *stockMode);
    const size_t slotCount = HouseServiceRuntime::slotCountForStockMode(*pHouseEntry, *stockMode);
    const HouseShopVisualLayout overlayLayout =
        buildHouseShopVisualLayout(
            *pHouseEntry,
            view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpellbooks);

    for (size_t slotIndex = 0;
         slotIndex < slotCount && slotIndex < stock.size() && slotIndex < overlayLayout.slots.size();
         ++slotIndex)
    {
        const InventoryItem &item = stock[slotIndex];

        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        const ItemDefinition *pItemDefinition = view.itemTable()->get(item.objectDescriptionId);

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

        int opaqueTextureWidth = itemTexture->width;
        int opaqueTextureHeight = itemTexture->height;
        int opaqueMinX = 0;
        int opaqueMinY = 0;
        int opaqueMaxX = itemTexture->width - 1;
        int opaqueMaxY = itemTexture->height - 1;
        view.tryGetOpaqueHudTextureBounds(
            pItemDefinition->iconName,
            opaqueTextureWidth,
            opaqueTextureHeight,
            opaqueMinX,
            opaqueMinY,
            opaqueMaxX,
            opaqueMaxY);
        const HouseShopItemDrawRect drawRect = resolveHouseShopItemDrawRect(
            resolvedFrame->x,
            resolvedFrame->y,
            static_cast<float>(resolvedFrame->width),
            static_cast<float>(resolvedFrame->height),
            resolvedFrame->scale,
            overlayLayout.slots[slotIndex],
            slotIndex,
            itemTexture->width,
            itemTexture->height,
            opaqueMinY,
            opaqueMaxY);

        if (dialogMouseX >= drawRect.x
            && dialogMouseX < drawRect.x + drawRect.width
            && dialogMouseY >= drawRect.y
            && dialogMouseY < drawRect.y + drawRect.height)
        {
            hoveredHouseServiceTopicText =
                HouseServiceRuntime::buildBuyHoverText(
                    party,
                    *view.itemTable(),
                    *view.standardItemEnchantTable(),
                    *view.specialItemEnchantTable(),
                    *pHouseEntry,
                    item);
            return;
        }
    }
}

void GameplayDialogueRenderer::renderHouseShopOverlay(
    GameplayOverlayContext &view,
    int width,
    int height,
    float dialogMouseX,
    float dialogMouseY,
    std::string &dialogueResponseHintText,
    bool renderAboveHud)
{
    if (!view.houseShopOverlay().active
        || view.party() == nullptr
        || view.worldRuntime() == nullptr
        || view.itemTable() == nullptr
        || view.houseTable() == nullptr)
    {
        return;
    }

    const HouseEntry *pHouseEntry = view.houseTable()->get(view.houseShopOverlay().houseId);

    if (pHouseEntry == nullptr)
    {
        return;
    }

    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedFrame =
        view.resolveHouseShopOverlayFrame(width, height);

    if (!resolvedFrame)
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pFrameLayout = view.findHudLayoutElement("DialogueShopOverlayFrame");
    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (pFrameLayout != nullptr && shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pFrameLayout->zIndex))
    {
        const HouseShopVisualLayout overlayLayout =
            buildHouseShopVisualLayout(
                *pHouseEntry,
                view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpellbooks);
        const std::string backgroundAsset =
            !overlayLayout.backgroundAsset.empty() ? overlayLayout.backgroundAsset : pFrameLayout->primaryAsset;

        if (!backgroundAsset.empty())
        {
            const std::optional<GameplayOverlayContext::HudTextureHandle> frameTexture =
                view.ensureHudTextureLoaded(backgroundAsset);

            if (frameTexture)
            {
                view.submitHudTexturedQuad(
                    *frameTexture,
                    resolvedFrame->x,
                    resolvedFrame->y,
                    resolvedFrame->width,
                    resolvedFrame->height);
            }
        }
    }

    std::optional<HouseStockMode> stockMode;

    switch (view.houseShopOverlay().mode)
    {
        case GameplayUiController::HouseShopMode::BuyStandard:
            stockMode = HouseStockMode::ShopStandard;
            break;

        case GameplayUiController::HouseShopMode::BuySpecial:
            stockMode = HouseStockMode::ShopSpecial;
            break;

        case GameplayUiController::HouseShopMode::BuySpellbooks:
            stockMode = HouseStockMode::GuildSpellbooks;
            break;

        case GameplayUiController::HouseShopMode::None:
        default:
            return;
    }

    Party &party = *view.party();
    const std::vector<InventoryItem> &stock = HouseServiceRuntime::ensureStock(
        party,
        *view.itemTable(),
        *view.standardItemEnchantTable(),
        *view.specialItemEnchantTable(),
        *pHouseEntry,
        view.worldRuntime()->gameMinutes(),
        *stockMode);
    const size_t slotCount = HouseServiceRuntime::slotCountForStockMode(*pHouseEntry, *stockMode);
    const HouseShopVisualLayout overlayLayout =
        buildHouseShopVisualLayout(
            *pHouseEntry,
            view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpellbooks);
    bool hoveredItem = false;

    for (size_t slotIndex = 0;
         slotIndex < slotCount && slotIndex < stock.size() && slotIndex < overlayLayout.slots.size();
         ++slotIndex)
    {
        const InventoryItem &item = stock[slotIndex];

        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        const ItemDefinition *pItemDefinition = view.itemTable()->get(item.objectDescriptionId);

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

        int opaqueTextureWidth = itemTexture->width;
        int opaqueTextureHeight = itemTexture->height;
        int opaqueMinX = 0;
        int opaqueMinY = 0;
        int opaqueMaxX = itemTexture->width - 1;
        int opaqueMaxY = itemTexture->height - 1;
        view.tryGetOpaqueHudTextureBounds(
            pItemDefinition->iconName,
            opaqueTextureWidth,
            opaqueTextureHeight,
            opaqueMinX,
            opaqueMinY,
            opaqueMaxX,
            opaqueMaxY);
        const HouseShopItemDrawRect drawRect = resolveHouseShopItemDrawRect(
            resolvedFrame->x,
            resolvedFrame->y,
            static_cast<float>(resolvedFrame->width),
            static_cast<float>(resolvedFrame->height),
            resolvedFrame->scale,
            overlayLayout.slots[slotIndex],
            slotIndex,
            itemTexture->width,
            itemTexture->height,
            opaqueMinY,
            opaqueMaxY);
        view.submitHudTexturedQuad(*itemTexture, drawRect.x, drawRect.y, drawRect.width, drawRect.height);

        GameplayRenderedInspectableHudItem inspectableItem = {};
        inspectableItem.objectDescriptionId = item.objectDescriptionId;
        inspectableItem.hasItemState = true;
        inspectableItem.itemState = item;
        inspectableItem.textureName = pItemDefinition->iconName;
        inspectableItem.x = drawRect.x;
        inspectableItem.y = drawRect.y;
        inspectableItem.width = drawRect.width;
        inspectableItem.height = drawRect.height;
        view.addRenderedInspectableHudItem(inspectableItem);

        if (dialogMouseX >= drawRect.x
            && dialogMouseX < drawRect.x + drawRect.width
            && dialogMouseY >= drawRect.y
            && dialogMouseY < drawRect.y + drawRect.height)
        {
            hoveredItem = true;
        }
    }

    if (!hoveredItem && (view.statusBarEventRemainingSeconds() <= 0.0f || view.statusBarEventText().empty()))
    {
        dialogueResponseHintText = "LMB buy  RMB inspect  Esc close";
    }
}

void GameplayDialogueRenderer::renderDialogueTextureElement(
    GameplayOverlayContext &view,
    const std::string &layoutId,
    int width,
    int height,
    float dialogMouseX,
    float dialogMouseY,
    bool showDialogueTextFrame,
    bool showDialogueVideoArea,
    bool showEventDialogPanel,
    bool renderAboveHud)
{
    const GameplayOverlayContext::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

    if (pLayout == nullptr || !pLayout->visible || toLowerCopy(pLayout->screen) != "dialogue")
    {
        return;
    }

    const std::string normalizedLayoutId = toLowerCopy(layoutId);

    if (normalizedLayoutId == "dialoguenpcportrait"
        || normalizedLayoutId == "dialoguetext"
        || normalizedLayoutId == "dialogueshopoverlayframe")
    {
        return;
    }

    if (!showDialogueTextFrame && isDialogueFrameSubtree(view, layoutId))
    {
        return;
    }

    if (normalizedLayoutId == "dialoguevideoarea" && !showDialogueVideoArea)
    {
        return;
    }

    if (normalizedLayoutId == "dialogueokbutton"
        && view.activeEventDialog().presentation != EventDialogPresentation::Transition)
    {
        return;
    }

    if (normalizedLayoutId == "dialogueeventdialog" && !showEventDialogPanel)
    {
        return;
    }

    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (!shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pLayout->zIndex))
    {
        return;
    }

    std::optional<GameplayOverlayContext::HudTextureHandle> baseTexture;

    if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
    {
        baseTexture = view.ensureHudTextureLoaded(pLayout->primaryAsset);
    }

    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
        layoutId,
        width,
        height,
        pLayout->width > 0.0f
            ? pLayout->width
            : (baseTexture ? static_cast<float>(baseTexture->width) : 0.0f),
        pLayout->height > 0.0f
            ? pLayout->height
            : (baseTexture ? static_cast<float>(baseTexture->height) : 0.0f));

    if (!resolved)
    {
        return;
    }

    if (normalizedLayoutId == "dialoguevideoarea")
    {
        renderDialogueVideoArea(view, resolved->x, resolved->y, resolved->width, resolved->height);
        return;
    }

    const bool isLeftMousePressed = (SDL_GetMouseState(nullptr, nullptr) & SDL_BUTTON_LMASK) != 0;
    const std::string *pAssetName =
        view.resolveInteractiveAssetName(*pLayout, *resolved, dialogMouseX, dialogMouseY, isLeftMousePressed);

    if (pAssetName->empty())
    {
        return;
    }

    const std::optional<GameplayOverlayContext::HudTextureHandle> texture = view.ensureHudTextureLoaded(*pAssetName);

    if (!texture)
    {
        return;
    }

    submitTextureHandleQuad(view, texture->textureHandle, resolved->x, resolved->y, resolved->width, resolved->height);
}

void GameplayDialogueRenderer::renderDialogueLabelById(
    GameplayOverlayContext &view,
    const std::string &layoutId,
    const std::string &label,
    int width,
    int height,
    bool renderAboveHud)
{
    const GameplayOverlayContext::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

    if (pLayout == nullptr || !pLayout->visible || toLowerCopy(pLayout->screen) != "dialogue")
    {
        return;
    }

    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (!shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pLayout->zIndex))
    {
        return;
    }

    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
        layoutId,
        width,
        height,
        pLayout->width,
        pLayout->height);

    if (!resolved)
    {
        return;
    }

    view.renderLayoutLabel(*pLayout, *resolved, label);
}

void GameplayDialogueRenderer::renderDialogueEventPanel(
    GameplayOverlayContext &view,
    int width,
    int height,
    float dialogMouseX,
    float dialogMouseY,
    bool renderAboveHud,
    bool showEventDialogPanel,
    bool isResidentSelectionMode,
    const HouseEntry *pHostHouseEntry,
    const std::optional<std::string> &hoveredHouseServiceTopicText,
    bool suppressServiceTopicsForShopOverlay)
{
    if (!showEventDialogPanel)
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pEventDialogLayout = view.findHudLayoutElement("DialogueEventDialog");
    const GameplayOverlayContext::HudLayoutElement *pNpcPortraitLayout = view.findHudLayoutElement("DialogueNpcPortrait");
    const GameplayOverlayContext::HudLayoutElement *pHouseTitleLayout = view.findHudLayoutElement("DialogueHouseTitle");
    const GameplayOverlayContext::HudLayoutElement *pNpcNameLayout = view.findHudLayoutElement("DialogueNpcName");
    const GameplayOverlayContext::HudLayoutElement *pTopicRowLayout = view.findHudLayoutElement("DialogueTopicRow_1");

    if (pEventDialogLayout == nullptr)
    {
        return;
    }

    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedEventDialog = view.resolveHudLayoutElement(
        "DialogueEventDialog",
        width,
        height,
        pEventDialogLayout->width,
        pEventDialogLayout->height);
    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (!resolvedEventDialog
        || !shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pEventDialogLayout->zIndex))
    {
        return;
    }

    const float panelScale = resolvedEventDialog->scale;
    const float panelPaddingX = 10.0f * panelScale;
    const float panelPaddingY = 10.0f * panelScale;
    const float panelInnerX = resolvedEventDialog->x + panelPaddingX;
    const float panelInnerY = resolvedEventDialog->y + panelPaddingY;
    const float panelInnerWidth = resolvedEventDialog->width - panelPaddingX * 2.0f;
    const float portraitInset = 4.0f * panelScale;
    const float sectionGap = 8.0f * panelScale;
    const float houseTitleToPortraitGap = 2.0f * panelScale;
    float contentY = panelInnerY;
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedPortraitTemplate =
        pNpcPortraitLayout != nullptr
        ? view.resolveHudLayoutElement(
            "DialogueNpcPortrait",
            width,
            height,
            pNpcPortraitLayout->width,
            pNpcPortraitLayout->height)
        : std::nullopt;
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedNpcNameTemplate =
        pNpcNameLayout != nullptr
        ? view.resolveHudLayoutElement(
            "DialogueNpcName",
            width,
            height,
            pNpcNameLayout->width,
            pNpcNameLayout->height)
        : std::nullopt;
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedTopicRowTemplate =
        pTopicRowLayout != nullptr
        ? view.resolveHudLayoutElement(
            "DialogueTopicRow_1",
            width,
            height,
            pTopicRowLayout->width,
            pTopicRowLayout->height)
        : std::nullopt;
    const GameplayOverlayContext::HudLayoutElement *pEffectiveHouseTitleLayout =
        pHouseTitleLayout != nullptr ? pHouseTitleLayout : pNpcNameLayout;
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedHouseTitleTemplate =
        pEffectiveHouseTitleLayout != nullptr
        ? view.resolveHudLayoutElement(
            pEffectiveHouseTitleLayout->id,
            width,
            height,
            pEffectiveHouseTitleLayout->width,
            pEffectiveHouseTitleLayout->height)
        : std::nullopt;
    const float portraitAreaWidth = resolvedPortraitTemplate ? resolvedPortraitTemplate->width : 80.0f * panelScale;
    const float portraitAreaHeight = resolvedPortraitTemplate ? resolvedPortraitTemplate->height : 80.0f * panelScale;
    const float portraitBorderSize = std::min(portraitAreaWidth, portraitAreaHeight);
    const float portraitAreaX = resolvedPortraitTemplate
        ? resolvedPortraitTemplate->x
        : std::round(panelInnerX + (panelInnerWidth - portraitAreaWidth) * 0.5f);
    const float portraitBaseY = resolvedPortraitTemplate ? resolvedPortraitTemplate->y : panelInnerY;
    const float nameWidth = resolvedNpcNameTemplate ? resolvedNpcNameTemplate->width : panelInnerWidth;
    const float nameHeight = resolvedNpcNameTemplate ? resolvedNpcNameTemplate->height : 20.0f * panelScale;
    const float nameX = resolvedNpcNameTemplate ? resolvedNpcNameTemplate->x : panelInnerX;
    const float nameScale = resolvedNpcNameTemplate ? resolvedNpcNameTemplate->scale : panelScale;
    const float nameOffsetY = resolvedNpcNameTemplate && resolvedPortraitTemplate
        ? (resolvedNpcNameTemplate->y - resolvedPortraitTemplate->y)
        : portraitBorderSize + 2.0f * panelScale;

    if (pHostHouseEntry != nullptr && pEffectiveHouseTitleLayout != nullptr)
    {
        GameplayOverlayContext::ResolvedHudLayoutElement resolvedHouseTitle = {};
        resolvedHouseTitle.x = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->x : panelInnerX;
        resolvedHouseTitle.y = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->y : contentY;
        resolvedHouseTitle.width = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->width : panelInnerWidth;
        resolvedHouseTitle.height = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->height : 20.0f * panelScale;
        resolvedHouseTitle.scale = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->scale : panelScale;

        if (shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pEffectiveHouseTitleLayout->zIndex))
        {
            const std::string &houseTitle = !view.activeEventDialog().houseTitle.empty()
                ? view.activeEventDialog().houseTitle
                : pHostHouseEntry->name;
            view.renderLayoutLabel(*pEffectiveHouseTitleLayout, resolvedHouseTitle, houseTitle);
        }

        contentY += resolvedHouseTitle.height + houseTitleToPortraitGap;
    }

    contentY = std::max(contentY, portraitBaseY);

    const auto drawEventNpcCard =
        [&view,
         pNpcNameLayout,
         nameHeight,
         nameOffsetY,
         nameScale,
         nameWidth,
         nameX,
         portraitAreaHeight,
         portraitAreaWidth,
         portraitAreaX,
         portraitBorderSize,
         portraitInset,
         renderAboveHud,
         hudZThreshold](
            float startY,
            const std::string &name,
            uint32_t pictureId,
            EventDialogParticipantVisual participantVisual,
            bool selected) -> float
        {
            const float portraitY = std::round(startY);
            const float portraitX = std::round(portraitAreaX + (portraitAreaWidth - portraitBorderSize) * 0.5f);
            const float portraitBorderY = std::round(portraitY + (portraitAreaHeight - portraitBorderSize) * 0.5f);
            const std::optional<GameplayOverlayContext::HudTextureHandle> portraitBorder =
                view.ensureHudTextureLoaded("evtnpc");

            if (portraitBorder)
            {
                view.submitHudTexturedQuad(*portraitBorder, portraitX, portraitBorderY, portraitBorderSize, portraitBorderSize);
            }

            if (participantVisual == EventDialogParticipantVisual::MapIcon)
            {
                const float innerX = std::round(portraitX + portraitInset);
                const float innerY = std::round(portraitBorderY + portraitInset);
                const float innerSize = std::round(portraitBorderSize - portraitInset * 2.0f);
                const std::optional<GameplayOverlayContext::HudTextureHandle> transitionIcon =
                    view.ensureHudTextureLoaded("Outside");

                if (transitionIcon)
                {
                    const float imageWidth = static_cast<float>(transitionIcon->width);
                    const float imageHeight = static_cast<float>(transitionIcon->height);
                    const float iconScale = std::max(
                        innerSize / std::max(1.0f, imageWidth),
                        innerSize / std::max(1.0f, imageHeight));
                    const float scaledWidth = imageWidth * iconScale;
                    const float scaledHeight = imageHeight * iconScale;
                    float u0 = 0.0f;
                    float v0 = 0.0f;
                    float u1 = 1.0f;
                    float v1 = 1.0f;

                    if (scaledWidth > innerSize)
                    {
                        const float croppedFraction = (scaledWidth - innerSize) / scaledWidth;
                        u0 = croppedFraction * 0.5f;
                        u1 = 1.0f - croppedFraction * 0.5f;
                    }

                    if (scaledHeight > innerSize)
                    {
                        const float croppedFraction = (scaledHeight - innerSize) / scaledHeight;
                        v0 = croppedFraction * 0.5f;
                        v1 = 1.0f - croppedFraction * 0.5f;
                    }

                    submitTextureHandleQuadUv(
                        view,
                        transitionIcon->textureHandle,
                        innerX,
                        innerY,
                        innerSize,
                        innerSize,
                        u0,
                        v0,
                        u1,
                        v1);
                }
                else
                {
                    const std::optional<GameplayOverlayContext::HudTextureHandle> parchment =
                        view.ensureSolidHudTextureLoaded("__dialogue_map_icon_bg__", 0xffcdb07aU);
                    const std::optional<GameplayOverlayContext::HudTextureHandle> lineTexture =
                        view.ensureSolidHudTextureLoaded("__dialogue_map_icon_line__", 0xff5c4228U);

                    if (parchment)
                    {
                        view.submitHudTexturedQuad(*parchment, innerX, innerY, innerSize, innerSize);
                    }

                    if (lineTexture)
                    {
                        view.submitHudTexturedQuad(
                            *lineTexture,
                            innerX + innerSize * 0.18f,
                            innerY + innerSize * 0.58f,
                            innerSize * 0.64f,
                            innerSize * 0.08f);
                        view.submitHudTexturedQuad(
                            *lineTexture,
                            innerX + innerSize * 0.52f,
                            innerY + innerSize * 0.20f,
                            innerSize * 0.08f,
                            innerSize * 0.54f);
                        view.submitHudTexturedQuad(
                            *lineTexture,
                            innerX + innerSize * 0.26f,
                            innerY + innerSize * 0.24f,
                            innerSize * 0.18f,
                            innerSize * 0.18f);
                    }
                }
            }
            else if (pictureId > 0)
            {
                char textureName[16] = {};
                std::snprintf(textureName, sizeof(textureName), "npc%04u", pictureId);
                const std::optional<GameplayOverlayContext::HudTextureHandle> portraitTexture =
                    view.ensureHudTextureLoaded(textureName);

                if (portraitTexture)
                {
                    const float imageWidth = static_cast<float>(portraitTexture->width);
                    const float imageHeight = static_cast<float>(portraitTexture->height);
                    const float targetSize = portraitBorderSize - portraitInset * 2.0f;
                    const float portraitScale = std::max(
                        targetSize / std::max(1.0f, imageWidth),
                        targetSize / std::max(1.0f, imageHeight));
                    const float scaledWidth = imageWidth * portraitScale;
                    const float scaledHeight = imageHeight * portraitScale;
                    const float innerX = std::round(portraitX + portraitInset);
                    const float innerY = std::round(portraitBorderY + portraitInset);
                    const float drawWidth = std::round(targetSize);
                    const float drawHeight = std::round(targetSize);
                    float u0 = 0.0f;
                    float v0 = 0.0f;
                    float u1 = 1.0f;
                    float v1 = 1.0f;

                    if (scaledWidth > targetSize)
                    {
                        const float croppedFraction = (scaledWidth - targetSize) / scaledWidth;
                        u0 = croppedFraction * 0.5f;
                        u1 = 1.0f - croppedFraction * 0.5f;
                    }

                    if (scaledHeight > targetSize)
                    {
                        const float croppedFraction = (scaledHeight - targetSize) / scaledHeight;
                        v0 = croppedFraction * 0.5f;
                        v1 = 1.0f - croppedFraction * 0.5f;
                    }

                    submitTextureHandleQuadUv(
                        view,
                        portraitTexture->textureHandle,
                        innerX,
                        innerY,
                        drawWidth,
                        drawHeight,
                        u0,
                        v0,
                        u1,
                        v1);
                }
            }

            if (selected)
            {
                const std::optional<GameplayOverlayContext::HudTextureHandle> highlight =
                    view.ensureSolidHudTextureLoaded("__dialogue_event_npc_highlight__", 0x40ffffaaU);

                if (highlight)
                {
                    view.submitHudTexturedQuad(*highlight, portraitX, portraitBorderY, portraitBorderSize, portraitBorderSize);
                }
            }

            float nextY = portraitY + portraitAreaHeight;

            if (pNpcNameLayout != nullptr
                && shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pNpcNameLayout->zIndex))
            {
                GameplayOverlayContext::ResolvedHudLayoutElement resolvedName = {};
                resolvedName.x = nameX;
                resolvedName.y = portraitY + nameOffsetY;
                resolvedName.width = nameWidth;
                resolvedName.height = nameHeight;
                resolvedName.scale = nameScale;
                view.renderLayoutLabel(*pNpcNameLayout, resolvedName, name);
                nextY = resolvedName.y + resolvedName.height;
            }

            return nextY;
        };

    if (isResidentSelectionMode)
    {
        for (size_t actionIndex = 0; actionIndex < view.activeEventDialog().actions.size(); ++actionIndex)
        {
            const EventDialogAction &action = view.activeEventDialog().actions[actionIndex];
            const NpcEntry *pNpc = view.npcDialogTable() ? view.npcDialogTable()->getNpc(action.id) : nullptr;
            const uint32_t pictureId = pNpc != nullptr ? pNpc->pictureId : 0;
            contentY = drawEventNpcCard(
                contentY,
                action.label,
                pictureId,
                EventDialogParticipantVisual::Portrait,
                false);
            contentY += sectionGap;
        }
    }
    else
    {
        uint32_t pictureId = view.activeEventDialog().participantPictureId;

        if (pictureId == 0 && view.activeEventDialog().participantVisual == EventDialogParticipantVisual::Portrait)
        {
            const NpcEntry *pNpc =
                view.npcDialogTable() ? view.npcDialogTable()->getNpc(view.activeEventDialog().sourceId) : nullptr;
            pictureId = pNpc != nullptr
                ? pNpc->pictureId
                : (pHostHouseEntry != nullptr ? pHostHouseEntry->proprietorPictureId : 0);
        }

        contentY = drawEventNpcCard(
            contentY,
            view.activeEventDialog().title,
            pictureId,
            view.activeEventDialog().participantVisual,
            false);
        contentY += sectionGap;

        if (view.activeEventDialog().presentation != EventDialogPresentation::Transition
            && pTopicRowLayout != nullptr
            && ((!suppressServiceTopicsForShopOverlay && !view.activeEventDialog().actions.empty())
                || hoveredHouseServiceTopicText.has_value()))
        {
            const std::optional<GameplayOverlayContext::HudFontHandle> topicFont =
                view.findHudFont(pTopicRowLayout->fontName);
            const float topicFontScale = snappedHudFontScale(
                resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale);
            const float topicLineHeight = topicFont
                ? static_cast<float>(topicFont->fontHeight) * topicFontScale
                : 20.0f * panelScale;
            const float topicWrapWidth = 140.0f * (resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale);
            const float topicTextWidthScaled = std::max(
                0.0f,
                std::min(
                    resolvedTopicRowTemplate ? resolvedTopicRowTemplate->width : panelInnerWidth,
                    topicWrapWidth)
                        - std::abs(pTopicRowLayout->textPadX * topicFontScale) * 2.0f
                        - 4.0f * topicFontScale);
            const float topicTextWidth = std::max(0.0f, topicTextWidthScaled / std::max(1.0f, topicFontScale));
            const float rowGap = 4.0f * panelScale;
            const bool showHoveredShopTopic = hoveredHouseServiceTopicText.has_value();
            const size_t visibleActionCount =
                showHoveredShopTopic
                ? 1
                : (suppressServiceTopicsForShopOverlay ? 0 : std::min<size_t>(view.activeEventDialog().actions.size(), 5));
            const float availableTop = contentY;
            const float availableHeight =
                resolvedEventDialog->y + resolvedEventDialog->height - panelPaddingY - availableTop;
            std::vector<std::vector<std::string>> wrappedActionLabels;
            std::vector<float> actionRowHeights;
            std::vector<float> actionPressHeights;
            wrappedActionLabels.reserve(visibleActionCount);
            actionRowHeights.reserve(visibleActionCount);
            actionPressHeights.reserve(visibleActionCount);

            for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
            {
                std::string label = showHoveredShopTopic
                    ? *hoveredHouseServiceTopicText
                    : view.activeEventDialog().actions[actionIndex].label;

                if (!showHoveredShopTopic
                    && !view.activeEventDialog().actions[actionIndex].enabled
                    && !view.activeEventDialog().actions[actionIndex].disabledReason.empty())
                {
                    label += " [disabled]";
                }

                std::vector<std::string> wrappedLines = topicFont
                    ? view.wrapHudTextToWidth(*topicFont, label, topicTextWidth)
                    : std::vector<std::string>{label};

                if (wrappedLines.empty())
                {
                    wrappedLines.push_back(label);
                }

                const float minimumRowHeight = resolvedTopicRowTemplate
                    ? resolvedTopicRowTemplate->height
                    : pTopicRowLayout->height * panelScale;
                const float wrappedRowHeight = static_cast<float>(wrappedLines.size()) * topicLineHeight;
                wrappedActionLabels.push_back(std::move(wrappedLines));
                actionRowHeights.push_back(std::max(minimumRowHeight, wrappedRowHeight));
                actionPressHeights.push_back(wrappedRowHeight);
            }

            float totalHeight = 0.0f;

            for (size_t actionIndex = 0; actionIndex < actionRowHeights.size(); ++actionIndex)
            {
                totalHeight += actionRowHeights[actionIndex];

                if (actionIndex + 1 < actionRowHeights.size())
                {
                    totalHeight += rowGap;
                }
            }

            const float topicListCenterOffsetY = 8.0f * panelScale;
            float rowY = availableTop + std::max(0.0f, (availableHeight - totalHeight) * 0.5f) - topicListCenterOffsetY;

            for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
            {
                GameplayOverlayContext::ResolvedHudLayoutElement resolvedRow = {};
                resolvedRow.x = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->x : panelInnerX;
                resolvedRow.y = rowY;
                resolvedRow.width = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->width : panelInnerWidth;
                resolvedRow.height = actionRowHeights[actionIndex];
                resolvedRow.scale = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale;

                if (shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pTopicRowLayout->zIndex))
                {
                    const float pressAreaInsetY = 2.0f * panelScale;
                    const float pressAreaHeight =
                        std::min(
                            resolvedRow.height,
                            std::max(topicLineHeight, actionPressHeights[actionIndex]) + pressAreaInsetY * 2.0f);
                    const float pressAreaY = resolvedRow.y + (resolvedRow.height - pressAreaHeight) * 0.5f;
                    const bool isHovered = !showHoveredShopTopic
                        && dialogMouseX >= resolvedRow.x
                        && dialogMouseX < resolvedRow.x + resolvedRow.width
                        && dialogMouseY >= pressAreaY
                        && dialogMouseY < pressAreaY + pressAreaHeight;

                    if (topicFont)
                    {
                        float lineY = pressAreaY;
                        GameplayOverlayContext::HudLayoutElement hoveredTopicRowLayout = *pTopicRowLayout;

                        if (isHovered)
                        {
                            hoveredTopicRowLayout.textColorAbgr = HoveredDialogueTopicTextColorAbgr;
                        }

                        for (const std::string &wrappedLine : wrappedActionLabels[actionIndex])
                        {
                            GameplayOverlayContext::ResolvedHudLayoutElement resolvedLine = resolvedRow;
                            resolvedLine.y = lineY;
                            resolvedLine.height = topicLineHeight;
                            view.renderLayoutLabel(
                                isHovered ? hoveredTopicRowLayout : *pTopicRowLayout,
                                resolvedLine,
                                wrappedLine);
                            lineY += topicLineHeight;
                        }
                    }
                    else
                    {
                        GameplayOverlayContext::HudLayoutElement hoveredTopicRowLayout = *pTopicRowLayout;

                        if (isHovered)
                        {
                            hoveredTopicRowLayout.textColorAbgr = HoveredDialogueTopicTextColorAbgr;
                        }

                        view.renderLayoutLabel(
                            isHovered ? hoveredTopicRowLayout : *pTopicRowLayout,
                            resolvedRow,
                            showHoveredShopTopic
                                ? *hoveredHouseServiceTopicText
                                : view.activeEventDialog().actions[actionIndex].label);
                    }
                }

                rowY += actionRowHeights[actionIndex] + rowGap;
            }
        }
    }
}

void GameplayDialogueRenderer::renderDialogueBodyText(
    GameplayOverlayContext &view,
    int width,
    int height,
    bool renderAboveHud,
    const std::vector<std::string> &dialogueBodyLines)
{
    if (dialogueBodyLines.empty())
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pDialogueTextLayout = view.findHudLayoutElement("DialogueText");

    if (pDialogueTextLayout == nullptr || toLowerCopy(pDialogueTextLayout->screen) != "dialogue")
    {
        return;
    }

    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedText = view.resolveHudLayoutElement(
        "DialogueText",
        width,
        height,
        pDialogueTextLayout->width,
        pDialogueTextLayout->height);
    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (!resolvedText
        || !shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pDialogueTextLayout->zIndex))
    {
        return;
    }

    const std::optional<GameplayOverlayContext::HudFontHandle> font =
        view.findHudFont(pDialogueTextLayout->fontName);

    if (!font)
    {
        return;
    }

    static constexpr float DialogueTextTopInset = 2.0f;
    static constexpr float DialogueTextRightInset = 6.0f;
    const float fontScale = snappedHudFontScale(resolvedText->scale);
    bgfx::TextureHandle coloredMainTextureHandle =
        view.ensureHudFontMainTextureColor(*font, pDialogueTextLayout->textColorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = font->mainTextureHandle;
    }

    const float lineHeight = static_cast<float>(font->fontHeight) * fontScale;
    float textX = resolvedText->x + pDialogueTextLayout->textPadX * fontScale;
    float textY = resolvedText->y + (pDialogueTextLayout->textPadY + DialogueTextTopInset) * fontScale;
    textX = std::round(textX);
    textY = std::round(textY);
    const float textWrapWidth = std::max(
        0.0f,
        (resolvedText->width
            - std::abs(pDialogueTextLayout->textPadX * fontScale) * 2.0f
            - DialogueTextRightInset * fontScale)
            / std::max(1.0f, fontScale));
    const size_t maxVisibleLines = std::max<size_t>(
        1,
        static_cast<size_t>(resolvedText->height / std::max(1.0f, lineHeight)));
    size_t visibleLineIndex = 0;

    for (const std::string &sourceLine : dialogueBodyLines)
    {
        const std::vector<std::string> wrappedLines = view.wrapHudTextToWidth(*font, sourceLine, textWrapWidth);

        for (const std::string &wrappedLine : wrappedLines)
        {
            if (visibleLineIndex >= maxVisibleLines)
            {
                break;
            }

            view.renderHudFontLayer(*font, font->shadowTextureHandle, wrappedLine, textX, textY, fontScale);
            view.renderHudFontLayer(*font, coloredMainTextureHandle, wrappedLine, textX, textY, fontScale);
            textY += lineHeight;
            ++visibleLineIndex;
        }

        if (visibleLineIndex >= maxVisibleLines)
        {
            break;
        }
    }
}

void GameplayDialogueRenderer::submitTextureHandleQuad(
    GameplayOverlayContext &view,
    bgfx::TextureHandle textureHandle,
    float x,
    float y,
    float quadWidth,
    float quadHeight)
{
    view.submitWorldTextureQuad(textureHandle, x, y, quadWidth, quadHeight, 0.0f, 0.0f, 1.0f, 1.0f);
}

void GameplayDialogueRenderer::submitTextureHandleQuadUv(
    GameplayOverlayContext &view,
    bgfx::TextureHandle textureHandle,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    float u0,
    float v0,
    float u1,
    float v1)
{
    view.submitWorldTextureQuad(textureHandle, x, y, quadWidth, quadHeight, u0, v0, u1, v1);
}

void GameplayDialogueRenderer::renderDialogueVideoArea(
    GameplayOverlayContext &view,
    float x,
    float y,
    float quadWidth,
    float quadHeight)
{
    if (view.renderHouseVideoFrame(x, y, quadWidth, quadHeight))
    {
        return;
    }

    const std::optional<GameplayOverlayContext::HudTextureHandle> videoFillTexture =
        view.ensureSolidHudTextureLoaded("__dialogue_video_area_fill__", 0xa0181818u);
    const std::optional<GameplayOverlayContext::HudTextureHandle> videoBorderTexture =
        view.ensureSolidHudTextureLoaded("__dialogue_video_area_border__", 0xff505050u);

    if (videoFillTexture)
    {
        view.submitHudTexturedQuad(
            *videoFillTexture,
            x,
            y,
            quadWidth,
            quadHeight);
    }

    if (!videoBorderTexture)
    {
        return;
    }

    static constexpr float BorderThickness = 2.0f;
    view.submitHudTexturedQuad(
        *videoBorderTexture,
        x,
        y,
        quadWidth,
        BorderThickness);
    view.submitHudTexturedQuad(
        *videoBorderTexture,
        x,
        y + quadHeight - BorderThickness,
        quadWidth,
        BorderThickness);
    view.submitHudTexturedQuad(
        *videoBorderTexture,
        x,
        y,
        BorderThickness,
        quadHeight);
    view.submitHudTexturedQuad(
        *videoBorderTexture,
        x + quadWidth - BorderThickness,
        y,
        BorderThickness,
        quadHeight);
}
} // namespace OpenYAMM::Game
