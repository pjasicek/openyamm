#include "game/ui/GameplayBattleOrders.h"

#include "engine/Localization.h"
#include "game/app/KeyboardBindings.h"
#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"
#include "game/party/WorldSpells.h"
#include "game/rules/GameRules.h"
#include "game/tables/SpellTable.h"
#include "game/ui/GameplayObsidianPainter.h"
#include "game/ui/SpellbookUiLayout.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
using namespace GameplayObsidianColors;
using Rect = GameplayObsidianRect;
using WindowState = GameplayUiController::BattleOrdersWindowState;
using MenuState = GameplayUiController::SpellbookSpellMenuState;

constexpr char TitleFont[] = "Fondamento";
constexpr char NameFont[] = "Arrus";
constexpr char TextFont[] = "alegreya_semibold";

constexpr uint32_t Shade = abgr(0x020606, 0xc4);
constexpr uint32_t RowFill = abgr(0x0d1515, 0xe6);
constexpr uint32_t RowBorder = abgr(0x333c37);
constexpr uint32_t RowSelectedFill = abgr(0x1e1f16, 0xf0);
constexpr uint32_t RowSelectedBorder = abgr(0xd6bb80);
constexpr uint32_t BoxFill = abgr(0x0b1212, 0xd8);
constexpr uint32_t Rule = abgr(0x3a3f35);
constexpr uint32_t ChipBorder = abgr(0x4f5b55);
constexpr uint32_t ChipOnFill = abgr(0x2b2a1a);
constexpr uint32_t ChipOnBorder = abgr(0xd6bb80);
constexpr uint32_t ChipOnText = abgr(0xffe7b0);
constexpr uint32_t HoverFill = abgr(0xffffff, 0x14);
constexpr uint32_t Track = abgr(0x070b0b);
constexpr uint32_t TrackBorder = abgr(0x56604f);
constexpr uint32_t TrackFill = abgr(0xc9a865);
constexpr uint32_t MeleeZone = abgr(0xb2402a, 0x70);
constexpr uint32_t Thumb = abgr(0xd8bd80);
constexpr uint32_t ThumbEdge = abgr(0x241c0e);
constexpr uint32_t Disabled = abgr(0x6f7468);
constexpr uint32_t MenuFill = abgr(0x0b1212, 0xf5);
constexpr uint32_t MenuHot = abgr(0x2b2a1a);
constexpr uint32_t IconWell = abgr(0x101a18);

// The window in logical units (the HUD's 480-high scale): as wide as the screen allows between these.
constexpr float WindowHeight = 462;
constexpr float MinimumWindowWidth = 600;
constexpr float MaximumWindowWidth = 790;
constexpr float Margin = 30;
constexpr float RowTop = 92;
constexpr float RowHeight = 32;
constexpr float RowPitch = 35;
constexpr float EditorTop = 78;
constexpr float EditorHeight = 192;
constexpr float PaletteTop = 276;
constexpr float PaletteHeight = 120;
constexpr float PaletteIcon = 38;
constexpr float PalettePitch = 41;
constexpr size_t PaletteRows = 2;
constexpr float QuickTop = 410;
constexpr float FrameEdge = 120;

// The distance slider gives its first half to 0-1024 units, where blows and spread spells are decided.
constexpr float DistanceKnee = 1024;
constexpr int AllyMinimum = 10;
constexpr int AllyMaximum = 90;
constexpr int KeepMaximum = 80;
// The rows a list shows at once; a longer list scrolls. The attack list keeps a row for its fallback.
constexpr size_t AttackVisibleRows = 6;
constexpr size_t UpkeepVisibleRows = 8;
// The upkeep list's presets sit under its rows.
constexpr float UpkeepPresetsTop = RowTop + float(UpkeepVisibleRows) * RowPitch + 3;

constexpr std::array<std::string_view, 5> QuickSlotNames = {Engine::trNoop("Quick Cast"),
    Engine::trNoop("Quick Spell 1"), Engine::trNoop("Quick Spell 2"), Engine::trNoop("Quick Spell 3"),
    Engine::trNoop("Quick Spell 4")};

// The "Start from" chips: the four plans, then the menu of the other members' orders.
constexpr std::array<std::string_view, 5> PresetNames = {Engine::trNoop("Fighter"), Engine::trNoop("Archer"),
    Engine::trNoop("Caster"), Engine::trNoop("Healer"), Engine::trNoop("Copy from...")};
// The upkeep list's "Add" chips: the buffs and the healing the member knows, then the same menu.
constexpr std::array<std::string_view, 3> UpkeepPresetNames = {Engine::trNoop("Buffs"), Engine::trNoop("Healing"),
    Engine::trNoop("Copy from...")};
constexpr std::array<std::string_view, 2> ListNames = {Engine::trNoop("On Attack"), Engine::trNoop("Upkeep")};
constexpr std::array<std::string_view, 3> PlaceNames = {Engine::trNoop("Anywhere"), Engine::trNoop("Indoors"),
    Engine::trNoop("Outdoors")};

enum class Slider
{
    None = -1,
    Distance,
    Ally,
    Keep,
    // Upkeep's "renew when under".
    Renew,
};

enum class Control
{
    None,
    Close,
    Tab,
    // The list switch: 0 the attack orders, 1 the upkeep spells.
    List,
    Row,
    RowToggle,
    RowUp,
    RowDown,
    RowRemove,
    FallbackWeapon,
    FallbackHold,
    Preset,
    CopyMenu,
    CopyMember,
    PaletteEntry,
    PaletteScrollUp,
    PaletteScrollDown,
    PaletteSearch,
    QuickSlot,
    // The Upkeep key's box, in place of the quick keys while the upkeep list shows.
    UpkeepKey,
    // The list's scrollbar.
    ScrollBar,
    ConditionToggle,
    DistancePreset,
    SliderTrack,
    // A place chip: a BattleOrderPlace.
    Place,
};

struct Hit
{
    Control control = Control::None;
    size_t index = 0;
};

// A palette entry: a spell, the two weapon orders, or clearing the armed quick key.
struct PaletteEntry
{
    BattleOrderKind kind = BattleOrderKind::Spell;
    uint32_t spellId = 0;
    bool clear = false;
};

struct Layout
{
    GameplayResolvedHudLayoutElement page;
    float width = MinimumWindowWidth;
    float leftRight = 0;
    float rightLeft = 0;
    float rightRight = 0;

    Rect window() const
    {
        return {page.x, page.y, width * page.scale, WindowHeight * page.scale};
    }
};

Layout layoutFor(int screenWidth, int screenHeight)
{
    Layout layout;
    const float scale = float(screenHeight) / 480.0f;
    layout.width = std::clamp(float(screenWidth) / scale - 24.0f, MinimumWindowWidth, MaximumWindowWidth);
    layout.page.scale = scale;
    layout.page.width = layout.width * scale;
    layout.page.height = WindowHeight * scale;
    layout.page.x = std::round((float(screenWidth) - layout.page.width) / 2);
    layout.page.y = std::round((float(screenHeight) - layout.page.height) / 2);
    layout.leftRight = std::round(layout.width * 0.56f);
    layout.rightLeft = layout.leftRight + 14;
    layout.rightRight = layout.width - Margin;
    return layout;
}

Rect pageRect(const Layout &layout, float x, float y, float width, float height)
{
    return {layout.page.x + x * layout.page.scale, layout.page.y + y * layout.page.scale, width * layout.page.scale,
        height * layout.page.scale};
}

WindowState &window(const GameplayScreenRuntime &context)
{
    return context.spellbook().battleOrders;
}

MenuState &menu(const GameplayScreenRuntime &context)
{
    return context.spellbook().spellMenu;
}

Character *editedMember(const GameplayScreenRuntime &context)
{
    Party *pParty = context.party();

    if (pParty == nullptr || pParty->members().empty())
    {
        return nullptr;
    }

    WindowState &state = window(context);
    state.memberIndex = std::min(state.memberIndex, pParty->members().size() - 1);
    return pParty->member(state.memberIndex);
}

// The list the window shows and edits: the member's upkeep spells or attack orders.
std::vector<BattleOrder> &shownOrders(Character &member, const WindowState &state)
{
    return state.upkeep ? member.upkeepOrders : member.battleOrders;
}

const std::vector<BattleOrder> &shownOrders(const Character &member, const WindowState &state)
{
    return state.upkeep ? member.upkeepOrders : member.battleOrders;
}

size_t visibleRows(const WindowState &state)
{
    return state.upkeep ? UpkeepVisibleRows : AttackVisibleRows;
}

// The furthest the shown list scrolls.
size_t maximumScroll(const Character &member, const WindowState &state)
{
    const size_t count = shownOrders(member, state).size();
    return count > visibleRows(state) ? count - visibleRows(state) : 0;
}

// Scrolls the list so that the order's row shows.
void showOrder(WindowState &state, size_t index)
{
    if (index < state.listScroll)
    {
        state.listScroll = index;
    }
    else if (index >= state.listScroll + visibleRows(state))
    {
        state.listScroll = index + 1 - visibleRows(state);
    }
}

// An upkeep spell that keeps a buff up, so it has a time left to renew at; not a heal, a cure or Awaken.
bool isUpkeepBuff(uint32_t spellId)
{
    const SpellId spell = spellIdFromValue(spellId);
    return PartySpellSystem::isUpkeepSpell(spellId) && !PartySpellSystem::hasQuickCastCharacterTarget(spellId)
        && spell != SpellId::PowerCure && spell != SpellId::Awaken;
}

// Whether the member's upkeep list can take the spell: an upkeep spell the rules do not hold as an aura.
bool upkeepTakes(const Party &party, const Character &member, uint32_t spellId)
{
    if (!PartySpellSystem::isUpkeepSpell(spellId))
    {
        return false;
    }

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        if (&party.members()[index] == &member)
        {
            return !party.rules().spells.castsAsAura(party, index, spellId);
        }
    }

    return true;
}

bool upkeepTakes(const GameplayScreenRuntime &context, const Character &member, uint32_t spellId)
{
    const Party *pParty = context.partyReadOnly();
    return pParty != nullptr && upkeepTakes(*pParty, member, spellId);
}

const SpellEntry *orderSpell(const GameplayScreenRuntime &context, const Character &member, const BattleOrder &order)
{
    return order.kind == BattleOrderKind::Spell && context.spellTable() != nullptr
        ? context.spellTable()->findByName(order.spellName, spellKnownBy(member))
        : nullptr;
}

std::string spellDisplayName(const GameplayScreenRuntime &context, const Character &member, const SpellEntry &spell)
{
    return Engine::localize(partySpellName(context.partyReadOnly(), member, spell), "spell");
}

std::string orderName(const GameplayScreenRuntime &context, const Character &member, const BattleOrder &order)
{
    switch (order.kind)
    {
        case BattleOrderKind::Melee:
            return Engine::tr("Melee");
        case BattleOrderKind::Shoot:
            return Engine::tr("Shoot");
        case BattleOrderKind::Spell:
            break;
    }

    const SpellEntry *pSpell = orderSpell(context, member, order);
    return pSpell != nullptr ? spellDisplayName(context, member, *pSpell) : Engine::localize(order.spellName, "spell");
}

std::string distanceText(const BattleOrderDistance &distance)
{
    if (distance.minimum == 0 && distance.maximum == BattleOrderMeleeReach)
    {
        return Engine::tr("target in melee reach");
    }

    if (distance.minimum == BattleOrderMeleeReach && distance.maximum >= BattleOrderMaximumDistance)
    {
        return Engine::tr("target beyond melee reach");
    }

    if (distance.maximum >= BattleOrderMaximumDistance)
    {
        return Engine::tr("target {minimum} units or further", {{"minimum", int64_t(distance.minimum)}});
    }

    if (distance.minimum == 0)
    {
        return Engine::tr("target within {maximum} units", {{"maximum", int64_t(distance.maximum)}});
    }

    return Engine::tr("target {minimum}-{maximum} units away",
        {{"minimum", int64_t(distance.minimum)}, {"maximum", int64_t(distance.maximum)}});
}

// The order's conditions in a line: "target in melee reach · keeps 30 % SP", or what it always checks. An upkeep
// spell's line starts with when it is due.
std::string conditionSummary(const GameplayScreenRuntime &context, const Character &member, const BattleOrder &order,
    bool upkeep)
{
    if (!order.enabled)
    {
        return Engine::tr("off, settings kept");
    }

    std::vector<std::string> parts;

    if (upkeep)
    {
        const SpellEntry *pSpell = orderSpell(context, member, order);

        if (pSpell != nullptr && !isUpkeepBuff(uint32_t(pSpell->id)))
        {
            parts.push_back(Engine::tr("when someone needs it"));
        }
        else if (order.renewBelowMinutes)
        {
            parts.push_back(Engine::tr("under {minutes} min left", {{"minutes", int64_t(*order.renewBelowMinutes)}}));
        }
        else
        {
            parts.push_back(Engine::tr("when it has run out"));
        }
    }

    if (order.kind == BattleOrderKind::Melee)
    {
        parts.push_back(Engine::tr("in the weapon's reach"));
    }
    else if (order.kind == BattleOrderKind::Shoot)
    {
        parts.push_back(Engine::tr("with a ranged weapon"));
    }

    if (order.distance)
    {
        parts.push_back(distanceText(*order.distance));
    }

    if (order.allyHealthBelowPercent)
    {
        parts.push_back(Engine::tr("an ally below {percent} % HP", {{"percent", int64_t(*order.allyHealthBelowPercent)}}));
    }

    if (order.keepSpellPointsPercent && order.kind == BattleOrderKind::Spell)
    {
        parts.push_back(Engine::tr("keeps {percent} % SP", {{"percent", int64_t(*order.keepSpellPointsPercent)}}));
    }

    if (order.place != BattleOrderPlace::Anywhere)
    {
        parts.push_back(order.place == BattleOrderPlace::Indoors ? Engine::tr("indoors") : Engine::tr("outdoors"));
    }

    if (parts.empty())
    {
        const SpellEntry *pSpell = orderSpell(context, member, order);
        const std::optional<PartySpellDescriptor> descriptor =
            pSpell != nullptr ? PartySpellSystem::describeSpell(uint32_t(pSpell->id)) : std::nullopt;

        if (descriptor && PartySpellSystem::hasQuickCastCharacterTarget(uint32_t(pSpell->id)))
        {
            parts.push_back(Engine::tr("when someone needs it"));
        }
        else if (pSpell != nullptr && (PartySpellSystem::isUpkeepBuffSpell(uint32_t(pSpell->id))
                     || (descriptor && descriptor->partyBuff)))
        {
            parts.push_back(Engine::tr("when the party lacks it"));
        }
        else
        {
            parts.push_back(Engine::tr("always"));
        }
    }

    std::string result;

    for (const std::string &part : parts)
    {
        result += (result.empty() ? "" : " \xC2\xB7 ") + part;
    }

    return result;
}

