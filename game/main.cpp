#include "engine/ApplicationConfig.h"
#include "game/GameApplication.h"

int main()
{
    const OpenYAMM::Engine::ApplicationConfig config = OpenYAMM::Engine::ApplicationConfig::createDefault();
    OpenYAMM::Game::GameApplication application(config);
    return application.run();
}
