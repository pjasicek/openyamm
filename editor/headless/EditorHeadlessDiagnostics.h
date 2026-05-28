#pragma once

#include "engine/ApplicationConfig.h"

#include <filesystem>
#include <string>

namespace OpenYAMM::Editor
{
class EditorHeadlessDiagnostics
{
public:
    explicit EditorHeadlessDiagnostics(const Engine::ApplicationConfig &config);

    int runRegressionSuite(
        const std::filesystem::path &basePath,
        const std::string &suiteName
    ) const;
    int runCompareOutdoorScene(
        const std::filesystem::path &basePath,
        const std::string &mapFileName
    ) const;
    int runVerifyModelInstances(
        const std::filesystem::path &basePath,
        const std::string &mapFileName
    ) const;
    int runVerifyMm9DatLevel(
        const std::filesystem::path &basePath,
        const std::string &levelFileName
    ) const;
    int runVerifyMm9DatFilters(
        const std::filesystem::path &basePath,
        const std::string &levelFileName
    ) const;
    int runVerifyMm9EventProvenance(
        const std::filesystem::path &basePath,
        const std::string &levelFileName,
        const std::string &sourceObjectIndexText
    ) const;
    int runVerifyMm9Events(
        const std::filesystem::path &basePath,
        const std::string &levelFileName
    ) const;
    int runVerifyMm9SourceManifest(const std::filesystem::path &basePath) const;
    int runVerifyMm9InspectorSearch(
        const std::filesystem::path &basePath,
        const std::string &levelFileName
    ) const;
    int runVerifyDocumentDispatch(const std::filesystem::path &basePath) const;
    int runVerifyAllMm9DatLevels(const std::filesystem::path &basePath) const;

private:
    Engine::ApplicationConfig m_config;
};
}
