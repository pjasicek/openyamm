#include "editor/headless/EditorHeadlessDiagnostics.h"

#include "editor/document/EditorSession.h"
#include "editor/document/EditorDocument.h"
#include "editor/import/IndoorSourceGeometryCompiler.h"
#include "engine/AssetFileSystem.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/MapDeltaData.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Editor
{
namespace
{
constexpr size_t ChestItemRecordSize = 36;
constexpr size_t ChestItemRecordCount = 140;

bool nearlyEqualFloat(float left, float right, float epsilon = 0.001f)
{
    return std::fabs(left - right) <= epsilon;
}

bool containsDiagnosticSubstring(const std::vector<std::string> &diagnostics, const std::string &substring)
{
    for (const std::string &diagnostic : diagnostics)
    {
        if (diagnostic.find(substring) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

std::filesystem::path activeWorldEditorPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::filesystem::path &relativePath)
{
    return assetFileSystem.getEditorDevelopmentRoot()
        / std::filesystem::path("worlds")
        / assetFileSystem.getActiveWorldId()
        / relativePath;
}

std::filesystem::path activeWorldDevelopmentPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::filesystem::path &relativePath)
{
    return assetFileSystem.getDevelopmentRoot()
        / std::filesystem::path("worlds")
        / assetFileSystem.getActiveWorldId()
        / relativePath;
}

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

void appendBytes(std::vector<uint8_t> &bytes, const void *pData, size_t size)
{
    const uint8_t *pByteData = static_cast<const uint8_t *>(pData);
    bytes.insert(bytes.end(), pByteData, pByteData + size);
}

void appendPaddingBytes(std::vector<uint8_t> &bytes, size_t alignment, uint8_t value)
{
    const size_t remainder = bytes.size() % alignment;

    if (remainder == 0)
    {
        return;
    }

    bytes.insert(bytes.end(), alignment - remainder, value);
}

bool readBinaryFileBytes(const std::filesystem::path &path, std::vector<uint8_t> &bytes)
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
    return input.read(reinterpret_cast<char *>(bytes.data()), size).good();
}

bool readTextFileContents(const std::filesystem::path &path, std::string &text)
{
    text.clear();
    std::ifstream input(path);

    if (!input)
    {
        return false;
    }

    text.assign(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
    return true;
}

bool writeGlbFile(
    const std::filesystem::path &path,
    const std::string &json,
    const std::vector<uint8_t> &binaryChunk)
{
    std::vector<uint8_t> jsonBytes(json.begin(), json.end());
    appendPaddingBytes(jsonBytes, 4, ' ');

    std::vector<uint8_t> binBytes = binaryChunk;
    appendPaddingBytes(binBytes, 4, 0);

    const uint32_t magic = 0x46546c67;
    const uint32_t version = 2;
    const uint32_t jsonChunkType = 0x4e4f534a;
    const uint32_t binChunkType = 0x004e4942;
    const uint32_t totalLength =
        12u
        + 8u + static_cast<uint32_t>(jsonBytes.size())
        + 8u + static_cast<uint32_t>(binBytes.size());
    const uint32_t jsonLength = static_cast<uint32_t>(jsonBytes.size());
    const uint32_t binLength = static_cast<uint32_t>(binBytes.size());

    std::ofstream output(path, std::ios::binary | std::ios::trunc);

    if (!output)
    {
        return false;
    }

    output.write(reinterpret_cast<const char *>(&magic), sizeof(magic));
    output.write(reinterpret_cast<const char *>(&version), sizeof(version));
    output.write(reinterpret_cast<const char *>(&totalLength), sizeof(totalLength));
    output.write(reinterpret_cast<const char *>(&jsonLength), sizeof(jsonLength));
    output.write(reinterpret_cast<const char *>(&jsonChunkType), sizeof(jsonChunkType));
    output.write(reinterpret_cast<const char *>(jsonBytes.data()), static_cast<std::streamsize>(jsonBytes.size()));
    output.write(reinterpret_cast<const char *>(&binLength), sizeof(binLength));
    output.write(reinterpret_cast<const char *>(&binChunkType), sizeof(binChunkType));
    output.write(reinterpret_cast<const char *>(binBytes.data()), static_cast<std::streamsize>(binBytes.size()));
    return output.good();
}

void appendNormalizedPosition(std::ostringstream &stream, int x, int y, int z)
{
    stream << x << ',' << y << ',' << z;
}

std::string buildNormalizedOutdoorAuthoredSnapshot(
    const OpenYAMM::Game::OutdoorMapData &outdoorMapData,
    const OpenYAMM::Game::MapDeltaData &mapDeltaData)
{
    std::ostringstream stream;

    const std::string effectiveSkyTexture =
        !mapDeltaData.locationTime.skyTextureName.empty()
        ? mapDeltaData.locationTime.skyTextureName
        : outdoorMapData.skyTexture;
    uint32_t mapExtraBitsRaw = 0;
    int32_t ceiling = 0;

    if (mapDeltaData.locationTime.reserved.size() >= sizeof(mapExtraBitsRaw) + sizeof(ceiling))
    {
        std::memcpy(&mapExtraBitsRaw, mapDeltaData.locationTime.reserved.data(), sizeof(mapExtraBitsRaw));
        std::memcpy(
            &ceiling,
            mapDeltaData.locationTime.reserved.data() + sizeof(mapExtraBitsRaw),
            sizeof(ceiling));
    }

    stream << "environment\n";
    stream << "sky_texture=" << effectiveSkyTexture << '\n';
    stream << "ground_tileset_name=" << outdoorMapData.groundTilesetName << '\n';
    stream << "master_tile=" << static_cast<int>(outdoorMapData.masterTile) << '\n';
    stream << "tile_set_lookup_indices="
           << outdoorMapData.tileSetLookupIndices[0] << ','
           << outdoorMapData.tileSetLookupIndices[1] << ','
           << outdoorMapData.tileSetLookupIndices[2] << ','
           << outdoorMapData.tileSetLookupIndices[3] << '\n';
    stream << "day_bits_raw=" << mapDeltaData.locationTime.weatherFlags << '\n';
    stream << "map_extra_bits_raw=" << mapExtraBitsRaw << '\n';
    stream << "fog_weak_distance=" << mapDeltaData.locationTime.fogWeakDistance << '\n';
    stream << "fog_strong_distance=" << mapDeltaData.locationTime.fogStrongDistance << '\n';
    stream << "ceiling=" << ceiling << '\n';

    stream << "terrain\n";
    stream << "height_map_hex=" << bytesToUpperHex(outdoorMapData.heightMap) << '\n';
    stream << "tile_map_hex=" << bytesToUpperHex(outdoorMapData.tileMap) << '\n';

    for (size_t cellIndex = 0; cellIndex < outdoorMapData.attributeMap.size(); ++cellIndex)
    {
        const uint8_t value = outdoorMapData.attributeMap[cellIndex];

        if (value == 0)
        {
            continue;
        }

        const size_t x = cellIndex % OpenYAMM::Game::OutdoorMapData::TerrainWidth;
        const size_t y = cellIndex / OpenYAMM::Game::OutdoorMapData::TerrainWidth;
        stream << x << ',' << y << ',' << static_cast<int>(value)
               << ',' << (((value & 0x01) != 0) ? 1 : 0)
               << ',' << (((value & 0x02) != 0) ? 1 : 0) << '\n';
    }

    stream << "interactive_faces\n";

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OpenYAMM::Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            const OpenYAMM::Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];

            if (face.attributes == 0
                && face.cogNumber == 0
                && face.cogTriggeredNumber == 0
                && face.cogTrigger == 0)
            {
                continue;
            }

            stream << bmodelIndex << ',' << faceIndex << ','
                   << face.attributes << ','
                   << face.cogNumber << ','
                   << face.cogTriggeredNumber << ','
                   << face.cogTrigger << '\n';
        }
    }

    stream << "bmodel_vertices\n";

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OpenYAMM::Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];
        stream << "bmodel=" << bmodelIndex << '\n';

        for (const OpenYAMM::Game::OutdoorBModelVertex &vertex : bmodel.vertices)
        {
            stream << vertex.x << ',' << vertex.y << ',' << vertex.z << '\n';
        }
    }

    stream << "bmodel_face_textures\n";

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OpenYAMM::Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            stream << bmodelIndex << ',' << faceIndex << ',' << bmodel.faces[faceIndex].textureName << '\n';
        }
    }

    stream << "entities\n";

    for (size_t entityIndex = 0; entityIndex < outdoorMapData.entities.size(); ++entityIndex)
    {
        const OpenYAMM::Game::OutdoorEntity &entity = outdoorMapData.entities[entityIndex];
        const uint16_t decorationFlag =
            entityIndex < mapDeltaData.decorationFlags.size()
            ? mapDeltaData.decorationFlags[entityIndex]
            : 0;

        stream << entity.name << '|'
               << entity.decorationListId << '|'
               << entity.aiAttributes << '|';
        appendNormalizedPosition(stream, entity.x, entity.y, entity.z);
        stream << '|'
               << entity.facing << '|'
               << entity.eventIdPrimary << '|'
               << entity.eventIdSecondary << '|'
               << entity.variablePrimary << '|'
               << entity.variableSecondary << '|'
               << entity.specialTrigger << '|'
               << decorationFlag << '\n';
    }

    stream << "spawns\n";

    for (const OpenYAMM::Game::OutdoorSpawn &spawn : outdoorMapData.spawns)
    {
        appendNormalizedPosition(stream, spawn.x, spawn.y, spawn.z);
        stream << '|'
               << spawn.radius << '|'
               << spawn.typeId << '|'
               << spawn.index << '|'
               << spawn.attributes << '|'
               << spawn.group << '\n';
    }

    stream << "location\n";
    stream << mapDeltaData.locationInfo.respawnCount << '|'
           << mapDeltaData.locationInfo.lastRespawnDay << '|'
           << mapDeltaData.locationInfo.reputation << '|'
           << mapDeltaData.locationInfo.alertStatus << '\n';

    stream << "face_attribute_overrides\n";
    size_t flattenedFaceIndex = 0;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OpenYAMM::Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex, ++flattenedFaceIndex)
        {
            const uint32_t baseValue = bmodel.faces[faceIndex].attributes;
            const uint32_t overrideValue =
                flattenedFaceIndex < mapDeltaData.faceAttributes.size()
                ? mapDeltaData.faceAttributes[flattenedFaceIndex]
                : baseValue;

            if (overrideValue == baseValue)
            {
                continue;
            }

            stream << bmodelIndex << ',' << faceIndex << ',' << overrideValue << '\n';
        }
    }

    stream << "actors\n";

    for (const OpenYAMM::Game::MapDeltaActor &actor : mapDeltaData.actors)
    {
        stream << actor.name << '|'
               << actor.npcId << '|'
               << actor.attributes << '|'
               << actor.hp << '|'
               << static_cast<int>(actor.hostilityType) << '|'
               << actor.monsterInfoId << '|'
               << actor.monsterId << '|'
               << actor.radius << '|'
               << actor.height << '|'
               << actor.moveSpeed << '|';
        appendNormalizedPosition(stream, actor.x, actor.y, actor.z);
        stream << '|'
               << actor.spriteIds[0] << ','
               << actor.spriteIds[1] << ','
               << actor.spriteIds[2] << ','
               << actor.spriteIds[3] << '|'
               << actor.sectorId << '|'
               << actor.currentActionAnimation << '|'
               << actor.group << '|'
               << actor.ally << '|'
               << actor.uniqueNameIndex << '\n';
    }

    stream << "sprite_objects\n";

    for (const OpenYAMM::Game::MapDeltaSpriteObject &spriteObject : mapDeltaData.spriteObjects)
    {
        stream << spriteObject.spriteId << '|'
               << spriteObject.objectDescriptionId << '|';
        appendNormalizedPosition(stream, spriteObject.x, spriteObject.y, spriteObject.z);
        stream << '|';
        appendNormalizedPosition(
            stream,
            spriteObject.velocityX,
            spriteObject.velocityY,
            spriteObject.velocityZ);
        stream << '|'
               << spriteObject.yawAngle << '|'
               << spriteObject.soundId << '|'
               << spriteObject.attributes << '|'
               << spriteObject.sectorId << '|'
               << spriteObject.timeSinceCreated << '|'
               << spriteObject.temporaryLifetime << '|'
               << spriteObject.glowRadiusMultiplier << '|'
               << spriteObject.spellId << '|'
               << spriteObject.spellLevel << '|'
               << spriteObject.spellSkill << '|'
               << spriteObject.field54 << '|'
               << spriteObject.spellCasterPid << '|'
               << spriteObject.spellTargetPid << '|'
               << static_cast<int>(spriteObject.lodDistance) << '|'
               << static_cast<int>(spriteObject.spellCasterAbility) << '|';
        appendNormalizedPosition(stream, spriteObject.initialX, spriteObject.initialY, spriteObject.initialZ);
        stream << '|'
               << bytesToUpperHex(spriteObject.rawContainingItem) << '\n';
    }

    stream << "chests\n";

    for (const OpenYAMM::Game::MapDeltaChest &chest : mapDeltaData.chests)
    {
        stream << chest.chestTypeId << '|'
               << chest.flags << '|'
               << bytesToUpperHex(chest.rawItems) << '|';

        for (size_t index = 0; index < chest.inventoryMatrix.size(); ++index)
        {
            if (index > 0)
            {
                stream << ',';
            }

            stream << chest.inventoryMatrix[index];
        }

        stream << '\n';
    }

    stream << "variables_map\n";

    for (size_t index = 0; index < mapDeltaData.eventVariables.mapVars.size(); ++index)
    {
        if (index > 0)
        {
            stream << ',';
        }

        stream << static_cast<int>(mapDeltaData.eventVariables.mapVars[index]);
    }

    stream << "\nvariables_decor\n";

    for (size_t index = 0; index < mapDeltaData.eventVariables.decorVars.size(); ++index)
    {
        if (index > 0)
        {
            stream << ',';
        }

        stream << static_cast<int>(mapDeltaData.eventVariables.decorVars[index]);
    }

    stream << '\n';
    return stream.str();
}

std::string replaceExtension(const std::string &fileName, const std::string &newExtension)
{
    const std::filesystem::path path(fileName);
    return path.stem().string() + newExtension;
}

bool loadOutdoorGeometry(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    OpenYAMM::Game::OutdoorMapData &outdoorMapData,
    std::string &failure)
{
    const std::string geometryPath = "Data/games/" + mapFileName;
    const std::optional<std::vector<uint8_t>> geometryBytes = assetFileSystem.readBinaryFile(geometryPath);

    if (!geometryBytes)
    {
        failure = "could not read geometry bytes for " + mapFileName;
        return false;
    }

    OpenYAMM::Game::OutdoorMapDataLoader loader = {};
    const std::optional<OpenYAMM::Game::OutdoorMapData> loadedMap = loader.loadFromBytes(*geometryBytes);

    if (!loadedMap)
    {
        failure = "could not parse outdoor geometry for " + mapFileName;
        return false;
    }

    outdoorMapData = *loadedMap;
    return true;
}

bool loadIndoorGeometry(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    OpenYAMM::Game::IndoorMapData &indoorMapData,
    std::string &failure)
{
    const std::string geometryPath = "Data/games/" + mapFileName;
    const std::optional<std::vector<uint8_t>> geometryBytes = assetFileSystem.readBinaryFile(geometryPath);

    if (!geometryBytes)
    {
        failure = "could not read geometry bytes for " + mapFileName;
        return false;
    }

    OpenYAMM::Game::IndoorMapDataLoader loader = {};
    const std::optional<OpenYAMM::Game::IndoorMapData> loadedMap = loader.loadFromBytes(*geometryBytes);

    if (!loadedMap)
    {
        failure = "could not parse indoor geometry for " + mapFileName;
        return false;
    }

    indoorMapData = *loadedMap;
    return true;
}

