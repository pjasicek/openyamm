#include "engine/ApplicationConfig.h"
#include "game/HeadlessOutdoorDiagnostics.h"
#include "game/GameApplication.h"

#include <cstdint>
#include <exception>
#include <iostream>
#include <string>
#include <vector>

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

    if (argc >= 5 && std::string(argv[1]) == "--headless-run-dialog-sequence")
    {
        const std::string mapFileName = argv[2];
        const int parsedEventId = std::stoi(argv[3]);

        if (parsedEventId < 0 || parsedEventId > 65535)
        {
            return 2;
        }

        std::vector<size_t> actionIndices;

        for (int argumentIndex = 4; argumentIndex < argc; ++argumentIndex)
        {
            const int parsedActionIndex = std::stoi(argv[argumentIndex]);

            if (parsedActionIndex < 0)
            {
                return 2;
            }

            actionIndices.push_back(static_cast<size_t>(parsedActionIndex));
        }

        OpenYAMM::Game::HeadlessOutdoorDiagnostics diagnostics(config);
        return diagnostics.runDialogSequence(argv[0], mapFileName, static_cast<uint16_t>(parsedEventId), actionIndices);
    }

    if (argc == 3 && std::string(argv[1]) == "--headless-run-regression-suite")
    {
        OpenYAMM::Game::HeadlessOutdoorDiagnostics diagnostics(config);
        return diagnostics.runRegressionSuite(argv[0], argv[2]);
    }

    if (argc == 3 && std::string(argv[1]) == "--headless-profile-map-load-full")
    {
        OpenYAMM::Game::HeadlessOutdoorDiagnostics diagnostics(config);
        return diagnostics.runProfileFullMapLoad(argv[0], argv[2]);
    }

    if (argc == 6 && std::string(argv[1]) == "--headless-simulate-actor")
    {
        const std::string mapFileName = argv[2];
        const int parsedActorIndex = std::stoi(argv[3]);
        const int parsedStepCount = std::stoi(argv[4]);
        const float deltaSeconds = std::stof(argv[5]);

        if (parsedActorIndex < 0 || parsedStepCount <= 0 || deltaSeconds <= 0.0f)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessOutdoorDiagnostics diagnostics(config);
        return diagnostics.runSimulateActor(
            argv[0],
            mapFileName,
            static_cast<size_t>(parsedActorIndex),
            parsedStepCount,
            deltaSeconds);
    }

    if (argc == 6 && std::string(argv[1]) == "--headless-trace-actor-ai")
    {
        const std::string mapFileName = argv[2];
        const int parsedActorIndex = std::stoi(argv[3]);
        const int parsedStepCount = std::stoi(argv[4]);
        const float deltaSeconds = std::stof(argv[5]);

        if (parsedActorIndex < 0 || parsedStepCount <= 0 || deltaSeconds <= 0.0f)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessOutdoorDiagnostics diagnostics(config);
        return diagnostics.runTraceActorAi(
            argv[0],
            mapFileName,
            static_cast<size_t>(parsedActorIndex),
            parsedStepCount,
            deltaSeconds);
    }

    if (argc == 4 && std::string(argv[1]) == "--headless-inspect-actor-preview")
    {
        const std::string mapFileName = argv[2];
        const int parsedActorIndex = std::stoi(argv[3]);

        if (parsedActorIndex < 0)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessOutdoorDiagnostics diagnostics(config);
        return diagnostics.runInspectActorPreview(argv[0], mapFileName, static_cast<size_t>(parsedActorIndex));
    }

    if (argc == 4 && std::string(argv[1]) == "--headless-dump-actor-support")
    {
        const std::string mapFileName = argv[2];
        const int parsedActorIndex = std::stoi(argv[3]);

        if (parsedActorIndex < 0)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessOutdoorDiagnostics diagnostics(config);
        return diagnostics.runDumpActorSupport(argv[0], mapFileName, static_cast<size_t>(parsedActorIndex));
    }

    if (argc == 5 && std::string(argv[1]) == "--headless-dump-actor-preview-texture")
    {
        const std::string mapFileName = argv[2];
        const int parsedActorIndex = std::stoi(argv[3]);

        if (parsedActorIndex < 0)
        {
            return 2;
        }

        OpenYAMM::Game::HeadlessOutdoorDiagnostics diagnostics(config);
        return diagnostics.runDumpActorPreviewTexture(
            argv[0],
            mapFileName,
            static_cast<size_t>(parsedActorIndex),
            argv[4]);
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
