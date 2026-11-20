#include "game/indoor/IndoorBakeSceneExport.h"

#include "engine/AssetFileSystem.h"
#include "game/FaceEnums.h"
#include "game/data/GameDataLoader.h"
#include "game/events/EventRuntime.h"
#include "game/indoor/IndoorBakedLighting.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/MapDeltaData.h"
#include "game/render/IndoorStaticLighting.h"
#include "game/render/WaterGeometry.h"
#include "game/tables/LiquidTable.h"

#include <algorithm>
#include <fstream>
#include <iomanip>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
void writeJsonString(std::ostream &out, const std::string &text)
{
    out << '"';
    for (char character : text)
    {
        if (character == '"' || character == '\\')
        {
            out << '\\';
        }
        out << character;
    }
    out << '"';
}
}

int exportIndoorBakeScene(
    const Engine::ApplicationConfig &config,
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    const std::filesystem::path &outputPath)
{
    Engine::AssetFileSystem assetFileSystem;
    if (!assetFileSystem.initialize(basePath, config.assetRoot, config.assetScaleTier, config.assetScaleProfile,
            config.activeWorldId))
    {
        std::cerr << "Indoor bake export failed: could not initialize asset file system\n";
        return 1;
    }
    GameDataLoader gameDataLoader;
    // Decoration billboards (their lights) without any baked lighting, which this export is about to replace.
    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem)
        || !gameDataLoader.loadMapByFileNameForDecorationPlacements(assetFileSystem, mapFileName))
    {
        std::cerr << "Indoor bake export failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }
    const std::optional<MapAssetInfo> &map = gameDataLoader.getSelectedMap();
    if (!map || !map->indoorMapData)
    {
        std::cerr << "Indoor bake export failed: not an indoor map\n";
        return 1;
    }

    const IndoorMapData &mapData = *map->indoorMapData;
    const MapDeltaData *pDelta = map->indoorMapDeltaData ? &*map->indoorMapDeltaData : nullptr;
    const EventRuntimeState *pState = map->eventRuntimeState ? &*map->eventRuntimeState : nullptr;
    const std::vector<IndoorVertex> vertices = buildIndoorMechanismAdjustedVertices(mapData, pDelta, pState);
    // The doors that move each face: a face a single door moves rigidly is baked in the BLV's stored pose
    // (indoorMoverFaceBakeable), the game moving its lightmap with it.
    std::vector<std::vector<const MapDeltaDoor *>> faceDoors(mapData.faces.size());
    if (pDelta != nullptr)
    {
        for (const MapDeltaDoor &door : pDelta->doors)
        {
            for (uint16_t faceId : door.faceIds)
            {
                if (faceId < faceDoors.size()
                    && std::find(faceDoors[faceId].begin(), faceDoors[faceId].end(), &door) == faceDoors[faceId].end())
                {
                    faceDoors[faceId].push_back(&door);
                }
            }
        }
    }
    const std::vector<BakedStaticLightSource> lights = buildBakedStaticLightSources(
        mapData, pState, map->indoorDecorationBillboardSet ? &*map->indoorDecorationBillboardSet : nullptr, false);
    // The map's liquids: a see-through one (liquids.yml opacity) lets light through to its bed.
    LiquidTable liquids;
    if (const std::optional<std::string> liquidYaml = assetFileSystem.readTextFile("engine/liquids/liquids.yml"))
    {
        std::string error;
        LiquidTable allLiquids;
        if (!allLiquids.loadFromYaml(*liquidYaml, error))
        {
            std::cerr << "Indoor bake export failed: liquids: " << error << '\n';
            return 1;
        }
        liquids = allLiquids.forWorld(map->map.worldId);
    }

    std::ofstream out(outputPath);
    out << std::setprecision(9);
    out << "{\"map\": ";
    writeJsonString(out, map->map.fileName);
    out << ", \"world\": ";
    writeJsonString(out, map->map.worldId);
    out << ", \"geometry_path\": ";
    writeJsonString(out, map->geometryPath);
    out << ", \"scene_path\": ";
    writeJsonString(out, map->scenePath ? *map->scenePath : std::string());
    out << ", \"face_count\": " << mapData.faces.size() << ", \"sector_count\": " << mapData.sectors.size()
        << ", \"light_scale\": " << IndoorBakedStaticLightScale << ",\n \"sector_ambient\": [";
    for (size_t sectorId = 0; sectorId < mapData.sectors.size(); ++sectorId)
    {
        out << (sectorId == 0 ? "" : ", ") << IndoorLightingRuntime::ambientFromMinAmbientLightLevel(
            IndoorLightingRuntime::sectorAmbientLevel(mapData, pState, sectorId));
    }
    out << "],\n \"lights\": [";
    for (size_t index = 0; index < lights.size(); ++index)
    {
        const BakedStaticLightSource &light = lights[index];
        out << (index == 0 ? "" : ",") << "\n  {\"position\": [" << light.position.x << ", " << light.position.y
            << ", " << light.position.z << "], \"radius\": " << light.radius << ", \"color\": ["
            << int(light.red) << ", " << int(light.green) << ", " << int(light.blue) << "], \"alpha\": "
            << light.alpha << ", \"source\": " << light.sourceId << "}";
    }
    // Faces the renderer draws: not portals (unless translucent), with a texture and three vertices. "visible" is
    // false for invisible faces (collision only: they neither receive nor cast); "mover" for the faces a door moves,
    // "points" in their load pose; "mover_receiver" for the movers the bake lightmaps, in their stored pose
    // ("stored_points"); "translucency" for a translucent face (devdocs/INDOOR_TRANSLUCENT_FACES.md) and for a face of a
    // see-through liquid (its opacity, untinted), which let light through in the bake.
    out << "],\n \"faces\": [";
    bool first = true;
    for (size_t faceIndex = 0; faceIndex < mapData.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = mapData.faces[faceIndex];
        if ((face.isPortal && findIndoorFaceTranslucency(mapData, faceIndex) == nullptr)
            || face.textureName.empty() || face.vertexIndices.size() < 3)
        {
            continue;
        }
        const uint32_t attributes = pDelta != nullptr && faceIndex < pDelta->faceAttributes.size()
            ? pDelta->faceAttributes[faceIndex] : face.attributes;
        const bool visible = !hasFaceAttribute(attributes, FaceAttribute::Invisible)
            && (pState == nullptr || !pState->hasFacetInvisibleOverride(uint32_t(faceIndex)));
        out << (first ? "" : ",") << "\n  {\"index\": " << faceIndex << ", \"sector\": " << face.roomNumber
            << ", \"back_sector\": " << face.roomBehindNumber << ", \"texture\": ";
        writeJsonString(out, face.textureName);
        out << ", \"attributes\": " << attributes << ", \"visible\": " << (visible ? "true" : "false")
            << ", \"mover\": " << (faceDoors[faceIndex].empty() ? "false" : "true") << ", \"mover_receiver\": "
            << (!faceDoors[faceIndex].empty() && indoorMoverFaceBakeable(face, faceDoors[faceIndex],
                   findIndoorMoverDefinition(mapData, faceDoors[faceIndex].front()->doorId)) ? "true" : "false")
            << ", \"plane_normal\": ";
        if (face.planeNormal)
        {
            out << "[" << (*face.planeNormal)[0] << ", " << (*face.planeNormal)[1] << ", " << (*face.planeNormal)[2]
                << "]";
        }
        else
        {
            out << "null";
        }
        out << ", \"points\": [";
        for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
        {
            const uint16_t vertexIndex = face.vertexIndices[corner];
            const IndoorVertex vertex = vertexIndex < vertices.size() ? vertices[vertexIndex] : IndoorVertex{};
            out << (corner == 0 ? "" : ", ") << "[" << vertex.x << ", " << vertex.y << ", " << vertex.z << "]";
        }
        out << "]";
        const LiquidDefinition *pLiquid = liquids.findMatch(face.textureName, attributes, false);
        if (const IndoorFaceTranslucency *pTranslucency = findIndoorFaceTranslucency(mapData, faceIndex))
        {
            out << ", \"translucency\": {\"opacity\": " << pTranslucency->opacity << ", \"tint\": ["
                << pTranslucency->tint[0] << ", " << pTranslucency->tint[1] << ", " << pTranslucency->tint[2]
                << "], \"two_sided\": " << (pTranslucency->twoSided ? "true" : "false") << "}";
        }
        else if (pLiquid != nullptr && pLiquid->opacity < 1.0f
            && faceLiquidKind(attributes, pLiquid->kind) != LiquidKind::None)
        {
            out << ", \"translucency\": {\"opacity\": " << pLiquid->opacity
                << ", \"tint\": [1, 1, 1], \"two_sided\": false}";
        }
        if (!faceDoors[faceIndex].empty())
        {
            out << ", \"stored_points\": [";
            for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
            {
                const uint16_t vertexIndex = face.vertexIndices[corner];
                const IndoorVertex vertex =
                    vertexIndex < mapData.vertices.size() ? mapData.vertices[vertexIndex] : IndoorVertex{};
                out << (corner == 0 ? "" : ", ") << "[" << vertex.x << ", " << vertex.y << ", " << vertex.z << "]";
            }
            out << "]";
        }
        out << "}";
        first = false;
    }
    out << "\n]}\n";
    if (!out)
    {
        std::cerr << "Indoor bake export failed: cannot write " << outputPath << '\n';
        return 1;
    }
    std::cout << "Exported " << mapData.faces.size() << " faces and " << lights.size() << " lights to " << outputPath
              << '\n';
    return 0;
}
}