bool loadLegacyOutdoorMapDelta(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    const OpenYAMM::Game::OutdoorMapData &outdoorMapData,
    OpenYAMM::Game::MapDeltaData &mapDeltaData,
    std::string &failure)
{
    const std::string companionFileName = replaceExtension(mapFileName, ".ddm");
    std::optional<std::vector<uint8_t>> companionBytes =
        assetFileSystem.readBinaryFile("Data/games/legacy/" + companionFileName);

    if (!companionBytes)
    {
        companionBytes = assetFileSystem.readBinaryFile("Data/games/" + companionFileName);
    }

    if (!companionBytes)
    {
        failure = "could not read legacy companion for " + mapFileName;
        return false;
    }

    OpenYAMM::Game::MapDeltaDataLoader loader = {};
    const std::optional<OpenYAMM::Game::MapDeltaData> loadedMapDelta =
        loader.loadOutdoorFromBytes(*companionBytes, outdoorMapData);

    if (!loadedMapDelta)
    {
        failure = "could not parse legacy companion for " + mapFileName;
        return false;
    }

    mapDeltaData = *loadedMapDelta;
    return true;
}

bool loadLegacyIndoorMapDelta(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    const OpenYAMM::Game::IndoorMapData &indoorMapData,
    OpenYAMM::Game::MapDeltaData &mapDeltaData,
    std::string &failure)
{
    const std::string companionFileName = replaceExtension(mapFileName, ".dlv");
    std::optional<std::vector<uint8_t>> companionBytes =
        assetFileSystem.readBinaryFile("Data/games/legacy/" + companionFileName);

    if (!companionBytes)
    {
        companionBytes = assetFileSystem.readBinaryFile("Data/games/" + companionFileName);
    }

    if (!companionBytes)
    {
        failure = "could not read legacy companion for " + mapFileName;
        return false;
    }

    OpenYAMM::Game::MapDeltaDataLoader loader = {};
    const std::optional<OpenYAMM::Game::MapDeltaData> loadedMapDelta =
        loader.loadIndoorFromBytes(*companionBytes, indoorMapData);

    if (!loadedMapDelta)
    {
        failure = "could not parse legacy companion for " + mapFileName;
        return false;
    }

    mapDeltaData = *loadedMapDelta;
    return true;
}

bool loadSceneOutdoorMapDelta(
    const OpenYAMM::Editor::EditorDocument &document,
    OpenYAMM::Game::OutdoorMapData &outdoorMapData,
    OpenYAMM::Game::MapDeltaData &mapDeltaData,
    std::string &failure)
{
    return document.buildOutdoorAuthoredRuntimeState(outdoorMapData, mapDeltaData, failure);
}

bool compareOutdoorSceneAgainstLegacy(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    std::string &failure)
{
    OpenYAMM::Game::OutdoorMapData legacyOutdoorMapData = {};
    OpenYAMM::Game::OutdoorMapData sceneOutdoorMapData = {};
    OpenYAMM::Game::MapDeltaData legacyMapDeltaData = {};
    OpenYAMM::Game::MapDeltaData sceneMapDeltaData = {};

    if (!loadOutdoorGeometry(assetFileSystem, mapFileName, legacyOutdoorMapData, failure))
    {
        return false;
    }

    if (!loadOutdoorGeometry(assetFileSystem, mapFileName, sceneOutdoorMapData, failure))
    {
        return false;
    }

    if (!loadLegacyOutdoorMapDelta(assetFileSystem, mapFileName, legacyOutdoorMapData, legacyMapDeltaData, failure))
    {
        return false;
    }

    OpenYAMM::Editor::EditorDocument document;

    if (!document.loadOutdoorMapPackage(assetFileSystem, mapFileName, failure))
    {
        failure = "could not load editor document for " + mapFileName + ": " + failure;
        return false;
    }

    if (!loadSceneOutdoorMapDelta(document, sceneOutdoorMapData, sceneMapDeltaData, failure))
    {
        return false;
    }

    const std::string legacySnapshot =
        buildNormalizedOutdoorAuthoredSnapshot(legacyOutdoorMapData, legacyMapDeltaData);
    const std::string sceneSnapshot =
        buildNormalizedOutdoorAuthoredSnapshot(sceneOutdoorMapData, sceneMapDeltaData);

    if (legacySnapshot != sceneSnapshot)
    {
        failure = "legacy and scene authored state differ for " + mapFileName;
        return false;
    }

    return true;
}

