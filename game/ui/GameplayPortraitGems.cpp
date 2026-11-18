#include "game/ui/GameplayPortraitGems.h"

#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayUiRuntime.h"

#include <array>
#include <cstdint>

namespace OpenYAMM::Game
{
namespace
{
// The badge texture's size; gems are made at the pixel size they are drawn at, so they stay sharp at any HUD scale.
constexpr int GemTextureSize = 32;
constexpr int MinimumGemPixels = 6;

enum class GemTexture
{
    Socket,
    Ruby,
    Amber,
    PaleGold,
    Badge
};

// Light, middle and dark stops of each lit stone (the study's colours: WoW red, fire amber, the second lap's gold).
constexpr std::array<std::array<uint32_t, 3>, 3> StoneColors = {{
    {{0xff8a70, 0xd8402c, 0x6e1408}},
    {{0xffd27a, 0xf08a2a, 0x7a3408}},
    {{0xfff4c8, 0xf2d27a, 0x8a6420}}
}};

float channel(uint32_t color, int shift)
{
    return float((color >> shift) & 0xff);
}

uint32_t mix(uint32_t from, uint32_t to, float t)
{
    t = std::clamp(t, 0.0f, 1.0f);
    uint32_t result = 0;

    for (int shift : {0, 8, 16})
    {
        result |= uint32_t(std::lround(channel(from, shift) + (channel(to, shift) - channel(from, shift)) * t))
            << shift;
    }

    return result;
}

void putPixel(std::vector<uint8_t> &pixels, size_t pixel, uint32_t rgb, float alpha)
{
    // The HUD's dynamic textures are BGRA.
    pixels[pixel * 4 + 0] = uint8_t(rgb & 0xff);
    pixels[pixel * 4 + 1] = uint8_t((rgb >> 8) & 0xff);
    pixels[pixel * 4 + 2] = uint8_t((rgb >> 16) & 0xff);
    pixels[pixel * 4 + 3] = uint8_t(std::lround(std::clamp(alpha, 0.0f, 1.0f) * 255));
}

// Coverage of a disc edge at distance `distance` from the centre, one texel wide.
float edge(float radius, float distance, float texel)
{
    return std::clamp((radius - distance) / texel + 0.5f, 0.0f, 1.0f);
}

// The share of a gem's radius the lit stone takes: all but the socket's black and bronze rims, a pixel each.
float stoneRadius(int size)
{
    return std::max(0.3f, 1.0f - 4.0f / float(size));
}

std::vector<uint8_t> gemPixels(GemTexture kind, int size)
{
    const float texel = 2.0f / size;
    const float stone = stoneRadius(size);
    const float bronzeRadius = 1.0f - texel;
    std::vector<uint8_t> pixels(size_t(size * size * 4), 0);

    for (int y = 0; y < size; ++y)
    {
        for (int x = 0; x < size; ++x)
        {
            const float u = (x + 0.5f) / size * 2 - 1;
            const float v = (y + 0.5f) / size * 2 - 1;
            const float distance = std::hypot(u, v);
            const size_t pixel = size_t(y * size + x);

            if (kind == GemTexture::Socket)
            {
                // A black outer ring, a worn bronze rim and a dark recessed socket, each band a pixel or more, their
                // edges blended over one pixel.
                const float depth = std::hypot(u + 0.1f * stone, v + 0.2f * stone) / stone;
                const uint32_t recess = mix(0x2a2f2c, 0x080b0a, depth / 1.4f);
                uint32_t color = mix(0x050706, 0x8a7c56, edge(bronzeRadius, distance, texel));
                color = mix(color, recess, edge(stone, distance, texel));
                putPixel(pixels, pixel, color, edge(1.0f, distance, texel));
                continue;
            }

            // A lit stone: a radial gradient from an upper-left light with a soft white glint.
            const std::array<uint32_t, 3> &stops = StoneColors[size_t(kind) - size_t(GemTexture::Ruby)];
            const float lightDistance =
                std::hypot(u + 0.24f * stone, v + 0.36f * stone) / (1.5f * stone);
            uint32_t color = lightDistance < 0.55f ? mix(stops[0], stops[1], lightDistance / 0.55f)
                : mix(stops[1], stops[2], (lightDistance - 0.55f) / 0.45f);
            const float glint = std::hypot(u + 0.32f * stone, v + 0.36f * stone) / (0.26f * stone);
            color = mix(color, 0xffffff, 0.55f * std::clamp(1.2f - glint, 0.0f, 1.0f));
            putPixel(pixels, pixel, color, edge(stone, distance, texel));
        }
    }

    return pixels;
}

// A pill-shaped badge, 2:1: half discs at both ends so its middle third can stretch.
std::vector<uint8_t> badgePixels()
{
    constexpr int Height = GemTextureSize / 2;
    constexpr int Width = Height * 2;
    constexpr float Radius = Height / 2.0f;
    std::vector<uint8_t> pixels(size_t(Width * Height * 4), 0);

    for (int y = 0; y < Height; ++y)
    {
        for (int x = 0; x < Width; ++x)
        {
            const float px = x + 0.5f;
            const float py = y + 0.5f;
            const float cx = std::clamp(px, Radius, Width - Radius);
            const float distance = std::hypot(px - cx, py - Radius);
            const uint32_t color = distance > Radius - 1.2f ? 0x8c815f : 0x0b1212;
            putPixel(pixels, size_t(y * Width + x), color, std::clamp(Radius - distance + 0.5f, 0.0f, 1.0f));
        }
    }

    return pixels;
}

std::optional<GameplayHudTextureHandle> gemTexture(GameplayScreenRuntime &context, GemTexture kind, int size = 0)
{
    constexpr std::array<const char *, 5> Names = {{
        "__portrait_gem_socket__", "__portrait_gem_ruby__", "__portrait_gem_amber__", "__portrait_gem_gold__",
        "__portrait_gem_badge__"
    }};
    constexpr const char *pSignature = "portrait-gems-v2";
    GameplayUiRuntime &runtime = context.gameplayUiRuntime();
    const bool badge = kind == GemTexture::Badge;
    const int pixelsAcross = badge ? GemTextureSize : std::max(size, MinimumGemPixels);
    const std::string name = std::string(Names[size_t(kind)]) + (badge ? "" : std::to_string(pixelsAcross));
    std::optional<GameplayHudTextureHandle> texture = runtime.findCachedDynamicHudTexture(name, pSignature);

    if (!texture)
    {
        texture = runtime.ensureDynamicHudTexture(name, pixelsAcross,
            badge ? GemTextureSize / 2 : pixelsAcross, badge ? badgePixels() : gemPixels(kind, pixelsAcross));

        if (texture)
        {
            runtime.setDynamicHudTextureContentSignature(name, pSignature);
        }
    }

    return texture;
}

struct ScreenGem
{
    float x = 0;
    float y = 0;
    float radius = 0;
};

// The gems in screen pixels: the pure layout runs in the arc's logical units around its centre.
std::vector<ScreenGem> screenGems(int pips, const GameplayResolvedHudLayoutElement &arc, float strokeWidth)
{
    const float scale = std::max(0.001f, arc.scale);
    const float centreX = arc.x + arc.width * 0.5f;
    const float centreY = arc.y + arc.height * 0.5f;
    std::vector<ScreenGem> gems;

    for (const PortraitGemPlace &place :
        portraitGemPlaces(pips, 0, 0, arc.width * 0.5f / scale, arc.height * 0.5f / scale, strokeWidth))
    {
        gems.push_back({centreX + place.x * scale, centreY + place.y * scale, place.radius * scale});
    }

    return gems;
}

// The number badge's height in logical units.
constexpr float BadgeHeight = 9.2f;

// A row's badge is wider than the arc's: the unit frame's scale draws the digits wider against the pill.
float rowBadgeWidth(size_t digits)
{
    return 6.0f + 6.0f * float(digits);
}

// The gems, socket and lit stone each, at their screen places.
void renderGems(GameplayScreenRuntime &context, const PortraitCounter &counter, const std::vector<ScreenGem> &gems)
{
    const std::vector<PortraitGemFill> fills = portraitGemFills(counter);
    const GemTexture stone = counter.kind == PortraitCounterKind::ComboPoints ? GemTexture::Ruby : GemTexture::Amber;
    GameplayUiRuntime &runtime = context.gameplayUiRuntime();

    for (size_t k = 0; k < gems.size() && k < fills.size(); ++k)
    {
        // Whole pixels, one texel to a pixel, so the small gems stay crisp.
        const ScreenGem &gem = gems[k];
        const int pixelsAcross = std::max(MinimumGemPixels, int(std::lround(2 * gem.radius)));
        const float size = float(pixelsAcross);
        const float left = std::round(gem.x - size * 0.5f);
        const float top = std::round(gem.y - size * 0.5f);
        const float stoneShare = stoneRadius(pixelsAcross);
        const std::optional<GameplayHudTextureHandle> socket = gemTexture(context, GemTexture::Socket, pixelsAcross);

        if (socket)
        {
            runtime.submitHudTexturedQuad(socket->textureHandle, left, top, size, size);
        }

        const PortraitGemFill &fill = fills[k];
        const std::optional<GameplayHudTextureHandle> lit =
            fill.fill > 0 ? gemTexture(context, fill.secondLap ? GemTexture::PaleGold : stone, pixelsAcross)
                          : std::nullopt;

        if (!lit)
        {
            continue;
        }

        // A part-lit stone shows its lower part: the cut runs across the stone, not the whole texture.
        const float cut = fill.fill >= 1 ? 0.0f : 0.5f + 0.5f * stoneShare * (1 - 2 * fill.fill);
        runtime.submitHudTexturedQuad(lit->textureHandle, left, top + size * cut, size, size * (1 - cut),
            0, cut, 1, 1);
    }
}

// The exact number in a small badge centred at `centreX`, `centreY` (screen pixels), `badgeWidth` logical units wide.
void renderBadge(GameplayScreenRuntime &context, float centreX, float centreY, float badgeWidth, float scale,
    const std::string &text, const std::string &badgeLayoutId)
{
    GameplayUiRuntime &runtime = context.gameplayUiRuntime();
    const float height = BadgeHeight * scale;
    const float width = badgeWidth * scale;
    const float x = centreX - width / 2;
    const float y = centreY - height / 2;

    if (const std::optional<GameplayHudTextureHandle> badge = gemTexture(context, GemTexture::Badge))
    {
        const float cap = height / 2;
        runtime.submitHudTexturedQuad(badge->textureHandle, x, y, cap, height, 0, 0, 0.25f, 1);
        runtime.submitHudTexturedQuad(badge->textureHandle, x + cap, y, width - 2 * cap, height, 0.25f, 0, 0.75f, 1);
        runtime.submitHudTexturedQuad(badge->textureHandle, x + width - cap, y, cap, height, 0.75f, 0, 1, 1);
    }

    if (const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(badgeLayoutId))
    {
        // The label's own box is wider than the badge so a centred number is never clipped.
        context.renderLayoutLabel(*pLayout, {x - 4 * scale, y, width + 8 * scale, height, scale}, text);
    }
}
}

void renderPortraitCounterGems(GameplayScreenRuntime &context, const PortraitCounter &counter,
    const GameplayResolvedHudLayoutElement &healthArc, float strokeWidth, const std::string &badgeLayoutId)
{
    if (counter.kind == PortraitCounterKind::None || counter.pips <= 0)
    {
        return;
    }

    renderGems(context, counter, screenGems(counter.pips, healthArc, strokeWidth));

    if (counter.kind != PortraitCounterKind::Stacks || counter.amount <= 0)
    {
        return;
    }

    // The exact number in a small badge below the first gem.
    const float scale = std::max(0.001f, healthArc.scale);
    const std::string text = std::to_string(int(std::lround(counter.amount)));
    const float badgeWidth = BadgeHeight + 5.0f * float(text.size() - 1);
    const PortraitGemPlace place = portraitGemBadgePlace(badgeWidth, BadgeHeight, healthArc.width * 0.5f / scale,
        healthArc.height * 0.5f / scale, strokeWidth);
    renderBadge(context, healthArc.x + healthArc.width * 0.5f + place.x * scale,
        healthArc.y + healthArc.height * 0.5f + place.y * scale, badgeWidth, scale, text, badgeLayoutId);
}

void renderCounterGemRow(GameplayScreenRuntime &context, const PortraitCounter &counter, float centreX, float centreY,
    float scale, const std::string &badgeLayoutId)
{
    if (counter.kind == PortraitCounterKind::None || counter.pips <= 0)
    {
        return;
    }

    scale = std::max(0.001f, scale);
    std::vector<ScreenGem> gems;
    for (const PortraitGemPlace &place : counterGemRowPlaces(counter.pips, 0, 0))
    {
        gems.push_back({centreX + place.x * scale, centreY + place.y * scale, place.radius * scale});
    }
    renderGems(context, counter, gems);

    if (counter.kind != PortraitCounterKind::Stacks || counter.amount <= 0)
    {
        return;
    }

    const std::string text = std::to_string(int(std::lround(counter.amount)));
    const float badgeWidth = rowBadgeWidth(text.size());
    const PortraitGemPlace place = counterGemRowBadgePlace(counter.pips, badgeWidth, BadgeHeight, 0, 0);
    renderBadge(context, centreX + place.x * scale, centreY + place.y * scale, badgeWidth, scale, text,
        badgeLayoutId);
}

std::optional<GameplayResolvedHudLayoutElement> counterGemRowBounds(const PortraitCounter &counter, float centreX,
    float centreY, float scale)
{
    if (counter.kind == PortraitCounterKind::None || counter.pips <= 0)
    {
        return std::nullopt;
    }

    const std::vector<PortraitGemPlace> places = counterGemRowPlaces(counter.pips, 0, 0);
    float right = places.back().x + places.back().radius;
    if (counter.kind == PortraitCounterKind::Stacks)
    {
        // Room for a two-digit badge.
        const float badgeWidth = rowBadgeWidth(2);
        const PortraitGemPlace badge = counterGemRowBadgePlace(counter.pips, badgeWidth, BadgeHeight, 0, 0);
        right = badge.x + badgeWidth / 2;
    }
    const float left = places.front().x - places.front().radius;
    const float half = std::max(places.front().radius, BadgeHeight / 2);
    return GameplayResolvedHudLayoutElement{centreX + left * scale, centreY - half * scale, (right - left) * scale,
        2 * half * scale, scale};
}

std::optional<GameplayResolvedHudLayoutElement> portraitCounterGemBounds(const PortraitCounter &counter,
    const GameplayResolvedHudLayoutElement &healthArc, float strokeWidth)
{
    if (counter.kind == PortraitCounterKind::None || counter.pips <= 0)
    {
        return std::nullopt;
    }

    float left = 1e9f;
    float top = 1e9f;
    float right = -1e9f;
    float bottom = -1e9f;

    for (const ScreenGem &gem : screenGems(counter.pips, healthArc, strokeWidth))
    {
        left = std::min(left, gem.x - gem.radius);
        top = std::min(top, gem.y - gem.radius);
        right = std::max(right, gem.x + gem.radius);
        bottom = std::max(bottom, gem.y + gem.radius);
    }

    if (counter.kind == PortraitCounterKind::Stacks)
    {
        // The badge below the first gem.
        const float scale = std::max(0.001f, healthArc.scale);
        const PortraitGemPlace badge = portraitGemBadgePlace(14.2f, 9.2f, healthArc.width * 0.5f / scale,
            healthArc.height * 0.5f / scale, strokeWidth);
        const float centreX = healthArc.x + healthArc.width * 0.5f + badge.x * scale;
        left = std::min(left, centreX - 7.1f * scale);
        bottom = std::max(bottom, healthArc.y + healthArc.height * 0.5f + (badge.y + 4.6f) * scale);
    }

    return GameplayResolvedHudLayoutElement{left, top, right - left, bottom - top, healthArc.scale};
}
}
