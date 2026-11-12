#include "game/ui/GameplayJournalProgress.h"

#include "engine/Localization.h"
#include "engine/Utf8Text.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/RulesetProgress.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiRuntime.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <memory>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
// The approved study's colours (maw_loot_progress_20261025 index.html), as ABGR.
constexpr uint32_t abgr(uint32_t rgb, uint32_t alpha = 0xff)
{
    return alpha << 24 | (rgb & 0xffu) << 16 | (rgb & 0xff00u) | (rgb >> 16 & 0xffu);
}

constexpr uint32_t Ivory = abgr(0xefe0bc);
constexpr uint32_t Label = abgr(0xe6d1a8);
constexpr uint32_t Body = abgr(0xc8c7a7);
constexpr uint32_t Muted = abgr(0x9fa594);
constexpr uint32_t Gold = abgr(0xe3c185);
constexpr uint32_t Amount = abgr(0xffe66b);
constexpr uint32_t Good = abgr(0x8fe08a);
constexpr uint32_t Warn = abgr(0xf2c35a);
constexpr uint32_t Bad = abgr(0xe66a5a);
constexpr uint32_t PanelFill = abgr(0x0d1716, 0xcc);
constexpr uint32_t PanelBorder = abgr(0x5d6449);
constexpr uint32_t SelectedFill = abgr(0x2b2a1a, 0x99);
constexpr uint32_t SelectedBorder = abgr(0xd6bb80);
constexpr uint32_t RowHighlight = abgr(0xc9b07a, 0x1f);
constexpr uint32_t RowRule = abgr(0xffffff, 0x0d);
constexpr uint32_t DetailFill = abgr(0xbbab61, 0x12);
constexpr uint32_t DetailRule = abgr(0xac9663);
// Tracks light enough to read as bars at 0 %; a map not visited keeps a dimmer one with no fill.
constexpr uint32_t BarTrack = abgr(0x4a564c);
constexpr uint32_t BarTrackDim = abgr(0x2e3630);
constexpr uint32_t BarGold = abgr(0xc9aa6a);
constexpr uint32_t Coral = abgr(0xe6a24a);

// Upright and heavier than the bitmap Lucida (the enemy labels' face), for the page's text.
constexpr char TextFont[] = "alegreya_semibold";

constexpr std::array<std::string_view, JournalProgressFilterCount> FilterNames = {Engine::trNoop("All"),
    Engine::trNoop("Cleared"), Engine::trNoop("In progress"), Engine::trNoop("Not visited")};

// The layout in the page's logical units (518 x 456, JournalProgressPage).
constexpr float CardTop = 58;
constexpr float CardHeight = 76;
constexpr float CardGap = 7;
constexpr float ChipTop = 140;
constexpr float ChipHeight = 15;
constexpr float ChipGap = 4;
constexpr float ChipPad = 6;
constexpr float ListLeft = 3;
constexpr float ListRight = 333;
constexpr float HeaderTop = 160;
constexpr float RowTop = 171;
constexpr float RowHeight = 18;
constexpr float LegendTop = 410;
constexpr float DetailLeft = 342;
constexpr float DetailRight = 515;

// The continents' cards share the row from ListLeft to DetailRight: 166 wide for three, narrower for Chedian's fourth.
float continentCardWidth(size_t cardCount)
{
    const float count = float(std::max<size_t>(cardCount, 1));
    return (DetailRight - ListLeft - CardGap * (count - 1)) / count;
}
constexpr float DetailTop = 140;
constexpr float DetailBottom = 404;
constexpr float FooterTop = 436;
constexpr float TextHeight = 9.5f;
// The player's guide link at the header's right.
constexpr float GuideLinkTop = 14;
constexpr float GuideLinkWidth = 80;
// The map list's columns: the name, the flags, the level, the bar and the resets.
constexpr float NameWidth = 128;
constexpr float FlagLeft = 138;
constexpr float FlagSize = 10;
constexpr float FlagStep = 12;
constexpr float LevelRight = 216;
constexpr float BarLeft = 222;
constexpr float BarWidth = 76;
constexpr float ResetsRight = 329;
// With every continent listed, the name gives room to the continent's column and the flags start after it.
constexpr float CombinedNameWidth = 102;
constexpr float CombinedContinentLeft = 111;
constexpr float CombinedContinentWidth = 38;
constexpr float CombinedFlagLeft = 152;

// What a map row's flags say at a glance, in their order; the legend and the hover name them.
enum class MapFlag : uint8_t
{
    Cleared,
    ResetOffered,
    Refilled,
    RewardWaiting,
    Bounty,
    DimensionRun,
};