// The member's spells an order or quick key can use: those cast at a monster, a member or nobody, in book order;
// for the upkeep list, the upkeep spells; with a search, those whose shown name contains it.
std::vector<PaletteEntry> paletteEntries(const GameplayScreenRuntime &context, const Character &member, bool quickKey,
    const std::string &search, bool upkeep)
{
    const std::string wanted = Engine::Utf8::lower(search);
    const auto matches = [&context, &member, &wanted](const PaletteEntry &entry)
    {
        if (wanted.empty() || entry.clear)
        {
            return true;
        }

        std::string name = entry.kind == BattleOrderKind::Melee ? Engine::tr("Melee")
            : entry.kind == BattleOrderKind::Shoot ? Engine::tr("Shoot") : std::string();
        const SpellEntry *pSpell = entry.kind == BattleOrderKind::Spell && context.spellTable() != nullptr
            ? context.spellTable()->findById(int(entry.spellId)) : nullptr;

        if (pSpell != nullptr)
        {
            name = Engine::localize(partySpellName(context.partyReadOnly(), member, *pSpell), "spell");
        }

        return Engine::Utf8::lower(name).find(wanted) != std::string::npos;
    };

    std::vector<PaletteEntry> entries;

    if (quickKey)
    {
        entries.push_back({BattleOrderKind::Spell, 0, true});
    }

    for (const SpellbookSchoolUiDefinition &school : spellbookSchoolUiDefinitions())
    {
        for (uint32_t offset = 0; offset < school.spellCount; ++offset)
        {
            const uint32_t spellId = school.firstSpellId + offset;

            if (!member.knowsSpell(spellId))
            {
                continue;
            }

            const std::optional<PartySpellDescriptor> descriptor = PartySpellSystem::describeSpell(spellId);
            const bool utility = descriptor
                && (descriptor->targetKind == PartySpellCastTargetKind::InventoryItem
                    || descriptor->targetKind == PartySpellCastTargetKind::TelekinesisTarget
                    || descriptor->targetKind == PartySpellCastTargetKind::UtilityUi
                    || descriptor->effectKind == PartySpellCastEffectKind::Jump);

            // A quick key may hold any spell; the orders take the ones Attack can use, the upkeep list its own.
            if (quickKey || (upkeep ? upkeepTakes(context, member, spellId) : descriptor && !utility))
            {
                entries.push_back({BattleOrderKind::Spell, spellId, false});
            }
        }
    }

    if (!quickKey && !upkeep)
    {
        entries.push_back({BattleOrderKind::Melee, 0, false});
        entries.push_back({BattleOrderKind::Shoot, 0, false});
    }

    std::erase_if(entries, [&matches](const PaletteEntry &entry) { return !matches(entry); });
    return entries;
}

// The palette's search field, right of its label and left of the scroll arrows (page units).
Rect searchRect(const Layout &layout)
{
    const float searchWidth = std::clamp((layout.rightRight - layout.rightLeft - 34) * 0.45f, 80.0f, 150.0f);
    return pageRect(layout, layout.rightRight - 34 - searchWidth, PaletteTop + 3, searchWidth, 15);
}

size_t paletteColumns(const Layout &layout)
{
    return std::max<size_t>(1, size_t((layout.rightRight - layout.rightLeft - 16) / PalettePitch));
}

// The distance slider's position (0-1) of a distance, and back.
float distancePosition(float units)
{
    return units <= DistanceKnee ? 0.5f * units / DistanceKnee
        : 0.5f + 0.5f * (units - DistanceKnee) / (BattleOrderMaximumDistance - DistanceKnee);
}

uint16_t distanceAt(float position)
{
    position = std::clamp(position, 0.0f, 1.0f);
    const float units = position <= 0.5f ? position * 2 * DistanceKnee
        : DistanceKnee + (position - 0.5f) * 2 * (BattleOrderMaximumDistance - DistanceKnee);
    const float step = units < DistanceKnee ? 16.0f : 64.0f;
    return uint16_t(std::clamp(std::round(units / step) * step, 0.0f, float(BattleOrderMaximumDistance)));
}

struct EditorRects
{
    Rect distanceToggle;
    std::array<Rect, 3> distancePresets;
    Rect distanceTrack;
    Rect renewToggle;
    Rect renewTrack;
    Rect allyToggle;
    Rect allyTrack;
    Rect keepToggle;
    Rect keepTrack;
    // The place row: its label, then the three chips.
    Rect placeLabel;
    std::array<Rect, 3> placeChips;
};

// The place row's label takes this much of its width (page units).
constexpr float PlaceLabelWidth = 40;

// The selected order's editor in page units, the rectangles in screen pixels: an attack order's distance, or an
// upkeep spell's renew time, then the ally's HP, the SP kept and the place.
EditorRects editorRects(const Layout &layout, bool upkeep)
{
    const float left = layout.rightLeft + 10;
    const float right = layout.rightRight - 10;
    EditorRects rects;
    float y = EditorTop + 38;

    if (upkeep)
    {
        rects.renewToggle = pageRect(layout, left, y, right - left, 13);
        rects.renewTrack = pageRect(layout, left + 14, y + 18, right - left - 18, 8);
        y += 38;
    }
    else
    {
        rects.distanceToggle = pageRect(layout, left, y, right - left, 13);
        const float chipWidth = (right - left - 14 - 8) / 3;
        float chipX = left + 14;

        for (Rect &chip : rects.distancePresets)
        {
            chip = pageRect(layout, chipX, y + 16, chipWidth, 15);
            chipX += chipWidth + 4;
        }

        rects.distanceTrack = pageRect(layout, left + 14, y + 36, right - left - 18, 8);
        y += 62;
    }

    const float step = upkeep ? 38 : 32;
    rects.allyToggle = pageRect(layout, left, y, right - left, 13);
    rects.allyTrack = pageRect(layout, left + 14, y + 17, right - left - 18, 8);
    y += step;
    rects.keepToggle = pageRect(layout, left, y, right - left, 13);
    rects.keepTrack = pageRect(layout, left + 14, y + 17, right - left - 18, 8);
    y += step;
    rects.placeLabel = pageRect(layout, left, y, PlaceLabelWidth, 15);
    const float placeWidth = (right - left - PlaceLabelWidth - 8) / 3;
    float placeX = left + PlaceLabelWidth;

    for (Rect &chip : rects.placeChips)
    {
        chip = pageRect(layout, placeX, y, placeWidth, 15);
        placeX += placeWidth + 4;
    }

    return rects;
}

Rect rowRect(const Layout &layout, size_t row)
{
    return pageRect(layout, Margin, RowTop + float(row) * RowPitch, layout.leftRight - Margin, RowHeight);
}

Rect rowControlRect(const Layout &layout, size_t row, int control)
{
    const float y = RowTop + float(row) * RowPitch + (RowHeight - 13) / 2;
    return pageRect(layout, layout.leftRight - 6 - float(3 - control) * 16, y, 13, 13);
}

Rect rowToggleRect(const Layout &layout, size_t row)
{
    return pageRect(layout, Margin + 5, RowTop + float(row) * RowPitch + (RowHeight - 11) / 2, 11, 11);
}

float fallbackTop(const Character &member)
{
    return RowTop + float(std::min(member.battleOrders.size(), AttackVisibleRows)) * RowPitch;
}

// The list's scrollbar, in the gap right of the rows: its track, and the thumb for the rows shown.
Rect scrollTrackRect(const Layout &layout, const WindowState &state)
{
    return pageRect(layout, layout.leftRight + 4, RowTop, 5, float(visibleRows(state)) * RowPitch - 3);
}

Rect scrollThumbRect(const Layout &layout, const Character &member, const WindowState &state)
{
    const Rect track = scrollTrackRect(layout, state);
    const size_t count = shownOrders(member, state).size();
    const size_t last = maximumScroll(member, state);
    const float thumbHeight = std::max(16 * layout.page.scale, track.height * float(visibleRows(state)) / float(count));
    const float travel = track.height - thumbHeight;
    return {track.x, track.y + (last > 0 ? travel * float(std::min(state.listScroll, last)) / float(last) : 0),
        track.width, thumbHeight};
}

// The row the scrollbar's thumb shows first with its middle at the pointer.
size_t scrollAt(const Layout &layout, const Character &member, const WindowState &state, float pointerY)
{
    const Rect track = scrollTrackRect(layout, state);
    const Rect thumb = scrollThumbRect(layout, member, state);
    const float travel = track.height - thumb.height;
    const size_t last = maximumScroll(member, state);

    if (travel <= 0 || last == 0)
    {
        return 0;
    }

    const float position = std::clamp((pointerY - track.y - thumb.height / 2) / travel, 0.0f, 1.0f);
    return size_t(std::round(position * float(last)));
}

// The Upkeep key's box, where the quick keys start.
Rect upkeepKeyRect(const Layout &layout)
{
    return pageRect(layout, Margin + 84, QuickTop + 3, 92, 24);
}

// The list switch's two chips, over the rows: their widths depend on the text.
std::array<Rect, 2> listRects(const GameplayObsidianPainter &painter, const Layout &layout)
{
    std::array<Rect, 2> rects;
    float x = Margin;

    for (size_t index = 0; index < rects.size(); ++index)
    {
        const float chipWidth = painter.width(TextFont, 8.5f, Engine::tr(ListNames[index])) + 16;
        rects[index] = pageRect(layout, x, 74, chipWidth, 15);
        x += chipWidth + 3;
    }

    return rects;
}

Rect fallbackChoiceRect(const Layout &layout, const Character &member, bool hold)
{
    return pageRect(layout, layout.leftRight - 6 - (hold ? 48 : 98), fallbackTop(member) + 8, 48, 16);
}

float presetsTop(bool upkeep)
{
    return upkeep ? UpkeepPresetsTop : RowTop + float(BattleOrderLimit + 1) * RowPitch + 22;
}

Rect tabRect(const Layout &layout, size_t index, size_t count)
{
    const float left = 214;
    const float available = layout.width - left - 100;
    const float tabWidth = std::min(86.0f, (available - 4 * float(std::max<size_t>(1, count) - 1)) / float(count));
    return pageRect(layout, left + float(index) * (tabWidth + 4), 20, tabWidth, 42);
}

Rect closeRect(const Layout &layout)
{
    return pageRect(layout, layout.width - Margin - 64, 30, 64, 21);
}

Rect quickSlotRect(const Layout &layout, size_t slot)
{
    const float left = Margin + 70;
    const float pitch = (layout.width - Margin - left) / 5;
    return pageRect(layout, left + float(slot) * pitch, QuickTop, 30, 30);
}

Rect paletteRect(const Layout &layout, size_t visibleIndex)
{
    const size_t columns = paletteColumns(layout);
    const float x = layout.rightLeft + 8 + float(visibleIndex % columns) * PalettePitch;
    const float y = PaletteTop + 22 + float(visibleIndex / columns) * PalettePitch;
    return pageRect(layout, x, y, PaletteIcon, PaletteIcon);
}

// The preset chips' names: the attack plans, or what the upkeep list can add; the last opens the copy menu.
std::vector<std::string_view> presetNames(bool upkeep)
{
    return upkeep ? std::vector<std::string_view>(UpkeepPresetNames.begin(), UpkeepPresetNames.end())
                  : std::vector<std::string_view>(PresetNames.begin(), PresetNames.end());
}

std::string presetsLabel(bool upkeep)
{
    return upkeep ? Engine::tr("Add") : Engine::tr("Start from");
}

// The preset chips and Copy, as the painter lays them out: their widths depend on the text.
std::vector<Rect> presetRects(const GameplayObsidianPainter &painter, const Layout &layout, bool upkeep)
{
    std::vector<Rect> rects;
    float x = Margin + painter.width(TextFont, 9, presetsLabel(upkeep)) + 8;

    for (const std::string_view name : presetNames(upkeep))
    {
        const float chipWidth = painter.width(TextFont, 8.5f, Engine::tr(name)) + 14;
        rects.push_back(pageRect(layout, x, presetsTop(upkeep), chipWidth, 16));
        x += chipWidth + 4;
    }

    return rects;
}

Rect copyMenuRowRect(const std::vector<Rect> &presets, const Layout &layout, size_t row)
{
    const Rect &anchor = presets.back();
    return {anchor.x, anchor.y - (float(row) + 1) * 17 * layout.page.scale, std::max(anchor.width, 100 * layout.page.scale),
        17 * layout.page.scale};
}

