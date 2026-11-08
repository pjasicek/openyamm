#include "game/ui/GameplayMapProgressBar.h"
#include "engine/Localization.h"

#include "game/app/KeyboardBindings.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiRuntime.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// The study's colours (maw_map_progress_20261025 index.html), as RGB.
struct Stop
{
    float at = 0;
    uint32_t rgb = 0;
};

using Gradient = std::array<Stop, 4>;

constexpr Gradient Violet = {{{0.0f, 0xd9c0ff}, {0.35f, 0x9b6cec}, {0.75f, 0x6a3fc0}, {1.0f, 0x3b2175}}};
constexpr Gradient GoldFill = {{{0.0f, 0xfff0bf}, {0.35f, 0xe6bf6a}, {0.75f, 0xb98a35}, {1.0f, 0x6e4f18}}};
constexpr Gradient Dimension = {{{0.0f, 0xbff4ee}, {0.35f, 0x7f8ff0}, {0.75f, 0x5a3fc4}, {1.0f, 0x2a1f6e}}};
constexpr uint32_t ChannelTrack = 0x050a0a;
constexpr uint32_t TabFill = 0x0b1413;
constexpr uint32_t RimLight = 0xe0c890;
constexpr uint32_t RimMid = 0xa8925f;
constexpr uint32_t Ivory = 0xefe0bc;
constexpr uint32_t GoldText = 0xf2d27a;
constexpr uint32_t DimensionText = 0xbff4ee;
constexpr uint32_t RevivalRed = 0xe0604f;
constexpr uint32_t Black = 0x000000;

constexpr char TabFont[] = "alegreya_semibold";

// The tab geometry in HUD units, from the study at scale 1.875: the right tab ends 52 px right of the channel, rises
// from the frame's top edge (2 px above the channel) to 25 px above the channel, 17 px text (the font's 24-unit line
// holds leading, so its line is 21 px) with 11 px padding.
constexpr float TabOverhang = 27.733333f;
constexpr float TabTop = 13.333333f;
constexpr float TabBottom = 1.066667f;
constexpr float TabTextHeight = 11.2f;
constexpr float TabPadding = 5.866667f;
constexpr float TabRim = 0.75f;

constexpr uint32_t abgr(uint32_t rgb, uint32_t alpha = 0xff)
{
    return alpha << 24 | (rgb & 0xffu) << 16 | (rgb & 0xff00u) | (rgb >> 16 & 0xffu);
}