constexpr std::array<std::string_view, 6> MapFlagNames = {Engine::trNoop("Cleared since its refill"),
    Engine::trNoop("Its entrance offers a reset"), Engine::trNoop("Refilled: cleared once, its monsters are back"),
    Engine::trNoop("Completion reward waiting"), Engine::trNoop("This month's bounty target"),
    Engine::trNoop("A dimension run is open")};
constexpr std::array<std::string_view, 6> MapFlagShortNames = {Engine::trNoop("cleared"), Engine::trNoop("reset"),
    Engine::trNoop("refilled"), Engine::trNoop("reward"), Engine::trNoop("bounty"), Engine::trNoop("dimension")};

std::vector<MapFlag> mapFlags(const RulesetProgressMap &map)
{
    std::vector<MapFlag> flags;
    const auto add = [&flags](bool condition, MapFlag flag)
    {
        if (condition)
        {
            flags.push_back(flag);
        }
    };
    add(map.clearedSinceRefill, MapFlag::Cleared);
    add(map.resetOffer.has_value(), MapFlag::ResetOffered);
    add(map.completedOnce && !map.clearedSinceRefill, MapFlag::Refilled);
    add(!map.completedOnce && map.state != RulesetMapProgressState::NotVisited, MapFlag::RewardWaiting);
    add(map.bountyTarget, MapFlag::Bounty);
    add(map.dimensionRun, MapFlag::DimensionRun);
    return flags;
}

struct Rect
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

Rect pageRect(const GameplayResolvedHudLayoutElement &page, float x, float y, float width, float height)
{
    return {page.x + x * page.scale, page.y + y * page.scale, width * page.scale, height * page.scale};
}

float fontScale(const GameplayScreenRuntime &context, const std::string &font, float logicalHeight, float scale)
{
    const int height = std::max(1, context.hudFontHeight(font));
    const float wanted = logicalHeight * scale / float(height);
    return wanted >= 1.0f ? GameplayHudCommon::snappedHudFontScale(wanted) : std::max(0.5f, wanted);
}

float textWidth(const GameplayScreenRuntime &context, const std::string &font, const std::string &text, float scale)
{
    return context.measureHudTextWidth(font, text) * scale;
}

// The filter chips' boxes, laid out left to right by their text.
std::array<Rect, JournalProgressFilterCount> chipRects(
    const GameplayScreenRuntime &context,
    const GameplayResolvedHudLayoutElement &page)
{
    std::array<Rect, JournalProgressFilterCount> rects = {};
    const float scale = fontScale(context, TextFont, TextHeight, page.scale);
    float x = ListLeft;

    for (size_t index = 0; index < FilterNames.size(); ++index)
    {
        const float width =
            textWidth(context, TextFont, Engine::tr(FilterNames[index]), scale) / page.scale + 2 * ChipPad;
        rects[index] = pageRect(page, x, ChipTop, width, ChipHeight);
        x += width + ChipGap;
    }

    return rects;
}

// The "All continents" chip, at the list's right end of the filters' row.
Rect allContinentsChipRect(const GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &page)
{
    const float scale = fontScale(context, TextFont, TextHeight, page.scale);
    const float width = textWidth(context, TextFont, Engine::tr("All continents"), scale) / page.scale + 2 * ChipPad;
    return pageRect(page, ListRight - width, ChipTop, width, ChipHeight);
}

// Whether the list holds the continent's maps: the chosen one, or each of them with "All continents" on.
bool continentShown(const GameplayUiController::JournalScreenState &journal, size_t index)
{
    return journal.progressAllContinents || index == journal.progressContinent;
}

const RulesetProgressContinent *continentOfMap(const RulesetProgressSummary &summary, const RulesetProgressMap &map)
{
    for (const RulesetProgressContinent &continent : summary.continents)
    {
        for (const RulesetProgressMap &entry : continent.maps)
        {
            if (&entry == &map)
            {
                return &continent;
            }
        }
    }

    return nullptr;
}

bool passesFilter(const RulesetProgressMap &map, uint8_t filter)
{
    switch (filter)
    {
        case 1:
            return map.state == RulesetMapProgressState::Cleared;
        case 2:
            return map.state == RulesetMapProgressState::InProgress;
        case 3:
            return map.state == RulesetMapProgressState::NotVisited;
        default:
            return true;
    }
}

std::string percentText(double share)
{
    return std::to_string(int(std::lround(share * 100))) + "%";
}

// The bar colour of the minimap plate's bands: green cleared, yellow half, red started, dark not visited.
uint32_t barColour(const RulesetProgressMap &map)
{
    if (map.state == RulesetMapProgressState::Cleared)
    {
        return Good;
    }

    return map.slainShare >= 0.5 ? Warn : Bad;
}

