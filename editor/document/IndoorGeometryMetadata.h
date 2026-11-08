#pragma once

#include "game/indoor/IndoorMapData.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Editor
{
struct EditorIndoorGeometrySourceAsset
{
    std::string authoringFile;
    std::string assetPath;
    std::string rootNodeName;
    std::string coordinateSystem = "blender_z_up";
    float unitScale = 128.0f;
};

struct EditorIndoorGeometryImportSettings
{
    std::string sourceFormat = "glb";
    float mergeVerticesEpsilon = 0.01f;
    bool mergeCoplanarFaces = false;
    bool triangulateNgons = true;
    bool generateBsp = true;
    bool generateOutlines = true;
    bool generatePortals = true;
    bool reserveSectorZero = false;
};

struct EditorIndoorGeometryMaterialMetadata
{
    std::string id;
    std::string sourceMaterial;
    std::string texture;
    uint32_t textureWidth = 256;
    uint32_t textureHeight = 256;
    std::vector<std::string> flags;
    std::string facetType;
};

struct EditorIndoorGeometryRoomMetadata
{
    std::string id;
    uint32_t roomId = 0;
    int16_t minAmbientLightLevel = 0;
    std::string name;
    std::vector<std::string> sourceNodeNames;
    std::optional<size_t> runtimeSectorIndex = std::nullopt;
};

struct EditorIndoorGeometryPortalMetadata
{
    std::string id;
    uint32_t portalId = 0;
    std::string name;
    std::string frontRoom;
    std::string backRoom;
    uint32_t frontRoomId = 0;
    uint32_t backRoomId = 0;
    std::string sourceNodeName;
    std::vector<std::string> flags;
    std::optional<size_t> runtimeFaceIndex = std::nullopt;
};

struct EditorIndoorGeometrySurfaceTriggerMetadata
{
    uint16_t eventId = 0;
    std::string type;
};

struct EditorIndoorGeometrySurfaceMetadata
{
    std::string id;
    std::string sourceNodeName;
    std::string materialId;
    std::vector<std::string> flags;
    std::optional<EditorIndoorGeometrySurfaceTriggerMetadata> trigger = std::nullopt;
    // The face's cog number, the id evt.SetFacetBit and evt.SetTexture address it by (0: none).
    uint16_t cogNumber = 0;
    // A second room the faces bound (the BLV face's room behind, empty: none): a non-portal face is drawn when
    // either room is visible. For faces in a wall's thickness that both rooms see (jambs, reveals, wall bases).
    std::string backRoomId;
    std::optional<size_t> runtimeFaceIndex = std::nullopt;
};

struct EditorIndoorGeometryMechanismMetadata
{
    std::string id;
    uint32_t mechanismId = 0;
    std::string name;
    std::string kind;
    std::vector<std::string> sourceNodeNames;
    std::vector<std::string> triggerSurfaceIds;
    // A `rotating` mover: the other room its swing enters (at most one; its faces then belong to both).
    std::vector<std::string> extraRoomIds;
    std::optional<size_t> runtimeDoorIndex = std::nullopt;
    std::optional<uint32_t> doorId = std::nullopt;
    std::string initialState;
    // Native direction points from open to closed; source geometry may represent either endpoint.
    std::string sourcePose = "open";
    std::vector<size_t> affectedFaceIndices;
    std::vector<size_t> affectedVertexIndices;
    std::vector<size_t> triggerFaceIndices;
    std::optional<std::array<float, 3>> moveAxis = std::nullopt;
    std::optional<float> moveDistance = std::nullopt;
    std::optional<uint32_t> moveLength = std::nullopt;
    std::optional<float> openSpeed = std::nullopt;
    std::optional<float> closeSpeed = std::nullopt;
};

struct EditorIndoorGeometryEntityMetadata
{
    std::string id;
    std::string kind;
    std::string sourceNodeName;
    uint16_t decorationListId = 0;
    uint16_t eventIdPrimary = 0;
    uint16_t eventIdSecondary = 0;
    // Degrees, as the BLV entity stores it; a model decoration bound with yaw: facing turns by it.
    int facing = 0;
    std::optional<size_t> runtimeEntityIndex = std::nullopt;
};

struct EditorIndoorGeometryLightMetadata
{
    std::string id;
    std::string sourceNodeName;
    std::array<uint8_t, 3> color = {255, 255, 255};
    int16_t radius = 0;
    int16_t brightness = 0;
    std::string type = "point";
    // The BLV light id: lights sharing a group switch together with evt.SetLight(group, on) (0: none).
    int32_t group = 0;
    std::optional<size_t> runtimeLightIndex = std::nullopt;
};

struct EditorIndoorGeometrySpawnMetadata
{
    std::string id;
    std::string sourceNodeName;
    uint16_t typeId = 0;
    uint16_t index = 0;
    uint16_t radius = 0;
    uint32_t group = 0;
    std::optional<size_t> runtimeSpawnIndex = std::nullopt;
};

struct EditorIndoorGeometryMetadata
{
    uint32_t version = 2;
    std::string mapFileName;
    EditorIndoorGeometrySourceAsset source = {};
    EditorIndoorGeometryImportSettings importSettings = {};
    std::vector<EditorIndoorGeometryMaterialMetadata> materials;
    std::vector<EditorIndoorGeometryRoomMetadata> rooms;
    std::vector<EditorIndoorGeometryPortalMetadata> portals;
    std::vector<EditorIndoorGeometrySurfaceMetadata> surfaces;
    std::vector<EditorIndoorGeometryMechanismMetadata> mechanisms;
    std::vector<EditorIndoorGeometryEntityMetadata> entities;
    std::vector<EditorIndoorGeometryLightMetadata> lights;
    std::vector<EditorIndoorGeometrySpawnMetadata> spawns;
};

std::string serializeIndoorGeometryMetadata(const EditorIndoorGeometryMetadata &metadata);

std::optional<EditorIndoorGeometryMetadata> loadIndoorGeometryMetadataFromText(
    const std::string &yamlText,
    std::string &errorMessage);

void normalizeIndoorGeometryMetadata(EditorIndoorGeometryMetadata &metadata, const std::string &mapFileName);

bool isIndoorGeometryMetadataEmpty(const EditorIndoorGeometryMetadata &metadata);

std::vector<std::string> validateIndoorGeometryMetadata(
    const EditorIndoorGeometryMetadata &metadata,
    const Game::IndoorMapData &indoorGeometry);
}