bool verifyOutdoorSceneRoundTrip(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    bool useExplicitSaveBuild,
    bool reloadViaMapPackage,
    bool verifyPersistedBuildState,
    std::string &failure)
{
    OpenYAMM::Editor::EditorSession session;
    session.initialize(assetFileSystem);

    if (!session.openOutdoorMap(mapFileName, failure))
    {
        failure = "could not load editor document for round-trip " + mapFileName + ": " + failure;
        return false;
    }

    OpenYAMM::Editor::EditorDocument &document = session.document();

    OpenYAMM::Game::OutdoorMapData initialOutdoorMapData = {};
    OpenYAMM::Game::MapDeltaData initialMapDeltaData = {};

    if (!document.buildOutdoorAuthoredRuntimeState(initialOutdoorMapData, initialMapDeltaData, failure))
    {
        failure = "could not build initial authored state for " + mapFileName + ": " + failure;
        return false;
    }

    OpenYAMM::Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();
    sceneData.environment.fogWeakDistance += 1;
    sceneData.environment.fogStrongDistance = std::max(
        sceneData.environment.fogStrongDistance,
        sceneData.environment.fogWeakDistance);

    if (!sceneData.entities.empty())
    {
        sceneData.entities[0].entity.facing += 1;
    }

    if (!sceneData.spawns.empty())
    {
        sceneData.spawns[0].spawn.radius = static_cast<uint16_t>(
            std::min<int>(sceneData.spawns[0].spawn.radius + 1, 65535));
    }

    if (sceneData.terrainAttributeOverrides.empty())
    {
        sceneData.terrainAttributeOverrides.push_back({32, 32, 0x01});
    }
    else
    {
        sceneData.terrainAttributeOverrides[0].legacyAttributes ^= 0x03;
    }

    if (sceneData.interactiveFaces.empty())
    {
        if (!document.outdoorGeometry().bmodels.empty() && !document.outdoorGeometry().bmodels[0].faces.empty())
        {
            sceneData.interactiveFaces.push_back({0, 0, 1, 0, 0, 0});
        }
    }
    else
    {
        sceneData.interactiveFaces[0].cogTrigger = static_cast<uint16_t>(sceneData.interactiveFaces[0].cogTrigger + 1);
    }

    if (!document.outdoorGeometry().bmodels.empty())
    {
        OpenYAMM::Game::OutdoorBModel &bmodel = document.mutableOutdoorGeometry().bmodels.front();

        for (OpenYAMM::Game::OutdoorBModelVertex &vertex : bmodel.vertices)
        {
            vertex.x += 64;
            vertex.y -= 32;
        }

        bmodel.positionX += 64;
        bmodel.positionY -= 32;
        bmodel.minX += 64;
        bmodel.minY -= 32;
        bmodel.maxX += 64;
        bmodel.maxY -= 32;
        bmodel.boundingCenterX += 64;
        bmodel.boundingCenterY -= 32;
    }

    const float centerWorldX = 0.0f;
    const float centerWorldY = 0.0f;
    const int placementZ = static_cast<int>(std::lround(
        OpenYAMM::Game::sampleOutdoorPlacementFloorHeight(
            document.outdoorGeometry(),
            centerWorldX,
            centerWorldY,
            32768.0f)));
    std::string errorMessage;

    if (!session.createOutdoorObject(OpenYAMM::Editor::EditorSelectionKind::Entity, 0, 0, placementZ, errorMessage))
    {
        failure = "could not create entity during round-trip test for " + mapFileName + ": " + errorMessage;
        return false;
    }

    if (!session.createOutdoorObject(OpenYAMM::Editor::EditorSelectionKind::Spawn, 512, 512, placementZ, errorMessage))
    {
        failure = "could not create spawn during round-trip test for " + mapFileName + ": " + errorMessage;
        return false;
    }

    if (!session.duplicateSelectedObject(errorMessage))
    {
        failure = "could not duplicate spawn during round-trip test for " + mapFileName + ": " + errorMessage;
        return false;
    }

    if (!session.deleteSelectedObject(errorMessage))
    {
        failure = "could not delete duplicate spawn during round-trip test for " + mapFileName + ": " + errorMessage;
        return false;
    }

    if (!session.createOutdoorObject(OpenYAMM::Editor::EditorSelectionKind::Actor, 1024, 0, placementZ, errorMessage))
    {
        failure = "could not create actor during round-trip test for " + mapFileName + ": " + errorMessage;
        return false;
    }

    if (!session.createOutdoorObject(
            OpenYAMM::Editor::EditorSelectionKind::SpriteObject,
            1536,
            0,
            placementZ,
            errorMessage))
    {
        failure = "could not create sprite object during round-trip test for " + mapFileName + ": " + errorMessage;
        return false;
    }

    if (!sceneData.initialState.chests.empty())
    {
        OpenYAMM::Game::MapDeltaChest &chest = sceneData.initialState.chests.front();

        if (chest.rawItems.size() < ChestItemRecordCount * ChestItemRecordSize)
        {
            chest.rawItems.resize(ChestItemRecordCount * ChestItemRecordSize, 0);
        }

        int32_t rawItemId = 0;
        std::memcpy(&rawItemId, chest.rawItems.data(), sizeof(rawItemId));

        int32_t replacementRawItemId = 618;

        if (rawItemId > 0)
        {
            replacementRawItemId = rawItemId == 618 ? 619 : 618;
        }
        else if (rawItemId < 0)
        {
            replacementRawItemId = rawItemId == -1 ? -2 : -1;
        }

        std::memcpy(chest.rawItems.data(), &replacementRawItemId, sizeof(replacementRawItemId));
    }

    if (!document.mutableOutdoorGeometry().bmodels.empty() && !document.mutableOutdoorGeometry().bmodels.front().faces.empty())
    {
        OpenYAMM::Game::OutdoorBModelFace &face = document.mutableOutdoorGeometry().bmodels.front().faces.front();
        face.textureName = face.textureName == "grastyl" ? "dirttyl" : "grastyl";
    }

    if (!document.mutableOutdoorGeometry().heightMap.empty())
    {
        uint8_t &height = document.mutableOutdoorGeometry().heightMap.front();
        height = static_cast<uint8_t>(std::clamp(static_cast<int>(height) + 1, 0, 255));
    }

    const std::filesystem::path tempDirectory = activeWorldEditorPath(assetFileSystem, "maps");
    const std::filesystem::path tempImportPath = tempDirectory / "__editor_headless_import.obj";
    const std::filesystem::path tempGltfPath = tempDirectory / "__editor_headless_import.gltf";
    const std::filesystem::path tempGltfBinPath = tempDirectory / "__editor_headless_import.bin";
    const std::filesystem::path tempGlbPath = tempDirectory / "__editor_headless_import.glb";
    const std::filesystem::path tempSplitGltfPath = tempDirectory / "__editor_headless_split_import.gltf";
    const std::filesystem::path tempTexturePngPath = tempDirectory / "__editor_headless_import_texture.png";
    const std::filesystem::path tempTexturedGltfPath = tempDirectory / "__editor_headless_textured_import.gltf";
    const std::filesystem::path tempTexturedGlbPath = tempDirectory / "__editor_headless_textured_import.glb";

    {
        std::ofstream output(tempImportPath, std::ios::binary | std::ios::trunc);
        output
            << "o headless_import\n"
            << "usemtl grastyl\n"
            << "v -128 -128 0\n"
            << "v 128 -128 0\n"
            << "v 128 128 0\n"
            << "v -128 128 0\n"
            << "vt 0 0\n"
            << "vt 1 0\n"
            << "vt 1 1\n"
            << "vt 0 1\n"
            << "f 1/1 2/2 3/3 4/4\n";
    }

    {
        std::ofstream binaryOutput(tempGltfBinPath, std::ios::binary | std::ios::trunc);
        const float positions[] = {
            -128.0f, -128.0f, 0.0f,
             128.0f, -128.0f, 0.0f,
             128.0f,  128.0f, 0.0f,
            -128.0f,  128.0f, 0.0f
        };
        const float texCoords[] = {
            0.0f, 0.0f,
            1.0f, 0.0f,
            1.0f, 1.0f,
            0.0f, 1.0f
        };
        const uint16_t indices[] = {0, 1, 2, 0, 2, 3};
        binaryOutput.write(reinterpret_cast<const char *>(positions), sizeof(positions));
        binaryOutput.write(reinterpret_cast<const char *>(texCoords), sizeof(texCoords));
        binaryOutput.write(reinterpret_cast<const char *>(indices), sizeof(indices));
    }

    {
        const uint32_t texturePixels[] = {
            0xff0000ffu,
            0xff00ff00u,
            0xffff0000u,
            0xffffffffu,
        };
        SDL_Surface *pSurface = SDL_CreateSurfaceFrom(
            2,
            2,
            SDL_PIXELFORMAT_BGRA32,
            const_cast<uint32_t *>(texturePixels),
            2 * static_cast<int>(sizeof(uint32_t)));

        if (pSurface == nullptr || !SDL_SavePNG(pSurface, tempTexturePngPath.string().c_str()))
        {
            if (pSurface != nullptr)
            {
                SDL_DestroySurface(pSurface);
            }

            failure = "could not create temporary PNG import texture for " + mapFileName;
            return false;
        }

        SDL_DestroySurface(pSurface);
    }

    {
        std::ofstream output(tempGltfPath, std::ios::binary | std::ios::trunc);
        output
            << "{\n"
            << "  \"asset\": {\"version\": \"2.0\"},\n"
            << "  \"buffers\": [{\"uri\": \"" << tempGltfBinPath.filename().string() << "\", \"byteLength\": 92}],\n"
            << "  \"bufferViews\": [\n"
            << "    {\"buffer\": 0, \"byteOffset\": 0, \"byteLength\": 48, \"target\": 34962},\n"
            << "    {\"buffer\": 0, \"byteOffset\": 48, \"byteLength\": 32, \"target\": 34962},\n"
            << "    {\"buffer\": 0, \"byteOffset\": 80, \"byteLength\": 12, \"target\": 34963}\n"
            << "  ],\n"
            << "  \"accessors\": [\n"
            << "    {\"bufferView\": 0, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC3\"},\n"
            << "    {\"bufferView\": 1, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC2\"},\n"
            << "    {\"bufferView\": 2, \"componentType\": 5123, \"count\": 6, \"type\": \"SCALAR\"}\n"
            << "  ],\n"
            << "  \"materials\": [{\"name\": \"dirttyl\"}],\n"
            << "  \"meshes\": [{\"name\": \"headless_import_gltf\", \"primitives\": ["
            << "{\"attributes\": {\"POSITION\": 0, \"TEXCOORD_0\": 1}, \"indices\": 2, \"material\": 0, \"mode\": 4}"
            << "]}],\n"
            << "  \"nodes\": [{\"mesh\": 0}],\n"
            << "  \"scenes\": [{\"nodes\": [0]}],\n"
            << "  \"scene\": 0\n"
            << "}\n";
    }

    {
        std::ofstream output(tempSplitGltfPath, std::ios::binary | std::ios::trunc);
        output
            << "{\n"
            << "  \"asset\": {\"version\": \"2.0\"},\n"
            << "  \"buffers\": [{\"uri\": \"" << tempGltfBinPath.filename().string() << "\", \"byteLength\": 92}],\n"
            << "  \"bufferViews\": [\n"
            << "    {\"buffer\": 0, \"byteOffset\": 0, \"byteLength\": 48, \"target\": 34962},\n"
            << "    {\"buffer\": 0, \"byteOffset\": 48, \"byteLength\": 32, \"target\": 34962},\n"
            << "    {\"buffer\": 0, \"byteOffset\": 80, \"byteLength\": 12, \"target\": 34963}\n"
            << "  ],\n"
            << "  \"accessors\": [\n"
            << "    {\"bufferView\": 0, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC3\"},\n"
            << "    {\"bufferView\": 1, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC2\"},\n"
            << "    {\"bufferView\": 2, \"componentType\": 5123, \"count\": 6, \"type\": \"SCALAR\"}\n"
            << "  ],\n"
            << "  \"materials\": [{\"name\": \"dirttyl\"}],\n"
            << "  \"meshes\": [{\"name\": \"shared_quad\", \"primitives\": ["
            << "{\"attributes\": {\"POSITION\": 0, \"TEXCOORD_0\": 1}, \"indices\": 2, \"material\": 0, \"mode\": 4}"
            << "]}],\n"
            << "  \"nodes\": [\n"
            << "    {\"name\": \"left_quad\", \"mesh\": 0, \"translation\": [-256.0, 0.0, 0.0]},\n"
            << "    {\"name\": \"right_quad\", \"mesh\": 0, \"translation\": [256.0, 0.0, 0.0]}\n"
            << "  ],\n"
            << "  \"scenes\": [{\"nodes\": [0, 1]}],\n"
            << "  \"scene\": 0\n"
            << "}\n";
    }

    {
        std::ofstream output(tempTexturedGltfPath, std::ios::binary | std::ios::trunc);
        output
            << "{\n"
            << "  \"asset\": {\"version\": \"2.0\"},\n"
            << "  \"buffers\": [{\"uri\": \"" << tempGltfBinPath.filename().string() << "\", \"byteLength\": 92}],\n"
            << "  \"bufferViews\": [\n"
            << "    {\"buffer\": 0, \"byteOffset\": 0, \"byteLength\": 48, \"target\": 34962},\n"
            << "    {\"buffer\": 0, \"byteOffset\": 48, \"byteLength\": 32, \"target\": 34962},\n"
            << "    {\"buffer\": 0, \"byteOffset\": 80, \"byteLength\": 12, \"target\": 34963}\n"
            << "  ],\n"
            << "  \"accessors\": [\n"
            << "    {\"bufferView\": 0, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC3\"},\n"
            << "    {\"bufferView\": 1, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC2\"},\n"
            << "    {\"bufferView\": 2, \"componentType\": 5123, \"count\": 6, \"type\": \"SCALAR\"}\n"
            << "  ],\n"
            << "  \"images\": [{\"uri\": \"" << tempTexturePngPath.filename().string() << "\"}],\n"
            << "  \"textures\": [{\"source\": 0}],\n"
            << "  \"materials\": [{\"pbrMetallicRoughness\": {\"baseColorTexture\": {\"index\": 0}}}],\n"
            << "  \"meshes\": [{\"name\": \"headless_import_textured_gltf\", \"primitives\": ["
            << "{\"attributes\": {\"POSITION\": 0, \"TEXCOORD_0\": 1}, \"indices\": 2, \"material\": 0, \"mode\": 4}"
            << "]}],\n"
            << "  \"nodes\": [{\"mesh\": 0}],\n"
            << "  \"scenes\": [{\"nodes\": [0]}],\n"
            << "  \"scene\": 0\n"
            << "}\n";
    }

    {
        const std::string glbJson =
            "{\n"
            "  \"asset\": {\"version\": \"2.0\"},\n"
            "  \"buffers\": [{\"byteLength\": 92}],\n"
            "  \"bufferViews\": [\n"
            "    {\"buffer\": 0, \"byteOffset\": 0, \"byteLength\": 48, \"target\": 34962},\n"
            "    {\"buffer\": 0, \"byteOffset\": 48, \"byteLength\": 32, \"target\": 34962},\n"
            "    {\"buffer\": 0, \"byteOffset\": 80, \"byteLength\": 12, \"target\": 34963}\n"
            "  ],\n"
            "  \"accessors\": [\n"
            "    {\"bufferView\": 0, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC3\"},\n"
            "    {\"bufferView\": 1, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC2\"},\n"
            "    {\"bufferView\": 2, \"componentType\": 5123, \"count\": 6, \"type\": \"SCALAR\"}\n"
            "  ],\n"
            "  \"materials\": [{\"name\": \"dirttyl\"}],\n"
            "  \"meshes\": [{\"name\": \"headless_import_glb\", \"primitives\": ["
            "{\"attributes\": {\"POSITION\": 0, \"TEXCOORD_0\": 1}, \"indices\": 2, \"material\": 0, \"mode\": 4}"
            "]}],\n"
            "  \"nodes\": [{\"mesh\": 0}],\n"
            "  \"scenes\": [{\"nodes\": [0]}],\n"
            "  \"scene\": 0\n"
            "}\n";
        std::vector<uint8_t> glbBinary;
        const float positions[] = {
            -128.0f, -128.0f, 0.0f,
             128.0f, -128.0f, 0.0f,
             128.0f,  128.0f, 0.0f,
            -128.0f,  128.0f, 0.0f
        };
        const float texCoords[] = {
            0.0f, 0.0f,
            1.0f, 0.0f,
            1.0f, 1.0f,
            0.0f, 1.0f
        };
        const uint16_t indices[] = {0, 1, 2, 0, 2, 3};
        appendBytes(glbBinary, positions, sizeof(positions));
        appendBytes(glbBinary, texCoords, sizeof(texCoords));
        appendBytes(glbBinary, indices, sizeof(indices));

        if (!writeGlbFile(tempGlbPath, glbJson, glbBinary))
        {
            failure = "could not create temporary GLB import fixture for " + mapFileName;
            return false;
        }
    }

    {
        std::vector<uint8_t> textureBytes;

        if (!readBinaryFileBytes(tempTexturePngPath, textureBytes))
        {
            failure = "could not read temporary PNG import texture for " + mapFileName;
            return false;
        }

        std::vector<uint8_t> glbBinary;
        const size_t positionsOffset = glbBinary.size();
        const float positions[] = {
            -128.0f, -128.0f, 0.0f,
             128.0f, -128.0f, 0.0f,
             128.0f,  128.0f, 0.0f,
            -128.0f,  128.0f, 0.0f
        };
        appendBytes(glbBinary, positions, sizeof(positions));

        const size_t texCoordsOffset = glbBinary.size();
        const float texCoords[] = {
            0.0f, 0.0f,
            1.0f, 0.0f,
            1.0f, 1.0f,
            0.0f, 1.0f
        };
        appendBytes(glbBinary, texCoords, sizeof(texCoords));

        const size_t indicesOffset = glbBinary.size();
        const uint16_t indices[] = {0, 1, 2, 0, 2, 3};
        appendBytes(glbBinary, indices, sizeof(indices));
        appendPaddingBytes(glbBinary, 4, 0);
        const size_t imageOffset = glbBinary.size();
        appendBytes(glbBinary, textureBytes.data(), textureBytes.size());

        const std::string texturedGlbJson =
            "{\n"
            "  \"asset\": {\"version\": \"2.0\"},\n"
            "  \"buffers\": [{\"byteLength\": " + std::to_string(glbBinary.size()) + "}],\n"
            "  \"bufferViews\": [\n"
            "    {\"buffer\": 0, \"byteOffset\": " + std::to_string(positionsOffset)
                + ", \"byteLength\": 48, \"target\": 34962},\n"
            "    {\"buffer\": 0, \"byteOffset\": " + std::to_string(texCoordsOffset)
                + ", \"byteLength\": 32, \"target\": 34962},\n"
            "    {\"buffer\": 0, \"byteOffset\": " + std::to_string(indicesOffset)
                + ", \"byteLength\": 12, \"target\": 34963},\n"
            "    {\"buffer\": 0, \"byteOffset\": " + std::to_string(imageOffset)
                + ", \"byteLength\": " + std::to_string(textureBytes.size()) + "}\n"
            "  ],\n"
            "  \"accessors\": [\n"
            "    {\"bufferView\": 0, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC3\"},\n"
            "    {\"bufferView\": 1, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC2\"},\n"
            "    {\"bufferView\": 2, \"componentType\": 5123, \"count\": 6, \"type\": \"SCALAR\"}\n"
            "  ],\n"
            "  \"images\": [{\"bufferView\": 3, \"mimeType\": \"image/png\"}],\n"
            "  \"textures\": [{\"source\": 0}],\n"
            "  \"materials\": [{\"pbrMetallicRoughness\": {\"baseColorTexture\": {\"index\": 0}}}],\n"
            "  \"meshes\": [{\"name\": \"headless_import_textured_glb\", \"primitives\": ["
            "{\"attributes\": {\"POSITION\": 0, \"TEXCOORD_0\": 1}, \"indices\": 2, \"material\": 0, \"mode\": 4}"
            "]}],\n"
            "  \"nodes\": [{\"mesh\": 0}],\n"
            "  \"scenes\": [{\"nodes\": [0]}],\n"
            "  \"scene\": 0\n"
            "}\n";

        if (!writeGlbFile(tempTexturedGlbPath, texturedGlbJson, glbBinary))
        {
            failure = "could not create temporary textured GLB import fixture for " + mapFileName;
            return false;
        }
    }
    if (!document.mutableOutdoorGeometry().bmodels.empty())
    {
        session.select(OpenYAMM::Editor::EditorSelectionKind::BModel, 0);

        if (!session.replaceSelectedBModelFromModel(tempImportPath.string(), 1.0f, "grastyl", {}, false, errorMessage))
        {
            failure = "could not replace bmodel from OBJ during round-trip test for "
                + mapFileName + ": " + errorMessage;
            return false;
        }

        if (document.mutableOutdoorGeometry().bmodels.front().faces.size() != 1
            || document.mutableOutdoorGeometry().bmodels.front().vertices.size() != 4)
        {
            failure = "OBJ replace produced unexpected bmodel geometry for " + mapFileName;
            return false;
        }

        if (!session.reimportSelectedBModel(errorMessage))
        {
            failure = "could not reimport bmodel from remembered OBJ source during round-trip test for "
                + mapFileName + ": " + errorMessage;
            return false;
        }
    }

    if (!session.importNewBModelFromModel(tempGltfPath.string(), 1.0f, "dirttyl", {}, false, false, errorMessage))
    {
        failure = "could not import new bmodel from glTF during round-trip test for "
            + mapFileName + ": " + errorMessage;
        return false;
    }

    if (document.mutableOutdoorGeometry().bmodels.back().faces.size() != 2
        || document.mutableOutdoorGeometry().bmodels.back().vertices.size() != 4)
    {
        failure = "glTF import produced unexpected bmodel geometry for " + mapFileName;
        return false;
    }

    const size_t importedBModelIndex = document.mutableOutdoorGeometry().bmodels.empty()
        ? 0
        : (document.mutableOutdoorGeometry().bmodels.size() - 1);

    if (!session.importNewBModelFromModel(tempGlbPath.string(), 1.0f, "dirttyl", {}, false, false, errorMessage))
    {
        failure = "could not import new GLB bmodel during round-trip test for "
            + mapFileName + ": " + errorMessage;
        return false;
    }

    if (document.mutableOutdoorGeometry().bmodels.back().faces.size() != 2
        || document.mutableOutdoorGeometry().bmodels.back().vertices.size() != 4)
    {
        failure = "GLB import produced unexpected bmodel geometry for " + mapFileName;
        return false;
    }

    const size_t mergedImportStartIndex = document.mutableOutdoorGeometry().bmodels.size();

    if (!session.importNewBModelFromModel(tempGltfPath.string(), 1.0f, "dirttyl", {}, false, true, errorMessage))
    {
        failure = "could not import merged glTF bmodel during round-trip test for "
            + mapFileName + ": " + errorMessage;
        return false;
    }

    if (document.mutableOutdoorGeometry().bmodels.size() != mergedImportStartIndex + 1)
    {
        failure = "merged glTF import did not append exactly one bmodel for " + mapFileName;
        return false;
    }

    if (document.mutableOutdoorGeometry().bmodels.back().faces.size() != 1
        || document.mutableOutdoorGeometry().bmodels.back().vertices.size() != 4)
    {
        failure = "merged glTF import did not collapse the coplanar quad for " + mapFileName;
        return false;
    }

    const std::optional<OpenYAMM::Editor::EditorBModelImportSource> mergedImportSource =
        document.outdoorBModelImportSource(document.mutableOutdoorGeometry().bmodels.size() - 1);

    if (!mergedImportSource || !mergedImportSource->mergeCoplanarFaces)
    {
        failure = "merged glTF import did not persist merge_coplanar_faces metadata for " + mapFileName;
        return false;
    }

    const std::optional<OpenYAMM::Editor::EditorBModelImportSource> savedImportSource =
        document.outdoorBModelImportSource(importedBModelIndex);

    if (!savedImportSource || savedImportSource->materialRemaps.empty())
    {
        failure = "imported bmodel did not persist material remaps for " + mapFileName;
        return false;
    }

    const size_t texturedImportStartIndex = document.mutableOutdoorGeometry().bmodels.size();

    if (!session.importNewBModelFromModel(tempTexturedGltfPath.string(), 1.0f, "", {}, false, false, errorMessage))
    {
        failure = "could not import textured glTF bmodel during round-trip test for "
            + mapFileName + ": " + errorMessage;
        return false;
    }

    if (document.mutableOutdoorGeometry().bmodels.size() != texturedImportStartIndex + 1)
    {
        failure = "textured glTF import did not append exactly one bmodel for " + mapFileName;
        return false;
    }

    const OpenYAMM::Game::OutdoorBModel &texturedBModel = document.mutableOutdoorGeometry().bmodels.back();

    if (texturedBModel.faces.empty() || texturedBModel.faces.front().textureName.empty())
    {
        failure = "textured glTF import did not assign an imported bitmap texture for " + mapFileName;
        return false;
    }

    const std::filesystem::path importedBitmapPath =
        assetFileSystem.getEditorDevelopmentRoot() / "Data" / "bitmaps"
        / (texturedBModel.faces.front().textureName + ".bmp");

    if (!std::filesystem::exists(importedBitmapPath))
    {
        failure = "textured glTF import did not materialize bitmap asset for " + mapFileName;
        return false;
    }

    const std::optional<OpenYAMM::Editor::EditorBModelImportSource> texturedImportSource =
        document.outdoorBModelImportSource(document.mutableOutdoorGeometry().bmodels.size() - 1);

    if (!texturedImportSource || texturedImportSource->materialRemaps.empty())
    {
        failure = "textured glTF import did not persist generated material remap for " + mapFileName;
        return false;
    }

    const size_t texturedGlbImportStartIndex = document.mutableOutdoorGeometry().bmodels.size();

    if (!session.importNewBModelFromModel(tempTexturedGlbPath.string(), 1.0f, "", {}, false, false, errorMessage))
    {
        failure = "could not import textured GLB bmodel during round-trip test for "
            + mapFileName + ": " + errorMessage;
        return false;
    }

    if (document.mutableOutdoorGeometry().bmodels.size() != texturedGlbImportStartIndex + 1)
    {
        failure = "textured GLB import did not append exactly one bmodel for " + mapFileName;
        return false;
    }

    const OpenYAMM::Game::OutdoorBModel &texturedGlbBModel = document.mutableOutdoorGeometry().bmodels.back();

    if (texturedGlbBModel.faces.empty() || texturedGlbBModel.faces.front().textureName.empty())
    {
        failure = "textured GLB import did not assign an imported bitmap texture for " + mapFileName;
        return false;
    }

    const std::filesystem::path importedGlbBitmapPath =
        assetFileSystem.getEditorDevelopmentRoot()
        / "Data"
        / "bitmaps"
        / (texturedGlbBModel.faces.front().textureName + ".bmp");

    if (!std::filesystem::exists(importedGlbBitmapPath))
    {
        failure = "textured GLB import did not materialize bitmap asset for " + mapFileName;
        return false;
    }

    const std::optional<OpenYAMM::Editor::EditorBModelImportSource> texturedGlbImportSource =
        document.outdoorBModelImportSource(document.mutableOutdoorGeometry().bmodels.size() - 1);

    if (!texturedGlbImportSource || texturedGlbImportSource->materialRemaps.empty())
    {
        failure = "textured GLB import did not persist generated material remap for " + mapFileName;
        return false;
    }

    std::vector<size_t> rememberedImportSourceIndices = {
        importedBModelIndex,
        mergedImportStartIndex,
        texturedImportStartIndex,
        texturedGlbImportStartIndex,
    };

    const size_t splitImportStartIndex = document.mutableOutdoorGeometry().bmodels.size();

    if (!session.importNewBModelFromModel(tempSplitGltfPath.string(), 1.0f, "dirttyl", {}, true, false, errorMessage))
    {
        failure = "could not import split glTF bmodels during round-trip test for "
            + mapFileName + ": " + errorMessage;
        return false;
    }

    if (document.mutableOutdoorGeometry().bmodels.size() != splitImportStartIndex + 2)
    {
        failure = "split glTF import did not create the expected number of bmodels for " + mapFileName;
        return false;
    }

    const std::optional<OpenYAMM::Editor::EditorBModelImportSource> splitImportSourceA =
        document.outdoorBModelImportSource(splitImportStartIndex);
    const std::optional<OpenYAMM::Editor::EditorBModelImportSource> splitImportSourceB =
        document.outdoorBModelImportSource(splitImportStartIndex + 1);

    if (!splitImportSourceA || !splitImportSourceB)
    {
        failure = "split glTF import did not remember import sources for " + mapFileName;
        return false;
    }

    if (splitImportSourceA->sourceMeshName.empty()
        || splitImportSourceB->sourceMeshName.empty()
        || splitImportSourceA->sourceMeshName == splitImportSourceB->sourceMeshName)
    {
        failure = "split glTF import did not preserve distinct mesh/node names for " + mapFileName;
        return false;
    }

    rememberedImportSourceIndices.push_back(splitImportStartIndex);
    rememberedImportSourceIndices.push_back(splitImportStartIndex + 1);
    session.select(OpenYAMM::Editor::EditorSelectionKind::BModel, splitImportStartIndex);

    if (!session.reimportSelectedBModel(errorMessage))
    {
        failure = "could not reimport split glTF bmodel from remembered source during round-trip test for "
            + mapFileName + ": " + errorMessage;
        return false;
    }

    const std::vector<std::string> validationIssues = document.validate();

    if (!validationIssues.empty())
    {
        failure = "mutated document became invalid for " + mapFileName + ": " + validationIssues.front();
        return false;
    }

    const std::string tempSceneFileName = "__editor_headless_tmp__" + replaceExtension(mapFileName, ".scene.yml");
    const std::filesystem::path tempScenePath = tempDirectory / tempSceneFileName;

    const std::filesystem::path tempGeometryMetadataPath =
        tempDirectory / ("__editor_headless_tmp__" + replaceExtension(mapFileName, ".geometry.yml"));
    const std::filesystem::path tempMapPackagePath =
        tempDirectory / ("__editor_headless_tmp__" + replaceExtension(mapFileName, ".map.yml"));
    const std::filesystem::path tempTerrainMetadataPath =
        tempDirectory / ("__editor_headless_tmp__" + replaceExtension(mapFileName, ".terrain.yml"));
    const std::filesystem::path tempGeometryPath =
        tempDirectory / ("__editor_headless_tmp__" + replaceExtension(mapFileName, ".odm"));

    if (useExplicitSaveBuild)
    {
        std::error_code removeError;
        std::filesystem::remove(tempScenePath, removeError);
        std::filesystem::remove(tempGeometryMetadataPath, removeError);
        std::filesystem::remove(tempMapPackagePath, removeError);
        std::filesystem::remove(tempTerrainMetadataPath, removeError);
        std::filesystem::remove(tempGeometryPath, removeError);

        if (!document.saveSourceAs(tempScenePath, failure))
        {
            failure = "could not save source round-trip scene for " + mapFileName + ": " + failure;
            return false;
        }

        if (std::filesystem::exists(tempGeometryPath))
        {
            failure = "source save unexpectedly emitted runtime ODM for " + mapFileName;
            return false;
        }

        if (document.isDirty())
        {
            failure = "source save did not clear source dirty flag for " + mapFileName;
            return false;
        }

        if (!document.isRuntimeBuildDirty())
        {
            failure = "source save unexpectedly cleared runtime build dirty flag for " + mapFileName;
            return false;
        }

        if (verifyPersistedBuildState)
        {
            std::ifstream packageInput(tempMapPackagePath);
            std::stringstream packageBuffer;
            packageBuffer << packageInput.rdbuf();
            std::string packageParseError;
            const std::optional<OpenYAMM::Editor::EditorOutdoorMapPackageMetadata> stalePackageMetadata =
                OpenYAMM::Editor::loadOutdoorMapPackageMetadataFromText(packageBuffer.str(), packageParseError);

            if (!stalePackageMetadata)
            {
                failure = "could not parse stale package state for " + mapFileName + ": " + packageParseError;
                return false;
            }

            if (stalePackageMetadata->sourceFingerprint.empty()
                || stalePackageMetadata->sourceFingerprint == stalePackageMetadata->builtSourceFingerprint)
            {
                failure = "saved source package did not preserve stale build fingerprint state for " + mapFileName;
                return false;
            }
        }

        if (!document.buildRuntimeAs(tempScenePath, failure))
        {
            failure = "could not build runtime round-trip scene for " + mapFileName + ": " + failure;
            return false;
        }

        if (!std::filesystem::exists(tempGeometryPath))
        {
            failure = "runtime build did not emit ODM for " + mapFileName;
            return false;
        }

        if (verifyPersistedBuildState)
        {
            OpenYAMM::Editor::EditorDocument builtReloadedDocument;

            if (!builtReloadedDocument.loadOutdoorMapPackage(assetFileSystem, tempGeometryPath.filename().string(), failure))
            {
                failure = "could not reload built package state for " + mapFileName + ": " + failure;
                return false;
            }

            if (builtReloadedDocument.isRuntimeBuildDirty())
            {
                const OpenYAMM::Editor::EditorOutdoorMapPackageMetadata &packageMetadata =
                    builtReloadedDocument.outdoorMapPackageMetadata();
                failure = "reloaded package still reports stale build state for "
                    + mapFileName
                    + " (source="
                    + packageMetadata.sourceFingerprint
                    + ", built="
                    + packageMetadata.builtSourceFingerprint
                    + ", current="
                    + builtReloadedDocument.currentSourcePackageFingerprint()
                    + ")";
                return false;
            }

            const OpenYAMM::Editor::EditorOutdoorMapPackageMetadata &packageMetadata =
                builtReloadedDocument.outdoorMapPackageMetadata();

            if (packageMetadata.sourceFingerprint.empty()
                || packageMetadata.sourceFingerprint != packageMetadata.builtSourceFingerprint)
            {
                failure = "reloaded built package lost source/build fingerprint parity for " + mapFileName;
                return false;
            }
        }
    }
    else if (!document.saveAs(tempScenePath, failure))
    {
        failure = "could not save round-trip scene for " + mapFileName + ": " + failure;
        return false;
    }

    if (!std::filesystem::exists(tempGeometryMetadataPath))
    {
        failure = "round-trip save did not emit geometry metadata for " + mapFileName;
        return false;
    }

    if (!std::filesystem::exists(tempMapPackagePath))
    {
        failure = "round-trip save did not emit map package root for " + mapFileName;
        return false;
    }

    if (!std::filesystem::exists(tempTerrainMetadataPath))
    {
        failure = "round-trip save did not emit terrain metadata for " + mapFileName;
        return false;
    }

    OpenYAMM::Editor::EditorDocument reloadedDocument;

    if (reloadViaMapPackage)
    {
        if (!reloadedDocument.loadOutdoorMapPackage(assetFileSystem, tempGeometryPath.filename().string(), failure))
        {
            failure = "could not reload round-trip package for " + mapFileName + ": " + failure;
            return false;
        }
    }
    else
    {
        if (!reloadedDocument.loadOutdoorSceneVirtualPath(
                assetFileSystem,
                "Data/games/" + tempSceneFileName,
                failure))
        {
            failure = "could not reload round-trip scene for " + mapFileName + ": " + failure;
            return false;
        }
    }

    OpenYAMM::Game::OutdoorMapData reloadedOutdoorMapData = {};
    OpenYAMM::Game::MapDeltaData reloadedMapDeltaData = {};

    if (!reloadedDocument.buildOutdoorAuthoredRuntimeState(reloadedOutdoorMapData, reloadedMapDeltaData, failure))
    {
        failure = "could not build reloaded authored state for " + mapFileName + ": " + failure;
        return false;
    }

    for (size_t rememberedIndex : rememberedImportSourceIndices)
    {
        const std::optional<OpenYAMM::Editor::EditorBModelImportSource> reloadedImportSource =
            reloadedDocument.outdoorBModelImportSource(rememberedIndex);
        const std::optional<OpenYAMM::Editor::EditorBModelImportSource> originalImportSource =
            document.outdoorBModelImportSource(rememberedIndex);

        if (!reloadedImportSource || !originalImportSource)
        {
            failure = "reloaded geometry metadata lost remembered bmodel import source for " + mapFileName;
            return false;
        }

        if (reloadedImportSource->materialRemaps.empty())
        {
            failure = "reloaded geometry metadata lost bmodel material remaps for " + mapFileName;
            return false;
        }

        const std::optional<OpenYAMM::Editor::EditorBModelSourceTransform> reloadedSourceTransform =
            reloadedDocument.outdoorBModelSourceTransform(rememberedIndex);
        const std::optional<OpenYAMM::Editor::EditorBModelSourceTransform> originalSourceTransform =
            document.outdoorBModelSourceTransform(rememberedIndex);

        if (!originalSourceTransform || !reloadedSourceTransform)
        {
            failure = "reloaded geometry metadata lost remembered bmodel source transform for " + mapFileName;
            return false;
        }

        if (reloadedImportSource->sourceMeshName != originalImportSource->sourceMeshName)
        {
            failure = "reloaded geometry metadata changed remembered source mesh name for " + mapFileName;
            return false;
        }

        if (reloadedImportSource->mergeCoplanarFaces != originalImportSource->mergeCoplanarFaces)
        {
            failure = "reloaded geometry metadata changed remembered merge_coplanar_faces for " + mapFileName;
            return false;
        }

        if (!nearlyEqualFloat(originalSourceTransform->originX, reloadedSourceTransform->originX)
            || !nearlyEqualFloat(originalSourceTransform->originY, reloadedSourceTransform->originY)
            || !nearlyEqualFloat(originalSourceTransform->originZ, reloadedSourceTransform->originZ))
        {
            failure = "reloaded geometry metadata changed bmodel source transform origin for " + mapFileName;
            return false;
        }

        if (!nearlyEqualFloat(originalSourceTransform->basisX[0], reloadedSourceTransform->basisX[0])
            || !nearlyEqualFloat(originalSourceTransform->basisX[1], reloadedSourceTransform->basisX[1])
            || !nearlyEqualFloat(originalSourceTransform->basisX[2], reloadedSourceTransform->basisX[2])
            || !nearlyEqualFloat(originalSourceTransform->basisY[0], reloadedSourceTransform->basisY[0])
            || !nearlyEqualFloat(originalSourceTransform->basisY[1], reloadedSourceTransform->basisY[1])
            || !nearlyEqualFloat(originalSourceTransform->basisY[2], reloadedSourceTransform->basisY[2])
            || !nearlyEqualFloat(originalSourceTransform->basisZ[0], reloadedSourceTransform->basisZ[0])
            || !nearlyEqualFloat(originalSourceTransform->basisZ[1], reloadedSourceTransform->basisZ[1])
            || !nearlyEqualFloat(originalSourceTransform->basisZ[2], reloadedSourceTransform->basisZ[2]))
        {
            failure = "reloaded geometry metadata changed bmodel source transform basis for " + mapFileName;
            return false;
        }
    }

    const std::string reloadedSnapshot =
        buildNormalizedOutdoorAuthoredSnapshot(reloadedOutdoorMapData, reloadedMapDeltaData);

    OpenYAMM::Game::OutdoorMapData expectedOutdoorMapData = {};
    OpenYAMM::Game::MapDeltaData expectedMapDeltaData = {};

    if (!document.buildOutdoorAuthoredRuntimeState(expectedOutdoorMapData, expectedMapDeltaData, failure))
    {
        failure = "could not build mutated authored state for " + mapFileName + ": " + failure;
        return false;
    }

    const std::string expectedRuntimeSnapshot =
        buildNormalizedOutdoorAuthoredSnapshot(expectedOutdoorMapData, expectedMapDeltaData);

    if (expectedRuntimeSnapshot != reloadedSnapshot)
    {
        failure = "round-trip scene save/load changed authored state for " + mapFileName;
        return false;
    }

    return true;
}

