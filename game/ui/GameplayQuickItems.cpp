#include "game/ui/GameplayQuickItems.h"

#include "game/app/GameSettings.h"
#include "game/app/KeyboardBindings.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/items/InventoryBags.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/QuickItemSlots.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/party/SpellSchool.h"
#include "game/rules/GameRules.h"
#include "game/rules/ItemRules.h"
#include "game/tables/ItemTable.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayUiSkin.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <optional>
#include <string>
#include <tuple>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// The study's colours (maw_potion_radial_20261025 index.html), as ABGR.
constexpr uint32_t abgr(uint32_t rgb, uint32_t alpha = 0xff)
{
    return alpha << 24 | (rgb & 0xffu) << 16 | (rgb & 0xff00u) | (rgb >> 16 & 0xffu);
}

constexpr uint32_t Ivory = abgr(0xefe0bc);
constexpr uint32_t Label = abgr(0xe6d1a8);
constexpr uint32_t Body = abgr(0xc8c7a7);
constexpr uint32_t Muted = abgr(0x9fa594);
constexpr uint32_t Gold = abgr(0xe3c185);
constexpr uint32_t Warn = abgr(0xffb347);
constexpr uint32_t Bad = abgr(0xff6a5a);
constexpr uint32_t Disc = abgr(0x13201e);
constexpr uint32_t Dim = abgr(0x0a1312, 0xd8);
constexpr uint32_t Badge = abgr(0x0b1212);
constexpr uint32_t BadgeBorder = abgr(0x8c815f);
constexpr uint32_t Socket = abgr(0x050a0a);
constexpr uint32_t PanelFill = abgr(0x070e0e, 0xf0);
constexpr uint32_t PanelBorder = abgr(0x8c815f);
constexpr uint32_t ChipFill = abgr(0x0d1716, 0xcc);
constexpr uint32_t ChipBorder = abgr(0x5d6449);
constexpr uint32_t ChipOnFill = abgr(0x2b2a1a, 0xcc);
constexpr uint32_t ChipOnBorder = abgr(0xd6bb80);
constexpr uint32_t RowHighlight = abgr(0xc9b07a, 0x26);
constexpr uint32_t RowRule = abgr(0xffffff, 0x10);
constexpr uint32_t Track = abgr(0x2a3829);
constexpr uint32_t Thumb = abgr(0xac8d6a);

// The picker's text: upright and heavier than the bitmap Lucida (the enemy labels' face).
constexpr char TextFont[] = "alegreya_semibold";

// A tap of the wheel key opens the ring and leaves it open; a longer hold uses the slot it is released over.
constexpr uint64_t WheelHoldTicks = 250;

struct Circle
{
    float x = 0;
    float y = 0;
    float radius = 0;

    bool contains(float pointX, float pointY) const
    {
        return std::hypot(pointX - x, pointY - y) <= radius;
    }
};

struct Box
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

// The ring above a portrait: the hub, the six slots (slot 1 on top, clockwise) and the dimmed disc behind them, in
// the portrait's face units.
struct RingLayout
{
    Circle hub;
    Circle backdrop;
    std::array<Circle, QuickItemSlotCount> slots = {};
    float unit = 1;
};

std::optional<GameplayResolvedHudLayoutElement> faceRect(GameplayScreenRuntime &context, int width, int height,
    size_t member)
{
    return context.resolvePartyPortraitRect(width, height, member);
}

// The round button at a portrait's upper right, outside the mana arc: about 40 degrees above the horizontal from the
// face's centre, one radius past the arc's outer edge, and short of the next portrait's HP arc. None unless the
// Quick item rings setting shows them.
std::optional<Circle> buttonCircle(GameplayScreenRuntime &context, int width, int height, size_t member)
{
    const std::optional<GameplayResolvedHudLayoutElement> face = faceRect(context, width, height, member);

    if (!face || !context.settingsSnapshot().quickItemRings)
    {
        return std::nullopt;
    }

    return Circle{face->x + face->width * 1.234f, face->y + face->height * 0.043f, face->height * 0.13f};
}

std::optional<RingLayout> ringLayout(GameplayScreenRuntime &context, int width, int height, size_t member)
{
    const std::optional<GameplayResolvedHudLayoutElement> face = faceRect(context, width, height, member);

    if (!face)
    {
        return std::nullopt;
    }

    RingLayout layout;
    const float faceHeight = face->height;
    const float radius = faceHeight * 0.88f;
    const float slotRadius = faceHeight * 0.29f;
    layout.unit = faceHeight / 128.0f;
    const float reach = radius + slotRadius + 6 * layout.unit;
    const float x = std::clamp(face->x + face->width / 2, reach, float(width) - reach);
    const float y = face->y - faceHeight * 1.46f;
    layout.hub = {x, y, faceHeight * 0.39f};
    layout.backdrop = {x, y, reach + 4 * layout.unit};

    for (size_t slot = 0; slot < QuickItemSlotCount; ++slot)
    {
        const float angle = (-90.0f + 60.0f * float(slot)) * 3.14159265f / 180.0f;
        layout.slots[slot] = {x + radius * std::cos(angle), y + radius * std::sin(angle), slotRadius};
    }

    return layout;
}

// The picker beside the ring, on the side with more room: the slot's title and bottle rule, the list of what the
// party carries, its scrollbar, and Clear slot and Close.
struct PickerLayout
{
    Box panel;
    std::array<Box, 2> rules = {};
    Box list;
    float rowHeight = 0;
    size_t visibleRows = 0;
    Box track;
    Box clear;
    Box close;
    float unit = 1;
};

std::optional<PickerLayout> pickerLayout(GameplayScreenRuntime &context, int width, int height, size_t member)
{
    const std::optional<RingLayout> ring = ringLayout(context, width, height, member);

    if (!ring)
    {
        return std::nullopt;
    }

    PickerLayout layout;
    const float u = ring->unit;
    layout.unit = u;
    const float panelWidth = 300 * u;
    const float panelHeight = 2 * ring->backdrop.radius;
    const bool right = ring->backdrop.x < float(width) / 2;
    const float x = right ? ring->backdrop.x + ring->backdrop.radius + 8 * u
                          : ring->backdrop.x - ring->backdrop.radius - 8 * u - panelWidth;
    const float y = std::clamp(ring->backdrop.y - ring->backdrop.radius, 4 * u, float(height) - panelHeight - 4 * u);
    layout.panel = {std::clamp(x, 4 * u, float(width) - panelWidth - 4 * u), y, panelWidth, panelHeight};
    const Box &panel = layout.panel;
    layout.rules[1] = {panel.x + panel.width - 10 * u - 84 * u, panel.y + 10 * u, 84 * u, 22 * u};
    layout.rules[0] = {layout.rules[1].x - 4 * u - 84 * u, panel.y + 10 * u, 84 * u, 22 * u};
    const float footerHeight = 30 * u;
    layout.list = {panel.x + 8 * u, panel.y + 40 * u, panel.width - 24 * u, panel.height - 40 * u - footerHeight - 6 * u};
    layout.rowHeight = 38 * u;
    layout.visibleRows = size_t(std::max(1.0f, std::floor(layout.list.height / layout.rowHeight)));
    layout.track = {layout.list.x + layout.list.width + 4 * u, layout.list.y, 5 * u, layout.list.height};
    layout.close = {panel.x + panel.width - 10 * u - 76 * u, panel.y + panel.height - footerHeight, 76 * u, 22 * u};
    layout.clear = {layout.close.x - 6 * u - 90 * u, layout.close.y, 90 * u, 22 * u};
    return layout;
}

int bagCount(const Party &party)
{
    return std::max(1, party.rules().items.bagCount(party));
}

// One row of the picker: a kind of potion or scroll at one strength, how many the party carries and who.
struct PickerRow
{
    uint32_t itemId = 0;
    uint16_t power = 0;
    size_t count = 0;
    bool scroll = false;
    std::string name;
    std::string icon;
    std::vector<std::string> carriers;
};

// Every potion and scroll a slot may hold, from every member's bags: potions first, then scrolls, by name and
// strength.
std::vector<PickerRow> pickerRows(GameplayScreenRuntime &context, const Party &party)
{
    std::vector<PickerRow> rows;
    const ItemTable *pItemTable = context.itemTable();

    if (pItemTable == nullptr)
    {
        return rows;
    }

    for (const QuickItemSlots::PartyItemKind &kind : QuickItemSlots::partyItemKinds(party, *pItemTable,
             context.mergedPotionSettingTable(), context.mergedReagentSettingTable(), bagCount(party)))
    {
        const ItemDefinition *pDefinition = pItemTable->get(kind.itemId);

        if (pDefinition == nullptr)
        {
            continue;
        }

        PickerRow row;
        row.itemId = kind.itemId;
        row.power = kind.power;
        row.count = kind.count;
        row.scroll = kind.scroll;
        row.name = pDefinition->name;
        row.icon = pDefinition->iconName;

        for (size_t carrier : kind.carriers)
        {
            if (const Character *pCarrier = party.member(carrier))
            {
                row.carriers.push_back(pCarrier->name);
            }
        }

        rows.push_back(std::move(row));
    }

    std::sort(rows.begin(), rows.end(), [](const PickerRow &left, const PickerRow &right)
        {
            return std::tie(left.scroll, left.name, left.power) < std::tie(right.scroll, right.name, right.power);
        });
    return rows;
}