class Painter
{
public:
    Painter(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &page)
        : m_context(context)
        , m_page(page)
    {
    }

    void fill(const Rect &rect, uint32_t colour) const
    {
        if (rect.width <= 0 || rect.height <= 0)
        {
            return;
        }

        char name[48] = {};
        std::snprintf(name, sizeof(name), "__journal_progress_%08x", colour);

        if (const std::optional<GameplayHudTextureHandle> texture =
                m_context.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colour))
        {
            m_context.submitHudTexturedQuad(*texture, rect.x, rect.y, rect.width, rect.height);
        }
    }

    void frame(const Rect &rect, uint32_t colour) const
    {
        const float line = std::max(1.0f, std::round(m_page.scale));
        fill({rect.x, rect.y, rect.width, line}, colour);
        fill({rect.x, rect.y + rect.height - line, rect.width, line}, colour);
        fill({rect.x, rect.y, line, rect.height}, colour);
        fill({rect.x + rect.width - line, rect.y, line, rect.height}, colour);
    }

    // Text with its top left at page units (x, y); align 0 left, 1 centred on x, 2 ending at x. Returns its width in
    // page units.
    float text(const std::string &font, float height, uint32_t colour, const std::string &value, float x, float y,
        int align = 0) const
    {
        const float scale = fontScale(m_context, font, height, m_page.scale);
        const float width = textWidth(m_context, font, value, scale);
        float left = m_page.x + x * m_page.scale;
        left -= align == 1 ? width / 2 : align == 2 ? width : 0;
        m_context.renderHudTextLine(font, colour, value, std::round(left), std::round(m_page.y + y * m_page.scale),
            scale);
        return width / m_page.scale;
    }

    // The value shortened with an ellipsis to fit the width (page units).
    std::string fitted(const std::string &font, float height, const std::string &value, float width) const
    {
        const float scale = fontScale(m_context, font, height, m_page.scale);

        if (textWidth(m_context, font, value, scale) / m_page.scale <= width)
        {
            return value;
        }

        std::string result = value;

        while (result.size() > 1)
        {
            // A whole character: shown names may be translated into letters of several bytes.
            Engine::Utf8::popBack(result);

            while (!result.empty() && result.back() == ' ')
            {
                result.pop_back();
            }

            if (textWidth(m_context, font, result + "...", scale) / m_page.scale <= width)
            {
                return result + "...";
            }
        }

        return result;
    }

    std::vector<std::string> wrapped(const std::string &font, float height, const std::string &value,
        float width) const
    {
        const float scale = fontScale(m_context, font, height, m_page.scale);
        return m_context.wrapHudTextToWidth(font, value, width * m_page.scale / scale);
    }

    Rect rect(float x, float y, float width, float height) const
    {
        return pageRect(m_page, x, y, width, height);
    }

    // A flag's glyph in a size x size box at page units (x, y).
    void glyph(MapFlag flag, float x, float y, float size) const
    {
        const float cx = x + size / 2;
        const float cy = y + size / 2;
        const float r = size / 2;

        switch (flag)
        {
            case MapFlag::Cleared:
                lines({{cx - r * 0.8f, cy, cx - r * 0.2f, cy + r * 0.65f}, {cx - r * 0.2f, cy + r * 0.65f,
                    cx + r * 0.85f, cy - r * 0.7f}}, Good, 1.6f);
                break;
            case MapFlag::ResetOffered:
                arc(cx, cy, r * 0.75f, -60, 290, Gold, 1.3f);
                lines({{cx + r * 0.38f, cy - r * 0.95f, cx + r * 0.42f, cy - r * 0.6f}, {cx + r * 0.42f, cy - r * 0.6f,
                    cx + r * 0.05f, cy - r * 0.55f}}, Gold, 1.3f);
                break;
            case MapFlag::Refilled:
                arc(cx, cy, r * 0.72f, 0, 360, Coral, 1.3f);
                break;
            case MapFlag::RewardWaiting:
                disc(cx, cy, r * 0.8f, abgr(0x6a5426));
                disc(cx, cy, r * 0.6f, Gold);
                break;
            case MapFlag::Bounty:
                texture("obsidian_buff_skull", x - 2, y - 2, size + 4, size + 4);
                break;
            case MapFlag::DimensionRun:
                texture("obsidian_action_portal", x - 2.5f, y - 2.5f, size + 5, size + 5);
                break;
        }
    }

