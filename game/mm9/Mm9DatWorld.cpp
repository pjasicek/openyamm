#include "game/mm9/Mm9DatWorld.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t Mm9DatVersion = 66;

class Mm9DatParseError : public std::runtime_error
{
public:
    explicit Mm9DatParseError(const std::string &message)
        : std::runtime_error(message)
    {
    }
};

class BinaryReader
{
public:
    explicit BinaryReader(const std::vector<uint8_t> &bytes)
        : m_bytes(bytes)
    {
    }

    size_t tell() const
    {
        return m_offset;
    }

    void seek(size_t offset)
    {
        if (offset > m_bytes.size())
        {
            throw Mm9DatParseError("seek out of range");
        }

        m_offset = offset;
    }

    void skip(size_t byteCount)
    {
        seek(m_offset + byteCount);
    }

    std::vector<uint8_t> readBytes(size_t byteCount)
    {
        if (m_offset + byteCount > m_bytes.size())
        {
            throw Mm9DatParseError("read out of range");
        }

        std::vector<uint8_t> result(
            m_bytes.begin() + static_cast<std::ptrdiff_t>(m_offset),
            m_bytes.begin() + static_cast<std::ptrdiff_t>(m_offset + byteCount));
        m_offset += byteCount;
        return result;
    }

    uint8_t u8()
    {
        return readScalar<uint8_t>();
    }

    uint16_t u16()
    {
        return readScalar<uint16_t>();
    }

    uint32_t u32()
    {
        return readScalar<uint32_t>();
    }

    float f32()
    {
        return readScalar<float>();
    }

    Mm9DatVec3 vec3()
    {
        Mm9DatVec3 value = {};
        value.x = f32();
        value.y = f32();
        value.z = f32();
        return value;
    }

    std::string string(bool lengthIsShort = true)
    {
        const size_t length = lengthIsShort ? u16() : u32();
        const std::vector<uint8_t> bytes = readBytes(length);
        size_t textLength = 0;

        while (textLength < bytes.size() && bytes[textLength] != 0)
        {
            ++textLength;
        }

        return std::string(reinterpret_cast<const char *>(bytes.data()), textLength);
    }

    std::string nullString()
    {
        const size_t begin = m_offset;

        while (m_offset < m_bytes.size() && m_bytes[m_offset] != 0)
        {
            ++m_offset;
        }

        const size_t end = m_offset;

        if (m_offset < m_bytes.size())
        {
            ++m_offset;
        }

        return std::string(reinterpret_cast<const char *>(m_bytes.data() + begin), end - begin);
    }

private:
    template <typename ValueType>
    ValueType readScalar()
    {
        if (m_offset + sizeof(ValueType) > m_bytes.size())
        {
            throw Mm9DatParseError("scalar read out of range");
        }

        ValueType value = {};
        std::memcpy(&value, m_bytes.data() + m_offset, sizeof(ValueType));
        m_offset += sizeof(ValueType);
        return value;
    }

    const std::vector<uint8_t> &m_bytes;
    size_t m_offset = 0;
};

void readWorldTreeLayout(BinaryReader &reader, uint8_t &currentByte, int &currentBit)
{
    if (currentBit == 8)
    {
        currentByte = reader.u8();
        currentBit = 0;
    }

    const bool subdivide = (currentByte & (1u << currentBit)) != 0;
    ++currentBit;

    if (subdivide)
    {
        for (int child = 0; child < 4; ++child)
        {
            readWorldTreeLayout(reader, currentByte, currentBit);
        }
    }
}

void readWorldTree(BinaryReader &reader)
{
    reader.vec3();
    reader.vec3();
    reader.u32();
    reader.u32();

    uint8_t currentByte = 0;
    int currentBit = 8;
    readWorldTreeLayout(reader, currentByte, currentBit);
}

Mm9DatLeaf readLeaf(BinaryReader &reader)
{
    Mm9DatLeaf leaf = {};
    leaf.count = reader.u16();

    if (leaf.count == 0xffffu)
    {
        leaf.index = reader.u16();
    }
    else
    {
        leaf.portalData.reserve(leaf.count);

        for (uint16_t index = 0; index < leaf.count; ++index)
        {
            Mm9DatLeafPortalData portalData = {};
            portalData.portalId = reader.u16();
            const uint16_t size = reader.u16();
            portalData.contents = reader.readBytes(size);
            leaf.portalData.push_back(std::move(portalData));
        }
    }

    const uint32_t polygonEntryCount = reader.u32();
    leaf.polygonEntries.reserve(polygonEntryCount);

    for (uint32_t index = 0; index < polygonEntryCount; ++index)
    {
        leaf.polygonEntries.push_back(reader.u32());
    }

    leaf.unknown = reader.u32();
    return leaf;
}

Mm9DatSurface readSurface(BinaryReader &reader)
{
    Mm9DatSurface surface = {};
    surface.uvOriginLt = reader.vec3();
    surface.uvULt = reader.vec3();
    surface.uvVLt = reader.vec3();
    surface.textureIndex = reader.u16();
    surface.unknown = reader.u32();
    surface.flags = reader.u32();
    surface.unknown2 = reader.u32();

    const uint8_t useEffects = reader.u8();

    if (useEffects > 0)
    {
        surface.effectName = reader.string();
        surface.effectParam = reader.string();
    }

    surface.textureFlags = reader.u16();
    return surface;
}