uint32_t sample(const Gradient &gradient, float t)
{
    size_t index = 1;

    while (index + 1 < gradient.size() && t > gradient[index].at)
    {
        ++index;
    }

    const Stop &from = gradient[index - 1];
    const Stop &to = gradient[index];
    const float mix = std::clamp((t - from.at) / std::max(0.0001f, to.at - from.at), 0.0f, 1.0f);
    uint32_t rgb = 0;

    for (int shift : {0, 8, 16})
    {
        const float a = float(from.rgb >> shift & 0xffu);
        const float b = float(to.rgb >> shift & 0xffu);
        rgb |= uint32_t(std::lround(a + (b - a) * mix)) << shift;
    }

    return rgb;
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

struct Tab
{
    Rect box;
    std::string text;
    uint32_t colour = Ivory;
};

struct Layout
{
    Rect channel;
    float unit = 1;
    std::optional<Tab> right;
    std::optional<Tab> left;
};

float fontScale(GameplayScreenRuntime &context, float height)
{
    const float wanted = height / float(std::max(1, context.hudFontHeight(TabFont)));
    return wanted >= 1.0f ? GameplayHudCommon::snappedHudFontScale(wanted) : std::max(0.5f, wanted);
}

float textWidth(GameplayScreenRuntime &context, float height, const std::string &text)
{
    return context.measureHudTextWidth(TabFont, text) * fontScale(context, height);
}

// A tab of the texts that fits beside the frame's middle, the first that fits; `fromRight` ends it at `edge`.
std::optional<Tab> fitTab(GameplayScreenRuntime &context, const Layout &layout, float edge, bool fromRight,
    const std::vector<std::string> &texts, uint32_t colour)
{
    const float u = layout.unit;
    const float middle = layout.channel.x + layout.channel.width / 2;
    const float room = fromRight ? edge - middle : middle - edge;

    for (const std::string &text : texts)
    {
        const float width = std::ceil(textWidth(context, TabTextHeight * u, text) + 2 * TabPadding * u);

        if (width <= room)
        {
            Tab tab;
            tab.box = {fromRight ? edge - width : edge, layout.channel.y - TabTop * u, width,
                (TabTop - TabBottom) * u};
            tab.text = text;
            tab.colour = colour;
            return tab;
        }
    }

    return std::nullopt;
}

// On a cleared map with satchels left, the gather key loots them all (GameplayActionController::gatherLoot): "G: loot
// all" with the key it is bound to; empty otherwise.
std::string lootAllHint(GameplayScreenRuntime &context, const RulesetMapProgress &progress)
{
    const Party *pParty = context.partyReadOnly();
    const IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();

    if (!progress.complete || progress.kind == RulesetMapProgress::Kind::Arena || pParty == nullptr
        || pWorldRuntime == nullptr || !pParty->rules().items.lootGathering()
        || pWorldRuntime->lootableCorpseActorIndices().empty())
    {
        return {};
    }

    const InputBinding &binding =
        context.settingsSnapshot().keyboard.bindings[keyboardActionIndex(KeyboardAction::GatherLoot)];
    return binding.kind == InputBindingKind::None
        ? std::string()
        : Engine::tr("{key}: loot all", {{"key", inputBindingDisplayName(binding)}});
}

std::optional<Layout> resolveLayout(GameplayScreenRuntime &context, int width, int height,
    const RulesetMapProgress &progress)
{
    const std::optional<GameplayResolvedHudLayoutElement> channel =
        context.resolveHudLayoutElement("MapProgressChannel", width, height, 0, 0);

    if (!channel || channel->width <= 0 || channel->height <= 0)
    {
        return std::nullopt;
    }

    Layout layout;
    layout.channel = {std::round(channel->x), std::round(channel->y), std::round(channel->width),
        std::max(1.0f, std::round(channel->height))};
    layout.unit = channel->scale;
    const float u = layout.unit;
    const uint32_t colour = progress.complete && progress.kind != RulesetMapProgress::Kind::Arena ? GoldText : Ivory;
    std::vector<std::string> texts = {GameplayMapProgressBar::tabText(progress, false)};

    if (const std::string hint = lootAllHint(context, progress); !hint.empty())
    {
        texts.insert(texts.begin(), texts.front() + " \xB7 " + hint);
    }

    // The Arena keeps its level on a narrower tab ("Arena L5 \xB7 60 %"), as the study's short form.
    if (progress.kind == RulesetMapProgress::Kind::Arena)
    {
        texts.push_back(Engine::tr("Arena L{level}", {{"level", int64_t(progress.arenaLevel)}}) + " \xB7 "
            + GameplayMapProgressBar::percentText(progress.percent));
    }

    texts.push_back(GameplayMapProgressBar::tabText(progress, true));
    layout.right = fitTab(context, layout, layout.channel.x + layout.channel.width + TabOverhang * u, true, texts,
        colour);

    if (progress.kind == RulesetMapProgress::Kind::DimensionRun)
    {
        const std::string power = Engine::tr("Power {power}", {{"power", int64_t(progress.dimensionPower)}});
        layout.left = fitTab(context, layout, layout.channel.x - TabOverhang * u, false,
            {Engine::tr("Dimension") + " \xB7 " + power, power}, DimensionText);
    }

    return layout;
}

class Batch
{
public:
    explicit Batch(GameplayScreenRuntime &context)
        : m_context(context)
    {
    }

    void fill(const Rect &rect, uint32_t rgb, uint32_t alpha = 0xff)
    {
        if (rect.width <= 0 || rect.height <= 0)
        {
            return;
        }

        if (const std::optional<GameplayHudPaletteColor> colour =
                m_context.gameplayUiRuntime().ensureHudPaletteColor(abgr(rgb, alpha)))
        {
            m_quads.push_back(gameplayHudPaletteQuad(*colour, rect.x, rect.y, rect.width, rect.height));
        }
    }

    // A gradient top to bottom, one strip per pixel row.
    void gradient(const Rect &rect, const Gradient &gradient)
    {
        const int rows = std::max(1, int(std::lround(rect.height)));
        const float rowHeight = rect.height / rows;

        for (int row = 0; row < rows; ++row)
        {
            fill({rect.x, rect.y + row * rowHeight, rect.width, rowHeight}, sample(gradient, (row + 0.5f) / rows));
        }
    }

    // A diamond of a radius around a centre, row by row.
    void diamond(float centreX, float centreY, float radius, uint32_t rgb)
    {
        const int rows = std::max(1, int(std::lround(2 * radius)));
        const float rowHeight = 2 * radius / rows;

        for (int row = 0; row < rows; ++row)
        {
            const float middle = -radius + (row + 0.5f) * rowHeight;
            const float half = radius - std::abs(middle);
            fill({centreX - half, centreY - radius + row * rowHeight, 2 * half, rowHeight}, rgb);
        }
    }

    void submit()
    {
        if (!m_quads.empty())
        {
            m_context.submitHudQuadBatch(m_quads);
            m_quads.clear();
        }
    }

private:
    GameplayScreenRuntime &m_context;
    std::vector<GameplayHudBatchQuad> m_quads;
};

void drawTab(Batch &batch, const Tab &tab, float u)
{
    const Rect &box = tab.box;
    const float rim = std::max(1.0f, std::round(TabRim * u));
    // Its drop shadow, then the dark plate with a brass rim that is lit on top; open at the bottom on the frame.
    batch.fill({box.x - rim, box.y + rim, box.width + 2 * rim, box.height}, Black, 0x90);
    batch.fill(box, TabFill);
    batch.fill({box.x + rim, box.y, box.width - 2 * rim, rim}, RimLight);
    batch.fill({box.x, box.y + rim, rim, box.height - rim}, RimMid);
    batch.fill({box.x + box.width - rim, box.y + rim, rim, box.height - rim}, RimMid);
}

std::optional<RulesetMapProgress> currentProgress(GameplayScreenRuntime &context)
{
    const Party *pParty = context.partyReadOnly();

    if (pParty == nullptr || context.worldRuntime() == nullptr
        || context.currentHudScreenState() != GameplayHudScreenState::Gameplay)
    {
        return std::nullopt;
    }

    return pParty->rules().monsters.mapProgress(*context.worldRuntime());
}
}

