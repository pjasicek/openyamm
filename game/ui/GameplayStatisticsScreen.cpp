#include "game/ui/GameplayStatisticsScreen.h"

#include "engine/Localization.h"
#include "engine/Utf8Text.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/Party.h"
#include "game/party/PlaythroughStatistics.h"
#include "game/ui/CalendarText.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <optional>

namespace OpenYAMM::Game
{
namespace GameplayStatisticsScreen
{
namespace
{
// Colours of the approved overlays (level_generation/ui/playthrough_stats_20261107/).
constexpr uint32_t IvoryColor = GameplayUiSkin::Ivory;
constexpr uint32_t GoldColor = GameplayUiSkin::Gold;
constexpr uint32_t LossColor = GameplayUiSkin::Penalty;
constexpr uint32_t LowColor = GameplayUiSkin::Low;
constexpr uint32_t MutedColor = 0xffa5b5aeu;
constexpr uint32_t DimColor = 0xff79867fu;
constexpr uint32_t GroupBorderColor = 0x8f72a1b6u;
constexpr uint32_t GroupShadowColor = 0xff080c05u;
constexpr uint32_t GroupInnerColor = 0x238fc5dcu;
constexpr uint32_t GroupFillColor = 0x30091107u;
constexpr uint32_t RowHighlightColor = 0x1493c7e4u;
constexpr uint32_t TrackColor = 0xff070b05u;
constexpr uint32_t ShareColor = 0xff6fa3c9u;

// The surface of the screen above the party frame, and its parts, in the 640x480 frame's units.
constexpr float SurfaceHeight = 368.0f;
constexpr float ColumnsTop = 44.0f;
constexpr float ColumnsBottom = 318.0f;
constexpr float ColumnsLeft = 18.0f;
constexpr float ColumnGap = 11.0f;
constexpr float ColumnCount = 3.0f;
constexpr float GroupGap = 8.0f;
constexpr float GroupPadX = 8.0f;
constexpr float GroupPadY = 3.0f;
constexpr float HeadingHeight = 17.0f;
constexpr float RowHeight = 17.0f;
constexpr float RowScale = 15.0f / 17.0f;
constexpr float HeadingScale = 15.0f / 19.0f;
constexpr float SmallScale = 13.0f / 14.0f;

constexpr std::array<uint32_t, StatDamageSchoolCount> SchoolColors = {
    0xff8ab5c9u, 0xff4f81d8u, 0xffd8c49fu, 0xffc08f5eu, 0xff5c8a9bu, 0xffa0c0c8u,
    0xffa08ab8u, 0xffa08ab8u, 0xffa8e2efu, 0xffa87a8fu, 0xffc0d08fu, 0xffbbbbbbu};
constexpr std::array<std::string_view, StatDamageSchoolCount> SchoolNames = {Engine::trNoop("Physical"),
    Engine::trNoop("Fire"), Engine::trNoop("Air"), Engine::trNoop("Water"), Engine::trNoop("Earth"),
    Engine::trNoop("Spirit"), Engine::trNoop("Mind"), Engine::trNoop("Body"), Engine::trNoop("Light"),
    Engine::trNoop("Dark"), Engine::trNoop("Energy"), Engine::trNoop("Irresistible")};

using Rect = GameplayResolvedHudLayoutElement;

struct Row
{
    std::string label;
    std::string value;
    uint32_t valueColor = IvoryColor;
    std::string breakdown;
};

struct Group
{
    std::string heading;
    std::vector<Row> rows;
};

struct InspectableRect
{
    Rect rect;
    std::string breakdown;
};

std::string percentText(double part, double total)
{
    if (total <= 0.0)
    {
        return std::string();
    }

    const double percent = 100.0 * part / total;
    char text[16] = {};
    std::snprintf(text, sizeof(text), percent < 10.0 && percent > 0.0 ? "%.1f%%" : "%.0f%%", percent);
    return text;
}

std::string rateText(double amount, double seconds)
{
    if (seconds < 60.0)
    {
        return "-";
    }

    const double perHour = amount * 3600.0 / seconds;

    if (perHour >= 100.0)
    {
        return formatCount(uint64_t(std::llround(perHour)));
    }

    char text[16] = {};
    std::snprintf(text, sizeof(text), "%.1f", perHour);
    return text;
}

std::string dayText(double day)
{
    return Engine::tr("day {day}", {{"day", int64_t(std::floor(day)) + 1}});
}

// "2026-10-14T19:02:11Z" as "14 October 2026".
std::string dateText(const std::string &utc)
{
    return formatUtcDate(utc);
}

std::string upperText(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char ch) { return char(std::toupper(ch)); });
    return text;
}

std::string capitalizedText(std::string text)
{
    if (!text.empty())
    {
        text[0] = char(std::toupper(static_cast<unsigned char>(text[0])));
    }

    return text;
}

// A recorded name (monster, spell, item, death cause) as the interface language shows it.
std::string recordedText(const std::string &text)
{
    return text.empty() || text == "unknown" ? Engine::tr("unknown") : Engine::localizeKnown(text);
}

template<typename Value>
std::vector<std::pair<std::string, Value>> topEntries(const std::map<std::string, Value> &values, size_t count)
{
    std::vector<std::pair<std::string, Value>> entries(values.begin(), values.end());
    std::sort(entries.begin(), entries.end(), [](const auto &left, const auto &right) { return left.second > right.second; });

    if (entries.size() > count)
    {
        entries.resize(count);
    }

    return entries;
}

const PlaythroughMemberCounters *memberCounters(const PlaythroughCounters &counters, uint64_t statsMemberId)
{
    const auto found = counters.members.find(PlaythroughStatistics::memberKey(statsMemberId));
    return found != counters.members.end() ? &found->second : nullptr;
}

BreakdownLine row(std::string label, std::string value, std::string extra = std::string())
{
    BreakdownLine line;
    line.label = std::move(label);
    line.value = std::move(value);
    line.extra = std::move(extra);
    return line;
}

BreakdownLine section(std::string label)
{
    BreakdownLine line;
    line.kind = BreakdownLine::Kind::Section;
    line.label = std::move(label);
    return line;
}

BreakdownLine rule()
{
    BreakdownLine line;
    line.kind = BreakdownLine::Kind::Rule;
    return line;
}

BreakdownLine note(std::string text)
{
    BreakdownLine line;
    line.kind = BreakdownLine::Kind::Note;
    line.label = std::move(text);
    return line;
}

std::string mapName(const GameplayScreenRuntime *pContext, const std::string &mapFileName)
{
    if (pContext == nullptr || mapFileName.empty())
    {
        return mapFileName;
    }

    const std::string name = pContext->resolveMapLocationName(mapFileName);
    return name.empty() ? mapFileName : Engine::localizeKnown(name);
}

std::vector<Group> overviewGroups(const PlaythroughStatistics &statistics, float gameMinutes,
    std::vector<Group> &secondColumn, std::vector<Group> &thirdColumn)
{
    const PlaythroughCounters &t = statistics.timeline();
    const PlaythroughCounters &l = statistics.lifetime();
    const auto count = [](uint64_t value) { return formatCount(value); };
    const auto lossColor = [](uint64_t value) { return value > 0 ? LossColor : DimColor; };
    const uint64_t largestHit = t.largestHits.empty() ? 0 : t.largestHits.front().amount;
    const std::string gameDays =
        Engine::tr("{count} days", {{"count", formatCount(uint64_t(gameMinutes / (24.0f * 60.0f)))}});

    std::vector<Group> first = {
        {Engine::tr("Time"),
            {{Engine::tr("Played"), formatDuration(l.playedSeconds), IvoryColor, "played"},
                {Engine::tr("Game time"), gameDays, IvoryColor, "played"},
                {Engine::tr("Turn-based"), formatDuration(l.turnBasedSeconds), IvoryColor, "turnbased"},
                {Engine::tr("Sessions"), count(l.sessions), IvoryColor, "played"}}},
        {Engine::tr("Experience"),
            {{Engine::tr("Earned"), count(t.experienceTotal()), IvoryColor, "xp"},
                {Engine::tr("Per hour"), rateText(double(t.experienceTotal()), l.playedSeconds), GoldColor, "xp"},
                {Engine::tr("Levels gained"), count(t.levelsGained), IvoryColor, "levels"}}},
        {Engine::tr("Saves"),
            {{Engine::tr("Saves"), count(l.saves()), IvoryColor, "saves"},
                {Engine::tr("Loads"), count(l.loads()), IvoryColor, "saves"}}},
    };
    secondColumn = {
        {Engine::tr("Combat"),
            {{Engine::tr("Monsters killed"), count(t.kills), IvoryColor, "kills"},
                {Engine::tr("Kills per hour"), rateText(double(t.kills), l.playedSeconds), GoldColor, "kills"},
                {Engine::tr("Damage dealt"), count(t.damageDealtTotal()), IvoryColor, "damage"},
                {Engine::tr("Damage taken"), count(t.damageTakenTotal()), IvoryColor, "taken"},
                {Engine::tr("Largest hit"), count(largestHit), GoldColor, "biggest"},
                {Engine::tr("Spells cast"), count(t.spellsCast), IvoryColor, "spells"}}},
        // Losses count undone play too: a player reloads after exactly these, and MM9's early game over reloads the
        // autosave by itself, so the timeline would hide nearly all of them.
        {Engine::tr("Losses"),
            {{Engine::tr("Deaths"), count(l.deaths), lossColor(l.deaths), "deaths"},
                {Engine::tr("Eradications"), count(l.eradications), lossColor(l.eradications), "deaths"},
                {Engine::tr("Party wipes"), count(l.partyWipes), lossColor(l.partyWipes), "wipes"},
                {Engine::tr("Temple healings"), count(l.templeHeals), IvoryColor, "temple"}}},
    };
    thirdColumn = {
        {Engine::tr("Exploration"),
            {{Engine::tr("Town Portals"), count(t.townPortals), IvoryColor, "tp"},
                {Engine::tr("Lloyd's Beacons"), count(t.lloydRecalls), IvoryColor, "lloyd"},
                {Engine::tr("Coach and ship"), count(t.coachTrips + t.shipTrips), IvoryColor, "travel"},
                {Engine::tr("Maps visited"), count(t.mapsVisited.size()), IvoryColor, "maps"},
                {Engine::tr("Chests opened"), count(t.chestsOpened.size()), IvoryColor, "chests"}}},
        {Engine::tr("Wealth"),
            {{Engine::tr("Gold looted"), count(t.goldLooted()), IvoryColor, "looted"},
                {Engine::tr("Gold spent"), count(t.goldSpentTotal()), IvoryColor, "spent"},
                {Engine::tr("Artifacts found"), count(t.artifactsFound.size()), IvoryColor, "artifacts"}}},
    };
    return first;
}

Rect rootRect(GameplayScreenRuntime &context, int width, int height)
{
    const GameplayScreenRuntime::HudLayoutElement *pRoot = context.findHudLayoutElement("StatisticsRoot");
    const std::optional<Rect> resolved = pRoot != nullptr
        ? context.resolveHudLayoutElement("StatisticsRoot", width, height, pRoot->width, pRoot->height)
        : std::nullopt;

    if (resolved)
    {
        return *resolved;
    }

    const GameplayUiViewportRect viewport = GameplayHudCommon::computeUiViewportRect(width, height);
    return {viewport.x, viewport.y, viewport.width, viewport.height, viewport.height / 480.0f};
}

Rect toScreen(const Rect &root, float x, float y, float width, float height)
{
    return {root.x + x * root.scale, root.y + y * root.scale, width * root.scale, height * root.scale, root.scale};
}

void fillRect(GameplayScreenRuntime &context, const Rect &rect, uint32_t colorAbgr)
{
    char name[40] = {};
    std::snprintf(name, sizeof(name), "__statistics_%08x__", colorAbgr);
    const std::optional<GameplayHudTextureHandle> texture =
        context.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colorAbgr);

