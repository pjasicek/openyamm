#include "editor/import/IndoorSourceGeometryCompiler.h"
#include "editor/import/IndoorDerivedGeometry.h"

#include "editor/import/ObjModelImport.h"
#include "game/FaceEnums.h"
#include "game/events/EvtEnums.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <limits>
#include <optional>
#include <unordered_map>

namespace OpenYAMM::Editor
{
namespace
{
constexpr size_t NativeTextureNameLength = 10;

std::string trimCopy(const std::string &value)
{
    const auto begin = std::find_if_not(value.begin(), value.end(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    });
    const auto end = std::find_if_not(value.rbegin(), value.rend(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    }).base();

    if (begin >= end)
    {
        return {};
    }

    return std::string(begin, end);
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

bool startsWithInsensitive(const std::string &value, const std::string &prefix)
{
    if (value.size() < prefix.size())
    {
        return false;
    }

    return toLowerCopy(value.substr(0, prefix.size())) == toLowerCopy(prefix);
}

std::string stripPrefix(const std::string &value, const std::string &prefix)
{
    if (!startsWithInsensitive(value, prefix))
    {
        return value;
    }

    return value.substr(prefix.size());
}

std::string sourceNodeNameFromModelName(const std::string &modelName)
{
    const size_t separator = modelName.find(" :: ");

    if (separator == std::string::npos)
    {
        return trimCopy(modelName);
    }

    return trimCopy(modelName.substr(0, separator));
}

std::string stripIndexedMaterialSuffix(const std::string &materialName)
{
    const std::string trimmed = trimCopy(materialName);
    const size_t bracketOffset = trimmed.rfind(" [");

    if (bracketOffset == std::string::npos || trimmed.back() != ']')
    {
        return trimmed;
    }

    return trimCopy(trimmed.substr(0, bracketOffset));
}

std::string sanitizeId(const std::string &value)
{
    std::string result;
    bool lastWasSeparator = false;

    for (char character : trimCopy(value))
    {
        const unsigned char byte = static_cast<unsigned char>(character);

        if (std::isalnum(byte) != 0)
        {
            result.push_back(static_cast<char>(std::tolower(byte)));
            lastWasSeparator = false;
        }
        else if (!lastWasSeparator)
        {
            result.push_back('_');
            lastWasSeparator = true;
        }
    }

    while (!result.empty() && result.back() == '_')
    {
        result.pop_back();
    }

    while (!result.empty() && result.front() == '_')
    {
        result.erase(result.begin());
    }

    return result.empty() ? "unnamed" : result;
}

int clampToInt16(int value)
{
    return std::clamp(value, -32768, 32767);
}

int scaledCoordinate(float value, float scale)
{
    return clampToInt16(static_cast<int>(std::lround(value * scale)));
}

Game::IndoorVertex convertPosition(const ImportedModelPosition &position, float scale)
{
    Game::IndoorVertex vertex = {};
    vertex.x = scaledCoordinate(position.x, scale);
    vertex.y = scaledCoordinate(position.y, scale);
    vertex.z = scaledCoordinate(position.z, scale);
    return vertex;
}

struct IndoorVertexKey
{
    int x = 0;
    int y = 0;
    int z = 0;

    bool operator==(const IndoorVertexKey &other) const
    {
        return x == other.x && y == other.y && z == other.z;
    }
};

struct IndoorVertexKeyHash
{
    size_t operator()(const IndoorVertexKey &key) const
    {
        uint64_t hash = static_cast<uint32_t>(key.x);
        hash = (hash ^ static_cast<uint32_t>(key.y)) * 1099511628211ull;
        hash = (hash ^ static_cast<uint32_t>(key.z)) * 1099511628211ull;
        return static_cast<size_t>(hash);
    }
};

class IndoorVertexInterner
{
public:
    bool intern(
        const Game::IndoorVertex &vertex,
        Game::IndoorMapData &indoorGeometry,
        uint16_t &vertexId,
        std::string &errorMessage)
    {
        const IndoorVertexKey key = {vertex.x, vertex.y, vertex.z};
        const std::unordered_map<IndoorVertexKey, uint16_t, IndoorVertexKeyHash>::const_iterator iterator =
            m_vertexIds.find(key);

        if (iterator != m_vertexIds.end())
        {
            vertexId = iterator->second;
            return true;
        }

        if (indoorGeometry.vertices.size() >= MaxIndoorBlvVertexCount)
        {
            errorMessage = "indoor source compiler exceeded 65536 unique vertices";
            return false;
        }

        vertexId = static_cast<uint16_t>(indoorGeometry.vertices.size());
        indoorGeometry.vertices.push_back(vertex);
        m_vertexIds.emplace(key, vertexId);
        return true;
    }

private:
    static constexpr size_t MaxIndoorBlvVertexCount = 0x10000u;
    std::unordered_map<IndoorVertexKey, uint16_t, IndoorVertexKeyHash> m_vertexIds;
};

std::string roomIdFromSourceNode(const std::string &sourceNodeName)
{
    return "room_" + sanitizeId(stripPrefix(sourceNodeName, "ROOM_"));
}

std::string portalIdFromSourceNode(const std::string &sourceNodeName)
{
    return "portal_" + sanitizeId(stripPrefix(sourceNodeName, "PORTAL_"));
}

std::string mechanismIdFromSourceNode(const std::string &sourceNodeName)
{
    return sanitizeId(stripPrefix(sourceNodeName, "MECH_"));
}

std::string surfaceIdFromSourceNode(const std::string &sourceNodeName)
{
    return sanitizeId(stripPrefix(sourceNodeName, "TRIGGER_"));
}

std::string entityIdFromSourceNode(const std::string &sourceNodeName)
{
    return sanitizeId(stripPrefix(sourceNodeName, "DECOR_"));
}

std::string lightIdFromSourceNode(const std::string &sourceNodeName)
{
    return sanitizeId(stripPrefix(sourceNodeName, "LIGHT_"));
}

std::string spawnIdFromSourceNode(const std::string &sourceNodeName)
{
    return sanitizeId(stripPrefix(sourceNodeName, "SPAWN_"));
}

void inferPortalRoomsFromSourceNode(
    const std::string &sourceNodeName,
    std::string &frontRoom,
    std::string &backRoom)
{
    const std::string suffix = stripPrefix(sourceNodeName, "PORTAL_");
    const size_t separator = suffix.find('_');

    if (separator == std::string::npos)
    {
        return;
    }

    frontRoom = "room_" + sanitizeId(suffix.substr(0, separator));
    backRoom = "room_" + sanitizeId(suffix.substr(separator + 1));
}

struct SourceMaterial
{
    std::string texture;
    uint32_t width = 256;
    uint32_t height = 256;
};

using MaterialTextureLookup = std::unordered_map<std::string, SourceMaterial>;

MaterialTextureLookup buildMaterialTextureLookup(
    const EditorIndoorGeometryMetadata &metadata)
{
    MaterialTextureLookup lookup;

    for (const EditorIndoorGeometryMaterialMetadata &material : metadata.materials)
    {
        const std::string sourceMaterial = stripIndexedMaterialSuffix(material.sourceMaterial);
        const std::string texture = trimCopy(material.texture);

        if (!sourceMaterial.empty() && !texture.empty())
        {
            lookup[toLowerCopy(sourceMaterial)] = {texture, material.textureWidth, material.textureHeight};
        }

        if (!material.id.empty() && !texture.empty())
        {
            lookup[toLowerCopy(material.id)] = {texture, material.textureWidth, material.textureHeight};
        }
    }

    return lookup;
}

SourceMaterial resolveFaceMaterial(
    const MaterialTextureLookup &materialTextureLookup,
    const std::string &materialName)
{
    const std::string sourceMaterial = stripIndexedMaterialSuffix(materialName);

    if (sourceMaterial.empty())
    {
        return {"untextured"};
    }

    const auto iterator = materialTextureLookup.find(toLowerCopy(sourceMaterial));

    if (iterator != materialTextureLookup.end() && !iterator->second.texture.empty())
    {
        return iterator->second;
    }

    return {sourceMaterial};
}

float faceNormalZ(const Game::IndoorMapData &indoorGeometry, const Game::IndoorFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return 0.0f;
    }

    const Game::IndoorVertex &a = indoorGeometry.vertices[face.vertexIndices[0]];
    const Game::IndoorVertex &b = indoorGeometry.vertices[face.vertexIndices[1]];
    const Game::IndoorVertex &c = indoorGeometry.vertices[face.vertexIndices[2]];
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float abZ = static_cast<float>(b.z - a.z);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    const float acZ = static_cast<float>(c.z - a.z);
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    const float normalLength = std::sqrt(normalX * normalX + normalY * normalY + normalZ * normalZ);

    if (normalLength <= 0.0001f)
    {
        return 0.0f;
    }

    return normalZ / normalLength;
}

uint8_t classifyFacetType(const Game::IndoorMapData &indoorGeometry, const Game::IndoorFace &face)
{
    const float normalZ = faceNormalZ(indoorGeometry, face);
    const float absNormalZ = std::fabs(normalZ);

    if (absNormalZ >= 0.85f)
    {
        return normalZ >= 0.0f ? 3 : 5;
    }

    if (absNormalZ >= 0.45f)
    {
        return normalZ >= 0.0f ? 4 : 6;
    }

    return 1;
}

void appendFaceToSector(Game::IndoorSector &sector, uint16_t faceIndex, uint8_t facetType)
{
    sector.faceIds.push_back(faceIndex);
    sector.nonBspFaceIds.push_back(faceIndex);

    if (facetType == 3 || facetType == 4)
    {
        sector.floorFaceIds.push_back(faceIndex);
    }
    else if (facetType == 5 || facetType == 6)
    {
        sector.ceilingFaceIds.push_back(faceIndex);
    }
    else
    {
        sector.wallFaceIds.push_back(faceIndex);
    }
}

void refreshSectorCounts(Game::IndoorSector &sector)
{
    sector.floorCount = static_cast<uint16_t>(sector.floorFaceIds.size());
    sector.wallCount = static_cast<uint16_t>(sector.wallFaceIds.size());
    sector.ceilingCount = static_cast<uint16_t>(sector.ceilingFaceIds.size());
    sector.portalCount = static_cast<int16_t>(sector.portalFaceIds.size());
    sector.faceCount = static_cast<uint16_t>(sector.faceIds.size());
    sector.nonBspFaceCount = static_cast<uint16_t>(sector.nonBspFaceIds.size());
    sector.cylinderFaceCount = static_cast<uint16_t>(sector.cylinderFaceIds.size());
    sector.decorationCount = static_cast<uint16_t>(sector.decorationIds.size());
    sector.lightCount = static_cast<uint16_t>(sector.lightIds.size());
}

uint16_t stateFromMechanismMetadata(const EditorIndoorGeometryMechanismMetadata &mechanism)
{
    const std::string state = toLowerCopy(trimCopy(mechanism.initialState));

    if (state == "open")
    {
        return static_cast<uint16_t>(Game::EvtMechanismState::Open);
    }

    if (state == "opening")
    {
        return static_cast<uint16_t>(Game::EvtMechanismState::Opening);
    }

    if (state == "closing")
    {
        return static_cast<uint16_t>(Game::EvtMechanismState::Closing);
    }

    return static_cast<uint16_t>(Game::EvtMechanismState::Closed);
}

uint32_t positiveLengthFromMechanismMetadata(const EditorIndoorGeometryMechanismMetadata &mechanism)
{
    if (mechanism.moveLength.has_value())
    {
        return *mechanism.moveLength;
    }

    if (mechanism.moveDistance.has_value() && *mechanism.moveDistance > 0.0f)
    {
        return static_cast<uint32_t>(std::lround(*mechanism.moveDistance));
    }

    return 0;
}

uint32_t positiveSpeedOrDefault(std::optional<float> value, uint32_t defaultValue)
{
    if (!value.has_value() || *value <= 0.0f)
    {
        return defaultValue;
    }

    return static_cast<uint32_t>(std::lround(*value));
}

std::array<float, 3> moveAxisOrDefault(const EditorIndoorGeometryMechanismMetadata &mechanism)
{
    if (mechanism.moveAxis.has_value())
    {
        return *mechanism.moveAxis;
    }

    return {0.0f, 0.0f, -1.0f};
}

int fixedDirectionComponent(float value)
{
    return static_cast<int>(std::lround(value * 65536.0f));
}

Game::IndoorVertex markerPosition(const ImportedModel &model, float scale)
{
    if (model.positions.empty())
    {
        return {};
    }

    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;

    for (const ImportedModelPosition &position : model.positions)
    {
        x += position.x;
        y += position.y;
        z += position.z;
    }

    const float inverseCount = 1.0f / static_cast<float>(model.positions.size());
    ImportedModelPosition center = {};
    center.x = x * inverseCount;
    center.y = y * inverseCount;
    center.z = z * inverseCount;
    return convertPosition(center, scale);
}

void expandSectorBounds(Game::IndoorSector &sector, const Game::IndoorVertex &vertex, bool &initialized)
{
    if (!initialized)
    {
        sector.minX = static_cast<int16_t>(vertex.x);
        sector.maxX = static_cast<int16_t>(vertex.x);
        sector.minY = static_cast<int16_t>(vertex.y);
        sector.maxY = static_cast<int16_t>(vertex.y);
        sector.minZ = static_cast<int16_t>(vertex.z);
        sector.maxZ = static_cast<int16_t>(vertex.z);
        initialized = true;
        return;
    }

    sector.minX = static_cast<int16_t>(std::min<int>(sector.minX, vertex.x));
    sector.maxX = static_cast<int16_t>(std::max<int>(sector.maxX, vertex.x));
    sector.minY = static_cast<int16_t>(std::min<int>(sector.minY, vertex.y));
    sector.maxY = static_cast<int16_t>(std::max<int>(sector.maxY, vertex.y));
    sector.minZ = static_cast<int16_t>(std::min<int>(sector.minZ, vertex.z));
    sector.maxZ = static_cast<int16_t>(std::max<int>(sector.maxZ, vertex.z));
}

bool appendModelVertices(
    const ImportedModel &model,
    float scale,
    Game::IndoorMapData &indoorGeometry,
    Game::IndoorSector *pSector,
    bool *pBoundsInitialized,
    IndoorVertexInterner &vertexInterner,
    std::vector<uint16_t> &positionVertexIds,
    std::string &errorMessage)
{
    positionVertexIds.clear();
    positionVertexIds.reserve(model.positions.size());

    for (const ImportedModelPosition &position : model.positions)
    {
        Game::IndoorVertex vertex = convertPosition(position, scale);
        uint16_t vertexId = 0;

        if (!vertexInterner.intern(vertex, indoorGeometry, vertexId, errorMessage))
        {
            return false;
        }

        positionVertexIds.push_back(vertexId);

        if (pSector != nullptr && pBoundsInitialized != nullptr)
        {
            expandSectorBounds(*pSector, vertex, *pBoundsInitialized);
        }
    }

    return true;
}

bool appendImportedFaces(
    const ImportedModel &model,
    const MaterialTextureLookup &materialTextureLookup,
    const std::vector<uint16_t> &positionVertexIds,
    uint16_t roomNumber,
    uint16_t roomBehindNumber,
    uint32_t attributes,
    bool isPortal,
    Game::IndoorMapData &indoorGeometry,
    std::vector<uint16_t> &appendedFaceIds,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage)
{
    if (indoorGeometry.faces.size() + model.faces.size() > 0xffffu)
    {
        errorMessage = "indoor source compiler exceeded 65535 faces";
        return false;
    }

    for (const ImportedModelFace &importedFace : model.faces)
    {
        if (importedFace.vertices.size() < 3)
        {
            result.warnings.push_back("Skipping degenerate indoor source face in " + model.name);
            continue;
        }

        Game::IndoorFace face = {};
        face.attributes = attributes;
        face.isPortal = isPortal;
        face.roomNumber = roomNumber;
        face.roomBehindNumber = roomBehindNumber;
        const SourceMaterial material = resolveFaceMaterial(materialTextureLookup, importedFace.materialName);

        // BLV face texture names are a fixed 10-byte field; a longer name would be cut and could collide.
        if (material.texture.size() > NativeTextureNameLength)
        {
            errorMessage = "indoor source texture name \"" + material.texture + "\" in " + model.name
                + " exceeds the native " + std::to_string(NativeTextureNameLength) + "-character limit";
            return false;
        }

        face.textureName = material.texture;
        face.vertexIndices.reserve(importedFace.vertices.size());
        face.textureUs.reserve(importedFace.vertices.size());
        face.textureVs.reserve(importedFace.vertices.size());

        for (const ImportedModelFaceVertex &importedVertex : importedFace.vertices)
        {
            if (importedVertex.positionIndex >= model.positions.size())
            {
                errorMessage = "indoor source compiler found a face vertex outside the source vertex range";
                return false;
            }

            if (importedVertex.positionIndex >= positionVertexIds.size())
            {
                errorMessage = "indoor source compiler found a face vertex outside the remapped vertex range";
                return false;
            }

            face.vertexIndices.push_back(positionVertexIds[importedVertex.positionIndex]);

            if (importedVertex.hasUv)
            {
                const double u = std::round(double(importedVertex.u) * material.width);
                const double v = std::round((1.0 - double(importedVertex.v)) * material.height);
                if (!std::isfinite(u) || !std::isfinite(v) || u < -32768 || u > 32767 || v < -32768 || v > 32767)
                {
                    errorMessage = "indoor source UV exceeds native int16 range in " + model.name;
                    return false;
                }
                face.textureUs.push_back(static_cast<int16_t>(u));
                face.textureVs.push_back(static_cast<int16_t>(v));
            }
            else
            {
                face.textureUs.push_back(0);
                face.textureVs.push_back(0);
            }
        }

        face.facetType = classifyFacetType(indoorGeometry, face);
        const uint16_t faceIndex = static_cast<uint16_t>(indoorGeometry.faces.size());
        appendedFaceIds.push_back(faceIndex);
        indoorGeometry.faces.push_back(std::move(face));
    }

    return true;
}

bool compileRoomModel(
    const ImportedModel &model,
    const MaterialTextureLookup &materialTextureLookup,
    uint16_t sectorIndex,
    float scale,
    IndoorVertexInterner &vertexInterner,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage)
{
    Game::IndoorSector sector = {};
    sector.firstBspNode = -1;
    bool boundsInitialized = false;
    std::vector<uint16_t> positionVertexIds;

    if (!appendModelVertices(
            model,
            scale,
            indoorGeometry,
            &sector,
            &boundsInitialized,
            vertexInterner,
            positionVertexIds,
            errorMessage))
    {
        return false;
    }

    std::vector<uint16_t> appendedFaceIds;

    if (!appendImportedFaces(
            model,
            materialTextureLookup,
            positionVertexIds,
            sectorIndex,
            sectorIndex,
            0,
            false,
            indoorGeometry,
            appendedFaceIds,
            result,
            errorMessage))
    {
        return false;
    }

    for (uint16_t faceIndex : appendedFaceIds)
    {
        appendFaceToSector(sector, faceIndex, indoorGeometry.faces[faceIndex].facetType);
    }

    refreshSectorCounts(sector);
    indoorGeometry.sectors.push_back(std::move(sector));
    return true;
}

std::unordered_map<std::string, const EditorIndoorGeometryPortalMetadata *> buildPortalLookup(
    const EditorIndoorGeometryMetadata &metadata)
{
    std::unordered_map<std::string, const EditorIndoorGeometryPortalMetadata *> lookup;

    for (const EditorIndoorGeometryPortalMetadata &portal : metadata.portals)
    {
        if (!portal.sourceNodeName.empty())
        {
            lookup[toLowerCopy(portal.sourceNodeName)] = &portal;
        }

        if (!portal.id.empty())
        {
            lookup[toLowerCopy(portal.id)] = &portal;
        }
    }

    return lookup;
}

const EditorIndoorGeometryPortalMetadata *findPortalMetadata(
    const std::unordered_map<std::string, const EditorIndoorGeometryPortalMetadata *> &portalLookup,
    const std::string &sourceNodeName)
{
    const auto sourceIterator = portalLookup.find(toLowerCopy(sourceNodeName));

    if (sourceIterator != portalLookup.end())
    {
        return sourceIterator->second;
    }

    const auto idIterator = portalLookup.find(toLowerCopy(portalIdFromSourceNode(sourceNodeName)));

    if (idIterator != portalLookup.end())
    {
        return idIterator->second;
    }

    return nullptr;
}

// BLV sector flag: the sector has portals in its floor (read as floor faces by findIndoorSectorForPoint).
constexpr int32_t IndoorSectorHasFloorPortals = 0x8;

bool compilePortalModel(
    const ImportedModel &model,
    const EditorIndoorGeometryPortalMetadata *pPortalMetadata,
    const std::unordered_map<std::string, uint16_t> &roomSectorById,
    const MaterialTextureLookup &materialTextureLookup,
    float scale,
    IndoorVertexInterner &vertexInterner,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage)
{
    const std::string sourceNodeName = sourceNodeNameFromModelName(model.name);
    std::string frontRoom = pPortalMetadata != nullptr ? pPortalMetadata->frontRoom : std::string();
    std::string backRoom = pPortalMetadata != nullptr ? pPortalMetadata->backRoom : std::string();

    if (frontRoom.empty() || backRoom.empty())
    {
        inferPortalRoomsFromSourceNode(sourceNodeName, frontRoom, backRoom);
    }

    const auto frontIterator = roomSectorById.find(frontRoom);
    const auto backIterator = roomSectorById.find(backRoom);

    if (frontIterator == roomSectorById.end() || backIterator == roomSectorById.end())
    {
        errorMessage = "indoor source portal " + sourceNodeName + " references missing rooms";
        return false;
    }

    std::vector<uint16_t> positionVertexIds;

    if (!appendModelVertices(
            model,
            scale,
            indoorGeometry,
            nullptr,
            nullptr,
            vertexInterner,
            positionVertexIds,
            errorMessage))
    {
        return false;
    }

    std::vector<uint16_t> appendedFaceIds;
    const uint32_t portalAttributes = static_cast<uint32_t>(Game::FaceAttribute::IsPortal);

    if (!appendImportedFaces(
            model,
            materialTextureLookup,
            positionVertexIds,
            frontIterator->second,
            backIterator->second,
            portalAttributes,
            true,
            indoorGeometry,
            appendedFaceIds,
            result,
            errorMessage))
    {
        return false;
    }

    if (appendedFaceIds.empty())
    {
        result.warnings.push_back("Portal source mesh has no valid faces: " + sourceNodeName);
    }

    for (uint16_t faceIndex : appendedFaceIds)
    {
        indoorGeometry.sectors[frontIterator->second].portalFaceIds.push_back(faceIndex);
        indoorGeometry.sectors[backIterator->second].portalFaceIds.push_back(faceIndex);

        // A floor portal (a pit's mouth, a ladder shaft's top): the room above has no floor face over the hole, so the
        // native flag makes the portal stand for one when a point there looks for its sector. Without it a body whose
        // eye rises through the hole has no sector, and the move is refused. The front room is on the normal's side.
        if (indoorGeometry.faces[faceIndex].facetType == 3)
        {
            indoorGeometry.sectors[frontIterator->second].flags |= IndoorSectorHasFloorPortals;
        }
    }

    refreshSectorCounts(indoorGeometry.sectors[frontIterator->second]);
    refreshSectorCounts(indoorGeometry.sectors[backIterator->second]);
    return true;
}

std::unordered_map<std::string, const EditorIndoorGeometryMechanismMetadata *> buildMechanismLookup(
    const EditorIndoorGeometryMetadata &metadata)
{
    std::unordered_map<std::string, const EditorIndoorGeometryMechanismMetadata *> lookup;

    for (const EditorIndoorGeometryMechanismMetadata &mechanism : metadata.mechanisms)
    {
        if (!mechanism.id.empty())
        {
            lookup[toLowerCopy(mechanism.id)] = &mechanism;
        }

        for (const std::string &sourceNodeName : mechanism.sourceNodeNames)
        {
            if (!sourceNodeName.empty())
            {
                lookup[toLowerCopy(sourceNodeName)] = &mechanism;
            }
        }
    }

    return lookup;
}

const EditorIndoorGeometryMechanismMetadata *findMechanismMetadata(
    const std::unordered_map<std::string, const EditorIndoorGeometryMechanismMetadata *> &mechanismLookup,
    const std::string &sourceNodeName)
{
    const auto sourceIterator = mechanismLookup.find(toLowerCopy(sourceNodeName));

    if (sourceIterator != mechanismLookup.end())
    {
        return sourceIterator->second;
    }

    const auto idIterator = mechanismLookup.find(toLowerCopy(mechanismIdFromSourceNode(sourceNodeName)));

    if (idIterator != mechanismLookup.end())
    {
        return idIterator->second;
    }

    return nullptr;
}

uint16_t chooseMechanismSector(const Game::IndoorMapData &indoorGeometry, const ImportedModel &model, float scale)
{
    if (indoorGeometry.sectors.empty() || model.positions.empty())
    {
        return 0;
    }

    float centerX = 0.0f;
    float centerY = 0.0f;
    float centerZ = 0.0f;

    for (const ImportedModelPosition &position : model.positions)
    {
        centerX += position.x * scale;
        centerY += position.y * scale;
        centerZ += position.z * scale;
    }

    const float inverseCount = 1.0f / static_cast<float>(model.positions.size());
    centerX *= inverseCount;
    centerY *= inverseCount;
    centerZ *= inverseCount;

    for (size_t sectorIndex = 0; sectorIndex < indoorGeometry.sectors.size(); ++sectorIndex)
    {
        const Game::IndoorSector &sector = indoorGeometry.sectors[sectorIndex];

        if (!sector.faceIds.empty() && centerX >= sector.minX && centerX <= sector.maxX
            && centerY >= sector.minY && centerY <= sector.maxY
            && centerZ >= sector.minZ && centerZ <= sector.maxZ)
        {
            return static_cast<uint16_t>(sectorIndex);
        }
    }

    return 0;
}

uint16_t chooseMarkerSector(const Game::IndoorMapData &indoorGeometry, const Game::IndoorVertex &position)
{
    if (indoorGeometry.sectors.empty())
    {
        return 0;
    }

    for (size_t sectorIndex = 0; sectorIndex < indoorGeometry.sectors.size(); ++sectorIndex)
    {
        const Game::IndoorSector &sector = indoorGeometry.sectors[sectorIndex];

        if (!sector.faceIds.empty() && position.x >= sector.minX && position.x <= sector.maxX
            && position.y >= sector.minY && position.y <= sector.maxY
            && position.z >= sector.minZ && position.z <= sector.maxZ)
        {
            return static_cast<uint16_t>(sectorIndex);
        }
    }

    return 0;
}

std::unordered_map<std::string, const EditorIndoorGeometrySurfaceMetadata *> buildSurfaceLookup(
    const EditorIndoorGeometryMetadata &metadata)
{
    std::unordered_map<std::string, const EditorIndoorGeometrySurfaceMetadata *> lookup;

    for (const EditorIndoorGeometrySurfaceMetadata &surface : metadata.surfaces)
    {
        if (!surface.id.empty())
        {
            lookup[toLowerCopy(surface.id)] = &surface;
        }

        if (!surface.sourceNodeName.empty())
        {
            lookup[toLowerCopy(surface.sourceNodeName)] = &surface;
        }
    }

    return lookup;
}

const EditorIndoorGeometrySurfaceMetadata *findSurfaceMetadata(
    const std::unordered_map<std::string, const EditorIndoorGeometrySurfaceMetadata *> &surfaceLookup,
    const std::string &sourceNodeName)
{
    const auto sourceIterator = surfaceLookup.find(toLowerCopy(sourceNodeName));

    if (sourceIterator != surfaceLookup.end())
    {
        return sourceIterator->second;
    }

    const auto idIterator = surfaceLookup.find(toLowerCopy(surfaceIdFromSourceNode(sourceNodeName)));

    if (idIterator != surfaceLookup.end())
    {
        return idIterator->second;
    }

    return nullptr;
}

template <typename MetadataType>
std::unordered_map<std::string, const MetadataType *> buildSourceNodeLookup(
    const std::vector<MetadataType> &entries)
{
    std::unordered_map<std::string, const MetadataType *> lookup;

    for (const MetadataType &entry : entries)
    {
        if (!entry.id.empty())
        {
            lookup[toLowerCopy(entry.id)] = &entry;
        }

        if (!entry.sourceNodeName.empty())
        {
            lookup[toLowerCopy(entry.sourceNodeName)] = &entry;
        }
    }

    return lookup;
}

template <typename MetadataType>
const MetadataType *findSourceNodeMetadata(
    const std::unordered_map<std::string, const MetadataType *> &lookup,
    const std::string &sourceNodeName,
    const std::string &sourceId)
{
    const auto sourceIterator = lookup.find(toLowerCopy(sourceNodeName));

    if (sourceIterator != lookup.end())
    {
        return sourceIterator->second;
    }

    const auto idIterator = lookup.find(toLowerCopy(sourceId));

    if (idIterator != lookup.end())
    {
        return idIterator->second;
    }

    return nullptr;
}

bool sourceSurfaceAttributes(
    const EditorIndoorGeometrySurfaceMetadata *pSurfaceMetadata,
    uint32_t &attributes,
    std::string &errorMessage)
{
    attributes = Game::faceAttributeBit(Game::FaceAttribute::Clickable);
    if (pSurfaceMetadata == nullptr)
    {
        return true;
    }
    if (!pSurfaceMetadata->trigger)
    {
        attributes = 0;                 // a surface with only flags (water, a cog for SetTexture) is not clickable
    }
    const std::unordered_map<std::string, Game::FaceAttribute> flags = {
        {"clickable", Game::FaceAttribute::Clickable},
        {"touch", Game::FaceAttribute::TriggerByTouch},
        {"pressure_plate", Game::FaceAttribute::PressurePlate},
        {"secret", Game::FaceAttribute::IsSecret},
        {"invisible", Game::FaceAttribute::Invisible},
        {"untouchable", Game::FaceAttribute::Untouchable},
        {"trigger_monster", Game::FaceAttribute::TriggerByMonster},
        {"trigger_object", Game::FaceAttribute::TriggerByObject},
        {"has_hint", Game::FaceAttribute::HasHint},
        {"texture_move_by_door", Game::FaceAttribute::TextureMoveByDoor},
        {"animated", Game::FaceAttribute::Animated},
        {"lava", Game::FaceAttribute::Lava},
        {"water", Game::FaceAttribute::Fluid},
    };
    for (const std::string &name : pSurfaceMetadata->flags)
    {
        const auto iterator = flags.find(toLowerCopy(name));
        if (iterator == flags.end())
        {
            errorMessage = "unsupported source surface flag: " + name + " on " + pSurfaceMetadata->id;
            return false;
        }
        attributes |= Game::faceAttributeBit(iterator->second);
    }
    const std::string activation = pSurfaceMetadata->trigger
        ? toLowerCopy(pSurfaceMetadata->trigger->type) : std::string();
    if (activation == "touch" || activation == "pressure_plate")
    {
        attributes &= ~Game::faceAttributeBit(Game::FaceAttribute::Clickable);
        attributes |= Game::faceAttributeBit(Game::FaceAttribute::TriggerByTouch);
        if (activation == "pressure_plate")
        {
            attributes |= Game::faceAttributeBit(Game::FaceAttribute::PressurePlate);
        }
    }
    return true;
}

bool compileTriggerSurfaceModel(
    const ImportedModel &model,
    const EditorIndoorGeometrySurfaceMetadata *pSurfaceMetadata,
    const std::unordered_map<std::string, uint16_t> &roomSectorById,
    const MaterialTextureLookup &materialTextureLookup,
    std::optional<uint16_t> sourceSector,
    float scale,
    IndoorVertexInterner &vertexInterner,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage)
{
    const uint16_t sectorIndex = sourceSector.value_or(chooseMechanismSector(indoorGeometry, model, scale));
    Game::IndoorSector &sector = indoorGeometry.sectors[sectorIndex];
    bool boundsInitialized = true;
    std::vector<uint16_t> positionVertexIds;

    if (!appendModelVertices(
            model,
            scale,
            indoorGeometry,
            &sector,
            &boundsInitialized,
            vertexInterner,
            positionVertexIds,
            errorMessage))
    {
        return false;
    }

    std::vector<uint16_t> appendedFaceIds;
    uint32_t attributes = 0;
    if (!sourceSurfaceAttributes(pSurfaceMetadata, attributes, errorMessage))
    {
        return false;
    }

    // The surface's second room (`back_room`): its faces are drawn when either room is visible.
    uint16_t backSectorIndex = sectorIndex;
    if (pSurfaceMetadata != nullptr && !pSurfaceMetadata->backRoomId.empty())
    {
        const auto backRoom = roomSectorById.find(pSurfaceMetadata->backRoomId);
        if (backRoom == roomSectorById.end())
        {
            errorMessage = "indoor source surface names an unknown back room: " + pSurfaceMetadata->id;
            return false;
        }
        backSectorIndex = backRoom->second;
    }

    if (!appendImportedFaces(
            model,
            materialTextureLookup,
            positionVertexIds,
            sectorIndex,
            backSectorIndex,
            attributes,
            false,
            indoorGeometry,
            appendedFaceIds,
            result,
            errorMessage))
    {
        return false;
    }

    for (uint16_t faceIndex : appendedFaceIds)
    {
        Game::IndoorFace &face = indoorGeometry.faces[faceIndex];

        if (pSurfaceMetadata != nullptr && pSurfaceMetadata->trigger.has_value())
        {
            face.cogTriggered = pSurfaceMetadata->trigger->eventId;
            face.cogTriggerType = 0;
        }

        if (pSurfaceMetadata != nullptr)
        {
            face.cogNumber = pSurfaceMetadata->cogNumber;
        }

        appendFaceToSector(sector, faceIndex, face.facetType);
    }

    refreshSectorCounts(sector);
    // Reported like the static groups, so a converter can name the faces of a node (MM9's monster barriers).
    result.generatedFaceGroups.push_back(IndoorSourceFaceGroup{
        sourceNodeNameFromModelName(model.name),
        std::move(appendedFaceIds),
    });
    return true;
}

void compileEntityMarker(
    const ImportedModel &model,
    const EditorIndoorGeometryEntityMetadata *pEntityMetadata,
    std::optional<uint16_t> sourceSector,
    float scale,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result)
{
    const Game::IndoorVertex position = markerPosition(model, scale);
    const uint16_t sectorIndex = sourceSector.value_or(chooseMarkerSector(indoorGeometry, position));
    Game::IndoorEntity entity = {};
    entity.x = position.x;
    entity.y = position.y;
    entity.z = position.z;

    if (pEntityMetadata != nullptr)
    {
        entity.decorationListId = pEntityMetadata->decorationListId;
        entity.eventIdPrimary = pEntityMetadata->eventIdPrimary;
        entity.eventIdSecondary = pEntityMetadata->eventIdSecondary;
        entity.facing = pEntityMetadata->facing;
        entity.name = pEntityMetadata->id;

        if (entity.decorationListId == 0)
        {
            result.warnings.push_back("Decoration marker has no decoration_list_id: " + pEntityMetadata->id);
        }
    }
    else
    {
        entity.name = entityIdFromSourceNode(sourceNodeNameFromModelName(model.name));
        result.warnings.push_back("Decoration marker has no metadata: " + sourceNodeNameFromModelName(model.name));
    }

    const uint16_t entityIndex = static_cast<uint16_t>(indoorGeometry.entities.size());
    indoorGeometry.entities.push_back(std::move(entity));
    indoorGeometry.sectors[sectorIndex].decorationIds.push_back(entityIndex);
    refreshSectorCounts(indoorGeometry.sectors[sectorIndex]);
}

void compileLightMarker(
    const ImportedModel &model,
    const EditorIndoorGeometryLightMetadata *pLightMetadata,
    std::optional<uint16_t> sourceSector,
    float scale,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result)
{
    const Game::IndoorVertex position = markerPosition(model, scale);
    const uint16_t sectorIndex = sourceSector.value_or(chooseMarkerSector(indoorGeometry, position));
    Game::IndoorLight light = {};
    light.x = static_cast<int16_t>(position.x);
    light.y = static_cast<int16_t>(position.y);
    light.z = static_cast<int16_t>(position.z);

    if (pLightMetadata != nullptr)
    {
        light.red = pLightMetadata->color[0];
        light.green = pLightMetadata->color[1];
        light.blue = pLightMetadata->color[2];
        light.radius = pLightMetadata->radius;
        light.brightness = pLightMetadata->brightness;
        light.type = toLowerCopy(pLightMetadata->type) == "point" ? 0 : 1;
        light.id = pLightMetadata->group;

        if (light.radius == 0 || light.brightness == 0)
        {
            result.warnings.push_back("Light marker has zero radius or brightness: " + pLightMetadata->id);
        }
    }
    else
    {
        light.red = 255;
        light.green = 255;
        light.blue = 255;
        result.warnings.push_back("Light marker has no metadata: " + sourceNodeNameFromModelName(model.name));
    }

    const uint16_t lightIndex = static_cast<uint16_t>(indoorGeometry.lights.size());
    indoorGeometry.lights.push_back(light);
    indoorGeometry.sectors[sectorIndex].lightIds.push_back(lightIndex);
    refreshSectorCounts(indoorGeometry.sectors[sectorIndex]);
}

void compileSpawnMarker(
    const ImportedModel &model,
    const EditorIndoorGeometrySpawnMetadata *pSpawnMetadata,
    float scale,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result)
{
    const Game::IndoorVertex position = markerPosition(model, scale);
    Game::IndoorSpawn spawn = {};
    spawn.x = position.x;
    spawn.y = position.y;
    spawn.z = position.z;

    if (pSpawnMetadata != nullptr)
    {
        spawn.typeId = pSpawnMetadata->typeId;
        spawn.index = pSpawnMetadata->index;
        spawn.radius = pSpawnMetadata->radius;
        spawn.group = pSpawnMetadata->group;

        if (spawn.typeId == 0 && spawn.index == 0)
        {
            result.warnings.push_back("Spawn marker has unresolved type/index: " + pSpawnMetadata->id);
        }
    }
    else
    {
        result.warnings.push_back("Spawn marker has no metadata: " + sourceNodeNameFromModelName(model.name));
    }

    indoorGeometry.spawns.push_back(spawn);
}

bool compileMechanismModel(
    const ImportedModel &model,
    const EditorIndoorGeometryMechanismMetadata *pMechanismMetadata,
    const EditorIndoorGeometrySurfaceMetadata *pSurfaceMetadata,
    const std::unordered_map<std::string, uint16_t> &roomSectorById,
    const MaterialTextureLookup &materialTextureLookup,
    std::optional<uint16_t> sourceSector,
    float scale,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage)
{
    if (pMechanismMetadata == nullptr)
    {
        result.warnings.push_back("Mechanism source mesh has no metadata: " + sourceNodeNameFromModelName(model.name));
        return true;
    }

    const uint16_t sectorIndex = sourceSector.value_or(chooseMechanismSector(indoorGeometry, model, scale));
    Game::IndoorSector &sector = indoorGeometry.sectors[sectorIndex];
    bool boundsInitialized = true;
    IndoorVertexInterner mechanismVertexInterner;
    std::vector<uint16_t> positionVertexIds;

    if (!appendModelVertices(
            model,
            scale,
            indoorGeometry,
            &sector,
            &boundsInitialized,
            mechanismVertexInterner,
            positionVertexIds,
            errorMessage))
    {
        return false;
    }

    std::vector<uint16_t> appendedFaceIds;

    if (!appendImportedFaces(
            model,
            materialTextureLookup,
            positionVertexIds,
            sectorIndex,
            sectorIndex,
            0,
            false,
            indoorGeometry,
            appendedFaceIds,
            result,
            errorMessage))
    {
        return false;
    }

    std::vector<uint16_t> vertexIds;
    vertexIds.reserve(positionVertexIds.size());

    for (uint16_t vertexId : positionVertexIds)
    {
        if (std::find(vertexIds.begin(), vertexIds.end(), vertexId) == vertexIds.end())
        {
            vertexIds.push_back(vertexId);
        }
    }

    for (uint16_t faceIndex : appendedFaceIds)
    {
        if (pSurfaceMetadata != nullptr)
        {
            Game::IndoorFace &face = indoorGeometry.faces[faceIndex];
            if (!sourceSurfaceAttributes(pSurfaceMetadata, face.attributes, errorMessage))
            {
                return false;
            }
            if (pSurfaceMetadata->trigger)
            {
                face.cogTriggered = pSurfaceMetadata->trigger->eventId;
            }
            face.cogNumber = pSurfaceMetadata->cogNumber;
        }
        appendFaceToSector(sector, faceIndex, indoorGeometry.faces[faceIndex].facetType);
    }

    refreshSectorCounts(sector);

    // A rotating mover (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md): its faces keep the sector list of their
    // stored pose but take facet type 0, their kind following the current normal, and belong also to the other room
    // the swing enters. Its direction is zero and its travel in tenths of a degree, so the rest is an ordinary door.
    const bool rotatingMover = toLowerCopy(trimCopy(pMechanismMetadata->kind)) == "rotating";
    std::optional<uint16_t> extraSectorIndex;

    if (rotatingMover)
    {
        if (pMechanismMetadata->extraRoomIds.size() > 1)
        {
            errorMessage = "Rotating mechanism has more than one extra room: " + pMechanismMetadata->id;
            return false;
        }

        if (!pMechanismMetadata->extraRoomIds.empty())
        {
            const auto extraRoom = roomSectorById.find(pMechanismMetadata->extraRoomIds.front());

            if (extraRoom == roomSectorById.end())
            {
                errorMessage = "Rotating mechanism names an unknown room: " + pMechanismMetadata->id;
                return false;
            }

            if (extraRoom->second != sectorIndex)
            {
                extraSectorIndex = extraRoom->second;
            }
        }

        for (uint16_t faceIndex : appendedFaceIds)
        {
            Game::IndoorFace &face = indoorGeometry.faces[faceIndex];

            if (extraSectorIndex)
            {
                face.roomBehindNumber = *extraSectorIndex;
                appendFaceToSector(indoorGeometry.sectors[*extraSectorIndex], faceIndex, face.facetType);
            }

            face.facetType = 0;
        }

        if (extraSectorIndex)
        {
            refreshSectorCounts(indoorGeometry.sectors[*extraSectorIndex]);
        }
    }

    Game::IndoorSceneDoor sceneDoor = {};
    sceneDoor.doorIndex = result.generatedDoors.size();
    sceneDoor.door.slotIndex = sceneDoor.doorIndex;
    sceneDoor.door.doorId = pMechanismMetadata->doorId.value_or(static_cast<uint32_t>(sceneDoor.doorIndex));
    sceneDoor.door.moveLength = positiveLengthFromMechanismMetadata(*pMechanismMetadata);
    sceneDoor.door.openSpeed = positiveSpeedOrDefault(pMechanismMetadata->openSpeed, 128);
    sceneDoor.door.closeSpeed = positiveSpeedOrDefault(pMechanismMetadata->closeSpeed, 128);
    sceneDoor.door.state = stateFromMechanismMetadata(*pMechanismMetadata);
    sceneDoor.door.vertexIds = std::move(vertexIds);
    sceneDoor.door.faceIds = std::move(appendedFaceIds);
    sceneDoor.door.sectorIds.push_back(sectorIndex);
    if (extraSectorIndex)
    {
        sceneDoor.door.sectorIds.push_back(*extraSectorIndex);
    }
    sceneDoor.door.deltaUs.assign(sceneDoor.door.faceIds.size(), 0);
    sceneDoor.door.deltaVs.assign(sceneDoor.door.faceIds.size(), 0);
    sceneDoor.door.xOffsets.reserve(sceneDoor.door.vertexIds.size());
    sceneDoor.door.yOffsets.reserve(sceneDoor.door.vertexIds.size());
    sceneDoor.door.zOffsets.reserve(sceneDoor.door.vertexIds.size());

    const std::string sourcePose = toLowerCopy(trimCopy(pMechanismMetadata->sourcePose));
    if (sourcePose != "open" && sourcePose != "closed")
    {
        errorMessage = "Mechanism source_pose must be open or closed: " + pMechanismMetadata->id;
        return false;
    }
    const std::array<float, 3> moveAxis = moveAxisOrDefault(*pMechanismMetadata);
    for (float component : moveAxis)
    {
        if (!std::isfinite(component) || std::abs(component) > 1.0f)
        {
            errorMessage = "Mechanism direction component is outside [-1,1]: " + pMechanismMetadata->id;
            return false;
        }
    }
    sceneDoor.door.directionX = fixedDirectionComponent(moveAxis[0]);
    sceneDoor.door.directionY = fixedDirectionComponent(moveAxis[1]);
    sceneDoor.door.directionZ = fixedDirectionComponent(moveAxis[2]);
    const std::array<int, 3> fixedDirection = {
        sceneDoor.door.directionX, sceneDoor.door.directionY, sceneDoor.door.directionZ};

    for (uint16_t vertexId : sceneDoor.door.vertexIds)
    {
        const Game::IndoorVertex &vertex = indoorGeometry.vertices[vertexId];
        const std::array<int, 3> position = {vertex.x, vertex.y, vertex.z};
        std::array<int16_t, 3> offsets;
        for (size_t axis = 0; axis < offsets.size(); ++axis)
        {
            const double displacement = double(fixedDirection[axis]) / 65536.0 * sceneDoor.door.moveLength;
            // Runtime distance is zero when open and moveLength when closed.
            const double openPosition = position[axis] - (sourcePose == "closed" ? displacement : 0.0);
            const double closedPosition = openPosition + displacement;
            if (openPosition < std::numeric_limits<int16_t>::min()
                || openPosition > std::numeric_limits<int16_t>::max()
                || closedPosition < std::numeric_limits<int16_t>::min()
                || closedPosition > std::numeric_limits<int16_t>::max())
            {
                errorMessage = "Mechanism endpoint exceeds native coordinate range: " + pMechanismMetadata->id;
                return false;
            }
            offsets[axis] = int16_t(std::lround(openPosition));
        }
        sceneDoor.door.xOffsets.push_back(offsets[0]);
        sceneDoor.door.yOffsets.push_back(offsets[1]);
        sceneDoor.door.zOffsets.push_back(offsets[2]);
    }

    sceneDoor.door.numVertices = static_cast<uint16_t>(sceneDoor.door.vertexIds.size());
    sceneDoor.door.numFaces = static_cast<uint16_t>(sceneDoor.door.faceIds.size());
    sceneDoor.door.numSectors = static_cast<uint16_t>(sceneDoor.door.sectorIds.size());
    sceneDoor.door.numOffsets = static_cast<uint16_t>(sceneDoor.door.xOffsets.size());
    result.generatedDoors.push_back(std::move(sceneDoor));
    return true;
}

bool compileStaticFaceGroupModel(
    const ImportedModel &model,
    const MaterialTextureLookup &materialTextureLookup,
    std::optional<uint16_t> sourceSector,
    float scale,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage)
{
    const uint16_t sectorIndex = sourceSector.value_or(chooseMechanismSector(indoorGeometry, model, scale));
    Game::IndoorSector &sector = indoorGeometry.sectors[sectorIndex];
    bool boundsInitialized = true;
    IndoorVertexInterner vertexInterner;
    std::vector<uint16_t> positionVertexIds;
    if (!appendModelVertices(
            model,
            scale,
            indoorGeometry,
            &sector,
            &boundsInitialized,
            vertexInterner,
            positionVertexIds,
            errorMessage))
    {
        return false;
    }

    std::vector<uint16_t> appendedFaceIds;
    if (!appendImportedFaces(
            model,
            materialTextureLookup,
            positionVertexIds,
            sectorIndex,
            sectorIndex,
            0,
            false,
            indoorGeometry,
            appendedFaceIds,
            result,
            errorMessage))
    {
        return false;
    }

    for (uint16_t faceIndex : appendedFaceIds)
    {
        appendFaceToSector(sector, faceIndex, indoorGeometry.faces[faceIndex].facetType);
    }
    refreshSectorCounts(sector);
    result.generatedFaceGroups.push_back(IndoorSourceFaceGroup{
        sourceNodeNameFromModelName(model.name),
        std::move(appendedFaceIds),
    });
    return true;
}
}

bool compileIndoorSourceGeometry(
    const std::filesystem::path &sourcePath,
    const EditorIndoorGeometryMetadata &metadata,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage)
{
    result = {};
    std::vector<ImportedModel> models;

    if (!loadImportedModelsFromFile(
            sourcePath,
            models,
            errorMessage,
            metadata.importSettings.mergeCoplanarFaces,
            true,
            !metadata.importSettings.triangulateNgons))
    {
        return false;
    }

    if (!std::isfinite(metadata.source.unitScale) || metadata.source.unitScale <= 0.0f)
    {
        errorMessage = "indoor source unit scale must be finite and positive";
        return false;
    }
    for (const EditorIndoorGeometryMaterialMetadata &material : metadata.materials)
    {
        if (material.textureWidth == 0 || material.textureHeight == 0)
        {
            errorMessage = "indoor source texture dimensions must be positive: " + material.id;
            return false;
        }
    }
    for (const ImportedModel &model : models)
    {
        for (const ImportedModelPosition &position : model.positions)
        {
            for (float value : {position.x, position.y, position.z})
            {
                const double scaled = std::round(double(value) * metadata.source.unitScale);
                if (!std::isfinite(scaled) || scaled < -32768 || scaled > 32767)
                {
                    errorMessage = "indoor source coordinate exceeds native int16 range in " + model.name;
                    return false;
                }
            }
        }
    }

    const MaterialTextureLookup materialTextureLookup = buildMaterialTextureLookup(metadata);
    const std::unordered_map<std::string, const EditorIndoorGeometryPortalMetadata *> portalLookup =
        buildPortalLookup(metadata);
    const std::unordered_map<std::string, const EditorIndoorGeometryMechanismMetadata *> mechanismLookup =
        buildMechanismLookup(metadata);
    const std::unordered_map<std::string, const EditorIndoorGeometrySurfaceMetadata *> surfaceLookup =
        buildSurfaceLookup(metadata);
    const std::unordered_map<std::string, const EditorIndoorGeometryEntityMetadata *> entityLookup =
        buildSourceNodeLookup(metadata.entities);
    const std::unordered_map<std::string, const EditorIndoorGeometryLightMetadata *> lightLookup =
        buildSourceNodeLookup(metadata.lights);
    const std::unordered_map<std::string, const EditorIndoorGeometrySpawnMetadata *> spawnLookup =
        buildSourceNodeLookup(metadata.spawns);
    std::unordered_map<std::string, uint16_t> roomSectorById;
    IndoorVertexInterner staticVertexInterner;

    result.indoorGeometry.version = 8;
    if (metadata.importSettings.reserveSectorZero)
    {
        Game::IndoorSector emptySector = {};
        emptySector.firstBspNode = -1;
        result.indoorGeometry.sectors.push_back(emptySector);
    }

    for (const ImportedModel &model : models)
    {
        const std::string sourceNodeName = sourceNodeNameFromModelName(model.name);

        if (!startsWithInsensitive(sourceNodeName, "ROOM_"))
        {
            continue;
        }

        const std::string roomId = roomIdFromSourceNode(sourceNodeName);
        const uint16_t sectorIndex = static_cast<uint16_t>(result.indoorGeometry.sectors.size());
        if (!roomSectorById.emplace(roomId, sectorIndex).second)
        {
            errorMessage = "duplicate indoor source room identity: " + roomId;
            return false;
        }

        if (!compileRoomModel(
                model,
                materialTextureLookup,
                sectorIndex,
                metadata.source.unitScale,
                staticVertexInterner,
                result.indoorGeometry,
                result,
                errorMessage))
        {
            return false;
        }
    }

    if (roomSectorById.empty())
    {
        errorMessage = "indoor source compiler found no ROOM_* meshes in " + sourcePath.string();
        return false;
    }

    std::unordered_map<std::string, uint16_t> sourceNodeSectors;
    for (const EditorIndoorGeometryRoomMetadata &room : metadata.rooms)
    {
        const auto sector = roomSectorById.find(room.id);
        if (sector == roomSectorById.end())
        {
            errorMessage = "indoor source metadata refers to an unknown room: " + room.id;
            return false;
        }
        if (room.minAmbientLightLevel < 0 || room.minAmbientLightLevel > 31)
        {
            errorMessage = "indoor room min_ambient_light_level must be between 0 and 31";
            return false;
        }
        result.indoorGeometry.sectors[sector->second].minAmbientLightLevel = room.minAmbientLightLevel;
        for (const std::string &name : room.sourceNodeNames)
        {
            const bool sourceNodeExists = std::any_of(models.begin(), models.end(), [&name](const ImportedModel &model)
            {
                return toLowerCopy(sourceNodeNameFromModelName(model.name)) == toLowerCopy(name);
            });
            if (!sourceNodeExists)
            {
                errorMessage = "indoor source room refers to a missing node: " + name;
                return false;
            }
            const auto [iterator, inserted] = sourceNodeSectors.emplace(toLowerCopy(name), sector->second);
            if (!inserted && iterator->second != sector->second)
            {
                errorMessage = "indoor source node assigned to multiple rooms: " + name;
                return false;
            }
        }
    }
    const auto explicitSector = [&sourceNodeSectors](const std::string &name) -> std::optional<uint16_t>
    {
        const auto iterator = sourceNodeSectors.find(toLowerCopy(name));
        return iterator == sourceNodeSectors.end() ? std::nullopt : std::optional<uint16_t>(iterator->second);
    };

    for (const ImportedModel &model : models)
    {
        const std::string sourceNodeName = sourceNodeNameFromModelName(model.name);

        if (!startsWithInsensitive(sourceNodeName, "PORTAL_"))
        {
            continue;
        }

        if (!compilePortalModel(
                model,
                findPortalMetadata(portalLookup, sourceNodeName),
                roomSectorById,
                materialTextureLookup,
                metadata.source.unitScale,
                staticVertexInterner,
                result.indoorGeometry,
                result,
                errorMessage))
        {
            return false;
        }
    }

    for (const ImportedModel &model : models)
    {
        const std::string sourceNodeName = sourceNodeNameFromModelName(model.name);

        if (!startsWithInsensitive(sourceNodeName, "INTERACT_")
            && !startsWithInsensitive(sourceNodeName, "IPVAR_")
            && !startsWithInsensitive(sourceNodeName, "STATIC_"))
        {
            continue;
        }

        if (startsWithInsensitive(sourceNodeName, "STATIC_") && !explicitSector(sourceNodeName))
        {
            errorMessage = "indoor static source mesh requires explicit room ownership: " + sourceNodeName;
            return false;
        }

        if (!compileStaticFaceGroupModel(
                model,
                materialTextureLookup,
                explicitSector(sourceNodeName),
                metadata.source.unitScale,
                result.indoorGeometry,
                result,
                errorMessage))
        {
            return false;
        }
    }

    for (const ImportedModel &model : models)
    {
        const std::string sourceNodeName = sourceNodeNameFromModelName(model.name);

        if (!startsWithInsensitive(sourceNodeName, "TRIGGER_"))
        {
            continue;
        }

        if (!compileTriggerSurfaceModel(
                model,
                findSurfaceMetadata(surfaceLookup, sourceNodeName),
                roomSectorById,
                materialTextureLookup,
                explicitSector(sourceNodeName),
                metadata.source.unitScale,
                staticVertexInterner,
                result.indoorGeometry,
                result,
                errorMessage))
        {
            return false;
        }
    }

    for (const ImportedModel &model : models)
    {
        const std::string sourceNodeName = sourceNodeNameFromModelName(model.name);

        if (!startsWithInsensitive(sourceNodeName, "MECH_"))
        {
            continue;
        }

        if (!compileMechanismModel(
                model,
                findMechanismMetadata(mechanismLookup, sourceNodeName),
                findSurfaceMetadata(surfaceLookup, sourceNodeName),
                roomSectorById,
                materialTextureLookup,
                explicitSector(sourceNodeName),
                metadata.source.unitScale,
                result.indoorGeometry,
                result,
                errorMessage))
        {
            return false;
        }
    }

    for (const ImportedModel &model : models)
    {
        const std::string sourceNodeName = sourceNodeNameFromModelName(model.name);

        if (startsWithInsensitive(sourceNodeName, "DECOR_"))
        {
            compileEntityMarker(
                model,
                findSourceNodeMetadata(entityLookup, sourceNodeName, entityIdFromSourceNode(sourceNodeName)),
                explicitSector(sourceNodeName),
                metadata.source.unitScale,
                result.indoorGeometry,
                result);
        }
        else if (startsWithInsensitive(sourceNodeName, "LIGHT_"))
        {
            compileLightMarker(
                model,
                findSourceNodeMetadata(lightLookup, sourceNodeName, lightIdFromSourceNode(sourceNodeName)),
                explicitSector(sourceNodeName),
                metadata.source.unitScale,
                result.indoorGeometry,
                result);
        }
        else if (startsWithInsensitive(sourceNodeName, "SPAWN_"))
        {
            compileSpawnMarker(
                model,
                findSourceNodeMetadata(spawnLookup, sourceNodeName, spawnIdFromSourceNode(sourceNodeName)),
                metadata.source.unitScale,
                result.indoorGeometry,
                result);
        }
    }

    result.indoorGeometry.rawFaceCount = static_cast<uint32_t>(result.indoorGeometry.faces.size());
    result.indoorGeometry.sectorCount = result.indoorGeometry.sectors.size();
    result.indoorGeometry.spriteCount = result.indoorGeometry.entities.size();
    result.indoorGeometry.lightCount = result.indoorGeometry.lights.size();
    result.indoorGeometry.spawnCount = result.indoorGeometry.spawns.size();
    result.indoorGeometry.doorCount = static_cast<uint32_t>(result.generatedDoors.size());
    std::vector<uint16_t> movingFaceIds;
    for (const Game::IndoorSceneDoor &door : result.generatedDoors)
    {
        movingFaceIds.insert(movingFaceIds.end(), door.door.faceIds.begin(), door.door.faceIds.end());
    }
    return generateIndoorDerivedGeometry(
        result.indoorGeometry, movingFaceIds, metadata.importSettings.generateBsp,
        metadata.importSettings.generateOutlines, errorMessage);
}
}
