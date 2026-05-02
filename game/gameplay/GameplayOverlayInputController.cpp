#include "game/gameplay/GameplayOverlayInputController.h"

#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/StringUtils.h"
#include "game/tables/ItemTable.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/KeyboardScreenLayout.h"

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
constexpr uint64_t SaveGameDoubleClickWindowMs = 500;
constexpr size_t SaveLoadVisibleSlotCount = 10;

struct SaveGameKeyBinding
{
    SDL_Scancode scancode;
    char lower;
    char upper;
};

constexpr std::array<SaveGameKeyBinding, 39> SaveGameEditBindings = {{
    {SDL_SCANCODE_A, 'a', 'A'}, {SDL_SCANCODE_B, 'b', 'B'}, {SDL_SCANCODE_C, 'c', 'C'},
    {SDL_SCANCODE_D, 'd', 'D'}, {SDL_SCANCODE_E, 'e', 'E'}, {SDL_SCANCODE_F, 'f', 'F'},
    {SDL_SCANCODE_G, 'g', 'G'}, {SDL_SCANCODE_H, 'h', 'H'}, {SDL_SCANCODE_I, 'i', 'I'},
    {SDL_SCANCODE_J, 'j', 'J'}, {SDL_SCANCODE_K, 'k', 'K'}, {SDL_SCANCODE_L, 'l', 'L'},
    {SDL_SCANCODE_M, 'm', 'M'}, {SDL_SCANCODE_N, 'n', 'N'}, {SDL_SCANCODE_O, 'o', 'O'},
    {SDL_SCANCODE_P, 'p', 'P'}, {SDL_SCANCODE_Q, 'q', 'Q'}, {SDL_SCANCODE_R, 'r', 'R'},
    {SDL_SCANCODE_S, 's', 'S'}, {SDL_SCANCODE_T, 't', 'T'}, {SDL_SCANCODE_U, 'u', 'U'},
    {SDL_SCANCODE_V, 'v', 'V'}, {SDL_SCANCODE_W, 'w', 'W'}, {SDL_SCANCODE_X, 'x', 'X'},
    {SDL_SCANCODE_Y, 'y', 'Y'}, {SDL_SCANCODE_Z, 'z', 'Z'}, {SDL_SCANCODE_1, '1', '!'},
    {SDL_SCANCODE_2, '2', '@'}, {SDL_SCANCODE_3, '3', '#'}, {SDL_SCANCODE_4, '4', '$'},
    {SDL_SCANCODE_5, '5', '%'}, {SDL_SCANCODE_6, '6', '^'}, {SDL_SCANCODE_7, '7', '&'},
    {SDL_SCANCODE_8, '8', '*'}, {SDL_SCANCODE_9, '9', '('}, {SDL_SCANCODE_0, '0', ')'},
    {SDL_SCANCODE_SPACE, ' ', ' '}, {SDL_SCANCODE_MINUS, '-', '_'}, {SDL_SCANCODE_APOSTROPHE, '\'', '"'}
}};

struct HudPointerState
{
    float x = 0.0f;
    float y = 0.0f;
    bool leftButtonPressed = false;
};

HudPointerState pointerStateFromInput(const GameplayInputFrame &input)
{
    return {
        input.pointerX,
        input.pointerY,
        input.leftMouseButton.held
    };
}

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

std::string formatFoundGoldStatusText(int goldAmount)
{
    return "You found " + std::to_string(std::max(0, goldAmount)) + " gold!";
}

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

std::optional<SDL_Scancode> firstNewlyPressedScancode(
    const bool *pKeyboardState,
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState)
{
    if (pKeyboardState == nullptr)
    {
        return std::nullopt;
    }

    for (int scancode = 0; scancode < SDL_SCANCODE_COUNT; ++scancode)
    {
        if (pKeyboardState[scancode] && previousKeyboardState[scancode] == 0)
        {
            return static_cast<SDL_Scancode>(scancode);
        }
    }

    return std::nullopt;
}

enum class JournalShortcutView : uint8_t
{
    None = 0,
    Map,
    Story,
    Notes
};

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

