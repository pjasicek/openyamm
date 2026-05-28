#pragma once

#include "game/maps/Mm9EventsYml.h"
#include "game/mm9/Mm9LightLayer.h"
#include "game/mm9/Mm9ObjectLayer.h"
#include "game/mm9/Mm9SoundLayer.h"
#include "game/mm9/Mm9SpawnLayer.h"

#include <array>
#include <filesystem>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Editor
{
struct EditorMm9DatLevelSource
{
    std::string dat;
    std::string originalDat;
    std::string sourceGame;
    int datVersion = 0;
    std::string contentHash;
};

struct EditorMm9DatLevelRuntime
{
    std::string worldBackend;
    std::string classification;
    std::string classificationConfidence;
    std::string visibility;
    std::string collision;
    std::string render;
    bool sky = false;
};

struct EditorMm9DatLevelSidecars
{
    std::string datWorld;
    std::string rawObjects;
    std::string materials;
    std::string events;
    std::optional<std::string> sourceAssetAliases;
    std::optional<std::string> sceneCompat;
    std::optional<std::string> sourceMetadataCompat;
    std::optional<std::string> bspCompat;
    std::optional<std::string> geometryCompat;
    std::optional<std::string> modelAssetsCompat;
    std::optional<std::string> odmCompat;
    std::optional<std::string> blvCompat;
};

struct EditorMm9DatLevelScripts
{
    std::string level;
    std::string scriptIr;
};

struct EditorMm9DatLevelCompatibility
{
    std::string legacyTargetFormat;
    bool generatedOdmBlvAreDerived = false;
};

struct EditorMm9DatLevelMetadata
{
    int formatVersion = 0;
    std::string kind;
    std::string mapId;
    std::string displayName;
    EditorMm9DatLevelSource source;
    EditorMm9DatLevelRuntime runtime;
    EditorMm9DatLevelSidecars sidecars;
    EditorMm9DatLevelScripts scripts;
    EditorMm9DatLevelCompatibility compatibility;
};

struct EditorMm9DatWorldTotals
{
    size_t worldModelCount = 0;
    size_t objectCount = 0;
    size_t sourcePolyCount = 0;
    size_t surfaceCount = 0;
    size_t userPortalCount = 0;
    size_t leafCount = 0;
    size_t leafReferenceCount = 0;
    size_t invalidLeafReferenceCount = 0;
};

struct EditorMm9Vec3
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct EditorMm9DatWorldCoordinateSystem
{
    std::string source;
    std::vector<std::string> openYammMapping;
    float scale = 0.0f;
};

struct EditorMm9DatWorldInfo
{
    std::string propertyString;
    float lightMapGridSize = 0.0f;
    EditorMm9Vec3 extentsMinLt;
    EditorMm9Vec3 extentsMaxLt;
};

struct EditorMm9DatWorldModelPBlockTable
{
    bool preservedInSourceDat = false;
    bool decodedSummary = false;
    size_t dimA = 0;
    size_t dimB = 0;
    size_t dimC = 0;
    EditorMm9Vec3 boundsMinLt;
    EditorMm9Vec3 boundsMaxLt;
    std::optional<size_t> recordCount;
};

struct EditorMm9DatWorldModelBspCounts
{
    size_t vertCount = 0;
    size_t totalVisListSize = 0;
    size_t leafListCount = 0;
    size_t textureNameLength = 0;
    size_t textureCount = 0;
};

struct EditorMm9DatWorldModelUnknownValues
{
    uint32_t worldBspUnknownValue = 0;
    uint32_t worldBspUnknownValue2 = 0;
    uint32_t worldBspUnknownValue3 = 0;
};

struct EditorMm9DatWorldModelReferenceValidation
{
    size_t invalidSurfaceTextureRefs = 0;
    size_t invalidPolySurfaceRefs = 0;
    size_t invalidPolyPlaneRefs = 0;
    size_t invalidPolyVertexRefs = 0;
    size_t invalidNodePolyRefs = 0;
    size_t invalidRootNodeRefs = 0;
};

struct EditorMm9DatWorldModelTexture
{
    size_t textureIndex = 0;
    std::string sourceTexture;
};

struct EditorMm9DatWorldHistogramEntry
{
    int key = 0;
    size_t count = 0;
};

struct EditorMm9DatWorldModelRoles
{
    bool visible = false;
    bool terrain = false;
    bool physicsBsp = false;
    bool visBsp = false;
    bool sky = false;
    bool water = false;
    bool triggerOrVolume = false;
    bool movable = false;
};

struct EditorMm9DatWorldModelSummary
{
    size_t sourceModelIndex = 0;
    std::string sourceName;
    std::string kind;
    uint32_t worldInfoFlags = 0;
    size_t pointCount = 0;
    size_t planeCount = 0;
    size_t surfaceCount = 0;
    size_t polyCount = 0;
    size_t leafCount = 0;
    size_t nodeCount = 0;
    size_t userPortalCount = 0;
    size_t textureCount = 0;
    size_t rootNodeIndex = 0;
    size_t sectionCount = 0;
    EditorMm9DatWorldModelBspCounts bspCounts;
    EditorMm9DatWorldModelUnknownValues unknownValues;
    EditorMm9DatWorldModelReferenceValidation referenceValidation;
    EditorMm9DatWorldModelPBlockTable pblockTable;
    EditorMm9Vec3 boundsMinLt;
    EditorMm9Vec3 boundsMaxLt;
    EditorMm9Vec3 worldTranslationLt;
    std::vector<EditorMm9DatWorldModelTexture> textures;
    std::vector<EditorMm9DatWorldHistogramEntry> surfaceFlagHistogram;
    std::vector<EditorMm9DatWorldHistogramEntry> textureUserFlagHistogram;
    EditorMm9DatWorldModelRoles roles;
};

struct EditorMm9DatUserPortalRawUnknowns
{
    int unknownInt1 = 0;
    int unknownShort = 0;
};

struct EditorMm9DatUserPortalSummary
{
    size_t sourceModelIndex = 0;
    std::string sourceModelName;
    size_t portalIndex = 0;
    std::string name;
    EditorMm9Vec3 centerLt;
    EditorMm9Vec3 dimsLt;
    EditorMm9DatUserPortalRawUnknowns rawUnknowns;
};

struct EditorMm9DatLeafReferenceSummary
{
    std::string decode;
    size_t totalRefs = 0;
    size_t invalidRefs = 0;
};

struct EditorMm9DatWorldValidationSummary
{
    std::string parseStatus;
    std::string unknownFieldPolicy;
    std::string pblockSummaryStatus;
};

struct EditorMm9DatWorldSidecar
{
    int formatVersion = 0;
    std::string kind;
    std::string mapId;
    std::string sourceDat;
    std::string sourceHash;
    int datVersion = 0;
    EditorMm9DatWorldCoordinateSystem coordinateSystem;
    EditorMm9DatWorldInfo worldInfo;
    std::string classification;
    std::string classificationConfidence;
    std::string classificationReason;
    EditorMm9DatWorldTotals totals;
    std::vector<EditorMm9DatWorldModelSummary> worldModels;
    std::vector<EditorMm9DatUserPortalSummary> userPortals;
    EditorMm9DatLeafReferenceSummary leafReferences;
    EditorMm9DatWorldValidationSummary validation;
};

struct EditorMm9MaterialAliasStats
{
    size_t sourceModels = 0;
    size_t sourcePolies = 0;
    size_t emittedFaces = 0;
    size_t skippedPolies = 0;
    size_t triangulatedPolies = 0;
    size_t skippedDegenerateTriangles = 0;
    size_t modelInstances = 0;
    size_t uniqueModelAssets = 0;
};

struct EditorMm9MaterialTexture
{
    std::string alias;
    std::string sourceTexture;
    std::string physicalPath;
    std::string emittedBitmap;
    std::string emittedBitmapMode;
    int width = 0;
    int height = 0;
    int dtxSurfaceFlag = 0;
    int dtxTextureGroup = 0;
    int dtxBpp = 0;
    int dtxMipmapCount = 0;
    int dtxMipmapsUsed = 0;
    int dtxFlags = 0;
    float dtxDetailScale = 0.0f;
    int dtxDetailAngle = 0;
    std::string dtxCommandString;
};

struct EditorMm9MaterialAliasesSidecar
{
    int formatVersion = 0;
    std::string kind;
    std::string sourceDat;
    EditorMm9MaterialAliasStats stats;
    std::vector<EditorMm9MaterialTexture> textures;
};

struct EditorMm9DtxMipLevel
{
    size_t level = 0;
    uint32_t width = 0;
    uint32_t height = 0;
    size_t payloadOffset = 0;
    size_t payloadSize = 0;
    bool payloadAvailable = false;
    bool decodedPreviewAvailable = false;
};

struct EditorMm9DtxSection
{
    size_t sectionIndex = 0;
    std::string type;
    std::string name;
    size_t payloadOffset = 0;
    size_t payloadSize = 0;
    bool payloadAvailable = false;
};

struct EditorMm9DtxHeader
{
    int fileType = 0;
    int version = 0;
    int width = 0;
    int height = 0;
    int mipmapCount = 0;
    int lightFlag = 0;
    int sectionCount = 0;
    int flags = 0;
    int unknown = 0;
    int surfaceFlag = 0;
    int userFlags = 0;
    int textureGroup = 0;
    int mipmapsUsed = 0;
    int bpp = 0;
    int nonS3tcOffset = 0;
    int uiMipmapOffset = 0;
    int texturePriority = 0;
    float detailScale = 0.0f;
    int detailAngle = 0;
    std::array<int, 12> extraBytes = {};
    std::string commandString;
    std::vector<EditorMm9DtxMipLevel> mips;
    std::vector<EditorMm9DtxSection> sections;
    size_t trailingBytes = 0;
};

struct EditorMm9MaterialTextureStatus
{
    size_t textureIndex = 0;
    std::string alias;
    std::string sourceTexture;
    std::string sourceAssetFamily;
    std::string physicalPath;
    std::string resolvedSourcePath;
    std::string resolvedSpritePath;
    std::string sourceDtxSha256;
    std::string emittedBitmap;
    std::string resolvedCachePath;
    std::string cacheSha256;
    std::string emittedBitmapMode;
    std::vector<std::string> sourceDtxCandidates;
    std::vector<std::string> sourceSpriteCandidates;
    std::vector<std::string> spriteFrameTextureRefs;
    std::vector<std::string> resolvedSpriteFrameTexturePaths;
    std::vector<std::string> unresolvedSpriteFrameTextureRefs;
    std::vector<std::string> ambiguousSpriteFrameTextureRefs;
    uintmax_t sourceDtxSizeBytes = 0;
    uintmax_t cacheSizeBytes = 0;
    size_t datReferenceCount = 0;
    size_t materialAliasCountForSource = 0;
    size_t sourceDtxCandidateCount = 0;
    size_t sourceSpriteCandidateCount = 0;
    size_t spriteFrameTextureCount = 0;
    size_t resolvedSpriteFrameTextureCount = 0;
    size_t unresolvedSpriteFrameTextureCount = 0;
    size_t ambiguousSpriteFrameTextureCount = 0;
    bool placeholderMissingSource = false;
    bool sourceDtxResolved = false;
    bool sourceDtxAmbiguous = false;
    bool sourceSpriteResolved = false;
    bool sourceSpriteAmbiguous = false;
    bool sourceSpritePathExists = false;
    bool sourceSpriteParsed = false;
    bool sourcePathExists = false;
    bool cachePathExists = false;
    bool sourceDtxHashLoaded = false;
    bool cacheHashLoaded = false;
    bool cacheFreshnessKnown = false;
    bool cacheNewerThanSource = false;
    bool cacheOlderThanSource = false;
    bool dtxHeaderLoaded = false;
    bool dtxHeaderMatchesSidecar = false;
    std::optional<EditorMm9DtxHeader> dtxHeader;
};

struct EditorMm9FileInspectionCacheEntry
{
    bool exists = false;
    bool hashLoaded = false;
    bool dtxHeaderLoaded = false;
    uintmax_t sizeBytes = 0;
    std::filesystem::file_time_type lastWriteTime = {};
    std::string sha256;
    std::optional<EditorMm9DtxHeader> dtxHeader;
};

struct EditorMm9MaterialInspectionCache
{
    std::filesystem::path sourceDtxIndexRoot;
    bool sourceDtxIndexBuilt = false;
    std::unordered_map<std::string, std::vector<std::filesystem::path>> sourceDtxIndex;
    std::unordered_map<std::string, EditorMm9FileInspectionCacheEntry> filesByPath;
    size_t sourceDtxIndexBuildCount = 0;
    size_t fileHashReadCount = 0;
    size_t dtxHeaderReadCount = 0;
};

struct EditorMm9RawObjectProperty
{
    std::string name;
    int code = 0;
    int flags = 0;
    size_t declaredDataLength = 0;
    size_t consumedDataLength = 0;
    bool decoded = false;
    std::string rawHex;
    std::string valueJson;
};

struct EditorMm9RawObject
{
    size_t objectIndex = 0;
    std::string name;
    size_t propertyCount = 0;
    size_t dataLength = 0;
    std::string trailingHex;
    std::vector<EditorMm9RawObjectProperty> properties;
};

struct EditorMm9RawObjectsSidecar
{
    int formatVersion = 0;
    std::string kind;
    std::string sourceDat;
    size_t objectCount = 0;
    size_t unknownPropertyCount = 0;
    std::vector<int> unknownPropertyCodes;
    std::vector<EditorMm9RawObject> objects;
};

struct EditorMm9RawObjectAssetReferenceStatus
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string objectName;
    size_t propertyIndex = 0;
    std::string propertyName;
    std::string sourceFamily;
    std::string sourceValue;
    std::string normalizedKey;
    std::string resolvedSourcePath;
    std::vector<std::string> sourceCandidates;
    std::string resolutionSource;
    std::string aliasTargetKey;
    bool required = false;
    bool resolved = false;
    bool ambiguous = false;
    bool aliasApplied = false;
};