    if (texture && rect.width > 0.0f && rect.height > 0.0f)
    {
        context.submitHudTexturedQuad(*texture, rect.x, rect.y, rect.width, rect.height);
    }
}

void outlineRect(GameplayScreenRuntime &context, const Rect &rect, float thickness, uint32_t colorAbgr)
{
    fillRect(context, {rect.x, rect.y, rect.width, thickness, rect.scale}, colorAbgr);
    fillRect(context, {rect.x, rect.y + rect.height - thickness, rect.width, thickness, rect.scale}, colorAbgr);
    fillRect(context, {rect.x, rect.y + thickness, thickness, rect.height - 2 * thickness, rect.scale}, colorAbgr);
    fillRect(context, {rect.x + rect.width - thickness, rect.y + thickness, thickness, rect.height - 2 * thickness,
        rect.scale}, colorAbgr);
}

// The stats screen's group frame: dark outline, brass border, faint inner light.
void renderGroupFrame(GameplayScreenRuntime &context, const Rect &rect)
{
    const float unit = std::max(1.0f, std::round(rect.scale));
    fillRect(context, rect, GroupFillColor);
    outlineRect(context, {rect.x - unit, rect.y - unit, rect.width + 2 * unit, rect.height + 2 * unit, rect.scale},
        unit, GroupShadowColor);
    outlineRect(context, rect, unit, GroupBorderColor);
    outlineRect(context, {rect.x + unit, rect.y + unit, rect.width - 2 * unit, rect.height - 2 * unit, rect.scale},
        unit, GroupInnerColor);
}

float textWidth(GameplayScreenRuntime &context, const std::string &font, const std::string &text, float scale)
{
    return context.measureHudTextWidth(font, text) * scale;
}

// Text in the frame's units: left, right or centre aligned in [x, x + width].
void drawText(GameplayScreenRuntime &context, const Rect &root, const std::string &font, float scale,
    uint32_t colorAbgr, const std::string &text, float x, float y, float width,
    UiLayoutManager::TextAlignX alignX = UiLayoutManager::TextAlignX::Left)
{
    if (text.empty())
    {
        return;
    }

    GameplayScreenRuntime::HudLayoutElement layout = {};
    layout.fontName = font;
    layout.textColorAbgr = colorAbgr;
    layout.textAlignX = alignX;
    layout.textAlignY = UiLayoutManager::TextAlignY::Top;
    layout.textScale = scale;
    const float height = float(std::max(1, context.hudFontHeight(font))) * scale + 2.0f;
    context.renderLayoutLabel(layout, toScreen(root, x, y, width, height), text, false);
}

bool pointerInside(const Rect &rect, const GameplayInputFrame *pInput)
{
    return pInput != nullptr && pInput->pointerX >= rect.x && pInput->pointerX < rect.x + rect.width
        && pInput->pointerY >= rect.y && pInput->pointerY < rect.y + rect.height;
}