GameplayMenuPointerTarget resolveMenuPointerTarget(
    GameplayScreenRuntime &view,
    int screenWidth,
    int screenHeight,
    const char *pLayoutId,
    GameplayMenuPointerTargetType type,
    float pointerX,
    float pointerY)
{
    const UiLayoutManager::LayoutElement *pLayout = view.findHudLayoutElement(pLayoutId);

    if (pLayout == nullptr)
    {
        return {};
    }

    const std::optional<GameplayResolvedHudLayoutElement> resolved =
        view.resolveHudLayoutElement(pLayoutId, screenWidth, screenHeight, pLayout->width, pLayout->height);

    if (!resolved || !view.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
    {
        return {};
    }

    GameplayMenuPointerTarget target = {};
    target.type = type;
    return target;
}

GameplaySaveLoadPointerTarget resolveSaveLoadPointerTarget(
    GameplayScreenRuntime &view,
    int screenWidth,
    int screenHeight,
    const char *pLayoutId,
    GameplaySaveLoadPointerTargetType type,
    float pointerX,
    float pointerY)
{
    const UiLayoutManager::LayoutElement *pLayout = view.findHudLayoutElement(pLayoutId);

    if (pLayout == nullptr)
    {
        return {};
    }

    const std::optional<GameplayResolvedHudLayoutElement> resolved =
        view.resolveHudLayoutElement(pLayoutId, screenWidth, screenHeight, pLayout->width, pLayout->height);

    if (!resolved || !view.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
    {
        return {};
    }

    GameplaySaveLoadPointerTarget target = {};
    target.type = type;
    return target;
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

    if (gridMetrics.cellWidth <= 0.0f || gridMetrics.cellHeight <= 0.0f)
    {
        return std::nullopt;
    }

    const int itemWidth = std::max<int>(1, itemWidthCells);
    const int itemHeight = std::max<int>(1, itemHeightCells);
    const float slotSpanWidth = static_cast<float>(itemWidth) * gridMetrics.cellWidth;
    const float slotSpanHeight = static_cast<float>(itemHeight) * gridMetrics.cellHeight;
    const int gridX = static_cast<int>(std::floor(
        (centerX - gridMetrics.x - slotSpanWidth * 0.5f + gridMetrics.cellWidth * 0.5f)
        / gridMetrics.cellWidth));
    const int gridY = static_cast<int>(std::floor(
        (centerY - gridMetrics.y - slotSpanHeight * 0.5f + gridMetrics.cellHeight * 0.5f)
        / gridMetrics.cellHeight));
    return std::pair<int, int>{gridX, gridY};
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
        || houseEntry.type.find(" Guild") != std::string::npos
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

bool GameplayOverlayInputController::handleRestOverlayInput(
    GameplayScreenRuntime &view,
    const GameplayInputFrame &input)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;
    GameplayUiController::RestScreenState &restScreen = view.restScreenState();

    if (!restScreen.active)
    {
        view.interactionState().restClickLatch = false;
        view.interactionState().restPressedTarget = {};
        return false;
    }

    const auto finishOrCloseRestScreen =
        [&view, &restScreen]()
        {
            if (restScreen.mode != GameplayUiController::RestMode::None)
            {
                view.completeRestAction(true);
            }
            else
            {
                view.closeRestOverlay();
            }
        };
    const auto waitUntilDawnMinutes =
        [&view]() -> float
        {
            if (view.worldRuntime() == nullptr)
            {
                return 8.0f * 60.0f;
            }

            constexpr float DawnMinuteOfDay = 6.0f * 60.0f;
            const float minutesOfDay = std::fmod(std::max(0.0f, view.worldRuntime()->gameMinutes()), 1440.0f);
            float targetMinuteOfDay = DawnMinuteOfDay;

            if (targetMinuteOfDay <= minutesOfDay)
            {
                targetMinuteOfDay += 1440.0f;
            }

            return targetMinuteOfDay - minutesOfDay;
        };

    if (pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_ESCAPE])
    {
        if (!view.interactionState().closeOverlayLatch)
        {
            finishOrCloseRestScreen();
            view.interactionState().closeOverlayLatch = true;
        }
    }
    else
    {
        view.interactionState().closeOverlayLatch = false;
    }

    if (!restScreen.active)
    {
        return true;
    }

    if (screenWidth <= 0 || screenHeight <= 0)
    {
        view.interactionState().restClickLatch = false;
        view.interactionState().restPressedTarget = {};
        return true;
    }

    const HudPointerState pointerState = pointerStateFromInput(input);
    const GameplayRestPointerTarget noneTarget = {};
    const auto resolveTarget =
        [&view, screenWidth, screenHeight](
            const std::string &layoutId,
            GameplayRestPointerTargetType targetType,
            float pointerX,
            float pointerY) -> GameplayRestPointerTarget
        {
            const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

            if (pLayout == nullptr)
            {
                return {};
            }

            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                view.resolveHudLayoutElement(layoutId, screenWidth, screenHeight, pLayout->width, pLayout->height);

            if (!resolved || !view.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
            {
                return {};
            }

            return {targetType};
        };
    const auto findPointerTarget =
        [&resolveTarget](float pointerX, float pointerY) -> GameplayRestPointerTarget
        {
            static const std::pair<const char *, GameplayRestPointerTargetType> Targets[] = {
                {"RestButton8Hours", GameplayRestPointerTargetType::Rest8HoursButton},
                {"RestButtonUntilDawn", GameplayRestPointerTargetType::WaitUntilDawnButton},
                {"RestButton1Hour", GameplayRestPointerTargetType::Wait1HourButton},
                {"RestButton5Minutes", GameplayRestPointerTargetType::Wait5MinutesButton},
                {"RestButtonExit", GameplayRestPointerTargetType::ExitButton},
            };

            for (const auto &[layoutId, targetType] : Targets)
            {
                const GameplayRestPointerTarget target = resolveTarget(layoutId, targetType, pointerX, pointerY);

                if (target.type != GameplayRestPointerTargetType::None)
                {
                    return target;
                }
            }

            return {};
        };

    handlePointerClickRelease(
        pointerState,
        view.interactionState().restClickLatch,
        view.interactionState().restPressedTarget,
        noneTarget,
        findPointerTarget,
        [&view, &finishOrCloseRestScreen, &waitUntilDawnMinutes](const GameplayRestPointerTarget &target)
        {
            switch (target.type)
            {
            case GameplayRestPointerTargetType::Rest8HoursButton:
                view.startRestAction(GameplayUiController::RestMode::Heal, 8.0f * 60.0f);
                break;

            case GameplayRestPointerTargetType::WaitUntilDawnButton:
                view.startRestAction(GameplayUiController::RestMode::Wait, waitUntilDawnMinutes());
                break;

            case GameplayRestPointerTargetType::Wait1HourButton:
                view.startRestAction(GameplayUiController::RestMode::Wait, 60.0f);
                break;

            case GameplayRestPointerTargetType::Wait5MinutesButton:
                view.startRestAction(GameplayUiController::RestMode::Wait, 5.0f);
                break;

            case GameplayRestPointerTargetType::ExitButton:
                finishOrCloseRestScreen();
                break;

            case GameplayRestPointerTargetType::None:
            case GameplayRestPointerTargetType::OpenButton:
                break;
            }
        });

    return true;
}

bool GameplayOverlayInputController::handleMenuOverlayInput(
    GameplayScreenRuntime &view,
    const GameplayInputFrame &input)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;
    GameplayUiController::MenuScreenState &menuScreen = view.menuScreenState();

    if (!menuScreen.active)
    {
        view.interactionState().menuToggleLatch = false;
        view.interactionState().menuClickLatch = false;
        view.interactionState().menuPressedTarget = {};
        return false;
    }

    const bool closePressed = pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (closePressed)
    {
        if (!view.interactionState().menuToggleLatch)
        {
            view.closeMenuOverlay();
            view.interactionState().menuToggleLatch = true;
        }
    }
    else
    {
        view.interactionState().menuToggleLatch = false;
    }

    if (!menuScreen.active)
    {
        return true;
    }

    const HudPointerState menuPointerState = pointerStateFromInput(input);
    const GameplayMenuPointerTarget noneMenuTarget = {};
    const auto findMenuPointerTarget =
        [&view, screenWidth, screenHeight](float pointerX, float pointerY) -> GameplayMenuPointerTarget
        {
            GameplayMenuPointerTarget target = resolveMenuPointerTarget(
                view,
                screenWidth,
                screenHeight,
                "MenuButtonNewGame",
                GameplayMenuPointerTargetType::NewGameButton,
                pointerX,
                pointerY);

            if (target.type != GameplayMenuPointerTargetType::None)
            {
                return target;
            }

            target = resolveMenuPointerTarget(
                view,
                screenWidth,
                screenHeight,
                "MenuButtonSaveGame",
                GameplayMenuPointerTargetType::SaveGameButton,
                pointerX,
                pointerY);

            if (target.type != GameplayMenuPointerTargetType::None)
            {
                return target;
            }

            target = resolveMenuPointerTarget(
                view,
                screenWidth,
                screenHeight,
                "MenuButtonLoadGame",
                GameplayMenuPointerTargetType::LoadGameButton,
                pointerX,
                pointerY);

            if (target.type != GameplayMenuPointerTargetType::None)
            {
                return target;
            }

            target = resolveMenuPointerTarget(
                view,
                screenWidth,
                screenHeight,
                "MenuButtonControls",
                GameplayMenuPointerTargetType::ControlsButton,
                pointerX,
                pointerY);

            if (target.type != GameplayMenuPointerTargetType::None)
            {
                return target;
            }

            target = resolveMenuPointerTarget(
                view,
                screenWidth,
                screenHeight,
                "MenuButtonQuit",
                GameplayMenuPointerTargetType::QuitButton,
                pointerX,
                pointerY);

            if (target.type != GameplayMenuPointerTargetType::None)
            {
                return target;
            }

            return resolveMenuPointerTarget(
                view,
                screenWidth,
                screenHeight,
                "MenuButtonReturn",
                GameplayMenuPointerTargetType::ReturnButton,
                pointerX,
                pointerY);
        };

    handlePointerClickRelease(
        menuPointerState,
        view.interactionState().menuClickLatch,
        view.interactionState().menuPressedTarget,
        noneMenuTarget,
        findMenuPointerTarget,
        [&view, &menuScreen](const GameplayMenuPointerTarget &target)
        {
            switch (target.type)
            {
            case GameplayMenuPointerTargetType::NewGameButton:
                if (menuScreen.newGameConfirmationArmed)
                {
                    menuScreen.bottomBarTextUseWhite = false;

                    if (GameAudioSystem *pAudio = view.audioSystem())
                    {
                        pAudio->playCommonSound(SoundId::ClickIn, GameAudioSystem::PlaybackGroup::Ui);
                    }

                    view.requestOpenNewGameScreen();
                }
                else
                {
                    menuScreen.newGameConfirmationArmed = true;
                    menuScreen.quitConfirmationArmed = false;
                    menuScreen.bottomBarTextUseWhite = true;
                    menuScreen.bottomBarText = "Press New Game again to abandon current progress.";

                    if (GameAudioSystem *pAudio = view.audioSystem())
                    {
                        pAudio->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
                    }
                }
                break;

            case GameplayMenuPointerTargetType::SaveGameButton:
                menuScreen.newGameConfirmationArmed = false;
                menuScreen.quitConfirmationArmed = false;
                menuScreen.bottomBarTextUseWhite = false;
                menuScreen.bottomBarText.clear();

                if (GameAudioSystem *pAudio = view.audioSystem())
                {
                    pAudio->playCommonSound(SoundId::ClickIn, GameAudioSystem::PlaybackGroup::Ui);
                }

                view.openSaveGameOverlay();
                break;

            case GameplayMenuPointerTargetType::LoadGameButton:
                menuScreen.newGameConfirmationArmed = false;
                menuScreen.quitConfirmationArmed = false;
                menuScreen.bottomBarTextUseWhite = false;
                menuScreen.bottomBarText.clear();

                if (GameAudioSystem *pAudio = view.audioSystem())
                {
                    pAudio->playCommonSound(SoundId::ClickIn, GameAudioSystem::PlaybackGroup::Ui);
                }

                view.requestOpenLoadGameScreen();
                break;

            case GameplayMenuPointerTargetType::ControlsButton:
                menuScreen.newGameConfirmationArmed = false;
                menuScreen.quitConfirmationArmed = false;
                menuScreen.bottomBarTextUseWhite = false;
                menuScreen.bottomBarText.clear();

                if (GameAudioSystem *pAudio = view.audioSystem())
                {
                    pAudio->playCommonSound(SoundId::ClickIn, GameAudioSystem::PlaybackGroup::Ui);
                }

                view.openControlsOverlay();
                break;

            case GameplayMenuPointerTargetType::QuitButton:
                if (menuScreen.quitConfirmationArmed)
                {
                    if (GameAudioSystem *pAudio = view.audioSystem())
                    {
                        pAudio->playCommonSound(SoundId::WoodDoorClosing, GameAudioSystem::PlaybackGroup::Ui);
                    }

                    SDL_Event event = {};
                    event.type = SDL_EVENT_QUIT;
                    SDL_PushEvent(&event);
                }
                else
                {
                    menuScreen.newGameConfirmationArmed = false;
                    menuScreen.quitConfirmationArmed = true;
                    menuScreen.bottomBarTextUseWhite = true;
                    menuScreen.bottomBarText = "Press Quit again to exit.";

                    if (GameAudioSystem *pAudio = view.audioSystem())
                    {
                        pAudio->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
                    }
                }
                break;

            case GameplayMenuPointerTargetType::ReturnButton:
                menuScreen.newGameConfirmationArmed = false;
                menuScreen.quitConfirmationArmed = false;
                menuScreen.bottomBarTextUseWhite = false;
                menuScreen.bottomBarText.clear();
                view.closeMenuOverlay();
                break;

            case GameplayMenuPointerTargetType::None:
                break;
            }
        });

    return true;
}

bool GameplayOverlayInputController::handleControlsOverlayInput(
    GameplayScreenRuntime &view,
    const GameplayInputFrame &input)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;
    GameplayUiController::ControlsScreenState &controlsScreen = view.controlsScreenState();

    if (!controlsScreen.active)
    {
        view.interactionState().controlsToggleLatch = false;
        view.interactionState().controlsClickLatch = false;
        view.interactionState().controlsPressedTarget = {};
        view.interactionState().controlsSliderDragActive = false;
        view.interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
        return false;
    }

    const bool closePressed =
        pKeyboardState != nullptr && (pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_RETURN]);

    if (closePressed)
    {
        if (!view.interactionState().controlsToggleLatch)
        {
            view.closeControlsOverlay();
            view.interactionState().controlsToggleLatch = true;
        }
    }
    else
    {
        view.interactionState().controlsToggleLatch = false;
    }

    if (!controlsScreen.active)
    {
        return true;
    }

    const HudPointerState pointerState = pointerStateFromInput(input);
    const GameplayControlsPointerTarget noneTarget = {};
    const auto resolveTarget =
        [&view, screenWidth, screenHeight](
            const char *pLayoutId,
            GameplayControlsPointerTargetType type,
            float pointerX,
            float pointerY) -> GameplayControlsPointerTarget
        {
            const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(pLayoutId);

            if (pLayout == nullptr)
            {
                return {};
            }

            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                view.resolveHudLayoutElement(pLayoutId, screenWidth, screenHeight, pLayout->width, pLayout->height);

            if (!resolved || !view.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
            {
                return {};
            }

            GameplayControlsPointerTarget target = {};
            target.type = type;

            if (type == GameplayControlsPointerTargetType::SoundTrack
                || type == GameplayControlsPointerTargetType::MusicTrack
                || type == GameplayControlsPointerTargetType::VoiceTrack)
            {
                const float trackWidth = std::max(1.0f, resolved->width);
                const float t = std::clamp((pointerX - resolved->x) / trackWidth, 0.0f, 1.0f);
                target.sliderValue = std::clamp(static_cast<int>(std::lround(t * 9.0f)), 0, 9);
            }

            return target;
        };
    const auto findPointerTarget =
        [&resolveTarget](float pointerX, float pointerY) -> GameplayControlsPointerTarget
        {
            static const std::pair<const char *, GameplayControlsPointerTargetType> Targets[] = {
                {"ControlsConfigureKeyboardButton", GameplayControlsPointerTargetType::ConfigureKeyboardButton},
                {"ControlsVideoOptionsButton", GameplayControlsPointerTargetType::VideoOptionsButton},
                {"ControlsTurnRate16Button", GameplayControlsPointerTargetType::TurnRate16Button},
                {"ControlsTurnRate32Button", GameplayControlsPointerTargetType::TurnRate32Button},
                {"ControlsTurnRateSmoothButton", GameplayControlsPointerTargetType::TurnRateSmoothButton},
                {"ControlsWalkSoundButton", GameplayControlsPointerTargetType::WalkSoundButton},
                {"ControlsShowHitsButton", GameplayControlsPointerTargetType::ShowHitsButton},
                {"ControlsAlwaysRunButton", GameplayControlsPointerTargetType::AlwaysRunButton},
                {"ControlsFlipOnExitButton", GameplayControlsPointerTargetType::FlipOnExitButton},
                {"ControlsSoundLeftButton", GameplayControlsPointerTargetType::SoundLeftButton},
                {"ControlsSoundRightButton", GameplayControlsPointerTargetType::SoundRightButton},
                {"ControlsMusicLeftButton", GameplayControlsPointerTargetType::MusicLeftButton},
                {"ControlsMusicRightButton", GameplayControlsPointerTargetType::MusicRightButton},
                {"ControlsVoiceLeftButton", GameplayControlsPointerTargetType::VoiceLeftButton},
                {"ControlsVoiceRightButton", GameplayControlsPointerTargetType::VoiceRightButton},
                {"ControlsReturnButton", GameplayControlsPointerTargetType::ReturnButton},
            };

            for (const auto &[layoutId, targetType] : Targets)
            {
                const GameplayControlsPointerTarget target = resolveTarget(layoutId, targetType, pointerX, pointerY);

                if (target.type != GameplayControlsPointerTargetType::None)
                {
                    return target;
                }
            }

            return {};
        };
    const auto findSliderPressTarget =
        [&resolveTarget](float pointerX, float pointerY) -> GameplayControlsPointerTarget
        {
            static const std::pair<const char *, GameplayControlsPointerTargetType> Sliders[] = {
                {"ControlsSoundKnobLane", GameplayControlsPointerTargetType::SoundTrack},
                {"ControlsMusicKnobLane", GameplayControlsPointerTargetType::MusicTrack},
                {"ControlsVoiceKnobLane", GameplayControlsPointerTargetType::VoiceTrack},
            };

            for (const auto &[layoutId, targetType] : Sliders)
            {
                const GameplayControlsPointerTarget target = resolveTarget(layoutId, targetType, pointerX, pointerY);

                if (target.type != GameplayControlsPointerTargetType::None)
                {
                    return target;
                }
            }

            return {};
        };
    const auto applySliderValue =
        [&view](GameplayControlsPointerTargetType type, int sliderValue) -> bool
        {
            GameSettings &settings = view.mutableSettings();
            const int clampedValue = std::clamp(sliderValue, 0, 9);
            int *pSettingValue = nullptr;
            std::optional<GameAudioSystem::PlaybackGroup> previewGroup;

            switch (type)
            {
            case GameplayControlsPointerTargetType::SoundTrack:
                pSettingValue = &settings.soundVolume;
                previewGroup = GameAudioSystem::PlaybackGroup::Ui;
                break;

            case GameplayControlsPointerTargetType::MusicTrack:
                pSettingValue = &settings.musicVolume;
                previewGroup = GameAudioSystem::PlaybackGroup::Music;
                break;

            case GameplayControlsPointerTargetType::VoiceTrack:
                pSettingValue = &settings.voiceVolume;
                previewGroup = GameAudioSystem::PlaybackGroup::Speech;
                break;

            default:
                break;
            }

            if (pSettingValue == nullptr || *pSettingValue == clampedValue)
            {
                return false;
            }

            *pSettingValue = clampedValue;
            view.commitSettingsChange();

            if (previewGroup && view.audioSystem() != nullptr)
            {
                view.audioSystem()->playCommonSound(SoundId::Church, *previewGroup);
            }

            return true;
        };
    const auto updateDraggedSlider =
        [&view, screenWidth, screenHeight, &applySliderValue](GameplayControlsPointerTargetType type, float pointerX)
        {
            const char *pLayoutId = nullptr;

            switch (type)
            {
            case GameplayControlsPointerTargetType::SoundTrack:
                pLayoutId = "ControlsSoundKnobLane";
                break;

            case GameplayControlsPointerTargetType::MusicTrack:
                pLayoutId = "ControlsMusicKnobLane";
                break;

            case GameplayControlsPointerTargetType::VoiceTrack:
                pLayoutId = "ControlsVoiceKnobLane";
                break;

            default:
                return;
            }

            const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(pLayoutId);

            if (pLayout == nullptr)
            {
                return;
            }

            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                view.resolveHudLayoutElement(pLayoutId, screenWidth, screenHeight, pLayout->width, pLayout->height);

            if (!resolved)
            {
                return;
            }

            const float trackWidth = std::max(1.0f, resolved->width);
            const float t = std::clamp((pointerX - resolved->x) / trackWidth, 0.0f, 1.0f);
            const int sliderValue = std::clamp(static_cast<int>(std::lround(t * 9.0f)), 0, 9);
            (void)applySliderValue(type, sliderValue);
        };

    if (pointerState.leftButtonPressed)
    {
        if (!view.interactionState().controlsSliderDragActive)
        {
            const GameplayControlsPointerTarget sliderTarget = findSliderPressTarget(pointerState.x, pointerState.y);

            if (sliderTarget.type == GameplayControlsPointerTargetType::SoundTrack
                || sliderTarget.type == GameplayControlsPointerTargetType::MusicTrack
                || sliderTarget.type == GameplayControlsPointerTargetType::VoiceTrack)
            {
                view.interactionState().controlsSliderDragActive = true;
                view.interactionState().controlsDraggedSlider = sliderTarget.type;
                view.interactionState().controlsClickLatch = false;
                view.interactionState().controlsPressedTarget = {};
                (void)applySliderValue(sliderTarget.type, sliderTarget.sliderValue);
                return true;
            }
        }
        else
        {
            updateDraggedSlider(view.interactionState().controlsDraggedSlider, pointerState.x);
            return true;
        }
    }
    else if (view.interactionState().controlsSliderDragActive)
    {
        view.interactionState().controlsSliderDragActive = false;
        view.interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
        view.interactionState().controlsClickLatch = false;
        view.interactionState().controlsPressedTarget = {};
        return true;
    }

    handlePointerClickRelease(
        pointerState,
        view.interactionState().controlsClickLatch,
        view.interactionState().controlsPressedTarget,
        noneTarget,
        findPointerTarget,
        [&view, &applySliderValue](const GameplayControlsPointerTarget &target)
        {
            GameSettings &settings = view.mutableSettings();

            switch (target.type)
            {
            case GameplayControlsPointerTargetType::ConfigureKeyboardButton:
                view.openKeyboardOverlay();
                break;

            case GameplayControlsPointerTargetType::VideoOptionsButton:
                view.openVideoOptionsOverlay();
                break;

            case GameplayControlsPointerTargetType::TurnRate16Button:
                settings.turnRate = TurnRateMode::X16;
                view.commitSettingsChange();
                break;

            case GameplayControlsPointerTargetType::TurnRate32Button:
                settings.turnRate = TurnRateMode::X32;
                view.commitSettingsChange();
                break;

            case GameplayControlsPointerTargetType::TurnRateSmoothButton:
                settings.turnRate = TurnRateMode::Smooth;
                view.commitSettingsChange();
                break;

            case GameplayControlsPointerTargetType::WalkSoundButton:
                settings.walksound = !settings.walksound;
                view.commitSettingsChange();
                break;

            case GameplayControlsPointerTargetType::ShowHitsButton:
                settings.showHits = !settings.showHits;
                view.commitSettingsChange();
                break;

            case GameplayControlsPointerTargetType::AlwaysRunButton:
                settings.alwaysRun = !settings.alwaysRun;
                view.commitSettingsChange();
                break;

            case GameplayControlsPointerTargetType::FlipOnExitButton:
                settings.flipOnExit = !settings.flipOnExit;
                view.commitSettingsChange();
                break;

            case GameplayControlsPointerTargetType::SoundLeftButton:
                (void)applySliderValue(GameplayControlsPointerTargetType::SoundTrack, settings.soundVolume - 1);
                break;

            case GameplayControlsPointerTargetType::SoundRightButton:
                (void)applySliderValue(GameplayControlsPointerTargetType::SoundTrack, settings.soundVolume + 1);
                break;

            case GameplayControlsPointerTargetType::MusicLeftButton:
                (void)applySliderValue(GameplayControlsPointerTargetType::MusicTrack, settings.musicVolume - 1);
                break;

            case GameplayControlsPointerTargetType::MusicRightButton:
                (void)applySliderValue(GameplayControlsPointerTargetType::MusicTrack, settings.musicVolume + 1);
                break;

            case GameplayControlsPointerTargetType::VoiceLeftButton:
                (void)applySliderValue(GameplayControlsPointerTargetType::VoiceTrack, settings.voiceVolume - 1);
                break;

            case GameplayControlsPointerTargetType::VoiceRightButton:
                (void)applySliderValue(GameplayControlsPointerTargetType::VoiceTrack, settings.voiceVolume + 1);
                break;

            case GameplayControlsPointerTargetType::ReturnButton:
                view.closeControlsOverlay();
                break;

            case GameplayControlsPointerTargetType::SoundTrack:
            case GameplayControlsPointerTargetType::MusicTrack:
            case GameplayControlsPointerTargetType::VoiceTrack:
            case GameplayControlsPointerTargetType::None:
                break;
            }
        });

    return true;
}