Hit hitTest(const GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const Layout &layout,
    const Character &member, float x, float y)
{
    const WindowState &state = window(context);
    const Party &party = *context.partyReadOnly();
    const std::vector<Rect> presets = presetRects(painter, layout, state.upkeep);
    const std::vector<BattleOrder> &orders = shownOrders(member, state);

    if (state.copyMenuOpen)
    {
        size_t row = 0;

        for (size_t index = 0; index < party.members().size(); ++index)
        {
            if (index == state.memberIndex)
            {
                continue;
            }

            if (copyMenuRowRect(presets, layout, row).contains(x, y))
            {
                return {Control::CopyMember, index};
            }

            ++row;
        }
    }

    if (closeRect(layout).contains(x, y))
    {
        return {Control::Close};
    }

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        if (tabRect(layout, index, party.members().size()).contains(x, y))
        {
            return {Control::Tab, index};
        }
    }

    const std::array<Rect, 2> lists = listRects(painter, layout);

    for (size_t index = 0; index < lists.size(); ++index)
    {
        if (lists[index].contains(x, y))
        {
            return {Control::List, index};
        }
    }

    // The rows shown: the scrolled list's order `row` is on line `shown`.
    for (size_t shown = 0; shown < visibleRows(state) && state.listScroll + shown < orders.size(); ++shown)
    {
        const size_t row = state.listScroll + shown;

        if (rowToggleRect(layout, shown).contains(x, y))
        {
            return {Control::RowToggle, row};
        }

        for (int control = 0; control < 3; ++control)
        {
            if (rowControlRect(layout, shown, control).contains(x, y))
            {
                return {control == 0 ? Control::RowUp : control == 1 ? Control::RowDown : Control::RowRemove, row};
            }
        }

        if (rowRect(layout, shown).contains(x, y))
        {
            return {Control::Row, row};
        }
    }

    if (orders.size() > visibleRows(state))
    {
        const Rect track = scrollTrackRect(layout, state);
        const float pad = 3 * layout.page.scale;

        if (Rect{track.x - pad, track.y, track.width + 2 * pad, track.height}.contains(x, y))
        {
            return {Control::ScrollBar};
        }
    }

    if (!state.upkeep && fallbackChoiceRect(layout, member, false).contains(x, y))
    {
        return {Control::FallbackWeapon};
    }

    if (!state.upkeep && fallbackChoiceRect(layout, member, true).contains(x, y))
    {
        return {Control::FallbackHold};
    }

    for (size_t index = 0; index < presets.size(); ++index)
    {
        if (presets[index].contains(x, y))
        {
            return {index + 1 == presets.size() ? Control::CopyMenu : Control::Preset, index};
        }
    }

    for (size_t slot = 0; slot < QuickSlotNames.size() && !state.upkeep; ++slot)
    {
        if (quickSlotRect(layout, slot).contains(x, y))
        {
            return {Control::QuickSlot, slot};
        }
    }

    if (state.upkeep && upkeepKeyRect(layout).contains(x, y))
    {
        return {Control::UpkeepKey};
    }

    const size_t columns = paletteColumns(layout);
    const std::vector<PaletteEntry> entries =
        paletteEntries(context, member, state.armedQuickSlot.has_value(), state.paletteSearch, state.upkeep);
    const size_t first = state.paletteRow * columns;

    for (size_t visible = 0; visible < columns * PaletteRows && first + visible < entries.size(); ++visible)
    {
        if (paletteRect(layout, visible).contains(x, y))
        {
            return {Control::PaletteEntry, first + visible};
        }
    }

    if (searchRect(layout).contains(x, y))
    {
        return {Control::PaletteSearch};
    }

    if (pageRect(layout, layout.rightRight - 28, PaletteTop + 4, 12, 12).contains(x, y))
    {
        return {Control::PaletteScrollUp};
    }

    if (pageRect(layout, layout.rightRight - 14, PaletteTop + 4, 12, 12).contains(x, y))
    {
        return {Control::PaletteScrollDown};
    }

    if (state.selectedOrder && *state.selectedOrder < orders.size())
    {
        const EditorRects editor = editorRects(layout, state.upkeep);
        const BattleOrder &order = orders[*state.selectedOrder];
        // An attack order's distance (not a blow's: its reach is the distance); an upkeep buff's renew time.
        const bool melee = order.kind == BattleOrderKind::Melee || state.upkeep;
        const bool spell = order.kind == BattleOrderKind::Spell;
        const SpellEntry *pSpell = state.upkeep ? orderSpell(context, member, order) : nullptr;
        const bool renews = pSpell != nullptr && isUpkeepBuff(uint32_t(pSpell->id));

        for (size_t chip = 0; chip < editor.distancePresets.size() && !melee; ++chip)
        {
            if (editor.distancePresets[chip].contains(x, y))
            {
                return {Control::DistancePreset, chip};
            }
        }

        for (size_t chip = 0; chip < editor.placeChips.size(); ++chip)
        {
            if (editor.placeChips[chip].contains(x, y))
            {
                return {Control::Place, chip};
            }
        }

        const auto nearTrack = [x, y, &layout](const Rect &track)
        {
            const float pad = 4 * layout.page.scale;
            return Rect{track.x - pad, track.y - pad, track.width + 2 * pad, track.height + 2 * pad}.contains(x, y);
        };

        if (renews && nearTrack(editor.renewTrack))
        {
            return {Control::SliderTrack, size_t(Slider::Renew)};
        }

        if (renews && editor.renewToggle.contains(x, y))
        {
            return {Control::ConditionToggle, size_t(Slider::Renew)};
        }

        if (!melee && nearTrack(editor.distanceTrack))
        {
            return {Control::SliderTrack, size_t(Slider::Distance)};
        }

        if (nearTrack(editor.allyTrack))
        {
            return {Control::SliderTrack, size_t(Slider::Ally)};
        }

        if (spell && nearTrack(editor.keepTrack))
        {
            return {Control::SliderTrack, size_t(Slider::Keep)};
        }

        if (!melee && editor.distanceToggle.contains(x, y))
        {
            return {Control::ConditionToggle, size_t(Slider::Distance)};
        }

        if (editor.allyToggle.contains(x, y))
        {
            return {Control::ConditionToggle, size_t(Slider::Ally)};
        }

        if (spell && editor.keepToggle.contains(x, y))
        {
            return {Control::ConditionToggle, size_t(Slider::Keep)};
        }
    }

    return {};
}

void playSound(const GameplayScreenRuntime &context, SoundId sound)
{
    if (context.audioSystem() != nullptr)
    {
        context.audioSystem()->playCommonSound(sound, GameAudioSystem::PlaybackGroup::Ui);
    }
}

std::string limitText(bool upkeep)
{
    return upkeep ? Engine::tr("At most {count} upkeep spells", {{"count", int64_t(BattleOrderLimit)}})
                  : Engine::tr("At most {count} orders", {{"count", int64_t(BattleOrderLimit)}});
}

// Adds an order at the end of the shown list and selects it; refused at the limit and, in the upkeep list, for a
// spell already there.
bool addOrder(GameplayScreenRuntime &context, Character &member, BattleOrder order)
{
    WindowState &state = window(context);
    std::vector<BattleOrder> &orders = shownOrders(member, state);
    const bool listed = state.upkeep && std::any_of(orders.begin(), orders.end(),
        [&order](const BattleOrder &other) { return other.spellName == order.spellName; });

    if (orders.size() >= BattleOrderLimit || listed)
    {
        playSound(context, SoundId::Fizzle);
        context.setStatusBarEvent(listed ? Engine::tr("Already in the upkeep list") : limitText(state.upkeep));
        return false;
    }

    orders.push_back(std::move(order));
    state.selectedOrder = orders.size() - 1;
    showOrder(state, orders.size() - 1);
    playSound(context, SoundId::ClickSkill);
    return true;
}

// An upkeep order for the spell: a buff is renewed from the default time left on.
BattleOrder upkeepOrderFor(const SpellEntry &spell)
{
    BattleOrder order;
    order.spellName = spell.name;

    if (isUpkeepBuff(uint32_t(spell.id)))
    {
        order.renewBelowMinutes = UpkeepRenewDefaultMinutes;
    }

    return order;
}

void setSlider(const Layout &layout, BattleOrder &order, Slider slider, bool maximum, float pointerX, bool upkeep)
{
    const EditorRects editor = editorRects(layout, upkeep);
    const Rect &track = slider == Slider::Distance ? editor.distanceTrack
        : slider == Slider::Renew ? editor.renewTrack
        : slider == Slider::Ally ? editor.allyTrack : editor.keepTrack;
    const float position = track.width > 0 ? std::clamp((pointerX - track.x) / track.width, 0.0f, 1.0f) : 0.0f;

    if (slider == Slider::Renew)
    {
        const int span = UpkeepRenewMaximumMinutes - UpkeepRenewMinimumMinutes;
        const int value = UpkeepRenewMinimumMinutes + int(std::round(position * span / 5.0f)) * 5;
        order.renewBelowMinutes =
            uint16_t(std::clamp(value, int(UpkeepRenewMinimumMinutes), int(UpkeepRenewMaximumMinutes)));
        return;
    }

    if (slider == Slider::Distance)
    {
        BattleOrderDistance distance = order.distance.value_or(BattleOrderDistance{});
        const uint16_t value = distanceAt(position);

        if (maximum)
        {
            distance.maximum = std::max<uint16_t>(value, uint16_t(distance.minimum + 16));
        }
        else
        {
            distance.minimum = std::min<uint16_t>(value, uint16_t(std::max(0, int(distance.maximum) - 16)));
        }

        order.distance = distance;
    }
    else if (slider == Slider::Ally)
    {
        const int value = AllyMinimum + int(std::round(position * (AllyMaximum - AllyMinimum) / 5.0f)) * 5;
        order.allyHealthBelowPercent = uint8_t(std::clamp(value, AllyMinimum, AllyMaximum));
    }
    else
    {
        const int value = int(std::round(position * KeepMaximum / 5.0f)) * 5;
        order.keepSpellPointsPercent = uint8_t(std::clamp(value, 0, KeepMaximum));
    }
}


// Text centred in a screen rectangle.
void centredText(const GameplayObsidianPainter &painter, const Layout &layout, const std::string &font, float height,
    uint32_t colour, const std::string &value, const Rect &box)
{
    const float x = (box.x + box.width / 2 - layout.page.x) / layout.page.scale;
    const float y = (box.y - layout.page.y) / layout.page.scale + (box.height / layout.page.scale - height) / 2;
    painter.text(font, height, colour, value, x, y, 1);
}

void drawChip(const GameplayObsidianPainter &painter, const Layout &layout, const Rect &box, const std::string &label,
    bool on, bool hovered, bool enabled = true)
{
    painter.fill(box, on ? ChipOnFill : abgr(0x101818));

    if (hovered && !on && enabled)
    {
        painter.fill(box, HoverFill);
    }

    painter.frame(box, on ? ChipOnBorder : ChipBorder);
    centredText(painter, layout, TextFont, 8.5f, !enabled ? Disabled : on ? ChipOnText : Body, label, box);
}

void drawTick(const GameplayObsidianPainter &painter, const Rect &box, bool on, bool enabled = true)
{
    painter.fill(box, abgr(0x0b1111));
    painter.frame(box, on && enabled ? ChipOnBorder : abgr(0x7a7052));

    if (on)
    {
        const float inset = std::max(1.0f, std::round(box.width * 0.25f));
        painter.fill({box.x + inset, box.y + inset, box.width - 2 * inset, box.height - 2 * inset},
            enabled ? Gold : Disabled);
    }
}

void drawIconWell(const GameplayObsidianPainter &painter, const Rect &box, uint32_t border)
{
    painter.fill(box, IconWell);
    painter.frame(box, border);
}

// A weapon order's icon: a sword or a bow from the item icons.
void drawWeaponIcon(GameplayScreenRuntime &context, const Rect &box, BattleOrderKind kind, bool dim)
{
    const std::optional<GameplayHudTextureHandle> texture = context.gameplayUiRuntime().ensureItemIconTextureLoaded(
        kind == BattleOrderKind::Melee ? "7item009" : "7item043");

    if (!texture || texture->width <= 0 || texture->height <= 0)
    {
        return;
    }

    const float fit = std::min(box.width * 0.9f / texture->width, box.height * 0.9f / texture->height);
    const float iconWidth = std::round(texture->width * fit);
    const float iconHeight = std::round(texture->height * fit);
    GameplayHudBatchQuad quad;
    quad.textureHandle = texture->textureHandle;
    quad.x = std::round(box.x + (box.width - iconWidth) / 2);
    quad.y = std::round(box.y + (box.height - iconHeight) / 2);
    quad.width = iconWidth;
    quad.height = iconHeight;
    quad.tintAbgr = dim ? 0xff707070u : 0xffffffffu;
    context.submitHudQuadBatch({quad});
}

void drawOrderIcon(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const Character &member,
    const BattleOrder &order, const Rect &box, bool dim)
{
    const float inset = std::max(1.0f, painter.scale());
    const Rect inner = {box.x + inset, box.y + inset, box.width - 2 * inset, box.height - 2 * inset};

    if (order.kind != BattleOrderKind::Spell)
    {
        drawWeaponIcon(context, inner, order.kind, dim);
        return;
    }

    if (const SpellEntry *pSpell = orderSpell(context, member, order))
    {
        painter.spellIcon(uint32_t(pSpell->id), inner, dim);
    }
}

// A slider: its track, the filled span between the thumbs (from the left with one thumb), the thumbs and the
// melee reach's red span on the distance.
void drawSlider(const GameplayObsidianPainter &painter, const Rect &track, float from, std::optional<float> to,
    bool enabled, std::optional<float> zone)
{
    const float s = painter.scale();
    const Rect bar = {track.x, track.y + track.height / 2 - 2 * s, track.width, 4 * s};
    painter.fill(bar, Track);

    if (zone)
    {
        painter.fill({bar.x, track.y + track.height / 2 - 3 * s, bar.width * *zone, 6 * s}, MeleeZone);
    }

    const float left = to ? from : 0.0f;
    const float right = to ? *to : from;
    painter.fill({bar.x + bar.width * left, bar.y, bar.width * (right - left), bar.height},
        enabled ? TrackFill : Disabled);
    painter.frame(bar, TrackBorder);

    for (const std::optional<float> thumb : {to ? std::optional<float>(from) : std::nullopt, to ? to : from})
    {
        if (!thumb)
        {
            continue;
        }

        const Rect knob = {bar.x + bar.width * *thumb - 3 * s, track.y - 3 * s, 6 * s, track.height + 6 * s};
        painter.fill(knob, enabled ? Thumb : Disabled);
        painter.frame(knob, ThumbEdge);
    }
}

void renderTabs(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const Layout &layout,
    const Party &party, const Hit &hover)
{
    const WindowState &state = window(context);

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        const Character &member = party.members()[index];
        const Rect tab = tabRect(layout, index, party.members().size());
        const bool selected = index == state.memberIndex;
        painter.fill(tab, selected ? abgr(0x222217, 0xf0) : abgr(0x0d1515, 0xe6));

        if (!selected && hover.control == Control::Tab && hover.index == index)
        {
            painter.fill(tab, HoverFill);
        }

        painter.frame(tab, selected ? RowSelectedBorder : abgr(0x3d463f));
        const float s = layout.page.scale;
        const Rect face = {tab.x + 5 * s, tab.y + 6 * s, 23 * s, 30 * s};
        painter.face(member, face, false);
        const float textX = (tab.x - layout.page.x) / s + 33;
        const float textY = (tab.y - layout.page.y) / s;
        const float available = tab.width / s - 37;
        painter.text(NameFont, 11.5f, Ivory, painter.fitted(NameFont, 11.5f, member.name, available), textX, textY + 5);
        painter.text(TextFont, 8, Muted, painter.fitted(TextFont, 8, Engine::localizeKnown(member.className),
            available), textX, textY + 19);
        const int maximum = party.reachableMaximumSpellPoints(index);
        const Rect bar = pageRect(layout, textX, textY + 32, available, 3.5f);

        if (maximum > 0)
        {
            painter.fill(bar, abgr(0x0a0f0f));
            painter.fill({bar.x, bar.y, bar.width * std::clamp(float(member.spellPoints) / maximum, 0.0f, 1.0f),
                bar.height}, abgr(0x79b5f0));
            painter.frame(bar, abgr(0x3c463f));
        }
        else
        {
            painter.text(TextFont, 7.5f, Muted, Engine::tr("no SP"), textX, textY + 29);
        }
    }
}

