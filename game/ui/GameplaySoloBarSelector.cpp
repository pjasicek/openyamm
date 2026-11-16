#include "game/ui/GameplaySoloBarSelector.h"

#include "engine/Localization.h"
#include "engine/Utf8Text.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/QuickItemSlots.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SkillData.h"
#include "game/party/SpellSchool.h"
#include "game/rules/GameRules.h"
#include "game/rules/ItemRules.h"
#include "game/rules/SoloTalents.h"
#include "game/tables/ItemTable.h"
#include "game/tables/SpellTable.h"
#include "game/ui/GameplayObsidianPainter.h"
#include "game/ui/GameplaySoloHud.h"
#include "game/ui/SoloBarSelectorModel.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
using GameplayObsidianColors::abgr;
using GameplayObsidianColors::Body;
using GameplayObsidianColors::Gold;
using GameplayObsidianColors::Ivory;
using GameplayObsidianColors::Label;
using GameplayObsidianColors::Muted;

// The potion and scroll popups' colours (GameplayQuickItems), so the selector reads as one of them.
constexpr uint32_t Brass = abgr(0xa8915c);
constexpr uint32_t BrassDark = abgr(0x6f5f3a);
constexpr uint32_t PanelFill = abgr(0x070e0e, 0xf0);
constexpr uint32_t OuterFill = abgr(0x1a1f1a, 0xf0);
constexpr uint32_t RowFill = abgr(0x111c1b, 0xd8);
constexpr uint32_t RowBorder = abgr(0x263027);
constexpr uint32_t ChipFill = abgr(0x0d1716, 0xcc);
constexpr uint32_t ChipBorder = abgr(0x5d6449);
constexpr uint32_t ChipOnFill = abgr(0x2b2a1a, 0xcc);
constexpr uint32_t ChipOnBorder = abgr(0xd6bb80);
constexpr uint32_t Rule = abgr(0x3a4234);
constexpr uint32_t Track = abgr(0x2a3829);
constexpr uint32_t Thumb = abgr(0x6a8dac);
constexpr uint32_t Disabled = abgr(0x5d6449);
constexpr uint32_t IconBack = abgr(0x0b1012);

constexpr char TextFont[] = "alegreya_semibold";
constexpr char NameFont[] = "Arrus";

// The window in the HUD's layout units (the bar's scale): its width, the list's rows and the bands above and below.
constexpr float PanelWidth = 212;
constexpr float Pad = 8;
constexpr float SearchTop = 25;
constexpr float SearchHeight = 15;
constexpr float TabsTop = 45;
constexpr float TabHeight = 14;
constexpr float TabGap = 2.5f;
constexpr float ListTop = 66;
constexpr float EntryHeight = 21;
constexpr float HeadingHeight = 12;
constexpr float RowGap = 2;
constexpr float ListHeightMax = 9 * (EntryHeight + RowGap);
constexpr float FooterHeight = 28;
constexpr float ScrollbarWidth = 3.5f;
constexpr float CloseWidth = 40;
constexpr size_t EmptyButton = SoloBarSelectorTabCount;
constexpr size_t CloseButton = SoloBarSelectorTabCount + 1;
constexpr size_t MaximumSearchLength = 24;

SoloBarSelectorState &state(const GameplayScreenRuntime &context)
{
    return context.interactionState().soloBarSelector;
}

int bagCount(const Party &party)
{
    return std::max(1, party.rules().items.bagCount(party));
}

std::string tabName(SoloBarSelectorTab tab)
{
    switch (tab)
    {
        case SoloBarSelectorTab::All: return Engine::tr("All");
        case SoloBarSelectorTab::Spells: return Engine::tr("Spells");
        case SoloBarSelectorTab::Talents: return Engine::tr("Talents");
        case SoloBarSelectorTab::Potions: return Engine::tr("Potions");
        case SoloBarSelectorTab::Scrolls: return Engine::tr("Scrolls");
        case SoloBarSelectorTab::Actions: return Engine::tr("Actions");
    }
    return {};
}

