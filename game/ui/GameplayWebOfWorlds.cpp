#include "game/ui/GameplayWebOfWorlds.h"

#include "engine/Localization.h"
#include "game/StringUtils.h"
#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/tables/MapStats.h"
#include "game/tables/WebOfWorldsTable.h"
#include "game/ui/GameplayObsidianPainter.h"
#include "game/ui/GameplayUiSkin.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game::GameplayWebOfWorlds
{
namespace
{
using GameplayObsidianColors::abgr;

constexpr float Tau = 6.2831853f;
// The chart's parts in page units (the mockup's 1280 x 960 pixels halved).
constexpr GameplayObsidianRect ChartArea = {15, 45, 395, 395};
constexpr GameplayObsidianRect Panel = {418, 48, 205, 384};
constexpr GameplayObsidianRect Rail = {17, 447, 606, 20};
constexpr float PanelInner = 10;
constexpr float BeaconTop = 328;
constexpr float BeaconBottom = 393;
constexpr GameplayObsidianRect TravelButton = {428, 399, 90, 25};
constexpr GameplayObsidianRect CloseButton = {523, 399, 90, 25};

const WebOfWorldsTable *table(const GameplayScreenRuntime &context)
{
    return context.gameplayUiRuntime().webOfWorldsTable();
}

bool hasQBit(const GameplayScreenRuntime &context, uint32_t qbit)
{
    const Party *pParty = context.partyReadOnly();
    return pParty != nullptr && pParty->campaign().hasQuestBit(qbit);
}

WebOfWorldsQBitQuery qbitQuery(const GameplayScreenRuntime &context)
{
    return [&context](uint32_t qbit) { return hasQBit(context, qbit); };
}

bool homeIsWeb(const GameplayScreenRuntime &context)
{
    const std::vector<GameplayTownPortalContinent> &pages = context.townPortalContinents();
    const size_t home = context.gameplayUiRuntime().townPortalHomeContinentIndex();
    return home < pages.size() && pages[home].webOfWorlds;
}

// The Town Portal page a known world opens: its first group this installation has (the home page when it is one).
std::optional<size_t> knownWorldPage(const GameplayScreenRuntime &context, const WebOfWorldsKnownWorld &world)
{
    const std::vector<GameplayTownPortalContinent> &pages = context.townPortalContinents();
    const size_t home = context.gameplayUiRuntime().townPortalHomeContinentIndex();
    std::optional<size_t> first;

    for (const std::string &group : world.continents)
    {
        for (size_t index = 0; index < pages.size(); ++index)
        {
            if (pages[index].webOfWorlds || toLowerCopy(pages[index].groupName) != toLowerCopy(group))
            {
                continue;
            }

            if (index == home)
            {
                return index;
            }

            first = first ? first : std::optional<size_t>(index);
        }
    }

    return first;
}

// What the chart shows this frame.
struct Model
{
    const WebOfWorldsTable *pTable = nullptr;
    const WebOfWorldsPlanet *pPlanet = nullptr;
    size_t planetIndex = 0;
    std::optional<size_t> signal;
    const WebOfWorldsPlanetProgress *pProgress = nullptr;
    std::optional<size_t> beacon;
};

Model model(const GameplayScreenRuntime &context)
{
    Model result;
    result.pTable = table(context);

    if (result.pTable == nullptr || result.pTable->planets().empty())
    {
        return result;
    }

    GameplayUiController::UtilitySpellOverlayState &overlay = context.utilitySpellOverlay();
    result.planetIndex = std::min(overlay.webPlanet, result.pTable->planets().size() - 1);
    result.pPlanet = &result.pTable->planets()[result.planetIndex];
    const Party *pParty = context.partyReadOnly();
    result.pProgress = &overlay.webProgress.get(*result.pPlanet, pParty ? &pParty->campaign() : nullptr);

    if (overlay.webSignal && *overlay.webSignal < result.pPlanet->signals.size())
    {
        result.signal = overlay.webSignal;
    }

    const std::vector<size_t> &lit = result.pProgress->litBeacons;

    if (overlay.webBeacon && std::find(lit.begin(), lit.end(), *overlay.webBeacon) != lit.end())
    {
        result.beacon = overlay.webBeacon;
    }
    else if (!lit.empty())
    {
        result.beacon = lit.front();
    }

    return result;
}

float beaconStep(const WebOfWorldsPlanet &planet)
{
    return std::min(15.0f, (BeaconBottom - BeaconTop) / float(std::max<size_t>(1, planet.beacons.size())));
}

GameplayObsidianRect beaconRow(const WebOfWorldsPlanet &planet, size_t index)
{
    const float step = beaconStep(planet);
    return {Panel.x + PanelInner, BeaconTop + step * float(index), Panel.width - PanelInner * 2, step};
}

bool inside(const GameplayObsidianRect &area, float x, float y)
{
    return area.contains(x, y);
}

bool nearPoint(float x, float y, float cx, float cy, float radius)
{
    return (x - cx) * (x - cx) + (y - cy) * (y - cy) <= radius * radius;
}

std::string beaconTravelText(const WebOfWorldsBeacon &beacon)
{
    return Engine::localize(beacon.travel.empty() ? beacon.name : beacon.travel);
}

class ChartPainter : public GameplayObsidianPainter
{
public:
    using GameplayObsidianPainter::GameplayObsidianPainter;
    using GameplayObsidianPainter::lines;
    using GameplayObsidianPainter::Segment;

    void disc(float cx, float cy, float radius, uint32_t colour) const
    {
        ellipse(solid(colour), rect(cx - radius, cy - radius, radius * 2, radius * 2));
    }

    // A circle's outline as segments (only those inside `clip`, page units).
    void ring(float cx, float cy, float radius, uint32_t colour, float lineWidth,
        const GameplayObsidianRect *pClip = nullptr) const
    {
        const int count = std::clamp(int(radius * 0.6f), 24, 120);
        std::vector<Segment> segments;

        for (int index = 0; index < count; ++index)
        {
            const float a0 = Tau * float(index) / float(count);
            const float a1 = Tau * float(index + 1) / float(count);
            const Segment segment = {cx + std::cos(a0) * radius, cy + std::sin(a0) * radius,
                cx + std::cos(a1) * radius, cy + std::sin(a1) * radius};

            if (pClip != nullptr
                && (!pClip->contains(segment.x1, segment.y1) || !pClip->contains(segment.x2, segment.y2)))
            {
                continue;
            }

            segments.push_back(segment);
        }

        lines(segments, colour, lineWidth);
    }

    bool iconDisc(float cx, float cy, float radius, const std::string &icon) const
    {
        const auto art = m_context.gameplayUiRuntime().ensureHudTextureLoaded(icon);
        if (!art)
        {
            return false;
        }
        ellipse(art, rect(cx - radius, cy - radius, radius * 2, radius * 2));
        return true;
    }

    // A dashed line; `offset` moves the dashes along it (page units).
    void dashed(float x1, float y1, float x2, float y2, float dash, float gap, float offset, uint32_t colour,
        float lineWidth) const
    {
        const float length = std::hypot(x2 - x1, y2 - y1);

        if (length < 0.01f)
        {
            return;
        }

        const float dx = (x2 - x1) / length;
        const float dy = (y2 - y1) / length;
        const float period = dash + gap;
        std::vector<Segment> segments;

        for (float start = std::fmod(offset, period) - period; start < length; start += period)
        {
            const float a = std::max(0.0f, start);
            const float b = std::min(length, start + dash);

            if (b > a)
            {
                segments.push_back({x1 + dx * a, y1 + dy * a, x1 + dx * b, y1 + dy * b});
            }
        }

        lines(segments, colour, lineWidth);
    }

    // A soft glow: stacked translucent discs, the outer ones fainter.
    void glow(float cx, float cy, float radius, uint32_t rgb, float strength) const
    {
        constexpr int Steps = 7;
        const uint32_t alpha = uint32_t(std::clamp(strength * 255.0f / Steps * 1.4f, 0.0f, 255.0f));
        const auto texture = solid(abgr(rgb, alpha));
        if (!texture)
        {
            return;
        }
        std::array<GameplayUiViewportRect, Steps> discs;
        for (int step = 0; step < Steps; ++step)
        {
            const float t = float(step) / float(Steps - 1);
            const float r = radius * (1.0f - t * 0.82f);
            const Rect box = rect(cx - r, cy - r, r * 2, r * 2);
            discs[step] = {box.x, box.y, box.width, box.height};
        }
        m_context.gameplayUiRuntime().submitHudTexturedEllipses(texture->textureHandle, discs);
    }

    // A small diamond (a beacon's mark), filled or outlined.
    void diamond(float cx, float cy, float half, uint32_t fillColour, uint32_t edgeColour, bool filled) const
    {
        if (filled)
        {
            Quads quads;

            for (float row = -half; row <= half; row += 0.5f)
            {
                const float w = half - std::abs(row);
                addFill(quads, rect(cx - w, cy + row - 0.25f, w * 2, 0.5f), fillColour);
            }

            submit(quads);
        }

        lines({{cx, cy - half, cx + half, cy}, {cx + half, cy, cx, cy + half}, {cx, cy + half, cx - half, cy},
                  {cx - half, cy, cx, cy - half}},
            edgeColour, 0.7f);
    }

    void star(float cx, float cy, float half, uint32_t colour) const
    {
        lines({{cx - half, cy, cx + half, cy}, {cx, cy - half, cx, cy + half},
                  {cx - half * 0.6f, cy - half * 0.6f, cx + half * 0.6f, cy + half * 0.6f},
                  {cx + half * 0.6f, cy - half * 0.6f, cx - half * 0.6f, cy + half * 0.6f}},
            colour, 0.6f);
    }
};

void renderBackdrop(const ChartPainter &painter)
{
    painter.fill(painter.rect(0, 0, 640, 480), abgr(0x0a0608));
    painter.glow(243, 216, 330, 0x2a0f12, 0.9f);
    painter.glow(280, 195, 180, 0x8c1e18, 0.32f);

    // A fixed field of stars (the same every frame).
    GameplayObsidianPainter::Quads quads;
    uint32_t seed = 7;
    const auto random = [&seed]()
    {
        seed = uint32_t((uint64_t(seed) * 16807u) % 2147483647u);
        return float(seed) / 2147483647.0f;
    };
    static constexpr uint32_t Tints[] = {0xf0e0d0, 0xe8d0b8, 0xf6ead8, 0xd8c8c0};

    for (int index = 0; index < 260; ++index)
    {
        const float x = random() * 640;
        const float y = random() * 480;
        const float size = random() * 0.65f + 0.25f;
        const uint32_t tint = Tints[index % 4];
        const uint32_t alpha = 70 + uint32_t(random() * 3) * 60;
        painter.addFill(quads, painter.rect(x, y, size, size), abgr(tint, alpha));
    }

    painter.submit(quads);
}

void renderFrame(const ChartPainter &painter)
{
    GameplayObsidianPainter::Quads quads;
    const auto band = [&painter, &quads](float inset, float thickness, uint32_t colour)
    {
        painter.addFill(quads, painter.rect(inset, inset, 640 - inset * 2, thickness), colour);
        painter.addFill(quads, painter.rect(inset, 480 - inset - thickness, 640 - inset * 2, thickness), colour);
        painter.addFill(quads, painter.rect(inset, inset, thickness, 480 - inset * 2), colour);
        painter.addFill(quads, painter.rect(640 - inset - thickness, inset, thickness, 480 - inset * 2), colour);
    };
    band(0, 7, abgr(0x151012));
    band(7, 1, abgr(0x8a6a3c));
    band(8, 1.5f, abgr(0x000000));
    band(9.5f, 1, abgr(0x5b452a));
    painter.submit(quads);
}

void renderChartNodes(GameplayScreenRuntime &context, const ChartPainter &painter, const Model &state,
    const Target &hovered)
{
    const WebOfWorldsTable &web = *state.pTable;
    const WebOfWorldsPlanet &planet = *state.pPlanet;
    const bool cleared = state.pProgress->cleared;
    const float seconds = float(SDL_GetTicks() % 1000000u) / 1000.0f;
    std::vector<const WebOfWorldsKnownWorld *> known;

    for (const WebOfWorldsKnownWorld &world : web.knownWorlds())
    {
        if (knownWorldPage(context, world))
        {
            known.push_back(&world);
        }
    }

    const WebOfWorldsKnownWorld *pFrom = known.empty() ? nullptr : known.front();

    for (const WebOfWorldsKnownWorld *pWorld : known)
    {
        pFrom = pWorld->name == planet.threadFrom ? pWorld : pFrom;
    }

    // The gate web's rings around the home of the threads.
    if (pFrom != nullptr)
    {
        for (const float radius : {100.0f, 190.0f, 280.0f})
        {
            painter.ring(pFrom->x, pFrom->y, radius, abgr(0x5b452a, 90), 0.5f, &ChartArea);
        }
    }

    // Brass threads between the known worlds.
    std::vector<ChartPainter::Segment> threads;

    for (size_t a = 0; a < known.size(); ++a)
    {
        for (size_t b = a + 1; b < known.size(); ++b)
        {
            threads.push_back({known[a]->x, known[a]->y, known[b]->x, known[b]->y});
        }
    }

    painter.lines(threads, abgr(0x8a6a3c, 180), 0.75f);

    // The live thread to the planet, flowing outwards; the signals' faint ones.
    if (pFrom != nullptr)
    {
        painter.dashed(pFrom->x, pFrom->y, planet.x, planet.y, 2, 8, cleared ? 0 : seconds * 12.5f,
            abgr(cleared ? 0xd9c27a : 0xff8a3a), 1.25f);
    }

    std::vector<ChartPainter::Label> namedSignals, unknownSignals;
    for (size_t index = 0; index < planet.signals.size(); ++index)
    {
        const WebOfWorldsSignal &signal = planet.signals[index];
        const bool strong = cleared && index == 0;
        painter.dashed(planet.x, planet.y, signal.x, signal.y, strong ? 3 : 1, strong ? 3 : 4, 0,
            abgr(strong ? 0xc9a46a : 0x6b5a48, strong ? 255 : 200), strong ? 1.0f : 0.6f);
    }

    // The known worlds: pale discs with their names.
    std::vector<GameplayObsidianPainter::Label> names;
    std::vector<GameplayObsidianPainter::Label> subtitles;

    for (size_t index = 0; index < known.size(); ++index)
    {
        const WebOfWorldsKnownWorld &world = *known[index];
        const bool hover = hovered.type == TargetType::KnownWorld && known[index] == &web.knownWorlds()[hovered.index];
        painter.ring(world.x, world.y, world.radius + 5, abgr(hover ? 0xffd28a : 0x8a6a3c, hover ? 255 : 128), 0.5f);
        painter.disc(world.x, world.y, world.radius, abgr(0xece6da, 230));
        painter.disc(world.x - world.radius * 0.3f, world.y - world.radius * 0.3f, world.radius * 0.55f,
            abgr(0xffffff, 46));
        names.push_back({Engine::localize(world.name), world.x, world.y + world.radius + 4, 1});

        if (!world.subtitle.empty())
        {
            subtitles.push_back({Engine::localize(world.subtitle), world.x, world.y + world.radius + 16, 1});
        }
    }

    painter.texts("Fondamento", 11, abgr(0xe8d6ae), names);
    painter.texts("Lucida", 7.5f, abgr(0x9c8b72), subtitles);

    // The planet: a pulsing halo while infested, its art in a disc, the selection cross.
    const uint32_t haloRgb = cleared ? 0xd9c27a : 0xff5a2a;
    const float pulse = cleared ? 0.55f : 0.42f + 0.18f * std::sin(seconds * Tau / 2.4f);
    painter.glow(planet.x, planet.y, planet.radius + 17, haloRgb, pulse);

    if (!painter.iconDisc(planet.x, planet.y, planet.radius,
            cleared && !planet.clearedIcon.empty() ? planet.clearedIcon : planet.icon))
    {
        painter.disc(planet.x, planet.y, planet.radius, abgr(0x6a1e14));
    }

    if (cleared && planet.clearedIcon.empty())
    {
        painter.disc(planet.x, planet.y, planet.radius, abgr(0xc9a86a, 110));
    }

    const float r = planet.radius;

    if (!state.signal)
    {
        const uint32_t gold = abgr(0xffd28a);
        painter.ring(planet.x, planet.y, r + 4, gold, 1.0f);
        painter.lines({{planet.x - r - 9, planet.y, planet.x - r - 16, planet.y},
                          {planet.x + r + 9, planet.y, planet.x + r + 16, planet.y},
                          {planet.x, planet.y - r - 9, planet.x, planet.y - r - 16},
                          {planet.x, planet.y + r + 9, planet.x, planet.y + r + 16}},
            gold, 1.0f);
    }
    else if (hovered.type == TargetType::Planet)
    {
        painter.ring(planet.x, planet.y, r + 4, abgr(0xffd28a, 140), 0.7f);
    }

    painter.text("Fondamento", 14, abgr(0xffd9a8), Engine::localize(planet.name), planet.x, planet.y + r + 17, 1);

    // The signals: dark "?" discs; the first one gets its name when the planet is cleansed.
    for (size_t index = 0; index < planet.signals.size(); ++index)
    {
        const WebOfWorldsSignal &signal = planet.signals[index];
        const bool named = cleared && index == 0;
        const uint32_t rim = named ? 0xc9a46a : 0x4d4548;
        if (!painter.iconDisc(signal.x, signal.y, signal.radius, signal.icon))
        {
            painter.disc(signal.x, signal.y, signal.radius, abgr(0x1c1719));
        }
        painter.ring(signal.x, signal.y, signal.radius, abgr(rim), 1.0f);
        painter.text("Fondamento", signal.radius, abgr(named ? 0xc9a46a : 0x5d5458), "?", signal.x,
            signal.y - signal.radius * 0.5f, 1);

        if ((state.signal && *state.signal == index)
            || (hovered.type == TargetType::Signal && hovered.index == index))
        {
            painter.ring(signal.x, signal.y, signal.radius + 4,
                abgr(0xffd28a, state.signal && *state.signal == index ? 255 : 140), 1.0f);
        }

        const std::string label = Engine::localize(named && !signal.clearedName.empty() ? signal.clearedName
                                                                                        : signal.name);
        (named ? namedSignals : unknownSignals).push_back({label, signal.x, signal.y + signal.radius + 5, 1});
    }
    painter.texts("Lucida", 8.5f, abgr(0xc9a46a), namedSignals);
    painter.texts("Lucida", 8.5f, abgr(0x6b625c), unknownSignals);

    // The legend.
    static constexpr struct
    {
        uint32_t rgb;
        std::string_view text;
    } legend[] = {{0xece6da, Engine::trNoop("Known worlds (Town Portal)")},
        {0xff5a2a, Engine::trNoop("Infested")}, {0xd9c27a, Engine::trNoop("Cleansed")},
        {0x4d4548, Engine::trNoop("Signal")}};
    float x = 25;
    std::vector<ChartPainter::Label> legendLabels;

    for (const auto &entry : legend)
    {
        painter.disc(x + 2.5f, 433, 2.5f, abgr(entry.rgb));
        legendLabels.push_back({Engine::localize(entry.text), x + 8, 429});
        x += 18 + painter.width("Lucida", 7.5f, legendLabels.back().value);
    }
    painter.texts("Lucida", 7.5f, abgr(0xa8987f), legendLabels);
}

void renderPanel(GameplayScreenRuntime &context, const ChartPainter &painter, const Model &state,
    const Target &hovered, const Target &pressed, bool leftPressed)
{
    const WebOfWorldsPlanet &planet = *state.pPlanet;
    const bool cleared = state.pProgress->cleared;
    GameplayUiSkin::renderPanel(context, GameplayResolvedHudLayoutElement{painter.rect(Panel.x, Panel.y, 0, 0).x,
        painter.rect(Panel.x, Panel.y, 0, 0).y, Panel.width * painter.scale(), Panel.height * painter.scale(),
        painter.scale()});
    const float cx = Panel.x + Panel.width / 2;
    const float left = Panel.x + PanelInner;
    const float right = Panel.x + Panel.width - PanelInner;
    const auto button = [&painter, &hovered, &pressed, leftPressed](const GameplayObsidianRect &box,
                            const std::string &label, bool enabled, TargetType type)
    {
        painter.button(painter.rect(box.x, box.y, box.width, box.height), label, false, enabled,
            enabled && hovered.type == type, enabled && leftPressed && pressed.type == type);
    };

    if (state.signal)
    {
        const WebOfWorldsSignal &signal = planet.signals[*state.signal];
        const bool named = cleared && *state.signal == 0 && !signal.clearedName.empty();
        painter.glow(cx, 118, 58, 0x3a3438, 0.9f);
        if (!painter.iconDisc(cx, 118, 50, signal.icon))
        {
            painter.disc(cx, 118, 50, abgr(0x161214));
            painter.text("Fondamento", 45, abgr(0x4d4548), "?", cx, 92, 1);
        }
        painter.text("Fondamento", 20, abgr(0xf2dcae), Engine::localize(named ? signal.clearedName : signal.name),
            cx, 176, 1);
        painter.text("Lucida", 9, abgr(0xbba98f), Engine::localize(signal.epithet), cx, 199, 1);
        const std::string badge = Engine::tr("UNREACHABLE");
        const float badgeWidth = painter.width("Lucida", 7, badge) + 9;
        painter.frame(painter.rect(cx - badgeWidth / 2, 213, badgeWidth, 13), abgr(0x4d4548));
        painter.text("Lucida", 7, abgr(0x7d7470), badge, cx, 216, 1);
        std::vector<ChartPainter::Label> message;
        float y = 240;
        for (const std::string &line :
            painter.wrapped("Lucida", 8.5f, Engine::localize(signal.message), right - left))
        {
            message.push_back({line, cx, y, 1});
            y += 11.5f;
        }
        painter.texts("Lucida", 8.5f, abgr(0xc9b79a), message);

        button(TravelButton, Engine::tr("Travel"), false, TargetType::Travel);
        button(CloseButton, Engine::tr("Close"), true, TargetType::Close);
        return;
    }

    // The planet's art, its name and epithet.
    painter.iconDisc(cx, 115.5f, 57.5f, cleared && !planet.clearedIcon.empty() ? planet.clearedIcon : planet.icon);

    if (cleared && planet.clearedIcon.empty())
    {
        painter.disc(cx, 115.5f, 57.5f, abgr(0xc9a86a, 110));
    }

    painter.text("Fondamento", 20, abgr(0xf2dcae), Engine::localize(planet.name), cx, 176, 1);
    painter.text("Lucida", 9, abgr(0xbba98f),
        Engine::localize(cleared && !planet.clearedEpithet.empty() ? planet.clearedEpithet : planet.epithet), cx, 199,
        1);

    // Badges: the status and the threat.
    const std::string &statusKey = cleared ? planet.clearedStatus : planet.status;
    const std::string status = Engine::localize(statusKey.empty()
        ? (cleared ? Engine::trNoop("CLEANSED") : Engine::trNoop("INFESTED")) : std::string_view(statusKey));
    const uint32_t statusColour = abgr(cleared ? 0xd9c27a : 0xff6a3a);
    const std::string threat = Engine::tr("THREAT");
    const float statusWidth = painter.width("Lucida", 7, status) + 9;
    const float threatWidth = planet.threat == 0 ? 0 : painter.width("Lucida", 7, threat) + 12 + 5.5f * planet.threat;
    float badgeX = cx - (statusWidth + (threatWidth > 0 ? threatWidth + 4 : 0)) / 2;
    painter.frame(painter.rect(badgeX, 223, statusWidth, 13), statusColour);
    painter.text("Lucida", 7, statusColour, status, badgeX + 4.5f, 226);
    badgeX += statusWidth + 4;

    if (threatWidth > 0)
    {
        painter.frame(painter.rect(badgeX, 223, threatWidth, 13), abgr(0x5b452a));
        const float textEnd = badgeX + 4.5f + painter.text("Lucida", 7, abgr(0xd8b884), threat, badgeX + 4.5f, 226);

        for (uint32_t index = 0; index < planet.threat; ++index)
        {
            painter.star(textEnd + 6 + 5.5f * float(index), 229.5f, 2.0f, abgr(0xd8b884));
        }
    }

    // The purge meter.
    painter.text("Lucida", 8.5f, abgr(0xc8b9a0), Engine::tr("Purged"), left, 244);
    painter.text("Lucida", 8.5f, abgr(0xf2dcae), std::to_string(state.pProgress->purgePercent) + "%", right, 244, 2);
    GameplayObsidianPainter::Quads bar;
    const float barWidth = right - left;
    painter.addFill(bar, painter.rect(left, 256, barWidth, 6), abgr(0x0a0809));
    painter.addFrame(bar, painter.rect(left, 256, barWidth, 6), abgr(0x5b452a));
    const float filled = std::max(1.0f, barWidth * float(state.pProgress->purgePercent) / 100.0f);
    constexpr int Slices = 12;

    for (int slice = 0; slice < Slices; ++slice)
    {
        const float t = float(slice) / float(Slices - 1);
        const auto mix = [t](uint32_t a, uint32_t b, int shift)
        {
            return uint32_t(float((a >> shift) & 0xff) * (1 - t) + float((b >> shift) & 0xff) * t) << shift;
        };
        const uint32_t from = cleared ? 0x5d6f3c : 0x7a1c18;
        const uint32_t to = cleared ? 0xc9d77a : 0xff6a24;
        const uint32_t rgb = mix(from, to, 16) | mix(from, to, 8) | mix(from, to, 0);
        painter.addFill(bar, painter.rect(left + 0.5f + filled * float(slice) / Slices, 256.5f,
                                 filled / Slices + 0.05f, 5), abgr(rgb));
    }

    painter.submit(bar);

    // The counters.
    std::vector<GameplayObsidianPainter::Label> labels;
    std::vector<GameplayObsidianPainter::Label> values;

    for (size_t index = 0; index < planet.counters.size() && index < 3; ++index)
    {
        const float y = 270 + 14.5f * float(index);
        const WebOfWorldsCount &count = state.pProgress->counters[index];
        labels.push_back({Engine::localize(planet.counters[index].label), left, y, 0});
        values.push_back({std::to_string(count.done) + " / " + std::to_string(count.total), right, y, 2});
    }

    painter.texts("Lucida", 8.5f, abgr(0xc8b9a0), labels);
    painter.texts("Lucida", 8.5f, abgr(0xf2dcae), values);

    // The beacons: the lit ones can be chosen.
    painter.text("Fondamento", 10, abgr(0xd8b884), Engine::tr("Beacons"), left, 315);

    const std::array beaconColours = {abgr(0x6b625c), abgr(0xffe0a8), abgr(0xffefd4), abgr(0xe9dcc0)};
    std::array<std::vector<ChartPainter::Label>, 4> beaconLabels;
    for (size_t index = 0; index < planet.beacons.size(); ++index)
    {
        const GameplayObsidianRect row = beaconRow(planet, index);
        const std::vector<size_t> &lit = state.pProgress->litBeacons;
        const bool isLit = std::find(lit.begin(), lit.end(), index) != lit.end();
        const bool selected = state.beacon && *state.beacon == index;
        const bool hover = isLit && hovered.type == TargetType::Beacon && hovered.index == index;
        const float my = row.y + row.height / 2;
        painter.diamond(row.x + 4, my, 3.2f, abgr(0xffb04a), abgr(isLit ? 0xffd28a : 0x8a6a3c), isLit);
        const std::string name = Engine::localize(planet.beacons[index].name);
        beaconLabels[!isLit ? 0 : selected ? 1 : hover ? 2 : 3].push_back(
            {painter.fitted("Lucida", 8.5f, name, row.width - 12), row.x + 11, my - 5});
    }
    for (size_t i = 0; i < beaconLabels.size(); ++i)
    {
        painter.texts("Lucida", 8.5f, beaconColours[i], beaconLabels[i]);
    }

    button(TravelButton, Engine::tr("Travel"), state.beacon.has_value(), TargetType::Travel);
    button(CloseButton, Engine::tr("Close"), true, TargetType::Close);
}
}

GameplayUtilitySpellPointerTarget pointerTarget(const Target &target)
{
    if (target.type == TargetType::None)
    {
        return {};
    }

    return {GameplayUtilitySpellPointerTargetType::WebOfWorlds, size_t(target.type) << 16 | (target.index & 0xffff)};
}

Target fromPointerTarget(const GameplayUtilitySpellPointerTarget &target)
{
    if (target.type != GameplayUtilitySpellPointerTargetType::WebOfWorlds)
    {
        return {};
    }

    return {TargetType(target.index >> 16), target.index & 0xffff};
}

bool hasPage(const GameplayScreenRuntime &context)
{
    const std::vector<GameplayTownPortalContinent> &pages = context.townPortalContinents();
    return !pages.empty() && pages.back().webOfWorlds;
}

bool pageShown(const GameplayScreenRuntime &context)
{
    const std::vector<GameplayTownPortalContinent> &pages = context.townPortalContinents();
    const size_t index = context.townPortalContinentIndex();
    return index < pages.size() && pages[index].webOfWorlds;
}

bool unlocked(const GameplayScreenRuntime &context)
{
    const WebOfWorldsTable *pTable = table(context);
    return pTable != nullptr && pTable->isUnlocked(qbitQuery(context), homeIsWeb(context));
}

void greetOnFirstOpen(GameplayScreenRuntime &context)
{
    const WebOfWorldsTable *pWeb = table(context);
    Party *pParty = context.party();
    if (pWeb == nullptr || pParty == nullptr || pWeb->firstOpen().qbit == 0)
    {
        return;
    }

    const WebOfWorldsGreeting &greeting = pWeb->firstOpen();
    if (pParty->campaign().hasQuestBit(greeting.qbit))
    {
        return;
    }
    pParty->campaign().setQuestBit(greeting.qbit, true);
    context.setStatusBarEvent(greeting.message, 5.0f);
    if (!greeting.sound.empty() && context.audioSystem() != nullptr)
    {
        context.audioSystem()->playSoundByName(greeting.sound, GameAudioSystem::PlaybackGroup::Speech);
    }
}

std::string tabHint(const GameplayScreenRuntime &context)
{
    const WebOfWorldsTable *pTable = table(context);

    if (pTable == nullptr)
    {
        return {};
    }

    return unlocked(context) ? pTable->openHint() : pTable->lockedHint();
}

void renderTab(GameplayScreenRuntime &context, int width, int height, float mouseX, float mouseY, bool pressed)
{
    const GameplayScreenRuntime::HudLayoutElement *pLayout = context.findHudLayoutElement("TownPortalWebButton");

    if (pLayout == nullptr || !pLayout->visible)
    {
        return;
    }

    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
        context.resolveHudLayoutElement("TownPortalWebButton", width, height, pLayout->width, pLayout->height);

    if (!resolved)
    {
        return;
    }

    const bool hovered = context.isPointerInsideResolvedElement(*resolved, mouseX, mouseY);
    const bool open = unlocked(context);
    const bool selected = pageShown(context);
    const std::string label = Engine::tr("Web of Worlds");
    GameplayUiSkin::renderButton(context, "TownPortalWebButton", width, height, selected, open, &label);

    // The ember glow of a woken gate web and its glyph, in the tab's own units (its layout size).
    const GameplayResolvedHudLayoutElement page = {resolved->x, resolved->y, resolved->width, resolved->height,
        resolved->width / float(pLayout->width)};
    const ChartPainter painter(context, page);
    const float gx = 10;
    const float gy = float(pLayout->height) / 2;
    const uint32_t glyph = !open ? abgr(0x77706a, 110) : hovered || pressed ? abgr(0xffd0a0) : abgr(0xffb06a);

    if (open)
    {
        painter.glow(gx, gy, 9, 0xff6428, selected ? 0.55f : 0.35f);
    }

    painter.ring(gx, gy, 5, glyph, 0.8f);
    painter.lines({{gx, gy - 5, gx, gy + 5}, {gx - 5, gy, gx + 5, gy}, {gx - 3.5f, gy - 3.5f, gx + 3.5f, gy + 3.5f},
                      {gx + 3.5f, gy - 3.5f, gx - 3.5f, gy + 3.5f}},
        glyph, 0.8f);
    painter.disc(gx, gy, 1.5f, open ? abgr(0xff7a2f) : abgr(0x77706a, 110));

    // The hint: how to wake the gate web, or what it does; above the tab, kept on the screen.
    if (!hovered)
    {
        return;
    }
    const std::string hint = Engine::localize(tabHint(context));
    if (hint.empty())
    {
        return;
    }

    const float unit = page.scale;
    const ChartPainter tip(context, GameplayResolvedHudLayoutElement{0, 0, float(width), float(height), unit});
    const float tipWidth = 200;
    const std::vector<std::string> hintLines = tip.wrapped("Lucida", 9, hint, tipWidth - 14);
    const float tipHeight = 26 + 11.5f * float(hintLines.size());
    const float tipX = std::clamp((resolved->x + resolved->width) / unit - tipWidth, 2.0f,
        float(width) / unit - tipWidth - 2);
    const float tipY = resolved->y / unit - tipHeight - 6;
    GameplayUiSkin::renderPanel(context, GameplayResolvedHudLayoutElement{tipX * unit, tipY * unit, tipWidth * unit,
        tipHeight * unit, unit});
    tip.text("Fondamento", 11, abgr(0xffd9a0), label, tipX + 7, tipY + 6);
    float lineY = tipY + 21;

    std::vector<ChartPainter::Label> hintLabels;
    for (const std::string &line : hintLines)
    {
        hintLabels.push_back({line, tipX + 7, lineY});
        lineY += 11.5f;
    }
    tip.texts("Lucida", 9, abgr(0xe9dcc0), hintLabels);
}

void renderChart(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &page, float mouseX,
    float mouseY, bool leftPressed)
{
    const Model state = model(context);
    const ChartPainter painter(context, page);
    renderBackdrop(painter);

    if (state.pPlanet == nullptr)
    {
        renderFrame(painter);
        return;
    }

    const Target hovered = targetAt(context, page, mouseX, mouseY);
    const Target pressed = fromPointerTarget(context.interactionState().utilitySpellPressedTarget);
    renderChartNodes(context, painter, state, hovered);
    renderPanel(context, painter, state, hovered, pressed, leftPressed);

    // The title plate.
    const std::string title = Engine::tr("Web of Worlds");
    const float titleWidth = painter.width("Fondamento", 20, title) + 46;
    GameplayUiSkin::renderPanel(context,
        GameplayResolvedHudLayoutElement{painter.rect(320 - titleWidth / 2, 13, 0, 0).x,
            painter.rect(0, 13, 0, 0).y, titleWidth * painter.scale(), 31 * painter.scale(), painter.scale()});
    painter.text("Fondamento", 20, abgr(0xf0d9a8), title, 320, 18, 1);

    // The status rail: where Travel goes, or what is hovered.
    std::string rail;

    if (state.signal)
    {
        const WebOfWorldsSignal &signal = state.pPlanet->signals[*state.signal];
        rail = Engine::tr("{signal}: unreachable", {{"signal", Engine::localize(signal.name)}});
    }
    else if (state.beacon)
    {
        rail = Engine::tr("Travel to {planet}: {beacon}",
            {{"planet", Engine::localize(state.pPlanet->name)},
                {"beacon", beaconTravelText(state.pPlanet->beacons[*state.beacon])}});
    }
    else
    {
        rail = Engine::tr("No beacon is lit on {planet}", {{"planet", Engine::localize(state.pPlanet->name)}});
    }

    if (hovered.type == TargetType::KnownWorld && state.pTable != nullptr)
    {
        rail = Engine::tr("Town Portal: {world}",
            {{"world", Engine::localize(state.pTable->knownWorlds()[hovered.index].name)}});
    }

    GameplayObsidianPainter::Quads quads;
    painter.addFill(quads, painter.rect(Rail.x, Rail.y, Rail.width, Rail.height), abgr(0x080607, 204));
    painter.addFill(quads, painter.rect(Rail.x, Rail.y, Rail.width, 0.5f), abgr(0x5b452a));
    painter.submit(quads);
    const auto &status = context.statusBarState();
    painter.text("Lucida", 9.5f, abgr(0xe9dcc0),
        status.eventRemainingSeconds > 0.0f && !status.eventText.empty() ? status.eventText : rail,
        320, Rail.y + 4.5f, 1);
    renderFrame(painter);
}

Target targetAt(const GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &page, float x, float y)
{
    const Model state = model(context);

    if (state.pPlanet == nullptr || page.scale <= 0)
    {
        return {};
    }

    // To page units.
    const float px = (x - page.x) / page.scale;
    const float py = (y - page.y) / page.scale;
    const WebOfWorldsPlanet &planet = *state.pPlanet;

    if (inside(TravelButton, px, py))
    {
        return {TargetType::Travel, 0};
    }

    if (inside(CloseButton, px, py))
    {
        return {TargetType::Close, 0};
    }

    if (!state.signal)
    {
        for (size_t index = 0; index < planet.beacons.size(); ++index)
        {
            if (inside(beaconRow(planet, index), px, py))
            {
                return {TargetType::Beacon, index};
            }
        }
    }

    if (nearPoint(px, py, planet.x, planet.y, planet.radius + 8))
    {
        return {TargetType::Planet, state.planetIndex};
    }

    for (size_t index = 0; index < planet.signals.size(); ++index)
    {
        const WebOfWorldsSignal &signal = planet.signals[index];

        if (nearPoint(px, py, signal.x, signal.y, signal.radius + 6))
        {
            return {TargetType::Signal, index};
        }
    }

    const std::vector<WebOfWorldsKnownWorld> &known = state.pTable->knownWorlds();

    for (size_t index = 0; index < known.size(); ++index)
    {
        if (nearPoint(px, py, known[index].x, known[index].y, known[index].radius + 6)
            && knownWorldPage(context, known[index]))
        {
            return {TargetType::KnownWorld, index};
        }
    }

    return {};
}

bool activate(GameplayScreenRuntime &context, const Target &target, PartySpellCastRequest &request)
{
    const Model state = model(context);
    GameplayUiController::UtilitySpellOverlayState &overlay = context.utilitySpellOverlay();

    if (state.pPlanet == nullptr)
    {
        return false;
    }

    switch (target.type)
    {
        case TargetType::Planet:
            overlay.webPlanet = target.index;
            overlay.webSignal.reset();
            return false;

        case TargetType::Signal:
            overlay.webSignal = target.index;
            return false;

        case TargetType::Beacon:
        {
            const std::vector<size_t> &lit = state.pProgress->litBeacons;

            if (std::find(lit.begin(), lit.end(), target.index) != lit.end())
            {
                overlay.webBeacon = target.index;
            }

            return false;
        }

        case TargetType::KnownWorld:
            if (const std::optional<size_t> page = knownWorldPage(context, state.pTable->knownWorlds()[target.index]))
            {
                context.selectTownPortalContinent(*page);
            }

            return false;

        case TargetType::Close:
            // Back to the Town Portal pages; on a planet the chart is home and Close ends the spell.
            if (!homeIsWeb(context))
            {
                context.selectTownPortalContinent(context.gameplayUiRuntime().townPortalHomeContinentIndex());
                return false;
            }

            context.utilitySpellOverlay() = {};
            context.resetUtilitySpellOverlayInteractionState();
            context.setStatusBarEvent(std::string(Engine::trNoop("Spell cancelled")), 2.0f);
            return false;

        case TargetType::Travel:
        {
            if (state.signal || !state.beacon)
            {
                return false;
            }

            const WebOfWorldsBeacon &beacon = state.pPlanet->beacons[*state.beacon];

            if (context.mapStats().findByFileName(beacon.mapFileName) == nullptr)
            {
                context.setStatusBarEvent(std::string(Engine::trNoop("The beacon does not answer")), 2.0f);
                return false;
            }

            request.utilityAction = PartySpellUtilityActionKind::TownPortalDestination;
            request.hasUtilityMapMove = true;
            request.utilityActionId = std::string(WebOfWorldsTownPortalGroupName) + ":" + state.pPlanet->key + ":"
                + std::to_string(*state.beacon);
            request.utilityMapMoveMapName = beacon.mapFileName;
            request.utilityMapMoveX = beacon.position ? (*beacon.position)[0] : 0;
            request.utilityMapMoveY = beacon.position ? (*beacon.position)[1] : 0;
            request.utilityMapMoveZ = beacon.position ? (*beacon.position)[2] : 0;
            request.utilityMapMoveDirectionDegrees = beacon.directionDegrees;
            request.utilityMapMoveUseMapStartPosition = !beacon.position;
            request.utilityStatusText = beacon.name;
            return true;
        }

        case TargetType::None:
            return false;
    }

    return false;
}
}