class Painter
{
public:
    explicit Painter(GameplayScreenRuntime &context)
        : m_context(context)
    {
    }

    void fill(const Box &box, uint32_t colour) const
    {
        if (const std::optional<GameplayHudTextureHandle> texture = solid(colour))
        {
            m_context.submitHudTexturedQuad(*texture, box.x, box.y, box.width, box.height);
        }
    }

    void frame(const Box &box, float line, uint32_t colour) const
    {
        fill({box.x, box.y, box.width, line}, colour);
        fill({box.x, box.y + box.height - line, box.width, line}, colour);
        fill({box.x, box.y, line, box.height}, colour);
        fill({box.x + box.width - line, box.y, line, box.height}, colour);
    }

    void disc(const Circle &circle, uint32_t colour) const
    {
        if (const std::optional<GameplayHudTextureHandle> texture = solid(colour))
        {
            m_context.gameplayUiRuntime().submitHudTexturedEllipse(texture->textureHandle, circle.x - circle.radius,
                circle.y - circle.radius, 2 * circle.radius, 2 * circle.radius);
        }
    }

    void ring(const Circle &circle, float stroke, bool bright) const
    {
        const GameplayResolvedHudLayoutElement rect = {circle.x - circle.radius, circle.y - circle.radius,
            2 * circle.radius, 2 * circle.radius, circle.radius / 37.0f};
        GameplayUiSkin::renderArc(m_context, rect, stroke, 0, 360,
            bright ? GameplayUiSkin::ArcMaterial::SelectedRim : GameplayUiSkin::ArcMaterial::NormalRim);
    }

    // An item's icon fitted in a box, centred, greyed when asked.
    void icon(const std::string &iconName, const Box &box, bool grey) const
    {
        const std::optional<GameplayHudTextureHandle> texture =
            m_context.gameplayUiRuntime().ensureItemIconTextureLoaded(iconName);

        if (!texture || texture->width <= 0 || texture->height <= 0)
        {
            return;
        }

        const float scale = std::min(box.width / float(texture->width), box.height / float(texture->height));
        const float iconWidth = texture->width * scale;
        const float iconHeight = texture->height * scale;
        const bgfx::TextureHandle handle = grey
            ? m_context.gameplayUiRuntime().ensureHudTextureColorModulated(*texture, 0xff606060u)
            : texture->textureHandle;
        m_context.gameplayUiRuntime().submitHudTexturedQuad(handle, box.x + (box.width - iconWidth) / 2,
            box.y + (box.height - iconHeight) / 2, iconWidth, iconHeight);
    }

    // Text of a pixel height; align 0 left, 1 centred on x, 2 ending at x.
    void text(const std::string &font, float height, uint32_t colour, const std::string &value, float x, float y,
        int align = 0) const
    {
        const float scale = fontScale(font, height);
        const float textWidth = m_context.measureHudTextWidth(font, value) * scale;
        x -= align == 1 ? textWidth / 2 : align == 2 ? textWidth : 0;
        m_context.renderHudTextLine(font, colour, value, std::round(x), std::round(y), scale);
    }

    float width(const std::string &font, float height, const std::string &value) const
    {
        return m_context.measureHudTextWidth(font, value) * fontScale(font, height);
    }

    // The value shortened with an ellipsis to fit the width.
    std::string fitted(const std::string &font, float height, const std::string &value, float maxWidth) const
    {
        std::string result = value;

        while (result.size() > 1 && width(font, height, result) > maxWidth)
        {
            result.pop_back();

            if (width(font, height, result + "...") <= maxWidth)
            {
                return result + "...";
            }
        }

        return result;
    }

private:
    std::optional<GameplayHudTextureHandle> solid(uint32_t colour) const
    {
        char name[40] = {};
        std::snprintf(name, sizeof(name), "__quick_item_%08x", colour);
        return m_context.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colour);
    }

    float fontScale(const std::string &font, float height) const
    {
        const float wanted = height / float(std::max(1, m_context.hudFontHeight(font)));
        return wanted >= 1.0f ? GameplayHudCommon::snappedHudFontScale(wanted) : std::max(0.5f, wanted);
    }

    GameplayScreenRuntime &m_context;
};

// The member's state as the hub says it: ready, recovering (and who gives the next drink, where drinks cost
// recovery), or nobody ready.
std::string hubState(GameplayScreenRuntime &context, const Party &party, size_t member)
{
    const Character *pMember = party.member(member);

    if (pMember == nullptr)
    {
        return {};
    }

    if (GameMechanics::canTakeGameplayAction(*pMember))
    {
        return "ready";
    }

    if (!InventoryItemUseRuntime::drinkRecoveryApplies(context.mergedPotionSettingTable()))
    {
        return "recovering";
    }

    const std::optional<size_t> payer =
        InventoryItemUseRuntime::drinkRecoveryPayer(*context.mergedPotionSettingTable(), party, member);
    const Character *pPayer = payer ? party.member(*payer) : nullptr;
    return pPayer != nullptr ? "next fed by " + pPayer->name : "nobody ready";
}

void closeRing(GameplayScreenRuntime &context)
{
    GameplayOverlayInteractionState &state = context.interactionState();
    state.quickItemRingOpen = false;
    state.quickItemHoveredSlot.reset();
    state.quickItemPickerSlot.reset();
}

void openPicker(GameplayScreenRuntime &context, size_t slot)
{
    context.interactionState().quickItemPickerSlot = slot;
    context.interactionState().quickItemPickerScroll = 0;
}

void renderPicker(GameplayScreenRuntime &context, const Party &party, const Character &member, size_t slot,
    const PickerLayout &layout)
{
    const Painter paint(context);
    const float u = layout.unit;
    const QuickItemSlot &quickSlot = member.quickItemSlots[slot];
    paint.fill(layout.panel, PanelFill);
    paint.frame(layout.panel, std::max(1.0f, u), PanelBorder);
    paint.text("Fondamento", 18 * u, Label, "Slot " + std::to_string(slot + 1), layout.panel.x + 12 * u,
        layout.panel.y + 9 * u);
    const std::array<const char *, 2> rules = {"Weakest first", "Strongest first"};

    for (size_t index = 0; index < rules.size(); ++index)
    {
        const bool on = size_t(quickSlot.bottleRule) == index;
        paint.fill(layout.rules[index], on ? ChipOnFill : ChipFill);
        paint.frame(layout.rules[index], std::max(1.0f, u), on ? ChipOnBorder : ChipBorder);
        paint.text(TextFont, 11 * u, on ? Ivory : Body, rules[index],
            layout.rules[index].x + layout.rules[index].width / 2, layout.rules[index].y + 4 * u, 1);
    }

    const std::vector<PickerRow> rows = pickerRows(context, party);
    const size_t scroll = std::min(context.interactionState().quickItemPickerScroll,
        rows.size() > layout.visibleRows ? rows.size() - layout.visibleRows : size_t(0));

    for (size_t index = 0; index < layout.visibleRows && scroll + index < rows.size(); ++index)
    {
        const PickerRow &row = rows[scroll + index];
        const Box box = {layout.list.x, layout.list.y + index * layout.rowHeight, layout.list.width, layout.rowHeight};

        if (row.itemId == quickSlot.itemId)
        {
            paint.fill(box, RowHighlight);
        }

        paint.fill({box.x, box.y + box.height - std::max(1.0f, u), box.width, std::max(1.0f, u)}, RowRule);
        paint.icon(row.icon, {box.x + 2 * u, box.y + 3 * u, 30 * u, box.height - 6 * u}, false);
        const std::string countText = "x" + std::to_string(row.count);
        const float countWidth = paint.width(TextFont, 13 * u, countText);
        paint.text(TextFont, 13 * u, Ivory,
            paint.fitted(TextFont, 13 * u, row.name, box.width - 46 * u - countWidth - 8 * u), box.x + 38 * u,
            box.y + 4 * u);
        paint.text(TextFont, 13 * u, Ivory, countText, box.x + box.width - 6 * u, box.y + 4 * u, 2);
        std::string carriers;

        for (const std::string &name : row.carriers)
        {
            carriers += (carriers.empty() ? "" : ", ") + name;
        }

        // The HUD fonts are single-byte: the middle dot is 0xB7.
        const std::string note = (row.power > 0 ? "strength " + std::to_string(row.power) + "  \xB7  " : std::string())
            + carriers;
        paint.text(TextFont, 10 * u, Muted, paint.fitted(TextFont, 10 * u, note, box.width - 44 * u), box.x + 38 * u,
            box.y + 21 * u);
    }

    if (rows.empty())
    {
        paint.text(TextFont, 12 * u, Muted, "Nobody carries a potion or a scroll", layout.list.x + 6 * u,
            layout.list.y + 8 * u);
    }

    if (rows.size() > layout.visibleRows)
    {
        paint.fill(layout.track, Track);
        const float thumb = layout.track.height * float(layout.visibleRows) / float(rows.size());
        const float offset = (layout.track.height - thumb) * float(scroll) / float(rows.size() - layout.visibleRows);
        paint.fill({layout.track.x, layout.track.y + offset, layout.track.width, thumb}, Thumb);
    }

    const auto button = [&](const Box &box, const char *pLabel)
    {
        paint.fill(box, ChipFill);
        paint.frame(box, std::max(1.0f, u), ChipOnBorder);
        paint.text("Fondamento", 14 * u, abgr(0xe8d1a4), pLabel, box.x + box.width / 2, box.y + 3 * u, 1);
    };
    button(layout.clear, "Clear slot");
    button(layout.close, "Close");
}