void renderHeader(GameplayScreenRuntime &context, const Rect &root, const PlaythroughStatistics &statistics)
{
    const PlaythroughStatistics::Header &header = statistics.header();
    const PlaythroughTrackingInfo &info = statistics.lifetimeInfo();
    std::string title = Engine::tr("Begun {date}", {{"date", dateText(header.createdUtc)}});
    std::string detail;

    if (!header.startWorld.empty())
    {
        detail = Engine::tr("{world} start", {{"world", upperText(header.startWorld)}});
    }

    if (!header.ruleset.empty() && header.ruleset != "standard")
    {
        detail += (detail.empty() ? "" : "  -  ") + upperText(header.ruleset);
    }

    if (!header.difficulty.empty())
    {
        // The difficulty's id ("normal") capitalized is its English name.
        detail += (detail.empty() ? "" : "  -  ") + Engine::tr(capitalizedText(header.difficulty));
    }

    if (info.partial)
    {
        title = Engine::tr("Statistics");
        detail = Engine::tr("Tracked since {date}: earlier play predates them",
            {{"date", dateText(info.trackingSinceUtc)}});
    }

    drawText(context, root, "Create", 1.0f, IvoryColor, title, 22.0f, 14.0f, 260.0f);
    const float titleWidth = textWidth(context, "Create", title, 1.0f);
    drawText(context, root, "SMALLNUM", SmallScale, info.partial ? LowColor : MutedColor, detail,
        22.0f + titleWidth + 10.0f, 17.0f, 600.0f - titleWidth - 150.0f);

    const std::string played = formatDuration(statistics.lifetime().playedSeconds);
    drawText(context, root, "Create", 1.0f, GoldColor, played, 470.0f, 14.0f, 150.0f, UiLayoutManager::TextAlignX::Right);
    const float playedWidth = textWidth(context, "Create", played, 1.0f);
    drawText(context, root, "Create", 1.0f, IvoryColor, Engine::tr("Played"), 470.0f, 14.0f,
        150.0f - playedWidth - 7.0f,
        UiLayoutManager::TextAlignX::Right);
}

void renderOverview(GameplayScreenRuntime &context, const Rect &root, const PlaythroughStatistics &statistics,
    float gameMinutes, std::vector<InspectableRect> &inspectables, const GameplayInputFrame *pInput, bool inspecting)
{
    std::vector<Group> second;
    std::vector<Group> third;
    const std::vector<Group> first = overviewGroups(statistics, gameMinutes, second, third);
    const std::array<const std::vector<Group> *, 3> columns = {&first, &second, &third};
    const float columnWidth = (640.0f - 2 * ColumnsLeft - (ColumnCount - 1) * ColumnGap) / ColumnCount;

    for (size_t column = 0; column < columns.size(); ++column)
    {
        const float columnX = ColumnsLeft + float(column) * (columnWidth + ColumnGap);
        float y = ColumnsTop;
        const std::vector<Group> &groups = *columns[column];

        for (size_t groupIndex = 0; groupIndex < groups.size(); ++groupIndex)
        {
            const Group &group = groups[groupIndex];
            const bool last = groupIndex + 1 == groups.size();
            const float naturalHeight = 2 * GroupPadY + HeadingHeight + float(group.rows.size()) * RowHeight;
            const float height = last ? std::max(naturalHeight, ColumnsBottom - y) : naturalHeight;
            renderGroupFrame(context, toScreen(root, columnX, y, columnWidth, height));
            drawText(context, root, "Arrus", HeadingScale, GoldColor, group.heading, columnX + GroupPadX,
                y + GroupPadY, columnWidth - 2 * GroupPadX);
            float rowY = y + GroupPadY + HeadingHeight;

            for (const Row &entry : group.rows)
            {
                const Rect rowRect = toScreen(root, columnX + GroupPadX - 3.0f, rowY, columnWidth - 2 * GroupPadX + 6.0f,
                    RowHeight);

                if (inspecting && pointerInside(rowRect, pInput))
                {
                    fillRect(context, rowRect, RowHighlightColor);
                }

                const float innerWidth = columnWidth - 2 * GroupPadX;
                const float valueWidth = textWidth(context, "Lucida", entry.value, RowScale);
                drawText(context, root, "Lucida", RowScale, entry.valueColor, entry.value, columnX + GroupPadX, rowY + 1.0f,
                    innerWidth, UiLayoutManager::TextAlignX::Right);
                drawText(context, root, "Lucida", RowScale, IvoryColor, entry.label, columnX + GroupPadX, rowY + 1.0f,
                    std::max(10.0f, innerWidth - valueWidth - 6.0f));
                inspectables.push_back({rowRect, entry.breakdown});
                rowY += RowHeight;
            }

            y += height + GroupGap;
        }
    }
}

