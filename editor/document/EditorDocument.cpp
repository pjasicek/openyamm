#include "editor/document/EditorDocument.h"
#include "editor/import/IndoorSourceGeometryCompiler.h"
#include "editor/import/ObjModelImport.h"

#include <yaml-cpp/yaml.h>
#include <SDL3/SDL.h>

#include <cctype>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string_view>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Editor
{
namespace
{
constexpr uint32_t EnvironmentFlagRain = 0x1;
constexpr uint32_t EnvironmentFlagSnow = 0x2;
constexpr uint32_t EnvironmentFlagUnderwater = 0x4;
constexpr uint32_t EnvironmentFlagNoTerrain = 0x8;
constexpr uint32_t EnvironmentFlagAlwaysDark = 0x10;
constexpr uint32_t EnvironmentFlagAlwaysLight = 0x20;
constexpr uint32_t EnvironmentFlagAlwaysFoggy = 0x40;
constexpr uint32_t EnvironmentFlagRedFog = 0x80;

constexpr size_t SpriteObjectContainingItemSize = 0x24;
constexpr size_t ChestItemPayloadSize = 140 * 36;
constexpr char DocumentSnapshotSeparator[] = "\n---ODM-HEX---\n";
constexpr char IndoorDocumentSnapshotSeparator[] = "\n---BLV-HEX---\n";
constexpr char DocumentSnapshotGeometryMetadataSeparator[] = "\n---GEOMETRY-YML---\n";
constexpr char IndoorDocumentSnapshotGeometryMetadataSeparator[] = "\n---INDOOR-GEOMETRY-YML---\n";
constexpr char DocumentSnapshotTerrainMetadataSeparator[] = "\n---TERRAIN-YML---\n";
constexpr int DefaultOutdoorBoundsExtent = 23143;
constexpr int DefaultOutdoorEncounterChance = 0;
constexpr int DefaultOutdoorRedbookTrack = 4;
constexpr std::string_view PartyStartEntityName = "party start";

std::string bytesToUpperHex(const std::vector<uint8_t> &bytes)
{
    static constexpr char HexDigits[] = "0123456789ABCDEF";

    std::string text;
    text.reserve(bytes.size() * 2);

    for (uint8_t value : bytes)
    {
        text.push_back(HexDigits[(value >> 4) & 0x0f]);
        text.push_back(HexDigits[value & 0x0f]);
    }

    return text;
}

bool upperHexToBytes(const std::string &text, std::vector<uint8_t> &bytes)
{
    bytes.clear();

    if ((text.size() % 2) != 0)
    {
        return false;
    }

    auto decodeNibble = [](char character) -> int
    {
        if (character >= '0' && character <= '9')
        {
            return character - '0';
        }

        if (character >= 'A' && character <= 'F')
        {
            return 10 + character - 'A';
        }

        if (character >= 'a' && character <= 'f')
        {
            return 10 + character - 'a';
        }

        return -1;
    };

    bytes.reserve(text.size() / 2);

    for (size_t index = 0; index < text.size(); index += 2)
    {
        const int highNibble = decodeNibble(text[index]);
        const int lowNibble = decodeNibble(text[index + 1]);

        if (highNibble < 0 || lowNibble < 0)
        {
            return false;
        }

        bytes.push_back(static_cast<uint8_t>((highNibble << 4) | lowNibble));
    }

    return true;
}

std::filesystem::path scenePhysicalPathFromVirtual(
    const std::filesystem::path &developmentRoot,
    const std::string &sceneVirtualPath)
{
    return developmentRoot / std::filesystem::path(sceneVirtualPath);
}

std::string sceneVirtualPathFromPhysical(
    const std::filesystem::path &developmentRoot,
    const std::filesystem::path &scenePhysicalPath)
{
    return std::filesystem::relative(scenePhysicalPath, developmentRoot).generic_string();
}

bool ensureOverlaySeedTextFile(
    const std::filesystem::path &baseRoot,
    const std::filesystem::path &editorRoot,
    const std::filesystem::path &relativePath,
    std::string &errorMessage)
{
    const std::filesystem::path targetPath = editorRoot / relativePath;

    if (std::filesystem::exists(targetPath))
    {
        return true;
    }

    const std::filesystem::path sourcePath = baseRoot / relativePath;

    if (!std::filesystem::exists(sourcePath))
    {
        errorMessage = "could not seed overlay file because the base file is missing: " + sourcePath.string();
        return false;
    }

    std::error_code createDirectoriesError;
    std::filesystem::create_directories(targetPath.parent_path(), createDirectoriesError);

    if (createDirectoriesError)
    {
        errorMessage = "could not create overlay directory " + targetPath.parent_path().string()
            + ": " + createDirectoriesError.message();
        return false;
    }

    std::error_code copyError;
    std::filesystem::copy_file(sourcePath, targetPath, std::filesystem::copy_options::overwrite_existing, copyError);

    if (copyError)
    {
        errorMessage = "could not seed overlay file " + targetPath.string() + ": " + copyError.message();
        return false;
    }

    return true;
}

bool readTextFile(const std::filesystem::path &path, std::string &text)
{
    std::ifstream input(path);

    if (!input)
    {
        return false;
    }

    text.assign(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
    return true;
}

bool readBinaryFile(const std::filesystem::path &path, std::vector<uint8_t> &bytes)
{
    bytes.clear();
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        return false;
    }

    input.seekg(0, std::ios::end);
    const std::streamsize size = input.tellg();

    if (size < 0)
    {
        return false;
    }

    input.seekg(0, std::ios::beg);
    bytes.resize(static_cast<size_t>(size));

    if (size == 0)
    {
        return true;
    }

    return input.read(reinterpret_cast<char *>(bytes.data()), size).good();
}

std::optional<std::vector<uint8_t>> loadLegacyIndoorCompanionBytes(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::filesystem::path &scenePhysicalPath,
    const std::string &sceneVirtualPath,
    const std::string &legacyCompanionFile)
{
    if (legacyCompanionFile.empty())
    {
        return std::nullopt;
    }

    std::vector<std::filesystem::path> physicalCandidates;

    if (!scenePhysicalPath.empty())
    {
        physicalCandidates.push_back(scenePhysicalPath.parent_path() / legacyCompanionFile);
    }

    const std::filesystem::path companionPath = legacyCompanionFile;

    if (companionPath.is_absolute())
    {
        physicalCandidates.push_back(companionPath);
    }

    for (const std::filesystem::path &candidate : physicalCandidates)
    {
        std::vector<uint8_t> bytes;

        if (readBinaryFile(candidate, bytes))
        {
            return bytes;
        }
    }

    std::vector<std::string> virtualCandidates;

    if (!sceneVirtualPath.empty())
    {
        virtualCandidates.push_back((std::filesystem::path(sceneVirtualPath).parent_path() / legacyCompanionFile).generic_string());
    }

    const std::string defaultGamesPath = (std::filesystem::path("Data/games") / legacyCompanionFile).generic_string();

    if (virtualCandidates.empty() || virtualCandidates.front() != defaultGamesPath)
    {
        virtualCandidates.push_back(defaultGamesPath);
    }

    for (const std::string &candidate : virtualCandidates)
    {
        const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(candidate);

        if (bytes)
        {
            return bytes;
        }
    }

    return std::nullopt;
}

void synthesizeIndoorFaceAttributeOverridesFromLegacyCompanion(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::filesystem::path &scenePhysicalPath,
    const std::string &sceneVirtualPath,
    const Game::IndoorMapData &indoorGeometry,
    Game::IndoorSceneData &sceneData)
{
    if (!sceneData.legacyCompanionFile
        || sceneData.legacyCompanionFile->empty()
        || !sceneData.initialState.faceAttributeOverrides.empty())
    {
        return;
    }

    const std::optional<std::vector<uint8_t>> companionBytes =
        loadLegacyIndoorCompanionBytes(
            assetFileSystem,
            scenePhysicalPath,
            sceneVirtualPath,
            *sceneData.legacyCompanionFile);

    if (!companionBytes)
    {
        return;
    }

    const Game::MapDeltaDataLoader loader = {};
    const std::optional<Game::MapDeltaData> legacyMapDeltaData = loader.loadIndoorFromBytes(*companionBytes, indoorGeometry);

    if (!legacyMapDeltaData || legacyMapDeltaData->faceAttributes.size() < indoorGeometry.faces.size())
    {
        return;
    }

    size_t overrideCount = 0;

    for (size_t faceIndex = 0; faceIndex < indoorGeometry.faces.size(); ++faceIndex)
    {
        if (legacyMapDeltaData->faceAttributes[faceIndex] != indoorGeometry.faces[faceIndex].attributes)
        {
            ++overrideCount;
        }
    }

    sceneData.initialState.faceAttributeOverrides.clear();
    sceneData.initialState.faceAttributeOverrides.reserve(overrideCount);

    for (size_t faceIndex = 0; faceIndex < indoorGeometry.faces.size(); ++faceIndex)
    {
        const uint32_t effectiveAttributes = legacyMapDeltaData->faceAttributes[faceIndex];

        if (effectiveAttributes == indoorGeometry.faces[faceIndex].attributes)
        {
            continue;
        }

        Game::IndoorSceneFaceAttributeOverride overrideEntry = {};
        overrideEntry.faceIndex = faceIndex;
        overrideEntry.legacyAttributes = effectiveAttributes;
        sceneData.initialState.faceAttributeOverrides.push_back(std::move(overrideEntry));
    }
}

std::string displayPathForDocument(
    const std::filesystem::path &editorDevelopmentRoot,
    const std::filesystem::path &path)
{
    std::error_code relativeError;
    const std::filesystem::path relativePath = std::filesystem::relative(path, editorDevelopmentRoot, relativeError);

    if (!relativeError && !relativePath.empty() && !relativePath.native().starts_with(".."))
    {
        return relativePath.generic_string();
    }

    return path.generic_string();
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

std::string fileStemLowerCopy(const std::string &value)
{
    const std::filesystem::path path(value);
    const std::string stem = path.stem().string();
    return toLowerCopy(stem.empty() ? value : stem);
}

void buildBitmapTextureNames(const Engine::AssetFileSystem &assetFileSystem, std::vector<std::string> &textureNames)
{
    textureNames.clear();
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/bitmaps");

    for (const std::string &entry : entries)
    {
        const std::string lowerEntry = toLowerCopy(entry);

        if (!lowerEntry.ends_with(".bmp"))
        {
            continue;
        }

        const std::filesystem::path path(entry);
        const std::string stem = path.stem().string();

        if (!stem.empty())
        {
            textureNames.push_back(stem);
        }
    }

    std::sort(textureNames.begin(), textureNames.end(), [](const std::string &left, const std::string &right)
    {
        return toLowerCopy(left) < toLowerCopy(right);
    });
    textureNames.erase(
        std::unique(textureNames.begin(), textureNames.end(), [](const std::string &left, const std::string &right)
        {
            return toLowerCopy(left) == toLowerCopy(right);
        }),
        textureNames.end());
}

std::string canonicalBitmapTextureName(
    const std::vector<std::string> &bitmapTextureNames,
    const std::string &textureName)
{
    if (textureName.empty())
    {
        return {};
    }

    const std::string normalizedName = fileStemLowerCopy(trimCopy(textureName));

    if (normalizedName.empty())
    {
        return {};
    }

    for (const std::string &candidate : bitmapTextureNames)
    {
        if (toLowerCopy(candidate) == normalizedName)
        {
            return candidate;
        }
    }

    return normalizedName.substr(0, std::min<size_t>(normalizedName.size(), 10));
}

std::string resolveImportedMaterialTextureName(
    const std::vector<std::string> &bitmapTextureNames,
    const EditorBModelImportSource *pImportSource,
    const std::string &materialName)
{
    const std::string resolvedDefaultTexture =
        pImportSource != nullptr
        ? canonicalBitmapTextureName(bitmapTextureNames, pImportSource->defaultTextureName)
        : std::string();

    if (materialName.empty())
    {
        return resolvedDefaultTexture;
    }

    if (pImportSource != nullptr)
    {
        const std::string normalizedMaterialName = toLowerCopy(trimCopy(materialName));

        for (const EditorMaterialTextureRemap &remap : pImportSource->materialRemaps)
        {
            if (toLowerCopy(trimCopy(remap.sourceMaterialName)) == normalizedMaterialName)
            {
                const std::string remappedTextureName =
                    canonicalBitmapTextureName(bitmapTextureNames, remap.textureName);

                if (!remappedTextureName.empty())
                {
                    return remappedTextureName;
                }
            }
        }
    }

    const std::string canonicalMaterialTextureName = canonicalBitmapTextureName(bitmapTextureNames, materialName);

    if (!canonicalMaterialTextureName.empty())
    {
        return canonicalMaterialTextureName;
    }

    return resolvedDefaultTexture;
}

bool loadBitmapTextureSize(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &bitmapTextureNames,
    const std::string &textureName,
    int &width,
    int &height)
{
    const std::string canonicalName = canonicalBitmapTextureName(bitmapTextureNames, textureName);

    if (canonicalName.empty())
    {
        return false;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes =
        assetFileSystem.readBinaryFile("Data/bitmaps/" + canonicalName + ".bmp");

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return false;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        return false;
    }

    SDL_Surface *pSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pSurface == nullptr)
    {
        return false;
    }

    width = pSurface->w;
    height = pSurface->h;
    SDL_DestroySurface(pSurface);
    return width > 0 && height > 0;
}

uint8_t classifyImportedPolygonType(const ImportedModel &importedModel, const ImportedModelFace &face)
{
    if (face.vertices.size() < 3)
    {
        return 0;
    }

    const ImportedModelPosition &a = importedModel.positions[face.vertices[0].positionIndex];
    const ImportedModelPosition &b = importedModel.positions[face.vertices[1].positionIndex];
    const ImportedModelPosition &c = importedModel.positions[face.vertices[2].positionIndex];
    const float abX = b.x - a.x;
    const float abY = b.y - a.y;
    const float abZ = b.z - a.z;
    const float acX = c.x - a.x;
    const float acY = c.y - a.y;
    const float acZ = c.z - a.z;
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    const float normalLength = std::sqrt(normalX * normalX + normalY * normalY + normalZ * normalZ);

    if (normalLength <= 0.0001f)
    {
        return 0;
    }

    const float normalZNormalized = std::fabs(normalZ / normalLength);

    if (normalZNormalized >= 0.85f)
    {
        return 0x3;
    }

    if (normalZNormalized >= 0.45f)
    {
        return 0x4;
    }

    return 0;
}

float faceNormalZ(const std::vector<Game::OutdoorBModelVertex> &vertices, const Game::OutdoorBModelFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return 0.0f;
    }

    const Game::OutdoorBModelVertex &a = vertices[face.vertexIndices[0]];
    const Game::OutdoorBModelVertex &b = vertices[face.vertexIndices[1]];
    const Game::OutdoorBModelVertex &c = vertices[face.vertexIndices[2]];
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    return abX * acY - abY * acX;
}

float faceOutwardDot(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.size() < 3)
    {
        return 0.0f;
    }

    const Game::OutdoorBModelVertex &a = vertices[face.vertexIndices[0]];
    const Game::OutdoorBModelVertex &b = vertices[face.vertexIndices[1]];
    const Game::OutdoorBModelVertex &c = vertices[face.vertexIndices[2]];
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float abZ = static_cast<float>(b.z - a.z);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    const float acZ = static_cast<float>(c.z - a.z);
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;

    float faceCenterX = 0.0f;
    float faceCenterY = 0.0f;
    float faceCenterZ = 0.0f;

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size())
        {
            continue;
        }

        faceCenterX += static_cast<float>(vertices[vertexIndex].x);
        faceCenterY += static_cast<float>(vertices[vertexIndex].y);
        faceCenterZ += static_cast<float>(vertices[vertexIndex].z);
    }

    const float invVertexCount = 1.0f / static_cast<float>(face.vertexIndices.size());
    faceCenterX *= invVertexCount;
    faceCenterY *= invVertexCount;
    faceCenterZ *= invVertexCount;
    return normalX * (faceCenterX - modelCenterX)
        + normalY * (faceCenterY - modelCenterY)
        + normalZ * (faceCenterZ - modelCenterZ);
}

void reverseImportedFaceWinding(Game::OutdoorBModelFace &face)
{
    std::reverse(face.vertexIndices.begin(), face.vertexIndices.end());
    std::reverse(face.textureUs.begin(), face.textureUs.end());
    std::reverse(face.textureVs.begin(), face.textureVs.end());
}

void orientImportedFaceWinding(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.size() < 3)
    {
        return;
    }

    const bool shouldReverse = (face.polygonType == 0x3 || face.polygonType == 0x4)
        ? (faceNormalZ(vertices, face) < 0.0f)
        : (faceOutwardDot(vertices, face, modelCenterX, modelCenterY, modelCenterZ) < 0.0f);

    if (shouldReverse)
    {
        reverseImportedFaceWinding(face);
    }
}

void generateFallbackFaceTextureCoordinates(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    Game::OutdoorBModelFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return;
    }

    const Game::OutdoorBModelVertex &a = vertices[face.vertexIndices[0]];
    const Game::OutdoorBModelVertex &b = vertices[face.vertexIndices[1]];
    const Game::OutdoorBModelVertex &c = vertices[face.vertexIndices[2]];
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float abZ = static_cast<float>(b.z - a.z);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    const float acZ = static_cast<float>(c.z - a.z);
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    const float absNormalX = std::fabs(normalX);
    const float absNormalY = std::fabs(normalY);
    const float absNormalZ = std::fabs(normalZ);

    face.textureUs.clear();
    face.textureVs.clear();
    face.textureUs.reserve(face.vertexIndices.size());
    face.textureVs.reserve(face.vertexIndices.size());

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size())
        {
            face.textureUs.push_back(0);
            face.textureVs.push_back(0);
            continue;
        }

        const Game::OutdoorBModelVertex &vertex = vertices[vertexIndex];
        int16_t textureU = 0;
        int16_t textureV = 0;

        if (absNormalZ >= absNormalX && absNormalZ >= absNormalY)
        {
            textureU = static_cast<int16_t>(std::clamp(vertex.x, -32768, 32767));
            textureV = static_cast<int16_t>(std::clamp(-vertex.y, -32768, 32767));
        }
        else if (absNormalX >= absNormalY)
        {
            textureU = static_cast<int16_t>(std::clamp(vertex.y, -32768, 32767));
            textureV = static_cast<int16_t>(std::clamp(-vertex.z, -32768, 32767));
        }
        else
        {
            textureU = static_cast<int16_t>(std::clamp(vertex.x, -32768, 32767));
            textureV = static_cast<int16_t>(std::clamp(-vertex.z, -32768, 32767));
        }

        face.textureUs.push_back(textureU);
        face.textureVs.push_back(textureV);
    }
}