bool verifyOutdoorLuaEventDiscovery(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    std::string &failure)
{
    OpenYAMM::Editor::EditorSession session;
    session.initialize(assetFileSystem);

    if (!session.openOutdoorMap("out01.odm", failure))
    {
        failure = "could not load out01.odm for lua event discovery: " + failure;
        return false;
    }

    const OpenYAMM::Editor::EditorOutdoorMapPackageMetadata &packageMetadata =
        session.document().outdoorMapPackageMetadata();

    if (packageMetadata.scriptModule != "Data/scripts/maps/out01.lua")
    {
        failure = "unexpected out01 script module path: " + packageMetadata.scriptModule;
        return false;
    }

    const std::optional<std::string> localScriptModulePath = session.localScriptModulePath();

    if (!localScriptModulePath || !localScriptModulePath->ends_with("Data/scripts/maps/out01.lua"))
    {
        failure = "editor did not resolve out01 local lua module";
        return false;
    }

    if (session.mapEventOptions().empty())
    {
        failure = "editor did not expose any lua-derived map events for out01";
        return false;
    }

    const std::optional<std::string> enterTrueMettle = session.describeMapEvent(171);

    if (!enterTrueMettle || enterTrueMettle->find("True Mettle") == std::string::npos)
    {
        failure = "editor did not resolve event 171 from out01.lua";
        return false;
    }

    const std::optional<std::string> openPairedChest = session.describeMapEvent(81);

    if (!openPairedChest || openPairedChest->find("Chest") == std::string::npos)
    {
        failure = "editor did not resolve chest event 81 from out01.lua";
        return false;
    }

    return true;
}