Mm9DatPoly readPoly(BinaryReader &reader, uint8_t vertexCount)
{
    Mm9DatPoly poly = {};
    poly.centerLt = reader.vec3();
    poly.lightmapWidth = reader.u16();
    poly.lightmapHeight = reader.u16();
    poly.unknownFlag = reader.u16();
    poly.unknownList.reserve(static_cast<size_t>(poly.unknownFlag) * 2);

    for (size_t index = 0; index < static_cast<size_t>(poly.unknownFlag) * 2; ++index)
    {
        poly.unknownList.push_back(reader.u16());
    }

    poly.surfaceIndex = reader.u16();
    poly.planeIndex = reader.u16();
    poly.vertices.reserve(vertexCount);

    for (uint8_t index = 0; index < vertexCount; ++index)
    {
        Mm9DatPolyVertex vertex = {};
        vertex.pointIndex = reader.u16();
        const std::vector<uint8_t> dummy = reader.readBytes(3);
        std::copy(dummy.begin(), dummy.end(), vertex.rawDummy.begin());
        poly.vertices.push_back(vertex);
    }

    return poly;
}

Mm9DatNode readNode(BinaryReader &reader)
{
    Mm9DatNode node = {};
    node.polyIndex = reader.u32();
    node.leafIndex = reader.u16();
    node.frontIndex = reader.u32();
    node.backIndex = reader.u32();
    return node;
}

Mm9DatUserPortal readUserPortal(BinaryReader &reader)
{
    Mm9DatUserPortal portal = {};
    portal.name = reader.string();
    portal.unknownInt1 = reader.u32();
    portal.unknownShort = reader.u16();
    portal.centerLt = reader.vec3();
    portal.dimsLt = reader.vec3();
    return portal;
}

Mm9DatPBlockTableSummary readPBlockSummary(BinaryReader &reader)
{
    Mm9DatPBlockTableSummary summary = {};
    summary.dimA = reader.u32();
    summary.dimB = reader.u32();
    summary.dimC = reader.u32();
    summary.boundsMinLt = reader.vec3();
    summary.boundsMaxLt = reader.vec3();
    summary.recordCount =
        static_cast<uint64_t>(summary.dimA) * static_cast<uint64_t>(summary.dimB) * static_cast<uint64_t>(summary.dimC);

    if (summary.recordCount > 10000000ull)
    {
        throw Mm9DatParseError("implausible PBlock record count");
    }

    for (uint64_t index = 0; index < summary.recordCount; ++index)
    {
        const uint16_t size = reader.u16();
        reader.u16();
        reader.skip(static_cast<size_t>(size) * 6);
    }

    return summary;
}

Mm9DatWorldModel readWorldModel(BinaryReader &reader)
{
    Mm9DatWorldModel model = {};
    model.worldInfoFlags = reader.u32();
    model.unknownValue = reader.u32();
    model.name = reader.string();

    const uint32_t pointCount = reader.u32();
    const uint32_t planeCount = reader.u32();
    const uint32_t surfaceCount = reader.u32();
    const uint32_t userPortalCount = reader.u32();
    const uint32_t polyCount = reader.u32();
    const uint32_t leafCount = reader.u32();
    model.vertCount = reader.u32();
    model.totalVisListSize = reader.u32();
    model.leafListCount = reader.u32();
    const uint32_t nodeCount = reader.u32();

    model.unknownValue2 = reader.u32();
    model.unknownValue3 = reader.u32();
    model.boundsMinLt = reader.vec3();
    model.boundsMaxLt = reader.vec3();
    model.worldTranslationLt = reader.vec3();

    const uint32_t textureNameLength = reader.u32();
    const uint32_t textureCount = reader.u32();
    (void)textureNameLength;

    model.textures.reserve(textureCount);

    for (uint32_t index = 0; index < textureCount; ++index)
    {
        model.textures.push_back(reader.nullString());
    }

    std::vector<uint8_t> polyVertexCounts;
    polyVertexCounts.reserve(polyCount);

    for (uint32_t index = 0; index < polyCount; ++index)
    {
        const uint8_t first = reader.u8();
        const uint8_t second = reader.u8();
        polyVertexCounts.push_back(static_cast<uint8_t>(first + second));
    }

    model.leaves.reserve(leafCount);

    for (uint32_t index = 0; index < leafCount; ++index)
    {
        model.leaves.push_back(readLeaf(reader));
    }

    model.planes.reserve(planeCount);

    for (uint32_t index = 0; index < planeCount; ++index)
    {
        Mm9DatPlane plane = {};
        plane.normalLt = reader.vec3();
        plane.distance = reader.f32();
        model.planes.push_back(plane);
    }

    model.surfaces.reserve(surfaceCount);

    for (uint32_t index = 0; index < surfaceCount; ++index)
    {
        model.surfaces.push_back(readSurface(reader));
    }

    model.polies.reserve(polyCount);

    for (uint32_t index = 0; index < polyCount; ++index)
    {
        model.polies.push_back(readPoly(reader, polyVertexCounts[index]));
    }

    model.nodes.reserve(nodeCount);

    for (uint32_t index = 0; index < nodeCount; ++index)
    {
        model.nodes.push_back(readNode(reader));
    }

    model.userPortals.reserve(userPortalCount);

    for (uint32_t index = 0; index < userPortalCount; ++index)
    {
        model.userPortals.push_back(readUserPortal(reader));
    }

    model.pointsLt.reserve(pointCount);
    model.pointNormalsLt.reserve(pointCount);

    for (uint32_t index = 0; index < pointCount; ++index)
    {
        model.pointsLt.push_back(reader.vec3());
        model.pointNormalsLt.push_back(reader.vec3());
    }

    model.pblockTable = readPBlockSummary(reader);
    model.rootNodeIndex = reader.u32();
    model.sectionCount = reader.u32();
    return model;
}