void recomputeBModelBounds(Game::OutdoorBModel &bmodel)
{
    if (bmodel.vertices.empty())
    {
        bmodel.positionX = 0;
        bmodel.positionY = 0;
        bmodel.positionZ = 0;
        bmodel.minX = 0;
        bmodel.minY = 0;
        bmodel.minZ = 0;
        bmodel.maxX = 0;
        bmodel.maxY = 0;
        bmodel.maxZ = 0;
        bmodel.boundingCenterX = 0;
        bmodel.boundingCenterY = 0;
        bmodel.boundingCenterZ = 0;
        bmodel.boundingRadius = 0;
        return;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    const float centerX = (minX + maxX) * 0.5f;
    const float centerY = (minY + maxY) * 0.5f;
    const float centerZ = (minZ + maxZ) * 0.5f;
    float maxRadiusSquared = 0.0f;

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        const float deltaX = static_cast<float>(vertex.x) - centerX;
        const float deltaY = static_cast<float>(vertex.y) - centerY;
        const float deltaZ = static_cast<float>(vertex.z) - centerZ;
        maxRadiusSquared = std::max(maxRadiusSquared, deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
    }

    bmodel.positionX = static_cast<int>(std::lround(centerX));
    bmodel.positionY = static_cast<int>(std::lround(centerY));
    bmodel.positionZ = static_cast<int>(std::lround(centerZ));
    bmodel.minX = static_cast<int>(std::floor(minX));
    bmodel.minY = static_cast<int>(std::floor(minY));
    bmodel.minZ = static_cast<int>(std::floor(minZ));
    bmodel.maxX = static_cast<int>(std::ceil(maxX));
    bmodel.maxY = static_cast<int>(std::ceil(maxY));
    bmodel.maxZ = static_cast<int>(std::ceil(maxZ));
    bmodel.boundingCenterX = static_cast<int>(std::lround(centerX));
    bmodel.boundingCenterY = static_cast<int>(std::lround(centerY));
    bmodel.boundingCenterZ = static_cast<int>(std::lround(centerZ));
    bmodel.boundingRadius = static_cast<int>(std::ceil(std::sqrt(maxRadiusSquared)));
}

Game::OutdoorBModelVertex transformImportedVertex(
    const EditorBModelSourceTransform &transform,
    float localX,
    float localY,
    float localZ)
{
    Game::OutdoorBModelVertex vertex = {};
    const float worldX =
        transform.originX
        + localX * transform.basisX[0]
        + localY * transform.basisY[0]
        + localZ * transform.basisZ[0];
    const float worldY =
        transform.originY
        + localX * transform.basisX[1]
        + localY * transform.basisY[1]
        + localZ * transform.basisZ[1];
    const float worldZ =
        transform.originZ
        + localX * transform.basisX[2]
        + localY * transform.basisY[2]
        + localZ * transform.basisZ[2];
    vertex.x = static_cast<int>(std::lround(worldX));
    vertex.y = static_cast<int>(std::lround(worldY));
    vertex.z = static_cast<int>(std::lround(worldZ));
    return vertex;
}

Game::OutdoorBModel buildImportedBModel(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &bitmapTextureNames,
    const ImportedModel &importedModel,
    const std::filesystem::path &sourcePath,
    float importScale,
    const EditorBModelImportSource &importSource,
    const std::optional<EditorBModelSourceTransform> &sourceTransform,
    std::string &errorMessage)
{
    Game::OutdoorBModel bmodel = {};
    bmodel.name = importedModel.name.empty() ? sourcePath.stem().string() : importedModel.name;
    bmodel.secondaryName = bmodel.name;

    if (importScale <= 0.0f)
    {
        errorMessage = "import scale must be greater than zero";
        return {};
    }

    std::vector<Game::OutdoorBModelVertex> importedVertices;
    importedVertices.reserve(importedModel.positions.size());
    float importedMinX = std::numeric_limits<float>::max();
    float importedMinY = std::numeric_limits<float>::max();
    float importedMinZ = std::numeric_limits<float>::max();
    float importedMaxX = std::numeric_limits<float>::lowest();
    float importedMaxY = std::numeric_limits<float>::lowest();
    float importedMaxZ = std::numeric_limits<float>::lowest();

    for (const ImportedModelPosition &position : importedModel.positions)
    {
        const float scaledX = position.x * importScale;
        const float scaledY = position.y * importScale;
        const float scaledZ = position.z * importScale;
        Game::OutdoorBModelVertex vertex = {};
        vertex.x = static_cast<int>(std::lround(scaledX));
        vertex.y = static_cast<int>(std::lround(scaledY));
        vertex.z = static_cast<int>(std::lround(scaledZ));
        importedVertices.push_back(vertex);
        importedMinX = std::min(importedMinX, static_cast<float>(vertex.x));
        importedMinY = std::min(importedMinY, static_cast<float>(vertex.y));
        importedMinZ = std::min(importedMinZ, static_cast<float>(vertex.z));
        importedMaxX = std::max(importedMaxX, static_cast<float>(vertex.x));
        importedMaxY = std::max(importedMaxY, static_cast<float>(vertex.y));
        importedMaxZ = std::max(importedMaxZ, static_cast<float>(vertex.z));
    }

    const float importedCenterX = (importedMinX + importedMaxX) * 0.5f;
    const float importedCenterY = (importedMinY + importedMaxY) * 0.5f;
    const float importedCenterZ = (importedMinZ + importedMaxZ) * 0.5f;
    EditorBModelSourceTransform resolvedTransform = {};
    resolvedTransform.originX = importedCenterX;
    resolvedTransform.originY = importedCenterY;
    resolvedTransform.originZ = importedCenterZ;

    if (sourceTransform)
    {
        resolvedTransform = *sourceTransform;
    }

    for (Game::OutdoorBModelVertex &vertex : importedVertices)
    {
        const float localX = static_cast<float>(vertex.x) - importedCenterX;
        const float localY = static_cast<float>(vertex.y) - importedCenterY;
        const float localZ = static_cast<float>(vertex.z) - importedCenterZ;
        vertex = transformImportedVertex(resolvedTransform, localX, localY, localZ);
    }

    bmodel.vertices = std::move(importedVertices);
    for (const ImportedModelFace &importedFace : importedModel.faces)
    {
        Game::OutdoorBModelFace face = {};
        face.attributes = 0;
        face.bitmapIndex = 0;
        face.textureDeltaU = 0;
        face.textureDeltaV = 0;
        face.cogNumber = 0;
        face.cogTriggeredNumber = 0;
        face.cogTrigger = 0;
        face.reserved = 0;
        face.polygonType = classifyImportedPolygonType(importedModel, importedFace);
        face.shade = 0;
        face.visibility = 31;
        face.textureName = resolveImportedMaterialTextureName(
            bitmapTextureNames,
            &importSource,
            importedFace.materialName);

        int textureWidth = 256;
        int textureHeight = 256;
        loadBitmapTextureSize(assetFileSystem, bitmapTextureNames, face.textureName, textureWidth, textureHeight);
        bool allVerticesHaveUv = true;
        bool hasVaryingUv = false;
        float firstU = 0.0f;
        float firstV = 0.0f;
        bool firstUvAssigned = false;

        for (const ImportedModelFaceVertex &importedVertex : importedFace.vertices)
        {
            face.vertexIndices.push_back(static_cast<uint16_t>(importedVertex.positionIndex));

            if (importedVertex.hasUv)
            {
                if (!firstUvAssigned)
                {
                    firstU = importedVertex.u;
                    firstV = importedVertex.v;
                    firstUvAssigned = true;
                }
                else if (std::fabs(importedVertex.u - firstU) > 0.0001f
                    || std::fabs(importedVertex.v - firstV) > 0.0001f)
                {
                    hasVaryingUv = true;
                }

                face.textureUs.push_back(
                    static_cast<int16_t>(std::clamp(
                        static_cast<int>(std::lround(importedVertex.u * static_cast<float>(textureWidth))),
                        -32768,
                        32767)));
                face.textureVs.push_back(
                    static_cast<int16_t>(std::clamp(
                        static_cast<int>(std::lround((1.0f - importedVertex.v) * static_cast<float>(textureHeight))),
                        -32768,
                        32767)));
            }
            else
            {
                allVerticesHaveUv = false;
                face.textureUs.push_back(0);
                face.textureVs.push_back(0);
            }
        }

        orientImportedFaceWinding(
            bmodel.vertices,
            face,
            resolvedTransform.originX,
            resolvedTransform.originY,
            resolvedTransform.originZ);

        if (!allVerticesHaveUv || !hasVaryingUv)
        {
            generateFallbackFaceTextureCoordinates(bmodel.vertices, face);
        }

        bmodel.faces.push_back(std::move(face));
    }

    recomputeBModelBounds(bmodel);
    return bmodel;
}

std::optional<Game::OutdoorMapData> buildOutdoorGeometryFromSourcePackage(
    const Engine::AssetFileSystem &assetFileSystem,
    const Game::OutdoorSceneData &sceneData,
    const std::optional<EditorOutdoorGeometryMetadata> &geometryMetadata,
    const std::optional<EditorOutdoorTerrainMetadata> &terrainMetadata,
    std::string &errorMessage)
{
    Game::OutdoorMapData outdoorGeometry = {};
    outdoorGeometry.version = 8;
    outdoorGeometry.name = sceneData.geometryFile;
    outdoorGeometry.fileName = sceneData.geometryFile;
    outdoorGeometry.skyTexture = sceneData.environment.skyTexture;
    outdoorGeometry.groundTilesetName = sceneData.environment.groundTilesetName;
    outdoorGeometry.masterTile = sceneData.environment.masterTile;
    outdoorGeometry.tileSetLookupIndices = sceneData.environment.tileSetLookupIndices;
    outdoorGeometry.heightMap.assign(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight, 0);
    outdoorGeometry.tileMap.assign(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight, 0);
    outdoorGeometry.attributeMap.assign(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight, 0);
    outdoorGeometry.decorationMap.assign(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight, 0);

    if (terrainMetadata)
    {
        if (terrainMetadata->heightMap.size() == outdoorGeometry.heightMap.size())
        {
            outdoorGeometry.heightMap = terrainMetadata->heightMap;
        }

        if (terrainMetadata->tileMap.size() == outdoorGeometry.tileMap.size())
        {
            outdoorGeometry.tileMap = terrainMetadata->tileMap;
        }

        if (terrainMetadata->attributeMap.size() == outdoorGeometry.attributeMap.size())
        {
            outdoorGeometry.attributeMap = terrainMetadata->attributeMap;
        }
    }

    std::vector<std::string> bitmapTextureNames;
    buildBitmapTextureNames(assetFileSystem, bitmapTextureNames);

    if (geometryMetadata)
    {
        size_t expectedIndex = 0;
        std::vector<EditorOutdoorGeometryMetadataEntry> entries = geometryMetadata->bmodels;
        std::sort(entries.begin(), entries.end(), [](const auto &left, const auto &right)
        {
            return left.runtimeBModelIndex < right.runtimeBModelIndex;
        });

        for (const EditorOutdoorGeometryMetadataEntry &entry : entries)
        {
            if (entry.runtimeBModelIndex != expectedIndex)
            {
                errorMessage = "source-only load cannot reconstruct missing bmodel slot "
                    + std::to_string(expectedIndex);
                return std::nullopt;
            }

            if (trimCopy(entry.importSource.sourcePath).empty())
            {
                errorMessage = "source-only load requires source-backed bmodels; missing source for bmodel "
                    + std::to_string(expectedIndex);
                return std::nullopt;
            }

            ImportedModel importedModel = {};
            const std::filesystem::path sourcePath = std::filesystem::absolute(entry.importSource.sourcePath);

            if (!loadImportedModelFromFile(
                    sourcePath,
                    importedModel,
                    errorMessage,
                    entry.importSource.sourceMeshName,
                    entry.importSource.mergeCoplanarFaces))
            {
                errorMessage = "could not rebuild bmodel " + std::to_string(expectedIndex) + ": " + errorMessage;
                return std::nullopt;
            }

            Game::OutdoorBModel bmodel = buildImportedBModel(
                assetFileSystem,
                bitmapTextureNames,
                importedModel,
                sourcePath,
                entry.importSource.importScale,
                entry.importSource,
                entry.sourceTransform,
                errorMessage);

            if (!errorMessage.empty() && bmodel.vertices.empty())
            {
                errorMessage = "could not rebuild bmodel " + std::to_string(expectedIndex) + ": " + errorMessage;
                return std::nullopt;
            }

            outdoorGeometry.bmodels.push_back(std::move(bmodel));
            ++expectedIndex;
        }
    }

    outdoorGeometry.bmodelCount = outdoorGeometry.bmodels.size();
    outdoorGeometry.entityCount = outdoorGeometry.entities.size();
    outdoorGeometry.idListCount = outdoorGeometry.decorationPidList.size();
    outdoorGeometry.spawnCount = outdoorGeometry.spawns.size();
    outdoorGeometry.uniqueTileCount = 1;

    if (!outdoorGeometry.heightMap.empty())
    {
        const auto [minIt, maxIt] = std::minmax_element(outdoorGeometry.heightMap.begin(), outdoorGeometry.heightMap.end());
        outdoorGeometry.minHeightSample = *minIt;
        outdoorGeometry.maxHeightSample = *maxIt;
    }

    return outdoorGeometry;
}

std::optional<std::vector<uint8_t>> compileOutdoorGeometryBytes(
    const Game::OutdoorMapData &outdoorMapData,
    const std::vector<uint8_t> &sourceBytes)
{
    Game::OutdoorMapDataWriter geometryWriter = {};

    if (!sourceBytes.empty())
    {
        const std::optional<std::vector<uint8_t>> patchedBytes = geometryWriter.patchBytes(outdoorMapData, sourceBytes);

        if (patchedBytes)
        {
            return patchedBytes;
        }
    }

    return geometryWriter.buildBytes(outdoorMapData);
}

std::filesystem::path resolveIndoorSourceAssetPath(
    const std::filesystem::path &developmentRoot,
    const std::filesystem::path &scenePhysicalPath,
    const EditorIndoorGeometryMetadata &metadata)
{
    const std::string sourceAssetPath = trimCopy(metadata.source.assetPath);

    if (sourceAssetPath.empty())
    {
        return {};
    }

    const std::filesystem::path sourcePath(sourceAssetPath);

    if (sourcePath.is_absolute())
    {
        return sourcePath;
    }

    if (!scenePhysicalPath.empty())
    {
        const std::filesystem::path sceneRelativePath = scenePhysicalPath.parent_path() / sourcePath;

        if (std::filesystem::exists(sceneRelativePath))
        {
            return sceneRelativePath;
        }
    }

    return developmentRoot / sourcePath;
}

bool compileIndoorSourceGeometryBytes(
    const std::filesystem::path &developmentRoot,
    const std::filesystem::path &scenePhysicalPath,
    const EditorIndoorGeometryMetadata &metadata,
    const Game::IndoorSceneData &sceneData,
    Game::IndoorMapData &compiledGeometry,
    std::vector<uint8_t> &compiledBytes,
    std::string &errorMessage)
{
    const std::filesystem::path sourcePath = resolveIndoorSourceAssetPath(developmentRoot, scenePhysicalPath, metadata);

    if (sourcePath.empty() || !std::filesystem::exists(sourcePath))
    {
        return false;
    }

    IndoorSourceGeometryCompileResult compileResult = {};

    if (!compileIndoorSourceGeometry(sourcePath, metadata, compileResult, errorMessage))
    {
        errorMessage = "could not compile indoor source geometry: " + errorMessage;
        return false;
    }

    Game::MapDeltaData ignoredMapDeltaData = {};
    compiledGeometry = std::move(compileResult.indoorGeometry);
    Game::IndoorSceneData compiledSceneData = sceneData;

    if (!compileResult.generatedDoors.empty())
    {
        std::unordered_set<size_t> doorIndices;

        for (const Game::IndoorSceneDoor &door : compiledSceneData.initialState.doors)
        {
            doorIndices.insert(door.doorIndex);
        }

        for (const Game::IndoorSceneDoor &generatedDoor : compileResult.generatedDoors)
        {
            if (!doorIndices.insert(generatedDoor.doorIndex).second)
            {
                errorMessage = "source-generated indoor mechanism conflicts with an authored scene door index";
                return false;
            }

            compiledSceneData.initialState.doors.push_back(generatedDoor);
        }
    }

    if (!Game::buildIndoorMapStateFromScene(compiledSceneData, compiledGeometry, ignoredMapDeltaData, errorMessage))
    {
        errorMessage = "could not apply indoor scene to compiled source geometry: " + errorMessage;
        return false;
    }

    Game::IndoorMapDataWriter writer = {};
    const std::optional<std::vector<uint8_t>> bytes = writer.buildBytes(compiledGeometry);

    if (!bytes)
    {
        errorMessage = "could not serialize compiled indoor source geometry";
        return false;
    }

    compiledBytes = *bytes;
    return true;
}

std::string deriveDefaultScriptModuleForMapFile(const std::string &mapFileName)
{
    const std::string stem = std::filesystem::path(mapFileName).stem().string();
    return "Data/scripts/maps/" + toLowerCopy(stem) + ".lua";
}

void emitPositionMap(YAML::Emitter &emitter, int x, int y, int z)
{
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "x" << YAML::Value << x;
    emitter << YAML::Key << "y" << YAML::Value << y;
    emitter << YAML::Key << "z" << YAML::Value << z;
    emitter << YAML::EndMap;
}

template <typename ValueType>
void emitSequence(YAML::Emitter &emitter, const std::vector<ValueType> &values)
{
    emitter << YAML::Flow << YAML::BeginSeq;

    for (const ValueType &value : values)
    {
        emitter << value;
    }

    emitter << YAML::EndSeq;
}

template <typename ValueType, size_t Count>
void emitSequence(YAML::Emitter &emitter, const std::array<ValueType, Count> &values)
{
    emitter << YAML::Flow << YAML::BeginSeq;

    for (const ValueType &value : values)
    {
        emitter << value;
    }

    emitter << YAML::EndSeq;
}

template <typename ValueType, size_t Count>
void emitIntegerSequence(YAML::Emitter &emitter, const std::array<ValueType, Count> &values)
{
    emitter << YAML::Flow << YAML::BeginSeq;

    for (const ValueType &value : values)
    {
        emitter << static_cast<int>(value);
    }

    emitter << YAML::EndSeq;
}

std::vector<std::string> splitTabSeparatedLine(const std::string &line)
{
    std::vector<std::string> columns;
    size_t start = 0;

    while (start <= line.size())
    {
        const size_t separator = line.find('\t', start);

        if (separator == std::string::npos)
        {
            columns.push_back(line.substr(start));
            break;
        }

        columns.push_back(line.substr(start, separator - start));
        start = separator + 1;
    }

    return columns;
}

std::string joinTabSeparatedRow(const std::vector<std::string> &row)
{
    std::ostringstream stream;

    for (size_t index = 0; index < row.size(); ++index)
    {
        if (index != 0)
        {
            stream << '\t';
        }

        stream << row[index];
    }

    return stream.str();
}

bool readTabSeparatedRows(
    const std::filesystem::path &path,
    std::vector<std::vector<std::string>> &rows,
    std::string &errorMessage)
{
    std::ifstream stream(path);

    if (!stream)
    {
        errorMessage = "could not open " + path.string();
        return false;
    }

    rows.clear();
    std::string line;

    while (std::getline(stream, line))
    {
        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        rows.push_back(splitTabSeparatedLine(line));
    }

    return true;
}

std::string serializeTabSeparatedRows(const std::vector<std::vector<std::string>> &rows)
{
    std::ostringstream stream;

    for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
    {
        stream << joinTabSeparatedRow(rows[rowIndex]);

        if (rowIndex + 1 < rows.size())
        {
            stream << '\n';
        }
    }

    return stream.str();
}

bool isCommentOrHeaderRow(const std::vector<std::string> &row)
{
    for (const std::string &cell : row)
    {
        const std::string trimmed = trimCopy(cell);

        if (trimmed.empty())
        {
            continue;
        }

        return trimmed.starts_with('#') || trimmed.starts_with('/');
    }

    return true;
}

bool parseIntegerLoose(const std::string &value, int &result)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        result = 0;
        return true;
    }

    size_t processedCharacters = 0;

    try
    {
        result = std::stoi(trimmed, &processedCharacters);
    }
    catch (...)
    {
        return false;
    }

    return processedCharacters == trimmed.size();
}

int nextAvailableMapStatsId(const std::filesystem::path &mapStatsPath)
{
    std::vector<std::vector<std::string>> rows;
    std::string errorMessage;

    if (!readTabSeparatedRows(mapStatsPath, rows, errorMessage))
    {
        return 1000;
    }

    int maxId = 0;

    for (const std::vector<std::string> &row : rows)
    {
        if (row.empty() || isCommentOrHeaderRow(row))
        {
            continue;
        }

        int rowId = 0;

        if (parseIntegerLoose(row[0], rowId))
        {
            maxId = std::max(maxId, rowId);
        }
    }

    return std::max(1, maxId + 1);
}

std::vector<std::string> buildMapStatsRow(const EditorOutdoorMapPackageMetadata &metadata)
{
    std::vector<std::string> row(34, "0");
    row[0] = std::to_string(std::max(1, metadata.mapStatsId));
    row[1] = metadata.displayName;
    row[2] = metadata.mapFileName;
    row[3] = "0";
    row[4] = "0";
    row[5] = "0";
    row[6] = "672";
    row[7] = "0";
    row[8] = "1";
    row[9] = "0";
    row[10] = "0";
    row[11] = "0";
    row[12] = std::to_string(DefaultOutdoorEncounterChance);
    row[13] = "0";
    row[14] = "0";
    row[15] = "0";
    row[16] = "0";
    row[17] = "0";
    row[18] = "0";
    row[19] = "0";
    row[20] = "0";
    row[21] = "0";
    row[22] = "0";
    row[23] = "0";
    row[24] = "0";
    row[25] = "0";
    row[26] = "0";
    row[27] = "0";
    row[28] = std::to_string(std::max(0, metadata.redbookTrack));
    row[29] = metadata.environmentName;
    row[30] = "0";
    row[31] = std::string();
    row[32] = "0";
    row[33] = metadata.isTopLevelArea ? "x" : std::string();
    return row;
}

void applyNavigationTransitionToRow(
    std::vector<std::string> &row,
    size_t mapColumn,
    size_t travelDaysColumn,
    size_t headingColumn,
    size_t arrivalXColumn,
    size_t arrivalYColumn,
    size_t arrivalZColumn,
    const std::optional<Game::MapEdgeTransition> &transition)
{
    if (!transition.has_value())
    {
        row[mapColumn] = "0";
        row[travelDaysColumn] = "0";
        row[headingColumn] = "0";
        row[arrivalXColumn].clear();
        row[arrivalYColumn].clear();
        row[arrivalZColumn].clear();
        return;
    }

    row[mapColumn] = transition->destinationMapFileName;
    row[travelDaysColumn] = std::to_string(std::max(0, transition->travelDays));
    row[headingColumn] = transition->directionDegrees.has_value() ? std::to_string(*transition->directionDegrees) : "0";

    if (transition->useMapStartPosition
        || !transition->arrivalX.has_value()
        || !transition->arrivalY.has_value()
        || !transition->arrivalZ.has_value())
    {
        row[arrivalXColumn].clear();
        row[arrivalYColumn].clear();
        row[arrivalZColumn].clear();
        return;
    }

    row[arrivalXColumn] = std::to_string(*transition->arrivalX);
    row[arrivalYColumn] = std::to_string(*transition->arrivalY);
    row[arrivalZColumn] = std::to_string(*transition->arrivalZ);
}