bool verifyNewOutdoorMapCreation(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    std::string &failure)
{
    OpenYAMM::Editor::EditorSession session;
    session.initialize(assetFileSystem);

    if (!session.createNewOutdoorMap(
            "__editor_headless_new_map",
            "Headless New Map",
            OpenYAMM::Editor::EditorOutdoorMapTilesetPreset::Grassland,
            failure))
    {
        failure = "could not create headless outdoor map: " + failure;
        return false;
    }

    const std::filesystem::path gamesPath = activeWorldEditorPath(assetFileSystem, "maps");
    const std::filesystem::path scenePath = gamesPath / "__editor_headless_new_map.scene.yml";
    const std::filesystem::path mapPath = gamesPath / "__editor_headless_new_map.odm";
    const std::filesystem::path packagePath = gamesPath / "__editor_headless_new_map.map.yml";
    const std::filesystem::path geometryMetadataPath = gamesPath / "__editor_headless_new_map.geometry.yml";
    const std::filesystem::path terrainMetadataPath = gamesPath / "__editor_headless_new_map.terrain.yml";
    const std::filesystem::path scriptPath =
        activeWorldEditorPath(assetFileSystem, "events/maps/__editor_headless_new_map.lua");
    const std::filesystem::path mapStatsPath =
        activeWorldEditorPath(assetFileSystem, "data_tables/map_stats.txt");
    const std::filesystem::path mapNavigationPath =
        activeWorldEditorPath(assetFileSystem, "data_tables/map_navigation.txt");

    if (!std::filesystem::exists(scenePath)
        || !std::filesystem::exists(mapPath)
        || !std::filesystem::exists(packagePath)
        || !std::filesystem::exists(geometryMetadataPath)
        || !std::filesystem::exists(terrainMetadataPath)
        || !std::filesystem::exists(scriptPath))
    {
        failure = "new outdoor map creation did not emit the full package/file set";
        return false;
    }

    if (session.document().isDirty() || session.document().isRuntimeBuildDirty())
    {
        failure = "new outdoor map should be saved and built immediately after creation";
        return false;
    }

    const OpenYAMM::Game::OutdoorMapData &geometry = session.document().outdoorGeometry();
    const OpenYAMM::Game::OutdoorSceneData &scene = session.document().outdoorSceneData();

    if (!geometry.bmodels.empty() || !geometry.spawns.empty())
    {
        failure = "new outdoor map should start without outdoor geometry content";
        return false;
    }

    if (scene.entities.size() != 1 || scene.entities.front().entity.name != "party start")
    {
        failure = "new outdoor map should contain a default party start entity";
        return false;
    }

    if (scene.environment.masterTile != 0
        || scene.environment.tileSetLookupIndices != std::array<uint16_t, 4>{90, 126, 162, 414})
    {
        failure = "new outdoor map did not keep the expected grassland terrain preset";
        return false;
    }

    if (session.document().outdoorMapPackageMetadata().scriptModule
        != "Data/scripts/maps/__editor_headless_new_map.lua")
    {
        failure = "new outdoor map package did not get the expected default script module";
        return false;
    }

    if (session.document().outdoorMapPackageMetadata().mapStatsId <= 0)
    {
        failure = "new outdoor map package did not get a valid map stats id";
        return false;
    }

    std::ifstream mapStatsStream(mapStatsPath);
    std::string tableText{
        std::istreambuf_iterator<char>(mapStatsStream),
        std::istreambuf_iterator<char>()};

    if (tableText.find("__editor_headless_new_map.odm") == std::string::npos)
    {
        failure = "new outdoor map build did not update map_stats.txt";
        return false;
    }

    std::ifstream mapNavigationStream(mapNavigationPath);
    tableText.assign(std::istreambuf_iterator<char>(mapNavigationStream), std::istreambuf_iterator<char>());

    if (tableText.find("__editor_headless_new_map.odm") == std::string::npos)
    {
        failure = "new outdoor map build did not update map_navigation.txt";
        return false;
    }

    OpenYAMM::Editor::EditorDocument reloadedDocument;

    if (!reloadedDocument.loadOutdoorMapPackage(assetFileSystem, "__editor_headless_new_map.odm", failure))
    {
        failure = "could not reload created outdoor package: " + failure;
        return false;
    }

    if (!reloadedDocument.outdoorGeometry().bmodels.empty())
    {
        failure = "reloaded new outdoor map unexpectedly has bmodels";
        return false;
    }

    if (reloadedDocument.outdoorSceneData().entities.size() != 1
        || reloadedDocument.outdoorSceneData().entities.front().entity.name != "party start")
    {
        failure = "reloaded new outdoor map did not preserve the party start entity";
        return false;
    }

    return true;
}

bool verifyOutdoorSourceOnlyPackageLoad(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    std::string &failure)
{
    OpenYAMM::Editor::EditorSession session;
    session.initialize(assetFileSystem);

    if (!session.createNewOutdoorMap(
            "__editor_headless_source_only",
            "Headless Source Only",
            OpenYAMM::Editor::EditorOutdoorMapTilesetPreset::Grassland,
            failure))
    {
        failure = "could not create source-only test map: " + failure;
        return false;
    }

    const std::filesystem::path gamesPath = activeWorldEditorPath(assetFileSystem, "maps");
    const std::filesystem::path mapPath = gamesPath / "__editor_headless_source_only.odm";
    std::error_code removeError;
    std::filesystem::remove(mapPath, removeError);

    if (removeError)
    {
        failure = "could not remove compiled odm for source-only load test";
        return false;
    }

    OpenYAMM::Editor::EditorSession reloadedSession;
    reloadedSession.initialize(assetFileSystem);

    if (!reloadedSession.openOutdoorMap("__editor_headless_source_only.odm", failure))
    {
        failure = "could not open source-only outdoor package: " + failure;
        return false;
    }

    if (!reloadedSession.document().geometryPhysicalPath().empty()
        && std::filesystem::exists(reloadedSession.document().geometryPhysicalPath()))
    {
        failure = "source-only outdoor package unexpectedly depended on compiled odm";
        return false;
    }

    const OpenYAMM::Game::OutdoorMapData &geometry = reloadedSession.document().outdoorGeometry();

    if (!geometry.bmodels.empty())
    {
        failure = "source-only reloaded test map unexpectedly has bmodels";
        return false;
    }

    if (geometry.heightMap.size() != OpenYAMM::Game::OutdoorMapData::TerrainWidth
            * OpenYAMM::Game::OutdoorMapData::TerrainHeight
        || geometry.tileMap.size() != geometry.heightMap.size()
        || geometry.attributeMap.size() != geometry.heightMap.size())
    {
        failure = "source-only reloaded test map did not rebuild terrain arrays";
        return false;
    }

    if (reloadedSession.document().outdoorSceneData().entities.size() != 1
        || reloadedSession.document().outdoorSceneData().entities.front().entity.name != "party start")
    {
        failure = "source-only reloaded test map did not preserve scene semantics";
        return false;
    }

    return true;
}

