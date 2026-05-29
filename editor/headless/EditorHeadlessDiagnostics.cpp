#include "editor/headless/EditorHeadlessDiagnostics.h"

#include "editor/document/EditorSession.h"
#include "editor/document/EditorDocument.h"
#include "editor/import/IndoorSourceGeometryCompiler.h"
#include "editor/import/ObjModelImport.h"
#include "editor/model/Mm9ModelInstanceActorResolver.h"
#include "engine/AssetFileSystem.h"
#include "engine/ImageAssetLoader.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/MapIdentity.h"
#include "game/maps/TerrainTileData.h"
#include "game/mm9/Mm9DtxTexture.h"
#include "game/mm9/Mm9LightLayer.h"
#include "game/mm9/Mm9SoundLayer.h"
#include "game/mm9/Mm9SpawnLayer.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"

#include <SDL3/SDL.h>
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
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

std::string lowerAsciiCopy(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return result;
}

Game::Mm9DatVec3 mm9TriangleVertexPosition(
    const Game::Mm9DatRenderTriangle &triangle,
    size_t vertexIndex)
{
    return {
        triangle.vertices[vertexIndex].x,
        triangle.vertices[vertexIndex].y,
        triangle.vertices[vertexIndex].z,
    };
}

Game::Mm9DatVec3 mm9Subtract(const Game::Mm9DatVec3 &left, const Game::Mm9DatVec3 &right)
{
    return {
        left.x - right.x,
        left.y - right.y,
        left.z - right.z,
    };
}

Game::Mm9DatVec3 mm9Add(const Game::Mm9DatVec3 &left, const Game::Mm9DatVec3 &right)
{
    return {
        left.x + right.x,
        left.y + right.y,
        left.z + right.z,
    };
}

Game::Mm9DatVec3 mm9Multiply(const Game::Mm9DatVec3 &value, float scalar)
{
    return {
        value.x * scalar,
        value.y * scalar,
        value.z * scalar,
    };
}

Game::Mm9DatVec3 mm9Cross(const Game::Mm9DatVec3 &left, const Game::Mm9DatVec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x,
    };
}

float mm9Dot(const Game::Mm9DatVec3 &left, const Game::Mm9DatVec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

float mm9Length(const Game::Mm9DatVec3 &value)
{
    return std::sqrt(mm9Dot(value, value));
}

std::optional<Game::Mm9DatVec3> mm9TriangleNormal(const Game::Mm9DatRenderTriangle &triangle)
{
    const Game::Mm9DatVec3 vertex0 = mm9TriangleVertexPosition(triangle, 0);
    const Game::Mm9DatVec3 vertex1 = mm9TriangleVertexPosition(triangle, 1);
    const Game::Mm9DatVec3 vertex2 = mm9TriangleVertexPosition(triangle, 2);
    const Game::Mm9DatVec3 normal = mm9Cross(mm9Subtract(vertex1, vertex0), mm9Subtract(vertex2, vertex0));
    const float normalLength = mm9Length(normal);

    if (normalLength <= 0.0001f)
    {
        return std::nullopt;
    }

    return Game::Mm9DatVec3{
        normal.x / normalLength,
        normal.y / normalLength,
        normal.z / normalLength,
    };
}

Game::Mm9DatVec3 mm9TriangleCenter(const Game::Mm9DatRenderTriangle &triangle)
{
    const Game::Mm9DatVec3 vertex0 = mm9TriangleVertexPosition(triangle, 0);
    const Game::Mm9DatVec3 vertex1 = mm9TriangleVertexPosition(triangle, 1);
    const Game::Mm9DatVec3 vertex2 = mm9TriangleVertexPosition(triangle, 2);

    return {
        (vertex0.x + vertex1.x + vertex2.x) / 3.0f,
        (vertex0.y + vertex1.y + vertex2.y) / 3.0f,
        (vertex0.z + vertex1.z + vertex2.z) / 3.0f,
    };
}

std::optional<Game::Mm9DatPickRay> mm9SyntheticPickRay(const Game::Mm9DatRenderMesh &mesh)
{
    for (const Game::Mm9DatRenderTriangle &triangle : mesh.triangles)
    {
        const std::optional<Game::Mm9DatVec3> normal = mm9TriangleNormal(triangle);

        if (!normal)
        {
            continue;
        }

        Game::Mm9DatPickRay ray = {};
        ray.origin = mm9Add(mm9TriangleCenter(triangle), mm9Multiply(*normal, 2.0f));
        ray.direction = mm9Multiply(*normal, -1.0f);
        return ray;
    }

    return std::nullopt;
}

bool validateMm9SyntheticPick(
    const Game::Mm9DatRenderMesh &mesh,
    std::optional<Game::Mm9DatRenderMeshPickHit> &hit,
    std::string &failure)
{
    const std::optional<Game::Mm9DatPickRay> ray = mm9SyntheticPickRay(mesh);

    if (!ray)
    {
        failure = "no non-degenerate native DAT triangle is available for synthetic picking";
        return false;
    }

    hit = Game::pickMm9DatRenderMesh(mesh, *ray);

    if (!hit)
    {
        failure = "native DAT synthetic pick ray missed the render mesh";
        return false;
    }

    if (hit->triangleIndex >= mesh.triangles.size())
    {
        failure = "native DAT synthetic pick returned an out-of-range triangle index";
        return false;
    }

    const Game::Mm9DatRenderTriangle &triangle = mesh.triangles[hit->triangleIndex];

    if (hit->sourceModelIndex != triangle.sourceModelIndex
        || hit->sourcePolyIndex != triangle.sourcePolyIndex
        || hit->sourceSurfaceIndex != triangle.sourceSurfaceIndex
        || hit->sourceTextureIndex != triangle.sourceTextureIndex
        || hit->sourceModelName != triangle.sourceModelName
        || hit->sourceTexture != triangle.sourceTexture)
    {
        failure = "native DAT synthetic pick source ids do not match the picked render triangle";
        return false;
    }

    if (!std::isfinite(hit->position.x)
        || !std::isfinite(hit->position.y)
        || !std::isfinite(hit->position.z)
        || !std::isfinite(hit->distance)
        || hit->distance <= 0.0f)
    {
        failure = "native DAT synthetic pick returned invalid hit position or distance";
        return false;
    }

    return true;
}

void writeYamlQuoted(std::ostream &stream, const std::string &value)
{
    stream << '"';

    for (unsigned char character : value)
    {
        switch (character)
        {
        case '\\':
            stream << "\\\\";
            break;
        case '"':
            stream << "\\\"";
            break;
        case '\n':
            stream << "\\n";
            break;
        case '\r':
            stream << "\\r";
            break;
        case '\t':
            stream << "\\t";
            break;
        default:
            if (character < 0x20)
            {
                stream << "\\x"
                       << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(character)
                       << std::dec << std::setfill(' ');
            }
            else
            {
                stream << static_cast<char>(character);
            }

            break;
        }
    }

    stream << '"';
}

void writeYamlScalar(std::ostream &stream, const std::string &indent, const std::string &key, const std::string &value)
{
    stream << indent << key << ": ";
    writeYamlQuoted(stream, value);
    stream << '\n';
}

void writeYamlScalar(std::ostream &stream, const std::string &indent, const std::string &key, const char *pValue)
{
    writeYamlScalar(stream, indent, key, std::string(pValue));
}

void writeYamlScalar(std::ostream &stream, const std::string &indent, const std::string &key, size_t value)
{
    stream << indent << key << ": " << value << '\n';
}

void writeYamlScalar(std::ostream &stream, const std::string &indent, const std::string &key, bool value)
{
    stream << indent << key << ": " << (value ? "true" : "false") << '\n';
}

template<typename ValueType>
ValueType yamlScalarValue(const YAML::Node &node, const char *pKey, const ValueType &defaultValue)
{
    if (!node || !node.IsMap())
    {
        return defaultValue;
    }

    const YAML::Node valueNode = node[pKey];

    if (!valueNode || !valueNode.IsScalar())
    {
        return defaultValue;
    }

    try
    {
        return valueNode.as<ValueType>();
    }
    catch (const YAML::Exception &)
    {
        return defaultValue;
    }
}

struct Mm9ValidationReportSummary
{
    std::filesystem::path path;
    std::string mapId;
    std::string displayName;
    std::string levelFile;
    bool clean = false;
    size_t levelLoadDiagnostics = 0;
    bool sourceMutationSnapshotVerified = false;
    size_t sourceMutationSnapshotFiles = 0;
    size_t sourceDatHashDiagnostics = 0;
    bool sourceDatHashVerified = false;
    size_t sourceManifestDiagnostics = 0;
    size_t sourceManifestExpectedFiles = 0;
    size_t sourceManifestActualFiles = 0;
    size_t sourceManifestCountDriftFamilies = 0;
    size_t sourceManifestMissingDirectories = 0;
    size_t documentPathsTotal = 0;
    size_t documentPathsMissing = 0;
    size_t documentPathsMissingRequired = 0;
    size_t documentPathsReadOnlySource = 0;
    size_t documentPathsGenerated = 0;
    size_t documentPathsAuthored = 0;
    size_t documentPathsAuthoredOverrides = 0;
    size_t documentPathsCompatibilityDerived = 0;
    size_t datWorldReferenceIssues = 0;
    size_t datWorldInvalidLeafReferences = 0;
    size_t datWorldInvalidSurfaceTextureRefs = 0;
    size_t datWorldInvalidPolySurfaceRefs = 0;
    size_t datWorldInvalidPolyPlaneRefs = 0;
    size_t datWorldInvalidPolyVertexRefs = 0;
    size_t datWorldInvalidNodePolyRefs = 0;
    size_t datWorldInvalidRootNodeRefs = 0;
    size_t assetGraphTotal = 0;
    size_t assetGraphResolved = 0;
    size_t assetGraphUnresolved = 0;
    size_t assetGraphAmbiguous = 0;
    size_t assetGraphStale = 0;
    size_t assetGraphRequiredTotal = 0;
    size_t assetGraphRequiredResolved = 0;
    size_t assetGraphRequiredUnresolved = 0;
    size_t assetGraphRequiredAmbiguous = 0;
    size_t assetGraphOptionalTotal = 0;
    size_t assetGraphOptionalResolved = 0;
    size_t assetGraphOptionalUnresolved = 0;
    size_t assetGraphOptionalAmbiguous = 0;
    size_t assetGraphSourceOnly = 0;
    size_t assetGraphUnusedSource = 0;
    size_t rawObjectAssetRefs = 0;
    size_t requiredRawObjectAssetRefs = 0;
    size_t optionalRawObjectAssetRefs = 0;
    size_t unresolvedRequiredRawObjectAssetRefs = 0;
    size_t unresolvedOptionalRawObjectAssetRefs = 0;
    size_t staleCaches = 0;
    size_t mechanismUnresolvedRequiredTargets = 0;
    size_t mechanismIncompleteLinearMotion = 0;
    size_t mechanismIncompleteRotationMotion = 0;
    size_t mechanismSoundSlots = 0;
    size_t mechanismAuthoredSoundReferences = 0;
    size_t mechanismEmptySoundReferences = 0;
    size_t mechanismPreviewableMechanisms = 0;
    size_t mechanismInertMechanisms = 0;
    size_t mechanismInertPreviewEntries = 0;
    size_t mechanismWithoutPreviewMotion = 0;
    size_t mechanismWithoutPreviewTarget = 0;
    size_t mechanismActivationStartOpenFields = 0;
    size_t mechanismActivationLockedFields = 0;
    size_t mechanismActivationPushOpenFields = 0;
    size_t mechanismActivationTouchToOpenFields = 0;
    size_t mechanismActivationLockOnCloseFields = 0;
    size_t mechanismActivationReopenOnContactFields = 0;
    size_t mechanismRotationOpenAwayFields = 0;
    size_t mechanismTimingMoveDelayFields = 0;
    size_t mechanismTimingOpenWaitFields = 0;
    size_t mechanismTriggerOutputs = 0;
    size_t mechanismUnresolvedTriggerOutputs = 0;
    size_t scriptIncludes = 0;
    size_t scriptLabels = 0;
    size_t scriptIncludeReferences = 0;
    size_t scriptResolvedIncludes = 0;
    size_t scriptUnresolvedIncludes = 0;
    size_t scriptAmbiguousIncludes = 0;
    size_t scriptRegisteredTriggers = 0;
    size_t scriptTriggerEdges = 0;
    size_t scriptMovementCommands = 0;
    size_t scriptUnknownCommands = 0;
    size_t scriptCommandCount = 0;
    size_t mechanismWorldModelTargetsWithoutMovableRole = 0;
    size_t mechanismWorldModelTargetsMissingModel = 0;
    size_t mechanismWorldModelTargetsMissingPolygonGroup = 0;
    size_t mechanismWorldModelTargetsMismatchedPolygonGroup = 0;
    size_t nativeRenderableTriangles = 0;
    size_t viewportNativeMissingMaterialTriangles = 0;
    size_t viewportNativePlaceholderMaterialTriangles = 0;
    size_t viewportNativeUnresolvedMaterialTriangles = 0;
    size_t nativeFilterVisual = 0;
    size_t nativeFilterInvisible = 0;
    size_t nativeFilterWater = 0;
    size_t nativeFilterVisibleWater = 0;
    size_t nativeFilterWaterVolume = 0;
    size_t nativeFilterRail = 0;
    size_t nativeFilterHelper = 0;
    size_t nativeFilterPhysics = 0;
    size_t nativeFilterVisibility = 0;
    size_t nativeFilterPortals = 0;
    size_t worldModelOverlayVertices = 0;
    size_t worldModelOverlayPickCandidates = 0;
    size_t selectedPolygonOverlayVertices = 0;
    size_t selectedSurfaceOverlayVertices = 0;
    size_t rawObjects = 0;
    size_t rawObjectSidecarIssues = 0;
    size_t objectSourceTransforms = 0;
    size_t objectBoundsEvidence = 0;
    size_t objectTriggerVolumes = 0;
    size_t objectOverlayVertices = 0;
    size_t objectOverlayPickCandidates = 0;
    size_t assetIssueMarkerSourceObjects = 0;
    size_t assetIssueMarkerCandidates = 0;
    size_t assetIssueMarkerUnpositioned = 0;
    size_t assetIssueMarkerRequiredCandidates = 0;
    size_t assetIssueMarkerRequiredUnpositioned = 0;
    size_t mechanismTargetMarkerGroups = 0;
    size_t mechanismTargetMarkerCandidates = 0;
    size_t mechanismTargetMarkerVertices = 0;
    size_t mechanismTargetMarkerSourceLinks = 0;
    size_t mechanismGizmoCandidates = 0;
    size_t mechanismCircleGizmoCandidates = 0;
    size_t mechanismTargetGizmoCandidates = 0;
    size_t mechanismMotionPathMarkers = 0;
    size_t mechanismLineOfSightCheckedCandidates = 0;
    size_t mechanismLineOfSightBlockedCandidates = 0;
    size_t lightObjects = 0;
    size_t lightOverlayVertices = 0;
    size_t staticRenderLights = 0;
    size_t lightDiagnostics = 0;
    size_t soundObjects = 0;
    size_t soundOverlayVertices = 0;
    size_t soundReferences = 0;
    size_t resolvedSoundReferences = 0;
    size_t unresolvedRequiredSoundReferences = 0;
    size_t spawnSourceObjects = 0;
    size_t spawnOverlayVertices = 0;
    size_t spawnNpcNumbers = 0;
    size_t modelInstances = 0;
    size_t modelInstancesInCameraFrame = 0;
    size_t missingModelInstanceAssets = 0;
    size_t missingDrawableModelInstanceGeometry = 0;
    size_t actorVariantCandidates = 0;
    size_t actorVariantGameplayIdentityRows = 0;
    size_t actorVariantFootSoundFields = 0;
    size_t actorVariantResolvedFootSounds = 0;
    size_t actorVariantUnresolvedFootSounds = 0;
    size_t actorVariantSourceSoundReferences = 0;
    size_t actorVariantResolvedSourceSoundReferences = 0;
    size_t actorVariantUnresolvedSourceSoundReferences = 0;
    size_t actorVariantSourceVoiceReferences = 0;
    size_t actorVariantResolvedSourceVoiceReferences = 0;
    size_t actorVariantUnresolvedSourceVoiceReferences = 0;
    size_t actorVariantUnresolved = 0;
    size_t scriptedObjectsWithModelCollisionVolumes = 0;
    size_t scriptedObjectsRequiringBillboardCollisionVisuals = 0;
    size_t missingScriptedObjectCollisionVisuals = 0;
    size_t mechanismPreviewCandidates = 0;
    size_t mechanismPreviewChangedBounds = 0;
    size_t materialTextures = 0;
    size_t resolvedDtx = 0;
    size_t ambiguousDtx = 0;
    size_t sourceDtxPaths = 0;
    size_t defaultHelperMaterials = 0;
    size_t placeholderMissingSourceMaterials = 0;
    size_t dtxHeaders = 0;
    size_t dtxHeadersMatchingSidecar = 0;
    size_t dtxUserFlagRecords = 0;
    size_t dtxExtraByteRecords = 0;
    size_t dtxMipPayloads = 0;
    size_t dtxDecodedPreviewMips = 0;
    size_t dtxSectionMetadataRecords = 0;
    size_t dtxSectionPayloadsAvailable = 0;
    size_t dtxCommandStrings = 0;
    size_t decodedCacheDeterminismChecked = 0;
    size_t decodedCacheSourceDecoded = 0;
    size_t decodedCacheImageDecoded = 0;
    size_t decodedCacheMatchesSource = 0;
    size_t decodedCacheMismatches = 0;
    size_t spriteMaterials = 0;
    size_t resolvedSpriteMaterials = 0;
    size_t spriteFrameTextures = 0;
    size_t resolvedSpriteFrameTextures = 0;
    size_t unresolvedSpriteFrameTextures = 0;
    size_t ambiguousSpriteFrameTextures = 0;
    size_t diagnosticErrors = 0;
    size_t diagnosticWarnings = 0;
    size_t diagnosticInfo = 0;
};

bool readMm9ValidationReportSummary(
    const std::filesystem::path &reportPath,
    Mm9ValidationReportSummary &summary,
    std::string &errorMessage)
{
    YAML::Node root;

    try
    {
        root = YAML::LoadFile(reportPath.string());
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = "could not parse validation report " + reportPath.generic_string() + ": " + exception.what();
        return false;
    }

    if (!root || !root.IsMap())
    {
        errorMessage = "validation report is not a YAML map: " + reportPath.generic_string();
        return false;
    }

    if (yamlScalarValue<std::string>(root, "kind", std::string()) != "mm9_asset_validation_report")
    {
        errorMessage = "validation report has unexpected kind: " + reportPath.generic_string();
        return false;
    }

    const YAML::Node reportSummaryNode = root["summary"];
    const YAML::Node datWorldReferenceNode = root["dat_world_reference_validation"];
    const YAML::Node assetGraphNode = root["asset_graph"];
    const YAML::Node mechanismNode = root["mechanisms"];
    const YAML::Node diagnosticsNode = root["diagnostics"];
    const YAML::Node sourceIntegrityNode = root["source_integrity"];
    const YAML::Node documentPathsNode = root["document_paths"];

    summary = {};
    summary.path = reportPath;
    summary.mapId = yamlScalarValue<std::string>(root, "map_id", std::string());
    summary.displayName = yamlScalarValue<std::string>(root, "display_name", std::string());
    summary.levelFile = yamlScalarValue<std::string>(root, "level_file", std::string());
    summary.clean = yamlScalarValue<bool>(root, "clean", false);
    summary.levelLoadDiagnostics =
        yamlScalarValue<size_t>(sourceIntegrityNode, "level_load_diagnostics", 0);
    summary.sourceMutationSnapshotVerified =
        yamlScalarValue<bool>(sourceIntegrityNode, "source_mutation_snapshot_verified", false);
    summary.sourceMutationSnapshotFiles =
        yamlScalarValue<size_t>(sourceIntegrityNode, "source_mutation_snapshot_files", 0);
    summary.sourceDatHashDiagnostics =
        yamlScalarValue<size_t>(sourceIntegrityNode, "source_dat_hash_diagnostics", 0);
    summary.sourceDatHashVerified =
        yamlScalarValue<bool>(sourceIntegrityNode, "source_dat_hash_verified", false);
    summary.sourceManifestDiagnostics =
        yamlScalarValue<size_t>(sourceIntegrityNode, "source_manifest_diagnostics", 0);
    summary.sourceManifestExpectedFiles =
        yamlScalarValue<size_t>(sourceIntegrityNode, "source_manifest_expected_files", 0);
    summary.sourceManifestActualFiles =
        yamlScalarValue<size_t>(sourceIntegrityNode, "source_manifest_actual_files", 0);
    summary.sourceManifestCountDriftFamilies =
        yamlScalarValue<size_t>(sourceIntegrityNode, "source_manifest_count_drift_families", 0);
    summary.sourceManifestMissingDirectories =
        yamlScalarValue<size_t>(sourceIntegrityNode, "source_manifest_missing_directories", 0);
    summary.documentPathsTotal = yamlScalarValue<size_t>(documentPathsNode, "total", 0);
    summary.documentPathsMissing = yamlScalarValue<size_t>(documentPathsNode, "missing", 0);
    summary.documentPathsMissingRequired = yamlScalarValue<size_t>(documentPathsNode, "missing_required", 0);
    summary.documentPathsReadOnlySource = yamlScalarValue<size_t>(documentPathsNode, "source_read_only", 0);
    summary.documentPathsGenerated = yamlScalarValue<size_t>(documentPathsNode, "generated", 0);
    summary.documentPathsAuthored = yamlScalarValue<size_t>(documentPathsNode, "authored", 0);
    summary.documentPathsAuthoredOverrides =
        yamlScalarValue<size_t>(documentPathsNode, "authored_overrides", 0);
    summary.documentPathsCompatibilityDerived =
        yamlScalarValue<size_t>(documentPathsNode, "compatibility_derived", 0);
    summary.datWorldReferenceIssues = yamlScalarValue<size_t>(datWorldReferenceNode, "issues", 0);
    summary.datWorldInvalidLeafReferences =
        yamlScalarValue<size_t>(reportSummaryNode, "dat_world_invalid_leaf_references", 0);
    summary.datWorldInvalidSurfaceTextureRefs =
        yamlScalarValue<size_t>(reportSummaryNode, "dat_world_invalid_surface_texture_refs", 0);
    summary.datWorldInvalidPolySurfaceRefs =
        yamlScalarValue<size_t>(reportSummaryNode, "dat_world_invalid_poly_surface_refs", 0);
    summary.datWorldInvalidPolyPlaneRefs =
        yamlScalarValue<size_t>(reportSummaryNode, "dat_world_invalid_poly_plane_refs", 0);
    summary.datWorldInvalidPolyVertexRefs =
        yamlScalarValue<size_t>(reportSummaryNode, "dat_world_invalid_poly_vertex_refs", 0);
    summary.datWorldInvalidNodePolyRefs =
        yamlScalarValue<size_t>(reportSummaryNode, "dat_world_invalid_node_poly_refs", 0);
    summary.datWorldInvalidRootNodeRefs =
        yamlScalarValue<size_t>(reportSummaryNode, "dat_world_invalid_root_node_refs", 0);
    summary.assetGraphTotal = yamlScalarValue<size_t>(assetGraphNode, "total", 0);
    summary.assetGraphResolved = yamlScalarValue<size_t>(assetGraphNode, "resolved", 0);
    summary.assetGraphUnresolved = yamlScalarValue<size_t>(assetGraphNode, "unresolved", 0);
    summary.assetGraphAmbiguous = yamlScalarValue<size_t>(assetGraphNode, "ambiguous", 0);
    summary.assetGraphStale = yamlScalarValue<size_t>(assetGraphNode, "stale", 0);
    summary.assetGraphRequiredTotal = yamlScalarValue<size_t>(assetGraphNode, "required_total", 0);
    summary.assetGraphRequiredResolved = yamlScalarValue<size_t>(assetGraphNode, "required_resolved", 0);
    summary.assetGraphRequiredUnresolved = yamlScalarValue<size_t>(assetGraphNode, "required_unresolved", 0);
    summary.assetGraphRequiredAmbiguous = yamlScalarValue<size_t>(assetGraphNode, "required_ambiguous", 0);
    summary.assetGraphOptionalTotal = yamlScalarValue<size_t>(assetGraphNode, "optional_total", 0);
    summary.assetGraphOptionalResolved = yamlScalarValue<size_t>(assetGraphNode, "optional_resolved", 0);
    summary.assetGraphOptionalUnresolved = yamlScalarValue<size_t>(assetGraphNode, "optional_unresolved", 0);
    summary.assetGraphOptionalAmbiguous = yamlScalarValue<size_t>(assetGraphNode, "optional_ambiguous", 0);
    summary.assetGraphSourceOnly = yamlScalarValue<size_t>(assetGraphNode, "source_only", 0);
    summary.assetGraphUnusedSource = yamlScalarValue<size_t>(assetGraphNode, "unused_source", 0);
    summary.rawObjectAssetRefs = yamlScalarValue<size_t>(reportSummaryNode, "raw_object_asset_refs", 0);
    summary.requiredRawObjectAssetRefs =
        yamlScalarValue<size_t>(reportSummaryNode, "required_raw_object_asset_refs", 0);
    summary.optionalRawObjectAssetRefs =
        yamlScalarValue<size_t>(reportSummaryNode, "optional_raw_object_asset_refs", 0);
    summary.unresolvedRequiredRawObjectAssetRefs =
        yamlScalarValue<size_t>(reportSummaryNode, "unresolved_required_raw_object_asset_refs", 0);
    summary.unresolvedOptionalRawObjectAssetRefs =
        yamlScalarValue<size_t>(reportSummaryNode, "unresolved_optional_raw_object_asset_refs", 0);
    summary.staleCaches = summary.assetGraphStale;
    summary.mechanismUnresolvedRequiredTargets =
        yamlScalarValue<size_t>(mechanismNode, "unresolved_required_targets", 0);
    summary.mechanismIncompleteLinearMotion =
        yamlScalarValue<size_t>(mechanismNode, "incomplete_linear_motion", 0);
    summary.mechanismIncompleteRotationMotion =
        yamlScalarValue<size_t>(mechanismNode, "incomplete_rotation_motion", 0);
    summary.mechanismSoundSlots = yamlScalarValue<size_t>(mechanismNode, "sound_slots", 0);
    summary.mechanismAuthoredSoundReferences =
        yamlScalarValue<size_t>(mechanismNode, "authored_sound_references", 0);
    summary.mechanismEmptySoundReferences =
        yamlScalarValue<size_t>(mechanismNode, "empty_sound_references", 0);
    summary.mechanismPreviewableMechanisms =
        yamlScalarValue<size_t>(mechanismNode, "previewable_mechanisms", 0);
    summary.mechanismInertMechanisms =
        yamlScalarValue<size_t>(mechanismNode, "inert_mechanisms", 0);
    summary.mechanismInertPreviewEntries =
        yamlScalarValue<size_t>(mechanismNode, "inert_preview_entries", 0);
    summary.mechanismWithoutPreviewMotion =
        yamlScalarValue<size_t>(mechanismNode, "without_preview_motion", 0);
    summary.mechanismWithoutPreviewTarget =
        yamlScalarValue<size_t>(mechanismNode, "without_preview_target", 0);
    summary.mechanismActivationStartOpenFields =
        yamlScalarValue<size_t>(mechanismNode, "activation_start_open_fields", 0);
    summary.mechanismActivationLockedFields =
        yamlScalarValue<size_t>(mechanismNode, "activation_locked_fields", 0);
    summary.mechanismActivationPushOpenFields =
        yamlScalarValue<size_t>(mechanismNode, "activation_push_open_fields", 0);
    summary.mechanismActivationTouchToOpenFields =
        yamlScalarValue<size_t>(mechanismNode, "activation_touch_to_open_fields", 0);
    summary.mechanismActivationLockOnCloseFields =
        yamlScalarValue<size_t>(mechanismNode, "activation_lock_on_close_fields", 0);
    summary.mechanismActivationReopenOnContactFields =
        yamlScalarValue<size_t>(mechanismNode, "activation_reopen_on_contact_fields", 0);
    summary.mechanismRotationOpenAwayFields =
        yamlScalarValue<size_t>(mechanismNode, "rotation_open_away_fields", 0);
    summary.mechanismTimingMoveDelayFields =
        yamlScalarValue<size_t>(mechanismNode, "timing_move_delay_fields", 0);
    summary.mechanismTimingOpenWaitFields =
        yamlScalarValue<size_t>(mechanismNode, "timing_open_wait_fields", 0);
    summary.mechanismTriggerOutputs = yamlScalarValue<size_t>(mechanismNode, "trigger_outputs", 0);
    summary.mechanismUnresolvedTriggerOutputs =
        yamlScalarValue<size_t>(mechanismNode, "unresolved_trigger_outputs", 0);
    summary.scriptIncludes = yamlScalarValue<size_t>(reportSummaryNode, "script_includes", 0);
    summary.scriptLabels = yamlScalarValue<size_t>(reportSummaryNode, "script_labels", 0);
    summary.scriptIncludeReferences = yamlScalarValue<size_t>(reportSummaryNode, "script_include_references", 0);
    summary.scriptResolvedIncludes = yamlScalarValue<size_t>(reportSummaryNode, "script_resolved_includes", 0);
    summary.scriptUnresolvedIncludes = yamlScalarValue<size_t>(reportSummaryNode, "script_unresolved_includes", 0);
    summary.scriptAmbiguousIncludes = yamlScalarValue<size_t>(reportSummaryNode, "script_ambiguous_includes", 0);
    summary.scriptRegisteredTriggers = yamlScalarValue<size_t>(reportSummaryNode, "script_registered_triggers", 0);
    summary.scriptTriggerEdges = yamlScalarValue<size_t>(reportSummaryNode, "script_trigger_edges", 0);
    summary.scriptMovementCommands = yamlScalarValue<size_t>(reportSummaryNode, "script_movement_commands", 0);
    summary.scriptUnknownCommands = yamlScalarValue<size_t>(reportSummaryNode, "script_unknown_commands", 0);
    summary.scriptCommandCount = yamlScalarValue<size_t>(reportSummaryNode, "script_command_count", 0);
    summary.objectSourceTransforms = yamlScalarValue<size_t>(reportSummaryNode, "object_source_transforms", 0);
    summary.objectBoundsEvidence = yamlScalarValue<size_t>(reportSummaryNode, "object_bounds_evidence", 0);
    summary.objectTriggerVolumes = yamlScalarValue<size_t>(reportSummaryNode, "object_trigger_volumes", 0);
    summary.objectOverlayVertices = yamlScalarValue<size_t>(reportSummaryNode, "object_overlay_vertices", 0);
    summary.objectOverlayPickCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "object_overlay_pick_candidates", 0);
    summary.assetIssueMarkerSourceObjects =
        yamlScalarValue<size_t>(reportSummaryNode, "asset_issue_marker_source_objects", 0);
    summary.assetIssueMarkerCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "asset_issue_marker_candidates", 0);
    summary.assetIssueMarkerUnpositioned =
        yamlScalarValue<size_t>(reportSummaryNode, "asset_issue_marker_unpositioned", 0);
    summary.assetIssueMarkerRequiredCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "asset_issue_marker_required_candidates", 0);
    summary.assetIssueMarkerRequiredUnpositioned =
        yamlScalarValue<size_t>(reportSummaryNode, "asset_issue_marker_required_unpositioned", 0);
    summary.mechanismTargetMarkerGroups =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_target_marker_groups", 0);
    summary.mechanismTargetMarkerCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_target_marker_candidates", 0);
    summary.mechanismTargetMarkerVertices =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_target_marker_vertices", 0);
    summary.mechanismTargetMarkerSourceLinks =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_target_marker_source_links", 0);
    summary.mechanismGizmoCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_gizmo_candidates", 0);
    summary.mechanismCircleGizmoCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_circle_gizmo_candidates", 0);
    summary.mechanismTargetGizmoCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_target_gizmo_candidates", 0);
    summary.mechanismMotionPathMarkers =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_motion_path_markers", 0);
    summary.mechanismLineOfSightCheckedCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_los_checked_candidates", 0);
    summary.mechanismLineOfSightBlockedCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_los_blocked_candidates", 0);
    summary.lightObjects = yamlScalarValue<size_t>(reportSummaryNode, "light_objects", 0);
    summary.lightOverlayVertices = yamlScalarValue<size_t>(reportSummaryNode, "light_overlay_vertices", 0);
    summary.staticRenderLights = yamlScalarValue<size_t>(reportSummaryNode, "static_render_lights", 0);
    summary.lightDiagnostics = yamlScalarValue<size_t>(reportSummaryNode, "light_diagnostics", 0);
    summary.soundObjects = yamlScalarValue<size_t>(reportSummaryNode, "sound_objects", 0);
    summary.soundOverlayVertices = yamlScalarValue<size_t>(reportSummaryNode, "sound_overlay_vertices", 0);
    summary.soundReferences = yamlScalarValue<size_t>(reportSummaryNode, "sound_references", 0);
    summary.resolvedSoundReferences = yamlScalarValue<size_t>(reportSummaryNode, "resolved_sound_references", 0);
    summary.unresolvedRequiredSoundReferences =
        yamlScalarValue<size_t>(reportSummaryNode, "unresolved_required_sound_references", 0);
    summary.spawnSourceObjects = yamlScalarValue<size_t>(reportSummaryNode, "spawn_source_objects", 0);
    summary.spawnOverlayVertices = yamlScalarValue<size_t>(reportSummaryNode, "spawn_overlay_vertices", 0);
    summary.spawnNpcNumbers = yamlScalarValue<size_t>(reportSummaryNode, "spawn_npc_numbers", 0);
    summary.mechanismWorldModelTargetsWithoutMovableRole =
        yamlScalarValue<size_t>(mechanismNode, "world_model_targets_without_movable_role", 0);
    summary.mechanismWorldModelTargetsMissingModel =
        yamlScalarValue<size_t>(mechanismNode, "world_model_targets_missing_model", 0);
    summary.mechanismWorldModelTargetsMissingPolygonGroup =
        yamlScalarValue<size_t>(mechanismNode, "world_model_targets_missing_polygon_group", 0);
    summary.mechanismWorldModelTargetsMismatchedPolygonGroup =
        yamlScalarValue<size_t>(mechanismNode, "world_model_targets_mismatched_polygon_group", 0);
    summary.nativeRenderableTriangles =
        yamlScalarValue<size_t>(reportSummaryNode, "viewport_native_renderable_triangles", 0);
    summary.viewportNativeMissingMaterialTriangles =
        yamlScalarValue<size_t>(reportSummaryNode, "viewport_native_missing_material_triangles", 0);
    summary.viewportNativePlaceholderMaterialTriangles =
        yamlScalarValue<size_t>(reportSummaryNode, "viewport_native_placeholder_material_triangles", 0);
    summary.viewportNativeUnresolvedMaterialTriangles =
        yamlScalarValue<size_t>(reportSummaryNode, "viewport_native_unresolved_material_triangles", 0);
    summary.nativeFilterVisual = yamlScalarValue<size_t>(reportSummaryNode, "native_filter_visual", 0);
    summary.nativeFilterInvisible = yamlScalarValue<size_t>(reportSummaryNode, "native_filter_invisible", 0);
    summary.nativeFilterWater = yamlScalarValue<size_t>(reportSummaryNode, "native_filter_water", 0);
    summary.nativeFilterVisibleWater = yamlScalarValue<size_t>(reportSummaryNode, "native_filter_visible_water", 0);
    summary.nativeFilterWaterVolume = yamlScalarValue<size_t>(reportSummaryNode, "native_filter_water_volume", 0);
    summary.nativeFilterRail = yamlScalarValue<size_t>(reportSummaryNode, "native_filter_rail", 0);
    summary.nativeFilterHelper = yamlScalarValue<size_t>(reportSummaryNode, "native_filter_helper", 0);
    summary.nativeFilterPhysics = yamlScalarValue<size_t>(reportSummaryNode, "native_filter_physics", 0);
    summary.nativeFilterVisibility = yamlScalarValue<size_t>(reportSummaryNode, "native_filter_visibility", 0);
    summary.nativeFilterPortals = yamlScalarValue<size_t>(reportSummaryNode, "native_filter_portals", 0);
    summary.worldModelOverlayVertices =
        yamlScalarValue<size_t>(reportSummaryNode, "world_model_overlay_vertices", 0);
    summary.worldModelOverlayPickCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "world_model_overlay_pick_candidates", 0);
    summary.selectedPolygonOverlayVertices =
        yamlScalarValue<size_t>(reportSummaryNode, "selected_polygon_overlay_vertices", 0);
    summary.selectedSurfaceOverlayVertices =
        yamlScalarValue<size_t>(reportSummaryNode, "selected_surface_overlay_vertices", 0);
    summary.rawObjects = yamlScalarValue<size_t>(reportSummaryNode, "raw_objects", 0);
    summary.rawObjectSidecarIssues = yamlScalarValue<size_t>(reportSummaryNode, "raw_object_sidecar_issues", 0);
    summary.modelInstances = yamlScalarValue<size_t>(reportSummaryNode, "model_instances", 0);
    summary.modelInstancesInCameraFrame =
        yamlScalarValue<size_t>(reportSummaryNode, "model_instances_in_camera_frame", 0);
    summary.missingModelInstanceAssets =
        yamlScalarValue<size_t>(reportSummaryNode, "missing_model_instance_assets", 0);
    summary.missingDrawableModelInstanceGeometry =
        yamlScalarValue<size_t>(reportSummaryNode, "missing_drawable_model_instance_geometry", 0);
    summary.actorVariantCandidates = yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_candidates", 0);
    summary.actorVariantGameplayIdentityRows =
        yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_gameplay_identity_rows", 0);
    summary.actorVariantFootSoundFields =
        yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_foot_sound_fields", 0);
    summary.actorVariantResolvedFootSounds =
        yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_resolved_foot_sounds", 0);
    summary.actorVariantUnresolvedFootSounds =
        yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_unresolved_foot_sounds", 0);
    summary.actorVariantSourceSoundReferences =
        yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_source_sound_references", 0);
    summary.actorVariantResolvedSourceSoundReferences =
        yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_resolved_source_sound_references", 0);
    summary.actorVariantUnresolvedSourceSoundReferences =
        yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_unresolved_source_sound_references", 0);
    summary.actorVariantSourceVoiceReferences =
        yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_source_voice_references", 0);
    summary.actorVariantResolvedSourceVoiceReferences =
        yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_resolved_source_voice_references", 0);
    summary.actorVariantUnresolvedSourceVoiceReferences =
        yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_unresolved_source_voice_references", 0);
    summary.actorVariantUnresolved = yamlScalarValue<size_t>(reportSummaryNode, "actor_variant_unresolved", 0);
    summary.scriptedObjectsWithModelCollisionVolumes =
        yamlScalarValue<size_t>(reportSummaryNode, "scripted_objects_with_model_collision_volumes", 0);
    summary.scriptedObjectsRequiringBillboardCollisionVisuals =
        yamlScalarValue<size_t>(reportSummaryNode, "scripted_objects_requiring_billboard_collision_visuals", 0);
    summary.missingScriptedObjectCollisionVisuals =
        yamlScalarValue<size_t>(reportSummaryNode, "missing_scripted_object_collision_visuals", 0);
    summary.mechanismPreviewCandidates =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_preview_candidates", 0);
    summary.mechanismPreviewChangedBounds =
        yamlScalarValue<size_t>(reportSummaryNode, "mechanism_preview_changed_bounds", 0);
    summary.materialTextures = yamlScalarValue<size_t>(reportSummaryNode, "material_textures", 0);
    summary.resolvedDtx = yamlScalarValue<size_t>(reportSummaryNode, "resolved_dtx", 0);
    summary.ambiguousDtx = yamlScalarValue<size_t>(reportSummaryNode, "ambiguous_dtx", 0);
    summary.sourceDtxPaths = yamlScalarValue<size_t>(reportSummaryNode, "source_dtx_paths", 0);
    summary.defaultHelperMaterials = yamlScalarValue<size_t>(reportSummaryNode, "default_helper_materials", 0);
    summary.placeholderMissingSourceMaterials =
        yamlScalarValue<size_t>(reportSummaryNode, "placeholder_missing_source_materials", 0);
    summary.dtxHeaders = yamlScalarValue<size_t>(reportSummaryNode, "dtx_headers", 0);
    summary.dtxHeadersMatchingSidecar =
        yamlScalarValue<size_t>(reportSummaryNode, "dtx_headers_matching_sidecar", 0);
    summary.dtxUserFlagRecords = yamlScalarValue<size_t>(reportSummaryNode, "dtx_user_flag_records", 0);
    summary.dtxExtraByteRecords = yamlScalarValue<size_t>(reportSummaryNode, "dtx_extra_byte_records", 0);
    summary.dtxMipPayloads = yamlScalarValue<size_t>(reportSummaryNode, "dtx_mip_payloads", 0);
    summary.dtxDecodedPreviewMips = yamlScalarValue<size_t>(reportSummaryNode, "dtx_decoded_preview_mips", 0);
    summary.dtxSectionMetadataRecords =
        yamlScalarValue<size_t>(reportSummaryNode, "dtx_section_metadata_records", 0);
    summary.dtxSectionPayloadsAvailable =
        yamlScalarValue<size_t>(reportSummaryNode, "dtx_section_payloads_available", 0);
    summary.dtxCommandStrings = yamlScalarValue<size_t>(reportSummaryNode, "dtx_command_strings", 0);
    summary.decodedCacheDeterminismChecked =
        yamlScalarValue<size_t>(reportSummaryNode, "decoded_cache_determinism_checked", 0);
    summary.decodedCacheSourceDecoded =
        yamlScalarValue<size_t>(reportSummaryNode, "decoded_cache_source_decoded", 0);
    summary.decodedCacheImageDecoded =
        yamlScalarValue<size_t>(reportSummaryNode, "decoded_cache_image_decoded", 0);
    summary.decodedCacheMatchesSource =
        yamlScalarValue<size_t>(reportSummaryNode, "decoded_cache_matches_source", 0);
    summary.decodedCacheMismatches = yamlScalarValue<size_t>(reportSummaryNode, "decoded_cache_mismatches", 0);
    summary.spriteMaterials = yamlScalarValue<size_t>(reportSummaryNode, "sprite_materials", 0);
    summary.resolvedSpriteMaterials = yamlScalarValue<size_t>(reportSummaryNode, "resolved_sprite_materials", 0);
    summary.spriteFrameTextures = yamlScalarValue<size_t>(reportSummaryNode, "sprite_frame_textures", 0);
    summary.resolvedSpriteFrameTextures =
        yamlScalarValue<size_t>(reportSummaryNode, "resolved_sprite_frame_textures", 0);
    summary.unresolvedSpriteFrameTextures =
        yamlScalarValue<size_t>(reportSummaryNode, "unresolved_sprite_frame_textures", 0);
    summary.ambiguousSpriteFrameTextures =
        yamlScalarValue<size_t>(reportSummaryNode, "ambiguous_sprite_frame_textures", 0);
    summary.diagnosticErrors = yamlScalarValue<size_t>(diagnosticsNode, "errors", 0);
    summary.diagnosticWarnings = yamlScalarValue<size_t>(diagnosticsNode, "warnings", 0);
    summary.diagnosticInfo = yamlScalarValue<size_t>(diagnosticsNode, "info", 0);
    return true;
}

bool writeMm9ValidationSummaryReport(
    const std::filesystem::path &worldRoot,
    std::filesystem::path &summaryReportPath,
    std::string &errorMessage)
{
    const std::filesystem::path validationRoot = worldRoot / "import" / "validation";
    std::vector<Mm9ValidationReportSummary> reports;

    if (!std::filesystem::exists(validationRoot))
    {
        errorMessage = "validation report directory does not exist: " + validationRoot.generic_string();
        return false;
    }

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(validationRoot))
    {
        if (!entry.is_regular_file())
        {
            continue;
        }

        const std::string fileName = entry.path().filename().string();

        if (!fileName.ends_with(".asset_validation.yml"))
        {
            continue;
        }

        Mm9ValidationReportSummary report;

        if (!readMm9ValidationReportSummary(entry.path(), report, errorMessage))
        {
            return false;
        }

        reports.push_back(std::move(report));
    }

    std::sort(
        reports.begin(),
        reports.end(),
        [](const Mm9ValidationReportSummary &left, const Mm9ValidationReportSummary &right)
        {
            return left.mapId < right.mapId;
        });

    if (reports.empty())
    {
        errorMessage = "no per-map MM9 validation reports found in " + validationRoot.generic_string();
        return false;
    }

    size_t cleanCount = 0;
    size_t dirtyCount = 0;
    size_t levelLoadDiagnostics = 0;
    size_t sourceMutationSnapshotVerifiedReports = 0;
    size_t sourceMutationSnapshotFiles = 0;
    size_t sourceDatHashDiagnostics = 0;
    size_t sourceDatHashVerifiedReports = 0;
    size_t sourceManifestDiagnostics = 0;
    size_t sourceManifestExpectedFiles = 0;
    size_t sourceManifestActualFiles = 0;
    size_t sourceManifestCountDriftFamilies = 0;
    size_t sourceManifestMissingDirectories = 0;
    size_t documentPathsTotal = 0;
    size_t documentPathsMissing = 0;
    size_t documentPathsMissingRequired = 0;
    size_t readonlySourcePaths = 0;
    size_t generatedPaths = 0;
    size_t authoredPaths = 0;
    size_t authoredOverridePaths = 0;
    size_t compatibilityPaths = 0;
    size_t datWorldReferenceIssues = 0;
    size_t datWorldInvalidLeafReferences = 0;
    size_t datWorldInvalidSurfaceTextureRefs = 0;
    size_t datWorldInvalidPolySurfaceRefs = 0;
    size_t datWorldInvalidPolyPlaneRefs = 0;
    size_t datWorldInvalidPolyVertexRefs = 0;
    size_t datWorldInvalidNodePolyRefs = 0;
    size_t datWorldInvalidRootNodeRefs = 0;
    size_t assetGraphTotal = 0;
    size_t assetGraphResolved = 0;
    size_t assetGraphUnresolved = 0;
    size_t assetGraphAmbiguous = 0;
    size_t assetGraphStale = 0;
    size_t assetGraphRequiredTotal = 0;
    size_t assetGraphRequiredResolved = 0;
    size_t assetGraphRequiredUnresolved = 0;
    size_t assetGraphRequiredAmbiguous = 0;
    size_t assetGraphOptionalTotal = 0;
    size_t assetGraphOptionalResolved = 0;
    size_t assetGraphOptionalUnresolved = 0;
    size_t assetGraphOptionalAmbiguous = 0;
    size_t assetGraphSourceOnly = 0;
    size_t assetGraphUnusedSource = 0;
    size_t rawObjectAssetRefs = 0;
    size_t requiredRawObjectAssetRefs = 0;
    size_t optionalRawObjectAssetRefs = 0;
    size_t unresolvedRequiredRawObjectAssetRefs = 0;
    size_t unresolvedOptionalRawObjectAssetRefs = 0;
    size_t staleCaches = 0;
    size_t mechanismUnresolvedRequiredTargets = 0;
    size_t mechanismIncompleteLinearMotion = 0;
    size_t mechanismIncompleteRotationMotion = 0;
    size_t mechanismSoundSlots = 0;
    size_t mechanismAuthoredSoundReferences = 0;
    size_t mechanismEmptySoundReferences = 0;
    size_t mechanismPreviewableMechanisms = 0;
    size_t mechanismInertMechanisms = 0;
    size_t mechanismInertPreviewEntries = 0;
    size_t mechanismWithoutPreviewMotion = 0;
    size_t mechanismWithoutPreviewTarget = 0;
    size_t mechanismActivationStartOpenFields = 0;
    size_t mechanismActivationLockedFields = 0;
    size_t mechanismActivationPushOpenFields = 0;
    size_t mechanismActivationTouchToOpenFields = 0;
    size_t mechanismActivationLockOnCloseFields = 0;
    size_t mechanismActivationReopenOnContactFields = 0;
    size_t mechanismRotationOpenAwayFields = 0;
    size_t mechanismTimingMoveDelayFields = 0;
    size_t mechanismTimingOpenWaitFields = 0;
    size_t mechanismTriggerOutputs = 0;
    size_t mechanismUnresolvedTriggerOutputs = 0;
    size_t scriptIncludes = 0;
    size_t scriptLabels = 0;
    size_t scriptIncludeReferences = 0;
    size_t scriptResolvedIncludes = 0;
    size_t scriptUnresolvedIncludes = 0;
    size_t scriptAmbiguousIncludes = 0;
    size_t scriptRegisteredTriggers = 0;
    size_t scriptTriggerEdges = 0;
    size_t scriptMovementCommands = 0;
    size_t scriptUnknownCommands = 0;
    size_t scriptCommandCount = 0;
    size_t mechanismWorldModelTargetsWithoutMovableRole = 0;
    size_t mechanismWorldModelTargetsMissingModel = 0;
    size_t mechanismWorldModelTargetsMissingPolygonGroup = 0;
    size_t mechanismWorldModelTargetsMismatchedPolygonGroup = 0;
    size_t nativeRenderableTriangles = 0;
    size_t viewportNativeMissingMaterialTriangles = 0;
    size_t viewportNativePlaceholderMaterialTriangles = 0;
    size_t viewportNativeUnresolvedMaterialTriangles = 0;
    size_t nativeFilterVisual = 0;
    size_t nativeFilterInvisible = 0;
    size_t nativeFilterWater = 0;
    size_t nativeFilterVisibleWater = 0;
    size_t nativeFilterWaterVolume = 0;
    size_t nativeFilterRail = 0;
    size_t nativeFilterHelper = 0;
    size_t nativeFilterPhysics = 0;
    size_t nativeFilterVisibility = 0;
    size_t nativeFilterPortals = 0;
    size_t worldModelOverlayVertices = 0;
    size_t worldModelOverlayPickCandidates = 0;
    size_t selectedPolygonOverlayVertices = 0;
    size_t selectedSurfaceOverlayVertices = 0;
    size_t rawObjects = 0;
    size_t rawObjectSidecarIssues = 0;
    size_t objectSourceTransforms = 0;
    size_t objectBoundsEvidence = 0;
    size_t objectTriggerVolumes = 0;
    size_t objectOverlayVertices = 0;
    size_t objectOverlayPickCandidates = 0;
    size_t assetIssueMarkerSourceObjects = 0;
    size_t assetIssueMarkerCandidates = 0;
    size_t assetIssueMarkerUnpositioned = 0;
    size_t assetIssueMarkerRequiredCandidates = 0;
    size_t assetIssueMarkerRequiredUnpositioned = 0;
    size_t mechanismTargetMarkerGroups = 0;
    size_t mechanismTargetMarkerCandidates = 0;
    size_t mechanismTargetMarkerVertices = 0;
    size_t mechanismTargetMarkerSourceLinks = 0;
    size_t mechanismGizmoCandidates = 0;
    size_t mechanismCircleGizmoCandidates = 0;
    size_t mechanismTargetGizmoCandidates = 0;
    size_t mechanismMotionPathMarkers = 0;
    size_t mechanismLineOfSightCheckedCandidates = 0;
    size_t mechanismLineOfSightBlockedCandidates = 0;
    size_t lightObjects = 0;
    size_t lightOverlayVertices = 0;
    size_t staticRenderLights = 0;
    size_t lightDiagnostics = 0;
    size_t soundObjects = 0;
    size_t soundOverlayVertices = 0;
    size_t soundReferences = 0;
    size_t resolvedSoundReferences = 0;
    size_t unresolvedRequiredSoundReferences = 0;
    size_t spawnSourceObjects = 0;
    size_t spawnOverlayVertices = 0;
    size_t spawnNpcNumbers = 0;
    size_t modelInstances = 0;
    size_t modelInstancesInCameraFrame = 0;
    size_t missingModelInstanceAssets = 0;
    size_t missingDrawableModelInstanceGeometry = 0;
    size_t actorVariantCandidates = 0;
    size_t actorVariantGameplayIdentityRows = 0;
    size_t actorVariantFootSoundFields = 0;
    size_t actorVariantResolvedFootSounds = 0;
    size_t actorVariantUnresolvedFootSounds = 0;
    size_t actorVariantSourceSoundReferences = 0;
    size_t actorVariantResolvedSourceSoundReferences = 0;
    size_t actorVariantUnresolvedSourceSoundReferences = 0;
    size_t actorVariantSourceVoiceReferences = 0;
    size_t actorVariantResolvedSourceVoiceReferences = 0;
    size_t actorVariantUnresolvedSourceVoiceReferences = 0;
    size_t actorVariantUnresolved = 0;
    size_t scriptedObjectsWithModelCollisionVolumes = 0;
    size_t scriptedObjectsRequiringBillboardCollisionVisuals = 0;
    size_t missingScriptedObjectCollisionVisuals = 0;
    size_t mechanismPreviewCandidates = 0;
    size_t mechanismPreviewChangedBounds = 0;
    size_t materialTextures = 0;
    size_t resolvedDtx = 0;
    size_t ambiguousDtx = 0;
    size_t sourceDtxPaths = 0;
    size_t defaultHelperMaterials = 0;
    size_t placeholderMissingSourceMaterials = 0;
    size_t dtxHeaders = 0;
    size_t dtxHeadersMatchingSidecar = 0;
    size_t dtxUserFlagRecords = 0;
    size_t dtxExtraByteRecords = 0;
    size_t dtxMipPayloads = 0;
    size_t dtxDecodedPreviewMips = 0;
    size_t dtxSectionMetadataRecords = 0;
    size_t dtxSectionPayloadsAvailable = 0;
    size_t dtxCommandStrings = 0;
    size_t decodedCacheDeterminismChecked = 0;
    size_t decodedCacheSourceDecoded = 0;
    size_t decodedCacheImageDecoded = 0;
    size_t decodedCacheMatchesSource = 0;
    size_t decodedCacheMismatches = 0;
    size_t spriteMaterials = 0;
    size_t resolvedSpriteMaterials = 0;
    size_t spriteFrameTextures = 0;
    size_t resolvedSpriteFrameTextures = 0;
    size_t unresolvedSpriteFrameTextures = 0;
    size_t ambiguousSpriteFrameTextures = 0;
    size_t diagnosticErrors = 0;
    size_t diagnosticWarnings = 0;
    size_t diagnosticInfo = 0;

    for (const Mm9ValidationReportSummary &report : reports)
    {
        if (report.clean)
        {
            ++cleanCount;
        }
        else
        {
            ++dirtyCount;
        }

        levelLoadDiagnostics += report.levelLoadDiagnostics;
        if (report.sourceMutationSnapshotVerified)
        {
            ++sourceMutationSnapshotVerifiedReports;
        }
        sourceMutationSnapshotFiles += report.sourceMutationSnapshotFiles;
        sourceDatHashDiagnostics += report.sourceDatHashDiagnostics;
        if (report.sourceDatHashVerified)
        {
            ++sourceDatHashVerifiedReports;
        }
        sourceManifestDiagnostics += report.sourceManifestDiagnostics;
        sourceManifestExpectedFiles += report.sourceManifestExpectedFiles;
        sourceManifestActualFiles += report.sourceManifestActualFiles;
        sourceManifestCountDriftFamilies += report.sourceManifestCountDriftFamilies;
        sourceManifestMissingDirectories += report.sourceManifestMissingDirectories;
        documentPathsTotal += report.documentPathsTotal;
        documentPathsMissing += report.documentPathsMissing;
        documentPathsMissingRequired += report.documentPathsMissingRequired;
        readonlySourcePaths += report.documentPathsReadOnlySource;
        generatedPaths += report.documentPathsGenerated;
        authoredPaths += report.documentPathsAuthored;
        authoredOverridePaths += report.documentPathsAuthoredOverrides;
        compatibilityPaths += report.documentPathsCompatibilityDerived;
        datWorldReferenceIssues += report.datWorldReferenceIssues;
        datWorldInvalidLeafReferences += report.datWorldInvalidLeafReferences;
        datWorldInvalidSurfaceTextureRefs += report.datWorldInvalidSurfaceTextureRefs;
        datWorldInvalidPolySurfaceRefs += report.datWorldInvalidPolySurfaceRefs;
        datWorldInvalidPolyPlaneRefs += report.datWorldInvalidPolyPlaneRefs;
        datWorldInvalidPolyVertexRefs += report.datWorldInvalidPolyVertexRefs;
        datWorldInvalidNodePolyRefs += report.datWorldInvalidNodePolyRefs;
        datWorldInvalidRootNodeRefs += report.datWorldInvalidRootNodeRefs;
        assetGraphTotal += report.assetGraphTotal;
        assetGraphResolved += report.assetGraphResolved;
        assetGraphUnresolved += report.assetGraphUnresolved;
        assetGraphAmbiguous += report.assetGraphAmbiguous;
        assetGraphStale += report.assetGraphStale;
        assetGraphRequiredTotal += report.assetGraphRequiredTotal;
        assetGraphRequiredResolved += report.assetGraphRequiredResolved;
        assetGraphRequiredUnresolved += report.assetGraphRequiredUnresolved;
        assetGraphRequiredAmbiguous += report.assetGraphRequiredAmbiguous;
        assetGraphOptionalTotal += report.assetGraphOptionalTotal;
        assetGraphOptionalResolved += report.assetGraphOptionalResolved;
        assetGraphOptionalUnresolved += report.assetGraphOptionalUnresolved;
        assetGraphOptionalAmbiguous += report.assetGraphOptionalAmbiguous;
        assetGraphSourceOnly += report.assetGraphSourceOnly;
        assetGraphUnusedSource += report.assetGraphUnusedSource;
        rawObjectAssetRefs += report.rawObjectAssetRefs;
        requiredRawObjectAssetRefs += report.requiredRawObjectAssetRefs;
        optionalRawObjectAssetRefs += report.optionalRawObjectAssetRefs;
        unresolvedRequiredRawObjectAssetRefs += report.unresolvedRequiredRawObjectAssetRefs;
        unresolvedOptionalRawObjectAssetRefs += report.unresolvedOptionalRawObjectAssetRefs;
        staleCaches += report.staleCaches;
        mechanismUnresolvedRequiredTargets += report.mechanismUnresolvedRequiredTargets;
        mechanismIncompleteLinearMotion += report.mechanismIncompleteLinearMotion;
        mechanismIncompleteRotationMotion += report.mechanismIncompleteRotationMotion;
        mechanismSoundSlots += report.mechanismSoundSlots;
        mechanismAuthoredSoundReferences += report.mechanismAuthoredSoundReferences;
        mechanismEmptySoundReferences += report.mechanismEmptySoundReferences;
        mechanismPreviewableMechanisms += report.mechanismPreviewableMechanisms;
        mechanismInertMechanisms += report.mechanismInertMechanisms;
        mechanismInertPreviewEntries += report.mechanismInertPreviewEntries;
        mechanismWithoutPreviewMotion += report.mechanismWithoutPreviewMotion;
        mechanismWithoutPreviewTarget += report.mechanismWithoutPreviewTarget;
        mechanismActivationStartOpenFields += report.mechanismActivationStartOpenFields;
        mechanismActivationLockedFields += report.mechanismActivationLockedFields;
        mechanismActivationPushOpenFields += report.mechanismActivationPushOpenFields;
        mechanismActivationTouchToOpenFields += report.mechanismActivationTouchToOpenFields;
        mechanismActivationLockOnCloseFields += report.mechanismActivationLockOnCloseFields;
        mechanismActivationReopenOnContactFields += report.mechanismActivationReopenOnContactFields;
        mechanismRotationOpenAwayFields += report.mechanismRotationOpenAwayFields;
        mechanismTimingMoveDelayFields += report.mechanismTimingMoveDelayFields;
        mechanismTimingOpenWaitFields += report.mechanismTimingOpenWaitFields;
        mechanismTriggerOutputs += report.mechanismTriggerOutputs;
        mechanismUnresolvedTriggerOutputs += report.mechanismUnresolvedTriggerOutputs;
        scriptIncludes += report.scriptIncludes;
        scriptLabels += report.scriptLabels;
        scriptIncludeReferences += report.scriptIncludeReferences;
        scriptResolvedIncludes += report.scriptResolvedIncludes;
        scriptUnresolvedIncludes += report.scriptUnresolvedIncludes;
        scriptAmbiguousIncludes += report.scriptAmbiguousIncludes;
        scriptRegisteredTriggers += report.scriptRegisteredTriggers;
        scriptTriggerEdges += report.scriptTriggerEdges;
        scriptMovementCommands += report.scriptMovementCommands;
        scriptUnknownCommands += report.scriptUnknownCommands;
        scriptCommandCount += report.scriptCommandCount;
        mechanismWorldModelTargetsWithoutMovableRole += report.mechanismWorldModelTargetsWithoutMovableRole;
        mechanismWorldModelTargetsMissingModel += report.mechanismWorldModelTargetsMissingModel;
        mechanismWorldModelTargetsMissingPolygonGroup += report.mechanismWorldModelTargetsMissingPolygonGroup;
        mechanismWorldModelTargetsMismatchedPolygonGroup += report.mechanismWorldModelTargetsMismatchedPolygonGroup;
        nativeRenderableTriangles += report.nativeRenderableTriangles;
        viewportNativeMissingMaterialTriangles += report.viewportNativeMissingMaterialTriangles;
        viewportNativePlaceholderMaterialTriangles += report.viewportNativePlaceholderMaterialTriangles;
        viewportNativeUnresolvedMaterialTriangles += report.viewportNativeUnresolvedMaterialTriangles;
        nativeFilterVisual += report.nativeFilterVisual;
        nativeFilterInvisible += report.nativeFilterInvisible;
        nativeFilterWater += report.nativeFilterWater;
        nativeFilterVisibleWater += report.nativeFilterVisibleWater;
        nativeFilterWaterVolume += report.nativeFilterWaterVolume;
        nativeFilterRail += report.nativeFilterRail;
        nativeFilterHelper += report.nativeFilterHelper;
        nativeFilterPhysics += report.nativeFilterPhysics;
        nativeFilterVisibility += report.nativeFilterVisibility;
        nativeFilterPortals += report.nativeFilterPortals;
        worldModelOverlayVertices += report.worldModelOverlayVertices;
        worldModelOverlayPickCandidates += report.worldModelOverlayPickCandidates;
        selectedPolygonOverlayVertices += report.selectedPolygonOverlayVertices;
        selectedSurfaceOverlayVertices += report.selectedSurfaceOverlayVertices;
        rawObjects += report.rawObjects;
        rawObjectSidecarIssues += report.rawObjectSidecarIssues;
        objectSourceTransforms += report.objectSourceTransforms;
        objectBoundsEvidence += report.objectBoundsEvidence;
        objectTriggerVolumes += report.objectTriggerVolumes;
        objectOverlayVertices += report.objectOverlayVertices;
        objectOverlayPickCandidates += report.objectOverlayPickCandidates;
        assetIssueMarkerSourceObjects += report.assetIssueMarkerSourceObjects;
        assetIssueMarkerCandidates += report.assetIssueMarkerCandidates;
        assetIssueMarkerUnpositioned += report.assetIssueMarkerUnpositioned;
        assetIssueMarkerRequiredCandidates += report.assetIssueMarkerRequiredCandidates;
        assetIssueMarkerRequiredUnpositioned += report.assetIssueMarkerRequiredUnpositioned;
        mechanismTargetMarkerGroups += report.mechanismTargetMarkerGroups;
        mechanismTargetMarkerCandidates += report.mechanismTargetMarkerCandidates;
        mechanismTargetMarkerVertices += report.mechanismTargetMarkerVertices;
        mechanismTargetMarkerSourceLinks += report.mechanismTargetMarkerSourceLinks;
        mechanismGizmoCandidates += report.mechanismGizmoCandidates;
        mechanismCircleGizmoCandidates += report.mechanismCircleGizmoCandidates;
        mechanismTargetGizmoCandidates += report.mechanismTargetGizmoCandidates;
        mechanismMotionPathMarkers += report.mechanismMotionPathMarkers;
        mechanismLineOfSightCheckedCandidates += report.mechanismLineOfSightCheckedCandidates;
        mechanismLineOfSightBlockedCandidates += report.mechanismLineOfSightBlockedCandidates;
        lightObjects += report.lightObjects;
        lightOverlayVertices += report.lightOverlayVertices;
        staticRenderLights += report.staticRenderLights;
        lightDiagnostics += report.lightDiagnostics;
        soundObjects += report.soundObjects;
        soundOverlayVertices += report.soundOverlayVertices;
        soundReferences += report.soundReferences;
        resolvedSoundReferences += report.resolvedSoundReferences;
        unresolvedRequiredSoundReferences += report.unresolvedRequiredSoundReferences;
        spawnSourceObjects += report.spawnSourceObjects;
        spawnOverlayVertices += report.spawnOverlayVertices;
        spawnNpcNumbers += report.spawnNpcNumbers;
        modelInstances += report.modelInstances;
        modelInstancesInCameraFrame += report.modelInstancesInCameraFrame;
        missingModelInstanceAssets += report.missingModelInstanceAssets;
        missingDrawableModelInstanceGeometry += report.missingDrawableModelInstanceGeometry;
        actorVariantCandidates += report.actorVariantCandidates;
        actorVariantGameplayIdentityRows += report.actorVariantGameplayIdentityRows;
        actorVariantFootSoundFields += report.actorVariantFootSoundFields;
        actorVariantResolvedFootSounds += report.actorVariantResolvedFootSounds;
        actorVariantUnresolvedFootSounds += report.actorVariantUnresolvedFootSounds;
        actorVariantSourceSoundReferences += report.actorVariantSourceSoundReferences;
        actorVariantResolvedSourceSoundReferences += report.actorVariantResolvedSourceSoundReferences;
        actorVariantUnresolvedSourceSoundReferences += report.actorVariantUnresolvedSourceSoundReferences;
        actorVariantSourceVoiceReferences += report.actorVariantSourceVoiceReferences;
        actorVariantResolvedSourceVoiceReferences += report.actorVariantResolvedSourceVoiceReferences;
        actorVariantUnresolvedSourceVoiceReferences += report.actorVariantUnresolvedSourceVoiceReferences;
        actorVariantUnresolved += report.actorVariantUnresolved;
        scriptedObjectsWithModelCollisionVolumes += report.scriptedObjectsWithModelCollisionVolumes;
        scriptedObjectsRequiringBillboardCollisionVisuals +=
            report.scriptedObjectsRequiringBillboardCollisionVisuals;
        missingScriptedObjectCollisionVisuals += report.missingScriptedObjectCollisionVisuals;
        mechanismPreviewCandidates += report.mechanismPreviewCandidates;
        mechanismPreviewChangedBounds += report.mechanismPreviewChangedBounds;
        materialTextures += report.materialTextures;
        resolvedDtx += report.resolvedDtx;
        ambiguousDtx += report.ambiguousDtx;
        sourceDtxPaths += report.sourceDtxPaths;
        defaultHelperMaterials += report.defaultHelperMaterials;
        placeholderMissingSourceMaterials += report.placeholderMissingSourceMaterials;
        dtxHeaders += report.dtxHeaders;
        dtxHeadersMatchingSidecar += report.dtxHeadersMatchingSidecar;
        dtxUserFlagRecords += report.dtxUserFlagRecords;
        dtxExtraByteRecords += report.dtxExtraByteRecords;
        dtxMipPayloads += report.dtxMipPayloads;
        dtxDecodedPreviewMips += report.dtxDecodedPreviewMips;
        dtxSectionMetadataRecords += report.dtxSectionMetadataRecords;
        dtxSectionPayloadsAvailable += report.dtxSectionPayloadsAvailable;
        dtxCommandStrings += report.dtxCommandStrings;
        decodedCacheDeterminismChecked += report.decodedCacheDeterminismChecked;
        decodedCacheSourceDecoded += report.decodedCacheSourceDecoded;
        decodedCacheImageDecoded += report.decodedCacheImageDecoded;
        decodedCacheMatchesSource += report.decodedCacheMatchesSource;
        decodedCacheMismatches += report.decodedCacheMismatches;
        spriteMaterials += report.spriteMaterials;
        resolvedSpriteMaterials += report.resolvedSpriteMaterials;
        spriteFrameTextures += report.spriteFrameTextures;
        resolvedSpriteFrameTextures += report.resolvedSpriteFrameTextures;
        unresolvedSpriteFrameTextures += report.unresolvedSpriteFrameTextures;
        ambiguousSpriteFrameTextures += report.ambiguousSpriteFrameTextures;
        diagnosticErrors += report.diagnosticErrors;
        diagnosticWarnings += report.diagnosticWarnings;
        diagnosticInfo += report.diagnosticInfo;
    }

    summaryReportPath = validationRoot / "active_slice.validation_summary.yml";
    std::ofstream stream(summaryReportPath);

    if (!stream)
    {
        errorMessage = "could not write validation summary report " + summaryReportPath.generic_string();
        return false;
    }

    writeYamlScalar(stream, "", "format_version", static_cast<size_t>(1));
    writeYamlScalar(stream, "", "kind", "mm9_asset_validation_summary");
    writeYamlScalar(stream, "", "scope", "active_two_map_slice");
    writeYamlScalar(stream, "", "report_count", reports.size());
    writeYamlScalar(stream, "", "clean", dirtyCount == 0);
    writeYamlScalar(stream, "", "clean_reports", cleanCount);
    writeYamlScalar(stream, "", "dirty_reports", dirtyCount);
    writeYamlScalar(stream, "", "level_load_diagnostics", levelLoadDiagnostics);
    writeYamlScalar(
        stream,
        "",
        "source_mutation_snapshot_verified_reports",
        sourceMutationSnapshotVerifiedReports);
    writeYamlScalar(stream, "", "source_mutation_snapshot_files", sourceMutationSnapshotFiles);
    writeYamlScalar(stream, "", "source_dat_hash_diagnostics", sourceDatHashDiagnostics);
    writeYamlScalar(stream, "", "source_dat_hash_verified_reports", sourceDatHashVerifiedReports);
    writeYamlScalar(stream, "", "source_manifest_diagnostics", sourceManifestDiagnostics);
    writeYamlScalar(stream, "", "source_manifest_expected_files", sourceManifestExpectedFiles);
    writeYamlScalar(stream, "", "source_manifest_actual_files", sourceManifestActualFiles);
    writeYamlScalar(stream, "", "source_manifest_count_drift_families", sourceManifestCountDriftFamilies);
    writeYamlScalar(stream, "", "source_manifest_missing_directories", sourceManifestMissingDirectories);
    writeYamlScalar(stream, "", "document_paths_total", documentPathsTotal);
    writeYamlScalar(stream, "", "document_paths_missing", documentPathsMissing);
    writeYamlScalar(stream, "", "document_paths_missing_required", documentPathsMissingRequired);
    writeYamlScalar(stream, "", "readonly_source_paths", readonlySourcePaths);
    writeYamlScalar(stream, "", "generated_paths", generatedPaths);
    writeYamlScalar(stream, "", "authored_paths", authoredPaths);
    writeYamlScalar(stream, "", "authored_override_paths", authoredOverridePaths);
    writeYamlScalar(stream, "", "compatibility_paths", compatibilityPaths);
    writeYamlScalar(stream, "", "dat_world_reference_issues", datWorldReferenceIssues);
    writeYamlScalar(stream, "", "dat_world_invalid_leaf_references", datWorldInvalidLeafReferences);
    writeYamlScalar(stream, "", "dat_world_invalid_surface_texture_refs", datWorldInvalidSurfaceTextureRefs);
    writeYamlScalar(stream, "", "dat_world_invalid_poly_surface_refs", datWorldInvalidPolySurfaceRefs);
    writeYamlScalar(stream, "", "dat_world_invalid_poly_plane_refs", datWorldInvalidPolyPlaneRefs);
    writeYamlScalar(stream, "", "dat_world_invalid_poly_vertex_refs", datWorldInvalidPolyVertexRefs);
    writeYamlScalar(stream, "", "dat_world_invalid_node_poly_refs", datWorldInvalidNodePolyRefs);
    writeYamlScalar(stream, "", "dat_world_invalid_root_node_refs", datWorldInvalidRootNodeRefs);
    writeYamlScalar(stream, "", "asset_graph_total", assetGraphTotal);
    writeYamlScalar(stream, "", "asset_graph_resolved", assetGraphResolved);
    writeYamlScalar(stream, "", "asset_graph_unresolved", assetGraphUnresolved);
    writeYamlScalar(stream, "", "asset_graph_ambiguous", assetGraphAmbiguous);
    writeYamlScalar(stream, "", "asset_graph_stale", assetGraphStale);
    writeYamlScalar(stream, "", "asset_graph_required_total", assetGraphRequiredTotal);
    writeYamlScalar(stream, "", "asset_graph_required_resolved", assetGraphRequiredResolved);
    writeYamlScalar(stream, "", "asset_graph_required_unresolved", assetGraphRequiredUnresolved);
    writeYamlScalar(stream, "", "asset_graph_required_ambiguous", assetGraphRequiredAmbiguous);
    writeYamlScalar(stream, "", "asset_graph_optional_total", assetGraphOptionalTotal);
    writeYamlScalar(stream, "", "asset_graph_optional_resolved", assetGraphOptionalResolved);
    writeYamlScalar(stream, "", "asset_graph_optional_unresolved", assetGraphOptionalUnresolved);
    writeYamlScalar(stream, "", "asset_graph_optional_ambiguous", assetGraphOptionalAmbiguous);
    writeYamlScalar(stream, "", "asset_graph_source_only", assetGraphSourceOnly);
    writeYamlScalar(stream, "", "asset_graph_unused_source", assetGraphUnusedSource);
    writeYamlScalar(stream, "", "raw_object_asset_refs", rawObjectAssetRefs);
    writeYamlScalar(stream, "", "required_raw_object_asset_refs", requiredRawObjectAssetRefs);
    writeYamlScalar(stream, "", "optional_raw_object_asset_refs", optionalRawObjectAssetRefs);
    writeYamlScalar(stream, "", "unresolved_required_raw_object_asset_refs", unresolvedRequiredRawObjectAssetRefs);
    writeYamlScalar(stream, "", "unresolved_optional_raw_object_asset_refs", unresolvedOptionalRawObjectAssetRefs);
    writeYamlScalar(stream, "", "stale_caches", staleCaches);
    writeYamlScalar(stream, "", "mechanism_unresolved_required_targets", mechanismUnresolvedRequiredTargets);
    writeYamlScalar(stream, "", "mechanism_incomplete_linear_motion", mechanismIncompleteLinearMotion);
    writeYamlScalar(stream, "", "mechanism_incomplete_rotation_motion", mechanismIncompleteRotationMotion);
    writeYamlScalar(stream, "", "mechanism_sound_slots", mechanismSoundSlots);
    writeYamlScalar(stream, "", "mechanism_authored_sound_references", mechanismAuthoredSoundReferences);
    writeYamlScalar(stream, "", "mechanism_empty_sound_references", mechanismEmptySoundReferences);
    writeYamlScalar(stream, "", "mechanism_previewable_mechanisms", mechanismPreviewableMechanisms);
    writeYamlScalar(stream, "", "mechanism_inert_mechanisms", mechanismInertMechanisms);
    writeYamlScalar(stream, "", "mechanism_inert_preview_entries", mechanismInertPreviewEntries);
    writeYamlScalar(stream, "", "mechanism_without_preview_motion", mechanismWithoutPreviewMotion);
    writeYamlScalar(stream, "", "mechanism_without_preview_target", mechanismWithoutPreviewTarget);
    writeYamlScalar(stream, "", "mechanism_activation_start_open_fields", mechanismActivationStartOpenFields);
    writeYamlScalar(stream, "", "mechanism_activation_locked_fields", mechanismActivationLockedFields);
    writeYamlScalar(stream, "", "mechanism_activation_push_open_fields", mechanismActivationPushOpenFields);
    writeYamlScalar(stream, "", "mechanism_activation_touch_to_open_fields", mechanismActivationTouchToOpenFields);
    writeYamlScalar(stream, "", "mechanism_activation_lock_on_close_fields", mechanismActivationLockOnCloseFields);
    writeYamlScalar(
        stream,
        "",
        "mechanism_activation_reopen_on_contact_fields",
        mechanismActivationReopenOnContactFields);
    writeYamlScalar(stream, "", "mechanism_rotation_open_away_fields", mechanismRotationOpenAwayFields);
    writeYamlScalar(stream, "", "mechanism_timing_move_delay_fields", mechanismTimingMoveDelayFields);
    writeYamlScalar(stream, "", "mechanism_timing_open_wait_fields", mechanismTimingOpenWaitFields);
    writeYamlScalar(stream, "", "mechanism_trigger_outputs", mechanismTriggerOutputs);
    writeYamlScalar(stream, "", "mechanism_unresolved_trigger_outputs", mechanismUnresolvedTriggerOutputs);
    writeYamlScalar(stream, "", "script_includes", scriptIncludes);
    writeYamlScalar(stream, "", "script_labels", scriptLabels);
    writeYamlScalar(stream, "", "script_include_references", scriptIncludeReferences);
    writeYamlScalar(stream, "", "script_resolved_includes", scriptResolvedIncludes);
    writeYamlScalar(stream, "", "script_unresolved_includes", scriptUnresolvedIncludes);
    writeYamlScalar(stream, "", "script_ambiguous_includes", scriptAmbiguousIncludes);
    writeYamlScalar(stream, "", "script_registered_triggers", scriptRegisteredTriggers);
    writeYamlScalar(stream, "", "script_trigger_edges", scriptTriggerEdges);
    writeYamlScalar(stream, "", "script_movement_commands", scriptMovementCommands);
    writeYamlScalar(stream, "", "script_unknown_commands", scriptUnknownCommands);
    writeYamlScalar(stream, "", "script_command_count", scriptCommandCount);
    writeYamlScalar(
        stream,
        "",
        "mechanism_world_model_targets_without_movable_role",
        mechanismWorldModelTargetsWithoutMovableRole);
    writeYamlScalar(
        stream,
        "",
        "mechanism_world_model_targets_missing_model",
        mechanismWorldModelTargetsMissingModel);
    writeYamlScalar(
        stream,
        "",
        "mechanism_world_model_targets_missing_polygon_group",
        mechanismWorldModelTargetsMissingPolygonGroup);
    writeYamlScalar(
        stream,
        "",
        "mechanism_world_model_targets_mismatched_polygon_group",
        mechanismWorldModelTargetsMismatchedPolygonGroup);
    writeYamlScalar(stream, "", "native_renderable_triangles", nativeRenderableTriangles);
    writeYamlScalar(
        stream,
        "",
        "viewport_native_missing_material_triangles",
        viewportNativeMissingMaterialTriangles);
    writeYamlScalar(
        stream,
        "",
        "viewport_native_placeholder_material_triangles",
        viewportNativePlaceholderMaterialTriangles);
    writeYamlScalar(
        stream,
        "",
        "viewport_native_unresolved_material_triangles",
        viewportNativeUnresolvedMaterialTriangles);
    writeYamlScalar(stream, "", "native_filter_visual", nativeFilterVisual);
    writeYamlScalar(stream, "", "native_filter_invisible", nativeFilterInvisible);
    writeYamlScalar(stream, "", "native_filter_water", nativeFilterWater);
    writeYamlScalar(stream, "", "native_filter_visible_water", nativeFilterVisibleWater);
    writeYamlScalar(stream, "", "native_filter_water_volume", nativeFilterWaterVolume);
    writeYamlScalar(stream, "", "native_filter_rail", nativeFilterRail);
    writeYamlScalar(stream, "", "native_filter_helper", nativeFilterHelper);
    writeYamlScalar(stream, "", "native_filter_physics", nativeFilterPhysics);
    writeYamlScalar(stream, "", "native_filter_visibility", nativeFilterVisibility);
    writeYamlScalar(stream, "", "native_filter_portals", nativeFilterPortals);
    writeYamlScalar(stream, "", "world_model_overlay_vertices", worldModelOverlayVertices);
    writeYamlScalar(stream, "", "world_model_overlay_pick_candidates", worldModelOverlayPickCandidates);
    writeYamlScalar(stream, "", "selected_polygon_overlay_vertices", selectedPolygonOverlayVertices);
    writeYamlScalar(stream, "", "selected_surface_overlay_vertices", selectedSurfaceOverlayVertices);
    writeYamlScalar(stream, "", "raw_objects", rawObjects);
    writeYamlScalar(stream, "", "raw_object_sidecar_issues", rawObjectSidecarIssues);
    writeYamlScalar(stream, "", "object_source_transforms", objectSourceTransforms);
    writeYamlScalar(stream, "", "object_bounds_evidence", objectBoundsEvidence);
    writeYamlScalar(stream, "", "object_trigger_volumes", objectTriggerVolumes);
    writeYamlScalar(stream, "", "object_overlay_vertices", objectOverlayVertices);
    writeYamlScalar(stream, "", "object_overlay_pick_candidates", objectOverlayPickCandidates);
    writeYamlScalar(stream, "", "asset_issue_marker_source_objects", assetIssueMarkerSourceObjects);
    writeYamlScalar(stream, "", "asset_issue_marker_candidates", assetIssueMarkerCandidates);
    writeYamlScalar(stream, "", "asset_issue_marker_unpositioned", assetIssueMarkerUnpositioned);
    writeYamlScalar(stream, "", "asset_issue_marker_required_candidates", assetIssueMarkerRequiredCandidates);
    writeYamlScalar(
        stream,
        "",
        "asset_issue_marker_required_unpositioned",
        assetIssueMarkerRequiredUnpositioned);
    writeYamlScalar(stream, "", "mechanism_target_marker_groups", mechanismTargetMarkerGroups);
    writeYamlScalar(stream, "", "mechanism_target_marker_candidates", mechanismTargetMarkerCandidates);
    writeYamlScalar(stream, "", "mechanism_target_marker_vertices", mechanismTargetMarkerVertices);
    writeYamlScalar(stream, "", "mechanism_target_marker_source_links", mechanismTargetMarkerSourceLinks);
    writeYamlScalar(stream, "", "mechanism_gizmo_candidates", mechanismGizmoCandidates);
    writeYamlScalar(stream, "", "mechanism_circle_gizmo_candidates", mechanismCircleGizmoCandidates);
    writeYamlScalar(stream, "", "mechanism_target_gizmo_candidates", mechanismTargetGizmoCandidates);
    writeYamlScalar(stream, "", "mechanism_motion_path_markers", mechanismMotionPathMarkers);
    writeYamlScalar(stream, "", "mechanism_los_checked_candidates", mechanismLineOfSightCheckedCandidates);
    writeYamlScalar(stream, "", "mechanism_los_blocked_candidates", mechanismLineOfSightBlockedCandidates);
    writeYamlScalar(stream, "", "light_objects", lightObjects);
    writeYamlScalar(stream, "", "light_overlay_vertices", lightOverlayVertices);
    writeYamlScalar(stream, "", "static_render_lights", staticRenderLights);
    writeYamlScalar(stream, "", "light_diagnostics", lightDiagnostics);
    writeYamlScalar(stream, "", "sound_objects", soundObjects);
    writeYamlScalar(stream, "", "sound_overlay_vertices", soundOverlayVertices);
    writeYamlScalar(stream, "", "sound_references", soundReferences);
    writeYamlScalar(stream, "", "resolved_sound_references", resolvedSoundReferences);
    writeYamlScalar(stream, "", "unresolved_required_sound_references", unresolvedRequiredSoundReferences);
    writeYamlScalar(stream, "", "spawn_source_objects", spawnSourceObjects);
    writeYamlScalar(stream, "", "spawn_overlay_vertices", spawnOverlayVertices);
    writeYamlScalar(stream, "", "spawn_npc_numbers", spawnNpcNumbers);
    writeYamlScalar(stream, "", "model_instances", modelInstances);
    writeYamlScalar(stream, "", "model_instances_in_camera_frame", modelInstancesInCameraFrame);
    writeYamlScalar(stream, "", "missing_model_instance_assets", missingModelInstanceAssets);
    writeYamlScalar(stream, "", "missing_drawable_model_instance_geometry", missingDrawableModelInstanceGeometry);
    writeYamlScalar(stream, "", "actor_variant_candidates", actorVariantCandidates);
    writeYamlScalar(stream, "", "actor_variant_gameplay_identity_rows", actorVariantGameplayIdentityRows);
    writeYamlScalar(stream, "", "actor_variant_foot_sound_fields", actorVariantFootSoundFields);
    writeYamlScalar(stream, "", "actor_variant_resolved_foot_sounds", actorVariantResolvedFootSounds);
    writeYamlScalar(stream, "", "actor_variant_unresolved_foot_sounds", actorVariantUnresolvedFootSounds);
    writeYamlScalar(stream, "", "actor_variant_source_sound_references", actorVariantSourceSoundReferences);
    writeYamlScalar(
        stream,
        "",
        "actor_variant_resolved_source_sound_references",
        actorVariantResolvedSourceSoundReferences);
    writeYamlScalar(
        stream,
        "",
        "actor_variant_unresolved_source_sound_references",
        actorVariantUnresolvedSourceSoundReferences);
    writeYamlScalar(stream, "", "actor_variant_source_voice_references", actorVariantSourceVoiceReferences);
    writeYamlScalar(
        stream,
        "",
        "actor_variant_resolved_source_voice_references",
        actorVariantResolvedSourceVoiceReferences);
    writeYamlScalar(
        stream,
        "",
        "actor_variant_unresolved_source_voice_references",
        actorVariantUnresolvedSourceVoiceReferences);
    writeYamlScalar(stream, "", "actor_variant_unresolved", actorVariantUnresolved);
    writeYamlScalar(
        stream,
        "",
        "scripted_objects_with_model_collision_volumes",
        scriptedObjectsWithModelCollisionVolumes);
    writeYamlScalar(
        stream,
        "",
        "scripted_objects_requiring_billboard_collision_visuals",
        scriptedObjectsRequiringBillboardCollisionVisuals);
    writeYamlScalar(stream, "", "missing_scripted_object_collision_visuals", missingScriptedObjectCollisionVisuals);
    writeYamlScalar(stream, "", "mechanism_preview_candidates", mechanismPreviewCandidates);
    writeYamlScalar(stream, "", "mechanism_preview_changed_bounds", mechanismPreviewChangedBounds);
    writeYamlScalar(stream, "", "material_textures", materialTextures);
    writeYamlScalar(stream, "", "resolved_dtx", resolvedDtx);
    writeYamlScalar(stream, "", "ambiguous_dtx", ambiguousDtx);
    writeYamlScalar(stream, "", "source_dtx_paths", sourceDtxPaths);
    writeYamlScalar(stream, "", "default_helper_materials", defaultHelperMaterials);
    writeYamlScalar(stream, "", "placeholder_missing_source_materials", placeholderMissingSourceMaterials);
    writeYamlScalar(stream, "", "dtx_headers", dtxHeaders);
    writeYamlScalar(stream, "", "dtx_headers_matching_sidecar", dtxHeadersMatchingSidecar);
    writeYamlScalar(stream, "", "dtx_user_flag_records", dtxUserFlagRecords);
    writeYamlScalar(stream, "", "dtx_extra_byte_records", dtxExtraByteRecords);
    writeYamlScalar(stream, "", "dtx_mip_payloads", dtxMipPayloads);
    writeYamlScalar(stream, "", "dtx_decoded_preview_mips", dtxDecodedPreviewMips);
    writeYamlScalar(stream, "", "dtx_section_metadata_records", dtxSectionMetadataRecords);
    writeYamlScalar(stream, "", "dtx_section_payloads_available", dtxSectionPayloadsAvailable);
    writeYamlScalar(stream, "", "dtx_command_strings", dtxCommandStrings);
    writeYamlScalar(stream, "", "decoded_cache_determinism_checked", decodedCacheDeterminismChecked);
    writeYamlScalar(stream, "", "decoded_cache_source_decoded", decodedCacheSourceDecoded);
    writeYamlScalar(stream, "", "decoded_cache_image_decoded", decodedCacheImageDecoded);
    writeYamlScalar(stream, "", "decoded_cache_matches_source", decodedCacheMatchesSource);
    writeYamlScalar(stream, "", "decoded_cache_mismatches", decodedCacheMismatches);
    writeYamlScalar(stream, "", "sprite_materials", spriteMaterials);
    writeYamlScalar(stream, "", "resolved_sprite_materials", resolvedSpriteMaterials);
    writeYamlScalar(stream, "", "sprite_frame_textures", spriteFrameTextures);
    writeYamlScalar(stream, "", "resolved_sprite_frame_textures", resolvedSpriteFrameTextures);
    writeYamlScalar(stream, "", "unresolved_sprite_frame_textures", unresolvedSpriteFrameTextures);
    writeYamlScalar(stream, "", "ambiguous_sprite_frame_textures", ambiguousSpriteFrameTextures);
    writeYamlScalar(stream, "", "diagnostic_errors", diagnosticErrors);
    writeYamlScalar(stream, "", "diagnostic_warnings", diagnosticWarnings);
    writeYamlScalar(stream, "", "diagnostic_info", diagnosticInfo);

    stream << "reports:\n";

    for (const Mm9ValidationReportSummary &report : reports)
    {
        stream << "  - map_id: ";
        writeYamlQuoted(stream, report.mapId);
        stream << '\n';
        writeYamlScalar(stream, "    ", "display_name", report.displayName);
        writeYamlScalar(stream, "    ", "level_file", report.levelFile);
        writeYamlScalar(stream, "    ", "report_file", report.path.filename().generic_string());
        writeYamlScalar(stream, "    ", "clean", report.clean);
        writeYamlScalar(stream, "    ", "level_load_diagnostics", report.levelLoadDiagnostics);
        writeYamlScalar(
            stream,
            "    ",
            "source_mutation_snapshot_verified",
            report.sourceMutationSnapshotVerified);
        writeYamlScalar(
            stream,
            "    ",
            "source_mutation_snapshot_files",
            report.sourceMutationSnapshotFiles);
        writeYamlScalar(stream, "    ", "source_dat_hash_diagnostics", report.sourceDatHashDiagnostics);
        writeYamlScalar(stream, "    ", "source_dat_hash_verified", report.sourceDatHashVerified);
        writeYamlScalar(stream, "    ", "source_manifest_diagnostics", report.sourceManifestDiagnostics);
        writeYamlScalar(stream, "    ", "source_manifest_expected_files", report.sourceManifestExpectedFiles);
        writeYamlScalar(stream, "    ", "source_manifest_actual_files", report.sourceManifestActualFiles);
        writeYamlScalar(
            stream,
            "    ",
            "source_manifest_count_drift_families",
            report.sourceManifestCountDriftFamilies);
        writeYamlScalar(
            stream,
            "    ",
            "source_manifest_missing_directories",
            report.sourceManifestMissingDirectories);
        writeYamlScalar(stream, "    ", "document_paths_total", report.documentPathsTotal);
        writeYamlScalar(stream, "    ", "document_paths_missing", report.documentPathsMissing);
        writeYamlScalar(stream, "    ", "document_paths_missing_required", report.documentPathsMissingRequired);
        writeYamlScalar(stream, "    ", "readonly_source_paths", report.documentPathsReadOnlySource);
        writeYamlScalar(stream, "    ", "generated_paths", report.documentPathsGenerated);
        writeYamlScalar(stream, "    ", "authored_paths", report.documentPathsAuthored);
        writeYamlScalar(stream, "    ", "authored_override_paths", report.documentPathsAuthoredOverrides);
        writeYamlScalar(stream, "    ", "compatibility_paths", report.documentPathsCompatibilityDerived);
        writeYamlScalar(stream, "    ", "dat_world_reference_issues", report.datWorldReferenceIssues);
        writeYamlScalar(stream, "    ", "dat_world_invalid_leaf_references", report.datWorldInvalidLeafReferences);
        writeYamlScalar(
            stream,
            "    ",
            "dat_world_invalid_surface_texture_refs",
            report.datWorldInvalidSurfaceTextureRefs);
        writeYamlScalar(stream, "    ", "dat_world_invalid_poly_surface_refs", report.datWorldInvalidPolySurfaceRefs);
        writeYamlScalar(stream, "    ", "dat_world_invalid_poly_plane_refs", report.datWorldInvalidPolyPlaneRefs);
        writeYamlScalar(stream, "    ", "dat_world_invalid_poly_vertex_refs", report.datWorldInvalidPolyVertexRefs);
        writeYamlScalar(stream, "    ", "dat_world_invalid_node_poly_refs", report.datWorldInvalidNodePolyRefs);
        writeYamlScalar(stream, "    ", "dat_world_invalid_root_node_refs", report.datWorldInvalidRootNodeRefs);
        writeYamlScalar(stream, "    ", "asset_graph_total", report.assetGraphTotal);
        writeYamlScalar(stream, "    ", "asset_graph_resolved", report.assetGraphResolved);
        writeYamlScalar(stream, "    ", "asset_graph_unresolved", report.assetGraphUnresolved);
        writeYamlScalar(stream, "    ", "asset_graph_ambiguous", report.assetGraphAmbiguous);
        writeYamlScalar(stream, "    ", "asset_graph_stale", report.assetGraphStale);
        writeYamlScalar(stream, "    ", "asset_graph_required_total", report.assetGraphRequiredTotal);
        writeYamlScalar(stream, "    ", "asset_graph_required_resolved", report.assetGraphRequiredResolved);
        writeYamlScalar(stream, "    ", "asset_graph_required_unresolved", report.assetGraphRequiredUnresolved);
        writeYamlScalar(stream, "    ", "asset_graph_required_ambiguous", report.assetGraphRequiredAmbiguous);
        writeYamlScalar(stream, "    ", "asset_graph_optional_total", report.assetGraphOptionalTotal);
        writeYamlScalar(stream, "    ", "asset_graph_optional_resolved", report.assetGraphOptionalResolved);
        writeYamlScalar(stream, "    ", "asset_graph_optional_unresolved", report.assetGraphOptionalUnresolved);
        writeYamlScalar(stream, "    ", "asset_graph_optional_ambiguous", report.assetGraphOptionalAmbiguous);
        writeYamlScalar(stream, "    ", "asset_graph_source_only", report.assetGraphSourceOnly);
        writeYamlScalar(stream, "    ", "asset_graph_unused_source", report.assetGraphUnusedSource);
        writeYamlScalar(stream, "    ", "raw_object_asset_refs", report.rawObjectAssetRefs);
        writeYamlScalar(stream, "    ", "required_raw_object_asset_refs", report.requiredRawObjectAssetRefs);
        writeYamlScalar(stream, "    ", "optional_raw_object_asset_refs", report.optionalRawObjectAssetRefs);
        writeYamlScalar(
            stream,
            "    ",
            "unresolved_required_raw_object_asset_refs",
            report.unresolvedRequiredRawObjectAssetRefs);
        writeYamlScalar(
            stream,
            "    ",
            "unresolved_optional_raw_object_asset_refs",
            report.unresolvedOptionalRawObjectAssetRefs);
        writeYamlScalar(stream, "    ", "stale_caches", report.staleCaches);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_unresolved_required_targets",
            report.mechanismUnresolvedRequiredTargets);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_incomplete_linear_motion",
            report.mechanismIncompleteLinearMotion);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_incomplete_rotation_motion",
            report.mechanismIncompleteRotationMotion);
        writeYamlScalar(stream, "    ", "mechanism_sound_slots", report.mechanismSoundSlots);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_authored_sound_references",
            report.mechanismAuthoredSoundReferences);
        writeYamlScalar(stream, "    ", "mechanism_empty_sound_references", report.mechanismEmptySoundReferences);
        writeYamlScalar(stream, "    ", "mechanism_previewable_mechanisms", report.mechanismPreviewableMechanisms);
        writeYamlScalar(stream, "    ", "mechanism_inert_mechanisms", report.mechanismInertMechanisms);
        writeYamlScalar(stream, "    ", "mechanism_inert_preview_entries", report.mechanismInertPreviewEntries);
        writeYamlScalar(stream, "    ", "mechanism_without_preview_motion", report.mechanismWithoutPreviewMotion);
        writeYamlScalar(stream, "    ", "mechanism_without_preview_target", report.mechanismWithoutPreviewTarget);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_activation_start_open_fields",
            report.mechanismActivationStartOpenFields);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_activation_locked_fields",
            report.mechanismActivationLockedFields);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_activation_push_open_fields",
            report.mechanismActivationPushOpenFields);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_activation_touch_to_open_fields",
            report.mechanismActivationTouchToOpenFields);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_activation_lock_on_close_fields",
            report.mechanismActivationLockOnCloseFields);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_activation_reopen_on_contact_fields",
            report.mechanismActivationReopenOnContactFields);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_rotation_open_away_fields",
            report.mechanismRotationOpenAwayFields);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_timing_move_delay_fields",
            report.mechanismTimingMoveDelayFields);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_timing_open_wait_fields",
            report.mechanismTimingOpenWaitFields);
        writeYamlScalar(stream, "    ", "mechanism_trigger_outputs", report.mechanismTriggerOutputs);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_unresolved_trigger_outputs",
            report.mechanismUnresolvedTriggerOutputs);
        writeYamlScalar(stream, "    ", "script_includes", report.scriptIncludes);
        writeYamlScalar(stream, "    ", "script_labels", report.scriptLabels);
        writeYamlScalar(stream, "    ", "script_include_references", report.scriptIncludeReferences);
        writeYamlScalar(stream, "    ", "script_resolved_includes", report.scriptResolvedIncludes);
        writeYamlScalar(stream, "    ", "script_unresolved_includes", report.scriptUnresolvedIncludes);
        writeYamlScalar(stream, "    ", "script_ambiguous_includes", report.scriptAmbiguousIncludes);
        writeYamlScalar(stream, "    ", "script_registered_triggers", report.scriptRegisteredTriggers);
        writeYamlScalar(stream, "    ", "script_trigger_edges", report.scriptTriggerEdges);
        writeYamlScalar(stream, "    ", "script_movement_commands", report.scriptMovementCommands);
        writeYamlScalar(stream, "    ", "script_unknown_commands", report.scriptUnknownCommands);
        writeYamlScalar(stream, "    ", "script_command_count", report.scriptCommandCount);
        writeYamlScalar(stream, "    ", "native_renderable_triangles", report.nativeRenderableTriangles);
        writeYamlScalar(
            stream,
            "    ",
            "viewport_native_missing_material_triangles",
            report.viewportNativeMissingMaterialTriangles);
        writeYamlScalar(
            stream,
            "    ",
            "viewport_native_placeholder_material_triangles",
            report.viewportNativePlaceholderMaterialTriangles);
        writeYamlScalar(
            stream,
            "    ",
            "viewport_native_unresolved_material_triangles",
            report.viewportNativeUnresolvedMaterialTriangles);
        writeYamlScalar(stream, "    ", "native_filter_visual", report.nativeFilterVisual);
        writeYamlScalar(stream, "    ", "native_filter_invisible", report.nativeFilterInvisible);
        writeYamlScalar(stream, "    ", "native_filter_water", report.nativeFilterWater);
        writeYamlScalar(stream, "    ", "native_filter_visible_water", report.nativeFilterVisibleWater);
        writeYamlScalar(stream, "    ", "native_filter_water_volume", report.nativeFilterWaterVolume);
        writeYamlScalar(stream, "    ", "native_filter_rail", report.nativeFilterRail);
        writeYamlScalar(stream, "    ", "native_filter_helper", report.nativeFilterHelper);
        writeYamlScalar(stream, "    ", "native_filter_physics", report.nativeFilterPhysics);
        writeYamlScalar(stream, "    ", "native_filter_visibility", report.nativeFilterVisibility);
        writeYamlScalar(stream, "    ", "native_filter_portals", report.nativeFilterPortals);
        writeYamlScalar(stream, "    ", "world_model_overlay_vertices", report.worldModelOverlayVertices);
        writeYamlScalar(
            stream,
            "    ",
            "world_model_overlay_pick_candidates",
            report.worldModelOverlayPickCandidates);
        writeYamlScalar(stream, "    ", "selected_polygon_overlay_vertices", report.selectedPolygonOverlayVertices);
        writeYamlScalar(stream, "    ", "selected_surface_overlay_vertices", report.selectedSurfaceOverlayVertices);
        writeYamlScalar(stream, "    ", "raw_objects", report.rawObjects);
        writeYamlScalar(stream, "    ", "raw_object_sidecar_issues", report.rawObjectSidecarIssues);
        writeYamlScalar(stream, "    ", "object_source_transforms", report.objectSourceTransforms);
        writeYamlScalar(stream, "    ", "object_bounds_evidence", report.objectBoundsEvidence);
        writeYamlScalar(stream, "    ", "object_trigger_volumes", report.objectTriggerVolumes);
        writeYamlScalar(stream, "    ", "object_overlay_vertices", report.objectOverlayVertices);
        writeYamlScalar(stream, "    ", "object_overlay_pick_candidates", report.objectOverlayPickCandidates);
        writeYamlScalar(stream, "    ", "asset_issue_marker_source_objects", report.assetIssueMarkerSourceObjects);
        writeYamlScalar(stream, "    ", "asset_issue_marker_candidates", report.assetIssueMarkerCandidates);
        writeYamlScalar(stream, "    ", "asset_issue_marker_unpositioned", report.assetIssueMarkerUnpositioned);
        writeYamlScalar(
            stream,
            "    ",
            "asset_issue_marker_required_candidates",
            report.assetIssueMarkerRequiredCandidates);
        writeYamlScalar(
            stream,
            "    ",
            "asset_issue_marker_required_unpositioned",
            report.assetIssueMarkerRequiredUnpositioned);
        writeYamlScalar(stream, "    ", "mechanism_target_marker_groups", report.mechanismTargetMarkerGroups);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_target_marker_candidates",
            report.mechanismTargetMarkerCandidates);
        writeYamlScalar(stream, "    ", "mechanism_target_marker_vertices", report.mechanismTargetMarkerVertices);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_target_marker_source_links",
            report.mechanismTargetMarkerSourceLinks);
        writeYamlScalar(stream, "    ", "mechanism_gizmo_candidates", report.mechanismGizmoCandidates);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_circle_gizmo_candidates",
            report.mechanismCircleGizmoCandidates);
        writeYamlScalar(stream, "    ", "mechanism_target_gizmo_candidates", report.mechanismTargetGizmoCandidates);
        writeYamlScalar(stream, "    ", "mechanism_motion_path_markers", report.mechanismMotionPathMarkers);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_los_checked_candidates",
            report.mechanismLineOfSightCheckedCandidates);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_los_blocked_candidates",
            report.mechanismLineOfSightBlockedCandidates);
        writeYamlScalar(stream, "    ", "light_objects", report.lightObjects);
        writeYamlScalar(stream, "    ", "light_overlay_vertices", report.lightOverlayVertices);
        writeYamlScalar(stream, "    ", "static_render_lights", report.staticRenderLights);
        writeYamlScalar(stream, "    ", "light_diagnostics", report.lightDiagnostics);
        writeYamlScalar(stream, "    ", "sound_objects", report.soundObjects);
        writeYamlScalar(stream, "    ", "sound_overlay_vertices", report.soundOverlayVertices);
        writeYamlScalar(stream, "    ", "sound_references", report.soundReferences);
        writeYamlScalar(stream, "    ", "resolved_sound_references", report.resolvedSoundReferences);
        writeYamlScalar(
            stream,
            "    ",
            "unresolved_required_sound_references",
            report.unresolvedRequiredSoundReferences);
        writeYamlScalar(stream, "    ", "spawn_source_objects", report.spawnSourceObjects);
        writeYamlScalar(stream, "    ", "spawn_overlay_vertices", report.spawnOverlayVertices);
        writeYamlScalar(stream, "    ", "spawn_npc_numbers", report.spawnNpcNumbers);
        writeYamlScalar(stream, "    ", "model_instances", report.modelInstances);
        writeYamlScalar(stream, "    ", "model_instances_in_camera_frame", report.modelInstancesInCameraFrame);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_world_model_targets_without_movable_role",
            report.mechanismWorldModelTargetsWithoutMovableRole);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_world_model_targets_missing_model",
            report.mechanismWorldModelTargetsMissingModel);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_world_model_targets_missing_polygon_group",
            report.mechanismWorldModelTargetsMissingPolygonGroup);
        writeYamlScalar(
            stream,
            "    ",
            "mechanism_world_model_targets_mismatched_polygon_group",
            report.mechanismWorldModelTargetsMismatchedPolygonGroup);
        writeYamlScalar(stream, "    ", "actor_variant_candidates", report.actorVariantCandidates);
        writeYamlScalar(
            stream,
            "    ",
            "actor_variant_gameplay_identity_rows",
            report.actorVariantGameplayIdentityRows);
        writeYamlScalar(stream, "    ", "actor_variant_foot_sound_fields", report.actorVariantFootSoundFields);
        writeYamlScalar(
            stream,
            "    ",
            "actor_variant_resolved_foot_sounds",
            report.actorVariantResolvedFootSounds);
        writeYamlScalar(
            stream,
            "    ",
            "actor_variant_unresolved_foot_sounds",
            report.actorVariantUnresolvedFootSounds);
        writeYamlScalar(
            stream,
            "    ",
            "actor_variant_source_sound_references",
            report.actorVariantSourceSoundReferences);
        writeYamlScalar(
            stream,
            "    ",
            "actor_variant_resolved_source_sound_references",
            report.actorVariantResolvedSourceSoundReferences);
        writeYamlScalar(
            stream,
            "    ",
            "actor_variant_unresolved_source_sound_references",
            report.actorVariantUnresolvedSourceSoundReferences);
        writeYamlScalar(
            stream,
            "    ",
            "actor_variant_source_voice_references",
            report.actorVariantSourceVoiceReferences);
        writeYamlScalar(
            stream,
            "    ",
            "actor_variant_resolved_source_voice_references",
            report.actorVariantResolvedSourceVoiceReferences);
        writeYamlScalar(
            stream,
            "    ",
            "actor_variant_unresolved_source_voice_references",
            report.actorVariantUnresolvedSourceVoiceReferences);
        writeYamlScalar(stream, "    ", "actor_variant_unresolved", report.actorVariantUnresolved);
        writeYamlScalar(
            stream,
            "    ",
            "scripted_objects_with_model_collision_volumes",
            report.scriptedObjectsWithModelCollisionVolumes);
        writeYamlScalar(
            stream,
            "    ",
            "scripted_objects_requiring_billboard_collision_visuals",
            report.scriptedObjectsRequiringBillboardCollisionVisuals);
        writeYamlScalar(
            stream,
            "    ",
            "missing_scripted_object_collision_visuals",
            report.missingScriptedObjectCollisionVisuals);
        writeYamlScalar(stream, "    ", "mechanism_preview_candidates", report.mechanismPreviewCandidates);
        writeYamlScalar(stream, "    ", "mechanism_preview_changed_bounds", report.mechanismPreviewChangedBounds);
        writeYamlScalar(stream, "    ", "material_textures", report.materialTextures);
        writeYamlScalar(stream, "    ", "resolved_dtx", report.resolvedDtx);
        writeYamlScalar(stream, "    ", "ambiguous_dtx", report.ambiguousDtx);
        writeYamlScalar(stream, "    ", "source_dtx_paths", report.sourceDtxPaths);
        writeYamlScalar(stream, "    ", "default_helper_materials", report.defaultHelperMaterials);
        writeYamlScalar(
            stream,
            "    ",
            "placeholder_missing_source_materials",
            report.placeholderMissingSourceMaterials);
        writeYamlScalar(stream, "    ", "dtx_headers", report.dtxHeaders);
        writeYamlScalar(stream, "    ", "dtx_headers_matching_sidecar", report.dtxHeadersMatchingSidecar);
        writeYamlScalar(stream, "    ", "dtx_user_flag_records", report.dtxUserFlagRecords);
        writeYamlScalar(stream, "    ", "dtx_extra_byte_records", report.dtxExtraByteRecords);
        writeYamlScalar(stream, "    ", "dtx_mip_payloads", report.dtxMipPayloads);
        writeYamlScalar(stream, "    ", "dtx_decoded_preview_mips", report.dtxDecodedPreviewMips);
        writeYamlScalar(stream, "    ", "dtx_section_metadata_records", report.dtxSectionMetadataRecords);
        writeYamlScalar(stream, "    ", "dtx_section_payloads_available", report.dtxSectionPayloadsAvailable);
        writeYamlScalar(stream, "    ", "dtx_command_strings", report.dtxCommandStrings);
        writeYamlScalar(
            stream,
            "    ",
            "decoded_cache_determinism_checked",
            report.decodedCacheDeterminismChecked);
        writeYamlScalar(stream, "    ", "decoded_cache_source_decoded", report.decodedCacheSourceDecoded);
        writeYamlScalar(stream, "    ", "decoded_cache_image_decoded", report.decodedCacheImageDecoded);
        writeYamlScalar(stream, "    ", "decoded_cache_matches_source", report.decodedCacheMatchesSource);
        writeYamlScalar(stream, "    ", "decoded_cache_mismatches", report.decodedCacheMismatches);
        writeYamlScalar(stream, "    ", "sprite_materials", report.spriteMaterials);
        writeYamlScalar(stream, "    ", "resolved_sprite_materials", report.resolvedSpriteMaterials);
        writeYamlScalar(stream, "    ", "sprite_frame_textures", report.spriteFrameTextures);
        writeYamlScalar(stream, "    ", "resolved_sprite_frame_textures", report.resolvedSpriteFrameTextures);
        writeYamlScalar(stream, "    ", "unresolved_sprite_frame_textures", report.unresolvedSpriteFrameTextures);
        writeYamlScalar(stream, "    ", "ambiguous_sprite_frame_textures", report.ambiguousSpriteFrameTextures);
        writeYamlScalar(stream, "    ", "diagnostic_errors", report.diagnosticErrors);
        writeYamlScalar(stream, "    ", "diagnostic_warnings", report.diagnosticWarnings);
        writeYamlScalar(stream, "    ", "diagnostic_info", report.diagnosticInfo);
    }

    return true;
}

void writeMm9RawObjectAssetReferenceStatus(
    std::ostream &stream,
    const EditorMm9RawObjectAssetReferenceStatus &status)
{
    stream << "    - source_object_index: " << status.sourceObjectIndex << '\n';
    writeYamlScalar(stream, "      ", "source_class", status.sourceClass);
    writeYamlScalar(stream, "      ", "object_name", status.objectName);
    writeYamlScalar(stream, "      ", "property_index", status.propertyIndex);
    writeYamlScalar(stream, "      ", "property_name", status.propertyName);
    writeYamlScalar(stream, "      ", "source_family", status.sourceFamily);
    writeYamlScalar(stream, "      ", "source_value", status.sourceValue);
    writeYamlScalar(stream, "      ", "normalized_key", status.normalizedKey);
    writeYamlScalar(stream, "      ", "required", status.required);
    writeYamlScalar(stream, "      ", "resolved", status.resolved);
    writeYamlScalar(stream, "      ", "ambiguous", status.ambiguous);
    writeYamlScalar(stream, "      ", "alias_applied", status.aliasApplied);
    writeYamlScalar(stream, "      ", "builtin_reference", status.builtinReference);

    if (!status.resolvedSourcePath.empty())
    {
        writeYamlScalar(stream, "      ", "resolved_source_path", status.resolvedSourcePath);
    }

    if (!status.resolutionSource.empty())
    {
        writeYamlScalar(stream, "      ", "resolution_source", status.resolutionSource);
    }

    if (!status.aliasTargetKey.empty())
    {
        writeYamlScalar(stream, "      ", "alias_target_key", status.aliasTargetKey);
    }

    if (!status.sourceCandidates.empty())
    {
        stream << "      candidates:\n";

        for (const std::string &candidate : status.sourceCandidates)
        {
            stream << "        - ";
            writeYamlQuoted(stream, candidate);
            stream << '\n';
        }
    }
}

struct Mm9ModelInstanceAssetResolutionSummary
{
    struct UnresolvedActorVariant
    {
        size_t sourceObjectIndex = 0;
        std::string sourceRef;
        std::string sourceClass;
        std::string sourceName;
        std::string sourceModel;
        std::string sourceSkin;
    };

    size_t total = 0;
    size_t resolvedAssets = 0;
    size_t missingAssets = 0;
    size_t drawableGeometry = 0;
    size_t missingDrawableGeometry = 0;
    size_t decodedSkinTextures = 0;
    size_t actorVariantCandidates = 0;
    size_t actorVariantResolved = 0;
    size_t actorVariantUnresolved = 0;
    size_t actorVariantActorRows = 0;
    size_t actorVariantGameplayIdentityRows = 0;
    size_t actorVariantFootSoundFields = 0;
    size_t actorVariantResolvedFootSounds = 0;
    size_t actorVariantUnresolvedFootSounds = 0;
    size_t actorVariantSourceSoundReferences = 0;
    size_t actorVariantResolvedSourceSoundReferences = 0;
    size_t actorVariantUnresolvedSourceSoundReferences = 0;
    size_t actorVariantSourceVoiceReferences = 0;
    size_t actorVariantResolvedSourceVoiceReferences = 0;
    size_t actorVariantUnresolvedSourceVoiceReferences = 0;
    size_t scriptedObjects = 0;
    size_t scriptedObjectsWithCollisionVisuals = 0;
    size_t scriptedObjectsWithModelCollisionVolumes = 0;
    size_t scriptedObjectsRequiringBillboardCollisionVisuals = 0;
    size_t missingScriptedObjectCollisionVisuals = 0;
    std::vector<UnresolvedActorVariant> unresolvedActorVariants;
};

struct Mm9DatViewportRenderabilitySummary
{
    struct MissingMaterialTriangle
    {
        size_t triangleIndex = 0;
        size_t sourceModelIndex = 0;
        size_t sourcePolyIndex = 0;
        size_t sourceSurfaceIndex = 0;
        size_t sourceTextureIndex = 0;
        size_t materialCandidateCount = 0;
        uint32_t filterFlags = 0;
        std::string sourceTexture;
        std::string alias;
        bool assigned = false;
        bool ambiguous = false;
        bool sourceDtxResolved = false;
        bool placeholderMissingSource = false;
    };

    size_t nativeRenderableTriangles = 0;
    size_t nativeRenderablePhysicsTriangles = 0;
    size_t nativeTexturedTriangles = 0;
    size_t nativeMissingMaterialTriangles = 0;
    size_t nativePlaceholderMaterialTriangles = 0;
    size_t nativeUnresolvedMaterialTriangles = 0;
    size_t modelInstanceDrawableGeometry = 0;
    size_t modelInstanceDecodedSkinTextures = 0;
    std::vector<MissingMaterialTriangle> missingMaterialTriangles;
};

struct Mm9ModelInstanceCameraFrameSummary
{
    size_t total = 0;
    size_t inFront = 0;
    size_t inDepthRange = 0;
    size_t inView = 0;
};

struct Mm9MechanismValidationSummary
{
    struct CandidateWorldModel
    {
        size_t sourceModelIndex = 0;
        std::string sourceName;
        bool movable = false;
        float distanceFromRotationPointLt = 0.0f;
    };

    struct UnresolvedMechanismTarget
    {
        int sourceObjectIndex = -1;
        std::string sourceClass;
        std::string sourceName;
        std::string mechanismId;
        std::string targetKind;
        std::string confidence;
        bool required = false;
        std::vector<CandidateWorldModel> nearestWorldModels;
    };

    struct IncompleteMotion
    {
        int sourceObjectIndex = -1;
        std::string sourceClass;
        std::string sourceName;
        std::string mechanismId;
        std::string motionKind;
        std::vector<std::string> missingFields;
    };

    struct NonMovableWorldModelTarget
    {
        int sourceObjectIndex = -1;
        std::string sourceClass;
        std::string sourceName;
        std::string mechanismId;
        size_t sourceModelIndex = 0;
        std::string sourceModelName;
        std::string confidence;
        bool targetModelFound = false;
    };

    struct PolygonGroupTargetIssue
    {
        int sourceObjectIndex = -1;
        std::string sourceClass;
        std::string sourceName;
        std::string mechanismId;
        size_t bmodelIndex = 0;
        size_t groupSourceModelIndex = 0;
        std::string confidence;
        std::string issue;
    };

    struct InertPreviewMechanism
    {
        int sourceObjectIndex = -1;
        std::string sourceClass;
        std::string sourceName;
        std::string mechanismId;
        std::string reason;
        bool hasPreviewMotion = false;
        bool hasPreviewWorldModelTarget = false;
        bool hasBinding = false;
        bool requiredTarget = false;
    };

    size_t total = 0;
    size_t withBinding = 0;
    size_t withWorldModelTarget = 0;
    size_t withModelInstanceTarget = 0;
    size_t movableWorldModels = 0;
    size_t worldModelTargetsWithMovableRole = 0;
    size_t worldModelTargetsWithoutMovableRole = 0;
    size_t worldModelTargetsMissingModel = 0;
    size_t worldModelTargetsWithPolygonGroup = 0;
    size_t worldModelTargetsMissingPolygonGroup = 0;
    size_t worldModelTargetsMismatchedPolygonGroup = 0;
    size_t withLinearMotion = 0;
    size_t withRotationMotion = 0;
    size_t withSoundEvidence = 0;
    size_t soundSlots = 0;
    size_t authoredSoundReferences = 0;
    size_t emptySoundReferences = 0;
    size_t previewableMechanisms = 0;
    size_t inertMechanisms = 0;
    size_t mechanismsWithoutPreviewMotion = 0;
    size_t mechanismsWithoutPreviewTarget = 0;
    size_t activationStartOpenFields = 0;
    size_t activationLockedFields = 0;
    size_t activationPushOpenFields = 0;
    size_t activationTouchToOpenFields = 0;
    size_t activationLockOnCloseFields = 0;
    size_t activationReopenOnContactFields = 0;
    size_t rotationOpenAwayFields = 0;
    size_t timingMoveDelayFields = 0;
    size_t timingOpenWaitFields = 0;
    size_t triggerOutputs = 0;
    size_t unresolvedTriggerOutputs = 0;
    size_t incompleteLinearMotion = 0;
    size_t incompleteRotationMotion = 0;
    size_t unresolvedTargets = 0;
    size_t unresolvedRequiredTargets = 0;
    std::vector<UnresolvedMechanismTarget> unresolved;
    std::vector<IncompleteMotion> incompleteMotion;
    std::vector<NonMovableWorldModelTarget> nonMovableWorldModelTargets;
    std::vector<PolygonGroupTargetIssue> polygonGroupTargetIssues;
    std::vector<InertPreviewMechanism> inertPreviewMechanisms;
};

struct Mm9MechanismPreviewValidationSummary
{
    size_t candidates = 0;
    size_t targetFound = 0;
    size_t transformedTriangles = 0;
    size_t changedBounds = 0;
};

struct Mm9InspectorSearchEntry
{
    std::string family;
    std::string label;
    std::string sourceRef;
    std::string searchText;
};

void appendMm9InspectorSearchEntry(
    std::vector<Mm9InspectorSearchEntry> &entries,
    const std::string &family,
    const std::string &label,
    const std::string &sourceRef,
    const std::vector<std::string> &values)
{
    std::ostringstream searchText;
    searchText << family << ' ' << label << ' ' << sourceRef;

    for (const std::string &value : values)
    {
        searchText << ' ' << value;
    }

    Mm9InspectorSearchEntry entry = {};
    entry.family = family;
    entry.label = label;
    entry.sourceRef = sourceRef;
    entry.searchText = lowerAsciiCopy(searchText.str());
    entries.push_back(std::move(entry));
}

size_t countMm9InspectorSearchMatches(
    const std::vector<Mm9InspectorSearchEntry> &entries,
    const std::string &family,
    const std::string &query)
{
    const std::string normalizedQuery = lowerAsciiCopy(query);
    size_t matches = 0;

    for (const Mm9InspectorSearchEntry &entry : entries)
    {
        if (!family.empty() && entry.family != family)
        {
            continue;
        }

        if (entry.searchText.find(normalizedQuery) != std::string::npos)
        {
            ++matches;
        }
    }

    return matches;
}

size_t countMm9InspectorSearchFamily(
    const std::vector<Mm9InspectorSearchEntry> &entries,
    const std::string &family)
{
    size_t count = 0;

    for (const Mm9InspectorSearchEntry &entry : entries)
    {
        if (entry.family == family)
        {
            ++count;
        }
    }

    return count;
}

float mm9DistanceFromRotationPointLt(
    const std::vector<float> &rotationPointLt,
    const EditorMm9Vec3 &positionLt)
{
    if (rotationPointLt.size() < 3)
    {
        return 0.0f;
    }

    const float deltaX = rotationPointLt[0] - positionLt.x;
    const float deltaY = rotationPointLt[1] - positionLt.y;
    const float deltaZ = rotationPointLt[2] - positionLt.z;
    return std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
}

std::vector<Mm9MechanismValidationSummary::CandidateWorldModel> nearestMm9MovableWorldModelsForMechanism(
    const EditorMm9DatWorldSidecar &datWorld,
    const OpenYAMM::Game::Mm9EventMechanism &mechanism)
{
    std::vector<Mm9MechanismValidationSummary::CandidateWorldModel> candidates;

    if (!mechanism.rotation.hasRotationPoint || mechanism.rotation.rotationPointLt.size() < 3)
    {
        return candidates;
    }

    for (const EditorMm9DatWorldModelSummary &worldModel : datWorld.worldModels)
    {
        if (!worldModel.roles.movable)
        {
            continue;
        }

        Mm9MechanismValidationSummary::CandidateWorldModel candidate = {};
        candidate.sourceModelIndex = worldModel.sourceModelIndex;
        candidate.sourceName = worldModel.sourceName;
        candidate.movable = worldModel.roles.movable;
        candidate.distanceFromRotationPointLt =
            mm9DistanceFromRotationPointLt(mechanism.rotation.rotationPointLt, worldModel.worldTranslationLt);
        candidates.push_back(std::move(candidate));
    }

    std::sort(
        candidates.begin(),
        candidates.end(),
        [](const Mm9MechanismValidationSummary::CandidateWorldModel &left,
           const Mm9MechanismValidationSummary::CandidateWorldModel &right)
        {
            return left.distanceFromRotationPointLt < right.distanceFromRotationPointLt;
        });

    if (candidates.size() > 5)
    {
        candidates.resize(5);
    }

    return candidates;
}

const OpenYAMM::Game::Mm9EventBinding *findMm9EventBindingForObject(
    const OpenYAMM::Game::Mm9EventsData &events,
    const std::string &objectId)
{
    for (const OpenYAMM::Game::Mm9EventBinding &binding : events.bindings)
    {
        if (binding.objectId == objectId)
        {
            return &binding;
        }
    }

    return nullptr;
}

const EditorMm9DatWorldModelSummary *findMm9DatWorldModelBySourceIndex(
    const EditorMm9DatWorldSidecar &datWorld,
    size_t sourceModelIndex)
{
    for (const EditorMm9DatWorldModelSummary &worldModel : datWorld.worldModels)
    {
        if (worldModel.sourceModelIndex == sourceModelIndex)
        {
            return &worldModel;
        }
    }

    return nullptr;
}

bool isMm9RequiredMechanismTarget(const OpenYAMM::Game::Mm9EventMechanism &mechanism)
{
    return mechanism.sourceClass != "ScriptObject";
}

Mm9MechanismValidationSummary summarizeMm9Mechanisms(
    const OpenYAMM::Game::Mm9EventsData &events,
    const EditorMm9DatWorldSidecar &datWorld)
{
    Mm9MechanismValidationSummary summary = {};
    summary.total = events.mechanisms.size();

    for (const EditorMm9DatWorldModelSummary &worldModel : datWorld.worldModels)
    {
        if (worldModel.roles.movable)
        {
            ++summary.movableWorldModels;
        }
    }

    for (const OpenYAMM::Game::Mm9EventMechanism &mechanism : events.mechanisms)
    {
        const OpenYAMM::Game::Mm9EventBinding *pBinding =
            findMm9EventBindingForObject(events, mechanism.objectId);

        const bool hasAnyLinearMotion =
            mechanism.linear.hasMoveDir
            || mechanism.linear.hasMoveDist
            || mechanism.linear.hasOpenSpeed
            || mechanism.linear.hasCloseSpeed;
        const bool hasAnyRotationMotion =
            mechanism.rotation.hasRotationPoint
            || mechanism.rotation.hasRotationAngles;
        const bool hasPreviewMotion =
            (mechanism.linear.hasMoveDir
                && mechanism.linear.hasMoveDist
                && std::fabs(mechanism.linear.moveDistLt) > 0.0001f)
            || (mechanism.rotation.hasRotationPoint && mechanism.rotation.hasRotationAngles);
        bool hasPreviewWorldModelTarget = false;

        if (pBinding != nullptr)
        {
            for (const OpenYAMM::Game::Mm9EventBindingTarget &target : pBinding->targets)
            {
                if (target.targetKind == "odm_bmodel" && target.bmodelIndex.has_value())
                {
                    hasPreviewWorldModelTarget = true;
                    break;
                }
            }
        }

        if (hasPreviewMotion && hasPreviewWorldModelTarget)
        {
            ++summary.previewableMechanisms;
        }
        else
        {
            ++summary.inertMechanisms;
            Mm9MechanismValidationSummary::InertPreviewMechanism inert = {};
            inert.sourceObjectIndex = mechanism.sourceObjectIndex;
            inert.sourceClass = mechanism.sourceClass;
            inert.sourceName = mechanism.sourceName;
            inert.mechanismId = mechanism.mechanismId;
            inert.hasPreviewMotion = hasPreviewMotion;
            inert.hasPreviewWorldModelTarget = hasPreviewWorldModelTarget;
            inert.hasBinding = pBinding != nullptr;
            inert.requiredTarget = isMm9RequiredMechanismTarget(mechanism);

            if (!hasPreviewMotion)
            {
                ++summary.mechanismsWithoutPreviewMotion;
            }
            if (!hasPreviewWorldModelTarget)
            {
                ++summary.mechanismsWithoutPreviewTarget;
            }

            if (!hasPreviewMotion && !hasPreviewWorldModelTarget)
            {
                inert.reason = "missing_preview_motion_and_world_model_target";
            }
            else if (!hasPreviewMotion)
            {
                inert.reason = "missing_preview_motion";
            }
            else
            {
                inert.reason = "missing_preview_world_model_target";
            }

            summary.inertPreviewMechanisms.push_back(std::move(inert));
        }

        if (mechanism.activation.hasStartOpen)
        {
            ++summary.activationStartOpenFields;
        }
        if (mechanism.activation.hasLocked)
        {
            ++summary.activationLockedFields;
        }
        if (mechanism.activation.hasPushOpen)
        {
            ++summary.activationPushOpenFields;
        }
        if (mechanism.activation.hasTouchToOpen)
        {
            ++summary.activationTouchToOpenFields;
        }
        if (mechanism.activation.hasLockOnClose)
        {
            ++summary.activationLockOnCloseFields;
        }
        if (mechanism.activation.hasReopenOnContact)
        {
            ++summary.activationReopenOnContactFields;
        }
        if (mechanism.rotation.hasOpenAway)
        {
            ++summary.rotationOpenAwayFields;
        }
        if (mechanism.timing.hasMoveDelaySecondsSource)
        {
            ++summary.timingMoveDelayFields;
        }
        if (mechanism.timing.hasOpenWaitSecondsSource)
        {
            ++summary.timingOpenWaitFields;
        }

        if (!mechanism.sounds.empty())
        {
            ++summary.withSoundEvidence;
        }

        summary.soundSlots += mechanism.sounds.size();
        for (const OpenYAMM::Game::Mm9EventMechanismSound &sound : mechanism.sounds)
        {
            if (!sound.soundName.empty())
            {
                ++summary.authoredSoundReferences;
            }
            else if (sound.authored)
            {
                ++summary.emptySoundReferences;
            }
        }

        summary.triggerOutputs += mechanism.triggerOutputs.size();
        for (const OpenYAMM::Game::Mm9EventTriggerOutput &output : mechanism.triggerOutputs)
        {
            if (output.resolution == "unresolved")
            {
                ++summary.unresolvedTriggerOutputs;
            }
        }

        if (hasAnyLinearMotion)
        {
            ++summary.withLinearMotion;

            std::vector<std::string> missingFields;
            if (!mechanism.linear.hasMoveDir)
            {
                missingFields.push_back("MoveDir");
            }
            if (!mechanism.linear.hasMoveDist)
            {
                missingFields.push_back("MoveDist");
            }
            if (!mechanism.linear.hasOpenSpeed)
            {
                missingFields.push_back("OpenSpeed");
            }
            if (!mechanism.linear.hasCloseSpeed)
            {
                missingFields.push_back("CloseSpeed");
            }

            if (!missingFields.empty())
            {
                Mm9MechanismValidationSummary::IncompleteMotion incomplete = {};
                incomplete.sourceObjectIndex = mechanism.sourceObjectIndex;
                incomplete.sourceClass = mechanism.sourceClass;
                incomplete.sourceName = mechanism.sourceName;
                incomplete.mechanismId = mechanism.mechanismId;
                incomplete.motionKind = "linear";
                incomplete.missingFields = std::move(missingFields);
                ++summary.incompleteLinearMotion;
                summary.incompleteMotion.push_back(std::move(incomplete));
            }
        }

        if (hasAnyRotationMotion)
        {
            ++summary.withRotationMotion;

            std::vector<std::string> missingFields;
            if (!mechanism.rotation.hasRotationPoint)
            {
                missingFields.push_back("RotationPoint");
            }
            if (!mechanism.rotation.hasRotationAngles)
            {
                missingFields.push_back("RotationAngles");
            }

            if (!missingFields.empty())
            {
                Mm9MechanismValidationSummary::IncompleteMotion incomplete = {};
                incomplete.sourceObjectIndex = mechanism.sourceObjectIndex;
                incomplete.sourceClass = mechanism.sourceClass;
                incomplete.sourceName = mechanism.sourceName;
                incomplete.mechanismId = mechanism.mechanismId;
                incomplete.motionKind = "rotation";
                incomplete.missingFields = std::move(missingFields);
                ++summary.incompleteRotationMotion;
                summary.incompleteMotion.push_back(std::move(incomplete));
            }
        }

        if (pBinding == nullptr || pBinding->targets.empty())
        {
            Mm9MechanismValidationSummary::UnresolvedMechanismTarget unresolved = {};
            unresolved.sourceObjectIndex = mechanism.sourceObjectIndex;
            unresolved.sourceClass = mechanism.sourceClass;
            unresolved.sourceName = mechanism.sourceName;
            unresolved.mechanismId = mechanism.mechanismId;
            unresolved.targetKind = "<missing_binding>";
            unresolved.confidence = "<missing_binding>";
            unresolved.required = isMm9RequiredMechanismTarget(mechanism);
            unresolved.nearestWorldModels = nearestMm9MovableWorldModelsForMechanism(datWorld, mechanism);
            ++summary.unresolvedTargets;
            if (unresolved.required)
            {
                ++summary.unresolvedRequiredTargets;
            }
            summary.unresolved.push_back(std::move(unresolved));
            continue;
        }

        ++summary.withBinding;
        bool hasResolvedTarget = false;

        for (const OpenYAMM::Game::Mm9EventBindingTarget &target : pBinding->targets)
        {
            if (target.targetKind == "odm_bmodel" && target.bmodelIndex.has_value())
            {
                ++summary.withWorldModelTarget;
                hasResolvedTarget = true;

                const EditorMm9DatWorldModelSummary *pTargetWorldModel =
                    findMm9DatWorldModelBySourceIndex(datWorld, *target.bmodelIndex);

                if (pTargetWorldModel != nullptr && pTargetWorldModel->roles.movable)
                {
                    ++summary.worldModelTargetsWithMovableRole;
                }
                else
                {
                    Mm9MechanismValidationSummary::NonMovableWorldModelTarget nonMovableTarget = {};
                    nonMovableTarget.sourceObjectIndex = mechanism.sourceObjectIndex;
                    nonMovableTarget.sourceClass = mechanism.sourceClass;
                    nonMovableTarget.sourceName = mechanism.sourceName;
                    nonMovableTarget.mechanismId = mechanism.mechanismId;
                    nonMovableTarget.sourceModelIndex = *target.bmodelIndex;
                    nonMovableTarget.sourceModelName = target.sourceModelName.empty()
                        ? target.bmodelName
                        : target.sourceModelName;
                    nonMovableTarget.confidence = target.confidence;
                    nonMovableTarget.targetModelFound = pTargetWorldModel != nullptr;

                    if (pTargetWorldModel != nullptr)
                    {
                        nonMovableTarget.sourceModelName = pTargetWorldModel->sourceName;
                        ++summary.worldModelTargetsWithoutMovableRole;
                    }
                    else
                    {
                        ++summary.worldModelTargetsMissingModel;
                    }

                    summary.nonMovableWorldModelTargets.push_back(std::move(nonMovableTarget));
                }

                if (target.sourcePolygonGroup.has_value())
                {
                    ++summary.worldModelTargetsWithPolygonGroup;

                    if (target.sourcePolygonGroup->sourceModelIndex != *target.bmodelIndex)
                    {
                        Mm9MechanismValidationSummary::PolygonGroupTargetIssue issue = {};
                        issue.sourceObjectIndex = mechanism.sourceObjectIndex;
                        issue.sourceClass = mechanism.sourceClass;
                        issue.sourceName = mechanism.sourceName;
                        issue.mechanismId = mechanism.mechanismId;
                        issue.bmodelIndex = *target.bmodelIndex;
                        issue.groupSourceModelIndex = target.sourcePolygonGroup->sourceModelIndex;
                        issue.confidence = target.confidence;
                        issue.issue = "source_polygon_group_model_mismatch";
                        ++summary.worldModelTargetsMismatchedPolygonGroup;
                        summary.polygonGroupTargetIssues.push_back(std::move(issue));
                    }
                }
                else
                {
                    Mm9MechanismValidationSummary::PolygonGroupTargetIssue issue = {};
                    issue.sourceObjectIndex = mechanism.sourceObjectIndex;
                    issue.sourceClass = mechanism.sourceClass;
                    issue.sourceName = mechanism.sourceName;
                    issue.mechanismId = mechanism.mechanismId;
                    issue.bmodelIndex = *target.bmodelIndex;
                    issue.confidence = target.confidence;
                    issue.issue = "missing_source_polygon_group";
                    ++summary.worldModelTargetsMissingPolygonGroup;
                    summary.polygonGroupTargetIssues.push_back(std::move(issue));
                }
            }
            else if (target.targetKind == "model_instance" && !target.targetId.empty())
            {
                ++summary.withModelInstanceTarget;
                hasResolvedTarget = true;
            }
            else if (target.targetKind == "unresolved")
            {
                Mm9MechanismValidationSummary::UnresolvedMechanismTarget unresolved = {};
                unresolved.sourceObjectIndex = mechanism.sourceObjectIndex;
                unresolved.sourceClass = mechanism.sourceClass;
                unresolved.sourceName = mechanism.sourceName;
                unresolved.mechanismId = mechanism.mechanismId;
                unresolved.targetKind = target.targetKind;
                unresolved.confidence = target.confidence;
                unresolved.required = isMm9RequiredMechanismTarget(mechanism);
                unresolved.nearestWorldModels = nearestMm9MovableWorldModelsForMechanism(datWorld, mechanism);
                ++summary.unresolvedTargets;
                if (unresolved.required)
                {
                    ++summary.unresolvedRequiredTargets;
                }
                summary.unresolved.push_back(std::move(unresolved));
            }
        }

        if (!hasResolvedTarget)
        {
            bool alreadyRecorded = false;
            for (const Mm9MechanismValidationSummary::UnresolvedMechanismTarget &unresolved : summary.unresolved)
            {
                if (unresolved.sourceObjectIndex == mechanism.sourceObjectIndex)
                {
                    alreadyRecorded = true;
                    break;
                }
            }

            if (!alreadyRecorded)
            {
                Mm9MechanismValidationSummary::UnresolvedMechanismTarget unresolved = {};
                unresolved.sourceObjectIndex = mechanism.sourceObjectIndex;
                unresolved.sourceClass = mechanism.sourceClass;
                unresolved.sourceName = mechanism.sourceName;
                unresolved.mechanismId = mechanism.mechanismId;
                unresolved.targetKind = "<no_resolved_target>";
                unresolved.confidence = "<no_resolved_target>";
                unresolved.required = isMm9RequiredMechanismTarget(mechanism);
                unresolved.nearestWorldModels = nearestMm9MovableWorldModelsForMechanism(datWorld, mechanism);
                ++summary.unresolvedTargets;
                if (unresolved.required)
                {
                    ++summary.unresolvedRequiredTargets;
                }
                summary.unresolved.push_back(std::move(unresolved));
            }
        }
    }

    return summary;
}

bool mm9Vec3FromFloatVector(const std::vector<float> &values, OpenYAMM::Game::Mm9DatVec3 &result)
{
    if (values.size() < 3)
    {
        return false;
    }

    result = {values[0], values[1], values[2]};
    return true;
}

Mm9MechanismPreviewValidationSummary validateMm9MechanismPreviewTransforms(
    const OpenYAMM::Game::Mm9EventsData &events,
    const OpenYAMM::Game::Mm9DatRenderMesh &mesh)
{
    Mm9MechanismPreviewValidationSummary summary = {};

    for (const OpenYAMM::Game::Mm9EventMechanism &mechanism : events.mechanisms)
    {
        const OpenYAMM::Game::Mm9EventBinding *pBinding =
            findMm9EventBindingForObject(events, mechanism.objectId);

        if (pBinding == nullptr)
        {
            continue;
        }

        OpenYAMM::Game::Mm9DatMechanismPreviewMotion motion = {};
        motion.progress = 1.0f;
        motion.hasLinearMotion =
            mechanism.linear.hasMoveDir
            && mechanism.linear.hasMoveDist
            && std::fabs(mechanism.linear.moveDistLt) > 0.0001f
            && mm9Vec3FromFloatVector(mechanism.linear.moveDirLt, motion.moveDirLt);
        motion.moveDistLt = mechanism.linear.moveDistLt;
        motion.hasRotationMotion =
            mechanism.rotation.hasRotationPoint
            && mechanism.rotation.hasRotationAngles
            && mm9Vec3FromFloatVector(mechanism.rotation.rotationPointLt, motion.rotationPointLt)
            && mm9Vec3FromFloatVector(mechanism.rotation.rotationAnglesDeg, motion.rotationAnglesDeg);

        if (!motion.hasLinearMotion && !motion.hasRotationMotion)
        {
            continue;
        }

        for (const OpenYAMM::Game::Mm9EventBindingTarget &target : pBinding->targets)
        {
            if (target.targetKind != "odm_bmodel" || !target.bmodelIndex.has_value())
            {
                continue;
            }

            ++summary.candidates;
            motion.sourceModelIndex = *target.bmodelIndex;

            const OpenYAMM::Game::Mm9DatMechanismPreviewResult preview =
                OpenYAMM::Game::buildMm9DatMechanismPreviewMesh(mesh, motion);

            if (preview.targetFound)
            {
                ++summary.targetFound;
            }

            summary.transformedTriangles += preview.transformedTriangles;

            if (preview.boundsChanged)
            {
                ++summary.changedBounds;
            }
        }
    }

    return summary;
}

bool mm9DatFilterEntryShouldRenderInEditorViewport(const OpenYAMM::Game::Mm9DatRenderFilterEntry &filterEntry)
{
    const bool visual =
        (filterEntry.flags
            & (OpenYAMM::Game::Mm9DatRenderFilterVisual
                | OpenYAMM::Game::Mm9DatRenderFilterSky
                | OpenYAMM::Game::Mm9DatRenderFilterWater
                | OpenYAMM::Game::Mm9DatRenderFilterTerrain
                | OpenYAMM::Game::Mm9DatRenderFilterPhysics
                | OpenYAMM::Game::Mm9DatRenderFilterMovable)) != 0;
    const bool hiddenHelper =
        (filterEntry.flags
            & (OpenYAMM::Game::Mm9DatRenderFilterInvisible
                | OpenYAMM::Game::Mm9DatRenderFilterWaterVolume
                | OpenYAMM::Game::Mm9DatRenderFilterRail
                | OpenYAMM::Game::Mm9DatRenderFilterVisibility
                | OpenYAMM::Game::Mm9DatRenderFilterTrigger)) != 0;

    return visual && !hiddenHelper;
}

Mm9DatViewportRenderabilitySummary summarizeMm9DatViewportRenderability(
    const OpenYAMM::Game::Mm9DatRenderFilterResult &nativeFilters,
    const std::vector<OpenYAMM::Game::Mm9DatRenderMaterialAssignment> &materialAssignments,
    const Mm9ModelInstanceAssetResolutionSummary &modelInstanceSummary)
{
    Mm9DatViewportRenderabilitySummary summary = {};

    for (const OpenYAMM::Game::Mm9DatRenderFilterEntry &filterEntry : nativeFilters.entries)
    {
        if (!mm9DatFilterEntryShouldRenderInEditorViewport(filterEntry))
        {
            continue;
        }

        ++summary.nativeRenderableTriangles;

        if ((filterEntry.flags & OpenYAMM::Game::Mm9DatRenderFilterPhysics) != 0)
        {
            ++summary.nativeRenderablePhysicsTriangles;
        }

        const bool hasTexturedMaterial =
            filterEntry.triangleIndex < materialAssignments.size()
            && materialAssignments[filterEntry.triangleIndex].assigned
            && !materialAssignments[filterEntry.triangleIndex].ambiguous
            && materialAssignments[filterEntry.triangleIndex].sourceDtxResolved
            && !materialAssignments[filterEntry.triangleIndex].resolvedSourcePath.empty();

        if (hasTexturedMaterial)
        {
            ++summary.nativeTexturedTriangles;
        }
        else
        {
            ++summary.nativeMissingMaterialTriangles;

            Mm9DatViewportRenderabilitySummary::MissingMaterialTriangle missing = {};
            missing.triangleIndex = filterEntry.triangleIndex;
            missing.filterFlags = filterEntry.flags;

            if (filterEntry.triangleIndex < materialAssignments.size())
            {
                const OpenYAMM::Game::Mm9DatRenderMaterialAssignment &assignment =
                    materialAssignments[filterEntry.triangleIndex];
                missing.sourceModelIndex = assignment.sourceModelIndex;
                missing.sourcePolyIndex = assignment.sourcePolyIndex;
                missing.sourceSurfaceIndex = assignment.sourceSurfaceIndex;
                missing.sourceTextureIndex = assignment.sourceTextureIndex;
                missing.materialCandidateCount = assignment.materialCandidateCount;
                missing.sourceTexture = assignment.sourceTexture;
                missing.alias = assignment.alias;
                missing.assigned = assignment.assigned;
                missing.ambiguous = assignment.ambiguous;
                missing.sourceDtxResolved = assignment.sourceDtxResolved;
                missing.placeholderMissingSource = assignment.placeholderMissingSource;
            }

            if (missing.placeholderMissingSource)
            {
                ++summary.nativePlaceholderMaterialTriangles;
            }
            else
            {
                ++summary.nativeUnresolvedMaterialTriangles;
            }

            summary.missingMaterialTriangles.push_back(missing);
        }
    }

    summary.modelInstanceDrawableGeometry = modelInstanceSummary.drawableGeometry;
    summary.modelInstanceDecodedSkinTextures = modelInstanceSummary.decodedSkinTextures;
    return summary;
}

size_t countMm9ObjectOverlayVertices(const Game::Mm9ObjectLayer &objectLayer)
{
    size_t vertexCount = 0;

    for (const Game::Mm9Object &object : objectLayer.objects)
    {
        if (!object.hasPosition)
        {
            continue;
        }

        if (object.hasDims)
        {
            vertexCount += 24;
        }
        else if (object.hasRadius)
        {
            vertexCount += 30;
        }
        else if (object.triggerVolume)
        {
            vertexCount += 6;
        }
    }

    return vertexCount;
}

size_t countMm9WorldModelOverlayVertices(const EditorMm9DatWorldSidecar &datWorld)
{
    return datWorld.worldModels.size() * 24;
}

size_t countMm9WorldModelOverlayPickCandidates(const EditorMm9DatWorldSidecar &datWorld)
{
    return datWorld.worldModels.size();
}

struct Mm9SelectedDatOverlaySummary
{
    size_t polygonVertices = 0;
    size_t surfaceVertices = 0;
};

Mm9SelectedDatOverlaySummary summarizeMm9SelectedDatOverlay(
    const Game::Mm9DatRenderMesh &mesh,
    size_t selectedTriangleIndex)
{
    Mm9SelectedDatOverlaySummary summary = {};

    if (selectedTriangleIndex >= mesh.triangles.size())
    {
        return summary;
    }

    const Game::Mm9DatRenderTriangle &selectedTriangle = mesh.triangles[selectedTriangleIndex];

    for (const Game::Mm9DatRenderTriangle &triangle : mesh.triangles)
    {
        if (triangle.sourceModelIndex != selectedTriangle.sourceModelIndex)
        {
            continue;
        }

        if (triangle.sourceSurfaceIndex == selectedTriangle.sourceSurfaceIndex)
        {
            summary.surfaceVertices += 3;
        }

        if (triangle.sourcePolyIndex == selectedTriangle.sourcePolyIndex)
        {
            summary.polygonVertices += 9;
        }
    }

    return summary;
}

bool mm9RawObjectSidecarContainsSourceObject(
    const EditorMm9RawObjectsSidecar &rawObjects,
    size_t sourceObjectIndex)
{
    for (const EditorMm9RawObject &rawObject : rawObjects.objects)
    {
        if (rawObject.objectIndex == sourceObjectIndex)
        {
            return true;
        }
    }

    return false;
}

size_t countMm9ObjectOverlayPickCandidates(
    const Game::Mm9ObjectLayer &objectLayer,
    const EditorMm9RawObjectsSidecar &rawObjects)
{
    size_t candidateCount = 0;

    for (const Game::Mm9Object &object : objectLayer.objects)
    {
        if (!object.hasPosition || (!object.hasDims && !object.hasRadius && !object.triggerVolume))
        {
            continue;
        }

        if (mm9RawObjectSidecarContainsSourceObject(rawObjects, object.sourceObjectIndex))
        {
            ++candidateCount;
        }
    }

    return candidateCount;
}

struct Mm9SourceMarkerOverlaySummary
{
    size_t lightVertices = 0;
    size_t soundVertices = 0;
    size_t spawnVertices = 0;
};

Mm9SourceMarkerOverlaySummary summarizeMm9SourceMarkerOverlayVertices(
    const Game::Mm9LightLayer &lightLayer,
    const Game::Mm9SoundLayer &soundLayer,
    const Game::Mm9SpawnLayer &spawnLayer)
{
    Mm9SourceMarkerOverlaySummary summary = {};

    for (const Game::Mm9LightObject &light : lightLayer.lights)
    {
        if (!light.hasPosition)
        {
            continue;
        }

        summary.lightVertices += 6;

        if (light.hasLightRadius)
        {
            summary.lightVertices += 30;
        }
    }

    for (const Game::Mm9SoundObject &sound : soundLayer.objects)
    {
        if (!sound.hasSoundPosition && !sound.hasPosition)
        {
            continue;
        }

        summary.soundVertices += 6;

        if (sound.hasSoundRadius)
        {
            summary.soundVertices += 30;
        }
    }

    for (const Game::Mm9SpawnObject &spawn : spawnLayer.objects)
    {
        if (!spawn.hasPosition)
        {
            continue;
        }

        summary.spawnVertices += 6;

        if (spawn.hasSpawnObjectVelocity && mm9Length(spawn.spawnObjectVelocityLt) > 0.001f)
        {
            summary.spawnVertices += 2;
        }
    }

    return summary;
}

bool mm9SourceObjectHasMarkerPosition(
    const Game::Mm9ObjectLayer &objectLayer,
    const Game::Mm9LightLayer &lightLayer,
    const Game::Mm9SoundLayer &soundLayer,
    const Game::Mm9SpawnLayer &spawnLayer,
    const Game::OutdoorSceneData &sceneData,
    size_t sourceObjectIndex)
{
    for (const Game::Mm9Object &object : objectLayer.objects)
    {
        if (object.sourceObjectIndex == sourceObjectIndex && object.hasPosition)
        {
            return true;
        }
    }

    for (const Game::Mm9LightObject &light : lightLayer.lights)
    {
        if (light.sourceObjectIndex == sourceObjectIndex && light.hasPosition)
        {
            return true;
        }
    }

    for (const Game::Mm9SoundObject &sound : soundLayer.objects)
    {
        if (sound.sourceObjectIndex == sourceObjectIndex && (sound.hasSoundPosition || sound.hasPosition))
        {
            return true;
        }
    }

    for (const Game::Mm9SpawnObject &spawn : spawnLayer.objects)
    {
        if (spawn.sourceObjectIndex == sourceObjectIndex && spawn.hasPosition)
        {
            return true;
        }
    }

    for (const Game::OutdoorSceneModelInstance &modelInstance : sceneData.modelInstances)
    {
        if (modelInstance.sourceObjectIndex == sourceObjectIndex)
        {
            return true;
        }
    }

    return false;
}

struct Mm9AssetIssueMarkerSummary
{
    size_t sourceObjects = 0;
    size_t candidates = 0;
    size_t unpositioned = 0;
    size_t requiredCandidates = 0;
    size_t requiredUnpositioned = 0;
};

Mm9AssetIssueMarkerSummary summarizeMm9AssetIssueMarkers(
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &statuses,
    const Game::Mm9ObjectLayer &objectLayer,
    const Game::Mm9LightLayer &lightLayer,
    const Game::Mm9SoundLayer &soundLayer,
    const Game::Mm9SpawnLayer &spawnLayer,
    const Game::OutdoorSceneData &sceneData,
    const EditorMm9RawObjectsSidecar &rawObjects)
{
    Mm9AssetIssueMarkerSummary summary = {};
    std::unordered_map<size_t, bool> requiredIssueBySourceObject;

    for (const EditorMm9RawObjectAssetReferenceStatus &status : statuses)
    {
        if (status.resolved && !status.ambiguous)
        {
            continue;
        }

        bool &hasRequiredIssue = requiredIssueBySourceObject[status.sourceObjectIndex];
        hasRequiredIssue = hasRequiredIssue || status.required;
    }

    summary.sourceObjects = requiredIssueBySourceObject.size();

    for (const std::pair<const size_t, bool> &issue : requiredIssueBySourceObject)
    {
        const bool hasMarkerPosition =
            mm9RawObjectSidecarContainsSourceObject(rawObjects, issue.first)
            && mm9SourceObjectHasMarkerPosition(
                objectLayer,
                lightLayer,
                soundLayer,
                spawnLayer,
                sceneData,
                issue.first);

        if (hasMarkerPosition)
        {
            ++summary.candidates;

            if (issue.second)
            {
                ++summary.requiredCandidates;
            }
        }
        else
        {
            ++summary.unpositioned;

            if (issue.second)
            {
                ++summary.requiredUnpositioned;
            }
        }
    }

    return summary;
}

struct Mm9MechanismTargetMarkerSummary
{
    size_t targetGroups = 0;
    size_t candidates = 0;
    size_t vertices = 0;
    size_t sourceLinkedTargets = 0;
    size_t gizmoCandidates = 0;
    size_t circleGizmoCandidates = 0;
    size_t targetGizmoCandidates = 0;
    size_t motionPathMarkers = 0;
    size_t lineOfSightCheckedCandidates = 0;
    size_t lineOfSightBlockedCandidates = 0;
};

bool mm9DatWorldModelBoundsForMarker(
    const EditorMm9DatWorldSidecar &datWorld,
    size_t sourceModelIndex,
    Game::Mm9DatVec3 &center,
    Game::Mm9DatVec3 &halfExtents)
{
    if (sourceModelIndex >= datWorld.worldModels.size())
    {
        return false;
    }

    const EditorMm9DatWorldModelSummary &model = datWorld.worldModels[sourceModelIndex];
    const Game::Mm9DatVec3 minPoint = {
        model.boundsMinLt.x * Game::Mm9DatToOpenYammScale,
        model.boundsMinLt.z * Game::Mm9DatToOpenYammScale,
        model.boundsMinLt.y * Game::Mm9DatToOpenYammScale,
    };
    const Game::Mm9DatVec3 maxPoint = {
        model.boundsMaxLt.x * Game::Mm9DatToOpenYammScale,
        model.boundsMaxLt.z * Game::Mm9DatToOpenYammScale,
        model.boundsMaxLt.y * Game::Mm9DatToOpenYammScale,
    };

    center = {
        (minPoint.x + maxPoint.x) * 0.5f,
        (minPoint.y + maxPoint.y) * 0.5f,
        (minPoint.z + maxPoint.z) * 0.5f,
    };
    halfExtents = {
        std::max(std::fabs(maxPoint.x - minPoint.x) * 0.5f, 16.0f),
        std::max(std::fabs(maxPoint.y - minPoint.y) * 0.5f, 16.0f),
        std::max(std::fabs(maxPoint.z - minPoint.z) * 0.5f, 16.0f),
    };
    return true;
}

bool mm9PointInsideAabb(
    const Game::Mm9DatVec3 &point,
    const Game::Mm9DatVec3 &minPoint,
    const Game::Mm9DatVec3 &maxPoint)
{
    return point.x >= minPoint.x && point.x <= maxPoint.x
        && point.y >= minPoint.y && point.y <= maxPoint.y
        && point.z >= minPoint.z && point.z <= maxPoint.z;
}

bool intersectMm9RayAabbDistance(
    const Game::Mm9DatVec3 &origin,
    const Game::Mm9DatVec3 &direction,
    const Game::Mm9DatVec3 &minPoint,
    const Game::Mm9DatVec3 &maxPoint,
    float &distance)
{
    float tMin = 0.0f;
    float tMax = std::numeric_limits<float>::max();

    const float originValues[3] = {origin.x, origin.y, origin.z};
    const float directionValues[3] = {direction.x, direction.y, direction.z};
    const float minValues[3] = {minPoint.x, minPoint.y, minPoint.z};
    const float maxValues[3] = {maxPoint.x, maxPoint.y, maxPoint.z};

    for (size_t axis = 0; axis < 3; ++axis)
    {
        if (std::fabs(directionValues[axis]) <= 0.00001f)
        {
            if (originValues[axis] < minValues[axis] || originValues[axis] > maxValues[axis])
            {
                return false;
            }

            continue;
        }

        const float inverseDirection = 1.0f / directionValues[axis];
        float t0 = (minValues[axis] - originValues[axis]) * inverseDirection;
        float t1 = (maxValues[axis] - originValues[axis]) * inverseDirection;

        if (t0 > t1)
        {
            std::swap(t0, t1);
        }

        tMin = std::max(tMin, t0);
        tMax = std::min(tMax, t1);

        if (tMin > tMax)
        {
            return false;
        }
    }

    distance = tMin;
    return true;
}

bool mm9DatMarkerHasLineOfSightForReport(
    const EditorMm9DatWorldSidecar &datWorld,
    const Game::Mm9DatVec3 &cameraPosition,
    const Game::Mm9DatVec3 &target)
{
    const Game::Mm9DatVec3 toTarget = mm9Subtract(target, cameraPosition);
    const float targetDistance = mm9Length(toTarget);

    if (targetDistance <= 1.0f)
    {
        return true;
    }

    const Game::Mm9DatVec3 direction = mm9Multiply(toTarget, 1.0f / targetDistance);
    constexpr float StartSlack = 8.0f;
    constexpr float EndSlack = 16.0f;
    constexpr float BoundsSlack = 4.0f;

    for (const EditorMm9DatWorldModelSummary &model : datWorld.worldModels)
    {
        if ((!model.roles.visible && !model.roles.terrain && !model.roles.movable)
            || model.roles.sky
            || model.roles.visBsp
            || model.roles.triggerOrVolume)
        {
            continue;
        }

        const Game::Mm9DatVec3 rawMinPoint = {
            model.boundsMinLt.x * Game::Mm9DatToOpenYammScale,
            model.boundsMinLt.z * Game::Mm9DatToOpenYammScale,
            model.boundsMinLt.y * Game::Mm9DatToOpenYammScale,
        };
        const Game::Mm9DatVec3 rawMaxPoint = {
            model.boundsMaxLt.x * Game::Mm9DatToOpenYammScale,
            model.boundsMaxLt.z * Game::Mm9DatToOpenYammScale,
            model.boundsMaxLt.y * Game::Mm9DatToOpenYammScale,
        };
        const Game::Mm9DatVec3 minPoint = {
            std::min(rawMinPoint.x, rawMaxPoint.x) - BoundsSlack,
            std::min(rawMinPoint.y, rawMaxPoint.y) - BoundsSlack,
            std::min(rawMinPoint.z, rawMaxPoint.z) - BoundsSlack,
        };
        const Game::Mm9DatVec3 maxPoint = {
            std::max(rawMinPoint.x, rawMaxPoint.x) + BoundsSlack,
            std::max(rawMinPoint.y, rawMaxPoint.y) + BoundsSlack,
            std::max(rawMinPoint.z, rawMaxPoint.z) + BoundsSlack,
        };

        if (mm9PointInsideAabb(target, minPoint, maxPoint))
        {
            continue;
        }

        float distance = 0.0f;

        if (!intersectMm9RayAabbDistance(cameraPosition, direction, minPoint, maxPoint, distance))
        {
            continue;
        }

        if (distance > StartSlack && distance < targetDistance - EndSlack)
        {
            return false;
        }
    }

    return true;
}

Mm9MechanismTargetMarkerSummary summarizeMm9MechanismTargetMarkers(
    const Game::Mm9EventsData &events,
    const EditorMm9DatWorldSidecar &datWorld,
    const Game::Mm9ObjectLayer &objectLayer,
    const Game::Mm9LightLayer &lightLayer,
    const Game::Mm9SoundLayer &soundLayer,
    const Game::Mm9SpawnLayer &spawnLayer,
    const Game::OutdoorSceneData &sceneData,
    const Game::Mm9DatCameraFrame &cameraFrame)
{
    Mm9MechanismTargetMarkerSummary summary = {};

    for (const Game::Mm9EventMechanism &mechanism : events.mechanisms)
    {
        const Game::Mm9EventBinding *pBinding =
            findMm9EventBindingForObject(events, mechanism.objectId);

        if (pBinding == nullptr)
        {
            continue;
        }

        const bool sourcePositioned =
            mechanism.sourceObjectIndex >= 0
            && mm9SourceObjectHasMarkerPosition(
                objectLayer,
                lightLayer,
                soundLayer,
                spawnLayer,
                sceneData,
                static_cast<size_t>(mechanism.sourceObjectIndex));
        bool hasTargetGizmo = false;

        if (sourcePositioned)
        {
            ++summary.gizmoCandidates;
            ++summary.circleGizmoCandidates;
        }

        for (const Game::Mm9EventBindingTarget &target : pBinding->targets)
        {
            if (target.targetKind != "odm_bmodel"
                || !target.bmodelIndex.has_value()
                || *target.bmodelIndex >= datWorld.worldModels.size())
            {
                continue;
            }

            ++summary.targetGroups;
            ++summary.candidates;
            summary.vertices += 24;

            if (sourcePositioned)
            {
                ++summary.sourceLinkedTargets;
                summary.vertices += 8;
            }

            Game::Mm9DatVec3 center = {};
            Game::Mm9DatVec3 halfExtents = {};
            if (mm9DatWorldModelBoundsForMarker(datWorld, *target.bmodelIndex, center, halfExtents))
            {
                ++summary.gizmoCandidates;
                ++summary.targetGizmoCandidates;
                hasTargetGizmo = true;

                if (cameraFrame.valid)
                {
                    ++summary.lineOfSightCheckedCandidates;

                    if (!mm9DatMarkerHasLineOfSightForReport(datWorld, cameraFrame.position, center))
                    {
                        ++summary.lineOfSightBlockedCandidates;
                    }
                }
            }

            Game::Mm9DatMechanismPreviewMotion motion = {};
            motion.progress = 1.0f;
            motion.hasLinearMotion =
                mechanism.linear.hasMoveDir
                && mechanism.linear.hasMoveDist
                && std::fabs(mechanism.linear.moveDistLt) > 0.0001f
                && mm9Vec3FromFloatVector(mechanism.linear.moveDirLt, motion.moveDirLt);
            motion.hasRotationMotion =
                mechanism.rotation.hasRotationPoint
                && mechanism.rotation.hasRotationAngles
                && mm9Vec3FromFloatVector(mechanism.rotation.rotationPointLt, motion.rotationPointLt)
                && mm9Vec3FromFloatVector(mechanism.rotation.rotationAnglesDeg, motion.rotationAnglesDeg);

            if (motion.hasLinearMotion || motion.hasRotationMotion)
            {
                ++summary.motionPathMarkers;
            }
        }

        if (!sourcePositioned && hasTargetGizmo)
        {
            ++summary.gizmoCandidates;
            ++summary.circleGizmoCandidates;
        }
    }

    return summary;
}

Game::Mm9DatVec3 normalizeMm9Vector(const Game::Mm9DatVec3 &value)
{
    const float length = mm9Length(value);

    if (length <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {value.x / length, value.y / length, value.z / length};
}

Mm9ModelInstanceCameraFrameSummary summarizeMm9ModelInstanceCameraFrame(
    const Game::OutdoorSceneData &sceneData,
    const Game::Mm9DatCameraFrame &cameraFrame,
    float verticalFovDegrees,
    float aspectRatio)
{
    Mm9ModelInstanceCameraFrameSummary summary = {};
    summary.total = sceneData.modelInstances.size();

    if (!cameraFrame.valid || verticalFovDegrees <= 1.0f || aspectRatio <= 0.1f)
    {
        return summary;
    }

    constexpr float Pi = 3.14159265358979323846f;
    const float halfFovRadians = (verticalFovDegrees * 0.5f) * Pi / 180.0f;
    const float tangent = std::tan(halfFovRadians);

    if (tangent <= 0.0001f)
    {
        return summary;
    }

    const Game::Mm9DatVec3 forward =
        normalizeMm9Vector(mm9Subtract(cameraFrame.target, cameraFrame.position));

    if (mm9Length(forward) <= 0.0001f)
    {
        return summary;
    }

    const Game::Mm9DatVec3 worldUp = {0.0f, 0.0f, 1.0f};
    Game::Mm9DatVec3 right = normalizeMm9Vector(mm9Cross(forward, worldUp));

    if (mm9Length(right) <= 0.0001f)
    {
        right = {1.0f, 0.0f, 0.0f};
    }

    const Game::Mm9DatVec3 cameraUp = normalizeMm9Vector(mm9Cross(right, forward));

    for (const Game::OutdoorSceneModelInstance &modelInstance : sceneData.modelInstances)
    {
        const float radius = 128.0f
            * std::max({modelInstance.scale[0], modelInstance.scale[1], modelInstance.scale[2], 1.0f});
        const Game::Mm9DatVec3 center = {
            static_cast<float>(modelInstance.x),
            static_cast<float>(modelInstance.y),
            static_cast<float>(modelInstance.z) + radius
        };
        const Game::Mm9DatVec3 cameraToCenter = mm9Subtract(center, cameraFrame.position);
        const float depth = mm9Dot(cameraToCenter, forward);

        if (depth + radius <= 0.0f)
        {
            continue;
        }

        ++summary.inFront;

        if (depth + radius < cameraFrame.nearPlane || depth - radius > cameraFrame.farPlane)
        {
            continue;
        }

        ++summary.inDepthRange;

        const float verticalExtent = std::max(depth, 1.0f) * tangent;
        const float horizontalExtent = verticalExtent * aspectRatio;
        const float x = mm9Dot(cameraToCenter, right);
        const float y = mm9Dot(cameraToCenter, cameraUp);

        if (std::fabs(x) <= horizontalExtent + radius && std::fabs(y) <= verticalExtent + radius)
        {
            ++summary.inView;
        }
    }

    return summary;
}

std::vector<Game::Mm9DatModelRenderRole> mm9ModelRenderRolesFromSidecar(
    const EditorMm9DatWorldSidecar &sidecar);

bool writeMm9DatLevelValidationReport(
    const std::filesystem::path &worldRoot,
    const std::filesystem::path &levelPhysicalPath,
    const EditorDocument &document,
    const Mm9ModelInstanceAssetResolutionSummary &modelInstanceSummary,
    const Mm9DatViewportRenderabilitySummary &viewportSummary,
    const Mm9MechanismPreviewValidationSummary &mechanismPreviewSummary,
    size_t selectedTriangleIndex,
    bool sourceIntegritySnapshotVerified,
    size_t sourceIntegritySnapshotFileCount,
    std::filesystem::path &reportPath,
    std::string &errorMessage)
{
    const EditorMm9DatLevelMetadata &metadata = document.mm9DatLevelMetadata();
    const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
    const Game::Mm9DatRenderMesh &datRenderMesh = document.mm9DatRenderMesh();
    const Game::Mm9DatRenderFilterResult nativeFilters =
        Game::classifyMm9DatRenderMeshFilters(
            datRenderMesh,
            mm9ModelRenderRolesFromSidecar(sidecars.datWorld),
            sidecars.datWorld.userPortals.size());
    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();
    const Game::Mm9ObjectLayer &objectLayer = document.mm9ObjectLayer();
    const Game::Mm9LightLayer &lightLayer = document.mm9LightLayer();
    const Game::Mm9SoundLayer &soundLayer = document.mm9SoundLayer();
    const Game::Mm9SpawnLayer &spawnLayer = document.mm9SpawnLayer();
    const size_t worldModelOverlayVertices = countMm9WorldModelOverlayVertices(sidecars.datWorld);
    const size_t worldModelOverlayPickCandidates = countMm9WorldModelOverlayPickCandidates(sidecars.datWorld);
    const Mm9SelectedDatOverlaySummary selectedDatOverlaySummary =
        summarizeMm9SelectedDatOverlay(datRenderMesh, selectedTriangleIndex);
    const size_t objectOverlayVertices = countMm9ObjectOverlayVertices(objectLayer);
    const size_t objectOverlayPickCandidates =
        countMm9ObjectOverlayPickCandidates(objectLayer, sidecars.rawObjects);
    const Mm9SourceMarkerOverlaySummary sourceMarkerOverlaySummary =
        summarizeMm9SourceMarkerOverlayVertices(lightLayer, soundLayer, spawnLayer);
    const Mm9AssetIssueMarkerSummary assetIssueMarkerSummary =
        summarizeMm9AssetIssueMarkers(
            document.mm9RawObjectAssetReferenceStatuses(),
            objectLayer,
            lightLayer,
            soundLayer,
            spawnLayer,
            sceneData,
            sidecars.rawObjects);
    const Game::Mm9DatCameraFrame reportCameraFrame = Game::frameMm9DatRenderMeshCamera(datRenderMesh);
    const Mm9MechanismTargetMarkerSummary mechanismTargetMarkerSummary =
        summarizeMm9MechanismTargetMarkers(
            sidecars.events,
            sidecars.datWorld,
            objectLayer,
            lightLayer,
            soundLayer,
            spawnLayer,
            sceneData,
            reportCameraFrame);
    const Mm9ModelInstanceCameraFrameSummary modelInstanceCameraFrameSummary =
        summarizeMm9ModelInstanceCameraFrame(sceneData, reportCameraFrame, 60.0f, 1920.0f / 1200.0f);
    const Mm9MechanismValidationSummary mechanismSummary =
        summarizeMm9Mechanisms(sidecars.events, sidecars.datWorld);
    const EditorMm9AssetDependencySummary &assetSummary = document.mm9AssetDependencySummary();
    const std::vector<EditorMm9MaterialTextureStatus> &textureStatuses =
        document.mm9MaterialTextureStatuses();
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &rawObjectStatuses =
        document.mm9RawObjectAssetReferenceStatuses();
    const std::vector<EditorMm9DocumentPathStatus> &pathStatuses = document.mm9DocumentPathStatuses();

    std::vector<const EditorMm9RawObjectAssetReferenceStatus *> unresolvedRequiredRawObjects;
    std::vector<const EditorMm9RawObjectAssetReferenceStatus *> unresolvedOptionalRawObjects;
    std::vector<const EditorMm9MaterialTextureStatus *> invalidMaterialTextures;
    std::vector<const EditorMm9MaterialTextureStatus *> staleMaterialCaches;
    std::vector<const EditorMm9MaterialTextureStatus *> nondeterministicMaterialCaches;
    std::vector<const EditorMm9DocumentPathStatus *> authoredPathStatuses;
    std::vector<const EditorMm9DocumentPathStatus *> authoredOverridePathStatuses;
    std::vector<const EditorMm9DocumentPathStatus *> generatedPathStatuses;
    std::vector<const EditorMm9DocumentPathStatus *> sourceReadOnlyPathStatuses;
    std::vector<const EditorMm9DocumentPathStatus *> compatibilityPathStatuses;
    size_t missingDocumentPathCount = 0;
    size_t missingRequiredDocumentPathCount = 0;
    size_t optionalRawObjectAssetReferenceCount = 0;
    size_t requiredRawObjectAssetReferenceCount = 0;
    size_t resolvedTextureCount = 0;
    size_t ambiguousTextureCount = 0;
    size_t sourceDtxPathCount = 0;
    size_t defaultHelperMaterialCount = 0;
    size_t placeholderMissingSourceMaterialCount = 0;
    size_t loadedDtxHeaderCount = 0;
    size_t matchedDtxHeaderCount = 0;
    size_t dtxUserFlagRecordCount = 0;
    size_t dtxExtraByteRecordCount = 0;
    size_t dtxMipPayloadCount = 0;
    size_t dtxDecodedPreviewMipCount = 0;
    size_t dtxSectionMetadataCount = 0;
    size_t dtxSectionPayloadAvailableCount = 0;
    size_t dtxCommandStringCount = 0;
    size_t decodedCacheDeterminismCheckedCount = 0;
    size_t decodedCacheSourceDecodedCount = 0;
    size_t decodedCacheImageDecodedCount = 0;
    size_t decodedCacheMatchCount = 0;
    size_t spriteMaterialCount = 0;
    size_t resolvedSpriteMaterialCount = 0;
    size_t spriteFrameTextureCount = 0;
    size_t resolvedSpriteFrameTextureCount = 0;
    size_t unresolvedSpriteFrameTextureCount = 0;
    size_t ambiguousSpriteFrameTextureCount = 0;
    size_t invalidSurfaceTextureRefs = 0;
    size_t invalidPolySurfaceRefs = 0;
    size_t invalidPolyPlaneRefs = 0;
    size_t invalidPolyVertexRefs = 0;
    size_t invalidNodePolyRefs = 0;
    size_t invalidRootNodeRefs = 0;
    size_t worldModelsWithUnknownValues = 0;
    size_t userPortalsWithRawUnknowns = 0;
    size_t scriptIncludes = 0;
    size_t scriptLabels = 0;
    size_t scriptRegisteredTriggers = 0;
    size_t scriptTriggerEdges = 0;
    size_t scriptMovementCommands = 0;
    size_t scriptUnknownCommands = 0;
    size_t scriptCommandCount = 0;
    size_t unresolvedEventWarnings = 0;
    size_t unresolvedEventErrors = 0;
    size_t unresolvedEventRotationCandidates = 0;
    size_t unresolvedEventPositionCandidates = 0;
    const size_t staticRenderLightCount = Game::buildMm9StaticRenderLights(lightLayer).size();
    const std::vector<std::string> datWorldReferenceIssues =
        validateMm9DatWorldSidecarReferences(sidecars.datWorld);
    const std::vector<std::string> rawObjectSidecarIssues =
        validateMm9RawObjectsSidecarReferences(sidecars.rawObjects);
    const std::vector<std::string> &levelLoadDiagnostics = document.mm9DatLevelLoadDiagnostics();
    const std::vector<std::string> &sourceManifestDiagnostics = document.mm9SourceAssetManifestDiagnostics();
    const std::vector<EditorMm9SourceAssetFamilyStatus> &sourceFamilyStatuses =
        document.mm9SourceAssetFamilyStatuses();
    size_t sourceFamilyDeclaredCount = 0;
    size_t sourceFamilyRequiredCount = 0;
    size_t sourceFamilyExpectedFileCount = 0;
    size_t sourceFamilyActualFileCount = 0;
    size_t sourceFamilyCountDriftCount = 0;
    size_t sourceFamilyMissingDirectoryCount = 0;
    size_t sourceDatHashDiagnosticCount = 0;
    const EditorMm9ScriptIncludeResolutionSummary scriptIncludeSummary =
        summarizeMm9EventScriptIncludeResolution(levelPhysicalPath, sidecars.events);

    for (const OpenYAMM::Game::Mm9EventScript &script : sidecars.events.scripts)
    {
        scriptIncludes += script.includes.size();
        scriptLabels += script.labels.size();
        scriptRegisteredTriggers += script.registeredTriggers.size();
        scriptTriggerEdges += script.triggerEdges.size();
        scriptMovementCommands += script.movementCommands.size();
        scriptUnknownCommands += script.unknownCommands.size();
        scriptCommandCount += script.commandCount;
    }

    for (const OpenYAMM::Game::Mm9EventUnresolved &entry : sidecars.events.unresolved)
    {
        const std::string severity = lowerAsciiCopy(entry.severity);

        if (severity == "error")
        {
            ++unresolvedEventErrors;
        }
        else if (severity == "warning")
        {
            ++unresolvedEventWarnings;
        }

        unresolvedEventRotationCandidates += entry.nearestMovableWorldModelsByRotationPoint.size();
        unresolvedEventPositionCandidates += entry.nearestMovableWorldModelsByPosition.size();
    }

    for (const EditorMm9RawObjectAssetReferenceStatus &status : rawObjectStatuses)
    {
        if (status.required)
        {
            ++requiredRawObjectAssetReferenceCount;
        }
        else
        {
            ++optionalRawObjectAssetReferenceCount;
        }

        if (!status.resolved || status.ambiguous)
        {
            if (status.required)
            {
                unresolvedRequiredRawObjects.push_back(&status);
            }
            else
            {
                unresolvedOptionalRawObjects.push_back(&status);
            }
        }
    }

    for (const EditorMm9DocumentPathStatus &status : pathStatuses)
    {
        if (!status.exists)
        {
            ++missingDocumentPathCount;

            if (isMm9DocumentPathRequired(status))
            {
                ++missingRequiredDocumentPathCount;
            }
        }

        if (status.authored)
        {
            authoredPathStatuses.push_back(&status);
        }

        if (status.role == "authored_override")
        {
            authoredOverridePathStatuses.push_back(&status);
        }

        if (status.generated)
        {
            generatedPathStatuses.push_back(&status);
        }

        if (status.sourceReadOnly)
        {
            sourceReadOnlyPathStatuses.push_back(&status);
        }

        if (status.compatibilityDerived)
        {
            compatibilityPathStatuses.push_back(&status);
        }
    }

    for (const EditorMm9MaterialTextureStatus &status : textureStatuses)
    {
        if (status.defaultHelperMaterial)
        {
            ++defaultHelperMaterialCount;
        }

        if (status.placeholderMissingSource)
        {
            ++placeholderMissingSourceMaterialCount;
        }

        if (status.sourceDtxResolved)
        {
            ++resolvedTextureCount;
        }

        if (status.sourceDtxResolved && status.sourcePathExists)
        {
            ++sourceDtxPathCount;
        }

        if (status.sourceDtxAmbiguous)
        {
            ++ambiguousTextureCount;
        }

        if (status.dtxHeaderLoaded)
        {
            ++loadedDtxHeaderCount;
        }

        if (status.dtxHeaderMatchesSidecar)
        {
            ++matchedDtxHeaderCount;
        }

        if (status.dtxHeader)
        {
            ++dtxUserFlagRecordCount;
            dtxExtraByteRecordCount += status.dtxHeader->extraBytes.size();
            dtxMipPayloadCount += status.dtxHeader->mips.size();
            dtxSectionMetadataCount += status.dtxHeader->sections.size();

            if (!status.dtxHeader->commandString.empty())
            {
                ++dtxCommandStringCount;
            }

            for (const EditorMm9DtxMipLevel &mip : status.dtxHeader->mips)
            {
                if (mip.decodedPreviewAvailable)
                {
                    ++dtxDecodedPreviewMipCount;
                }
            }

            for (const EditorMm9DtxSection &section : status.dtxHeader->sections)
            {
                if (section.payloadAvailable)
                {
                    ++dtxSectionPayloadAvailableCount;
                }
            }
        }

        const bool missingRequiredMaterialAliasField =
            status.materialAliasEntry
            && (!status.aliasFieldPresent
                || status.alias.empty()
                || !status.sourceTextureFieldPresent
                || status.sourceTexture.empty()
                || !status.emittedBitmapFieldPresent
                || status.emittedBitmap.empty()
                || !status.emittedBitmapModeFieldPresent
                || status.emittedBitmapMode.empty());
        const bool requiredSource = status.datReferenceCount > 0 || !status.sourceTexture.empty();
        bool invalid =
            !status.defaultHelperMaterial
            && (missingRequiredMaterialAliasField
                || (requiredSource
                    && !status.placeholderMissingSource
                    && (!status.sourceDtxResolved
                        || status.sourceDtxAmbiguous
                        || !status.sourcePathExists
                        || !status.dtxHeaderLoaded
                        || !status.dtxHeaderMatchesSidecar)));

        if (status.sourceAssetFamily == "sprites")
        {
            ++spriteMaterialCount;
            spriteFrameTextureCount += status.spriteFrameTextureCount;
            resolvedSpriteFrameTextureCount += status.resolvedSpriteFrameTextureCount;
            unresolvedSpriteFrameTextureCount += status.unresolvedSpriteFrameTextureCount;
            ambiguousSpriteFrameTextureCount += status.ambiguousSpriteFrameTextureCount;

            if (status.sourceSpriteResolved
                && status.sourceSpritePathExists
                && status.sourceSpriteParsed
                && status.spriteFrameTextureCount > 0
                && status.unresolvedSpriteFrameTextureCount == 0
                && status.ambiguousSpriteFrameTextureCount == 0)
            {
                ++resolvedSpriteMaterialCount;
            }

            invalid =
                !status.defaultHelperMaterial
                && (missingRequiredMaterialAliasField
                    || (requiredSource
                        && (!status.sourceSpriteResolved
                            || status.sourceSpriteAmbiguous
                            || !status.sourceSpritePathExists
                            || !status.sourceSpriteParsed
                            || status.spriteFrameTextureCount == 0
                            || status.unresolvedSpriteFrameTextureCount != 0
                            || status.ambiguousSpriteFrameTextureCount != 0)));
        }

        if (invalid)
        {
            invalidMaterialTextures.push_back(&status);
        }

        if (status.cacheOlderThanSource)
        {
            staleMaterialCaches.push_back(&status);
        }

        if (status.cacheDeterminismChecked)
        {
            ++decodedCacheDeterminismCheckedCount;

            if (status.sourceDtxDecodedForCache)
            {
                ++decodedCacheSourceDecodedCount;
            }

            if (status.cacheImageDecoded)
            {
                ++decodedCacheImageDecodedCount;
            }

            if (status.cacheMatchesDecodedSource)
            {
                ++decodedCacheMatchCount;
            }
            else
            {
                nondeterministicMaterialCaches.push_back(&status);
            }
        }
    }

    for (const std::string &diagnostic : levelLoadDiagnostics)
    {
        if (diagnostic.find("source DAT hash") != std::string::npos)
        {
            ++sourceDatHashDiagnosticCount;
        }
    }

    for (const EditorMm9SourceAssetFamilyStatus &status : sourceFamilyStatuses)
    {
        if (status.declared)
        {
            ++sourceFamilyDeclaredCount;
        }

        if (status.required)
        {
            ++sourceFamilyRequiredCount;
        }

        sourceFamilyExpectedFileCount += status.expectedFileCount;
        sourceFamilyActualFileCount += status.actualFileCount;

        if (status.declared && !status.packageDirectoryExists)
        {
            ++sourceFamilyMissingDirectoryCount;
        }

        if (status.declared && status.expectedFileCount != status.actualFileCount)
        {
            ++sourceFamilyCountDriftCount;
        }
    }

    for (const EditorMm9DatWorldModelSummary &model : sidecars.datWorld.worldModels)
    {
        invalidSurfaceTextureRefs += model.referenceValidation.invalidSurfaceTextureRefs;
        invalidPolySurfaceRefs += model.referenceValidation.invalidPolySurfaceRefs;
        invalidPolyPlaneRefs += model.referenceValidation.invalidPolyPlaneRefs;
        invalidPolyVertexRefs += model.referenceValidation.invalidPolyVertexRefs;
        invalidNodePolyRefs += model.referenceValidation.invalidNodePolyRefs;
        invalidRootNodeRefs += model.referenceValidation.invalidRootNodeRefs;

        if (model.unknownValues.worldBspUnknownValue != 0
            || model.unknownValues.worldBspUnknownValue2 != 0
            || model.unknownValues.worldBspUnknownValue3 != 0)
        {
            ++worldModelsWithUnknownValues;
        }
    }

    for (const EditorMm9DatUserPortalSummary &portal : sidecars.datWorld.userPortals)
    {
        if (portal.rawUnknowns.unknownInt1 != 0 || portal.rawUnknowns.unknownShort != 0)
        {
            ++userPortalsWithRawUnknowns;
        }
    }

    const bool clean =
        unresolvedRequiredRawObjects.empty()
        && missingRequiredDocumentPathCount == 0
        && levelLoadDiagnostics.empty()
        && sourceManifestDiagnostics.empty()
        && datWorldReferenceIssues.empty()
        && rawObjectSidecarIssues.empty()
        && invalidMaterialTextures.empty()
        && nondeterministicMaterialCaches.empty()
        && ambiguousTextureCount == 0
        && modelInstanceSummary.missingAssets == 0
        && modelInstanceSummary.missingDrawableGeometry == 0
        && modelInstanceSummary.actorVariantUnresolved == 0
        && modelInstanceSummary.actorVariantGameplayIdentityRows == modelInstanceSummary.actorVariantResolved
        && modelInstanceSummary.actorVariantUnresolvedFootSounds == 0
        && modelInstanceSummary.actorVariantResolvedFootSounds == modelInstanceSummary.actorVariantFootSoundFields
        && modelInstanceSummary.actorVariantUnresolvedSourceSoundReferences == 0
        && modelInstanceSummary.actorVariantResolvedSourceSoundReferences
            == modelInstanceSummary.actorVariantSourceSoundReferences
        && modelInstanceSummary.actorVariantUnresolvedSourceVoiceReferences == 0
        && modelInstanceSummary.actorVariantResolvedSourceVoiceReferences
            == modelInstanceSummary.actorVariantSourceVoiceReferences
        && viewportSummary.nativeRenderableTriangles != 0
        && viewportSummary.nativeTexturedTriangles != 0
        && assetSummary.requiredUnresolved == 0
        && assetSummary.requiredAmbiguous == 0
        && mechanismSummary.unresolvedRequiredTargets == 0
        && mechanismSummary.worldModelTargetsMissingModel == 0
        && mechanismSummary.worldModelTargetsMissingPolygonGroup == 0
        && mechanismSummary.worldModelTargetsMismatchedPolygonGroup == 0
        && mechanismSummary.inertPreviewMechanisms.size() == mechanismSummary.inertMechanisms
        && (sidecars.datWorld.worldModels.empty() || worldModelOverlayVertices != 0)
        && (worldModelOverlayVertices == 0 || worldModelOverlayPickCandidates != 0)
        && (datRenderMesh.triangles.empty() || selectedDatOverlaySummary.polygonVertices != 0)
        && (datRenderMesh.triangles.empty() || selectedDatOverlaySummary.surfaceVertices != 0)
        && (objectLayer.boundsEvidenceObjectCount == 0 || objectOverlayVertices != 0)
        && (objectOverlayVertices == 0 || objectOverlayPickCandidates != 0)
        && (lightLayer.lights.empty() || sourceMarkerOverlaySummary.lightVertices != 0)
        && (soundLayer.objects.empty() || sourceMarkerOverlaySummary.soundVertices != 0)
        && (spawnLayer.objects.empty() || sourceMarkerOverlaySummary.spawnVertices != 0)
        && (sceneData.modelInstances.empty() || modelInstanceCameraFrameSummary.inView != 0)
        && (mechanismPreviewSummary.candidates == 0 || mechanismPreviewSummary.changedBounds != 0);

    reportPath = worldRoot
        / "import"
        / "validation"
        / (metadata.mapId + ".asset_validation.yml");

    std::error_code errorCode;
    std::filesystem::create_directories(reportPath.parent_path(), errorCode);

    if (errorCode)
    {
        errorMessage = "could not create validation report directory "
            + reportPath.parent_path().generic_string()
            + ": "
            + errorCode.message();
        return false;
    }

    std::ofstream stream(reportPath);

    if (!stream)
    {
        errorMessage = "could not write validation report " + reportPath.generic_string();
        return false;
    }

    writeYamlScalar(stream, "", "format_version", static_cast<size_t>(1));
    writeYamlScalar(stream, "", "kind", "mm9_asset_validation_report");
    writeYamlScalar(stream, "", "scope", "active_two_map_slice");
    writeYamlScalar(stream, "", "map_id", metadata.mapId);
    writeYamlScalar(stream, "", "display_name", metadata.displayName);
    writeYamlScalar(stream, "", "level_file", levelPhysicalPath.filename().generic_string());
    writeYamlScalar(stream, "", "source_dat", metadata.source.dat);
    writeYamlScalar(stream, "", "clean", clean);

    stream << "source_integrity:\n";
    writeYamlScalar(stream, "  ", "level_load_diagnostics", levelLoadDiagnostics.size());
    writeYamlScalar(stream, "  ", "source_mutation_snapshot_verified", sourceIntegritySnapshotVerified);
    writeYamlScalar(stream, "  ", "source_mutation_snapshot_files", sourceIntegritySnapshotFileCount);
    writeYamlScalar(stream, "  ", "source_dat_hash_expected", metadata.source.contentHash);
    writeYamlScalar(stream, "  ", "source_dat_hash_diagnostics", sourceDatHashDiagnosticCount);
    writeYamlScalar(
        stream,
        "  ",
        "source_dat_hash_verified",
        !metadata.source.contentHash.empty() && sourceDatHashDiagnosticCount == 0);
    writeYamlScalar(stream, "  ", "source_manifest_diagnostics", sourceManifestDiagnostics.size());
    writeYamlScalar(stream, "  ", "source_manifest_families_declared", sourceFamilyDeclaredCount);
    writeYamlScalar(stream, "  ", "source_manifest_families_required", sourceFamilyRequiredCount);
    writeYamlScalar(stream, "  ", "source_manifest_expected_files", sourceFamilyExpectedFileCount);
    writeYamlScalar(stream, "  ", "source_manifest_actual_files", sourceFamilyActualFileCount);
    writeYamlScalar(stream, "  ", "source_manifest_count_drift_families", sourceFamilyCountDriftCount);
    writeYamlScalar(stream, "  ", "source_manifest_missing_directories", sourceFamilyMissingDirectoryCount);
    if (levelLoadDiagnostics.empty())
    {
        stream << "  level_load_issue_details: []\n";
    }
    else
    {
        stream << "  level_load_issue_details:\n";

        for (const std::string &diagnostic : levelLoadDiagnostics)
        {
            stream << "    - ";
            writeYamlQuoted(stream, diagnostic);
            stream << '\n';
        }
    }
    if (sourceManifestDiagnostics.empty())
    {
        stream << "  source_manifest_issue_details: []\n";
    }
    else
    {
        stream << "  source_manifest_issue_details:\n";

        for (const std::string &diagnostic : sourceManifestDiagnostics)
        {
            stream << "    - ";
            writeYamlQuoted(stream, diagnostic);
            stream << '\n';
        }
    }

    const auto writeDocumentPathEntry =
        [&stream](const EditorMm9DocumentPathStatus &status)
    {
        stream << "    - label: ";
        writeYamlQuoted(stream, status.label);
        stream << '\n';
        writeYamlScalar(stream, "      ", "role", status.role);
        writeYamlScalar(stream, "      ", "relative_path", status.relativePath);
        writeYamlScalar(stream, "      ", "resolved_path", status.resolvedPath);
        writeYamlScalar(stream, "      ", "exists", status.exists);
    };

    stream << "document_paths:\n";
    writeYamlScalar(stream, "  ", "total", pathStatuses.size());
    writeYamlScalar(stream, "  ", "missing", missingDocumentPathCount);
    writeYamlScalar(stream, "  ", "missing_required", missingRequiredDocumentPathCount);
    writeYamlScalar(stream, "  ", "source_read_only", sourceReadOnlyPathStatuses.size());
    writeYamlScalar(stream, "  ", "generated", generatedPathStatuses.size());
    writeYamlScalar(stream, "  ", "authored", authoredPathStatuses.size());
    writeYamlScalar(stream, "  ", "authored_overrides", authoredOverridePathStatuses.size());
    writeYamlScalar(stream, "  ", "compatibility_derived", compatibilityPathStatuses.size());
    if (sourceReadOnlyPathStatuses.empty())
    {
        stream << "  source_read_only_files: []\n";
    }
    else
    {
        stream << "  source_read_only_files:\n";

        for (const EditorMm9DocumentPathStatus *pStatus : sourceReadOnlyPathStatuses)
        {
            writeDocumentPathEntry(*pStatus);
        }
    }
    if (authoredPathStatuses.empty())
    {
        stream << "  authored_files: []\n";
    }
    else
    {
        stream << "  authored_files:\n";

        for (const EditorMm9DocumentPathStatus *pStatus : authoredPathStatuses)
        {
            writeDocumentPathEntry(*pStatus);
        }
    }
    if (authoredOverridePathStatuses.empty())
    {
        stream << "  authored_overrides: []\n";
    }
    else
    {
        stream << "  authored_overrides:\n";

        for (const EditorMm9DocumentPathStatus *pStatus : authoredOverridePathStatuses)
        {
            writeDocumentPathEntry(*pStatus);
        }
    }
    if (generatedPathStatuses.empty())
    {
        stream << "  generated_files: []\n";
    }
    else
    {
        stream << "  generated_files:\n";

        for (const EditorMm9DocumentPathStatus *pStatus : generatedPathStatuses)
        {
            writeDocumentPathEntry(*pStatus);
        }
    }
    if (compatibilityPathStatuses.empty())
    {
        stream << "  compatibility_derived_files: []\n";
    }
    else
    {
        stream << "  compatibility_derived_files:\n";

        for (const EditorMm9DocumentPathStatus *pStatus : compatibilityPathStatuses)
        {
            writeDocumentPathEntry(*pStatus);
        }
    }

    stream << "summary:\n";
    writeYamlScalar(stream, "  ", "world_models", sidecars.datWorld.worldModels.size());
    writeYamlScalar(stream, "  ", "leaves", sidecars.datWorld.totals.leafCount);
    writeYamlScalar(stream, "  ", "user_portals", sidecars.datWorld.totals.userPortalCount);
    writeYamlScalar(stream, "  ", "dat_world_reference_issues", datWorldReferenceIssues.size());
    writeYamlScalar(
        stream,
        "  ",
        "dat_world_invalid_leaf_references",
        sidecars.datWorld.totals.invalidLeafReferenceCount + sidecars.datWorld.leafReferences.invalidRefs);
    writeYamlScalar(stream, "  ", "dat_world_invalid_surface_texture_refs", invalidSurfaceTextureRefs);
    writeYamlScalar(stream, "  ", "dat_world_invalid_poly_surface_refs", invalidPolySurfaceRefs);
    writeYamlScalar(stream, "  ", "dat_world_invalid_poly_plane_refs", invalidPolyPlaneRefs);
    writeYamlScalar(stream, "  ", "dat_world_invalid_poly_vertex_refs", invalidPolyVertexRefs);
    writeYamlScalar(stream, "  ", "dat_world_invalid_node_poly_refs", invalidNodePolyRefs);
    writeYamlScalar(stream, "  ", "dat_world_invalid_root_node_refs", invalidRootNodeRefs);
    writeYamlScalar(stream, "  ", "dat_world_models_with_unknown_values", worldModelsWithUnknownValues);
    writeYamlScalar(stream, "  ", "dat_world_user_portals_with_raw_unknowns", userPortalsWithRawUnknowns);
    writeYamlScalar(stream, "  ", "native_mesh_triangles", datRenderMesh.triangles.size());
    writeYamlScalar(stream, "  ", "native_mesh_source_polies", datRenderMesh.sourcePolyCount);
    writeYamlScalar(stream, "  ", "viewport_native_renderable_triangles", viewportSummary.nativeRenderableTriangles);
    writeYamlScalar(
        stream,
        "  ",
        "viewport_native_renderable_physics_triangles",
        viewportSummary.nativeRenderablePhysicsTriangles);
    writeYamlScalar(stream, "  ", "viewport_native_textured_triangles", viewportSummary.nativeTexturedTriangles);
    writeYamlScalar(
        stream,
        "  ",
        "viewport_native_missing_material_triangles",
        viewportSummary.nativeMissingMaterialTriangles);
    writeYamlScalar(
        stream,
        "  ",
        "viewport_native_placeholder_material_triangles",
        viewportSummary.nativePlaceholderMaterialTriangles);
    writeYamlScalar(
        stream,
        "  ",
        "viewport_native_unresolved_material_triangles",
        viewportSummary.nativeUnresolvedMaterialTriangles);
    writeYamlScalar(stream, "  ", "native_filter_visual", nativeFilters.summary.visualTriangles);
    writeYamlScalar(stream, "  ", "native_filter_invisible", nativeFilters.summary.invisibleTriangles);
    writeYamlScalar(stream, "  ", "native_filter_water", nativeFilters.summary.waterTriangles);
    writeYamlScalar(stream, "  ", "native_filter_visible_water", nativeFilters.summary.visibleWaterTriangles);
    writeYamlScalar(stream, "  ", "native_filter_water_volume", nativeFilters.summary.waterVolumeTriangles);
    writeYamlScalar(stream, "  ", "native_filter_rail", nativeFilters.summary.railTriangles);
    writeYamlScalar(stream, "  ", "native_filter_helper", nativeFilters.summary.helperTriangles);
    writeYamlScalar(stream, "  ", "native_filter_physics", nativeFilters.summary.physicsTriangles);
    writeYamlScalar(stream, "  ", "native_filter_visibility", nativeFilters.summary.visibilityTriangles);
    writeYamlScalar(stream, "  ", "native_filter_portals", nativeFilters.summary.portalOverlays);
    writeYamlScalar(stream, "  ", "world_model_overlay_vertices", worldModelOverlayVertices);
    writeYamlScalar(stream, "  ", "world_model_overlay_pick_candidates", worldModelOverlayPickCandidates);
    writeYamlScalar(stream, "  ", "selected_polygon_overlay_vertices", selectedDatOverlaySummary.polygonVertices);
    writeYamlScalar(stream, "  ", "selected_surface_overlay_vertices", selectedDatOverlaySummary.surfaceVertices);
    writeYamlScalar(
        stream,
        "  ",
        "viewport_model_instance_drawable_geometry",
        viewportSummary.modelInstanceDrawableGeometry);
    writeYamlScalar(
        stream,
        "  ",
        "viewport_model_instance_decoded_skin_textures",
        viewportSummary.modelInstanceDecodedSkinTextures);
    writeYamlScalar(stream, "  ", "script_includes", scriptIncludes);
    writeYamlScalar(stream, "  ", "script_labels", scriptLabels);
    writeYamlScalar(stream, "  ", "script_include_references", scriptIncludeSummary.references);
    writeYamlScalar(stream, "  ", "script_resolved_includes", scriptIncludeSummary.resolved);
    writeYamlScalar(stream, "  ", "script_unresolved_includes", scriptIncludeSummary.unresolved);
    writeYamlScalar(stream, "  ", "script_ambiguous_includes", scriptIncludeSummary.ambiguous);
    writeYamlScalar(stream, "  ", "script_registered_triggers", scriptRegisteredTriggers);
    writeYamlScalar(stream, "  ", "script_trigger_edges", scriptTriggerEdges);
    writeYamlScalar(stream, "  ", "script_movement_commands", scriptMovementCommands);
    writeYamlScalar(stream, "  ", "script_unknown_commands", scriptUnknownCommands);
    writeYamlScalar(stream, "  ", "script_command_count", scriptCommandCount);
    writeYamlScalar(stream, "  ", "unresolved_events", sidecars.events.unresolved.size());
    writeYamlScalar(stream, "  ", "unresolved_event_warnings", unresolvedEventWarnings);
    writeYamlScalar(stream, "  ", "unresolved_event_errors", unresolvedEventErrors);
    writeYamlScalar(stream, "  ", "unresolved_event_rotation_candidates", unresolvedEventRotationCandidates);
    writeYamlScalar(stream, "  ", "unresolved_event_position_candidates", unresolvedEventPositionCandidates);
    writeYamlScalar(stream, "  ", "raw_objects", sidecars.rawObjects.objects.size());
    writeYamlScalar(stream, "  ", "raw_object_sidecar_issues", rawObjectSidecarIssues.size());
    writeYamlScalar(stream, "  ", "object_source_transforms", objectLayer.positionedObjectCount);
    writeYamlScalar(stream, "  ", "object_bounds_evidence", objectLayer.boundsEvidenceObjectCount);
    writeYamlScalar(stream, "  ", "object_trigger_volumes", objectLayer.triggerVolumeCount);
    writeYamlScalar(stream, "  ", "object_overlay_vertices", objectOverlayVertices);
    writeYamlScalar(stream, "  ", "object_overlay_pick_candidates", objectOverlayPickCandidates);
    writeYamlScalar(stream, "  ", "light_objects", lightLayer.lights.size());
    writeYamlScalar(stream, "  ", "light_overlay_vertices", sourceMarkerOverlaySummary.lightVertices);
    writeYamlScalar(stream, "  ", "static_render_lights", staticRenderLightCount);
    writeYamlScalar(stream, "  ", "light_diagnostics", lightLayer.diagnostics.size());
    writeYamlScalar(stream, "  ", "sound_objects", soundLayer.objects.size());
    writeYamlScalar(stream, "  ", "sound_overlay_vertices", sourceMarkerOverlaySummary.soundVertices);
    writeYamlScalar(stream, "  ", "sound_references", soundLayer.referenceCount);
    writeYamlScalar(stream, "  ", "resolved_sound_references", soundLayer.resolvedReferenceCount);
    writeYamlScalar(
        stream,
        "  ",
        "unresolved_required_sound_references",
        soundLayer.unresolvedRequiredReferenceCount);
    writeYamlScalar(stream, "  ", "spawn_source_objects", spawnLayer.objects.size());
    writeYamlScalar(stream, "  ", "spawn_overlay_vertices", sourceMarkerOverlaySummary.spawnVertices);
    writeYamlScalar(stream, "  ", "spawn_npc_numbers", spawnLayer.npcNumberCount);
    writeYamlScalar(stream, "  ", "model_instances", sceneData.modelInstances.size());
    writeYamlScalar(stream, "  ", "model_instances_in_camera_front", modelInstanceCameraFrameSummary.inFront);
    writeYamlScalar(stream, "  ", "model_instances_in_camera_depth_range", modelInstanceCameraFrameSummary.inDepthRange);
    writeYamlScalar(stream, "  ", "model_instances_in_camera_frame", modelInstanceCameraFrameSummary.inView);
    writeYamlScalar(stream, "  ", "expected_model_instances", sidecars.materialAliases.stats.modelInstances);
    writeYamlScalar(stream, "  ", "resolved_model_instance_assets", modelInstanceSummary.resolvedAssets);
    writeYamlScalar(stream, "  ", "missing_model_instance_assets", modelInstanceSummary.missingAssets);
    writeYamlScalar(stream, "  ", "drawable_model_instance_geometry", modelInstanceSummary.drawableGeometry);
    writeYamlScalar(stream, "  ", "missing_drawable_model_instance_geometry", modelInstanceSummary.missingDrawableGeometry);
    writeYamlScalar(stream, "  ", "decoded_model_instance_skin_textures", modelInstanceSummary.decodedSkinTextures);
    writeYamlScalar(stream, "  ", "actor_variant_candidates", modelInstanceSummary.actorVariantCandidates);
    writeYamlScalar(stream, "  ", "actor_variant_resolved", modelInstanceSummary.actorVariantResolved);
    writeYamlScalar(stream, "  ", "actor_variant_unresolved", modelInstanceSummary.actorVariantUnresolved);
    writeYamlScalar(stream, "  ", "actor_variant_actor_rows", modelInstanceSummary.actorVariantActorRows);
    writeYamlScalar(
        stream,
        "  ",
        "actor_variant_gameplay_identity_rows",
        modelInstanceSummary.actorVariantGameplayIdentityRows);
    writeYamlScalar(stream, "  ", "actor_variant_foot_sound_fields", modelInstanceSummary.actorVariantFootSoundFields);
    writeYamlScalar(
        stream,
        "  ",
        "actor_variant_resolved_foot_sounds",
        modelInstanceSummary.actorVariantResolvedFootSounds);
    writeYamlScalar(
        stream,
        "  ",
        "actor_variant_unresolved_foot_sounds",
        modelInstanceSummary.actorVariantUnresolvedFootSounds);
    writeYamlScalar(
        stream,
        "  ",
        "actor_variant_source_sound_references",
        modelInstanceSummary.actorVariantSourceSoundReferences);
    writeYamlScalar(
        stream,
        "  ",
        "actor_variant_resolved_source_sound_references",
        modelInstanceSummary.actorVariantResolvedSourceSoundReferences);
    writeYamlScalar(
        stream,
        "  ",
        "actor_variant_unresolved_source_sound_references",
        modelInstanceSummary.actorVariantUnresolvedSourceSoundReferences);
    writeYamlScalar(
        stream,
        "  ",
        "actor_variant_source_voice_references",
        modelInstanceSummary.actorVariantSourceVoiceReferences);
    writeYamlScalar(
        stream,
        "  ",
        "actor_variant_resolved_source_voice_references",
        modelInstanceSummary.actorVariantResolvedSourceVoiceReferences);
    writeYamlScalar(
        stream,
        "  ",
        "actor_variant_unresolved_source_voice_references",
        modelInstanceSummary.actorVariantUnresolvedSourceVoiceReferences);
    writeYamlScalar(stream, "  ", "scripted_objects", modelInstanceSummary.scriptedObjects);
    writeYamlScalar(
        stream,
        "  ",
        "scripted_objects_with_collision_visuals",
        modelInstanceSummary.scriptedObjectsWithCollisionVisuals);
    writeYamlScalar(
        stream,
        "  ",
        "scripted_objects_with_model_collision_volumes",
        modelInstanceSummary.scriptedObjectsWithModelCollisionVolumes);
    writeYamlScalar(
        stream,
        "  ",
        "scripted_objects_requiring_billboard_collision_visuals",
        modelInstanceSummary.scriptedObjectsRequiringBillboardCollisionVisuals);
    writeYamlScalar(
        stream,
        "  ",
        "missing_scripted_object_collision_visuals",
        modelInstanceSummary.missingScriptedObjectCollisionVisuals);

    writeYamlScalar(stream, "  ", "mechanism_preview_candidates", mechanismPreviewSummary.candidates);
    writeYamlScalar(stream, "  ", "mechanism_preview_changed_bounds", mechanismPreviewSummary.changedBounds);
    writeYamlScalar(stream, "  ", "material_textures", textureStatuses.size());
    writeYamlScalar(stream, "  ", "resolved_dtx", resolvedTextureCount);
    writeYamlScalar(stream, "  ", "ambiguous_dtx", ambiguousTextureCount);
    writeYamlScalar(stream, "  ", "source_dtx_paths", sourceDtxPathCount);
    writeYamlScalar(stream, "  ", "default_helper_materials", defaultHelperMaterialCount);
    writeYamlScalar(stream, "  ", "placeholder_missing_source_materials", placeholderMissingSourceMaterialCount);
    writeYamlScalar(stream, "  ", "dtx_headers", loadedDtxHeaderCount);
    writeYamlScalar(stream, "  ", "dtx_headers_matching_sidecar", matchedDtxHeaderCount);
    writeYamlScalar(stream, "  ", "dtx_user_flag_records", dtxUserFlagRecordCount);
    writeYamlScalar(stream, "  ", "dtx_extra_byte_records", dtxExtraByteRecordCount);
    writeYamlScalar(stream, "  ", "dtx_mip_payloads", dtxMipPayloadCount);
    writeYamlScalar(stream, "  ", "dtx_decoded_preview_mips", dtxDecodedPreviewMipCount);
    writeYamlScalar(stream, "  ", "dtx_section_metadata_records", dtxSectionMetadataCount);
    writeYamlScalar(stream, "  ", "dtx_section_payloads_available", dtxSectionPayloadAvailableCount);
    writeYamlScalar(stream, "  ", "dtx_command_strings", dtxCommandStringCount);
    writeYamlScalar(stream, "  ", "decoded_cache_determinism_checked", decodedCacheDeterminismCheckedCount);
    writeYamlScalar(stream, "  ", "decoded_cache_source_decoded", decodedCacheSourceDecodedCount);
    writeYamlScalar(stream, "  ", "decoded_cache_image_decoded", decodedCacheImageDecodedCount);
    writeYamlScalar(stream, "  ", "decoded_cache_matches_source", decodedCacheMatchCount);
    writeYamlScalar(stream, "  ", "decoded_cache_mismatches", nondeterministicMaterialCaches.size());
    writeYamlScalar(stream, "  ", "sprite_materials", spriteMaterialCount);
    writeYamlScalar(stream, "  ", "resolved_sprite_materials", resolvedSpriteMaterialCount);
    writeYamlScalar(stream, "  ", "sprite_frame_textures", spriteFrameTextureCount);
    writeYamlScalar(stream, "  ", "resolved_sprite_frame_textures", resolvedSpriteFrameTextureCount);
    writeYamlScalar(stream, "  ", "unresolved_sprite_frame_textures", unresolvedSpriteFrameTextureCount);
    writeYamlScalar(stream, "  ", "ambiguous_sprite_frame_textures", ambiguousSpriteFrameTextureCount);
    writeYamlScalar(stream, "  ", "raw_object_asset_refs", rawObjectStatuses.size());
    writeYamlScalar(stream, "  ", "required_raw_object_asset_refs", requiredRawObjectAssetReferenceCount);
    writeYamlScalar(stream, "  ", "optional_raw_object_asset_refs", optionalRawObjectAssetReferenceCount);
    writeYamlScalar(stream, "  ", "unresolved_required_raw_object_asset_refs", unresolvedRequiredRawObjects.size());
    writeYamlScalar(stream, "  ", "unresolved_optional_raw_object_asset_refs", unresolvedOptionalRawObjects.size());
    writeYamlScalar(stream, "  ", "asset_issue_marker_source_objects", assetIssueMarkerSummary.sourceObjects);
    writeYamlScalar(stream, "  ", "asset_issue_marker_candidates", assetIssueMarkerSummary.candidates);
    writeYamlScalar(stream, "  ", "asset_issue_marker_unpositioned", assetIssueMarkerSummary.unpositioned);
    writeYamlScalar(stream, "  ", "asset_issue_marker_required_candidates", assetIssueMarkerSummary.requiredCandidates);
    writeYamlScalar(
        stream,
        "  ",
        "asset_issue_marker_required_unpositioned",
        assetIssueMarkerSummary.requiredUnpositioned);
    writeYamlScalar(stream, "  ", "mechanism_target_marker_groups", mechanismTargetMarkerSummary.targetGroups);
    writeYamlScalar(stream, "  ", "mechanism_target_marker_candidates", mechanismTargetMarkerSummary.candidates);
    writeYamlScalar(stream, "  ", "mechanism_target_marker_vertices", mechanismTargetMarkerSummary.vertices);
    writeYamlScalar(
        stream,
        "  ",
        "mechanism_target_marker_source_links",
        mechanismTargetMarkerSummary.sourceLinkedTargets);
    writeYamlScalar(stream, "  ", "mechanism_gizmo_candidates", mechanismTargetMarkerSummary.gizmoCandidates);
    writeYamlScalar(
        stream,
        "  ",
        "mechanism_circle_gizmo_candidates",
        mechanismTargetMarkerSummary.circleGizmoCandidates);
    writeYamlScalar(
        stream,
        "  ",
        "mechanism_target_gizmo_candidates",
        mechanismTargetMarkerSummary.targetGizmoCandidates);
    writeYamlScalar(stream, "  ", "mechanism_motion_path_markers", mechanismTargetMarkerSummary.motionPathMarkers);
    writeYamlScalar(
        stream,
        "  ",
        "mechanism_los_checked_candidates",
        mechanismTargetMarkerSummary.lineOfSightCheckedCandidates);
    writeYamlScalar(
        stream,
        "  ",
        "mechanism_los_blocked_candidates",
        mechanismTargetMarkerSummary.lineOfSightBlockedCandidates);

    stream << "actor_variants:\n";
    writeYamlScalar(stream, "  ", "candidates", modelInstanceSummary.actorVariantCandidates);
    writeYamlScalar(stream, "  ", "resolved", modelInstanceSummary.actorVariantResolved);
    writeYamlScalar(stream, "  ", "unresolved", modelInstanceSummary.actorVariantUnresolved);
    writeYamlScalar(stream, "  ", "actor_rows", modelInstanceSummary.actorVariantActorRows);
    writeYamlScalar(
        stream,
        "  ",
        "gameplay_identity_rows",
        modelInstanceSummary.actorVariantGameplayIdentityRows);
    writeYamlScalar(stream, "  ", "foot_sound_fields", modelInstanceSummary.actorVariantFootSoundFields);
    writeYamlScalar(stream, "  ", "resolved_foot_sounds", modelInstanceSummary.actorVariantResolvedFootSounds);
    writeYamlScalar(stream, "  ", "unresolved_foot_sounds", modelInstanceSummary.actorVariantUnresolvedFootSounds);
    writeYamlScalar(stream, "  ", "source_sound_references", modelInstanceSummary.actorVariantSourceSoundReferences);
    writeYamlScalar(
        stream,
        "  ",
        "resolved_source_sound_references",
        modelInstanceSummary.actorVariantResolvedSourceSoundReferences);
    writeYamlScalar(
        stream,
        "  ",
        "unresolved_source_sound_references",
        modelInstanceSummary.actorVariantUnresolvedSourceSoundReferences);
    writeYamlScalar(stream, "  ", "source_voice_references", modelInstanceSummary.actorVariantSourceVoiceReferences);
    writeYamlScalar(
        stream,
        "  ",
        "resolved_source_voice_references",
        modelInstanceSummary.actorVariantResolvedSourceVoiceReferences);
    writeYamlScalar(
        stream,
        "  ",
        "unresolved_source_voice_references",
        modelInstanceSummary.actorVariantUnresolvedSourceVoiceReferences);

    if (modelInstanceSummary.unresolvedActorVariants.empty())
    {
        stream << "  missing_variants: []\n";
    }
    else
    {
        stream << "  missing_variants:\n";

        for (const Mm9ModelInstanceAssetResolutionSummary::UnresolvedActorVariant &unresolved :
            modelInstanceSummary.unresolvedActorVariants)
        {
            stream << "    - source_object_index: " << unresolved.sourceObjectIndex << '\n';
            writeYamlScalar(stream, "      ", "source_ref", unresolved.sourceRef);
            writeYamlScalar(stream, "      ", "source_class", unresolved.sourceClass);
            writeYamlScalar(stream, "      ", "source_name", unresolved.sourceName);
            writeYamlScalar(stream, "      ", "source_model", unresolved.sourceModel);
            writeYamlScalar(stream, "      ", "source_skin", unresolved.sourceSkin);
        }
    }

    stream << "dat_world_reference_validation:\n";
    writeYamlScalar(stream, "  ", "issues", datWorldReferenceIssues.size());
    writeYamlScalar(stream, "  ", "invalid_leaf_reference_count", sidecars.datWorld.totals.invalidLeafReferenceCount);
    writeYamlScalar(stream, "  ", "invalid_leaf_refs", sidecars.datWorld.leafReferences.invalidRefs);
    writeYamlScalar(stream, "  ", "invalid_surface_texture_refs", invalidSurfaceTextureRefs);
    writeYamlScalar(stream, "  ", "invalid_poly_surface_refs", invalidPolySurfaceRefs);
    writeYamlScalar(stream, "  ", "invalid_poly_plane_refs", invalidPolyPlaneRefs);
    writeYamlScalar(stream, "  ", "invalid_poly_vertex_refs", invalidPolyVertexRefs);
    writeYamlScalar(stream, "  ", "invalid_node_poly_refs", invalidNodePolyRefs);
    writeYamlScalar(stream, "  ", "invalid_root_node_refs", invalidRootNodeRefs);

    if (datWorldReferenceIssues.empty())
    {
        stream << "  issue_details: []\n";
    }
    else
    {
        stream << "  issue_details:\n";

        for (const std::string &issue : datWorldReferenceIssues)
        {
            stream << "    - ";
            writeYamlQuoted(stream, issue);
            stream << '\n';
        }
    }

    stream << "raw_object_sidecar_validation:\n";
    writeYamlScalar(stream, "  ", "issues", rawObjectSidecarIssues.size());

    if (rawObjectSidecarIssues.empty())
    {
        stream << "  issue_details: []\n";
    }
    else
    {
        stream << "  issue_details:\n";

        for (const std::string &issue : rawObjectSidecarIssues)
        {
            stream << "    - ";
            writeYamlQuoted(stream, issue);
            stream << '\n';
        }
    }

    stream << "unresolved_events:\n";
    writeYamlScalar(stream, "  ", "total", sidecars.events.unresolved.size());
    writeYamlScalar(stream, "  ", "warnings", unresolvedEventWarnings);
    writeYamlScalar(stream, "  ", "errors", unresolvedEventErrors);

    if (sidecars.events.unresolved.empty())
    {
        stream << "  entries: []\n";
    }
    else
    {
        stream << "  entries:\n";

        for (const OpenYAMM::Game::Mm9EventUnresolved &entry : sidecars.events.unresolved)
        {
            stream << "    - kind: ";
            writeYamlQuoted(stream, entry.kind);
            stream << '\n';
            writeYamlScalar(
                stream,
                "      ",
                "source_object_index",
                entry.sourceObjectIndex >= 0 ? static_cast<size_t>(entry.sourceObjectIndex) : 0);
            writeYamlScalar(stream, "      ", "source_name", entry.sourceName);
            writeYamlScalar(stream, "      ", "source_class", entry.sourceClass);
            writeYamlScalar(stream, "      ", "severity", entry.severity);
            writeYamlScalar(
                stream,
                "      ",
                "nearest_movable_world_models_by_rotation_point",
                entry.nearestMovableWorldModelsByRotationPoint.size());
            writeYamlScalar(
                stream,
                "      ",
                "nearest_movable_world_models_by_position",
                entry.nearestMovableWorldModelsByPosition.size());
        }
    }

    stream << "mechanisms:\n";
    writeYamlScalar(stream, "  ", "total", mechanismSummary.total);
    writeYamlScalar(stream, "  ", "with_binding", mechanismSummary.withBinding);
    writeYamlScalar(stream, "  ", "movable_world_models", mechanismSummary.movableWorldModels);
    writeYamlScalar(stream, "  ", "world_model_targets", mechanismSummary.withWorldModelTarget);
    writeYamlScalar(
        stream,
        "  ",
        "world_model_targets_with_movable_role",
        mechanismSummary.worldModelTargetsWithMovableRole);
    writeYamlScalar(
        stream,
        "  ",
        "world_model_targets_without_movable_role",
        mechanismSummary.worldModelTargetsWithoutMovableRole);
    writeYamlScalar(
        stream,
        "  ",
        "world_model_targets_missing_model",
        mechanismSummary.worldModelTargetsMissingModel);
    writeYamlScalar(
        stream,
        "  ",
        "world_model_targets_with_polygon_group",
        mechanismSummary.worldModelTargetsWithPolygonGroup);
    writeYamlScalar(
        stream,
        "  ",
        "world_model_targets_missing_polygon_group",
        mechanismSummary.worldModelTargetsMissingPolygonGroup);
    writeYamlScalar(
        stream,
        "  ",
        "world_model_targets_mismatched_polygon_group",
        mechanismSummary.worldModelTargetsMismatchedPolygonGroup);
    writeYamlScalar(stream, "  ", "model_instance_targets", mechanismSummary.withModelInstanceTarget);
    writeYamlScalar(stream, "  ", "with_linear_motion", mechanismSummary.withLinearMotion);
    writeYamlScalar(stream, "  ", "with_rotation_motion", mechanismSummary.withRotationMotion);
    writeYamlScalar(stream, "  ", "with_sound_evidence", mechanismSummary.withSoundEvidence);
    writeYamlScalar(stream, "  ", "sound_slots", mechanismSummary.soundSlots);
    writeYamlScalar(stream, "  ", "authored_sound_references", mechanismSummary.authoredSoundReferences);
    writeYamlScalar(stream, "  ", "empty_sound_references", mechanismSummary.emptySoundReferences);
    writeYamlScalar(stream, "  ", "previewable_mechanisms", mechanismSummary.previewableMechanisms);
    writeYamlScalar(stream, "  ", "inert_mechanisms", mechanismSummary.inertMechanisms);
    writeYamlScalar(stream, "  ", "inert_preview_entries", mechanismSummary.inertPreviewMechanisms.size());
    writeYamlScalar(stream, "  ", "without_preview_motion", mechanismSummary.mechanismsWithoutPreviewMotion);
    writeYamlScalar(stream, "  ", "without_preview_target", mechanismSummary.mechanismsWithoutPreviewTarget);
    writeYamlScalar(stream, "  ", "activation_start_open_fields", mechanismSummary.activationStartOpenFields);
    writeYamlScalar(stream, "  ", "activation_locked_fields", mechanismSummary.activationLockedFields);
    writeYamlScalar(stream, "  ", "activation_push_open_fields", mechanismSummary.activationPushOpenFields);
    writeYamlScalar(stream, "  ", "activation_touch_to_open_fields", mechanismSummary.activationTouchToOpenFields);
    writeYamlScalar(stream, "  ", "activation_lock_on_close_fields", mechanismSummary.activationLockOnCloseFields);
    writeYamlScalar(
        stream,
        "  ",
        "activation_reopen_on_contact_fields",
        mechanismSummary.activationReopenOnContactFields);
    writeYamlScalar(stream, "  ", "rotation_open_away_fields", mechanismSummary.rotationOpenAwayFields);
    writeYamlScalar(stream, "  ", "timing_move_delay_fields", mechanismSummary.timingMoveDelayFields);
    writeYamlScalar(stream, "  ", "timing_open_wait_fields", mechanismSummary.timingOpenWaitFields);
    writeYamlScalar(stream, "  ", "trigger_outputs", mechanismSummary.triggerOutputs);
    writeYamlScalar(stream, "  ", "unresolved_trigger_outputs", mechanismSummary.unresolvedTriggerOutputs);
    writeYamlScalar(stream, "  ", "incomplete_linear_motion", mechanismSummary.incompleteLinearMotion);
    writeYamlScalar(stream, "  ", "incomplete_rotation_motion", mechanismSummary.incompleteRotationMotion);
    writeYamlScalar(stream, "  ", "unresolved_targets", mechanismSummary.unresolvedTargets);
    writeYamlScalar(stream, "  ", "unresolved_required_targets", mechanismSummary.unresolvedRequiredTargets);
    writeYamlScalar(stream, "  ", "preview_candidates", mechanismPreviewSummary.candidates);
    writeYamlScalar(stream, "  ", "preview_target_found", mechanismPreviewSummary.targetFound);
    writeYamlScalar(stream, "  ", "preview_transformed_triangles", mechanismPreviewSummary.transformedTriangles);
    writeYamlScalar(stream, "  ", "preview_changed_bounds", mechanismPreviewSummary.changedBounds);

    if (mechanismSummary.incompleteMotion.empty())
    {
        stream << "  incomplete_motion: []\n";
    }
    else
    {
        stream << "  incomplete_motion:\n";

        for (const Mm9MechanismValidationSummary::IncompleteMotion &incomplete :
            mechanismSummary.incompleteMotion)
        {
            stream << "    - source_object_index: " << incomplete.sourceObjectIndex << '\n';
            writeYamlScalar(stream, "      ", "source_class", incomplete.sourceClass);
            writeYamlScalar(stream, "      ", "source_name", incomplete.sourceName);
            writeYamlScalar(stream, "      ", "mechanism_id", incomplete.mechanismId);
            writeYamlScalar(stream, "      ", "motion_kind", incomplete.motionKind);
            stream << "      missing_fields:\n";

            for (const std::string &fieldName : incomplete.missingFields)
            {
                stream << "        - ";
                writeYamlQuoted(stream, fieldName);
                stream << '\n';
            }
        }
    }

    if (!mechanismSummary.unresolved.empty())
    {
        stream << "  unresolved:\n";

        for (const Mm9MechanismValidationSummary::UnresolvedMechanismTarget &unresolved : mechanismSummary.unresolved)
        {
            stream << "    - source_object_index: " << unresolved.sourceObjectIndex << '\n';
            writeYamlScalar(stream, "      ", "source_class", unresolved.sourceClass);
            writeYamlScalar(stream, "      ", "source_name", unresolved.sourceName);
            writeYamlScalar(stream, "      ", "mechanism_id", unresolved.mechanismId);
            writeYamlScalar(stream, "      ", "target_kind", unresolved.targetKind);
            writeYamlScalar(stream, "      ", "confidence", unresolved.confidence);
            writeYamlScalar(stream, "      ", "required", unresolved.required);

            if (!unresolved.nearestWorldModels.empty())
            {
                stream << "      nearest_movable_world_models_by_rotation_point:\n";

                for (const Mm9MechanismValidationSummary::CandidateWorldModel &candidate :
                    unresolved.nearestWorldModels)
                {
                    stream << "        - source_model_index: " << candidate.sourceModelIndex << '\n';
                    writeYamlScalar(stream, "          ", "source_name", candidate.sourceName);
                    writeYamlScalar(stream, "          ", "movable", candidate.movable);
                    stream << "          distance_from_rotation_point_lt: "
                           << candidate.distanceFromRotationPointLt << '\n';
                }
            }
        }
    }
    else
    {
        stream << "  unresolved: []\n";
    }

    if (mechanismSummary.nonMovableWorldModelTargets.empty())
    {
        stream << "  non_movable_world_model_targets: []\n";
    }
    else
    {
        stream << "  non_movable_world_model_targets:\n";

        for (const Mm9MechanismValidationSummary::NonMovableWorldModelTarget &target :
            mechanismSummary.nonMovableWorldModelTargets)
        {
            stream << "    - source_object_index: " << target.sourceObjectIndex << '\n';
            writeYamlScalar(stream, "      ", "source_class", target.sourceClass);
            writeYamlScalar(stream, "      ", "source_name", target.sourceName);
            writeYamlScalar(stream, "      ", "mechanism_id", target.mechanismId);
            writeYamlScalar(stream, "      ", "source_model_index", target.sourceModelIndex);
            writeYamlScalar(stream, "      ", "source_model_name", target.sourceModelName);
            writeYamlScalar(stream, "      ", "confidence", target.confidence);
            writeYamlScalar(stream, "      ", "target_model_found", target.targetModelFound);
        }
    }

    if (mechanismSummary.polygonGroupTargetIssues.empty())
    {
        stream << "  polygon_group_target_issues: []\n";
    }
    else
    {
        stream << "  polygon_group_target_issues:\n";

        for (const Mm9MechanismValidationSummary::PolygonGroupTargetIssue &issue :
            mechanismSummary.polygonGroupTargetIssues)
        {
            stream << "    - source_object_index: " << issue.sourceObjectIndex << '\n';
            writeYamlScalar(stream, "      ", "source_class", issue.sourceClass);
            writeYamlScalar(stream, "      ", "source_name", issue.sourceName);
            writeYamlScalar(stream, "      ", "mechanism_id", issue.mechanismId);
            writeYamlScalar(stream, "      ", "bmodel_index", issue.bmodelIndex);
            writeYamlScalar(stream, "      ", "group_source_model_index", issue.groupSourceModelIndex);
            writeYamlScalar(stream, "      ", "confidence", issue.confidence);
            writeYamlScalar(stream, "      ", "issue", issue.issue);
        }
    }

    if (mechanismSummary.inertPreviewMechanisms.empty())
    {
        stream << "  inert_preview_mechanisms: []\n";
    }
    else
    {
        stream << "  inert_preview_mechanisms:\n";

        for (const Mm9MechanismValidationSummary::InertPreviewMechanism &inert :
            mechanismSummary.inertPreviewMechanisms)
        {
            stream << "    - source_object_index: " << inert.sourceObjectIndex << '\n';
            writeYamlScalar(stream, "      ", "source_class", inert.sourceClass);
            writeYamlScalar(stream, "      ", "source_name", inert.sourceName);
            writeYamlScalar(stream, "      ", "mechanism_id", inert.mechanismId);
            writeYamlScalar(stream, "      ", "reason", inert.reason);
            writeYamlScalar(stream, "      ", "has_preview_motion", inert.hasPreviewMotion);
            writeYamlScalar(stream, "      ", "has_preview_world_model_target", inert.hasPreviewWorldModelTarget);
            writeYamlScalar(stream, "      ", "has_binding", inert.hasBinding);
            writeYamlScalar(stream, "      ", "required_target", inert.requiredTarget);
        }
    }

    stream << "asset_graph:\n";
    writeYamlScalar(stream, "  ", "total", assetSummary.total);
    writeYamlScalar(stream, "  ", "resolved", assetSummary.resolved);
    writeYamlScalar(stream, "  ", "unresolved", assetSummary.unresolved);
    writeYamlScalar(stream, "  ", "ambiguous", assetSummary.ambiguous);
    writeYamlScalar(stream, "  ", "stale", assetSummary.stale);
    writeYamlScalar(stream, "  ", "required_total", assetSummary.requiredTotal);
    writeYamlScalar(stream, "  ", "required_resolved", assetSummary.requiredResolved);
    writeYamlScalar(stream, "  ", "required_unresolved", assetSummary.requiredUnresolved);
    writeYamlScalar(stream, "  ", "required_ambiguous", assetSummary.requiredAmbiguous);
    writeYamlScalar(stream, "  ", "optional_total", assetSummary.optionalTotal);
    writeYamlScalar(stream, "  ", "optional_resolved", assetSummary.optionalResolved);
    writeYamlScalar(stream, "  ", "optional_unresolved", assetSummary.optionalUnresolved);
    writeYamlScalar(stream, "  ", "optional_ambiguous", assetSummary.optionalAmbiguous);
    writeYamlScalar(stream, "  ", "source_only", assetSummary.sourceOnly);
    writeYamlScalar(stream, "  ", "unused_source", assetSummary.unusedSource);
    stream << "  families:\n";

    for (const EditorMm9AssetDependencyFamilySummary &family : assetSummary.families)
    {
        stream << "    - family: ";
        writeYamlQuoted(stream, family.family);
        stream << '\n';
        writeYamlScalar(stream, "      ", "total", family.total);
        writeYamlScalar(stream, "      ", "resolved", family.resolved);
        writeYamlScalar(stream, "      ", "unresolved", family.unresolved);
        writeYamlScalar(stream, "      ", "ambiguous", family.ambiguous);
        writeYamlScalar(stream, "      ", "stale", family.stale);
        writeYamlScalar(stream, "      ", "required_total", family.requiredTotal);
        writeYamlScalar(stream, "      ", "required_resolved", family.requiredResolved);
        writeYamlScalar(stream, "      ", "required_unresolved", family.requiredUnresolved);
        writeYamlScalar(stream, "      ", "required_ambiguous", family.requiredAmbiguous);
        writeYamlScalar(stream, "      ", "optional_total", family.optionalTotal);
        writeYamlScalar(stream, "      ", "optional_resolved", family.optionalResolved);
        writeYamlScalar(stream, "      ", "optional_unresolved", family.optionalUnresolved);
        writeYamlScalar(stream, "      ", "optional_ambiguous", family.optionalAmbiguous);
        writeYamlScalar(stream, "      ", "source_only", family.sourceOnly);
        writeYamlScalar(stream, "      ", "unused_source", family.unusedSource);
    }

    stream << "viewport_missing_material_triangles:\n";
    if (viewportSummary.missingMaterialTriangles.empty())
    {
        stream << "  entries: []\n";
    }
    else
    {
        stream << "  entries:\n";

        for (const Mm9DatViewportRenderabilitySummary::MissingMaterialTriangle &missing :
             viewportSummary.missingMaterialTriangles)
        {
            stream << "    - triangle_index: " << missing.triangleIndex << '\n';
            writeYamlScalar(stream, "      ", "source_model_index", missing.sourceModelIndex);
            writeYamlScalar(stream, "      ", "source_poly_index", missing.sourcePolyIndex);
            writeYamlScalar(stream, "      ", "source_surface_index", missing.sourceSurfaceIndex);
            writeYamlScalar(stream, "      ", "source_texture_index", missing.sourceTextureIndex);
            writeYamlScalar(stream, "      ", "source_texture", missing.sourceTexture);
            writeYamlScalar(stream, "      ", "filter_flags", static_cast<size_t>(missing.filterFlags));
            writeYamlScalar(stream, "      ", "assigned", missing.assigned);
            writeYamlScalar(stream, "      ", "ambiguous", missing.ambiguous);
            writeYamlScalar(stream, "      ", "material_candidate_count", missing.materialCandidateCount);
            writeYamlScalar(stream, "      ", "alias", missing.alias);
            writeYamlScalar(stream, "      ", "source_dtx_resolved", missing.sourceDtxResolved);
            writeYamlScalar(stream, "      ", "placeholder_missing_source", missing.placeholderMissingSource);
        }
    }

    stream << "material_textures:\n";
    if (invalidMaterialTextures.empty())
    {
        stream << "  invalid_or_unresolved: []\n";
    }
    else
    {
        stream << "  invalid_or_unresolved:\n";

        for (const EditorMm9MaterialTextureStatus *pStatus : invalidMaterialTextures)
        {
            stream << "    - texture_index: " << pStatus->textureIndex << '\n';
        writeYamlScalar(stream, "      ", "alias", pStatus->alias);
        writeYamlScalar(stream, "      ", "source_texture", pStatus->sourceTexture);
        writeYamlScalar(stream, "      ", "source_asset_family", pStatus->sourceAssetFamily);
        writeYamlScalar(stream, "      ", "physical_path", pStatus->physicalPath);
        writeYamlScalar(stream, "      ", "default_helper_material", pStatus->defaultHelperMaterial);
        writeYamlScalar(
            stream,
            "      ",
            "default_renderable_dat_refs",
            pStatus->defaultRenderableDatReferenceCount);
        writeYamlScalar(stream, "      ", "helper_only_dat_refs", pStatus->helperOnlyDatReferenceCount);
        writeYamlScalar(stream, "      ", "alias_field_present", pStatus->aliasFieldPresent);
        writeYamlScalar(stream, "      ", "source_texture_field_present", pStatus->sourceTextureFieldPresent);
        writeYamlScalar(stream, "      ", "emitted_bitmap_field_present", pStatus->emittedBitmapFieldPresent);
        writeYamlScalar(
            stream,
            "      ",
            "emitted_bitmap_mode_field_present",
            pStatus->emittedBitmapModeFieldPresent);
        writeYamlScalar(stream, "      ", "emitted_bitmap", pStatus->emittedBitmap);
        writeYamlScalar(stream, "      ", "emitted_bitmap_mode", pStatus->emittedBitmapMode);
        writeYamlScalar(stream, "      ", "resolution_source", pStatus->resolutionSource);
        writeYamlScalar(stream, "      ", "alias_applied", pStatus->aliasApplied);
        writeYamlScalar(stream, "      ", "alias_target_key", pStatus->aliasTargetKey);
        writeYamlScalar(stream, "      ", "source_dtx_resolved", pStatus->sourceDtxResolved);
        writeYamlScalar(stream, "      ", "source_dtx_ambiguous", pStatus->sourceDtxAmbiguous);
        writeYamlScalar(stream, "      ", "source_path_exists", pStatus->sourcePathExists);
        writeYamlScalar(stream, "      ", "dtx_header_loaded", pStatus->dtxHeaderLoaded);
        writeYamlScalar(stream, "      ", "dtx_header_matches_sidecar", pStatus->dtxHeaderMatchesSidecar);
        writeYamlScalar(stream, "      ", "source_sprite_resolved", pStatus->sourceSpriteResolved);
        writeYamlScalar(stream, "      ", "source_sprite_ambiguous", pStatus->sourceSpriteAmbiguous);
        writeYamlScalar(stream, "      ", "source_sprite_path_exists", pStatus->sourceSpritePathExists);
        writeYamlScalar(stream, "      ", "source_sprite_parsed", pStatus->sourceSpriteParsed);
        writeYamlScalar(stream, "      ", "sprite_frame_textures", pStatus->spriteFrameTextureCount);
        writeYamlScalar(
            stream,
            "      ",
            "resolved_sprite_frame_textures",
            pStatus->resolvedSpriteFrameTextureCount);
        writeYamlScalar(
            stream,
            "      ",
            "unresolved_sprite_frame_textures",
            pStatus->unresolvedSpriteFrameTextureCount);
        writeYamlScalar(
            stream,
            "      ",
            "ambiguous_sprite_frame_textures",
            pStatus->ambiguousSpriteFrameTextureCount);

        if (!pStatus->sourceDtxCandidates.empty())
        {
                stream << "      candidates:\n";

                for (const std::string &candidate : pStatus->sourceDtxCandidates)
                {
                    stream << "        - ";
                    writeYamlQuoted(stream, candidate);
                stream << '\n';
            }
        }

        if (!pStatus->sourceSpriteCandidates.empty())
        {
            stream << "      sprite_candidates:\n";

            for (const std::string &candidate : pStatus->sourceSpriteCandidates)
            {
                stream << "        - ";
                writeYamlQuoted(stream, candidate);
                stream << '\n';
            }
        }

        if (!pStatus->unresolvedSpriteFrameTextureRefs.empty())
        {
            stream << "      unresolved_sprite_frame_texture_refs:\n";

            for (const std::string &frameTextureRef : pStatus->unresolvedSpriteFrameTextureRefs)
            {
                stream << "        - ";
                writeYamlQuoted(stream, frameTextureRef);
                stream << '\n';
            }
        }

        if (!pStatus->ambiguousSpriteFrameTextureRefs.empty())
        {
            stream << "      ambiguous_sprite_frame_texture_refs:\n";

            for (const std::string &frameTextureRef : pStatus->ambiguousSpriteFrameTextureRefs)
            {
                stream << "        - ";
                writeYamlQuoted(stream, frameTextureRef);
                stream << '\n';
            }
        }
    }
    }

    if (staleMaterialCaches.empty())
    {
        stream << "  stale_caches: []\n";
    }
    else
    {
        stream << "  stale_caches:\n";

        for (const EditorMm9MaterialTextureStatus *pStatus : staleMaterialCaches)
        {
            stream << "    - texture_index: " << pStatus->textureIndex << '\n';
            writeYamlScalar(stream, "      ", "alias", pStatus->alias);
            writeYamlScalar(stream, "      ", "source_texture", pStatus->sourceTexture);
            writeYamlScalar(stream, "      ", "emitted_bitmap", pStatus->emittedBitmap);
            writeYamlScalar(stream, "      ", "resolved_cache_path", pStatus->resolvedCachePath);
        }
    }

    if (nondeterministicMaterialCaches.empty())
    {
        stream << "  nondeterministic_decoded_caches: []\n";
    }
    else
    {
        stream << "  nondeterministic_decoded_caches:\n";

        for (const EditorMm9MaterialTextureStatus *pStatus : nondeterministicMaterialCaches)
        {
            stream << "    - texture_index: " << pStatus->textureIndex << '\n';
            writeYamlScalar(stream, "      ", "alias", pStatus->alias);
            writeYamlScalar(stream, "      ", "source_texture", pStatus->sourceTexture);
            writeYamlScalar(stream, "      ", "emitted_bitmap", pStatus->emittedBitmap);
            writeYamlScalar(stream, "      ", "emitted_bitmap_mode", pStatus->emittedBitmapMode);
            writeYamlScalar(stream, "      ", "resolved_source_path", pStatus->resolvedSourcePath);
            writeYamlScalar(stream, "      ", "resolved_cache_path", pStatus->resolvedCachePath);
            writeYamlScalar(stream, "      ", "source_dtx_decoded", pStatus->sourceDtxDecodedForCache);
            writeYamlScalar(stream, "      ", "cache_image_decoded", pStatus->cacheImageDecoded);
            writeYamlScalar(stream, "      ", "cache_matches_decoded_source", pStatus->cacheMatchesDecodedSource);
            writeYamlScalar(stream, "      ", "message", pStatus->cacheDeterminismMessage);
        }
    }

    stream << "raw_object_asset_references:\n";
    if (unresolvedRequiredRawObjects.empty())
    {
        stream << "  unresolved_required: []\n";
    }
    else
    {
        stream << "  unresolved_required:\n";

        for (const EditorMm9RawObjectAssetReferenceStatus *pStatus : unresolvedRequiredRawObjects)
        {
            writeMm9RawObjectAssetReferenceStatus(stream, *pStatus);
        }
    }

    if (unresolvedOptionalRawObjects.empty())
    {
        stream << "  unresolved_optional: []\n";
    }
    else
    {
        stream << "  unresolved_optional:\n";

        for (const EditorMm9RawObjectAssetReferenceStatus *pStatus : unresolvedOptionalRawObjects)
        {
            writeMm9RawObjectAssetReferenceStatus(stream, *pStatus);
        }
    }

    struct Mm9NormalizedDiagnostic
    {
        std::string severity;
        std::string sourceFile;
        std::string sourceIndexPath;
        std::string sidecarPath;
        std::string resolver;
        std::string suggestedOwner;
        std::string message;
    };

    std::vector<Mm9NormalizedDiagnostic> normalizedDiagnostics;
    const auto addNormalizedDiagnostic =
        [&normalizedDiagnostics](
            const std::string &severity,
            const std::string &sourceFile,
            const std::string &sourceIndexPath,
            const std::string &sidecarPath,
            const std::string &resolver,
            const std::string &suggestedOwner,
            const std::string &message)
    {
        Mm9NormalizedDiagnostic diagnostic = {};
        diagnostic.severity = severity;
        diagnostic.sourceFile = sourceFile;
        diagnostic.sourceIndexPath = sourceIndexPath;
        diagnostic.sidecarPath = sidecarPath;
        diagnostic.resolver = resolver;
        diagnostic.suggestedOwner = suggestedOwner;
        diagnostic.message = message;
        normalizedDiagnostics.push_back(std::move(diagnostic));
    };

    for (const std::string &diagnostic : levelLoadDiagnostics)
    {
        addNormalizedDiagnostic(
            "error",
            levelPhysicalPath.filename().generic_string(),
            "",
            levelPhysicalPath.filename().generic_string(),
            "mm9_level_loader",
            "parser",
            diagnostic);
    }

    for (const std::string &diagnostic : sourceManifestDiagnostics)
    {
        addNormalizedDiagnostic(
            "error",
            "source/manifest.yml",
            "",
            "source/manifest.yml",
            "mm9_source_manifest_validator",
            "source asset mirror",
            diagnostic);
    }

    for (const EditorMm9DocumentPathStatus &status : pathStatuses)
    {
        if (status.exists)
        {
            continue;
        }

        addNormalizedDiagnostic(
            isMm9DocumentPathRequired(status)
                ? "error"
                : (status.role == "generated_cache" ? "warning" : "info"),
            levelPhysicalPath.filename().generic_string(),
            "document_paths/" + status.label,
            status.relativePath,
            "mm9_document_path_inventory",
            status.sourceReadOnly ? "source asset mirror" : "sidecar generator",
            "document path is missing: " + status.relativePath);
    }

    for (const std::string &issue : datWorldReferenceIssues)
    {
        addNormalizedDiagnostic(
            "error",
            metadata.source.dat,
            "dat_world_reference_validation",
            metadata.sidecars.datWorld,
            "mm9_dat_world_sidecar_reference_validator",
            "sidecar generator",
            issue);
    }

    for (const std::string &issue : rawObjectSidecarIssues)
    {
        addNormalizedDiagnostic(
            "error",
            metadata.source.dat,
            "raw_object_sidecar_validation",
            metadata.sidecars.rawObjects,
            "mm9_raw_object_sidecar_validator",
            "sidecar generator",
            issue);
    }

    for (const EditorMm9MaterialTextureStatus *pStatus : invalidMaterialTextures)
    {
        const bool missingRequiredMaterialAliasField =
            pStatus->materialAliasEntry
            && (!pStatus->aliasFieldPresent
                || pStatus->alias.empty()
                || !pStatus->sourceTextureFieldPresent
                || pStatus->sourceTexture.empty()
                || !pStatus->emittedBitmapFieldPresent
                || pStatus->emittedBitmap.empty()
                || !pStatus->emittedBitmapModeFieldPresent
                || pStatus->emittedBitmapMode.empty());

        addNormalizedDiagnostic(
            "error",
            pStatus->physicalPath,
            "material_textures/" + std::to_string(pStatus->textureIndex),
            metadata.sidecars.materials,
            missingRequiredMaterialAliasField
                ? "mm9_material_alias_sidecar_validator"
                : "mm9_material_texture_resolver",
            missingRequiredMaterialAliasField
                ? "sidecar generator"
                : (pStatus->sourceDtxAmbiguous || pStatus->sourceSpriteAmbiguous
                    ? "authored override"
                    : "source asset mirror"),
            missingRequiredMaterialAliasField
                ? "material alias sidecar is missing required mapping fields: " + pStatus->alias
                : "material texture reference is unresolved or ambiguous: " + pStatus->sourceTexture);
    }

    for (const EditorMm9MaterialTextureStatus *pStatus : staleMaterialCaches)
    {
        addNormalizedDiagnostic(
            "error",
            pStatus->physicalPath,
            "material_textures/" + std::to_string(pStatus->textureIndex),
            pStatus->emittedBitmap,
            "mm9_material_cache_validator",
            "sidecar generator",
            "generated material cache is older than source DTX: " + pStatus->sourceTexture);
    }

    for (const EditorMm9MaterialTextureStatus *pStatus : nondeterministicMaterialCaches)
    {
        addNormalizedDiagnostic(
            "error",
            pStatus->physicalPath,
            "material_textures/" + std::to_string(pStatus->textureIndex),
            pStatus->emittedBitmap,
            "mm9_material_cache_determinism_validator",
            "sidecar generator",
            "generated material cache does not match decoded source DTX: " + pStatus->sourceTexture
                + " reason=" + pStatus->cacheDeterminismMessage);
    }

    for (const EditorMm9MaterialTextureStatus &status : textureStatuses)
    {
        const bool hasResolvedPreviewSource =
            status.defaultHelperMaterial
                ? true
                : (status.sourceAssetFamily == "sprites"
                    ? status.sourceSpriteResolved
                        && status.sourceSpritePathExists
                        && status.sourceSpriteParsed
                        && status.spriteFrameTextureCount != 0
                        && status.unresolvedSpriteFrameTextureCount == 0
                        && status.ambiguousSpriteFrameTextureCount == 0
                    : status.sourceDtxResolved && status.sourcePathExists);

        if (!status.placeholderMissingSource
            || status.datReferenceCount == 0
            || hasResolvedPreviewSource)
        {
            continue;
        }

        addNormalizedDiagnostic(
            "warning",
            status.physicalPath.empty() ? status.sourceTexture : status.physicalPath,
            "material_textures/" + std::to_string(status.textureIndex),
            metadata.sidecars.materials,
            "mm9_material_texture_resolver",
            "source asset mirror",
            "DAT material alias still renders from a placeholder cache: " + status.sourceTexture
                + " dat_refs=" + std::to_string(status.datReferenceCount));
    }

    for (const EditorMm9RawObjectAssetReferenceStatus *pStatus : unresolvedRequiredRawObjects)
    {
        addNormalizedDiagnostic(
            "error",
            metadata.source.dat,
            "raw_objects/" + std::to_string(pStatus->sourceObjectIndex)
                + "/properties/" + std::to_string(pStatus->propertyIndex),
            metadata.sidecars.rawObjects,
            "mm9_raw_object_asset_resolver",
            pStatus->ambiguous ? "authored override" : "source asset mirror",
            "required raw object asset reference is unresolved or ambiguous: "
                + pStatus->sourceFamily + " " + pStatus->sourceValue);
    }

    for (const EditorMm9RawObjectAssetReferenceStatus *pStatus : unresolvedOptionalRawObjects)
    {
        addNormalizedDiagnostic(
            "warning",
            metadata.source.dat,
            "raw_objects/" + std::to_string(pStatus->sourceObjectIndex)
                + "/properties/" + std::to_string(pStatus->propertyIndex),
            metadata.sidecars.rawObjects,
            "mm9_raw_object_asset_resolver",
            "source asset mirror",
            "optional raw object asset reference is unresolved or ambiguous: "
                + pStatus->sourceFamily + " " + pStatus->sourceValue);
    }

    for (const EditorMm9AssetDependencyFamilySummary &family : assetSummary.families)
    {
        if (family.unusedSource == 0)
        {
            continue;
        }

        addNormalizedDiagnostic(
            "warning",
            metadata.source.manifest,
            "asset_graph/families/" + family.family,
            metadata.source.manifest,
            "mm9_asset_graph_source_inventory",
            "source asset mirror",
            "source family has unused entries for the loaded map: family=" + family.family
                + " unused_source=" + std::to_string(family.unusedSource)
                + " source_only=" + std::to_string(family.sourceOnly)
                + " graph_refs=" + std::to_string(family.total));
    }

    for (const Mm9ModelInstanceAssetResolutionSummary::UnresolvedActorVariant &unresolved :
        modelInstanceSummary.unresolvedActorVariants)
    {
        addNormalizedDiagnostic(
            "error",
            metadata.source.dat,
            "raw_objects/" + std::to_string(unresolved.sourceObjectIndex),
            metadata.sidecars.materials,
            "mm9_actor_variant_resolver",
            "sidecar generator",
            "actor/monster variant is unresolved: " + unresolved.sourceName
                + " class=" + unresolved.sourceClass
                + " model=" + unresolved.sourceModel
                + " skin=" + unresolved.sourceSkin);
    }

    if (modelInstanceSummary.missingScriptedObjectCollisionVisuals != 0)
    {
        addNormalizedDiagnostic(
            "warning",
            metadata.source.dat,
            "model_instances",
            metadata.sidecars.materials,
            "mm9_scripted_object_model_resolver",
            "sidecar generator",
            "scripted object model/native collision volumes are unresolved for "
                + std::to_string(modelInstanceSummary.missingScriptedObjectCollisionVisuals)
                + " of "
                + std::to_string(modelInstanceSummary.scriptedObjectsRequiringBillboardCollisionVisuals)
                + " scripted objects");
    }

    for (const Mm9MechanismValidationSummary::IncompleteMotion &incomplete : mechanismSummary.incompleteMotion)
    {
        std::string missingFieldsText;
        for (const std::string &fieldName : incomplete.missingFields)
        {
            if (!missingFieldsText.empty())
            {
                missingFieldsText += ", ";
            }
            missingFieldsText += fieldName;
        }

        addNormalizedDiagnostic(
            "warning",
            metadata.source.dat,
            "raw_objects/" + std::to_string(incomplete.sourceObjectIndex),
            metadata.sidecars.events,
            "mm9_mechanism_motion_resolver",
            "sidecar generator",
            "mechanism " + incomplete.motionKind + " motion has incomplete parameters: "
                + incomplete.sourceName + " missing=" + missingFieldsText);
    }

    for (const Mm9MechanismValidationSummary::NonMovableWorldModelTarget &target :
        mechanismSummary.nonMovableWorldModelTargets)
    {
        addNormalizedDiagnostic(
            target.targetModelFound ? "warning" : "error",
            metadata.source.dat,
            "raw_objects/" + std::to_string(target.sourceObjectIndex),
            metadata.sidecars.events,
            "mm9_mechanism_movable_target_resolver",
            "sidecar generator",
            "mechanism world-model target is not marked movable by DAT roles: "
                + target.sourceName
                + " source_model_index=" + std::to_string(target.sourceModelIndex)
                + " target_model_found=" + (target.targetModelFound ? "true" : "false")
                + " confidence=" + target.confidence);
    }

    for (const Mm9MechanismValidationSummary::PolygonGroupTargetIssue &issue :
        mechanismSummary.polygonGroupTargetIssues)
    {
        addNormalizedDiagnostic(
            "error",
            metadata.source.dat,
            "raw_objects/" + std::to_string(issue.sourceObjectIndex),
            metadata.sidecars.events,
            "mm9_mechanism_polygon_group_resolver",
            "sidecar generator",
            "mechanism world-model target has invalid source polygon group: "
                + issue.sourceName
                + " issue=" + issue.issue
                + " bmodel_index=" + std::to_string(issue.bmodelIndex)
                + " group_source_model_index=" + std::to_string(issue.groupSourceModelIndex)
                + " confidence=" + issue.confidence);
    }

    for (const Mm9MechanismValidationSummary::UnresolvedMechanismTarget &unresolved : mechanismSummary.unresolved)
    {
        addNormalizedDiagnostic(
            unresolved.required ? "error" : "warning",
            metadata.source.dat,
            "raw_objects/" + std::to_string(unresolved.sourceObjectIndex),
            metadata.sidecars.events,
            "mm9_mechanism_target_resolver",
            "sidecar generator",
            "mechanism target is unresolved: " + unresolved.sourceName + " target_kind="
                + unresolved.targetKind + " confidence=" + unresolved.confidence);
    }

    if (mechanismSummary.inertMechanisms != 0)
    {
        addNormalizedDiagnostic(
            "info",
            metadata.source.dat,
            "mechanisms/inert_preview_mechanisms",
            metadata.sidecars.events,
            "mm9_mechanism_preview_state_resolver",
            "sidecar generator",
            "mechanisms without editor movement preview are listed with source-object reasons: inert="
                + std::to_string(mechanismSummary.inertMechanisms)
                + " missing_motion=" + std::to_string(mechanismSummary.mechanismsWithoutPreviewMotion)
                + " missing_world_model_target="
                + std::to_string(mechanismSummary.mechanismsWithoutPreviewTarget));
    }

    size_t normalizedErrorCount = 0;
    size_t normalizedWarningCount = 0;
    size_t normalizedInfoCount = 0;

    for (const Mm9NormalizedDiagnostic &diagnostic : normalizedDiagnostics)
    {
        if (diagnostic.severity == "error")
        {
            ++normalizedErrorCount;
        }
        else if (diagnostic.severity == "warning")
        {
            ++normalizedWarningCount;
        }
        else
        {
            ++normalizedInfoCount;
        }
    }

    stream << "diagnostics:\n";
    writeYamlScalar(stream, "  ", "total", normalizedDiagnostics.size());
    writeYamlScalar(stream, "  ", "errors", normalizedErrorCount);
    writeYamlScalar(stream, "  ", "warnings", normalizedWarningCount);
    writeYamlScalar(stream, "  ", "info", normalizedInfoCount);
    stream << "  severity_policy:\n";

    for (const EditorMm9DiagnosticSeverityRule &rule : mm9DiagnosticSeverityRules())
    {
        stream << "    - severity: ";
        writeYamlQuoted(stream, rule.severity);
        stream << '\n';
        writeYamlScalar(stream, "      ", "category", rule.category);
        writeYamlScalar(stream, "      ", "blocks_clean_validation", rule.blocksCleanValidation);
        writeYamlScalar(stream, "      ", "suggested_owner", rule.suggestedOwner);
    }

    if (normalizedDiagnostics.empty())
    {
        stream << "  entries: []\n";
    }
    else
    {
        stream << "  entries:\n";

        for (const Mm9NormalizedDiagnostic &diagnostic : normalizedDiagnostics)
        {
            stream << "    - severity: ";
            writeYamlQuoted(stream, diagnostic.severity);
            stream << '\n';
            writeYamlScalar(stream, "      ", "source_file", diagnostic.sourceFile);
            writeYamlScalar(stream, "      ", "source_index_path", diagnostic.sourceIndexPath);
            writeYamlScalar(stream, "      ", "sidecar_path", diagnostic.sidecarPath);
            writeYamlScalar(stream, "      ", "resolver", diagnostic.resolver);
            writeYamlScalar(stream, "      ", "suggested_owner", diagnostic.suggestedOwner);
            writeYamlScalar(stream, "      ", "message", diagnostic.message);
        }
    }

    return true;
}

std::vector<Game::Mm9DatModelRenderRole> mm9ModelRenderRolesFromSidecar(
    const EditorMm9DatWorldSidecar &sidecar)
{
    std::vector<Game::Mm9DatModelRenderRole> roles;
    roles.reserve(sidecar.worldModels.size());

    for (const EditorMm9DatWorldModelSummary &model : sidecar.worldModels)
    {
        Game::Mm9DatModelRenderRole role = {};
        role.sourceModelIndex = model.sourceModelIndex;
        role.visible = model.roles.visible;
        role.terrain = model.roles.terrain;
        role.physicsBsp = model.roles.physicsBsp;
        role.visBsp = model.roles.visBsp;
        role.sky = model.roles.sky;
        role.water = model.roles.water;
        role.triggerOrVolume = model.roles.triggerOrVolume;
        role.movable = model.roles.movable;
        roles.push_back(role);
    }

    return roles;
}

std::string lowerCopy(const std::string &value)
{
    std::string result = value;
    std::transform(
        result.begin(),
        result.end(),
        result.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
    return result;
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

Game::OutdoorSceneInteractiveFace makeInteractiveFaceEntry(
    size_t bmodelIndex,
    size_t faceIndex,
    uint32_t legacyAttributes,
    uint16_t cogNumber,
    uint16_t cogTriggeredNumber,
    uint16_t cogTrigger)
{
    Game::OutdoorSceneInteractiveFace interactiveFace = {};
    interactiveFace.bmodelIndex = bmodelIndex;
    interactiveFace.faceIndex = faceIndex;
    interactiveFace.legacyAttributes = legacyAttributes;
    interactiveFace.cogNumber = cogNumber;
    interactiveFace.cogTriggeredNumber = cogTriggeredNumber;
    interactiveFace.cogTrigger = cogTrigger;
    return interactiveFace;
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

struct Mm9SourceIntegritySnapshot
{
    bool valid = false;
    std::vector<std::string> levelDiagnostics;
    std::vector<std::string> sourceManifestDiagnostics;
    std::unordered_map<std::string, std::string> referencedSourceFileHashes;
    size_t sourceFamilyExpectedFileCount = 0;
    size_t sourceFamilyActualFileCount = 0;
    size_t sourceFamilyCountDriftCount = 0;
    size_t sourceFamilyMissingDirectoryCount = 0;
};

void summarizeMm9SourceFamilyStatuses(
    const std::vector<EditorMm9SourceAssetFamilyStatus> &statuses,
    Mm9SourceIntegritySnapshot &snapshot)
{
    snapshot.sourceFamilyExpectedFileCount = 0;
    snapshot.sourceFamilyActualFileCount = 0;
    snapshot.sourceFamilyCountDriftCount = 0;
    snapshot.sourceFamilyMissingDirectoryCount = 0;

    for (const EditorMm9SourceAssetFamilyStatus &status : statuses)
    {
        snapshot.sourceFamilyExpectedFileCount += status.expectedFileCount;
        snapshot.sourceFamilyActualFileCount += status.actualFileCount;

        if (status.declared && !status.packageDirectoryExists)
        {
            ++snapshot.sourceFamilyMissingDirectoryCount;
        }

        if (status.declared && status.expectedFileCount != status.actualFileCount)
        {
            ++snapshot.sourceFamilyCountDriftCount;
        }
    }
}

std::string mm9SourceFileDigestHex(const std::vector<uint8_t> &bytes)
{
    uint64_t hash = 1469598103934665603ull;

    for (uint8_t byte : bytes)
    {
        hash ^= byte;
        hash *= 1099511628211ull;
    }

    std::ostringstream output;
    output << std::hex << std::setfill('0') << std::setw(16) << hash;
    return output.str();
}

void addMm9ReferencedSourceFileHash(Mm9SourceIntegritySnapshot &snapshot, const std::string &pathText)
{
    if (pathText.empty())
    {
        return;
    }

    const std::filesystem::path path(pathText);

    if (path.empty())
    {
        return;
    }

    const std::string key = path.lexically_normal().generic_string();

    if (snapshot.referencedSourceFileHashes.find(key) != snapshot.referencedSourceFileHashes.end())
    {
        return;
    }

    std::vector<uint8_t> bytes;
    if (!readBinaryFileBytes(path, bytes))
    {
        snapshot.referencedSourceFileHashes.emplace(key, "<unreadable>");
        return;
    }

    snapshot.referencedSourceFileHashes.emplace(key, mm9SourceFileDigestHex(bytes));
}

Mm9SourceIntegritySnapshot collectMm9ReferencedSourceFileSnapshot(const EditorDocument &document)
{
    Mm9SourceIntegritySnapshot snapshot = {};

    for (const EditorMm9MaterialTextureStatus &status : document.mm9MaterialTextureStatuses())
    {
        if (status.sourceDtxResolved && status.sourcePathExists)
        {
            addMm9ReferencedSourceFileHash(snapshot, status.resolvedSourcePath);
        }

        if (status.sourceSpriteResolved && status.sourceSpritePathExists)
        {
            addMm9ReferencedSourceFileHash(snapshot, status.resolvedSpritePath);
        }

        for (const std::string &frameTexturePath : status.resolvedSpriteFrameTexturePaths)
        {
            addMm9ReferencedSourceFileHash(snapshot, frameTexturePath);
        }
    }

    for (const EditorMm9RawObjectAssetReferenceStatus &status : document.mm9RawObjectAssetReferenceStatuses())
    {
        if (status.resolved && !status.ambiguous)
        {
            addMm9ReferencedSourceFileHash(snapshot, status.resolvedSourcePath);
        }
    }

    snapshot.valid = true;
    return snapshot;
}

Mm9SourceIntegritySnapshot collectMm9SourceIntegritySnapshot(const std::filesystem::path &levelPath)
{
    Mm9SourceIntegritySnapshot snapshot = {};

    std::string levelText;
    if (!readTextFileContents(levelPath, levelText))
    {
        snapshot.levelDiagnostics.push_back("could not read MM9 level file: " + levelPath.generic_string());
        return snapshot;
    }

    std::string levelErrorMessage;
    const std::optional<EditorMm9DatLevelMetadata> metadata =
        loadMm9DatLevelMetadataFromText(levelText, levelErrorMessage);

    if (!metadata)
    {
        snapshot.levelDiagnostics.push_back("could not parse MM9 level file: " + levelErrorMessage);
        return snapshot;
    }

    snapshot.levelDiagnostics = validateMm9DatLevelMetadataFiles(levelPath, *metadata);

    const std::filesystem::path manifestPath = resolveMm9SourceAssetManifestPath(levelPath, *metadata);
    std::string manifestText;
    if (!readTextFileContents(manifestPath, manifestText))
    {
        snapshot.sourceManifestDiagnostics.push_back(
            "could not read MM9 source asset manifest: " + manifestPath.generic_string());
        snapshot.valid = true;
        return snapshot;
    }

    std::string manifestErrorMessage;
    const std::optional<EditorMm9SourceAssetManifest> manifest =
        loadMm9SourceAssetManifestFromText(manifestText, manifestErrorMessage);

    if (!manifest)
    {
        snapshot.sourceManifestDiagnostics.push_back(
            "could not parse MM9 source asset manifest: " + manifestErrorMessage);
        snapshot.valid = true;
        return snapshot;
    }

    snapshot.sourceManifestDiagnostics = validateMm9SourceAssetManifestFiles(manifestPath, *manifest);
    summarizeMm9SourceFamilyStatuses(inspectMm9SourceAssetManifestFiles(manifestPath, *manifest), snapshot);
    snapshot.valid = true;
    return snapshot;
}

bool mm9SourceIntegritySnapshotsMatch(
    const Mm9SourceIntegritySnapshot &before,
    const Mm9SourceIntegritySnapshot &after,
    std::string &failure)
{
    if (before.valid != after.valid)
    {
        failure = "source integrity snapshot validity changed";
        return false;
    }

    if (before.levelDiagnostics != after.levelDiagnostics)
    {
        failure = "source DAT/level diagnostics changed during verification";
        return false;
    }

    if (before.sourceManifestDiagnostics != after.sourceManifestDiagnostics)
    {
        failure = "source manifest diagnostics changed during verification";
        return false;
    }

    if (before.referencedSourceFileHashes != after.referencedSourceFileHashes)
    {
        failure = "referenced source file hashes changed during verification";
        return false;
    }

    if (before.sourceFamilyExpectedFileCount != after.sourceFamilyExpectedFileCount
        || before.sourceFamilyActualFileCount != after.sourceFamilyActualFileCount
        || before.sourceFamilyCountDriftCount != after.sourceFamilyCountDriftCount
        || before.sourceFamilyMissingDirectoryCount != after.sourceFamilyMissingDirectoryCount)
    {
        failure = "source manifest family counts changed during verification";
        return false;
    }

    return true;
}

std::string mm9LowerAsciiCopy(std::string value)
{
    for (char &character : value)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }
    return value;
}

std::string mm9TrimScalarText(const std::string &value)
{
    size_t begin = 0;
    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    size_t end = value.size();
    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    std::string trimmed = value.substr(begin, end - begin);
    if (trimmed.size() >= 2
        && ((trimmed.front() == '\'' && trimmed.back() == '\'')
            || (trimmed.front() == '"' && trimmed.back() == '"')))
    {
        trimmed = trimmed.substr(1, trimmed.size() - 2);
    }
    return trimmed;
}

std::string mm9FileNameLowerCopy(const std::string &value)
{
    const std::string trimmed = mm9TrimScalarText(value);
    const size_t slash = trimmed.find_last_of("/\\");
    return mm9LowerAsciiCopy(slash == std::string::npos ? trimmed : trimmed.substr(slash + 1));
}

std::filesystem::path resolveMm9LevelRelativePath(
    const std::filesystem::path &levelPath,
    const std::string &relativePath)
{
    const std::filesystem::path path(relativePath);
    if (path.empty())
    {
        return {};
    }
    if (path.is_absolute())
    {
        return path.lexically_normal();
    }
    return (levelPath.parent_path() / path).lexically_normal();
}

std::filesystem::path resolveMm9SourceScriptPath(
    const std::filesystem::path &levelPath,
    const std::string &sourcePath)
{
    const std::filesystem::path path(sourcePath);
    if (path.empty())
    {
        return {};
    }
    if (path.is_absolute())
    {
        return path.lexically_normal();
    }
    return (levelPath.parent_path() / "../source/scripts" / path).lexically_normal();
}

const Game::Mm9EventObject *findMm9EventObjectBySourceIndex(
    const Game::Mm9EventsData &events,
    size_t sourceObjectIndex,
    size_t *pEventObjectIndex)
{
    for (size_t objectIndex = 0; objectIndex < events.objects.size(); ++objectIndex)
    {
        const Game::Mm9EventObject &eventObject = events.objects[objectIndex];
        if (eventObject.sourceObjectIndex == static_cast<int>(sourceObjectIndex))
        {
            if (pEventObjectIndex != nullptr)
            {
                *pEventObjectIndex = objectIndex;
            }
            return &eventObject;
        }
    }
    return nullptr;
}

const EditorMm9RawObject *findMm9RawObjectBySourceIndex(
    const EditorMm9RawObjectsSidecar &rawObjects,
    size_t sourceObjectIndex)
{
    for (const EditorMm9RawObject &rawObject : rawObjects.objects)
    {
        if (rawObject.objectIndex == sourceObjectIndex)
        {
            return &rawObject;
        }
    }
    return nullptr;
}

const Game::Mm9EventMechanism *findMm9MechanismForObject(
    const Game::Mm9EventsData &events,
    const std::string &objectId,
    size_t *pMechanismIndex)
{
    for (size_t mechanismIndex = 0; mechanismIndex < events.mechanisms.size(); ++mechanismIndex)
    {
        const Game::Mm9EventMechanism &mechanism = events.mechanisms[mechanismIndex];
        if (mechanism.objectId == objectId)
        {
            if (pMechanismIndex != nullptr)
            {
                *pMechanismIndex = mechanismIndex;
            }
            return &mechanism;
        }
    }
    return nullptr;
}

const Game::Mm9EventBinding *findMm9BindingForObject(
    const Game::Mm9EventsData &events,
    const std::string &objectId)
{
    for (const Game::Mm9EventBinding &binding : events.bindings)
    {
        if (binding.objectId == objectId)
        {
            return &binding;
        }
    }
    return nullptr;
}

const Game::Mm9EventScript *findMm9EventScriptById(
    const Game::Mm9EventsData &events,
    const std::string &scriptId)
{
    const std::string normalizedScriptId = mm9LowerAsciiCopy(scriptId);
    for (const Game::Mm9EventScript &script : events.scripts)
    {
        if (mm9LowerAsciiCopy(script.scriptId) == normalizedScriptId)
        {
            return &script;
        }
    }
    return nullptr;
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
        companionBytes = assetFileSystem.readBinaryFile("_legacy/map_delta/" + companionFileName);
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
        companionBytes = assetFileSystem.readBinaryFile("_legacy/map_delta/" + companionFileName);
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
            sceneData.interactiveFaces.push_back(makeInteractiveFaceEntry(0, 0, 1, 0, 0, 0));
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

bool verifyEditorWorldOutdoorTerrainLoad(
    OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    std::string &failure)
{
    const std::filesystem::path mapPath =
        assetFileSystem.getEditorDevelopmentRoot() / "worlds/mm6/maps/oute3.scene.yml";

    if (!std::filesystem::exists(mapPath))
    {
        failure = "editor world terrain test map is missing: " + mapPath.string();
        return false;
    }

    OpenYAMM::Editor::EditorSession session;
    session.initialize(assetFileSystem);

    if (!session.openMapPhysicalPath(mapPath, failure))
    {
        failure = "could not open editor world terrain test map: " + failure;
        return false;
    }

    if (assetFileSystem.getActiveWorldId() != "mm6")
    {
        failure = "editor world terrain test did not switch to mm6";
        return false;
    }

    const OpenYAMM::Game::OutdoorMapData &outdoorGeometry = session.document().outdoorGeometry();

    if (outdoorGeometry.fileName != "oute3.odm")
    {
        failure = "editor world terrain test loaded wrong outdoor filename: " + outdoorGeometry.fileName;
        return false;
    }

    const std::optional<std::vector<std::string>> textureNames =
        OpenYAMM::Game::loadTerrainTileTextureNames(assetFileSystem, outdoorGeometry);

    if (!textureNames)
    {
        failure = "editor world terrain test could not load terrain texture names";
        return false;
    }

    OpenYAMM::Engine::DirectoryAssetPathCache directoryAssetPathsByPath;
    OpenYAMM::Engine::AssetPathLookupCache assetPathByKey;
    std::unordered_set<uint8_t> checkedTileIds;

    for (uint8_t tileId : outdoorGeometry.tileMap)
    {
        if (!checkedTileIds.insert(tileId).second)
        {
            continue;
        }

        const std::string &textureName = (*textureNames)[tileId];

        if (textureName.empty() || textureName == "pending")
        {
            failure = "editor world terrain test has unresolved texture for tile " + std::to_string(tileId);
            return false;
        }

        const std::optional<std::string> texturePath = OpenYAMM::Engine::findImageAssetPath(
            assetFileSystem,
            "Data/bitmaps",
            textureName,
            directoryAssetPathsByPath,
            assetPathByKey);

        if (!texturePath)
        {
            failure = "editor world terrain test is missing texture asset: " + textureName;
            return false;
        }
    }

    return true;
}

std::filesystem::path canonicalPathForCompare(const std::filesystem::path &path)
{
    std::error_code error;
    const std::filesystem::path canonicalPath = std::filesystem::weakly_canonical(path, error);
    return error ? path.lexically_normal() : canonicalPath;
}

bool verifyScriptVirtualPathResolvesTo(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &scriptVirtualPath,
    const std::filesystem::path &expectedPhysicalPath,
    std::string &failure)
{
    const std::optional<std::filesystem::path> resolvedPhysicalPath =
        assetFileSystem.resolvePhysicalPath(scriptVirtualPath);

    if (!resolvedPhysicalPath)
    {
        failure = "could not resolve script path " + scriptVirtualPath;
        return false;
    }

    if (canonicalPathForCompare(*resolvedPhysicalPath) != canonicalPathForCompare(expectedPhysicalPath))
    {
        failure = "script path " + scriptVirtualPath + " resolved to " + resolvedPhysicalPath->string()
            + " instead of " + expectedPhysicalPath.string();
        return false;
    }

    return true;
}

bool verifyLoadedEditorWorldMapScript(
    OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &worldId,
    const std::string &mapFileName,
    std::string &failure)
{
    const std::filesystem::path mapPath =
        assetFileSystem.getEditorDevelopmentRoot() / "worlds" / worldId / "maps" / mapFileName;
    const std::string mapStem = std::filesystem::path(mapFileName).stem().string();
    const std::string scriptVirtualPath = "Data/scripts/maps/" + mapStem + ".lua";
    const std::filesystem::path expectedScriptPhysicalPath =
        assetFileSystem.getEditorDevelopmentRoot() / "worlds" / worldId / "events/maps" / (mapStem + ".lua");

    if (!std::filesystem::exists(mapPath))
    {
        failure = "editor world script test map is missing: " + mapPath.string();
        return false;
    }

    if (!std::filesystem::exists(expectedScriptPhysicalPath))
    {
        failure = "editor world script test lua is missing: " + expectedScriptPhysicalPath.string();
        return false;
    }

    OpenYAMM::Editor::EditorSession session;
    session.initialize(assetFileSystem);

    if (!session.openMapPhysicalPath(mapPath, failure))
    {
        failure = "could not open editor world script test map " + mapPath.string() + ": " + failure;
        return false;
    }

    if (assetFileSystem.getActiveWorldId() != worldId)
    {
        failure = "editor world script test did not switch to " + worldId;
        return false;
    }

    const std::optional<std::string> localScriptModulePath = session.localScriptModulePath();

    if (!localScriptModulePath || *localScriptModulePath != scriptVirtualPath)
    {
        failure = "editor world script test resolved unexpected local module for " + mapFileName;
        return false;
    }

    if (worldId == "mm6" && mapFileName == "oute3.odm")
    {
        const std::optional<std::string> eventSummary = session.describeMapEvent(28);

        if (!eventSummary || eventSummary->find("Town Hall") == std::string::npos)
        {
            failure = "mm6 oute3 event 28 did not resolve to Town Hall";
            return false;
        }

        if (eventSummary->find("Barbarian Fortress") != std::string::npos)
        {
            failure = "mm6 oute3 event 28 still resolves to Barbarian Fortress";
            return false;
        }
    }

    return verifyScriptVirtualPathResolvesTo(
        assetFileSystem,
        scriptVirtualPath,
        expectedScriptPhysicalPath,
        failure);
}

bool verifyEditorWorldMapScriptLoad(
    OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    std::string &failure)
{
    if (!verifyLoadedEditorWorldMapScript(assetFileSystem, "mm6", "oute3.odm", failure))
    {
        return false;
    }

    if (!verifyLoadedEditorWorldMapScript(assetFileSystem, "mm8", "out01.odm", failure))
    {
        return false;
    }

    if (!assetFileSystem.switchActiveWorld("mm7"))
    {
        failure = "could not switch asset file system to mm7 for script resolution test";
        return false;
    }

    const std::string scriptVirtualPath = "Data/scripts/maps/out09.lua";
    const std::filesystem::path expectedScriptPhysicalPath =
        assetFileSystem.getEditorDevelopmentRoot() / "worlds/mm7/events/maps/out09.lua";

    if (!verifyScriptVirtualPathResolvesTo(assetFileSystem, scriptVirtualPath, expectedScriptPhysicalPath, failure))
    {
        return false;
    }

    EditorSession session = {};
    session.initialize(assetFileSystem);
    const std::filesystem::path mapPath =
        activeWorldEditorPath(assetFileSystem, std::filesystem::path("maps") / "7d06.blv");

    if (!session.openMapPhysicalPath(mapPath, failure))
    {
        failure = "could not open mm7 7d06 mechanism test map: " + failure;
        return false;
    }

    if (session.document().kind() != EditorDocument::Kind::Indoor)
    {
        failure = "mm7 7d06 mechanism test did not load an indoor scene";
        return false;
    }

    if (!session.ensurePreviewEventRuntimeState(failure))
    {
        failure = "could not initialize mm7 7d06 preview event state: " + failure;
        return false;
    }

    const std::optional<EditorPreviewMechanismState> initialDoor5 = session.previewMechanismState(5);
    const std::optional<EditorPreviewMechanismState> initialDoor6 = session.previewMechanismState(6);
    const uint16_t closedState = static_cast<uint16_t>(OpenYAMM::Game::EvtMechanismState::Closed);

    if (!initialDoor5 || !initialDoor6 || initialDoor5->state != closedState || initialDoor6->state != closedState)
    {
        failure = "mm7 7d06 doors 5 and 6 did not initialize closed";
        return false;
    }

    if (!session.simulateMapEvent(2, failure))
    {
        failure = "could not simulate mm7 7d06 event 2: " + failure;
        return false;
    }

    const std::optional<EditorPreviewMechanismState> eventDoor5 = session.previewMechanismState(5);
    const std::optional<EditorPreviewMechanismState> eventDoor6 = session.previewMechanismState(6);
    const uint16_t openingState = static_cast<uint16_t>(OpenYAMM::Game::EvtMechanismState::Opening);

    if (!eventDoor5 || !eventDoor6 || eventDoor5->state != openingState || eventDoor6->state != openingState)
    {
        failure = "mm7 7d06 event 2 did not start opening doors 5 and 6";
        return false;
    }

    const OpenYAMM::Game::MapDeltaDoor *pDoor5 = nullptr;

    for (const OpenYAMM::Game::IndoorSceneDoor &door : session.document().indoorSceneData().initialState.doors)
    {
        if (door.door.doorId == 5)
        {
            pDoor5 = &door.door;
            break;
        }
    }

    if (pDoor5 == nullptr)
    {
        failure = "mm7 7d06 door 5 was not found in scene data";
        return false;
    }

    if (pDoor5->vertexIds.empty() || pDoor5->xOffsets.empty())
    {
        failure = "mm7 7d06 door 5 has no movement vertices";
        return false;
    }

    OpenYAMM::Game::MapDeltaData previewMapDeltaData = {};

    for (const OpenYAMM::Game::IndoorSceneDoor &door : session.document().indoorSceneData().initialState.doors)
    {
        previewMapDeltaData.doors.push_back(door.door);
    }

    OpenYAMM::Game::EventRuntimeState previewRuntimeState = {};
    OpenYAMM::Game::RuntimeMechanismState movingDoor5 = {};
    movingDoor5.state = openingState;
    movingDoor5.timeSinceTriggeredMs = 1000.0f;
    movingDoor5.currentDistance = 110.0f;
    movingDoor5.isMoving = true;
    previewRuntimeState.mechanisms[5] = movingDoor5;
    const std::vector<OpenYAMM::Game::IndoorVertex> adjustedVertices =
        OpenYAMM::Game::buildIndoorMechanismAdjustedVertices(
            session.document().indoorGeometry(),
            &previewMapDeltaData,
            &previewRuntimeState);
    const uint16_t firstVertexId = pDoor5->vertexIds.front();

    if (firstVertexId >= adjustedVertices.size())
    {
        failure = "mm7 7d06 door 5 first movement vertex is out of range";
        return false;
    }

    const float directionX = static_cast<float>(pDoor5->directionX) / 65536.0f;
    const float openX = static_cast<float>(pDoor5->xOffsets.front());
    const float closedX = openX + directionX * static_cast<float>(pDoor5->moveLength);
    const float adjustedX = static_cast<float>(adjustedVertices[firstVertexId].x);

    if (!(adjustedX > std::min(openX, closedX) && adjustedX < std::max(openX, closedX)))
    {
        failure = "mm7 7d06 door 5 adjusted vertex did not move between closed and open";
        return false;
    }

    return true;
}

bool importedModelsHaveGeometry(const std::vector<ImportedModel> &models)
{
    for (const ImportedModel &model : models)
    {
        if (!model.positions.empty() && !model.faces.empty())
        {
            return true;
        }
    }

    return false;
}

bool imageHasVisibleAlpha(const OpenYAMM::Engine::ImagePixelsBgra &image)
{
    for (size_t offset = 3; offset < image.pixels.size(); offset += 4)
    {
        if (image.pixels[offset] != 0)
        {
            return true;
        }
    }

    return false;
}

bool endsWithCaseInsensitive(const std::string &value, const std::string &suffix)
{
    if (suffix.size() > value.size())
    {
        return false;
    }

    const size_t offset = value.size() - suffix.size();
    for (size_t index = 0; index < suffix.size(); ++index)
    {
        const char left = static_cast<char>(std::tolower(static_cast<unsigned char>(value[offset + index])));
        const char right = static_cast<char>(std::tolower(static_cast<unsigned char>(suffix[index])));
        if (left != right)
        {
            return false;
        }
    }

    return true;
}

std::optional<std::filesystem::path> findMm9CaseInsensitivePhysicalPath(
    const std::filesystem::path &root,
    const std::filesystem::path &relativePath)
{
    std::filesystem::path currentPath = root;

    for (const std::filesystem::path &part : relativePath)
    {
        if (part.empty() || part == ".")
        {
            continue;
        }

        if (part == "..")
        {
            return std::nullopt;
        }

        const std::filesystem::path exactPath = currentPath / part;
        std::error_code exactError;
        if (std::filesystem::exists(exactPath, exactError) && !exactError)
        {
            currentPath = exactPath;
            continue;
        }

        std::error_code directoryError;
        if (!std::filesystem::is_directory(currentPath, directoryError) || directoryError)
        {
            return std::nullopt;
        }

        const std::string targetName = lowerCopy(part.generic_string());
        bool found = false;
        std::error_code iteratorError;
        std::filesystem::directory_iterator iterator(currentPath, iteratorError);
        const std::filesystem::directory_iterator endIterator;

        while (!iteratorError && iterator != endIterator)
        {
            if (lowerCopy(iterator->path().filename().generic_string()) == targetName)
            {
                currentPath = iterator->path();
                found = true;
                break;
            }

            iterator.increment(iteratorError);
        }

        if (!found)
        {
            return std::nullopt;
        }
    }

    return currentPath;
}

std::optional<std::filesystem::path> resolveMm9ModelTexturePhysicalPath(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &texturePath)
{
    const std::optional<std::filesystem::path> mountedPath =
        assetFileSystem.resolvePhysicalPath(texturePath);
    if (mountedPath)
    {
        return mountedPath;
    }

    const std::filesystem::path sourceRoot =
        assetFileSystem.getDevelopmentRoot()
        / std::filesystem::path("worlds")
        / assetFileSystem.getActiveWorldId()
        / "source";
    const std::string normalizedPath = normalizeMm9ModelInstanceImagePath(texturePath);

    if (normalizedPath.rfind("skins/", 0) == 0)
    {
        return findMm9CaseInsensitivePhysicalPath(sourceRoot, std::filesystem::path(normalizedPath));
    }

    if (normalizedPath.rfind("textures/", 0) == 0)
    {
        return findMm9CaseInsensitivePhysicalPath(sourceRoot, std::filesystem::path(normalizedPath));
    }

    return std::nullopt;
}

std::optional<OpenYAMM::Engine::ImagePixelsBgra> loadMm9ModelTexturePixels(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &texturePath,
    OpenYAMM::Engine::BinaryAssetCache &binaryAssetCache)
{
    if (endsWithCaseInsensitive(texturePath, ".dtx"))
    {
        const std::optional<std::filesystem::path> resolvedPath =
            resolveMm9ModelTexturePhysicalPath(assetFileSystem, texturePath);
        if (!resolvedPath)
        {
            return std::nullopt;
        }

        std::string errorMessage;
        const std::optional<OpenYAMM::Game::Mm9DtxTexture> texture =
            OpenYAMM::Game::loadMm9DtxTexture(*resolvedPath, errorMessage);
        if (!texture
            || texture->width == 0
            || texture->height == 0
            || texture->pixelsBgra.empty())
        {
            return std::nullopt;
        }

        OpenYAMM::Engine::ImagePixelsBgra pixels = {};
        pixels.width = static_cast<int>(texture->width);
        pixels.height = static_cast<int>(texture->height);
        pixels.pixels = texture->pixelsBgra;
        return pixels;
    }

    return OpenYAMM::Engine::loadImageAssetPixelsBgra(
        assetFileSystem,
        texturePath,
        binaryAssetCache);
}

std::string mm9GeneratedModelAssetPathFromSourceModelPath(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &resolvedSourcePath)
{
    const std::filesystem::path sourceModelsRoot =
        assetFileSystem.getDevelopmentRoot()
        / std::filesystem::path("worlds")
        / assetFileSystem.getActiveWorldId()
        / "source"
        / "models";
    std::filesystem::path relativePath =
        std::filesystem::path(resolvedSourcePath).lexically_relative(sourceModelsRoot);

    if (relativePath.empty() || relativePath.native().find("..") == 0)
    {
        relativePath = std::filesystem::path(resolvedSourcePath).filename();
    }

    relativePath.replace_extension(".glb");
    std::string normalized = lowerCopy(relativePath.generic_string());

    if (normalized.empty())
    {
        return {};
    }

    return (std::filesystem::path("models") / normalized).generic_string();
}

std::vector<std::string> mm9ModelInstanceAssetCandidates(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const OpenYAMM::Game::OutdoorSceneModelInstance &modelInstance,
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &rawObjectAssetStatuses)
{
    std::vector<std::string> candidates;
    const auto appendCandidate =
        [&candidates](const std::string &candidate)
        {
            if (!candidate.empty()
                && std::find(candidates.begin(), candidates.end(), candidate) == candidates.end())
            {
                candidates.push_back(candidate);
            }
        };

    appendCandidate(modelInstance.modelAsset);

    for (const EditorMm9RawObjectAssetReferenceStatus &status : rawObjectAssetStatuses)
    {
        if (status.sourceObjectIndex != modelInstance.sourceObjectIndex
            || status.sourceFamily != "models"
            || !status.resolved
            || status.ambiguous
            || status.resolvedSourcePath.empty())
        {
            continue;
        }

        appendCandidate(mm9GeneratedModelAssetPathFromSourceModelPath(assetFileSystem, status.resolvedSourcePath));
    }

    const std::string normalizedSourceModel = normalizeMm9ModelInstanceVirtualPath(modelInstance.sourceModel);
    if (!normalizedSourceModel.empty())
    {
        std::filesystem::path sourceModelPath(normalizedSourceModel);
        sourceModelPath.replace_extension(".glb");
        appendCandidate(sourceModelPath.generic_string());
    }

    return candidates;
}

bool resolveMm9ModelInstanceAssetCandidate(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const OpenYAMM::Game::OutdoorSceneModelInstance &modelInstance,
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &rawObjectAssetStatuses,
    std::string &resolvedAssetPath)
{
    const std::vector<std::string> candidates =
        mm9ModelInstanceAssetCandidates(assetFileSystem, modelInstance, rawObjectAssetStatuses);

    for (const std::string &candidate : candidates)
    {
        if (assetFileSystem.resolvePhysicalPath(candidate))
        {
            resolvedAssetPath = candidate;
            return true;
        }
    }

    resolvedAssetPath.clear();
    return false;
}

bool actorRowHasGameplayIdentity(const Mm9ResolvedModelInstanceActorSource::ActorRow &actorRow)
{
    return !actorRow.level.empty()
        || !actorRow.hitPoints.empty()
        || !actorRow.armorClass.empty()
        || !actorRow.experience.empty()
        || !actorRow.speed.empty()
        || !actorRow.scriptName.empty()
        || !actorRow.footSound.empty()
        || !actorRow.isMonster.empty()
        || !actorRow.hostilityGroup.empty()
        || !actorRow.voiceRadius.empty();
}

Mm9ModelInstanceAssetResolutionSummary summarizeMm9ModelInstanceAssetResolution(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapId,
    const OpenYAMM::Game::OutdoorSceneData &sceneData,
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &rawObjectAssetStatuses)
{
    Mm9ModelInstanceAssetResolutionSummary summary = {};
    OpenYAMM::Engine::BinaryAssetCache binaryAssetCache;
    const std::optional<Mm9ModelInstanceActorSourceLookup> actorSourceLookup =
        loadMm9ModelInstanceActorSourceLookup(assetFileSystem);

    summary.total = sceneData.modelInstances.size();

    for (const OpenYAMM::Game::OutdoorSceneModelInstance &modelInstance : sceneData.modelInstances)
    {
        const Mm9ResolvedModelInstanceActorSource resolvedSource =
            resolveMm9ModelInstanceActorSource(
                modelInstance,
                actorSourceLookup ? &*actorSourceLookup : nullptr);
        const bool requiresActorResolution =
            canResolveMm9ModelInstanceActorSource(
                modelInstance,
                actorSourceLookup ? &*actorSourceLookup : nullptr);
        const bool scriptedObject =
            requiresActorResolution
            || (!modelInstance.sourceModel.empty() && lowerCopy(modelInstance.sourceClass) != "prop");

        if (requiresActorResolution)
        {
            ++summary.actorVariantCandidates;

            if (resolvedSource.inferredFromActorClass)
            {
                ++summary.actorVariantResolved;

                if (!resolvedSource.actorRow.table.empty()
                    || !resolvedSource.actorRow.row.empty()
                    || !resolvedSource.actorRow.number.empty()
                    || !resolvedSource.actorRow.monsterName.empty()
                    || !resolvedSource.actorRow.typePicture.empty())
                {
                    ++summary.actorVariantActorRows;
                }

                if (actorRowHasGameplayIdentity(resolvedSource.actorRow))
                {
                    ++summary.actorVariantGameplayIdentityRows;
                }

                if (mm9ActorFootSoundRequiresResolution(resolvedSource.actorRow.footSound))
                {
                    ++summary.actorVariantFootSoundFields;
                    if (resolvedSource.actorRow.footSoundReferences.empty())
                    {
                        ++summary.actorVariantUnresolvedFootSounds;
                    }
                    else
                    {
                        ++summary.actorVariantResolvedFootSounds;
                    }
                }
            }
            else
            {
                ++summary.actorVariantUnresolved;

                Mm9ModelInstanceAssetResolutionSummary::UnresolvedActorVariant unresolved = {};
                unresolved.sourceObjectIndex = modelInstance.sourceObjectIndex;
                unresolved.sourceRef = modelInstance.sourceRef;
                unresolved.sourceClass = modelInstance.sourceClass;
                unresolved.sourceName = modelInstance.sourceName;
                unresolved.sourceModel = modelInstance.sourceModel;
                unresolved.sourceSkin = modelInstance.sourceSkin;
                summary.unresolvedActorVariants.push_back(std::move(unresolved));
            }

            for (const EditorMm9RawObjectAssetReferenceStatus &status : rawObjectAssetStatuses)
            {
                if (status.sourceObjectIndex != modelInstance.sourceObjectIndex
                    || (status.sourceFamily != "sounds" && status.sourceFamily != "voices"))
                {
                    continue;
                }

                const bool resolvedReference = status.resolved && !status.ambiguous;
                if (status.sourceFamily == "sounds")
                {
                    ++summary.actorVariantSourceSoundReferences;
                    if (resolvedReference)
                    {
                        ++summary.actorVariantResolvedSourceSoundReferences;
                    }
                    else
                    {
                        ++summary.actorVariantUnresolvedSourceSoundReferences;
                    }
                }
                else
                {
                    ++summary.actorVariantSourceVoiceReferences;
                    if (resolvedReference)
                    {
                        ++summary.actorVariantResolvedSourceVoiceReferences;
                    }
                    else
                    {
                        ++summary.actorVariantUnresolvedSourceVoiceReferences;
                    }
                }
            }
        }

        const std::string actorAssetPath =
            resolvedSource.inferredFromActorClass
                ? mm9ModelInstanceActorVariantAssetPath(resolvedSource.sourceModel, resolvedSource.sourceSkin)
                : std::string();
        std::string resolvedAssetPath;

        if (!actorAssetPath.empty() && assetFileSystem.resolvePhysicalPath(actorAssetPath))
        {
            resolvedAssetPath = actorAssetPath;
        }
        else
        {
            resolveMm9ModelInstanceAssetCandidate(
                assetFileSystem,
                modelInstance,
                rawObjectAssetStatuses,
                resolvedAssetPath);
        }

        if (scriptedObject)
        {
            ++summary.scriptedObjects;

            if (!resolvedAssetPath.empty())
            {
                ++summary.scriptedObjectsWithModelCollisionVolumes;
            }
            else
            {
                ++summary.scriptedObjectsRequiringBillboardCollisionVisuals;
                ++summary.missingScriptedObjectCollisionVisuals;
            }
        }

        if (resolvedAssetPath.empty())
        {
            ++summary.missingAssets;
        }
        else
        {
            ++summary.resolvedAssets;

            const std::optional<std::filesystem::path> resolvedPhysicalPath =
                assetFileSystem.resolvePhysicalPath(resolvedAssetPath);
            std::vector<ImportedModel> importedModels;
            std::string loadError;

            if (resolvedPhysicalPath
                && loadImportedModelsFromFile(*resolvedPhysicalPath, importedModels, loadError, false, false)
                && importedModelsHaveGeometry(importedModels))
            {
                ++summary.drawableGeometry;
            }
            else
            {
                ++summary.missingDrawableGeometry;
            }
        }

        for (const std::string &skinTexturePath : splitMm9ModelInstanceSourceSkinImages(resolvedSource.sourceSkin))
        {
            const std::optional<OpenYAMM::Engine::ImagePixelsBgra> pixels =
                loadMm9ModelTexturePixels(
                    assetFileSystem,
                    skinTexturePath,
                    binaryAssetCache);
            if (pixels && !pixels->pixels.empty())
            {
                ++summary.decodedSkinTextures;
            }
        }
    }

    return summary;
}

bool verifyOutdoorModelInstanceResolution(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    std::string &failure,
    size_t &inferredActorCount,
    size_t &verifiedAssetCount,
    size_t &scriptedObjectCount,
    size_t &collisionVisualCount)
{
    EditorSession session = {};
    session.initialize(assetFileSystem);

    if (!session.openOutdoorMap(mapFileName, failure))
    {
        failure = "could not load model instance resolution map " + mapFileName + ": " + failure;
        return false;
    }

    const OpenYAMM::Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();
    const OpenYAMM::Game::OutdoorMapData &outdoorGeometry = session.document().outdoorGeometry();
    inferredActorCount = 0;
    verifiedAssetCount = 0;
    scriptedObjectCount = 0;
    collisionVisualCount = 0;
    OpenYAMM::Engine::BinaryAssetCache binaryAssetCache;
    const std::optional<Mm9ModelInstanceActorSourceLookup> actorSourceLookup =
        loadMm9ModelInstanceActorSourceLookup(assetFileSystem);
    const bool isMm9Map =
        OpenYAMM::Game::normalizeWorldId(outdoorGeometry.worldId) == "mm9"
        || OpenYAMM::Game::normalizeWorldId(assetFileSystem.getActiveWorldId()) == "mm9";

    for (const OpenYAMM::Game::OutdoorSceneModelInstance &modelInstance : sceneData.modelInstances)
    {
        const Mm9ResolvedModelInstanceActorSource resolvedSource =
            resolveMm9ModelInstanceActorSource(
                modelInstance,
                actorSourceLookup ? &*actorSourceLookup : nullptr);
        const bool requiresActorResolution =
            canResolveMm9ModelInstanceActorSource(
                modelInstance,
                actorSourceLookup ? &*actorSourceLookup : nullptr);
        const bool scriptedObject =
            isMm9Map
            && (requiresActorResolution
                || (!modelInstance.sourceModel.empty() && lowerCopy(modelInstance.sourceClass) != "prop"));

        if (requiresActorResolution && !resolvedSource.inferredFromActorClass)
        {
            failure = "model instance " + modelInstance.sourceRef
                + " kept unresolved actor placeholder model " + modelInstance.sourceModel
                + " class=" + modelInstance.sourceClass
                + " name=" + modelInstance.sourceName;
            return false;
        }

        if (scriptedObject)
        {
            ++scriptedObjectCount;
        }

        if (!resolvedSource.inferredFromActorClass)
        {
            continue;
        }

        ++inferredActorCount;

        const std::string resolvedAssetPath =
            mm9ModelInstanceActorVariantAssetPath(resolvedSource.sourceModel, resolvedSource.sourceSkin);
        if (resolvedAssetPath.empty())
        {
            failure = "model instance " + modelInstance.sourceRef + " did not produce a variant asset path";
            return false;
        }

        const std::optional<std::filesystem::path> resolvedPhysicalPath =
            assetFileSystem.resolvePhysicalPath(resolvedAssetPath);
        if (!resolvedPhysicalPath)
        {
            failure = "model instance " + modelInstance.sourceRef
                + " resolved to missing actor model asset " + resolvedAssetPath;
            return false;
        }

        std::vector<ImportedModel> importedModels;
        std::string loadError;
        if (!loadImportedModelsFromFile(*resolvedPhysicalPath, importedModels, loadError, false, false)
            || !importedModelsHaveGeometry(importedModels))
        {
            failure = "model instance " + modelInstance.sourceRef
                + " resolved actor model has no loadable geometry " + resolvedAssetPath
                + " (" + loadError + ")";
            return false;
        }

        for (const std::string &skinTexturePath : splitMm9ModelInstanceSourceSkinImages(resolvedSource.sourceSkin))
        {
            if (!resolveMm9ModelTexturePhysicalPath(assetFileSystem, skinTexturePath))
            {
                failure = "model instance " + modelInstance.sourceRef
                    + " resolved to missing actor skin texture " + skinTexturePath;
                return false;
            }

            const std::optional<OpenYAMM::Engine::ImagePixelsBgra> skinPixels =
                loadMm9ModelTexturePixels(
                    assetFileSystem,
                    skinTexturePath,
                    binaryAssetCache);
            if (!skinPixels || skinPixels->pixels.empty() || !imageHasVisibleAlpha(*skinPixels))
            {
                failure = "model instance " + modelInstance.sourceRef
                    + " resolved to fully transparent actor skin texture " + skinTexturePath;
                return false;
            }
        }

        if (scriptedObject)
        {
            ++collisionVisualCount;
        }

        ++verifiedAssetCount;
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

    bool hasLegacyCompanionFile = false;
    bool hasOutdoorSceneKind = false;
    std::string line;

    while (std::getline(input, line))
    {
        if (line.find("legacy_companion_file:") != std::string::npos)
        {
            hasLegacyCompanionFile = true;
        }

        if (line.find("kind:") != std::string::npos && line.find("outdoor_scene") != std::string::npos)
        {
            hasOutdoorSceneKind = true;
        }
    }

    return hasLegacyCompanionFile && hasOutdoorSceneKind;
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
    removeTemporaryRowsFromTable(assetFileSystem.getEditorDevelopmentRoot() / "engine/data_tables/map_stats.txt", 2);
    removeTemporaryRowsFromTable(assetFileSystem.getEditorDevelopmentRoot() / "engine/data_tables/map_navigation.txt", 0);
    const std::filesystem::path scriptsPath = activeWorldEditorPath(assetFileSystem, "events/maps");

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
    const bool runEditorWorldOutdoorTerrainChecks = suiteName == "editor-world-outdoor-terrain-load";
    const bool runEditorWorldMapScriptChecks = suiteName == "editor-world-map-script-load";
    const bool runMm9ModelInstanceResolutionChecks = suiteName == "mm9-model-instance-resolution";
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
        || runSpriteObjectPlacementChecks
        || runEditorWorldOutdoorTerrainChecks
        || runEditorWorldMapScriptChecks
        || runMm9ModelInstanceResolutionChecks;

    if (!runRoundTripChecks)
    {
        std::cerr << "Unknown editor regression suite: " << suiteName << '\n';
        return 2;
    }

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(
            basePath,
            m_config.assetRoot,
            m_config.assetScaleTier,
            m_config.assetScaleProfile,
            m_config.activeWorldId))
    {
        std::cerr << "Editor headless diagnostics failed: could not initialize asset file system\n";
        return 1;
    }

    const std::filesystem::path gamesPath = activeWorldEditorPath(assetFileSystem, "maps");

    if (!std::filesystem::exists(gamesPath))
    {
        std::cerr << "Editor headless diagnostics failed: games directory not found: " << gamesPath << '\n';
        return 1;
    }

    removeTemporaryRoundTripScenes(gamesPath);
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

    if (runEditorWorldOutdoorTerrainChecks)
    {
        std::string failure;

        if (!verifyEditorWorldOutdoorTerrainLoad(assetFileSystem, failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        std::cout << "Editor headless regression: suite=" << suiteName << " maps=1\n";
        std::cout << "  pass oute3.odm\n";
        std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
        removeTemporaryRoundTripScenes(activeWorldEditorPath(assetFileSystem, "maps"));
        removeTemporaryRoundTripSupportFiles(assetFileSystem);
        return 0;
    }

    if (runEditorWorldMapScriptChecks)
    {
        std::string failure;

        if (!verifyEditorWorldMapScriptLoad(assetFileSystem, failure))
        {
            std::cerr << "Editor headless regression failed: " << failure << '\n';
            return 1;
        }

        std::cout << "Editor headless regression: suite=" << suiteName << " maps=4\n";
        std::cout << "  pass mm6/oute3.odm\n";
        std::cout << "  pass mm7/out09.lua\n";
        std::cout << "  pass mm7/7d06.blv\n";
        std::cout << "  pass mm8/out01.odm\n";
        std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
        removeTemporaryRoundTripScenes(activeWorldEditorPath(assetFileSystem, "maps"));
        removeTemporaryRoundTripSupportFiles(assetFileSystem);
        return 0;
    }

    if (runMm9ModelInstanceResolutionChecks)
    {
        std::array<std::string, 4> mapFileNames = {{
            "guberland.odm",
            "guberlandcity.odm",
            "thjorgard.odm",
            "thjorgardcity.odm"
        }};

        std::cout << "Editor headless regression: suite=" << suiteName
                  << " maps=" << mapFileNames.size() << '\n';

        for (const std::string &mapFileName : mapFileNames)
        {
            std::string failure;
            size_t inferredActorCount = 0;
            size_t verifiedAssetCount = 0;
            size_t scriptedObjectCount = 0;
            size_t collisionVisualCount = 0;

            if (!verifyOutdoorModelInstanceResolution(
                    assetFileSystem,
                    mapFileName,
                    failure,
                    inferredActorCount,
                    verifiedAssetCount,
                    scriptedObjectCount,
                    collisionVisualCount))
            {
                std::cerr << "Editor headless regression failed: " << failure << '\n';
                return 1;
            }

            std::cout << "  pass " << mapFileName
                      << " inferred=" << inferredActorCount
                      << " verified_assets=" << verifiedAssetCount
                      << " scripted_objects=" << scriptedObjectCount
                      << " collision_visuals=" << collisionVisualCount << '\n';
        }

        std::cout << "Editor headless regression passed: suite=" << suiteName << '\n';
        removeTemporaryRoundTripScenes(activeWorldEditorPath(assetFileSystem, "maps"));
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

    if (!assetFileSystem.initialize(
            basePath,
            m_config.assetRoot,
            m_config.assetScaleTier,
            m_config.assetScaleProfile,
            m_config.activeWorldId))
    {
        std::cerr << "Editor headless diagnostics failed: could not initialize asset file system\n";
        return 1;
    }

    removeTemporaryRoundTripScenes(activeWorldEditorPath(assetFileSystem, "maps"));
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
    removeTemporaryRoundTripScenes(activeWorldEditorPath(assetFileSystem, "maps"));
    removeTemporaryRoundTripSupportFiles(assetFileSystem);
    return 0;
}

int EditorHeadlessDiagnostics::runVerifyModelInstances(
    const std::filesystem::path &basePath,
    const std::string &mapFileName) const
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(
            basePath,
            m_config.assetRoot,
            m_config.assetScaleTier,
            m_config.assetScaleProfile,
            m_config.activeWorldId))
    {
        std::cerr << "Editor headless diagnostics failed: could not initialize asset file system\n";
        return 1;
    }

    std::string failure;
    size_t inferredActorCount = 0;
    size_t verifiedAssetCount = 0;
    size_t scriptedObjectCount = 0;
    size_t collisionVisualCount = 0;

    if (!verifyOutdoorModelInstanceResolution(
            assetFileSystem,
            mapFileName,
            failure,
            inferredActorCount,
            verifiedAssetCount,
            scriptedObjectCount,
            collisionVisualCount))
    {
        std::cerr << "Editor headless model instance resolution failed: " << failure << '\n';
        return 1;
    }

    std::cout << "Editor headless model instance resolution passed: " << mapFileName
              << " inferred=" << inferredActorCount
              << " verified_assets=" << verifiedAssetCount
              << " scripted_objects=" << scriptedObjectCount
              << " collision_visuals=" << collisionVisualCount << '\n';
    return 0;
}

int EditorHeadlessDiagnostics::runVerifyMm9DatLevel(
    const std::filesystem::path &basePath,
    const std::string &levelFileName) const
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(
            basePath,
            m_config.assetRoot,
            m_config.assetScaleTier,
            m_config.assetScaleProfile,
            m_config.activeWorldId))
    {
        std::cerr << "Editor headless diagnostics failed: could not initialize asset file system\n";
        return 1;
    }

    std::filesystem::path levelPath =
        activeWorldEditorPath(assetFileSystem, std::filesystem::path("maps") / levelFileName);

    if (!std::filesystem::exists(levelPath))
    {
        levelPath = assetFileSystem.getDevelopmentRoot()
            / std::filesystem::path("worlds")
            / assetFileSystem.getActiveWorldId()
            / "maps"
            / levelFileName;
    }

    const Mm9SourceIntegritySnapshot sourceIntegrityBefore =
        collectMm9SourceIntegritySnapshot(levelPath);

    EditorDocument document;
    std::string failure;

    if (!document.loadMapPhysicalPath(assetFileSystem, levelPath, failure))
    {
        std::cerr << "Editor headless MM9 DAT level failed: " << failure << '\n';
        return 1;
    }

    if (document.kind() != EditorDocument::Kind::Mm9Dat)
    {
        std::cerr << "Editor headless MM9 DAT level failed: document kind is not Mm9Dat\n";
        return 1;
    }

    if (!document.hasMm9DatLoadedSidecars())
    {
        std::cerr << "Editor headless MM9 DAT level failed: sidecars were not loaded\n";
        return 1;
    }

    if (!document.hasMm9DatWorld() || document.mm9DatRenderMesh().triangles.empty())
    {
        std::cerr << "Editor headless MM9 DAT level failed: source DAT world render mesh was not built\n";
        return 1;
    }

    const std::vector<std::string> diagnostics = document.validate();

    if (!diagnostics.empty())
    {
        std::cerr << "Editor headless MM9 DAT level failed: validation diagnostics:\n";

        for (const std::string &diagnostic : diagnostics)
        {
            std::cerr << "  " << diagnostic << '\n';
        }

        return 1;
    }

    const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
    const Game::Mm9DatRenderMesh &datRenderMesh = document.mm9DatRenderMesh();
    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();
    const Mm9MechanismValidationSummary mechanismSummary =
        summarizeMm9Mechanisms(sidecars.events, sidecars.datWorld);
    const std::vector<EditorMm9MaterialTextureStatus> &textureStatuses =
        document.mm9MaterialTextureStatuses();
    const std::vector<EditorMm9DocumentPathStatus> &pathStatuses = document.mm9DocumentPathStatuses();
    size_t readOnlySourcePathCount = 0;
    size_t generatedPathCount = 0;
    size_t authoredPathCount = 0;
    size_t authoredOverridePathCount = 0;
    size_t compatibilityPathCount = 0;
    size_t resolvedTextureCount = 0;
    size_t ambiguousTextureCount = 0;
    size_t loadedDtxHeaderCount = 0;
    size_t matchedDtxHeaderCount = 0;
    size_t dtxMipPayloadCount = 0;
    size_t dtxDecodedPreviewMipCount = 0;
    size_t dtxSectionMetadataCount = 0;
    size_t dtxSectionPayloadAvailableCount = 0;
    size_t dtxCommandStringCount = 0;
    size_t cacheTextureCount = 0;
    size_t sourceDtxHashCount = 0;
    size_t cacheHashCount = 0;
    size_t staleCacheCount = 0;
    size_t decodedCacheDeterminismCheckedCount = 0;
    size_t decodedCacheMatchCount = 0;
    size_t physicsBspCount = 0;
    size_t visBspCount = 0;
    size_t decodedPBlockCount = 0;
    size_t rawObjectAssetReferenceCount = 0;
    size_t optionalRawObjectAssetReferenceCount = 0;
    size_t unresolvedRawObjectAssetReferenceCount = 0;
    size_t unresolvedOptionalRawObjectAssetReferenceCount = 0;
    size_t assignedNativeMaterialCount = 0;
    size_t nativeMaterialPreviewCount = 0;
    size_t invalidSurfaceTextureRefs = 0;
    size_t invalidPolySurfaceRefs = 0;
    size_t invalidPolyPlaneRefs = 0;
    size_t invalidPolyVertexRefs = 0;
    size_t invalidNodePolyRefs = 0;
    size_t invalidRootNodeRefs = 0;
    size_t worldModelsWithUnknownValues = 0;
    size_t userPortalsWithRawUnknowns = 0;
    size_t scriptIncludes = 0;
    size_t scriptLabels = 0;
    size_t scriptRegisteredTriggers = 0;
    size_t scriptTriggerEdges = 0;
    size_t scriptMovementCommands = 0;
    size_t scriptUnknownCommands = 0;
    size_t scriptCommandCount = 0;
    size_t unresolvedEventWarnings = 0;
    size_t unresolvedEventErrors = 0;
    size_t unresolvedEventRotationCandidates = 0;
    size_t unresolvedEventPositionCandidates = 0;
    const std::vector<std::string> datWorldReferenceIssues =
        validateMm9DatWorldSidecarReferences(sidecars.datWorld);
    const std::vector<std::string> rawObjectSidecarIssues =
        validateMm9RawObjectsSidecarReferences(sidecars.rawObjects);
    const std::vector<EditorMm9SourceAssetFamilyStatus> &sourceFamilyStatuses =
        document.mm9SourceAssetFamilyStatuses();
    size_t sourceFamilyExpectedFileCount = 0;
    size_t sourceFamilyActualFileCount = 0;
    size_t sourceFamilyCountDriftCount = 0;
    size_t sourceFamilyMissingDirectoryCount = 0;
    size_t sourceDatHashDiagnosticCount = 0;
    const EditorMm9AssetDependencySummary &assetSummary = document.mm9AssetDependencySummary();
    const EditorMm9ScriptIncludeResolutionSummary scriptIncludeSummary =
        summarizeMm9EventScriptIncludeResolution(levelPath, sidecars.events);

    if (document.mm9DatWorld().worldModels.size() != sidecars.datWorld.worldModels.size())
    {
        std::cerr << "Editor headless MM9 DAT level failed: parsed DAT world model count does not match sidecar\n";
        return 1;
    }

    if (datRenderMesh.sourcePolyCount != sidecars.datWorld.totals.sourcePolyCount)
    {
        std::cerr << "Editor headless MM9 DAT level failed: parsed DAT source poly count does not match sidecar\n";
        return 1;
    }

    if (document.mm9DatRenderMaterialAssignments().size() != datRenderMesh.triangles.size())
    {
        std::cerr << "Editor headless MM9 DAT level failed: native material assignment count does not match mesh\n";
        return 1;
    }

    if (!datWorldReferenceIssues.empty())
    {
        std::cerr << "Editor headless MM9 DAT level failed: DAT world sidecar reference issues remain:\n";

        for (const std::string &issue : datWorldReferenceIssues)
        {
            std::cerr << "  " << issue << '\n';
        }

        return 1;
    }

    if (!rawObjectSidecarIssues.empty())
    {
        std::cerr << "Editor headless MM9 DAT level failed: raw object sidecar issues remain:\n";

        for (const std::string &issue : rawObjectSidecarIssues)
        {
            std::cerr << "  " << issue << '\n';
        }

        return 1;
    }

    for (const std::string &diagnostic : document.mm9DatLevelLoadDiagnostics())
    {
        if (diagnostic.find("source DAT hash") != std::string::npos)
        {
            ++sourceDatHashDiagnosticCount;
        }
    }

    for (const OpenYAMM::Game::Mm9EventScript &script : sidecars.events.scripts)
    {
        scriptIncludes += script.includes.size();
        scriptLabels += script.labels.size();
        scriptRegisteredTriggers += script.registeredTriggers.size();
        scriptTriggerEdges += script.triggerEdges.size();
        scriptMovementCommands += script.movementCommands.size();
        scriptUnknownCommands += script.unknownCommands.size();
        scriptCommandCount += script.commandCount;
    }

    for (const OpenYAMM::Game::Mm9EventUnresolved &entry : sidecars.events.unresolved)
    {
        const std::string severity = lowerAsciiCopy(entry.severity);

        if (severity == "error")
        {
            ++unresolvedEventErrors;
        }
        else if (severity == "warning")
        {
            ++unresolvedEventWarnings;
        }

        unresolvedEventRotationCandidates += entry.nearestMovableWorldModelsByRotationPoint.size();
        unresolvedEventPositionCandidates += entry.nearestMovableWorldModelsByPosition.size();
    }

    for (const EditorMm9SourceAssetFamilyStatus &status : sourceFamilyStatuses)
    {
        sourceFamilyExpectedFileCount += status.expectedFileCount;
        sourceFamilyActualFileCount += status.actualFileCount;

        if (status.declared && !status.packageDirectoryExists)
        {
            ++sourceFamilyMissingDirectoryCount;
        }

        if (status.declared && status.expectedFileCount != status.actualFileCount)
        {
            ++sourceFamilyCountDriftCount;
        }
    }

    if (sidecars.materialAliases.stats.modelInstances != 0
        && sceneData.modelInstances.size() != sidecars.materialAliases.stats.modelInstances)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: object-derived model instance count does not match sidecar"
            << " expected=" << sidecars.materialAliases.stats.modelInstances
            << " loaded=" << sceneData.modelInstances.size() << '\n';
        return 1;
    }

    const Mm9ModelInstanceAssetResolutionSummary modelInstanceSummary =
        summarizeMm9ModelInstanceAssetResolution(
            assetFileSystem,
            document.mm9DatLevelMetadata().mapId,
            sceneData,
            document.mm9RawObjectAssetReferenceStatuses());
    const Mm9MechanismPreviewValidationSummary mechanismPreviewSummary =
        validateMm9MechanismPreviewTransforms(sidecars.events, datRenderMesh);
    const Game::Mm9DatCameraFrame nativeCameraFrame = Game::frameMm9DatRenderMeshCamera(datRenderMesh);
    const size_t worldModelOverlayVertices = countMm9WorldModelOverlayVertices(sidecars.datWorld);
    const size_t worldModelOverlayPickCandidates = countMm9WorldModelOverlayPickCandidates(sidecars.datWorld);
    const size_t objectOverlayVertices = countMm9ObjectOverlayVertices(document.mm9ObjectLayer());
    const size_t objectOverlayPickCandidates =
        countMm9ObjectOverlayPickCandidates(document.mm9ObjectLayer(), sidecars.rawObjects);
    const Mm9SourceMarkerOverlaySummary sourceMarkerOverlaySummary =
        summarizeMm9SourceMarkerOverlayVertices(
            document.mm9LightLayer(),
            document.mm9SoundLayer(),
            document.mm9SpawnLayer());
    const Mm9MechanismTargetMarkerSummary mechanismTargetMarkerSummary =
        summarizeMm9MechanismTargetMarkers(
            sidecars.events,
            sidecars.datWorld,
            document.mm9ObjectLayer(),
            document.mm9LightLayer(),
            document.mm9SoundLayer(),
            document.mm9SpawnLayer(),
            sceneData,
            nativeCameraFrame);

    if (modelInstanceSummary.total != 0 && modelInstanceSummary.missingAssets != 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: object-derived model instances have unresolved model assets"
            << " total=" << modelInstanceSummary.total
            << " resolved=" << modelInstanceSummary.resolvedAssets
            << " missing=" << modelInstanceSummary.missingAssets << '\n';
        return 1;
    }

    if (modelInstanceSummary.total != 0 && modelInstanceSummary.missingDrawableGeometry != 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: object-derived model instances have no drawable geometry"
            << " total=" << modelInstanceSummary.total
            << " drawable=" << modelInstanceSummary.drawableGeometry
            << " missing_geometry=" << modelInstanceSummary.missingDrawableGeometry << '\n';
        return 1;
    }

    if (mechanismPreviewSummary.candidates != 0
        && mechanismPreviewSummary.changedBounds == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: mechanism preview transforms did not change target bounds"
            << " candidates=" << mechanismPreviewSummary.candidates
            << " target_found=" << mechanismPreviewSummary.targetFound
            << " transformed_triangles=" << mechanismPreviewSummary.transformedTriangles << '\n';
        return 1;
    }

    if (!sidecars.datWorld.worldModels.empty() && worldModelOverlayVertices == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: world model bounds overlay has no vertices"
            << " world_models=" << sidecars.datWorld.worldModels.size() << '\n';
        return 1;
    }

    if (worldModelOverlayVertices != 0 && worldModelOverlayPickCandidates == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: world model bounds overlay has no pick candidates"
            << " overlay_vertices=" << worldModelOverlayVertices << '\n';
        return 1;
    }

    if (document.mm9ObjectLayer().boundsEvidenceObjectCount != 0 && objectOverlayVertices == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: object bounds overlay has no vertices"
            << " bounds_evidence=" << document.mm9ObjectLayer().boundsEvidenceObjectCount << '\n';
        return 1;
    }

    if (objectOverlayVertices != 0 && objectOverlayPickCandidates == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: object bounds overlay has no raw-object pick candidates"
            << " overlay_vertices=" << objectOverlayVertices << '\n';
        return 1;
    }

    if (!document.mm9LightLayer().lights.empty() && sourceMarkerOverlaySummary.lightVertices == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: light source overlay has no vertices"
            << " light_objects=" << document.mm9LightLayer().lights.size() << '\n';
        return 1;
    }

    if (!document.mm9SoundLayer().objects.empty() && sourceMarkerOverlaySummary.soundVertices == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: sound source overlay has no vertices"
            << " sound_objects=" << document.mm9SoundLayer().objects.size() << '\n';
        return 1;
    }

    if (!document.mm9SpawnLayer().objects.empty() && sourceMarkerOverlaySummary.spawnVertices == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: spawn source overlay has no vertices"
            << " spawn_source_objects=" << document.mm9SpawnLayer().objects.size() << '\n';
        return 1;
    }

    if (mechanismPreviewSummary.candidates != 0 && mechanismTargetMarkerSummary.vertices == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: mechanism target overlay has no vertices"
            << " preview_candidates=" << mechanismPreviewSummary.candidates << '\n';
        return 1;
    }

    if (!sidecars.events.mechanisms.empty()
        && mechanismTargetMarkerSummary.circleGizmoCandidates < sidecars.events.mechanisms.size())
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: mechanism overlay has no selectable circle gizmo"
            << " mechanisms=" << sidecars.events.mechanisms.size()
            << " circle_gizmos=" << mechanismTargetMarkerSummary.circleGizmoCandidates << '\n';
        return 1;
    }

    if (mechanismTargetMarkerSummary.targetGroups != 0
        && mechanismTargetMarkerSummary.targetGizmoCandidates < mechanismTargetMarkerSummary.targetGroups)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: mechanism target markers have no selectable target gizmo"
            << " target_groups=" << mechanismTargetMarkerSummary.targetGroups
            << " target_gizmos=" << mechanismTargetMarkerSummary.targetGizmoCandidates << '\n';
        return 1;
    }

    if (mechanismPreviewSummary.candidates != 0
        && mechanismTargetMarkerSummary.motionPathMarkers < mechanismPreviewSummary.candidates)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: mechanism previewable targets have no motion path markers"
            << " preview_candidates=" << mechanismPreviewSummary.candidates
            << " motion_paths=" << mechanismTargetMarkerSummary.motionPathMarkers << '\n';
        return 1;
    }

    if (nativeCameraFrame.valid
        && mechanismTargetMarkerSummary.targetGizmoCandidates != 0
        && mechanismTargetMarkerSummary.lineOfSightCheckedCandidates
            != mechanismTargetMarkerSummary.targetGizmoCandidates)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: mechanism target gizmos did not get LoS fade checks"
            << " target_gizmos=" << mechanismTargetMarkerSummary.targetGizmoCandidates
            << " los_checked=" << mechanismTargetMarkerSummary.lineOfSightCheckedCandidates << '\n';
        return 1;
    }

    const Game::Mm9DatRenderBounds nativeBounds = Game::computeMm9DatRenderBounds(datRenderMesh);
    const Mm9ModelInstanceCameraFrameSummary modelInstanceCameraFrameSummary =
        summarizeMm9ModelInstanceCameraFrame(sceneData, nativeCameraFrame, 60.0f, 1920.0f / 1200.0f);
    const Game::Mm9DatRenderFilterResult nativeFilters =
        Game::classifyMm9DatRenderMeshFilters(
            datRenderMesh,
            mm9ModelRenderRolesFromSidecar(sidecars.datWorld),
            sidecars.datWorld.userPortals.size());
    const Mm9DatViewportRenderabilitySummary viewportSummary =
        summarizeMm9DatViewportRenderability(
            nativeFilters,
            document.mm9DatRenderMaterialAssignments(),
            modelInstanceSummary);

    if (!nativeBounds.valid || !nativeCameraFrame.valid)
    {
        std::cerr << "Editor headless MM9 DAT level failed: native DAT camera frame could not be built\n";
        return 1;
    }

    if (nativeFilters.entries.size() != datRenderMesh.triangles.size()
        || nativeFilters.summary.totalTriangles != datRenderMesh.triangles.size()
        || nativeFilters.summary.unclassifiedTriangles != 0)
    {
        std::cerr << "Editor headless MM9 DAT level failed: native DAT display filters are incomplete\n";
        return 1;
    }

    if (viewportSummary.nativeRenderableTriangles == 0)
    {
        std::cerr << "Editor headless MM9 DAT level failed: viewport preflight has no renderable native DAT triangles\n";
        return 1;
    }

    if (viewportSummary.nativeTexturedTriangles == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: viewport preflight has no native DAT source-DTX materials"
            << " renderable=" << viewportSummary.nativeRenderableTriangles
            << " textured=" << viewportSummary.nativeTexturedTriangles
            << " missing=" << viewportSummary.nativeMissingMaterialTriangles << '\n';
        return 1;
    }

    if (viewportSummary.nativeUnresolvedMaterialTriangles != 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: viewport preflight has unresolved native DAT materials"
            << " renderable=" << viewportSummary.nativeRenderableTriangles
            << " textured=" << viewportSummary.nativeTexturedTriangles
            << " missing=" << viewportSummary.nativeMissingMaterialTriangles
            << " placeholder=" << viewportSummary.nativePlaceholderMaterialTriangles
            << " unresolved=" << viewportSummary.nativeUnresolvedMaterialTriangles << '\n';
        return 1;
    }

    if (modelInstanceSummary.total != 0
        && (viewportSummary.modelInstanceDrawableGeometry == 0
            || viewportSummary.modelInstanceDecodedSkinTextures == 0))
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: viewport preflight has incomplete model-instance draw inputs"
            << " model_instances=" << modelInstanceSummary.total
            << " drawable_geometry=" << viewportSummary.modelInstanceDrawableGeometry
            << " decoded_skin_textures=" << viewportSummary.modelInstanceDecodedSkinTextures << '\n';
        return 1;
    }

    if (modelInstanceSummary.total != 0 && modelInstanceCameraFrameSummary.inView == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: default native DAT camera frame sees no model instances"
            << " model_instances=" << modelInstanceSummary.total
            << " in_front=" << modelInstanceCameraFrameSummary.inFront
            << " in_depth_range=" << modelInstanceCameraFrameSummary.inDepthRange << '\n';
        return 1;
    }

    for (const EditorMm9DocumentPathStatus &status : pathStatuses)
    {
        if (status.sourceReadOnly)
        {
            ++readOnlySourcePathCount;

            if (!status.exists)
            {
                std::cerr
                    << "Editor headless MM9 DAT level failed: read-only source path is missing: "
                    << status.resolvedPath << '\n';
                return 1;
            }
        }

        if (status.generated)
        {
            ++generatedPathCount;
        }

        if (status.authored)
        {
            ++authoredPathCount;
        }

        if (status.role == "authored_override")
        {
            ++authoredOverridePathCount;
        }

        if (status.compatibilityDerived)
        {
            ++compatibilityPathCount;
        }
    }

    for (const EditorMm9MaterialTextureStatus &status : textureStatuses)
    {
        if (status.sourceDtxResolved)
        {
            ++resolvedTextureCount;
        }

        if (status.sourceDtxAmbiguous)
        {
            ++ambiguousTextureCount;
        }

        if (status.dtxHeaderLoaded)
        {
            ++loadedDtxHeaderCount;
        }

        if (status.dtxHeaderMatchesSidecar)
        {
            ++matchedDtxHeaderCount;
        }

        if (status.dtxHeader)
        {
            dtxMipPayloadCount += status.dtxHeader->mips.size();
            dtxSectionMetadataCount += status.dtxHeader->sections.size();

            if (!status.dtxHeader->commandString.empty())
            {
                ++dtxCommandStringCount;
            }

            for (const EditorMm9DtxMipLevel &mip : status.dtxHeader->mips)
            {
                if (mip.decodedPreviewAvailable)
                {
                    ++dtxDecodedPreviewMipCount;
                }
            }

            for (const EditorMm9DtxSection &section : status.dtxHeader->sections)
            {
                if (section.payloadAvailable)
                {
                    ++dtxSectionPayloadAvailableCount;
                }
            }
        }

        if (status.cachePathExists)
        {
            ++cacheTextureCount;
        }

        if (status.sourceDtxHashLoaded)
        {
            ++sourceDtxHashCount;
        }

        if (status.cacheHashLoaded)
        {
            ++cacheHashCount;
        }

        if (status.cacheOlderThanSource)
        {
            ++staleCacheCount;
        }

        if (status.cacheDeterminismChecked)
        {
            ++decodedCacheDeterminismCheckedCount;

            if (status.cacheMatchesDecodedSource)
            {
                ++decodedCacheMatchCount;
            }
        }
    }

    for (const EditorMm9RawObjectAssetReferenceStatus &status : document.mm9RawObjectAssetReferenceStatuses())
    {
        ++rawObjectAssetReferenceCount;

        if (!status.required)
        {
            ++optionalRawObjectAssetReferenceCount;
        }

        if (!status.resolved || status.ambiguous)
        {
            if (status.required)
            {
                ++unresolvedRawObjectAssetReferenceCount;
            }
            else
            {
                ++unresolvedOptionalRawObjectAssetReferenceCount;
            }
        }
    }

    for (const Game::Mm9DatRenderMaterialAssignment &assignment : document.mm9DatRenderMaterialAssignments())
    {
        if (!assignment.assigned || assignment.ambiguous)
        {
            std::cerr
                << "Editor headless MM9 DAT level failed: native mesh triangle has no unique material alias: "
                << assignment.sourceTexture << '\n';
            return 1;
        }

        ++assignedNativeMaterialCount;

        if (assignment.previewCacheAvailable)
        {
            ++nativeMaterialPreviewCount;
        }
    }

    for (const EditorMm9DatWorldModelSummary &model : sidecars.datWorld.worldModels)
    {
        invalidSurfaceTextureRefs += model.referenceValidation.invalidSurfaceTextureRefs;
        invalidPolySurfaceRefs += model.referenceValidation.invalidPolySurfaceRefs;
        invalidPolyPlaneRefs += model.referenceValidation.invalidPolyPlaneRefs;
        invalidPolyVertexRefs += model.referenceValidation.invalidPolyVertexRefs;
        invalidNodePolyRefs += model.referenceValidation.invalidNodePolyRefs;
        invalidRootNodeRefs += model.referenceValidation.invalidRootNodeRefs;

        if (model.unknownValues.worldBspUnknownValue != 0
            || model.unknownValues.worldBspUnknownValue2 != 0
            || model.unknownValues.worldBspUnknownValue3 != 0)
        {
            ++worldModelsWithUnknownValues;
        }

        if (model.roles.physicsBsp)
        {
            ++physicsBspCount;
        }

        if (model.roles.visBsp)
        {
            ++visBspCount;
        }

        if (model.pblockTable.decodedSummary && model.pblockTable.recordCount)
        {
            ++decodedPBlockCount;
        }
    }

    for (const EditorMm9DatUserPortalSummary &portal : sidecars.datWorld.userPortals)
    {
        if (portal.rawUnknowns.unknownInt1 != 0 || portal.rawUnknowns.unknownShort != 0)
        {
            ++userPortalsWithRawUnknowns;
        }
    }

    if (physicsBspCount != 0 && nativeFilters.summary.physicsTriangles == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: PhysicsBSP models produced no physics-filter triangles"
            << " physics_bsp_models=" << physicsBspCount << '\n';
        return 1;
    }

    if (visBspCount != 0 && nativeFilters.summary.visibilityTriangles == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: VisBSP models produced no visibility-filter triangles"
            << " vis_bsp_models=" << visBspCount << '\n';
        return 1;
    }

    if (nativeFilters.summary.helperTriangles
        < nativeFilters.summary.physicsTriangles + nativeFilters.summary.visibilityTriangles)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: helper triangle count does not preserve helper BSP roles"
            << " helper=" << nativeFilters.summary.helperTriangles
            << " physics=" << nativeFilters.summary.physicsTriangles
            << " visibility=" << nativeFilters.summary.visibilityTriangles << '\n';
        return 1;
    }

    if (readOnlySourcePathCount < 2 || generatedPathCount == 0 || authoredPathCount == 0
        || compatibilityPathCount == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: incomplete document path role inventory"
            << " read_only_source=" << readOnlySourcePathCount
            << " generated=" << generatedPathCount
            << " authored=" << authoredPathCount
            << " compatibility=" << compatibilityPathCount << '\n';
        return 1;
    }

    const EditorMm9DatLevelMetadata &metadata = document.mm9DatLevelMetadata();

    if (metadata.sidecars.sourceAssetAliases && authoredOverridePathCount == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: source asset aliases sidecar is not classified as an"
            << " authored override\n";
        return 1;
    }

    std::string saveFailure;

    if (document.saveSource(saveFailure)
        || saveFailure.find("source/* immutable") == std::string::npos)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: MM9 saveSource did not reject source mutation: "
            << saveFailure << '\n';
        return 1;
    }

    std::string saveFailureViaAlias;

    if (document.save(saveFailureViaAlias)
        || saveFailureViaAlias.find("source/* immutable") == std::string::npos)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: MM9 save did not reject source mutation: "
            << saveFailureViaAlias << '\n';
        return 1;
    }

    const std::filesystem::path rejectedSaveAsPath =
        document.scenePhysicalPath().parent_path() / "__openyamm_mm9_rejected_save_as.level.yml";

    if (std::filesystem::exists(rejectedSaveAsPath))
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: rejected save-as sentinel already exists: "
            << rejectedSaveAsPath.generic_string() << '\n';
        return 1;
    }

    std::string saveSourceAsFailure;

    if (document.saveSourceAs(rejectedSaveAsPath, saveSourceAsFailure)
        || saveSourceAsFailure.find("source/* immutable") == std::string::npos
        || std::filesystem::exists(rejectedSaveAsPath))
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: MM9 saveSourceAs did not reject source mutation: "
            << saveSourceAsFailure << '\n';
        return 1;
    }

    std::string saveAsFailure;

    if (document.saveAs(rejectedSaveAsPath, saveAsFailure)
        || saveAsFailure.find("source/* immutable") == std::string::npos
        || std::filesystem::exists(rejectedSaveAsPath))
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: MM9 saveAs did not reject source mutation: "
            << saveAsFailure << '\n';
        return 1;
    }

    std::string buildFailure;

    if (document.buildRuntime(buildFailure)
        || buildFailure.find("DAT/DTX runtime path") == std::string::npos)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: MM9 buildRuntime did not reject ODM/BLV build: "
            << buildFailure << '\n';
        return 1;
    }

    std::string buildRuntimeAsFailure;

    if (document.buildRuntimeAs(rejectedSaveAsPath, buildRuntimeAsFailure)
        || buildRuntimeAsFailure.find("DAT/DTX runtime path") == std::string::npos
        || std::filesystem::exists(rejectedSaveAsPath))
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: MM9 buildRuntimeAs did not reject ODM/BLV build: "
            << buildRuntimeAsFailure << '\n';
        return 1;
    }

    const Mm9SourceIntegritySnapshot sourceIntegrityAfter =
        collectMm9SourceIntegritySnapshot(levelPath);
    std::string sourceIntegrityFailure;

    if (!mm9SourceIntegritySnapshotsMatch(sourceIntegrityBefore, sourceIntegrityAfter, sourceIntegrityFailure))
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: source/* changed during open/validation/save/build checks: "
            << sourceIntegrityFailure << '\n';
        return 1;
    }

    const Mm9SourceIntegritySnapshot referencedSourceFilesBefore =
        collectMm9ReferencedSourceFileSnapshot(document);

    if (!sidecars.materialAliases.textures.empty() && resolvedTextureCount == 0)
    {
        std::cerr << "Editor headless MM9 DAT level failed: no material textures resolved to source DTX\n";
        return 1;
    }

    if (!sidecars.materialAliases.textures.empty() && loadedDtxHeaderCount == 0)
    {
        std::cerr << "Editor headless MM9 DAT level failed: no material texture loaded a source DTX header\n";
        return 1;
    }

    if (ambiguousTextureCount != 0)
    {
        std::cerr << "Editor headless MM9 DAT level failed: ambiguous source DTX references remain\n";
        return 1;
    }

    std::optional<Game::Mm9DatRenderMeshPickHit> nativePickHit;
    std::string nativePickFailure;

    if (!validateMm9SyntheticPick(datRenderMesh, nativePickHit, nativePickFailure))
    {
        std::cerr << "Editor headless MM9 DAT level failed: " << nativePickFailure << '\n';
        return 1;
    }

    const Mm9SelectedDatOverlaySummary selectedDatOverlaySummary =
        summarizeMm9SelectedDatOverlay(datRenderMesh, nativePickHit->triangleIndex);

    if (selectedDatOverlaySummary.polygonVertices == 0 || selectedDatOverlaySummary.surfaceVertices == 0)
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: native DAT selected polygon/surface overlay is empty"
            << " triangle=" << nativePickHit->triangleIndex
            << " polygon_vertices=" << selectedDatOverlaySummary.polygonVertices
            << " surface_vertices=" << selectedDatOverlaySummary.surfaceVertices << '\n';
        return 1;
    }

    const Mm9SourceIntegritySnapshot referencedSourceFilesAfter =
        collectMm9ReferencedSourceFileSnapshot(document);
    std::string referencedSourceIntegrityFailure;

    if (!mm9SourceIntegritySnapshotsMatch(
            referencedSourceFilesBefore,
            referencedSourceFilesAfter,
            referencedSourceIntegrityFailure))
    {
        std::cerr
            << "Editor headless MM9 DAT level failed: referenced source files changed during validation/pick checks: "
            << referencedSourceIntegrityFailure << '\n';
        return 1;
    }

    if (document.mm9DatLevelMetadata().runtime.visibility == "dat_bsp_portal")
    {
        if (sidecars.datWorld.totals.leafCount == 0)
        {
            std::cerr
                << "Editor headless MM9 DAT level failed: portalized DAT map has no decoded leaves\n";
            return 1;
        }

        if (physicsBspCount == 0 || visBspCount == 0)
        {
            std::cerr
                << "Editor headless MM9 DAT level failed: portalized DAT map has no PhysicsBSP or VisBSP model\n";
            return 1;
        }
    }

    std::filesystem::path validationReportPath;
    std::string validationReportFailure;

    if (!writeMm9DatLevelValidationReport(
            assetFileSystem.getDevelopmentRoot()
                / std::filesystem::path("worlds")
                / assetFileSystem.getActiveWorldId(),
            levelPath,
            document,
            modelInstanceSummary,
            viewportSummary,
            mechanismPreviewSummary,
            nativePickHit->triangleIndex,
            sourceIntegrityBefore.valid && sourceIntegrityAfter.valid,
            referencedSourceFilesAfter.referencedSourceFileHashes.size(),
            validationReportPath,
            validationReportFailure))
    {
        std::cerr << "Editor headless MM9 DAT level failed: " << validationReportFailure << '\n';
        return 1;
    }

    std::filesystem::path validationSummaryReportPath;
    std::string validationSummaryReportFailure;

    if (!writeMm9ValidationSummaryReport(
            assetFileSystem.getDevelopmentRoot()
                / std::filesystem::path("worlds")
                / assetFileSystem.getActiveWorldId(),
            validationSummaryReportPath,
            validationSummaryReportFailure))
    {
        std::cerr << "Editor headless MM9 DAT level failed: " << validationSummaryReportFailure << '\n';
        return 1;
    }

    std::cout << "Editor headless MM9 DAT level passed: " << levelFileName
              << " kind=Mm9Dat"
              << " map_id=" << document.mm9DatLevelMetadata().mapId
              << " classification=" << document.mm9DatLevelMetadata().runtime.classification
              << " visibility=" << document.mm9DatLevelMetadata().runtime.visibility
              << " world_models=" << sidecars.datWorld.worldModels.size()
              << " leaves=" << sidecars.datWorld.totals.leafCount
              << " user_portals=" << sidecars.datWorld.totals.userPortalCount
              << " dat_world_reference_issues=" << datWorldReferenceIssues.size()
              << " dat_world_invalid_leaf_references="
              << (sidecars.datWorld.totals.invalidLeafReferenceCount + sidecars.datWorld.leafReferences.invalidRefs)
              << " dat_world_invalid_surface_texture_refs=" << invalidSurfaceTextureRefs
              << " dat_world_invalid_poly_surface_refs=" << invalidPolySurfaceRefs
              << " dat_world_invalid_poly_plane_refs=" << invalidPolyPlaneRefs
              << " dat_world_invalid_poly_vertex_refs=" << invalidPolyVertexRefs
              << " dat_world_invalid_node_poly_refs=" << invalidNodePolyRefs
              << " dat_world_invalid_root_node_refs=" << invalidRootNodeRefs
              << " dat_world_models_with_unknown_values=" << worldModelsWithUnknownValues
              << " dat_world_user_portals_with_raw_unknowns=" << userPortalsWithRawUnknowns
              << " native_mesh_triangles=" << datRenderMesh.triangles.size()
              << " native_mesh_source_polies=" << datRenderMesh.sourcePolyCount
              << " native_mesh_degenerate_triangles=" << datRenderMesh.skippedDegenerateTriangleCount
              << " native_pick_triangle=" << nativePickHit->triangleIndex
              << " native_pick_model=" << nativePickHit->sourceModelIndex
              << " native_pick_poly=" << nativePickHit->sourcePolyIndex
              << " native_pick_surface=" << nativePickHit->sourceSurfaceIndex
              << " native_pick_texture=" << nativePickHit->sourceTextureIndex
              << " selected_polygon_overlay_vertices=" << selectedDatOverlaySummary.polygonVertices
              << " selected_surface_overlay_vertices=" << selectedDatOverlaySummary.surfaceVertices
              << " native_material_assignments=" << assignedNativeMaterialCount
              << " native_material_previews=" << nativeMaterialPreviewCount
              << " viewport_native_renderable_triangles=" << viewportSummary.nativeRenderableTriangles
              << " viewport_native_renderable_physics_triangles="
              << viewportSummary.nativeRenderablePhysicsTriangles
              << " viewport_native_textured_triangles=" << viewportSummary.nativeTexturedTriangles
              << " viewport_native_missing_material_triangles=" << viewportSummary.nativeMissingMaterialTriangles
              << " viewport_native_placeholder_material_triangles="
              << viewportSummary.nativePlaceholderMaterialTriangles
              << " viewport_native_unresolved_material_triangles="
              << viewportSummary.nativeUnresolvedMaterialTriangles
              << " native_bounds_radius=" << nativeBounds.radius
              << " native_camera_far=" << nativeCameraFrame.farPlane
              << " native_filter_visual=" << nativeFilters.summary.visualTriangles
              << " native_filter_invisible=" << nativeFilters.summary.invisibleTriangles
              << " native_filter_water=" << nativeFilters.summary.waterTriangles
              << " native_filter_visible_water=" << nativeFilters.summary.visibleWaterTriangles
              << " native_filter_water_volume=" << nativeFilters.summary.waterVolumeTriangles
              << " native_filter_rail=" << nativeFilters.summary.railTriangles
              << " native_filter_helper=" << nativeFilters.summary.helperTriangles
              << " native_filter_physics=" << nativeFilters.summary.physicsTriangles
              << " native_filter_visibility=" << nativeFilters.summary.visibilityTriangles
              << " native_filter_portals=" << nativeFilters.summary.portalOverlays
              << " readonly_source_paths=" << readOnlySourcePathCount
              << " source_integrity_snapshot_verified="
              << (sourceIntegrityBefore.valid && sourceIntegrityAfter.valid ? 1 : 0)
              << " referenced_source_snapshot_files="
              << referencedSourceFilesAfter.referencedSourceFileHashes.size()
              << " source_dat_hash_diagnostics=" << sourceDatHashDiagnosticCount
              << " source_manifest_diagnostics=" << document.mm9SourceAssetManifestDiagnostics().size()
              << " source_manifest_expected_files=" << sourceFamilyExpectedFileCount
              << " source_manifest_actual_files=" << sourceFamilyActualFileCount
              << " source_manifest_count_drift_families=" << sourceFamilyCountDriftCount
              << " source_manifest_missing_directories=" << sourceFamilyMissingDirectoryCount
              << " generated_paths=" << generatedPathCount
              << " authored_paths=" << authoredPathCount
              << " authored_override_paths=" << authoredOverridePathCount
              << " compatibility_paths=" << compatibilityPathCount
              << " physics_bsp_models=" << physicsBspCount
              << " vis_bsp_models=" << visBspCount
              << " decoded_pblocks=" << decodedPBlockCount
              << " raw_objects=" << sidecars.rawObjects.objects.size()
              << " raw_object_sidecar_issues=" << rawObjectSidecarIssues.size()
              << " world_model_overlay_vertices=" << worldModelOverlayVertices
              << " world_model_overlay_pick_candidates=" << worldModelOverlayPickCandidates
              << " object_source_transforms=" << document.mm9ObjectLayer().positionedObjectCount
              << " object_bounds_evidence=" << document.mm9ObjectLayer().boundsEvidenceObjectCount
              << " object_trigger_volumes=" << document.mm9ObjectLayer().triggerVolumeCount
              << " object_overlay_vertices=" << objectOverlayVertices
              << " object_overlay_pick_candidates=" << objectOverlayPickCandidates
              << " mechanism_gizmo_candidates=" << mechanismTargetMarkerSummary.gizmoCandidates
              << " mechanism_circle_gizmo_candidates=" << mechanismTargetMarkerSummary.circleGizmoCandidates
              << " mechanism_target_gizmo_candidates=" << mechanismTargetMarkerSummary.targetGizmoCandidates
              << " mechanism_motion_path_markers=" << mechanismTargetMarkerSummary.motionPathMarkers
              << " mechanism_los_checked_candidates="
              << mechanismTargetMarkerSummary.lineOfSightCheckedCandidates
              << " mechanism_los_blocked_candidates="
              << mechanismTargetMarkerSummary.lineOfSightBlockedCandidates
              << " light_objects=" << document.mm9LightLayer().lights.size()
              << " light_overlay_vertices=" << sourceMarkerOverlaySummary.lightVertices
              << " static_render_lights=" << Game::buildMm9StaticRenderLights(document.mm9LightLayer()).size()
              << " light_diagnostics=" << document.mm9LightLayer().diagnostics.size()
              << " sound_objects=" << document.mm9SoundLayer().objects.size()
              << " sound_overlay_vertices=" << sourceMarkerOverlaySummary.soundVertices
              << " sound_references=" << document.mm9SoundLayer().referenceCount
              << " resolved_sound_references=" << document.mm9SoundLayer().resolvedReferenceCount
              << " unresolved_required_sound_references="
              << document.mm9SoundLayer().unresolvedRequiredReferenceCount
              << " spawn_source_objects=" << document.mm9SpawnLayer().objects.size()
              << " spawn_overlay_vertices=" << sourceMarkerOverlaySummary.spawnVertices
              << " spawn_npc_numbers=" << document.mm9SpawnLayer().npcNumberCount
              << " model_instances=" << sceneData.modelInstances.size()
              << " model_instances_in_camera_front=" << modelInstanceCameraFrameSummary.inFront
              << " model_instances_in_camera_depth_range=" << modelInstanceCameraFrameSummary.inDepthRange
              << " model_instances_in_camera_frame=" << modelInstanceCameraFrameSummary.inView
              << " resolved_model_instance_assets=" << modelInstanceSummary.resolvedAssets
              << " missing_model_instance_assets=" << modelInstanceSummary.missingAssets
              << " drawable_model_instance_geometry=" << modelInstanceSummary.drawableGeometry
              << " missing_drawable_model_instance_geometry=" << modelInstanceSummary.missingDrawableGeometry
              << " viewport_model_instance_drawable_geometry=" << viewportSummary.modelInstanceDrawableGeometry
              << " viewport_model_instance_decoded_skin_textures="
              << viewportSummary.modelInstanceDecodedSkinTextures
              << " decoded_model_instance_skin_textures=" << modelInstanceSummary.decodedSkinTextures
              << " actor_variant_candidates=" << modelInstanceSummary.actorVariantCandidates
              << " actor_variant_resolved=" << modelInstanceSummary.actorVariantResolved
              << " actor_variant_unresolved=" << modelInstanceSummary.actorVariantUnresolved
              << " actor_variant_actor_rows=" << modelInstanceSummary.actorVariantActorRows
              << " actor_variant_gameplay_identity_rows="
              << modelInstanceSummary.actorVariantGameplayIdentityRows
              << " actor_variant_foot_sound_fields=" << modelInstanceSummary.actorVariantFootSoundFields
              << " actor_variant_resolved_foot_sounds=" << modelInstanceSummary.actorVariantResolvedFootSounds
              << " actor_variant_unresolved_foot_sounds=" << modelInstanceSummary.actorVariantUnresolvedFootSounds
              << " actor_variant_source_sound_references="
              << modelInstanceSummary.actorVariantSourceSoundReferences
              << " actor_variant_resolved_source_sound_references="
              << modelInstanceSummary.actorVariantResolvedSourceSoundReferences
              << " actor_variant_unresolved_source_sound_references="
              << modelInstanceSummary.actorVariantUnresolvedSourceSoundReferences
              << " actor_variant_source_voice_references="
              << modelInstanceSummary.actorVariantSourceVoiceReferences
              << " actor_variant_resolved_source_voice_references="
              << modelInstanceSummary.actorVariantResolvedSourceVoiceReferences
              << " actor_variant_unresolved_source_voice_references="
              << modelInstanceSummary.actorVariantUnresolvedSourceVoiceReferences
              << " scripted_objects=" << modelInstanceSummary.scriptedObjects
              << " scripted_objects_with_collision_visuals="
              << modelInstanceSummary.scriptedObjectsWithCollisionVisuals
              << " scripted_objects_with_model_collision_volumes="
              << modelInstanceSummary.scriptedObjectsWithModelCollisionVolumes
              << " scripted_objects_requiring_billboard_collision_visuals="
              << modelInstanceSummary.scriptedObjectsRequiringBillboardCollisionVisuals
              << " missing_scripted_object_collision_visuals="
              << modelInstanceSummary.missingScriptedObjectCollisionVisuals
              << " materials=" << sidecars.materialAliases.textures.size()
              << " resolved_dtx=" << resolvedTextureCount
              << " dtx_headers=" << loadedDtxHeaderCount
              << " dtx_headers_matching_sidecar=" << matchedDtxHeaderCount
              << " dtx_mip_payloads=" << dtxMipPayloadCount
              << " dtx_decoded_preview_mips=" << dtxDecodedPreviewMipCount
              << " dtx_section_metadata_records=" << dtxSectionMetadataCount
              << " dtx_section_payloads_available=" << dtxSectionPayloadAvailableCount
              << " dtx_command_strings=" << dtxCommandStringCount
              << " texture_caches=" << cacheTextureCount
              << " source_dtx_hashes=" << sourceDtxHashCount
              << " cache_hashes=" << cacheHashCount
              << " stale_caches=" << staleCacheCount
              << " decoded_cache_checks=" << decodedCacheDeterminismCheckedCount
              << " decoded_cache_matches=" << decodedCacheMatchCount
              << " raw_object_asset_refs=" << rawObjectAssetReferenceCount
              << " optional_raw_object_asset_refs=" << optionalRawObjectAssetReferenceCount
              << " unresolved_raw_object_asset_refs=" << unresolvedRawObjectAssetReferenceCount
              << " unresolved_optional_raw_object_asset_refs=" << unresolvedOptionalRawObjectAssetReferenceCount
              << " asset_graph_total=" << assetSummary.total
              << " asset_graph_resolved=" << assetSummary.resolved
              << " asset_graph_unresolved=" << assetSummary.unresolved
              << " asset_graph_ambiguous=" << assetSummary.ambiguous
              << " asset_graph_stale=" << assetSummary.stale
              << " asset_graph_required_unresolved=" << assetSummary.requiredUnresolved
              << " asset_graph_required_ambiguous=" << assetSummary.requiredAmbiguous
              << " asset_graph_optional_unresolved=" << assetSummary.optionalUnresolved
              << " asset_graph_source_only=" << assetSummary.sourceOnly
              << " asset_graph_unused_source=" << assetSummary.unusedSource
              << " mechanisms=" << mechanismSummary.total
              << " mechanism_unresolved_targets=" << mechanismSummary.unresolvedTargets
              << " mechanism_unresolved_required_targets=" << mechanismSummary.unresolvedRequiredTargets
              << " mechanism_incomplete_linear_motion=" << mechanismSummary.incompleteLinearMotion
              << " mechanism_incomplete_rotation_motion=" << mechanismSummary.incompleteRotationMotion
              << " mechanism_sound_slots=" << mechanismSummary.soundSlots
              << " mechanism_authored_sound_references=" << mechanismSummary.authoredSoundReferences
              << " mechanism_empty_sound_references=" << mechanismSummary.emptySoundReferences
              << " mechanism_previewable_mechanisms=" << mechanismSummary.previewableMechanisms
              << " mechanism_inert_mechanisms=" << mechanismSummary.inertMechanisms
              << " mechanism_inert_preview_entries=" << mechanismSummary.inertPreviewMechanisms.size()
              << " mechanism_without_preview_motion=" << mechanismSummary.mechanismsWithoutPreviewMotion
              << " mechanism_without_preview_target=" << mechanismSummary.mechanismsWithoutPreviewTarget
              << " mechanism_activation_start_open_fields=" << mechanismSummary.activationStartOpenFields
              << " mechanism_activation_locked_fields=" << mechanismSummary.activationLockedFields
              << " mechanism_activation_push_open_fields=" << mechanismSummary.activationPushOpenFields
              << " mechanism_activation_touch_to_open_fields=" << mechanismSummary.activationTouchToOpenFields
              << " mechanism_activation_lock_on_close_fields=" << mechanismSummary.activationLockOnCloseFields
              << " mechanism_activation_reopen_on_contact_fields="
              << mechanismSummary.activationReopenOnContactFields
              << " mechanism_rotation_open_away_fields=" << mechanismSummary.rotationOpenAwayFields
              << " mechanism_timing_move_delay_fields=" << mechanismSummary.timingMoveDelayFields
              << " mechanism_timing_open_wait_fields=" << mechanismSummary.timingOpenWaitFields
              << " mechanism_trigger_outputs=" << mechanismSummary.triggerOutputs
              << " mechanism_unresolved_trigger_outputs=" << mechanismSummary.unresolvedTriggerOutputs
              << " script_includes=" << scriptIncludes
              << " script_labels=" << scriptLabels
              << " script_include_references=" << scriptIncludeSummary.references
              << " script_resolved_includes=" << scriptIncludeSummary.resolved
              << " script_unresolved_includes=" << scriptIncludeSummary.unresolved
              << " script_ambiguous_includes=" << scriptIncludeSummary.ambiguous
              << " script_registered_triggers=" << scriptRegisteredTriggers
              << " script_trigger_edges=" << scriptTriggerEdges
              << " script_movement_commands=" << scriptMovementCommands
              << " script_unknown_commands=" << scriptUnknownCommands
              << " script_command_count=" << scriptCommandCount
              << " unresolved_events=" << sidecars.events.unresolved.size()
              << " unresolved_event_warnings=" << unresolvedEventWarnings
              << " unresolved_event_errors=" << unresolvedEventErrors
              << " unresolved_event_rotation_candidates=" << unresolvedEventRotationCandidates
              << " unresolved_event_position_candidates=" << unresolvedEventPositionCandidates
              << " mechanism_movable_world_models=" << mechanismSummary.movableWorldModels
              << " mechanism_world_model_targets_with_movable_role="
              << mechanismSummary.worldModelTargetsWithMovableRole
              << " mechanism_world_model_targets_without_movable_role="
              << mechanismSummary.worldModelTargetsWithoutMovableRole
              << " mechanism_world_model_targets_missing_model=" << mechanismSummary.worldModelTargetsMissingModel
              << " mechanism_world_model_targets_with_polygon_group="
              << mechanismSummary.worldModelTargetsWithPolygonGroup
              << " mechanism_world_model_targets_missing_polygon_group="
              << mechanismSummary.worldModelTargetsMissingPolygonGroup
              << " mechanism_world_model_targets_mismatched_polygon_group="
              << mechanismSummary.worldModelTargetsMismatchedPolygonGroup
              << " mechanism_preview_candidates=" << mechanismPreviewSummary.candidates
              << " mechanism_preview_target_found=" << mechanismPreviewSummary.targetFound
              << " mechanism_preview_transformed_triangles=" << mechanismPreviewSummary.transformedTriangles
              << " mechanism_preview_changed_bounds=" << mechanismPreviewSummary.changedBounds
              << " validation_report=" << validationReportPath.generic_string()
              << " validation_summary_report=" << validationSummaryReportPath.generic_string()
              << " event_objects=" << sidecars.events.objects.size() << '\n';
    return 0;
}

int EditorHeadlessDiagnostics::runVerifyMm9DatFilters(
    const std::filesystem::path &basePath,
    const std::string &levelFileName) const
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(
            basePath,
            m_config.assetRoot,
            m_config.assetScaleTier,
            m_config.assetScaleProfile,
            m_config.activeWorldId))
    {
        std::cerr << "Editor headless MM9 DAT filters failed: could not initialize asset file system\n";
        return 1;
    }

    std::filesystem::path levelPath =
        activeWorldEditorPath(assetFileSystem, std::filesystem::path("maps") / levelFileName);

    if (!std::filesystem::exists(levelPath))
    {
        levelPath = assetFileSystem.getDevelopmentRoot()
            / std::filesystem::path("worlds")
            / assetFileSystem.getActiveWorldId()
            / "maps"
            / levelFileName;
    }

    EditorDocument document;
    std::string failure;

    if (!document.loadMapPhysicalPath(assetFileSystem, levelPath, failure))
    {
        std::cerr << "Editor headless MM9 DAT filters failed: " << failure << '\n';
        return 1;
    }

    if (document.kind() != EditorDocument::Kind::Mm9Dat
        || !document.hasMm9DatLoadedSidecars()
        || !document.hasMm9DatWorld()
        || document.mm9DatRenderMesh().triangles.empty())
    {
        std::cerr << "Editor headless MM9 DAT filters failed: MM9 DAT document is incomplete\n";
        return 1;
    }

    const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
    const Game::Mm9DatRenderMesh &renderMesh = document.mm9DatRenderMesh();
    const Game::Mm9DatRenderFilterResult filters =
        Game::classifyMm9DatRenderMeshFilters(
            renderMesh,
            mm9ModelRenderRolesFromSidecar(sidecars.datWorld),
            sidecars.datWorld.userPortals.size());

    if (filters.entries.size() != renderMesh.triangles.size()
        || filters.summary.totalTriangles != renderMesh.triangles.size()
        || filters.summary.unclassifiedTriangles != 0)
    {
        std::cerr << "Editor headless MM9 DAT filters failed: classifier did not cover every render triangle\n";
        return 1;
    }

    size_t defaultRenderedTriangles = 0;
    size_t skyTriangles = 0;
    size_t physicsTriangles = 0;
    size_t waterTriangles = 0;
    size_t visibleWaterTriangles = 0;
    size_t waterVolumeTriangles = 0;
    size_t waterVolumeTrianglesWithoutHelper = 0;
    size_t railTriangles = 0;
    size_t railTrianglesWithoutHelper = 0;
    size_t visibilityTriangles = 0;
    size_t invisibleTriangles = 0;
    size_t helperTriangles = 0;
    size_t triggerTriangles = 0;
    size_t defaultHiddenTriangles = 0;
    size_t datSolidTriangles = 0;
    size_t datPhysicsBlockerTriangles = 0;
    size_t datVisibilityBlockerTriangles = 0;
    size_t datNotAStepTriangles = 0;
    size_t datPortalSurfaceTriangles = 0;
    const size_t portalOverlayVertices = sidecars.datWorld.userPortals.size() * 24;
    const size_t objectOverlayVertices = countMm9ObjectOverlayVertices(document.mm9ObjectLayer());

    for (const Game::Mm9DatRenderFilterEntry &entry : filters.entries)
    {
        if (entry.triangleIndex >= renderMesh.triangles.size())
        {
            std::cerr << "Editor headless MM9 DAT filters failed: classifier entry triangle index is out of range\n";
            return 1;
        }

        const uint32_t datSurfaceFlags = renderMesh.triangles[entry.triangleIndex].surfaceFlags;
        const bool renderable =
            (entry.flags
                & (Game::Mm9DatRenderFilterVisual
                    | Game::Mm9DatRenderFilterSky
                    | Game::Mm9DatRenderFilterWater
                    | Game::Mm9DatRenderFilterTerrain
                    | Game::Mm9DatRenderFilterPhysics
                    | Game::Mm9DatRenderFilterMovable)) != 0;
        const bool hiddenInDefault =
            (entry.flags
                & (Game::Mm9DatRenderFilterInvisible
                    | Game::Mm9DatRenderFilterWaterVolume
                    | Game::Mm9DatRenderFilterRail
                    | Game::Mm9DatRenderFilterVisibility
                    | Game::Mm9DatRenderFilterTrigger)) != 0;

        if (renderable && !hiddenInDefault)
        {
            ++defaultRenderedTriangles;
        }

        if (hiddenInDefault)
        {
            ++defaultHiddenTriangles;
        }

        if ((entry.flags & Game::Mm9DatRenderFilterSky) != 0)
        {
            ++skyTriangles;
        }

        if ((entry.flags & Game::Mm9DatRenderFilterPhysics) != 0)
        {
            ++physicsTriangles;
        }

        if ((entry.flags & Game::Mm9DatRenderFilterWater) != 0)
        {
            ++waterTriangles;
        }

        if ((entry.flags & Game::Mm9DatRenderFilterVisibleWater) != 0)
        {
            ++visibleWaterTriangles;
        }

        if ((entry.flags & Game::Mm9DatRenderFilterWaterVolume) != 0)
        {
            ++waterVolumeTriangles;
            if ((entry.flags & Game::Mm9DatRenderFilterHelper) == 0)
            {
                ++waterVolumeTrianglesWithoutHelper;
            }
        }

        if ((entry.flags & Game::Mm9DatRenderFilterRail) != 0)
        {
            ++railTriangles;
            if ((entry.flags & Game::Mm9DatRenderFilterHelper) == 0)
            {
                ++railTrianglesWithoutHelper;
            }
        }

        if ((entry.flags & Game::Mm9DatRenderFilterVisibility) != 0)
        {
            ++visibilityTriangles;
        }

        if ((entry.flags & Game::Mm9DatRenderFilterInvisible) != 0)
        {
            ++invisibleTriangles;
        }

        if ((entry.flags & Game::Mm9DatRenderFilterHelper) != 0)
        {
            ++helperTriangles;
        }

        if ((entry.flags & Game::Mm9DatRenderFilterTrigger) != 0)
        {
            ++triggerTriangles;
        }

        if ((datSurfaceFlags & Game::Mm9DatSurfaceFlagSolid) != 0)
        {
            ++datSolidTriangles;
        }

        if ((datSurfaceFlags & Game::Mm9DatSurfaceFlagPhysicsBlocker) != 0)
        {
            ++datPhysicsBlockerTriangles;
        }

        if ((datSurfaceFlags & Game::Mm9DatSurfaceFlagVisibilityBlocker) != 0)
        {
            ++datVisibilityBlockerTriangles;
        }

        if ((datSurfaceFlags & Game::Mm9DatSurfaceFlagNotAStep) != 0)
        {
            ++datNotAStepTriangles;
        }

        if ((datSurfaceFlags & Game::Mm9DatSurfaceFlagPortal) != 0)
        {
            ++datPortalSurfaceTriangles;
        }
    }

    if (defaultRenderedTriangles == 0)
    {
        std::cerr << "Editor headless MM9 DAT filters failed: default subset has no renderable triangles\n";
        return 1;
    }

    if (sidecars.datWorld.totals.userPortalCount != 0 && portalOverlayVertices == 0)
    {
        std::cerr << "Editor headless MM9 DAT filters failed: portal overlay has no vertices\n";
        return 1;
    }

    if (document.mm9ObjectLayer().boundsEvidenceObjectCount != 0 && objectOverlayVertices == 0)
    {
        std::cerr << "Editor headless MM9 DAT filters failed: object bounds overlay has no vertices\n";
        return 1;
    }

    if (skyTriangles != filters.summary.skyTriangles
        || physicsTriangles != filters.summary.physicsTriangles
        || waterTriangles != filters.summary.waterTriangles
        || visibleWaterTriangles != filters.summary.visibleWaterTriangles
        || waterVolumeTriangles != filters.summary.waterVolumeTriangles
        || railTriangles != filters.summary.railTriangles
        || visibilityTriangles != filters.summary.visibilityTriangles
        || invisibleTriangles != filters.summary.invisibleTriangles
        || helperTriangles != filters.summary.helperTriangles
        || triggerTriangles != filters.summary.triggerTriangles)
    {
        std::cerr << "Editor headless MM9 DAT filters failed: subset counts do not match classifier summary\n";
        return 1;
    }

    if (waterVolumeTrianglesWithoutHelper != 0)
    {
        std::cerr << "Editor headless MM9 DAT filters failed: water volumes are not helper geometry\n";
        return 1;
    }

    if (railTrianglesWithoutHelper != 0)
    {
        std::cerr << "Editor headless MM9 DAT filters failed: rail containers are not helper geometry\n";
        return 1;
    }

    if (document.mm9DatLevelMetadata().mapId == "thjorgard"
        && (visibleWaterTriangles == 0 || waterVolumeTriangles == 0))
    {
        std::cerr
            << "Editor headless MM9 DAT filters failed: Thjorgard must preserve visible Ocean water and "
               "hidden BlueWater/WaterMarker volume geometry\n";
        return 1;
    }

    if ((document.mm9DatLevelMetadata().mapId == "thjorgard"
            || document.mm9DatLevelMetadata().mapId == "thjorgardcity")
        && railTriangles == 0)
    {
        std::cerr << "Editor headless MM9 DAT filters failed: active map has no classified AITrk/rail geometry\n";
        return 1;
    }

    std::cout << "Editor headless MM9 DAT filters passed: " << levelFileName
              << " total=" << filters.summary.totalTriangles
              << " default=" << defaultRenderedTriangles
              << " hidden_from_default=" << defaultHiddenTriangles
              << " sky=" << skyTriangles
              << " physics=" << physicsTriangles
              << " water=" << waterTriangles
              << " visible_water=" << visibleWaterTriangles
              << " water_volume=" << waterVolumeTriangles
              << " rail=" << railTriangles
              << " visibility=" << visibilityTriangles
              << " invisible=" << invisibleTriangles
              << " helper=" << helperTriangles
              << " trigger=" << triggerTriangles
              << " dat_solid=" << datSolidTriangles
              << " dat_physics_blocker=" << datPhysicsBlockerTriangles
              << " dat_visibility_blocker=" << datVisibilityBlockerTriangles
              << " dat_not_a_step=" << datNotAStepTriangles
              << " dat_portal_surface=" << datPortalSurfaceTriangles
              << " portals=" << filters.summary.portalOverlays
              << " portal_overlay_vertices=" << portalOverlayVertices
              << " object_overlay_vertices=" << objectOverlayVertices << '\n';
    return 0;
}

int EditorHeadlessDiagnostics::runVerifyMm9EventProvenance(
    const std::filesystem::path &basePath,
    const std::string &levelFileName,
    const std::string &sourceObjectIndexText) const
{
    size_t sourceObjectIndex = 0;
    try
    {
        size_t processedCharacters = 0;
        const unsigned long long parsedIndex = std::stoull(sourceObjectIndexText, &processedCharacters, 10);
        if (processedCharacters != sourceObjectIndexText.size()
            || parsedIndex > static_cast<unsigned long long>(std::numeric_limits<size_t>::max()))
        {
            std::cerr << "Editor headless MM9 event provenance failed: invalid source object index "
                      << sourceObjectIndexText << '\n';
            return 2;
        }
        sourceObjectIndex = static_cast<size_t>(parsedIndex);
    }
    catch (const std::exception &exception)
    {
        std::cerr << "Editor headless MM9 event provenance failed: invalid source object index "
                  << sourceObjectIndexText << ": " << exception.what() << '\n';
        return 2;
    }

    Engine::AssetFileSystem assetFileSystem;
    if (!assetFileSystem.initialize(
            basePath,
            m_config.assetRoot,
            m_config.assetScaleTier,
            m_config.assetScaleProfile,
            m_config.activeWorldId))
    {
        std::cerr << "Editor headless MM9 event provenance failed: could not initialize asset file system\n";
        return 1;
    }

    std::filesystem::path levelPath =
        activeWorldEditorPath(assetFileSystem, std::filesystem::path("maps") / levelFileName);

    if (!std::filesystem::exists(levelPath))
    {
        levelPath = assetFileSystem.getDevelopmentRoot()
            / std::filesystem::path("worlds")
            / assetFileSystem.getActiveWorldId()
            / "maps"
            / levelFileName;
    }

    EditorSession session;
    session.initialize(assetFileSystem);
    std::string failure;
    if (!session.openMapPhysicalPath(levelPath, failure))
    {
        std::cerr << "Editor headless MM9 event provenance failed: " << failure << '\n';
        return 1;
    }

    const EditorDocument &document = session.document();
    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatLoadedSidecars())
    {
        std::cerr << "Editor headless MM9 event provenance failed: document is not a loaded MM9 DAT level\n";
        return 1;
    }

    const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
    const Game::Mm9EventsData &events = sidecars.events;
    size_t eventObjectIndex = 0;
    const Game::Mm9EventObject *pEventObject =
        findMm9EventObjectBySourceIndex(events, sourceObjectIndex, &eventObjectIndex);
    if (pEventObject == nullptr)
    {
        std::cerr << "Editor headless MM9 event provenance failed: no generated event object for source object "
                  << sourceObjectIndex << '\n';
        return 1;
    }

    session.select(EditorSelectionKind::Mm9EventObject, eventObjectIndex);
    if (session.selection().kind != EditorSelectionKind::Mm9EventObject
        || session.selection().index != eventObjectIndex)
    {
        std::cerr << "Editor headless MM9 event provenance failed: event object selection did not stick\n";
        return 1;
    }

    const EditorMm9RawObject *pRawObject =
        findMm9RawObjectBySourceIndex(sidecars.rawObjects, sourceObjectIndex);
    if (pRawObject == nullptr)
    {
        std::cerr << "Editor headless MM9 event provenance failed: no raw object for source object "
                  << sourceObjectIndex << '\n';
        return 1;
    }

    if (pEventObject->rawPropertyCount != pRawObject->properties.size())
    {
        std::cerr
            << "Editor headless MM9 event provenance failed: raw property count mismatch for source object "
            << sourceObjectIndex << " event=" << pEventObject->rawPropertyCount
            << " raw=" << pRawObject->properties.size() << '\n';
        return 1;
    }

    const std::filesystem::path generatedLuaPath =
        resolveMm9LevelRelativePath(levelPath, document.mm9DatLevelMetadata().scripts.level);
    const std::filesystem::path generatedScriptIrPath =
        resolveMm9LevelRelativePath(levelPath, document.mm9DatLevelMetadata().scripts.scriptIr);

    if (events.generatedLua != document.mm9DatLevelMetadata().scripts.level
        || events.generatedScriptIr != document.mm9DatLevelMetadata().scripts.scriptIr)
    {
        std::cerr
            << "Editor headless MM9 event provenance failed: events sidecar generated script paths do not match level"
            << '\n';
        return 1;
    }

    if (!std::filesystem::exists(generatedLuaPath) || !std::filesystem::exists(generatedScriptIrPath))
    {
        std::cerr
            << "Editor headless MM9 event provenance failed: generated Lua or script IR is missing"
            << " lua=" << generatedLuaPath.generic_string()
            << " script_ir=" << generatedScriptIrPath.generic_string() << '\n';
        return 1;
    }

    std::string generatedLuaText;
    std::string generatedScriptIrText;

    if (!readTextFileContents(generatedLuaPath, generatedLuaText)
        || !readTextFileContents(generatedScriptIrPath, generatedScriptIrText)
        || generatedLuaText.empty()
        || generatedScriptIrText.empty()
        || generatedLuaText.find("generated from MM9 event sidecars") == std::string::npos
        || generatedScriptIrText.find("kind: mm9_script_ir") == std::string::npos)
    {
        std::cerr
            << "Editor headless MM9 event provenance failed: generated Lua or script IR is not readable"
            << " lua=" << generatedLuaPath.generic_string()
            << " script_ir=" << generatedScriptIrPath.generic_string() << '\n';
        return 1;
    }

    bool resolvedMechanismTarget = false;
    size_t mechanismIndex = 0;
    const Game::Mm9EventMechanism *pMechanism =
        findMm9MechanismForObject(events, pEventObject->objectId, &mechanismIndex);
    if (pMechanism != nullptr)
    {
        session.select(EditorSelectionKind::Mm9Mechanism, mechanismIndex);
        if (session.selection().kind != EditorSelectionKind::Mm9Mechanism
            || session.selection().index != mechanismIndex)
        {
            std::cerr << "Editor headless MM9 event provenance failed: mechanism selection did not stick\n";
            return 1;
        }

        const Game::Mm9EventBinding *pBinding = findMm9BindingForObject(events, pEventObject->objectId);
        if (pBinding == nullptr || pBinding->targets.empty())
        {
            std::cerr
                << "Editor headless MM9 event provenance failed: selected mechanism has no generated binding target"
                << '\n';
            return 1;
        }

        for (const Game::Mm9EventBindingTarget &target : pBinding->targets)
        {
            if (target.targetKind == "unresolved")
            {
                std::cerr
                    << "Editor headless MM9 event provenance failed: selected mechanism still has unresolved target"
                    << '\n';
                return 1;
            }

            if (target.targetKind == "odm_bmodel" && target.bmodelIndex)
            {
                if (*target.bmodelIndex >= sidecars.datWorld.worldModels.size())
                {
                    std::cerr
                        << "Editor headless MM9 event provenance failed: mechanism target world model is out of range"
                        << '\n';
                    return 1;
                }

                const EditorMm9DatWorldModelSummary &worldModel =
                    sidecars.datWorld.worldModels[*target.bmodelIndex];
                if (!target.sourceModelName.empty() && target.sourceModelName != worldModel.sourceName)
                {
                    std::cerr
                        << "Editor headless MM9 event provenance failed: mechanism target source model mismatch"
                        << " target=" << target.sourceModelName
                        << " dat=" << worldModel.sourceName << '\n';
                    return 1;
                }

                resolvedMechanismTarget = true;
            }
        }
    }

    bool resolvedScript = false;
    const std::unordered_map<std::string, std::string>::const_iterator scriptNameIterator =
        pEventObject->normalizedProperties.find("ScriptName");
    const std::string scriptName = scriptNameIterator == pEventObject->normalizedProperties.end()
        ? std::string()
        : mm9TrimScalarText(scriptNameIterator->second);
    if (!scriptName.empty())
    {
        const std::string scriptId = mm9FileNameLowerCopy(scriptName);
        const Game::Mm9EventScript *pScript = findMm9EventScriptById(events, scriptId);
        if (pScript == nullptr)
        {
            std::cerr
                << "Editor headless MM9 event provenance failed: selected event object script is missing from events"
                << " script=" << scriptName << '\n';
            return 1;
        }

        std::filesystem::path sourceScriptPath = resolveMm9SourceScriptPath(levelPath, pScript->sourcePath);
        if (!std::filesystem::exists(sourceScriptPath))
        {
            const std::filesystem::path developmentSourceScriptPath =
                assetFileSystem.getDevelopmentRoot()
                / std::filesystem::path("worlds")
                / assetFileSystem.getActiveWorldId()
                / "source"
                / "scripts"
                / pScript->sourcePath;
            if (std::filesystem::exists(developmentSourceScriptPath))
            {
                sourceScriptPath = developmentSourceScriptPath;
            }
        }
        if (!std::filesystem::exists(sourceScriptPath))
        {
            std::cerr
                << "Editor headless MM9 event provenance failed: selected event object source script is missing"
                << " script=" << sourceScriptPath.generic_string() << '\n';
            return 1;
        }

        resolvedScript = true;
    }

    if (!resolvedMechanismTarget && !resolvedScript)
    {
        std::cerr
            << "Editor headless MM9 event provenance failed: selected object has neither a resolved mechanism target"
            << " nor a resolved source script\n";
        return 1;
    }

    std::cout << "Editor headless MM9 event provenance passed: " << levelFileName
              << " source_object_index=" << sourceObjectIndex
              << " object_id=" << pEventObject->objectId
              << " source_class=" << pEventObject->sourceClass
              << " source_name=" << pEventObject->sourceName
              << " event_object_index=" << eventObjectIndex
              << " raw_properties=" << pRawObject->properties.size()
              << " mechanism=" << (pMechanism != nullptr ? "true" : "false")
              << " resolved_mechanism_target=" << (resolvedMechanismTarget ? "true" : "false")
              << " script=" << (resolvedScript ? "true" : "false")
              << " generated_lua=" << generatedLuaPath.generic_string()
              << " generated_lua_bytes=" << generatedLuaText.size()
              << " generated_script_ir=" << generatedScriptIrPath.generic_string() << '\n';
    return 0;
}

int EditorHeadlessDiagnostics::runVerifyMm9Events(
    const std::filesystem::path &basePath,
    const std::string &levelFileName) const
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(
            basePath,
            m_config.assetRoot,
            m_config.assetScaleTier,
            m_config.assetScaleProfile,
            m_config.activeWorldId))
    {
        std::cerr << "Editor headless MM9 events failed: could not initialize asset file system\n";
        return 1;
    }

    std::filesystem::path levelPath =
        activeWorldEditorPath(assetFileSystem, std::filesystem::path("maps") / levelFileName);

    if (!std::filesystem::exists(levelPath))
    {
        levelPath = assetFileSystem.getDevelopmentRoot()
            / std::filesystem::path("worlds")
            / assetFileSystem.getActiveWorldId()
            / "maps"
            / levelFileName;
    }

    EditorSession session;
    session.initialize(assetFileSystem);
    std::string failure;
    if (!session.openMapPhysicalPath(levelPath, failure))
    {
        std::cerr << "Editor headless MM9 events failed: " << failure << '\n';
        return 1;
    }

    const EditorDocument &document = session.document();
    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatLoadedSidecars())
    {
        std::cerr << "Editor headless MM9 events failed: document is not a loaded MM9 DAT level\n";
        return 1;
    }

    const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
    const Game::Mm9EventsData &events = sidecars.events;
    const std::filesystem::path generatedLuaPath =
        resolveMm9LevelRelativePath(levelPath, document.mm9DatLevelMetadata().scripts.level);
    const std::filesystem::path generatedScriptIrPath =
        resolveMm9LevelRelativePath(levelPath, document.mm9DatLevelMetadata().scripts.scriptIr);

    if (events.generatedLua != document.mm9DatLevelMetadata().scripts.level
        || events.generatedScriptIr != document.mm9DatLevelMetadata().scripts.scriptIr)
    {
        std::cerr << "Editor headless MM9 events failed: generated script paths do not match level metadata\n";
        return 1;
    }

    std::string generatedLuaText;
    std::string generatedScriptIrText;
    if (!readTextFileContents(generatedLuaPath, generatedLuaText)
        || !readTextFileContents(generatedScriptIrPath, generatedScriptIrText)
        || generatedLuaText.find("generated from MM9 event sidecars") == std::string::npos
        || generatedScriptIrText.find("kind: mm9_script_ir") == std::string::npos)
    {
        std::cerr
            << "Editor headless MM9 events failed: generated Lua or script IR is unreadable"
            << " lua=" << generatedLuaPath.generic_string()
            << " script_ir=" << generatedScriptIrPath.generic_string() << '\n';
        return 1;
    }

    std::unordered_map<std::string, const Game::Mm9EventObject *> eventObjectsById;
    eventObjectsById.reserve(events.objects.size());
    size_t rawPropertyMismatches = 0;

    for (const Game::Mm9EventObject &eventObject : events.objects)
    {
        eventObjectsById.emplace(eventObject.objectId, &eventObject);
        const EditorMm9RawObject *pRawObject =
            findMm9RawObjectBySourceIndex(sidecars.rawObjects, static_cast<size_t>(eventObject.sourceObjectIndex));

        if (pRawObject == nullptr || pRawObject->properties.size() != eventObject.rawPropertyCount)
        {
            ++rawPropertyMismatches;
        }
    }

    size_t missingSourceScripts = 0;
    size_t resolvedSourceScripts = 0;
    const EditorMm9ScriptIncludeResolutionSummary scriptIncludeSummary =
        summarizeMm9EventScriptIncludeResolution(levelPath, events);

    for (const Game::Mm9EventScript &script : events.scripts)
    {
        std::filesystem::path sourceScriptPath = resolveMm9SourceScriptPath(levelPath, script.sourcePath);
        if (!std::filesystem::exists(sourceScriptPath))
        {
            const std::filesystem::path developmentSourceScriptPath =
                assetFileSystem.getDevelopmentRoot()
                / std::filesystem::path("worlds")
                / assetFileSystem.getActiveWorldId()
                / "source"
                / "scripts"
                / script.sourcePath;
            if (std::filesystem::exists(developmentSourceScriptPath))
            {
                sourceScriptPath = developmentSourceScriptPath;
            }
        }

        if (std::filesystem::exists(sourceScriptPath))
        {
            ++resolvedSourceScripts;
        }
        else
        {
            ++missingSourceScripts;
        }
    }

    size_t bindingTargets = 0;
    size_t unresolvedTargets = 0;
    size_t outOfRangeWorldTargets = 0;
    size_t missingBindingObjects = 0;

    for (const Game::Mm9EventBinding &binding : events.bindings)
    {
        if (eventObjectsById.find(binding.objectId) == eventObjectsById.end())
        {
            ++missingBindingObjects;
        }

        bindingTargets += binding.targets.size();

        for (const Game::Mm9EventBindingTarget &target : binding.targets)
        {
            if (target.targetKind == "unresolved")
            {
                ++unresolvedTargets;
            }

            if (target.targetKind == "odm_bmodel"
                && (!target.bmodelIndex || *target.bmodelIndex >= sidecars.datWorld.worldModels.size()))
            {
                ++outOfRangeWorldTargets;
            }
        }
    }

    size_t mechanismsWithMissingObjects = 0;
    for (const Game::Mm9EventMechanism &mechanism : events.mechanisms)
    {
        if (eventObjectsById.find(mechanism.objectId) == eventObjectsById.end())
        {
            ++mechanismsWithMissingObjects;
        }
    }

    if (rawPropertyMismatches != 0
        || missingSourceScripts != 0
        || scriptIncludeSummary.unresolved != 0
        || scriptIncludeSummary.ambiguous != 0
        || missingBindingObjects != 0
        || outOfRangeWorldTargets != 0
        || mechanismsWithMissingObjects != 0)
    {
        std::cerr
            << "Editor headless MM9 events failed:"
            << " raw_property_mismatches=" << rawPropertyMismatches
            << " missing_source_scripts=" << missingSourceScripts
            << " unresolved_source_includes=" << scriptIncludeSummary.unresolved
            << " ambiguous_source_includes=" << scriptIncludeSummary.ambiguous
            << " missing_binding_objects=" << missingBindingObjects
            << " out_of_range_world_targets=" << outOfRangeWorldTargets
            << " mechanisms_with_missing_objects=" << mechanismsWithMissingObjects << '\n';
        return 1;
    }

    std::cout << "Editor headless MM9 events passed: " << levelFileName
              << " objects=" << events.objects.size()
              << " scripts=" << events.scripts.size()
              << " resolved_source_scripts=" << resolvedSourceScripts
              << " resolved_source_includes=" << scriptIncludeSummary.resolved
              << " source_include_references=" << scriptIncludeSummary.references
              << " generated_lua_bytes=" << generatedLuaText.size()
              << " generated_script_ir_bytes=" << generatedScriptIrText.size()
              << " mechanisms=" << events.mechanisms.size()
              << " bindings=" << events.bindings.size()
              << " binding_targets=" << bindingTargets
              << " unresolved_targets=" << unresolvedTargets
              << '\n';
    return 0;
}

int EditorHeadlessDiagnostics::runVerifyMm9SourceManifest(const std::filesystem::path &basePath) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(
            basePath,
            m_config.assetRoot,
            m_config.assetScaleTier,
            m_config.assetScaleProfile,
            m_config.activeWorldId))
    {
        std::cerr << "Editor headless MM9 source manifest failed: could not initialize asset file system\n";
        return 1;
    }

    std::filesystem::path manifestPath =
        assetFileSystem.getDevelopmentRoot()
        / std::filesystem::path("worlds")
        / assetFileSystem.getActiveWorldId()
        / "source"
        / "manifest.yml";

    if (!std::filesystem::exists(manifestPath))
    {
        manifestPath =
            assetFileSystem.getEditorDevelopmentRoot()
            / std::filesystem::path("worlds")
            / assetFileSystem.getActiveWorldId()
            / "source"
            / "manifest.yml";
    }

    std::string manifestText;
    if (!readTextFileContents(manifestPath, manifestText))
    {
        std::cerr
            << "Editor headless MM9 source manifest failed: could not read "
            << manifestPath.generic_string() << '\n';
        return 1;
    }

    std::string errorMessage;
    const std::optional<EditorMm9SourceAssetManifest> manifest =
        loadMm9SourceAssetManifestFromText(manifestText, errorMessage);

    if (!manifest)
    {
        std::cerr
            << "Editor headless MM9 source manifest failed: could not parse "
            << manifestPath.generic_string() << ": " << errorMessage << '\n';
        return 1;
    }

    const std::vector<EditorMm9SourceAssetFamilyStatus> statuses =
        inspectMm9SourceAssetManifestFiles(manifestPath, *manifest);
    const std::vector<std::string> issues =
        validateMm9SourceAssetManifestFiles(manifestPath, *manifest);

    if (!issues.empty())
    {
        std::cerr << "Editor headless MM9 source manifest failed: validation diagnostics:\n";

        for (const std::string &issue : issues)
        {
            std::cerr << "  " << issue << '\n';
        }

        return 1;
    }

    size_t declaredFamilies = 0;
    size_t requiredFamilies = 0;
    size_t totalExpectedFiles = 0;
    size_t totalActualFiles = 0;

    for (const EditorMm9SourceAssetFamilyStatus &status : statuses)
    {
        if (status.declared)
        {
            ++declaredFamilies;
            totalExpectedFiles += status.expectedFileCount;
            totalActualFiles += status.actualFileCount;
        }

        if (status.required)
        {
            ++requiredFamilies;
        }
    }

    std::cout
        << "Editor headless MM9 source manifest passed:"
        << " world=" << assetFileSystem.getActiveWorldId()
        << " families=" << manifest->families.size()
        << " declared_statuses=" << declaredFamilies
        << " required_statuses=" << requiredFamilies
        << " expected_files=" << totalExpectedFiles
        << " actual_files=" << totalActualFiles
        << " manifest=" << manifestPath.generic_string() << '\n';
    return 0;
}

int EditorHeadlessDiagnostics::runVerifyMm9InspectorSearch(
    const std::filesystem::path &basePath,
    const std::string &levelFileName) const
{
    struct ExpectedSearch
    {
        std::string family;
        std::string query;
    };

    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(
            basePath,
            m_config.assetRoot,
            m_config.assetScaleTier,
            m_config.assetScaleProfile,
            m_config.activeWorldId))
    {
        std::cerr << "Editor headless MM9 inspector search failed: could not initialize asset file system\n";
        return 1;
    }

    std::filesystem::path levelPath =
        activeWorldEditorPath(assetFileSystem, std::filesystem::path("maps") / levelFileName);

    if (!std::filesystem::exists(levelPath))
    {
        levelPath = assetFileSystem.getDevelopmentRoot()
            / std::filesystem::path("worlds")
            / assetFileSystem.getActiveWorldId()
            / "maps"
            / levelFileName;
    }

    EditorSession session;
    session.initialize(assetFileSystem);

    std::string failure;
    if (!session.openMapPhysicalPath(levelPath, failure))
    {
        std::cerr << "Editor headless MM9 inspector search failed: " << failure << '\n';
        return 1;
    }

    const EditorDocument &document = session.document();
    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatLoadedSidecars())
    {
        std::cerr << "Editor headless MM9 inspector search failed: document is not a loaded MM9 DAT level\n";
        return 1;
    }

    const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();
    const std::optional<Mm9ModelInstanceActorSourceLookup> actorSourceLookup =
        loadMm9ModelInstanceActorSourceLookup(assetFileSystem);
    std::vector<Mm9InspectorSearchEntry> entries;

    for (const EditorMm9DatWorldModelSummary &worldModel : sidecars.datWorld.worldModels)
    {
        std::vector<std::string> values = {
            worldModel.sourceName,
            worldModel.kind,
            std::to_string(worldModel.sourceModelIndex),
        };

        for (const EditorMm9DatWorldModelTexture &texture : worldModel.textures)
        {
            values.push_back(texture.sourceTexture);
        }

        appendMm9InspectorSearchEntry(
            entries,
            "world_model",
            worldModel.sourceName,
            std::to_string(worldModel.sourceModelIndex),
            values);
    }

    for (const EditorMm9MaterialTextureStatus &texture : document.mm9MaterialTextureStatuses())
    {
        std::vector<std::string> values = {
            texture.alias,
            texture.sourceTexture,
            texture.sourceAssetFamily,
            texture.physicalPath,
            texture.resolvedSourcePath,
            texture.resolvedSpritePath,
            texture.resolvedCachePath,
        };
        values.insert(values.end(), texture.spriteFrameTextureRefs.begin(), texture.spriteFrameTextureRefs.end());
        values.insert(
            values.end(),
            texture.resolvedSpriteFrameTexturePaths.begin(),
            texture.resolvedSpriteFrameTexturePaths.end());

        appendMm9InspectorSearchEntry(
            entries,
            "texture",
            texture.alias,
            std::to_string(texture.textureIndex),
            values);

        if (!texture.defaultHelperMaterial
            && (texture.placeholderMissingSource
                || !texture.sourceDtxResolved
                || texture.sourceDtxAmbiguous
                || texture.cacheOlderThanSource
                || (texture.cacheDeterminismChecked && !texture.cacheMatchesDecodedSource)))
        {
            appendMm9InspectorSearchEntry(
                entries,
                "diagnostic",
                "material " + texture.alias,
                std::to_string(texture.textureIndex),
                values);
        }
    }

    std::unordered_map<int, std::string> rawObjectNamesByIndex;

    for (const EditorMm9RawObject &rawObject : sidecars.rawObjects.objects)
    {
        rawObjectNamesByIndex[rawObject.objectIndex] = rawObject.name;

        std::vector<std::string> values = {
            rawObject.name,
            std::to_string(rawObject.objectIndex),
        };

        for (const EditorMm9RawObjectProperty &property : rawObject.properties)
        {
            values.push_back(property.name);
            values.push_back(property.valueJson);
        }

        appendMm9InspectorSearchEntry(
            entries,
            "object",
            rawObject.name,
            std::to_string(rawObject.objectIndex),
            values);
    }

    for (const Game::Mm9Object &object : document.mm9ObjectLayer().objects)
    {
        appendMm9InspectorSearchEntry(
            entries,
            "object_source",
            object.sourceName,
            std::to_string(object.sourceObjectIndex),
            {
                object.sourceClass,
                object.sourceName,
                std::to_string(object.sourceObjectIndex),
                object.hasPosition ? std::to_string(object.positionLt.x) : std::string(),
                object.hasPosition ? std::to_string(object.positionLt.y) : std::string(),
                object.hasPosition ? std::to_string(object.positionLt.z) : std::string(),
                object.hasRotation ? std::to_string(object.rotationLt.x) : std::string(),
                object.hasRotation ? std::to_string(object.rotationLt.y) : std::string(),
                object.hasRotation ? std::to_string(object.rotationLt.z) : std::string(),
                object.hasScale ? std::to_string(object.scale) : std::string(),
                object.hasDims ? std::to_string(object.dimsLt.x) : std::string(),
                object.hasDims ? std::to_string(object.dimsLt.y) : std::string(),
                object.hasDims ? std::to_string(object.dimsLt.z) : std::string(),
                object.hasRadius ? std::to_string(object.radius) : std::string(),
                object.visible ? (*object.visible ? "visible" : "hidden") : std::string(),
                object.solid ? (*object.solid ? "solid" : "nonsolid") : std::string(),
                object.triggerVolume ? "trigger_volume" : std::string(),
            });
    }

    for (const EditorMm9RawObjectAssetReferenceStatus &status : document.mm9RawObjectAssetReferenceStatuses())
    {
        const std::string family =
            (status.sourceFamily == "sounds" || status.sourceFamily == "voices") ? "sound" : status.sourceFamily;
        const std::vector<std::string> values = {
            status.sourceClass,
            status.objectName,
            status.propertyName,
            status.sourceFamily,
            status.sourceValue,
            status.resolvedSourcePath,
            status.aliasTargetKey,
        };

        appendMm9InspectorSearchEntry(
            entries,
            family,
            status.objectName,
            std::to_string(status.sourceObjectIndex),
            values);

        if ((!status.resolved || status.ambiguous) && status.required)
        {
            appendMm9InspectorSearchEntry(
                entries,
                "diagnostic",
                "asset " + status.objectName,
                std::to_string(status.sourceObjectIndex),
                values);
        }
    }

    for (const Game::Mm9EventScript &script : sidecars.events.scripts)
    {
        appendMm9InspectorSearchEntry(
            entries,
            "script",
            script.scriptId,
            script.sourcePath,
            {
                script.scriptId,
                script.sourcePath,
                std::to_string(script.includes.size()),
                std::to_string(script.labels.size()),
                std::to_string(script.registeredTriggerCount),
                std::to_string(script.movementCommandCount),
            });
    }

    for (const Game::Mm9EventObject &object : sidecars.events.objects)
    {
        rawObjectNamesByIndex[object.sourceObjectIndex] = object.sourceName;

        appendMm9InspectorSearchEntry(
            entries,
            "event",
            object.objectId,
            std::to_string(object.sourceObjectIndex),
            {
                object.objectId,
                object.sourceClass,
                object.sourceName,
                object.rawObjectRef,
            });
    }

    for (const Game::Mm9EventMechanism &mechanism : sidecars.events.mechanisms)
    {
        appendMm9InspectorSearchEntry(
            entries,
            "mechanism",
            mechanism.mechanismId,
            std::to_string(mechanism.sourceObjectIndex),
            {
                mechanism.mechanismId,
                mechanism.objectId,
                mechanism.sourceClass,
                mechanism.sourceName,
                mechanism.kind,
            });
    }

    for (const Game::Mm9EventBinding &binding : sidecars.events.bindings)
    {
        const std::unordered_map<int, std::string>::const_iterator rawObjectNameIt =
            rawObjectNamesByIndex.find(binding.sourceObjectIndex);
        const std::string rawObjectName =
            rawObjectNameIt != rawObjectNamesByIndex.end() ? rawObjectNameIt->second : std::string();

        for (const Game::Mm9EventBindingTarget &target : binding.targets)
        {
            appendMm9InspectorSearchEntry(
                entries,
                "binding",
                binding.objectId,
                std::to_string(binding.sourceObjectIndex),
                {
                    binding.objectId,
                    rawObjectName,
                    target.targetKind,
                    target.targetId,
                    target.confidence,
                    target.bmodelName,
                    target.sourceModelName,
                });
        }
    }

    for (const Game::Mm9LightObject &light : document.mm9LightLayer().lights)
    {
        appendMm9InspectorSearchEntry(
            entries,
            "light",
            light.sourceName,
            std::to_string(light.sourceObjectIndex),
            {
                light.sourceClass,
                light.sourceName,
                std::to_string(light.sourceObjectIndex),
                light.hasLightRadius ? std::to_string(light.lightRadius) : std::string(),
                light.hasLightGroup ? light.lightGroup : std::string(),
                light.hasPosition ? std::to_string(light.positionLt.x) : std::string(),
                light.hasPosition ? std::to_string(light.positionLt.y) : std::string(),
                light.hasPosition ? std::to_string(light.positionLt.z) : std::string(),
            });
    }

    for (const Game::Mm9SoundObject &sound : document.mm9SoundLayer().objects)
    {
        std::vector<std::string> values = {
            sound.sourceClass,
            sound.sourceName,
            std::to_string(sound.sourceObjectIndex),
            sound.hasSoundRadius ? std::to_string(sound.soundRadius) : std::string(),
            sound.hasPosition ? std::to_string(sound.positionLt.x) : std::string(),
            sound.hasPosition ? std::to_string(sound.positionLt.y) : std::string(),
            sound.hasPosition ? std::to_string(sound.positionLt.z) : std::string(),
        };

        for (const Game::Mm9SoundSourceReference &reference : sound.references)
        {
            values.push_back(reference.propertyName);
            values.push_back(reference.sourceFamily);
            values.push_back(reference.sourceValue);
            values.push_back(reference.normalizedKey);
            values.push_back(reference.resolvedSourcePath);
        }

        appendMm9InspectorSearchEntry(
            entries,
            "sound_object",
            sound.sourceName,
            std::to_string(sound.sourceObjectIndex),
            values);
    }

    for (const Game::Mm9SpawnObject &spawn : document.mm9SpawnLayer().objects)
    {
        appendMm9InspectorSearchEntry(
            entries,
            "spawn_source",
            spawn.sourceName,
            std::to_string(spawn.sourceObjectIndex),
            {
                spawn.sourceClass,
                spawn.sourceName,
                std::to_string(spawn.sourceObjectIndex),
                spawn.spawnLevel ? std::to_string(*spawn.spawnLevel) : std::string(),
                spawn.spawnObject ? *spawn.spawnObject : std::string(),
                spawn.npcProps ? std::to_string(*spawn.npcProps) : std::string(),
                spawn.npcNumber ? std::to_string(*spawn.npcNumber) : std::string(),
                spawn.hasPosition ? std::to_string(spawn.positionLt.x) : std::string(),
                spawn.hasPosition ? std::to_string(spawn.positionLt.y) : std::string(),
                spawn.hasPosition ? std::to_string(spawn.positionLt.z) : std::string(),
            });
    }

    const Mm9MechanismValidationSummary mechanismSummary =
        summarizeMm9Mechanisms(sidecars.events, sidecars.datWorld);

    for (const Mm9MechanismValidationSummary::UnresolvedMechanismTarget &unresolved : mechanismSummary.unresolved)
    {
        std::vector<std::string> values = {
            unresolved.mechanismId,
            unresolved.sourceClass,
            unresolved.sourceName,
            unresolved.targetKind,
            unresolved.confidence,
            unresolved.required ? "required" : "optional",
        };

        for (const Mm9MechanismValidationSummary::CandidateWorldModel &candidate : unresolved.nearestWorldModels)
        {
            values.push_back(candidate.sourceName);
            values.push_back(std::to_string(candidate.sourceModelIndex));
        }

        appendMm9InspectorSearchEntry(
            entries,
            "diagnostic",
            "mechanism " + unresolved.sourceName,
            std::to_string(unresolved.sourceObjectIndex),
            values);
    }

    for (const std::string &diagnostic : document.validate())
    {
        appendMm9InspectorSearchEntry(entries, "diagnostic", "document validation", levelFileName, {diagnostic});
    }

    for (const Game::OutdoorSceneModelInstance &modelInstance : sceneData.modelInstances)
    {
        const std::vector<std::string> values = {
            modelInstance.instanceId,
            modelInstance.sourceRef,
            modelInstance.sourceKind,
            modelInstance.sourceClass,
            modelInstance.sourceName,
            modelInstance.sourceModel,
            modelInstance.sourceSkin,
            modelInstance.modelAsset,
            modelInstance.modelSkinBinding,
        };

        appendMm9InspectorSearchEntry(
            entries,
            "model",
            modelInstance.instanceId,
            modelInstance.sourceRef,
            values);

        const Mm9ResolvedModelInstanceActorSource resolvedSource =
            resolveMm9ModelInstanceActorSource(
                modelInstance,
                actorSourceLookup ? &*actorSourceLookup : nullptr);

        appendMm9InspectorSearchEntry(
            entries,
            "actor_variant",
            resolvedSource.variantId.empty() ? modelInstance.sourceName : resolvedSource.variantId,
            modelInstance.sourceRef,
            {
                resolvedSource.variantId,
                resolvedSource.sourceModel,
                resolvedSource.sourceSkin,
                resolvedSource.inferredFromActorClass ? "actor table" : "object source",
                mm9ModelInstanceActorVariantAssetPath(resolvedSource.sourceModel, resolvedSource.sourceSkin),
                modelInstance.sourceClass,
                modelInstance.sourceName,
                resolvedSource.actorRow.level,
                resolvedSource.actorRow.hitPoints,
                resolvedSource.actorRow.armorClass,
                resolvedSource.actorRow.speed,
                resolvedSource.actorRow.hostilityGroup,
                resolvedSource.actorRow.scriptName,
                resolvedSource.actorRow.footSound,
                resolvedSource.actorRow.voiceRadius,
            });
    }

    std::vector<ExpectedSearch> expectedSearches = {
        {"texture", "RAIL"},
        {"world_model", "BlueWater0"},
        {"object", "BlueWater0"},
        {"script", "PROPANIM.scr"},
        {"model", "Barrel"},
        {"actor_variant", "peasant"},
        {"light", "Light"},
        {"sound_object", "Sound"},
        {"diagnostic", "MTNDOWN"},
    };

    if (document.mm9DatLevelMetadata().mapId == "thjorgardcity")
    {
        expectedSearches.push_back({"object", "BembStudy3"});
        expectedSearches.push_back({"mechanism", "BembStudy3"});
        expectedSearches.push_back({"binding", "BembStudy3"});
        expectedSearches.push_back({"binding", "shared_rotation_point_exact_source_object_position"});
    }
    else
    {
        expectedSearches.push_back({"object", "HalfOrcCaptain0"});
    }

    for (const ExpectedSearch &expected : expectedSearches)
    {
        const size_t matches = countMm9InspectorSearchMatches(entries, expected.family, expected.query);

        if (matches == 0)
        {
            std::cerr
                << "Editor headless MM9 inspector search failed: query did not match"
                << " level=" << levelFileName
                << " family=" << expected.family
                << " query=" << expected.query << '\n';
            return 1;
        }
    }

    std::cout
        << "Editor headless MM9 inspector search passed: " << levelFileName
        << " entries=" << entries.size()
        << " world_models=" << countMm9InspectorSearchFamily(entries, "world_model")
        << " textures=" << countMm9InspectorSearchFamily(entries, "texture")
        << " objects=" << countMm9InspectorSearchFamily(entries, "object")
        << " object_sources=" << countMm9InspectorSearchFamily(entries, "object_source")
        << " scripts=" << countMm9InspectorSearchFamily(entries, "script")
        << " sounds=" << countMm9InspectorSearchFamily(entries, "sound")
        << " lights=" << countMm9InspectorSearchFamily(entries, "light")
        << " sound_objects=" << countMm9InspectorSearchFamily(entries, "sound_object")
        << " spawn_sources=" << countMm9InspectorSearchFamily(entries, "spawn_source")
        << " models=" << countMm9InspectorSearchFamily(entries, "model")
        << " actor_variants=" << countMm9InspectorSearchFamily(entries, "actor_variant")
        << " diagnostics=" << countMm9InspectorSearchFamily(entries, "diagnostic")
        << '\n';
    return 0;
}

int EditorHeadlessDiagnostics::runVerifyDocumentDispatch(const std::filesystem::path &basePath) const
{
    struct DispatchCase
    {
        std::string worldId;
        std::filesystem::path mapRelativePath;
        EditorDocument::Kind expectedKind;
        bool requireMm9Sidecars = false;
    };

    const auto kindName = [](EditorDocument::Kind kind) -> const char *
    {
        switch (kind)
        {
        case EditorDocument::Kind::None:
            return "None";
        case EditorDocument::Kind::Outdoor:
            return "Outdoor";
        case EditorDocument::Kind::Indoor:
            return "Indoor";
        case EditorDocument::Kind::Mm9Dat:
            return "Mm9Dat";
        }

        return "Unknown";
    };

    const std::vector<DispatchCase> dispatchCases = {
        {"mm9", "thjorgard.level.yml", EditorDocument::Kind::Mm9Dat, true},
        {"mm9", "thjorgardcity.level.yml", EditorDocument::Kind::Mm9Dat, true},
        {"mm8", "out01.odm", EditorDocument::Kind::Outdoor, false},
        {"mm8", "d18.blv", EditorDocument::Kind::Indoor, false},
        {"mm7", "7out01.odm", EditorDocument::Kind::Outdoor, false},
        {"mm7", "7d06.blv", EditorDocument::Kind::Indoor, false},
        {"mm6", "oute3.odm", EditorDocument::Kind::Outdoor, false},
        {"mm6", "6d01.blv", EditorDocument::Kind::Indoor, false},
    };

    size_t verifiedCases = 0;
    size_t verifiedMm9Cases = 0;
    size_t verifiedOutdoorCases = 0;
    size_t verifiedIndoorCases = 0;

    for (const DispatchCase &dispatchCase : dispatchCases)
    {
        Engine::AssetFileSystem assetFileSystem;

        if (!assetFileSystem.initialize(
                basePath,
                m_config.assetRoot,
                m_config.assetScaleTier,
                m_config.assetScaleProfile,
                dispatchCase.worldId))
        {
            std::cerr
                << "Editor headless document dispatch failed: could not initialize asset file system for world "
                << dispatchCase.worldId << '\n';
            return 1;
        }

        std::filesystem::path mapPath =
            assetFileSystem.getDevelopmentRoot()
            / std::filesystem::path("worlds")
            / dispatchCase.worldId
            / "maps"
            / dispatchCase.mapRelativePath;

        if (!std::filesystem::exists(mapPath))
        {
            mapPath =
                assetFileSystem.getEditorDevelopmentRoot()
                / std::filesystem::path("worlds")
                / dispatchCase.worldId
                / "maps"
                / dispatchCase.mapRelativePath;
        }

        if (!std::filesystem::exists(mapPath))
        {
            std::cerr
                << "Editor headless document dispatch failed: missing map path "
                << dispatchCase.worldId << "/" << dispatchCase.mapRelativePath.generic_string() << '\n';
            return 1;
        }

        EditorDocument document;
        std::string failure;

        if (!document.loadMapPhysicalPath(assetFileSystem, mapPath, failure))
        {
            std::cerr
                << "Editor headless document dispatch failed: could not open "
                << mapPath.generic_string() << ": " << failure << '\n';
            return 1;
        }

        if (document.kind() != dispatchCase.expectedKind)
        {
            std::cerr
                << "Editor headless document dispatch failed: "
                << dispatchCase.worldId << "/" << dispatchCase.mapRelativePath.generic_string()
                << " expected_kind=" << kindName(dispatchCase.expectedKind)
                << " actual_kind=" << kindName(document.kind()) << '\n';
            return 1;
        }

        if (dispatchCase.expectedKind != EditorDocument::Kind::Mm9Dat && document.hasMm9DatLoadedSidecars())
        {
            std::cerr
                << "Editor headless document dispatch failed: legacy map unexpectedly loaded MM9 sidecars for "
                << dispatchCase.worldId << "/" << dispatchCase.mapRelativePath.generic_string() << '\n';
            return 1;
        }

        if (dispatchCase.requireMm9Sidecars
            && (!document.hasMm9DatLoadedSidecars()
                || !document.hasMm9DatWorld()
                || document.mm9DatRenderMesh().triangles.empty()))
        {
            std::cerr
                << "Editor headless document dispatch failed: MM9 level did not load native DAT sidecars/world for "
                << dispatchCase.worldId << "/" << dispatchCase.mapRelativePath.generic_string() << '\n';
            return 1;
        }

        ++verifiedCases;

        if (document.kind() == EditorDocument::Kind::Mm9Dat)
        {
            ++verifiedMm9Cases;
        }
        else if (document.kind() == EditorDocument::Kind::Outdoor)
        {
            ++verifiedOutdoorCases;
        }
        else if (document.kind() == EditorDocument::Kind::Indoor)
        {
            ++verifiedIndoorCases;
        }
    }

    std::cout
        << "Editor headless document dispatch passed:"
        << " cases=" << verifiedCases
        << " mm9_dat=" << verifiedMm9Cases
        << " outdoor=" << verifiedOutdoorCases
        << " indoor=" << verifiedIndoorCases << '\n';
    return 0;
}

int EditorHeadlessDiagnostics::runVerifyAllMm9DatLevels(const std::filesystem::path &basePath) const
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(
            basePath,
            m_config.assetRoot,
            m_config.assetScaleTier,
            m_config.assetScaleProfile,
            m_config.activeWorldId))
    {
        std::cerr << "Editor headless diagnostics failed: could not initialize asset file system\n";
        return 1;
    }

    std::filesystem::path mapsRoot = activeWorldEditorPath(assetFileSystem, "maps");

    if (!std::filesystem::exists(mapsRoot))
    {
        mapsRoot = assetFileSystem.getDevelopmentRoot()
            / std::filesystem::path("worlds")
            / assetFileSystem.getActiveWorldId()
            / "maps";
    }

    if (!std::filesystem::exists(mapsRoot))
    {
        std::cerr << "Editor headless MM9 DAT all-level verification failed: maps root is missing: "
                  << mapsRoot.generic_string() << '\n';
        return 1;
    }

    const auto collectLevelPaths =
        [](const std::filesystem::path &root)
        {
            std::vector<std::filesystem::path> paths;

            if (!std::filesystem::exists(root))
            {
                return paths;
            }

            for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(root))
            {
                if (!entry.is_regular_file())
                {
                    continue;
                }

                const std::string fileName = entry.path().filename().string();

                if (fileName.size() >= 10 && fileName.ends_with(".level.yml"))
                {
                    paths.push_back(entry.path());
                }
            }

            std::sort(paths.begin(), paths.end());
            return paths;
        };

    std::vector<std::filesystem::path> levelPaths = collectLevelPaths(mapsRoot);

    if (levelPaths.empty())
    {
        mapsRoot = assetFileSystem.getDevelopmentRoot()
            / std::filesystem::path("worlds")
            / assetFileSystem.getActiveWorldId()
            / "maps";
        levelPaths = collectLevelPaths(mapsRoot);
    }

    if (levelPaths.empty())
    {
        std::cerr << "Editor headless MM9 DAT all-level verification failed: no *.level.yml files found in "
                  << mapsRoot.generic_string() << '\n';
        return 1;
    }

    EditorDocument document;
    size_t totalWorldModels = 0;
    size_t totalMaterials = 0;
    size_t totalResolvedTextures = 0;
    size_t totalSourceDtxHashes = 0;
    size_t totalCacheHashes = 0;
    size_t totalStaleCaches = 0;
    size_t totalDecodedCacheChecks = 0;
    size_t totalDecodedCacheMatches = 0;
    size_t totalDecodedPBlocks = 0;
    size_t totalEventObjects = 0;
    size_t totalRawObjectAssetReferences = 0;
    size_t totalUnresolvedRawObjectAssetReferences = 0;
    size_t totalUnresolvedOptionalRawObjectAssetReferences = 0;
    size_t totalAssetGraphReferences = 0;
    size_t totalAssetGraphResolved = 0;
    size_t totalAssetGraphUnresolved = 0;
    size_t totalAssetGraphAmbiguous = 0;
    size_t totalAssetGraphStale = 0;
    size_t totalAssetGraphRequiredUnresolved = 0;
    size_t totalAssetGraphRequiredAmbiguous = 0;
    size_t totalAssetGraphOptionalUnresolved = 0;
    size_t totalAssetGraphSourceOnly = 0;
    size_t totalAssetGraphUnusedSource = 0;
    size_t totalReadOnlySourcePaths = 0;
    size_t totalGeneratedPaths = 0;
    size_t totalAuthoredPaths = 0;
    size_t totalNativeMeshTriangles = 0;
    size_t totalNativeMeshDegenerateTriangles = 0;
    size_t totalNativeSyntheticPicks = 0;
    size_t totalNativeMaterialAssignments = 0;
    size_t totalNativeMaterialPreviews = 0;
    size_t totalNativeCameraFrames = 0;
    size_t totalNativeFilterVisual = 0;
    size_t totalNativeFilterInvisible = 0;
    size_t totalNativeFilterHelper = 0;
    size_t totalNativeFilterPhysics = 0;
    size_t totalNativeFilterVisibility = 0;
    size_t totalNativeFilterPortals = 0;
    size_t portalizedMapCount = 0;

    for (const std::filesystem::path &levelPath : levelPaths)
    {
        std::string failure;

        if (!document.loadMapPhysicalPath(assetFileSystem, levelPath, failure))
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << levelPath.filename().string() << ": " << failure << '\n';
            return 1;
        }

        if (document.kind() != EditorDocument::Kind::Mm9Dat)
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << levelPath.filename().string() << ": document kind is not Mm9Dat\n";
            return 1;
        }

        const std::string fileName = levelPath.filename().string();
        const std::string expectedMapId = fileName.substr(0, fileName.size() - std::string(".level.yml").size());

        if (document.mm9DatLevelMetadata().mapId != expectedMapId)
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": stale or mismatched map id, expected=" << expectedMapId
                      << " actual=" << document.mm9DatLevelMetadata().mapId << '\n';
            return 1;
        }

        if (!document.hasMm9DatLoadedSidecars())
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": sidecars were not loaded\n";
            return 1;
        }

        if (!document.hasMm9DatWorld() || document.mm9DatRenderMesh().triangles.empty())
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": source DAT world render mesh was not built\n";
            return 1;
        }

        const std::vector<std::string> diagnostics = document.validate();

        if (!diagnostics.empty())
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": validation diagnostics:\n";

            for (const std::string &diagnostic : diagnostics)
            {
                std::cerr << "  " << diagnostic << '\n';
            }

            return 1;
        }

        const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
        const Game::Mm9DatRenderMesh &datRenderMesh = document.mm9DatRenderMesh();
        size_t readOnlySourcePathCount = 0;
        size_t generatedPathCount = 0;
        size_t authoredPathCount = 0;
        size_t resolvedTextureCount = 0;
        size_t loadedDtxHeaderCount = 0;
        size_t sourceDtxHashCount = 0;
        size_t cacheHashCount = 0;
        size_t staleCacheCount = 0;
        size_t decodedCacheCheckCount = 0;
        size_t decodedCacheMatchCount = 0;
        size_t unresolvedRawObjectAssetReferenceCount = 0;
        size_t unresolvedOptionalRawObjectAssetReferenceCount = 0;

        for (const EditorMm9MaterialTextureStatus &status : document.mm9MaterialTextureStatuses())
        {
            if (status.sourceDtxResolved)
            {
                ++resolvedTextureCount;
            }

            if (status.dtxHeaderLoaded)
            {
                ++loadedDtxHeaderCount;
            }

            if (status.sourceDtxHashLoaded)
            {
                ++sourceDtxHashCount;
            }

            if (status.cacheHashLoaded)
            {
                ++cacheHashCount;
            }

            if (status.cacheOlderThanSource)
            {
                ++staleCacheCount;
            }

            if (status.cacheDeterminismChecked)
            {
                ++decodedCacheCheckCount;

                if (status.cacheMatchesDecodedSource)
                {
                    ++decodedCacheMatchCount;
                }
                else
                {
                    std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                              << fileName << ": decoded material cache does not match source DTX: "
                              << status.sourceTexture << " reason=" << status.cacheDeterminismMessage << '\n';
                    return 1;
                }
            }
        }

        for (const EditorMm9RawObjectAssetReferenceStatus &status : document.mm9RawObjectAssetReferenceStatuses())
        {
            if (!status.resolved || status.ambiguous)
            {
                if (status.required)
                {
                    ++unresolvedRawObjectAssetReferenceCount;
                }
                else
                {
                    ++unresolvedOptionalRawObjectAssetReferenceCount;
                }
            }
        }

        for (const EditorMm9DocumentPathStatus &status : document.mm9DocumentPathStatuses())
        {
            if (status.sourceReadOnly)
            {
                ++readOnlySourcePathCount;

                if (!status.exists)
                {
                    std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                              << fileName << ": read-only source path is missing: "
                              << status.resolvedPath << '\n';
                    return 1;
                }
            }

            if (status.generated)
            {
                ++generatedPathCount;
            }

            if (status.authored)
            {
                ++authoredPathCount;
            }
        }

        if (document.mm9DatWorld().worldModels.size() != sidecars.datWorld.worldModels.size()
            || datRenderMesh.sourcePolyCount != sidecars.datWorld.totals.sourcePolyCount)
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": parsed DAT geometry counts do not match sidecar\n";
            return 1;
        }

        if (document.mm9DatRenderMaterialAssignments().size() != datRenderMesh.triangles.size())
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": native material assignment count does not match mesh\n";
            return 1;
        }

        const Game::Mm9DatRenderBounds nativeBounds = Game::computeMm9DatRenderBounds(datRenderMesh);
        const Game::Mm9DatCameraFrame nativeCameraFrame = Game::frameMm9DatRenderMeshCamera(datRenderMesh);
        const Game::Mm9DatRenderFilterResult nativeFilters =
            Game::classifyMm9DatRenderMeshFilters(
                datRenderMesh,
                mm9ModelRenderRolesFromSidecar(sidecars.datWorld),
                sidecars.datWorld.userPortals.size());

        if (!nativeBounds.valid || !nativeCameraFrame.valid)
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": native DAT camera frame could not be built\n";
            return 1;
        }

        if (nativeFilters.entries.size() != datRenderMesh.triangles.size()
            || nativeFilters.summary.totalTriangles != datRenderMesh.triangles.size()
            || nativeFilters.summary.unclassifiedTriangles != 0)
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": native DAT display filters are incomplete\n";
            return 1;
        }

        size_t nativeMaterialPreviewCount = 0;

        for (const Game::Mm9DatRenderMaterialAssignment &assignment : document.mm9DatRenderMaterialAssignments())
        {
            if (!assignment.assigned || assignment.ambiguous)
            {
                std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                          << fileName << ": native mesh triangle has no unique material alias: "
                          << assignment.sourceTexture << '\n';
                return 1;
            }

            if (assignment.previewCacheAvailable)
            {
                ++nativeMaterialPreviewCount;
            }
        }

        std::optional<Game::Mm9DatRenderMeshPickHit> nativePickHit;
        std::string nativePickFailure;

        if (!validateMm9SyntheticPick(datRenderMesh, nativePickHit, nativePickFailure))
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": " << nativePickFailure << '\n';
            return 1;
        }

        if (readOnlySourcePathCount < 2 || generatedPathCount == 0 || authoredPathCount == 0)
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": incomplete document path role inventory\n";
            return 1;
        }

        std::string saveFailure;

        if (document.saveSource(saveFailure)
            || saveFailure.find("source/* immutable") == std::string::npos)
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": MM9 saveSource did not reject source mutation: "
                      << saveFailure << '\n';
            return 1;
        }

        std::string buildFailure;

        if (document.buildRuntime(buildFailure)
            || buildFailure.find("DAT/DTX runtime path") == std::string::npos)
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": MM9 buildRuntime did not reject ODM/BLV build: "
                      << buildFailure << '\n';
            return 1;
        }

        if (!sidecars.materialAliases.textures.empty()
            && (resolvedTextureCount == 0 || loadedDtxHeaderCount == 0))
        {
            std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                      << fileName << ": material inspection did not resolve any source DTX/header\n";
            return 1;
        }

        if (document.mm9DatLevelMetadata().runtime.visibility == "dat_bsp_portal")
        {
            ++portalizedMapCount;

            if (sidecars.datWorld.totals.leafCount == 0)
            {
                std::cerr << "Editor headless MM9 DAT all-level verification failed for "
                          << fileName << ": portalized DAT map has no decoded leaves\n";
                return 1;
            }
        }

        totalWorldModels += sidecars.datWorld.worldModels.size();
        totalMaterials += sidecars.materialAliases.textures.size();
        totalResolvedTextures += resolvedTextureCount;
        totalSourceDtxHashes += sourceDtxHashCount;
        totalCacheHashes += cacheHashCount;
        totalStaleCaches += staleCacheCount;
        totalDecodedCacheChecks += decodedCacheCheckCount;
        totalDecodedCacheMatches += decodedCacheMatchCount;
        totalEventObjects += sidecars.events.objects.size();
        totalRawObjectAssetReferences += document.mm9RawObjectAssetReferenceStatuses().size();
        totalUnresolvedRawObjectAssetReferences += unresolvedRawObjectAssetReferenceCount;
        totalUnresolvedOptionalRawObjectAssetReferences += unresolvedOptionalRawObjectAssetReferenceCount;
        totalAssetGraphReferences += document.mm9AssetDependencySummary().total;
        totalAssetGraphResolved += document.mm9AssetDependencySummary().resolved;
        totalAssetGraphUnresolved += document.mm9AssetDependencySummary().unresolved;
        totalAssetGraphAmbiguous += document.mm9AssetDependencySummary().ambiguous;
        totalAssetGraphStale += document.mm9AssetDependencySummary().stale;
        totalAssetGraphRequiredUnresolved += document.mm9AssetDependencySummary().requiredUnresolved;
        totalAssetGraphRequiredAmbiguous += document.mm9AssetDependencySummary().requiredAmbiguous;
        totalAssetGraphOptionalUnresolved += document.mm9AssetDependencySummary().optionalUnresolved;
        totalAssetGraphSourceOnly += document.mm9AssetDependencySummary().sourceOnly;
        totalAssetGraphUnusedSource += document.mm9AssetDependencySummary().unusedSource;
        totalReadOnlySourcePaths += readOnlySourcePathCount;
        totalGeneratedPaths += generatedPathCount;
        totalAuthoredPaths += authoredPathCount;
        totalNativeMeshTriangles += datRenderMesh.triangles.size();
        totalNativeMeshDegenerateTriangles += datRenderMesh.skippedDegenerateTriangleCount;
        ++totalNativeSyntheticPicks;
        totalNativeMaterialAssignments += document.mm9DatRenderMaterialAssignments().size();
        totalNativeMaterialPreviews += nativeMaterialPreviewCount;
        ++totalNativeCameraFrames;
        totalNativeFilterVisual += nativeFilters.summary.visualTriangles;
        totalNativeFilterInvisible += nativeFilters.summary.invisibleTriangles;
        totalNativeFilterHelper += nativeFilters.summary.helperTriangles;
        totalNativeFilterPhysics += nativeFilters.summary.physicsTriangles;
        totalNativeFilterVisibility += nativeFilters.summary.visibilityTriangles;
        totalNativeFilterPortals += nativeFilters.summary.portalOverlays;

        for (const EditorMm9DatWorldModelSummary &model : sidecars.datWorld.worldModels)
        {
            if (model.pblockTable.decodedSummary && model.pblockTable.recordCount)
            {
                ++totalDecodedPBlocks;
            }
        }
    }

    std::cout << "Editor headless MM9 DAT all-level verification passed:"
              << " levels=" << levelPaths.size()
              << " portalized=" << portalizedMapCount
              << " world_models=" << totalWorldModels
              << " materials=" << totalMaterials
              << " resolved_dtx=" << totalResolvedTextures
              << " source_dtx_hashes=" << totalSourceDtxHashes
              << " cache_hashes=" << totalCacheHashes
              << " stale_caches=" << totalStaleCaches
              << " decoded_cache_checks=" << totalDecodedCacheChecks
              << " decoded_cache_matches=" << totalDecodedCacheMatches
              << " decoded_pblocks=" << totalDecodedPBlocks
              << " raw_object_asset_refs=" << totalRawObjectAssetReferences
              << " unresolved_raw_object_asset_refs=" << totalUnresolvedRawObjectAssetReferences
              << " unresolved_optional_raw_object_asset_refs="
              << totalUnresolvedOptionalRawObjectAssetReferences
              << " asset_graph_total=" << totalAssetGraphReferences
              << " asset_graph_resolved=" << totalAssetGraphResolved
              << " asset_graph_unresolved=" << totalAssetGraphUnresolved
              << " asset_graph_ambiguous=" << totalAssetGraphAmbiguous
              << " asset_graph_stale=" << totalAssetGraphStale
              << " asset_graph_required_unresolved=" << totalAssetGraphRequiredUnresolved
              << " asset_graph_required_ambiguous=" << totalAssetGraphRequiredAmbiguous
              << " asset_graph_optional_unresolved=" << totalAssetGraphOptionalUnresolved
              << " asset_graph_source_only=" << totalAssetGraphSourceOnly
              << " asset_graph_unused_source=" << totalAssetGraphUnusedSource
              << " readonly_source_paths=" << totalReadOnlySourcePaths
              << " generated_paths=" << totalGeneratedPaths
              << " authored_paths=" << totalAuthoredPaths
              << " native_mesh_triangles=" << totalNativeMeshTriangles
              << " native_mesh_degenerate_triangles=" << totalNativeMeshDegenerateTriangles
              << " native_synthetic_picks=" << totalNativeSyntheticPicks
              << " native_material_assignments=" << totalNativeMaterialAssignments
              << " native_material_previews=" << totalNativeMaterialPreviews
              << " native_camera_frames=" << totalNativeCameraFrames
              << " native_filter_visual=" << totalNativeFilterVisual
              << " native_filter_invisible=" << totalNativeFilterInvisible
              << " native_filter_helper=" << totalNativeFilterHelper
              << " native_filter_physics=" << totalNativeFilterPhysics
              << " native_filter_visibility=" << totalNativeFilterVisibility
              << " native_filter_portals=" << totalNativeFilterPortals
              << " event_objects=" << totalEventObjects << '\n';
    return 0;
}
}