std::vector<std::string> buildMapNavigationRow(const EditorOutdoorMapPackageMetadata &metadata)
{
    std::vector<std::string> row(29, "0");
    row[0] = metadata.mapFileName;
    row[1] = std::to_string(metadata.outdoorBounds.minX);
    row[2] = std::to_string(metadata.outdoorBounds.maxX);
    row[3] = std::to_string(metadata.outdoorBounds.minY);
    row[4] = std::to_string(metadata.outdoorBounds.maxY);

    applyNavigationTransitionToRow(row, 5, 6, 7, 17, 18, 19, metadata.northTransition);
    applyNavigationTransitionToRow(row, 8, 9, 10, 20, 21, 22, metadata.southTransition);
    applyNavigationTransitionToRow(row, 11, 12, 13, 23, 24, 25, metadata.eastTransition);
    applyNavigationTransitionToRow(row, 14, 15, 16, 26, 27, 28, metadata.westTransition);
    return row;
}

void upsertTableRowByKey(
    std::vector<std::vector<std::string>> &rows,
    size_t keyColumn,
    const std::string &key,
    const std::vector<std::string> &replacementRow)
{
    const std::string normalizedKey = toLowerCopy(trimCopy(key));

    for (std::vector<std::string> &row : rows)
    {
        if (row.size() <= keyColumn || isCommentOrHeaderRow(row))
        {
            continue;
        }

        if (toLowerCopy(trimCopy(row[keyColumn])) == normalizedKey)
        {
            row = replacementRow;
            return;
        }
    }

    rows.push_back(replacementRow);
}

std::string escapeLuaStringLiteral(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        if (character == '\\' || character == '"')
        {
            result.push_back('\\');
        }

        result.push_back(character);
    }

    return result;
}

std::string buildOutdoorMapScriptStub(const EditorOutdoorMapPackageMetadata &metadata)
{
    std::ostringstream stream;
    stream << "-- Source-generated map script stub for " << metadata.mapFileName << "\n";
    stream << "SetMapMetadata({\n";
    stream << "    name = \"" << escapeLuaStringLiteral(metadata.displayName) << "\",\n";
    stream << "    onLoad = {}\n";
    stream << "})\n";
    return stream.str();
}

Game::OutdoorSceneEntity buildDefaultPartyStartSceneEntity()
{
    Game::OutdoorSceneEntity entity = {};
    entity.entityIndex = 0;
    entity.entity.name = std::string(PartyStartEntityName);
    entity.entity.x = 0;
    entity.entity.y = 0;
    entity.entity.z = 0;
    entity.entity.facing = 0;
    return entity;
}
}

bool EditorDocument::loadOutdoorMapPackage(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    std::string &errorMessage)
{
    const std::string packageVirtualPath = "Data/games/" + replaceExtension(mapFileName, ".map.yml");

    if (assetFileSystem.exists(packageVirtualPath))
    {
        const std::optional<std::string> packageText = assetFileSystem.readTextFile(packageVirtualPath);

        if (!packageText)
        {
            errorMessage = "could not read map package root: " + packageVirtualPath;
            return false;
        }

        const std::optional<EditorOutdoorMapPackageMetadata> packageMetadata =
            loadOutdoorMapPackageMetadataFromText(*packageText, errorMessage);

        if (!packageMetadata)
        {
            errorMessage = "could not parse map package root " + packageVirtualPath + ": " + errorMessage;
            return false;
        }

        const std::string sceneVirtualPath =
            (std::filesystem::path(packageVirtualPath).parent_path() / packageMetadata->sceneFile).generic_string();
        const std::optional<std::string> sceneText = assetFileSystem.readTextFile(sceneVirtualPath);

        if (!sceneText)
        {
            errorMessage = "could not read scene text: " + sceneVirtualPath;
            return false;
        }

        return loadOutdoorSceneText(
            assetFileSystem,
            sceneVirtualPath,
            *sceneText,
            *packageMetadata,
            packageVirtualPath,
            errorMessage);
    }

    const std::string sceneVirtualPath = "Data/games/" + replaceExtension(mapFileName, ".scene.yml");

    if (!assetFileSystem.exists(sceneVirtualPath))
    {
        errorMessage = "could not find scene supplement for " + mapFileName;
        return false;
    }

    return loadOutdoorSceneVirtualPath(assetFileSystem, sceneVirtualPath, errorMessage);
}

bool EditorDocument::loadOutdoorSceneVirtualPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneVirtualPath,
    std::string &errorMessage)
{
    const std::optional<std::string> sceneText = assetFileSystem.readTextFile(sceneVirtualPath);

    if (!sceneText)
    {
        errorMessage = "could not read scene text: " + sceneVirtualPath;
        return false;
    }

    return loadOutdoorSceneText(assetFileSystem, sceneVirtualPath, *sceneText, std::nullopt, std::nullopt, errorMessage);
}

bool EditorDocument::loadIndoorMapPackage(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    std::string &errorMessage)
{
    const std::string sceneVirtualPath = "Data/games/" + replaceExtension(mapFileName, ".scene.yml");

    if (!assetFileSystem.exists(sceneVirtualPath))
    {
        errorMessage = "could not find scene supplement for " + mapFileName;
        return false;
    }

    return loadIndoorSceneVirtualPath(assetFileSystem, sceneVirtualPath, errorMessage);
}

bool EditorDocument::loadIndoorSceneVirtualPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneVirtualPath,
    std::string &errorMessage)
{
    const std::optional<std::string> sceneText = assetFileSystem.readTextFile(sceneVirtualPath);

    if (!sceneText)
    {
        errorMessage = "could not read scene text: " + sceneVirtualPath;
        return false;
    }

    return loadIndoorSceneText(assetFileSystem, sceneVirtualPath, *sceneText, errorMessage);
}

bool EditorDocument::loadMapPhysicalPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::filesystem::path &path,
    std::string &errorMessage)
{
    const std::filesystem::path normalizedPath = std::filesystem::absolute(path);
    const std::string fileNameLower = toLowerCopy(normalizedPath.filename().string());
    const std::string extensionLower = toLowerCopy(normalizedPath.extension().string());

    if (extensionLower == ".odm")
    {
        const std::filesystem::path packagePath =
            normalizedPath.parent_path() / std::filesystem::path(normalizedPath.stem().string() + ".map.yml");
        const std::filesystem::path scenePath =
            normalizedPath.parent_path() / std::filesystem::path(normalizedPath.stem().string() + ".scene.yml");

        if (std::filesystem::exists(packagePath))
        {
            return loadMapPhysicalPath(assetFileSystem, packagePath, errorMessage);
        }

        if (std::filesystem::exists(scenePath))
        {
            return loadMapPhysicalPath(assetFileSystem, scenePath, errorMessage);
        }

        errorMessage = "could not find scene supplement for " + normalizedPath.string();
        return false;
    }

    if (extensionLower == ".blv")
    {
        const std::filesystem::path scenePath =
            normalizedPath.parent_path() / std::filesystem::path(normalizedPath.stem().string() + ".scene.yml");

        if (!std::filesystem::exists(scenePath))
        {
            errorMessage = "could not find scene supplement for " + normalizedPath.string();
            return false;
        }

        return loadMapPhysicalPath(assetFileSystem, scenePath, errorMessage);
    }

    if (fileNameLower.ends_with(".map.yml"))
    {
        std::string packageText;

        if (!readTextFile(normalizedPath, packageText))
        {
            errorMessage = "could not read map package root: " + normalizedPath.string();
            return false;
        }

        const std::optional<EditorOutdoorMapPackageMetadata> packageMetadata =
            loadOutdoorMapPackageMetadataFromText(packageText, errorMessage);

        if (!packageMetadata)
        {
            errorMessage = "could not parse map package root " + normalizedPath.string() + ": " + errorMessage;
            return false;
        }

        const std::filesystem::path scenePath = normalizedPath.parent_path() / packageMetadata->sceneFile;
        std::string sceneText;

        if (!readTextFile(scenePath, sceneText))
        {
            errorMessage = "could not read scene text: " + scenePath.string();
            return false;
        }

        return loadOutdoorScenePhysicalPath(
            assetFileSystem,
            scenePath,
            sceneText,
            *packageMetadata,
            normalizedPath,
            errorMessage);
    }

    if (fileNameLower.ends_with(".scene.yml"))
    {
        std::string sceneText;

        if (!readTextFile(normalizedPath, sceneText))
        {
            errorMessage = "could not read scene text: " + normalizedPath.string();
            return false;
        }

        YAML::Node root;

        try
        {
            root = YAML::Load(sceneText);
        }
        catch (const YAML::Exception &exception)
        {
            errorMessage = "could not parse scene text: " + std::string(exception.what());
            return false;
        }

        const std::string kind = root["kind"].as<std::string>(std::string());
        const std::string geometryFile =
            root["source"] ? root["source"]["geometry_file"].as<std::string>(std::string()) : std::string();
        const std::string geometryExtension = toLowerCopy(std::filesystem::path(geometryFile).extension().string());

        if (kind == "indoor_scene" || geometryExtension == ".blv")
        {
            return loadIndoorScenePhysicalPath(assetFileSystem, normalizedPath, sceneText, errorMessage);
        }

        if (kind == "outdoor_scene" || geometryExtension == ".odm")
        {
            return loadOutdoorScenePhysicalPath(assetFileSystem, normalizedPath, sceneText, std::nullopt, std::nullopt, errorMessage);
        }

        errorMessage = "could not determine map kind for scene " + normalizedPath.string();
        return false;
    }

    errorMessage = "unsupported map path: " + normalizedPath.string();
    return false;
}

bool EditorDocument::createNewOutdoorMapPackage(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    const std::string &displayName,
    const Game::OutdoorSceneEnvironment &environment,
    std::string &errorMessage)
{
    const std::string trimmedMapFileName = trimCopy(mapFileName);

    if (trimmedMapFileName.empty() || std::filesystem::path(trimmedMapFileName).extension() != ".odm")
    {
        errorMessage = "new outdoor map file name must end with .odm";
        return false;
    }

    const std::string sceneVirtualPath = "Data/games/" + replaceExtension(trimmedMapFileName, ".scene.yml");
    const std::string mapVirtualPath = "Data/games/" + trimmedMapFileName;
    const std::string packageVirtualPath = "Data/games/" + replaceExtension(trimmedMapFileName, ".map.yml");
    const std::string geometryMetadataVirtualPath = "Data/games/" + replaceExtension(trimmedMapFileName, ".geometry.yml");
    const std::string terrainMetadataVirtualPath = "Data/games/" + replaceExtension(trimmedMapFileName, ".terrain.yml");
    const std::filesystem::path mapStatsRelativePath = std::filesystem::path("Data") / "data_tables" / "map_stats.txt";
    const std::filesystem::path mapStatsPath = assetFileSystem.getEditorDevelopmentRoot() / mapStatsRelativePath;

    if (assetFileSystem.exists(sceneVirtualPath)
        || assetFileSystem.exists(mapVirtualPath)
        || assetFileSystem.exists(packageVirtualPath)
        || assetFileSystem.exists(geometryMetadataVirtualPath)
        || assetFileSystem.exists(terrainMetadataVirtualPath))
    {
        errorMessage = "target map files already exist for " + trimmedMapFileName;
        return false;
    }

    m_kind = Kind::Outdoor;
    m_isDirty = true;
    m_isRuntimeBuildDirty = true;
    m_developmentRoot = assetFileSystem.getDevelopmentRoot();
    m_editorDevelopmentRoot = assetFileSystem.getEditorDevelopmentRoot();
    m_outdoorGeometry = {};
    m_outdoorGeometry.version = 8;
    m_outdoorGeometrySourceBytes.clear();
    m_indoorGeometry = {};
    m_indoorSceneData = {};
    m_indoorGeometrySourceBytes.clear();
    m_hasIndoorGeometryMetadata = false;
    m_indoorGeometryMetadata = {};
    m_outdoorSceneData = {};
    m_outdoorGeometryMetadata = {};
    m_outdoorMapPackageMetadata = {};
    m_outdoorTerrainMetadata = {};
    ++m_sceneRevision;
    m_displayName = trimmedMapFileName;
    m_hasMapPackageRoot = false;
    m_sceneVirtualPath.clear();
    m_geometryVirtualPath.clear();
    m_geometryMetadataVirtualPath.clear();
    m_mapPackageVirtualPath.clear();
    m_terrainMetadataVirtualPath.clear();
    m_scenePhysicalPath.clear();
    m_geometryPhysicalPath.clear();
    m_geometryMetadataPhysicalPath.clear();
    m_mapPackagePhysicalPath.clear();
    m_terrainMetadataPhysicalPath.clear();

    if (!ensureOverlaySeedTextFile(m_developmentRoot, m_editorDevelopmentRoot, mapStatsRelativePath, errorMessage))
    {
        return false;
    }

    m_outdoorGeometry.fileName = trimmedMapFileName;
    m_outdoorGeometry.name = displayName;
    m_outdoorGeometry.description.clear();
    m_outdoorGeometry.skyTexture = environment.skyTexture;
    m_outdoorGeometry.groundTilesetName = environment.groundTilesetName;
    m_outdoorGeometry.masterTile = environment.masterTile;
    m_outdoorGeometry.tileSetLookupIndices = environment.tileSetLookupIndices;
    m_outdoorGeometry.bmodels.clear();
    m_outdoorGeometry.entities.clear();
    m_outdoorGeometry.decorationPidList.clear();
    m_outdoorGeometry.spawns.clear();
    m_outdoorGeometry.decorationMap.assign(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight, 0);
    m_outdoorGeometry.heightMap.assign(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight, 0);
    m_outdoorGeometry.tileMap.assign(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight, 90);
    m_outdoorGeometry.attributeMap.assign(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight, 0);
    m_outdoorGeometry.bmodelCount = 0;
    m_outdoorGeometry.entityCount = 0;
    m_outdoorGeometry.idListCount = 0;
    m_outdoorGeometry.spawnCount = 0;
    m_outdoorGeometry.minHeightSample = 0;
    m_outdoorGeometry.maxHeightSample = 0;
    m_outdoorGeometry.uniqueTileCount = 1;
    m_outdoorGeometry.terrainNormalCount = 0;
    m_outdoorGeometry.someOtherMap.clear();
    m_outdoorGeometry.normalMap.clear();
    m_outdoorGeometry.normals.clear();

    m_outdoorSceneData.formatVersion = 1;
    m_outdoorSceneData.geometryFile = trimmedMapFileName;
    m_outdoorSceneData.legacyCompanionFile.reset();
    m_outdoorSceneData.environment = environment;
    m_outdoorSceneData.terrainAttributeOverrides.clear();
    m_outdoorSceneData.interactiveFaces.clear();
    m_outdoorSceneData.entities.clear();
    m_outdoorSceneData.entities.push_back(buildDefaultPartyStartSceneEntity());
    m_outdoorSceneData.spawns.clear();
    m_outdoorSceneData.initialState = {};
    m_outdoorMapPackageMetadata.packageId = deriveOutdoorMapPackageId(trimmedMapFileName);
    m_outdoorMapPackageMetadata.displayName = displayName;
    m_outdoorMapPackageMetadata.mapFileName = trimmedMapFileName;
    m_outdoorMapPackageMetadata.scriptModule = deriveDefaultScriptModuleForMapFile(trimmedMapFileName);
    m_outdoorMapPackageMetadata.mapStatsId = nextAvailableMapStatsId(mapStatsPath);
    m_outdoorMapPackageMetadata.redbookTrack = DefaultOutdoorRedbookTrack;
    m_outdoorMapPackageMetadata.environmentName = "FOREST";
    m_outdoorMapPackageMetadata.isTopLevelArea = true;
    m_outdoorMapPackageMetadata.outdoorBounds.enabled = true;
    m_outdoorMapPackageMetadata.outdoorBounds.minX = -DefaultOutdoorBoundsExtent;
    m_outdoorMapPackageMetadata.outdoorBounds.maxX = DefaultOutdoorBoundsExtent;
    m_outdoorMapPackageMetadata.outdoorBounds.minY = -DefaultOutdoorBoundsExtent;
    m_outdoorMapPackageMetadata.outdoorBounds.maxY = DefaultOutdoorBoundsExtent;

    synchronizeOutdoorGeometryMetadata();
    synchronizeOutdoorTerrainMetadata();

    const std::filesystem::path targetScenePath =
        assetFileSystem.getEditorDevelopmentRoot() / "Data" / "games" / replaceExtension(trimmedMapFileName, ".scene.yml");

    return saveAs(targetScenePath, errorMessage);
}

bool EditorDocument::saveSource(std::string &errorMessage)
{
    if (m_kind != Kind::Outdoor && m_kind != Kind::Indoor)
    {
        errorMessage = "no editable document is loaded";
        return false;
    }

    if (m_scenePhysicalPath.empty())
    {
        errorMessage = "document has no save path";
        return false;
    }

    return saveSourceAs(m_scenePhysicalPath, errorMessage);
}