// The picker's clicks and wheel: true when the pointer was over it.
bool handlePickerInput(GameplayScreenRuntime &context, const GameplayInputFrame &input, const Party &party,
    Character &member, size_t slot, const PickerLayout &layout, bool left)
{
    GameplayOverlayInteractionState &state = context.interactionState();
    const float x = input.pointerX;
    const float y = input.pointerY;

    if (!layout.panel.contains(x, y))
    {
        return false;
    }

    const std::vector<PickerRow> rows = pickerRows(context, party);
    const size_t maxScroll = rows.size() > layout.visibleRows ? rows.size() - layout.visibleRows : 0;
    state.quickItemPickerScroll = std::min(state.quickItemPickerScroll, maxScroll);

    if (input.mouseWheelDelta > 0)
    {
        state.quickItemPickerScroll = state.quickItemPickerScroll > 0 ? state.quickItemPickerScroll - 1 : 0;
    }
    else if (input.mouseWheelDelta < 0)
    {
        state.quickItemPickerScroll = std::min(state.quickItemPickerScroll + 1, maxScroll);
    }

    if (!left)
    {
        return true;
    }

    QuickItemSlot &quickSlot = member.quickItemSlots[slot];

    for (size_t index = 0; index < layout.rules.size(); ++index)
    {
        if (layout.rules[index].contains(x, y))
        {
            quickSlot.bottleRule = QuickItemBottleRule(index);
        }
    }

    if (layout.clear.contains(x, y))
    {
        quickSlot.itemId = 0;
        state.quickItemPickerSlot.reset();
    }
    else if (layout.close.contains(x, y))
    {
        state.quickItemPickerSlot.reset();
    }
    else if (layout.track.contains(x, y) && maxScroll > 0)
    {
        // A click on the track scrolls to that point of the list.
        const float position = (y - layout.track.y) / std::max(1.0f, layout.track.height);
        state.quickItemPickerScroll = std::min(size_t(std::lround(position * float(maxScroll))), maxScroll);
    }
    else if (layout.list.contains(x, y))
    {
        const size_t index = state.quickItemPickerScroll + size_t((y - layout.list.y) / layout.rowHeight);

        if (index < rows.size())
        {
            quickSlot.itemId = rows[index].itemId;
            state.quickItemPickerSlot.reset();
        }
    }

    return true;
}

// The basebar's potion and scroll buttons and their popups (level_generation/ui/potion_scroll_popups_20261102, A):
// a medallion on each end ornament of the party frame, scrolls on the left and potions on the right (user,
// 2026-11-02). Each opens a list of what the party carries over the paused game; a click drinks the potion or reads
// the scroll as the chosen member, exactly as one dropped on their portrait from the inventory. Sizes are the study's
// 1600x900 pixels times `k`, the frame's height over its 195 pixels there.
constexpr float StudyBasebarHeight = 195.0f;
constexpr char PotionButtonIcon[] = "item178";
constexpr char ScrollButtonIcon[] = "item202";
constexpr uint32_t Brass = abgr(0xa8915c);
constexpr uint32_t BrassDark = abgr(0x6f5f3a);
constexpr uint32_t RowFill = abgr(0x111c1b, 0xd8);
constexpr uint32_t RowBorder = abgr(0x263027);
constexpr uint32_t Good = abgr(0x8fe08a);
constexpr uint32_t HealthFill = abgr(0x7fd27a);
constexpr uint32_t HealthGhost = abgr(0xb7f2a8, 0x90);
constexpr uint32_t ManaFill = abgr(0x79b5f0);
constexpr uint32_t ManaGhost = abgr(0xb4d8ff, 0x90);
constexpr uint32_t BarTrack = abgr(0x142020);
constexpr uint32_t BarBorder = abgr(0x3b4639);
// The popup: its width and the top of its room (below the top HUD) in the study's pixels, and its contents' scale.
constexpr float PopupWidth = 1000.0f;
constexpr float PopupTop = 140.0f;
constexpr float PopupScale = 1.3f;
constexpr char NameFont[] = "Arrus";

std::optional<GameplayResolvedHudLayoutElement> basebarRect(GameplayScreenRuntime &context, int width, int height)
{
    return context.resolveHudLayoutElement("OutdoorGameplayBasebar", width, height, 0, 0);
}

// Where a popup's button sits: in the socket of the frame's end ornament (scrolls left, potions right).
std::optional<Circle> itemButtonAnchor(GameplayScreenRuntime &context, int width, int height, QuickItemPopupKind kind)
{
    const std::optional<GameplayResolvedHudLayoutElement> bar = basebarRect(context, width, height);

    if (!bar)
    {
        return std::nullopt;
    }

    const GameplayUiSkin::PartyBasebarSocket socket =
        GameplayUiSkin::partyBasebarSocket(*bar, kind == QuickItemPopupKind::Potions);

    // With the frame hidden there is no ornament to hold them: closer to the portraits and a little lower (user,
    // 2026-11-02), just outside where the frame's border would be.
    if (!context.settingsSnapshot().partyFrame)
    {
        const float inset = socket.radius * 0.45f;
        const float x = kind == QuickItemPopupKind::Potions ? bar->x + bar->width + inset : bar->x - inset;
        return Circle{x, bar->y + bar->height * 0.64f, socket.radius};
    }

    return Circle{socket.x, socket.y, socket.radius};
}

// Whether the frame is drawn with its sockets, so a button is only its icon in the carved socket.
bool itemButtonsInSockets(GameplayScreenRuntime &context)
{
    return context.settingsSnapshot().partyFrame && GameplayUiSkin::partyBasebarHasSockets(context);
}

// The button itself: none while the Potion and scroll buttons setting hides them.
std::optional<Circle> itemButtonCircle(GameplayScreenRuntime &context, int width, int height, QuickItemPopupKind kind)
{
    if (!context.settingsSnapshot().basebarItemButtons)
    {
        return std::nullopt;
    }

    return itemButtonAnchor(context, width, height, kind);
}

// One entry of a popup: a kind of potion or scroll at one strength.
struct PopupEntry
{
    uint32_t itemId = 0;
    uint16_t power = 0;
    size_t count = 0;
    std::string name;
    std::string icon;
    std::vector<size_t> carriers;
};

std::vector<PopupEntry> popupEntries(GameplayScreenRuntime &context, const Party &party, QuickItemPopupKind kind)
{
    std::vector<PopupEntry> entries;
    const ItemTable *pItemTable = context.itemTable();

    if (pItemTable == nullptr || kind == QuickItemPopupKind::None)
    {
        return entries;
    }

    for (const QuickItemSlots::PartyItemKind &item : QuickItemSlots::partyItemKinds(party, *pItemTable,
             context.mergedPotionSettingTable(), context.mergedReagentSettingTable(), bagCount(party)))
    {
        const ItemDefinition *pDefinition = pItemTable->get(item.itemId);

        if (pDefinition == nullptr || item.scroll != (kind == QuickItemPopupKind::Scrolls))
        {
            continue;
        }

        entries.push_back({item.itemId, item.power, item.count, pDefinition->name, pDefinition->iconName,
            item.carriers});
    }

    std::sort(entries.begin(), entries.end(), [](const PopupEntry &left, const PopupEntry &right)
        {
            return std::tie(left.name, left.power) < std::tie(right.name, right.power);
        });
    return entries;
}

