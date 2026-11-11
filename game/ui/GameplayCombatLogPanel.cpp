#include "game/ui/GameplayCombatLogPanel.h"
#include "engine/Localization.h"
#include "engine/Utf8Text.h"

#include "game/gameplay/CombatLog.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/rules/maw/MawMonsterInspect.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiSkin.h"
#include "game/ui/GameplayUiRuntime.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <span>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
// The study's colours (index.html :root), as ABGR.
constexpr uint32_t PartyColor = 0xffc4e6f2u;
constexpr uint32_t MonsterColor = 0xff8aa9e6u;
constexpr uint32_t AmountColor = 0xff6be6ffu;
constexpr uint32_t CritColor = 0xff47b3ffu;
constexpr uint32_t KillColor = 0xff5a6affu;
constexpr uint32_t BodyColor = 0xffa7c7c8u;
constexpr uint32_t SpellColor = 0xffe6c39eu;
constexpr uint32_t StageColor = 0xffb0c4b9u;
constexpr uint32_t DownColor = 0xff8aa9e6u;
constexpr uint32_t UpColor = 0xff9ad9a8u;
constexpr uint32_t PanelColor = 0xdb0e0e07u;
constexpr uint32_t BorderColor = 0xff5f818cu;
constexpr uint32_t OpenLineColor = 0x1f7ab0c9u;
constexpr uint32_t RuleColor = 0xff6396acu;
constexpr uint32_t ChipColor = 0xcc16170du;
constexpr uint32_t ChipOnColor = 0xcc1a2a2bu;
constexpr uint32_t ChipBorderColor = 0xff49645du;
constexpr uint32_t ChipOnBorderColor = 0xff80bbd6u;
constexpr uint32_t ChipTextOnColor = 0xfface4ffu;
constexpr uint32_t TrackColor = 0xff29382au;
constexpr uint32_t ThumbColor = 0xff6a8dacu;
// The narrowest the panel gets beside the party frame, in layout units.
constexpr float MinimumWidth = 150;

struct Segment
{
    std::string text;
    uint32_t color = BodyColor;
};

struct TextStyle
{
    const GameplayHudFontData *pFont = nullptr;
    float scale = 1;
    float lineHeight = 0;
};

TextStyle textStyle(GameplayScreenRuntime &context, const char *pLayoutId, float areaScale)
{
    TextStyle style;
    const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(pLayoutId);

    if (pLayout == nullptr)
    {
        return style;
    }

    style.pFont = GameplayHudCommon::findHudFont(context.gameplayUiRuntime().hudFontHandles(), pLayout->fontName);

    if (style.pFont == nullptr)
    {
        return style;
    }

    style.scale = areaScale * std::max(0.1f, pLayout->textScale);

    if (!style.pFont->smooth && style.scale >= 1.0f)
    {
        style.scale = GameplayHudCommon::snappedHudFontScale(style.scale);
    }

    style.lineHeight = std::round(float(style.pFont->fontHeight) * style.scale);
    return style;
}

float textWidth(const TextStyle &style, const std::string &text)
{
    return GameplayHudCommon::measureHudTextWidth(*style.pFont, text) * style.scale;
}

// Appends a text's shadow and main quads at (x, y); returns where the next text starts.
float appendText(std::vector<GameplayHudBatchQuad> &quads, const TextStyle &style, const std::string &text, float x,
    float y, uint32_t color)
{
    const auto collect = [&quads](bgfx::TextureHandle texture, float quadX, float quadY, float quadWidth,
                             float quadHeight, float u0, float v0, float u1, float v1, TextureFilterProfile,
                             uint32_t tint)
    {
        if (quadWidth <= 0 || quadHeight <= 0)
        {
            return;
        }

        GameplayHudBatchQuad quad;
        quad.textureHandle = texture;
        quad.x = quadX;
        quad.y = quadY;
        quad.width = quadWidth;
        quad.height = quadHeight;
        quad.u0 = u0;
        quad.v0 = v0;
        quad.u1 = u1;
        quad.v1 = v1;
        quad.tintAbgr = tint;
        quads.push_back(quad);
    };
    const float roundedX = std::round(x);
    const float roundedY = std::round(y);
    GameplayHudCommon::renderHudFontLayer(
        *style.pFont, GameplayHudFontLayer(style.pFont->shadowTextureHandle), text, roundedX, roundedY, style.scale,
        collect);
    GameplayHudCommon::renderHudFontLayer(
        *style.pFont, GameplayHudCommon::hudFontMainLayer(*style.pFont, color), text, roundedX, roundedY, style.scale,
        collect);
    return x + textWidth(style, text);
}