bool EditorDocument::saveSourceAs(const std::filesystem::path &scenePhysicalPath, std::string &errorMessage)
{
    if (m_kind == Kind::Indoor)
    {
        if (m_editorDevelopmentRoot.empty())
        {
            errorMessage = "document save root is not initialized";
            return false;
        }

        if (m_indoorSceneData.geometryFile.empty())
        {
            errorMessage = "document geometry save path is not initialized";
            return false;
        }

        const std::string targetGeometryFileName = deriveGeometryFileNameForScenePath(
            scenePhysicalPath,
            m_indoorSceneData.geometryFile);
        const std::filesystem::path targetGeometryPath = scenePhysicalPath.parent_path() / targetGeometryFileName;
        const std::filesystem::path targetGeometryMetadataPath =
            deriveGeometryMetadataPathForScenePath(scenePhysicalPath);
        const std::string yamlText = serializeIndoorScene(m_indoorSceneData, targetGeometryFileName);
        Game::IndoorMapDataWriter geometryWriter = {};
        const std::optional<std::vector<uint8_t>> geometryBytes = geometryWriter.buildBytes(m_indoorGeometry);

        if (!geometryBytes)
        {
            errorMessage = "could not serialize indoor geometry";
            return false;
        }

        if (!writeTextFileAtomically(scenePhysicalPath, yamlText, errorMessage))
        {
            return false;
        }

        if (!m_hasIndoorGeometryMetadata
            && !writeBinaryFileAtomically(targetGeometryPath, *geometryBytes, errorMessage))
        {
            return false;
        }

        if (m_hasIndoorGeometryMetadata || !isIndoorGeometryMetadataEmpty(m_indoorGeometryMetadata))
        {
            m_hasIndoorGeometryMetadata = true;
            normalizeIndoorGeometryMetadata(m_indoorGeometryMetadata, targetGeometryFileName);

            if (!writeTextFileAtomically(
                    targetGeometryMetadataPath,
                    serializeIndoorGeometryMetadata(m_indoorGeometryMetadata),
                    errorMessage))
            {
                return false;
            }
        }

        m_scenePhysicalPath = scenePhysicalPath;
        m_sceneVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, scenePhysicalPath);
        m_geometryPhysicalPath = targetGeometryPath;
        m_geometryVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, targetGeometryPath);
        m_geometryMetadataPhysicalPath =
            m_hasIndoorGeometryMetadata ? targetGeometryMetadataPath : std::filesystem::path();
        m_geometryMetadataVirtualPath =
            m_hasIndoorGeometryMetadata
                ? sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, targetGeometryMetadataPath)
                : std::string();
        if (!m_hasIndoorGeometryMetadata)
        {
            m_indoorGeometrySourceBytes = *geometryBytes;
        }
        m_mapPackagePhysicalPath.clear();
        m_mapPackageVirtualPath.clear();
        m_terrainMetadataPhysicalPath.clear();
        m_terrainMetadataVirtualPath.clear();
        m_hasMapPackageRoot = false;
        m_displayName = targetGeometryFileName;
        m_isRuntimeBuildDirty = false;
        m_isDirty = false;
        return true;
    }

    if (m_kind != Kind::Outdoor)
    {
        errorMessage = "no editable document is loaded";
        return false;
    }

    if (m_editorDevelopmentRoot.empty())
    {
        errorMessage = "document save root is not initialized";
        return false;
    }

    if (m_outdoorSceneData.geometryFile.empty())
    {
        errorMessage = "document geometry save path is not initialized";
        return false;
    }

    const std::string targetGeometryFileName = deriveGeometryFileNameForScenePath(
        scenePhysicalPath,
        m_outdoorSceneData.geometryFile);
    const std::filesystem::path targetGeometryPath = scenePhysicalPath.parent_path() / targetGeometryFileName;
    const std::filesystem::path targetGeometryMetadataPath = deriveGeometryMetadataPathForScenePath(scenePhysicalPath);
    const std::filesystem::path targetMapPackagePath = deriveMapPackagePathForScenePath(scenePhysicalPath);
    const std::filesystem::path targetTerrainMetadataPath = deriveTerrainMetadataPathForScenePath(scenePhysicalPath);
    const std::filesystem::path mapStatsRelativePath = std::filesystem::path("Data") / "data_tables" / "map_stats.txt";
    const std::filesystem::path mapStatsPath = m_editorDevelopmentRoot / mapStatsRelativePath;

    if (!ensureOverlaySeedTextFile(m_developmentRoot, m_editorDevelopmentRoot, mapStatsRelativePath, errorMessage))
    {
        return false;
    }

    const std::string yamlText = serializeOutdoorScene(m_outdoorSceneData, targetGeometryFileName);
    synchronizeOutdoorGeometryMetadata();
    synchronizeOutdoorTerrainMetadata();
    m_outdoorGeometryMetadata.mapFileName = targetGeometryFileName;
    m_outdoorTerrainMetadata.mapFileName = targetGeometryFileName;
    const std::string geometryMetadataText = serializeOutdoorGeometryMetadata(m_outdoorGeometryMetadata);
    const std::string terrainMetadataText = serializeOutdoorTerrainMetadata(m_outdoorTerrainMetadata);
    EditorOutdoorMapPackageMetadata packageMetadata = m_outdoorMapPackageMetadata;
    normalizeOutdoorMapPackageMetadata(
        packageMetadata,
        deriveOutdoorMapPackageId(targetGeometryFileName),
        deriveOutdoorMapPackageDisplayName(targetGeometryFileName),
        targetGeometryFileName,
        scenePhysicalPath.filename().string(),
        targetGeometryMetadataPath.filename().string(),
        targetTerrainMetadataPath.filename().string(),
        deriveDefaultScriptModuleForMapFile(targetGeometryFileName),
        std::string(),
        packageMetadata.builtSourceFingerprint);
    packageMetadata.mapFileName = targetGeometryFileName;
    packageMetadata.sceneFile = scenePhysicalPath.filename().string();
    packageMetadata.geometryMetadataFile = targetGeometryMetadataPath.filename().string();
    packageMetadata.terrainMetadataFile = targetTerrainMetadataPath.filename().string();

    const bool savePathChanged = targetMapPackagePath != m_mapPackagePhysicalPath;

    if (savePathChanged || toLowerCopy(m_outdoorMapPackageMetadata.mapFileName) != toLowerCopy(targetGeometryFileName))
    {
        packageMetadata.mapStatsId = nextAvailableMapStatsId(mapStatsPath);
    }

    const std::string sourceFingerprint =
        currentSourcePackageFingerprintForTexts(yamlText, geometryMetadataText, terrainMetadataText, packageMetadata);

    if (savePathChanged)
    {
        packageMetadata.builtSourceFingerprint.clear();
    }
    else if (!m_isRuntimeBuildDirty)
    {
        packageMetadata.builtSourceFingerprint = sourceFingerprint;
    }

    packageMetadata.sourceFingerprint = sourceFingerprint;
    const std::string packageMetadataText = serializeOutdoorMapPackageMetadata(packageMetadata);

    if (!writeTextFileAtomically(targetGeometryMetadataPath, geometryMetadataText, errorMessage))
    {
        return false;
    }

    if (!writeTextFileAtomically(targetTerrainMetadataPath, terrainMetadataText, errorMessage))
    {
        return false;
    }

    if (!writeTextFileAtomically(targetMapPackagePath, packageMetadataText, errorMessage))
    {
        return false;
    }

    if (!packageMetadata.scriptModule.empty())
    {
        const std::filesystem::path scriptModulePath =
            m_editorDevelopmentRoot / std::filesystem::path(packageMetadata.scriptModule);

        if (!std::filesystem::exists(scriptModulePath))
        {
            std::error_code createDirectoriesError;
            std::filesystem::create_directories(scriptModulePath.parent_path(), createDirectoriesError);

            if (createDirectoriesError)
            {
                errorMessage = "could not create script directory " + scriptModulePath.parent_path().string()
                    + ": " + createDirectoriesError.message();
                return false;
            }

            if (!writeTextFileAtomically(scriptModulePath, buildOutdoorMapScriptStub(packageMetadata), errorMessage))
            {
                return false;
            }
        }
    }

    if (!writeTextFileAtomically(scenePhysicalPath, yamlText, errorMessage))
    {
        return false;
    }

    m_scenePhysicalPath = scenePhysicalPath;
    m_sceneVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, scenePhysicalPath);
    m_geometryPhysicalPath = targetGeometryPath;
    m_geometryVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, targetGeometryPath);
    m_geometryMetadataPhysicalPath = targetGeometryMetadataPath;
    m_geometryMetadataVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, targetGeometryMetadataPath);
    m_mapPackagePhysicalPath = targetMapPackagePath;
    m_mapPackageVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, targetMapPackagePath);
    m_hasMapPackageRoot = true;
    m_terrainMetadataPhysicalPath = targetTerrainMetadataPath;
    m_terrainMetadataVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, targetTerrainMetadataPath);
    m_outdoorMapPackageMetadata = packageMetadata;
    m_displayName = targetGeometryFileName;
    m_isRuntimeBuildDirty = (packageMetadata.builtSourceFingerprint != sourceFingerprint);
    m_isDirty = false;
    return true;
}

bool EditorDocument::buildRuntime(std::string &errorMessage)
{
    if (m_kind != Kind::Outdoor && m_kind != Kind::Indoor)
    {
        errorMessage = "no editable document is loaded";
        return false;
    }

    if (m_scenePhysicalPath.empty())
    {
        errorMessage = "document has no build path";
        return false;
    }

    if (m_isDirty)
    {
        errorMessage = "save source before build";
        return false;
    }

    return buildRuntimeAs(m_scenePhysicalPath, errorMessage);
}

bool EditorDocument::buildRuntimeAs(const std::filesystem::path &scenePhysicalPath, std::string &errorMessage)
{
    if (m_kind == Kind::Indoor)
    {
        if (m_editorDevelopmentRoot.empty())
        {
            errorMessage = "document save root is not initialized";
            return false;
        }

        if (m_isDirty)
        {
            errorMessage = "save source before build";
            return false;
        }

        if (m_indoorSceneData.geometryFile.empty())
        {
            errorMessage = "document geometry save path is not initialized";
            return false;
        }

        const std::string targetGeometryFileName = deriveGeometryFileNameForScenePath(
            scenePhysicalPath,
            m_indoorSceneData.geometryFile);
        const std::filesystem::path targetGeometryPath = scenePhysicalPath.parent_path() / targetGeometryFileName;
        Game::IndoorMapData compiledIndoorGeometry = {};
        std::vector<uint8_t> compiledIndoorGeometryBytes;
        std::string compileErrorMessage;

        if (m_hasIndoorGeometryMetadata
            && compileIndoorSourceGeometryBytes(
                m_editorDevelopmentRoot,
                scenePhysicalPath,
                m_indoorGeometryMetadata,
                m_indoorSceneData,
                compiledIndoorGeometry,
                compiledIndoorGeometryBytes,
                compileErrorMessage))
        {
            if (!writeBinaryFileAtomically(targetGeometryPath, compiledIndoorGeometryBytes, errorMessage))
            {
                return false;
            }

            m_indoorGeometry = std::move(compiledIndoorGeometry);
            m_indoorGeometrySourceBytes = std::move(compiledIndoorGeometryBytes);
            m_geometryPhysicalPath = targetGeometryPath;
            m_geometryVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, targetGeometryPath);
            m_isRuntimeBuildDirty = false;
            return true;
        }

        if (!compileErrorMessage.empty())
        {
            errorMessage = compileErrorMessage;
            return false;
        }

        if (!m_indoorGeometrySourceBytes.empty()
            && !writeBinaryFileAtomically(targetGeometryPath, m_indoorGeometrySourceBytes, errorMessage))
        {
            return false;
        }

        m_geometryPhysicalPath = targetGeometryPath;
        m_geometryVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, targetGeometryPath);
        m_isRuntimeBuildDirty = false;
        return true;
    }

    if (m_kind != Kind::Outdoor)
    {
        errorMessage = "no editable document is loaded";
        return false;
    }

    if (m_editorDevelopmentRoot.empty())
    {
        errorMessage = "document save root is not initialized";
        return false;
    }

    if (m_isDirty)
    {
        errorMessage = "save source before build";
        return false;
    }

    if (m_outdoorSceneData.geometryFile.empty())
    {
        errorMessage = "document geometry save path is not initialized";
        return false;
    }

    const std::string targetGeometryFileName = deriveGeometryFileNameForScenePath(
        scenePhysicalPath,
        m_outdoorSceneData.geometryFile);
    const std::filesystem::path targetGeometryPath = scenePhysicalPath.parent_path() / targetGeometryFileName;
    const std::optional<std::vector<uint8_t>> geometryBytes =
        compileOutdoorGeometryBytes(m_outdoorGeometry, m_outdoorGeometrySourceBytes);

    if (!geometryBytes)
    {
        errorMessage = "could not serialize outdoor geometry back into ODM";
        return false;
    }

    if (!writeBinaryFileAtomically(targetGeometryPath, *geometryBytes, errorMessage))
    {
        return false;
    }

    if (m_hasMapPackageRoot)
    {
        synchronizeOutdoorGeometryMetadata();
        synchronizeOutdoorTerrainMetadata();
        const std::string targetGeometryFileName = deriveGeometryFileNameForScenePath(
            scenePhysicalPath,
            m_outdoorSceneData.geometryFile);
        const std::filesystem::path targetGeometryMetadataPath = deriveGeometryMetadataPathForScenePath(scenePhysicalPath);
        const std::filesystem::path targetTerrainMetadataPath = deriveTerrainMetadataPathForScenePath(scenePhysicalPath);
        const std::filesystem::path targetMapPackagePath = deriveMapPackagePathForScenePath(scenePhysicalPath);
        m_outdoorGeometryMetadata.mapFileName = targetGeometryFileName;
        m_outdoorTerrainMetadata.mapFileName = targetGeometryFileName;
        const std::string sceneText = serializeOutdoorScene(m_outdoorSceneData, targetGeometryFileName);
        const std::string geometryMetadataText = serializeOutdoorGeometryMetadata(m_outdoorGeometryMetadata);
        const std::string terrainMetadataText = serializeOutdoorTerrainMetadata(m_outdoorTerrainMetadata);
        EditorOutdoorMapPackageMetadata packageMetadata = m_outdoorMapPackageMetadata;
        normalizeOutdoorMapPackageMetadata(
            packageMetadata,
            deriveOutdoorMapPackageId(targetGeometryFileName),
            deriveOutdoorMapPackageDisplayName(targetGeometryFileName),
            targetGeometryFileName,
            scenePhysicalPath.filename().string(),
            targetGeometryMetadataPath.filename().string(),
            targetTerrainMetadataPath.filename().string(),
            deriveDefaultScriptModuleForMapFile(targetGeometryFileName),
            std::string(),
            std::string());
        packageMetadata.mapFileName = targetGeometryFileName;
        packageMetadata.sceneFile = scenePhysicalPath.filename().string();
        packageMetadata.geometryMetadataFile = targetGeometryMetadataPath.filename().string();
        packageMetadata.terrainMetadataFile = targetTerrainMetadataPath.filename().string();

        std::vector<std::vector<std::string>> mapStatsRows;
        std::vector<std::vector<std::string>> navigationRows;
        const std::filesystem::path mapStatsRelativePath = std::filesystem::path("Data") / "data_tables" / "map_stats.txt";
        const std::filesystem::path navigationRelativePath =
            std::filesystem::path("Data") / "data_tables" / "map_navigation.txt";
        const std::filesystem::path mapStatsPath = m_editorDevelopmentRoot / mapStatsRelativePath;
        const std::filesystem::path navigationPath = m_editorDevelopmentRoot / navigationRelativePath;

        if (!ensureOverlaySeedTextFile(m_developmentRoot, m_editorDevelopmentRoot, mapStatsRelativePath, errorMessage))
        {
            return false;
        }

        if (!ensureOverlaySeedTextFile(m_developmentRoot, m_editorDevelopmentRoot, navigationRelativePath, errorMessage))
        {
            return false;
        }

        if (packageMetadata.mapStatsId <= 0)
        {
            packageMetadata.mapStatsId = nextAvailableMapStatsId(mapStatsPath);
        }

        const std::string sourceFingerprint =
            currentSourcePackageFingerprintForTexts(sceneText, geometryMetadataText, terrainMetadataText, packageMetadata);
        packageMetadata.sourceFingerprint = sourceFingerprint;
        packageMetadata.builtSourceFingerprint = sourceFingerprint;
        const std::string packageMetadataText = serializeOutdoorMapPackageMetadata(packageMetadata);

        if (!readTabSeparatedRows(mapStatsPath, mapStatsRows, errorMessage))
        {
            return false;
        }

        if (!readTabSeparatedRows(navigationPath, navigationRows, errorMessage))
        {
            return false;
        }

        upsertTableRowByKey(mapStatsRows, 2, packageMetadata.mapFileName, buildMapStatsRow(packageMetadata));
        upsertTableRowByKey(navigationRows, 0, packageMetadata.mapFileName, buildMapNavigationRow(packageMetadata));
        const std::string mapStatsText = serializeTabSeparatedRows(mapStatsRows);
        const std::string navigationText = serializeTabSeparatedRows(navigationRows);

        if (!writeTextFileAtomically(mapStatsPath, mapStatsText, errorMessage))
        {
            return false;
        }

        if (!writeTextFileAtomically(navigationPath, navigationText, errorMessage))
        {
            return false;
        }

        if (!writeTextFileAtomically(targetMapPackagePath, packageMetadataText, errorMessage))
        {
            return false;
        }

        m_mapPackagePhysicalPath = targetMapPackagePath;
        m_mapPackageVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, targetMapPackagePath);
        m_outdoorMapPackageMetadata = packageMetadata;
        m_displayName = targetGeometryFileName;
    }

    m_outdoorGeometrySourceBytes = *geometryBytes;
    m_geometryPhysicalPath = targetGeometryPath;
    m_geometryVirtualPath = sceneVirtualPathFromPhysical(m_editorDevelopmentRoot, targetGeometryPath);
    m_isRuntimeBuildDirty = false;
    return true;
}

bool EditorDocument::save(std::string &errorMessage)
{
    return saveSource(errorMessage);
}

bool EditorDocument::saveAs(const std::filesystem::path &scenePhysicalPath, std::string &errorMessage)
{
    if (!saveSourceAs(scenePhysicalPath, errorMessage))
    {
        return false;
    }

    return buildRuntimeAs(scenePhysicalPath, errorMessage);
}

bool EditorDocument::buildOutdoorAuthoredRuntimeState(
    Game::OutdoorMapData &outdoorMapData,
    Game::MapDeltaData &mapDeltaData,
    std::string &errorMessage) const
{
    if (m_kind != Kind::Outdoor)
    {
        errorMessage = "document does not contain an outdoor scene";
        return false;
    }

    outdoorMapData = m_outdoorGeometry;
    mapDeltaData = {};
    return Game::buildOutdoorMapStateFromScene(m_outdoorSceneData, outdoorMapData, mapDeltaData, errorMessage);
}

bool EditorDocument::buildIndoorAuthoredRuntimeState(
    Game::IndoorMapData &indoorMapData,
    Game::MapDeltaData &mapDeltaData,
    std::string &errorMessage) const
{
    if (m_kind != Kind::Indoor)
    {
        errorMessage = "document does not contain an indoor scene";
        return false;
    }

    if (m_hasIndoorGeometryMetadata)
    {
        Game::IndoorMapData compiledIndoorGeometry = {};
        std::vector<uint8_t> ignoredCompiledBytes;
        std::string compileErrorMessage;

        if (compileIndoorSourceGeometryBytes(
                m_editorDevelopmentRoot,
                m_scenePhysicalPath,
                m_indoorGeometryMetadata,
                m_indoorSceneData,
                compiledIndoorGeometry,
                ignoredCompiledBytes,
                compileErrorMessage))
        {
            indoorMapData = std::move(compiledIndoorGeometry);
            mapDeltaData = {};
            return true;
        }

        if (!compileErrorMessage.empty())
        {
            errorMessage = compileErrorMessage;
            return false;
        }
    }

    indoorMapData = m_indoorGeometry;
    mapDeltaData = {};
    return Game::buildIndoorMapStateFromScene(m_indoorSceneData, indoorMapData, mapDeltaData, errorMessage);
}

bool EditorDocument::restoreOutdoorSceneSnapshot(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneSnapshot,
    std::string &errorMessage)
{
    if (m_kind != Kind::Outdoor)
    {
        errorMessage = "document does not contain an outdoor scene";
        return false;
    }

    const std::string separator = DocumentSnapshotSeparator;
    const size_t separatorOffset = sceneSnapshot.find(separator);

    if (separatorOffset == std::string::npos)
    {
        errorMessage = "document snapshot is missing ODM geometry section";
        return false;
    }

    const std::string geometryMetadataSeparator = DocumentSnapshotGeometryMetadataSeparator;
    const size_t geometryMetadataSeparatorOffset =
        sceneSnapshot.find(geometryMetadataSeparator, separatorOffset + separator.size());
    const std::string terrainMetadataSeparator = DocumentSnapshotTerrainMetadataSeparator;
    const size_t terrainMetadataSeparatorOffset =
        sceneSnapshot.find(
            terrainMetadataSeparator,
            geometryMetadataSeparatorOffset == std::string::npos
                ? separatorOffset + separator.size()
                : geometryMetadataSeparatorOffset + geometryMetadataSeparator.size());
    const std::string sceneText = sceneSnapshot.substr(0, separatorOffset);
    const std::string geometryHex =
        geometryMetadataSeparatorOffset == std::string::npos
            ? sceneSnapshot.substr(separatorOffset + separator.size())
            : sceneSnapshot.substr(
                separatorOffset + separator.size(),
                geometryMetadataSeparatorOffset - (separatorOffset + separator.size()));
    const std::string geometryMetadataText =
        geometryMetadataSeparatorOffset == std::string::npos
            ? std::string()
            : sceneSnapshot.substr(
                geometryMetadataSeparatorOffset + geometryMetadataSeparator.size(),
                terrainMetadataSeparatorOffset == std::string::npos
                    ? std::string::npos
                    : terrainMetadataSeparatorOffset
                        - (geometryMetadataSeparatorOffset + geometryMetadataSeparator.size()));
    const std::string terrainMetadataText =
        terrainMetadataSeparatorOffset == std::string::npos
            ? std::string()
            : sceneSnapshot.substr(terrainMetadataSeparatorOffset + terrainMetadataSeparator.size());
    std::vector<uint8_t> geometryBytes;

    if (!upperHexToBytes(geometryHex, geometryBytes))
    {
        errorMessage = "document snapshot contains invalid ODM hex";
        return false;
    }

    Game::OutdoorMapDataLoader geometryLoader = {};
    const std::optional<Game::OutdoorMapData> outdoorGeometry = geometryLoader.loadFromBytes(geometryBytes);

    if (!outdoorGeometry)
    {
        errorMessage = "document snapshot contains invalid ODM geometry";
        return false;
    }

    const bool usePhysicalPath = std::filesystem::path(m_sceneVirtualPath).is_absolute();
    const bool loaded = usePhysicalPath
        ? loadOutdoorScenePhysicalPath(
            assetFileSystem,
            m_scenePhysicalPath,
            sceneText,
            m_hasMapPackageRoot ? std::optional<EditorOutdoorMapPackageMetadata>(m_outdoorMapPackageMetadata) : std::nullopt,
            m_hasMapPackageRoot ? std::optional<std::filesystem::path>(m_mapPackagePhysicalPath) : std::nullopt,
            errorMessage)
        : loadOutdoorSceneText(
            assetFileSystem,
            m_sceneVirtualPath,
            sceneText,
            m_hasMapPackageRoot ? std::optional<EditorOutdoorMapPackageMetadata>(m_outdoorMapPackageMetadata) : std::nullopt,
            m_hasMapPackageRoot ? std::optional<std::string>(m_mapPackageVirtualPath) : std::nullopt,
            errorMessage);

    if (loaded)
    {
        m_outdoorGeometrySourceBytes = geometryBytes;
        m_outdoorGeometry = *outdoorGeometry;
        if (!geometryMetadataText.empty())
        {
            const std::optional<EditorOutdoorGeometryMetadata> geometryMetadata =
                loadOutdoorGeometryMetadataFromText(geometryMetadataText, errorMessage);

            if (!geometryMetadata)
            {
                return false;
            }

            m_outdoorGeometryMetadata = *geometryMetadata;
        }

        if (!terrainMetadataText.empty())
        {
            const std::optional<EditorOutdoorTerrainMetadata> terrainMetadata =
                loadOutdoorTerrainMetadataFromText(terrainMetadataText, errorMessage);

            if (!terrainMetadata)
            {
                return false;
            }

            m_outdoorTerrainMetadata = *terrainMetadata;
        }

        synchronizeOutdoorGeometryMetadata();

        if (!terrainMetadataText.empty())
        {
            normalizeOutdoorTerrainMetadata(
                m_outdoorTerrainMetadata,
                m_displayName,
                m_outdoorGeometry.heightMap,
                m_outdoorGeometry.tileMap,
                m_outdoorGeometry.attributeMap);
            m_outdoorGeometry.heightMap = m_outdoorTerrainMetadata.heightMap;
            m_outdoorGeometry.tileMap = m_outdoorTerrainMetadata.tileMap;
            m_outdoorGeometry.attributeMap = m_outdoorTerrainMetadata.attributeMap;
        }
        else
        {
            synchronizeOutdoorTerrainMetadata();
        }
        ++m_sceneRevision;
        m_isDirty = true;
        m_isRuntimeBuildDirty = true;
    }

    return loaded;
}

