#include "game/gameplay/GameplayOverlayInputController.h"

#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/StringUtils.h"
#include "game/ui/GameplayOverlayContext.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float HudFontIntegerSnapThreshold = 0.1f;

struct HudPointerState
{
    float x = 0.0f;
    float y = 0.0f;
    bool leftButtonPressed = false;
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

template <typename Target, typename ResolveTargetFn, typename ActivateTargetFn>
void handlePointerClickRelease(
    const HudPointerState &pointerState,
    bool &clickLatch,
    Target &pressedTarget,
    const Target &noneTarget,
    ResolveTargetFn resolveTargetFn,
    ActivateTargetFn activateTargetFn)
{
    if (pointerState.leftButtonPressed)
    {
        if (!clickLatch)
        {
            pressedTarget = resolveTargetFn(pointerState.x, pointerState.y);
            clickLatch = true;
        }
    }
    else if (clickLatch)
    {
        const Target currentTarget = resolveTargetFn(pointerState.x, pointerState.y);

        if (currentTarget == pressedTarget)
        {
            activateTargetFn(currentTarget);
        }

        clickLatch = false;
        pressedTarget = noneTarget;
    }
    else
    {
        pressedTarget = noneTarget;
    }
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

bool isHouseType(const HouseEntry &houseEntry, const char *pTypeName)
{
    return houseEntry.type == pTypeName;
}

uint32_t currentDialogueHostHouseId(const EventRuntimeState *pEventRuntimeState)
{
    return pEventRuntimeState != nullptr ? pEventRuntimeState->dialogueState.hostHouseId : 0;
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
    rect.x = std::round(gridMetrics.x + static_cast<float>(item.gridX) * gridMetrics.cellWidth + offsetX);
    rect.y = std::round(gridMetrics.y + static_cast<float>(item.gridY) * gridMetrics.cellHeight + offsetY);
    rect.width = textureWidth;
    rect.height = textureHeight;
    return rect;
}

std::optional<std::pair<int, int>> computeHeldInventoryPlacement(
    const InventoryGridMetrics &gridMetrics,
    uint8_t itemWidthCells,
    uint8_t itemHeightCells,
    float itemWidthPixels,
    float itemHeightPixels,
    float drawX,
    float drawY)
{
    const float centerX = drawX + itemWidthPixels * 0.5f;
    const float centerY = drawY + itemHeightPixels * 0.5f;
    const float localX = centerX - gridMetrics.x;
    const float localY = centerY - gridMetrics.y;

    if (gridMetrics.cellWidth <= 0.0f || gridMetrics.cellHeight <= 0.0f)
    {
        return std::nullopt;
    }

    const int centerCellX = static_cast<int>(std::floor(localX / gridMetrics.cellWidth));
    const int centerCellY = static_cast<int>(std::floor(localY / gridMetrics.cellHeight));
    const int itemWidth = std::max<int>(1, itemWidthCells);
    const int itemHeight = std::max<int>(1, itemHeightCells);
    const int targetGridX = centerCellX - itemWidth / 2;
    const int targetGridY = centerCellY - itemHeight / 2;

    return std::pair<int, int>{targetGridX, targetGridY};
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
            result.y = std::round(slotY + (slotHeight - itemHeight) * 0.5f);
            break;
    }

    return result;
}
} // namespace