struct EditorMm9AssetDependencyFamilySummary
{
    std::string family;
    size_t total = 0;
    size_t resolved = 0;
    size_t unresolved = 0;
    size_t ambiguous = 0;
    size_t stale = 0;
    size_t requiredTotal = 0;
    size_t requiredResolved = 0;
    size_t requiredUnresolved = 0;
    size_t requiredAmbiguous = 0;
    size_t optionalTotal = 0;
    size_t optionalResolved = 0;
    size_t optionalUnresolved = 0;
    size_t optionalAmbiguous = 0;
};

struct EditorMm9AssetDependencySummary
{
    size_t total = 0;
    size_t resolved = 0;
    size_t unresolved = 0;
    size_t ambiguous = 0;
    size_t stale = 0;
    size_t requiredTotal = 0;
    size_t requiredResolved = 0;
    size_t requiredUnresolved = 0;
    size_t requiredAmbiguous = 0;
    size_t optionalTotal = 0;
    size_t optionalResolved = 0;
    size_t optionalUnresolved = 0;
    size_t optionalAmbiguous = 0;
    std::vector<EditorMm9AssetDependencyFamilySummary> families;
};

struct EditorMm9DocumentPathStatus
{
    std::string label;
    std::string role;
    std::string relativePath;
    std::string resolvedPath;
    bool exists = false;
    bool sourceReadOnly = false;
    bool generated = false;
    bool authored = false;
    bool compatibilityDerived = false;
};