// What a bar slot is as a selector entry: its category, name and detail; none when it names nothing known.
std::optional<SoloBarSelectorEntry> entryFor(GameplayScreenRuntime &context, const Party &party,
    const Character &member, const ActionBarSlot &slot)
{
    SoloBarSelectorEntry entry;
    entry.slot = slot;

    if (slot.kind == ActionBarSlotKind::Spell)
    {
        const SpellEntry *pSpell = context.spellTable() != nullptr ? context.spellTable()->findById(int(slot.id))
                                                                   : nullptr;
        if (pSpell == nullptr || findSpellbookSchoolUiDefinitionForSpellId(slot.id) == nullptr)
        {
            return std::nullopt;
        }
        entry.category = SoloBarSelectorTab::Spells;
        entry.name = Engine::localize(pSpell->name, "spell");
        const std::optional<std::string> skill = resolveMagicSkillName(slot.id);
        const std::string school = skill ? Engine::localize(displaySkillName(*skill), "skill") : std::string();
        // The cost the bar's tab shows (the same check: PartySpellSystem::manaCost).
        if (const std::optional<uint32_t> cost = PartySpellSystem::manaCost(party, member, *context.spellTable(),
                slot.id))
        {
            entry.detail = Engine::tr("{school} · {cost} SP", {{"school", school}, {"cost", int64_t(*cost)}});
        }
        else
        {
            entry.detail = school;
        }
        return entry;
    }

    if (slot.kind == ActionBarSlotKind::Talent)
    {
        if (slot.id >= soloTalentTable().talents().size())
        {
            return std::nullopt;
        }
        const TalentDefinition &talent = soloTalentTable().talents()[slot.id];
        const int rank = talentRank(member, talent.id);
        entry.category = SoloBarSelectorTab::Talents;
        entry.name = Engine::tr(talent.name);
        entry.detail = Engine::tr("Rank {rank} · cooldown {seconds} s", {{"rank", int64_t(rank)},
            {"seconds", int64_t(std::lround(talentCooldownSeconds(talent, std::max(rank, 1))))}});
        return entry;
    }

    const ItemTable *pItemTable = context.itemTable();

    if (slot.kind == ActionBarSlotKind::Item)
    {
        const ItemDefinition *pItem = pItemTable != nullptr ? pItemTable->get(slot.item.itemId) : nullptr;
        if (pItem == nullptr)
        {
            return std::nullopt;
        }
        entry.category = InventoryItemUseRuntime::scrollSpellId(*pItem) ? SoloBarSelectorTab::Scrolls
                                                                         : SoloBarSelectorTab::Potions;
        entry.name = Engine::localize(pItem->name);
        const size_t count = QuickItemSlots::countPartyItems(party, slot.item, bagCount(party));
        entry.detail = Engine::tr("{count} carried", {{"count", int64_t(count)}});
        entry.noneCarried = count == 0;
        return entry;
    }

    if (slot.kind == ActionBarSlotKind::Weapon)
    {
        const bool swap = slot.id == ActionBarWeaponSwapId;
        const uint32_t itemId = swap ? member.equipment.bow : member.equipment.mainHand;
        const ItemDefinition *pItem = pItemTable != nullptr && itemId != 0 ? pItemTable->get(itemId) : nullptr;
        entry.category = SoloBarSelectorTab::Actions;
        entry.name = swap ? Engine::tr("Swap weapon") : Engine::tr("Attack");
        entry.detail = swap ? (pItem != nullptr ? Engine::tr("Draw {weapon} or put it away",
                                                      {{"weapon", Engine::localize(pItem->name)}})
                                                : std::string())
                            : pItem != nullptr ? Engine::localize(pItem->name) : Engine::tr("Bare hands");
        return entry;
    }

    return std::nullopt;
}

// Everything the key can hold, once, when the selector opens: the known spells in book order, the learned active
// talents in the table's order, the potions and scrolls carried by name, then the weapon actions. What the key holds
// now stays listed even when it is no longer known or carried.
std::vector<SoloBarSelectorEntry> buildEntries(GameplayScreenRuntime &context, const Party &party,
    const Character &member, size_t slot)
{
    std::vector<ActionBarSlot> candidates;
    std::vector<uint32_t> spells(member.knownSpellIds.begin(), member.knownSpellIds.end());
    std::sort(spells.begin(), spells.end());

    for (const uint32_t spellId : spells)
    {
        candidates.push_back({ActionBarSlotKind::Spell, spellId, {}});
    }

    const std::vector<TalentDefinition> &talents = soloTalentTable().talents();

    for (size_t index = 0; index < talents.size(); ++index)
    {
        if (talents[index].kind == TalentKind::Active && talentRank(member, talents[index].id) > 0)
        {
            candidates.push_back({ActionBarSlotKind::Talent, uint32_t(index), {}});
        }
    }

    std::vector<SoloBarSelectorEntry> items;

    if (const ItemTable *pItemTable = context.itemTable())
    {
        for (const QuickItemSlots::PartyItemKind &kind : QuickItemSlots::partyItemKinds(party, *pItemTable,
                 context.mergedPotionSettingTable(), context.mergedReagentSettingTable(), bagCount(party)))
        {
            const ActionBarSlot itemSlot = {ActionBarSlotKind::Item, 0, {kind.itemId, QuickItemBottleRule::Strongest}};
            // One entry a kind: its strengths share the slot (it drinks the strongest first).
            const bool listed = std::any_of(items.begin(), items.end(),
                [&itemSlot](const SoloBarSelectorEntry &entry) { return soloBarSameEntry(entry.slot, itemSlot); });

            if (!listed)
            {
                if (std::optional<SoloBarSelectorEntry> entry = entryFor(context, party, member, itemSlot))
                {
                    items.push_back(std::move(*entry));
                }
            }
        }
    }

    std::sort(items.begin(), items.end(),
        [](const SoloBarSelectorEntry &left, const SoloBarSelectorEntry &right) { return left.name < right.name; });
    candidates.push_back({ActionBarSlotKind::Weapon, 0, {}});

    if (member.equipment.bow != 0)
    {
        candidates.push_back({ActionBarSlotKind::Weapon, ActionBarWeaponSwapId, {}});
    }

    std::vector<SoloBarSelectorEntry> entries;

    for (const ActionBarSlot &candidate : candidates)
    {
        if (std::optional<SoloBarSelectorEntry> entry = entryFor(context, party, member, candidate))
        {
            entries.push_back(std::move(*entry));
        }
    }

    entries.insert(entries.end(), std::make_move_iterator(items.begin()), std::make_move_iterator(items.end()));
    const ActionBarSlot &current = member.actionBar[slot];

    if (std::none_of(entries.begin(), entries.end(),
            [&current](const SoloBarSelectorEntry &entry) { return soloBarSameEntry(entry.slot, current); }))
    {
        if (std::optional<SoloBarSelectorEntry> entry = entryFor(context, party, member, current))
        {
            entries.push_back(std::move(*entry));
        }
    }

    for (SoloBarSelectorEntry &entry : entries)
    {
        entry.onKey = soloBarKeyOf(member.actionBar, entry.slot);
    }

    return entries;
}