Mm9DatVec3 ltToOpenYamm(const Mm9DatVec3 &value, float scale)
{
    return {
        value.x * scale,
        value.z * scale,
        value.y * scale,
    };
}

Mm9DatVec3 openYammToLt(const Mm9DatVec3 &value, float scale)
{
    return {
        value.x / scale,
        value.z / scale,
        value.y / scale,
    };
}

Mm9DatVec3 sub(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.x - right.x,
        left.y - right.y,
        left.z - right.z,
    };
}

Mm9DatVec3 add(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.x + right.x,
        left.y + right.y,
        left.z + right.z,
    };
}

Mm9DatVec3 scale(const Mm9DatVec3 &value, float scalar)
{
    return {
        value.x * scalar,
        value.y * scalar,
        value.z * scalar,
    };
}

Mm9DatVec3 cross(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x,
    };
}

float dot(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

Mm9DatVec3 renderVertexPosition(const Mm9DatRenderVertex &vertex)
{
    return {
        vertex.x,
        vertex.y,
        vertex.z,
    };
}

Mm9DatRenderVertex transformedRenderVertex(
    const Mm9DatRenderVertex &vertex,
    const Mm9DatMechanismPreviewMotion &motion,
    float transformScale)
{
    constexpr float Pi = 3.14159265358979323846f;
    const Mm9DatVec3 openYammPosition = renderVertexPosition(vertex);
    Mm9DatVec3 sourcePositionLt = openYammToLt(openYammPosition, transformScale);

    if (motion.hasLinearMotion && std::fabs(motion.moveDistLt) > 0.0001f)
    {
        sourcePositionLt = add(
            sourcePositionLt,
            scale(motion.moveDirLt, motion.moveDistLt * motion.progress));
    }

    if (motion.hasRotationMotion)
    {
        const Mm9DatVec3 angles = scale(motion.rotationAnglesDeg, motion.progress * Pi / 180.0f);
        Mm9DatVec3 relative = sub(sourcePositionLt, motion.rotationPointLt);

        if (std::fabs(angles.x) > 0.0001f)
        {
            const float angleSin = std::sin(angles.x);
            const float angleCos = std::cos(angles.x);
            relative = {
                relative.x,
                relative.y * angleCos - relative.z * angleSin,
                relative.y * angleSin + relative.z * angleCos,
            };
        }

        if (std::fabs(angles.y) > 0.0001f)
        {
            const float angleSin = std::sin(angles.y);
            const float angleCos = std::cos(angles.y);
            relative = {
                relative.x * angleCos + relative.z * angleSin,
                relative.y,
                -relative.x * angleSin + relative.z * angleCos,
            };
        }

        if (std::fabs(angles.z) > 0.0001f)
        {
            const float angleSin = std::sin(angles.z);
            const float angleCos = std::cos(angles.z);
            relative = {
                relative.x * angleCos - relative.y * angleSin,
                relative.x * angleSin + relative.y * angleCos,
                relative.z,
            };
        }

        sourcePositionLt = add(motion.rotationPointLt, relative);
    }

    const Mm9DatVec3 transformedPosition = ltToOpenYamm(sourcePositionLt, transformScale);
    Mm9DatRenderVertex transformedVertex = vertex;
    transformedVertex.x = transformedPosition.x;
    transformedVertex.y = transformedPosition.y;
    transformedVertex.z = transformedPosition.z;
    return transformedVertex;
}

bool renderBoundsDifferent(const Mm9DatRenderBounds &left, const Mm9DatRenderBounds &right)
{
    if (left.valid != right.valid)
    {
        return true;
    }

    if (!left.valid)
    {
        return false;
    }

    constexpr float Epsilon = 0.001f;
    return std::fabs(left.min.x - right.min.x) > Epsilon
        || std::fabs(left.min.y - right.min.y) > Epsilon
        || std::fabs(left.min.z - right.min.z) > Epsilon
        || std::fabs(left.max.x - right.max.x) > Epsilon
        || std::fabs(left.max.y - right.max.y) > Epsilon
        || std::fabs(left.max.z - right.max.z) > Epsilon;
}

float length(const Mm9DatVec3 &value)
{
    return std::sqrt(dot(value, value));
}

std::optional<Mm9DatVec3> normalized(const Mm9DatVec3 &value)
{
    const float valueLength = length(value);

    if (valueLength <= 0.0001f)
    {
        return std::nullopt;
    }

    return Mm9DatVec3{
        value.x / valueLength,
        value.y / valueLength,
        value.z / valueLength,
    };
}

std::optional<Mm9DatVec3> unitNormal(const std::array<Mm9DatVec3, 3> &vertices)
{
    const Mm9DatVec3 normal = cross(sub(vertices[1], vertices[0]), sub(vertices[2], vertices[0]));
    return normalized(normal);
}

std::optional<Mm9DatVec3> transformedPlaneNormal(const Mm9DatPlane &plane)
{
    Mm9DatVec3 normal = {
        plane.normalLt.x,
        plane.normalLt.z,
        plane.normalLt.y,
    };
    const float normalLength = length(normal);

    if (normalLength <= 0.0001f)
    {
        return std::nullopt;
    }

    normal.x /= normalLength;
    normal.y /= normalLength;
    normal.z /= normalLength;
    return normal;
}

float uvPixelCoordinate(const Mm9DatVec3 &point, const Mm9DatVec3 &origin, const Mm9DatVec3 &axis)
{
    return dot(sub(point, origin), axis);
}

Mm9DatRenderVertex renderVertex(
    const Mm9DatVec3 &sourcePointLt,
    const Mm9DatSurface &surface,
    float scale)
{
    const Mm9DatVec3 position = ltToOpenYamm(sourcePointLt, scale);
    Mm9DatRenderVertex vertex = {};
    vertex.x = position.x;
    vertex.y = position.y;
    vertex.z = position.z;
    vertex.uPixels = uvPixelCoordinate(sourcePointLt, surface.uvOriginLt, surface.uvULt);
    vertex.vPixels = uvPixelCoordinate(sourcePointLt, surface.uvOriginLt, surface.uvVLt);
    return vertex;
}

std::array<Mm9DatVec3, 3> trianglePositions(const Mm9DatRenderTriangle &triangle)
{
    return {{
        {triangle.vertices[0].x, triangle.vertices[0].y, triangle.vertices[0].z},
        {triangle.vertices[1].x, triangle.vertices[1].y, triangle.vertices[1].z},
        {triangle.vertices[2].x, triangle.vertices[2].y, triangle.vertices[2].z},
    }};
}

void reverseTriangleWinding(Mm9DatRenderTriangle &triangle)
{
    std::swap(triangle.vertices[1], triangle.vertices[2]);
}

std::string normalizedMaterialTextureKey(const std::string &value)
{
    std::string normalized;
    normalized.reserve(value.size());

    for (char character : value)
    {
        normalized.push_back(
            character == '\\' ? '/' : static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return normalized;
}

bool startsWith(const std::string &value, const std::string &prefix)
{
    return value.rfind(prefix, 0) == 0;
}

bool endsWith(const std::string &value, const std::string &suffix)
{
    return value.size() >= suffix.size()
        && value.compare(value.size() - suffix.size(), suffix.size(), suffix) == 0;
}

bool isMm9DatWaterVolumeOrMarkerTexture(const std::string &sourceTexture)
{
    const std::string textureKey = normalizedMaterialTextureKey(sourceTexture);
    return endsWith(textureKey, "/invisible.dtx")
        || endsWith(textureKey, "/watermarker.dtx");
}

bool isMm9DatWaterVolumeOrMarkerModel(
    const Mm9DatRenderTriangle &triangle,
    const Mm9DatModelRenderRole &role)
{
    if (!role.water)
    {
        return false;
    }

    const std::string modelKey = normalizedMaterialTextureKey(triangle.sourceModelName);
    return startsWith(modelKey, "bluewater")
        || isMm9DatWaterVolumeOrMarkerTexture(triangle.sourceTexture);
}

bool isMm9DatRailHelperTexture(const std::string &sourceTexture)
{
    const std::string textureKey = normalizedMaterialTextureKey(sourceTexture);
    return textureKey == "rail.dtx" || endsWith(textureKey, "/rail.dtx");
}

bool isMm9DatRailHelperModel(const Mm9DatRenderTriangle &triangle)
{
    const std::string modelKey = normalizedMaterialTextureKey(triangle.sourceModelName);
    return startsWith(modelKey, "aitrk")
        || isMm9DatRailHelperTexture(triangle.sourceTexture);
}

struct RayTriangleIntersection
{
    float distance = 0.0f;
    float barycentricU = 0.0f;
    float barycentricV = 0.0f;
};

std::optional<RayTriangleIntersection> intersectRayTriangle(
    const Mm9DatPickRay &ray,
    const Mm9DatRenderTriangle &triangle,
    bool includeBackfaces)
{
    constexpr float Epsilon = 0.0001f;

    const Mm9DatVec3 vertex0 = renderVertexPosition(triangle.vertices[0]);
    const Mm9DatVec3 vertex1 = renderVertexPosition(triangle.vertices[1]);
    const Mm9DatVec3 vertex2 = renderVertexPosition(triangle.vertices[2]);
    const Mm9DatVec3 edge1 = sub(vertex1, vertex0);
    const Mm9DatVec3 edge2 = sub(vertex2, vertex0);
    const Mm9DatVec3 pvec = cross(ray.direction, edge2);
    const float determinant = dot(edge1, pvec);

    if (includeBackfaces)
    {
        if (std::fabs(determinant) <= Epsilon)
        {
            return std::nullopt;
        }
    }
    else if (determinant <= Epsilon)
    {
        return std::nullopt;
    }

    const float inverseDeterminant = 1.0f / determinant;
    const Mm9DatVec3 tvec = sub(ray.origin, vertex0);
    const float barycentricU = dot(tvec, pvec) * inverseDeterminant;

    if (barycentricU < -Epsilon || barycentricU > 1.0f + Epsilon)
    {
        return std::nullopt;
    }

    const Mm9DatVec3 qvec = cross(tvec, edge1);
    const float barycentricV = dot(ray.direction, qvec) * inverseDeterminant;

    if (barycentricV < -Epsilon || barycentricU + barycentricV > 1.0f + Epsilon)
    {
        return std::nullopt;
    }

    const float distance = dot(edge2, qvec) * inverseDeterminant;

    if (distance <= Epsilon)
    {
        return std::nullopt;
    }

    RayTriangleIntersection intersection = {};
    intersection.distance = distance;
    intersection.barycentricU = barycentricU;
    intersection.barycentricV = barycentricV;
    return intersection;
}
}

std::optional<Mm9DatWorld> parseMm9DatWorld(
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage)
{
    try
    {
        BinaryReader reader(bytes);
        Mm9DatWorld world = {};
        world.version = reader.u32();

        if (world.version != Mm9DatVersion)
        {
            errorMessage = "expected MM9 DAT version 66, got " + std::to_string(world.version);
            return std::nullopt;
        }

        world.objectDataPos = reader.u32();
        world.renderDataPos = reader.u32();
        reader.skip(8 * sizeof(uint32_t));
        world.worldInfo.propertyString = reader.string(false);
        world.worldInfo.lightMapGridSize = reader.f32();
        world.worldInfo.extentsMinLt = reader.vec3();
        world.worldInfo.extentsMaxLt = reader.vec3();
        readWorldTree(reader);
        world.worldModelPos = static_cast<uint32_t>(reader.tell());

        const uint32_t worldModelCount = reader.u32();
        world.worldModels.reserve(worldModelCount);

        for (uint32_t index = 0; index < worldModelCount; ++index)
        {
            const uint32_t nextWorldModelPos = reader.u32();
            reader.skip(32);
            Mm9DatWorldModel model = readWorldModel(reader);
            const bool seekToNextWorldModel = model.sectionCount > 0;
            world.worldModels.push_back(std::move(model));

            if (seekToNextWorldModel)
            {
                reader.seek(nextWorldModelPos);
            }
        }

        errorMessage.clear();
        return world;
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return std::nullopt;
    }
}

std::optional<Mm9DatWorld> loadMm9DatWorld(
    const std::filesystem::path &path,
    std::string &errorMessage)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        errorMessage = "could not read MM9 DAT: " + path.generic_string();
        return std::nullopt;
    }

    std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    return parseMm9DatWorld(bytes, errorMessage);
}

