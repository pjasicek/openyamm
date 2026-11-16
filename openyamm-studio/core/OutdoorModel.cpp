#include "core/OutdoorModel.h"

#include "core/CoreMath.h"
#include "game/FaceEnums.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Studio
{
namespace
{
OutdoorModelPoint normalOf(const std::vector<OutdoorModelPoint> &points, double &length)
{
    OutdoorModelPoint normal = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < points.size(); ++index)
    {
        const OutdoorModelPoint &from = points[index];
        const OutdoorModelPoint &to = points[(index + 1) % points.size()];
        normal[0] += (from[1] - to[1]) * (from[2] + to[2]);
        normal[1] += (from[2] - to[2]) * (from[0] + to[0]);
        normal[2] += (from[0] - to[0]) * (from[1] + to[1]);
    }

    length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

    if (length > 1.0e-9)
    {
        normal = {normal[0] / length, normal[1] / length, normal[2] / length};
    }

    return normal;
}

int16_t texel(double value)
{
    return static_cast<int16_t>(std::clamp(std::lround(value), -32768l, 32767l));
}

// game/outdoor/OutdoorMovementController.cpp: WalkableNormalZ and MaxSmallSlopeHeight.
constexpr double WalkableNormalZ = 0.70767211914;
constexpr double MaxSmallSlopeHeight = 128.0;
}

uint32_t outdoorLiquidBits(const std::string &liquid, const std::string &flow, const std::string &world)
{
    uint32_t bits = 0;

    if (liquid == "water")
    {
        bits |= Game::faceAttributeBit(Game::FaceAttribute::Fluid);
    }
    else if (liquid == "lava")
    {
        bits |= world == "mm6" ? Game::faceAttributeBit(Game::FaceAttribute::Fluid)
            : Game::faceAttributeBit(Game::FaceAttribute::Lava);
    }
    else if (!liquid.empty())
    {
        return UINT32_MAX;
    }

    if (flow == "down")
    {
        bits |= Game::faceAttributeBit(Game::FaceAttribute::FlowDown);
    }
    else if (flow == "up")
    {
        bits |= Game::faceAttributeBit(Game::FaceAttribute::FlowUp);
    }
    else if (flow == "left")
    {
        bits |= Game::faceAttributeBit(Game::FaceAttribute::FlowLeft);
    }
    else if (flow == "right")
    {
        bits |= Game::faceAttributeBit(Game::FaceAttribute::FlowRight);
    }
    else if (!flow.empty())
    {
        return UINT32_MAX;
    }

    return bits;
}

bool outdoorSlopeWalkable(double rise, double run)
{
    if (rise < MaxSmallSlopeHeight)
    {
        return true;
    }

    // As the game reads it: the normal as stored, in steps of 1/65536.
    const double normalZ = std::lround(run / oy::hypot(run, rise) * 65536.0) / 65536.0;
    return normalZ >= WalkableNormalZ;
}

OutdoorModelBuilder::OutdoorModelBuilder(Game::OutdoorBModel &model)
    : m_model(model)
{
}

int OutdoorModelBuilder::addFace(
    const std::vector<OutdoorModelPoint> &points,
    const std::string &texture,
    const std::vector<std::array<double, 2>> &texels,
    uint16_t event)
{
    // The plane is that of the whole units the corners are stored at.
    std::vector<OutdoorModelPoint> stored;

    for (const OutdoorModelPoint &point : points)
    {
        stored.push_back({std::round(point[0]), std::round(point[1]), std::round(point[2])});
    }

    double length = 0.0;
    const OutdoorModelPoint normal = normalOf(stored, length);

    if (points.size() < 3 || texels.size() != points.size() || length <= 1.0e-6)
    {
        return -1;
    }

    Game::OutdoorBModelFace face;
    const bool wall = std::fabs(normal[2]) < 1.0e-4;
    const bool level = std::fabs(normal[0]) < 1.0e-4 && std::fabs(normal[1]) < 1.0e-4;
    face.polygonType = static_cast<uint8_t>(wall ? 1 : (normal[2] > 0.0 ? (level ? 3 : 4) : (level ? 5 : 6)));
    face.planeNormalX = static_cast<int32_t>(std::lround(normal[0] * 65536.0));
    face.planeNormalY = static_cast<int32_t>(std::lround(normal[1] * 65536.0));
    face.planeNormalZ = static_cast<int32_t>(std::lround(normal[2] * 65536.0));
    face.planeDistance = static_cast<int32_t>(std::lround(-(normal[0] * stored[0][0] + normal[1] * stored[0][1]
        + normal[2] * stored[0][2]) * 65536.0));
    const double absX = std::fabs(normal[0]);
    const double absY = std::fabs(normal[1]);
    const double absZ = std::fabs(normal[2]);
    face.attributes = Game::faceAttributeBit(absZ >= absX && absZ >= absY ? Game::FaceAttribute::XYPlane
        : (absX >= absY ? Game::FaceAttribute::YZPlane : Game::FaceAttribute::XZPlane));

    if (event != 0)
    {
        face.attributes |= Game::faceAttributeBit(Game::FaceAttribute::Clickable);
        face.cogTriggeredNumber = event;
    }

    for (size_t index = 0; index < points.size(); ++index)
    {
        face.vertexIndices.push_back(vertexOf(points[index]));
        face.textureUs.push_back(texel(texels[index][0]));
        face.textureVs.push_back(texel(texels[index][1]));
    }

    face.textureName = texture;
    m_model.faces.push_back(face);
    return static_cast<int>(m_model.faces.size()) - 1;
}