void renderOrders(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const Layout &layout,
    const Character &member, const Hit &hover)
{
    const WindowState &state = window(context);
    const float s = layout.page.scale;
    const std::vector<BattleOrder> &orders = shownOrders(member, state);
    const std::array<Rect, 2> lists = listRects(painter, layout);

    for (size_t index = 0; index < lists.size(); ++index)
    {
        drawChip(painter, layout, lists[index], Engine::tr(ListNames[index]), state.upkeep == (index == 1),
            hover.control == Control::List && hover.index == index);
    }

    // What the list does, beside its switch: the upkeep list names its key.
    const float hintLeft = (lists.back().x + lists.back().width - layout.page.x) / s + 8;
    const InputBinding upkeepKey = context.settingsSnapshot().keyboard.binding(KeyboardAction::Upkeep);
    const std::string hint = !state.upkeep
        ? Engine::tr("top to bottom; the first order whose conditions all hold is used")
        : upkeepKey.kind == InputBindingKind::None
            ? Engine::tr("the Upkeep key (not set) casts the first that is due")
            : Engine::tr("{key} casts the first that is due; hold it to go on",
                {{"key", inputBindingDisplayName(upkeepKey)}});
    painter.text(TextFont, 8.5f, Muted, painter.fitted(TextFont, 8.5f, hint, layout.leftRight - hintLeft), hintLeft,
        77.5f);

    for (size_t shown = 0; shown < visibleRows(state) && state.listScroll + shown < orders.size(); ++shown)
    {
        const size_t row = state.listScroll + shown;
        const BattleOrder &order = orders[row];
        const Rect box = rowRect(layout, shown);
        const bool selected = state.selectedOrder == row;
        painter.fill(box, selected ? RowSelectedFill : RowFill);

        if (!selected && hover.control == Control::Row && hover.index == row)
        {
            painter.fill(box, HoverFill);
        }

        painter.frame(box, selected ? RowSelectedBorder : RowBorder);
        drawTick(painter, rowToggleRect(layout, shown), order.enabled);
        const float top = RowTop + float(shown) * RowPitch;
        const uint32_t nameColour = order.enabled ? Ivory : Disabled;
        painter.text(TextFont, 9, order.enabled ? Gold : Disabled, std::to_string(row + 1), Margin + 22, top + 10, 1);
        const Rect icon = pageRect(layout, Margin + 30, top + 3, 26, 26);
        drawIconWell(painter, icon, abgr(0x6d6447));
        drawOrderIcon(context, painter, member, order, icon, !order.enabled);
        const float textLeft = Margin + 62;
        const float textRight = layout.leftRight - 62;
        const std::string name = orderName(context, member, order);
        const float nameWidth = painter.text(NameFont, 11.5f, nameColour,
            painter.fitted(NameFont, 11.5f, name, textRight - textLeft), textLeft, top + 3);

        if (const SpellEntry *pSpell = orderSpell(context, member, order))
        {
            const std::optional<uint32_t> cost = context.partyReadOnly() != nullptr
                ? PartySpellSystem::manaCost(*context.partyReadOnly(), member, *context.spellTable(),
                    uint32_t(pSpell->id))
                : std::nullopt;

            if (cost && textLeft + nameWidth + 30 < textRight)
            {
                painter.text(TextFont, 8, Muted, Engine::tr("{points} SP", {{"points", int64_t(*cost)}}),
                    textLeft + nameWidth + 5, top + 5);
            }
        }

        painter.text(TextFont, 8.5f, order.enabled ? abgr(0xcfe2f2) : Disabled,
            painter.fitted(TextFont, 8.5f, conditionSummary(context, member, order, state.upkeep),
                textRight - textLeft), textLeft, top + 18);

        for (int control = 0; control < 3; ++control)
        {
            const Rect button = rowControlRect(layout, shown, control);
            const Control kind = control == 0 ? Control::RowUp : control == 1 ? Control::RowDown : Control::RowRemove;
            const bool usable = (control != 0 || row > 0) && (control != 1 || row + 1 < orders.size());
            painter.fill(button, abgr(0x0b1111));

            if (usable && hover.control == kind && hover.index == row)
            {
                painter.fill(button, HoverFill);
            }

            painter.frame(button, abgr(0x4d5148));
            const float cx = (button.x + button.width / 2 - layout.page.x) / s;
            const float cy = (button.y + button.height / 2 - layout.page.y) / s;
            const uint32_t colour = usable ? Body : abgr(0x3c4238);

            if (control == 0)
            {
                painter.text(TextFont, 9, colour, "^", cx, cy - 2.5f, 1);
            }
            else if (control == 1)
            {
                painter.text(TextFont, 9, colour, "v", cx, cy - 4.5f, 1);
            }
            else
            {
                painter.text(TextFont, 9, colour, "x", cx, cy - 4.5f, 1);
            }
        }
    }

    // A list longer than its rows scrolls.
    if (orders.size() > visibleRows(state))
    {
        const Rect track = scrollTrackRect(layout, state);
        painter.fill(track, Track);
        painter.frame(track, TrackBorder);
        const Rect thumb = scrollThumbRect(layout, member, state);
        painter.fill(thumb, state.draggingScroll || hover.control == Control::ScrollBar ? Thumb : TrackFill);
        painter.frame(thumb, ThumbEdge);
    }

    // The upkeep list has no fallback: under its rows, while there is room, only where the next spell goes.
    if (state.upkeep)
    {
        if (orders.size() < UpkeepVisibleRows)
        {
            const float addTop = RowTop + float(orders.size()) * RowPitch;
            painter.frame(pageRect(layout, Margin, addTop, layout.leftRight - Margin, 20), abgr(0x3a3f35));
            painter.text(TextFont, 8.5f, Muted,
                painter.fitted(TextFont, 8.5f, Engine::tr("+ Add a spell to keep up: click it on the right"),
                    layout.leftRight - Margin - 20),
                Margin + 10, addTop + 5);
        }

        return;
    }

    // The fallback row: always last.
    const float top = fallbackTop(member);
    const Rect box = pageRect(layout, Margin, top, layout.leftRight - Margin, RowHeight);
    painter.fill(box, abgr(0x0b1111, 0xe6));
    painter.frame(box, abgr(0x4d5148));
    const bool hold = member.battleOrderFallback == BattleOrderFallback::Hold;
    painter.text(TextFont, 9, Muted, "~", Margin + 22, top + 11, 1);
    const Rect icon = pageRect(layout, Margin + 30, top + 3, 26, 26);
    drawIconWell(painter, icon, abgr(0x4d5148));

    if (hold)
    {
        centredText(painter, layout, TextFont, 10, Muted, "||", icon);
    }
    else
    {
        drawWeaponIcon(context, {icon.x + s, icon.y + s, icon.width - 2 * s, icon.height - 2 * s},
            BattleOrderKind::Melee, false);
    }

    painter.text(NameFont, 11.5f, Ivory, hold ? Engine::tr("Otherwise: hold") : Engine::tr("Otherwise: the weapon"),
        Margin + 62, top + 3);
    painter.text(TextFont, 8.5f, Muted, hold ? Engine::tr("the press goes to the next ready member")
                                             : Engine::tr("a blow in reach, the ranged weapon beyond"),
        Margin + 62, top + 18);

    for (const bool choice : {false, true})
    {
        drawChip(painter, layout, fallbackChoiceRect(layout, member, choice),
            choice ? Engine::tr("Hold") : Engine::tr("Weapon"), choice == hold,
            hover.control == (choice ? Control::FallbackHold : Control::FallbackWeapon));
    }

    const float addTop = top + RowPitch;
    const Rect add = pageRect(layout, Margin, addTop, layout.leftRight - Margin, 20);
    painter.frame(add, abgr(0x3a3f35));
    painter.text(TextFont, 8.5f, Muted,
        member.battleOrders.size() >= BattleOrderLimit ? limitText(false)
            : state.armedQuickSlot ? Engine::tr("Choose the spell for the quick key on the right")
                                   : Engine::tr("+ Add an order: click a spell or weapon on the right"),
        Margin + 10, addTop + 5);
}

void renderPresets(const GameplayObsidianPainter &painter, const Layout &layout, const Party &party,
    const WindowState &state, const Hit &hover)
{
    const std::vector<Rect> presets = presetRects(painter, layout, state.upkeep);
    const std::vector<std::string_view> names = presetNames(state.upkeep);
    painter.text(TextFont, 9, Muted, presetsLabel(state.upkeep), Margin, presetsTop(state.upkeep) + 2);

    for (size_t index = 0; index < presets.size(); ++index)
    {
        const bool hovered = (hover.control == Control::Preset || hover.control == Control::CopyMenu)
            && hover.index == index;
        drawChip(painter, layout, presets[index], Engine::tr(names[index]),
            index + 1 == presets.size() && state.copyMenuOpen, hovered);
    }

    if (!state.copyMenuOpen)
    {
        return;
    }

    size_t row = 0;

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        if (index == state.memberIndex)
        {
            continue;
        }

        const Rect item = copyMenuRowRect(presets, layout, row++);
        painter.fill(item, hover.control == Control::CopyMember && hover.index == index ? MenuHot : MenuFill);
        painter.frame(item, abgr(0x8c815f));
        centredText(painter, layout, TextFont, 9, Body, party.members()[index].name, item);
    }
}

void renderEditor(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const Layout &layout,
    const Character &member, const Hit &hover)
{
    const WindowState &state = window(context);
    const Rect box = pageRect(layout, layout.rightLeft, EditorTop, layout.rightRight - layout.rightLeft, EditorHeight);
    painter.fill(box, BoxFill);
    painter.frame(box, RowBorder);
    const float left = layout.rightLeft + 10;
    const float right = layout.rightRight - 10;
    const std::vector<BattleOrder> &orders = shownOrders(member, state);

    if (!state.selectedOrder || *state.selectedOrder >= orders.size())
    {
        painter.text(TitleFont, 13, Ivory,
            state.upkeep ? (orders.empty() ? Engine::tr("No upkeep") : Engine::tr("Upkeep"))
                         : (orders.empty() ? Engine::tr("No orders") : Engine::tr("Orders")),
            left, EditorTop + 8);
        float y = EditorTop + 30;
        const std::string hint = !orders.empty()
            ? (state.upkeep ? Engine::tr("Select a spell to set when it is cast.")
                            : Engine::tr("Select an order to set when it is used."))
            : state.upkeep
                ? Engine::tr("The buffs, heals and cures {member} keeps up. The Upkeep key casts the first that is "
                             "due, at its usual cost. Add spells on the right, or the member's buffs or healing "
                             "below.", {{"member", member.name}})
                : Engine::tr("{member} attacks with the weapon: a blow in reach, the ranged weapon beyond. Add a spell "
                             "to cast it first, or start from a plan below.", {{"member", member.name}});

        for (const std::string &line : painter.wrapped(TextFont, 9, hint, right - left))
        {
            painter.text(TextFont, 9, Body, line, left, y);
            y += 13;
        }

        return;
    }

    const size_t selected = *state.selectedOrder;
    const BattleOrder &order = orders[selected];
    const bool melee = order.kind == BattleOrderKind::Melee;
    const bool spell = order.kind == BattleOrderKind::Spell;
    const std::string title = std::to_string(selected + 1) + " \xC2\xB7 " + orderName(context, member, order);
    painter.text(TitleFont, 13, Ivory, painter.fitted(TitleFont, 13, title, right - left), left, EditorTop + 8);
    painter.text(TextFont, 8.5f, Muted,
        painter.fitted(TextFont, 8.5f,
            state.upkeep ? Engine::tr("Cast when it is due and every ticked condition holds.")
                         : Engine::tr("Used when every ticked condition holds; none ticked: always."),
            right - left),
        left, EditorTop + 24);
    const EditorRects rects = editorRects(layout, state.upkeep);
    const float s = layout.page.scale;
    const auto rowText = [&painter, &layout, s](const Rect &toggle, const std::string &label, const std::string &value,
                             bool on, bool usable)
    {
        drawTick(painter, {toggle.x, toggle.y + 2 * s, 9 * s, 9 * s}, on, usable);
        const float y = (toggle.y - layout.page.y) / s + 0.5f;
        const float x = (toggle.x - layout.page.x) / s;
        painter.text(TextFont, 9, !usable ? Disabled : on ? ChipOnText : Body, label, x + 14, y);
        painter.text(TextFont, 9, !usable ? Disabled : on ? Ivory : Muted, value, x + toggle.width / s, y, 2);
    };

    // An upkeep buff's renew time.
    if (state.upkeep)
    {
        const SpellEntry *pSpell = orderSpell(context, member, order);
        const bool renews = pSpell != nullptr && isUpkeepBuff(uint32_t(pSpell->id));
        const int minutes = order.renewBelowMinutes.value_or(UpkeepRenewDefaultMinutes);
        rowText(rects.renewToggle, Engine::tr("Renew when less is left than"),
            !renews ? Engine::tr("buffs only")
                    : Engine::tr("{minutes} min", {{"minutes", int64_t(minutes)}}),
            renews && order.renewBelowMinutes.has_value(), renews);

        if (renews)
        {
            drawSlider(painter, rects.renewTrack,
                float(minutes - UpkeepRenewMinimumMinutes)
                    / float(UpkeepRenewMaximumMinutes - UpkeepRenewMinimumMinutes),
                std::nullopt, order.renewBelowMinutes.has_value(), std::nullopt);
        }
    }

    // Distance.
    if (!state.upkeep)
    {
        const BattleOrderDistance distance = order.distance.value_or(BattleOrderDistance{0, BattleOrderMeleeReach});
        const std::string value = melee ? Engine::tr("the weapon's reach")
            : distance.minimum == 0 && distance.maximum == BattleOrderMeleeReach ? Engine::tr("in melee reach")
            : distance.minimum == BattleOrderMeleeReach && distance.maximum >= BattleOrderMaximumDistance
                ? Engine::tr("beyond melee reach")
            : distance.maximum >= BattleOrderMaximumDistance
                ? Engine::tr("{minimum} units or more", {{"minimum", int64_t(distance.minimum)}})
                : Engine::tr("{minimum}-{maximum} units",
                    {{"minimum", int64_t(distance.minimum)}, {"maximum", int64_t(distance.maximum)}});
        rowText(rects.distanceToggle, Engine::tr("Target distance"), value, order.distance.has_value() || melee,
            !melee);

        if (!melee)
        {
            const bool on = order.distance.has_value();
            const bool inReach = on && distance.minimum == 0 && distance.maximum == BattleOrderMeleeReach;
            const bool beyond = on && distance.minimum == BattleOrderMeleeReach
                && distance.maximum >= BattleOrderMaximumDistance;
            const std::array<std::string, 3> labels = {Engine::tr("In melee reach"), Engine::tr("Beyond melee reach"),
                Engine::tr("Custom")};
            const std::array<bool, 3> chosen = {inReach, beyond, on && !inReach && !beyond};

            for (size_t chip = 0; chip < labels.size(); ++chip)
            {
                drawChip(painter, layout, rects.distancePresets[chip], labels[chip], chosen[chip],
                    hover.control == Control::DistancePreset && hover.index == chip);
            }

            drawSlider(painter, rects.distanceTrack, distancePosition(battleOrderDistanceBound(distance.minimum)),
                distance.maximum >= BattleOrderMaximumDistance ? 1.0f
                                                               : distancePosition(float(distance.maximum)),
                on, distancePosition(battleOrderDistanceBound(BattleOrderMeleeReach)));
            const float trackLeft = (rects.distanceTrack.x - layout.page.x) / s;
            const float trackWidth = rects.distanceTrack.width / s;
            const float tickY = (rects.distanceTrack.y - layout.page.y) / s + 12;
            painter.text(TextFont, 7.5f, abgr(0xd27a62), Engine::tr("melee"),
                trackLeft + trackWidth * distancePosition(battleOrderDistanceBound(BattleOrderMeleeReach)), tickY, 1);

            for (const int units : {1024, 2048, 3072, 4096})
            {
                painter.text(TextFont, 7.5f, Muted, std::to_string(units),
                    trackLeft + trackWidth * distancePosition(float(units)), tickY, 1);
            }

            painter.text(TextFont, 7.5f, Muted, Engine::tr("any"), trackLeft + trackWidth, tickY, 2);
        }
    }

    // An ally's HP.
    {
        const int percent = order.allyHealthBelowPercent.value_or(50);
        rowText(rects.allyToggle, Engine::tr("An ally's HP is below"), std::to_string(percent) + " %",
            order.allyHealthBelowPercent.has_value(), true);
        drawSlider(painter, rects.allyTrack, float(percent - AllyMinimum) / float(AllyMaximum - AllyMinimum),
            std::nullopt, order.allyHealthBelowPercent.has_value(), std::nullopt);
    }

    // SP kept.
    {
        const int percent = order.keepSpellPointsPercent.value_or(30);
        rowText(rects.keepToggle, Engine::tr("Keep SP after casting, at least"),
            spell ? std::to_string(percent) + " %" : Engine::tr("spells only"),
            spell && order.keepSpellPointsPercent.has_value(), spell);

        if (spell)
        {
            drawSlider(painter, rects.keepTrack, float(percent) / float(KeepMaximum), std::nullopt,
                order.keepSpellPointsPercent.has_value(), std::nullopt);
        }
    }

    // The place.
    {
        const float labelX = (rects.placeLabel.x - layout.page.x) / s;
        const float labelY = (rects.placeLabel.y - layout.page.y) / s + 3;
        painter.text(TextFont, 9, order.place != BattleOrderPlace::Anywhere ? ChipOnText : Body,
            painter.fitted(TextFont, 9, Engine::tr("Place"), PlaceLabelWidth - 4), labelX, labelY);

        for (size_t chip = 0; chip < rects.placeChips.size(); ++chip)
        {
            drawChip(painter, layout, rects.placeChips[chip], Engine::tr(PlaceNames[chip]),
                size_t(order.place) == chip, hover.control == Control::Place && hover.index == chip);
        }
    }
}