// Ctrl is already someone else's: an action bound to the held Ctrl key, or the debug turbo movement while the party
// moves (Ctrl held standing still still arms the bar; a movement key then lets the turbo have it).
bool ctrlTaken(const GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    if (context.settingsSnapshot().turboMovementEnabled)
    {
        for (const KeyboardAction action : {KeyboardAction::Forward, KeyboardAction::Backward, KeyboardAction::Left,
                 KeyboardAction::Right, KeyboardAction::Jump, KeyboardAction::FlyUp, KeyboardAction::FlyDown})
        {
            if (input.action(action).held)
            {
                return true;
            }
        }
    }

    for (size_t action = 0; action < KeyboardActionCount; ++action)
    {
        const InputBinding binding = context.settingsSnapshot().keyboard.binding(KeyboardAction(action));

        if (binding.kind == InputBindingKind::Keyboard
            && (binding.scancode == SDL_SCANCODE_LCTRL || binding.scancode == SDL_SCANCODE_RCTRL)
            && input.isScancodeHeld(binding.scancode))
        {
            return true;
        }
    }

    return false;
}

void refilter(SoloBarSelectorState &selector)
{
    selector.rows = soloBarSelectorRows(selector.entries, selector.tab, selector.search);
    selector.scroll = 0;
    selector.hoveredRow.reset();
}

// The window: its origin and scale (the bar's), and the list's height in layout units (less on a short screen).
struct Layout
{
    GameplayResolvedHudLayoutElement page;
    float height = 0;
    float listHeight = 0;
};

std::optional<Layout> layout(GameplayScreenRuntime &context, int width, int height)
{
    const SoloBarSelectorState &selector = state(context);
    const std::optional<GameplayResolvedHudLayoutElement> bar = GameplaySoloHud::barPanelRect(context, width, height);
    const std::optional<SoloHudRect> slot = GameplaySoloHud::barSlotRect(context, width, height, selector.slot);

    if (!bar || !slot || bar->scale <= 0)
    {
        return std::nullopt;
    }

    Layout result;
    const float scale = bar->scale;
    const float margin = 4 * scale;
    const float room = (float(height) - 2 * margin) / scale - ListTop - FooterHeight;
    result.listHeight = std::clamp(room, EntryHeight, ListHeightMax);
    result.height = ListTop + result.listHeight + FooterHeight;
    // Beside the bar, its middle level with the chosen key, inside the screen.
    const float pixelHeight = result.height * scale;
    const float x = std::min(bar->x + bar->width + 3 * scale, float(width) - margin - PanelWidth * scale);
    const float y = std::clamp(slot->y + slot->height / 2 - pixelHeight / 2, margin,
        std::max(margin, float(height) - margin - pixelHeight));
    result.page = {x, y, PanelWidth * scale, pixelHeight, scale};
    return result;
}

GameplayObsidianRect searchRect()
{
    return {Pad, SearchTop, PanelWidth - 2 * Pad, SearchHeight};
}

GameplayObsidianRect tabRect(size_t tab)
{
    const float tabWidth = (PanelWidth - 2 * Pad - TabGap * float(SoloBarSelectorTabCount - 1))
        / float(SoloBarSelectorTabCount);
    return {Pad + float(tab) * (tabWidth + TabGap), TabsTop, tabWidth, TabHeight};
}

