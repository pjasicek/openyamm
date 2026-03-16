#pragma once

#include "engine/ApplicationConfig.h"
#include "engine/AssetFileSystem.h"

#include <functional>

namespace OpenYAMM::Engine
{
class EngineApplication
{
public:
    using StartupCallback = std::function<bool(const AssetFileSystem &)>;
    using RenderSetupCallback = std::function<bool()>;
    using RenderFrameCallback = std::function<void(int, int, float, float)>;

    EngineApplication(
        const ApplicationConfig &config,
        StartupCallback startupCallback,
        RenderSetupCallback renderSetupCallback,
        RenderFrameCallback renderFrameCallback
    );

    int run() const;

private:
    bool initializeAssetFileSystem(AssetFileSystem &assetFileSystem) const;
    bool validateConfiguration() const;

    ApplicationConfig m_config;
    StartupCallback m_startupCallback;
    RenderSetupCallback m_renderSetupCallback;
    RenderFrameCallback m_renderFrameCallback;
};
}