bool EditorDocument::restoreIndoorSceneSnapshot(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneSnapshot,
    std::string &errorMessage)
{
    if (m_kind != Kind::Indoor)
    {
        errorMessage = "document does not contain an indoor scene";
        return false;
    }

    const std::string separator = IndoorDocumentSnapshotSeparator;
    const size_t separatorOffset = sceneSnapshot.find(separator);

    if (separatorOffset == std::string::npos)
    {
        errorMessage = "document snapshot is missing BLV geometry section";
        return false;
    }

    const std::string sceneText = sceneSnapshot.substr(0, separatorOffset);
    const std::string geometryAndMetadataText = sceneSnapshot.substr(separatorOffset + separator.size());
    const std::string metadataSeparator = IndoorDocumentSnapshotGeometryMetadataSeparator;
    const size_t metadataSeparatorOffset = geometryAndMetadataText.find(metadataSeparator);
    const std::string geometryHex =
        metadataSeparatorOffset == std::string::npos
            ? geometryAndMetadataText
            : geometryAndMetadataText.substr(0, metadataSeparatorOffset);
    const std::string geometryMetadataText =
        metadataSeparatorOffset == std::string::npos
            ? std::string()
            : geometryAndMetadataText.substr(metadataSeparatorOffset + metadataSeparator.size());
    std::vector<uint8_t> geometryBytes;

    if (!upperHexToBytes(geometryHex, geometryBytes))
    {
        errorMessage = "document snapshot contains invalid BLV hex";
        return false;
    }

    Game::IndoorMapDataLoader geometryLoader = {};
    const std::optional<Game::IndoorMapData> indoorGeometry = geometryLoader.loadFromBytes(geometryBytes);

    if (!indoorGeometry)
    {
        errorMessage = "document snapshot contains invalid BLV geometry";
        return false;
    }

    const bool usePhysicalPath = std::filesystem::path(m_sceneVirtualPath).is_absolute();
    const bool loaded = usePhysicalPath
        ? loadIndoorScenePhysicalPath(assetFileSystem, m_scenePhysicalPath, sceneText, errorMessage)
        : loadIndoorSceneText(assetFileSystem, m_sceneVirtualPath, sceneText, errorMessage);

    if (loaded)
    {
        m_indoorGeometrySourceBytes = geometryBytes;
        m_indoorGeometry = *indoorGeometry;

        if (metadataSeparatorOffset != std::string::npos)
        {
            std::optional<EditorIndoorGeometryMetadata> geometryMetadata =
                loadIndoorGeometryMetadataFromText(geometryMetadataText, errorMessage);

            if (!geometryMetadata)
            {
                return false;
            }

            m_hasIndoorGeometryMetadata = true;
            m_indoorGeometryMetadata = *geometryMetadata;
            normalizeIndoorGeometryMetadata(m_indoorGeometryMetadata, m_indoorSceneData.geometryFile);
        }

        ++m_sceneRevision;
        m_isDirty = true;
        m_isRuntimeBuildDirty = false;
    }

    return loaded;
}

bool EditorDocument::loadOutdoorScenePhysicalPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::filesystem::path &scenePhysicalPath,
    const std::string &sceneText,
    const std::optional<EditorOutdoorMapPackageMetadata> &packageMetadata,
    const std::optional<std::filesystem::path> &packagePhysicalPath,
    std::string &errorMessage)
{
    Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<Game::OutdoorSceneData> sceneData = sceneLoader.loadFromText(sceneText, errorMessage);

    if (!sceneData)
    {
        return false;
    }

    const std::filesystem::path developmentRoot = assetFileSystem.getDevelopmentRoot();
    const std::filesystem::path editorDevelopmentRoot = assetFileSystem.getEditorDevelopmentRoot();
    const std::filesystem::path geometryPath = scenePhysicalPath.parent_path() / sceneData->geometryFile;
    const std::filesystem::path geometryMetadataPhysicalPath =
        packageMetadata
            ? (scenePhysicalPath.parent_path() / packageMetadata->geometryMetadataFile)
            : deriveGeometryMetadataPathForScenePath(scenePhysicalPath);
    const std::filesystem::path terrainMetadataPhysicalPath =
        packageMetadata
            ? (scenePhysicalPath.parent_path() / packageMetadata->terrainMetadataFile)
            : deriveTerrainMetadataPathForScenePath(scenePhysicalPath);
    std::string geometryMetadataText;
    std::string terrainMetadataText;
    const bool hasGeometryMetadataText = readTextFile(geometryMetadataPhysicalPath, geometryMetadataText);
    const bool hasTerrainMetadataText = readTextFile(terrainMetadataPhysicalPath, terrainMetadataText);

    std::optional<EditorOutdoorGeometryMetadata> geometryMetadata;

    if (hasGeometryMetadataText)
    {
        geometryMetadata = loadOutdoorGeometryMetadataFromText(geometryMetadataText, errorMessage);

        if (!geometryMetadata)
        {
            return false;
        }
    }

    std::optional<EditorOutdoorTerrainMetadata> terrainMetadata;

    if (hasTerrainMetadataText)
    {
        terrainMetadata = loadOutdoorTerrainMetadataFromText(terrainMetadataText, errorMessage);

        if (!terrainMetadata)
        {
            return false;
        }
    }

    std::vector<uint8_t> geometryBytesStorage;
    const bool hasGeometryBytes = readBinaryFile(geometryPath, geometryBytesStorage);
    std::optional<std::vector<uint8_t>> geometryBytes;

    if (hasGeometryBytes)
    {
        geometryBytes = geometryBytesStorage;
    }

    std::optional<Game::OutdoorMapData> outdoorGeometry;

    if (geometryBytes)
    {
        Game::OutdoorMapDataLoader geometryLoader = {};
        outdoorGeometry = geometryLoader.loadFromBytes(*geometryBytes);

        if (!outdoorGeometry)
        {
            errorMessage = "could not parse outdoor geometry: " + geometryPath.string();
            return false;
        }
    }
    else if (packageMetadata)
    {
        outdoorGeometry = buildOutdoorGeometryFromSourcePackage(
            assetFileSystem,
            *sceneData,
            geometryMetadata,
            terrainMetadata,
            errorMessage);

        if (!outdoorGeometry)
        {
            if (errorMessage.empty())
            {
                errorMessage = "could not rebuild outdoor geometry from source package";
            }

            return false;
        }
    }
    else
    {
        errorMessage = "could not read outdoor geometry: " + geometryPath.string();
        return false;
    }

    m_kind = Kind::Outdoor;
    m_isDirty = false;
    m_isRuntimeBuildDirty = false;
    m_developmentRoot = developmentRoot;
    m_editorDevelopmentRoot = editorDevelopmentRoot;
    m_outdoorGeometry = *outdoorGeometry;
    m_outdoorGeometrySourceBytes = geometryBytes.value_or(std::vector<uint8_t>{});
    m_outdoorSceneData = *sceneData;
    m_indoorGeometry = {};
    m_indoorGeometrySourceBytes.clear();
    m_indoorSceneData = {};
    m_hasIndoorGeometryMetadata = false;
    m_indoorGeometryMetadata = {};
    ++m_sceneRevision;
    m_sceneVirtualPath = displayPathForDocument(editorDevelopmentRoot, scenePhysicalPath);
    m_scenePhysicalPath = scenePhysicalPath;
    m_geometryVirtualPath = displayPathForDocument(editorDevelopmentRoot, geometryPath);
    m_geometryPhysicalPath = geometryPath;
    m_geometryMetadataVirtualPath = displayPathForDocument(editorDevelopmentRoot, geometryMetadataPhysicalPath);
    m_geometryMetadataPhysicalPath = geometryMetadataPhysicalPath;
    m_hasMapPackageRoot = packageMetadata.has_value();
    m_mapPackageVirtualPath =
        packagePhysicalPath
            ? displayPathForDocument(editorDevelopmentRoot, *packagePhysicalPath)
            : std::string();
    m_mapPackagePhysicalPath = packagePhysicalPath.value_or(std::filesystem::path());
    m_terrainMetadataVirtualPath = displayPathForDocument(editorDevelopmentRoot, terrainMetadataPhysicalPath);
    m_terrainMetadataPhysicalPath = terrainMetadataPhysicalPath;
    m_displayName = sceneData->geometryFile;
    m_outdoorMapPackageMetadata = packageMetadata.value_or(EditorOutdoorMapPackageMetadata{});
    m_outdoorGeometryMetadata = geometryMetadata.value_or(EditorOutdoorGeometryMetadata{});
    m_outdoorTerrainMetadata = terrainMetadata.value_or(EditorOutdoorTerrainMetadata{});

    synchronizeOutdoorGeometryMetadata();

    if (hasTerrainMetadataText)
    {
        normalizeOutdoorTerrainMetadata(
            m_outdoorTerrainMetadata,
            m_displayName,
            m_outdoorGeometry.heightMap,
            m_outdoorGeometry.tileMap,
            m_outdoorGeometry.attributeMap);
        m_outdoorGeometry.heightMap = m_outdoorTerrainMetadata.heightMap;
        m_outdoorGeometry.tileMap = m_outdoorTerrainMetadata.tileMap;
        m_outdoorGeometry.attributeMap = m_outdoorTerrainMetadata.attributeMap;
    }
    else
    {
        synchronizeOutdoorTerrainMetadata();
    }

    const std::string sourceFingerprint = currentSourcePackageFingerprint();
    normalizeOutdoorMapPackageMetadata(
        m_outdoorMapPackageMetadata,
        deriveOutdoorMapPackageId(sceneData->geometryFile),
        deriveOutdoorMapPackageDisplayName(sceneData->geometryFile),
        sceneData->geometryFile,
        m_scenePhysicalPath.filename().string(),
        m_geometryMetadataPhysicalPath.filename().string(),
        m_terrainMetadataPhysicalPath.filename().string(),
        deriveDefaultScriptModuleForMapFile(sceneData->geometryFile),
        sourceFingerprint,
        m_hasMapPackageRoot ? m_outdoorMapPackageMetadata.builtSourceFingerprint : sourceFingerprint);
    m_isRuntimeBuildDirty = (m_outdoorMapPackageMetadata.builtSourceFingerprint != sourceFingerprint);
    return true;
}

bool EditorDocument::loadIndoorScenePhysicalPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::filesystem::path &scenePhysicalPath,
    const std::string &sceneText,
    std::string &errorMessage)
{
    Game::IndoorSceneYmlLoader sceneLoader = {};
    const std::optional<Game::IndoorSceneData> sceneData = sceneLoader.loadFromText(sceneText, errorMessage);

    if (!sceneData)
    {
        return false;
    }

    const std::filesystem::path developmentRoot = assetFileSystem.getDevelopmentRoot();
    const std::filesystem::path editorDevelopmentRoot = assetFileSystem.getEditorDevelopmentRoot();
    const std::filesystem::path geometryPath = scenePhysicalPath.parent_path() / sceneData->geometryFile;
    const std::filesystem::path geometryMetadataPhysicalPath =
        deriveGeometryMetadataPathForScenePath(scenePhysicalPath);
    std::string geometryMetadataText;
    const bool hasGeometryMetadataText = readTextFile(geometryMetadataPhysicalPath, geometryMetadataText);
    std::vector<uint8_t> geometryBytes;

    if (!readBinaryFile(geometryPath, geometryBytes))
    {
        errorMessage = "could not read indoor geometry: " + geometryPath.string();
        return false;
    }

    Game::IndoorMapDataLoader geometryLoader = {};
    const std::optional<Game::IndoorMapData> indoorGeometry = geometryLoader.loadFromBytes(geometryBytes);

    if (!indoorGeometry)
    {
        errorMessage = "could not parse indoor geometry: " + geometryPath.string();
        return false;
    }

    std::optional<EditorIndoorGeometryMetadata> geometryMetadata;

    if (hasGeometryMetadataText)
    {
        geometryMetadata = loadIndoorGeometryMetadataFromText(geometryMetadataText, errorMessage);

        if (!geometryMetadata)
        {
            return false;
        }

        normalizeIndoorGeometryMetadata(*geometryMetadata, sceneData->geometryFile);
    }

    Game::IndoorSceneData normalizedSceneData = *sceneData;
    synthesizeIndoorFaceAttributeOverridesFromLegacyCompanion(
        assetFileSystem,
        scenePhysicalPath,
        displayPathForDocument(editorDevelopmentRoot, scenePhysicalPath),
        *indoorGeometry,
        normalizedSceneData);

    m_kind = Kind::Indoor;
    m_isDirty = false;
    m_isRuntimeBuildDirty = false;
    m_developmentRoot = developmentRoot;
    m_editorDevelopmentRoot = editorDevelopmentRoot;
    m_outdoorGeometry = {};
    m_outdoorSceneData = {};
    m_outdoorGeometryMetadata = {};
    m_outdoorMapPackageMetadata = {};
    m_outdoorTerrainMetadata = {};
    m_outdoorGeometrySourceBytes.clear();
    m_indoorGeometry = *indoorGeometry;
    m_indoorGeometrySourceBytes = geometryBytes;
    m_indoorSceneData = std::move(normalizedSceneData);
    m_hasIndoorGeometryMetadata = hasGeometryMetadataText;
    m_indoorGeometryMetadata = geometryMetadata.value_or(EditorIndoorGeometryMetadata{});
    normalizeIndoorGeometryMetadata(m_indoorGeometryMetadata, sceneData->geometryFile);
    ++m_sceneRevision;
    m_sceneVirtualPath = displayPathForDocument(editorDevelopmentRoot, scenePhysicalPath);
    m_scenePhysicalPath = scenePhysicalPath;
    m_geometryVirtualPath = displayPathForDocument(editorDevelopmentRoot, geometryPath);
    m_geometryPhysicalPath = geometryPath;
    m_geometryMetadataVirtualPath =
        hasGeometryMetadataText
            ? displayPathForDocument(editorDevelopmentRoot, geometryMetadataPhysicalPath)
            : std::string();
    m_geometryMetadataPhysicalPath = hasGeometryMetadataText ? geometryMetadataPhysicalPath : std::filesystem::path();
    m_hasMapPackageRoot = false;
    m_mapPackageVirtualPath.clear();
    m_mapPackagePhysicalPath.clear();
    m_terrainMetadataVirtualPath.clear();
    m_terrainMetadataPhysicalPath.clear();
    m_displayName = sceneData->geometryFile;
    return true;
}

std::string EditorDocument::createOutdoorSceneSnapshot() const
{
    if (m_kind != Kind::Outdoor)
    {
        return {};
    }

    const std::optional<std::vector<uint8_t>> geometryBytes =
        compileOutdoorGeometryBytes(m_outdoorGeometry, m_outdoorGeometrySourceBytes);
    EditorOutdoorGeometryMetadata geometryMetadata = m_outdoorGeometryMetadata;
    EditorOutdoorTerrainMetadata terrainMetadata = m_outdoorTerrainMetadata;
    normalizeOutdoorGeometryMetadata(geometryMetadata, m_displayName, m_outdoorGeometry.bmodels.size());
    normalizeOutdoorTerrainMetadata(
        terrainMetadata,
        m_displayName,
        m_outdoorGeometry.heightMap,
        m_outdoorGeometry.tileMap,
        m_outdoorGeometry.attributeMap);

    if (!geometryBytes)
    {
        return serializeOutdoorScene(m_outdoorSceneData)
            + DocumentSnapshotSeparator
            + DocumentSnapshotGeometryMetadataSeparator
            + serializeOutdoorGeometryMetadata(geometryMetadata)
            + DocumentSnapshotTerrainMetadataSeparator
            + serializeOutdoorTerrainMetadata(terrainMetadata);
    }

    return serializeOutdoorScene(m_outdoorSceneData)
        + DocumentSnapshotSeparator
        + bytesToUpperHex(*geometryBytes)
        + DocumentSnapshotGeometryMetadataSeparator
        + serializeOutdoorGeometryMetadata(geometryMetadata)
        + DocumentSnapshotTerrainMetadataSeparator
        + serializeOutdoorTerrainMetadata(terrainMetadata);
}

std::string EditorDocument::createIndoorSceneSnapshot() const
{
    if (m_kind != Kind::Indoor)
    {
        return {};
    }

    Game::IndoorMapDataWriter geometryWriter = {};
    const std::optional<std::vector<uint8_t>> geometryBytes =
        m_hasIndoorGeometryMetadata ? std::nullopt : geometryWriter.buildBytes(m_indoorGeometry);
    const std::vector<uint8_t> &snapshotGeometryBytes = geometryBytes ? *geometryBytes : m_indoorGeometrySourceBytes;
    std::string snapshot = serializeIndoorScene(m_indoorSceneData)
        + IndoorDocumentSnapshotSeparator
        + bytesToUpperHex(snapshotGeometryBytes);

    if (m_hasIndoorGeometryMetadata || !isIndoorGeometryMetadataEmpty(m_indoorGeometryMetadata))
    {
        EditorIndoorGeometryMetadata geometryMetadata = m_indoorGeometryMetadata;
        normalizeIndoorGeometryMetadata(geometryMetadata, m_displayName);
        snapshot += IndoorDocumentSnapshotGeometryMetadataSeparator;
        snapshot += serializeIndoorGeometryMetadata(geometryMetadata);
    }

    return snapshot;
}

