#pragma once

#include "engine/ApplicationConfig.h"

#include <cstdint>
#include <filesystem>
#include <string>

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

private:
    Engine::ApplicationConfig m_config;
};
}