GameplayObsidianRect closeRect()
{
    return {PanelWidth - Pad - CloseWidth, 5, CloseWidth, 14};
}

GameplayObsidianRect emptyRect(const Layout &frame)
{
    return {Pad, frame.height - FooterHeight + 7, 70, 15};
}

float rowHeight(const SoloBarSelectorRow &row)
{
    return row.heading ? HeadingHeight : EntryHeight;
}

// The rows in view from the scroll on, with their tops in layout units.
std::vector<std::pair<size_t, float>> visibleRows(const SoloBarSelectorState &selector, const Layout &frame)
{
    std::vector<std::pair<size_t, float>> shown;
    float y = ListTop;

    for (size_t index = selector.scroll; index < selector.rows.size(); ++index)
    {
        const float rowBottom = y + rowHeight(selector.rows[index]);

        if (rowBottom > ListTop + frame.listHeight + 0.01f)
        {
            break;
        }

        shown.emplace_back(index, y);
        y = rowBottom + RowGap;
    }

    return shown;
}

// The first row the list can start at with its last row still at the bottom.
size_t maximumScroll(const SoloBarSelectorState &selector, const Layout &frame)
{
    float used = 0;
    size_t first = selector.rows.size();

    while (first > 0)
    {
        const float next = used + rowHeight(selector.rows[first - 1]) + (used > 0 ? RowGap : 0);

        if (next > frame.listHeight + 0.01f)
        {
            break;
        }

        used = next;
        --first;
    }

    return first;
}

GameplayObsidianRect rowRect(float top, const SoloBarSelectorRow &row)
{
    return {Pad, top, PanelWidth - 2 * Pad - ScrollbarWidth - 3, rowHeight(row)};
}

GameplayObsidianRect trackRect(const Layout &frame)
{
    return {PanelWidth - Pad - ScrollbarWidth, ListTop, ScrollbarWidth, frame.listHeight};
}

bool inside(const Layout &frame, const GameplayObsidianRect &unitRect, float x, float y)
{
    const float unitX = (x - frame.page.x) / frame.page.scale;
    const float unitY = (y - frame.page.y) / frame.page.scale;
    return unitRect.contains(unitX, unitY);
}

void assign(GameplayScreenRuntime &context, const ActionBarSlot &slot, const std::string &name)
{
    SoloBarSelectorState &selector = state(context);
    Party *pParty = context.party();
    Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;

    if (pMember != nullptr)
    {
        soloBarAssign(pMember->actionBar, selector.slot, slot);
        const std::string key = GameplaySoloHud::barKeyName(context, selector.slot);
        context.setStatusBarEvent(slot.kind == ActionBarSlotKind::Empty
                ? Engine::tr("Key {key} is empty", {{"key", key}})
                : Engine::tr("{name} is on key {key}", {{"name", name}, {"key", key}}));
    }

    GameplaySoloBarSelector::close(context);
}
}

bool GameplaySoloBarSelector::isOpen(const GameplayScreenRuntime &context)
{
    return state(context).open;
}

void GameplaySoloBarSelector::open(GameplayScreenRuntime &context, size_t slot)
{
    const Party *pParty = context.partyReadOnly();
    const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;

    if (pMember == nullptr || !context.soloHud() || slot >= ActionBarSlotCount / 2)
    {
        return;
    }

    SoloBarSelectorState &selector = state(context);
    const bool latch = selector.pointerLatch;
    selector = {};
    selector.open = true;
    selector.slot = slot;
    selector.pointerLatch = latch;
    selector.entries = buildEntries(context, *pParty, *pMember, slot);
    refilter(selector);
    // Start where the key's own entry is, so a full key shows what it holds.
    const std::optional<size_t> current = [&]() -> std::optional<size_t>
    {
        for (size_t row = 0; row < selector.rows.size(); ++row)
        {
            if (!selector.rows[row].heading
                && soloBarSameEntry(selector.entries[selector.rows[row].entry].slot, pMember->actionBar[slot]))
            {
                return row;
            }
        }
        return std::nullopt;
    }();

    if (current && *current > 3)
    {
        selector.scroll = *current - 3;
    }
}

void GameplaySoloBarSelector::close(GameplayScreenRuntime &context)
{
    SoloBarSelectorState &selector = state(context);
    const bool latch = selector.pointerLatch;
    selector = {};
    selector.pointerLatch = latch;
}

bool GameplaySoloBarSelector::armed(const GameplayScreenRuntime &context)
{
    return state(context).armed;
}

void GameplaySoloBarSelector::disarm(GameplayScreenRuntime &context)
{
    SoloBarSelectorState &selector = state(context);

    if (selector.armed)
    {
        selector.armed = false;
        context.clearStatusBarHoverText();
    }
}

