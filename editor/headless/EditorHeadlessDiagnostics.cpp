#include "editor/headless/EditorHeadlessDiagnostics.h"

#include "editor/document/EditorSession.h"
#include "editor/document/EditorDocument.h"
#include "engine/AssetFileSystem.h"
#include "game/maps/MapDeltaData.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"

#include <algorithm>
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

    const std::filesystem::path tempDirectory =
        assetFileSystem.getDevelopmentRoot() / "Data" / "games";
    const std::filesystem::path tempImportPath = tempDirectory / "__editor_headless_import.obj";

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

    if (!document.mutableOutdoorGeometry().bmodels.empty())
    {
        session.select(OpenYAMM::Editor::EditorSelectionKind::BModel, 0);

        if (!session.replaceSelectedBModelFromObj(tempImportPath.string(), 1.0f, "grastyl", errorMessage))
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

    if (!session.importNewBModelFromObj(tempImportPath.string(), 1.0f, "dirttyl", errorMessage))
    {
        failure = "could not import new bmodel from OBJ during round-trip test for "
            + mapFileName + ": " + errorMessage;
        return false;
    }

    const size_t importedBModelIndex = document.mutableOutdoorGeometry().bmodels.empty()
        ? 0
        : (document.mutableOutdoorGeometry().bmodels.size() - 1);
    const std::optional<OpenYAMM::Editor::EditorBModelSourceTransform> savedSourceTransform =
        document.outdoorBModelSourceTransform(importedBModelIndex);

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

    if (!document.mutableOutdoorGeometry().bmodels.empty())
    {
        const std::optional<OpenYAMM::Editor::EditorBModelImportSource> reloadedImportSource =
            reloadedDocument.outdoorBModelImportSource(importedBModelIndex);

        if (!reloadedImportSource)
        {
            failure = "reloaded geometry metadata lost remembered bmodel import source for " + mapFileName;
            return false;
        }

        const std::optional<OpenYAMM::Editor::EditorBModelSourceTransform> reloadedSourceTransform =
            reloadedDocument.outdoorBModelSourceTransform(importedBModelIndex);

        if (!savedSourceTransform || !reloadedSourceTransform)
        {
            failure = "reloaded geometry metadata lost remembered bmodel source transform for " + mapFileName;
            return false;
        }

        if (!nearlyEqualFloat(savedSourceTransform->originX, reloadedSourceTransform->originX)
            || !nearlyEqualFloat(savedSourceTransform->originY, reloadedSourceTransform->originY)
            || !nearlyEqualFloat(savedSourceTransform->originZ, reloadedSourceTransform->originZ))
        {
            failure = "reloaded geometry metadata changed bmodel source transform origin for " + mapFileName;
            return false;
        }

        if (!nearlyEqualFloat(savedSourceTransform->basisX[0], reloadedSourceTransform->basisX[0])
            || !nearlyEqualFloat(savedSourceTransform->basisX[1], reloadedSourceTransform->basisX[1])
            || !nearlyEqualFloat(savedSourceTransform->basisX[2], reloadedSourceTransform->basisX[2])
            || !nearlyEqualFloat(savedSourceTransform->basisY[0], reloadedSourceTransform->basisY[0])
            || !nearlyEqualFloat(savedSourceTransform->basisY[1], reloadedSourceTransform->basisY[1])
            || !nearlyEqualFloat(savedSourceTransform->basisY[2], reloadedSourceTransform->basisY[2])
            || !nearlyEqualFloat(savedSourceTransform->basisZ[0], reloadedSourceTransform->basisZ[0])
            || !nearlyEqualFloat(savedSourceTransform->basisZ[1], reloadedSourceTransform->basisZ[1])
            || !nearlyEqualFloat(savedSourceTransform->basisZ[2], reloadedSourceTransform->basisZ[2]))
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

    if (!openPairedChest || openPairedChest->find("paired chest") == std::string::npos)
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

    const std::filesystem::path gamesPath = assetFileSystem.getDevelopmentRoot() / "Data" / "games";
    const std::filesystem::path scenePath = gamesPath / "__editor_headless_new_map.scene.yml";
    const std::filesystem::path mapPath = gamesPath / "__editor_headless_new_map.odm";
    const std::filesystem::path packagePath = gamesPath / "__editor_headless_new_map.map.yml";
    const std::filesystem::path geometryMetadataPath = gamesPath / "__editor_headless_new_map.geometry.yml";
    const std::filesystem::path terrainMetadataPath = gamesPath / "__editor_headless_new_map.terrain.yml";
    const std::filesystem::path scriptPath =
        assetFileSystem.getDevelopmentRoot() / "Data" / "scripts" / "maps" / "__editor_headless_new_map.lua";
    const std::filesystem::path mapStatsPath =
        assetFileSystem.getDevelopmentRoot() / "Data" / "data_tables" / "map_stats.txt";
    const std::filesystem::path mapNavigationPath =
        assetFileSystem.getDevelopmentRoot() / "Data" / "data_tables" / "map_navigation.txt";

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

    const std::filesystem::path gamesPath = assetFileSystem.getDevelopmentRoot() / "Data" / "games";
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

    const std::filesystem::path gamesPath = assetFileSystem.getDevelopmentRoot() / "Data" / "games";
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
                || fileName.ends_with(".odm"))
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

void removeTemporaryRoundTripSupportFiles(const std::filesystem::path &developmentRoot)
{
    removeTemporaryRowsFromTable(developmentRoot / "Data" / "data_tables" / "map_stats.txt", 2);
    removeTemporaryRowsFromTable(developmentRoot / "Data" / "data_tables" / "map_navigation.txt", 0);
    const std::filesystem::path scriptsPath = developmentRoot / "Data" / "scripts" / "maps";

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

    const std::filesystem::path gamesPath = assetFileSystem.getDevelopmentRoot() / "Data" / "games";

    if (!std::filesystem::exists(gamesPath))
    {
        std::cerr << "Editor headless diagnostics failed: games directory not found: " << gamesPath << '\n';
        return 1;
    }

    removeTemporaryRoundTripScenes(gamesPath);
    removeTemporaryRoundTripSupportFiles(assetFileSystem.getDevelopmentRoot());

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
        removeTemporaryRoundTripSupportFiles(assetFileSystem.getDevelopmentRoot());
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
        removeTemporaryRoundTripSupportFiles(assetFileSystem.getDevelopmentRoot());
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
        removeTemporaryRoundTripSupportFiles(assetFileSystem.getDevelopmentRoot());
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
        removeTemporaryRoundTripSupportFiles(assetFileSystem.getDevelopmentRoot());
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
        removeTemporaryRoundTripSupportFiles(assetFileSystem.getDevelopmentRoot());
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
        removeTemporaryRoundTripSupportFiles(assetFileSystem.getDevelopmentRoot());
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
    removeTemporaryRoundTripSupportFiles(assetFileSystem.getDevelopmentRoot());
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

    removeTemporaryRoundTripScenes(assetFileSystem.getDevelopmentRoot() / "Data" / "games");
    removeTemporaryRoundTripSupportFiles(assetFileSystem.getDevelopmentRoot());

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
    removeTemporaryRoundTripScenes(assetFileSystem.getDevelopmentRoot() / "Data" / "games");
    removeTemporaryRoundTripSupportFiles(assetFileSystem.getDevelopmentRoot());
    return 0;
}
}