struct EditorMm9DiagnosticSeverityRule
{
    std::string severity;
    std::string category;
    bool blocksCleanValidation = false;
    std::string suggestedOwner;
};

struct EditorMm9LoadedSidecars
{
    EditorMm9DatWorldSidecar datWorld;
    EditorMm9MaterialAliasesSidecar materialAliases;
    EditorMm9RawObjectsSidecar rawObjects;
    Game::Mm9EventsData events;
};

struct EditorMm9SourceAssetManifestPolicy
{
    bool sourceTruth = false;
    bool generatedCache = false;
    bool preserveRezRelativeNames = false;
    bool duplicateRezFamilyFolderRemoved = false;
    std::string syncCommand;
};

struct EditorMm9SourceAssetFamily
{
    std::string id;
    std::string source;
    std::string package;
    size_t fileCount = 0;
};

struct EditorMm9SourceAssetFamilyStatus
{
    std::string id;
    std::string source;
    std::string package;
    size_t expectedFileCount = 0;
    size_t actualFileCount = 0;
    bool required = false;
    bool declared = false;
    bool packageDirectoryExists = false;
};

struct EditorMm9SourceAssetManifest
{
    int formatVersion = 0;
    std::string kind;
    std::string sourceRoot;
    std::string packageRoot;
    EditorMm9SourceAssetManifestPolicy policy;
    std::vector<EditorMm9SourceAssetFamily> families;
    std::vector<std::string> notes;
};