Mm9DatRenderMesh buildMm9DatRenderMesh(const Mm9DatWorld &world, float scale)
{
    Mm9DatRenderMesh mesh = {};

    for (size_t modelIndex = 0; modelIndex < world.worldModels.size(); ++modelIndex)
    {
        const Mm9DatWorldModel &model = world.worldModels[modelIndex];

        for (size_t polyIndex = 0; polyIndex < model.polies.size(); ++polyIndex)
        {
            const Mm9DatPoly &poly = model.polies[polyIndex];
            ++mesh.sourcePolyCount;

            if (poly.vertices.size() < 3
                || poly.surfaceIndex >= model.surfaces.size()
                || poly.planeIndex >= model.planes.size())
            {
                ++mesh.skippedPolyCount;
                continue;
            }

            const Mm9DatSurface &surface = model.surfaces[poly.surfaceIndex];

            if (surface.textureIndex >= model.textures.size())
            {
                ++mesh.skippedPolyCount;
                continue;
            }

            bool invalidPointRef = false;

            for (const Mm9DatPolyVertex &vertex : poly.vertices)
            {
                if (vertex.pointIndex >= model.pointsLt.size())
                {
                    invalidPointRef = true;
                    break;
                }
            }

            if (invalidPointRef)
            {
                ++mesh.skippedPolyCount;
                continue;
            }

            if (poly.vertices.size() > 3)
            {
                ++mesh.triangulatedPolyCount;
            }

            for (size_t fanIndex = 1; fanIndex + 1 < poly.vertices.size(); ++fanIndex)
            {
                std::array<uint16_t, 3> pointIndices = {{
                    poly.vertices[0].pointIndex,
                    poly.vertices[fanIndex].pointIndex,
                    poly.vertices[fanIndex + 1].pointIndex,
                }};

                Mm9DatRenderTriangle triangle = {};
                triangle.sourceModelIndex = modelIndex;
                triangle.sourcePolyIndex = polyIndex;
                triangle.sourceSurfaceIndex = poly.surfaceIndex;
                triangle.sourceTextureIndex = surface.textureIndex;
                triangle.sourceModelName = model.name;
                triangle.sourceTexture = model.textures[surface.textureIndex];
                triangle.surfaceFlags = surface.flags;
                triangle.textureFlags = surface.textureFlags;

                for (size_t vertexIndex = 0; vertexIndex < 3; ++vertexIndex)
                {
                    triangle.vertices[vertexIndex] =
                        renderVertex(model.pointsLt[pointIndices[vertexIndex]], surface, scale);
                }

                reverseTriangleWinding(triangle);

                const std::optional<Mm9DatVec3> sourceNormal = transformedPlaneNormal(model.planes[poly.planeIndex]);
                const std::optional<Mm9DatVec3> emittedNormal = unitNormal(trianglePositions(triangle));

                if (sourceNormal && emittedNormal && dot(*sourceNormal, *emittedNormal) < -0.75f)
                {
                    reverseTriangleWinding(triangle);
                    triangle.sourcePlaneOrientationFlipped = true;
                    ++mesh.sourcePlaneOrientationFlipCount;
                }

                if (!unitNormal(trianglePositions(triangle)))
                {
                    ++mesh.skippedDegenerateTriangleCount;
                    continue;
                }

                mesh.triangles.push_back(std::move(triangle));
            }
        }
    }

    return mesh;
}