// Appends segments on one line up to maxRight, the last one cut with "..." when they do not fit.
void appendLine(std::vector<GameplayHudBatchQuad> &quads, const TextStyle &style, const std::vector<Segment> &segments,
    float x, float y, float maxRight)
{
    for (const Segment &segment : segments)
    {
        if (x + textWidth(style, segment.text) <= maxRight)
        {
            x = appendText(quads, style, segment.text, x, y, segment.color);
            continue;
        }

        const float room = std::max(0.0f, maxRight - x - textWidth(style, "..."));
        const std::string cut = GameplayHudCommon::clampHudTextToWidth(*style.pFont, segment.text, room / style.scale);
        appendText(quads, style, cut + "...", x, y, segment.color);
        return;
    }
}

// A damage stage's name for the player; the rules name their stages for code (CombatRules, MawCombatRules).
std::string stageName(const std::string &stage)
{
    static const std::unordered_map<std::string, std::string_view> Names = {
        {"resistance", Engine::trNoop("Resistance")},
        {"missile-shield", Engine::trNoop("Missile shield")},
        {"physical-taken", Engine::trNoop("Physical damage taken")},
        {"mitigation", Engine::trNoop("Armour and resistances")},
        {"resistance-and-armor", Engine::trNoop("Resistances and armour")},
        {"damage-recompute", Engine::trNoop("Monster damage")},
        {"damage-taken-stacks", Engine::trNoop("Spear stacks")},
        {"boss-affixes", Engine::trNoop("Boss affix")},
        {"map-affixes", Engine::trNoop("Dimension affix")},
        {"map-energy", Engine::trNoop("Energy shield")},
        {"legendary-blows", Engine::trNoop("Legendary")},
        {"legendary-defense", Engine::trNoop("Legendary defence")},
        {"mist-form", Engine::trNoop("Mist Form")},
        {"solo-cover", Engine::trNoop("Cover")},
        {"disease", Engine::trNoop("Disease")},
        {"monster-vs-monster", Engine::trNoop("Monster against monster")},
    };
    const auto found = Names.find(stage);

    if (found != Names.end())
    {
        return Engine::localize(found->second, "combat-log");
    }

    std::string name = stage;
    std::replace(name.begin(), name.end(), '-', ' ');

    if (!name.empty())
    {
        name[0] = char(std::toupper(static_cast<unsigned char>(name[0])));
    }

    return name;
}

// A part of a line, for its template's {name}.
struct SegmentArgument
{
    std::string_view name;
    std::string text;
    uint32_t color = BodyColor;
};

// The segments of a translated line template: each {name} of an argument in its colour, the words between in
// `wordColor`, so a language can reorder the parts.
std::vector<Segment> templateSegments(std::string_view pattern, std::initializer_list<SegmentArgument> arguments,
    uint32_t wordColor)
{
    std::vector<Segment> segments;
    std::string words;
    size_t position = 0;

    while (position < pattern.size())
    {
        const SegmentArgument *pArgument = nullptr;

        if (pattern[position] == '{')
        {
            const size_t close = pattern.find('}', position);

            if (close != std::string_view::npos)
            {
                const std::string_view name = pattern.substr(position + 1, close - position - 1);

                for (const SegmentArgument &argument : arguments)
                {
                    if (argument.name == name)
                    {
                        pArgument = &argument;
                        break;
                    }
                }

                if (pArgument != nullptr)
                {
                    if (!words.empty())
                    {
                        segments.push_back({words, wordColor});
                        words.clear();
                    }

                    segments.push_back({pArgument->text, pArgument->color});
                    position = close + 1;
                    continue;
                }
            }
        }

        words += pattern[position];
        ++position;
    }

    if (!words.empty())
    {
        segments.push_back({words, wordColor});
    }

    return segments;
}

