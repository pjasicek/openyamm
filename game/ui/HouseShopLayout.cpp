#include "game/ui/HouseShopLayout.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
bool isHouseType(const HouseEntry &houseEntry, const char *pTypeName)
{
    return houseEntry.type == pTypeName;
}
}

HouseShopVisualLayout buildHouseShopVisualLayout(const HouseEntry &houseEntry, bool spellbookMode)
{
    HouseShopVisualLayout layout = {};

    if (spellbookMode || houseEntry.vendorStockProfile == VendorStockProfile::Mm9Library)
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

    if (houseEntry.vendorStockProfile == VendorStockProfile::Weapon
        || isHouseType(houseEntry, "Weapon Shop"))
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
            slot.fitToSlot = false;
            layout.slots.push_back(slot);
        }

        return layout;
    }

    if (houseEntry.vendorStockProfile == VendorStockProfile::Armor
        || isHouseType(houseEntry, "Armor Shop"))
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

    if (houseEntry.vendorStockProfile == VendorStockProfile::Mm9Apothecary
        || houseEntry.vendorStockProfile == VendorStockProfile::Mm9GeneralStore
        || isHouseType(houseEntry, "Magic Shop")
        || isHouseType(houseEntry, "Alchemist"))
    {
        layout.backgroundAsset = "GENSHELF";
        const size_t columnCount = houseEntry.vendorStockProfile == VendorStockProfile::Mm9GeneralStore ? 4 : 6;
        const float columnWidth = 450.0f / static_cast<float>(columnCount);

        for (size_t index = 0; index < columnCount; ++index)
        {
            HouseShopSlotLayout topRowSlot = {};
            topRowSlot.x = 6.0f + static_cast<float>(index) * columnWidth;
            topRowSlot.y = 63.0f;
            topRowSlot.width = columnWidth - 1.0f;
            topRowSlot.height = 132.0f;
            topRowSlot.baselineY = 201.0f;
            topRowSlot.verticalAlign = HouseShopVerticalAlign::Baseline;
            layout.slots.push_back(topRowSlot);
        }

        for (size_t index = 0; index < columnCount; ++index)
        {
            HouseShopSlotLayout bottomRowSlot = {};
            bottomRowSlot.x = 6.0f + static_cast<float>(index) * columnWidth;
            bottomRowSlot.y = 192.0f;
            bottomRowSlot.width = columnWidth - 1.0f;
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
    const float itemScale = slot.fitToSlot ? std::min(frameScale, fitScale) : frameScale;
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
            // An item taller than its slot rises until its opaque bottom rests on the slot floor.
            result.y = std::round(std::min(slotY - opaqueTop, slotY + slotHeight - opaqueBottom));
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
}
