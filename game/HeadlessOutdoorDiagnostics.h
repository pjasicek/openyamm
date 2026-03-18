#pragma once

#include "engine/ApplicationConfig.h"

#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class HeadlessOutdoorDiagnostics
{
public:
    explicit HeadlessOutdoorDiagnostics(const Engine::ApplicationConfig &config);

    int runOpenEvent(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        uint16_t eventId
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
    int runSimulateActor(
        const std::filesystem::path &basePath,
        const std::string &mapFileName,
        size_t actorIndex,
        int stepCount,
        float deltaSeconds
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

private:
    Engine::ApplicationConfig m_config;
};
}