void GameplayMapProgressBar::renderHud(GameplayScreenRuntime &context, int width, int height)
{
    const std::optional<RulesetMapProgress> progress = currentProgress(context);

    if (!progress)
    {
        return;
    }

    const std::optional<Layout> layout = resolveLayout(context, width, height, *progress);

    if (!layout)
    {
        return;
    }

    const Rect &channel = layout->channel;
    const float u = layout->unit;
    const Gradient &fill = progress->complete && progress->kind != RulesetMapProgress::Kind::Arena ? GoldFill
        : progress->kind == RulesetMapProgress::Kind::DimensionRun ? Dimension : Violet;
    const float filled = std::round(channel.width * float(std::clamp(progress->percent / 100, 0.0, 1.0)));
    Batch batch(context);
    batch.fill(channel, ChannelTrack);

    if (filled > 0)
    {
        // A soft glow a pixel around the fill, then the fill itself.
        const float glow = std::max(1.0f, std::round(0.6f * u));
        batch.fill({channel.x, channel.y - glow, filled, channel.height + 2 * glow}, sample(fill, 0.45f), 0x50);
        batch.gradient({channel.x, channel.y, filled, channel.height}, fill);
    }

    // The revival mark: a line through the channel with a diamond above it, red until passed, then ivory.
    if (progress->revival)
    {
        const uint32_t colour = progress->revivalPassed ? Ivory : RevivalRed;
        const float x = std::round(channel.x + channel.width * progress->revivalPosition);
        const float top = channel.y - 1.6f * u;
        const float bottom = channel.y + channel.height + 0.533333f * u;
        const float line = std::max(1.0f, std::round(0.96f * u));
        const float outline = std::max(1.0f, std::round(0.5f * u));
        const float radius = 2.4f * u;
        batch.fill({x - line / 2 - outline, top, line + 2 * outline, bottom - top}, Black, 0xd0);
        batch.fill({x - line / 2, top, line, bottom - top}, colour);
        batch.diamond(x, top - radius + 0.5f * u, radius + outline, Black);
        batch.diamond(x, top - radius + 0.5f * u, radius, colour);
    }

    for (const std::optional<Tab> &tab : {layout->right, layout->left})
    {
        if (tab)
        {
            drawTab(batch, *tab, u);
        }
    }

    batch.submit();

    for (const std::optional<Tab> &tab : {layout->right, layout->left})
    {
        if (!tab)
        {
            continue;
        }

        const float scale = fontScale(context, TabTextHeight * u);
        const float textX = tab->box.x + (tab->box.width - context.measureHudTextWidth(TabFont, tab->text) * scale) / 2;
        const float textY = tab->box.y + (tab->box.height - TabTextHeight * u) / 2 + 0.25f * u;
        context.renderHudTextLine(TabFont, abgr(tab->colour), tab->text, std::round(textX), std::round(textY), scale);
    }
}

std::optional<GameplayMapProgressBar::Popup> GameplayMapProgressBar::popupAt(
    GameplayScreenRuntime &context, int width, int height, float pointerX, float pointerY)
{
    // Cheap first: only a pointer near the channel's row reads the map's progress.
    const std::optional<GameplayResolvedHudLayoutElement> channel =
        context.resolveHudLayoutElement("MapProgressChannel", width, height, 0, 0);

    if (!channel || pointerY < channel->y - TabTop * channel->scale
        || pointerY > channel->y + channel->height + 3 * channel->scale)
    {
        return std::nullopt;
    }

    const std::optional<RulesetMapProgress> progress = currentProgress(context);
    const std::optional<Layout> layout = progress ? resolveLayout(context, width, height, *progress) : std::nullopt;

    if (!layout)
    {
        return std::nullopt;
    }

    const float u = layout->unit;
    const Rect band = {layout->channel.x, layout->channel.y - 2 * u, layout->channel.width,
        layout->channel.height + 5 * u};
    const bool hovered = band.contains(pointerX, pointerY)
        || (layout->right && layout->right->box.contains(pointerX, pointerY))
        || (layout->left && layout->left->box.contains(pointerX, pointerY));

    if (!hovered)
    {
        return std::nullopt;
    }

    // It rises above the bar, its right edge at the channel's.
    Popup popup;
    popup.title = progress->kind == RulesetMapProgress::Kind::Arena ? Engine::tr("Endless Arena")
                                                                     : Engine::tr("Map progress");
    popup.body = popupBody(*progress);
    popup.x = layout->channel.x;
    popup.y = layout->channel.y - TabTop * u;
    popup.width = layout->channel.width;
    popup.height = TabTop * u;
    return popup;
}
}