// A hit as a sentence, "Gerrard shoots Goblin 58!": the party's names ivory, monsters coral, the amount yellow with
// an orange "!" for a critical hit. A killing blow says "kills" in red; a cast names its spell ("Lys Fire Bolt on
// Goblin 96", "Lys Fireball kills 3 monsters 512"). The names arrive as the player reads them. A loot line is
// always this; a hit's row is the compact HitRow, and its sentence heads the details a click opens.
std::vector<Segment> hitSegments(const CombatLogEntry &entry)
{
    // "Filtered: Uncommon Longsword -> 312 gold", the rarity in its colour.
    if (entry.kind == CombatLogKind::Loot)
    {
        const std::string item = Engine::localize(entry.target);
        const std::string gold = Engine::tr("{gold} gold", {{"gold", entry.amount}});

        if (entry.rarity.empty())
        {
            return templateSegments(Engine::tr("Filtered: {item} -> {gold}"),
                {{"item", item, PartyColor}, {"gold", gold, AmountColor}}, BodyColor);
        }

        return templateSegments(Engine::tr("Filtered: {rarity} {item} -> {gold}"),
            {{"rarity", Engine::tr(entry.rarity), entry.rarityColor != 0 ? entry.rarityColor : BodyColor},
                {"item", item, PartyColor}, {"gold", gold, AmountColor}},
            BodyColor);
    }

    const bool dealt = entry.kind == CombatLogKind::Dealt;
    const SegmentArgument attacker{"attacker", entry.attacker, dealt ? PartyColor : MonsterColor};
    const SegmentArgument target{"target", entry.target, dealt ? MonsterColor : PartyColor};
    const SegmentArgument amount{"amount", std::to_string(entry.amount), AmountColor};
    std::vector<Segment> segments;

    if (!entry.spell.empty())
    {
        const SegmentArgument spell{"spell", entry.spell, SpellColor};
        segments = entry.killed
            ? templateSegments(Engine::tr("{attacker} {spell} kills {target} {amount}"),
                {attacker, spell, target, amount}, KillColor)
            : templateSegments(Engine::tr("{attacker} {spell} on {target} {amount}"),
                {attacker, spell, target, amount}, BodyColor);
    }
    else if (entry.killed)
    {
        segments = templateSegments(Engine::tr("{attacker} kills {target} {amount}"), {attacker, target, amount},
            KillColor);
    }
    else if (entry.verb == "shoots")
    {
        segments = templateSegments(Engine::tr("{attacker} shoots {target} {amount}"), {attacker, target, amount},
            BodyColor);
    }
    else
    {
        // "hits": the only other verb a line without a spell has.
        segments = templateSegments(Engine::tr("{attacker} hits {target} {amount}"), {attacker, target, amount},
            BodyColor);
    }

    if (entry.critical)
    {
        segments.push_back({"!", CritColor});
    }

    return segments;
}

// The line glyphs (level_generation/ui/maw_combat_log_20261024/make_glyphs.py), white, tinted when drawn.
constexpr const char *MeleeGlyph = "combat_log_melee";
constexpr const char *ShootGlyph = "combat_log_shoot";
constexpr const char *KillGlyph = "combat_log_kill";

// A hit's one-line row, for a corner about 26 characters wide: who, how, whom, and the amount right-aligned so it is
// never cut ("Cauri <bow> Skeleton Lord    58!", "Lys Fireball 3 monsters  <skull>512"). How is a sword or bow glyph
// in place of the verb, or the spell's name in its colour; a killing blow puts a red skull before the amount.
struct HitRow
{
    std::string attacker;
    uint32_t attackerColor = PartyColor;
    const char *pGlyph = nullptr;
    std::string spell;
    std::string target;
    uint32_t targetColor = MonsterColor;
    // The amount, shortened from 10000 as MAW's panels do ("99.5K"): the digits, then the K, M or B in yellow, orange
    // or red.
    std::string amount;
    std::string amountSuffix;
    uint32_t suffixColor = AmountColor;
    bool critical = false;
    bool killed = false;
};

HitRow hitRow(const CombatLogEntry &entry)
{
    const bool dealt = entry.kind == CombatLogKind::Dealt;
    HitRow row;
    row.attacker = entry.attacker;
    row.attackerColor = dealt ? PartyColor : MonsterColor;
    row.spell = entry.spell;
    row.pGlyph = !entry.spell.empty() ? nullptr : entry.verb == "shoots" ? ShootGlyph : MeleeGlyph;
    row.target = entry.target;
    row.targetColor = dealt ? MonsterColor : PartyColor;
    row.amount = std::to_string(entry.amount);

    if (entry.amount >= 10000)
    {
        row.amount = mawShortNumber(entry.amount, false);
        row.amountSuffix = row.amount.substr(row.amount.size() - 1);
        row.amount.pop_back();
        row.suffixColor = row.amountSuffix == "B" ? KillColor : row.amountSuffix == "M" ? CritColor : AmountColor;
    }
    row.critical = entry.critical;
    row.killed = entry.killed;
    return row;
}

