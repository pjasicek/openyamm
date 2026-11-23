#pragma once

#include "game/party/ActionBarSlot.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <optional>

namespace OpenYAMM::Game
{
// The solo run's HUD geometry (devdocs/solo_action/HUD.md), in layout units of the 480-high reference (1.875 screen
// pixels at 1600 x 900). Pure: the renderer places it on resolved layout elements, the tests check it alone.
struct SoloHudRect
{
    float x = 0;
    float y = 0;
    float width = 0;
    float height = 0;

    bool contains(float pointX, float pointY) const
    {
        return pointX >= x && pointX < x + width && pointY >= y && pointY < y + height;
    }
};

// The unit frame (the study's frame=wow, level_generation/ui/solo_action_hud_20261113): an oval medallion overlapping
// the left end of a framed box with the name row and the HP and SP bars; the level coin at the medallion's foot, the
// weapon socket at its shoulder; the buff and debuff rows under the box. Origin: the SoloUnitFrame element's top left.
struct SoloUnitFrameLayout
{
    SoloHudRect medallion;
    SoloHudRect face;
    SoloHudRect box;
    SoloHudRect name;
    SoloHudRect health;
    SoloHudRect mana;
    SoloHudRect coin;
    SoloHudRect weapon;
    // The scroll and potion buttons on the medallion's upper-left rim, mirroring the coin at its foot (the study's
    // lbar=corner); they open the potion and scroll popups (GameplayQuickItems).
    SoloHudRect scrollSocket;
    SoloHudRect potionSocket;
    // The centre of the class counter's row of gems (MAW's combo points and Elementalist stacks): on the box's top
    // edge over the bars, right of the weapon socket (MAW's map progress holds the bottom band).
    float counterX = 0;
    float counterY = 0;
    float buffX = 0;
    float buffY = 0;
    float debuffY = 0;
    float tile = 0;
    float tileGap = 0;
};

inline SoloUnitFrameLayout soloUnitFrameLayout()
{
    SoloUnitFrameLayout layout;
    layout.medallion = {0, 0, 64, 83.2f};
    // The whole head inside the ring: the ring's stroke and a hair of air, no crop beyond the oval.
    layout.face = {3.2f, 3.2f, 57.6f, 76.8f};
    layout.box = {50.1f, 15.5f, 168.5f, 52.3f};
    const float innerX = layout.box.x + 22.4f;
    const float innerWidth = layout.box.width - 22.4f - 6.4f;
    layout.name = {innerX, layout.box.y + 5.9f, innerWidth, 12.8f};
    layout.health = {innerX, layout.box.y + 20.3f, innerWidth, 12.8f};
    layout.mana = {innerX, layout.box.y + 34.1f, innerWidth, 10.7f};
    layout.coin = {-2.1f, 64.0f, 20.3f, 20.3f};
    layout.weapon = {57.6f, layout.box.y - 4.3f, 14.9f, 14.9f};
    layout.scrollSocket = {-4.3f, 0, 18.1f, 18.1f};
    layout.potionSocket = {-7.5f, 22.4f, 18.1f, 18.1f};
    layout.counterX = innerX + innerWidth / 2;
    layout.counterY = layout.box.y;
    layout.buffX = 71.5f;
    layout.buffY = layout.box.y + layout.box.height + 5.3f;
    // Bigger tiles, closer together (the user, 2026-11-14): seven to a row under the box, the timer under each.
    layout.debuffY = layout.buffY + 25.0f;
    layout.tile = 17.0f;
    layout.tileGap = 2.4f;
    return layout;
}

// The action bar's grid inside its panel: the panel's size (the SoloActionBar element) and the slot, gap and
// padding (SoloActionSlot, SoloActionSlotRight, SoloActionSlotBelow) decide the columns and rows. A panel one slot wide
// is the left column of keys 1-0 (the user's layout); a wider one gives a 2 x 5, one-row
// or 2 x 10 bar is a layout change.
struct SoloActionBarGrid
{
    size_t columns = 5;
    size_t rows = 2;
    float slot = 27.7f;
    float gapX = 3.2f;
    float gapY = 4.3f;
    float padX = 12;
    float padY = 11;
};

inline SoloActionBarGrid soloActionBarGrid(float barWidth, float barHeight, float slot, float gapX, float gapY,
    float padX, float padY)
{
    SoloActionBarGrid grid;
    grid.slot = std::max(slot, 1.0f);
    grid.gapX = std::max(gapX, 0.0f);
    grid.gapY = std::max(gapY, 0.0f);
    grid.padX = std::max(padX, 0.0f);
    grid.padY = std::max(padY, 0.0f);
    const float columns = std::floor((barWidth - 2 * grid.padX + grid.gapX) / (grid.slot + grid.gapX) + 0.01f);
    const float rows = std::floor((barHeight - 2 * grid.padY + grid.gapY) / (grid.slot + grid.gapY) + 0.01f);
    grid.columns = size_t(std::clamp(columns, 1.0f, 10.0f));
    grid.rows = size_t(std::clamp(rows, 1.0f, grid.columns == 1 ? 10.0f : 2.0f));
    return grid;
}

// A slot's rectangle by its row (0 the top) and column, from the panel's top left.
inline SoloHudRect soloActionSlotRect(const SoloActionBarGrid &grid, size_t row, size_t column)
{
    return {grid.padX + float(column) * (grid.slot + grid.gapX), grid.padY + float(row) * (grid.slot + grid.gapY),
        grid.slot, grid.slot};
}

// Which of the character's bar slots (Character::actionBar) a grid cell shows. Five columns: keys 1-5 over 6-0
// (slots 0-9). Ten columns: the main row 1-0 at the bottom (slots 0-9) and the second row (slots 10-19) above it.
inline size_t soloActionBarSlotAt(const SoloActionBarGrid &grid, size_t row, size_t column)
{
    if (grid.columns >= 10)
    {
        return row + 1 == grid.rows ? column : ActionBarSlotCount / 2 + column;
    }

    return std::min(row * grid.columns + column, ActionBarSlotCount - 1);
}

// The number key (0-9 for keys 1-0) a bar slot is pressed with on the main row; none for the second row.
inline std::optional<size_t> soloActionBarKeyOfSlot(size_t slot)
{
    return slot < ActionBarSlotCount / 2 ? std::optional<size_t>(slot) : std::nullopt;
}

// The status line's top (screen pixels): where it is, or `gap` above the action bar when the bar lies under it (the
// touch layout's bar at the bottom centre; the desktop column at the left edge never does).
inline float soloStatusLineTop(const SoloHudRect &line, const SoloHudRect &bar, float gap)
{
    const bool overlaps = line.x < bar.x + bar.width && bar.x < line.x + line.width && line.y < bar.y + bar.height
        && bar.y < line.y + line.height;
    return overlaps ? std::min(line.y, bar.y - gap - line.height) : line.y;
}

// How far a recovery has run, 0 just begun to 1 ready, for the crosshair brackets and the slots' wedge.
inline float soloRecoveryProgress(float remainingSeconds, float totalSeconds)
{
    if (remainingSeconds <= 0 || totalSeconds <= 0)
    {
        return 1;
    }

    return std::clamp(1 - remainingSeconds / totalSeconds, 0.0f, 1.0f);
}

// A buff tile's sweep: the share of its duration spent, from the longest remaining time seen since it began.
inline float soloBuffSpent(float remainingSeconds, float longestSeenSeconds)
{
    if (longestSeenSeconds <= 0)
    {
        return 0;
    }

    return std::clamp(1 - remainingSeconds / longestSeenSeconds, 0.0f, 1.0f);
}
}