bool GameplayOverlayInputController::handleKeyboardOverlayInput(
    GameplayScreenRuntime &view,
    const GameplayInputFrame &input)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;
    GameplayUiController::KeyboardScreenState &keyboardScreen = view.keyboardScreenState();

    if (!keyboardScreen.active)
    {
        view.interactionState().keyboardToggleLatch = false;
        view.interactionState().keyboardClickLatch = false;
        view.interactionState().keyboardPressedTarget = {};
        return false;
    }

    const bool closePressed = pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (closePressed)
    {
        if (!view.interactionState().keyboardToggleLatch)
        {
            view.closeKeyboardOverlayToControls();
            view.interactionState().keyboardToggleLatch = true;
        }
    }
    else
    {
        view.interactionState().keyboardToggleLatch = false;
    }

    if (!keyboardScreen.active)
    {
        return true;
    }

    if (keyboardScreen.waitingForBinding)
    {
        const std::optional<SDL_Scancode> reboundScancode =
            firstNewlyPressedScancode(pKeyboardState, view.previousKeyboardState());

        if (reboundScancode.has_value())
        {
            view.mutableSettings().keyboard.setBinding(keyboardScreen.pendingAction, *reboundScancode);
            keyboardScreen.waitingForBinding = false;
            view.commitSettingsChange();
        }
    }

    const HudPointerState pointerState = pointerStateFromInput(input);
    const GameplayKeyboardPointerTarget noneTarget = {};
    const auto resolveLayoutTarget =
        [&view, screenWidth, screenHeight](
            const char *pLayoutId,
            GameplayKeyboardPointerTargetType type,
            float pointerX,
            float pointerY) -> GameplayKeyboardPointerTarget
        {
            const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(pLayoutId);

            if (pLayout == nullptr)
            {
                return {};
            }

            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                view.resolveHudLayoutElement(pLayoutId, screenWidth, screenHeight, pLayout->width, pLayout->height);

            if (!resolved || !view.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
            {
                return {};
            }

            GameplayKeyboardPointerTarget target = {};
            target.type = type;
            return target;
        };
    const auto resolveBindingRowTarget =
        [&view, &keyboardScreen, screenWidth, screenHeight](float pointerX, float pointerY) -> GameplayKeyboardPointerTarget
        {
            const std::optional<KeyboardScreenLayout> keyboardLayout =
                resolveKeyboardScreenLayout(view, screenWidth, screenHeight);

            if (!keyboardLayout)
            {
                return {};
            }

            for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
            {
                if (definition.page != keyboardScreen.page)
                {
                    continue;
                }

                const float rowX = keyboardLayout->labelColumnX(definition.column);
                const float rowY = keyboardLayout->rowY(definition.row);

                if (pointerX < rowX
                    || pointerX >= rowX + keyboardLayout->rowWidth(definition.column)
                    || pointerY < rowY
                    || pointerY >= rowY + keyboardLayout->rowHeight)
                {
                    continue;
                }

                GameplayKeyboardPointerTarget target = {};
                target.type = GameplayKeyboardPointerTargetType::BindingRow;
                target.action = definition.action;
                return target;
            }

            return {};
        };
    const auto findPointerTarget =
        [&resolveLayoutTarget, &resolveBindingRowTarget](float pointerX, float pointerY) -> GameplayKeyboardPointerTarget
        {
            if (const GameplayKeyboardPointerTarget bindingTarget = resolveBindingRowTarget(pointerX, pointerY);
                bindingTarget.type != GameplayKeyboardPointerTargetType::None)
            {
                return bindingTarget;
            }

            static const std::pair<const char *, GameplayKeyboardPointerTargetType> Targets[] = {
                {"KeyboardPage1Button", GameplayKeyboardPointerTargetType::Page1Button},
                {"KeyboardPage2Button", GameplayKeyboardPointerTargetType::Page2Button},
                {"KeyboardDefaultButton", GameplayKeyboardPointerTargetType::DefaultButton},
                {"KeyboardBackButton", GameplayKeyboardPointerTargetType::BackButton},
                {"KeyboardReturnButton", GameplayKeyboardPointerTargetType::ReturnButton},
            };

            for (const auto &[layoutId, targetType] : Targets)
            {
                const GameplayKeyboardPointerTarget target =
                    resolveLayoutTarget(layoutId, targetType, pointerX, pointerY);

                if (target.type != GameplayKeyboardPointerTargetType::None)
                {
                    return target;
                }
            }

            return {};
        };

    handlePointerClickRelease(
        pointerState,
        view.interactionState().keyboardClickLatch,
        view.interactionState().keyboardPressedTarget,
        noneTarget,
        findPointerTarget,
        [&view, &keyboardScreen](const GameplayKeyboardPointerTarget &target)
        {
            switch (target.type)
            {
            case GameplayKeyboardPointerTargetType::BindingRow:
                keyboardScreen.waitingForBinding = true;
                keyboardScreen.pendingAction = target.action;
                break;

            case GameplayKeyboardPointerTargetType::Page1Button:
                keyboardScreen.page = KeyboardBindingPage::Page1;
                keyboardScreen.waitingForBinding = false;
                break;

            case GameplayKeyboardPointerTargetType::Page2Button:
                keyboardScreen.page = KeyboardBindingPage::Page2;
                keyboardScreen.waitingForBinding = false;
                break;

            case GameplayKeyboardPointerTargetType::DefaultButton:
                view.mutableSettings().keyboard.restoreDefaults();
                keyboardScreen.waitingForBinding = false;
                view.commitSettingsChange();
                break;

            case GameplayKeyboardPointerTargetType::BackButton:
                view.closeKeyboardOverlayToControls();
                break;

            case GameplayKeyboardPointerTargetType::ReturnButton:
                view.closeKeyboardOverlayToMenu();
                break;

            case GameplayKeyboardPointerTargetType::None:
                break;
            }
        });

    return true;
}