bool verifyIndoorMapPackageLoad(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    std::string &failure)
{
    OpenYAMM::Game::IndoorMapData legacyIndoorGeometry = {};
    OpenYAMM::Game::MapDeltaData legacyMapDeltaData = {};

    if (!loadIndoorGeometry(assetFileSystem, "d18.blv", legacyIndoorGeometry, failure))
    {
        failure = "could not load legacy d18.blv geometry for indoor package test: " + failure;
        return false;
    }

    if (!loadLegacyIndoorMapDelta(assetFileSystem, "d18.blv", legacyIndoorGeometry, legacyMapDeltaData, failure))
    {
        failure = "could not load legacy d18.dlv for indoor package test: " + failure;
        return false;
    }

    std::vector<OpenYAMM::Game::IndoorSceneFaceAttributeOverride> expectedFaceAttributeOverrides;
    expectedFaceAttributeOverrides.reserve(legacyIndoorGeometry.faces.size());

    for (size_t faceIndex = 0; faceIndex < legacyIndoorGeometry.faces.size(); ++faceIndex)
    {
        if (faceIndex >= legacyMapDeltaData.faceAttributes.size())
        {
            failure = "legacy indoor map delta face attributes are shorter than indoor geometry";
            return false;
        }

        const uint32_t effectiveAttributes = legacyMapDeltaData.faceAttributes[faceIndex];

        if (effectiveAttributes == legacyIndoorGeometry.faces[faceIndex].attributes)
        {
            continue;
        }

        OpenYAMM::Game::IndoorSceneFaceAttributeOverride overrideEntry = {};
        overrideEntry.faceIndex = faceIndex;
        overrideEntry.legacyAttributes = effectiveAttributes;
        expectedFaceAttributeOverrides.push_back(std::move(overrideEntry));
    }

    OpenYAMM::Editor::EditorSession session;
    session.initialize(assetFileSystem);

    if (!session.openIndoorMap("d18.blv", failure))
    {
        failure = "could not open d18.blv for indoor package test: " + failure;
        return false;
    }

    OpenYAMM::Editor::EditorDocument &document = session.document();

    if (document.kind() != OpenYAMM::Editor::EditorDocument::Kind::Indoor)
    {
        failure = "indoor package test did not load an indoor document";
        return false;
    }

    if (document.indoorGeometry().faces.empty())
    {
        failure = "indoor package test loaded an empty indoor geometry";
        return false;
    }

    const std::filesystem::path gamesPath = activeWorldEditorPath(assetFileSystem, "maps");
    const std::filesystem::path tempSourceGlbPath = gamesPath / "__editor_headless_indoor_source.glb";

    {
        const std::string glbJson =
            "{\n"
            "  \"asset\": {\"version\": \"2.0\"},\n"
            "  \"buffers\": [{\"byteLength\": 92}],\n"
            "  \"bufferViews\": [\n"
            "    {\"buffer\": 0, \"byteOffset\": 0, \"byteLength\": 48, \"target\": 34962},\n"
            "    {\"buffer\": 0, \"byteOffset\": 48, \"byteLength\": 32, \"target\": 34962},\n"
            "    {\"buffer\": 0, \"byteOffset\": 80, \"byteLength\": 12, \"target\": 34963}\n"
            "  ],\n"
            "  \"accessors\": [\n"
            "    {\"bufferView\": 0, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC3\"},\n"
            "    {\"bufferView\": 1, \"componentType\": 5126, \"count\": 4, \"type\": \"VEC2\"},\n"
            "    {\"bufferView\": 2, \"componentType\": 5123, \"count\": 6, \"type\": \"SCALAR\"}\n"
            "  ],\n"
            "  \"materials\": [{\"name\": \"StoneWall\"}],\n"
            "  \"meshes\": [{\"name\": \"semantic_surface\", \"primitives\": ["
            "{\"attributes\": {\"POSITION\": 0, \"TEXCOORD_0\": 1}, \"indices\": 2, \"material\": 0, \"mode\": 4}"
            "]}],\n"
            "  \"nodes\": [\n"
            "    {\"name\": \"ROOM_entry\", \"mesh\": 0},\n"
            "    {\"name\": \"ROOM_main\", \"mesh\": 0},\n"
            "    {\"name\": \"PORTAL_entry_main\", \"mesh\": 0},\n"
            "    {\"name\": \"TRIGGER_button_open_gate\", \"mesh\": 0},\n"
            "    {\"name\": \"MECH_gate_74\", \"mesh\": 0},\n"
            "    {\"name\": \"DECOR_torch_01\", \"mesh\": 0},\n"
            "    {\"name\": \"LIGHT_torch_01\", \"mesh\": 0},\n"
            "    {\"name\": \"SPAWN_guard_01\", \"mesh\": 0}\n"
            "  ],\n"
            "  \"scenes\": [{\"nodes\": [0, 1, 2, 3, 4, 5, 6, 7]}],\n"
            "  \"scene\": 0\n"
            "}\n";
        std::vector<uint8_t> glbBinary;
        const float positions[] = {
            -128.0f, -128.0f, 0.0f,
             128.0f, -128.0f, 0.0f,
             128.0f,  128.0f, 0.0f,
            -128.0f,  128.0f, 0.0f
        };
        const float texCoords[] = {
            0.0f, 0.0f,
            1.0f, 0.0f,
            1.0f, 1.0f,
            0.0f, 1.0f
        };
        const uint16_t indices[] = {0, 1, 2, 0, 2, 3};
        appendBytes(glbBinary, positions, sizeof(positions));
        appendBytes(glbBinary, texCoords, sizeof(texCoords));
        appendBytes(glbBinary, indices, sizeof(indices));

        if (!writeGlbFile(tempSourceGlbPath, glbJson, glbBinary))
        {
            failure = "indoor package test could not create indoor source GLB fixture";
            return false;
        }
    }

    std::string importFailure;

    if (!session.importIndoorSourceGeometryFromModel(tempSourceGlbPath.string(), importFailure))
    {
        failure = "indoor package test could not import indoor source GLB metadata: " + importFailure;
        return false;
    }

    const OpenYAMM::Editor::EditorIndoorGeometryMetadata &importedSourceMetadata =
        document.indoorGeometryMetadata();

    if (!document.hasIndoorGeometryMetadata()
        || importedSourceMetadata.rooms.size() != 2
        || importedSourceMetadata.portals.size() != 1
        || importedSourceMetadata.surfaces.size() != 1
        || importedSourceMetadata.mechanisms.size() != 1
        || importedSourceMetadata.entities.size() != 1
        || importedSourceMetadata.lights.size() != 1
        || importedSourceMetadata.spawns.size() != 1)
    {
        failure = "indoor package test imported unexpected indoor source metadata counts";
        return false;
    }

    const std::vector<std::string> importedSourceDiagnostics = document.validate();

    if (!containsDiagnosticSubstring(importedSourceDiagnostics, "trigger has no event id")
        || !containsDiagnosticSubstring(importedSourceDiagnostics, "decoration list id is not set")
        || !containsDiagnosticSubstring(importedSourceDiagnostics, "radius must be greater than zero")
        || !containsDiagnosticSubstring(importedSourceDiagnostics, "type/index is not set"))
    {
        failure = "indoor package test did not report expected source metadata diagnostics";
        return false;
    }

    OpenYAMM::Editor::EditorIndoorGeometryMetadata &mutableImportedSourceMetadata =
        document.mutableIndoorGeometryMetadata();

    if (!mutableImportedSourceMetadata.surfaces.empty()
        && mutableImportedSourceMetadata.surfaces.front().trigger.has_value())
    {
        mutableImportedSourceMetadata.surfaces.front().trigger->eventId = 14;
    }

    if (!mutableImportedSourceMetadata.entities.empty())
    {
        mutableImportedSourceMetadata.entities.front().decorationListId = 7;
        mutableImportedSourceMetadata.entities.front().eventIdPrimary = 15;
    }

    if (!mutableImportedSourceMetadata.lights.empty())
    {
        mutableImportedSourceMetadata.lights.front().color = {255, 180, 96};
        mutableImportedSourceMetadata.lights.front().radius = 512;
        mutableImportedSourceMetadata.lights.front().brightness = 128;
    }

    if (!mutableImportedSourceMetadata.spawns.empty())
    {
        mutableImportedSourceMetadata.spawns.front().typeId = 1;
        mutableImportedSourceMetadata.spawns.front().index = 3;
        mutableImportedSourceMetadata.spawns.front().radius = 256;
        mutableImportedSourceMetadata.spawns.front().group = 2;
    }

    const OpenYAMM::Editor::EditorIndoorGeometryMetadata &compiledSourceMetadata =
        document.indoorGeometryMetadata();

    if (compiledSourceMetadata.rooms.front().id != "room_entry"
        || compiledSourceMetadata.portals.front().frontRoom != "room_entry"
        || compiledSourceMetadata.portals.front().backRoom != "room_main"
        || compiledSourceMetadata.surfaces.front().id != "button_open_gate"
        || compiledSourceMetadata.mechanisms.front().id != "gate_74"
        || compiledSourceMetadata.mechanisms.front().doorId.value_or(0) != 74)
    {
        failure = "indoor package test imported unexpected indoor source metadata ids";
        return false;
    }

    OpenYAMM::Editor::IndoorSourceGeometryCompileResult sourceCompileResult = {};

    if (!OpenYAMM::Editor::compileIndoorSourceGeometry(
            tempSourceGlbPath,
            compiledSourceMetadata,
            sourceCompileResult,
            failure))
    {
        failure = "indoor package test could not compile indoor source geometry: " + failure;
        return false;
    }

    if (sourceCompileResult.indoorGeometry.sectors.size() != 2
        || sourceCompileResult.indoorGeometry.vertices.size() != 20
        || sourceCompileResult.indoorGeometry.faces.size() != 10
        || sourceCompileResult.indoorGeometry.doorCount != 1
        || sourceCompileResult.generatedDoors.size() != 1
        || sourceCompileResult.indoorGeometry.entities.size() != 1
        || sourceCompileResult.indoorGeometry.lights.size() != 1
        || sourceCompileResult.indoorGeometry.spawns.size() != 1
        || sourceCompileResult.indoorGeometry.faces.front().textureName != "StoneWall"
        || sourceCompileResult.indoorGeometry.sectors[0].portalFaceIds.empty()
        || sourceCompileResult.indoorGeometry.sectors[1].portalFaceIds.empty())
    {
        failure = "indoor package test compiled unexpected indoor source geometry";
        return false;
    }

    if (sourceCompileResult.indoorGeometry.entities.front().decorationListId != 7
        || sourceCompileResult.indoorGeometry.entities.front().eventIdPrimary != 15
        || sourceCompileResult.indoorGeometry.lights.front().radius != 512
        || sourceCompileResult.indoorGeometry.lights.front().brightness != 128
        || sourceCompileResult.indoorGeometry.spawns.front().typeId != 1
        || sourceCompileResult.indoorGeometry.spawns.front().index != 3
        || sourceCompileResult.indoorGeometry.spawns.front().group != 2)
    {
        failure = "indoor package test compiled unexpected indoor source marker data";
        return false;
    }

    bool foundTriggerSurfaceFace = false;

    for (const OpenYAMM::Game::IndoorFace &face : sourceCompileResult.indoorGeometry.faces)
    {
        if (face.cogTriggered == 14
            && OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Clickable))
        {
            foundTriggerSurfaceFace = true;
            break;
        }
    }

    if (!foundTriggerSurfaceFace)
    {
        failure = "indoor package test did not compile source trigger surface face data";
        return false;
    }

    if (sourceCompileResult.generatedDoors.front().door.faceIds.size() != 2
        || sourceCompileResult.generatedDoors.front().door.vertexIds.size() != 4
        || sourceCompileResult.generatedDoors.front().door.sectorIds.size() != 1
        || sourceCompileResult.generatedDoors.front().door.doorId != 74
        || sourceCompileResult.generatedDoors.front().door.state
            != static_cast<uint16_t>(OpenYAMM::Game::EvtMechanismState::Closed))
    {
        failure = "indoor package test compiled unexpected indoor source mechanism data";
        return false;
    }

    const uint16_t sourcePortalFaceIndex = sourceCompileResult.indoorGeometry.sectors[0].portalFaceIds.front();

    if (sourcePortalFaceIndex >= sourceCompileResult.indoorGeometry.faces.size())
    {
        failure = "indoor package test compiled an out-of-range indoor portal face reference";
        return false;
    }

    const OpenYAMM::Game::IndoorFace &sourcePortalFace =
        sourceCompileResult.indoorGeometry.faces[sourcePortalFaceIndex];

    if (!sourcePortalFace.isPortal
        || sourcePortalFace.roomNumber != 0
        || sourcePortalFace.roomBehindNumber != 1)
    {
        failure = "indoor package test compiled incorrect indoor portal face data";
        return false;
    }

    OpenYAMM::Game::IndoorMapDataWriter sourceWriter = {};
    const std::optional<std::vector<uint8_t>> sourceBytes =
        sourceWriter.buildBytes(sourceCompileResult.indoorGeometry);

    if (!sourceBytes)
    {
        failure = "indoor package test could not serialize compiled indoor source geometry";
        return false;
    }

    OpenYAMM::Game::IndoorMapDataLoader sourceLoader = {};
    const std::optional<OpenYAMM::Game::IndoorMapData> reloadedSourceGeometry =
        sourceLoader.loadFromBytes(*sourceBytes);

    if (!reloadedSourceGeometry
        || reloadedSourceGeometry->sectors.size() != 2
        || reloadedSourceGeometry->vertices.size() != 20
        || reloadedSourceGeometry->faces.size() != 10
        || reloadedSourceGeometry->doorCount != 1
        || reloadedSourceGeometry->entities.size() != 1
        || reloadedSourceGeometry->lights.size() != 1
        || reloadedSourceGeometry->spawns.size() != 1
        || reloadedSourceGeometry->faces.front().textureName != "StoneWall"
        || reloadedSourceGeometry->sectors[0].portalFaceIds.empty()
        || reloadedSourceGeometry->sectors[1].portalFaceIds.empty())
    {
        failure = "indoor package test could not reload compiled indoor source geometry";
        return false;
    }

    if (reloadedSourceGeometry->entities.front().decorationListId != 7
        || reloadedSourceGeometry->entities.front().eventIdPrimary != 15
        || reloadedSourceGeometry->lights.front().radius != 512
        || reloadedSourceGeometry->lights.front().brightness != 128
        || reloadedSourceGeometry->spawns.front().typeId != 1
        || reloadedSourceGeometry->spawns.front().index != 3
        || reloadedSourceGeometry->spawns.front().group != 2)
    {
        failure = "indoor package test did not preserve compiled indoor source marker data";
        return false;
    }

    bool reloadedTriggerSurfaceFace = false;

    for (const OpenYAMM::Game::IndoorFace &face : reloadedSourceGeometry->faces)
    {
        if (face.cogTriggered == 14
            && OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Clickable))
        {
            reloadedTriggerSurfaceFace = true;
            break;
        }
    }

    if (!reloadedTriggerSurfaceFace)
    {
        failure = "indoor package test did not preserve source trigger surface face data";
        return false;
    }

    const uint16_t reloadedPortalFaceIndex = reloadedSourceGeometry->sectors[0].portalFaceIds.front();

    if (reloadedPortalFaceIndex >= reloadedSourceGeometry->faces.size()
        || !reloadedSourceGeometry->faces[reloadedPortalFaceIndex].isPortal
        || reloadedSourceGeometry->faces[reloadedPortalFaceIndex].roomNumber != 0
        || reloadedSourceGeometry->faces[reloadedPortalFaceIndex].roomBehindNumber != 1)
    {
        failure = "indoor package test did not preserve compiled indoor portal face data";
        return false;
    }

    const std::vector<OpenYAMM::Game::IndoorSceneFaceAttributeOverride> &loadedFaceAttributeOverrides =
        document.indoorSceneData().initialState.faceAttributeOverrides;

    if (loadedFaceAttributeOverrides.size() != expectedFaceAttributeOverrides.size())
    {
        failure = "indoor package test did not synthesize the expected indoor face attribute override count";
        return false;
    }

    for (size_t overrideIndex = 0; overrideIndex < expectedFaceAttributeOverrides.size(); ++overrideIndex)
    {
        const OpenYAMM::Game::IndoorSceneFaceAttributeOverride &expectedOverride =
            expectedFaceAttributeOverrides[overrideIndex];
        const OpenYAMM::Game::IndoorSceneFaceAttributeOverride &loadedOverride =
            loadedFaceAttributeOverrides[overrideIndex];

        if (loadedOverride.faceIndex != expectedOverride.faceIndex
            || loadedOverride.legacyAttributes != expectedOverride.legacyAttributes)
        {
            failure = "indoor package test synthesized incorrect indoor face attribute overrides";
            return false;
        }
    }

    const std::filesystem::path originalGeometryPath = document.geometryPhysicalPath();
    std::vector<uint8_t> originalGeometryBytes;

    if (originalGeometryPath.empty() || !readBinaryFileBytes(originalGeometryPath, originalGeometryBytes))
    {
        failure = "indoor package test could not read original d18.blv bytes";
        return false;
    }

    OpenYAMM::Game::IndoorSceneData &sceneData = document.mutableIndoorSceneData();
    sceneData.environment.skyTexture = "testsky";
    sceneData.environment.dayBitsRaw = 1;
    sceneData.environment.mapExtraBitsRaw = 0x20;
    sceneData.environment.fogWeakDistance = 2048;
    sceneData.environment.fogStrongDistance = 4096;
    sceneData.environment.ceiling = 7777;
    session.noteDocumentMutated({});

    std::string mutationFailure;

    if (!session.createOutdoorObject(OpenYAMM::Editor::EditorSelectionKind::Actor, 1024, 2048, 512, mutationFailure))
    {
        failure = "indoor package test could not create actor: " + mutationFailure;
        return false;
    }

    if (!session.createOutdoorObject(
            OpenYAMM::Editor::EditorSelectionKind::SpriteObject,
            1536,
            2304,
            640,
            mutationFailure))
    {
        failure = "indoor package test could not create sprite object: " + mutationFailure;
        return false;
    }

    if (!session.createOutdoorObject(OpenYAMM::Editor::EditorSelectionKind::Chest, 0, 0, 0, mutationFailure))
    {
        failure = "indoor package test could not create chest: " + mutationFailure;
        return false;
    }

    uint32_t expectedDoorId = 0;
    uint16_t expectedDoorState = 0;
    size_t expectedTriggerFaceIndex = 0;
    uint16_t expectedTriggerCogNumber = 0;
    uint16_t expectedTriggerEvent = 0;
    uint16_t expectedTriggerType = 0;
    uint16_t expectedTriggerTextureFrameCog = 0;

    if (!sceneData.initialState.doors.empty())
    {
        OpenYAMM::Game::IndoorSceneDoor &door = sceneData.initialState.doors.front();
        door.door.doorId += 1000;
        door.door.state = 2;
        expectedDoorId = door.door.doorId;
        expectedDoorState = door.door.state;
        session.noteDocumentMutated({});
    }

    if (!document.indoorGeometry().faces.empty())
    {
        const OpenYAMM::Game::IndoorFace &baseFace = document.indoorGeometry().faces.front();
        expectedTriggerFaceIndex = 0;
        expectedTriggerCogNumber = baseFace.cogNumber == 0 ? 77 : static_cast<uint16_t>(baseFace.cogNumber + 1);
        expectedTriggerEvent = baseFace.cogTriggered == 0 ? 14 : static_cast<uint16_t>(baseFace.cogTriggered + 1);
        expectedTriggerType =
            baseFace.cogTriggerType == 0 ? 1 : static_cast<uint16_t>(baseFace.cogTriggerType + 1);
        expectedTriggerTextureFrameCog =
            baseFace.textureFrameTableCog == 0 ? 33 : static_cast<uint16_t>(baseFace.textureFrameTableCog + 1);

        OpenYAMM::Game::IndoorSceneFaceAttributeOverride *pOverride =
            OpenYAMM::Game::findIndoorSceneFaceOverride(sceneData, expectedTriggerFaceIndex);

        if (pOverride == nullptr)
        {
            OpenYAMM::Game::IndoorSceneFaceAttributeOverride overrideEntry = {};
            overrideEntry.faceIndex = expectedTriggerFaceIndex;
            overrideEntry.cogNumber = expectedTriggerCogNumber;
            overrideEntry.cogTriggered = expectedTriggerEvent;
            overrideEntry.cogTriggerType = expectedTriggerType;
            overrideEntry.textureFrameTableCog = expectedTriggerTextureFrameCog;
            sceneData.initialState.faceAttributeOverrides.push_back(std::move(overrideEntry));
        }
        else
        {
            pOverride->cogNumber = expectedTriggerCogNumber;
            pOverride->cogTriggered = expectedTriggerEvent;
            pOverride->cogTriggerType = expectedTriggerType;
            pOverride->textureFrameTableCog = expectedTriggerTextureFrameCog;
        }

        session.noteDocumentMutated({});
    }

    const size_t expectedFaceCount = document.indoorGeometry().faces.size();
    const size_t expectedLightCount = document.indoorGeometry().lights.size();
    const size_t expectedEntityCount = document.indoorGeometry().entities.size();
    const size_t expectedSpawnCount = document.indoorGeometry().spawns.size();
    const size_t expectedActorCount = sceneData.initialState.actors.size();
    const size_t expectedSpriteObjectCount = sceneData.initialState.spriteObjects.size();
    const size_t expectedChestCount = sceneData.initialState.chests.size();
    const size_t expectedDoorCount = sceneData.initialState.doors.size();
    const std::string expectedSkyTexture = sceneData.environment.skyTexture;
    const int32_t expectedDayBitsRaw = sceneData.environment.dayBitsRaw;
    const uint32_t expectedMapExtraBitsRaw = sceneData.environment.mapExtraBitsRaw;
    const int32_t expectedFogWeakDistance = sceneData.environment.fogWeakDistance;
    const int32_t expectedFogStrongDistance = sceneData.environment.fogStrongDistance;
    const int32_t expectedCeiling = sceneData.environment.ceiling;
    const size_t expectedFaceOverrideCount = sceneData.initialState.faceAttributeOverrides.size();
    OpenYAMM::Editor::EditorIndoorGeometryMetadata &indoorGeometryMetadata =
        document.mutableIndoorGeometryMetadata();
    indoorGeometryMetadata.source.authoringFile = "source/d18.blend";
    indoorGeometryMetadata.source.assetPath = "source/d18.glb";
    indoorGeometryMetadata.source.rootNodeName = "d18";
    indoorGeometryMetadata.source.coordinateSystem = "openyamm_mm8";
    indoorGeometryMetadata.source.unitScale = 1.0f;
    indoorGeometryMetadata.importSettings.sourceFormat = "glb";
    indoorGeometryMetadata.importSettings.generateBsp = true;

    OpenYAMM::Editor::EditorIndoorGeometryMaterialMetadata material = {};
    material.id = "test_wall";
    material.sourceMaterial = "TestWall";
    material.texture = "dngnwall";
    material.facetType = "wall";
    indoorGeometryMetadata.materials.push_back(std::move(material));

    if (!document.indoorGeometry().sectors.empty())
    {
        OpenYAMM::Editor::EditorIndoorGeometryRoomMetadata room = {};
        room.roomId = 1;
        room.name = "Room 1";
        room.sourceNodeNames.push_back("room_001");
        room.runtimeSectorIndex = 0;
        indoorGeometryMetadata.rooms.push_back(std::move(room));
    }

    for (size_t faceIndex = 0; faceIndex < document.indoorGeometry().faces.size(); ++faceIndex)
    {
        if (!document.indoorGeometry().faces[faceIndex].isPortal)
        {
            continue;
        }

        OpenYAMM::Editor::EditorIndoorGeometryPortalMetadata portal = {};
        portal.portalId = 1;
        portal.name = "Portal 1";
        portal.frontRoomId = 1;
        portal.backRoomId = 1;
        portal.sourceNodeName = "portal_001";
        portal.runtimeFaceIndex = faceIndex;
        indoorGeometryMetadata.portals.push_back(std::move(portal));
        break;
    }

    if (document.indoorGeometry().doorCount > 0)
    {
        OpenYAMM::Editor::EditorIndoorGeometryMechanismMetadata mechanism = {};
        mechanism.id = "gate_001";
        mechanism.name = "Door 1";
        mechanism.kind = "sliding_door";
        mechanism.sourceNodeNames.push_back("door_001");
        mechanism.triggerSurfaceIds.push_back("button_001");
        mechanism.runtimeDoorIndex = 0;
        mechanism.doorId = 1;
        mechanism.initialState = "closed";

        if (!document.indoorGeometry().faces.empty())
        {
            OpenYAMM::Editor::EditorIndoorGeometrySurfaceMetadata surface = {};
            surface.id = "button_001";
            surface.sourceNodeName = "trigger_button_001";
            surface.materialId = "test_wall";
            surface.flags.push_back("clickable");
            surface.runtimeFaceIndex = 0;
            surface.trigger = OpenYAMM::Editor::EditorIndoorGeometrySurfaceTriggerMetadata{14, "door"};
            indoorGeometryMetadata.surfaces.push_back(std::move(surface));

            mechanism.affectedFaceIndices.push_back(0);
            mechanism.triggerFaceIndices.push_back(0);
        }

        if (!document.indoorGeometry().vertices.empty())
        {
            mechanism.affectedVertexIndices.push_back(0);
        }

        mechanism.moveAxis = std::array<float, 3>{0.0f, 0.0f, -1.0f};
        mechanism.moveDistance = 256.0f;
        mechanism.openSpeed = 64.0f;
        mechanism.closeSpeed = 64.0f;
        indoorGeometryMetadata.mechanisms.push_back(std::move(mechanism));
    }

    session.noteDocumentMutated({});

    OpenYAMM::Game::IndoorMapData builtIndoorGeometry = {};
    OpenYAMM::Game::MapDeltaData builtMapDeltaData = {};

    if (!document.buildIndoorAuthoredRuntimeState(builtIndoorGeometry, builtMapDeltaData, failure))
    {
        failure = "indoor package test could not build authored runtime state: " + failure;
        return false;
    }

    if (builtIndoorGeometry.faces.size() != expectedFaceCount
        || builtMapDeltaData.doors.size() != expectedDoorCount
        || builtMapDeltaData.actors.size() != expectedActorCount)
    {
        failure = "indoor package test built unexpected authored runtime counts";
        return false;
    }

    if (builtMapDeltaData.faceAttributes != legacyMapDeltaData.faceAttributes)
    {
        failure = "indoor package test did not rebuild indoor face attributes to match d18.dlv";
        return false;
    }

    if (expectedTriggerFaceIndex >= builtIndoorGeometry.faces.size())
    {
        failure = "indoor package test trigger override face index is out of range";
        return false;
    }

    const OpenYAMM::Game::IndoorFace &builtTriggerFace = builtIndoorGeometry.faces[expectedTriggerFaceIndex];

    if (builtTriggerFace.cogNumber != expectedTriggerCogNumber
        || builtTriggerFace.cogTriggered != expectedTriggerEvent
        || builtTriggerFace.cogTriggerType != expectedTriggerType
        || builtTriggerFace.textureFrameTableCog != expectedTriggerTextureFrameCog)
    {
        failure = "indoor package test did not apply indoor face trigger overrides into built runtime geometry";
        return false;
    }

    const std::filesystem::path tempScenePath = gamesPath / "__editor_headless_d18.scene.yml";
    const std::filesystem::path tempGeometryPath = gamesPath / "__editor_headless_d18.blv";
    const std::filesystem::path tempGeometryMetadataPath = gamesPath / "__editor_headless_d18.geometry.yml";

    if (!document.saveSourceAs(tempScenePath, failure))
    {
        failure = "indoor package test could not save source scene: " + failure;
        return false;
    }

    if (!std::filesystem::exists(tempScenePath))
    {
        failure = "indoor package test did not emit a saved .scene.yml";
        return false;
    }

    if (!std::filesystem::exists(tempGeometryMetadataPath))
    {
        failure = "indoor package test did not emit a saved indoor .geometry.yml";
        return false;
    }

    std::string savedSceneText;

    if (!readTextFileContents(tempScenePath, savedSceneText))
    {
        failure = "indoor package test could not read saved .scene.yml";
        return false;
    }

    OpenYAMM::Game::IndoorSceneYmlLoader savedSceneLoader = {};
    std::string savedSceneError;
    const std::optional<OpenYAMM::Game::IndoorSceneData> savedSceneData =
        savedSceneLoader.loadFromText(savedSceneText, savedSceneError);

    if (!savedSceneData)
    {
        failure = "indoor package test could not parse saved .scene.yml: " + savedSceneError;
        return false;
    }

    if (savedSceneData->initialState.faceAttributeOverrides.size() != expectedFaceOverrideCount)
    {
        failure = "indoor package test did not persist indoor face overrides";
        return false;
    }

    const OpenYAMM::Game::IndoorSceneFaceAttributeOverride *pSavedTriggerOverride =
        OpenYAMM::Game::findIndoorSceneFaceOverride(*savedSceneData, expectedTriggerFaceIndex);

    if (pSavedTriggerOverride == nullptr
        || pSavedTriggerOverride->cogNumber != expectedTriggerCogNumber
        || pSavedTriggerOverride->cogTriggered != expectedTriggerEvent
        || pSavedTriggerOverride->cogTriggerType != expectedTriggerType
        || pSavedTriggerOverride->textureFrameTableCog != expectedTriggerTextureFrameCog)
    {
        failure = "indoor package test did not persist indoor face trigger overrides";
        return false;
    }

    if (std::filesystem::exists(tempGeometryPath))
    {
        failure = "indoor package test unexpectedly emitted .blv during source save";
        return false;
    }

    std::string savedGeometryMetadataText;

    if (!readTextFileContents(tempGeometryMetadataPath, savedGeometryMetadataText))
    {
        failure = "indoor package test could not read saved indoor .geometry.yml";
        return false;
    }

    std::string savedGeometryMetadataError;
    const std::optional<OpenYAMM::Editor::EditorIndoorGeometryMetadata> savedGeometryMetadata =
        OpenYAMM::Editor::loadIndoorGeometryMetadataFromText(
            savedGeometryMetadataText,
            savedGeometryMetadataError);

    if (!savedGeometryMetadata)
    {
        failure = "indoor package test could not parse saved indoor .geometry.yml: " + savedGeometryMetadataError;
        return false;
    }

    if (savedGeometryMetadata->source.assetPath != "source/d18.glb"
        || savedGeometryMetadata->source.authoringFile != "source/d18.blend"
        || savedGeometryMetadata->materials.size() != indoorGeometryMetadata.materials.size()
        || savedGeometryMetadata->rooms.size() != indoorGeometryMetadata.rooms.size()
        || savedGeometryMetadata->portals.size() != indoorGeometryMetadata.portals.size()
        || savedGeometryMetadata->surfaces.size() != indoorGeometryMetadata.surfaces.size()
        || savedGeometryMetadata->mechanisms.size() != indoorGeometryMetadata.mechanisms.size())
    {
        failure = "indoor package test did not persist indoor source geometry metadata";
        return false;
    }

    if (!document.buildRuntimeAs(tempScenePath, failure))
    {
        failure = "indoor package test could not build .blv output: " + failure;
        return false;
    }

    if (!std::filesystem::exists(tempGeometryPath))
    {
        failure = "indoor package test did not emit built .blv output";
        return false;
    }

    std::vector<uint8_t> builtGeometryBytes;

    if (!readBinaryFileBytes(tempGeometryPath, builtGeometryBytes))
    {
        failure = "indoor package test could not read built .blv bytes";
        return false;
    }

    if (builtGeometryBytes != originalGeometryBytes)
    {
        failure = "indoor package test changed indoor geometry bytes during save/build";
        return false;
    }

    OpenYAMM::Editor::EditorSession reloadedSession;
    reloadedSession.initialize(assetFileSystem);

    if (!reloadedSession.openIndoorMap("__editor_headless_d18.blv", failure))
    {
        failure = "indoor package test could not reload saved indoor package: " + failure;
        return false;
    }

    const OpenYAMM::Editor::EditorDocument &reloadedDocument = reloadedSession.document();

    if (reloadedDocument.kind() != OpenYAMM::Editor::EditorDocument::Kind::Indoor)
    {
        failure = "reloaded indoor package did not stay indoor";
        return false;
    }

    if (!reloadedDocument.hasIndoorGeometryMetadata()
        || reloadedDocument.indoorGeometryMetadata().source.assetPath != "source/d18.glb"
        || reloadedDocument.indoorGeometryMetadata().materials.size() != indoorGeometryMetadata.materials.size()
        || reloadedDocument.indoorGeometryMetadata().rooms.size() != indoorGeometryMetadata.rooms.size()
        || reloadedDocument.indoorGeometryMetadata().surfaces.size() != indoorGeometryMetadata.surfaces.size()
        || reloadedDocument.indoorGeometryMetadata().mechanisms.size() != indoorGeometryMetadata.mechanisms.size())
    {
        failure = "reloaded indoor package lost indoor source geometry metadata";
        return false;
    }

    if (reloadedDocument.indoorGeometry().faces.size() != expectedFaceCount
        || reloadedDocument.indoorGeometry().lights.size() != expectedLightCount
        || reloadedDocument.indoorGeometry().entities.size() != expectedEntityCount
        || reloadedDocument.indoorGeometry().spawns.size() != expectedSpawnCount
        || reloadedDocument.indoorSceneData().initialState.actors.size() != expectedActorCount
        || reloadedDocument.indoorSceneData().initialState.spriteObjects.size() != expectedSpriteObjectCount
        || reloadedDocument.indoorSceneData().initialState.chests.size() != expectedChestCount
        || reloadedDocument.indoorSceneData().initialState.doors.size() != expectedDoorCount)
    {
        failure = "reloaded indoor package changed indoor authored counts";
        return false;
    }

    if (reloadedDocument.indoorSceneData().environment.skyTexture != expectedSkyTexture
        || reloadedDocument.indoorSceneData().environment.dayBitsRaw != expectedDayBitsRaw
        || reloadedDocument.indoorSceneData().environment.mapExtraBitsRaw != expectedMapExtraBitsRaw
        || reloadedDocument.indoorSceneData().environment.fogWeakDistance != expectedFogWeakDistance
        || reloadedDocument.indoorSceneData().environment.fogStrongDistance != expectedFogStrongDistance
        || reloadedDocument.indoorSceneData().environment.ceiling != expectedCeiling)
    {
        failure = "reloaded indoor package changed indoor environment values";
        return false;
    }

    if (!reloadedDocument.indoorSceneData().initialState.doors.empty())
    {
        const OpenYAMM::Game::IndoorSceneDoor &door = reloadedDocument.indoorSceneData().initialState.doors.front();

        if (door.door.doorId != expectedDoorId || door.door.state != expectedDoorState)
        {
            failure = "reloaded indoor package changed indoor door override values";
            return false;
        }
    }

    OpenYAMM::Game::IndoorMapData reloadedBuiltIndoorGeometry = {};
    OpenYAMM::Game::MapDeltaData reloadedBuiltMapDeltaData = {};

    if (!reloadedSession.document().buildIndoorAuthoredRuntimeState(
            reloadedBuiltIndoorGeometry,
            reloadedBuiltMapDeltaData,
            failure))
    {
        failure = "reloaded indoor package could not rebuild authored runtime state: " + failure;
        return false;
    }

    if (expectedTriggerFaceIndex >= reloadedBuiltIndoorGeometry.faces.size())
    {
        failure = "reloaded indoor package trigger face index is out of range";
        return false;
    }

    const OpenYAMM::Game::IndoorFace &reloadedTriggerFace = reloadedBuiltIndoorGeometry.faces[expectedTriggerFaceIndex];

    if (reloadedTriggerFace.cogNumber != expectedTriggerCogNumber
        || reloadedTriggerFace.cogTriggered != expectedTriggerEvent
        || reloadedTriggerFace.cogTriggerType != expectedTriggerType
        || reloadedTriggerFace.textureFrameTableCog != expectedTriggerTextureFrameCog)
    {
        failure = "reloaded indoor package lost indoor face trigger overrides";
        return false;
    }

    return true;
}

