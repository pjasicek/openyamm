#include "engine/ApplicationConfig.h"
#include "game/HeadlessOutdoorDiagnostics.h"
#include "game/GameApplication.h"

#include <cstdint>
#include <exception>
#include <iostream>
#include <string>

namespace
{
int runApplication(int argc, char **argv)
{
    const OpenYAMM::Engine::ApplicationConfig config = OpenYAMM::Engine::ApplicationConfig::createDefault();

    if (argc == 4 && std::string(argv[1]) == "--headless-open-event")
    {
        const std::string mapFileName = argv[2];
        const int parsedEventId = std::stoi(argv[3]);

        if (parsedEventId < 0 || parsedEventId > 65535)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessOutdoorDiagnostics diagnostics(config);
        return diagnostics.runOpenEvent(argv[0], mapFileName, static_cast<uint16_t>(parsedEventId));
    }

    if (argc == 4 && std::string(argv[1]) == "--headless-open-actor")
    {
        const std::string mapFileName = argv[2];
        const int parsedActorIndex = std::stoi(argv[3]);

        if (parsedActorIndex < 0)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessOutdoorDiagnostics diagnostics(config);
        return diagnostics.runOpenActor(argv[0], mapFileName, static_cast<size_t>(parsedActorIndex));
    }

    OpenYAMM::Game::GameApplication application(config);
    return application.run();
}
}

int main(int argc, char **argv)
{
    try
    {
        return runApplication(argc, argv);
    }
    catch (const std::exception &exception)
    {
        std::cerr << "Fatal error: " << exception.what() << '\n';
        return 1;
    }
}