bool GameplayOverlayInputController::handleVideoOptionsOverlayInput(
    GameplayScreenRuntime &view,
    const GameplayInputFrame &input)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;
    GameplayUiController::VideoOptionsScreenState &videoOptionsScreen = view.videoOptionsScreenState();

    if (!videoOptionsScreen.active)
    {
        view.interactionState().videoOptionsToggleLatch = false;
        view.interactionState().videoOptionsClickLatch = false;
        view.interactionState().videoOptionsPressedTarget = {};
        return false;
    }

    const bool closePressed =
        pKeyboardState != nullptr && (pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_RETURN]);

    if (closePressed)
    {
        if (!view.interactionState().videoOptionsToggleLatch)
        {
            view.closeVideoOptionsOverlay();
            view.interactionState().videoOptionsToggleLatch = true;
        }
    }
    else
    {
        view.interactionState().videoOptionsToggleLatch = false;
    }

    if (!videoOptionsScreen.active)
    {
        return true;
    }

    const HudPointerState pointerState = pointerStateFromInput(input);
    const GameplayVideoOptionsPointerTarget noneTarget = {};
    const auto resolveTarget =
        [&view, screenWidth, screenHeight](
            const char *pLayoutId,
            GameplayVideoOptionsPointerTargetType type,
            float pointerX,
            float pointerY) -> GameplayVideoOptionsPointerTarget
        {
            const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(pLayoutId);

            if (pLayout == nullptr)
            {
                return {};
            }

            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                view.resolveHudLayoutElement(pLayoutId, screenWidth, screenHeight, pLayout->width, pLayout->height);

            if (!resolved || !view.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
            {
                return {};
            }

            GameplayVideoOptionsPointerTarget target = {};
            target.type = type;
            return target;
        };
    const auto findPointerTarget =
        [&resolveTarget](float pointerX, float pointerY) -> GameplayVideoOptionsPointerTarget
        {
            static const std::pair<const char *, GameplayVideoOptionsPointerTargetType> Targets[] = {
                {"VideoOptionsBloodSplatsButton", GameplayVideoOptionsPointerTargetType::BloodSplatsButton},
                {"VideoOptionsColoredLightsButton", GameplayVideoOptionsPointerTargetType::ColoredLightsButton},
                {"VideoOptionsTintingButton", GameplayVideoOptionsPointerTargetType::TintingButton},
                {"VideoOptionsReturnButton", GameplayVideoOptionsPointerTargetType::ReturnButton},
            };

            for (const auto &[layoutId, targetType] : Targets)
            {
                const GameplayVideoOptionsPointerTarget target = resolveTarget(layoutId, targetType, pointerX, pointerY);

                if (target.type != GameplayVideoOptionsPointerTargetType::None)
                {
                    return target;
                }
            }

            return {};
        };

    handlePointerClickRelease(
        pointerState,
        view.interactionState().videoOptionsClickLatch,
        view.interactionState().videoOptionsPressedTarget,
        noneTarget,
        findPointerTarget,
        [&view](const GameplayVideoOptionsPointerTarget &target)
        {
            GameSettings &settings = view.mutableSettings();

            switch (target.type)
            {
            case GameplayVideoOptionsPointerTargetType::BloodSplatsButton:
                settings.bloodSplats = !settings.bloodSplats;
                view.commitSettingsChange();
                break;

            case GameplayVideoOptionsPointerTargetType::ColoredLightsButton:
                settings.coloredLights = !settings.coloredLights;
                view.commitSettingsChange();
                break;

            case GameplayVideoOptionsPointerTargetType::TintingButton:
                settings.tinting = !settings.tinting;
                view.commitSettingsChange();
                break;

            case GameplayVideoOptionsPointerTargetType::ReturnButton:
                view.closeVideoOptionsOverlay();
                break;

            case GameplayVideoOptionsPointerTargetType::None:
                break;
            }
        });

    return true;
}

bool GameplayOverlayInputController::handleSaveGameOverlayInput(
    GameplayScreenRuntime &view,
    const GameplayInputFrame &input)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;
    GameplayUiController::SaveGameScreenState &saveGameScreen = view.saveGameScreenState();

    if (!saveGameScreen.active)
    {
        view.interactionState().saveGameToggleLatch = false;
        view.interactionState().saveGameClickLatch = false;
        view.interactionState().saveGamePressedTarget = {};
        view.interactionState().saveGameEditKeyLatches.fill(false);
        view.interactionState().saveGameEditBackspaceLatch = false;
        return false;
    }

    const bool closePressed =
        pKeyboardState != nullptr
        && (pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_RETURN]);

    if (closePressed)
    {
        if (!view.interactionState().saveGameToggleLatch)
        {
            view.closeSaveGameOverlay();
            view.interactionState().saveGameToggleLatch = true;
        }
    }
    else
    {
        view.interactionState().saveGameToggleLatch = false;
    }

    if (!saveGameScreen.active)
    {
        return true;
    }

    if (saveGameScreen.editActive && pKeyboardState != nullptr)
    {
        const bool shiftPressed =
            pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];

        for (size_t bindingIndex = 0; bindingIndex < SaveGameEditBindings.size(); ++bindingIndex)
        {
            const SaveGameKeyBinding &binding = SaveGameEditBindings[bindingIndex];
            const bool pressed = pKeyboardState[binding.scancode];

            if (pressed)
            {
                if (!view.interactionState().saveGameEditKeyLatches[bindingIndex] && saveGameScreen.editBuffer.size() < 30)
                {
                    saveGameScreen.editBuffer.push_back(shiftPressed ? binding.upper : binding.lower);
                    view.interactionState().saveGameEditKeyLatches[bindingIndex] = true;
                }
            }
            else
            {
                view.interactionState().saveGameEditKeyLatches[bindingIndex] = false;
            }
        }

        if (pKeyboardState[SDL_SCANCODE_BACKSPACE])
        {
            if (!view.interactionState().saveGameEditBackspaceLatch && !saveGameScreen.editBuffer.empty())
            {
                saveGameScreen.editBuffer.pop_back();
                view.interactionState().saveGameEditBackspaceLatch = true;
            }
        }
        else
        {
            view.interactionState().saveGameEditBackspaceLatch = false;
        }
    }
    else
    {
        view.interactionState().saveGameEditKeyLatches.fill(false);
        view.interactionState().saveGameEditBackspaceLatch = false;
    }

    const HudPointerState savePointerState = pointerStateFromInput(input);
    const GameplaySaveLoadPointerTarget noneSaveTarget = {};
    const auto findSavePointerTarget =
        [&view, screenWidth, screenHeight](float pointerX, float pointerY) -> GameplaySaveLoadPointerTarget
        {
            for (size_t row = 0; row < SaveLoadVisibleSlotCount; ++row)
            {
                const std::string layoutId = "SaveGameSlotRow" + std::to_string(row);
                GameplaySaveLoadPointerTarget target = resolveSaveLoadPointerTarget(
                    view,
                    screenWidth,
                    screenHeight,
                    layoutId.c_str(),
                    GameplaySaveLoadPointerTargetType::Slot,
                    pointerX,
                    pointerY);

                if (target.type != GameplaySaveLoadPointerTargetType::None)
                {
                    target.slotIndex = row;
                    return target;
                }
            }

            GameplaySaveLoadPointerTarget target = resolveSaveLoadPointerTarget(
                view,
                screenWidth,
                screenHeight,
                "SaveGameScrollUpButton",
                GameplaySaveLoadPointerTargetType::ScrollUpButton,
                pointerX,
                pointerY);

            if (target.type != GameplaySaveLoadPointerTargetType::None)
            {
                return target;
            }

            target = resolveSaveLoadPointerTarget(
                view,
                screenWidth,
                screenHeight,
                "SaveGameScrollDownButton",
                GameplaySaveLoadPointerTargetType::ScrollDownButton,
                pointerX,
                pointerY);

            if (target.type != GameplaySaveLoadPointerTargetType::None)
            {
                return target;
            }

            target = resolveSaveLoadPointerTarget(
                view,
                screenWidth,
                screenHeight,
                "SaveGameConfirmButton",
                GameplaySaveLoadPointerTargetType::ConfirmButton,
                pointerX,
                pointerY);

            if (target.type != GameplaySaveLoadPointerTargetType::None)
            {
                return target;
            }

            return resolveSaveLoadPointerTarget(
                view,
                screenWidth,
                screenHeight,
                "SaveGameCancelButton",
                GameplaySaveLoadPointerTargetType::CancelButton,
                pointerX,
                pointerY);
        };

    handlePointerClickRelease(
        savePointerState,
        view.interactionState().saveGameClickLatch,
        view.interactionState().saveGamePressedTarget,
        noneSaveTarget,
        findSavePointerTarget,
        [&view, &saveGameScreen](const GameplaySaveLoadPointerTarget &target)
        {
            switch (target.type)
            {
            case GameplaySaveLoadPointerTargetType::Slot:
                if (!saveGameScreen.slots.empty())
                {
                    const size_t slotIndex = std::min(target.slotIndex, saveGameScreen.slots.size() - 1);

                    if (saveGameScreen.editActive && saveGameScreen.editSlotIndex != slotIndex)
                    {
                        saveGameScreen.editActive = false;
                        saveGameScreen.editBuffer.clear();
                    }

                    saveGameScreen.selectedIndex = slotIndex;
                    const uint64_t nowTicks = SDL_GetTicks();

                    if (view.interactionState().lastSaveGameClickedSlotIndex == slotIndex
                        && nowTicks - view.interactionState().lastSaveGameSlotClickTicks <= SaveGameDoubleClickWindowMs)
                    {
                        saveGameScreen.editActive = true;
                        saveGameScreen.editSlotIndex = slotIndex;
                        saveGameScreen.editBuffer =
                            saveGameScreen.slots[slotIndex].fileLabel == "Empty"
                                ? std::string()
                                : saveGameScreen.slots[slotIndex].fileLabel;
                    }

                    view.interactionState().lastSaveGameSlotClickTicks = nowTicks;
                    view.interactionState().lastSaveGameClickedSlotIndex = slotIndex;
                }
                break;

            case GameplaySaveLoadPointerTargetType::ScrollUpButton:
            case GameplaySaveLoadPointerTargetType::ScrollDownButton:
                break;

            case GameplaySaveLoadPointerTargetType::ConfirmButton:
                if (saveGameScreen.editActive && saveGameScreen.editSlotIndex < saveGameScreen.slots.size())
                {
                    saveGameScreen.slots[saveGameScreen.editSlotIndex].fileLabel =
                        saveGameScreen.editBuffer.empty()
                            ? "Empty"
                            : saveGameScreen.editBuffer;
                }

                view.trySaveToSelectedGameSlot();
                break;

            case GameplaySaveLoadPointerTargetType::CancelButton:
                view.closeSaveGameOverlay();
                break;

            case GameplaySaveLoadPointerTargetType::None:
                break;
            }
        });

    return true;
}

