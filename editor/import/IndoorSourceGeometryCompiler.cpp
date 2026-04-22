#include "editor/import/IndoorSourceGeometryCompiler.h"

#include "editor/import/ObjModelImport.h"
#include "game/FaceEnums.h"
#include "game/events/EvtEnums.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <limits>
#include <optional>
#include <unordered_map>

namespace OpenYAMM::Editor
{
namespace
{
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

std::unordered_map<std::string, std::string> buildMaterialTextureLookup(
    const EditorIndoorGeometryMetadata &metadata)
{
    std::unordered_map<std::string, std::string> lookup;

    for (const EditorIndoorGeometryMaterialMetadata &material : metadata.materials)
    {
        const std::string sourceMaterial = stripIndexedMaterialSuffix(material.sourceMaterial);
        const std::string texture = trimCopy(material.texture);

        if (!sourceMaterial.empty() && !texture.empty())
        {
            lookup[toLowerCopy(sourceMaterial)] = texture;
        }

        if (!material.id.empty() && !texture.empty())
        {
            lookup[toLowerCopy(material.id)] = texture;
        }
    }

    return lookup;
}

std::string resolveFaceTextureName(
    const std::unordered_map<std::string, std::string> &materialTextureLookup,
    const std::string &materialName)
{
    const std::string sourceMaterial = stripIndexedMaterialSuffix(materialName);

    if (sourceMaterial.empty())
    {
        return "untextured";
    }

    const auto iterator = materialTextureLookup.find(toLowerCopy(sourceMaterial));

    if (iterator != materialTextureLookup.end() && !iterator->second.empty())
    {
        return iterator->second;
    }

    return sourceMaterial;
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
    size_t &vertexBase,
    std::string &errorMessage)
{
    if (indoorGeometry.vertices.size() + model.positions.size() > 0xffffu)
    {
        errorMessage = "indoor source compiler exceeded 65535 vertices";
        return false;
    }

    vertexBase = indoorGeometry.vertices.size();

    for (const ImportedModelPosition &position : model.positions)
    {
        Game::IndoorVertex vertex = convertPosition(position, scale);
        indoorGeometry.vertices.push_back(vertex);

        if (pSector != nullptr && pBoundsInitialized != nullptr)
        {
            expandSectorBounds(*pSector, vertex, *pBoundsInitialized);
        }
    }

    return true;
}

bool appendImportedFaces(
    const ImportedModel &model,
    const std::unordered_map<std::string, std::string> &materialTextureLookup,
    size_t vertexBase,
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
        face.textureName = resolveFaceTextureName(materialTextureLookup, importedFace.materialName);
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

            face.vertexIndices.push_back(static_cast<uint16_t>(vertexBase + importedVertex.positionIndex));

            if (importedVertex.hasUv)
            {
                face.textureUs.push_back(static_cast<int16_t>(clampToInt16(
                    static_cast<int>(std::lround(importedVertex.u * 256.0f)))));
                face.textureVs.push_back(static_cast<int16_t>(clampToInt16(
                    static_cast<int>(std::lround((1.0f - importedVertex.v) * 256.0f)))));
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
    const std::unordered_map<std::string, std::string> &materialTextureLookup,
    uint16_t sectorIndex,
    float scale,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage)
{
    Game::IndoorSector sector = {};
    sector.firstBspNode = -1;
    bool boundsInitialized = false;
    size_t vertexBase = 0;

    if (!appendModelVertices(model, scale, indoorGeometry, &sector, &boundsInitialized, vertexBase, errorMessage))
    {
        return false;
    }

    std::vector<uint16_t> appendedFaceIds;

    if (!appendImportedFaces(
            model,
            materialTextureLookup,
            vertexBase,
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

bool compilePortalModel(
    const ImportedModel &model,
    const EditorIndoorGeometryPortalMetadata *pPortalMetadata,
    const std::unordered_map<std::string, uint16_t> &roomSectorById,
    const std::unordered_map<std::string, std::string> &materialTextureLookup,
    float scale,
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

    size_t vertexBase = 0;

    if (!appendModelVertices(model, scale, indoorGeometry, nullptr, nullptr, vertexBase, errorMessage))
    {
        return false;
    }

    std::vector<uint16_t> appendedFaceIds;
    const uint32_t portalAttributes = static_cast<uint32_t>(Game::FaceAttribute::IsPortal);

    if (!appendImportedFaces(
            model,
            materialTextureLookup,
            vertexBase,
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

        if (centerX >= sector.minX && centerX <= sector.maxX
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

        if (position.x >= sector.minX && position.x <= sector.maxX
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

bool compileTriggerSurfaceModel(
    const ImportedModel &model,
    const EditorIndoorGeometrySurfaceMetadata *pSurfaceMetadata,
    const std::unordered_map<std::string, std::string> &materialTextureLookup,
    float scale,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result,
    std::string &errorMessage)
{
    const uint16_t sectorIndex = chooseMechanismSector(indoorGeometry, model, scale);
    Game::IndoorSector &sector = indoorGeometry.sectors[sectorIndex];
    bool boundsInitialized = true;
    size_t vertexBase = 0;

    if (!appendModelVertices(model, scale, indoorGeometry, &sector, &boundsInitialized, vertexBase, errorMessage))
    {
        return false;
    }

    std::vector<uint16_t> appendedFaceIds;
    uint32_t attributes = Game::faceAttributeBit(Game::FaceAttribute::Clickable);

    const bool triggerByTouch =
        pSurfaceMetadata != nullptr
        && std::find(pSurfaceMetadata->flags.begin(), pSurfaceMetadata->flags.end(), "touch")
            != pSurfaceMetadata->flags.end();

    if (triggerByTouch)
    {
        attributes |= Game::faceAttributeBit(Game::FaceAttribute::TriggerByTouch);
    }

    if (!appendImportedFaces(
            model,
            materialTextureLookup,
            vertexBase,
            sectorIndex,
            sectorIndex,
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

        appendFaceToSector(sector, faceIndex, face.facetType);
    }

    refreshSectorCounts(sector);
    return true;
}

void compileEntityMarker(
    const ImportedModel &model,
    const EditorIndoorGeometryEntityMetadata *pEntityMetadata,
    float scale,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result)
{
    const Game::IndoorVertex position = markerPosition(model, scale);
    const uint16_t sectorIndex = chooseMarkerSector(indoorGeometry, position);
    Game::IndoorEntity entity = {};
    entity.x = position.x;
    entity.y = position.y;
    entity.z = position.z;

    if (pEntityMetadata != nullptr)
    {
        entity.decorationListId = pEntityMetadata->decorationListId;
        entity.eventIdPrimary = pEntityMetadata->eventIdPrimary;
        entity.eventIdSecondary = pEntityMetadata->eventIdSecondary;
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
    float scale,
    Game::IndoorMapData &indoorGeometry,
    IndoorSourceGeometryCompileResult &result)
{
    const Game::IndoorVertex position = markerPosition(model, scale);
    const uint16_t sectorIndex = chooseMarkerSector(indoorGeometry, position);
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
    const std::unordered_map<std::string, std::string> &materialTextureLookup,
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

    const uint16_t sectorIndex = chooseMechanismSector(indoorGeometry, model, scale);
    Game::IndoorSector &sector = indoorGeometry.sectors[sectorIndex];
    bool boundsInitialized = true;
    size_t vertexBase = 0;

    if (!appendModelVertices(model, scale, indoorGeometry, &sector, &boundsInitialized, vertexBase, errorMessage))
    {
        return false;
    }

    std::vector<uint16_t> appendedFaceIds;

    if (!appendImportedFaces(
            model,
            materialTextureLookup,
            vertexBase,
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
    vertexIds.reserve(model.positions.size());

    for (size_t vertexOffset = 0; vertexOffset < model.positions.size(); ++vertexOffset)
    {
        vertexIds.push_back(static_cast<uint16_t>(vertexBase + vertexOffset));
    }

    for (uint16_t faceIndex : appendedFaceIds)
    {
        appendFaceToSector(sector, faceIndex, indoorGeometry.faces[faceIndex].facetType);
    }

    refreshSectorCounts(sector);

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
    sceneDoor.door.deltaUs.assign(sceneDoor.door.faceIds.size(), 0);
    sceneDoor.door.deltaVs.assign(sceneDoor.door.faceIds.size(), 0);
    sceneDoor.door.xOffsets.reserve(sceneDoor.door.vertexIds.size());
    sceneDoor.door.yOffsets.reserve(sceneDoor.door.vertexIds.size());
    sceneDoor.door.zOffsets.reserve(sceneDoor.door.vertexIds.size());

    for (uint16_t vertexId : sceneDoor.door.vertexIds)
    {
        const Game::IndoorVertex &vertex = indoorGeometry.vertices[vertexId];
        sceneDoor.door.xOffsets.push_back(static_cast<int16_t>(clampToInt16(vertex.x)));
        sceneDoor.door.yOffsets.push_back(static_cast<int16_t>(clampToInt16(vertex.y)));
        sceneDoor.door.zOffsets.push_back(static_cast<int16_t>(clampToInt16(vertex.z)));
    }

    const std::array<float, 3> moveAxis = moveAxisOrDefault(*pMechanismMetadata);
    sceneDoor.door.directionX = fixedDirectionComponent(moveAxis[0]);
    sceneDoor.door.directionY = fixedDirectionComponent(moveAxis[1]);
    sceneDoor.door.directionZ = fixedDirectionComponent(moveAxis[2]);
    sceneDoor.door.numVertices = static_cast<uint16_t>(sceneDoor.door.vertexIds.size());
    sceneDoor.door.numFaces = static_cast<uint16_t>(sceneDoor.door.faceIds.size());
    sceneDoor.door.numSectors = static_cast<uint16_t>(sceneDoor.door.sectorIds.size());
    sceneDoor.door.numOffsets = static_cast<uint16_t>(sceneDoor.door.xOffsets.size());
    result.generatedDoors.push_back(std::move(sceneDoor));
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

    if (!loadImportedModelsFromFile(sourcePath, models, errorMessage, false))
    {
        return false;
    }

    const std::unordered_map<std::string, std::string> materialTextureLookup = buildMaterialTextureLookup(metadata);
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

    result.indoorGeometry.version = 8;

    for (const ImportedModel &model : models)
    {
        const std::string sourceNodeName = sourceNodeNameFromModelName(model.name);

        if (!startsWithInsensitive(sourceNodeName, "ROOM_"))
        {
            continue;
        }

        const std::string roomId = roomIdFromSourceNode(sourceNodeName);
        const uint16_t sectorIndex = static_cast<uint16_t>(result.indoorGeometry.sectors.size());
        roomSectorById[roomId] = sectorIndex;

        if (!compileRoomModel(
                model,
                materialTextureLookup,
                sectorIndex,
                metadata.source.unitScale,
                result.indoorGeometry,
                result,
                errorMessage))
        {
            return false;
        }
    }

    if (result.indoorGeometry.sectors.empty())
    {
        errorMessage = "indoor source compiler found no ROOM_* meshes in " + sourcePath.string();
        return false;
    }

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
                materialTextureLookup,
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

        if (!startsWithInsensitive(sourceNodeName, "MECH_"))
        {
            continue;
        }

        if (!compileMechanismModel(
                model,
                findMechanismMetadata(mechanismLookup, sourceNodeName),
                materialTextureLookup,
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
                metadata.source.unitScale,
                result.indoorGeometry,
                result);
        }
        else if (startsWithInsensitive(sourceNodeName, "LIGHT_"))
        {
            compileLightMarker(
                model,
                findSourceNodeMetadata(lightLookup, sourceNodeName, lightIdFromSourceNode(sourceNodeName)),
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
    return true;
}
}