private:
    std::optional<GameplayHudTextureHandle> solid(uint32_t colour) const
    {
        char name[48] = {};
        std::snprintf(name, sizeof(name), "__journal_progress_%08x", colour);
        return m_context.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colour);
    }

    struct Segment
    {
        float x1;
        float y1;
        float x2;
        float y2;
    };

    void lines(const std::vector<Segment> &segments, uint32_t colour, float width) const
    {
        const std::optional<GameplayHudTextureHandle> texture = solid(colour);

        if (!texture)
        {
            return;
        }

        std::vector<GameplayHudBatchQuad> quads;

        for (const Segment &segment : segments)
        {
            GameplayHudBatchQuad quad;
            quad.textureHandle = texture->textureHandle;
            quad.line = true;
            quad.width = std::max(1.0f, width * m_page.scale);
            quad.x = m_page.x + segment.x1 * m_page.scale;
            quad.y = m_page.y + segment.y1 * m_page.scale;
            quad.x2 = m_page.x + segment.x2 * m_page.scale;
            quad.y2 = m_page.y + segment.y2 * m_page.scale;
            quads.push_back(quad);
        }

        m_context.submitHudQuadBatch(quads);
    }

    void arc(float cx, float cy, float radius, float startDegrees, float sweepDegrees, uint32_t colour,
        float width) const
    {
        std::vector<Segment> segments;
        constexpr int Steps = 20;

        for (int step = 0; step < Steps; ++step)
        {
            const float a = (startDegrees + sweepDegrees * step / Steps) * 3.14159265f / 180.0f;
            const float b = (startDegrees + sweepDegrees * (step + 1) / Steps) * 3.14159265f / 180.0f;
            segments.push_back({cx + radius * std::cos(a), cy + radius * std::sin(a), cx + radius * std::cos(b),
                cy + radius * std::sin(b)});
        }

        lines(segments, colour, width);
    }

    void disc(float cx, float cy, float radius, uint32_t colour) const
    {
        if (const std::optional<GameplayHudTextureHandle> texture = solid(colour))
        {
            m_context.gameplayUiRuntime().submitHudTexturedEllipse(texture->textureHandle,
                m_page.x + (cx - radius) * m_page.scale, m_page.y + (cy - radius) * m_page.scale,
                2 * radius * m_page.scale, 2 * radius * m_page.scale);
        }
    }

    void texture(const char *pName, float x, float y, float width, float height) const
    {
        if (const std::optional<GameplayHudTextureHandle> handle =
                m_context.gameplayUiRuntime().ensureHudTextureLoaded(pName))
        {
            m_context.submitHudTexturedQuad(*handle, m_page.x + x * m_page.scale, m_page.y + y * m_page.scale,
                width * m_page.scale, height * m_page.scale);
        }
    }

public:

private:
    GameplayScreenRuntime &m_context;
    const GameplayResolvedHudLayoutElement &m_page;
};

const RulesetProgressMap *shownMap(const GameplayUiController::JournalScreenState &journal)
{
    if (!journal.progress)
    {
        return nullptr;
    }

    const std::vector<RulesetProgressContinent> &continents = journal.progress->continents;

    for (const std::string *pName : {&journal.progressHoveredMap, &journal.progressSelectedMap})
    {
        for (size_t index = 0; !pName->empty() && index < continents.size(); ++index)
        {
            for (const RulesetProgressMap &map : continents[index].maps)
            {
                if (continentShown(journal, index) && map.fileName == *pName)
                {
                    return &map;
                }
            }
        }
    }

    // None chosen: the lowest of the shown continents' maps.
    const RulesetProgressMap *pLowest = nullptr;

    for (size_t index = 0; index < continents.size(); ++index)
    {
        if (continentShown(journal, index) && !continents[index].maps.empty()
            && (pLowest == nullptr || continents[index].maps.front().level < pLowest->level))
        {
            pLowest = &continents[index].maps.front();
        }
    }

    return pLowest;
}
}

bool journalHasProgressTab(const GameplayScreenRuntime &context)
{
    return gameRulesFor(context.partyReadOnly()).monsters.hasProgressTab();
}