std::optional<EditorMm9DatLevelMetadata> loadMm9DatLevelMetadataFromText(
    const std::string &text,
    std::string &errorMessage);

std::optional<EditorMm9DatWorldSidecar> loadMm9DatWorldSidecarFromText(
    const std::string &text,
    std::string &errorMessage);

std::optional<EditorMm9MaterialAliasesSidecar> loadMm9MaterialAliasesSidecarFromText(
    const std::string &text,
    std::string &errorMessage);

std::optional<EditorMm9RawObjectsSidecar> loadMm9RawObjectsSidecarFromText(
    const std::string &text,
    std::string &errorMessage);

std::vector<Game::Mm9LightSourceObject> buildMm9LightSourceObjects(
    const EditorMm9RawObjectsSidecar &rawObjects);

std::vector<Game::Mm9SoundSourceObject> buildMm9SoundSourceObjects(
    const EditorMm9RawObjectsSidecar &rawObjects,
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &assetReferenceStatuses);

std::optional<EditorMm9SourceAssetManifest> loadMm9SourceAssetManifestFromText(
    const std::string &text,
    std::string &errorMessage);

bool isMm9DatLevelText(const std::string &text);

std::filesystem::path resolveMm9DatLevelRelativePath(
    const std::filesystem::path &levelPhysicalPath,
    const std::string &relativePath);

