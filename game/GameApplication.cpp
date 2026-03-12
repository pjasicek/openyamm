#include "game/GameApplication.h"

#include <filesystem>
#include <iostream>

namespace OpenYAMM::Game
{
GameApplication::GameApplication(Engine::ApplicationConfig config)
    : m_config(std::move(config))
{
}

int GameApplication::run() const
{
    std::cout << m_config.appName << '\n';
    std::cout << "Development assets: " << m_config.assetRoot << '\n';

    const bool assetsExist = std::filesystem::exists(m_config.assetRoot);
    std::cout << "Assets available: " << (assetsExist ? "yes" : "no") << '\n';

    return assetsExist ? 0 : 1;
}
}