// A name's shorter forms, longest first: "Dark Elf Priestess", "D.E. Priestess", "Priestess". A count ("3 monsters")
// and a one-word name have only themselves.
std::vector<std::string> shortForms(const std::string &name)
{
    std::vector<std::string> words;
    size_t begin = 0;

    while (begin < name.size())
    {
        const size_t space = name.find(' ', begin);
        const size_t end = space == std::string::npos ? name.size() : space;

        if (end > begin)
        {
            words.push_back(name.substr(begin, end - begin));
        }

        begin = end + 1;
    }

    if (words.size() < 2 || std::isdigit(static_cast<unsigned char>(words.front().front())))
    {
        return {name};
    }

    std::string initials;

    for (size_t index = 0; index + 1 < words.size(); ++index)
    {
        const size_t letter = std::max<size_t>(1, Engine::Utf8::decode(words[index], 0).size);
        initials += words[index].substr(0, letter) + ".";
    }

    return {name, initials + " " + words.back(), words.back()};
}

// Shortens the row's names until its left part fits `available`: each step takes the widest field that has a
// shorter form to its next one. When none is left, the widest field is cut with "...".
void fitHitRow(const TextStyle &style, HitRow &row, float glyphWidth, float available)
{
    std::array<std::string *, 3> fields = {&row.attacker, &row.spell, &row.target};
    std::array<std::vector<std::string>, 3> forms;
    std::array<size_t, 3> chosen = {0, 0, 0};

    for (size_t index = 0; index < fields.size(); ++index)
    {
        forms[index] = shortForms(*fields[index]);
    }

    const float space = textWidth(style, " ");
    const auto leftWidth = [&]()
    {
        float width = 0;
        int parts = 0;

        for (const std::string *pField : fields)
        {
            if (!pField->empty())
            {
                width += textWidth(style, *pField);
                ++parts;
            }
        }

        if (row.pGlyph != nullptr)
        {
            width += glyphWidth;
            ++parts;
        }

        return width + float(std::max(0, parts - 1)) * space;
    };

    float width = leftWidth();

    while (width > available)
    {
        size_t widest = fields.size();
        float widestWidth = 0;

        for (size_t index = 0; index < fields.size(); ++index)
        {
            const float fieldWidth = textWidth(style, *fields[index]);

            if (chosen[index] + 1 < forms[index].size() && fieldWidth > widestWidth)
            {
                widest = index;
                widestWidth = fieldWidth;
            }
        }

        if (widest == fields.size())
        {
            break;
        }

        *fields[widest] = forms[widest][++chosen[widest]];
        width = leftWidth();
    }

    if (width <= available)
    {
        return;
    }

    std::string *pWidest = fields[0];

    for (std::string *pField : fields)
    {
        if (textWidth(style, *pField) > textWidth(style, *pWidest))
        {
            pWidest = pField;
        }
    }

    const float room = std::max(0.0f, textWidth(style, *pWidest) - (width - available) - textWidth(style, "..."));
    *pWidest = GameplayHudCommon::clampHudTextToWidth(*style.pFont, *pWidest, room / style.scale) + "...";
}

// "Rolled 612 -> Monster resistance -92 -> Dimension affix -8 -> 512".
std::vector<Segment> stageSegments(const CombatLogEntry &entry)
{
    if (entry.stages.empty())
    {
        return {{Engine::tr("No damage steps for this line."), StageColor}};
    }

    std::vector<Segment> segments = {{Engine::tr("Rolled") + " ", StageColor},
        {std::to_string(entry.stages.front().before), AmountColor}};

    for (const CombatLogStage &stage : entry.stages)
    {
        const int change = stage.after - stage.before;

        if (change != 0)
        {
            segments.push_back({" -> " + stageName(stage.name) + " ", StageColor});
            segments.push_back({(change > 0 ? "+" : "-") + std::to_string(std::abs(change)),
                change > 0 ? UpColor : DownColor});
        }
    }

    segments.push_back({" -> ", StageColor});
    segments.push_back({std::to_string(entry.stages.back().after), AmountColor});
    return segments;
}

// Breaks segments into lines of at most `width`, at spaces.
std::vector<std::vector<Segment>> wrapSegments(const TextStyle &style, const std::vector<Segment> &segments,
    float width)
{
    std::vector<std::vector<Segment>> lines(1);
    float x = 0;

    for (const Segment &segment : segments)
    {
        size_t begin = 0;

        while (begin < segment.text.size())
        {
            const size_t space = segment.text.find(' ', begin);
            const size_t end = space == std::string::npos ? segment.text.size() : space + 1;
            const std::string word = segment.text.substr(begin, end - begin);
            const float wordWidth = textWidth(style, word);

            if (x + wordWidth > width && x > 0)
            {
                lines.emplace_back();
                x = 0;
            }

            lines.back().push_back({word, segment.color});
            x += wordWidth;
            begin = end;
        }
    }

    return lines;
}
}

bool GameplayCombatLogPanel::open() const
{
    return m_open;
}