bool GameplayOverlayInputController::handleJournalOverlayInput(
    GameplayScreenRuntime &view,
    const GameplayInputFrame &input,
    bool canToggleJournal,
    bool mapShortcutPressed,
    bool storyShortcutPressed,
    bool notesShortcutPressed,
    bool zoomInPressed,
    bool zoomOutPressed,
    float mouseWheelDelta)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;
    GameplayUiController::JournalScreenState &journalScreen = view.journalScreenState();
    JournalShortcutView requestedJournalView = JournalShortcutView::None;

    if (mapShortcutPressed)
    {
        requestedJournalView = JournalShortcutView::Map;
    }
    else if (storyShortcutPressed)
    {
        requestedJournalView = JournalShortcutView::Story;
    }
    else if (notesShortcutPressed)
    {
        requestedJournalView = JournalShortcutView::Notes;
    }

    if (requestedJournalView != JournalShortcutView::None)
    {
        if (!view.interactionState().journalToggleLatch)
        {
            const auto activateJournalView =
                [&view, &journalScreen](JournalShortcutView targetView)
                {
                    if (!journalScreen.active)
                    {
                        view.openJournalOverlay();
                    }

                    switch (targetView)
                    {
                    case JournalShortcutView::Map:
                        journalScreen.view = GameplayUiController::JournalView::Map;
                        break;

                    case JournalShortcutView::Story:
                        journalScreen.view = GameplayUiController::JournalView::Story;
                        journalScreen.mapDragActive = false;
                        break;

                    case JournalShortcutView::Notes:
                        journalScreen.view = GameplayUiController::JournalView::Notes;
                        journalScreen.mapDragActive = false;
                        break;

                    case JournalShortcutView::None:
                        break;
                    }
                };

            const auto currentJournalView =
                [&journalScreen]() -> JournalShortcutView
                {
                    if (!journalScreen.active)
                    {
                        return JournalShortcutView::None;
                    }

                    switch (journalScreen.view)
                    {
                    case GameplayUiController::JournalView::Map:
                        return JournalShortcutView::Map;

                    case GameplayUiController::JournalView::Story:
                        return JournalShortcutView::Story;

                    case GameplayUiController::JournalView::Notes:
                        return JournalShortcutView::Notes;

                    case GameplayUiController::JournalView::Quests:
                        return JournalShortcutView::None;
                    }

                    return JournalShortcutView::None;
                };

            if (journalScreen.active && requestedJournalView == JournalShortcutView::Map)
            {
                view.closeJournalOverlay();
            }
            else if (journalScreen.active
                && currentJournalView() == requestedJournalView
                && requestedJournalView != JournalShortcutView::Map)
            {
                view.closeJournalOverlay();
            }
            else if (canToggleJournal || journalScreen.active)
            {
                activateJournalView(requestedJournalView);
            }

            view.interactionState().journalToggleLatch = true;
        }
    }
    else
    {
        view.interactionState().journalToggleLatch = false;
    }

    if (!journalScreen.active)
    {
        view.interactionState().journalClickLatch = false;
        view.interactionState().journalPressedTarget = {};
        view.interactionState().journalMapKeyZoomLatch = false;
        return false;
    }

    const auto adjustPage =
        [&journalScreen](int delta)
        {
            if (journalScreen.view == GameplayUiController::JournalView::Quests)
            {
                if (delta < 0 && journalScreen.questPage > 0)
                {
                    --journalScreen.questPage;
                }
                else if (delta > 0)
                {
                    ++journalScreen.questPage;
                }
            }
            else if (journalScreen.view == GameplayUiController::JournalView::Story)
            {
                if (delta < 0 && journalScreen.storyPage > 0)
                {
                    --journalScreen.storyPage;
                }
                else if (delta > 0)
                {
                    ++journalScreen.storyPage;
                }
            }
            else if (journalScreen.view == GameplayUiController::JournalView::Notes)
            {
                if (delta < 0 && journalScreen.notesPage > 0)
                {
                    --journalScreen.notesPage;
                }
                else if (delta > 0)
                {
                    ++journalScreen.notesPage;
                }
            }
        };

    if (journalScreen.view == GameplayUiController::JournalView::Map)
    {
        if (zoomInPressed && !view.interactionState().journalMapKeyZoomLatch)
        {
            journalScreen.mapZoomStep =
                std::min(journalScreen.mapZoomStep + 1, static_cast<int>(GameplayJournalMapZoomLevels.size()) - 1);
            clampJournalMapState(journalScreen);
            journalScreen.cachedMapValid = false;
            view.interactionState().journalMapKeyZoomLatch = true;
        }
        else if (zoomOutPressed && !view.interactionState().journalMapKeyZoomLatch)
        {
            journalScreen.mapZoomStep = std::max(journalScreen.mapZoomStep - 1, 0);
            clampJournalMapState(journalScreen);
            journalScreen.cachedMapValid = false;
            view.interactionState().journalMapKeyZoomLatch = true;
        }
        else if (!zoomInPressed && !zoomOutPressed)
        {
            view.interactionState().journalMapKeyZoomLatch = false;
        }

        if (mouseWheelDelta > 0.0f)
        {
            journalScreen.mapZoomStep =
                std::min(journalScreen.mapZoomStep + 1, static_cast<int>(GameplayJournalMapZoomLevels.size()) - 1);
            clampJournalMapState(journalScreen);
            journalScreen.cachedMapValid = false;
        }
        else if (mouseWheelDelta < 0.0f)
        {
            journalScreen.mapZoomStep = std::max(journalScreen.mapZoomStep - 1, 0);
            clampJournalMapState(journalScreen);
            journalScreen.cachedMapValid = false;
        }
    }
    else
    {
        view.interactionState().journalMapKeyZoomLatch = false;
    }

    if (pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_ESCAPE])
    {
        if (!view.interactionState().closeOverlayLatch)
        {
            view.closeJournalOverlay();
            view.interactionState().closeOverlayLatch = true;
        }
    }
    else
    {
        view.interactionState().closeOverlayLatch = false;
    }

    if (!journalScreen.active)
    {
        return true;
    }

    if (screenWidth <= 0 || screenHeight <= 0)
    {
        view.interactionState().journalClickLatch = false;
        view.interactionState().journalPressedTarget = {};
        return true;
    }

    const HudPointerState journalPointerState = pointerStateFromInput(input);
    const GameplayJournalPointerTarget noneJournalTarget = {};

    const auto resolveJournalTarget =
        [&view, screenWidth, screenHeight](
            const std::string &layoutId,
            GameplayJournalPointerTargetType targetType,
            float pointerX,
            float pointerY) -> GameplayJournalPointerTarget
        {
            const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

            if (pLayout == nullptr)
            {
                return {};
            }

            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                view.resolveHudLayoutElement(
                    layoutId,
                    screenWidth,
                    screenHeight,
                    pLayout->width,
                    pLayout->height);

            if (!resolved || !view.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
            {
                return {};
            }

            return {targetType};
        };

    const auto findJournalPointerTarget =
        [&journalScreen, &resolveJournalTarget](float pointerX, float pointerY) -> GameplayJournalPointerTarget
        {
            static const std::pair<const char *, GameplayJournalPointerTargetType> CommonTargets[] = {
                {"JournalMainViewMap", GameplayJournalPointerTargetType::MainMapView},
                {"JournalMainViewQuests", GameplayJournalPointerTargetType::MainQuestsView},
                {"JournalMainViewStory", GameplayJournalPointerTargetType::MainStoryView},
                {"JournalMainViewNotes", GameplayJournalPointerTargetType::MainNotesView},
                {"JournalCloseButton", GameplayJournalPointerTargetType::CloseButton},
            };
            static const std::pair<const char *, GameplayJournalPointerTargetType> MapTargets[] = {
                {"JournalMapZoomInButton", GameplayJournalPointerTargetType::MapZoomInButton},
                {"JournalMapZoomOutButton", GameplayJournalPointerTargetType::MapZoomOutButton},
            };
            static const std::pair<const char *, GameplayJournalPointerTargetType> PageTargets[] = {
                {"JournalPrevPageButton", GameplayJournalPointerTargetType::PrevPageButton},
                {"JournalNextPageButton", GameplayJournalPointerTargetType::NextPageButton},
            };
            static const std::pair<const char *, GameplayJournalPointerTargetType> NotesTargets[] = {
                {"JournalNotesPotionButton", GameplayJournalPointerTargetType::NotesPotionButton},
                {"JournalNotesFountainButton", GameplayJournalPointerTargetType::NotesFountainButton},
                {"JournalNotesObeliskButton", GameplayJournalPointerTargetType::NotesObeliskButton},
                {"JournalNotesSeerButton", GameplayJournalPointerTargetType::NotesSeerButton},
                {"JournalNotesMiscButton", GameplayJournalPointerTargetType::NotesMiscButton},
                {"JournalNotesTrainerButton", GameplayJournalPointerTargetType::NotesTrainerButton},
            };

            for (const auto &[layoutId, targetType] : CommonTargets)
            {
                const GameplayJournalPointerTarget target =
                    resolveJournalTarget(layoutId, targetType, pointerX, pointerY);

                if (target.type != GameplayJournalPointerTargetType::None)
                {
                    return target;
                }
            }

            if (journalScreen.view == GameplayUiController::JournalView::Map)
            {
                for (const auto &[layoutId, targetType] : MapTargets)
                {
                    const GameplayJournalPointerTarget target =
                        resolveJournalTarget(layoutId, targetType, pointerX, pointerY);

                    if (target.type != GameplayJournalPointerTargetType::None)
                    {
                        return target;
                    }
                }
            }
            else
            {
                for (const auto &[layoutId, targetType] : PageTargets)
                {
                    const GameplayJournalPointerTarget target =
                        resolveJournalTarget(layoutId, targetType, pointerX, pointerY);

                    if (target.type != GameplayJournalPointerTargetType::None)
                    {
                        return target;
                    }
                }

                if (journalScreen.view == GameplayUiController::JournalView::Notes)
                {
                    for (const auto &[layoutId, targetType] : NotesTargets)
                    {
                        const GameplayJournalPointerTarget target =
                            resolveJournalTarget(layoutId, targetType, pointerX, pointerY);

                        if (target.type != GameplayJournalPointerTargetType::None)
                        {
                            return target;
                        }
                    }
                }
            }

            return {};
        };

    const auto resolveJournalViewport =
        [&view, screenWidth, screenHeight]() -> std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement>
        {
            const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement("JournalMapViewport");

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            return view.resolveHudLayoutElement(
                "JournalMapViewport",
                screenWidth,
                screenHeight,
                pLayout->width,
                pLayout->height);
        };

    const auto activateJournalTarget =
        [&view, &journalScreen, &adjustPage](const GameplayJournalPointerTarget &target)
        {
            switch (target.type)
            {
            case GameplayJournalPointerTargetType::MainMapView:
                journalScreen.view = GameplayUiController::JournalView::Map;
                break;

            case GameplayJournalPointerTargetType::MainQuestsView:
                journalScreen.view = GameplayUiController::JournalView::Quests;
                journalScreen.mapDragActive = false;
                break;

            case GameplayJournalPointerTargetType::MainStoryView:
                journalScreen.view = GameplayUiController::JournalView::Story;
                journalScreen.mapDragActive = false;
                break;

            case GameplayJournalPointerTargetType::MainNotesView:
                journalScreen.view = GameplayUiController::JournalView::Notes;
                journalScreen.mapDragActive = false;
                break;

            case GameplayJournalPointerTargetType::PrevPageButton:
                adjustPage(-1);
                break;

            case GameplayJournalPointerTargetType::NextPageButton:
                adjustPage(1);
                break;

            case GameplayJournalPointerTargetType::NotesPotionButton:
                journalScreen.view = GameplayUiController::JournalView::Notes;
                journalScreen.notesCategory = GameplayUiController::JournalNotesCategory::Potion;
                journalScreen.notesPage = 0;
                break;

            case GameplayJournalPointerTargetType::NotesFountainButton:
                journalScreen.view = GameplayUiController::JournalView::Notes;
                journalScreen.notesCategory = GameplayUiController::JournalNotesCategory::Fountain;
                journalScreen.notesPage = 0;
                break;

            case GameplayJournalPointerTargetType::NotesObeliskButton:
                journalScreen.view = GameplayUiController::JournalView::Notes;
                journalScreen.notesCategory = GameplayUiController::JournalNotesCategory::Obelisk;
                journalScreen.notesPage = 0;
                break;

            case GameplayJournalPointerTargetType::NotesSeerButton:
                journalScreen.view = GameplayUiController::JournalView::Notes;
                journalScreen.notesCategory = GameplayUiController::JournalNotesCategory::Seer;
                journalScreen.notesPage = 0;
                break;

            case GameplayJournalPointerTargetType::NotesMiscButton:
                journalScreen.view = GameplayUiController::JournalView::Notes;
                journalScreen.notesCategory = GameplayUiController::JournalNotesCategory::Misc;
                journalScreen.notesPage = 0;
                break;

            case GameplayJournalPointerTargetType::NotesTrainerButton:
                journalScreen.view = GameplayUiController::JournalView::Notes;
                journalScreen.notesCategory = GameplayUiController::JournalNotesCategory::Trainer;
                journalScreen.notesPage = 0;
                break;

            case GameplayJournalPointerTargetType::MapZoomInButton:
                journalScreen.view = GameplayUiController::JournalView::Map;
                journalScreen.mapZoomStep =
                    std::min(journalScreen.mapZoomStep + 1, static_cast<int>(GameplayJournalMapZoomLevels.size()) - 1);

                if (view.worldRuntime() != nullptr)
                {
                    journalScreen.mapCenterX = view.worldRuntime()->partyX();
                    journalScreen.mapCenterY = view.worldRuntime()->partyY();
                }

                clampJournalMapState(journalScreen);
                journalScreen.cachedMapValid = false;
                break;

            case GameplayJournalPointerTargetType::MapZoomOutButton:
                journalScreen.view = GameplayUiController::JournalView::Map;
                journalScreen.mapZoomStep = std::max(journalScreen.mapZoomStep - 1, 0);

                if (view.worldRuntime() != nullptr)
                {
                    journalScreen.mapCenterX = view.worldRuntime()->partyX();
                    journalScreen.mapCenterY = view.worldRuntime()->partyY();
                }

                clampJournalMapState(journalScreen);
                journalScreen.cachedMapValid = false;
                break;

            case GameplayJournalPointerTargetType::CloseButton:
                view.closeJournalOverlay();
                break;

            case GameplayJournalPointerTargetType::None:
                break;
            }
        };

    const auto isImmediateJournalMapTarget =
        [](const GameplayJournalPointerTarget &target) -> bool
        {
            switch (target.type)
            {
            case GameplayJournalPointerTargetType::MapZoomInButton:
            case GameplayJournalPointerTargetType::MapZoomOutButton:
                return true;

            case GameplayJournalPointerTargetType::None:
            case GameplayJournalPointerTargetType::MainMapView:
            case GameplayJournalPointerTargetType::MainQuestsView:
            case GameplayJournalPointerTargetType::MainStoryView:
            case GameplayJournalPointerTargetType::MainNotesView:
            case GameplayJournalPointerTargetType::PrevPageButton:
            case GameplayJournalPointerTargetType::NextPageButton:
            case GameplayJournalPointerTargetType::NotesPotionButton:
            case GameplayJournalPointerTargetType::NotesFountainButton:
            case GameplayJournalPointerTargetType::NotesObeliskButton:
            case GameplayJournalPointerTargetType::NotesSeerButton:
            case GameplayJournalPointerTargetType::NotesMiscButton:
            case GameplayJournalPointerTargetType::NotesTrainerButton:
            case GameplayJournalPointerTargetType::CloseButton:
                return false;
            }

            return false;
        };

    if (journalScreen.mapDragActive)
    {
        if (journalPointerState.leftButtonPressed)
        {
            const int zoom = GameplayJournalMapZoomLevels[journalScreen.mapZoomStep];
            const float zoomFactor = static_cast<float>(zoom) / 384.0f;
            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> mapViewport = resolveJournalViewport();
            const float viewportWidth = mapViewport.has_value() ? mapViewport->width : 336.0f;
            const float viewportHeight = mapViewport.has_value() ? mapViewport->height : 336.0f;
            const float worldUnitsPerPixelX =
                (GameplayJournalMapWorldHalfExtent * 2.0f) / (zoomFactor * std::max(1.0f, viewportWidth));
            const float worldUnitsPerPixelY =
                (GameplayJournalMapWorldHalfExtent * 2.0f) / (zoomFactor * std::max(1.0f, viewportHeight));
            const float deltaX = journalPointerState.x - journalScreen.mapDragStartMouseX;
            const float deltaY = journalPointerState.y - journalScreen.mapDragStartMouseY;
            const float previousCenterX = journalScreen.mapCenterX;
            const float previousCenterY = journalScreen.mapCenterY;

            journalScreen.mapCenterX = journalScreen.mapDragStartCenterX - deltaX * worldUnitsPerPixelX;
            journalScreen.mapCenterY = journalScreen.mapDragStartCenterY - deltaY * worldUnitsPerPixelY;
            clampJournalMapState(journalScreen);

            if (std::abs(journalScreen.mapCenterX - previousCenterX) > 0.01f
                || std::abs(journalScreen.mapCenterY - previousCenterY) > 0.01f)
            {
                journalScreen.cachedMapValid = false;
            }
        }
        else
        {
            journalScreen.mapDragActive = false;
            view.interactionState().journalClickLatch = false;
            view.interactionState().journalPressedTarget = noneJournalTarget;
        }

        return true;
    }

    if (journalPointerState.leftButtonPressed && !view.interactionState().journalClickLatch)
    {
        const GameplayJournalPointerTarget pressedTarget =
            findJournalPointerTarget(journalPointerState.x, journalPointerState.y);

        if (isImmediateJournalMapTarget(pressedTarget))
        {
            activateJournalTarget(pressedTarget);
            view.interactionState().journalClickLatch = true;
            view.interactionState().journalPressedTarget = noneJournalTarget;
            return true;
        }

        if (journalScreen.view == GameplayUiController::JournalView::Map && pressedTarget == noneJournalTarget)
        {
            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> mapViewport = resolveJournalViewport();

            if (mapViewport.has_value()
                && view.isPointerInsideResolvedElement(*mapViewport, journalPointerState.x, journalPointerState.y))
            {
                journalScreen.mapDragActive = true;
                journalScreen.mapDragStartMouseX = journalPointerState.x;
                journalScreen.mapDragStartMouseY = journalPointerState.y;
                journalScreen.mapDragStartCenterX = journalScreen.mapCenterX;
                journalScreen.mapDragStartCenterY = journalScreen.mapCenterY;
                view.interactionState().journalClickLatch = true;
                view.interactionState().journalPressedTarget = noneJournalTarget;
                return true;
            }
        }
    }

    handlePointerClickRelease(
        journalPointerState,
        view.interactionState().journalClickLatch,
        view.interactionState().journalPressedTarget,
        noneJournalTarget,
        findJournalPointerTarget,
        activateJournalTarget);

    return true;
}