void renderPalette(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const Layout &layout,
    const Character &member, const Hit &hover)
{
    const WindowState &state = window(context);
    const Rect box = pageRect(layout, layout.rightLeft, PaletteTop, layout.rightRight - layout.rightLeft,
        PaletteHeight);
    painter.fill(box, BoxFill);
    painter.frame(box, state.armedQuickSlot ? RowSelectedBorder : RowBorder);
    const std::string label = state.armedQuickSlot
        ? Engine::tr("Choose the spell for {key}", {{"key", Engine::tr(QuickSlotNames[*state.armedQuickSlot])}})
        : state.upkeep ? Engine::tr("Add: {member}'s buffs, heals and cures", {{"member", member.name}})
                       : Engine::tr("Add: {member}'s spells and weapons", {{"member", member.name}});
    const Rect search = searchRect(layout);
    const float searchLeft = (search.x - layout.page.x) / layout.page.scale;
    painter.text(TextFont, 8.5f, Gold, painter.fitted(TextFont, 8.5f, label, searchLeft - layout.rightLeft - 14),
        layout.rightLeft + 8, PaletteTop + 6);
    painter.fill(search, abgr(0x070b0b));

    if (!state.paletteSearchActive && hover.control == Control::PaletteSearch)
    {
        painter.fill(search, HoverFill);
    }

    painter.frame(search, state.paletteSearchActive ? RowSelectedBorder : ChipBorder);
    const bool caret = state.paletteSearchActive && SDL_GetTicks() / 500 % 2 == 0;
    const std::string shown = state.paletteSearch.empty() && !state.paletteSearchActive
        ? Engine::tr("Search") : state.paletteSearch + (caret ? "|" : "");
    painter.text(TextFont, 8.5f, state.paletteSearch.empty() && !state.paletteSearchActive ? Muted : Ivory,
        painter.fitted(TextFont, 8.5f, shown, search.width / layout.page.scale - 8), searchLeft + 4, PaletteTop + 5);
    const std::vector<PaletteEntry> entries =
        paletteEntries(context, member, state.armedQuickSlot.has_value(), state.paletteSearch, state.upkeep);
    const size_t columns = paletteColumns(layout);
    const size_t first = state.paletteRow * columns;

    for (size_t visible = 0; visible < columns * PaletteRows && first + visible < entries.size(); ++visible)
    {
        const PaletteEntry &entry = entries[first + visible];
        const Rect icon = paletteRect(layout, visible);
        const bool hovered = hover.control == Control::PaletteEntry && hover.index == first + visible;
        drawIconWell(painter, icon, hovered ? RowSelectedBorder : abgr(0x5f5a43));

        if (entry.clear)
        {
            centredText(painter, layout, TextFont, 9, Bad, "x", icon);
        }
        else if (entry.kind != BattleOrderKind::Spell)
        {
            drawWeaponIcon(context, icon, entry.kind, false);
        }
        else
        {
            const float inset = std::max(1.0f, painter.scale());
            painter.spellIcon(entry.spellId, {icon.x + inset, icon.y + inset, icon.width - 2 * inset,
                icon.height - 2 * inset}, false);
        }
    }

    const size_t rows = (entries.size() + columns - 1) / columns;

    if (rows > PaletteRows)
    {
        for (const bool down : {false, true})
        {
            const Rect arrow = pageRect(layout, layout.rightRight - (down ? 14 : 28), PaletteTop + 4, 12, 12);
            const bool usable = down ? state.paletteRow + PaletteRows < rows : state.paletteRow > 0;
            painter.frame(arrow, abgr(0x4d5148));
            centredText(painter, layout, TextFont, 9, usable ? Body : abgr(0x3c4238), down ? "v" : "^", arrow);
        }
    }

    // The hovered entry's name under the icons.
    if (hover.control == Control::PaletteEntry && hover.index < entries.size())
    {
        const PaletteEntry &entry = entries[hover.index];
        std::string name = entry.clear ? Engine::tr("Clear the quick key")
            : entry.kind == BattleOrderKind::Melee ? Engine::tr("Melee: a blow in reach")
            : entry.kind == BattleOrderKind::Shoot ? Engine::tr("Shoot: the ranged weapon")
                                                   : std::string();

        if (name.empty() && context.spellTable() != nullptr)
        {
            if (const SpellEntry *pSpell = context.spellTable()->findById(int(entry.spellId)))
            {
                name = spellDisplayName(context, member, *pSpell);
            }
        }

        painter.text(TextFont, 8.5f, Ivory, name, layout.rightLeft + 8, PaletteTop + PaletteHeight - 14);
    }
}

void renderQuickKeys(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const Layout &layout,
    const Character &member, const Hit &hover)
{
    const WindowState &state = window(context);
    painter.text(TextFont, 9, Gold, Engine::tr("QUICK KEYS"), Margin + 2, QuickTop + 9);

    for (size_t slot = 0; slot < QuickSlotNames.size(); ++slot)
    {
        const Rect icon = quickSlotRect(layout, slot);
        const bool armed = state.armedQuickSlot == slot;
        const bool hovered = hover.control == Control::QuickSlot && hover.index == slot;
        drawIconWell(painter, icon, armed || hovered ? RowSelectedBorder : abgr(0x6d6447));
        const std::string &bound = slot == 0 ? member.quickSpellName : member.extraQuickSpellNames[slot - 1];
        const SpellEntry *pSpell = !bound.empty() && context.spellTable() != nullptr
            ? context.spellTable()->findByName(bound, spellKnownBy(member)) : nullptr;

        if (pSpell != nullptr)
        {
            const float inset = std::max(1.0f, painter.scale());
            painter.spellIcon(uint32_t(pSpell->id),
                {icon.x + inset, icon.y + inset, icon.width - 2 * inset, icon.height - 2 * inset}, false);
        }
        else
        {
            centredText(painter, layout, TextFont, 10, abgr(0x6f6a52), "+", icon);
        }

        if (armed)
        {
            const float s = painter.scale();
            painter.frame({icon.x - s, icon.y - s, icon.width + 2 * s, icon.height + 2 * s}, Gold);
        }

        const float x = (icon.x + icon.width - layout.page.x) / layout.page.scale + 5;
        const float y = (icon.y - layout.page.y) / layout.page.scale;
        const float available = (layout.width - Margin - 70) / 5 - 40;
        painter.text(TextFont, 8.5f, Body, painter.fitted(TextFont, 8.5f, Engine::tr(QuickSlotNames[slot]), available),
            x, y + 3);
        painter.text(TextFont, 8.5f, pSpell != nullptr ? Muted : abgr(0x6f7468),
            painter.fitted(TextFont, 8.5f, pSpell != nullptr ? spellDisplayName(context, member, *pSpell)
                                                             : Engine::tr("empty"), available), x, y + 16);
    }
}

// Binds the Upkeep key (nothing clears it) and says so; a key another action has is refused, since one press would
// then do both, and the window says which action.
void bindUpkeepKey(GameplayScreenRuntime &context, const InputBinding &binding)
{
    GameSettings &settings = context.mutableSettings();
    window(context).upkeepKeyRefusal.clear();

    if (binding.kind == InputBindingKind::None)
    {
        settings.keyboard.setBinding(KeyboardAction::Upkeep, binding);
        context.commitSettingsChange();
        playSound(context, SoundId::Fizzle);
        context.setStatusBarEvent(Engine::tr("Upkeep key cleared"));
        return;
    }

    for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
    {
        const InputBinding other = settings.keyboard.binding(definition.action);

        if (definition.action != KeyboardAction::Upkeep && other.kind == binding.kind
            && other.scancode == binding.scancode)
        {
            playSound(context, SoundId::Fizzle);
            window(context).upkeepKeyRefusal = Engine::tr("{key} is taken by {action}. Choose another key.",
                {{"key", inputBindingDisplayName(binding)}, {"action", Engine::tr(definition.label)}});
            return;
        }
    }

    settings.keyboard.setBinding(KeyboardAction::Upkeep, binding);
    context.commitSettingsChange();
    playSound(context, SoundId::ClickSkill);
    context.setStatusBarEvent(Engine::tr("Upkeep key: {key}", {{"key", inputBindingDisplayName(binding)}}));
}

// The Upkeep key, where the quick keys are while the attack orders show: its box binds the key in place.
void renderUpkeepKey(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const Layout &layout,
    const Hit &hover)
{
    const WindowState &state = window(context);
    painter.text(TextFont, 9, Gold, Engine::tr("UPKEEP KEY"), Margin + 2, QuickTop + 9);
    const Rect box = upkeepKeyRect(layout);
    const bool hovered = hover.control == Control::UpkeepKey;
    painter.fill(box, state.capturingUpkeepKey ? ChipOnFill : IconWell);

    if (hovered && !state.capturingUpkeepKey)
    {
        painter.fill(box, HoverFill);
    }

    painter.frame(box, state.capturingUpkeepKey || hovered ? RowSelectedBorder : abgr(0x6d6447));
    const InputBinding binding = context.settingsSnapshot().keyboard.binding(KeyboardAction::Upkeep);
    const bool unbound = binding.kind == InputBindingKind::None;
    const float boxWidth = box.width / layout.page.scale;
    centredText(painter, layout, NameFont, 12,
        state.capturingUpkeepKey ? ChipOnText : unbound ? Disabled : Ivory,
        painter.fitted(NameFont, 12, state.capturingUpkeepKey ? "..." : inputBindingDisplayName(binding),
            boxWidth - 8),
        box);
    const float textLeft = (box.x + box.width - layout.page.x) / layout.page.scale + 10;
    const float available = layout.width - Margin - textLeft;
    painter.text(TextFont, 8.5f, Body,
        painter.fitted(TextFont, 8.5f,
            state.capturingUpkeepKey ? Engine::tr("Press the key to use. Escape keeps the old one.")
                                     : Engine::tr("Click the box, then press a key. A right click clears it."),
            available),
        textLeft, QuickTop + 4);
    painter.text(TextFont, 8.5f, state.upkeepKeyRefusal.empty() ? Muted : Bad,
        painter.fitted(TextFont, 8.5f,
            !state.upkeepKeyRefusal.empty() ? state.upkeepKeyRefusal
                : Engine::tr("One key for the whole party: each ready member casts what is due on their list."),
            available),
        textLeft, QuickTop + 17);
}