std::optional<Mm9DatRenderMeshPickHit> pickMm9DatRenderMesh(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatPickRay &ray,
    bool includeBackfaces)
{
    const std::optional<Mm9DatVec3> normalizedDirection = normalized(ray.direction);

    if (!normalizedDirection)
    {
        return std::nullopt;
    }

    Mm9DatPickRay normalizedRay = {};
    normalizedRay.origin = ray.origin;
    normalizedRay.direction = *normalizedDirection;

    std::optional<Mm9DatRenderMeshPickHit> bestHit;
    float bestDistance = std::numeric_limits<float>::max();

    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        const Mm9DatRenderTriangle &triangle = mesh.triangles[triangleIndex];
        const std::optional<RayTriangleIntersection> intersection =
            intersectRayTriangle(normalizedRay, triangle, includeBackfaces);

        if (!intersection || intersection->distance >= bestDistance)
        {
            continue;
        }

        Mm9DatRenderMeshPickHit hit = {};
        hit.triangleIndex = triangleIndex;
        hit.sourceModelIndex = triangle.sourceModelIndex;
        hit.sourcePolyIndex = triangle.sourcePolyIndex;
        hit.sourceSurfaceIndex = triangle.sourceSurfaceIndex;
        hit.sourceTextureIndex = triangle.sourceTextureIndex;
        hit.sourceModelName = triangle.sourceModelName;
        hit.sourceTexture = triangle.sourceTexture;
        hit.distance = intersection->distance;
        hit.barycentricU = intersection->barycentricU;
        hit.barycentricV = intersection->barycentricV;
        hit.position = add(normalizedRay.origin, scale(normalizedRay.direction, intersection->distance));
        bestHit = std::move(hit);
        bestDistance = intersection->distance;
    }

    return bestHit;
}