bool ensureJournalProgress(GameplayScreenRuntime &context, GameplayUiController::JournalScreenState &journal)
{
    if (journal.progress)
    {
        return true;
    }

    const IGameplayWorldRuntime *pWorld = context.worldRuntime();
    RulesetProgressQuery query;
    query.pParty = context.partyReadOnly();
    query.pMonsterTable = pWorld != nullptr ? pWorld->monsterTable() : nullptr;
    query.gameMinutes = pWorld != nullptr ? pWorld->gameMinutes() : 0.0f;
    query.pEventState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
    MapKillProgress progress;

    if (pWorld != nullptr && pWorld->mapKillProgress(progress))
    {
        query.currentMap = progress;
    }

    std::optional<RulesetProgressSummary> summary = gameRulesFor(query.pParty).monsters.progressSummary(query);

    if (!summary)
    {
        return false;
    }

    journal.progress = std::make_shared<const RulesetProgressSummary>(std::move(*summary));

    if (!query.currentMap)
    {
        return true;
    }

    // Open on the continent the party is on.
    std::string current = query.currentMap->mapFileName;
    std::transform(current.begin(), current.end(), current.begin(),
        [](unsigned char c) { return char(std::tolower(c)); });
    const RulesetProgressMap *pCurrent = nullptr;

    for (size_t index = 0; index < journal.progress->continents.size(); ++index)
    {
        for (const RulesetProgressMap &map : journal.progress->continents[index].maps)
        {
            if (map.fileName == current)
            {
                journal.progressContinent = index;
                journal.progressSelectedMap = map.fileName;
                journal.progressFilter = 0;
                pCurrent = &map;
            }
        }
    }

    if (pCurrent != nullptr)
    {
        // Scrolled to show it, a few rows down.
        const std::vector<const RulesetProgressMap *> maps = journalProgressMaps(journal);
        const size_t row = size_t(std::find(maps.begin(), maps.end(), pCurrent) - maps.begin());
        journal.progressScroll = maps.size() > JournalProgressVisibleRows
            ? std::min(row > 3 ? row - 3 : 0, maps.size() - JournalProgressVisibleRows) : 0;
    }

    return true;
}

std::vector<const RulesetProgressMap *> journalProgressMaps(const GameplayUiController::JournalScreenState &journal)
{
    std::vector<const RulesetProgressMap *> maps;

    if (!journal.progress)
    {
        return maps;
    }

    for (size_t index = 0; index < journal.progress->continents.size(); ++index)
    {
        if (!continentShown(journal, index))
        {
            continue;
        }

        for (const RulesetProgressMap &map : journal.progress->continents[index].maps)
        {
            if (passesFilter(map, journal.progressFilter))
            {
                maps.push_back(&map);
            }
        }
    }

    if (journal.progressAllContinents)
    {
        // Each continent's maps are by level already; equal levels stay in the continents' order.
        std::stable_sort(maps.begin(), maps.end(), [](const RulesetProgressMap *pLeft, const RulesetProgressMap *pRight)
            {
                return pLeft->level < pRight->level;
            });
    }

    return maps;
}

JournalProgressTarget journalProgressTargetAt(
    const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float x,
    float y)
{
    if (!journal.progress)
    {
        return {};
    }

    if (!context.rulesetGuideUrl().empty()
        && pageRect(page, DetailRight - GuideLinkWidth, GuideLinkTop, GuideLinkWidth, TextHeight + 4).contains(x, y))
    {
        return {JournalProgressTargetKind::Guide, 0};
    }

    const float cardWidth = continentCardWidth(journal.progress->continents.size());

    for (size_t index = 0; index < journal.progress->continents.size(); ++index)
    {
        if (pageRect(page, ListLeft + index * (cardWidth + CardGap), CardTop, cardWidth, CardHeight).contains(x, y))
        {
            return {JournalProgressTargetKind::Continent, index};
        }
    }

    const std::array<Rect, JournalProgressFilterCount> chips = chipRects(context, page);

    for (size_t index = 0; index < chips.size(); ++index)
    {
        if (chips[index].contains(x, y))
        {
            return {JournalProgressTargetKind::Filter, index};
        }
    }

    if (allContinentsChipRect(context, page).contains(x, y))
    {
        return {JournalProgressTargetKind::AllContinents, 0};
    }

    const size_t count = journalProgressMaps(journal).size();

    for (size_t row = 0; row < JournalProgressVisibleRows; ++row)
    {
        const size_t index = journal.progressScroll + row;

        if (index < count
            && pageRect(page, ListLeft, RowTop + row * RowHeight, ListRight - ListLeft, RowHeight).contains(x, y))
        {
            return {JournalProgressTargetKind::Map, index};
        }
    }

    return {};
}