void renderWindow(GameplayScreenRuntime &context, int width, int height)
{
    const Party *pParty = context.partyReadOnly();
    const Character *pMember = editedMember(context);

    if (pParty == nullptr || pMember == nullptr || !context.hasHudRenderResources())
    {
        return;
    }

    const Layout layout = layoutFor(width, height);
    context.prepareHudView(width, height);
    context.gameplayUiRuntime().clearRenderedInspectableHudItems();
    const GameplayObsidianPainter painter(context, layout.page);
    painter.fill({0, 0, float(width), float(height)}, Shade);
    // The Settings frame as a nine-slice: its x2 corners at their own size, only the plain edges stretched.
    painter.sliced("hud_x2/menus/omenu_frame.png", layout.window(), FrameEdge, layout.page.scale / 2);
    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    const Hit hover = pInput != nullptr
        ? hitTest(context, painter, layout, *pMember, pInput->pointerX, pInput->pointerY) : Hit{};
    painter.text(TitleFont, 20, Ivory, Engine::tr("Battle Orders"), Margin + 2, 20);
    painter.text(TextFont, 8.5f, Muted, Engine::tr("Attack, upkeep and the quick keys, per member"), Margin + 3, 47);
    renderTabs(context, painter, layout, *pParty, hover);
    const Rect close = closeRect(layout);
    painter.button(close, Engine::tr("Close"), false, true, hover.control == Control::Close, false);
    painter.fill(pageRect(layout, Margin, 70, layout.width - 2 * Margin, 0.6f), Rule);
    renderOrders(context, painter, layout, *pMember, hover);
    renderEditor(context, painter, layout, *pMember, hover);
    renderPalette(context, painter, layout, *pMember, hover);
    painter.fill(pageRect(layout, Margin, QuickTop - 9, layout.width - 2 * Margin, 0.6f), Rule);

    if (window(context).upkeep)
    {
        renderUpkeepKey(context, painter, layout, hover);
    }
    else
    {
        renderQuickKeys(context, painter, layout, *pMember, hover);
    }

    renderPresets(painter, layout, *pParty, window(context), hover);
}

// The Quick Reference's Orders row shows this many order icons, and its box lists this many orders.
constexpr size_t QuickReferenceIcons = 6;
constexpr size_t QuickReferenceLines = 10;

// The spellbook's spell menu: its rows (0 Quick Cast, 1-4 the quick spells, 5 add an order, 6 add to the upkeep list,
// 7 the window).
constexpr size_t MenuRows = 8;
constexpr size_t MenuUpkeepRow = 6;
constexpr float MenuWidth = 200;
constexpr float MenuHeader = 30;
constexpr float MenuRowHeight = 17;

Rect menuRect(const GameplayScreenRuntime &context, int width, int height)
{
    const MenuState &state = menu(context);
    const float scale = float(height) / 480.0f;
    const float menuWidth = MenuWidth * scale;
    const float menuHeight = (MenuHeader + MenuRowHeight * MenuRows + 6) * scale;
    return {std::clamp(state.x, 0.0f, std::max(0.0f, float(width) - menuWidth)),
        std::clamp(state.y, 0.0f, std::max(0.0f, float(height) - menuHeight)), menuWidth, menuHeight};
}

std::optional<size_t> menuRowAt(const GameplayScreenRuntime &context, int width, int height, float x, float y)
{
    const Rect box = menuRect(context, width, height);
    const float scale = float(height) / 480.0f;

    for (size_t row = 0; row < MenuRows; ++row)
    {
        const float top = box.y + (MenuHeader + float(row) * MenuRowHeight + (row >= 5 ? 4 : 0)) * scale;

        if (Rect{box.x, top, box.width, MenuRowHeight * scale}.contains(x, y))
        {
            return row;
        }
    }

    return std::nullopt;
}
}

void GameplayBattleOrders::assignQuickSlot(
    GameplayScreenRuntime &context, size_t memberIndex, size_t slot, const SpellEntry *pSpell)
{
    Party *pParty = context.party();
    Character *pMember = pParty != nullptr ? pParty->member(memberIndex) : nullptr;

    if (pMember == nullptr || slot >= QuickSlotNames.size())
    {
        return;
    }

    std::string &bound = slot == 0 ? pMember->quickSpellName : pMember->extraQuickSpellNames[slot - 1];

    if (pSpell == nullptr)
    {
        bound.clear();
        playSound(context, SoundId::Fizzle);
        context.setStatusBarEvent(slot == 0 ? Engine::tr("Quick spell cleared")
                                            : Engine::tr("Quick spell {slot} cleared", {{"slot", int64_t(slot)}}));
        return;
    }

    bound = pSpell->name;
    playSound(context, SoundId::ClickSkill);
    context.playSpeechReaction(memberIndex, SpeechId::SetQuickSpell, true);
    const std::string name = spellDisplayName(context, *pMember, *pSpell);
    context.setStatusBarEvent(slot == 0
            ? Engine::tr("Quick spell set to {spell}", {{"spell", name}})
            : Engine::tr("Quick spell {slot} set to {spell}", {{"slot", int64_t(slot)}, {"spell", name}}));
}

void GameplayBattleOrders::assignAttackSpell(
    GameplayScreenRuntime &context, size_t memberIndex, const SpellEntry *pSpell)
{
    Party *pParty = context.party();
    Character *pMember = pParty != nullptr ? pParty->member(memberIndex) : nullptr;

    if (pMember == nullptr)
    {
        return;
    }

    setAttackSpell(pSpell != nullptr ? pSpell->name : std::string(), pMember->battleOrders,
        pMember->battleOrderFallback);

    if (pSpell == nullptr)
    {
        playSound(context, SoundId::Fizzle);
        context.setStatusBarEvent(Engine::tr("Attack spell cleared"));
        return;
    }

    playSound(context, SoundId::ClickSkill);
    context.playSpeechReaction(memberIndex, SpeechId::SetQuickSpell, true);
    context.setStatusBarEvent(
        Engine::tr("Attack spell set to {spell}", {{"spell", spellDisplayName(context, *pMember, *pSpell)}}));
}

bool GameplayBattleOrders::isOpen(const GameplayScreenRuntime &context)
{
    return context.spellbookReadOnly().active && context.spellbookReadOnly().battleOrders.open;
}

void GameplayBattleOrders::open(GameplayScreenRuntime &context, bool closesBook)
{
    const Party *pParty = context.partyReadOnly();

    if (!context.spellbookReadOnly().active || pParty == nullptr || pParty->members().empty())
    {
        return;
    }

    WindowState &state = window(context);
    state = {};
    state.open = true;
    state.closesBook = closesBook;
    state.memberIndex = std::min(pParty->activeMemberIndex(), pParty->members().size() - 1);
    const Character *pMember = pParty->member(state.memberIndex);

    if (pMember != nullptr && !pMember->battleOrders.empty())
    {
        state.selectedOrder = 0;
    }

    menu(context).open = false;
}

void GameplayBattleOrders::close(GameplayScreenRuntime &context)
{
    if (window(context).closesBook)
    {
        context.closeSpellbookOverlay();
        return;
    }

    window(context) = {};
}

void GameplayBattleOrders::render(GameplayScreenRuntime &context, int width, int height)
{
    if (isOpen(context) && width > 0 && height > 0)
    {
        renderWindow(context, width, height);
    }
}