bool GameplaySoloBarSelector::takesPointer(const GameplayScreenRuntime &context)
{
    return state(context).open || state(context).armed || state(context).pointerLatch;
}

std::optional<size_t> GameplaySoloBarSelector::clickedBarSlot(const GameplayScreenRuntime &context)
{
    return state(context).clickedSlot;
}

bool GameplaySoloBarSelector::takesPointerAction(const GameplayScreenRuntime &context, KeyboardAction action)
{
    return takesPointer(context)
        && context.settingsSnapshot().keyboard.binding(action).kind != InputBindingKind::Keyboard;
}

bool GameplaySoloBarSelector::handleBarInput(GameplayScreenRuntime &context, const GameplayInputFrame &input,
    int width, int height, bool allowed, bool pointerAllowed)
{
    SoloBarSelectorState &selector = state(context);

    if (!input.leftMouseButton.held && !input.rightMouseButton.held)
    {
        selector.pointerLatch = false;
    }

    if (!input.leftMouseButton.held || !allowed || !context.soloHud() || selector.open)
    {
        selector.clickedSlot.reset();
    }

    const bool ctrl = input.isScancodeHeld(SDL_SCANCODE_LCTRL) || input.isScancodeHeld(SDL_SCANCODE_RCTRL);

    // A plain click on a key uses it; the click stays the bar's, so the world does not attack or interact as well.
    if (allowed && pointerAllowed && context.soloHud() && !selector.open && !ctrl && input.leftMouseButton.pressed)
    {
        if (const std::optional<size_t> slot =
                GameplaySoloHud::barSlotAt(context, width, height, input.pointerX, input.pointerY))
        {
            selector.pointerLatch = true;
            selector.clickedSlot = slot;
            disarm(context);
            return true;
        }
    }

    if (!allowed || !context.soloHud() || selector.open || !ctrl || ctrlTaken(context, input))
    {
        disarm(context);
        return false;
    }

    // Held Ctrl pauses the game, frees the cursor and lights the keys until it is let go or a key is chosen.
    selector.armed = true;
    context.setStatusBarHoverText(Engine::tr("Click a key to choose what goes on it"));

    if (pointerAllowed && input.leftMouseButton.pressed)
    {
        if (const std::optional<size_t> slot =
                GameplaySoloHud::barSlotAt(context, width, height, input.pointerX, input.pointerY))
        {
            selector.pointerLatch = true;
            disarm(context);
            open(context, *slot);
            return true;
        }
    }

    for (size_t slot = 0; slot < ActionBarSlotCount / 2; ++slot)
    {
        if (GameplaySoloHud::barSlotPressed(input, slot))
        {
            disarm(context);
            open(context, slot);
            return false;
        }
    }

    // A click elsewhere while armed is the bar's too: the world is paused under it.
    if (pointerAllowed && input.leftMouseButton.pressed)
    {
        selector.pointerLatch = true;
        return true;
    }

    return false;
}

