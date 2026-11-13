#include "game/ui/GameplayJournalAuras.h"
#include "game/ui/GameplayObsidianPainter.h"

#include "engine/Localization.h"
#include "engine/Utf8Text.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/SkillData.h"
#include "game/party/WorldSpells.h"
#include "game/rules/GameRules.h"
#include "game/tables/SpellTable.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayUiSkin.h"
#include "game/ui/SpellbookUiLayout.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// The approved study's colours (maw_aura_panel_20261025 index.html), as ABGR.
constexpr uint32_t abgr(uint32_t rgb, uint32_t alpha = 0xff)
{
    return alpha << 24 | (rgb & 0xffu) << 16 | (rgb & 0xff00u) | (rgb >> 16 & 0xffu);
}

constexpr uint32_t Ivory = abgr(0xefe0bc);
constexpr uint32_t Label = abgr(0xe6d1a8);
constexpr uint32_t Body = abgr(0xc8c7a7);
constexpr uint32_t Muted = abgr(0x9fa594);
constexpr uint32_t Gold = abgr(0xe3c185);
constexpr uint32_t Good = abgr(0x8fe08a);
constexpr uint32_t Warn = abgr(0xffb347);
constexpr uint32_t Bad = abgr(0xff6a5a);
constexpr uint32_t Mana = abgr(0x8fc3ff);
constexpr uint32_t Dim = abgr(0xb4ab92);
constexpr uint32_t CardFill = abgr(0x0a1312, 0xb3);
constexpr uint32_t CardBorder = abgr(0x4a5140);
constexpr uint32_t Brass = abgr(0x8c815f);
constexpr uint32_t RowRule = abgr(0x2f3a33);
constexpr uint32_t RowHover = abgr(0xffffff, 0x0d);
constexpr uint32_t RowSelected = abgr(0xe3c185, 0x2a);
constexpr uint32_t WhoRule = abgr(0xffffff, 0x0f);
constexpr uint32_t BarTrack = abgr(0x0a1312);
constexpr uint32_t BarBorder = abgr(0x938666);
constexpr uint32_t MenuFill = abgr(0x0b1212, 0xf5);
constexpr uint32_t MenuRule = abgr(0x3c4436);
constexpr uint32_t MenuHot = abgr(0xe3c185, 0x26);
constexpr uint32_t Divider = abgr(0xc9a96a, 0xc0);
constexpr uint32_t Shade = abgr(0x05090a, 0x90);

constexpr char TextFont[] = "alegreya_semibold";
constexpr char TitleFont[] = "Fondamento";

// The layout in the page's logical units (600 x 456, JournalAuraPage: the Journal's frame inside its border, the
// right rail included). The content column is 518 wide, as the Progress tab's.
constexpr float ContentWidth = 518;
constexpr float CardLeft = 4;
constexpr float CardTop = 53;
constexpr float CardWidth = 98;
constexpr float CardHeight = 66;
constexpr float CardGap = 5.25f;
constexpr float ListLeft = 4;
constexpr float ListRight = 258;
constexpr float HeaderTop = 133;
constexpr float RowTop = 146;
constexpr float RowHeight = 18.6f;
constexpr size_t VisibleRows = 15;
constexpr float DividerX = 263;
constexpr float DetailLeft = 270;
constexpr float DetailRight = 518;
constexpr float DetailBottom = 412;
constexpr float ButtonTop = 418;
constexpr float ButtonHeight = 19;
constexpr float ReleaseLeft = 278;
constexpr float ReleaseWidth = 78;
constexpr float MoveLeft = 369;
constexpr float MoveWidth = 76;
constexpr float RailCenter = 560.5f;
constexpr float RailButtonWidth = 59;
constexpr float RailButtonHeight = 17;
constexpr float ReleaseAllTop = 17;
constexpr float SpellbookTop = 72;
constexpr float LegendTop = 121;
constexpr float MenuLeft = 339;
constexpr float MenuWidth = 175;
constexpr float MenuRowHeight = 20;
constexpr float TextHeight = 9.5f;
constexpr float SmallHeight = 8;

constexpr std::array<std::string_view, 5> MasteryNames = {"", Engine::trNoop("Normal"), Engine::trNoop("Expert"),
    Engine::trNoop("Master"), Engine::trNoop("Grandmaster")};
constexpr std::array<std::string_view, 5> StateNames = {Engine::trNoop("Active"), Engine::trNoop("Partly used"),
    Engine::trNoop("Adds nothing"), Engine::trNoop("Suspended"), Engine::trNoop("Blessing")};
constexpr std::array<std::string_view, 5> LegendTexts = {Engine::trNoop("full effect"),
    Engine::trNoop("a stronger source covers part"), Engine::trNoop("a stronger source covers all"),
    Engine::trNoop("holder down: off, still reserved"), Engine::trNoop("temple, scroll or pedestal; reserves nothing")};

using Rect = GameplayObsidianRect;

Rect pageRect(const GameplayResolvedHudLayoutElement &page, float x, float y, float width, float height)
{
    return {page.x + x * page.scale, page.y + y * page.scale, width * page.scale, height * page.scale};
}

const std::string Dot = " \xB7 ";

std::string number(double value, int decimals = 1)
{
    char text[32] = {};
    std::snprintf(text, sizeof(text), "%.*f", decimals, value);
    std::string result = text;

    if (result.find('.') != std::string::npos)
    {
        while (result.back() == '0')
        {
            result.pop_back();
        }

        if (result.back() == '.')
        {
            result.pop_back();
        }
    }

    return result == "-0" ? "0" : result;
}

// Whole numbers with thousands separators.
std::string grouped(int value)
{
    std::string digits = std::to_string(std::abs(value));

    for (int index = int(digits.size()) - 3; index > 0; index -= 3)
    {
        digits.insert(size_t(index), ",");
    }

    return value < 0 ? "-" + digits : digits;
}

std::string valueText(AuraValueKind kind, double value)
{
    switch (kind)
    {
        case AuraValueKind::Bonus:
            return "+" + number(value);
        case AuraValueKind::BonusPercent:
            return "+" + number(value) + " %";
        case AuraValueKind::ReductionPercent:
            return "-" + number(value) + " %";
        case AuraValueKind::Text:
            break;
    }

    return {};
}

std::string effectValue(const AuraEffect &effect)
{
    return effect.kind == AuraValueKind::Text ? effect.text : valueText(effect.kind, effect.value);
}