void GameplayOverlayInputController::handleDialogueOverlayInput(
    GameplayScreenRuntime &view,
    const GameplayInputFrame &input,
    bool isResidentSelectionMode)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;

    if (view.partyReadOnly() != nullptr)
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
                if (!view.interactionState().eventDialogPartySelectLatches[memberIndex])
                {
                    view.trySelectPartyMember(memberIndex, false);
                    view.interactionState().eventDialogPartySelectLatches[memberIndex] = true;
                }
            }
            else
            {
                view.interactionState().eventDialogPartySelectLatches[memberIndex] = false;
            }
        }
    }
    else
    {
        view.interactionState().eventDialogPartySelectLatches.fill(false);
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

        for (size_t digit = 0; digit < view.interactionState().houseBankDigitLatches.size(); ++digit)
        {
            const bool pressed = pKeyboardState[DigitScancodes[digit]]
                || pKeyboardState[KeypadDigitScancodes[digit]];

            if (pressed)
            {
                if (!view.interactionState().houseBankDigitLatches[digit] && view.houseBankState().inputText.size() < 10)
                {
                    view.houseBankState().inputText.push_back(static_cast<char>('0' + digit));
                }

                view.interactionState().houseBankDigitLatches[digit] = true;
            }
            else
            {
                view.interactionState().houseBankDigitLatches[digit] = false;
            }
        }

        const bool backspacePressed = pKeyboardState[SDL_SCANCODE_BACKSPACE];

        if (backspacePressed)
        {
            if (!view.interactionState().houseBankBackspaceLatch && !view.houseBankState().inputText.empty())
            {
                view.houseBankState().inputText.pop_back();
            }

            view.interactionState().houseBankBackspaceLatch = true;
        }
        else
        {
            view.interactionState().houseBankBackspaceLatch = false;
        }

        const bool confirmPressed = pKeyboardState[SDL_SCANCODE_RETURN] || pKeyboardState[SDL_SCANCODE_KP_ENTER];

        if (confirmPressed)
        {
            if (!view.interactionState().houseBankConfirmLatch)
            {
                view.confirmHouseBankInput();
                view.interactionState().houseBankConfirmLatch = true;
            }
        }
        else
        {
            view.interactionState().houseBankConfirmLatch = false;
        }

        view.refreshHouseBankInputDialog();

        const HudPointerState pointerState = pointerStateFromInput(input);
        const GameplayDialoguePointerTarget noneDialogueTarget = {};
        const auto findDialogueCloseTarget =
            [&view, screenWidth, screenHeight](float mouseX, float mouseY) -> GameplayDialoguePointerTarget
            {
                const GameplayScreenRuntime::HudLayoutElement *pGoodbyeLayout =
                    view.findHudLayoutElement("DialogueGoodbyeButton");
                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedGoodbye =
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
            view.interactionState().dialogueClickLatch,
            view.interactionState().dialoguePressedTarget,
            noneDialogueTarget,
            findDialogueCloseTarget,
            [&view](const GameplayDialoguePointerTarget &target)
            {
                if (target.type == GameplayDialoguePointerTargetType::CloseButton)
                {
                    view.handleDialogueCloseRequest();
                }
            });

        const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE];

        if (closePressed)
        {
            if (!view.interactionState().closeOverlayLatch)
            {
                view.handleDialogueCloseRequest();
                view.interactionState().closeOverlayLatch = true;
            }
        }
        else
        {
            view.interactionState().closeOverlayLatch = false;
        }

        return;
    }

    if (!view.activeEventDialog().actions.empty() && !isResidentSelectionMode)
    {
        if (pKeyboardState[SDL_SCANCODE_UP])
        {
            if (!view.interactionState().eventDialogSelectUpLatch)
            {
                view.eventDialogSelectionIndex() = view.eventDialogSelectionIndex() == 0
                    ? (view.activeEventDialog().actions.size() - 1)
                    : (view.eventDialogSelectionIndex() - 1);
                view.interactionState().eventDialogSelectUpLatch = true;
            }
        }
        else
        {
            view.interactionState().eventDialogSelectUpLatch = false;
        }

        if (pKeyboardState[SDL_SCANCODE_DOWN])
        {
            if (!view.interactionState().eventDialogSelectDownLatch)
            {
                view.eventDialogSelectionIndex() =
                    (view.eventDialogSelectionIndex() + 1) % view.activeEventDialog().actions.size();
                view.interactionState().eventDialogSelectDownLatch = true;
            }
        }
        else
        {
            view.interactionState().eventDialogSelectDownLatch = false;
        }
    }
    else
    {
        view.interactionState().eventDialogSelectUpLatch = false;
        view.interactionState().eventDialogSelectDownLatch = false;
    }

    const bool acceptPressed = pKeyboardState[SDL_SCANCODE_RETURN] || pKeyboardState[SDL_SCANCODE_SPACE];

    if (acceptPressed && !isResidentSelectionMode)
    {
        if (!view.interactionState().eventDialogAcceptLatch)
        {
            if (view.activeEventDialog().actions.empty())
            {
                view.handleDialogueCloseRequest();
            }
            else
            {
                view.executeActiveDialogAction();
            }

            view.interactionState().eventDialogAcceptLatch = true;
        }
    }
    else
    {
        view.interactionState().eventDialogAcceptLatch = false;
    }

    const float dialogMouseX = input.pointerX;
    const float dialogMouseY = input.pointerY;
    const bool isLeftMousePressed = input.leftMouseButton.held;
    const EventRuntimeState *pDialogueEventRuntimeState =
        view.worldRuntime() != nullptr ? view.worldRuntime()->eventRuntimeState() : nullptr;
    const HouseEntry *pDialogueHouseEntry =
        (currentDialogueHostHouseId(pDialogueEventRuntimeState) != 0 && view.houseTable() != nullptr)
        ? view.houseTable()->get(currentDialogueHostHouseId(pDialogueEventRuntimeState))
        : nullptr;

    if (view.houseShopOverlay().active
        && pDialogueHouseEntry != nullptr
        && view.party() != nullptr
        && view.worldRuntime() != nullptr
        && view.itemTable() != nullptr)
    {
        const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedFrame =
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
            Party &party = *view.party();
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

                        const std::optional<GameplayScreenRuntime::HudTextureHandle> itemTexture =
                            view.gameplayUiRuntime().ensureHudTextureLoaded(pItemDefinition->iconName);

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
                        view.gameplayUiRuntime().tryGetOpaqueHudTextureBounds(
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
                view.interactionState().houseShopClickLatch,
                view.interactionState().houseShopPressedSlotIndex,
                std::numeric_limits<size_t>::max(),
                resolveHoveredSlotIndex,
                [&view, pDialogueHouseEntry, stockMode](size_t slotIndex)
                {
                    if (slotIndex == std::numeric_limits<size_t>::max()
                        || view.party() == nullptr
                        || view.itemTable() == nullptr
                        || view.worldRuntime() == nullptr
                        || !stockMode)
                    {
                        return;
                    }

                    std::string statusText;
                    HouseServiceRuntime::tryBuyStockItem(
                        *view.party(),
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
        && view.party() != nullptr)
    {
        const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedInventoryGrid =
            view.resolveInventoryNestedOverlayGridArea(screenWidth, screenHeight);

        if (resolvedInventoryGrid
            && isLeftMousePressed
            && !view.interactionState().inventoryNestedOverlayItemClickLatch
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
                    *view.party(),
                    *view.itemTable(),
                    *view.standardItemEnchantTable(),
                    *view.specialItemEnchantTable(),
                    *pDialogueHouseEntry,
                    view.partyReadOnly()->activeMemberIndex(),
                    gridX,
                    gridY,
                    statusText,
                    &serviceResult);
            }
            else if (view.inventoryNestedOverlay().mode
                == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify)
            {
                HouseServiceRuntime::tryIdentifyInventoryItem(
                    *view.party(),
                    *view.itemTable(),
                    *view.standardItemEnchantTable(),
                    *view.specialItemEnchantTable(),
                    *pDialogueHouseEntry,
                    view.partyReadOnly()->activeMemberIndex(),
                    gridX,
                    gridY,
                    statusText,
                    &serviceResult);
            }
            else if (view.inventoryNestedOverlay().mode
                == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
            {
                HouseServiceRuntime::tryRepairInventoryItem(
                    *view.party(),
                    *view.itemTable(),
                    *view.standardItemEnchantTable(),
                    *view.specialItemEnchantTable(),
                    *pDialogueHouseEntry,
                    view.partyReadOnly()->activeMemberIndex(),
                    gridX,
                    gridY,
                    statusText,
                    &serviceResult);
            }

            const size_t activeMemberIndex = view.partyReadOnly()->activeMemberIndex();

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
                            worldSound(*soundId),
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

            view.interactionState().inventoryNestedOverlayItemClickLatch = true;
        }
        else if (!isLeftMousePressed)
        {
            view.interactionState().inventoryNestedOverlayItemClickLatch = false;
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
                (currentDialogueHostHouseId(pEventRuntimeState) != 0 && view.houseTable() != nullptr)
                ? view.houseTable()->get(currentDialogueHostHouseId(pEventRuntimeState))
                : nullptr;
            const bool showEventDialogPanel =
                isResidentSelectionMode || !view.activeEventDialog().actions.empty() || pHostHouseEntry != nullptr;

            if (isResidentSelectionMode)
            {
                const GameplayScreenRuntime::HudLayoutElement *pEventDialogLayout =
                    view.findHudLayoutElement("DialogueEventDialog");
                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedEventDialog =
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
                const GameplayScreenRuntime::HudLayoutElement *pEventDialogLayout =
                    view.findHudLayoutElement("DialogueEventDialog");
                const GameplayScreenRuntime::HudLayoutElement *pTopicRowLayout =
                    view.findHudLayoutElement("DialogueTopicRow_1");
                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedTopicRowTemplate =
                    pTopicRowLayout != nullptr
                    ? view.resolveHudLayoutElement(
                        "DialogueTopicRow_1",
                        screenWidth,
                        screenHeight,
                        pTopicRowLayout->width,
                        pTopicRowLayout->height)
                    : std::nullopt;
                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedEventDialog =
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
                    if (view.activeEventDialog().presentation == EventDialogPresentation::Transition)
                    {
                        const GameplayScreenRuntime::HudLayoutElement *pOkLayout =
                            view.findHudLayoutElement("DialogueOkButton");
                        const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedOk =
                            pOkLayout != nullptr
                            ? view.resolveHudLayoutElement(
                                "DialogueOkButton",
                                screenWidth,
                                screenHeight,
                                pOkLayout->width,
                                pOkLayout->height)
                            : std::nullopt;

                        if (resolvedOk
                            && !view.activeEventDialog().actions.empty()
                            && mouseX >= resolvedOk->x
                            && mouseX < resolvedOk->x + resolvedOk->width
                            && mouseY >= resolvedOk->y
                            && mouseY < resolvedOk->y + resolvedOk->height)
                        {
                            return {GameplayDialoguePointerTargetType::Action, 0};
                        }
                    }

                    const float panelScale = resolvedEventDialog->scale;
                    const float panelPaddingX = 10.0f * panelScale;
                    const float panelPaddingY = 10.0f * panelScale;
                    const float panelInnerX = resolvedEventDialog->x + panelPaddingX;
                    const float panelInnerY = resolvedEventDialog->y + panelPaddingY;
                    const float panelInnerWidth = resolvedEventDialog->width - panelPaddingX * 2.0f;
                    const float portraitBorderSize = 80.0f * panelScale;
                    const float sectionGap = 8.0f * panelScale;
                    const std::optional<GameplayScreenRuntime::HudFontHandle> topicFont =
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

            const GameplayScreenRuntime::HudLayoutElement *pGoodbyeLayout =
                view.findHudLayoutElement("DialogueGoodbyeButton");
            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedGoodbye =
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
        view.interactionState().dialogueClickLatch,
        view.interactionState().dialoguePressedTarget,
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

    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (closePressed)
    {
        if (!view.interactionState().closeOverlayLatch)
        {
            view.handleDialogueCloseRequest();
            view.interactionState().closeOverlayLatch = true;
        }
    }
    else
    {
        view.interactionState().closeOverlayLatch = false;
    }
}

void GameplayOverlayInputController::handleLootOverlayInput(
    GameplayScreenRuntime &view,
    const GameplayInputFrame &input,
    bool hasActiveLootView)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;

    if (!hasActiveLootView)
    {
        view.resetLootOverlayInteractionState();
        return;
    }

    const GameplayChestViewState *pChestView =
        view.worldRuntime() != nullptr ? view.worldRuntime()->activeChestView() : nullptr;
    const GameplayCorpseViewState *pCorpseView =
        view.worldRuntime() != nullptr ? view.worldRuntime()->activeCorpseView() : nullptr;
    const size_t itemCount =
        pChestView != nullptr ? pChestView->items.size() : (pCorpseView != nullptr ? pCorpseView->items.size() : 0);

    if (pChestView != nullptr && screenWidth > 0 && screenHeight > 0)
    {
        const float chestMouseX = input.pointerX;
        const float chestMouseY = input.pointerY;
        const bool isChestLeftMousePressed = input.leftMouseButton.held;
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
                const GameplayScreenRuntime::HudLayoutElement *pCloseLayout =
                    view.findHudLayoutElement("ChestCloseButton");

                if (pCloseLayout == nullptr)
                {
                    return {};
                }

                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedClose =
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
            && view.party() != nullptr;

        if (inventoryNestedOverlayActive && view.inventoryNestedOverlay().active)
        {
            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedInventoryGrid =
                view.resolveInventoryNestedOverlayGridArea(screenWidth, screenHeight);

            if (resolvedInventoryGrid
                && isChestLeftMousePressed
                && !view.interactionState().inventoryNestedOverlayItemClickLatch
                && chestMouseX >= resolvedInventoryGrid->x
                && chestMouseX < resolvedInventoryGrid->x + resolvedInventoryGrid->width
                && chestMouseY >= resolvedInventoryGrid->y
                && chestMouseY < resolvedInventoryGrid->y + resolvedInventoryGrid->height)
            {
                Party &party = *view.party();
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
                        const std::optional<GameplayScreenRuntime::HudTextureHandle> pItemTexture =
                            view.gameplayUiRuntime().ensureHudTextureLoaded(pItemDefinition->iconName);

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
                            const std::optional<GameplayScreenRuntime::HudTextureHandle> pItemTexture =
                                view.gameplayUiRuntime().ensureHudTextureLoaded(pItemDefinition->iconName);

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

                view.interactionState().inventoryNestedOverlayItemClickLatch = true;
            }
            else if (!isChestLeftMousePressed)
            {
                view.interactionState().inventoryNestedOverlayItemClickLatch = false;
            }
        }

        const GameplayChestPointerTarget noneChestTarget = {};
        handlePointerClickRelease(
            chestPointerState,
            view.interactionState().chestClickLatch,
            view.interactionState().chestPressedTarget,
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
                    view.interactionState().activateInspectLatch = true;
                    view.interactionState().chestSelectionIndex = 0;
                }
            });

        const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedChestGrid =
            view.resolveChestGridArea(screenWidth, screenHeight);
        const GameplayChestPointerTarget hoveredChestTarget =
            findChestPointerTarget(chestMouseX, chestMouseY);

        if (!inventoryNestedOverlayActive
            && resolvedChestGrid
            && isChestLeftMousePressed
            && !view.interactionState().chestItemClickLatch
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
                GameplayChestItemState chestItem = {};
                chestItem.item = view.heldInventoryItem().item;
                chestItem.itemId = view.heldInventoryItem().item.objectDescriptionId;
                chestItem.quantity = view.heldInventoryItem().item.quantity;
                chestItem.width = view.heldInventoryItem().item.width;
                chestItem.height = view.heldInventoryItem().item.height;
                const ItemDefinition *pItemDefinition =
                    view.itemTable() != nullptr ? view.itemTable()->get(view.heldInventoryItem().item.objectDescriptionId) : nullptr;

                if (pItemDefinition != nullptr)
                {
                    const std::optional<GameplayScreenRuntime::HudTextureHandle> pItemTexture =
                        view.gameplayUiRuntime().ensureHudTextureLoaded(pItemDefinition->iconName);

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
            else if (view.worldRuntime() != nullptr && view.party() != nullptr)
            {
                GameplayChestItemState takenItem = {};

                if (view.worldRuntime()->takeActiveChestItemAt(gridX, gridY, takenItem))
                {
                    if (takenItem.isGold)
                    {
                        view.party()->addGold(static_cast<int>(takenItem.goldAmount));
                        view.setStatusBarEvent(formatFoundGoldStatusText(static_cast<int>(takenItem.goldAmount)));

                        if (view.audioSystem() != nullptr)
                        {
                            view.audioSystem()->playCommonSound(SoundId::Gold, GameAudioSystem::PlaybackGroup::Ui);
                        }
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
                            const std::optional<GameplayScreenRuntime::HudTextureHandle> pItemTexture =
                                view.gameplayUiRuntime().ensureHudTextureLoaded(pItemDefinition->iconName);

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

            view.interactionState().chestItemClickLatch = true;
        }
        else if (!isChestLeftMousePressed)
        {
            view.interactionState().chestItemClickLatch = false;
        }
    }
    else
    {
        view.interactionState().chestClickLatch = false;
        view.interactionState().chestItemClickLatch = false;
        view.interactionState().chestPressedTarget = {};
        view.resetInventoryNestedOverlayInteractionState();
    }

    if (itemCount == 0)
    {
        view.interactionState().chestSelectionIndex = 0;
    }
    else if (view.interactionState().chestSelectionIndex >= itemCount)
    {
        view.interactionState().chestSelectionIndex = itemCount - 1;
    }

    if (pKeyboardState[SDL_SCANCODE_UP])
    {
        if (!view.interactionState().chestSelectUpLatch && itemCount > 0)
        {
            view.interactionState().chestSelectionIndex =
                (view.interactionState().chestSelectionIndex == 0) ? (itemCount - 1) : (view.interactionState().chestSelectionIndex - 1);
            view.interactionState().chestSelectUpLatch = true;
        }
    }
    else
    {
        view.interactionState().chestSelectUpLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_DOWN])
    {
        if (!view.interactionState().chestSelectDownLatch && itemCount > 0)
        {
            view.interactionState().chestSelectionIndex = (view.interactionState().chestSelectionIndex + 1) % itemCount;
            view.interactionState().chestSelectDownLatch = true;
        }
    }
    else
    {
        view.interactionState().chestSelectDownLatch = false;
    }

    const bool lootPressed = pKeyboardState[SDL_SCANCODE_RETURN];

    if (lootPressed)
    {
        if (!view.interactionState().lootChestItemLatch
            && !view.inventoryNestedOverlay().active
            && itemCount > 0
            && view.party() != nullptr)
        {
            const GameplayChestViewState *pCurrentChestView =
                view.worldRuntime()->activeChestView();
            const GameplayCorpseViewState *pCurrentCorpseView =
                view.worldRuntime()->activeCorpseView();
            const std::vector<GameplayChestItemState> *pItems = nullptr;

            if (pCurrentChestView != nullptr)
            {
                pItems = &pCurrentChestView->items;
            }
            else if (pCurrentCorpseView != nullptr)
            {
                pItems = &pCurrentCorpseView->items;
            }

            if (pItems != nullptr && view.interactionState().chestSelectionIndex < pItems->size())
            {
                const GameplayChestItemState item = (*pItems)[view.interactionState().chestSelectionIndex];
                bool canLoot = true;

                if (!item.isGold)
                {
                    canLoot = view.party()->tryGrantInventoryItem(item.item);
                }

                if (canLoot)
                {
                    GameplayChestItemState removedItem = {};
                    const bool removed = pCurrentChestView != nullptr
                        ? view.worldRuntime()->takeActiveChestItem(view.interactionState().chestSelectionIndex, removedItem)
                        : view.worldRuntime()->takeActiveCorpseItem(view.interactionState().chestSelectionIndex, removedItem);

                    if (removed)
                    {
                        if (removedItem.isGold)
                        {
                            view.party()->addGold(static_cast<int>(removedItem.goldAmount));
                            view.setStatusBarEvent(formatFoundGoldStatusText(static_cast<int>(removedItem.goldAmount)));

                            if (view.audioSystem() != nullptr)
                            {
                                view.audioSystem()->playCommonSound(SoundId::Gold, GameAudioSystem::PlaybackGroup::Ui);
                            }
                        }

                        const GameplayChestViewState *pUpdatedChestView =
                            view.worldRuntime()->activeChestView();
                        const GameplayCorpseViewState *pUpdatedCorpseView =
                            view.worldRuntime()->activeCorpseView();
                        const std::vector<GameplayChestItemState> *pUpdatedItems = nullptr;

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
                            && view.interactionState().chestSelectionIndex >= pUpdatedItems->size())
                        {
                            view.interactionState().chestSelectionIndex = pUpdatedItems->size() - 1;
                        }
                    }
                }
            }

            view.interactionState().lootChestItemLatch = true;
        }
    }
    else
    {
        view.interactionState().lootChestItemLatch = false;
    }

    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (closePressed)
    {
        if (!view.interactionState().closeOverlayLatch)
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
                view.interactionState().activateInspectLatch = true;
                view.interactionState().chestSelectionIndex = 0;
            }

            view.interactionState().closeOverlayLatch = true;
        }
    }
    else
    {
        view.interactionState().closeOverlayLatch = false;
    }
}
} // namespace OpenYAMM::Game
