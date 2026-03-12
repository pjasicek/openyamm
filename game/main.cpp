#include "engine/ApplicationConfig.h"
#include "game/GameApplication.h"

int main()
{
    const auto config = OpenYAMM::Engine::ApplicationConfig::createDefault();
    const OpenYAMM::Game::GameApplication application(config);
    return application.run();
}