size_t popupItemCount(GameplayScreenRuntime &context, const Party &party, QuickItemPopupKind kind)
{
    size_t count = 0;

    for (const PopupEntry &entry : popupEntries(context, party, kind))
    {
        count += entry.count;
    }

    return count;
}

// The popup, centred over the scene above the frame (user, 2026-11-02: symmetric, roomy and readable, no dimming): the
// header (title, the member, their HP and SP, Close), a hint line, the entries in two columns with a scrollbar, and
// for potions the footer describing the hovered one. Its contents are drawn in `k`, the study's pixels at
// PopupScale.
struct PopupLayout
{
    Box panel;
    Box close;
    Box memberChip;
    Box bars;
    Box list;
    Box track;
    Box footer;
    float rowHeight = 0;
    float rowGap = 0;
    float columnWidth = 0;
    float columnGap = 0;
    size_t visibleRows = 0;
    float k = 1;
};

// `entries` sizes the list: the panel ends below its last row, up to the room between the top HUD and the frame, and
// sits in the middle of that room.
std::optional<PopupLayout> popupLayout(GameplayScreenRuntime &context, int width, int height, QuickItemPopupKind kind,
    size_t entries)
{
    const std::optional<GameplayResolvedHudLayoutElement> bar = basebarRect(context, width, height);

    if (!bar)
    {
        return std::nullopt;
    }

    PopupLayout layout;
    const float base = bar->height / StudyBasebarHeight;
    const float k = base * PopupScale;
    layout.k = k;
    const float top = PopupTop * base;
    const float bottom = bar->y - 10 * base;
    const float panelWidth = std::min(PopupWidth * base, float(width) - 8 * base);
    const float footerHeight = kind == QuickItemPopupKind::Potions ? 84 * k : 0;
    const float chrome = 92 * k + footerHeight + (footerHeight > 0 ? 6 * k : 12 * k);
    // Whole rows only: as many as the entries need (at least two) and the room allows.
    const float rowPitch = 52 * k;
    const size_t fitting = size_t(std::max(1.0f, std::floor((bottom - top - chrome + 4 * k) / rowPitch + 0.01f)));
    const size_t rows = std::min(std::clamp<size_t>((entries + 1) / 2, 2, 8), fitting);
    const float panelHeight = chrome + float(rows) * rowPitch - 4 * k;
    layout.panel = {(float(width) - panelWidth) / 2, top + std::max(0.0f, (bottom - top - panelHeight) / 2),
        panelWidth, panelHeight};
    const Box &panel = layout.panel;
    layout.close = {panel.x + panel.width - 16 * k - 96 * k, panel.y + 14 * k, 96 * k, 36 * k};
    layout.memberChip = {panel.x + 150 * k, panel.y + 9 * k, 200 * k, 46 * k};
    layout.bars = {layout.memberChip.x + layout.memberChip.width + 16 * k, panel.y + 18 * k, 112 * k, 29 * k};
    layout.footer = {panel.x, panel.y + panel.height - footerHeight, panel.width, footerHeight};
    layout.list = {panel.x + 12 * k, panel.y + 92 * k, panel.width - 38 * k,
        panel.height - 92 * k - footerHeight - (footerHeight > 0 ? 6 * k : 12 * k)};
    layout.rowHeight = 48 * k;
    layout.rowGap = 4 * k;
    layout.columnGap = 8 * k;
    layout.columnWidth = (layout.list.width - layout.columnGap) / 2;
    layout.visibleRows = rows;
    layout.track = {panel.x + panel.width - 18 * k, layout.list.y, 6 * k,
        layout.visibleRows * (layout.rowHeight + layout.rowGap) - layout.rowGap};
    return layout;
}

size_t popupRowCount(size_t entries)
{
    return (entries + 1) / 2;
}

size_t popupMaxScroll(const PopupLayout &layout, size_t entries)
{
    const size_t rows = popupRowCount(entries);
    return rows > layout.visibleRows ? rows - layout.visibleRows : 0;
}

// The entry's box when it is in view.
std::optional<Box> popupEntryBox(const PopupLayout &layout, size_t index, size_t scroll)
{
    const size_t row = index / 2;

    if (row < scroll || row >= scroll + layout.visibleRows)
    {
        return std::nullopt;
    }

    return Box{layout.list.x + float(index % 2) * (layout.columnWidth + layout.columnGap),
        layout.list.y + float(row - scroll) * (layout.rowHeight + layout.rowGap), layout.columnWidth,
        layout.rowHeight};
}

// The six quick-slot chips a right click opens over an entry: a click puts the entry's kind in that slot of the
// member's (or takes it out again).
Box keyChip(const Box &entry, size_t slot, float k)
{
    const float chip = 26 * k;
    const float gap = 4 * k;
    const float right = entry.x + entry.width - 8 * k;
    return {right - float(QuickItemSlotCount - slot) * (chip + gap) + gap, entry.y + (entry.height - chip) / 2, chip,
        chip};
}

std::string carrierNames(const Party &party, const std::vector<size_t> &carriers)
{
    std::string names;

    for (size_t carrier : carriers)
    {
        if (const Character *pCarrier = party.member(carrier))
        {
            names += (names.empty() ? "" : ", ") + pCarrier->name;
        }
    }

    return names;
}

// The school a scroll's spell belongs to, as its skill names it ("FireMagic"), and that school's colour.
std::optional<std::pair<std::string, uint32_t>> scrollSchool(const ItemTable &itemTable, uint32_t itemId)
{
    static const std::array<std::pair<const char *, uint32_t>, 9> Schools = {{
        {"FireMagic", abgr(0xff8a4a)}, {"AirMagic", abgr(0xbfe3ff)}, {"WaterMagic", abgr(0x5aa8ff)},
        {"EarthMagic", abgr(0xb9935a)}, {"SpiritMagic", abgr(0xf0e6b0)}, {"MindMagic", abgr(0xc49aff)},
        {"BodyMagic", abgr(0x7fe0a0)}, {"LightMagic", abgr(0xfff3c0)}, {"DarkMagic", abgr(0x9a7fb0)},
    }};
    const ItemDefinition *pDefinition = itemTable.get(itemId);
    const std::optional<uint32_t> spellId =
        pDefinition != nullptr ? InventoryItemUseRuntime::scrollSpellId(*pDefinition) : std::nullopt;
    const std::optional<std::string> skill = spellId ? resolveMagicSkillName(*spellId) : std::nullopt;

    if (!skill)
    {
        return std::nullopt;
    }

    for (const auto &[name, colour] : Schools)
    {
        if (*skill == name)
        {
            return std::pair<std::string, uint32_t>{displaySkillName(*skill), colour};
        }
    }

    return std::pair<std::string, uint32_t>{displaySkillName(*skill), Muted};
}

void closePopup(GameplayScreenRuntime &context)
{
    GameplayOverlayInteractionState &state = context.interactionState();
    state.quickItemPopup = QuickItemPopupKind::None;
    state.quickItemPopupHovered.reset();
    state.quickItemPopupKeyEntry.reset();
}

void togglePopup(GameplayScreenRuntime &context, const Party &party, QuickItemPopupKind kind)
{
    GameplayOverlayInteractionState &state = context.interactionState();

    if (state.quickItemPopup == kind)
    {
        closePopup(context);
        return;
    }

    closeRing(context);
    closePopup(context);
    state.quickItemPopup = kind;
    state.quickItemPopupMember = party.activeMemberIndex();
    state.quickItemPopupScroll = 0;
}

void renderItemButtons(GameplayScreenRuntime &context, const Party &party, int width, int height)
{
    const Painter paint(context);
    const QuickItemPopupKind open = context.interactionState().quickItemPopup;

    for (const QuickItemPopupKind kind : {QuickItemPopupKind::Scrolls, QuickItemPopupKind::Potions})
    {
        const std::optional<Circle> button = itemButtonCircle(context, width, height, kind);

        if (!button)
        {
            continue;
        }

        // Only the icon (user, 2026-11-02), greyed when the party carries none. In the ornament's socket the carving is
        // the button; with the frame hidden a round obsidian plate of its own stands in its place.
        const size_t count = popupItemCount(context, party, kind);

        if (itemButtonsInSockets(context))
        {
            if (open == kind)
            {
                paint.ring({button->x, button->y, button->radius * 0.97f}, 4.0f, true);
            }
        }
        else
        {
            paint.disc(*button, abgr(0x0b1414));
            paint.disc({button->x, button->y, button->radius * 0.86f}, abgr(0x14201f));
            paint.ring(*button, 6.0f, open == kind);
        }

        const bool potions = kind == QuickItemPopupKind::Potions;
        const float iconSize = button->radius * 1.7f;
        paint.icon(potions ? PotionButtonIcon : ScrollButtonIcon, {button->x - iconSize / 2, button->y - iconSize / 2,
            iconSize, iconSize}, count == 0);
    }
}