int OutdoorModelBuilder::addSurface(
    const std::vector<OutdoorModelPoint> &points,
    const std::string &texture,
    uint16_t event)
{
    double length = 0.0;
    const OutdoorModelPoint normal = normalOf(points, length);

    if (points.size() < 3 || length <= 1.0e-6)
    {
        return -1;
    }

    // Across: level in the face. Down: the way the face falls (south on a level face).
    const double level = oy::hypot(normal[0], normal[1]);
    OutdoorModelPoint across = {1.0, 0.0, 0.0};
    OutdoorModelPoint down = {0.0, -1.0, 0.0};

    if (level > 1.0e-6)
    {
        // Seen from outside, to the viewer's right; on a roof slope this keeps the texture upright along it.
        across = {-normal[1] / level, normal[0] / level, 0.0};
        down = {across[1] * normal[2] - across[2] * normal[1], across[2] * normal[0] - across[0] * normal[2],
            across[0] * normal[1] - across[1] * normal[0]};

        // In the face and square to `across`: the way that falls.
        if (down[2] > 0.0)
        {
            down = {-down[0], -down[1], -down[2]};
        }
    }

    // From the corner that is highest up the face and furthest left, so the numbers stay small.
    double leastU = 1.0e18;
    double leastV = 1.0e18;
    std::vector<std::array<double, 2>> texels;

    for (const OutdoorModelPoint &point : points)
    {
        const double u = point[0] * across[0] + point[1] * across[1] + point[2] * across[2];
        const double v = point[0] * down[0] + point[1] * down[1] + point[2] * down[2];
        leastU = std::min(leastU, u);
        leastV = std::min(leastV, v);
        texels.push_back({u, v});
    }

    for (std::array<double, 2> &texelPair : texels)
    {
        texelPair = {texelPair[0] - leastU, texelPair[1] - leastV};
    }

    return addFace(points, texture, texels, event);
}

void OutdoorModelBuilder::addBox(
    const OutdoorModelPoint &low,
    const OutdoorModelPoint &high,
    const std::string &sideTexture,
    const std::string &topTexture,
    uint16_t event)
{
    const double x0 = low[0];
    const double y0 = low[1];
    const double x1 = high[0];
    const double y1 = high[1];
    addSurface({{x0, y0, low[2]}, {x1, y0, low[2]}, {x1, y0, high[2]}, {x0, y0, high[2]}}, sideTexture, event);
    addSurface({{x1, y0, low[2]}, {x1, y1, low[2]}, {x1, y1, high[2]}, {x1, y0, high[2]}}, sideTexture, event);
    addSurface({{x1, y1, low[2]}, {x0, y1, low[2]}, {x0, y1, high[2]}, {x1, y1, high[2]}}, sideTexture, event);
    addSurface({{x0, y1, low[2]}, {x0, y0, low[2]}, {x0, y0, high[2]}, {x0, y1, high[2]}}, sideTexture, event);
    addSurface({{x0, y0, high[2]}, {x1, y0, high[2]}, {x1, y1, high[2]}, {x0, y1, high[2]}}, topTexture, event);
}

void OutdoorModelBuilder::addPrism(
    const std::vector<std::array<double, 2>> &outline,
    double low,
    double high,
    const std::string &sideTexture,
    const std::string &topTexture,
    const std::string &bottomTexture,
    uint16_t event)
{
    const size_t count = outline.size();
    std::vector<OutdoorModelPoint> top;
    std::vector<OutdoorModelPoint> bottom;

    for (size_t index = 0; index < count; ++index)
    {
        const std::array<double, 2> &from = outline[index];
        const std::array<double, 2> &to = outline[(index + 1) % count];
        addSurface({{from[0], from[1], low}, {to[0], to[1], low}, {to[0], to[1], high}, {from[0], from[1], high}},
            sideTexture, event);
        top.push_back({from[0], from[1], high});
        bottom.push_back({outline[count - 1 - index][0], outline[count - 1 - index][1], low});
    }

    if (!topTexture.empty())
    {
        addSurface(top, topTexture, event);
    }

    if (!bottomTexture.empty())
    {
        addSurface(bottom, bottomTexture, event);
    }
}

