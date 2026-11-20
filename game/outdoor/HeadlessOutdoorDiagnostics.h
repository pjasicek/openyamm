#pragma once

#include "engine/ApplicationConfig.h"

#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class HeadlessGameplayDiagnostics
{
public:
    explicit HeadlessGameplayDiagnostics(const Engine::ApplicationConfig &config);

    int runOpenEvent(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        uint16_t eventId,
        float advanceSeconds = 0.0f
    ) const;
    int runOpenActor(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        size_t actorIndex
    ) const;
    int runDialogSequence(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        uint16_t eventId,
        const std::vector<size_t> &actionIndices
    ) const;
    int runRegressionSuite(
        const std::filesystem::path &basePath,
        const std::string &suiteName
    ) const;
    int runProfileFullMapLoad(
        const std::filesystem::path &basePath,
        const std::string &mapFileName
    ) const;
    // Builds every actor model binding of the active world's actors.yml (or of every mounted world's with all) with the
    // game's own loader and binding rules, prints each refusal and returns 1 when one fails: headless scenarios load no
    // models, so a refused GLB passes them and breaks maps only on the desktop.
    int runValidateActorModels(
        const std::filesystem::path &basePath,
        bool allWorlds
    ) const;
    int runDumpOutdoorNavigation(
        const std::filesystem::path &basePath,
        const std::string &mapFileName
    ) const;
    // Plans a walking monster's path between point pairs on an indoor map's monster path map (barriers included) and
    // writes each pair's plan status: a converter's check that the path map joins what MM9's AI rails join. The pairs
    // file: {object: {radius, height}, pairs: [{id, from: [x, y, z], to: [x, y, z]}]}, feet positions.
    int runCheckIndoorReachability(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        const std::filesystem::path &pairsPath,
        const std::filesystem::path &outputPath
    ) const;
    // Writes the map's 3D decoration placements as the game places them (decorations.yml), for the lighting bake:
    // per model its asset path, and per placement the decoration entity index and the asset-to-world matrix.
    int runExportDecorationModels(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        const std::filesystem::path &outputPath
    ) const;
    int runVerifyOutdoorWorldItemFloor(
        const std::filesystem::path &basePath,
        const std::string &mapFileName
    ) const;
    int runVerifyOutdoorSaveRoundtrip(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        uint16_t chestEventId,
        uint16_t mechanismEventId
    ) const;
    int runVerifyOutdoorMechanismPassage(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        uint32_t mechanismId
    ) const;
    int runVerifyMm9PositionedTransition(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        uint32_t sourceObjectIndex
    ) const;
    int runSimulateActor(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        size_t actorIndex,
        int stepCount,
        float deltaSeconds,
        float partyOffsetX,
        uint16_t preEventId = 0
    ) const;
    int runTraceActorAi(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        size_t actorIndex,
        int stepCount,
        float deltaSeconds,
        float partyOffsetX
    ) const;
    int runInspectActorPreview(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        size_t actorIndex
    ) const;
    int runDumpActorSupport(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        size_t actorIndex
    ) const;
    int runDumpActorPreviewTexture(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        size_t actorIndex,
        const std::filesystem::path &outputPath
    ) const;
    int runCaptureProjectileFx(
        const std::filesystem::path &basePath,
        const std::filesystem::path &outputDirectory
    ) const;

private:
    Engine::ApplicationConfig m_config;
};
}
