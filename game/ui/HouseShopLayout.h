#pragma once

#include "game/tables/HouseTable.h"

#include <cstddef>
#include <limits>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
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
    // Shrinks items larger than the slot. Weapon tables keep native size and raise tall items instead.
    bool fitToSlot = true;
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

// Slot positions are in the 460x344 shop frame's logical coordinates.
HouseShopVisualLayout buildHouseShopVisualLayout(const HouseEntry &houseEntry, bool spellbookMode);

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
    int opaqueMaxY);
}