void renderJournalProgress(
    GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float pointerX,
    float pointerY)
{
    if (!journal.progress)
    {
        return;
    }

    const RulesetProgressSummary &summary = *journal.progress;
    const Painter paint(context, page);
    constexpr float PageWidth = 518;
    // The pointer in page units, for the flags' names.
    const float pointerPageX = (pointerX - page.x) / page.scale;
    const float pointerPageY = (pointerY - page.y) / page.scale;
    std::optional<MapFlag> hoveredFlag;

    // Header: the title and the game's mode.
    paint.text("Fondamento", 22, Gold, Engine::tr("Progress"), PageWidth / 2, 10, 1);
    // The HUD fonts are single-byte: the middle dot is 0xB7.
    const std::string dot = "  \xB7  ";
    // The summary holds the options' English names.
    std::string mode =
        Engine::tr("{difficulty} difficulty", {{"difficulty", Engine::localizeKnown(summary.difficulty)}}) + dot
        + Engine::tr("{progression} progression", {{"progression", Engine::localizeKnown(summary.progression)}})
        + dot + Engine::tr("total level {level}", {{"level", summary.totalLevel}}) + dot
        + Engine::tr("challenge mode {mode}", {{"mode", Engine::localizeKnown(summary.challengeMode)}});

    if (summary.deaths)
    {
        mode += dot + Engine::trn("{count} death", "{count} deaths", uint64_t(*summary.deaths),
            {{"count", *summary.deaths}});
    }

    paint.text(TextFont, TextHeight, Ivory, mode, PageWidth / 2, 39, 1);

    if (!context.rulesetGuideUrl().empty())
    {
        const bool guideHovered = pointerPageX >= DetailRight - GuideLinkWidth && pointerPageX <= DetailRight
            && pointerPageY >= GuideLinkTop && pointerPageY <= GuideLinkTop + TextHeight + 4;
        paint.text(TextFont, TextHeight, guideHovered ? Ivory : Gold, Engine::tr("Player's guide"), DetailRight,
            GuideLinkTop, 2);
    }

    // The continents' cards.
    const float cardWidth = continentCardWidth(summary.continents.size());

    for (size_t index = 0; index < summary.continents.size(); ++index)
    {
        const RulesetProgressContinent &continent = summary.continents[index];
        const float x = ListLeft + index * (cardWidth + CardGap);
        const bool selected = continentShown(journal, index);
        const Rect card = paint.rect(x, CardTop, cardWidth, CardHeight);
        paint.fill(card, selected ? SelectedFill : PanelFill);
        paint.frame(card, selected ? SelectedBorder : PanelBorder);
        paint.text("Fondamento", 13, Label, Engine::localizeKnown(continent.name), x + 7, CardTop + 3);
        paint.text(TextFont, 8, Muted, continent.world, x + cardWidth - 7, CardTop + 6, 2);
        const auto row = [&](float y, const std::string &key, const std::string &value, uint32_t colour)
        {
            paint.text(TextFont, TextHeight, Body, key, x + 7, y);
            paint.text(TextFont, TextHeight, colour, value, x + cardWidth - 7, y, 2);
        };
        row(CardTop + 21, Engine::tr("Monster levels"),
            continent.levelHigh > 0
                ? std::to_string(continent.levelLow) + " - " + std::to_string(continent.levelHigh) : std::string("-"),
            Ivory);
        row(CardTop + 33, Engine::tr("Levels banked here"),
            "+" + std::to_string(int(std::lround(continent.levelsBanked))), Amount);
        row(CardTop + 45, Engine::tr("Maps cleared"),
            std::to_string(continent.mapsCleared) + " / " + std::to_string(continent.maps.size()), Ivory);
        const float barWidth = cardWidth - 14;
        paint.fill(paint.rect(x + 7, CardTop + 62, barWidth, 6), BarTrack);
        const float share = continent.maps.empty() ? 0.0f : float(continent.mapsCleared) / continent.maps.size();
        paint.fill(paint.rect(x + 7, CardTop + 62, barWidth * share, 6), BarGold);
    }

    // The filters.
    const std::array<Rect, JournalProgressFilterCount> chips = chipRects(context, page);

    for (size_t index = 0; index < chips.size(); ++index)
    {
        const bool on = index == journal.progressFilter;
        paint.fill(chips[index], on ? SelectedFill : PanelFill);
        paint.frame(chips[index], on ? SelectedBorder : PanelBorder);
        paint.text(TextFont, TextHeight, on ? Ivory : Body, Engine::tr(FilterNames[index]),
            (chips[index].x - page.x) / page.scale + ChipPad, ChipTop + 2.5f);
    }

    const bool combined = journal.progressAllContinents;
    const Rect allChip = allContinentsChipRect(context, page);
    paint.fill(allChip, combined ? SelectedFill : PanelFill);
    paint.frame(allChip, combined ? SelectedBorder : PanelBorder);
    paint.text(TextFont, TextHeight, combined ? Ivory : Body, Engine::tr("All continents"),
        (allChip.x - page.x) / page.scale + ChipPad, ChipTop + 2.5f);

    // The map list.
    paint.text(TextFont, 8, Muted, Engine::tr("Map"), ListLeft + 4, HeaderTop);

    if (combined)
    {
        paint.text(TextFont, 8, Muted, Engine::tr("Continent"), CombinedContinentLeft, HeaderTop);
    }

    paint.text(TextFont, 8, Muted, Engine::tr("Level"), LevelRight, HeaderTop, 2);
    paint.text(TextFont, 8, Muted, Engine::tr("Cleared"), BarLeft, HeaderTop);
    paint.text(TextFont, 8, Muted, Engine::tr("Resets"), ResetsRight, HeaderTop, 2);
    const std::vector<const RulesetProgressMap *> maps = journalProgressMaps(journal);
    const RulesetProgressMap *pShown = shownMap(journal);

    for (size_t row = 0; row < JournalProgressVisibleRows && journal.progressScroll + row < maps.size(); ++row)
    {
        const RulesetProgressMap &map = *maps[journal.progressScroll + row];
        const float y = RowTop + row * RowHeight;

        if (&map == pShown)
        {
            paint.fill(paint.rect(ListLeft, y, ListRight - ListLeft, RowHeight), RowHighlight);
        }

        paint.fill(paint.rect(ListLeft, y + RowHeight - 0.5f, ListRight - ListLeft, 0.5f), RowRule);
        paint.text(TextFont, TextHeight, Ivory,
            paint.fitted(TextFont, TextHeight, Engine::localizeKnown(map.name),
                combined ? CombinedNameWidth : NameWidth),
            ListLeft + 4, y + 4);

        if (const RulesetProgressContinent *pContinent = combined ? continentOfMap(summary, map) : nullptr)
        {
            paint.text(TextFont, 8, Muted,
                paint.fitted(TextFont, 8, Engine::localizeKnown(pContinent->name), CombinedContinentWidth),
                CombinedContinentLeft, y + 5);
        }

        // The flags, the one under the pointer named below.
        float flagX = combined ? CombinedFlagLeft : FlagLeft;

        for (const MapFlag flag : mapFlags(map))
        {
            paint.glyph(flag, flagX, y + (RowHeight - FlagSize) / 2, FlagSize);

            if (pointerPageX >= flagX && pointerPageX < flagX + FlagStep && pointerPageY >= y
                && pointerPageY < y + RowHeight)
            {
                hoveredFlag = flag;
            }

            flagX += FlagStep;
        }

        paint.text(TextFont, TextHeight, Ivory, std::to_string(map.level), LevelRight, y + 4, 2);
        const bool visited = map.state != RulesetMapProgressState::NotVisited;
        paint.fill(paint.rect(BarLeft, y + 6.5f, BarWidth, 5), visited ? BarTrack : BarTrackDim);

        if (visited && map.slainShare > 0)
        {
            paint.fill(paint.rect(BarLeft, y + 6.5f, BarWidth * float(map.slainShare), 5), barColour(map));
        }

        if (map.resets > 0)
        {
            paint.text(TextFont, TextHeight, Ivory, std::to_string(map.resets), ResetsRight, y + 4, 2);
        }
    }

    if (maps.size() > JournalProgressVisibleRows)
    {
        const float trackHeight = JournalProgressVisibleRows * RowHeight;
        const float thumb = trackHeight * JournalProgressVisibleRows / maps.size();
        const float offset = (trackHeight - thumb) * journal.progressScroll
            / float(maps.size() - JournalProgressVisibleRows);
        paint.fill(paint.rect(ListRight + 2, RowTop, 1.5f, trackHeight), BarTrack);
        paint.fill(paint.rect(ListRight + 1.25f, RowTop + offset, 3, thumb), BarGold);
    }
    else if (maps.empty())
    {
        paint.text(TextFont, TextHeight, Muted, Engine::tr("No maps"), ListLeft + 4, RowTop + 4);
    }

    // The legend of the flags.
    float legendX = ListLeft;

    for (size_t index = 0; index < MapFlagShortNames.size(); ++index)
    {
        paint.glyph(MapFlag(index), legendX, LegendTop + 1, FlagSize);
        legendX += FlagSize + 3;
        legendX += paint.text(TextFont, 8, Body, Engine::tr(MapFlagShortNames[index]), legendX, LegendTop) + 10;
    }

    // The shown map's details.
    paint.fill(paint.rect(DetailLeft, DetailTop, DetailRight - DetailLeft, DetailBottom - DetailTop), DetailFill);
    paint.fill(paint.rect(DetailLeft, DetailTop, 1, DetailBottom - DetailTop), DetailRule);

    if (pShown != nullptr)
    {
        const RulesetProgressMap &map = *pShown;
        constexpr float Left = DetailLeft + 8;
        constexpr float Right = DetailRight - 6;
        const std::string mapName = Engine::localizeKnown(map.name);
        paint.text("Fondamento", 14, Label, paint.fitted("Fondamento", 14, mapName, Right - Left), Left, DetailTop + 4);
        float y = DetailTop + 26;
        const auto row = [&](const std::string &key, const std::string &value)
        {
            paint.text(TextFont, TextHeight, Body, key, Left, y);
            paint.text(TextFont, TextHeight, Ivory, value, Right, y, 2);
            y += 13;
        };
        const auto note = [&](const std::string &value, uint32_t colour)
        {
            for (const std::string &line : paint.wrapped(TextFont, 8.5f, value, Right - Left))
            {
                paint.text(TextFont, 8.5f, colour, line, Left, y);
                y += 11;
            }
        };

        if (const RulesetProgressContinent *pContinent = combined ? continentOfMap(summary, map) : nullptr)
        {
            row(Engine::tr("Continent"), Engine::localizeKnown(pContinent->name));
        }

        row(Engine::tr("Monster level"), map.levelFromResets > 0
            ? Engine::tr("{level} (+{added} from resets)", {{"level", map.level}, {"added", map.levelFromResets}})
            : std::to_string(map.level));
        row(Engine::tr("State"),
            map.state == RulesetMapProgressState::NotVisited ? std::string("-") : percentText(map.slainShare));
        note(map.state == RulesetMapProgressState::Cleared ? Engine::tr("Cleared since its refill")
            : map.state == RulesetMapProgressState::NotVisited ? Engine::tr("Not visited")
            : map.completedOnce && map.slainShare <= 0 ? Engine::tr("Completed once, refilled since")
            : Engine::tr("{percent} of its monsters slain", {{"percent", percentText(map.slainShare)}}), Body);
        y += 2;
        row(Engine::tr("Completion reward"), map.completedOnce ? Engine::tr("claimed") : Engine::tr("waiting"));
        row(Engine::tr("Resets"), std::to_string(map.resets));
        row(Engine::tr("Refills in"), !map.refillInDays ? std::string("-")
            : *map.refillInDays == 0 ? Engine::tr("next visit")
            : Engine::trn("{count} day", "{count} days", uint64_t(*map.refillInDays), {{"count", *map.refillInDays}}));
        y += 4;

        for (const MapFlag flag : mapFlags(map))
        {
            paint.glyph(flag, Left, y + 1, FlagSize);
            paint.text(TextFont, 8.5f, Body, Engine::tr(MapFlagNames[size_t(flag)]), Left + FlagSize + 4, y);
            y += 11;
        }

        y += 3;

        if (map.resetOffer)
        {
            note(Engine::tr("Entering it offers a reset: {offer}", {{"offer", *map.resetOffer}}), Body);
        }
        else if (!map.completedOnce)
        {
            note(Engine::tr("Clearing it banks experience on this continent and adds it to the dimension map pool."),
                Body);
        }
    }

    // The dimension and bounty records.
    float x = ListLeft;
    const auto record = [&](const std::string &key, const std::string &value)
    {
        x += paint.text(TextFont, TextHeight, Body, key + " ", x, FooterTop);
        x += paint.text(TextFont, TextHeight, Ivory, value, x, FooterTop) + 14;
    };
    record(Engine::tr("Dimension quest"), summary.dimensionQuest);
    record(Engine::tr("Dimension runs"), Engine::tr("{count} cleared", {{"count", summary.dimensionRunsCleared}}));
    record(Engine::tr("Current run"), summary.currentRun);
    record(Engine::tr("Bounties"), Engine::tr("{count} claimed, {gold} gold",
        {{"count", summary.bountiesClaimed}, {"gold", summary.bountyGold}}));

    // The name of the flag under the pointer.
    if (hoveredFlag)
    {
        const std::string name = Engine::tr(MapFlagNames[size_t(*hoveredFlag)]);
        const float nameWidth =
            textWidth(context, TextFont, name, fontScale(context, TextFont, 8.5f, page.scale)) / page.scale;
        const float tipX = std::min(pointerPageX + 8, PageWidth - nameWidth - 10);
        const Rect tip = paint.rect(tipX, pointerPageY + 10, nameWidth + 10, 14);
        paint.fill(tip, abgr(0x070e0e, 0xf0));
        paint.frame(tip, SelectedBorder);
        paint.text(TextFont, 8.5f, Ivory, name, tipX + 5, pointerPageY + 12.5f);
    }
}
}
