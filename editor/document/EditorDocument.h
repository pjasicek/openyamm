#pragma once

#include "engine/AssetFileSystem.h"
#include "editor/document/IndoorGeometryMetadata.h"
#include "editor/document/Mm9DatLevelMetadata.h"
#include "editor/document/OutdoorGeometryMetadata.h"
#include "editor/document/OutdoorMapPackageMetadata.h"
#include "editor/document/OutdoorTerrainMetadata.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/mm9/Mm9DatWorld.h"
#include "game/outdoor/OutdoorMapData.h"

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Editor
{
class EditorDocument
{
public:
    enum class Kind
    {
        None,
        Outdoor,
        Indoor,
        Mm9Dat
    };

    bool loadOutdoorMapPackage(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &mapFileName,
        std::string &errorMessage);
    bool loadIndoorMapPackage(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &mapFileName,
        std::string &errorMessage);
    bool loadMapPhysicalPath(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::filesystem::path &path,
        std::string &errorMessage);
    bool loadMm9DatLevelPhysicalPath(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::filesystem::path &levelPhysicalPath,
        std::string &errorMessage);
    bool createNewOutdoorMapPackage(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &mapFileName,
        const std::string &displayName,
        const Game::OutdoorSceneEnvironment &environment,
        std::string &errorMessage);
    bool loadOutdoorSceneVirtualPath(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &sceneVirtualPath,
        std::string &errorMessage);
    bool loadIndoorSceneVirtualPath(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &sceneVirtualPath,
        std::string &errorMessage);

    bool saveSource(std::string &errorMessage);
    bool saveSourceAs(const std::filesystem::path &scenePhysicalPath, std::string &errorMessage);
    bool buildRuntime(std::string &errorMessage);
    bool buildRuntimeAs(const std::filesystem::path &scenePhysicalPath, std::string &errorMessage);
    bool save(std::string &errorMessage);
    bool saveAs(const std::filesystem::path &scenePhysicalPath, std::string &errorMessage);

    bool buildOutdoorAuthoredRuntimeState(
        Game::OutdoorMapData &outdoorMapData,
        Game::MapDeltaData &mapDeltaData,
        std::string &errorMessage) const;
    bool buildIndoorAuthoredRuntimeState(
        Game::IndoorMapData &indoorMapData,
        Game::MapDeltaData &mapDeltaData,
        std::string &errorMessage) const;
    bool restoreOutdoorSceneSnapshot(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &sceneSnapshot,
        std::string &errorMessage);
    bool restoreIndoorSceneSnapshot(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &sceneSnapshot,
        std::string &errorMessage);
    std::string createOutdoorSceneSnapshot() const;
    std::string createIndoorSceneSnapshot() const;
    std::vector<std::string> validate() const;

    Kind kind() const;
    bool hasDocument() const;
    bool isDirty() const;
    bool isRuntimeBuildDirty() const;
    void setDirty(bool isDirty);
    void touchSceneRevision();
    uint64_t sceneRevision() const;

    const std::string &displayName() const;
    const std::string &sceneVirtualPath() const;
    const std::filesystem::path &scenePhysicalPath() const;
    const std::filesystem::path &geometryPhysicalPath() const;
    const std::filesystem::path &geometryMetadataPhysicalPath() const;
    const std::filesystem::path &terrainMetadataPhysicalPath() const;
    const std::filesystem::path &mapPackagePhysicalPath() const;
    bool hasMapPackageRoot() const;
    const EditorOutdoorMapPackageMetadata &outdoorMapPackageMetadata() const;
    EditorOutdoorMapPackageMetadata &mutableOutdoorMapPackageMetadata();
    std::string currentSourcePackageFingerprint() const;

    const Game::OutdoorMapData &outdoorGeometry() const;
    Game::OutdoorMapData &mutableOutdoorGeometry();
    Game::OutdoorSceneData &mutableOutdoorSceneData();
    const Game::OutdoorSceneData &outdoorSceneData() const;
    const Game::IndoorMapData &indoorGeometry() const;
    Game::IndoorMapData &mutableIndoorGeometry();
    Game::IndoorSceneData &mutableIndoorSceneData();
    const Game::IndoorSceneData &indoorSceneData() const;
    const EditorMm9DatLevelMetadata &mm9DatLevelMetadata() const;
    const EditorMm9LoadedSidecars &mm9DatLoadedSidecars() const;
    const Game::Mm9DatWorld &mm9DatWorld() const;
    const Game::Mm9DatRenderMesh &mm9DatRenderMesh() const;
    const Game::Mm9DatRenderBounds &mm9DatRenderBounds() const;
    const std::vector<Game::Mm9DatRenderMaterialAssignment> &mm9DatRenderMaterialAssignments() const;
    const Game::Mm9ObjectLayer &mm9ObjectLayer() const;
    const Game::Mm9LightLayer &mm9LightLayer() const;
    const Game::Mm9SoundLayer &mm9SoundLayer() const;
    const Game::Mm9SpawnLayer &mm9SpawnLayer() const;
    const std::vector<EditorMm9MaterialTextureStatus> &mm9MaterialTextureStatuses() const;
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &mm9RawObjectAssetReferenceStatuses() const;
    const EditorMm9AssetDependencySummary &mm9AssetDependencySummary() const;
    const std::vector<EditorMm9DocumentPathStatus> &mm9DocumentPathStatuses() const;
    const EditorMm9SourceAssetManifest &mm9SourceAssetManifest() const;
    const std::filesystem::path &mm9SourceAssetManifestPhysicalPath() const;
    const std::vector<EditorMm9SourceAssetFamilyStatus> &mm9SourceAssetFamilyStatuses() const;
    const std::vector<std::string> &mm9DatLevelLoadDiagnostics() const;
    const std::vector<std::string> &mm9SourceAssetManifestDiagnostics() const;
    bool hasMm9DatLoadedSidecars() const;
    bool hasMm9DatWorld() const;
    bool hasMm9SourceAssetManifest() const;
    bool hasIndoorGeometryMetadata() const;
    const EditorIndoorGeometryMetadata &indoorGeometryMetadata() const;
    EditorIndoorGeometryMetadata &mutableIndoorGeometryMetadata();
    const EditorOutdoorGeometryMetadata &outdoorGeometryMetadata() const;
    std::optional<EditorBModelImportSource> outdoorBModelImportSource(size_t bmodelIndex) const;
    std::optional<EditorBModelSourceTransform> outdoorBModelSourceTransform(size_t bmodelIndex) const;
    void prepareOutdoorMapPackageIdentityForMapFile(const std::string &mapFileName, const std::string &displayName);
    void setOutdoorBModelImportSource(size_t bmodelIndex, const EditorBModelImportSource &importSource);
    void setOutdoorBModelSourceTransform(size_t bmodelIndex, const EditorBModelSourceTransform &sourceTransform);
    void copyOutdoorBModelImportSource(size_t sourceBModelIndex, size_t targetBModelIndex);
    void eraseOutdoorBModelImportSource(size_t deletedBModelIndex);
    void synchronizeOutdoorGeometryMetadata();
    void synchronizeOutdoorTerrainMetadata();

private:
    bool loadOutdoorSceneText(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &sceneVirtualPath,
        const std::string &sceneText,
        const std::optional<EditorOutdoorMapPackageMetadata> &packageMetadata,
        const std::optional<std::string> &packageVirtualPath,
        std::string &errorMessage);
    bool loadIndoorSceneText(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &sceneVirtualPath,
        const std::string &sceneText,
        std::string &errorMessage);
    bool loadOutdoorScenePhysicalPath(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::filesystem::path &scenePhysicalPath,
        const std::string &sceneText,
        const std::optional<EditorOutdoorMapPackageMetadata> &packageMetadata,
        const std::optional<std::filesystem::path> &packagePhysicalPath,
        std::string &errorMessage);
    bool loadIndoorScenePhysicalPath(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::filesystem::path &scenePhysicalPath,
        const std::string &sceneText,
        std::string &errorMessage);

    static std::string replaceExtension(const std::string &fileName, const std::string &newExtension);
    static std::string deriveGeometryFileNameForScenePath(
        const std::filesystem::path &scenePhysicalPath,
        const std::string &geometryFileName);
    static std::filesystem::path deriveGeometryMetadataPathForScenePath(const std::filesystem::path &scenePhysicalPath);
    static std::filesystem::path deriveMapPackagePathForScenePath(const std::filesystem::path &scenePhysicalPath);
    static std::filesystem::path deriveTerrainMetadataPathForScenePath(const std::filesystem::path &scenePhysicalPath);
    std::string currentSourcePackageFingerprintForTexts(
        const std::string &sceneText,
        const std::string &geometryMetadataText,
        const std::string &terrainMetadataText,
        const EditorOutdoorMapPackageMetadata &packageMetadata) const;
    static std::string serializeOutdoorScene(
        const Game::OutdoorSceneData &sceneData,
        const std::optional<std::string> &geometryFileOverride = std::nullopt);
    static std::string serializeIndoorScene(
        const Game::IndoorSceneData &sceneData,
        const std::optional<std::string> &geometryFileOverride = std::nullopt);
    static bool writeTextFileAtomically(
        const std::filesystem::path &path,
        const std::string &text,
        std::string &errorMessage);
    static bool writeBinaryFileAtomically(
        const std::filesystem::path &path,
        const std::vector<uint8_t> &bytes,
        std::string &errorMessage);

    Kind m_kind = Kind::None;
    bool m_isDirty = false;
    std::filesystem::path m_developmentRoot;
    std::filesystem::path m_editorDevelopmentRoot;
    std::string m_displayName;
    std::string m_sceneVirtualPath;
    std::string m_geometryVirtualPath;
    std::filesystem::path m_scenePhysicalPath;
    std::filesystem::path m_geometryPhysicalPath;
    std::string m_geometryMetadataVirtualPath;
    std::filesystem::path m_geometryMetadataPhysicalPath;
    std::string m_mapPackageVirtualPath;
    std::filesystem::path m_mapPackagePhysicalPath;
    bool m_hasMapPackageRoot = false;
    std::string m_terrainMetadataVirtualPath;
    std::filesystem::path m_terrainMetadataPhysicalPath;
    Game::OutdoorMapData m_outdoorGeometry = {};
    Game::OutdoorSceneData m_outdoorSceneData = {};
    Game::IndoorMapData m_indoorGeometry = {};
    Game::IndoorSceneData m_indoorSceneData = {};
    EditorMm9DatLevelMetadata m_mm9DatLevelMetadata = {};
    EditorMm9LoadedSidecars m_mm9DatLoadedSidecars = {};
    Game::Mm9DatWorld m_mm9DatWorld = {};
    Game::Mm9DatRenderMesh m_mm9DatRenderMesh = {};
    Game::Mm9DatRenderBounds m_mm9DatRenderBounds = {};
    std::vector<Game::Mm9DatRenderMaterialAssignment> m_mm9DatRenderMaterialAssignments;
    Game::Mm9ObjectLayer m_mm9ObjectLayer = {};
    Game::Mm9LightLayer m_mm9LightLayer = {};
    Game::Mm9SoundLayer m_mm9SoundLayer = {};
    Game::Mm9SpawnLayer m_mm9SpawnLayer = {};
    std::vector<EditorMm9MaterialTextureStatus> m_mm9MaterialTextureStatuses;
    std::vector<EditorMm9RawObjectAssetReferenceStatus> m_mm9RawObjectAssetReferenceStatuses;
    EditorMm9AssetDependencySummary m_mm9AssetDependencySummary = {};
    std::vector<EditorMm9DocumentPathStatus> m_mm9DocumentPathStatuses;
    EditorMm9MaterialInspectionCache m_mm9MaterialInspectionCache = {};
    EditorMm9SourceAssetManifest m_mm9SourceAssetManifest = {};
    std::filesystem::path m_mm9SourceAssetManifestPhysicalPath;
    std::vector<EditorMm9SourceAssetFamilyStatus> m_mm9SourceAssetFamilyStatuses;
    std::vector<std::string> m_mm9DatLevelLoadDiagnostics;
    std::vector<std::string> m_mm9SourceAssetManifestDiagnostics;
    bool m_hasMm9DatLoadedSidecars = false;
    bool m_hasMm9DatWorld = false;
    bool m_hasMm9SourceAssetManifest = false;
    bool m_hasIndoorGeometryMetadata = false;
    EditorIndoorGeometryMetadata m_indoorGeometryMetadata = {};
    EditorOutdoorGeometryMetadata m_outdoorGeometryMetadata = {};
    EditorOutdoorMapPackageMetadata m_outdoorMapPackageMetadata = {};
    EditorOutdoorTerrainMetadata m_outdoorTerrainMetadata = {};
    std::vector<uint8_t> m_outdoorGeometrySourceBytes;
    std::vector<uint8_t> m_indoorGeometrySourceBytes;
    uint64_t m_sceneRevision = 0;
    bool m_isRuntimeBuildDirty = false;
};
}