// The effect's short name for a member's row: "armour" of "Stone Skin, armour".
std::string shortLabel(const std::string &label)
{
    const size_t comma = label.find(", ");
    std::string result = comma != std::string::npos ? label.substr(comma + 2) : label;

    if (result.empty() || result.find(' ') != std::string::npos)
    {
        return result;
    }

    const Engine::Utf8::Character first = Engine::Utf8::decode(result, 0);
    std::string lowered;
    Engine::Utf8::append(lowered, Engine::Utf8::lower(first.point));
    return lowered + result.substr(first.size);
}

// The spell's name as the rules give it (MAW's Meditation on Telepathy's id).
std::string spellName(const GameplayScreenRuntime &context, uint32_t spellId)
{
    const SpellEntry *pSpell = context.spellTable() != nullptr ? context.spellTable()->findById(int(spellId)) : nullptr;
    const Party *pParty = context.partyReadOnly();

    if (pSpell == nullptr || pSpell->name.empty())
    {
        return Engine::tr("Spell {id}", {{"id", spellId}});
    }

    // In the interface language, as the buff panels name them (issue #31, OY-577).
    return Engine::localize(pParty != nullptr && !pParty->members().empty()
            ? partySpellName(pParty, pParty->members().front(), *pSpell) : pSpell->name,
        "spell");
}

std::string memberName(const Party &party, std::optional<size_t> memberIndex)
{
    const Character *pMember = memberIndex ? party.member(*memberIndex) : nullptr;
    return pMember != nullptr ? pMember->name : Engine::tr("a blessing");
}

// English writes the possessive of a name ending in s without a second s ("Lewis'"); the sentences have both forms.
bool plainPossessive(const std::string &name)
{
    return name.empty() || name.back() != 's';
}

// What happened to a holder whose auras are off.
std::string downWord(const Character &member)
{
    return member.conditions.test(size_t(CharacterCondition::Eradicated)) ? Engine::tr("eradicated")
        : member.conditions.test(size_t(CharacterCondition::Dead)) ? Engine::tr("dead")
        : member.conditions.test(size_t(CharacterCondition::Petrified)) ? Engine::tr("stoned")
        : Engine::tr("unconscious");
}

// A stronger source in words: "Hour of Power (Serena)", "own potion".
std::string rivalName(const GameplayScreenRuntime &context, const Party &party, const AuraRival &rival)
{
    if (rival.potion)
    {
        return Engine::tr("own {spell} potion", {{"spell", spellName(context, rival.spellId)}});
    }

    return rival.memberIndex
        ? Engine::tr("{spell} ({member})",
            {{"spell", spellName(context, rival.spellId)}, {"member", memberName(party, rival.memberIndex)}})
        : Engine::tr("{spell} (blessing)", {{"spell", spellName(context, rival.spellId)}});
}

// "120 SP", "45 HP".
std::string pointsText(const std::string &points, bool health)
{
    return health ? Engine::tr("{points} HP", {{"points", points}}) : Engine::tr("{points} SP", {{"points", points}});
}

// The effect as the interface language shows it: its label comes from the rules in English.
std::string effectLabel(const AuraEffect &effect)
{
    return Engine::localizeKnown(effect.label);
}

std::string effectValueText(const AuraEffect &effect)
{
    return effect.kind == AuraValueKind::Text ? Engine::localizeKnown(effect.text) : effectValue(effect);
}

std::string reservedText(const AuraReportEntry &entry, bool brief)
{
    if (!entry.holder || entry.cost.free)
    {
        return brief ? "-" : Engine::tr("nothing");
    }

    if (!entry.cost.flat)
    {
        return number(entry.cost.percent) + " %";
    }

    const std::string points = std::to_string(entry.cost.points);

    if (brief)
    {
        return pointsText(points, entry.cost.health);
    }

    return entry.cost.health ? Engine::tr("{points} hit points", {{"points", points}})
                             : Engine::tr("{points} spell points", {{"points", points}});
}


// The shared Obsidian drawing with the aura page's own pieces: pool bars, state pills and the hatch.
class Painter : public GameplayObsidianPainter
{
public:
    using GameplayObsidianPainter::GameplayObsidianPainter;

    void icon(uint32_t spellId, const Rect &box, bool dim) const
    {
        spellIcon(spellId, box, dim);
    }

    // A pool bar as the reserve study's option A: the fill, a hatched span for what the auras hold and a gold mark
    // where the free pool ends.
    void poolBar(const Rect &bar, const AuraMemberPool &pool) const
    {
        fill(bar, BarTrack);

        if (pool.maximum <= 0)
        {
            frame(bar, abgr(0x938666, 0x60));
            return;
        }

        const float line = std::max(1.0f, std::round(m_page.scale * 0.6f));
        const Rect inner = {bar.x + line, bar.y + line, bar.width - 2 * line, bar.height - 2 * line};
        const float current = std::clamp(float(pool.current) / pool.maximum, 0.0f, 1.0f);
        const float held = std::clamp(float(pool.reserved) / pool.maximum, 0.0f, 1.0f);
        const std::optional<GameplayHudTextureHandle> fillTexture = pool.health
            ? GameplayUiSkin::healthMeterTexture(m_context, 1.0f) : manaTexture();

        if (fillTexture && current > 0)
        {
            m_context.submitHudTexturedQuad(*fillTexture, inner.x, inner.y, inner.width * current, inner.height);
        }

        if (held > 0)
        {
            hatch({inner.x + inner.width * (1 - held), inner.y, inner.width * held, inner.height}, pool.health);
        }

        frame(bar, BarBorder);

        if (held > 0)
        {
            const float markX = inner.x + inner.width * (1 - held);
            const float markWidth = std::max(2.0f, std::round(m_page.scale * 1.4f));
            fill({markX - markWidth / 2 - line, bar.y - 2 * line, markWidth + 2 * line, bar.height + 4 * line},
                abgr(0x000000));
            fill({markX - markWidth / 2, bar.y - line, markWidth, bar.height + 2 * line}, Gold);
        }
    }

    // A state pill: its colour, its words centred on x.
    void pill(AuraState state, float x, float y) const
    {
        static constexpr std::array<std::array<uint32_t, 3>, 5> Colours = {{
            {abgr(0x8fe08a), abgr(0x4f7d4c), abgr(0x122414, 0x66)},
            {abgr(0xffb347), abgr(0x8a6a35), abgr(0x2a1f0f, 0x66)},
            {abgr(0xffb347), abgr(0x8a6a35), abgr(0x2a1f0f, 0x99)},
            {abgr(0xff6a5a), abgr(0x8a4a3a), abgr(0x2a1210, 0x66)},
            {abgr(0x8fc3ff), abgr(0x4b6a80), abgr(0x0f1d2a, 0x66)},
        }};
        const std::array<uint32_t, 3> &colour = Colours[size_t(state)];
        const std::string name = Engine::tr(StateNames[size_t(state)]);
        const float textWidth = width(TextFont, SmallHeight, name);
        const Rect box = rect(x - textWidth / 2 - 4.5f, y, textWidth + 9, 11.5f);
        fill(box, colour[2]);
        frame(box, colour[1]);
        text(TextFont, SmallHeight, colour[0], name, x, y + 1.6f, 1);
    }

