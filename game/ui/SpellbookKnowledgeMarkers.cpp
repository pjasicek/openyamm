#include "game/ui/SpellbookKnowledgeMarkers.h"

#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayUiRuntime.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
// Sizes in HUD units.
constexpr float PipDiameter = 8.0f;
constexpr float PipGap = 1.5f;
constexpr float PadX = 2.5f;
constexpr float PadY = 2.5f;
constexpr float PlateRadius = 5.0f;
constexpr float PlateBorder = 0.6f;
// Bump when the drawing changes, so cached plates are redrawn.
constexpr const char *TextureVersion = "1";

struct Color
{
    float r = 0.0f;
    float g = 0.0f;
    float b = 0.0f;
};

constexpr Color rgb(uint32_t value)
{
    return {float((value >> 16) & 0xffu) / 255.0f, float((value >> 8) & 0xffu) / 255.0f, float(value & 0xffu) / 255.0f};
}

// The approved study's colours.
constexpr Color PlateFill = rgb(0x0a0e0c);
constexpr float PlateFillAlpha = 0.86f;
constexpr Color PlateLine = rgb(0x7a6440);
constexpr Color KnownDisc = rgb(0xd4ad55);
constexpr Color KnownTick = rgb(0x1d1508);
constexpr Color LearnRing = rgb(0x6cc4e0);
constexpr Color LearnPlus = rgb(0x9fe0f4);
constexpr Color TrainRing = rgb(0x8f8166);
constexpr Color TrainChevron = rgb(0xb9a77f);
constexpr Color NeverDash = rgb(0x6a665e);

struct Point
{
    float x = 0.0f;
    float y = 0.0f;
};

// Premultiplied canvas, composited front to back with "over".
class Canvas
{
public:
    Canvas(int width, int height, float pixelsPerUnit)
        : m_width(width)
        , m_height(height)
        , m_pixelsPerUnit(pixelsPerUnit)
        , m_pixels(size_t(width) * size_t(height) * 4, 0.0f)
    {
    }

    // Paints `color` where `distance(point in units)` (signed, in units, negative inside) covers the pixel.
    template <typename Distance>
    void paint(const Color &color, float alpha, const Distance &distance)
    {
        for (int y = 0; y < m_height; ++y)
        {
            for (int x = 0; x < m_width; ++x)
            {
                const Point point = {(float(x) + 0.5f) / m_pixelsPerUnit, (float(y) + 0.5f) / m_pixelsPerUnit};
                const float coverage = std::clamp(0.5f - distance(point) * m_pixelsPerUnit, 0.0f, 1.0f) * alpha;

                if (coverage <= 0.0f)
                {
                    continue;
                }

                float *pPixel = &m_pixels[(size_t(y) * size_t(m_width) + size_t(x)) * 4];
                pPixel[0] = color.r * coverage + pPixel[0] * (1.0f - coverage);
                pPixel[1] = color.g * coverage + pPixel[1] * (1.0f - coverage);
                pPixel[2] = color.b * coverage + pPixel[2] * (1.0f - coverage);
                pPixel[3] = coverage + pPixel[3] * (1.0f - coverage);
            }
        }
    }

    std::vector<uint8_t> bgra() const
    {
        std::vector<uint8_t> result(m_pixels.size());

        for (size_t index = 0; index < m_pixels.size(); index += 4)
        {
            const float alpha = m_pixels[index + 3];
            const auto channel = [alpha](float premultiplied)
            {
                const float straight = alpha > 0.0f ? premultiplied / alpha : 0.0f;
                return uint8_t(std::lround(std::clamp(straight, 0.0f, 1.0f) * 255.0f));
            };
            result[index + 0] = channel(m_pixels[index + 2]);
            result[index + 1] = channel(m_pixels[index + 1]);
            result[index + 2] = channel(m_pixels[index + 0]);
            result[index + 3] = uint8_t(std::lround(std::clamp(alpha, 0.0f, 1.0f) * 255.0f));
        }

        return result;
    }

private:
    int m_width;
    int m_height;
    float m_pixelsPerUnit;
    std::vector<float> m_pixels;
};

float circleDistance(const Point &point, const Point &centre, float radius)
{
    return std::hypot(point.x - centre.x, point.y - centre.y) - radius;
}

float segmentDistance(const Point &point, const Point &a, const Point &b)
{
    const float abX = b.x - a.x;
    const float abY = b.y - a.y;
    const float length = abX * abX + abY * abY;
    const float t = length > 0.0f ? std::clamp(((point.x - a.x) * abX + (point.y - a.y) * abY) / length, 0.0f, 1.0f)
                                  : 0.0f;
    return std::hypot(point.x - (a.x + abX * t), point.y - (a.y + abY * t));
}

float roundedBoxDistance(const Point &point, float width, float height, float radius)
{
    const float qx = std::abs(point.x - width * 0.5f) - (width * 0.5f - radius);
    const float qy = std::abs(point.y - height * 0.5f) - (height * 0.5f - radius);
    return std::hypot(std::max(qx, 0.0f), std::max(qy, 0.0f)) + std::min(std::max(qx, qy), 0.0f) - radius;
}

// A stroked polyline with round caps and joins, `points` relative to the pip's top-left corner.
template <size_t Count>
void stroke(
    Canvas &canvas, const Point &origin, const std::array<Point, Count> &points, float width, const Color &color)
{
    canvas.paint(color, 1.0f, [&](const Point &point)
        {
            float distance = 1.0e9f;

            for (size_t index = 0; index + 1 < Count; ++index)
            {
                const Point a = {origin.x + points[index].x, origin.y + points[index].y};
                const Point b = {origin.x + points[index + 1].x, origin.y + points[index + 1].y};
                distance = std::min(distance, segmentDistance(point, a, b));
            }

            return distance - width * 0.5f;
        });
}