void renderPartyTab(GameplayScreenRuntime &context, const Rect &root, const PlaythroughStatistics &statistics,
    const Party &party)
{
    const PlaythroughCounters &t = statistics.timeline();
    std::vector<uint64_t> ids;
    std::vector<std::string> names;

    for (const Character &member : party.members())
    {
        ids.push_back(member.statsMemberId);
        names.push_back(member.name);
    }

    if (ids.empty())
    {
        return;
    }

    struct PartyRow
    {
        std::string_view label;
        uint64_t PlaythroughMemberCounters::*pField = nullptr;
        bool share = false;
        bool lowerIsBetter = false;
        bool lifetime = false; // Losses, as on the Overview.
    };

    static const std::array<PartyRow, 10> Rows = {{
        {Engine::trNoop("Kills"), &PlaythroughMemberCounters::kills, false, false},
        {Engine::trNoop("Damage dealt"), &PlaythroughMemberCounters::damageDealt, false, false},
        {Engine::trNoop("Share"), &PlaythroughMemberCounters::damageDealt, true, false},
        {Engine::trNoop("Largest hit"), &PlaythroughMemberCounters::largestHit, false, false},
        {Engine::trNoop("Damage taken"), &PlaythroughMemberCounters::damageTaken, false, true},
        {Engine::trNoop("Spells cast"), &PlaythroughMemberCounters::spellsCast, false, false},
        {Engine::trNoop("Healing given"), &PlaythroughMemberCounters::healingGiven, false, false},
        {Engine::trNoop("Knocked out"), &PlaythroughMemberCounters::knockouts, false, true, true},
        {Engine::trNoop("Deaths"), &PlaythroughMemberCounters::deaths, false, true, true},
        {Engine::trNoop("Experience"), &PlaythroughMemberCounters::experience, false, false},
    }};

    const float left = ColumnsLeft;
    const float top = ColumnsTop - 2.0f;
    const float labelWidth = 112.0f;
    const float cellWidth = std::min(100.0f, (640.0f - 2 * ColumnsLeft - labelWidth) / float(ids.size()));
    const float tableWidth = labelWidth + cellWidth * float(ids.size());
    const float rowHeight = 22.0f;
    const float tableHeight = rowHeight * float(Rows.size() + 1);
    renderGroupFrame(context, toScreen(root, left, top, tableWidth, tableHeight));

    for (size_t column = 0; column < ids.size(); ++column)
    {
        const float x = left + labelWidth + float(column) * cellWidth;
        fillRect(context, toScreen(root, x, top + 4.0f, 1.0f / root.scale, tableHeight - 8.0f), GroupBorderColor);
        drawText(context, root, "Arrus", HeadingScale, GoldColor, names[column], x + 4.0f, top + 4.0f, cellWidth - 10.0f,
            UiLayoutManager::TextAlignX::Right);
    }

    const uint64_t damageTotal = t.damageDealtTotal();

    for (size_t rowIndex = 0; rowIndex < Rows.size(); ++rowIndex)
    {
        const PartyRow &partyRow = Rows[rowIndex];
        const float y = top + rowHeight * float(rowIndex + 1);
        fillRect(context, toScreen(root, left + 4.0f, y, tableWidth - 8.0f, 1.0f / root.scale), GroupInnerColor);
        drawText(context, root, "Arrus", HeadingScale, IvoryColor, Engine::tr(partyRow.label), left + 8.0f, y + 3.0f,
            labelWidth - 10.0f);
        const PlaythroughCounters &counters = partyRow.lifetime ? statistics.lifetime() : t;
        uint64_t best = 0;

        for (uint64_t id : ids)
        {
            const PlaythroughMemberCounters *pCounters = memberCounters(counters, id);
            best = std::max(best, pCounters != nullptr ? pCounters->*partyRow.pField : 0);
        }

        for (size_t column = 0; column < ids.size(); ++column)
        {
            const PlaythroughMemberCounters *pCounters = memberCounters(counters, ids[column]);
            const uint64_t value = pCounters != nullptr ? pCounters->*partyRow.pField : 0;
            const float x = left + labelWidth + float(column) * cellWidth;

            if (partyRow.share)
            {
                const std::string percent = percentText(double(value), double(damageTotal));
                const float barWidth = cellWidth - 46.0f;
                fillRect(context, toScreen(root, x + 8.0f, y + 9.0f, barWidth, 4.0f), TrackColor);
                fillRect(context, toScreen(root, x + 8.0f, y + 9.0f, best > 0 ? barWidth * float(value) / float(best) : 0.0f,
                    4.0f), ShareColor);
                drawText(context, root, "SMALLNUM", SmallScale, MutedColor, percent.empty() ? "-" : percent, x + 4.0f,
                    y + 5.0f, cellWidth - 10.0f, UiLayoutManager::TextAlignX::Right);
                continue;
            }

            const uint32_t color = value == 0 ? DimColor
                : value == best && !partyRow.lowerIsBetter ? GoldColor
                : IvoryColor;
            drawText(context, root, "Lucida", RowScale, color, value == 0 ? "-" : formatCount(value), x + 4.0f, y + 3.0f,
                cellWidth - 10.0f, UiLayoutManager::TextAlignX::Right);
        }
    }

    // Former members and the party's allies, so the columns add up to the Overview's totals.
    std::string formerMembers;
    uint64_t memberKills = 0;

    for (const auto &[key, counters] : t.members)
    {
        memberKills += counters.kills;
        const bool current = std::any_of(ids.begin(), ids.end(),
            [&key](uint64_t id) { return PlaythroughStatistics::memberKey(id) == key; });

        if (!current && (counters.kills > 0 || counters.experience > 0))
        {
            formerMembers += (formerMembers.empty() ? "" : ", ")
                + Engine::tr("{name} ({kills} kills)",
                    {{"name", counters.name}, {"kills", formatCount(counters.kills)}});
        }
    }

    const uint64_t otherKills = t.kills > memberKills ? t.kills - memberKills : 0;
    std::string footer =
        formerMembers.empty() ? std::string() : Engine::tr("Former members: {members}", {{"members", formerMembers}});

    if (otherKills > 0)
    {
        footer += (footer.empty() ? "" : ".  ")
            + Engine::tr("Allies and traps: {kills} kills", {{"kills", formatCount(otherKills)}});
    }

    drawText(context, root, "SMALLNUM", SmallScale, DimColor, footer, left + 4.0f, top + tableHeight + 6.0f,
        640.0f - 2 * ColumnsLeft - 8.0f);
}

// This session in the party frame's right panel.
void renderSessionPanel(GameplayScreenRuntime &context, const Rect &root, const PlaythroughStatistics &statistics)
{
    const PlaythroughStatistics::SessionCounters &session = statistics.session();
    const float x = 497.0f;
    const float width = 113.0f;
    float y = 383.0f;
    drawText(context, root, "Create", 0.8f, GoldColor, Engine::tr("This session"), x, y, width,
        UiLayoutManager::TextAlignX::Center);
    y += 18.0f;
    const std::array<std::pair<std::string, std::string>, 4> lines = {{
        {Engine::tr("Time"), formatDuration(session.playedSeconds)},
        {Engine::tr("Kills"), formatCount(session.kills)},
        {Engine::tr("Experience"), formatCount(session.experience)},
        {Engine::tr("Deaths"), formatCount(session.deaths)},
    }};

    for (const auto &[label, value] : lines)
    {
        drawText(context, root, "SMALLNUM", SmallScale, MutedColor, label, x, y, width);
        drawText(context, root, "SMALLNUM", SmallScale, IvoryColor, value, x, y, width,
            UiLayoutManager::TextAlignX::Right);
        y += 15.0f;
    }
}