    float pillWidth(AuraState state) const
    {
        return width(TextFont, SmallHeight, Engine::tr(StateNames[size_t(state)])) + 9;
    }

private:
    // The mana arcs' blue as a vertical gradient (GameplayUiSkin's Mana material).
    std::optional<GameplayHudTextureHandle> manaTexture() const
    {
        GameplayUiRuntime &runtime = m_context.gameplayUiRuntime();
        const char *pName = "__journal_auras_mana__";
        const char *pSignature = "aura-mana-v2";

        if (const std::optional<GameplayHudTextureHandle> cached = runtime.findCachedDynamicHudTexture(pName, pSignature))
        {
            return cached;
        }

        constexpr std::array<uint32_t, 3> Stops = {0xabcfd8, 0x73a4b7, 0x2d596a};
        constexpr int Height = 32;
        std::vector<uint8_t> pixels(Height * 4);

        for (int y = 0; y < Height; ++y)
        {
            const float phase = y / float(Height - 1);
            const size_t stop = phase < 0.45f ? 0 : 1;
            const float t = stop == 0 ? phase / 0.45f : (phase - 0.45f) / 0.55f;

            // The HUD's dynamic textures are BGRA: the lowest byte of 0xRRGGBB first (as GameplayUiSkin's).
            for (int channel = 0; channel < 3; ++channel)
            {
                const int from = int(Stops[stop] >> (channel * 8) & 0xff);
                const int to = int(Stops[stop + 1] >> (channel * 8) & 0xff);
                pixels[size_t(y) * 4 + channel] = uint8_t(from + (to - from) * t);
            }

            pixels[size_t(y) * 4 + 3] = 255;
        }

        const std::optional<GameplayHudTextureHandle> texture = runtime.ensureDynamicHudTexture(pName, 1, Height, pixels);

        if (texture)
        {
            runtime.setDynamicHudTextureContentSignature(pName, pSignature);
        }

        return texture;
    }

    // The portrait arcs' hatch (GameplayUiSkin::renderReservedArc's colours) in square tiles along the span.
    void hatch(const Rect &span, bool health) const
    {
        GameplayUiRuntime &runtime = m_context.gameplayUiRuntime();
        const char *pName = health ? "__journal_auras_hatch_hp__" : "__journal_auras_hatch_sp__";
        const char *pSignature = "aura-hatch-v2";
        std::optional<GameplayHudTextureHandle> texture = runtime.findCachedDynamicHudTexture(pName, pSignature);

        if (!texture)
        {
            constexpr int Size = 16;
            const uint32_t base = health ? 0x25301f : 0x1b2a36;
            const uint32_t stripe = health ? 0x7f9a6c : 0x5f88a0;
            std::vector<uint8_t> pixels(Size * Size * 4);

            for (int y = 0; y < Size; ++y)
            {
                for (int x = 0; x < Size; ++x)
                {
                    const uint32_t colour = (x + Size - y) % (Size / 2) < Size / 5 ? stripe : base;
                    const size_t pixel = size_t(y * Size + x) * 4;

                    for (int channel = 0; channel < 3; ++channel)
                    {
                        pixels[pixel + channel] = uint8_t(colour >> (channel * 8) & 0xff);
                    }

                    pixels[pixel + 3] = 255;
                }
            }

            texture = runtime.ensureDynamicHudTexture(pName, Size, Size, pixels);

            if (texture)
            {
                runtime.setDynamicHudTextureContentSignature(pName, pSignature);
            }
        }

        if (!texture || span.width <= 0 || span.height <= 0)
        {
            return;
        }

        std::vector<GameplayHudBatchQuad> quads;
        const float tile = span.height * 1.6f;

        for (float x = 0; x < span.width; x += tile)
        {
            const float part = std::min(tile, span.width - x);
            GameplayHudBatchQuad quad;
            quad.textureHandle = texture->textureHandle;
            quad.x = span.x + x;
            quad.y = span.y;
            quad.width = part;
            quad.height = span.height;
            quad.u1 = part / tile;
            quads.push_back(quad);
        }

        m_context.submitHudQuadBatch(quads);
    }
};

std::optional<AuraReport> reportOf(const GameplayScreenRuntime &context)
{
    const Party *pParty = context.partyReadOnly();
    return pParty != nullptr ? gameRulesFor(pParty).spells.auraReport(*pParty) : std::nullopt;
}

// The chosen aura: the one selected, else the first.
const AuraReportEntry *shownAura(const AuraReport &report, uint32_t selected)
{
    for (const AuraReportEntry &entry : report.auras)
    {
        if (entry.spellId == selected)
        {
            return &entry;
        }
    }

    return report.auras.empty() ? nullptr : &report.auras.front();
}

size_t maximumScroll(const AuraReport &report)
{
    return report.auras.size() > VisibleRows ? report.auras.size() - VisibleRows : 0;
}

bool canMove(const AuraReportEntry &entry)
{
    return std::any_of(entry.moveTo.begin(), entry.moveTo.end(),
        [](const AuraMoveOption &option)
        {
            return option.knowsSpell;
        });
}

float menuTop(const AuraReportEntry &entry)
{
    return ButtonTop - 6 - (24 + entry.moveTo.size() * MenuRowHeight + 44);
}

Rect menuRect(const GameplayResolvedHudLayoutElement &page, const AuraReportEntry &entry)
{
    return pageRect(page, MenuLeft, menuTop(entry), MenuWidth, 24 + entry.moveTo.size() * MenuRowHeight + 44);
}
}

bool journalHasAuraPanel(const GameplayScreenRuntime &context)
{
    return reportOf(context).has_value();
}

void openJournalAuraPanel(GameplayScreenRuntime &context)
{
    GameplayUiController::JournalScreenState &journal = context.journalScreenState();

    if (!journal.active)
    {
        context.openJournalOverlay();
    }

    journal.view = GameplayUiController::JournalView::Auras;
    journal.auraScroll = 0;
    journal.auraMoveMenuOpen = false;
    journal.mapDragActive = false;
}