std::vector<std::string> EditorDocument::validate() const
{
    std::vector<std::string> issues;

    if (m_kind == Kind::Indoor)
    {
        if (m_indoorSceneData.geometryFile.empty())
        {
            issues.push_back("Scene source.geometry_file is empty.");
        }

        if (m_hasIndoorGeometryMetadata || !isIndoorGeometryMetadataEmpty(m_indoorGeometryMetadata))
        {
            std::vector<std::string> geometryMetadataIssues =
                validateIndoorGeometryMetadata(m_indoorGeometryMetadata, m_indoorGeometry);
            issues.insert(issues.end(), geometryMetadataIssues.begin(), geometryMetadataIssues.end());

            const std::string sourceAssetPath = trimCopy(m_indoorGeometryMetadata.source.assetPath);

            if (!sourceAssetPath.empty())
            {
                const std::filesystem::path sourcePath =
                    resolveIndoorSourceAssetPath(m_editorDevelopmentRoot, m_scenePhysicalPath, m_indoorGeometryMetadata);

                if (sourcePath.empty() || !std::filesystem::exists(sourcePath))
                {
                    issues.push_back("Indoor geometry source asset is missing: " + sourceAssetPath);
                }
            }
        }

        if (m_indoorSceneData.environment.fogWeakDistance < 0)
        {
            issues.push_back("Environment fog weak distance must be non-negative.");
        }

        if (m_indoorSceneData.environment.fogStrongDistance < 0)
        {
            issues.push_back("Environment fog strong distance must be non-negative.");
        }

        if (m_indoorSceneData.environment.fogStrongDistance < m_indoorSceneData.environment.fogWeakDistance)
        {
            issues.push_back("Environment fog strong distance must be greater than or equal to weak distance.");
        }

        std::vector<uint8_t> seenFaceOverrides(m_indoorGeometry.faces.size(), 0);

        for (const Game::IndoorSceneFaceAttributeOverride &overrideEntry : m_indoorSceneData.initialState.faceAttributeOverrides)
        {
            if (overrideEntry.faceIndex >= m_indoorGeometry.faces.size())
            {
                issues.push_back("Face override " + std::to_string(overrideEntry.faceIndex) + " is out of range.");
                continue;
            }

            if (seenFaceOverrides[overrideEntry.faceIndex] != 0)
            {
                issues.push_back("Face override " + std::to_string(overrideEntry.faceIndex) + " is duplicated.");
                continue;
            }

            seenFaceOverrides[overrideEntry.faceIndex] = 1;

            if (!overrideEntry.legacyAttributes.has_value()
                && !overrideEntry.textureFrameTableCog.has_value()
                && !overrideEntry.cogNumber.has_value()
                && !overrideEntry.cogTriggered.has_value()
                && !overrideEntry.cogTriggerType.has_value())
            {
                issues.push_back(
                    "Face override " + std::to_string(overrideEntry.faceIndex) + " does not define any override fields.");
            }
        }

        std::vector<uint8_t> seenDoorIndices(m_indoorGeometry.doorCount, 0);

        for (const Game::IndoorSceneDoor &door : m_indoorSceneData.initialState.doors)
        {
            if (door.doorIndex >= m_indoorGeometry.doorCount)
            {
                issues.push_back("Door " + std::to_string(door.doorIndex) + " is out of range.");
                continue;
            }

            if (seenDoorIndices[door.doorIndex] != 0)
            {
                issues.push_back("Door " + std::to_string(door.doorIndex) + " is duplicated.");
                continue;
            }

            seenDoorIndices[door.doorIndex] = 1;
        }

        for (const Game::IndoorSceneDecorationFlag &flag : m_indoorSceneData.initialState.decorationFlags)
        {
            if (flag.entityIndex >= m_indoorGeometry.entities.size())
            {
                issues.push_back("Decoration flag entity index " + std::to_string(flag.entityIndex) + " is invalid.");
            }
        }

        return issues;
    }

    if (m_kind != Kind::Outdoor)
    {
        issues.push_back("No outdoor document is loaded.");
        return issues;
    }

    if (m_outdoorSceneData.geometryFile.empty())
    {
        issues.push_back("Scene source.geometry_file is empty.");
    }

    if (m_outdoorSceneData.environment.fogWeakDistance < 0)
    {
        issues.push_back("Environment fog weak distance must be non-negative.");
    }

    if (m_outdoorSceneData.environment.fogStrongDistance < 0)
    {
        issues.push_back("Environment fog strong distance must be non-negative.");
    }

    if (m_outdoorSceneData.environment.fogStrongDistance < m_outdoorSceneData.environment.fogWeakDistance)
    {
        issues.push_back("Environment fog strong distance must be greater than or equal to weak distance.");
    }

    std::vector<bool> seenEntityIndices(m_outdoorSceneData.entities.size(), false);

    for (const Game::OutdoorSceneEntity &entity : m_outdoorSceneData.entities)
    {
        if (entity.entityIndex >= m_outdoorSceneData.entities.size())
        {
            issues.push_back("Entity index " + std::to_string(entity.entityIndex) + " is out of range.");
            continue;
        }

        if (seenEntityIndices[entity.entityIndex])
        {
            issues.push_back("Entity index " + std::to_string(entity.entityIndex) + " is duplicated.");
            continue;
        }

        seenEntityIndices[entity.entityIndex] = true;
    }

    std::vector<bool> seenSpawnIndices(m_outdoorSceneData.spawns.size(), false);

    for (const Game::OutdoorSceneSpawn &spawn : m_outdoorSceneData.spawns)
    {
        if (spawn.spawnIndex >= m_outdoorSceneData.spawns.size())
        {
            issues.push_back("Spawn index " + std::to_string(spawn.spawnIndex) + " is out of range.");
            continue;
        }

        if (seenSpawnIndices[spawn.spawnIndex])
        {
            issues.push_back("Spawn index " + std::to_string(spawn.spawnIndex) + " is duplicated.");
            continue;
        }

        seenSpawnIndices[spawn.spawnIndex] = true;
    }

    for (const Game::OutdoorSceneTerrainAttributeOverride &overrideEntry : m_outdoorSceneData.terrainAttributeOverrides)
    {
        if (overrideEntry.x < 0
            || overrideEntry.y < 0
            || overrideEntry.x >= Game::OutdoorMapData::TerrainWidth
            || overrideEntry.y >= Game::OutdoorMapData::TerrainHeight)
        {
            issues.push_back(
                "Terrain override (" + std::to_string(overrideEntry.x) + ", "
                + std::to_string(overrideEntry.y) + ") is out of bounds.");
        }
    }

    for (const Game::OutdoorSceneInteractiveFace &face : m_outdoorSceneData.interactiveFaces)
    {
        if (face.bmodelIndex >= m_outdoorGeometry.bmodels.size())
        {
            issues.push_back("Interactive face bmodel index " + std::to_string(face.bmodelIndex) + " is invalid.");
            continue;
        }

        if (face.faceIndex >= m_outdoorGeometry.bmodels[face.bmodelIndex].faces.size())
        {
            issues.push_back(
                "Interactive face (" + std::to_string(face.bmodelIndex) + ", "
                + std::to_string(face.faceIndex) + ") is invalid.");
        }
    }

    std::unordered_set<std::string> seenGeometryIds;

    for (const EditorOutdoorGeometryMetadataEntry &entry : m_outdoorGeometryMetadata.bmodels)
    {
        if (entry.runtimeBModelIndex >= m_outdoorGeometry.bmodels.size())
        {
            issues.push_back(
                "Geometry metadata bmodel index " + std::to_string(entry.runtimeBModelIndex) + " is invalid.");
            continue;
        }

        const std::string normalizedId = toLowerCopy(entry.geometryId);

        if (normalizedId.empty())
        {
            issues.push_back("Geometry metadata contains an empty geometry id.");
            continue;
        }

        if (seenGeometryIds.contains(normalizedId))
        {
            issues.push_back("Geometry metadata geometry_id '" + entry.geometryId + "' is duplicated.");
            continue;
        }

        seenGeometryIds.insert(normalizedId);
    }

    if (m_outdoorTerrainMetadata.heightMap.size() != m_outdoorGeometry.heightMap.size())
    {
        issues.push_back("Terrain metadata height map size does not match outdoor geometry.");
    }

    if (m_outdoorTerrainMetadata.tileMap.size() != m_outdoorGeometry.tileMap.size())
    {
        issues.push_back("Terrain metadata tile map size does not match outdoor geometry.");
    }

    if (m_outdoorTerrainMetadata.attributeMap.size() != m_outdoorGeometry.attributeMap.size())
    {
        issues.push_back("Terrain metadata attribute map size does not match outdoor geometry.");
    }

    if (m_hasMapPackageRoot)
    {
        if (m_outdoorMapPackageMetadata.packageId.empty())
        {
            issues.push_back("Map package package_id is empty.");
        }

        if (m_outdoorMapPackageMetadata.displayName.empty())
        {
            issues.push_back("Map package display_name is empty.");
        }

        if (m_outdoorMapPackageMetadata.mapStatsId <= 0)
        {
            issues.push_back("Map package map_stats_id must be positive.");
        }

        if (m_outdoorMapPackageMetadata.environmentName.empty())
        {
            issues.push_back("Map package environment_name is empty.");
        }

        if (m_outdoorMapPackageMetadata.outdoorBounds.enabled
            && (m_outdoorMapPackageMetadata.outdoorBounds.minX > m_outdoorMapPackageMetadata.outdoorBounds.maxX
                || m_outdoorMapPackageMetadata.outdoorBounds.minY > m_outdoorMapPackageMetadata.outdoorBounds.maxY))
        {
            issues.push_back("Map package outdoor bounds are inverted.");
        }

        const std::string currentFingerprint = currentSourcePackageFingerprint();

        if (m_outdoorMapPackageMetadata.sourceFingerprint != currentFingerprint)
        {
            issues.push_back("Map package source fingerprint is stale relative to current source files.");
        }
    }

    return issues;
}

EditorDocument::Kind EditorDocument::kind() const
{
    return m_kind;
}

bool EditorDocument::hasDocument() const
{
    return m_kind != Kind::None;
}

bool EditorDocument::isDirty() const
{
    return m_isDirty;
}

bool EditorDocument::isRuntimeBuildDirty() const
{
    return m_isRuntimeBuildDirty;
}

void EditorDocument::setDirty(bool isDirty)
{
    m_isDirty = isDirty;

    if (m_kind == Kind::Indoor)
    {
        m_isRuntimeBuildDirty = false;
        return;
    }

    if (m_kind != Kind::Outdoor)
    {
        m_isRuntimeBuildDirty = isDirty;
        return;
    }

    if (!m_hasMapPackageRoot)
    {
        m_isRuntimeBuildDirty = isDirty;
        return;
    }

    m_isRuntimeBuildDirty = (currentSourcePackageFingerprint() != m_outdoorMapPackageMetadata.builtSourceFingerprint);
}

void EditorDocument::touchSceneRevision()
{
    ++m_sceneRevision;
}

uint64_t EditorDocument::sceneRevision() const
{
    return m_sceneRevision;
}

const std::string &EditorDocument::displayName() const
{
    return m_displayName;
}

const std::string &EditorDocument::sceneVirtualPath() const
{
    return m_sceneVirtualPath;
}

const std::filesystem::path &EditorDocument::scenePhysicalPath() const
{
    return m_scenePhysicalPath;
}

const std::filesystem::path &EditorDocument::geometryPhysicalPath() const
{
    return m_geometryPhysicalPath;
}

const std::filesystem::path &EditorDocument::geometryMetadataPhysicalPath() const
{
    return m_geometryMetadataPhysicalPath;
}

const std::filesystem::path &EditorDocument::mapPackagePhysicalPath() const
{
    return m_mapPackagePhysicalPath;
}

bool EditorDocument::hasMapPackageRoot() const
{
    return m_hasMapPackageRoot;
}

const EditorOutdoorMapPackageMetadata &EditorDocument::outdoorMapPackageMetadata() const
{
    return m_outdoorMapPackageMetadata;
}

EditorOutdoorMapPackageMetadata &EditorDocument::mutableOutdoorMapPackageMetadata()
{
    return m_outdoorMapPackageMetadata;
}

std::string EditorDocument::currentSourcePackageFingerprint() const
{
    if (m_kind != Kind::Outdoor)
    {
        return {};
    }

    EditorOutdoorGeometryMetadata geometryMetadata = m_outdoorGeometryMetadata;
    EditorOutdoorTerrainMetadata terrainMetadata = m_outdoorTerrainMetadata;
    normalizeOutdoorGeometryMetadata(geometryMetadata, m_displayName, m_outdoorGeometry.bmodels.size());
    normalizeOutdoorTerrainMetadata(
        terrainMetadata,
        m_displayName,
        m_outdoorGeometry.heightMap,
        m_outdoorGeometry.tileMap,
        m_outdoorGeometry.attributeMap);
    terrainMetadata.heightMap = m_outdoorGeometry.heightMap;
    terrainMetadata.tileMap = m_outdoorGeometry.tileMap;
    terrainMetadata.attributeMap = m_outdoorGeometry.attributeMap;
    const std::string sceneText = serializeOutdoorScene(m_outdoorSceneData, m_outdoorSceneData.geometryFile);
    const std::string geometryMetadataText = serializeOutdoorGeometryMetadata(geometryMetadata);
    const std::string terrainMetadataText = serializeOutdoorTerrainMetadata(terrainMetadata);
    EditorOutdoorMapPackageMetadata packageMetadata = m_outdoorMapPackageMetadata;
    normalizeOutdoorMapPackageMetadata(
        packageMetadata,
        deriveOutdoorMapPackageId(m_outdoorSceneData.geometryFile),
        deriveOutdoorMapPackageDisplayName(m_outdoorSceneData.geometryFile),
        m_outdoorSceneData.geometryFile,
        m_scenePhysicalPath.empty() ? replaceExtension(m_outdoorSceneData.geometryFile, ".scene.yml")
                                    : m_scenePhysicalPath.filename().string(),
        m_geometryMetadataPhysicalPath.empty() ? replaceExtension(m_outdoorSceneData.geometryFile, ".geometry.yml")
                                               : m_geometryMetadataPhysicalPath.filename().string(),
        m_terrainMetadataPhysicalPath.empty() ? replaceExtension(m_outdoorSceneData.geometryFile, ".terrain.yml")
                                              : m_terrainMetadataPhysicalPath.filename().string(),
        deriveDefaultScriptModuleForMapFile(m_outdoorSceneData.geometryFile),
        std::string(),
        packageMetadata.builtSourceFingerprint);
    return currentSourcePackageFingerprintForTexts(sceneText, geometryMetadataText, terrainMetadataText, packageMetadata);
}

const std::filesystem::path &EditorDocument::terrainMetadataPhysicalPath() const
{
    return m_terrainMetadataPhysicalPath;
}

const Game::OutdoorMapData &EditorDocument::outdoorGeometry() const
{
    return m_outdoorGeometry;
}

Game::OutdoorMapData &EditorDocument::mutableOutdoorGeometry()
{
    return m_outdoorGeometry;
}

Game::OutdoorSceneData &EditorDocument::mutableOutdoorSceneData()
{
    return m_outdoorSceneData;
}

const Game::OutdoorSceneData &EditorDocument::outdoorSceneData() const
{
    return m_outdoorSceneData;
}

const Game::IndoorMapData &EditorDocument::indoorGeometry() const
{
    return m_indoorGeometry;
}

Game::IndoorMapData &EditorDocument::mutableIndoorGeometry()
{
    return m_indoorGeometry;
}

Game::IndoorSceneData &EditorDocument::mutableIndoorSceneData()
{
    return m_indoorSceneData;
}

const Game::IndoorSceneData &EditorDocument::indoorSceneData() const
{
    return m_indoorSceneData;
}

bool EditorDocument::hasIndoorGeometryMetadata() const
{
    return m_hasIndoorGeometryMetadata;
}

const EditorIndoorGeometryMetadata &EditorDocument::indoorGeometryMetadata() const
{
    return m_indoorGeometryMetadata;
}

EditorIndoorGeometryMetadata &EditorDocument::mutableIndoorGeometryMetadata()
{
    m_hasIndoorGeometryMetadata = true;
    return m_indoorGeometryMetadata;
}

const EditorOutdoorGeometryMetadata &EditorDocument::outdoorGeometryMetadata() const
{
    return m_outdoorGeometryMetadata;
}

std::optional<EditorBModelImportSource> EditorDocument::outdoorBModelImportSource(size_t bmodelIndex) const
{
    if (bmodelIndex >= m_outdoorGeometryMetadata.bmodels.size())
    {
        return std::nullopt;
    }

    const EditorBModelImportSource &importSource = m_outdoorGeometryMetadata.bmodels[bmodelIndex].importSource;

    if (importSource.sourcePath.empty())
    {
        return std::nullopt;
    }

    return importSource;
}

std::optional<EditorBModelSourceTransform> EditorDocument::outdoorBModelSourceTransform(size_t bmodelIndex) const
{
    if (bmodelIndex >= m_outdoorGeometryMetadata.bmodels.size())
    {
        return std::nullopt;
    }

    return m_outdoorGeometryMetadata.bmodels[bmodelIndex].sourceTransform;
}

void EditorDocument::prepareOutdoorMapPackageIdentityForMapFile(
    const std::string &mapFileName,
    const std::string &displayName)
{
    const std::string resolvedDisplayName =
        trimCopy(displayName).empty() ? deriveOutdoorMapPackageDisplayName(mapFileName) : trimCopy(displayName);
    m_outdoorMapPackageMetadata.packageId = deriveOutdoorMapPackageId(mapFileName);
    m_outdoorMapPackageMetadata.displayName = resolvedDisplayName;
    m_outdoorMapPackageMetadata.mapFileName = mapFileName;
    m_outdoorMapPackageMetadata.scriptModule = deriveDefaultScriptModuleForMapFile(mapFileName);
    m_outdoorGeometry.name = resolvedDisplayName;
}

void EditorDocument::setOutdoorBModelImportSource(size_t bmodelIndex, const EditorBModelImportSource &importSource)
{
    synchronizeOutdoorGeometryMetadata();

    if (bmodelIndex >= m_outdoorGeometryMetadata.bmodels.size())
    {
        return;
    }

    m_outdoorGeometryMetadata.bmodels[bmodelIndex].importSource = importSource;
}

void EditorDocument::setOutdoorBModelSourceTransform(size_t bmodelIndex, const EditorBModelSourceTransform &sourceTransform)
{
    synchronizeOutdoorGeometryMetadata();

    if (bmodelIndex >= m_outdoorGeometryMetadata.bmodels.size())
    {
        return;
    }

    m_outdoorGeometryMetadata.bmodels[bmodelIndex].sourceTransform = sourceTransform;
}

void EditorDocument::copyOutdoorBModelImportSource(size_t sourceBModelIndex, size_t targetBModelIndex)
{
    synchronizeOutdoorGeometryMetadata();

    if (sourceBModelIndex >= m_outdoorGeometryMetadata.bmodels.size()
        || targetBModelIndex >= m_outdoorGeometryMetadata.bmodels.size())
    {
        return;
    }

    m_outdoorGeometryMetadata.bmodels[targetBModelIndex].importSource =
        m_outdoorGeometryMetadata.bmodels[sourceBModelIndex].importSource;
    m_outdoorGeometryMetadata.bmodels[targetBModelIndex].sourceTransform =
        m_outdoorGeometryMetadata.bmodels[sourceBModelIndex].sourceTransform;
    m_outdoorGeometryMetadata.bmodels[targetBModelIndex].geometryId.clear();
    synchronizeOutdoorGeometryMetadata();
}

void EditorDocument::eraseOutdoorBModelImportSource(size_t deletedBModelIndex)
{
    synchronizeOutdoorGeometryMetadata();

    if (deletedBModelIndex >= m_outdoorGeometryMetadata.bmodels.size())
    {
        return;
    }

    m_outdoorGeometryMetadata.bmodels.erase(
        m_outdoorGeometryMetadata.bmodels.begin() + static_cast<ptrdiff_t>(deletedBModelIndex));
    synchronizeOutdoorGeometryMetadata();
}

void EditorDocument::synchronizeOutdoorGeometryMetadata()
{
    if (m_kind != Kind::Outdoor)
    {
        return;
    }

    normalizeOutdoorGeometryMetadata(m_outdoorGeometryMetadata, m_displayName, m_outdoorGeometry.bmodels.size());
}

void EditorDocument::synchronizeOutdoorTerrainMetadata()
{
    if (m_kind != Kind::Outdoor)
    {
        return;
    }

    normalizeOutdoorTerrainMetadata(
        m_outdoorTerrainMetadata,
        m_displayName,
        m_outdoorGeometry.heightMap,
        m_outdoorGeometry.tileMap,
        m_outdoorGeometry.attributeMap);
    m_outdoorTerrainMetadata.heightMap = m_outdoorGeometry.heightMap;
    m_outdoorTerrainMetadata.tileMap = m_outdoorGeometry.tileMap;
    m_outdoorTerrainMetadata.attributeMap = m_outdoorGeometry.attributeMap;
}