void GameplayOverlayInputController::handleDialogueOverlayInput(
    GameplayOverlayContext &view,
    const bool *pKeyboardState,
    int screenWidth,
    int screenHeight,
    bool isResidentSelectionMode)
{
    if (view.partyRuntime() != nullptr)
    {
        static constexpr SDL_Scancode PartySelectScancodes[5] = {
            SDL_SCANCODE_1,
            SDL_SCANCODE_2,
            SDL_SCANCODE_3,
            SDL_SCANCODE_4,
            SDL_SCANCODE_5,
        };

        for (size_t memberIndex = 0; memberIndex < std::size(PartySelectScancodes); ++memberIndex)
        {
            if (pKeyboardState[PartySelectScancodes[memberIndex]])
            {
                if (!view.eventDialogPartySelectLatches()[memberIndex])
                {
                    view.trySelectPartyMember(memberIndex, false);
                    view.eventDialogPartySelectLatches()[memberIndex] = true;
                }
            }
            else
            {
                view.eventDialogPartySelectLatches()[memberIndex] = false;
            }
        }
    }
    else
    {
        view.eventDialogPartySelectLatches().fill(false);
    }

    if (view.houseBankState().inputActive())
    {
        static constexpr SDL_Scancode DigitScancodes[10] = {
            SDL_SCANCODE_0,
            SDL_SCANCODE_1,
            SDL_SCANCODE_2,
            SDL_SCANCODE_3,
            SDL_SCANCODE_4,
            SDL_SCANCODE_5,
            SDL_SCANCODE_6,
            SDL_SCANCODE_7,
            SDL_SCANCODE_8,
            SDL_SCANCODE_9,
        };
        static constexpr SDL_Scancode KeypadDigitScancodes[10] = {
            SDL_SCANCODE_KP_0,
            SDL_SCANCODE_KP_1,
            SDL_SCANCODE_KP_2,
            SDL_SCANCODE_KP_3,
            SDL_SCANCODE_KP_4,
            SDL_SCANCODE_KP_5,
            SDL_SCANCODE_KP_6,
            SDL_SCANCODE_KP_7,
            SDL_SCANCODE_KP_8,
            SDL_SCANCODE_KP_9,
        };

        for (size_t digit = 0; digit < view.houseBankDigitLatches().size(); ++digit)
        {
            const bool pressed = pKeyboardState[DigitScancodes[digit]]
                || pKeyboardState[KeypadDigitScancodes[digit]];

            if (pressed)
            {
                if (!view.houseBankDigitLatches()[digit] && view.houseBankState().inputText.size() < 10)
                {
                    view.houseBankState().inputText.push_back(static_cast<char>('0' + digit));
                }

                view.houseBankDigitLatches()[digit] = true;
            }
            else
            {
                view.houseBankDigitLatches()[digit] = false;
            }
        }

        const bool backspacePressed = pKeyboardState[SDL_SCANCODE_BACKSPACE];

        if (backspacePressed)
        {
            if (!view.houseBankBackspaceLatch() && !view.houseBankState().inputText.empty())
            {
                view.houseBankState().inputText.pop_back();
            }

            view.houseBankBackspaceLatch() = true;
        }
        else
        {
            view.houseBankBackspaceLatch() = false;
        }

        const bool confirmPressed = pKeyboardState[SDL_SCANCODE_RETURN] || pKeyboardState[SDL_SCANCODE_KP_ENTER];

        if (confirmPressed)
        {
            if (!view.houseBankConfirmLatch())
            {
                view.confirmHouseBankInput();
                view.houseBankConfirmLatch() = true;
            }
        }
        else
        {
            view.houseBankConfirmLatch() = false;
        }

        view.refreshHouseBankInputDialog();

        float dialogMouseX = 0.0f;
        float dialogMouseY = 0.0f;
        const SDL_MouseButtonFlags dialogMouseButtons = SDL_GetMouseState(&dialogMouseX, &dialogMouseY);
        const HudPointerState pointerState = {
            dialogMouseX,
            dialogMouseY,
            (dialogMouseButtons & SDL_BUTTON_LMASK) != 0
        };
        const GameplayDialoguePointerTarget noneDialogueTarget = {};
        const auto findDialogueCloseTarget =
            [&view, screenWidth, screenHeight](float mouseX, float mouseY) -> GameplayDialoguePointerTarget
            {
                const GameplayOverlayContext::HudLayoutElement *pGoodbyeLayout =
                    view.findHudLayoutElement("DialogueGoodbyeButton");
                const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedGoodbye =
                    pGoodbyeLayout != nullptr
                    ? view.resolveHudLayoutElement(
                        "DialogueGoodbyeButton",
                        screenWidth,
                        screenHeight,
                        pGoodbyeLayout->width,
                        pGoodbyeLayout->height)
                    : std::nullopt;

                if (resolvedGoodbye
                    && mouseX >= resolvedGoodbye->x
                    && mouseX < resolvedGoodbye->x + resolvedGoodbye->width
                    && mouseY >= resolvedGoodbye->y
                    && mouseY < resolvedGoodbye->y + resolvedGoodbye->height)
                {
                    return {GameplayDialoguePointerTargetType::CloseButton, 0};
                }

                return {};
            };

        handlePointerClickRelease(
            pointerState,
            view.dialogueClickLatch(),
            view.dialoguePressedTarget(),
            noneDialogueTarget,
            findDialogueCloseTarget,
            [&view](const GameplayDialoguePointerTarget &target)
            {
                if (target.type == GameplayDialoguePointerTargetType::CloseButton)
                {
                    view.handleDialogueCloseRequest();
                }
            });

        const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_E];

        if (closePressed)
        {
            if (!view.closeOverlayLatch())
            {
                view.handleDialogueCloseRequest();
                view.closeOverlayLatch() = true;
            }
        }
        else
        {
            view.closeOverlayLatch() = false;
        }

        return;
    }

    if (!view.activeEventDialog().actions.empty() && !isResidentSelectionMode)
    {
        if (pKeyboardState[SDL_SCANCODE_UP])
        {
            if (!view.eventDialogSelectUpLatch())
            {
                view.eventDialogSelectionIndex() = view.eventDialogSelectionIndex() == 0
                    ? (view.activeEventDialog().actions.size() - 1)
                    : (view.eventDialogSelectionIndex() - 1);
                view.eventDialogSelectUpLatch() = true;
            }
        }
        else
        {
            view.eventDialogSelectUpLatch() = false;
        }

        if (pKeyboardState[SDL_SCANCODE_DOWN])
        {
            if (!view.eventDialogSelectDownLatch())
            {
                view.eventDialogSelectionIndex() =
                    (view.eventDialogSelectionIndex() + 1) % view.activeEventDialog().actions.size();
                view.eventDialogSelectDownLatch() = true;
            }
        }
        else
        {
            view.eventDialogSelectDownLatch() = false;
        }
    }
    else
    {
        view.eventDialogSelectUpLatch() = false;
        view.eventDialogSelectDownLatch() = false;
    }

    const bool acceptPressed = pKeyboardState[SDL_SCANCODE_RETURN] || pKeyboardState[SDL_SCANCODE_SPACE];

    if (acceptPressed && !isResidentSelectionMode)
    {
        if (!view.eventDialogAcceptLatch())
        {
            if (view.activeEventDialog().actions.empty())
            {
                view.handleDialogueCloseRequest();
            }
            else
            {
                view.executeActiveDialogAction();
            }

            view.eventDialogAcceptLatch() = true;
        }
    }
    else
    {
        view.eventDialogAcceptLatch() = false;
    }

    float dialogMouseX = 0.0f;
    float dialogMouseY = 0.0f;
    const SDL_MouseButtonFlags dialogMouseButtons = SDL_GetMouseState(&dialogMouseX, &dialogMouseY);
    const bool isLeftMousePressed = (dialogMouseButtons & SDL_BUTTON_LMASK) != 0;
    const EventRuntimeState *pDialogueEventRuntimeState =
        view.worldRuntime() != nullptr ? view.worldRuntime()->eventRuntimeState() : nullptr;
    const HouseEntry *pDialogueHouseEntry =
        (currentDialogueHostHouseId(pDialogueEventRuntimeState) != 0 && view.houseTable().has_value())
        ? view.houseTable()->get(currentDialogueHostHouseId(pDialogueEventRuntimeState))
        : nullptr;

    if (view.houseShopOverlay().active
        && pDialogueHouseEntry != nullptr
        && view.partyRuntime() != nullptr
        && view.worldRuntime() != nullptr
        && view.itemTable() != nullptr)
    {
        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedFrame =
            view.resolveHouseShopOverlayFrame(screenWidth, screenHeight);
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
                break;
        }

        if (resolvedFrame && stockMode)
        {
            Party &party = view.partyRuntime()->party();
            const std::vector<InventoryItem> &stock = HouseServiceRuntime::ensureStock(
                party,
                *view.itemTable(),
                *view.standardItemEnchantTable(),
                *view.specialItemEnchantTable(),
                *pDialogueHouseEntry,
                view.worldRuntime()->gameMinutes(),
                *stockMode);
            const size_t slotCount = HouseServiceRuntime::slotCountForStockMode(*pDialogueHouseEntry, *stockMode);
            const HouseShopVisualLayout overlayLayout = buildHouseShopVisualLayout(
                *pDialogueHouseEntry,
                view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpellbooks);
            const auto resolveHoveredSlotIndex =
                [&view, &stock, slotCount, resolvedFrame, &overlayLayout](float mouseX, float mouseY) -> size_t
                {
                    for (size_t slotIndex = 0;
                         slotIndex < slotCount && slotIndex < stock.size() && slotIndex < overlayLayout.slots.size();
                         ++slotIndex)
                    {
                        const InventoryItem &item = stock[slotIndex];

                        if (item.objectDescriptionId == 0 || view.itemTable() == nullptr)
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

                        if (mouseX >= drawRect.x
                            && mouseX < drawRect.x + drawRect.width
                            && mouseY >= drawRect.y
                            && mouseY < drawRect.y + drawRect.height)
                        {
                            return slotIndex;
                        }
                    }

                    return std::numeric_limits<size_t>::max();
                };
            const HudPointerState houseShopPointerState = {
                dialogMouseX,
                dialogMouseY,
                isLeftMousePressed
            };

            handlePointerClickRelease(
                houseShopPointerState,
                view.houseShopClickLatch(),
                view.houseShopPressedSlotIndex(),
                std::numeric_limits<size_t>::max(),
                resolveHoveredSlotIndex,
                [&view, pDialogueHouseEntry, stockMode](size_t slotIndex)
                {
                    if (slotIndex == std::numeric_limits<size_t>::max()
                        || view.partyRuntime() == nullptr
                        || view.itemTable() == nullptr
                        || view.worldRuntime() == nullptr
                        || !stockMode)
                    {
                        return;
                    }

                    std::string statusText;
                    HouseServiceRuntime::tryBuyStockItem(
                        view.partyRuntime()->party(),
                        *view.itemTable(),
                        *view.standardItemEnchantTable(),
                        *view.specialItemEnchantTable(),
                        *pDialogueHouseEntry,
                        view.worldRuntime()->gameMinutes(),
                        *stockMode,
                        slotIndex,
                        statusText);

                    if (!statusText.empty())
                    {
                        view.setStatusBarEvent(statusText);
                    }
                });
        }
    }

    if (view.inventoryNestedOverlay().active
        && (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
        && pDialogueHouseEntry != nullptr
        && view.partyRuntime() != nullptr)
    {
        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedInventoryGrid =
            view.resolveInventoryNestedOverlayGridArea(screenWidth, screenHeight);

        if (resolvedInventoryGrid
            && isLeftMousePressed
            && !view.inventoryNestedOverlayItemClickLatch()
            && dialogMouseX >= resolvedInventoryGrid->x
            && dialogMouseX < resolvedInventoryGrid->x + resolvedInventoryGrid->width
            && dialogMouseY >= resolvedInventoryGrid->y
            && dialogMouseY < resolvedInventoryGrid->y + resolvedInventoryGrid->height)
        {
            const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                resolvedInventoryGrid->x,
                resolvedInventoryGrid->y,
                resolvedInventoryGrid->width,
                resolvedInventoryGrid->height,
                resolvedInventoryGrid->scale);
            const uint8_t gridX = static_cast<uint8_t>(std::clamp(
                static_cast<int>((dialogMouseX - resolvedInventoryGrid->x) / gridMetrics.cellWidth),
                0,
                Character::InventoryWidth - 1));
            const uint8_t gridY = static_cast<uint8_t>(std::clamp(
                static_cast<int>((dialogMouseY - resolvedInventoryGrid->y) / gridMetrics.cellHeight),
                0,
                Character::InventoryHeight - 1));
            std::string statusText;
            HouseServiceRuntime::ShopItemServiceResult serviceResult =
                HouseServiceRuntime::ShopItemServiceResult::None;

            if (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell)
            {
                HouseServiceRuntime::trySellInventoryItem(
                    view.partyRuntime()->party(),
                    *view.itemTable(),
                    *view.standardItemEnchantTable(),
                    *view.specialItemEnchantTable(),
                    *pDialogueHouseEntry,
                    view.partyRuntime()->party().activeMemberIndex(),
                    gridX,
                    gridY,
                    statusText,
                    &serviceResult);
            }
            else if (view.inventoryNestedOverlay().mode
                == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify)
            {
                HouseServiceRuntime::tryIdentifyInventoryItem(
                    view.partyRuntime()->party(),
                    *view.itemTable(),
                    *view.standardItemEnchantTable(),
                    *view.specialItemEnchantTable(),
                    *pDialogueHouseEntry,
                    view.partyRuntime()->party().activeMemberIndex(),
                    gridX,
                    gridY,
                    statusText,
                    &serviceResult);
            }
            else if (view.inventoryNestedOverlay().mode
                == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
            {
                HouseServiceRuntime::tryRepairInventoryItem(
                    view.partyRuntime()->party(),
                    *view.itemTable(),
                    *view.standardItemEnchantTable(),
                    *view.specialItemEnchantTable(),
                    *pDialogueHouseEntry,
                    view.partyRuntime()->party().activeMemberIndex(),
                    gridX,
                    gridY,
                    statusText,
                    &serviceResult);
            }

            const size_t activeMemberIndex = view.partyRuntime()->party().activeMemberIndex();

            if (serviceResult == HouseServiceRuntime::ShopItemServiceResult::WrongShop)
            {
                if (view.audioSystem() != nullptr)
                {
                    view.audioSystem()->playCommonSound(
                        SoundId::Error,
                        GameAudioSystem::PlaybackGroup::Ui);
                }

                view.playSpeechReaction(activeMemberIndex, SpeechId::WrongShop, true);
            }
            else if (serviceResult == HouseServiceRuntime::ShopItemServiceResult::AlreadyIdentified
                || serviceResult == HouseServiceRuntime::ShopItemServiceResult::NothingToRepair)
            {
                view.playSpeechReaction(activeMemberIndex, SpeechId::AlreadyIdentified, true);
            }
            else if (serviceResult == HouseServiceRuntime::ShopItemServiceResult::NotEnoughGold)
            {
                if (view.audioSystem() != nullptr)
                {
                    const std::optional<uint32_t> soundId =
                        deriveHouseSoundId(*pDialogueHouseEntry, HouseSoundType::GeneralNotEnoughGold);

                    if (soundId.has_value())
                    {
                        view.audioSystem()->playSound(
                            *soundId,
                            GameAudioSystem::PlaybackGroup::HouseSpeech);
                    }
                }
            }
            else if (serviceResult == HouseServiceRuntime::ShopItemServiceResult::Success)
            {
                if (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell)
                {
                    view.playSpeechReaction(activeMemberIndex, SpeechId::ItemSold, true);
                }
                else if (view.inventoryNestedOverlay().mode
                    == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify)
                {
                    view.playSpeechReaction(activeMemberIndex, SpeechId::ShopIdentify, true);
                }
                else if (view.inventoryNestedOverlay().mode
                    == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
                {
                    view.playSpeechReaction(activeMemberIndex, SpeechId::ShopRepair, true);
                }
            }

            if (!statusText.empty())
            {
                view.setStatusBarEvent(statusText);
            }

            view.inventoryNestedOverlayItemClickLatch() = true;
        }
        else if (!isLeftMousePressed)
        {
            view.inventoryNestedOverlayItemClickLatch() = false;
        }
    }

    const auto findDialoguePointerTarget =
        [&view, isResidentSelectionMode, screenWidth, screenHeight](
            float mouseX,
            float mouseY) -> GameplayDialoguePointerTarget
        {
            if (screenWidth <= 0 || screenHeight <= 0)
            {
                return {};
            }

            const EventRuntimeState *pEventRuntimeState =
                view.worldRuntime() != nullptr ? view.worldRuntime()->eventRuntimeState() : nullptr;
            const HouseEntry *pHostHouseEntry =
                (currentDialogueHostHouseId(pEventRuntimeState) != 0 && view.houseTable().has_value())
                ? view.houseTable()->get(currentDialogueHostHouseId(pEventRuntimeState))
                : nullptr;
            const bool showEventDialogPanel =
                isResidentSelectionMode || !view.activeEventDialog().actions.empty() || pHostHouseEntry != nullptr;

            if (isResidentSelectionMode)
            {
                const GameplayOverlayContext::HudLayoutElement *pEventDialogLayout =
                    view.findHudLayoutElement("DialogueEventDialog");
                const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedEventDialog =
                    showEventDialogPanel && pEventDialogLayout != nullptr
                    ? view.resolveHudLayoutElement(
                        "DialogueEventDialog",
                        screenWidth,
                        screenHeight,
                        pEventDialogLayout->width,
                        pEventDialogLayout->height)
                    : std::nullopt;

                if (resolvedEventDialog)
                {
                    const float panelScale = resolvedEventDialog->scale;
                    const float panelPaddingX = 10.0f * panelScale;
                    const float panelPaddingY = 10.0f * panelScale;
                    const float panelInnerX = resolvedEventDialog->x + panelPaddingX;
                    const float panelInnerWidth = resolvedEventDialog->width - panelPaddingX * 2.0f;
                    const float portraitBorderSize = 80.0f * panelScale;
                    const float sectionGap = 8.0f * panelScale;
                    float contentY = resolvedEventDialog->y + panelPaddingY;

                    if (pHostHouseEntry != nullptr)
                    {
                        contentY += 20.0f * panelScale + sectionGap;
                    }

                    for (size_t actionIndex = 0; actionIndex < view.activeEventDialog().actions.size(); ++actionIndex)
                    {
                        const float portraitX =
                            std::round(panelInnerX + (panelInnerWidth - portraitBorderSize) * 0.5f);
                        const float portraitY = std::round(contentY);

                        if (mouseX >= portraitX
                            && mouseX < portraitX + portraitBorderSize
                            && mouseY >= portraitY
                            && mouseY < portraitY + portraitBorderSize)
                        {
                            return {GameplayDialoguePointerTargetType::Action, actionIndex};
                        }

                        contentY += portraitBorderSize + 20.0f * panelScale + sectionGap;
                    }
                }
            }
            else
            {
                const GameplayOverlayContext::HudLayoutElement *pEventDialogLayout =
                    view.findHudLayoutElement("DialogueEventDialog");
                const GameplayOverlayContext::HudLayoutElement *pTopicRowLayout =
                    view.findHudLayoutElement("DialogueTopicRow_1");
                const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedTopicRowTemplate =
                    pTopicRowLayout != nullptr
                    ? view.resolveHudLayoutElement(
                        "DialogueTopicRow_1",
                        screenWidth,
                        screenHeight,
                        pTopicRowLayout->width,
                        pTopicRowLayout->height)
                    : std::nullopt;
                const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedEventDialog =
                    (showEventDialogPanel && pEventDialogLayout != nullptr && pTopicRowLayout != nullptr)
                    ? view.resolveHudLayoutElement(
                        "DialogueEventDialog",
                        screenWidth,
                        screenHeight,
                        pEventDialogLayout->width,
                        pEventDialogLayout->height)
                    : std::nullopt;

                if (resolvedEventDialog && pTopicRowLayout != nullptr)
                {
                    const float panelScale = resolvedEventDialog->scale;
                    const float panelPaddingX = 10.0f * panelScale;
                    const float panelPaddingY = 10.0f * panelScale;
                    const float panelInnerX = resolvedEventDialog->x + panelPaddingX;
                    const float panelInnerY = resolvedEventDialog->y + panelPaddingY;
                    const float panelInnerWidth = resolvedEventDialog->width - panelPaddingX * 2.0f;
                    const float portraitBorderSize = 80.0f * panelScale;
                    const float sectionGap = 8.0f * panelScale;
                    const std::optional<GameplayOverlayContext::HudFontHandle> topicFont =
                        view.findHudFont(pTopicRowLayout->fontName);
                    const float topicFontScale =
                        snappedHudFontScale(resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale);
                    const float topicLineHeight = topicFont
                        ? static_cast<float>(topicFont->fontHeight) * topicFontScale
                        : 20.0f * panelScale;
                    const float topicWrapWidth = 140.0f
                        * (resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale);
                    const float topicTextWidthScaled = std::max(
                        0.0f,
                        std::min(
                            resolvedTopicRowTemplate ? resolvedTopicRowTemplate->width : panelInnerWidth,
                            topicWrapWidth)
                            - std::abs(pTopicRowLayout->textPadX * topicFontScale) * 2.0f
                            - 4.0f * topicFontScale);
                    const float topicTextWidth =
                        std::max(0.0f, topicTextWidthScaled / std::max(1.0f, topicFontScale));
                    const float rowGap = 4.0f * panelScale;
                    const size_t visibleActionCount = std::min<size_t>(view.activeEventDialog().actions.size(), 5);
                    float contentY = panelInnerY;
                    std::vector<float> actionRowHeights;
                    std::vector<float> actionPressHeights;

                    actionRowHeights.reserve(visibleActionCount);
                    actionPressHeights.reserve(visibleActionCount);

                    if (pHostHouseEntry != nullptr)
                    {
                        contentY += 20.0f * panelScale + sectionGap;
                    }

                    contentY += portraitBorderSize + 20.0f * panelScale + sectionGap;
                    const float availableHeight =
                        resolvedEventDialog->y + resolvedEventDialog->height - panelPaddingY - contentY;

                    for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
                    {
                        std::string label = view.activeEventDialog().actions[actionIndex].label;

                        if (!view.activeEventDialog().actions[actionIndex].enabled
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
                        actionRowHeights.push_back(std::max(minimumRowHeight, wrappedRowHeight));
                        actionPressHeights.push_back(std::max(topicLineHeight, wrappedRowHeight));
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
                    float rowY = contentY + std::max(0.0f, (availableHeight - totalHeight) * 0.5f)
                        - topicListCenterOffsetY;

                    for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
                    {
                        const float rowX = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->x : panelInnerX;
                        const float rowWidth = resolvedTopicRowTemplate
                            ? resolvedTopicRowTemplate->width
                            : panelInnerWidth;
                        const float rowHeight = actionRowHeights[actionIndex];
                        const float pressAreaInsetY = 2.0f * panelScale;
                        const float pressAreaHeight = std::min(
                            rowHeight,
                            actionPressHeights[actionIndex] + pressAreaInsetY * 2.0f);
                        const float pressAreaY = rowY + (rowHeight - pressAreaHeight) * 0.5f;

                        if (mouseX >= rowX
                            && mouseX < rowX + rowWidth
                            && mouseY >= pressAreaY
                            && mouseY < pressAreaY + pressAreaHeight)
                        {
                            return {GameplayDialoguePointerTargetType::Action, actionIndex};
                        }

                        rowY += rowHeight + rowGap;
                    }
                }
            }

            const GameplayOverlayContext::HudLayoutElement *pGoodbyeLayout =
                view.findHudLayoutElement("DialogueGoodbyeButton");
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedGoodbye =
                pGoodbyeLayout != nullptr
                ? view.resolveHudLayoutElement(
                    "DialogueGoodbyeButton",
                    screenWidth,
                    screenHeight,
                    pGoodbyeLayout->width,
                    pGoodbyeLayout->height)
                : std::nullopt;

            if (resolvedGoodbye
                && mouseX >= resolvedGoodbye->x
                && mouseX < resolvedGoodbye->x + resolvedGoodbye->width
                && mouseY >= resolvedGoodbye->y
                && mouseY < resolvedGoodbye->y + resolvedGoodbye->height)
            {
                return {GameplayDialoguePointerTargetType::CloseButton, 0};
            }

            return {};
        };

    const HudPointerState pointerState = {
        dialogMouseX,
        dialogMouseY,
        isLeftMousePressed
    };
    const GameplayDialoguePointerTarget noneDialogueTarget = {};
    handlePointerClickRelease(
        pointerState,
        view.dialogueClickLatch(),
        view.dialoguePressedTarget(),
        noneDialogueTarget,
        findDialoguePointerTarget,
        [&view](const GameplayDialoguePointerTarget &target)
        {
            if (target.type == GameplayDialoguePointerTargetType::Action
                && target.index < view.activeEventDialog().actions.size())
            {
                view.eventDialogSelectionIndex() = target.index;
                view.executeActiveDialogAction();
            }
            else if (target.type == GameplayDialoguePointerTargetType::CloseButton)
            {
                view.handleDialogueCloseRequest();
            }
        });

    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_E];

    if (closePressed)
    {
        if (!view.closeOverlayLatch())
        {
            view.handleDialogueCloseRequest();
            view.closeOverlayLatch() = true;
        }
    }
    else
    {
        view.closeOverlayLatch() = false;
    }
}

void GameplayOverlayInputController::handleLootOverlayInput(
    GameplayOverlayContext &view,
    const bool *pKeyboardState,
    int screenWidth,
    int screenHeight,
    bool hasActiveLootView)
{
    if (!hasActiveLootView)
    {
        view.resetLootOverlayInteractionState();
        return;
    }

    const OutdoorWorldRuntime::ChestViewState *pChestView =
        view.worldRuntime() != nullptr ? view.worldRuntime()->activeChestView() : nullptr;
    const OutdoorWorldRuntime::CorpseViewState *pCorpseView =
        view.worldRuntime() != nullptr ? view.worldRuntime()->activeCorpseView() : nullptr;
    const size_t itemCount =
        pChestView != nullptr ? pChestView->items.size() : (pCorpseView != nullptr ? pCorpseView->items.size() : 0);

    if (pChestView != nullptr && screenWidth > 0 && screenHeight > 0)
    {
        float chestMouseX = 0.0f;
        float chestMouseY = 0.0f;
        const SDL_MouseButtonFlags chestMouseButtons = SDL_GetMouseState(&chestMouseX, &chestMouseY);
        const bool isChestLeftMousePressed = (chestMouseButtons & SDL_BUTTON_LMASK) != 0;
        const HudPointerState chestPointerState = {
            chestMouseX,
            chestMouseY,
            isChestLeftMousePressed
        };
        const auto setHeldItem =
            [&view](const InventoryItem &item)
            {
                view.heldInventoryItem().active = true;
                view.heldInventoryItem().item = item;
                view.heldInventoryItem().grabCellOffsetX = 0;
                view.heldInventoryItem().grabCellOffsetY = 0;
                view.heldInventoryItem().grabOffsetX = 0.0f;
                view.heldInventoryItem().grabOffsetY = 0.0f;
            };
        const auto findChestPointerTarget =
            [&view, screenWidth, screenHeight](float mouseX, float mouseY) -> GameplayChestPointerTarget
            {
                const GameplayOverlayContext::HudLayoutElement *pCloseLayout =
                    view.findHudLayoutElement("ChestCloseButton");

                if (pCloseLayout == nullptr)
                {
                    return {};
                }

                const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedClose =
                    view.resolveHudLayoutElement(
                        "ChestCloseButton",
                        screenWidth,
                        screenHeight,
                        pCloseLayout->width,
                        pCloseLayout->height);

                if (!resolvedClose)
                {
                    return {};
                }

                if (mouseX >= resolvedClose->x
                    && mouseX < resolvedClose->x + resolvedClose->width
                    && mouseY >= resolvedClose->y
                    && mouseY < resolvedClose->y + resolvedClose->height)
                {
                    return {GameplayChestPointerTargetType::CloseButton};
                }

                return {};
            };
        const bool inventoryNestedOverlayActive =
            view.inventoryNestedOverlay().active
            && view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ChestTransfer
            && view.partyRuntime() != nullptr;

        if (inventoryNestedOverlayActive && view.inventoryNestedOverlay().active)
        {
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedInventoryGrid =
                view.resolveInventoryNestedOverlayGridArea(screenWidth, screenHeight);

            if (resolvedInventoryGrid
                && isChestLeftMousePressed
                && !view.inventoryNestedOverlayItemClickLatch()
                && chestMouseX >= resolvedInventoryGrid->x
                && chestMouseX < resolvedInventoryGrid->x + resolvedInventoryGrid->width
                && chestMouseY >= resolvedInventoryGrid->y
                && chestMouseY < resolvedInventoryGrid->y + resolvedInventoryGrid->height)
            {
                Party &party = view.partyRuntime()->party();
                const Character *pCharacter = party.activeMember();
                const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                    resolvedInventoryGrid->x,
                    resolvedInventoryGrid->y,
                    resolvedInventoryGrid->width,
                    resolvedInventoryGrid->height,
                    resolvedInventoryGrid->scale);
                const uint8_t gridX = static_cast<uint8_t>(std::clamp(
                    static_cast<int>((chestMouseX - resolvedInventoryGrid->x) / gridMetrics.cellWidth),
                    0,
                    Character::InventoryWidth - 1));
                const uint8_t gridY = static_cast<uint8_t>(std::clamp(
                    static_cast<int>((chestMouseY - resolvedInventoryGrid->y) / gridMetrics.cellHeight),
                    0,
                    Character::InventoryHeight - 1));

                if (view.heldInventoryItem().active)
                {
                    const ItemDefinition *pItemDefinition =
                        view.itemTable() != nullptr
                        ? view.itemTable()->get(view.heldInventoryItem().item.objectDescriptionId)
                        : nullptr;

                    if (pItemDefinition != nullptr && !pItemDefinition->iconName.empty())
                    {
                        const std::optional<GameplayOverlayContext::HudTextureHandle> pItemTexture =
                            view.ensureHudTextureLoaded(pItemDefinition->iconName);

                        if (pItemTexture)
                        {
                            const float itemWidth = static_cast<float>(pItemTexture->width) * gridMetrics.scale;
                            const float itemHeight = static_cast<float>(pItemTexture->height) * gridMetrics.scale;
                            const float drawX = chestMouseX - view.heldInventoryItem().grabOffsetX;
                            const float drawY = chestMouseY - view.heldInventoryItem().grabOffsetY;
                            const std::optional<std::pair<int, int>> placement = computeHeldInventoryPlacement(
                                gridMetrics,
                                view.heldInventoryItem().item.width,
                                view.heldInventoryItem().item.height,
                                itemWidth,
                                itemHeight,
                                drawX,
                                drawY);

                            if (placement
                                && placement->first >= 0
                                && placement->second >= 0
                                && placement->first < Character::InventoryWidth
                                && placement->second < Character::InventoryHeight)
                            {
                                std::optional<InventoryItem> replacedItem;

                                if (party.tryPlaceItemInMemberInventoryCell(
                                        party.activeMemberIndex(),
                                        view.heldInventoryItem().item,
                                        static_cast<uint8_t>(placement->first),
                                        static_cast<uint8_t>(placement->second),
                                        replacedItem))
                                {
                                    if (replacedItem)
                                    {
                                        view.heldInventoryItem().item = *replacedItem;
                                        view.heldInventoryItem().grabCellOffsetX = 0;
                                        view.heldInventoryItem().grabCellOffsetY = 0;
                                        view.heldInventoryItem().grabOffsetX = 0.0f;
                                        view.heldInventoryItem().grabOffsetY = 0.0f;
                                    }
                                    else
                                    {
                                        view.heldInventoryItem() = {};
                                    }
                                }
                            }
                        }
                    }
                }
                else if (pCharacter != nullptr)
                {
                    const InventoryItem *pItem = pCharacter->inventoryItemAt(gridX, gridY);
                    InventoryItem heldItem = {};

                    if (pItem != nullptr
                        && party.takeItemFromMemberInventoryCell(
                            party.activeMemberIndex(),
                            pItem->gridX,
                            pItem->gridY,
                            heldItem))
                    {
                        setHeldItem(heldItem);
                        const ItemDefinition *pItemDefinition =
                            view.itemTable() != nullptr ? view.itemTable()->get(heldItem.objectDescriptionId) : nullptr;

                        if (pItemDefinition != nullptr && !pItemDefinition->iconName.empty())
                        {
                            const std::optional<GameplayOverlayContext::HudTextureHandle> pItemTexture =
                                view.ensureHudTextureLoaded(pItemDefinition->iconName);

                            if (pItemTexture)
                            {
                                const float itemWidth = static_cast<float>(pItemTexture->width) * gridMetrics.scale;
                                const float itemHeight = static_cast<float>(pItemTexture->height) * gridMetrics.scale;
                                const InventoryItemScreenRect itemRect =
                                    computeInventoryItemScreenRect(gridMetrics, heldItem, itemWidth, itemHeight);
                                view.heldInventoryItem().grabOffsetX = chestMouseX - itemRect.x;
                                view.heldInventoryItem().grabOffsetY = chestMouseY - itemRect.y;
                            }
                        }
                    }
                }

                view.inventoryNestedOverlayItemClickLatch() = true;
            }
            else if (!isChestLeftMousePressed)
            {
                view.inventoryNestedOverlayItemClickLatch() = false;
            }
        }

        const GameplayChestPointerTarget noneChestTarget = {};
        handlePointerClickRelease(
            chestPointerState,
            view.chestClickLatch(),
            view.chestPressedTarget(),
            noneChestTarget,
            findChestPointerTarget,
            [&view](const GameplayChestPointerTarget &target)
            {
                if (target.type != GameplayChestPointerTargetType::CloseButton)
                {
                    return;
                }

                if (view.inventoryNestedOverlay().active)
                {
                    view.closeInventoryNestedOverlay();
                    return;
                }

                if (view.worldRuntime() != nullptr)
                {
                    if (view.audioSystem() != nullptr && view.worldRuntime()->activeChestView() != nullptr)
                    {
                        view.audioSystem()->playCommonSound(
                            SoundId::ChestClose,
                            GameAudioSystem::PlaybackGroup::Ui);
                    }

                    view.worldRuntime()->closeActiveChestView();
                    view.worldRuntime()->closeActiveCorpseView();
                    view.closeInventoryNestedOverlay();
                    view.activateInspectLatch() = true;
                    view.chestSelectionIndex() = 0;
                }
            });

        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedChestGrid =
            view.resolveChestGridArea(screenWidth, screenHeight);
        const GameplayChestPointerTarget hoveredChestTarget =
            findChestPointerTarget(chestMouseX, chestMouseY);

        if (!inventoryNestedOverlayActive
            && resolvedChestGrid
            && isChestLeftMousePressed
            && !view.chestItemClickLatch()
            && hoveredChestTarget.type == GameplayChestPointerTargetType::None
            && chestMouseX >= resolvedChestGrid->x
            && chestMouseX < resolvedChestGrid->x + resolvedChestGrid->width
            && chestMouseY >= resolvedChestGrid->y
            && chestMouseY < resolvedChestGrid->y + resolvedChestGrid->height)
        {
            const InventoryGridMetrics chestGridMetrics = computeInventoryGridMetrics(
                resolvedChestGrid->x,
                resolvedChestGrid->y,
                resolvedChestGrid->width,
                resolvedChestGrid->height,
                resolvedChestGrid->scale,
                pChestView->gridWidth,
                pChestView->gridHeight);
            const uint8_t gridX = static_cast<uint8_t>(std::clamp(
                static_cast<int>((chestMouseX - resolvedChestGrid->x) / chestGridMetrics.cellWidth),
                0,
                static_cast<int>(pChestView->gridWidth) - 1));
            const uint8_t gridY = static_cast<uint8_t>(std::clamp(
                static_cast<int>((chestMouseY - resolvedChestGrid->y) / chestGridMetrics.cellHeight),
                0,
                static_cast<int>(pChestView->gridHeight) - 1));

            if (view.heldInventoryItem().active)
            {
                OutdoorWorldRuntime::ChestItemState chestItem = {};
                chestItem.item = view.heldInventoryItem().item;
                chestItem.itemId = view.heldInventoryItem().item.objectDescriptionId;
                chestItem.quantity = view.heldInventoryItem().item.quantity;
                chestItem.width = view.heldInventoryItem().item.width;
                chestItem.height = view.heldInventoryItem().item.height;
                const ItemDefinition *pItemDefinition =
                    view.itemTable() != nullptr ? view.itemTable()->get(view.heldInventoryItem().item.objectDescriptionId) : nullptr;

                if (pItemDefinition != nullptr)
                {
                    const std::optional<GameplayOverlayContext::HudTextureHandle> pItemTexture =
                        view.ensureHudTextureLoaded(pItemDefinition->iconName);

                    if (pItemTexture)
                    {
                        const float itemWidth = static_cast<float>(pItemTexture->width) * chestGridMetrics.scale;
                        const float itemHeight = static_cast<float>(pItemTexture->height) * chestGridMetrics.scale;
                        const float drawX = chestMouseX - view.heldInventoryItem().grabOffsetX;
                        const float drawY = chestMouseY - view.heldInventoryItem().grabOffsetY;
                        const std::optional<std::pair<int, int>> placement = computeHeldInventoryPlacement(
                            chestGridMetrics,
                            chestItem.width,
                            chestItem.height,
                            itemWidth,
                            itemHeight,
                            drawX,
                            drawY);

                        if (placement
                            && placement->first >= 0
                            && placement->second >= 0
                            && placement->first < pChestView->gridWidth
                            && placement->second < pChestView->gridHeight
                            && view.worldRuntime()->tryPlaceActiveChestItemAt(
                                chestItem,
                                static_cast<uint8_t>(placement->first),
                                static_cast<uint8_t>(placement->second)))
                        {
                            view.heldInventoryItem() = {};
                        }
                    }
                }
            }
            else if (view.worldRuntime() != nullptr && view.partyRuntime() != nullptr)
            {
                OutdoorWorldRuntime::ChestItemState takenItem = {};

                if (view.worldRuntime()->takeActiveChestItemAt(gridX, gridY, takenItem))
                {
                    if (takenItem.isGold)
                    {
                        view.partyRuntime()->party().addGold(static_cast<int>(takenItem.goldAmount));
                    }
                    else
                    {
                        view.heldInventoryItem().active = true;
                        view.heldInventoryItem().item = takenItem.item;
                        view.heldInventoryItem().item.objectDescriptionId =
                            takenItem.item.objectDescriptionId != 0 ? takenItem.item.objectDescriptionId : takenItem.itemId;
                        view.heldInventoryItem().item.quantity = takenItem.quantity;
                        view.heldInventoryItem().item.width = takenItem.width;
                        view.heldInventoryItem().item.height = takenItem.height;
                        view.heldInventoryItem().item.gridX = takenItem.gridX;
                        view.heldInventoryItem().item.gridY = takenItem.gridY;
                        view.heldInventoryItem().grabCellOffsetX = 0;
                        view.heldInventoryItem().grabCellOffsetY = 0;
                        view.heldInventoryItem().grabOffsetX = 0.0f;
                        view.heldInventoryItem().grabOffsetY = 0.0f;

                        const ItemDefinition *pItemDefinition =
                            view.itemTable() != nullptr ? view.itemTable()->get(takenItem.itemId) : nullptr;

                        if (pItemDefinition != nullptr && !pItemDefinition->iconName.empty())
                        {
                            const std::optional<GameplayOverlayContext::HudTextureHandle> pItemTexture =
                                view.ensureHudTextureLoaded(pItemDefinition->iconName);

                            if (pItemTexture)
                            {
                                const float itemWidth =
                                    static_cast<float>(pItemTexture->width) * chestGridMetrics.scale;
                                const float itemHeight =
                                    static_cast<float>(pItemTexture->height) * chestGridMetrics.scale;
                                const InventoryItemScreenRect itemRect = computeInventoryItemScreenRect(
                                    chestGridMetrics,
                                    view.heldInventoryItem().item,
                                    itemWidth,
                                    itemHeight);
                                view.heldInventoryItem().grabOffsetX = chestMouseX - itemRect.x;
                                view.heldInventoryItem().grabOffsetY = chestMouseY - itemRect.y;
                            }
                        }
                    }
                }
            }

            view.chestItemClickLatch() = true;
        }
        else if (!isChestLeftMousePressed)
        {
            view.chestItemClickLatch() = false;
        }
    }
    else
    {
        view.chestClickLatch() = false;
        view.chestItemClickLatch() = false;
        view.chestPressedTarget() = {};
        view.resetInventoryNestedOverlayInteractionState();
    }

    if (itemCount == 0)
    {
        view.chestSelectionIndex() = 0;
    }
    else if (view.chestSelectionIndex() >= itemCount)
    {
        view.chestSelectionIndex() = itemCount - 1;
    }

    if (pKeyboardState[SDL_SCANCODE_UP])
    {
        if (!view.chestSelectUpLatch() && itemCount > 0)
        {
            view.chestSelectionIndex() =
                (view.chestSelectionIndex() == 0) ? (itemCount - 1) : (view.chestSelectionIndex() - 1);
            view.chestSelectUpLatch() = true;
        }
    }
    else
    {
        view.chestSelectUpLatch() = false;
    }

    if (pKeyboardState[SDL_SCANCODE_DOWN])
    {
        if (!view.chestSelectDownLatch() && itemCount > 0)
        {
            view.chestSelectionIndex() = (view.chestSelectionIndex() + 1) % itemCount;
            view.chestSelectDownLatch() = true;
        }
    }
    else
    {
        view.chestSelectDownLatch() = false;
    }

    const bool lootPressed = pKeyboardState[SDL_SCANCODE_RETURN] || pKeyboardState[SDL_SCANCODE_SPACE];

    if (lootPressed)
    {
        if (!view.lootChestItemLatch()
            && !view.inventoryNestedOverlay().active
            && itemCount > 0
            && view.partyRuntime() != nullptr)
        {
            const OutdoorWorldRuntime::ChestViewState *pCurrentChestView =
                view.worldRuntime()->activeChestView();
            const OutdoorWorldRuntime::CorpseViewState *pCurrentCorpseView =
                view.worldRuntime()->activeCorpseView();
            const std::vector<OutdoorWorldRuntime::ChestItemState> *pItems = nullptr;

            if (pCurrentChestView != nullptr)
            {
                pItems = &pCurrentChestView->items;
            }
            else if (pCurrentCorpseView != nullptr)
            {
                pItems = &pCurrentCorpseView->items;
            }

            if (pItems != nullptr && view.chestSelectionIndex() < pItems->size())
            {
                const OutdoorWorldRuntime::ChestItemState item = (*pItems)[view.chestSelectionIndex()];
                bool canLoot = true;

                if (!item.isGold)
                {
                    canLoot = view.partyRuntime()->party().tryGrantInventoryItem(item.item);
                }

                if (canLoot)
                {
                    OutdoorWorldRuntime::ChestItemState removedItem = {};
                    const bool removed = pCurrentChestView != nullptr
                        ? view.worldRuntime()->takeActiveChestItem(view.chestSelectionIndex(), removedItem)
                        : view.worldRuntime()->takeActiveCorpseItem(view.chestSelectionIndex(), removedItem);

                    if (removed)
                    {
                        if (removedItem.isGold)
                        {
                            view.partyRuntime()->party().addGold(static_cast<int>(removedItem.goldAmount));
                        }

                        const OutdoorWorldRuntime::ChestViewState *pUpdatedChestView =
                            view.worldRuntime()->activeChestView();
                        const OutdoorWorldRuntime::CorpseViewState *pUpdatedCorpseView =
                            view.worldRuntime()->activeCorpseView();
                        const std::vector<OutdoorWorldRuntime::ChestItemState> *pUpdatedItems = nullptr;

                        if (pUpdatedChestView != nullptr)
                        {
                            pUpdatedItems = &pUpdatedChestView->items;
                        }
                        else if (pUpdatedCorpseView != nullptr)
                        {
                            pUpdatedItems = &pUpdatedCorpseView->items;
                        }

                        if (pUpdatedItems != nullptr
                            && !pUpdatedItems->empty()
                            && view.chestSelectionIndex() >= pUpdatedItems->size())
                        {
                            view.chestSelectionIndex() = pUpdatedItems->size() - 1;
                        }
                    }
                }
            }

            view.lootChestItemLatch() = true;
        }
    }
    else
    {
        view.lootChestItemLatch() = false;
    }

    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_E];

    if (closePressed)
    {
        if (!view.closeOverlayLatch())
        {
            if (view.inventoryNestedOverlay().active)
            {
                view.closeInventoryNestedOverlay();
            }
            else if (view.worldRuntime() != nullptr)
            {
                if (view.audioSystem() != nullptr && view.worldRuntime()->activeChestView() != nullptr)
                {
                    view.audioSystem()->playCommonSound(
                        SoundId::ChestClose,
                        GameAudioSystem::PlaybackGroup::Ui);
                }

                view.worldRuntime()->closeActiveChestView();
                view.worldRuntime()->closeActiveCorpseView();
                view.activateInspectLatch() = true;
                view.chestSelectionIndex() = 0;
            }

            view.closeOverlayLatch() = true;
        }
    }
    else
    {
        view.closeOverlayLatch() = false;
    }
}
} // namespace OpenYAMM::Game
