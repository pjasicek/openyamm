#pragma once

#include "game/tables/MapStats.h"

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Editor
{
struct EditorOutdoorMapPackageMetadata
{
    uint32_t version = 1;
    std::string packageId;
    std::string displayName;
    std::string mapFileName;
    std::string sceneFile;
    std::string geometryMetadataFile;
    std::string terrainMetadataFile;
    std::string scriptModule;
    int mapStatsId = 0;
    int redbookTrack = 0;
    std::string environmentName;
    bool isTopLevelArea = true;
    Game::MapBounds outdoorBounds = {};
    std::optional<Game::MapEdgeTransition> northTransition;
    std::optional<Game::MapEdgeTransition> southTransition;
    std::optional<Game::MapEdgeTransition> eastTransition;
    std::optional<Game::MapEdgeTransition> westTransition;
    std::string sourceFingerprint;
    std::string builtSourceFingerprint;
};

std::string serializeOutdoorMapPackageMetadata(const EditorOutdoorMapPackageMetadata &metadata);
std::string serializeOutdoorMapPackageSourceFields(const EditorOutdoorMapPackageMetadata &metadata);

std::optional<EditorOutdoorMapPackageMetadata> loadOutdoorMapPackageMetadataFromText(
    const std::string &yamlText,
    std::string &errorMessage);

std::string deriveOutdoorMapPackageId(const std::string &mapFileName);
std::string deriveOutdoorMapPackageDisplayName(const std::string &mapFileName);
std::string computeOutdoorMapPackageSourceFingerprint(
    const std::string &sceneText,
    const std::string &geometryMetadataText,
    const std::string &terrainMetadataText,
    const std::string &packageSourceText);

void normalizeOutdoorMapPackageMetadata(
    EditorOutdoorMapPackageMetadata &metadata,
    const std::string &packageId,
    const std::string &displayName,
    const std::string &mapFileName,
    const std::string &sceneFile,
    const std::string &geometryMetadataFile,
    const std::string &terrainMetadataFile,
    const std::string &scriptModule,
    const std::string &sourceFingerprint,
    const std::string &builtSourceFingerprint);
}