bool verifyOutdoorMapPackageLifecycle(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    std::string &failure)
{
    OpenYAMM::Editor::EditorSession session;
    session.initialize(assetFileSystem);

    if (!session.openOutdoorMap("out01.odm", failure))
    {
        failure = "could not load out01.odm for lifecycle test: " + failure;
        return false;
    }

    if (!session.saveActiveDocumentAs("__editor_headless_save_as", "Headless Save As", failure))
    {
        failure = "could not save-as outdoor package in lifecycle test: " + failure;
        return false;
    }

    const std::filesystem::path gamesPath = activeWorldEditorPath(assetFileSystem, "maps");
    const std::filesystem::path scenePath = gamesPath / "__editor_headless_save_as.scene.yml";
    const std::filesystem::path mapPath = gamesPath / "__editor_headless_save_as.odm";
    const std::filesystem::path packagePath = gamesPath / "__editor_headless_save_as.map.yml";
    const std::filesystem::path geometryMetadataPath = gamesPath / "__editor_headless_save_as.geometry.yml";
    const std::filesystem::path terrainMetadataPath = gamesPath / "__editor_headless_save_as.terrain.yml";

    if (!std::filesystem::exists(scenePath)
        || !std::filesystem::exists(mapPath)
        || !std::filesystem::exists(packagePath)
        || !std::filesystem::exists(geometryMetadataPath)
        || !std::filesystem::exists(terrainMetadataPath))
    {
        failure = "save-as lifecycle test did not emit the full package/file set";
        return false;
    }

    if (session.document().outdoorMapPackageMetadata().displayName != "Headless Save As")
    {
        failure = "save-as lifecycle test lost explicit display name";
        return false;
    }

    if (session.document().outdoorMapPackageMetadata().scriptModule
        != "Data/scripts/maps/__editor_headless_save_as.lua")
    {
        failure = "save-as lifecycle test did not retarget the script module";
        return false;
    }

    if (!session.deleteActiveDocumentPackage(failure))
    {
        failure = "could not delete duplicated package in lifecycle test: " + failure;
        return false;
    }

    if (std::filesystem::exists(scenePath)
        || std::filesystem::exists(mapPath)
        || std::filesystem::exists(packagePath)
        || std::filesystem::exists(geometryMetadataPath)
        || std::filesystem::exists(terrainMetadataPath))
    {
        failure = "delete lifecycle test left package files behind";
        return false;
    }

    return true;
}

