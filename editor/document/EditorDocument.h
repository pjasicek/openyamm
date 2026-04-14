#pragma once

#include "engine/AssetFileSystem.h"
#include "editor/document/OutdoorGeometryMetadata.h"
#include "editor/document/OutdoorMapPackageMetadata.h"
#include "editor/document/OutdoorTerrainMetadata.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/OutdoorSceneYml.h"
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
        Outdoor
    };

    bool loadOutdoorMapPackage(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &mapFileName,
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
    bool restoreOutdoorSceneSnapshot(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &sceneSnapshot,
        std::string &errorMessage);
    std::string createOutdoorSceneSnapshot() const;
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
    EditorOutdoorGeometryMetadata m_outdoorGeometryMetadata = {};
    EditorOutdoorMapPackageMetadata m_outdoorMapPackageMetadata = {};
    EditorOutdoorTerrainMetadata m_outdoorTerrainMetadata = {};
    std::vector<uint8_t> m_outdoorGeometrySourceBytes;
    uint64_t m_sceneRevision = 0;
    bool m_isRuntimeBuildDirty = false;
};
}