void ring(Canvas &canvas, const Point &centre, float thickness, const Color &color)
{
    const float radius = PipDiameter * 0.5f;
    canvas.paint(color, 1.0f, [&](const Point &point)
        {
            return std::abs(circleDistance(point, centre, radius - thickness * 0.5f)) - thickness * 0.5f;
        });
}

void paintPip(Canvas &canvas, SpellbookKnowledge knowledge, const Point &origin)
{
    const Point centre = {origin.x + PipDiameter * 0.5f, origin.y + PipDiameter * 0.5f};

    switch (knowledge)
    {
        case SpellbookKnowledge::Known:
            canvas.paint(KnownDisc, 1.0f, [&](const Point &point)
                {
                    return circleDistance(point, centre, PipDiameter * 0.5f);
                });
            stroke<3>(canvas, origin, {{{2.25f, 4.1f}, {3.5f, 5.3f}, {5.8f, 2.7f}}}, 1.0f, KnownTick);
            break;

        case SpellbookKnowledge::CanLearn:
            canvas.paint(LearnRing, 0.16f, [&](const Point &point)
                {
                    return circleDistance(point, centre, PipDiameter * 0.5f - 0.5f);
                });
            ring(canvas, centre, 1.0f, LearnRing);
            stroke<2>(canvas, origin, {{{4.0f, 2.25f}, {4.0f, 5.75f}}}, 1.0f, LearnPlus);
            stroke<2>(canvas, origin, {{{2.25f, 4.0f}, {5.75f, 4.0f}}}, 1.0f, LearnPlus);
            break;

        case SpellbookKnowledge::NeedsTraining:
            ring(canvas, centre, 0.75f, TrainRing);
            stroke<3>(canvas, origin, {{{2.5f, 4.8f}, {4.0f, 3.3f}, {5.5f, 4.8f}}}, 0.9f, TrainChevron);
            break;

        case SpellbookKnowledge::CannotLearn:
        default:
            stroke<2>(canvas, origin, {{{2.75f, 4.0f}, {5.25f, 4.0f}}}, 1.0f, NeverDash);
            break;
    }
}

char signatureLetter(SpellbookKnowledge knowledge)
{
    switch (knowledge)
    {
        case SpellbookKnowledge::Known:
            return 'k';
        case SpellbookKnowledge::CanLearn:
            return 'l';
        case SpellbookKnowledge::NeedsTraining:
            return 't';
        case SpellbookKnowledge::CannotLearn:
        default:
            return 'x';
    }
}
}

namespace SpellbookKnowledgeMarkers
{
float plateWidth(size_t memberCount)
{
    const float count = float(std::max<size_t>(memberCount, 1));
    return PadX * 2.0f + PipDiameter * count + PipGap * (count - 1.0f);
}

float plateHeight()
{
    return PadY * 2.0f + PipDiameter;
}

void render(
    GameplayScreenRuntime &context,
    const std::vector<SpellbookKnowledge> &knowledge,
    float centerX,
    float top,
    float scale)
{
    if (knowledge.empty() || scale <= 0.0f)
    {
        return;
    }

    // Drawn at the plate's on-screen pixel size, so it stays sharp at every HUD scale.
    const int pixelHeight = std::max(1, int(std::lround(plateHeight() * scale)));
    const float pixelsPerUnit = float(pixelHeight) / plateHeight();
    const int pixelWidth = std::max(1, int(std::lround(plateWidth(knowledge.size()) * pixelsPerUnit)));
    std::string signature;

    for (SpellbookKnowledge entry : knowledge)
    {
        signature.push_back(signatureLetter(entry));
    }

    const std::string textureName = "spellbook_markers_" + signature + "_" + std::to_string(pixelHeight);
    GameplayUiRuntime &uiRuntime = context.gameplayUiRuntime();
    std::optional<GameplayHudTextureHandle> texture =
        uiRuntime.findCachedDynamicHudTexture(textureName, TextureVersion);

    if (!texture)
    {
        const float widthUnits = float(pixelWidth) / pixelsPerUnit;
        Canvas canvas(pixelWidth, pixelHeight, pixelsPerUnit);
        canvas.paint(PlateFill, PlateFillAlpha, [&](const Point &point)
            {
                return roundedBoxDistance(point, widthUnits, plateHeight(), PlateRadius);
            });
        canvas.paint(PlateLine, 1.0f, [&](const Point &point)
            {
                const float distance = roundedBoxDistance(point, widthUnits, plateHeight(), PlateRadius);
                return std::max(distance, -distance - PlateBorder);
            });

        for (size_t index = 0; index < knowledge.size(); ++index)
        {
            const Point origin = {PadX + float(index) * (PipDiameter + PipGap), PadY};
            paintPip(canvas, knowledge[index], origin);
        }

        texture = uiRuntime.ensureDynamicHudTexture(textureName, pixelWidth, pixelHeight, canvas.bgra());

        if (!texture)
        {
            return;
        }

        uiRuntime.setDynamicHudTextureContentSignature(textureName, TextureVersion);
    }

    context.submitHudTexturedQuad(
        *texture,
        std::round(centerX - float(pixelWidth) * 0.5f),
        std::round(top),
        float(pixelWidth),
        float(pixelHeight));
}
}
}