void GameplaySoloBarSelector::handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input, int width,
    int height)
{
    SoloBarSelectorState &selector = state(context);
    const Party *pParty = context.partyReadOnly();
    const std::optional<Layout> frame = layout(context, width, height);

    if (!selector.open || pParty == nullptr || pParty->activeMember() == nullptr || !frame)
    {
        close(context);
        return;
    }

    if (!input.leftMouseButton.held && !input.rightMouseButton.held)
    {
        selector.pointerLatch = false;
    }

    // Escape clears the search first, then closes.
    const bool escape = input.isScancodeHeld(SDL_SCANCODE_ESCAPE);
    const bool escapePressed = escape && !selector.escapeHeld;
    selector.escapeHeld = escape;

    if (escapePressed)
    {
        context.interactionState().menuToggleLatch = true;

        if (!selector.search.empty())
        {
            selector.search.clear();
            refilter(selector);
        }
        else
        {
            close(context);
        }

        return;
    }

    // Ctrl and another bar key moves the selector to that key.
    const bool ctrl = input.isScancodeHeld(SDL_SCANCODE_LCTRL) || input.isScancodeHeld(SDL_SCANCODE_RCTRL);

    for (size_t slot = 0; ctrl && slot < ActionBarSlotCount / 2; ++slot)
    {
        if (slot != selector.slot && GameplaySoloHud::barSlotPressed(input, slot))
        {
            open(context, slot);
            return;
        }
    }

    // Typing filters as it goes.
    const std::string before = selector.search;

    if (!ctrl)
    {
        Engine::Utf8::appendPrintable(selector.search, input.textInput, MaximumSearchLength);
    }

    for (uint16_t count = input.scancodePressCount(SDL_SCANCODE_BACKSPACE); count > 0 && !selector.search.empty();
         --count)
    {
        Engine::Utf8::popBack(selector.search);
    }

    if (selector.search != before)
    {
        refilter(selector);
    }

    const size_t maxScroll = maximumScroll(selector, *frame);
    selector.scroll = std::min(selector.scroll, maxScroll);
    const float x = input.pointerX;
    const float y = input.pointerY;
    const GameplayObsidianRect panel = {0, 0, PanelWidth, frame->height};
    const bool overPanel = inside(*frame, panel, x, y);

    if (overPanel && input.mouseWheelDelta != 0)
    {
        selector.scroll = input.mouseWheelDelta > 0 ? (selector.scroll > 2 ? selector.scroll - 2 : 0)
                                                    : std::min(selector.scroll + 2, maxScroll);
    }

    // What the pointer is over: a row, a tab, Empty or Close.
    selector.hoveredRow.reset();
    selector.hoveredButton.reset();

    for (const auto &[row, top] : visibleRows(selector, *frame))
    {
        if (!selector.rows[row].heading && inside(*frame, rowRect(top, selector.rows[row]), x, y))
        {
            selector.hoveredRow = row;
        }
    }

    for (size_t tab = 0; tab < SoloBarSelectorTabCount; ++tab)
    {
        if (inside(*frame, tabRect(tab), x, y)
            && soloBarSelectorTabHasEntries(selector.entries, SoloBarSelectorTab(tab)))
        {
            selector.hoveredButton = tab;
        }
    }

    if (inside(*frame, emptyRect(*frame), x, y))
    {
        selector.hoveredButton = EmptyButton;
    }
    else if (inside(*frame, closeRect(), x, y))
    {
        selector.hoveredButton = CloseButton;
    }

    const bool left = input.leftMouseButton.pressed && !selector.pointerLatch;
    const bool right = input.rightMouseButton.pressed && !selector.pointerLatch;

    if (!left && !right)
    {
        return;
    }

    selector.pointerLatch = true;

    // A click away closes it; a right click inside does nothing.
    if (!overPanel)
    {
        close(context);
        return;
    }

    if (!left)
    {
        return;
    }

    if (selector.hoveredRow)
    {
        const SoloBarSelectorEntry &entry = selector.entries[selector.rows[*selector.hoveredRow].entry];
        assign(context, entry.slot, entry.name);
        return;
    }

    if (selector.hoveredButton == EmptyButton)
    {
        assign(context, {}, {});
        return;
    }

    if (selector.hoveredButton == CloseButton)
    {
        close(context);
        return;
    }

    if (selector.hoveredButton && *selector.hoveredButton < SoloBarSelectorTabCount)
    {
        selector.tab = SoloBarSelectorTab(*selector.hoveredButton);
        refilter(selector);
        return;
    }

    const GameplayObsidianRect track = trackRect(*frame);

    if (maxScroll > 0 && inside(*frame, {track.x - 2, track.y, track.width + 4, track.height}, x, y))
    {
        const float position = ((y - frame->page.y) / frame->page.scale - track.y) / std::max(1.0f, track.height);
        selector.scroll = std::min(size_t(std::lround(std::clamp(position, 0.0f, 1.0f) * float(maxScroll))),
            maxScroll);
    }
}