void renderBreakdownPopup(GameplayScreenRuntime &context, const Rect &root, const Breakdown &breakdown,
    const Rect &anchor)
{
    constexpr float PadX = 20.0f;
    constexpr float ColumnGap = 12.0f;
    constexpr float BarLabelWidth = 62.0f;
    constexpr float BarWidth = 70.0f;
    constexpr float PadTop = 16.0f;
    constexpr float PadBottom = 18.0f;
    constexpr float LineHeight = 15.0f;
    constexpr float SectionHeight = 17.0f;
    constexpr float RuleHeight = 9.0f;
    const float fontScale = SmallScale;

    // As wide as the widest line needs: label, value and the third column (percent, level, day) right-aligned.
    float labelMax = 0.0f;
    float valueMax = 0.0f;
    float extraMax = 0.0f;
    float barValueMax = 0.0f;

    for (const BreakdownLine &line : breakdown.lines)
    {
        if (line.kind == BreakdownLine::Kind::Row)
        {
            labelMax = std::max(labelMax, textWidth(context, "SMALLNUM", line.label, fontScale));
            valueMax = std::max(valueMax, textWidth(context, "SMALLNUM", line.value, fontScale));
        }
        else if (line.kind == BreakdownLine::Kind::Bar)
        {
            barValueMax = std::max(barValueMax, textWidth(context, "SMALLNUM", line.value, fontScale));
        }

        if (line.kind == BreakdownLine::Kind::Row || line.kind == BreakdownLine::Kind::Bar)
        {
            extraMax = std::max(extraMax, textWidth(context, "SMALLNUM", line.extra, fontScale));
        }
    }

    const float extraColumn = extraMax > 0.0f ? extraMax + ColumnGap : 0.0f;
    const float rowsWidth = std::max(labelMax + ColumnGap + valueMax,
        barValueMax > 0.0f ? BarLabelWidth + BarWidth + ColumnGap + barValueMax : 0.0f) + extraColumn;
    const float titleWidth = textWidth(context, "Create", breakdown.title, 1.0f);
    const float PopupWidth = std::clamp(std::max(rowsWidth, titleWidth) + 2 * PadX, 240.0f, 460.0f);
    const float innerWidth = PopupWidth - 2 * PadX;

    // Notes wrap; everything else is one line.
    std::vector<std::vector<std::string>> wrappedNotes;
    float height = PadTop + 22.0f + PadBottom;

    for (const BreakdownLine &line : breakdown.lines)
    {
        switch (line.kind)
        {
        case BreakdownLine::Kind::Row:
        case BreakdownLine::Kind::Bar:
            height += LineHeight;
            break;
        case BreakdownLine::Kind::Section:
            height += SectionHeight;
            break;
        case BreakdownLine::Kind::Rule:
            height += RuleHeight;
            break;
        case BreakdownLine::Kind::Note:
            wrappedNotes.push_back(context.wrapHudTextToWidth("SMALLNUM", line.label, innerWidth / fontScale));
            height += LineHeight * float(wrappedNotes.back().size());
            break;
        }
    }

    // Below the row when it fits, else above it, else beside its column; never over the row itself.
    const float anchorX = (anchor.x - root.x) / root.scale;
    const float anchorY = (anchor.y - root.y) / root.scale;
    const float anchorWidth = anchor.width / root.scale;
    const float anchorHeight = anchor.height / root.scale;
    float x = std::clamp(anchorX + anchorWidth * 0.5f - PopupWidth * 0.5f, 4.0f, 636.0f - PopupWidth);
    float y = anchorY + anchorHeight + 4.0f;

    if (y + height > 476.0f)
    {
        y = anchorY - height - 4.0f;
    }

    if (y < 4.0f)
    {
        x = anchorX + anchorWidth + 12.0f + PopupWidth <= 636.0f ? anchorX + anchorWidth + 12.0f
                                                                  : std::max(4.0f, anchorX - 12.0f - PopupWidth);
        y = std::clamp(anchorY + anchorHeight * 0.5f - height * 0.5f, 4.0f, std::max(4.0f, 476.0f - height));
    }

    GameplayUiSkin::renderPanel(context, toScreen(root, x, y, PopupWidth, height));
    drawText(context, root, "Create", 1.0f, GoldColor, breakdown.title, x + PadX, y + PadTop, innerWidth,
        UiLayoutManager::TextAlignX::Center);
    float lineY = y + PadTop + 22.0f;
    size_t noteIndex = 0;
    const float valueRight = innerWidth - extraColumn;

    for (const BreakdownLine &line : breakdown.lines)
    {
        switch (line.kind)
        {
        case BreakdownLine::Kind::Row:
        {
            const bool hasExtra = !line.extra.empty();
            const float valueSpan = hasExtra ? valueRight : innerWidth;
            const float valueWidth = textWidth(context, "SMALLNUM", line.value, fontScale);
            drawText(context, root, "SMALLNUM", fontScale, IvoryColor, line.value, x + PadX, lineY, valueSpan,
                UiLayoutManager::TextAlignX::Right);
            drawText(context, root, "SMALLNUM", fontScale, IvoryColor, line.label, x + PadX, lineY,
                std::max(10.0f, valueSpan - valueWidth - 8.0f));

            if (hasExtra)
            {
                drawText(context, root, "SMALLNUM", fontScale, MutedColor, line.extra, x + PadX, lineY, innerWidth,
                    UiLayoutManager::TextAlignX::Right);
            }

            lineY += LineHeight;
            break;
        }
        case BreakdownLine::Kind::Bar:
        {
            const float labelWidth = BarLabelWidth;
            const float barWidth = BarWidth;
            drawText(context, root, "SMALLNUM", fontScale, IvoryColor, line.label, x + PadX, lineY, labelWidth);
            fillRect(context, toScreen(root, x + PadX + labelWidth, lineY + 5.0f, barWidth, 4.0f), TrackColor);
            fillRect(context, toScreen(root, x + PadX + labelWidth, lineY + 5.0f, barWidth * line.fraction, 4.0f),
                line.colorAbgr);
            drawText(context, root, "SMALLNUM", fontScale, IvoryColor, line.value, x + PadX, lineY, valueRight,
                UiLayoutManager::TextAlignX::Right);
            drawText(context, root, "SMALLNUM", fontScale, MutedColor, line.extra, x + PadX, lineY, innerWidth,
                UiLayoutManager::TextAlignX::Right);
            lineY += LineHeight;
            break;
        }
        case BreakdownLine::Kind::Section:
            drawText(context, root, "Create", 0.8f, GoldColor, line.label, x + PadX, lineY + 2.0f, innerWidth);
            lineY += SectionHeight;
            break;
        case BreakdownLine::Kind::Rule:
            GameplayUiSkin::renderTexture(context, "obsidian_value_divider",
                toScreen(root, x + PadX, lineY + 4.0f, innerWidth, 1.0f / root.scale));
            lineY += RuleHeight;
            break;
        case BreakdownLine::Kind::Note:
            for (const std::string &text : wrappedNotes[noteIndex])
            {
                drawText(context, root, "SMALLNUM", fontScale, MutedColor, text, x + PadX, lineY, innerWidth);
                lineY += LineHeight;
            }

            ++noteIndex;
            break;
        }
    }
}
}

std::string formatCount(uint64_t value)
{
    std::string digits = std::to_string(value);
    std::string text;

    for (size_t index = 0; index < digits.size(); ++index)
    {
        if (index > 0 && (digits.size() - index) % 3 == 0)
        {
            text += ',';
        }

        text += digits[index];
    }

    return text;
}

std::string formatDuration(double seconds)
{
    const uint64_t total = uint64_t(std::max(0.0, seconds));
    char text[32] = {};
    std::snprintf(text, sizeof(text), "%llu:%02llu:%02llu", static_cast<unsigned long long>(total / 3600),
        static_cast<unsigned long long>(total / 60 % 60), static_cast<unsigned long long>(total % 60));
    return text;
}