std::vector<Mm9DatRenderMaterialAssignment> assignMm9DatRenderMeshMaterials(
    const Mm9DatRenderMesh &mesh,
    const std::vector<Mm9DatMaterialPreview> &materials)
{
    std::unordered_map<std::string, std::vector<size_t>> materialIndexesBySourceTexture;

    for (size_t materialRow = 0; materialRow < materials.size(); ++materialRow)
    {
        const std::string sourceTextureKey = normalizedMaterialTextureKey(materials[materialRow].sourceTexture);

        if (!sourceTextureKey.empty())
        {
            materialIndexesBySourceTexture[sourceTextureKey].push_back(materialRow);
        }
    }

    std::vector<Mm9DatRenderMaterialAssignment> assignments;
    assignments.reserve(mesh.triangles.size());

    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        const Mm9DatRenderTriangle &triangle = mesh.triangles[triangleIndex];
        Mm9DatRenderMaterialAssignment assignment = {};
        assignment.triangleIndex = triangleIndex;
        assignment.sourceModelIndex = triangle.sourceModelIndex;
        assignment.sourcePolyIndex = triangle.sourcePolyIndex;
        assignment.sourceSurfaceIndex = triangle.sourceSurfaceIndex;
        assignment.sourceTextureIndex = triangle.sourceTextureIndex;
        assignment.sourceTexture = triangle.sourceTexture;

        const auto materialIterator =
            materialIndexesBySourceTexture.find(normalizedMaterialTextureKey(triangle.sourceTexture));

        if (materialIterator != materialIndexesBySourceTexture.end())
        {
            assignment.materialCandidateCount = materialIterator->second.size();
            assignment.ambiguous = assignment.materialCandidateCount > 1;

            if (assignment.materialCandidateCount == 1)
            {
                const Mm9DatMaterialPreview &material = materials[materialIterator->second.front()];
                assignment.materialIndex = material.materialIndex;
                assignment.alias = material.alias;
                assignment.resolvedSourcePath = material.resolvedSourcePath;
                assignment.resolvedPreviewPath = material.resolvedPreviewPath;
                assignment.sourceDtxResolved = material.sourceDtxResolved;
                assignment.previewCacheAvailable = material.previewCacheAvailable;
                assignment.placeholderMissingSource = material.placeholderMissingSource;
                assignment.assigned = true;
            }
        }

        assignments.push_back(std::move(assignment));
    }

    return assignments;
}