bool EditorDocument::loadOutdoorSceneText(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneVirtualPath,
    const std::string &sceneText,
    const std::optional<EditorOutdoorMapPackageMetadata> &packageMetadata,
    const std::optional<std::string> &packageVirtualPath,
    std::string &errorMessage)
{
    Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<Game::OutdoorSceneData> sceneData = sceneLoader.loadFromText(sceneText, errorMessage);

    if (!sceneData)
    {
        return false;
    }

    const std::filesystem::path developmentRoot = assetFileSystem.getDevelopmentRoot();
    const std::filesystem::path editorDevelopmentRoot = assetFileSystem.getEditorDevelopmentRoot();
    const std::filesystem::path scenePhysicalPath =
        assetFileSystem.resolvePhysicalPath(sceneVirtualPath).value_or(
            scenePhysicalPathFromVirtual(editorDevelopmentRoot, sceneVirtualPath));
    std::filesystem::path geometryPath = std::filesystem::path(sceneVirtualPath).parent_path() / sceneData->geometryFile;
    const std::string geometryMetadataVirtualPath =
        packageMetadata
            ? (std::filesystem::path(sceneVirtualPath).parent_path() / packageMetadata->geometryMetadataFile).generic_string()
            : (std::filesystem::path(sceneVirtualPath).parent_path()
                / deriveGeometryMetadataPathForScenePath(scenePhysicalPath).filename()).generic_string();
    const std::string terrainMetadataVirtualPath =
        packageMetadata
            ? (std::filesystem::path(sceneVirtualPath).parent_path() / packageMetadata->terrainMetadataFile).generic_string()
            : (std::filesystem::path(sceneVirtualPath).parent_path()
                / deriveTerrainMetadataPathForScenePath(scenePhysicalPath).filename()).generic_string();
    const std::optional<std::string> geometryMetadataText = assetFileSystem.readTextFile(geometryMetadataVirtualPath);
    const std::optional<std::string> terrainMetadataText = assetFileSystem.readTextFile(terrainMetadataVirtualPath);

    std::optional<EditorOutdoorGeometryMetadata> geometryMetadata;

    if (geometryMetadataText)
    {
        geometryMetadata = loadOutdoorGeometryMetadataFromText(*geometryMetadataText, errorMessage);

        if (!geometryMetadata)
        {
            return false;
        }
    }

    std::optional<EditorOutdoorTerrainMetadata> terrainMetadata;

    if (terrainMetadataText)
    {
        terrainMetadata = loadOutdoorTerrainMetadataFromText(*terrainMetadataText, errorMessage);

        if (!terrainMetadata)
        {
            return false;
        }
    }

    std::optional<std::vector<uint8_t>> geometryBytes = assetFileSystem.readBinaryFile(geometryPath.generic_string());
    std::optional<Game::OutdoorMapData> outdoorGeometry;

    if (geometryBytes)
    {
        Game::OutdoorMapDataLoader geometryLoader = {};
        outdoorGeometry = geometryLoader.loadFromBytes(*geometryBytes);

        if (!outdoorGeometry)
        {
            errorMessage = "could not parse outdoor geometry: " + geometryPath.generic_string();
            return false;
        }
    }
    else if (packageMetadata)
    {
        outdoorGeometry = buildOutdoorGeometryFromSourcePackage(
            assetFileSystem,
            *sceneData,
            geometryMetadata,
            terrainMetadata,
            errorMessage);

        if (!outdoorGeometry)
        {
            if (errorMessage.empty())
            {
                errorMessage = "could not rebuild outdoor geometry from source package";
            }

            return false;
        }
    }
    else
    {
        errorMessage = "could not read outdoor geometry: " + geometryPath.generic_string();
        return false;
    }

    m_kind = Kind::Outdoor;
    m_isDirty = false;
    m_isRuntimeBuildDirty = false;
    m_developmentRoot = developmentRoot;
    m_editorDevelopmentRoot = editorDevelopmentRoot;
    m_outdoorGeometry = *outdoorGeometry;
    m_outdoorGeometrySourceBytes = geometryBytes.value_or(std::vector<uint8_t>{});
    m_outdoorSceneData = *sceneData;
    m_indoorGeometry = {};
    m_indoorGeometrySourceBytes.clear();
    m_indoorSceneData = {};
    m_hasIndoorGeometryMetadata = false;
    m_indoorGeometryMetadata = {};
    ++m_sceneRevision;
    m_sceneVirtualPath = sceneVirtualPath;
    m_scenePhysicalPath = scenePhysicalPath;
    m_geometryVirtualPath = geometryPath.generic_string();
    m_geometryPhysicalPath = assetFileSystem.resolvePhysicalPath(m_geometryVirtualPath).value_or(std::filesystem::path());
    m_geometryMetadataVirtualPath = geometryMetadataVirtualPath;
    m_geometryMetadataPhysicalPath =
        assetFileSystem.resolvePhysicalPath(m_geometryMetadataVirtualPath).value_or(std::filesystem::path());
    m_hasMapPackageRoot = packageMetadata.has_value();
    m_mapPackageVirtualPath =
        packageVirtualPath
            ? *packageVirtualPath
            : (std::filesystem::path(sceneVirtualPath).parent_path()
                / deriveMapPackagePathForScenePath(m_scenePhysicalPath).filename()).generic_string();
    m_mapPackagePhysicalPath = assetFileSystem.resolvePhysicalPath(m_mapPackageVirtualPath).value_or(std::filesystem::path());
    m_terrainMetadataVirtualPath = terrainMetadataVirtualPath;
    m_terrainMetadataPhysicalPath =
        assetFileSystem.resolvePhysicalPath(m_terrainMetadataVirtualPath).value_or(std::filesystem::path());
    m_displayName = sceneData->geometryFile;
    m_outdoorMapPackageMetadata = packageMetadata.value_or(EditorOutdoorMapPackageMetadata{});
    m_outdoorGeometryMetadata = geometryMetadata.value_or(EditorOutdoorGeometryMetadata{});
    m_outdoorTerrainMetadata = terrainMetadata.value_or(EditorOutdoorTerrainMetadata{});

    synchronizeOutdoorGeometryMetadata();

    if (terrainMetadataText)
    {
        normalizeOutdoorTerrainMetadata(
            m_outdoorTerrainMetadata,
            m_displayName,
            m_outdoorGeometry.heightMap,
            m_outdoorGeometry.tileMap,
            m_outdoorGeometry.attributeMap);
        m_outdoorGeometry.heightMap = m_outdoorTerrainMetadata.heightMap;
        m_outdoorGeometry.tileMap = m_outdoorTerrainMetadata.tileMap;
        m_outdoorGeometry.attributeMap = m_outdoorTerrainMetadata.attributeMap;
    }
    else
    {
        synchronizeOutdoorTerrainMetadata();
    }

    const std::string sourceFingerprint = currentSourcePackageFingerprint();
    normalizeOutdoorMapPackageMetadata(
        m_outdoorMapPackageMetadata,
        deriveOutdoorMapPackageId(sceneData->geometryFile),
        deriveOutdoorMapPackageDisplayName(sceneData->geometryFile),
        sceneData->geometryFile,
        m_scenePhysicalPath.filename().string(),
        m_geometryMetadataPhysicalPath.filename().string(),
        m_terrainMetadataPhysicalPath.filename().string(),
        deriveDefaultScriptModuleForMapFile(sceneData->geometryFile),
        sourceFingerprint,
        m_hasMapPackageRoot ? m_outdoorMapPackageMetadata.builtSourceFingerprint : sourceFingerprint);
    m_isRuntimeBuildDirty = (m_outdoorMapPackageMetadata.builtSourceFingerprint != sourceFingerprint);
    return true;
}

bool EditorDocument::loadIndoorSceneText(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sceneVirtualPath,
    const std::string &sceneText,
    std::string &errorMessage)
{
    Game::IndoorSceneYmlLoader sceneLoader = {};
    const std::optional<Game::IndoorSceneData> sceneData = sceneLoader.loadFromText(sceneText, errorMessage);

    if (!sceneData)
    {
        return false;
    }

    const std::filesystem::path developmentRoot = assetFileSystem.getDevelopmentRoot();
    const std::filesystem::path editorDevelopmentRoot = assetFileSystem.getEditorDevelopmentRoot();
    const std::filesystem::path scenePhysicalPath =
        assetFileSystem.resolvePhysicalPath(sceneVirtualPath).value_or(
            scenePhysicalPathFromVirtual(editorDevelopmentRoot, sceneVirtualPath));
    const std::filesystem::path geometryPath =
        std::filesystem::path(sceneVirtualPath).parent_path() / sceneData->geometryFile;
    const std::string geometryMetadataVirtualPath =
        deriveGeometryMetadataPathForScenePath(std::filesystem::path(sceneVirtualPath)).generic_string();
    const std::optional<std::string> geometryMetadataText =
        assetFileSystem.exists(geometryMetadataVirtualPath)
            ? assetFileSystem.readTextFile(geometryMetadataVirtualPath)
            : std::nullopt;
    const std::optional<std::vector<uint8_t>> geometryBytes =
        assetFileSystem.readBinaryFile(geometryPath.generic_string());

    if (!geometryBytes)
    {
        errorMessage = "could not read indoor geometry: " + geometryPath.generic_string();
        return false;
    }

    Game::IndoorMapDataLoader geometryLoader = {};
    const std::optional<Game::IndoorMapData> indoorGeometry = geometryLoader.loadFromBytes(*geometryBytes);

    if (!indoorGeometry)
    {
        errorMessage = "could not parse indoor geometry: " + geometryPath.generic_string();
        return false;
    }

    std::optional<EditorIndoorGeometryMetadata> geometryMetadata;

    if (geometryMetadataText)
    {
        geometryMetadata = loadIndoorGeometryMetadataFromText(*geometryMetadataText, errorMessage);

        if (!geometryMetadata)
        {
            return false;
        }

        normalizeIndoorGeometryMetadata(*geometryMetadata, sceneData->geometryFile);
    }

    Game::IndoorSceneData normalizedSceneData = *sceneData;
    synthesizeIndoorFaceAttributeOverridesFromLegacyCompanion(
        assetFileSystem,
        scenePhysicalPath,
        sceneVirtualPath,
        *indoorGeometry,
        normalizedSceneData);

    m_kind = Kind::Indoor;
    m_isDirty = false;
    m_isRuntimeBuildDirty = false;
    m_developmentRoot = developmentRoot;
    m_editorDevelopmentRoot = editorDevelopmentRoot;
    m_outdoorGeometry = {};
    m_outdoorSceneData = {};
    m_outdoorGeometryMetadata = {};
    m_outdoorMapPackageMetadata = {};
    m_outdoorTerrainMetadata = {};
    m_outdoorGeometrySourceBytes.clear();
    m_indoorGeometry = *indoorGeometry;
    m_indoorGeometrySourceBytes = *geometryBytes;
    m_indoorSceneData = std::move(normalizedSceneData);
    m_hasIndoorGeometryMetadata = geometryMetadataText.has_value();
    m_indoorGeometryMetadata = geometryMetadata.value_or(EditorIndoorGeometryMetadata{});
    normalizeIndoorGeometryMetadata(m_indoorGeometryMetadata, sceneData->geometryFile);
    ++m_sceneRevision;
    m_sceneVirtualPath = sceneVirtualPath;
    m_scenePhysicalPath = scenePhysicalPath;
    m_geometryVirtualPath = geometryPath.generic_string();
    m_geometryPhysicalPath = assetFileSystem.resolvePhysicalPath(m_geometryVirtualPath).value_or(std::filesystem::path());
    m_geometryMetadataVirtualPath = geometryMetadataText ? geometryMetadataVirtualPath : std::string();
    m_geometryMetadataPhysicalPath =
        geometryMetadataText
            ? assetFileSystem.resolvePhysicalPath(m_geometryMetadataVirtualPath).value_or(std::filesystem::path())
            : std::filesystem::path();
    m_hasMapPackageRoot = false;
    m_mapPackageVirtualPath.clear();
    m_mapPackagePhysicalPath.clear();
    m_terrainMetadataVirtualPath.clear();
    m_terrainMetadataPhysicalPath.clear();
    m_displayName = sceneData->geometryFile;
    return true;
}

std::string EditorDocument::replaceExtension(const std::string &fileName, const std::string &newExtension)
{
    const std::filesystem::path path(fileName);
    const std::filesystem::path replacedPath =
        path.parent_path() / std::filesystem::path(path.stem().string() + newExtension);
    return replacedPath.generic_string();
}

std::string EditorDocument::deriveGeometryFileNameForScenePath(
    const std::filesystem::path &scenePhysicalPath,
    const std::string &geometryFileName)
{
    const std::filesystem::path sceneFileName = scenePhysicalPath.filename();
    const std::string sceneName = sceneFileName.filename().string();

    if (sceneName.ends_with(".scene.yml"))
    {
        const std::string baseName = sceneName.substr(0, sceneName.size() - std::strlen(".scene.yml"));
        return baseName + std::filesystem::path(geometryFileName).extension().string();
    }

    return geometryFileName;
}

std::filesystem::path EditorDocument::deriveGeometryMetadataPathForScenePath(const std::filesystem::path &scenePhysicalPath)
{
    const std::string sceneName = scenePhysicalPath.filename().string();

    if (sceneName.ends_with(".scene.yml"))
    {
        const std::string baseName = sceneName.substr(0, sceneName.size() - std::strlen(".scene.yml"));
        return scenePhysicalPath.parent_path() / (baseName + ".geometry.yml");
    }

    return scenePhysicalPath.parent_path() / (scenePhysicalPath.stem().string() + ".geometry.yml");
}

std::filesystem::path EditorDocument::deriveMapPackagePathForScenePath(const std::filesystem::path &scenePhysicalPath)
{
    const std::string sceneName = scenePhysicalPath.filename().string();

    if (sceneName.ends_with(".scene.yml"))
    {
        const std::string baseName = sceneName.substr(0, sceneName.size() - std::strlen(".scene.yml"));
        return scenePhysicalPath.parent_path() / (baseName + ".map.yml");
    }

    return scenePhysicalPath.parent_path() / (scenePhysicalPath.stem().string() + ".map.yml");
}

std::string EditorDocument::currentSourcePackageFingerprintForTexts(
    const std::string &sceneText,
    const std::string &geometryMetadataText,
    const std::string &terrainMetadataText,
    const EditorOutdoorMapPackageMetadata &packageMetadata) const
{
    return computeOutdoorMapPackageSourceFingerprint(
        sceneText,
        geometryMetadataText,
        terrainMetadataText,
        serializeOutdoorMapPackageSourceFields(packageMetadata));
}

std::filesystem::path EditorDocument::deriveTerrainMetadataPathForScenePath(const std::filesystem::path &scenePhysicalPath)
{
    const std::string sceneName = scenePhysicalPath.filename().string();

    if (sceneName.ends_with(".scene.yml"))
    {
        const std::string baseName = sceneName.substr(0, sceneName.size() - std::strlen(".scene.yml"));
        return scenePhysicalPath.parent_path() / (baseName + ".terrain.yml");
    }

    return scenePhysicalPath.parent_path() / (scenePhysicalPath.stem().string() + ".terrain.yml");
}

std::string EditorDocument::serializeOutdoorScene(
    const Game::OutdoorSceneData &sceneData,
    const std::optional<std::string> &geometryFileOverride)
{
    YAML::Emitter emitter;
    emitter.SetIndent(2);
    emitter.SetSeqFormat(YAML::Block);
    emitter.SetMapFormat(YAML::Block);

    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << sceneData.formatVersion;
    emitter << YAML::Key << "kind" << YAML::Value << "outdoor_scene";

    emitter << YAML::Key << "source" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "geometry_file" << YAML::Value
            << (geometryFileOverride ? *geometryFileOverride : sceneData.geometryFile);

    if (sceneData.legacyCompanionFile && !sceneData.legacyCompanionFile->empty())
    {
        emitter << YAML::Key << "legacy_companion_file" << YAML::Value << *sceneData.legacyCompanionFile;
    }

    emitter << YAML::EndMap;

    emitter << YAML::Key << "environment" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "sky_texture" << YAML::Value << sceneData.environment.skyTexture;
    emitter << YAML::Key << "ground_tileset_name" << YAML::Value << sceneData.environment.groundTilesetName;
    emitter << YAML::Key << "master_tile" << YAML::Value << static_cast<int>(sceneData.environment.masterTile);
    emitter << YAML::Key << "tile_set_lookup_indices" << YAML::Value;
    emitSequence(emitter, sceneData.environment.tileSetLookupIndices);
    emitter << YAML::Key << "day_bits_raw" << YAML::Value << sceneData.environment.dayBitsRaw;
    emitter << YAML::Key << "map_extra_bits_raw" << YAML::Value << sceneData.environment.mapExtraBitsRaw;

    emitter << YAML::Key << "flags" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "foggy" << YAML::Value << ((sceneData.environment.dayBitsRaw & 0x1) != 0);
    emitter << YAML::Key << "raining" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagRain) != 0);
    emitter << YAML::Key << "snowing" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagSnow) != 0);
    emitter << YAML::Key << "underwater" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagUnderwater) != 0);
    emitter << YAML::Key << "no_terrain" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagNoTerrain) != 0);
    emitter << YAML::Key << "always_dark" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagAlwaysDark) != 0);
    emitter << YAML::Key << "always_light" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagAlwaysLight) != 0);
    emitter << YAML::Key << "always_foggy" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagAlwaysFoggy) != 0);
    emitter << YAML::Key << "red_fog" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagRedFog) != 0);
    emitter << YAML::EndMap;

    emitter << YAML::Key << "fog" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "weak_distance" << YAML::Value << sceneData.environment.fogWeakDistance;
    emitter << YAML::Key << "strong_distance" << YAML::Value << sceneData.environment.fogStrongDistance;
    emitter << YAML::EndMap;
    emitter << YAML::Key << "weather" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "fog_mode" << YAML::Value
            << (sceneData.environment.weather.fogMode == Game::OutdoorFogMode::DailyRandom ? "daily_random" : "static");

    const char *pPrecipitation = "none";

    if (sceneData.environment.weather.precipitation == Game::OutdoorPrecipitationKind::Snow)
    {
        pPrecipitation = "snow";
    }
    else if (sceneData.environment.weather.precipitation == Game::OutdoorPrecipitationKind::Rain)
    {
        pPrecipitation = "rain";
    }

    emitter << YAML::Key << "precipitation" << YAML::Value << pPrecipitation;
    emitter << YAML::Key << "daily_fog" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "small_chance" << YAML::Value << sceneData.environment.weather.smallFogChance;
    emitter << YAML::Key << "average_chance" << YAML::Value << sceneData.environment.weather.averageFogChance;
    emitter << YAML::Key << "dense_chance" << YAML::Value << sceneData.environment.weather.denseFogChance;
    emitter << YAML::Key << "small" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "weak_distance" << YAML::Value << sceneData.environment.weather.smallFog.weakDistance;
    emitter << YAML::Key << "strong_distance" << YAML::Value << sceneData.environment.weather.smallFog.strongDistance;
    emitter << YAML::EndMap;
    emitter << YAML::Key << "average" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "weak_distance" << YAML::Value << sceneData.environment.weather.averageFog.weakDistance;
    emitter << YAML::Key << "strong_distance" << YAML::Value << sceneData.environment.weather.averageFog.strongDistance;
    emitter << YAML::EndMap;
    emitter << YAML::Key << "dense" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "weak_distance" << YAML::Value << sceneData.environment.weather.denseFog.weakDistance;
    emitter << YAML::Key << "strong_distance" << YAML::Value << sceneData.environment.weather.denseFog.strongDistance;
    emitter << YAML::EndMap;
    emitter << YAML::EndMap;
    emitter << YAML::EndMap;
    emitter << YAML::Key << "ceiling" << YAML::Value << sceneData.environment.ceiling;
    emitter << YAML::EndMap;

    emitter << YAML::Key << "terrain" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "attribute_overrides" << YAML::Value << YAML::BeginSeq;

    for (const Game::OutdoorSceneTerrainAttributeOverride &overrideEntry : sceneData.terrainAttributeOverrides)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "x" << YAML::Value << overrideEntry.x;
        emitter << YAML::Key << "y" << YAML::Value << overrideEntry.y;
        emitter << YAML::Key << "legacy_attributes" << YAML::Value
                << static_cast<int>(overrideEntry.legacyAttributes);
        emitter << YAML::Key << "burn" << YAML::Value << ((overrideEntry.legacyAttributes & 0x01) != 0);
        emitter << YAML::Key << "water" << YAML::Value << ((overrideEntry.legacyAttributes & 0x02) != 0);
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;

    emitter << YAML::Key << "bmodel_faces" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "interactive_faces" << YAML::Value << YAML::BeginSeq;

    for (const Game::OutdoorSceneInteractiveFace &interactiveFace : sceneData.interactiveFaces)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "bmodel_index" << YAML::Value << interactiveFace.bmodelIndex;
        emitter << YAML::Key << "face_index" << YAML::Value << interactiveFace.faceIndex;
        emitter << YAML::Key << "legacy_attributes" << YAML::Value << interactiveFace.legacyAttributes;
        emitter << YAML::Key << "cog_number" << YAML::Value << interactiveFace.cogNumber;
        emitter << YAML::Key << "cog_triggered_number" << YAML::Value << interactiveFace.cogTriggeredNumber;
        emitter << YAML::Key << "cog_trigger" << YAML::Value << interactiveFace.cogTrigger;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;

    emitter << YAML::Key << "entities" << YAML::Value << YAML::BeginSeq;

    for (const Game::OutdoorSceneEntity &entity : sceneData.entities)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "entity_index" << YAML::Value << entity.entityIndex;
        emitter << YAML::Key << "name" << YAML::Value << entity.entity.name;
        emitter << YAML::Key << "decoration_list_id" << YAML::Value << entity.entity.decorationListId;
        emitter << YAML::Key << "ai_attributes" << YAML::Value << entity.entity.aiAttributes;
        emitter << YAML::Key << "position" << YAML::Value;
        emitPositionMap(emitter, entity.entity.x, entity.entity.y, entity.entity.z);
        emitter << YAML::Key << "facing" << YAML::Value << entity.entity.facing;
        emitter << YAML::Key << "event_id_primary" << YAML::Value << entity.entity.eventIdPrimary;
        emitter << YAML::Key << "event_id_secondary" << YAML::Value << entity.entity.eventIdSecondary;
        emitter << YAML::Key << "variable_primary" << YAML::Value << entity.entity.variablePrimary;
        emitter << YAML::Key << "variable_secondary" << YAML::Value << entity.entity.variableSecondary;
        emitter << YAML::Key << "special_trigger" << YAML::Value << entity.entity.specialTrigger;
        emitter << YAML::Key << "initial_decoration_flag" << YAML::Value << entity.initialDecorationFlag;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;

    emitter << YAML::Key << "spawns" << YAML::Value << YAML::BeginSeq;

    for (const Game::OutdoorSceneSpawn &spawn : sceneData.spawns)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "spawn_index" << YAML::Value << spawn.spawnIndex;
        emitter << YAML::Key << "position" << YAML::Value;
        emitPositionMap(emitter, spawn.spawn.x, spawn.spawn.y, spawn.spawn.z);
        emitter << YAML::Key << "radius" << YAML::Value << spawn.spawn.radius;
        emitter << YAML::Key << "type_id" << YAML::Value << spawn.spawn.typeId;
        emitter << YAML::Key << "index" << YAML::Value << spawn.spawn.index;
        emitter << YAML::Key << "attributes" << YAML::Value << spawn.spawn.attributes;
        emitter << YAML::Key << "group" << YAML::Value << spawn.spawn.group;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;

    emitter << YAML::Key << "initial_state" << YAML::Value << YAML::BeginMap;

    emitter << YAML::Key << "location" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "respawn_count" << YAML::Value << sceneData.initialState.locationInfo.respawnCount;
    emitter << YAML::Key << "last_respawn_day" << YAML::Value << sceneData.initialState.locationInfo.lastRespawnDay;
    emitter << YAML::Key << "reputation" << YAML::Value << sceneData.initialState.locationInfo.reputation;
    emitter << YAML::Key << "alert_status" << YAML::Value << sceneData.initialState.locationInfo.alertStatus;
    emitter << YAML::EndMap;

    emitter << YAML::Key << "face_attribute_overrides" << YAML::Value << YAML::BeginSeq;

    for (const Game::OutdoorSceneFaceAttributeOverride &faceOverride : sceneData.initialState.faceAttributeOverrides)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "bmodel_index" << YAML::Value << faceOverride.bmodelIndex;
        emitter << YAML::Key << "face_index" << YAML::Value << faceOverride.faceIndex;
        emitter << YAML::Key << "legacy_attributes" << YAML::Value << faceOverride.legacyAttributes;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;

    emitter << YAML::Key << "actors" << YAML::Value << YAML::BeginSeq;

    for (const Game::MapDeltaActor &actor : sceneData.initialState.actors)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "name" << YAML::Value << actor.name;
        emitter << YAML::Key << "npc_id" << YAML::Value << actor.npcId;
        emitter << YAML::Key << "attributes" << YAML::Value << actor.attributes;
        emitter << YAML::Key << "hp" << YAML::Value << actor.hp;
        emitter << YAML::Key << "hostility_type" << YAML::Value << static_cast<int>(actor.hostilityType);
        emitter << YAML::Key << "monster_info_id" << YAML::Value << actor.monsterInfoId;
        emitter << YAML::Key << "monster_id" << YAML::Value << actor.monsterId;
        emitter << YAML::Key << "radius" << YAML::Value << actor.radius;
        emitter << YAML::Key << "height" << YAML::Value << actor.height;
        emitter << YAML::Key << "move_speed" << YAML::Value << actor.moveSpeed;
        emitter << YAML::Key << "position" << YAML::Value;
        emitPositionMap(emitter, actor.x, actor.y, actor.z);
        emitter << YAML::Key << "sprite_ids" << YAML::Value;
        emitSequence(emitter, actor.spriteIds);
        emitter << YAML::Key << "sector_id" << YAML::Value << actor.sectorId;
        emitter << YAML::Key << "current_action_animation" << YAML::Value << actor.currentActionAnimation;
        emitter << YAML::Key << "group" << YAML::Value << actor.group;
        emitter << YAML::Key << "ally" << YAML::Value << actor.ally;
        emitter << YAML::Key << "unique_name_index" << YAML::Value << actor.uniqueNameIndex;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;

    emitter << YAML::Key << "sprite_objects" << YAML::Value << YAML::BeginSeq;

    for (const Game::MapDeltaSpriteObject &spriteObject : sceneData.initialState.spriteObjects)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "sprite_id" << YAML::Value << spriteObject.spriteId;
        emitter << YAML::Key << "object_description_id" << YAML::Value << spriteObject.objectDescriptionId;
        emitter << YAML::Key << "position" << YAML::Value;
        emitPositionMap(emitter, spriteObject.x, spriteObject.y, spriteObject.z);
        emitter << YAML::Key << "velocity" << YAML::Value;
        emitPositionMap(emitter, spriteObject.velocityX, spriteObject.velocityY, spriteObject.velocityZ);
        emitter << YAML::Key << "yaw_angle" << YAML::Value << spriteObject.yawAngle;
        emitter << YAML::Key << "sound_id" << YAML::Value << spriteObject.soundId;
        emitter << YAML::Key << "attributes" << YAML::Value << spriteObject.attributes;
        emitter << YAML::Key << "sector_id" << YAML::Value << spriteObject.sectorId;
        emitter << YAML::Key << "time_since_created" << YAML::Value << spriteObject.timeSinceCreated;
        emitter << YAML::Key << "temporary_lifetime" << YAML::Value << spriteObject.temporaryLifetime;
        emitter << YAML::Key << "glow_radius_multiplier" << YAML::Value << spriteObject.glowRadiusMultiplier;
        emitter << YAML::Key << "spell_id" << YAML::Value << spriteObject.spellId;
        emitter << YAML::Key << "spell_level" << YAML::Value << spriteObject.spellLevel;
        emitter << YAML::Key << "spell_skill" << YAML::Value << spriteObject.spellSkill;
        emitter << YAML::Key << "field54" << YAML::Value << spriteObject.field54;
        emitter << YAML::Key << "spell_caster_pid" << YAML::Value << spriteObject.spellCasterPid;
        emitter << YAML::Key << "spell_target_pid" << YAML::Value << spriteObject.spellTargetPid;
        emitter << YAML::Key << "lod_distance" << YAML::Value << static_cast<int>(spriteObject.lodDistance);
        emitter << YAML::Key << "spell_caster_ability" << YAML::Value
                << static_cast<int>(spriteObject.spellCasterAbility);
        emitter << YAML::Key << "initial_position" << YAML::Value;
        emitPositionMap(emitter, spriteObject.initialX, spriteObject.initialY, spriteObject.initialZ);
        emitter << YAML::Key << "raw_containing_item_hex" << YAML::Value;
        emitter << bytesToUpperHex(spriteObject.rawContainingItem);
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;

    emitter << YAML::Key << "chests" << YAML::Value << YAML::BeginSeq;

    for (const Game::MapDeltaChest &chest : sceneData.initialState.chests)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "chest_type_id" << YAML::Value << chest.chestTypeId;
        emitter << YAML::Key << "flags" << YAML::Value << chest.flags;
        emitter << YAML::Key << "raw_items_hex" << YAML::Value << bytesToUpperHex(chest.rawItems);
        emitter << YAML::Key << "inventory_matrix" << YAML::Value;
        emitSequence(emitter, chest.inventoryMatrix);
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;

    emitter << YAML::Key << "variables" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "map" << YAML::Value;
    emitIntegerSequence(emitter, sceneData.initialState.eventVariables.mapVars);
    emitter << YAML::Key << "decor" << YAML::Value;
    emitIntegerSequence(emitter, sceneData.initialState.eventVariables.decorVars);
    emitter << YAML::EndMap;

    emitter << YAML::EndMap;
    emitter << YAML::EndMap;

    std::string text = emitter.c_str();

    if (!text.empty() && text.back() != '\n')
    {
        text.push_back('\n');
    }

    return text;
}