void GameplayBattleOrders::handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    Character *pMember = editedMember(context);
    Party *pParty = context.party();

    if (!isOpen(context) || pMember == nullptr || pParty == nullptr || context.spellTable() == nullptr)
    {
        return;
    }

    WindowState &state = window(context);
    Character &member = *pMember;
    const Layout layout = layoutFor(input.screenWidth, input.screenHeight);
    const GameplayObsidianPainter painter(context, layout.page);

    const bool escapeHeld = input.keyboardState()[SDL_SCANCODE_ESCAPE];
    const bool escapePressed =
        (escapeHeld || input.scancodePressCount(SDL_SCANCODE_ESCAPE) > 0) && !state.escapeLatch;
    state.escapeLatch = escapeHeld || escapePressed;

    state.listScroll = std::min(state.listScroll, maximumScroll(member, state));

    // The Upkeep key's box waits for a key: the first bindable one pressed is taken, unless another action has it.
    if (state.capturingUpkeepKey)
    {
        if (escapePressed)
        {
            state.capturingUpkeepKey = false;
            return;
        }

        for (int code = SDL_SCANCODE_UNKNOWN + 1; code < SDL_SCANCODE_COUNT; ++code)
        {
            const SDL_Scancode scancode = SDL_Scancode(code);

            // A key the settings can name, as the keyboard settings bind.
            if (scancode == SDL_SCANCODE_ESCAPE || input.scancodePressCount(scancode) == 0
                || parseKeyboardBindingName(keyboardBindingName(scancode)) != scancode)
            {
                continue;
            }

            state.capturingUpkeepKey = false;
            bindUpkeepKey(context, keyboardInputBinding(scancode));
            return;
        }
    }

    // The search field: typed text filters the palette; Enter keeps it, Escape clears it.
    if (state.paletteSearchActive)
    {
        if (escapePressed)
        {
            state.paletteSearch.clear();
            state.paletteSearchActive = false;
            state.paletteRow = 0;
            return;
        }

        const std::string before = state.paletteSearch;
        Engine::Utf8::appendPrintable(state.paletteSearch, input.textInput, 24);

        for (uint16_t count = input.scancodePressCount(SDL_SCANCODE_BACKSPACE); count > 0; --count)
        {
            if (!state.paletteSearch.empty())
            {
                Engine::Utf8::popBack(state.paletteSearch);
            }
        }

        if (input.scancodePressCount(SDL_SCANCODE_RETURN) > 0 || input.scancodePressCount(SDL_SCANCODE_KP_ENTER) > 0)
        {
            state.paletteSearchActive = false;
        }

        if (state.paletteSearch != before)
        {
            state.paletteRow = 0;
        }
    }

    if (escapePressed)
    {
        if (state.copyMenuOpen)
        {
            state.copyMenuOpen = false;
        }
        else if (state.armedQuickSlot)
        {
            state.armedQuickSlot.reset();
        }
        else
        {
            close(context);
        }

        return;
    }

    // The scrollbar follows the pointer while the button is held.
    if (state.draggingScroll)
    {
        state.listScroll = scrollAt(layout, member, state, input.pointerY);
        state.draggingScroll = input.leftMouseButton.held;
        return;
    }

    // A slider follows the pointer while the button is held.
    if (state.draggedSlider >= 0)
    {
        if (state.selectedOrder && *state.selectedOrder < shownOrders(member, state).size())
        {
            setSlider(layout, shownOrders(member, state)[*state.selectedOrder], Slider(state.draggedSlider),
                state.draggingMaximum, input.pointerX, state.upkeep);
        }

        if (!input.leftMouseButton.held)
        {
            state.draggedSlider = -1;
        }

        return;
    }

    const std::vector<PaletteEntry> entries =
        paletteEntries(context, member, state.armedQuickSlot.has_value(), state.paletteSearch, state.upkeep);
    const size_t columns = paletteColumns(layout);
    const size_t paletteRows = (entries.size() + columns - 1) / columns;
    const size_t lastRow = paletteRows > PaletteRows ? paletteRows - PaletteRows : 0;
    state.paletteRow = std::min(state.paletteRow, lastRow);

    if (input.mouseWheelDelta != 0.0f
        && pageRect(layout, layout.rightLeft, PaletteTop, layout.rightRight - layout.rightLeft, PaletteHeight)
            .contains(input.pointerX, input.pointerY))
    {
        state.paletteRow = input.mouseWheelDelta > 0 ? (state.paletteRow > 0 ? state.paletteRow - 1 : 0)
                                                     : std::min(lastRow, state.paletteRow + 1);
    }

    // The wheel over the rows scrolls the list.
    if (input.mouseWheelDelta != 0.0f
        && pageRect(layout, Margin, RowTop, layout.rightLeft - Margin, float(visibleRows(state)) * RowPitch)
            .contains(input.pointerX, input.pointerY))
    {
        const size_t last = maximumScroll(member, state);
        state.listScroll = input.mouseWheelDelta > 0 ? (state.listScroll > 0 ? state.listScroll - 1 : 0)
                                                     : std::min(last, state.listScroll + 1);
    }

    const Hit hit = hitTest(context, painter, layout, member, input.pointerX, input.pointerY);

    // A right click clears a quick key, the Upkeep key or the search.
    if (input.rightMouseButton.pressed && hit.control == Control::QuickSlot)
    {
        assignQuickSlot(context, state.memberIndex, hit.index, nullptr);
        return;
    }

    if (input.rightMouseButton.pressed && hit.control == Control::UpkeepKey)
    {
        state.capturingUpkeepKey = false;
        bindUpkeepKey(context, InputBinding{});
        return;
    }

    if (input.rightMouseButton.pressed && hit.control == Control::PaletteSearch)
    {
        state.paletteSearch.clear();
        state.paletteRow = 0;
        return;
    }

    if (!input.leftMouseButton.pressed)
    {
        return;
    }

    // A click anywhere else takes the focus from the search; its text keeps filtering. It also ends the wait for the
    // Upkeep key, which its own box toggles.
    state.paletteSearchActive = hit.control == Control::PaletteSearch;
    state.capturingUpkeepKey = hit.control == Control::UpkeepKey && !state.capturingUpkeepKey;
    state.upkeepKeyRefusal.clear();

    if (hit.control != Control::CopyMenu && hit.control != Control::CopyMember)
    {
        state.copyMenuOpen = false;
    }

    std::vector<BattleOrder> &orders = shownOrders(member, state);
    BattleOrder *pSelected = state.selectedOrder && *state.selectedOrder < orders.size()
        ? &orders[*state.selectedOrder] : nullptr;

    switch (hit.control)
    {
        case Control::None:
        case Control::PaletteSearch:
            break;
        case Control::Close:
            close(context);
            break;
        case Control::Tab:
            if (hit.index != state.memberIndex)
            {
                const bool closesBook = state.closesBook;
                const bool upkeep = state.upkeep;
                state = {};
                state.open = true;
                state.closesBook = closesBook;
                state.upkeep = upkeep;
                state.memberIndex = hit.index;
                const Character *pOther = pParty->member(hit.index);

                if (pOther != nullptr && !shownOrders(*pOther, state).empty())
                {
                    state.selectedOrder = 0;
                }
            }
            break;
        case Control::List:
            if (state.upkeep != (hit.index == 1))
            {
                state.upkeep = hit.index == 1;
                state.selectedOrder = shownOrders(member, state).empty() ? std::nullopt : std::optional<size_t>(0);
                state.armedQuickSlot.reset();
                state.paletteRow = 0;
                state.listScroll = 0;
            }
            break;
        case Control::Row:
            state.selectedOrder = hit.index;
            state.armedQuickSlot.reset();
            break;
        case Control::RowToggle:
            orders[hit.index].enabled = !orders[hit.index].enabled;
            state.selectedOrder = hit.index;
            break;
        case Control::RowUp:
        case Control::RowDown:
        {
            const bool up = hit.control == Control::RowUp;

            if ((up && hit.index > 0) || (!up && hit.index + 1 < orders.size()))
            {
                const size_t other = up ? hit.index - 1 : hit.index + 1;
                std::swap(orders[hit.index], orders[other]);
                state.selectedOrder = other;
                showOrder(state, other);
            }
            break;
        }
        case Control::RowRemove:
            orders.erase(orders.begin() + std::ptrdiff_t(hit.index));
            state.selectedOrder = orders.empty()
                ? std::nullopt
                : std::optional<size_t>(std::min(hit.index, orders.size() - 1));
            playSound(context, SoundId::Fizzle);
            break;
        case Control::FallbackWeapon:
            member.battleOrderFallback = BattleOrderFallback::Weapon;
            break;
        case Control::FallbackHold:
            member.battleOrderFallback = BattleOrderFallback::Hold;
            break;
        case Control::Preset:
            if (state.upkeep)
            {
                // The upkeep chips add to the list what it lacks; the last added spell is selected.
                const size_t before = orders.size();
                addUpkeepPreset(member, *pParty, *context.spellTable(),
                    hit.index == 0 ? UpkeepPreset::Buffs : UpkeepPreset::Healing);

                if (orders.size() == before)
                {
                    playSound(context, SoundId::Fizzle);
                    context.setStatusBarEvent(orders.size() >= BattleOrderLimit ? limitText(true)
                                                                                : Engine::tr("Nothing to add"));
                    break;
                }

                state.selectedOrder = orders.size() - 1;
                showOrder(state, orders.size() - 1);
                playSound(context, SoundId::ClickSkill);
                break;
            }

            applyPreset(member, *context.spellTable(), Preset(hit.index));
            state.selectedOrder = orders.empty() ? std::nullopt : std::optional<size_t>(0);
            state.listScroll = 0;
            playSound(context, SoundId::ClickSkill);
            break;
        case Control::CopyMenu:
            state.copyMenuOpen = !state.copyMenuOpen;
            break;
        case Control::CopyMember:
            if (const Character *pSource = pParty->member(hit.index))
            {
                if (state.upkeep)
                {
                    copyUpkeep(member, *pSource, *pParty, *context.spellTable());
                }
                else
                {
                    copyOrders(member, *pSource, *context.spellTable());
                }

                state.selectedOrder = orders.empty() ? std::nullopt : std::optional<size_t>(0);
                state.listScroll = 0;
                context.setStatusBarEvent(
                    state.upkeep ? Engine::tr("Copied {member}'s upkeep", {{"member", pSource->name}})
                                 : Engine::tr("Copied {member}'s orders", {{"member", pSource->name}}));
                playSound(context, SoundId::ClickSkill);
            }

            state.copyMenuOpen = false;
            break;
        case Control::PaletteEntry:
        {
            const PaletteEntry &entry = entries[hit.index];

            if (state.armedQuickSlot)
            {
                const SpellEntry *pSpell = entry.clear ? nullptr : context.spellTable()->findById(int(entry.spellId));
                assignQuickSlot(context, state.memberIndex, *state.armedQuickSlot, pSpell);
                state.armedQuickSlot.reset();
                state.paletteRow = 0;
                break;
            }

            BattleOrder order;
            order.kind = entry.kind;

            if (entry.kind == BattleOrderKind::Spell)
            {
                const SpellEntry *pSpell = context.spellTable()->findById(int(entry.spellId));

                if (pSpell == nullptr)
                {
                    break;
                }

                order = state.upkeep ? upkeepOrderFor(*pSpell) : order;
                order.spellName = pSpell->name;
            }
            else if (entry.kind == BattleOrderKind::Shoot)
            {
                order.distance = BattleOrderDistance{BattleOrderMeleeReach, BattleOrderMaximumDistance};
            }

            addOrder(context, member, order);
            break;
        }
        case Control::PaletteScrollUp:
            state.paletteRow = state.paletteRow > 0 ? state.paletteRow - 1 : 0;
            break;
        case Control::PaletteScrollDown:
            state.paletteRow = std::min(lastRow, state.paletteRow + 1);
            break;
        case Control::QuickSlot:
            state.armedQuickSlot = state.armedQuickSlot == hit.index ? std::nullopt : std::optional<size_t>(hit.index);
            state.paletteRow = 0;
            break;
        case Control::UpkeepKey:
            // Toggled above with the focus.
            break;
        case Control::ScrollBar:
            state.draggingScroll = true;
            state.listScroll = scrollAt(layout, member, state, input.pointerY);
            break;
        case Control::ConditionToggle:
            if (pSelected != nullptr)
            {
                BattleOrder &order = *pSelected;

                if (Slider(hit.index) == Slider::Distance)
                {
                    order.distance = order.distance ? std::nullopt
                        : std::optional<BattleOrderDistance>(BattleOrderDistance{0, BattleOrderMeleeReach});
                }
                else if (Slider(hit.index) == Slider::Renew)
                {
                    order.renewBelowMinutes =
                        order.renewBelowMinutes ? std::nullopt : std::optional<uint16_t>(UpkeepRenewDefaultMinutes);
                }
                else if (Slider(hit.index) == Slider::Ally)
                {
                    order.allyHealthBelowPercent =
                        order.allyHealthBelowPercent ? std::nullopt : std::optional<uint8_t>(50);
                }
                else
                {
                    order.keepSpellPointsPercent =
                        order.keepSpellPointsPercent ? std::nullopt : std::optional<uint8_t>(30);
                }
            }
            break;
        case Control::DistancePreset:
            if (pSelected != nullptr)
            {
                BattleOrder &order = *pSelected;

                if (hit.index == 0)
                {
                    order.distance = BattleOrderDistance{0, BattleOrderMeleeReach};
                }
                else if (hit.index == 1)
                {
                    order.distance = BattleOrderDistance{BattleOrderMeleeReach, BattleOrderMaximumDistance};
                }
                else if (!order.distance || (order.distance->minimum == 0
                             && order.distance->maximum == BattleOrderMeleeReach)
                    || (order.distance->minimum == BattleOrderMeleeReach
                        && order.distance->maximum >= BattleOrderMaximumDistance))
                {
                    order.distance = BattleOrderDistance{0, 1024};
                }
            }
            break;
        case Control::SliderTrack:
            if (pSelected != nullptr)
            {
                BattleOrder &order = *pSelected;
                const Slider slider = Slider(hit.index);
                state.draggedSlider = int(slider);
                state.draggingMaximum = false;

                if (slider == Slider::Distance)
                {
                    const BattleOrderDistance distance =
                        order.distance.value_or(BattleOrderDistance{0, BattleOrderMeleeReach});
                    order.distance = distance;
                    const Rect track = editorRects(layout, state.upkeep).distanceTrack;
                    const float at = track.width > 0 ? (input.pointerX - track.x) / track.width : 0;
                    const float low = distancePosition(battleOrderDistanceBound(distance.minimum));
                    const float high = distance.maximum >= BattleOrderMaximumDistance
                        ? 1.0f : distancePosition(float(distance.maximum));
                    state.draggingMaximum = std::abs(at - high) <= std::abs(at - low);
                }

                setSlider(layout, order, slider, state.draggingMaximum, input.pointerX, state.upkeep);
            }
            break;
        case Control::Place:
            if (pSelected != nullptr)
            {
                pSelected->place = BattleOrderPlace(hit.index);
            }
            break;
    }
}

bool GameplayBattleOrders::spellMenuOpen(const GameplayScreenRuntime &context)
{
    return context.spellbookReadOnly().active && context.spellbookReadOnly().spellMenu.open;
}

void GameplayBattleOrders::openSpellMenu(GameplayScreenRuntime &context, uint32_t spellId, float x, float y)
{
    MenuState &state = menu(context);
    state.open = true;
    state.spellId = spellId;
    state.x = x;
    state.y = y;
}

void GameplayBattleOrders::closeSpellMenu(GameplayScreenRuntime &context)
{
    menu(context).open = false;
}

void GameplayBattleOrders::renderSpellMenu(GameplayScreenRuntime &context, int width, int height)
{
    const Party *pParty = context.partyReadOnly();
    const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;
    const SpellEntry *pSpell = context.spellTable() != nullptr
        ? context.spellTable()->findById(int(menu(context).spellId)) : nullptr;

    if (!spellMenuOpen(context) || pMember == nullptr || pSpell == nullptr || width <= 0 || height <= 0)
    {
        return;
    }

    const Rect box = menuRect(context, width, height);
    GameplayResolvedHudLayoutElement page;
    page.x = box.x;
    page.y = box.y;
    page.scale = float(height) / 480.0f;
    page.width = box.width;
    page.height = box.height;
    context.prepareHudView(width, height);
    const GameplayObsidianPainter painter(context, page);
    painter.fill(box, MenuFill);
    painter.frame(box, abgr(0x8c815f));
    painter.spellIcon(uint32_t(pSpell->id), painter.rect(6, 5, 20, 20), false);
    painter.text(TitleFont, 11, Ivory, painter.fitted(TitleFont, 11, spellDisplayName(context, *pMember, *pSpell),
        MenuWidth - 36), 31, 2);
    painter.text(TextFont, 7.5f, Muted, Engine::tr("assign for {member}", {{"member", pMember->name}}), 31, 16.5f);
    painter.fill(painter.rect(0, MenuHeader - 2, MenuWidth, 0.6f), Rule);
    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    const std::optional<size_t> hot =
        pInput != nullptr ? menuRowAt(context, width, height, pInput->pointerX, pInput->pointerY) : std::nullopt;

    for (size_t row = 0; row < MenuRows; ++row)
    {
        const float top = MenuHeader + float(row) * MenuRowHeight + (row >= 5 ? 4 : 0);

        if (row == 5)
        {
            painter.fill(painter.rect(0, top - 3, MenuWidth, 0.6f), Rule);
        }

        if (hot == row)
        {
            painter.fill(painter.rect(1, top, MenuWidth - 2, MenuRowHeight), MenuHot);
        }

        std::string label;
        std::string current;

        if (row < QuickSlotNames.size())
        {
            const std::string &bound = row == 0 ? pMember->quickSpellName : pMember->extraQuickSpellNames[row - 1];
            const bool same = bound == pSpell->name;
            label = same ? Engine::tr("Clear {key}", {{"key", Engine::tr(QuickSlotNames[row])}})
                         : row == 0 ? Engine::tr("Set as Quick Cast")
                                    : Engine::tr("Put on {key}", {{"key", Engine::tr(QuickSlotNames[row])}});
            current = bound.empty() || same ? std::string() : Engine::localize(bound, "spell");
        }
        else if (row == 5)
        {
            label = Engine::tr("Add to {member}'s attack orders", {{"member", pMember->name}});
        }
        else if (row == MenuUpkeepRow)
        {
            label = Engine::tr("Add to {member}'s upkeep", {{"member", pMember->name}});
        }
        else
        {
            label = Engine::tr("Open Battle Orders");
        }

        // The upkeep list takes only its own spells.
        const bool usable = row != MenuUpkeepRow || upkeepTakes(context, *pMember, uint32_t(pSpell->id));
        const float labelWidth = painter.text(TextFont, 9, !usable ? Disabled : hot == row ? ChipOnText : Body,
            painter.fitted(TextFont, 9, label, MenuWidth - 16), 8, top + 3);

        if (!current.empty() && 8 + labelWidth + 6 < MenuWidth - 8)
        {
            painter.text(TextFont, 8, Muted, painter.fitted(TextFont, 8, current, MenuWidth - 22 - labelWidth),
                MenuWidth - 8, top + 4, 2);
        }
    }
}

void GameplayBattleOrders::handleSpellMenuInput(GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    Party *pParty = context.party();
    const SpellEntry *pSpell = context.spellTable() != nullptr
        ? context.spellTable()->findById(int(menu(context).spellId)) : nullptr;

    if (!spellMenuOpen(context) || pParty == nullptr || pParty->activeMember() == nullptr || pSpell == nullptr)
    {
        closeSpellMenu(context);
        return;
    }

    if (input.scancodePressCount(SDL_SCANCODE_ESCAPE) > 0 || input.rightMouseButton.pressed)
    {
        closeSpellMenu(context);
        menu(context).rightHeld = input.rightMouseButton.held;
        return;
    }

    if (!input.leftMouseButton.pressed)
    {
        return;
    }

    const std::optional<size_t> row =
        menuRowAt(context, input.screenWidth, input.screenHeight, input.pointerX, input.pointerY);
    const size_t memberIndex = pParty->activeMemberIndex();
    Character &member = *pParty->activeMember();

    // A spell the upkeep list does not take leaves the menu open.
    if (row == MenuUpkeepRow && !upkeepTakes(context, member, uint32_t(pSpell->id)))
    {
        return;
    }

    closeSpellMenu(context);

    if (!row)
    {
        return;
    }

    if (*row < QuickSlotNames.size())
    {
        const std::string &bound = *row == 0 ? member.quickSpellName : member.extraQuickSpellNames[*row - 1];
        assignQuickSlot(context, memberIndex, *row, bound == pSpell->name ? nullptr : pSpell);
        return;
    }

    open(context, false);

    if (*row == 5)
    {
        BattleOrder order;
        order.spellName = pSpell->name;
        addOrder(context, member, order);
    }
    else if (*row == MenuUpkeepRow)
    {
        window(context).upkeep = true;
        window(context).selectedOrder = member.upkeepOrders.empty() ? std::nullopt : std::optional<size_t>(0);
        addOrder(context, member, upkeepOrderFor(*pSpell));
    }
}