void GameplaySoloBarSelector::render(GameplayScreenRuntime &context, int width, int height)
{
    const SoloBarSelectorState &selector = state(context);
    const Party *pParty = context.partyReadOnly();
    const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;

    // Armed: a gold rim with a soft glow round every key of the bar.
    if (selector.armed && pMember != nullptr)
    {
        const std::optional<GameplayResolvedHudLayoutElement> bar =
            GameplaySoloHud::barPanelRect(context, width, height);
        const GameplayObsidianPainter painter(context, bar.value_or(GameplayResolvedHudLayoutElement{}));
        const float scale = bar ? bar->scale : 1.0f;

        for (size_t slot = 0; bar && slot < ActionBarSlotCount / 2; ++slot)
        {
            const std::optional<SoloHudRect> rect = GameplaySoloHud::barSlotRect(context, width, height, slot);

            if (!rect)
            {
                continue;
            }

            for (int ring = 3; ring >= 1; --ring)
            {
                const float spread = float(ring) * scale * 0.9f;
                const GameplayObsidianRect glow = {rect->x - spread, rect->y - spread, rect->width + 2 * spread,
                    rect->height + 2 * spread};
                painter.frame(glow, abgr(0xf2d27a, uint32_t(0xa0 / ring)));
            }

            const float line = std::max(1.0f, std::round(scale * 0.9f));
            const GameplayObsidianRect rim = {rect->x - line, rect->y - line, rect->width + 2 * line,
                rect->height + 2 * line};
            painter.fill({rim.x, rim.y, rim.width, line}, abgr(0xf2d27a));
            painter.fill({rim.x, rim.y + rim.height - line, rim.width, line}, abgr(0xf2d27a));
            painter.fill({rim.x, rim.y, line, rim.height}, abgr(0xf2d27a));
            painter.fill({rim.x + rim.width - line, rim.y, line, rim.height}, abgr(0xf2d27a));
        }

        return;
    }

    const std::optional<Layout> frame = selector.open ? layout(context, width, height) : std::nullopt;

    if (!frame || pMember == nullptr)
    {
        return;
    }

    const GameplayObsidianPainter painter(context, frame->page);
    const float scale = frame->page.scale;
    const std::string key = GameplaySoloHud::barKeyName(context, selector.slot);

    // The chosen key on the bar gets the selected rim, as the popups mark their member.
    if (const std::optional<SoloHudRect> slot = GameplaySoloHud::barSlotRect(context, width, height, selector.slot))
    {
        const float line = std::max(1.0f, std::round(scale * 0.9f));
        const GameplayObsidianRect rim = {slot->x - line, slot->y - line, slot->width + 2 * line,
            slot->height + 2 * line};
        painter.fill({rim.x, rim.y, rim.width, line}, ChipOnBorder);
        painter.fill({rim.x, rim.y + rim.height - line, rim.width, line}, ChipOnBorder);
        painter.fill({rim.x, rim.y, line, rim.height}, ChipOnBorder);
        painter.fill({rim.x + rim.width - line, rim.y, line, rim.height}, ChipOnBorder);
    }

    // The popups' panel: a dark outer band in dark brass round the panel in brass.
    const GameplayObsidianRect panel = painter.rect(0, 0, PanelWidth, frame->height);
    const GameplayObsidianRect outer = painter.rect(-2, -2, PanelWidth + 4, frame->height + 4);
    painter.fill(outer, OuterFill);
    painter.frame(outer, BrassDark);
    painter.fill(panel, PanelFill);
    painter.frame(panel, Brass);

    // Header: the key, Close.
    painter.text("Fondamento", 14, Ivory, Engine::tr("Key {key}", {{"key", key}}), Pad, 4);
    const GameplayObsidianRect close = closeRect();
    const bool closeHot = selector.hoveredButton == CloseButton;
    painter.fill(painter.rect(close.x, close.y, close.width, close.height), closeHot ? ChipOnFill : ChipFill);
    painter.frame(painter.rect(close.x, close.y, close.width, close.height), ChipOnBorder);
    painter.text("Fondamento", 9, abgr(0xe8d1a4), Engine::tr("Close"), close.x + close.width / 2, close.y + 2.5f, 1);

    // The search field: always typing.
    const GameplayObsidianRect search = searchRect();
    painter.fill(painter.rect(search.x, search.y, search.width, search.height), abgr(0x0b1212));
    painter.frame(painter.rect(search.x, search.y, search.width, search.height), ChipOnBorder);
    const bool caret = SDL_GetTicks() / 500 % 2 == 0;
    if (selector.search.empty())
    {
        painter.text(TextFont, 8, Muted, Engine::tr("Type to search"), search.x + 5, search.y + 3);
    }
    else
    {
        painter.text(TextFont, 8, Ivory,
            painter.fitted(TextFont, 8, selector.search + (caret ? "|" : ""), search.width - 10), search.x + 5,
            search.y + 3);
    }

    // The tabs: only those with entries can be chosen.
    for (size_t tab = 0; tab < SoloBarSelectorTabCount; ++tab)
    {
        const GameplayObsidianRect chip = tabRect(tab);
        const bool enabled = soloBarSelectorTabHasEntries(selector.entries, SoloBarSelectorTab(tab));
        const bool on = selector.tab == SoloBarSelectorTab(tab);
        const bool hot = selector.hoveredButton == tab;
        const GameplayObsidianRect box = painter.rect(chip.x, chip.y, chip.width, chip.height);
        painter.fill(box, on || hot ? ChipOnFill : ChipFill);
        painter.frame(box, on ? ChipOnBorder : ChipBorder);
        painter.text(TextFont, 7, !enabled ? Disabled : on ? Ivory : Body,
            painter.fitted(TextFont, 7, tabName(SoloBarSelectorTab(tab)), chip.width - 3), chip.x + chip.width / 2,
            chip.y + 3, 1);
    }

    painter.fill(painter.rect(0, ListTop - 4, PanelWidth, 0.6f), Rule);

    // The list.
    const ActionBarSlot &current = pMember->actionBar[selector.slot];

    for (const auto &[index, top] : visibleRows(selector, *frame))
    {
        const SoloBarSelectorRow &row = selector.rows[index];
        const GameplayObsidianRect area = rowRect(top, row);

        if (row.heading)
        {
            const float labelWidth = painter.text(TextFont, 7.5f, Label, tabName(row.category), area.x + 2, top + 1.5f);
            painter.fill(painter.rect(area.x + labelWidth + 6, top + 6.5f, area.width - labelWidth - 8, 0.6f), Rule);
            continue;
        }

        const SoloBarSelectorEntry &entry = selector.entries[row.entry];
        const bool selected = soloBarSameEntry(entry.slot, current);
        const bool hot = selector.hoveredRow == index;
        const GameplayObsidianRect box = painter.rect(area.x, area.y, area.width, area.height);
        painter.fill(box, selected || hot ? ChipOnFill : RowFill);
        painter.frame(box, selected ? ChipOnBorder : hot ? ChipBorder : RowBorder);
        const GameplayObsidianRect icon = painter.rect(area.x + 2, area.y + 2, area.height - 4, area.height - 4);
        painter.fill(icon, IconBack);
        GameplaySoloHud::renderSlotIcon(context, painter, *pMember, entry.slot, icon, entry.noneCarried);
        const float textX = area.x + area.height + 3;
        // The key it is on now: a gold chip at the right, as the potion popup marks its quick slots.
        float right = area.x + area.width - 3;
        if (entry.onKey)
        {
            const GameplayObsidianRect pin = painter.rect(right - 9, area.y + 6, 9, 9);
            painter.fill(pin, abgr(0x1c2524));
            painter.frame(pin, selected ? ChipOnBorder : abgr(0x6b6a4e));
            painter.text(TextFont, 7, Gold, GameplaySoloHud::barKeyName(context, *entry.onKey), right - 4.5f,
                area.y + 6.6f, 1);
            right -= 12;
        }
        painter.text(NameFont, 9, selected ? Gold : Ivory, painter.fitted(NameFont, 9, entry.name, right - textX),
            textX, area.y + 1.5f);
        painter.text(TextFont, 6.5f, Muted, painter.fitted(TextFont, 6.5f, entry.detail, right - textX), textX,
            area.y + 11.5f);
    }

    if (selector.rows.empty())
    {
        painter.text(TextFont, 8, Muted,
            selector.search.empty() ? Engine::tr("Nothing to put here") : Engine::tr("Nothing matches the search"),
            Pad + 2, ListTop + 4);
    }

    const size_t maxScroll = maximumScroll(selector, *frame);

    if (maxScroll > 0)
    {
        const GameplayObsidianRect track = trackRect(*frame);
        painter.fill(painter.rect(track.x, track.y, track.width, track.height), Track);
        const size_t shown = visibleRows(selector, *frame).size();
        const float thumb = std::max(8.0f, track.height * float(shown) / float(selector.rows.size()));
        const float offset = (track.height - thumb) * float(std::min(selector.scroll, maxScroll)) / float(maxScroll);
        painter.fill(painter.rect(track.x - 0.5f, track.y + offset, track.width + 1, thumb), Thumb);
    }

    // Footer: Empty this key, and the hint.
    painter.fill(painter.rect(0, frame->height - FooterHeight + 2, PanelWidth, 0.6f), Rule);
    const GameplayObsidianRect empty = emptyRect(*frame);
    const bool emptyHot = selector.hoveredButton == EmptyButton;
    const GameplayObsidianRect emptyBox = painter.rect(empty.x, empty.y, empty.width, empty.height);
    painter.fill(emptyBox, emptyHot ? ChipOnFill : ChipFill);
    painter.frame(emptyBox, ChipOnBorder);
    painter.text("Fondamento", 8.5f, current.kind == ActionBarSlotKind::Empty ? abgr(0x8c8670) : abgr(0xe8d1a4),
        Engine::tr("Empty this key"), empty.x + empty.width / 2, empty.y + 3, 1);
    painter.text(TextFont, 7, Muted,
        painter.fitted(TextFont, 7, Engine::tr("Click to put it on key {key}", {{"key", key}}),
            PanelWidth - empty.width - 3 * Pad),
        PanelWidth - Pad, empty.y + 3.5f, 2);
}

std::string GameplaySoloBarSelector::barHoverText(GameplayScreenRuntime &context, int width, int height, float x,
    float y)
{
    const Party *pParty = context.partyReadOnly();
    const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;

    if (pMember == nullptr || !context.soloHud() || state(context).open
        || context.currentHudScreenState() != GameplayHudScreenState::Gameplay)
    {
        return {};
    }

    const std::optional<size_t> slot = GameplaySoloHud::barSlotAt(context, width, height, x, y);

    if (!slot)
    {
        return {};
    }

    const ActionBarSlot &held = pMember->actionBar[*slot];

    if (held.kind == ActionBarSlotKind::Empty)
    {
        return Engine::tr("Ctrl+click: choose what goes on this key");
    }

    const std::optional<SoloBarSelectorEntry> entry = entryFor(context, *pParty, *pMember, held);
    return entry ? Engine::tr("{name} (click: use, Ctrl+click: change this key)", {{"name", entry->name}})
                 : std::string();
}
}