int OutdoorModelBuilder::addStepSlope(
    const std::vector<OutdoorModelPoint> &points,
    const std::string &texture,
    uint16_t event)
{
    const int face = addSurface(points, texture, event);

    if (face >= 0)
    {
        m_model.faces[static_cast<size_t>(face)].attributes |= Game::faceAttributeBit(Game::FaceAttribute::Invisible);
    }

    return face;
}

void OutdoorModelBuilder::letThrough(int face)
{
    if (face >= 0 && static_cast<size_t>(face) < m_model.faces.size())
    {
        m_model.faces[static_cast<size_t>(face)].attributes |=
            Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
    }
}

void OutdoorModelBuilder::hideUnder(size_t from, size_t to, size_t coverFrom, size_t coverTo)
{
    const size_t count = m_model.faces.size();

    for (size_t face = from; face < std::min(to, count); ++face)
    {
        const Game::OutdoorBModelFace &under = m_model.faces[face];

        for (size_t cover = coverFrom; cover < std::min(coverTo, count); ++cover)
        {
            const Game::OutdoorBModelFace &over = m_model.faces[cover];

            if (std::abs(under.planeNormalX - over.planeNormalX) <= 4 && std::abs(under.planeNormalY
                    - over.planeNormalY) <= 4 && std::abs(under.planeNormalZ - over.planeNormalZ) <= 4
                && std::abs(static_cast<int64_t>(under.planeDistance) - over.planeDistance) <= 32768)
            {
                hide(static_cast<int>(face));
                break;
            }
        }
    }
}

size_t OutdoorModelBuilder::faceCount() const
{
    return m_model.faces.size();
}

void OutdoorModelBuilder::hide(int face)
{
    if (face >= 0 && static_cast<size_t>(face) < m_model.faces.size())
    {
        m_model.faces[static_cast<size_t>(face)].attributes |= Game::faceAttributeBit(Game::FaceAttribute::Invisible);
    }
}

void OutdoorModelBuilder::finish()
{
    if (m_model.vertices.empty())
    {
        return;
    }

    Game::OutdoorBModelVertex low = m_model.vertices[0];
    Game::OutdoorBModelVertex high = m_model.vertices[0];

    for (const Game::OutdoorBModelVertex &vertex : m_model.vertices)
    {
        low = {std::min(low.x, vertex.x), std::min(low.y, vertex.y), std::min(low.z, vertex.z)};
        high = {std::max(high.x, vertex.x), std::max(high.y, vertex.y), std::max(high.z, vertex.z)};
    }

    const double centerX = (low.x + high.x) * 0.5;
    const double centerY = (low.y + high.y) * 0.5;
    const double centerZ = (low.z + high.z) * 0.5;
    double radius = 0.0;

    for (const Game::OutdoorBModelVertex &vertex : m_model.vertices)
    {
        radius = std::max(radius, std::sqrt((vertex.x - centerX) * (vertex.x - centerX)
            + (vertex.y - centerY) * (vertex.y - centerY) + (vertex.z - centerZ) * (vertex.z - centerZ)));
    }

    m_model.positionX = static_cast<int>(std::lround(centerX));
    m_model.positionY = static_cast<int>(std::lround(centerY));
    m_model.positionZ = static_cast<int>(std::lround(centerZ));
    m_model.minX = low.x;
    m_model.minY = low.y;
    m_model.minZ = low.z;
    m_model.maxX = high.x;
    m_model.maxY = high.y;
    m_model.maxZ = high.z;
    m_model.boundingCenterX = m_model.positionX;
    m_model.boundingCenterY = m_model.positionY;
    m_model.boundingCenterZ = m_model.positionZ;
    m_model.boundingRadius = static_cast<int>(std::ceil(radius));
}

uint16_t OutdoorModelBuilder::vertexOf(const OutdoorModelPoint &point)
{
    const std::array<int, 3> key = {static_cast<int>(std::lround(point[0])),
        static_cast<int>(std::lround(point[1])), static_cast<int>(std::lround(point[2]))};
    const std::map<std::array<int, 3>, uint16_t>::const_iterator found = m_indices.find(key);

    if (found != m_indices.end())
    {
        return found->second;
    }

    m_model.vertices.push_back({key[0], key[1], key[2]});
    m_indices[key] = static_cast<uint16_t>(m_model.vertices.size() - 1);
    return m_indices[key];
}
}