void GameplayBattleOrders::renderQuickReferenceOrders(GameplayScreenRuntime &context, int width, int height)
{
    const Party *pParty = context.partyReadOnly();
    const std::optional<GameplayResolvedHudLayoutElement> root =
        context.resolveHudLayoutElement("QuickReferenceRoot", width, height, 0, 0);
    const std::optional<GameplayResolvedHudLayoutElement> row =
        context.resolveHudLayoutElement("QuickReferenceOrdersLabel", width, height, 0, 0);

    if (pParty == nullptr || !root || !row || context.spellTable() == nullptr)
    {
        return;
    }

    const GameplayObsidianPainter painter(context, *root);
    const float s = root->scale;
    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    std::optional<size_t> pointed;
    Rect pointedCell;

    for (size_t index = 0; index < std::min<size_t>(pParty->members().size(), 5); ++index)
    {
        const Character &member = pParty->members()[index];
        const std::optional<GameplayResolvedHudLayoutElement> column = context.resolveHudLayoutElement(
            "QuickReferenceMemberColumn" + std::to_string(index + 1), width, height, 0, 0);

        if (!column)
        {
            continue;
        }

        const Rect cell = {column->x, row->y, column->width, row->height};
        std::vector<const BattleOrder *> shown;

        for (const BattleOrder &order : member.battleOrders)
        {
            if (order.enabled)
            {
                shown.push_back(&order);
            }
        }

        const bool hold = member.battleOrderFallback == BattleOrderFallback::Hold;

        if (shown.empty())
        {
            const float labelX = (cell.x + cell.width / 2 - root->x) / s;
            const float labelY = (cell.y - root->y) / s + 1;
            painter.text(NameFont, 12, Ivory, hold ? Engine::tr("Hold") : Engine::tr("Weapon"), labelX, labelY, 1);
        }
        else
        {
            // Up to six orders as icons; of more, the first five and how many follow. The fallback's mark is last.
            const size_t iconCount = shown.size() > QuickReferenceIcons ? QuickReferenceIcons - 1 : shown.size();
            const bool more = shown.size() > iconCount;
            const size_t count = iconCount + (more ? 1 : 0) + 1;
            const float gap = 2 * s;
            const float icon = std::min(cell.height - 2 * s, (cell.width - 8 * s - gap * float(count - 1)) / count);
            float x = cell.x + (cell.width - (icon * count + gap * float(count - 1))) / 2;
            const float y = cell.y + (cell.height - icon) / 2;

            for (size_t index = 0; index < iconCount; ++index)
            {
                const Rect box = {x, y, icon, icon};
                drawIconWell(painter, box, abgr(0x5f5a43));
                drawOrderIcon(context, painter, member, *shown[index], box, false);
                x += icon + gap;
            }

            if (more)
            {
                centredText(painter, Layout{*root, 640}, TextFont, 8, Body,
                    "+" + std::to_string(shown.size() - iconCount), {x, y, icon, icon});
                x += icon + gap;
            }

            const Rect end = {x, y, icon, icon};
            painter.frame(end, abgr(0x4d5148));

            if (hold)
            {
                centredText(painter, Layout{*root, 640}, TextFont, 8, Muted, "||", end);
            }
            else
            {
                drawWeaponIcon(context, end, BattleOrderKind::Melee, true);
            }
        }

        if (pInput != nullptr && cell.contains(pInput->pointerX, pInput->pointerY))
        {
            pointed = index;
            pointedCell = cell;
        }
    }

    if (!pointed)
    {
        return;
    }

    // The pointed member's orders and quick keys in a box above the row: the first orders that fit over the row, and
    // how many follow.
    const Character &member = pParty->members()[*pointed];
    std::vector<std::pair<std::string, std::string>> lines;
    const size_t listed = std::min(member.battleOrders.size(), QuickReferenceLines);

    for (size_t index = 0; index < listed; ++index)
    {
        const BattleOrder &order = member.battleOrders[index];
        lines.emplace_back(orderName(context, member, order), conditionSummary(context, member, order, false));
    }

    if (listed < member.battleOrders.size())
    {
        lines.emplace_back(
            Engine::tr("and {count} more", {{"count", int64_t(member.battleOrders.size() - listed)}}), std::string());
    }

    lines.emplace_back(member.battleOrderFallback == BattleOrderFallback::Hold ? Engine::tr("Otherwise: hold")
                                                                                : Engine::tr("Otherwise: the weapon"),
        std::string());
    constexpr float BoxWidth = 290;
    // The upkeep spells that are on, in a line or two under the orders.
    std::string upkeep;

    for (const BattleOrder &order : member.upkeepOrders)
    {
        if (order.enabled)
        {
            upkeep += (upkeep.empty() ? Engine::tr("Upkeep") + ": " : ", ") + orderName(context, member, order);
        }
    }

    const GameplayResolvedHudLayoutElement measurePage = *root;
    const std::vector<std::string> upkeepLines = upkeep.empty() ? std::vector<std::string>{}
        : GameplayObsidianPainter(context, measurePage).wrapped(TextFont, 8.5f, upkeep, BoxWidth - 16);
    const size_t upkeepShown = std::min<size_t>(upkeepLines.size(), 2);
    const float boxHeight = 24 + float(lines.size()) * 14 + float(upkeepShown) * 12 + (upkeepShown > 0 ? 6 : 0) + 36;
    const float left = std::clamp((pointedCell.x + pointedCell.width / 2 - root->x) / s - BoxWidth / 2, 4.0f,
        640.0f - BoxWidth - 4);
    const float top = std::max(4.0f, (pointedCell.y - root->y) / s - boxHeight - 4);
    const Rect box = painter.rect(left, top, BoxWidth, boxHeight);
    painter.fill(box, MenuFill);
    painter.frame(box, abgr(0x8c815f));
    painter.text(TitleFont, 11, Ivory, Engine::tr("{member}: on Attack", {{"member", member.name}}), left + 8,
        top + 4);
    float y = top + 23;

    for (size_t line = 0; line < lines.size(); ++line)
    {
        const bool last = line + 1 == lines.size();
        const bool off = line < listed && !member.battleOrders[line].enabled;
        const std::string number = last ? "~" : line < listed ? std::to_string(line + 1) : "";
        painter.text(TextFont, 9, Gold, number, left + 12, y, 1);
        const float nameWidth = painter.text(TextFont, 9, off ? Disabled : Ivory, lines[line].first, left + 20, y);

        if (!lines[line].second.empty())
        {
            painter.text(TextFont, 8.5f, off ? Disabled : Muted,
                painter.fitted(TextFont, 8.5f, lines[line].second, BoxWidth - 34 - nameWidth),
                left + 26 + nameWidth, y + 0.5f);
        }

        y += 14;
    }

    if (upkeepShown > 0)
    {
        painter.fill(painter.rect(left + 6, y + 2, BoxWidth - 12, 0.6f), Rule);

        for (size_t line = 0; line < upkeepShown; ++line)
        {
            painter.text(TextFont, 8.5f, Body, upkeepLines[line], left + 8, y + 6 + float(line) * 12);
        }

        y += 6 + float(upkeepShown) * 12;
    }

    painter.fill(painter.rect(left + 6, y + 2, BoxWidth - 12, 0.6f), Rule);
    std::string keys;

    for (size_t slot = 0; slot < QuickSlotNames.size(); ++slot)
    {
        const std::string &bound = slot == 0 ? member.quickSpellName : member.extraQuickSpellNames[slot - 1];

        if (!bound.empty())
        {
            keys += (keys.empty() ? "" : "   ") + Engine::tr(QuickSlotNames[slot]) + ": "
                + Engine::localize(bound, "spell");
        }
    }

    const std::vector<std::string> keyLines = painter.wrapped(TextFont, 8.5f,
        keys.empty() ? Engine::tr("No quick keys set") : keys, BoxWidth - 16);

    for (size_t line = 0; line < std::min<size_t>(keyLines.size(), 2); ++line)
    {
        painter.text(TextFont, 8.5f, Body, keyLines[line], left + 8, y + 6 + float(line) * 12);
    }
}

void GameplayBattleOrders::applyPreset(Character &member, const SpellTable &spellTable, Preset preset)
{
    member.battleOrders.clear();
    member.battleOrderFallback = BattleOrderFallback::Weapon;
    const auto addSpell = [&member, &spellTable](uint32_t spellId, std::optional<uint8_t> allyBelow)
    {
        const SpellEntry *pSpell = spellTable.findById(int(spellId));

        if (pSpell == nullptr || !member.knowsSpell(spellId) || member.battleOrders.size() >= BattleOrderLimit)
        {
            return;
        }

        BattleOrder order;
        order.spellName = pSpell->name;
        order.allyHealthBelowPercent = allyBelow;
        member.battleOrders.push_back(order);
    };

    switch (preset)
    {
        case Preset::Fighter:
            break;
        case Preset::Archer:
        {
            BattleOrder order;
            order.kind = BattleOrderKind::Shoot;
            order.distance = BattleOrderDistance{BattleOrderMeleeReach, BattleOrderMaximumDistance};
            member.battleOrders.push_back(order);
            break;
        }
        case Preset::Caster:
        {
            // The strongest known single-target missile: the highest in its school's book, the later school on a tie.
            std::optional<uint32_t> best;
            uint32_t bestOrdinal = 0;

            for (const uint32_t spellId : member.knownSpellIds)
            {
                const std::optional<PartySpellDescriptor> descriptor = PartySpellSystem::describeSpell(spellId);
                const SpellbookSchoolUiDefinition *pSchool = findSpellbookSchoolUiDefinitionForSpellId(spellId);

                if (!descriptor || pSchool == nullptr || descriptor->targetKind != PartySpellCastTargetKind::Actor
                    || descriptor->effectKind != PartySpellCastEffectKind::Projectile)
                {
                    continue;
                }

                const uint32_t ordinal = spellId - pSchool->firstSpellId;

                if (!best || ordinal > bestOrdinal || (ordinal == bestOrdinal && spellId > *best))
                {
                    best = spellId;
                    bestOrdinal = ordinal;
                }
            }

            if (best)
            {
                addSpell(*best, std::nullopt);
            }

            break;
        }
        case Preset::Healer:
            addSpell(uint32_t(SpellId::Heal), uint8_t(50));

            for (const SpellId cure : {SpellId::CurePoison, SpellId::CureDisease, SpellId::CureWeakness,
                     SpellId::RemoveFear, SpellId::CureParalysis, SpellId::CureInsanity, SpellId::RemoveCurse})
            {
                addSpell(uint32_t(cure), std::nullopt);
            }

            member.battleOrderFallback = BattleOrderFallback::Hold;
            break;
    }
}

void GameplayBattleOrders::copyOrders(Character &member, const Character &source, const SpellTable &spellTable)
{
    member.battleOrders.clear();

    for (const BattleOrder &order : source.battleOrders)
    {
        if (order.kind == BattleOrderKind::Spell)
        {
            const SpellEntry *pSpell = spellTable.findByName(order.spellName, spellKnownBy(member));

            if (pSpell == nullptr || !member.knowsSpell(uint32_t(pSpell->id)))
            {
                continue;
            }
        }

        member.battleOrders.push_back(order);
    }

    member.battleOrderFallback = source.battleOrderFallback;
}

size_t GameplayBattleOrders::addUpkeepPreset(
    Character &member, const Party &party, const SpellTable &spellTable, UpkeepPreset preset)
{
    size_t added = 0;
    const auto knows = [&member, &party](SpellId spell)
    {
        return member.knowsSpell(uint32_t(spell)) && upkeepTakes(party, member, uint32_t(spell));
    };
    const auto add = [&](SpellId spell, std::optional<uint8_t> allyBelow, BattleOrderPlace place)
    {
        const SpellEntry *pSpell = spellTable.findById(int(spell));
        const bool listed = pSpell != nullptr
            && std::any_of(member.upkeepOrders.begin(), member.upkeepOrders.end(),
                [pSpell](const BattleOrder &order) { return order.spellName == pSpell->name; });

        if (pSpell == nullptr || listed || !knows(spell) || member.upkeepOrders.size() >= BattleOrderLimit)
        {
            return;
        }

        BattleOrder order = upkeepOrderFor(*pSpell);
        order.allyHealthBelowPercent = allyBelow;
        order.place = place;
        member.upkeepOrders.push_back(order);
        ++added;
    };

    if (preset == UpkeepPreset::Healing)
    {
        add(SpellId::Heal, uint8_t(AllyMaximum), BattleOrderPlace::Anywhere);

        for (const SpellId cure : {SpellId::CurePoison, SpellId::CureDisease, SpellId::CureWeakness,
                 SpellId::RemoveFear, SpellId::CureParalysis, SpellId::CureInsanity, SpellId::RemoveCurse})
        {
            add(cure, std::nullopt, BattleOrderPlace::Anywhere);
        }

        return added;
    }

    // The strongest first. A wider spell the member knows stands for the ones it gives.
    const bool power = knows(SpellId::HourOfPower);
    const bool protection = knows(SpellId::DayOfProtection);
    const bool boon = knows(SpellId::TravelersBoon);

    for (const SpellId buff : {SpellId::DayOfGods, SpellId::HourOfPower, SpellId::DayOfProtection,
             SpellId::ProtectionFromMagic, SpellId::Preservation, SpellId::PainReflection, SpellId::Hammerhands,
             SpellId::Regeneration, SpellId::TravelersBoon})
    {
        add(buff, std::nullopt, BattleOrderPlace::Anywhere);
    }

    for (const SpellId buff : {SpellId::Bless, SpellId::Heroism, SpellId::Haste, SpellId::Shield, SpellId::StoneSkin})
    {
        if (!power)
        {
            add(buff, std::nullopt, BattleOrderPlace::Anywhere);
        }
    }

    for (const SpellId buff : {SpellId::FireResistance, SpellId::AirResistance, SpellId::WaterResistance,
             SpellId::EarthResistance, SpellId::MindResistance, SpellId::BodyResistance})
    {
        if (!protection)
        {
            add(buff, std::nullopt, BattleOrderPlace::Anywhere);
        }
    }

    if (!protection && !boon)
    {
        add(SpellId::WizardEye, std::nullopt, BattleOrderPlace::Anywhere);
    }

    if (!boon)
    {
        add(SpellId::TorchLight, std::nullopt, BattleOrderPlace::Indoors);
    }

    return added;
}

void GameplayBattleOrders::copyUpkeep(
    Character &member, const Character &source, const Party &party, const SpellTable &spellTable)
{
    member.upkeepOrders.clear();

    for (const BattleOrder &order : source.upkeepOrders)
    {
        const SpellEntry *pSpell = spellTable.findByName(order.spellName, spellKnownBy(member));

        if (pSpell != nullptr && member.knowsSpell(uint32_t(pSpell->id))
            && upkeepTakes(party, member, uint32_t(pSpell->id)))
        {
            member.upkeepOrders.push_back(order);
        }
    }
}
}