// A meter of the header: the value, a striped gain the hovered potion would add, and the numbers beside it.
void renderPopupBar(const Painter &paint, const Box &box, int value, int maximum, int gain, uint32_t fill,
    uint32_t ghost, float k)
{
    paint.fill(box, BarTrack);
    paint.frame(box, std::max(1.0f, k), BarBorder);

    if (maximum <= 0)
    {
        paint.text(TextFont, 11 * k, Muted, "no SP", box.x + box.width + 8 * k, box.y - 2 * k);
        return;
    }

    const float inner = box.width - 2 * k;
    const float filled = inner * std::clamp(float(value) / float(maximum), 0.0f, 1.0f);
    paint.fill({box.x + k, box.y + k, filled, box.height - 2 * k}, fill);

    if (gain > 0)
    {
        const float extra = std::min(inner - filled, inner * float(gain) / float(maximum));
        paint.fill({box.x + k + filled, box.y + k, extra, box.height - 2 * k}, ghost);
    }

    paint.text(TextFont, 11 * k, Ivory, std::to_string(value) + " / " + std::to_string(maximum),
        box.x + box.width + 8 * k, box.y - 2 * k);
}

void renderPopup(GameplayScreenRuntime &context, const Party &party, int width, int height)
{
    const GameplayOverlayInteractionState &state = context.interactionState();
    const QuickItemPopupKind kind = state.quickItemPopup;
    const std::vector<PopupEntry> entries = popupEntries(context, party, kind);
    const std::optional<PopupLayout> layout = popupLayout(context, width, height, kind, entries.size());
    const std::optional<GameplayResolvedHudLayoutElement> bar = basebarRect(context, width, height);
    const Character *pMember = party.member(state.quickItemPopupMember);
    const ItemTable *pItemTable = context.itemTable();

    if (!layout || !bar || pMember == nullptr || pItemTable == nullptr)
    {
        return;
    }

    const Painter paint(context);
    const float k = layout->k;
    const bool potions = kind == QuickItemPopupKind::Potions;

    // The member's portrait gets the selected rim, thicker, when it is not the active member's.
    if (state.quickItemPopupMember != party.activeMemberIndex())
    {
        const std::string rimId = "ObsidianPc" + std::to_string(state.quickItemPopupMember + 1) + "Rim";
        const UiLayoutManager::LayoutElement *pRim = context.findHudLayoutElement(rimId);
        const std::optional<GameplayResolvedHudLayoutElement> rim =
            context.resolveHudLayoutElement(rimId, width, height, 0, 0);

        if (pRim != nullptr && pRim->meterArc && rim)
        {
            GameplayUiSkin::renderArc(context, *rim, 3.0f, pRim->meterArc->startDegrees,
                pRim->meterArc->sweepDegrees, GameplayUiSkin::ArcMaterial::SelectedRim);
        }
    }

    const Box &panel = layout->panel;
    const Box outer = {panel.x - 4 * k, panel.y - 4 * k, panel.width + 8 * k, panel.height + 8 * k};
    paint.fill(outer, abgr(0x1a1f1a, 0xf0));
    paint.frame(outer, std::max(1.0f, k), BrassDark);
    paint.fill(panel, PanelFill);
    paint.frame(panel, std::max(1.0f, k), Brass);

    // Header: title, the member, their HP and SP, Close.
    paint.text("Fondamento", 30 * k, Ivory, potions ? "Potions" : "Scrolls", panel.x + 16 * k, panel.y + 15 * k);
    const Box &chip = layout->memberChip;
    paint.fill(chip, abgr(0x0d1716));
    paint.frame(chip, std::max(1.0f, k), ChipBorder);

    if (const std::optional<GameplayHudTextureHandle> portrait =
            context.gameplayUiRuntime().ensureHudTextureLoaded(context.resolvePortraitTextureName(*pMember)))
    {
        context.gameplayUiRuntime().submitHudTexturedEllipse(portrait->textureHandle, chip.x + 4 * k, chip.y + 3 * k,
            34 * k, 40 * k);
    }

    paint.text("Fondamento", 19 * k, Label, paint.fitted("Fondamento", 19 * k, pMember->name, chip.width - 52 * k),
        chip.x + 46 * k, chip.y + 4 * k);
    paint.text(TextFont, 11 * k, Muted,
        std::string(potions ? "drinks" : "reads") + "  \xB7  " + hubState(context, party, state.quickItemPopupMember),
        chip.x + 46 * k, chip.y + 27 * k);

    const std::optional<size_t> hovered =
        state.quickItemPopupHovered && *state.quickItemPopupHovered < entries.size() ? state.quickItemPopupHovered
                                                                                     : std::nullopt;
    PotionPreview preview;

    if (potions && hovered && context.mergedPotionSettingTable() != nullptr)
    {
        InventoryItem item;
        item.objectDescriptionId = entries[*hovered].itemId;
        item.standardEnchantPower = entries[*hovered].power;
        preview = InventoryItemUseRuntime::previewPotion(party, state.quickItemPopupMember, item,
            *context.mergedPotionSettingTable());
    }

    const Box &bars = layout->bars;
    renderPopupBar(paint, {bars.x, bars.y, bars.width, 12 * k}, pMember->health,
        Party::effectiveMaximumHealth(*pMember), preview.healthGain, HealthFill, HealthGhost, k);
    renderPopupBar(paint, {bars.x, bars.y + 17 * k, bars.width, 12 * k}, pMember->spellPoints,
        Party::effectiveMaximumSpellPoints(*pMember), preview.spellPointGain, ManaFill, ManaGhost, k);

    const Box &close = layout->close;
    paint.fill(close, ChipFill);
    paint.frame(close, std::max(1.0f, k), ChipOnBorder);
    paint.text("Fondamento", 19 * k, abgr(0xe8d1a4), "Close", close.x + close.width / 2, close.y + 7 * k, 1);
    paint.fill({panel.x, panel.y + 64 * k, panel.width, std::max(1.0f, k)}, abgr(0x3a4234));

    // The hint line.
    paint.text(TextFont, 12 * k, Muted, potions ? "Click a portrait below to choose who drinks"
                                                : "Click a portrait below to choose who reads",
        panel.x + 16 * k, panel.y + 68 * k);
    paint.text(TextFont, 12 * k, Muted, "Right-click: put on a quick slot", panel.x + panel.width - 16 * k,
        panel.y + 68 * k, 2);

    // The entries, two to a row.
    const size_t scroll = std::min(state.quickItemPopupScroll, popupMaxScroll(*layout, entries.size()));
    const MergedPotionSettingTable *pPotionTable = context.mergedPotionSettingTable();

    for (size_t index = 0; index < entries.size(); ++index)
    {
        const std::optional<Box> box = popupEntryBox(*layout, index, scroll);

        if (!box)
        {
            continue;
        }

        const PopupEntry &entry = entries[index];
        bool idle = false;

        if (potions && pPotionTable != nullptr)
        {
            InventoryItem item;
            item.objectDescriptionId = entry.itemId;
            item.standardEnchantPower = entry.power;
            idle = InventoryItemUseRuntime::previewPotion(party, state.quickItemPopupMember, item, *pPotionTable)
                       .noEffectNow();
        }

        const bool hot = hovered == index || state.quickItemPopupKeyEntry == index;
        paint.fill(*box, hot ? ChipOnFill : RowFill);
        paint.frame(*box, std::max(1.0f, k), hot ? ChipOnBorder : RowBorder);
        paint.icon(entry.icon, {box->x + 4 * k, box->y + 2 * k, 44 * k, 44 * k}, idle);
        const float textX = box->x + 56 * k;
        const std::string countText = "x" + std::to_string(entry.count);
        const float countWidth = paint.width(TextFont, 14 * k, countText);
        paint.text(NameFont, 16 * k, idle ? Muted : Ivory,
            paint.fitted(NameFont, 16 * k, entry.name, box->width - 66 * k - countWidth), textX, box->y + 6 * k);
        paint.text(TextFont, 14 * k, Ivory, countText, box->x + box->width - 10 * k, box->y + 15 * k, 2);
        const std::string carriers = carrierNames(party, entry.carriers);
        float subX = textX;

        if (potions)
        {
            const std::string sub = "strength " + std::to_string(entry.power) + "  \xB7  " + carriers;
            const std::string fitted = paint.fitted(TextFont, 11 * k, sub, box->width - 70 * k - countWidth
                - (idle ? paint.width(TextFont, 11 * k, "  \xB7  no effect now") : 0));
            paint.text(TextFont, 11 * k, Muted, fitted, subX, box->y + 28 * k);

            if (idle)
            {
                subX += paint.width(TextFont, 11 * k, fitted);
                paint.text(TextFont, 11 * k, Warn, "  \xB7  no effect now", subX, box->y + 28 * k);
            }
        }
        else
        {
            const std::optional<std::pair<std::string, uint32_t>> school = scrollSchool(*pItemTable, entry.itemId);

            if (school)
            {
                paint.disc({subX + 3.5f * k, box->y + 34 * k, 3.5f * k}, school->second);
                subX += 11 * k;
            }

            paint.text(TextFont, 11 * k, Muted,
                paint.fitted(TextFont, 11 * k, (school ? school->first + "  \xB7  " : std::string()) + carriers,
                    box->width - 80 * k - countWidth),
                subX, box->y + 28 * k);
        }

        // The member's quick slots holding this kind.
        float pinX = box->x + 2 * k;

        for (size_t slot = 0; slot < QuickItemSlotCount; ++slot)
        {
            if (pMember->quickItemSlots[slot].itemId == entry.itemId)
            {
                const Box pin = {pinX, box->y + 2 * k, 15 * k, 15 * k};
                paint.fill(pin, abgr(0x1c2524));
                paint.frame(pin, std::max(1.0f, k), abgr(0x6b6a4e));
                paint.text(TextFont, 10 * k, Gold, std::to_string(slot + 1), pin.x + pin.width / 2, pin.y + 1 * k, 1);
                pinX += 17 * k;
            }
        }

        // The quick-slot chooser over the entry.
        if (state.quickItemPopupKeyEntry == index)
        {
            const Box first = keyChip(*box, 0, k);
            const Box strip = {first.x - 82 * k, box->y + 3 * k, box->x + box->width - 4 * k - (first.x - 82 * k),
                box->height - 6 * k};
            paint.fill(strip, abgr(0x0b1212, 0xf4));
            paint.frame(strip, std::max(1.0f, k), ChipOnBorder);
            paint.text(TextFont, 11 * k, Body, "Quick slot", strip.x + 8 * k, strip.y + strip.height / 2 - 7 * k);

            for (size_t slot = 0; slot < QuickItemSlotCount; ++slot)
            {
                const Box chipBox = keyChip(*box, slot, k);
                const bool on = pMember->quickItemSlots[slot].itemId == entry.itemId;
                paint.fill(chipBox, on ? ChipOnFill : ChipFill);
                paint.frame(chipBox, std::max(1.0f, k), on ? ChipOnBorder : ChipBorder);
                paint.text(TextFont, 13 * k, on ? Ivory : Body, std::to_string(slot + 1),
                    chipBox.x + chipBox.width / 2, chipBox.y + 5 * k, 1);
            }
        }
    }

    if (entries.empty())
    {
        paint.text(TextFont, 14 * k, Muted, potions ? "The party carries no potion" : "The party carries no scroll",
            layout->list.x + 8 * k, layout->list.y + 10 * k);
    }

    const size_t maxScroll = popupMaxScroll(*layout, entries.size());

    if (maxScroll > 0)
    {
        const Box &track = layout->track;
        paint.fill(track, Track);
        const float thumb = track.height * float(layout->visibleRows) / float(popupRowCount(entries.size()));
        const float offset = (track.height - thumb) * float(scroll) / float(maxScroll);
        paint.fill({track.x - k, track.y + offset, track.width + 2 * k, thumb}, abgr(0x6a8dac));
    }

    // Potions: the hovered one's effect on the member.
    if (!potions || layout->footer.height <= 0)
    {
        return;
    }

    const Box &footer = layout->footer;
    paint.fill({footer.x, footer.y, footer.width, std::max(1.0f, k)}, abgr(0x3a4234));

    if (!hovered)
    {
        paint.text(TextFont, 13 * k, Muted, "Point at a potion to see what it does for " + pMember->name,
            footer.x + 16 * k, footer.y + 32 * k);
        return;
    }

    const PopupEntry &entry = entries[*hovered];
    const int bags = bagCount(party);
    const std::optional<QuickItemSlots::PartyLocation> source = QuickItemSlots::findPartyItemOfPower(
        party, state.quickItemPopupMember, entry.itemId, entry.power, bags);
    const Character *pSource = source ? party.member(source->memberIndex) : nullptr;
    paint.text("Fondamento", 19 * k, Label, entry.name, footer.x + 16 * k, footer.y + 12 * k);
    paint.text(TextFont, 13 * k, Muted, "strength " + std::to_string(entry.power)
            + (pSource != nullptr ? "  \xB7  from " + pSource->name + "'s pack" : std::string()),
        footer.x + 24 * k + paint.width("Fondamento", 19 * k, entry.name), footer.y + 17 * k);
    float x = footer.x + 16 * k;
    const float y = footer.y + 46 * k;
    const auto say = [&](const std::string &text, uint32_t colour)
    {
        paint.text(TextFont, 13 * k, colour, text, x, y);
        x += paint.width(TextFont, 13 * k, text);
    };

    if (preview.noEffectNow())
    {
        say("No effect on " + pMember->name + " now", Warn);
        return;
    }

    if (preview.healthGain > 0)
    {
        say(pMember->name + " ", Body);
        say("+" + std::to_string(preview.healthGain) + " HP", Good);
        say(" (" + std::to_string(preview.healthBefore) + " to "
                + std::to_string(preview.healthBefore + preview.healthGain) + " of "
                + std::to_string(preview.healthMaximum) + ")   ",
            Muted);
    }

    if (preview.spellPointGain > 0)
    {
        say(preview.healthGain > 0 ? "" : pMember->name + " ", Body);
        say("+" + std::to_string(preview.spellPointGain) + " SP", Good);
        say(" (" + std::to_string(preview.spellPointsBefore) + " to "
                + std::to_string(preview.spellPointsBefore + preview.spellPointGain) + " of "
                + std::to_string(preview.spellPointsMaximum) + ")   ",
            Muted);
    }

    for (CharacterCondition condition : preview.cures)
    {
        say("Cures " + GameMechanics::conditionName(condition) + "   ", Good);
    }

    if (preview.healthGain == 0 && preview.spellPointGain == 0 && preview.cures.empty())
    {
        const ItemDefinition *pDefinition = pItemTable->get(entry.itemId);
        // The item's description, without its inventory hint ("(To drink, pick the potion up ...)").
        std::string notes = pDefinition != nullptr ? pDefinition->notes : std::string();
        notes = notes.substr(0, notes.find("  (To "));
        notes = notes.substr(0, notes.find(" (To "));
        say(!notes.empty() ? paint.fitted(TextFont, 13 * k, notes, footer.width - 48 * k) : pMember->name + " drinks it",
            Body);
    }
}

