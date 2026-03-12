#pragma once

#include "engine/ApplicationConfig.h"

namespace OpenYAMM::Game
{
class GameApplication
{
public:
    explicit GameApplication(Engine::ApplicationConfig config);

    [[nodiscard]] int run() const;

private:
    Engine::ApplicationConfig m_config;
};
}