void GameplayCombatLogPanel::toggle()
{
    m_open = !m_open;
}

void GameplayCombatLogPanel::scroll(int lines, const CombatLog &log)
{
    const size_t count = size_t(std::count_if(log.entries().begin(), log.entries().end(),
        [this](const CombatLogEntry &entry) { return shows(entry); }));
    const long scrolled = long(m_scroll) + lines;
    m_scroll = size_t(std::clamp(scrolled, 0L, long(count > 0 ? count - 1 : 0)));
}

void GameplayCombatLogPanel::toggleEntry(uint32_t entryId)
{
    m_openEntry = m_openEntry == entryId ? 0 : entryId;
}

void GameplayCombatLogPanel::setFilter(CombatLogFilter filter)
{
    m_filter = filter;
    m_scroll = 0;
}

bool GameplayCombatLogPanel::shows(const CombatLogEntry &entry) const
{
    // Loot lines show under All only.
    return m_filter == CombatLogFilter::All
        || (m_filter == CombatLogFilter::Dealt && entry.kind == CombatLogKind::Dealt)
        || (m_filter == CombatLogFilter::Taken && entry.kind == CombatLogKind::Taken);
}

void GameplayCombatLogPanel::render(GameplayScreenRuntime &context, int width, int height)
{
    m_drawn = false;

    if (!m_open || !context.combatLogShown())
    {
        return;
    }

    const std::optional<GameplayResolvedHudLayoutElement> panel =
        context.resolveHudLayoutElement("CombatLogPanel", width, height, 0, 0);

    if (!panel)
    {
        return;
    }

    // The corner beside the party frame: narrowed to end before the frame's left ornament, or lifted above the
    // frame when that leaves too little room (a narrow screen or a full party).
    GameplayResolvedHudLayoutElement placed = *panel;
    const std::optional<GameplayResolvedHudLayoutElement> basebar = context.settingsSnapshot().partyFrame
        ? context.resolveHudLayoutElement("OutdoorGameplayBasebar", width, height, 0, 0)
        : std::nullopt;

    if (basebar && placed.x + placed.width > GameplayUiSkin::partyBasebarLeft(context, *basebar)
        && placed.y + placed.height > basebar->y)
    {
        const float room = GameplayUiSkin::partyBasebarLeft(context, *basebar) - 4 * placed.scale - placed.x;

        if (room >= MinimumWidth * placed.scale)
        {
            placed.width = std::floor(room);
        }
        else
        {
            placed.y = basebar->y - 4 * placed.scale - placed.height;
        }
    }

    m_drawn = true;
    const CombatLog &log = context.combatLog();
    const CacheKey key{log.revision(), m_scroll, m_openEntry, m_filter, placed.x, placed.y, placed.width,
        placed.height, placed.scale};

    if (m_cacheKey != key)
    {
        m_placedPanel = placed;
        layOut(context, log);
        m_cacheKey = key;
    }

    if (!m_fillQuads.empty())
    {
        context.gameplayUiRuntime().submitHudQuadBatch(
            std::span<const GameplayHudBatchQuad>(m_fillQuads.data(), m_fillQuads.size()));
    }

    if (!m_textQuads.empty())
    {
        context.gameplayUiRuntime().submitHudQuadBatch(
            std::span<const GameplayHudBatchQuad>(m_textQuads.data(), m_textQuads.size()), m_textFilter);
    }

    if (!m_glyphQuads.empty())
    {
        context.gameplayUiRuntime().submitHudQuadBatch(
            std::span<const GameplayHudBatchQuad>(m_glyphQuads.data(), m_glyphQuads.size()));
    }
}

void GameplayCombatLogPanel::appendGlyph(GameplayScreenRuntime &context, const char *pName, float x, float y,
    float size, uint32_t tint)
{
    const std::optional<GameplayHudTextureHandle> handle =
        context.gameplayUiRuntime().ensureHudTextureLoaded(pName);

    if (!handle)
    {
        return;
    }

    GameplayHudBatchQuad quad;
    quad.textureHandle = handle->textureHandle;
    quad.x = std::round(x);
    quad.y = std::round(y);
    quad.width = size;
    quad.height = size;
    quad.tintAbgr = tint;
    m_glyphQuads.push_back(quad);
}