bool verifyOutdoorSpriteObjectPlacementDefaults(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    std::string &failure)
{
    OpenYAMM::Editor::EditorSession session;
    session.initialize(assetFileSystem);

    if (!session.openOutdoorMap("out01.odm", failure))
    {
        failure = "could not load out01.odm for sprite object placement test: " + failure;
        return false;
    }

    std::optional<uint16_t> selectedObjectDescriptionId;

    for (const OpenYAMM::Editor::EditorIdLabelOption &option : session.objectOptions())
    {
        const OpenYAMM::Game::ObjectEntry *pObjectEntry = session.objectTable().get(static_cast<uint16_t>(option.id));

        if (pObjectEntry != nullptr && pObjectEntry->spriteId != 0)
        {
            selectedObjectDescriptionId = static_cast<uint16_t>(option.id);
            break;
        }
    }

    if (!selectedObjectDescriptionId)
    {
        failure = "could not find a sprite-backed object description for placement test";
        return false;
    }

    session.setPendingSpriteObjectDescriptionId(*selectedObjectDescriptionId);

    if (!session.createOutdoorObject(OpenYAMM::Editor::EditorSelectionKind::SpriteObject, 100, 200, 300, failure))
    {
        failure = "could not create sprite object in placement test: " + failure;
        return false;
    }

    const OpenYAMM::Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

    if (sceneData.initialState.spriteObjects.empty())
    {
        failure = "sprite object placement test did not create a sprite object";
        return false;
    }

    const OpenYAMM::Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects.back();
    const OpenYAMM::Game::ObjectEntry *pObjectEntry = session.objectTable().get(*selectedObjectDescriptionId);

    if (pObjectEntry == nullptr)
    {
        failure = "sprite object placement test lost the chosen object entry";
        return false;
    }

    if (spriteObject.objectDescriptionId != *selectedObjectDescriptionId)
    {
        failure = "sprite object placement test did not preserve pending object description id";
        return false;
    }

    if (spriteObject.spriteId != pObjectEntry->spriteId)
    {
        failure = "sprite object placement test did not seed sprite id from object table";
        return false;
    }

    return true;
}

bool verifyOutdoorEntityPlacementDefaults(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    std::string &failure)
{
    OpenYAMM::Editor::EditorSession session;
    session.initialize(assetFileSystem);

    if (!session.openOutdoorMap("out01.odm", failure))
    {
        failure = "could not load out01.odm for entity placement test: " + failure;
        return false;
    }

    std::optional<uint16_t> selectedDecorationId;

    for (const OpenYAMM::Editor::EditorIdLabelOption &option : session.decorationOptions())
    {
        const OpenYAMM::Game::DecorationEntry *pDecoration =
            session.decorationTable().get(static_cast<uint16_t>(option.id));

        if (pDecoration != nullptr && pDecoration->spriteId != 0)
        {
            selectedDecorationId = static_cast<uint16_t>(option.id);
            break;
        }
    }

    if (!selectedDecorationId)
    {
        failure = "could not find a sprite-backed decoration for entity placement test";
        return false;
    }

    session.setPendingEntityDecorationListId(*selectedDecorationId);

    if (!session.createOutdoorObject(OpenYAMM::Editor::EditorSelectionKind::Entity, 100, 200, 300, failure))
    {
        failure = "could not create entity in placement test: " + failure;
        return false;
    }

    const OpenYAMM::Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

    if (sceneData.entities.empty())
    {
        failure = "entity placement test did not create an entity";
        return false;
    }

    const OpenYAMM::Game::OutdoorSceneEntity &entity = sceneData.entities.back();
    const OpenYAMM::Game::DecorationEntry *pDecoration = session.decorationTable().get(*selectedDecorationId);

    if (pDecoration == nullptr)
    {
        failure = "entity placement test lost the chosen decoration entry";
        return false;
    }

    if (entity.entity.decorationListId != *selectedDecorationId)
    {
        failure = "entity placement test did not preserve pending decoration id";
        return false;
    }

    if (entity.entity.name != pDecoration->internalName)
    {
        failure = "entity placement test did not seed entity name from decoration";
        return false;
    }

    return true;
}

bool isCanonicalLegacyBackedOutdoorMap(const std::filesystem::path &gamesPath, const std::string &mapFileName)
{
    const std::filesystem::path scenePath =
        gamesPath / (std::filesystem::path(mapFileName).stem().string() + ".scene.yml");
    std::ifstream input(scenePath);

    if (!input)
    {
        return false;
    }

    std::string line;

    while (std::getline(input, line))
    {
        if (line.find("legacy_companion_file:") != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

void removeTemporaryRoundTripScenes(const std::filesystem::path &gamesPath)
{
    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(gamesPath))
    {
        if (entry.is_regular_file() && entry.path().filename().string().starts_with("__editor_headless_"))
        {
            const std::string fileName = entry.path().filename().string();

            if (fileName.ends_with(".scene.yml")
                || fileName.ends_with(".geometry.yml")
                || fileName.ends_with(".map.yml")
                || fileName.ends_with(".terrain.yml")
                || fileName.ends_with(".odm")
                || fileName.ends_with(".blv")
                || fileName.ends_with(".obj")
                || fileName.ends_with(".gltf")
                || fileName.ends_with(".glb")
                || fileName.ends_with(".bin"))
            {
                std::filesystem::remove(entry.path());
            }
        }
    }
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

void removeTemporaryRowsFromTable(const std::filesystem::path &path, size_t keyColumn)
{
    std::ifstream stream(path);

    if (!stream)
    {
        return;
    }

    std::vector<std::vector<std::string>> rows;
    std::string line;

    while (std::getline(stream, line))
    {
        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        rows.push_back(splitTabSeparatedLine(line));
    }

    std::vector<std::vector<std::string>> filteredRows;
    filteredRows.reserve(rows.size());

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= keyColumn)
        {
            filteredRows.push_back(row);
            continue;
        }

        const std::string normalizedKey = row[keyColumn];

        if (normalizedKey.starts_with("__editor_headless_") || normalizedKey.starts_with("__EDITOR_HEADLESS_"))
        {
            continue;
        }

        filteredRows.push_back(row);
    }

    std::ofstream output(path, std::ios::trunc);

    for (size_t rowIndex = 0; rowIndex < filteredRows.size(); ++rowIndex)
    {
        output << joinTabSeparatedRow(filteredRows[rowIndex]);

        if (rowIndex + 1 < filteredRows.size())
        {
            output << '\n';
        }
    }
}

void removeTemporaryRoundTripSupportFiles(const Engine::AssetFileSystem &assetFileSystem)
{
    removeTemporaryRowsFromTable(activeWorldDevelopmentPath(assetFileSystem, "data_tables/map_stats.txt"), 2);
    removeTemporaryRowsFromTable(activeWorldDevelopmentPath(assetFileSystem, "data_tables/map_navigation.txt"), 0);
    const std::filesystem::path scriptsPath = activeWorldDevelopmentPath(assetFileSystem, "events/maps");

    if (!std::filesystem::exists(scriptsPath))
    {
        return;
    }

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(scriptsPath))
    {
        if (!entry.is_regular_file())
        {
            continue;
        }

        if (entry.path().filename().string().starts_with("__editor_headless_")
            && entry.path().extension() == ".lua")
        {
            std::filesystem::remove(entry.path());
        }
    }
}
}

EditorHeadlessDiagnostics::EditorHeadlessDiagnostics(const OpenYAMM::Engine::ApplicationConfig &config)
    : m_config(config)
{
}

int EditorHeadlessDiagnostics::runRegressionSuite(
    const std::filesystem::path &basePath,
    const std::string &suiteName) const
{
    const bool runParityChecks = suiteName == "outdoor-scene-yml-parity";
    const bool runLuaEventDiscoveryChecks = suiteName == "outdoor-lua-event-discovery";
    const bool runNewMapCreationChecks = suiteName == "outdoor-new-map-creation";
    const bool runSourceOnlyPackageLoadChecks = suiteName == "outdoor-source-only-package-load";
    const bool runIndoorPackageLoadChecks = suiteName == "indoor-map-package-load";
    const bool runMapPackageLifecycleChecks = suiteName == "outdoor-map-package-lifecycle";
    const bool runEntityPlacementChecks = suiteName == "outdoor-entity-placement";
    const bool runSpriteObjectPlacementChecks = suiteName == "outdoor-sprite-object-placement";
    const bool runRoundTripChecks =
        suiteName == "outdoor-scene-yml-parity"
        || suiteName == "outdoor-scene-yml-roundtrip"
        || suiteName == "outdoor-geometry-yml-roundtrip"
        || suiteName == "outdoor-terrain-yml-roundtrip"
        || suiteName == "outdoor-save-build-separation"
        || suiteName == "outdoor-map-package-roundtrip"
        || suiteName == "outdoor-map-package-build-state"
        || runLuaEventDiscoveryChecks
        || runNewMapCreationChecks
        || runSourceOnlyPackageLoadChecks
        || runIndoorPackageLoadChecks
        || runMapPackageLifecycleChecks
        || runEntityPlacementChecks
        || runSpriteObjectPlacementChecks;

    if (!runRoundTripChecks)
    {
        std::cerr << "Unknown editor regression suite: " << suiteName << '\n';
        return 2;
    }

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Editor headless diagnostics failed: could not initialize asset file system\n";
        return 1;
    }

    const std::filesystem::path gamesPath = activeWorldDevelopmentPath(assetFileSystem, "maps");

    if (!std::filesystem::exists(gamesPath))
    {
        std::cerr << "Editor headless diagnostics failed: games directory not found: " << gamesPath << '\n';
        return 1;
    }

    removeTemporaryRoundTripScenes(gamesPath);
    removeTemporaryRoundTripScenes(activeWorldEditorPath(assetFileSystem, "maps"));
    removeTemporaryRoundTripSupportFiles(assetFileSystem);

    if (runLuaEventDiscoveryChecks)
    {
        std::string failure;

        if (!verifyOutdoorLuaEventDiscovery(assetFileSystem, failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        std::cout << "Editor headless regression: suite=" << suiteName << " maps=1\n";
        std::cout << "  pass out01.odm\n";
        std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
        removeTemporaryRoundTripScenes(gamesPath);
        removeTemporaryRoundTripSupportFiles(assetFileSystem);
        return 0;
    }

    if (runNewMapCreationChecks)
    {
        std::string failure;

        if (!verifyNewOutdoorMapCreation(assetFileSystem, failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        std::cout << "Editor headless regression: suite=" << suiteName << " maps=1\n";
        std::cout << "  pass __editor_headless_new_map.odm\n";
        std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
        removeTemporaryRoundTripScenes(gamesPath);
        removeTemporaryRoundTripSupportFiles(assetFileSystem);
        return 0;
    }

    if (runSourceOnlyPackageLoadChecks)
    {
        std::string failure;

        if (!verifyOutdoorSourceOnlyPackageLoad(assetFileSystem, failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        std::cout << "Editor headless regression: suite=" << suiteName << " maps=1\n";
        std::cout << "  pass __editor_headless_source_only.odm\n";
        std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
        removeTemporaryRoundTripScenes(gamesPath);
        removeTemporaryRoundTripSupportFiles(assetFileSystem);
        return 0;
    }

    if (runIndoorPackageLoadChecks)
    {
        std::string failure;

        if (!verifyIndoorMapPackageLoad(assetFileSystem, failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        std::cout << "Editor headless regression: suite=" << suiteName << " maps=1\n";
        std::cout << "  pass d18.blv\n";
        std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
        removeTemporaryRoundTripScenes(activeWorldEditorPath(assetFileSystem, "maps"));
        removeTemporaryRoundTripSupportFiles(assetFileSystem);
        return 0;
    }

    if (runMapPackageLifecycleChecks)
    {
        std::string failure;

        if (!verifyOutdoorMapPackageLifecycle(assetFileSystem, failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        std::cout << "Editor headless regression: suite=" << suiteName << " maps=1\n";
        std::cout << "  pass __editor_headless_save_as.odm\n";
        std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
        removeTemporaryRoundTripScenes(gamesPath);
        removeTemporaryRoundTripSupportFiles(assetFileSystem);
        return 0;
    }

    if (runEntityPlacementChecks)
    {
        std::string failure;

        if (!verifyOutdoorEntityPlacementDefaults(assetFileSystem, failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        std::cout << "Editor headless regression: suite=" << suiteName << " maps=1\n";
        std::cout << "  pass out01.odm\n";
        std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
        removeTemporaryRoundTripScenes(gamesPath);
        removeTemporaryRoundTripSupportFiles(assetFileSystem);
        return 0;
    }

    if (runSpriteObjectPlacementChecks)
    {
        std::string failure;

        if (!verifyOutdoorSpriteObjectPlacementDefaults(assetFileSystem, failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        std::cout << "Editor headless regression: suite=" << suiteName << " maps=1\n";
        std::cout << "  pass out01.odm\n";
        std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
        removeTemporaryRoundTripScenes(gamesPath);
        removeTemporaryRoundTripSupportFiles(assetFileSystem);
        return 0;
    }

    std::vector<std::string> mapFileNames;

    std::unordered_set<std::string> seenMapFileNames;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(gamesPath))
    {
        if (!entry.is_regular_file())
        {
            continue;
        }

        const std::string fileName = entry.path().filename().string();
        std::string mapFileName;

        if (fileName.ends_with(".map.yml"))
        {
            mapFileName = entry.path().stem().stem().string() + ".odm";
        }
        else if (fileName.ends_with(".scene.yml"))
        {
            mapFileName = entry.path().stem().stem().string() + ".odm";
        }
        else
        {
            continue;
        }

        if (seenMapFileNames.insert(mapFileName).second)
        {
            if (!isCanonicalLegacyBackedOutdoorMap(gamesPath, mapFileName))
            {
                continue;
            }

            mapFileNames.push_back(mapFileName);
        }
    }

    std::sort(mapFileNames.begin(), mapFileNames.end());

    if (mapFileNames.empty())
    {
        std::cerr << "Editor headless diagnostics failed: no outdoor map packages or scene yml files found\n";
        return 1;
    }

    std::cout << "Editor headless regression: suite=" << suiteName
              << " maps=" << mapFileNames.size() << '\n';

    for (const std::string &mapFileName : mapFileNames)
    {
        std::string failure;

        if (runParityChecks && !compareOutdoorSceneAgainstLegacy(assetFileSystem, mapFileName, failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        if (!verifyOutdoorSceneRoundTrip(
                assetFileSystem,
                mapFileName,
                suiteName == "outdoor-save-build-separation" || suiteName == "outdoor-map-package-build-state",
                suiteName == "outdoor-map-package-roundtrip" || suiteName == "outdoor-map-package-build-state",
                suiteName == "outdoor-map-package-build-state",
                failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        std::cout << "  pass " << mapFileName << '\n';
    }

    std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
    removeTemporaryRoundTripScenes(gamesPath);
    removeTemporaryRoundTripSupportFiles(assetFileSystem);
    return 0;
}

int EditorHeadlessDiagnostics::runCompareOutdoorScene(
    const std::filesystem::path &basePath,
    const std::string &mapFileName) const
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Editor headless diagnostics failed: could not initialize asset file system\n";
        return 1;
    }

    removeTemporaryRoundTripScenes(activeWorldDevelopmentPath(assetFileSystem, "maps"));
    removeTemporaryRoundTripSupportFiles(assetFileSystem);

    std::string failure;

    if (!compareOutdoorSceneAgainstLegacy(assetFileSystem, mapFileName, failure))
    {
        std::cerr << "Editor headless compare failed: " << failure << '\n';
        return 1;
    }

    if (!verifyOutdoorSceneRoundTrip(assetFileSystem, mapFileName, false, false, false, failure))
    {
        std::cerr << "Editor headless compare failed: " << failure << '\n';
        return 1;
    }

    std::cout << "Editor headless compare passed: " << mapFileName << '\n';
    removeTemporaryRoundTripScenes(activeWorldDevelopmentPath(assetFileSystem, "maps"));
    removeTemporaryRoundTripSupportFiles(assetFileSystem);
    return 0;
}
}