// The popup's clicks, wheel and keys while it is open; it takes every click (the game is paused under it).
bool handlePopupInput(GameplayScreenRuntime &context, const GameplayInputFrame &input, Party &party, int width,
    int height, bool pointerAllowed, bool escapePressed)
{
    GameplayOverlayInteractionState &state = context.interactionState();
    const QuickItemPopupKind kind = state.quickItemPopup;
    const std::vector<PopupEntry> entries = popupEntries(context, party, kind);
    const std::optional<PopupLayout> layout = popupLayout(context, width, height, kind, entries.size());

    if (!layout || party.member(state.quickItemPopupMember) == nullptr)
    {
        closePopup(context);
        return false;
    }

    const size_t maxScroll = popupMaxScroll(*layout, entries.size());
    state.quickItemPopupScroll = std::min(state.quickItemPopupScroll, maxScroll);
    const float x = input.pointerX;
    const float y = input.pointerY;
    std::optional<size_t> under;

    for (size_t index = 0; pointerAllowed && index < entries.size(); ++index)
    {
        const std::optional<Box> box = popupEntryBox(*layout, index, state.quickItemPopupScroll);

        if (box && box->contains(x, y))
        {
            under = index;
        }
    }

    state.quickItemPopupHovered = under;

    if (escapePressed)
    {
        if (state.quickItemPopupKeyEntry)
        {
            state.quickItemPopupKeyEntry.reset();
        }
        else
        {
            closePopup(context);
        }

        state.menuToggleLatch = true;
        return true;
    }

    if (pointerAllowed && layout->panel.contains(x, y) && input.mouseWheelDelta != 0)
    {
        state.quickItemPopupKeyEntry.reset();
        state.quickItemPopupScroll = input.mouseWheelDelta > 0
            ? (state.quickItemPopupScroll > 0 ? state.quickItemPopupScroll - 1 : 0)
            : std::min(state.quickItemPopupScroll + 1, maxScroll);
    }

    const bool left = pointerAllowed && input.leftMouseButton.pressed;
    const bool right = pointerAllowed && input.rightMouseButton.pressed;

    if (!left && !right)
    {
        return state.quickItemClickLatch && (input.leftMouseButton.held || input.rightMouseButton.held);
    }

    state.quickItemClickLatch = true;
    Character &member = *party.member(state.quickItemPopupMember);

    // The quick-slot chooser takes the click first; anywhere else just closes it.
    if (state.quickItemPopupKeyEntry)
    {
        const size_t entryIndex = *state.quickItemPopupKeyEntry;
        const std::optional<Box> box = entryIndex < entries.size()
            ? popupEntryBox(*layout, entryIndex, state.quickItemPopupScroll)
            : std::nullopt;
        state.quickItemPopupKeyEntry.reset();

        for (size_t slot = 0; box && left && slot < QuickItemSlotCount; ++slot)
        {
            if (keyChip(*box, slot, layout->k).contains(x, y))
            {
                QuickItemSlot &quickSlot = member.quickItemSlots[slot];
                quickSlot.itemId = quickSlot.itemId == entries[entryIndex].itemId ? 0 : entries[entryIndex].itemId;
                return true;
            }
        }

        if (box && box->contains(x, y))
        {
            return true;
        }
    }

    if (left && layout->close.contains(x, y))
    {
        closePopup(context);
        return true;
    }

    // The buttons: the open one closes its popup, the other switches to its own.
    for (const QuickItemPopupKind buttonKind : {QuickItemPopupKind::Scrolls, QuickItemPopupKind::Potions})
    {
        const std::optional<Circle> button = itemButtonCircle(context, width, height, buttonKind);

        if (left && button && button->contains(x, y))
        {
            const size_t member = state.quickItemPopupMember;
            togglePopup(context, party, buttonKind);

            if (state.quickItemPopup != QuickItemPopupKind::None)
            {
                state.quickItemPopupMember = member;
            }

            return true;
        }
    }

    // A portrait chooses who drinks or reads.
    for (size_t index = 0; index < std::min<size_t>(5, party.members().size()); ++index)
    {
        const std::optional<GameplayResolvedHudLayoutElement> face = faceRect(context, width, height, index);

        if (left && face && x >= face->x && x < face->x + face->width && y >= face->y && y < face->y + face->height)
        {
            state.quickItemPopupMember = index;
            return true;
        }
    }

    if (left && maxScroll > 0 && layout->track.contains(x, y))
    {
        const float position = (y - layout->track.y) / std::max(1.0f, layout->track.height);
        state.quickItemPopupScroll = std::min(size_t(std::lround(position * float(maxScroll))), maxScroll);
        return true;
    }

    if (under)
    {
        const PopupEntry &entry = entries[*under];

        if (right)
        {
            state.quickItemPopupKeyEntry = *under;
            return true;
        }

        const size_t user = state.quickItemPopupMember;
        const std::optional<QuickItemSlots::PartyLocation> location =
            QuickItemSlots::findPartyItemOfPower(party, user, entry.itemId, entry.power, bagCount(party));

        // The popup closes first: a scroll's spell then takes its target over the running game, as one read from
        // the inventory does.
        closePopup(context);

        if (location)
        {
            context.itemService().useCarriedItem(context, user, *location);
        }

        return true;
    }

    // A click away closes the popup.
    if (!layout->panel.contains(x, y))
    {
        closePopup(context);
    }

    return true;
}
}

