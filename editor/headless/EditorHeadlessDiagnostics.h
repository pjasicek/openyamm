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

private:
    Engine::ApplicationConfig m_config;
};
}