Mm9DatRenderBounds computeMm9DatRenderBounds(const Mm9DatRenderMesh &mesh)
{
    Mm9DatRenderBounds bounds = {};

    if (mesh.triangles.empty())
    {
        return bounds;
    }

    bounds.min = {
        std::numeric_limits<float>::max(),
        std::numeric_limits<float>::max(),
        std::numeric_limits<float>::max(),
    };
    bounds.max = {
        -std::numeric_limits<float>::max(),
        -std::numeric_limits<float>::max(),
        -std::numeric_limits<float>::max(),
    };

    for (const Mm9DatRenderTriangle &triangle : mesh.triangles)
    {
        for (const Mm9DatRenderVertex &vertex : triangle.vertices)
        {
            bounds.min.x = std::min(bounds.min.x, vertex.x);
            bounds.min.y = std::min(bounds.min.y, vertex.y);
            bounds.min.z = std::min(bounds.min.z, vertex.z);
            bounds.max.x = std::max(bounds.max.x, vertex.x);
            bounds.max.y = std::max(bounds.max.y, vertex.y);
            bounds.max.z = std::max(bounds.max.z, vertex.z);
        }
    }

    bounds.center = scale(add(bounds.min, bounds.max), 0.5f);
    bounds.valid = true;

    for (const Mm9DatRenderTriangle &triangle : mesh.triangles)
    {
        for (const Mm9DatRenderVertex &vertex : triangle.vertices)
        {
            const float distance = length(sub(renderVertexPosition(vertex), bounds.center));
            bounds.radius = std::max(bounds.radius, distance);
        }
    }

    return bounds;
}

Mm9DatRenderBounds computeMm9DatRenderBoundsForSourceModel(
    const Mm9DatRenderMesh &mesh,
    size_t sourceModelIndex)
{
    Mm9DatRenderMesh modelMesh = {};

    for (const Mm9DatRenderTriangle &triangle : mesh.triangles)
    {
        if (triangle.sourceModelIndex == sourceModelIndex)
        {
            modelMesh.triangles.push_back(triangle);
        }
    }

    return computeMm9DatRenderBounds(modelMesh);
}

Mm9DatMechanismPreviewResult buildMm9DatMechanismPreviewMesh(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismPreviewMotion &motion,
    float transformScale)
{
    Mm9DatMechanismPreviewResult result = {};
    result.previewMesh = mesh;
    result.originalTargetBounds =
        computeMm9DatRenderBoundsForSourceModel(mesh, motion.sourceModelIndex);
    result.targetFound = result.originalTargetBounds.valid;

    if (!result.targetFound)
    {
        result.previewTargetBounds = result.originalTargetBounds;
        return result;
    }

    for (Mm9DatRenderTriangle &triangle : result.previewMesh.triangles)
    {
        if (triangle.sourceModelIndex != motion.sourceModelIndex)
        {
            continue;
        }

        for (Mm9DatRenderVertex &vertex : triangle.vertices)
        {
            vertex = transformedRenderVertex(vertex, motion, transformScale);
        }

        ++result.transformedTriangles;
    }

    result.previewTargetBounds =
        computeMm9DatRenderBoundsForSourceModel(result.previewMesh, motion.sourceModelIndex);
    result.boundsChanged =
        renderBoundsDifferent(result.originalTargetBounds, result.previewTargetBounds);
    return result;
}

Mm9DatCameraFrame frameMm9DatRenderMeshCamera(
    const Mm9DatRenderMesh &mesh,
    float verticalFovDegrees,
    float paddingScale)
{
    const Mm9DatRenderBounds bounds = computeMm9DatRenderBounds(mesh);
    return frameMm9DatRenderBoundsCamera(bounds, verticalFovDegrees, paddingScale);
}