uint32_t packJournalAuraTarget(const JournalAuraTarget &target)
{
    return uint32_t(target.kind) << 16 | uint32_t(target.index & 0xffffu);
}

JournalAuraTarget unpackJournalAuraTarget(uint32_t packed)
{
    return {JournalAuraTargetKind(packed >> 16), size_t(packed & 0xffffu)};
}

JournalAuraTarget journalAuraTargetAt(
    const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float x,
    float y)
{
    const std::optional<AuraReport> report = reportOf(context);

    if (!report)
    {
        return {};
    }

    const AuraReportEntry *pShown = shownAura(*report, journal.auraSelected);

    // The open menu takes the clicks over it first.
    if (journal.auraMoveMenuOpen && pShown != nullptr)
    {
        const Rect menu = menuRect(page, *pShown);

        for (size_t row = 0; row < pShown->moveTo.size(); ++row)
        {
            if (pageRect(page, MenuLeft, menuTop(*pShown) + 24 + row * MenuRowHeight, MenuWidth, MenuRowHeight)
                    .contains(x, y))
            {
                return {JournalAuraTargetKind::MoveMember, pShown->moveTo[row].memberIndex};
            }
        }

        if (menu.contains(x, y))
        {
            return {JournalAuraTargetKind::MoveMenuBody, 0};
        }
    }

    if (pageRect(page, RailCenter - RailButtonWidth / 2, ReleaseAllTop, RailButtonWidth, RailButtonHeight).contains(x, y))
    {
        return {JournalAuraTargetKind::ReleaseAll, 0};
    }

    if (pageRect(page, RailCenter - RailButtonWidth / 2, SpellbookTop, RailButtonWidth, RailButtonHeight).contains(x, y))
    {
        return {JournalAuraTargetKind::Spellbook, 0};
    }

    if (pShown != nullptr)
    {
        if (pageRect(page, ReleaseLeft, ButtonTop, ReleaseWidth, ButtonHeight).contains(x, y) && pShown->holder)
        {
            return {JournalAuraTargetKind::Release, 0};
        }

        if (pageRect(page, MoveLeft, ButtonTop, MoveWidth, ButtonHeight).contains(x, y) && canMove(*pShown))
        {
            return {JournalAuraTargetKind::MoveMenu, 0};
        }
    }

    const size_t scroll = std::min(journal.auraScroll, maximumScroll(*report));

    for (size_t row = 0; row < VisibleRows && scroll + row < report->auras.size(); ++row)
    {
        if (pageRect(page, ListLeft, RowTop + row * RowHeight, ListRight - ListLeft, RowHeight).contains(x, y))
        {
            return {JournalAuraTargetKind::Aura, scroll + row};
        }
    }

    return {};
}

void activateJournalAuraTarget(
    GameplayScreenRuntime &context,
    GameplayUiController::JournalScreenState &journal,
    const JournalAuraTarget &target)
{
    Party *pParty = context.party();
    const std::optional<AuraReport> report = reportOf(context);

    if (pParty == nullptr || !report)
    {
        return;
    }

    const SpellRules &spells = gameRulesFor(pParty).spells;
    const AuraReportEntry *pShown = shownAura(*report, journal.auraSelected);
    const bool menuWasOpen = journal.auraMoveMenuOpen;
    journal.auraMoveMenuOpen = false;

    switch (target.kind)
    {
        case JournalAuraTargetKind::Aura:
            if (target.index < report->auras.size())
            {
                journal.auraSelected = report->auras[target.index].spellId;
            }

            break;
        case JournalAuraTargetKind::ReleaseAll:
            if (const std::optional<std::string> status = spells.removeAllBuffs(*pParty))
            {
                spells.updateAuras(*pParty, 0.0f);
                context.setStatusBarEvent(*status);
            }

            break;
        case JournalAuraTargetKind::Spellbook:
            context.closeJournalOverlay();
            context.openSpellbookOverlay();
            break;
        case JournalAuraTargetKind::Release:
            // Letting go is the holder's own toggle: free, no recovery, the holder awake or not.
            if (pShown != nullptr && pShown->holder
                && spells.castAura(*pParty, *pShown->holder, pShown->spellId) == AuraCastResult::Released)
            {
                spells.updateAuras(*pParty, 0.0f);
                context.setStatusBarEvent(
                    Engine::tr("{spell} released", {{"spell", spellName(context, pShown->spellId)}}));
            }

            break;
        case JournalAuraTargetKind::MoveMenu:
            journal.auraMoveMenuOpen = !menuWasOpen;
            break;
        case JournalAuraTargetKind::MoveMenuBody:
            journal.auraMoveMenuOpen = true;
            break;
        case JournalAuraTargetKind::MoveMember:
        {
            const Character *pMember = pParty->member(target.index);
            const auto option = pShown != nullptr
                ? std::find_if(pShown->moveTo.begin(), pShown->moveTo.end(),
                    [&target](const AuraMoveOption &candidate)
                    {
                        return candidate.memberIndex == target.index;
                    })
                : std::vector<AuraMoveOption>::const_iterator();

            if (pMember == nullptr || pShown == nullptr || option == pShown->moveTo.end() || !option->knowsSpell)
            {
                journal.auraMoveMenuOpen = menuWasOpen;
                break;
            }

            // A cast as the new holder, as from the spellbook: they must be ready, and pay its recovery.
            if (!GameMechanics::canTakeGameplayAction(*pMember))
            {
                context.setStatusBarEvent(Engine::tr("{name} is not ready", {{"name", pMember->name}}));
                journal.auraMoveMenuOpen = true;
                break;
            }

            context.tryCastSpellFromMember(target.index, pShown->spellId, spellName(context, pShown->spellId));
            break;
        }
        case JournalAuraTargetKind::None:
            break;
    }
}

void scrollJournalAuras(
    const GameplayScreenRuntime &context,
    GameplayUiController::JournalScreenState &journal,
    float wheelDelta)
{
    const std::optional<AuraReport> report = reportOf(context);

    if (!report || wheelDelta == 0.0f)
    {
        return;
    }

    const size_t maximum = maximumScroll(*report);
    journal.auraScroll = std::min(journal.auraScroll, maximum);
    journal.auraScroll = wheelDelta > 0 ? (journal.auraScroll > 3 ? journal.auraScroll - 3 : 0)
                                        : std::min(journal.auraScroll + 3, maximum);
}