bool GameplayQuickItems::ringOpen(GameplayScreenRuntime &context)
{
    return context.interactionState().quickItemRingOpen;
}

bool GameplayQuickItems::popupOpen(GameplayScreenRuntime &context)
{
    return context.interactionState().quickItemPopup != QuickItemPopupKind::None;
}

bool GameplayQuickItems::needsCursor(GameplayScreenRuntime &context)
{
    return ringOpen(context) || popupOpen(context);
}

bool GameplayQuickItems::takesPointer(GameplayScreenRuntime &context)
{
    const GameplayOverlayInteractionState &state = context.interactionState();
    return state.quickItemRingOpen || state.quickItemPopup != QuickItemPopupKind::None || state.quickItemClickLatch;
}

bool GameplayQuickItems::takesPointerAction(GameplayScreenRuntime &context, KeyboardAction action)
{
    return takesPointer(context)
        && context.settingsSnapshot().keyboard.binding(action).kind != InputBindingKind::Keyboard;
}

void GameplayQuickItems::renderHud(GameplayScreenRuntime &context, int width, int height)
{
    const Party *pParty = context.partyReadOnly();
    const ItemTable *pItemTable = context.itemTable();

    if (pParty == nullptr || pItemTable == nullptr)
    {
        return;
    }

    const Painter paint(context);
    const GameplayOverlayInteractionState &state = context.interactionState();
    const size_t members = std::min<size_t>(5, pParty->members().size());
    renderItemButtons(context, *pParty, width, height);

    if (state.quickItemPopup != QuickItemPopupKind::None)
    {
        renderPopup(context, *pParty, width, height);
        return;
    }

    // The buttons: a small round obsidian plate showing a miniature of slot 1's item (user, 2026-10-25), greyed with
    // its party-wide count when nobody carries one; an empty black socket when slot 1 is empty (user).
    for (size_t member = 0; member < members; ++member)
    {
        const std::optional<Circle> button = buttonCircle(context, width, height, member);
        const Character *pMember = pParty->member(member);

        if (!button || pMember == nullptr)
        {
            continue;
        }

        const bool on = state.quickItemRingOpen && state.quickItemRingMember == member;
        const QuickItemSlot &first = pMember->quickItemSlots[0];
        const ItemDefinition *pItem = first.itemId != 0 ? pItemTable->get(first.itemId) : nullptr;
        paint.disc(*button, Disc);

        if (pItem == nullptr)
        {
            paint.disc({button->x, button->y, button->radius * 0.62f}, Socket);
        }

        paint.ring(*button, 3.2f, on);

        if (pItem != nullptr)
        {
            const size_t count = QuickItemSlots::countPartyItems(*pParty, first, bagCount(*pParty));
            const float iconHeight = button->radius * 1.5f;
            paint.icon(pItem->iconName, {button->x - button->radius, button->y - iconHeight / 2, 2 * button->radius,
                iconHeight}, count == 0);
            const float textHeight = std::max(9.0f, button->radius * 0.62f);
            paint.text("Lucida", textHeight, count == 0 ? Bad : count <= 2 ? Warn : Ivory, std::to_string(count),
                button->x + button->radius * 1.05f, button->y + button->radius - textHeight * 0.55f, 2);
        }
    }

    if (!state.quickItemRingOpen || state.quickItemRingMember >= members)
    {
        return;
    }

    const std::optional<RingLayout> layout = ringLayout(context, width, height, state.quickItemRingMember);
    const Character *pMember = pParty->member(state.quickItemRingMember);

    if (!layout || pMember == nullptr)
    {
        return;
    }

    const float unit = layout->unit;
    paint.disc(layout->backdrop, Dim);

    for (size_t slot = 0; slot < QuickItemSlotCount; ++slot)
    {
        const Circle &circle = layout->slots[slot];
        const QuickItemSlot &quickSlot = pMember->quickItemSlots[slot];
        const ItemDefinition *pItem = quickSlot.itemId != 0 ? pItemTable->get(quickSlot.itemId) : nullptr;
        const bool hot = state.quickItemHoveredSlot == slot || state.quickItemPickerSlot == slot;
        paint.disc(circle, Disc);
        paint.ring(circle, hot ? 4.0f : 3.2f, hot);

        if (pItem != nullptr)
        {
            // The slot's kind across the party: the owner's bags first, then the others' (useQuickItemSlot).
            const size_t count = QuickItemSlots::countPartyItems(*pParty, quickSlot, bagCount(*pParty));
            const float iconHeight = circle.radius * 1.55f;
            paint.icon(pItem->iconName, {circle.x - circle.radius, circle.y - iconHeight / 2, 2 * circle.radius,
                iconHeight}, count == 0);
            // The count: amber at two or fewer, red when none is left.
            const std::string countText = std::to_string(count);
            const float badgeHeight = 20 * unit;
            const float badgeWidth = std::max(26 * unit, paint.width("Lucida", 13 * unit, countText) + 10 * unit);
            const Box badge = {circle.x + circle.radius - badgeWidth + 4 * unit,
                circle.y + circle.radius - badgeHeight + 2 * unit, badgeWidth, badgeHeight};
            paint.fill(badge, Badge);
            paint.frame(badge, std::max(1.0f, unit), count == 0 ? Bad : count <= 2 ? Warn : BadgeBorder);
            paint.text("Lucida", 13 * unit, count == 0 ? Bad : count <= 2 ? Warn : Ivory, countText,
                badge.x + badge.width / 2, badge.y + 3 * unit, 1);
            paint.text("Lucida", 12 * unit, Body, pItem->name, circle.x, circle.y + circle.radius + 4 * unit, 1);
        }
        else
        {
            paint.text("Fondamento", 34 * unit, abgr(0x9a8d64), "+", circle.x, circle.y - 20 * unit, 1);
        }

        // The slot's key, only when one is bound (slots 2-6 are unbound by default).
        const InputBinding binding = context.settingsSnapshot().keyboard.binding(
            KeyboardAction(size_t(KeyboardAction::QuickItem1) + slot));

        if (binding.kind != InputBindingKind::None)
        {
            const std::string keyText = inputBindingDisplayName(binding);
            const float keyWidth = std::max(22 * unit, paint.width("Lucida", 14 * unit, keyText) + 10 * unit);
            const Box key = {circle.x - circle.radius - 6 * unit, circle.y - circle.radius - 4 * unit, keyWidth,
                22 * unit};
            paint.fill(key, abgr(0x1c2524));
            paint.frame(key, std::max(1.0f, unit), abgr(0x6b6a4e));
            paint.text("Lucida", 14 * unit, Gold, keyText, key.x + key.width / 2, key.y + 3 * unit, 1);
        }
    }

    paint.disc(layout->hub, abgr(0x0d1716));
    paint.ring(layout->hub, 3.0f, false);
    paint.text("Fondamento", 19 * unit, Label, pMember->name, layout->hub.x, layout->hub.y - 16 * unit, 1);
    const std::string stateText = hubState(context, *pParty, state.quickItemRingMember);
    paint.text("Lucida", 11 * unit, stateText == "nobody ready" ? Warn : Muted, stateText, layout->hub.x,
        layout->hub.y + 8 * unit, 1);

    if (state.quickItemPickerSlot && *state.quickItemPickerSlot < QuickItemSlotCount)
    {
        if (const std::optional<PickerLayout> picker = pickerLayout(context, width, height, state.quickItemRingMember))
        {
            renderPicker(context, *pParty, *pMember, *state.quickItemPickerSlot, *picker);
        }
    }
}