Breakdown buildBreakdown(const std::string &id, const PlaythroughStatistics &statistics, const Party *pParty,
    const GameplayScreenRuntime *pContext)
{
    const PlaythroughCounters &t = statistics.timeline();
    const PlaythroughCounters &l = statistics.lifetime();
    const auto count = [](uint64_t value) { return formatCount(value); };
    const auto undone = [&](uint64_t lifetimeValue)
    {
        return row(Engine::tr("Including undone play"), count(lifetimeValue));
    };
    // The losses show the lifetime; their breakdowns end with the timeline instead.
    const auto inTimeline = [&](uint64_t timelineValue)
    {
        return row(Engine::tr("In this timeline"), count(timelineValue));
    };
    Breakdown breakdown;
    std::vector<BreakdownLine> &lines = breakdown.lines;

    if (id == "played")
    {
        breakdown.title = Engine::tr("Time played");
        const double sessions = double(std::max<uint64_t>(1, l.sessions));
        lines.push_back(row(Engine::tr("This session"), formatDuration(statistics.session().playedSeconds)));
        lines.push_back(row(Engine::tr("Longest session"), formatDuration(l.longestSessionSeconds)));
        lines.push_back(row(Engine::tr("Average session"), formatDuration(l.playedSeconds / sessions)));

        if (!l.playedSecondsByWorld.empty())
        {
            lines.push_back(section(Engine::tr("By world")));

            for (const auto &[world, seconds] : topEntries(l.playedSecondsByWorld, 6))
            {
                lines.push_back(row(upperText(world), formatDuration(seconds), percentText(seconds, l.playedSeconds)));
            }
        }

        lines.push_back(rule());
        lines.push_back(row(Engine::tr("In this timeline"), formatDuration(t.playedSeconds)));
        lines.push_back(row(Engine::tr("Undone by loading"),
            formatDuration(std::max(0.0, l.playedSeconds - t.playedSeconds))));
        lines.push_back(note(Engine::tr("Counts while a game runs in the window in front, without the pause menu, and "
                                        "stops after five minutes without input. First played {date}.",
            {{"date", dateText(statistics.header().createdUtc)}})));
    }
    else if (id == "turnbased")
    {
        breakdown.title = Engine::tr("Turn-based combat");
        lines.push_back(row(Engine::tr("Time in turn-based"), formatDuration(l.turnBasedSeconds),
            percentText(l.turnBasedSeconds, l.playedSeconds)));
        lines.push_back(row(Engine::tr("Fights"), count(l.turnBasedFights)));
        lines.push_back(row(Engine::tr("Turns"), count(l.turnBasedTurns)));
        lines.push_back(row(Engine::tr("Kills in turn-based"), count(t.turnBasedKills),
            percentText(double(t.turnBasedKills), double(t.kills))));
    }
    else if (id == "xp")
    {
        breakdown.title = Engine::tr("Experience earned");
        const double total = double(t.experienceTotal());
        lines.push_back(row(Engine::tr("Monsters"), count(t.experience[size_t(ExperienceReason::Monster)]),
            percentText(double(t.experience[size_t(ExperienceReason::Monster)]), total)));
        lines.push_back(row(Engine::tr("Quests and events"), count(t.experience[size_t(ExperienceReason::Event)]),
            percentText(double(t.experience[size_t(ExperienceReason::Event)]), total)));
        lines.push_back(row(Engine::tr("Other"), count(t.experience[size_t(ExperienceReason::Other)]),
            percentText(double(t.experience[size_t(ExperienceReason::Other)]), total)));
        lines.push_back(note(Engine::tr("Other: wells, fountains, books and potions.")));
        lines.push_back(rule());
        lines.push_back(row(Engine::tr("Largest single award"), count(t.largestAward)));
        lines.push_back(undone(l.experienceTotal()));
    }
    else if (id == "levels")
    {
        breakdown.title = Engine::tr("Levels gained");

        if (pParty != nullptr)
        {
            for (const Character &member : pParty->members())
            {
                const PlaythroughMemberCounters *pCounters = memberCounters(t, member.statsMemberId);
                lines.push_back(row(member.name, count(pCounters != nullptr ? pCounters->levelsGained : 0),
                    Engine::tr("level {level}", {{"level", member.level}})));
            }
        }

        lines.push_back(rule());
        lines.push_back(row(Engine::tr("Training cost"), count(t.goldSpent[size_t(GoldReason::Training)])));
    }
    else if (id == "saves")
    {
        breakdown.title = Engine::tr("Saves and loads");
        lines.push_back(section(Engine::tr("Saves")));
        lines.push_back(row(Engine::tr("Quicksaves"), count(l.quickSaves)));
        lines.push_back(row(Engine::tr("Autosaves"), count(l.autoSaves)));
        lines.push_back(row(Engine::tr("Save slots"), count(l.namedSaves)));
        lines.push_back(section(Engine::tr("Loads")));
        lines.push_back(row(Engine::tr("Quickloads"), count(l.quickLoads)));
        lines.push_back(row(Engine::tr("From the Load screen"), count(l.menuLoads)));
        lines.push_back(row(Engine::tr("After a party wipe"), count(l.loadsAfterWipe)));
    }
    else if (id == "kills")
    {
        breakdown.title = Engine::tr("Monsters killed");
        const double total = double(t.kills);
        uint64_t credited = 0;
        lines.push_back(section(Engine::tr("By method")));
        static constexpr std::array<std::string_view, size_t(StatKillMethod::Count)> Methods = {
            Engine::trNoop("Melee"), Engine::trNoop("Missiles"), Engine::trNoop("Spells")};

        for (size_t method = 0; method < Methods.size(); ++method)
        {
            credited += t.killsByMethod[method];
            lines.push_back(row(Engine::tr(Methods[method]), count(t.killsByMethod[method]),
                percentText(double(t.killsByMethod[method]), total)));
        }

        const uint64_t other = t.kills > credited ? t.kills - credited : 0;
        lines.push_back(row(Engine::tr("Allies and traps"), count(other), percentText(double(other), total)));

        if (!t.killsByMonster.empty())
        {
            lines.push_back(section(Engine::tr("Most slain")));

            for (const auto &[monster, kills] : topEntries(t.killsByMonster, 5))
            {
                lines.push_back(row(recordedText(monster), count(kills)));
            }
        }

        lines.push_back(rule());

        if (!t.strongestKill.empty())
        {
            lines.push_back(row(Engine::tr("Strongest foe"), recordedText(t.strongestKill),
                Engine::tr("level {level}", {{"level", t.strongestKillLevel}})));
        }

        lines.push_back(undone(l.kills));
    }
    else if (id == "damage")
    {
        breakdown.title = Engine::tr("Damage dealt");
        const uint64_t total = t.damageDealtTotal();
        std::vector<size_t> schools;

        for (size_t school = 0; school < StatDamageSchoolCount; ++school)
        {
            if (t.damageDealtBySchool[school] > 0)
            {
                schools.push_back(school);
            }
        }

        std::sort(schools.begin(), schools.end(), [&t](size_t left, size_t right)
            { return t.damageDealtBySchool[left] > t.damageDealtBySchool[right]; });
        const uint64_t largest = schools.empty() ? 1 : t.damageDealtBySchool[schools.front()];

        for (size_t school : schools)
        {
            BreakdownLine bar = row(Engine::tr(SchoolNames[school]), count(t.damageDealtBySchool[school]),
                percentText(double(t.damageDealtBySchool[school]), double(total)));
            bar.kind = BreakdownLine::Kind::Bar;
            bar.fraction = float(double(t.damageDealtBySchool[school]) / double(largest));
            bar.colorAbgr = SchoolColors[school];
            lines.push_back(bar);
        }

        lines.push_back(rule());
        lines.push_back(row(Engine::tr("Critical hits"), count(t.criticalHits)));
        lines.push_back(undone(l.damageDealtTotal()));
    }
    else if (id == "taken")
    {
        breakdown.title = Engine::tr("Damage taken");
        const double total = double(t.damageTakenTotal());
        static constexpr std::array<std::string_view, size_t(StatDamageTakenKind::Count)> Kinds = {
            Engine::trNoop("Melee"), Engine::trNoop("Missiles"), Engine::trNoop("Spells"),
            Engine::trNoop("Falls, traps, water")};

        for (size_t kind = 0; kind < Kinds.size(); ++kind)
        {
            lines.push_back(row(Engine::tr(Kinds[kind]), count(t.damageTaken[kind]),
                percentText(double(t.damageTaken[kind]), total)));
        }

        lines.push_back(rule());

        if (t.largestHitTaken.amount > 0)
        {
            lines.push_back(row(Engine::tr("Largest hit taken"), count(t.largestHitTaken.amount)));
            lines.push_back(row(t.largestHitTaken.source.empty() ? "-" : recordedText(t.largestHitTaken.source),
                t.largestHitTaken.member));
        }

        lines.push_back(undone(l.damageTakenTotal()));
    }
    else if (id == "biggest")
    {
        breakdown.title = Engine::tr("Largest hits");

        for (const PlaythroughHitRecord &hit : t.largestHits)
        {
            lines.push_back(row(count(hit.amount), hit.member + ", " + recordedText(hit.source),
                recordedText(hit.target)));
        }

        if (t.largestHits.empty())
        {
            lines.push_back(note(Engine::tr("No hits yet.")));
        }
    }
    else if (id == "spells")
    {
        breakdown.title = Engine::tr("Spells cast");

        if (!t.spellCasts.empty())
        {
            lines.push_back(section(Engine::tr("Most cast")));

            for (const auto &[spell, casts] : topEntries(t.spellCasts, 5))
            {
                lines.push_back(row(recordedText(spell), count(casts)));
            }
        }

        lines.push_back(rule());
        lines.push_back(row(Engine::tr("Cast from scrolls"), count(t.scrollCasts)));
        lines.push_back(row(Engine::tr("Spell points spent"), count(t.manaSpent)));
        lines.push_back(row(Engine::tr("Healing given"), count(t.healingGiven)));
        lines.push_back(undone(l.spellsCast));
    }
    else if (id == "deaths")
    {
        breakdown.title = Engine::tr("Deaths");

        if (pParty != nullptr && !pParty->members().empty())
        {
            lines.push_back(section(Engine::tr("By member")));

            for (const Character &member : pParty->members())
            {
                const PlaythroughMemberCounters *pCounters = memberCounters(l, member.statsMemberId);
                const uint64_t eradications = pCounters != nullptr ? pCounters->eradications : 0;
                lines.push_back(row(member.name, count(pCounters != nullptr ? pCounters->deaths : 0),
                    eradications > 0 ? Engine::tr("{count} erad.", {{"count", count(eradications)}}) : std::string()));
            }
        }

        if (!l.deathCauses.empty())
        {
            lines.push_back(section(Engine::tr("Deadliest")));

            for (const auto &[cause, deaths] : topEntries(l.deathCauses, 3))
            {
                lines.push_back(row(Engine::Utf8::capitalizedFirst(recordedText(cause)), count(deaths)));
            }
        }

        if (!l.deathLog.empty())
        {
            lines.push_back(section(Engine::tr("Latest")));

            for (size_t index = 0; index < std::min<size_t>(3, l.deathLog.size()); ++index)
            {
                const PlaythroughLogEntry &entry = l.deathLog[l.deathLog.size() - 1 - index];
                lines.push_back(row(entry.member, Engine::Utf8::capitalizedFirst(recordedText(entry.cause)),
                    dayText(entry.day)));
            }
        }

        lines.push_back(rule());
        lines.push_back(inTimeline(t.deaths + t.eradications));
    }
    else if (id == "wipes")
    {
        breakdown.title = Engine::tr("Party wipes");

        for (size_t index = 0; index < std::min<size_t>(4, l.wipeLog.size()); ++index)
        {
            const PlaythroughLogEntry &entry = l.wipeLog[l.wipeLog.size() - 1 - index];
            lines.push_back(row(mapName(pContext, entry.map), std::string(), dayText(entry.day)));
        }

        lines.push_back(rule());
        lines.push_back(row(Engine::tr("Gold lost"), count(l.goldSpent[size_t(GoldReason::Defeat)])));
        lines.push_back(row(Engine::tr("Loads after a wipe"), count(l.loadsAfterWipe)));
        lines.push_back(inTimeline(t.partyWipes));
    }
    else if (id == "temple")
    {
        breakdown.title = Engine::tr("Temples");
        lines.push_back(row(Engine::tr("Healings"), count(l.templeHeals)));
        lines.push_back(row(Engine::tr("Donations"), count(l.donations)));
        lines.push_back(row(Engine::tr("Gold paid"), count(l.goldSpent[size_t(GoldReason::Temple)])));
        lines.push_back(rule());
        lines.push_back(inTimeline(t.templeHeals));
    }
    else if (id == "tp")
    {
        breakdown.title = Engine::tr("Town Portal");

        if (!t.townPortalDestinations.empty())
        {
            lines.push_back(section(Engine::tr("Most used")));

            for (const auto &[destination, uses] : topEntries(t.townPortalDestinations, 4))
            {
                lines.push_back(row(recordedText(destination), count(uses)));
            }

            lines.push_back(rule());
        }

        lines.push_back(undone(l.townPortals));
    }
    else if (id == "lloyd")
    {
        breakdown.title = Engine::tr("Lloyd's Beacon");
        lines.push_back(row(Engine::tr("Recalls"), count(t.lloydRecalls)));
        lines.push_back(row(Engine::tr("Beacons set"), count(t.lloydSets)));
    }
    else if (id == "travel")
    {
        breakdown.title = Engine::tr("Coach and ship");
        lines.push_back(row(Engine::tr("Coach trips"), count(t.coachTrips)));
        lines.push_back(row(Engine::tr("Ship voyages"), count(t.shipTrips)));
        lines.push_back(row(Engine::tr("Days travelled"), count(uint64_t(std::llround(t.travelDays)))));
        lines.push_back(row(Engine::tr("Gold paid"), count(t.goldSpent[size_t(GoldReason::Travel)])));
    }
    else if (id == "maps")
    {
        breakdown.title = Engine::tr("Maps visited");
        lines.push_back(row(Engine::tr("Maps"), count(t.mapsVisited.size())));
        lines.push_back(note(Engine::tr("A map counts once, the first time the party enters it.")));
    }
    else if (id == "chests")
    {
        breakdown.title = Engine::tr("Chests opened");
        lines.push_back(row(Engine::tr("Chests"), count(t.chestsOpened.size())));
        lines.push_back(note(Engine::tr("A chest counts once, however often it is opened.")));
    }
    else if (id == "looted")
    {
        breakdown.title = Engine::tr("Gold looted");
        const double total = double(t.goldLooted());
        const std::array<std::pair<std::string_view, GoldReason>, 4> sources = {{
            {Engine::trNoop("Corpses"), GoldReason::LootCorpse},
            {Engine::trNoop("Chests"), GoldReason::LootChest},
            {Engine::trNoop("Ground"), GoldReason::LootGround},
            {Engine::trNoop("Quests and events"), GoldReason::Event},
        }};

        for (const auto &[label, reason] : sources)
        {
            lines.push_back(row(Engine::tr(label), count(t.goldGained[size_t(reason)]),
                percentText(double(t.goldGained[size_t(reason)]), total)));
        }

        lines.push_back(rule());
        lines.push_back(row(Engine::tr("Earned selling items"), count(t.goldGained[size_t(GoldReason::Sold)])));
        lines.push_back(undone(l.goldLooted()));
    }
    else if (id == "spent")
    {
        breakdown.title = Engine::tr("Gold spent");
        const double total = double(t.goldSpentTotal());
        const std::array<std::pair<std::string_view, GoldReason>, 7> purposes = {{
            {Engine::trNoop("Training"), GoldReason::Training},
            {Engine::trNoop("Shops"), GoldReason::Shop},
            {Engine::trNoop("Guilds and lessons"), GoldReason::Guild},
            {Engine::trNoop("Temples"), GoldReason::Temple},
            {Engine::trNoop("Travel"), GoldReason::Travel},
            {Engine::trNoop("Taverns"), GoldReason::Tavern},
            {Engine::trNoop("Other"), GoldReason::Other},
        }};

        for (const auto &[label, reason] : purposes)
        {
            lines.push_back(row(Engine::tr(label), count(t.goldSpent[size_t(reason)]),
                percentText(double(t.goldSpent[size_t(reason)]), total)));
        }

        lines.push_back(rule());
        lines.push_back(row(Engine::tr("Banked"), count(t.goldSpent[size_t(GoldReason::Bank)])));
    }
    else if (id == "integrity")
    {
        const PlaythroughTrackingInfo &integrity = statistics.lifetimeInfo();
        breakdown.title = integrity.assists.empty() && !integrity.unverified && !integrity.restoredOlder
            ? Engine::tr("Development build")
            : Engine::tr("Not a clean playthrough");

        if (!integrity.assists.empty())
        {
            lines.push_back(section(Engine::tr("Assisted")));

            for (const auto &[reason, record] : integrity.assists)
            {
                // Assist reasons are the English the game records ("immortal").
                lines.push_back(row(Engine::Utf8::capitalizedFirst(Engine::tr(reason)),
                    Engine::trn("{count} session", "{count} sessions", record.sessions,
                        {{"count", count(record.sessions)}}),
                    Engine::tr("from {day}", {{"day", dayText(record.firstDay)}})));
            }

            const auto console = integrity.assists.find("debug console");

            if (console != integrity.assists.end() && !console->second.commands.empty())
            {
                lines.push_back(section(Engine::tr("Console commands")));

                for (const auto &[command, times] : topEntries(console->second.commands, 8))
                {
                    lines.push_back(
                        row(command, Engine::trn("{count} time", "{count} times", times, {{"count", count(times)}})));
                }
            }
        }

        if (integrity.unverified || integrity.restoredOlder || integrity.developmentBuild)
        {
            lines.push_back(rule());
        }

        if (integrity.unverified)
        {
            lines.push_back(note(Engine::tr("Changed outside the game: a statistics file or a save's statistics "
                                            "failed their check, so the record restarted from what could be trusted.")));
        }

        if (integrity.restoredOlder)
        {
            lines.push_back(note(Engine::tr("Restored from an older copy: the statistics file was older than a save "
                                            "loaded with it.")));
        }

        if (integrity.developmentBuild)
        {
            lines.push_back(
                note(Engine::tr("Development build: recorded by a build of the game made without the release key.")));
        }
    }
    else if (id == "artifacts")
    {
        breakdown.title = Engine::tr("Artifacts found");

        for (size_t index = 0; index < std::min<size_t>(8, t.artifactsFound.size()); ++index)
        {
            const PlaythroughArtifactRecord &artifact = t.artifactsFound[index];
            lines.push_back(row(recordedText(artifact.name), std::string(), dayText(artifact.day)));
        }

        if (t.artifactsFound.size() > 8)
        {
            lines.push_back(note(Engine::tr("and {count} more", {{"count", t.artifactsFound.size() - 8}})));
        }

        if (t.artifactsFound.empty())
        {
            lines.push_back(note(Engine::tr("None yet.")));
        }
    }

    return breakdown;
}