void renderJournalAuras(
    GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float pointerX,
    float pointerY)
{
    const Party *pParty = context.partyReadOnly();
    const std::optional<AuraReport> report = reportOf(context);

    if (pParty == nullptr || !report)
    {
        return;
    }

    const Painter paint(context, page);
    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    const bool mouseDown = pInput != nullptr && pInput->leftMouseButton.held;
    const JournalAuraTarget hovered = journalAuraTargetAt(context, journal, page, pointerX, pointerY);
    const AuraReportEntry *pShown = shownAura(*report, journal.auraSelected);

    // Header: the title and the party's totals.
    paint.text(TitleFont, 22, Label, Engine::tr("Auras"), ContentWidth / 2, 7, 1);
    const std::string held =
        Engine::trn("{count} aura held", "{count} auras held", report->auras.size(), {{"count", report->auras.size()}});
    const std::string reserved = report->reservedHitPoints > 0
        ? Engine::tr("{spellPoints} spell points and {hitPoints} hit points reserved",
            {{"spellPoints", grouped(report->reservedSpellPoints)}, {"hitPoints", grouped(report->reservedHitPoints)}})
        : Engine::tr("{spellPoints} spell points reserved", {{"spellPoints", grouped(report->reservedSpellPoints)}});
    const std::string totals = held + Dot + reserved + Dot + Engine::tr("releasing is free");
    paint.text(TextFont, TextHeight, Muted, totals, ContentWidth / 2, 37, 1);

    // The members' cards.
    for (size_t memberIndex = 0; memberIndex < pParty->members().size() && memberIndex < 5; ++memberIndex)
    {
        const Character &member = pParty->members()[memberIndex];
        const AuraMemberPool &pool = report->pools[memberIndex];
        const float x = CardLeft + memberIndex * (CardWidth + CardGap);
        const Rect card = paint.rect(x, CardTop, CardWidth, CardHeight);
        paint.fill(card, CardFill);
        paint.frame(card, CardBorder);
        paint.face(member, paint.rect(x + 5.5f, CardTop + 5, 25, 30), !pool.conscious);
        paint.text(TitleFont, 12, Label, paint.fitted(TitleFont, 12, member.name, CardWidth - 40), x + 36,
            CardTop + 3);

        if (pool.conscious)
        {
            paint.text(TextFont, SmallHeight, Muted, paint.fitted(TextFont, SmallHeight,
                Engine::localizeKnown(displayClassName(member.className)), CardWidth - 40), x + 36, CardTop + 20);
        }
        else
        {
            const std::string word = Engine::Utf8::capitalizedFirst(downWord(member));
            paint.text(TextFont, SmallHeight, Bad, word, x + 36, CardTop + 20);
        }

        paint.poolBar(paint.rect(x + 5.5f, CardTop + 40, CardWidth - 11, 6.4f), pool);
        const float lineY = CardTop + 51;

        if (pool.maximum <= 0)
        {
            paint.text(TextFont, SmallHeight, Muted, Engine::tr("no spell points"), x + 5.5f, lineY);
        }
        else if (pool.reserved <= 0)
        {
            paint.text(TextFont, SmallHeight, Muted,
                pool.reservesNothing ? Engine::tr("reserves nothing") : Engine::tr("holds nothing"), x + 5.5f, lineY);
            paint.text(TextFont, SmallHeight, Muted, pointsText(grouped(pool.maximum), pool.health),
                x + CardWidth - 5.5f, lineY, 2);
        }
        else
        {
            const float numberWidth = paint.text(TextFont, SmallHeight, Gold, grouped(pool.reserved), x + 5.5f, lineY);
            paint.text(TextFont, SmallHeight, Body, " " + (pool.health ? Engine::tr("HP held") : Engine::tr("SP held")),
                x + 5.5f + numberWidth, lineY);
            paint.text(TextFont, SmallHeight, Muted,
                Engine::tr("{points} free", {{"points", grouped(std::max(0, pool.maximum - pool.reserved))}}),
                x + CardWidth - 5.5f, lineY, 2);
        }
    }

    // The held auras.
    paint.text(TextFont, SmallHeight, Muted, Engine::tr("Aura"), 28, HeaderTop);
    paint.text(TextFont, SmallHeight, Muted, Engine::tr("Holder"), 118, HeaderTop);
    paint.text(TextFont, SmallHeight, Muted, Engine::tr("Reserved"), 203, HeaderTop, 2);
    paint.text(TextFont, SmallHeight, Muted, Engine::tr("State"), 232, HeaderTop, 1);
    paint.fill(paint.rect(ListLeft, RowTop - 1.5f, ListRight - ListLeft, 0.6f), CardBorder);
    const size_t scroll = std::min(journal.auraScroll, maximumScroll(*report));
    std::optional<size_t> lastHolder;

    for (size_t row = 0; row < VisibleRows && scroll + row < report->auras.size(); ++row)
    {
        const AuraReportEntry &entry = report->auras[scroll + row];
        const float y = RowTop + row * RowHeight;
        const Rect rowRect = paint.rect(ListLeft, y, ListRight - ListLeft, RowHeight);
        const bool dim = entry.state == AuraState::Suspended;

        if (&entry == pShown)
        {
            paint.fill(rowRect, RowSelected);
            paint.fill(paint.rect(ListLeft, y, 1.1f, RowHeight), Gold);
        }
        else if (hovered.kind == JournalAuraTargetKind::Aura && hovered.index == scroll + row
            && !journal.auraMoveMenuOpen)
        {
            paint.fill(rowRect, RowHover);
        }

        if (row > 0 && entry.holder != lastHolder)
        {
            paint.fill(paint.rect(ListLeft, y, ListRight - ListLeft, 0.6f), RowRule);
        }

        lastHolder = entry.holder;
        paint.icon(entry.spellId, paint.rect(ListLeft + 2, y + 1.6f, 18, 15.4f), dim);
        paint.text(TextFont, TextHeight, dim ? Dim : Ivory,
            paint.fitted(TextFont, TextHeight, spellName(context, entry.spellId), 86), 28, y + 4);
        const std::string holder = entry.holder ? memberName(*pParty, entry.holder)
            : entry.templeBlessing ? Engine::tr("Temple") : Engine::tr("Place");
        paint.text(TextFont, SmallHeight, Body, paint.fitted(TextFont, SmallHeight, holder, 50), 118, y + 5);
        paint.text(TextFont, 8.5f, Gold, reservedText(entry, true), 203, y + 4.6f, 2);
        paint.pill(entry.state, 232, y + 3.5f);
    }

    if (report->auras.empty())
    {
        paint.text(TextFont, TextHeight, Muted, Engine::tr("Nobody holds an aura. Cast a buff spell to hold it."),
            ListLeft + 4, RowTop + 4);
    }
    else if (report->auras.size() > VisibleRows)
    {
        const float track = VisibleRows * RowHeight;
        const float thumb = track * VisibleRows / report->auras.size();
        const float offset = (track - thumb) * scroll / float(maximumScroll(*report));
        paint.fill(paint.rect(ListRight + 1.5f, RowTop, 1, track), CardBorder);
        paint.fill(paint.rect(ListRight + 0.75f, RowTop + offset, 2.5f, thumb), Brass);
    }

    // The divider, faded at both ends.
    for (int step = 0; step < 12; ++step)
    {
        const float fade = 1 - std::abs(step - 5.5f) / 6;
        const uint32_t alpha = uint32_t(0xc0 * fade);
        paint.fill(paint.rect(DividerX, 140 + step * 25, 1, 25), (alpha << 24) | (Divider & 0x00ffffffu));
    }

    // The chosen aura's details.
    if (pShown != nullptr)
    {
        const AuraReportEntry &entry = *pShown;
        const Character *pHolder = entry.holder ? pParty->member(*entry.holder) : nullptr;
        const std::string holderName = pHolder != nullptr ? pHolder->name : std::string();
        constexpr float Left = DetailLeft;
        constexpr float Right = DetailRight;
        paint.icon(entry.spellId, paint.rect(Left, 128, 44, 37), entry.state == AuraState::Suspended);
        paint.text(TitleFont, 17, Label, paint.fitted(TitleFont, 17, spellName(context, entry.spellId), Right - 320),
            320, 126);
        std::string school = entry.schoolSkill;

        if (school.size() > 5 && school.compare(school.size() - 5, 5, "Magic") == 0)
        {
            school.resize(school.size() - 5);
        }

        // The school's skill name without "Magic" ("Fire Magic" is the Fire school).
        const std::string schoolName = Engine::localizeKnown(school);
        const std::string_view mastery = MasteryNames[size_t(std::clamp(entry.mastery, 0, 4))];
        const std::string masteryName = mastery.empty() ? std::string() : Engine::tr(mastery);
        const std::string strength = (entry.skillCapped
                ? Engine::tr("{school} {mastery}, skill {skill} (cap)",
                    {{"school", schoolName}, {"mastery", masteryName}, {"skill", number(entry.skill, 0)}})
                : Engine::tr("{school} {mastery}, skill {skill}",
                    {{"school", schoolName}, {"mastery", masteryName}, {"skill", number(entry.skill, 0)}}))
            + Dot + Engine::tr("level {level}", {{"level", entry.level}});
        const std::string byLine = pHolder != nullptr
            ? Engine::tr("Held by {holder}", {{"holder", holderName}}) + Dot + strength
            : (entry.templeBlessing ? Engine::tr("Temple blessing") : Engine::tr("Blessing of this place")) + Dot
                + Engine::tr("skill 7, Master, level 40");
        paint.text(TextFont, 8.5f, Muted, paint.fitted(TextFont, 8.5f, byLine, Right - 320), 320, 151);
        float y = 172;
        const auto note = [&](const std::string &value, uint32_t colour, float height = SmallHeight)
        {
            for (const std::string &line : paint.wrapped(TextFont, height, value, Right - Left))
            {
                if (y + height > DetailBottom)
                {
                    return;
                }

                paint.text(TextFont, height, colour, line, Left, y);
                y += height + 2.2f;
            }
        };

        // What it reserves and its state.
        paint.text(TextFont, TextHeight, Body, Engine::tr("Reserves"), Left, y);

        if (pHolder == nullptr || entry.cost.free)
        {
            paint.text(TextFont, TextHeight, Ivory,
                pHolder == nullptr ? Engine::tr("nothing") : Engine::tr("nothing (class)"), Right, y, 2);
        }
        else
        {
            const uint32_t colour = entry.cost.health ? Good : Mana;
            float x = Right;

            if (entry.cost.flat)
            {
                x -= paint.text(TextFont, TextHeight, Body, " " + Engine::tr("(flat)"), x, y, 2);
                paint.text(TextFont, TextHeight, colour, reservedText(entry, false), x, y, 2);
            }
            else
            {
                // "12 % of Serena's spell points · 120", the percent and the points in their own colours.
                const bool plain = plainPossessive(holderName);
                const std::string share = entry.cost.health
                    ? (plain ? Engine::tr("of {holder}'s hit points", {{"holder", holderName}})
                             : Engine::tr("of {holder}' hit points", {{"holder", holderName}}))
                    : (plain ? Engine::tr("of {holder}'s spell points", {{"holder", holderName}})
                             : Engine::tr("of {holder}' spell points", {{"holder", holderName}}));
                x -= paint.text(TextFont, TextHeight, Ivory, grouped(entry.cost.points), x, y, 2);
                x -= paint.text(TextFont, TextHeight, Body, " " + share + Dot, x, y, 2);
                paint.text(TextFont, TextHeight, colour, number(entry.cost.percent) + " %", x, y, 2);
            }
        }

        y += 14;
        paint.text(TextFont, TextHeight, Body, Engine::tr("State"), Left, y);
        std::string stateNote;
        size_t effectsUsed = 0;

        for (const AuraEffect &effect : entry.effects)
        {
            effectsUsed += effect.membersUsing > 0 ? 1 : 0;
        }

        const auto firstRival = [&entry]() -> std::optional<AuraRival>
        {
            for (const AuraEffect &effect : entry.effects)
            {
                if (effect.stronger)
                {
                    return effect.stronger;
                }
            }

            return std::nullopt;
        };

        switch (entry.state)
        {
            case AuraState::PartlyUsed:
                stateNote = effectsUsed < entry.effects.size()
                    ? Engine::tr("{used} of its {count} parts in use",
                        {{"used", effectsUsed}, {"count", entry.effects.size()}})
                    : Engine::tr("some members have stronger");
                break;
            case AuraState::AddsNothing:
                if (const std::optional<AuraRival> rival = firstRival())
                {
                    stateNote = rival->potion
                        ? Engine::tr("the members' own potions are stronger")
                        : Engine::tr("while {spell} is held", {{"spell", spellName(context, rival->spellId)}});
                }

                break;
            case AuraState::Blessing:
                stateNote = entry.templeBlessing ? Engine::tr("ends on the next map")
                                                 : Engine::tr("ends on another outdoor map");
                break;
            case AuraState::Active:
            case AuraState::Suspended:
                break;
        }

        const float noteWidth = stateNote.empty() ? 0 : paint.text(TextFont, SmallHeight, Muted, stateNote, Right, y + 1, 2);
        paint.pill(entry.state, Right - noteWidth - (noteWidth > 0 ? 3 : 0) - paint.pillWidth(entry.state) / 2,
            y - 0.5f);
        y += 15;

        if (entry.cost.health && pHolder != nullptr)
        {
            note(plainPossessive(holderName)
                    ? Engine::tr("Legendary 32: {holder}'s auras hold back hit points instead of mana.",
                        {{"holder", holderName}})
                    : Engine::tr("Legendary 32: {holder}' auras hold back hit points instead of mana.",
                        {{"holder", holderName}}),
                Muted);
        }

        const bool suspended = entry.state == AuraState::Suspended && pHolder != nullptr;

        if (suspended)
        {
            const std::string state = downWord(*pHolder);
            const std::string points = grouped(entry.cost.points);
            note(entry.cost.health
                    ? Engine::tr("{holder} is {state}: the aura is off, but its {points} HP stay reserved. It returns "
                                 "when {holder} recovers.",
                        {{"holder", holderName}, {"state", state}, {"points", points}})
                    : Engine::tr("{holder} is {state}: the aura is off, but its {points} SP stay reserved. It returns "
                                 "when {holder} recovers.",
                        {{"holder", holderName}, {"state", state}, {"points", points}}),
                Bad);
        }

        // Its effects.
        y += 3;
        paint.text(TitleFont, 12, Label, Engine::tr("Effect"), Left, y);
        y += 16;
        const float effectPitch = entry.effects.size() > 4 ? 11.2f : 13;
        const float effectHeight = entry.effects.size() > 4 ? 8.5f : TextHeight;

        if (suspended)
        {
            paint.text(TextFont, TextHeight, Bad, Engine::tr("Off"), Left, y);
            y += effectPitch;
        }
        else
        {
            for (const AuraEffect &effect : entry.effects)
            {
                // The value and what it is set against, right-aligned; the label gets what is left.
                std::string comparison;
                uint32_t comparisonColour = Warn;

                if (effect.membersUsing == 0 && effect.stronger)
                {
                    comparison = Dot
                        + Engine::tr("{source} {value} is stronger",
                            {{"source", rivalName(context, *pParty, *effect.stronger)},
                                {"value", valueText(effect.kind, effect.stronger->value)}});
                }
                else if (effect.membersUsing < effect.members)
                {
                    comparison = Dot
                        + Engine::tr("in use for {used} of {count}",
                            {{"used", effect.membersUsing}, {"count", effect.members}});
                }
                else if (entry.state == AuraState::PartlyUsed)
                {
                    comparison = " " + Engine::tr("in use");
                    comparisonColour = Good;
                }

                const std::string value = effectValueText(effect);
                const float valueWidth = paint.width(TextFont, effectHeight, value)
                    + paint.width(TextFont, effectHeight, comparison);
                paint.text(TextFont, effectHeight, Body,
                    paint.fitted(TextFont, effectHeight, effectLabel(effect), Right - Left - valueWidth - 6), Left, y);
                const float x = Right - paint.text(TextFont, effectHeight, comparisonColour, comparison, Right, y, 2);
                paint.text(TextFont, effectHeight, Ivory, value, x, y, 2);
                y += effectPitch;
            }
        }

        // What each member gets.
        y += 3;
        paint.text(TitleFont, 12, Label, Engine::tr("The party"), Left, y);
        y += 16;
        const float whoPitch = pParty->members().size() > 4 && entry.effects.size() > 4 ? 14 : 16;

        for (size_t memberIndex = 0; memberIndex < pParty->members().size() && memberIndex < entry.members.size();
             ++memberIndex)
        {
            const Character &member = pParty->members()[memberIndex];
            const AuraMemberBenefit &benefit = entry.members[memberIndex];
            const float faceHeight = whoPitch - 2;
            paint.face(member, paint.rect(Left + 1, y, faceHeight * 0.84f, faceHeight),
                !report->pools[memberIndex].conscious);
            const float textY = y + (faceHeight - TextHeight) / 2;
            paint.text(TextFont, 8.5f, Body, paint.fitted(TextFont, 8.5f, member.name, 50), Left + 17, textY + 0.5f);
            constexpr float ValueLeft = Left + 70;
            float x = ValueLeft;

            if (suspended)
            {
                x += paint.text(TextFont, 8.5f, Bad, Engine::tr("nothing"), x, textY + 0.5f);
                paint.text(TextFont, 7.5f, Muted, Dot + Engine::tr("until {holder} recovers", {{"holder", holderName}}),
                    x, textY + 1.2f);
            }
            else if (benefit.effects.empty())
            {
                x += paint.text(TextFont, 8.5f, Warn, Engine::tr("nothing"), x, textY + 0.5f);

                if (benefit.coveredBy)
                {
                    // A member with no effect lost the first one first: the rival names its strength.
                    const AuraValueKind kind = entry.effects.empty() ? AuraValueKind::Bonus : entry.effects[0].kind;
                    const std::string why = benefit.coveredBy->potion
                        ? Engine::tr("own potion ({value}) is stronger",
                            {{"value", valueText(kind, benefit.coveredBy->value)}})
                        : Engine::tr("{spell} gives {value}",
                            {{"spell", spellName(context, benefit.coveredBy->spellId)},
                                {"value", valueText(kind, benefit.coveredBy->value)}});
                    paint.text(TextFont, 7.5f, Muted, paint.fitted(TextFont, 7.5f, Dot + why, Right - x), x,
                        textY + 1.2f);
                }
            }
            else
            {
                std::string gets;

                for (const size_t index : benefit.effects)
                {
                    const AuraEffect &effect = entry.effects[index];
                    const std::string part = Engine::tr("{effect} {value}",
                        {{"effect", shortLabel(effectLabel(effect))}, {"value", effectValueText(effect)}});
                    gets += (gets.empty() ? "" : ", ") + part;
                }

                paint.text(TextFont, 8.5f, Ivory, paint.fitted(TextFont, 8.5f, gets, Right - ValueLeft), x,
                    textY + 0.5f);
            }

            paint.fill(paint.rect(Left, y + whoPitch - 1, Right - Left, 0.5f), WhoRule);
            y += whoPitch;
        }

        y += 4;

        if (pHolder != nullptr && !entry.cost.free && !suspended)
        {
            const bool plain = plainPossessive(holderName);
            const std::string points = grouped(entry.cost.points);
            note(entry.cost.health
                    ? (plain ? Engine::tr("Releasing it frees {points} of {holder}'s hit points.",
                                   {{"points", points}, {"holder", holderName}})
                             : Engine::tr("Releasing it frees {points} of {holder}' hit points.",
                                   {{"points", points}, {"holder", holderName}}))
                    : (plain ? Engine::tr("Releasing it frees {points} of {holder}'s spell points.",
                                   {{"points", points}, {"holder", holderName}})
                             : Engine::tr("Releasing it frees {points} of {holder}' spell points.",
                                   {{"points", points}, {"holder", holderName}})),
                Muted);
        }

        // Release and Move to.
        const Rect release = paint.rect(ReleaseLeft, ButtonTop, ReleaseWidth, ButtonHeight);
        const bool releaseHover = hovered.kind == JournalAuraTargetKind::Release;
        paint.button(release, Engine::tr("Release"), true, pHolder != nullptr, releaseHover, releaseHover && mouseDown);
        const Rect move = paint.rect(MoveLeft, ButtonTop, MoveWidth, ButtonHeight);
        const bool moveHover = hovered.kind == JournalAuraTargetKind::MoveMenu;
        paint.button(move, Engine::tr("Move to"), false, canMove(entry), moveHover || journal.auraMoveMenuOpen,
            moveHover && mouseDown, true);
        const std::string buttonNote = pHolder != nullptr ? Engine::tr("Release: free, no recovery")
            : entry.templeBlessing ? Engine::tr("Ends on the next map") : Engine::tr("Ends on another outdoor map");
        float noteY = ButtonTop + 0.5f;

        for (const std::string &line : paint.wrapped(TextFont, 7.5f, buttonNote, 62))
        {
            paint.text(TextFont, 7.5f, Muted, line, 452, noteY);
            noteY += 9.5f;
        }

        // The Move-to menu over the details.
        if (journal.auraMoveMenuOpen)
        {
            const Rect menu = menuRect(page, entry);
            const float top = menuTop(entry);
            paint.fill(menu, MenuFill);
            paint.frame(menu, Brass);
            paint.text(TitleFont, 10.5f, Label,
                paint.fitted(TitleFont, 10.5f,
                    Engine::tr("Move {spell} to", {{"spell", spellName(context, entry.spellId)}}), MenuWidth - 12),
                MenuLeft + 6.5f, top + 5);
            paint.fill(paint.rect(MenuLeft, top + 21, MenuWidth, 0.6f), MenuRule);

            for (size_t row = 0; row < entry.moveTo.size(); ++row)
            {
                const AuraMoveOption &option = entry.moveTo[row];
                const Character &member = pParty->members()[option.memberIndex];
                const float rowY = top + 24 + row * MenuRowHeight;
                const bool usable = option.knowsSpell && option.fits && option.conscious;

                if (usable && hovered.kind == JournalAuraTargetKind::MoveMember && hovered.index == option.memberIndex)
                {
                    paint.fill(paint.rect(MenuLeft + 1, rowY, MenuWidth - 2, MenuRowHeight), MenuHot);
                }

                paint.face(member, paint.rect(MenuLeft + 7, rowY + 2.5f, 13, 15.5f),
                    !option.knowsSpell || !option.conscious);
                paint.text(TextFont, 8.5f, option.knowsSpell ? Body : abgr(0x7f8578), member.name, MenuLeft + 26,
                    rowY + 5.5f);
                std::string what;
                uint32_t colour = Good;

                if (!option.knowsSpell)
                {
                    what = Engine::tr("does not know it");
                    colour = abgr(0x7f8578);
                }
                else
                {
                    what = option.cost.free ? Engine::tr("reserves nothing")
                        : (option.cost.flat ? "" : number(option.cost.percent) + " %" + Dot)
                            + pointsText(grouped(option.cost.points), option.cost.health);

                    if (!option.fits)
                    {
                        what += Dot + Engine::tr("{points} free", {{"points", grouped(option.freePoints)}});
                        colour = Bad;
                    }

                    if (!option.conscious)
                    {
                        what += Dot + downWord(member);
                        colour = Bad;
                    }
                }

                paint.text(TextFont, 8.5f, colour, what, MenuLeft + MenuWidth - 6.5f, rowY + 5.5f, 2);
            }

            const float footer = top + 24 + entry.moveTo.size() * MenuRowHeight;
            paint.fill(paint.rect(MenuLeft, footer + 1, MenuWidth, 0.6f), MenuRule);
            float footY = footer + 4;

            for (const std::string &line : paint.wrapped(TextFont, 7.5f,
                     Engine::tr("Moving casts it as the new holder: they must be ready and pay its recovery, and the "
                                "old holder's reservation is released. The strength follows the new holder's skill."),
                     MenuWidth - 13))
            {
                paint.text(TextFont, 7.5f, Muted, line, MenuLeft + 6.5f, footY);
                footY += 9.2f;
            }
        }
    }

    // The right rail: Release all, the Spellbook and the states' legend.
    const bool releaseAllHover = hovered.kind == JournalAuraTargetKind::ReleaseAll;
    paint.button(paint.rect(RailCenter - RailButtonWidth / 2, ReleaseAllTop, RailButtonWidth, RailButtonHeight),
        Engine::tr("Release all"), true, !report->auras.empty(), releaseAllHover, releaseAllHover && mouseDown);
    // One sentence on two lines.
    const std::string releaseHint = Engine::tr("Also R in the\nspellbook");
    const size_t hintBreak = releaseHint.find('\n');
    paint.text(TextFont, 7.5f, Muted, releaseHint.substr(0, hintBreak), RailCenter,
        ReleaseAllTop + RailButtonHeight + 4, 1);

    if (hintBreak != std::string::npos)
    {
        paint.text(TextFont, 7.5f, Muted, releaseHint.substr(hintBreak + 1), RailCenter,
            ReleaseAllTop + RailButtonHeight + 13.5f, 1);
    }
    const bool spellbookHover = hovered.kind == JournalAuraTargetKind::Spellbook;
    paint.button(paint.rect(RailCenter - RailButtonWidth / 2, SpellbookTop, RailButtonWidth, RailButtonHeight),
        Engine::tr("Spellbook"), false, true, spellbookHover, spellbookHover && mouseDown);
    float legendY = LegendTop;

    for (size_t state = 0; state < StateNames.size(); ++state)
    {
        const float pillWidth = paint.pillWidth(AuraState(state));
        paint.pill(AuraState(state), 532 + pillWidth / 2, legendY);
        legendY += 14;

        for (const std::string &line : paint.wrapped(TextFont, 7.5f, Engine::tr(LegendTexts[state]), 58))
        {
            paint.text(TextFont, 7.5f, Muted, line, 532, legendY);
            legendY += 9.5f;
        }

        legendY += 4;
    }
}
}