bool GameplayQuickItems::handleHudInput(GameplayScreenRuntime &context, const GameplayInputFrame &input, int width,
    int height, bool allowInput, bool pointerAllowed)
{
    GameplayOverlayInteractionState &state = context.interactionState();
    Party *pParty = context.party();

    if (!allowInput || pParty == nullptr)
    {
        closeRing(context);
        closePopup(context);
        state.quickItemWheelHeld = false;
        state.quickItemClickLatch = false;
        return false;
    }

    // The latch keeps a click on the ring from reaching the world until its button is let go.
    if (!input.leftMouseButton.held && !input.rightMouseButton.held)
    {
        state.quickItemClickLatch = false;
    }

    const size_t members = std::min<size_t>(5, pParty->members().size());
    const auto hoveredSlot = [&]() -> std::optional<size_t>
    {
        const std::optional<RingLayout> layout = ringLayout(context, width, height, state.quickItemRingMember);

        for (size_t slot = 0; layout && slot < QuickItemSlotCount; ++slot)
        {
            if (layout->slots[slot].contains(input.pointerX, input.pointerY))
            {
                return slot;
            }
        }

        return std::nullopt;
    };

    // Escape closes the popup, else the picker, else the ring.
    const bool escape = input.isScancodeHeld(SDL_SCANCODE_ESCAPE);
    const bool escapePressed = escape && !state.quickItemEscapeHeld;
    state.quickItemEscapeHeld = escape;

    // The Potions key opens the potion popup (the active member's ring with the quick item rings on), the Scrolls key
    // the scroll popup; each closes its own.
    const GameplayButtonInputState &wheel = input.action(KeyboardAction::QuickItemWheel);
    const bool rings = context.settingsSnapshot().quickItemRings;

    if (input.action(KeyboardAction::ScrollPopup).pressed)
    {
        togglePopup(context, *pParty, QuickItemPopupKind::Scrolls);
    }
    else if (!rings && wheel.pressed)
    {
        togglePopup(context, *pParty, QuickItemPopupKind::Potions);
    }

    if (state.quickItemPopup != QuickItemPopupKind::None)
    {
        return handlePopupInput(context, input, *pParty, width, height, pointerAllowed, escapePressed);
    }

    // The basebar's buttons open their popups.
    for (const QuickItemPopupKind kind : {QuickItemPopupKind::Scrolls, QuickItemPopupKind::Potions})
    {
        const std::optional<Circle> button = itemButtonCircle(context, width, height, kind);

        if (pointerAllowed && input.leftMouseButton.pressed && button
            && button->contains(input.pointerX, input.pointerY))
        {
            togglePopup(context, *pParty, kind);
            state.quickItemClickLatch = true;
            return true;
        }
    }

    // The wheel key (quick item rings on): a tap opens the active member's ring (or closes it), a hold uses the slot it
    // is released over.
    if (rings && wheel.pressed && !state.quickItemWheelHeld)
    {
        state.quickItemWheelHeld = true;
        state.quickItemWheelPressedTicks = SDL_GetTicks();
        const size_t active = pParty->activeMemberIndex();
        const bool same = state.quickItemRingOpen && state.quickItemRingMember == active;
        closeRing(context);

        if (!same)
        {
            state.quickItemRingOpen = true;
            state.quickItemRingMember = active;
        }
    }
    else if (!wheel.held && state.quickItemWheelHeld)
    {
        state.quickItemWheelHeld = false;

        if (state.quickItemRingOpen && !state.quickItemPickerSlot
            && SDL_GetTicks() - state.quickItemWheelPressedTicks >= WheelHoldTicks)
        {
            const std::optional<size_t> slot = pointerAllowed ? hoveredSlot() : std::nullopt;
            closeRing(context);

            if (slot)
            {
                context.itemService().useQuickItemSlot(context, state.quickItemRingMember, *slot);
            }
        }
    }

    state.quickItemHoveredSlot =
        state.quickItemRingOpen && pointerAllowed && !state.quickItemPickerSlot ? hoveredSlot() : std::nullopt;

    if (state.quickItemRingOpen && escapePressed)
    {
        if (state.quickItemPickerSlot)
        {
            state.quickItemPickerSlot.reset();
        }
        else
        {
            closeRing(context);
        }

        state.menuToggleLatch = true;
        return true;
    }

    const bool left = pointerAllowed && input.leftMouseButton.pressed;
    const bool right = pointerAllowed && input.rightMouseButton.pressed;
    Character *pMember = state.quickItemRingOpen ? pParty->member(state.quickItemRingMember) : nullptr;

    // The picker takes its own clicks and wheel.
    if (pMember != nullptr && state.quickItemPickerSlot && *state.quickItemPickerSlot < QuickItemSlotCount)
    {
        const std::optional<PickerLayout> picker = pickerLayout(context, width, height, state.quickItemRingMember);

        if (picker && pointerAllowed
            && handlePickerInput(context, input, *pParty, *pMember, *state.quickItemPickerSlot, *picker, left))
        {
            state.quickItemClickLatch = left || state.quickItemClickLatch;
            return true;
        }
    }

    if (!left && !right)
    {
        return state.quickItemRingOpen
            && (input.leftMouseButton.held || input.rightMouseButton.held) && state.quickItemClickLatch;
    }

    // A button opens or closes its member's ring.
    for (size_t member = 0; member < members && left; ++member)
    {
        const std::optional<Circle> button = buttonCircle(context, width, height, member);

        if (button && button->contains(input.pointerX, input.pointerY))
        {
            const bool same = state.quickItemRingOpen && state.quickItemRingMember == member;
            closeRing(context);

            if (!same)
            {
                state.quickItemRingOpen = true;
                state.quickItemRingMember = member;
            }

            state.quickItemClickLatch = true;
            return true;
        }
    }

    if (!state.quickItemRingOpen || pMember == nullptr)
    {
        return false;
    }

    state.quickItemClickLatch = true;
    const std::optional<RingLayout> layout = ringLayout(context, width, height, state.quickItemRingMember);
    std::optional<size_t> slot;

    for (size_t index = 0; layout && index < QuickItemSlotCount; ++index)
    {
        if (layout->slots[index].contains(input.pointerX, input.pointerY))
        {
            slot = index;
        }
    }

    if (slot)
    {
        // A click uses the slot; an empty one, or a right click, opens the picker for it.
        if (right || pMember->quickItemSlots[*slot].itemId == 0)
        {
            openPicker(context, *slot);
        }
        else
        {
            state.quickItemPickerSlot.reset();
            context.itemService().useQuickItemSlot(context, state.quickItemRingMember, *slot);
        }

        return true;
    }

    // A click away closes the picker first, then the ring; one on the dimmed disc does nothing.
    if (state.quickItemPickerSlot)
    {
        state.quickItemPickerSlot.reset();
    }
    else if (!layout || !layout->backdrop.contains(input.pointerX, input.pointerY)
        || layout->hub.contains(input.pointerX, input.pointerY))
    {
        closeRing(context);
    }

    return true;
}
}