void render(GameplayScreenRuntime &context, int width, int height)
{
    const Party *pParty = context.partyReadOnly();

    if (pParty == nullptr || width <= 0 || height <= 0)
    {
        return;
    }

    const PlaythroughStatistics &statistics = context.playthroughStatistics();
    const GameplayUiController::QuickReferenceScreenState &screen = context.quickReferenceScreenStateReadOnly();
    context.prepareHudView(width, height);
    context.renderViewportSidePanels(width, height, "obsidian_reading_surface");
    const Rect root = rootRect(context, width, height);
    GameplayUiSkin::renderSurface(context, toScreen(root, 0.0f, 0.0f, 640.0f, SurfaceHeight));

    if (!statistics.active())
    {
        drawText(context, root, "Create", 1.0f, MutedColor, Engine::tr("No statistics for this game."), 0.0f, 160.0f,
            640.0f,
            UiLayoutManager::TextAlignX::Center);
    }
    else
    {
        const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
        const bool inspecting = pInput != nullptr && pInput->rightMouseButton.held;
        const IGameplayWorldRuntime *pWorld = context.worldRuntime();
        std::vector<InspectableRect> inspectables;
        renderHeader(context, root, statistics);

        if (screen.statisticsPartyTab)
        {
            renderPartyTab(context, root, statistics, *pParty);
        }
        else
        {
            renderOverview(context, root, statistics, pWorld != nullptr ? pWorld->gameMinutes() : 0.0f, inspectables,
                pInput, inspecting);
        }

        renderSessionPanel(context, root, statistics);
        GameplayUiSkin::renderButton(context, "StatisticsOverviewButton", width, height, !screen.statisticsPartyTab);
        GameplayUiSkin::renderButton(context, "StatisticsPartyButton", width, height, screen.statisticsPartyTab);
        GameplayUiSkin::renderButton(context, "StatisticsExitButton", width, height);

        // Why the record is not a clean playthrough, in place of the hint.
        const PlaythroughTrackingInfo &integrity = statistics.lifetimeInfo();

        if (!integrity.clean())
        {
            std::string notes;
            const auto addNote = [&notes](const std::string &note)
            {
                notes += (notes.empty() ? "" : ". ") + note;
            };

            if (!integrity.assists.empty())
            {
                std::string assists;

                for (const auto &[assist, record] : integrity.assists)
                {
                    assists += (assists.empty() ? "" : ", ") + Engine::tr(assist);
                }

                addNote(Engine::tr("Assisted: {assists}", {{"assists", assists}}));
            }

            if (integrity.unverified)
            {
                addNote(Engine::tr("Changed outside the game"));
            }

            if (integrity.restoredOlder)
            {
                addNote(Engine::tr("Restored from an older copy"));
            }

            if (integrity.developmentBuild)
            {
                addNote(Engine::tr("Development build"));
            }

            const bool onlyDevelopment = integrity.assists.empty() && !integrity.unverified && !integrity.restoredOlder;
            const Rect notesRect = toScreen(root, 196.0f, 331.0f, 338.0f, 18.0f);

            if (inspecting && pointerInside(notesRect, pInput))
            {
                fillRect(context, notesRect, RowHighlightColor);
            }

            drawText(context, root, "SMALLNUM", SmallScale, onlyDevelopment ? MutedColor : LossColor, notes, 196.0f,
                333.0f, 338.0f, UiLayoutManager::TextAlignX::Center);
            // Held right-click lists what helped the party, and when.
            inspectables.push_back({notesRect, "integrity"});
        }
        else if (!inspecting && !screen.statisticsPartyTab)
        {
            drawText(context, root, "SMALLNUM", SmallScale, DimColor,
                Engine::tr("Hold right mouse on a line for its breakdown"),
                196.0f, 333.0f, 338.0f, UiLayoutManager::TextAlignX::Center);
        }

        for (const InspectableRect &inspectable : inspectables)
        {
            if (inspecting && !inspectable.breakdown.empty() && pointerInside(inspectable.rect, pInput))
            {
                const Breakdown breakdown = buildBreakdown(inspectable.breakdown, statistics, pParty, &context);

                if (!breakdown.title.empty())
                {
                    renderBreakdownPopup(context, root, breakdown, inspectable.rect);
                }

                break;
            }
        }

        return;
    }

    GameplayUiSkin::renderButton(context, "StatisticsExitButton", width, height);
}
}
}