std::string EditorDocument::serializeIndoorScene(
    const Game::IndoorSceneData &sceneData,
    const std::optional<std::string> &geometryFileOverride)
{
    YAML::Emitter emitter;
    emitter.SetIndent(2);
    emitter.SetSeqFormat(YAML::Block);
    emitter.SetMapFormat(YAML::Block);

    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << sceneData.formatVersion;
    emitter << YAML::Key << "kind" << YAML::Value << "indoor_scene";

    emitter << YAML::Key << "source" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "geometry_file" << YAML::Value
            << (geometryFileOverride ? *geometryFileOverride : sceneData.geometryFile);

    if (sceneData.legacyCompanionFile && !sceneData.legacyCompanionFile->empty())
    {
        emitter << YAML::Key << "legacy_companion_file" << YAML::Value << *sceneData.legacyCompanionFile;
    }

    emitter << YAML::EndMap;

    emitter << YAML::Key << "environment" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "sky_texture" << YAML::Value << sceneData.environment.skyTexture;
    emitter << YAML::Key << "day_bits_raw" << YAML::Value << sceneData.environment.dayBitsRaw;
    emitter << YAML::Key << "map_extra_bits_raw" << YAML::Value << sceneData.environment.mapExtraBitsRaw;
    emitter << YAML::Key << "flags" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "foggy" << YAML::Value << ((sceneData.environment.dayBitsRaw & 0x1) != 0);
    emitter << YAML::Key << "raining" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagRain) != 0);
    emitter << YAML::Key << "snowing" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagSnow) != 0);
    emitter << YAML::Key << "underwater" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagUnderwater) != 0);
    emitter << YAML::Key << "no_terrain" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagNoTerrain) != 0);
    emitter << YAML::Key << "always_dark" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagAlwaysDark) != 0);
    emitter << YAML::Key << "always_light" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagAlwaysLight) != 0);
    emitter << YAML::Key << "always_foggy" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagAlwaysFoggy) != 0);
    emitter << YAML::Key << "red_fog" << YAML::Value
            << ((sceneData.environment.mapExtraBitsRaw & EnvironmentFlagRedFog) != 0);
    emitter << YAML::EndMap;
    emitter << YAML::Key << "fog" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "weak_distance" << YAML::Value << sceneData.environment.fogWeakDistance;
    emitter << YAML::Key << "strong_distance" << YAML::Value << sceneData.environment.fogStrongDistance;
    emitter << YAML::EndMap;
    emitter << YAML::Key << "ceiling" << YAML::Value << sceneData.environment.ceiling;
    emitter << YAML::EndMap;

    emitter << YAML::Key << "initial_state" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "location" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "respawn_count" << YAML::Value << sceneData.initialState.locationInfo.respawnCount;
    emitter << YAML::Key << "last_respawn_day" << YAML::Value << sceneData.initialState.locationInfo.lastRespawnDay;
    emitter << YAML::Key << "reputation" << YAML::Value << sceneData.initialState.locationInfo.reputation;
    emitter << YAML::Key << "alert_status" << YAML::Value << sceneData.initialState.locationInfo.alertStatus;
    emitter << YAML::EndMap;

    emitter << YAML::Key << "visible_outlines" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "bitset_hex" << YAML::Value << bytesToUpperHex(sceneData.initialState.visibleOutlines);
    emitter << YAML::EndMap;

    emitter << YAML::Key << "face_attribute_overrides" << YAML::Value << YAML::BeginSeq;

    for (const Game::IndoorSceneFaceAttributeOverride &faceOverride : sceneData.initialState.faceAttributeOverrides)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "face_index" << YAML::Value << faceOverride.faceIndex;

        if (faceOverride.legacyAttributes.has_value())
        {
            emitter << YAML::Key << "legacy_attributes" << YAML::Value << *faceOverride.legacyAttributes;
        }

        if (faceOverride.textureFrameTableCog.has_value())
        {
            emitter << YAML::Key << "texture_frame_table_cog" << YAML::Value << *faceOverride.textureFrameTableCog;
        }

        if (faceOverride.cogNumber.has_value())
        {
            emitter << YAML::Key << "cog_number" << YAML::Value << *faceOverride.cogNumber;
        }

        if (faceOverride.cogTriggered.has_value())
        {
            emitter << YAML::Key << "cog_triggered" << YAML::Value << *faceOverride.cogTriggered;
        }

        if (faceOverride.cogTriggerType.has_value())
        {
            emitter << YAML::Key << "cog_trigger_type" << YAML::Value << *faceOverride.cogTriggerType;
        }

        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "decoration_flags" << YAML::Value << YAML::BeginSeq;

    for (const Game::IndoorSceneDecorationFlag &flag : sceneData.initialState.decorationFlags)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "entity_index" << YAML::Value << flag.entityIndex;
        emitter << YAML::Key << "flag" << YAML::Value << flag.flag;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "actors" << YAML::Value << YAML::BeginSeq;

    for (const Game::MapDeltaActor &actor : sceneData.initialState.actors)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "name" << YAML::Value << actor.name;
        emitter << YAML::Key << "npc_id" << YAML::Value << actor.npcId;
        emitter << YAML::Key << "attributes" << YAML::Value << actor.attributes;
        emitter << YAML::Key << "hp" << YAML::Value << actor.hp;
        emitter << YAML::Key << "hostility_type" << YAML::Value << static_cast<int>(actor.hostilityType);
        emitter << YAML::Key << "monster_info_id" << YAML::Value << actor.monsterInfoId;
        emitter << YAML::Key << "monster_id" << YAML::Value << actor.monsterId;
        emitter << YAML::Key << "radius" << YAML::Value << actor.radius;
        emitter << YAML::Key << "height" << YAML::Value << actor.height;
        emitter << YAML::Key << "move_speed" << YAML::Value << actor.moveSpeed;
        emitter << YAML::Key << "position" << YAML::Value;
        emitPositionMap(emitter, actor.x, actor.y, actor.z);
        emitter << YAML::Key << "sprite_ids" << YAML::Value;
        emitSequence(emitter, actor.spriteIds);
        emitter << YAML::Key << "sector_id" << YAML::Value << actor.sectorId;
        emitter << YAML::Key << "current_action_animation" << YAML::Value << actor.currentActionAnimation;
        emitter << YAML::Key << "group" << YAML::Value << actor.group;
        emitter << YAML::Key << "ally" << YAML::Value << actor.ally;
        emitter << YAML::Key << "unique_name_index" << YAML::Value << actor.uniqueNameIndex;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "sprite_objects" << YAML::Value << YAML::BeginSeq;

    for (const Game::MapDeltaSpriteObject &spriteObject : sceneData.initialState.spriteObjects)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "sprite_id" << YAML::Value << spriteObject.spriteId;
        emitter << YAML::Key << "object_description_id" << YAML::Value << spriteObject.objectDescriptionId;
        emitter << YAML::Key << "position" << YAML::Value;
        emitPositionMap(emitter, spriteObject.x, spriteObject.y, spriteObject.z);
        emitter << YAML::Key << "velocity" << YAML::Value;
        emitPositionMap(emitter, spriteObject.velocityX, spriteObject.velocityY, spriteObject.velocityZ);
        emitter << YAML::Key << "yaw_angle" << YAML::Value << spriteObject.yawAngle;
        emitter << YAML::Key << "sound_id" << YAML::Value << spriteObject.soundId;
        emitter << YAML::Key << "attributes" << YAML::Value << spriteObject.attributes;
        emitter << YAML::Key << "sector_id" << YAML::Value << spriteObject.sectorId;
        emitter << YAML::Key << "time_since_created" << YAML::Value << spriteObject.timeSinceCreated;
        emitter << YAML::Key << "temporary_lifetime" << YAML::Value << spriteObject.temporaryLifetime;
        emitter << YAML::Key << "glow_radius_multiplier" << YAML::Value << spriteObject.glowRadiusMultiplier;
        emitter << YAML::Key << "spell_id" << YAML::Value << spriteObject.spellId;
        emitter << YAML::Key << "spell_level" << YAML::Value << spriteObject.spellLevel;
        emitter << YAML::Key << "spell_skill" << YAML::Value << spriteObject.spellSkill;
        emitter << YAML::Key << "field54" << YAML::Value << spriteObject.field54;
        emitter << YAML::Key << "spell_caster_pid" << YAML::Value << spriteObject.spellCasterPid;
        emitter << YAML::Key << "spell_target_pid" << YAML::Value << spriteObject.spellTargetPid;
        emitter << YAML::Key << "lod_distance" << YAML::Value << static_cast<int>(spriteObject.lodDistance);
        emitter << YAML::Key << "spell_caster_ability" << YAML::Value
                << static_cast<int>(spriteObject.spellCasterAbility);
        emitter << YAML::Key << "initial_position" << YAML::Value;
        emitPositionMap(emitter, spriteObject.initialX, spriteObject.initialY, spriteObject.initialZ);
        emitter << YAML::Key << "raw_containing_item_hex" << YAML::Value << bytesToUpperHex(spriteObject.rawContainingItem);
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "chests" << YAML::Value << YAML::BeginSeq;

    for (const Game::MapDeltaChest &chest : sceneData.initialState.chests)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "chest_type_id" << YAML::Value << chest.chestTypeId;
        emitter << YAML::Key << "flags" << YAML::Value << chest.flags;
        emitter << YAML::Key << "raw_items_hex" << YAML::Value << bytesToUpperHex(chest.rawItems);
        emitter << YAML::Key << "inventory_matrix" << YAML::Value;
        emitSequence(emitter, chest.inventoryMatrix);
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "doors" << YAML::Value << YAML::BeginSeq;

    for (const Game::IndoorSceneDoor &door : sceneData.initialState.doors)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "door_index" << YAML::Value << door.doorIndex;
        emitter << YAML::Key << "legacy_attributes" << YAML::Value << door.door.attributes;
        emitter << YAML::Key << "door_id" << YAML::Value << door.door.doorId;
        emitter << YAML::Key << "time_since_triggered_ms" << YAML::Value << door.door.timeSinceTriggered;
        emitter << YAML::Key << "move_length" << YAML::Value << door.door.moveLength;
        emitter << YAML::Key << "open_speed" << YAML::Value << door.door.openSpeed;
        emitter << YAML::Key << "close_speed" << YAML::Value << door.door.closeSpeed;
        emitter << YAML::Key << "state" << YAML::Value << door.door.state;
        emitter << YAML::Key << "direction" << YAML::Value;
        emitPositionMap(emitter, door.door.directionX, door.door.directionY, door.door.directionZ);
        emitter << YAML::Key << "vertex_ids" << YAML::Value;
        emitSequence(emitter, door.door.vertexIds);
        emitter << YAML::Key << "face_ids" << YAML::Value;
        emitSequence(emitter, door.door.faceIds);
        emitter << YAML::Key << "sector_ids" << YAML::Value;
        emitSequence(emitter, door.door.sectorIds);
        emitter << YAML::Key << "delta_us" << YAML::Value;
        emitSequence(emitter, door.door.deltaUs);
        emitter << YAML::Key << "delta_vs" << YAML::Value;
        emitSequence(emitter, door.door.deltaVs);
        emitter << YAML::Key << "x_offsets" << YAML::Value;
        emitSequence(emitter, door.door.xOffsets);
        emitter << YAML::Key << "y_offsets" << YAML::Value;
        emitSequence(emitter, door.door.yOffsets);
        emitter << YAML::Key << "z_offsets" << YAML::Value;
        emitSequence(emitter, door.door.zOffsets);
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "variables" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "map" << YAML::Value;
    emitIntegerSequence(emitter, sceneData.initialState.eventVariables.mapVars);
    emitter << YAML::Key << "decor" << YAML::Value;
    emitIntegerSequence(emitter, sceneData.initialState.eventVariables.decorVars);
    emitter << YAML::EndMap;
    emitter << YAML::EndMap;
    emitter << YAML::EndMap;

    std::string text = emitter.c_str();

    if (!text.empty() && text.back() != '\n')
    {
        text.push_back('\n');
    }

    return text;
}

bool EditorDocument::writeTextFileAtomically(
    const std::filesystem::path &path,
    const std::string &text,
    std::string &errorMessage)
{
    try
    {
        std::filesystem::create_directories(path.parent_path());
        const std::filesystem::path temporaryPath = path.string() + ".tmp";

        {
            std::ofstream outputStream(temporaryPath, std::ios::binary | std::ios::trunc);

            if (!outputStream)
            {
                errorMessage = "could not open file for writing: " + temporaryPath.string();
                return false;
            }

            outputStream.write(text.data(), static_cast<std::streamsize>(text.size()));

            if (!outputStream)
            {
                errorMessage = "could not write file: " + temporaryPath.string();
                return false;
            }
        }

        std::filesystem::copy_file(
            temporaryPath,
            path,
            std::filesystem::copy_options::overwrite_existing);
        std::filesystem::remove(temporaryPath);
        return true;
    }

    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }
}

bool EditorDocument::writeBinaryFileAtomically(
    const std::filesystem::path &path,
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage)
{
    try
    {
        std::filesystem::create_directories(path.parent_path());
        const std::filesystem::path tempPath = path.string() + ".tmp";
        std::ofstream output(tempPath, std::ios::binary | std::ios::trunc);

        if (!output)
        {
            errorMessage = "could not open file for writing: " + tempPath.string();
            return false;
        }

        output.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));

        if (!output.good())
        {
            errorMessage = "could not write file: " + tempPath.string();
            return false;
        }

        output.close();

        std::filesystem::copy_file(
            tempPath,
            path,
            std::filesystem::copy_options::overwrite_existing);
        std::filesystem::remove(tempPath);
        return true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }
}
}
