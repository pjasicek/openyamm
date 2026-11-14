#pragma once

#include "engine/Utf8Text.h"
#include "game/party/ActionBarSlot.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
// The solo action bar's slot selector (devdocs/solo_action/HUD.md "Slot selector"): Ctrl and a bar key (or a Ctrl
// click on a slot) opens a list of what the member can put on that key. Pure: the runtime (GameplaySoloBarSelector)
// builds the entries once when it opens, this filters them by tab and search and puts the choice on the bar.
enum class SoloBarSelectorTab : uint8_t
{
    All = 0,
    Spells,
    Talents,
    Potions,
    Scrolls,
    Actions,
};

constexpr size_t SoloBarSelectorTabCount = 6;

// One thing the key can hold: the bar slot it makes, its category (never All), its shown name and a short detail
// (a spell's cost, a talent's rank, the carried count), the key of the main row it is on now, and whether none is
// carried (a potion or scroll kind kept on the key).
struct SoloBarSelectorEntry
{
    ActionBarSlot slot;
    SoloBarSelectorTab category = SoloBarSelectorTab::Spells;
    std::string name;
    std::string detail;
    std::optional<size_t> onKey;
    bool noneCarried = false;
};

// One line of the list: a category's heading (only under All) or an entry (its index in the entries).
struct SoloBarSelectorRow
{
    bool heading = false;
    SoloBarSelectorTab category = SoloBarSelectorTab::All;
    size_t entry = 0;

    bool operator==(const SoloBarSelectorRow &) const = default;
};

// The open selector: transient, in GameplayOverlayInteractionState. `entries` are built when it opens; `rows` again
// on a tab or search change. `hoveredButton` is a tab (0-5), the Empty button (6) or Close (7).
struct SoloBarSelectorState
{
    bool open = false;
    size_t slot = 0;
    std::string search;
    SoloBarSelectorTab tab = SoloBarSelectorTab::All;
    std::vector<SoloBarSelectorEntry> entries;
    std::vector<SoloBarSelectorRow> rows;
    size_t scroll = 0;
    std::optional<size_t> hoveredRow;
    std::optional<size_t> hoveredButton;
    // The click that opened or closed it, held: neither the selector nor the world takes it until it is let go.
    bool pointerLatch = false;
    // Escape was down last frame: a press acts once, on its way down.
    bool escapeHeld = false;
    // Ctrl is held over plain gameplay (the selector closed): the game pauses, the cursor is free and every key of the
    // bar is lit, waiting for a click on a key or a key's number.
    bool armed = false;
};

// Whether two bar slots hold the same thing: the spell, the talent, the kind of potion or scroll, the weapon action.
inline bool soloBarSameEntry(const ActionBarSlot &left, const ActionBarSlot &right)
{
    if (left.kind != right.kind || left.kind == ActionBarSlotKind::Empty)
    {
        return false;
    }

    return left.kind == ActionBarSlotKind::Item ? left.item.itemId == right.item.itemId : left.id == right.id;
}

// The key of the main row (0-9) holding the thing, if any.
inline std::optional<size_t> soloBarKeyOf(const std::array<ActionBarSlot, ActionBarSlotCount> &bar,
    const ActionBarSlot &entry)
{
    for (size_t slot = 0; slot < ActionBarSlotCount / 2; ++slot)
    {
        if (soloBarSameEntry(bar[slot], entry))
        {
            return slot;
        }
    }

    return std::nullopt;
}

// Puts the thing on bar slot `slot`, taking it off any other slot that holds it (a move); an empty one clears the slot.
inline void soloBarAssign(std::array<ActionBarSlot, ActionBarSlotCount> &bar, size_t slot, const ActionBarSlot &entry)
{
    if (slot >= ActionBarSlotCount)
    {
        return;
    }

    for (size_t other = 0; other < ActionBarSlotCount; ++other)
    {
        if (other != slot && soloBarSameEntry(bar[other], entry))
        {
            bar[other] = {};
        }
    }

    bar[slot] = entry;
}

// Whether a tab lists anything (the search aside): a tab without entries is disabled. All has every entry.
inline bool soloBarSelectorTabHasEntries(const std::vector<SoloBarSelectorEntry> &entries, SoloBarSelectorTab tab)
{
    for (const SoloBarSelectorEntry &entry : entries)
    {
        if (tab == SoloBarSelectorTab::All || entry.category == tab)
        {
            return true;
        }
    }

    return false;
}

// The lines a tab shows for a search (a case-insensitive part of the shown name): under All each category in tab order
// under its heading, a heading only when something of it matches; the entries keep their given order.
inline std::vector<SoloBarSelectorRow> soloBarSelectorRows(const std::vector<SoloBarSelectorEntry> &entries,
    SoloBarSelectorTab tab, std::string_view search)
{
    const std::string wanted = Engine::Utf8::lower(search);
    std::vector<SoloBarSelectorRow> rows;

    for (size_t category = 1; category < SoloBarSelectorTabCount; ++category)
    {
        const SoloBarSelectorTab shown = SoloBarSelectorTab(category);

        if (tab != SoloBarSelectorTab::All && tab != shown)
        {
            continue;
        }

        bool headed = false;

        for (size_t index = 0; index < entries.size(); ++index)
        {
            const SoloBarSelectorEntry &entry = entries[index];

            if (entry.category != shown
                || (!wanted.empty() && Engine::Utf8::lower(entry.name).find(wanted) == std::string::npos))
            {
                continue;
            }

            if (tab == SoloBarSelectorTab::All && !headed)
            {
                rows.push_back({true, shown, 0});
                headed = true;
            }

            rows.push_back({false, shown, index});
        }
    }

    return rows;
}
}