Mm9DatCameraFrame frameMm9DatRenderBoundsCamera(
    const Mm9DatRenderBounds &bounds,
    float verticalFovDegrees,
    float paddingScale)
{
    Mm9DatCameraFrame frame = {};
    if (!bounds.valid || bounds.radius <= 0.0001f || verticalFovDegrees <= 1.0f)
    {
        return frame;
    }

    constexpr float Pi = 3.14159265358979323846f;
    const float halfFovRadians = (verticalFovDegrees * 0.5f) * Pi / 180.0f;
    const float tangent = std::tan(halfFovRadians);

    if (tangent <= 0.0001f)
    {
        return frame;
    }

    const float paddedRadius = bounds.radius * std::max(1.0f, paddingScale);
    const float cameraDistance = paddedRadius / tangent;
    frame.target = bounds.center;
    frame.position = {
        bounds.center.x,
        bounds.center.y + cameraDistance * 0.55f,
        bounds.center.z + cameraDistance,
    };
    frame.radius = bounds.radius;
    frame.nearPlane = std::max(1.0f, cameraDistance - paddedRadius * 1.5f);
    frame.farPlane = cameraDistance + paddedRadius * 2.5f;
    frame.valid = std::isfinite(frame.position.x)
        && std::isfinite(frame.position.y)
        && std::isfinite(frame.position.z)
        && std::isfinite(frame.target.x)
        && std::isfinite(frame.target.y)
        && std::isfinite(frame.target.z)
        && std::isfinite(frame.nearPlane)
        && std::isfinite(frame.farPlane)
        && frame.farPlane > frame.nearPlane;
    return frame;
}

Mm9DatRenderFilterResult classifyMm9DatRenderMeshFilters(
    const Mm9DatRenderMesh &mesh,
    const std::vector<Mm9DatModelRenderRole> &modelRoles,
    size_t portalOverlayCount)
{
    std::unordered_map<size_t, Mm9DatModelRenderRole> rolesBySourceModel;

    for (const Mm9DatModelRenderRole &role : modelRoles)
    {
        rolesBySourceModel[role.sourceModelIndex] = role;
    }

    Mm9DatRenderFilterResult result = {};
    result.entries.reserve(mesh.triangles.size());
    result.summary.totalTriangles = mesh.triangles.size();
    result.summary.portalOverlays = portalOverlayCount;

    for (size_t triangleIndex = 0; triangleIndex < mesh.triangles.size(); ++triangleIndex)
    {
        const Mm9DatRenderTriangle &triangle = mesh.triangles[triangleIndex];
        Mm9DatRenderFilterEntry entry = {};
        entry.triangleIndex = triangleIndex;
        entry.sourceModelIndex = triangle.sourceModelIndex;
        entry.sourcePolyIndex = triangle.sourcePolyIndex;
        entry.sourceSurfaceIndex = triangle.sourceSurfaceIndex;

        const auto roleIterator = rolesBySourceModel.find(triangle.sourceModelIndex);
        const bool hasRole = roleIterator != rolesBySourceModel.end();
        const Mm9DatModelRenderRole role = hasRole ? roleIterator->second : Mm9DatModelRenderRole{};
        const bool invisible = (triangle.surfaceFlags & Mm9DatSurfaceFlagInvisible) != 0;
        const bool waterVolumeOrMarker = isMm9DatWaterVolumeOrMarkerModel(triangle, role);
        const bool visibleWater = role.water && !waterVolumeOrMarker;
        const bool railHelper = isMm9DatRailHelperModel(triangle);
        const bool helper =
            invisible || waterVolumeOrMarker || railHelper || role.physicsBsp || role.visBsp || role.triggerOrVolume;
        const bool visual = (role.visible || !helper) && !waterVolumeOrMarker && !railHelper;

        if (visual)
        {
            entry.flags |= Mm9DatRenderFilterVisual;
            ++result.summary.visualTriangles;
        }

        if (invisible)
        {
            entry.flags |= Mm9DatRenderFilterInvisible;
            ++result.summary.invisibleTriangles;
        }

        if (role.sky)
        {
            entry.flags |= Mm9DatRenderFilterSky;
            ++result.summary.skyTriangles;
        }

        if (role.water)
        {
            entry.flags |= Mm9DatRenderFilterWater;
            ++result.summary.waterTriangles;

            if (visibleWater)
            {
                entry.flags |= Mm9DatRenderFilterVisibleWater;
                ++result.summary.visibleWaterTriangles;
            }

            if (waterVolumeOrMarker)
            {
                entry.flags |= Mm9DatRenderFilterWaterVolume;
                ++result.summary.waterVolumeTriangles;
            }
        }

        if (railHelper)
        {
            entry.flags |= Mm9DatRenderFilterRail;
            ++result.summary.railTriangles;
        }

        if (helper)
        {
            entry.flags |= Mm9DatRenderFilterHelper;
            ++result.summary.helperTriangles;
        }

        if (role.physicsBsp)
        {
            entry.flags |= Mm9DatRenderFilterPhysics;
            ++result.summary.physicsTriangles;
        }

        if (role.visBsp)
        {
            entry.flags |= Mm9DatRenderFilterVisibility;
            ++result.summary.visibilityTriangles;
        }

        if (role.triggerOrVolume)
        {
            entry.flags |= Mm9DatRenderFilterTrigger;
            ++result.summary.triggerTriangles;
        }

        if (role.terrain)
        {
            entry.flags |= Mm9DatRenderFilterTerrain;
            ++result.summary.terrainTriangles;
        }

        if (role.movable)
        {
            entry.flags |= Mm9DatRenderFilterMovable;
            ++result.summary.movableTriangles;
        }

        if (entry.flags == 0)
        {
            ++result.summary.unclassifiedTriangles;
        }

        result.entries.push_back(entry);
    }

    return result;
}
}