std::filesystem::path resolveMm9SourceAssetManifestPath(const std::filesystem::path &levelPhysicalPath);

std::vector<std::string> validateMm9DatLevelMetadataFiles(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata);

std::vector<std::string> validateMm9DatWorldSidecarReferences(const EditorMm9DatWorldSidecar &sidecar);

std::optional<EditorMm9DtxHeader> readMm9DtxHeader(
    const std::filesystem::path &physicalPath,
    std::string &errorMessage);

std::vector<EditorMm9MaterialTextureStatus> inspectMm9MaterialTextureReferences(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatWorldSidecar &datWorld,
    const EditorMm9MaterialAliasesSidecar &materialAliases,
    EditorMm9MaterialInspectionCache *pCache = nullptr);

std::vector<std::string> validateMm9MaterialTextureReferences(
    const std::vector<EditorMm9MaterialTextureStatus> &statuses);

std::vector<std::string> validateMm9RawObjectsSidecarReferences(const EditorMm9RawObjectsSidecar &sidecar);

std::vector<Game::Mm9ObjectSourceObject> buildMm9ObjectSourceObjects(const EditorMm9RawObjectsSidecar &rawObjects);

std::vector<Game::Mm9SpawnSourceObject> buildMm9SpawnSourceObjects(const EditorMm9RawObjectsSidecar &rawObjects);

std::vector<EditorMm9RawObjectAssetReferenceStatus> inspectMm9RawObjectAssetReferences(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9RawObjectsSidecar &rawObjects,
    const EditorMm9DatLevelMetadata *pMetadata = nullptr);

std::vector<std::string> validateMm9RawObjectAssetReferences(
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &statuses);

EditorMm9AssetDependencySummary summarizeMm9AssetDependencies(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata,
    const std::vector<EditorMm9MaterialTextureStatus> &materialStatuses,
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &rawObjectAssetStatuses);

std::vector<EditorMm9DocumentPathStatus> inspectMm9DatLevelDocumentPaths(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata,
    const std::vector<EditorMm9MaterialTextureStatus> &materialStatuses = {});

bool isMm9DocumentPathRequired(const EditorMm9DocumentPathStatus &status);

std::vector<std::string> validateMm9DatLevelDocumentPathRoles(
    const std::vector<EditorMm9DocumentPathStatus> &statuses);

const std::vector<EditorMm9DiagnosticSeverityRule> &mm9DiagnosticSeverityRules();

std::vector<std::string> validateMm9EventsReferences(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata,
    const EditorMm9DatWorldSidecar &datWorld,
    const EditorMm9RawObjectsSidecar &rawObjects,
    const Game::Mm9EventsData &events);

std::vector<EditorMm9SourceAssetFamilyStatus> inspectMm9SourceAssetManifestFiles(
    const std::filesystem::path &manifestPhysicalPath,
    const EditorMm9SourceAssetManifest &manifest);

std::vector<std::string> validateMm9SourceAssetManifestFiles(
    const std::filesystem::path &manifestPhysicalPath,
    const EditorMm9SourceAssetManifest &manifest);

bool loadMm9DatLevelSidecars(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata,
    EditorMm9LoadedSidecars &sidecars,
    std::string &errorMessage);
}