void GameplayCombatLogPanel::layOut(GameplayScreenRuntime &context, const CombatLog &log)
{
    m_textQuads.clear();
    m_glyphQuads.clear();
    m_fills.clear();
    m_fillQuads.clear();
    m_entryRects.clear();
    m_filterRects.clear();
    const float scale = m_placedPanel.scale;
    const TextStyle titleStyle = textStyle(context, "CombatLogTitle", scale);
    const TextStyle chipStyle = textStyle(context, "CombatLogChipText", scale);
    const TextStyle lineStyle = textStyle(context, "CombatLogText", scale);
    const TextStyle stageStyle = textStyle(context, "CombatLogStageText", scale);

    if (titleStyle.pFont == nullptr || chipStyle.pFont == nullptr || lineStyle.pFont == nullptr
        || stageStyle.pFont == nullptr)
    {
        return;
    }

    // The panel loses the part of a line its height leaves over at the top, so no gap opens under the header.
    const float headerHeight = 17 * scale;
    const float lineGap = std::round(scale * 1.5f);
    const float linePitch = lineStyle.lineHeight + lineGap;
    const float listHeight = m_placedPanel.height - headerHeight - 6 * scale;
    const float leftover = listHeight - std::max(1.0f, std::floor(listHeight / linePitch)) * linePitch;
    m_panel = m_placedPanel;
    m_panel.y += std::max(0.0f, leftover);
    m_panel.height -= std::max(0.0f, leftover);
    const GameplayResolvedHudLayoutElement &panel = m_panel;

    // The study's panel: dark glass with a thin brass border.
    const float border = std::max(1.0f, std::round(scale * 0.6f));
    m_fills.push_back({panel, PanelColor});
    m_fills.push_back({{panel.x, panel.y, panel.width, border, scale}, BorderColor});
    m_fills.push_back({{panel.x, panel.y + panel.height - border, panel.width, border, scale}, BorderColor});
    m_fills.push_back({{panel.x, panel.y, border, panel.height, scale}, BorderColor});
    m_fills.push_back({{panel.x + panel.width - border, panel.y, border, panel.height, scale}, BorderColor});

    // The header row (title left, filter chips right), the lines under it and the scrollbar along their right.
    const GameplayResolvedHudLayoutElement area{panel.x + 6 * scale, panel.y + headerHeight + 2 * scale,
        panel.width - 17 * scale, panel.height - headerHeight - 6 * scale, scale};
    const GameplayResolvedHudLayoutElement scrollbar{panel.x + panel.width - 9 * scale, area.y, 6 * scale,
        area.height, scale};
    m_textFilter = lineStyle.pFont->smooth ? TextureFilterProfile::SmoothText : TextureFilterProfile::Text;
    appendText(m_textQuads, titleStyle, Engine::tr("Combat log"), panel.x + 6 * scale,
        panel.y + 2 * scale + (headerHeight - 2 * scale - titleStyle.lineHeight) / 2, 0xffa8d1e6u);

    // The filter chips, laid out leftwards from the panel's right edge.
    const std::array<std::pair<std::string, CombatLogFilter>, 3> chips = {{
        {Engine::tr("Taken"), CombatLogFilter::Taken},
        {Engine::tr("Dealt"), CombatLogFilter::Dealt},
        {Engine::tr("All"), CombatLogFilter::All},
    }};
    const float hairline = std::max(1.0f, std::round(scale * 0.5f));
    float chipRight = panel.x + panel.width - 5 * scale;

    for (const auto &[label, filter] : chips)
    {
        const float chipWidth = std::round(textWidth(chipStyle, label) + 8 * scale);
        const GameplayResolvedHudLayoutElement chip{chipRight - chipWidth, panel.y + 3 * scale, chipWidth,
            13 * scale, scale};
        chipRight = chip.x - 2 * scale;
        const bool on = filter == m_filter;
        const uint32_t edge = on ? ChipOnBorderColor : ChipBorderColor;
        m_fills.push_back({chip, on ? ChipOnColor : ChipColor});
        m_fills.push_back({{chip.x, chip.y, chip.width, hairline, scale}, edge});
        m_fills.push_back({{chip.x, chip.y + chip.height - hairline, chip.width, hairline, scale}, edge});
        m_fills.push_back({{chip.x, chip.y, hairline, chip.height, scale}, edge});
        m_fills.push_back({{chip.x + chip.width - hairline, chip.y, hairline, chip.height, scale}, edge});
        appendText(m_textQuads, chipStyle, label, chip.x + (chip.width - textWidth(chipStyle, label)) / 2,
            chip.y + (chip.height - chipStyle.lineHeight) / 2, on ? ChipTextOnColor : BodyColor);
        m_filterRects.push_back({chip, filter});
    }

    // The hits that show, oldest first, and how far back the view is scrolled.
    std::vector<const CombatLogEntry *> shown;

    for (const CombatLogEntry &entry : log.entries())
    {
        if (shows(entry))
        {
            shown.push_back(&entry);
        }
    }

    const size_t skipped = std::min(m_scroll, shown.size());
    const float stageIndent = 12 * scale;
    const float stageWidth = area.width - stageIndent - 6 * scale;

    // A block per hit, newest last: its row and, when open, its whole sentence and wrapped damage steps under it.
    struct Block
    {
        const CombatLogEntry *pEntry = nullptr;
        // A hit is one compact row; a loot line wraps so its gold shows.
        std::optional<HitRow> row;
        std::vector<std::vector<Segment>> lines;
        std::vector<std::vector<Segment>> stageLines;
        float height = 0;
    };

    const float rowLeft = area.x + 2 * scale;
    const float rowRight = area.x + area.width - 2 * scale;
    const float glyphSize = std::round(lineStyle.lineHeight * 0.95f);
    const float space = textWidth(lineStyle, " ");
    std::vector<Block> blocks;
    float used = 0;
    size_t shownCount = 0;

    for (size_t index = shown.size() - skipped; index-- > 0;)
    {
        Block block;
        block.pEntry = shown[index];
        const bool loot = block.pEntry->kind == CombatLogKind::Loot;

        if (loot)
        {
            block.lines = wrapSegments(lineStyle, hitSegments(*block.pEntry), area.width - 4 * scale);
        }
        else
        {
            HitRow row = hitRow(*block.pEntry);
            const float amountWidth = textWidth(lineStyle, row.amount + row.amountSuffix)
                + (row.critical ? textWidth(lineStyle, "!") : 0)
                + (row.killed ? glyphSize + 1 * scale : 0);
            fitHitRow(lineStyle, row, glyphSize, rowRight - rowLeft - amountWidth - 2 * space);
            block.row = std::move(row);
            block.lines.resize(1);
        }

        block.height = float(block.lines.size()) * (lineStyle.lineHeight + lineGap);

        // A loot line has no damage steps to open. A hit opens its whole sentence, then its steps.
        if (block.pEntry->id == m_openEntry && !loot)
        {
            block.stageLines = wrapSegments(stageStyle, hitSegments(*block.pEntry), stageWidth);
            std::vector<std::vector<Segment>> steps = wrapSegments(stageStyle, stageSegments(*block.pEntry),
                stageWidth);
            block.stageLines.insert(block.stageLines.end(), steps.begin(), steps.end());
            block.height += float(block.stageLines.size()) * (stageStyle.lineHeight + lineGap) + 2 * lineGap;
        }

        if (used + block.height > area.height && !blocks.empty())
        {
            break;
        }

        used += block.height;
        ++shownCount;
        blocks.insert(blocks.begin(), std::move(block));
    }

    // Laid out from the bottom up, so the newest hit sits on the panel's last line.
    float y = area.y + area.height - used;

    for (const Block &block : blocks)
    {
        const CombatLogEntry &entry = *block.pEntry;
        const GameplayResolvedHudLayoutElement row{area.x, y, area.width, block.height, scale};

        if (entry.id == m_openEntry && entry.kind != CombatLogKind::Loot)
        {
            m_fills.push_back({row, OpenLineColor});
        }

        if (block.row)
        {
            const HitRow &row = *block.row;
            const float glyphY = y + std::round((lineStyle.lineHeight - glyphSize) / 2);
            float x = appendText(m_textQuads, lineStyle, row.attacker, rowLeft, y, row.attackerColor) + space;

            if (row.pGlyph != nullptr)
            {
                appendGlyph(context, row.pGlyph, x, glyphY, glyphSize, BodyColor);
                x += glyphSize + space;
            }

            if (!row.spell.empty())
            {
                x = appendText(m_textQuads, lineStyle, row.spell, x, y, SpellColor) + space;
            }

            appendText(m_textQuads, lineStyle, row.target, x, y, row.targetColor);

            // The amount right-aligned: a kill's skull, the number, a critical hit's "!".
            float right = rowRight;

            if (row.critical)
            {
                right -= textWidth(lineStyle, "!");
                appendText(m_textQuads, lineStyle, "!", right, y, CritColor);
            }

            if (!row.amountSuffix.empty())
            {
                right -= textWidth(lineStyle, row.amountSuffix);
                appendText(m_textQuads, lineStyle, row.amountSuffix, right, y, row.suffixColor);
            }

            right -= textWidth(lineStyle, row.amount);
            appendText(m_textQuads, lineStyle, row.amount, right, y, AmountColor);

            if (row.killed)
            {
                appendGlyph(context, KillGlyph, right - 1 * scale - glyphSize, glyphY, glyphSize, KillColor);
            }
        }
        else
        {
            for (size_t line = 0; line < block.lines.size(); ++line)
            {
                appendLine(m_textQuads, lineStyle, block.lines[line], rowLeft,
                    y + float(line) * (lineStyle.lineHeight + lineGap), rowRight);
            }
        }

        m_entryRects.push_back({row, entry.id});
        float stageY = y + lineStyle.lineHeight + 2 * lineGap;

        if (!block.stageLines.empty())
        {
            const float ruleX = area.x + stageIndent - 6 * scale;
            m_fills.push_back({{ruleX, stageY, std::max(1.0f, std::round(scale)),
                float(block.stageLines.size()) * (stageStyle.lineHeight + lineGap), scale}, RuleColor});
        }

        for (const std::vector<Segment> &stageLine : block.stageLines)
        {
            appendLine(m_textQuads, stageStyle, stageLine, area.x + stageIndent, stageY,
                area.x + area.width - 2 * scale);
            stageY += stageStyle.lineHeight + lineGap;
        }

        y += block.height;
    }

    // The scrollbar: the shown share of the hits, its place by how far back the view is.
    m_fills.push_back({{scrollbar.x + 2 * scale, scrollbar.y, std::max(1.0f, std::round(1.5f * scale)),
        scrollbar.height, scale}, TrackColor});

    if (!shown.empty())
    {
        const float share = std::clamp(float(shownCount) / float(shown.size()), 0.08f, 1.0f);
        const float thumbHeight = scrollbar.height * share;
        const float fromBottom = float(skipped) / float(shown.size()) * scrollbar.height;
        const float thumbY = std::max(scrollbar.y,
            scrollbar.y + scrollbar.height - fromBottom - thumbHeight);
        m_fills.push_back({{scrollbar.x + scale, thumbY, std::max(2.0f, std::round(3.5f * scale)), thumbHeight,
            scale}, ThumbColor});
    }

    // The fills in palette colours (one texture, so one draw), and the text regrouped into few draws: every shadow
    // first (they sit under all glyphs), then the glyphs by texture and colour, which never overlap one another.
    m_fillQuads.clear();
    GameplayUiRuntime &ui = context.gameplayUiRuntime();

    for (const Fill &part : m_fills)
    {
        const std::optional<GameplayHudPaletteColor> color = ui.ensureHudPaletteColor(part.colorAbgr);

        if (color && part.rect.width > 0 && part.rect.height > 0)
        {
            m_fillQuads.push_back(
                gameplayHudPaletteQuad(*color, part.rect.x, part.rect.y, part.rect.width, part.rect.height));
        }
    }

    const std::array<uint16_t, 4> shadowTextures = {titleStyle.pFont->shadowTextureHandle.idx,
        chipStyle.pFont->shadowTextureHandle.idx, lineStyle.pFont->shadowTextureHandle.idx,
        stageStyle.pFont->shadowTextureHandle.idx};
    const auto isShadow = [&shadowTextures](const GameplayHudBatchQuad &quad)
    {
        return std::find(shadowTextures.begin(), shadowTextures.end(), quad.textureHandle.idx)
            != shadowTextures.end();
    };
    std::stable_sort(m_textQuads.begin(), m_textQuads.end(),
        [&isShadow](const GameplayHudBatchQuad &left, const GameplayHudBatchQuad &right)
        {
            const bool leftShadow = isShadow(left);
            const bool rightShadow = isShadow(right);

            if (leftShadow != rightShadow)
            {
                return leftShadow;
            }

            if (left.textureHandle.idx != right.textureHandle.idx)
            {
                return left.textureHandle.idx < right.textureHandle.idx;
            }

            return left.tintAbgr < right.tintAbgr;
        });
}

bool GameplayCombatLogPanel::contains(float x, float y) const
{
    return m_drawn && GameplayHudCommon::isPointerInsideResolvedElement(m_panel, x, y);
}

std::optional<uint32_t> GameplayCombatLogPanel::entryAt(float x, float y) const
{
    if (!m_drawn)
    {
        return std::nullopt;
    }

    for (const auto &[rect, entryId] : m_entryRects)
    {
        if (GameplayHudCommon::isPointerInsideResolvedElement(rect, x, y))
        {
            return entryId;
        }
    }

    return std::nullopt;
}

std::optional<CombatLogFilter> GameplayCombatLogPanel::filterAt(float x, float y) const
{
    if (!m_drawn)
    {
        return std::nullopt;
    }

    for (const auto &[rect, filter] : m_filterRects)
    {
        if (GameplayHudCommon::isPointerInsideResolvedElement(rect, x, y))
        {
            return filter;
        }
    }

    return std::nullopt;
}
}
